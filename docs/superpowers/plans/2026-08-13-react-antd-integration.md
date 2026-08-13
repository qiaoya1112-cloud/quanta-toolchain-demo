# React and Ant Design Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable Vite, React, and Ant Design workspace to the Flask repository and serve the first workflow showcase page at `/workflow` without changing existing Jinja pages.

**Architecture:** Flask remains the application host and continues serving all existing routes. Vite builds one isolated React page into `static/workflow/`; Flask serves its generated entry document at `/workflow`, while workflow content remains data-driven inside `frontend/src/content/workflow.js`.

**Tech Stack:** Python 3.11, Flask 3, Node.js 20, Vite, React, Ant Design, Vitest, React Testing Library

## Global Constraints

- Preserve every existing Flask and Jinja route and do not migrate existing pages.
- Use only Ant Design as the React component library; do not add Element Plus or shadcn/ui.
- Use `#149DAA` as the single primary accent through Ant Design theme tokens.
- Keep the page light, restrained, responsive, and suitable for independent internal reading.
- Leave the Quanta case-study section as an explicit empty placeholder.
- Do not add a database, authentication, CMS, React Router, or backend API.
- Keep all code comments and repository documentation in English.
- Preserve unrelated tracked and untracked user files.

---

## File Structure

- Create `frontend/package.json`: frontend scripts and dependency versions.
- Create `frontend/package-lock.json`: reproducible npm installation.
- Create `frontend/vite.config.js`: React plugin, Vitest setup, and Flask build destination.
- Create `frontend/index.html`: Vite entry document.
- Create `frontend/src/main.jsx`: React root and Ant Design theme provider.
- Create `frontend/src/App.jsx`: showcase page composition and selected-stage state.
- Create `frontend/src/content/workflow.js`: eight-stage workflow content model.
- Create `frontend/src/components/WorkflowOverview.jsx`: interactive stage strip.
- Create `frontend/src/components/StageDetail.jsx`: execution guide and navigation.
- Create `frontend/src/components/CasePlaceholder.jsx`: approved empty case-study state.
- Create `frontend/src/styles/app.css`: responsive editorial layout and Quanta tokens.
- Create `frontend/src/test/setup.js`: DOM matcher setup.
- Create `frontend/src/App.test.jsx`: user-facing interaction tests.
- Create `tests/test_workflow_route.py`: Flask route tests.
- Modify `toolchain_demo.py`: add `/workflow` route and missing-build fallback.
- Modify `.gitignore`: ignore frontend dependencies and generated Flask assets.
- Modify `render.yaml`: build React assets before Gunicorn starts.
- Modify `README.md`: document frontend development and integrated build commands.

### Task 1: Frontend Scaffold and Build Contract

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/package-lock.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/test/setup.js`
- Create: `frontend/src/App.test.jsx`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `npm run dev`, `npm run build`, and `npm test` commands.
- Produces: build output at `static/workflow/index.html` with assets rooted at `/static/workflow/`.
- Produces: root component `App` as the page composition boundary.

- [ ] **Step 1: Scaffold the Vite React package**

Run:

```powershell
npm create vite@latest frontend -- --template react
cd frontend
npm install antd @ant-design/icons
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

Expected: `frontend/package.json` and `frontend/package-lock.json` exist with React, Ant Design, Vite, and test dependencies.

- [ ] **Step 2: Write the failing smoke test**

Create `frontend/src/App.test.jsx`:

```jsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('introduces the workflow playbook', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /从需求输入，到可验证、可交付的产品方案/ })).toBeInTheDocument()
  })
})
```

Configure Vitest in `vite.config.js` with `environment: 'jsdom'` and `setupFiles: './src/test/setup.js'`.

- [ ] **Step 3: Run the test and verify the content contract fails**

Run: `npm test -- --run`

Expected: FAIL because the default Vite application does not contain the workflow heading.

- [ ] **Step 4: Add the minimal React entry and build configuration**

Set Vite's production `base` to `/static/workflow/` and `build.outDir` to `../static/workflow`. Replace the starter `App` with the required heading and configure `ConfigProvider` in `main.jsx` with `colorPrimary: '#149DAA'`.

- [ ] **Step 5: Run frontend tests and production build**

Run:

```powershell
npm test -- --run
npm run build
```

Expected: tests PASS; `static/workflow/index.html` exists and contains `/static/workflow/assets/` references.

- [ ] **Step 6: Ignore generated artifacts**

Add these entries to `.gitignore`:

```gitignore
frontend/node_modules/
static/workflow/
```

- [ ] **Step 7: Commit the scaffold**

```powershell
git add .gitignore frontend
git commit -m "build: add React prototype workspace"
```

### Task 2: Data-Driven Workflow Experience

**Files:**
- Create: `frontend/src/content/workflow.js`
- Create: `frontend/src/components/WorkflowOverview.jsx`
- Create: `frontend/src/components/StageDetail.jsx`
- Create: `frontend/src/components/CasePlaceholder.jsx`
- Create: `frontend/src/styles/app.css`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/App.test.jsx`

**Interfaces:**
- Produces: `workflowStages: WorkflowStage[]` containing exactly eight ordered stages.
- Consumes: `selectedStageId: string` and `onSelect(stageId: string)` in `WorkflowOverview`.
- Consumes: `stage`, `stageIndex`, `stageCount`, `onPrevious`, and `onNext` in `StageDetail`.

- [ ] **Step 1: Write failing interaction tests**

Extend `App.test.jsx` to verify:

```jsx
it('shows all eight workflow stages', () => {
  render(<App />)
  expect(screen.getAllByRole('button', { name: /阶段/ })).toHaveLength(8)
})

it('opens the selected stage guide', async () => {
  const user = userEvent.setup()
  render(<App />)
  await user.click(screen.getByRole('button', { name: /阶段 3：业务访谈/ }))
  expect(screen.getByRole('heading', { name: /业务访谈：校准真实业务流程/ })).toBeInTheDocument()
})

it('keeps the real case study empty', () => {
  render(<App />)
  expect(screen.getByText('真实案例待补充')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run tests and verify they fail**

Run: `npm test -- --run`

Expected: FAIL because the workflow stages and detail components do not exist.

- [ ] **Step 3: Implement the workflow content model**

Create eight records with these stage titles:

1. 需求输入
2. AI 辅助理解
3. 业务访谈
4. 需求对齐
5. 方案构思
6. 原型实现
7. 评审迭代
8. 文档沉淀

Each record must include every field defined in the approved design schema and use explicit empty strings for unavailable prompt templates.

- [ ] **Step 4: Implement the overview and stage details**

Use Ant Design `Button`, `Tag`, `Collapse`, `Progress`, `Typography`, and `message` components. Use custom semantic wrappers for the hero, workflow strip, human-versus-AI responsibility columns, and case-study placeholder.

- [ ] **Step 5: Implement restrained responsive styling**

Use one light theme, a maximum content width of `1200px`, an 8px spacing rhythm, modest radii no larger than `8px`, and break the eight-stage strip into a horizontally scrollable region below `960px`.

- [ ] **Step 6: Run tests and build**

Run:

```powershell
npm test -- --run
npm run build
```

Expected: all tests PASS and the production build completes.

- [ ] **Step 7: Commit the workflow experience**

```powershell
git add frontend/src
git commit -m "feat: add AI product workflow showcase"
```

### Task 3: Flask Route and Graceful Missing-Build State

**Files:**
- Create: `tests/test_workflow_route.py`
- Modify: `toolchain_demo.py`

**Interfaces:**
- Produces: `GET /workflow` returning the built React entry document.
- Produces: HTTP 503 with build instructions when `static/workflow/index.html` is absent.

- [ ] **Step 1: Write failing Flask route tests**

Create `tests/test_workflow_route.py`:

```python
import unittest
from unittest.mock import patch

import toolchain_demo


class WorkflowRouteTest(unittest.TestCase):
    def setUp(self):
        self.client = toolchain_demo.app.test_client()

    def test_workflow_serves_built_frontend(self):
        response = self.client.get('/workflow')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="root"', response.data)

    @patch('toolchain_demo.os.path.isfile', return_value=False)
    def test_workflow_explains_missing_build(self, _isfile):
        response = self.client.get('/workflow')
        self.assertEqual(response.status_code, 503)
        self.assertIn(b'npm run build', response.data)
```

- [ ] **Step 2: Run tests and verify the new route fails**

Run: `python -m unittest tests.test_workflow_route -v`

Expected: FAIL because `/workflow` is not registered.

- [ ] **Step 3: Implement the Flask route**

Use `send_from_directory` and resolve the entry path relative to `app.root_path`. Return an English fallback page with exact commands `cd frontend`, `npm install`, and `npm run build` and status 503 when the build output is absent.

- [ ] **Step 4: Run route tests and representative route checks**

Run:

```powershell
python -m unittest tests.test_workflow_route -v
@'
import toolchain_demo
client = toolchain_demo.app.test_client()
for path in ['/', '/data', '/model', '/workflow']:
    response = client.get(path)
    print(path, response.status_code)
'@ | python -
```

Expected: route tests PASS and all four paths return 200 after the frontend build.

- [ ] **Step 5: Commit the Flask integration**

```powershell
git add toolchain_demo.py tests/test_workflow_route.py
git commit -m "feat: serve React workflow from Flask"
```

### Task 4: Deployment and Developer Documentation

**Files:**
- Modify: `render.yaml`
- Modify: `README.md`

**Interfaces:**
- Produces: Render build command that installs Python dependencies, installs locked frontend dependencies, and builds React assets.
- Produces: documented local commands for Vite-only and Flask-integrated development.

- [ ] **Step 1: Verify the hosting environment supports the planned Node build**

Check Render's current official native runtime documentation. If a Python service cannot run Node during the build, preserve the existing Render command and document a separate static deployment for `frontend/` instead of assuming support.

- [ ] **Step 2: Update the deployment build command when supported**

Set:

```yaml
buildCommand: pip install -r requirements.txt && cd frontend && npm ci && npm run build
```

Keep the existing Gunicorn start command unchanged.

- [ ] **Step 3: Document developer commands**

Add README sections covering:

- `cd frontend && npm install && npm run dev`
- `cd frontend && npm run build`
- `python toolchain_demo.py`
- `/workflow` integration behavior
- Existing Jinja pages versus new React prototype pages

- [ ] **Step 4: Verify clean installation and build**

Run:

```powershell
cd frontend
npm ci
npm test -- --run
npm run build
cd ..
python -m unittest tests.test_workflow_route -v
```

Expected: every command succeeds.

- [ ] **Step 5: Commit deployment documentation**

```powershell
git add render.yaml README.md
git commit -m "docs: add React workflow build instructions"
```

### Task 5: Browser and Regression Verification

**Files:**
- Modify only files required to correct defects found by verification.

**Interfaces:**
- Validates all user-visible and regression requirements from the approved design.

- [ ] **Step 1: Start the integrated Flask application**

Run: `python toolchain_demo.py`

Expected: Flask listens on port 5004 without import or route errors.

- [ ] **Step 2: Inspect `/workflow` at desktop width**

Verify:

- The hero and eight-stage overview are readable without narration.
- Every stage can be selected.
- Previous and next controls select the correct stage.
- Required and customizable stages are visually distinguishable.
- The Quanta case-study placeholder contains no invented project content.
- Ant Design components inherit `#149DAA`.

- [ ] **Step 3: Inspect `/workflow` at mobile width**

Verify the stage strip scrolls, text does not overflow, buttons remain reachable, and detail sections collapse into one column.

- [ ] **Step 4: Check regression routes and browser console**

Open `/`, `/data`, and `/model`; verify their existing structure still renders. Confirm the `/workflow` console has no runtime errors.

- [ ] **Step 5: Run final automated verification**

Run:

```powershell
cd frontend
npm test -- --run
npm run build
cd ..
python -m unittest discover -s tests -v
git diff --check
```

Expected: all tests and build commands PASS and `git diff --check` reports no whitespace errors.

- [ ] **Step 6: Commit verification fixes if any**

```powershell
git add <verified-files>
git commit -m "fix: polish React workflow integration"
```
