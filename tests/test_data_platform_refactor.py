import re
import unittest

import data_platform
import data_platform_refactor as architecture
import toolchain_demo


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

    def test_navigation_matches_target_information_architecture(self):
        expected_groups = [
            (
                "任务管理",
                [
                    "collection_tasks",
                    "processing_tasks",
                    "allocation_management",
                ],
            ),
            ("数据资产", ["data_management", "dataset_management"]),
            ("工作台", ["workbench", "personal_dashboard"]),
            (
                "工作流",
                [
                    "workflow_management",
                    "execution_records",
                    "operator_management",
                    "workbench_management",
                ],
            ),
            (
                "配置管理",
                [
                    "project_management",
                    "rule_management",
                    "scene_management",
                    "tag_management",
                ],
            ),
            (
                "运营管理",
                [
                    "supplier_management",
                    "personnel_management",
                    "permission_management",
                ],
            ),
        ]
        self.assertEqual(expected_groups, architecture.NAV_GROUPS)

        nav_keys = [key for _, keys in architecture.NAV_GROUPS for key in keys]
        self.assertEqual(set(architecture.PAGE_SPECS), set(nav_keys))
        self.assertEqual(18, len(nav_keys))
        self.assertEqual(len(nav_keys), len(set(nav_keys)))
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

    def test_data_root_opens_collection_tasks(self):
        response = self.client.get("/data", follow_redirects=False)
        self.assertEqual(302, response.status_code)
        self.assertTrue(
            response.headers["Location"].endswith("/data/collection-tasks")
        )

    def test_collection_tasks_match_table_definition(self):
        html = self.client.get("/data/collection-tasks").get_data(as_text=True)
        self.assertIn("<h1>采集任务</h1>", html)
        self.assertEqual(3, len(re.findall(r'class="dpr-task-tab(?: active)?"', html)))
        self.assertIn(
            'class="dpr-task-tab active" data-task-mode="instruction"',
            html,
        )
        for expected in (
            "指令采集 <b>2</b>",
            "自由采集 <b>2</b>",
            "DAgger 采集 <b>1</b>",
            "<label>任务 ID</label>",
            "<label>名称</label>",
            "<label>类型</label>",
            "<label>操作人</label>",
            "<th>任务 ID</th>",
            "<th>名称</th>",
            "<th>类型</th>",
            "<th>进度</th>",
            "<th>优先级</th>",
            "<th>操作人</th>",
            "<th>创建人</th>",
            "<th>创建时间</th>",
            'href="/data/tasks/COL-2026-0718"',
            ">数据</a>",
            "dprOpenCollectionTaskDrawer('detail', this)",
            "dprOpenCollectionTaskDrawer('edit', this)",
            ">详情</button>",
            ">编辑</button>",
        ):
            self.assertIn(expected, html)
        task_table = re.search(
            r'<table class="dpr-table" id="dpr-collection-task-table">.*?</table>',
            html,
            flags=re.S,
        )
        self.assertIsNotNone(task_table)
        self.assertNotIn("PROC-2026-0922", task_table.group(0))

    def test_new_collection_task_uses_required_side_drawer_fields(self):
        html = self.client.get("/data/collection-tasks").get_data(as_text=True)
        for expected in (
            "dprOpenCollectionTaskDrawer('new')",
            'class="drawer dpr-collection-drawer" id="drawerCollectionTaskForm"',
            'id="collectionTaskDrawerTitle">新建采集任务</h3>',
            "'采集任务详情'",
            "'编辑采集任务'",
            ">任务名称</label>",
            ">采集类型</label>",
            "处理任务 <span",
            "（可选，选择则流式流转）",
            ">所属项目</label>",
            ">优先级</label>",
            "<option>指令采集</option>",
            "<option>自由采集</option>",
            "<option>DAgger 采集</option>",
            "<option>预训练采集</option>",
            "<option>demo 项目</option>",
            "<option>宁德项目</option>",
            "不关联处理任务",
            "选择后，采集产生的数据将持续流转到对应处理任务。",
        ):
            self.assertIn(expected, html)
        self.assertNotIn("预期交付日期</label>", html)
        self.assertNotIn("采集 SOP 说明</label>", html)
        drawer_start = html.index('id="drawerCollectionTaskForm"')
        drawer_html = html[drawer_start:]
        field_positions = [
            drawer_html.index(f'name="{field}"')
            for field in (
                "task_name",
                "collection_type",
                "project",
                "priority",
                "processing_task",
            )
        ]
        self.assertEqual(sorted(field_positions), field_positions)

    def test_processing_tasks_match_table_definition(self):
        html = self.client.get("/data/processing-tasks").get_data(as_text=True)
        self.assertIn("<h1>处理任务</h1>", html)
        self.assertEqual(3, len(re.findall(r'class="dpr-task-tab(?: active)?"', html)))
        self.assertIn(
            'class="dpr-task-tab active" data-processing-stage="cleaning"',
            html,
        )
        for expected in (
            "质检环节 <b>1</b>",
            "标注环节 <b>1</b>",
            "验收环节 <b>1</b>",
            "<label>任务 ID</label>",
            "<label>名称</label>",
            "<label>流程</label>",
            "<label>节点</label>",
            "<label>操作人</label>",
            "<th>任务 ID</th>",
            "<th>名称</th>",
            "<th>流程</th>",
            "<th>节点</th>",
            "<th>进度</th>",
            "<th>优先级</th>",
            "<th>操作人</th>",
            "<th>创建人</th>",
            "<th>创建时间</th>",
            "多级复核数据处理流程",
            "双轮人工数据处理流程",
            'href="/data/tasks/PROC-2026-0922"',
            ">数据</a>",
            "dprOpenProcessingTaskDrawer('detail', this)",
            "dprOpenProcessingTaskDrawer('edit', this)",
            ">详情</button>",
            ">编辑</button>",
        ):
            self.assertIn(expected, html)
        self.assertEqual(3, html.count('class="dpr-task-progress-stack"'))
        self.assertEqual(9, html.count('class="dpr-task-progress-line"'))
        self.assertNotIn("dpr-task-progress-copy", html)
        self.assertRegex(
            html,
            r'<div class="dpr-task-progress-line">\s*'
            r'<i class="(?:blue|teal|green)" style="width:\d+%"></i>\s*'
            r"<b>[\d,]+ / [\d,]+ · \d+%</b>",
        )
        for stage in ("质检", "标注", "验收"):
            self.assertEqual(
                3,
                html.count(f'data-progress-stage="{stage}"'),
            )
        self.assertNotIn("COL-2026-0718", html)

    def test_new_processing_task_uses_required_side_drawer_fields(self):
        html = self.client.get("/data/processing-tasks").get_data(as_text=True)
        for expected in (
            "dprOpenProcessingTaskDrawer('new')",
            'id="drawerProcessingTaskForm"',
            'id="processingTaskDrawerTitle">新建处理任务</h3>',
            "'处理任务详情'",
            "'编辑处理任务'",
            ">任务名称</label>",
            ">所属项目</label>",
            ">优先级</label>",
            ">处理流程（绑定工作流）</label>",
            "<option>预训练采集</option>",
            "<option>demo 项目</option>",
            "<option>宁德项目</option>",
            "<option>多级复核数据处理流程</option>",
            "<option>双轮人工数据处理流程</option>",
            "<option>标准训练数据流水线</option>",
            "<option>DAgger 数据流水线</option>",
            "人工节点分配",
            "分配方式",
            "供应商",
            "操作员",
            "分配对象",
            "比例",
            "添加分配对象",
            "dprRenderProcessingAssignments",
            "dprSetNodeAssignmentMode",
            "每个人工节点的分配比例需合计 100%",
        ):
            self.assertIn(expected, html)
        drawer_start = html.index('id="drawerProcessingTaskForm"')
        drawer_html = html[drawer_start:]
        field_positions = [
            drawer_html.index(f'name="{field}"')
            for field in ("task_name", "project", "priority", "workflow")
        ]
        self.assertEqual(sorted(field_positions), field_positions)
        self.assertEqual(
            7,
            len(
                architecture.PROCESSING_FLOW_HUMAN_NODES[
                    "多级复核数据处理流程"
                ]
            ),
        )
        self.assertEqual(
            5,
            len(
                architecture.PROCESSING_FLOW_HUMAN_NODES[
                    "双轮人工数据处理流程"
                ]
            ),
        )
        self.assertEqual(
            [],
            architecture.PROCESSING_FLOW_HUMAN_NODES[
                "标准训练数据流水线"
            ],
        )

    def test_task_detail_pages_preserve_record_list_views(self):
        collection = self.client.get("/data/tasks/COL-2026-0718")
        self.assertEqual(200, collection.status_code)
        collection_html = collection.get_data(as_text=True)
        for expected in (
            "厨房狭窄台面补采",
            "recording_id",
            "4057808",
            "三路采集视频",
            "ID 搜索",
            "设备序列号",
            "上传状态",
            "采集结论",
        ):
            self.assertIn(expected, collection_html)
        collection_table_head = re.search(
            r'<table class="ant-table dpr-record-table dpr-collection-record-table">'
            r"\s*<thead><tr>(.*?)</tr></thead>",
            collection_html,
            flags=re.S,
        )
        self.assertIsNotNone(collection_table_head)
        self.assertEqual(
            [
                "recording_id",
                "视频",
                "设备序列号",
                "上传状态",
                "采集结论",
                "操作人",
            ],
            re.findall(r"<th>(.*?)</th>", collection_table_head.group(1)),
        )
        self.assertIn(
            ".table-wrap.dpr-record-table-wrap{width:100%;max-width:100%;min-width:0;overflow-x:auto;",
            collection_html,
        )
        for removed_layout in (
            '<div class="dpr-metrics">',
            "最近采集数据",
            "采集进度</h2>",
        ):
            self.assertNotIn(removed_layout, collection_html)

        processing = self.client.get("/data/tasks/PROC-2026-0922")
        self.assertEqual(200, processing.status_code)
        processing_html = processing.get_data(as_text=True)
        for expected in (
            "家居动作分段标注",
            "recording_id",
            "处理环节",
            "质检结论",
            "标注状态",
            "验收状态",
            "4057761",
            "标注：供应商 A",
        ):
            self.assertIn(expected, processing_html)
        processing_table_head = re.search(
            r'<table class="ant-table dpr-record-table">'
            r"\s*<thead><tr>(.*?)</tr></thead>",
            processing_html,
            flags=re.S,
        )
        self.assertIsNotNone(processing_table_head)
        self.assertEqual(
            [
                "recording_id",
                "视频",
                "处理环节",
                "质检结论",
                "标注状态",
                "验收状态",
                "操作人",
                "操作",
            ],
            re.findall(r"<th>(.*?)</th>", processing_table_head.group(1)),
        )
        for removed_header in ("Task ID", "collection_id", "采集结论", "当前节点"):
            self.assertNotIn(f"<th>{removed_header}</th>", processing_table_head.group(1))
        for removed_layout in (
            "处理进度</h2>",
            "运行信息",
            "执行明细",
            "dpr-detail-stage",
        ):
            self.assertNotIn(removed_layout, processing_html)

    def test_allocation_management_supports_three_assignment_scenarios(self):
        html = self.client.get("/data/allocations").get_data(as_text=True)
        for expected in (
            "分配管理",
            "项目视角",
            "全部项目",
            "宁德项目",
            "demo 项目",
            "预训练采集",
            ">资源调度</span>",
            ">处理绑定</span>",
            ">数据再处理</span>",
            "当前处理流程保持不变，仅重新指派供应商和处理人",
            "流式积压任务",
            "输入 / 吞吐",
            "重新指派流式处理资源",
            "重新指派供应商",
            "重新指派处理人",
            "处理任务和处理流程保持不变",
            "未绑定处理任务的数据",
            "指定处理任务",
            "绑定处理流程",
            "筛选训练所需数据",
            "符合条件的数据",
            "发起再处理",
            "任务名称",
            "处理流程",
            "优先级",
            "原流程",
            ">继续</option>",
            ">终止</option>",
            'id="drawerStreamReassign"',
            'id="drawerBindProcessingTask"',
            'id="drawerCreateReprocess"',
            'id="dprReprocessTaskName"',
            'id="dprReprocessWorkflow"',
            'id="dprReprocessPriority"',
            'id="dprReprocessOriginalFlow"',
            'id="dprAllocationProjectScope"',
            'id="dpr-stream-backlog-table"',
            'id="dpr-unbound-pool-table"',
            'id="dpr-reprocess-overview"',
            'data-project="宁德项目"',
            "dprSelectAllocationProject",
            "dprFilterStreamRows",
            "dprOpenStreamReassign",
            "dprSubmitStreamReassign",
            "dprFilterUnboundRows",
            "dprOpenBindTask",
            "dprSubmitBindTask",
            "dprRunReprocessFilter",
            "dprOpenReprocessDrawer",
            "dprSubmitReprocess",
        ):
            self.assertIn(expected, html)
        self.assertNotIn(">环节分配</span>", html)
        self.assertNotIn(">流程分配</span>", html)
        self.assertNotIn(">流式积压调度</span>", html)
        self.assertNotIn(">待绑定处理</span>", html)
        self.assertNotIn(">数据二次处理</span>", html)
        self.assertNotIn('id="dprReprocessPurpose"', html)
        self.assertNotIn('id="drawerReassignAllocation"', html)
        self.assertNotIn('id="drawerAssignProcess"', html)
        reprocess_drawer = re.search(
            r'id="drawerCreateReprocess".*?<div class="drawer-foot">',
            html,
            flags=re.S,
        )
        self.assertIsNotNone(reprocess_drawer)
        reprocess_drawer_html = reprocess_drawer.group(0)
        self.assertLess(
            reprocess_drawer_html.index('id="dprReprocessTaskName"'),
            reprocess_drawer_html.index('id="dprReprocessWorkflow"'),
        )
        self.assertLess(
            reprocess_drawer_html.index('id="dprReprocessWorkflow"'),
            reprocess_drawer_html.index('id="dprReprocessPriority"'),
        )
        self.assertLess(
            reprocess_drawer_html.index('id="dprReprocessPriority"'),
            reprocess_drawer_html.index('id="dprReprocessOriginalFlow"'),
        )
        self.assertEqual(4, len(architecture.STREAM_CAPACITY_BACKLOGS))
        self.assertTrue(
            all(
                item["input_rate"] > item["throughput"]
                for item in architecture.STREAM_CAPACITY_BACKLOGS
            )
        )
        self.assertEqual(3, len(architecture.UNBOUND_DATA_POOLS))
        self.assertEqual(
            {"采集", "导入"},
            {item["source"] for item in architecture.UNBOUND_DATA_POOLS},
        )
        self.assertEqual(3, len(architecture.REPROCESS_DATA_OVERVIEW))

    def test_data_management_uses_one_list_with_data_source(self):
        html = self.client.get("/data/recordings").get_data(as_text=True)
        for expected in (
            "recording_id",
            "来源任务 ID",
            "数据来源",
            "全部来源",
            ">采集</option>",
            ">导入</option>",
            "设备序列号",
            "操作人",
            "视频",
            "上传状态",
            "采集结论",
            "质检结论",
            "标注状态",
            "关联处理流程",
            "流程名称",
            "当前节点",
            "COL-2026-0718",
            "IMP-2026-0042",
            "厨房数据质检流程 v3",
            "家居动作标注流程 v2",
            "vendor-12-001",
            'href="/data/recordings/4057808"',
            'class="dpr-process-tree-row"',
        ):
            self.assertIn(expected, html)
        self.assertNotIn('<div class="det-tabs">', html)
        self.assertNotIn("det-pane-collected-records", html)
        self.assertNotIn("det-pane-imported-records", html)
        self.assertNotIn(">自采数据<", html)
        self.assertNotIn(">三方数据<", html)
        self.assertNotIn("lerobot/OrganizePencilCase", html)
        table_head = re.search(
            r'<table class="ant-table dpr-management-record-table">\s*'
            r"<thead><tr>(.*?)</tr></thead>",
            html,
            flags=re.S,
        )
        self.assertIsNotNone(table_head)
        expected_headers = (
            "recording_id",
            "数据来源",
            "视频",
            "上传状态",
            "采集结论",
            "质检结论",
            "标注状态",
            "关联处理流程",
        )
        self.assertEqual(
            list(expected_headers),
            re.findall(r"<th>(.*?)</th>", table_head.group(1)),
        )
        self.assertIn('href="/data/recordings/4057808"', html)
        self.assertIn('aria-label="三路采集视频"', html)

    def test_record_enums_are_centralized_and_valid(self):
        self.assertEqual(
            ("合格", "不合格", "操作失误"),
            architecture.QUALITY_CONCLUSIONS,
        )
        self.assertEqual(
            ("未标注", "已标注"),
            architecture.ANNOTATION_STATUSES,
        )
        self.assertEqual(
            ("未上传", "上传中", "上传成功", "上传失败"),
            architecture.UPLOAD_STATUSES,
        )
        self.assertEqual(
            ("成功", "失败"),
            architecture.COLLECTION_CONCLUSIONS,
        )
        self.assertEqual(
            {"collection": "采集", "import": "导入"},
            architecture.DATA_SOURCE_LABELS,
        )

    def test_record_detail_reuses_trajectory_and_process_preview(self):
        for record in architecture.DATA_MANAGEMENT_RECORDS:
            response = self.client.get(f"/data/recordings/{record['id']}")
            self.assertEqual(200, response.status_code, record["id"])
        html = self.client.get("/data/recordings/4057808").get_data(as_text=True)
        for expected in (
            "Recording 4057808",
            ">轨迹信息</button>",
            ">处理信息</button>",
            ">数据处理记录</button>",
            ">采集信息</button>",
            "cam_high",
            "cam_left_wrist",
            "cam_right_wrist",
            ">LeftArm</button>",
            ">Torso</button>",
            ">RightArm</button>",
            ">Base</button>",
            ">3D Replay</button>",
            "CMD",
            "State",
            'class="dpr-preview-toolbar"',
            'id="dprProcessSwitcher"',
            'id="dprProcessFlow"',
            'id="dprQualityRuleVersion"',
            'id="dprAnnotationRuleVersion"',
            'id="dprHistorySwitcher"',
            'id="dprHistoryFlow"',
            'id="dprHistoryVersion"',
            'id="dprHistoryRows"',
            "dprSelectRecordFlow",
            "dprSelectRecordRuleVersion",
            "dprSwitchRecordHistory",
            "dprSelectRecordHistoryFlow",
            "dprSelectRecordHistoryVersion",
            "质检规则 v3",
            "标注规则 v3",
            "处理版本 v3",
            "highlevel / lowlevel 处理结果",
            "点击分段查看对应处理内容",
            "版本说明",
            "<th>操作人</th><th>操作时间</th><th>操作记录</th>",
            "创建数据记录，来源任务：COL-2026-0718",
            "完成数据采集，采集结论：成功",
            "上传原始数据，上传状态：上传成功",
            '"history_versions"',
            "完成质检，质检结论：合格",
            "修正动作边界 2 处，标注状态：已标注",
            '"version": "v3"',
            '"version": "v2"',
            '"version": "v1"',
            "厨房数据质检流程 v3",
            "家居动作标注流程 v2",
        ):
            self.assertIn(expected, html)
        toolbar_html = re.search(
            r'<div class="dpr-preview-toolbar">(.*?)</div>\s*</div>',
            html,
            flags=re.S,
        )
        self.assertIsNotNone(toolbar_html)
        self.assertIn('class="dpr-preview-tabs"', toolbar_html.group(1))
        self.assertIn('class="dpr-process-switcher"', toolbar_html.group(1))
        self.assertNotIn('id="dprProcessVersion"', html)
        self.assertNotIn(">处理版本<", toolbar_html.group(1))
        self.assertNotIn('class="dpr-process-version-meta"', html)
        for removed_card_id in (
            "dprProcessNode",
            "dprProcessCreated",
            "dprProcessQuality",
            "dprProcessState",
        ):
            self.assertNotIn(f'id="{removed_card_id}"', html)
        self.assertNotIn(">标注信息<", html)
        self.assertNotIn(">版本记录<", html)

    def test_main_workbench_pages_are_restored(self):
        workbench = self.client.get("/data/workbench").get_data(as_text=True)
        for expected in (
            "今日完成任务量",
            "本周完成任务量",
            "流程名称",
            "环节",
            "节点",
            "优先级",
            "数据量",
            "进入工作台",
            "/data/workbench/tasks/WB-2026-0718-QC",
        ):
            self.assertIn(expected, workbench)
        priorities = re.findall(
            r'data-workbench-priority="(P\d)"',
            workbench,
        )
        self.assertEqual(["P0", "P0", "P1", "P1", "P2"], priorities)
        self.assertTrue(all(task.get("stage") for task in toolchain_demo.WB_TASKS))

        for task in toolchain_demo.WB_TASKS:
            response = self.client.get(f"/data/workbench/tasks/{task['id']}")
            self.assertEqual(200, response.status_code, task["id"])
        task_home = self.client.get(
            "/data/workbench/tasks/WB-2026-0718-QC"
        ).get_data(as_text=True)
        for expected in (
            "筛选条件",
            "处理规则",
            'name="recording_id"',
            'name="collected_from"',
            'name="collected_to"',
            'name="collector"',
            'name="supplier"',
            "请输入 recording_id",
            "全部采集员",
            "全部供应商",
            "失误标准",
            "不合格标准",
            "夹爪超出画面（自动化）",
            "三路视频完整性与时间戳一致性检测（自动化）",
            "wb-rule-group mistake",
            "wb-rule-group rejection",
            "开始处理",
            'action="/data/workbench/edit"',
            'name="task" value="WB-2026-0718-QC"',
        ):
            self.assertIn(expected, task_home)
        self.assertNotIn("wb-condition-item", task_home)
        self.assertIn("wb-task-config-grid", task_home)

        editor = self.client.get(
            "/data/workbench/edit?task=WB-2026-0718-QC"
        ).get_data(as_text=True)
        for expected in (
            "WB-2026-0718-QC",
            "厨房数据质检流程 v3",
            "完整性质检",
            "提交",
        ):
            self.assertIn(expected, editor)

        dashboard = self.client.get("/data/dashboard").get_data(as_text=True)
        for expected in (
            "个人看板",
            "今日待处理",
            "今日已完成",
            "一次通过率",
            "平均处理时长",
            "我的待办",
            "近 7 日处理趋势",
            "今日分环节表现",
            "操作员排行榜",
            "Top 10",
            "我的位次",
            "/data/workbench/tasks/WB-2026-0718-QC",
        ):
            self.assertIn(expected, dashboard)
        self.assertNotIn("采集 → 标注 数据漏斗", dashboard)
        self.assertNotIn("各环节处理能力", dashboard)
        self.assertEqual(
            [str(rank) for rank in range(1, 11)],
            re.findall(r'<li data-rank="(\d+)">', dashboard),
        )

    def test_main_workflow_pages_are_restored(self):
        requirements = {
            "/data/pipelines": (
                "流程管理",
                "标准训练数据流水线",
                "多级复核数据处理流程",
                "双轮人工数据处理流程",
                "3 个环节",
                "流程结构",
                "新建工作流",
            ),
            "/data/runs": (
                "执行记录",
                "run_0612a",
                "手动触发",
            ),
            "/data/operators": (
                "算子管理",
                "算子名称",
                "采样配比",
            ),
        }
        for path, expected_values in requirements.items():
            html = self.client.get(path).get_data(as_text=True)
            for expected in expected_values:
                with self.subTest(path=path, expected=expected):
                    self.assertIn(expected, html)

    def test_processing_flow_examples_match_supplied_workflows(self):
        requirements = {
            "/data/pipelines/pl3": (
                'data-processing-flow="pl3"',
                "多级复核数据处理流程",
                'id="wfCanvas"',
                'id="wfFrames"',
                "wf-phase-frame",
                "添加环节",
                "数据质检环节",
                "自动化质检",
                "抽检复核",
                "供应商复核",
                "申诉复核",
                "数据标注环节",
                "端到端切分",
                "一轮复核",
                "二轮复核",
                "支持驳回",
                "内部验收",
                "验收环节",
            ),
            "/data/pipelines/pl4": (
                'data-processing-flow="pl4"',
                "双轮人工数据处理流程",
                'id="wfCanvas"',
                'id="wfFrames"',
                "wf-phase-frame",
                "添加环节",
                "数据质检环节",
                "人工质检",
                "质检",
                "抽检",
                "数据标注环节",
                "人工标注",
                "标注",
                "抽验",
                "2 轮 · 不支持驳回",
                "验收环节",
            ),
        }
        for path, expected_values in requirements.items():
            response = self.client.get(path)
            self.assertEqual(200, response.status_code, path)
            html = response.get_data(as_text=True)
            self.assertIn(
                'href="/data/pipelines" class="sn-item active"',
                html,
            )
            for expected in expected_values:
                with self.subTest(path=path, expected=expected):
                    self.assertIn(expected, html)
            self.assertNotIn("pf-stage-grid", html)
            self.assertIn("wf-phase-port", html)
            self.assertIn("wf-phase-terminal", html)
            self.assertIn("data-terminal-id", html)
            self.assertIn("<span>输入</span>", html)
            self.assertIn("<span>输出</span>", html)
            self.assertIn("phase-edge", html)
            self.assertIn('data-port="branch"', html)
            self.assertIn("wf-condition-content", html)
            self.assertIn(".wf-node.automatic", html)
            self.assertIn('data-node-type="human"', html)
            self.assertIn('data-node-type="automatic"', html)
            self.assertIn('data-node-type="condition"', html)
            self.assertIn("人工节点", html)
            self.assertIn("自动化节点", html)
            self.assertIn("条件节点", html)
            self.assertNotIn(".wf-phase-frame:nth-child", html)

        for pipeline_id in ("pl3", "pl4"):
            pipeline = next(
                item for item in data_platform.PIPELINES if item["id"] == pipeline_id
            )
            nodes, edges, frames = data_platform._processing_canvas_payload(pipeline)
            self.assertEqual(3, len(frames))
            self.assertTrue(nodes)
            for frame in frames:
                phase_nodes = [
                    node for node in nodes if node["phaseId"] == frame["id"]
                ]
                self.assertTrue(phase_nodes)
                self.assertTrue(
                    any(
                        edge["from"] == frame["inputId"]
                        and edge["to"] == phase_nodes[0]["id"]
                        for edge in edges
                    )
                )
                self.assertTrue(
                    any(
                        edge["from"] == phase_nodes[-1]["id"]
                        and edge["to"] == frame["outputId"]
                        for edge in edges
                    )
                )
                for condition_node in (
                    node
                    for node in phase_nodes
                    if node["kind"] == "condition"
                ):
                    self.assertTrue(
                        any(
                            edge["from"] == condition_node["id"]
                            and edge["to"] == frame["outputId"]
                            and edge.get("fromPort") == "branch"
                            and edge.get("branch") == "no"
                            for edge in edges
                        ),
                        "条件节点的否分支必须默认连接本环节输出",
                    )

    def test_automatic_pipelines_follow_processing_flows_and_use_cleaning_phase(self):
        list_html = self.client.get("/data/pipelines").get_data(as_text=True)
        expected_order = (
            "多级复核数据处理流程",
            "双轮人工数据处理流程",
            "标准训练数据流水线",
            "DAgger 数据流水线",
        )
        positions = [list_html.index(name) for name in expected_order]
        self.assertEqual(sorted(positions), positions)

        expected_nodes = {"pl1": 5, "pl2": 2}
        for pipeline_id, node_count in expected_nodes.items():
            pipeline = next(
                item for item in data_platform.PIPELINES if item["id"] == pipeline_id
            )
            nodes, edges, frames = data_platform._processing_canvas_payload(pipeline)
            self.assertEqual(1, len(frames))
            self.assertEqual("数据质检环节", frames[0]["name"])
            self.assertEqual(node_count, len(nodes))
            self.assertEqual(node_count + 1, len(edges))
            self.assertTrue(all(node["kind"] == "automatic" for node in nodes))

            html = self.client.get(f"/data/pipelines/{pipeline_id}").get_data(
                as_text=True
            )
            self.assertIn(
                f'data-processing-flow="{pipeline_id}"',
                html,
            )
            self.assertIn("数据质检环节", html)
            self.assertIn("自动化算子按顺序完成数据质检与校验", html)

    def test_processing_flow_phase_and_node_configuration(self):
        html = self.client.get("/data/pipelines/pl3").get_data(as_text=True)
        for expected in (
            'onclick="wfOpenPhaseDrawer()"',
            'data-phase-type="cleaning"',
            'data-phase-type="annotation"',
            'data-phase-type="acceptance"',
            "质检",
            "标注",
            "验收",
            "已添加",
            "节点名称",
            "标识",
            "描述",
            "所属环节",
            "进入条件",
            "不限制：所有数据进入“是”分支",
            "配置项",
            "表达式",
            "质检结论",
            "添加条件",
            "进入比例",
            "统一比例",
            "高级设置",
            "字段值",
            "添加比例规则",
            "工作区部分组件（勾选控制显隐）",
            "质检工作台",
            "标注工作台",
            "详情工作台",
            "驳回设置",
            "支持驳回",
            "支持驳回到的节点",
            "请选择前序人工节点",
            "previousHumanNodes",
            "wfToggleReject",
            "wfRejectTargetsUpdate",
            "wfSaveConfig",
            "wfAddTypedNode",
            "syncConditionNoBranch",
            'data-node-type="human"',
            'data-node-type="automatic"',
            'data-node-type="condition"',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, html)
        self.assertIn("background:transparent", html)
        self.assertNotIn("示例：质检结论", html)
        self.assertNotIn("sample_rate(", html)
        self.assertNotIn("工作台工作区组件", html)
        self.assertNotIn("wf-cond-percent", html)
        self.assertNotIn("处理人", html)
        self.assertNotIn("wfhAssignee", html)
        self.assertNotIn("处理轮次", html)
        self.assertNotIn('id="wfhRounds"', html)
        self.assertIn('id="wfhRejectEnabled"', html)
        self.assertIn('id="wfhRejectPanel"', html)
        human_start = html.index('<div id="wfHumanConfig"')
        condition_start = html.index('<div id="wfConditionNodeConfig"')
        generic_start = html.index('<div id="wfGenericConfig"')
        human_config = html[human_start:condition_start]
        condition_config = html[condition_start:generic_start]
        self.assertNotIn("进入条件", human_config)
        self.assertNotIn("进入比例", human_config)
        self.assertIn("进入条件", condition_config)
        self.assertIn("进入比例", condition_config)
        self.assertNotIn('<span class="wf-sec-tag ro">默认不限制</span>', html)
        self.assertNotIn('<span class="wf-sec-tag ro">默认 100%</span>', html)
        self.assertIn('id="wfhRatioAdvancedToggle"', html)
        self.assertIn(
            'onchange="wfToggleRatioAdvanced(this.checked)"',
            html,
        )
        self.assertNotIn('id="wfhRatioConfigModes"', html)
        self.assertNotIn("wfRatioConfigMode", html)
        self.assertGreaterEqual(html.count('data-mode="config"'), 2)
        self.assertGreaterEqual(html.count('data-mode="expression"'), 2)

    def test_workbench_management_has_workbench_and_component_tabs(self):
        html = self.client.get("/data/workbench-management").get_data(as_text=True)
        for expected in (
            "工作台管理",
            ">工作台</span>",
            ">组件</span>",
            "质检工作台",
            "标注工作台",
            "详情工作台",
            "multi_view_video",
            "quality_issue_editor",
            "annotation_segment_editor",
            "trajectory_viewer",
            "quality_result_viewer",
            "annotation_result_viewer",
            "tag_viewer",
            "conclusion_selector",
            "workbench_log",
            "task_actions",
            "适用工作台",
            "/data/workbench-management/preview/quality",
            "/data/workbench-management/preview/annotation",
            "/data/workbench-management/preview/detail",
        ):
            self.assertIn(expected, html)

    def test_quality_annotation_and_detail_workbenches_use_separate_modules(self):
        requirements = {
            "/data/workbench-management/preview/quality?task=WB-2026-0718-QC": (
                "质检工作台",
                "采集指令",
                "失误记录",
                ">轨迹</button>",
                ">质检</button>",
                ">日志</button>",
                'data-component="trajectory_viewer"',
                'data-component="quality_issue_editor"',
                'data-component="workbench_log"',
            ),
            "/data/workbench-management/preview/annotation?task=WB-2026-0922-LB": (
                "标注工作台",
                "任务描述",
                ">轨迹</button>",
                ">质检</button>",
                ">标注</button>",
                ">日志</button>",
                'data-component="trajectory_viewer"',
                'data-component="quality_result_viewer"',
                'data-component="annotation_segment_editor"',
                'data-component="workbench_log"',
                'data-component="quality_result_timeline"',
                'aria-label="质检问题时间条"',
                "wbx-quality-marker",
                "夹爪超出画面",
            ),
            "/data/workbench-management/preview/detail?task=WB-2026-0922-AC": (
                "详情工作台",
                ">轨迹</button>",
                ">质检</button>",
                ">标注</button>",
                ">标签</button>",
                ">日志</button>",
                'data-component="trajectory_viewer"',
                'data-component="quality_result_viewer"',
                'data-component="annotation_result_viewer"',
                'data-component="tag_viewer"',
                'data-component="workbench_log"',
                'data-component="quality_result_timeline"',
                'aria-label="质检问题时间条"',
                "wbx-quality-marker",
                "画面异常",
                "switchWorkbenchDetailTab",
            ),
        }
        for path, expected_values in requirements.items():
            response = self.client.get(path)
            self.assertEqual(200, response.status_code, path)
            html = response.get_data(as_text=True)
            self.assertIn(
                'href="/data/workbench-management" class="sn-item active"',
                html,
            )
            for expected in expected_values:
                with self.subTest(path=path, expected=expected):
                    self.assertIn(expected, html)
            for module in ("conclusion", "operation"):
                self.assertIn(
                    f'data-workbench-module="{module}"',
                    html,
                )
            for expected in (
                "合格",
                "不合格",
                "操作失误",
                'data-component="sticky_decision_actions"',
                "wbx-conclusion-panel",
                "wbx-operation-panel",
                "wbx-operation-actions",
                ">重置</button>",
                ">暂离</button>",
                ">驳回</button>",
                ">提交</button>",
                "wbResetWorkbench",
                ".wbx-execution { position:fixed;",
            ):
                self.assertIn(expected, html)
            self.assertNotIn("submit.textContent", html)
            self.assertNotIn("wbx-action-divider", html)
            self.assertNotIn('data-workbench-module="log"', html)
            self.assertNotIn("workbenchLogModal", html)

    def test_main_configuration_pages_are_restored(self):
        requirements = {
            "/data/rules": ("规则管理", "缺帧检测规则", "图像模糊度检测"),
            "/data/scenes": ("场景管理", "场景名称", "新增场景"),
            "/data/tags": ("标签管理", "能力标签", "动作标签"),
        }
        for path, expected_values in requirements.items():
            html = self.client.get(path).get_data(as_text=True)
            for expected in expected_values:
                with self.subTest(path=path, expected=expected):
                    self.assertIn(expected, html)

    def test_tag_groups_show_required_fields_and_create_drawer(self):
        html = self.client.get("/data/tags").get_data(as_text=True)
        for expected in (
            "标签组",
            "名称",
            "描述",
            "负责人",
            "启用状态",
            "平台通用标签体系",
            "由平台统一维护的标准标签体系",
            "质量处理标签组",
            "项目交付标签组",
            "自定义标签",
            "历史标签迁移",
            "Alan Li",
            "Dream",
            "Raleigh",
            "Oasis",
            "Joanna",
            'data-enabled="true"',
            'data-enabled="false"',
            "tag-status-switch",
            "tagToggleGroupStatus",
            "tagOpenCreateGroup",
            'id="create-tag-group-drawer"',
            "新建标签组",
            'id="newTagGroupName"',
            'id="newTagGroupIdentifier"',
            'id="newTagGroupDescription"',
            'id="newTagGroupOwner"',
            'id="newTagGroupEnabled"',
            "支持添加多个负责人",
            'data-identifier="platform_standard_taxonomy"',
            'data-identifier="custom_tag"',
            'data-group-id="custom_tag"',
            'data-owners="Alan Li|Dream|Raleigh|Oasis|Joanna"',
            "tagIdentifierExists",
            "标识已存在，请更换",
            "newTagGroupIdentifier').disabled = true",
            "tagGroupOwnerChips",
            "tagOpenEditGroup",
            "currentTagUser",
            "tagSyncEditPermission",
            "tagCurrentUserOwns",
            "仅支持负责人编辑",
            "tagDeleteGroup",
            "当前标签组已被引用，不支持删除",
            'data-references="0"',
            'data-references="12"',
            'data-can-manage="true"',
            'data-can-manage="false"',
            'id="tagGroupSearchInput"',
            "tagFilterGroups",
            "发布标签",
            "tagPublishLabels",
            "tag-publish-button",
            "tag-detail-actions",
            "tag-readonly",
            "tagSyncManagePermission",
            "tag-group-create-button",
            "position:sticky",
            "tag-list-toolbar",
            "标签名称",
            "层级",
            "英文名称",
            "已发布",
            "创建时间",
            "创建人 ID",
            "tag-level-badge",
            "tag-drag-handle",
            "tag-row-check",
            "新建一级标签",
            "tag-list-pagination",
            "20条/页",
            "查看详情",
            'class="tag-group-description" data-tip=',
            "text-overflow:ellipsis",
            "card.querySelector('small').setAttribute('data-tip', description)",
            "tagCreateGroup",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, html)
        self.assertNotIn('id="tagGroupMeta"', html)
        self.assertNotIn("<th>描述</th>", html)
        self.assertRegex(html, r'aria-label="编辑"\s+disabled')
        self.assertRegex(html, r'class="tag-card-action act-icon act-danger" aria-label="删除" disabled')

    def test_project_management_is_under_configuration_management(self):
        html = self.client.get("/data/projects").get_data(as_text=True)
        for expected in (
            "项目管理",
            "<th>项目名称</th>",
            "<th>项目描述</th>",
            "<th>负责人</th>",
            "预训练采集",
            "demo 项目",
            "宁德项目",
        ):
            self.assertIn(expected, html)
        project_rows = re.findall(r"<tbody>(.*?)</tbody>", html, flags=re.S)
        self.assertTrue(any(body.count("<tr>") == 3 for body in project_rows))

    def test_asset_and_operations_pages_match_table(self):
        requirements = {
            "/data/datasets": (
                "数据集管理",
                "数据集目录",
                "数据预览",
                "构成分析",
                ">版本</div>",
                "基本信息",
                "处理数据",
                "查看血缘",
                'id="procDrawer"',
                'href="/data/datasets?sel=',
            ),
            "/data/suppliers": (
                "供应商管理",
                "光轮智能",
                "服务类型",
            ),
            "/data/personnel": (
                "人员管理",
                "供应商 A-017",
                "最近活跃",
            ),
            "/data/permissions": (
                "权限管理",
                "角色管理",
                "资源管理",
                "授权管理",
            ),
        }
        for path, expected_values in requirements.items():
            html = self.client.get(path).get_data(as_text=True)
            for expected in expected_values:
                with self.subTest(path=path, expected=expected):
                    self.assertIn(expected, html)

    def test_data_platform_reuses_model_dataset_management(self):
        data_html = self.client.get(
            "/data/datasets?sel=ds1"
        ).get_data(as_text=True)
        model_html = self.client.get(
            "/model/data/datasets?sel=ds1"
        ).get_data(as_text=True)
        shared_markers = (
            "数据集目录",
            'id="datasetTreeKeyword"',
            'id="datasetTreeTagFilter"',
            "请选择标签",
            "filterDatasetTree",
            "数据预览",
            "构成分析",
            "摘要信息",
            "完整信息",
            'data-dataset-info-field="tags"',
            "处理数据",
            "新建目录",
            "新建数据集",
            'id="dsEditModal"',
            'id="dsEditTags"',
            "<label>标签</label>",
            "openDsEdit",
            "datasetTagSetValues",
            "dataset-tag-picker",
            "dataset-tag-chip",
            "dataset-tag-picker-control",
            "场景标签 &gt; 作业区域 &gt; 白板区",
            '"tags": [',
            'id="procDrawer"',
            "HighLevel 维度",
            "Lowlevel 维度",
        )
        for marker in shared_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, data_html)
                self.assertIn(marker, model_html)
        self.assertIn('href="/data/datasets?sel=', data_html)
        self.assertIn('action="/data/datasets/', data_html)
        self.assertIn('href="/model/data/datasets?sel=', model_html)
        self.assertNotIn('href="/model/data/datasets?sel=', data_html)
        self.assertIn(">查看血缘</a>", data_html)
        self.assertIn(">查看血缘</a>", model_html)
        self.assertIn(">导出数据</button>", model_html)
        model_actions = re.search(
            r'<div class="dataset-detail-actions">(.*?)</div>',
            model_html,
            flags=re.S,
        )
        self.assertIsNotNone(model_actions)
        self.assertNotIn("处理数据", model_actions.group(1))
        self.assertLess(
            model_actions.group(1).index("查看血缘"),
            model_actions.group(1).index("导出数据"),
        )

        standalone_detail = self.client.get(
            "/model/data/datasets/ds_501"
        ).get_data(as_text=True)
        self.assertIn(">导出数据</button>", standalone_detail)
        self.assertIn(">查看血缘</a>", standalone_detail)
        self.assertIn('data-dataset-info-field="tags"', standalone_detail)
        self.assertIn("白板区", standalone_detail)
        self.assertIn("dataset-tag-path-list", standalone_detail)
        self.assertIn("场景标签 > 作业区域 > 白板区", standalone_detail)

    def test_model_query_build_dataset_drawer_supports_labels(self):
        html = self.client.get("/model/data/query").get_data(as_text=True)
        drawer = re.search(
            r'<div class="modal-mask" id="buildDsDrawer".*?</div>\s*</div>\s*</div>',
            html,
            flags=re.S,
        )
        self.assertIsNotNone(drawer)
        self.assertIn("用结果建数据集", drawer.group(0))
        self.assertIn('id="buildDsTags"', drawer.group(0))
        self.assertIn("<label>标签</label>", drawer.group(0))
        self.assertIn('name="dataset_tag"', drawer.group(0))
        self.assertIn("dataset-tag-picker-control", drawer.group(0))
        self.assertIn("请选择或创建标签", drawer.group(0))
        self.assertIn("能力标签 &gt; 方位理解 &gt; 左右", drawer.group(0))
        self.assertIn("datasetTagToggleOption", drawer.group(0))

    def test_model_prompt_management_uses_ordered_expandable_rows(self):
        html = self.client.get("/model/eval/prompts").get_data(as_text=True)
        for marker in (
            "任务提示词",
            "Labels",
            "序号",
            "Task-Prompt",
            "Difficulty",
            "Creator",
            "Actions",
            "prompt-child-row",
            "prompt-drag-handle",
            "拖拽调整顺序",
            "prompt-add-child-row",
            "stepPromptDifficulty",
            "新增测试任务",
            "导入 JSON",
            ">保存</button>",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

        self.assertLess(
            html.index("prompt-parent-row"),
            html.index('id="new-parent-row"'),
        )
        self.assertIn(
            "fetch('/model/eval/prompts/' + pid + '/reorder-children'",
            html,
        )

    def test_model_prompt_child_reorder_persists(self):
        prompt = toolchain_demo.ep.PROMPTS[0]
        original = [child["id"] for child in prompt["low_levels"]]
        if len(original) < 2:
            self.skipTest("mock prompt needs at least two children")
        reordered = list(reversed(original))
        try:
            response = self.client.post(
                f'/model/eval/prompts/{prompt["id"]}/reorder-children',
                json={"order": reordered},
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual(reordered, response.get_json()["order"])
            self.assertEqual(
                reordered,
                [child["id"] for child in prompt["low_levels"]],
            )
        finally:
            self.client.post(
                f'/model/eval/prompts/{prompt["id"]}/reorder-children',
                json={"order": original},
            )

    def test_retired_architecture_and_old_refactor_paths_redirect(self):
        redirects = {
            "/data/architecture": "/data/dashboard",
            "/data/tasks": "/data/collection-tasks",
            "/data/task-pool": "/data/workbench",
            "/data/pipeline-definitions": "/data/pipelines",
            "/data/pipeline-runs": "/data/runs",
            "/data/assets": "/data/recordings",
            "/data/dataset-versions": "/data/datasets",
            "/data/lineage": "/data/datasets",
            "/data/capabilities": "/data/operators",
            "/data/workbench-schemas": "/data/workbench-management",
            "/data/operations": "/data/dashboard",
            "/data/process": "/data/runs",
            "/data/raw": "/data/recordings",
        }
        for old_path, new_path in redirects.items():
            with self.subTest(old_path=old_path):
                response = self.client.get(old_path, follow_redirects=False)
                self.assertEqual(302, response.status_code)
                self.assertTrue(response.headers["Location"].endswith(new_path))

    def test_removed_quality_gate_product_objects_stay_removed(self):
        retired_pages = {"quality_results", "rework_orders", "policies"}
        self.assertTrue(retired_pages.isdisjoint(architecture.PAGE_SPECS))
        for path in (
            "/data/collection-tasks",
            "/data/processing-tasks",
            "/data/recordings",
        ):
            html = self.visible_html(self.client.get(path).get_data(as_text=True))
            for term in (
                "质量门槛",
                "质量门禁",
                "Quality Gate",
                "Quality Result",
                "质量结果",
                "返工管理",
                "规则策略",
            ):
                with self.subTest(path=path, term=term):
                    self.assertNotIn(term, html)

    def test_design_documentation_is_not_a_product_page(self):
        self.assertNotIn("architecture", architecture.PAGE_SPECS)
        for spec in architecture.PAGE_SPECS.values():
            html = self.visible_html(
                self.client.get(spec["path"]).get_data(as_text=True)
            )
            for term in FORBIDDEN_DESIGN_DOCUMENT_TERMS:
                with self.subTest(path=spec["path"], term=term):
                    self.assertNotIn(term, html)

    def test_product_pages_only_link_to_registered_internal_routes(self):
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
