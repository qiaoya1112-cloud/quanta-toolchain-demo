import json
import re
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from toolchain_demo import app


class JobCenterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_db = app.config.get('WORKBENCH_POOL_DB')
        app.config['WORKBENCH_POOL_DB'] = str(Path(self.temp.name) / 'pools.sqlite3')
        self.client = app.test_client()
        self.base = '/data/job-centers/1'
        self.node = '?task=WB-PRETRAINING-QC'

    def tearDown(self):
        if self.previous_db is None:
            app.config.pop('WORKBENCH_POOL_DB', None)
        else:
            app.config['WORKBENCH_POOL_DB'] = self.previous_db
        self.temp.cleanup()

    def claim(self, client=None, center=1, task='WB-PRETRAINING-QC'):
        return (client or self.client).post(f'/data/job-centers/{center}/claim?task={task}', json={})

    def test_two_views_parent_totals_and_placeholder(self):
        for center in (1, 2):
            response = self.client.get(f'/data/job-centers/{center}')
            self.assertEqual(200, response.status_code)
            html = response.get_data(as_text=True)
            self.assertIn('作业记录', html)
            payload = json.loads(re.search(r'id="jcPayload">(.*?)</script>', html, re.S)[1])
            for group in payload['groups']:
                self.assertEqual(group['count'], sum(node['count'] for node in group['nodes']))
            self.assertIn('任务列表' if center==1 else '流程列表', html)
        self.assertEqual(404, self.client.get('/data/job-centers/3').status_code)

    def test_conditions_persist_apply_together_and_never_fall_back(self):
        response = self.client.post(self.base+'/state'+self.node, json={'collection_task_id':'20456', 'supplier':'SUP-001', 'operator':'刘立斌'})
        self.assertEqual(1, response.json['available'])
        self.assertEqual(response.json['conditions'], self.client.get(self.base+'/state'+self.node).json['conditions'])
        claimed = self.claim()
        self.assertEqual(200, claimed.status_code)
        self.assertEqual(['7523787'], claimed.json['jobs'][0]['record_ids'])
        self.assertEqual(409, self.claim().status_code)
        self.client.post(self.base+'/state'+self.node, json={})
        self.assertEqual(9, self.client.get(self.base+'/state'+self.node).json['available'])
        self.assertEqual(400, self.client.post(self.base+'/state'+self.node,json={'supplier':[]}).status_code)

    def test_batch_is_scoped_no_status_and_owned(self):
        claimed = self.claim().json
        self.assertEqual(10, claimed['claimed'])
        url = claimed['jobs'][0]['url']
        home = self.client.get(self.base+self.node).get_data(as_text=True)
        self.assertIn('const action = \'<a class="btn btn-primary" href="\'+escape(job.url)+\'">处理</a>\';',
                      Path('static/job_centers/center.js').read_text())
        self.assertNotIn('workbench_pool/rows.js', home)
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        self.assertNotIn('<th>状态</th>', html)
        self.assertIn('<th>操作结论</th>', html)
        for control in ('id="wpFilters"', 'id="wpCount"', 'id="wpBatch"', 'id="wpSelectAll"'):
            self.assertNotIn(control, html)
        payload=json.loads(re.search(r'id="wpPayload" type="application/json">(.*?)</script>',html,re.S)[1])
        self.assertEqual(10,len(payload['records']))
        self.assertIn('class="wp-action-cell">操作</th>', html)
        self.assertEqual('OP-001', payload['records'][0]['collector_id'])
        self.assertEqual(404,app.test_client().get(url).status_code)
        detail_url=url.replace('/process?', '/details?')
        detail=self.client.get(detail_url)
        self.assertEqual(200, detail.status_code)
        self.assertEqual(set(claimed['jobs'][0]['record_ids']), {record['id'] for record in detail.json['records']})
        self.assertNotIn('owner', detail.json['records'][0])
        self.assertEqual(404, app.test_client().get(detail_url).status_code)
        task='WB-PRETRAINING-QC'
        process='/data/job-centers/1/record?task='+task+'&unit='+claimed['jobs'][0]['id']+'&recording_id='
        self.assertEqual(302,self.client.get(process+payload['records'][0]['id']).status_code)
        self.assertEqual(404,self.client.get(process+'unknown').status_code)

    def test_single_opens_annotation_and_both_centers_share_claims(self):
        response=self.claim(task='WB-E2E-ACCEPTANCE')
        self.assertEqual(1,response.json['claimed'])
        job=response.json['jobs'][0]
        opened=self.client.get(job['url'])
        self.assertEqual(302,opened.status_code)
        self.assertIn('mode=annotation',opened.location)
        editor=self.client.get(opened.location)
        self.assertEqual(200,editor.status_code)
        self.assertIn('语义标注工作台',editor.get_data(as_text=True))
        state=self.client.get('/data/job-centers/2/state?task=WB-E2E-ACCEPTANCE').json
        self.assertEqual(job['record_ids'],state['jobs'][0]['record_ids'])
        self.assertEqual('领取', job['source_action'])
        self.assertEqual(1, job['current_round'])
        self.assertEqual(404, self.client.get(job['url'].replace('/process?', '/details?')).status_code)

    def test_concurrent_claims_do_not_overlap(self):
        clients=[app.test_client(),app.test_client()]
        with ThreadPoolExecutor(max_workers=2) as executor:
            responses=list(executor.map(lambda client:self.claim(client),clients))
        self.assertEqual([200,409],sorted(response.status_code for response in responses))
        winner=next(response for response in responses if response.status_code==200)
        self.assertEqual(10,len(winner.json['jobs'][0]['record_ids']))

    def test_finish_keeps_batch_metadata_and_other_records(self):
        claim=self.claim().json
        job=claim['jobs'][0]
        response=self.client.post('/data/workbench-v2/pools/POOL-PRETRAINING-QC/records/actions',json={'action':'finish','ids':[job['record_ids'][0]],'result':'合格'})
        self.assertEqual(200,response.status_code)
        completed=next(record for record in response.json['records'] if record['id']==job['record_ids'][0])
        self.assertEqual(job['id'],completed['job_batch'])
        batch=self.client.get(job['url']).get_data(as_text=True)
        payload=json.loads(re.search(r'id="wpPayload" type="application/json">(.*?)</script>',batch,re.S)[1])
        self.assertEqual(9,len(payload['records']))


if __name__=='__main__':
    unittest.main()
