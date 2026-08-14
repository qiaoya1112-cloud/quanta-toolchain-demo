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
        self.assertTrue(V2.exists(), "V2 HTML must exist as an independent file")
        original = parse_page(ORIGINAL)
        v2 = parse_page(V2)
        self.assertEqual(v2.visible_text, original.visible_text)
        self.assertEqual(v2.modal_ids, original.modal_ids)
        self.assertEqual(v2.onclick_handlers, original.onclick_handlers)

    def test_v2_is_an_independent_framework_free_document(self):
        self.assertTrue(V2.exists(), "V2 HTML must exist as an independent file")
        v2 = parse_page(V2)
        self.assertEqual(v2.root_attributes.get("data-visual-version"), "v2")
        self.assertEqual(v2.external_scripts, [])
        self.assertEqual(
            v2.modal_ids,
            ["modal-stage1", "modal-stage2", "modal-stage3"],
        )


if __name__ == "__main__":
    unittest.main()
