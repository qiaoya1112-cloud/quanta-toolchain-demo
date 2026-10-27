import html
import json
import re
import unittest
from copy import deepcopy

import data_platform as dp
import toolchain_demo


class DatasetTaskTests(unittest.TestCase):
    def setUp(self):
        self.client = toolchain_demo.app.test_client()
        self.datasets = deepcopy(dp.DATASETS)
        self.versions = deepcopy(dp.DS_VERSIONS)
        self.creation_tasks = deepcopy(dp.DATASET_CREATION_TASKS)
        self.runs = deepcopy(dp.RUNS)
        self.folders = deepcopy(dp.V2_FOLDER_MAP)
        self.sequence = dp._PROC_SEQ[0]

    def tearDown(self):
        dp.DATASETS[:] = self.datasets
        dp.DS_VERSIONS.clear()
        dp.DS_VERSIONS.update(self.versions)
        dp.DATASET_CREATION_TASKS[:] = self.creation_tasks
        dp.RUNS[:] = self.runs
        dp.V2_FOLDER_MAP.clear()
        dp.V2_FOLDER_MAP.update(self.folders)
        dp._PROC_SEQ[0] = self.sequence

    def create(self, **changes):
        query = self.client.get('/model/data/query?task=t2&limit=2').get_data(as_text=True)
        token = html.unescape(re.search(r'id="qAppendSource" value="([^"]+)"', query)[1])
        return self.client.post('/model/data/datasets/create', json={
            'ident': 'task_test_dataset', 'name': '任务关联测试', 'source_token': token,
            'folder': '预训练', 'format': 'LeRobort', 'query': {'task': 't2', 'limit': '2'}, **changes})

    def automate(self):
        return self.client.post('/model/data/datasets/ds1/save', json={
            'base_version': 'v3', 'operations': [{'type': 'workflow', 'scope': 'all', 'target_id': 'pl1', 'params': {}}]}).json

    def tasks(self, prefix='/model/data', **filters):
        response = self.client.get(prefix + '/datasets/tasks', query_string=filters)
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        config = json.loads(re.search(r'id="datasetTaskConfig">(.*?)</script>', page, re.S)[1])
        return page, config

    def test_creation_registers_unpublished_version_and_exact_query_input(self):
        response = self.create(tags=[dp.DATASET_TAG_PATH_OPTIONS[0]])
        self.assertEqual(response.status_code, 200)
        result = response.json
        dataset = dp.get_ds(result['dataset_id'])
        snapshot = dp.dataset_version_snapshot(dataset, 'v1')
        self.assertEqual(snapshot['publish_status'], '未发布')
        self.assertEqual(snapshot['processing_status'], 'running')
        self.assertEqual(snapshot['labels'], [dp.DATASET_TAG_PATH_OPTIONS[0]])
        self.assertEqual([dp.get_rec(row['rec'])['task'] for row in dp.dataset_episodes(snapshot)], ['t2', 't2'])
        page, config = self.tasks(dataset_id=dataset['id'], version='v1', task=result['task_id'])
        self.assertEqual(list(config), [result['task_id']])
        self.assertEqual(config[result['task_id']]['status'], '校验中')
        self.assertEqual(json.loads(config[result['task_id']]['parameters'])['筛选条件'], {'task': 't2', 'limit': '2'})
        self.assertEqual(self.client.post('/model/data/datasets/' + dataset['id'] + '/version/v1/publish').status_code, 409)
        self.assertEqual(self.client.get('/model/data/datasets?sel=' + dataset['id']).status_code, 200)
        task = next(t for t in dp.DATASET_CREATION_TASKS if t['id'] == result['task_id'])
        for state, label in [('verify', '校验中'), ('running', '进行中'), ('fail', '失败'), ('done', '成功')]:
            task['status'] = state
            for prefix in ('/model/data', '/data'):
                _, config = self.tasks(prefix, dataset_id=dataset['id'], version='v1')
                self.assertEqual(config[result['task_id']]['status'], label)
                version_page = self.client.get(prefix + '/datasets', query_string={'sel': dataset['id'], 'tab': 'version'}).get_data(as_text=True)
                self.assertIn('>' + label + '</a>', version_page)
        self.assertEqual(dp.dataset_version_snapshot(dataset)['processing_status'], 'ready')
        self.assertEqual(self.client.post('/model/data/datasets/' + dataset['id'] + '/version/v1/publish').status_code, 302)

    def test_invalid_creation_leaves_no_job_or_dataset(self):
        count = len(dp.DATASETS), len(dp.DATASET_CREATION_TASKS)
        for changes in ({'source_token': 'invalid'}, {'ident': 'ds1'}, {'tags': [1]},
                        {'folder': 'unknown'}, {'visibility': '受限', 'visible_group_ids': []}):
            with self.subTest(changes=changes):
                self.assertIn(self.create(**changes).status_code, (400, 409))
                self.assertEqual((len(dp.DATASETS), len(dp.DATASET_CREATION_TASKS)), count)

    def test_task_status_drives_version_status_and_publication_in_both_modules(self):
        result = self.automate()
        task = next(run for run in dp.RUNS if run['id'] == result['run_id'])
        dataset = dp.get_ds('ds1')
        for status, processing, label in [('queued', 'queued', '待处理'), ('running', 'running', '进行中'),
                                          ('failed', 'failed', '失败'), ('done', 'ready', '成功')]:
            task['status'] = status
            snapshot = dp.dataset_version_snapshot(dataset, result['version'])
            self.assertEqual(snapshot['processing_status'], processing)
            for prefix in ('/model/data', '/data'):
                page, config = self.tasks(prefix, dataset_id='ds1', version=result['version'], task=result['run_id'])
                self.assertEqual(config[result['run_id']]['status'], label)
                version_page = self.client.get(prefix + '/datasets', query_string={'sel': 'ds1', 'tab': 'version'}).get_data(as_text=True)
                self.assertIn('task=' + result['run_id'], version_page)
                self.assertIn('>' + label + '</a>', version_page)
        self.assertEqual(self.client.post('/model/data/datasets/ds1/version/' + result['version'] + '/publish').status_code, 302)

    def test_retry_reuses_failed_task_and_version_and_rejects_stale_task(self):
        result = self.automate()
        task = next(run for run in dp.RUNS if run['id'] == result['run_id'])
        path = '/model/data/datasets/tasks/' + result['run_id'] + '/retry'
        count = len(dp.ds_versions(dp.get_ds('ds1')))
        self.assertEqual(self.client.post(path).status_code, 409)
        task.update(status='failed', error='执行失败')
        self.assertEqual(self.client.post(path).status_code, 200)
        self.assertEqual(task['status'], 'queued')
        self.assertEqual(task['attempt'], 2)
        self.assertEqual(len(dp.ds_versions(dp.get_ds('ds1'))), count)
        task['status'] = 'done'
        self.client.post('/model/data/datasets/ds1/version/' + result['version'] + '/publish')
        task['status'] = 'failed'
        self.assertEqual(self.client.post(path).status_code, 409)

    def test_filters_paginate_and_keep_original_status_enums(self):
        _, config = self.tasks(task_type='create', status='失败', creator='Will Xiao')
        self.assertTrue(config)
        self.assertTrue(all(task['status'] == '失败' and task['by'] == 'Will Xiao' for task in config.values()))
        page, _ = self.tasks(keyword='2026', task_type='create', page=2)
        self.assertIn('keyword=2026', page)
        self.assertIn('task_type=create', page)
        _, config = self.tasks(version='v999')
        self.assertEqual(config, {})
        self.assertEqual(dp.DATASET_CREATION_LABELS, {'done': '成功', 'fail': '失败', 'running': '进行中', 'verify': '校验中'})
        self.assertEqual(dp.DATASET_PROCESSING_LABELS, {'ready': '成功', 'queued': '待处理', 'running': '进行中', 'failed': '失败'})

    def test_task_types_group_updates_and_version_precedes_type(self):
        created = self.create().json
        updated = self.automate()
        for prefix in ('/model/data', '/data'):
            page, config = self.tasks(prefix, task_type='create', task=created['task_id'])
            self.assertTrue('<title>数据集任务列表 - Quanta</title>' in page)
            self.assertTrue('<th>版本</th><th>任务类型</th>' in page)
            selector = re.search(r'id="datasetTaskType".*?</select>',page,re.S)[0]
            self.assertEqual(re.findall(r'<option value="([^"]+)"',selector),['create','update'])
            self.assertTrue(config)
            self.assertEqual({task['kind'] for task in config.values()},{'创建数据集'})
            page, config = self.tasks(prefix, task_type='update', task=updated['run_id'])
            self.assertTrue(config)
            self.assertEqual({task['kind'] for task in config.values()},{'更新数据集'})
            self.assertTrue(updated['run_id'] in config)
            self.assertTrue('<td>'+updated['version']+'</td><td>更新数据集</td>' in page)

    def test_manual_save_does_not_create_background_job(self):
        count = len(dp.dataset_task_records())
        snapshot = dp.dataset_version_snapshot(dp.get_ds('ds1'), 'v3')
        rows = dp.dataset_episodes(snapshot)[1:]
        response = self.client.post('/model/data/datasets/ds1/save', json={
            'base_version': 'v3', 'episodes': [{'idx': row['idx'], 'instr': row['instr']} for row in rows]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['processing_status'], 'ready')
        self.assertEqual(len(dp.dataset_task_records()), count)
