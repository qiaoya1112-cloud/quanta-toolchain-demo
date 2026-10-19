import unittest
from copy import deepcopy
from unittest.mock import patch

import toolchain_demo as platform


class ModelAssetTests(unittest.TestCase):
    def setUp(self):
        self.client = platform.app.test_client()

    def test_list_links_to_model_and_matching_dataset_inside_model_platform(self):
        page = self.client.get('/model/models').get_data(as_text=True)
        for model in platform.MODELS:
            self.assertIn(f'href="/model/models/{model["id"]}"', page)
            dataset = platform._dataset_by_id_or_name(model['from_dataset'])
            self.assertIn(f'href="/model/data/datasets/{dataset["id"]}"', page)
        self.assertNotIn('href="/data/datasets', page)

    def test_each_detail_tab_renders_for_every_model(self):
        for model in platform.MODELS:
            for tab in ('card', 'artifacts', 'evaluations', 'deployments', 'versions'):
                with self.subTest(model=model['id'], tab=tab):
                    response = self.client.get(f'/model/models/{model["id"]}?tab={tab}')
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(model['name'], response.get_data(as_text=True))
        self.assertEqual(self.client.get('/model/models/unknown').status_code, 404)

    def test_dataset_link_resolves_to_correct_detail_and_platform(self):
        page = self.client.get('/model/models/md_901').get_data(as_text=True)
        self.assertIn('href="/model/data/datasets/ds_501"', page)
        response = self.client.get('/model/data/datasets/ds_501')
        self.assertEqual(response.status_code, 200)
        self.assertIn('clean_whiteboard_v4', response.get_data(as_text=True))
        self.assertIn('模型平台', response.get_data(as_text=True))

    def test_version_specific_relationships_do_not_mix_same_name_models(self):
        first = platform._model_asset_context(platform.MODELS[0])
        newer = platform._model_asset_context(platform.MODELS[2])
        self.assertEqual([row['id'] for row in first['artifacts']], ['cv_a01'])
        self.assertEqual([row['id'] for row in newer['artifacts']], ['cv_a02'])
        self.assertEqual([row['id'] for row in first['deployments']], ['dp_801'])
        self.assertEqual([row['id'] for row in newer['deployments']], ['dp_803'])
        self.assertEqual([row['id'] for row in first['services']], ['svc_a02'])
        self.assertEqual(newer['services'], [])
        self.assertEqual([row['id'] for row in first['versions']], ['md_903', 'md_901'])

    def test_missing_source_keeps_original_reference_without_inventing_links(self):
        page = self.client.get('/model/models/md_901').get_data(as_text=True)
        self.assertIn('exp_601', page)
        self.assertIn('暂无对应任务记录', page)
        self.assertNotIn('href="/model/experiments/exp_601"', page)
        self.assertIn('暂未关联', page)
        self.assertIn('暂无关联评测记录', self.client.get(
            '/model/models/md_901?tab=evaluations').get_data(as_text=True))

    def test_evaluations_require_explicit_model_or_checkpoint_reference(self):
        model = deepcopy(platform.MODELS[0])
        records = [{'id': 'unrelated', 'ckpt_id': '9002', 'at': '2026-01-01'},
                   {'id': 'linked', 'ckpt_id': '9001', 'at': '2026-01-02'},
                   {'id': 'direct', 'model_id': model['id'], 'at': '2026-01-03'}]
        with patch.object(platform, '_evaluation_lineage_records', return_value=records):
            self.assertEqual([r['id'] for r in platform._model_asset_context(model)['evaluations']], ['direct'])
            model['checkpoint_id'] = '9001'
            self.assertEqual([r['id'] for r in platform._model_asset_context(model)['evaluations']], ['direct', 'linked'])
            page = platform.app.test_client()
            with patch.object(platform, 'MODELS', [model]):
                self.assertEqual(page.get('/model/models/md_901?tab=evaluations').status_code, 200)

    def test_filters_combine_and_show_empty_results(self):
        page = self.client.get('/model/models?name=WHITEBOARD&base=Spirit+v1.6').get_data(as_text=True)
        self.assertIn('href="/model/models/md_902"', page)
        self.assertNotIn('href="/model/models/md_901"', page)
        self.assertIn('暂无符合条件的模型', self.client.get(
            '/model/models?name=missing').get_data(as_text=True))

    def test_detail_escapes_model_card_text(self):
        model = deepcopy(platform.MODELS[0])
        model['description'] = '<script>alert(1)</script>'
        with patch.object(platform, 'MODELS', [model]):
            page = self.client.get('/model/models/md_901').get_data(as_text=True)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
        self.assertNotIn('<script>alert(1)</script>', page)


if __name__ == '__main__':
    unittest.main()
