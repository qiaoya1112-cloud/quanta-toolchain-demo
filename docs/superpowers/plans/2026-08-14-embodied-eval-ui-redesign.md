# Embodied Evaluation UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the existing embodied evaluation Flask pages so they match the training and data modules' information density and Ant Design v4 visual language while preserving the current data model and interactions.

**Architecture:** Keep the implementation in `toolchain_demo.py`, add narrowly prefixed shared presentation helpers and CSS, enrich the existing in-memory mock records, and refactor the five list surfaces plus key create/detail surfaces. Use Flask test-client assertions for route structure and browser verification for visual and interaction acceptance.

**Tech Stack:** Python 3.11+, Flask 3.0+, inline HTML/CSS, vanilla JavaScript, Ant Design v4 stylesheet

## Global Constraints

- Do not add React, Vue, or a new runtime dependency.
- Do not add a new embodied evaluation overview dashboard.
- `/model/embodied-eval/` redirects to `/model/embodied-eval/tasks`.
- Do not merge or modify the general evaluation module.
- Keep all production behavior mock-only and in memory.
- Scope new CSS with `ee-` classes unless an existing shared class is reused unchanged.
- Preserve all unrelated working-tree changes.

---

### Task 1: Route Contract and Shared Page Primitives

**Files:**
- Modify: `toolchain_demo.py`
- Create: `tests/test_embodied_eval_redesign.py`

**Interfaces:**
- Produces: `embodied_eval_root()` redirect route
- Produces: `embodied_page_intro(title: str, description: str, eyebrow: str = "具身评测") -> str`
- Produces: `embodied_pager(total: int, page_size: int = 10) -> str`

- [ ] **Step 1: Write failing route and structure tests**

```python
def test_embodied_eval_root_redirects_to_tasks(self):
    response = self.client.get('/model/embodied-eval/')
    self.assertEqual(response.status_code, 302)
    self.assertTrue(response.headers['Location'].endswith('/model/embodied-eval/tasks'))

def test_task_list_uses_redesigned_structure(self):
    response = self.client.get('/model/embodied-eval/tasks')
    self.assertIn(b'ee-page-head', response.data)
    self.assertIn(b'fb-labeled', response.data)
    self.assertIn(b'list-summarybar', response.data)
    self.assertIn(b'mini-pager', response.data)
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `python -m unittest tests.test_embodied_eval_redesign -v`

Expected: root route returns 404 and the current task page lacks the new structure markers.

- [ ] **Step 3: Add the redirect, shared helpers, and scoped CSS**

Add a compact page heading with purpose copy, a reusable visual pager, focus-visible states, progress cells, compact metadata, and responsive horizontal table handling. Reuse existing `.fb-labeled`, `.list-summarybar`, `.table-wrap`, `.ant-table`, `.qa`, `.tag`, `.det-tabs`, and `.bi-*` rules.

- [ ] **Step 4: Run the focused tests**

Run: `python -m unittest tests.test_embodied_eval_redesign -v`

Expected: both tests pass.

### Task 2: Realistic Mock Coverage and Presentation Helpers

**Files:**
- Modify: `toolchain_demo.py`
- Modify: `tests/test_embodied_eval_redesign.py`

**Interfaces:**
- Extends: `EMBODIED_PROMPTS`, `EMBODIED_METRIC_TEMPLATES`, `EMBODIED_EVAL_SETS`, `EMBODIED_EVAL_TASKS`, `EMBODIED_SEGMENTS`
- Produces: helpers for status labels, relation counts, progress, completeness, and compact field summaries

- [ ] **Step 1: Add failing coverage assertions**

```python
def test_mock_data_covers_operational_states(self):
    self.assertGreaterEqual(len(toolchain_demo.EMBODIED_PROMPTS), 15)
    self.assertGreaterEqual(len(toolchain_demo.EMBODIED_METRIC_TEMPLATES), 4)
    self.assertGreaterEqual(len(toolchain_demo.EMBODIED_EVAL_SETS), 6)
    self.assertGreaterEqual(len(toolchain_demo.EMBODIED_EVAL_TASKS), 10)
    self.assertGreaterEqual(len(toolchain_demo.EMBODIED_SEGMENTS), 20)
    states = {task['status'] for task in toolchain_demo.EMBODIED_EVAL_TASKS}
    self.assertTrue({'pending', 'deploying', 'running', 'uploading', 'completed', 'partial_failed', 'failed'} <= states)
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `python -m unittest tests.test_embodied_eval_redesign.EmbodiedEvalRedesignTest.test_mock_data_covers_operational_states -v`

- [ ] **Step 3: Add realistic records without changing core identifiers used by existing routes**

Use embodied-robotics scenarios, Policy/checkpoint/version data, HMI devices, lifecycle timestamps, Segment artifact states, Metric results, and BadCase examples. Keep the current `ep*`, `emt*`, `ees*`, `eet*`, and `eseg*` record shapes backward compatible.

- [ ] **Step 4: Run the coverage test**

Run: `python -m unittest tests.test_embodied_eval_redesign.EmbodiedEvalRedesignTest.test_mock_data_covers_operational_states -v`

### Task 3: Prompt and Metric Management Lists

**Files:**
- Modify: `toolchain_demo.py`
- Modify: `tests/test_embodied_eval_redesign.py`

**Interfaces:**
- Updates: `embodied_eval_prompts()`
- Updates: `embodied_eval_metrics()`
- Preserves: existing create, edit, copy, delete, and API routes

- [ ] **Step 1: Add failing list-contract tests**

```python
def test_prompt_list_exposes_traceability_fields(self):
    body = self.client.get('/model/embodied-eval/prompts').get_data(as_text=True)
    for text in ('Prompt ID', '引用评测集', '更新时间', 'Prompt 快照'):
        self.assertIn(text, body)

def test_metric_list_is_a_dense_table(self):
    body = self.client.get('/model/embodied-eval/metrics').get_data(as_text=True)
    for text in ('字段数量', '字段摘要', '引用评测集', '创建人'):
        self.assertIn(text, body)
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_embodied_eval_redesign -v`

- [ ] **Step 3: Refactor both lists**

Use labeled filters, result summaries, primary action rows, dense tables, traceability links, realistic empty results, pagination, and existing teal action styles. Replace the Metric card grid with a table. Keep inline Prompt creation and enforce one edit row.

- [ ] **Step 4: Run focused tests**

Run: `python -m unittest tests.test_embodied_eval_redesign -v`

### Task 4: Evaluation Set and Task Lists

**Files:**
- Modify: `toolchain_demo.py`
- Modify: `tests/test_embodied_eval_redesign.py`

**Interfaces:**
- Updates: `embodied_eval_sets()`
- Updates: `embodied_eval_tasks()`
- Preserves: existing create, edit, start, delete, and detail routes

- [ ] **Step 1: Add failing PRD-field tests**

```python
def test_eval_set_list_exposes_prd_fields(self):
    body = self.client.get('/model/embodied-eval/sets').get_data(as_text=True)
    for text in ('版本', 'Benchmark', '覆盖场景', 'Prompt 数量', 'Metric 数量', '引用任务'):
        self.assertIn(text, body)

def test_task_list_exposes_execution_fields(self):
    body = self.client.get('/model/embodied-eval/tasks').get_data(as_text=True)
    for text in ('执行进度', 'Segment 成功率', 'HMI / 设备', 'Policy'):
        self.assertIn(text, body)
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_embodied_eval_redesign -v`

- [ ] **Step 3: Implement the redesigned lists**

Add PRD-driven filters, relation counts, Benchmark and version tags, task lifecycle states, progress, success rate, devices, creators, timestamps, and pagination. Remove redundant card wrappers and keep tables horizontally usable.

- [ ] **Step 4: Run focused tests**

Run: `python -m unittest tests.test_embodied_eval_redesign -v`

### Task 5: Task and Segment Traceability Details

**Files:**
- Modify: `toolchain_demo.py`
- Modify: `tests/test_embodied_eval_redesign.py`

**Interfaces:**
- Updates: `embodied_eval_task_detail(task_id)`
- Updates: `embodied_eval_segments()`
- Updates: `embodied_eval_segment_detail(segment_id)`

- [ ] **Step 1: Add failing detail-contract tests**

```python
def test_task_detail_shows_platform_hmi_boundary(self):
    body = self.client.get('/model/embodied-eval/tasks/eet001').get_data(as_text=True)
    for text in ('部署与 HMI', '执行进度', 'Policy 对比', 'Segment 记录'):
        self.assertIn(text, body)

def test_segment_detail_shows_process_artifacts(self):
    body = self.client.get('/model/embodied-eval/segments/eseg001').get_data(as_text=True)
    for text in ('Metric 结果', '失败归因', 'Robot State', 'MozTrace', '数据入湖'):
        self.assertIn(text, body)
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_embodied_eval_redesign -v`

- [ ] **Step 3: Refactor task detail, record list, and Segment detail**

Use detail tabs and shared information blocks. Show task lifecycle, Policy/checkpoint/branch, HMI status, Segment progress, artifact upload states, Metrics, failure attribution, and clearly labeled planned capabilities. Platform pages display emergency-operation history but do not expose HMI emergency controls.

- [ ] **Step 4: Run focused tests**

Run: `python -m unittest tests.test_embodied_eval_redesign -v`

### Task 6: Full Regression and Browser Acceptance

**Files:**
- Modify: `tests/test_embodied_eval_redesign.py` only if a regression assertion needs correction

**Interfaces:**
- Consumes: all redesigned routes and shared helpers
- Produces: verified Flask prototype with no new runtime dependencies

### Task 7: Align List Chrome with Training and Deployment

**Files:**
- Modify: `toolchain_demo.py`
- Modify: `tests/test_embodied_eval_redesign.py`

**Interfaces:**
- Updates: the five embodied-evaluation list routes only
- Preserves: create and detail headings, table fields, mock data, and interactions

- [x] **Step 1: Update list-contract tests to reject standalone headings and require `.fb-labeled > .ff` fields.**
- [x] **Step 2: Run the focused test and confirm it fails because list pages still render `.ee-page-head` and `.fb-field`.**
- [x] **Step 3: Remove list headings, use the existing training/deployment filter DOM, order reset before query, and move primary actions to `.list-summarybar`.**
- [x] **Step 4: Run focused and full regression tests.**
- [x] **Step 5: Render all five lists at 1440 × 1000 and compare spacing and controls with the training and deployment lists.**

- [ ] **Step 1: Run automated verification**

```powershell
python -m unittest discover -s tests -v
python -m py_compile toolchain_demo.py
git diff --check
```

- [ ] **Step 2: Run route smoke checks**

Verify 200 responses for training, data, general evaluation, all five embodied evaluation lists, one create page, one task detail, and one Segment detail. Verify the embodied root returns a redirect.

- [ ] **Step 3: Run browser acceptance**

Inspect the five list pages, task creation, task detail, and Segment detail at the default desktop viewport. Check table clipping, active navigation, filters, primary actions, tabs, empty states, focus states, and console errors. Compare the task list against the existing training task page.

- [ ] **Step 4: Commit only scoped files**

```powershell
git add toolchain_demo.py tests/test_embodied_eval_redesign.py docs/superpowers/plans/2026-08-14-embodied-eval-ui-redesign.md
git commit -m "feat: redesign embodied evaluation UI"
```
