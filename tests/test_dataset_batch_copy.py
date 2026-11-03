import json
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

import data_platform as dp
import toolchain_demo


class DatasetBatchCopyTests(unittest.TestCase):
    def test_v1_publication_migration_preserves_later_drafts(self):
        from copy import deepcopy
        dataset = deepcopy(dp.get_ds('ds1'))
        dataset['id'] = 'publication-migration-test'
        dp.DS_VERSIONS[dataset['id']] = [
            {'version': version, 'publish_status': '未发布', 'status': '未生效',
             'snapshot': {**dataset, 'version': version, 'publish_status': '未发布'}}
            for version in ('v4', 'v1')]
        try:
            dataset['version'] = 'v1'
            versions = dp.ds_versions(dataset)
            self.assertEqual([row['publish_status'] for row in versions], ['未发布', '已发布'])
            self.assertEqual(versions[1]['snapshot']['publish_status'], '已发布')
            self.assertEqual(dataset['publish_status'], '已发布')
        finally:
            dp.DS_VERSIONS.pop(dataset['id'], None)

    def test_copy_metadata_uses_snapshot_and_only_object_storage_paths(self):
        dataset = {"id": "copy-test", "version": "v2"}
        snapshot = {**dataset, "name": "测试数据集", "format": "Mozdataset v2",
                    "third_party_storage_address": "ks3://bucket/imports/demo.zip",
                    "tos": "tos://bucket/data/v2/", "storage_locations": [
                        "火山云", "金山云", "/mnt/data", "https://example.com/data",
                        "tos://bucket/data/v2/", "—", "tos://"]}
        with patch.object(dp, "dataset_version_snapshot", return_value=snapshot) as get_snapshot:
            result = dp.dataset_copy_metadata(dataset)
        get_snapshot.assert_called_once_with(dataset, "v2")
        self.assertEqual(result, {"id": "copy-test", "ident": "copy-test", "name": "测试数据集", "version": "v2",
                                  "format": "mozdataset v2", "vepfs_addresses": [], "addresses": [
                                      "ks3://bucket/imports/demo.zip", "tos://bucket/data/v2/"]})

    def test_missing_storage_is_not_fabricated(self):
        snapshot = {"id": "copy-test", "name": "待生成", "version": "v1",
                    "tos": "—", "storage_locations": ["火山云", "金山云"]}
        with patch.object(dp, "dataset_version_snapshot", return_value=snapshot):
            self.assertEqual(dp.dataset_copy_metadata(snapshot)["addresses"], [])

    def test_vepfs_paths_are_separate_from_object_storage(self):
        snapshot = {"id": "paths", "name": "路径测试", "version": "v2", "format": "Mozdataset v2",
                    "tos": "tos://bucket/data/", "vepfs": "/mnt/vepfs01/data/v2/",
                    "storage_locations": ["/mnt/local/data/", "vepfs://cluster/data/v2/", "火山云"]}
        with patch.object(dp, "dataset_version_snapshot", return_value=snapshot):
            result = dp.dataset_copy_metadata(snapshot)
        self.assertEqual(result["format"], "mozdataset v2")
        self.assertEqual(result["addresses"], ["tos://bucket/data/"])
        self.assertEqual(result["vepfs_addresses"], ["vepfs://cluster/data/v2/", "/mnt/vepfs01/data/v2/"])

    def test_page_copy_config_matches_filtered_dataset_checkboxes(self):
        client = toolchain_demo.app.test_client()
        response = client.get('/model/data/datasets?keyword=clean_whiteboard_v3')
        self.assertEqual(response.status_code, 200)
        doc = BeautifulSoup(response.data, 'html.parser')
        config = json.loads(doc.select_one('#datasetTreeCopyConfig').string)
        self.assertEqual([item['id'] for item in config], ['ds1'])
        self.assertEqual([node['value'] for node in doc.select('.dataset-tree-checkbox')], ['ds1'])
        self.assertEqual(len(doc.select('[data-dataset-copy]')), 3)
        self.assertIsNone(doc.select_one('#datasetTreeSelectAll'))
        leaf = doc.select_one('.dataset-tree-checkbox')
        self.assertEqual(len(leaf.find_parents('section', class_='dataset-folder')), 3)
        self.assertIsNotNone(doc.select_one('#datasetPreviewButton'))
        self.assertIsNotNone(doc.select_one('#datasetGenerateModal #datasetGenerateCopy'))
        self.assertIsNotNone(doc.select_one('#datasetGenerateContent'))
        self.assertEqual(doc.select_one('#datasetGenerateNotice').get_text(), '预览生成中，生成完成会通过飞书通知')
        self.assertIn('tos://embodied/datasets/clean_whiteboard_v3/', config[0]['addresses'])

    def test_version_options_default_latest_and_keep_only_published_alternatives(self):
        dataset = {'id': 'test', 'version': 'v2'}
        versions = [
            {'version': 'v2', 'publish_status': '已发布'},
            {'version': 'v4', 'publish_status': '未发布'},
            {'version': 'v3', 'publish_status': '未发布'},
            {'version': 'v1', 'publish_status': '已发布'},
        ]
        def metadata(d, version):
            return {'id': d['id'], 'name': '测试', 'version': version,
                    'format': 'LeRobort', 'addresses': ['tos://bucket/' + version + '/']}
        with patch.object(dp, 'ds_versions', return_value=versions), patch.object(dp, 'dataset_copy_metadata', side_effect=metadata):
            result = dp.dataset_batch_version_metadata(dataset)
        self.assertEqual(result['version'], 'v2')
        self.assertEqual([row['version'] for row in result['versions']], ['v2', 'v1'])
        self.assertEqual(result['versions'][0]['addresses'], ['tos://bucket/v2/'])
        self.assertEqual([row['version'] for row in result['all_versions']], ['v4', 'v3', 'v2', 'v1'])

    def test_no_published_versions_does_not_fall_back_to_draft(self):
        dataset = {'id': 'test', 'name': '测试', 'version': 'v1'}
        with patch.object(dp, 'ds_versions', return_value=[{'version': 'v1', 'publish_status': '未发布'}]), patch.object(dp, 'dataset_copy_metadata', return_value={**dataset, 'addresses': []}):
            result = dp.dataset_batch_version_metadata(dataset)
        self.assertEqual(result['versions'], [])
        self.assertEqual(result['version'], '')
        self.assertEqual(result['addresses'], [])


if __name__ == '__main__':
    unittest.main()
