import json
import re
import unittest
from copy import deepcopy

from bs4 import BeautifulSoup

import data_platform as dp
import toolchain_demo


class DatasetEditingTests(unittest.TestCase):
    def setUp(self):
        self.client = toolchain_demo.app.test_client()
        self.dataset = dp.get_ds('ds1')
        self.saved_dataset = deepcopy(self.dataset)
        self.saved_versions = deepcopy(dp.DS_VERSIONS)
        self.saved_runs = deepcopy(dp.RUNS)
        self.saved_sequence = dp._PROC_SEQ[0]
        dp.DS_VERSIONS.pop('ds1', None)
        self.source = dp.dataset_version_snapshot(self.dataset)
        self.original = dp.dataset_episodes(self.source)

    def tearDown(self):
        self.dataset.clear()
        self.dataset.update(self.saved_dataset)
        dp.DS_VERSIONS.clear()
        dp.DS_VERSIONS.update(self.saved_versions)
        dp.RUNS[:] = self.saved_runs
        dp._PROC_SEQ[0] = self.saved_sequence

    def payload(self, rows=None, version=None):
        return {'base_version': version or self.source['version'], 'episodes': [
            {'idx': row['idx'], 'instr': row['instr']} for row in (self.original if rows is None else rows)
        ]}

    def save(self, payload, prefix='/model/data'):
        return self.client.post(prefix + '/datasets/ds1/save', json=payload)

    def config(self, version):
        response = self.client.get('/model/data/datasets?sel=ds1&ver=' + version)
        self.assertEqual(response.status_code, 200)
        return json.loads(re.search(r'id="datasetEditorConfig">(.*?)</script>', response.get_data(as_text=True), re.S)[1])

    def test_basic_info_has_requested_fields_and_known_storage_path(self):
        page = self.client.get('/model/data/datasets?sel=ds1&tab=info')
        self.assertEqual(page.status_code, 200)
        summary = BeautifulSoup(page.data, 'html.parser').select_one('#info_sum .desc-grid')
        self.assertEqual([field.get_text(strip=True) for field in summary.select('.dk')],
                         ['名称', '标识', '数据格式', '存储位置', '数据条数', '数据时长', '数据来源'])
        values = [field.get_text(strip=True) for field in summary.select('.dv')]
        self.assertEqual(values[0], self.source['name'])
        self.assertEqual(values[1], self.source['ident'])
        self.assertEqual(values[3], self.source['tos'])
        self.assertEqual(values[4], str(len(self.original)))
        self.assertRegex(values[5], r'^\d{2}:\d{2}:\d{2}$')
        self.assertEqual(values[6], '自采数据')

        missing = self.client.get('/model/data/datasets?sel=ds2&tab=info')
        missing_summary = BeautifulSoup(missing.data, 'html.parser').select_one('#info_sum .desc-grid')
        self.assertEqual(missing_summary.select('.dv')[3].get_text(strip=True), '—')

    def test_save_deletes_one_episode_updates_prompts_and_preserves_source(self):
        rows = deepcopy(self.original[1:])
        rows[0]['instr'] = rows[1]['instr'] = '请擦拭白板\nKeep the arm steady.'
        response = self.save(self.payload(rows))
        self.assertEqual(response.status_code, 200)
        version = response.json['version']
        self.assertEqual(version, 'v5')  # v4 is an existing demo draft.
        saved = dp.dataset_version_snapshot(self.dataset, version)
        self.assertEqual(saved['episodes'], 47)
        self.assertEqual(saved['frames'], self.source['frames'] - self.original[0]['length'])
        self.assertEqual(dp.dataset_episodes(saved), saved['episode_rows'])
        self.assertEqual(dp.dataset_episodes(dp.dataset_version_snapshot(self.dataset, 'v3')), self.original)
        self.assertEqual(saved['episode_rows'][0]['instr'], rows[0]['instr'])
        self.assertEqual(saved['episode_rows'][2]['instr'], self.original[3]['instr'])
        self.assertEqual(saved['episode_rows'][0]['annotation']['lowlevel_segments'], self.original[1]['annotation']['lowlevel_segments'])
        self.assertEqual(sum(item['episode_count'] for item in dp.dataset_prompt_composition(saved)), 47)
        self.assertEqual(len(dp.dataset_episode_prompt_annotations(saved)), 47)
        self.assertEqual(self.config('v3')['episodes'][0]['idx'], 0)
        self.assertEqual(self.config(version)['episodes'][0]['idx'], 1)
        self.assertEqual(self.config(version)['episodes'][0]['instr'], rows[0]['instr'])
        self.assertIn('删除 1 条数据，修改 2 条 Prompt', dp.ds_versions(self.dataset)[0]['note'])
        self.assertEqual(saved['status'], '未生效')
        self.assertEqual(saved['publish_status'], '未发布')
        self.assertEqual(self.dataset['version'], 'v3')
        self.assertEqual([v['version'] for v in dp.ds_versions(self.dataset) if v['status'] == '生效中'], ['v3'])

    def test_unpublished_current_save_updates_only_target_and_preserves_identity(self):
        versions = dp.ds_versions(self.dataset)
        draft = versions[0]
        frozen = deepcopy(versions[1:])
        created, creator, count = draft['created'], draft['creator'], len(versions)
        rows = deepcopy(self.original[1:])
        rows[0]['instr'] = '更新当前草稿的 Prompt'
        for prefix in ('/model/data', '/data'):
            payload = self.payload(rows, version=draft['version'])
            payload['save_mode'] = 'current'
            if prefix == '/data':
                rows[0]['instr'] = '再次保存草稿'
                payload = {**self.payload(rows, version=draft['version']), 'save_mode': 'current'}
            response = self.save(payload, prefix=prefix)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['save_mode'], 'current')
            self.assertEqual(response.json['version'], draft['version'])
            self.assertEqual(len(dp.ds_versions(self.dataset)), count)
            snapshot = dp.dataset_version_snapshot(self.dataset, draft['version'])
            self.assertEqual(snapshot['publish_status'], '未发布')
            self.assertEqual(snapshot['episodes'], 47)
            self.assertEqual(snapshot['episode_rows'][0]['instr'], rows[0]['instr'])
            self.assertEqual(snapshot['frames'], sum(row['length'] for row in rows))
            self.assertEqual(snapshot['created'], created)
            self.assertEqual(draft['creator'], creator)
            self.assertEqual(draft['updater'], dp.CURRENT_USER)
            self.assertEqual(versions[1:], frozen)
            self.assertEqual(self.dataset['version'], 'v3')
        self.assertEqual(dp.dataset_episodes(self.dataset), self.original)

    def test_published_current_save_and_invalid_modes_are_rejected_without_changes(self):
        frozen = deepcopy(dp.ds_versions(self.dataset))
        for mode in ('current', '', 'replace', None, [], {}):
            response = self.save({**self.payload(self.original[1:]), 'save_mode': mode})
            self.assertIn(response.status_code, (400, 409))
            self.assertEqual(dp.ds_versions(self.dataset), frozen)
            self.assertEqual(dp.dataset_episodes(self.dataset), self.original)
        draft = dp.ds_versions(self.dataset)[0]
        self.client.post('/data/datasets/ds1/version/' + draft['version'] + '/publish')
        self.assertEqual(self.save({**self.payload(self.original[1:], draft['version']), 'save_mode': 'current'}).status_code, 409)

    def test_unpublished_can_also_save_as_new_version(self):
        draft = dp.ds_versions(self.dataset)[0]
        frozen = deepcopy(draft)
        response = self.save({**self.payload(self.original[1:], draft['version']), 'save_mode': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json['version'], draft['version'])
        self.assertEqual(draft, frozen)
        self.assertEqual(dp.dataset_version_snapshot(self.dataset, response.json['version'])['publish_status'], '未发布')

    def test_current_save_automation_queues_task_for_same_version(self):
        draft = dp.ds_versions(self.dataset)[0]
        count = len(dp.ds_versions(self.dataset))
        response = self.save({'base_version': draft['version'], 'save_mode': 'current', 'operations': [
            {'type': 'remove', 'scope': 'selected', 'episode_ids': [0]},
            {'type': 'operator', 'scope': 'all', 'target_id': 'op_split', 'params': {}},
        ]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['version'], draft['version'])
        self.assertEqual(response.json['processing_status'], 'queued')
        self.assertEqual(len(dp.ds_versions(self.dataset)), count)
        self.assertEqual(dp.RUNS[0]['version'], draft['version'])
        self.assertEqual(len(dp.RUNS[0]['input_episodes']), 47)
        self.assertEqual(draft['snapshot']['run_id'], dp.RUNS[0]['id'])
        self.assertEqual(self.client.post('/data/datasets/ds1/version/' + draft['version'] + '/publish').status_code, 409)
        self.assertEqual(self.save({'base_version': draft['version'], 'save_mode': 'current', 'episodes': []}).status_code, 409)

    def test_save_controls_follow_publication_state(self):
        for version, published in (('v3', True), ('v4', False)):
            config = self.config(version)
            self.assertEqual(config['publish_status'], '已发布' if published else '未发布')
            page = self.client.get('/model/data/datasets?sel=ds1&ver=' + version).get_data(as_text=True)
            self.assertIn('id="datasetSaveButton"', page)
            self.assertEqual('id="datasetSaveCurrentButton"' in page, not published)

    def test_invalid_or_unchanged_edits_do_not_create_versions(self):
        count = len(dp.ds_versions(self.dataset))
        bad_payloads = [self.payload(), self.payload([]), {}, {'base_version': ''},
                        self.payload(version='v999'), {'base_version': 'v3', 'episodes': 'bad'}]
        for invalid in ({'idx': 999999, 'instr': 'x'}, {'idx': True, 'instr': 'x'},
                        {'idx': 0, 'instr': ' '}, {'idx': 0, 'instr': 12}):
            payload = self.payload()
            payload['episodes'][0] = invalid
            bad_payloads.append(payload)
        duplicate = self.payload()
        duplicate['episodes'].append(duplicate['episodes'][0])
        bad_payloads.append(duplicate)
        for payload in bad_payloads:
            with self.subTest(payload=payload):
                self.assertIn(self.save(payload).status_code, (400, 409))
                self.assertEqual(len(dp.ds_versions(self.dataset)), count)
                self.assertEqual(dp.dataset_episodes(self.dataset), self.original)

    def test_editing_historical_version_branches_without_overwriting_later_version(self):
        first = self.save(self.payload(self.original[1:])).json['version']
        frozen = deepcopy(dp.dataset_version_snapshot(self.dataset, first))
        second = self.save(self.payload(self.original[2:])).json['version']
        self.assertNotEqual(first, second)
        self.assertEqual(dp.dataset_version_snapshot(self.dataset, first), frozen)
        self.assertEqual(len(self.config(second)['episodes']), 46)
        self.assertEqual(len(self.config('v3')['episodes']), 48)

    def test_edit_entry_and_endpoint_work_in_both_shared_workspaces(self):
        for prefix in ('/model/data', '/data'):
            response = self.client.get(prefix + '/datasets?sel=ds1')
            self.assertEqual(response.status_code, 200)
            self.assertIn('data-save-url="' + prefix + '/datasets/ds1/save"', response.get_data(as_text=True))
        path_detail = self.client.get('/model/data/datasets/ds1').get_data(as_text=True)
        self.assertIn('href="/model/data/datasets?sel=ds1&amp;edit=1">编辑', path_detail)
        response = self.save(self.payload(self.original[:-1]), prefix='/data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.post('/model/data/datasets/not-found/save', json=self.payload()).status_code, 404)

    def test_prompt_markup_is_escaped_and_round_trips(self):
        prompt = '</script></textarea><img src=x onerror=alert(1)> & "测试"'
        payload = self.payload()
        payload['episodes'][0]['instr'] = prompt
        version = self.save(payload).json['version']
        self.assertEqual(self.config(version)['episodes'][0]['instr'], prompt)
        html = self.client.get('/model/data/datasets?sel=ds1&ver=' + version).get_data(as_text=True)
        self.assertNotIn(prompt, html)
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', html)

    def test_activation_switches_content_without_creating_versions(self):
        version = self.save(self.payload(self.original[1:])).json['version']
        count = len(dp.ds_versions(self.dataset))
        self.client.post('/model/data/datasets/ds1/version/' + version + '/publish')
        self.client.post('/model/data/datasets/ds1/version/' + version + '/activate')
        self.assertEqual(self.dataset['status'], '生效中')
        self.assertEqual(self.dataset['episodes'], 47)
        self.assertEqual([v['version'] for v in dp.ds_versions(self.dataset) if v['status'] == '生效中'], [version])
        response = self.client.post('/data/datasets/ds1/version/v3/activate')
        self.assertTrue(response.headers['Location'].startswith('/data/datasets'))
        self.assertEqual(self.dataset['episodes'], 48)
        self.assertEqual(dp.dataset_episodes(self.dataset), self.original)
        self.assertEqual(len(dp.ds_versions(self.dataset)), count)
        self.assertEqual([v['version'] for v in dp.ds_versions(self.dataset) if v['status'] == '生效中'], ['v3'])
        self.assertEqual(len(self.config(version)['episodes']), 47)
        self.assertEqual(dp.dataset_version_snapshot(self.dataset, version)['status'], '未生效')

    def test_activation_is_idempotent_and_invalid_version_preserves_active(self):
        count = len(dp.ds_versions(self.dataset))
        for version in ('v3', 'v3', 'v999'):
            response = self.client.post('/model/data/datasets/ds1/version/' + version + '/activate')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(len(dp.ds_versions(self.dataset)), count)
            self.assertEqual([v['version'] for v in dp.ds_versions(self.dataset) if v['status'] == '生效中'], ['v3'])
        html = self.client.get('/model/data/datasets?sel=ds1&tab=version').get_data(as_text=True)
        version_table = re.search(r'id="pane-version">(.*?)</table>', html, re.S)[1]
        self.assertNotIn('标为生效', version_table)
        self.assertNotIn('回退', version_table)
        self.assertIn('<th>发布状态</th>', version_table)
        self.assertNotIn('<th>生效状态</th>', version_table)
        self.assertIn('已发布', version_table)
        self.assertIn('未发布', version_table)
        self.assertNotIn('发布 / 上传 TOS', html)
        self.assertEqual(self.client.get('/model/data/datasets/ds1/version/v3/publish').status_code, 405)
        self.assertEqual(self.client.get('/model/data/datasets/ds1/version/v3/rollback').status_code, 404)

    def test_unpublished_version_requires_publish_before_activation(self):
        version = self.save(self.payload(self.original[1:])).json['version']
        count = len(dp.ds_versions(self.dataset))
        for prefix in ('/model/data', '/data'):
            response = self.client.post(prefix + '/datasets/ds1/version/' + version + '/activate')
            self.assertEqual(response.status_code, 409)
            self.assertIn('先发布', response.json['error'])
        self.assertEqual(self.dataset['version'], 'v3')
        for prefix in ('/model/data', '/data'):
            response = self.client.post(prefix + '/datasets/ds1/version/' + version + '/publish')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.headers['Location'].startswith(prefix + '/datasets'))
            self.assertEqual(self.dataset['version'], 'v3')
            snapshot = dp.dataset_version_snapshot(self.dataset, version)
            self.assertEqual(snapshot['publish_status'], '已发布')
            self.assertEqual(snapshot['status'], '未生效')
            self.assertEqual(len(dp.ds_versions(self.dataset)), count)
        self.assertEqual(self.client.post('/data/datasets/ds1/version/' + version + '/activate').status_code, 302)
        self.assertEqual(self.dataset['version'], version)
        self.assertEqual(self.dataset['publish_status'], '已发布')
        self.client.post('/data/datasets/ds1/version/v3/activate')
        self.assertEqual(dp.dataset_version_snapshot(self.dataset, version)['publish_status'], '已发布')
        self.assertEqual(dp.dataset_version_snapshot(self.dataset, version)['status'], '未生效')
        branched = self.save(self.payload(self.original[2:], version=version)).json['version']
        self.assertEqual(dp.dataset_version_snapshot(self.dataset, branched)['publish_status'], '未发布')

    def test_seed_and_legacy_versions_have_separate_publication_state(self):
        versions = dp.ds_versions(self.dataset)
        self.assertEqual(versions[0]['publish_status'], '未发布')
        self.assertTrue(all(v['publish_status'] == '已发布' for v in versions[1:]))
        for version in versions:
            version.pop('publish_status')
            version['snapshot'].pop('publish_status')
        versions = dp.ds_versions(self.dataset)
        self.assertEqual(next(v for v in versions if v['status'] == '生效中')['publish_status'], '已发布')
        self.assertTrue(all(v['snapshot']['publish_status'] == v['publish_status'] for v in versions))

    def test_processing_versions_cannot_publish_until_ready(self):
        version = self.save({'base_version': 'v3', 'operations': [
            {'type': 'workflow', 'scope': 'all', 'target_id': 'pl1', 'params': {}},
        ]}).json['version']
        for state in ('queued', 'running', 'failed'):
            record = dp.ds_versions(self.dataset)[0]
            dp.RUNS[0]['status'] = state
            for prefix in ('/model/data', '/data'):
                self.assertEqual(self.client.post(prefix + '/datasets/ds1/version/' + version + '/publish').status_code, 409)
                self.assertEqual(record['publish_status'], '未发布')
                self.assertEqual(self.dataset['version'], 'v3')
        dp.RUNS[0]['status'] = 'done'
        self.assertEqual(self.client.post('/model/data/datasets/ds1/version/' + version + '/publish').status_code, 302)
        self.assertEqual(record['publish_status'], '已发布')
        self.assertEqual(self.dataset['version'], 'v3')

    def test_processing_creates_inactive_version_and_keeps_current_effective(self):
        response = self.client.post('/data/datasets/ds1/process', data={'op': 'task|标准训练数据流水线'})
        self.assertEqual(response.status_code, 302)
        versions = dp.ds_versions(self.dataset)
        self.assertEqual(versions[0]['status'], '未生效')
        self.assertEqual(self.dataset['version'], 'v3')
        self.assertEqual([v['version'] for v in versions if v['status'] == '生效中'], ['v3'])
        self.assertEqual(dp.RUNS[0]['status'], 'queued')

    def test_manual_changes_save_with_one_automation_task(self):
        operations = [
            {'type': 'remove', 'scope': 'selected', 'episode_ids': [0]},
            {'type': 'prompt', 'scope': 'selected', 'episode_ids': [1, 2], 'prompt': 'Clean the desk'},
            {'type': 'operator', 'scope': 'all', 'target_id': 'op_split', 'params': {'--seed': '123'}},
        ]
        response = self.save({'base_version': 'v3', 'operations': operations})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['processing_status'], 'queued')
        version = response.json['version']
        snapshot = dp.dataset_version_snapshot(self.dataset, version)
        self.assertEqual(snapshot['episodes'], 47)
        self.assertEqual(snapshot['episode_rows'][0]['instr'], 'Clean the desk')
        self.assertEqual([step['type'] for step in snapshot['operation_plan']], ['remove', 'prompt', 'operator'])
        self.assertEqual(snapshot['operation_plan'][-1]['definition']['id'], 'op_split')
        run = dp.RUNS[0]
        self.assertEqual(run['id'], response.json['run_id'])
        self.assertEqual(run['status'], 'queued')
        self.assertEqual(run['input_episodes'], snapshot['episode_rows'])
        self.assertEqual(run['operations'][0]['params'], {'--seed': '123'})
        self.assertEqual(len(run['operations']), 1)
        self.assertEqual(self.dataset['version'], 'v3')
        self.assertEqual(self.client.post('/model/data/datasets/ds1/version/' + version + '/activate').status_code, 409)
        self.assertEqual(self.save({'base_version': version, 'operations': operations}).status_code, 409)
        execution_page = self.client.get('/model/data/runs')
        self.assertEqual(execution_page.status_code, 200)
        self.assertIn(run['id'], execution_page.get_data(as_text=True))
        self.assertIn('待执行', execution_page.get_data(as_text=True))

    def test_multiple_automation_tasks_are_rejected_without_changes(self):
        frozen = deepcopy(dp.ds_versions(self.dataset))
        for kinds in (('operator', 'operator'), ('operator', 'workflow'), ('workflow', 'workflow')):
            with self.subTest(kinds=kinds):
                operations = [{'type': kind, 'scope': 'all', 'target_id': 'op_split' if kind == 'operator' else 'pl1', 'params': {}}
                              for kind in kinds]
                response = self.save({'base_version': 'v3', 'operations': operations})
                self.assertEqual(response.status_code, 400)
                self.assertIn('每次只能提交一个', response.json['error'])
                self.assertEqual(dp.ds_versions(self.dataset), frozen)
                self.assertEqual(dp.RUNS, self.saved_runs)

    def test_manual_operations_share_save_contract_and_preserve_annotations(self):
        response = self.save({'base_version': 'v3', 'operations': [
            {'type': 'prompt', 'scope': 'all', 'prompt': 'Wipe the board'},
            {'type': 'remove', 'scope': 'selected', 'episode_ids': [0, 1]},
        ]})
        self.assertEqual(response.status_code, 200)
        snapshot = dp.dataset_version_snapshot(self.dataset, response.json['version'])
        self.assertEqual(snapshot['processing_status'], 'ready')
        self.assertEqual(snapshot['episodes'], 46)
        self.assertTrue(all(row['instr'] == 'Wipe the board' for row in snapshot['episode_rows']))
        self.assertEqual(snapshot['episode_rows'][0]['annotation']['lowlevel_segments'], self.original[2]['annotation']['lowlevel_segments'])
        self.assertEqual(dp.dataset_episodes(dp.dataset_version_snapshot(self.dataset, 'v3')), self.original)
        self.assertEqual(dp.RUNS, self.saved_runs)

    def test_automation_only_plan_creates_pending_version(self):
        response = self.save({'base_version': 'v3', 'operations': [
            {'type': 'workflow', 'scope': 'all', 'target_id': 'pl1', 'params': {}},
        ]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(dp.RUNS[0]['status'], 'queued')
        self.assertEqual(dp.RUNS[0]['input_episodes'], self.original)
        self.assertEqual(self.dataset['version'], 'v3')

    def test_invalid_plans_have_no_side_effects(self):
        count = len(dp.ds_versions(self.dataset))
        valid_auto = {'type': 'operator', 'scope': 'all', 'target_id': 'op_split', 'params': {}}
        invalid_plans = [[], 'bad', [None], [{'type': 'unknown', 'scope': 'all'}],
                         [{'type': 'remove', 'scope': 'all'}],
                         [{'type': 'remove', 'scope': 'selected', 'episode_ids': [0, 0]}],
                         [{'type': 'prompt', 'scope': 'selected', 'episode_ids': [True], 'prompt': 'x'}],
                         [{'type': 'prompt', 'scope': 'all', 'prompt': ' '}],
                         [{**valid_auto, 'target_id': 'missing'}],
                         [{**valid_auto, 'scope': 'selected', 'episode_ids': [0]}],
                         [{**valid_auto, 'params': {'unknown-key': 'x'}}],
                         [valid_auto, {'type': 'remove', 'scope': 'selected', 'episode_ids': [0]}]]
        for plan in invalid_plans:
            with self.subTest(plan=plan):
                response = self.save({'base_version': 'v3', 'operations': plan})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(len(dp.ds_versions(self.dataset)), count)
                self.assertEqual(dp.RUNS, self.saved_runs)
                self.assertEqual(dp.dataset_episodes(self.dataset), self.original)

    def test_editor_uses_generic_operations_and_existing_catalog(self):
        config = self.config('v3')
        operator = next(item for item in config['catalog']['operator'] if item['id'] == 'op_split')
        self.assertIn({'key': '--seed', 'default': '42'}, operator['parameters'])
        draft_ids = {flow['id'] for flow in dp.PIPELINES if flow.get('status') == '草稿'}
        self.assertFalse(draft_ids.intersection(flow['id'] for flow in config['catalog']['workflow']))
        html = self.client.get('/model/data/datasets?sel=ds1').get_data(as_text=True)
        self.assertIn('id="datasetDetailView"', html)
        self.assertIn('id="datasetListView"', html)
        self.assertIn('class="ant-table dpr-record-table dataset-editor-table"', html)
        self.assertEqual(html.count('id="datasetEditorRows"'), 1)
        self.assertNotIn('id="datasetEditorDrawer"', html)
        self.assertIn('id="datasetOperationDrawer"', html)
        self.assertNotIn('id="procDrawer"', html)
        self.assertNotIn('<th>新 Prompt</th>', html)
        for label in ('剔除数据', '修改 Prompt', '执行算子', '执行工作流'):
            self.assertIn(label, html)

    def test_composition_uses_selected_version_episode_counts_and_duration(self):
        response = self.save(self.payload(self.original[1:]))
        self.assertEqual(response.status_code, 200)
        version = response.json['version']
        snapshot = dp.dataset_version_snapshot(self.dataset, version)
        episodes = dp.dataset_episodes(snapshot)
        self.assertEqual(sum(item['episode_count'] for item in dp.dataset_prompt_composition(snapshot)), 47)
        self.assertEqual(sum(item['frames'] for item in dp.dataset_prompt_composition(snapshot)), snapshot['frames'])
        for group in dp.dataset_tag_tree(snapshot):
            for tag in group['tags']:
                matching = [row for row in episodes if tag['name'] in row['tags']]
                self.assertEqual(tag['episode_count'], len(matching))
                self.assertEqual(tag['frames'], sum(row['length'] for row in matching))
        overlapping = deepcopy(snapshot)
        overlapping['episode_rows'] = deepcopy(episodes)
        overlapping['episode_rows'][0]['tags'] = ['抓取', '放置']
        skill_l2 = next(group for group in dp.dataset_tag_tree(overlapping, level=2)
                        if group['group'] == '技能')
        pick_place = next(tag for tag in skill_l2['tags'] if tag['name'] == '拿放类')
        matching = [row for row in overlapping['episode_rows'] if {'抓取', '放置'} & set(row['tags'])]
        self.assertEqual(pick_place['episode_count'], len(matching))
        self.assertEqual(pick_place['frames'], sum(row['length'] for row in matching))
        page = self.client.get('/model/data/datasets', query_string={
            'sel': 'ds1', 'ver': version, 'tab': 'compose',
        })
        self.assertEqual(page.status_code, 200)
        document = BeautifulSoup(page.data, 'html.parser')
        title_stats = document.select_one('#datasetWorkspace .dh-title .dataset-title-stats')
        seconds = round(snapshot['frames'] / snapshot['fps'])
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.assertEqual(title_stats.get_text(' ', strip=True),
                         f'条数 47 条 时长 {hours:02d}:{minutes:02d}:{seconds:02d}')
        pane = document.select_one('#pane-compose')
        self.assertIsNone(pane.select_one('.dataset-compose-overview'))
        for level in ('high', 'low'):
            sections = pane.select(f'#cmp_{level} > details.dataset-compose-section')
            self.assertEqual(len(sections), 2)
            self.assertTrue(sections[0].summary.text.strip().startswith('标签构成'))
            self.assertTrue(sections[1].summary.text.strip().startswith('Prompt 构成'))
            self.assertIn('47 条', sections[0].summary.text)
            self.assertIn('47 条', sections[1].summary.text)
            selector = sections[0].select_one('select.lvl-sel')
            self.assertEqual([option.text for option in selector.select('option')],
                             ['展示层级：二级', '展示层级：三级'])
            self.assertEqual(selector['onchange'], f"levelSel(this,'{level}')")
            self.assertIsNotNone(sections[0].select_one(f'#tag_{level}_l2 .pie-legend'))
            self.assertIsNotNone(sections[0].select_one(f'#tag_{level}_l3 .pie-legend'))
            self.assertIn('清洁类', sections[0].select_one(f'#tag_{level}_l2').text)
            self.assertIn('擦拭', sections[0].select_one(f'#tag_{level}_l3').text)
            self.assertEqual([th.text for th in sections[0].select_one('.pie-legend').select('th')],
                             ['标签', '占比', '条数', '时长'])
            self.assertEqual([span.text for span in sections[1].select_one('.recipe-header').select('span')],
                             ['Prompt', '占比', '条数', '时长'])


if __name__ == '__main__':
    unittest.main()
