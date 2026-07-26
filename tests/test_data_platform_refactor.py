import re
import unittest

import data_platform_refactor as architecture
import toolchain_demo


FORBIDDEN_QUALITY_GATE_TERMS = (
    "质量门槛",
    "质量门禁",
    "Quality Gate",
    "Quality Result",
    "QualityResult",
    "质量结果",
    "返工管理",
    "规则策略",
    "终验",
    "质检",
    "合格率",
    "误判",
    "抽检",
    "PASS",
    "REVIEW",
    "REJECT",
)

FORBIDDEN_DESIGN_DOCUMENT_TERMS = (
    "产品边界",
    "三个任务对象不能合并",
    "对象边界",
    "项目权限与职责分离",
    "配置与执行分离",
    "生产与发布分离",
    "分配与连续作业协议",
    "运行不变量",
    "稳定数据对象",
    "每条血缘必须回答",
    "三类基础节点",
    "架构成效指标",
    "五层功能架构",
    "领域命令与事件边界",
    "统一审计链路",
    "PRODUCT OBJECT",
    "ARCHITECTURE · FIVE LAYERS",
)


class DataPlatformArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = toolchain_demo.app.test_client()

    @staticmethod
    def visible_html(html):
        return re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.S)

    def test_configuration_invariants(self):
        self.assertEqual([], architecture.validate_architecture())

    def test_navigation_and_page_registry_have_one_source_of_truth(self):
        nav_keys = [key for _, keys in architecture.NAV_GROUPS for key in keys]
        self.assertEqual(set(architecture.PAGE_SPECS), set(nav_keys))
        self.assertEqual(len(nav_keys), len(set(nav_keys)))
        self.assertEqual(12, len(nav_keys))
        paths = [item["path"] for item in architecture.PAGE_SPECS.values()]
        self.assertEqual(len(paths), len(set(paths)))

    def test_all_configured_pages_render_in_shared_portal(self):
        for key, spec in architecture.PAGE_SPECS.items():
            with self.subTest(page=key):
                response = self.client.get(spec["path"])
                self.assertEqual(200, response.status_code)
                html = response.get_data(as_text=True)
                self.assertIn(spec["title"], html)
                self.assertIn("数据平台", html)
                self.assertIn('class="q-sider"', html)

    def test_home_exposes_core_role_tasks_and_active_runs(self):
        html = self.client.get("/data").get_data(as_text=True)
        for expected in (
            "项目 / 数据运营",
            "数据工厂管理员",
            "生产执行人员",
            "算法 / 数据工程师",
            "数据集管理员",
            "平台管理员",
            "run-moz1-0921",
            "run-moz1-0922",
        ):
            self.assertIn(expected, html)

    def test_business_tasks_keep_three_types_separate(self):
        html = self.client.get("/data/tasks").get_data(as_text=True)
        self.assertIn("<h1>任务管理</h1>", html)
        self.assertEqual(3, len(re.findall(r'class="dpr-task-tab(?: active)?"', html)))
        self.assertIn('class="dpr-task-tab active" data-task-type="data_collection_task"', html)
        for expected in (
            "data_collection_task",
            "data_import_task",
            "data_processing_task",
        ):
            self.assertIn(expected, str(architecture.BUSINESS_TASKS))
        for expected in (
            "数据采集 <b>1</b>",
            "数据导入 <b>1</b>",
            "数据处理 <b>3</b>",
            "数据处理 · 标准化",
            "数据处理 · 标注",
            "数据处理 · 数据集构建",
        ):
            self.assertIn(expected, html)

    def test_human_tasks_show_required_runtime_associations(self):
        html = self.client.get("/data/task-pool").get_data(as_text=True)
        for expected in (
            "ht-220976",
            "PROC-2026-0922",
            "run-moz1-0922",
            "nr-0922-ann-127",
            "数据范围 / SOP",
            "优先级 / SLA",
            "锁",
        ):
            self.assertIn(expected, html)

    def test_pipeline_runs_expose_node_runs_and_attempt_history(self):
        html = self.client.get("/data/pipeline-runs").get_data(as_text=True)
        for expected in (
            "nr-0921-split-002",
            "nr-0922-ann-127",
            "nr-0314-build-003",
            "Attempt",
            "执行器版本",
        ):
            self.assertIn(expected, html)

    def test_recordings_keep_source_task_identity(self):
        html = self.client.get("/data/assets").get_data(as_text=True)
        for expected in (
            "recording:4057808@raw",
            "data_collection_task",
            "COL-2026-0718",
            "recording:vendor-12-001@raw",
            "data_import_task",
            "IMP-2026-0042",
        ):
            self.assertIn(expected, html)

    def test_dataset_release_uses_version_integrity_conditions(self):
        html = self.client.get("/data/dataset-versions").get_data(as_text=True)
        for expected in (
            "Data Snapshot 已冻结",
            "版本元数据完整",
            "血缘完整",
            "发布不可变 Dataset Version",
        ):
            self.assertIn(expected, html)

    def test_system_architecture_is_not_a_product_page(self):
        self.assertNotIn("architecture", architecture.PAGE_SPECS)
        response = self.client.get("/data/architecture", follow_redirects=False)
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.headers["Location"].endswith("/data/operations"))

    def test_phase_one_scope_is_represented_end_to_end(self):
        requirements = {
            "/data/projects": (
                "PRJ-MOZ1-SFT-07",
                "本月交付目标",
                "预算使用",
            ),
            "/data/tasks": (
                "数据采集",
                "数据导入",
                "数据处理 · 标准化",
                "数据处理 · 标注",
                "数据处理 · 数据集构建",
                "PROC-2026-0922",
            ),
            "/data/pipeline-definitions": (
                "pv.capture-to-dataset@7",
                "operator",
                "human",
                "gateway",
                "数据集构建",
            ),
            "/data/pipeline-runs": (
                "流程版本",
                "输入快照",
                "幂等键",
                "Node Run",
                "Attempt",
            ),
            "/data/task-pool": (
                "ht-220976",
                "ht-220981",
                "数据范围 / SOP",
                "执行人 / 锁",
                "SLA",
            ),
            "/data/workbench-schemas": (
                "multimodal_viewer",
                "timeline_segment_editor",
                "instruction_context",
                "task_submit",
            ),
            "/data/assets": (
                "Recording",
                "Episode",
                "Annotation Version",
                "Data Snapshot",
                "校验和",
            ),
            "/data/dataset-versions": (
                "Data Snapshot 已冻结",
                "发布不可变 Dataset Version",
                "不可引用",
            ),
            "/data/lineage": (
                "Pipeline Run",
                "Dataset",
                "配置版本覆盖率",
                "dataset.moz1-household@4.0.0",
            ),
            "/data/capabilities": (
                "op.timestamp-align@2.1.0",
                "op.dataset-build@1.2.0",
                "multimodal_viewer",
            ),
            "/data/operations": (
                "端到端交付周期",
                "本周产能",
                "端到端交付漏斗",
            ),
        }
        for path, expected_values in requirements.items():
            html = self.client.get(path).get_data(as_text=True)
            for expected in expected_values:
                with self.subTest(path=path, expected=expected):
                    self.assertIn(expected, html)

    def test_quality_gate_concepts_are_removed_from_product_pages(self):
        retired_pages = {"quality_results", "rework_orders", "policies"}
        self.assertTrue(retired_pages.isdisjoint(architecture.PAGE_SPECS))
        for key, spec in architecture.PAGE_SPECS.items():
            html = self.visible_html(self.client.get(spec["path"]).get_data(as_text=True))
            for term in FORBIDDEN_QUALITY_GATE_TERMS:
                with self.subTest(page=key, term=term):
                    self.assertNotIn(term, html)

    def test_design_documentation_is_removed_from_product_pages(self):
        for key, spec in architecture.PAGE_SPECS.items():
            html = self.visible_html(self.client.get(spec["path"]).get_data(as_text=True))
            for term in FORBIDDEN_DESIGN_DOCUMENT_TERMS:
                with self.subTest(page=key, term=term):
                    self.assertNotIn(term, html)
        home = self.client.get("/data").get_data(as_text=True)
        self.assertNotIn("/data/architecture", home)
        self.assertNotIn("系统架构", home)

    def test_retired_legacy_quality_routes_leave_the_old_product(self):
        redirects = {
            "/data/qc": "/data/tasks",
            "/data/rules": "/data/capabilities",
            "/data/collect": "/data/tasks",
            "/data/recordings": "/data/assets",
            "/data/workbench": "/data/task-pool",
            "/data/dashboard": "/data/operations",
            "/data/process": "/data/pipeline-runs",
            "/data/raw": "/data/assets",
            "/data/operators": "/data/capabilities",
            "/data/pipelines": "/data/pipeline-definitions",
            "/data/pipelines/pl1": "/data/pipeline-definitions",
            "/data/runs": "/data/pipeline-runs",
            "/data/architecture": "/data/operations",
        }
        for old_path, new_path in redirects.items():
            with self.subTest(old_path=old_path):
                response = self.client.get(old_path, follow_redirects=False)
                self.assertEqual(302, response.status_code)
                self.assertTrue(response.headers["Location"].endswith(new_path))

    def test_new_pages_only_link_to_registered_internal_routes(self):
        route_patterns = {str(rule) for rule in toolchain_demo.app.url_map.iter_rules()}
        literal_routes = {route for route in route_patterns if "<" not in route}
        variable_prefixes = {
            route.split("<", 1)[0]
            for route in route_patterns
            if "<" in route
        }
        missing = set()
        for spec in architecture.PAGE_SPECS.values():
            html = self.client.get(spec["path"]).get_data(as_text=True)
            visible_html = self.visible_html(html)
            hrefs = re.findall(r'href="([^"]+)"', visible_html)
            for href in hrefs:
                path = href.split("?", 1)[0]
                if (
                    not path.startswith("/")
                    or path in literal_routes
                    or any(path.startswith(prefix) for prefix in variable_prefixes)
                ):
                    continue
                missing.add(path)
        self.assertEqual(set(), missing)


if __name__ == "__main__":
    unittest.main()
