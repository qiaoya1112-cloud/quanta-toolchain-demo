"""Two views of the same owned task-pool work, with atomic filtered claims."""
from collections import OrderedDict
from datetime import datetime
from urllib.parse import urlencode
from uuid import uuid4
from zoneinfo import ZoneInfo
from flask import abort, jsonify, redirect, render_template, request, session
import workbench_pool as pools


def register_job_centers(app, render_page, tasks, db_path, owner, records_for, history_for, rule_names):
    nodes = sorted((dict(task, execution_unit=task.get('execution_unit', 'single'),
                         batch_size=task.get('batch_size', 3)) for task in tasks if task.get('v2_only')),
                   key=lambda task: (not task['id'].startswith('WB-PRETRAINING'), task['processing_task'], task['id'] != 'WB-PRETRAINING-QC', task['id']))
    by_id = {task['id']: task for task in nodes}

    def node(task_id):
        if task_id not in by_id:
            abort(404)
        return by_id[task_id]

    def valid_center(center):
        if center not in (1, 2):
            abort(404)

    def conditions(center, task_id):
        return session.get('job_center_conditions', {}).get(f'{center}:{task_id}', {})

    def matches(record, filters):
        fields = {
            'collection_task_id': [record['task_id']],
            'operator': [record.get('collector', ''), record.get('collector_id', ''),
                         record.get('self_checker', ''), record.get('self_checker_id', ''),
                         record.get('collection_qc_operator', ''), record.get('collection_qc_operator_id', '')],
            'supplier': [record.get('supplier', ''), record.get('supplier_id', '')],
        }
        return all(not value or any(value.lower() in str(item).lower() for item in fields[key]) for key, value in filters.items())

    def available(record):
        return record['status'] == 'pending' or (record['status'] == 'processing' and not record.get('owner'))

    def units(center, task, records):
        result = OrderedDict()
        for record in records:
            if record['status'] != 'processing' or record.get('owner') != owner():
                continue
            key = record.get('job_batch') or record['id']
            if key not in result:
                result[key] = {'id': key, 'record_ids': [], 'collection_task_id': record['task_id'],
                               'supplier': record['supplier'], 'operator': record['collector'],
                               'claimed_at': record.get('claimed_at', '—'),
                               'source_action': record.get('source_action', '领取'),
                               'description': record.get('explanation', record.get('description', '—')),
                               'current_round': record.get('current_round', 1),
                               'updated_at': record.get('updated_at', record.get('claimed_at', '—')),
                               'url': f'/data/job-centers/{center}/process?' + urlencode({'task': task['id'], 'unit': key})}
            result[key]['record_ids'].append(record['id'])
            result[key]['supplier'] = '、'.join(dict.fromkeys(result[key]['supplier'].split('、') + [record['supplier']]))
            result[key]['operator'] = '、'.join(dict.fromkeys(result[key]['operator'].split('、') + [record['collector']]))
            result[key]['source_action'] = '、'.join(dict.fromkeys(result[key]['source_action'].split('、') + [record.get('source_action', '领取')]))
        return list(result.values())

    def snapshot(center, selected):
        groups = OrderedDict()
        selected_records = []
        for task in nodes:
            records = records_for(task)
            count = sum(item['status'] != 'completed' and item.get('owner') in (None, '', owner()) for item in records)
            key = task['processing_task'] if center == 1 else task['flow']
            title = ({'20456': '预训练数据质检任务', '20455': '端到端切分标注任务'}.get(key, task['task_name']) if center == 1 else key)
            group = groups.setdefault(key, {'id': key, 'name': title, 'count': 0, 'nodes': []})
            group['count'] += count
            group['nodes'].append({'id': task['id'], 'name': task['node'], 'group': task['user_group'], 'count': count})
            if task['id'] == selected['id']:
                selected_records = history_for(task, records)
        filters = conditions(center, selected['id'])
        return {'center': center, 'groups': list(groups.values()), 'task': selected,
                'conditions': filters, 'jobs': units(center, selected, selected_records),
                'available': sum(available(item) and matches(item, filters) for item in selected_records)}

    @app.get('/data/job-centers/<int:center>')
    def job_center_home(center):
        valid_center(center)
        task = node(request.args.get('task', nodes[0]['id']))
        payload = snapshot(center, task)
        content = render_template('job_centers/home.html', payload=payload, reasons=pools.REJECTION_REASONS)
        return render_page(f'作业中心{center}', content, active=f'/data/job-centers/{center}', module='data',
                           breadcrumb=f'数据平台 / <b>作业中心{center}</b>')

    @app.route('/data/job-centers/<int:center>/state', methods=['GET', 'POST'])
    def job_center_state(center):
        valid_center(center)
        task = node(request.args.get('task', nodes[0]['id']))
        if request.method == 'POST':
            body = request.get_json(silent=True)
            if not isinstance(body, dict) or set(body) - {'collection_task_id', 'operator', 'supplier'} or any(not isinstance(value, str) or len(value)>200 for value in body.values()):
                return jsonify(error='请输入有效的领取条件'), 400
            saved = dict(session.get('job_center_conditions', {}))
            saved[f'{center}:{task["id"]}'] = {key: value.strip() for key, value in body.items() if value.strip()}
            session['job_center_conditions'] = saved
        return jsonify(snapshot(center, task))

    @app.post('/data/job-centers/<int:center>/claim')
    def job_center_claim(center):
        valid_center(center)
        task = node(request.args.get('task', nodes[0]['id']))
        # Candidate selection and ownership changes share one database transaction.
        history = {item['id']: item for item in history_for(task, records_for(task))}
        with pools.shared_state(db_path(), task, session.get('workbench_pool_states', {}), owner()) as saved:
            records = [dict(item, **{key: value for key, value in history[item['id']].items() if key.startswith('collection_qc_')})
                       for item in pools.pool_records(task, saved)]
            candidates = [item for item in records if available(item) and matches(item, conditions(center, task['id']))]
            count = task['batch_size'] if task['execution_unit'] == 'batch' else 1
            ids = [item['id'] for item in candidates[:count]]
            if not ids:
                return jsonify(error='当前领取条件下暂无可领取数据'), 409
            updated = pools.transition(task, saved, 'start', ids, owner=owner())
            batch = uuid4().hex
            scope = task['pool'] + ':' + task['id']
            for record_id in ids:
                updated[scope][record_id].update(job_batch=batch, claimed_at=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'))
            saved.update(updated)
        return jsonify(dict(snapshot(center, task), claimed=len(ids)))

    def owned_unit(task, unit):
        records = history_for(task, records_for(task))
        selected = [record for record in records if (record.get('job_batch') or record['id']) == unit]
        if not selected or any(record.get('owner') != owner() for record in selected):
            abort(404)
        return [record for record in selected if record['status'] == 'processing']

    @app.get('/data/job-centers/<int:center>/process')
    def job_center_process(center):
        valid_center(center)
        task = node(request.args.get('task', ''))
        unit = request.args.get('unit', '')
        records = owned_unit(task, unit)
        if not records:
            return redirect(f'/data/job-centers/{center}?' + urlencode({'task': task['id']}))
        if task['execution_unit'] == 'single':
            return redirect(editor_url(center, task, records[0]['id']))
        task = dict(task, job_center=center, job_batch=unit, hide_status=True,
                    selected_rule=next(iter(rule_names(task)), ''),
                    process_url=f'/data/job-centers/{center}/record?'+urlencode({'task':task['id'], 'unit':unit}))
        content = render_template('workbench_pool/list.html', task=task,
                                  records=pools.public_records(records, owner()), reasons=pools.REJECTION_REASONS, notice='')
        return render_page('批量作业数据列表', content, active=f'/data/job-centers/{center}', module='data')

    def editor_url(center, task, record_id):
        return '/data/workbench-v2/edit?' + urlencode({'task': task['id'], 'pool_id':task['pool'],
            'recording_id':record_id, 'job_center':center, 'mode':'annotation' if task['stage']=='标注' else 'quality'})

    @app.get('/data/job-centers/<int:center>/details')
    def job_center_details(center):
        valid_center(center)
        task = node(request.args.get('task', ''))
        if task['execution_unit'] != 'batch':
            abort(404)
        unit = request.args.get('unit', '')
        records = owned_unit(task, unit)
        view_task = dict(task, job_center=center, job_batch=unit, hide_status=True,
                         process_url=f'/data/job-centers/{center}/record?' + urlencode({'task': task['id'], 'unit': unit}))
        return jsonify(task=view_task, records=pools.public_records(records, owner()))

    @app.get('/data/job-centers/<int:center>/record')
    def job_center_record(center):
        valid_center(center)
        task = node(request.args.get('task', ''))
        records = owned_unit(task, request.args.get('unit', ''))
        record_id = request.args.get('recording_id', '')
        if not any(record['id'] == record_id for record in records):
            abort(404)
        return redirect(editor_url(center, task, record_id))
