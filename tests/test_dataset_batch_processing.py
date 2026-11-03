import unittest
from copy import deepcopy
import data_platform as dp
import toolchain_demo

class BatchProcessingTests(unittest.TestCase):
    def setUp(self):
        self.datasets = deepcopy(dp.DATASETS)
        self.versions = deepcopy(dp.DS_VERSIONS)
        self.runs = deepcopy(dp.RUNS)
        self.seq = dp._PROC_SEQ[0]
        self.client = toolchain_demo.app.test_client()
        self.rows = [{'id': 'ds1', 'version': 'v3'}, {'id': 'ds1', 'version': 'v2'}]

    def tearDown(self):
        dp.DATASETS[:] = self.datasets
        dp.DS_VERSIONS.clear(); dp.DS_VERSIONS.update(self.versions)
        dp.RUNS[:] = self.runs
        dp._PROC_SEQ[0] = self.seq

    def post(self, **payload):
        return self.client.post('/model/data/datasets/batch-process', json=payload)

    def test_storage_queues_separate_versions_without_modifying_source(self):
        before = deepcopy(dp.dataset_version_snapshot(dp.get_ds('ds1'), 'v3'))
        response = self.post(type='storage', datasets=self.rows, targets=['ks3', 'vepfs'])
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(len(response.json['results']), 2)
        self.assertEqual({run['version'] for run in dp.RUNS[:2]}, {'v3', 'v2'})
        self.assertTrue(all(run['storage_targets'] == ['ks3', 'vepfs'] for run in dp.RUNS[:2]))
        self.assertEqual(dp.dataset_version_snapshot(dp.get_ds('ds1'), 'v3'), before)
        page = self.client.get('/model/data/datasets/tasks')
        self.assertEqual(page.status_code, 200)
        self.assertIn('同步存储', page.get_data(as_text=True))

    def test_storage_accepts_unpublished_but_operator_does_not(self):
        versions = dp.ds_versions(dp.get_ds('ds1'))
        version = next(row for row in versions if row['version'] == 'v2')
        version['publish_status'] = '未发布'
        if version.get('snapshot'):
            version['snapshot']['publish_status'] = '未发布'
        rows = [{'id': 'ds1', 'version': 'v2'}]
        response = self.post(type='storage', datasets=rows, targets=['ks3'])
        self.assertEqual(response.status_code, 200, response.json)
        response = self.post(type='operator', datasets=rows, operator_id='op_split', params={})
        self.assertEqual(response.status_code, 400, response.json)
        self.assertIn('已发布', response.json['error'])

    def test_operator_creates_new_version_per_input(self):
        response = self.post(type='operator', datasets=self.rows, operator_id='op_split', params={})
        self.assertEqual(response.status_code, 200, response.json)
        results = response.json['results']
        self.assertEqual(len({row['version'] for row in results}), 2)
        for row in results:
            snapshot = dp.dataset_version_snapshot(dp.get_ds('ds1'), row['version'])
            self.assertEqual(snapshot['publish_status'], '未发布')
            self.assertEqual(snapshot['processing_status'], 'queued')
        self.assertEqual(dp.dataset_version_snapshot(dp.get_ds('ds1'), 'v3')['publish_status'], '已发布')

    def test_storage_skips_synced_and_active_targets_and_allows_failed_retry(self):
        rows = [self.rows[0]]
        count = len(dp.RUNS)
        response = self.post(type='storage', datasets=rows, targets=['tos', 'ks3'])
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json['results'][0]['storage_status']['tos'], 'synced')
        self.assertEqual(response.json['results'][0]['storage_status']['ks3'], 'syncing')
        self.assertEqual(dp.RUNS[0]['storage_targets'], ['ks3'])
        self.assertEqual(len(dp.RUNS), count + 1)
        dp.RUNS[0]['status'] = 'running'
        again = self.post(type='storage', datasets=rows, targets=['tos', 'ks3'])
        self.assertNotIn('run_id', again.json['results'][0])
        self.assertEqual(len(dp.RUNS), count + 1)
        dp.RUNS[0]['status'] = 'failed'
        retry = self.post(type='storage', datasets=rows, targets=['ks3'])
        self.assertIn('run_id', retry.json['results'][0])
        dp.RUNS[0]['status'] = 'done'
        done = self.post(type='storage', datasets=rows, targets=['ks3'])
        self.assertEqual(done.json['results'][0]['storage_status']['ks3'], 'synced')
        self.assertNotIn('run_id', done.json['results'][0])
        metadata = dp.dataset_batch_version_metadata(dp.get_ds('ds1'))
        self.assertEqual(metadata['storage_status']['ks3'], 'synced')

    def test_invalid_batch_has_no_partial_submission(self):
        for payload in [
            dict(type='storage', datasets=self.rows + [self.rows[0]], targets=['tos']),
            dict(type='storage', datasets=self.rows, targets=['invalid']),
            dict(type='operator', datasets=self.rows, operator_id='missing', params={}),
            dict(type='operator', datasets=self.rows, operator_id='op_split', params={'bad': 'value'}),
        ]:
            with self.subTest(payload=payload):
                count = len(dp.RUNS)
                response = self.post(**payload)
                self.assertEqual(response.status_code, 400, response.json)
                self.assertEqual(len(dp.RUNS), count)

    def test_stale_selection_requests_refresh_without_partial_submission(self):
        count = len(dp.RUNS)
        response = self.post(type='storage', datasets=self.rows + [{'id': 'ds1', 'version': 'v999'}], targets=['tos'])
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json['error'], '所选数据已更新，请刷新页面后重新选择')
        self.assertEqual(len(dp.RUNS), count)
