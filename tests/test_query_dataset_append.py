import html
import json
import re
import time
import unittest
from copy import deepcopy
from unittest.mock import patch

from itsdangerous import URLSafeTimedSerializer
import data_platform as dp
import toolchain_demo


class QueryDatasetAppendTests(unittest.TestCase):
    def setUp(self):
        self.client = toolchain_demo.app.test_client()
        self.dataset = dp.get_ds('ds1')
        self.saved_dataset = deepcopy(self.dataset)
        self.saved_versions = deepcopy(dp.DS_VERSIONS)
        dp.DS_VERSIONS.pop('ds1', None)
        self.source = dp.dataset_version_snapshot(self.dataset)
        self.original = dp.dataset_episodes(self.source)
        self.version_count = len(dp.ds_versions(self.dataset))

    def tearDown(self):
        self.dataset.clear()
        self.dataset.update(self.saved_dataset)
        dp.DS_VERSIONS.clear()
        dp.DS_VERSIONS.update(self.saved_versions)

    def payload(self, **query):
        page = self.client.get('/model/data/query', query_string=query).get_data(as_text=True)
        token = html.unescape(re.search(r'id="qAppendSource" value="([^"]+)"', page)[1])
        return {'dataset_id': 'ds1', 'base_version': self.source['version'],
                'description': '补充本次查询筛选出的采集数据', 'source_token': token}

    def append(self, payload, prefix='/model/data'):
        return self.client.post(prefix + '/datasets/append', json=payload)

    def test_target_catalog_only_contains_my_datasets_with_formats(self):
        page = self.client.get('/model/data/query').get_data(as_text=True)
        selector = re.search(r'<select id="qAppendTarget".*?</select>', page, re.S)[0]
        ids = re.findall(r'<option value="([^"]+)"', selector)
        expected = [d['id'] for d in dp.DATASETS if d.get('owner') == dp.CURRENT_USER]
        self.assertEqual(ids, expected)
        config = json.loads(re.search(r'id="qAppendVersionsConfig">(.*?)</script>', page, re.S)[1])
        self.assertEqual(set(config), set(expected))
        self.assertIn('data-format="LeRobort"', selector)
        self.assertIn('data-format="Mozdataset v2"', selector)
        self.assertIn('id="qAppendTargetSearch" role="combobox"', page)
        self.assertIn('class="query-picker-group">我创建的', page)
        self.assertIn('id="qAppendFormat" readonly', page)
        self.assertEqual(dp.dataset_format({'name':'renamed', 'format':'Mozdataset v2'}),'Mozdataset v2')

    def test_cannot_append_to_other_users_dataset(self):
        payload = self.payload()
        other = next(d for d in dp.DATASETS if d.get('owner') != dp.CURRENT_USER)
        saved = deepcopy(other)
        versions = deepcopy(dp.DS_VERSIONS)
        for prefix in ('/model/data', '/data'):
            response = self.append({**payload, 'dataset_id':other['id'], 'base_version':other['version']},prefix)
            self.assertEqual(response.status_code,403)
        self.assertEqual(other,saved)
        self.assertEqual(dp.DS_VERSIONS,versions)

    def test_append_uses_final_query_result_and_preserves_effective_version(self):
        payload = self.payload(task='t2', excluded_ids='121014', limit='2')
        response = self.append(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['added'], 2)
        version = response.json['version']
        snapshot = dp.dataset_version_snapshot(self.dataset, version)
        self.assertEqual(snapshot['status'], '未生效')
        self.assertEqual(snapshot['publish_status'], '未发布')
        self.assertEqual(snapshot['episode_rows'][:len(self.original)], self.original)
        self.assertEqual([row['rec'] for row in snapshot['episode_rows'][len(self.original):]], [121023, 121005])
        self.assertEqual(snapshot['frames'], sum(row['length'] for row in snapshot['episode_rows']))
        self.assertEqual(snapshot['episodes'], len(self.original) + 2)
        self.assertEqual(dp.dataset_episodes(self.dataset), self.original)
        record = dp.ds_versions(self.dataset)[0]
        self.assertEqual(record['note'], payload['description'])
        self.assertEqual(record['creator'], dp.CURRENT_USER)
        detail = self.client.get('/model/data/datasets', query_string={'sel':'ds1','ver':version,'tab':'version'})
        self.assertEqual(detail.status_code, 200)
        self.assertIn(payload['description'], detail.get_data(as_text=True))

    def test_duplicates_are_skipped_and_repeat_request_is_idempotent(self):
        payload = self.payload()
        first = self.append(payload)
        self.assertEqual(first.json['added'], 7)
        self.assertEqual(first.json['skipped'], 3)
        self.assertEqual(self.append(payload).json, first.json)
        self.assertEqual(len(dp.ds_versions(self.dataset)), self.version_count + 1)

    def test_new_version_can_copy_historical_published_source(self):
        source = next(v for v in dp.ds_versions(self.dataset) if v['version']=='v1')
        historical_rows = deepcopy(self.original[1:])
        historical_rows[0]['instr'] = '历史版本独有的提示词'
        source['snapshot'].update(episode_rows=historical_rows, labels=['历史版本标签'])
        saved_versions = deepcopy(dp.ds_versions(self.dataset))
        effective = deepcopy(self.dataset)
        payload = {**self.payload(task='t2', limit='1'), 'base_version':'v1'}
        response = self.append(payload)
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json['created'])
        record = dp.ds_versions(self.dataset)[0]
        snapshot = dp.dataset_version_snapshot(self.dataset,response.json['version'])
        self.assertEqual(record['base_version'],'v1')
        self.assertEqual(snapshot['episode_rows'][:-1],historical_rows)
        self.assertEqual(snapshot['episode_rows'][-1]['rec'],121023)
        self.assertEqual(snapshot['labels'],['历史版本标签'])
        self.assertEqual(snapshot['publish_status'],'未发布')
        self.assertEqual(snapshot['status'],'未生效')
        self.assertEqual(dp.ds_versions(self.dataset)[1:],saved_versions)
        self.assertEqual(self.dataset,effective)
        self.assertEqual(self.append(payload).json,response.json)
        self.assertEqual(len(dp.ds_versions(self.dataset)),self.version_count+1)

    def test_new_version_requires_published_ready_source(self):
        payload = self.payload(task='t2')
        draft = dp.ds_versions(self.dataset)[0]
        for base,status in [(draft['version'],409),('v999',409),('',400),(None,400),([],400)]:
            with self.subTest(base=base):
                self.assertEqual(self.append({**payload,'base_version':base}).status_code,status)
        historical = next(v for v in dp.ds_versions(self.dataset) if v['version']=='v1')
        historical['snapshot']['processing_status']='queued'
        self.assertEqual(self.append({**payload,'base_version':'v1'}).status_code,409)
        self.assertEqual(len(dp.ds_versions(self.dataset)),self.version_count)

    def test_append_only_selected_results_and_reject_out_of_scope_selection(self):
        payload = self.payload(task='t2')
        for selection in ([], [120489], [121023,120489], ['121023'], True):
            with self.subTest(selection=selection):
                response = self.append({**payload, 'selected_ids':selection})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(len(dp.ds_versions(self.dataset)), self.version_count)
        response = self.append({**payload, 'selected_ids':[121005,121023,121005]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['added'], 2)
        snapshot = dp.dataset_version_snapshot(self.dataset, response.json['version'])
        self.assertEqual([row['rec'] for row in snapshot['episode_rows'][len(self.original):]], [121023,121005])

    def test_append_can_update_existing_unpublished_version_or_create_new_one(self):
        page = self.client.get('/model/data/query').get_data(as_text=True)
        self.assertIn('id="qAppendVersion"', page)
        self.assertNotIn('id="qManageExclusions"', page)
        target = dp.ds_versions(self.dataset)[0]
        self.assertEqual(target['publish_status'], '未发布')
        draft_rows = deepcopy(self.original[2:])
        draft_rows[0]['instr'] = '草稿中已修改的提示词'
        target['snapshot']['episode_rows'] = deepcopy(draft_rows)
        metadata = (target['created'],target['creator'])
        other_versions = deepcopy(dp.ds_versions(self.dataset)[1:])
        payload = self.payload(task='t2', limit='1')
        payload.update(target_version=target['version'], selected_ids=[121023])
        response = self.append(payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['created'])
        self.assertEqual(response.json['version'], target['version'])
        self.assertEqual(len(dp.ds_versions(self.dataset)), self.version_count)
        snapshot = dp.dataset_version_snapshot(self.dataset, target['version'])
        self.assertEqual(snapshot['episode_rows'][:-1], draft_rows)
        self.assertEqual(snapshot['episode_rows'][-1]['rec'],121023)
        self.assertEqual(snapshot['episodes'], len(draft_rows)+1)
        self.assertEqual(snapshot['publish_status'],'未发布')
        self.assertEqual((target['created'],target['creator']),metadata)
        self.assertEqual(target['note'],payload['description'])
        self.assertEqual(dp.ds_versions(self.dataset)[1:],other_versions)
        self.assertEqual(self.append(payload).json,response.json)
        second_payload = {**self.payload(task='t2'), 'target_version':target['version'], 'selected_ids':[121005]}
        self.assertEqual(self.append(second_payload).json['added'],1)
        self.assertEqual(self.append(payload).json,response.json)
        self.assertEqual(len(dp.dataset_episodes(dp.dataset_version_snapshot(self.dataset,target['version']))),len(draft_rows)+2)
        saved_draft = deepcopy(target)
        created = self.append({**payload,'target_version':''})
        self.assertEqual(created.status_code,200)
        self.assertTrue(created.json['created'])
        self.assertEqual(dp.dataset_version_snapshot(self.dataset,created.json['version'])['episodes'],len(self.original)+1)
        self.assertEqual(saved_draft,target)
        published = {**payload, 'target_version': self.source['version']}
        self.assertEqual(self.append(published).status_code, 409)

    def test_existing_version_validation_and_catalog_follow_publish_state(self):
        payload=self.payload(task='t2')
        target=dp.ds_versions(self.dataset)[0]
        for version,status in [('v999',404),('v1',409),([],400)]:
            self.assertEqual(self.append({**payload,'target_version':version}).status_code,status)
        target['snapshot']['processing_status']='queued'
        self.assertEqual(self.append({**payload,'target_version':target['version']}).status_code,409)
        page=self.client.get('/model/data/query').get_data(as_text=True)
        config=json.loads(re.search(r'id="qAppendVersionsConfig">(.*?)</script>',page,re.S)[1])
        self.assertEqual([item['version'] for item in config['ds1'] if item['publish_status']=='未发布'],[target['version']])
        self.assertEqual([item['version'] for item in config['ds1'] if item['publish_status']=='已发布'],['v3','v2','v1'])
        self.assertFalse(config['ds1'][0]['ready'])
        target['snapshot']['processing_status']='ready'
        self.client.post('/model/data/datasets/ds1/version/'+target['version']+'/publish')
        self.assertEqual(self.append({**payload,'target_version':target['version']}).status_code,409)
        self.assertEqual(len(dp.ds_versions(self.dataset)),self.version_count)

    def test_required_description_stale_version_and_invalid_target_do_not_create_versions(self):
        payload = self.payload(task='t2')
        for overrides, status in [({'description':''},400), ({'description':'  '},400),
                                  ({'description':'x'*1001},400), ({'base_version':'v999'},409),
                                  ({'dataset_id':'missing'},404)]:
            with self.subTest(overrides=overrides):
                self.assertEqual(self.append({**payload, **overrides}).status_code, status)
                self.assertEqual(len(dp.ds_versions(self.dataset)), self.version_count)

    def test_empty_duplicate_expired_and_tampered_results_are_rejected(self):
        for payload in [self.payload(task='unknown'), self.payload(task='t1', excluded_ids='120513,120521'),
                        {**self.payload(), 'source_token':'tampered'}, {**self.payload(), 'source_token':[]}]:
            self.assertIn(self.append(payload).status_code, (400,409))
        with patch('itsdangerous.timed.TimestampSigner.get_timestamp', return_value=int(time.time())-3601):
            token = URLSafeTimedSerializer(dp.app.secret_key, salt='query-dataset-append').dumps([121005])
        self.assertEqual(self.append({**self.payload(), 'source_token':token}).status_code, 409)
        self.assertEqual(len(dp.ds_versions(self.dataset)), self.version_count)

    def test_shared_data_workspace_and_activation_show_appended_data(self):
        payload = self.payload(task='t2', limit='1')
        version = self.append(payload, prefix='/data').json['version']
        self.assertEqual(self.client.post('/data/datasets/ds1/version/'+version+'/activate').status_code, 409)
        self.client.post('/data/datasets/ds1/version/'+version+'/publish')
        self.client.post('/data/datasets/ds1/version/'+version+'/activate')
        self.assertEqual(self.dataset['version'], version)
        self.assertEqual(len(dp.dataset_episodes(self.dataset)), len(self.original)+1)
        self.assertEqual(dp.dataset_episodes(dp.dataset_version_snapshot(self.dataset,self.source['version'])), self.original)


if __name__ == '__main__':
    unittest.main()
