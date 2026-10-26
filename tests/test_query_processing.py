import html
import json
import re
import unittest
from unittest.mock import patch

import data_platform as dp
import toolchain_demo
from query_processing import parse_processing_filters, processing_matches, processing_sql
from werkzeug.datastructures import MultiDict


class ProcessingArrayTests(unittest.TestCase):
    def quality(self, rule='', flow='', result='pass', scope='any', status='yes'):
        return dict(status=status, rule=rule, flow=flow, rule_match=scope, results=[result] if result else [])

    def annotation(self, rule='', flow='', version='', status='yes'):
        return dict(status=status, rule=rule, flow=flow, version=version)

    def parse(self, kind, groups, logic='and'):
        return parse_processing_filters(MultiDict({kind + '_filters': json.dumps(dict(logic=logic, groups=groups))}), kind)

    def matches(self, groups, entries, logic='and', kind='quality'):
        return processing_matches(self.parse(kind, groups, logic), kind, {kind + '_records': entries}, False)

    def setUp(self):
        self.pass_a = dict(rule='规则 A', flow='流程 A', done=True, result='pass')
        self.fail_b = dict(rule='规则 B', flow='流程 B', done=True, result='fail')

    def test_any_and_all_rules_require_actual_completed_results(self):
        entries = [self.pass_a, self.fail_b]
        self.assertTrue(self.matches([self.quality()], entries))
        self.assertFalse(self.matches([self.quality(scope='all')], entries))
        self.assertTrue(self.matches([self.quality(scope='all')], [self.pass_a, {**self.fail_b, 'result':'pass'}]))
        self.assertFalse(self.matches([self.quality(scope='all')], [self.pass_a, {**self.fail_b, 'done':False, 'result':None}]))
        self.assertFalse(self.matches([self.quality(scope='all')], []))
        self.assertFalse(self.matches([self.quality()], []))
        self.assertTrue(self.matches([self.quality(scope='all', flow='流程 A')], entries))
        self.assertFalse(processing_matches(self.parse('quality', [self.quality(scope='all')]),
                                            'quality', {'qa':'pass'}, True))

    def test_rule_flow_and_conclusion_are_correlated(self):
        self.assertFalse(self.matches([self.quality(rule='规则 B')], [self.pass_a, self.fail_b]))
        self.assertFalse(self.matches([self.quality(rule='规则 A', flow='流程 B')], [self.pass_a, self.fail_b]))
        self.assertTrue(self.matches([self.quality(rule='规则 B', result='fail')], [self.pass_a, self.fail_b]))

    def test_groups_support_and_or_and_ignore_empty_rows(self):
        groups = [self.quality(rule='规则 A'), self.quality(rule='规则 B')]
        self.assertFalse(self.matches(groups, [self.pass_a, self.fail_b]))
        self.assertTrue(self.matches(groups, [self.pass_a, self.fail_b], 'or'))
        self.assertFalse(self.matches([self.quality(rule='不存在'), self.quality(status='', result='')], [self.pass_a], 'or'))
        self.assertTrue(self.matches([], []))

    def test_not_done_is_scoped_absence_of_completed_results(self):
        self.assertTrue(self.matches([self.quality(rule='规则 B', status='no', result='')], [self.pass_a]))
        self.assertFalse(self.matches([self.quality(status='no', result='')], [self.pass_a]))
        self.assertTrue(self.matches([self.quality(status='no', result='')], []))

    def test_annotation_new_rules_and_legacy_versions(self):
        entries = [dict(platform='new', rule='标注 A', flow='标注流程 A', done=True),
                   dict(platform='legacy', version='2', done=True)]
        groups = [self.annotation(rule='标注 A'), self.annotation(version='2')]
        self.assertTrue(self.matches(groups, entries, kind='annotation'))
        self.assertFalse(self.matches(groups, entries[:1], kind='annotation'))
        self.assertTrue(self.matches(groups, entries[:1], 'or', kind='annotation'))
        self.assertFalse(self.matches([self.annotation(version='3')], entries, kind='annotation'))
        self.assertTrue(self.matches([self.annotation(version='3', status='no')], entries, kind='annotation'))

    def test_invalid_configs_fail_closed(self):
        invalid = [None, [], {}, {'logic':'xor','groups':[]}, {'logic':'and','groups':[{}]*21},
                   {'logic':'and','groups':[{'status':'unknown'}]},
                   {'logic':'and','groups':[{'rule_match':'bad'}]},
                   {'logic':'and','groups':[{'results':['unknown']}]},
                   {'logic':'and','groups':[{'status':'no','results':['pass']}]},
                   {'logic':'and','groups':[{'rule':[]}]}]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                parse_processing_filters(MultiDict({'quality_filters':json.dumps(payload)}), 'quality')
        for group in [self.annotation(version='0'), self.annotation(version='1.5'), self.annotation(rule='A', version='2')]:
            with self.assertRaises(ValueError): self.parse('annotation', [group])

    def test_single_selection_defaults_and_rejects_multiple_values(self):
        for kind in ('quality', 'annotation'):
            default = parse_processing_filters(MultiDict(), kind)
            self.assertEqual('yes', default['groups'][0]['status'])
            self.assertEqual(['*'], default['groups'][0]['rule'])
            self.assertEqual(['*'], default['groups'][0]['flow'])
            self.assertFalse(processing_matches(default, kind, {}, False))
            self.assertIn('exists(', processing_sql(default, kind))
            if kind == 'quality':
                self.assertEqual(['pass'], default['groups'][0]['results'])
            self.assertTrue(processing_matches(parse_processing_filters(
                MultiDict({'is_qc' if kind == 'quality' else 'is_annotated': ''}), kind), kind, {}, False))
            for field in ('rule', 'flow'):
                for bad in ([], [''], ['*', 'A'], ['A', 'B'], ['A', 'A'], [None], {'a':1}):
                    with self.subTest(kind=kind, field=field, bad=bad), self.assertRaises(ValueError):
                        self.parse(kind, [{field:bad}])
            restored = self.parse(kind, [{'rule':' A ', 'flow':['X']}])
            self.assertEqual(['A'], restored['groups'][0]['rule'])
            self.assertEqual(['X'], restored['groups'][0]['flow'])

    def test_single_selection_correlates_rule_flow_and_result(self):
        entries = [self.pass_a, self.fail_b]
        group = self.quality(rule=['规则 A'], flow=['流程 A'])
        self.assertTrue(self.matches([group], entries))
        self.assertTrue(self.matches([{**group, 'rule_match':'all'}], entries))
        self.assertFalse(self.matches([{**group, 'flow':['流程 B']}], entries))
        self.assertFalse(self.matches([{**group, 'rule':['规则 B']}], entries))
        sql = processing_sql(self.parse('quality', [{**group, 'rule_match':'all'}]), 'quality')
        self.assertIn("p.rule = '规则 A'", sql)
        self.assertIn("p.flow = '流程 A'", sql)
        self.assertIn('forall(', sql)
        quoted = processing_sql(self.parse('quality', [self.quality(rule=["a'b"])]), 'quality')
        self.assertIn("p.rule = 'a''b'", quoted)

    def test_any_selection_keeps_legacy_records_compatible(self):
        quality = self.quality(rule=['*'], flow=['*'])
        self.assertTrue(processing_matches(self.parse('quality', [quality]), 'quality', {'qa':'pass'}, True))
        legacy = [{'platform':'legacy', 'version':'2', 'done':True}]
        annotation = self.annotation(rule=['*'], flow=['*'], version='2')
        self.assertTrue(self.matches([annotation], legacy, kind='annotation'))
        self.assertTrue(self.matches([self.annotation(rule=['*'], flow=['*'])], legacy, kind='annotation'))
        self.assertFalse(self.matches([self.annotation(rule=['规则 A'])], legacy, kind='annotation'))
        new = [{'platform':'new', 'rule':'规则 B', 'flow':'流程 B', 'done':True}]
        self.assertTrue(self.matches([self.annotation(rule=['规则 B'], flow=['流程 B'])], new, kind='annotation'))
        self.assertFalse(self.matches([self.annotation(rule=['规则 A'], flow=['流程 B'])], new, kind='annotation'))
        default_sql = processing_sql(self.parse('annotation', [self.annotation(rule=['*'], flow=['*'])]), 'annotation')
        self.assertNotIn("p.platform = 'new'", default_sql)
        self.assertNotIn("p.rule = '*'", default_sql)
        with self.assertRaises(ValueError):
            self.parse('annotation', [self.annotation(rule=['规则 A'], version='2')])

    def test_route_restores_single_choices_and_matches_within_one_record(self):
        client = toolchain_demo.app.test_client()
        base = dp.RECORDINGS[0]
        quality = self.parse('quality', [self.quality(rule=['规则 A'], flow=['流程 A'])])
        annotation = self.parse('annotation', [self.annotation(rule=['标注 B'], flow=['标注流程 B'])])
        new = dict(platform='new', rule='标注 B', flow='标注流程 B', done=True)
        records = [{**base, 'id':800001, 'quality_records':[self.pass_a], 'annotation_records':[new]},
                   {**base, 'id':800002, 'quality_records':[self.fail_b], 'annotation_records':[new]}]
        with patch.object(dp, 'RECORDINGS', records):
            response = client.get('/model/data/query', query_string={'quality_filters':json.dumps(quality), 'annotation_filters':json.dumps(annotation)})
            self.assertEqual(200, response.status_code)
            text = response.get_data(as_text=True)
            self.assertEqual(['800001'], re.findall(r'<tr data-pg="\d+" data-recording-id="(\d+)"', text))
            restored = json.loads(re.search(r'id="qAdvancedConfig">(.*?)</script>', text, re.S)[1])
            self.assertEqual(quality, restored['processing']['quality'])
            self.assertEqual(annotation, restored['processing']['annotation'])

    def test_sql_matches_quantifiers_and_keeps_values_literal(self):
        config = self.parse('quality', [self.quality(scope='all', flow="a'b"), self.quality(rule='B')], 'or')
        sql = processing_sql(config, 'quality')
        self.assertIn('forall(', sql)
        self.assertIn('size(', sql)
        self.assertIn(' OR exists(', sql)
        self.assertIn("p.flow = 'a''b'", sql)
        self.assertIn("COALESCE(p.result IN ('pass'), FALSE)", sql)
        self.assertIn("p.platform = 'legacy'", processing_sql(self.parse('annotation', [self.annotation(version='2')]), 'annotation'))

    def test_route_arrays_restore_and_apply_before_exclusion_limit(self):
        base = dp.RECORDINGS[0]
        records = [{**base, 'id':800001, 'quality_records':[self.pass_a, self.fail_b]},
                   {**base, 'id':800002, 'quality_records':[self.pass_a, {**self.fail_b,'result':'pass'}]},
                   {**base, 'id':800003, 'quality_records':[]}]
        client = toolchain_demo.app.test_client()
        def page(config, **params):
            response = client.get('/model/data/query', query_string={'quality_filters':json.dumps(config), 'is_annotated':'', **params})
            self.assertEqual(200, response.status_code)
            text = response.get_data(as_text=True)
            return text, re.findall(r'<tr data-pg="\d+" data-recording-id="(\d+)"', text)
        with patch.object(dp, 'RECORDINGS', records):
            any_config = self.parse('quality', [self.quality()])
            self.assertEqual(['800002','800001'], page(any_config)[1])
            all_config = self.parse('quality', [self.quality(scope='all')])
            text, ids = page(all_config)
            self.assertEqual(['800002'], ids)
            restored = json.loads(re.search(r'id="qAdvancedConfig">(.*?)</script>', text, re.S)[1])
            self.assertEqual(all_config, restored['processing']['quality'])
            self.assertEqual([], page(all_config, excluded_ids='800002', limit='1')[1])
            self.assertIn('forall(', html.unescape(text))
            self.assertEqual([], page({'logic':'bad','groups':[]})[1])

    def test_demo_data_distinguishes_any_all_and_legacy_annotation(self):
        any_config = self.parse('quality', [self.quality()])
        all_config = self.parse('quality', [self.quality(scope='all')])
        any_ids = {row['id'] for row in dp.RECORDINGS if processing_matches(any_config, 'quality', row, dp.rec_qc(row))}
        all_ids = {row['id'] for row in dp.RECORDINGS if processing_matches(all_config, 'quality', row, dp.rec_qc(row))}
        self.assertTrue(all_ids)
        self.assertLess(all_ids, any_ids)
        self.assertIn(120502, any_ids - all_ids)
        self.assertIn(121014, any_ids - all_ids)
        legacy_config = self.parse('annotation', [self.annotation(version='2')])
        legacy_ids = {row['id'] for row in dp.RECORDINGS if processing_matches(legacy_config, 'annotation', row, dp.rec_anno(row))}
        self.assertIn(121005, legacy_ids)
        self.assertNotIn(120489, legacy_ids)


if __name__ == '__main__':
    unittest.main()
