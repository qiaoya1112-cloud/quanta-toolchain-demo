# Quanta · 开发者工具链 Demo

面向具身智能算法 / 数据 / 标注开发者的工具链 Demo，门户 + 多平台架构：

- **数据平台** — 项目 → 任务管理 → Pipeline → 人工任务 / 数据处理 → 数据集版本
- **模型平台** — 数据 → 训练 → 部署 → 评测
- **应用编排平台** — 模型服务 · 编排 · 资产
- **设备管理平台** — 设备 · 监测 · OTA

S026 指令采集交互演示拆分为 `/data/instruction-management`（指令管理）、`/data/instruction-packages`（指令包管理）和 `/data/collection-plans`（采集方案）三个并列侧栏入口；采集方案从独立指令包管理中导入指令包，并通过独立页面配置采集策略与供应商。上传与审批使用独立子页面，审批详情支持筛选、分页和逐条审批。采集方案中的“端侧采集”按钮会进入 `/data/edge-collection` 手机 App 模拟页。演示数据均为虚构的浏览器本地 Mock，不连接生产接口。

`/data/post-training-collection` 是独立的数据采集交互实现：UDAS 与机器人采集分开，机器人任务细分 NORMAL 和 DAGGER；提供任务列表、新建/复制/编辑、详情、任务卡、结束/重新开放及采集数据示例。创建入口跟随 UDAS/机器人列表 Tab，表单内不重复选择来源；复制、编辑和草稿沿用对应类型。任务配置存在本机 `instance/post-training-collection.sqlite3`，与原 S026 采集方案流程分离；列表和录制数据为虚构演示，不连接采集设备、生产上传或后处理服务。详细业务限制与实现验证见项目根目录 `02-evidence/2026-10-23/collection-fixes/`。

任务卡使用稳定的任务详情链接，每次打开及复制时读取最新任务；`GET /api/post-training-collection/tasks/<id>/collection-check` 返回 `can_start`、原因和任务当前内容，不缓存、不写入录制。仅已关闭任务返回 `can_start=false`；历史链接中的版本参数忽略，不再执行版本过期拦截。成功结果是核对时的状态，不是设备录制许可，当前 Demo 未接真实设备。

2026-10-25用户确认一期不做任务配置V1/V2管理：页面/API不展示任务或录制的配置版本，不生成新版本及配置历史；历史存储原样保留但不再推进。编辑保存比较规范化后的字段，有变化则写入日志（修改人、时间、字段及修改前后内容）；内容相同返回 `unchanged=true`，不改日志、更新时间或内部并发修订号。过期修订号仍返回409，避免覆盖其他人的修改。飞书正文不检测，不能通过平台日志还原文档历史；Prompt资产自身版本仍保留，不属于本次下线范围。

本轮新版预览使用 `http://127.0.0.1:5046/data/post-training-collection`，旧5041后端未重启。日志专项入口：`tests/collection_logs_browser.cjs`。

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

本地需要更多数据采集演示数据时，可在仓库目录运行 `python -m flask --app toolchain_demo seed-collection-demo`。
该命令一次性追加采集任务、录制和 5 个关联处理样例（待处理、处理中、已完成），重复执行不重复添加。02602 关联 3 个处理任务；02601、02607 共用另外 2 个质检与标注任务，部分数据关联多个任务。采集任务列表优先展示有关联的任务。旧版多余且未修改的处理样例会自动精简，手动创建及已修改的数据保留。可通过 `COLLECTION_DEMO_DB` 指定本地数据库，`instance/` 运行数据不提交到仓库。

关联处理任务复用原处理模块的配置详情与 `/data/tasks/<id>` 数据列表，不另设详情页。`/data/processing-tasks?linked=<id>` 打开原只读配置详情；来源采集任务支持返回链接。数据列表仅显示实际纳入成员，支持数据 ID 查询和分页；未接收的质检结果显示“-”，每条录制可回到采集数据查看。

| 变量 | 默认 | 说明 |
|------|------|------|
| `PORT` | 5004 | 监听端口（Render 会自动注入） |
| `DP_DIR` | 脚本所在目录 | data_platform.py 所在目录 |
| `EP_DIR` | 脚本所在目录 | quanta_eval_platform.py 所在目录 |
