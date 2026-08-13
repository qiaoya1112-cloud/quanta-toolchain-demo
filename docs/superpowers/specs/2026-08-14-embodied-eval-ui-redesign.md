# Embodied Evaluation UI Redesign

**Date:** 2026-08-14

**Status:** Approved design pending written-spec review

**Target:** Flask inline HTML templates with the existing Ant Design v4 visual language

## 1. Objective

Redesign the existing `/model/embodied-eval/*` prototype so it uses the same mature page structure, information density, spacing, status language, and interaction patterns as the training and data modules.

The redesign must stay inside the current Flask and Jinja-style inline HTML architecture. It must not migrate the embodied evaluation pages to React or introduce a new component library.

The product requirements in `docs/eval-module-prd-hmi-quanta.md` are the primary source for page structure, fields, lifecycle states, and traceability requirements.

## 2. Scope

### 2.1 Included

- Prompt library list and inline creation experience
- Metric template list, create, and edit experiences
- Evaluation set list, create, and edit experiences
- Evaluation task list, create, and detail experiences
- Segment record list and detail experiences
- A redirect from `/model/embodied-eval/` to `/model/embodied-eval/tasks`
- Shared embodied-evaluation page header, filter, summary, table, status, detail, and pagination patterns
- Realistic mock data that covers the important lifecycle and error states
- Regression checks for training, data, and the existing general evaluation module

### 2.2 Excluded

- A new embodied evaluation overview dashboard
- Merging the general evaluation module with embodied evaluation
- React, Vue, or another frontend framework migration
- A database, persistence layer, authentication, or production backend services
- A real HMI implementation
- A real deployment engine, data-lake upload pipeline, replay engine, or DAgger integration
- A new analysis module or report-generation module

## 3. Information Architecture

The existing five navigation destinations remain separate:

1. Prompt Library
2. Metric Templates
3. Evaluation Sets
4. Evaluation Tasks
5. Evaluation Records

The underlying business relationship is:

```text
Prompt Library + Metric Templates
                |
                v
          Evaluation Set
                |
                v
          Evaluation Task
                |
                v
        Segment Evaluation Records
```

`/model/embodied-eval/` redirects to Evaluation Tasks because the task list is the operational entry point. No overview page is added.

The general evaluation navigation and routes remain unchanged.

## 4. Shared Page Structure

Every embodied evaluation list page uses the same hierarchy:

1. Compact page heading and one-sentence purpose
2. Field-labeled filter panel
3. Result summary and primary action row
4. Main table or business-specific content
5. Pagination

The redesign reuses existing project patterns wherever possible:

- `.fb-labeled` for structured filters
- `.list-summarybar` for counts and the primary action
- `.table-wrap` and `.ant-table` for lists
- `.qa` and `.tag` for statuses
- `.det-tabs` for detail tabs
- `.bi-*` patterns for detail information
- `.mini-pager` for pagination
- Existing drawer, modal, form, and action-link patterns

Embodied-evaluation-specific CSS must use a dedicated prefix where a shared component is insufficient. It must not override unrelated training, data, or general evaluation pages.

## 5. Page Designs

### 5.1 Prompt Library

**Purpose:** Manage reusable evaluation instructions.

**Filters:**

- Prompt keyword
- Scene
- Task type
- Tag
- Creator

**Table columns:**

- Prompt ID
- Scene
- Task name
- Prompt text
- Tags
- Referencing evaluation set count
- Creator
- Updated time
- Actions

**Primary actions:**

- Import prompts
- Create prompt

**Interactions:**

- Preserve inline creation
- Preserve copy and delete actions
- Prevent more than one inline creation row
- Show that evaluation tasks use a prompt snapshot
- Do not implement prompt-version write-back because the PRD marks this behavior as unresolved

### 5.2 Metric Templates

**Purpose:** Define reusable dynamic result fields collected for each Segment.

The current sparse card grid is replaced with a table so the page matches the density and scanning behavior of other management lists.

**Filters:**

- Template name
- Field type
- Creator

**Table columns:**

- Template name
- Field count
- Field summary
- Referencing evaluation set count
- Creator
- Updated time
- Actions

**Supported field types:**

- Integer
- Float
- Percentage
- Boolean
- Enumeration

**Create and edit sections:**

1. Basic information
2. Metric field configuration
3. Reference information

Enumeration options may be added dynamically. Multi-select enumeration is excluded because the PRD leaves it unresolved.

### 5.3 Evaluation Sets

**Purpose:** Assemble prompts, metrics, and task defaults into a reusable evaluation specification.

**Filters:**

- Evaluation set name
- Scene
- Benchmark flag
- Version
- Creator

**Table columns:**

- Evaluation set name
- Version
- Type: standard or Benchmark
- Covered scenes
- Prompt count
- Metric count
- Referencing task count
- Creator
- Updated time
- Actions

**Create and edit sections:**

1. Basic information
2. Prompt composition
3. Metric configuration
4. Task preset configuration
5. Save confirmation

The existing single-page form remains. Clear section headings and an in-page section index replace a multi-step wizard.

The page must expose the PRD concepts of version, Benchmark flag, Prompt collection, Metric definitions, `task_config`, and configuration reuse.

### 5.4 Evaluation Tasks

**Purpose:** Represent one concrete embodied evaluation execution plan and act as the default embodied evaluation entry point.

**Filters:**

- Task name
- Evaluation set
- Policy or model
- Status
- Creator

**Summary:**

- Running count
- Pending count
- Completed count
- Exceptional count

**Table columns:**

- Task name
- Evaluation set and version
- Policies under test
- Execution progress
- Segment success rate
- HMI or device
- Status
- Creator
- Updated time
- Actions

**Create sections:**

1. Basic information
2. Evaluation set or Benchmark selection
3. Policy, checkpoint, and code branch configuration
4. Repeat count and timeout configuration
5. Test-machine selection
6. Config JSON
7. Creation confirmation

**Detail tabs:**

1. Task summary
2. Evaluation configuration
3. Deployment and HMI status
4. Execution progress
5. Policy comparison
6. Segment records
7. Operation log

Emergency stop, reset, and manual robot movement belong to the HMI. The platform prototype displays their status or history but does not present them as platform-side controls.

### 5.5 Evaluation Records

**Purpose:** Search and inspect Segment-level evaluation results and process data.

**Filters:**

- Evaluation task
- Evaluation set
- Prompt
- Policy and version
- Scene
- Execution status
- BadCase flag
- Creation time

**Table columns:**

- Segment ID
- Prompt
- Evaluation task
- Evaluation set version
- Policy
- Repeat index
- Duration
- Metric summary
- Data completeness
- Status
- BadCase flag
- Actions

**Detail tabs or sections:**

1. Basic information
2. Metric results
3. Failure attribution
4. Process data
5. Files and upload status

Process data includes third-party video, Robot State, MozTrace, optional sensor data, and their individual upload or data-lake states.

The prototype preserves the ability to mark a Segment as a BadCase. DAgger return remains a clearly labeled planned capability because its data flow is unresolved in the PRD.

## 6. Lifecycle and Status Language

### 6.1 Evaluation task lifecycle

```text
Pending -> Deploying -> Running -> Uploading -> Processing -> Completed
                                      |             |
                                      +-------> Partially failed

Any active stage may also end as Failed or Terminated.
```

List pages show a compact status tag. Task details show the lifecycle as a progress sequence.

### 6.2 Segment lifecycle

- Pending
- Running
- Uploading
- Processed
- Failed
- Timed out

### 6.3 Process-data state

Each video, Robot State, MozTrace, and Metric JSON artifact can be:

- Not generated
- Pending upload
- Uploading
- Stored in the data lake
- Upload failed

These states reflect the PRD's platform-to-HMI task handoff, execution, upload, and asynchronous processing flow.

## 7. Mock Data Requirements

Mock data must create a credible operational page rather than a placeholder layout.

Minimum coverage:

- 15 or more prompts
- 4 to 6 Metric templates
- 6 to 10 evaluation sets
- 10 to 12 evaluation tasks
- 20 or more Segment records

Evaluation task examples must include:

- A multi-Policy comparison task
- A Benchmark regression task
- A single-model standard task
- Deploying, running, uploading, completed, partially failed, and failed states

Segment examples must include:

- Successful execution
- Timeout
- Metric failure
- BadCase
- Incomplete upload
- Multiple policies
- Multiple repeat indices

All sample names and values must use credible embodied-robotics evaluation language.

## 8. Unresolved PRD Capabilities

The following items may have a visible planned entry, but the prototype must not imply that the backend workflow is complete:

- Prompt field-edit write-back and evaluation-set version creation
- Automatic BadCase return to DAgger
- Synchronized trajectory and video replay
- Offline evaluation
- Final failure taxonomy
- Config JSON schema validation and merge-conflict rules
- Checkpoint deployment rollback
- Production task-delivery and status-synchronization protocol

Planned entries use an explicit `Planned` or `Rule pending` label.

## 9. Interaction and Error Handling

- Existing search, filter, create, edit, delete, start, export, detail navigation, and BadCase marking interactions remain available.
- Destructive actions require confirmation.
- User-facing state changes should use the existing toast or inline feedback patterns instead of relying on `window.alert()` for primary flows.
- Empty results provide a composed explanation and a relevant next action.
- Invalid create forms show inline required-field feedback where practical for the prototype.
- Long identifiers, prompt text, model lists, and paths must not break table layout.

## 10. Accessibility and Responsive Constraints

- Preserve visible keyboard focus for interactive controls.
- Use semantic buttons for actions where practical.
- Do not communicate status with color alone; every status includes text.
- Keep action targets at least as large as the project's existing button and action-link standards.
- At common desktop widths, tables must not be incorrectly clipped.
- Narrow layouts may use horizontal table scrolling, but the page body itself must not develop uncontrolled horizontal overflow.

## 11. Verification and Acceptance Criteria

The redesign is accepted when:

1. `/model/embodied-eval/` redirects to `/model/embodied-eval/tasks`.
2. All five list pages share the heading, purpose, filters, summary, primary action, table, and pagination hierarchy.
3. Information density is comparable to the training-task list without becoming visually crowded.
4. Create and detail pages reuse the project's established form, tab, information-card, and status styles.
5. Evaluation set, task, and Segment relationships are traceable through visible fields and links.
6. Policy, checkpoint, code branch, execution parameters, and test-machine concepts appear where required by the PRD.
7. Segment details expose Metric results, failure attribution, and process-data states.
8. Training, data, and general evaluation pages retain their existing behavior and layout.
9. Common desktop widths do not incorrectly clip the redesigned tables.
10. Automated tests cover the root redirect, major list pages, and key details.
11. Browser verification covers the five list pages, one create flow, one task detail, and one Segment detail.
12. Browser console inspection reports no new errors introduced by the redesign.

## 12. Implementation Boundaries

- Primary implementation stays in `toolchain_demo.py` to match the repository's single-file prototype architecture.
- New shared CSS is narrowly scoped and added to the existing inline style system.
- Existing mock data structures may be extended with presentation and lifecycle fields, but their core relationships remain compatible with current routes and actions.
- Existing user changes outside the embodied evaluation scope must be preserved.
- The implementation must remain deployable through the current Flask and Render setup without new runtime dependencies.
