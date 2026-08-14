# AI Workflow Visual V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a visually richer `ai-workflow-share-enhanced-v2.html` while preserving the original page, content, and interactions.

**Architecture:** Duplicate the existing standalone HTML as an independently accessible V2 artifact, then add a scoped visual token layer and targeted CSS refinements. Protect scope with source-level tests and verify the rendered page and modal interactions in the browser.

**Tech Stack:** Standalone HTML, CSS, vanilla JavaScript, Python `unittest`, in-app browser verification

## Global Constraints

- Preserve `ai-workflow-share-enhanced.html` with SHA-256 `a5456472039b41ea5363c90da30e1f12bdbab05d7d830465543b6191b78d459d`.
- Create only `ai-workflow-share-enhanced-v2.html` for the visual version.
- Preserve all visible content, section order, modal content, and JavaScript behavior.
- Do not add React, Vue, Ant Design, or external component dependencies.
- Keep one light, cool gray-blue theme and one cobalt-blue accent family.
- Do not add human decision-point content, architecture diagrams, or data-flow content.

---

### Task 1: Add V2 Scope Protection Tests

**Files:**
- Create: `tests/test_ai_workflow_visual_v2.py`
- Test: `tests/test_ai_workflow_visual_v2.py`

**Interfaces:**
- Consumes: the original and V2 HTML files at the repository root
- Produces: regression checks for file preservation, content parity, visual tokens, modal behavior hooks, and dependency boundaries

- [ ] **Step 1: Write the failing regression tests**

```python
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "ai-workflow-share-enhanced.html"
V2 = ROOT / "ai-workflow-share-enhanced-v2.html"


class AiWorkflowVisualV2Test(unittest.TestCase):
    def test_original_file_is_unchanged(self):
        digest = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "a5456472039b41ea5363c90da30e1f12bdbab05d7d830465543b6191b78d459d",
        )

    def test_v2_preserves_content_and_interaction_contract(self):
        original = ORIGINAL.read_text(encoding="utf-8")
        v2 = V2.read_text(encoding="utf-8")
        for text in (
            "AI 辅助产品工具链实践",
            "产品团队的效率挑战",
            "工作流程",
            "S004 用户手册更新迭代",
            "效率对比",
            "阶段 1：需求阶段",
            "阶段 2：方案实施阶段",
            "阶段 3：验证阶段",
        ):
            self.assertIn(text, original)
            self.assertIn(text, v2)
        for hook in (
            "openModal('stage1')",
            "openModal('stage2')",
            "openModal('stage3')",
            "function openModal(stage)",
            "function closeModal(stage)",
        ):
            self.assertIn(hook, v2)

    def test_v2_has_scoped_visual_tokens_and_reduced_motion(self):
        v2 = V2.read_text(encoding="utf-8")
        self.assertIn('data-visual-version="v2"', v2)
        self.assertIn("--canvas: #f3f6fa", v2.lower())
        self.assertIn("--surface-emphasis: #eaf1f8", v2.lower())
        self.assertIn("@media (prefers-reduced-motion: reduce)", v2)

    def test_v2_does_not_add_framework_dependencies(self):
        v2 = V2.read_text(encoding="utf-8").lower()
        self.assertNotIn("react", v2)
        self.assertNotIn("vue", v2)
        self.assertNotIn("antd", v2)
        self.assertNotIn("unpkg.com", v2)
        self.assertNotIn("cdn.jsdelivr.net", v2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify the V2 checks fail**

Run: `python -m unittest tests.test_ai_workflow_visual_v2 -v`

Expected: the original hash test passes and V2 tests fail because `ai-workflow-share-enhanced-v2.html` does not exist.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_ai_workflow_visual_v2.py
git commit -m "test: define AI workflow visual v2 contract"
```

### Task 2: Create the Standalone V2 Visual Layer

**Files:**
- Create: `ai-workflow-share-enhanced-v2.html`
- Test: `tests/test_ai_workflow_visual_v2.py`

**Interfaces:**
- Consumes: the exact HTML structure and JavaScript behavior from `ai-workflow-share-enhanced.html`
- Produces: an independently accessible V2 HTML page marked with `data-visual-version="v2"`

- [ ] **Step 1: Duplicate the original HTML through an apply-patch file addition**

Create `ai-workflow-share-enhanced-v2.html` with the complete contents of the original file. Add `data-visual-version="v2"` to the root `<html>` element without changing content or behavior.

- [ ] **Step 2: Add semantic V2 visual tokens**

Add these tokens to `:root`:

```css
--canvas: #f3f6fa;
--surface: #f8fafc;
--surface-emphasis: #eaf1f8;
--surface-card: rgba(255, 255, 255, 0.94);
--surface-card-strong: #ffffff;
--text-v2-primary: #102033;
--text-v2-secondary: #52657a;
--border-v2: #d9e3ee;
--shadow-v2: 0 16px 45px rgba(67, 91, 118, 0.12);
```

- [ ] **Step 3: Replace the empty white canvas with section-aware depth**

Implement the visual layer with scoped CSS overrides:

```css
html[data-visual-version="v2"] body {
    background: var(--canvas);
    color: var(--text-v2-primary);
}

html[data-visual-version="v2"] .animated-bg {
    opacity: 1;
    background:
        radial-gradient(circle at 12% 8%, rgba(37, 99, 235, 0.08), transparent 28%),
        radial-gradient(circle at 88% 28%, rgba(37, 99, 235, 0.05), transparent 24%),
        radial-gradient(circle at 40% 78%, rgba(82, 101, 122, 0.05), transparent 30%);
    animation: none;
}

html[data-visual-version="v2"] .header,
html[data-visual-version="v2"] .section {
    background-color: transparent;
}

html[data-visual-version="v2"] .section:nth-of-type(even) {
    background: rgba(234, 241, 248, 0.72);
}
```

Calibrate selectors against the existing DOM so the alternating surfaces match the actual section order.

- [ ] **Step 4: Refine cards, workflow stages, and modals**

Use `--surface-card`, `--border-v2`, and `--shadow-v2` for existing card families. Preserve the current radius scale and reduce hover movement to no more than 4px. Apply the same surface system to modal panels and sidebars without changing layout dimensions.

- [ ] **Step 5: Add reduced-motion protection**

```css
@media (prefers-reduced-motion: reduce) {
    html[data-visual-version="v2"] *,
    html[data-visual-version="v2"] *::before,
    html[data-visual-version="v2"] *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
    }
}
```

- [ ] **Step 6: Run the V2 regression tests**

Run: `python -m unittest tests.test_ai_workflow_visual_v2 -v`

Expected: all tests pass.

- [ ] **Step 7: Commit the V2 artifact**

```bash
git add ai-workflow-share-enhanced-v2.html
git commit -m "feat: add AI workflow visual v2"
```

### Task 3: Browser Verification and Visual Calibration

**Files:**
- Modify if required: `ai-workflow-share-enhanced-v2.html`
- Test: `tests/test_ai_workflow_visual_v2.py`

**Interfaces:**
- Consumes: the local V2 URL served from port 5500
- Produces: verified screenshots and interaction evidence for the overview and all three modal states

- [ ] **Step 1: Open the V2 page in the in-app browser**

Open `http://127.0.0.1:5500/ai-workflow-share-enhanced-v2.html` and wait for the document to become visually stable.

- [ ] **Step 2: Capture and inspect the overview**

Verify that the canvas is cool gray-blue, section boundaries are visible, text contrast remains strong, and no content changed.

- [ ] **Step 3: Verify all three workflow modals**

Open stage 1, stage 2, and stage 3 from their existing cards. Confirm each modal title and close behavior.

- [ ] **Step 4: Verify narrow viewport behavior**

Check that the page has no new horizontal overflow and that background decoration remains clipped.

- [ ] **Step 5: Check runtime errors**

Inspect browser console logs and confirm no new errors originate from the V2 page.

- [ ] **Step 6: Re-run regression tests and diff checks**

Run:

```bash
python -m unittest tests.test_ai_workflow_visual_v2 -v
git diff --check
```

Expected: all tests pass and `git diff --check` reports no errors.

- [ ] **Step 7: Commit any visual calibration**

```bash
git add ai-workflow-share-enhanced-v2.html
git commit -m "style: calibrate AI workflow visual v2"
```
