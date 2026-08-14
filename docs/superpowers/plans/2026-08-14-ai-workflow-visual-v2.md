# AI Workflow Visual V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a visually richer `ai-workflow-share-enhanced-v2.html` while preserving the original page, content, and interactions.

**Architecture:** Duplicate the existing standalone HTML as an independently accessible V2 artifact, then add a scoped visual token layer and targeted CSS refinements. Protect scope with source-level tests and verify the rendered page and modal interactions in the browser.

**Tech Stack:** Standalone HTML, CSS, vanilla JavaScript, Python `unittest`, in-app browser verification

## Global Constraints

- Preserve the current user-edited `ai-workflow-share-enhanced.html` with SHA-256 `5360c9077ca170dd9d63bc2b5f4499b08725b3627c7e6191d9343b064f553ba2`.
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
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "ai-workflow-share-enhanced.html"
V2 = ROOT / "ai-workflow-share-enhanced-v2.html"


class PageContractParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ignored_depth = 0
        self.root_attributes = {}
        self.visible_text = []
        self.modal_ids = []
        self.onclick_handlers = []
        self.external_scripts = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in {"style", "script"}:
            self.ignored_depth += 1
        if tag == "html":
            self.root_attributes = attributes
        element_id = attributes.get("id", "")
        if element_id.startswith("modal-stage"):
            self.modal_ids.append(element_id)
        if "onclick" in attributes:
            self.onclick_handlers.append(attributes["onclick"])
        if tag == "script" and attributes.get("src"):
            self.external_scripts.append(attributes["src"])

    def handle_endtag(self, tag):
        if tag in {"style", "script"}:
            self.ignored_depth -= 1

    def handle_data(self, data):
        if self.ignored_depth:
            return
        normalized = " ".join(data.split())
        if normalized:
            self.visible_text.append(normalized)


def parse_page(path):
    parser = PageContractParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class AiWorkflowVisualV2Test(unittest.TestCase):
    def test_v2_preserves_visible_content_and_interactions(self):
        original = parse_page(ORIGINAL)
        v2 = parse_page(V2)
        self.assertEqual(v2.visible_text, original.visible_text)
        self.assertEqual(v2.modal_ids, original.modal_ids)
        self.assertEqual(v2.onclick_handlers, original.onclick_handlers)

    def test_v2_is_an_independent_framework_free_document(self):
        v2 = parse_page(V2)
        self.assertEqual(v2.root_attributes.get("data-visual-version"), "v2")
        self.assertEqual(v2.external_scripts, [])
        self.assertEqual(
            v2.modal_ids,
            ["modal-stage1", "modal-stage2", "modal-stage3"],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify the V2 checks fail**

Run: `python -m unittest tests.test_ai_workflow_visual_v2 -v`

Expected: both tests fail because `ai-workflow-share-enhanced-v2.html` does not exist.

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
