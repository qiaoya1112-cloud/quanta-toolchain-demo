import json
import re
import unittest

import toolchain_demo
from eval_catalog import seed_data, ENTITIES


class EvalCatalogTests(unittest.TestCase):
    def setUp(self):
        self.client = toolchain_demo.app.test_client()

    def test_navigation_and_pages(self):
        js_response = self.client.get('/static/eval_catalog/catalog.js')
        catalog_js = js_response.get_data(as_text=True)
        js_response.close()
        self.assertIn('发布状态', catalog_js)
        self.assertIn('启用状态', catalog_js)
        self.assertNotIn("status:'停用'", catalog_js)
        self.assertNotIn("field_'+(i+2)", catalog_js)
        for kind in ENTITIES:
            with self.subTest(kind=kind):
                response = self.client.get('/model/eval/' + kind, follow_redirects=True)
                self.assertEqual(response.status_code, 200)
                body = response.get_data(as_text=True)
                page_title = '评测用例' if kind == 'test-cases' else '场景库'
                self.assertIn(f'<h1>{page_title}</h1>', body)
                self.assertIn(f'<title>{page_title} - Quanta</title>', body)
                self.assertIn('场景库', body)
                self.assertIn('id="ec-create"', body)
                self.assertIn('id="ec-form"', body)
                match = re.search(r'<script id="ec-seed" type="application/json">(.*?)</script>', body, re.S)
                self.assertEqual(json.loads(match.group(1)), seed_data())
                self.assertIn('/model/eval/catalog', body)
                if kind != 'test-cases':
                    self.assertIn('/model/eval/catalog?section=scenario', body)
                    self.assertIn('/model/eval/catalog?section=elements&amp;tab=' + kind, body)
                    for other in ('stages','stories','skills','factors'):
                        self.assertIn('/model/eval/catalog?section=elements&amp;tab=' + other, body)
                self.assertIn('class="ant-table"', body)
                self.assertIn('class="ant-drawer-mask"', body)
                self.assertIn('发布状态', body)
                self.assertNotIn('class="ec-dialog"', body)
                self.assertNotIn('/static/eval_catalog/catalog.css', body)
                self.assertEqual(body.count('class="stat-card"'), 0 if kind == 'test-cases' else 4)
                if kind != 'test-cases':
                    self.assertIn('class="tm-tabs" id="ec-top-tabs"', body)
                    self.assertIn('class="tm-subtabs" id="ec-tabs"', body)
                    self.assertLess(body.index('id="ec-top-tabs"'), body.index('id="ec-tabs"'))

    def test_scenario_library_top_tab(self):
        for query in ('', '?section=scenario', '?section=scenario&tab=skills'):
            with self.subTest(query=query):
                response = self.client.get('/model/eval/catalog' + query)
                self.assertEqual(response.status_code, 200)
                body = response.get_data(as_text=True)
                self.assertIn('data-section="scenario"', body)
                self.assertIn('data-kind="stories"', body)
                self.assertRegex(body, r'class="tm-tab active"[^>]*aria-selected="true">场景库定义</a>')
                self.assertNotIn('id="ec-tabs"', body)
                self.assertIn('id="ec-filter"', body)
                self.assertIn('id="ec-tbody"', body)
                self.assertIn('id="ec-create">批量新增场景</button>', body)
                self.assertNotIn('id="ec-aggregate"', body)
                self.assertNotIn('id="ec-scenario-stats"', body)
                self.assertLess(body.index('id="ec-filter"'), body.index('id="ec-table"'))
                self.assertNotIn('演示数据仅保存在当前浏览器', body)
                self.assertNotIn('id="ec-storage"', body)
                for kind in ('stages', 'stories', 'skills', 'factors'):
                    self.assertIn(f'data-filter-kind="{kind}"', body)
                self.assertNotIn('id="ec-search"', body)
                self.assertNotIn('id="ec-status"', body)

    def test_element_tabs_retain_matching_tables(self):
        for kind in ('stages', 'stories', 'skills', 'factors'):
            with self.subTest(kind=kind):
                response = self.client.get('/model/eval/catalog?section=elements&tab=' + kind)
                self.assertEqual(response.status_code, 200)
                body = response.get_data(as_text=True)
                self.assertIn(f'data-kind="{kind}" data-section="elements"', body)
                self.assertLess(body.index('id="ec-top-tabs"'), body.index('id="ec-element-stats"'))
                self.assertLess(body.index('id="ec-element-stats"'), body.index('id="ec-tabs"'))
                for target in ('stages', 'stories', 'skills', 'factors'):
                    self.assertIn(f'id="ec-total-{target}">{len(seed_data()[target])}</div>', body)
                self.assertRegex(body, r'class="tm-tab active"[^>]*aria-selected="true">要素定义</a>')
                self.assertRegex(body, rf'class="tm-subtab active"[^>]*tab={kind}"[^>]*aria-selected="true"')
                self.assertIn('id="ec-tbody"', body)
                self.assertIn('id="ec-create"', body)
                self.assertIn('id="ec-search"', body)
                self.assertIn('id="ec-status"', body)
                self.assertIn('id="ec-enabled"', body)
                self.assertNotIn('演示数据仅保存在当前浏览器', body)
                self.assertNotIn('id="ec-storage"', body)
                self.assertNotIn('id="ec-stage-filter"', body)

    def test_assets_served_and_existing_evaluation_pages_intact(self):
        for path in ['/static/eval_catalog/catalog.js',
                     '/model/eval/tasks', '/model/eval/benchmarks', '/model/eval/criteria']:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                response.close()

    def test_element_tags_share_tag_management_options(self):
        from quanta_eval_platform import tag_management_dimensions
        expected = {}
        def walk(nodes, path):
            for node in nodes:
                names = path + [node['name']]
                expected[node['id']] = ' / '.join(names)
                walk(node.get('sub_tags', []), names)
        for dimension in tag_management_dimensions():
            walk(dimension['tags'], [dimension['name']])
        response = self.client.get('/model/eval/catalog?section=elements&tab=skills')
        body = response.get_data(as_text=True)
        options = json.loads(re.search(r'<script id="ec-tag-options" type="application/json">(.*?)</script>', body, re.S).group(1))
        self.assertEqual({option['id']: option['name'] for option in options}, expected)
        tree = json.loads(re.search(r'<script id="ec-tag-tree" type="application/json">(.*?)</script>', body, re.S).group(1))
        self.assertEqual(tree, tag_management_dimensions())
        self.assertIn('q_success', expected)
        self.assertEqual(self.client.get('/model/eval/tags').status_code, 200)

    def test_source_ids_and_dependency_chain_preserved(self):
        cases = {row['id']: row for row in seed_data()['test-cases']}
        self.assertEqual(cases['Study_49']['prerequisite_ids'], ['Study_48'])
        self.assertEqual(cases['Study_48']['prerequisite_ids'], ['Study_47'])
        self.assertEqual(cases['Kit_23']['prerequisite_ids'], ['Kit_22'])
        self.assertEqual(cases['BM_05']['factors'], [{'factor_id': 'FC_SIZE', 'value': '适中'}])

    def test_publish_and_enabled_metadata_on_every_entity(self):
        data = seed_data()
        for kind, rows in data.items():
            with self.subTest(kind=kind):
                self.assertTrue(rows)
                for row in rows:
                    self.assertIn(row['publish_status'], {'已发布', '未发布'})
                    self.assertIsInstance(row['enabled'], bool)

    def test_create_benchmark_retains_selected_case_snapshots(self):
        cases = seed_data()['test-cases'][:2]
        cases[0]['distribution_type'] = 'OOD'
        cases[0]['factors'] = [{'factor_id': 'FC_SIZE', 'values': ['小', '适中']}]
        original = list(toolchain_demo.ep.BENCHMARKS)
        try:
            response = self.client.post('/model/eval/benchmarks/create', data={
                'name': '批量用例评测集', 'test_cases': json.dumps(cases),
            })
            self.assertEqual(response.status_code, 302)
            benchmark = toolchain_demo.ep.BENCHMARKS[-1]
            self.assertEqual(benchmark['test_case_ids'], [row['id'] for row in cases])
            self.assertEqual(benchmark['test_cases'], [{**row, 'distribution_type': row.get('distribution_type', 'ID')} for row in cases])
            self.assertEqual(benchmark['publish_status'], '未发布')
            page = self.client.get('/model/eval/benchmarks').get_data(as_text=True)
            self.assertIn('bm-test-case-section', page)
            self.assertIn('test_cases', page)
            for invalid in ['{}', 'invalid', json.dumps([cases[0], cases[0]]), json.dumps([{**cases[0], 'distribution_type': 'invalid'}])]:
                response = self.client.post('/model/eval/benchmarks/create', data={
                    'name': '无效评测集', 'test_cases': invalid,
                })
                self.assertEqual(response.status_code, 400)
            self.assertEqual(len(toolchain_demo.ep.BENCHMARKS), len(original) + 1)
        finally:
            toolchain_demo.ep.BENCHMARKS[:] = original


class BenchmarkBatchAddTests(unittest.TestCase):
    def setUp(self):
        import copy
        self.client = toolchain_demo.app.test_client()
        self.original = copy.deepcopy(toolchain_demo.ep.BENCHMARKS)
        self.case = {**seed_data()['test-cases'][0], 'distribution_type': 'OOD'}
        toolchain_demo.ep.BENCHMARKS[:] = [
            {'id': 'draft', 'name': '未发布评测集', 'publish_status': '未发布',
             'description': '保留说明', 'tags': ['tag1'], 'prompt_ids': ['p1'],
             'test_cases': [self.case], 'test_case_ids': [self.case['id']]},
            {'id': 'published', 'name': '已发布评测集', 'publish_status': '已发布'},
        ]

    def tearDown(self):
        toolchain_demo.ep.BENCHMARKS[:] = self.original

    def test_append_deduplicates_without_overwriting_existing_configuration(self):
        incoming = seed_data()['test-cases'][1]
        response = self.client.post('/model/eval/benchmarks/draft/cases', json={
            'test_cases': [{**self.case, 'distribution_type': 'ID', 'prompt': '不应覆盖'}, incoming, incoming],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'added': 1, 'skipped': 2})
        draft = toolchain_demo.ep.BENCHMARKS[0]
        self.assertEqual(draft['test_cases'][0], self.case)
        self.assertEqual(draft['test_cases'][1]['distribution_type'], 'ID')
        self.assertEqual(draft['test_case_ids'], [self.case['id'], incoming['id']])
        self.assertEqual((draft['description'], draft['tags'], draft['prompt_ids']), ('保留说明', ['tag1'], ['p1']))
        retry = self.client.post('/model/eval/benchmarks/draft/cases', json={'test_cases': [incoming]})
        self.assertEqual(retry.json, {'added': 0, 'skipped': 1})

    def test_options_and_submit_recheck_status_and_reject_invalid_cases(self):
        import copy
        response = self.client.get('/model/eval/benchmarks/drafts')
        self.assertEqual([row['id'] for row in response.json['benchmarks']], ['draft'])
        before = copy.deepcopy(toolchain_demo.ep.BENCHMARKS)
        for cases in [[], [None], [{**self.case, 'publish_status': '未发布'}],
                      [{**self.case, 'distribution_type': 'invalid'}], [{**self.case, 'prompt': ''}]]:
            self.assertEqual(self.client.post('/model/eval/benchmarks/draft/cases', json={'test_cases': cases}).status_code, 400)
        self.assertEqual(toolchain_demo.ep.BENCHMARKS, before)
        self.assertEqual(self.client.post('/model/eval/benchmarks/missing/cases', json={'test_cases': [self.case]}).status_code, 404)
        toolchain_demo.ep.BENCHMARKS[0]['publish_status'] = '已发布'
        self.assertEqual(self.client.post('/model/eval/benchmarks/draft/cases', json={'test_cases': [self.case]}).status_code, 409)
        self.assertEqual(self.client.get('/model/eval/benchmarks/drafts').json['benchmarks'], [])


if __name__ == '__main__':
    unittest.main()
