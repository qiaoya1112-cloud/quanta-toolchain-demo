# S004 User Manual Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a new S004 Feishu user-manual copy that preserves S003 structure while aligning confirmed content with production.

**Architecture:** Use `lark-cli docs` under the user identity to read the S003 source, create a separate personal-library document, and update only its copy. Production UI labels are the source of truth; S004-only or unverified functions are recorded as pending instead of represented as live operations.

**Tech Stack:** Feishu `lark-cli` Docs v2 API, in-app browser, Markdown verification notes.

## Global Constraints

- Never modify S003 document `WLKJdA2mzooUuDxgtxVcYxAInOc`.
- Create `机器学习平台用户手册_S004版` in `my_library`.
- Use `--as user` and `--api-version v2` for every Docs API call.
- Production UI supersedes S004 requirements; S004 supersedes S003 only when production evidence is absent and the item is explicitly marked pending.
- Use only user-facing Chinese in the final manual; exclude internal `[增]` / `[改]` / `[删]` labels.

---

### Task 1: Capture source structure and confirmed production evidence

**Files:**
- Read: S003 document `WLKJdA2mzooUuDxgtxVcYxAInOc`
- Read: S004 requirement document `UwTddHFzooK0AFxW3ugce1YdnOr`
- Read: production URL `https://quanta.i.spirit-ai.com/data-preparation/data-query`

**Interfaces:**
- Consumes: source document IDs and active authenticated browser tab.
- Produces: a scoped evidence set for the new manual.

- [ ] **Step 1: Fetch the S003 outline and data-query section.**

Run:
```powershell
lark-cli docs +fetch --api-version v2 --as user --doc WLKJdA2mzooUuDxgtxVcYxAInOc --scope outline --max-depth 4 --detail with-ids
lark-cli docs +fetch --api-version v2 --as user --doc WLKJdA2mzooUuDxgtxVcYxAInOc --scope section --start-block-id doxcnqc1RNyWy6vbUAlzqFjZLQc --detail with-ids
```

- [ ] **Step 2: Fetch the S004 internal requirements section.**

Run:
```powershell
lark-cli docs +fetch --api-version v2 --as user --doc UwTddHFzooK0AFxW3ugce1YdnOr --scope section --start-block-id QXsBdXcDLo9n28xN23scsoyinqf --detail simple
```

- [ ] **Step 3: Record the production data-query labels.**

Verify the current UI contains the two tabs, 14 fixed-filter labels, four actions, and nine result fields captured in the approved design.

- [ ] **Step 4: Mark Task 1 complete only if the S003 source has not been written to.**

### Task 2: Create an independent S004 manual copy

**Files:**
- Create: Feishu Doc `机器学习平台用户手册_S004版`

**Interfaces:**
- Consumes: verified source structure from Task 1.
- Produces: a writable S004 document URL and token.

- [ ] **Step 1: Create a skeleton document in the personal library.**

Run:
```powershell
lark-cli docs +create --api-version v2 --as user --parent-position my_library --content '<title>机器学习平台用户手册_S004版</title><callout emoji="ℹ️" background-color="light-blue" border-color="blue"><p>本手册依据当前机器学习平台已上线页面整理。</p></callout><h2>快速入门</h2><h2>功能详情</h2><h3>功能总览</h3><h3>数据：数据查询</h3><h3>数据：数据集</h3><h3>训练：训练任务</h3><h3>部署：Checkpoint</h3><h3>配置</h3><h3>数据可视化</h3><h2>附录</h2><h3>待确认项</h3>'
```

- [ ] **Step 2: Fetch the new document with IDs and retain its URL.**

Run:
```powershell
lark-cli docs +fetch --api-version v2 --as user --doc '<new-doc-url>' --detail with-ids
```

- [ ] **Step 3: Verify the new document title and confirm it has a distinct document ID from S003.**

### Task 3: Populate confirmed operational content

**Files:**
- Modify: the S004 Feishu document from Task 2

**Interfaces:**
- Consumes: Task 1 production evidence and Task 2 heading block IDs.
- Produces: user-facing instructions without unverified features.

- [ ] **Step 1: Replace the data-query section with confirmed content.**

Insert after the `数据：数据查询` heading:
```xml
<p><b>使用入口：</b>数据 → 数据查询。</p>
<p><b>功能说明：</b>通过固定筛选或执行 SQL 查询采集记录，并可根据查询结果创建数据集。</p>
<h4>固定筛选</h4>
<table><thead><tr><th background-color="light-gray">分类</th><th background-color="light-gray">筛选项</th></tr></thead><tbody><tr><td>任务信息</td><td>采集任务、批次编号、设备序列号、采集时间、操作员、采集类型、Dagger 类型</td></tr><tr><td>处理信息</td><td>采集结论、是否质检、质检结论、是否标注、标注版本</td></tr><tr><td>导出要求</td><td>Episode 上限、Prompt 语言</td></tr></tbody></table>
<ol><li seq="auto">填写需要的筛选项；多个任务、批次或设备序列号使用英文逗号分隔。</li><li seq="auto">点击“查询”查看结果；如需重新设置条件，点击“重置”。</li><li seq="auto">核对 recording_id、Task ID、设备、类型、是否质检、是否标注、帧数和时长。</li><li seq="auto">确认结果后点击“用结果建数据集”；可通过“查看数据集创建进度”跟踪创建状态。</li></ol>
<callout emoji="❗" background-color="light-yellow" border-color="yellow"><p>执行 SQL 仅适用于已明确查询字段、语句范围和权限的场景。</p></callout>
```

- [ ] **Step 2: Populate the overview with only visible navigation.**

State the confirmed menu paths: 数据（数据查询、数据集）、训练（训练任务）、部署（Checkpoint）、配置、数据可视化（数据可视化）.

- [ ] **Step 3: Neutralize unverified training and Checkpoint claims.**

Do not instruct users to use `缓存`、`TEST`、`DAGGER`、`血缘`、training-code configuration, or advanced configuration. Instead, state that detailed actions depend on the controls available to the current account and are listed under pending verification when not visible.

- [ ] **Step 4: Add a pending-items appendix.**

List training-branch search, dataset-tag changes, prompt-ordering changes, checkpoint merge/download, and test/DAgger workflow as requirement-side changes not yet confirmed in the production pages inspected in this task.

### Task 4: Verify, finalize, and report

**Files:**
- Read: completed S004 Feishu document
- Modify: task checklist in this plan

**Interfaces:**
- Consumes: completed S004 document URL.
- Produces: final manual link and alignment report.

- [ ] **Step 1: Fetch the completed document.**

Run:
```powershell
lark-cli docs +fetch --api-version v2 --as user --doc '<new-doc-url>' --detail simple
```

- [ ] **Step 2: Verify required wording.**

Confirm the completed copy includes `固定筛选`、`执行 SQL`、`查看数据集创建进度`、`用结果建数据集`, and excludes live-operation instructions for unverified `缓存`, `TEST`, `DAGGER`, and `血缘`.

- [ ] **Step 3: Confirm the S003 document revision remains unchanged.**

Run:
```powershell
lark-cli docs +fetch --api-version v2 --as user --doc WLKJdA2mzooUuDxgtxVcYxAInOc --scope outline --max-depth 1
```

- [ ] **Step 4: Deliver the new link, a module change summary, alignment explanation, and pending-items list.**
