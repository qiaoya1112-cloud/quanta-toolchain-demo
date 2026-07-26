"""Configuration-driven product architecture for the Quanta data platform demo.

This module deliberately contains no Flask routes.  It owns the product objects,
navigation, capability registry, demo facts and rendering functions; the portal
only supplies the shared chrome.  Keeping the domain model here makes the
boundaries in ``Quanta-数据平台产品架构调整方案-完善版.md`` executable and testable.
"""

from html import escape


# ---------------------------------------------------------------------------
# Product information architecture
# ---------------------------------------------------------------------------

PAGE_SPECS = {
    "workspace": {
        "path": "/data",
        "title": "工作台总览",
        "subtitle": "按项目与角色汇总待办、风险和交付进度",
        "icon": "&#9638;",
    },
    "projects": {
        "path": "/data/projects",
        "title": "项目管理",
        "subtitle": "权限、数据范围、交付目标与成本归属的协作边界",
        "icon": "&#9635;",
    },
    "business_tasks": {
        "path": "/data/tasks",
        "title": "任务管理",
        "subtitle": "按数据采集、数据导入和数据处理分类管理任务",
        "icon": "&#9776;",
    },
    "human_tasks": {
        "path": "/data/task-pool",
        "title": "人工任务池",
        "subtitle": "人工任务的路由、分配、锁定、SLA 与连续作业",
        "icon": "&#9745;",
    },
    "pipeline_definitions": {
        "path": "/data/pipeline-definitions",
        "title": "流程定义",
        "subtitle": "配置环节、节点、流转并发布不可变流程版本",
        "icon": "&#8644;",
    },
    "pipeline_runs": {
        "path": "/data/pipeline-runs",
        "title": "运行实例",
        "subtitle": "固定流程版本与数据快照，隔离每次实际执行",
        "icon": "&#9654;",
    },
    "data_assets": {
        "path": "/data/assets",
        "title": "数据资产",
        "subtitle": "Recording、Episode、Annotation Version 与 Data Snapshot",
        "icon": "&#9783;",
    },
    "dataset_versions": {
        "path": "/data/dataset-versions",
        "title": "数据集版本",
        "subtitle": "构建、冻结、发布以及下游固定引用",
        "icon": "&#9636;",
    },
    "lineage": {
        "path": "/data/lineage",
        "title": "数据血缘",
        "subtitle": "从发布版本追溯到输入、流程、算子与人员",
        "icon": "&#8646;",
    },
    "capabilities": {
        "path": "/data/capabilities",
        "title": "能力注册",
        "subtitle": "自动节点、人工组件与网关能力的统一注册中心",
        "icon": "&#9881;",
    },
    "workbench_schemas": {
        "path": "/data/workbench-schemas",
        "title": "工作台 Schema",
        "subtitle": "用已注册组件配置人工节点执行界面",
        "icon": "&#9634;",
    },
    "operations": {
        "path": "/data/operations",
        "title": "交付看板",
        "subtitle": "范围、周期、产能和成本的统一运营口径",
        "icon": "&#9681;",
    },
}

NAV_GROUPS = [
    ("工作空间", ["workspace", "projects"]),
    ("任务中心", ["business_tasks", "human_tasks"]),
    ("流程运行", ["pipeline_definitions", "pipeline_runs"]),
    ("数据资产", ["data_assets", "dataset_versions", "lineage"]),
    ("配置中心", ["capabilities", "workbench_schemas"]),
    ("运营治理", ["operations"]),
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
    "multimodal_viewer": ("多模态预览器", "视频、图像、传感器流与时间同步"),
    "timeline_segment_editor": ("时间轴与片段编辑", "片段新增、修改、删除"),
    "annotation_editor": ("标注编辑器", "Schema、草稿与新标注版本"),
    "evidence_panel": ("证据面板", "截图、片段、附件与说明"),
    "instruction_context": ("任务说明", "SOP、操作说明与示例"),
    "task_navigation": ("任务导航", "上一条、下一条、跳过与暂存"),
    "task_submit": ("任务提交器", "保存草稿、提交与进入下一条"),
}

OPERATORS = {
    "op.timestamp-align@2.1.0": "时间戳对齐",
    "op.episode-split@1.6.2": "Episode 切分",
    "op.schema-validate@2.0.0": "格式与 Schema 校验",
    "op.dataset-build@1.2.0": "数据集版本构建",
}

WORKBENCH_SCHEMAS = [
    {
        "id": "wb.action-annotation@4.1",
        "name": "动作分段标注工作台",
        "regions": ["viewer", "timeline", "editor", "evidence", "actions"],
        "components": [
            "multimodal_viewer",
            "timeline_segment_editor",
            "annotation_editor",
            "evidence_panel",
            "instruction_context",
            "task_navigation",
            "task_submit",
        ],
        "actions": ["save_draft", "submit", "skip", "next"],
        "status": "published",
        "frozen": True,
    },
]

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
        "type_name": "数据采集",
        "name": "厨房狭窄台面补采",
        "project": "PRJ-MOZ1-SFT-07",
        "input": "采集 SOP v3.4 · Moz1 设备组",
        "output": "1,240 / 1,500 Recording",
        "pipeline": "—",
        "snapshot": "—",
        "progress": 83,
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


def render_business_tasks():
    task_tabs = [
        ("data_collection_task", "数据采集"),
        ("data_import_task", "数据导入"),
        ("data_processing_task", "数据处理"),
    ]
    type_counts = {task_type: 0 for task_type, _ in task_tabs}
    rows = []
    row_attrs = []
    for item in BUSINESS_TASKS:
        type_counts[item["type"]] += 1
        rows.append(
            [
                f'<code>{_e(item["id"])}</code>',
                f'<b>{_e(item["type_name"])}</b><br><span class="muted">{_e(item["name"])}</span>',
                f'<code>{_e(item["project"])}</code>',
                _e(item["input"]),
                _e(item["output"]),
                f'<code>{_e(item["pipeline"])}</code><br><code>{_e(item["snapshot"])}</code>',
                _progress(item["progress"]),
                _state(item["status"]),
                '<a href="/data/pipeline-runs">查看运行</a>' if item["type"] == "data_processing_task" else '<a href="/data/assets">查看产物</a>',
            ]
        )
        hidden = "" if item["type"] == "data_collection_task" else ' style="display:none;"'
        row_attrs.append(f'data-task-type="{_e(item["type"])}"{hidden}')
    tabs = "".join(
        f'<button type="button" class="dpr-task-tab{" active" if index == 0 else ""}" '
        f'data-task-type="{_e(task_type)}" onclick="dprSwitchTaskTab(this, \'{_e(task_type)}\')">'
        f'{_e(label)} <b>{type_counts[task_type]}</b></button>'
        for index, (task_type, label) in enumerate(task_tabs)
    )
    body = f"""
    <div class="dpr-toolbar">
      <div class="dpr-task-tabs" role="tablist">{tabs}</div>
      <a class="btn btn-primary" href="#" onclick="toast('Demo: 新建任务');return false;">+ 新建任务</a>
    </div>
    """
    body += _table(
        ["任务 ID", "类型 / 名称", "项目", "主要输入", "主要输出", "固定版本 / 快照", "进度", "状态", "操作"],
        rows,
        table_id="dpr-task-table",
        row_attrs=row_attrs,
    )
    body += """
    <script>
    function dprSwitchTaskTab(button, taskType) {
      document.querySelectorAll('.dpr-task-tab').forEach(function(tab) {
        tab.classList.toggle('active', tab === button);
      });
      document.querySelectorAll('#dpr-task-table tbody tr').forEach(function(row) {
        row.style.display = row.dataset.taskType === taskType ? '' : 'none';
      });
    }
    </script>
    """
    return _intro("任务管理", "查看数据采集、数据导入和数据处理任务的进度与产物。", "") + _section("任务列表", body)


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
          <div class="dpr-card-foot"><span>已发布版本冻结</span><a href="/data/workbench/edit">预览工作台 →</a></div>
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


PAGE_RENDERERS = {
    "workspace": render_workspace,
    "projects": render_projects,
    "business_tasks": render_business_tasks,
    "human_tasks": render_human_tasks,
    "pipeline_definitions": render_pipeline_definitions,
    "pipeline_runs": render_pipeline_runs,
    "data_assets": render_data_assets,
    "dataset_versions": render_dataset_versions,
    "lineage": render_lineage,
    "capabilities": render_capabilities,
    "workbench_schemas": render_workbench_schemas,
    "operations": render_operations,
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
.dpr-pipeline-list{display:flex;flex-direction:column;gap:14px}.dpr-pipeline-card{border:1px solid #e1e7e9;border-radius:9px;padding:17px}.dpr-pipeline-head{display:flex;justify-content:space-between;gap:20px}.dpr-pipeline-head h3{margin:4px 0;font-size:15px}.dpr-pipeline-head span{font-size:11.5px;color:#7a898f}.dpr-version-stack{display:flex;flex-direction:column;gap:4px;text-align:right}.dpr-version-stack span{background:#f4f7f8;padding:4px 8px;border-radius:4px}
.dpr-node-flow{display:flex;align-items:center;gap:6px;overflow-x:auto;padding:17px 0 13px}.dpr-node{display:flex;flex-direction:column;min-width:118px;padding:9px 10px;border:1px solid #dfe6e8;border-radius:7px;background:#fafcfc}.dpr-node i{font:9px 'SF Mono',Menlo,monospace;text-transform:uppercase;color:#839197}.dpr-node b{font-size:12px;margin:3px 0;color:#31484f}.dpr-node small{font:9.5px 'SF Mono',Menlo,monospace;color:#7d8a90;max-width:155px;overflow:hidden;text-overflow:ellipsis}.dpr-node.operator{border-top:3px solid #6d8fda}.dpr-node.human{border-top:3px solid #d18a4f}.dpr-node.gateway{border-top:3px solid #8b6eb5}.dpr-node-arrow{color:#9aa5a9}
.dpr-card-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-top:11px;border-top:1px solid #edf0f1;font-size:11.5px;color:#7c8a90}
.dpr-publish-conditions{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.dpr-publish-conditions span,.dpr-publish-conditions b{padding:10px 12px;background:#f4f7f8;border:1px solid #e3e8ea;border-radius:7px;font-size:12px}.dpr-publish-conditions i{font-style:normal;color:#97a3a7}.dpr-publish-conditions b{background:#e7f6f3;border-color:#b9ddd3;color:#26785f}
.dpr-lineage{display:flex;flex-direction:column;gap:13px}.dpr-line-chain{display:flex;align-items:center;gap:7px;overflow:auto;padding:12px;background:#f7f9fa;border-radius:8px}.dpr-line-node{display:flex;flex-direction:column;min-width:135px;padding:9px;background:#fff;border:1px solid #e2e8ea;border-radius:7px}.dpr-line-node span{font-size:10px;color:#149DAA;font-weight:650;margin-bottom:4px}.dpr-line-arrow{color:#89969b}
.dpr-lock{display:inline-flex;padding:2px 7px;border-radius:10px;background:#f1eafa;color:#6c4ba2;font-size:11px}
.dpr-schema-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.dpr-schema-card{display:flex;flex-direction:column;padding:16px;border:1px solid #e3e9eb;border-radius:9px}.dpr-schema-head{display:flex;justify-content:space-between;gap:8px}.dpr-schema-head h3{margin:5px 0 12px;font-size:14px}.dpr-schema-label{font-size:10px;color:#89969b;text-transform:uppercase;letter-spacing:.5px;margin:9px 0 5px}.dpr-region-row,.dpr-component-list{display:flex;gap:5px;flex-wrap:wrap}.dpr-code{font:9.5px 'SF Mono',Menlo,monospace;background:#f2f5f6;color:#52666d;padding:3px 5px;border-radius:4px}.dpr-schema-card .dpr-card-foot{margin-top:auto;padding-top:13px}
@media(max-width:1180px){.dpr-metrics{grid-template-columns:repeat(2,1fr)}.dpr-role-grid{grid-template-columns:repeat(2,1fr)}.dpr-schema-grid{grid-template-columns:1fr}}
@media(max-width:780px){.dpr-intro{align-items:flex-start;flex-direction:column}.dpr-metrics,.dpr-role-grid,.dpr-run-grid{grid-template-columns:1fr}}
"""
