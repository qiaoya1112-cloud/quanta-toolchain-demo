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
        "subtitle": "管理指令采集、自由采集、DAgger 采集和数据导入任务",
        "icon": "&#9776;",
        "hide_from_nav": True,
    },
    "processing_tasks": {
        "path": "/data/processing-tasks",
        "title": "处理任务",
        "subtitle": "用筛选条件接收数据，并编排多个独立处理流程",
        "icon": "&#9776;",
        "nav_badge": "S025",
    },
    "allocation_management": {
        "path": "/data/allocations",
        "title": "分配管理",
        "subtitle": "先发现处理问题，再调整资源或补充处理绑定",
        "icon": "&#8646;",
        "hide_from_nav": True,
    },
    "allocation_management_v2": {
        "path": "/data/allocations-v2",
        "title": "分配管理",
        "subtitle": "按供应商与用户组统筹进行中的人工处理任务",
        "icon": "&#8646;",
        "nav_badge": "S025",
    },
    "allocation_management_old": {
        "path": "/data/allocations-legacy",
        "title": "分配管理-旧",
        "subtitle": "按资源调度、处理绑定和数据再处理三个场景管理分配",
        "icon": "&#8646;",
        "hidden": True,
    },
    "data_management": {
        "path": "/data/recordings",
        "title": "数据管理",
        "subtitle": "统一查看采集数据与导入数据",
        "icon": "&#9783;",
        "hide_from_nav": True,
    },
    "workbench": {
        "path": "/data/workbench",
        "title": "工作台",
        "subtitle": "领取并连续处理人工执行任务",
        "icon": "&#9881;",
        "legacy": True,
        "hide_from_nav": True,
    },
    "workbench_v2": {
        "path": "/data/workbench-v2",
        "title": "标注工作台",
        "nav_title": "标注工作台",
        "subtitle": "领取用户组或供应商任务，并处理被驳回的数据",
        "icon": "&#9881;",
        "nav_badge": "S025",
    },
    "personal_dashboard": {
        "path": "/data/dashboard",
        "title": "个人看板",
        "subtitle": "查看个人任务、产能与处理趋势",
        "icon": "&#9636;",
        "badge": "草稿",
        "legacy": True,
        "hide_from_nav": True,
    },
    "workflow_management": {
        "path": "/data/pipelines",
        "title": "流程管理",
        "subtitle": "配置并管理数据处理工作流",
        "icon": "&#8644;",
        "legacy": True,
    },
    "user_group_management": {
        "path": "/data/user-groups",
        "title": "用户组管理",
        "subtitle": "管理人工节点的领取范围与共享任务池",
        "icon": "&#9786;",
        "nav_badge": "S025",
    },
    "execution_records": {
        "path": "/data/runs",
        "title": "执行记录",
        "subtitle": "查看流程执行状态、输入、输出与日志",
        "icon": "&#9654;",
        "badge": "草稿",
        "legacy": True,
        "hide_from_nav": True,
    },
    "operator_management": {
        "path": "/data/operators",
        "title": "算子管理",
        "subtitle": "管理工作流可复用处理算子",
        "icon": "&#9881;",
        "badge": "草稿",
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
        "hide_from_nav": True,
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
        "badge": "草稿",
        "legacy": True,
        "hide_from_nav": True,
    },
    "tag_management": {
        "path": "/data/tags",
        "title": "标签管理",
        "subtitle": "维护数据与任务标签体系",
        "icon": "&#9873;",
        "legacy": True,
        "hide_from_nav": True,
    },
    "dataset_management": {
        "path": "/data/datasets",
        "title": "数据集管理",
        "subtitle": "管理数据集、版本与数据划分",
        "icon": "&#9636;",
        "legacy": True,
        "hide_from_nav": True,
    },
    "supplier_management": {
        "path": "/data/suppliers",
        "title": "供应商管理",
        "subtitle": "管理外部供应商、协议与交付状态",
        "icon": "&#9635;",
        "badge": "草稿",
    },
    "personnel_management": {
        "path": "/data/personnel",
        "title": "人员管理",
        "subtitle": "管理人员、技能、状态与供应商归属",
        "icon": "&#9786;",
        "badge": "草稿",
        "hide_from_nav": True,
    },
    "permission_management": {
        "path": "/data/permissions",
        "title": "权限管理",
        "subtitle": "管理角色、资源权限与授权关系",
        "icon": "&#9634;",
        "badge": "草稿",
    },
}

NAV_GROUPS = [
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
            "permission_management",
        ],
    ),
]


def build_navigation():
    """Return the tuple format consumed by the shared Quanta sidebar."""
    def nav_entry(page_key):
        spec = PAGE_SPECS[page_key]
        entry = (
            spec["path"],
            spec.get("nav_title", spec["title"]),
            spec["icon"],
        )
        badge = spec.get("nav_badge")
        return entry + (badge,) if badge else entry

    return [
        (
            group,
            [nav_entry(key) for key in page_keys],
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
    "basic_info": ("基础信息", "任务 ID、记录 ID、序列号、采集员等上下文"),
    "multi_view_video": ("多视角视频", "头部、左臂、右臂视频同步播放与逐帧定位"),
    "head_view_video": ("头部视频", "单头部摄像头视频播放与逐帧定位"),
    "playback_timeline": ("播放时间轴", "播放窗口、问题区间与标注片段的时间映射"),
    "instruction_context": ("任务说明", "采集指令、处理规则与任务上下文"),
    "quality_issue_editor": ("质检记录", "失误区间、严重程度、问题描述与证据"),
    "annotation_segment_editor": ("标注编辑器", "层级动作片段、动作元素、描述和起止时间"),
    "trajectory_viewer": ("轨迹信息", "关节、末端位姿与控制轨迹可视化"),
    "quality_result_viewer": ("质检信息", "质检结论、问题区间与规则版本"),
    "annotation_result_viewer": ("标注信息", "动作片段、标注版本与结构化结果"),
    "tag_viewer": ("标签信息", "场景、动作、设备与质量标签"),
    "high_low_editor": ("High/Low level 编辑器", "编辑 highlevel 与 lowlevel 两级动作描述"),
    "action_element_editor": ("动作元素编辑器", "编辑动作元素与动作描述"),
    "conclusion_selector": ("结论选择", "合格、不合格、操作失误三类业务结论"),
    "workbench_log": ("处理日志", "查看当前数据的处理、提交与退回日志"),
    "task_actions": ("任务操作", "提交、驳回与后续任务流转"),
    "submit_actions": ("提交操作栏", "只展示提交与暂离"),
    "reject_submit_actions": ("驳回与提交操作栏", "展示驳回、提交与暂离"),
}

WORKBENCH_COMPONENT_USAGE = {
    "basic_info": "全部工作台",
    "multi_view_video": "质检、标注、详情",
    "head_view_video": "标注、详情",
    "playback_timeline": "质检、标注",
    "instruction_context": "质检、标注",
    "quality_issue_editor": "质检、详情",
    "annotation_segment_editor": "标注、详情",
    "trajectory_viewer": "质检、标注、详情",
    "quality_result_viewer": "标注、详情",
    "annotation_result_viewer": "详情",
    "tag_viewer": "详情",
    "high_low_editor": "标注",
    "action_element_editor": "标注",
    "conclusion_selector": "质检、标注、详情",
    "workbench_log": "质检、标注、详情",
    "task_actions": "质检、标注、详情",
    "submit_actions": "质检、标注、详情",
    "reject_submit_actions": "质检、标注、详情",
}

WORKBENCH_COMPONENT_META = {
    "basic_info": ("基础信息", "context", "required"),
    "instruction_context": ("基础信息", "context", "optional"),
    "multi_view_video": ("视频区", "video", "exclusive"),
    "head_view_video": ("视频区", "video", "exclusive"),
    "playback_timeline": ("视频区", "timeline", "optional"),
    "trajectory_viewer": ("工作区", "tabs", "optional"),
    "quality_issue_editor": ("工作区", "tabs", "optional"),
    "quality_result_viewer": ("工作区", "tabs", "optional"),
    "annotation_segment_editor": ("工作区", "tabs", "optional"),
    "annotation_result_viewer": ("工作区", "tabs", "optional"),
    "tag_viewer": ("工作区", "tabs", "optional"),
    "workbench_log": ("工作区", "tabs", "optional"),
    "high_low_editor": ("处理表单", "editor", "exclusive"),
    "action_element_editor": ("处理表单", "editor", "exclusive"),
    "conclusion_selector": ("结论", "decision", "optional"),
    "submit_actions": ("操作栏", "actions", "exclusive"),
    "reject_submit_actions": ("操作栏", "actions", "exclusive"),
    "task_actions": ("操作栏", "actions", "legacy"),
}

PROCESSING_FLOWS = [
    {
        "id": "flow.annotation.e2e-review@2",
        "name": "端到端切分标注流程",
        "stage": "标注",
        "version": "v2",
        "input_contract": "quality_conclusion=合格/操作失误",
        "output_contract": "annotation_payload + annotation_version",
        "human_nodes": ["供应商抽验", "供应商复核", "供应商验收", "内部验收"],
        "preview_nodes": [
            {"name": "start", "kind": "start"},
            {"name": "端到端切分", "kind": "automatic"},
            {"name": "供应商抽验", "kind": "human"},
            {"name": "供应商复核", "kind": "human"},
            {"name": "供应商验收", "kind": "human"},
            {"name": "供应商抽样", "kind": "condition"},
            {"name": "内部验收", "kind": "human"},
            {"name": "end", "kind": "end"},
        ],
        "node_assignment_configs": {
            "供应商抽验": {"type": "supplier", "mode": "task_custom"},
            "供应商复核": {"type": "supplier", "mode": "inherit", "inherit_text": "继承供应商抽验节点"},
            "供应商验收": {"type": "supplier", "mode": "task_custom"},
            "内部验收": {"type": "user_group", "mode": "task_custom"},
        },
    },
    {
        "id": "flow.quality.multi-review@3",
        "name": "多级质检复核流程",
        "stage": "质检",
        "version": "v3",
        "input_contract": "完整 Recording 元数据",
        "output_contract": "quality_conclusion + quality_records",
        "human_nodes": ["抽检复核", "供应商复核", "申诉复核"],
    },
    {
        "id": "flow.quality.double-review@2",
        "name": "双轮人工质检流程",
        "stage": "质检",
        "version": "v2",
        "input_contract": "完整 Recording 元数据",
        "output_contract": "quality_conclusion + quality_records",
        "human_nodes": ["质检", "抽检"],
    },
    {
        "id": "flow.annotation.double-pass@2",
        "name": "双轮人工标注流程",
        "stage": "标注",
        "version": "v2",
        "input_contract": "quality_conclusion=合格/操作失误",
        "output_contract": "annotation_payload + annotation_version",
        "human_nodes": ["标注", "抽验"],
    },
    {
        "id": "flow.acceptance.final@1",
        "name": "数据验收流程",
        "stage": "验收",
        "version": "v1",
        "input_contract": "质检与标注流程输出",
        "output_contract": "acceptance_conclusion",
        "human_nodes": ["验收"],
    },
    {
        "id": "flow.quality.standard-training@1",
        "name": "标准训练数据自动质检流程",
        "stage": "质检",
        "version": "v1",
        "input_contract": "完整 Recording 元数据",
        "output_contract": "quality_conclusion + normalized_recording",
        "human_nodes": [],
    },
    {
        "id": "flow.quality.dagger@1",
        "name": "DAgger 数据自动质检流程",
        "stage": "质检",
        "version": "v1",
        "input_contract": "DAgger Recording 元数据",
        "output_contract": "quality_conclusion + statistics",
        "human_nodes": [],
    },
]

PROCESSING_RULES = [
    {
        "stage": "标注",
        "name": "端到端切分标注规则",
        "version": "v1",
        "annotation_method": "仅切分",
        "config": "略",
        "workbench": "语义标注工作台",
    },
    {"stage": "质检", "name": "通用质检规则", "version": "v3"},
    {"stage": "质检", "name": "自动化质检规则", "version": "v2"},
    {"stage": "质检", "name": "DAgger 质检规则", "version": "v1"},
    {"stage": "标注", "name": "通用动作标注规则", "version": "v3"},
]

USER_GROUPS = [
    {
        "id": "group.annotation",
        "name": "标注员用户组",
        "members": 10,
        "organizations": [
            {"name": "供应商 A", "members": 6},
            {"name": "光轮智能", "members": 4},
        ],
        "skills": "动作标注",
        "business_stages": ["标注"],
        "status": "enabled",
    },
    {
        "id": "group.annotation-sampling",
        "name": "标注抽验员用户组",
        "members": 20,
        "organizations": [
            {"name": "平台自有", "members": 12},
            {"name": "光轮智能", "members": 8},
        ],
        "skills": "标注抽验",
        "business_stages": ["标注"],
        "status": "enabled",
    },
    {
        "id": "group.experimental-annotation",
        "name": "新规实验标注员用户组",
        "members": 8,
        "organizations": [{"name": "联合项目组", "members": 8}],
        "skills": "新规则实验标注",
        "business_stages": ["标注"],
        "status": "disabled",
    },
    {
        "id": "group.quality-review",
        "name": "质检复核用户组",
        "members": 12,
        "organizations": [
            {"name": "光轮智能", "members": 8},
            {"name": "平台自有", "members": 4},
        ],
        "skills": "质检与申诉复核",
        "business_stages": ["质检"],
        "status": "enabled",
    },
    {
        "id": "group.acceptance",
        "name": "内部验收用户组",
        "members": 6,
        "organizations": [{"name": "平台自有", "members": 6}],
        "skills": "交付验收",
        "business_stages": ["质检", "标注"],
        "status": "enabled",
    },
    {
        "id": "group.e2e-split-acceptance",
        "name": "验收-端到端切分标注",
        "members": 6,
        "organizations": [{"name": "平台自有", "members": 6}],
        "skills": "端到端切分标注验收",
        "business_stages": ["标注"],
        "status": "enabled",
    },
]

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
        "description": "面向质检节点的多视角视频与质检问题处理工作台。",
        "type": "质检",
        "regions": ["context", "video", "tabs", "decision", "actions"],
        "components": [
            "basic_info",
            "instruction_context",
            "multi_view_video",
            "playback_timeline",
            "trajectory_viewer",
            "quality_issue_editor",
            "conclusion_selector",
            "workbench_log",
            "reject_submit_actions",
        ],
        "actions": ["submit", "reject"],
        "preview": "/data/workbench-management/preview/quality?task=WB-2026-0718-QC",
        "status": "published",
        "frozen": True,
    },
    {
        "id": "wb.action-annotation@4.1",
        "name": "动作标注工作台",
        "description": "面向动作元素标注的分段、动作描述与提交工作台。",
        "type": "标注",
        "annotation_kind": "action",
        "regions": ["context", "video", "tabs", "decision", "actions"],
        "components": [
            "basic_info",
            "instruction_context",
            "multi_view_video",
            "playback_timeline",
            "trajectory_viewer",
            "quality_result_viewer",
            "annotation_segment_editor",
            "action_element_editor",
            "conclusion_selector",
            "workbench_log",
            "reject_submit_actions",
        ],
        "actions": ["submit", "reject"],
        "preview": "/data/workbench-management/preview/annotation?task=WB-2026-0922-LB&rule=通用动作标注规则%20v1%EF%BC%88动作标注%20A%2FB%2FC%2FD%2FZ%EF%BC%89",
        "status": "published",
        "frozen": True,
    },
    {
        "id": "wb.semantic-annotation@1.0",
        "name": "语义标注工作台",
        "description": "面向语义标注 E/F/G 的低高层级语义编辑工作台。",
        "type": "标注",
        "annotation_kind": "semantic",
        "regions": ["context", "video", "tabs", "decision", "actions"],
        "components": [
            "basic_info",
            "instruction_context",
            "multi_view_video",
            "playback_timeline",
            "trajectory_viewer",
            "quality_result_viewer",
            "annotation_segment_editor",
            "high_low_editor",
            "conclusion_selector",
            "workbench_log",
            "reject_submit_actions",
        ],
        "actions": ["submit", "reject"],
        "preview": "/data/workbench-management/preview/annotation?task=WB-2026-0922-LB&rule=精细动作标注规则%20v2%EF%BC%88语义标注%20E%2FF%2FG%EF%BC%89",
        "status": "published",
        "frozen": True,
    },
    {
        "id": "wb.data-detail@1.0",
        "name": "详情工作台",
        "description": "用于验收节点查看处理结果与数据详情的工作台。",
        "type": "详情",
        "regions": ["video", "tabs", "decision", "actions"],
        "components": [
            "basic_info",
            "multi_view_video",
            "trajectory_viewer",
            "quality_result_viewer",
            "annotation_result_viewer",
            "tag_viewer",
            "conclusion_selector",
            "workbench_log",
            "submit_actions",
        ],
        "actions": ["submit", "reject"],
        "preview": "/data/workbench-management/preview/detail?task=WB-2026-0922-AC",
        "status": "published",
        "frozen": True,
    },
]
WORKBENCH_SCHEMAS.sort(
    key=lambda item: item["id"] != "wb.semantic-annotation@1.0"
)

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
        "priority": "P0",
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
        "priority": "P1",
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
        "priority": "P1",
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
        "priority": "P2",
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
        "priority": "P0",
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
        "collection_mode": "import",
        "name": "供应商 Batch-12 导入",
        "project": "PRJ-MOZ2-PRE-03",
        "input": "s3://vendor/batch-12 · LeRobot v2",
        "output": "导入报告 · 失败 18 条",
        "pipeline": "—",
        "snapshot": "—",
        "progress": 96,
        "collection_progress": {"done": 982, "total": 1024},
        "priority": "P1",
        "created": "2026-07-22 14:06",
        "due": "2026-07-29",
        "operator": "供应商 A",
        "creator": "Lance Li",
        "status": "running",
    },
    {
        "id": "20455",
        "type": "data_processing_task",
        "type_name": "数据处理 · 标注",
        "name": "端到端切分标注",
        "project": "PRJ-MOZ2-PRE-03",
        "input": "持续筛选命中的 Recording",
        "output": "Annotation Version",
        "pipeline": "flow.annotation.e2e-review@2",
        "snapshot": "—",
        "progress": 35,
        "priority": "P0",
        "created": "2026-08-03 10:00",
        "due": "—",
        "stage_progress": [
            {"label": "标注", "done": 420, "total": 1200},
        ],
        "enabled": True,
        "runtime_status": "正常",
        "filter_summary": "所属项目=预训练采集；采集任务=20197；质检结论=合格/操作失误",
        "filter_rules": [
            ("所属项目", "等于", "预训练采集"),
            ("采集任务", "等于", "20197"),
            ("质检结论", "等于", "合格,操作失误"),
        ],
        "flow_bindings": [
            ("标注", "端到端切分标注流程", "v2", "端到端切分标注规则"),
        ],
        "assignments": {
            "标注": {
                "供应商抽验": [
                    {"type": "supplier", "target": "供应商 A", "percent": 50},
                    {"type": "supplier", "target": "光轮智能", "percent": 50},
                ],
                "供应商复核": [],
                "内部验收": [
                    {"type": "user_group", "target": "验收-端到端切分标注", "percent": 100},
                ],
            },
        },
        "input_count": 1200,
        "processed_count": 420,
        "backlog_count": 780,
        "creator": "joanna.qiao",
        "status": "running",
    },
    {
        "id": "20454",
        "type": "data_processing_task",
        "type_name": "数据处理 · 标准化",
        "name": "厨房数据标准化处理",
        "project": "PRJ-MOZ1-SFT-07",
        "input": "1,206 Recording",
        "output": "842 Episode + 新快照",
        "pipeline": "pv.capture-to-dataset@7",
        "snapshot": "snap-moz1-0718-r3",
        "progress": 72,
        "priority": "P0",
        "created": "2026-07-24 09:42",
        "due": "2026-08-02",
        "stage_progress": [
            {"label": "质检", "done": 842, "total": 1206},
            {"label": "标注", "done": 488, "total": 842},
            {"label": "验收", "done": 240, "total": 842},
        ],
        "enabled": True,
        "runtime_status": "积压",
        "filter_summary": "所属项目=demo 项目；数据来源=采集；来源任务=COL-2026-0718",
        "filter_rules": [
            ("所属项目", "demo 项目"),
            ("数据来源", "采集"),
            ("来源任务 ID", "COL-2026-0718"),
        ],
        "flow_bindings": [
            ("质检", "多级质检复核流程", "v3"),
            ("标注", "端到端切分标注流程", "v2"),
            ("验收", "数据验收流程", "v1"),
        ],
        "input_count": 1206,
        "processed_count": 842,
        "backlog_count": 364,
        "creator": "joanna.qiao",
        "status": "running",
    },
    {
        "id": "20453",
        "type": "data_processing_task",
        "type_name": "数据处理 · 标注",
        "name": "家居动作分段标注",
        "project": "PRJ-MOZ1-SFT-07",
        "input": "842 Episode",
        "output": "Annotation Version",
        "pipeline": "pv.capture-to-dataset@7",
        "snapshot": "snap-moz1-episodes-r2",
        "progress": 58,
        "priority": "P0",
        "created": "2026-07-25 16:20",
        "due": "2026-08-05",
        "stage_progress": [
            {"label": "质检", "done": 842, "total": 842},
            {"label": "标注", "done": 488, "total": 842},
            {"label": "验收", "done": 320, "total": 842},
        ],
        "enabled": True,
        "runtime_status": "正常",
        "filter_summary": "所属项目=demo 项目；质检结论=合格/操作失误",
        "filter_rules": [
            ("所属项目", "demo 项目"),
            ("质检结论", "合格、操作失误"),
        ],
        "flow_bindings": [
            ("标注", "双轮人工标注流程", "v2"),
            ("验收", "数据验收流程", "v1"),
        ],
        "input_count": 842,
        "processed_count": 488,
        "backlog_count": 354,
        "creator": "joanna.qiao",
        "status": "running",
    },
    {
        "id": "20452",
        "type": "data_processing_task",
        "type_name": "数据处理 · 数据集构建",
        "name": "通用评测集季度构建",
        "project": "PRJ-EVAL-GEN-02",
        "input": "Snapshot snap-eval-q3-input",
        "output": "dataset.eval-general@2026q3",
        "pipeline": "pv.vendor-import@3",
        "snapshot": "snap-eval-q3-input",
        "progress": 100,
        "priority": "P1",
        "created": "2026-07-23 11:08",
        "due": "2026-07-30",
        "stage_progress": [
            {"label": "质检", "done": 488, "total": 488},
            {"label": "标注", "done": 488, "total": 488},
            {"label": "验收", "done": 452, "total": 488},
        ],
        "enabled": False,
        "runtime_status": "已关闭",
        "filter_summary": "所属项目=宁德项目；数据来源=采集/导入；标注状态=已标注",
        "filter_rules": [
            ("所属项目", "宁德项目"),
            ("数据来源", "采集、导入"),
            ("标注状态", "已标注"),
        ],
        "flow_bindings": [
            ("质检", "标准训练数据自动质检流程", "v1"),
            ("验收", "数据验收流程", "v1"),
        ],
        "input_count": 488,
        "processed_count": 452,
        "backlog_count": 0,
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
    {
        "id": "snap-moz1-0709-r1",
        "project": "PRJ-MOZ1-SFT-07",
        "members": "96 Recording",
        "checksum": "sha256:0f42…bb17",
        "created_by": "COL-2026-0715",
        "immutable": True,
    },
]

PIPELINE_RUNS = [
    {
        "id": "run-moz1-0921",
        "project": "PRJ-MOZ1-SFT-07",
        "business_task": "20454",
        "pipeline_version": "pv.capture-to-dataset@7",
        "input_snapshot": "snap-moz1-0718-r3",
        "input_members": "1,206 Recording",
        "recording_ids": ["4057808", "4057761", "4057711", "4057669"],
        "current_node": "Episode 切分",
        "node_progress": "3 / 5",
        "status": "running",
        "idempotency_key": "idem:0c92…cf18",
        "started": "2026-07-26 09:42",
        "ended": "—",
        "duration": "运行中 04:18:32",
    },
    {
        "id": "run-moz1-0922",
        "project": "PRJ-MOZ1-SFT-07",
        "business_task": "20453",
        "pipeline_version": "pv.capture-to-dataset@7",
        "input_snapshot": "snap-moz1-episodes-r2",
        "input_members": "842 Episode",
        "recording_ids": ["4057808", "4057761", "4057711", "4057669"],
        "current_node": "动作标注",
        "node_progress": "4 / 5",
        "status": "running",
        "idempotency_key": "idem:812e…31ad",
        "started": "2026-07-25 16:20",
        "ended": "—",
        "duration": "运行中 21:40:18",
    },
    {
        "id": "run-eval-0314",
        "project": "PRJ-EVAL-GEN-02",
        "business_task": "20452",
        "pipeline_version": "pv.vendor-import@3",
        "input_snapshot": "snap-eval-q3-input",
        "input_members": "1,238 Episode",
        "recording_ids": ["5088112", "5088076", "5088029"],
        "current_node": "数据集构建",
        "node_progress": "3 / 3",
        "status": "succeeded",
        "idempotency_key": "idem:aa02…908c",
        "started": "2026-07-23 11:08",
        "ended": "2026-07-23 11:50",
        "duration": "00:42:16",
    },
    {
        "id": "run-moz1-0908",
        "project": "PRJ-MOZ1-SFT-07",
        "business_task": "20454",
        "pipeline_version": "pv.capture-to-dataset@7",
        "input_snapshot": "snap-moz1-0709-r1",
        "input_members": "96 Recording",
        "recording_ids": ["4057422", "4057419"],
        "current_node": "时间戳对齐",
        "node_progress": "2 / 5",
        "status": "failed",
        "idempotency_key": "idem:7b31…aa62",
        "started": "2026-07-22 18:06",
        "ended": "2026-07-22 18:14",
        "duration": "00:08:27",
        "error": "传感器时间戳缺失，自动重试 2 次后失败",
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
    {
        "id": "nr-0908-align-002",
        "pipeline_run": "run-moz1-0908",
        "node": "时间戳对齐",
        "node_type": "operator",
        "input_snapshot": "snap-moz1-0709-r1",
        "executor_version": "op.timestamp-align@2.1.0",
        "attempt": 3,
        "output": "—",
        "status": "failed",
        "error": "missing timestamp: left_arm_camera",
    },
]

HUMAN_TASKS = [
    {
        "id": "ht-220981",
        "task_type": "动作分段标注",
        "business_task": "20453",
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
        "business_task": "20453",
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
        "business_task": "20453",
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
    "20455": [
        {
            "id": "recording_e2e_001",
            "collection_id": "20197",
            "device": "MOZ2-20197-01",
            "node": "供应商抽验",
            "collection": "成功",
            "quality": "合格",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "标注：供应商 A",
            "workbench_task": "WB-E2E-SUPPLIER-A",
        },
        {
            "id": "recording_e2e_002",
            "collection_id": "20197",
            "device": "MOZ2-20197-02",
            "node": "供应商抽验",
            "collection": "成功",
            "quality": "操作失误",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "标注：光轮智能",
            "workbench_task": "WB-E2E-GUAN",
        },
        {
            "id": "recording_e2e_003",
            "collection_id": "20197",
            "device": "MOZ2-20197-03",
            "node": "供应商抽验",
            "collection": "成功",
            "quality": "合格",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "标注：供应商 A",
            "workbench_task": "WB-E2E-SUPPLIER-A",
        },
        {
            "id": "recording_e2e_004",
            "collection_id": "20197",
            "device": "MOZ2-20197-04",
            "node": "供应商复核",
            "collection": "成功",
            "quality": "合格",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "标注：供应商 A",
            "workbench_task": "WB-E2E-REVIEW",
        },
        {
            "id": "recording_e2e_005",
            "collection_id": "20197",
            "device": "MOZ2-20197-05",
            "node": "供应商复核",
            "collection": "成功",
            "quality": "操作失误",
            "annotation": "未标注",
            "acceptance": "待验收",
            "operators": "标注：光轮智能",
            "workbench_task": "WB-E2E-REVIEW",
        },
        {
            "id": "recording_e2e_006",
            "collection_id": "20197",
            "device": "MOZ2-20197-06",
            "node": "供应商验收",
            "collection": "成功",
            "quality": "合格",
            "annotation": "已标注",
            "acceptance": "进行中",
            "operators": "标注：光轮智能",
            "workbench_task": "WB-E2E-REVIEW",
        },
        {
            "id": "recording_e2e_007",
            "collection_id": "20197",
            "device": "MOZ2-20197-07",
            "node": "内部验收",
            "collection": "成功",
            "quality": "合格",
            "annotation": "已标注",
            "acceptance": "进行中",
            "operators": "验收：joanna.qiao",
            "workbench_task": "WB-E2E-ACCEPTANCE",
        },
        {
            "id": "recording_e2e_008",
            "collection_id": "20197",
            "device": "MOZ2-20197-08",
            "node": "内部验收",
            "collection": "成功",
            "quality": "操作失误",
            "annotation": "已标注",
            "acceptance": "进行中",
            "operators": "验收：joanna.qiao",
            "workbench_task": "WB-E2E-ACCEPTANCE",
        },
        {
            "id": "recording_e2e_009",
            "collection_id": "20197",
            "device": "MOZ2-20197-09",
            "node": "内部验收",
            "collection": "成功",
            "quality": "合格",
            "annotation": "已标注",
            "acceptance": "已完成",
            "operators": "验收：joanna.qiao",
            "workbench_task": "WB-E2E-ACCEPTANCE",
        },
    ],
    "20454": [
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
    "20453": [
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
    "20452": [
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
        "task": "20454",
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
        "task": "20453",
        "project": "demo 项目",
        "count": 140,
        "status": "已分配未处理",
        "supplier": "质检复核用户组",
        "operator": "包媛桐",
        "stalled": "18 小时",
        "priority": "P1",
    },
    {
        "id": "ALLOC-LB-0314",
        "stage": "标注",
        "task": "20453",
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
        "task": "20454",
        "project": "预训练采集",
        "count": 186,
        "status": "已分配未处理",
        "supplier": "标注员用户组",
        "operator": "供应商 A-017",
        "stalled": "14 小时",
        "priority": "P1",
    },
    {
        "id": "ALLOC-AC-0112",
        "stage": "验收",
        "task": "20452",
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
        "task": "20453",
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
        "source_tasks": ["COL-2026-0718", "COL-2026-0719", "IMP-2026-0042"],
        "processing_task": "20454",
        "workflow": "厨房数据质检流程 v3",
        "stage": "质检",
        "node": "供应商复核",
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
        "source_tasks": ["COL-2026-0719", "COL-2026-0718"],
        "processing_task": "20453",
        "workflow": "家居动作标注流程 v2",
        "stage": "标注",
        "node": "标注抽验",
        "input_rate": 96,
        "throughput": 72,
        "backlog": 140,
        "supplier": "标注抽验员用户组",
        "operator": "供应商 A-017",
        "stalled": "18 小时",
        "priority": "P1",
    },
    {
        "id": "STREAM-0042-LB",
        "project": "预训练采集",
        "source_task": "IMP-2026-0042",
        "processing_task": "20451",
        "workflow": "三方数据导入质检流程 v4",
        "stage": "标注",
        "node": "供应商标注",
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
        "project": "demo 项目",
        "source_task": "COL-2026-0718",
        "processing_task": "20453",
        "workflow": "家居动作标注流程 v2",
        "stage": "验收",
        "node": "内部验收",
        "input_rate": 84,
        "throughput": 56,
        "backlog": 86,
        "supplier": "内部验收用户组",
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
        "reason": "未命中任何启用中的处理任务筛选条件",
        "operator": "刘素粉",
    },
    {
        "id": "POOL-IMP-0048",
        "project": "预训练采集",
        "source": "导入",
        "source_task": "IMP-2026-0048",
        "count": 388,
        "created": "2026-07-26 19:10",
        "reason": "未命中任何启用中的处理任务筛选条件",
        "operator": "数据导入服务",
    },
    {
        "id": "POOL-COL-0720",
        "project": "demo 项目",
        "source": "采集",
        "source_task": "COL-2026-0720",
        "count": 254,
        "created": "2026-07-27 10:06",
        "reason": "已有关联任务关闭，当前无有效订阅",
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
    visible_page_keys = {
        key for key, spec in PAGE_SPECS.items()
        if not spec.get("hidden") and not spec.get("hide_from_nav")
    }
    if set(all_page_keys) != visible_page_keys:
        errors.append("navigation and page registry are inconsistent")
    paths = [spec["path"] for spec in PAGE_SPECS.values()]
    if len(paths) != len(set(paths)):
        errors.append("page paths must be unique")

    flow_catalog = {
        (flow["stage"], flow["name"], flow["version"])
        for flow in PROCESSING_FLOWS
    }
    user_group_ids = [group["id"] for group in USER_GROUPS]
    if len(user_group_ids) != len(set(user_group_ids)):
        errors.append("user group identifiers must be unique")
    for task in BUSINESS_TASKS:
        if task["type"] == "data_collection_task" and task.get("pipeline") != "—":
            errors.append(f"{task['id']} must write to the data lake without a direct processing binding")
        if task["type"] != "data_processing_task":
            continue
        if not task.get("filter_rules"):
            errors.append(f"{task['id']} must define persistent data-lake filters")
        if not task.get("flow_bindings"):
            errors.append(f"{task['id']} must bind at least one versioned processing flow")
        for binding in task.get("flow_bindings", []):
            if tuple(binding[:3]) not in flow_catalog:
                errors.append(f"{task['id']} references an unknown processing flow: {binding}")

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
        "enabled": "green",
        "disabled": "orange",
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
        "enabled": "启用",
        "disabled": "停用",
        "frozen": "已冻结",
        "published": "已发布",
        "succeeded": "已完成",
        "failed": "失败",
    }.get(normalized, value)
    return f'<span class="dpr-state {tone}">{_e(label)}</span>'


def _intro(
    title,
    subtitle,
    eyebrow="DATA PIPELINE",
    action_html="",
    inline_action=False,
):
    eyebrow_html = f'<div class="dpr-eyebrow">{_e(eyebrow)}</div>' if eyebrow else ""
    if inline_action:
        return f"""
        <div class="dpr-intro dpr-intro-inline-action">
          <div>
            {eyebrow_html}
            <div class="dpr-intro-title-row">
              <h1>{_e(title)}</h1>
              <div class="dpr-intro-actions">{action_html}</div>
            </div>
          </div>
        </div>
        """
    return f"""
    <div class="dpr-intro">
      <div>
        {eyebrow_html}
        <h1>{_e(title)}</h1>
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


def _priority_tag(value):
    legacy = {"P0": 9, "P1": 6, "P2": 3, "高": 9, "中": 6, "低": 3}
    try:
        normalized = legacy[str(value)] if str(value) in legacy else int(value)
    except (TypeError, ValueError):
        normalized = 3
    normalized = max(1, min(9, normalized))
    tone = "priority-low" if normalized <= 3 else ("priority-medium" if normalized <= 6 else "priority-high")
    return (
        f'<span class="dpr-priority wb-priority {_e(tone)}">'
        f'{_e(normalized)}</span>'
    )


def _table(
    headers,
    rows,
    empty="暂无数据",
    table_id="",
    row_attrs=None,
    wrap_class="table-wrap q-table-scroll",
    table_class="ant-table",
):
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
    <div class="{_e(wrap_class)}">
      <table class="{_e(table_class)}"{table_id_attr}>
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
        _intro("项目管理", "管理项目成员、数据范围、交付目标、进度与预算。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 新增项目\');return false;">新增项目</a>')
        + _metrics([("进行中项目", "3", "跨 2 个机器人构型"), ("本月交付目标", "21,200 EP", "已完成 13,764 EP"), ("处理异常", "2", "均已关联责任任务"), ("预算使用", "68%", "按项目统一归集")])
        + _section("项目列表", _table(["项目", "负责人", "数据范围", "交付目标", "进度", "风险 / 截止", "操作"], rows))
    )


def _task_filter_bar(fields):
    controls = []
    for field in fields:
        label, control_type, options = field[:3]
        placeholder = field[3] if len(field) > 3 else f"请输入{label}"
        if control_type == "input":
            controls.append(
                f'<div class="q-field"><label>{_e(label)}</label>'
                f'<input placeholder="{_e(placeholder)}"></div>'
            )
        else:
            option_html = "".join(f"<option>{_e(option)}</option>" for option in options)
            controls.append(
                f'<div class="q-field"><label>{_e(label)}</label><select>{option_html}</select></div>'
            )
    return f"""
    <div class="q-filters rule-filter-panel dpr-task-filters">
      <div class="q-filter-row">
        {''.join(controls)}
        <div class="q-actions">
          <button type="button" class="btn" onclick="resetFilters(this)">清空</button>
          <button type="button" class="btn btn-primary" onclick="queryFilters(this)">查询</button>
        </div>
      </div>
    </div>
    """


def render_collection_tasks():
    tab_specs = [
        ("instruction", "指令采集"),
        ("free", "自由采集"),
        ("dagger", "DAgger 采集"),
        ("import", "数据导入"),
    ]
    tasks = [
        item for item in BUSINESS_TASKS
        if item["type"] in ("data_collection_task", "data_import_task")
    ]
    counts = {
        mode: sum(1 for item in tasks if item["collection_mode"] == mode)
        for mode, _ in tab_specs
    }
    tabs = "".join(
        f'<span class="det-tab dpr-collection-tab{" active" if index == 0 else ""}" '
        f'role="tab" tabindex="0" '
        f'data-task-mode="{_e(mode)}" onclick="dprSwitchCollectionTab(this, \'{_e(mode)}\')">'
        f'{_e(label)} <b>{counts[mode]}</b></span>'
        for index, (mode, label) in enumerate(tab_specs)
    )
    rows = []
    row_attrs = []
    for item in tasks:
        detail_path = (
            f'/data/recordings?source=import&task={_e(item["id"])}'
            if item["type"] == "data_import_task"
            else f'/data/tasks/{_e(item["id"])}'
        )
        project_label = TASK_PROJECT_LABELS[item["project"]]
        drawer_data = (
            f'data-task-id="{_e(item["id"])}" '
            f'data-task-name="{_e(item["name"])}" '
            f'data-collection-type="{_e(item["type_name"])}" '
            f'data-project="{_e(project_label)}" '
            f'data-priority="{_e(item["priority"])}"'
        )
        rows.append(
            [
                f'<code>{_e(item["id"])}</code>',
                f'<a class="dpr-task-name" href="{detail_path}"><b>{_e(item["name"])}</b></a>',
                _record_tag(item["type_name"]),
                (
                    '<div class="dpr-task-progress-line dpr-collection-progress-line">'
                    f'<i class="teal" style="width:{item["progress"]}%"></i>'
                    f'<b>{item["collection_progress"]["done"]:,} / '
                    f'{item["collection_progress"]["total"]:,} · '
                    f'{item["progress"]}%</b></div>'
                ),
                _priority_tag(item["priority"]),
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
            ("类型", "select", ["全部类型", "指令采集", "自由采集", "DAgger 采集", "数据导入"]),
            ("操作人", "select", ["全部操作人", "刘素粉", "王一帆", "采集团队 B", "供应商 A", "DAgger 小组"]),
        ]
    )
    table = _table(
        ["任务 ID", "名称", "类型", "进度", "优先级", "创建人", "创建时间", "操作"],
        rows,
        table_id="dpr-collection-task-table",
        row_attrs=row_attrs,
    )
    new_task_button = """
    <button type="button" class="btn btn-primary" id="newCollectionTaskButton"
      onclick="dprOpenCollectionTaskDrawer('new')">新增采集任务</button>
    """
    body = f"""
    <div class="det-tabs dpr-allocation-tabs dpr-collection-tabs" role="tablist">
      {tabs}
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
            <option>数据导入</option>
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
            <option>P1</option>
            <option>P0</option>
            <option>P2</option>
          </select>
        </div>
        <div class="dpr-source-task-note">
          采集结果统一写入数据湖。处理任务将根据数据来源、来源任务 ID、项目及质量状态等条件持续筛选数据。
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn btn-primary" id="collectionTaskDrawerSubmit"
          onclick="dprSubmitCollectionTask()">创建</button>
      </div>
    </div>
    <script>
    var DPR_COLLECTION_ACTIVE_MODE = 'instruction';
    function dprSwitchCollectionTab(button, taskMode) {{
      DPR_COLLECTION_ACTIVE_MODE = taskMode;
      document.querySelectorAll('.dpr-collection-tab').forEach(function(tab) {{
        tab.classList.toggle('active', tab === button);
      }});
      document.querySelectorAll('#dpr-collection-task-table tbody tr').forEach(function(row) {{
        row.style.display = row.dataset.taskMode === taskMode ? '' : 'none';
      }});
      document.getElementById('newCollectionTaskButton').textContent =
        taskMode === 'import' ? '新增导入任务' : '新增采集任务';
    }}
    function dprOpenCollectionTaskDrawer(mode, trigger) {{
      var typeByMode = {{
        instruction: '指令采集',
        free: '自由采集',
        dagger: 'DAgger 采集',
        import: '数据导入'
      }};
      var data = trigger ? trigger.dataset : {{
        taskName: '',
        collectionType: typeByMode[DPR_COLLECTION_ACTIVE_MODE] || '指令采集',
        project: '预训练采集',
        priority: 'P1'
      }};
      var drawer = document.getElementById('drawerCollectionTaskForm');
      var isDetail = mode === 'detail';
      var isImport = data.collectionType === '数据导入';
      drawer.dataset.mode = mode;
      document.getElementById('collectionTaskDrawerTitle').textContent =
        mode === 'new'
          ? (isImport ? '新建数据导入任务' : '新建采集任务')
          : (isDetail
            ? (isImport ? '数据导入任务详情' : '采集任务详情')
            : (isImport ? '编辑数据导入任务' : '编辑采集任务'));
      document.getElementById('collectionTaskName').value = data.taskName || '';
      document.getElementById('collectionTaskType').value = data.collectionType || '指令采集';
      document.getElementById('collectionTaskProject').value = data.project || '预训练采集';
      document.getElementById('collectionTaskPriority').value = data.priority || 'P1';
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
        "管理数据采集与导入任务，支持指令采集、自由采集、DAgger 采集和数据导入。",
        "",
        new_task_button,
        inline_action=True,
    ) + body


def _render_processing_tasks_legacy():
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
    tasks = sorted(
        (item for item in BUSINESS_TASKS if item["type"] == "data_processing_task"),
        key=lambda item: item["name"] != "端到端切分标注",
    )
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
            f'data-task-category="{_e(item.get("task_category", "formal"))}" '
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
                _priority_tag(item["priority"]),
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
        onclick="dprOpenProcessingTaskDrawer('new')">新增处理任务</button>
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
      if (mode === 'new') DPR_ALLOCATION_SETTING = {mode:'proportional', quantitativeType:'time', expectedTotal:''};
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


def render_processing_tasks():
    """Render the v2 continuous processing-task model.

    A processing task subscribes to matching lake data and binds one or more
    independently versioned flows. Human assignment intentionally does not
    live here; it belongs to the human-node configuration and its user groups.
    """
    flow_catalog_json = json.dumps(
        PROCESSING_FLOWS,
        ensure_ascii=False,
    ).replace("</", "<\\/")
    rule_catalog_json = json.dumps(
        PROCESSING_RULES,
        ensure_ascii=False,
    ).replace("</", "<\\/")
    tasks = sorted(
        (item for item in BUSINESS_TASKS if item["type"] == "data_processing_task"),
        key=lambda item: item["name"] != "端到端切分标注",
    )
    rows = []
    for item in tasks:
        detail_path = f'/data/tasks/{_e(item["id"])}'
        project_label = TASK_PROJECT_LABELS[item["project"]]
        filter_payload = json.dumps(item["filter_rules"], ensure_ascii=False)
        visible_flow_bindings = [binding for binding in item["flow_bindings"] if binding[0] != "验收"]
        flow_payload = json.dumps(visible_flow_bindings, ensure_ascii=False)
        assignment_payload = json.dumps(item.get("assignments", {}), ensure_ascii=False)
        flowed_count = item.get("input_count", 0)
        flowed_hours = item.get("input_duration_hours", 0)
        drawer_data = (
            f'data-task-id="{_e(item["id"])}" '
            f'data-task-name="{_e(item["name"])}" '
            f'data-project="{_e(project_label)}" '
            f'data-task-category="{_e(item.get("task_category", "formal"))}" '
            f'data-priority="{_e(item["priority"])}" '
            f'data-enabled="{"true" if item["enabled"] else "false"}" '
            f'data-expected-mode="{_e(item.get("expected_task_mode", "continuous"))}" '
            f'data-expected-value="{_e(item.get("expected_task_value", ""))}" '
            f'data-flowed-count="{_e(flowed_count)}" '
            f'data-flowed-hours="{_e(flowed_hours)}" '
            f'data-filters="{_e(filter_payload)}" '
            f'data-flows="{_e(flow_payload)}" '
            f'data-assignments="{_e(assignment_payload)}"'
        )
        progress_by_stage = {
            progress["label"]: progress
            for progress in item["stage_progress"]
        }
        stage_tones = {"质检": "blue", "标注": "teal"}
        flow_bindings = "".join(
            (
                f'<div class="dpr-flow-binding-chip" data-progress-stage="{_e(stage)}">'
                f'<span>{_e(stage)}</span><div class="dpr-flow-binding-name">'
                f'<b>{_e(flow)}</b><code>{_e(_version)}</code></div>'
                f'<div class="dpr-task-progress-line dpr-flow-progress-line">'
                f'<i class="{_e(stage_tones[stage])}" '
                f'style="width:{round(progress_by_stage[stage]["done"] / progress_by_stage[stage]["total"] * 100) if progress_by_stage[stage]["total"] else 0}%"></i>'
                f'<b>{progress_by_stage[stage]["done"]:,} / '
                f'{progress_by_stage[stage]["total"]:,} · '
                f'{round(progress_by_stage[stage]["done"] / progress_by_stage[stage]["total"] * 100) if progress_by_stage[stage]["total"] else 0}%</b>'
                f'</div></div>'
            )
            for stage, flow, _version, *_ in visible_flow_bindings
        )
        status_control = (
            f'<label class="dpr-task-enable" title="关闭后停止接收新数据，已进入流程的数据继续处理">'
            f'<input type="checkbox" {"checked" if item["enabled"] else ""} '
            f'aria-label="切换任务 {_e(item["id"])} 状态" '
            f'onchange="dprToggleProcessingTask(this, \'{_e(item["id"])}\')">'
            f'<i></i></label>'
        )
        rows.append(
            [
                f'<code>{_e(item["id"])}</code>',
                f'<a class="dpr-task-name" href="{detail_path}"><b>{_e(item["name"])}</b></a>',
                _e(project_label),
                f'<div class="dpr-flow-binding-list">{flow_bindings}</div>',
                status_control,
                _priority_tag(item["priority"]),
                "非正式" if item.get("task_category") == "informal" else "正式",
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

    filters = _task_filter_bar(
        [
            ("任务 ID", "input", [], "请输入任务 ID，多个英文逗号隔开"),
            ("名称", "input", []),
            ("所属项目", "select", ["全部项目", *TASK_PROJECT_LABELS.values()]),
            (
                "处理流程",
                "select",
                ["全部流程", *[flow["name"] for flow in PROCESSING_FLOWS]],
            ),
            ("状态", "select", ["全部状态", "开启", "关闭"]),
            ("任务性质", "select", ["全部", "正式", "非正式"]),
            ("创建人", "input", []),
        ]
    )
    table = _table(
        [
            "任务 ID",
            "名称",
            "所属项目",
            "处理流程",
            "状态",
            "优先级",
            "任务性质",
            "创建人",
            "创建时间",
            "操作",
        ],
        rows,
        table_id="dpr-processing-task-table",
    )
    new_task_button = """
    <button type="button" class="btn btn-primary"
      onclick="dprOpenProcessingTaskDrawer('new')">新增处理任务</button>
    """
    body = f"""
    {filters}
    {table}
    <section class="dpr-processing-task-page" id="drawerProcessingTaskForm" data-mode="new" aria-hidden="true">
      <style>
        .dpr-processing-task-page{{font-size:13px}}.dpr-processing-task-page-foot{{display:flex;justify-content:flex-end;gap:10px;padding:14px 28px;border-top:1px solid #e2e8ea;background:#fff}}.dpr-filter-add-bottom{{margin-top:12px;padding:0;border:0;background:transparent;color:#149DAA;font-size:13px;cursor:pointer}}.dpr-filter-cols,.dpr-filter-row{{grid-template-columns:28px 170px 1fr 26px}}.dpr-filter-and{{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:4px;background:#e8f5f6;color:#147a83;font-size:12px;font-weight:650}}.dpr-flow-selector{{border:0;background:transparent}}.dpr-flow-config-card{{display:flex;flex-direction:column;gap:10px;margin:0 0 12px;padding:16px;border:1px solid #e2e9eb;border-radius:8px;background:#fff;font-size:13px}}.dpr-flow-config-card.active{{border-color:#69bdc4;background:#f4fbfb}}.dpr-flow-config-card.collapsed{{padding-bottom:13px}}.dpr-flow-config-card-head{{display:flex!important;flex-direction:column!important;align-items:stretch!important;gap:4px}}.dpr-flow-card-title-line{{display:flex;align-items:center;justify-content:space-between;gap:12px}}.dpr-flow-card-help{{color:#849298;font-size:12px}}.dpr-flow-config-card b{{font-size:13px;color:#30484f}}.dpr-flow-config-card span{{color:#849298;font-size:12px}}.dpr-flow-config-card label{{display:flex;flex-direction:column;gap:5px;color:#74848a;font-size:13px}}.dpr-flow-config-card select{{height:36px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;padding:0 9px;color:#344c54;font-size:13px}}.dpr-flow-config-card button{{padding:2px 0 0;border:0;background:transparent;color:#149DAA;text-align:left;font-size:13px;cursor:pointer}}.dpr-flow-toggle{{display:flex!important;flex-direction:row!important;align-items:center;gap:7px;white-space:nowrap;color:#74848a!important}}.dpr-flow-toggle input{{display:none}}.dpr-flow-toggle i{{position:relative;width:30px;height:17px;border-radius:10px;background:#cbd4d7;cursor:pointer}}.dpr-flow-toggle i:after{{content:"";position:absolute;left:2px;top:2px;width:13px;height:13px;border-radius:50%;background:#fff;transition:.15s}}.dpr-flow-toggle input:checked+i{{background:#149DAA}}.dpr-flow-toggle input:checked+i:after{{left:15px}}.dpr-flow-toggle em{{font-style:normal;font-size:12px}}.dpr-processing-task-form,.dpr-processing-task-form input,.dpr-processing-task-form select,.dpr-processing-task-form button{{font-size:13px}}.dpr-page-section-head p,.dpr-processing-basic-grid small,.dpr-processing-task-menu button i{{font-size:12px}}
      </style>
      <style>
        .dpr-processing-task-page .dpr-filter-cols,
        .dpr-processing-task-page .dpr-filter-row {{
          grid-template-columns: 28px 170px 110px minmax(160px, 1fr) 26px !important;
        }}
        .dpr-filter-multi {{ position:relative; }}
        .dpr-filter-multi summary {{ display:flex;align-items:center;height:34px;padding:0 28px 0 9px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#344c54;cursor:pointer;list-style:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }}
        .dpr-filter-multi summary::-webkit-details-marker {{ display:none; }}
        .dpr-filter-multi summary:after {{ content:'⌄';position:absolute;right:10px;color:#718188;font-size:16px; }}
        .dpr-filter-multi>div {{ position:absolute;z-index:4;top:39px;left:0;min-width:190px;padding:6px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;box-shadow:0 6px 16px rgba(37,61,69,.12); }}
        .dpr-filter-multi label {{ display:flex!important;flex-direction:row!important;align-items:center;gap:7px;padding:7px 8px;color:#405860!important;cursor:pointer; }}
        .dpr-filter-multi label:hover {{ background:#f2f8f8; }}
        .dpr-filter-multi input {{ width:auto!important;height:auto!important; }}
        .dpr-filter-datetime-range {{ display:grid;grid-template-columns:minmax(0,1fr) 16px minmax(0,1fr);align-items:center;gap:6px;height:34px; }}
        .dpr-filter-datetime-range input {{ width:100%;height:34px;box-sizing:border-box;border:1px solid #d8e0e3;border-radius:6px;padding:0 7px;color:#344c54;font-size:12px; }}
        .dpr-filter-datetime-range>span {{ color:#879399;text-align:center; }}
        .dpr-filter-people {{ position:relative;display:flex;align-items:center;min-height:34px;padding:3px 7px;box-sizing:border-box;border:1px solid #d8e0e3;border-radius:6px;background:#fff; }}
        .dpr-filter-people:focus-within {{ border-color:#149DAA;box-shadow:0 0 0 2px rgba(20,157,170,.12); }}
        .dpr-filter-people-picked {{ display:flex;align-items:center;gap:4px;flex-wrap:wrap; }}
        .dpr-filter-people-picked span {{ display:inline-flex;align-items:center;gap:5px;height:26px;padding:0 7px;border-radius:5px;background:#f1f3f5;color:#5e6870;font-size:12px;white-space:nowrap; }}
        .dpr-filter-people-picked button {{ padding:0!important;border:0!important;background:transparent!important;color:#929aa1!important;font-size:17px!important;line-height:1; }}
        .dpr-filter-people-search {{ flex:1;min-width:88px;height:26px!important;border:0!important;outline:0;padding:0 4px!important;background:#fff!important; }}
        .dpr-filter-people-results {{ position:absolute;z-index:4;top:39px;left:0;right:0;padding:5px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;box-shadow:0 6px 16px rgba(37,61,69,.12); }}
        .dpr-filter-people-results:empty {{ display:none; }}
        .dpr-filter-people-results button {{ display:block;width:100%;box-sizing:border-box;padding:9px 10px!important;border:0!important;border-radius:4px;background:#fff!important;color:#405860!important;font:inherit;font-size:13px!important;text-align:left;cursor:pointer; }}
        .dpr-filter-people-results button:hover {{ background:#f2f8f8!important;color:#147a83!important; }}
        .dpr-filter-people-results small {{ display:block;padding:7px 8px;color:#879399; }}
        .dpr-expected-task-value .dpr-expected-task-input {{ position:relative;display:flex;align-items:center; }}
        .dpr-expected-task-input input {{ padding-right:42px!important; }}
        .dpr-expected-task-input i {{ position:absolute;right:11px;color:#7f8e94;font-style:normal;font-size:12px;pointer-events:none; }}
        .dpr-flow-selector {{ position:sticky;z-index:5;top:-30px;align-self:start;background:#f6f8f9; }}
        .dpr-flow-node-assignments {{ overflow:visible; }}
        #processingTaskFlowPreview {{ position:sticky;z-index:6;top:-30px;margin-bottom:4px;padding-bottom:10px;background:#fff;box-shadow:0 14px 18px -17px rgba(37,73,87,.45); }}
        .dpr-flow-preview-section {{ margin:0;border:1px solid #dce7ea;border-radius:9px;background:#fff;overflow:hidden; }}
        .dpr-flow-preview-head {{ display:flex;align-items:center;justify-content:space-between;padding:11px 14px;border-bottom:1px solid #e7eef0;background:#f3f8fa; }}
        .dpr-flow-preview-head b {{ color:#30484f;font-size:13px; }}
        .dpr-flow-preview-head span {{ color:#849298;font-size:11px; }}
        .dpr-flow-preview-canvas {{ overflow-x:auto;padding:17px 16px 20px;background:#fbfdfe;background-image:radial-gradient(#dfe8eb 1px,transparent 1px);background-size:16px 16px; }}
        .dpr-flow-preview-track {{ display:flex;align-items:center;min-width:max-content;gap:0; }}
        .dpr-flow-preview-node {{ position:relative;display:flex;flex-direction:column;justify-content:center;width:132px;min-height:64px;box-sizing:border-box;padding:10px 11px 9px;border:1px solid #d7e3e6;border-left:4px solid #18a8d1;border-radius:8px;background:#fff;box-shadow:0 2px 6px rgba(37,73,87,.08);text-align:left; }}
        .dpr-flow-preview-node:focus {{ outline:2px solid rgba(20,157,170,.25);outline-offset:2px; }}
        .dpr-flow-preview-node.human {{ border-left-color:#48a86b;cursor:pointer; }}
        .dpr-flow-preview-node.human:hover,.dpr-flow-preview-node.human.active {{ background:#f4fbf6;box-shadow:0 0 0 2px rgba(72,168,107,.14),0 4px 10px rgba(37,73,87,.12); }}
        .dpr-flow-preview-node.condition {{ border-left-color:#ee9b32;background:#fffaf3; }}
        .dpr-flow-preview-node.start {{ border-left-color:#16a39a; }}
        .dpr-flow-preview-node.end {{ border-left-color:#756fd0; }}
        .dpr-flow-preview-node i {{ display:inline-flex;align-items:center;justify-content:center;width:19px;height:19px;margin-bottom:5px;border-radius:6px;background:#eaf7fb;color:#168fb2;font-style:normal;font-size:11px; }}
        .dpr-flow-preview-node.human i {{ background:#eaf7ee;color:#348d56; }}
        .dpr-flow-preview-node.condition i {{ background:#fff0da;color:#dc8125; }}
        .dpr-flow-preview-node.start i {{ background:#e7f7f5;color:#11877f; }}
        .dpr-flow-preview-node.end i {{ background:#efedfb;color:#635bc0; }}
        .dpr-flow-preview-node b {{ overflow:hidden;color:#30484f;font-size:11px;text-overflow:ellipsis;white-space:nowrap; }}
        .dpr-flow-preview-node small {{ margin-top:3px;color:#849298;font-size:9.5px; }}
        .dpr-flow-preview-edge {{ position:relative;width:30px;height:2px;flex:none;background:#a5cbd5; }}
        .dpr-flow-preview-edge::after {{ content:'';position:absolute;right:-1px;top:-4px;border-left:7px solid #8fbfc9;border-top:5px solid transparent;border-bottom:5px solid transparent; }}
        .dpr-node-assignment-section {{ margin-top:15px;padding:14px;border:1px solid #dfe4e7;border-radius:9px;background:#f4f6f7; }}
        .dpr-node-assignment-section-head {{ display:flex;align-items:center;justify-content:space-between;padding:0 0 11px;border-bottom:1px solid #e7ecee; }}
        .dpr-node-assignment-section-head>div {{ display:flex;align-items:center;gap:8px; }}
        .dpr-node-assignment-section-head b {{ color:#30484f;font-size:13px; }}
        .dpr-node-assignment-section-head em {{ padding:2px 7px;border-radius:10px;background:#e5f2e9;color:#348458;font-style:normal;font-size:10px;font-weight:650; }}
        .dpr-node-assignment-section-head span {{ color:#849298;font-size:11px; }}
        .dpr-node-assignment-section .dpr-flow-node-card {{ border-left:3px solid #7bc392;background:#fff; }}
        .dpr-flow-node-card.focused {{ border-color:#48a86b;box-shadow:0 0 0 3px rgba(72,168,107,.16),0 5px 14px rgba(37,73,87,.12);scroll-margin-top:18px; }}
      </style>
      <div class="dpr-processing-task-page-head">
        <div><button type="button" class="dpr-processing-back" onclick="dprCloseProcessingTaskPage()">‹ 返回</button><h2 id="processingTaskDrawerTitle">新建处理任务</h2></div>
      </div>
      <div class="dpr-processing-task-page-body">
        <aside class="dpr-processing-task-menu" aria-label="处理任务配置">
          <button type="button" class="active" data-task-pane="basic" onclick="dprSwitchProcessingTaskPane(this)"><i>1</i>基本信息</button>
          <button type="button" data-task-pane="filter" onclick="dprSwitchProcessingTaskPane(this)"><i>2</i>筛选条件</button>
          <button type="button" data-task-pane="flow" onclick="dprSwitchProcessingTaskPane(this)"><i>3</i>处理环节</button>
        </aside>
        <main class="dpr-processing-task-form">
          <div class="dpr-processing-task-pane active" data-task-pane-content="basic">
            <div class="dpr-page-section-head"><div><h3>基本信息</h3></div></div>
            <div class="dpr-processing-basic-grid">
              <label class="fg"><span class="fg-req">任务名称</span><input id="processingTaskName" name="task_name" placeholder="请输入处理任务名称"></label>
              <label class="fg"><span class="fg-req">所属项目</span><select id="processingTaskProject" name="project"><option>预训练采集</option><option>demo 项目</option><option>宁德项目</option></select></label>
              <label class="fg"><span class="fg-req">任务性质</span><select id="processingTaskCategory" name="task_category"><option value="formal">正式</option><option value="informal">非正式（测试、培训等）</option></select></label>
              <label class="fg"><span class="fg-req">优先级</span><select id="processingTaskPriority" name="priority"><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option><option selected>6</option><option>7</option><option>8</option><option>9</option></select><small>数字越大越先处理：1–3 低，4–6 中，7–9 高</small></label>
              <label class="fg"><span class="fg-req">预期任务量</span><select id="processingTaskExpectedMode" name="expected_task_mode" onchange="dprExpectedTaskModeChange(this)"><option value="continuous">持续任务</option><option value="count">固定条数</option><option value="duration">固定时长</option></select></label>
              <label class="fg dpr-expected-task-value" id="processingTaskExpectedValueField" hidden><span class="fg-req" id="processingTaskExpectedValueLabel">任务条数</span><div class="dpr-expected-task-input"><input id="processingTaskExpectedValue" name="expected_task_value" type="number" min="0" step="1" placeholder="请输入任务条数" oninput="dprExpectedTaskValueChange(this)"><i id="processingTaskExpectedValueUnit">条</i></div></label>
              <label class="fg" id="processingTaskEnabledField"><span class="fg-req">任务状态</span><select id="processingTaskEnabled" name="enabled"><option value="true">开启</option><option value="false">关闭</option></select><small>关闭后停止接收新数据；在途数据继续处理完成。</small></label>
            </div>
          </div>
          <div class="dpr-processing-task-pane" data-task-pane-content="filter">
            <div class="dpr-page-section-head"><div><h3>筛选条件</h3></div></div>
            <div class="dpr-task-config-block dpr-page-config-block">
              <div class="dpr-task-config-cols dpr-filter-cols"><span></span><span>筛选项</span><span>操作符</span><span>值</span><span></span></div>
              <div id="processingTaskFilters"></div>
              <div class="dpr-task-config-empty" id="processingTaskFilterEmpty">不限制：所有新入湖数据均可进入该任务</div>
              <button type="button" class="dpr-filter-add-bottom" onclick="dprAddTaskFilter()">+ 添加条件</button>
            </div>
          </div>
          <div class="dpr-processing-task-pane" data-task-pane-content="flow">
            <div class="dpr-page-section-head"><div><h3>处理环节</h3></div></div>
            <div class="dpr-flow-assignment-layout">
              <div class="dpr-flow-selector"><div id="processingTaskFlowChoices"></div></div>
              <div class="dpr-flow-node-assignments">
                <div class="dpr-flow-assignment-summary" id="processingTaskFlowSummary">—</div>
                <div id="processingTaskFlowPreview"></div>
                <section class="dpr-node-assignment-section">
                  <div class="dpr-node-assignment-section-head"><div><em>节点级</em><b>人工任务节点分配</b></div><span id="processingTaskAssignmentHint">按节点配置供应商或用户组</span></div>
                  <div id="processingTaskAssignments"></div>
                </section>
              </div>
            </div>
          </div>
        </main>
      </div>
      <div class="dpr-processing-task-page-foot"><button type="button" class="btn" onclick="dprCloseProcessingTaskPage()">取消</button><button type="button" class="btn btn-primary" id="processingTaskDrawerSubmit" onclick="dprSubmitProcessingTask()">创建任务</button></div>
    </section>
    <script>
    var DPR_PROCESSING_FLOWS = {flow_catalog_json};
    var DPR_PROCESSING_RULES = {rule_catalog_json};
    var DPR_TASK_FILTER_FIELDS = {{
      '所属项目': {{type:'multi', options:['预训练采集', 'demo 项目', '宁德项目']}},
      '采集任务': {{type:'text', placeholder:'多个任务 ID 请用英文逗号隔开'}},
      '采集类型': {{type:'multi', options:['Normal', 'DAgger']}},
      '采集员': {{type:'people', options:['刘素粉', '王一帆', '陈晨', 'Wei Zhang', 'Lance Li', '包媛桐']}},
      '采集时间': {{type:'datetime_range'}},
      'recording_id': {{type:'text', placeholder:'多个 recording_id 请用英文逗号隔开'}},
      '质检结论': {{type:'multi', options:['合格', '不合格', '操作失误']}},
      '是否标注': {{type:'single', options:['是', '否']}}
    }};
    var DPR_TASK_FILTER_OPERATORS = ['等于', '不等于', '包含', '不包含', '为空', '不为空'];
    function dprProcessingEscape(value) {{
      return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/"/g, '&quot;');
    }}
    function dprToggleProcessingTask(input, taskId) {{
      var message = input.checked
        ? '开启后将持续筛选数据并处理，确认开启'
        : '关闭后将停止筛选新数据，已流入的数据将继续处理';
      if (!window.confirm(message)) {{
        input.checked = !input.checked;
        return;
      }}
      toast(input.checked
        ? '已开启 ' + taskId + '，将继续接收命中数据'
        : '已关闭 ' + taskId + '，不再接收新数据；在途流程继续执行');
    }}
    function dprTaskFilterValueControl(field, value) {{
      var config = DPR_TASK_FILTER_FIELDS[field] || {{type:'text'}};
      var values = String(value || '').split(',').filter(Boolean);
      if (config.type === 'text') {{
        return '<input class="dpr-task-filter-value" value="' + dprProcessingEscape(value) +
          '" placeholder="' + dprProcessingEscape(config.placeholder || '请输入字段值') + '">';
      }}
      if (config.type === 'datetime_range') {{
        var range = String(value || '').split('~');
        return '<div class="dpr-filter-datetime-range"><input class="dpr-task-filter-value" type="datetime-local" value="' + dprProcessingEscape(range[0] || '') + '" aria-label="开始时间" title="开始时间"><span>至</span><input class="dpr-task-filter-value" type="datetime-local" value="' + dprProcessingEscape(range[1] || '') + '" aria-label="结束时间（可选）" title="结束时间（可选）"></div>';
      }}
      if (config.type === 'people') {{
        return '<div class="dpr-filter-people" data-options="' + dprProcessingEscape(config.options.join(',')) + '"><div class="dpr-filter-people-picked">' + dprTaskFilterPeopleChips(values) + '</div><input class="dpr-task-filter-value dpr-filter-people-search" data-selected="' + dprProcessingEscape(values.join(',')) + '" placeholder="搜索采集员" oninput="dprSearchFilterPeople(this)" onfocus="dprFocusFilterPeople(this)"><div class="dpr-filter-people-results"></div></div>';
      }}
      if (config.type === 'multi') {{
        return dprTaskFilterMultiControl(config.options, values);
      }}
      return '<select class="dpr-task-filter-value">' + config.options.map(function(item) {{
        return '<option' + (item === value ? ' selected' : '') + '>' + dprProcessingEscape(item) + '</option>';
      }}).join('') + '</select>';
    }}
    function dprTaskFilterMultiControl(options, values) {{
      var label = values.length ? values.join('、') : '请选择选项';
      return '<details class="dpr-filter-multi"><summary class="dpr-task-filter-value">' + dprProcessingEscape(label) + '</summary><div>' + options.map(function(item) {{ return '<label><input type="checkbox" value="' + dprProcessingEscape(item) + '"' + (values.indexOf(item) >= 0 ? ' checked' : '') + ' onchange="dprUpdateFilterMulti(this)">' + dprProcessingEscape(item) + '</label>'; }}).join('') + '</div></details>';
    }}
    function dprUpdateFilterMulti(input) {{
      var box = input.closest('.dpr-filter-multi');
      var values = Array.from(box.querySelectorAll('input:checked')).map(function(item) {{ return item.value; }});
      box.querySelector('summary').textContent = values.length ? values.join('、') : '请选择选项';
    }}
    function dprTaskFilterPeopleChips(values) {{ return values.map(function(name) {{ return '<span>' + dprProcessingEscape(name) + '<button type="button" aria-label="移除" onclick="dprRemoveFilterPerson(this)">&times;</button></span>'; }}).join(''); }}
    function dprFocusFilterPeople(input) {{ input.value = ''; }}
    function dprSearchFilterPeople(input) {{
      var holder = input.closest('.dpr-filter-people');
      var keyword = input.value.trim().toLowerCase();
      if (!keyword) {{ holder.querySelector('.dpr-filter-people-results').innerHTML = ''; return; }}
      var options = (holder.dataset.options || '').split(',').filter(function(name) {{ return name && name.toLowerCase().indexOf(keyword) >= 0; }});
      var selected = (input.dataset.selected || '').split(',').filter(Boolean);
      holder.querySelector('.dpr-filter-people-results').innerHTML = options.filter(function(name) {{ return selected.indexOf(name) < 0; }}).map(function(name) {{ return '<button type="button" onclick="dprSelectFilterPerson(this)">' + dprProcessingEscape(name) + '</button>'; }}).join('') || '<small>未找到匹配人员</small>';
    }}
    function dprSelectFilterPerson(button) {{
      var holder = button.closest('.dpr-filter-people');
      var input = holder.querySelector('.dpr-filter-people-search');
      var selected = (input.dataset.selected || '').split(',').filter(Boolean);
      selected.push(button.textContent);
      input.dataset.selected = selected.join(',');
      holder.querySelector('.dpr-filter-people-picked').innerHTML = dprTaskFilterPeopleChips(selected);
      input.value = '';
      holder.querySelector('.dpr-filter-people-results').innerHTML = '';
    }}
    function dprRemoveFilterPerson(button) {{
      var holder = button.closest('.dpr-filter-people');
      var input = holder.querySelector('.dpr-filter-people-search');
      var name = button.parentNode.firstChild.textContent;
      var selected = (input.dataset.selected || '').split(',').filter(function(item) {{ return item && item !== name; }});
      input.dataset.selected = selected.join(',');
      button.parentNode.remove();
      input.focus();
    }}
    function dprTaskFilterRow(field, operator, value) {{
      var fields = Object.keys(DPR_TASK_FILTER_FIELDS);
      var selectedField = fields.indexOf(field) >= 0 ? field : fields[0];
      if (value === undefined) {{ value = operator; operator = '等于'; }}
      var selectedOperator = DPR_TASK_FILTER_OPERATORS.indexOf(operator) >= 0 ? operator : '等于';
      return '<div class="dpr-task-config-row dpr-filter-row">' +
        '<span class="dpr-filter-and">且</span>' +
        '<select class="dpr-task-filter-field" onchange="dprTaskFilterFieldChange(this)">' +
          fields.map(function(item) {{
            return '<option' + (item === selectedField ? ' selected' : '') + '>' +
              dprProcessingEscape(item) + '</option>';
          }}).join('') + '</select>' +
        '<select class="dpr-task-filter-operator" onchange="dprTaskFilterOperatorChange(this)">' +
          DPR_TASK_FILTER_OPERATORS.map(function(item) {{
            return '<option' + (item === selectedOperator ? ' selected' : '') + '>' + item + '</option>';
          }}).join('') + '</select>' +
        '<div class="dpr-task-filter-value-wrap">' +
          dprTaskFilterValueControl(selectedField, value) + '</div>' +
        '<button type="button" class="dpr-task-config-remove" ' +
          'onclick="dprRemoveTaskFilter(this)">&times;</button></div>';
    }}
    function dprRenderTaskFilters(filters) {{
      var holder = document.getElementById('processingTaskFilters');
      holder.innerHTML = (filters || []).map(function(item) {{
        return item.length >= 3
          ? dprTaskFilterRow(item[0], item[1], item[2])
          : dprTaskFilterRow(item[0], '等于', item[1]);
      }}).join('');
      dprRefreshFilterRelationLabels();
      document.getElementById('processingTaskFilterEmpty').style.display =
        holder.children.length ? 'none' : '';
    }}
    function dprRefreshFilterRelationLabels() {{
      document.querySelectorAll('#processingTaskFilters .dpr-filter-and').forEach(function(mark, index) {{
        mark.style.visibility = index === 0 ? 'hidden' : 'visible';
      }});
    }}
    function dprAddTaskFilter() {{
      document.getElementById('processingTaskFilters').insertAdjacentHTML(
        'beforeend', dprTaskFilterRow('所属项目', '等于', '预训练采集'));
      dprRefreshFilterRelationLabels();
      document.getElementById('processingTaskFilterEmpty').style.display = 'none';
    }}
    function dprRemoveTaskFilter(button) {{
      button.closest('.dpr-filter-row').remove();
      var holder = document.getElementById('processingTaskFilters');
      dprRefreshFilterRelationLabels();
      document.getElementById('processingTaskFilterEmpty').style.display =
        holder.children.length ? 'none' : '';
    }}
    function dprTaskFilterFieldChange(select) {{
      select.closest('.dpr-filter-row').querySelector(
        '.dpr-task-filter-value-wrap').innerHTML =
          dprTaskFilterValueControl(select.value, '');
    }}
    function dprTaskFilterOperatorChange(select) {{
      var row = select.closest('.dpr-filter-row');
      var valueWrap = row.querySelector('.dpr-task-filter-value-wrap');
      var valueControls = valueWrap.querySelectorAll('input.dpr-task-filter-value, select.dpr-task-filter-value');
      if (select.value === '为空' || select.value === '不为空') {{
        valueControls.forEach(function(valueControl) {{
          valueControl.value = '';
          valueControl.disabled = true;
          valueControl.placeholder = '无需填写';
        }});
      }} else {{
        valueControls.forEach(function(valueControl) {{
          valueControl.disabled = false;
          valueControl.placeholder = valueControl.tagName === 'SELECT' ? '请选择选项' : '请输入字段值';
        }});
      }}
    }}
    var DPR_ASSIGNMENT_TARGETS = {{
      user_group: ['质检复核用户组', '标注员用户组', '标注抽验员用户组', '内部验收用户组', '验收-端到端切分标注'],
      supplier: ['光轮智能', '供应商 A', '千寻数据']
    }};
    var DPR_SELECTED_FLOWS = {{}};
    var DPR_SELECTED_RULES = {{}};
    var DPR_ACTIVE_ASSIGNMENT_STAGE = '质检';
    var DPR_ENABLED_FLOW_STAGES = {{质检:false, 标注:false}};
    var DPR_FLOW_ASSIGNMENT_CACHE = {{}};
    var DPR_INITIAL_ASSIGNMENTS = {{}};
    var DPR_ALLOCATION_SETTING = {{mode:'proportional', quantitativeType:'time', expectedTotal:''}};
    var DPR_ACTIVE_PREVIEW_NODE = '';
    function dprFlowsForStage(stage) {{
      return DPR_PROCESSING_FLOWS.filter(function(flow) {{ return flow.stage === stage; }});
    }}
    function dprFlowByName(name) {{
      return DPR_PROCESSING_FLOWS.find(function(flow) {{ return flow.name === name; }});
    }}
    function dprAssignmentOptions(type, selected, used) {{
      used = used || [];
      return (DPR_ASSIGNMENT_TARGETS[type] || []).map(function(target) {{
        return '<option' + (target === selected ? ' selected' : '') + (used.indexOf(target) >= 0 ? ' disabled' : '') + '>' + dprProcessingEscape(target) + '</option>';
      }}).join('');
    }}
    function dprNodeAssignmentConfig(flow, node) {{
      var configs = flow && flow.node_assignment_configs ? flow.node_assignment_configs : {{}};
      return configs[node] || {{type: 'user_group', mode: 'task_custom'}};
    }}
    function dprNodeAssignmentTypeLocked(flow, node) {{
      // 处理任务中的分配类型由任务配置，不从流程节点锁定。
      return false;
    }}
    function dprFlowPreviewNodes(flow) {{
      if (flow && flow.preview_nodes && flow.preview_nodes.length) return flow.preview_nodes;
      return [{{name:'start',kind:'start'}}].concat((flow && flow.human_nodes || []).map(function(name) {{ return {{name:name,kind:'human'}}; }}), [{{name:'end',kind:'end'}}]);
    }}
    function dprFlowPreviewIcon(kind) {{
      return {{start:'▶',end:'■',automatic:'⚙',human:'人',condition:'⑂'}}[kind] || '·';
    }}
    function dprRenderFlowPreview(flow) {{
      var holder=document.getElementById('processingTaskFlowPreview');
      if (!flow) {{ holder.innerHTML=''; return; }}
      var nodes=dprFlowPreviewNodes(flow);
      var html='<section class="dpr-flow-preview-section"><div class="dpr-flow-preview-head"><b>流程图</b><span>点击人工任务节点定位下方分配卡片</span></div><div class="dpr-flow-preview-canvas"><div class="dpr-flow-preview-track">';
      nodes.forEach(function(node,index) {{
        var human=node.kind==='human';
        var active=human&&node.name===DPR_ACTIVE_PREVIEW_NODE?' active':'';
        var focusAttr=human?' data-focus-node="'+dprProcessingEscape(node.name)+'" onclick="dprFocusAssignmentCard(this.dataset.focusNode,this)"':'';
        var tag=human?'button type="button"':'div';
        html += '<'+tag+' class="dpr-flow-preview-node '+node.kind+active+'"'+focusAttr+'>'+
          '<i>'+dprFlowPreviewIcon(node.kind)+'</i><b>'+dprProcessingEscape(node.name)+'</b>'+
          '<small>'+ (node.kind==='human'?'人工任务节点':node.kind==='condition'?'IF / ELSE':node.kind==='automatic'?'自动化节点':node.kind==='start'?'Start':'End') +'</small></'+(human?'button':'div')+'>';
        if(index<nodes.length-1) html+='<span class="dpr-flow-preview-edge"></span>';
      }});
      holder.innerHTML=html+'</div></div></section>';
    }}
    function dprFocusAssignmentCard(nodeName, previewNode) {{
      DPR_ACTIVE_PREVIEW_NODE=nodeName;
      document.querySelectorAll('.dpr-flow-preview-node.human').forEach(function(node) {{ node.classList.toggle('active',node.dataset.focusNode===nodeName); }});
      var card=Array.from(document.querySelectorAll('#processingTaskAssignments .dpr-flow-node-card')).find(function(item) {{ return item.dataset.node===nodeName; }});
      if (!card) {{ toast('该人工节点无需配置分配'); return; }}
      document.querySelectorAll('#processingTaskAssignments .dpr-flow-node-card').forEach(function(item) {{ item.classList.remove('focused'); }});
      card.classList.add('focused');
      card.scrollIntoView({{behavior:'smooth',block:'center'}});
    }}
    function dprRefreshAllocationPresentation() {{
      var hint = document.getElementById('processingTaskAssignmentHint');
      if (hint) hint.textContent = '多个处理人之间为竞签关系';
    }}
    function dprAssignmentRow(type, amount, disabled, typeLocked) {{
      var disabledAttr = disabled ? ' disabled' : '';
      var typeDisabledAttr = (disabled || typeLocked) ? ' disabled' : '';
      return '<div class="dpr-flow-assignment-row">' +
        '<select class="dpr-flow-assignment-type" onchange="dprAssignmentTypeChange(this)"' + typeDisabledAttr + '>' +
          '<option value="user_group"' + (type === 'user_group' ? ' selected' : '') + '>用户组</option>' +
          '<option value="supplier"' + (type === 'supplier' ? ' selected' : '') + '>供应商</option></select>' +
        '<select class="dpr-flow-assignment-target" onchange="dprRefreshAssignmentTargets(this.closest(\\'.dpr-flow-node-card\\'))"' + disabledAttr + '>' + dprAssignmentOptions(type) + '</select>' +
        '<button type="button" class="dpr-task-config-remove" onclick="dprRemoveFlowAssignment(this)"' + disabledAttr + '>&times;</button>' +
      '</div>';
    }}
    function dprRenderNodeAssignments(flow, isDetail) {{
      var holder = document.getElementById('processingTaskAssignments');
      var humanNodes = flow && flow.human_nodes ? flow.human_nodes : [];
      document.getElementById('processingTaskFlowSummary').innerHTML = flow
        ? '<b>' + dprProcessingEscape(flow.name) + '</b><span>' + dprProcessingEscape(flow.version) + ' · ' + humanNodes.length + ' 个人工任务节点</span>'
        : '请选择左侧流程';
      dprRenderFlowPreview(flow);
      if (!humanNodes.length) {{
        holder.innerHTML = '<div class="dpr-processing-assignment-empty">该流程没有人工任务节点，无需配置处理人。</div>';
        return;
      }}
      if (DPR_FLOW_ASSIGNMENT_CACHE[flow.name]) {{
        holder.innerHTML = DPR_FLOW_ASSIGNMENT_CACHE[flow.name];
        holder.querySelectorAll('.dpr-flow-node-card').forEach(dprRefreshAssignmentTargets);
        dprRefreshAllocationPresentation();
        return;
      }}
      holder.innerHTML = humanNodes.map(function(node) {{
        var config = dprNodeAssignmentConfig(flow, node);
        var typeLocked = dprNodeAssignmentTypeLocked(flow, node);
        var inherited = config.mode === 'inherit';
        if (inherited) return '<section class="dpr-flow-node-card dpr-flow-node-card-inherited" data-node="' + dprProcessingEscape(node) + '" data-assignment-mode="inherit">' +
          '<div class="dpr-flow-node-card-head"><div><b>' + dprProcessingEscape(node) + '</b><span>人工任务节点</span></div></div>' +
          '<div class="dpr-flow-inherit-note">' + dprProcessingEscape(config.inherit_text || '继承前序节点') + '</div></section>';
        return '<section class="dpr-flow-node-card" data-node="' + dprProcessingEscape(node) + '">' +
          '<div class="dpr-flow-node-card-head"><div><b>' + dprProcessingEscape(node) + '</b><span>人工任务节点</span></div></div>' +
          '<div class="dpr-flow-assignment-cols"><span>类型</span><span>处理人</span><span></span></div>' +
          '<div class="dpr-flow-assignment-rows">' + dprAssignmentRow(config.type, '', isDetail, typeLocked) + '</div>' +
          '<button type="button" class="dpr-flow-add-assignment" onclick="dprAddFlowAssignment(this)"' + (isDetail ? ' disabled' : '') + '>+ 添加处理人分配</button>' +
        '</section>';
      }}).join('');
      holder.querySelectorAll('.dpr-flow-node-card').forEach(dprRefreshAssignmentTargets);
      dprRefreshAllocationPresentation();
    }}
    function dprRulesForStage(stage) {{ return DPR_PROCESSING_RULES.filter(function(rule) {{ return rule.stage === stage; }}); }}
    function dprRenderFlowChoices(stage, isDetail) {{
      var configDisabled = isDetail || document.getElementById('drawerProcessingTaskForm').dataset.mode === 'edit';
      ['质检', '标注'].forEach(function(itemStage) {{
        var flows = dprFlowsForStage(itemStage);
        if (!DPR_SELECTED_FLOWS[itemStage]) DPR_SELECTED_FLOWS[itemStage] = flows[0] && flows[0].name;
        var rules = dprRulesForStage(itemStage);
        if (!DPR_SELECTED_RULES[itemStage]) DPR_SELECTED_RULES[itemStage] = rules[0] && rules[0].name;
      }});
      DPR_ACTIVE_ASSIGNMENT_STAGE = stage || DPR_ACTIVE_ASSIGNMENT_STAGE;
      document.getElementById('processingTaskFlowChoices').innerHTML = ['质检', '标注'].map(function(itemStage) {{
        var flows = dprFlowsForStage(itemStage), rules = dprRulesForStage(itemStage), selected = DPR_SELECTED_FLOWS[itemStage];
        var enabled = !!DPR_ENABLED_FLOW_STAGES[itemStage];
        var disabled = configDisabled;
        return '<section class="dpr-flow-config-card' + (itemStage === DPR_ACTIVE_ASSIGNMENT_STAGE && enabled ? ' active' : '') + (!enabled ? ' collapsed' : '') + '" onclick="dprShowAssignmentsForStage(&quot;' + itemStage + '&quot;)">' +
          '<div class="dpr-flow-config-card-head"><div class="dpr-flow-card-title-line"><b>' + itemStage + '环节</b><label class="dpr-flow-toggle" onclick="event.stopPropagation()"><input type="checkbox" data-toggle-stage="' + itemStage + '" onchange="dprToggleFlowStage(this)"' + (enabled ? ' checked' : '') + (disabled ? ' disabled' : '') + '><i></i><em>' + (enabled ? '已开启' : '未开启') + '</em></label></div></div>' +
          '<div class="dpr-flow-config-card-body" onclick="event.stopPropagation()"' + (!enabled ? ' style="display:none;"' : '') + '><label>处理流程<select data-flow-stage="' + itemStage + '" onchange="dprProcessingFlowChange(this)"' + (configDisabled ? ' disabled' : '') + '>' + flows.map(function(flow) {{ return '<option' + (flow.name === selected ? ' selected' : '') + '>' + dprProcessingEscape(flow.name) + '</option>'; }}).join('') + '</select></label><label>' + itemStage + '规则<select data-rule-stage="' + itemStage + '" onchange="dprProcessingRuleChange(this)"' + (configDisabled ? ' disabled' : '') + '>' + rules.map(function(rule) {{ return '<option' + (rule.name === DPR_SELECTED_RULES[itemStage] ? ' selected' : '') + '>' + dprProcessingEscape(rule.name + ' ' + rule.version) + '</option>'; }}).join('') + '</select></label></div></section>';
      }}).join('');
      dprRenderNodeAssignments(DPR_ENABLED_FLOW_STAGES[DPR_ACTIVE_ASSIGNMENT_STAGE] ? dprFlowByName(DPR_SELECTED_FLOWS[DPR_ACTIVE_ASSIGNMENT_STAGE]) : null, isDetail);
    }}
    function dprApplyInitialAssignments(isDetail) {{
      var flow = dprFlowByName(DPR_SELECTED_FLOWS[DPR_ACTIVE_ASSIGNMENT_STAGE]);
      var initial = flow && DPR_INITIAL_ASSIGNMENTS[DPR_ACTIVE_ASSIGNMENT_STAGE];
      if (!initial || typeof initial !== 'object') return;
      document.querySelectorAll('#processingTaskAssignments .dpr-flow-node-card').forEach(function(card) {{
        var rows = initial[card.dataset.node] || [];
        if (!rows.length) return;
        var holder = card.querySelector('.dpr-flow-assignment-rows');
        holder.innerHTML = rows.map(function(item) {{
          var config = dprNodeAssignmentConfig(flow, card.dataset.node);
          return dprAssignmentRow(item.type, item.amount == null ? item.percent : item.amount, isDetail, dprNodeAssignmentTypeLocked(flow, card.dataset.node));
        }}).join('');
        holder.querySelectorAll('.dpr-flow-assignment-row').forEach(function(row, index) {{
          var target = row.querySelector('.dpr-flow-assignment-target');
          if (target && rows[index]) target.value = rows[index].target;
        }});
        dprRefreshAssignmentTargets(card);
      }});
    }}
    function dprToggleFlowStage(input) {{
      var stage = input.dataset.toggleStage;
      DPR_ENABLED_FLOW_STAGES[stage] = input.checked;
      if (input.checked) DPR_ACTIVE_ASSIGNMENT_STAGE = stage;
      dprRenderFlowChoices(DPR_ACTIVE_ASSIGNMENT_STAGE, document.getElementById('drawerProcessingTaskForm').dataset.mode === 'detail');
    }}
    function dprProcessingFlowChange(select) {{
      var stage = select.dataset.flowStage;
      var previousFlow = dprFlowByName(DPR_SELECTED_FLOWS[stage]);
      if (stage === DPR_ACTIVE_ASSIGNMENT_STAGE && previousFlow) {{
        DPR_FLOW_ASSIGNMENT_CACHE[previousFlow.name] = document.getElementById('processingTaskAssignments').innerHTML;
      }}
      DPR_SELECTED_FLOWS[stage] = select.value;
      delete DPR_FLOW_ASSIGNMENT_CACHE[select.value];
      dprShowAssignmentsForStage(stage);
    }}
    function dprProcessingRuleChange(select) {{ DPR_SELECTED_RULES[select.dataset.ruleStage] = select.value.split(' v')[0]; }}
    function dprShowAssignmentsForStage(stage) {{
      if (!DPR_ENABLED_FLOW_STAGES[stage]) return;
      var oldFlow = dprFlowByName(DPR_SELECTED_FLOWS[DPR_ACTIVE_ASSIGNMENT_STAGE]);
      if (stage !== DPR_ACTIVE_ASSIGNMENT_STAGE && oldFlow) {{
        DPR_FLOW_ASSIGNMENT_CACHE[oldFlow.name] = document.getElementById('processingTaskAssignments').innerHTML;
      }}
      DPR_ACTIVE_ASSIGNMENT_STAGE = stage;
      dprRenderFlowChoices(stage, document.getElementById('drawerProcessingTaskForm').dataset.mode === 'detail');
    }}
    function dprAssignmentTypeChange(select) {{
      dprRefreshAssignmentTargets(select.closest('.dpr-flow-node-card'));
    }}
    function dprRefreshAssignmentTargets(card) {{
      var rows = Array.from(card.querySelectorAll('.dpr-flow-assignment-row'));
      rows.forEach(function(row) {{
        var target = row.querySelector('.dpr-flow-assignment-target');
        var current = target.value;
        var usedByOthers = rows.filter(function(other) {{ return other !== row && other.querySelector('.dpr-flow-assignment-type').value === row.querySelector('.dpr-flow-assignment-type').value; }}).map(function(other) {{ return other.querySelector('.dpr-flow-assignment-target').value; }});
        if (usedByOthers.indexOf(current) >= 0 || (DPR_ASSIGNMENT_TARGETS[row.querySelector('.dpr-flow-assignment-type').value] || []).indexOf(current) < 0) {{
          current = (DPR_ASSIGNMENT_TARGETS[row.querySelector('.dpr-flow-assignment-type').value] || []).find(function(item) {{ return usedByOthers.indexOf(item) < 0; }}) || '';
        }}
        target.innerHTML = dprAssignmentOptions(row.querySelector('.dpr-flow-assignment-type').value, current, usedByOthers);
      }});
    }}
    function dprAddFlowAssignment(button) {{
      var card = button.closest('.dpr-flow-node-card');
      var flow = dprFlowByName(DPR_SELECTED_FLOWS[DPR_ACTIVE_ASSIGNMENT_STAGE]);
      var config = dprNodeAssignmentConfig(flow, card.dataset.node);
      card.querySelector('.dpr-flow-assignment-rows').insertAdjacentHTML('beforeend', dprAssignmentRow(config.type, '', false, dprNodeAssignmentTypeLocked(flow, card.dataset.node)));
      dprRefreshAssignmentTargets(card);
    }}
    function dprRemoveFlowAssignment(button) {{
      var card = button.closest('.dpr-flow-node-card');
      var rows = card.querySelectorAll('.dpr-flow-assignment-row');
      if (rows.length <= 1) {{ toast('每个人工节点至少保留一个处理人分配'); return; }}
      button.closest('.dpr-flow-assignment-row').remove();
      dprRefreshAssignmentTargets(card);
    }}
    function dprProcessingAssignmentsValid() {{
      return Array.from(document.querySelectorAll('.dpr-flow-node-card')).every(function(card) {{
        if (card.dataset.assignmentMode === 'inherit') return true;
        var rows = Array.from(card.querySelectorAll('.dpr-flow-assignment-row'));
        return rows.length > 0 && rows.every(function(row) {{
          var target = row.querySelector('.dpr-flow-assignment-target');
          return !!(target && target.value);
        }});
      }});
    }}
    function dprExpectedTaskModeChange(select) {{
      var mode = select.value;
      var field = document.getElementById('processingTaskExpectedValueField');
      var input = document.getElementById('processingTaskExpectedValue');
      var label = document.getElementById('processingTaskExpectedValueLabel');
      var unit = document.getElementById('processingTaskExpectedValueUnit');
      var visible = mode !== 'continuous';
      field.hidden = !visible;
      input.step = mode === 'duration' ? '0.5' : '1';
      label.textContent = mode === 'duration' ? '任务时长' : '任务条数';
      unit.textContent = mode === 'duration' ? '小时' : '条';
      input.placeholder = mode === 'duration' ? '请输入任务时长' : '请输入任务条数';
      dprSyncAllocationFromExpectedTask(true);
    }}
    function dprExpectedTaskValueChange(input) {{
      dprSyncAllocationFromExpectedTask(false);
      var validation = dprExpectedTaskValidation();
      input.setCustomValidity(validation.valid ? '' : validation.message);
    }}
    function dprSyncAllocationFromExpectedTask(clearValues) {{
      var mode = document.getElementById('processingTaskExpectedMode').value;
      var nextMode = mode === 'continuous' ? 'proportional' : 'quantitative';
      var nextType = mode === 'duration' ? 'time' : 'count';
      DPR_ALLOCATION_SETTING.mode = nextMode;
      DPR_ALLOCATION_SETTING.quantitativeType = nextType;
      DPR_ALLOCATION_SETTING.expectedTotal = mode === 'continuous' ? '' : (document.getElementById('processingTaskExpectedValue').value || '');
      dprRefreshAllocationPresentation();
    }}
    function dprExpectedTaskValidation() {{
      var mode = document.getElementById('processingTaskExpectedMode').value;
      if (mode === 'continuous') return {{valid:true, message:''}};
      var value = Number(document.getElementById('processingTaskExpectedValue').value);
      if (!(value > 0)) return {{valid:false, message:mode === 'duration' ? '请填写任务时长' : '请填写任务条数'}};
      var drawer = document.getElementById('drawerProcessingTaskForm');
      if (drawer.dataset.mode === 'edit') {{
        var current = Number(drawer.dataset.currentFlowedValue || 0);
        var unit = drawer.dataset.currentFlowedUnit || (mode === 'duration' ? '小时' : '条');
        if (current > 0 && value < current) return {{valid:false, message:'预期任务量不能小于当前已流入数据量（' + current + ' ' + unit + '）'}};
      }}
      return {{valid:true, message:''}};
    }}
    function dprExpectedTaskValid() {{
      return dprExpectedTaskValidation().valid;
    }}
    function dprSwitchProcessingTaskPane(button) {{
      document.querySelectorAll('.dpr-processing-task-menu button').forEach(function(item) {{ item.classList.toggle('active', item === button); }});
      document.querySelectorAll('.dpr-processing-task-pane').forEach(function(pane) {{ pane.classList.toggle('active', pane.dataset.taskPaneContent === button.dataset.taskPane); }});
    }}
    function dprOpenProcessingTaskDrawer(mode, trigger) {{
      var data = trigger ? trigger.dataset : {{
        taskName: '',
        project: '预训练采集',
        taskCategory: 'formal',
        priority: '6',
        enabled: 'true',
        expectedMode: 'continuous',
        expectedValue: '',
        filters: '[]',
        assignments: '{{}}',
        flows: JSON.stringify([
          ['质检', '多级质检复核流程', 'v3', '通用质检规则'],
          ['标注', '端到端切分标注流程', 'v2', '通用动作标注规则'],
          ['验收', '数据验收流程', 'v1']
        ])
      }};
      var drawer = document.getElementById('drawerProcessingTaskForm');
      var isDetail = mode === 'detail';
      var isReadOnly = isDetail || mode === 'edit';
      drawer.dataset.mode = mode;
      document.getElementById('processingTaskEnabledField').hidden = mode === 'new';
      document.getElementById('processingTaskDrawerTitle').textContent =
        mode === 'new' ? '新建处理任务' : (isDetail ? '处理任务详情' : '编辑处理任务');
      document.getElementById('processingTaskName').value = data.taskName || '';
      document.getElementById('processingTaskProject').value = data.project || '预训练采集';
      document.getElementById('processingTaskCategory').value = data.taskCategory || 'formal';
      var priorityValue = {{P0:'9', P1:'6', P2:'3'}}[data.priority] || data.priority || '6';
      document.getElementById('processingTaskPriority').value = priorityValue;
      document.getElementById('processingTaskEnabled').value = data.enabled || 'true';
      document.getElementById('processingTaskExpectedMode').value = data.expectedMode || 'continuous';
      document.getElementById('processingTaskExpectedValue').value = data.expectedValue || '';
      var currentExpectedMode = data.expectedMode || 'continuous';
      drawer.dataset.currentFlowedValue = currentExpectedMode === 'duration' ? (data.flowedHours || '0') : (data.flowedCount || '0');
      drawer.dataset.currentFlowedUnit = currentExpectedMode === 'duration' ? '小时' : '条';
      dprExpectedTaskModeChange(document.getElementById('processingTaskExpectedMode'));
      var filters = [];
      var flows = [];
      try {{ filters = JSON.parse(data.filters || '[]'); }} catch (error) {{}}
      try {{ flows = JSON.parse(data.flows || '[]'); }} catch (error) {{}}
      try {{ DPR_INITIAL_ASSIGNMENTS = JSON.parse(data.assignments || '{{}}'); }} catch (error) {{ DPR_INITIAL_ASSIGNMENTS = {{}}; }}
      DPR_FLOW_ASSIGNMENT_CACHE = {{}};
      DPR_SELECTED_FLOWS = {{}};
      DPR_SELECTED_RULES = {{}};
      DPR_ENABLED_FLOW_STAGES = {{质检:false, 标注:false}};
      dprRenderTaskFilters(filters);
      (flows || []).forEach(function(binding) {{
        if (binding[0] === '质检' || binding[0] === '标注') {{
          DPR_SELECTED_FLOWS[binding[0]] = binding[1];
          if (binding[3]) DPR_SELECTED_RULES[binding[0]] = binding[3];
          if (mode !== 'new') DPR_ENABLED_FLOW_STAGES[binding[0]] = true;
        }}
      }});
      if (DPR_ENABLED_FLOW_STAGES.标注) DPR_ACTIVE_ASSIGNMENT_STAGE = '标注';
      dprRenderFlowChoices(DPR_ACTIVE_ASSIGNMENT_STAGE, isReadOnly);
      dprApplyInitialAssignments(isReadOnly);
      drawer.querySelectorAll('input, select').forEach(function(control) {{
        if (isDetail) control.disabled = true;
        else if (mode === 'edit') control.disabled = !['processingTaskPriority', 'processingTaskEnabled', 'processingTaskExpectedValue'].includes(control.id);
        else if (control.classList.contains('dpr-flow-assignment-type')) {{
          var card = control.closest('.dpr-flow-node-card');
          var flow = dprFlowByName(DPR_SELECTED_FLOWS[DPR_ACTIVE_ASSIGNMENT_STAGE]);
          control.disabled = !!(card && dprNodeAssignmentTypeLocked(flow, card.dataset.node));
        }}
        else if (!control.closest('.dpr-flow-config-card-head, .dpr-flow-config-card-body')) control.disabled = false;
      }});
      if (mode === 'edit' && document.getElementById('processingTaskExpectedMode').value === 'continuous') document.getElementById('processingTaskExpectedValue').disabled = true;
      drawer.querySelectorAll('.dpr-flow-preview-node, .dpr-flow-add-assignment').forEach(function(button) {{ button.disabled = isReadOnly; }});
      drawer.querySelectorAll('.dpr-task-config-remove').forEach(function(button) {{ button.style.display = isDetail ? 'none' : ''; }});
      var filterLocked = isDetail || mode === 'edit';
      drawer.querySelectorAll('#processingTaskFilters input, #processingTaskFilters select, #processingTaskFilters button').forEach(function(control) {{
        control.disabled = filterLocked;
      }});
      drawer.querySelectorAll('#processingTaskFilters .dpr-task-config-remove').forEach(function(button) {{
        button.style.display = filterLocked ? 'none' : '';
      }});
      drawer.querySelector('.dpr-filter-add-bottom').style.display = filterLocked ? 'none' : '';
      if (mode === 'edit') drawer.querySelectorAll('#processingTaskFilters .dpr-task-config-remove').forEach(function(button) {{ button.disabled = true; }});
      var submit = document.getElementById('processingTaskDrawerSubmit');
      submit.style.display = isDetail ? 'none' : '';
      submit.textContent = mode === 'new' ? '创建任务' : '保存修改';
      drawer.setAttribute('aria-hidden', 'false');
      document.body.classList.add('dpr-processing-task-page-open');
      var firstMenu = document.querySelector('.dpr-processing-task-menu button[data-task-pane="basic"]');
      dprSwitchProcessingTaskPane(firstMenu);
    }}
    function dprCloseProcessingTaskPage() {{
      document.getElementById('drawerProcessingTaskForm').setAttribute('aria-hidden', 'true');
      document.body.classList.remove('dpr-processing-task-page-open');
    }}
    function dprSubmitProcessingTask() {{
      var expectedValidation = dprExpectedTaskValidation();
      if (!expectedValidation.valid) {{
        toast(expectedValidation.message);
        return;
      }}
      if (!DPR_ENABLED_FLOW_STAGES['质检']) {{
        toast('请先开启并配置质检流程');
        return;
      }}
      if (!dprProcessingAssignmentsValid()) {{
        toast('每个人工任务节点至少配置一个处理人');
        return;
      }}
      var mode = document.getElementById('drawerProcessingTaskForm').dataset.mode;
      toast(mode === 'new'
        ? 'Demo: 已创建持续处理任务并开始监听数据湖'
        : 'Demo: 已保存处理任务');
      dprCloseProcessingTaskPage();
    }}
    </script>
    """
    return _intro(
        "处理任务",
        "处理任务是持续运行的数据筛选器；任务命中数据后，按业务顺序进入多个独立、可版本化的处理流程。",
        "",
        new_task_button,
        inline_action=True,
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
        <button class="btn btn-tertiary" type="button" onclick="dprResetAllocationFilters()">清空</button>
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
        <button type="button" class="btn btn-tertiary" onclick="dprResetFlowFilters()">清空</button>
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


def render_allocation_management_old():
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
      <div class="ff"><label>当前用户组</label><select id="dprStreamSupplier">
        <option value="">全部用户组</option><option>质检复核用户组</option>
        <option>标注员用户组</option><option>标注抽验员用户组</option>
        <option>内部验收用户组</option>
      </select></div>
      <div class="ff"><label>当前成员</label>
        <input id="dprStreamOperator" placeholder="请输入成员"></div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" type="button" onclick="dprResetStreamFilters()">清空</button>
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
            "当前任务池 / 当前成员",
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
          <p>当前流程实例保持不变，仅调整人工节点的用户组或指定成员。</p>
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
                f'onclick="dprOpenBindTask(this)">补充处理绑定</button>',
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
        <button class="btn btn-tertiary" type="button" onclick="dprResetUnboundFilters()">清空</button>
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
            "未命中原因",
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
          <div><span>未命中批次</span><b id="dprUnboundVisibleBatches">3</b><small>个</small></div>
          <div><span>待分配数据</span><b id="dprUnboundDataCount">1,484</b><small>条</small></div>
          <p>通过补充处理任务筛选条件，让池中数据进入持续处理链路。</p>
        </div>
        """
        + _section(
            "未命中处理任务的数据",
            unbound_filters
            + unbound_table
            + '<div class="dpr-allocation-table-foot">'
            + '<span>已选择 <b id="dprUnboundSelectedCount">0</b> 个批次</span>'
            + '<button type="button" class="btn btn-primary" id="dprBulkBindTask" '
            + 'disabled onclick="dprOpenBindTask()">批量补充处理绑定</button></div>',
            "只展示尚未命中任何启用中处理任务筛选条件的数据。",
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
        <button type="button" class="btn btn-tertiary" onclick="dprResetReprocessFilters()">清空</button>
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
        <h3>重新指派任务池资源</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-drawer-summary" id="dprStreamReassignSummary">—</div>
        <div class="dpr-assignment-context">
          <span>当前处理任务<b id="dprStreamCurrentTask">—</b></span>
          <span>当前处理流程<b id="dprStreamCurrentWorkflow">—</b></span>
        </div>
        <div class="dpr-inline-notice">处理任务和流程实例保持不变，本次仅调整人工节点任务池的领取范围。</div>
        <div class="fg"><label class="fg-req">重新指派用户组</label>
          <select id="dprStreamNewSupplier" onchange="dprSyncStreamOperators()">
            <option>质检复核用户组</option><option>标注员用户组</option>
            <option>标注抽验员用户组</option><option>内部验收用户组</option>
          </select>
        </div>
        <div class="fg"><label>指定成员 <span class="dpr-optional">（可选）</span></label>
          <select id="dprStreamNewOperator"><option value="">由用户组成员领取</option></select>
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
        <h3>补充处理绑定</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-drawer-summary" id="dprBindTaskSummary">—</div>
        <div class="dpr-inline-notice">来源任务不再直接绑定处理任务；系统将把本批数据对应条件补充到持续处理任务中。</div>
        <div class="fg"><label class="fg-req">持续处理任务</label>
          <select id="dprBindProcessingTask">
            <option>20448 · 宁德采集数据处理</option>
            <option>20447 · 预训练数据质检</option>
            <option>20446 · Demo 数据处理</option>
          </select>
        </div>
        <div class="fg"><label class="fg-req">新增流程绑定</label>
          <select id="dprBindWorkflow">
            <option>多级质检复核流程 v3</option>
            <option>端到端切分标注流程 v2</option>
            <option>数据验收流程 v1</option>
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
        '质检复核用户组':['','包媛桐','光轮-QC-021'],
        '标注员用户组':['','供应商 A-017','供应商 A-026'],
        '标注抽验员用户组':['','joanna.qiao','标注抽验-008'],
        '内部验收用户组':['','joanna.qiao','Wei Zhang']
      };
      document.getElementById('dprStreamNewOperator').innerHTML =
        (options[supplier] || []).map(function(name) {
          return '<option value="' + name + '">' + (name || '由用户组成员领取') + '</option>';
        }).join('');
    }
    function dprSubmitStreamReassign() {
      toast('Demo: 已调整用户组任务池，当前流程实例保持不变');
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
      toast('Demo: 已补充持续处理任务的筛选条件与流程绑定');
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
            "分配管理-旧",
            "按任务池调度人工处理资源，补充持续处理任务的筛选绑定，并支持面向训练需求的数据再处理。",
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


def render_allocation_management():
    stage_cards = ""
    for item in ALLOCATION_STAGE_SUMMARY:
        total = item["total"] or 1
        pending = item["unassigned"] + item["assigned_waiting"]
        segments = "".join(
            f'<i class="{tone}" data-dispatch-segment="{key}" '
            f'style="width:{round(value / total * 100, 1)}%"></i>'
            for key, value, tone in (
                ("unassigned", item["unassigned"], "unassigned"),
                ("assigned_waiting", item["assigned_waiting"], "assigned"),
                ("processing", item["processing"], "processing"),
                ("completed", item["completed"], "completed"),
            )
        )
        stage_cards += f"""
        <button type="button" class="dpr-dispatch-stage-card"
          data-dispatch-stage="{_e(item["stage"])}"
          onclick="dprSelectDispatchStage(this)">
          <div class="dpr-dispatch-stage-title">
            <span>{_e(item["stage"])}</span>
            <b data-stage-pending>{pending:,}<small>待处理</small></b>
          </div>
          <div class="dpr-allocation-bar">{segments}</div>
          <div class="dpr-dispatch-stage-values">
            <span><i class="unassigned"></i>未分配
              <b data-stage-value="unassigned">{item["unassigned"]:,}</b></span>
            <span><i class="assigned"></i>已分配待处理
              <b data-stage-value="assigned_waiting">{item["assigned_waiting"]:,}</b></span>
            <span><i class="processing"></i>处理中
              <b data-stage-value="processing">{item["processing"]:,}</b></span>
            <span><i class="completed"></i>已完成
              <b data-stage-value="completed">{item["completed"]:,}</b></span>
          </div>
        </button>
        """

    issue_rows = []
    issue_attrs = []
    stage_groups = {}
    for stream_item in STREAM_CAPACITY_BACKLOGS:
        group_key = (stream_item["processing_task"], stream_item["node"])
        source_tasks = stream_item.get(
            "source_tasks", [stream_item["source_task"]]
        )
        if group_key not in stage_groups:
            stage_groups[group_key] = {
                **stream_item,
                "source_tasks": list(dict.fromkeys(source_tasks)),
            }
            continue
        group = stage_groups[group_key]
        group["source_tasks"] = list(
            dict.fromkeys(group["source_tasks"] + list(source_tasks))
        )
        group["input_rate"] += stream_item["input_rate"]
        group["backlog"] += stream_item["backlog"]
        group["throughput"] = max(
            group["throughput"], stream_item["throughput"]
        )
        if int(stream_item["stalled"].split()[0]) > int(
            group["stalled"].split()[0]
        ):
            group["stalled"] = stream_item["stalled"]
        if stream_item["priority"] == "P0":
            group["priority"] = "P0"

    task_groups = {}
    for stage_item in stage_groups.values():
        task_id = stage_item["processing_task"]
        if task_id not in task_groups:
            task_groups[task_id] = {
                "processing_task": task_id,
                "project": stage_item["project"],
                "source_tasks": [],
                "stages": [],
            }
        task_group = task_groups[task_id]
        task_group["source_tasks"] = list(
            dict.fromkeys(
                task_group["source_tasks"] + stage_item["source_tasks"]
            )
        )
        task_group["stages"].append(stage_item)

    for task_group in task_groups.values():
        stages = task_group["stages"]
        source_tasks = task_group["source_tasks"]
        source_task_payload = "|".join(source_tasks)
        processing_task = task_group["processing_task"]
        total_backlog = sum(item["backlog"] for item in stages)
        longest_age = max(int(item["stalled"].split()[0]) for item in stages)
        highest_priority = (
            "P0" if any(item["priority"] == "P0" for item in stages) else "P1"
        )
        stage_names = [item["stage"] for item in stages]
        search_tasks = " ".join(source_tasks + [processing_task])
        issue_rows.append(
            [
                '<span class="dpr-dispatch-issue capacity">吞吐不足</span>',
                f'<div class="dpr-dispatch-object">'
                f'<span><i>来源任务</i><button type="button" '
                f'class="dpr-dispatch-source-link" '
                f'data-sources="{_e(source_task_payload)}" '
                f'onclick="dprOpenDispatchSources(this)">'
                f'{len(source_tasks)} 个 · 查看</button></span>'
                f'<span><i>处理任务</i><code>{_e(processing_task)}</code></span>'
                f'</div>',
                _e(task_group["project"]),
                f'<button type="button" class="dpr-dispatch-stage-count" '
                f'onclick="dprToggleDispatchTask(this)">'
                f'{len(stages)} 个处理节点积压</button>',
                f'<b>{total_backlog:,}</b> 条',
                f'<span class="dpr-stalled">{longest_age} 小时</span>',
                '<span class="dpr-dispatch-current">多个处理节点能力不足'
                '<small>展开查看各节点的吞吐与处理资源</small></span>',
                _priority_tag(highest_priority),
                '<button type="button" class="dpr-link-button '
                'dpr-dispatch-expand-button" '
                'onclick="dprToggleDispatchTask(this)">展开</button>',
            ]
        )
        issue_attrs.append(
            f'class="dpr-dispatch-task-row" '
            f'data-dispatch-role="parent" '
            f'data-dispatch-type="capacity" '
            f'data-dispatch-group="{_e(processing_task)}" '
            f'data-dispatch-project="{_e(task_group["project"])}" '
            f'data-dispatch-stages="{_e("|".join(stage_names))}" '
            f'data-dispatch-task="{_e(search_tasks)}" '
            f'data-dispatch-count="{total_backlog}" '
            f'data-dispatch-age="{longest_age}" '
            f'data-dispatch-expanded="false"'
        )

        for item in stages:
            age = int(item["stalled"].split()[0])
            issue_rows.append(
                [
                    '<span class="dpr-dispatch-tree-branch">↳</span>',
                    '<span class="dpr-dispatch-child-label">节点明细</span>',
                    '<span class="muted">—</span>',
                    _record_tag(item["node"]),
                    f'<b>{item["backlog"]:,}</b> 条',
                    f'<span class="dpr-stalled">{_e(item["stalled"])}</span>',
                    f'<span class="dpr-dispatch-current">'
                    f'输入 {item["input_rate"]} / 处理 {item["throughput"]} 条/小时'
                    f'<small>处理资源：{_e(item["supplier"])}</small></span>',
                    _priority_tag(item["priority"]),
                    f'<button type="button" class="dpr-link-button" '
                    f'data-processing-task="{_e(item["processing_task"])}" '
                    f'data-workflow="{_e(item["workflow"])}" '
                    f'data-stage="{_e(item["stage"])}" '
                    f'data-node="{_e(item["node"])}" '
                    f'data-backlog="{item["backlog"]}" '
                    f'data-input-rate="{item["input_rate"]}" '
                    f'data-throughput="{item["throughput"]}" '
                    f'data-supplier="{_e(item["supplier"])}" '
                    f'data-operator="{_e(item["operator"])}" '
                    f'onclick="dprOpenDispatchResource(this)">分配积压数据</button>',
                ]
            )
            issue_attrs.append(
                f'class="dpr-dispatch-stage-row" '
                f'data-dispatch-role="child" '
                f'data-dispatch-type="capacity" '
                f'data-dispatch-parent="{_e(processing_task)}" '
                f'data-dispatch-project="{_e(task_group["project"])}" '
                f'data-dispatch-stage="{_e(item["stage"])}" '
                f'data-dispatch-count="{item["backlog"]}" '
                f'data-dispatch-age="{age}" '
                f'style="display:none"'
            )

    unbound_ages = (31, 22, 17)
    for index, item in enumerate(UNBOUND_DATA_POOLS):
        age = unbound_ages[index]
        priority = "P0" if item["count"] >= 800 else "P1"
        issue_rows.append(
            [
                '<span class="dpr-dispatch-issue unbound">未进入处理</span>',
                f'<div class="dpr-dispatch-object">'
                f'<span><i>来源任务</i><button type="button" '
                f'class="dpr-dispatch-source-link" '
                f'data-sources="{_e(item["source_task"])}" '
                f'onclick="dprOpenDispatchSources(this)">1 个 · 查看</button></span>'
                f'<span><i>处理任务</i><code class="empty">—</code></span>'
                f'</div>',
                _e(item["project"]),
                '<span class="muted">—</span>',
                f'<b>{item["count"]:,}</b> 条',
                f'<span class="dpr-stalled">{age} 小时</span>',
                f'<span class="dpr-dispatch-current">{_e(item["reason"])}'
                f'<small>数据来源：{_e(item["source"])} · '
                f'操作人：{_e(item["operator"])}</small></span>',
                _priority_tag(priority),
                f'<button type="button" class="dpr-link-button" '
                f'data-pool-id="{_e(item["id"])}" '
                f'data-source-task="{_e(item["source_task"])}" '
                f'data-source="{_e(item["source"])}" '
                f'data-count="{item["count"]}" '
                f'onclick="dprOpenDispatchBinding(this)">绑定处理任务</button>',
            ]
        )
        issue_attrs.append(
            f'data-dispatch-role="standalone" '
            f'data-dispatch-type="unbound" '
            f'data-dispatch-project="{_e(item["project"])}" '
            f'data-dispatch-stage="" '
            f'data-dispatch-task="{_e(item["source_task"])} {_e(item["id"])}" '
            f'data-dispatch-count="{item["count"]}" '
            f'data-dispatch-age="{age}"'
        )

    issue_table = _table(
        [
            "问题类型",
            "影响任务",
            "项目",
            "处理节点",
            "影响数据",
            "滞留时间",
            "当前状态",
            "优先级",
            "操作",
        ],
        issue_rows,
        table_id="dpr-dispatch-issue-table",
        row_attrs=issue_attrs,
    )

    reprocess_preview = _table(
        ["项目", "数据来源", "可见数据", "原处理流程", "当前状态"],
        [
            [
                _e(item["project"]),
                _record_tag(item["source"]),
                f'{item["count"]:,} 条',
                _e(item["current_process"]),
                _e(item["status"]),
            ]
            for item in REPROCESS_DATA_OVERVIEW
        ],
        table_id="dpr-dispatch-reprocess-preview",
        row_attrs=[
            f'data-project="{_e(item["project"])}"'
            for item in REPROCESS_DATA_OVERVIEW
        ],
    )

    project_summary_json = json.dumps(
        ALLOCATION_PROJECT_STAGE_SUMMARY, ensure_ascii=False
    ).replace("</", "<\\/")
    reprocess_counts_json = json.dumps(
        {
            "全部项目": sum(item["count"] for item in REPROCESS_DATA_OVERVIEW),
            **{
                item["project"]: item["count"]
                for item in REPROCESS_DATA_OVERVIEW
            },
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")

    project_switcher = """
    <label class="dpr-project-scope">
      <span>项目</span>
      <select id="dprDispatchProjectScope" onchange="dprRefreshDispatchPage()">
        <option>全部项目</option>
        <option>宁德项目</option>
        <option>demo 项目</option>
        <option>预训练采集</option>
      </select>
    </label>
    """

    drawers_and_script = """
    <div class="drawer dpr-dispatch-source-drawer" id="drawerDispatchSources">
      <div class="drawer-head">
        <h3>来源任务明细</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-inline-notice">
          当前处理任务通过筛选条件持续接收数据，可能同时命中多个采集或导入任务。
        </div>
        <div class="dpr-dispatch-source-list" id="dprDispatchSourceList"></div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn btn-primary" onclick="closeDrawer()">知道了</button>
      </div>
    </div>

    <div class="drawer dpr-allocation-drawer" id="drawerDispatchResource">
      <div class="drawer-head">
        <h3>分配存量积压</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-drawer-summary" id="dprDispatchResourceSummary">—</div>
        <div class="dpr-dispatch-backlog-context">
          <div><span>处理流程</span><b id="dprDispatchCurrentFlow">—</b></div>
          <div><span>输入 / 处理速度</span>
            <b><i id="dprDispatchCurrentInput">—</i> / <i id="dprDispatchCurrentThroughput">—</i></b>
          </div>
          <div><span>当前积压</span><b id="dprDispatchCurrentBacklog">—</b></div>
        </div>
        <div class="dpr-task-config-block dpr-dispatch-assignment-block">
          <div class="dpr-task-config-head">
            <div><b>分配对象</b><span>本期仅支持将当前积压拆分给多个用户组。</span></div>
            <button type="button" onclick="dprAddDispatchAssignment()">
              + 添加分配
            </button>
          </div>
          <div class="dpr-task-config-cols dpr-dispatch-assignment-cols">
            <span>对象类型</span><span>用户组</span>
            <span>分配条数</span><span></span>
          </div>
          <div id="dprDispatchAssignmentRows"></div>
          <div class="dpr-dispatch-assignment-total">
            <span>分配合计</span>
            <b id="dprDispatchAssignmentTotal">0 / — 条</b>
          </div>
        </div>
        <div class="dpr-inline-notice">
          本次分配只影响当前存量积压数据，不修改流程模板中的用户组配置；
          后续新增数据仍按原有流转与分配规则执行。
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn btn-primary"
          onclick="dprSubmitDispatchResource()">确认分配</button>
      </div>
    </div>

    <div class="drawer dpr-allocation-drawer" id="drawerDispatchBinding">
      <div class="drawer-head">
        <h3>绑定处理任务</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-drawer-summary" id="dprDispatchBindingSummary">—</div>
        <div class="dpr-dispatch-current-card">
          <span>当前状态</span>
          <b>数据已进入数据湖，但尚未命中处理任务</b>
          <small id="dprDispatchBindingSource">—</small>
        </div>
        <div class="fg"><label>优先级</label>
          <select id="dprDispatchBindingPriority">
            <option>P1</option><option>P0</option><option>P2</option>
          </select>
        </div>
        <div class="fg dpr-dispatch-task-picker"><label class="fg-req">处理任务</label>
          <select id="dprDispatchProcessingTask"
            onchange="dprRenderDispatchBindingFlows()">
            <option value="" selected disabled>请选择处理任务</option>
            <option value="20448">20448 · 宁德采集数据处理</option>
            <option value="20447">20447 · 预训练数据质检</option>
            <option value="20446">20446 · Demo 数据处理</option>
          </select>
        </div>
        <div class="dpr-task-config-block dpr-dispatch-binding-flows">
          <div class="dpr-task-config-head">
            <div><b>处理流程</b><span>由所选处理任务自动带出，不支持在此修改。</span></div>
          </div>
          <div class="dpr-task-config-cols dpr-flow-cols">
            <span>业务环节</span><span>处理流程</span><span>版本</span><span>规则</span>
          </div>
          <div id="dprDispatchBindingFlows"></div>
        </div>
        <div class="dpr-inline-notice success">
          确认后，本批数据将从所选处理任务的第一个匹配流程开始处理。
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn btn-primary"
          onclick="dprSubmitDispatchBinding()">确认绑定处理任务</button>
      </div>
    </div>

    <div class="drawer dpr-dispatch-reprocess-drawer" id="drawerDispatchReprocess">
      <div class="drawer-head">
        <h3>发起数据再处理</h3>
        <span class="dismiss" onclick="closeDrawer()">&times;</span>
      </div>
      <div class="drawer-body">
        <div class="dpr-dispatch-steps">
          <span class="active" data-dispatch-step-indicator="1"><b>1</b>筛选数据</span>
          <i></i>
          <span data-dispatch-step-indicator="2"><b>2</b>配置处理任务</span>
        </div>
        <div class="dpr-dispatch-step active" data-dispatch-step="1">
          <div class="dpr-dispatch-filter-grid">
            <div class="ff"><label>recording_id</label>
              <input id="dprDispatchReprocessRecording" placeholder="请输入 recording_id"></div>
            <div class="ff"><label>数据来源</label>
              <select id="dprDispatchReprocessSource"><option value="">全部来源</option>
                <option>采集</option><option>导入</option></select></div>
            <div class="ff"><label>来源任务 ID</label>
              <input id="dprDispatchReprocessTask" placeholder="请输入任务 ID"></div>
            <div class="ff"><label>质检结论</label>
              <select id="dprDispatchReprocessQuality"><option value="">全部结论</option>
                <option>合格</option><option>不合格</option><option>操作失误</option></select></div>
            <div class="ff"><label>标注状态</label>
              <select id="dprDispatchReprocessAnnotation"><option value="">全部状态</option>
                <option>未标注</option><option>已标注</option></select></div>
            <div class="ff"><label>已有处理流程</label>
              <select id="dprDispatchReprocessFlow"><option value="">全部流程</option>
                <option>厨房数据质检流程 v3</option>
                <option>家居动作标注流程 v2</option>
                <option>三方数据导入质检流程 v4</option></select></div>
          </div>
          <div class="dpr-dispatch-filter-actions">
            <button type="button" class="btn btn-tertiary"
              onclick="dprResetDispatchReprocess()">清空</button>
            <button type="button" class="btn btn-primary"
              onclick="dprCalculateDispatchReprocess()">查询</button>
          </div>
          <div class="dpr-dispatch-match">
            <span>符合条件的数据</span>
            <b><em id="dprDispatchReprocessCount">4,218</em> 条</b>
            <small>请确认数据范围后继续</small>
          </div>
          <div class="dpr-dispatch-preview-title">命中数据概览</div>
          __REPROCESS_PREVIEW__
        </div>
        <div class="dpr-dispatch-step" data-dispatch-step="2">
          <div class="dpr-drawer-summary">
            将为 <b id="dprDispatchReprocessConfirmCount">4,218</b> 条数据创建新的处理任务
          </div>
          <div class="fg"><label class="fg-req">任务名称</label>
            <input id="dprDispatchReprocessName" placeholder="请输入再处理任务名称"></div>
          <div class="fg"><label class="fg-req">处理流程</label>
            <select><option>训练数据专项质检流程 v1</option>
              <option>家居动作精标流程 v3</option>
              <option>评测数据复核流程 v2</option></select></div>
          <div class="fg"><label>优先级</label>
            <select><option>P1</option><option>P0</option><option>P2</option></select></div>
          <div class="fg"><label class="fg-req">原流程</label>
            <select id="dprDispatchOriginalFlow"><option>继续</option><option>终止</option></select></div>
          <div class="dpr-inline-notice success">
            新流程独立生成处理记录；原流程是否继续由上方配置决定。
          </div>
        </div>
      </div>
      <div class="drawer-foot">
        <button type="button" class="btn" onclick="closeDrawer()">取消</button>
        <button type="button" class="btn" id="dprDispatchReprocessBack"
          style="display:none" onclick="dprShowDispatchReprocessStep(1)">上一步</button>
        <button type="button" class="btn btn-primary" id="dprDispatchReprocessNext"
          onclick="dprShowDispatchReprocessStep(2)">下一步</button>
        <button type="button" class="btn btn-primary" id="dprDispatchReprocessSubmit"
          style="display:none" onclick="dprSubmitDispatchReprocess()">确认发起</button>
      </div>
    </div>

    <script>
    var dprDispatchProjectStages = __PROJECT_STAGE_DATA__;
    var dprDispatchReprocessCounts = __REPROCESS_COUNTS__;
    var dprDispatchIssueType = 'all';
    var dprDispatchStage = '';
    var dprDispatchResourceBacklog = 0;
    var dprDispatchResourceStage = '';
    var dprDispatchResourceNode = '';
    var dprDispatchAssignmentOptions = {
      '质检': {
        groups: ['质检复核用户组'],
        users: ['包媛桐', '光轮-QC-021']
      },
      '标注': {
        groups: ['标注员用户组', '标注抽验员用户组'],
        users: ['供应商 A-017', '供应商 A-026', '抽验员-008', '抽验员-015']
      },
      '验收': {
        groups: ['内部验收用户组'],
        users: ['joanna.qiao', 'Wei Zhang']
      }
    };
    var dprDispatchProcessingTaskConfigs = {
      '20448': [
        ['质检', '多级质检复核流程', 'v3', '通用质检规则 v3'],
        ['标注', '端到端切分标注流程', 'v2', '通用动作标注规则 v3'],
        ['验收', '数据验收流程', 'v1', '—']
      ],
      '20447': [
        ['质检', '标准训练数据自动质检流程', 'v1', '自动化质检规则 v2'],
        ['标注', '双轮人工标注流程', 'v2', '通用动作标注规则 v3'],
        ['验收', '数据验收流程', 'v1', '—']
      ],
      '20446': [
        ['质检', 'DAgger 数据自动质检流程', 'v1', 'DAgger 质检规则 v1'],
        ['标注', '端到端切分标注流程', 'v2', '端到端切分标注规则 v2'],
        ['验收', '数据验收流程', 'v1', '—']
      ]
    };

    function dprDispatchProject() {
      return document.getElementById('dprDispatchProjectScope').value;
    }
    function dprSetDispatchIssueType(button) {
      document.querySelectorAll('.dpr-dispatch-type-button').forEach(function(item) {
        item.classList.toggle('active', item === button);
      });
      dprDispatchIssueType = button.dataset.issueType;
      dprFilterDispatchIssues();
    }
    function dprSelectDispatchStage(card) {
      var next = card.classList.contains('active') ? '' : card.dataset.dispatchStage;
      dprDispatchStage = next;
      document.querySelectorAll('.dpr-dispatch-stage-card').forEach(function(item) {
        item.classList.toggle('active', item.dataset.dispatchStage === next);
      });
      dprFilterDispatchIssues();
    }
    function dprUpdateDispatchStageCards() {
      var summary = dprDispatchProjectStages[dprDispatchProject()] || [];
      summary.forEach(function(stage) {
        var card = document.querySelector(
          '.dpr-dispatch-stage-card[data-dispatch-stage="' + stage.stage + '"]'
        );
        if(!card) return;
        var total = stage.total || 1;
        card.querySelector('[data-stage-pending]').childNodes[0].nodeValue =
          (stage.unassigned + stage.assigned_waiting).toLocaleString();
        ['unassigned','assigned_waiting','processing','completed'].forEach(function(key) {
          card.querySelector('[data-stage-value="' + key + '"]').textContent =
            stage[key].toLocaleString();
          card.querySelector('[data-dispatch-segment="' + key + '"]').style.width =
            (stage[key] / total * 100) + '%';
        });
      });
    }
    function dprFilterDispatchIssues() {
      var project = dprDispatchProject();
      var query = document.getElementById('dprDispatchTaskQuery').value.trim().toLowerCase();
      var capacityItems = 0;
      var capacityData = 0;
      var unboundItems = 0;
      var unboundData = 0;
      var longest = 0;
      var visible = 0;
      var childRows = Array.from(document.querySelectorAll(
        '#dpr-dispatch-issue-table tbody tr[data-dispatch-role="child"]'
      ));
      document.querySelectorAll(
        '#dpr-dispatch-issue-table tbody tr[data-dispatch-role="parent"]'
      ).forEach(function(row) {
        var stages = (row.dataset.dispatchStages || '').split('|');
        var matches = (project === '全部项目' || row.dataset.dispatchProject === project)
          && (dprDispatchIssueType === 'all' || dprDispatchIssueType === 'capacity')
          && (!dprDispatchStage || stages.indexOf(dprDispatchStage) >= 0)
          && (!query || row.dataset.dispatchTask.toLowerCase().indexOf(query) >= 0);
        row.style.display = matches ? '' : 'none';
        var matchingChildren = childRows.filter(function(child) {
          return child.dataset.dispatchParent === row.dataset.dispatchGroup
            && (!dprDispatchStage || child.dataset.dispatchStage === dprDispatchStage);
        });
        matchingChildren.forEach(function(child) {
          child.style.display = matches && row.dataset.dispatchExpanded === 'true'
            ? '' : 'none';
        });
        childRows.filter(function(child) {
          return child.dataset.dispatchParent === row.dataset.dispatchGroup
            && matchingChildren.indexOf(child) < 0;
        }).forEach(function(child) {
          child.style.display = 'none';
        });
        if(!matches) return;
        visible += 1;
        capacityItems += 1;
        if(dprDispatchStage) {
          matchingChildren.forEach(function(child) {
            capacityData += Number(child.dataset.dispatchCount || 0);
            longest = Math.max(longest, Number(child.dataset.dispatchAge || 0));
          });
        } else {
          capacityData += Number(row.dataset.dispatchCount || 0);
          longest = Math.max(longest, Number(row.dataset.dispatchAge || 0));
        }
      });
      document.querySelectorAll(
        '#dpr-dispatch-issue-table tbody tr[data-dispatch-role="standalone"]'
      ).forEach(function(row) {
        var matches = (project === '全部项目' || row.dataset.dispatchProject === project)
          && (dprDispatchIssueType === 'all' || dprDispatchIssueType === 'unbound')
          && !dprDispatchStage
          && (!query || row.dataset.dispatchTask.toLowerCase().indexOf(query) >= 0);
        row.style.display = matches ? '' : 'none';
        if(!matches) return;
        visible += 1;
        unboundItems += 1;
        unboundData += Number(row.dataset.dispatchCount || 0);
        longest = Math.max(longest, Number(row.dataset.dispatchAge || 0));
      });
      document.getElementById('dprDispatchCapacityItems').textContent = capacityItems;
      document.getElementById('dprDispatchCapacityData').textContent =
        capacityData.toLocaleString();
      document.getElementById('dprDispatchUnboundItems').textContent = unboundItems;
      document.getElementById('dprDispatchUnboundData').textContent =
        unboundData.toLocaleString();
      document.getElementById('dprDispatchLongest').textContent = longest;
      document.getElementById('dprDispatchVisibleCount').textContent = visible;
      document.getElementById('dprDispatchEmpty').style.display = visible ? 'none' : 'block';
    }
    function dprToggleDispatchTask(button) {
      var row = button.closest('tr[data-dispatch-role="parent"]');
      if(!row) return;
      var expanded = row.dataset.dispatchExpanded !== 'true';
      row.dataset.dispatchExpanded = expanded ? 'true' : 'false';
      row.classList.toggle('expanded', expanded);
      var toggle = row.querySelector('.dpr-dispatch-expand-button');
      if(toggle) toggle.textContent = expanded ? '收起' : '展开';
      dprFilterDispatchIssues();
    }
    function dprResetDispatchFilters() {
      document.getElementById('dprDispatchTaskQuery').value = '';
      dprDispatchIssueType = 'all';
      dprDispatchStage = '';
      document.querySelectorAll('.dpr-dispatch-type-button').forEach(function(item) {
        item.classList.toggle('active', item.dataset.issueType === 'all');
      });
      document.querySelectorAll('.dpr-dispatch-stage-card').forEach(function(item) {
        item.classList.remove('active');
      });
      dprFilterDispatchIssues();
    }
    function dprRefreshDispatchPage() {
      dprDispatchStage = '';
      document.querySelectorAll('.dpr-dispatch-stage-card').forEach(function(item) {
        item.classList.remove('active');
      });
      dprUpdateDispatchStageCards();
      dprFilterDispatchIssues();
    }
    function dprOpenDispatchSources(button) {
      var sources = (button.dataset.sources || '').split('|').filter(Boolean);
      document.getElementById('dprDispatchSourceList').innerHTML =
        sources.map(function(taskId) {
          var type = taskId.indexOf('IMP-') === 0 ? '数据导入任务' : '采集任务';
          return '<div><span>' + type + '</span><code>' + taskId + '</code></div>';
        }).join('');
      openDrawer('drawerDispatchSources');
    }
    function dprDispatchTargetOptions(selected) {
      var options = dprDispatchAssignmentOptions[dprDispatchResourceStage] || {
        groups: [], users: []
      };
      return options.groups.map(function(name) {
        return '<option' + (name === selected ? ' selected' : '') + '>' +
          name + '</option>';
      }).join('');
    }
    function dprDispatchAssignmentRow(target, count) {
      return '<div class="dpr-task-config-row dpr-dispatch-assignment-row">' +
        '<select class="dpr-dispatch-assignment-type" disabled ' +
          'title="本期仅支持分配到用户组">' +
          '<option value="group" selected>用户组</option>' +
        '</select>' +
        '<select class="dpr-dispatch-assignment-target">' +
          dprDispatchTargetOptions(target) + '</select>' +
        '<input class="dpr-dispatch-assignment-count" type="number" min="1" ' +
          'max="' + dprDispatchResourceBacklog + '" step="1" value="' +
          (count || '') + '" placeholder="请输入条数" ' +
          'oninput="dprUpdateDispatchAssignmentTotal()">' +
        '<button type="button" class="dpr-task-config-remove" ' +
          'onclick="dprRemoveDispatchAssignment(this)">&times;</button></div>';
    }
    function dprAddDispatchAssignment(target, count) {
      document.getElementById('dprDispatchAssignmentRows').insertAdjacentHTML(
        'beforeend', dprDispatchAssignmentRow(target || '', count || '')
      );
      dprUpdateDispatchAssignmentTotal();
    }
    function dprRemoveDispatchAssignment(button) {
      var holder = document.getElementById('dprDispatchAssignmentRows');
      if(holder.children.length <= 1) {
        toast('至少保留一组分配');
        return;
      }
      button.closest('.dpr-dispatch-assignment-row').remove();
      dprUpdateDispatchAssignmentTotal();
    }
    function dprUpdateDispatchAssignmentTotal() {
      var total = 0;
      document.querySelectorAll('.dpr-dispatch-assignment-count')
        .forEach(function(input) {
          var count = Number(input.value || 0);
          if(Number.isFinite(count) && count > 0) total += count;
        });
      var summary = document.getElementById('dprDispatchAssignmentTotal');
      summary.textContent = total.toLocaleString() + ' / ' +
        dprDispatchResourceBacklog.toLocaleString() + ' 条';
      summary.classList.toggle('over', total > dprDispatchResourceBacklog);
    }
    function dprRenderDispatchBindingFlows() {
      var taskId = document.getElementById('dprDispatchProcessingTask').value;
      var bindings = dprDispatchProcessingTaskConfigs[taskId] || [];
      if(!bindings.length) {
        document.getElementById('dprDispatchBindingFlows').innerHTML =
          '<div class="dpr-task-config-empty">请先选择处理任务</div>';
        return;
      }
      document.getElementById('dprDispatchBindingFlows').innerHTML =
        bindings.map(function(item) {
          return '<div class="dpr-task-config-row dpr-flow-row ' +
            'dpr-dispatch-flow-readonly">' +
            '<b class="dpr-flow-stage-fixed">' + item[0] + '</b>' +
            '<span class="dpr-dispatch-flow-name">' + item[1] + '</span>' +
            '<code class="dpr-flow-version">' + item[2] + '</code>' +
            '<span class="dpr-dispatch-flow-rule">' + item[3] + '</span>' +
            '</div>';
        }).join('');
    }
    function dprOpenDispatchResource(button) {
      dprDispatchResourceBacklog = Number(button.dataset.backlog || 0);
      dprDispatchResourceStage = button.dataset.stage;
      dprDispatchResourceNode = button.dataset.node;
      document.getElementById('dprDispatchResourceSummary').innerHTML =
        '<b>' + button.dataset.processingTask + '</b> · ' +
        button.dataset.node + '节点积压 <b>' +
        dprDispatchResourceBacklog.toLocaleString() + '</b> 条';
      document.getElementById('dprDispatchCurrentFlow').textContent = button.dataset.workflow;
      document.getElementById('dprDispatchCurrentInput').textContent =
        button.dataset.inputRate + ' 条/小时';
      document.getElementById('dprDispatchCurrentThroughput').textContent =
        button.dataset.throughput + ' 条/小时';
      document.getElementById('dprDispatchCurrentBacklog').textContent =
        dprDispatchResourceBacklog.toLocaleString() + ' 条';
      document.getElementById('dprDispatchAssignmentRows').innerHTML = '';
      dprAddDispatchAssignment('', '');
      openDrawer('drawerDispatchResource');
    }
    function dprSubmitDispatchResource() {
      var rows = Array.from(document.querySelectorAll(
        '#dprDispatchAssignmentRows .dpr-dispatch-assignment-row'
      ));
      var assignments = [];
      var targets = {};
      var total = 0;
      for(var index = 0; index < rows.length; index += 1) {
        var row = rows[index];
        var target = row.querySelector('.dpr-dispatch-assignment-target').value;
        var input = row.querySelector('.dpr-dispatch-assignment-count');
        var value = input.value.trim();
        var count = Number(value);
        if(!value || !Number.isInteger(count) || count < 1) {
          toast('第 ' + (index + 1) + ' 组请输入大于 0 的整数条数');
          input.focus();
          return;
        }
        if(!target) {
          toast('第 ' + (index + 1) + ' 组请选择分配对象');
          return;
        }
        if(targets[target]) {
          toast('同一分配对象不能重复添加');
          return;
        }
        targets[target] = true;
        total += count;
        assignments.push({target: target, count: count});
      }
      if(total > dprDispatchResourceBacklog) {
        toast('分配合计不能超过当前积压数量 ' +
          dprDispatchResourceBacklog.toLocaleString() + ' 条');
        return;
      }
      toast('Demo: 已将 ' + total.toLocaleString() + ' 条' +
        dprDispatchResourceNode + '节点的存量积压分配给 ' +
        assignments.length + ' 个对象，增量分配规则保持不变');
      closeDrawer();
    }
    function dprOpenDispatchBinding(button) {
      document.getElementById('dprDispatchBindingSummary').innerHTML =
        '<b>' + button.dataset.sourceTask + '</b> · 待处理 <b>' +
        Number(button.dataset.count).toLocaleString() + '</b> 条';
      document.getElementById('dprDispatchBindingSource').textContent =
        button.dataset.source + '数据 · ' + button.dataset.poolId;
      document.getElementById('dprDispatchProcessingTask').value = '';
      document.getElementById('dprDispatchBindingPriority').value = 'P1';
      dprRenderDispatchBindingFlows();
      openDrawer('drawerDispatchBinding');
    }
    function dprSubmitDispatchBinding() {
      if(!document.getElementById('dprDispatchProcessingTask').value) {
        toast('请选择处理任务');
        document.getElementById('dprDispatchProcessingTask').focus();
        return;
      }
      toast('Demo: 数据已绑定处理任务并开始进入处理链路');
      closeDrawer();
    }
    function dprOpenDispatchReprocess() {
      dprResetDispatchReprocess();
      dprShowDispatchReprocessStep(1);
      openDrawer('drawerDispatchReprocess');
    }
    function dprCalculateDispatchReprocess() {
      var count = dprDispatchReprocessCounts[dprDispatchProject()] || 0;
      var factors = [
        ['dprDispatchReprocessSource', .72],
        ['dprDispatchReprocessQuality', .31],
        ['dprDispatchReprocessAnnotation', .58],
        ['dprDispatchReprocessFlow', .46]
      ];
      factors.forEach(function(item) {
        if(document.getElementById(item[0]).value) count = Math.floor(count * item[1]);
      });
      if(document.getElementById('dprDispatchReprocessTask').value.trim()) {
        count = Math.min(count, 842);
      }
      if(document.getElementById('dprDispatchReprocessRecording').value.trim()) count = 1;
      document.getElementById('dprDispatchReprocessCount').textContent =
        count.toLocaleString();
      document.getElementById('dprDispatchReprocessConfirmCount').textContent =
        count.toLocaleString();
      document.querySelectorAll('#dpr-dispatch-reprocess-preview tbody tr')
        .forEach(function(row) {
          row.style.display = dprDispatchProject() === '全部项目' ||
            row.dataset.project === dprDispatchProject() ? '' : 'none';
        });
    }
    function dprResetDispatchReprocess() {
      ['dprDispatchReprocessSource','dprDispatchReprocessQuality',
       'dprDispatchReprocessAnnotation','dprDispatchReprocessFlow']
        .forEach(function(id) { document.getElementById(id).selectedIndex = 0; });
      document.getElementById('dprDispatchReprocessTask').value = '';
      document.getElementById('dprDispatchReprocessRecording').value = '';
      dprCalculateDispatchReprocess();
    }
    function dprShowDispatchReprocessStep(step) {
      document.querySelectorAll('[data-dispatch-step]').forEach(function(item) {
        item.classList.toggle('active', item.dataset.dispatchStep === String(step));
      });
      document.querySelectorAll('[data-dispatch-step-indicator]').forEach(function(item) {
        item.classList.toggle('active',
          Number(item.dataset.dispatchStepIndicator) <= step);
      });
      document.getElementById('dprDispatchReprocessBack').style.display =
        step === 2 ? '' : 'none';
      document.getElementById('dprDispatchReprocessNext').style.display =
        step === 1 ? '' : 'none';
      document.getElementById('dprDispatchReprocessSubmit').style.display =
        step === 2 ? '' : 'none';
    }
    function dprSubmitDispatchReprocess() {
      if(!document.getElementById('dprDispatchReprocessName').value.trim()) {
        toast('请输入任务名称');
        return;
      }
      var original = document.getElementById('dprDispatchOriginalFlow').value;
      toast(original === '继续'
        ? 'Demo: 已创建新的处理任务，原流程继续'
        : 'Demo: 已创建新的处理任务，原流程终止');
      closeDrawer();
    }
    dprRenderDispatchBindingFlows();
    dprRefreshDispatchPage();
    </script>
    """
    drawers_and_script = (
        drawers_and_script
        .replace("__PROJECT_STAGE_DATA__", project_summary_json)
        .replace("__REPROCESS_COUNTS__", reprocess_counts_json)
        .replace("__REPROCESS_PREVIEW__", reprocess_preview)
    )

    return (
        _intro(
            "分配管理",
            "先查看质检、标注和验收的处理情况，再处理吞吐不足或尚未进入处理链路的数据。",
            "",
            project_switcher,
        )
        + """
        <section class="dpr-section dpr-dispatch-overview">
          <div class="dpr-section-head">
            <div><h2>处理概览</h2>
              <p>点击业务环节，可以筛选下方与该环节相关的待处理事项。</p></div>
          </div>
          <div class="dpr-dispatch-stage-grid">
            __STAGE_CARDS__
          </div>
        </section>
        <div class="dpr-dispatch-alerts">
          <button type="button" class="dpr-dispatch-alert"
            onclick="dprSetDispatchIssueType(document.querySelector('[data-issue-type=capacity]'))">
            <span>处理吞吐不足</span>
            <b><em id="dprDispatchCapacityItems">3</em> 项</b>
            <small>影响 <strong id="dprDispatchCapacityData">508</strong> 条数据</small>
          </button>
          <button type="button" class="dpr-dispatch-alert"
            onclick="dprSetDispatchIssueType(document.querySelector('[data-issue-type=unbound]'))">
            <span>未进入处理</span>
            <b><em id="dprDispatchUnboundItems">3</em> 个批次</b>
            <small>待处理 <strong id="dprDispatchUnboundData">1,484</strong> 条数据</small>
          </button>
          <div class="dpr-dispatch-alert risk">
            <span>最长滞留</span>
            <b><em id="dprDispatchLongest">31</em> 小时</b>
            <small>建议优先处理 P0 事项</small>
          </div>
        </div>
        """
        .replace("__STAGE_CARDS__", stage_cards)
        + _section(
            "待处理事项",
            """
            <div class="dpr-dispatch-toolbar">
              <div class="dpr-dispatch-type-switch" role="tablist">
                <button type="button" class="dpr-dispatch-type-button active"
                  data-issue-type="all" onclick="dprSetDispatchIssueType(this)">全部问题</button>
                <button type="button" class="dpr-dispatch-type-button"
                  data-issue-type="capacity" onclick="dprSetDispatchIssueType(this)">吞吐不足</button>
                <button type="button" class="dpr-dispatch-type-button"
                  data-issue-type="unbound" onclick="dprSetDispatchIssueType(this)">未进入处理</button>
              </div>
              <div class="dpr-dispatch-search">
                <input id="dprDispatchTaskQuery" placeholder="搜索采集/处理任务 ID">
                <button type="button" class="btn btn-tertiary"
                  onclick="dprResetDispatchFilters()">清空</button>
                <button type="button" class="btn btn-primary"
                  onclick="dprFilterDispatchIssues()">查询</button>
              </div>
            </div>
            """
            + issue_table
            + """
            <div class="dpr-dispatch-empty" id="dprDispatchEmpty">当前条件下没有待处理事项</div>
            <div class="dpr-dispatch-table-summary">
              当前显示 <b id="dprDispatchVisibleCount">6</b> 个待处理事项
            </div>
            """,
            "统一展示需要人工决策的问题；数据再处理请使用页面右上角入口。",
        )
        + drawers_and_script
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
    for record_index, record in enumerate(records):
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
            flow_bindings = task.get("flow_bindings", [])
            binding = flow_bindings[record_index % len(flow_bindings)] if flow_bindings else (
                "—",
                "未绑定流程",
                "—",
            )
            stage = binding[0]
            workbench_task = record.get("workbench_task", "WB-2026-0922-AC")
            rows += f"""
        <tr>
          <td><code>{_e(record["id"])}</code></td>
          <td>
            <div class="dpr-video-group" aria-label="三路采集视频">
              <span class="vid-thumb"></span><span class="vid-thumb"></span><span class="vid-thumb"></span>
            </div>
          </td>
          <td><code>{_e(record["device"])}</code></td>
          <td>{_record_tag(record["collection"])}</td>
          <td>{_record_tag(record["quality"])}</td>
          <td>{_record_tag(record["annotation"])}</td>
          <td>{_record_tag(stage)}</td>
          <td>{_e(record["node"])}</td>
          <td class="dpr-record-actions">
            <a href="/data/workbench-v2/edit?mode=annotation&amp;task={_e(workbench_task)}&amp;recording_id={_e(record["id"])}&amp;entry=task-data">查看标注</a>
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
        filter_html = """
      <div class="fb-labeled dpr-record-filters">
        <div class="ff"><label>ID 搜索</label><input placeholder="请输入 recording_id"></div>
        <div class="ff"><label>序列号</label><select><option>请选择设备序列号</option><option>UDAS-007</option><option>Benchmark</option></select></div>
        <div class="ff"><label>操作人</label><select><option>请选择操作类型/操作人</option><option>采集</option><option>质检</option><option>标注</option><option>验收</option></select></div>
        <div class="filter-actions">
          <button class="btn btn-tertiary" onclick="resetFilters(this)">清空</button>
          <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
        </div>
      </div>
        """
    else:
        summary = (
            f'命中 <b>{task.get("input_count", 0):,}</b> 条 · '
            f'已完成 <b>{task.get("processed_count", 0):,}</b> 条 · '
            f'待处理 <b>{task.get("backlog_count", 0):,}</b> 条'
        )
        table_class = "ant-table dpr-record-table"
        table_head = (
            "<th>recording_id</th><th>视频区域（头部 ｜ 左臂 ｜ 右臂）</th><th>序列号</th>"
            "<th>采集结论</th><th>质检结论</th><th>标注状态</th>"
            "<th>当前环节</th><th>当前节点</th><th>操作</th>"
        )
        empty_colspan = 9
        filter_html = """
      <div class="fb-labeled dpr-record-filters">
        <div class="ff"><label>recording_id</label><input placeholder="请输入 recording_id"></div>
        <div class="filter-actions">
          <button class="btn btn-tertiary" onclick="resetFilters(this)">清空</button>
          <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
        </div>
      </div>
        """

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
      {filter_html}
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
            flow_rows = ""
            for flow_index, flow in enumerate(record["flows"]):
                flow_parts = flow["name"].rsplit(" ", 1)
                flow_name = flow_parts[0]
                flow_version = flow_parts[1] if len(flow_parts) > 1 else "v1"
                processing_task_id = (
                    "20454"
                    if flow_index == 0
                    else "20453"
                )
                instance_state = "已完成" if flow["annotation"] == "已标注" else "处理中"
                flow_rows += f"""
                <tr>
                  <td><code>{_e(processing_task_id)}</code></td>
                  <td><a href="/data/runs?task={_e(processing_task_id)}&amp;recording={_e(record["id"])}"><b>{_e(flow_name)}</b></a><br><code>run-{_e(record["id"])}-{flow_index + 1}</code></td>
                  <td><code>{_e(flow_version)}</code></td>
                  <td>{_record_tag(flow["node"])}</td>
                  <td>{_record_tag(instance_state)}</td>
                  <td>{_record_tag(flow["quality"])}</td>
                  <td>{_record_tag("是" if flow["annotation"] == "已标注" else "否")}</td>
                </tr>
                """
            rows += f"""
            <tr class="dpr-record-main-row">
              <td>
                <button type="button" class="dpr-tree-toggle" aria-expanded="false"
                  onclick="dprToggleProcessTree('{_e(row_id)}', this)">&#9656;</button>
                <code>{_e(record["id"])}</code>
              </td>
              <td>{_record_tag(DATA_SOURCE_LABELS[record["source_type"]])}</td>
              <td>
                <div class="dpr-video-group" aria-label="三路采集视频">
                  <span class="vid-thumb"></span><span class="vid-thumb"></span><span class="vid-thumb"></span>
                </div>
              </td>
              <td>{_record_tag(record["upload"])}</td>
              <td>{_record_tag(record["collection"])}</td>
              <td><b>{_e(record["operator"])}</b></td>
              <td>
                <button type="button" class="dpr-flow-link"
                  onclick="dprToggleProcessTree('{_e(row_id)}', this)">
                  {len(record["flows"])} 条 · {_e(record["flows"][0]["name"])}
                </button>
              </td>
              <td class="dpr-record-actions">
                <a href="/data/workbench/edit?mode=detail&amp;task=WB-2026-0922-AC&amp;recording_id={_e(record["id"])}&amp;source=data-management">查看详情</a>
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
                      <th>处理任务</th><th>处理流程</th><th>流程版本</th>
                      <th>当前节点</th><th>处理状态</th>
                      <th>质检结论</th><th>是否标注</th>
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
          <div class="ff"><label>流程 ID</label><input placeholder="请输入流程 ID"></div>
          <div class="filter-actions">
            <button class="btn btn-tertiary" onclick="resetFilters(this)">清空</button>
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
              <th>采集人</th><th>处理流程</th><th>操作</th>
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
    document.getElementById('dprProcessInstanceMeta').innerHTML =
      '<span>处理任务 <code>' + esc(flow.processing_task) + '</code></span>'
      + '<span>流程实例 <code>' + esc(flow.instance_id) + '</code></span>'
      + '<span>流程版本 <b>' + esc(flow.flow_version) + '</b></span>'
      + '<span>实例状态 <b>' + esc(flow.instance_state) + '</b></span>'
      + '<span>当前节点 <b>' + esc(flow.node) + '</b></span>';
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
            "processing_task": (
                "20454" if flow_index == 0 else "20453"
            ),
            "instance_id": f"run-{recording_id}-{flow_index + 1}",
            "flow_version": (
                flow["name"].rsplit(" ", 1)[-1]
                if " " in flow["name"]
                else "v1"
            ),
            "instance_state": (
                "已完成" if flow["annotation"] == "已标注" else "处理中"
            ),
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
        <span>关联处理任务 <b>{len(record["flows"])} 个</b></span>
        <span>流程实例 <b>{len(record["flows"])} 条</b></span>
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
        <div class="dpr-process-instance-meta" id="dprProcessInstanceMeta"></div>
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
        _intro("流程定义", "管理已发布流程和草稿版本。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 新增流程\');return false;">新增流程</a>')
        + _section("流程列表", f'<div class="dpr-pipeline-list">{cards}</div>')
    )


def render_pipeline_runs():
    task_catalog = {
        task["id"]: task
        for task in BUSINESS_TASKS
        if task["type"] == "data_processing_task"
    }
    flow_catalog = {
        definition["published_version"]: definition
        for definition in PIPELINE_DEFINITIONS
    }
    run_catalog = {
        run["id"]: run
        for run in PIPELINE_RUNS
    }
    human_task_by_node_run = {
        task["node_run"]: task
        for task in HUMAN_TASKS
    }
    rows = []
    row_attrs = []
    for run in PIPELINE_RUNS:
        task = task_catalog.get(run["business_task"], {})
        flow = flow_catalog.get(run["pipeline_version"], {})
        recording_ids = run.get("recording_ids", [])
        search_values = [
            run["id"],
            run["project"],
            run["business_task"],
            task.get("name", ""),
            run["pipeline_version"],
            flow.get("name", ""),
            run["input_snapshot"],
            *recording_ids,
        ]
        error = run.get("error")
        state_detail = (
            f'<br><small class="dpr-risk">{_e(error)}</small>'
            if error
            else f'<br><small>{_e(run["duration"])}</small>'
        )
        rows.append(
            [
                (
                    f'<b>{_e(flow.get("name", "未识别流程"))}</b><br>'
                    f'<code>{_e(run["pipeline_version"])}</code><br>'
                    f'<small>{_e(run["id"])}</small>'
                ),
                (
                    f'<a href="/data/tasks/{_e(run["business_task"])}">'
                    f'<b>{_e(task.get("name", run["business_task"]))}</b></a><br>'
                    f'<code>{_e(run["business_task"])}</code> · '
                    f'<small>{_e(run["project"])}</small>'
                ),
                (
                    f'<code>{_e(run["input_snapshot"])}</code><br>'
                    f'<small>{_e(run.get("input_members", "—"))}</small>'
                ),
                f'<b>{_e(run["current_node"])}</b><br><span>{_e(run["node_progress"])}</span>',
                (
                    _state(run["status"])
                    + state_detail
                    + f'<br><small>{_e(run["started"])}</small>'
                ),
                (
                    f'<button type="button" class="dpr-run-open" '
                    f'onclick="dprOpenNodeRuns(\'{_e(run["id"])}\')">'
                    f'查看节点</button>'
                ),
            ]
        )
        row_attrs.append(
            f'class="dpr-execution-run-row" '
            f'data-run-id="{_e(run["id"])}" '
            f'data-run-task="{_e(run["business_task"])}" '
            f'data-run-flow="{_e(run["pipeline_version"])}" '
            f'data-run-status="{_e(run["status"])}" '
            f'data-run-search="{_e(" ".join(search_values).lower())}"'
        )

    node_rows = []
    node_row_attrs = []
    for node_run in NODE_RUNS:
        run = run_catalog.get(node_run["pipeline_run"], {})
        flow = flow_catalog.get(run.get("pipeline_version"), {})
        task = task_catalog.get(run.get("business_task"), {})
        human_task = human_task_by_node_run.get(node_run["id"])
        error = node_run.get("error")
        action = (
            '<a href="#" onclick="toast(\'Demo: 查看节点日志\');return false;">日志</a>'
        )
        if node_run["status"] == "failed":
            action += (
                ' · <a href="#" onclick="toast(\'Demo: 已基于原输入创建新的 Attempt\');'
                'return false;">重试</a>'
            )
        node_rows.append(
            [
                (
                    f'<b>{_e(node_run["node"])}</b><br>'
                    f'<code>{_e(node_run["executor_version"])}</code><br>'
                    f'<small>{_e(node_run["id"])}</small>'
                ),
                (
                    f'<b>{_e(flow.get("name", "未识别流程"))}</b><br>'
                    f'<code>{_e(run.get("pipeline_version", "—"))}</code><br>'
                    f'<small>{_e(node_run["pipeline_run"])}</small>'
                ),
                (
                    f'<code>{_e(node_run["input_snapshot"])}</code>'
                    f'<span class="dpr-io-arrow">→</span>'
                    f'<code>{_e(node_run["output"])}</code>'
                ),
                f'Attempt {node_run["attempt"]}',
                (
                    _state(node_run["status"])
                    + (f'<br><small class="dpr-risk">{_e(error)}</small>' if error else "")
                ),
                action,
            ]
        )
        node_search_values = [
            node_run["id"],
            node_run["node"],
            node_run["executor_version"],
            node_run["pipeline_run"],
            run.get("pipeline_version", ""),
            run.get("business_task", ""),
            task.get("name", ""),
            node_run["input_snapshot"],
            node_run["output"],
            *(run.get("recording_ids") or []),
        ]
        if human_task:
            node_search_values.extend(
                [human_task["id"], human_task["assignee"]]
            )
        node_row_attrs.append(
            f'data-node-parent="{_e(node_run["pipeline_run"])}" '
            f'data-node-status="{_e(node_run["status"])}" '
            f'data-node-search="{_e(" ".join(node_search_values).lower())}"'
        )

    filters = """
    <div class="fb-labeled dpr-task-filters dpr-execution-filters">
      <div class="ff"><label>版本 / 任务 / 运行 ID</label>
        <input id="dprExecutionKeyword" placeholder="请输入关键词"></div>
      <div class="ff"><label>运行状态</label>
        <select id="dprExecutionStatus">
          <option value="">全部状态</option>
          <option value="running">运行中</option>
          <option value="succeeded">已完成</option>
          <option value="failed">失败</option>
        </select>
      </div>
      <div class="filter-actions">
        <button type="button" class="btn btn-tertiary" onclick="dprResetExecutionRuns()">清空</button>
        <button type="button" class="btn btn-primary" onclick="dprFilterExecutionRuns()">查询</button>
      </div>
    </div>
    """
    run_table = _table(
        [
            "流程版本",
            "处理任务 / 项目",
            "输入数据",
            "当前节点 / 进度",
            "状态 / 时间",
            "操作",
        ],
        rows,
        table_id="dpr-execution-run-table",
        row_attrs=row_attrs,
    )
    node_table = _table(
        [
            "节点版本",
            "所属流程版本",
            "输入 → 输出",
            "执行次数",
            "状态 / 异常",
            "操作",
        ],
        node_rows,
        table_id="dpr-node-run-table",
        row_attrs=node_row_attrs,
    )
    script = f"""
    <script>
    var dprExecutionTab = 'flow';
    function dprExecutionRunRows() {{
      return Array.from(document.querySelectorAll('#dpr-execution-run-table tbody tr[data-run-id]'));
    }}
    function dprExecutionNodeRows() {{
      return Array.from(document.querySelectorAll('#dpr-node-run-table tbody tr[data-node-parent]'));
    }}
    function dprSwitchExecutionTab(button, tabName) {{
      dprExecutionTab = tabName;
      document.querySelectorAll('[data-execution-tab]').forEach(function(item) {{
        item.classList.toggle('active', item.dataset.executionTab === tabName);
      }});
      document.querySelectorAll('[data-execution-pane]').forEach(function(pane) {{
        pane.style.display = pane.dataset.executionPane === tabName ? '' : 'none';
      }});
      dprFilterExecutionRuns();
    }}
    function dprFilterExecutionRuns() {{
      var keyword = document.getElementById('dprExecutionKeyword').value.trim().toLowerCase();
      var status = document.getElementById('dprExecutionStatus').value;
      var visibleRuns = [];
      dprExecutionRunRows().forEach(function(row) {{
        var matched = (!keyword || row.dataset.runSearch.indexOf(keyword) >= 0)
          && (!status || row.dataset.runStatus === status);
        row.style.display = matched ? '' : 'none';
        if (matched) visibleRuns.push(row);
      }});
      var visibleNodes = [];
      dprExecutionNodeRows().forEach(function(row) {{
        var matched = (!keyword || row.dataset.nodeSearch.indexOf(keyword) >= 0)
          && (!status || row.dataset.nodeStatus === status);
        row.style.display = matched ? '' : 'none';
        if (matched) visibleNodes.push(row);
      }});
      var visible = dprExecutionTab === 'flow' ? visibleRuns.length : visibleNodes.length;
      var result = document.getElementById('dprExecutionResultCount');
      if (result) result.textContent = '当前展示 ' + visible + ' 条记录';
    }}
    function dprOpenNodeRuns(runId) {{
      document.getElementById('dprExecutionKeyword').value = runId;
      document.getElementById('dprExecutionStatus').value = '';
      var nodeTab = document.querySelector('[data-execution-tab="node"]');
      dprSwitchExecutionTab(nodeTab, 'node');
    }}
    function dprResetExecutionRuns() {{
      document.getElementById('dprExecutionKeyword').value = '';
      document.getElementById('dprExecutionStatus').value = '';
      dprFilterExecutionRuns();
    }}
    document.addEventListener('DOMContentLoaded', function() {{
      var params = new URLSearchParams(window.location.search);
      var keyword = params.get('run') || params.get('recording') || params.get('task') || '';
      var status = params.get('status') || '';
      if (keyword) document.getElementById('dprExecutionKeyword').value = keyword;
      if (status) document.getElementById('dprExecutionStatus').value = status;
      dprFilterExecutionRuns();
    }});
    </script>
    """
    return (
        _intro(
            "执行记录",
            "查看流程与节点的执行状态、版本和异常信息。",
            "",
        )
        + f"""
        <div class="dpr-list-tab-card dpr-execution-tabbar">
          <div class="dpr-task-tabs dpr-execution-tabs" role="tablist">
            <button type="button" class="dpr-task-tab active"
              data-execution-tab="flow"
              onclick="dprSwitchExecutionTab(this,'flow')">
              流程执行记录 <b>{len(PIPELINE_RUNS)}</b>
            </button>
            <button type="button" class="dpr-task-tab"
              data-execution-tab="node"
              onclick="dprSwitchExecutionTab(this,'node')">
              节点执行记录 <b>{len(NODE_RUNS)}</b>
            </button>
          </div>
          <span id="dprExecutionResultCount">当前展示 {len(PIPELINE_RUNS)} 条记录</span>
        </div>
        {filters}
        <div class="dpr-execution-pane" data-execution-pane="flow">
          {run_table}
        </div>
        <div class="dpr-execution-pane" data-execution-pane="node" style="display:none;">
          {node_table}
        </div>
        """
        + script
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
        _intro("工作台 Schema", "管理人工任务使用的工作台界面配置。", "", '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 新增 Schema\');return false;">新增 Schema</a>')
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
        + _section(
            "项目列表",
            _table(["项目名称", "项目描述", "负责人"], rows),
            "统一维护项目基础信息，供采集任务和处理任务选择。",
            (
                '<a class="btn btn-primary" href="#" '
                'onclick="toast(\'Demo: 新建项目\');return false;">'
                "新增项目</a>"
            ),
        )
    )


def _render_workbench_management_legacy():
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
        actions="""<a class="btn btn-primary" href="#" onclick="toast('Demo: 新增工作台');return false;">新增工作台</a>""",
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


def render_workbench_management():
    schema_json = json.dumps(WORKBENCH_SCHEMAS, ensure_ascii=False).replace(
        "</", "<\\/"
    )
    workbench_rows = []
    workbench_row_attrs = []
    management_statuses = {
        "wb.semantic-annotation@1.0": "enabled",
        "wb.quality-review@2.0": "enabled",
        "wb.action-annotation@4.1": "disabled",
        "wb.data-detail@1.0": "draft",
    }
    for schema in WORKBENCH_SCHEMAS:
        business_stage = "验收" if schema["type"] == "详情" else schema["type"]
        workbench_rows.append(
            [
                f'<code>{_e(schema["id"])}</code>',
                f'<b>{_e(schema["name"])}</b>',
                _e(schema.get("description", "")),
                _record_tag(business_stage),
                _state(management_statuses.get(schema["id"], "draft")),
            ]
        )
        workbench_row_attrs.append(
            f'data-workbench-name="{_e(schema["name"])}" '
            f'data-workbench-description="{_e(schema.get("description", ""))}"'
        )

    category_order = ["基础信息", "视频区", "工作区", "处理表单", "结论", "操作栏"]
    component_controls = []
    for category in category_order:
        controls = []
        for component_id, (name, description) in WORKBENCH_COMPONENTS.items():
            meta = WORKBENCH_COMPONENT_META.get(component_id)
            if not meta or meta[0] != category or meta[2] == "legacy":
                continue
            input_type = "radio" if meta[2] == "exclusive" else "checkbox"
            required = meta[2] == "required"
            input_name = f' name="wb-slot-{_e(meta[1])}"' if input_type == "radio" else ""
            controls.append(
                f'<label class="dpr-wb-component-option" data-component-option="{_e(component_id)}">'
                f'<input type="{input_type}"{input_name} value="{_e(component_id)}" '
                f'{"checked disabled" if required else ""} onchange="dprRenderWorkbenchPreview()">'
                f'<span><b>{_e(name)}</b><small>{_e(description)}</small></span></label>'
            )
        if controls:
            component_controls.append(
                f'<div class="dpr-wb-component-group"><h4>{_e(category)}</h4>'
                f'<div>{"".join(controls)}</div></div>'
            )

    component_rows = []
    component_preview_modes = {
        "playback_timeline": "annotation",
        "annotation_segment_editor": "annotation",
        "high_low_editor": "annotation",
        "action_element_editor": "annotation",
        "head_view_video": "detail",
        "quality_result_viewer": "detail",
        "annotation_result_viewer": "detail",
        "tag_viewer": "detail",
    }
    for component_id, (name, description) in WORKBENCH_COMPONENTS.items():
        meta = WORKBENCH_COMPONENT_META.get(component_id, ("其他", "custom", "optional"))
        if meta[2] == "legacy":
            continue
        preview_mode = component_preview_modes.get(component_id, "quality")
        annotation_kind = "semantic" if component_id == "high_low_editor" else "action"
        component_rows.append(
            [
                f'<code>{_e(component_id)}</code>',
                f'<b>{_e(name)}</b>',
                _record_tag(meta[0]),
                _e(description),
                _e(WORKBENCH_COMPONENT_USAGE[component_id]),
                '<span class="dpr-state green">可用</span>',
                (
                    f'<button class="dpr-link-button" '
                    f'onclick="dprOpenComponentPreview('
                    f'\'{_e(component_id)}\',\'{_e(name)}\',\'{preview_mode}\','
                    f'\'{annotation_kind}\')">'
                    f'预览</button>'
                ),
            ]
        )

    return (
        _intro(
            "工作台管理",
            "管理人工执行工作台及其启停状态。",
            "",
            '<button class="btn btn-primary" onclick="dprOpenWorkbenchBuilder(\'new\')">新增工作台</button>',
        )
        + f"""
        <form class="q-filters rule-filter-panel dpr-workbench-filter" onsubmit="dprFilterWorkbenchList(event)">
          <div class="q-filter-row">
            <div class="q-field">
              <label for="workbenchFilterName">工作台名称</label>
              <input id="workbenchFilterName" type="search" placeholder="请输入工作台名称">
            </div>
            <div class="q-actions">
              <button class="btn" type="button" onclick="dprClearWorkbenchFilter()">清空</button>
              <button class="btn btn-primary" type="submit">查询</button>
            </div>
          </div>
        </form>
        {_table(
            ["工作台 ID", "名称", "描述", "业务环节", "状态"],
            workbench_rows,
            table_id="dpr-workbench-table",
            row_attrs=workbench_row_attrs,
            wrap_class="table-wrap",
            table_class="ant-table",
        )}
        <script>
        function dprFilterWorkbenchList(event) {{
          if (event) event.preventDefault();
          var keyword = (document.getElementById('workbenchFilterName').value || '').trim().toLowerCase();
          document.querySelectorAll('#dpr-workbench-table tbody tr[data-workbench-name]').forEach(function(row) {{
            row.style.display = !keyword || row.dataset.workbenchName.toLowerCase().indexOf(keyword) >= 0 ? '' : 'none';
          }});
        }}
        function dprClearWorkbenchFilter() {{
          document.getElementById('workbenchFilterName').value = '';
          dprFilterWorkbenchList();
        }}
        </script>
        <style>
          .dpr-workbench-filter{{margin-bottom:12px;padding:16px 18px}}
          .dpr-workbench-filter .q-filter-row{{align-items:flex-end}}
          .dpr-workbench-filter .q-field input,.dpr-workbench-filter .q-field select{{min-width:220px}}
        </style>
        <div class="drawer dpr-workbench-builder" id="drawerWorkbenchBuilder" data-mode="new">
          <div class="drawer-head">
            <h3 id="workbenchBuilderTitle">新建工作台</h3>
            <span class="dismiss" onclick="closeDrawer()">&times;</span>
          </div>
          <div class="drawer-body">
            <div class="dpr-wb-builder-layout">
              <div class="dpr-wb-builder-form">
                <div class="dpr-wb-basic-grid">
                  <label><span>工作台名称</span><input id="wbBuilderName" placeholder="请输入工作台名称"></label>
                  <label><span>英文标识</span><input id="wbBuilderId" placeholder="workbench.identifier"></label>
                  <label><span>业务类型</span><select id="wbBuilderType">
                    <option>质检</option><option>标注</option><option>验收</option><option>通用</option>
                  </select></label>
                  <label><span>版本</span><input id="wbBuilderVersion" value="v1-draft" disabled></label>
                  <label class="full"><span>描述</span><textarea id="wbBuilderDescription" placeholder="请输入工作台描述"></textarea></label>
                </div>
                <div class="dpr-wb-component-catalog">{"".join(component_controls)}</div>
              </div>
              <div class="dpr-wb-live-preview">
                <div class="dpr-wb-live-head"><b>工作台预览</b></div>
                <div id="workbenchLivePreview" class="dpr-wb-preview-viewport">
                  <iframe id="workbenchPreviewFrame" title="高保真工作台预览"
                    onload="dprFitPreviewFrame(this)"></iframe>
                </div>
              </div>
            </div>
          </div>
          <div class="drawer-foot">
            <button class="btn" onclick="closeDrawer()">取消</button>
            <button class="btn" id="workbenchSaveDraft" onclick="dprSaveWorkbench('draft')">保存草稿</button>
            <button class="btn btn-primary" id="workbenchPublish" onclick="dprSaveWorkbench('publish')">发布工作台</button>
          </div>
        </div>
        <div class="drawer dpr-component-preview-drawer" id="drawerComponentPreview">
          <div class="drawer-head">
            <div>
              <h3 id="componentPreviewTitle">预览组件</h3>
              <p id="componentPreviewDescription">在高保真工作台中查看组件的真实呈现效果</p>
            </div>
            <span class="dismiss" onclick="closeDrawer()">&times;</span>
          </div>
          <div class="drawer-body">
            <div class="dpr-component-preview-browser">
              <iframe id="componentPreviewFrame" title="高保真组件预览"
                onload="dprFitPreviewFrame(this)"></iframe>
            </div>
          </div>
          <div class="drawer-foot">
            <button class="btn" onclick="closeDrawer()">关闭</button>
          </div>
        </div>
        <script>
        var DPR_WORKBENCH_SCHEMAS = {schema_json};
        var DPR_WORKBENCH_PREVIEW_ROUTES = {{
          quality: '/data/workbench-management/preview/quality?task=WB-2026-0718-QC',
          annotation: '/data/workbench-management/preview/annotation?task=WB-2026-0922-LB',
          detail: '/data/workbench-management/preview/detail?task=WB-2026-0922-AC'
        }};
        var DPR_WORKBENCH_PREVIEW_TIMER = null;
        function dprWorkbenchSelectedComponents() {{
          return Array.from(document.querySelectorAll(
            '#drawerWorkbenchBuilder [data-component-option] input:checked'
          )).map(function(input) {{ return input.value; }});
        }}
        function dprWorkbenchPreviewMode() {{
          var type = document.getElementById('wbBuilderType').value;
          return type === '质检' ? 'quality' : (type === '标注' ? 'annotation' : 'detail');
        }}
        function dprWorkbenchPreviewUrl(mode, components, focus, annotationKind) {{
          var url = DPR_WORKBENCH_PREVIEW_ROUTES[mode] || DPR_WORKBENCH_PREVIEW_ROUTES.detail;
          if (mode === 'annotation') {{
            var rule = annotationKind === 'semantic'
              ? '精细动作标注规则 v2（语义标注 E/F/G）'
              : '通用动作标注规则 v1（动作标注 A/B/C/D/Z）';
            url += '&rule=' + encodeURIComponent(rule);
          }}
          url += '&embed=1';
          if (components && components.length) {{
            url += '&components=' + encodeURIComponent(components.join(','));
          }}
          if (focus) {{
            url += '&focus=' + encodeURIComponent(focus);
          }}
          return url;
        }}
        function dprFitPreviewFrame(frame) {{
          if (!frame || !frame.parentElement) return;
          var viewport = frame.parentElement;
          var naturalWidth = 1440;
          var scale = viewport.clientWidth / naturalWidth;
          if (!scale || scale <= 0) return;
          frame.style.width = naturalWidth + 'px';
          frame.style.height = Math.ceil(viewport.clientHeight / scale) + 'px';
          frame.style.transform = 'scale(' + scale + ')';
        }}
        function dprFitAllPreviewFrames() {{
          dprFitPreviewFrame(document.getElementById('workbenchPreviewFrame'));
          dprFitPreviewFrame(document.getElementById('componentPreviewFrame'));
        }}
        function dprRenderWorkbenchPreview() {{
          var selected = dprWorkbenchSelectedComponents();
          var frame = document.getElementById('workbenchPreviewFrame');
          if (!frame) return;
          window.clearTimeout(DPR_WORKBENCH_PREVIEW_TIMER);
          DPR_WORKBENCH_PREVIEW_TIMER = window.setTimeout(function() {{
            frame.src = dprWorkbenchPreviewUrl(
              dprWorkbenchPreviewMode(), selected, '',
              document.getElementById('drawerWorkbenchBuilder').dataset.annotationKind || 'action'
            );
            dprFitPreviewFrame(frame);
          }}, 80);
        }}
        function dprOpenComponentPreview(componentId, componentName, mode, annotationKind) {{
          document.getElementById('componentPreviewTitle').textContent =
            '预览组件 · ' + componentName;
          document.getElementById('componentPreviewDescription').textContent =
            componentId + ' · 在高保真工作台中定位展示';
          document.getElementById('componentPreviewFrame').src =
            dprWorkbenchPreviewUrl(mode, [], componentId, annotationKind || 'action');
          openDrawer('drawerComponentPreview');
        }}
        function dprOpenWorkbenchBuilder(mode, trigger) {{
          var drawer = document.getElementById('drawerWorkbenchBuilder');
          var data = trigger ? trigger.dataset : {{
            workbenchId: '', workbenchName: '', workbenchType: '通用',
            workbenchDescription: '',
            workbenchAnnotationKind: 'action',
            workbenchComponents: JSON.stringify([
              'basic_info','multi_view_video','trajectory_viewer','submit_actions'
            ])
          }};
          var previewOnly = mode === 'preview';
          drawer.dataset.mode = mode;
          drawer.dataset.annotationKind = data.workbenchAnnotationKind || 'action';
          document.getElementById('workbenchBuilderTitle').textContent =
            previewOnly ? '预览工作台' : (mode === 'new' ? '新建工作台' : '编辑工作台');
          document.getElementById('wbBuilderName').value = data.workbenchName || '';
          document.getElementById('wbBuilderId').value = data.workbenchId || '';
          document.getElementById('wbBuilderType').value = data.workbenchType || '通用';
          document.getElementById('wbBuilderDescription').value = data.workbenchDescription || '';
          var selected = [];
          try {{ selected = JSON.parse(data.workbenchComponents || '[]'); }} catch (error) {{}}
          document.querySelectorAll(
            '#drawerWorkbenchBuilder [data-component-option] input').forEach(function(input) {{
              input.checked = input.value === 'basic_info' || selected.indexOf(input.value) >= 0;
              input.disabled = previewOnly || input.value === 'basic_info';
            }});
          drawer.querySelectorAll('.dpr-wb-basic-grid input, .dpr-wb-basic-grid select, .dpr-wb-basic-grid textarea').forEach(
            function(control) {{ control.disabled = previewOnly || control.id === 'wbBuilderVersion'; }}
          );
          document.getElementById('workbenchSaveDraft').style.display = previewOnly ? 'none' : '';
          document.getElementById('workbenchPublish').style.display = previewOnly ? 'none' : '';
          dprRenderWorkbenchPreview();
          openDrawer('drawerWorkbenchBuilder');
        }}
        function dprSaveWorkbench(action) {{
          if (!document.getElementById('wbBuilderName').value.trim()) {{
            toast('请输入工作台名称'); return;
          }}
          var components = dprWorkbenchSelectedComponents();
          if (!components.some(function(id) {{
            return id === 'multi_view_video' || id === 'head_view_video';
          }})) {{ toast('请选择一种视频布局'); return; }}
          if (!components.some(function(id) {{
            return id === 'submit_actions' || id === 'reject_submit_actions';
          }})) {{ toast('请选择一种操作栏'); return; }}
          toast(action === 'publish'
            ? 'Demo: 已发布工作台新版本，节点可选择该版本'
            : 'Demo: 已保存工作台草稿');
          closeDrawer();
        }}
        document.getElementById('wbBuilderType').addEventListener(
          'change', dprRenderWorkbenchPreview
        );
        window.addEventListener('resize', dprFitAllPreviewFrames);
        if (window.ResizeObserver) {{
          var dprPreviewResizeObserver = new ResizeObserver(dprFitAllPreviewFrames);
          dprPreviewResizeObserver.observe(
            document.getElementById('workbenchLivePreview')
          );
          dprPreviewResizeObserver.observe(
            document.querySelector('.dpr-component-preview-browser')
          );
        }}
        </script>
        """
    )


def render_supplier_management():
    suppliers = [
        {
            "id": "SUP-001",
            "name": "光轮智能",
            "status": "enabled",
            "business_stages": ["质检", "标注"],
        },
        {
            "id": "SUP-002",
            "name": "供应商 A",
            "status": "enabled",
            "business_stages": ["标注"],
        },
        {
            "id": "SUP-003",
            "name": "千寻数据",
            "status": "disabled",
            "business_stages": ["质检"],
        },
    ]
    table_rows = "".join(
        f"""
        <tr data-supplier-row data-supplier-name="{_e(item['name'])}" data-supplier-stages="{_e(' '.join(item['business_stages']))}" data-supplier-status="{_e(item['status'])}">
          <td><code>{_e(item['id'])}</code></td>
          <td><b>{_e(item['name'])}</b></td>
          <td><div class="dpr-supplier-stage-tags">{''.join(f'<span>{_e(stage)}</span>' for stage in item['business_stages'])}</div></td>
          <td>{_state(item['status'])}</td>
          <td class="actions-cell"><button type="button" class="dpr-supplier-edit-link" onclick="dprOpenSupplierModal('edit', '{_e(item['id'])}')">编辑</button></td>
        </tr>
        """
        for item in suppliers
    )
    supplier_json = json.dumps(
        {item["id"]: item for item in suppliers}, ensure_ascii=False
    ).replace("</", "<\\/")
    return _intro(
        "供应商管理",
        "管理供应商基础信息与支持的业务环节。",
        "",
        '<button type="button" class="btn btn-primary" onclick="dprOpenSupplierModal(\'new\')">新增供应商</button>',
    ) + f"""
    <form class="q-filters rule-filter-panel dpr-supplier-filter" onsubmit="dprFilterSuppliers(event)">
      <div class="q-filter-row">
        <div class="q-field">
          <label for="dprSupplierNameFilter">供应商名称</label>
          <input id="dprSupplierNameFilter" placeholder="请输入供应商名称">
        </div>
        <div class="q-field">
          <label for="dprSupplierStageFilter">支持业务环节</label>
          <select id="dprSupplierStageFilter"><option value="">全部业务环节</option><option value="质检">质检</option><option value="标注">标注</option></select>
        </div>
        <div class="q-field">
          <label for="dprSupplierStatusFilter">状态</label>
          <select id="dprSupplierStatusFilter"><option value="">全部状态</option><option value="enabled">启用</option><option value="disabled">停用</option></select>
        </div>
        <div class="q-actions">
          <button type="button" class="btn" onclick="dprResetSupplierFilters(this.form)">清空</button>
          <button type="submit" class="btn btn-primary">查询</button>
        </div>
      </div>
    </form>
    <div class="table-wrap">
      <table class="ant-table" id="dprSupplierTable">
        <thead><tr><th>供应商 ID</th><th>供应商名称</th><th>支持业务环节</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>{table_rows}</tbody>
      </table>
    </div>
    <div class="drawer-mask" id="dprSupplierModalMask" onclick="dprCloseSupplierModal(event)">
      <div class="drawer dpr-supplier-drawer" role="dialog" aria-modal="true" aria-labelledby="dprSupplierModalTitle" onclick="event.stopPropagation()">
        <div class="drawer-head"><h3 id="dprSupplierModalTitle">新增供应商</h3><button type="button" class="drawer-close" aria-label="关闭" onclick="dprCloseSupplierModal()">&times;</button></div>
        <div class="drawer-body">
          <div class="dpr-supplier-basic-form">
            <label><span>供应商名称</span><input id="dprSupplierFormName" placeholder="请输入供应商名称"></label>
            <fieldset class="dpr-supplier-stage-field"><legend>支持业务环节</legend><div><label><input type="checkbox" name="dprSupplierBusinessStage" value="质检"><span>质检</span></label><label><input type="checkbox" name="dprSupplierBusinessStage" value="标注"><span>标注</span></label></div></fieldset>
            <label><span>状态</span><select id="dprSupplierFormStatus"><option value="enabled">启用</option><option value="disabled">停用</option></select></label>
          </div>
        </div>
        <div class="drawer-foot"><button type="button" class="btn" onclick="dprCloseSupplierModal()">取消</button><button type="button" class="btn btn-primary" onclick="dprSaveSupplier()">保存</button></div>
      </div>
    </div>
    <style>
    .dpr-supplier-edit-link{{padding:0;border:0;background:transparent;color:#149DAA;font:inherit;cursor:pointer}}
    .dpr-supplier-stage-tags{{display:flex;align-items:center;gap:6px;flex-wrap:wrap}}.dpr-supplier-stage-tags span{{display:inline-flex;padding:2px 8px;border-radius:10px;background:#e8f6f7;color:#147a83;font-size:10.5px}}
    .dpr-supplier-drawer{{width:560px;max-width:calc(100vw - 24px)}}
    .dpr-supplier-modal-close{{padding:0;border:0;background:transparent;color:#7c898e;font-size:22px;line-height:1;cursor:pointer}}
    .dpr-supplier-basic-form{{display:grid;grid-template-columns:minmax(0,1fr) 150px;gap:18px}}
    .dpr-supplier-basic-form label{{display:flex;flex-direction:column;gap:7px;color:#53666d;font-size:12px}}
    .dpr-supplier-basic-form input,.dpr-supplier-basic-form select{{height:38px;box-sizing:border-box;padding:0 10px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#304850}}
    .dpr-supplier-stage-field{{grid-column:1/-1;margin:0;padding:0;border:0}}.dpr-supplier-stage-field legend{{margin-bottom:7px;color:#53666d;font-size:12px}}.dpr-supplier-stage-field>div{{display:flex;gap:10px}}.dpr-supplier-stage-field label{{display:inline-flex;flex-direction:row;align-items:center;gap:7px;min-width:90px;padding:9px 12px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;cursor:pointer}}.dpr-supplier-stage-field label:has(input:checked){{border-color:#69bdc5;background:#f1fbfb;color:#147a83}}.dpr-supplier-stage-field input{{width:14px;height:14px;padding:0}}
    @media(max-width:900px){{.dpr-supplier-basic-form{{grid-template-columns:1fr}}}}
    </style>
    <script>
    var DPR_SUPPLIER_DATA = {supplier_json};
    function dprSupplierEscape(value) {{
      return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
    }}
    function dprOpenSupplierModal(mode, supplierId) {{
      var supplier = mode === 'edit' ? DPR_SUPPLIER_DATA[supplierId] : null;
      document.getElementById('dprSupplierModalTitle').textContent = supplier ? '编辑供应商' : '新增供应商';
      document.getElementById('dprSupplierFormName').value = supplier ? supplier.name : '';
      document.getElementById('dprSupplierFormStatus').value = supplier ? supplier.status : 'enabled';
      document.querySelectorAll('[name="dprSupplierBusinessStage"]').forEach(function(input) {{ input.checked = !!(supplier && supplier.business_stages.indexOf(input.value) >= 0); }});
      document.getElementById('dprSupplierModalMask').classList.add('active');
    }}
    function dprCloseSupplierModal(event) {{
      if (event && event.target !== document.getElementById('dprSupplierModalMask')) return;
      document.getElementById('dprSupplierModalMask').classList.remove('active');
    }}
    function dprSaveSupplier() {{
      if (!document.getElementById('dprSupplierFormName').value.trim()) {{ toast('请输入供应商名称'); return; }}
      if (!document.querySelector('[name="dprSupplierBusinessStage"]:checked')) {{ toast('请至少选择一个支持业务环节'); return; }}
      toast('Demo: 已保存供应商信息');
      dprCloseSupplierModal();
    }}
    function dprFilterSuppliers(event) {{
      event.preventDefault();
      var keyword = document.getElementById('dprSupplierNameFilter').value.trim().toLowerCase();
      var stage = document.getElementById('dprSupplierStageFilter').value;
      var status = document.getElementById('dprSupplierStatusFilter').value;
      document.querySelectorAll('[data-supplier-row]').forEach(function(row) {{
        var matchesName = !keyword || row.dataset.supplierName.toLowerCase().indexOf(keyword) >= 0;
        var matchesStage = !stage || String(row.dataset.supplierStages || '').split(' ').indexOf(stage) >= 0;
        var matchesStatus = !status || row.dataset.supplierStatus === status;
        row.style.display = matchesName && matchesStage && matchesStatus ? '' : 'none';
      }});
    }}
    function dprResetSupplierFilters(form) {{
      form.reset();
      document.querySelectorAll('[data-supplier-row]').forEach(function(row) {{ row.style.display = ''; }});
    }}
    </script>
    """


def _render_user_group_section():
    group_rows = []
    row_attrs = []
    for group in USER_GROUPS:
        group_rows.append(
            [
                f'<code>{_e(group["id"])}</code>',
                f'<b data-user-group-name>{_e(group["name"])}</b>',
                f'<div class="dpr-stage-tags">{"".join(f"<span>{_e(stage)}</span>" for stage in group.get("business_stages", []))}</div>',
                f'<span class="dpr-member-count" data-user-group-members>{group["members"]} 人</span>',
                f'<span data-user-group-status>{_state(group.get("status", "enabled"))}</span>',
                f'<button type="button" class="dpr-user-group-edit-link" onclick="dprOpenUserGroupDrawer(\'{_e(group["id"])}\')">编辑</button>',
            ]
        )
        row_attrs.append(
            f'data-user-group-row="{_e(group["id"])}" '
            f'data-user-group-name="{_e(group["name"])}" '
            f'data-user-group-stages="{_e(" ".join(group.get("business_stages", [])))}" '
            f'data-user-group-status="{_e(group.get("status", "enabled"))}"'
        )
    return _table(
        ["用户组标识", "用户组名称", "支持业务环节", "成员", "状态", "操作"],
        group_rows,
        table_id="dprUserGroupTable",
        row_attrs=row_attrs,
    )


def render_user_group_management():
    member_options = [
        {"id": "USR-2105", "name": "joanna.qiao", "organization": "平台自有"},
        {"id": "USR-2217", "name": "刘素粉", "organization": "光轮智能"},
        {"id": "USR-2240", "name": "包媛桐", "organization": "平台自有"},
        {"id": "USR-2298", "name": "供应商 A-017", "organization": "供应商 A"},
        {"id": "USR-2301", "name": "Wei Zhang", "organization": "平台自有"},
        {"id": "USR-2306", "name": "供应商 A-026", "organization": "供应商 A"},
        {"id": "USR-2312", "name": "标注抽验-008", "organization": "平台自有"},
        {"id": "USR-2318", "name": "光轮-QC-021", "organization": "光轮智能"},
        {"id": "USR-2321", "name": "王一帆", "organization": "平台自有"},
        {"id": "USR-2328", "name": "陈晨", "organization": "平台自有"},
        {"id": "USR-2335", "name": "lance li", "organization": "平台自有"},
        {"id": "USR-2341", "name": "标注员-041", "organization": "供应商 A"},
        {"id": "USR-2346", "name": "标注员-046", "organization": "供应商 A"},
        {"id": "USR-2350", "name": "标注员-050", "organization": "光轮智能"},
        {"id": "USR-2357", "name": "质检员-057", "organization": "光轮智能"},
        {"id": "USR-2363", "name": "质检员-063", "organization": "光轮智能"},
        {"id": "USR-2368", "name": "复核员-068", "organization": "平台自有"},
        {"id": "USR-2372", "name": "复核员-072", "organization": "平台自有"},
        {"id": "USR-2379", "name": "验收员-079", "organization": "平台自有"},
        {"id": "USR-2384", "name": "验收员-084", "organization": "平台自有"},
        {"id": "USR-2390", "name": "标注员-090", "organization": "联合项目组"},
        {"id": "USR-2394", "name": "标注员-094", "organization": "联合项目组"},
        {"id": "USR-2397", "name": "质检员-097", "organization": "光轮智能"},
        {"id": "USR-2401", "name": "质检员-101", "organization": "平台自有"},
    ]
    group_payload = {}
    for index, group in enumerate(USER_GROUPS):
        selected_members = [
            member_options[(index * 3 + offset) % len(member_options)]["id"]
            for offset in range(group["members"])
        ]
        group_payload[group["id"]] = {
            **group,
            "member_ids": selected_members,
        }
    groups_json = json.dumps(group_payload, ensure_ascii=False).replace("</", "<\\/")
    member_options_json = json.dumps(member_options, ensure_ascii=False).replace(
        "</", "<\\/"
    )
    return (
        _intro(
            "用户组管理",
            "管理人工节点的领取范围；同一用户组的多个节点汇入共享任务池。",
            "",
            '<button type="button" class="btn btn-primary" onclick="dprOpenNewUserGroupModal()">新增用户组</button>',
            inline_action=True,
        )
        + """
    <form class="q-filters rule-filter-panel dpr-user-group-filter" onsubmit="dprFilterUserGroups(event)">
      <div class="q-filter-row">
        <div class="q-field"><label for="dprUserGroupNameFilter">用户组名称</label><input id="dprUserGroupNameFilter" placeholder="请输入用户组名称"></div>
        <div class="q-field"><label for="dprUserGroupStageFilter">支持业务环节</label><select id="dprUserGroupStageFilter"><option value="">全部业务环节</option><option value="质检">质检</option><option value="标注">标注</option></select></div>
        <div class="q-field"><label for="dprUserGroupStatusFilter">状态</label><select id="dprUserGroupStatusFilter"><option value="">全部状态</option><option value="enabled">启用</option><option value="disabled">停用</option></select></div>
        <div class="q-actions"><button type="button" class="btn" onclick="dprResetUserGroupFilters(this.form)">清空</button><button type="submit" class="btn btn-primary">查询</button></div>
      </div>
    </form>
        """
        + _render_user_group_section()
        + f"""
    <div class="drawer-mask" id="dprNewUserGroupModalMask" onclick="dprCloseNewUserGroupModal(event)">
      <div class="drawer dpr-new-user-group-drawer" role="dialog" aria-modal="true" aria-labelledby="dprNewUserGroupModalTitle" onclick="event.stopPropagation()">
        <div class="drawer-head"><h3 id="dprNewUserGroupModalTitle">新增用户组</h3><button type="button" class="drawer-close" aria-label="关闭" onclick="dprCloseNewUserGroupModal()">&times;</button></div>
        <div class="drawer-body">
          <div class="dpr-new-user-group-basic">
            <label><span><i>*</i>标识</span><input id="dprNewUserGroupIdent" placeholder="例如 group.annotation-review"></label>
            <label><span><i>*</i>名称</span><input id="dprNewUserGroupName" placeholder="请输入用户组名称"></label>
            <fieldset class="dpr-new-user-group-stages"><legend><i>*</i>支持业务环节</legend><div><label><input type="checkbox" name="dprNewUserGroupStage" value="质检"><span>质检</span></label><label><input type="checkbox" name="dprNewUserGroupStage" value="标注"><span>标注</span></label></div></fieldset>
          </div>
          <section class="dpr-new-user-group-members">
            <div class="dpr-new-user-group-section-head"><div><h4>成员管理</h4><p>成员创建后也可以在编辑用户组中继续调整</p></div><span id="dprNewUserGroupMemberCount">0 人</span></div>
            <div class="dpr-user-group-member-toolbar"><input id="dprNewUserGroupMemberKeyword" type="search" placeholder="请输入姓名或人员 ID 搜索" oninput="dprSearchNewUserGroupMembers()"><button type="button" class="btn dpr-new-user-group-add-member" onclick="dprToggleNewUserGroupMemberPicker()">+ 添加成员</button></div>
            <div class="table-wrap"><table class="ant-table dpr-new-user-group-member-table"><thead><tr><th>姓名</th><th>操作</th></tr></thead><tbody id="dprNewUserGroupMemberRows"></tbody></table></div>
            <div class="dpr-new-user-group-member-picker" id="dprNewUserGroupMemberPicker">
              <div id="dprNewUserGroupMemberChoices"></div>
            </div>
          </section>
        </div>
        <div class="drawer-foot"><button type="button" class="btn" onclick="dprCloseNewUserGroupModal()">取消</button><button type="button" class="btn btn-primary" onclick="dprSaveNewUserGroup()">保存</button></div>
      </div>
    </div>
    <div class="drawer-mask" id="dprUserGroupDrawerMask" onclick="dprCloseUserGroupDrawer(event)">
      <div class="drawer dpr-user-group-drawer" role="dialog" aria-modal="true" aria-labelledby="dprUserGroupDrawerTitle" onclick="event.stopPropagation()">
        <div class="drawer-head"><h3 id="dprUserGroupDrawerTitle">编辑用户组</h3><button type="button" class="drawer-close" aria-label="关闭" onclick="dprCloseUserGroupDrawer()">&times;</button></div>
        <div class="drawer-body">
          <div class="fg"><label for="dprUserGroupFormIdent">用户组标识</label><input id="dprUserGroupFormIdent" disabled></div>
          <div class="fg"><label for="dprUserGroupFormName"><span class="req">*</span>用户组名称</label><input id="dprUserGroupFormName" placeholder="请输入用户组名称"></div>
          <div class="fg"><label for="dprUserGroupFormStatus">状态</label><select id="dprUserGroupFormStatus"><option value="enabled">启用</option><option value="disabled">停用</option></select></div>
          <div class="fg dpr-user-group-members-field">
            <div class="dpr-user-group-members-head"><label for="dprUserGroupMemberSearch">成员</label><span id="dprUserGroupSelectedCount">已选 0 人</span></div>
            <div class="dpr-user-group-member-toolbar"><input id="dprUserGroupMemberSearch" type="search" placeholder="请输入姓名或人员 ID 搜索" oninput="dprFilterUserGroupMembers(this.value)"><button type="button" class="btn" onclick="dprToggleUserGroupMemberPicker()">+ 添加成员</button></div>
            <div class="table-wrap"><table class="ant-table dpr-user-group-member-table"><thead><tr><th>姓名</th><th>操作</th></tr></thead><tbody id="dprUserGroupMemberRows"></tbody></table></div>
            <div class="dpr-user-group-member-picker" id="dprUserGroupMemberPicker"><div class="dpr-user-group-member-options" id="dprUserGroupMemberOptions"></div></div>
          </div>
        </div>
        <div class="drawer-foot"><button type="button" class="btn" onclick="dprCloseUserGroupDrawer()">取消</button><button type="button" class="btn btn-primary" onclick="dprSaveUserGroup()">保存</button></div>
      </div>
    </div>
    <style>
    .dpr-user-group-edit-link{{padding:0;border:0;background:transparent;color:#149DAA;font:inherit;cursor:pointer}}
    .dpr-new-user-group-drawer{{width:560px;max-width:calc(100vw - 24px)}}
    .dpr-new-user-group-basic{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
    .dpr-new-user-group-basic>label{{display:flex;flex-direction:column;gap:7px;color:#53666d;font-size:12px}}.dpr-new-user-group-basic>label span i,.dpr-new-user-group-stages legend i{{margin-right:3px;color:#d4504e;font-style:normal}}
    .dpr-new-user-group-basic input{{height:38px;box-sizing:border-box;padding:0 10px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#304850}}
    .dpr-new-user-group-stages{{grid-column:1/-1;margin:0;padding:0;border:0}}.dpr-new-user-group-stages legend{{margin-bottom:7px;color:#53666d;font-size:12px}}.dpr-new-user-group-stages>div{{display:flex;gap:10px}}.dpr-new-user-group-stages label{{display:inline-flex;align-items:center;gap:7px;min-width:90px;padding:9px 12px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#53666d;font-size:12px;cursor:pointer}}.dpr-new-user-group-stages label:has(input:checked){{border-color:#69bdc5;background:#f1fbfb;color:#147a83}}.dpr-new-user-group-stages input{{width:14px;height:14px;margin:0;accent-color:#149DAA}}
    .dpr-new-user-group-members{{margin-top:24px;padding-top:20px;border-top:1px solid #e7edef}}.dpr-new-user-group-section-head{{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:10px}}.dpr-new-user-group-section-head h4{{margin:0;color:#304850;font-size:13px}}.dpr-new-user-group-section-head p{{margin:4px 0 0;color:#8a979c;font-size:10.5px}}.dpr-new-user-group-section-head>span{{color:#149DAA;font-size:11.5px}}
    .dpr-new-user-group-member-table th:last-child,.dpr-new-user-group-member-table td:last-child{{width:76px;text-align:right}}.dpr-new-user-group-member-name b,.dpr-new-user-group-member-name small{{display:block}}.dpr-new-user-group-member-name b{{color:#344c54;font-size:12px}}.dpr-new-user-group-member-name small{{margin-top:3px;color:#8a979c;font-size:10px}}.dpr-new-user-group-remove-member{{padding:0;border:0;background:transparent;color:#d1524b;font-size:11.5px;cursor:pointer}}.dpr-new-user-group-member-empty{{padding:24px!important;color:#8b989d!important;text-align:center!important}}
    .dpr-user-group-member-toolbar{{display:flex;align-items:center;gap:8px;margin-bottom:10px}}.dpr-user-group-member-toolbar input{{flex:1;min-width:0;height:36px;box-sizing:border-box;padding:0 10px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#304850}}.dpr-user-group-member-toolbar .btn{{flex:none;height:36px;white-space:nowrap}}.dpr-new-user-group-member-picker,.dpr-user-group-member-picker{{display:none;margin-top:10px;padding:10px;border:1px solid #dce4e6;border-radius:7px;background:#fafcfc}}.dpr-new-user-group-member-picker.active,.dpr-user-group-member-picker.active{{display:block}}.dpr-new-user-group-member-picker>div,.dpr-user-group-member-picker>div{{display:grid;grid-template-columns:1fr 1fr;gap:7px;max-height:190px;overflow-y:auto}}.dpr-new-user-group-member-choice{{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 10px;border:1px solid #e1e7e9;border-radius:6px;background:#fff;color:#405860;text-align:left;cursor:pointer}}.dpr-new-user-group-member-choice:hover{{border-color:#9bd2d6;background:#f1fbfb}}.dpr-new-user-group-member-choice span{{min-width:0}}.dpr-new-user-group-member-choice b,.dpr-new-user-group-member-choice small{{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.dpr-new-user-group-member-choice b{{font-size:11.5px}}.dpr-new-user-group-member-choice small{{margin-top:3px;color:#8a979c;font-size:9.5px}}.dpr-new-user-group-picker-empty{{grid-column:1/-1;padding:18px;color:#8a979c;text-align:center;font-size:11px}}
    .dpr-user-group-drawer{{width:560px;max-width:calc(100vw - 24px)}}
    .dpr-user-group-drawer .fg{{margin-bottom:20px}}.dpr-user-group-drawer .fg>input,.dpr-user-group-drawer .fg>select{{height:38px;box-sizing:border-box}}
    .dpr-user-group-members-head{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:7px}}.dpr-user-group-members-head label{{margin:0}}.dpr-user-group-members-head span{{color:#149DAA;font-size:11.5px}}
    .dpr-user-group-member-table th:last-child,.dpr-user-group-member-table td:last-child{{width:76px;text-align:right}}.dpr-user-group-member-table .dpr-new-user-group-member-name b,.dpr-user-group-member-table .dpr-new-user-group-member-name small{{display:block}}.dpr-user-group-member-options{{display:grid;grid-template-columns:1fr 1fr;gap:7px;padding:0;max-height:280px;overflow-y:auto}}
    .dpr-user-group-member-search-empty{{grid-column:1/-1;padding:22px;color:#8a979c;text-align:center;font-size:11px}}
    .dpr-user-group-member-option{{display:grid;grid-template-columns:16px minmax(0,1fr);gap:8px;align-items:start;padding:8px;border:1px solid transparent;border-radius:6px;background:#fff;cursor:pointer}}.dpr-user-group-member-option:has(input:checked){{border-color:#9bd2d6;background:#f1fbfb}}.dpr-user-group-member-option input{{width:14px;height:14px;margin:2px 0 0;accent-color:#149DAA}}.dpr-user-group-member-option b,.dpr-user-group-member-option small{{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.dpr-user-group-member-option b{{color:#344c54;font-size:11.5px}}.dpr-user-group-member-option small{{margin-top:3px;color:#89969b;font-size:9.5px}}
    @media(max-width:700px){{.dpr-new-user-group-basic{{grid-template-columns:1fr}}.dpr-new-user-group-stages{{grid-column:auto}}.dpr-new-user-group-member-picker>div,.dpr-user-group-member-options{{grid-template-columns:1fr}}}}
    </style>
    <script>
    var DPR_USER_GROUP_DATA = {groups_json};
    var DPR_USER_GROUP_MEMBER_OPTIONS = {member_options_json};
    var dprEditingUserGroupId = '';
    var DPR_EDIT_USER_GROUP_MEMBER_IDS = [];
    var DPR_NEW_USER_GROUP_MEMBER_IDS = [];
    var dprNewUserGroupSearchTimer = null;
    function dprUserGroupEscape(value) {{
      return String(value == null ? '' : value).replace(/[&<>"']/g, function(character) {{ return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[character]; }});
    }}
    function dprFilterUserGroups(event) {{
      event.preventDefault();
      var keyword = document.getElementById('dprUserGroupNameFilter').value.trim().toLowerCase();
      var stage = document.getElementById('dprUserGroupStageFilter').value;
      var status = document.getElementById('dprUserGroupStatusFilter').value;
      document.querySelectorAll('[data-user-group-row]').forEach(function(row) {{
        var matchesName = !keyword || String(row.dataset.userGroupName || '').toLowerCase().indexOf(keyword) >= 0;
        var matchesStage = !stage || String(row.dataset.userGroupStages || '').split(' ').indexOf(stage) >= 0;
        var matchesStatus = !status || row.dataset.userGroupStatus === status;
        row.style.display = matchesName && matchesStage && matchesStatus ? '' : 'none';
      }});
    }}
    function dprResetUserGroupFilters(form) {{
      form.reset();
      document.querySelectorAll('[data-user-group-row]').forEach(function(row) {{ row.style.display = ''; }});
    }}
    function dprNewUserGroupMemberById(memberId) {{
      return DPR_USER_GROUP_MEMBER_OPTIONS.find(function(member) {{ return member.id === memberId; }});
    }}
    function dprRenderNewUserGroupMembers() {{
      var holder = document.getElementById('dprNewUserGroupMemberRows');
      document.getElementById('dprNewUserGroupMemberCount').textContent = DPR_NEW_USER_GROUP_MEMBER_IDS.length + ' 人';
      holder.innerHTML = DPR_NEW_USER_GROUP_MEMBER_IDS.length ? DPR_NEW_USER_GROUP_MEMBER_IDS.map(function(memberId) {{
        var member = dprNewUserGroupMemberById(memberId);
        if (!member) return '';
        return '<tr><td><div class="dpr-new-user-group-member-name"><b>' + dprUserGroupEscape(member.name) + '</b><small>' + dprUserGroupEscape(member.id) + ' · ' + dprUserGroupEscape(member.organization) + '</small></div></td><td><button type="button" class="dpr-new-user-group-remove-member" data-member-id="' + dprUserGroupEscape(member.id) + '" onclick="dprRemoveNewUserGroupMember(this.dataset.memberId)">移除</button></td></tr>';
      }}).join('') : '<tr><td colspan="2" class="dpr-new-user-group-member-empty">暂未添加成员</td></tr>';
      dprRenderNewUserGroupMemberPicker();
    }}
    function dprRenderNewUserGroupMemberPicker() {{
      var keywordElement = document.getElementById('dprNewUserGroupMemberKeyword');
      var keyword = keywordElement ? keywordElement.value.trim().toLowerCase() : '';
      if (!keyword) {{
        document.getElementById('dprNewUserGroupMemberChoices').innerHTML = '<div class="dpr-new-user-group-picker-empty">请输入姓名或人员 ID 后搜索成员</div>';
        return;
      }}
      var available = DPR_USER_GROUP_MEMBER_OPTIONS.filter(function(member) {{
        var search = (member.name + ' ' + member.id + ' ' + member.organization).toLowerCase();
        return DPR_NEW_USER_GROUP_MEMBER_IDS.indexOf(member.id) < 0 && search.indexOf(keyword) >= 0;
      }});
      document.getElementById('dprNewUserGroupMemberChoices').innerHTML = available.length ? available.map(function(member) {{
        return '<button type="button" class="dpr-new-user-group-member-choice" data-member-id="' + dprUserGroupEscape(member.id) + '" onclick="dprAddNewUserGroupMember(this.dataset.memberId)"><span><b>' + dprUserGroupEscape(member.name) + '</b><small>' + dprUserGroupEscape(member.id) + ' · ' + dprUserGroupEscape(member.organization) + '</small></span><small>添加</small></button>';
      }}).join('') : '<div class="dpr-new-user-group-picker-empty">没有搜索到可添加的成员</div>';
    }}
    function dprSearchNewUserGroupMembers() {{
      clearTimeout(dprNewUserGroupSearchTimer);
      var holder = document.getElementById('dprNewUserGroupMemberChoices');
      var keyword = document.getElementById('dprNewUserGroupMemberKeyword').value.trim();
      if (!keyword) {{ dprRenderNewUserGroupMemberPicker(); return; }}
      holder.innerHTML = '<div class="dpr-new-user-group-picker-empty">正在搜索...</div>';
      dprNewUserGroupSearchTimer = setTimeout(dprRenderNewUserGroupMemberPicker, 250);
    }}
    function dprToggleNewUserGroupMemberPicker() {{
      var picker = document.getElementById('dprNewUserGroupMemberPicker');
      picker.classList.toggle('active');
      if (picker.classList.contains('active')) {{ document.getElementById('dprNewUserGroupMemberKeyword').focus(); dprRenderNewUserGroupMemberPicker(); }}
    }}
    function dprAddNewUserGroupMember(memberId) {{
      if (DPR_NEW_USER_GROUP_MEMBER_IDS.indexOf(memberId) < 0) DPR_NEW_USER_GROUP_MEMBER_IDS.push(memberId);
      document.getElementById('dprNewUserGroupMemberKeyword').value = '';
      dprRenderNewUserGroupMembers();
    }}
    function dprRemoveNewUserGroupMember(memberId) {{
      DPR_NEW_USER_GROUP_MEMBER_IDS = DPR_NEW_USER_GROUP_MEMBER_IDS.filter(function(item) {{ return item !== memberId; }});
      dprRenderNewUserGroupMembers();
    }}
    function dprOpenNewUserGroupModal() {{
      DPR_NEW_USER_GROUP_MEMBER_IDS = [];
      document.getElementById('dprNewUserGroupIdent').value = '';
      document.getElementById('dprNewUserGroupName').value = '';
      document.querySelectorAll('[name="dprNewUserGroupStage"]').forEach(function(input) {{ input.checked = false; }});
      document.getElementById('dprNewUserGroupMemberKeyword').value = '';
      document.getElementById('dprNewUserGroupMemberPicker').classList.remove('active');
      dprRenderNewUserGroupMembers();
      document.getElementById('dprNewUserGroupModalMask').classList.add('active');
      document.getElementById('dprNewUserGroupIdent').focus();
    }}
    function dprCloseNewUserGroupModal(event) {{
      if (event && event.target !== document.getElementById('dprNewUserGroupModalMask')) return;
      document.getElementById('dprNewUserGroupModalMask').classList.remove('active');
    }}
    function dprSaveNewUserGroup() {{
      var identifier = document.getElementById('dprNewUserGroupIdent').value.trim();
      var name = document.getElementById('dprNewUserGroupName').value.trim();
      var stages = Array.from(document.querySelectorAll('[name="dprNewUserGroupStage"]:checked')).map(function(input) {{ return input.value; }});
      if (!identifier) {{ toast('请输入用户组标识'); return; }}
      if (!/^[A-Za-z0-9._-]+$/.test(identifier)) {{ toast('用户组标识仅支持英文、数字、点、中划线和下划线'); return; }}
      if (DPR_USER_GROUP_DATA[identifier]) {{ toast('用户组标识已存在'); return; }}
      if (!name) {{ toast('请输入用户组名称'); return; }}
      if (!stages.length) {{ toast('请至少选择一个支持业务环节'); return; }}
      var group = {{id:identifier,name:name,business_stages:stages,members:DPR_NEW_USER_GROUP_MEMBER_IDS.length,member_ids:DPR_NEW_USER_GROUP_MEMBER_IDS.slice(),status:'enabled'}};
      DPR_USER_GROUP_DATA[identifier] = group;
      var stageHtml = stages.map(function(stage) {{ return '<span>' + dprUserGroupEscape(stage) + '</span>'; }}).join('');
      document.querySelector('#dprUserGroupTable tbody').insertAdjacentHTML('afterbegin','<tr data-user-group-row="' + dprUserGroupEscape(identifier) + '" data-user-group-name="' + dprUserGroupEscape(name) + '" data-user-group-stages="' + dprUserGroupEscape(stages.join(' ')) + '" data-user-group-status="enabled"><td><code>' + dprUserGroupEscape(identifier) + '</code></td><td><b data-user-group-name>' + dprUserGroupEscape(name) + '</b></td><td><div class="dpr-stage-tags">' + stageHtml + '</div></td><td><span class="dpr-member-count" data-user-group-members>' + group.members + ' 人</span></td><td><span data-user-group-status><span class="dpr-state green">启用</span></span></td><td><button type="button" class="dpr-user-group-edit-link" data-user-group-id="' + dprUserGroupEscape(identifier) + '" onclick="dprOpenUserGroupDrawer(this.dataset.userGroupId)">编辑</button></td></tr>');
      toast('Demo: 已新增用户组');
      dprCloseNewUserGroupModal();
    }}
    function dprRenderUserGroupMembers(selectedIds, keyword) {{
      if (selectedIds) DPR_EDIT_USER_GROUP_MEMBER_IDS = selectedIds.slice();
      var searchKeyword = String(keyword == null ? document.getElementById('dprUserGroupMemberSearch').value : keyword).trim().toLowerCase();
      var memberRows = document.getElementById('dprUserGroupMemberRows');
      var selectedMembers = DPR_EDIT_USER_GROUP_MEMBER_IDS.map(dprNewUserGroupMemberById).filter(Boolean);
      memberRows.innerHTML = selectedMembers.length ? selectedMembers.map(function(member) {{
        return '<tr><td><div class="dpr-new-user-group-member-name"><b>' + dprUserGroupEscape(member.name) + '</b><small>' + dprUserGroupEscape(member.id) + ' · ' + dprUserGroupEscape(member.organization) + '</small></div></td><td><button type="button" class="dpr-new-user-group-remove-member" data-member-id="' + dprUserGroupEscape(member.id) + '" onclick="dprRemoveUserGroupMember(this.dataset.memberId)">移除</button></td></tr>';
      }}).join('') : '<tr><td colspan="2" class="dpr-new-user-group-member-empty">暂未添加成员</td></tr>';
      var options = DPR_USER_GROUP_MEMBER_OPTIONS.filter(function(member) {{
        var search = (member.name + ' ' + member.id + ' ' + member.organization).toLowerCase();
        return (!searchKeyword || search.indexOf(searchKeyword) >= 0) && DPR_EDIT_USER_GROUP_MEMBER_IDS.indexOf(member.id) < 0;
      }});
      document.getElementById('dprUserGroupMemberOptions').innerHTML = options.length ? options.map(function(member) {{
        var search = (member.name + ' ' + member.id + ' ' + member.organization).toLowerCase();
        return '<label class="dpr-user-group-member-option" data-member-search="' + dprUserGroupEscape(search) + '"><input type="checkbox" name="dprUserGroupMember" value="' + dprUserGroupEscape(member.id) + '" onchange="dprToggleUserGroupMember(this)"><span><b>' + dprUserGroupEscape(member.name) + '</b><small>' + dprUserGroupEscape(member.id) + ' · ' + dprUserGroupEscape(member.organization) + '</small></span></label>';
      }}).join('') : '<div class="dpr-user-group-member-search-empty">' + (searchKeyword ? '没有搜索到成员' : '当前用户组暂无成员，请先搜索后添加') + '</div>';
      dprUpdateUserGroupMemberCount();
    }}
    function dprUpdateUserGroupMemberCount() {{
      var count = DPR_EDIT_USER_GROUP_MEMBER_IDS.length;
      document.getElementById('dprUserGroupSelectedCount').textContent = '已选 ' + count + ' 人';
    }}
    function dprToggleUserGroupMember(input) {{
      if (input.checked && DPR_EDIT_USER_GROUP_MEMBER_IDS.indexOf(input.value) < 0) DPR_EDIT_USER_GROUP_MEMBER_IDS.push(input.value);
      if (!input.checked) DPR_EDIT_USER_GROUP_MEMBER_IDS = DPR_EDIT_USER_GROUP_MEMBER_IDS.filter(function(item) {{ return item !== input.value; }});
      dprRenderUserGroupMembers(null, document.getElementById('dprUserGroupMemberSearch').value);
    }}
    function dprRemoveUserGroupMember(memberId) {{
      DPR_EDIT_USER_GROUP_MEMBER_IDS = DPR_EDIT_USER_GROUP_MEMBER_IDS.filter(function(item) {{ return item !== memberId; }});
      dprRenderUserGroupMembers(null, document.getElementById('dprUserGroupMemberSearch').value);
    }}
    function dprFilterUserGroupMembers(keyword) {{
      if (String(keyword || '').trim()) document.getElementById('dprUserGroupMemberPicker').classList.add('active');
      dprRenderUserGroupMembers(null, keyword);
    }}
    function dprToggleUserGroupMemberPicker() {{
      var picker = document.getElementById('dprUserGroupMemberPicker');
      picker.classList.toggle('active');
      if (picker.classList.contains('active')) {{ document.getElementById('dprUserGroupMemberSearch').focus(); dprRenderUserGroupMembers(null, document.getElementById('dprUserGroupMemberSearch').value); }}
    }}
    function dprOpenUserGroupDrawer(groupId) {{
      var group = DPR_USER_GROUP_DATA[groupId];
      if (!group) return;
      dprEditingUserGroupId = groupId;
      document.getElementById('dprUserGroupFormIdent').value = group.id;
      document.getElementById('dprUserGroupFormName').value = group.name;
      document.getElementById('dprUserGroupFormStatus').value = group.status || 'enabled';
      document.getElementById('dprUserGroupMemberSearch').value = '';
      document.getElementById('dprUserGroupMemberPicker').classList.remove('active');
      dprRenderUserGroupMembers(group.member_ids || []);
      document.getElementById('dprUserGroupDrawerMask').classList.add('active');
    }}
    function dprCloseUserGroupDrawer(event) {{
      if (event && event.target !== document.getElementById('dprUserGroupDrawerMask')) return;
      document.getElementById('dprUserGroupDrawerMask').classList.remove('active');
    }}
    function dprSaveUserGroup() {{
      var group = DPR_USER_GROUP_DATA[dprEditingUserGroupId];
      var name = document.getElementById('dprUserGroupFormName').value.trim();
      if (!group || !name) {{ toast('请输入用户组名称'); return; }}
      var memberIds = DPR_EDIT_USER_GROUP_MEMBER_IDS.slice();
      group.name = name;
      group.member_ids = memberIds;
      group.members = memberIds.length;
      group.status = document.getElementById('dprUserGroupFormStatus').value;
      var row = Array.from(document.querySelectorAll('[data-user-group-row]')).find(function(item) {{ return item.dataset.userGroupRow === dprEditingUserGroupId; }});
      if (row) {{
        row.dataset.userGroupName = group.name;
        row.dataset.userGroupStatus = group.status;
        row.querySelector('[data-user-group-name]').textContent = group.name;
        row.querySelector('[data-user-group-members]').textContent = group.members + ' 人';
        row.querySelector('[data-user-group-status]').innerHTML = group.status === 'enabled' ? '<span class="dpr-state green">启用</span>' : '<span class="dpr-state orange">停用</span>';
      }}
      toast('Demo: 已保存用户组');
      dprCloseUserGroupDrawer();
    }}
    </script>
    """
    )


def render_personnel_management():
    rows = [
        ["USR-2105", "<b>joanna.qiao</b>", "平台自有", "标注抽验员用户组 · 内部验收用户组", "标注 · 验收", "工作中", "2026-07-27 10:42", '<a href="#">详情</a>'],
        ["USR-2217", "<b>刘素粉</b>", "光轮智能", "质检复核用户组", "数据质检", "工作中", "2026-07-27 10:35", '<a href="#">详情</a>'],
        ["USR-2240", "<b>包媛桐</b>", "平台自有", "质检复核用户组", "数据质检", "在线", "2026-07-27 10:38", '<a href="#">详情</a>'],
        ["USR-2298", "<b>供应商 A-017</b>", "供应商 A", "标注员用户组", "动作标注", "离线", "2026-07-26 18:12", '<a href="#">详情</a>'],
    ]
    personnel_table = _table(
        ["人员 ID", "姓名", "归属", "所属用户组", "技能", "状态", "最近活跃", "操作"],
        rows,
    )
    return (
        _intro(
            "人员管理",
            "管理人员、技能、状态与供应商归属。",
            "",
            '<a class="btn btn-primary" href="#" onclick="toast(\'Demo: 添加人员\');return false;">+ 添加人员</a>',
            inline_action=True,
        )
        + personnel_table
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
        ["RES-USER-GROUP", "用户组", "group.*", "查看 · 编辑成员 · 绑定节点"],
        ["RES-TASK-POOL", "任务池", "POOL-*", "查看 · 领取 · 转派"],
        ["RES-DATASET", "数据集", "dataset.*", "查看 · 构建 · 发布"],
        ["RES-CONFIG", "配置", "规则 / 场景 / 标签", "查看 · 编辑"],
    ]
    grant_rows = [
        ["AUTH-001", "ROLE-DATA-ADMIN", "PRJ-MOZ1-SFT-07", "管理", "joanna.qiao", "长期有效"],
        ["AUTH-002", "ROLE-OPERATOR", "20453", "执行", "数据工厂管理员", "2026-08-05"],
        ["AUTH-003", "ROLE-VENDOR", "COL-2026-0718", "执行", "joanna.qiao", "2026-07-31"],
    ]
    role_section = (
        '<div class="dpr-tab-list-actions"><a class="btn btn-primary" href="#" '
        'onclick="toast(\'Demo: 新增角色\');return false;">新增角色</a></div>'
        + _table(["角色 ID", "角色名称", "成员", "数据范围", "更新时间", "操作"], role_rows)
    )
    resource_section = _table(
        ["资源类型", "资源名称", "资源标识", "可授权动作"], resource_rows
    )
    grant_section = (
        '<div class="dpr-tab-list-actions"><a class="btn btn-primary" href="#" '
        'onclick="toast(\'Demo: 新增授权\');return false;">新增授权</a></div>'
        + _table(["授权 ID", "角色", "资源", "权限", "授权人", "有效期"], grant_rows)
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
        <style>.dpr-tab-list-actions{{display:flex;justify-content:flex-end;margin:0 0 12px}}</style>
        """
    )


def render_allocation_management_v2():
    return """
    <style>
      .dpr-v2-filter-required label:after{content:" *";color:#d4504e}.dpr-v2-resource-summary{display:grid;grid-template-columns:1.35fr repeat(3,1fr);gap:0;margin:-5px 0 16px;border:1px solid #e3eaec;border-radius:8px;background:#f8fafb;overflow:hidden}.dpr-v2-capacity-fact{display:flex;flex-direction:column;gap:5px;min-width:0;padding:12px 14px;border-right:1px solid #e3eaec}.dpr-v2-capacity-fact:last-child{border-right:0}.dpr-v2-capacity-fact span{color:#819096;font-size:10.5px}.dpr-v2-capacity-fact strong{overflow:hidden;color:#2d464e;font-size:16px;line-height:1.25;text-overflow:ellipsis;white-space:nowrap}.dpr-v2-task-title-line{display:flex;align-items:center;gap:10px}.dpr-v2-capacity-button{display:none;height:30px;padding:0 11px;border-color:#149daa!important;background:#fff!important;color:#147a83!important;font-size:11px}.dpr-v2-capacity-button:hover{border-color:#0f7f89!important;background:#f2fbfb!important;color:#0f7f89!important}
      .dpr-v2-shell{display:grid;grid-template-columns:270px minmax(0,1fr);min-height:620px;border:1px solid #e3eaec;border-radius:10px;background:#fff;overflow:hidden}.dpr-v2-resource-pane{border-right:1px solid #e6edef;background:#fbfcfc}.dpr-v2-resource-head{padding:18px 18px 12px;border-bottom:1px solid #e8edef}.dpr-v2-resource-head h2,.dpr-v2-task-head h2{margin:0;color:#20383f;font-size:16px}.dpr-v2-resource-head p,.dpr-v2-task-head p{margin:5px 0 0;color:#7a898f;font-size:12px}.dpr-v2-tabs{display:flex;gap:18px;margin-top:16px}.dpr-v2-tabs button{position:relative;padding:0 0 10px;border:0;background:transparent;color:#728188;font-size:13px;cursor:pointer}.dpr-v2-tabs button.active{color:#149daa;font-weight:650}.dpr-v2-tabs button.active:after{content:"";position:absolute;right:0;bottom:0;left:0;height:2px;background:#149daa}.dpr-v2-resource-list{padding:10px}.dpr-v2-resource{display:flex;align-items:center;justify-content:space-between;gap:8px;width:100%;margin-bottom:4px;padding:11px 10px;border:1px solid transparent;border-radius:7px;background:transparent;color:#405860;text-align:left;cursor:pointer}.dpr-v2-resource:hover{background:#f0f8f8}.dpr-v2-resource.active{border-color:#b8dfe2;background:#eaf7f7;color:#147a83}.dpr-v2-resource b{font-size:12px}.dpr-v2-resource span{color:#89969b;font-size:11px}.dpr-v2-task-pane{min-width:0;padding:20px 22px;background:#fff}.dpr-v2-task-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:16px}.dpr-v2-task-count{color:#149daa;font-size:12px}.dpr-v2-task-list{display:flex;flex-direction:column;gap:10px;min-height:250px}.dpr-v2-task{display:grid;grid-template-columns:minmax(0,1fr) auto!important;align-items:center;gap:12px;padding:14px;border:1px solid #e2eaec;border-radius:8px;background:#fff;cursor:default}.dpr-v2-task.dragging{opacity:.45}.dpr-v2-task.paused{background:#fafbfb}.dpr-v2-task-main{min-width:0;width:100%}.dpr-v2-task-title{display:flex;align-items:center;gap:8px;min-width:0;width:100%;color:#2d464e;font-size:13px;font-weight:650;line-height:1.45;white-space:nowrap;overflow:hidden;writing-mode:horizontal-tb}.dpr-v2-task-name{min-width:0;flex:0 1 auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.dpr-v2-task-status{flex:0 0 auto;padding:2px 6px;border-radius:8px;background:#e7f6ee;color:#2f8064;font-size:10px;white-space:nowrap}.dpr-v2-task-status.paused{background:#f1f3f4;color:#7e8b90}.dpr-v2-task-main{min-width:0}.dpr-v2-task-action{width:96px;box-sizing:border-box;padding:6px 10px;border:1px solid #d8e2e4;border-radius:5px;background:#fff;color:#536970;font-size:11px;text-align:center;cursor:pointer}.dpr-v2-task-action:hover{border-color:#149daa;color:#147a83}.dpr-v2-drag-handle{color:#a5b0b4;font-size:18px;text-align:center;cursor:grab}.dpr-v2-empty{padding:55px 20px;color:#8a979c;text-align:center;font-size:12px;border:1px dashed #dce5e7;border-radius:8px}@media(max-width:820px){.dpr-v2-shell{grid-template-columns:1fr}.dpr-v2-resource-pane{border-right:0;border-bottom:1px solid #e6edef}.dpr-v2-resource-list{display:flex;gap:6px;overflow:auto}.dpr-v2-resource{min-width:190px}}
      .dpr-v2-task-facts{display:grid;grid-template-columns:minmax(155px,1.15fr) minmax(105px,.8fr) 56px minmax(250px,1.7fr);align-items:end;gap:12px;margin-top:9px;white-space:nowrap}.dpr-v2-task-fact{display:flex;flex-direction:column;gap:3px;min-width:0}.dpr-v2-task-fact i{color:#93a0a5;font-size:10px;font-style:normal}.dpr-v2-task-fact b{overflow:hidden;color:#536970;font-size:11.5px;font-weight:500;text-overflow:ellipsis;white-space:nowrap}.dpr-v2-task-priority{align-items:flex-start}.dpr-v2-priority{display:inline-flex!important;align-items:center;align-self:flex-start;width:auto!important;min-width:34px;padding:3px 8px;border-radius:5px;font-size:11px!important;font-weight:650!important;text-align:center}.dpr-v2-priority[class~="1"],.dpr-v2-priority[class~="2"],.dpr-v2-priority[class~="3"]{background:#e6f4f8;color:#147b99!important}.dpr-v2-priority[class~="4"],.dpr-v2-priority[class~="5"],.dpr-v2-priority[class~="6"]{background:#fff3d9;color:#ad6800!important}.dpr-v2-priority[class~="7"],.dpr-v2-priority[class~="8"],.dpr-v2-priority[class~="9"]{background:#fdeceb;color:#cf3f38!important}.dpr-v2-progress{width:100%;min-width:250px}.dpr-v2-progress .dpr-task-progress-line{width:100%;min-width:250px;white-space:nowrap}.dpr-v2-progress .dpr-task-progress-line b{white-space:nowrap}.dpr-v2-task-actions{display:flex;flex-direction:column;align-items:flex-end;gap:7px}.dpr-v2-task-limit-summary{color:#7c8b91;font-size:10px;white-space:nowrap}.dpr-v2-task-limit-summary.full{color:#c24f45;font-weight:650}.dpr-v2-task-status.capacity-full{background:#fdeceb;color:#b34239}.dpr-v2-capacity-modal{width:860px}.dpr-v2-capacity-context{margin-bottom:12px;color:#61747b;font-size:12px}.dpr-v2-capacity-context b{color:#2f4850}.dpr-v2-capacity-rules{margin-bottom:12px;padding:10px 12px;border-left:3px solid #e5a64c;border-radius:5px;background:#fff8e8;color:#76591f;font-size:11px;line-height:1.65}.dpr-v2-capacity-table input,.dpr-v2-capacity-table select{width:100%;height:34px;box-sizing:border-box;padding:0 8px;border:1px solid #d8e0e3;border-radius:6px;background:#fff}.dpr-v2-capacity-table input:disabled,.dpr-v2-capacity-table select:disabled{border-color:#e4e8e9;background:#f3f5f5;color:#8b969a}.dpr-v2-capacity-period-inputs{display:grid;grid-template-columns:1fr 16px 1fr;align-items:center;gap:6px}.dpr-v2-capacity-period-inputs span{text-align:center;color:#8b989d}.dpr-v2-capacity-kind{display:inline-flex;padding:3px 8px;border-radius:10px;font-size:10px;font-weight:650;white-space:nowrap}.dpr-v2-capacity-kind.history{background:#edf0f1;color:#6e7c82}.dpr-v2-capacity-kind.current{background:#e7f6ee;color:#2f8064}.dpr-v2-capacity-kind.future{background:#e6f4f8;color:#147b99}.dpr-v2-capacity-row-remove{padding:0;border:0;background:transparent;color:#9aa6aa;font-size:18px;cursor:pointer}.dpr-v2-capacity-row-remove:disabled{color:#ccd3d5;cursor:not-allowed}.dpr-v2-capacity-add{margin-top:10px;padding:0;border:0;background:transparent;color:#149daa;cursor:pointer}.dpr-v2-limit-modal{width:480px}.dpr-v2-limit-form{display:flex;flex-direction:column;gap:8px}.dpr-v2-limit-form label{color:#596d74;font-size:12px}.dpr-v2-limit-input{display:grid;grid-template-columns:1fr 54px;align-items:center;gap:8px}.dpr-v2-limit-input input{height:38px;box-sizing:border-box;padding:0 10px;border:1px solid #d8e0e3;border-radius:6px}.dpr-v2-limit-input span{color:#52676e}.dpr-v2-limit-help{margin:4px 0 0;color:#869399;font-size:11px;line-height:1.5}
      .dpr-v2-node-progress-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.dpr-v2-node-progress-head b{color:#536970;font-size:11px;font-weight:600}.dpr-v2-contribution-bar{display:flex;width:100%;height:7px;margin-top:5px;border-radius:4px;background:#edf2f3;overflow:hidden}.dpr-v2-contribution-bar i{display:block;height:100%}.dpr-v2-contribution-current{background:#149daa}.dpr-v2-contribution-other{background:#8fc8ce}.dpr-v2-contribution-legend{display:flex;align-items:center;gap:12px;margin-top:5px;color:#7c8b91;font-size:9.5px;white-space:nowrap}.dpr-v2-contribution-legend span{display:inline-flex;align-items:center;gap:4px}.dpr-v2-contribution-legend i{width:6px;height:6px;border-radius:50%;background:#cfd9dc}.dpr-v2-contribution-legend .current i{background:#149daa}.dpr-v2-contribution-legend .other i{background:#8fc8ce}.dpr-v2-page-head{display:flex;align-items:center;justify-content:flex-start;gap:18px}.dpr-v2-stage-filter{display:flex;align-items:center;height:36px;padding:0 4px 0 12px;border:1px solid #aebfc3;border-radius:7px;background:transparent}.dpr-v2-stage-filter:hover,.dpr-v2-stage-filter:focus-within{border-color:#149daa;background:transparent;box-shadow:0 0 0 2px rgba(20,157,170,.09)}.dpr-v2-stage-filter label{margin:0;color:#527078;font-size:12px;font-weight:500;white-space:nowrap}.dpr-v2-stage-filter select{height:34px;min-width:126px;padding:0 28px 0 9px;border:0;background:transparent;color:#126f78;font-size:13px;font-weight:650;outline:0;box-shadow:none}
    </style>
    <style>.dpr-v2-capacity-add{display:block;margin:0 0 10px}</style>
    <div class="dpr-intro dpr-v2-page-head"><h1>分配管理</h1><div class="dpr-v2-stage-filter"><label for="dprV2FilterStage">处理环节</label><select id="dprV2FilterStage" onchange="dprV2FilterStageChanged(this)"><option value="质检">质检环节</option><option value="标注">标注环节</option></select></div></div>
    <div class="q-filters rule-filter-panel dpr-v2-filter-panel"><div class="q-filter-row"><div class="q-field"><label for="dprV2FilterFlow">处理任务</label><select id="dprV2FilterFlow" onchange="dprV2FilterFlowChanged(this)"><option value="">全部处理任务</option></select></div><div class="q-field"><label for="dprV2FilterNode">节点</label><select id="dprV2FilterNode" onchange="dprV2FilterChanged()"><option value="">全部节点</option></select></div><div class="q-actions"><button type="button" class="btn" onclick="dprV2ClearFilters()">清空</button><button type="button" class="btn btn-primary" onclick="dprV2Query()">查询</button></div></div></div>
    <div class="dpr-v2-shell"><aside class="dpr-v2-resource-pane"><div class="dpr-v2-resource-head"><h2>处理资源</h2><p>选择供应商或用户组查看进产能分布</p><div class="dpr-v2-tabs"><button class="active" data-v2-type="supplier" onclick="dprV2SwitchType(this)">供应商</button><button data-v2-type="user_group" onclick="dprV2SwitchType(this)">用户组</button></div></div><div class="dpr-v2-resource-list" id="dprV2ResourceList"></div></aside><section class="dpr-v2-task-pane"><div class="dpr-v2-task-head"><div><div class="dpr-v2-task-title-line"><h2 id="dprV2TaskTitle">正在处理中的任务</h2><button type="button" class="btn dpr-v2-capacity-button" id="dprV2CapacityButton" onclick="dprV2OpenCapacityModal()">产能分配</button></div><p>任务优先级相同，优先分配靠前的任务；暂停会停止分配，不会停止数据流入</p></div><span class="dpr-v2-task-count" id="dprV2TaskCount"></span></div><div class="dpr-v2-resource-summary" id="dprV2ResourceSummary"><div class="dpr-v2-capacity-fact"><span>当前周期</span><strong id="dprV2CapacityPeriod">—</strong></div><div class="dpr-v2-capacity-fact"><span>总产能</span><strong id="dprV2CapacityTotal">—</strong></div><div class="dpr-v2-capacity-fact"><span>已消耗产能</span><strong id="dprV2CapacityConsumed">—</strong></div><div class="dpr-v2-capacity-fact"><span>剩余产能</span><strong id="dprV2CapacityRemaining">—</strong></div></div><div class="dpr-v2-task-list" id="dprV2TaskList"></div></section></div>
    <div class="modal-mask" id="dprV2CapacityModalMask" onclick="dprV2CloseCapacityModal(event)"><div class="modal dpr-v2-capacity-modal" role="dialog" aria-modal="true" aria-labelledby="dprV2CapacityModalTitle" onclick="event.stopPropagation()"><div class="modal-head"><h3 id="dprV2CapacityModalTitle">产能分配</h3><button type="button" class="dpr-supplier-modal-close" aria-label="关闭" onclick="dprV2CloseCapacityModal()">&times;</button></div><div class="modal-body"><div class="dpr-v2-capacity-context" id="dprV2CapacityContext"></div><div class="dpr-v2-capacity-rules">历史周期不可修改；当前周期截止时间不得晚于今天，产能不得小于已消耗产能；未来周期开始时间须晚于当前周期。</div><div class="table-wrap"><table class="ant-table dpr-v2-capacity-table"><thead><tr><th>周期类型</th><th>周期</th><th>计量单位</th><th>产能</th><th></th></tr></thead><tbody id="dprV2CapacityRows"></tbody></table></div><button type="button" class="dpr-v2-capacity-add" onclick="dprV2AddCapacityRow()">+ 增加表格行</button></div><div class="modal-foot"><button type="button" class="btn" onclick="dprV2CloseCapacityModal()">取消</button><button type="button" class="btn btn-primary" onclick="dprV2SaveCapacity()">保存</button></div></div></div>
    <div class="modal-mask" id="dprV2LimitModalMask" onclick="dprV2CloseLimitModal(event)"><div class="modal dpr-v2-limit-modal" role="dialog" aria-modal="true" aria-labelledby="dprV2LimitModalTitle" onclick="event.stopPropagation()"><div class="modal-head"><h3 id="dprV2LimitModalTitle">设置产能分配上限</h3><button type="button" class="dpr-supplier-modal-close" aria-label="关闭" onclick="dprV2CloseLimitModal()">&times;</button></div><div class="modal-body"><div class="dpr-v2-capacity-context" id="dprV2LimitContext"></div><div class="dpr-v2-limit-form"><label for="dprV2LimitValue">产能分配上限</label><div class="dpr-v2-limit-input"><input id="dprV2LimitValue" type="number" min="0" step="1" placeholder="请输入非负整数"><span id="dprV2LimitUnit">—</span></div><p class="dpr-v2-limit-help">达到上限后，工作台内将不再能领取当前处理任务。</p></div></div><div class="modal-foot"><button type="button" class="btn" onclick="dprV2CloseLimitModal()">取消</button><button type="button" class="btn btn-primary" onclick="dprV2SaveTaskLimit()">保存</button></div></div></div>
    <script>
    var DPR_V2_DATA={supplier:[{id:'光轮智能',count:'2 个任务',tasks:[{name:'厨房数据质检流程 · 供应商复核',stage:'质检',progress:'96 / 240 条',status:'processing'},{name:'三方数据导入质检流程 · 格式校验',stage:'质检',progress:'138 / 388 条',status:'processing'}]},{id:'供应商 A',count:'2 个任务',tasks:[{name:'端到端切分标注流程 · 供应商标注',stage:'标注',progress:'186 / 420 条',status:'processing'},{name:'双轮人工标注流程 · 标注抽验',stage:'标注',progress:'74 / 186 条',status:'processing'}]},{id:'千寻数据',count:'1 个任务',tasks:[{name:'动作标注流程 · 供应商抽验',stage:'标注',progress:'42 / 120 条',status:'processing'}]}],user_group:[{id:'质检复核用户组',count:'2 个任务',tasks:[{name:'厨房数据质检流程 · 完整性质检',stage:'质检',progress:'128 / 260 条',status:'processing'},{name:'三方数据导入质检流程 · Schema 校验',stage:'质检',progress:'96 / 180 条',status:'processing'}]},{id:'标注员用户组',count:'2 个任务',tasks:[{name:'端到端切分标注流程 · 动作分段标注',stage:'标注',progress:'220 / 510 条',status:'processing'},{name:'双轮人工标注流程 · 初轮标注',stage:'标注',progress:'88 / 220 条',status:'processing'}]},{id:'标注抽验员用户组',count:'1 个任务',tasks:[{name:'双轮人工标注流程 · 标注抽验',stage:'标注',progress:'31 / 90 条',status:'processing'}]}]};var DPR_V2_OTHER_CONTRIBUTIONS={'厨房数据质检流程 · 供应商复核':36,'三方数据导入质检流程 · 格式校验':72,'端到端切分标注流程 · 供应商标注':74,'双轮人工标注流程 · 标注抽验':46,'动作标注流程 · 供应商抽验':28,'厨房数据质检流程 · 完整性质检':48,'三方数据导入质检流程 · Schema 校验':36,'端到端切分标注流程 · 动作分段标注':105,'双轮人工标注流程 · 初轮标注':62,'双轮人工标注流程 · 标注抽验':24};var DPR_V2_TASK_HOURS={'厨房数据质检流程 · 供应商复核':18.5,'三方数据导入质检流程 · 格式校验':21,'端到端切分标注流程 · 供应商标注':32.5,'双轮人工标注流程 · 标注抽验':14,'动作标注流程 · 供应商抽验':9.5,'厨房数据质检流程 · 完整性质检':24,'三方数据导入质检流程 · Schema 校验':17.5,'端到端切分标注流程 · 动作分段标注':38,'双轮人工标注流程 · 初轮标注':16.5,'双轮人工标注流程 · 标注抽验':8};var DPR_V2_TASK_DATES={'厨房数据质检流程 · 供应商复核':'2026-08-01','三方数据导入质检流程 · 格式校验':'2026-08-02','端到端切分标注流程 · 供应商标注':'2026-08-03','双轮人工标注流程 · 标注抽验':'2026-08-04','动作标注流程 · 供应商抽验':'2026-08-03','厨房数据质检流程 · 完整性质检':'2026-08-01','三方数据导入质检流程 · Schema 校验':'2026-08-02','端到端切分标注流程 · 动作分段标注':'2026-08-03','双轮人工标注流程 · 初轮标注':'2026-08-04','双轮人工标注流程 · 标注抽验':'2026-08-04'};var DPR_V2_TYPE='supplier',DPR_V2_STAGE='质检',DPR_V2_FILTER_FLOW='',DPR_V2_FILTER_NODE='',DPR_V2_RESOURCE='光轮智能',DPR_V2_DRAG_INDEX=null;
    var DPR_V2_CAPACITIES={
      supplier:{
        '光轮智能':{'质检':[{start:'2026-07-01',end:'2026-07-31',total:17200,unit:'条'},{start:'2026-08-01',end:'2026-08-04',total:18600,unit:'条'},{start:'2026-08-05',end:'2026-08-31',total:19000,unit:'条'}],'标注':[{start:'2026-07-01',end:'2026-07-31',total:1180,unit:'小时'},{start:'2026-08-01',end:'2026-08-04',total:1280,unit:'小时'},{start:'2026-08-05',end:'2026-08-31',total:1320,unit:'小时'}]},
        '供应商 A':{'质检':[{start:'2026-07-01',end:'2026-07-31',total:11200,unit:'条'},{start:'2026-08-01',end:'2026-08-04',total:12480,unit:'条'},{start:'2026-08-05',end:'2026-08-31',total:13600,unit:'条'}],'标注':[{start:'2026-07-01',end:'2026-07-31',total:860,unit:'小时'},{start:'2026-08-01',end:'2026-08-04',total:960,unit:'小时'},{start:'2026-08-05',end:'2026-08-31',total:1040,unit:'小时'}]},
        '千寻数据':{'质检':[{start:'2026-07-01',end:'2026-07-31',total:4800,unit:'条'},{start:'2026-08-01',end:'2026-08-04',total:5260,unit:'条'},{start:'2026-08-05',end:'2026-08-31',total:5600,unit:'条'}],'标注':[{start:'2026-07-01',end:'2026-07-31',total:360,unit:'小时'},{start:'2026-08-01',end:'2026-08-04',total:420,unit:'小时'},{start:'2026-08-05',end:'2026-08-31',total:480,unit:'小时'}]}
      },
      user_group:{
        '质检复核用户组':{'质检':[{start:'2026-08-01',end:'2026-08-31',total:9600,unit:'条'}]},
        '标注员用户组':{'标注':[{start:'2026-08-01',end:'2026-08-31',total:720,unit:'小时'}]},
        '标注抽验员用户组':{'标注':[{start:'2026-08-01',end:'2026-08-31',total:320,unit:'小时'}]}
      }
    };
    var DPR_V2_TASK_NAMES={
      '厨房数据质检流程 · 供应商复核':'厨房数据质检','三方数据导入质检流程 · 格式校验':'三方数据导入质检','端到端切分标注流程 · 供应商标注':'端到端切分标注','双轮人工标注流程 · 标注抽验':'家居动作标注','动作标注流程 · 供应商抽验':'动作标注专项','厨房数据质检流程 · 完整性质检':'厨房数据质检','三方数据导入质检流程 · Schema 校验':'三方数据导入质检','端到端切分标注流程 · 动作分段标注':'端到端切分标注','双轮人工标注流程 · 初轮标注':'家居动作标注'
    };
    var DPR_V2_TASK_LIMITS={'厨房数据质检流程 · 供应商复核':180,'三方数据导入质检流程 · 格式校验':260,'端到端切分标注流程 · 供应商标注':32,'双轮人工标注流程 · 标注抽验':20,'动作标注流程 · 供应商抽验':14};
    var DPR_V2_LIMIT_TASK=null;
    function dprV2TaskParts(task){var parts=task.name.split(' · ');return {task:DPR_V2_TASK_NAMES[task.name]||parts[0]||'',flow:parts[0]||'',node:parts[1]||''};}
    function dprV2AllTasks(){return Object.keys(DPR_V2_DATA).reduce(function(all,type){DPR_V2_DATA[type].forEach(function(resource){all=all.concat(resource.tasks);});return all;},[]);}
    function dprV2TaskMatches(task){var parts=dprV2TaskParts(task);return task.stage===DPR_V2_STAGE&&(!DPR_V2_FILTER_FLOW||parts.task===DPR_V2_FILTER_FLOW)&&(!DPR_V2_FILTER_NODE||parts.node===DPR_V2_FILTER_NODE);}
    function dprV2ResourcesForStage(){return DPR_V2_DATA[DPR_V2_TYPE].filter(function(resource){return resource.tasks.some(dprV2TaskMatches);});}
    function dprV2EnsureResource(){var resources=dprV2ResourcesForStage();if(!resources.some(function(resource){return resource.id===DPR_V2_RESOURCE;}))DPR_V2_RESOURCE=resources[0]?resources[0].id:'';}
    function dprV2FilterValues(){
      var stageTasks=dprV2AllTasks().filter(function(task){return task.stage===DPR_V2_STAGE;}),flows=[];
      stageTasks.forEach(function(task){var flow=dprV2TaskParts(task).task;if(flows.indexOf(flow)<0)flows.push(flow);});
      var flowSelect=document.getElementById('dprV2FilterFlow');
      if(DPR_V2_FILTER_FLOW&&flows.indexOf(DPR_V2_FILTER_FLOW)<0)DPR_V2_FILTER_FLOW='';
      flowSelect.innerHTML='<option value="">全部处理任务</option>'+flows.map(function(flow){return '<option value="'+flow+'"'+(flow===DPR_V2_FILTER_FLOW?' selected':'')+'>'+flow+'</option>';}).join('');
      var nodes=[];
      if(DPR_V2_FILTER_FLOW)stageTasks.forEach(function(task){var parts=dprV2TaskParts(task);if(parts.task===DPR_V2_FILTER_FLOW&&nodes.indexOf(parts.node)<0)nodes.push(parts.node);});
      if(DPR_V2_FILTER_NODE&&nodes.indexOf(DPR_V2_FILTER_NODE)<0)DPR_V2_FILTER_NODE='';
      var nodeSelect=document.getElementById('dprV2FilterNode');
      nodeSelect.disabled=!DPR_V2_FILTER_FLOW;
      nodeSelect.innerHTML='<option value="">全部节点</option>'+nodes.map(function(node){return '<option value="'+node+'"'+(node===DPR_V2_FILTER_NODE?' selected':'')+'>'+node+'</option>';}).join('');
    }
    function dprV2SetStage(stage){DPR_V2_STAGE=stage;DPR_V2_FILTER_FLOW='';DPR_V2_FILTER_NODE='';document.getElementById('dprV2FilterStage').value=stage;dprV2Render();}
    function dprV2FilterStageChanged(select){dprV2SetStage(select.value);}
    function dprV2FilterFlowChanged(select){DPR_V2_FILTER_FLOW=select.value;DPR_V2_FILTER_NODE='';dprV2Render();}
    function dprV2FilterChanged(){DPR_V2_FILTER_NODE=document.getElementById('dprV2FilterNode').value;dprV2Render();}
    function dprV2Query(){DPR_V2_FILTER_NODE=document.getElementById('dprV2FilterNode').value;dprV2Render();}
    function dprV2ClearFilters(){DPR_V2_STAGE='质检';DPR_V2_FILTER_FLOW='';DPR_V2_FILTER_NODE='';document.getElementById('dprV2FilterStage').value='质检';dprV2Render();}
    function dprV2SwitchType(button){DPR_V2_TYPE=button.dataset.v2Type;document.querySelectorAll('.dpr-v2-tabs button').forEach(function(item){item.classList.toggle('active',item===button);});dprV2EnsureResource();dprV2Render();}
    function dprV2RenderResources(){var resources=dprV2ResourcesForStage();document.getElementById('dprV2ResourceList').innerHTML=resources.map(function(resource){var count=resource.tasks.filter(dprV2TaskMatches).length;return '<button class="dpr-v2-resource'+(resource.id===DPR_V2_RESOURCE?' active':'')+'" onclick="dprV2SelectResource(this)" data-v2-resource="'+resource.id+'"><b>'+resource.id+'</b><span>'+count+' 个任务</span></button>';}).join('')||'<div class="dpr-v2-empty">当前筛选条件下暂无处理资源</div>';}
    function dprV2SelectResource(button){DPR_V2_RESOURCE=button.dataset.v2Resource;dprV2Render();}
    function dprV2VisibleTasks(resource){return resource?resource.tasks.filter(dprV2TaskMatches):[];}
    function dprV2TaskUnit(task){return task.stage==='质检'?'条':'小时';}
    function dprV2TaskConsumed(task){if(task.stage==='质检'){var counts=task.progress.match(/\d+/g)||[];return Number(counts[0]||0);}return Number(DPR_V2_TASK_HOURS[task.name]||0);}
    function dprV2FormatDate(date){var month=String(date.getMonth()+1).padStart(2,'0'),day=String(date.getDate()).padStart(2,'0');return date.getFullYear()+'-'+month+'-'+day;}
    function dprV2AddDays(value,days){var date=new Date(value+'T00:00:00');date.setDate(date.getDate()+days);return dprV2FormatDate(date);}
    function dprV2CapacityKind(item){var today=dprV2FormatDate(new Date());if(item.end<today)return 'history';if(item.start>today)return 'future';return 'current';}
    function dprV2CapacityKindLabel(kind){return kind==='history'?'历史周期':(kind==='future'?'未来周期':'当前周期');}
    function dprV2SortCapacityItems(items){return (items||[]).slice().sort(function(left,right){return String(right.start||right.end||'').localeCompare(String(left.start||left.end||''));});}
    function dprV2CurrentCapacity(resource){
      if(!resource)return null;
      var stages=((DPR_V2_CAPACITIES[DPR_V2_TYPE]||{})[resource.id]||{}),periods=stages[DPR_V2_STAGE]||[],today=dprV2FormatDate(new Date());
      return periods.find(function(item){return item.start<=today&&today<=item.end;})||periods[0]||null;
    }
    function dprV2ResourceConsumed(resource){
      var stageTasks=resource?resource.tasks.filter(function(task){return task.stage===DPR_V2_STAGE;}):[];
      if(DPR_V2_STAGE==='质检')return stageTasks.reduce(function(total,task){var counts=task.progress.match(/\d+/g)||[];return total+Number(counts[0]||0);},0);
      return stageTasks.reduce(function(total,task){return total+Number(DPR_V2_TASK_HOURS[task.name]||0);},0);
    }
    function dprV2RenderResourceSummary(resource){
      var capacity=dprV2CurrentCapacity(resource),consumed=dprV2ResourceConsumed(resource);
      var unit=capacity?capacity.unit:(DPR_V2_STAGE==='质检'?'条':'小时');
      document.getElementById('dprV2CapacityPeriod').textContent=capacity?capacity.start+' 至 '+capacity.end:'未配置';
      document.getElementById('dprV2CapacityTotal').textContent=capacity?capacity.total+' '+unit:'未配置';
      document.getElementById('dprV2CapacityConsumed').textContent=(Math.round(consumed*10)/10)+' '+unit;
      document.getElementById('dprV2CapacityRemaining').textContent=capacity?(Math.max(0,Math.round((Number(capacity.total)-consumed)*10)/10)+' '+unit):'未配置';
      document.getElementById('dprV2ResourceSummary').style.display=resource?'grid':'none';
    }
    function dprV2RenderTasks(){
      var resource=DPR_V2_DATA[DPR_V2_TYPE].find(function(item){return item.id===DPR_V2_RESOURCE;});
      var tasks=dprV2VisibleTasks(resource),holder=document.getElementById('dprV2TaskList');
      document.getElementById('dprV2TaskTitle').textContent=(resource?resource.id+' · ':'')+'正在处理中的任务';
      document.getElementById('dprV2CapacityButton').style.display=resource&&DPR_V2_TYPE==='supplier'?'inline-flex':'none';
      document.getElementById('dprV2TaskCount').textContent=tasks.length+' 个任务';
      dprV2RenderResourceSummary(resource);
      holder.innerHTML=tasks.length?tasks.map(function(task,index){
        var parts=dprV2TaskParts(task),counts=task.progress.match(/\d+/g)||[];
        var current=Number(counts[0]||0),total=Number(counts[1]||0),other=Math.min(Number(DPR_V2_OTHER_CONTRIBUTIONS[task.name]||0),Math.max(0,total-current));
        var completed=Math.min(total,current+other),remaining=Math.max(0,total-completed),pct=total?Math.round(completed/total*100):0,currentPct=total?current/total*100:0,otherPct=total?other/total*100:0;
        var priority=task.priority||(index===0?'9':'6'),taskConsumed=dprV2TaskConsumed(task),taskUnit=dprV2TaskUnit(task),limit=Number(DPR_V2_TASK_LIMITS[task.name]||0),limitReached=limit>0&&taskConsumed>=limit;
        var taskPaused=task.status==='paused'||limitReached,statusClass=taskPaused?' paused':'',statusText=taskPaused?'已暂停':'处理中';
        return '<article class="dpr-v2-task'+(taskPaused?' paused':'')+'" data-claimable="'+(limitReached?'false':'true')+'"><div class="dpr-v2-task-main"><div class="dpr-v2-task-title"><span class="dpr-v2-task-name">'+parts.task+'</span><span class="dpr-v2-task-status'+statusClass+'">'+statusText+'</span></div><div class="dpr-v2-task-facts"><span class="dpr-v2-task-fact"><i>处理流程</i><b>'+parts.flow+'</b></span><span class="dpr-v2-task-fact"><i>节点</i><b>'+parts.node+'</b></span><span class="dpr-v2-task-fact dpr-v2-task-priority"><i>优先级</i><b class="dpr-v2-priority '+priority.toLowerCase()+'">'+priority+'</b></span><span class="dpr-v2-task-fact dpr-v2-progress"><span class="dpr-v2-node-progress-head"><i>节点整体进度</i><b>'+completed+' / '+total+' 条 · '+pct+'%</b></span><span class="dpr-v2-contribution-bar"><i class="dpr-v2-contribution-current" style="width:'+currentPct+'%"></i><i class="dpr-v2-contribution-other" style="width:'+otherPct+'%"></i></span><span class="dpr-v2-contribution-legend"><span class="current"><i></i>当前处理人 '+current+'</span><span class="other"><i></i>其他处理人 '+other+'</span><span><i></i>未完成 '+remaining+'</span></span></span></div></div><div class="dpr-v2-task-actions"><span class="dpr-v2-task-limit-summary'+(limitReached?' full':'')+'">'+(limit?'上限 '+limit+' '+taskUnit:'未设置上限')+'</span><button class="dpr-v2-task-action" onclick="dprV2OpenLimitModal(event,'+index+')">设置产能上限</button><button class="dpr-v2-task-action'+(taskPaused?' resume':'')+'" onclick="dprV2TogglePause(event,'+index+')"' +(limitReached?' disabled':'')+'><span class="dpr-v2-task-action-icon" aria-hidden="true">'+(taskPaused?'&#9654;':'&#10074;&#10074;')+'</span>'+(taskPaused?'恢复处理':'暂停处理')+'</button></div></article>';
      }).join(''):'<div class="dpr-v2-empty">当前没有正在处理中的任务</div>';
    }
    function dprV2CapacityRow(item,kind){
      var unit=DPR_V2_STAGE==='质检'?'条':'小时';
      item=item||{start:'',end:'',unit:unit,total:''};kind=kind||dprV2CapacityKind(item);
      var disabled=kind==='history'?' disabled':'',total=item.total===0?0:(item.total||'');
      return '<tr data-capacity-kind="'+kind+'"><td><span class="dpr-v2-capacity-kind '+kind+'">'+dprV2CapacityKindLabel(kind)+'</span></td><td><div class="dpr-v2-capacity-period-inputs"><input type="date" value="'+(item.start||'')+'" oninput="dprV2RefreshCapacityConstraints()"'+disabled+'><span>至</span><input type="date" value="'+(item.end||'')+'" oninput="dprV2RefreshCapacityConstraints()"'+disabled+'></div></td><td><select'+disabled+'><option'+(item.unit==='小时'?' selected':'')+'>小时</option><option'+(item.unit==='条'?' selected':'')+'>条</option></select></td><td><input type="number" min="0" step="1" value="'+total+'" placeholder="请输入整数"'+disabled+'></td><td><button type="button" class="dpr-v2-capacity-row-remove" aria-label="删除" onclick="dprV2RemoveCapacityRow(this)"'+disabled+'>&times;</button></td></tr>';
    }
    function dprV2CapacityRowsData(){return Array.from(document.querySelectorAll('#dprV2CapacityRows tr')).map(function(row){var dates=row.querySelectorAll('input[type="date"]');return {row:row,kind:row.dataset.capacityKind,start:dates[0].value,end:dates[1].value,totalInput:row.querySelector('input[type="number"]')};});}
    function dprV2SortCapacityRows(){var holder=document.getElementById('dprV2CapacityRows');dprV2CapacityRowsData().sort(function(left,right){return String(right.start||right.end||'').localeCompare(String(left.start||left.end||''));}).forEach(function(item){holder.appendChild(item.row);});}
    function dprV2RefreshCapacityConstraints(){
      var rows=dprV2CapacityRowsData(),today=dprV2FormatDate(new Date()),historyEnds=rows.filter(function(item){return item.kind==='history'&&item.end;}).map(function(item){return item.end;}).sort(),latestHistoryEnd=historyEnds.length?historyEnds[historyEnds.length-1]:'',current=rows.find(function(item){return item.kind==='current';}),currentEnd=current&&current.end?current.end:'';
      var resource=DPR_V2_DATA[DPR_V2_TYPE].find(function(item){return item.id===DPR_V2_RESOURCE;}),consumed=dprV2ResourceConsumed(resource);
      rows.forEach(function(item){var dates=item.row.querySelectorAll('input[type="date"]');
        if(item.kind==='current'){dates[0].min=latestHistoryEnd?dprV2AddDays(latestHistoryEnd,1):'';dates[0].max=today;dates[1].min=dates[0].value||dates[0].min;dates[1].max=today;item.totalInput.min=String(Math.ceil(consumed));item.totalInput.title='当前已消耗 '+(Math.round(consumed*10)/10)+' '+(DPR_V2_STAGE==='质检'?'条':'小时');}
        if(item.kind==='future'){dates[0].min=currentEnd?dprV2AddDays(currentEnd,1):dprV2AddDays(today,1);dates[1].min=dates[0].value||dates[0].min;}
      });
    }
    function dprV2AddCapacityRow(item){
      var kind=item&&item.kind?item.kind:'future';
      if(!item){var ends=dprV2CapacityRowsData().map(function(row){return row.end;}).filter(Boolean).sort(),latestEnd=ends.length?ends[ends.length-1]:dprV2FormatDate(new Date()),start=dprV2AddDays(latestEnd,1);item={start:start,end:dprV2AddDays(start,29),unit:DPR_V2_STAGE==='质检'?'条':'小时',total:''};}
      document.getElementById('dprV2CapacityRows').insertAdjacentHTML('beforeend',dprV2CapacityRow(item,kind));dprV2SortCapacityRows();dprV2RefreshCapacityConstraints();
    }
    function dprV2RemoveCapacityRow(button){button.closest('tr').remove();dprV2RefreshCapacityConstraints();}
    function dprV2OpenCapacityModal(){
      if(DPR_V2_TYPE!=='supplier'||!DPR_V2_RESOURCE)return;
      var stages=((DPR_V2_CAPACITIES.supplier||{})[DPR_V2_RESOURCE]||{}),items=stages[DPR_V2_STAGE]||[];
      document.getElementById('dprV2CapacityContext').innerHTML='<b>'+DPR_V2_RESOURCE+'</b> · '+DPR_V2_STAGE+'环节';
      var capacityAdd=document.querySelector('.dpr-v2-capacity-add'),capacityTable=document.querySelector('.dpr-v2-capacity-modal .table-wrap');
      if(capacityAdd&&capacityTable) capacityTable.parentNode.insertBefore(capacityAdd,capacityTable);
      document.getElementById('dprV2CapacityRows').innerHTML=dprV2SortCapacityItems(items).map(function(item){return dprV2CapacityRow(item);}).join('');
      dprV2RefreshCapacityConstraints();
      document.getElementById('dprV2CapacityModalMask').classList.add('active');
    }
    function dprV2CloseCapacityModal(event){if(event&&event.target!==document.getElementById('dprV2CapacityModalMask'))return;document.getElementById('dprV2CapacityModalMask').classList.remove('active');}
    function dprV2SaveCapacity(){
      var rows=Array.from(document.querySelectorAll('#dprV2CapacityRows tr'));
      if(!rows.length){toast('请至少增加一行产能分配');return;}
      var items=[],valid=true,today=dprV2FormatDate(new Date()),resource=DPR_V2_DATA[DPR_V2_TYPE].find(function(item){return item.id===DPR_V2_RESOURCE;}),consumed=dprV2ResourceConsumed(resource);
      rows.forEach(function(row){var dates=row.querySelectorAll('input[type="date"]'),unit=row.querySelector('select').value,total=Number(row.querySelector('input[type="number"]').value),kind=row.dataset.capacityKind;if(!dates[0].value||!dates[1].value||dates[0].value>dates[1].value||!Number.isInteger(total)||total<0)valid=false;items.push({start:dates[0].value,end:dates[1].value,unit:unit,total:total,kind:kind});});
      if(!valid){toast('请填写有效的起止时间和非负整数产能');return;}
      var histories=items.filter(function(item){return item.kind==='history';}),current=items.find(function(item){return item.kind==='current';}),futures=items.filter(function(item){return item.kind==='future';}),latestHistoryEnd=histories.map(function(item){return item.end;}).sort().pop()||'';
      if(!current){toast('请保留当前周期');return;}
      if(latestHistoryEnd&&current.start<=latestHistoryEnd){toast('当前周期开始时间必须晚于最近的历史周期结束时间');return;}
      if(current.end>today){toast('当前周期截止时间最多只能修改到今天');return;}
      if(current.total<consumed){toast('当前周期产能不能小于已消耗产能 '+(Math.round(consumed*10)/10)+' '+current.unit);return;}
      if(futures.some(function(item){return item.start<=current.end;})){toast('未来周期开始时间必须晚于当前周期');return;}
      items=dprV2SortCapacityItems(items);items.forEach(function(item){delete item.kind;});
      DPR_V2_CAPACITIES.supplier[DPR_V2_RESOURCE]=DPR_V2_CAPACITIES.supplier[DPR_V2_RESOURCE]||{};
      DPR_V2_CAPACITIES.supplier[DPR_V2_RESOURCE][DPR_V2_STAGE]=items;
      dprV2CloseCapacityModal();dprV2Render();toast('Demo: 产能分配已更新');
    }
    function dprV2OpenLimitModal(event,index){
      event.stopPropagation();var resource=DPR_V2_DATA[DPR_V2_TYPE].find(function(item){return item.id===DPR_V2_RESOURCE;}),task=dprV2VisibleTasks(resource)[index];if(!task)return;
      DPR_V2_LIMIT_TASK=task;var parts=dprV2TaskParts(task),unit=dprV2TaskUnit(task),value=DPR_V2_TASK_LIMITS[task.name]||'';
      document.getElementById('dprV2LimitContext').innerHTML='<b>'+parts.task+'</b> · '+parts.node;
      document.getElementById('dprV2LimitValue').value=value;document.getElementById('dprV2LimitUnit').textContent=unit;document.getElementById('dprV2LimitModalMask').classList.add('active');
    }
    function dprV2CloseLimitModal(event){if(event&&event.target!==document.getElementById('dprV2LimitModalMask'))return;document.getElementById('dprV2LimitModalMask').classList.remove('active');DPR_V2_LIMIT_TASK=null;}
    function dprV2SaveTaskLimit(){
      var value=Number(document.getElementById('dprV2LimitValue').value);if(!DPR_V2_LIMIT_TASK||!Number.isInteger(value)||value<0){toast('请输入非负整数产能上限');return;}
      DPR_V2_TASK_LIMITS[DPR_V2_LIMIT_TASK.name]=value;dprV2CloseLimitModal();dprV2Render();toast('Demo: 产能分配上限已更新');
    }
    function dprV2DecorateProgress(){document.querySelectorAll('.dpr-v2-task').forEach(function(card){var facts=card.querySelectorAll('.dpr-v2-task-fact'),doneFact=facts[3],pendingFact=facts[4];if(!doneFact||!pendingFact)return;var done=Number((doneFact.textContent.match(/\d+/)||[0])[0]),pending=Number((pendingFact.textContent.match(/\d+/)||[0])[0]),total=done+pending,pct=total?Math.round(done/total*100):0;doneFact.className='dpr-v2-task-fact dpr-v2-progress';doneFact.innerHTML='<i>处理进度</i><div class="dpr-task-progress-line"><i style="width:'+pct+'%"></i><b>'+done+' / '+total+' 条 · '+pct+'%</b></div>';pendingFact.style.display='none';});}
    function dprV2Render(){dprV2FilterValues();dprV2EnsureResource();dprV2RenderResources();dprV2RenderTasks();dprV2DecorateProgress();}function dprV2TogglePause(event,index){event.stopPropagation();var resource=DPR_V2_DATA[DPR_V2_TYPE].find(function(item){return item.id===DPR_V2_RESOURCE;}),task=dprV2VisibleTasks(resource)[index];if(!task)return;var limit=Number(DPR_V2_TASK_LIMITS[task.name]||0);if(limit>0&&dprV2TaskConsumed(task)>=limit)return;task.status=task.status==='paused'?'processing':'paused';dprV2Render();}
    function dprV2StylePriority(){document.querySelectorAll('.dpr-v2-priority').forEach(function(item){item.classList.add(item.textContent.toLowerCase());});}
    var dprV2CardStyle=document.createElement('style');dprV2CardStyle.textContent='.dpr-v2-task{grid-template-columns:minmax(0,1fr) auto;cursor:default}.dpr-v2-task-action{display:inline-flex;align-items:center;justify-content:center;gap:5px}.dpr-v2-task-action.resume{border-color:#b8dfe2;background:#f6fbfb;color:#147a83}.dpr-v2-task-action.resume:hover{border-color:#8bcbd0;background:#eef9fa;color:#0f7079}.dpr-v2-task-action:disabled{border-color:#e4e9ea;background:#f4f6f6;color:#a7b1b4;cursor:not-allowed}.dpr-v2-task-action:disabled:hover{border-color:#e4e9ea;color:#a7b1b4}.dpr-v2-task-action-icon{display:inline-flex;align-items:center;justify-content:center;width:12px;font-size:11px;line-height:1}';document.head.appendChild(dprV2CardStyle);
    new MutationObserver(dprV2StylePriority).observe(document.getElementById('dprV2TaskList'),{childList:true,subtree:true});
    dprV2Render();
    </script>
    """


PAGE_RENDERERS = {
    "collection_tasks": render_collection_tasks,
    "processing_tasks": render_processing_tasks,
    "allocation_management": render_allocation_management,
    "allocation_management_v2": render_allocation_management_v2,
    "allocation_management_old": render_allocation_management_old,
    "data_management": render_data_management,
    "execution_records": render_pipeline_runs,
    "project_management": render_project_management,
    "user_group_management": render_user_group_management,
    "workbench_management": render_workbench_management,
    "supplier_management": render_supplier_management,
    "personnel_management": render_personnel_management,
    "permission_management": render_permission_management,
}


def render_workbench_v2():
    pool_items = [
        {"owner": "验收-端到端切分标注", "pool": "端到端切分标注 · 内部验收任务池", "pool_id": "POOL-E2E-ACCEPTANCE", "stage": "标注", "priority": 9, "pending": 86, "processing": 18, "stalled": "2.1 小时", "priority_summary": "9级 62 · 8级 24", "source_summary": "端到端切分标注 · 内部验收"},
        {"owner": "供应商 A", "pool": "端到端切分标注 · 供应商 A 任务池", "pool_id": "POOL-E2E-SUPPLIER-A", "stage": "标注", "priority": 9, "pending": 124, "processing": 31, "stalled": "3.4 小时", "priority_summary": "9级 88 · 7级 36", "source_summary": "端到端切分标注 · 供应商抽验"},
        {"owner": "光轮智能", "pool": "端到端切分标注 · 光轮智能任务池", "pool_id": "POOL-E2E-GUAN", "stage": "标注", "priority": 9, "pending": 118, "processing": 28, "stalled": "2.8 小时", "priority_summary": "9级 76 · 6级 42", "source_summary": "端到端切分标注 · 供应商抽验"},
    ]
    pool_cards = "".join(
        f"""
        <article class="wb-pool-card">
          <div class="wb-pool-head"><div><h3>{_e(item["owner"])}</h3></div></div>
          <div class="wb-pool-volume"><div><b>{item["pending"]}</b><span>待领取</span></div><div><b>{item["processing"]}</b><span>处理中</span></div><div><b>{_e(item["stalled"])}</b><span>最长滞留</span></div></div>
          <div class="wb-pool-foot wb-v2-pool-foot"><span class="wb-v2-foot-spacer" aria-hidden="true"></span><span class="wb-v2-priority-summary">{_e(item["priority_summary"])}</span><a class="btn btn-primary" href="/data/workbench-v2/pools/{_e(item['pool_id'])}">进入任务池 ›</a></div>
        </article>
        """
        for item in pool_items
    )
    rejected = [
        ("recording_e2e_001", "flow.annotation.e2e-review@2", "端到端切分标注流程", "供应商抽验", "供应商复核", "驳回", "第 2 轮", "切分起点与动作开始不一致", "2026-08-04 16:42", "WB-E2E-SUPPLIER-A"),
        ("recording_e2e_002", "flow.annotation.e2e-review@2", "端到端切分标注流程", "供应商抽验", "供应商复核", "驳回", "第 2 轮", "High-level 片段范围需要调整", "2026-08-04 15:18", "WB-E2E-GUAN"),
        ("recording_e2e_003", "flow.annotation.e2e-review@2", "端到端切分标注流程", "供应商抽验", "供应商复核", "驳回", "第 3 轮", "存在连续片段未完成切分", "2026-08-04 13:56", "WB-E2E-SUPPLIER-A"),
        ("recording_e2e_004", "flow.annotation.e2e-review@2", "端到端切分标注流程", "供应商复核", "供应商抽验", "提交", "第 2 轮", "复核发现片段边界仍需确认", "2026-08-03 18:20", "WB-E2E-REVIEW"),
        ("recording_e2e_005", "flow.annotation.e2e-review@2", "端到端切分标注流程", "供应商复核", "供应商验收", "驳回", "第 2 轮", "Low-level 动作片段存在重叠", "2026-08-03 16:05", "WB-E2E-REVIEW"),
        ("recording_e2e_006", "flow.annotation.e2e-review@2", "端到端切分标注流程", "供应商复核", "供应商抽验", "提交", "第 3 轮", "切分结果与规则不一致", "2026-08-03 11:48", "WB-E2E-REVIEW"),
        ("recording_e2e_007", "flow.annotation.e2e-review@2", "端到端切分标注流程", "内部验收", "供应商验收", "提交", "第 1 轮", "验收发现关键片段缺少结束时间", "2026-08-02 17:32", "WB-E2E-ACCEPTANCE"),
        ("recording_e2e_008", "flow.annotation.e2e-review@2", "端到端切分标注流程", "内部验收", "供应商验收", "提交", "第 2 轮", "动作片段描述与切分范围不匹配", "2026-08-02 14:10", "WB-E2E-ACCEPTANCE"),
        ("recording_e2e_009", "flow.annotation.e2e-review@2", "端到端切分标注流程", "内部验收", "供应商验收", "提交", "第 3 轮", "存在一条待确认的异常片段", "2026-08-01 19:25", "WB-E2E-ACCEPTANCE"),
    ]
    todo_items = [
        {
            "recording_id": recording_id,
            "flow_id": flow_id,
            "flow_name": flow_name,
            "processing_task": {
                "WB-E2E-SUPPLIER-A": "端到端切分标注任务 · 供应商 A",
                "WB-E2E-GUAN": "端到端切分标注任务 · 光轮智能",
                "WB-E2E-REVIEW": "端到端切分标注任务 · 供应商复核",
                "WB-E2E-ACCEPTANCE": "端到端切分标注任务 · 内部验收",
            }.get(task_id, task_id),
            "current_node": current_node,
            "source_node": source_node,
            "source_operation": source_operation,
            "current_round": current_round,
            "description": description,
            "updated_at": updated_at,
            "task_id": task_id,
        }
        for recording_id, flow_id, flow_name, current_node, source_node, source_operation, current_round, description, updated_at, task_id in rejected
    ]
    todo_data_json = json.dumps(todo_items, ensure_ascii=False).replace("</", "<\\/")
    return f"""
    <style>
      .dpr-wb2-items-toolbar .q-field select:disabled{{background:#f5f7f8!important;border-color:#e5eaec!important;color:#a6b1b5!important;cursor:not-allowed;opacity:1}}
      .dpr-wb2-items-split{{display:grid;grid-template-columns:minmax(240px,300px) minmax(0,1fr);gap:16px;align-items:start}}.dpr-wb2-group-panel,.dpr-wb2-recordings-panel{{min-width:0;border:1px solid #e8edef;border-radius:10px;background:#fff}}.dpr-wb2-group-panel{{overflow:hidden}}.dpr-wb2-group-panel-head,.dpr-wb2-recordings-head{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:15px 16px;border-bottom:1px solid #edf1f2}}.dpr-wb2-group-panel-head b,.dpr-wb2-recordings-head b{{color:#263f47;font-size:13px}}.dpr-wb2-group-panel-head span,.dpr-wb2-recordings-head span{{color:#849197;font-size:11px}}.dpr-wb2-total-count{{margin-left:auto;color:#0f7f8a!important;font-size:13px!important;font-weight:700!important;white-space:nowrap}}.dpr-wb2-group-list{{display:flex;flex-direction:column;max-height:540px;overflow:auto}}.dpr-wb2-group-item{{display:block;width:100%;padding:13px 16px;border:0;border-bottom:1px solid #f0f3f4;background:#fff;text-align:left;cursor:pointer;box-sizing:border-box}}.dpr-wb2-group-item:last-child{{border-bottom:0}}.dpr-wb2-group-item:hover{{background:#f7fbfb}}.dpr-wb2-group-item.active{{background:#eef9fa;box-shadow:inset 3px 0 #149daa}}.dpr-wb2-group-title-row{{display:flex;align-items:center;gap:8px;min-width:0}}.dpr-wb2-group-title-row .dpr-wb2-group-label{{flex:none;color:#849197;font-size:10px;font-style:normal;white-space:nowrap}}.dpr-wb2-group-title-row b{{flex:1;min-width:0;overflow:hidden;color:#334c54;font-size:12px;font-weight:600;text-overflow:ellipsis;white-space:nowrap}}.dpr-wb2-group-title-row em{{flex:none;color:#149daa;font-size:11px;font-style:normal;font-weight:600;white-space:nowrap}}.dpr-wb2-group-meta{{display:grid;grid-template-columns:1fr;gap:4px;margin-top:7px;color:#718188;font-size:11px;line-height:1.5}}.dpr-wb2-group-meta span{{display:block;min-width:0;margin:0!important;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.dpr-wb2-group-meta i{{margin-right:3px;color:#9aa7ab;font-style:normal;font-size:10px}}.dpr-wb2-recordings-head{{align-items:flex-start;flex-direction:column;gap:4px}}.dpr-wb2-recordings-head span{{line-height:1.5}}.dpr-wb2-recordings-panel .table-wrap{{border:0;border-radius:0}}.dpr-wb2-recordings-panel .dpr-wb2-items-table{{min-width:760px}}.dpr-wb2-recordings-empty{{padding:42px 16px!important;text-align:center;color:#9aa7ab;font-size:12px}}@media(max-width:900px){{.dpr-wb2-items-split{{grid-template-columns:1fr}}.dpr-wb2-group-list{{max-height:300px}}}}
      .wb-v2-pool-foot{{display:flex;align-items:center;justify-content:flex-end;gap:7px}}.wb-v2-pool-foot .wb-v2-foot-spacer{{flex:1;visibility:hidden}}.wb-v2-pool-foot .wb-v2-priority-summary{{padding:3px 9px;border-radius:5px;background:#f2f5f6;color:#68777d;font-size:10.5px;font-weight:650;white-space:nowrap}}.wb-v2-pool-foot .btn{{flex:none}}
      .dpr-wb2-tabs{{display:flex;gap:22px;margin:0 0 16px;border-bottom:1px solid #e3eaec}}.dpr-wb2-tab{{position:relative;padding:0 2px 11px;border:0;background:transparent;color:#718188;font-size:13px;cursor:pointer}}.dpr-wb2-tab.active{{color:#149daa;font-weight:650}}.dpr-wb2-tab.active:after{{content:"";position:absolute;right:0;bottom:-1px;left:0;height:2px;background:#149daa}}.dpr-wb2-pane{{display:none}}.dpr-wb2-pane.active{{display:block}}.dpr-wb2-pool-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}.dpr-wb2-pool-card{{padding:16px;border:1px solid #e1e8ea;border-radius:9px;background:#fff}}.dpr-wb2-pool-head{{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:13px}}.dpr-wb2-pool-head h3{{margin:0;color:#263f47;font-size:15px}}.dpr-wb2-pool-head span{{display:block;margin-top:4px;color:#829096;font-size:11px}}.dpr-wb2-count{{color:#149daa;font-size:18px}}.dpr-wb2-pool-task{{display:flex;flex-direction:column;gap:4px;padding:11px 12px;border-radius:7px;background:#f7fafb}}.dpr-wb2-pool-task b{{color:#334c54;font-size:12px}}.dpr-wb2-pool-task span{{color:#829096;font-size:10.5px}}.dpr-wb2-pool-meta{{display:grid;grid-template-columns:minmax(0,1.5fr) 74px 100px;gap:12px;margin-top:14px}}.dpr-wb2-pool-meta span{{display:flex;flex-direction:column;gap:4px;min-width:0}}.dpr-wb2-pool-meta i{{color:#8a989d;font-size:10px;font-style:normal}}.dpr-wb2-pool-meta b{{overflow:hidden;color:#536970;font-size:11px;text-overflow:ellipsis;white-space:nowrap}}.dpr-wb2-pool-meta .dpr-priority{{align-self:flex-start}}.dpr-wb2-pool-foot{{display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding-top:12px;border-top:1px solid #edf1f2;color:#849197;font-size:11px}}.dpr-wb2-pool-foot .btn{{padding:6px 12px;font-size:11px}}.dpr-wb2-items-toolbar{{margin-bottom:12px}}.dpr-wb2-items-list{{overflow:auto}}.dpr-wb2-items-table{{width:100%;min-width:1120px}}.dpr-wb2-items-table th button{{display:inline-flex;align-items:center;gap:5px;padding:0;border:0;background:transparent;color:inherit;font:inherit;cursor:pointer}}.dpr-wb2-items-table th button:hover{{color:#147a83}}.dpr-wb2-sort-indicator{{color:#149daa;font-size:10px}}.dpr-wb2-reject-reason{{max-width:360px;color:#536970}}.dpr-wb2-operation{{display:inline-flex;padding:3px 8px;border-radius:10px;background:#fff3d9;color:#ad6800;font-size:11px;white-space:nowrap}}.dpr-wb2-operation.submit{{background:#e7f6ee;color:#2f8064}}.dpr-wb2-item-action{{white-space:nowrap}}.dpr-wb2-item-action .btn{{padding:5px 11px;font-size:11px}}.dpr-wb2-pagination{{display:flex;align-items:center;justify-content:flex-end;gap:7px;margin-top:12px;color:#7a898f;font-size:11px}}.dpr-wb2-pagination button{{min-width:30px;height:30px;padding:0 9px;border:1px solid #d8e2e4;border-radius:6px;background:#fff;color:#536970;cursor:pointer}}.dpr-wb2-pagination button.active{{border-color:#149daa;background:#149daa;color:#fff}}.dpr-wb2-pagination button:disabled{{cursor:not-allowed;opacity:.45}}@media(max-width:900px){{.dpr-wb2-pool-grid{{grid-template-columns:1fr}}.dpr-wb2-items-toolbar{{flex-wrap:wrap}}.dpr-wb2-items-actions{{margin-left:0}}}}
    </style>
    <div class="dpr-intro"><div><h1>标注工作台</h1></div><div class="dpr-intro-actions"><a class="btn btn-primary" href="/data/workbench-v2/style-examples">样式示例</a></div></div>
    <div class="dpr-wb2-tabs"><button class="dpr-wb2-tab active" onclick="dprSwitchWorkbenchV2Tab(this,'pool')">任务池</button><button class="dpr-wb2-tab" onclick="dprSwitchWorkbenchV2Tab(this,'items')">待办项</button></div>
    <section class="dpr-wb2-pane active" data-wb2-pane="pool"><div class="wb-pool-grid">{pool_cards}</div></section>
    <section class="dpr-wb2-pane" data-wb2-pane="items">
      <div class="q-filters rule-filter-panel dpr-wb2-items-toolbar">
        <div class="q-filter-row">
          <div class="q-field"><label for="dprWb2RecordingFilter">recording_id</label><input id="dprWb2RecordingFilter" type="search" placeholder="请输入 recording_id" oninput="dprWb2Query()"></div>
          <div class="q-field"><label for="dprWb2TaskFilter">处理任务</label><select id="dprWb2TaskFilter" onchange="dprWb2Query()"><option value="">全部处理任务</option></select></div>
          <div class="q-field"><label for="dprWb2FlowFilter">流程</label><select id="dprWb2FlowFilter" onchange="dprWb2FlowChanged(this)"><option value="">全部流程</option></select></div>
          <div class="q-field"><label for="dprWb2CurrentNodeFilter">当前节点</label><select id="dprWb2CurrentNodeFilter" onchange="dprWb2Query()" disabled><option value="">全部当前节点</option></select></div>
          <div class="q-field"><label for="dprWb2NodeFilter">来源节点</label><select id="dprWb2NodeFilter" onchange="dprWb2Query()" disabled><option value="">全部来源节点</option></select></div>
          <div class="q-field"><label for="dprWb2OperationFilter">来源操作</label><select id="dprWb2OperationFilter" onchange="dprWb2Query()"><option value="">全部来源操作</option></select></div>
          <div class="q-actions"><button type="button" class="btn" onclick="dprWb2ClearFilters()">清空</button><button type="button" class="btn btn-primary" onclick="dprWb2Query()">查询</button></div>
        </div>
      </div>
      <div class="dpr-wb2-items-split">
        <aside class="dpr-wb2-group-panel">
          <div class="dpr-wb2-group-panel-head"><b>任务分组</b><span id="dprWb2TotalCount" class="dpr-wb2-total-count"></span></div>
          <div id="dprWb2GroupList" class="dpr-wb2-group-list"></div>
        </aside>
        <section class="dpr-wb2-recordings-panel">
          <div class="table-wrap dpr-wb2-items-list">
            <table class="ant-table dpr-wb2-items-table">
              <thead><tr><th>recording_id</th><th>来源操作</th><th>说明</th><th>当前轮次</th><th><button type="button" onclick="dprWb2Sort(&quot;updated_at&quot;)">更新时间<span class="dpr-wb2-sort-indicator" data-sort-indicator="updated_at"></span></button></th><th>操作</th></tr></thead>
              <tbody id="dprWb2ItemsRows"></tbody>
            </table>
          </div>
        </section>
      </div>
      <div class="dpr-wb2-pagination"><span>10 条/页</span><button type="button" id="dprWb2PrevPage" onclick="dprWb2ChangePage(-1)">‹</button><span id="dprWb2PageButtons"></span><button type="button" id="dprWb2NextPage" onclick="dprWb2ChangePage(1)">›</button></div>
    </section>
    <script>
    var dprWb2Items={todo_data_json},dprWb2SortKey='updated_at',dprWb2SortDirection='desc',dprWb2Page=1,dprWb2PageSize=10,dprWb2TotalPages=1,dprWb2SelectedGroupKey='';
    function dprSwitchWorkbenchV2Tab(button,pane){{document.querySelectorAll('.dpr-wb2-tab').forEach(function(item){{item.classList.toggle('active',item===button);}});document.querySelectorAll('.dpr-wb2-pane').forEach(function(item){{item.classList.toggle('active',item.dataset.wb2Pane===pane);}});}}
    function dprWb2Escape(value){{return String(value==null?'':value).replace(/[&<>\"']/g,function(char){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}}[char];}});}}
    function dprWb2RenderPagination(){{var holder=document.getElementById('dprWb2PageButtons');holder.innerHTML='';for(var page=1;page<=dprWb2TotalPages;page++)holder.innerHTML+='<button type="button" class="'+(page===dprWb2Page?'active':'')+'" onclick="dprWb2GoToPage('+page+')">'+page+'</button>';document.getElementById('dprWb2PrevPage').disabled=dprWb2Page<=1;document.getElementById('dprWb2NextPage').disabled=dprWb2Page>=dprWb2TotalPages;}}
    function dprWb2Query(){{dprWb2Page=1;dprWb2RenderItems();}}
    function dprWb2ClearFilters(){{document.getElementById('dprWb2FlowFilter').value='';document.getElementById('dprWb2TaskFilter').value='';var currentNodeSelect=document.getElementById('dprWb2CurrentNodeFilter');currentNodeSelect.value='';currentNodeSelect.disabled=true;currentNodeSelect.innerHTML='<option value="">全部当前节点</option>';var nodeSelect=document.getElementById('dprWb2NodeFilter');nodeSelect.value='';nodeSelect.disabled=true;nodeSelect.innerHTML='<option value="">全部来源节点</option>';document.getElementById('dprWb2RecordingFilter').value='';document.getElementById('dprWb2OperationFilter').value='';dprWb2SelectedGroupKey='';dprWb2Query();}}
    function dprWb2GoToPage(page){{dprWb2Page=Math.max(1,Math.min(page,dprWb2TotalPages));dprWb2RenderItems();}}
    function dprWb2ChangePage(delta){{dprWb2GoToPage(dprWb2Page+delta);}}
    function dprWb2BuildOptions(){{var flows=[],tasks=[],currentNodes=[],operations=[];dprWb2Items.forEach(function(item){{if(flows.indexOf(item.flow_name)<0)flows.push(item.flow_name);if(tasks.indexOf(item.processing_task)<0)tasks.push(item.processing_task);if(currentNodes.indexOf(item.current_node)<0)currentNodes.push(item.current_node);if(operations.indexOf(item.source_operation)<0)operations.push(item.source_operation);}});document.getElementById('dprWb2FlowFilter').innerHTML='<option value="">全部流程</option>'+flows.map(function(value){{return '<option value="'+dprWb2Escape(value)+'">'+dprWb2Escape(value)+'</option>';}}).join('');document.getElementById('dprWb2TaskFilter').innerHTML='<option value="">全部处理任务</option>'+tasks.map(function(value){{return '<option value="'+dprWb2Escape(value)+'">'+dprWb2Escape(value)+'</option>';}}).join('');document.getElementById('dprWb2CurrentNodeFilter').innerHTML='<option value="">全部当前节点</option>'+currentNodes.map(function(value){{return '<option value="'+dprWb2Escape(value)+'">'+dprWb2Escape(value)+'</option>';}}).join('');document.getElementById('dprWb2OperationFilter').innerHTML='<option value="">全部来源操作</option>'+operations.map(function(value){{return '<option value="'+dprWb2Escape(value)+'">'+dprWb2Escape(value)+'</option>';}}).join('');}}
    function dprWb2FlowChanged(select){{var currentNodes=[],sourceNodes=[];dprWb2Items.forEach(function(item){{if(select.value&&item.flow_name===select.value){{if(currentNodes.indexOf(item.current_node)<0)currentNodes.push(item.current_node);if(sourceNodes.indexOf(item.source_node)<0)sourceNodes.push(item.source_node);}}}});var currentNodeSelect=document.getElementById('dprWb2CurrentNodeFilter');currentNodeSelect.disabled=!select.value;currentNodeSelect.value='';currentNodeSelect.innerHTML='<option value="">全部当前节点</option>'+currentNodes.map(function(value){{return '<option value="'+dprWb2Escape(value)+'">'+dprWb2Escape(value)+'</option>';}}).join('');var nodeSelect=document.getElementById('dprWb2NodeFilter');nodeSelect.disabled=!select.value;nodeSelect.value='';nodeSelect.innerHTML='<option value="">全部来源节点</option>'+sourceNodes.map(function(value){{return '<option value="'+dprWb2Escape(value)+'">'+dprWb2Escape(value)+'</option>';}}).join('');dprWb2Query();}}
    function dprWb2GroupItems(items){{var groups={{}};items.forEach(function(item){{var key=[item.task_id,item.processing_task,item.current_node,item.source_node].join('|'),group=groups[key];if(!group){{group=groups[key]=Object.assign({{}},item,{{group_key:key,group_count:0,items:[]}});}}group.group_count+=1;group.items.push(item);if(String(item.updated_at||'')>String(group.updated_at||'')){{group.updated_at=item.updated_at;}}}});return Object.keys(groups).map(function(key){{return groups[key];}});}}
    function dprWb2FilteredItems(){{var flow=document.getElementById('dprWb2FlowFilter').value,task=document.getElementById('dprWb2TaskFilter').value,currentNode=document.getElementById('dprWb2CurrentNodeFilter').value,node=document.getElementById('dprWb2NodeFilter').value,recording=document.getElementById('dprWb2RecordingFilter').value.trim().toLowerCase(),operation=document.getElementById('dprWb2OperationFilter').value;var filtered=dprWb2Items.filter(function(item){{return (!flow||item.flow_name===flow)&&(!task||item.processing_task===task)&&(!currentNode||item.current_node===currentNode)&&(!node||item.source_node===node)&&(!recording||item.recording_id.toLowerCase().indexOf(recording)>=0)&&(!operation||item.source_operation===operation);}});return dprWb2GroupItems(filtered).sort(function(a,b){{var left=String(a[dprWb2SortKey]||''),right=String(b[dprWb2SortKey]||''),result=left.localeCompare(right,'zh-CN');return dprWb2SortDirection==='asc'?result:-result;}});}}
    function dprWb2SelectGroup(key){{dprWb2SelectedGroupKey=key;dprWb2Page=1;dprWb2RenderItems();}}
    function dprWb2DisplayTaskName(value){{return String(value||'').split(' · ')[0];}}
    function dprWb2RenderItems(){{var allItems=dprWb2FilteredItems(),groups=dprWb2GroupItems(allItems),selected=groups.find(function(group){{return group.group_key===dprWb2SelectedGroupKey;}})||groups[0]||null;if(selected)dprWb2SelectedGroupKey=selected.group_key;else dprWb2SelectedGroupKey='';document.getElementById('dprWb2TotalCount').textContent=allItems.length+' 条待办';document.getElementById('dprWb2GroupList').innerHTML=groups.length?groups.map(function(group){{var groupTitle=dprWb2DisplayTaskName(group.processing_task);return '<button type="button" class="dpr-wb2-group-item'+(group.group_key===dprWb2SelectedGroupKey?' active':'')+'" data-group-key="'+dprWb2Escape(group.group_key)+'" onclick="dprWb2SelectGroup(this.dataset.groupKey)"><div class="dpr-wb2-group-title-row"><i class="dpr-wb2-group-label">处理任务</i><b>'+dprWb2Escape(groupTitle)+'</b><em>'+group.group_count+' 条待办</em></div><div class="dpr-wb2-group-meta"><span><i>当前节点</i>'+dprWb2Escape(group.current_node)+'</span><span><i>来源节点</i>'+dprWb2Escape(group.source_node)+'</span></div></button>';}}).join(''):'<div class="dpr-wb2-recordings-empty">当前没有匹配的处理分组</div>';var recordingItems=selected?selected.items:[];dprWb2TotalPages=Math.max(1,Math.ceil(recordingItems.length/dprWb2PageSize));if(dprWb2Page>dprWb2TotalPages)dprWb2Page=dprWb2TotalPages;var items=recordingItems.slice((dprWb2Page-1)*dprWb2PageSize,dprWb2Page*dprWb2PageSize);document.getElementById('dprWb2ItemsRows').innerHTML=items.length?items.map(function(item){{var operationClass=item.source_operation==='提交'?' submit':'',href='/data/workbench-v2/edit?task='+encodeURIComponent(item.task_id)+'&recording_id='+encodeURIComponent(item.recording_id)+'&entry=todo';return '<tr><td><code>'+dprWb2Escape(item.recording_id)+'</code></td><td><span class="dpr-wb2-operation'+operationClass+'">'+dprWb2Escape(item.source_operation)+'</span></td><td class="dpr-wb2-reject-reason">'+dprWb2Escape(item.description||'—')+'</td><td>'+dprWb2Escape(item.current_round)+'</td><td>'+dprWb2Escape(item.updated_at)+'</td><td class="dpr-wb2-item-action"><a class="btn btn-sm" href="'+dprWb2Escape(href)+'">处理</a></td></tr>';}}).join(''):'<tr><td colspan="6" class="dpr-wb2-recordings-empty">当前分组没有匹配的 recording</td></tr>';document.querySelectorAll('[data-sort-indicator]').forEach(function(indicator){{indicator.textContent=indicator.dataset.sortIndicator===dprWb2SortKey?(dprWb2SortDirection==='asc'?' ↑':' ↓'):'';}});dprWb2RenderPagination();}}
    function dprWb2Sort(key){{if(dprWb2SortKey===key)dprWb2SortDirection=dprWb2SortDirection==='asc'?'desc':'asc';else{{dprWb2SortKey=key;dprWb2SortDirection='asc';}}dprWb2Page=1;dprWb2RenderItems();}}
    dprWb2BuildOptions();dprWb2RenderItems();
    </script>
    """


PAGE_RENDERERS["workbench_v2"] = render_workbench_v2


def render_product_page(page_key):
    if page_key not in PAGE_RENDERERS:
        raise KeyError(f"unknown data platform page: {page_key}")
    return PAGE_RENDERERS[page_key]()


# ---------------------------------------------------------------------------
# Styles isolated with a dpr- prefix so the shared portal remains unaffected.
# ---------------------------------------------------------------------------

DATA_PLATFORM_CSS = """
.dpr-priority.priority-low{background:#e6f4f8;color:#147b99!important}.dpr-priority.priority-medium{background:#fff7e6;color:#b56b00!important}.dpr-priority.priority-high{background:#fff1f0;color:#cf3f3b!important}
.dpr-intro{display:flex;justify-content:space-between;gap:24px;align-items:center;margin:0 0 22px;padding:4px 0}
.dpr-intro h1{margin:3px 0 0;font-size:24px;font-weight:650;letter-spacing:-.2px;color:#142b33}
.dpr-intro p{margin:0;max-width:820px;color:#607078;font-size:13px;line-height:1.7}
.dpr-intro-inline-action{justify-content:flex-start;align-items:flex-start}.dpr-intro-inline-action>div{width:100%;position:relative}.dpr-intro-title-row{display:flex;align-items:center;justify-content:flex-start;width:100%;gap:12px;margin-bottom:0}.dpr-intro-title-row h1{margin:3px 0 0}.dpr-intro-title-row .dpr-intro-actions{position:absolute;right:0;top:50%;transform:translateY(-50%);margin:0}
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
.dpr-section-head{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:16px}
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
.dpr-list-tab-card{display:flex;align-items:stretch;justify-content:space-between;gap:20px;min-height:51px;margin-bottom:14px;padding:0 20px;border:1px solid #e8edef;border-radius:10px;background:#fff;box-shadow:0 1px 2px rgba(16,42,50,.025);box-sizing:border-box}.dpr-execution-tabbar>span{display:flex;align-items:center;color:#7b898e;font-size:11.5px;white-space:nowrap}.dpr-execution-tabs{flex:1}
.dpr-execution-filters .ff:first-child{min-width:310px}.dpr-execution-filters .ff:first-child input{min-width:310px}
.dpr-run-open{padding:0;border:0;background:transparent;color:#149DAA;font-size:12px;cursor:pointer;white-space:nowrap}.dpr-run-open:hover{text-decoration:underline}
.dpr-io-arrow{display:inline-block;margin:0 7px;color:#94a1a6}#dpr-execution-run-table,#dpr-node-run-table{min-width:820px}#dpr-execution-run-table td,#dpr-node-run-table td{vertical-align:top}
.dpr-risk{color:#c64b40!important}.dpr-ok{color:#2f8d70!important}
.dpr-state{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:650;white-space:nowrap}.dpr-state.green{color:#26785f;background:#e5f5ee}.dpr-state.blue{color:#136f78;background:#dff4f6}.dpr-state.amber{color:#946118;background:#fff2d7}.dpr-state.red{color:#b34239;background:#fdebea}.dpr-state.purple{color:#6c4ba2;background:#f1eafa}.dpr-state.gray{color:#66757b;background:#edf0f1}
.dpr-table-wrap{overflow:auto;border:1px solid #e8edef;border-radius:8px}.dpr-table{width:100%;border-collapse:separate;border-spacing:0;min-width:920px;font-size:12px}
.dpr-table th{padding:10px 12px;text-align:left;background:#f6f8f9;color:#65747a;font-weight:600;white-space:nowrap;border-bottom:1px solid #e4e9eb}
.dpr-table td{padding:12px;vertical-align:middle;color:#334a52;border-bottom:1px solid #eef1f2;line-height:1.55}.dpr-table tbody tr:last-child td{border-bottom:0}.dpr-table tbody tr:hover td{background:#fbfdfd}
.dpr-org-count{display:inline-flex;align-items:center;justify-content:center;min-width:26px;height:24px;padding:0 7px;border-radius:12px;background:#e8f7f8;color:#117a83;font-weight:700;line-height:24px;cursor:help;box-sizing:border-box}.dpr-org-count:focus{outline:2px solid rgba(20,157,170,.25);outline-offset:2px}
.dpr-stage-tags{display:flex;align-items:center;gap:6px;flex-wrap:wrap}.dpr-stage-tags span{display:inline-flex;padding:2px 8px;border-radius:10px;background:#e8f6f7;color:#147a83;font-size:10.5px}.dpr-member-count{color:#405860;font-weight:500}
.dpr-table code,.dpr-pipeline-card code,.dpr-schema-card code,.dpr-run-top code,.dpr-history code,.dpr-line-node code{font:11px 'SF Mono',Menlo,monospace;color:#50636a}.dpr-table small{color:#7d8b90}
.dpr-empty{text-align:center!important;color:#8b989d!important;padding:32px!important}
.dpr-progress{display:flex;align-items:center;gap:8px;min-width:100px}.dpr-progress-track{height:6px;flex:1;background:#edf1f2;border-radius:5px;overflow:hidden}.dpr-progress-track span{display:block;height:100%;background:#149DAA;border-radius:5px}.dpr-progress b{font-size:11px;color:#52666d}
.dpr-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}.dpr-task-tabs{display:flex;align-items:center;gap:24px;border-bottom:1px solid #e5eaec}.dpr-task-tab{position:relative;border:0;background:transparent;padding:7px 2px 10px;color:#65757b;font-size:13px;cursor:pointer}.dpr-task-tab:hover{color:#149DAA}.dpr-task-tab.active{color:#149DAA;font-weight:650}.dpr-task-tab.active:after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:2px;background:#149DAA;border-radius:2px}.dpr-task-tab b{display:inline-flex;align-items:center;justify-content:center;min-width:18px;height:18px;margin-left:4px;padding:0 5px;border-radius:9px;background:#edf2f3;color:#65757b;font-size:10px}.dpr-task-tab.active b{background:#dff4f6;color:#136f78}
.dpr-collection-tabs{align-items:stretch}.dpr-collection-tabs .dpr-collection-tab{display:flex;align-items:center;gap:7px}.dpr-collection-tabs .dpr-collection-tab b{display:inline-flex;align-items:center;justify-content:center;min-width:19px;height:19px;padding:0 5px;border-radius:10px;background:#f0f3f4;color:#718087;box-sizing:border-box;font:600 10px 'SF Mono',Menlo,monospace}.dpr-collection-tabs .dpr-collection-tab.active b{background:#e5f6f7;color:#149DAA}
#dpr-task-table{background:#fff}#dpr-task-table td{background:#fff}#dpr-task-table tbody tr:hover td{background:#fbfdfd}
.dpr-task-filters{width:100%;margin-bottom:12px;box-sizing:border-box}.dpr-task-filters .ff{min-width:155px}.dpr-task-filters .ff input,.dpr-task-filters .ff select{min-width:155px}
.dpr-collection-drawer{width:500px;max-width:calc(100vw - 24px)}.dpr-collection-drawer .drawer-body{padding-top:24px}.dpr-collection-drawer .fg{margin-bottom:20px}.dpr-collection-drawer .fg input,.dpr-collection-drawer .fg select{height:38px;box-sizing:border-box;background:#fff}.dpr-optional{color:#829096;font-weight:400}.dpr-field-help{margin-top:1px;color:#849298;font-size:11.5px;line-height:1.5}.dpr-processing-drawer{width:720px}.dpr-processing-assignment{margin-top:8px;padding-top:18px;border-top:1px solid #edf1f2}.dpr-processing-assignment-title{display:flex;align-items:baseline;justify-content:space-between;gap:14px;margin-bottom:12px}.dpr-processing-assignment-title b{font-size:14px;color:#2b434b}.dpr-processing-assignment-title span{font-size:11px;color:#829197}.dpr-processing-assignment-card{margin-bottom:10px;padding:12px;border:1px solid #e2e8ea;border-radius:8px;background:#fafcfc}.dpr-processing-assignment-head{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:10px}.dpr-processing-assignment-head>div{display:flex;align-items:center;gap:7px}.dpr-processing-assignment-head b{font-size:12.5px;color:#2e464e}.dpr-processing-assignment-head>div span{padding:2px 6px;border-radius:8px;background:#e5f5ee;color:#2f8064;font-size:9.5px}.dpr-processing-assignment-head label{display:flex;align-items:center;gap:7px;color:#718087;font-size:11px}.dpr-processing-assignment-head select{width:94px;height:30px;padding:0 7px;border:1px solid #d8e0e3;border-radius:5px;background:#fff;color:#324950}.dpr-processing-assignment-cols,.dpr-processing-assignment-row{display:grid;grid-template-columns:1fr 110px 26px;align-items:center;gap:7px}.dpr-processing-assignment-cols{margin-bottom:4px;color:#879398;font-size:9.5px}.dpr-processing-assignment-row{margin-bottom:6px}.dpr-processing-assignment-row select,.dpr-processing-percent input{width:100%;height:32px;box-sizing:border-box;border:1px solid #d9e0e2;border-radius:6px;background:#fff;color:#334a52}.dpr-processing-assignment-row select{padding:0 8px}.dpr-processing-percent{position:relative}.dpr-processing-percent input{padding:0 24px 0 8px}.dpr-processing-percent span{position:absolute;right:8px;top:7px;color:#89959a;font-size:11px}.dpr-processing-assignment-remove{width:26px;height:26px;border:0;background:transparent;color:#a7b0b4;font-size:17px;cursor:pointer}.dpr-processing-assignment-remove:hover{color:#d05a50}.dpr-processing-assignment-foot{display:flex;align-items:center;justify-content:space-between;margin-top:7px}.dpr-processing-assignment-foot button{padding:0;border:0;background:transparent;color:#149DAA;font-size:11px;cursor:pointer}.dpr-processing-assignment-foot span{color:#74848a;font-size:11px}.dpr-processing-assignment-foot b.ok{color:#2f8d70}.dpr-processing-assignment-foot b.bad{color:#c64b40}.dpr-processing-assignment-empty{padding:18px;border:1px dashed #d6dfe2;border-radius:8px;background:#fafcfc;color:#7d8c91;font-size:12px;text-align:center}
.dpr-processing-task-page{position:fixed;z-index:260;top:52px;left:220px;right:0;bottom:0;display:none;background:#f6f8f9;color:#30464e}.dpr-processing-task-page[aria-hidden="false"]{display:flex;flex-direction:column}.dpr-processing-task-page-head{height:70px;display:flex;align-items:center;justify-content:space-between;gap:18px;padding:0 28px;border-bottom:1px solid #e2e8ea;background:#fff}.dpr-processing-task-page-head>div{display:flex;align-items:center;gap:12px}.dpr-processing-task-page-head h2{margin:0;font-size:18px;color:#20383f}.dpr-processing-back{padding:0;border:0;background:transparent;color:#149DAA;font-size:12px;cursor:pointer}.dpr-processing-task-page-body{display:grid;grid-template-columns:208px minmax(0,1fr);flex:1;min-height:0}.dpr-processing-task-menu{padding:22px 12px;border-right:1px solid #e1e7e9;background:#fff}.dpr-processing-task-menu button{display:flex;align-items:center;gap:10px;width:100%;margin-bottom:5px;padding:10px 12px;border:0;border-radius:7px;background:transparent;color:#65767c;text-align:left;font-size:13px;cursor:pointer}.dpr-processing-task-menu button i{display:inline-flex;align-items:center;justify-content:center;width:19px;height:19px;border-radius:50%;background:#edf1f2;color:#7c8c91;font:600 10px sans-serif}.dpr-processing-task-menu button.active{background:#e8f7f8;color:#117a83;font-weight:650}.dpr-processing-task-menu button.active i{background:#149DAA;color:#fff}.dpr-processing-task-form{overflow:auto;padding:30px 38px}.dpr-processing-task-pane{display:none;max-width:1120px;margin:0 auto}.dpr-processing-task-pane.active{display:block}.dpr-page-section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:20px}.dpr-page-section-head h3{margin:0;color:#243d45;font-size:17px}.dpr-page-section-head p{margin:6px 0 0;color:#7a898f;font-size:12px}.dpr-processing-basic-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px 24px;padding:24px;border:1px solid #e2e8ea;border-radius:10px;background:#fff}.dpr-processing-basic-grid .fg{display:flex;flex-direction:column;gap:7px;margin:0;color:#51646b;font-size:12px}.dpr-processing-basic-grid input,.dpr-processing-basic-grid select{height:38px;box-sizing:border-box;border:1px solid #d8e0e3;border-radius:7px;background:#fff;padding:0 11px;color:#324950}.dpr-processing-basic-grid small{color:#869399;font-size:11px;line-height:1.45}.dpr-page-config-block{margin-top:0;padding:18px;background:#fff}.dpr-flow-assignment-layout{display:grid;grid-template-columns:310px minmax(0,1fr);gap:18px;min-height:490px}.dpr-flow-selector,.dpr-flow-node-assignments{border:1px solid #e1e8ea;border-radius:10px;background:#fff}.dpr-flow-selector-tabs{display:flex;padding:10px 12px 0;border-bottom:1px solid #e8edef}.dpr-flow-selector-tabs button{flex:1;padding:9px 4px;border:0;border-bottom:2px solid transparent;background:transparent;color:#728188;font-size:12px;cursor:pointer}.dpr-flow-selector-tabs button.active{border-bottom-color:#149DAA;color:#117a83;font-weight:650}.dpr-flow-choice{display:flex;flex-direction:column;gap:5px;width:calc(100% - 24px);margin:12px;padding:13px;border:1px solid #e3e9eb;border-radius:8px;background:#fff;color:#3a5158;text-align:left;cursor:pointer}.dpr-flow-choice:hover,.dpr-flow-choice.selected{border-color:#69bdc4;background:#f1fbfb}.dpr-flow-choice b{font-size:12.5px}.dpr-flow-choice span{color:#819096;font-size:10.5px}.dpr-flow-node-assignments{padding:18px;overflow:auto}.dpr-flow-assignment-summary{display:flex;align-items:baseline;gap:8px;padding-bottom:14px;border-bottom:1px solid #e7ecee;color:#829096;font-size:11px}.dpr-flow-assignment-summary b{color:#2e464e;font-size:14px}.dpr-flow-node-card{margin-top:14px;padding:14px;border:1px solid #e2e9eb;border-radius:8px;background:#fbfcfc}.dpr-flow-node-card-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:11px}.dpr-flow-node-card-head>div{display:flex;align-items:center;gap:7px}.dpr-flow-node-card-head b{font-size:13px;color:#30484f}.dpr-flow-node-card-head>div span{padding:2px 6px;border-radius:8px;background:#e5f5ee;color:#2f8064;font-size:9.5px}.dpr-flow-total{color:#74848a;font-size:11px}.dpr-flow-total b.ok{color:#2f8d70}.dpr-flow-total b.bad{color:#c64b40}.dpr-flow-assignment-cols,.dpr-flow-assignment-row{display:grid;grid-template-columns:100px minmax(150px,1fr) 100px 26px;gap:7px;align-items:center}.dpr-flow-assignment-cols{margin-bottom:5px;color:#89959a;font-size:9.5px}.dpr-flow-assignment-row{margin-bottom:7px}.dpr-flow-assignment-row select,.dpr-flow-assignment-percent input{width:100%;height:34px;box-sizing:border-box;border:1px solid #d8e0e3;border-radius:6px;background:#fff;padding:0 9px;color:#344c54}.dpr-flow-assignment-percent{position:relative}.dpr-flow-assignment-percent input{padding-right:24px}.dpr-flow-assignment-percent span{position:absolute;right:8px;top:8px;color:#89959a;font-size:11px}.dpr-flow-add-assignment{padding:0;border:0;background:transparent;color:#149DAA;font-size:11px;cursor:pointer}.dpr-flow-add-assignment:disabled{opacity:.45;cursor:not-allowed}@media(max-width:900px){.dpr-processing-task-page{left:0}.dpr-processing-task-page-body{grid-template-columns:1fr}.dpr-processing-task-menu{display:flex;overflow:auto;padding:8px;border-right:0;border-bottom:1px solid #e1e7e9}.dpr-processing-task-menu button{min-width:max-content;margin:0}.dpr-processing-task-form{padding:20px}.dpr-flow-assignment-layout{grid-template-columns:1fr}.dpr-processing-basic-grid{grid-template-columns:1fr}}
.dpr-source-task-note{padding:12px 14px;border:1px solid #dcebed;border-radius:8px;background:#f4fafb;color:#567078;font-size:12px;line-height:1.6}.dpr-processing-task-note{max-width:760px;color:#5d737b;font-size:12px}.dpr-task-enable{display:inline-flex;align-items:center;gap:6px;cursor:pointer}.dpr-task-enable input{display:none}.dpr-task-enable i{position:relative;width:30px;height:17px;border-radius:10px;background:#cbd4d7;transition:.2s}.dpr-task-enable i:after{content:"";position:absolute;left:2px;top:2px;width:13px;height:13px;border-radius:50%;background:#fff;transition:.2s}.dpr-task-enable input:checked+i{background:#149DAA}.dpr-task-enable input:checked+i:after{left:15px}.dpr-task-enable span{font-size:11px;color:#536a72}.dpr-task-enable+small{display:block;margin-top:5px}.dpr-filter-summary{display:block;max-width:240px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#4d656d}.dpr-flow-binding-list{display:flex;flex-direction:column;gap:6px;min-width:480px}.dpr-flow-binding-chip{display:grid;grid-template-columns:34px minmax(145px,1fr) 30px minmax(170px,.9fr);align-items:center;gap:7px}.dpr-flow-binding-chip span{padding:2px 5px;border-radius:8px;background:#edf5f6;color:#247783;font-size:9px;text-align:center}.dpr-flow-binding-chip b{font-size:10.5px;font-weight:500;color:#405860}.dpr-flow-binding-chip code{font-size:9.5px;color:#839197}.dpr-flow-progress-line{min-width:170px}.dpr-processing-volume{display:flex;flex-direction:column;gap:3px;white-space:nowrap;color:#74848a;font-size:10px}.dpr-processing-volume b{color:#334b53}.dpr-processing-volume .risk,.dpr-processing-volume .risk b{color:#bc5549}.dpr-task-config-block{margin-top:14px;padding:14px;border:1px solid #e3e9eb;border-radius:9px;background:#fbfcfc}.dpr-task-config-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:12px}.dpr-task-config-head>div{display:flex;flex-direction:column;gap:3px}.dpr-task-config-head b{font-size:13px;color:#2a434b}.dpr-task-config-head span{color:#849298;font-size:10.5px}.dpr-task-config-head button{border:0;background:transparent;color:#149DAA;font-size:11px;cursor:pointer}.dpr-task-config-cols,.dpr-task-config-row{display:grid;align-items:center;gap:7px}.dpr-filter-cols,.dpr-filter-row{grid-template-columns:170px 1fr 26px}.dpr-flow-cols,.dpr-flow-row{grid-template-columns:64px minmax(185px,1fr) 52px minmax(158px,.9fr)}.dpr-task-config-cols{margin-bottom:5px;color:#879399;font-size:9.5px}.dpr-task-config-row{margin-bottom:7px}.dpr-task-config-row select,.dpr-task-config-row input{width:100%;height:34px;box-sizing:border-box;border:1px solid #d8e0e3;border-radius:6px;background:#fff;padding:0 9px;color:#344c54}.dpr-task-config-row code{padding:8px 4px;color:#60747b;font-size:10.5px}.dpr-flow-stage-fixed{font-size:11px;font-weight:600;color:#405860}.dpr-flow-rule-empty{color:#9aa6aa;text-align:center}.dpr-task-config-remove{width:26px;height:26px;border:0;background:transparent;color:#9da9ad;font-size:17px;cursor:pointer}.dpr-task-config-remove:hover{color:#cf584e}.dpr-task-config-empty{padding:12px;border:1px dashed #d8e1e3;border-radius:7px;color:#849298;font-size:11px;text-align:center}
.dpr-flow-binding-chip{grid-template-columns:34px minmax(190px,max-content) minmax(170px,.9fr)}.dpr-flow-binding-name{display:flex;align-items:center;gap:5px;min-width:0;white-space:nowrap}.dpr-flow-binding-name b{overflow:hidden;text-overflow:ellipsis}.dpr-flow-binding-name code{flex:none}
.dpr-scenario-summary{display:flex;align-items:center;gap:28px;margin-bottom:16px;padding:14px 18px;border:1px solid #dce8ea;border-radius:9px;background:#f7fbfb}.dpr-scenario-summary>div{display:flex;align-items:baseline;gap:6px}.dpr-scenario-summary span{color:#66777d;font-size:12px}.dpr-scenario-summary b{color:#149DAA;font-size:24px}.dpr-scenario-summary small{color:#829096}.dpr-scenario-summary p{margin:0 0 0 auto;color:#53666d;font-size:12px}.dpr-capacity-overload{color:#b45246;font-weight:650;white-space:nowrap}.dpr-assignment-context{display:grid;grid-template-columns:1fr;gap:8px;margin-bottom:12px;padding:12px 14px;border:1px solid #e1e7e9;border-radius:7px;background:#fafcfc}.dpr-assignment-context span{display:flex;justify-content:space-between;gap:18px;color:#74848a;font-size:12px}.dpr-assignment-context b{color:#2f464e}.dpr-inline-notice{margin-bottom:18px;padding:10px 12px;border-left:3px solid #e5a64c;border-radius:5px;background:#fff8e8;color:#76591f;font-size:12px}.dpr-inline-notice.success{border-left-color:#69ad8d;background:#f0faf5;color:#3f725d}.dpr-project-scope{display:flex;align-items:center;gap:9px;color:#63757c;font-size:12px;white-space:nowrap}.dpr-project-scope select{min-width:152px;height:36px;padding:0 32px 0 11px;border:1px solid #d8e0e3;border-radius:7px;background:#fff;color:#2d444c}.dpr-allocation-tabs{margin-bottom:16px}.dpr-allocation-funnel{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.dpr-allocation-stage{padding:15px;border:1px solid #e4eaec;border-radius:9px;background:#fbfdfd}.dpr-allocation-stage-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:13px}.dpr-allocation-stage-head>div{display:flex;flex-direction:column;gap:4px}.dpr-allocation-stage-head b{font-size:15px;color:#263f47}.dpr-allocation-stage-head span{font-size:11px;color:#7a898f}.dpr-allocation-stage-head strong{font-size:22px;color:#273f47;text-align:right}.dpr-allocation-stage-head strong small{display:block;font-size:10px;color:#89969b;font-weight:400}.dpr-allocation-bar{display:flex;height:12px;overflow:hidden;border-radius:6px;background:#edf1f2}.dpr-allocation-bar i{display:block;height:100%}.dpr-allocation-bar i.unassigned,.dpr-allocation-legend i.unassigned{background:#d96c62}.dpr-allocation-bar i.assigned,.dpr-allocation-legend i.assigned{background:#e5a64c}.dpr-allocation-bar i.processing,.dpr-allocation-legend i.processing{background:#5c9db3}.dpr-allocation-bar i.completed,.dpr-allocation-legend i.completed{background:#69ad8d}.dpr-allocation-legend{display:grid;grid-template-columns:1fr 1fr;gap:7px 12px;margin-top:12px;color:#6c7c82;font-size:10.5px}.dpr-allocation-legend span{white-space:nowrap}.dpr-allocation-legend b{font-weight:400}.dpr-allocation-legend i{display:inline-block;width:7px;height:7px;border-radius:2px;margin-right:5px}.dpr-allocation-filters{margin-bottom:14px}.dpr-allocation-filters .ff{min-width:135px}.dpr-allocation-filters .ff input,.dpr-allocation-filters .ff select{min-width:135px}.dpr-allocation-table-foot{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:12px;color:#738289;font-size:12px}.dpr-allocation-table-foot button:disabled{opacity:.45;cursor:not-allowed}.dpr-stalled{color:#b45246;font-weight:650;white-space:nowrap}.dpr-link-button{padding:0;border:0;background:transparent;color:#149DAA;font:inherit;cursor:pointer;white-space:nowrap}#dpr-allocation-backlog-table{min-width:1320px}#dpr-allocation-backlog-table th:first-child,#dpr-allocation-backlog-table td:first-child{width:28px;text-align:center}#dpr-stream-backlog-table{min-width:1280px}#dpr-unbound-pool-table{min-width:1180px}#dpr-stream-backlog-table th:first-child,#dpr-stream-backlog-table td:first-child,#dpr-unbound-pool-table th:first-child,#dpr-unbound-pool-table td:first-child{width:28px;text-align:center}.dpr-flow-assignment-filters{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:14px}.dpr-flow-assignment-filters .ff{display:flex;flex-direction:column;gap:6px}.dpr-flow-assignment-filters .ff label{font-size:12px;color:#5b6b72}.dpr-flow-assignment-filters .ff input,.dpr-flow-assignment-filters .ff select{width:100%;height:36px;padding:0 10px;border:1px solid #d9e0e2;border-radius:6px;background:#fff;box-sizing:border-box}.dpr-flow-assignment-filters .filter-actions{display:flex;align-items:flex-end;gap:8px}.dpr-flow-match{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-top:18px;padding:16px 18px;border:1px solid #cfe5e7;border-radius:9px;background:#f4fbfb}.dpr-flow-match>div{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}.dpr-flow-match span{color:#5b6d73;font-size:12px}.dpr-flow-match b{font-size:14px;color:#2a424a}.dpr-flow-match em{font-size:26px;font-style:normal;color:#149DAA}.dpr-flow-match small{color:#839197}.dpr-allocation-drawer{width:500px;max-width:calc(100vw - 24px)}.dpr-allocation-drawer .drawer-body{padding-top:22px}.dpr-allocation-drawer .fg{margin-bottom:18px}.dpr-allocation-drawer .fg input,.dpr-allocation-drawer .fg select,.dpr-allocation-drawer .fg textarea{width:100%;box-sizing:border-box;background:#fff}.dpr-allocation-drawer .fg input,.dpr-allocation-drawer .fg select{height:38px}.dpr-allocation-drawer .fg textarea{padding:9px 11px;border:1px solid #d9e0e2;border-radius:6px;resize:vertical}.dpr-drawer-summary{margin-bottom:20px;padding:12px 14px;border-radius:7px;background:#f1f7f8;color:#53666d;font-size:12px}.dpr-drawer-summary b{color:#149DAA}
.dpr-flow-assignment-cols,.dpr-flow-assignment-row{grid-template-columns:100px minmax(150px,1fr) 26px}
.dpr-dispatch-stage-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.dpr-dispatch-stage-card{display:block;width:100%;padding:16px;border:1px solid #e2e9eb;border-radius:9px;background:#fff;color:#30464e;text-align:left;cursor:pointer;transition:.18s}.dpr-dispatch-stage-card:hover{border-color:#8bcbd0;box-shadow:0 3px 12px rgba(20,157,170,.08)}.dpr-dispatch-stage-card.active{border-color:#149DAA;background:#f3fbfb;box-shadow:0 0 0 1px rgba(20,157,170,.1)}.dpr-dispatch-stage-title{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}.dpr-dispatch-stage-title>span{font-size:15px;font-weight:650}.dpr-dispatch-stage-title>b{font-size:22px;color:#20383f;text-align:right}.dpr-dispatch-stage-title small{display:block;margin-top:2px;color:#879399;font-size:10px;font-weight:400}.dpr-dispatch-stage-values{display:grid;grid-template-columns:1fr 1fr;gap:7px 12px;margin-top:11px;color:#718188;font-size:10.5px}.dpr-dispatch-stage-values span{white-space:nowrap}.dpr-dispatch-stage-values b{margin-left:3px;color:#425860;font-weight:600}.dpr-dispatch-stage-values i{display:inline-block;width:7px;height:7px;margin-right:5px;border-radius:2px}.dpr-dispatch-stage-values i.unassigned{background:#d96c62}.dpr-dispatch-stage-values i.assigned{background:#e5a64c}.dpr-dispatch-stage-values i.processing{background:#5c9db3}.dpr-dispatch-stage-values i.completed{background:#69ad8d}.dpr-dispatch-alerts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:16px}.dpr-dispatch-alert{display:flex;align-items:baseline;gap:8px;min-height:72px;padding:14px 16px;border:1px solid #e2e8ea;border-radius:9px;background:#fff;color:#5e7077;text-align:left}.dpr-dispatch-alert:is(button){font:inherit;cursor:pointer}.dpr-dispatch-alert:is(button):hover{border-color:#8bcbd0;background:#fbfefe}.dpr-dispatch-alert>span{font-size:12px}.dpr-dispatch-alert>b{color:#263e46;font-size:13px}.dpr-dispatch-alert em{color:#149DAA;font-size:24px;font-style:normal}.dpr-dispatch-alert small{margin-left:auto;color:#839096;font-size:10.5px}.dpr-dispatch-alert strong{color:#52676e}.dpr-dispatch-alert.risk em{color:#c85a4f}.dpr-dispatch-toolbar{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:14px}.dpr-dispatch-type-switch{display:flex;align-items:center;gap:20px}.dpr-dispatch-type-button{position:relative;padding:4px 1px 10px;border:0;background:transparent;color:#6c7c82;font-size:12px;cursor:pointer}.dpr-dispatch-type-button.active{color:#149DAA;font-weight:650}.dpr-dispatch-type-button.active:after{content:"";position:absolute;right:0;bottom:0;left:0;height:2px;border-radius:2px;background:#149DAA}.dpr-dispatch-search{display:flex;align-items:center;gap:8px}.dpr-dispatch-search input{width:230px;height:34px;padding:0 10px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;box-sizing:border-box}.dpr-dispatch-issue{display:inline-flex;padding:3px 8px;border-radius:10px;font-size:10.5px;font-weight:650;white-space:nowrap}.dpr-dispatch-issue.capacity{background:#fdebea;color:#b34239}.dpr-dispatch-issue.unbound{background:#fff2d7;color:#946118}#dpr-dispatch-issue-table{min-width:1120px}.dpr-dispatch-object{display:flex;flex-direction:column;gap:5px;min-width:205px}.dpr-dispatch-object span{display:grid;grid-template-columns:54px 1fr;align-items:center;gap:7px}.dpr-dispatch-object i{color:#8a979c;font-size:10px;font-style:normal}.dpr-dispatch-object code{color:#2f474f;font-size:10.5px}.dpr-dispatch-object code.empty{color:#a5afb2}.dpr-dispatch-source-link{justify-self:start;padding:0;border:0;background:transparent;color:#149DAA;font-size:10.5px;cursor:pointer}.dpr-dispatch-source-link:hover{color:#0f7780}.dpr-dispatch-source-drawer{width:420px;max-width:calc(100vw - 24px)}.dpr-dispatch-source-list{display:flex;flex-direction:column;border:1px solid #e3e9eb;border-radius:8px;overflow:hidden}.dpr-dispatch-source-list>div{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:12px 14px;border-bottom:1px solid #edf1f2}.dpr-dispatch-source-list>div:last-child{border-bottom:0}.dpr-dispatch-source-list span{color:#74858b;font-size:11px}.dpr-dispatch-source-list code{color:#304850;font-size:11px}.dpr-dispatch-current small{display:block;margin-top:4px;color:#849197;font-size:10.5px}.dpr-dispatch-current{display:block;max-width:250px;color:#405860;line-height:1.45}.dpr-dispatch-empty{display:none;padding:24px;color:#879499;text-align:center}.dpr-dispatch-table-summary{margin-top:12px;color:#78878d;font-size:11.5px}.dpr-dispatch-table-summary b{color:#3e565e}.dpr-dispatch-compare{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:18px}.dpr-dispatch-compare>div{padding:14px;border:1px solid #e1e8ea;border-radius:8px;background:#fafcfc}.dpr-dispatch-compare>div.next{border-color:#cce4e6;background:#f5fbfb}.dpr-dispatch-compare>div>span{display:block;margin-bottom:11px;color:#546970;font-size:12px;font-weight:650}.dpr-dispatch-compare dl{display:grid;grid-template-columns:72px 1fr;gap:9px 8px;margin:0;font-size:11px}.dpr-dispatch-compare dt{color:#849197}.dpr-dispatch-compare dd{margin:0;color:#344c54}.dpr-dispatch-compare .fg{margin-bottom:10px}.dpr-dispatch-current-card{display:flex;flex-direction:column;gap:5px;margin-bottom:18px;padding:13px 14px;border:1px solid #e1e8ea;border-radius:8px;background:#fafcfc}.dpr-dispatch-current-card span{color:#849197;font-size:10.5px}.dpr-dispatch-current-card b{color:#334b53;font-size:12px}.dpr-dispatch-current-card small{color:#75868c;font-size:11px}.dpr-dispatch-reprocess-drawer{width:760px;max-width:calc(100vw - 24px)}.dpr-dispatch-reprocess-drawer .drawer-body{padding-top:18px}.dpr-dispatch-steps{display:flex;align-items:center;justify-content:center;gap:10px;margin:0 0 22px}.dpr-dispatch-steps span{display:flex;align-items:center;gap:7px;color:#89969b;font-size:11.5px}.dpr-dispatch-steps span b{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:#edf1f2;color:#7b898f}.dpr-dispatch-steps span.active{color:#149DAA;font-weight:650}.dpr-dispatch-steps span.active b{background:#149DAA;color:#fff}.dpr-dispatch-steps i{width:70px;height:1px;background:#dfe6e8}.dpr-dispatch-step{display:none}.dpr-dispatch-step.active{display:block}.dpr-dispatch-filter-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.dpr-dispatch-filter-grid .ff{display:flex;flex-direction:column;gap:6px}.dpr-dispatch-filter-grid label{color:#62747b;font-size:11.5px}.dpr-dispatch-filter-grid input,.dpr-dispatch-filter-grid select{width:100%;height:36px;padding:0 9px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;box-sizing:border-box}.dpr-dispatch-filter-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:14px}.dpr-dispatch-match{display:flex;align-items:baseline;gap:11px;margin:16px 0;padding:13px 15px;border:1px solid #cfe5e7;border-radius:8px;background:#f4fbfb}.dpr-dispatch-match span{color:#60747b;font-size:11.5px}.dpr-dispatch-match b{color:#2c454d;font-size:12px}.dpr-dispatch-match em{color:#149DAA;font-size:23px;font-style:normal}.dpr-dispatch-match small{margin-left:auto;color:#819096;font-size:10.5px}.dpr-dispatch-preview-title{margin:17px 0 9px;color:#3a5159;font-size:12px;font-weight:650}#dpr-dispatch-reprocess-preview{min-width:680px}
#drawerDispatchResource{width:640px}#drawerDispatchBinding{width:720px}.dpr-dispatch-backlog-context{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(190px,1.4fr) minmax(85px,.7fr);gap:10px;margin-bottom:18px}.dpr-dispatch-backlog-context>div{display:flex;flex-direction:column;gap:5px;padding:11px 12px;border:1px solid #e1e8ea;border-radius:7px;background:#fafcfc}.dpr-dispatch-backlog-context span{color:#849197;font-size:10.5px}.dpr-dispatch-backlog-context b{color:#344c54;font-size:11px;font-weight:600}.dpr-dispatch-backlog-context>div:nth-child(2) b{white-space:nowrap}.dpr-dispatch-backlog-context i{font-style:normal}.dpr-dispatch-assignment-block{margin:0 0 18px}.dpr-dispatch-assignment-cols,.dpr-dispatch-assignment-row{grid-template-columns:92px minmax(190px,1fr) 112px 26px}.dpr-dispatch-assignment-type:disabled{border-color:#e1e5e6;background:#f1f3f4;color:#8b969a;cursor:not-allowed}.dpr-dispatch-assignment-total{display:flex;align-items:center;justify-content:flex-end;gap:9px;margin-top:9px;padding-top:10px;border-top:1px solid #e5eaec;color:#78878d;font-size:11px}.dpr-dispatch-assignment-total b{color:#405860}.dpr-dispatch-assignment-total b.over{color:#c24f45}.dpr-dispatch-task-picker{margin-bottom:8px!important}.dpr-dispatch-binding-flows{margin:0 0 18px}.dpr-dispatch-flow-readonly{min-height:34px}.dpr-dispatch-flow-name,.dpr-dispatch-flow-rule{overflow:hidden;color:#405860;font-size:10.5px;text-overflow:ellipsis;white-space:nowrap}.dpr-dispatch-flow-rule{color:#60747b}
.dpr-dispatch-task-row td{border-top:1px solid #dfe8ea;background:#fbfdfd}.dpr-dispatch-task-row.expanded td{background:#f4fbfb}.dpr-dispatch-stage-row td{background:#fff}.dpr-dispatch-stage-row td:first-child{padding-left:20px}.dpr-dispatch-tree-branch{color:#8fb0b6;font-size:15px}.dpr-dispatch-child-label{color:#7d8b90;font-size:10.5px}.dpr-dispatch-stage-count{padding:0;border:0;background:transparent;color:#149DAA;font-size:11px;cursor:pointer}.dpr-dispatch-stage-count:hover{color:#0f7780}
.dpr-task-name{color:#20383f}.dpr-task-name:hover{color:#149DAA}.dpr-priority{font-weight:650;color:#354b52}.dpr-task-actions{display:flex;align-items:center;gap:10px;white-space:nowrap}.dpr-task-actions a,.dpr-task-actions button{padding:0;border:0;background:transparent;color:#149DAA;font:inherit;cursor:pointer}.dpr-task-actions a:hover,.dpr-task-actions button:hover{color:#0f7780}.dpr-task-progress-stack{display:flex;flex-direction:column;gap:5px;min-width:230px}.dpr-task-progress-stack.collection{max-width:300px}.dpr-task-progress-item{display:grid;grid-template-columns:30px minmax(170px,1fr);align-items:center;gap:6px;white-space:nowrap}.dpr-task-progress-label{font-size:10.5px;color:#354b52;font-weight:600}.dpr-task-progress-line{position:relative;height:14px;background:#edf1f2;border-radius:7px;overflow:hidden}.dpr-task-progress-line i{position:absolute;inset:0 auto 0 0;display:block;height:100%;border-radius:7px;background:#149DAA;opacity:.62}.dpr-task-progress-line i.blue{background:#5a82d1}.dpr-task-progress-line i.teal{background:#149DAA}.dpr-task-progress-line i.green{background:#5fab91}.dpr-task-progress-line b{position:relative;z-index:1;display:block;padding:0 6px;font:9px/14px 'SF Mono',Menlo,monospace;color:#30454d;text-align:center;white-space:nowrap}.dpr-record-page{width:100%;max-width:100%;min-width:0;overflow:hidden;padding-top:2px;box-sizing:border-box}.dpr-record-top{display:flex;align-items:center;justify-content:space-between;gap:16px;max-width:100%;margin-bottom:14px}.dpr-record-top>div{display:flex;align-items:center;gap:12px;min-width:0}.dpr-record-top a{font-size:12px;color:#149DAA}.dpr-record-top b{font-size:16px;color:#233a42}.dpr-record-top code{font:11px 'SF Mono',Menlo,monospace;color:#718188;background:#edf2f3;padding:3px 7px;border-radius:4px}.dpr-record-filters{width:100%;max-width:100%;margin-bottom:16px;box-sizing:border-box}.dpr-record-summary{display:flex;align-items:center;gap:8px;max-width:100%;margin:0 0 12px;color:#52636a;font-size:13px}.dpr-record-summary span:first-child:after{content:"：";margin-left:2px}.table-wrap.dpr-record-table-wrap{width:100%;max-width:100%;min-width:0;overflow-x:auto;overflow-y:hidden;background:#fff;box-sizing:border-box}.dpr-record-table{width:100%;min-width:1480px}.dpr-record-table.dpr-collection-record-table{min-width:940px}.dpr-record-table td{vertical-align:middle}.dpr-video-group{display:flex;align-items:center;white-space:nowrap}.dpr-record-table .vid-thumb{width:86px;height:54px}.dpr-record-tag{display:inline-flex;align-items:center;padding:3px 8px;border:1px solid transparent;border-radius:5px;font-size:11.5px;white-space:nowrap}.dpr-record-tag.green{color:#2f8d60;background:#edf8f2;border-color:#caead9}.dpr-record-tag.orange{color:#a96b13;background:#fff8e6;border-color:#f5dda4}.dpr-record-tag.red{color:#b7473f;background:#fdeeee;border-color:#f3cbc8}.dpr-record-tag.blue{color:#4f69aa;background:#eef2fb;border-color:#cad5f0}.dpr-record-tag.teal{color:#117a83;background:#e8f7f8;border-color:#b9e3e7}.dpr-record-tag.purple{color:#7447ad;background:#f4edfb;border-color:#ddc9f2}.dpr-record-tag.gray{color:#7b878c;background:#f3f5f5;border-color:#e2e6e7}.dpr-record-operator{font-size:11.5px;color:#67777d;white-space:nowrap}.dpr-record-actions{white-space:nowrap}.dpr-record-actions a{margin-right:10px;color:#149DAA}
.dpr-collection-progress-line{min-width:190px}
.dpr-data-management{width:100%;max-width:100%;min-width:0;overflow:hidden}.dpr-data-management .det-tabs{margin-bottom:16px}.dpr-management-record-table{width:100%;min-width:1240px}.dpr-management-record-table .vid-thumb{width:76px;height:48px}.dpr-third-party-table{width:100%;min-width:1080px}.dpr-management-summary{display:flex;align-items:center;justify-content:space-between;gap:16px;margin:0 0 14px;color:#52636a;font-size:13px}.dpr-management-summary .btn{flex:none}
.dpr-tree-toggle{width:24px;height:24px;margin-right:7px;padding:0;border:0;border-radius:5px;background:#edf5f6;color:#147c86;cursor:pointer}.dpr-flow-link{padding:0;border:0;background:transparent;color:#149DAA;font-size:12px;cursor:pointer}.dpr-process-tree-row>td{padding:0!important;background:#f8fafb!important}.dpr-process-tree{padding:14px 20px 17px 50px}.dpr-process-tree-meta{display:flex;gap:24px;flex-wrap:wrap;margin-bottom:10px;color:#6c7d83;font-size:11.5px}.dpr-process-tree table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e8ea;border-radius:7px;overflow:hidden}.dpr-process-tree th,.dpr-process-tree td{padding:9px 12px;border-bottom:1px solid #edf1f2;font-size:11.5px;text-align:left}.dpr-process-tree th{background:#f2f6f7;color:#68787e}.dpr-process-tree tbody tr:last-child td{border-bottom:0}
.dpr-record-detail-meta{display:flex;gap:22px;flex-wrap:wrap;margin:0 0 16px;padding:11px 14px;border:1px solid #e5eaec;border-radius:8px;background:#fff;color:#6a7a80;font-size:12px}.dpr-record-detail-meta code{font:11px 'SF Mono',Menlo,monospace;color:#486068}.dpr-record-detail-meta b{color:#2f454d}.dpr-record-page>.det-tabs{margin-bottom:16px}.dpr-detail-video-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:18px}.dpr-detail-video{position:relative;display:flex;align-items:center;justify-content:center;aspect-ratio:16/9;border-radius:8px;background:linear-gradient(135deg,#283545,#17202c);color:#fff}.dpr-detail-video span{position:absolute;left:12px;top:10px;font-size:11px;color:rgba(255,255,255,.72)}.dpr-detail-video b{font-size:26px;color:rgba(255,255,255,.72)}.dpr-trajectory-card{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:12px}.dpr-trajectory-card>div{display:flex;flex-direction:column;gap:4px;padding:13px;border:1px solid #e5eaec;border-radius:8px;background:#fff}.dpr-trajectory-card span{font-size:11px;color:#7c8a8f}.dpr-trajectory-card b{font-size:15px;color:#2a424a}.dpr-trajectory-chart{display:flex;align-items:center;justify-content:center;height:230px;border:1px dashed #cdd8dc;border-radius:8px;background:linear-gradient(180deg,#fbfdfd,#f3f8f9);color:#7e8d92;font-size:12px}.dpr-version-switch{display:flex;gap:8px;margin-bottom:12px}.dpr-version-button{padding:6px 14px;border:1px solid #dce4e6;border-radius:6px;background:#fff;color:#617278;cursor:pointer}.dpr-version-button.active{border-color:#149DAA;background:#e8f7f8;color:#117a83;font-weight:650}.dpr-version-pane{padding:16px;border:1px solid #e5eaec;border-radius:8px;background:#fff;margin-bottom:18px}.dpr-version-meta{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.dpr-version-meta>div{display:flex;flex-direction:column;gap:6px}.dpr-version-meta span{font-size:11px;color:#7b898f}.dpr-version-meta b{font-size:12px;color:#30474f}.dpr-version-note{display:flex;gap:12px;margin-top:14px;padding-top:12px;border-top:1px solid #eef1f2;font-size:12px}.dpr-version-note b{color:#30474f}.dpr-version-note span{color:#6f7f85}
.dpr-record-preview-page{background:#fff;border:1px solid #e7ecee;border-radius:10px;padding:18px}.dpr-preview-toolbar{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;min-height:43px;border-bottom:1px solid #e6ebed;margin-bottom:16px}.dpr-preview-tabs{display:flex;align-items:flex-end;gap:4px;flex:none}.dpr-preview-tab{padding:10px 16px;border:0;border-bottom:2px solid transparent;background:transparent;color:#66777d;font-size:13px;cursor:pointer}.dpr-preview-tab:hover{color:#149DAA}.dpr-preview-tab.active{color:#149DAA;border-bottom-color:#149DAA;font-weight:650}.dpr-preview-pane{min-height:560px}.dpr-preview-camera-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-bottom:16px}.dpr-preview-camera{position:relative;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:7px;height:150px;border-radius:8px;background:linear-gradient(135deg,#283545,#131b27);color:rgba(255,255,255,.72)}.dpr-preview-camera>span{position:absolute;left:9px;top:8px;padding:2px 7px;border-radius:4px;background:rgba(0,0,0,.58);font:10px 'SF Mono',Menlo,monospace;color:#fff}.dpr-preview-camera>b{font-size:24px}.dpr-preview-camera>small{font-size:10px;color:rgba(255,255,255,.42)}.dpr-preview-traj-bar{display:flex;align-items:center;gap:14px;padding:10px 0;border-bottom:1px solid #edf1f2;margin-bottom:10px}.dpr-preview-traj-tabs{display:flex;align-items:center;gap:6px;flex:1}.dpr-preview-traj-tabs button{padding:5px 12px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#607178;font-size:11.5px;cursor:pointer}.dpr-preview-traj-tabs button.on{border-color:#149DAA;background:#149DAA;color:#fff}.dpr-preview-traj-tabs>i{width:1px;height:18px;background:#e3e8ea;margin:0 2px}.dpr-preview-traj-legend{display:flex;gap:12px;color:#65767c;font-size:11px}.dpr-preview-traj-legend i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:4px}.dpr-preview-traj-legend .cmd{background:#1F80A0}.dpr-preview-traj-legend .state{background:#52c41a}.dpr-preview-play{display:flex;gap:6px}.dpr-preview-play button{width:29px;height:29px;border:1px solid #dfe5e7;border-radius:6px;background:#fff;color:#149DAA;cursor:pointer}.dpr-preview-traj-views{height:340px;overflow:hidden}.dpr-preview-traj-grid{width:100%;height:100%;border-collapse:collapse;table-layout:fixed}.dpr-preview-traj-grid th{padding:5px 10px;border-bottom:1px solid #edf1f2;text-align:center;font-size:12px;color:#344b53}.dpr-preview-traj-grid th:first-child,.dpr-preview-traj-grid td:first-child{width:34px;text-align:center;color:#78868b}.dpr-preview-traj-grid td{padding:3px 10px;border-bottom:1px solid #f4f6f7}.dpr-preview-spark{display:block;width:100%;height:100%;min-height:18px}.dpr-preview-base-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;height:100%}.dpr-preview-base-grid>div{display:flex;flex-direction:column;gap:12px;padding:14px;border:1px solid #e5eaec;border-radius:8px;color:#40575f;font-size:12px}.dpr-preview-chart-line{display:block;flex:1;border-radius:6px;background-color:#f8fbfb;background-size:28px 28px;background-image:linear-gradient(#ebf0f1 1px,transparent 1px),linear-gradient(90deg,#ebf0f1 1px,transparent 1px);position:relative}.dpr-preview-chart-line:after{content:"";position:absolute;left:5%;right:5%;top:45%;height:3px;background:#149DAA;transform:skewY(-8deg);box-shadow:0 13px 0 #62aa72}.dpr-preview-chart-line.two:after{left:22%;right:22%;top:49%;height:90px;border:3px solid #149DAA;border-radius:50%;background:transparent;transform:none;box-shadow:5px 4px 0 #62aa72}.dpr-preview-moz{position:relative;height:100%;overflow:hidden;border:1px solid #e5eaec;border-radius:8px;background:#fbfcfd}.dpr-preview-moz-floor{position:absolute;left:0;right:0;bottom:0;height:70%;background-size:40px 40px;background-image:linear-gradient(#e8edef 1px,transparent 1px),linear-gradient(90deg,#e8edef 1px,transparent 1px);transform:perspective(600px) rotateX(55deg);transform-origin:bottom}.dpr-preview-robot{position:absolute;left:48%;top:40%;display:flex;flex-direction:column;align-items:center;font-size:62px;color:#c5ccd1}.dpr-preview-robot span{font-size:11px;color:#6d7d83}.dpr-preview-moz-info{position:absolute;right:14px;top:14px;display:flex;flex-direction:column;gap:8px;width:290px;padding:12px;border:1px solid #e3e9eb;border-radius:9px;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.05);font:10px 'SF Mono',Menlo,monospace;color:#687980}.dpr-preview-moz-info b{font:600 12px sans-serif;color:#314850}.dpr-preview-slider{width:100%;margin-top:13px;accent-color:#149DAA}.dpr-process-switcher{display:flex;align-items:center;gap:10px;justify-content:flex-end;min-width:0;margin:0 0 7px auto;white-space:nowrap}.dpr-process-switcher label{display:flex;align-items:center;gap:6px;color:#64757b;font-size:11.5px}.dpr-process-switcher select{width:146px;min-width:0;height:32px;padding:0 9px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#324850}.dpr-process-switcher label:first-child select{width:190px}.dpr-process-version-meta{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:14px}.dpr-process-version-meta>div{display:flex;flex-direction:column;gap:5px;padding:10px 12px;border:1px solid #e7ecee;border-radius:7px;background:#fafcfc}.dpr-process-version-meta span{font-size:10.5px;color:#7c8a8f}.dpr-process-version-meta b{font-size:12px;color:#30474f}.dpr-preview-seg-timeline{margin:16px 0 8px}.dpr-preview-seg-row{display:flex;align-items:center;gap:8px}.dpr-preview-seg-row>span{display:flex;align-items:center;justify-content:center;width:23px;height:23px;border-radius:50%;background:#e8f5f6;color:#127a84;font-size:10.5px;font-weight:650}.dpr-preview-seg-track{display:flex;flex:1;height:15px;gap:2px;overflow:hidden;border-radius:4px;background:#f1f4f5}.dpr-preview-segment{height:100%;cursor:pointer}.dpr-preview-segment:hover{filter:brightness(1.06)}.dpr-preview-process-caption{margin:18px 0 5px;color:#334b53;font-size:13px;font-weight:650}.dpr-preview-process-caption span{margin-left:7px;color:#849197;font-size:11px;font-weight:400}.dpr-preview-process-table{width:100%;border-collapse:collapse;font-size:12px}.dpr-preview-process-table th{padding:8px 11px;border-bottom:1px solid #e8edef;text-align:left;color:#77868c;font-weight:500}.dpr-preview-process-table td{padding:8px 11px;border-bottom:1px solid #f1f4f5;color:#354b52}.dpr-preview-process-table tr:hover td{background:#fafcfc}.dpr-preview-process-parent td{background:#f8fafb;font-weight:650}.dpr-preview-process-num{display:inline-flex;align-items:center;justify-content:center;width:19px;height:19px;margin-right:7px;border-radius:50%;background:#edf1f2;color:#6d7c82;font-size:10px}.dpr-preview-process-note{display:flex;gap:12px;margin-top:13px;padding:11px 13px;border:1px solid #e7ecee;border-radius:7px;background:#fafcfc;font-size:11.5px}.dpr-preview-process-note b{color:#344b53}.dpr-preview-process-note span{color:#6f7f85}
.dpr-process-instance-meta{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:10px 12px;border:1px solid #dfe7e9;border-radius:7px;background:#f8fbfb;color:#6d7d83;font-size:10.5px}.dpr-process-instance-meta code{font:10px 'SF Mono',Menlo,monospace;color:#3f5962}.dpr-process-instance-meta b{color:#30474f}
.dpr-history-toolbar{display:flex;align-items:center;justify-content:space-between;gap:18px;min-height:44px;margin-bottom:12px;border-bottom:1px solid #e8edef}.dpr-history-tabs{display:flex;align-items:center;gap:18px;align-self:stretch}.dpr-history-tab{position:relative;padding:0 2px;border:0;background:transparent;color:#687980;font-size:12px;cursor:pointer}.dpr-history-tab.active{color:#149DAA;font-weight:650}.dpr-history-tab.active:after{content:"";position:absolute;right:0;bottom:-1px;left:0;height:2px;background:#149DAA}.dpr-history-switcher{display:flex;align-items:center;gap:10px;padding-bottom:6px;white-space:nowrap}.dpr-history-switcher label{display:flex;align-items:center;gap:6px;color:#64757b;font-size:11.5px}.dpr-history-switcher select{width:148px;height:32px;padding:0 9px;border:1px solid #d8e0e3;border-radius:6px;background:#fff;color:#324850}.dpr-history-switcher label:first-child select{width:210px}.dpr-history-table th:first-child,.dpr-history-table td:first-child{width:18%}.dpr-history-table th:nth-child(2),.dpr-history-table td:nth-child(2){width:22%}
.dpr-pipeline-list{display:flex;flex-direction:column;gap:14px}.dpr-pipeline-card{border:1px solid #e1e7e9;border-radius:9px;padding:17px}.dpr-pipeline-head{display:flex;justify-content:space-between;gap:20px}.dpr-pipeline-head h3{margin:4px 0;font-size:15px}.dpr-pipeline-head span{font-size:11.5px;color:#7a898f}.dpr-version-stack{display:flex;flex-direction:column;gap:4px;text-align:right}.dpr-version-stack span{background:#f4f7f8;padding:4px 8px;border-radius:4px}
.dpr-node-flow{display:flex;align-items:center;gap:6px;overflow-x:auto;padding:17px 0 13px}.dpr-node{display:flex;flex-direction:column;min-width:118px;padding:9px 10px;border:1px solid #dfe6e8;border-radius:7px;background:#fafcfc}.dpr-node i{font:9px 'SF Mono',Menlo,monospace;text-transform:uppercase;color:#839197}.dpr-node b{font-size:12px;margin:3px 0;color:#31484f}.dpr-node small{font:9.5px 'SF Mono',Menlo,monospace;color:#7d8a90;max-width:155px;overflow:hidden;text-overflow:ellipsis}.dpr-node.operator{border-top:3px solid #6d8fda}.dpr-node.human{border-top:3px solid #d18a4f}.dpr-node.gateway{border-top:3px solid #8b6eb5}.dpr-node-arrow{color:#9aa5a9}
.dpr-card-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-top:11px;border-top:1px solid #edf0f1;font-size:11.5px;color:#7c8a90}
.dpr-publish-conditions{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.dpr-publish-conditions span,.dpr-publish-conditions b{padding:10px 12px;background:#f4f7f8;border:1px solid #e3e8ea;border-radius:7px;font-size:12px}.dpr-publish-conditions i{font-style:normal;color:#97a3a7}.dpr-publish-conditions b{background:#e7f6f3;border-color:#b9ddd3;color:#26785f}
.dpr-lineage{display:flex;flex-direction:column;gap:13px}.dpr-line-chain{display:flex;align-items:center;gap:7px;overflow:auto;padding:12px;background:#f7f9fa;border-radius:8px}.dpr-line-node{display:flex;flex-direction:column;min-width:135px;padding:9px;background:#fff;border:1px solid #e2e8ea;border-radius:7px}.dpr-line-node span{font-size:10px;color:#149DAA;font-weight:650;margin-bottom:4px}.dpr-line-arrow{color:#89969b}
.dpr-lock{display:inline-flex;padding:2px 7px;border-radius:10px;background:#f1eafa;color:#6c4ba2;font-size:11px}
.dpr-workbench-builder{width:min(1600px,calc(100vw - 24px))}
.dpr-workbench-builder .drawer-body{padding:14px 16px;overflow:hidden}
.dpr-wb-builder-layout{display:grid;grid-template-columns:minmax(330px,400px) minmax(0,1fr);gap:16px;height:100%;min-height:0}
.dpr-wb-builder-form{min-height:0;overflow-y:auto;padding-right:8px}
.dpr-wb-basic-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.dpr-wb-basic-grid label.full{grid-column:1/-1}
.dpr-wb-basic-grid label{display:flex;flex-direction:column;gap:5px;color:#64777e;font-size:10.5px}
.dpr-wb-basic-grid input,.dpr-wb-basic-grid select,.dpr-wb-basic-grid textarea{height:35px;box-sizing:border-box;border:1px solid #d8e0e3;border-radius:6px;background:#fff;padding:0 9px;color:#334b53}
.dpr-wb-basic-grid textarea{height:70px;padding:8px 9px;resize:vertical;line-height:1.5}
.dpr-wb-component-catalog{margin-top:16px}
.dpr-wb-component-group{margin-bottom:13px}
.dpr-wb-component-group h4{margin:0 0 7px;color:#324b53;font-size:12px}
.dpr-wb-component-group>div{display:grid;grid-template-columns:1fr 1fr;gap:7px}
.dpr-wb-component-option{display:flex;align-items:flex-start;gap:8px;min-height:50px;padding:9px;border:1px solid #e0e7e9;border-radius:7px;background:#fff;cursor:pointer}
.dpr-wb-component-option:has(input:checked){border-color:#69bdc5;background:#f2fbfb}
.dpr-wb-component-option span{display:flex;flex-direction:column;gap:3px}
.dpr-wb-component-option b{color:#344d55;font-size:11px}
.dpr-wb-component-option small{color:#849298;font-size:9.5px;line-height:1.35}
.dpr-wb-live-preview{position:relative;align-self:stretch;min-height:0;border:1px solid #dce4e6;border-radius:10px;background:#fff;overflow:hidden}
.dpr-wb-live-head{display:flex;align-items:center;min-height:40px;box-sizing:border-box;padding:10px 13px;border-bottom:1px solid #e2e8ea;background:#fff}
.dpr-wb-live-head b{font-size:12px}
.dpr-wb-preview-viewport{position:relative;height:calc(100% - 40px);min-height:0;overflow:hidden;background:#fff}
.dpr-wb-preview-viewport iframe{position:absolute;top:0;left:0;width:1440px;height:1120px;border:0;background:#fff;transform:scale(.6);transform-origin:0 0}
.dpr-component-preview-drawer{width:min(1120px,calc(100vw - 32px))}
.dpr-component-preview-drawer .drawer-head>div{min-width:0}
.dpr-component-preview-drawer .drawer-head p{margin:4px 0 0;color:#839197;font-size:11px}
.dpr-component-preview-drawer .drawer-body{padding:16px;background:#eef2f4}
.dpr-component-preview-browser{position:relative;height:720px;overflow:auto;border:1px solid #d9e1e4;border-radius:9px;background:#fff;box-shadow:0 8px 26px rgba(27,48,56,.08)}
.dpr-component-preview-browser iframe{position:absolute;top:0;left:0;width:1440px;height:1040px;border:0;background:#fff;transform:scale(.74);transform-origin:0 0}
.dpr-schema-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.dpr-schema-card{display:flex;flex-direction:column;padding:16px;border:1px solid #e3e9eb;border-radius:9px}.dpr-schema-head{display:flex;justify-content:space-between;gap:8px}.dpr-schema-head h3{margin:5px 0 12px;font-size:14px}.dpr-schema-label{font-size:10px;color:#89969b;text-transform:uppercase;letter-spacing:.5px;margin:9px 0 5px}.dpr-region-row,.dpr-component-list{display:flex;gap:5px;flex-wrap:wrap}.dpr-code{font:9.5px 'SF Mono',Menlo,monospace;background:#f2f5f6;color:#52666d;padding:3px 5px;border-radius:4px}.dpr-schema-card .dpr-card-foot{margin-top:auto;padding-top:13px}
.wbx-data-detail-return{display:flex;align-items:center;gap:14px;margin:0 0 12px;padding:10px 14px;border:1px solid #e3e9eb;border-radius:8px;background:#fff;color:#344b53}.wbx-data-detail-return a{color:#149DAA}.wbx-data-detail-return>b{font-size:14px}.wbx-data-detail-return>span{display:inline-flex;align-items:center;gap:5px;margin-left:auto;color:#7d8b90;font-size:11.5px}.wbx-data-detail-return>span b{color:#149DAA;font:600 11.5px 'SF Mono',Menlo,monospace}
@media(max-width:1180px){.dpr-metrics{grid-template-columns:repeat(2,1fr)}.dpr-role-grid{grid-template-columns:repeat(2,1fr)}.dpr-schema-grid{grid-template-columns:1fr}.dpr-allocation-funnel{grid-template-columns:1fr}.dpr-flow-assignment-filters{grid-template-columns:repeat(2,minmax(150px,1fr))}.dpr-dispatch-stage-grid,.dpr-dispatch-alerts{grid-template-columns:1fr}.dpr-workbench-builder .drawer-body{overflow-y:auto}.dpr-wb-builder-layout{grid-template-columns:1fr;height:auto}.dpr-wb-builder-form{overflow:visible}.dpr-wb-preview-viewport{height:620px}.dpr-wb-live-preview{position:relative}}
@media(max-width:780px){.dpr-intro{align-items:flex-start;flex-direction:column}.dpr-metrics,.dpr-role-grid,.dpr-run-grid,.dpr-detail-video-grid,.dpr-trajectory-card,.dpr-version-meta,.dpr-flow-assignment-filters,.dpr-dispatch-filter-grid,.dpr-dispatch-compare{grid-template-columns:1fr}.dpr-dispatch-toolbar,.dpr-dispatch-alert{align-items:flex-start;flex-direction:column}.dpr-dispatch-alert small{margin-left:0}.dpr-dispatch-search{width:100%;flex-wrap:wrap}.dpr-dispatch-search input{width:100%}.dpr-record-top>div{align-items:flex-start;flex-direction:column;gap:5px}.dpr-record-summary{align-items:flex-start;flex-direction:column}.dpr-flow-match,.dpr-allocation-table-foot{align-items:flex-start;flex-direction:column}}
"""
