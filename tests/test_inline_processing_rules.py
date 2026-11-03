"""Rule creation, shared catalog, and server-side permission/publication guards."""
import copy
import json
import tempfile
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from flask import Flask
import post_training_collection as collection
import collection_processing as processing
import processing_rule_store as rules


class InlineRulesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, COLLECTION_DEMO_DB=str(Path(self.tmp.name)/'rules.sqlite'))
        collection.register_collection(self.app, lambda title, content, **kw:content,
                                      [dict(id='a', name='亮剑'), dict(id='b', name='京东项目')], [dict(id='1',name='模型',status='cached')])
        self.flow = dict(stage='质检', name='人工质检', human_nodes=['质检'])
        self.annotation_flow = dict(stage='标注', name='人工标注', human_nodes=['标注'])
        processing.register_processing(self.app,[self.flow, self.annotation_flow])
        rules.register_rules(self.app, [], [], lambda rows,project:'shared editor')
        self.client=self.app.test_client()
        self.body=dict(name='亮剑质检要求',project='亮剑',stage='质检',rule_type='质检',quality_mistakes=['动作未完成'],
                       quality_unqualified=['画面不完整'],error_reasons=[dict(name='结论不符')],publish=True)

    def tearDown(self):
        self.tmp.cleanup()

    def create(self, key='key', **changes):
        return self.client.post(rules.API,json=dict(self.body,**changes),headers={'Idempotency-Key':key})

    def job(self, rule):
        return dict(name='质检处理',source_ids=['02601'],filters=[['采集任务 ID','等于','02601']],
                    stages={'质检':'人工质检'},configs={'质检':{'质检':dict(rule=rule,assignments=[dict(type='supplier',target='光轮智能')])}})

    def test_shared_catalog_and_idempotency(self):
        created=self.create(); self.assertEqual(201,created.status_code)
        self.assertEqual(200,self.create().status_code)
        result=created.json['rule']
        self.assertEqual('已发布',result['publish_status'])
        self.assertEqual([result['id']],[r['id'] for r in self.client.get(rules.API+'?project=亮剑').json['rules']])
        self.assertEqual(409,self.create('another-key').status_code)
        self.assertEqual(409,self.create(name='不同内容').status_code)
        self.assertEqual([],self.client.get(rules.API+'?project=京东项目').json['rules'])
        with self.app.app_context():
            self.assertEqual(result['id'],rules.catalog([])[0]['id'])
        self.assertEqual(200,self.client.get('/data/rules/editor-fragment?project=亮剑').status_code)

    def test_no_create_permission_frontend_contract_and_api(self):
        self.app.config['PROCESSING_RULE_PERMISSIONS']={'create':False,'publish':True}
        self.assertFalse(self.client.get(rules.API+'?project=亮剑').json['permissions']['create'])
        self.assertEqual(403,self.create().status_code)
        self.assertEqual(403,self.client.get('/data/rules/editor-fragment?project=亮剑').status_code)
        self.assertEqual(403,self.client.get(rules.API+'/check-name?project=亮剑&name=test').status_code)

    def test_name_check_covers_drafts_disabled_and_edit_self(self):
        rule = self.create(publish=False).json['rule']
        def check(name, project='亮剑', exclude=''):
            return self.client.get(rules.API+'/check-name', query_string=dict(
                name=name, project=project, exclude_id=exclude)).json['duplicate']
        self.assertTrue(check('  '+self.body['name']+'  '))
        self.assertFalse(check(self.body['name'], '京东项目'))
        self.assertFalse(check(self.body['name'], exclude=rule['id']))
        duplicate = self.create('duplicate', name=' '+self.body['name']+' ')
        self.assertEqual(409, duplicate.status_code)
        self.assertEqual('name', duplicate.json['field'])
        other = self.create('other', name='另一规则', publish=False).json['rule']
        renamed = self.client.put(rules.API+'/'+other['id'], json=dict(self.body, publish=False))
        self.assertEqual(409, renamed.status_code)
        self.assertEqual(200, self.client.post('/data/rules/'+rule['id']+'/publish', json=dict(revision=rule['revision'])).status_code)
        self.assertEqual(200, self.client.post('/data/rules/'+rule['id']+'/status', json=dict(status='disabled')).status_code)
        self.assertTrue(check(self.body['name']))
        self.assertEqual(201, self.create('latin', name='QC Rule').status_code)
        self.assertTrue(check(' qc rule '))
        self.assertEqual(409, self.create('latin-duplicate', name='qc rule').status_code)
        self.assertEqual(200, self.client.delete('/data/rules/'+other['id'],json=dict(revision=other['revision'])).status_code)
        self.assertFalse(check('另一规则'))
        self.app.config['PROCESSING_RULE_SEEDS'].append(dict(self.body, id='legacy-seed', name='种子规则'))
        self.assertTrue(check('种子规则'))
        self.assertEqual(409, self.create('seed-duplicate', name='种子规则').status_code)

    def test_concurrent_new_rules_cannot_claim_same_name(self):
        self.client.get(rules.API)
        def submit(key):
            with self.app.test_client() as client:
                return client.post(rules.API, json=self.body,
                                   headers={'Idempotency-Key':key}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual([201, 409], sorted(pool.map(submit, ['first', 'second'])))
        with self.app.app_context():
            self.assertEqual(1, len(rules.catalog([])))

    def test_no_publish_permission_saves_only_unpublished(self):
        self.app.config['PROCESSING_RULE_PERMISSIONS']={'create':True,'publish':False}
        self.assertEqual(403,self.create().status_code)
        response=self.create(publish=False);self.assertEqual(201,response.status_code)
        rule=response.json['rule'];self.assertEqual('未发布',rule['publish_status'])
        self.assertEqual([],self.client.get(rules.API+'?project=亮剑').json['rules'])
        self.assertEqual(403,self.client.post('/data/rules/'+rule['id']+'/publish').status_code)
        self.assertEqual(422,self.client.post('/data/rules/'+rule['id']+'/status',json={'status':'enabled'}).status_code)
        job=self.client.post(processing.API+'/tasks',json=self.job(rule['value']),headers={'Idempotency-Key':str(uuid.uuid4())})
        self.assertEqual(422,job.status_code)

    def test_project_permissions_resolved_on_server(self):
        self.app.config['PROCESSING_RULE_PERMISSION_RESOLVER']=lambda project:dict(create=project=='亮剑',publish=project=='亮剑')
        self.assertEqual(201,self.create().status_code)
        self.assertEqual(403,self.create('other',project='京东项目').status_code)
        self.assertEqual(403,self.client.get('/data/rules/editor-fragment?project=京东项目').status_code)

    def test_task_reference_validated_and_rechecked_at_publish(self):
        rule=self.create().json['rule']
        response=self.client.post(processing.API+'/tasks',json=self.job(rule['value']),headers={'Idempotency-Key':str(uuid.uuid4())})
        self.assertEqual(201,response.status_code,response.json);job=response.json['task']
        self.assertEqual(200,self.client.post('/data/rules/'+rule['id']+'/status',json=dict(status='disabled')).status_code)
        published=self.client.post(processing.API+'/tasks/'+job['id']+'/action',json=dict(action='publish',revision=job['revision']))
        self.assertEqual(422,published.status_code)
        self.assertIn('停用',published.json['error'])

    def test_unpublished_can_publish_edit_delete_but_published_is_immutable(self):
        rule=self.create(publish=False).json['rule']
        renamed=self.client.put(rules.API+'/'+rule['id'],json=dict(self.body,name='编辑后的名称',publish=False,revision=rule['revision']))
        self.assertEqual(200,renamed.status_code)
        edited=self.client.put(rules.API+'/'+rule['id'],json=dict(self.body,quality_mistakes=['修改后的标准'],publish=False,revision=renamed.json['rule']['revision']))
        self.assertEqual(200,edited.status_code)
        self.assertEqual(self.body['name'],edited.json['rule']['name'])
        published=self.client.post('/data/rules/'+rule['id']+'/publish',json=dict(revision=edited.json['rule']['revision']));self.assertEqual(200,published.status_code)
        self.assertEqual(403,self.client.put(rules.API+'/'+rule['id'],json=self.body).status_code)
        self.assertEqual(403,self.client.delete('/data/rules/'+rule['id'],json=dict(revision=published.json['rule']['revision'])).status_code)
        second=self.create('second',name='可删除草稿',publish=False).json['rule']
        self.assertEqual(200,self.client.delete('/data/rules/'+second['id'],json=dict(revision=second['revision'])).status_code)
        with self.app.app_context():
            self.assertEqual(1,len(rules.catalog([])))

    def test_all_rule_types_and_validation(self):
        variants=[dict(stage='标注',rule_type='标签标注',annotation_tags=['tag.one']),
                  dict(stage='标注',rule_type='语义标注',semantic_mode='text',semantic_text='标注切分边界'),
                  dict(stage='标注',rule_type='语义标注',semantic_mode='link',document_link='https://example.com/rule'),
                  dict(stage='标注',rule_type='动作标注',action_elements=[dict(name='物品',key='item',values=[dict(name='茶杯',key='cup')])],action_descriptions=[dict(zh='拿起{物品}',en='Pick up {item}')])]
        for i,variant in enumerate(variants):
            self.assertEqual(201,self.create(str(i),name='规则'+str(i),**variant).status_code)
        for changes in (dict(error_reasons=[]),dict(quality_mistakes=[]),dict(stage='坏环节'),dict(project='不存在'),dict(publish='false')):
            self.assertEqual(422,self.create('invalid',**changes).status_code)
        self.assertEqual(422,self.client.post(rules.API,json=None).status_code)

    def test_cross_project_and_stage_rule_rejected(self):
        rule=self.create(project='京东项目').json['rule']
        rejected=self.client.post(processing.API+'/tasks',json=self.job(rule['value']),headers={'Idempotency-Key':str(uuid.uuid4())})
        self.assertEqual(422,rejected.status_code)
        self.assertIn('不匹配',rejected.json['error'])

    def test_task_rejects_rule_from_other_stage_in_both_directions(self):
        quality=self.create('quality').json['rule']
        annotation=self.create('annotation',name='语义标注规则',stage='标注',rule_type='语义标注',
                               semantic_mode='text',semantic_text='按动作切分').json['rule']
        wrong_quality=self.client.post(processing.API+'/tasks',json=self.job(annotation['value']),
                                       headers={'Idempotency-Key':str(uuid.uuid4())})
        self.assertEqual(422,wrong_quality.status_code)
        self.assertIn('业务环节不匹配',wrong_quality.json['error'])
        job=self.job(quality['value'])
        job['stages']={'标注':'人工标注'}
        job['configs']={'标注':{'标注':dict(rule=quality['value'],assignments=[dict(type='supplier',target='光轮智能')])}}
        wrong_annotation=self.client.post(processing.API+'/tasks',json=job,
                                          headers={'Idempotency-Key':str(uuid.uuid4())})
        self.assertEqual(422,wrong_annotation.status_code)
        self.assertIn('业务环节不匹配',wrong_annotation.json['error'])

    def test_inline_creation_rejects_other_stage_even_when_body_is_internally_valid(self):
        quality_context=dict(project='亮剑',stage='质检',flow='双轮人工质检流程',node='质检')
        result=self.create('wrong-inline-quality',node_context=quality_context,stage='标注',rule_type='语义标注',
                           semantic_mode='text',semantic_text='按动作切分')
        self.assertEqual(422,result.status_code)
        self.assertIn('业务环节不匹配',result.json['error'])
        annotation_context=dict(project='亮剑',stage='标注',flow='双轮人工标注流程',node='标注')
        result=self.create('wrong-inline-annotation',node_context=annotation_context)
        self.assertEqual(422,result.status_code)
        self.assertIn('业务环节不匹配',result.json['error'])
        with self.app.app_context():
            self.assertEqual([],rules.catalog([]))

    def test_legacy_rule_must_match_flow_type(self):
        self.app.config['PROCESSING_RULE_LEGACY']=[dict(name='旧动作标注',version='v1',stage='标注',rule_type='动作标注')]
        flow=dict(name='端到端切分标注流程',stage='标注',rule_types=['语义标注'])
        with self.app.app_context(), collection.database() as conn:
            self.assertIn('类型不适用',rules.reference_error(conn,'旧动作标注 v1','亮剑','标注',flow))
            flow['rule_types']=['动作标注']
            self.assertIsNone(rules.reference_error(conn,'旧动作标注 v1','亮剑','标注',flow))

    def test_node_context_cannot_override_inherited_or_flow_type(self):
        context=dict(project='亮剑',flow='端到端切分标注流程',node='供应商复核')
        result=self.create(node_context=context,stage='标注',rule_type='语义标注',semantic_mode='text',semantic_text='边界切分')
        self.assertEqual(422,result.status_code)
        context['node']='供应商抽验'
        result=self.create(node_context=context,stage='标注',rule_type='标签标注',annotation_tags=['tag.one'])
        self.assertEqual(422,result.status_code)
        result=self.create(node_context=context,stage='标注',rule_type='语义标注',semantic_mode='text',semantic_text='边界切分')
        self.assertEqual(201,result.status_code)


if __name__=='__main__':unittest.main()
