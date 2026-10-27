import html
import re
import unittest
from copy import deepcopy
from unittest.mock import patch

import toolchain_demo as platform


class CheckpointProcessingTests(unittest.TestCase):
    def setUp(self):
        self.client = platform.app.test_client()
        for field in ('CHECKPOINTS', 'UPLOADED_CKPTS', 'CKPT_CACHE_OPERATIONS',
                      'REGISTERED_MODEL_CHECKPOINT_IDS', 'DEPLOYS', 'DEVICES'):
            mock = patch.object(platform, field, deepcopy(getattr(platform, field)))
            mock.start()
            self.addCleanup(mock.stop)

    def import_checkpoint(self, mode='cache'):
        response = self.client.post('/model/checkpoints/upload', data={
            'name': 'external-processing-weights', 'merge_mode': mode,
            'source_platform': '金山云', 'train_task_id': 'TRAIN-123',
            'base_model': 'pi0.5', 'step': '60000',
            'storage_address': 'ks3://weights/test/',
        })
        self.assertEqual(response.status_code, 303)
        return platform.UPLOADED_CKPTS[-1], platform.CKPT_CACHE_OPERATIONS[-1]

    def finish(self, operation, result):
        return self.client.post(
            f'/model/checkpoints/cache-operations/{operation["operation_id"]}/result',
            json={'result': result},
        )

    def test_processing_list_replaces_old_list_and_legacy_links_preserve_filters(self):
        page = self.client.get('/model/checkpoints?page_size=50').get_data(as_text=True)
        self.assertIn('训练任务 ID</label><input name="train_task_id"', page)
        self.assertNotIn('<input name="train_task_name"', page)
        self.assertIn('data-status="unmerged"', page)
        self.assertIn('data-status="cache_failed"', page)
        self.assertIn('ckpt-status-filter', page)
        self.assertIn('ckptStatusLogModalMask', page)
        self.assertNotIn('>TEST</a>', page)
        self.assertNotIn('ckpt-cache-action', page)
        detail_ids = re.findall(r'data-detail-id="([^"]+)"', page)
        self.assertTrue(detail_ids)
        for drawer_id in detail_ids:
            self.assertIn(f'id="{drawer_id}" role="dialog"', page)
        response = self.client.get('/model/checkpoints/cache-records?resource=kingsoft&operation_id=cache-op-2')
        self.assertEqual(response.location, '/model/checkpoints?resource=kingsoft&operation_id=cache-op-2')

    def test_import_uses_training_task_id_in_checkpoint_details(self):
        uploaded, operation = self.import_checkpoint()
        self.assertEqual(uploaded['train_task_id'], 'TRAIN-123')
        self.assertEqual(operation['experiment_name'], 'TRAIN-123')
        page = self.client.get('/model/checkpoints?resource=kingsoft&page_size=50').get_data(as_text=True)
        self.assertIn('>TRAIN-123</div>', page)

    def test_all_five_actions_are_gated_for_every_status(self):
        for status in platform.CKPT_STATUS_LABEL:
            with self.subTest(status=status), platform.app.test_request_context('/model/checkpoints'):
                row = platform._ckpt_rows_html([{
                    'id': 'test', 'name': 'checkpoint', 'status': status,
                    'owner': 'Joanna Qiao', 'created': '2026-10-20 10:00:00',
                }])
                actions = re.search(r'<td class="actions-cell">(.*?)</td>', row, re.S).group(1)
                self.assertIn('data-detail-id="drawerCkpttest"', actions)
                self.assertLess(actions.index('>详情<'), actions.index('>评测<'))
                for label in ('评测', 'DAgger', '血缘', '部署', '登记为模型'):
                    self.assertIn(f'>{label}<', actions)
                if status in {'merged', 'cached'}:
                    self.assertEqual(actions.count('<a '), 5)
                    self.assertIn('register-model', actions)
                    self.assertNotIn('aria-disabled', actions)
                else:
                    self.assertEqual(actions.count('aria-disabled="true"'), 5)
                    self.assertEqual(actions.count('href='), 1)
                    self.assertNotIn('<form', actions)

    def test_status_filter_paginates_after_filtering_and_logs_still_open(self):
        for resource, status in [('volcano', 'cache_failed'), ('volcano', 'merge_failed'),
                                 ('kingsoft', 'caching'), ('kingsoft', 'merging')]:
            with self.subTest(resource=resource, status=status):
                response = self.client.get(f'/model/checkpoints?resource={resource}&status={status}&page_size=10')
                self.assertEqual(response.status_code, 200)
                page = response.get_data(as_text=True)
                self.assertEqual(set(re.findall(r'<tr data-status="([^"]+)"', page)), {status})
                self.assertIn(f'class="ckpt-status-option active" data-value="{status}"', page)
                if status.endswith('_failed'):
                    self.assertIn('onclick="openCkptStatusLog(this)"', page)
        page = self.client.get('/model/checkpoints').get_data(as_text=True)
        self.assertLessEqual(len(re.findall(r'<tr data-status=', page)), 10)
        self.assertIn('aria-label="下一页"', page)

    def test_import_waits_for_processing_then_registration_and_can_deploy(self):
        uploaded, operation = self.import_checkpoint()
        self.assertEqual(uploaded['status'], 'merging')
        self.assertTrue(operation['cache_server'])
        self.assertEqual(self.client.post(f'/model/checkpoints/{uploaded["id"]}/register-model').status_code, 409)
        page = self.client.get(platform._cache_operation_record_url(operation)).get_data(as_text=True)
        self.assertEqual(page.count('<tr data-status="merging">'), 1)
        self.assertNotIn('data-status="cached"', page)
        self.assertEqual(self.finish(operation, 'cached').status_code, 200)
        self.assertEqual(platform._ckpt_by_id(uploaded['id'])['status'], 'cached')
        self.assertNotIn(uploaded['id'], {m['id'] for m in platform._model_asset_records()})
        response = self.client.post(f'/model/checkpoints/{uploaded["id"]}/register-model',
                                    data={'model_name': '外部模型', 'description': '外部模型说明'})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.client.get(response.location).status_code, 200)
        self.assertIn(uploaded['id'], {m['id'] for m in platform._model_asset_records()})
        self.client.post(f'/model/checkpoints/{uploaded["id"]}/register-model',
                         data={'model_name': '外部模型', 'description': '外部模型说明'})
        self.assertEqual(sum(m['id'] == uploaded['id'] for m in platform._model_asset_records()), 1)
        page = self.client.get('/model/deploy?deploy_checkpoint=' + uploaded['name']).get_data(as_text=True)
        self.assertIn(f'class="ddp-item on" data-value="{uploaded["name"]}"', page)

    def test_merge_only_and_failed_imports_keep_correct_actions(self):
        uploaded, operation = self.import_checkpoint('merge')
        self.assertFalse(operation['cache_server'])
        self.assertEqual(self.finish(operation, 'cache_failed').status_code, 400)
        self.assertEqual(self.finish(operation, 'merge_failed').status_code, 200)
        self.assertEqual(platform._ckpt_by_id(uploaded['id'])['status'], 'merge_failed')
        self.assertEqual(self.client.post(f'/model/checkpoints/{uploaded["id"]}/register-model').status_code, 409)
        self.assertEqual(self.finish(operation, 'cached').status_code, 200)
        self.assertEqual(platform._ckpt_by_id(uploaded['id'])['status'], 'merged')

    def test_training_processing_result_can_be_registered_and_traced(self):
        experiment = platform.EXPERIMENTS[0]
        with patch.object(platform, '_task_ckpts', return_value=[{'step': '60000', 'location': 'tos://train/shards'}]):
            response = self.client.post(f'/model/experiments/{experiment["id"]}/cache-checkpoints', json={
                'name': 'training-processing-weights', 'description': 'ready for evaluation',
                'step': '60000', 'cache_server': False,
            })
        self.assertEqual(response.status_code, 200)
        operation = platform.CKPT_CACHE_OPERATIONS[-1]
        self.assertEqual(self.finish(operation, 'cached').status_code, 200)
        response = self.client.post(f'/model/checkpoints/{operation["id"]}/register-model',
                                    data={'model_name': '训练模型', 'description': '训练模型说明'})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.client.get(response.location).status_code, 200)
        self.assertEqual(self.client.get(f'/model/lineage/checkpoint/{operation["id"]}').status_code, 200)

    def test_registration_drawer_prefills_escaped_checkpoint_fields_without_registering(self):
        checkpoint = next(c for c in platform.CHECKPOINTS if c['status'] == 'merged')
        checkpoint.update(name='模型 "A" <v1>', description='已有描述 "测试" <说明>\n第二行')
        platform.REGISTERED_MODEL_CHECKPOINT_IDS.discard(checkpoint['id'])
        with platform.app.test_request_context('/model/checkpoints'):
            row = platform._ckpt_rows_html([checkpoint])
        self.assertIn('onclick="openCkptRegisterDrawer(this)"', row)
        self.assertIn('data-model-name="' + html.escape(checkpoint['name'], quote=True) + '"', row)
        self.assertIn('data-description="' + html.escape(checkpoint['description'], quote=True) + '"', row)
        self.assertNotIn('<form', row)
        page = self.client.get('/model/checkpoints').get_data(as_text=True)
        self.assertIn('id="drawerCkptRegister"', page)
        self.assertIn('name="model_name" required', page)
        self.assertIn('name="description" rows="4" required', page)
        self.assertNotIn(checkpoint['id'], platform.REGISTERED_MODEL_CHECKPOINT_IDS)

    def test_registration_saves_model_metadata_without_changing_checkpoint(self):
        uploaded, operation = self.import_checkpoint()
        uploaded['description'] = operation['description'] = '原始 Ckpt 描述'
        self.finish(operation, 'cached')
        response = self.client.post(f'/model/checkpoints/{uploaded["id"]}/register-model', json={
            'model_name': '  精选模型 <A>  ', 'description': '  修改后的模型描述\n第二行  ',
        })
        self.assertEqual(response.status_code, 200)
        model = next(m for m in platform._model_asset_records() if m['id'] == uploaded['id'])
        self.assertEqual(model['name'], '精选模型 <A>')
        self.assertEqual(model['description'], '修改后的模型描述\n第二行')
        self.assertEqual(model['checkpoint_name'], uploaded['name'])
        for source in (uploaded, operation, platform._ckpt_by_id(uploaded['id'])):
            self.assertEqual(source['description'], '原始 Ckpt 描述')
            self.assertEqual(source['model_name'], model['name'])
            self.assertEqual(source['model_description'], model['description'])
        page = self.client.get(response.get_json()['model_url']).get_data(as_text=True)
        self.assertIn('精选模型 &lt;A&gt;', page)
        self.assertIn('修改后的模型描述', page)

    def test_registration_rejects_incomplete_fields_without_creating_asset(self):
        checkpoint = next(c for c in platform.CHECKPOINTS if c['status'] == 'merged')
        platform.REGISTERED_MODEL_CHECKPOINT_IDS.discard(checkpoint['id'])
        endpoint = f'/model/checkpoints/{checkpoint["id"]}/register-model'
        for payload in ({}, [], {'model_name': '   ', 'description': '描述'},
                        {'model_name': ['模型'], 'description': '描述'},
                        {'model_name': '模型', 'description': '  '},
                        {'model_name': '模型', 'description': None}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post(endpoint, json=payload).status_code, 400)
        self.assertEqual(self.client.post(endpoint).status_code, 400)
        self.assertEqual(self.client.post('/model/checkpoints/missing/register-model').status_code, 404)
        self.assertNotIn(checkpoint['id'], platform.REGISTERED_MODEL_CHECKPOINT_IDS)

    def test_deploy_opens_device_drawer_on_checkpoint_page(self):
        page = self.client.get('/model/checkpoints').get_data(as_text=True)
        self.assertIn('id="drawerCkptDeploy"', page)
        self.assertIn('onclick="openCkptDeployDrawer(this);return false;"', page)
        self.assertIn('id="ckptDeployResultModal"', page)
        self.assertIn('部署任务已下发至设备平台', page)
        self.assertIn('id="ckptDeployProgressLink"', page)
        self.assertIn('请选择部署设备', page)
        self.assertNotIn('data-id="moz2-002"', page)

    def test_deploy_creates_device_task_for_selected_devices_and_returns_progress(self):
        for status in ('merged', 'cached'):
            with self.subTest(status=status):
                checkpoint = next(c for c in platform.CHECKPOINTS if c['status'] == status)
                response = self.client.post(f'/model/checkpoints/{checkpoint["id"]}/deploy', json={
                    'devices': ['moz1-001', 'moz1-003', 'moz1-001'],
                })
                self.assertEqual(response.status_code, 201)
                result = response.get_json()
                self.assertEqual(result['message'], '部署任务已下发至设备平台')
                task = platform.DEPLOYS[0]
                self.assertEqual(task['targets'], ['moz1-001', 'moz1-003'])
                self.assertEqual(task['checkpoint_id'], checkpoint['id'])
                self.assertEqual(task['status'], 'in_progress')
                self.assertEqual(task['progress']['running'], 2)
                self.assertEqual(task['id'], result['deployment_id'])
                self.assertTrue(result['progress_url'].startswith('/device/deployments/'))
                page = self.client.get(result['progress_url']).get_data(as_text=True)
                for value in (task['id'], checkpoint['name'], 'moz1-001', 'moz1-003', '部署中'):
                    self.assertIn(value, page)
                self.assertIn(task['id'], self.client.get('/device/devices').get_data(as_text=True))
                task['device_statuses']['moz1-001'] = 'deployed'
                task['progress'].update(success=1, running=1)
                page = self.client.get(result['progress_url']).get_data(as_text=True)
                self.assertIn('成功 1', page)
                self.assertIn('<span class="tag tag-green">成功</span>', page)

    def test_deploy_rejects_unavailable_checkpoints_and_invalid_devices(self):
        count = len(platform.DEPLOYS)
        for status in set(platform.CKPT_STATUS_LABEL) - {'merged', 'cached'}:
            checkpoint = platform.CHECKPOINTS[0]
            checkpoint['status'] = status
            response = self.client.post(f'/model/checkpoints/{checkpoint["id"]}/deploy',
                                        json={'devices': ['moz1-001']})
            self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.post('/model/checkpoints/missing/deploy', json={'devices': ['moz1-001']}).status_code, 404)
        checkpoint['status'] = 'cached'
        for payload in ({}, {'devices': []}, {'devices': 'moz1-001'}, {'devices': [{}]},
                        {'devices': ['missing']}, {'devices': ['moz2-002']},
                        {'devices': ['moz1-001', 'moz2-002']}):
            with self.subTest(payload=payload):
                response = self.client.post(f'/model/checkpoints/{checkpoint["id"]}/deploy', json=payload)
                self.assertEqual(response.status_code, 400)
        self.assertEqual(len(platform.DEPLOYS), count)


if __name__ == '__main__':
    unittest.main()
