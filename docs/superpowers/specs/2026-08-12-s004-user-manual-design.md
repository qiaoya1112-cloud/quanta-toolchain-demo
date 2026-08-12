# S004 User Manual Update Design

## Goal

Create a new Feishu document named `机器学习平台用户手册_S004版` in the user's personal knowledge base. Preserve the S003 manual's structure, writing style, existing media, and original S003 document. Update only the content that can be reconciled with the current production machine-learning platform and the S004 internal requirements.

## Source Priority

1. Production UI currently accessible at `https://quanta.i.spirit-ai.com/data-preparation/data-query`.
2. S004 requirement document, section `四、需求详情 > 内部版`.
3. S003 user manual.

## Confirmed Production Scope

The visible production navigation exposes:

- 数据: 数据查询、数据集
- 训练: 训练任务
- 部署: Checkpoint
- 配置
- 数据可视化: 数据可视化

The production 数据查询 page exposes:

- Tabs: 固定筛选、执行 SQL
- Fixed filters: 采集任务、批次编号、设备序列号、采集时间、操作员、采集类型、Dagger 类型、采集结论、是否质检、质检结论、是否标注、标注版本、Episode 上限、Prompt 语言
- Actions: 重置、查询、查看数据集创建进度、用结果建数据集
- Result fields: recording_id、Task ID、设备、类型、是否质检、是否标注、帧数、时长、操作

## Update Strategy

### Keep

- The S003 document's high-level structure: 快速入门、功能详情、附录.
- Existing screenshots, videos, document metadata, and sections whose production behavior has not been revalidated.
- The data-query section where its labels match the production UI.

### Rewrite

- Data query wording to use the exact current labels above, including `查看数据集创建进度` and `用结果建数据集`.
- Training-task and Checkpoint wording that presents S003-only `缓存` terminology or `TEST` / `DAGGER` / `血缘` actions as current production behavior. These statements will be replaced by neutral, verified navigation and observation instructions unless their corresponding production pages can be confirmed.
- Any S003 content that describes user-configurable training code, advanced configuration, or other S004-removed options as generally available.

### Add only when confirmed

- Dataset tags, prompt ordering, training-branch selection, or checkpoint merge/download wording only when the production UI shows the relevant page and control.
- If a feature exists only in the S004 requirement, keep it out of the operational manual and list it in a `待确认项` section instead.

## Manual Content Pattern

Each updated module follows the existing manual's concise pattern:

1. 功能说明
2. 使用入口
3. 操作步骤
4. 注意事项

Terminology is user-facing Chinese; internal labels such as `[增]`, `[改]`, `[删]`, `S004`, and implementation details are excluded from the final manual.

## Validation

- Fetch the created document and compare the headings and updated paragraphs with the source draft.
- Confirm the source S003 document ID remains unchanged.
- Verify every stated button, tab, and result field against the production UI evidence collected above.
- Include a final change summary and a separate list of unverified S004 items.

## Expected Deliverables

- Link to the new S004 manual.
- Module-by-module change summary.
- Alignment statement describing which changes come from S004 and which were calibrated to production.
- Explicit `待确认项` list for requirements unavailable or unverified in production.
