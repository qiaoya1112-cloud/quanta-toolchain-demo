import unittest
from copy import deepcopy
from unittest.mock import patch

import toolchain_demo as platform


class ModelAssetTests(unittest.TestCase):
    def setUp(self):
        self.client = platform.app.test_client()

    def test_assets_use_available_checkpoints_and_imports(self):
        assets = platform._model_asset_records()
        expected = {row['id'] for row in platform.CHECKPOINTS + platform.UPLOADED_CKPTS
                    if row['status'] in {'merged', 'cached'}}
        self.assertEqual({row['id'] for row in assets}, expected)
        self.assertFalse({row['id'] for row in platform.MODELS} & expected)
        self.assertEqual([row['created'] for row in assets],
                         sorted([row['created'] for row in assets], reverse=True))

    def test_list_paginates_and_links_to_existing_details(self):
        assets = platform._model_asset_records()
        first = self.client.get('/model/models').get_data(as_text=True)
        second = self.client.get('/model/models?page=2').get_data(as_text=True)
        for index, model in enumerate(assets):
            page = first if index < 10 else second
            self.assertIn(f'href="/model/models/{model["id"]}"', page)
        self.assertNotIn(f'href="/model/models/{assets[10]["id"]}"', first)
        self.assertNotIn(f'href="/model/models/{assets[0]["id"]}"', second)
        self.assertIn('aria-label="下一页"', first)
        self.assertIn('aria-label="上一页"', second)
        self.assertEqual(first, self.client.get('/model/models?page=invalid').get_data(as_text=True))

    def test_each_detail_tab_renders_without_legacy_capabilities(self):
        for model in platform._model_asset_records():
            for tab in ('info', 'evaluations', 'lineage', 'artifacts'):
                with self.subTest(model=model['id'], tab=tab):
                    response = self.client.get(f'/model/models/{model["id"]}?tab={tab}')
                    self.assertEqual(response.status_code, 200)
                    page = response.get_data(as_text=True)
                    self.assertIn(model['name'], page)
                    for unsupported in ('Model Card', '转换产物', '推理格式', '使用限制', '适用场景', '版本记录', 'P95 延迟'):
                        self.assertNotIn(unsupported, page)
        for missing in ('unknown', 'md_901', '7466'):
            self.assertEqual(self.client.get(f'/model/models/{missing}').status_code, 404)

    def test_explicit_training_source_and_all_datasets(self):
        model = next(row for row in platform._model_asset_records() if row['id'] == '9004')
        self.assertEqual(model['description'], '—')
        context = platform._model_asset_context(model)
        self.assertEqual(context['experiment']['id'], 'DEMO_EXP_9003')
        self.assertEqual([row['id'] for row in context['datasets']], ['DEMO_DS_9002', 'DEMO_DS_9003'])
        page = self.client.get('/model/models/9004').get_data(as_text=True)
        self.assertIn('href="/model/experiments/DEMO_EXP_9003"', page)
        for dataset in context['datasets']:
            self.assertIn(f'href="/model/data/datasets/{dataset["id"]}"', page)
            self.assertEqual(self.client.get(f'/model/data/datasets/{dataset["id"]}').status_code, 200)
        self.assertNotIn('href="/data/datasets', page)

    def test_missing_source_does_not_guess_by_id_or_name(self):
        checkpoint = deepcopy(platform.CHECKPOINTS[0])
        checkpoint.update(id='7916', exp_id='missing-task')
        with patch.object(platform, 'CHECKPOINTS', [checkpoint]):
            model = next(row for row in platform._model_asset_records() if row['id'] == '7916')
            context = platform._model_asset_context(model)
            self.assertIsNone(context['experiment'])
            self.assertEqual(context['datasets'], [])
            page = self.client.get('/model/models/7916').get_data(as_text=True)
            self.assertIn('missing-task', page)
            self.assertIn('暂无关联数据集', page)
            self.assertNotIn('href="/model/experiments/exp_7916"', page)

    def test_evaluations_match_only_current_checkpoint(self):
        model = next(row for row in platform._model_asset_records() if row['id'] == '9001')
        records = [{'id': 'other', 'ckpt_id': '9002', 'at': '2026-01-03'},
                   {'id': 'older', 'ckpt_id': '9001', 'at': '2026-01-01'},
                   {'id': 'newer', 'ckpt_id': '9001', 'at': '2026-01-02'}]
        with patch.object(platform, '_evaluation_lineage_records', return_value=records):
            self.assertEqual([row['id'] for row in platform._model_asset_context(model)['evaluations']],
                             ['newer', 'older'])
        page = self.client.get('/model/models/9001?tab=evaluations').get_data(as_text=True)
        self.assertIn('href="/model/eval/tasks/t7/statistics" target="_blank" rel="noopener noreferrer"', page)
        self.assertNotIn('href="/model/eval/tasks/t8/statistics"', page)
        self.assertNotIn('href="/model/eval/tasks/t7"', page)
        response = self.client.get('/model/eval/tasks/t7/statistics')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<h1>评测统计</h1>', response.get_data(as_text=True))
        task = platform.ep.get_task('t7')
        benchmark = platform.ep.get_benchmark(task['benchmark_id'])
        self.assertIn(f'<b title="{benchmark["name"]}">{benchmark["name"]}</b>', response.get_data(as_text=True))

    def test_external_imports_sync_without_linking_to_platform_training(self):
        with patch.object(platform, 'UPLOADED_CKPTS', deepcopy(platform.UPLOADED_CKPTS)), \
                patch.object(platform, 'CKPT_CACHE_OPERATIONS', []), \
                patch.object(platform, 'REGISTERED_MODEL_CHECKPOINT_IDS', set(platform.REGISTERED_MODEL_CHECKPOINT_IDS)):
            response = self.client.post('/model/checkpoints/upload', data={
                'name': 'new_external_12345', 'step': '12345', 'base_model': 'external-base',
                'train_task_id': 'TRAIN-456', 'storage_address': 's3://external/weights',
                'merge_mode': 'merge',
            })
            self.assertEqual(response.status_code, 303)
            uploaded = platform.UPLOADED_CKPTS[-1]
            self.assertEqual(uploaded['status'], 'merging')
            self.assertNotIn(uploaded['id'], {row['id'] for row in platform._model_asset_records()})
            operation = platform.CKPT_CACHE_OPERATIONS[-1]
            self.assertEqual(self.client.post(
                f'/model/checkpoints/cache-operations/{operation["operation_id"]}/result',
                json={'result': 'cached'},
            ).status_code, 200)
            self.assertEqual(self.client.post(
                f'/model/checkpoints/{uploaded["id"]}/register-model',
                data={'model_name': uploaded['name'], 'description': '外部模型说明'},
            ).status_code, 303)
            model = next(row for row in platform._model_asset_records() if row['name'] == 'new_external_12345')
            self.assertEqual(model['step'], 12345)
            self.assertEqual(model['status'], 'merged')
            self.assertEqual(platform._model_asset_context(model)['datasets'], [])
            page = self.client.get(f'/model/models/{model["id"]}').get_data(as_text=True)
            self.assertIn('s3://external/weights', page)
            self.assertIn('外部导入时登记', page)
            self.assertNotIn('href="/model/experiments/', page)
            filtered = self.client.get('/model/models', query_string={
                'ckpt_id': uploaded['id'], 'checkpoint': 'NEW_EXTERNAL',
                'name': 'NEW_EXTERNAL', 'base': 'external-base',
                'registered_by': platform.CURRENT_USER.upper(),
            }).get_data(as_text=True)
            self.assertIn(f'href="/model/models/{model["id"]}"', filtered)
            self.assertNotIn('href="/model/models/9001"', filtered)

    def test_combined_filters_empty_state_and_pagination_keep_filters(self):
        page = self.client.get('/model/models?base=Spirit+v1.7').get_data(as_text=True)
        self.assertNotIn('href="/model/models/UP8001"', page)
        self.assertIn('ckpt_id=&amp;checkpoint=&amp;name=&amp;base=Spirit+v1.7&amp;registered_by=&amp;page=2', page)
        self.assertIn('暂无符合条件的模型', self.client.get('/model/models?name=missing').get_data(as_text=True))
        self.assertIn('暂无符合条件的模型', self.client.get('/model/models?ckpt_id=UP8001&base=Spirit+v1.7').get_data(as_text=True))

    def test_edit_description_for_training_and_imported_models(self):
        with patch.object(platform, 'CHECKPOINTS', deepcopy(platform.CHECKPOINTS)), \
                patch.object(platform, 'UPLOADED_CKPTS', deepcopy(platform.UPLOADED_CKPTS)), \
                patch.object(platform, 'CKPT_CACHE_OPERATIONS', []):
            assets = platform._model_asset_records()
            for source in ('training', 'upload'):
                model = next(row for row in assets if row['source'] == source)
                original = next(row for row in platform.CHECKPOINTS + platform.UPLOADED_CKPTS
                                if row['id'] == model['id'])
                before = deepcopy(original)
                description = '编辑描述 <script>alert("test")</script> & 说明'
                response = self.client.post(f'/model/models/{model["id"]}/edit', json={
                    'description': f'  {description}  ', 'name': '不应修改名称', 'status': 'unmerged',
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(original, {**before, 'model_description': description})
                for path in (f'/model/models?ckpt_id={model["id"]}', f'/model/models/{model["id"]}'):
                    page = self.client.get(path).get_data(as_text=True)
                    self.assertIn('编辑描述 &lt;script&gt;', page)
                    self.assertNotIn('<script>alert("test")</script>', page)
                self.assertEqual(self.client.post(f'/model/models/{model["id"]}/edit',
                                                 json={'description': '  '}).status_code, 200)
                updated = next(row for row in platform._model_asset_records() if row['id'] == model['id'])
                self.assertEqual(updated['description'], '—')

    def test_edit_description_rejects_missing_assets_and_invalid_values(self):
        with patch.object(platform, 'CHECKPOINTS', deepcopy(platform.CHECKPOINTS)), \
                patch.object(platform, 'UPLOADED_CKPTS', deepcopy(platform.UPLOADED_CKPTS)), \
                patch.object(platform, 'CKPT_CACHE_OPERATIONS', []):
            before = deepcopy(platform.CHECKPOINTS + platform.UPLOADED_CKPTS)
            for payload in ({}, {'description': None}, {'description': []}, []):
                self.assertEqual(self.client.post('/model/models/9004/edit', json=payload).status_code, 400)
            for model_id in ('unknown', '7466'):
                self.assertEqual(self.client.post(f'/model/models/{model_id}/edit',
                                                 json={'description': '不可修改'}).status_code, 404)
            self.assertEqual(platform.CHECKPOINTS + platform.UPLOADED_CKPTS, before)

    def test_model_text_is_escaped_in_both_views(self):
        checkpoint = deepcopy(platform.CHECKPOINTS[0])
        checkpoint.update(name='<script>alert(1)</script>', description='<img src=x onerror=alert(1)>')
        with patch.object(platform, 'CHECKPOINTS', [checkpoint]), patch.object(platform, 'UPLOADED_CKPTS', []):
            for path in ('/model/models', f'/model/models/{checkpoint["id"]}'):
                page = self.client.get(path).get_data(as_text=True)
                self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
                self.assertNotIn('<script>alert(1)</script>', page)
                self.assertNotIn('<img src=x onerror=alert(1)>', page)

    def test_basic_information_has_requested_fields_and_dataset_weights(self):
        page = self.client.get('/model/models/9004').get_data(as_text=True)
        for label in ('名称', '描述', '基础模型', '训练任务', '步数', '来源', '存储地址'):
            self.assertIn(f'<div class="bi-field-label">{label}</div>', page)
        self.assertIn('aria-label="数据集与权重"', page)
        self.assertLess(page.index('bi-field-label">来源'), page.index('bi-field-label">存储地址'))
        self.assertLess(page.index('bi-field-label">存储地址'), page.index('bi-subsection-title">数据集与权重'))
        self.assertIn('<th>权重</th>', page)
        model = next(row for row in platform._model_asset_records() if row['id'] == '9004')
        self.assertEqual([row['weight'] for row in platform._model_asset_context(model)['datasets']], [1, 1])
        self.assertIn('tos://quanta-model/checkpoints/20260618_tidy_desk_joint_train_35000.pt', page)
        self.assertIn('href="/model/experiments/DEMO_EXP_9003"', page)

    def test_evaluation_information_has_exactly_requested_columns(self):
        page = self.client.get('/model/models/9001?tab=evaluations').get_data(as_text=True)
        self.assertIn('<thead><tr><th>任务 ID</th><th>名称</th><th>评测集</th><th>创建时间</th></tr></thead>', page)
        self.assertNotIn('<th>状态</th>', page)
        self.assertNotIn('<th>成功率</th>', page)

    def test_lineage_tab_reuses_checkpoint_canvas_and_preserves_detail_navigation(self):
        page = self.client.get('/model/models/9004?tab=lineage').get_data(as_text=True)
        self.assertIn(platform._lineage_detail_html('checkpoint', '9004', view_path='/model/models/9004'), page)
        for tab, label in (('info', '基本信息'), ('evaluations', '评测信息'), ('lineage', '血缘关系')):
            self.assertIn(f'href="/model/models/9004?tab={tab}"', page)
            self.assertIn(f'>{label}</a>', page)
        for control in ('linViewport', 'linInput', 'linZoomValue', 'linBackView', 'linHistoryToggle'):
            self.assertIn(f'id="{control}"', page)
        self.assertIn('href="/model/models"', page)

    def test_registration_records_actor_and_time_once_and_keeps_checkpoint_name(self):
        with patch.object(platform, 'CHECKPOINTS', deepcopy(platform.CHECKPOINTS)), \
                patch.object(platform, 'REGISTERED_MODEL_CHECKPOINT_IDS', set(platform.REGISTERED_MODEL_CHECKPOINT_IDS)), \
                patch.object(platform, 'CKPT_CACHE_OPERATIONS', []):
            checkpoint = next(row for row in platform.CHECKPOINTS if row['id'] == '9004')
            checkpoint['model_name'] = '桌面整理模型'
            platform.REGISTERED_MODEL_CHECKPOINT_IDS.discard(checkpoint['id'])
            with patch.object(platform, 'datetime') as clock:
                clock.now.return_value.strftime.return_value = '2026-10-20 15:20:00'
                self.assertEqual(self.client.post('/model/checkpoints/9004/register-model',
                                     data={'model_name': '桌面整理模型', 'description': '整理桌面'}).status_code, 303)
            with patch.object(platform, 'CURRENT_USER', 'another.user'), patch.object(platform, 'datetime') as clock:
                clock.now.return_value.strftime.return_value = '2026-10-21 16:30:00'
                self.client.post('/model/checkpoints/9004/register-model',
                                     data={'model_name': '桌面整理模型', 'description': '整理桌面'})
            model = next(row for row in platform._model_asset_records() if row['id'] == '9004')
            self.assertEqual(model['name'], '桌面整理模型')
            self.assertEqual(model['checkpoint_name'], checkpoint['name'])
            self.assertEqual(model['registered_by'], platform.CURRENT_USER)
            self.assertEqual(model['registered_at'], '2026-10-20 15:20:00')
            for query in ({'name': '桌面整理模型'}, {'checkpoint': checkpoint['name']},
                          {'ckpt_id': '9004', 'checkpoint': checkpoint['name'].upper(),
                           'name': '整理', 'base': model['base'],
                           'registered_by': platform.CURRENT_USER.upper()}):
                page = self.client.get('/model/models', query_string=query).get_data(as_text=True)
                self.assertIn('href="/model/models/9004"', page)
                self.assertIn('2026-10-20 15:20:00', page)
            for query in ({'name': checkpoint['name']}, {'checkpoint': '桌面整理模型'},
                          {'ckpt_id': '9004', 'registered_by': 'another.user'}):
                page = self.client.get('/model/models', query_string=query).get_data(as_text=True)
                self.assertNotIn('href="/model/models/9004"', page)


if __name__ == '__main__':
    unittest.main()
