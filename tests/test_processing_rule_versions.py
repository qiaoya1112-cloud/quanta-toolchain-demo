"""Published revisions, stable task bindings and immutable rule identity."""
import uuid
import unittest
import tests.test_inline_processing_rules as fixture
import processing_rule_store as rules
import collection_processing as processing


class VersionTests(unittest.TestCase):
    setUp=fixture.InlineRulesTests.setUp
    tearDown=fixture.InlineRulesTests.tearDown
    create=fixture.InlineRulesTests.create
    job=fixture.InlineRulesTests.job
    def update(self, rule, **changes):
        return self.client.post(rules.API+'/'+rule['id']+'/revisions',json=dict(
            self.body,revision=rule['revision'],quality_mistakes=['动作未完成','出现碰撞'],**changes))

    def detail(self, rule):
        return self.client.get(rules.API+'/'+rule['id']).json['rule']

    def test_identity_locked_after_first_publication(self):
        for published in (True,):
            rule=self.create(str(published),name='身份'+str(published),publish=published).json['rule']
            for key,value in dict(name='换名',project='京东项目',stage='标注',rule_type='语义标注').items():
                body=dict(self.body,name=rule['name'],revision=rule['revision'],publish=False)
                body.update({key:value})
                response=self.client.post(rules.API+'/'+rule['id']+'/revisions',json=body)
                self.assertIn(response.status_code,(403,409,422))
            self.assertEqual(rule['name'],self.detail(rule)['name'])
        unpublished=self.create('unpublished',name='未发布可改',publish=False).json['rule']
        response=self.client.put(rules.API+'/'+unpublished['id'],json=dict(self.body,name='首次发布前修改',project='京东项目',revision=unpublished['revision'],publish=False))
        self.assertEqual(200,response.status_code,response.json)
        self.assertFalse(response.json['rule']['versions'])
        self.assertEqual('京东项目',response.json['rule']['project'])


    def test_preview_no_write_permission_required_but_view_permission_checked(self):
        v1=self.create().json['rule']
        params=dict(project='亮剑',stage='质检',value=v1['value'])
        self.app.config['PROCESSING_RULE_PERMISSIONS']=dict(create=False,edit=False,publish=False,view=True)
        self.assertEqual(200,self.client.get(rules.API+'/preview',query_string=params).status_code)
        self.assertEqual(200,self.client.get('/data/rules/editor-fragment',query_string=dict(project='亮剑',readonly='1')).status_code)
        self.assertEqual(403,self.client.get('/data/rules/editor-fragment',query_string=dict(project='亮剑')).status_code)
        self.assertEqual(403,self.client.get(rules.API+'/preview',query_string=dict(params,project='京东项目')).status_code)
        self.assertEqual(404,self.client.get(rules.API+'/preview',query_string=dict(params,value='rule:missing@1')).status_code)
        self.app.config['PROCESSING_RULE_PERMISSIONS']=dict(view=False)
        self.assertEqual(403,self.client.get(rules.API+'/preview',query_string=params).status_code)
        self.assertEqual(403,self.client.get('/data/rules/editor-fragment',query_string=dict(project='亮剑',readonly='1')).status_code)

    def test_preview_does_not_expose_pending_content(self):
        v1=self.create().json['rule']
        self.update(v1,publish=False)
        result=self.client.get(rules.API+'/preview',query_string=dict(project='亮剑',stage='质检',value=v1['value']))
        self.assertEqual(200,result.status_code)
        self.assertEqual(['动作未完成'],result.json['rule']['quality_mistakes'])
        self.assertNotIn('draft',result.json['rule'])


    def test_separate_edit_and_publish_permissions(self):
        v1=self.create().json['rule']
        self.app.config['PROCESSING_RULE_PERMISSIONS']=dict(create=False,edit=True,publish=False,manage=False)
        pending=self.update(v1,publish=False)
        self.assertEqual(403,pending.status_code,pending.json)
        self.assertEqual(403,self.create('blocked',name='无权创建').status_code)
        self.assertEqual(403,self.client.post('/data/rules/'+v1['id']+'/status',json=dict(status='disabled')).status_code)
        self.app.config['PROCESSING_RULE_PERMISSIONS']=dict(create=False,edit=False,publish=True,manage=True)
        self.assertEqual(403,self.update(v1,publish=False).status_code)


    def test_soft_delete_keeps_internal_events_and_name_can_be_reused(self):
        rule=self.create(publish=False).json['rule']
        self.assertEqual(200,self.client.delete('/data/rules/'+rule['id'],json=dict(revision=rule['revision'])).status_code)
        self.assertEqual(404,self.client.get(rules.API+'/'+rule['id']).status_code)
        with self.app.app_context(),rules.collection.database() as conn:
            stored=rules.stored(conn)[0]
        self.assertTrue(stored['deleted']);self.assertEqual('删除',stored['events'][-1]['action'])
        self.assertEqual(201,self.create('reuse').status_code)

    def test_permission_to_view_or_use_checked_independently(self):
        rule=self.create().json['rule']
        self.app.config['PROCESSING_RULE_PERMISSIONS']=dict(create=True,publish=True,use=False)
        self.assertEqual([],self.client.get(rules.API).json['rules'])
        result=self.client.post(processing.API+'/tasks',json=self.job(rule['value']),headers={'Idempotency-Key':uuid.uuid4().hex})
        self.assertEqual(422,result.status_code)
        self.app.config['PROCESSING_RULE_PERMISSIONS']=dict(create=True,publish=True,view=False)
        self.assertEqual(403,self.client.get(rules.API+'/'+rule['id']).status_code)
        self.assertEqual([],self.client.get(rules.API).json['published_versions'])


    def test_standalone_publish_revalidates_and_requires_revision(self):
        draft=self.create(publish=False).json['rule']
        with self.app.app_context(),rules.collection.database() as conn,conn:
            from processing_rule_versions import all_rules,persist
            record=all_rules(conn)[0];record['draft']['quality_mistakes']=[];persist(conn,record)
        response=self.client.post('/data/rules/'+draft['id']+'/publish',json=dict(revision=draft['revision']))
        self.assertEqual(422,response.status_code)
        self.assertFalse(self.detail(draft)['versions'])

    def test_unknown_legacy_names_rejected_and_revision_permissions(self):
        response=self.client.post(processing.API+'/tasks',json=self.job('不存在的规则 v1'),headers={'Idempotency-Key':uuid.uuid4().hex})
        self.assertEqual(422,response.status_code)
        v1=self.create().json['rule']
        self.app.config['PROCESSING_RULE_PERMISSIONS']={'create':True,'publish':False}
        self.assertEqual(403,self.update(v1,publish=True).status_code)
        self.assertEqual(403,self.update(v1,publish=False).status_code)
        self.app.config['PROCESSING_RULE_PERMISSIONS']={'create':False,'publish':False}
        self.assertEqual(403,self.update(v1,publish=False).status_code)
