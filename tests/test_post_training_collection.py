"""Collection facts, change logs and lifecycle checks with an isolated local DB."""
import copy
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

from flask import Flask

import post_training_collection as collection


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="quanta-collection-")
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, COLLECTION_DEMO_DB=str(Path(self.directory.name) / "tasks.sqlite3"))
        collection.register_collection(self.app, lambda title, content, **kwargs: content,
                                       [{"id": "project-a", "name": "演示项目"}],
                                       [{"id": "9001", "name": "可用模型", "status": "cached"},
                                        {"id": "9002", "name": "未缓存模型", "status": "not_cached"}])
        self.client = self.app.test_client()
        self.base = collection.API + "/tasks"

    def tearDown(self):
        self.directory.cleanup()

    def payload(self, **kwargs):
        body = dict(name="遥操采集测试", project="project-a", source="robot", mode="NORMAL",
                    description="摆场后执行取放动作，归位后结束录制。", tags=[], spec_url="",
                    location="", checkpoint="", prompt_ids=[], generalization=[])
        body.update(kwargs)
        return body

    def get(self, task_id):
        return self.client.get(self.base + "/" + task_id).json["task"]

    def update_config(self, task, **kwargs):
        body = {k: copy.deepcopy(task[k]) for k in self.payload() if k in task}
        body["prompt_ids"] = [p["id"] for p in task["prompts"]]
        body.update(kwargs, revision=task["revision"])
        return self.client.patch(self.base + "/" + task["id"], json=body)

    def test_normal_creation_discards_model_configuration(self):
        response = self.client.post(self.base, json=self.payload(checkpoint="9001", prompt_ids=[collection.PROMPTS[0]["id"]]))
        self.assertEqual(201, response.status_code)
        task = response.json["task"]
        self.assertEqual(([], "", "open"), (task["prompts"], task["checkpoint"], task["status"]))
        self.assertEqual([], task["records"])
        self.assertEqual(task, self.get(task["id"]))

    # 【新】Task fields and shared specification catalog contract.
    def test_priority_hours_persist_edit_log_and_do_not_close_task(self):
        r = self.client.post(self.base, json=self.payload(priority=9, expected_hours=.001))
        self.assertEqual(201, r.status_code)
        task = r.json['task']
        self.assertEqual((9, .001, 'open'), (task['priority'], task['expected_hours'], task['status']))
        updated = self.client.patch(self.base+'/'+task['id'], json={'revision': task['revision'], 'priority': 2, 'expected_hours': 18.5}).json['task']
        self.assertEqual({'priority', 'expected_hours'}, {c['field'] for c in updated['events'][-1]['changes']})
        self.assertEqual(updated, self.get(task['id']))
        clear = self.client.patch(self.base+'/'+task['id'], json={'revision': updated['revision'], 'expected_hours': None}).json['task']
        self.assertIsNone(clear['expected_hours'])
        fixture = self.get('02602')
        result = self.client.patch(self.base+'/'+fixture['id'], json={'revision': fixture['revision'], 'expected_hours': .000001}).json['task']
        self.assertGreater(result['metrics']['seconds']/3600, result['expected_hours'])
        self.assertEqual('open', result['status'])

    def test_priority_hours_validation_and_legacy_defaults(self):
        for priority in [0, 10, True, '6', 1.5, None]:
            with self.subTest(priority=priority):
                r = self.client.post(self.base, json=self.payload(priority=priority))
                self.assertEqual(422, r.status_code)
                self.assertIn('priority', r.json['errors'])
        for hours in [-1, 0, True, '12', float('inf'), float('nan'), 1000001]:
            with self.subTest(hours=hours):
                r = self.client.post(self.base, json=self.payload(expected_hours=hours))
                self.assertEqual(422, r.status_code)
                self.assertIn('expected_hours', r.json['errors'])
        self.assertEqual((6, None), (self.get('02601')['priority'], self.get('02601')['expected_hours']))

    def test_spec_direct_link_deduplicates_and_is_selectable(self):
        url = 'https://example.feishu.cn/wiki/ExampleSpec'
        one = self.client.post(self.base, json=self.payload(spec_url=url+'?from=share#abc')).json['task']
        two = self.client.post(self.base, json=self.payload(spec_url=url+'/')).json['task']
        self.assertEqual(one['spec_id'], two['spec_id'])
        self.assertEqual(url, one['spec_url'])
        three = self.client.post(self.base, json=self.payload(spec_id=one['spec_id'])).json['task']
        self.assertEqual(url, three['spec_url'])
        specs = self.client.get(collection.API+'/specs').json['specs']
        self.assertEqual(1, len(specs))
        self.assertEqual(3, specs[0]['task_count'])

    def test_failed_task_does_not_register_spec_and_retry_is_idempotent(self):
        url = 'https://example.feishu.cn/docx/NewSpec'
        r = self.client.post(self.base, json=self.payload(name='', spec_url=url))
        self.assertEqual(422, r.status_code)
        self.assertEqual([], self.client.get(collection.API+'/specs').json['specs'])
        headers = {'Idempotency-Key': 'spec-register-retry'}
        first = self.client.post(self.base, json=self.payload(spec_url=url), headers=headers)
        second = self.client.post(self.base, json=self.payload(spec_url=url), headers=headers)
        self.assertEqual(first.json['task']['id'], second.json['task']['id'])
        self.assertEqual(1, len(self.client.get(collection.API+'/specs').json['specs']))

    def test_spec_catalog_create_edit_updates_references_and_logs(self):
        api = collection.API+'/specs'
        spec = self.client.post(api, json={'name': '原规范', 'url': 'https://example.feishu.cn/docx/SpecOne'}).json['spec']
        task = self.client.post(self.base, json=self.payload(spec_id=spec['id'])).json['task']
        new_url = 'https://example.feishu.cn/wiki/SpecTwo'
        r = self.client.patch(api+'/'+spec['id'], json={'name': '新规范', 'url': new_url, 'revision': spec['revision']})
        self.assertEqual(200, r.status_code)
        updated = self.get(task['id'])
        self.assertEqual(('新规范', new_url, task['revision']+1), (updated['spec_name'], updated['spec_url'], updated['revision']))
        self.assertEqual(task['prompts'], updated['prompts'])
        self.assertEqual({'spec_name', 'spec_url'}, {c['field'] for c in updated['events'][-1]['changes']})
        stale_task = self.client.patch(self.base+'/'+task['id'], json={'revision': task['revision'], 'priority': 3})
        self.assertEqual(409, stale_task.status_code)
        stale_spec = self.client.patch(api+'/'+spec['id'], json={'name': '覆盖', 'url': new_url, 'revision': spec['revision']})
        self.assertEqual(409, stale_spec.status_code)
        stale_selection = self.client.post(self.base, json=self.payload(spec_id=spec['id'], spec_url=spec['url']))
        self.assertEqual(422, stale_selection.status_code)

    def test_spec_catalog_validates_links_and_prevents_duplicate_documents(self):
        api = collection.API+'/specs'
        for url in ['https://evil.test/docx/Spec', 'javascript:alert(1)', 'https://a.feishu.cn.evil.test/wiki/S', 'https://user:pass@a.feishu.cn/docx/Spec', 'http://a.feishu.cn/wiki/S']:
            with self.subTest(url=url):
                self.assertEqual(422, self.client.post(api, json={'name': '规范', 'url': url}).status_code)
        url = 'https://a.feishu.cn/docx/Spec'
        self.assertEqual(201, self.client.post(api, json={'name': '规范', 'url': url}).status_code)
        self.assertEqual(409, self.client.post(api, json={'name': '重复规范', 'url': url+'?from=share'}).status_code)
        self.assertEqual(422, self.client.post(self.base, json=self.payload(spec_id='missing')).status_code)

    def test_edit_changes_spec_and_can_remove_reference(self):
        one = self.client.post(self.base, json=self.payload(spec_url='https://a.feishu.cn/wiki/One')).json['task']
        updated = self.client.patch(self.base+'/'+one['id'], json={'revision': one['revision'], 'spec_id': '', 'spec_url': 'https://a.feishu.cn/docx/Two', 'spec_name': ''}).json['task']
        self.assertNotEqual(one['spec_id'], updated['spec_id'])
        removed = self.client.patch(self.base+'/'+one['id'], json={'revision': updated['revision'], 'spec_id': '', 'spec_url': '', 'spec_name': ''}).json['task']
        self.assertEqual(('', '', ''), (removed['spec_id'], removed['spec_url'], removed['spec_name']))
        self.assertEqual(2, len(self.client.get(collection.API+'/specs').json['specs']))

    def test_concurrent_same_document_uses_one_catalog_entry(self):
        self.client.get(self.base)
        def create(_):
            with self.app.test_client() as client:
                response = client.post(self.base, json=self.payload(spec_url='https://a.feishu.cn/wiki/Shared'))
                self.assertEqual(201, response.status_code)
                return response.json['task']['spec_id']
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(1, len(set(pool.map(create, range(4)))))
        self.assertEqual(1, len(self.client.get(collection.API+'/specs').json['specs']))

    def test_five_digit_ids_and_concurrent_creation(self):
        initial = self.client.get(self.base).json["tasks"]
        self.assertTrue(all(collection.is_task_id(task["id"]) for task in initial))
        def create(_):
            with self.app.test_client() as client:
                response = client.post(self.base, json=self.payload())
                self.assertEqual(201, response.status_code)
                return response.json["task"]["id"]
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(create, range(12)))
        self.assertEqual(12, len(set(ids)))
        self.assertTrue(all(collection.is_task_id(value) for value in ids))
        self.assertTrue(set(ids).isdisjoint(task["id"] for task in initial))

    def test_creation_retries_share_one_task_even_concurrently(self):
        headers = {"Idempotency-Key": "browser-attempt-123"}
        def create(_):
            with self.app.test_client() as client:
                response = client.post(self.base, json=self.payload(), headers=headers)
                self.assertIn(response.status_code, (200, 201))
                return response.json["task"]["id"]
        # Initialize fixtures before the concurrent submissions.
        before = len(self.client.get(self.base).json["tasks"])
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(create, range(8)))
        self.assertEqual(1, len(set(ids)))
        self.assertEqual(before + 1, len(self.client.get(self.base).json["tasks"]))
        conflict = self.client.post(self.base, json=self.payload(name="changed"), headers=headers)
        self.assertEqual(409, conflict.status_code)
        self.assertEqual(ids[0], conflict.json["task_id"])

    def test_invalid_creation_does_not_consume_idempotency_key(self):
        headers = {"Idempotency-Key": "correctable-attempt"}
        invalid = self.client.post(self.base, json=self.payload(name=""), headers=headers)
        self.assertEqual(422, invalid.status_code)
        created = self.client.post(self.base, json=self.payload(), headers=headers)
        self.assertEqual(201, created.status_code)
        replay = self.client.post(self.base, json=self.payload(), headers=headers)
        self.assertEqual(200, replay.status_code)
        self.assertTrue(replay.json["replayed"])
        self.assertEqual(created.json["task"]["id"], replay.json["task"]["id"])

    def test_reopen_restarts_review_clock_and_edits_do_not(self):
        original = self.get("02603")
        self.assertTrue(original["metrics"]["needs_review"])
        closed = self.client.post(self.base + "/02603/state", json={"status": "closed", "revision": original["revision"]}).json["task"]
        reopened = self.client.post(self.base + "/02603/state", json={"status": "open", "revision": closed["revision"]}).json["task"]
        self.assertFalse(reopened["metrics"]["needs_review"])
        self.assertEqual(reopened["events"][-1]["at"], reopened["metrics"]["review_since"])
        updated = self.update_config(reopened, description="更新采集要求").json["task"]
        self.assertEqual(reopened["metrics"]["review_since"], updated["metrics"]["review_since"])
        self.assertEqual(original["records"], updated["records"])

    def test_review_threshold_latest_recording_and_closed_state(self):
        stamp = datetime(2026, 10, 25, 12, 0, 0)
        task = self.get("02603")
        task.update(created_at=(stamp-timedelta(days=7)).isoformat(), events=[])
        task["records"] = []
        task["events"] = [{"title": "重新开放采集", "at": (stamp-timedelta(hours=48)).isoformat()}]
        with patch.object(collection, "datetime", wraps=datetime) as clock:
            clock.now.return_value = stamp
            self.assertTrue(collection.task_metrics(task)["needs_review"])
            task["events"][0]["at"] = (stamp-timedelta(hours=48)+timedelta(seconds=1)).isoformat()
            self.assertFalse(collection.task_metrics(task)["needs_review"])
            record = self.get("02603")["records"][0]
            record["recorded_at"] = (stamp-timedelta(hours=1)).isoformat()
            task["records"] = [record]
            self.assertEqual(record["recorded_at"], collection.task_metrics(task)["review_since"])
            self.assertFalse(collection.task_metrics(task)["needs_review"])
            task["status"] = "closed"
            task["records"] = []
            task["events"] = []
            self.assertFalse(collection.task_metrics(task)["needs_review"])

    def test_id_migration_preserves_records_and_legacy_links(self):
        original = self.get("DC-2602")
        original["id"] = "DC-2602"
        for record in original["records"]:
            record["task_id"] = original["id"]
        extra = copy.deepcopy(original)
        extra.update(id="DC-261023-ABCDEF", name="existing custom task")
        for record in extra["records"]:
            record["task_id"] = extra["id"]
        with closing(sqlite3.connect(self.app.config["COLLECTION_DEMO_DB"])) as conn, conn:
            conn.execute("DELETE FROM collection_tasks")
            conn.execute("DELETE FROM collection_task_aliases")
            conn.execute("DELETE FROM collection_meta WHERE key IN ('five_digit_ids', 'next_task_id')")
            for task in (original, extra):
                conn.execute("INSERT INTO collection_tasks VALUES (?, ?)", (task["id"], json.dumps(task)))
        migrated = self.get("DC-2602")
        expected = copy.deepcopy(original)
        expected["id"] = "02602"
        for record in expected["records"]:
            record["task_id"] = "02602"
        self.assertEqual(expected, migrated)
        other = self.get(extra["id"])
        self.assertTrue(collection.is_task_id(other["id"]))
        self.assertNotEqual(migrated["id"], other["id"])
        self.assertEqual(other, self.get(other["id"]))
        page = self.client.get(collection.BASE + "/DC-2602/edit?card=1&version=1")
        self.assertEqual(302, page.status_code)
        self.assertTrue(page.location.endswith('/02602/edit?card=1&version=1'))
        response = self.client.post(self.base + "/DC-2602/state", json={"status":"closed", "revision":migrated["revision"]})
        self.assertEqual(200, response.status_code)
        self.assertEqual("closed", self.get("02602")["status"])

    def test_five_digit_capacity_does_not_reuse_an_id(self):
        before = self.client.get(self.base).json["tasks"]
        with closing(sqlite3.connect(self.app.config["COLLECTION_DEMO_DB"])) as conn, conn:
            conn.execute("UPDATE collection_meta SET value='100000' WHERE key='next_task_id'")
        self.assertEqual(409, self.client.post(self.base, json=self.payload()).status_code)
        self.assertEqual(before, self.client.get(self.base).json["tasks"])

    def test_collection_check_reads_latest_and_rejects_closed_without_versions(self):
        task = self.get("DC-2602")
        endpoint = self.base + "/" + task["id"] + "/collection-check"
        result = self.client.get(endpoint)
        self.assertTrue(result.json["can_start"])
        self.assertEqual("no-store", result.headers["Cache-Control"])
        for version in ("", "garbage", "0", "999"):
            result = self.client.get(endpoint, query_string={"config_version": version})
            self.assertTrue(result.json["can_start"])
            self.assertEqual("ready", result.json["reason"])
        self.assertEqual(task, self.get(task["id"]))
        changed = self.update_config(task, description=task["description"] + "补采要求").json["task"]
        stale = self.client.get(endpoint, query_string={"config_version": "1"}).json
        self.assertTrue(stale["can_start"])
        self.assertEqual(changed["description"], stale["task"]["description"])
        self.client.post(self.base + "/" + task["id"] + "/state", json={"status": "closed", "revision": changed["revision"]})
        closed = self.get(task["id"])
        for version in ("1", "999"):
            result = self.client.get(endpoint, query_string={"config_version": version}).json
            self.assertFalse(result["can_start"])
            self.assertEqual("closed", result["reason"])
        self.assertEqual(closed, self.get(task["id"]))

    def test_udas_has_no_robot_configuration(self):
        response = self.client.post(self.base, json=self.payload(source="udas", mode="DAGGER", checkpoint="9001",
                                    location="北京采集场", prompt_ids=[collection.PROMPTS[0]["id"]], generalization=[{"invalid": True}]))
        self.assertEqual(201, response.status_code)
        task = response.json["task"]
        self.assertEqual(("", "", [], []), (task["mode"], task["checkpoint"], task["prompts"], task["generalization"]))
        self.assertEqual("北京采集场", task["location"])

    def test_dagger_requires_resolved_prompt_and_cached_checkpoint(self):
        invalid = self.client.post(self.base, json=self.payload(mode="DAGGER"))
        self.assertEqual(422, invalid.status_code)
        self.assertTrue({"prompts", "checkpoint"}.issubset(invalid.json["errors"]))
        invalid = self.client.post(self.base, json=self.payload(mode="DAGGER", prompt_ids=["missing"], checkpoint="9002"))
        self.assertEqual(422, invalid.status_code)
        response = self.client.post(self.base, json=self.payload(mode="DAGGER", prompt_ids=[collection.PROMPTS[0]["id"]], checkpoint="9001"))
        self.assertEqual(201, response.status_code)
        self.assertEqual(collection.PROMPTS[0], response.json["task"]["prompts"][0])

    def test_close_and_reopen_preserve_all_recording_facts(self):
        original = self.get("DC-2602")
        for status in ("closed", "open"):
            current = self.get("DC-2602")
            response = self.client.post(self.base + "/DC-2602/state", json={"status": status, "revision": current["revision"]})
            self.assertEqual(200, response.status_code)
            updated = response.json["task"]
            self.assertEqual(status, updated["status"])
            self.assertEqual(original["records"], updated["records"])
            self.assertEqual(original["metrics"]["uploaded"], updated["metrics"]["uploaded"])
            self.assertNotIn("config_version", updated)

    def test_recorded_task_cannot_change_source_or_mode(self):
        original = self.get("DC-2602")
        response = self.update_config(original, source="udas")
        self.assertEqual(422, response.status_code)
        self.assertIn("source", response.json["errors"])
        response = self.update_config(original, mode="NORMAL")
        self.assertEqual(422, response.status_code)
        self.assertEqual(original, self.get(original["id"]))

    def test_unchanged_save_preserves_entire_task_in_all_modes(self):
        for task_id in ("DC-2601", "DC-2602", "DC-2607"):
            with self.subTest(task_id=task_id):
                original = self.get(task_id)
                for _ in range(2):
                    response = self.update_config(original)
                    self.assertEqual(200, response.status_code)
                    self.assertTrue(response.json["unchanged"])
                    self.assertEqual(original, response.json["task"])
                    self.assertEqual(original, self.get(task_id))

    def test_normalized_equivalent_save_does_not_create_log(self):
        original = self.get("DC-2601")
        response = self.update_config(original, name="  " + original["name"] + "  ",
                                      description=original["description"] + "\n  ",
                                      tags=original["tags"] * 2)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json["unchanged"])
        self.assertEqual(original, self.get(original["id"]))

    def test_immutable_fields_are_locked_before_any_recording(self):
        task = self.client.post(self.base, json=self.payload(mode="DAGGER",
            checkpoint="9001", prompt_ids=[collection.PROMPTS[0]["id"]])).json["task"]
        self.assertEqual([], task["records"])
        for change in ({"name":"新名称"}, {"project":"other"}, {"source":"udas"},
                       {"mode":"NORMAL"}, {"location":"新地点"}, {"checkpoint":"9002"},
                       {"prompt_ids":[collection.PROMPTS[1]["id"]]}, {"prompts":[]}, {"status":"closed"}):
            with self.subTest(change=change):
                response = self.update_config(task, **change)
                self.assertEqual(422, response.status_code)
                self.assertEqual(task, self.get(task["id"]))

    def test_partial_edit_accepts_requirements_and_registers_spec(self):
        task = self.get("DC-2601")
        g = dict(name="放杯位置", prompt_id="", arm="left", event="close",
                 operator=collection.OPERATORS[0]["id"], plane="XY",
                 bounds={"X":[-.3,.3],"Y":[0,.5]}, allow_adjust=True)
        changes = dict(description="更新说明", spec_url="https://example.feishu.cn/docx/spec",
                       tags=["补采"], generalization=[g])
        response = self.client.patch(self.base+"/"+task["id"], json={**changes,"revision":task["revision"]})
        self.assertEqual(200, response.status_code)
        updated = response.json["task"]
        for key, value in changes.items():
            self.assertEqual(value, updated[key])
        for key in ("name","project","source","mode","location","prompts","checkpoint","records","status"):
            self.assertEqual(task[key], updated[key])
        self.assertNotIn("config_version", updated)
        self.assertNotIn("config_history", updated)
        changes_by_field = {c["field"]: c for c in updated["events"][-1]["changes"]}
        self.assertEqual(set(changes) | {'spec_name'}, set(changes_by_field))
        for field, change in changes_by_field.items():
            self.assertEqual(task[field], change["before"])
            self.assertEqual(updated[field], change["after"])

    def test_edit_preserves_bound_prompt_snapshot_when_catalog_changes(self):
        task = self.get("DC-2602")
        previous_prompts = collection.PROMPTS
        previous_checkpoints = self.app.config["COLLECTION_CHECKPOINTS"]
        try:
            collection.PROMPTS = []
            self.app.config["COLLECTION_CHECKPOINTS"] = []
            response = self.client.patch(self.base+"/"+task["id"],
                json={"description":"只更新任务说明","revision":task["revision"]})
            self.assertEqual(200, response.status_code)
            self.assertEqual(task["prompts"], response.json["task"]["prompts"])
            self.assertEqual(task["checkpoint"], response.json["task"]["checkpoint"])
        finally:
            collection.PROMPTS = previous_prompts
            self.app.config["COLLECTION_CHECKPOINTS"] = previous_checkpoints

    def test_copy_can_choose_new_immutable_values(self):
        original = self.get("DC-2601")
        response = self.client.post(self.base, json=self.payload(name="复制后自定义名称"))
        self.assertEqual(201, response.status_code)
        self.assertEqual("复制后自定义名称", response.json["task"]["name"])
        self.assertNotEqual(original["id"], response.json["task"]["id"])

    def test_unchanged_save_after_change_keeps_logs_and_concurrent_edit_check(self):
        original = self.get("DC-2602")
        changed = self.update_config(original, description="更新后的采集要求").json["task"]
        self.assertEqual(original["revision"] + 1, changed["revision"])
        self.assertEqual(len(original["events"]) + 1, len(changed["events"]))
        self.assertNotIn("config_history", changed)
        response = self.update_config(changed)
        self.assertTrue(response.json["unchanged"])
        self.assertEqual(changed, self.get(changed["id"]))
        stale = dict(changed, revision=original["revision"])
        self.assertEqual(409, self.update_config(stale).status_code)
        self.assertEqual(changed, self.get(changed["id"]))

    def test_edit_records_who_when_and_before_after_without_versions(self):
        original = self.get("DC-2602")
        response = self.update_config(original, description="更新后的动作要求")
        self.assertEqual(200, response.status_code)
        updated = response.json["task"]
        self.assertNotIn("config_version", updated)
        self.assertNotIn("config_history", updated)
        event = updated["events"][-1]
        self.assertEqual(collection.USER, event["actor"])
        self.assertEqual(updated["updated_at"], event["at"])
        self.assertEqual("更新采集任务", event["title"])
        self.assertEqual("已更新：任务说明", event["detail"])
        self.assertEqual([{"field": "description", "label": "任务说明", "before": original["description"], "after": "更新后的动作要求"}], event["changes"])
        self.assertEqual(original["records"], updated["records"])
        self.assertTrue(all("config_version" not in r for r in updated["records"]))

    def test_legacy_versions_are_inert_and_hidden_without_rewriting_stored_history(self):
        task = self.get("02602")
        history = [{"version": 1, "config": {"description": "旧要求"}}]
        with closing(sqlite3.connect(self.app.config["COLLECTION_DEMO_DB"])) as conn, conn:
            payload = json.loads(conn.execute("SELECT payload FROM collection_tasks WHERE id=?", (task["id"],)).fetchone()[0])
            payload["config_version"] = 2
            payload["config_history"] = history
            payload["records"][0]["config_version"] = 1
            conn.execute("UPDATE collection_tasks SET payload=? WHERE id=?", (json.dumps(payload), task["id"]))
        updated = self.update_config(task, description="只记录日志").json["task"]
        self.assertNotIn("config_version", updated)
        self.assertNotIn("config_history", updated)
        self.assertNotIn("config_version", updated["records"][0])
        with closing(sqlite3.connect(self.app.config["COLLECTION_DEMO_DB"])) as conn:
            stored = json.loads(conn.execute("SELECT payload FROM collection_tasks WHERE id=?", (task["id"],)).fetchone()[0])
        self.assertEqual(2, stored["config_version"])
        self.assertEqual(history, stored["config_history"])
        self.assertEqual(1, stored["records"][0]["config_version"])

    def test_stale_revision_is_rejected(self):
        original = self.get("DC-2601")
        self.client.post(self.base + "/DC-2601/state", json={"status": "closed", "revision": original["revision"]})
        conflict = self.update_config(original, name="不得覆盖较新数据")
        self.assertEqual(409, conflict.status_code)
        self.assertEqual(original["name"], self.get("DC-2601")["name"])

    def test_metrics_use_uploaded_records_and_actual_latest(self):
        for task in self.client.get(self.base).json["tasks"]:
            records = self.get(task["id"])["records"]
            uploaded = [r for r in records if r["upload"] == "uploaded"]
            self.assertEqual(len(uploaded), task["metrics"]["uploaded"])
            self.assertEqual(sum(r["seconds"] for r in uploaded), task["metrics"]["seconds"])
            self.assertEqual(sum(r["upload"] == "uploading" for r in records), task["metrics"]["uploading"])
            self.assertEqual(sum(r["upload"] == "failed" for r in records), task["metrics"]["upload_failed"])
            self.assertEqual(len(uploaded), sum(task["metrics"][k] for k in ("pending", "processing", "passed", "rejected")))
            self.assertEqual(max((r["recorded_at"] for r in records), default=None), task["metrics"]["latest"])
        self.assertTrue(self.get("DC-2603")["metrics"]["needs_review"])
        self.assertFalse(self.get("DC-2606")["metrics"]["needs_review"])

    def test_generalization_operator_bounds_and_prompt_ownership(self):
        g = dict(name="放杯位置", prompt_id="", arm="left", event="close", operator=collection.OPERATORS[0]["id"],
                 plane="XY", bounds={"X": [-.3, .3], "Y": [0, .5]}, allow_adjust=True)
        self.assertEqual(201, self.client.post(self.base, json=self.payload(generalization=[g])).status_code)
        for change in ({"operator": collection.OPERATORS[1]["id"]}, {"bounds": {"X": [1, 0], "Y": [0, 1]}}, {"bounds": {"X": [0, 1]}}):
            invalid = {**g, **change}
            self.assertEqual(422, self.client.post(self.base, json=self.payload(generalization=[invalid])).status_code)
        g["prompt_id"] = collection.PROMPTS[0]["id"]
        self.assertEqual(422, self.client.post(self.base, json=self.payload(mode="DAGGER", checkpoint="9001", prompt_ids=[g["prompt_id"]], generalization=[g, g])).status_code)

    def test_input_validation_and_missing_tasks(self):
        for url in ("javascript:alert(1)", "https://u:p@example.com/x", "not-a-url"):
            self.assertEqual(422, self.client.post(self.base, json=self.payload(spec_url=url)).status_code)
        for value in (None, [], "bad", 1):
            self.assertEqual(422, self.client.post(self.base, json=value).status_code)
        self.assertEqual(422, self.client.post(self.base, json=self.payload(name="", project="missing")).status_code)
        self.assertEqual(404, self.client.get(self.base + "/not-found").status_code)
        self.assertIn("error", self.client.get(self.base + "/not-found").json)

    def test_invalid_state_is_not_persisted(self):
        original = self.get("DC-2601")
        response = self.client.post(self.base + "/DC-2601/state", json={"status": "complete", "revision": original["revision"]})
        self.assertEqual(422, response.status_code)
        self.assertEqual(original, self.get("DC-2601"))


    def admit(self, task, record_id="ADMITTED-001", **fields):
        return self.client.post(self.base + "/" + task["id"] + "/recordings/start",
                                json={"record_id": record_id, "operator": "tina", "device": "MOZ1-001", **fields})

    def upload(self, task, record_id="ADMITTED-001", failed=False, **fields):
        return self.client.post(self.base + "/" + task["id"] + "/recordings/" + record_id +
                                ("/upload-failed" if failed else "/upload-complete"), json=fields)

    def test_inflight_upload_completes_after_close_without_reopening(self):
        task = self.client.post(self.base, json=self.payload()).json["task"]
        started = self.admit(task)
        self.assertEqual(201, started.status_code)
        self.assertEqual(1, started.json["task"]["metrics"]["uploading"])
        closed = self.client.post(self.base + "/" + task["id"] + "/state",
                                 json={"status": "closed", "revision": task["revision"]}).json["task"]
        completed = self.upload(task, seconds=3600, collection_result="failure")
        self.assertEqual(200, completed.status_code)
        updated = completed.json["task"]
        self.assertEqual(("closed", 1, 0, 3600),
                         (updated["status"], updated["metrics"]["uploaded"], updated["metrics"]["uploading"], updated["metrics"]["seconds"]))
        self.assertEqual(closed["revision"], updated["revision"])
        self.assertEqual(closed["events"], updated["events"])
        self.assertEqual("failure", updated["records"][0]["collection_result"])

    def test_closed_task_rejects_backdated_new_record_and_unknown_completion(self):
        task = self.client.post(self.base, json=self.payload()).json["task"]
        self.client.post(self.base + "/" + task["id"] + "/state", json={"status": "closed", "revision": task["revision"]})
        rejected = self.admit(task, recorded_at="2020-01-01T00:00:00")
        self.assertEqual(409, rejected.status_code)
        self.assertEqual("task_closed", rejected.json["code"])
        self.assertEqual(404, self.upload(task, recorded_at="2020-01-01T00:00:00").status_code)
        self.assertEqual([], self.get(task["id"])["records"])

    def test_failed_upload_is_independent_and_can_recover_after_close(self):
        task = self.client.post(self.base, json=self.payload()).json["task"]
        self.admit(task, seconds=123)
        failed = self.upload(task, failed=True, error="网络中断 <连接重置>").json["task"]
        self.assertEqual((0, 0, 1, 0), tuple(failed["metrics"][k] for k in ("uploaded", "uploading", "upload_failed", "seconds")))
        self.assertIsNone(failed["records"][0]["collection_result"])
        self.client.post(self.base + "/" + task["id"] + "/state", json={"status": "closed", "revision": task["revision"]})
        recovered = self.upload(task, seconds=123).json["task"]
        self.assertEqual(("closed", 1, 0, 123), (recovered["status"], recovered["metrics"]["uploaded"], recovered["metrics"]["upload_failed"], recovered["metrics"]["seconds"]))
        self.assertNotIn("upload_error", recovered["records"][0])

    def test_upload_retry_is_idempotent_and_late_failure_cannot_downgrade(self):
        task = self.client.post(self.base, json=self.payload()).json["task"]
        self.admit(task)
        uploaded = self.upload(task, seconds=80, collection_result="success").json["task"]
        for changes in ({"seconds": 900}, {"failed": True, "error": "迟到的失败回执"}):
            retry = self.upload(task, **changes)
            self.assertTrue(retry.json["replayed"])
            self.assertEqual(uploaded, retry.json["task"])

    def test_start_retry_after_close_recovers_session_but_identity_conflict_fails(self):
        task = self.client.post(self.base, json=self.payload()).json["task"]
        started = self.admit(task).json["recording"]
        self.client.post(self.base + "/" + task["id"] + "/state", json={"status": "closed", "revision": task["revision"]})
        replay = self.admit(task)
        self.assertEqual(200, replay.status_code)
        self.assertEqual(started, replay.json["recording"])
        self.assertEqual(409, self.admit(task, device="OTHER-DEVICE").status_code)
        self.assertEqual(1, len(self.get(task["id"])["records"]))

    def test_recording_validation_and_multiple_prompt_attribution(self):
        task = self.client.post(self.base, json=self.payload(mode="DAGGER", checkpoint="9001",
            prompt_ids=[p["id"] for p in collection.PROMPTS[:2]])).json["task"]
        for fields in ({"record_id": "a/b"}, {"record_id": "a#b"}, {"seconds": -1},
                       {"recorded_at": "invalid"}, {"recorded_at": "2999-01-01T00:00:00"},
                       {"prompt_id": "not-bound"}, {}):
            self.assertEqual(422, self.admit(task, **fields).status_code, fields)
        actual = collection.PROMPTS[1]
        started = self.admit(task, prompt_id=actual["id"])
        self.assertEqual(201, started.status_code)
        self.assertEqual(actual, started.json["recording"]["prompt"])
        self.assertEqual("9001", started.json["recording"]["checkpoint"])
        self.assertEqual(422, self.upload(task, seconds=-10).status_code)
        self.assertEqual(422, self.upload(task, collection_result="unknown").status_code)
        self.assertEqual(422, self.upload(task, failed=True, error="x" * 501).status_code)
        self.assertEqual("uploading", self.get(task["id"])["records"][0]["upload"])

    def test_concurrent_start_close_and_completion_never_loses_facts(self):
        task = self.client.post(self.base, json=self.payload()).json["task"]
        self.admit(task)
        def complete(_):
            with self.app.test_client() as client:
                return client.post(self.base + "/" + task["id"] + "/recordings/ADMITTED-001/upload-complete", json={"seconds": 100}).status_code
        def close():
            with self.app.test_client() as client:
                return client.post(self.base + "/" + task["id"] + "/state", json={"status": "closed", "revision": task["revision"]}).status_code
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(complete, i) for i in range(6)] + [pool.submit(close)]
            self.assertTrue(all(f.result() == 200 for f in futures))
        updated = self.get(task["id"])
        self.assertEqual(("closed", 1, 100, 1), (updated["status"], updated["metrics"]["uploaded"], updated["metrics"]["seconds"], len(updated["records"])))

    def test_legacy_inflight_record_can_complete_after_close(self):
        task = self.get("02602")
        record = next(r for r in task["records"] if r["upload"] == "uploading")
        self.client.post(self.base + "/" + task["id"] + "/state", json={"status": "closed", "revision": task["revision"]})
        response = self.upload(task, record_id=record["id"])
        self.assertEqual(200, response.status_code)
        self.assertEqual("closed", response.json["task"]["status"])
        self.assertEqual(task["metrics"]["uploaded"] + 1, response.json["task"]["metrics"]["uploaded"])


class CollectionPortalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import toolchain_demo
        cls.portal = toolchain_demo.app
        cls.directory = tempfile.TemporaryDirectory(prefix="quanta-collection-portal-")
        cls.previous_database = cls.portal.config["COLLECTION_DEMO_DB"]
        cls.portal.config["COLLECTION_DEMO_DB"] = str(Path(cls.directory.name) / "collection.sqlite3")
        cls.client = cls.portal.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.portal.config["COLLECTION_DEMO_DB"] = cls.previous_database
        cls.directory.cleanup()

    def test_shared_shell_and_all_new_page_routes(self):
        for path in (collection.BASE, collection.BASE + "/new", collection.BASE + "/02602", collection.BASE + "/02602/edit"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(200, response.status_code)
                html = response.get_data(as_text=True)
                self.assertIn('class="q-sider"', html)
                self.assertIn('id="dc-bootstrap"', html)
                self.assertIn('/static/post_training_collection/collection.js', html)
        self.assertEqual(404, self.client.get(collection.BASE + "/not-found").status_code)

    def test_new_navigation_is_registered_once(self):
        import data_platform_refactor as architecture
        self.assertEqual([], architecture.validate_architecture())
        keys = [key for _, group in architecture.NAV_GROUPS for key in group]
        self.assertEqual(1, keys.count("post_training_collection"))
        self.assertTrue(architecture.PAGE_SPECS["post_training_collection"]["custom_view"])
        self.assertEqual("S028", architecture.PAGE_SPECS["post_training_collection"]["nav_badge"])

    def test_existing_collection_pages_remain_available(self):
        for path in ("/data/instruction-management", "/data/instruction-packages", "/data/collection-plans", "/data/recordings"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(200, response.status_code)
                self.assertNotIn('id="dc-app"', response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
