"""Shared recording membership, results and scoped views for the collection handoff."""
import copy
from urllib.parse import urlencode

LABELS = {'pending': '待处理', 'processing': '处理中', 'completed': '已完成', 'paused': '已暂停'}


def stage_position(member, stage):
    position = member.get('stage_workflow', {}).get(stage)
    if position:
        return position
    state = member.get('stages', {}).get(stage, 'pending')
    return dict(node='End' if state == 'completed' else None, status=state)


def stage_finished(member, stage):
    return (member.get('stages', {}).get(stage) != 'paused'
            and stage_position(member, stage).get('node') == 'End'
            and stage_position(member, stage).get('status') == 'completed'
            and (stage != '质检' or member.get('results', {}).get(stage, {}).get('conclusion') in ('合格', '不合格', '失误')))


def stage_nodes(job, stage):
    return job.get('stage_nodes', {}).get(stage) or list(job.get('configs', {}).get(stage, {})) or [stage + '执行']


def business_node_label(stage, node):
    if not node or str(node).lower() in ('start', 'end', '开始', '结束'):
        return '-'
    return stage + '验收' if any(word in str(node) for word in ('验收', '审核', '复核', '抽验', '抽检')) else stage


def current_business_position(job, member):
    """One recording occupies one business stage and one business node."""
    ordered = [stage for stage in ('质检', '标注') if stage in job['stages']]
    for stage in ordered:
        if stage_finished(member, stage):
            continue
        position = stage_position(member, stage)
        node = position.get('node')
        if not node:
            node = member.get('current_node') if member.get('current_stage') == stage else None
        node = node or stage_nodes(job, stage)[0]
        return stage, business_node_label(stage, node)
    return '', '-'


def node_progress(job, members, stage):
    nodes = stage_nodes(job, stage)
    counts = {node: {} for node in [*nodes, 'End']}
    for member in members:
        position = stage_position(member, stage)
        node = 'End' if stage_finished(member, stage) else position.get('node')
        node = node if node in nodes or node == 'End' and stage_finished(member, stage) else nodes[0]
        status = position.get('status', 'pending')
        if node == 'End':
            label = quality_result(member) if stage == '质检' else '已完成'
        elif status in ('rejected', 'rework'):
            label = '驳回返工'
        elif status == 'paused' or member.get('stages', {}).get(stage) == 'paused':
            label = '已暂停'
        elif any(word in node for word in ('验收', '审核', '复核', '抽验', '抽检')):
            label = '验收中' if status == 'processing' else '待验收'
        else:
            label = '执行中' if status == 'processing' else '待执行'
        counts[node][label] = counts[node].get(label, 0) + 1
    return [dict(node=node, total=sum(values.values()), states=[dict(label=key, count=value) for key, value in values.items()]) for node, values in counts.items()]


def business_nodes(nodes, stage):
    grouped = {}
    for node in nodes:
        if node['node'] == 'End':
            continue
        label = business_node_label(stage, node['node'])
        values = grouped.setdefault(label, {})
        for state in node['states']:
            values[state['label']] = values.get(state['label'], 0) + state['count']
    return [dict(node=node, total=sum(values.values()), states=[dict(label=key, count=value) for key, value in values.items()]) for node, values in grouped.items()]


def record_state(member):
    states = list(member.get('stages', {}).values())
    if states and all(stage_finished(member, stage) for stage in member['stages']):
        return 'completed'
    if 'paused' in states:
        return 'paused'
    return 'processing' if any(s in ('processing', 'completed') for s in states) else 'pending'


def progress(job, members):
    rows = []
    for stage in job['stages']:
        done = sum(stage_finished(m, stage) for m in members)
        running = sum(m.get('stages', {}).get(stage) == 'processing' for m in members)
        paused = any(m.get('stages', {}).get(stage) == 'paused' for m in members)
        passed = sum(quality_result(m) == '合格' for m in members) if stage == '质检' else 0
        failed = sum(quality_result(m) == '不合格' for m in members) if stage == '质检' else 0
        mistake = sum(quality_result(m) == '失误' for m in members) if stage == '质检' else 0
        if stage == '质检':
            done = passed + failed + mistake
        state = 'waiting' if not members else 'completed' if done == len(members) else 'paused' if paused else 'processing' if running or done else 'pending'
        nodes = node_progress(job, members, stage)
        def started(member):
            if stage_finished(member, stage):
                return False
            state = member.get('stages', {}).get(stage, 'pending')
            if state == 'paused':
                state = member.get('paused_stages', {}).get(stage, 'pending')
            position = stage_position(member, stage)
            return (state in ('processing', 'completed', 'rework', 'rejected')
                    or position.get('status') in ('processing', 'rework', 'rejected')
                    or position.get('node') not in (None, '', stage_nodes(job, stage)[0]))
        in_progress = sum(started(member) for member in members)
        rows.append(dict(stage=stage, done=done, running=running, total=len(members), status=state,
                         in_progress=in_progress, unprocessed=len(members)-done-in_progress,
                         passed=passed, failed=failed, mistake=mistake, unchecked=len(members)-done if stage == '质检' else 0,
                         nodes=nodes, business_nodes=business_nodes(nodes, stage),
                         label={'waiting': '暂无数据', **LABELS}.get(state, state)))
    status = 'waiting' if not members else 'completed' if all(r['done'] == len(members) for r in rows) else 'paused' if any(r['status'] == 'paused' for r in rows) else 'processing' if any(r['status'] == 'processing' for r in rows) else 'pending'
    return rows, status


def recording_stage_details(job, member):
    """Keep a recording's workflow position separate from its final result."""
    rows = []
    upstream_finished = True
    for stage in ('质检', '标注'):
        if stage not in job['stages']:
            continue
        finished = stage_finished(member, stage)
        position = stage_position(member, stage)
        node = position.get('node') or stage_nodes(job, stage)[0]
        if finished:
            execution = '已完成'
        elif not upstream_finished:
            execution = '等待前序完成'
        else:
            states = node_progress(job, [member], stage)
            execution = next((state['label'] for item in states for state in item['states']), '待执行')
        result = (quality_result(member) or '未完成') if stage == '质检' else ('已完成' if finished else '未完成')
        rows.append(dict(stage=stage, node='-' if finished else business_node_label(stage, node),
                         execution=execution, result=result))
        upstream_finished = upstream_finished and finished
    return rows


def enrich_job(result, job, selected):
    rows, state = progress(job, selected)
    all_rows, all_state = progress(job, job['records'])
    result.update(stage_progress=rows, scope_status=state, overall_stage_progress=all_rows,
                  task_status='draft' if not job['published'] else 'paused' if not job['enabled'] else all_state)
    result['task_status_label'] = {**LABELS, 'draft': '未发布', 'paused': '停止接数', 'waiting': '等待数据'}[result['task_status']]
    result['scope_status_label'] = {'waiting': '暂无数据', **LABELS}[state]
    result['completed_count'] = sum(record_state(m) == 'completed' for m in selected)
    result['running_count'] = sum(record_state(m) == 'processing' for m in selected)
    result['pending_count'] = sum(record_state(m) == 'pending' for m in selected)
    result['new_count'] = result.get('new_count', 0)
    result['can_manage'] = True  # Local demo identity; production authorization remains server-owned.
    return result


def quality_result(member):
    value = member.get('results', {}).get('质检', {})
    conclusion = value.get('conclusion') if stage_finished(member, '质检') else None
    return conclusion if conclusion in ('合格', '不合格', '失误') else None


def dataset(conn, job, mode='admitted'):
    import collection_processing as processing
    import post_training_collection as collection
    sources = processing.source_tasks(conn, job)
    members = {(r['task_id'], r['id']): r for r in job['records']}
    raw = {(t['id'], r['id']): (t, r) for t in sources for r in collection.public_task(t, detail=True)['records']}
    candidates = {(t['id'], r['id']) for t, r in processing.candidates(conn, job)}
    if mode == 'admitted':
        keys = list(members)
    elif mode == 'pending':
        keys = [k for k in raw if k in candidates and k not in members]
    elif mode == 'excluded':
        keys = [k for k in raw if k not in candidates and k not in members]
    else:
        keys = [k for k in raw if k in candidates]
    records = []
    for key in keys:
        member = members.get(key)
        source, recording = raw.get(key, ({'id': key[0], 'name': key[0]}, {'id': key[1]}))
        conclusion = recording.get('collection_result')
        if conclusion not in ('success', 'failure') and isinstance(recording.get('is_mistake'), bool):
            conclusion = 'failure' if recording['is_mistake'] else 'success'
        quality = quality_result(member) if member else None
        def stage_result(stage):
            if stage not in job['stages']:
                return '-'
            if stage == '质检':
                return quality or '未完成'
            return '已完成' if member and stage_finished(member, stage) else '未完成'
        records.append(dict(id=key[1], task_id=key[0], source_name=source['name'], device=recording.get('device', '-'),
                            collection={'success': '成功', 'failure': '失败'}.get(conclusion, '-'),
                            state=record_state(member) if member else 'not_admitted', admitted=bool(member),
                            stage_states=[(s, LABELS.get(v, v)) for s, v in (member or {}).get('stages', {}).items()],
                            quality=stage_result('质检'), annotation=stage_result('标注'),
                            reason='' if member or key in candidates else '尚未上传完成' if recording.get('upload') != 'uploaded' else '不符合筛选条件' if not job.get('upstream_id') else '上游结果未满足条件',
                            recording=recording, member=copy.deepcopy(member)))
    return records


def detail_payload(conn, job, source_id, record_id):
    rows = dataset(conn, job)
    row = next((r for r in rows if r['task_id'] == source_id and r['id'] == record_id), None)
    if not row:
        return None
    row.update(processing_id=job['id'], processing_name=job['name'], stages=job['stages'], configs=job['configs'])
    return row


def apply_upstream(conn, job, rows):
    if not job.get('upstream_id'):
        return rows
    import collection_processing as processing
    upstream = processing.get_job(conn, job['upstream_id'])
    accepted = {(m['task_id'], m['id']) for m in upstream['records'] if quality_result(m) == job.get('upstream_result', '合格')}
    return [(t, r) for t, r in rows if (t['id'], r['id']) in accepted]


def safe_return(value, fallback):
    from urllib.parse import urlsplit
    if not isinstance(value, str) or '\\' in value or any(ord(c) < 32 for c in value):
        return fallback
    try:
        parsed = urlsplit(value)
    except ValueError:
        return fallback
    if parsed.scheme or parsed.netloc or not parsed.path.startswith(('/data/tasks/', '/data/post-training-collection/')):
        return fallback
    return value


def data_url(job_id, source='', mode='admitted', **extra):
    params = {'collection': source, 'scope': mode, **extra}
    return '/data/tasks/' + job_id + '?' + urlencode({k: v for k, v in params.items() if v not in ('', None)})
