import html
import json
import re
import unittest
from unittest.mock import patch

from query_conditions import matches, parse_tree, tree_sql
import data_platform as dp
import toolchain_demo


class ConditionTests(unittest.TestCase):
    fields = {"frames": {"type": "number"}, "task": {"type": "text"}, "tags": {"type": "tags"},
              "date": {"type": "date"}, "qc": {"type": "boolean"}}

    def parse(self, tree):
        return parse_tree(json.dumps(tree), self.fields)

    def test_nested_precedence(self):
        tree = self.parse({"logic": "and", "children": [
            {"field": "frames", "op": "gte", "value": "1000"},
            {"logic": "or", "children": [{"field": "task", "op": "eq", "value": "t1"},
                                            {"field": "task", "op": "eq", "value": "t2"}]},
        ]})
        self.assertTrue(matches(tree, {"frames": 1200, "task": "t2"}, self.fields))
        self.assertFalse(matches(tree, {"frames": 800, "task": "t2"}, self.fields))
        self.assertFalse(matches(tree, {"frames": 1200, "task": "t3"}, self.fields))
        self.assertEqual("(frames >= 1000.0 AND (task = 't1' OR task = 't2'))", tree_sql(tree, self.fields))

    def test_types_sets_and_literal_sql(self):
        tree = self.parse({"logic": "and", "children": [
            {"field": "frames", "op": "in", "value": "1000，1200"},
            {"field": "tags", "op": "in", "value": ["sk_pick", "sk_wipe"]},
            {"field": "qc", "op": "eq", "value": "false"},
            {"field": "date", "op": "gte", "value": "2026-05-20"},
        ]})
        self.assertTrue(matches(tree, {"frames": 1200, "tags": ["sk_wipe"], "qc": False, "date": "2026-05-21"}, self.fields))
        quoted = self.parse({"logic":"and", "children":[{"field":"task", "op":"contains", "value":"a'b%_"}]})
        self.assertIn("'a''b%_'", tree_sql(quoted, self.fields))
        self.assertFalse(matches(quoted, {"task":"aZZb"}, self.fields))

    def test_invalid_conditions_cannot_silently_expand_query(self):
        for raw in ['{', 'null', '[]', json.dumps({"logic":"or","children":[{"logic":"and","children":[]}]}),
                    json.dumps({"logic":"and","children":[{"field":"unknown", "op":"eq", "value":"1"}]}),
                    json.dumps({"logic":"and","children":[{"field":"frames", "op":"eq", "value":"NaN"}]}),
                    json.dumps({"logic":"and","children":[{"field":"date", "op":"eq", "value":"2026-02-30"}]}),
                    json.dumps({"logic":"and","children":[{"field":"frames", "op":"in", "value":"1000,"}]})]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_tree(raw,self.fields)
        group = {"field":"task", "op":"eq", "value":"t1"}
        for _ in range(8): group={"logic":"and","children":[group]}
        with self.assertRaises(ValueError): self.parse(group)


class QueryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = toolchain_demo.app.test_client()

    def page(self, **params):
        response = self.client.get('/model/data/query', query_string=params)
        self.assertEqual(200,response.status_code)
        return response.get_data(as_text=True)

    def ids(self, text):
        return re.findall(r'<tr data-pg="\d+" data-recording-id="(\d+)"',text)

    def test_basic_nested_exclusion_limit_and_count_stay_consistent(self):
        include = {"logic":"and","children":[{"field":"frames","op":"gte","value":"1000"},
            {"logic":"or","children":[{"field":"task","op":"eq","value":"t1"},{"field":"task","op":"eq","value":"t2"}]}]}
        exclude = {"logic":"or","children":[{"field":"recording_id","op":"eq","value":"120502"}]}
        text=self.page(conditions=json.dumps(include),exclusions=json.dumps(exclude),excluded_ids='121014',limit='2')
        self.assertEqual(['121005','120532'],self.ids(text))
        self.assertIn('筛选命中 5 条 · 已剔除 2 条 · 保留 2 条',text)
        self.assertNotIn('id="qBuildSelectionSummary"',text)
        self.assertIn('recording_id NOT IN (121014)',text)
        self.assertIn('LIMIT 2',text)
        self.assertEqual(['120532','120489'],self.ids(self.page(task='t1',conditions=json.dumps(include),exclusions=json.dumps(exclude))))

    def test_restore_keeps_filter_and_ids_remain_unique(self):
        removed=self.page(task='t1',excluded_ids='120489,120489,#120502')
        self.assertNotIn('120489',self.ids(removed))
        restored=self.page(task='t1',excluded_ids='120502')
        self.assertIn('120489',self.ids(restored))
        self.assertEqual(4,len(self.ids(restored)))
        self.assertEqual(10,len(self.ids(self.page())))

    def test_collection_conclusion_filters_independently_of_quality(self):
        records=[{**dp.RECORDINGS[0], 'id':800001, 'collect_result':'成功', 'qa':'fail'},
                 {**dp.RECORDINGS[0], 'id':800002, 'collect_result':'失败', 'qa':'pass'}]
        with patch.object(dp,'RECORDINGS',records):
            self.assertEqual(['800001'],self.ids(self.page(collect_result='成功')))
            text=self.page(collect_result='失败',qa='pass')
            self.assertEqual(['800002'],self.ids(text))
            sql=html.unescape(re.search(r'id="qSqlEditor"[^>]*>(.*?)</textarea>',text,re.S)[1])
            self.assertIn("collect_result = '失败'",sql)
            self.assertIn('<option value="失败" selected>失败</option>',text)
            self.assertEqual(2,len(self.ids(self.page())))
        processing=re.search(r'id="qProcessingFilters">(.*?)</details>',text,re.S)[1]
        self.assertLess(processing.index('采集结论'),processing.index('是否质检'))

    def test_processing_task_ids_match_any_and_combine_with_collection_task(self):
        records=[{**dp.RECORDINGS[0], 'id':800001, 'task':'t1', 'processing_task_ids':['20454','20453']},
                 {**dp.RECORDINGS[0], 'id':800002, 'task':'t2', 'processing_task_ids':['20453']},
                 {**dp.RECORDINGS[0], 'id':800003, 'task':'t1', 'processing_task_ids':[]}]
        with patch.object(dp,'RECORDINGS',records):
            self.assertEqual(['800001'],self.ids(self.page(processing_task='20454')))
            self.assertEqual({'800001','800002'},set(self.ids(self.page(processing_task='20454，20453'))))
            text=self.page(task='t1',processing_task='20453')
            self.assertEqual(['800001'],self.ids(text))
            self.assertEqual([],self.ids(self.page(processing_task='missing')))
            self.assertEqual(3,len(self.ids(self.page())))
        sql=html.unescape(re.search(r'id="qSqlEditor"[^>]*>(.*?)</textarea>',text,re.S)[1])
        self.assertIn("array_contains(processing_task_ids, '20453')",sql)
        panel=re.search(r'id="qTaskFilters">(.*?)</details>',text,re.S)[1]
        self.assertTrue('采集任务 ID</label>' in panel and '处理任务 ID</label>' in panel)
        self.assertFalse('任务标签' in panel)
        self.assertTrue('name="processing_task" value="20453"' in panel)

    def test_empty_legacy_exclusion_group_defaults_to_or(self):
        for params in ({}, {'exclusions':json.dumps({'logic':'and','children':[]})}):
            text=self.page(**params)
            config=json.loads(re.search(r'id="qAdvancedConfig">(.*?)</script>',text,re.S).group(1))
            self.assertEqual(config['exclusions']['logic'],'or')
            self.assertEqual(config['conditions']['logic'],'and')
        explicit={'logic':'and','children':[{'field':'recording_id','op':'eq','value':'121005'}]}
        text=self.page(exclusions=json.dumps(explicit))
        config=json.loads(re.search(r'id="qAdvancedConfig">(.*?)</script>',text,re.S).group(1))
        self.assertEqual(config['exclusions']['logic'],'and')

    def test_visual_prompt_filter_combines_with_other_filters_and_preserves_selection(self):
        records=[{**dp.RECORDINGS[0], 'id':800001, 'has_visual_prompt':True, 'collect_result':'成功'},
                 {**dp.RECORDINGS[0], 'id':800002, 'has_visual_prompt':False, 'collect_result':'成功'},
                 {**dp.RECORDINGS[0], 'id':800003, 'has_visual_prompt':True, 'collect_result':'失败'}]
        with patch.object(dp,'RECORDINGS',records):
            self.assertEqual({'800001','800003'},set(self.ids(self.page(has_visual_prompt='yes'))))
            text=self.page(has_visual_prompt='no')
            self.assertEqual(['800002'],self.ids(text))
            sql=html.unescape(re.search(r'id="qSqlEditor"[^>]*>(.*?)</textarea>',text,re.S)[1])
            self.assertIn('has_visual_prompt = FALSE',sql)
            self.assertTrue('<option value="no" selected>否</option>' in text)
            self.assertEqual(['800001'],self.ids(self.page(has_visual_prompt='yes',collect_result='成功')))
            self.assertEqual(3,len(self.ids(self.page())))
            self.assertEqual([],self.ids(self.page(has_visual_prompt='invalid')))
        panel=re.search(r'id="qProcessingFilters">(.*?)</details>',text,re.S)[1]
        self.assertLess(panel.index('标注版本'),panel.index('是否包含 visual prompt'))

    def test_total_duration_cap_applies_after_exclusion_and_with_count_cap(self):
        text=self.page(duration_limit='0.03')
        self.assertEqual(['121131','121120'],self.ids(text))
        self.assertIn('cumulative_duration_s &lt;= 108',text)
        self.assertEqual(['121131'],self.ids(self.page(duration_limit='0.03',limit='1')))
        self.assertEqual(['121120','121023'],self.ids(self.page(duration_limit='0.03',excluded_ids='121131')))
        self.assertEqual([],self.ids(self.page(duration_limit='0.01')))
        self.assertIn('value="1.50"',self.page(duration_limit='1.5'))
        self.assertIn('value="1.23"',self.page(duration_limit='1.234'))

    def test_invalid_or_all_excluded_returns_no_rows_and_disables_build(self):
        for params in [{'conditions':'bad'}, {'excluded_ids':'bad'}, {'limit':'-1'},
                       {'duration_limit':'bad'}, {'duration_limit':'NaN'}, {'duration_limit':'inf'}, {'duration_limit':'-1'},
                       {'excluded_ids':','.join(str(r['id']) for r in dp.RECORDINGS)}]:
            with self.subTest(params=params):
                text=self.page(**params)
                self.assertEqual([],self.ids(text))
                self.assertRegex(text,r'id="qBuildDataset"[^>]*disabled')

    def test_pagination_is_based_on_final_unique_records(self):
        records=[{**dp.RECORDINGS[0], 'id':800000+i} for i in range(45)]
        with patch.object(dp,'RECORDINGS',records):
            text=self.page(excluded_ids=','.join(str(800000+i) for i in range(5)))
        self.assertEqual(40,len(self.ids(text)))
        self.assertIn('共 40 条',text)
        self.assertNotIn('data-p="2"',text)

    def test_condition_values_are_safe_in_markup_and_sql(self):
        value="</script><img src=x onerror=alert(1)>"
        tree={"logic":"and","children":[{"field":"task","op":"eq","value":value}]}
        text=self.page(conditions=json.dumps(tree))
        self.assertNotIn(value,text)
        self.assertIn('\\u003c/script',text)

    def test_operator_copy_uses_condition_operators_not_pipeline_operators(self):
        text=self.page()
        config=json.loads(re.search(r'id="qAdvancedConfig">(.*?)</script>',text,re.S).group(1))
        self.assertEqual('大于等于',config['operators']['gte'])
        self.assertEqual('等于',config['operators']['eq'])


if __name__ == '__main__':
    unittest.main()
