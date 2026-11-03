"""Synthetic demo enrichment preserves user data and actual membership semantics."""
import json
import tempfile
import unittest
from pathlib import Path

from flask import Flask

import collection_demo_data as demo
import collection_processing as processing
import post_training_collection as collection


class DemoSeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, COLLECTION_DEMO_DB=str(Path(self.tmp.name) / 'demo.sqlite3'))
        self.flows = [dict(stage='质检', name='自动质检', human_nodes=[]),
                      dict(stage='标注', name='人工标注', human_nodes=['标注'])]
        collection.register_collection(self.app, lambda title, content, **kw: content,
                                      [dict(id='a', name='亮剑')], [dict(id='1', name='模型', status='cached')])
        processing.register_processing(self.app, self.flows)
        demo.register_demo_seed(self.app, self.flows)

    def tearDown(self):
        self.tmp.cleanup()

    def test_fresh_deployment_initializes_links_without_cli(self):
        self.app.testing = False
        client = self.app.test_client()
        self.assertFalse(Path(self.app.config['COLLECTION_DEMO_DB']).exists())
        tasks = client.get(collection.API + '/tasks').json['tasks']
        self.assertEqual(['02602', '02607', '02601'], [task['id'] for task in tasks[:3]])
        self.assertEqual([3, 2, 2], [task['processing_task_count'] for task in tasks[:3]])
        jobs = client.get(processing.API + '/tasks?collection=02602').json['tasks']
        self.assertEqual(3, len(jobs))
        self.assertTrue(all(job['records'] for job in jobs))
        # A second worker or restart encounters existing markers, not duplicate jobs.
        with self.app.app_context(), collection.database() as conn, conn:
            again = demo.seed_demo(conn, self.flows)
        self.assertTrue(again['already_seeded'])
        self.assertEqual(tasks, client.get(collection.API + '/tasks').json['tasks'])

    def test_auto_seed_upgrades_existing_database_preserving_user_task(self):
        client = self.app.test_client()
        manual = client.post(collection.API + '/tasks', json=dict(name='保留已有任务', source='udas',
                             project='a', description='保留内容')).json['task']
        self.app.testing = False
        self.assertEqual(5, len(client.get(processing.API + '/tasks').json['tasks']))
        self.assertEqual(manual, client.get(collection.API + '/tasks/' + manual['id']).json['task'])

    def test_auto_seed_can_be_disabled_and_testing_is_explicit(self):
        client = self.app.test_client()
        self.assertEqual([], client.get(processing.API + '/tasks').json['tasks'])
        self.app.testing = False
        self.app.config['COLLECTION_DEMO_AUTO_SEED'] = False
        self.assertEqual([], client.get(processing.API + '/tasks').json['tasks'])
        self.app.config['COLLECTION_DEMO_AUTO_SEED'] = True
        self.assertEqual(5, len(client.get(processing.API + '/tasks').json['tasks']))

    def test_seed_preserves_manual_task_and_is_repeatable(self):
        client = self.app.test_client()
        manual = client.post(collection.API+'/tasks', json=dict(name='用户手动创建', source='udas',
                             project='a', description='保留内容')).json['task']
        result = self.app.test_cli_runner().invoke(args=['seed-collection-demo'])
        self.assertEqual(0, result.exit_code, result.output)
        totals = json.loads(result.output)
        self.assertEqual(6, totals['tasks'])
        self.assertGreater(totals['records'], 300)
        self.assertEqual(5, totals['processing_tasks'])
        self.assertEqual(manual, client.get(collection.API+'/tasks/'+manual['id']).json['task'])
        before = client.get(processing.API+'/tasks').json
        repeat = self.app.test_cli_runner().invoke(args=['seed-collection-demo'])
        self.assertEqual(0, repeat.exit_code, repeat.output)
        self.assertTrue(json.loads(repeat.output)['already_seeded'])
        self.assertEqual(before, client.get(processing.API+'/tasks').json)

    def test_demo_membership_and_states_are_consistent(self):
        result = self.app.test_cli_runner().invoke(args=['seed-collection-demo'])
        self.assertEqual(0, result.exit_code, result.output)
        client = self.app.test_client()
        jobs = client.get(processing.API+'/tasks').json['tasks']
        self.assertEqual(5, len(jobs))
        self.assertEqual({'processing','completed','pending'}, {j['status'] for j in jobs})
        self.assertTrue(all(j['creator'] == 'joanna.qiao' for j in jobs))
        memberships = {}
        for job in jobs:
            if not job['published']:
                self.assertEqual([], job['records'])
            for record in job['records']:
                if record['stages'].get('质检') == 'completed':
                    self.assertIn(record.get('results', {}).get('质检', {}).get('conclusion'), ('合格', '不合格'))
                key = (record['task_id'], record['id'])
                memberships[key] = memberships.get(key, 0)+1
                task = client.get(collection.API+'/tasks/'+record['task_id']).json['task']
                self.assertEqual('uploaded', next(r for r in task['records'] if r['id']==record['id'])['upload'])
        self.assertTrue(any(count>1 for count in memberships.values()))
        task = client.get(collection.API+'/tasks/02602').json['task']
        self.assertTrue(any((task['id'],r['id']) not in memberships for r in task['records'] if r['upload']=='uploaded'))

        for task_id, count in [('02602', 3), ('02601', 2), ('02607', 2)]:
            related = client.get(processing.API+'/tasks?collection='+task_id).json['tasks']
            self.assertEqual(count, len(related))
            self.assertTrue(any(key[0] == task_id and value > 1 for key, value in memberships.items()))
        shared = [job for job in jobs if len(job['source_ids']) > 1]
        self.assertEqual(2, len(shared))
        self.assertTrue(all({r['task_id'] for r in job['records']} == {'02601', '02607'} for job in shared))
        listed = client.get(collection.API+'/tasks').json['tasks']
        self.assertEqual(['02602', '02607', '02601'], [task['id'] for task in listed[:3]])
        self.assertEqual([3, 2, 2], [task['processing_task_count'] for task in listed[:3]])
        self.assertTrue(all(task['processing_task_count'] == 0 for task in listed[3:]))

    def test_compact_migration_preserves_manual_and_edited_jobs(self):
        runner = self.app.test_cli_runner()
        self.assertEqual(0, runner.invoke(args=['seed-collection-demo']).exit_code)
        with self.app.app_context(), collection.database() as conn, conn:
            conn.execute('DELETE FROM collection_meta WHERE key=?', (demo.PROCESSING_FIXTURE,))
            original = json.loads(conn.execute('SELECT payload FROM collection_processing WHERE id=?', ('30001',)).fetchone()['payload'])
            for job_id, fixture, revision in [('40004', demo.FIXTURE, 1),
                                               ('40005', demo.FIXTURE, 2), ('40006', None, 1)]:
                job = dict(original, id=job_id, name='保留用户修改' if revision == 2 else '额外任务', revision=revision)
                if fixture:
                    job['demo_fixture'] = fixture
                else:
                    job.pop('demo_fixture', None)
                payload = json.dumps(job, ensure_ascii=False)
                conn.execute('INSERT INTO collection_processing VALUES (?, ?, ?, ?)',
                             (job_id, job_id, demo.hashlib.sha256(payload.encode()).hexdigest(), payload))
        result = runner.invoke(args=['seed-collection-demo'])
        self.assertEqual(0, result.exit_code, result.output)
        jobs = self.app.test_client().get(processing.API+'/tasks').json['tasks']
        self.assertEqual({'30001','30002','30003','30004','30005','40005','40006'}, {j['id'] for j in jobs})
        self.assertEqual('保留用户修改', next(j for j in jobs if j['id'] == '40005')['name'])

    def test_multi_stage_example_has_real_nodes_and_non_end_rework(self):
        flows=[dict(stage='质检',name='人工质检验收',human_nodes=['质检','质检验收']),
               dict(stage='标注',name='人工标注验收',human_nodes=['标注','标注验收'])]
        # The normal seed also needs its automatic quality flow.
        self.flows.extend(flows)
        self.assertEqual(0,self.app.test_cli_runner().invoke(args=['seed-collection-demo']).exit_code)
        with self.app.app_context(),collection.database() as conn:
            job=processing.get_job(conn,'30005')
            scoped=processing.public_job(conn,job,'02601')
        self.assertEqual({'质检','标注'},set(job['stages']))
        qc,annotation=scoped['stage_progress']
        self.assertEqual((2,1),(qc['done'],annotation['done']))
        self.assertEqual((4,4),(sum(n['total'] for n in qc['nodes']),sum(n['total'] for n in annotation['nodes'])))
        self.assertTrue(any(s['label']=='驳回返工' for n in qc['nodes'] for s in n['states']))
        self.assertTrue(any(s['label']=='待验收' for n in annotation['nodes'] for s in n['states']))

    def test_existing_demo_quality_repair_is_scoped_and_repeatable(self):
        runner = self.app.test_cli_runner()
        self.assertEqual(0, runner.invoke(args=['seed-collection-demo']).exit_code)
        with self.app.app_context(), collection.database() as conn, conn:
            job = processing.get_job(conn, '30004')
            job['records'][0]['results'].pop('质检')
            job['records'][1]['results']['质检']['conclusion'] = '不合格'
            # Simulate the former persisted fixture without using the new write guard.
            conn.execute('UPDATE collection_processing SET payload=? WHERE id=?', (json.dumps(job), job['id']))
            manual = dict(job, id='40007', demo_fixture=None)
            conn.execute('INSERT INTO collection_processing VALUES (?, ?, ?, ?)', ('40007', 'manual', 'manual', json.dumps(manual)))
        repaired = runner.invoke(args=['seed-collection-demo'])
        self.assertEqual(0, repaired.exit_code, repaired.output)
        self.assertEqual(1, json.loads(repaired.output)['repaired_quality_results'])
        with self.app.app_context(), collection.database() as conn:
            repaired_job = processing.get_job(conn, '30004')
            self.assertEqual('合格', repaired_job['records'][0]['results']['质检']['conclusion'])
            self.assertEqual('不合格', repaired_job['records'][1]['results']['质检']['conclusion'])
            self.assertNotIn('质检', processing.get_job(conn, '40007')['records'][0]['results'])
        again = runner.invoke(args=['seed-collection-demo'])
        self.assertEqual(0, again.exit_code, again.output)
        self.assertEqual(0, json.loads(again.output)['repaired_quality_results'])
