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
from urllib.parse import quote, urlencode

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
    for member in job['records']:
        if (member.get('stages', {}).get('质检') == 'completed'
                and member.get('results', {}).get('质检', {}).get('conclusion') not in ('合格', '不合格', '失误')):
            raise ValueError('质检完成必须提供合格或不合格结论')
        for stage in member.get('stage_workflow', {}):
            if stage_position := member['stage_workflow'][stage]:
                ended = stage_position.get('node') == 'End'
                if ended != (member.get('stages', {}).get(stage) == 'completed'):
                    raise ValueError('环节完成状态必须与 End 节点一致')
                if ended and stage_position.get('status') != 'completed':
                    raise ValueError('End 节点必须处于完成状态')
    conn.execute('UPDATE collection_processing SET payload=? WHERE id=?', (json.dumps(job, ensure_ascii=False), job['id']))


def tokens(value):
    return [x.strip() for x in re.split('[,，、]', value) if x.strip()]


def matches(job, task, record):
    if record.get('upload') != 'uploaded':
        return False
    for field, operator, value, *scope in job['filters']:
        conclusion = record.get('collection_result')
        if conclusion not in ('success', 'failure') and isinstance(record.get('is_mistake'), bool):
            conclusion = 'failure' if record['is_mistake'] else 'success'
        actual = {'采集任务 ID': task['id'], '数据 ID': record['id'],
                  '采集员': record.get('operator', ''),
                  '采集结论': {'success': '成功', 'failure': '失败'}.get(conclusion, '')}.get(field, '')
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
    from collection_processing_scope import apply_upstream
    rows = [(task, record) for task in source_tasks(conn, job)
            for record in collection.public_task(task, detail=True)['records'] if matches(job, task, record)]
    return apply_upstream(conn, job, rows)


def admit(conn, job, task_id=None):
    existing = {(r['task_id'], r['id']) for r in job['records']}
    for task, record in candidates(conn, job):
        if task_id and task['id'] != task_id:
            continue
        key = (task['id'], record['id'])
        if key not in existing:
            job['records'].append({'id': record['id'], 'task_id': task['id'],
                                   'admitted_at': collection.now(),
                                   'stages': {stage: 'pending' for stage in job['stages']}})
            existing.add(key)


def public_job(conn, job, task_id=None, record_id=None):
    from collection_processing_scope import stage_finished
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
        done = sum(stage_finished(r, stage) for r in selected)
        running = any(r['stages'].get(stage) == 'processing' for r in selected)
        state = ('draft' if not job['published'] else 'paused' if not job['enabled'] else
                 'waiting' if not selected else 'completed' if done == len(selected) else
                 'processing' if running or done else 'pending')
        result['stage_progress'].append(dict(stage=stage, done=done, total=len(selected), status=state, label=STATES[state]))
    result['status'] = ('draft' if not job['published'] else 'paused' if not job['enabled'] else
                        'waiting' if not selected else 'completed' if all(p['done'] == len(selected) for p in result['stage_progress']) else
                        'processing' if any(p['status'] == 'processing' for p in result['stage_progress']) else 'pending')
    result['status_label'] = STATES[result['status']]
    result['href'] = '/data/tasks/' + quote(job['id'], safe='')
    params = {}
    if task_id:
        params['collection'] = task_id
    if record_id:
        params['data_id'] = record_id
    if params:
        result['href'] += '?' + urlencode(params)
    result.pop('request_key', None)
    from collection_processing_scope import enrich_job
    enrich_job(result, job, selected)
    if task_id and record_id and len(selected) == 1:
        from collection_processing_scope import recording_stage_details
        result['record_stages'] = recording_stage_details(job, selected[0])
    return result


def task_data_context(conn, job):
    """Adapt persisted membership to the existing task-data renderer, without
    inventing quality verdicts, workflow nodes or workbench assignments.
    """
    from collection_processing_scope import quality_result, record_state, stage_finished, current_business_position
    sources = source_tasks(conn, job)
    source_records = {(task['id'], record['id']): record
                      for task in sources for record in collection.public_task(task, detail=True)['records']}
    public = public_job(conn, job)
    records = []
    labels = {'pending': '待处理', 'processing': '处理中', 'completed': '已完成', 'paused': '已暂停'}
    for member in job['records']:
        record = source_records.get((member['task_id'], member['id']), {})
        conclusion = record.get('collection_result', record.get('result'))
        if conclusion not in ('success', 'failure') and isinstance(record.get('is_mistake'), bool):
            conclusion = 'failure' if record['is_mistake'] else 'success'
        current_stage, current_node = current_business_position(job, member)
        records.append(dict(
            id=member['id'], task_id=member['task_id'],
            device=record.get('device', '-'),
            collection={'success': '成功', 'failure': '失败'}.get(conclusion, '-'),
            quality=(quality_result(member) or '未完成') if '质检' in job['stages'] else '-',
            annotation=('已标注' if stage_finished(member, '标注') else '标注中' if member['stages'].get('标注') == 'processing' else '未标注') if '标注' in member['stages'] else '-',
            stage_states=[(stage, labels.get(state, '-')) for stage, state in member['stages'].items()],
            current_stage=current_stage, node=current_node,
        ))
    completed = sum(record_state(member) == 'completed' for member in job['records'])
    task = dict(id=job['id'], name=job['name'], type='data_processing_task',
                status={'processing': 'in_progress', 'completed': 'succeeded', 'draft': 'unpublished',
                        'paused': '已关闭', 'waiting': '等待数据'}.get(public['status'], public['status']),
                input_count=len(records), processed_count=completed,
                backlog_count=len(records)-completed,
                flow_bindings=[(stage, flow, '') for stage, flow in job['stages'].items()],
                source_tasks=[dict(id=source['id'], name=source['name']) for source in sources])
    task['processing_job'] = public
    return task, records


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
    upstream_id = body.get('upstream_id', '')
    upstream_result = body.get('upstream_result', '合格')
    if upstream_id:
        upstream = next((j for j in all_jobs(conn) if j['id'] == upstream_id), None)
        if not upstream or not upstream['published'] or '质检' not in upstream['stages'] or upstream['project'] != tasks[0]['project']:
            return None, '请选择同一项目已发布的上游质检任务'
        if not set(t['id'] for t in tasks).issubset(upstream['source_ids']) or upstream_result not in ('合格', '不合格', '失误'):
            return None, '上游质检任务的来源范围或结论无效'
        if body.get('id') == upstream_id:
            return None, '不能依赖当前处理任务'
    return dict(name=name.strip(), source_ids=[t['id'] for t in tasks], project=tasks[0]['project'],
                upstream_id=upstream_id, upstream_result=upstream_result,
                filters=filters, stages=stages, configs=configs, priority=priority,
                stage_nodes={stage: list(next(f for f in flows if f['stage'] == stage and f['name'] == name).get('human_nodes') or [stage+'执行']) for stage, name in stages.items()},
                category=category, expected_mode=expected_mode, expected_value=expected_value), None


def register_processing(app, flows):
    bp = Blueprint('collection_processing', __name__)

    @app.before_request
    def refresh_continuous_inputs():
        # Local demonstration of continuous intake. Production scheduling stays
        # in the processing service; users never have to confirm each batch.
        if request.method != 'GET' or not (request.path.startswith(collection.API) or request.path.startswith('/data/tasks/') or request.path == '/data/processing-tasks'):
            return
        with collection.database() as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            for job in all_jobs(conn):
                if job['published'] and job['enabled']:
                    previous = len(job['records'])
                    admit(conn, job)
                    if len(job['records']) != previous:
                        save_job(conn, job)

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

    @bp.get(API + '/tasks/<job_id>/records/<source_id>/<record_id>')
    def record_detail(job_id, source_id, record_id):
        from collection_processing_scope import detail_payload
        with collection.database() as conn:
            result = detail_payload(conn, get_job(conn, job_id), source_id, record_id)
            if result is None:
                return jsonify(error='该数据尚未纳入当前处理任务'), 404
            return jsonify(record=result)

    @bp.post(API + '/preview')
    def preview():
        body = request.get_json(silent=True)
        with collection.database() as conn:
            data, error = validate(conn, body, flows)
            if error:
                return jsonify(error=error), 422
            rows = candidates(conn, data)
            return jsonify(count=len(rows), sources=[dict(id=t['id'], name=t['name'], count=sum(s['id'] == t['id'] for s, _ in rows)) for t in source_tasks(conn, data)])

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
                expected = body.get('expected_count')
                if expected is not None and expected != len(candidates(conn, job)):
                    return jsonify(error='匹配数量已变化，请刷新后重新确认'), 409
                job['published'] = True
                admit(conn, job)
                title = '发布处理任务'
            elif action == 'admit' and job['published'] and job['enabled']:
                source_id = body.get('collection_id')
                if source_id and source_id not in job['source_ids']:
                    return jsonify(error='来源采集任务不属于当前处理任务'), 422
                current = public_job(conn, job, source_id)
                if body.get('expected_count') is not None and body['expected_count'] != current['new_count']:
                    return jsonify(error='待纳入数量已变化，请刷新后重新确认'), 409
                admit(conn, job, source_id)
                title = '纳入匹配数据'
            elif action in ('pause', 'resume') and job['published']:
                job['enabled'] = action == 'resume'
                if action == 'pause':
                    mode = body.get('existing_mode', 'continue')
                    if mode not in ('continue', 'pause'):
                        return jsonify(error='请选择已有数据处理方式'), 422
                    job['existing_mode'] = mode
                    if mode == 'pause':
                        for member in job['records']:
                            member['paused_stages'] = {k: v for k, v in member['stages'].items() if v in ('pending', 'processing')}
                            for stage in member['paused_stages']:
                                member['stages'][stage] = 'paused'
                else:
                    for member in job['records']:
                        member['stages'].update(member.pop('paused_stages', {}))
                    admit(conn, job)
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
            if job['published'] and set(body) <= {'revision', 'priority', 'expected_value'}:
                proposed = dict(job, **{key: value for key, value in body.items() if key != 'revision'})
                data, error = validate(conn, proposed, flows)
                if error:
                    return jsonify(error=error), 422
                job.update(priority=data['priority'], expected_value=data['expected_value'],
                           revision=job['revision'] + 1, updated_at=collection.now())
                job['events'].append(dict(at=job['updated_at'], actor=collection.USER, title='调整处理任务优先级或预期量'))
                save_job(conn, job)
                return jsonify(task=public_job(conn, job))
            if job['published']:
                return jsonify(error='任务已发布，配置不可直接覆盖，请创建新的处理任务'), 409
            data, error = validate(conn, body, flows)
            if error:
                return jsonify(error=error), 422
            if data.get('upstream_id') == job['id']:
                return jsonify(error='不能依赖当前处理任务'), 422
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
