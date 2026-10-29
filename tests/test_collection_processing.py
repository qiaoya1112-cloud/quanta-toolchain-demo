"""Cross-module relationship tests with a temporary database."""
import json
import tempfile
import unittest
import uuid
from pathlib import Path

from flask import Flask

import post_training_collection as collection
import collection_processing as processing


FLOWS = [dict(stage='质检', name='自动质检', human_nodes=[]),
         dict(stage='标注', name='人工标注', human_nodes=['标注'])]


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, COLLECTION_DEMO_DB=str(Path(self.tmp.name) / 'test.sqlite3'))
        collection.register_collection(self.app, lambda title, content, **kw: content,
                                      [dict(id='a', name='亮剑')], [dict(id='1', name='模型', status='cached')])
        processing.register_processing(self.app, FLOWS)
        self.client = self.app.test_client()
        self.task = self.client.get(collection.API + '/tasks/02601').json['task']

    def tearDown(self):
        self.tmp.cleanup()

    def body(self, **changes):
        body = dict(name='采集数据质检', source_ids=[self.task['id']], priority=3,
                    filters=[['采集任务 ID', '等于', self.task['id']]], stages={'质检': '自动质检'}, configs={'质检': {}})
        body.update(changes)
        return body

    def create(self, body=None, key=None):
        return self.client.post(processing.API + '/tasks', json=body or self.body(), headers={'Idempotency-Key': key or uuid.uuid4().hex})

    def action(self, job, action):
        return self.client.post(processing.API + '/tasks/' + job['id'] + '/action', json=dict(action=action, revision=job['revision']))

    def test_draft_zero_membership_and_publish(self):
        response = self.create()
        self.assertEqual(201, response.status_code)
        job = response.json['task']
        self.assertEqual('draft', job['status'])
        self.assertEqual(0, job['selected_count'])
        self.assertGreater(job['candidate_count'], 0)
        published = self.action(job, 'publish').json['task']
        self.assertEqual('pending', published['status'])
        self.assertEqual(self.task['metrics']['uploaded'], published['selected_count'])
        self.assertEqual(0, published['new_count'])
        self.assertTrue(all(r['stages']['质检'] == 'pending' for r in published['records']))

    def test_original_data_page_uses_membership_not_candidates(self):
        from data_platform_refactor import render_task_detail
        job = self.create().json['task']
        with self.app.app_context(), collection.database() as conn:
            task, records = processing.task_data_context(conn, processing.get_job(conn, job['id']))
            self.assertEqual([], records)
            self.assertEqual(0, task['input_count'])
            self.assertIn('暂无记录', render_task_detail(job['id'], task=task, records=records))
        job = self.action(job, 'publish').json['task']
        with self.app.app_context(), collection.database() as conn:
            task, records = processing.task_data_context(conn, processing.get_job(conn, job['id']))
        self.assertEqual(job['total_count'], len(records))
        self.assertEqual(0, task['processed_count'])
        self.assertTrue(all(r['quality'] == '未完成' for r in records))
        self.assertTrue(all(r['stage_states'] == [('质检', '待处理')] for r in records))
        content = render_task_detail(job['id'], task=task, records=records,
                                     record_filter=records[0]['id'], page=999)
        self.assertIn('dpr-record-page dpr-linked-record-page', content)
        self.assertIn('href="/data/processing-tasks"', content)
        self.assertIn('视频区域（头部 ｜ 左臂 ｜ 右臂）', content)
        self.assertIn('共 1 条', content)
        self.assertNotIn('WB-2026', content)
        self.assertNotIn(records[1]['id'], content)

    def test_partial_membership_does_not_mark_other_records(self):
        record = self.task['records'][0]
        job = self.create(self.body(filters=[['采集任务 ID', '等于', self.task['id']], ['数据 ID', '等于', record['id']]])).json['task']
        job = self.action(job, 'publish').json['task']
        self.assertEqual(1, job['selected_count'])
        selected = self.client.get(processing.API + '/tasks', query_string=dict(collection=self.task['id'], record=record['id'])).json
        self.assertEqual(1, len(selected['tasks']))
        unselected = self.client.get(processing.API + '/tasks', query_string=dict(collection=self.task['id'], record=self.task['records'][1]['id'])).json
        self.assertEqual([], unselected['tasks'])

    def test_creation_idempotency_and_conflict(self):
        key = uuid.uuid4().hex
        first = self.create(key=key)
        second = self.create(key=key)
        self.assertEqual(first.json['task']['id'], second.json['task']['id'])
        self.assertTrue(second.json['replayed'])
        self.assertEqual(409, self.create(self.body(name='不同任务'), key=key).status_code)

    def test_lifecycle_does_not_change_processing(self):
        job = self.action(self.create().json['task'], 'publish').json['task']
        for status in ('closed', 'open'):
            task = self.client.get(collection.API + '/tasks/' + self.task['id']).json['task']
            self.assertEqual(200, self.client.post(collection.API + '/tasks/' + task['id'] + '/state', json=dict(revision=task['revision'], status=status)).status_code)
            current = self.client.get(processing.API + '/tasks/' + job['id']).json['task']
            self.assertEqual(job['records'], current['records'])
            self.assertEqual(job['revision'], current['revision'])
            self.assertEqual('pending', current['status'])

    def test_new_upload_automatically_enters_enabled_task_once(self):
        job = self.action(self.create().json['task'], 'publish').json['task']
        with self.app.app_context(), collection.database() as conn, conn:
            task = collection.get_task(conn, self.task['id'])
            extra = dict(task['records'][0], id='NEW-1')
            task['records'].append(extra)
            conn.execute('UPDATE collection_tasks SET payload=? WHERE id=?', (json.dumps(task), task['id']))
        current = self.client.get(processing.API + '/tasks/' + job['id']).json['task']
        self.assertEqual(job['total_count'] + 1, current['total_count'])
        self.assertEqual(0, current['new_count'])
        admitted = self.action(current, 'admit').json['task']
        self.assertEqual(job['total_count'] + 1, admitted['total_count'])
        again = self.action(admitted, 'admit').json['task']
        self.assertEqual(admitted['records'], again['records'])

    def test_paused_task_does_not_admit_and_resume_keeps_collection(self):
        job = self.action(self.create().json['task'], 'publish').json['task']
        paused = self.action(job, 'pause').json['task']
        self.assertEqual('paused', paused['status'])
        self.assertEqual(422, self.action(paused, 'admit').status_code)
        self.action(paused, 'resume')
        self.assertEqual('open', self.client.get(collection.API + '/tasks/' + self.task['id']).json['task']['status'])
        self.assertEqual(409, self.action(job, 'pause').status_code)

    def test_paused_intake_waits_for_resume_and_keeps_historical_results(self):
        job=self.action(self.create().json['task'],'publish').json['task']
        paused=self.action(job,'pause').json['task']
        with self.app.app_context(),collection.database() as conn,conn:
            stored=processing.get_job(conn,job['id'])
            stored['records'][0]['stages']['质检']='completed'
            stored['records'][0]['results']={'质检':{'conclusion':'合格'}}
            processing.save_job(conn,stored)
            task=collection.get_task(conn,self.task['id'])
            task['records'].append(dict(task['records'][0],id='new-after-stop',upload='uploaded'))
            conn.execute('UPDATE collection_tasks SET payload=? WHERE id=?',(json.dumps(task),task['id']))
        current=self.client.get(processing.API+'/tasks/'+job['id']).json['task']
        self.assertEqual(paused['total_count'],current['total_count'])
        resumed=self.action(current,'resume').json['task']
        self.assertEqual(paused['total_count']+1,resumed['total_count'])
        self.assertEqual('合格',resumed['records'][0]['results']['质检']['conclusion'])

    def test_zero_data_can_create_before_upload(self):
        empty = self.client.get(collection.API + '/tasks/02605').json['task']
        job = self.create(self.body(source_ids=[empty['id']], filters=[['采集任务 ID', '等于', empty['id']]])).json['task']
        job = self.action(job, 'publish').json['task']
        self.assertEqual('waiting', job['status'])
        self.assertEqual(0, job['total_count'])

    def test_stages_are_separate_and_missing_record_is_not_success(self):
        configs = {'质检': {}, '标注': {'标注': dict(rule='规则 v1', assignments=[dict(type='user_group', target='标注组')], percent=100)}}
        job = self.create(self.body(stages={'质检': '自动质检', '标注': '人工标注'}, configs=configs)).json['task']
        job = self.action(job, 'publish').json['task']
        with self.app.app_context(), collection.database() as conn, conn:
            saved = processing.get_job(conn, job['id'])
            for r in saved['records']:
                r['stages']['质检'] = 'completed'
                r['results'] = {'质检': {'conclusion': '合格'}}
            processing.save_job(conn, saved)
        result = self.client.get(processing.API + '/tasks/' + job['id']).json['task']
        progress = {p['stage']: p['status'] for p in result['stage_progress']}
        self.assertEqual('completed', progress['质检'])
        self.assertEqual('pending', progress['标注'])
        self.assertNotEqual('completed', result['status'])

    def test_invalid_fields_and_configuration_rejected(self):
        for changes in (dict(name=''), dict(source_ids=[]), dict(priority=True), dict(stages={}),
                        dict(filters=[['质检结果', '等于', '合格']]),
                        dict(filters=[['采集任务 ID', '不等于', self.task['id']]]),
                        dict(filters=[['采集时间', '等于', 'not-a-date']]),
                        dict(stages={'标注': '人工标注'}, configs={'标注': {}})):
            self.assertEqual(422, self.create(self.body(**changes)).status_code, changes)

    def test_record_status_is_scoped_to_that_record(self):
        job = self.action(self.create().json['task'], 'publish').json['task']
        with self.app.app_context(), collection.database() as conn, conn:
            saved = processing.get_job(conn, job['id'])
            saved['records'][0]['stages']['质检'] = 'completed'
            saved['records'][0]['results'] = {'质检': {'conclusion': '合格'}}
            processing.save_job(conn, saved)
        result = self.client.get(processing.API + '/tasks', query_string=dict(collection=self.task['id'], record=job['records'][0]['id'])).json['tasks'][0]
        self.assertEqual(1, result['selected_count'])
        self.assertEqual('completed', result['status'])

    def test_draft_can_edit_and_published_config_is_locked(self):
        job = self.create().json['task']
        body = self.body(name='调整后的处理配置', category='informal', expected_mode='duration', expected_value='2.5', revision=job['revision'])
        response = self.client.patch(processing.API + '/tasks/' + job['id'], json=body)
        self.assertEqual(200, response.status_code)
        updated = response.json['task']
        self.assertEqual(job['id'], updated['id'])
        self.assertEqual('informal', updated['category'])
        self.assertEqual(2.5, updated['expected_value'])
        published = self.action(updated, 'publish').json['task']
        body['revision'] = published['revision']
        self.assertEqual(409, self.client.patch(processing.API + '/tasks/' + job['id'], json=body).status_code)

    def test_published_operational_edit_preserves_members_and_configuration(self):
        job = self.action(self.create().json['task'], 'publish').json['task']
        path = processing.API + '/tasks/' + job['id']
        response = self.client.patch(path, json=dict(revision=job['revision'], priority=8))
        self.assertEqual(200, response.status_code)
        updated = response.json['task']
        self.assertEqual(8, updated['priority'])
        for field in ('records', 'source_ids', 'filters', 'stages', 'configs', 'published', 'enabled'):
            self.assertEqual(job[field], updated[field])
        self.assertEqual(409, self.client.patch(path, json=dict(revision=job['revision'], priority=1)).status_code)
        self.assertEqual(422, self.client.patch(path, json=dict(revision=updated['revision'], priority=100)).status_code)
        self.assertEqual(409, self.client.patch(path, json=dict(revision=updated['revision'], name='覆盖配置')).status_code)

    def test_source_progress_does_not_replace_task_status(self):
        job = self.action(self.create().json['task'], 'publish').json['task']
        with self.app.app_context(), collection.database() as conn, conn:
            stored = processing.get_job(conn, job['id'])
            stored['records'][0]['stages']['质检'] = 'completed'
            stored['records'][0]['results'] = {'质检': {'conclusion': '合格'}}
            processing.save_job(conn, stored)
        scoped = self.client.get(processing.API + '/tasks', query_string={'collection': self.task['id'], 'record': job['records'][0]['id']}).json['tasks'][0]
        self.assertEqual('completed', scoped['scope_status'])
        self.assertEqual('processing', scoped['task_status'])
        stopped = self.action(self.client.get(processing.API+'/tasks/'+job['id']).json['task'], 'pause').json['task']
        self.assertEqual('paused', stopped['task_status'])
        self.assertEqual('停止接数', stopped['task_status_label'])
        self.assertEqual(1, stopped['stage_progress'][0]['done'])
        self.assertEqual('processing', stopped['stage_progress'][0]['status'])

    def test_admit_scope_and_stale_count_are_checked(self):
        other = self.client.get(collection.API + '/tasks/02607').json['task']
        ids=[self.task['id'], other['id']]
        job=self.action(self.create(self.body(source_ids=ids, filters=[['采集任务 ID','等于',','.join(ids)]])).json['task'],'publish').json['task']
        with self.app.app_context(), collection.database() as conn, conn:
            for tid in ids:
                task=collection.get_task(conn,tid)
                task['records'].append(dict(task['records'][0],id='new-'+tid,upload='uploaded'))
                conn.execute('UPDATE collection_tasks SET payload=? WHERE id=?',(json.dumps(task),tid))
        path=processing.API+'/tasks/'+job['id']+'/action'
        response=self.client.post(path,json=dict(action='admit',revision=job['revision'],collection_id=ids[0],expected_count=99))
        self.assertEqual(409,response.status_code)
        response=self.client.post(path,json=dict(action='admit',revision=job['revision'],collection_id=ids[0],expected_count=1))
        self.assertEqual(200,response.status_code)
        current=response.json['task']
        self.assertTrue(any(r['id']=='new-'+ids[0] for r in current['records']))
        self.assertFalse(any(r['id']=='new-'+ids[1] for r in current['records']))
        self.assertEqual(1,current['new_count'])

    def test_pause_existing_data_keeps_results_and_resumes_previous_states(self):
        job=self.action(self.create().json['task'],'publish').json['task']
        with self.app.app_context(), collection.database() as conn, conn:
            stored=processing.get_job(conn,job['id'])
            stored['records'][0]['stages']['质检']='completed'
            stored['records'][0]['results']={'质检':{'conclusion':'不合格'}}
            stored['records'][1]['stages']['质检']='processing'
            processing.save_job(conn,stored)
        stopped=self.client.post(processing.API+'/tasks/'+job['id']+'/action',json=dict(action='pause',existing_mode='pause',revision=job['revision'])).json['task']
        self.assertEqual('completed',stopped['records'][0]['stages']['质检'])
        self.assertEqual('不合格',stopped['records'][0]['results']['质检']['conclusion'])
        self.assertEqual('paused',stopped['records'][1]['stages']['质检'])
        resumed=self.action(stopped,'resume').json['task']
        self.assertEqual('processing',resumed['records'][1]['stages']['质检'])
        self.assertEqual('pending',resumed['records'][2]['stages']['质检'])

    def test_upstream_selection_uses_task_specific_verdicts_not_collection_conclusion(self):
        upstream=self.action(self.create().json['task'],'publish').json['task']
        with self.app.app_context(), collection.database() as conn, conn:
            stored=processing.get_job(conn,upstream['id'])
            for index,member in enumerate(stored['records']):
                member['stages']['质检']='completed' if index < 2 else 'pending'
                if index<2:member['results']={'质检':{'conclusion':'合格' if index==0 else '不合格'}}
            processing.save_job(conn,stored)
        dependent=self.create(self.body(name='合格结果复核',upstream_id=upstream['id'],upstream_result='合格')).json['task']
        self.assertEqual(1,dependent['candidate_count'])
        dependent=self.action(dependent,'publish').json['task']
        self.assertEqual([upstream['records'][0]['id']],[m['id'] for m in dependent['records']])
        self.assertEqual(422,self.create(self.body(upstream_id='DOES-NOT-EXIST')).status_code)
        with self.app.app_context(),collection.database() as conn,conn:
            stored=processing.get_job(conn,upstream['id'])
            stored['records'][0]['results']['质检']['conclusion']='不合格'
            processing.save_job(conn,stored)
        self.assertEqual(1,self.client.get(processing.API+'/tasks/'+dependent['id']).json['task']['total_count'])

    def test_detail_membership_and_results_remain_task_specific(self):
        job=self.action(self.create().json['task'],'publish').json['task']
        record_id=job['records'][0]['id']
        path=processing.API+'/tasks/'+job['id']+'/records/'+self.task['id']+'/'+record_id
        self.assertEqual('未完成',self.client.get(path).json['record']['quality'])
        with self.app.app_context(),collection.database() as conn,conn:
            stored=processing.get_job(conn,job['id']);stored['records'][0]['stages']['质检']='completed'
            with self.assertRaisesRegex(ValueError, '质检完成必须'):
                processing.save_job(conn,stored)
            stored['records'][0]['results']={'质检':{'conclusion':'合格'}}
            processing.save_job(conn,stored)
        self.assertEqual('合格',self.client.get(path).json['record']['quality'])
        self.assertEqual(404,self.client.get(path.replace(record_id,'missing')).status_code)

    def test_scoped_renderer_counts_current_results_and_pending_reasons(self):
        from data_platform_refactor import render_task_detail
        job=self.action(self.create().json['task'],'publish').json['task']
        with self.app.app_context(),collection.database() as conn:
            task,records=processing.task_data_context(conn,processing.get_job(conn,job['id']))
        with self.app.test_request_context('/data/tasks/'+job['id']+'?collection='+self.task['id']):
            one=render_task_detail(job['id'],task=task,records=records,source_filter=self.task['id'],record_filter=records[0]['id'])
            self.assertIn('命中 <b>1</b> 条',one)
            zero=render_task_detail(job['id'],task=task,records=records,source_filter=self.task['id'],record_filter='MISSING')
            self.assertIn('命中 <b>0</b> 条',zero)
            self.assertIn('暂无记录',zero)
            self.assertNotIn('data-linked-video=',zero)
        response=self.client.post(processing.API+'/preview',json=self.body())
        self.assertEqual(self.task['metrics']['uploaded'],response.json['count'])

    def test_multisource_draft_can_change_sources_before_publication(self):
        job=self.create().json['task']
        other=self.client.get(collection.API+'/tasks/02607').json['task']
        ids=[self.task['id'],other['id']]
        body=self.body(source_ids=ids,filters=[['采集任务 ID','等于',','.join(ids)]],revision=job['revision'])
        response=self.client.patch(processing.API+'/tasks/'+job['id'],json=body)
        self.assertEqual(200,response.status_code)
        self.assertEqual(ids,response.json['task']['source_ids'])

    def test_source_filter_does_not_invent_collection_return_context(self):
        from data_platform_refactor import render_task_detail
        job = self.create().json['task']
        with self.app.app_context(), collection.database() as conn:
            task, records = processing.task_data_context(conn, processing.get_job(conn, job['id']))
        page = render_task_detail(job['id'], task=task, records=records, source_filter=self.task['id'])
        self.assertIn('← 返回处理任务列表', page)
        self.assertNotIn('← 返回采集任务', page)
        page = render_task_detail(job['id'], task=task, records=records,
                                source_filter='', return_source=self.task['id'])
        self.assertIn('← 返回采集任务 ' + self.task['id'], page)
        self.assertIn('href="/data/tasks/' + job['id'] + '?return_collection=' + self.task['id'] + '&amp;return_tab=processing"', page)
        self.assertIn('id="processingCollectionId"', page)
        self.assertNotIn('dpr-linked-sources', page)

    def test_original_processing_records_support_real_source_and_id_filters(self):
        from data_platform_refactor import render_task_detail
        page = render_task_detail('20455', source_filter='20197', record_filter='recording_e2e_001')
        self.assertIn('共 1 条', page)
        self.assertIn('recording_e2e_001', page)
        self.assertNotIn('recording_e2e_002', page)
        empty = render_task_detail('20455', record_filter='NO-SUCH-RECORD')
        self.assertIn('共 0 条', empty)
        self.assertIn('暂无记录', empty)
        self.assertIn('共 0 条', render_task_detail('20455', source_filter='99999'))

    def test_invalid_source_cannot_silently_expand_data_scope(self):
        from data_platform_refactor import render_task_detail
        from collection_processing_scope import safe_return
        job=self.create().json['task']
        with self.app.app_context(),collection.database() as conn:
            task,records=processing.task_data_context(conn,processing.get_job(conn,job['id']))
        with self.app.test_request_context('/data/tasks/'+job['id']+'?collection=99999'):
            page = render_task_detail(job['id'],task=task,records=records,source_filter='99999')
            self.assertIn('共 0 条', page)
            self.assertIn('暂无记录', page)
            self.assertIn('type="search" value="99999"', page)
        for url in ('//example.com','https://example.com','/data/tasks/\\example','http://[','/data/tasks/1\n'):
            self.assertEqual('/fallback',safe_return(url,'/fallback'))

    def test_data_row_has_one_current_stage_and_one_business_node(self):
        from collection_processing_scope import current_business_position
        job={'stages':{'标注':'人工标注','质检':'人工质检'},
             'stage_nodes':{'质检':['质检','抽检'],'标注':['标注','抽验']}}
        member={'stages':{'质检':'processing','标注':'pending'},
                'stage_workflow':{'质检':{'node':'抽检','status':'pending'},'标注':{'node':'标注','status':'pending'}}}
        self.assertEqual(('质检','质检验收'),current_business_position(job,member))
        member['stage_workflow']['质检']={'node':'质检','status':'rework'}
        self.assertEqual(('质检','质检'),current_business_position(job,member))
        member['stages']['质检']='completed'
        member['stage_workflow']['质检']={'node':'End','status':'completed'}
        member['results']={'质检':{'conclusion':'合格'}}
        self.assertEqual(('标注','标注'),current_business_position(job,member))
        member['stage_workflow']['标注']={'node':'抽验','status':'pending'}
        self.assertEqual(('标注','标注验收'),current_business_position(job,member))
        member['stages']['标注']='completed'
        member['stage_workflow']['标注']={'node':'End','status':'completed'}
        self.assertEqual(('','-'),current_business_position(job,member))

    def test_end_node_controls_stage_completion_and_node_counts(self):
        from collection_processing_scope import progress, record_state, quality_result
        job={'stages':{'质检':'人工质检','标注':'人工标注'},
             'stage_nodes':{'质检':['质检','审核'],'标注':['标注','抽验']}}
        def member(node, state, conclusion='合格'):
            return {'stages':{'质检':'completed' if node=='End' else 'processing','标注':'pending'},
                    'results':{'质检':{'conclusion':conclusion}},
                    'stage_workflow':{'质检':{'node':node,'status':state}}}
        rows=[member('End','completed'),member('End','completed','不合格'),member('审核','pending'),member('质检','rework')]
        qc=progress(job,rows)[0][0]
        self.assertEqual((2,1,1,2),(qc['done'],qc['passed'],qc['failed'],qc['unchecked']))
        self.assertEqual(4,sum(n['total'] for n in qc['nodes']))
        self.assertEqual(2,sum(n['total'] for n in qc['business_nodes']))
        self.assertEqual(['质检','质检验收'],[n['node'] for n in qc['business_nodes']])
        self.assertEqual([{'label':'驳回返工','count':1}],qc['nodes'][0]['states'])
        self.assertEqual([{'label':'待验收','count':1}],qc['nodes'][1]['states'])
        self.assertIsNone(quality_result(rows[2]))
        self.assertEqual('processing',record_state(rows[2]))
        rows[0]['stage_workflow']['质检']={'node':'质检','status':'rework'}
        rows[0]['stages']['质检']='processing'
        self.assertEqual(1,progress(job,rows)[0][0]['done'])
        self.assertIsNone(quality_result(rows[0]))

    def test_explicit_non_end_position_cannot_be_saved_as_completed(self):
        job=self.action(self.create().json['task'],'publish').json['task']
        with self.app.app_context(),collection.database() as conn,conn:
            stored=processing.get_job(conn,job['id'])
            member=stored['records'][0]
            member['stages']['质检']='completed'
            member['results']={'质检':{'conclusion':'合格'}}
            member['stage_workflow']={'质检':{'node':'审核','status':'pending'}}
            with self.assertRaisesRegex(ValueError,'End'):
                processing.save_job(conn,stored)

    def test_record_results_use_only_conclusions_or_completion(self):
        from collection_processing_scope import dataset
        qc = self.action(self.create().json['task'], 'publish').json['task']
        annotation_config = {'标注': {'标注': dict(rule='规则 v1', assignments=[dict(type='user_group', target='标注组')], percent=100)}}
        annotation = self.action(self.create(self.body(stages={'标注': '人工标注'}, configs=annotation_config)).json['task'], 'publish').json['task']
        with self.app.app_context(), collection.database() as conn:
            for conclusion in ('合格', '不合格', '失误'):
                qc['records'][0]['stages']['质检'] = 'completed'
                qc['records'][0]['results'] = {'质检': {'conclusion': conclusion}}
                self.assertEqual(conclusion, dataset(conn, qc)[0]['quality'])
            for state in ('pending', 'processing', 'paused'):
                qc['records'][0]['stages']['质检'] = state
                self.assertEqual('未完成', dataset(conn, qc)[0]['quality'])
                annotation['records'][0]['stages']['标注'] = state
                self.assertEqual('未完成', dataset(conn, annotation)[0]['annotation'])
            annotation['records'][0]['stages']['标注'] = 'completed'
            self.assertEqual('已完成', dataset(conn, annotation)[0]['annotation'])
            annotation['records'][0]['stage_workflow'] = {'标注': {'node': '标注验收', 'status': 'pending'}}
            self.assertEqual('未完成', dataset(conn, annotation)[0]['annotation'])

    def test_record_association_separates_node_execution_and_result(self):
        from collection_processing_scope import recording_stage_details
        job = {'stages': {'质检': '人工质检', '标注': '人工标注'},
               'stage_nodes': {'质检': ['质检', '审核'], '标注': ['标注', '抽验']}}
        member = {'stages': {'质检': 'processing', '标注': 'pending'},
                  'stage_workflow': {'质检': {'node': '审核', 'status': 'pending'}}}
        rows = recording_stage_details(job, member)
        self.assertEqual(dict(stage='质检', node='质检验收', execution='待验收', result='未完成'), rows[0])
        self.assertEqual('等待前序完成', rows[1]['execution'])
        member['stage_workflow']['质检'] = {'node': '质检', 'status': 'rework'}
        self.assertEqual('驳回返工', recording_stage_details(job, member)[0]['execution'])
        member['stage_workflow']['质检'] = {'node': 'End', 'status': 'completed'}
        member['stages']['质检'] = 'completed'
        member['results'] = {'质检': {'conclusion': '失误'}}
        rows = recording_stage_details(job, member)
        self.assertEqual(dict(stage='质检', node='-', execution='已完成', result='失误'), rows[0])
        self.assertEqual('待执行', rows[1]['execution'])

    def test_single_record_api_and_return_context_are_scoped_to_membership(self):
        from data_platform_refactor import render_task_detail
        job = self.action(self.create().json['task'], 'publish').json['task']
        record = job['records'][0]
        response = self.client.get(processing.API + '/tasks', query_string={'collection': record['task_id'], 'record': record['id']})
        found = next(item for item in response.json['tasks'] if item['id'] == job['id'])
        self.assertEqual(1, found['selected_count'])
        self.assertTrue(found['record_stages'])
        with self.app.app_context(), collection.database() as conn:
            task, records = processing.task_data_context(conn, processing.get_job(conn, job['id']))
        page = render_task_detail(job['id'], task=task, records=records, return_source=record['task_id'], return_record=record['id'])
        self.assertIn('processing_record=', page)
        self.assertIn('name="return_record" value="' + record['id'] + '"', page)
        invalid = render_task_detail(job['id'], task=task, records=records, return_source=record['task_id'], return_record='unrelated-record', return_tab='records')
        self.assertNotIn('processing_record=', invalid)
        self.assertIn('#records', invalid)
        self.assertIn('name="return_tab" value="records"', invalid)
        task_origin = render_task_detail(job['id'], task=task, records=records, return_source=record['task_id'], return_tab='processing')
        self.assertIn('#processing', task_origin)
        fallback = render_task_detail(job['id'], task=task, records=records, return_source=record['task_id'], return_tab='invalid')
        self.assertIn('#processing', fallback)

    def test_original_processing_filters_use_completed_results_and_rule_versions(self):
        upstream = self.action(self.create().json['task'], 'publish').json['task']
        with self.app.app_context(), collection.database() as conn, conn:
            stored = processing.get_job(conn, upstream['id'])
            stored['configs']['质检'] = {'质检': {'rule': '拿取规范 v1'}}
            for member, conclusion in zip(stored['records'], ('合格', '不合格')):
                member['stages']['质检'] = 'completed'
                member['results'] = {'质检': {'conclusion': conclusion}}
            processing.save_job(conn, stored)
            job = dict(id='new-job', source_ids=[self.task['id']], filters=[])
            source = [['采集任务 ID', '等于', self.task['id']]]
            def selected(*extra):
                job['filters'] = source + list(extra)
                return {record['id'] for _, record in processing.candidates(conn, job)}
            finished = {m['id'] for m in stored['records'][:2]}
            self.assertEqual(finished, selected(['是否完成质检', '等于', '是', 'any']))
            self.assertEqual({stored['records'][0]['id']}, selected(['质检结果', '等于', '合格', 'any']))
            self.assertEqual({stored['records'][1]['id']}, selected(['质检结果', '等于', '不合格', 'any']))
            self.assertEqual(len(stored['records']) - 2, len(selected(['是否完成质检', '等于', '否', 'any'])))
            self.assertEqual(finished, selected(['是否完成质检', '等于', '是', json.dumps(['质检', '拿取规范', 'v1'])]))
            self.assertEqual(set(), selected(['是否完成质检', '等于', '是', json.dumps(['质检', '拿取规范', 'v2'])]))
            self.assertEqual(set(), selected(['是否完成标注', '等于', '是', 'any']))
            # A verdict recorded before End must not count as a finished result.
            member = stored['records'][2]
            member['results'] = {'质检': {'conclusion': '合格'}}
            processing.save_job(conn, stored)
            self.assertEqual(finished, selected(['是否完成质检', '等于', '是', 'any']))

    def test_original_processing_filters_choose_latest_verdict_and_validate_scope(self):
        for stamp, conclusion in [('2026-10-28 10:00:00', '合格'), ('2026-10-29 10:00:00', '不合格')]:
            job = self.action(self.create().json['task'], 'publish').json['task']
            with self.app.app_context(), collection.database() as conn, conn:
                stored = processing.get_job(conn, job['id'])
                stored['records'][0]['stages']['质检'] = 'completed'
                stored['records'][0]['results'] = {'质检': {'conclusion': conclusion, 'completed_at': stamp}}
                processing.save_job(conn, stored)
        for conclusion, count in [('合格', 0), ('不合格', 1)]:
            created = self.create(self.body(filters=[['采集任务 ID', '等于', self.task['id']], ['质检结果', '等于', conclusion, 'any']]))
            self.assertEqual(201, created.status_code)
            self.assertEqual(count, created.json['task']['candidate_count'])
        for condition in [['质检结果', '等于', '合格'], ['质检结果', '等于', '合格', 'bad-scope'], ['是否完成标注', '等于', '是', json.dumps(['质检', '规则', 'v1'])]]:
            self.assertEqual(422, self.create(self.body(filters=[condition])).status_code)

    def test_original_basic_filters_intersect_source_instead_of_being_ignored(self):
        for field, value, expected in [('所属项目', '亮剑', self.task['metrics']['uploaded']), ('所属项目', '其他项目', 0), ('采集任务', self.task['id'], self.task['metrics']['uploaded']), ('采集任务', '99999', 0)]:
            response = self.create(self.body(filters=[['采集任务 ID', '等于', self.task['id']], [field, '等于', value]]))
            self.assertEqual(201, response.status_code)
            self.assertEqual(expected, response.json['task']['candidate_count'])

    def test_quality_progress_keeps_mistake_separate_from_failed(self):
        from collection_processing_scope import progress
        job={'stages':{'质检':'自动质检','标注':'人工标注'}}
        rows=[{'stages':{'质检':'completed','标注':'pending'},'results':{'质检':{'conclusion':value}}} for value in ('合格','不合格','失误')]
        rows.extend([{'stages':{'质检':'completed','标注':'completed'}},{'stages':{'质检':'processing','标注':'pending'}}])
        qc,annotation=progress(job,rows)[0]
        self.assertEqual((5,3,1,1,1,2),(qc['total'],qc['done'],qc['passed'],qc['failed'],qc['mistake'],qc['unchecked']))
        from collection_processing_scope import quality_result
        self.assertEqual('失误',quality_result(rows[2]))
        self.assertNotIn('unreported',qc)
        self.assertEqual(1,annotation['done'])
        self.assertEqual(0,progress(job,[])[0][0]['total'])

    def test_progress_three_states_preserve_started_review_rework_and_paused_work(self):
        from collection_processing_scope import progress
        job = {'stages': {'质检': '人工质检'}, 'stage_nodes': {'质检': ['质检', '审核']}}
        rows = [
            {'stages': {'质检': 'completed'}, 'results': {'质检': {'conclusion': '失误'}}},
            {'stages': {'质检': 'processing'}},
            {'stages': {'质检': 'pending'}, 'stage_workflow': {'质检': {'node': '审核', 'status': 'pending'}}},
            {'stages': {'质检': 'processing'}, 'stage_workflow': {'质检': {'node': '质检', 'status': 'rework'}}},
            {'stages': {'质检': 'paused'}, 'paused_stages': {'质检': 'processing'}},
            {'stages': {'质检': 'paused'}, 'paused_stages': {'质检': 'pending'}},
            {'stages': {'质检': 'pending'}},
        ]
        qc = progress(job, rows)[0][0]
        self.assertEqual((7, 1, 4, 2, 1), (qc['total'], qc['done'], qc['in_progress'], qc['unprocessed'], qc['mistake']))
        self.assertEqual(qc['total'], qc['done'] + qc['in_progress'] + qc['unprocessed'])
        empty = progress(job, [])[0][0]
        self.assertEqual((0, 0, 0), (empty['done'], empty['in_progress'], empty['unprocessed']))


if __name__ == '__main__':
    unittest.main()
