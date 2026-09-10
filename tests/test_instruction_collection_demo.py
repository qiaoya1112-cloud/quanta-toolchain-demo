import unittest
import shutil
import subprocess
from pathlib import Path

import data_platform_refactor as architecture
from instruction_collection_demo import S026_MOCK_DATA
import toolchain_demo


class InstructionCollectionDemoTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed for browser-state checks")
    def test_browser_state_transitions_and_saved_data_migration(self):
        result = subprocess.run(
            ["node", str(Path(__file__).with_name("s026_browser_state.cjs"))],
            input=self.instruction_html,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    @classmethod
    def setUpClass(cls):
        cls.client = toolchain_demo.app.test_client()
        cls.instruction_html = cls.client.get("/data/instruction-management").get_data(as_text=True)
        cls.batch_response = cls.client.get(
            "/data/instruction-management/upload-batches", follow_redirects=False
        )
        cls.approval_html = cls.client.get(
            "/data/instruction-management/approval-tasks"
        ).get_data(as_text=True)
        cls.approval_detail_html = cls.client.get(
            "/data/instruction-management/approval-detail?id=AP260905002&mode=approve"
        ).get_data(as_text=True)
        cls.approval_view_html = cls.client.get(
            "/data/instruction-management/approval-detail?id=AP260905002&mode=view"
        ).get_data(as_text=True)
        cls.project_html = cls.client.get("/data/collection-plans").get_data(as_text=True)
        cls.supplier_plan_html = cls.client.get(
            "/data/collection-plans/assigned"
        ).get_data(as_text=True)
        cls.supplier_plan_detail_html = cls.client.get(
            "/data/collection-plans/assigned/detail?id=CP260001"
        ).get_data(as_text=True)
        cls.package_html = cls.client.get("/data/instruction-packages").get_data(as_text=True)
        cls.package_detail_html = cls.client.get(
            "/data/instruction-packages/detail?id=CIP2609070001"
        ).get_data(as_text=True)
        cls.project_detail_html = cls.client.get(
            "/data/collection-plans/detail?id=CP260001"
        ).get_data(as_text=True)
        cls.strategy_html = cls.client.get(
            "/data/collection-plans/strategies?id=CP260001"
        ).get_data(as_text=True)
        cls.supplier_html = cls.client.get(
            "/data/collection-plans/suppliers?id=CP260001"
        ).get_data(as_text=True)
        cls.plan_package_detail_html = cls.client.get(
            "/data/collection-plans/package-detail?plan=CP260001&package=CIP2609070001"
        ).get_data(as_text=True)
        cls.edge_html = cls.client.get("/data/edge-collection?project=CP260001").get_data(as_text=True)
        cls.edge_detail_html = cls.client.get(
            "/data/edge-collection/package-detail?project=CP260001&package=CIP2609090001"
        ).get_data(as_text=True)

    def test_route_uses_s026_information_architecture(self):
        self.assertEqual(200, self.client.get("/data/instruction-management").status_code)
        self.assertEqual(302, self.batch_response.status_code)
        self.assertTrue(
            self.batch_response.headers["Location"].endswith(
                "/data/instruction-management/approval-tasks"
            )
        )
        self.assertEqual(
            200, self.client.get("/data/instruction-management/approval-tasks").status_code
        )
        self.assertEqual(
            200, self.client.get("/data/instruction-management/approval-detail").status_code
        )
        self.assertEqual(200, self.client.get("/data/collection-plans").status_code)
        self.assertEqual(200, self.client.get("/data/collection-plans/assigned").status_code)
        self.assertEqual(
            200,
            self.client.get("/data/collection-plans/assigned/detail?id=CP260001").status_code,
        )
        self.assertEqual(200, self.client.get("/data/instruction-packages").status_code)
        self.assertEqual(200, self.client.get("/data/instruction-packages/detail").status_code)
        self.assertEqual(200, self.client.get("/data/collection-plans/detail").status_code)
        self.assertEqual(200, self.client.get("/data/collection-plans/strategies").status_code)
        self.assertEqual(200, self.client.get("/data/collection-plans/suppliers").status_code)
        self.assertEqual(200, self.client.get("/data/collection-plans/package-detail").status_code)
        self.assertEqual(200, self.client.get("/data/edge-collection").status_code)
        self.assertEqual(
            200, self.client.get("/data/edge-collection/package-detail").status_code
        )
        self.assertEqual("指令管理", architecture.PAGE_SPECS["instruction_management"]["title"])
        self.assertEqual("指令包管理", architecture.PAGE_SPECS["instruction_packages"]["title"])
        self.assertEqual("方案管理", architecture.PAGE_SPECS["collection_tasks"]["title"])
        self.assertEqual(
            "采集方案", architecture.PAGE_SPECS["supplier_collection_plans"]["title"]
        )
        self.assertNotIn("instruction_upload_batches", architecture.PAGE_SPECS)
        for html in (
            self.instruction_html,
            self.approval_html,
            self.approval_detail_html,
            self.package_html,
            self.package_detail_html,
            self.project_html,
            self.supplier_plan_html,
            self.supplier_plan_detail_html,
            self.project_detail_html,
            self.strategy_html,
            self.supplier_html,
            self.plan_package_detail_html,
            self.edge_html,
        ):
            self.assertIn("本地 Mock 数据", html)
            self.assertIn('class="s026-demo-tools"', html)
        legacy = self.client.get("/data/collection-tasks", follow_redirects=False)
        self.assertEqual(302, legacy.status_code)
        self.assertTrue(legacy.headers["Location"].endswith("/data/instruction-management"))
        legacy_plan = self.client.get(
            "/data/collection-projects/detail?id=CP260003", follow_redirects=False
        )
        self.assertEqual(302, legacy_plan.status_code)
        self.assertTrue(
            legacy_plan.headers["Location"].endswith(
                "/data/collection-plans/detail?id=CP260003"
            )
        )

    def test_instruction_approval_is_the_only_instruction_subpage(self):
        self.assertIn('class="s026-section-buttons"', self.instruction_html)
        self.assertIn("var S026_INSTRUCTION_SECTION='library'", self.instruction_html)
        self.assertIn(
            '<a class="s026-section-button s026-section-primary" href="/data/instruction-management/approval-tasks">指令审批</a>',
            self.instruction_html,
        )
        self.assertIn("s026-section-button.s026-section-primary", self.instruction_html)
        self.assertIn("<h1>指令审批</h1>", self.approval_html)
        self.assertIn(
            '<a class="s026-back-link" href="/data/instruction-management">‹ 返回</a>',
            self.approval_html,
        )
        self.assertNotIn('class="s026-section-buttons"', self.approval_html)
        self.assertNotIn(">指令上传</a>", self.instruction_html)
        self.assertNotIn(">指令库</a>", self.instruction_html)
        self.assertNotIn("集中检索和管理已完成审批", self.instruction_html)
        self.assertNotIn('class="s026-flow"', self.instruction_html)
        self.assertNotIn("1 上传指令表", self.instruction_html)
        self.assertNotIn('class="s026-view-tabs"', self.instruction_html)
        self.assertNotIn("统一查看指令、版本启用情况与采集进度。", self.instruction_html)

    def test_management_lists_share_the_same_workbench_structure(self):
        page_expectations = (
            (self.instruction_html, "s026QueryLibrary"),
            (self.approval_html, "s026QueryApprovals"),
            (self.package_html, "s026QueryPackageManagement"),
            (self.project_html, "s026QueryPlanList"),
        )
        for html, query_handler in page_expectations:
            with self.subTest(query_handler=query_handler):
                self.assertIn('class="s026-list-surface"', html)
                self.assertIn("s026-filter-panel", html)
                self.assertIn("s026-result-panel", html)
                self.assertIn(
                    f'onclick="{query_handler}()">查询</button>', html
                )
                self.assertNotIn("筛选条件变更后自动刷新", html)
        all_html = "".join(html for html, _ in page_expectations)
        for count_id in (
            "s026LibraryCount",
            "s026ApprovalCount",
            "s026GlobalPackageCount",
            "s026PlanCount",
        ):
            self.assertNotIn(f'id="{count_id}"', all_html)

    def test_management_filters_apply_only_from_query_buttons(self):
        html = self.approval_html
        for eager_handler in (
            'oninput="s026RenderLibrary()',
            'onchange="s026RenderLibrary()',
            'oninput="s026RenderApprovals()',
            'onchange="s026RenderApprovals()',
            'oninput="s026RenderPackageManagement()',
            'onchange="s026RenderPackageManagement()',
            'oninput="s026RenderPlanList()',
            'onchange="s026RenderPlanList()',
            'oninput="s026RenderPlanPackages()',
            'onchange="s026RenderPlanPackages()',
            'onchange="s026ApplyApprovalDetailFilters()',
            'oninput="s026FilterPackageCandidates()',
            'oninput="s026FilterPlanPackageCandidates()',
        ):
            self.assertNotIn(eager_handler, html)
        for query_handler in (
            "s026QueryLibrary",
            "s026QueryApprovals",
            "s026QueryPackageManagement",
            "s026QueryPlanList",
            "s026QueryPlanPackages",
            "s026ApplyApprovalDetailFilters",
            "s026FilterPackageCandidates",
            "s026FilterPlanPackageCandidates",
        ):
            self.assertIn(
                f'onclick="{query_handler}()">查询</button>', html
            )

    def test_core_instruction_lifecycle_is_interactive(self):
        for expected in (
            "上传指令表",
            "系统校验",
            "发起审批",
            "审批任务",
            "s026ValidateBatch",
            "s026CreateApproval",
            "s026CompleteApproval",
            "s026ToggleLibraryVersion",
            "发起后该指令表将不能删除，确认生成审批任务？",
        ):
            self.assertIn(expected, self.instruction_html + self.approval_html)
        self.assertNotIn(
            "发起后该上传批次将不能删除，确认生成审批任务？",
            self.approval_html,
        )

    def test_upload_flow_is_embedded_in_approval_page(self):
        for expected in (
            "支持 xlsx 格式，支持本地上传或拖拽上传；文件大小上限20M",
            "上传中",
            "校验中",
            "上传成功",
            "上传失败",
            "查看错误",
            "复制错误",
            "s026CopyUploadError",
            "s026LoadCompliantDemoFile",
            "s026LoadInvalidDemoFile",
            "载入合规文件",
            "载入非法文件",
            "第 3 行：指令 ID 为空",
            "第 5 行：指令版本号 V0 格式不合法",
            "第 8 行：道具字段超过 200 字符",
            'id="s026DrawerHeadActions"',
            "文件大小超过20M上限",
            "文件格式校验失败：仅支持 xlsx 格式",
            "已生成在线指令表",
            "当前状态为待审批",
            "status:'待审批'",
            "删除文件",
            'id="s026UploadConfirm" disabled',
            "s026CloseDrawer();s026Save()",
        ):
            self.assertIn(expected, self.approval_html)
        self.assertIn(
            '<button class="s026-btn primary s026-head-primary" type="button" onclick="s026OpenUpload()">上传指令表</button>',
            self.approval_html,
        )
        self.assertNotIn("载入演示文件", self.approval_html)
        self.assertNotIn(
            'class="s026-toolbar s026-list-toolbar s026-list-actionbar"',
            self.approval_html,
        )
        self.assertNotIn('data-instruction-pane="batches"', self.approval_html)
        self.assertNotIn("指令表列表", self.approval_html)
        self.assertNotIn("指令工作台</span><h2>指令审批", self.approval_html)
        self.assertIn(
            '</div><div class="s026-upload-error-detail" id="s026UploadErrorDetail">',
            self.approval_html,
        )
        self.assertIn(
            ".s026-drawer{width:min(560px,calc(100vw - 42px))}",
            self.approval_html,
        )

    def test_library_filters_columns_and_progress_follow_reviewed_contract(self):
        for expected in (
            "s026LibraryIdQuery",
            "s026LibraryNameQuery",
            "s026LibraryIteration",
            "s026LibraryScene",
            "s026LibraryZone",
            "s026LibraryStatus",
            "s026ResetLibraryFilter",
            "新建指令",
            "启用指令",
            "停用指令",
            "新建版本",
            "启用版本",
            "停用版本",
            "超出目标",
            "距目标",
        ):
            self.assertIn(expected, self.instruction_html)
        self.assertNotIn("更新日志", self.instruction_html)
        self.assertNotIn("s026OpenLibraryLog", self.instruction_html)
        self.assertIn(
            "<th>指令 ID</th><th>指令名称</th><th>指令迭代</th><th>场景</th><th>工作区</th>",
            self.instruction_html,
        )
        for expected in (
            "s026OpenDrawer",
            "s026CloseDrawer",
            "s026-drawer-mask",
            "s026-version-card",
            "s026-version-card-actions",
            "s026-version-card-identity",
            "s026-version-details",
            "s026-version-meta-row",
            "指令详情",
            "指令描述",
            "指令迭代",
            "目标态",
            "镜像",
            "难度",
            "道具",
            "采集进度",
        ):
            self.assertIn(expected, self.instruction_html)
        self.assertIn(
            """s026-version-card-identity">'+s026Status(version.status)+'<span class="s026-code">'+s026Esc(version.version)+'</span></div>""",
            self.instruction_html,
        )
        self.assertIn("s026MirrorValue(version)", self.instruction_html)
        self.assertNotIn("<h4>'+s026Esc(version.name)", self.instruction_html)
        self.assertNotIn('class="s026-drawer-summary"', self.instruction_html)
        self.assertIn('class="s026-table s026-fixed-actions"', self.instruction_html)
        self.assertEqual(18.5, S026_MOCK_DATA["library"][0]["collected"])
        self.assertGreater(
            S026_MOCK_DATA["library"][2]["collected"],
            S026_MOCK_DATA["library"][2]["target"],
        )

    def test_approval_list_and_detail_follow_reviewed_contract(self):
        for expected in (
            "s026ApprovalBatchQuery",
            "s026ApprovalResult",
            "s026ApprovalStatus",
            "s026ResetApprovalFilter",
            "指令表 ID",
            "指令版本总数",
            "审核人",
            "审核时间",
            "发布人",
            "操作时间",
            "上传人",
            "上传时间",
            "AP260905002",
            "mode=view",
            "mode=approve",
            ">查看</button>",
            ">删除</button>",
            ">发起审批</button>",
        ):
            self.assertIn(expected, self.approval_html)
        self.assertNotIn("s026ApprovalIdQuery", self.approval_html)
        self.assertNotIn("审批任务 ID", self.approval_html)
        self.assertNotIn("来源上传批次", self.approval_html)
        self.assertIn(
            "<th>指令表 ID</th><th>指令版本总数</th>", self.approval_html
        )
        for expected in (
            "场景",
            "工作区",
            "指令 ID",
            "指令名称",
            "指令版本号",
            "指令迭代",
            "目标态",
            "指令描述",
            "难度",
            "镜像",
            "目标采集时长",
            "道具",
            "审批结果",
            "不合格原因",
            "s026RenderApprovalDetail",
            "s026ApprovalDetailFilters",
            "s026ChangeApprovalDetailPage",
            "s026-pagination",
            "s026OpenReject",
            "选择不合格原因",
            "s026ConfirmReject",
            "s026ApprovalDetailVersion",
            "s026ApprovalDetailIteration",
            "s026ApprovalDetailDifficulty",
            "s026ApprovalDetailProps",
        ):
            self.assertIn(expected, self.approval_detail_html)
        self.assertTrue(
            all(
                version["decision"] == "审批合格"
                for version in S026_MOCK_DATA["approvals"][0]["versions"]
            )
        )
        self.assertIn("version.decision==='审批不合格'?", self.approval_detail_html)
        self.assertIn("s026-approval-result-cell", self.approval_detail_html)
        self.assertIn("s026-approval-action-cell", self.approval_detail_html)
        self.assertIn("s026MirrorValue(version)", self.approval_detail_html)
        self.assertNotIn("指令版本名称", self.approval_detail_html)
        self.assertIn("s026ApprovalProps", self.approval_detail_html)
        self.assertIn("s026ApprovalDecisionStatus", self.approval_detail_html)
        self.assertIn(">合格</button>", self.approval_detail_html)
        self.assertIn(">不合格</button>", self.approval_detail_html)
        self.assertNotIn('<div class="s026-approval-summary">', self.approval_detail_html)
        self.assertNotIn("<h2>审批任务 ", self.approval_detail_html)
        self.assertNotIn("审批模式", self.approval_detail_html)
        self.assertNotIn("只读模式", self.approval_detail_html)
        self.assertIn("actionHead=editable?'<th class=\"s026-approval-action-cell\">操作</th>':''", self.approval_view_html)
        self.assertIn("resultHead='<th class=\"s026-approval-result-cell'", self.approval_view_html)

    def test_collection_plan_list_and_detail_follow_pdf_contract(self):
        for expected in (
            "var S026_PAGE_MODE='plan-list'",
            "新建采集方案",
            'class="s026-btn edge" type="button" onclick="s026OpenEdgeApp()">端侧采集</button>',
            "s026PlanIdQuery",
            "s026PlanNameQuery",
            "s026PlanType",
            "s026PlanScene",
            "s026PlanStatusFilter",
            "<th>采集方案 ID</th><th>采集方案名称</th><th>采集方案类型</th><th>场景</th><th>状态</th><th>创建人及创建时间</th><th>操作</th>",
            "指令包采集",
            "configured:false",
            "&tab=basic",
            "s026CreatePlan",
            "id='CP26'+String(maxNumber+1).padStart(4,'0')",
            "s026RequestPlanStatus",
            "s026RequestPlanDelete",
            "s026SyncAllProjectMetrics",
            "/data/collection-plans/detail?id=",
        ):
            self.assertIn(expected, self.project_html)
        self.assertNotIn("自动暂停", self.project_html + self.strategy_html)
        self.assertNotIn(
            "无上线采集策略、无上线指令包或无启用供应商",
            self.project_html,
        )
        self.assertNotIn("采集方案版本</th>", self.project_html)
        self.assertNotIn("上线采集指令数", self.project_html)

        self.assertIn("var S026_PAGE_MODE='plan-detail'", self.project_detail_html)
        for expected in (
            "document.querySelector('.s026-head h1').textContent='采集方案详情'",
            "document.querySelector('.s026-head p').textContent=''",
            "s026-config-nav",
            "基础信息",
            'data-pane="plan-basic"',
            "s026PlanBaseName",
            "s026PlanBaseScene",
            "s026SavePlanBase",
            "s026ConfirmPlanBaseChange",
            "s026PlanLockedNav",
            "已导入的 <b>'+packageCount+'</b> 个指令包将被删除",
            "指令包配置",
            "策略配置",
            "供应商配置",
            "导入指令包",
            "s026OpenPlanPackageImport",
            "s026PlanPackageZone",
            "s026PlanPackageIdQuery",
            "s026PlanPackageNameQuery",
            "s026ResetPlanPackageFilters",
            "s026FilterPlanPackageCandidates",
            "s026ResetPlanPackageCandidates",
            "s026ImportPlanPackages",
            "已导入",
            "s026-plan-package-status-cell",
            "s026-plan-package-dispatch-cell",
            "s026-plan-package-action-cell",
            "<th>指令总数</th><th class=\"s026-plan-package-status-cell\">状态</th>",
            "版本已归属其他指令包",
            "s026PlanPackageOwner",
            "s026PlanPackageOverlap",
            "s026OpenPlanPackageDetail",
            "s026OpenPlanPackageRename",
            "s026OpenEdgeApp",
            "s026PlanDetailActions",
            "s026PlanDetailActionButtons",
            "s026PlanListToggle",
            "s026TogglePlanListMode",
            "s026PlanInstructionView",
            "s026QueryPlanInstructions",
            "s026ResetPlanInstructionFilters",
            "s026CollectPlanInstructionVersions",
            "s026PlanInstructionIdQuery",
            "s026PlanInstructionVersionQuery",
            "s026PlanInstructionNameQuery",
            "s026PlanInstructionIteration",
            "s026PlanInstructionDifficulty",
            "s026PlanInstructionPropsQuery",
            "s026PlanInstructionStatus",
            "<th>指令描述</th><th>难度</th><th>镜像</th><th>道具</th><th>状态</th><th>来源指令包</th>",
            "s026-plan-duration-cell",
            "s026-plan-threshold-cell",
            "s026-plan-operation-cell",
            "s026OpenThresholdAdjust",
        ):
            self.assertIn(expected, self.project_detail_html)
        self.assertIn("<th>指令名称</th><th>指令迭代</th>", self.project_detail_html)
        self.assertNotIn("指令版本名称", self.project_detail_html)
        self.assertNotIn("采集指令</button>", self.project_detail_html)
        package_table_header = self.project_detail_html.split(
            'class="s026-table s026-plan-package-table"', 1
        )[1].split("</thead>", 1)[0]
        self.assertNotIn("<th>启用数</th>", package_table_header)
        self.assertIn("grid-template-columns:168px minmax(0,1fr)", self.project_detail_html)
        self.assertNotIn("执行监控</button>", self.project_detail_html)
        self.assertNotIn("<span>1</span>", self.project_detail_html)
        self.assertNotIn("<span>2</span>", self.project_detail_html)
        self.assertNotIn("<span>3</span>", self.project_detail_html)
        self.assertNotIn(
            "从指令包管理批量导入；同一采集方案内不能重复导入。",
            self.project_detail_html,
        )

    def test_collection_strategy_supplier_and_package_detail_follow_pdf_contract(self):
        for expected in (
            "var S026_PAGE_MODE='plan-strategies'",
            "新建采集策略",
            "跳过次数",
            "单条指令采集条数",
            "单任务相同指令执行次数",
            "无限制",
            "每人每天",
            "1 至 9999 的正整数",
            'max="9999"',
            "s026-limit-unit",
            "<th>版本号</th><th>状态</th><th>策略配置</th><th>创建人及创建时间</th><th>发布人及发布时间</th><th>操作</th>",
            "s026OpenStrategyCreate",
            "s026OpenStrategyEdit",
            "s026OpenDrawer('新建采集策略'",
            "s026OpenDrawer('编辑采集策略 ",
            '<table class="s026-table s026-fixed-actions" style="min-width:1250px">',
            "s026RequestStrategyPublish",
            "s026DeleteStrategy",
        ):
            self.assertIn(expected, self.strategy_html)
        self.assertNotIn("管理采集策略版本及上线状态。", self.strategy_html)
        self.assertNotIn(
            "发布新策略时，如已有上线策略，确认后原策略自动下线。",
            self.strategy_html,
        )

        for expected in (
            "var S026_PAGE_MODE='plan-suppliers'",
            "导入供应商",
            "默认启用",
            "s026SupplierNameQuery",
            "s026QueryPlanSuppliers",
            "s026ResetPlanSupplierFilters",
            "<th>供应商 ID</th><th>供应商名称</th><th>方案内状态</th><th>任务数量</th><th>操作</th>",
            "s026OpenSupplierImport",
            "s026OpenDrawer('导入供应商'",
            "s026SupplierCandidateName",
            "s026FilterSupplierCandidates",
            "s026ResetSupplierCandidates",
            "s026ImportPlanSuppliers",
            "s026TogglePlanSupplier",
            "不能新领取指令或指令包",
            "重复供应商，不可导入",
        ):
            self.assertIn(expected, self.supplier_html)
        for removed in (
            "管理参与采集的供应商及启停状态。",
            "从供应商库批量选择；系统会校验供应商仍然有效且当前方案尚未导入，导入成功后默认启用。",
            "<th>采集员数量</th>",
            "供应商有效，可导入当前方案",
        ):
            self.assertNotIn(removed, self.supplier_html)

        for expected in (
            "var S026_PAGE_MODE='plan-package-detail'",
            "<th>序号</th><th>指令 ID</th><th>指令名称</th><th>指令迭代</th><th>指令版本号</th><th>指令描述</th><th>难度</th><th>镜像</th><th>道具</th><th>指令版本状态</th>",
            '<th class="s026-plan-duration-cell">采集时长</th>',
            '<th class="s026-plan-threshold-cell">暂停阈值</th>',
            '<th class="s026-plan-operation-cell">操作</th>',
            "s026PlanVersionState",
            "s026RequestPlanVersionStatus",
            "s026OpenThresholdAdjust",
            "s026SaveThreshold",
            "暂停阈值不能小于已采集时长",
        ):
            self.assertIn(expected, self.plan_package_detail_html)
        self.assertNotIn("上线重复指令版本时", self.plan_package_detail_html)
        self.assertNotIn("剩余目标采集时长</th>", self.plan_package_detail_html)
        self.assertNotIn("s026PlanPackageDetailTitle", self.plan_package_detail_html)
        self.assertNotIn("s026DropPlanPackageVersion", self.plan_package_detail_html)
        self.assertNotIn("s026PlanPackageDragStart", self.plan_package_detail_html)
        self.assertNotIn("指令版本名称", self.plan_package_detail_html)

    def test_supplier_collection_plan_portal_is_read_only_and_assignment_scoped(self):
        for expected in (
            "var S026_PAGE_MODE='supplier-plan-list'",
            "s026SupplierCurrentId='SUP-DEMO-001'",
            "s026SupplierAssignedPlans",
            "s026SupplierPlanIdQuery",
            "s026SupplierPlanNameQuery",
            "s026SupplierPlanStatus",
            "上线",
            "暂停",
            "下线",
            "/data/collection-plans/assigned/detail?id=",
        ):
            self.assertIn(expected, self.supplier_plan_html)
        for expected in (
            "var S026_PAGE_MODE='supplier-plan-detail'",
            'data-pane="supplier-plan-detail"',
            "s026RenderSupplierPlanDetail",
            "该采集方案未分配给当前供应商",
        ):
            self.assertIn(expected, self.supplier_plan_detail_html)
        self.assertNotIn("已发布指令包", self.supplier_plan_detail_html.split("var S026_STORAGE_KEY=", 1)[0])
        self.assertNotIn("供应商仅可查看，不支持进入指令包详情", self.supplier_plan_detail_html)
        self.assertNotIn("s026SupplierPlanDetailTitle", self.supplier_plan_detail_html)
        self.assertIn(
            "<th>指令包 ID</th><th>指令包名称</th><th>工作区</th><th>状态</th><th>指令数</th><th>道具</th>",
            self.supplier_plan_detail_html,
        )

    def test_independent_package_management_and_detail_flow(self):
        for expected in (
            "var S026_PAGE_MODE='package-list'",
            "创建指令包",
            "s026GlobalPackageIdQuery",
            "s026GlobalPackageNameQuery",
            "s026GlobalPackageScene",
            "s026GlobalPackageZone",
            "s026GlobalPackageStatus",
            'onclick="s026QueryPackageManagement()">查询</button>',
            "s026-list-surface",
            "s026-filter-panel",
            "<th>指令包 ID</th><th>指令包名称</th><th>场景</th><th>工作区</th><th>道具</th><th>指令包状态</th><th>指令总数</th><th>操作</th>",
            "s026OpenPackageCreate",
            "s026CreatePackage",
            "configured:false",
            "CIP260908",
            "s026PackageDisplayId",
            "s026RequestPackageStatus",
            "s026RequestPackageDelete",
            "s026OpenPackageDetail",
        ):
            self.assertIn(expected, self.package_html)
        self.assertNotIn("筛选条件变更后自动刷新", self.package_html)
        for expected in (
            "var S026_PAGE_MODE='package-detail'",
            "document.querySelector('.s026-head h1').textContent='指令包详情'",
            "document.querySelector('.s026-head p').textContent=''",
            "导入指令",
            "基础信息",
            "s026PackageBaseName",
            "s026PackageBaseScene",
            "s026PackageBaseZone",
            "s026SavePackageBase",
            "s026ConfirmPackageBaseChange",
            "s026PackageImportButton",
            "s026PackageReorderButton",
            "s026TogglePackageReorder",
            "s026PackageCandidateId",
            "s026PackageCandidateVersion",
            "s026PackageCandidateName",
            "s026PackageCandidateIteration",
            "s026PackageCandidateDifficulty",
            "s026PackageCandidateProps",
            "s026ResetPackageCandidateFilters",
            "s026TogglePackageCandidate",
            "取消选中",
            "已导入",
            "<th>序号</th><th>指令 ID</th><th>指令名称</th><th>指令迭代</th><th>指令版本号</th><th>指令描述</th><th>指令难度</th><th>镜像</th><th>道具</th><th>指令版本状态</th><th>操作</th>",
            "s026PackageDraftOrder",
            "s026RemoveFromPackage",
            "发布前至少导入一条指令版本",
            "s026PackageDetailIdQuery",
            "s026PackageDetailVersionQuery",
            "s026PackageDetailInstructionNameQuery",
            "s026PackageDetailIteration",
            "s026PackageDetailDifficulty",
            "s026PackageDetailPropsQuery",
            "s026QueryPackageDetail",
            "s026ResetPackageDetailFilters",
            "s026-detail-section",
        ):
            self.assertIn(expected, self.package_detail_html)
        for removed in (
            "s026PackageSelectAll",
            "s026-package-version-choice",
            "s026ToggleAllPackageVersions",
            "s026TogglePackageVersionSelection",
            "批量选中",
            "已选中",
        ):
            self.assertNotIn(removed, self.package_detail_html)
        self.assertNotIn("s026PackageSelectionCount", self.package_detail_html)
        self.assertNotIn("指令版本名称", self.package_detail_html)
        self.assertNotIn("s026PackageBatchRemove", self.package_detail_html)
        self.assertNotIn("s026RequestRemovePackageVersions", self.package_detail_html)
        self.assertNotIn("批量删除", self.package_detail_html)
        self.assertNotIn('id="s026PackageDetailScene"', self.package_detail_html)
        self.assertNotIn('id="s026PackageDetailZone"', self.package_detail_html)
        self.assertNotIn("包内指令版本", self.package_detail_html)
        self.assertNotIn("s026PackageVersionCount", self.package_detail_html)
        self.assertTrue(all("projectId" not in package for package in S026_MOCK_DATA["packages"]))
        self.assertGreaterEqual(len(S026_MOCK_DATA["projectPackages"]), 1)

    def test_edge_collection_has_workspace_tabs_and_execution_states(self):
        for expected in (
            "var S026_PAGE_MODE='edge'",
            "指令包列表",
            "在线采集",
            "s026EdgeZoneTabs",
            "s026SetEdgeZone",
            "厨房",
            "卧室",
            "客厅",
            "卫生间",
            "书房",
            "可采集指令数",
            "领取",
            "被占用",
            "s026ClaimPackage",
            "s026OpenEdgePackageDetail",
            "CIP2609090001",
            "CIP2609090002",
            "已完成的指令包不可查看",
            "道具（20）",
            "s026EdgePackageProps",
            "s026-edge-identity-line",
        ):
            self.assertIn(expected, self.edge_html)
        self.assertNotIn('id="s026EdgeProjectSelect"', self.edge_html)
        self.assertNotIn('id="s026EdgeZoneFilter"', self.edge_html)
        self.assertNotIn("该指令包已被占用", self.edge_html)
        for expected in (
            "var S026_PAGE_MODE='edge-package-detail'",
            "指令包详情",
            "返回指令包列表",
            "s026EdgeConnections",
            "s026ConnectDevice",
            "请先连接蓝牙和 Wi-Fi",
            "s026SetEdgeStatusFilter",
            "s026EdgeStatusFilter",
            "全部",
            "难度",
            "待采集",
            "采集中",
            "已跳过",
            "未采满",
            "已采满",
            "跳过当前指令",
            "s026EdgeSkipMask",
            "s026-phone-modal",
            "s026CloseEdgeSkip",
            "s026WithdrawInstance",
            "撤回",
            "采集进度",
            "s026EdgeConnectionMask",
            "s026DemoCollectOne",
            "s026ExitCollection",
            "s026-executed-copy",
            "提交指令包",
            "s026ShowEdgePackageList",
            "s026EdgeTaskRecords",
            "s026FinishPackage",
            "仍有待采集或采集中的指令，暂不可提交",
        ):
            self.assertIn(expected, self.edge_detail_html)
        self.assertNotIn('<div class="s026-device-bar">', self.edge_detail_html)
        self.assertNotIn("当前已完成 ", self.edge_detail_html)
        self.assertNotIn("指令 ID + 版本号", self.edge_detail_html)
        self.assertNotIn("record.id+' + '+record.version", self.edge_detail_html)
        self.assertNotIn("执行人：示例采集员", self.edge_detail_html)
        self.assertNotIn("2026-09-09 10:18", self.edge_detail_html)
        self.assertNotIn("采集进度 '+instance.collected", self.edge_detail_html)
        self.assertIn("s026-instance-count", self.edge_detail_html)
        self.assertIn("s026-instance-side", self.edge_detail_html)
        self.assertIn('class="s026-phone"', self.edge_html)
        self.assertIn('class="s026-phone"', self.edge_detail_html)
        self.assertIn("返回采集方案", self.edge_html)
        self.assertIn(
            "/data/edge-collection/package-detail?project=",
            self.edge_html,
        )

        referenced_ids = {
            item["packageId"]
            for item in S026_MOCK_DATA["projectPackages"]
            if item["projectId"] == "CP260001"
        }
        online_packages = [
            item
            for item in S026_MOCK_DATA["packages"]
            if item["id"] in referenced_ids and item["status"] == "上线"
        ]
        self.assertGreaterEqual(len(online_packages), 2)

    def test_demo_has_no_network_client_or_real_user_contacts(self):
        html = (
            self.instruction_html
            + self.approval_html
            + self.approval_detail_html
            + self.package_html
            + self.package_detail_html
            + self.project_html
            + self.project_detail_html
            + self.strategy_html
            + self.supplier_html
            + self.plan_package_detail_html
            + self.edge_html
        )
        self.assertNotIn("fetch(", html)
        self.assertNotIn("XMLHttpRequest", html)
        self.assertNotIn("18888888888", html)
        self.assertIn("localStorage", html)
        self.assertIn("示例供应商甲", html)

    def test_project_owned_mock_records_are_explicitly_scoped(self):
        project_ids = {item["id"] for item in S026_MOCK_DATA["projects"]}
        for collection in ("schemes", "projectInstructions", "projectPackages", "suppliers"):
            with self.subTest(collection=collection):
                self.assertTrue(S026_MOCK_DATA[collection])
                self.assertTrue(
                    all(item.get("projectId") in project_ids for item in S026_MOCK_DATA[collection])
                )


if __name__ == "__main__":
    unittest.main()
