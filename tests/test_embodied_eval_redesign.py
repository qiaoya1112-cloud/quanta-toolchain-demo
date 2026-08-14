import unittest

import toolchain_demo


class EmbodiedEvalRedesignTest(unittest.TestCase):
    def setUp(self):
        self.client = toolchain_demo.app.test_client()

    def test_embodied_eval_root_redirects_to_tasks(self):
        response = self.client.get('/model/embodied-eval/')
        try:
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.headers['Location'].endswith('/model/embodied-eval/tasks'))
        finally:
            response.close()

    def test_task_list_matches_training_list_chrome(self):
        response = self.client.get('/model/embodied-eval/tasks')
        try:
            body = response.get_data(as_text=True)
            self.assertNotIn('<div class="ee-page-head">', body)
            self.assertIn('<div class="fb-labeled">', body)
            self.assertIn('<div class="ff"><label>任务名称</label>', body)
            self.assertIn('<div class="list-summarybar">', body)
            self.assertIn('<div class="mini-pager">', body)
            summary_start = body.index('<div class="list-summarybar">')
            table_start = body.index('<div class="card"', summary_start)
            self.assertIn('新建评测任务', body[summary_start:table_start])
        finally:
            response.close()

    def test_mock_data_covers_realistic_list_density(self):
        self.assertGreaterEqual(len(toolchain_demo.EMBODIED_PROMPTS), 15)
        self.assertGreaterEqual(len(toolchain_demo.EMBODIED_METRIC_TEMPLATES), 4)
        self.assertGreaterEqual(len(toolchain_demo.EMBODIED_EVAL_SETS), 6)
        self.assertGreaterEqual(len(toolchain_demo.EMBODIED_EVAL_TASKS), 10)
        self.assertGreaterEqual(len(toolchain_demo.EMBODIED_SEGMENTS), 20)

    def test_all_list_pages_use_training_and_deployment_list_structure(self):
        pages = {
            '/model/embodied-eval/prompts': '新增提示词',
            '/model/embodied-eval/metrics': '新建 Metric 模板',
            '/model/embodied-eval/sets': '新建评测集',
            '/model/embodied-eval/tasks': '新建评测任务',
            '/model/embodied-eval/segments': '导出 CSV',
        }
        for path, primary_action in pages.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                try:
                    body = response.get_data(as_text=True)
                    self.assertEqual(response.status_code, 200)
                    self.assertNotIn('<div class="ee-page-head">', body)
                    self.assertIn('<div class="fb-labeled">', body)
                    self.assertIn('<div class="ff">', body)
                    self.assertNotIn('class="fb-field', body)
                    self.assertIn('<div class="list-summarybar">', body)
                    self.assertIn('<table class="ant-table">', body)
                    self.assertIn('<div class="mini-pager">', body)
                    summary_start = body.index('<div class="list-summarybar">')
                    table_start = body.index('<div class="card"', summary_start) if '<div class="card"' in body[summary_start:] else body.index('<div class="table-wrap"', summary_start)
                    self.assertIn(primary_action, body[summary_start:table_start])
                finally:
                    response.close()

    def test_create_and_detail_pages_explain_context_and_traceability(self):
        for path in (
            '/model/embodied-eval/metrics/create',
            '/model/embodied-eval/sets/create',
            '/model/embodied-eval/tasks/create',
            '/model/embodied-eval/tasks/eet001',
            '/model/embodied-eval/segments/eseg001',
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                try:
                    body = response.get_data(as_text=True)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn('<div class="ee-page-head">', body)
                finally:
                    response.close()

        segment_body = self.client.get('/model/embodied-eval/segments/eseg001').get_data(as_text=True)
        self.assertIn('robot_eseg001.parquet', segment_body)
        self.assertIn('moztrace_eseg001.json', segment_body)
        self.assertIn('Prompt 与配置', segment_body)


if __name__ == '__main__':
    unittest.main()
