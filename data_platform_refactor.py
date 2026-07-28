"""Configuration-driven product architecture for the Quanta data platform demo.

This module deliberately contains no Flask routes.  It owns the product objects,
navigation, capability registry, demo facts and rendering functions; the portal
only supplies the shared chrome.  Keeping the domain model here makes the
boundaries in ``Quanta-数据平台产品架构调整方案-完善版.md`` executable and testable.
"""

import json
from html import escape


# ---------------------------------------------------------------------------
# Product information architecture
# ---------------------------------------------------------------------------

PAGE_SPECS = {
    "collection_tasks": {
        "path": "/data/collection-tasks",
        "title": "采集任务",
        "subtitle": "管理指令采集、自由采集和 DAgger 采集任务",
        "icon": "&#9776;",
    },
    "processing_tasks": {
        "path": "/data/processing-tasks",
        "title": "处理任务",
        "subtitle": "按质检环节和标注环节管理数据处理任务",
        "icon": "&#9776;",
    },
    "allocation_management": {
        "path": "/data/allocations",
        "title": "分配管理",
        "subtitle": "查看处理环节滞留并分配人员、供应商和处理流程",
        "icon": "&#8646;",
    },
    "data_management": {
        "path": "/data/recordings",
        "title": "数据管理",
        "subtitle": "统一查看采集数据与导入数据",
        "icon": "&#9783;",
    },
    "workbench": {
        "path": "/data/workbench",
        "title": "工作台",
        "subtitle": "领取并连续处理人工执行任务",
        "icon": "&#9881;",
        "legacy": True,
    },
    "personal_dashboard": {
        "path": "/data/dashboard",
        "title": "个人看板",
        "subtitle": "查看个人任务、产能与处理趋势",
        "icon": "&#9636;",
        "legacy": True,
    },
    "workflow_management": {
        "path": "/data/pipelines",
        "title": "流程管理",
        "subtitle": "配置并管理数据处理工作流",
        "icon": "&#8644;",
        "legacy": True,
    },
    "execution_records": {
        "path": "/data/runs",
        "title": "执行记录",
        "subtitle": "查看流程执行状态、输入、输出与日志",
        "icon": "&#9654;",
        "legacy": True,
    },
    "operator_management": {
        "path": "/data/operators",
        "title": "算子管理",
        "subtitle": "管理工作流可复用处理算子",
        "icon": "&#9881;",
        "legacy": True,
    },
    "workbench_management": {
        "path": "/data/workbench-management",
        "title": "工作台管理",
        "subtitle": "管理工作台 Schema 与可复用组件",
        "icon": "&#9634;",
    },
    "project_management": {
        "path": "/data/projects",
        "title": "项目管理",
        "subtitle": "维护任务所属项目及负责人",
        "icon": "&#9635;",
    },
    "rule_management": {
        "path": "/data/rules",
        "title": "规则管理",
        "subtitle": "配置数据处理与人工执行规则",
        "icon": "&#9745;",
        "legacy": True,
    },
    "scene_management": {
        "path": "/data/scenes",
        "title": "场景管理",
        "subtitle": "统一维护业务场景定义",
        "icon": "&#9711;",
        "legacy": True,
    },
    "tag_management": {
        "path": "/data/tags",
        "title": "标签管理",
        "subtitle": "维护数据与任务标签体系",
        "icon": "&#9873;",
        "legacy": True,
    },
    "dataset_management": {
        "path": "/data/datasets",
        "title": "数据集管理",
        "subtitle": "管理数据集、版本与数据划分",
        "icon": "&#9636;",
        "legacy": True,
    },
    "supplier_management": {
        "path": "/data/suppliers",
        "title": "供应商管理",
        "subtitle": "管理外部供应商、协议与交付状态",
        "icon": "&#9635;",
    },
    "personnel_management": {
        "path": "/data/personnel",
        "title": "人员管理",
        "subtitle": "管理人员、技能、状态与供应商归属",
        "icon": "&#9786;",
    },
    "permission_management": {
        "path": "/data/permissions",
        "title": "权限管理",
        "subtitle": "管理角色、资源权限与授权关系",
        "icon": "&#9634;",
    },
}

NAV_GROUPS = [
    (
        "任务管理",
        ["collection_tasks", "processing_tasks", "allocation_management"],
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
        ["project_management", "rule_management", "scene_management", "tag_management"],
    ),
    (
        "运营管理",
        ["supplier_management", "personnel_management", "permission_management"],
    ),
]


def build_navigation():
    """Return the tuple format consumed by the shared Quanta sidebar."""
    return [
        (
            group,
            [
                (
                    PAGE_SPECS[key]["path"],
                    PAGE_SPECS[key]["title"],
                    PAGE_SPECS[key]["icon"],
                )
                for key in page_keys
            ],
        )
        for group, page_keys in NAV_GROUPS
    ]


DATA_PLATFORM_NAV = build_navigation()


# ---------------------------------------------------------------------------
# Stable product registries and demo facts
# ---------------------------------------------------------------------------

ROLES = [
    ("项目 / 数据运营负责人", "交付范围、周期、产能和成本"),
    ("数据工厂管理员", "任务分配、人员技能和产能"),
    ("采集 / 标注人员", "领取任务并连续作业"),
    ("算法 / 数据工程师", "算子、运行分析、检索和血缘"),
    ("数据集 / 交付管理员", "构建、冻结和发布版本"),
    ("平台管理员", "权限、配额、集成、日志和监控"),
]

NODE_TYPES = {
    "operator": {
        "name": "自动节点",
        "runtime": "Operator Runtime",
        "contract": "输入快照 → 算子版本与参数 → 新快照 / 结构化结果",
    },
    "human": {
        "name": "人工节点",
        "runtime": "Human Task Runtime",
        "contract": "输入快照 → 工作台 Schema → 提交结果 / 证据",
    },
    "gateway": {
        "name": "网关节点",
        "runtime": "Workflow Engine",
        "contract": "结构化结果 → 条件表达式 → 分支 / 合流 / 回流",
    },
}

WORKBENCH_COMPONENTS = {
    "multi_view_video": ("多视角视频", "头部、左臂、右臂视频同步播放与逐帧定位"),
    "playback_timeline": ("播放时间轴", "播放窗口、问题区间与标注片段的时间映射"),
    "instruction_context": ("任务说明", "采集指令、处理规则与任务上下文"),
    "quality_issue_editor": ("质检记录", "失误区间、严重程度、问题描述与证据"),
    "annotation_segment_editor": ("标注编辑器", "层级动作片段、动作元素、描述和起止时间"),
    "trajectory_viewer": ("轨迹信息", "关节、末端位姿与控制轨迹可视化"),
    "quality_result_viewer": ("质检信息", "质检结论、问题区间与规则版本"),
    "annotation_result_viewer": ("标注信息", "动作片段、标注版本与结构化结果"),
    "tag_viewer": ("标签信息", "场景、动作、设备与质量标签"),
    "conclusion_selector": ("结论选择", "合格、不合格、操作失误三类业务结论"),
    "workbench_log": ("处理日志", "查看当前数据的处理、提交与退回日志"),
    "task_actions": ("任务操作", "提交、驳回与后续任务流转"),
}

WORKBENCH_COMPONENT_USAGE = {
    "multi_view_video": "质检、标注、详情",
    "playback_timeline": "质检、标注",
    "instruction_context": "质检、标注",
    "quality_issue_editor": "质检、详情",
    "annotation_segment_editor": "标注、详情",
    "trajectory_viewer": "质检、标注、详情",
    "quality_result_viewer": "标注、详情",
    "annotation_result_viewer": "详情",
    "tag_viewer": "详情",
    "conclusion_selector": "质检、标注、详情",
    "workbench_log": "质检、标注、详情",
    "task_actions": "质检、标注、详情",
}

PROCESSING_FLOW_HUMAN_NODES = {
    "多级复核数据处理流程": [
        "质检环节 · 抽检复核",
        "质检环节 · 供应商复核",
        "质检环节 · 申诉复核",
        "标注环节 · 一轮复核",
        "标注环节 · 二轮复核",
        "标注环节 · 内部验收",
        "验收环节 · 验收",
    ],
    "双轮人工数据处理流程": [
        "质检环节 · 质检",
        "质检环节 · 抽检",
        "标注环节 · 标注",
        "标注环节 · 抽验",
        "验收环节 · 验收",
    ],
    "标准训练数据流水线": [],
    "DAgger 数据流水线": [],
}

OPERATORS = {
    "op.timestamp-align@2.1.0": "时间戳对齐",
    "op.episode-split@1.6.2": "Episode 切分",
    "op.schema-validate@2.0.0": "格式与 Schema 校验",
    "op.dataset-build@1.2.0": "数据集版本构建",
}

WORKBENCH_SCHEMAS = [
    {
        "id": "wb.quality-review@2.0",
        "name": "质检工作台",
        "type": "质检",
        "regions": ["context", "video", "tabs", "decision", "actions"],
        "components": [
            "instruction_context",
            "multi_view_video",
            "playback_timeline",
            "trajectory_viewer",
            "quality_issue_editor",
            "conclusion_selector",
            "workbench_log",
            "task_actions",
        ],
        "actions": ["submit", "reject"],
        "preview": "/data/workbench-management/preview/quality?task=WB-2026-0718-QC",
        "status": "published",
        "frozen": True,
    },
    {
        "id": "wb.action-annotation@4.1",
        "name": "标注工作台",
        "type": "标注",
        "regions": ["context", "video", "tabs", "decision", "actions"],
        "components": [
            "instruction_context",
            "multi_view_video",
            "playback_timeline",
            "trajectory_viewer",
            "quality_result_viewer",
            "annotation_segment_editor",
            "conclusion_selector",
            "workbench_log",
            "task_actions",
        ],
        "actions": ["submit", "reject"],
        "preview": "/data/workbench-management/preview/annotation?task=WB-2026-0922-LB",
        "status": "published",
        "frozen": True,
    },
    {
        "id": "wb.data-detail@1.0",
        "name": "详情工作台",
        "type": "详情",
        "regions": ["video", "tabs", "decision", "actions"],
        "components": [
            "multi_view_video",
            "trajectory_viewer",
            "quality_result_viewer",
            "annotation_result_viewer",
            "tag_viewer",
            "conclusion_selector",
            "workbench_log",
            "task_actions",
        ],
        "actions": ["submit", "reject"],
        "preview": "/data/workbench-management/preview/detail?task=WB-2026-0922-AC",
        "status": "published",
        "frozen": True,
    },
]

PROJECT_MANAGEMENT_ITEMS = [
    {
        "name": "预训练采集",
        "description": "面向基础模型预训练的数据采集与持续扩充项目",
        "owner": "Lance Li",
    },
    {
        "name": "demo 项目",
        "description": "面向客户演示和场景验证的快速数据生产项目",
        "owner": "Min Chen",
    },
    {
        "name": "宁德项目",
        "description": "宁德时代现场任务的数据采集与处理项目",
        "owner": "joanna.qiao",
    },
]

QUALITY_CONCLUSIONS = ("合格", "不合格", "操作失误")
ANNOTATION_STATUSES = ("未标注", "已标注")
UPLOAD_STATUSES = ("未上传", "上传中", "上传成功", "上传失败")
COLLECTION_CONCLUSIONS = ("成功", "失败")
DATA_SOURCE_LABELS = {"collection": "采集", "import": "导入"}
TASK_PROJECT_LABELS = {
    "PRJ-MOZ2-PRE-03": "预训练采集",
    "PRJ-MOZ1-SFT-07": "demo 项目",
    "PRJ-EVAL-GEN-02": "宁德项目",
}
COLLECTION_PROCESSING_BINDINGS = {
    "COL-2026-0718": "PROC-2026-0921",
}

PROJECTS = [
    {
        "id": "PRJ-MOZ1-SFT-07",
        "name": "Moz1 家居操作 SFT 数据交付",
        "owner": "joanna.qiao",
        "scope": "客厅 / 厨房 · 8 类任务",
        "target": "8,000 EP",
        "due": "2026-08-18",
        "progress": 68,
        "risk": "2 台设备离线",
    },
    {
        "id": "PRJ-MOZ2-PRE-03",
        "name": "Moz2 双臂预训练数据",
        "owner": "Lance Li",
        "scope": "仓储 · 4 类任务",
        "target": "12,000 EP",
        "due": "2026-09-02",
        "progress": 42,
        "risk": "进度正常",
    },
    {
        "id": "PRJ-EVAL-GEN-02",
        "name": "通用评测集季度更新",
        "owner": "Wei Zhang",
        "scope": "6 场景 · 24 子任务",
        "target": "1,200 EP",
        "due": "2026-08-06",
        "progress": 86,
        "risk": "待发布审批",
    },
]

BUSINESS_TASKS = [
    {
        "id": "COL-2026-0718",
        "type": "data_collection_task",
        "type_name": "指令采集",
        "collection_mode": "instruction",
        "name": "厨房狭窄台面补采",
        "project": "PRJ-MOZ1-SFT-07",
        "input": "采集 SOP v3.4 · Moz1 设备组",
        "output": "1,240 / 1,500 Recording",
        "pipeline": "—",
        "snapshot": "—",
        "progress": 83,
        "priority": "高",
        "created": "2026-07-18 10:24",
        "due": "2026-07-31",
        "collection_progress": {"done": 1240, "total": 1500},
        "operator": "刘素粉",
        "creator": "joanna.qiao",
        "status": "running",
    },
    {
        "id": "COL-2026-0721",
        "type": "data_collection_task",
        "type_name": "指令采集",
        "collection_mode": "instruction",
        "name": "桌面整理标准动作采集",
        "project": "PRJ-MOZ1-SFT-07",
        "input": "采集指令集 v2.6 · Moz1 设备组",
        "output": "860 / 1,000 Recording",
        "pipeline": "—",
        "snapshot": "—",
        "progress": 86,
        "priority": "中",
        "created": "2026-07-21 09:36",
        "due": "2026-08-03",
        "collection_progress": {"done": 860, "total": 1000},
        "operator": "王一帆",
        "creator": "数据工厂管理员",
        "status": "running",
    },
    {
        "id": "COL-2026-0724",
        "type": "data_collection_task",
        "type_name": "自由采集",
        "collection_mode": "free",
        "name": "开放场景自主探索采集",
        "project": "PRJ-MOZ2-PRE-03",
        "input": "客厅开放场景 · 自由采集配置 v1.2",
        "output": "420 / 800 Recording",
        "pipeline": "—",
        "snapshot": "—",
        "progress": 53,
        "priority": "中",
        "created": "2026-07-24 13:12",
        "due": "2026-08-08",
        "collection_progress": {"done": 420, "total": 800},
        "operator": "采集团队 B",
        "creator": "Lance Li",
        "status": "running",
    },
    {
        "id": "COL-2026-0726",
        "type": "data_collection_task",
        "type_name": "自由采集",
        "collection_mode": "free",
        "name": "仓储货架自由交互采集",
        "project": "PRJ-MOZ2-PRE-03",
        "input": "仓储货架 A/B 区 · 自由采集",
        "output": "188 / 600 Recording",
        "pipeline": "—",
        "snapshot": "—",
        "progress": 31,
        "priority": "低",
        "created": "2026-07-26 11:08",
        "due": "2026-08-12",
        "collection_progress": {"done": 188, "total": 600},
        "operator": "供应商 A",
        "creator": "Wei Zhang",
        "status": "running",
    },
    {
        "id": "COL-2026-0715",
        "type": "data_collection_task",
        "type_name": "DAgger 采集",
        "collection_mode": "dagger",
        "name": "白板擦除失败案例 DAgger 采集",
        "project": "PRJ-MOZ1-SFT-07",
        "input": "policy.moz1-whiteboard@0.8 · 人工接管",
        "output": "312 / 360 Recording",
        "pipeline": "—",
        "snapshot": "—",
        "progress": 87,
        "priority": "高",
        "created": "2026-07-15 16:45",
        "due": "2026-07-30",
        "collection_progress": {"done": 312, "total": 360},
        "operator": "DAgger 小组",
        "creator": "Min Chen",
        "status": "running",
    },
    {
        "id": "IMP-2026-0042",
        "type": "data_import_task",
        "type_name": "数据导入",
        "name": "供应商 Batch-12 导入",
        "project": "PRJ-MOZ2-PRE-03",
        "input": "s3://vendor/batch-12 · LeRobot v2",
        "output": "导入报告 · 失败 18 条",
        "pipeline": "—",
        "snapshot": "—",
        "progress": 96,
        "priority": "中",
        "created": "2026-07-22 14:06",
        "due": "2026-07-29",
        "status": "running",
    },
    {
        "id": "PROC-2026-0921",
        "type": "data_processing_task",
        "type_name": "数据处理 · 标准化",
        "name": "厨房数据标准化处理",
        "project": "PRJ-MOZ1-SFT-07",
        "input": "1,206 Recording",
        "output": "842 Episode + 新快照",
        "pipeline": "pv.capture-to-dataset@7",
        "snapshot": "snap-moz1-0718-r3",
        "progress": 72,
        "priority": "高",
        "created": "2026-07-24 09:42",
        "due": "2026-08-02",
        "stage_progress": [
            {"label": "质检", "done": 842, "total": 1206},
            {"label": "标注", "done": 488, "total": 842},
            {"label": "验收", "done": 240, "total": 842},
        ],
        "processing_stage": "cleaning",
        "flow_name": "多级复核数据处理流程",
        "node_name": "时间戳对齐",
        "operator": "包媛桐",
        "creator": "joanna.qiao",
        "status": "running",
    },
    {
        "id": "PROC-2026-0922",
        "type": "data_processing_task",
        "type_name": "数据处理 · 标注",
        "name": "家居动作分段标注",
        "project": "PRJ-MOZ1-SFT-07",
        "input": "842 Episode",
        "output": "Annotation Version",
        "pipeline": "pv.capture-to-dataset@7",
        "snapshot": "snap-moz1-episodes-r2",
        "progress": 58,
        "priority": "高",
        "created": "2026-07-25 16:20",
        "due": "2026-08-05",
        "stage_progress": [
            {"label": "质检", "done": 842, "total": 842},
            {"label": "标注", "done": 488, "total": 842},
            {"label": "验收", "done": 320, "total": 842},
        ],
        "processing_stage": "annotation",
        "flow_name": "双轮人工数据处理流程",
        "node_name": "动作分段标注",
        "operator": "供应商 A",
        "creator": "joanna.qiao",
        "status": "running",
    },
    {
        "id": "PROC-2026-0888",
        "type": "data_processing_task",
        "type_name": "数据处理 · 数据集构建",
        "name": "通用评测集季度构建",
        "project": "PRJ-EVAL-GEN-02",
        "input": "Snapshot snap-eval-q3-input",
        "output": "dataset.eval-general@2026q3",
        "pipeline": "pv.vendor-import@3",
        "snapshot": "snap-eval-q3-input",
        "progress": 100,
        "priority": "中",
        "created": "2026-07-23 11:08",
        "due": "2026-07-30",
        "stage_progress": [
            {"label": "质检", "done": 488, "total": 488},
            {"label": "标注", "done": 488, "total": 488},
            {"label": "验收", "done": 452, "total": 488},
        ],
        "processing_stage": "acceptance",
        "flow_name": "多级复核数据处理流程",
        "node_name": "交付验收",
        "operator": "Wei Zhang",
        "creator": "Wei Zhang",
        "status": "succeeded",
    },
]

PIPELINE_DEFINITIONS = [
    {
        "id": "pipeline.capture-to-dataset",
        "name": "采集到数据集标准流程",
        "owner": "数据运营组",
        "draft_version": "v8-draft",
        "published_version": "pv.capture-to-dataset@7",
        "status": "published",
        "frozen": True,
        "nodes": [
            ("采集导入", "gateway", None),
            ("时间戳对齐", "operator", "op.timestamp-align@2.1.0"),
            ("Episode 切分", "operator", "op.episode-split@1.6.2"),
            ("动作标注", "human", "wb.action-annotation@4.1"),
            ("数据集构建", "operator", "op.dataset-build@1.2.0"),
        ],
    },
    {
        "id": "pipeline.vendor-import",
        "name": "三方数据导入与构建",
        "owner": "数据资产组",
        "draft_version": "v4-draft",
        "published_version": "pv.vendor-import@3",
        "status": "published",
        "frozen": True,
        "nodes": [
            ("格式校验", "operator", "op.schema-validate@2.0.0"),
            ("去重与标准化", "operator", "op.timestamp-align@2.1.0"),
            ("数据集构建", "operator", "op.dataset-build@1.2.0"),
        ],
    },
]

DATA_SNAPSHOTS = [
    {
        "id": "snap-moz1-0718-r3",
        "project": "PRJ-MOZ1-SFT-07",
        "members": "1,206 Recording",
        "checksum": "sha256:8cf1…c92a",
        "created_by": "COL-2026-0718",
        "immutable": True,
    },
    {
        "id": "snap-moz1-episodes-r2",
        "project": "PRJ-MOZ1-SFT-07",
        "members": "1,084 Recording / 842 Episode",
        "checksum": "sha256:2ad7…ec10",
        "created_by": "run-moz1-0921",
        "immutable": True,
    },
    {
        "id": "snap-eval-q3-input",
        "project": "PRJ-EVAL-GEN-02",
        "members": "1,238 Episode",
        "checksum": "sha256:5c42…0b17",
        "created_by": "IMP-2026-0042",
        "immutable": True,
    },
    {
        "id": "snap-eval-q3-build",
        "project": "PRJ-EVAL-GEN-02",
        "members": "1,200 Episode",
        "checksum": "sha256:71bb…9f20",
        "created_by": "run-eval-0314",
        "immutable": True,
    },
]

PIPELINE_RUNS = [
    {
        "id": "run-moz1-0921",
        "project": "PRJ-MOZ1-SFT-07",
        "business_task": "PROC-2026-0921",
        "pipeline_version": "pv.capture-to-dataset@7",
        "input_snapshot": "snap-moz1-0718-r3",
        "current_node": "Episode 切分",
        "node_progress": "3 / 5",
        "status": "running",
        "idempotency_key": "idem:0c92…cf18",
        "started": "2026-07-26 09:42",
    },
    {
        "id": "run-moz1-0922",
        "project": "PRJ-MOZ1-SFT-07",
        "business_task": "PROC-2026-0922",
        "pipeline_version": "pv.capture-to-dataset@7",
        "input_snapshot": "snap-moz1-episodes-r2",
        "current_node": "动作标注",
        "node_progress": "4 / 5",
        "status": "running",
        "idempotency_key": "idem:812e…31ad",
        "started": "2026-07-25 16:20",
    },
    {
        "id": "run-eval-0314",
        "project": "PRJ-EVAL-GEN-02",
        "business_task": "PROC-2026-0888",
        "pipeline_version": "pv.vendor-import@3",
        "input_snapshot": "snap-eval-q3-input",
        "current_node": "数据集构建",
        "node_progress": "3 / 3",
        "status": "succeeded",
        "idempotency_key": "idem:aa02…908c",
        "started": "2026-07-23 11:08",
    },
]

NODE_RUNS = [
    {
        "id": "nr-0921-align-001",
        "pipeline_run": "run-moz1-0921",
        "node": "时间戳对齐",
        "node_type": "operator",
        "input_snapshot": "snap-moz1-0718-r3",
        "executor_version": "op.timestamp-align@2.1.0",
        "attempt": 1,
        "output": "snap-moz1-aligned-r1",
        "status": "succeeded",
    },
    {
        "id": "nr-0921-split-002",
        "pipeline_run": "run-moz1-0921",
        "node": "Episode 切分",
        "node_type": "operator",
        "input_snapshot": "snap-moz1-0718-r3",
        "executor_version": "op.episode-split@1.6.2",
        "attempt": 1,
        "output": "snap-moz1-episodes-r2",
        "status": "running",
    },
    {
        "id": "nr-0922-ann-127",
        "pipeline_run": "run-moz1-0922",
        "node": "动作标注",
        "node_type": "human",
        "input_snapshot": "snap-moz1-episodes-r2",
        "executor_version": "wb.action-annotation@4.1",
        "attempt": 1,
        "output": "annotation:EP-842-127@v3",
        "status": "running",
    },
    {
        "id": "nr-0922-ann-128",
        "pipeline_run": "run-moz1-0922",
        "node": "动作标注",
        "node_type": "human",
        "input_snapshot": "snap-moz1-episodes-r2",
        "executor_version": "wb.action-annotation@4.1",
        "attempt": 1,
        "output": "annotation:EP-842-128@draft",
        "status": "running",
    },
    {
        "id": "nr-0922-ann-129",
        "pipeline_run": "run-moz1-0922",
        "node": "动作标注",
        "node_type": "human",
        "input_snapshot": "snap-moz1-episodes-r2",
        "executor_version": "wb.action-annotation@4.1",
        "attempt": 1,
        "output": "annotation:EP-842-129@draft",
        "status": "pending",
    },
    {
        "id": "nr-0314-build-003",
        "pipeline_run": "run-eval-0314",
        "node": "数据集构建",
        "node_type": "operator",
        "input_snapshot": "snap-eval-q3-input",
        "executor_version": "op.dataset-build@1.2.0",
        "attempt": 1,
        "output": "snap-eval-q3-build",
        "status": "succeeded",
    },
]

HUMAN_TASKS = [
    {
        "id": "ht-220981",
        "task_type": "动作分段标注",
        "business_task": "PROC-2026-0922",
        "pipeline_run": "run-moz1-0922",
        "node_run": "nr-0922-ann-127",
        "data_scope": "Episode EP-842-127",
        "sop": "SOP-ACTION-SEG@4.1",
        "priority": "P0",
        "sla": "剩余 01:42",
        "assignee": "待领取",
        "lock": "未锁定",
        "status": "pending",
    },
    {
        "id": "ht-220976",
        "task_type": "动作分段标注",
        "business_task": "PROC-2026-0922",
        "pipeline_run": "run-moz1-0922",
        "node_run": "nr-0922-ann-128",
        "data_scope": "Episode EP-842-128",
        "sop": "SOP-ACTION-SEG@4.1",
        "priority": "P1",
        "sla": "剩余 06:18",
        "assignee": "joanna.qiao",
        "lock": "锁定至 16:45",
        "status": "in_progress",
    },
    {
        "id": "ht-220944",
        "task_type": "动作分段标注",
        "business_task": "PROC-2026-0922",
        "pipeline_run": "run-moz1-0922",
        "node_run": "nr-0922-ann-129",
        "data_scope": "Episode EP-842-129",
        "sop": "SOP-ACTION-SEG@4.1",
        "priority": "P1",
        "sla": "剩余 09:20",
        "assignee": "供应商 A",
        "lock": "锁定至 18:10",
        "status": "in_progress",
    },
]

DATASET_VERSIONS = [
    {
        "id": "dataset.moz1-household@4.0.0",
        "project": "PRJ-MOZ1-SFT-07",
        "snapshot": "snap-moz1-episodes-r2",
        "lineage": "98.7%",
        "status": "frozen",
        "consumer": "待发布审批",
        "immutable": True,
    },
    {
        "id": "dataset.eval-general@2026q3",
        "project": "PRJ-EVAL-GEN-02",
        "snapshot": "snap-eval-q3-build",
        "lineage": "100%",
        "status": "published",
        "consumer": "评测任务 8 个",
        "immutable": True,
    },
    {
        "id": "dataset.moz2-warehouse@1.3.0-draft",
        "project": "PRJ-MOZ2-PRE-03",
        "snapshot": "未冻结",
        "lineage": "91.2%",
        "status": "draft",
        "consumer": "不可引用",
        "immutable": False,
    },
]

RECORDING_ASSETS = [
    {
        "id": "recording:4057808@raw",
        "source_task_type": "data_collection_task",
        "source_task_id": "COL-2026-0718",
        "device": "UDAS-007",
        "time_range": "2026-07-24 09:11:02 · 42.8s",
        "modalities": "RGB ×3 · joint · gripper",
        "checksum": "sha256:21ad…904e",
    },
    {
        "id": "recording:4057761@raw",
        "source_task_type": "data_collection_task",
        "source_task_id": "COL-2026-0718",
        "device": "UDAS-007",
        "time_range": "2026-07-24 09:08:15 · 38.4s",
        "modalities": "RGB ×3 · joint · gripper",
        "checksum": "sha256:4f10…a28c",
    },
    {
        "id": "recording:vendor-12-001@raw",
        "source_task_type": "data_import_task",
        "source_task_id": "IMP-2026-0042",
        "device": "Vendor-MOZ2-03",
        "time_range": "2026-07-22 14:20:06 · 61.2s",
        "modalities": "RGB ×5 · joint · force",
        "checksum": "sha256:b31e…7a88",
    },
]

TASK_DETAIL_RECORDS = {
    "COL-2026-0718": [
        {
            "id": "4057808",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "采集",
            "collection": "成功",
            "quality": "合格",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "采集：刘素粉",
        },
        {
            "id": "4057761",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "采集",
            "collection": "成功",
            "quality": "合格",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "采集：刘素粉",
        },
        {
            "id": "4057711",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "上传",
            "collection": "成功",
            "quality": "操作失误",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "采集：刘素粉",
        },
        {
            "id": "4057669",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "采集",
            "collection": "失败",
            "quality": "不合格",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "采集：刘素粉",
        },
    ],
    "PROC-2026-0921": [
        {
            "id": "4057808",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "质检",
            "collection": "成功",
            "quality": "合格",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "质检：包媛桐",
        },
        {
            "id": "4057761",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "质检",
            "collection": "成功",
            "quality": "操作失误",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "质检：包媛桐",
        },
        {
            "id": "4057711",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "标注",
            "collection": "成功",
            "quality": "合格",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "标注：供应商 A",
        },
        {
            "id": "4057669",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "验收",
            "collection": "成功",
            "quality": "不合格",
            "annotation": "已标注",
            "acceptance": "进行中",
            "operators": "验收：joanna.qiao",
        },
    ],
    "PROC-2026-0922": [
        {
            "id": "4057808",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "标注",
            "collection": "成功",
            "quality": "合格",
            "annotation": "已标注",
            "acceptance": "已完成",
            "operators": "标注：joanna.qiao",
        },
        {
            "id": "4057761",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "标注",
            "collection": "成功",
            "quality": "合格",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "标注：供应商 A",
        },
        {
            "id": "4057711",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "验收",
            "collection": "成功",
            "quality": "合格",
            "annotation": "已标注",
            "acceptance": "进行中",
            "operators": "验收：joanna.qiao",
        },
        {
            "id": "4057669",
            "collection_id": "C-3635",
            "device": "UDAS-007",
            "node": "质检",
            "collection": "成功",
            "quality": "操作失误",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "质检：包媛桐",
        },
    ],
    "PROC-2026-0888": [
        {
            "id": "5088112",
            "collection_id": "EVAL-Q3",
            "device": "Benchmark",
            "node": "验收",
            "collection": "成功",
            "quality": "合格",
            "annotation": "已标注",
            "acceptance": "已完成",
            "operators": "验收：Wei Zhang",
        },
        {
            "id": "5088076",
            "collection_id": "EVAL-Q3",
            "device": "Benchmark",
            "node": "验收",
            "collection": "成功",
            "quality": "合格",
            "annotation": "已标注",
            "acceptance": "已完成",
            "operators": "验收：Wei Zhang",
        },
        {
            "id": "5088029",
            "collection_id": "EVAL-Q3",
            "device": "Benchmark",
            "node": "验收",
            "collection": "成功",
            "quality": "合格",
            "annotation": "已标注",
            "acceptance": "已完成",
            "operators": "验收：Wei Zhang",
        },
        {
            "id": "5087994",
            "collection_id": "EVAL-Q3",
            "device": "Benchmark",
            "node": "验收",
            "collection": "成功",
            "quality": "合格",
            "annotation": "已标注",
            "acceptance": "已完成",
            "operators": "验收：Wei Zhang",
        },
    ],
}

ALLOCATION_STAGE_SUMMARY = [
    {
        "stage": "质检",
        "total": 1240,
        "unassigned": 96,
        "assigned_waiting": 140,
        "processing": 61,
        "completed": 943,
    },
    {
        "stage": "标注",
        "total": 943,
        "unassigned": 124,
        "assigned_waiting": 186,
        "processing": 88,
        "completed": 545,
    },
    {
        "stage": "验收",
        "total": 545,
        "unassigned": 42,
        "assigned_waiting": 86,
        "processing": 54,
        "completed": 363,
    },
]

ALLOCATION_PROJECT_STAGE_SUMMARY = {
    "全部项目": ALLOCATION_STAGE_SUMMARY,
    "宁德项目": [
        {
            "stage": "质检",
            "total": 612,
            "unassigned": 96,
            "assigned_waiting": 0,
            "processing": 31,
            "completed": 485,
        },
        {
            "stage": "标注",
            "total": 445,
            "unassigned": 124,
            "assigned_waiting": 0,
            "processing": 47,
            "completed": 274,
        },
        {
            "stage": "验收",
            "total": 300,
            "unassigned": 0,
            "assigned_waiting": 86,
            "processing": 32,
            "completed": 182,
        },
    ],
    "demo 项目": [
        {
            "stage": "质检",
            "total": 356,
            "unassigned": 0,
            "assigned_waiting": 140,
            "processing": 18,
            "completed": 198,
        },
        {
            "stage": "标注",
            "total": 278,
            "unassigned": 0,
            "assigned_waiting": 0,
            "processing": 21,
            "completed": 257,
        },
        {
            "stage": "验收",
            "total": 163,
            "unassigned": 42,
            "assigned_waiting": 0,
            "processing": 10,
            "completed": 111,
        },
    ],
    "预训练采集": [
        {
            "stage": "质检",
            "total": 272,
            "unassigned": 0,
            "assigned_waiting": 0,
            "processing": 12,
            "completed": 260,
        },
        {
            "stage": "标注",
            "total": 220,
            "unassigned": 0,
            "assigned_waiting": 186,
            "processing": 20,
            "completed": 14,
        },
        {
            "stage": "验收",
            "total": 82,
            "unassigned": 0,
            "assigned_waiting": 0,
            "processing": 12,
            "completed": 70,
        },
    ],
}

ALLOCATION_PROJECT_STALLED = {
    "全部项目": 74,
    "宁德项目": 52,
    "demo 项目": 14,
    "预训练采集": 8,
}

ALLOCATION_BACKLOGS = [
    {
        "id": "ALLOC-QC-0719",
        "stage": "质检",
        "task": "PROC-2026-0921",
        "project": "宁德项目",
        "count": 96,
        "status": "未分配",
        "supplier": "—",
        "operator": "—",
        "stalled": "26 小时",
        "priority": "P0",
    },
    {
        "id": "ALLOC-QC-0720",
        "stage": "质检",
        "task": "PROC-2026-0922",
        "project": "demo 项目",
        "count": 140,
        "status": "已分配未处理",
        "supplier": "光轮智能",
        "operator": "包媛桐",
        "stalled": "18 小时",
        "priority": "P1",
    },
    {
        "id": "ALLOC-LB-0314",
        "stage": "标注",
        "task": "PROC-2026-0922",
        "project": "宁德项目",
        "count": 124,
        "status": "未分配",
        "supplier": "—",
        "operator": "—",
        "stalled": "31 小时",
        "priority": "P0",
    },
    {
        "id": "ALLOC-LB-0315",
        "stage": "标注",
        "task": "PROC-2026-0921",
        "project": "预训练采集",
        "count": 186,
        "status": "已分配未处理",
        "supplier": "供应商 A",
        "operator": "供应商 A-017",
        "stalled": "14 小时",
        "priority": "P1",
    },
    {
        "id": "ALLOC-AC-0112",
        "stage": "验收",
        "task": "PROC-2026-0888",
        "project": "demo 项目",
        "count": 42,
        "status": "未分配",
        "supplier": "平台自有",
        "operator": "—",
        "stalled": "9 小时",
        "priority": "P1",
    },
    {
        "id": "ALLOC-AC-0113",
        "stage": "验收",
        "task": "PROC-2026-0922",
        "project": "宁德项目",
        "count": 86,
        "status": "已分配未处理",
        "supplier": "平台自有",
        "operator": "joanna.qiao",
        "stalled": "6 小时",
        "priority": "P1",
    },
]

STREAM_CAPACITY_BACKLOGS = [
    {
        "id": "STREAM-0718-QC",
        "project": "宁德项目",
        "source_task": "COL-2026-0718",
        "processing_task": "PROC-2026-0921",
        "workflow": "厨房数据质检流程 v3",
        "stage": "质检",
        "input_rate": 180,
        "throughput": 120,
        "backlog": 96,
        "supplier": "光轮智能",
        "operator": "包媛桐",
        "stalled": "26 小时",
        "priority": "P0",
    },
    {
        "id": "STREAM-0719-LB",
        "project": "demo 项目",
        "source_task": "COL-2026-0719",
        "processing_task": "PROC-2026-0922",
        "workflow": "家居动作标注流程 v2",
        "stage": "标注",
        "input_rate": 96,
        "throughput": 72,
        "backlog": 140,
        "supplier": "供应商 A",
        "operator": "供应商 A-017",
        "stalled": "18 小时",
        "priority": "P1",
    },
    {
        "id": "STREAM-0042-LB",
        "project": "预训练采集",
        "source_task": "IMP-2026-0042",
        "processing_task": "PROC-2026-0930",
        "workflow": "三方数据导入质检流程 v4",
        "stage": "标注",
        "input_rate": 220,
        "throughput": 128,
        "backlog": 186,
        "supplier": "供应商 A",
        "operator": "供应商 A-026",
        "stalled": "14 小时",
        "priority": "P1",
    },
    {
        "id": "STREAM-0718-AC",
        "project": "宁德项目",
        "source_task": "COL-2026-0718",
        "processing_task": "PROC-2026-0922",
        "workflow": "家居动作标注流程 v2",
        "stage": "验收",
        "input_rate": 84,
        "throughput": 56,
        "backlog": 86,
        "supplier": "平台自有",
        "operator": "joanna.qiao",
        "stalled": "6 小时",
        "priority": "P1",
    },
]

UNBOUND_DATA_POOLS = [
    {
        "id": "POOL-COL-0721",
        "project": "宁德项目",
        "source": "采集",
        "source_task": "COL-2026-0721",
        "count": 842,
        "created": "2026-07-27 08:30",
        "reason": "采集任务未绑定处理任务",
        "operator": "刘素粉",
    },
    {
        "id": "POOL-IMP-0048",
        "project": "预训练采集",
        "source": "导入",
        "source_task": "IMP-2026-0048",
        "count": 388,
        "created": "2026-07-26 19:10",
        "reason": "导入任务未指定处理任务",
        "operator": "数据导入服务",
    },
    {
        "id": "POOL-COL-0720",
        "project": "demo 项目",
        "source": "采集",
        "source_task": "COL-2026-0720",
        "count": 254,
        "created": "2026-07-27 10:06",
        "reason": "采集任务未绑定处理任务",
        "operator": "陈晨",
    },
]

REPROCESS_DATA_OVERVIEW = [
    {
        "project": "宁德项目",
        "source": "采集",
        "count": 1602,
        "current_process": "厨房数据质检流程 v3",
        "status": "质检完成 · 待标注",
    },
    {
        "project": "预训练采集",
        "source": "导入",
        "count": 1104,
        "current_process": "三方数据导入质检流程 v4",
        "status": "已完成",
    },
    {
        "project": "demo 项目",
        "source": "采集",
        "count": 1512,
        "current_process": "家居动作标注流程 v2",
        "status": "标注中",
    },
]

DATA_MANAGEMENT_RECORDS = [
    {
        "id": "4057808",
        "source_type": "collection",
        "source_task_id": "COL-2026-0718",
        "device": "UDAS-007",
        "operator": "刘素粉",
        "upload": "上传成功",
        "collection": "成功",
        "quality": "合格",
        "annotation": "已标注",
        "flows": [
            {
                "name": "厨房数据质检流程 v3",
                "node": "完整性质检",
                "quality": "合格",
                "annotation": "未标注",
            },
            {
                "name": "家居动作标注流程 v2",
                "node": "动作分段标注",
                "quality": "合格",
                "annotation": "已标注",
            },
        ],
        "versions": [
            ("v3", "2026-07-27 09:42", "合格", "已标注", "修正动作边界 2 处"),
            ("v2", "2026-07-26 18:10", "合格", "已标注", "完成动作分段初标"),
            ("v1", "2026-07-25 14:36", "操作失误", "未标注", "原始采集版本"),
        ],
    },
    {
        "id": "4057761",
        "source_type": "collection",
        "source_task_id": "COL-2026-0718",
        "device": "UDAS-007",
        "operator": "刘素粉",
        "upload": "上传成功",
        "collection": "成功",
        "quality": "合格",
        "annotation": "未标注",
        "flows": [
            {
                "name": "厨房数据质检流程 v3",
                "node": "Episode 切分",
                "quality": "合格",
                "annotation": "未标注",
            }
        ],
        "versions": [
            ("v2", "2026-07-27 08:22", "合格", "未标注", "完成质检与 Episode 切分"),
            ("v1", "2026-07-24 09:08", "操作失误", "未标注", "原始采集版本"),
        ],
    },
    {
        "id": "4057711",
        "source_type": "collection",
        "source_task_id": "COL-2026-0718",
        "device": "UDAS-007",
        "operator": "刘素粉",
        "upload": "上传中",
        "collection": "成功",
        "quality": "操作失误",
        "annotation": "未标注",
        "flows": [
            {
                "name": "厨房数据质检流程 v3",
                "node": "时间戳对齐",
                "quality": "操作失误",
                "annotation": "未标注",
            }
        ],
        "versions": [
            ("v1", "2026-07-24 08:46", "操作失误", "未标注", "原始采集版本"),
        ],
    },
    {
        "id": "4057669",
        "source_type": "collection",
        "source_task_id": "COL-2026-0718",
        "device": "UDAS-007",
        "operator": "刘素粉",
        "upload": "上传失败",
        "collection": "失败",
        "quality": "不合格",
        "annotation": "未标注",
        "flows": [
            {
                "name": "厨房数据质检流程 v3",
                "node": "完整性质检",
                "quality": "不合格",
                "annotation": "未标注",
            },
            {
                "name": "补采处理流程 v1",
                "node": "等待补采",
                "quality": "不合格",
                "annotation": "未标注",
            },
        ],
        "versions": [
            ("v2", "2026-07-26 16:03", "不合格", "未标注", "缺失右腕相机片段"),
            ("v1", "2026-07-24 08:15", "操作失误", "未标注", "原始采集版本"),
        ],
    },
    {
        "id": "vendor-12-001",
        "source_type": "import",
        "source_task_id": "IMP-2026-0042",
        "device": "Vendor-MOZ2-03",
        "operator": "供应商 Batch-12",
        "upload": "上传成功",
        "collection": "成功",
        "quality": "合格",
        "annotation": "已标注",
        "flows": [
            {
                "name": "三方数据导入质检流程 v4",
                "node": "格式标准化",
                "quality": "合格",
                "annotation": "已标注",
            },
            {
                "name": "三方标注复核流程 v2",
                "node": "标注复核",
                "quality": "合格",
                "annotation": "已标注",
            },
        ],
        "versions": [
            ("v3", "2026-07-26 20:18", "合格", "已标注", "完成标注复核"),
            ("v2", "2026-07-24 11:06", "合格", "未标注", "完成格式标准化"),
            ("v1", "2026-07-22 14:20", "操作失误", "已标注", "供应商原始版本"),
        ],
    },
    {
        "id": "vendor-12-002",
        "source_type": "import",
        "source_task_id": "IMP-2026-0042",
        "device": "Vendor-MOZ2-03",
        "operator": "供应商 Batch-12",
        "upload": "未上传",
        "collection": "失败",
        "quality": "操作失误",
        "annotation": "已标注",
        "flows": [
            {
                "name": "三方数据导入质检流程 v4",
                "node": "Schema 校验",
                "quality": "操作失误",
                "annotation": "已标注",
            }
        ],
        "versions": [
            ("v1", "2026-07-22 14:24", "操作失误", "已标注", "供应商原始版本"),
        ],
    },
]

THIRD_PARTY_DATASETS = [
    {
        "id": "TP-2026-001",
        "source": "HuggingFace",
        "name": "lerobot/OrganizePencilCase",
        "license": "CC-BY-4.0",
        "episodes": 1240,
        "size_gb": 48.2,
        "pulled_at": "2026-06-01",
        "status": "已入湖",
        "owner": "joanna.qiao",
    },
    {
        "id": "TP-2026-002",
        "source": "Bytedance Open",
        "name": "ByteRobot-HD-Pickup-v2",
        "license": "Apache-2.0",
        "episodes": 3200,
        "size_gb": 156.8,
        "pulled_at": "2026-05-28",
        "status": "已入湖",
        "owner": "Lance Li",
    },
    {
        "id": "TP-2026-003",
        "source": "HuggingFace",
        "name": "lerobot/AlohaSimTransferCube",
        "license": "Apache-2.0",
        "episodes": 800,
        "size_gb": 22.5,
        "pulled_at": "2026-05-25",
        "status": "已入湖",
        "owner": "joanna.qiao",
    },
    {
        "id": "TP-2026-004",
        "source": "外部供应商",
        "name": "千寻_厨房场景_合作采集_batch3",
        "license": "商业授权",
        "episodes": 560,
        "size_gb": 89.4,
        "pulled_at": "2026-06-05",
        "status": "入湖中",
        "owner": "Wei Zhang",
    },
    {
        "id": "TP-2026-005",
        "source": "Open X-Embodiment",
        "name": "berkeley_autolab_ur5",
        "license": "CC-BY-4.0",
        "episodes": 896,
        "size_gb": 34.7,
        "pulled_at": "2026-04-20",
        "status": "已入湖",
        "owner": "Min Chen",
    },
]

AUDIT_EVENTS = [
    ("2026-07-26 15:08:42", "submit_human_task", "ht-220976", "joanna.qiao", "HumanTaskSubmitted"),
    ("2026-07-26 14:56:11", "build_dataset_version", "dataset.moz1-household@4.0.0", "dataset-service", "DatasetVersionBuilt"),
    ("2026-07-26 14:58:02", "publish_dataset_version", "dataset.eval-general@2026q3", "Wei Zhang", "DatasetVersionPublished"),
    ("2026-07-26 10:02:35", "start_pipeline_run", "run-moz1-0921", "joanna.qiao", "PipelineRunStarted"),
]


# ---------------------------------------------------------------------------
# Validation: product invariants from the architecture proposal
# ---------------------------------------------------------------------------

def validate_architecture():
    errors = []

    all_page_keys = [key for _, keys in NAV_GROUPS for key in keys]
    if len(all_page_keys) != len(set(all_page_keys)):
        errors.append("navigation contains duplicate page keys")
    if set(all_page_keys) != set(PAGE_SPECS):
        errors.append("navigation and page registry are inconsistent")
    paths = [spec["path"] for spec in PAGE_SPECS.values()]
    if len(paths) != len(set(paths)):
        errors.append("page paths must be unique")

    for task_id, records in TASK_DETAIL_RECORDS.items():
        for record in records:
            if record["collection"] not in COLLECTION_CONCLUSIONS:
                errors.append(f"{task_id}/{record['id']} has an invalid collection conclusion")
            if record["quality"] not in QUALITY_CONCLUSIONS:
                errors.append(f"{task_id}/{record['id']} has an invalid quality conclusion")
            if record["annotation"] not in ANNOTATION_STATUSES:
                errors.append(f"{task_id}/{record['id']} has an invalid annotation status")

    for record in DATA_MANAGEMENT_RECORDS:
        record_ref = f"recording/{record['id']}"
        if record["source_type"] not in DATA_SOURCE_LABELS:
            errors.append(f"{record_ref} has an invalid data source")
        if record["upload"] not in UPLOAD_STATUSES:
            errors.append(f"{record_ref} has an invalid upload status")
        if record["collection"] not in COLLECTION_CONCLUSIONS:
            errors.append(f"{record_ref} has an invalid collection conclusion")
        if record["quality"] not in QUALITY_CONCLUSIONS:
            errors.append(f"{record_ref} has an invalid quality conclusion")
        if record["annotation"] not in ANNOTATION_STATUSES:
            errors.append(f"{record_ref} has an invalid annotation status")
        for flow in record["flows"]:
            if flow["quality"] not in QUALITY_CONCLUSIONS:
                errors.append(f"{record_ref}/{flow['name']} has an invalid quality conclusion")
            if flow["annotation"] not in ANNOTATION_STATUSES:
                errors.append(f"{record_ref}/{flow['name']} has an invalid annotation status")
        for version, _, quality, annotation, _ in record["versions"]:
            if quality not in QUALITY_CONCLUSIONS:
                errors.append(f"{record_ref}/{version} has an invalid quality conclusion")
            if annotation not in ANNOTATION_STATUSES:
                errors.append(f"{record_ref}/{version} has an invalid annotation status")

    if set(NODE_TYPES) != {"operator", "human", "gateway"}:
        errors.append("node type registry must contain operator, human and gateway")

    component_keys = set(WORKBENCH_COMPONENTS)
    schema_ids = {schema["id"] for schema in WORKBENCH_SCHEMAS}
    for schema in WORKBENCH_SCHEMAS:
        missing = set(schema["components"]) - component_keys
        if missing:
            errors.append(f"{schema['id']} references unknown components: {sorted(missing)}")
        if schema["status"] == "published" and not schema["frozen"]:
            errors.append(f"published workbench schema is mutable: {schema['id']}")

    pipeline_versions = set()
    pipelines_by_version = {}
    for definition in PIPELINE_DEFINITIONS:
        pipeline_versions.add(definition["published_version"])
        pipelines_by_version[definition["published_version"]] = definition
        if definition["status"] == "published" and not definition["frozen"]:
            errors.append(f"published pipeline is mutable: {definition['id']}")
        for _, node_type, binding in definition["nodes"]:
            if node_type not in NODE_TYPES:
                errors.append(f"{definition['id']} uses unknown node type: {node_type}")
            if node_type == "operator" and binding not in OPERATORS:
                errors.append(f"{definition['id']} references unknown operator: {binding}")
            if node_type == "human" and binding not in schema_ids:
                errors.append(f"{definition['id']} references unknown workbench schema: {binding}")
            if node_type == "gateway" and binding is not None:
                errors.append(f"{definition['id']} gateway bindings must be inline routing expressions")

    snapshot_ids = {snapshot["id"] for snapshot in DATA_SNAPSHOTS}
    run_ids = {run["id"] for run in PIPELINE_RUNS}
    runs_by_id = {run["id"]: run for run in PIPELINE_RUNS}
    business_task_ids = {task["id"] for task in BUSINESS_TASKS}
    for run in PIPELINE_RUNS:
        if run["business_task"] not in business_task_ids:
            errors.append(f"{run['id']} references an unknown business task")
        if run["pipeline_version"] not in pipeline_versions:
            errors.append(f"{run['id']} does not reference a published pipeline version")
        if run["input_snapshot"] not in snapshot_ids:
            errors.append(f"{run['id']} does not reference an immutable data snapshot")

    node_run_ids = {node_run["id"] for node_run in NODE_RUNS}
    for node_run in NODE_RUNS:
        if node_run["pipeline_run"] not in run_ids:
            errors.append(f"{node_run['id']} references an unknown pipeline run")
        if node_run["node_type"] not in NODE_TYPES:
            errors.append(f"{node_run['id']} uses an unknown node type")
        if node_run["input_snapshot"] not in snapshot_ids:
            errors.append(f"{node_run['id']} does not bind an input data snapshot")
        if node_run["attempt"] < 1:
            errors.append(f"{node_run['id']} has an invalid attempt number")
        run = runs_by_id.get(node_run["pipeline_run"])
        if run and run["pipeline_version"] in pipelines_by_version:
            definition = pipelines_by_version[run["pipeline_version"]]
            base_node_name = node_run["node"].split(" · ", 1)[0]
            registered_nodes = {
                name: (node_type, binding)
                for name, node_type, binding in definition["nodes"]
            }
            if base_node_name not in registered_nodes:
                errors.append(f"{node_run['id']} is not present in its pipeline version")
            else:
                expected_type, expected_binding = registered_nodes[base_node_name]
                if node_run["node_type"] != expected_type:
                    errors.append(f"{node_run['id']} has a node type mismatch")
                if expected_binding and node_run["executor_version"] != expected_binding:
                    errors.append(f"{node_run['id']} has an executor version mismatch")

    required_human_task_fields = {
        "business_task",
        "pipeline_run",
        "node_run",
        "data_scope",
        "sop",
        "priority",
        "sla",
    }
    for task in HUMAN_TASKS:
        missing = [field for field in required_human_task_fields if not task.get(field)]
        if missing:
            errors.append(f"{task['id']} is missing required associations: {missing}")
        if task["business_task"] not in business_task_ids:
            errors.append(f"{task['id']} references an unknown business task")
        if task["pipeline_run"] not in run_ids:
            errors.append(f"{task['id']} references an unknown pipeline run")
        if task["node_run"] not in node_run_ids:
            errors.append(f"{task['id']} references an unknown node run")

    for version in DATASET_VERSIONS:
        if version["status"] == "published":
            if version["snapshot"] not in snapshot_ids:
                errors.append(f"published dataset has no immutable snapshot: {version['id']}")
            if not version["immutable"]:
                errors.append(f"published dataset is mutable: {version['id']}")

    return errors


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _e(value):
    return escape(str(value), quote=True)


def _state(value):
    normalized = str(value).lower()
    tone = {
        "running": "blue",
        "in_progress": "blue",
        "pending": "gray",
        "draft": "gray",
        "frozen": "purple",
        "published": "green",
        "succeeded": "green",
        "failed": "red",
    }.get(normalized, "gray")
    label = {
        "running": "运行中",
        "in_progress": "处理中",
        "pending": "待处理",
        "draft": "草稿",
        "frozen": "已冻结",
        "published": "已发布",
        "succeeded": "已完成",
    }.get(normalized, value)
    return f'<span class="dpr-state {tone}">{_e(label)}</span>'


def _intro(title, subtitle, eyebrow="DATA PIPELINE", action_html=""):
    eyebrow_html = f'<div class="dpr-eyebrow">{_e(eyebrow)}</div>' if eyebrow else ""
    return f"""
    <div class="dpr-intro">
      <div>
        {eyebrow_html}
        <h1>{_e(title)}</h1>
        <p>{_e(subtitle)}</p>
      </div>
      <div class="dpr-intro-actions">{action_html}</div>
    </div>
    """


def _metrics(items):
    cards = "".join(
        f"""
        <div class="dpr-metric">
          <div class="dpr-metric-label">{_e(label)}</div>
          <div class="dpr-metric-value">{value}</div>
          <div class="dpr-metric-sub">{sub}</div>
        </div>
        """
        for label, value, sub in items
    )
    return f'<div class="dpr-metrics">{cards}</div>'


def _progress(value):
    return f"""
    <div class="dpr-progress">
      <div class="dpr-progress-track"><span style="width:{int(value)}%"></span></div>
      <b>{int(value)}%</b>
    </div>
    """


def _task_progress(label, done, total, tone="teal"):
    percent = round(done / total * 100) if total else 0
    return f"""
    <div class="dpr-task-progress-item" data-progress-stage="{_e(label)}">
      <span class="dpr-task-progress-label">{_e(label)}</span>
      <div class="dpr-task-progress-line">
        <i class="{_e(tone)}" style="width:{percent}%"></i>
        <b>{done:,} / {total:,} · {percent}%</b>
      </div>
    </div>
    """


def _record_tag(value):
    tone = {
        "采集": "teal",
        "导入": "blue",
        "上传": "blue",
        "质检": "blue",
        "标注": "purple",
        "验收": "orange",
        "交付验收": "orange",
        "成功": "green",
        "上传成功": "green",
        "已完成": "green",
        "已标注": "green",
        "已入湖": "green",
        "合格": "green",
        "失败": "red",
        "不合格": "red",
        "操作失误": "red",
        "进行中": "orange",
        "上传中": "blue",
        "标注中": "orange",
        "待复核": "orange",
        "入湖中": "orange",
        "待处理": "gray",
        "待质检": "gray",
        "未标注": "gray",
        "待验收": "gray",
        "未上传": "gray",
        "上传失败": "red",
        "未分配": "red",
        "已分配未处理": "orange",
    }.get(value, "gray")
    return f'<span class="dpr-record-tag {tone}">{_e(value)}</span>'


def _table(headers, rows, empty="暂无数据", table_id="", row_attrs=None):
    head = "".join(f"<th>{_e(item)}</th>" for item in headers)
    row_attrs = row_attrs or [""] * len(rows)
    body = "".join(
        f"<tr{' ' + attrs if attrs else ''}>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row, attrs in zip(rows, row_attrs)
    )
    if not body:
        body = f'<tr><td colspan="{len(headers)}" class="dpr-empty">{_e(empty)}</td></tr>'
    table_id_attr = f' id="{_e(table_id)}"' if table_id else ""
    return f"""
    <div class="dpr-table-wrap">
      <table class="dpr-table"{table_id_attr}>
        <thead><tr>{head}</tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
    """


def _section(title, body, subtitle="", actions=""):
    sub = f'<p>{_e(subtitle)}</p>' if subtitle else ""
    return f"""
    <section class="dpr-section">
      <div class="dpr-section-head">
        <div><h2>{_e(title)}</h2>{sub}</div>
        <div>{actions}</div>
      </div>
      {body}
    </section>
    """


def _code_list(values):
    return "".join(f'<code class="dpr-code">{_e(item)}</code>' for item in values)


# ---------------------------------------------------------------------------
# Product page renderers
# ---------------------------------------------------------------------------

def render_workspace():
    role_options = "".join(f"<option>{_e(name)}</option>" for name, _ in ROLES)
    action = f"""
    <label class="dpr-role">
      <span>当前角色</span>
      <select>{role_options}</select>
    </label>
    """
    intro = _intro(
        "我的数据工作空间",
        "当前项目：宁德时代 / Moz1 家居操作 SFT 数据交付。",
        "PROJECT · PRJ-MOZ1-SFT-07",
        action,
    )
    metrics = _metrics(
        [
            ("我的人工待办", "12", '<span class="dpr-risk">2 个 P0 即将超时</span>'),
            ("负责的运行", "3", "2 运行中 · 1 已完成"),
            ("处理异常", "2", "设备离线 1 · 导入失败 1"),
            ("待发布版本", "2", "1 个等待发布审批"),
        ]
    )
    role_cards = """
    <div class="dpr-role-grid">
      <a class="dpr-role-card" href="/data/operations"><b>项目 / 数据运营</b><span>交付范围、风险、周期和成本</span><em>查看交付看板 →</em></a>
      <a class="dpr-role-card" href="/data/task-pool"><b>数据工厂管理员</b><span>任务分配、人员技能、SLA 和产能</span><em>管理人工任务池 →</em></a>
      <a class="dpr-role-card" href="/data/task-pool"><b>生产执行人员</b><span>领取、暂存、提交和连续下一条</span><em>进入人工任务池 →</em></a>
      <a class="dpr-role-card" href="/data/capabilities"><b>算法 / 数据工程师</b><span>算子注册、运行分析、检索和血缘</span><em>管理执行能力 →</em></a>
      <a class="dpr-role-card" href="/data/dataset-versions"><b>数据集管理员</b><span>构建、冻结、发布与下游引用</span><em>管理数据集版本 →</em></a>
      <a class="dpr-role-card" href="/data/capabilities"><b>平台管理员</b><span>权限、配额、集成、日志和监控</span><em>管理平台能力 →</em></a>
    </div>
    """
    run_cards = ""
    for run in PIPELINE_RUNS[:2]:
        run_cards += f"""
        <a class="dpr-run-card" href="/data/pipeline-runs">
          <div class="dpr-run-top"><code>{_e(run['id'])}</code>{_state(run['status'])}</div>
          <b>{_e(run['business_task'])} · {_e(run['current_node'])}</b>
          <div class="dpr-run-meta"><span>{_e(run['pipeline_version'])}</span><span>{_e(run['input_snapshot'])}</span></div>
          <div class="dpr-stage-rail">
            <i class="done"></i><i class="done"></i><i class="active"></i><i></i><i></i><i></i><i></i>
          </div>
          <small>节点进度 {_e(run['node_progress'])} · 输入与版本已固定</small>
        </a>
        """
    return (
        intro
        + metrics
        + _section("按角色进入核心任务", role_cards)
        + _section("运行中的交付链路", f'<div class="dpr-run-grid">{run_cards}</div>')
    )


def render_projects():
    rows = []
    for item in PROJECTS:
        risk_cls = "dpr-ok" if item["risk"] == "进度正常" else "dpr-risk"
        rows.append(
            [
                f'<code>{_e(item["id"])}</code><br><b>{_e(item["name"])}</b>',
                _e(item["owner"]),
                _e(item["scope"]),
                _e(item["target"]),
                _progress(item["progress"]),
                f'<span class="{risk_cls}">{_e(item["risk"])}</span><br><small>{_e(item["due"])}</small>',
                '<a href="/data/tasks">任务</a> · <a href="/data/pipeline-runs">运行</a>',
            ]
        )
    return (
        _intro("项目管理", "管理项目成员、数据范围、交付目标、进度与预算。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 新建项目\');return false;">+ 新建项目</a>')
        + _metrics([("进行中项目", "3", "跨 2 个机器人构型"), ("本月交付目标", "21,200 EP", "已完成 13,764 EP"), ("处理异常", "2", "均已关联责任任务"), ("预算使用", "68%", "按项目统一归集")])
        + _section("项目列表", _table(["项目", "负责人", "数据范围", "交付目标", "进度", "风险 / 截止", "操作"], rows))
    )


def _task_filter_bar(fields):
    controls = []
    for label, control_type, options in fields:
        if control_type == "input":
            controls.append(
                f'<div class="ff"><label>{_e(label)}</label>'
                f'<input placeholder="请输入{_e(label)}"></div>'
            )
        else:
            option_html = "".join(f"<option>{_e(option)}</option>" for option in options)
            controls.append(
                f'<div class="ff"><label>{_e(label)}</label><select>{option_html}</select></div>'
            )
    return f"""
    <div class="fb-labeled dpr-task-filters">
      {''.join(controls)}
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>
    """


def render_collection_tasks():
    tab_specs = [
        ("instruction", "指令采集"),
        ("free", "自由采集"),
        ("dagger", "DAgger 采集"),
    ]
    tasks = [item for item in BUSINESS_TASKS if item["type"] == "data_collection_task"]
    counts = {
        mode: sum(1 for item in tasks if item["collection_mode"] == mode)
        for mode, _ in tab_specs
    }
    tabs = "".join(
        f'<button type="button" class="dpr-task-tab{" active" if index == 0 else ""}" '
        f'data-task-mode="{_e(mode)}" onclick="dprSwitchCollectionTab(this, \'{_e(mode)}\')">'
        f'{_e(label)} <b>{counts[mode]}</b></button>'
        for index, (mode, label) in enumerate(tab_specs)
    )
    rows = []
    row_attrs = []
    for item in tasks:
        detail_path = f'/data/tasks/{_e(item["id"])}'
        project_label = TASK_PROJECT_LABELS[item["project"]]
        processing_task = COLLECTION_PROCESSING_BINDINGS.get(item["id"], "")
        drawer_data = (
            f'data-task-id="{_e(item["id"])}" '
            f'data-task-name="{_e(item["name"])}" '
            f'data-collection-type="{_e(item["type_name"])}" '
            f'data-project="{_e(project_label)}" '
            f'data-priority="{_e(item["priority"])}" '
            f'data-processing-task="{_e(processing_task)}"'
        )
        rows.append(
            [
                f'<code>{_e(item["id"])}</code>',
                f'<a class="dpr-task-name" href="{detail_path}"><b>{_e(item["name"])}</b></a>',
                _record_tag(item["type_name"]),
                _progress(item["progress"]),
                f'<span class="dpr-priority">{_e(item["priority"])}</span>',
                _e(item["operator"]),
                _e(item["creator"]),
                _e(item["created"]),
                (
                    f'<div class="dpr-task-actions">'
                    f'<a href="{detail_path}">数据</a>'
                    f'<button type="button" {drawer_data} '
                    f'onclick="dprOpenCollectionTaskDrawer(\'detail\', this)">详情</button>'
                    f'<button type="button" {drawer_data} '
                    f'onclick="dprOpenCollectionTaskDrawer(\'edit\', this)">编辑</button>'
                    f"</div>"
                ),
            ]
        )
        hidden = "" if item["collection_mode"] == "instruction" else ' style="display:none;"'
        row_attrs.append(f'data-task-mode="{_e(item["collection_mode"])}"{hidden}')
    filters = _task_filter_bar(
        [
            ("任务 ID", "input", []),
            ("名称", "input", []),
            ("类型", "select", ["全部类型", "指令采集", "自由采集", "DAgger 采集"]),
            ("操作人", "select", ["全部操作人", "刘素粉", "王一帆", "采集团队 B", "供应商 A", "DAgger 小组"]),
        ]
    )
    table = _table(
        ["任务 ID", "名称", "类型", "进度", "优先级", "操作人", "创建人", "创建时间", "操作"],
        rows,
        table_id="dpr-collection-task-table",
        row_attrs=row_attrs,
    )
    body = f"""
    <div class="dpr-toolbar">
      <div class="dpr-task-tabs" role="tablist">{tabs}</div>
      <button type="button" class="btn btn-primary"
        onclick="dprOpenCollectionTaskDrawer('new')">+ 新建采集任务</button>
    </div>
    {filters}
    {table}
    <div class="drawer dpr-collection-drawer" id="drawerCollectionTaskForm" data-mode="new">
      <div class="drawer-head">
        <h3 id="collectionTaskDrawerTitle">新建采集任务</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="fg">
          <label class="fg-req">任务名称</label>
          <input id="collectionTaskName" name="task_name" placeholder="请输入采集任务名称">
        </div>
        <div class="fg">
          <label class="fg-req">采集类型</label>
          <select id="collectionTaskType" name="collection_type">
            <option>指令采集</option>
            <option>自由采集</option>
            <option>DAgger 采集</option>
          </select>
        </div>
        <div class="fg">
          <label class="fg-req">所属项目</label>
          <select id="collectionTaskProject" name="project">
            <option>预训练采集</option>
            <option>demo 项目</option>
            <option>宁德项目</option>
          </select>
        </div>
        <div class="fg">
          <label class="fg-req">优先级</label>
          <select id="collectionTaskPriority" name="priority">
            <option>中</option>
            <option>高</option>
            <option>低</option>
          </select>
        </div>
        <div class="fg">
          <label>处理任务 <span class="dpr-optional">（可选，选择则流式流转）</span></label>
          <select id="collectionTaskProcessing" name="processing_task">
            <option value="">不关联处理任务</option>
            <option value="PROC-2026-0921">PROC-2026-0921 · 厨房数据标准化处理</option>
            <option value="PROC-2026-0922">PROC-2026-0922 · 家居动作分段标注</option>
            <option value="PROC-2026-0888">PROC-2026-0888 · 通用评测集季度构建</option>
          </select>
          <div class="dpr-field-help">选择后，采集产生的数据将持续流转到对应处理任务。</div>
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn btn-primary" id="collectionTaskDrawerSubmit"
          onclick="dprSubmitCollectionTask()">创建</button>
      </div>
    </div>
    <script>
    function dprSwitchCollectionTab(button, taskMode) {{
      document.querySelectorAll('.dpr-task-tab').forEach(function(tab) {{
        tab.classList.toggle('active', tab === button);
      }});
      document.querySelectorAll('#dpr-collection-task-table tbody tr').forEach(function(row) {{
        row.style.display = row.dataset.taskMode === taskMode ? '' : 'none';
      }});
    }}
    function dprOpenCollectionTaskDrawer(mode, trigger) {{
      var data = trigger ? trigger.dataset : {{
        taskName: '',
        collectionType: '指令采集',
        project: '预训练采集',
        priority: '中',
        processingTask: ''
      }};
      var drawer = document.getElementById('drawerCollectionTaskForm');
      var isDetail = mode === 'detail';
      drawer.dataset.mode = mode;
      document.getElementById('collectionTaskDrawerTitle').textContent =
        mode === 'new' ? '新建采集任务' : (isDetail ? '采集任务详情' : '编辑采集任务');
      document.getElementById('collectionTaskName').value = data.taskName || '';
      document.getElementById('collectionTaskType').value = data.collectionType || '指令采集';
      document.getElementById('collectionTaskProject').value = data.project || '预训练采集';
      document.getElementById('collectionTaskPriority').value = data.priority || '中';
      document.getElementById('collectionTaskProcessing').value = data.processingTask || '';
      drawer.querySelectorAll('input, select').forEach(function(control) {{
        control.disabled = isDetail;
      }});
      var submit = document.getElementById('collectionTaskDrawerSubmit');
      submit.style.display = isDetail ? 'none' : '';
      submit.textContent = mode === 'new' ? '创建' : '保存';
      openDrawer('drawerCollectionTaskForm');
    }}
    function dprSubmitCollectionTask() {{
      var mode = document.getElementById('drawerCollectionTaskForm').dataset.mode;
      toast(mode === 'new' ? 'Demo: 已创建采集任务' : 'Demo: 已保存采集任务');
      closeDrawer();
    }}
    </script>
    """
    return _intro(
        "采集任务",
        "管理数据采集任务，支持指令采集、自由采集和 DAgger 采集三种模式，适配预训练与 Demo 场景。",
        "",
    ) + body


def render_processing_tasks():
    workflow_names = list(PROCESSING_FLOW_HUMAN_NODES)
    workflow_options = "".join(
        f"<option>{_e(workflow_name)}</option>"
        for workflow_name in workflow_names
    )
    flow_nodes_json = json.dumps(
        PROCESSING_FLOW_HUMAN_NODES,
        ensure_ascii=False,
    ).replace("</", "<\\/")
    tab_specs = [
        ("cleaning", "质检环节"),
        ("annotation", "标注环节"),
        ("acceptance", "验收环节"),
    ]
    tasks = [item for item in BUSINESS_TASKS if item["type"] == "data_processing_task"]
    counts = {
        stage: sum(1 for item in tasks if item["processing_stage"] == stage)
        for stage, _ in tab_specs
    }
    tabs = "".join(
        f'<button type="button" class="dpr-task-tab{" active" if index == 0 else ""}" '
        f'data-processing-stage="{_e(stage)}" onclick="dprSwitchProcessingTab(this, \'{_e(stage)}\')">'
        f'{_e(label)} <b>{counts[stage]}</b></button>'
        for index, (stage, label) in enumerate(tab_specs)
    )
    rows = []
    row_attrs = []
    for item in tasks:
        detail_path = f'/data/tasks/{_e(item["id"])}'
        project_label = TASK_PROJECT_LABELS[item["project"]]
        drawer_data = (
            f'data-task-id="{_e(item["id"])}" '
            f'data-task-name="{_e(item["name"])}" '
            f'data-project="{_e(project_label)}" '
            f'data-priority="{_e(item["priority"])}" '
            f'data-workflow="{_e(item["flow_name"])}"'
        )
        stage_tones = {"质检": "blue", "标注": "teal", "验收": "green"}
        progress_stack = (
            '<div class="dpr-task-progress-stack">'
            + "".join(
                _task_progress(
                    stage["label"],
                    stage["done"],
                    stage["total"],
                    stage_tones[stage["label"]],
                )
                for stage in item["stage_progress"]
            )
            + "</div>"
        )
        rows.append(
            [
                f'<code>{_e(item["id"])}</code>',
                f'<a class="dpr-task-name" href="{detail_path}"><b>{_e(item["name"])}</b></a>',
                _e(item["flow_name"]),
                _record_tag(item["node_name"]),
                progress_stack,
                f'<span class="dpr-priority">{_e(item["priority"])}</span>',
                _e(item["operator"]),
                _e(item["creator"]),
                _e(item["created"]),
                (
                    f'<div class="dpr-task-actions">'
                    f'<a href="{detail_path}">数据</a>'
                    f'<button type="button" {drawer_data} '
                    f'onclick="dprOpenProcessingTaskDrawer(\'detail\', this)">详情</button>'
                    f'<button type="button" {drawer_data} '
                    f'onclick="dprOpenProcessingTaskDrawer(\'edit\', this)">编辑</button>'
                    f"</div>"
                ),
            ]
        )
        hidden = "" if item["processing_stage"] == "cleaning" else ' style="display:none;"'
        row_attrs.append(f'data-processing-stage="{_e(item["processing_stage"])}"{hidden}')
    filters = _task_filter_bar(
        [
            ("任务 ID", "input", []),
            ("名称", "input", []),
            ("流程", "select", ["全部流程", *workflow_names]),
            ("节点", "select", ["全部节点", "时间戳对齐", "动作分段标注", "交付验收"]),
            ("操作人", "select", ["全部操作人", "包媛桐", "供应商 A", "Wei Zhang"]),
        ]
    )
    table = _table(
        ["任务 ID", "名称", "流程", "节点", "进度", "优先级", "操作人", "创建人", "创建时间", "操作"],
        rows,
        table_id="dpr-processing-task-table",
        row_attrs=row_attrs,
    )
    body = f"""
    <div class="dpr-toolbar">
      <div class="dpr-task-tabs" role="tablist">{tabs}</div>
      <button type="button" class="btn btn-primary"
        onclick="dprOpenProcessingTaskDrawer('new')">+ 新建处理任务</button>
    </div>
    {filters}
    {table}
    <div class="drawer dpr-collection-drawer dpr-processing-drawer" id="drawerProcessingTaskForm" data-mode="new">
      <div class="drawer-head">
        <h3 id="processingTaskDrawerTitle">新建处理任务</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="fg">
          <label class="fg-req">任务名称</label>
          <input id="processingTaskName" name="task_name" placeholder="请输入处理任务名称">
        </div>
        <div class="fg">
          <label class="fg-req">所属项目</label>
          <select id="processingTaskProject" name="project">
            <option>预训练采集</option>
            <option>demo 项目</option>
            <option>宁德项目</option>
          </select>
        </div>
        <div class="fg">
          <label class="fg-req">优先级</label>
          <select id="processingTaskPriority" name="priority">
            <option>中</option>
            <option>高</option>
            <option>低</option>
          </select>
        </div>
        <div class="fg">
          <label class="fg-req">处理流程（绑定工作流）</label>
          <select id="processingTaskWorkflow" name="workflow"
            onchange="dprRenderProcessingAssignments(this.value, false)">
            {workflow_options}
          </select>
          <div class="dpr-field-help">创建后将按所选工作流配置执行处理节点。</div>
        </div>
        <div class="dpr-processing-assignment">
          <div class="dpr-processing-assignment-title">
            <b>人工节点分配</b>
            <span>为所选流程中的每个人工节点配置供应商或操作员，并按比例分配。</span>
          </div>
          <div id="processingTaskAssignments"></div>
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn btn-primary" id="processingTaskDrawerSubmit"
          onclick="dprSubmitProcessingTask()">创建</button>
      </div>
    </div>
    <script>
    var DPR_PROCESSING_FLOW_NODES = {flow_nodes_json};
    var DPR_ASSIGNMENT_TARGETS = {{
      supplier: ['光轮智能', '供应商 A', '千寻数据'],
      operator: ['包媛桐', '刘素粉', '王一帆', 'Wei Zhang']
    }};
    function dprSwitchProcessingTab(button, processingStage) {{
      document.querySelectorAll('.dpr-task-tab').forEach(function(tab) {{
        tab.classList.toggle('active', tab === button);
      }});
      document.querySelectorAll('#dpr-processing-task-table tbody tr').forEach(function(row) {{
        row.style.display = row.dataset.processingStage === processingStage ? '' : 'none';
      }});
    }}
    function dprAssignmentEscape(value) {{
      return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
    }}
    function dprAssignmentTargetOptions(mode) {{
      return (DPR_ASSIGNMENT_TARGETS[mode] || []).map(function(name) {{
        return '<option>' + dprAssignmentEscape(name) + '</option>';
      }}).join('');
    }}
    function dprAssignmentRow(mode, percent, disabled) {{
      var disabledAttr = disabled ? ' disabled' : '';
      var deleteStyle = disabled ? ' style="display:none;"' : '';
      return '<div class="dpr-processing-assignment-row">' +
        '<select class="dpr-processing-assignment-target"' + disabledAttr + '>' +
          dprAssignmentTargetOptions(mode) + '</select>' +
        '<div class="dpr-processing-percent"><input type="number" min="0" max="100" value="' + percent +
          '" oninput="dprUpdateNodeAssignmentTotal(this.closest(\\'.dpr-processing-assignment-card\\'))"' +
          disabledAttr + '><span>%</span></div>' +
        '<button type="button" class="dpr-processing-assignment-remove" onclick="dprRemoveAssignmentTarget(this)"' +
          deleteStyle + '>&times;</button>' +
      '</div>';
    }}
    function dprRenderProcessingAssignments(workflow, isDetail) {{
      var holder = document.getElementById('processingTaskAssignments');
      var nodes = DPR_PROCESSING_FLOW_NODES[workflow] || [];
      if (!nodes.length) {{
        holder.innerHTML = '<div class="dpr-processing-assignment-empty">该流程不包含人工节点，无需配置处理人。</div>';
        return;
      }}
      holder.innerHTML = nodes.map(function(node) {{
        var disabledAttr = isDetail ? ' disabled' : '';
        var addStyle = isDetail ? ' style="display:none;"' : '';
        return '<div class="dpr-processing-assignment-card" data-assignment-node="' + dprAssignmentEscape(node) + '">' +
          '<div class="dpr-processing-assignment-head"><div><b>' + dprAssignmentEscape(node) +
            '</b><span>人工节点</span></div>' +
            '<label>分配方式<select class="dpr-processing-assignment-mode" onchange="dprSetNodeAssignmentMode(this)"' +
              disabledAttr + '><option value="supplier">供应商</option><option value="operator">操作员</option></select></label>' +
          '</div>' +
          '<div class="dpr-processing-assignment-cols"><span>分配对象</span><span>比例</span><span></span></div>' +
          '<div class="dpr-processing-assignment-rows">' + dprAssignmentRow('supplier', 100, isDetail) + '</div>' +
          '<div class="dpr-processing-assignment-foot"><button type="button" onclick="dprAddAssignmentTarget(this)"' +
            addStyle + '>+ 添加分配对象</button><span>合计 <b class="ok">100%</b></span></div>' +
        '</div>';
      }}).join('');
    }}
    function dprSetNodeAssignmentMode(select) {{
      var card = select.closest('.dpr-processing-assignment-card');
      card.querySelector('.dpr-processing-assignment-rows').innerHTML =
        dprAssignmentRow(select.value, 100, false);
      dprUpdateNodeAssignmentTotal(card);
    }}
    function dprAddAssignmentTarget(button) {{
      var card = button.closest('.dpr-processing-assignment-card');
      var mode = card.querySelector('.dpr-processing-assignment-mode').value;
      card.querySelector('.dpr-processing-assignment-rows').insertAdjacentHTML(
        'beforeend',
        dprAssignmentRow(mode, 0, false)
      );
      dprUpdateNodeAssignmentTotal(card);
    }}
    function dprRemoveAssignmentTarget(button) {{
      var card = button.closest('.dpr-processing-assignment-card');
      var rows = card.querySelectorAll('.dpr-processing-assignment-row');
      if (rows.length <= 1) {{
        toast('每个人工节点至少保留一个分配对象');
        return;
      }}
      button.closest('.dpr-processing-assignment-row').remove();
      dprUpdateNodeAssignmentTotal(card);
    }}
    function dprUpdateNodeAssignmentTotal(card) {{
      var total = 0;
      card.querySelectorAll('.dpr-processing-percent input').forEach(function(input) {{
        total += Number(input.value) || 0;
      }});
      var totalElement = card.querySelector('.dpr-processing-assignment-foot b');
      totalElement.textContent = total + '%';
      totalElement.className = total === 100 ? 'ok' : 'bad';
      return total;
    }}
    function dprProcessingAssignmentsValid() {{
      return Array.from(document.querySelectorAll('.dpr-processing-assignment-card')).every(function(card) {{
        return dprUpdateNodeAssignmentTotal(card) === 100;
      }});
    }}
    function dprOpenProcessingTaskDrawer(mode, trigger) {{
      var data = trigger ? trigger.dataset : {{
        taskName: '',
        project: '预训练采集',
        priority: '中',
        workflow: '多级复核数据处理流程'
      }};
      var drawer = document.getElementById('drawerProcessingTaskForm');
      var isDetail = mode === 'detail';
      drawer.dataset.mode = mode;
      document.getElementById('processingTaskDrawerTitle').textContent =
        mode === 'new' ? '新建处理任务' : (isDetail ? '处理任务详情' : '编辑处理任务');
      document.getElementById('processingTaskName').value = data.taskName || '';
      document.getElementById('processingTaskProject').value = data.project || '预训练采集';
      document.getElementById('processingTaskPriority').value = data.priority || '中';
      var workflow = DPR_PROCESSING_FLOW_NODES[data.workflow]
        ? data.workflow
        : '多级复核数据处理流程';
      document.getElementById('processingTaskWorkflow').value = workflow;
      dprRenderProcessingAssignments(workflow, isDetail);
      drawer.querySelectorAll('input, select').forEach(function(control) {{
        control.disabled = isDetail;
      }});
      var submit = document.getElementById('processingTaskDrawerSubmit');
      submit.style.display = isDetail ? 'none' : '';
      submit.textContent = mode === 'new' ? '创建' : '保存';
      openDrawer('drawerProcessingTaskForm');
    }}
    function dprSubmitProcessingTask() {{
      if (!dprProcessingAssignmentsValid()) {{
        toast('每个人工节点的分配比例需合计 100%');
        return;
      }}
      var mode = document.getElementById('drawerProcessingTaskForm').dataset.mode;
      toast(mode === 'new' ? 'Demo: 已创建处理任务' : 'Demo: 已保存处理任务');
      closeDrawer();
    }}
    </script>
    """
    return _intro(
        "处理任务",
        "管理数据处理任务；不同业务可绑定不同工作流，流程整体分为质检、标注和验收三个环节，每个环节可由多个节点组成。",
        "",
    ) + body


def _render_allocation_management_legacy():
    funnel_cards = ""
    for item in ALLOCATION_STAGE_SUMMARY:
        total = item["total"] or 1
        pending = item["unassigned"] + item["assigned_waiting"]
        segments = "".join(
            f'<i class="{tone}" style="width:{round(value / total * 100, 1)}%" '
            f'title="{_e(label)} {value:,} 条"></i>'
            for label, value, tone in (
                ("未分配", item["unassigned"], "unassigned"),
                ("已分配未处理", item["assigned_waiting"], "assigned"),
                ("处理中", item["processing"], "processing"),
                ("已完成", item["completed"], "completed"),
            )
        )
        funnel_cards += f"""
        <div class="dpr-allocation-stage" data-allocation-funnel-stage="{_e(item["stage"])}">
          <div class="dpr-allocation-stage-head">
            <div><b>{_e(item["stage"])}</b><span>进入环节 <span data-stage-total>{item["total"]:,}</span> 条</span></div>
            <strong data-stage-pending>{pending:,}<small>待处理</small></strong>
          </div>
          <div class="dpr-allocation-bar">{segments}</div>
          <div class="dpr-allocation-legend">
            <span><i class="unassigned"></i>未分配 <b data-stage-value="unassigned">{item["unassigned"]:,}</b></span>
            <span><i class="assigned"></i>已分配未处理 <b data-stage-value="assigned_waiting">{item["assigned_waiting"]:,}</b></span>
            <span><i class="processing"></i>处理中 <b data-stage-value="processing">{item["processing"]:,}</b></span>
            <span><i class="completed"></i>已完成 <b data-stage-value="completed">{item["completed"]:,}</b></span>
          </div>
        </div>
        """

    backlog_rows = []
    backlog_attrs = []
    for item in ALLOCATION_BACKLOGS:
        drawer_data = (
            f'data-batch-id="{_e(item["id"])}" '
            f'data-stage="{_e(item["stage"])}" '
            f'data-supplier="{_e(item["supplier"])}" '
            f'data-operator="{_e(item["operator"])}" '
            f'data-count="{item["count"]}"'
        )
        assignee = (
            '<span class="muted">尚未分配</span>'
            if item["status"] == "未分配"
            else f'{_e(item["supplier"])}<br><small>{_e(item["operator"])}</small>'
        )
        backlog_rows.append(
            [
                f'<input type="checkbox" class="dpr-allocation-check" '
                f'value="{_e(item["id"])}" onchange="dprUpdateAllocationSelection()">',
                f'<code>{_e(item["id"])}</code>',
                _record_tag(item["stage"]),
                f'<code>{_e(item["task"])}</code>',
                _e(item["project"]),
                f'<b>{item["count"]:,}</b> 条',
                _record_tag(item["status"]),
                assignee,
                f'<span class="dpr-stalled">{_e(item["stalled"])}</span>',
                f'<b>{_e(item["priority"])}</b>',
                f'<button type="button" class="dpr-link-button" {drawer_data} '
                f'onclick="dprOpenReassignDrawer(this)">重新分配</button>',
            ]
        )
        backlog_attrs.append(
            f'data-allocation-stage="{_e(item["stage"])}" '
            f'data-allocation-status="{_e(item["status"])}" '
            f'data-allocation-supplier="{_e(item["supplier"])}" '
            f'data-allocation-project="{_e(item["project"])}"'
        )

    backlog_filters = """
    <div class="fb-labeled dpr-allocation-filters">
      <div class="ff"><label>处理环节</label><select id="dprAllocationStage">
        <option value="">全部环节</option><option>质检</option><option>标注</option><option>验收</option>
      </select></div>
      <div class="ff"><label>分配状态</label><select id="dprAllocationStatus">
        <option value="">全部状态</option><option>未分配</option><option>已分配未处理</option>
      </select></div>
      <div class="ff"><label>供应商</label><select id="dprAllocationSupplier">
        <option value="">全部供应商</option><option>平台自有</option><option>光轮智能</option><option>供应商 A</option>
      </select></div>
      <div class="ff"><label>操作员</label><input id="dprAllocationOperator" placeholder="请输入操作员"></div>
      <div class="ff"><label>滞留时长</label><select id="dprAllocationStalled">
        <option value="">全部时长</option><option value="4">超过 4 小时</option>
        <option value="12">超过 12 小时</option><option value="24">超过 24 小时</option>
      </select></div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" type="button" onclick="dprResetAllocationFilters()">重置</button>
        <button class="btn btn-primary" type="button" onclick="dprFilterAllocationRows()">查询</button>
      </div>
    </div>
    """
    backlog_table = _table(
        [
            "",
            "批次 ID",
            "处理环节",
            "处理任务",
            "项目",
            "数据量",
            "分配状态",
            "供应商 / 操作员",
            "滞留时长",
            "优先级",
            "操作",
        ],
        backlog_rows,
        table_id="dpr-allocation-backlog-table",
        row_attrs=backlog_attrs,
    )
    backlog_section = _section(
        "待处理与滞留批次",
        backlog_filters
        + backlog_table
        + '<div class="dpr-allocation-table-foot">'
        + '<span>当前显示 <b id="dprAllocationVisibleCount">6</b> 个批次</span>'
        + '<button type="button" class="btn btn-primary" id="dprBulkReassign" '
        + 'disabled onclick="dprOpenReassignDrawer()">批量重新分配'
        + '（<span id="dprAllocationSelectedCount">0</span>）</button></div>',
        "仅展示未分配、已分配未处理的数据批次。",
    )

    allocation_metrics = """
    <div class="dpr-metrics">
      <div class="dpr-metric">
        <div class="dpr-metric-label">未分配</div>
        <div class="dpr-metric-value" data-allocation-metric="unassigned">262</div>
        <div class="dpr-metric-sub" data-allocation-metric-sub="unassigned">质检 96 · 标注 124 · 验收 42</div>
      </div>
      <div class="dpr-metric">
        <div class="dpr-metric-label">已分配未处理</div>
        <div class="dpr-metric-value" data-allocation-metric="assigned_waiting">412</div>
        <div class="dpr-metric-sub" data-allocation-metric-sub="assigned_waiting">质检 140 · 标注 186 · 验收 86</div>
      </div>
      <div class="dpr-metric">
        <div class="dpr-metric-label">处理中</div>
        <div class="dpr-metric-value" data-allocation-metric="processing">203</div>
        <div class="dpr-metric-sub">当前正在处理</div>
      </div>
      <div class="dpr-metric">
        <div class="dpr-metric-label">滞留超过 24 小时</div>
        <div class="dpr-metric-value" id="dprAllocationStalledMetric">74</div>
        <div class="dpr-metric-sub"><span class="dpr-risk">需要优先重新分配</span></div>
      </div>
    </div>
    """
    stage_tab = (
        allocation_metrics
        + _section(
            "处理环节数据漏斗",
            f'<div class="dpr-allocation-funnel">{funnel_cards}</div>',
            "按进入环节的数据量展示未分配、已分配未处理、处理中和已完成。",
        )
        + backlog_section
    )

    flow_overview_rows = [
        ["宁德项目", "采集", "642", "厨房数据质检流程 v3", "质检完成 · 待标注"],
        ["预训练采集", "导入", "388", "未关联", "可分配新流程"],
        ["demo 项目", "采集", "254", "家居动作标注流程 v2", "标注中"],
    ]
    flow_filters = """
    <div class="dpr-flow-assignment-filters">
      <div class="ff"><label>recording_id</label><input id="dprFlowRecordingId" placeholder="请输入 recording_id"></div>
      <div class="ff"><label>所属项目</label><select id="dprFlowProject">
        <option value="">全部项目</option><option>预训练采集</option><option>demo 项目</option><option>宁德项目</option>
      </select></div>
      <div class="ff"><label>数据来源</label><select id="dprFlowSource">
        <option value="">全部来源</option><option>采集</option><option>导入</option>
      </select></div>
      <div class="ff"><label>来源任务 ID</label><input id="dprFlowSourceTask" placeholder="请输入任务 ID"></div>
      <div class="ff"><label>质检结论</label><select id="dprFlowQuality">
        <option value="">全部结论</option><option>合格</option><option>不合格</option><option>操作失误</option>
      </select></div>
      <div class="ff"><label>标注状态</label><select id="dprFlowAnnotation">
        <option value="">全部状态</option><option>未标注</option><option>已标注</option>
      </select></div>
      <div class="ff"><label>当前处理流程</label><select id="dprFlowCurrentProcess">
        <option value="">全部流程状态</option><option>未关联流程</option>
        <option>厨房数据质检流程 v3</option><option>家居动作标注流程 v2</option>
      </select></div>
      <div class="filter-actions">
        <button type="button" class="btn btn-tertiary" onclick="dprResetFlowFilters()">重置</button>
        <button type="button" class="btn btn-primary" onclick="dprRunFlowFilter()">查询</button>
      </div>
    </div>
    """
    flow_result = f"""
    <div class="dpr-flow-match">
      <div><span>符合条件的数据</span><b><em id="dprFlowMatchCount">4,218</em> 条</b>
        <small id="dprFlowMatchHint">当前为全部可见数据</small></div>
      <button type="button" class="btn btn-primary" onclick="dprOpenFlowAssignmentDrawer()">
        分配新的处理流程
      </button>
    </div>
    """
    flow_tab = (
        _section(
            "筛选数据",
            flow_filters + flow_result,
            "组合筛选条件，确认命中数据量后批量分配新的处理流程。",
        )
        + _section(
            "命中数据概览",
            _table(
                ["项目", "数据来源", "数据量", "当前处理流程", "处理状态"],
                flow_overview_rows,
                table_id="dpr-allocation-flow-overview",
                row_attrs=[
                    'data-flow-project="宁德项目"',
                    'data-flow-project="预训练采集"',
                    'data-flow-project="demo 项目"',
                ],
            ),
        )
    )

    project_summary_json = json.dumps(
        ALLOCATION_PROJECT_STAGE_SUMMARY, ensure_ascii=False
    ).replace("</", "<\\/")
    project_stalled_json = json.dumps(
        ALLOCATION_PROJECT_STALLED, ensure_ascii=False
    ).replace("</", "<\\/")
    drawers_and_script = """
    <div class="drawer dpr-allocation-drawer" id="drawerReassignAllocation">
      <div class="drawer-head">
        <h3>重新分配处理数据</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-drawer-summary" id="dprReassignSummary">—</div>
        <div class="fg"><label>处理环节</label>
          <select id="dprReassignStage"><option>质检</option><option>标注</option><option>验收</option></select>
        </div>
        <div class="fg"><label class="fg-req">指定供应商</label>
          <select id="dprReassignSupplier" onchange="dprSyncOperatorOptions()">
            <option>平台自有</option><option>光轮智能</option><option>供应商 A</option>
          </select>
        </div>
        <div class="fg"><label class="fg-req">指定操作员</label>
          <select id="dprReassignOperator">
            <option>joanna.qiao</option><option>包媛桐</option><option>刘素粉</option><option>供应商 A-017</option>
          </select>
        </div>
        <div class="fg"><label>分配原因</label>
          <textarea id="dprReassignReason" rows="3" placeholder="请输入重新分配原因"></textarea>
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn btn-primary" onclick="dprSubmitReassignment()">确认分配</button>
      </div>
    </div>

    <div class="drawer dpr-allocation-drawer" id="drawerAssignProcess">
      <div class="drawer-head">
        <h3>分配新的处理流程</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-drawer-summary">已选择 <b id="dprAssignProcessCount">4,218</b> 条数据</div>
        <div class="fg"><label class="fg-req">处理流程</label>
          <select id="dprAssignProcessFlow">
            <option>厨房数据质检流程 v3</option><option>家居动作标注流程 v2</option><option>评测集质检流程 v4</option>
          </select>
        </div>
        <div class="fg"><label class="fg-req">起始环节</label>
          <select id="dprAssignProcessStage">
            <option>从流程起点开始</option><option>质检</option><option>标注</option><option>验收</option>
          </select>
        </div>
        <div class="fg"><label>优先级</label>
          <select id="dprAssignProcessPriority"><option>P1</option><option>P0</option><option>P2</option></select>
        </div>
        <div class="fg"><label>已有流程处理方式</label>
          <select id="dprAssignProcessStrategy">
            <option>新增处理流程（保留已有流程）</option><option>替换尚未开始的流程</option>
          </select>
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn btn-primary" onclick="dprSubmitFlowAssignment()">确认分配</button>
      </div>
    </div>

    <script>
    var dprAllocationProjectData = __ALLOCATION_PROJECT_DATA__;
    var dprAllocationProjectStalled = __ALLOCATION_PROJECT_STALLED__;
    var dprAllocationProjectFlowCounts = {
      '全部项目':4218,
      '宁德项目':1602,
      'demo 项目':1512,
      '预训练采集':1104
    };
    function dprAllocationProjectName() {
      return document.getElementById('dprAllocationProjectScope').value || '全部项目';
    }
    function dprUpdateAllocationProjectSummary() {
      var project = dprAllocationProjectName();
      var summaries = dprAllocationProjectData[project] || dprAllocationProjectData['全部项目'];
      var totals = {unassigned:0, assigned_waiting:0, processing:0};
      summaries.forEach(function(item) {
        totals.unassigned += item.unassigned;
        totals.assigned_waiting += item.assigned_waiting;
        totals.processing += item.processing;
        var card = document.querySelector(
          '[data-allocation-funnel-stage="' + item.stage + '"]'
        );
        if(!card) return;
        card.querySelector('[data-stage-total]').textContent = item.total.toLocaleString();
        card.querySelector('[data-stage-pending]').firstChild.nodeValue =
          (item.unassigned + item.assigned_waiting).toLocaleString();
        ['unassigned','assigned_waiting','processing','completed'].forEach(function(key) {
          var value = item[key];
          var segment = card.querySelector('.dpr-allocation-bar .' + (
            key === 'assigned_waiting' ? 'assigned' : key
          ));
          if(segment) {
            segment.style.width = (item.total ? value / item.total * 100 : 0).toFixed(1) + '%';
            segment.title = (
              key === 'unassigned' ? '未分配' :
              key === 'assigned_waiting' ? '已分配未处理' :
              key === 'processing' ? '处理中' : '已完成'
            ) + ' ' + value.toLocaleString() + ' 条';
          }
          card.querySelector('[data-stage-value="' + key + '"]').textContent =
            value.toLocaleString();
        });
      });
      ['unassigned','assigned_waiting','processing'].forEach(function(key) {
        document.querySelector('[data-allocation-metric="' + key + '"]').textContent =
          totals[key].toLocaleString();
      });
      ['unassigned','assigned_waiting'].forEach(function(key) {
        document.querySelector('[data-allocation-metric-sub="' + key + '"]').textContent =
          summaries.map(function(item) {
            return item.stage + ' ' + item[key].toLocaleString();
          }).join(' · ');
      });
      document.getElementById('dprAllocationStalledMetric').textContent =
        Number(dprAllocationProjectStalled[project] || 0).toLocaleString();
    }
    function dprAllocationRows() {
      return Array.prototype.slice.call(
        document.querySelectorAll('#dpr-allocation-backlog-table tbody tr')
      );
    }
    function dprUpdateAllocationSelection() {
      var selected = document.querySelectorAll('.dpr-allocation-check:checked').length;
      document.getElementById('dprAllocationSelectedCount').textContent = selected;
      document.getElementById('dprBulkReassign').disabled = selected === 0;
    }
    function dprFilterAllocationRows() {
      var stage = document.getElementById('dprAllocationStage').value;
      var status = document.getElementById('dprAllocationStatus').value;
      var supplier = document.getElementById('dprAllocationSupplier').value;
      var operator = document.getElementById('dprAllocationOperator').value.trim().toLowerCase();
      var stalled = Number(document.getElementById('dprAllocationStalled').value || 0);
      var project = dprAllocationProjectName();
      var visible = 0;
      dprAllocationRows().forEach(function(row) {
        var stalledHours = Number((row.querySelector('.dpr-stalled').textContent.match(/\\d+/) || [0])[0]);
        var matches = (project === '全部项目' || row.dataset.allocationProject === project)
          && (!stage || row.dataset.allocationStage === stage)
          && (!status || row.dataset.allocationStatus === status)
          && (!supplier || row.dataset.allocationSupplier === supplier)
          && (!operator || row.textContent.toLowerCase().indexOf(operator) >= 0)
          && (!stalled || stalledHours > stalled);
        row.style.display = matches ? '' : 'none';
        if(matches) visible += 1;
      });
      document.getElementById('dprAllocationVisibleCount').textContent = visible;
    }
    function dprFilterAllocationFlowOverview() {
      var project = document.getElementById('dprFlowProject').value;
      document.querySelectorAll('#dpr-allocation-flow-overview tbody tr').forEach(function(row) {
        row.style.display = !project || row.dataset.flowProject === project ? '' : 'none';
      });
    }
    function dprSelectAllocationProject() {
      var project = dprAllocationProjectName();
      document.querySelectorAll('.dpr-allocation-check:checked').forEach(function(item) {
        item.checked = false;
      });
      dprUpdateAllocationSelection();
      dprUpdateAllocationProjectSummary();
      dprFilterAllocationRows();
      var flowProject = document.getElementById('dprFlowProject');
      flowProject.value = project === '全部项目' ? '' : project;
      flowProject.disabled = project !== '全部项目';
      dprRunFlowFilter();
    }
    function dprResetAllocationFilters() {
      ['dprAllocationStage','dprAllocationStatus','dprAllocationSupplier','dprAllocationStalled']
        .forEach(function(id) { document.getElementById(id).selectedIndex = 0; });
      document.getElementById('dprAllocationOperator').value = '';
      dprFilterAllocationRows();
    }
    function dprOpenReassignDrawer(trigger) {
      var selected = Array.prototype.slice.call(
        document.querySelectorAll('.dpr-allocation-check:checked')
      );
      var count = 0;
      var summary = '';
      if(trigger) {
        count = Number(trigger.dataset.count || 0);
        summary = trigger.dataset.batchId + ' · ' + count.toLocaleString() + ' 条数据';
        document.getElementById('dprReassignStage').value = trigger.dataset.stage;
      } else {
        count = selected.reduce(function(total, checkbox) {
          var row = checkbox.closest('tr');
          var button = row.querySelector('[data-count]');
          return total + Number(button.dataset.count || 0);
        }, 0);
        summary = '已选 ' + selected.length + ' 个批次 · ' + count.toLocaleString() + ' 条数据';
      }
      document.getElementById('dprReassignSummary').textContent = summary;
      openDrawer('drawerReassignAllocation');
    }
    function dprSyncOperatorOptions() {
      var supplier = document.getElementById('dprReassignSupplier').value;
      var options = {
        '平台自有':['joanna.qiao','包媛桐'],
        '光轮智能':['刘素粉','光轮-QC-021'],
        '供应商 A':['供应商 A-017','供应商 A-026']
      };
      document.getElementById('dprReassignOperator').innerHTML =
        (options[supplier] || []).map(function(name) {
          return '<option>' + name + '</option>';
        }).join('');
    }
    function dprSubmitReassignment() {
      toast('Demo: 已重新分配到指定供应商和操作员');
      closeDrawer();
    }
    function dprRunFlowFilter() {
      var project = document.getElementById('dprFlowProject').value;
      var count = dprAllocationProjectFlowCounts[project || '全部项目'];
      var factors = [
        ['dprFlowSource', .72], ['dprFlowQuality', .31], ['dprFlowAnnotation', .58],
        ['dprFlowCurrentProcess', .46]
      ];
      factors.forEach(function(item) {
        if(document.getElementById(item[0]).value) count = Math.floor(count * item[1]);
      });
      if(document.getElementById('dprFlowSourceTask').value.trim()) count = Math.min(count, 842);
      if(document.getElementById('dprFlowRecordingId').value.trim()) count = 1;
      document.getElementById('dprFlowMatchCount').textContent = count.toLocaleString();
      document.getElementById('dprFlowMatchHint').textContent =
        count === 4218 ? '当前为全部可见数据' : '已按当前项目与筛选条件统计';
      dprFilterAllocationFlowOverview();
    }
    function dprResetFlowFilters() {
      ['dprFlowSource','dprFlowQuality','dprFlowAnnotation','dprFlowCurrentProcess']
        .forEach(function(id) { document.getElementById(id).selectedIndex = 0; });
      var project = dprAllocationProjectName();
      document.getElementById('dprFlowProject').value =
        project === '全部项目' ? '' : project;
      document.getElementById('dprFlowSourceTask').value = '';
      document.getElementById('dprFlowRecordingId').value = '';
      dprRunFlowFilter();
    }
    function dprOpenFlowAssignmentDrawer() {
      document.getElementById('dprAssignProcessCount').textContent =
        document.getElementById('dprFlowMatchCount').textContent;
      openDrawer('drawerAssignProcess');
    }
    function dprSubmitFlowAssignment() {
      toast('Demo: 已为筛选数据分配新的处理流程');
      closeDrawer();
    }
    dprSyncOperatorOptions();
    dprSelectAllocationProject();
    </script>
    """
    drawers_and_script = (
        drawers_and_script
        .replace("__ALLOCATION_PROJECT_DATA__", project_summary_json)
        .replace("__ALLOCATION_PROJECT_STALLED__", project_stalled_json)
    )

    project_switcher = """
    <label class="dpr-project-scope">
      <span>项目视角</span>
      <select id="dprAllocationProjectScope" onchange="dprSelectAllocationProject()">
        <option>全部项目</option>
        <option>宁德项目</option>
        <option>demo 项目</option>
        <option>预训练采集</option>
      </select>
    </label>
    """
    return (
        _intro(
            "分配管理",
            "查看质检、标注、验收环节的数据滞留，并批量分配供应商、操作员或新的处理流程。",
            "",
            project_switcher,
        )
        + f"""
        <div class="det-tabs dpr-allocation-tabs">
          <span class="det-tab active" onclick="switchDetTab(this,'allocation-stage')">环节分配</span>
          <span class="det-tab" onclick="switchDetTab(this,'allocation-flow')">流程分配</span>
        </div>
        <div id="det-pane-allocation-stage" class="det-pane active">{stage_tab}</div>
        <div id="det-pane-allocation-flow" class="det-pane">{flow_tab}</div>
        {drawers_and_script}
        """
    )


def render_allocation_management():
    project_switcher = """
    <label class="dpr-project-scope">
      <span>项目视角</span>
      <select id="dprAllocationProjectScope" onchange="dprSelectAllocationProject()">
        <option>全部项目</option>
        <option>宁德项目</option>
        <option>demo 项目</option>
        <option>预训练采集</option>
      </select>
    </label>
    """

    stream_rows = []
    stream_attrs = []
    for item in STREAM_CAPACITY_BACKLOGS:
        drawer_data = (
            f'data-stream-id="{_e(item["id"])}" '
            f'data-processing-task="{_e(item["processing_task"])}" '
            f'data-workflow="{_e(item["workflow"])}" '
            f'data-stage="{_e(item["stage"])}" '
            f'data-backlog="{item["backlog"]}"'
        )
        overload = round((item["input_rate"] / item["throughput"] - 1) * 100)
        stream_rows.append(
            [
                f'<input type="checkbox" class="dpr-stream-check" '
                f'value="{_e(item["id"])}" onchange="dprUpdateStreamSelection()">',
                f'<code>{_e(item["source_task"])}</code><br>'
                f'<small>流入 {_e(item["processing_task"])}</small>',
                _e(item["project"]),
                f'<b>{_e(item["workflow"])}</b><br><small>当前环节：{_e(item["stage"])}</small>',
                f'<span class="dpr-capacity-overload">'
                f'{item["input_rate"]} / {item["throughput"]} 条/小时</span>'
                f'<br><small>输入超出吞吐 {overload}%</small>',
                f'<b>{item["backlog"]:,}</b> 条',
                f'{_e(item["supplier"])}<br><small>{_e(item["operator"])}</small>',
                f'<span class="dpr-stalled">{_e(item["stalled"])}</span>',
                f'<b>{_e(item["priority"])}</b>',
                f'<button type="button" class="dpr-link-button" {drawer_data} '
                f'onclick="dprOpenStreamReassign(this)">重新指派</button>',
            ]
        )
        stream_attrs.append(
            f'data-project="{_e(item["project"])}" '
            f'data-stage="{_e(item["stage"])}" '
            f'data-supplier="{_e(item["supplier"])}" '
            f'data-operator="{_e(item["operator"])}" '
            f'data-task="{_e(item["source_task"])} {_e(item["processing_task"])}" '
            f'data-backlog="{item["backlog"]}"'
        )

    stream_filters = """
    <div class="fb-labeled dpr-allocation-filters">
      <div class="ff"><label>处理环节</label><select id="dprStreamStage">
        <option value="">全部环节</option><option>质检</option><option>标注</option><option>验收</option>
      </select></div>
      <div class="ff"><label>任务 ID</label>
        <input id="dprStreamTask" placeholder="采集任务 / 处理任务"></div>
      <div class="ff"><label>当前供应商</label><select id="dprStreamSupplier">
        <option value="">全部供应商</option><option>平台自有</option>
        <option>光轮智能</option><option>供应商 A</option>
      </select></div>
      <div class="ff"><label>当前处理人</label>
        <input id="dprStreamOperator" placeholder="请输入处理人"></div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" type="button" onclick="dprResetStreamFilters()">重置</button>
        <button class="btn btn-primary" type="button" onclick="dprFilterStreamRows()">查询</button>
      </div>
    </div>
    """
    stream_table = _table(
        [
            "",
            "流式来源 / 处理任务",
            "项目",
            "当前处理流程",
            "输入 / 吞吐",
            "积压数据",
            "当前供应商 / 处理人",
            "最长滞留",
            "优先级",
            "操作",
        ],
        stream_rows,
        table_id="dpr-stream-backlog-table",
        row_attrs=stream_attrs,
    )
    stream_tab = (
        """
        <div class="dpr-scenario-summary">
          <div><span>吞吐不足任务</span><b id="dprStreamVisibleTasks">4</b><small>个</small></div>
          <div><span>当前积压</span><b id="dprStreamBacklogCount">508</b><small>条</small></div>
          <p>当前处理流程保持不变，仅重新指派供应商和处理人。</p>
        </div>
        """
        + _section(
            "流式积压任务",
            stream_filters
            + stream_table
            + '<div class="dpr-allocation-table-foot">'
            + '<span>已选择 <b id="dprStreamSelectedCount">0</b> 个任务</span>'
            + '<button type="button" class="btn btn-primary" id="dprBulkStreamReassign" '
            + 'disabled onclick="dprOpenStreamReassign()">批量重新指派</button></div>',
            "当采集或导入速度持续高于处理吞吐时，重新调度执行资源。",
        )
    )

    unbound_rows = []
    unbound_attrs = []
    for item in UNBOUND_DATA_POOLS:
        drawer_data = (
            f'data-pool-id="{_e(item["id"])}" '
            f'data-source-task="{_e(item["source_task"])}" '
            f'data-count="{item["count"]}"'
        )
        unbound_rows.append(
            [
                f'<input type="checkbox" class="dpr-unbound-check" '
                f'value="{_e(item["id"])}" onchange="dprUpdateUnboundSelection()">',
                f'<code>{_e(item["id"])}</code>',
                _e(item["project"]),
                _record_tag(item["source"]),
                f'<code>{_e(item["source_task"])}</code>',
                f'<b>{item["count"]:,}</b> 条',
                _e(item["created"]),
                _e(item["reason"]),
                _e(item["operator"]),
                f'<button type="button" class="dpr-link-button" {drawer_data} '
                f'onclick="dprOpenBindTask(this)">指定处理任务</button>',
            ]
        )
        unbound_attrs.append(
            f'data-project="{_e(item["project"])}" '
            f'data-source="{_e(item["source"])}" '
            f'data-source-task="{_e(item["source_task"])}" '
            f'data-count="{item["count"]}"'
        )

    unbound_filters = """
    <div class="fb-labeled dpr-allocation-filters">
      <div class="ff"><label>数据来源</label><select id="dprUnboundSource">
        <option value="">全部来源</option><option>采集</option><option>导入</option>
      </select></div>
      <div class="ff"><label>来源任务 ID</label>
        <input id="dprUnboundTask" placeholder="请输入采集 / 导入任务 ID"></div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" type="button" onclick="dprResetUnboundFilters()">重置</button>
        <button class="btn btn-primary" type="button" onclick="dprFilterUnboundRows()">查询</button>
      </div>
    </div>
    """
    unbound_table = _table(
        [
            "",
            "数据池批次",
            "项目",
            "数据来源",
            "来源任务",
            "数据量",
            "进入数据池时间",
            "未绑定原因",
            "操作人",
            "操作",
        ],
        unbound_rows,
        table_id="dpr-unbound-pool-table",
        row_attrs=unbound_attrs,
    )
    unbound_tab = (
        """
        <div class="dpr-scenario-summary">
          <div><span>未绑定批次</span><b id="dprUnboundVisibleBatches">3</b><small>个</small></div>
          <div><span>待分配数据</span><b id="dprUnboundDataCount">1,484</b><small>条</small></div>
          <p>为池中数据指定处理任务，并为该任务绑定处理流程。</p>
        </div>
        """
        + _section(
            "未绑定处理任务的数据",
            unbound_filters
            + unbound_table
            + '<div class="dpr-allocation-table-foot">'
            + '<span>已选择 <b id="dprUnboundSelectedCount">0</b> 个批次</span>'
            + '<button type="button" class="btn btn-primary" id="dprBulkBindTask" '
            + 'disabled onclick="dprOpenBindTask()">批量指定处理任务</button></div>',
            "只展示尚未进入任何处理任务的数据。",
        )
    )

    reprocess_rows = [
        [
            _e(item["project"]),
            _record_tag(item["source"]),
            f'<b>{item["count"]:,}</b> 条',
            _e(item["current_process"]),
            _e(item["status"]),
        ]
        for item in REPROCESS_DATA_OVERVIEW
    ]
    reprocess_attrs = [
        f'data-project="{_e(item["project"])}"'
        for item in REPROCESS_DATA_OVERVIEW
    ]
    reprocess_filters = """
    <div class="dpr-flow-assignment-filters">
      <div class="ff"><label>recording_id</label>
        <input id="dprReprocessRecordingId" placeholder="请输入 recording_id"></div>
      <div class="ff"><label>数据来源</label><select id="dprReprocessSource">
        <option value="">全部来源</option><option>采集</option><option>导入</option>
      </select></div>
      <div class="ff"><label>来源任务 ID</label>
        <input id="dprReprocessSourceTask" placeholder="请输入任务 ID"></div>
      <div class="ff"><label>质检结论</label><select id="dprReprocessQuality">
        <option value="">全部结论</option><option>合格</option><option>不合格</option><option>操作失误</option>
      </select></div>
      <div class="ff"><label>标注状态</label><select id="dprReprocessAnnotation">
        <option value="">全部状态</option><option>未标注</option><option>已标注</option>
      </select></div>
      <div class="ff"><label>已有处理流程</label><select id="dprReprocessCurrentFlow">
        <option value="">全部流程</option><option>厨房数据质检流程 v3</option>
        <option>家居动作标注流程 v2</option><option>三方数据导入质检流程 v4</option>
      </select></div>
      <div class="filter-actions">
        <button type="button" class="btn btn-tertiary" onclick="dprResetReprocessFilters()">重置</button>
        <button type="button" class="btn btn-primary" onclick="dprRunReprocessFilter()">查询</button>
      </div>
    </div>
    """
    reprocess_tab = (
        _section(
            "筛选训练所需数据",
            reprocess_filters
            + """
            <div class="dpr-flow-match">
              <div><span>符合条件的数据</span>
                <b><em id="dprReprocessMatchCount">4,218</em> 条</b>
                <small id="dprReprocessMatchHint">当前为全部可见数据</small>
              </div>
              <button type="button" class="btn btn-primary"
                onclick="dprOpenReprocessDrawer()">发起再处理</button>
            </div>
            """,
            "无论数据是否处理过，都可以为本次训练需求新增一条处理流程。",
        )
        + _section(
            "命中数据概览",
            _table(
                ["项目", "数据来源", "数据量", "原处理流程", "原流程状态"],
                reprocess_rows,
                table_id="dpr-reprocess-overview",
                row_attrs=reprocess_attrs,
            ),
            "新增再处理流程时，可选择原流程继续运行或终止。",
        )
    )

    drawers_and_script = """
    <div class="drawer dpr-allocation-drawer" id="drawerStreamReassign">
      <div class="drawer-head">
        <h3>重新指派流式处理资源</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-drawer-summary" id="dprStreamReassignSummary">—</div>
        <div class="dpr-assignment-context">
          <span>当前处理任务<b id="dprStreamCurrentTask">—</b></span>
          <span>当前处理流程<b id="dprStreamCurrentWorkflow">—</b></span>
        </div>
        <div class="dpr-inline-notice">处理任务和处理流程保持不变，本次只调整执行资源。</div>
        <div class="fg"><label class="fg-req">重新指派供应商</label>
          <select id="dprStreamNewSupplier" onchange="dprSyncStreamOperators()">
            <option>平台自有</option><option>光轮智能</option><option>供应商 A</option>
          </select>
        </div>
        <div class="fg"><label class="fg-req">重新指派处理人</label>
          <select id="dprStreamNewOperator"></select>
        </div>
        <div class="fg"><label>指派原因</label>
          <textarea id="dprStreamReason" rows="3" placeholder="例如：当前处理吞吐不足"></textarea>
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn btn-primary" onclick="dprSubmitStreamReassign()">确认指派</button>
      </div>
    </div>

    <div class="drawer dpr-allocation-drawer" id="drawerBindProcessingTask">
      <div class="drawer-head">
        <h3>指定处理任务</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-drawer-summary" id="dprBindTaskSummary">—</div>
        <div class="fg"><label class="fg-req">处理任务</label>
          <select id="dprBindProcessingTask">
            <option>PROC-2026-0941 · 宁德采集数据处理</option>
            <option>PROC-2026-0942 · 预训练数据质检</option>
            <option>PROC-2026-0943 · Demo 数据处理</option>
          </select>
        </div>
        <div class="fg"><label class="fg-req">绑定处理流程</label>
          <select id="dprBindWorkflow">
            <option>厨房数据质检流程 v3</option>
            <option>家居动作标注流程 v2</option>
            <option>三方数据导入质检流程 v4</option>
          </select>
        </div>
        <div class="fg"><label>优先级</label>
          <select id="dprBindPriority"><option>P1</option><option>P0</option><option>P2</option></select>
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn btn-primary" onclick="dprSubmitBindTask()">确认绑定</button>
      </div>
    </div>

    <div class="drawer dpr-allocation-drawer" id="drawerCreateReprocess">
      <div class="drawer-head">
        <h3>发起数据再处理</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-drawer-summary">已命中 <b id="dprReprocessDrawerCount">4,218</b> 条数据</div>
        <div class="dpr-inline-notice success">新增再处理流程后，可选择保留或终止数据的原处理流程。</div>
        <div class="fg"><label class="fg-req">任务名称</label>
          <input id="dprReprocessTaskName" placeholder="请输入再处理任务名称">
        </div>
        <div class="fg"><label class="fg-req">处理流程</label>
          <select id="dprReprocessWorkflow">
            <option>训练数据专项质检流程 v1</option>
            <option>家居动作精标流程 v3</option>
            <option>评测数据复核流程 v2</option>
          </select>
        </div>
        <div class="fg"><label>优先级</label>
          <select id="dprReprocessPriority"><option>P1</option><option>P0</option><option>P2</option></select>
        </div>
        <div class="fg"><label class="fg-req">原流程</label>
          <select id="dprReprocessOriginalFlow">
            <option>继续</option><option>终止</option>
          </select>
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn btn-primary" onclick="dprSubmitReprocess()">确认发起</button>
      </div>
    </div>

    <script>
    function dprCurrentAllocationProject() {
      return document.getElementById('dprAllocationProjectScope').value;
    }
    function dprVisibleRows(tableId) {
      return Array.prototype.slice.call(
        document.querySelectorAll('#' + tableId + ' tbody tr')
      ).filter(function(row) { return row.style.display !== 'none'; });
    }
    function dprUpdateStreamSelection() {
      var selected = document.querySelectorAll('.dpr-stream-check:checked').length;
      document.getElementById('dprStreamSelectedCount').textContent = selected;
      document.getElementById('dprBulkStreamReassign').disabled = selected === 0;
    }
    function dprFilterStreamRows() {
      var project = dprCurrentAllocationProject();
      var stage = document.getElementById('dprStreamStage').value;
      var task = document.getElementById('dprStreamTask').value.trim().toLowerCase();
      var supplier = document.getElementById('dprStreamSupplier').value;
      var operator = document.getElementById('dprStreamOperator').value.trim().toLowerCase();
      var visible = 0;
      var backlog = 0;
      document.querySelectorAll('#dpr-stream-backlog-table tbody tr').forEach(function(row) {
        var matches = (project === '全部项目' || row.dataset.project === project)
          && (!stage || row.dataset.stage === stage)
          && (!task || row.dataset.task.toLowerCase().indexOf(task) >= 0)
          && (!supplier || row.dataset.supplier === supplier)
          && (!operator || row.dataset.operator.toLowerCase().indexOf(operator) >= 0);
        row.style.display = matches ? '' : 'none';
        if(matches) {
          visible += 1;
          backlog += Number(row.dataset.backlog || 0);
        }
      });
      document.getElementById('dprStreamVisibleTasks').textContent = visible;
      document.getElementById('dprStreamBacklogCount').textContent = backlog.toLocaleString();
    }
    function dprResetStreamFilters() {
      ['dprStreamStage','dprStreamSupplier'].forEach(function(id) {
        document.getElementById(id).selectedIndex = 0;
      });
      document.getElementById('dprStreamTask').value = '';
      document.getElementById('dprStreamOperator').value = '';
      dprFilterStreamRows();
    }
    function dprOpenStreamReassign(trigger) {
      var selected = Array.prototype.slice.call(
        document.querySelectorAll('.dpr-stream-check:checked')
      );
      if(trigger) {
        document.getElementById('dprStreamReassignSummary').textContent =
          trigger.dataset.streamId + ' · 积压 ' + Number(trigger.dataset.backlog).toLocaleString() + ' 条';
        document.getElementById('dprStreamCurrentTask').textContent =
          trigger.dataset.processingTask;
        document.getElementById('dprStreamCurrentWorkflow').textContent =
          trigger.dataset.workflow;
      } else {
        var count = selected.reduce(function(total, checkbox) {
          return total + Number(checkbox.closest('tr').dataset.backlog || 0);
        }, 0);
        document.getElementById('dprStreamReassignSummary').textContent =
          '已选 ' + selected.length + ' 个流式任务 · 积压 ' + count.toLocaleString() + ' 条';
        document.getElementById('dprStreamCurrentTask').textContent = '多个处理任务';
        document.getElementById('dprStreamCurrentWorkflow').textContent = '各任务当前处理流程';
      }
      openDrawer('drawerStreamReassign');
    }
    function dprSyncStreamOperators() {
      var supplier = document.getElementById('dprStreamNewSupplier').value;
      var options = {
        '平台自有':['joanna.qiao','包媛桐'],
        '光轮智能':['刘素粉','光轮-QC-021'],
        '供应商 A':['供应商 A-017','供应商 A-026']
      };
      document.getElementById('dprStreamNewOperator').innerHTML =
        (options[supplier] || []).map(function(name) {
          return '<option>' + name + '</option>';
        }).join('');
    }
    function dprSubmitStreamReassign() {
      toast('Demo: 已重新指派供应商和处理人，当前处理流程保持不变');
      closeDrawer();
    }
    function dprUpdateUnboundSelection() {
      var selected = document.querySelectorAll('.dpr-unbound-check:checked').length;
      document.getElementById('dprUnboundSelectedCount').textContent = selected;
      document.getElementById('dprBulkBindTask').disabled = selected === 0;
    }
    function dprFilterUnboundRows() {
      var project = dprCurrentAllocationProject();
      var source = document.getElementById('dprUnboundSource').value;
      var task = document.getElementById('dprUnboundTask').value.trim().toLowerCase();
      var visible = 0;
      var count = 0;
      document.querySelectorAll('#dpr-unbound-pool-table tbody tr').forEach(function(row) {
        var matches = (project === '全部项目' || row.dataset.project === project)
          && (!source || row.dataset.source === source)
          && (!task || row.dataset.sourceTask.toLowerCase().indexOf(task) >= 0);
        row.style.display = matches ? '' : 'none';
        if(matches) {
          visible += 1;
          count += Number(row.dataset.count || 0);
        }
      });
      document.getElementById('dprUnboundVisibleBatches').textContent = visible;
      document.getElementById('dprUnboundDataCount').textContent = count.toLocaleString();
    }
    function dprResetUnboundFilters() {
      document.getElementById('dprUnboundSource').selectedIndex = 0;
      document.getElementById('dprUnboundTask').value = '';
      dprFilterUnboundRows();
    }
    function dprOpenBindTask(trigger) {
      var selected = Array.prototype.slice.call(
        document.querySelectorAll('.dpr-unbound-check:checked')
      );
      if(trigger) {
        document.getElementById('dprBindTaskSummary').textContent =
          trigger.dataset.poolId + ' · ' + Number(trigger.dataset.count).toLocaleString()
          + ' 条数据 · 来源 ' + trigger.dataset.sourceTask;
      } else {
        var count = selected.reduce(function(total, checkbox) {
          return total + Number(checkbox.closest('tr').dataset.count || 0);
        }, 0);
        document.getElementById('dprBindTaskSummary').textContent =
          '已选 ' + selected.length + ' 个批次 · ' + count.toLocaleString() + ' 条数据';
      }
      openDrawer('drawerBindProcessingTask');
    }
    function dprSubmitBindTask() {
      toast('Demo: 已指定处理任务并绑定处理流程');
      closeDrawer();
    }
    function dprFilterReprocessOverview() {
      var project = dprCurrentAllocationProject();
      document.querySelectorAll('#dpr-reprocess-overview tbody tr').forEach(function(row) {
        row.style.display = project === '全部项目' || row.dataset.project === project ? '' : 'none';
      });
    }
    function dprRunReprocessFilter() {
      var project = dprCurrentAllocationProject();
      var projectCounts = {'全部项目':4218,'宁德项目':1602,'预训练采集':1104,'demo 项目':1512};
      var count = projectCounts[project] || 0;
      [
        ['dprReprocessSource',.72],
        ['dprReprocessQuality',.31],
        ['dprReprocessAnnotation',.58],
        ['dprReprocessCurrentFlow',.46]
      ].forEach(function(item) {
        if(document.getElementById(item[0]).value) count = Math.floor(count * item[1]);
      });
      if(document.getElementById('dprReprocessSourceTask').value.trim()) count = Math.min(count,842);
      if(document.getElementById('dprReprocessRecordingId').value.trim()) count = 1;
      document.getElementById('dprReprocessMatchCount').textContent = count.toLocaleString();
      document.getElementById('dprReprocessMatchHint').textContent =
        count === 4218 ? '当前为全部可见数据' : '已按当前项目与筛选条件统计';
      dprFilterReprocessOverview();
    }
    function dprResetReprocessFilters() {
      ['dprReprocessSource','dprReprocessQuality','dprReprocessAnnotation','dprReprocessCurrentFlow']
        .forEach(function(id) { document.getElementById(id).selectedIndex = 0; });
      document.getElementById('dprReprocessSourceTask').value = '';
      document.getElementById('dprReprocessRecordingId').value = '';
      dprRunReprocessFilter();
    }
    function dprOpenReprocessDrawer() {
      document.getElementById('dprReprocessDrawerCount').textContent =
        document.getElementById('dprReprocessMatchCount').textContent;
      openDrawer('drawerCreateReprocess');
    }
    function dprSubmitReprocess() {
      var originalFlowAction = document.getElementById('dprReprocessOriginalFlow').value;
      toast(
        originalFlowAction === '终止'
          ? 'Demo: 已新增再处理流程，原处理流程已终止'
          : 'Demo: 已新增再处理流程，原处理流程继续运行'
      );
      closeDrawer();
    }
    function dprSelectAllocationProject() {
      document.querySelectorAll('.dpr-stream-check:checked,.dpr-unbound-check:checked')
        .forEach(function(item) { item.checked = false; });
      dprUpdateStreamSelection();
      dprUpdateUnboundSelection();
      dprFilterStreamRows();
      dprFilterUnboundRows();
      dprRunReprocessFilter();
    }
    dprSyncStreamOperators();
    dprSelectAllocationProject();
    </script>
    """

    return (
        _intro(
            "分配管理",
            "处理流式吞吐积压、未绑定处理任务的数据，以及面向训练需求的数据再处理。",
            "",
            project_switcher,
        )
        + f"""
        <div class="det-tabs dpr-allocation-tabs">
          <span class="det-tab active"
            onclick="switchDetTab(this,'allocation-stream')">资源调度</span>
          <span class="det-tab"
            onclick="switchDetTab(this,'allocation-unbound')">处理绑定</span>
          <span class="det-tab"
            onclick="switchDetTab(this,'allocation-reprocess')">数据再处理</span>
        </div>
        <div id="det-pane-allocation-stream" class="det-pane active">{stream_tab}</div>
        <div id="det-pane-allocation-unbound" class="det-pane">{unbound_tab}</div>
        <div id="det-pane-allocation-reprocess" class="det-pane">{reprocess_tab}</div>
        {drawers_and_script}
        """
    )


def render_task_detail(task_id):
    task = next((item for item in BUSINESS_TASKS if item["id"] == task_id), None)
    if not task or task["type"] == "data_import_task":
        raise KeyError(f"unknown task: {task_id}")
    records = TASK_DETAIL_RECORDS.get(task_id, [])
    back_path = (
        "/data/collection-tasks"
        if task["type"] == "data_collection_task"
        else "/data/processing-tasks"
    )
    back_label = "采集任务" if task["type"] == "data_collection_task" else "处理任务"
    is_collection_task = task["type"] == "data_collection_task"
    rows = ""
    for record in records:
        if is_collection_task:
            managed_record = next(
                (
                    item
                    for item in DATA_MANAGEMENT_RECORDS
                    if item["id"] == record["id"]
                ),
                None,
            )
            upload_status = managed_record["upload"] if managed_record else "上传成功"
            rows += f"""
            <tr>
              <td><code>{_e(record["id"])}</code></td>
              <td>
                <div class="dpr-video-group" aria-label="三路采集视频">
                  <span class="vid-thumb"></span><span class="vid-thumb"></span><span class="vid-thumb"></span>
                </div>
              </td>
              <td><code>{_e(record["device"])}</code></td>
              <td>{_record_tag(upload_status)}</td>
              <td>{_record_tag(record["collection"])}</td>
              <td><span class="dpr-record-operator">{_e(record["operators"])}</span></td>
            </tr>
            """
        else:
            rows += f"""
        <tr>
          <td><code>{_e(record["id"])}</code></td>
          <td>
            <div class="dpr-video-group" aria-label="三路采集视频">
              <span class="vid-thumb"></span><span class="vid-thumb"></span><span class="vid-thumb"></span>
            </div>
          </td>
          <td>{_record_tag(record["node"])}</td>
          <td>{_record_tag(record["quality"])}</td>
          <td>{_record_tag(record["annotation"])}</td>
          <td>{_record_tag(record["acceptance"])}</td>
          <td><span class="dpr-record-operator">{_e(record["operators"])}</span></td>
          <td class="dpr-record-actions">
            <a href="#" onclick="toast('Demo: 查看轨迹');return false;">轨迹</a>
            <a href="#" onclick="toast('Demo: 查看更多');return false;">⋯ 更多</a>
          </td>
        </tr>
        """

    if is_collection_task:
        progress = task["collection_progress"]
        summary = (
            f'采集 <b>{progress["done"]:,}</b> / {progress["total"]:,} 条'
        )
        table_class = "ant-table dpr-record-table dpr-collection-record-table"
        table_head = (
            "<th>recording_id</th><th>视频</th><th>设备序列号</th>"
            "<th>上传状态</th><th>采集结论</th><th>操作人</th>"
        )
        empty_colspan = 6
    else:
        summary = " · ".join(
            f'{stage["label"]} <b>{stage["done"]:,}</b> / {stage["total"]:,} 条'
            for stage in task["stage_progress"]
        )
        table_class = "ant-table dpr-record-table"
        table_head = (
            "<th>recording_id</th><th>视频</th><th>处理环节</th>"
            "<th>质检结论</th><th>标注状态</th>"
            "<th>验收状态</th><th>操作人</th><th>操作</th>"
        )
        empty_colspan = 8

    return f"""
    <div class="dpr-record-page">
      <div class="dpr-record-top">
        <div>
          <a href="{back_path}">← 返回{back_label}</a>
          <b>{_e(task["name"])}</b>
          <code>{_e(task["id"])}</code>
        </div>
        {_state(task["status"])}
      </div>
      <div class="fb-labeled dpr-record-filters">
        <div class="ff"><label>ID 搜索</label><input placeholder="请输入 recording_id"></div>
        <div class="ff"><label>序列号</label><select><option>请选择设备序列号</option><option>UDAS-007</option><option>Benchmark</option></select></div>
        <div class="ff"><label>操作人</label><select><option>请选择操作类型/操作人</option><option>采集</option><option>质检</option><option>标注</option><option>验收</option></select></div>
        <div class="filter-actions">
          <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
          <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
        </div>
      </div>
      <div class="dpr-record-summary">
        <span>{_e(task["name"])}</span>
        <span>{summary}</span>
      </div>
      <div class="table-wrap dpr-record-table-wrap">
        <table class="{table_class}">
          <thead><tr>{table_head}</tr></thead>
          <tbody>{rows or f'<tr><td colspan="{empty_colspan}" class="dpr-empty">暂无记录</td></tr>'}</tbody>
        </table>
      </div>
      <div class="mini-pager">
        <select><option>10条/页</option></select>
        <span class="pg-btn">&lsaquo;</span><span class="pg-btn active">1</span>
        <span class="pg-btn">2</span><span class="pg-btn">3</span>
        <span class="muted">...</span><span class="pg-btn">18</span>
        <span class="pg-btn">&rsaquo;</span><input class="pg-goto"><span class="pg-go">go</span>
      </div>
    </div>
    """


def render_data_management():
    def record_panel():
        records = DATA_MANAGEMENT_RECORDS
        rows = ""
        for record in records:
            row_id = f'process-tree-{record["id"]}'
            flow_rows = "".join(
                f"""
                <tr>
                  <td><b>{_e(flow["name"])}</b></td>
                  <td>{_record_tag(flow["node"])}</td>
                  <td>{_record_tag(flow["quality"])}</td>
                  <td>{_record_tag(flow["annotation"])}</td>
                </tr>
                """
                for flow in record["flows"]
            )
            rows += f"""
            <tr class="dpr-record-main-row">
              <td>
                <button type="button" class="dpr-tree-toggle" aria-expanded="false"
                  onclick="dprToggleProcessTree('{_e(row_id)}', this)">&#9656;</button>
                <a href="/data/recordings/{_e(record["id"])}"><code>{_e(record["id"])}</code></a>
              </td>
              <td>{_record_tag(DATA_SOURCE_LABELS[record["source_type"]])}</td>
              <td>
                <div class="dpr-video-group" aria-label="三路采集视频">
                  <span class="vid-thumb"></span><span class="vid-thumb"></span><span class="vid-thumb"></span>
                </div>
              </td>
              <td>{_record_tag(record["upload"])}</td>
              <td>{_record_tag(record["collection"])}</td>
              <td>{_record_tag(record["quality"])}</td>
              <td>{_record_tag(record["annotation"])}</td>
              <td>
                <button type="button" class="dpr-flow-link"
                  onclick="dprToggleProcessTree('{_e(row_id)}', this)">
                  {len(record["flows"])} 条 · {_e(record["flows"][0]["name"])}
                </button>
              </td>
            </tr>
            <tr id="{_e(row_id)}" class="dpr-process-tree-row" style="display:none;">
              <td colspan="8">
                <div class="dpr-process-tree">
                  <div class="dpr-process-tree-meta">
                    <span>来源任务 ID：<code>{_e(record["source_task_id"])}</code></span>
                    <span>设备序列号：<code>{_e(record["device"])}</code></span>
                  </div>
                  <table>
                    <thead><tr>
                      <th>流程名称</th><th>当前节点</th><th>质检结论</th><th>标注状态</th>
                    </tr></thead>
                    <tbody>{flow_rows}</tbody>
                  </table>
                </div>
              </td>
            </tr>
            """
        filters = f"""
        <div class="fb-labeled dpr-record-filters">
          <div class="ff"><label>recording_id</label><input placeholder="请输入 recording_id"></div>
          <div class="ff"><label>来源任务 ID</label><input placeholder="请输入来源任务 ID"></div>
          <div class="ff"><label>数据来源</label><select><option>全部来源</option><option>采集</option><option>导入</option></select></div>
          <div class="ff"><label>设备序列号</label><select><option>全部设备</option><option>UDAS-007</option><option>Vendor-MOZ2-03</option></select></div>
          <div class="ff"><label>操作人</label><select><option>全部操作人</option><option>刘素粉</option><option>供应商 Batch-12</option></select></div>
          <div class="filter-actions">
            <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
            <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
          </div>
        </div>
        """
        return f"""
        {filters}
        <div class="dpr-record-summary">
          <span>全部数据</span><span>当前展示 <b>{len(records)}</b> 条记录</span>
        </div>
        <div class="table-wrap dpr-record-table-wrap">
          <table class="ant-table dpr-management-record-table">
            <thead><tr>
              <th>recording_id</th><th>数据来源</th><th>视频</th><th>上传状态</th><th>采集结论</th>
              <th>质检结论</th><th>标注状态</th><th>关联处理流程</th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        <div class="mini-pager">
          <select><option>10条/页</option></select>
          <span class="pg-btn">&lsaquo;</span><span class="pg-btn active">1</span>
          <span class="pg-btn">2</span><span class="pg-btn">3</span>
          <span class="muted">...</span><span class="pg-btn">18</span>
          <span class="pg-btn">&rsaquo;</span><input class="pg-goto"><span class="pg-go">go</span>
        </div>
        """

    records = record_panel()
    body = f"""
    <div class="dpr-data-management">
      {records}
    </div>
    <script>
    function dprToggleProcessTree(rowId, trigger) {{
      var row = document.getElementById(rowId);
      if (!row) return;
      var opening = row.style.display === 'none';
      row.style.display = opening ? 'table-row' : 'none';
      var parent = row.previousElementSibling;
      if (parent) {{
        var toggle = parent.querySelector('.dpr-tree-toggle');
        if (toggle) {{
          toggle.innerHTML = opening ? '&#9662;' : '&#9656;';
          toggle.setAttribute('aria-expanded', opening ? 'true' : 'false');
        }}
      }}
    }}
    </script>
    """
    return _intro(
        "数据管理",
        "以 Recording 为数据主线，查看数据处理进度与版本记录。",
        "",
    ) + body


_RECORD_PREVIEW_SCRIPT = """
<script>
(function(){
  var processData = __PROCESS_DATA__;
  var activeArms = new Set(['LeftArm', 'RightArm']);
  var currentEpisode = 0;

  function esc(value){
    return String(value).replace(/[&<>"']/g, function(char){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char];
    });
  }
  function spark(seed, armIndex, rowIndex){
    var cmd = [], state = [], count = 46;
    for(var index = 0; index < count; index++){
      var x = index / (count - 1) * 200;
      var cmdValue = Math.sin(index / 4 + seed * .6 + armIndex * 1.3 + rowIndex * .9) * .7
        + Math.sin(index / 2 + rowIndex) * .15;
      var stateValue = Math.sin((index - 2) / 4 + seed * .6 + armIndex * 1.3 + rowIndex * .9) * .7
        + Math.sin((index - 2) / 2 + rowIndex) * .15;
      cmd.push(x.toFixed(1) + ',' + ((.5 - cmdValue / 2) * 30.4 + 3.8).toFixed(1));
      state.push(x.toFixed(1) + ',' + ((.5 - stateValue / 2) * 30.4 + 3.8).toFixed(1));
    }
    return '<svg class="dpr-preview-spark" viewBox="0 0 200 38" preserveAspectRatio="none">'
      + '<polyline points="' + cmd.join(' ') + '" fill="none" stroke="#1F80A0" stroke-width="1.2" vector-effect="non-scaling-stroke"/>'
      + '<polyline points="' + state.join(' ') + '" fill="none" stroke="#52c41a" stroke-width="1.2" vector-effect="non-scaling-stroke"/></svg>';
  }
  function renderArm(){
    var arms = ['LeftArm', 'Torso', 'RightArm'].filter(function(name){ return activeArms.has(name); });
    var rows = ['X', 'Y', 'Z', 'r', 'p', 'y', 'G'];
    var html = '<table class="dpr-preview-traj-grid"><thead><tr><th></th>';
    arms.forEach(function(name){ html += '<th>' + name + '</th>'; });
    html += '</tr></thead><tbody>';
    rows.forEach(function(row, rowIndex){
      html += '<tr><td>' + row + '</td>';
      arms.forEach(function(arm, armIndex){
        html += row === 'G' && arm === 'Torso'
          ? '<td></td>'
          : '<td>' + spark(currentEpisode, armIndex, rowIndex) + '</td>';
      });
      html += '</tr>';
    });
    document.getElementById('dprPreviewArmView').innerHTML = html + '</tbody></table>';
  }
  window.dprTogglePreviewArm = function(button, arm){
    if(activeArms.has(arm) && activeArms.size > 1) activeArms.delete(arm);
    else activeArms.add(arm);
    button.classList.toggle('on', activeArms.has(arm));
    document.querySelectorAll('[data-traj-view]').forEach(function(view){
      view.style.display = view.dataset.trajView === 'arm' ? '' : 'none';
    });
    renderArm();
  };
  window.dprSetPreviewMode = function(button, mode){
    document.querySelectorAll('.dpr-preview-traj-tabs button').forEach(function(item){
      if(item.dataset.mode) item.classList.toggle('on', item === button);
    });
    document.querySelectorAll('[data-traj-view]').forEach(function(view){
      view.style.display = view.dataset.trajView === mode ? '' : 'none';
    });
  };
  window.dprSwitchRecordPreview = function(button, pane){
    document.querySelectorAll('.dpr-preview-tab').forEach(function(item){
      item.classList.toggle('active', item === button);
    });
    document.querySelectorAll('.dpr-preview-pane').forEach(function(item){
      item.style.display = item.dataset.previewPane === pane ? '' : 'none';
    });
    document.getElementById('dprProcessSwitcher').style.display =
      pane === 'process' ? 'flex' : 'none';
  };
  function renderProcessRules(){
    var flowName = document.getElementById('dprProcessFlow').value;
    var flow = processData[flowName];
    if(!flow) return;
    var qualityVersion = document.getElementById('dprQualityRuleVersion').value;
    var annotationVersion = document.getElementById('dprAnnotationRuleVersion').value;
    var qualityRule = flow.quality_rules.find(function(item){
      return item.version === qualityVersion;
    }) || flow.quality_rules[0];
    var annotationRule = flow.annotation_rules.find(function(item){
      return item.version === annotationVersion;
    }) || flow.annotation_rules[0];
    if(!qualityRule || !annotationRule) return;
    document.getElementById('dprProcessNote').textContent =
      qualityRule.label + '：' + qualityRule.note + '；'
      + annotationRule.label + '：' + annotationRule.note;
    var total = annotationRule.segments.length
      ? annotationRule.segments[annotationRule.segments.length - 1].end
      : 1;
    document.getElementById('dprProcessSegments').innerHTML = annotationRule.segments.map(function(segment){
      var duration = Math.max(segment.end - segment.start, .1);
      return '<div class="dpr-preview-segment" style="flex:' + duration + ' 1 0;background:' + segment.color + ';"'
        + ' title="' + esc(segment.description) + ' · ' + segment.start.toFixed(2) + 's~' + segment.end.toFixed(2) + 's"></div>';
    }).join('');
    document.getElementById('dprProcessSegmentCount').textContent = annotationRule.segments.length;
    document.getElementById('dprProcessRows').innerHTML =
      '<tr class="dpr-preview-process-parent"><td>完整处理区间</td><td>0.00s</td><td>'
      + total.toFixed(2) + 's</td><td>' + total.toFixed(2) + 's</td></tr>'
      + annotationRule.segments.map(function(segment, index){
        return '<tr><td><span class="dpr-preview-process-num">' + (index + 1) + '</span>'
          + esc(segment.description) + '</td><td>' + segment.start.toFixed(2) + 's</td><td>'
          + segment.end.toFixed(2) + 's</td><td>'
          + (segment.end - segment.start).toFixed(2) + 's</td></tr>';
      }).join('');
  }
  window.dprSelectRecordFlow = function(){
    var flowName = document.getElementById('dprProcessFlow').value;
    var flow = processData[flowName];
    var selectors = [
      {
        element: document.getElementById('dprQualityRuleVersion'),
        items: flow ? flow.quality_rules : []
      },
      {
        element: document.getElementById('dprAnnotationRuleVersion'),
        items: flow ? flow.annotation_rules : []
      }
    ];
    selectors.forEach(function(config){
      config.element.innerHTML = '';
      config.items.forEach(function(item){
        var option = document.createElement('option');
        option.value = item.version;
        option.textContent = item.label;
        config.element.appendChild(option);
      });
    });
    renderProcessRules();
  };
  window.dprSelectRecordRuleVersion = renderProcessRules;

  function renderHistoryRecords(){
    var flowName = document.getElementById('dprHistoryFlow').value;
    var flow = processData[flowName];
    if(!flow) return;
    var versionName = document.getElementById('dprHistoryVersion').value;
    var version = flow.history_versions.find(function(item){
      return item.version === versionName;
    }) || flow.history_versions[0];
    if(!version) return;
    document.getElementById('dprHistoryRows').innerHTML = version.records.map(function(record){
      return '<tr><td>' + esc(record.operator) + '</td><td>' + esc(record.time)
        + '</td><td>' + esc(record.action) + '</td></tr>';
    }).join('');
  }
  window.dprSwitchRecordHistory = function(button, mode){
    document.querySelectorAll('.dpr-history-tab').forEach(function(item){
      item.classList.toggle('active', item === button);
    });
    document.querySelectorAll('[data-history-pane]').forEach(function(item){
      item.style.display = item.dataset.historyPane === mode ? '' : 'none';
    });
    document.getElementById('dprHistorySwitcher').style.display =
      mode === 'process' ? 'flex' : 'none';
  };
  window.dprSelectRecordHistoryFlow = function(){
    var flowName = document.getElementById('dprHistoryFlow').value;
    var flow = processData[flowName];
    var versionSelect = document.getElementById('dprHistoryVersion');
    versionSelect.innerHTML = '';
    (flow ? flow.history_versions : []).forEach(function(item){
      var option = document.createElement('option');
      option.value = item.version;
      option.textContent = item.label;
      versionSelect.appendChild(option);
    });
    renderHistoryRecords();
  };
  window.dprSelectRecordHistoryVersion = renderHistoryRecords;

  renderArm();
  var flowSelect = document.getElementById('dprProcessFlow');
  var historyFlowSelect = document.getElementById('dprHistoryFlow');
  Object.keys(processData).forEach(function(flowName){
    var option = document.createElement('option');
    option.value = flowName;
    option.textContent = flowName;
    flowSelect.appendChild(option);
    var historyOption = option.cloneNode(true);
    historyFlowSelect.appendChild(historyOption);
  });
  window.dprSelectRecordFlow();
  window.dprSelectRecordHistoryFlow();
})();
</script>
"""


def render_record_detail(recording_id):
    record = next(
        (item for item in DATA_MANAGEMENT_RECORDS if item["id"] == recording_id),
        None,
    )
    if not record:
        raise KeyError(f"unknown recording: {recording_id}")

    default_segments = [
        ("接近作业区域", 0.00, 6.70, "#7ed3a2"),
        ("识别目标物体", 6.70, 13.31, "#f4d35e"),
        ("执行抓取动作", 13.31, 23.74, "#e8a06a"),
        ("移动并调整姿态", 23.74, 38.00, "#5bc0be"),
        ("放置目标物体", 38.00, 52.00, "#9b8cce"),
        ("机械臂复位", 52.00, 64.20, "#5aa9e6"),
    ]
    annotation_segments = [
        ("接近目标", 0.00, 8.20, "#7ed3a2"),
        ("动作起点确认", 8.20, 15.60, "#f4d35e"),
        ("主体动作分段", 15.60, 34.80, "#e8a06a"),
        ("关键帧确认", 34.80, 48.40, "#5bc0be"),
        ("动作终点确认", 48.40, 58.10, "#9b8cce"),
    ]
    process_data = {}
    for flow_index, flow in enumerate(record["flows"]):
        quality_rule_items = []
        annotation_rule_items = []
        history_version_items = []
        segment_source = (
            annotation_segments if "标注" in flow["name"] else default_segments
        )
        for version_index, (version, created, quality, annotation, note) in enumerate(
            record["versions"]
        ):
            segments = segment_source[: max(3, len(segment_source) - version_index)]
            quality_rule_items.append(
                {
                    "version": version,
                    "label": f"质检规则 {version}",
                    "created": created,
                    "quality": quality,
                    "note": f"{note} · 质检口径",
                }
            )
            annotation_rule_items.append(
                {
                    "version": version,
                    "label": f"标注规则 {version}",
                    "created": created,
                    "process_state": annotation,
                    "note": f"{note} · 标注口径",
                    "segments": [
                        {
                            "description": description,
                            "start": start,
                            "end": end,
                            "color": color,
                        }
                        for description, start, end, color in segments
                    ],
                }
            )
            history_version_items.append(
                {
                    "version": version,
                    "label": f"处理版本 {version}",
                    "records": [
                        {
                            "operator": "数据处理服务",
                            "time": created,
                            "action": (
                                f"执行{flow['name']}，处理节点：{flow['node']}"
                            ),
                        },
                        {
                            "operator": (
                                record["operator"]
                                if flow_index == 0
                                else "供应商 A-017"
                            ),
                            "time": created,
                            "action": f"完成质检，质检结论：{quality}",
                        },
                        {
                            "operator": (
                                "joanna.qiao"
                                if annotation == "已标注"
                                else "任务分配服务"
                            ),
                            "time": created,
                            "action": f"{note}，标注状态：{annotation}",
                        },
                    ],
                }
            )
        process_data[flow["name"]] = {
            "node": flow["node"],
            "quality_rules": quality_rule_items,
            "annotation_rules": annotation_rule_items,
            "history_versions": history_version_items,
        }

    cameras = "".join(
        f'<div class="dpr-preview-camera"><span>{_e(label)}</span>'
        f'<b>&#9658;</b><small>240 × 320</small></div>'
        for label in ("cam_high", "cam_left_wrist", "cam_right_wrist")
    )
    source_action = (
        "完成数据采集" if record["source_type"] == "collection" else "完成数据导入"
    )
    source_service = (
        "采集任务服务" if record["source_type"] == "collection" else "数据导入服务"
    )
    first_created = record["versions"][-1][1]
    latest_created = record["versions"][0][1]
    collection_history_rows = "".join(
        f"<tr><td>{_e(operator)}</td><td>{_e(created)}</td>"
        f"<td>{_e(action)}</td></tr>"
        for operator, created, action in (
            (
                source_service,
                first_created,
                f"创建数据记录，来源任务：{record['source_task_id']}",
            ),
            (
                record["operator"],
                first_created,
                f"{source_action}，采集结论：{record['collection']}",
            ),
            (
                "数据接入服务",
                latest_created,
                f"上传原始数据，上传状态：{record['upload']}",
            ),
        )
    )
    process_json = json.dumps(process_data, ensure_ascii=False).replace("</", "<\\/")
    script = _RECORD_PREVIEW_SCRIPT.replace("__PROCESS_DATA__", process_json)
    return f"""
    <div class="dpr-record-page dpr-record-preview-page">
      <div class="dpr-record-top">
        <div>
          <a href="/data/recordings">← 返回数据管理</a>
          <b>Recording {_e(recording_id)}</b>
          <code>{_e(record["source_task_id"])}</code>
        </div>
        {_record_tag(record["quality"])}
      </div>
      <div class="dpr-record-detail-meta">
        <span>设备序列号 <code>{_e(record["device"])}</code></span>
        <span>操作人 <b>{_e(record["operator"])}</b></span>
        <span>关联流程 <b>{len(record["flows"])} 条</b></span>
      </div>
      <div class="dpr-preview-toolbar">
        <div class="dpr-preview-tabs" role="tablist">
          <button type="button" class="dpr-preview-tab active"
            onclick="dprSwitchRecordPreview(this,'trajectory')">轨迹信息</button>
          <button type="button" class="dpr-preview-tab"
            onclick="dprSwitchRecordPreview(this,'process')">处理信息</button>
          <button type="button" class="dpr-preview-tab"
            onclick="dprSwitchRecordPreview(this,'history')">数据处理记录</button>
        </div>
        <div class="dpr-process-switcher" id="dprProcessSwitcher" style="display:none;">
          <label>处理流程<select id="dprProcessFlow"
            onchange="dprSelectRecordFlow()"></select></label>
          <label>质检规则<select id="dprQualityRuleVersion"
            onchange="dprSelectRecordRuleVersion()"></select></label>
          <label>标注规则<select id="dprAnnotationRuleVersion"
            onchange="dprSelectRecordRuleVersion()"></select></label>
        </div>
      </div>

      <div class="dpr-preview-pane" data-preview-pane="trajectory">
        <div class="dpr-preview-camera-row">{cameras}</div>
        <div class="dpr-preview-traj-bar">
          <div class="dpr-preview-traj-tabs">
            <button type="button" class="on" data-mode="arm"
              onclick="dprTogglePreviewArm(this,'LeftArm')">LeftArm</button>
            <button type="button" data-mode="arm"
              onclick="dprTogglePreviewArm(this,'Torso')">Torso</button>
            <button type="button" class="on" data-mode="arm"
              onclick="dprTogglePreviewArm(this,'RightArm')">RightArm</button>
            <i></i>
            <button type="button" data-mode="base"
              onclick="dprSetPreviewMode(this,'base')">Base</button>
            <button type="button" data-mode="moz"
              onclick="dprSetPreviewMode(this,'moz')">3D Replay</button>
          </div>
          <div class="dpr-preview-traj-legend">
            <span><i class="cmd"></i>CMD</span><span><i class="state"></i>State</span>
          </div>
          <div class="dpr-preview-play">
            <button type="button" onclick="toast('Demo: 播放')">&#9658;</button>
            <button type="button" onclick="toast('Demo: 重置')">&#8635;</button>
          </div>
        </div>
        <div class="dpr-preview-traj-views">
          <div id="dprPreviewArmView" data-traj-view="arm"></div>
          <div class="dpr-preview-base-grid" data-traj-view="base" style="display:none;">
            <div><b>底盘速度 · State / CMD</b><span class="dpr-preview-chart-line one"></span></div>
            <div><b>底盘 XY 轨迹</b><span class="dpr-preview-chart-line two"></span></div>
          </div>
          <div class="dpr-preview-moz" data-traj-view="moz" style="display:none;">
            <div class="dpr-preview-moz-floor"></div>
            <div class="dpr-preview-robot">&#9673;<span>MOZ</span></div>
            <div class="dpr-preview-moz-info">
              <b>3D Replay</b>
              <span>左臂笛卡尔：0.215, -0.261, -0.052</span>
              <span>右臂笛卡尔：-0.174, -0.292, -0.050</span>
              <span>底盘速度：0.000, 0.000, 0.000</span>
            </div>
          </div>
        </div>
        <input type="range" class="dpr-preview-slider" min="0" max="100" value="38">
      </div>

      <div class="dpr-preview-pane" data-preview-pane="process" style="display:none;">
        <div class="dpr-preview-camera-row">{cameras}</div>
        <div class="dpr-preview-seg-timeline">
          <div class="dpr-preview-seg-row">
            <span id="dprProcessSegmentCount"></span>
            <div id="dprProcessSegments" class="dpr-preview-seg-track"></div>
          </div>
        </div>
        <div class="dpr-preview-process-caption">
          highlevel / lowlevel 处理结果
          <span>点击分段查看对应处理内容</span>
        </div>
        <table class="dpr-preview-process-table">
          <thead><tr><th>描述</th><th>开始</th><th>结束</th><th>时长</th></tr></thead>
          <tbody id="dprProcessRows"></tbody>
        </table>
        <div class="dpr-preview-process-note">
          <b>版本说明</b><span id="dprProcessNote"></span>
        </div>
      </div>

      <div class="dpr-preview-pane" data-preview-pane="history" style="display:none;">
        <div class="dpr-history-toolbar">
          <div class="dpr-history-tabs" role="tablist">
            <button type="button" class="dpr-history-tab active"
              onclick="dprSwitchRecordHistory(this,'collection')">采集信息</button>
            <button type="button" class="dpr-history-tab"
              onclick="dprSwitchRecordHistory(this,'process')">处理信息</button>
          </div>
          <div class="dpr-history-switcher" id="dprHistorySwitcher"
            style="display:none;">
            <label>处理流程<select id="dprHistoryFlow"
              onchange="dprSelectRecordHistoryFlow()"></select></label>
            <label>处理版本<select id="dprHistoryVersion"
              onchange="dprSelectRecordHistoryVersion()"></select></label>
          </div>
        </div>
        <div data-history-pane="collection">
          <table class="dpr-preview-process-table dpr-history-table">
            <thead><tr><th>操作人</th><th>操作时间</th><th>操作记录</th></tr></thead>
            <tbody>{collection_history_rows}</tbody>
          </table>
        </div>
        <div data-history-pane="process" style="display:none;">
          <table class="dpr-preview-process-table dpr-history-table">
            <thead><tr><th>操作人</th><th>操作时间</th><th>操作记录</th></tr></thead>
            <tbody id="dprHistoryRows"></tbody>
          </table>
        </div>
      </div>
    </div>
    {script}
    """


def render_human_tasks():
    rows = []
    for item in HUMAN_TASKS:
        sla_cls = "dpr-risk" if "超时" in item["sla"] or "01:" in item["sla"] else ""
        work_link = '<a class="btn btn-sm btn-primary" href="/data/workbench/edit">进入工作台</a>' if item["status"] == "in_progress" else '<a class="btn btn-sm" href="#" onclick="toast(\'Demo: 已领取并锁定任务\');return false;">领取</a>'
        rows.append(
            [
                f'<code>{_e(item["id"])}</code><br><b>{_e(item["task_type"])}</b>',
                f'<code>{_e(item["business_task"])}</code><br><code>{_e(item["pipeline_run"])}</code><br><code>{_e(item["node_run"])}</code>',
                f'{_e(item["data_scope"])}<br><small>{_e(item["sop"])}</small>',
                f'<b>{_e(item["priority"])}</b><br><span class="{sla_cls}">{_e(item["sla"])}</span>',
                f'{_e(item["assignee"])}<br><small>{_e(item["lock"])}</small>',
                _state(item["status"]),
                work_link,
            ]
        )
    header_actions = '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 已领取下一条 P0 任务\');return false;">领取下一条</a>'
    return (
        _intro("人工任务池", "领取和处理分配给你的人工任务。", "", header_actions)
        + _metrics([("待领取", "28", "P0 2 条"), ("我的处理中", "12", "全部锁定有效"), ("即将超时", "2", "已触发升级规则"), ("今日完成", "127", "较昨日 +12.4%")])
        + _section("任务池", _table(["人工任务", "完整关联", "数据范围 / SOP", "优先级 / SLA", "执行人 / 锁", "状态", "操作"], rows))
    )


def render_pipeline_definitions():
    cards = ""
    for definition in PIPELINE_DEFINITIONS:
        nodes = ""
        for index, (name, node_type, binding) in enumerate(definition["nodes"]):
            if index:
                nodes += '<span class="dpr-node-arrow">→</span>'
            nodes += f'<span class="dpr-node {node_type}"><i>{_e(node_type)}</i><b>{_e(name)}</b><small>{_e(binding or "expression")}</small></span>'
        cards += f"""
        <article class="dpr-pipeline-card">
          <div class="dpr-pipeline-head">
            <div><code>{_e(definition['id'])}</code><h3>{_e(definition['name'])}</h3><span>Owner · {_e(definition['owner'])}</span></div>
            <div class="dpr-version-stack"><span>已发布 <b>{_e(definition['published_version'])}</b></span><span>当前草稿 <b>{_e(definition['draft_version'])}</b></span></div>
          </div>
          <div class="dpr-node-flow">{nodes}</div>
          <div class="dpr-card-foot"><span>已发布版本不可原地修改 · 运行始终固定版本</span><a href="#" onclick="toast('Demo: 编辑 {_e(definition['id'])} 草稿');return false;">编辑草稿 →</a></div>
        </article>
        """
    return (
        _intro("流程定义", "管理已发布流程和草稿版本。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 新建流程草稿\');return false;">+ 新建流程</a>')
        + _section("流程列表", f'<div class="dpr-pipeline-list">{cards}</div>')
    )


def render_pipeline_runs():
    rows = []
    for run in PIPELINE_RUNS:
        rows.append(
            [
                f'<code>{_e(run["id"])}</code><br><small>{_e(run["started"])}</small>',
                f'<code>{_e(run["project"])}</code><br><code>{_e(run["business_task"])}</code>',
                f'<code>{_e(run["pipeline_version"])}</code>',
                f'<code>{_e(run["input_snapshot"])}</code>',
                f'<b>{_e(run["current_node"])}</b><br><span>{_e(run["node_progress"])}</span>',
                f'<code>{_e(run["idempotency_key"])}</code>',
                _state(run["status"]),
                '<a href="/data/lineage">血缘</a> · <a href="#" onclick="toast(\'Demo: 查看 Node Run\');return false;">节点记录</a>',
            ]
        )
    node_rows = []
    for node_run in NODE_RUNS:
        node_rows.append(
            [
                f'<code>{_e(node_run["id"])}</code>',
                f'<code>{_e(node_run["pipeline_run"])}</code>',
                f'<b>{_e(node_run["node"])}</b><br><code>{_e(node_run["node_type"])}</code>',
                f'<code>{_e(node_run["input_snapshot"])}</code>',
                f'<code>{_e(node_run["executor_version"])}</code>',
                str(node_run["attempt"]),
                f'<code>{_e(node_run["output"])}</code>',
                _state(node_run["status"]),
            ]
        )
    return (
        _intro("运行实例", "查看流程运行状态、当前节点与执行记录。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 发起运行\');return false;">发起运行</a>')
        + _section("运行列表", _table(["运行 / 发起时间", "项目 / 业务任务", "流程版本", "输入快照", "当前节点", "幂等键", "状态", "操作"], rows))
        + _section("节点执行记录", _table(["Node Run", "Pipeline Run", "节点 / 类型", "输入快照", "执行器版本", "Attempt", "结构化输出", "状态"], node_rows))
    )


def render_data_assets():
    recording_rows = [
        [
            f'<code>{_e(item["id"])}</code>',
            f'<code>{_e(item["source_task_type"])}</code>',
            f'<code>{_e(item["source_task_id"])}</code>',
            _e(item["device"]),
            _e(item["time_range"]),
            _e(item["modalities"]),
            f'<code>{_e(item["checksum"])}</code>',
        ]
        for item in RECORDING_ASSETS
    ]
    snapshot_rows = [
        [
            f'<code>{_e(item["id"])}</code>',
            f'<code>{_e(item["project"])}</code>',
            _e(item["members"]),
            f'<code>{_e(item["checksum"])}</code>',
            f'<code>{_e(item["created_by"])}</code>',
            _state("frozen") if item["immutable"] else _state("draft"),
        ]
        for item in DATA_SNAPSHOTS
    ]
    return (
        _intro("数据资产", "查看 Recording、Episode、标注版本和数据快照。", "")
        + _metrics([("Recording", "4,218", "本周新增 286"), ("Episode", "18,604", "本周新增 1,042"), ("Annotation Version", "12,921", "今日提交 127"), ("Data Snapshot", "38", "已冻结 31")])
        + _section("Recording 列表", _table(["Recording", "来源任务类型", "来源任务 ID", "设备", "时间范围", "模态", "校验和"], recording_rows))
        + _section("数据快照", _table(["Snapshot ID", "项目", "成员范围", "校验和", "生成来源", "状态"], snapshot_rows))
    )


def render_dataset_versions():
    rows = []
    for item in DATASET_VERSIONS:
        can_publish = item["status"] == "frozen"
        action = '<a href="#" onclick="toast(\'Demo: 已提交发布审批\');return false;">发布</a>' if can_publish else ('<a href="/model/data/datasets">下游引用</a>' if item["status"] == "published" else '<span class="muted">先完成构建</span>')
        metadata = "完整" if item["status"] != "draft" else "待补齐"
        rows.append(
            [
                f'<code>{_e(item["id"])}</code>',
                f'<code>{_e(item["project"])}</code>',
                f'<code>{_e(item["snapshot"])}</code>',
                _e(metadata),
                f'<b>{_e(item["lineage"])}</b>',
                _state(item["status"]),
                _e(item["consumer"]),
                action,
            ]
        )
    publish_conditions = """
    <div class="dpr-publish-conditions">
      <span>Data Snapshot 已冻结</span><i>+</i>
      <span>版本元数据完整</span><i>+</i>
      <span>血缘完整</span><i>→</i>
      <b>发布不可变 Dataset Version</b>
    </div>
    """
    return (
        _intro("数据集版本", "构建、冻结和发布数据集版本。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 构建数据集版本\');return false;">+ 构建版本</a>')
        + _section("发布条件", publish_conditions)
        + _section("版本列表", _table(["Dataset Version", "项目", "Snapshot", "元数据", "血缘覆盖", "状态", "下游消费", "操作"], rows))
    )


def render_lineage():
    chains = [
        [
            ("Recording", "recording:4057808@raw"),
            ("Snapshot", "snap-moz1-0718-r3"),
            ("Pipeline Run", "run-moz1-0921"),
            ("Snapshot", "snap-moz1-episodes-r2"),
            ("Dataset", "dataset.moz1-household@4.0.0"),
        ],
        [
            ("Import Task", "IMP-2026-0042"),
            ("Recording", "recording:vendor-12-*"),
            ("Pipeline Run", "run-vendor-042"),
            ("Snapshot", "snap-eval-q3-build"),
            ("Dataset", "dataset.eval-general@2026q3"),
        ],
    ]
    chain_html = ""
    for chain in chains:
        nodes = ""
        for index, (kind, entity_id) in enumerate(chain):
            if index:
                nodes += '<span class="dpr-line-arrow">→</span>'
            nodes += f'<div class="dpr-line-node"><span>{_e(kind)}</span><code>{_e(entity_id)}</code></div>'
        chain_html += f'<div class="dpr-line-chain">{nodes}</div>'
    return (
        _intro("数据血缘", "从数据集版本追溯输入数据、处理流程和操作记录。", "")
        + _metrics([("发布版本覆盖率", "100%", "目标：所有 Dataset Version"), ("配置版本覆盖率", "100%", "流程 / 算子 / Schema"), ("人工操作覆盖率", "99.6%", "18 条历史数据待补齐"), ("孤立资产", "0", "最近 24 小时")])
        + _section("血缘链路", f'<div class="dpr-lineage">{chain_html}</div>')
    )


def render_capabilities():
    component_rows = [
        [
            f'<code>{_e(key)}</code>',
            f'<b>{_e(name)}</b>',
            _e(description),
            '<span class="dpr-state green">已注册</span>',
        ]
        for key, (name, description) in WORKBENCH_COMPONENTS.items()
    ]
    operator_rows = [
        [f'<code>{_e(key)}</code>', f'<b>{_e(name)}</b>', '<span class="dpr-state green">已发布</span>', '<a href="#" onclick="toast(\'Demo: 查看能力详情\');return false;">详情</a>']
        for key, name in OPERATORS.items()
    ]
    return (
        _intro("能力注册", "管理流程可使用的自动化算子和工作台组件。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 注册能力\');return false;">+ 注册能力</a>')
        + _section("自动化算子", _table(["Operator Key", "能力", "状态", "操作"], operator_rows))
        + _section("工作台组件", _table(["Component Key", "组件", "输入 / 输出边界", "状态"], component_rows))
    )


def render_workbench_schemas():
    cards = ""
    for item in WORKBENCH_SCHEMAS:
        cards += f"""
        <article class="dpr-schema-card">
          <div class="dpr-schema-head"><div><code>{_e(item['id'])}</code><h3>{_e(item['name'])}</h3></div>{_state(item['status'])}</div>
          <div class="dpr-schema-label">Layout regions</div>
          <div class="dpr-region-row">{_code_list(item['regions'])}</div>
          <div class="dpr-schema-label">Components</div>
          <div class="dpr-component-list">{_code_list(item['components'])}</div>
          <div class="dpr-schema-label">Actions</div>
          <div class="dpr-component-list">{_code_list(item['actions'])}</div>
          <div class="dpr-card-foot"><span>已发布版本冻结</span><a href="{_e(item['preview'])}">预览工作台 →</a></div>
        </article>
        """
    return (
        _intro("工作台 Schema", "管理人工任务使用的工作台界面配置。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 新建 Schema 草稿\');return false;">+ 新建 Schema</a>')
        + _section("已发布 Schema", f'<div class="dpr-schema-grid">{cards}</div>')
    )


def render_operations():
    metrics = _metrics(
        [
            ("端到端交付周期", "6.8 天", '<span class="dpr-ok">↓ 12.4%</span> vs 上周期'),
            ("自动处理覆盖率", "74.6%", "算子节点占比"),
            ("资源利用率", "68.4%", "计算与存储综合"),
            ("血缘覆盖率", "99.7%", "发布版本 100%"),
            ("本周产能", "5,420 EP", "计划达成 94%"),
            ("存储使用", "28.6 TB", "本周新增 2.4 TB"),
        ]
    )
    stage_rows = [
        ["采集 / 导入", "1,500 Recording", "1,240", "82.7%", "0.8 天", "设备离线 1"],
        ["数据标准化", "1,240 Recording", "1,084", "87.4%", "0.7 天", "导入失败 18"],
        ["Episode 切分", "1,084 Recording", "842 EP", "77.7%", "0.6 天", "正常"],
        ["动作标注", "842 EP", "488 EP", "58.0%", "2.8 天", "当前瓶颈"],
        ["数据集构建", "488 EP", "452 EP", "92.6%", "0.4 天", "待构建 36"],
        ["版本发布", "452 EP", "441 EP", "97.6%", "0.2 天", "待审批 1"],
    ]
    return (
        _intro("交付看板", "查看交付进度、周期、产能和资源使用情况。", "")
        + metrics
        + _section("端到端交付漏斗", _table(["环节", "输入", "完成", "完成率", "平均周期", "风险"], [[_e(cell) for cell in row] for row in stage_rows]))
    )


def render_project_management():
    rows = [
        [
            f'<b>{_e(project["name"])}</b>',
            _e(project["description"]),
            _e(project["owner"]),
        ]
        for project in PROJECT_MANAGEMENT_ITEMS
    ]
    return (
        _intro("项目管理", "维护采集与处理任务所属项目。", "")
        + _table(["项目名称", "项目描述", "负责人"], rows)
    )


def render_workbench_management():
    workbench_rows = [
        [
            f'<code>{_e(schema["id"])}</code>',
            f'<b>{_e(schema["name"])}</b>',
            _record_tag(schema["type"]),
            _code_list(schema["regions"]),
            str(len(schema["components"])),
            _state(schema["status"]),
            (
                f'<a href="{_e(schema["preview"])}">预览</a> · '
                '<a href="#" onclick="toast(\'Demo: 编辑工作台\');return false;">编辑</a>'
            ),
        ]
        for schema in WORKBENCH_SCHEMAS
    ]
    component_rows = [
        [
            f'<code>{_e(component_id)}</code>',
            f'<b>{_e(name)}</b>',
            _e(description),
            _e(WORKBENCH_COMPONENT_USAGE[component_id]),
            '<span class="dpr-state green">可用</span>',
            '<a href="#" onclick="toast(\'Demo: 查看组件\');return false;">详情</a>',
        ]
        for component_id, (name, description) in WORKBENCH_COMPONENTS.items()
    ]
    workbench_section = _section(
        "工作台配置",
        _table(["工作台 ID", "名称", "类型", "区域", "组件数", "状态", "操作"], workbench_rows),
        actions="""<a class="btn btn-primary" href="#" onclick="toast('Demo: 新建工作台');return false;">+ 新建工作台</a>""",
    )
    component_section = _section(
        "组件列表",
        _table(["组件 ID", "组件名称", "功能", "适用工作台", "状态", "操作"], component_rows),
        actions="""<a class="btn btn-primary" href="#" onclick="toast('Demo: 注册组件');return false;">+ 注册组件</a>""",
    )
    return (
        _intro("工作台管理", "配置人工执行工作台，并维护可复用界面组件。", "")
        + f"""
        <div class="det-tabs">
          <span class="det-tab active" onclick="switchDetTab(this,'workbench-config')">工作台</span>
          <span class="det-tab" onclick="switchDetTab(this,'component-config')">组件</span>
        </div>
        <div id="det-pane-workbench-config" class="det-pane active">
          {workbench_section}
        </div>
        <div id="det-pane-component-config" class="det-pane">
          {component_section}
        </div>
        """
    )


def render_supplier_management():
    rows = [
        ["SUP-001", "<b>光轮智能</b>", "采集服务", "Moz1 家居场景", "12 人", "2026-12-31", _state("running"), '<a href="#">详情</a>'],
        ["SUP-002", "<b>供应商 A</b>", "标注服务", "动作分段标注", "28 人", "2026-10-15", _state("running"), '<a href="#">详情</a>'],
        ["SUP-003", "<b>千寻数据</b>", "数据采购", "厨房合作采集", "—", "2026-09-30", _state("pending"), '<a href="#">详情</a>'],
    ]
    return (
        _intro("供应商管理", "管理外部供应商、服务范围、协议周期和交付状态。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 新建供应商\');return false;">+ 新建供应商</a>')
        + _metrics([("合作供应商", "3", "2 家执行中"), ("供应商人员", "40", "已完成技能认证"), ("本月交付", "2,480 条", "按任务统一统计"), ("待处理事项", "2", "协议 1 · 交付 1")])
        + _section("供应商列表", _table(["供应商 ID", "供应商", "服务类型", "服务范围", "人员", "协议到期", "状态", "操作"], rows))
    )


def render_personnel_management():
    rows = [
        ["USR-2105", "<b>joanna.qiao</b>", "平台自有", "标注 · 验收", "P0 / P1", "工作中", "2026-07-27 10:42", '<a href="#">详情</a>'],
        ["USR-2217", "<b>刘素粉</b>", "光轮智能", "数据采集", "P1", "工作中", "2026-07-27 10:35", '<a href="#">详情</a>'],
        ["USR-2240", "<b>包媛桐</b>", "平台自有", "数据处理", "P0 / P1", "在线", "2026-07-27 10:38", '<a href="#">详情</a>'],
        ["USR-2298", "<b>供应商 A-017</b>", "供应商 A", "动作标注", "P1", "离线", "2026-07-26 18:12", '<a href="#">详情</a>'],
    ]
    return (
        _intro("人员管理", "管理人员归属、技能、可承接优先级与工作状态。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 添加人员\');return false;">+ 添加人员</a>')
        + _section("人员列表", _table(["人员 ID", "姓名", "归属", "技能", "任务等级", "状态", "最近活跃", "操作"], rows))
    )


def render_permission_management():
    role_rows = [
        ["ROLE-DATA-ADMIN", "<b>数据管理员</b>", "12 人", "数据平台全部菜单", "2026-07-21", '<a href="#">编辑</a>'],
        ["ROLE-OPERATOR", "<b>生产执行人员</b>", "46 人", "任务、工作台", "2026-07-18", '<a href="#">编辑</a>'],
        ["ROLE-VENDOR", "<b>供应商人员</b>", "40 人", "已授权任务与数据", "2026-07-16", '<a href="#">编辑</a>'],
    ]
    resource_rows = [
        ["RES-PROJECT", "项目", "PRJ-*", "查看 · 编辑 · 管理成员"],
        ["RES-TASK", "任务", "COL-* / PROC-*", "查看 · 执行 · 分配"],
        ["RES-DATASET", "数据集", "dataset.*", "查看 · 构建 · 发布"],
        ["RES-CONFIG", "配置", "规则 / 场景 / 标签", "查看 · 编辑"],
    ]
    grant_rows = [
        ["AUTH-001", "ROLE-DATA-ADMIN", "PRJ-MOZ1-SFT-07", "管理", "joanna.qiao", "长期有效"],
        ["AUTH-002", "ROLE-OPERATOR", "PROC-2026-0922", "执行", "数据工厂管理员", "2026-08-05"],
        ["AUTH-003", "ROLE-VENDOR", "COL-2026-0718", "执行", "joanna.qiao", "2026-07-31"],
    ]
    role_section = _section(
        "角色列表",
        _table(["角色 ID", "角色名称", "成员", "数据范围", "更新时间", "操作"], role_rows),
        actions="""<a class="btn btn-primary" href="#" onclick="toast('Demo: 新建角色');return false;">+ 新建角色</a>""",
    )
    resource_section = _section(
        "资源列表",
        _table(["资源类型", "资源名称", "资源标识", "可授权动作"], resource_rows),
    )
    grant_section = _section(
        "授权记录",
        _table(["授权 ID", "角色", "资源", "权限", "授权人", "有效期"], grant_rows),
        actions="""<a class="btn btn-primary" href="#" onclick="toast('Demo: 新建授权');return false;">+ 新建授权</a>""",
    )
    return (
        _intro("权限管理", "用角色、资源和授权关系控制数据平台访问范围。", "")
        + f"""
        <div class="det-tabs">
          <span class="det-tab active" onclick="switchDetTab(this,'permission-roles')">角色管理</span>
          <span class="det-tab" onclick="switchDetTab(this,'permission-resources')">资源管理</span>
          <span class="det-tab" onclick="switchDetTab(this,'permission-grants')">授权管理</span>
        </div>
        <div id="det-pane-permission-roles" class="det-pane active">
          {role_section}
        </div>
        <div id="det-pane-permission-resources" class="det-pane">
          {resource_section}
        </div>
        <div id="det-pane-permission-grants" class="det-pane">
          {grant_section}
        </div>
        """
    )


PAGE_RENDERERS = {
    "collection_tasks": render_collection_tasks,
    "processing_tasks": render_processing_tasks,
    "allocation_management": render_allocation_management,
    "data_management": render_data_management,
    "project_management": render_project_management,
    "workbench_management": render_workbench_management,
    "supplier_management": render_supplier_management,
    "personnel_management": render_personnel_management,
    "permission_management": render_permission_management,
}


def render_product_page(page_key):
    if page_key not in PAGE_RENDERERS:
        raise KeyError(f"unknown data platform page: {page_key}")
    return PAGE_RENDERERS[page_key]()


# ---------------------------------------------------------------------------
# Styles isolated with a dpr- prefix so the shared portal remains unaffected.
# ---------------------------------------------------------------------------

DATA_PLATFORM_CSS = """
.dpr-intro{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;margin:0 0 22px;padding:4px 0}
.dpr-intro h1{margin:3px 0 6px;font-size:24px;font-weight:650;letter-spacing:-.2px;color:#142b33}
.dpr-intro p{margin:0;max-width:820px;color:#607078;font-size:13px;line-height:1.7}
.dpr-eyebrow{font-size:11px;letter-spacing:1.2px;color:#149DAA;font-weight:700}
.dpr-intro-actions{display:flex;align-items:center;gap:8px;flex:none}
.dpr-role{display:flex;align-items:center;gap:8px;padding:7px 10px;background:#fff;border:1px solid #e2e7e9;border-radius:8px;font-size:12px;color:#607078}
.dpr-role select{border:0;outline:0;background:#fff;color:#142b33;font-weight:600;max-width:210px}
.dpr-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:18px}
.dpr-metric{background:#fff;border:1px solid #e8edef;border-radius:10px;padding:17px 18px;box-shadow:0 1px 2px rgba(16,42,50,.03)}
.dpr-metric-label{font-size:12px;color:#728188}
.dpr-metric-value{font-size:26px;font-weight:680;color:#142b33;margin:5px 0 3px}
.dpr-metric-sub{font-size:11.5px;color:#89969b}
.dpr-section{background:#fff;border:1px solid #e8edef;border-radius:10px;padding:20px;margin-bottom:16px;box-shadow:0 1px 2px rgba(16,42,50,.025)}
.dpr-section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:16px}
.dpr-section-head h2{margin:0;color:#20383f;font-size:16px;font-weight:650}
.dpr-section-head p{margin:5px 0 0;color:#76858b;font-size:12.5px;line-height:1.5}
.dpr-role-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.dpr-role-card{display:flex;flex-direction:column;min-height:112px;padding:15px;border:1px solid #e6ecee;border-radius:8px;color:#20383f;background:linear-gradient(180deg,#fff,#fbfdfd)}
.dpr-role-card:hover{border-color:#65bdc5;box-shadow:0 4px 14px rgba(20,157,170,.08);color:#20383f}
.dpr-role-card b{font-size:14px}.dpr-role-card span{font-size:12px;color:#728188;margin:7px 0;line-height:1.5}.dpr-role-card em{font-size:12px;color:#149DAA;font-style:normal;margin-top:auto}
.dpr-run-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.dpr-run-card{display:block;border:1px solid #e4eaec;border-radius:8px;padding:15px;color:#263d45}.dpr-run-card:hover{border-color:#65bdc5;color:#263d45}
.dpr-run-top{display:flex;justify-content:space-between;gap:10px;margin-bottom:10px}.dpr-run-card>b{font-size:13.5px}
.dpr-run-meta{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}.dpr-run-meta span{font:11px 'SF Mono',Menlo,monospace;background:#f2f6f7;padding:3px 7px;border-radius:4px;color:#5c6d73}
.dpr-stage-rail{display:flex;gap:4px;margin:13px 0 7px}.dpr-stage-rail i{height:5px;flex:1;background:#e5e9eb;border-radius:4px}.dpr-stage-rail i.done{background:#5fb39b}.dpr-stage-rail i.active{background:#149DAA;box-shadow:0 0 0 2px rgba(20,157,170,.13)}
.dpr-run-card small{color:#829096}
.dpr-risk{color:#c64b40!important}.dpr-ok{color:#2f8d70!important}
.dpr-state{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:650;white-space:nowrap}.dpr-state.green{color:#26785f;background:#e5f5ee}.dpr-state.blue{color:#136f78;background:#dff4f6}.dpr-state.amber{color:#946118;background:#fff2d7}.dpr-state.red{color:#b34239;background:#fdebea}.dpr-state.purple{color:#6c4ba2;background:#f1eafa}.dpr-state.gray{color:#66757b;background:#edf0f1}
.dpr-table-wrap{overflow:auto;border:1px solid #e8edef;border-radius:8px}.dpr-table{width:100%;border-collapse:separate;border-spacing:0;min-width:920px;font-size:12px}
.dpr-table th{padding:10px 12px;text-align:left;background:#f6f8f9;color:#65747a;font-weight:600;white-space:nowrap;border-bottom:1px solid #e4e9eb}
.dpr-table td{padding:12px;vertical-align:middle;color:#334a52;border-bottom:1px solid #eef1f2;line-height:1.55}.dpr-table tbody tr:last-child td{border-bottom:0}.dpr-table tbody tr:hover td{background:#fbfdfd}
.dpr-table code,.dpr-pipeline-card code,.dpr-schema-card code,.dpr-run-top code,.dpr-history code,.dpr-line-node code{font:11px 'SF Mono',Menlo,monospace;color:#50636a}.dpr-table small{color:#7d8b90}
.dpr-empty{text-align:center!important;color:#8b989d!important;padding:32px!important}
.dpr-progress{display:flex;align-items:center;gap:8px;min-width:100px}.dpr-progress-track{height:6px;flex:1;background:#edf1f2;border-radius:5px;overflow:hidden}.dpr-progress-track span{display:block;height:100%;background:#149DAA;border-radius:5px}.dpr-progress b{font-size:11px;color:#52666d}
.dpr-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}.dpr-task-tabs{display:flex;align-items:center;gap:24px;border-bottom:1px solid #e5eaec}.dpr-task-tab{position:relative;border:0;background:transparent;padding:7px 2px 10px;color:#65757b;font-size:13px;cursor:pointer}.dpr-task-tab:hover{color:#149DAA}.dpr-task-tab.active{color:#149DAA;font-weight:650}.dpr-task-tab.active:after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:2px;background:#149DAA;border-radius:2px}.dpr-task-tab b{display:inline-flex;align-items:center;justify-content:center;min-width:18px;height:18px;margin-left:4px;padding:0 5px;border-radius:9px;background:#edf2f3;color:#65757b;font-size:10px}.dpr-task-tab.active b{background:#dff4f6;color:#136f78}
#dpr-task-table{background:#fff}#dpr-task-table td{background:#fff}#dpr-task-table tbody tr:hover td{background:#fbfdfd}
.dpr-task-filters{width:100%;margin-bottom:16px;box-sizing:border-box}.dpr-task-filters .ff{min-width:155px}.dpr-task-filters .ff input,.dpr-task-filters .ff select{min-width:155px}
.dpr-collection-drawer{width:500px;max-width:calc(100vw - 24px)}.dpr-collection-drawer .drawer-body{padding-top:24px}.dpr-collection-drawer .fg{margin-bottom:20px}.dpr-collection-drawer .fg input,.dpr-collection-drawer .fg select{height:38px;box-sizing:border-box;background:#fff}.dpr-optional{color:#829096;font-weight:400}.dpr-field-help{margin-top:1px;color:#849298;font-size:11.5px;line-height:1.5}.dpr-processing-drawer{width:720px}.dpr-processing-assignment{margin-top:8px;padding-top:18px;border-top:1px solid #edf1f2}.dpr-processing-assignment-title{display:flex;align-items:baseline;justify-content:space-between;gap:14px;margin-bottom:12px}.dpr-processing-assignment-title b{font-size:14px;color:#2b434b}.dpr-processing-assignment-title span{font-size:11px;color:#829197}.dpr-processing-assignment-card{margin-bottom:10px;padding:12px;border:1px solid #e2e8ea;border-radius:8px;background:#fafcfc}.dpr-processing-assignment-head{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:10px}.dpr-processing-assignment-head>div{display:flex;align-items:center;gap:7px}.dpr-processing-assignment-head b{font-size:12.5px;color:#2e464e}.dpr-processing-assignment-head>div span{padding:2px 6px;border-radius:8px;background:#e5f5ee;color:#2f8064;font-size:9.5px}.dpr-processing-assignment-head label{display:flex;align-items:center;gap:7px;color:#718087;font-size:11px}.dpr-processing-assignment-head select{width:94px;height:30px;padding:0 7px;border:1px solid #d8e0e3;border-radius:5px;background:#fff;color:#324950}.dpr-processing-assignment-cols,.dpr-processing-assignment-row{display:grid;grid-template-columns:1fr 110px 26px;align-items:center;gap:7px}.dpr-processing-assignment-cols{margin-bottom:4px;color:#879398;font-size:9.5px}.dpr-processing-assignment-row{margin-bottom:6px}.dpr-processing-assignment-row select,.dpr-processing-percent input{width:100%;height:32px;box-sizing:border-box;border:1px solid #d9e0e2;border-radius:6px;background:#fff;color:#334a52}.dpr-processing-assignment-row select{padding:0 8px}.dpr-processing-percent{position:relative}.dpr-processing-percent input{padding:0 24px 0 8px}.dpr-processing-percent span{position:absolute;right:8px;top:7px;color:#89959a;font-size:11px}.dpr-processing-assignment-remove{width:26px;height:26px;border:0;background:transparent;color:#a7b0b4;font-size:17px;cursor:pointer}.dpr-processing-assignment-remove:hover{color:#d05a50}.dpr-processing-assignment-foot{display:flex;align-items:center;justify-content:space-between;margin-top:7px}.dpr-processing-assignment-foot button{padding:0;border:0;background:transparent;color:#149DAA;font-size:11px;cursor:pointer}.dpr-processing-assignment-foot span{color:#74848a;font-size:11px}.dpr-processing-assignment-foot b.ok{color:#2f8d70}.dpr-processing-assignment-foot b.bad{color:#c64b40}.dpr-processing-assignment-empty{padding:18px;border:1px dashed #d6dfe2;border-radius:8px;background:#fafcfc;color:#7d8c91;font-size:12px;text-align:center}
.dpr-scenario-summary{display:flex;align-items:center;gap:28px;margin-bottom:16px;padding:14px 18px;border:1px solid #dce8ea;border-radius:9px;background:#f7fbfb}.dpr-scenario-summary>div{display:flex;align-items:baseline;gap:6px}.dpr-scenario-summary span{color:#66777d;font-size:12px}.dpr-scenario-summary b{color:#149DAA;font-size:24px}.dpr-scenario-summary small{color:#829096}.dpr-scenario-summary p{margin:0 0 0 auto;color:#53666d;font-size:12px}.dpr-capacity-overload{color:#b45246;font-weight:650;white-space:nowrap}.dpr-assignment-context{display:grid;grid-template-columns:1fr;gap:8px;margin-bottom:12px;padding:12px 14px;border:1px solid #e1e7e9;border-radius:7px;background:#fafcfc}.dpr-assignment-context span{display:flex;justify-content:space-between;gap:18px;color:#74848a;font-size:12px}.dpr-assignment-context b{color:#2f464e}.dpr-inline-notice{margin-bottom:18px;padding:10px 12px;border-left:3px solid #e5a64c;border-radius:5px;background:#fff8e8;color:#76591f;font-size:12px}.dpr-inline-notice.success{border-left-color:#69ad8d;background:#f0faf5;color:#3f725d}.dpr-project-scope{display:flex;align-items:center;gap:9px;color:#63757c;font-size:12px;white-space:nowrap}.dpr-project-scope select{min-width:152px;height:36px;padding:0 32px 0 11px;border:1px solid #d8e0e3;border-radius:7px;background:#fff;color:#2d444c}.dpr-allocation-tabs{margin-bottom:16px}.dpr-allocation-funnel{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.dpr-allocation-stage{padding:15px;border:1px solid #e4eaec;border-radius:9px;background:#fbfdfd}.dpr-allocation-stage-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:13px}.dpr-allocation-stage-head>div{display:flex;flex-direction:column;gap:4px}.dpr-allocation-stage-head b{font-size:15px;color:#263f47}.dpr-allocation-stage-head span{font-size:11px;color:#7a898f}.dpr-allocation-stage-head strong{font-size:22px;color:#273f47;text-align:right}.dpr-allocation-stage-head strong small{display:block;font-size:10px;color:#89969b;font-weight:400}.dpr-allocation-bar{display:flex;height:12px;overflow:hidden;border-radius:6px;background:#edf1f2}.dpr-allocation-bar i{display:block;height:100%}.dpr-allocation-bar i.unassigned,.dpr-allocation-legend i.unassigned{background:#d96c62}.dpr-allocation-bar i.assigned,.dpr-allocation-legend i.assigned{background:#e5a64c}.dpr-allocation-bar i.processing,.dpr-allocation-legend i.processing{background:#5c9db3}.dpr-allocation-bar i.completed,.dpr-allocation-legend i.completed{background:#69ad8d}.dpr-allocation-legend{display:grid;grid-template-columns:1fr 1fr;gap:7px 12px;margin-top:12px;color:#6c7c82;font-size:10.5px}.dpr-allocation-legend span{white-space:nowrap}.dpr-allocation-legend b{font-weight:400}.dpr-allocation-legend i{display:inline-block;width:7px;height:7px;margin-right:5px;border-radius:2px}.dpr-allocation-filters{margin-bottom:14px}.dpr-allocation-filters .ff{min-width:135px}.dpr-allocation-filters .ff input,.dpr-allocation-filters .ff select{min-width:135px}.dpr-allocation-table-foot{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:12px;color:#738289;font-size:12px}.dpr-allocation-table-foot button:disabled{opacity:.45;cursor:not-allowed}.dpr-stalled{color:#b45246;font-weight:650;white-space:nowrap}.dpr-link-button{padding:0;border:0;background:transparent;color:#149DAA;font:inherit;cursor:pointer;white-space:nowrap}#dpr-allocation-backlog-table{min-width:1320px}#dpr-allocation-backlog-table th:first-child,#dpr-allocation-backlog-table td:first-child{width:28px;text-align:center}#dpr-stream-backlog-table{min-width:1280px}#dpr-unbound-pool-table{min-width:1180px}#dpr-stream-backlog-table th:first-child,#dpr-stream-backlog-table td:first-child,#dpr-unbound-pool-table th:first-child,#dpr-unbound-pool-table td:first-child{width:28px;text-align:center}.dpr-flow-assignment-filters{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:14px}.dpr-flow-assignment-filters .ff{display:flex;flex-direction:column;gap:6px}.dpr-flow-assignment-filters .ff label{font-size:12px;color:#5b6b72}.dpr-flow-assignment-filters .ff input,.dpr-flow-assignment-filters .ff select{width:100%;height:36px;padding:0 10px;border:1px solid #d9e0e2;border-radius:6px;background:#fff;box-sizing:border-box}.dpr-flow-assignment-filters .filter-actions{display:flex;align-items:flex-end;gap:8px}.dpr-flow-match{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-top:18px;padding:16px 18px;border:1px solid #cfe5e7;border-radius:9px;background:#f4fbfb}.dpr-flow-match>div{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}.dpr-flow-match span{color:#5b6d73;font-size:12px}.dpr-flow-match b{font-size:14px;color:#2a424a}.dpr-flow-match em{font-size:26px;font-style:normal;color:#149DAA}.dpr-flow-match small{color:#839197}.dpr-allocation-drawer{width:500px;max-width:calc(100vw - 24px)}.dpr-allocation-drawer .drawer-body{padding-top:22px}.dpr-allocation-drawer .fg{margin-bottom:18px}.dpr-allocation-drawer .fg input,.dpr-allocation-drawer .fg select,.dpr-allocation-drawer .fg textarea{width:100%;box-sizing:border-box;background:#fff}.dpr-allocation-drawer .fg input,.dpr-allocation-drawer .fg select{height:38px}.dpr-allocation-drawer .fg textarea{padding:9px 11px;border:1px solid #d9e0e2;border-radius:6px;resize:vertical}.dpr-drawer-summary{margin-bottom:20px;padding:12px 14px;border-radius:7px;background:#f1f7f8;color:#53666d;font-size:12px}.dpr-drawer-summary b{color:#149DAA}
.dpr-task-name{color:#20383f}.dpr-task-name:hover{color:#149DAA}.dpr-priority{font-weight:650;color:#354b52}.dpr-task-actions{display:flex;align-items:center;gap:10px;white-space:nowrap}.dpr-task-actions a,.dpr-task-actions button{padding:0;border:0;background:transparent;color:#149DAA;font:inherit;cursor:pointer}.dpr-task-actions a:hover,.dpr-task-actions button:hover{color:#0f7780}.dpr-task-progress-stack{display:flex;flex-direction:column;gap:5px;min-width:230px}.dpr-task-progress-stack.collection{max-width:300px}.dpr-task-progress-item{display:grid;grid-template-columns:30px minmax(170px,1fr);align-items:center;gap:6px;white-space:nowrap}.dpr-task-progress-label{font-size:10.5px;color:#354b52;font-weight:600}.dpr-task-progress-line{position:relative;height:14px;background:#edf1f2;border-radius:7px;overflow:hidden}.dpr-task-progress-line i{position:absolute;inset:0 auto 0 0;display:block;height:100%;border-radius:7px;background:#149DAA;opacity:.62}.dpr-task-progress-line i.blue{background:#5a82d1}.dpr-task-progress-line i.teal{background:#149DAA}.dpr-task-progress-line i.green{background:#5fab91}.dpr-task-progress-line b{position:relative;z-index:1;display:block;padding:0 6px;font:9px/14px 'SF Mono',Menlo,monospace;color:#30454d;text-align:center;white-space:nowrap}.dpr-record-page{width:100%;max-width:100%;min-width:0;overflow:hidden;padding-top:2px;box-sizing:border-box}.dpr-record-top{display:flex;align-items:center;justify-content:space-between;gap:16px;max-width:100%;margin-bottom:14px}.dpr-record-top>div{display:flex;align-items:center;gap:12px;min-width:0}.dpr-record-top a{font-size:12px;color:#149DAA}.dpr-record-top b{font-size:16px;color:#233a42}.dpr-record-top code{font:11px 'SF Mono',Menlo,monospace;color:#718188;background:#edf2f3;padding:3px 7px;border-radius:4px}.dpr-record-filters{width:100%;max-width:100%;margin-bottom:16px;box-sizing:border-box}.dpr-record-summary{display:flex;align-items:center;gap:8px;max-width:100%;margin:0 0 12px;color:#52636a;font-size:13px}.dpr-record-summary span:first-child:after{content:"：";margin-left:2px}.table-wrap.dpr-record-table-wrap{width:100%;max-width:100%;min-width:0;overflow-x:auto;overflow-y:hidden;background:#fff;box-sizing:border-box}.dpr-record-table{width:100%;min-width:1480px}.dpr-record-table.dpr-collection-record-table{min-width:940px}.dpr-record-table td{vertical-align:middle}.dpr-video-group{display:flex;align-items:center;white-space:nowrap}.dpr-record-table .vid-thumb{width:86px;height:54px}.dpr-record-tag{display:inline-flex;align-items:center;padding:3px 8px;border:1px solid transparent;border-radius:5px;font-size:11.5px;white-space:nowrap}.dpr-record-tag.green{color:#2f8d60;background:#edf8f2;border-color:#caead9}.dpr-record-tag.orange{color:#a96b13;background:#fff8e6;border-color:#f5dda4}.dpr-record-tag.red{color:#b7473f;background:#fdeeee;border-color:#f3cbc8}.dpr-record-tag.blue{color:#4f69aa;background:#eef2fb;border-color:#cad5f0}.dpr-record-tag.teal{color:#117a83;background:#e8f7f8;border-color:#b9e3e7}.dpr-record-tag.purple{color:#7447ad;background:#f4edfb;border-color:#ddc9f2}.dpr-record-tag.gray{color:#7b878c;background:#f3f5f5;border-color:#e2e6e7}.dpr-record-operator{font-size:11.5px;color:#67777d;white-space:nowrap}.dpr-record-actions{white-space:nowrap}.dpr-record-actions a{margin-right:10px;color:#149DAA}
.dpr-data-management{width:100%;max-width:100%;min-width:0;overflow:hidden}.dpr-data-management .det-tabs{margin-bottom:16px}.dpr-management-record-table{width:100%;min-width:1240px}.dpr-management-record-table .vid-thumb{width:76px;height:48px}.dpr-third-party-table{width:100%;min-width:1080px}.dpr-management-summary{display:flex;align-items:center;justify-content:space-between;gap:16px;margin:0 0 14px;color:#52636a;font-size:13px}.dpr-management-summary .btn{flex:none}
.dpr-tree-toggle{width:24px;height:24px;margin-right:7px;padding:0;border:0;border-radius:5px;background:#edf5f6;color:#147c86;cursor:pointer}.dpr-flow-link{padding:0;border:0;background:transparent;color:#149DAA;font-size:12px;cursor:pointer}.dpr-process-tree-row>td{padding:0!important;background:#f8fafb!important}.dpr-process-tree{padding:14px 20px 17px 50px}.dpr-process-tree-meta{display:flex;gap:24px;flex-wrap:wrap;margin-bottom:10px;color:#6c7d83;font-size:11.5px}.dpr-process-tree table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e8ea;border-radius:7px;overflow:hidden}.dpr-process-tree th,.dpr-process-tree td{padding:9px 12px;border-bottom:1px solid #edf1f2;font-size:11.5px;text-align:left}.dpr-process-tree th{background:#f2f6f7;color:#68787e}.dpr-process-tree tbody tr:last-child td{border-bottom:0}
.dpr-record-detail-meta{display:flex;gap:22px;flex-wrap:wrap;margin:0 0 16px;padding:11px 14px;border:1px solid #e5eaec;border-radius:8px;background:#fff;color:#6a7a80;font-size:12px}.dpr-record-detail-meta code{font:11px 'SF Mono',Menlo,monospace;color:#486068}.dpr-record-detail-meta b{color:#2f454d}.dpr-record-page>.det-tabs{margin-bottom:16px}.dpr-detail-video-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:18px}.dpr-detail-video{position:relative;display:flex;align-items:center;justify-content:center;aspect-ratio:16/9;border-radius:8px;background:linear-gradient(135deg,#283545,#17202c);color:#fff}.dpr-detail-video span{position:absolute;left:12px;top:10px;font-size:11px;color:rgba(255,255,255,.72)}.dpr-detail-video b{font-size:26px;color:rgba(255,255,255,.72)}.dpr-trajectory-card{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:12px}.dpr-trajectory-card>div{display:flex;flex-direction:column;gap:4px;padding:13px;border:1px solid #e5eaec;border-radius:8px;background:#fff}.dpr-trajectory-card span{font-size:11px;color:#7c8a8f}.dpr-trajectory-card b{font-size:15px;color:#2a424a}.dpr-trajectory-chart{display:flex;align-items:center;justify-content:center;height:230px;border:1px dashed #cdd8dc;border-radius:8px;background:linear-gradient(180deg,#fbfdfd,#f3f8f9);color:#7e8d92;font-size:12px}.dpr-version-switch{display:flex;gap:8px;margin-bottom:12px}.dpr-version-button{padding:6px 14px;border:1px solid #dce4e6;border-radius:6px;background:#fff;color:#617278;cursor:pointer}.dpr-version-button.active{border-color:#149DAA;background:#e8f7f8;color:#117a83;font-weight:650}.dpr-version-pane{padding:16px;border:1px solid #e5eaec;border-radius:8px;background:#fff;margin-bottom:18px}.dpr-version-meta{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.dpr-version-meta>div{display:flex;flex-direction:column;gap:6px}.dpr-version-meta span{font-size:11px;color:#7b898f}.dpr-version-meta b{font-size:12px;color:#30474f}.dpr-version-note{display:flex;gap:12px;margin-top:14px;padding-top:12px;border-top:1px solid #eef1f2;font-size:12px}.dpr-version-note b{color:#30474f}.dpr-version-note span{color:#6f7f85}
.dpr-record-preview-page{background:#fff;border:1px solid #e7ecee;border-radius:10px;padding:18px}.dpr-preview-toolbar{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;min-height:43px;border-bottom:1px solid #e6ebed;margin-bottom:16px}.dpr-preview-tabs{display:flex;align-items:flex-end;gap:4px;flex:none}.dpr-preview-tab{padding:10px 16px;border:0;border-bottom:2px solid transparent;background:transparent;color:#66777d;font-size:13px;cursor:pointer}.dpr-preview-tab:hover{color:#149DAA}.dpr-preview-tab.active{color:#149DAA;border-bottom-color:#149DAA;font-weight:650}.dpr-preview-pane{min-height:560px}.dpr-preview-camera-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-bottom:16px}.dpr-preview-camera{position:relative;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:7px;height:150px;border-radius:8px;background:linear-gradient(135deg,#283545,#131b27);color:rgba(255,255,255,.72)}.dpr-preview-camera>span{position:absolute;left:9px;top:8px;padding:2px 7px;border-radius:4px;background:rgba(0,0,0,.58);font:10px 'SF Mono',Menlo,monospace;color:#fff}.dpr-preview-camera>b{font-size:24px}.dpr-preview-camera>small{font-size:10px;color:rgba(255,255,255,.42)}.dpr-preview-traj-bar{display:flex;align-items:center;gap:14px;padding:10px 0;border-bottom:1px solid #edf1f2;margin-bottom:10px}.dpr-preview-traj-tabs{display:flex;align-items:center;gap:6px;flex:1}.dpr-preview-traj-tabs button{padding:5px 12px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#607178;font-size:11.5px;cursor:pointer}.dpr-preview-traj-tabs button.on{border-color:#149DAA;background:#149DAA;color:#fff}.dpr-preview-traj-tabs>i{width:1px;height:18px;background:#e3e8ea;margin:0 2px}.dpr-preview-traj-legend{display:flex;gap:12px;color:#65767c;font-size:11px}.dpr-preview-traj-legend i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:4px}.dpr-preview-traj-legend .cmd{background:#1F80A0}.dpr-preview-traj-legend .state{background:#52c41a}.dpr-preview-play{display:flex;gap:6px}.dpr-preview-play button{width:29px;height:29px;border:1px solid #dfe5e7;border-radius:6px;background:#fff;color:#149DAA;cursor:pointer}.dpr-preview-traj-views{height:340px;overflow:hidden}.dpr-preview-traj-grid{width:100%;height:100%;border-collapse:collapse;table-layout:fixed}.dpr-preview-traj-grid th{padding:5px 10px;border-bottom:1px solid #edf1f2;text-align:center;font-size:12px;color:#344b53}.dpr-preview-traj-grid th:first-child,.dpr-preview-traj-grid td:first-child{width:34px;text-align:center;color:#78868b}.dpr-preview-traj-grid td{padding:3px 10px;border-bottom:1px solid #f4f6f7}.dpr-preview-spark{display:block;width:100%;height:100%;min-height:18px}.dpr-preview-base-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;height:100%}.dpr-preview-base-grid>div{display:flex;flex-direction:column;gap:12px;padding:14px;border:1px solid #e5eaec;border-radius:8px;color:#40575f;font-size:12px}.dpr-preview-chart-line{display:block;flex:1;border-radius:6px;background-color:#f8fbfb;background-size:28px 28px;background-image:linear-gradient(#ebf0f1 1px,transparent 1px),linear-gradient(90deg,#ebf0f1 1px,transparent 1px);position:relative}.dpr-preview-chart-line:after{content:"";position:absolute;left:5%;right:5%;top:45%;height:3px;background:#149DAA;transform:skewY(-8deg);box-shadow:0 13px 0 #62aa72}.dpr-preview-chart-line.two:after{left:22%;right:22%;top:49%;height:90px;border:3px solid #149DAA;border-radius:50%;background:transparent;transform:none;box-shadow:5px 4px 0 #62aa72}.dpr-preview-moz{position:relative;height:100%;overflow:hidden;border:1px solid #e5eaec;border-radius:8px;background:#fbfcfd}.dpr-preview-moz-floor{position:absolute;left:0;right:0;bottom:0;height:70%;background-size:40px 40px;background-image:linear-gradient(#e8edef 1px,transparent 1px),linear-gradient(90deg,#e8edef 1px,transparent 1px);transform:perspective(600px) rotateX(55deg);transform-origin:bottom}.dpr-preview-robot{position:absolute;left:48%;top:40%;display:flex;flex-direction:column;align-items:center;font-size:62px;color:#c5ccd1}.dpr-preview-robot span{font-size:11px;color:#6d7d83}.dpr-preview-moz-info{position:absolute;right:14px;top:14px;display:flex;flex-direction:column;gap:8px;width:290px;padding:12px;border:1px solid #e3e9eb;border-radius:9px;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.05);font:10px 'SF Mono',Menlo,monospace;color:#687980}.dpr-preview-moz-info b{font:600 12px sans-serif;color:#314850}.dpr-preview-slider{width:100%;margin-top:13px;accent-color:#149DAA}.dpr-process-switcher{display:flex;align-items:center;gap:10px;justify-content:flex-end;min-width:0;margin:0 0 7px auto;white-space:nowrap}.dpr-process-switcher label{display:flex;align-items:center;gap:6px;color:#64757b;font-size:11.5px}.dpr-process-switcher select{width:146px;min-width:0;height:32px;padding:0 9px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#324850}.dpr-process-switcher label:first-child select{width:190px}.dpr-process-version-meta{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:14px}.dpr-process-version-meta>div{display:flex;flex-direction:column;gap:5px;padding:10px 12px;border:1px solid #e7ecee;border-radius:7px;background:#fafcfc}.dpr-process-version-meta span{font-size:10.5px;color:#7c8a8f}.dpr-process-version-meta b{font-size:12px;color:#30474f}.dpr-preview-seg-timeline{margin:16px 0 8px}.dpr-preview-seg-row{display:flex;align-items:center;gap:8px}.dpr-preview-seg-row>span{display:flex;align-items:center;justify-content:center;width:23px;height:23px;border-radius:50%;background:#e8f5f6;color:#127a84;font-size:10.5px;font-weight:650}.dpr-preview-seg-track{display:flex;flex:1;height:15px;gap:2px;overflow:hidden;border-radius:4px;background:#f1f4f5}.dpr-preview-segment{height:100%;cursor:pointer}.dpr-preview-segment:hover{filter:brightness(1.06)}.dpr-preview-process-caption{margin:18px 0 5px;color:#334b53;font-size:13px;font-weight:650}.dpr-preview-process-caption span{margin-left:7px;color:#849197;font-size:11px;font-weight:400}.dpr-preview-process-table{width:100%;border-collapse:collapse;font-size:12px}.dpr-preview-process-table th{padding:8px 11px;border-bottom:1px solid #e8edef;text-align:left;color:#77868c;font-weight:500}.dpr-preview-process-table td{padding:8px 11px;border-bottom:1px solid #f1f4f5;color:#354b52}.dpr-preview-process-table tr:hover td{background:#fafcfc}.dpr-preview-process-parent td{background:#f8fafb;font-weight:650}.dpr-preview-process-num{display:inline-flex;align-items:center;justify-content:center;width:19px;height:19px;margin-right:7px;border-radius:50%;background:#edf1f2;color:#6d7c82;font-size:10px}.dpr-preview-process-note{display:flex;gap:12px;margin-top:13px;padding:11px 13px;border:1px solid #e7ecee;border-radius:7px;background:#fafcfc;font-size:11.5px}.dpr-preview-process-note b{color:#344b53}.dpr-preview-process-note span{color:#6f7f85}
.dpr-history-toolbar{display:flex;align-items:center;justify-content:space-between;gap:18px;min-height:44px;margin-bottom:12px;border-bottom:1px solid #e8edef}.dpr-history-tabs{display:flex;align-items:center;gap:18px;align-self:stretch}.dpr-history-tab{position:relative;padding:0 2px;border:0;background:transparent;color:#687980;font-size:12px;cursor:pointer}.dpr-history-tab.active{color:#149DAA;font-weight:650}.dpr-history-tab.active:after{content:"";position:absolute;right:0;bottom:-1px;left:0;height:2px;background:#149DAA}.dpr-history-switcher{display:flex;align-items:center;gap:10px;padding-bottom:6px;white-space:nowrap}.dpr-history-switcher label{display:flex;align-items:center;gap:6px;color:#64757b;font-size:11.5px}.dpr-history-switcher select{width:148px;height:32px;padding:0 9px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#324850}.dpr-history-switcher label:first-child select{width:210px}.dpr-history-table th:first-child,.dpr-history-table td:first-child{width:18%}.dpr-history-table th:nth-child(2),.dpr-history-table td:nth-child(2){width:22%}
.dpr-pipeline-list{display:flex;flex-direction:column;gap:14px}.dpr-pipeline-card{border:1px solid #e1e7e9;border-radius:9px;padding:17px}.dpr-pipeline-head{display:flex;justify-content:space-between;gap:20px}.dpr-pipeline-head h3{margin:4px 0;font-size:15px}.dpr-pipeline-head span{font-size:11.5px;color:#7a898f}.dpr-version-stack{display:flex;flex-direction:column;gap:4px;text-align:right}.dpr-version-stack span{background:#f4f7f8;padding:4px 8px;border-radius:4px}
.dpr-node-flow{display:flex;align-items:center;gap:6px;overflow-x:auto;padding:17px 0 13px}.dpr-node{display:flex;flex-direction:column;min-width:118px;padding:9px 10px;border:1px solid #dfe6e8;border-radius:7px;background:#fafcfc}.dpr-node i{font:9px 'SF Mono',Menlo,monospace;text-transform:uppercase;color:#839197}.dpr-node b{font-size:12px;margin:3px 0;color:#31484f}.dpr-node small{font:9.5px 'SF Mono',Menlo,monospace;color:#7d8a90;max-width:155px;overflow:hidden;text-overflow:ellipsis}.dpr-node.operator{border-top:3px solid #6d8fda}.dpr-node.human{border-top:3px solid #d18a4f}.dpr-node.gateway{border-top:3px solid #8b6eb5}.dpr-node-arrow{color:#9aa5a9}
.dpr-card-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-top:11px;border-top:1px solid #edf0f1;font-size:11.5px;color:#7c8a90}
.dpr-publish-conditions{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.dpr-publish-conditions span,.dpr-publish-conditions b{padding:10px 12px;background:#f4f7f8;border:1px solid #e3e8ea;border-radius:7px;font-size:12px}.dpr-publish-conditions i{font-style:normal;color:#97a3a7}.dpr-publish-conditions b{background:#e7f6f3;border-color:#b9ddd3;color:#26785f}
.dpr-lineage{display:flex;flex-direction:column;gap:13px}.dpr-line-chain{display:flex;align-items:center;gap:7px;overflow:auto;padding:12px;background:#f7f9fa;border-radius:8px}.dpr-line-node{display:flex;flex-direction:column;min-width:135px;padding:9px;background:#fff;border:1px solid #e2e8ea;border-radius:7px}.dpr-line-node span{font-size:10px;color:#149DAA;font-weight:650;margin-bottom:4px}.dpr-line-arrow{color:#89969b}
.dpr-lock{display:inline-flex;padding:2px 7px;border-radius:10px;background:#f1eafa;color:#6c4ba2;font-size:11px}
.dpr-schema-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.dpr-schema-card{display:flex;flex-direction:column;padding:16px;border:1px solid #e3e9eb;border-radius:9px}.dpr-schema-head{display:flex;justify-content:space-between;gap:8px}.dpr-schema-head h3{margin:5px 0 12px;font-size:14px}.dpr-schema-label{font-size:10px;color:#89969b;text-transform:uppercase;letter-spacing:.5px;margin:9px 0 5px}.dpr-region-row,.dpr-component-list{display:flex;gap:5px;flex-wrap:wrap}.dpr-code{font:9.5px 'SF Mono',Menlo,monospace;background:#f2f5f6;color:#52666d;padding:3px 5px;border-radius:4px}.dpr-schema-card .dpr-card-foot{margin-top:auto;padding-top:13px}
@media(max-width:1180px){.dpr-metrics{grid-template-columns:repeat(2,1fr)}.dpr-role-grid{grid-template-columns:repeat(2,1fr)}.dpr-schema-grid{grid-template-columns:1fr}.dpr-allocation-funnel{grid-template-columns:1fr}.dpr-flow-assignment-filters{grid-template-columns:repeat(2,minmax(150px,1fr))}}
@media(max-width:780px){.dpr-intro{align-items:flex-start;flex-direction:column}.dpr-metrics,.dpr-role-grid,.dpr-run-grid,.dpr-detail-video-grid,.dpr-trajectory-card,.dpr-version-meta,.dpr-flow-assignment-filters{grid-template-columns:1fr}.dpr-record-top>div{align-items:flex-start;flex-direction:column;gap:5px}.dpr-record-summary{align-items:flex-start;flex-direction:column}.dpr-flow-match,.dpr-allocation-table-foot{align-items:flex-start;flex-direction:column}}
"""
