"""Published revisions, stable task bindings and immutable rule identity."""
import copy
import uuid
import unittest
from concurrent.futures import ThreadPoolExecutor
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
                self.assertIn(response.status_code,(409,422))
            self.assertEqual(rule['name'],self.detail(rule)['name'])
        unpublished=self.create('unpublished',name='未发布可改',publish=False).json['rule']
        response=self.client.put(rules.API+'/'+unpublished['id'],json=dict(self.body,name='首次发布前修改',project='京东项目',revision=unpublished['revision'],publish=False))
        self.assertEqual(200,response.status_code,response.json)
        self.assertFalse(response.json['rule']['versions'])
        self.assertEqual('京东项目',response.json['rule']['project'])

    def test_preview_exact_publication_and_pinned_task_snapshot(self):
        v1=self.create().json['rule']
        job=self.client.post(processing.API+'/tasks',json=self.job(v1['value']),
            headers={'Idempotency-Key':uuid.uuid4().hex}).json['task']
        v2=self.update(v1,publish=True).json['rule']
        path=rules.API+'/preview'
        current=self.client.get(path,query_string=dict(project='亮剑',stage='质检',value=v2['value']))
        self.assertEqual(200,current.status_code,current.json)
        self.assertEqual('v2',current.json['rule']['version'])
        self.assertEqual(['动作未完成','出现碰撞'],current.json['rule']['quality_mistakes'])
        # Client-supplied value cannot switch the task preview to another version.
        bound=self.client.get(path,query_string=dict(task_id=job['id'],stage='质检',node='质检',value=v2['value']))
        self.assertEqual(200,bound.status_code,bound.json)
        self.assertEqual('v1',bound.json['rule']['version'])
        self.assertEqual(['动作未完成'],bound.json['rule']['quality_mistakes'])
        self.assertNotIn('draft',bound.json['rule'])
        self.assertNotIn('versions',bound.json['rule'])
        self.client.post('/data/rules/'+v1['id']+'/status',json=dict(status='disabled'))
        self.assertEqual(200,self.client.get(path,query_string=dict(task_id=job['id'],stage='质检',node='质检')).status_code)
        self.assertEqual(404,self.client.get(path,query_string=dict(task_id=job['id'],stage='质检',node='不存在')).status_code)

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

    def test_draft_publish_history_and_noop(self):
        v1=self.create().json['rule']
        draft=self.update(v1,publish=False).json['rule']
        self.assertEqual('v1',draft['version']);self.assertTrue(draft['has_draft'])
        self.assertEqual(1,len(draft['quality_mistakes']))
        self.assertEqual(2,len(draft['draft']['quality_mistakes']))
        self.assertEqual(409,self.update(v1,publish=True).status_code)
        v2=self.update(draft,publish=True).json['rule']
        self.assertEqual('v2',v2['version']);self.assertFalse(v2['has_draft'])
        self.assertEqual(v1['versions'][0],v2['versions'][0])
        self.assertEqual(422,self.update(v2,publish=True).status_code)
        self.assertEqual(2,len(self.detail(v2)['versions']))
        self.assertEqual(v1['created'],v2['created']);self.assertEqual(v1['owner'],v2['owner'])

    def test_task_snapshot_remains_v1_after_v2(self):
        v1=self.create().json['rule']
        result=self.client.post(processing.API+'/tasks',json=self.job(v1['value']),headers={'Idempotency-Key':uuid.uuid4().hex})
        self.assertEqual(201,result.status_code,result.json)
        task=result.json['task']
        published=self.client.post(processing.API+'/tasks/'+task['id']+'/action',json=dict(action='publish',revision=task['revision']))
        self.assertEqual(200,published.status_code,published.json)
        v2=self.update(v1,publish=True).json['rule']
        config=published.json['task']['configs']['质检']['质检']
        self.assertEqual(v1['value'],config['rule'])
        self.assertEqual(['动作未完成'],config['rule_identity']['content']['quality_mistakes'])
        available=self.client.get(rules.API+'?project=亮剑').json
        self.assertEqual([v2['value']],[r['value'] for r in available['rules']])
        self.assertEqual(2,len(available['published_versions']))

    def test_new_or_unpublished_task_cannot_use_superseded_version(self):
        v1=self.create().json['rule']
        result=self.client.post(processing.API+'/tasks',json=self.job(v1['value']),headers={'Idempotency-Key':uuid.uuid4().hex})
        task=result.json['task'];self.update(v1,publish=True)
        response=self.client.post(processing.API+'/tasks',json=self.job(v1['value']),headers={'Idempotency-Key':uuid.uuid4().hex})
        self.assertEqual(422,response.status_code,response.json)
        response=self.client.post(processing.API+'/tasks/'+task['id']+'/action',json=dict(action='publish',revision=task['revision']))
        self.assertEqual(422,response.status_code,response.json)

    def test_saved_revision_and_list_publication_are_separate_and_noop_is_clean(self):
        rule=self.create(publish=False).json['rule']
        self.assertEqual('',rule['version']);self.assertEqual('disabled',rule['status'])
        v1=self.client.post('/data/rules/'+rule['id']+'/publish',json=dict(revision=rule['revision'])).json['rule']
        noop=self.client.post(rules.API+'/'+rule['id']+'/revisions',json=dict(self.body,publish=False,revision=v1['revision']))
        self.assertTrue(noop.json['unchanged']);self.assertFalse(noop.json['rule']['has_draft'])
        draft=self.update(v1,publish=False).json['rule']
        self.assertEqual('v1',self.detail(draft)['version']);self.assertTrue(self.detail(draft)['has_draft'])
        self.assertTrue(draft['pending_saved_at'])
        v2=self.client.post('/data/rules/'+rule['id']+'/publish',json=dict(revision=draft['revision'])).json['rule']
        self.assertEqual('v2',v2['version']);self.assertEqual('enabled',v2['status'])
        self.assertEqual(409,self.client.post('/data/rules/'+rule['id']+'/publish',json=dict(revision=draft['revision'])).status_code)
        self.assertEqual(422,self.client.post('/data/rules/'+rule['id']+'/publish',json=dict(revision=v2['revision'])).status_code)

    def test_link_change_requires_publish_and_stores_only_links(self):
        body=dict(self.body,stage='标注',rule_type='语义标注',semantic_mode='link',document_link='https://example.feishu.cn/docx/A')
        v1=self.client.post(rules.API,json=body,headers={'Idempotency-Key':'links'}).json['rule']
        pending=self.client.post(rules.API+'/'+v1['id']+'/revisions',json=dict(body,revision=v1['revision'],publish=False,document_link='https://example.feishu.cn/docx/B')).json['rule']
        self.assertEqual('v1',pending['version']);self.assertTrue(pending['rule_config'].endswith('/A'))
        v2=self.client.post('/data/rules/'+v1['id']+'/publish',json=dict(revision=pending['revision'])).json['rule']
        self.assertEqual('v2',v2['version']);self.assertTrue(v2['rule_config'].endswith('/B'))
        self.assertTrue(v2['versions'][0]['content']['rule_config'].endswith('/A'))
        self.assertNotIn('document_body',v2['versions'][0]['content'])

    def test_fixed_flow_may_pin_old_version_but_client_cannot_claim_exception(self):
        v1=self.create().json['rule'];self.update(v1,publish=True)
        self.flow['node_rule_configs']={'质检':dict(mode='fixed',rule=v1['value'])}
        response=self.client.post(processing.API+'/tasks',json=self.job(v1['value']),headers={'Idempotency-Key':uuid.uuid4().hex})
        self.assertEqual(201,response.status_code,response.json)
        v2=self.detail(v1)
        response=self.client.post(processing.API+'/tasks',json=self.job(v2['value']),headers={'Idempotency-Key':uuid.uuid4().hex})
        self.assertEqual(422,response.status_code,response.json)
        del self.flow['node_rule_configs']
        payload=self.job(v1['value']);payload['configs']['质检']['质检']['mode']='fixed'
        self.assertEqual(422,self.client.post(processing.API+'/tasks',json=payload,headers={'Idempotency-Key':uuid.uuid4().hex}).status_code)

    def test_separate_edit_and_publish_permissions(self):
        v1=self.create().json['rule']
        self.app.config['PROCESSING_RULE_PERMISSIONS']=dict(create=False,edit=True,publish=False,manage=False)
        pending=self.update(v1,publish=False)
        self.assertEqual(200,pending.status_code,pending.json)
        self.assertEqual(403,self.create('blocked',name='无权创建').status_code)
        self.assertEqual(403,self.client.post('/data/rules/'+v1['id']+'/status',json=dict(status='disabled')).status_code)
        self.app.config['PROCESSING_RULE_PERMISSIONS']=dict(create=False,edit=False,publish=True,manage=True)
        response=self.client.post('/data/rules/'+v1['id']+'/publish',json=dict(revision=pending.json['rule']['revision']))
        self.assertEqual(200,response.status_code,response.json)

    def test_legacy_alias_cannot_bypass_managed_rule_version_or_status(self):
        self.app.config['PROCESSING_RULE_LEGACY']=[dict(name=self.body['name'],stage='质检',version='v1')]
        v1=self.create().json['rule'];self.update(v1,publish=True)
        result=self.client.post(processing.API+'/tasks',json=self.job(self.body['name']+' v1'),headers={'Idempotency-Key':uuid.uuid4().hex})
        self.assertEqual(422,result.status_code,result.json)
        self.assertIn('新版',result.json['error'])

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

    def test_reverting_pending_content_clears_pending_without_new_version(self):
        v1=self.create().json['rule'];pending=self.update(v1,publish=False).json['rule']
        reverted=self.client.post(rules.API+'/'+v1['id']+'/revisions',json=dict(self.body,publish=False,revision=pending['revision']))
        self.assertFalse(reverted.json['rule']['has_draft']);self.assertEqual('v1',reverted.json['rule']['version'])
        self.assertEqual('撤销待发布修改',reverted.json['rule']['events'][-1]['action'])

    def test_discard_history_and_reject_historical_edit(self):
        v1=self.create().json['rule'];draft=self.update(v1,publish=False).json['rule']
        result=self.client.delete(rules.API+'/'+v1['id']+'/draft',json=dict(revision=draft['revision']))
        self.assertEqual(200,result.status_code)
        clean=result.json['rule'];self.assertFalse(clean['has_draft']);self.assertEqual(1,len(clean['versions']))
        v2=self.update(clean,publish=True).json['rule']
        restore=dict(self.body,revision=v2['revision'],publish=True,restore_from=1)
        rejected=self.client.post(rules.API+'/'+v2['id']+'/revisions',json=restore)
        self.assertEqual(422,rejected.status_code)
        self.assertIn('历史版本仅供查看',rejected.json['error'])
        unchanged=self.detail(v2)
        self.assertEqual('v2',unchanged['version'])
        self.assertEqual(2,len(unchanged['versions']))
        self.assertEqual(403,self.client.delete('/data/rules/'+v2['id'],json=dict(revision=v2['revision'])).status_code)

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
        saved=self.update(v1,publish=False).json['rule']
        self.app.config['PROCESSING_RULE_PERMISSIONS']={'create':False,'publish':False}
        self.assertEqual(403,self.update(saved,publish=False).status_code)

    def test_disabled_stays_disabled_after_new_revision(self):
        v1=self.create().json['rule']
        result=self.client.post('/data/rules/'+v1['id']+'/status',json=dict(status='disabled')).json['rule']
        v2=self.update(result,publish=True).json['rule']
        self.assertEqual('disabled',v2['status']);self.assertEqual('v2',v2['version'])

    def test_concurrent_revision_only_one_writes(self):
        v1=self.create().json['rule']
        def submit(label):
            with self.app.test_client() as client:
                return client.post(rules.API+'/'+v1['id']+'/revisions',json=dict(self.body,
                    revision=v1['revision'],publish=False,quality_mistakes=[label])).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual([200,409],sorted(pool.map(submit,['修订A','修订B'])))
        self.assertEqual(1,len(self.detail(v1)['versions']))

    def test_annotation_structure_history_and_zero_data(self):
        body=dict(self.body,stage='标注',rule_type='标签标注',annotation_tags=['tag.a','tag.b'])
        v1=self.client.post(rules.API,json=body,headers={'Idempotency-Key':'tags'}).json['rule']
        v2=self.client.post(rules.API+'/'+v1['id']+'/revisions',json=dict(body,
            revision=v1['revision'],annotation_tags=['tag.b','tag.c'])).json['rule']
        self.assertEqual(['tag.a','tag.b'],v2['versions'][0]['content']['annotation_tags'])
        self.assertEqual(['tag.b','tag.c'],v2['versions'][1]['content']['annotation_tags'])
        quality=self.create('quality',name='零数据质检').json['rule']
        job=self.job(quality['value']);job.update(source_ids=['02605'],filters=[['采集任务 ID','等于','02605']])
        result=self.client.post(processing.API+'/tasks',json=job,headers={'Idempotency-Key':uuid.uuid4().hex})
        self.assertEqual(201,result.status_code,result.json)
        self.assertEqual(0,result.json['task']['candidate_count'])
