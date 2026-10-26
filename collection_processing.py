"""Local processing-task persistence and explicit recording membership.

Reuse the existing processing form. Collection lifecycle writes never touch this
table; planned sources and recordings actually admitted are separate facts.
"""
import copy
import hashlib
import json
import math
import re
from datetime import datetime
from urllib.parse import quote

from flask import Blueprint, abort, jsonify, request

import post_training_collection as collection

API = collection.API + '/processing'
STATES = {'draft': '未发布', 'waiting': '等待数据', 'pending': '待处理',
          'processing': '处理中', 'completed': '已完成', 'paused': '已关闭'}


def setup(conn):
    conn.execute('CREATE TABLE IF NOT EXISTS collection_processing (id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL, fingerprint TEXT NOT NULL, payload TEXT NOT NULL)')


def all_jobs(conn):
    setup(conn)
    return [json.loads(row['payload']) for row in conn.execute('SELECT payload FROM collection_processing ORDER BY rowid DESC')]


def get_job(conn, job_id):
    setup(conn)
    row = conn.execute('SELECT payload FROM collection_processing WHERE id=?', (job_id,)).fetchone()
    if not row:
        abort(404, description='处理任务不存在')
    return json.loads(row['payload'])


def save_job(conn, job):
    conn.execute('UPDATE collection_processing SET payload=? WHERE id=?', (json.dumps(job, ensure_ascii=False), job['id']))


def tokens(value):
    return [x.strip() for x in re.split('[,，、]', value) if x.strip()]


def matches(job, task, record):
    if record.get('upload') != 'uploaded':
        return False
    for field, operator, value, *scope in job['filters']:
        actual = {'采集任务 ID': task['id'], '数据 ID': record['id'],
                  '采集员': record.get('operator', ''),
                  '采集结论': {'success': '成功', 'failure': '失败'}.get(record.get('collection_result'), '')}.get(field, '')
        if field == '采集时间':
            start, _, end = value.partition('~')
            passed = (not start or record['recorded_at'] >= start) and (not end or record['recorded_at'] <= end)
        elif operator == '为空':
            passed = not actual
        elif operator == '不为空':
            passed = bool(actual)
        elif operator in ('包含', '不包含'):
            passed = any(item in actual for item in tokens(value))
            if operator == '不包含':
                passed = not passed
        else:
            passed = actual in tokens(value)
            if operator == '不等于':
                passed = not passed
        if not passed:
            return False
    return True


def source_tasks(conn, job):
    return [collection.get_task(conn, tid) for tid in job['source_ids']]


def candidates(conn, job):
    return [(task, record) for task in source_tasks(conn, job)
            for record in task['records'] if matches(job, task, record)]


def admit(conn, job):
    existing = {(r['task_id'], r['id']) for r in job['records']}
    for task, record in candidates(conn, job):
        key = (task['id'], record['id'])
        if key not in existing:
            job['records'].append({'id': record['id'], 'task_id': task['id'],
                                   'admitted_at': collection.now(),
                                   'stages': {stage: 'pending' for stage in job['stages']}})
            existing.add(key)


def public_job(conn, job, task_id=None, record_id=None):
    result = copy.deepcopy(job)
    selected = [r for r in job['records'] if (not task_id or r['task_id'] == task_id)
                and (not record_id or r['id'] == record_id)]
    candidate_rows = [(t, r) for t, r in candidates(conn, job)
                      if (not task_id or t['id'] == task_id) and (not record_id or r['id'] == record_id)]
    existing = {(r['task_id'], r['id']) for r in job['records']}
    result['candidate_count'] = len(candidate_rows)
    result['new_count'] = sum((t['id'], r['id']) not in existing for t, r in candidate_rows)
    result['selected_count'] = len(selected)
    result['total_count'] = len(job['records'])
    result['stage_progress'] = []
    for stage in job['stages']:
        done = sum(r['stages'].get(stage) == 'completed' for r in selected)
        running = any(r['stages'].get(stage) == 'processing' for r in selected)
        state = ('draft' if not job['published'] else 'paused' if not job['enabled'] else
                 'waiting' if not selected else 'completed' if done == len(selected) else
                 'processing' if running or done else 'pending')
        result['stage_progress'].append(dict(stage=stage, done=done, total=len(selected), status=state, label=STATES[state]))
    result['status'] = ('draft' if not job['published'] else 'paused' if not job['enabled'] else
                        'waiting' if not selected else 'completed' if all(p['done'] == len(selected) for p in result['stage_progress']) else
                        'processing' if any(p['status'] == 'processing' for p in result['stage_progress']) else 'pending')
    result['status_label'] = STATES[result['status']]
    result['href'] = '/data/processing-tasks?linked=' + quote(job['id'])
    result.pop('request_key', None)
    return result


def validate(conn, body, flows):
    if not isinstance(body, dict):
        return None, '请求内容无效'
    name = body.get('name')
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
        return None, '请填写处理任务名称，最多 100 字'
    source_ids = body.get('source_ids')
    if not isinstance(source_ids, list) or not source_ids or len(source_ids) > 50 or any(not isinstance(t, str) for t in source_ids):
        return None, '请选择来源采集任务'
    tasks = [collection.get_task(conn, tid) for tid in dict.fromkeys(source_ids)]
    if len({task['project'] for task in tasks}) != 1:
        return None, '来源采集任务必须属于同一项目'
    filters = body.get('filters', [])
    if not isinstance(filters, list) or len(filters) > 30:
        return None, '筛选条件格式无效'
    # Only implement filters with collection facts. Never pretend a rule-specific
    # processing result can be inferred from the legacy quality fixture.
    allowed_fields = {'采集任务 ID', '数据 ID', '采集员', '采集时间', '采集结论'}
    for item in filters:
        if not isinstance(item, list) or len(item) != 3 or any(not isinstance(v, str) for v in item):
            return None, '筛选条件格式无效'
        field, operator, value = item
        if field not in allowed_fields:
            return None, '当前采集关联支持采集任务 ID、数据 ID、采集员、采集时间和采集结论筛选'
        if operator not in ('等于', '不等于', '包含', '不包含', '为空', '不为空') or len(value) > 20000:
            return None, '筛选条件无效'
        if operator not in ('为空', '不为空') and not value.strip():
            return None, '请补全筛选条件的值'
        if field == '采集任务 ID' and (operator != '等于' or set(tokens(value)) != {t['id'] for t in tasks}):
            return None, '来源采集任务已变化，请重新选择'
        if field == '采集时间':
            try:
                start, _, end = value.partition('~')
                if not start or datetime.fromisoformat(start).tzinfo is not None or (end and datetime.fromisoformat(end).tzinfo is not None) or (end and start > end):
                    raise ValueError()
            except ValueError:
                return None, '请填写有效的采集时间范围'
    stages = body.get('stages')
    if not isinstance(stages, dict) or not stages or set(stages) - {'质检', '标注'}:
        return None, '请至少配置一个业务环节'
    configs = body.get('configs')
    if not isinstance(configs, dict):
        return None, '请配置业务环节的处理人和规则'
    for stage, flow_name in stages.items():
        flow = next((f for f in flows if f['stage'] == stage and f['name'] == flow_name), None)
        if not flow:
            return None, '请选择有效的处理流程'
        nodes = configs.get(stage)
        if not isinstance(nodes, dict):
            return None, '请完成所有已开启环节的节点配置'
        for node in flow.get('human_nodes', []):
            config = nodes.get(node)
            if not isinstance(config, dict):
                return None, '请完成所有人工节点配置'
            rule_config = flow.get('node_rule_configs', {}).get(node, {})
            assignment_config = flow.get('node_assignment_configs', {}).get(node, {})
            if rule_config.get('mode') not in ('inherit', 'none') and not config.get('rule'):
                return None, '请为人工节点选择处理规则'
            if assignment_config.get('mode') != 'inherit':
                assignments = config.get('assignments')
                if not isinstance(assignments, list) or not assignments or any(not isinstance(a, dict) or a.get('type') not in ('supplier', 'user_group') or not isinstance(a.get('target'), str) or not a['target'].strip() for a in assignments):
                    return None, '请为人工节点配置处理人'
            percent = config.get('percent', 100)
            if type(percent) is not int or not 0 <= percent <= 100:
                return None, '处理比例请输入 0～100 的整数'
    priority = body.get('priority', 6)
    if type(priority) is not int or not 1 <= priority <= 9:
        return None, '优先级无效'
    category = body.get('category', 'formal')
    expected_mode = body.get('expected_mode', 'continuous')
    expected_value = body.get('expected_value')
    if category not in ('formal', 'informal') or expected_mode not in ('continuous', 'count', 'duration'):
        return None, '任务性质或预期任务量无效'
    if expected_mode == 'continuous':
        expected_value = None
    else:
        try:
            if isinstance(expected_value, bool):
                raise ValueError()
            expected_value = float(expected_value)
            if not math.isfinite(expected_value) or expected_value <= 0 or (expected_mode == 'count' and not expected_value.is_integer()):
                raise ValueError()
        except (ValueError, TypeError):
            return None, '请填写有效的预期任务量'
    return dict(name=name.strip(), source_ids=[t['id'] for t in tasks], project=tasks[0]['project'],
                filters=filters, stages=stages, configs=configs, priority=priority,
                category=category, expected_mode=expected_mode, expected_value=expected_value), None


def register_processing(app, flows):
    bp = Blueprint('collection_processing', __name__)

    @bp.errorhandler(404)
    def not_found(error):
        return jsonify(error=error.description), 404

    @bp.get(API + '/tasks')
    def list_jobs():
        task_id = request.args.get('collection')
        record_id = request.args.get('record')
        with collection.database() as conn:
            if task_id:
                task_id = collection.get_task(conn, task_id)['id']
            jobs = [job for job in all_jobs(conn) if not task_id or task_id in job['source_ids']]
            if record_id:
                jobs = [job for job in jobs if any(r['id'] == record_id and (not task_id or r['task_id'] == task_id) for r in job['records'])]
            return jsonify(tasks=[public_job(conn, job, task_id, record_id) for job in jobs])

    @bp.get(API + '/tasks/<job_id>')
    def detail(job_id):
        with collection.database() as conn:
            job = get_job(conn, job_id)
            return jsonify(task=public_job(conn, job), sources=[dict(id=t['id'], name=t['name']) for t in source_tasks(conn, job)])

    @bp.post(API + '/tasks')
    def create():
        body = request.get_json(silent=True)
        key = request.headers.get('Idempotency-Key', '')
        if not re.fullmatch('[A-Za-z0-9_-]{16,128}', key):
            return jsonify(error='创建请求标识无效，请刷新后重试'), 422
        fingerprint = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        with collection.database() as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            setup(conn)
            existing = conn.execute('SELECT payload, fingerprint FROM collection_processing WHERE request_key=?', (key,)).fetchone()
            if existing:
                if existing['fingerprint'] != fingerprint:
                    return jsonify(error='本次请求已创建成功，请先查看已创建任务'), 409
                return jsonify(task=public_job(conn, json.loads(existing['payload'])), replayed=True)
            data, error = validate(conn, body, flows)
            if error:
                return jsonify(error=error), 422
            ids = [int(row['id']) for row in conn.execute('SELECT id FROM collection_processing')]
            job_id = str(max([30000, *ids]) + 1)
            if len(job_id) > 5:
                return jsonify(error='处理任务编号已用完'), 409
            stamp = collection.now()
            data.update(id=job_id, published=False, enabled=True, revision=1, records=[], creator=collection.USER,
                        created_at=stamp, updated_at=stamp, events=[dict(at=stamp, title='创建处理任务', actor=collection.USER)])
            conn.execute('INSERT INTO collection_processing VALUES (?, ?, ?, ?)', (job_id, key, fingerprint, json.dumps(data, ensure_ascii=False)))
            return jsonify(task=public_job(conn, data)), 201

    @bp.post(API + '/tasks/<job_id>/action')
    def action(job_id):
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error='请求内容无效'), 422
        with collection.database() as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            job = get_job(conn, job_id)
            if type(body.get('revision')) is not int or body['revision'] != job['revision']:
                return jsonify(error='处理任务已更新，请刷新后重试'), 409
            action = body.get('action')
            if action == 'publish' and not job['published']:
                job['published'] = True
                admit(conn, job)
                title = '发布处理任务'
            elif action == 'admit' and job['published'] and job['enabled']:
                admit(conn, job)
                title = '纳入匹配数据'
            elif action in ('pause', 'resume') and job['published']:
                job['enabled'] = action == 'resume'
                title = '开启处理任务' if job['enabled'] else '关闭处理任务'
            else:
                return jsonify(error='当前状态不支持此操作'), 422
            job['revision'] += 1
            job['updated_at'] = collection.now()
            job['events'].append(dict(at=job['updated_at'], actor=collection.USER, title=title))
            save_job(conn, job)
            return jsonify(task=public_job(conn, job))

    @bp.patch(API + '/tasks/<job_id>')
    def edit(job_id):
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error='请求内容无效'), 422
        with collection.database() as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            job = get_job(conn, job_id)
            if type(body.get('revision')) is not int or body['revision'] != job['revision']:
                return jsonify(error='处理任务已更新，请刷新后重试'), 409
            if job['published']:
                return jsonify(error='任务已发布，配置不可直接覆盖，请创建新的处理任务'), 409
            data, error = validate(conn, body, flows)
            if error:
                return jsonify(error=error), 422
            if data['source_ids'] != job['source_ids']:
                return jsonify(error='来源采集任务不可更改，请创建新的处理任务'), 422
            job.update(data, revision=job['revision'] + 1, updated_at=collection.now())
            job['events'].append(dict(at=job['updated_at'], actor=collection.USER, title='修改处理配置'))
            save_job(conn, job)
            return jsonify(task=public_job(conn, job))

    @app.after_request
    def inject_processing_link_ui(response):
        if request.path == '/data/processing-tasks' and response.status_code == 200 and response.mimetype == 'text/html':
            suffix = '<link rel="stylesheet" href="/static/post_training_collection/processing-links.css"><script src="/static/post_training_collection/processing-links.js" defer></script>'
            response.set_data(response.get_data(as_text=True).replace('</body>', suffix + '</body>'))
        return response

    app.register_blueprint(bp)
