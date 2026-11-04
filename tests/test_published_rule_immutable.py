import copy
import uuid
import unittest

import collection_processing as processing
import processing_rule_store as rules
import tests.test_inline_processing_rules as fixture


class PublishedRuleImmutableTests(unittest.TestCase):
    setUp = fixture.InlineRulesTests.setUp
    tearDown = fixture.InlineRulesTests.tearDown
    create = fixture.InlineRulesTests.create
    job = fixture.InlineRulesTests.job

    def test_published_rule_rejects_all_edits_and_preserves_task(self):
        rule = self.create().json['rule']
        response = self.client.post(processing.API+'/tasks', json=self.job(rule['value']),
                                    headers={'Idempotency-Key': uuid.uuid4().hex})
        self.assertEqual(201, response.status_code, response.json)
        task = response.json['task']
        body = dict(self.body, revision=rule['revision'], quality_mistakes=['新标准'], publish=False)
        for method, path in [('put', rules.API+'/'+rule['id']),
                             ('post', rules.API+'/'+rule['id']+'/revisions')]:
            result = getattr(self.client, method)(path, json=body)
            self.assertEqual(403, result.status_code, result.json)
            self.assertIn('不可编辑', result.json['error'])
        self.assertEqual(422, self.client.post('/data/rules/'+rule['id']+'/publish',
                                              json={'revision': rule['revision']}).status_code)
        current = self.client.get(rules.API+'/'+rule['id']).json['rule']
        self.assertEqual(rule['versions'], current['versions'])
        updated = self.client.get(processing.API+'/tasks/'+task['id']).json['task']
        self.assertEqual(task['configs'], updated['configs'])
        self.assertEqual(task['revision'], updated['revision'])

    def test_unpublished_rule_remains_editable_then_publish_locks_it(self):
        rule = self.create(publish=False).json['rule']
        body = dict(self.body, revision=rule['revision'], quality_mistakes=['新标准'], publish=False)
        edited = self.client.put(rules.API+'/'+rule['id'], json=body)
        self.assertEqual(200, edited.status_code, edited.json)
        self.assertFalse(edited.json['rule']['versions'])
        published = self.client.post('/data/rules/'+rule['id']+'/publish',
                                     json={'revision': edited.json['rule']['revision']})
        self.assertEqual(200, published.status_code, published.json)
        self.assertEqual('v1', published.json['rule']['version'])
        body['revision'] = published.json['rule']['revision']
        self.assertEqual(403, self.client.put(rules.API+'/'+rule['id'], json=body).status_code)

    def test_historical_pending_draft_cannot_publish(self):
        rule = self.create().json['rule']
        from processing_rule_versions import all_rules, persist
        with self.app.app_context(), rules.collection.database() as conn, conn:
            stored = next(item for item in all_rules(conn) if item['id'] == rule['id'])
            stored['draft'] = copy.deepcopy(stored['versions'][-1]['content'])
            stored['draft']['quality_mistakes'] = ['旧的待发布修改']
            persist(conn, stored)
        result = self.client.post('/data/rules/'+rule['id']+'/publish', json={'revision': rule['revision']})
        self.assertEqual(422, result.status_code, result.json)
        self.assertEqual(1, len(self.client.get(rules.API+'/'+rule['id']).json['rule']['versions']))

    def test_publishing_an_independent_rule_never_changes_existing_task(self):
        original = self.create().json['rule']
        created = self.client.post(processing.API+'/tasks', json=self.job(original['value']),
                                   headers={'Idempotency-Key': uuid.uuid4().hex})
        self.assertEqual(201, created.status_code, created.json)
        before = created.json['task']
        other = self.create('other-rule', name='复制后的质检规则', publish=False).json['rule']
        published = self.client.post('/data/rules/'+other['id']+'/publish',
                                     json={'revision': other['revision']})
        self.assertEqual(200, published.status_code, published.json)
        after = self.client.get(processing.API+'/tasks/'+before['id']).json['task']
        self.assertEqual(before['configs'], after['configs'])
        self.assertEqual(before['revision'], after['revision'])

    def test_historical_task_keeps_old_binding_when_catalog_has_later_version(self):
        from processing_rule_versions import all_rules, persist
        v1 = self.create().json['rule']
        task = self.client.post(processing.API+'/tasks', json=self.job(v1['value']),
                                headers={'Idempotency-Key': uuid.uuid4().hex}).json['task']
        with self.app.app_context(), rules.collection.database() as conn, conn:
            stored = next(item for item in all_rules(conn) if item['id'] == v1['id'])
            v2 = copy.deepcopy(stored['versions'][0])
            v2['number'] = 2
            v2['content']['quality_mistakes'] = ['历史新版标准']
            stored['versions'].append(v2)
            persist(conn, stored)
        after = self.client.get(processing.API+'/tasks/'+task['id']).json['task']
        self.assertEqual(v1['value'], after['configs']['质检']['质检']['rule'])
        preview = self.client.get(rules.API+'/preview', query_string={'task_id': task['id'],
                                  'stage': '质检', 'node': '质检'})
        self.assertEqual(200, preview.status_code, preview.json)
        self.assertEqual('v1', preview.json['rule']['version'])
        self.assertEqual(['动作未完成'], preview.json['rule']['quality_mistakes'])
        published = self.client.post(processing.API+'/tasks/'+task['id']+'/action',
                                     json={'action': 'publish', 'revision': after['revision']})
        self.assertEqual(200, published.status_code, published.json)
        self.assertEqual(v1['value'], published.json['task']['configs']['质检']['质检']['rule'])


if __name__ == '__main__':
    unittest.main()
