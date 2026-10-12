import json
import re
import unittest
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from toolchain_demo import app, WB_TASKS, _workbench_pool_rule_names
from urllib.parse import urlencode
from workbench_pool import PRETRAINING_TASKS, transition, pool_records, shared_transition, PoolConflict


class WorkbenchPoolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_db = app.config.get("WORKBENCH_POOL_DB")
        app.config["WORKBENCH_POOL_DB"] = str(Path(self.temp.name) / "pools.sqlite3")
        self.client = app.test_client()
        self.base = "/data/workbench-v2/pools/POOL-PRETRAINING-QC/records"

    def tearDown(self):
        if self.previous_db is None:
            app.config.pop("WORKBENCH_POOL_DB", None)
        else:
            app.config["WORKBENCH_POOL_DB"] = self.previous_db
        self.temp.cleanup()

    def test_other_session_cannot_claim_finish_or_open_occupied_record(self):
        self.records()  # Load the stale list before the other session claims the record.
        other = app.test_client()
        self.assertEqual(200, other.post(self.base + "/actions", json={"action": "start", "ids": ["7523789"]}).status_code)
        response = self.action(action="start", ids=["7523789"])
        self.assertEqual((409, "record_occupied"), (response.status_code, response.json["code"]))
        self.assertIn("其他人", response.json["error"])
        self.assertEqual(409, self.action(action="finish", ids=["7523789"], result="合格").status_code)
        item = next(item for item in self.records() if item["id"] == "7523789")
        self.assertTrue(item["occupied"])
        self.assertNotIn("owner", item)
        url = "/data/workbench-v2/edit?task=WB-PRETRAINING-QC&pool_id=POOL-PRETRAINING-QC&recording_id=7523789"
        self.assertEqual(302, self.client.get(url).status_code)
        self.assertEqual(200, other.get(url).status_code)
        self.assertEqual(200, other.post(self.base + "/actions", json={"action": "start", "ids": ["7523789"]}).status_code)
        self.assertEqual(200, other.post(self.base + "/actions", json={"action": "finish", "ids": ["7523789"], "result": "合格"}).status_code)
        self.assertEqual(409, self.action(action="start", ids=["7523789"]).status_code)

    def test_conflicting_batch_is_atomic(self):
        other = app.test_client()
        other.post(self.base + "/actions", json={"action": "start", "ids": ["7523789"]})
        self.assertEqual(409, self.action(action="start", ids=["7523787", "7523789"]).status_code)
        self.assertEqual("pending", next(item for item in self.records() if item["id"] == "7523787")["status"])

    def test_simultaneous_claim_has_only_one_winner(self):
        path = app.config["WORKBENCH_POOL_DB"]
        def claim(owner):
            try:
                shared_transition(path, PRETRAINING_TASKS[0], {}, owner, "start", ["7523787"])
                return "claimed"
            except PoolConflict:
                return "conflict"
        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(["claimed", "conflict"], sorted(executor.map(claim, ("alice", "bob"))))

    def action(self, **payload):
        return self.client.post(self.base + "/actions", json=payload)

    def records(self, base=None):
        path = base or self.base
        task = next(item for item in WB_TASKS if item["pool"] == path.split("/")[-2])
        response = self.client.get(path + "?" + urlencode({"rule": _workbench_pool_rule_names(task)[0]}))
        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        return json.loads(re.search(r'<script id="wpPayload" type="application/json">(.*?)</script>', html, re.S)[1])["records"]

    def test_entry_and_new_nodes(self):
        html = self.client.get("/data/workbench-v2").get_data(as_text=True)
        table = re.search(r'<table class="ant-table" id="dpr-wb2-pool-table">.*?</table>', html, re.S)[0]
        self.assertEqual(4, table.count("<tr data-flow="))
        for node in ("采集质检", "采集验收"):
            self.assertIn(f'data-flow="预训练数据质检流程" data-node="{node}"', table)
        for pool in ("POOL-PRETRAINING-QC", "POOL-PRETRAINING-ACCEPTANCE", "POOL-E2E-ACCEPTANCE"):
            html = self.client.get("/data/workbench-v2/pools/" + pool).get_data(as_text=True)
            self.assertIn("/pools/" + pool + "/records?source=", html)
            self.assertLess(html.index(">重置</button>"), html.index(">数据列表</a>"))
            if "PRETRAINING" in pool:
                self.assertIn("规则 v1</option>", html)
            task = next(item for item in WB_TASKS if item["pool"] == pool)
            response = self.client.get("/data/workbench-v2/pools/" + pool + "/records?" + urlencode({"rule": _workbench_pool_rule_names(task)[0]}))
            self.assertEqual(200, response.status_code)
            self.assertNotIn("<th>人工质检结论</th>", response.get_data(as_text=True))
            self.assertNotIn("<th>任务状态</th>", response.get_data(as_text=True))

    def test_data_list_requires_a_specific_processing_rule(self):
        self.assertEqual(302, self.client.get(self.base).status_code)
        self.assertEqual(302, self.client.get(self.base + "?rule=invalid").status_code)
        self.records()
        self.assertEqual(200, self.client.get(self.base).status_code)
        self.assertEqual(302, self.client.get(self.base + "?rule=").status_code)

    def test_acceptance_reads_completed_upstream_quality_history(self):
        acceptance = "/data/workbench-v2/pools/POOL-PRETRAINING-ACCEPTANCE/records"
        before = next(item for item in self.records(acceptance) if item['id'] == '7523785')
        self.assertEqual('', before['collection_qc_result'])
        response = self.action(action='finish', ids=['7523785'], result='不合格', reasons=['其他'])
        self.assertEqual(200, response.status_code)
        after = next(item for item in self.records(acceptance) if item['id'] == '7523785')
        self.assertEqual('processing', after['status'])
        self.assertNotIn('result', after)
        self.assertEqual('不合格', after['collection_qc_result'])
        self.assertEqual('李奕冲', after['collection_qc_operator'])
        self.assertEqual('SUP-003', after['collection_qc_supplier_id'])
        self.assertTrue(after['collection_qc_at'])
        response = self.client.post(acceptance + '/actions', json={'action':'start', 'ids':['7523787']})
        self.assertEqual(200, response.status_code)
        self.assertEqual('不合格', next(item for item in response.json['records'] if item['id']=='7523785')['collection_qc_result'])

    def test_batch_start_persists_and_is_sorted(self):
        result = self.action(action="start", ids=["7523788", "7523790"])
        self.assertEqual(200, result.status_code)
        records = self.records()
        self.assertEqual(["processing"] * 4 + ["pending"] * 2, [item["status"] for item in records])
        other = self.records("/data/workbench-v2/pools/POOL-PRETRAINING-ACCEPTANCE/records")
        self.assertEqual(2, sum(item["status"] == "processing" for item in other))

    def test_atomic_validation_and_pending_cannot_finish(self):
        result = self.action(action="start", ids=["7523787", "unknown"])
        self.assertEqual(400, result.status_code)
        self.assertEqual("pending", next(item for item in self.records() if item["id"] == "7523787")["status"])
        for ids in ([], ["7523787", "7523787"], None, [["7523787"]]):
            self.assertEqual(400, self.action(action="start", ids=ids).status_code)
        self.assertEqual(400, self.action(action="finish", ids=["7523787"], result="合格").status_code)

    def test_decision_reason_and_repeat_guard(self):
        for reason, remark in (("", ""), ("bad", "")):
            self.assertEqual(400, self.action(action="finish", ids=["7523785"], result="不合格", reason=reason, remark=remark).status_code)
        result = self.action(action="finish", ids=["7523785"], result="不合格", reason="其他", remark="动作没有完成")
        self.assertEqual(200, result.status_code)
        saved = next(item for item in self.records() if item["id"] == "7523785")
        self.assertEqual(("completed", "不合格", "其他", "动作没有完成"), (saved["status"], saved["result"], saved["reason"], saved["remark"]))
        self.assertEqual(400, self.action(action="finish", ids=["7523785"], result="合格").status_code)
        self.assertEqual(400, self.action(action="start", ids=["7523785"]).status_code)
        result = self.action(action="finish", ids=["7523786"], result="合格")
        self.assertEqual(200, result.status_code)

    def test_multiple_rejection_reasons_are_validated_and_persisted(self):
        for reasons in ([], "其他", ["bad"], ["其他", "其他"], [None], [["其他"]]):
            response = self.action(action="finish", ids=["7523785"], result="不合格", reasons=reasons)
            self.assertEqual(400, response.status_code, reasons)
            self.assertEqual("processing", next(item for item in self.records() if item["id"] == "7523785")["status"])
        reasons = ["画面遮挡或模糊", "其他"]
        response = self.action(action="finish", ids=["7523785"], result="不合格", reasons=reasons)
        self.assertEqual(200, response.status_code)
        saved = next(item for item in self.records() if item["id"] == "7523785")
        self.assertEqual(reasons, saved["reasons"])
        self.assertEqual("", saved["remark"])
        self.assertRegex(saved["reviewed_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\+08:00$")

    def test_editor_is_scoped_to_pool_and_record(self):
        url = "/data/workbench-v2/edit?task=WB-PRETRAINING-QC&pool_id=POOL-PRETRAINING-QC&recording_id="
        self.assertEqual(302, self.client.get(url + "7523787").status_code)
        self.action(action="start", ids=["7523787"])
        html = self.client.get(url + "7523787").get_data(as_text=True)
        for text in ("质检工作台", "7523787", "采集质检"):
            self.assertTrue(text in html, text)
        self.assertEqual(404, self.client.get(url + "unknown").status_code)
        self.assertEqual(404, self.client.get(url.replace("pool_id=POOL-PRETRAINING-QC", "pool_id=POOL-PRETRAINING-ACCEPTANCE") + "7523785").status_code)
        self.assertEqual(404, self.client.get(self.base + "?source=WB-E2E-ACCEPTANCE").status_code)
        self.assertEqual(404, self.client.get("/data/workbench-v2/pools/unknown/records").status_code)

    def test_multiple_nodes_sharing_pool_do_not_share_state(self):
        task = PRETRAINING_TASKS[0]
        saved = transition(task, {}, "finish", ["7523785"], "合格")
        other = dict(task, id="another-node")
        self.assertEqual("processing", pool_records(other, saved)[0]["status"])


if __name__ == "__main__":
    unittest.main()
