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

    def test_new_upload_does_not_silently_join_and_admission_is_unique(self):
        job = self.action(self.create().json['task'], 'publish').json['task']
        with self.app.app_context(), collection.database() as conn, conn:
            task = collection.get_task(conn, self.task['id'])
            extra = dict(task['records'][0], id='NEW-1')
            task['records'].append(extra)
            conn.execute('UPDATE collection_tasks SET payload=? WHERE id=?', (json.dumps(task), task['id']))
        current = self.client.get(processing.API + '/tasks/' + job['id']).json['task']
        self.assertEqual(job['total_count'], current['total_count'])
        self.assertEqual(1, current['new_count'])
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


if __name__ == '__main__':
    unittest.main()
