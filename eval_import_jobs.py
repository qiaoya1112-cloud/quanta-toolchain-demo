"""Persistent evaluation imports and versioned catalog state for the local portal.

The signed session identifies demo visitors until the host supplies authenticated
user IDs. File ownership is enforced server-side on every job/download request.
"""
import hashlib
import io
import json
import os
import secrets
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from flask import abort, current_app, g, jsonify, request, send_file, session

ROOT = Path(__file__).resolve().parent
PREFIX = '/model/eval/test-cases/import'
JOB_METADATA = ('id, filename, submitted_at, status, message, summary, '
                'report IS NOT NULL AS has_report, length(source) > 0 AS has_source, lease_until')
FAILED_STATUSES = ('upload_failed', 'validation_failed', 'import_failed', 'failed')
_threads = set()
_lock = threading.Lock()


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def identity():
    resolver = current_app.config.get('EVAL_IMPORT_IDENTITY')
    if resolver:
        tenant, user, name = resolver()
        if not tenant or not user:
            abort(401)
        return str(tenant), str(user), str(name)
    user = getattr(g, 'user_id', None) or session.get('user_id')
    tenant = getattr(g, 'tenant_id', None) or session.get('tenant_id') or 'demo'
    if user:
        return str(tenant), str(user), str(getattr(g, 'user_name', None) or session.get('user_name') or user)
    # No real sign-in exists in this prototype. Never trust a request user_id.
    if not current_app.config.get('EVAL_IMPORT_DEMO_IDENTITY', True):
        abort(401)
    if 'eval_import_visitor' not in session:
        session['eval_import_visitor'] = secrets.token_urlsafe(24)
    return str(tenant), 'visitor:' + session['eval_import_visitor'], 'Joanna Qiao'


def db_path(app):
    return app.config.get('EVAL_IMPORT_DB', str(Path(app.instance_path) / 'eval_imports.sqlite3'))


@contextmanager
def connect(app):
    path = db_path(app)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('''CREATE TABLE IF NOT EXISTS eval_catalog_state (
        tenant TEXT PRIMARY KEY, revision INTEGER NOT NULL, document TEXT NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS eval_import_jobs (
        id TEXT PRIMARY KEY, tenant TEXT NOT NULL, user_id TEXT NOT NULL, actor TEXT NOT NULL,
        request_key TEXT NOT NULL, fingerprint TEXT NOT NULL, filename TEXT NOT NULL,
        source BLOB NOT NULL, duplicate_mode TEXT NOT NULL, status TEXT NOT NULL,
        submitted_at TEXT NOT NULL, finished_at TEXT, message TEXT NOT NULL DEFAULT '',
        report BLOB, summary TEXT, lease_until REAL NOT NULL DEFAULT 0,
        UNIQUE(tenant, user_id, request_key))''')
    db.execute('CREATE INDEX IF NOT EXISTS eval_import_owner ON eval_import_jobs(tenant,user_id,submitted_at)')
    db.commit()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_catalog(app, payload):
    node = app.config.get('EVAL_IMPORT_NODE') or os.environ.get('NODE_BINARY') or shutil.which('node')
    if not node:
        bundled = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
        node = str(bundled) if bundled.is_file() else None
    if not node:
        raise RuntimeError('导入服务缺少 Node.js 运行环境，请配置 NODE_BINARY')
    result = subprocess.run([node, str(ROOT / 'scripts/eval_import_runner.cjs')],
                            input=json.dumps(payload, ensure_ascii=False), text=True,
                            capture_output=True, timeout=120, cwd=ROOT)
    if result.returncode:
        raise RuntimeError('导入校验服务执行失败：' + result.stderr[:500])
    return json.loads(result.stdout)


def import_context():
    from data_platform_refactor import USER_GROUPS
    from quanta_eval_platform import tag_management_dimensions
    tags = []
    def walk(nodes, parent):
        for node in nodes:
            path = parent + [node['name']]
            tags.append({'id': node['id'], 'name': ' / '.join(path)})
            walk(node.get('sub_tags', []), path)
    for dimension in tag_management_dimensions():
        walk(dimension['tags'], [dimension['name']])
    return {'userGroups': [{'id': x['id'], 'name': x['name'], 'enabled': x.get('enabled', True)} for x in USER_GROUPS], 'tags': tags}


def public_job(row):
    status = row['status']
    if status == 'failed':
        status = 'validation_failed' if row['message'].startswith('校验失败') else 'import_failed'
    has_source = bool(row['has_source']) if 'has_source' in row.keys() else bool(row['source'])
    return {'id': row['id'], 'filename': row['filename'], 'submitted_at': row['submitted_at'],
            'status': status, 'message': row['message'], 'has_source': has_source,
            'summary': json.loads(row['summary']) if row['summary'] else None,
            'has_report': bool(row['has_report']) if 'has_report' in row.keys() else row['report'] is not None,
            'download_url': PREFIX + '/jobs/' + row['id'] + '/file' if has_source else None}


def finish_failed(app, task, errors, parsed=None, status='validation_failed'):
    from eval_case_import import error_workbook
    parsed = parsed or {}
    report = error_workbook(task['source'], task['filename'], errors, parsed.get('sheet', ''), parsed.get('header_row', 1)).getvalue()
    failed_rows = len({e['row'] for e in errors if e.get('row', 1) > parsed.get('header_row', 1)})
    label = '校验失败' if status == 'validation_failed' else '导入失败'
    message = f'{label}，整批未导入。{failed_rows} 条记录存在 {len(errors)} 项错误，请下载错误文件修正。' if failed_rows else label + '，整批未导入：' + '；'.join(e['message'] for e in errors[:3])
    with connect(app) as db:
        db.execute('''UPDATE eval_import_jobs SET status=?, report=?, message=?,
                      finished_at=?, lease_until=0 WHERE id=? AND status != 'success' ''',
                   (status, report, message, now(), task['id']))


def worker(app, task_id):
    task = None
    phase = 'validation_failed'
    key = (db_path(app), task_id)
    try:
        with app.app_context():
            with connect(app) as db:
                claimed = db.execute('''UPDATE eval_import_jobs SET lease_until=? WHERE id=?
                    AND status IN ('validating','importing') AND lease_until<?''',
                    (time.time() + 300, task_id, time.time())).rowcount
                if not claimed:
                    return
                task = dict(db.execute('SELECT * FROM eval_import_jobs WHERE id=?', (task_id,)).fetchone())
                state = db.execute('SELECT * FROM eval_catalog_state WHERE tenant=?', (task['tenant'],)).fetchone()
                if state is None:
                    raise ValueError('评测数据尚未初始化，请刷新页面后重新上传')
                revision, document = state['revision'], json.loads(state['document'])
            from eval_case_import import parse_upload
            try:
                parsed = parse_upload(task['source'], task['filename'])
            except Exception as error:
                finish_failed(app, task, [{'row': 1, 'message': str(error) if isinstance(error, ValueError) else '文件无法读取，请检查格式或图片是否损坏'}])
                return
            context = app.config.get('EVAL_IMPORT_CONTEXT_FACTORY', import_context)()
            context['duplicateMode'] = task['duplicate_mode']
            result = run_catalog(app, {'action': 'plan', 'db': document, 'parsed': parsed, 'context': context, 'actor': task['actor'], 'now': now()})
            if result['errors']:
                finish_failed(app, task, result['errors'], parsed)
                return
            with connect(app) as db:
                db.execute("UPDATE eval_import_jobs SET status='importing', message='校验通过，正在导入…' WHERE id=?", (task_id,))
            phase = 'import_failed'
            summary = {name: len(result[name]) for name in ('created', 'updated', 'unchanged', 'skipped')}
            summary['related'] = result['counts']
            summary['total'] = len(parsed['rows'])
            message = f"导入成功：新增 {summary['created']} 条、更新 {summary['updated']} 条、未变更 {summary['unchanged']} 条、跳过 {summary['skipped']} 条。"
            with connect(app) as db:
                db.execute('BEGIN IMMEDIATE')
                current = db.execute('SELECT revision FROM eval_catalog_state WHERE tenant=?', (task['tenant'],)).fetchone()
                if current['revision'] != revision:
                    raise ValueError('校验期间评测数据发生变化，整批未导入，请重新上传校验')
                if result['created'] or result['updated'] or any(result['counts'].values()):
                    db.execute('UPDATE eval_catalog_state SET revision=revision+1, document=? WHERE tenant=?',
                               (json.dumps(result['next'], ensure_ascii=False), task['tenant']))
                # Catalog and final task status commit together; retries cannot double-write.
                db.execute("UPDATE eval_import_jobs SET status='success',message=?,summary=?,finished_at=?,lease_until=0 WHERE id=?",
                           (message, json.dumps(summary, ensure_ascii=False), now(), task_id))
    except Exception as error:
        if task:
            try:
                finish_failed(app, task, [{'row': 1, 'message': str(error) if isinstance(error, ValueError) else '处理服务暂时不可用，整批未导入，请稍后重试'}], status=phase)
            except Exception:
                app.logger.exception('Unable to generate evaluation import error report')
                with connect(app) as db:
                    db.execute("UPDATE eval_import_jobs SET status=?,message=?,finished_at=?,lease_until=0 WHERE id=? AND status!='success'",
                               (phase, ('校验失败' if phase=='validation_failed' else '导入失败')+'，错误文件暂未生成，请重新上传。', now(), task_id))
        if not isinstance(error, ValueError):
            app.logger.exception('Evaluation import worker failed')
    finally:
        with _lock:
            _threads.discard(key)


def start(app, task_id):
    key = (db_path(app), task_id)
    with _lock:
        if key in _threads:
            return
        _threads.add(key)
    if app.config.get('EVAL_IMPORT_SYNC'):
        worker(app, task_id)
    else:
        threading.Thread(target=worker, args=(app, task_id), daemon=True).start()


def register_import_jobs(app):
    def state():
        tenant, user, actor = identity()
        with connect(app) as db:
            row = db.execute('SELECT * FROM eval_catalog_state WHERE tenant=?', (tenant,)).fetchone()
        namespace = hashlib.sha256((tenant + ':' + user).encode()).hexdigest()[:24]
        if request.method == 'GET':
            return jsonify(document=json.loads(row['document']) if row else None, revision=row['revision'] if row else 0, namespace=namespace, migrate_legacy=user.startswith('visitor:'))
        payload = request.get_json(silent=True) or {}
        document = payload.get('document')
        if not isinstance(document, dict) or any(not isinstance(document.get(k), list) for k in ['stages','stories','skills','factors','test-cases']):
            return jsonify(message='评测数据格式无效'), 400
        if row is None:
            from eval_catalog import seed_data
            updated = run_catalog(app, {'action':'initialize','seed':seed_data(),'saved':document,'actor':actor})
        else:
            if payload.get('revision') != row['revision']:
                return jsonify(message='评测数据已更新，请刷新后重新操作'), 409
            updated = run_catalog(app, {'action':'audit','previous':json.loads(row['document']),'next':document,'tags':import_context()['tags'],'actor':actor,'now':now()})
        with connect(app) as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT revision FROM eval_catalog_state WHERE tenant=?', (tenant,)).fetchone()
            if current and (row is None or current['revision'] != row['revision']):
                return jsonify(message='评测数据已更新，请刷新后重新操作'), 409
            revision = (current['revision'] if current else 0) + 1
            db.execute('INSERT OR REPLACE INTO eval_catalog_state VALUES (?,?,?)', (tenant,revision,json.dumps(updated,ensure_ascii=False)))
        return jsonify(document=updated,revision=revision,namespace=namespace)

    def jobs():
        tenant, user, actor = identity()
        if request.method == 'POST' and request.is_json:
            payload = request.get_json(silent=True) or {}
            mode, request_key = payload.get('duplicate_mode', 'skip'), payload.get('request_key', '')
            filename = Path(str(payload.get('filename', '')).replace('\\', '/')).name[:240]
            if not filename or mode not in ('skip', 'update') or not isinstance(request_key, str) or not request_key or len(request_key)>100:
                return jsonify(message='请选择文件及有效的重复处理方式'), 400
            with connect(app) as db:
                db.execute('BEGIN IMMEDIATE')
                existing = db.execute('SELECT * FROM eval_import_jobs WHERE tenant=? AND user_id=? AND request_key=?', (tenant,user,request_key)).fetchone()
                if existing:
                    if existing['filename'] != filename or existing['duplicate_mode'] != mode:
                        return jsonify(message='同一提交不能更换文件或重复处理方式'), 409
                    task_id = existing['id']
                    if existing['status'] == 'upload_failed':
                        db.execute("UPDATE eval_import_jobs SET status='uploading',message='正在上传文件…',finished_at=NULL,lease_until=? WHERE id=?", (time.time()+300,task_id))
                else:
                    task_id = uuid.uuid4().hex
                    db.execute('''INSERT INTO eval_import_jobs (id,tenant,user_id,actor,request_key,fingerprint,filename,source,duplicate_mode,status,submitted_at,message,lease_until)
                        VALUES (?,?,?,?,?,'',?,?,?,'uploading',?,'正在上传文件…',?)''',
                        (task_id,tenant,user,actor,request_key,filename,b'',mode,now(),time.time()+300))
                task = db.execute('SELECT '+JOB_METADATA+' FROM eval_import_jobs WHERE id=?', (task_id,)).fetchone()
            return jsonify(public_job(task)), 202
        if request.method == 'POST':
            from eval_case_import import MAX_UPLOAD
            file = request.files.get('file')
            mode = request.form.get('duplicate_mode', 'skip')
            request_key = request.form.get('request_key', '')
            if not file or not file.filename or mode not in ('skip','update') or not request_key or len(request_key)>100:
                return jsonify(message='请选择文件及有效的重复处理方式'), 400
            data = file.stream.read(MAX_UPLOAD + 1)
            if not data or len(data)>MAX_UPLOAD:
                return jsonify(message='文件不能为空，且不能超过 12 MB'), 400
            fingerprint = hashlib.sha256(data + mode.encode()).hexdigest()
            with connect(app) as db:
                db.execute('BEGIN IMMEDIATE')
                previous = db.execute('SELECT id, fingerprint FROM eval_import_jobs WHERE tenant=? AND user_id=? AND request_key=?', (tenant,user,request_key)).fetchone()
                if previous:
                    if previous['fingerprint'] != fingerprint:
                        return jsonify(message='同一提交不能更换文件或重复处理方式'), 409
                    task_id = previous['id']
                else:
                    task_id = uuid.uuid4().hex
                    filename = Path(file.filename.replace('\\','/')).name[:240]
                    db.execute('''INSERT INTO eval_import_jobs (id,tenant,user_id,actor,request_key,fingerprint,filename,source,duplicate_mode,status,submitted_at,message)
                        VALUES (?,?,?,?,?,?,?,?,?,'validating',?,'正在校验文件…')''',
                        (task_id,tenant,user,actor,request_key,fingerprint,filename,data,mode,now()))
            start(app, task_id)
            with connect(app) as db:
                task = db.execute('SELECT '+JOB_METADATA+' FROM eval_import_jobs WHERE id=?', (task_id,)).fetchone()
            return jsonify(public_job(task)), 202
        page = max(1, request.args.get('page', 1, type=int))
        with connect(app) as db:
            db.execute("UPDATE eval_import_jobs SET status='upload_failed',message='文件上传超时或中断，请重新上传。',finished_at=? WHERE tenant=? AND user_id=? AND status='uploading' AND lease_until<?", (now(),tenant,user,time.time()))
            total = db.execute('SELECT count(*) FROM eval_import_jobs WHERE tenant=? AND user_id=?',(tenant,user)).fetchone()[0]
            rows = db.execute('SELECT '+JOB_METADATA+' FROM eval_import_jobs WHERE tenant=? AND user_id=? ORDER BY submitted_at DESC,rowid DESC LIMIT 10 OFFSET ?', (tenant,user,(page-1)*10)).fetchall()
            recover = db.execute("SELECT id FROM eval_import_jobs WHERE tenant=? AND user_id=? AND status IN ('validating','importing') AND lease_until<?",(tenant,user,time.time())).fetchall()
        for task in recover:
            start(app, task['id'])
        return jsonify(items=[public_job(row) for row in rows],total=total,page=page)

    def upload(task_id):
        tenant, user, _ = identity()
        with connect(app) as db:
            task = db.execute('SELECT * FROM eval_import_jobs WHERE id=? AND tenant=? AND user_id=?', (task_id,tenant,user)).fetchone()
        if task is None:
            abort(404)
        if task['status'] not in ('uploading', 'upload_failed'):
            return jsonify(public_job(task))
        if request.is_json:
            reason = (request.get_json(silent=True) or {}).get('reason')
            message = {'empty':'文件为空，请重新上传。','too_large':'文件不能超过 12 MB，请拆分后重新上传。'}.get(reason, '文件上传失败或网络中断，请重试。')
            with connect(app) as db:
                db.execute("UPDATE eval_import_jobs SET status='upload_failed',message=?,finished_at=?,lease_until=0 WHERE id=? AND status='uploading'", (message,now(),task_id))
                updated = db.execute('SELECT '+JOB_METADATA+' FROM eval_import_jobs WHERE id=?', (task_id,)).fetchone()
            return jsonify(public_job(updated))
        from eval_case_import import MAX_UPLOAD
        try:
            file = request.files.get('file')
            data = file.stream.read(MAX_UPLOAD + 1) if file else b''
            if not data or len(data)>MAX_UPLOAD:
                raise ValueError('文件不能为空，且不能超过 12 MB，请重新上传。')
        except Exception as error:
            message = str(error) if isinstance(error, ValueError) else '文件上传失败，请重新上传。'
            with connect(app) as db:
                db.execute("UPDATE eval_import_jobs SET status='upload_failed',message=?,finished_at=?,lease_until=0 WHERE id=? AND status='uploading'", (message,now(),task_id))
                updated = db.execute('SELECT '+JOB_METADATA+' FROM eval_import_jobs WHERE id=?', (task_id,)).fetchone()
            return jsonify(public_job(updated)), 400
        with connect(app) as db:
            db.execute("UPDATE eval_import_jobs SET source=?,fingerprint=?,status='validating',message='正在校验文件…',finished_at=NULL,lease_until=0 WHERE id=? AND status IN ('uploading','upload_failed')",
                       (data,hashlib.sha256(data+task['duplicate_mode'].encode()).hexdigest(),task_id))
        start(app, task_id)
        with connect(app) as db:
            updated = db.execute('SELECT '+JOB_METADATA+' FROM eval_import_jobs WHERE id=?', (task_id,)).fetchone()
        return jsonify(public_job(updated)), 202

    def job(task_id):
        tenant, user, _ = identity()
        with connect(app) as db:
            fields = '*' if request.path.endswith('/file') else JOB_METADATA
            task = db.execute('SELECT '+fields+' FROM eval_import_jobs WHERE id=? AND tenant=? AND user_id=?', (task_id,tenant,user)).fetchone()
        if task is None:
            abort(404)
        if request.path.endswith('/file'):
            if not task['source']:
                abort(404)
            report = task['status'] in FAILED_STATUSES and task['report'] is not None
            name = Path(task['filename']).stem + '_错误明细.xlsx' if report else task['filename']
            response = send_file(io.BytesIO(task['report'] if report else task['source']),as_attachment=True,download_name=name)
            response.headers['Cache-Control']='private, no-store'
            return response
        if task['status'] in ('validating','importing') and task['lease_until']<time.time():
            start(app, task_id)
        return jsonify(public_job(task))

    app.add_url_rule(PREFIX+'/state','eval_import_state',state,methods=['GET','POST'])
    app.add_url_rule(PREFIX+'/jobs','eval_import_jobs',jobs,methods=['GET','POST'])
    app.add_url_rule(PREFIX+'/jobs/<task_id>','eval_import_job',job)
    app.add_url_rule(PREFIX+'/jobs/<task_id>/upload','eval_import_upload',upload,methods=['POST'])
    app.add_url_rule(PREFIX+'/jobs/<task_id>/file','eval_import_job_file',job)
