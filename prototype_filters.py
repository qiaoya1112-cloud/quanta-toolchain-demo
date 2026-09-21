"""Shared ownership controls for the in-memory prototype."""

import html
from urllib.parse import urlencode

from flask import request

# ponytail: fixed demo identity; replace with authenticated user ID when auth exists.
CURRENT_USER = "joanna.qiao"


def filter_url(**changes):
    args = request.args.to_dict()
    args.pop("page", None)
    args.update(changes)
    return "?" + html.escape(urlencode({k: v for k, v in args.items() if v}), quote=True)


def ownership_tabs():
    mine = request.args.get("scope") == "mine"
    links = "".join(
        f'<a href="{filter_url(scope=value, owner="", sel="", ver="")}" '
        f'aria-current="{"page" if active else "false"}" '
        f'class="ownership-option{" active" if active else ""}">{label}</a>'
        for value, label, active in (("all", "全部", not mine), ("mine", "我创建的", mine))
    )
    return '''<style>
    .ownership-tabs{display:inline-flex;width:max-content;gap:2px;padding:3px;margin:8px 0 12px;align-items:center;background:#f6f7f8;border-radius:5px}
    .fb-labeled.ownership-filters{padding:16px;row-gap:12px}
    .ownership-filters>.ownership-tabs{grid-column:1/-1;margin:0}
    .dataset-workspace .tree-panel .tree-head{padding:16px;justify-content:space-between}
    .dataset-workspace .tree-panel .ownership-tabs{margin:12px 16px}
    .dataset-workspace #datasetFilters{display:grid;gap:12px;padding:0 16px 16px}
    .dataset-workspace .tree-panel .tree-search,
    .dataset-workspace .tree-panel .tree-tag-search{padding:0;border:0}
    .ownership-option{display:inline-flex;align-items:center;justify-content:center;min-height:26px;padding:0 14px;border-radius:3px;color:#666;font-size:13px;line-height:20px;text-decoration:none}
    .ownership-option:hover{color:#116f79}
    .ownership-option.active{background:#fff;color:#149DAA;font-weight:500}
    .ownership-option:focus-visible{outline:2px solid #149DAA;outline-offset:2px}
    </style><nav class="ownership-tabs" aria-label="创建范围">''' + links + "</nav>"
