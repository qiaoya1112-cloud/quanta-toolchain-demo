import io
import os
import sqlite3
import tempfile
import time
import unittest
import zipfile
from copy import deepcopy

from bs4 import BeautifulSoup

import data_platform as dp
import third_party_imports
import toolchain_demo


def sample_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("meta/info.json", '{"codebase_version":"v2.1"}')
    buffer.seek(0)
    return buffer


def mapped_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("meta/info.json", '{"codebase_version":"v2.1","fps":25,"robot_type":"test-arm"}')
        archive.writestr("meta/tasks.jsonl", '{"task_index":0,"task":"Place the cup"}\n')
        archive.writestr("meta/episodes.jsonl",
                         '{"episode_index":0,"length":250,"task_index":0,"tags":["抓取"],'
                         '"lowlevel_prompt":"Reach cup","quality_result":"合格"}\n')
        for camera in ("cam_high", "cam_left_wrist", "cam_right_wrist"):
            archive.writestr(f"videos/chunk-000/{camera}/episode_000000.mp4", camera.encode())
    buffer.seek(0)
    return buffer


class ThirdPartyImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_db = dp.app.config.get("THIRD_PARTY_DB")
        dp.app.config["THIRD_PARTY_DB"] = os.path.join(self.temp.name, "imports.sqlite3")
        self.datasets = deepcopy(dp.DATASETS)
        self.versions = deepcopy(dp.DS_VERSIONS)
        self.folders = deepcopy(dp.V2_FOLDER_MAP)
        self.client = toolchain_demo.app.test_client()

    def tearDown(self):
        dp.DATASETS[:] = self.datasets
        dp.DS_VERSIONS.clear()
        dp.DS_VERSIONS.update(self.versions)
        dp.V2_FOLDER_MAP.clear()
        dp.V2_FOLDER_MAP.update(self.folders)
        if self.previous_db is None:
            dp.app.config.pop("THIRD_PARTY_DB", None)
        else:
            dp.app.config["THIRD_PARTY_DB"] = self.previous_db
        self.temp.cleanup()

    def submit(self, file, source="Example Source", dataset="example_dataset", ident="example_dataset"):
        return self.client.post("/model/data/raw/import", data={
            "source_name": source, "dataset_ident": ident, "dataset_name": dataset,
            "folder": "预训练", "format": "LeRobort", "file": (file, "example.zip"),
        }, content_type="multipart/form-data")

    def submit_address(self, location, address, suffix):
        return self.client.post("/model/data/raw/import", data={
            "source_name": "Address Source " + suffix,
            "storage_location": location, "storage_address": address,
            "dataset_ident": "address_dataset_" + suffix,
            "dataset_name": "address_dataset_" + suffix,
            "folder": "预训练", "format": "Mozdataset v2",
        })

    def wait_for(self, task_id, status):
        for _ in range(100):
            task = third_party_imports.get_import(dp.third_party_db_path(), task_id)
            if task["status"] == status:
                return task
            time.sleep(.02)
        self.fail(f"task {task_id} did not reach {status}: {task['status']}")

    def test_success_creates_linked_source_and_dataset(self):
        response = self.submit(sample_zip(), dataset="Readable Dataset", ident="example_dataset")
        self.assertEqual(response.status_code, 202)
        result = response.get_json()
        task = self.wait_for(result["task_id"], "done")
        self.assertEqual(task["dataset_ident"], "example_dataset")
        page = self.client.get("/model/data/raw").get_data(as_text=True)
        document = BeautifulSoup(page, "html.parser")
        self.assertEqual(document.select_one(".model-list-title h1").get_text(strip=True), "开源数据")
        self.assertTrue(document.select_one('a.sn-item[href="/model/data/raw"]').get_text(strip=True).endswith("开源数据"))
        self.assertEqual(document.select_one("#rawImportModal .drawer-head h3").get_text(strip=True), "导入开源数据")
        self.assertEqual(document.select_one("#rawImportBtn").get_text(strip=True), "导入开源数据")
        self.assertIsNone(document.select_one("#rawDataType"))
        self.assertIn("Example Source", page)
        self.assertIn('href="/model/data/tasks?task_type=import">查看全部导入记录</a>', page)
        title_actions = document.select_one(".model-list-actions")
        self.assertIn("仅展示导入成功的开源数据", title_actions.get_text())
        self.assertEqual(title_actions.select_one(".third-source-title-copy a").get_text(strip=True),
                         "查看全部导入记录")
        self.assertLess(page.index("仅展示导入成功的开源数据"), page.index("查看全部导入记录"))
        self.assertLess(page.index("查看全部导入记录"), page.index('id="rawImportBtn"'))
        self.assertNotIn("最近导入", page)
        self.assertIn("/model/data/datasets?sel=" + task["dataset_id"], page)
        detail_page = self.client.get("/model/data/raw?source=" + task["source_id"]).get_data(as_text=True)
        self.assertIn("<h3>开源数据详情</h3>", detail_page)
        self.assertNotIn("数据类型", BeautifulSoup(detail_page, "html.parser").select_one("#rawSourceDetail").get_text())
        task_page = self.client.get("/model/data/tasks?task_type=import&task=" + task["id"]).get_data(as_text=True)
        self.assertIn("开源数据导入", task_page)
        self.assertIn(task["id"], task_page)
        dataset_page = self.client.get("/model/data/datasets?sel=" + task["dataset_id"] + "&tab=info").get_data(as_text=True)
        self.assertIn("example_dataset", dataset_page)
        self.assertEqual(dp.get_ds(task["dataset_id"])["ident"], "example_dataset")
        self.assertNotIn("数据类型", BeautifulSoup(dataset_page, "html.parser").select_one("#pane-info").get_text())
        document = BeautifulSoup(dataset_page, "html.parser")
        self.assertIn("暂无数据", document.select_one("#pane-preview").get_text())
        summary = document.select_one("#info_sum")
        self.assertIn(task["file_path"], summary.get_text())
        self.assertIn("开源数据", summary.get_text())
        self.assertIsNotNone(document.select_one("#datasetEditorConfig"))
        publish = self.client.post("/model/data/datasets/" + task["dataset_id"] + "/version/v1/publish")
        self.assertEqual(publish.status_code, 409)

        dp.DATASETS[:] = [dataset for dataset in dp.DATASETS if dataset["id"] != task["dataset_id"]]
        dp.DS_VERSIONS.pop(task["dataset_id"], None)
        restored = self.client.get("/model/data/datasets?sel=" + task["dataset_id"]).get_data(as_text=True)
        self.assertIn(task["dataset_name"], restored)
        self.assertEqual(dp.get_ds(task["dataset_id"])["ident"], "example_dataset")

    def test_mapped_import_populates_dataset_tabs_and_media(self):
        response = self.submit(mapped_zip(), source="Mapped Source", dataset="mapped_dataset", ident="mapped_dataset")
        self.assertEqual(response.status_code, 202)
        task = self.wait_for(response.get_json()["task_id"], "done")
        dataset = dp.get_ds(task["dataset_id"])
        if dataset is None:
            dp.third_party_rows()
            dataset = dp.get_ds(task["dataset_id"])
        self.assertEqual(dataset["episodes"], 1)
        self.assertEqual(dataset["frames"], 250)
        self.assertEqual(dataset["fps"], 25)
        self.assertEqual(dataset["processing_status"], "ready")
        page = self.client.get("/model/data/datasets?sel=" + task["dataset_id"]).get_data(as_text=True)
        document = BeautifulSoup(page, "html.parser")
        self.assertIn("Place the cup", document.select_one("#pane-preview").get_text())
        self.assertNotIn("接近水槽", document.select_one("#pane-preview").get_text())
        preview = document.select_one("#pane-preview")
        self_collected = BeautifulSoup(self.client.get("/model/data/datasets?sel=ds1").get_data(as_text=True),
                                       "html.parser")
        self.assertEqual(preview.select_one(".preview-split").get("class"),
                         self_collected.select_one("#pane-preview .preview-split").get("class"))
        self.assertEqual([tab.get_text(strip=True) for tab in preview.select(".ep-tabs .ep-tab")],
                         [tab.get_text(strip=True) for tab in self_collected.select("#pane-preview .ep-tabs .ep-tab")])
        self.assertEqual([video.get("aria-label") for video in preview.select("#dsv2_tab_traj .camera-cell video")],
                         ["cam_high视频", "cam_left_wrist视频", "cam_right_wrist视频"])
        self.assertFalse(preview.select("#dsv2_tab_traj .cam-label"))
        self.assertEqual(len(preview.select('[data-segment-axis="dsv2"]')), 2)
        self.assertIsNotNone(preview.select_one("#dsv2_tab_anno .anno-table"))
        self.assertIsNotNone(preview.select_one("#dsv2_tab_va"))
        self.assertEqual(len(document.select("#datasetReadView .tabs .tab")), 5)
        summary = document.select_one("#info_sum")
        self.assertEqual([field.get_text(strip=True) for field in summary.select(".dk")],
                         ["名称", "标识", "数据格式", "存储位置", "数据条数", "数据时长", "数据来源"])
        self.assertEqual([field.get_text(strip=True) for field in summary.select(".dv")][4:],
                         ["1", "00:00:10", "开源数据"])
        self.assertIn("片段数 1 个", document.select_one(".dataset-title-stats").get_text(" ", strip=True))
        self.assertIn(task["file_path"], summary.get_text())
        self.assertIn("Place the cup", document.select_one("#pane-compose").get_text())
        version_cells = document.select_one("#pane-version tbody tr").select("td")
        self.assertEqual(version_cells[2].get_text(strip=True), "1")
        self.assertEqual(version_cells[6].get_text(strip=True), "成功")
        config = document.select_one("#datasetEditorConfig").get_text()
        for camera in ("cam_high", "cam_left_wrist", "cam_right_wrist"):
            self.assertIn(camera, config)
        self.assertIn("Place the cup", config)
        self.assertIn("/model/data/datasets/" + task["dataset_id"] + "/media", config)
        for camera in ("cam_high", "cam_left_wrist", "cam_right_wrist"):
            media = self.client.get("/model/data/datasets/" + task["dataset_id"] +
                                    "/media?episode=0&camera=" + camera)
            self.assertEqual(media.status_code, 200)
            self.assertEqual(media.data, camera.encode())
        self.assertEqual(self.client.get("/model/data/datasets/" + task["dataset_id"] +
                                         "/media?episode=0&camera=unknown").status_code, 404)

        dp.DATASETS[:] = [item for item in dp.DATASETS if item["id"] != task["dataset_id"]]
        dp.DS_VERSIONS.pop(task["dataset_id"], None)
        restored = self.client.get("/model/data/datasets?sel=" + task["dataset_id"]).get_data(as_text=True)
        self.assertIn("Place the cup", restored)

    def test_built_in_examples_have_mapped_rows_without_sample_label(self):
        rows = third_party_imports.list_imports(dp.third_party_db_path())
        built_ins = [row for row in rows if row["source_id"] in ("x1", "x2", "x5", "x6")]
        self.assertEqual(len(built_ins), 4)
        self.assertTrue(all(row["episode_count"] == 8 and row["stage"] == "已完成" for row in built_ins))
        page = self.client.get("/model/data/datasets?sel=third_x1").get_data(as_text=True)
        self.assertNotIn("示例映射数据", page)
        self.assertIn("Pick up the block", page)
        self.assertIn("sample://dataset-sample-preview.webm", page)
        document = BeautifulSoup(page, "html.parser")
        self.assertEqual([video.get("aria-label") for video in document.select("#dsv2_tab_traj .camera-cell video")],
                         ["cam_high视频", "cam_left_wrist视频", "cam_right_wrist视频"])
        self.assertFalse(document.select("#dsv2_tab_traj .cam-label"))
        for camera in ("cam_high", "cam_left_wrist", "cam_right_wrist"):
            clip = self.client.get("/model/data/datasets/third_x1/media?episode=0&camera=" + camera)
            self.assertEqual(clip.status_code, 200)
            self.assertEqual(clip.mimetype, "video/webm")
            self.assertGreater(len(clip.data), 1000)
            clip.close()

    def test_failed_import_stays_out_of_source_table_and_retries_with_new_file(self):
        response = self.submit(io.BytesIO(b"not a zip"), source="Broken Source", dataset="broken_dataset")
        self.assertEqual(response.status_code, 202)
        task = self.wait_for(response.get_json()["task_id"], "fail")
        page = self.client.get("/model/data/raw").get_data(as_text=True)
        self.assertNotIn("Broken Source", page)
        self.assertNotIn("broken_dataset</a>", page)
        task_page = self.client.get("/model/data/tasks?task_type=import&task=" + task["id"]).get_data(as_text=True)
        self.assertIn("Broken Source", task_page)
        self.assertIn("更换文件重试", task_page)
        retry = self.client.post("/model/data/tasks/" + task["id"] + "/retry",
                                 data={"file": (sample_zip(), "fixed.zip")},
                                 content_type="multipart/form-data")
        self.assertEqual(retry.status_code, 200)
        finished = self.wait_for(task["id"], "done")
        self.assertEqual(finished["attempts"], 2)
        self.assertEqual(finished["file_name"], "fixed.zip")
        self.assertIn("broken_dataset</a>", self.client.get("/model/data/raw").get_data(as_text=True))

    def test_storage_addresses_create_linked_sources(self):
        page = self.client.get("/model/data/raw").get_data(as_text=True)
        self.assertIn('name="storage_location"', page)
        self.assertIn('name="storage_address"', page)
        ident = BeautifulSoup(page, "html.parser").select_one("#rawDatasetIdent")
        self.assertEqual(ident.get("name"), "dataset_ident")
        self.assertIn("rawDatasetName", ident.get("oninput"))
        self.assertLess(page.index('id="rawDatasetIdent"'), page.index('id="rawDatasetName"'))
        self.assertIn('<option value="Mozdataset v2" selected>', page)
        self.assertNotIn('id="rawImportFile"', page)
        for location, address in (
            ("tos", "tos://bucket/path/to/dataset/"),
            ("vepfs", "/mnt/vepfs01/path/to/dataset/"),
            ("ks3", "ks3://bucket/path/to/dataset/"),
        ):
            with self.subTest(location=location):
                response = self.submit_address(location, address, location)
                self.assertEqual(response.status_code, 202)
                task = self.wait_for(response.get_json()["task_id"], "done")
                self.assertEqual(task["storage_location"], location)
                self.assertEqual(task["file_path"], address)
                source_page = self.client.get("/model/data/raw").get_data(as_text=True)
                self.assertIn(address, source_page)
                dataset_page = self.client.get("/model/data/datasets?sel=" + task["dataset_id"] + "&tab=info").get_data(as_text=True)
                info = BeautifulSoup(dataset_page, "html.parser").select_one("#pane-info")
                self.assertIn(address, info.get_text())
                self.assertIn("开源数据", info.get_text())

    def test_storage_location_must_match_address(self):
        response = self.submit_address("ks3", "tos://bucket/path/to/dataset/", "mismatch")
        self.assertEqual(response.status_code, 400)
        self.assertIn("ks3", response.get_json()["error"])

    def test_source_list_omits_data_type(self):
        page = BeautifulSoup(self.client.get("/model/data/raw").get_data(as_text=True), "html.parser")
        filters = page.select_one(".third-source-filters .q-filter-row")
        self.assertEqual(len(filters.select(":scope > .q-field")), 3)
        self.assertIsNotNone(filters.select_one(":scope > .third-source-filter-actions"))
        self.assertEqual([button.get_text(strip=True) for button in filters.select(".third-source-filter-actions > *")],
                         ["重置", "查询"])
        self.assertEqual([field.get("name") for field in filters.select("input[name], select[name]")],
                         ["id", "name", "creator"])
        self.assertEqual([cell.get_text(strip=True) for cell in page.select("table.ant-table thead th")][:3],
                         ["ID", "数据源名称", "存储位置"])
        filtered = BeautifulSoup(self.client.get("/model/data/raw?id=x1").get_data(as_text=True), "html.parser")
        rows = filtered.select("table.ant-table tbody tr")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].select_one("td").get_text(strip=True), "x1")
        self.assertIsNone(page.select_one("#thirdSourceDataType"))
        self.assertNotIn("数据类型", page.select_one("table.ant-table").get_text())

    def test_dataset_ident_is_required_valid_and_unique(self):
        for ident in ("", "1invalid", "bad space", "a" * 81):
            with self.subTest(ident=ident):
                response = self.client.post("/model/data/raw/import", data={
                    "source_name": "Invalid Ident", "storage_location": "tos",
                    "storage_address": "tos://bucket/path/to/dataset/",
                    "dataset_ident": ident, "dataset_name": "Invalid Dataset",
                    "folder": "预训练", "format": "Mozdataset v2",
                })
                self.assertEqual(response.status_code, 400)
        first = self.submit_address("tos", "tos://bucket/path/to/dataset/", "unique")
        self.assertEqual(first.status_code, 202)
        self.wait_for(first.get_json()["task_id"], "done")
        duplicate = self.submit(sample_zip(), source="Another Source", dataset="Another Dataset",
                                ident="ADDRESS_DATASET_UNIQUE")
        self.assertEqual(duplicate.status_code, 409)
        existing = self.submit(sample_zip(), source="Existing Dataset Source", dataset="New Dataset",
                               ident=dp.DATASETS[0]["id"])
        self.assertEqual(existing.status_code, 409)

    def test_existing_imports_gain_compatible_ident(self):
        with sqlite3.connect(dp.third_party_db_path()) as conn:
            conn.execute("""CREATE TABLE imports (
                id TEXT PRIMARY KEY, source_id TEXT UNIQUE NOT NULL,
                source_name TEXT NOT NULL, dataset_id TEXT UNIQUE NOT NULL,
                dataset_name TEXT NOT NULL, folder TEXT NOT NULL, format TEXT NOT NULL,
                file_name TEXT NOT NULL, file_path TEXT NOT NULL, file_size INTEGER NOT NULL,
                status TEXT NOT NULL, stage TEXT NOT NULL, error TEXT NOT NULL DEFAULT '',
                owner TEXT NOT NULL, created_at TEXT NOT NULL, completed_at TEXT NOT NULL DEFAULT '',
                attempts INTEGER NOT NULL DEFAULT 1, episode_count INTEGER NOT NULL DEFAULT 0
            )""")
            conn.execute("""INSERT INTO imports
                (id, source_id, source_name, dataset_id, dataset_name, folder, format,
                 file_name, file_path, file_size, status, stage, owner, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'done', '已完成', ?, ?)""",
                ("import_legacy", "tp_legacy", "Legacy Source", "third_legacy", "Legacy Dataset",
                 "预训练", "Mozdataset v2", "legacy.zip", "tos://bucket/legacy.zip",
                 "Joanna Qiao", "2026-06-01 09:00:00"))
        task = third_party_imports.get_import(dp.third_party_db_path(), "import_legacy")
        self.assertEqual(task["dataset_ident"], "third_legacy")
        self.assertEqual(task["storage_location"], "tos")


if __name__ == "__main__":
    unittest.main()
