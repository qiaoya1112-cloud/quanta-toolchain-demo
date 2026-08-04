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
                    "processing_tasks",
                    "allocation_management_v2",
                ],
            ),
            ("工作台", ["workbench_v2"]),
            (
                "工作流",
                [
                    "workflow_management",
                    "operator_management",
                ],
            ),
            (
                "配置管理",
                [
                    "rule_management",
                    "workbench_management",
                ],
            ),
            (
                "运营管理",
                [
                    "user_group_management",
                    "supplier_management",
                    "personnel_management",
                    "permission_management",
                ],
            ),
        ]
        self.assertEqual(expected_groups, architecture.NAV_GROUPS)
        workbench_nav_entry = next(
            entry
            for group, entries in architecture.DATA_PLATFORM_NAV
            for entry in entries
            if entry[0] == "/data/workbench-v2"
        )
        self.assertEqual("标注工作台", workbench_nav_entry[1])

        nav_keys = [key for _, keys in architecture.NAV_GROUPS for key in keys]
        self.assertEqual(
            {
                key
                for key, spec in architecture.PAGE_SPECS.items()
                if not spec.get("hidden") and not spec.get("hide_from_nav")
            },
            set(nav_keys),
        )
        self.assertEqual(11, len(nav_keys))
        self.assertEqual(len(nav_keys), len(set(nav_keys)))
        paths = [item["path"] for item in architecture.PAGE_SPECS.values()]
        self.assertEqual(len(paths), len(set(paths)))
        non_current_nav_entries = [
            entry
            for _, entries in architecture.DATA_PLATFORM_NAV
            for entry in entries
            if len(entry) > 3 and entry[3] == "非本期"
        ]
        self.assertEqual(0, len(non_current_nav_entries))
        no_ui_nav_entries = [
            entry
            for _, entries in architecture.DATA_PLATFORM_NAV
            for entry in entries
            if len(entry) > 3 and entry[3] == "无界面"
        ]
        self.assertEqual(5, len(no_ui_nav_entries))
        self.assertFalse(
            any(
                len(entry) > 3 and entry[3] == "草稿"
                for _, entries in architecture.DATA_PLATFORM_NAV
                for entry in entries
            )
        )
        sidebar_html = self.client.get("/data/recordings").get_data(as_text=True)
        self.assertNotIn('class="sn-tag t-nonphase">非本期</span>', sidebar_html)
        self.assertEqual(5, sidebar_html.count(">无界面</span>"))
        self.assertNotIn('href="/data/projects"', sidebar_html)
        self.assertNotIn('href="/data/allocations"', sidebar_html)
        self.assertIn('href="/data/allocations-v2"', sidebar_html)
        self.assertIn("分配管理", sidebar_html)
        self.assertNotIn('class="sn-tag t-draft">草稿</span>', sidebar_html)

    def test_allocation_management_filters_tasks(self):
        html = self.client.get("/data/allocations-v2").get_data(as_text=True)
        for expected in (
            "dpr-v2-page-head",
            '<option value="质检">质检环节</option>',
            '<option value="标注">标注环节</option>',
            "DPR_V2_STAGE",
            "dprV2ResourcesForStage",
            "dprV2VisibleTasks",
            "DPR_V2_OTHER_CONTRIBUTIONS",
            "节点整体进度",
            "当前处理人",
            "其他处理人",
            "未完成",
            "dpr-v2-contribution-current",
            "dpr-v2-contribution-other",
            'id="dprV2FilterStage"',
            'id="dprV2FilterFlow"',
            'id="dprV2FilterNode"',
            'id="dprV2SummaryDateFrom"',
            'id="dprV2SummaryDateTo"',
            "dprV2InitSummaryDates",
            "dprV2SummaryTaskMatches",
            "dprV2SummaryDateChanged",
            "统计时间",
            "dprV2FilterStageChanged",
            "dprV2FilterFlowChanged",
            "dprV2ClearFilters",
            "dprV2Query",
            '>清空</button>',
            '>查询</button>',
            "dprV2TaskMatches",
            "dprV2RenderResourceSummary",
            "已处理任务量：",
            "（含已完成任务）",
        ):
            self.assertIn(expected, html)
        self.assertNotIn('id="dprV2StageSelect"', html)
        self.assertNotIn("dprV2StageChanged", html)
        self.assertNotIn('id="dprV2FilterDateFrom"', html)
        self.assertNotIn('id="dprV2FilterDateTo"', html)
    def test_all_configured_pages_render_in_shared_portal(self):
        for key, spec in architecture.PAGE_SPECS.items():
            with self.subTest(page=key):
                response = self.client.get(spec["path"])
                self.assertEqual(200, response.status_code)
                html = response.get_data(as_text=True)
                self.assertIn(spec["title"], html)
                self.assertIn("数据平台", html)
                self.assertIn('class="q-sider"', html)

    def test_data_root_opens_processing_tasks(self):
        response = self.client.get("/data", follow_redirects=False)
        self.assertEqual(302, response.status_code)
        self.assertTrue(
            response.headers["Location"].endswith("/data/processing-tasks")
        )

    def test_collection_tasks_match_table_definition(self):
        html = self.client.get("/data/collection-tasks").get_data(as_text=True)
        self.assertIn("<h1>采集任务</h1>", html)
        self.assertRegex(
            html,
            re.compile(
                r'<div class="dpr-intro-title-row">.*?<h1>采集任务</h1>'
                r'.*?id="newCollectionTaskButton".*?</div>',
                flags=re.S,
            ),
        )
        self.assertEqual(
            4,
            len(
                re.findall(
                    r'class="det-tab dpr-collection-tab(?: active)?"',
                    html,
                )
            ),
        )
        self.assertIn(
            'class="det-tab dpr-collection-tab active" role="tab" tabindex="0" '
            'data-task-mode="instruction"',
            html,
        )
        self.assertIn(
            'class="det-tabs dpr-allocation-tabs dpr-collection-tabs" role="tablist"',
            html,
        )
        self.assertIn(
            "document.querySelectorAll('.dpr-collection-tab')",
            html,
        )
        for expected in (
            "指令采集 <b>2</b>",
            "自由采集 <b>2</b>",
            "DAgger 采集 <b>1</b>",
            "数据导入 <b>1</b>",
            "<label>任务 ID</label>",
            "<label>名称</label>",
            "<label>类型</label>",
            "<label>操作人</label>",
            "<th>任务 ID</th>",
            "<th>名称</th>",
            "<th>类型</th>",
            "<th>进度</th>",
            "<th>优先级</th>",
            "<th>创建人</th>",
            "<th>创建时间</th>",
            'href="/data/tasks/COL-2026-0718"',
            'href="/data/recordings?source=import&task=IMP-2026-0042"',
            ">数据</a>",
            "dprOpenCollectionTaskDrawer('detail', this)",
            "dprOpenCollectionTaskDrawer('edit', this)",
            ">详情</button>",
            ">编辑</button>",
            'class="dpr-priority wb-priority priority-high">9</span>',
            'class="dpr-priority wb-priority priority-medium">6</span>',
            'class="dpr-task-progress-line dpr-collection-progress-line"',
            "1,240 / 1,500 · 83%",
        ):
            self.assertIn(expected, html)
        self.assertNotIn("<th>操作人</th>", html)
        self.assertIn(
            ".dpr-intro-title-row .dpr-intro-actions{position:absolute;right:0;top:50%;transform:translateY(-50%);margin:0}",
            html,
        )
        task_table = re.search(
            r'<table class="dpr-table" id="dpr-collection-task-table">.*?</table>',
            html,
            flags=re.S,
        )
        self.assertIsNotNone(task_table)
        self.assertNotIn("PROC-2026-0922", task_table.group(0))
        for task in (
            item for item in architecture.BUSINESS_TASKS
            if item["type"] in ("data_collection_task", "data_import_task")
        ):
            self.assertIn(task["priority"], ("P0", "P1", "P2"))

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
            ">所属项目</label>",
            ">优先级</label>",
            "<option>指令采集</option>",
            "<option>自由采集</option>",
            "<option>DAgger 采集</option>",
            "<option>数据导入</option>",
            "<option>P1</option>",
            "<option>P0</option>",
            "<option>P2</option>",
            "<option>预训练采集</option>",
            "<option>demo 项目</option>",
            "<option>宁德项目</option>",
            "采集结果统一写入数据湖",
            "处理任务将根据数据来源、来源任务 ID、项目及质量状态等条件持续筛选数据",
            "DPR_COLLECTION_ACTIVE_MODE",
            "taskMode === 'import' ? '新增导入任务' : '新增采集任务'",
            "'新建数据导入任务'",
            "'数据导入任务详情'",
            "'编辑数据导入任务'",
        ):
            self.assertIn(expected, html)
        self.assertNotIn('name="processing_task"', html)
        self.assertNotIn("选择则流式流转", html)
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
            )
        ]
        self.assertEqual(sorted(field_positions), field_positions)

    def test_processing_tasks_match_table_definition(self):
        html = self.client.get("/data/processing-tasks").get_data(as_text=True)
        self.assertIn("<h1>处理任务</h1>", html)
        self.assertRegex(
            html,
            re.compile(
                r'<div class="dpr-intro-title-row">.*?<h1>处理任务</h1>'
                r'.*?dprOpenProcessingTaskDrawer\(\'new\'\).*?</div>',
                flags=re.S,
            ),
        )
        for expected in (
            "<label>任务 ID</label>",
            "<label>名称</label>",
            "<label>任务状态</label>",
            "<label>数据来源</label>",
            "<label>处理流程</label>",
            "<th>任务 ID</th>",
            "<th>名称</th>",
            "<th>状态</th>",
            "<th>绑定流程</th>",
            "<th>优先级</th>",
            "<th>创建人</th>",
            "<th>创建时间</th>",
            "多级质检复核流程",
            "双轮人工标注流程",
            'href="/data/tasks/PROC-2026-0922"',
            ">数据</a>",
            "dprOpenProcessingTaskDrawer('detail', this)",
            "dprOpenProcessingTaskDrawer('edit', this)",
            ">详情</button>",
            ">编辑</button>",
            'data-progress-stage="质检"',
            'data-progress-stage="标注"',
            "842 / 1,206 · 70%",
            "488 / 842 · 58%",
            'class="dpr-priority wb-priority priority-high">9</span>',
            'class="dpr-priority wb-priority priority-medium">6</span>',
            'class="dpr-flow-binding-name"',
        ):
            self.assertIn(expected, html)
        self.assertNotIn("<th>持续筛选条件</th>", html)
        self.assertNotIn("<th>数据量</th>", html)
        self.assertNotIn('data-progress-stage="验收"', html)
        self.assertNotIn(
            "处理任务持续监听数据湖；满足筛选条件的数据自动进入已绑定流程。",
            html,
        )
        self.assertIn("处理任务是持续运行的数据筛选器", html)
        self.assertNotIn('data-processing-stage=', html)
        self.assertNotIn("人工节点分配", html)
        self.assertNotIn(">积压</span>", html)
        self.assertNotIn(">正常</span>", html)
        for task in (
            item for item in architecture.BUSINESS_TASKS
            if item["type"] == "data_processing_task"
        ):
            self.assertIn("filter_rules", task)
            self.assertIn("flow_bindings", task)
            self.assertIn("enabled", task)
            self.assertIn(task["priority"], ("P0", "P1", "P2"))

    def test_new_processing_task_uses_full_page_flow_assignment(self):
        html = self.client.get("/data/processing-tasks").get_data(as_text=True)
        for expected in (
            "dprOpenProcessingTaskDrawer('new')",
            'id="drawerProcessingTaskForm"',
            'class="dpr-processing-task-page"',
            ".dpr-processing-task-page{position:fixed;z-index:260;top:52px;left:220px;",
            'id="processingTaskDrawerTitle">新建处理任务</h2>',
            "'处理任务详情'",
            "'编辑处理任务'",
            ">任务名称</span>",
            ">所属项目</span>",
            ">优先级</span>",
            ">任务状态</span>",
            "预期任务量",
            "持续任务",
            "固定条数",
            "固定时长",
            "processingTaskExpectedMode",
            "processingTaskExpectedValue",
            "任务条数",
            "任务时长",
            "dprExpectedTaskModeChange",
            "dprExpectedTaskValueChange",
            "dprSyncAllocationFromExpectedTask",
            "筛选条件",
            "留空表示不限制",
            "+ 添加条件",
            "处理环节",
            "质检流程",
            "标注流程",
            "人工任务节点",
            "用户组",
            "供应商",
            "定量分配",
            "比例分配",
            "每个人工节点合计 100%",
            "processingTaskAssignmentHint",
            "分配时间合计必须等于预期总时长",
            "流程图",
            "点击人工任务节点定位下方分配卡片",
            "节点级",
            "dprRenderFlowPreview",
            "dprFocusAssignmentCard",
            "dprRenderFlowChoices",
            "dprRenderNodeAssignments",
            "dprProcessingAssignmentsValid",
            "<option>预训练采集</option>",
            "<option>demo 项目</option>",
            "<option>宁德项目</option>",
            "<option>1</option><option>2</option><option>3</option>",
            "多级质检复核流程",
            "端到端切分标注流程",
            "dprRenderTaskFilters",
            "dprAddTaskFilter",
        ):
            self.assertIn(expected, html)
        self.assertNotIn(".dpr-processing-task-page{left:192px", html)
        self.assertLess(
            html.index('id="processingTaskFlowPreview"'),
            html.index('class="dpr-node-assignment-section"'),
        )
        self.assertIn(".dpr-flow-selector { position:sticky", html)
        self.assertIn("#processingTaskFlowPreview", html)
        self.assertIn("position:sticky", html)
        self.assertNotIn("持续筛选条件", html)
        self.assertNotIn('id="processingTaskAllocationSettings"', html)
        self.assertNotIn("dprRenderAllocationSettings", html)
        self.assertNotIn("<b>分配策略</b>", html)
        self.assertNotIn("当前任务预期总时长", html)
        self.assertNotIn("<em>任务级</em>", html)
        drawer_start = html.index('id="drawerProcessingTaskForm"')
        drawer_html = html[drawer_start:]
        field_positions = [
            drawer_html.index(f'name="{field}"')
            for field in ("task_name", "project", "priority", "enabled")
        ]
        self.assertEqual(sorted(field_positions), field_positions)
        self.assertEqual(
            {"质检", "标注", "验收"},
            {flow["stage"] for flow in architecture.PROCESSING_FLOWS},
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
            "流程实例",
            "流程版本",
            "当前节点",
            "实例状态",
            "任务池 / 当前处理人",
            "4057761",
            "标注：供应商 A",
            "双轮人工标注流程",
            "标注员用户组",
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
                "流程实例",
                "流程版本",
                "当前节点",
                "实例状态",
                "任务池 / 当前处理人",
                "操作",
            ],
            re.findall(r"<th>(.*?)</th>", processing_table_head.group(1)),
        )
        for removed_header in ("Task ID", "collection_id", "采集结论"):
            self.assertNotIn(f"<th>{removed_header}</th>", processing_table_head.group(1))
        for removed_layout in (
            "处理进度</h2>",
            "运行信息",
            "执行明细",
            "dpr-detail-stage",
        ):
            self.assertNotIn(removed_layout, processing_html)

    def test_allocation_management_is_decision_first_dispatch_center(self):
        html = self.client.get("/data/allocations").get_data(as_text=True)
        for expected in (
            "分配管理",
            "先查看质检、标注和验收的处理情况",
            ">项目</span>",
            "全部项目",
            "宁德项目",
            "demo 项目",
            "预训练采集",
            "处理概览",
            "点击业务环节",
            "未分配",
            "已分配待处理",
            "处理中",
            "已完成",
            "处理吞吐不足",
            "未进入处理",
            "最长滞留",
            "待处理事项",
            "全部问题",
            "吞吐不足",
            "影响任务",
            'placeholder="搜索采集/处理任务 ID"',
            "处理资源：光轮智能",
            "数据来源：采集",
            "操作人：刘素粉",
            "分配积压数据",
            "分配存量积压",
            "确认分配",
            "分配对象",
            "用户组",
            "用户",
            "分配条数",
            "+ 添加分配",
            "分配合计",
            "本期仅支持将当前积压拆分给多个用户组",
            "本期仅支持分配到用户组",
            "同一分配对象不能重复添加",
            "分配合计不能超过当前积压数量",
            "本次分配只影响当前存量积压数据",
            "不修改流程模板中的用户组配置",
            "后续新增数据仍按原有流转与分配规则执行",
            "绑定处理任务",
            "确认绑定处理任务",
            "数据已进入数据湖，但尚未命中处理任务",
            '<option value="" selected disabled>请选择处理任务</option>',
            "请先选择处理任务",
            "由所选处理任务自动带出，不支持在此修改",
            "业务环节",
            "通用质检规则 v3",
            "通用动作标注规则 v3",
            "数据验收流程",
            "发起数据再处理",
            "筛选数据",
            "配置处理任务",
            "命中数据概览",
            "下一步",
            "上一步",
            "确认发起",
            "任务名称",
            "处理流程",
            "优先级",
            "原流程",
            ">继续</option>",
            ">终止</option>",
            'id="drawerDispatchResource"',
            'id="drawerDispatchBinding"',
            'id="drawerDispatchReprocess"',
            'id="dprDispatchProjectScope"',
            'id="dpr-dispatch-issue-table"',
            'id="dpr-dispatch-reprocess-preview"',
            'class="dpr-dispatch-object"',
            "<i>来源任务</i><button",
            'data-sources="COL-2026-0718|COL-2026-0719|IMP-2026-0042"',
            "3 个 · 查看",
            "1 个 · 查看",
            "<i>处理任务</i><code>PROC-2026-0921</code>",
            '<i>处理任务</i><code class="empty">—</code>',
            'id="drawerDispatchSources"',
            'id="dprDispatchSourceList"',
            'data-project="宁德项目"',
            'data-dispatch-type="capacity"',
            'data-dispatch-type="unbound"',
            'class="dpr-dispatch-task-row"',
            'class="dpr-dispatch-stage-row"',
            'data-dispatch-role="parent"',
            'data-dispatch-role="child"',
            'data-dispatch-role="standalone"',
            'data-dispatch-expanded="false"',
            "处理节点",
            "节点明细",
            "供应商复核",
            "标注抽验",
            "供应商标注",
            "内部验收",
            "2 个处理节点积压",
            "多个处理节点能力不足",
            "展开查看各节点的吞吐与处理资源",
            "dprRefreshDispatchPage",
            "dprSelectDispatchStage",
            "dprSetDispatchIssueType",
            "dprFilterDispatchIssues",
            "dprToggleDispatchTask",
            "dprOpenDispatchSources",
            "dprOpenDispatchResource",
            "dprDispatchAssignmentRow",
            "dprAddDispatchAssignment",
            "dprRemoveDispatchAssignment",
            "dprUpdateDispatchAssignmentTotal",
            "dprSubmitDispatchResource",
            "dprOpenDispatchBinding",
            "dprRenderDispatchBindingFlows",
            "dprSubmitDispatchBinding",
            "dprOpenDispatchReprocess",
            "dprShowDispatchReprocessStep",
            "dprSubmitDispatchReprocess",
        ):
            self.assertIn(expected, html)
        self.assertNotIn(
            'onclick="dprOpenDispatchReprocess()">发起数据再处理</button>',
            html,
        )
        self.assertNotIn(">资源调度</span>", html)
        self.assertNotIn(">处理绑定</span>", html)
        self.assertNotIn('id="drawerStreamReassign"', html)
        self.assertNotIn('id="drawerBindProcessingTask"', html)
        self.assertNotIn('id="drawerCreateReprocess"', html)
        self.assertNotIn('href="/data/allocations-legacy"', html)
        self.assertNotIn('id="dprDispatchWorkflow"', html)
        self.assertNotIn('id="dprDispatchNewGroup"', html)
        self.assertNotIn("dprSyncDispatchMembers", html)
        self.assertNotIn("dprSwitchDispatchAssigneeType", html)
        self.assertNotIn('<option value="user"', html)
        self.assertNotIn("当前处理能力", html)
        self.assertNotIn("确认调整资源", html)
        self.assertNotIn("<small>数据池：", html)
        self.assertNotIn("处理资源：光轮智能 · 成员：包媛桐", html)
        self.assertNotIn("搜索任务 ID / 数据池批次", html)
        self.assertLess(html.index("处理概览"), html.index("待处理事项"))
        self.assertLess(
            html.index('data-dispatch-step="1"'),
            html.index('data-dispatch-step="2"'),
        )
        binding_drawer = re.search(
            r'<div class="drawer dpr-allocation-drawer" '
            r'id="drawerDispatchBinding">.*?</div>\s*</div>\s*</div>',
            html,
            re.S,
        )
        self.assertIsNotNone(binding_drawer)
        self.assertLess(
            binding_drawer.group(0).index('id="dprDispatchBindingPriority"'),
            binding_drawer.group(0).index('id="dprDispatchProcessingTask"'),
        )
        self.assertLess(
            binding_drawer.group(0).index('id="dprDispatchProcessingTask"'),
            binding_drawer.group(0).index("dpr-dispatch-binding-flows"),
        )
        task_row = re.search(
            r'<tr class="dpr-dispatch-task-row"[^>]*>.*?</tr>',
            html,
            re.S,
        )
        stage_row = re.search(
            r'<tr class="dpr-dispatch-stage-row"[^>]*>.*?</tr>',
            html,
            re.S,
        )
        self.assertIsNotNone(task_row)
        self.assertIsNotNone(stage_row)
        self.assertNotIn("分配积压数据", task_row.group(0))
        self.assertIn("分配积压数据", stage_row.group(0))
        self.assertEqual(4, len(architecture.STREAM_CAPACITY_BACKLOGS))
        self.assertEqual(
            3,
            len(architecture.STREAM_CAPACITY_BACKLOGS[0]["source_tasks"]),
        )
        self.assertTrue(
            all(
                item["input_rate"] > item["throughput"] and item["node"]
                for item in architecture.STREAM_CAPACITY_BACKLOGS
            )
        )
        self.assertEqual(3, len(architecture.UNBOUND_DATA_POOLS))
        self.assertTrue(
            all("筛选条件" in item["reason"] or "有效订阅" in item["reason"]
                for item in architecture.UNBOUND_DATA_POOLS)
        )
        self.assertEqual(
            {"采集", "导入"},
            {item["source"] for item in architecture.UNBOUND_DATA_POOLS},
        )
        self.assertEqual(3, len(architecture.REPROCESS_DATA_OVERVIEW))

    def test_old_allocation_management_is_kept_as_separate_menu(self):
        html = self.client.get("/data/allocations-legacy").get_data(as_text=True)
        self.assertIn("<h1>分配管理-旧</h1>", html)
        self.assertNotIn('href="/data/allocations-legacy"', html)
        for expected in (
            ">资源调度</span>",
            ">处理绑定</span>",
            ">数据再处理</span>",
            'id="drawerStreamReassign"',
            'id="drawerBindProcessingTask"',
            'id="drawerCreateReprocess"',
        ):
            self.assertIn(expected, html)

    def test_data_management_uses_one_list_with_data_source(self):
        html = self.client.get("/data/recordings").get_data(as_text=True)
        for expected in (
            "recording_id",
            "流程 ID",
            "请输入流程 ID",
            "数据来源",
            "视频",
            "上传状态",
            "采集结论",
            "采集人",
            "处理任务",
            "处理流程",
            "流程版本",
            "当前节点",
            "处理状态",
            "操作",
            "查看详情",
            "COL-2026-0718",
            "IMP-2026-0042",
            "厨房数据质检流程",
            "家居动作标注流程",
            "vendor-12-001",
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
            "采集人",
            "处理流程",
            "操作",
        )
        self.assertEqual(
            list(expected_headers),
            re.findall(r"<th>(.*?)</th>", table_head.group(1)),
        )
        self.assertIn('aria-label="三路采集视频"', html)
        self.assertIn(
            "/data/workbench/edit?mode=detail&amp;task=WB-2026-0922-AC"
            "&amp;recording_id=4057808&amp;source=data-management",
            html,
        )
        process_tree_head = re.search(
            r'<div class="dpr-process-tree">.*?<table>\s*'
            r"<thead><tr>(.*?)</tr></thead>",
            html,
            flags=re.S,
        )
        self.assertIsNotNone(process_tree_head)
        self.assertEqual(
            [
                "处理任务",
                "处理流程",
                "流程版本",
                "当前节点",
                "处理状态",
                "质检结论",
                "是否标注",
            ],
            re.findall(r"<th>(.*?)</th>", process_tree_head.group(1)),
        )
        self.assertIn(">是</span>", html)
        self.assertIn(">否</span>", html)
        self.assertNotIn("<th>流程实例</th>", html)
        self.assertNotIn("<th>实例状态</th>", html)

    def test_data_management_detail_action_opens_record_workbench(self):
        html = self.client.get(
            "/data/workbench/edit?mode=detail&task=WB-2026-0922-AC"
            "&recording_id=4057808&source=data-management"
        ).get_data(as_text=True)
        for expected in (
            "返回数据管理",
            "Recording 4057808",
            "UDAS-007",
            "刘素粉",
            "流程版本:",
            'id="wbxRecordFlowVersion"',
            '<option value="v3" selected>v3</option>',
            '<option value="v2">v2</option>',
            '<option value="v1">v1</option>',
            "wbSwitchRecordFlowVersion",
            "data-record-flow-version-value",
            ">轨迹</button>",
            ">质检</button>",
            ">标注</button>",
            ">日志</button>",
        ):
            self.assertIn(expected, html)

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
            'id="dprProcessInstanceMeta"',
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
            '"processing_task": "PROC-2026-0921"',
            '"instance_id": "run-4057808-1"',
            '"flow_version": "v3"',
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
            "今日已完成",
            "查看个人看板",
            "我的作业",
            "可领取任务池",
            "处理中",
            "暂离待继续",
            "驳回重做",
            '<span class="wb-job-label">处理任务</span>',
            '<span class="wb-job-label">当前节点</span>',
            "继续处理",
            "质检复核任务池",
            "动作标注任务池",
            "内部验收任务池",
            "最长滞留",
            "进入任务池",
            "/data/workbench/pools/POOL-QUALITY-REVIEW",
        ):
            self.assertIn(expected, workbench)
        self.assertNotIn('<span class="wb-job-label">数据 ID</span>', workbench)
        self.assertNotIn("宁德项目", workbench)
        self.assertNotIn("本周完成任务量", workbench)
        self.assertNotIn("任务合格率", workbench)
        priorities = re.findall(
            r'data-pool-priority="(P\d)"',
            workbench,
        )
        self.assertEqual(["P0", "P0", "P1"], priorities)
        job_priorities = re.findall(
            r'data-job-priority="(P\d)"',
            workbench,
        )
        self.assertEqual(["P0", "P0", "P1"], job_priorities)
        self.assertTrue(all(task.get("stage") for task in toolchain_demo.WB_TASKS))
        self.assertTrue(all(task.get("user_group") for task in toolchain_demo.WB_TASKS))
        self.assertTrue(all(task.get("workbench") for task in toolchain_demo.WB_TASKS))
        self.assertTrue(all(task.get("task_name") for task in toolchain_demo.WB_TASKS))
        self.assertEqual(200, self.client.get("/data/task-pool").status_code)

        for task in toolchain_demo.WB_TASKS:
            response = self.client.get(f"/data/workbench/tasks/{task['id']}")
            self.assertEqual(200, response.status_code, task["id"])
        pool_home = self.client.get(
            "/data/workbench/pools/POOL-QUALITY-REVIEW"
        ).get_data(as_text=True)
        for expected in (
            "任务来源",
            "厨房采集数据质检任务",
            "三方导入数据抽检任务",
            "规则和优先级随选择切换",
            'name="task_id"',
            'placeholder="请输入任务 ID"',
            'type="radio" name="wbSourceTask"',
            "已选择",
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
            "领取优先级最高的数据",
            "按筛选条件开始处理",
            'action="/data/workbench/edit"',
            'name="task" value="WB-2026-0718-QC"',
        ):
            self.assertIn(expected, pool_home)
        self.assertNotIn("wb-condition-item", pool_home)
        self.assertNotIn("工作台版本", pool_home)
        self.assertIn("wb-task-config-grid", pool_home)

        workbench_v2 = self.client.get(
            "/data/workbench-v2"
        ).get_data(as_text=True)
        for expected in (
            'href="/data/workbench-v2/pools/POOL-E2E-ACCEPTANCE"',
            'href="/data/workbench-v2/pools/POOL-E2E-SUPPLIER-A"',
            'href="/data/workbench-v2/pools/POOL-E2E-GUAN"',
            "验收-端到端切分标注",
            "供应商 A",
            "光轮智能",
            'href="/data/workbench-v2/style-examples">样式示例</a>',
            "wb-v2-pool-foot",
            "wb-v2-priority-summary",
        ):
            self.assertIn(expected, workbench_v2)
        self.assertNotIn('class="wb-pool-stage"', workbench_v2)
        self.assertNotIn('class="wb-pool-priorities"', workbench_v2)
        self.assertNotIn("端到端切分标注 · 内部验收</span>", workbench_v2)
        self.assertIn(
            ".wb-v2-pool-foot{display:flex;align-items:center;"
            "justify-content:flex-end;gap:7px}",
            workbench_v2,
        )
        self.assertNotIn("grid-template-columns:1fr auto 1fr", workbench_v2)

        quality_pool_v2 = self.client.get(
            "/data/workbench-v2/pools/POOL-QUALITY-REVIEW"
        ).get_data(as_text=True)
        for expected in (
            'href="/data/workbench-v2"',
            "筛选条件",
            "处理规则",
            "质检规则",
            'name="rule" form="wbFilterForm" required',
            "请选择质检规则",
            "var details=document.getElementById('wbRuleDetails')",
            "wb-v2-pool-home",
            "wb-filter-config",
            "wb-rule-config",
        ):
            self.assertIn(expected, quality_pool_v2)
        self.assertNotIn('<section class="wb-task-config wb-source-section">', quality_pool_v2)
        self.assertNotIn('<div class="wb-selected-source">', quality_pool_v2)
        self.assertNotIn("<th>流程 / 节点</th>", quality_pool_v2)
        self.assertNotIn("厨房数据质检流程 v3", quality_pool_v2)
        self.assertNotIn("领取优先级最高的数据", quality_pool_v2)
        self.assertNotIn("通用质检规则 v1", quality_pool_v2)
        self.assertNotIn("严格质量规则 v2", quality_pool_v2)

        annotation_pool_v2 = self.client.get(
            "/data/workbench-v2/pools/POOL-E2E-SUPPLIER-A"
        ).get_data(as_text=True)
        for expected in (
            "标注规则",
            "请选择标注规则",
            "端到端切分标注规则",
            "<h2>供应商 A 任务池</h2>",
        ):
            self.assertIn(expected, annotation_pool_v2)
        self.assertNotIn("通用动作标注规则", annotation_pool_v2)
        self.assertNotIn("精细动作标注规则", annotation_pool_v2)
        self.assertNotIn("失误标准", annotation_pool_v2)
        self.assertNotIn("不合格标准", annotation_pool_v2)
        self.assertNotIn("<th>流程 / 节点</th>", annotation_pool_v2)
        self.assertNotIn("家居动作标注流程 v2", annotation_pool_v2)
        self.assertNotIn("从多个处理任务统一领取数据", annotation_pool_v2)
        self.assertNotIn("最高 P0", annotation_pool_v2)
        self.assertNotIn('id="wbCollector"', annotation_pool_v2)
        self.assertNotIn('id="wbSupplier"', annotation_pool_v2)

        for expected in (
            "dpr-wb2-items-list",
            "dpr-wb2-items-table",
            "端到端切分标注流程",
            "供应商抽验",
            "供应商复核",
            "内部验收",
            "供应商验收",
            "recording_id",
            "流程 ID",
            "流程名称",
            "当前节点",
            "来源节点",
            "来源操作",
            "当前轮次",
            "说明",
            "dprWb2FlowFilter",
            "dprWb2NodeFilter",
            "dprWb2RecordingFilter",
            "dprWb2OperationFilter",
            "dprWb2Sort",
            "dprWb2SortDirection='asc'",
            "dpr-wb2-pagination",
            "10 条/页",
            "dprWb2PageSize=10",
            "dprWb2RenderPagination",
            "dprWb2GoToPage",
            "dprWb2ChangePage",
            ">操作</th>",
            ">处理</a>",
            "WB-E2E-SUPPLIER-A",
            '"source_operation": "提交"',
            '"source_operation": "驳回"',
            '"current_round": "第 2 轮"',
            "&entry=todo",
        ):
            self.assertIn(expected, workbench_v2)
        self.assertNotIn("dpr-wb2-two-col", workbench_v2)
        self.assertNotIn("dprSelectWorkbenchNode", workbench_v2)
        self.assertNotIn("dprWb2ItemsCount", workbench_v2)
        self.assertNotIn("9 个待办项", workbench_v2)
        self.assertNotIn("继续处理", workbench_v2)
        self.assertNotIn("最近操作人", workbench_v2)
        self.assertIn("更新时间", workbench_v2)
        self.assertIn("dprWb2Sort(&quot;updated_at&quot;)", workbench_v2)
        self.assertIn("dprWb2SortKey='updated_at'", workbench_v2)
        self.assertNotIn('<div class="dpr-wb2-items-toolbar-head"><b>待办项</b>', workbench_v2)
        for removed_operation in ("退回修改", "验收驳回", "补充说明"):
            self.assertNotIn(removed_operation, workbench_v2)
        node_operation_pairs = set(
            re.findall(
                r'"source_node": "([^"]+)", "source_operation": "([^"]+)"',
                workbench_v2,
            )
        )
        self.assertEqual(
            {
                ("供应商复核", "驳回"),
                ("供应商抽验", "提交"),
                ("供应商验收", "提交"),
                ("供应商验收", "驳回"),
            },
            node_operation_pairs,
        )

        action_workbench = self.client.get(
            "/data/workbench/edit?task=WB-2026-0922-LB&rule=通用动作标注规则%20v1%EF%BC%88%E5%8A%A8%E4%BD%9C%E6%A0%87%E6%B3%A8%20A%2FB%2FC%2FD%2FZ%EF%BC%89"
        ).get_data(as_text=True)
        self.assertIn("动作标注 · A/B/C/D/Z", action_workbench)
        self.assertIn("动作元素", action_workbench)
        self.assertIn("动作描述", action_workbench)

        semantic_workbench = self.client.get(
            "/data/workbench/edit?task=WB-2026-0922-LB&rule=精细动作标注规则%20v2%EF%BC%88%E8%AF%AD%E4%B9%89%E6%A0%87%E6%B3%A8%20E%2FF%2FG%EF%BC%89"
        ).get_data(as_text=True)
        self.assertIn("语义标注 · E/F/G", semantic_workbench)
        self.assertIn("lab-semantic-row", semantic_workbench)
        self.assertIn("lab-semantic-editor-cell", semantic_workbench)
        self.assertIn(
            ".lab-semantic-editor-cell { display:flex; align-items:center;",
            semantic_workbench,
        )
        self.assertNotIn("动作元素</th>", semantic_workbench)

        filtered_pool = self.client.get(
            "/data/workbench/pools/POOL-QUALITY-REVIEW?task_id=0930"
        ).get_data(as_text=True)
        self.assertIn("三方导入数据抽检任务", filtered_pool)
        self.assertNotIn("厨房采集数据质检任务", filtered_pool)
        self.assertIn(
            'name="task" value="WB-2026-0930-REVIEW"',
            filtered_pool,
        )

        acceptance_pool = self.client.get(
            "/data/workbench/pools/POOL-INTERNAL-ACCEPTANCE"
        ).get_data(as_text=True)
        self.assertIn("家居动作标注验收任务", acceptance_pool)
        self.assertIn("评测集入湖终验任务", acceptance_pool)

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
            'class="pd-dashboard"',
            "pd-stage-scroll",
            "height:calc(100vh - 112px)",
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
                "端到端切分标注流程",
                "业务环节",
                "启用",
                "详情",
                "编辑",
                "启用",
                "停用",
                "新增流程",
            ),
            "/data/runs": (
                "执行记录",
                "流程执行记录",
                "节点执行记录",
                "run-moz1-0921",
                "PROC-2026-0921",
                "pv.capture-to-dataset@7",
                "nr-0921-align-001",
                "流程版本",
                "节点版本",
                "输入 → 输出",
                "Attempt 3",
                "节点日志",
            ),
            "/data/operators": (
                "算子管理",
                "算子名称",
                "端到端切分标注处理算子",
            ),
        }
        for path, expected_values in requirements.items():
            html = self.client.get(path).get_data(as_text=True)
            for expected in expected_values:
                with self.subTest(path=path, expected=expected):
                    self.assertIn(expected, html)
        operator_html = self.client.get("/data/operators").get_data(as_text=True)
        self.assertNotIn("+ 新建算子", operator_html)
        self.assertNotIn("openOpDetail('op_e2e_segment_annotation')", operator_html)
        self.assertIn("<b>端到端切分标注处理算子</b>", operator_html)
        pipeline_html = self.client.get("/data/pipelines").get_data(as_text=True)
        self.assertEqual(
            2,
            pipeline_html.count("<td><b>端到端切分标注流程"),
        )
        self.assertIn("端到端切分标注流程（草稿）", pipeline_html)
        self.assertNotIn("<th>流程结构</th>", pipeline_html)
        self.assertNotIn("<th>周期调度数</th>", pipeline_html)
        for removed_pipeline in (
            "标准训练数据流水线",
            "多级质检复核流程",
            "数据验收流程",
            "双轮人工质检流程",
            "双轮人工标注流程",
        ):
            self.assertNotIn(removed_pipeline, pipeline_html)
        self.assertIn('name="stage"', pipeline_html)
        self.assertIn("全部业务环节", pipeline_html)
        self.assertNotIn('data-base="算子"', pipeline_html)
        self.assertNotIn("输入 / 输出契约", pipeline_html)
        self.assertNotIn("input → 节点 → output", pipeline_html)
        self.assertNotIn("openRun(", pipeline_html)
        runs_html = self.client.get("/data/runs").get_data(as_text=True)
        self.assertNotIn("手动触发", runs_html)
        self.assertNotIn("定时触发", runs_html)
        self.assertNotIn("发起运行", runs_html)
        self.assertNotIn("<th>产出数据集</th>", runs_html)
        self.assertNotIn("<th>所属流程运行</th>", runs_html)
        self.assertNotIn("<th>执行器 / 人工任务</th>", runs_html)
        self.assertNotIn("<th>输入</th>", runs_html)
        self.assertNotIn("<th>输出</th>", runs_html)
        self.assertIn('id="dpr-execution-run-table"', runs_html)
        self.assertIn('id="dpr-node-run-table"', runs_html)
        self.assertIn("dpr-list-tab-card dpr-execution-tabbar", runs_html)
        self.assertNotIn("dpr-execution-shell", runs_html)
        self.assertEqual(
            2,
            len(re.findall(
                r'<button[^>]+data-execution-tab="(?:flow|node)"',
                runs_html,
            )),
        )
        self.assertIn("dprSwitchExecutionTab", runs_html)
        self.assertIn("dprOpenNodeRuns", runs_html)
        self.assertIn("dprFilterExecutionRuns", runs_html)

    def test_processing_and_data_views_link_to_execution_records(self):
        processing_html = self.client.get("/data/processing-tasks").get_data(as_text=True)
        task_html = self.client.get("/data/tasks/PROC-2026-0921").get_data(as_text=True)
        data_html = self.client.get("/data/recordings").get_data(as_text=True)

        self.assertNotIn('/data/runs?task=PROC-2026-0921', processing_html)
        self.assertIn(
            '/data/runs?task=PROC-2026-0921&amp;recording=4057808',
            task_html,
        )
        self.assertIn(
            '/data/runs?task=PROC-2026-0921&amp;recording=4057808',
            data_html,
        )

        annotation_html = self.client.get(
            "/data/pipelines?stage=标注"
        ).get_data(as_text=True)
        self.assertIn("端到端切分标注流程", annotation_html)
        self.assertNotIn("双轮人工标注流程", annotation_html)
        self.assertNotIn("多级质检复核流程", annotation_html)

        view_html = self.client.get(
            "/data/pipelines/pl3q?mode=view"
        ).get_data(as_text=True)
        self.assertIn("查看工作流: 多级质检复核流程", view_html)
        self.assertIn("wf-stage view-only", view_html)
        self.assertIn('href="/data/pipelines/pl3q">编辑</a>', view_html)

    def test_processing_flow_examples_match_supplied_workflows(self):
        requirements = {
            "/data/pipelines/pl3q": (
                'data-processing-flow="pl3q"',
                "多级质检复核流程",
                "自动化质检",
                "抽检复核",
                "供应商复核",
                "申诉复核",
            ),
            "/data/pipelines/pl3a": (
                'data-processing-flow="pl3a"',
                "端到端切分标注流程",
                "端到端切分",
                "供应商抽验",
                "供应商复核",
                "内部验收",
            ),
            "/data/pipelines/pl3v": (
                'data-processing-flow="pl3v"',
                "数据验收流程",
                "验收",
            ),
            "/data/pipelines/pl4q": (
                'data-processing-flow="pl4q"',
                "双轮人工质检流程",
                "质检",
                "抽检",
            ),
            "/data/pipelines/pl4a": (
                'data-processing-flow="pl4a"',
                "双轮人工标注流程",
                "标注",
                "抽验",
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
            self.assertIn('id="wfCanvas"', html)
            self.assertIn('<div id="wfFrames"></div>', html)
            self.assertIn("flow-input", html)
            self.assertIn("flow-output", html)
            self.assertIn('data-port="branch"', html)
            self.assertIn("wf-condition-head", html)
            self.assertIn("wf-condition-branch-list", html)
            self.assertIn(".wf-node.automatic", html)
            self.assertIn('data-node-type="human"', html)
            self.assertIn('data-node-type="automatic"', html)
            self.assertIn('data-node-type="condition"', html)
            self.assertIn("人工节点", html)
            self.assertIn("自动化节点", html)
            self.assertIn("条件节点", html)

        for pipeline_id in ("pl3q", "pl3a", "pl3v", "pl4q", "pl4a"):
            pipeline = next(
                item for item in data_platform.PIPELINES if item["id"] == pipeline_id
            )
            nodes, edges, frames = data_platform._processing_canvas_payload(pipeline)
            self.assertEqual([], frames)
            self.assertTrue(nodes)
            self.assertEqual("flow-input", nodes[0]["id"])
            self.assertEqual("flow-output", nodes[-1]["id"])
            for condition_node in (
                node for node in nodes if node["kind"] == "condition"
            ):
                self.assertTrue(
                    any(
                        edge["from"] == condition_node["id"]
                        and edge.get("fromPort") == "branch-0"
                        for edge in edges
                    ),
                    "条件节点的首个分支必须有独立出口",
                )
                self.assertTrue(
                    all(
                        rule.get("operator")
                        for branch in condition_node.get("branches", [])
                        for rule in branch.get("rules", [])
                    ),
                    "条件规则必须保存筛选项、操作符和值三元组",
                )
                self.assertTrue(
                    all(branch.get("logic") == "or" for branch in condition_node.get("branches", [])),
                    "同一 IF 内的规则必须标记为 OR 逻辑",
                )
                self.assertFalse(
                    any(
                        edge["from"] == condition_node["id"]
                        and edge.get("toPort", "").startswith("branch-in-")
                        for edge in edges
                    ),
                    "所有分支必须汇入 end 的同一个入口",
                )
                self.assertTrue(
                    any(
                        edge["from"] == condition_node["id"]
                        and edge["to"] == "flow-output"
                        and edge.get("fromPort") == "branch"
                        and edge.get("branch") == "no"
                        for edge in edges
                    ),
                    "条件节点的否分支必须默认连接流程输出",
                )

    def test_automatic_pipelines_follow_business_flows_without_stage_frames(self):
        list_html = self.client.get("/data/pipelines").get_data(as_text=True)
        self.assertIn("端到端切分标注流程", list_html)
        for hidden_flow in (
            "多级质检复核流程",
            "数据验收流程",
            "双轮人工质检流程",
            "双轮人工标注流程",
            "标准训练数据流水线",
            "DAgger 数据流水线",
        ):
            self.assertNotIn(hidden_flow, list_html)

        expected_nodes = {"pl1": 5, "pl2": 2}
        for pipeline_id, node_count in expected_nodes.items():
            pipeline = next(
                item for item in data_platform.PIPELINES if item["id"] == pipeline_id
            )
            nodes, edges, frames = data_platform._processing_canvas_payload(pipeline)
            self.assertEqual([], frames)
            self.assertEqual(node_count + 2, len(nodes))
            self.assertEqual(node_count + 1, len(edges))
            self.assertTrue(
                all(
                    node["kind"] == "automatic"
                    for node in nodes
                    if node["kind"] not in ("flow-input", "flow-output")
                )
            )

            html = self.client.get(f"/data/pipelines/{pipeline_id}").get_data(
                as_text=True
            )
            self.assertIn(
                f'data-processing-flow="{pipeline_id}"',
                html,
            )
            self.assertIn("flow-input", html)
            self.assertIn("flow-output", html)
            self.assertIn('<div id="wfFrames"></div>', html)

    def test_processing_flow_phase_and_node_configuration(self):
        html = self.client.get("/data/pipelines/pl3q").get_data(as_text=True)
        for expected in (
            "节点名称",
            "标识",
            "描述",
            "分支设置",
            "ELSE · 其他",
            "操作符",
            "或（OR）",
            "供应商",
            "质检结论",
            "添加条件与比例",
            "wfConditionBranches",
            "wfAddBranchRule",
            "wf-branch-rule-head",
            "wf-branch-operator",
            "wf-branch-logic",
            "可用操作",
            "提交",
            "暂离",
            "驳回",
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
        self.assertNotIn("查看工作台配置", html)
        self.assertNotIn('<div class="ms-wrap wf-user-group-select"', html)
        self.assertIn('id="wfhAllowedActions"', html)
        self.assertIn("请至少选择一个可用操作", html)
        self.assertIn("background:transparent", html)
        self.assertNotIn("示例：质检结论", html)
        self.assertNotIn("sample_rate(", html)
        self.assertNotIn("工作台工作区组件", html)
        self.assertNotIn("工作台版本", html)
        self.assertNotIn("工作台的布局和组件由", html)
        self.assertNotIn("同一用户组关联的节点任务进入同一个任务池", html)
        self.assertNotIn('<div class="wf-cfg-sec">驳回设置</div>', html)
        self.assertNotIn("<span>支持驳回</span>", html)
        self.assertNotIn("已选择 '+names.length+' 个用户组", html)
        self.assertIn("names.join('、')", html)
        self.assertIn("(disabled.indexOf(item)>=0?' disabled':'')", html)
        self.assertNotIn('id="wfVersionSelect"', html)
        self.assertNotIn("wf-version-switch", html)
        self.assertIn('id="wfEffectiveTag"', html)
        self.assertIn(">启用</span>", html)
        self.assertNotIn("wf-hint", html)
        self.assertNotIn("input 连接上游", html)
        self.assertIn("(isUserGroup?'radio':'checkbox')", html)
        self.assertIn('name="wfhUserGroup"', html)
        self.assertNotIn("用户组（多选）", html)
        self.assertIn(">发布</button>", html)
        self.assertIn("发布后不可修改，确认发布？", html)
        self.assertIn("onclick=\"wfConfirmPublish()\"", html)
        self.assertNotIn('id="scheduleDrawer"', html)
        self.assertNotIn('id="runDrawer"', html)
        self.assertNotIn(">&#9201; 周期调度</button>", html)
        self.assertNotIn(">&#9654; 执行</button>", html)
        # The canvas now routes edges with compact orthogonal paths rather than
        # the previous long detour below every node.
        self.assertIn("Math.abs(t.y-s.y)<2", html)
        self.assertIn("var middle=t.x>=s.x?(s.x+t.x)/2:s.x+42", html)
        self.assertNotIn("wf-cond-percent", html)
        self.assertIn('<div class="wf-cfg-sec">处理人</div>', html)
        self.assertNotIn('name="wfhAssigneeType"', html)
        self.assertNotIn('<div class="wf-human-label">处理人类型</div>', html)
        self.assertIn("处理人分配", html)
        self.assertIn('value="task_custom"', html)
        self.assertIn('value="inherit"', html)
        self.assertIn("可选择任意前序人工节点", html)
        self.assertNotIn("(item.assigneeType||'supplier')===type", html)
        self.assertNotIn("处理轮次", html)
        self.assertNotIn('id="wfhRounds"', html)
        self.assertNotIn("添加环节", html)
        self.assertNotIn("所属环节", html)
        self.assertNotIn("data-phase-type=", html)
        self.assertIn('id="wfhRejectEnabled"', html)
        self.assertIn('id="wfhRejectPanel"', html)
        human_start = html.index('<div id="wfHumanConfig"')
        condition_start = html.index('<div id="wfConditionNodeConfig"')
        generic_start = html.index('<div id="wfGenericConfig"')
        generic_end = html.index('<div class="wf-config-foot">', generic_start)
        human_config = html[human_start:condition_start]
        condition_config = html[condition_start:generic_start]
        automatic_config = html[generic_start:generic_end]
        self.assertNotIn("进入条件", human_config)
        self.assertNotIn("进入比例", human_config)
        self.assertIn("分支设置", condition_config)
        self.assertIn("操作符", condition_config)
        self.assertIn("或（OR）", condition_config)
        self.assertIn('id="wfConditionBranches"', condition_config)
        self.assertNotIn("ELIF", condition_config)
        self.assertIn("ELSE · 其他", condition_config)
        self.assertNotIn('<span class="wf-sec-tag ro">默认不限制</span>', html)
        self.assertNotIn('<span class="wf-sec-tag ro">默认 100%</span>', html)
        self.assertNotIn('id="wfhRatioAdvancedToggle"', html)
        self.assertNotIn('id="wfhRatioConfigModes"', html)
        self.assertNotIn("wfRatioConfigMode", html)
        self.assertNotIn('onclick="wfAddBranch()"', html)
        self.assertIn("wfAddBranchRule", html)
        for expected in (
            'id="wfaName"',
            'id="wfaIdent"',
            'id="wfaDesc"',
            'id="wfaOperator"',
            "节点名称",
            "节点 ID",
            "节点描述",
            "执行算子",
        ):
            self.assertIn(expected, automatic_config)
        self.assertEqual(1, automatic_config.count('class="wf-cfg-sec"'))
        for removed in (
            'id="wfcImage"',
            'id="wfcScript"',
            'id="wfcParamsEdit"',
            'id="wfcReturns"',
            "运行环境",
            "出入参",
        ):
            self.assertNotIn(removed, automatic_config)
        self.assertIn("端到端切分标注处理算子", html)
        self.assertIn(
            "config.classList.toggle('human-mode',human||condition||automatic)",
            html,
        )
        self.assertIn("n.operatorId=operatorId", html)

    def test_workbench_management_only_shows_workbench_list(self):
        html = self.client.get("/data/workbench-management").get_data(as_text=True)
        for expected in (
            "工作台管理",
            'id="workbenchFilterName"',
            ">工作台名称</label>",
            ">清空</button>",
            ">查询</button>",
            'id="dpr-workbench-table"',
            "工作台 ID",
            "业务环节",
            "草稿",
            "启用",
            "停用",
            "质检工作台",
            "动作标注工作台",
            "语义标注工作台",
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
            "submit_actions",
            "reject_submit_actions",
            "/data/workbench-management/preview/quality",
            "/data/workbench-management/preview/annotation",
            "/data/workbench-management/preview/detail",
            "新建工作台",
            'id="drawerWorkbenchBuilder"',
            "保存草稿",
            "发布",
            "dprRenderWorkbenchPreview",
            'id="workbenchPreviewFrame"',
            'id="drawerComponentPreview"',
            'id="componentPreviewFrame"',
            "dprOpenComponentPreview",
            "高保真工作台预览",
            "dprFitPreviewFrame",
            "ResizeObserver",
            "通用动作标注规则 v1（动作标注 A/B/C/D/Z）",
            "精细动作标注规则 v2（语义标注 E/F/G）",
        ):
            self.assertIn(expected, html)
        workbench_table_start = html.index(
            '<table class="ant-table" id="dpr-workbench-table">'
        )
        self.assertIn('<div class="table-wrap">', html)
        self.assertIn(
            ".dpr-workbench-filter{margin-bottom:12px;padding:16px 18px}",
            html,
        )
        workbench_table_end = html.index("</table>", workbench_table_start)
        workbench_table = html[workbench_table_start:workbench_table_end]
        self.assertEqual(4, workbench_table.count("<th>"))
        self.assertNotIn("<th>组件数</th>", workbench_table)
        self.assertNotIn("<th>操作</th>", workbench_table)
        self.assertNotIn('class="det-tabs', html)
        self.assertNotIn(">组件</span>", html)
        self.assertNotIn('id="det-pane-component-config"', html)
        self.assertNotIn("组件列表", html)
        self.assertNotIn("复用线上工作台样式", html)
        self.assertNotIn("dpr-wb-preview-video", html)
        self.assertNotIn("dpr-wb-preview-workarea", html)

    def test_management_create_buttons_are_in_primary_title_rows(self):
        cases = (
            ("/data/pipelines", "流程管理", "新增流程"),
            ("/data/rules", "规则管理", "新增规则"),
            ("/data/user-groups", "用户组管理", "新增用户组"),
            ("/data/personnel", "人员管理", "+ 添加人员"),
        )
        for path, title, button_text in cases:
            html = self.client.get(path).get_data(as_text=True)
            with self.subTest(path=path):
                intro_start = html.index(
                    '<div class="dpr-intro dpr-intro-inline-action">'
                )
                title_row_start = html.index(
                    '<div class="dpr-intro-title-row">', intro_start
                )
                subtitle_start = html.index("<p>", title_row_start)
                title_row = html[title_row_start:subtitle_start]
                self.assertIn(f"<h1>{title}</h1>", title_row)
                self.assertIn(button_text, title_row)
                self.assertEqual(
                    1,
                    len(
                        re.findall(
                            rf">\s*{re.escape(button_text)}\s*</(?:a|button)>",
                            title_row,
                        )
                    ),
                )

    def test_workbench_management_annotation_previews_use_distinct_layouts(self):
        action_html = self.client.get(
            "/data/workbench-management/preview/annotation",
            query_string={
                "task": "WB-2026-0922-LB",
                "rule": "通用动作标注规则 v1（动作标注 A/B/C/D/Z）",
            },
        ).get_data(as_text=True)
        semantic_html = self.client.get(
            "/data/workbench-management/preview/annotation",
            query_string={
                "task": "WB-2026-0922-LB",
                "rule": "精细动作标注规则 v2（语义标注 E/F/G）",
            },
        ).get_data(as_text=True)

        self.assertIn("动作标注工作台", action_html)
        self.assertIn("动作元素", action_html)
        self.assertIn('data-component="action_element_editor"', action_html)
        self.assertNotIn('data-component="high_low_editor"', action_html)
        self.assertIn("语义标注工作台", semantic_html)
        self.assertIn("语义标注 · E/F/G", semantic_html)
        self.assertIn('data-component="high_low_editor"', semantic_html)
        self.assertIn("lab-semantic-row", semantic_html)

    def test_workbench_management_embeds_high_fidelity_component_aware_preview(self):
        response = self.client.get(
            "/data/workbench-management/preview/annotation"
            "?task=WB-2026-0922-LB&embed=1"
            "&components=basic_info,multi_view_video,annotation_segment_editor"
        )
        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        for expected in (
            '<body class="workbench-embed">',
            'id="workbench-embed-style"',
            'id="workbench-embed-script"',
            'class="lab-vid-grid"',
            'data-component="annotation_segment_editor"',
            'var selected = ["basic_info", "multi_view_video", "annotation_segment_editor"]',
            "document.querySelectorAll('[data-component]')",
        ):
            self.assertIn(expected, html)

        focus_html = self.client.get(
            "/data/workbench-management/preview/quality"
            "?task=WB-2026-0718-QC&embed=1&focus=quality_issue_editor"
        ).get_data(as_text=True)
        self.assertIn('var focus = "quality_issue_editor"', focus_html)
        self.assertIn("component-focus-mode", focus_html)
        self.assertIn("workbench-component-focus", focus_html)
        self.assertIn("workbench-component-wireframe", focus_html)
        self.assertIn(
            "element.contains(target) ||",
            focus_html,
        )
        self.assertIn(
            "target.contains(element)",
            focus_html,
        )

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
            self.assertNotIn(
                '<span class="wbx-module-title">操作</span>',
                html,
            )
            self.assertIn(
                ".wbx-operation-actions { width:100%; justify-content:center; }",
                html,
            )
            self.assertNotIn("submit.textContent", html)
            self.assertNotIn("wbx-action-divider", html)
            self.assertNotIn('data-workbench-module="log"', html)
            self.assertNotIn("workbenchLogModal", html)

    def test_main_configuration_pages_are_restored(self):
        requirements = {
            "/data/rules": (
                "规则管理",
                "端到端切分标注规则",
                "适用环节",
            ),
            "/data/scenes": ("场景管理", "场景名称", "新增场景"),
            "/data/tags": ("标签管理", "能力标签", "动作标签"),
        }
        for path, expected_values in requirements.items():
            html = self.client.get(path).get_data(as_text=True)
            for expected in expected_values:
                with self.subTest(path=path, expected=expected):
                    self.assertIn(expected, html)
        rules_html = self.client.get("/data/rules").get_data(as_text=True)
        for expected in (
            'id="ruleFilterName"',
            'id="ruleFilterStage"',
            'id="ruleFilterOwner"',
            ">规则名称</label>",
            ">适用环节</label>",
            ">创建人</label>",
            ">清空</a>",
            ">查询</button>",
        ):
            self.assertIn(expected, rules_html)
        self.assertNotIn('class="tm-tabs"', rules_html)
        self.assertNotIn("执行方式", rules_html)
        for removed in (
            "缺帧检测规则",
            "图像模糊度检测",
            "动作分段必备字段",
            "关键帧标注完整性",
            "Episode 时长阈值",
            "切分起止动作检测",
            "标注一致性校验",
            "终验抽检比例",
            "<th>标注方式</th>",
            "<th>规则配置</th>",
            "<th>关联工作台</th>",
        ):
            self.assertNotIn(removed, rules_html)
        self.assertEqual(1, rules_html.count('class="mono">RL-009</td>'))
        self.assertIn(">标注<", rules_html)
        filtered_rules = self.client.get(
            "/data/rules?rule_name=不存在的规则"
        ).get_data(as_text=True)
        self.assertNotIn("端到端切分标注规则", filtered_rules)

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
            "新增一级标签",
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

    def test_v2_annotation_explanation_is_inside_annotation_tab(self):
        review_html = self.client.get(
            "/data/workbench-v2/edit?task=WB-E2E-REVIEW&recording_id=recording_e2e_004"
        ).get_data(as_text=True)
        self.assertIn(">说明</b>", review_html)
        self.assertNotIn(">描述</b>", review_html)
        self.assertIn("请输入驳回说明", review_html)
        self.assertNotIn("请输入驳回备注", review_html)
        self.assertIn(
            "<span>时间</span><span>操作人</span><span>操作</span><span>节点</span><span>说明</span>",
            review_html,
        )
        self.assertIn(">驳回</span><span>供应商复核</span>", review_html)
        self.assertIn(">提交</span><span>供应商抽验</span>", review_html)
        self.assertNotIn("打开前序节点", review_html)
        self.assertNotIn("查看语义标注结果", review_html)
        explanation_pos = review_html.index('class="wbx-description-module"')
        annotation_pane_pos = review_html.index(
            'data-detail-pane="annotation" data-component="annotation_segment_editor"'
        )
        toolbar_pos = review_html.index('class="lab-tools-card"')
        self.assertGreater(explanation_pos, annotation_pane_pos)
        self.assertLess(explanation_pos, toolbar_pos)

        supplier_html = self.client.get(
            "/data/workbench-v2/edit?task=WB-E2E-SUPPLIER-A&recording_id=recording_e2e_001"
        ).get_data(as_text=True)
        self.assertNotIn("wbOpenRejectDialog", supplier_html)
        self.assertNotIn(">驳回</span><span>供应商抽验</span>", supplier_html)
        self.assertNotIn(">上一条</button>", supplier_html)
        self.assertNotIn(">下一条</button>", supplier_html)

        todo_html = self.client.get(
            "/data/workbench-v2/edit?task=WB-E2E-SUPPLIER-A&recording_id=recording_e2e_001&entry=todo"
        ).get_data(as_text=True)
        self.assertIn(">上一条</button>", todo_html)
        self.assertIn(">下一条</button>", todo_html)
        self.assertIn("wbx-item-navigation", todo_html)

        acceptance_html = self.client.get(
            "/data/workbench-v2/edit?task=WB-E2E-ACCEPTANCE&recording_id=recording_e2e_007"
        ).get_data(as_text=True)
        self.assertIn(">驳回</span><span>内部验收</span>", acceptance_html)
        self.assertIn(">提交</span><span>内部验收</span>", acceptance_html)

    def test_v2_workbench_style_examples_cover_five_variants(self):
        examples_html = self.client.get(
            "/data/workbench-v2/style-examples"
        ).get_data(as_text=True)
        for expected in (
            "工作台样式示例",
            "供应商抽验－首次提交",
            "供应商抽验－被驳回后处理",
            "供应商复核 / 供应商验收 / 内部验收－首次提交",
            "供应商复核 / 供应商验收－驳回重新提交处理",
            "供应商复核 / 供应商验收 / 内部验收－被驳回后处理",
            "wbSwitchStyleExample",
            "完整工作台样式预览",
            "仅切换标注、错误原因和提交 / 驳回规则",
        ):
            self.assertIn(expected, examples_html)
        self.assertEqual(5, examples_html.count('data-style-tab="'))
        self.assertEqual(5, examples_html.count('data-style-src="'))
        self.assertIn('id="wbStyleFrame"', examples_html)
        for style_id in ("one", "two", "three", "four", "five"):
            self.assertIn(f"style={style_id}", examples_html)

        style_expectations = {
            "one": (False, False, False),
            "two": (True, False, True),
            "three": (True, True, False),
            "four": (True, True, False),
            "five": (True, True, True),
        }
        for style_id, (has_reason, allow_reject, submit_reason) in style_expectations.items():
            style_html = self.client.get(
                "/data/workbench-v2/edit?task=WB-E2E-SUPPLIER-A&mode=annotation"
                f"&rule=端到端切分标注规则&style={style_id}&style_preview=1"
            ).get_data(as_text=True)
            for component in (
                "lab-meta",
                "lab-vid-grid",
                "lab-tools-card",
                "lab-semantic-row",
                "lab-semantic-editor-cell",
                "wbx-execution",
            ):
                self.assertIn(component, style_html)
            self.assertIn("<b>指令</b>", style_html)
            self.assertNotIn("第1版", style_html)
            self.assertNotIn('<span class="lbl">状态:</span>', style_html)
            self.assertIn(
                "<span>时间</span><span>操作人</span><span>操作</span><span>节点</span><span>说明</span>",
                style_html,
            )
            self.assertIn("overflow-y:auto", style_html)
            detail_tabs_pos = style_html.index(
                '<div class="wbx-detail-tabs"'
            )
            header_pos = style_html.index(
                '<div class="wbx-workbench-header">',
                detail_tabs_pos,
            )
            instruction_pos = style_html.index(
                'class="wbx-instruction"', header_pos
            )
            video_pos = style_html.index('class="lab-vid-grid"', instruction_pos)
            timeline_pos = style_html.index(
                'class="lab-tools-card"', video_pos
            )
            execution_pos = style_html.index(
                'class="wbx-execution"', timeline_pos
            )
            self.assertNotIn("wbx-sticky-workbench-header", style_html)
            self.assertNotIn("wbx-sticky-annotation-tools", style_html)
            self.assertLess(detail_tabs_pos, header_pos)
            self.assertLess(header_pos, instruction_pos)
            self.assertLess(instruction_pos, video_pos)
            self.assertLess(video_pos, timeline_pos)
            self.assertLess(timeline_pos, execution_pos)
            if has_reason:
                self.assertLess(style_html.index(">时长</th>"), style_html.index(">错误原因</th>"))
                self.assertLess(style_html.index(">错误原因</th>"), style_html.index(">操作</th>"))
            else:
                self.assertNotIn(">错误原因</th>", style_html)
            self.assertEqual(allow_reject, "wbOpenRejectDialog" in style_html)
            self.assertEqual(submit_reason, "wbSubmitDialog" in style_html)
            readonly_style = style_id in {"three", "four", "five"}
            self.assertEqual(
                not readonly_style,
                '<div class="lab-tl-seg orange"' in style_html,
            )
            self.assertEqual(
                not readonly_style,
                '<div class="lab-annotation-toolbox">' in style_html,
            )
            if style_id == "one":
                self.assertNotIn(
                    '<section class="wbx-description-module"',
                    style_html,
                )
            if style_id == "five":
                self.assertIn(
                    '<section class="wbx-description-module"',
                    style_html,
                )

        style_five_html = self.client.get(
            "/data/workbench-v2/edit?task=WB-E2E-ACCEPTANCE"
            "&recording_id=recording_e2e_007&mode=annotation"
            "&rule=端到端切分标注规则&style=five&style_preview=1"
        ).get_data(as_text=True)
        self.assertIn('<section class="wbx-description-module"', style_five_html)
        self.assertIn("内部验收发现标注结果需补充确认", style_five_html)

        v2_workbench = self.client.get(
            "/data/workbench-v2/edit?task=WB-E2E-SUPPLIER-A&recording_id=recording_e2e_001"
        ).get_data(as_text=True)
        self.assertNotIn("/data/workbench-v2/style-examples", v2_workbench)
        legacy_workbench = self.client.get(
            "/data/workbench/edit?task=WB-2026-0922-LB"
        ).get_data(as_text=True)
        self.assertNotIn("/data/workbench-v2/style-examples", legacy_workbench)

    def test_project_management_is_under_configuration_management(self):
        html = self.client.get("/data/projects").get_data(as_text=True)
        for expected in (
            "项目管理",
            "项目列表",
            "<th>项目名称</th>",
            "<th>项目描述</th>",
            "<th>负责人</th>",
            "预训练采集",
            "demo 项目",
            "宁德项目",
            "新增项目",
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
            "/data/user-groups": (
                "用户组管理",
                "用户组列表",
                "标注员用户组",
                "质检复核用户组",
                "关联任务池",
                "待领取",
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
        personnel_html = self.client.get("/data/personnel").get_data(as_text=True)
        self.assertNotIn(">用户组</span>", personnel_html)
        self.assertNotIn("用户组列表", personnel_html)
        user_group_html = self.client.get("/data/user-groups").get_data(as_text=True)
        self.assertIn('class="dpr-org-count"', user_group_html)
        self.assertIn('title="供应商 A：6 人；光轮智能：4 人"', user_group_html)
        self.assertIn(
            'aria-label="共 2 个组织；供应商 A：6 人；光轮智能：4 人">2</span>',
            user_group_html,
        )

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
            '[data-dataset-info-field="tags"] '
            ".dataset-tag-picker.readonly .dataset-tag-picker-control",
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
        self.assertIn(
            '[data-dataset-info-field="tags"] .dataset-tag-path-list',
            standalone_detail,
        )
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
            ">新增测试任务</button>",
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
        task_pool = self.client.get("/data/task-pool", follow_redirects=False)
        self.assertEqual(200, task_pool.status_code)
        self.assertIn("任务池", task_pool.get_data(as_text=True))

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
