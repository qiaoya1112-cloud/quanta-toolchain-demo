"""Repeatable synthetic fixtures for the collection demo, including fresh deployments."""
import copy
import hashlib
import json
import os
from datetime import datetime, timedelta

import click
from flask import current_app, request

import collection_processing as processing
import post_training_collection as collection


FIXTURE = 'collection-linked-demo-20261026'
PROCESSING_FIXTURE = FIXTURE + '-compact-v2'
MULTI_FIXTURE = FIXTURE + '-multi-source-v1'
WORKFLOW_FIXTURE = FIXTURE + '-end-nodes-v1'


def set_demo_quality_result(record, position):
    if record.get('stages', {}).get('质检') == 'completed':
        record.setdefault('results', {})['质检'] = dict(
            conclusion='不合格' if position % 3 == 2 else '合格',
            completed_at=record['admitted_at'])


def repair_demo_quality_results(conn):
    """Repair only synthetic fixture members, preserving existing verdicts."""
    repaired = 0
    for job in processing.all_jobs(conn):
        if job.get('demo_fixture') not in (FIXTURE, MULTI_FIXTURE):
            continue
        changed = False
        positions = {}
        for record in job['records']:
            position = positions.get(record['task_id'], 0)
            positions[record['task_id']] = position + 1
            if (record['id'].startswith('DEMO-R-') and record.get('stages', {}).get('质检') == 'completed'
                    and record.get('results', {}).get('质检', {}).get('conclusion') not in ('合格', '不合格', '失误')):
                set_demo_quality_result(record, position)
                repaired += 1
                changed = True
        if changed:
            processing.save_job(conn, job)
    return repaired


def seed_workflow_example(conn, flows):
    if conn.execute('SELECT 1 FROM collection_meta WHERE key=?', (WORKFLOW_FIXTURE,)).fetchone():
        return
    quality = next((f for f in flows if f['stage'] == '质检' and f.get('human_nodes') and len(f['human_nodes']) > 1), None)
    annotation = next((f for f in flows if f['stage'] == '标注' and len(f.get('human_nodes', [])) > 1), None)
    if not quality or not annotation:
        return
    for job in processing.all_jobs(conn):
        if job.get('demo_fixture') != MULTI_FIXTURE or job['name'] != '饮料取放动作标注' or job.get('revision') != 1:
            continue
        # Prefer the existing two-node flows when present; never invent nodes.
        quality = next((f for f in flows if f['stage'] == '质检' and len(f.get('human_nodes', [])) == 2), quality)
        annotation = next((f for f in flows if f['stage'] == '标注' and len(f.get('human_nodes', [])) == 2), annotation)
        job.update(name='饮料取放质检与标注', stages={'质检':quality['name'], '标注':annotation['name']},
                   stage_nodes={'质检': quality['human_nodes'], '标注': annotation['human_nodes']},
                   configs={stage: {node: dict(rule='通用质检规则' if stage == '质检' else '通用动作标注规则', percent=100,
                             assignments=[dict(type='user_group', target='质检复核用户组' if stage == '质检' else '标注员用户组')])
                             for node in flow['human_nodes']} for stage, flow in [('质检',quality), ('标注',annotation)]})
        positions = {}
        for record in job['records']:
            index = positions.get(record['task_id'], 0)
            positions[record['task_id']] = index + 1
            record['stages'] = {'质检':'completed' if index < 2 else 'processing',
                                '标注':'completed' if index == 0 else 'processing' if index == 1 else 'pending'}
            record['stage_workflow'] = {
                '质检': dict(node='End' if index < 2 else quality['human_nodes'][-1] if index == 2 else quality['human_nodes'][0],
                           status='completed' if index < 2 else 'pending' if index == 2 else 'rework'),
                '标注': dict(node='End' if index == 0 else annotation['human_nodes'][-1] if index == 1 else annotation['human_nodes'][0],
                           status='completed' if index == 0 else 'pending')}
            record['results'] = {'质检': {'conclusion':'合格'}} if index < 2 else {}
        processing.save_job(conn, job)
    conn.execute('INSERT INTO collection_meta VALUES (?, ?)', (WORKFLOW_FIXTURE, '1'))


def seed_multi_task_examples(conn, flows):
    """Two shared jobs demonstrate multiple sources without a long fake list."""
    if conn.execute('SELECT 1 FROM collection_meta WHERE key=?', (MULTI_FIXTURE,)).fetchone():
        return 0
    tasks = []
    for task_id in ['02601', '02607']:
        row = conn.execute('SELECT payload FROM collection_tasks WHERE id=?', (task_id,)).fetchone()
        if row:
            task = json.loads(row['payload'])
            if any(record['id'].startswith('DEMO-R-') for record in task['records']):
                tasks.append(task)
    if len(tasks) != 2 or len({task['project'] for task in tasks}) != 1:
        return 0
    automatic = next(f for f in flows if f['stage'] == '质检' and not f.get('human_nodes'))
    annotation = next((f for f in flows if f['name'] == '双轮人工标注流程'),
                      next((f for f in flows if f['stage'] == '标注'), None))
    source_ids = [task['id'] for task in tasks]
    for index, (name, flow, state) in enumerate([
            ('饮料取放数据质检', automatic, 'processing'),
            ('饮料取放动作标注', annotation, 'pending')]):
        if not flow:
            continue
        records = [(task, record) for task in tasks
                   for record in [r for r in task['records'] if r['upload'] == 'uploaded'][:8 if index == 0 else 4]]
        filters = [['采集任务 ID', '等于', ','.join(source_ids)],
                   ['数据 ID', '等于', ','.join(record['id'] for _, record in records)]]
        configs = {flow['stage']: {node: dict(rule='通用动作标注规则', percent=100,
            assignments=[dict(type='user_group', target='标注抽验员用户组' if node == '抽验' else '标注员用户组')])
            for node in flow.get('human_nodes', [])}}
        job, error = processing.validate(conn, dict(name=name, source_ids=source_ids, priority=6,
            filters=filters, stages={flow['stage']: flow['name']}, configs=configs), flows)
        if error:
            raise ValueError(error)
        job_id = str(max([30000, *[int(r['id']) for r in conn.execute('SELECT id FROM collection_processing')]]) + 1)
        if len(job_id) > 5:
            raise ValueError('五位处理任务编号已用完')
        stamp = min(datetime.now(), max(datetime.fromisoformat(r['recorded_at']) for _, r in records)
                    + timedelta(minutes=10 + index * 20)).replace(microsecond=0).isoformat()
        job.update(id=job_id, published=True, enabled=True, revision=1, records=[],
            creator='joanna.qiao', created_at=stamp, updated_at=stamp, demo_fixture=MULTI_FIXTURE,
            events=[dict(at=stamp, actor='joanna.qiao', title='创建处理任务')])
        processing.admit(conn, job)
        per_source = {}
        for record in job['records']:
            position = per_source.get(record['task_id'], 0)
            per_source[record['task_id']] = position + 1
            record['admitted_at'] = stamp
            record['stages'][flow['stage']] = ('completed' if state == 'processing' and position < 3 else
                'processing' if state == 'processing' and position == 3 else 'pending')
            set_demo_quality_result(record, position)
        payload = json.dumps(job, ensure_ascii=False)
        conn.execute('INSERT INTO collection_processing VALUES (?, ?, ?, ?)',
            (job_id, MULTI_FIXTURE + '-' + str(index), hashlib.sha256(payload.encode()).hexdigest(), payload))
    conn.execute('INSERT INTO collection_meta VALUES (?, ?)', (MULTI_FIXTURE, '1'))
    return 2 if annotation else 1


def seed_processing_examples(conn, flows):
    """Replace only untouched examples owned by this fixture; keep user jobs."""
    if conn.execute('SELECT 1 FROM collection_meta WHERE key=?', (PROCESSING_FIXTURE,)).fetchone():
        return 0
    rows = conn.execute('SELECT id, fingerprint, payload FROM collection_processing ORDER BY id').fetchall()
    owned = [row for row in rows if json.loads(row['payload']).get('demo_fixture') == FIXTURE]
    untouched = [row for row in owned if json.loads(row['payload']).get('revision') == 1
                 and hashlib.sha256(row['payload'].encode()).hexdigest() == row['fingerprint']]
    automatic = next((f for f in flows if f['stage'] == '质检' and 'dagger' in f.get('id', '').lower()),
                     next(f for f in flows if f['stage'] == '质检' and not f.get('human_nodes')))
    annotation = next((f for f in flows if f['name'] == '双轮人工标注流程'),
                      next((f for f in flows if f['stage'] == '标注'), None))
    review = next((f for f in flows if f['stage'] == '质检' and f.get('human_nodes')), automatic)
    row = conn.execute('SELECT payload FROM collection_tasks WHERE id=?', ('02602',)).fetchone()
    if not row:
        return 0
    task = json.loads(row['payload'])
    plans = [('杯子抓取数据质检', 0, 10, 'processing', automatic),
             ('杯子抓取动作标注', 0, 6, 'pending', annotation),
             ('杯子抓取首批复核', 3, 6, 'completed', review)]
    # Old seed used ten numbered jobs. Reuse its first three IDs so existing
    # links survive, but never overwrite a fixture edited/published by a user.
    retained = {r['id'] for r in owned[:3]}
    for old in untouched:
        if old['id'] not in retained:
            conn.execute('DELETE FROM collection_processing WHERE id=?', (old['id'],))
    count = 0
    for index, (name, start, end, state, flow) in enumerate(plans):
        if not flow:
            continue
        old = owned[index] if index < len(owned) else None
        if old and old not in untouched:
            continue
        records = [r for r in task['records'] if r['upload'] == 'uploaded'][start:end]
        configs = {flow['stage']: {node: dict(
            rule='通用动作标注规则' if flow['stage'] == '标注' else '通用质检规则', percent=100,
            assignments=[dict(type='user_group', target=('标注抽验员用户组' if node == '抽验' else
                         '标注员用户组') if flow['stage'] == '标注' else '质检复核用户组')])
            for node in flow.get('human_nodes', [])}}
        filters = [['采集任务 ID', '等于', task['id']]]
        if records:
            filters.append(['数据 ID', '等于', ','.join(r['id'] for r in records)])
        job, error = processing.validate(conn, dict(name=name, source_ids=[task['id']],
            priority=[6, 6, 3][index], filters=filters, stages={flow['stage']: flow['name']}, configs=configs), flows)
        if error:
            raise ValueError(error)
        job_id = old['id'] if old else str(max([30000, *[int(r['id']) for r in
            conn.execute('SELECT id FROM collection_processing')]]) + 1)
        if len(job_id) > 5:
            raise ValueError('五位处理任务编号已用完')
        recorded = max([datetime.fromisoformat(r['recorded_at']) for r in records],
                       default=datetime.fromisoformat(task['created_at']))
        stamp = min(datetime.now(), recorded + timedelta(minutes=5 + index * 15)).replace(microsecond=0).isoformat()
        job.update(id=job_id, published=True, enabled=True, revision=1, records=[],
                   creator='joanna.qiao', created_at=stamp, updated_at=stamp, demo_fixture=FIXTURE,
                   events=[dict(at=stamp, actor='joanna.qiao', title='创建处理任务')])
        processing.admit(conn, job)
        for i, record in enumerate(job['records']):
            record['admitted_at'] = stamp
            record['stages'][flow['stage']] = ('completed' if state == 'completed' or state == 'processing' and i < 6 else
                                              'processing' if state == 'processing' and i == 6 else 'pending')
            set_demo_quality_result(record, i)
        payload = json.dumps(job, ensure_ascii=False)
        fingerprint = hashlib.sha256(payload.encode()).hexdigest()
        if old:
            conn.execute('UPDATE collection_processing SET fingerprint=?, payload=? WHERE id=?',
                         (fingerprint, payload, job_id))
        else:
            conn.execute('INSERT INTO collection_processing VALUES (?, ?, ?, ?)',
                         (job_id, FIXTURE + '-' + job_id, fingerprint, payload))
        count += 1
    conn.execute('INSERT INTO collection_meta VALUES (?, ?)', (PROCESSING_FIXTURE, str(count)))
    return count


def seed_demo(conn, flows):
    processing.setup(conn)
    if conn.execute('SELECT 1 FROM collection_meta WHERE key=?', (FIXTURE,)).fetchone():
        count = seed_processing_examples(conn, flows) + seed_multi_task_examples(conn, flows)
        repaired = repair_demo_quality_results(conn)
        seed_workflow_example(conn, flows)
        return dict(tasks=0, records=0, processing_tasks=count, repaired_quality_results=repaired, already_seeded=True)
    totals = dict(tasks=0, records=0, processing_tasks=0, already_seeded=False)
    templates = collection.seed_tasks(current_app.config['COLLECTION_PROJECTS'],
                                      current_app.config['COLLECTION_CHECKPOINTS'])
    samples = []
    # Extend only known synthetic fixtures; preserve manually created tasks.
    for tid in ['02601', '02602', '02603', '02604', '02607', '02608']:
        row = conn.execute('SELECT payload FROM collection_tasks WHERE id=?', (tid,)).fetchone()
        if row:
            task = json.loads(row['payload'])
            if any(r['id'].startswith('DEMO-R-') for r in task['records']):
                samples.append(task)

    names = ['餐桌餐具整理', '货架物品抓取', '快递包裹搬运', '客厅场景走查', '厨房台面整理', '抽屉取物待采']
    number = int(conn.execute("SELECT value FROM collection_meta WHERE key='next_task_id'").fetchone()['value'])
    if number + len(names) > 100000:
        raise ValueError('五位任务编号不足，无法添加演示任务')
    new_tasks = []
    projects = current_app.config['COLLECTION_PROJECTS']
    for i, name in enumerate(names):
        task = copy.deepcopy(templates[[0, 1, 0, 6, 1, 6][i]])
        task.update(id=f'{number+i:05d}', name=name, project=projects[i % len(projects)]['id'],
                    records=[], priority=[9, 6, 3][i % 3], expected_hours=[4, 8, 12][i % 3],
                    demo_fixture=FIXTURE, created_at=collection.now(), updated_at=collection.now())
        task['events'] = [dict(at=collection.now(), actor='demo', title='创建采集任务', detail='本地合成演示数据')]
        conn.execute('INSERT INTO collection_tasks VALUES (?, ?)', (task['id'], json.dumps(task, ensure_ascii=False)))
        new_tasks.append(task)
        if i != 5:
            samples.append(task)
    totals['tasks'] = len(new_tasks)
    conn.execute("UPDATE collection_meta SET value=? WHERE key='next_task_id'", (str(number + len(names)),))

    for task in samples:
        for i in range(36):
            seconds = (datetime.now() - timedelta(minutes=i*8)).replace(microsecond=0).isoformat()
            task['records'].append(dict(
                id=f"DEMO-R-EXTRA-{task['id']}-{i+1:04d}", task_id=task['id'],
                operator=collection.DEMO_PEOPLE[i % len(collection.DEMO_PEOPLE)],
                device=f"{'UDAS' if task['source']=='udas' else 'MOZ1'}-{i%3+1:03d}",
                recorded_at=seconds, seconds=95+i*11,
                upload='uploading' if i == 35 else 'failed' if i == 34 else 'uploaded',
                upload_error='网络中断，请在端侧重试' if i == 34 else '',
                collection_result='failure' if i % 5 == 2 else 'success',
                quality='pending', annotation='未标注',
                prompt=copy.deepcopy(task['prompts'][0]) if task['prompts'] else None,
                checkpoint=task['checkpoint'], demo_fixture=FIXTURE))
        conn.execute('UPDATE collection_tasks SET payload=? WHERE id=?', (json.dumps(task, ensure_ascii=False), task['id']))
        totals['records'] += 36

    totals['processing_tasks'] = seed_processing_examples(conn, flows)
    totals['processing_tasks'] += seed_multi_task_examples(conn, flows)
    seed_workflow_example(conn, flows)
    conn.execute('INSERT INTO collection_meta VALUES (?, ?)', (FIXTURE, json.dumps(totals)))
    return totals


def register_demo_seed(app, flows):
    app.config.setdefault('COLLECTION_DEMO_AUTO_SEED',
                          os.environ.get('COLLECTION_DEMO_AUTO_SEED', '1').lower() not in ('0', 'false', 'no'))
    initialized = set()

    @app.before_request
    def initialize_collection_demo():
        # Fresh deployments must show the same examples as local previews.
        # Tests retain explicit fixtures; operators can disable automatic demo data.
        if app.testing or not app.config['COLLECTION_DEMO_AUTO_SEED'] or request.method != 'GET':
            return
        if not (request.path.startswith(collection.BASE) or request.path.startswith(collection.API)
                or request.path == '/data/processing-tasks' or request.path.startswith('/data/tasks/')):
            return
        path = str(app.config['COLLECTION_DEMO_DB'])
        if path in initialized:
            return
        with collection.database() as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            seed_demo(conn, flows)
        initialized.add(path)

    @app.cli.command('seed-collection-demo')
    def seed_command():
        """Add synthetic collection recordings and related processing examples once."""
        with collection.database() as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            click.echo(json.dumps(seed_demo(conn, flows), ensure_ascii=False))
