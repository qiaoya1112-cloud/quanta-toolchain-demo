import html
import json
import os
import re
import tempfile
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
            self.assertTrue('<title>数据准备任务 - Quanta</title>' in page)
            self.assertTrue('<th>版本</th><th>数据来源</th><th>任务类型</th>' in page)
            selector = re.search(r'id="datasetTaskType".*?</select>',page,re.S)[0]
            self.assertEqual(re.findall(r'<option value="([^"]+)"',selector),['import','create','update'])
            self.assertTrue(config)
            self.assertEqual({task['kind'] for task in config.values()},{'创建数据集'})
            page, config = self.tasks(prefix, task_type='update', task=updated['run_id'])
            self.assertTrue(config)
            self.assertEqual({task['kind'] for task in config.values()},{'更新数据集'})
            self.assertTrue(updated['run_id'] in config)
            self.assertTrue('<td>'+updated['version']+'</td><td>自采数据</td><td>更新数据集</td>' in page)

    def test_task_data_source_matches_import_and_dataset_origin(self):
        page, config = self.tasks(task_type='import', task='import_x5')
        self.assertIn('<th>版本</th><th>数据来源</th><th>任务类型</th>', page)
        self.assertEqual(config['import_x5']['data_source'], '开源数据')
        self.assertIn('<td>v1</td><td>开源数据</td><td>开源数据导入</td>', page)
        created = self.create().json
        page, config = self.tasks(task_type='create', task=created['task_id'])
        self.assertEqual(config[created['task_id']]['data_source'], '自采数据')
        self.assertIn('<td>v1</td><td>自采数据</td><td>创建数据集</td>', page)
        self.assertIn('data-task-detail="data_source"', page)
        dp.get_ds('ds1')['third_party_source_id'] = 'source_test'
        updated = self.automate()
        page, config = self.tasks(task_type='update', task=updated['run_id'])
        self.assertEqual(config[updated['run_id']]['data_source'], '开源数据')
        self.assertIn(f'<td>{updated["version"]}</td><td>开源数据</td><td>更新数据集</td>', page)

    def test_model_tasks_are_a_top_level_data_menu(self):
        page = self.client.get('/model/data/tasks?task_type=import').get_data(as_text=True)
        self.assertIn('<h1>数据准备任务</h1>', page)
        self.assertIn('href="/model/data/tasks" class="sn-item active"', page)
        self.assertIn('<option value="import" selected>开源数据导入</option>', page)
        self.assertNotIn('返回三方数据源</a>', page)
        self.assertNotIn('返回数据集</a>', page)
        self.assertIn('action="/model/data/tasks"', page)
        self.assertIn("document.getElementById('datasetTaskFilters').action", page)
        self.assertIn('href="/model/data/tasks"', self.client.get('/model/data/query').get_data(as_text=True))
        legacy = self.client.get('/model/data/datasets/tasks')
        self.assertEqual(legacy.status_code, 200)
        self.assertIn('开源数据导入', legacy.get_data(as_text=True))

    def test_first_page_has_import_and_update_cases_and_six_filter_fields(self):
        previous_db = dp.app.config.get('THIRD_PARTY_DB')
        try:
            with tempfile.TemporaryDirectory() as temp:
                dp.app.config['THIRD_PARTY_DB'] = os.path.join(temp, 'imports.sqlite3')
                page = self.client.get('/model/data/tasks').get_data(as_text=True)
                rows = re.findall(r'<tr data-task-id="[^"]+"[^>]*>.*?</tr>', page, re.S)
                self.assertEqual(len(rows), 10)
                self.assertGreaterEqual(sum('<td>开源数据导入</td>' in row for row in rows), 2)
                self.assertGreaterEqual(sum('<td>更新数据集</td>' in row for row in rows), 2)
                filters = page.split('id="datasetTaskFilters"', 1)[1].split('</form>', 1)[0]
                self.assertEqual(filters.count('class="q-field"'), 6)
                self.assertEqual(re.findall(r'<div class="q-field"><label[^>]*>([^<]+)</label>', filters),
                                 ['数据集名称', '版本', '数据来源', '任务类型', '状态', '创建人'])
                self.assertNotIn('name="task_id"', filters)
                self.assertIn('<th>创建人</th><th>创建时间</th>', page)
                self.assertNotIn('查看版本</a>', page)
                self.assertIn('查看数据集</a>', page)
                source_page = self.client.get('/model/data/tasks?data_source=开源数据').get_data(as_text=True)
                self.assertIn('<option value="开源数据" selected>开源数据</option>', source_page)
                self.assertIn('data-task-id="import_x5"', source_page)
                self.assertEqual(re.findall(r'<td>(自采数据|开源数据)</td>', source_page).count('自采数据'), 0)
                self.assertEqual(self.tasks(data_source='自采数据', task_type='import')[1], {})
                selected = self.client.get('/model/data/tasks?task_id=import_x5').get_data(as_text=True)
                self.assertIn('data-task-id="import_x5"', selected)
                self.assertNotIn('data-task-id="import_x6"', selected)
        finally:
            if previous_db is None:
                dp.app.config.pop('THIRD_PARTY_DB', None)
            else:
                dp.app.config['THIRD_PARTY_DB'] = previous_db

    def test_manual_save_does_not_create_background_job(self):
        count = len(dp.dataset_task_records())
        snapshot = dp.dataset_version_snapshot(dp.get_ds('ds1'), 'v3')
        rows = dp.dataset_episodes(snapshot)[1:]
        response = self.client.post('/model/data/datasets/ds1/save', json={
            'base_version': 'v3', 'episodes': [{'idx': row['idx'], 'instr': row['instr']} for row in rows]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['processing_status'], 'ready')
        self.assertEqual(len(dp.dataset_task_records()), count)
