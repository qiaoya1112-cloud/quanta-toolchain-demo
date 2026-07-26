# Quanta · 开发者工具链 Demo

面向具身智能算法 / 数据 / 标注开发者的工具链 Demo，门户 + 多平台架构：

- **数据平台** — 项目 → 任务管理 → Pipeline → 人工任务 / 数据处理 → 数据集版本
- **模型平台** — 数据 → 训练 → 部署 → 评测
- **应用编排平台** — 模型服务 · 编排 · 资产
- **设备管理平台** — 设备 · 监测 · OTA

Flask 门户集成 `data_platform.py` / `quanta_eval_platform.py` 作为模型平台数据 / 评测子模块。

数据平台重构由 `data_platform_refactor.py` 统一维护页面注册、导航、领域对象、节点类型、算子、工作台 Schema 和演示事实，`toolchain_demo.py` 只负责共享门户与路由承载。核心入口包括：

- `/data`：按角色组织的工作台总览
- `/data/tasks`：按数据采集、数据导入、数据处理三个 Tab 管理任务
- `/data/task-pool`：领取和处理人工任务
- `/data/pipeline-definitions`、`/data/pipeline-runs`：流程配置、版本、Run 与 Node Run
- `/data/assets`、`/data/dataset-versions`、`/data/lineage`：数据版本与血缘
- `/data/capabilities`、`/data/workbench-schemas`：配置中心
- `/data/operations`：交付进度、周期、产能和资源指标

产品边界、对象建模、分层架构与技术约束只保留在
`Quanta-数据平台产品架构调整方案-完善版.md` 等设计文档中，不作为产品页面或导航入口。

## 本地运行

```bash
pip install -r requirements.txt
python toolchain_demo.py
# http://localhost:5004
```

## 验证

```bash
PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m py_compile \
  toolchain_demo.py data_platform_refactor.py data_platform.py
PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m unittest discover -s tests -v
```

`data_platform_refactor.validate_architecture()` 会校验导航与页面注册一致性、三类节点、已发布配置冻结、Run 的版本与快照绑定、Human Task 完整关联，以及数据集版本的快照与发布条件。

## 部署 (Render)

仓库根目录已包含 `render.yaml` 蓝图。在 Render Dashboard → New + → Blueprint → 选择本仓库即可自动创建 Web Service。

启动命令：

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 toolchain_demo:app
```

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `PORT` | 5004 | 监听端口（Render 会自动注入） |
| `DP_DIR` | 脚本所在目录 | data_platform.py 所在目录 |
| `EP_DIR` | 脚本所在目录 | quanta_eval_platform.py 所在目录 |
