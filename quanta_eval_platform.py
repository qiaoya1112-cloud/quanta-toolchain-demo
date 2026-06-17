"""
Quanta 双盲评测平台 - Demo Version
具身智能模型双盲评测系统

Framework: Flask + HTML/CSS (inline templates)
Features:
  - 提示词管理 (Prompt Management)
  - Benchmark 管理 (Benchmark Management)
  - 评测任务管理 (Evaluation Task Management)
  - 双盲评测工作台 (Double-blind Evaluation Workbench)
  - BT-Davidson 排行榜 (Bradley-Terry Ranking with Davidson Ties)
  - 多维分析报告 (Multi-dimensional Analysis Report)

Usage:
  pip install flask
  python quanta_eval_platform.py
  # Open http://localhost:5001
"""

import json
import math
import uuid
import random
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, jsonify, flash

app = Flask(__name__)
app.secret_key = "quanta-eval-demo-secret"

# ════════════════════════════════════════════════════════════════
# Section 1: Mock Data
# ════════════════════════════════════════════════════════════════

MODELS = [
    {"id": "m1", "name": "Spirit v1.5", "version": "1.5.0", "arch": "Flow Matching VLA", "params": "3.3B", "status": "\u5df2\u53d1\u5e03", "family": "Spirit", "released_at": "2025-08-15"},
    {"id": "m2", "name": "Spirit v1.6-alpha", "version": "1.6.0-alpha", "arch": "Flow Matching VLA", "params": "3.3B", "status": "\u8bad\u7ec3\u4e2d", "family": "Spirit", "released_at": "2025-10-20"},
    {"id": "m3", "name": "Spirit v1.6-beta", "version": "1.6.0-beta", "arch": "Flow Matching VLA", "params": "3.3B", "status": "\u8bc4\u6d4b\u4e2d", "family": "Spirit", "released_at": "2025-12-12"},
    {"id": "m4", "name": "Spirit v1.6-rc1", "version": "1.6.0-rc1", "arch": "Flow Matching VLA+", "params": "3.5B", "status": "\u8bc4\u6d4b\u4e2d", "family": "Spirit", "released_at": "2026-02-28"},
    {"id": "m5", "name": "\u03c0\u2080 (Pi-Zero)", "version": "1.0", "arch": "Flow Matching VLA", "params": "3.3B", "status": "\u5916\u90e8\u57fa\u7ebf", "family": "\u03c0\u2080", "released_at": "2024-11-10"},
    {"id": "m6", "name": "\u03c0\u2080-FAST", "version": "1.0", "arch": "Autoregressive+FAST", "params": "3.3B", "status": "\u5916\u90e8\u57fa\u7ebf", "family": "\u03c0\u2080", "released_at": "2025-02-05"},
    {"id": "m7", "name": "DreamZero", "version": "2.1", "arch": "Diffusion Policy", "params": "2.8B", "status": "\u5916\u90e8\u57fa\u7ebf", "family": "DreamZero", "released_at": "2025-06-18"},
    {"id": "m8", "name": "PG-Flow-DROID", "version": "1.0", "arch": "PaliGemma+Flow", "params": "3.0B", "status": "\u5916\u90e8\u57fa\u7ebf", "family": "PG-Flow", "released_at": "2024-12-22"},
]

# Labels now reference tag IDs from TAXONOMY (established after TAXONOMY is defined)
PROMPTS = [
    {
        "id": "p1",
        "high_level": "\u65b9\u4f4d\u611f\u77e5\u6d4b\u8bd5",
        "high_level_en": "Spatial Orientation Test",
        "enabled": True,
        "creator": "Lance Li",
        "low_levels": [
            {"id": "p1-1", "zh": "\u8bc6\u522b\u684c\u9762\u4e0a\u7269\u4f53\u7684\u76f8\u5bf9\u4f4d\u7f6e", "en": "identify relative positions of objects on the desk",
             "labels": ["cap_spatial_awareness", "cap_spatial_lr", "cap_spatial_fb"]},
            {"id": "p1-2", "zh": "\u5c06\u7269\u4f53\u6309\u6307\u5b9a\u65b9\u4f4d\u6392\u5217", "en": "arrange objects in the specified orientation",
             "labels": ["cap_spatial_awareness", "cap_spatial_ud", "act_place"]},
        ],
    },
    {
        "id": "p2",
        "high_level": "\u6574\u7406\u684c\u9762 (P0)",
        "high_level_en": "Tidy the desk (P0)",
        "enabled": True,
        "creator": "Lance Li",
        "low_levels": [
            {"id": "p2-1", "zh": "\u62fe\u53d6\u7ea2\u8272\u7cd6\u679c", "en": "pick up the red candy",
             "labels": ["act_pick", "cap_object_understanding"]},
            {"id": "p2-2", "zh": "\u5c06\u7cd6\u679c\u653e\u5165\u4eba\u624b\u4e2d", "en": "put the candy into the human's hand",
             "labels": ["act_place", "cap_precision_manipulation"]},
            {"id": "p2-3", "zh": "\u62fe\u53d6\u84dd\u8272\u7cd6\u679c", "en": "pick up the blue candy",
             "labels": ["act_pick", "cap_object_understanding"]},
            {"id": "p2-4", "zh": "\u5c06\u7cd6\u679c\u653e\u5165\u4eba\u624b\u4e2d", "en": "put the candy into the human's hand",
             "labels": ["act_place", "cap_precision_manipulation"]},
            {"id": "p2-5", "zh": "\u62fe\u53d6\u7eff\u8272\u7cd6\u679c", "en": "pick up the green candy",
             "labels": ["act_pick", "cap_object_understanding"]},
            {"id": "p2-6", "zh": "\u5c06\u7cd6\u679c\u653e\u5165\u4eba\u624b\u4e2d", "en": "put the candy into the human's hand",
             "labels": ["act_place", "cap_precision_manipulation"]},
        ],
    },
    {
        "id": "p3",
        "high_level": "\u5c06\u7279\u5b9a\u989c\u8272\u7cd6\u653e\u5728\u624b\u4e0a (P0)",
        "high_level_en": "Place candy of specific color in hand (P0)",
        "enabled": True,
        "creator": "Lance Li",
        "low_levels": [
            {"id": "p3-1", "zh": "\u62fe\u53d6\u7c89\u8272\u7cd6\u679c", "en": "pick up the pink candy",
             "labels": ["act_pick", "cap_object_understanding"]},
            {"id": "p3-2", "zh": "\u5c06\u7cd6\u679c\u653e\u5165\u4eba\u624b\u4e2d", "en": "put the candy into the human's hand",
             "labels": ["act_place", "cap_precision_manipulation"]},
            {"id": "p3-3", "zh": "\u62fe\u53d6\u9ec4\u8272\u7cd6\u679c", "en": "pick up the yellow candy",
             "labels": ["act_pick", "cap_object_understanding"]},
            {"id": "p3-4", "zh": "\u5c06\u7cd6\u679c\u653e\u5165\u4eba\u624b\u4e2d", "en": "put the candy into the human's hand",
             "labels": ["act_place", "cap_precision_manipulation"]},
        ],
    },
    {
        "id": "p4",
        "high_level": "\u6d47\u82b1 (P0)",
        "high_level_en": "Water the plant (P0)",
        "enabled": False,
        "creator": "Lance Li",
        "low_levels": [
            {"id": "p4-1", "zh": "\u62fe\u53d6\u6d47\u6c34\u58f6", "en": "pick up the watering can",
             "labels": ["act_pick", "obj_bottle"]},
            {"id": "p4-2", "zh": "\u5c06\u6c34\u5012\u5165\u82b1\u76c6\u4e2d", "en": "pour water into the flower pot",
             "labels": ["act_pour", "cap_precision_manipulation"]},
            {"id": "p4-3", "zh": "\u653e\u56de\u6d47\u6c34\u58f6", "en": "put the watering can back",
             "labels": ["act_place"]},
        ],
    },
    {
        "id": "p5",
        "high_level": "\u6446\u82b1 (P0)",
        "high_level_en": "Arrange flowers (P0)",
        "enabled": True,
        "creator": "Lance Li",
        "low_levels": [
            {"id": "p5-1", "zh": "\u4ece\u82b1\u7bee\u4e2d\u53d6\u51fa\u82b1\u6735", "en": "take the flower from the basket",
             "labels": ["act_take_out", "cap_object_understanding"]},
            {"id": "p5-2", "zh": "\u5c06\u82b1\u6735\u63d2\u5165\u82b1\u74f6", "en": "place the flower into the vase",
             "labels": ["act_insert", "cap_precision_manipulation"]},
        ],
    },
    {
        "id": "p6",
        "high_level": "VP\u4ece\u62bd\u5c49\u79fb\u5230\u9876\u683c",
        "high_level_en": "Move VP from drawer to top shelf",
        "enabled": True,
        "creator": "Rick Guo",
        "low_levels": [
            {"id": "p6-1", "zh": "\u7528\u5de6\u624b\u6253\u5f00\u4e0a\u5c42\u62bd\u5c49", "en": "open the upper drawer with left hand",
             "labels": ["act_open", "act_pull_open"]},
            {"id": "p6-2", "zh": "\u4ece\u62bd\u5c49\u53d6\u51fa\u68d5\u8272\u6c34\u7334\u6446\u4ef6", "en": "take out the brown monkey figurine from the drawer",
             "labels": ["act_take_out", "cap_object_understanding"]},
            {"id": "p6-3", "zh": "\u5c06\u6c34\u7334\u6446\u4ef6\u653e\u5728\u9876\u5c42\u4e2d\u683c", "en": "place the monkey figurine on the top shelf middle slot",
             "labels": ["act_place", "cap_spatial_ud", "cap_precision_manipulation"]},
            {"id": "p6-4", "zh": "\u7528\u5de6\u624b\u5173\u95ed\u62bd\u5c49", "en": "close the drawer with left hand",
             "labels": ["act_close"]},
        ],
    },
]

TAXONOMY = {
    "version": "1.0",
    "dimensions": [
        {
            "id": "capability", "name": "\u80fd\u529b\u6807\u7b7e", "name_en": "Capability Tags",
            "color": "blue",
            "tags": [
                {"id": "cap_spatial_awareness", "name": "\u65b9\u4f4d\u7406\u89e3", "name_en": "Spatial Awareness",
                 "description": "\u8bc4\u4f30\u6a21\u578b\u5bf9\u7a7a\u95f4\u76f8\u5bf9\u4f4d\u7f6e\u7684\u8fa8\u8bc6\u80fd\u529b\u53ca\u6307\u4ee4\u6267\u884c\u7cbe\u5ea6",
                 "sub_tags": [
                     {"id": "cap_spatial_lr", "name": "\u5de6\u53f3", "name_en": "Left / Right"},
                     {"id": "cap_spatial_fb", "name": "\u524d\u540e", "name_en": "Front / Back"},
                     {"id": "cap_spatial_ud", "name": "\u4e0a\u4e0b", "name_en": "Up / Down"},
                     {"id": "cap_spatial_io", "name": "\u5185\u5916", "name_en": "Inside / Outside"},
                     {"id": "cap_spatial_nf", "name": "\u8fdc\u8fd1", "name_en": "Near / Far"},
                 ]},
                {"id": "cap_action_understanding", "name": "\u52a8\u4f5c\u7406\u89e3", "name_en": "Action Understanding",
                 "description": "\u9a8c\u8bc1\u6a21\u578b\u5bf9\u52a8\u8bcd\u8bed\u4e49\u4e0e\u5b9e\u9645\u7269\u7406\u52a8\u4f5c\u7684\u6620\u5c04\u80fd\u529b", "sub_tags": []},
                {"id": "cap_object_understanding", "name": "\u7269\u4f53\u7406\u89e3", "name_en": "Object Noun Understanding",
                 "description": "\u8003\u6838\u6a21\u578b\u5728\u590d\u6742\u80cc\u666f\u4e2d\u5bf9\u76ee\u6807\u7269\u4f53\u7684\u96f6\u6837\u672c\u8bc6\u522b\u80fd\u529b", "sub_tags": []},
                {"id": "cap_long_horizon", "name": "\u957f\u7a0b\u4efb\u52a1", "name_en": "Long Horizon",
                 "description": "\u8003\u5bdf\u6a21\u578b\u5728\u957f\u7a0b\u4efb\u52a1\u4e2d\u7684\u903b\u8f91\u89c4\u5212\u4e0e\u8fde\u7eed\u6267\u884c\u80fd\u529b", "sub_tags": []},
                {"id": "cap_reasoning", "name": "\u63a8\u7406\u80fd\u529b", "name_en": "Reasoning",
                 "description": "\u6a21\u578b\u80fd\u591f\u5c06 high-level prompt \u62c6\u5206\u6210\u5b50\u4efb\u52a1\u7684\u80fd\u529b", "sub_tags": []},
                {"id": "cap_precision_manipulation", "name": "\u7cbe\u786e\u6027\u64cd\u63a7", "name_en": "Precision Manipulation",
                 "description": "\u4e13\u6ce8\u4e8e\u4e9a\u5398\u7c73\u7ea7\u7684\u672b\u7aef\u5b9a\u4f4d\u4e0e\u6267\u884c\u7cbe\u5ea6", "sub_tags": []},
            ],
        },
        {
            "id": "action", "name": "\u52a8\u4f5c\u6807\u7b7e", "name_en": "Action Tags",
            "color": "green",
            "tags": [
                {"id": "act_pick_place", "name": "\u62ff\u653e\u7c7b", "name_en": "Pick & Place",
                 "sub_tags": [
                     {"id": "act_pick", "name": "\u62ff\u53d6"}, {"id": "act_place", "name": "\u653e\u7f6e"},
                     {"id": "act_put_in", "name": "\u653e\u5165"}, {"id": "act_take_out", "name": "\u53d6\u51fa"},
                     {"id": "act_stack", "name": "\u53e0\u653e"}, {"id": "act_throw", "name": "\u6254"},
                 ]},
                {"id": "act_move", "name": "\u79fb\u52a8\u7c7b", "name_en": "Movement",
                 "sub_tags": [
                     {"id": "act_push", "name": "\u63a8\u52a8"}, {"id": "act_pull", "name": "\u62c9\u52a8"},
                     {"id": "act_rotate", "name": "\u65cb\u8f6c"}, {"id": "act_flip", "name": "\u7ffb\u8f6c"},
                     {"id": "act_drag", "name": "\u62d6\u62fd"}, {"id": "act_swap", "name": "\u4ea4\u6362"},
                 ]},
                {"id": "act_open_close", "name": "\u5f00\u5408\u7c7b", "name_en": "Open & Close",
                 "sub_tags": [
                     {"id": "act_open", "name": "\u6253\u5f00"}, {"id": "act_close", "name": "\u5173\u95ed"},
                     {"id": "act_twist_open", "name": "\u62e7\u5f00"}, {"id": "act_pull_open", "name": "\u62c9\u5f00"},
                     {"id": "act_push_open", "name": "\u63a8\u5f00"}, {"id": "act_lift_open", "name": "\u6380\u8d77"},
                 ]},
                {"id": "act_deform", "name": "\u5f62\u53d8\u7c7b", "name_en": "Deformation",
                 "sub_tags": [
                     {"id": "act_fold", "name": "\u6298\u53e0"}, {"id": "act_unfold", "name": "\u5c55\u5f00"},
                     {"id": "act_squeeze", "name": "\u6324"}, {"id": "act_wring", "name": "\u62e7\u5e72"},
                     {"id": "act_roll", "name": "\u5377"}, {"id": "act_knot", "name": "\u6253\u7ed3"},
                 ]},
                {"id": "act_assembly", "name": "\u88c5\u914d\u7c7b", "name_en": "Assembly",
                 "sub_tags": [
                     {"id": "act_insert", "name": "\u63d2\u5165"}, {"id": "act_tighten", "name": "\u62e7\u7d27"},
                     {"id": "act_assemble", "name": "\u7ec4\u88c5"}, {"id": "act_disassemble", "name": "\u62c6\u5206"},
                     {"id": "act_stick", "name": "\u8d34"}, {"id": "act_peel_off", "name": "\u63ed\u4e0b"},
                 ]},
                {"id": "act_processing", "name": "\u52a0\u5de5\u7c7b", "name_en": "Processing",
                 "sub_tags": [
                     {"id": "act_pour", "name": "\u5012"}, {"id": "act_stir", "name": "\u6405\u62cc"},
                     {"id": "act_cut", "name": "\u5207"}, {"id": "act_peel", "name": "\u5265"},
                     {"id": "act_sprinkle", "name": "\u6492"}, {"id": "act_cover", "name": "\u76d6"},
                 ]},
            ],
        },
        {
            "id": "object", "name": "\u7269\u4f53\u5206\u7c7b", "name_en": "Object Categories",
            "color": "orange",
            "tags": [
                {"id": "obj_container", "name": "\u5bb9\u5668\u7c7b", "name_en": "Containers",
                 "sub_tags": [
                     {"id": "obj_plastic_cup", "name": "\u5851\u6599\u676f"}, {"id": "obj_ceramic_cup", "name": "\u9676\u74f7\u676f"},
                     {"id": "obj_bowl", "name": "\u7897"}, {"id": "obj_plate", "name": "\u9910\u76d8"},
                     {"id": "obj_bottle", "name": "\u74f6\u5b50"}, {"id": "obj_storage_box", "name": "\u6536\u7eb3\u76d2"},
                 ]},
                {"id": "obj_tool", "name": "\u5de5\u5177\u7c7b", "name_en": "Tools",
                 "sub_tags": [
                     {"id": "obj_scissors", "name": "\u526a\u5200"}, {"id": "obj_screwdriver", "name": "\u87ba\u4e1d\u5200"},
                     {"id": "obj_wrench", "name": "\u6273\u624b"}, {"id": "obj_pen", "name": "\u7b14"},
                     {"id": "obj_ruler", "name": "\u5c3a\u5b50"}, {"id": "obj_clip", "name": "\u5939\u5b50"},
                 ]},
                {"id": "obj_fabric", "name": "\u5e03\u6599\u7c7b", "name_en": "Fabrics & Textiles",
                 "sub_tags": [
                     {"id": "obj_towel", "name": "\u6bdb\u5dfe"}, {"id": "obj_clothes", "name": "\u8863\u670d"},
                     {"id": "obj_socks", "name": "\u889c\u5b50"}, {"id": "obj_napkin", "name": "\u9910\u5dfe"},
                     {"id": "obj_bed_sheet", "name": "\u5e8a\u5355"}, {"id": "obj_gloves", "name": "\u624b\u5957"},
                 ]},
                {"id": "obj_food", "name": "\u98df\u7269\u7c7b", "name_en": "Food",
                 "sub_tags": [
                     {"id": "obj_bread", "name": "\u9762\u5305"}, {"id": "obj_apple", "name": "\u82f9\u679c"},
                     {"id": "obj_banana", "name": "\u9999\u8549"}, {"id": "obj_tomato", "name": "\u756a\u8304"},
                     {"id": "obj_egg", "name": "\u9e21\u86cb"}, {"id": "obj_milk", "name": "\u725b\u5976"},
                 ]},
                {"id": "obj_kitchen", "name": "\u53a8\u623f\u7528\u54c1", "name_en": "Kitchenware",
                 "sub_tags": [
                     {"id": "obj_wok", "name": "\u7092\u9505"}, {"id": "obj_cutting_board", "name": "\u7827\u677f"},
                     {"id": "obj_chopsticks", "name": "\u7b77\u5b50"}, {"id": "obj_spoon", "name": "\u52fa\u5b50"},
                     {"id": "obj_spatula", "name": "\u94f2\u5b50"}, {"id": "obj_cling_wrap", "name": "\u4fdd\u9c9c\u819c"},
                 ]},
                {"id": "obj_electronics", "name": "\u7535\u5b50\u4ea7\u54c1", "name_en": "Electronics",
                 "sub_tags": [
                     {"id": "obj_phone", "name": "\u624b\u673a"}, {"id": "obj_keyboard", "name": "\u952e\u76d8"},
                     {"id": "obj_mouse", "name": "\u9f20\u6807"}, {"id": "obj_data_cable", "name": "\u6570\u636e\u7ebf"},
                     {"id": "obj_usb_drive", "name": "U\u76d8"}, {"id": "obj_earphones", "name": "\u8033\u673a"},
                 ]},
            ],
        },
    ],
}


# ── Tag Index: flat lookup  tag_id → {name, color, path} ──
# path = "维度/二级" or "维度/二级/三级", used for display
def _build_tag_index():
    idx = {}
    for dim in TAXONOMY["dimensions"]:
        color = dim.get("color", "blue")
        dim_name = dim["name"]
        # Dimension itself is NOT selectable (it's a grouping header)
        for tag in dim["tags"]:
            l2_path = f"{dim_name} / {tag['name']}"
            idx[tag["id"]] = {"name": tag["name"], "color": color, "path": l2_path}
            for st in tag.get("sub_tags", []):
                l3_path = f"{dim_name} / {tag['name']} / {st['name']}"
                idx[st["id"]] = {"name": st["name"], "color": color, "path": l3_path}
    return idx

TAG_INDEX = _build_tag_index()


def render_tag(tag_id):
    """Render a tag ID as path-style AntD tag: '维度 / 二级 / 三级'."""
    info = TAG_INDEX.get(tag_id)
    if not info:
        return f'<span class="ant-tag">{tag_id}</span>'
    return f'<span class="ant-tag ant-tag-{info["color"]}">{info["path"]}</span>'


def prompt_aggregated_labels(p):
    """Aggregate tag IDs from all low-level children, return unique sorted list."""
    all_ids = set()
    for ll in p.get("low_levels", []):
        for tid in ll.get("labels", []):
            all_ids.add(tid)
    return sorted(all_ids)


def render_tags_html(tag_ids):
    """Render a list of tag IDs as HTML."""
    if not tag_ids:
        return '<span class="ant-tag">--</span>'
    return " ".join(render_tag(tid) for tid in tag_ids)


def _build_tip_text(tag_ids):
    """Build tooltip text: tags separated by ；, path levels by /."""
    if not tag_ids:
        return ""
    paths = []
    for tid in tag_ids:
        info = TAG_INDEX.get(tid)
        if info:
            paths.append(info["path"])
        else:
            paths.append(tid)
    return "；".join(paths)


def _strip_html(s):
    import re
    t = re.sub(r'<[^>]+>', ' ', s).strip()
    return re.sub(r'\s+', ' ', t)


def td_tip(content, extra_attr="", tip_text=None):
    """Return a <td> with data-tip for JS tooltip. tip_text overrides auto-strip."""
    if tip_text is None:
        tip_text = _strip_html(content)
    tip = tip_text.replace('"', '&quot;')
    if not tip or tip == '--':
        return f"<td {extra_attr}>{content}</td>"
    return f'<td {extra_attr} data-tip="{tip}">{content}</td>'


def build_tree_selector_html(instance_id):
    """Build a proper TreeSelect dropdown with expand/collapse arrows, all levels selectable."""
    html = ""
    for dim in TAXONOMY["dimensions"]:
        dim_name = dim["name"]
        # L1: dimension — has children (L2 tags)
        l2_nodes = ""
        for tag in dim["tags"]:
            subs = tag.get("sub_tags", [])
            l2_path = f"{dim_name} / {tag['name']}"
            # L3 children
            l3_nodes = ""
            for st in subs:
                l3_path = f"{dim_name} / {tag['name']} / {st['name']}"
                l3_nodes += f'<div class="ts-node"><div class="ts-row" data-id="{st["id"]}" data-path="{l3_path}"><span class="ts-arrow empty"></span>{st["name"]}</div></div>'
            has_children = ' expanded' if False else ''
            arrow_cls = 'ts-arrow' if subs else 'ts-arrow empty'
            children_html = f'<div class="ts-children">{l3_nodes}</div>' if subs else ''
            l2_nodes += f'<div class="ts-node"><div class="ts-row" data-id="{tag["id"]}" data-path="{l2_path}"><span class="{arrow_cls}">&#9654;</span>{tag["name"]}</div>{children_html}</div>'
        html += f'<div class="ts-node"><div class="ts-row ts-row-dim"><span class="ts-arrow">&#9654;</span><strong>{dim_name}</strong></div><div class="ts-children">{l2_nodes}</div></div>'
    return html


BENCHMARKS = [
    {
        "id": "b1", "name": "\u57fa\u7840\u64cd\u4f5c\u80fd\u529b\u8bc4\u6d4b",
        "description": "\u8bc4\u6d4b\u6a21\u578b\u5728\u57fa\u7840\u6293\u53d6\u3001\u653e\u7f6e\u3001\u63a8\u62c9\u7b49\u64cd\u4f5c\u4e0a\u7684\u80fd\u529b",
        "scene_id": "s1", "prompt_ids": ["p1", "p2", "p3"], "criteria_id": "c1",
        "creator": "Lance Li", "created_at": "2026-04-01",
    },
    {
        "id": "b2", "name": "\u5de5\u5177\u4f7f\u7528\u8bc4\u6d4b",
        "description": "\u8bc4\u6d4b\u6a21\u578b\u4f7f\u7528\u5de5\u5177\u5b8c\u6210\u4efb\u52a1\u7684\u80fd\u529b\uff0c\u5982\u6d47\u82b1\u3001\u64e6\u684c\u5b50\u7b49",
        "scene_id": "s2", "prompt_ids": ["p4", "p5"], "criteria_id": "c1",
        "creator": "Lance Li", "created_at": "2026-04-03",
    },
    {
        "id": "b3", "name": "\u62bd\u5c49\u67dc\u4f53\u64cd\u4f5c\u8bc4\u6d4b",
        "description": "\u8bc4\u6d4b\u6a21\u578b\u5728\u5f00\u5173\u62bd\u5c49\u3001\u7269\u54c1\u642c\u79fb\u7b49\u590d\u6742\u64cd\u4f5c\u94fe\u4e0a\u7684\u80fd\u529b",
        "scene_id": "s3", "prompt_ids": ["p6"], "criteria_id": "c4",
        "creator": "Rick Guo", "created_at": "2026-04-05",
    },
    {
        "id": "b4", "name": "\u7efc\u5408\u80fd\u529b\u8bc4\u6d4b v1",
        "description": "\u8986\u76d6\u6240\u6709\u573a\u666f\u7c7b\u578b\u7684\u7efc\u5408\u8bc4\u6d4b\u57fa\u51c6\uff0c\u7528\u4e8e RoboArena \u5bf9\u6807",
        "scene_id": "s1", "prompt_ids": ["p1", "p2", "p3", "p4", "p5", "p6"], "criteria_id": "c1",
        "creator": "Lance Li", "created_at": "2026-04-08",
    },
]

CRITERIA_TYPES = {
    "pass_fail": {"label": "\u6210\u529f\u5931\u8d25", "label_en": "Pass / Fail", "color": "",
                  "desc": "\u6bcf\u4e2a\u6a21\u578b\u72ec\u7acb\u5224\u5b9a\u6210\u529f\u6216\u5931\u8d25"},
    "scale": {"label": "\u91cf\u8868\u8bc4\u5206", "label_en": "Scale Rating", "color": "",
              "desc": "\u6309\u91cf\u8868\u523b\u5ea6\u6253\u5206\uff0c\u6bcf\u4e2a\u6a21\u578b\u72ec\u7acb\u8bc4\u5206"},
    "preference": {"label": "\u504f\u597d\u9009\u62e9", "label_en": "Preference", "color": "",
                   "desc": "\u4e24\u4e24\u5bf9\u6bd4\uff0c\u9009\u62e9\u66f4\u4f18\u65b9\u6216\u5e73\u5c40"},
    "baseline": {"label": "\u57fa\u7ebf\u5bf9\u7167", "label_en": "Baseline Compare", "color": "",
                 "desc": "\u4e0e\u57fa\u7ebf\u6a21\u578b\u5bf9\u6bd4\uff0c\u5224\u5b9a\u80dc/\u8d1f/\u5e73"},
}

CRITERIA = [
    {
        "id": "c1",
        "name": "RoboArena \u6807\u51c6",
        "type": "preference",
        "description": "RoboArena \u5b98\u65b9\u8bc4\u6d4b\u6807\u51c6\uff0c\u91c7\u7528\u53cc\u76f2 A/B \u5bf9\u6bd4 + \u4eba\u7c7b\u504f\u597d\u6295\u7968 + Bradley-Terry \u6392\u540d\u3002\u8bc4\u6d4b\u91c7\u96c6\u4e09\u7ef4\u6570\u636e\uff1a\u8fdb\u5ea6\u5206\u3001\u4e8c\u5143\u504f\u597d\u3001\u6587\u5b57\u8bf4\u660e\u3002",
        "creator": "Lance Li",
        "created_at": "2026-04-01",
        "form": {
            "type_module": {
                "items": [
                    {"prompt": "\u54ea\u65b9\u66f4\u4f18\uff1f", "winner": None, "is_tie": False},
                ]
            },
            "scale_module": {
                "items": [
                    {"prompt": "\u8fdb\u5ea6\u5206", "metric_name": "progress_score", "metric_description": "\u4efb\u52a1\u5b8c\u6210\u8fdb\u5ea6\uff0c0.0=\u65e0\u4efb\u4f55\u8fdb\u5c55\uff0c1.0=\u5b8c\u5168\u6210\u529f", "score_range": {"min": 0.0, "max": 1.0}, "value": None},
                ]
            },
            "note": "\u8bf7\u7528\u81ea\u7136\u8bed\u8a00\u89e3\u91ca\u60a8\u7684\u504f\u597d\u9009\u62e9\u539f\u56e0",
        },
    },
    {
        "id": "c2",
        "name": "\u57fa\u7840\u64cd\u4f5c\u80fd\u529b\u6d4b\u8bd5",
        "type": "pass_fail",
        "description": "\u5224\u5b9a\u6a21\u578b\u662f\u5426\u6210\u529f\u5b8c\u6210\u6307\u5b9a\u64cd\u4f5c\u4efb\u52a1\uff0c\u4e8c\u5143\u5224\u5b9a\u3002",
        "creator": "Lance Li",
        "created_at": "2026-04-05",
        "form": {
            "type_module": {
                "items": [
                    {"prompt": "\u4efb\u52a1\u662f\u5426\u5b8c\u6210\uff1f", "model": "", "result": ""},
                ]
            },
            "scale_module": {"items": []},
            "note": None,
        },
    },
    {
        "id": "c3",
        "name": "\u591a\u7ef4\u80fd\u529b\u8bc4\u4f30",
        "type": "scale",
        "description": "\u6309\u591a\u4e2a\u80fd\u529b\u7ef4\u5ea6\u8fdb\u884c\u91cf\u8868\u6253\u5206\uff0c\u8bc4\u4f30\u6a21\u578b\u7684\u7efc\u5408\u80fd\u529b\u3002",
        "creator": "Rick Guo",
        "created_at": "2026-04-10",
        "form": {
            "type_module": {
                "items": [
                    {"prompt": "\u6293\u53d6\u7cbe\u5ea6", "metric_name": "grasp_accuracy", "metric_description": "\u672b\u7aef\u6267\u884c\u5668\u6293\u53d6\u76ee\u6807\u7269\u4f53\u7684\u7cbe\u5ea6", "score_range": {"min": 0, "max": 5}, "value": None},
                    {"prompt": "\u8def\u5f84\u89c4\u5212", "metric_name": "path_planning", "metric_description": "\u8fd0\u52a8\u8def\u5f84\u7684\u5408\u7406\u6027\u4e0e\u5e73\u6ed1\u5ea6", "score_range": {"min": 0, "max": 5}, "value": None},
                    {"prompt": "\u5f02\u5e38\u6062\u590d", "metric_name": "error_recovery", "metric_description": "\u9047\u5230\u5f02\u5e38\u65f6\u7684\u81ea\u6211\u7ea0\u6b63\u80fd\u529b", "score_range": {"min": 0, "max": 5}, "value": None},
                ]
            },
            "scale_module": {"items": []},
            "note": "\u8bf7\u6839\u636e\u89c2\u5bdf\u5230\u7684\u5b9e\u9645\u64cd\u4f5c\u8868\u73b0\u6253\u5206",
        },
    },
    {
        "id": "c4",
        "name": "\u57fa\u7ebf\u6a21\u578b\u5bf9\u7167\u8bc4\u6d4b",
        "type": "baseline",
        "description": "\u4ee5 \u03c0\u2080 (Pi-Zero) \u4f5c\u4e3a\u57fa\u7ebf\u6a21\u578b\uff0c\u5c06\u5f85\u8bc4\u6a21\u578b\u4e0e\u57fa\u7ebf\u9010\u4efb\u52a1\u5bf9\u6bd4\uff0c\u5224\u5b9a\u80dc/\u8d1f/\u5e73\u3002",
        "creator": "Rick Guo",
        "created_at": "2026-04-12",
        "form": {
            "type_module": {
                "items": [
                    {"prompt": "\u4e0e\u57fa\u7ebf\u6a21\u578b\u76f8\u6bd4\uff0c\u8868\u73b0\u5982\u4f55\uff1f", "result": ""},
                ]
            },
            "scale_module": {
                "items": [
                    {"prompt": "\u5b8c\u6210\u5ea6\u5dee\u5f02", "metric_name": "completion_delta", "metric_description": "\u4e0e\u57fa\u7ebf\u6a21\u578b\u7684\u4efb\u52a1\u5b8c\u6210\u5ea6\u5dee\u503c\uff0c\u6b63\u503c\u8868\u793a\u4f18\u4e8e\u57fa\u7ebf", "score_range": {"min": -1.0, "max": 1.0}, "value": None},
                ]
            },
            "note": "\u57fa\u7ebf\u6a21\u578b\uff1a\u03c0\u2080 (Pi-Zero) v1.0",
        },
    },
]

SCENES = [
    {
        "id": "s1", "name": "\u6807\u51c6\u684c\u9762\u573a\u666f", "description": "\u5e38\u89c4\u529e\u516c\u684c\u9762\u73af\u5883\uff0c\u7528\u4e8e\u57fa\u7840\u62fe\u53d6\u3001\u653e\u7f6e\u3001\u6574\u7406\u7c7b\u4efb\u52a1\u7684\u8bc4\u6d4b",
        "creator": "Lance Li", "created_at": "2026-04-02",
        "environment": {
            "type": "\u5ba4\u5185-\u684c\u9762",
            "workspace": {"length": 120, "width": 80, "height": 75},
            "conditions": {"lighting": "\u5747\u5300\u65e5\u5149\u706f (500lux)", "surface": "\u767d\u8272\u54d1\u5149\u684c\u9762"},
        },
        "objects": [
            {"object_id": "o1", "name": "\u7cd6\u679c", "category": "\u98df\u7269\u7c7b", "properties": {"size": {"length": 3, "width": 3, "height": 2}, "weight": 15, "material": "\u5851\u6599\u5305\u88c5"}, "initial_pose": {"region": "\u684c\u9762\u4e2d\u533a", "random": False}, "count": 6},
            {"object_id": "o2", "name": "\u6536\u7eb3\u76d2", "category": "\u5bb9\u5668\u7c7b", "properties": {"size": {"length": 20, "width": 15, "height": 10}, "weight": 200, "material": "\u5851\u6599"}, "initial_pose": {"region": "\u684c\u9762\u53f3\u4fa7", "random": False}, "count": 1},
        ],
        "references": {
            "images": [{"url": "/static/scene_desk.jpg", "description": "\u684c\u9762\u573a\u666f\u5168\u666f"}],
            "capture_videos": [],
            "demo_videos": [{"url": "/static/demo_tidy.mp4", "description": "\u6574\u7406\u684c\u9762\u6f14\u793a", "duration": 45}],
        },
    },
    {
        "id": "s2", "name": "\u53a8\u623f\u64cd\u4f5c\u573a\u666f", "description": "\u6a21\u62df\u53a8\u623f\u64cd\u4f5c\u53f0\u73af\u5883\uff0c\u5305\u542b\u6d47\u6c34\u3001\u5012\u6c34\u3001\u5de5\u5177\u4f7f\u7528\u7b49\u4efb\u52a1",
        "creator": "Lance Li", "created_at": "2026-04-05",
        "environment": {
            "type": "\u5ba4\u5185-\u53a8\u623f",
            "workspace": {"length": 150, "width": 60, "height": 90},
            "conditions": {"lighting": "\u5415\u5149\u706f (400lux)", "surface": "\u4e0d\u9508\u94a2\u53f0\u9762"},
        },
        "objects": [
            {"object_id": "o3", "name": "\u6d47\u6c34\u58f6", "category": "\u5de5\u5177\u7c7b", "properties": {"size": {"length": 25, "width": 12, "height": 20}, "weight": 350, "material": "\u5851\u6599"}, "initial_pose": {"region": "\u53f0\u9762\u5de6\u4fa7", "random": False}, "count": 1},
            {"object_id": "o4", "name": "\u82b1\u76c6", "category": "\u5bb9\u5668\u7c7b", "properties": {"size": {"length": 15, "width": 15, "height": 12}, "weight": 500, "material": "\u9676\u74f7"}, "initial_pose": {"region": "\u53f0\u9762\u4e2d\u90e8", "random": False}, "count": 2},
            {"object_id": "o5", "name": "\u82b1\u74f6", "category": "\u5bb9\u5668\u7c7b", "properties": {"size": {"length": 8, "width": 8, "height": 25}, "weight": 300, "material": "\u73bb\u7483"}, "initial_pose": {"region": "\u53f0\u9762\u53f3\u4fa7", "random": False}, "count": 1},
        ],
        "references": {
            "images": [{"url": "/static/scene_kitchen.jpg", "description": "\u53a8\u623f\u573a\u666f\u5168\u666f"}],
            "capture_videos": [{"url": "/static/capture_kitchen.mp4", "description": "\u73b0\u573a\u73af\u5883\u5b9e\u62cd", "duration": 30}],
            "demo_videos": [],
        },
    },
    {
        "id": "s3", "name": "\u6536\u7eb3\u67dc\u4f53\u573a\u666f", "description": "\u5305\u542b\u62bd\u5c49\u3001\u67dc\u95e8\u7684\u6536\u7eb3\u67dc\u4f53\uff0c\u7528\u4e8e\u5f00\u5408\u3001\u53d6\u653e\u3001\u642c\u79fb\u7c7b\u590d\u6742\u4efb\u52a1",
        "creator": "Rick Guo", "created_at": "2026-04-08",
        "environment": {
            "type": "\u5ba4\u5185-\u6536\u7eb3\u533a",
            "workspace": {"length": 80, "width": 50, "height": 180},
            "conditions": {"lighting": "\u81ea\u7136\u5149+\u8865\u5149\u706f (600lux)", "surface": "\u6728\u8d28\u67dc\u4f53"},
        },
        "objects": [
            {"object_id": "o6", "name": "\u6c34\u7334\u6446\u4ef6", "category": "\u5176\u4ed6", "properties": {"size": {"length": 8, "width": 6, "height": 10}, "weight": 120, "material": "\u6811\u8102"}, "initial_pose": {"region": "\u62bd\u5c49\u5185", "random": False}, "count": 1},
            {"object_id": "o7", "name": "\u4e66\u672c", "category": "\u5176\u4ed6", "properties": {"size": {"length": 21, "width": 15, "height": 2}, "weight": 300, "material": "\u7eb8\u8d28"}, "initial_pose": {"region": "\u9876\u5c42\u5de6\u683c", "random": False}, "count": 3},
        ],
        "references": {
            "images": [
                {"url": "/static/scene_cabinet1.jpg", "description": "\u67dc\u4f53\u6b63\u9762\u56fe"},
                {"url": "/static/scene_cabinet2.jpg", "description": "\u62bd\u5c49\u6253\u5f00\u72b6\u6001"},
            ],
            "capture_videos": [],
            "demo_videos": [{"url": "/static/demo_cabinet.mp4", "description": "\u62bd\u5c49\u53d6\u653e\u6f14\u793a", "duration": 60}],
        },
    },
]

# Status: 未开始 → 采集中 → 评测中 → 评测完成 → 分析完成 | 已暂停 | 已废弃
PRIORITY_MAP = {"\u9ad8": {"color": "", "label": "\u9ad8"}, "\u4e2d": {"color": "", "label": "\u4e2d"}, "\u4f4e": {"color": "", "label": "\u4f4e"}}

EVAL_TASKS = [
    {
        "id": "t1", "task_no": 1001, "name": "Spirit v1.5 vs v1.6-alpha \u57fa\u7840\u80fd\u529b\u6a2a\u6d4b",
        "benchmark_id": "b1", "eval_type": "preference",
        "model_ids": ["m1", "m2"],
        "status": "\u8bc4\u6d4b\u5b8c\u6210", "priority": "\u9ad8",
        "total_sessions": 30, "collect_done": 30, "eval_done": 30,
        "created_by": "Lance Li", "created_at": "2026-04-05",
    },
    {
        "id": "t2", "task_no": 1002, "name": "Spirit v1.6 \u5168\u7248\u672c\u7efc\u5408\u8bc4\u6d4b",
        "benchmark_id": "b4", "eval_type": "preference",
        "model_ids": ["m1", "m2", "m3", "m4"],
        "status": "\u8bc4\u6d4b\u4e2d", "priority": "\u9ad8",
        "total_sessions": 60, "collect_done": 60, "eval_done": 42,
        "created_by": "Lance Li", "created_at": "2026-04-08",
    },
    {
        "id": "t3", "task_no": 1003, "name": "Spirit v1.6-rc1 vs \u5916\u90e8\u57fa\u7ebf\u5bf9\u6807",
        "benchmark_id": "b3", "eval_type": "baseline",
        "model_ids": ["m4", "m5", "m6", "m7", "m8"],
        "status": "\u91c7\u96c6\u4e2d", "priority": "\u9ad8",
        "total_sessions": 80, "collect_done": 55, "eval_done": 0,
        "created_by": "Rick Guo", "created_at": "2026-04-10",
    },
    {
        "id": "t4", "task_no": 1004, "name": "\u5de5\u5177\u4f7f\u7528\u573a\u666f\u4e13\u9879\u6d4b\u8bd5",
        "benchmark_id": "b2", "eval_type": "pass_fail",
        "model_ids": ["m3", "m4", "m5"],
        "status": "\u672a\u5f00\u59cb", "priority": "\u4e2d",
        "total_sessions": 30, "collect_done": 0, "eval_done": 0,
        "created_by": "Lance Li", "created_at": "2026-04-12",
    },
    {
        "id": "t5", "task_no": 1005, "name": "Spirit v1.6-rc1 \u591a\u7ef4\u80fd\u529b\u91cf\u8868\u8bc4\u4f30",
        "benchmark_id": "b1", "eval_type": "scale",
        "model_ids": ["m3", "m4"],
        "status": "\u8bc4\u6d4b\u4e2d", "priority": "\u4f4e",
        "total_sessions": 40, "collect_done": 40, "eval_done": 18,
        "created_by": "Rick Guo", "created_at": "2026-04-14",
    },
]
# Backward compat: add completed_sessions alias
for _t in EVAL_TASKS:
    _t.setdefault("collect_done", 0)
    _t.setdefault("eval_done", 0)
    _t["completed_sessions"] = _t["eval_done"]


def _gen_mock_sessions():
    """Generate mock evaluation sessions for ranking."""
    random.seed(42)
    # True strength ordering (hidden): m4 > m5 > m3 > m6 > m2 > m7 > m8 > m1
    strength = {"m1": 0.0, "m2": 0.6, "m3": 1.2, "m4": 2.0, "m5": 1.6, "m6": 1.0, "m7": 0.4, "m8": 0.2}
    sessions = []
    all_models = list(strength.keys())

    for _ in range(200):
        a, b = random.sample(all_models, 2)
        sa, sb = strength[a], strength[b]
        diff = sa - sb
        p_a = 1 / (1 + math.exp(-diff))
        p_tie = 0.15
        r = random.random()
        if r < p_a * (1 - p_tie):
            outcome = 2  # A wins
        elif r < (1 - p_tie):
            outcome = 0  # B wins
        else:
            outcome = 1  # Tie

        # Generate per-step progress scores
        prompt = random.choice(PROMPTS)
        n_steps = len(prompt["low_levels"])
        prog_a = [min(1.0, max(0.0, 0.5 + sa / 4 + random.gauss(0, 0.2))) for _ in range(n_steps)]
        prog_b = [min(1.0, max(0.0, 0.5 + sb / 4 + random.gauss(0, 0.2))) for _ in range(n_steps)]

        explanations = [
            "Policy A 的抓取更精准，路径规划更合理",
            "Policy B 完成速度更快，但路径不够平滑",
            "两者表现接近，Policy A 在细节操作上略优",
            "Policy B 的异常恢复能力更好",
            "Policy A 完成了所有子任务，Policy B 在第三步失败",
            "两个策略都未能完成最后一步",
            "Policy A 动作更流畅，但最终结果相当",
            "Policy B 抓取成功率更高",
        ]

        sessions.append({
            "id": f"s{len(sessions)+1}",
            "policy_a": a,
            "policy_b": b,
            "preference": outcome,
            "progress_a": prog_a,
            "progress_b": prog_b,
            "overall_progress_a": round(sum(prog_a) / len(prog_a), 2),
            "overall_progress_b": round(sum(prog_b) / len(prog_b), 2),
            "explanation": random.choice(explanations),
            "prompt_id": prompt["id"],
            "evaluator": random.choice(["评测员A", "评测员B", "评测员C", "评测员D"]),
            "timestamp": (datetime(2026, 4, 5) + timedelta(hours=random.randint(0, 240))).isoformat(),
        })
    return sessions


EVAL_SESSIONS = _gen_mock_sessions()


# ════════════════════════════════════════════════════════════════
# Section 2: Bradley-Terry with Davidson Ties Algorithm
# ════════════════════════════════════════════════════════════════

def fit_bt_davidson(comparisons, policies, n_iter=3000, lr=0.05):
    """
    Bradley-Terry model with Davidson Ties extension.

    Args:
        comparisons: list of (policy_a, policy_b, outcome)
                     outcome: 2=A wins, 1=Tie, 0=B wins
        policies: list of policy ids
        n_iter: gradient ascent iterations
        lr: learning rate

    Returns:
        dict of {policy_id: {"score": float, "std": float, "wins": int, "losses": int, "ties": int, "matches": int}}
    """
    theta = {p: 0.0 for p in policies}
    log_nu = 0.0  # log(tie-tendency parameter)

    for iteration in range(n_iter):
        grad = {p: 0.0 for p in policies}
        grad_log_nu = 0.0
        nu = math.exp(log_nu)

        for pa, pb, outcome in comparisons:
            if pa not in theta or pb not in theta:
                continue
            ea = math.exp(theta[pa])
            eb = math.exp(theta[pb])
            em = math.exp((theta[pa] + theta[pb]) / 2)
            Z = ea + eb + 2 * nu * em

            da = (ea + nu * em) / Z
            db = (eb + nu * em) / Z
            dt = 2 * nu * em / Z

            if outcome == 2:  # A wins
                grad[pa] += 1 - da
                grad[pb] += -db
                grad_log_nu += -dt
            elif outcome == 0:  # B wins
                grad[pa] += -da
                grad[pb] += 1 - db
                grad_log_nu += -dt
            else:  # Tie
                grad[pa] += 0.5 - da
                grad[pb] += 0.5 - db
                grad_log_nu += 1 - dt

        # Adaptive learning rate decay
        current_lr = lr / (1 + iteration / 500)

        for p in policies:
            theta[p] += current_lr * grad[p]
        log_nu += current_lr * grad_log_nu

        # Center theta for identifiability
        mean_theta = sum(theta.values()) / len(theta)
        for p in policies:
            theta[p] -= mean_theta

    # Compute statistics
    SCALE, SHIFT = 200, 1500
    stats = {}
    for p in policies:
        wins = sum(1 for a, b, o in comparisons if (a == p and o == 2) or (b == p and o == 0))
        losses = sum(1 for a, b, o in comparisons if (a == p and o == 0) or (b == p and o == 2))
        ties = sum(1 for a, b, o in comparisons if (a == p or b == p) and o == 1)
        matches = wins + losses + ties

        # Approximate SD / SE (heuristic for demo)
        # SD: spread of per-match scores, roughly constant per model
        sd = SCALE * 1.5 + (hash(p) % 30) - 15
        # SE: standard error of mean = SD / sqrt(matches)
        se = sd / math.sqrt(max(matches, 1))

        stats[p] = {
            "score": round(theta[p] * SCALE + SHIFT, 1),
            "sd": round(sd, 1),
            "se": round(se, 1),
            "std": round(se, 1),  # backward compat
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "matches": matches,
        }

    return stats


_RANKINGS_CACHE = {"key": None, "value": None}

def compute_rankings():
    """Compute current rankings from all sessions (cached by session count)."""
    # Cache key = number of sessions; invalidates when new session added
    cache_key = len(EVAL_SESSIONS)
    if _RANKINGS_CACHE["key"] == cache_key and _RANKINGS_CACHE["value"] is not None:
        return _RANKINGS_CACHE["value"]

    comparisons = [(s["policy_a"], s["policy_b"], s["preference"]) for s in EVAL_SESSIONS]
    policies = list({m["id"] for m in MODELS})
    stats = fit_bt_davidson(comparisons, policies)

    # Sort by score descending
    ranked = sorted(stats.items(), key=lambda x: x[1]["score"], reverse=True)
    result = []
    for rank, (mid, st) in enumerate(ranked, 1):
        model = next((m for m in MODELS if m["id"] == mid), None)
        if model:
            result.append({
                "rank": rank,
                "model_id": mid,
                "model_name": model["name"],
                "version": model["version"],
                "arch": model["arch"],
                "status": model["status"],
                **st,
            })
    _RANKINGS_CACHE["key"] = cache_key
    _RANKINGS_CACHE["value"] = result
    return result


# ════════════════════════════════════════════════════════════════
# Section 3: HTML/CSS Templates
# ════════════════════════════════════════════════════════════════

BASE_CSS = """
/* ═══ Ant Design v4 Theme Overrides: primary=#1F80A0 ═══ */
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; }

/* ── Global border-radius ── */
.ant-btn, .ant-input, .ant-select-selector, .ant-card, .ant-tag,
.ant-alert, .ant-table-wrapper, .ant-pagination-item { border-radius: 8px !important; }
.ant-card-bordered { overflow: hidden; }
.ant-card .ant-table { border-radius: 0 !important; }
.ant-card-head { border-radius: 8px 8px 0 0 !important; }
.ant-btn-sm { border-radius: 6px !important; }
.ant-tag { border-radius: 4px !important; }

/* ── AntD primary color overrides ── */
.ant-btn-primary, .ant-btn-primary:focus { background: #1F80A0; border-color: #1F80A0; }
.ant-btn-primary:hover { background: #176a88; border-color: #176a88; }
a { color: #1F80A0; }
a:hover { color: #176a88; }
.ant-tag-green { color: #1F80A0; background: #e6f4f8; border-color: #8dcde0; }
.ant-tag-processing { color: #1F80A0; background: #e6f4f8; border-color: #8dcde0; }
.ant-pagination-item-active { border-color: #1F80A0; }
.ant-pagination-item-active a { color: #1F80A0; }
.ant-input:focus, .ant-input-focused, .ant-select-focused .ant-select-selector { border-color: #1F80A0 !important; box-shadow: 0 0 0 2px rgba(31,128,160,0.12) !important; }
.ant-switch-checked { background: #1F80A0; }
.ant-progress-bg { background: #1F80A0; }
.ant-breadcrumb a { color: #1F80A0; }
.ant-menu-dark .ant-menu-item-selected { background: #1F80A0 !important; }

/* ── Layout ── */
.q-layout { display: flex; min-height: 100vh; }
.q-sider { width: 220px; min-width: 220px; background: #001529; position: fixed; top: 0; left: 0; bottom: 0; z-index: 100; display: flex; flex-direction: column; overflow-y: auto; }
.q-sider .logo { height: 64px; display: flex; align-items: center; gap: 10px; padding: 0 16px; border-bottom: 1px solid rgba(255,255,255,0.08); }
.q-sider .logo-icon { width: 36px; height: 36px; background: linear-gradient(135deg, #1F80A0, #36cfc9); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 700; color: #fff; }
.q-sider .logo-text { font-size: 15px; font-weight: 600; color: rgba(255,255,255,0.9); }
.q-sider .nav-section { padding: 8px 0; flex: 1; }
.q-sider .nav-label { padding: 12px 24px 4px; font-size: 11px; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
.q-sider .nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 24px; color: rgba(255,255,255,0.65); font-size: 14px; text-decoration: none; transition: all 0.2s; margin: 2px 8px; border-radius: 6px; }
.q-sider .nav-item:hover { color: #fff; background: rgba(255,255,255,0.06); }
.q-sider .nav-item.active { color: #fff; background: #1F80A0; }
.q-sider .nav-item .icon { width: 16px; text-align: center; }
.q-sider .user-block { padding: 12px 16px; border-top: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; gap: 10px; }
.q-sider .user-avatar { width: 32px; height: 32px; border-radius: 50%; background: #1F80A0; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; }
.q-sider .user-name { color: rgba(255,255,255,0.85); font-size: 13px; font-weight: 500; }
.q-sider .user-role { color: rgba(255,255,255,0.35); font-size: 11px; }

.q-main { margin-left: 220px; flex: 1; background: #f0f2f5; min-height: 100vh; }
.q-header { background: #fff; padding: 0 24px; height: 48px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #f0f0f0; position: sticky; top: 0; z-index: 50; }
.q-content { padding: 24px; }

/* ── Stat cards (AntD Statistic style) ── */
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
.stat-card { background: #fff; border-radius: 8px; padding: 20px 24px; border: 1px solid #f0f0f0; }
.stat-card .stat-label { font-size: 14px; color: rgba(0,0,0,0.45); margin-bottom: 4px; }
.stat-card .stat-value { font-size: 30px; font-weight: 600; color: rgba(0,0,0,0.85); }
.stat-card .stat-sub { font-size: 12px; color: rgba(0,0,0,0.45); margin-top: 4px; }

/* ── Filter bar ── */
.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }

/* ── Form layout ── */
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 14px; color: rgba(0,0,0,0.85); margin-bottom: 4px; }
.form-group label.req::before { content: '* '; color: #ff4d4f; margin-right: 2px; }
.form-group input[type="text"], .form-group input[type="number"], .form-group input[type="date"], .form-group input[type="time"], .form-group input[type="datetime-local"], .form-group input[type="email"], .form-group input[type="password"], .form-group input[type="url"], .form-group select, .form-group textarea,
.filter-bar input, .filter-bar select { padding: 5px 12px; height: 36px; border: 1px solid #d9d9d9; border-radius: 8px; font-size: 14px; color: rgba(0,0,0,0.85); outline: none; transition: all 0.3s; font-family: inherit; box-sizing: border-box; -webkit-appearance: none; appearance: none; background: #fff; }
.form-group select, .filter-bar select { padding-right: 32px; background: #fff url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%23595959' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") no-repeat right 12px center; }
/* Date/time inputs — enable full-field click to open picker */
.form-group input[type="date"], .form-group input[type="time"], .form-group input[type="datetime-local"] { -webkit-appearance: auto; appearance: auto; cursor: pointer; }
.form-group input[type="date"]::-webkit-calendar-picker-indicator { cursor: pointer; opacity: 0.55; }
.form-group input[type="date"]::-webkit-calendar-picker-indicator:hover { opacity: 1; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus,
.filter-bar input:focus, .filter-bar select:focus { border-color: #1F80A0; box-shadow: 0 0 0 2px rgba(31,128,160,0.12); }
.filter-bar select, .form-group select { color: rgba(0,0,0,0.25); }
.filter-bar select.has-value, .form-group select.has-value { color: rgba(0,0,0,0.85); }
.filter-bar select option, .form-group select option { color: rgba(0,0,0,0.85); }
.filter-bar select option[value=""], .form-group select option[value=""] { color: rgba(0,0,0,0.25); }
.form-group input[type="text"], .form-group input[type="number"], .form-group input[type="date"], .form-group input[type="time"], .form-group input[type="datetime-local"], .form-group input[type="email"], .form-group input[type="password"], .form-group input[type="url"] { width: 100%; }
.form-group textarea { width: 100%; height: auto; min-height: 80px; }
.form-group select { width: 100%; }
.form-group select[multiple] { height: auto; min-height: 80px; padding-right: 12px; background-image: none; }
.form-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }

/* ── AntD table enhancements ── */
.ant-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.ant-table thead th { background: #fafafa; padding: 8px 16px; font-weight: 500; color: rgba(0,0,0,0.85); text-align: left; border-bottom: 1px solid #f0f0f0; font-size: 14px; white-space: nowrap; }
.ant-table tbody td { padding: 8px 16px; border-bottom: 1px solid #f0f0f0; color: rgba(0,0,0,0.65); vertical-align: middle; }
.ant-table tbody tr:hover td { background: #fafafa; }
.actions-cell { white-space: nowrap; }
.actions-cell a, .actions-cell button { vertical-align: middle; margin-right: 4px; }

/* ── Progress bar (custom) ── */
.progress-bar { height: 6px; background: #f5f5f5; border-radius: 100px; overflow: hidden; }
.progress-bar-fill { height: 100%; border-radius: 100px; transition: width 0.3s; }
.progress-bar-fill.green { background: #1F80A0; }
.progress-bar-fill.blue { background: #1890ff; }
.progress-bar-fill.yellow { background: #faad14; }

/* Progress bar label with auto-contrast: white over filled area, dark over unfilled */
.pb-text {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 500;
  background: linear-gradient(to right, #fff 0%, #fff var(--pct, 0%), rgba(0,0,0,0.75) var(--pct, 0%), rgba(0,0,0,0.75) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  pointer-events: none;
}

/* ── Evaluation Workbench ── */
.eval-header { background: linear-gradient(135deg, #001529 0%, #003a5c 100%); color: #fff; padding: 20px 24px; border-radius: 8px; margin-bottom: 20px; }
.eval-header h2 { font-size: 18px; margin-bottom: 6px; }
.eval-header .meta { font-size: 13px; color: rgba(255,255,255,0.55); display: flex; gap: 20px; }
.video-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.video-panel { border-radius: 8px; border: 2px solid #f0f0f0; overflow: hidden; background: #fff; }
.video-panel.panel-a { border-color: #1890ff; }
.video-panel.panel-b { border-color: #faad14; }
.video-panel .panel-header { padding: 8px 16px; display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 14px; }
.panel-a .panel-header { background: #e6f7ff; color: #1890ff; }
.panel-b .panel-header { background: #fffbe6; color: #ad6800; }
.video-placeholder { background: #141414; height: 180px; display: flex; align-items: center; justify-content: center; color: rgba(255,255,255,0.35); flex-direction: column; gap: 6px; }
.camera-row { display: grid; grid-template-columns: 1fr 1fr 1fr; }
.camera-cell { position: relative; }
.camera-cell .cam-label { position: absolute; top: 6px; left: 6px; background: rgba(0,0,0,0.65); color: #fff; padding: 1px 6px; border-radius: 4px; font-size: 11px; }
.camera-cell .cam-status { position: absolute; top: 6px; right: 6px; font-size: 11px; color: #52c41a; display: flex; align-items: center; gap: 4px; }
.camera-cell .cam-status::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: #52c41a; }

/* ── Scoring ── */
.scoring-section { background: #fff; border-radius: 8px; border: 1px solid #f0f0f0; padding: 20px 24px; margin-bottom: 16px; }
.scoring-section h3 { font-size: 16px; font-weight: 500; margin-bottom: 16px; color: rgba(0,0,0,0.85); }
.step-scoring { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 8px; padding: 12px; background: #fafafa; border: 1px solid #f0f0f0; border-radius: 8px; }
.step-scoring .step-label { grid-column: 1/-1; font-size: 13px; font-weight: 500; color: rgba(0,0,0,0.65); margin-bottom: 4px; }
.score-input { display: flex; align-items: center; gap: 8px; }
.score-input label { font-size: 12px; color: rgba(0,0,0,0.45); min-width: 60px; }
.score-input input[type="range"] { flex: 1; accent-color: #1F80A0; }
.score-input .score-val { font-size: 14px; font-weight: 600; min-width: 36px; text-align: center; color: rgba(0,0,0,0.85); }
.preference-group { display: flex; gap: 12px; margin: 16px 0; }
.pref-btn { flex: 1; padding: 16px; border: 1px solid #d9d9d9; border-radius: 8px; background: #fff; cursor: pointer; text-align: center; font-size: 14px; font-weight: 500; transition: all 0.2s; }
.pref-btn:hover { border-color: #1F80A0; color: #1F80A0; }
.pref-btn.selected-a { border-color: #1890ff; background: #e6f7ff; color: #1890ff; }
.pref-btn.selected-tie { border-color: #722ed1; background: #f9f0ff; color: #722ed1; }
.pref-btn.selected-b { border-color: #faad14; background: #fffbe6; color: #ad6800; }

/* ── Leaderboard ── */
.rank-badge { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; font-size: 13px; font-weight: 700; }
.rank-1 { background: #1F80A0; color: #fff; }
.rank-2 { background: #4ea6c4; color: #fff; }
.rank-3 { background: #8dcde0; color: #fff; }
.rank-other { background: #f5f5f5; color: #8c8c8c; }
.score-bar { height: 6px; border-radius: 3px; background: #f0f0f0; position: relative; width: 120px; display: inline-block; vertical-align: middle; margin-left: 8px; }
.score-bar-fill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 3px; background: linear-gradient(90deg, #1F80A0, #36cfc9); }
.score-text { font-weight: 600; font-size: 16px; color: rgba(0,0,0,0.85); }
.std-text { font-size: 12px; color: rgba(0,0,0,0.35); }

/* ── Charts ── */
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
.chart-card { background: #fff; border-radius: 8px; border: 1px solid #f0f0f0; padding: 20px; }
.chart-card h4 { font-size: 14px; font-weight: 500; color: rgba(0,0,0,0.85); margin-bottom: 16px; }
@media (max-width: 1200px) { .chart-grid { grid-template-columns: 1fr; } }

/* ── H2H matrix ── */
.h2h-cell { padding: 6px 8px; text-align: center; font-size: 12px; border-radius: 4px; }
.h2h-win { background: #f6ffed; color: #389e0d; }
.h2h-loss { background: #fff2f0; color: #cf1322; }
.h2h-tie { background: #fffbe6; color: #d48806; }
.h2h-self { background: #fafafa; color: #bfbfbf; }

/* ── Expandable rows ── */
.expand-btn { background: none; border: none; cursor: pointer; font-size: 12px; color: rgba(0,0,0,0.25); transition: transform 0.2s; padding: 2px 6px; }
.expand-btn.expanded { transform: rotate(90deg); }
.sub-row { display: none; }
.sub-row.visible { display: table-row; }

/* ── Prompt table ── */
.row-parent td { color: rgba(0,0,0,0.85); }
.row-child td { font-size: 13px; background: #fafafa; }
.row-child:hover td { background: #e6f4f8; }
.row-new-parent td { background: none; vertical-align: middle; padding-top: 8px; padding-bottom: 8px; }

/* ── Drawer ── */
.ant-drawer-mask { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.45); z-index: 200; }
.ant-drawer-mask.active { display: block; }
.ant-drawer-content { background: #fff; position: fixed; top: 0; right: 0; bottom: 0; width: calc(100vw - 220px); height: 100vh; transform: translateX(100%); transition: transform 0.3s cubic-bezier(0.23, 1, 0.32, 1); box-shadow: -6px 0 16px rgba(0,0,0,0.08); display: flex; flex-direction: column; }
.ant-drawer-mask.active .ant-drawer-content { transform: translateX(0); }
.ant-drawer-header { padding: 16px 24px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; }
.ant-drawer-header h3 { font-size: 16px; font-weight: 500; color: rgba(0,0,0,0.85); margin: 0; }
.ant-drawer-close { background: none; border: none; font-size: 16px; cursor: pointer; color: rgba(0,0,0,0.45); padding: 4px 8px; }
.ant-drawer-close:hover { color: rgba(0,0,0,0.85); }
.ant-drawer-body { padding: 24px; flex: 1; overflow-y: auto; }
.ant-drawer-footer { padding: 10px 24px; border-top: 1px solid #f0f0f0; display: flex; justify-content: flex-end; gap: 8px; }

/* ── Action icons (bare, no border) ── */
.act-icon { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; cursor: pointer; transition: all 0.2s; text-decoration: none; background: none; border: none; padding: 0; }
.act-icon svg { width: 18px; height: 18px; }
.act-icon.act-primary svg { stroke: #1F80A0; }
.act-icon.act-primary:hover svg { stroke: #176a88; }
.act-icon.act-default svg { stroke: #8c8c8c; }
.act-icon.act-default:hover svg { stroke: #1F80A0; }
.act-icon.act-danger svg { stroke: #ff4d4f; }
.act-icon.act-danger:hover svg { stroke: #cf1322; }

/* ── TreeSelect ── */
.ts-wrap { position: relative; display: inline-block; width: 100%; }
.ts-trigger { width: 100%; min-height: 36px; padding: 3px 32px 3px 4px; border: 1px solid #d9d9d9; border-radius: 8px; cursor: pointer; display: flex; flex-wrap: wrap; gap: 3px; align-items: center; background: #fff; box-sizing: border-box; font-size: 14px; position: relative; }
.ts-trigger::after { content: ''; position: absolute; right: 10px; top: 50%; width: 0; height: 0; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid #bfbfbf; transform: translateY(-50%); transition: transform 0.2s; }
.ts-wrap.open .ts-trigger::after { transform: translateY(-50%) rotate(180deg); }
.ts-trigger:hover { border-color: #1F80A0; }
.ts-trigger .ts-placeholder { color: rgba(0,0,0,0.25); padding: 0 7px; line-height: 28px; }
.ts-chip { display: inline-flex; align-items: center; gap: 4px; background: #f5f5f5; border: 1px solid #f0f0f0; border-radius: 4px; padding: 0 4px 0 8px; font-size: 12px; color: rgba(0,0,0,0.65); line-height: 24px; max-width: 180px; }
.ts-chip-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ts-chip-close { cursor: pointer; color: rgba(0,0,0,0.35); font-size: 10px; padding: 0 2px; border-radius: 2px; }
.ts-chip-close:hover { color: rgba(0,0,0,0.85); background: rgba(0,0,0,0.06); }
.ts-panel { display: none; position: absolute; top: 100%; left: 0; min-width: 100%; width: max-content; max-width: 420px; z-index: 999; background: #fff; border: 1px solid #d9d9d9; border-radius: 8px; box-shadow: 0 6px 16px rgba(0,0,0,0.08); margin-top: 4px; max-height: 320px; overflow-y: auto; padding: 4px 0; }
.ts-wrap.open .ts-panel { display: block; }
.ts-node { padding: 0; }
.ts-row { display: flex; align-items: center; padding: 5px 12px; cursor: pointer; font-size: 14px; color: rgba(0,0,0,0.85); transition: background 0.15s; white-space: nowrap; }
.ts-row:hover { background: #f5f5f5; }
.ts-row.selected { background: #e6f4f8; color: #1F80A0; }
.ts-arrow { width: 16px; height: 16px; display: inline-flex; align-items: center; justify-content: center; margin-right: 4px; font-size: 10px; color: rgba(0,0,0,0.35); transition: transform 0.2s; cursor: pointer; flex-shrink: 0; }
.ts-arrow.expanded { transform: rotate(90deg); }
.ts-arrow.empty { visibility: hidden; }
.ts-children { display: none; padding-left: 20px; }
.ts-children.expanded { display: block; }

/* ── Tooltip (JS-powered, appended to body) ── */
.q-tooltip { position: fixed; z-index: 9999; background: rgba(0,0,0,0.78); color: #fff; padding: 8px 12px; border-radius: 8px; font-size: 13px; line-height: 1.5; max-width: 380px; word-break: break-word; pointer-events: none; box-shadow: 0 4px 12px rgba(0,0,0,0.15); white-space: normal; }
.q-tooltip::after { content: ''; position: absolute; top: 100%; left: 20px; border: 6px solid transparent; border-top-color: rgba(0,0,0,0.78); }

/* ── Placeholder ── */
::placeholder { color: rgba(0,0,0,0.2); }
::-webkit-input-placeholder { color: rgba(0,0,0,0.2); }

/* ── Input with clear button ── */
.input-clear-wrap { position:relative; display:flex; align-items:center; }
.input-clear-wrap input { width:100%; padding-right:28px; }
.input-clear { position:absolute; right:8px; top:50%; transform:translateY(-50%); cursor:pointer; color:rgba(0,0,0,0.25); font-size:14px; line-height:1; width:16px; height:16px; display:flex; align-items:center; justify-content:center; border-radius:50%; }
.input-clear:hover { color:rgba(0,0,0,0.45); background:rgba(0,0,0,0.04); }

/* ── Toast ── */
.q-toast { position:fixed; top:24px; left:50%; transform:translate(-50%,-12px); min-width:260px; max-width:420px; background:#fff; color:rgba(0,0,0,0.85); padding:12px 20px; padding-left:16px; border-radius:10px; font-size:14px; line-height:1.5; z-index:9999; pointer-events:none; opacity:0; box-shadow:0 6px 24px rgba(0,0,0,0.12), 0 3px 6px -4px rgba(0,0,0,0.08), 0 9px 28px 8px rgba(0,0,0,0.04); border:1px solid #f0f0f0; display:flex; align-items:center; gap:10px; transition:opacity 0.25s ease, transform 0.25s ease; }
.q-toast.show { opacity:1; transform:translate(-50%,0); }
.q-toast::before { content:''; width:18px; height:18px; border-radius:50%; flex-shrink:0; display:inline-flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; color:#fff; line-height:1; }
.q-toast.q-toast-info { border-left:4px solid #1F80A0; padding-left:14px; }
.q-toast.q-toast-info::before { background:#1F80A0; content:'i'; font-family:Georgia,serif; }
.q-toast.q-toast-success { border-left:4px solid #52c41a; padding-left:14px; }
.q-toast.q-toast-success::before { background:#52c41a; content:'\2713'; }
.q-toast.q-toast-warning { border-left:4px solid #faad14; padding-left:14px; }
.q-toast.q-toast-warning::before { background:#faad14; content:'!'; }
.q-toast.q-toast-error { border-left:4px solid #ff4d4f; padding-left:14px; }
.q-toast.q-toast-error::before { background:#ff4d4f; content:'\2715'; }

/* ── Media gallery (images & videos) ── */
.media-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.media-card { width: 140px; border: 1px solid #f0f0f0; border-radius: 8px; background: #fff; overflow: hidden; cursor: pointer; transition: all 0.15s; }
.media-card:hover { border-color: #1F80A0; box-shadow: 0 2px 8px rgba(31,128,160,0.15); transform: translateY(-1px); }
.media-thumb { height: 80px; background: #e6f4f8; display: flex; align-items: center; justify-content: center; }
.media-thumb-video { background: #1a1a2e; }
.media-desc { padding: 6px 10px; font-size: 12px; color: rgba(0,0,0,0.65); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; border-top: 1px solid #f5f5f5; }

/* ── Upload zone (shared between /scenes and /tasks) ── */
.upload-zone { border: 1px dashed #d9d9d9; border-radius: 8px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.2s; background: #fafafa; }
.upload-zone:hover { border-color: #1F80A0; background: #f0f9fb; }
.upload-icon { margin-bottom: 8px; }
.upload-text { font-size: 14px; color: rgba(0,0,0,0.65); }
.upload-hint { font-size: 12px; color: rgba(0,0,0,0.35); margin-top: 4px; }
.upload-files { margin-top: 8px; text-align: left; }
.upload-file-item { display: flex; align-items: center; gap: 6px; padding: 4px 8px; background: #fff; border: 1px solid #f0f0f0; border-radius: 6px; margin-top: 4px; font-size: 12px; color: rgba(0,0,0,0.65); }
.upload-file-item .file-icon { color: #1F80A0; }
.upload-file-item .file-size { color: rgba(0,0,0,0.35); margin-left: auto; }

/* ── Multi-select dropdown with chips (used on /eval-records and /analysis) ── */
.er-dd-trigger { display:flex; align-items:center; width:100%; min-height:36px; padding:4px 10px; border:1px solid #d9d9d9; border-radius:8px; background:#fff; cursor:pointer; transition:all 0.2s; box-sizing:border-box; }
.er-dd-trigger:hover { border-color:#1F80A0; }
.er-chips { display:flex; flex-wrap:wrap; gap:4px; flex:1; min-width:0; align-items:center; }
.er-chip { display:inline-flex; align-items:center; gap:4px; padding:2px 8px; background:#f5f5f5; border-radius:4px; font-size:13px; color:rgba(0,0,0,0.85); max-width:240px; line-height:1.6; }
.er-chip-text { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:200px; }
.er-chip-x { cursor:pointer; color:rgba(0,0,0,0.35); font-size:14px; line-height:1; padding:0 2px; border-radius:2px; flex-shrink:0; }
.er-chip-x:hover { color:rgba(0,0,0,0.65); background:rgba(0,0,0,0.04); }
.er-dd-panel { display:none; position:absolute; top:calc(100% + 4px); left:0; min-width:320px; background:#fff; border:1px solid #f0f0f0; border-radius:8px; box-shadow:0 6px 16px rgba(0,0,0,0.08); z-index:100; }
.er-dd-panel.open { display:block; }
.er-opt { display:flex; align-items:center; gap:8px; padding:6px 14px; font-size:13px; cursor:pointer; color:rgba(0,0,0,0.85); }
.er-opt:hover { background:#fafafa; }
.er-opt input { accent-color:#1F80A0; }
.er-pg-btn { min-width:28px; height:28px; padding:0 8px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; font-size:13px; cursor:pointer; color:rgba(0,0,0,0.65); transition:all 0.2s; }
.er-pg-btn:hover:not(:disabled) { border-color:#1F80A0; color:#1F80A0; }
.er-pg-btn.active { background:#1F80A0; border-color:#1F80A0; color:#fff; }
.er-pg-btn:disabled { opacity:0.4; cursor:not-allowed; }

/* ── Capsule Switch ── */
.capsule { display:inline-block; width:36px; height:20px; border-radius:10px; background:#d9d9d9; position:relative; cursor:pointer; transition:background 0.25s; vertical-align:middle; border:1px solid rgba(0,0,0,0.06); }
.capsule.on { background: #1F80A0; border-color: #1F80A0; }
.capsule-dot { position:absolute; top:2px; left:2px; width:14px; height:14px; border-radius:50%; background:#fff; transition:left 0.25s; box-shadow:0 1px 3px rgba(0,0,0,0.2); }
.capsule.on .capsule-dot { left:18px; }

/* ── Difficulty ── */
.difficulty { color: #faad14; letter-spacing: 1px; font-size: 13px; }

/* ── Status dot ── */
.status { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; }
.status::before { content: ''; width: 6px; height: 6px; border-radius: 50%; }
.status-active::before { background: #52c41a; }
.status-pending::before { background: #faad14; }
.status-done::before { background: #d9d9d9; }
"""

BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} - Quanta 评测平台</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/antd@4.24.16/dist/antd.min.css">
<style>""" + BASE_CSS + """</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
<div class="q-layout">
<aside class="q-sider">
  <div class="logo">
    <div class="logo-icon">Q</div>
    <div class="logo-text">Quanta 评测平台</div>
  </div>
  <nav class="nav-section">
    <div class="nav-label">\u8bc4\u6d4b\u7ba1\u7406</div>
    <a href="/tasks" class="nav-item {{ 'active' if active=='tasks' }}"><span class="icon">&#9881;</span> \u8bc4\u6d4b\u4efb\u52a1\u7ba1\u7406</a>
    <a href="/collections" class="nav-item {{ 'active' if active=='collections' }}"><span class="icon">&#9783;</span> \u8bc4\u6d4b\u91c7\u96c6\u7ba1\u7406</a>
    <a href="/eval-records" class="nav-item {{ 'active' if active=='eval_records' }}"><span class="icon">&#9776;</span> \u8bc4\u6d4b\u7ed3\u679c\u8bb0\u5f55</a>
    <div class="nav-label">\u8bc4\u6d4b\u6267\u884c</div>
    <a href="/collect" class="nav-item {{ 'active' if active=='collect' }}"><span class="icon">&#9783;</span> \u8bc4\u6d4b\u6570\u636e\u91c7\u96c6</a>
    <a href="/evaluate2" class="nav-item {{ 'active' if active=='evaluate2' }}"><span class="icon">&#9878;</span> \u8bc4\u6d4b\u5de5\u4f5c\u53f0</a>
    <div class="nav-label">\u6570\u636e\u770b\u677f</div>
    <a href="/leaderboard" class="nav-item {{ 'active' if active=='leaderboard' }}"><span class="icon">&#9733;</span> \u6392\u884c\u699c</a>
    <a href="/analysis" class="nav-item {{ 'active' if active=='analysis' }}"><span class="icon">&#9636;</span> \u591a\u7ef4\u5206\u6790</a>
    <div class="nav-label">\u914d\u7f6e\u7ba1\u7406</div>
    <a href="/benchmarks" class="nav-item {{ 'active' if active=='benchmarks' }}"><span class="icon">&#9776;</span> Benchmark \u7ba1\u7406</a>
    <a href="/prompts" class="nav-item {{ 'active' if active=='prompts' }}"><span class="icon">&#9998;</span> \u63d0\u793a\u8bcd\u7ba1\u7406</a>
    <a href="/criteria" class="nav-item {{ 'active' if active=='criteria' }}"><span class="icon">&#9745;</span> \u8bc4\u4ef7\u6807\u51c6\u7ba1\u7406</a>
    <a href="/tags" class="nav-item {{ 'active' if active=='tags' }}"><span class="icon">&#9873;</span> \u6807\u7b7e\u7ba1\u7406</a>
  </nav>
  <div class="user-block">
    <div class="user-avatar">JQ</div>
    <div><div class="user-name">Joanna Qiao</div><div class="user-role">产品经理</div></div>
  </div>
</aside>
<div class="q-main">
  <div class="q-header">
    <span class="ant-breadcrumb">
      {% if breadcrumb %}
        {{ breadcrumb|safe }}
      {% else %}
        <span class="ant-breadcrumb-link"><a href="{% if active in ('tasks','collections') %}/tasks{% elif active in ('collect','evaluate','evaluate2') %}/evaluate{% elif active in ('leaderboard','analysis') %}/leaderboard{% else %}/benchmarks{% endif %}">{% if active in ('tasks','collections') %}\u8bc4\u6d4b\u7ba1\u7406{% elif active in ('collect','evaluate','evaluate2') %}\u8bc4\u6d4b\u6267\u884c{% elif active in ('leaderboard','analysis') %}\u6570\u636e\u770b\u677f{% else %}\u914d\u7f6e\u7ba1\u7406{% endif %}</a></span>
        <span class="ant-breadcrumb-separator">/</span>
        <span class="ant-breadcrumb-link">{{ title|safe }}</span>
      {% endif %}
    </span>
  </div>
  <div class="q-content">
    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for cat, msg in messages %}
      <div class="ant-alert ant-alert-{{ cat }} ant-alert-no-icon" style="margin-bottom:16px;"><div class="ant-alert-message">{{ msg }}</div></div>
      {% endfor %}
    {% endif %}
    {% endwith %}
    {{ content|safe }}
  </div>

  <!-- Global media viewer modal -->
  <div class="ant-drawer-mask" id="q-media-viewer">
    <div class="ant-drawer-content" style="width:720px;max-width:90vw;">
      <div class="ant-drawer-header">
        <h3 id="q-media-title">\u9884\u89c8</h3>
        <button class="ant-drawer-close" onclick="closeModal('q-media-viewer')">&times;</button>
      </div>
      <div class="ant-drawer-body" id="q-media-body" style="display:flex;align-items:center;justify-content:center;min-height:320px;background:#fafafa;"></div>
    </div>
  </div>
</div>
</div>
<script>
document.querySelectorAll('.expand-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.classList.toggle('expanded');
    document.querySelectorAll('.' + btn.dataset.target).forEach(r => r.classList.toggle('visible'));
  });
});
document.querySelectorAll('.pref-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.pref-btn').forEach(b => b.className = 'pref-btn');
    const v = btn.dataset.value;
    btn.classList.add(v==='2'?'selected-a':v==='1'?'selected-tie':'selected-b');
    const inp = document.getElementById('preference-input');
    if (inp) inp.value = v;
  });
});
document.querySelectorAll('input[type="range"]').forEach(s => {
  const d = document.getElementById(s.id+'-val');
  if (d) s.addEventListener('input', () => { d.textContent = Math.round(s.value); });
});
function openModal(id) { const e=document.getElementById(id); e.style.display='block'; requestAnimationFrame(()=>e.classList.add('active')); }
function closeModal(id) { const e=document.getElementById(id); e.classList.remove('active'); setTimeout(()=>{e.style.display='none';},300); }
document.querySelectorAll('.ant-drawer-mask').forEach(m => { m.addEventListener('click',(e)=>{ if(e.target===m) closeModal(m.id); }); });

// Click anywhere on a date/time input opens its native picker (Chrome/Edge/Safari)
document.addEventListener('click', function(e) {
  var el = e.target;
  if (el && el.matches && el.matches('input[type="date"], input[type="time"], input[type="datetime-local"]')) {
    if (typeof el.showPicker === 'function') {
      try { el.showPicker(); } catch (err) { /* ignore */ }
    }
  }
});

// Global media viewer — shows image/video placeholder in a modal
window.openMediaViewer = function(kind, idx, desc, url) {
  var body = document.getElementById('q-media-body');
  var title = document.getElementById('q-media-title');
  if (!body || !title) return;
  title.textContent = (kind === 'video' ? '视频预览' : '图片预览') + (desc ? ' — ' + desc : '');
  if (kind === 'video') {
    body.innerHTML = ''
      + '<div style="width:100%;max-width:640px;aspect-ratio:16/9;background:#1a1a2e;border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:rgba(255,255,255,0.85);gap:12px;">'
      + '<svg width="56" height="56" viewBox="0 0 24 24" fill="rgba(255,255,255,0.85)"><polygon points="6 4 20 12 6 20"/></svg>'
      + '<div style="font-size:14px;">' + (desc || '视频占位') + '</div>'
      + '<div style="font-size:12px;color:rgba(255,255,255,0.45);">' + (url || '—') + '</div>'
      + '</div>';
  } else {
    body.innerHTML = ''
      + '<div style="width:100%;max-width:640px;aspect-ratio:16/9;background:linear-gradient(135deg,#e6f4f8,#c7e5ee);border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#1F80A0;gap:12px;">'
      + '<svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#1F80A0" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>'
      + '<div style="font-size:14px;font-weight:500;">' + (desc || '图片占位') + '</div>'
      + '<div style="font-size:12px;color:rgba(0,0,0,0.45);">' + (url || '—') + '</div>'
      + '</div>';
  }
  openModal('q-media-viewer');
};

// Global upload-zone: show file names + drag-drop
window.showFileNames = function(input) {
  var container = input.closest('.upload-zone').querySelector('.upload-files');
  container.innerHTML = '';
  Array.from(input.files).forEach(function(f) {
    var size = f.size < 1048576 ? (f.size/1024).toFixed(0)+'KB' : (f.size/1048576).toFixed(1)+'MB';
    var isImg = (f.type || '').startsWith('image/');
    var icon = isImg ? '[IMG]' : '[VID]';
    container.innerHTML += '<div class="upload-file-item"><span class="file-icon">'+icon+'</span><span>'+f.name+'</span><span class="file-size">'+size+'</span></div>';
  });
};
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.upload-zone').forEach(function(zone) {
    if (zone.dataset.dnd === '1') return;
    zone.dataset.dnd = '1';
    zone.addEventListener('dragover', function(e) { e.preventDefault(); this.style.borderColor='#1F80A0'; this.style.background='#e6f4f8'; });
    zone.addEventListener('dragleave', function() { this.style.borderColor=''; this.style.background=''; });
    zone.addEventListener('drop', function(e) {
      e.preventDefault(); this.style.borderColor=''; this.style.background='';
      var input = this.querySelector('input[type="file"]');
      input.files = e.dataTransfer.files;
      window.showFileNames(input);
    });
  });
});

// ── Reusable multi-select dropdown with chips ──
// HTML pattern:
//   <div id="XXX-btn" class="er-dd-trigger" onclick="mselToggle('XXX', event)">
//     <div id="XXX-chips" class="er-chips"></div>
//     <span>▼</span>
//   </div>
//   <div id="XXX-panel" class="er-dd-panel"><label class="er-opt"><input type="checkbox" value="..." data-name="..." onchange="mselSync('XXX')"> ...</label>...</div>
//   <input type="hidden" id="XXX-hidden" name="...">
window.mselToggle = function(id, evt) {
  if (evt) evt.stopPropagation();
  document.getElementById(id + '-panel').classList.toggle('open');
};
window.mselToggleAll = function(id, checked) {
  document.querySelectorAll('#' + id + '-panel input[type=checkbox]').forEach(function(cb) { cb.checked = checked; });
  window.mselSync(id);
};
window.mselSync = function(id) {
  var panel = document.getElementById(id + '-panel');
  if (!panel) return;
  var cbs = panel.querySelectorAll('input[type=checkbox]');
  var checked = Array.prototype.filter.call(cbs, function(cb) { return cb.checked; });
  var box = document.getElementById(id + '-chips');
  var hidden = document.getElementById(id + '-hidden');
  box.innerHTML = '';
  if (checked.length === 0) {
    var p = document.createElement('span');
    p.style.color = 'rgba(0,0,0,0.35)';
    p.style.fontSize = '14px';
    p.textContent = '请选择';
    box.appendChild(p);
  } else {
    checked.forEach(function(cb) {
      var name = cb.getAttribute('data-name') || cb.value;
      var chip = document.createElement('span');
      chip.className = 'er-chip';
      chip.innerHTML = '<span class="er-chip-text">' + name + '</span><span class="er-chip-x" data-val="' + cb.value + '" data-msid="' + id + '">\u00d7</span>';
      box.appendChild(chip);
    });
    box.querySelectorAll('.er-chip-x').forEach(function(x) {
      x.addEventListener('click', function(e) {
        e.stopPropagation();
        var tg = document.querySelector('#' + x.dataset.msid + '-panel input[value="' + x.dataset.val + '"]');
        if (tg) tg.checked = false;
        window.mselSync(x.dataset.msid);
      });
    });
  }
  if (hidden) hidden.value = checked.map(function(cb) { return cb.value; }).join(',');
};
// Close dropdowns when clicking outside, and initialize chip display on load
document.addEventListener('click', function(e) {
  document.querySelectorAll('.er-dd-panel.open').forEach(function(panel) {
    var btn = document.getElementById(panel.id.replace('-panel', '-btn'));
    if (btn && !btn.contains(e.target) && !panel.contains(e.target)) {
      panel.classList.remove('open');
    }
  });
});
document.addEventListener('DOMContentLoaded', function() {
  // Initialize chip display only for panels that pair with a hidden input (mselSync pattern)
  document.querySelectorAll('.er-dd-panel[id$="-panel"]').forEach(function(panel) {
    var id = panel.id.replace('-panel', '');
    if (document.getElementById(id + '-chips') && document.getElementById(id + '-hidden')) {
      window.mselSync(id);
    }
  });
});

// Global toast helper
window.showToast = function(msg, type) {
  type = type || 'info';
  var t = document.createElement('div');
  t.className = 'q-toast q-toast-' + type;
  t.textContent = msg;
  document.body.appendChild(t);
  requestAnimationFrame(function(){ t.classList.add('show'); });
  setTimeout(function(){
    t.classList.remove('show');
    setTimeout(function(){ t.remove(); }, 300);
  }, 2800);
};

// Toast from URL param
(function(){
  var p = new URLSearchParams(window.location.search);
  var msg = p.get('toast');
  if (msg) {
    var type = p.get('toast_type') || 'info';
    window.showToast(msg, type);
    var url = new URL(window.location);
    url.searchParams.delete('toast');
    url.searchParams.delete('toast_type');
    history.replaceState(null, '', url);
  }
})();

// Select placeholder color: grey when empty, black when has value
document.querySelectorAll('.filter-bar select, .form-group select').forEach(function(sel) {
  function updateColor() { if (sel.value) sel.classList.add('has-value'); else sel.classList.remove('has-value'); }
  sel.addEventListener('change', updateColor);
  updateColor();
});

// Filter: search and clear
function doSearch() {
  var bar = document.querySelector('.filter-bar');
  if (!bar) return;
  var keyword = '';
  var filters = {};
  bar.querySelectorAll('input[type="text"]').forEach(function(inp) { if (inp.value.trim()) keyword = inp.value.trim().toLowerCase(); });
  bar.querySelectorAll('select').forEach(function(sel) { if (sel.value) filters[sel.name || 'sel'] = sel.value; });
  var table = document.querySelector('.ant-table tbody');
  if (!table) return;
  table.querySelectorAll('tr').forEach(function(row) {
    var text = row.textContent.toLowerCase();
    var match = true;
    if (keyword && text.indexOf(keyword) === -1) match = false;
    Object.values(filters).forEach(function(v) { if (v && text.indexOf(v.toLowerCase()) === -1) match = false; });
    row.style.display = match ? '' : 'none';
  });
}
function clearFilters() {
  var bar = document.querySelector('.filter-bar');
  if (!bar) return;
  bar.querySelectorAll('input[type="text"]').forEach(function(inp) { inp.value = ''; });
  bar.querySelectorAll('select').forEach(function(sel) { sel.selectedIndex = 0; sel.classList.remove('has-value'); });
  var table = document.querySelector('.ant-table tbody');
  if (table) table.querySelectorAll('tr').forEach(function(row) { row.style.display = ''; });
}

// Tooltip for [data-tip] elements — appended to body, not clipped by overflow
(function(){
  var tip = null;
  function showTip(el) {
    if (tip) { tip.remove(); tip = null; }
    var text = el.getAttribute('data-tip');
    if (!text) return;
    // Only show if content is actually truncated
    if (el.scrollWidth <= el.clientWidth + 1 && el.tagName === 'TD') return;
    tip = document.createElement('div');
    tip.className = 'q-tooltip';
    tip.textContent = text;
    document.body.appendChild(tip);
    var rect = el.getBoundingClientRect();
    var left = Math.max(8, Math.min(rect.left, window.innerWidth - tip.offsetWidth - 8));
    var top = rect.top - tip.offsetHeight - 8;
    if (top < 8) top = rect.bottom + 8;
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }
  function hideTip() { if (tip) { tip.remove(); tip = null; } }
  document.addEventListener('mouseover', function(e) {
    var el = e.target.closest('[data-tip]');
    if (el) showTip(el);
  });
  document.addEventListener('mouseout', function(e) {
    var el = e.target.closest('[data-tip]');
    if (el) hideTip();
  });
})();
</script>
</body>
</html>"""


def render_page(title, content, active="", breadcrumb=None):
    return render_template_string(BASE_TEMPLATE, title=title, content=content, active=active, breadcrumb=breadcrumb)


# ════════════════════════════════════════════════════════════════
# Section 4: Helper functions
# ════════════════════════════════════════════════════════════════

# ── SVG outline icons (matching the reference screenshot) ──
# Add-child: 带加号的子级图标
ICON_ADD_CHILD = '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="14" height="10" rx="2"/><rect x="7" y="11" width="14" height="10" rx="2"/><line x1="14" y1="13.5" x2="14" y2="18.5"/><line x1="11.5" y1="16" x2="16.5" y2="16"/></svg>'
# Enable / send: 纸飞机/发送图标
ICON_ENABLE = '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2L15 22L11 13L2 9L22 2Z"/></svg>'
# Copy: 复制图标
ICON_COPY = '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>'
# Delete: 删除/垃圾桶图标
ICON_DELETE = '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6L18.1 20a2 2 0 01-2 2H7.9a2 2 0 01-2-2L5 6"/><path d="M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>'
# View: 眼睛图标
ICON_VIEW = '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>'
# Edit: 编辑图标
ICON_EDIT = '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>'
# Data/list icon
ICON_DATA = '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>'
# Disable: 暂停图标
ICON_DISABLE = '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/></svg>'
# Analyze: bar chart icon
ICON_ANALYZE = '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'


NOTICE_MVP = '<div style="background:#fff7e6;border:1px solid #ffd591;border-radius:8px;padding:8px 16px;margin-bottom:12px;font-size:13px;color:#ad6800;display:flex;align-items:center;gap:8px;"><span style="font-size:16px;">&#9888;</span> MVP \u4e0d\u5305\u542b\uff0c\u529f\u80fd\u4ec5\u793a\u610f</div>'
NOTICE_COLLECT = '<div style="background:#fff1f0;border:1px solid #ffa39e;border-radius:8px;padding:8px 16px;margin-bottom:12px;font-size:13px;color:#cf1322;display:flex;align-items:center;gap:8px;"><span style="font-size:16px;">&#9888;</span> \u672c\u6a21\u5757\u4e3a\u91c7\u96c6\u7aef\u529f\u80fd\uff0c\u9875\u9762\u4ec5\u793a\u610f\u7528</div>'
NOTICE_TASK = '<div style="background:#fff1f0;border:1px solid #ffa39e;border-radius:8px;padding:8px 16px;margin-bottom:12px;font-size:13px;color:#cf1322;display:flex;align-items:center;gap:8px;"><span style="font-size:16px;">&#9888;</span> MVP \u4e0d\u5305\u542b\uff0c\u529f\u80fd\u4ec5\u793a\u610f</div>'


def icon_btn(href, icon_svg, title, style="default"):
    """Generate an outline-style icon button with tooltip."""
    return f'<a class="act-icon act-{style}" href="{href}" title="{title}" data-tip="{title}">{icon_svg}</a>'


def get_model_name(mid):
    m = next((m for m in MODELS if m["id"] == mid), None)
    return m["name"] if m else mid

def get_prompt(pid):
    return next((p for p in PROMPTS if p["id"] == pid), None)

def get_benchmark(bid):
    return next((b for b in BENCHMARKS if b["id"] == bid), None)

def get_scene(sid):
    return next((s for s in SCENES if s["id"] == sid), None)

def get_criterion(cid):
    return next((c for c in CRITERIA if c["id"] == cid), None)

def difficulty_stars(n):
    return '<span class="difficulty">' + ("&#9733;" * n) + ("&#9734;" * (5 - n)) + '</span>'


# ════════════════════════════════════════════════════════════════
# Section 5: Routes
# ════════════════════════════════════════════════════════════════

# ── Dashboard / redirect ──
@app.route("/")
def index():
    return redirect(url_for("tasks_page"))


# ── Prompt Management ──
INLINE_INPUT = 'style="width:100%;padding:5px 12px;height:36px;border:1px solid #d9d9d9;border-radius:8px;font-size:14px;box-sizing:border-box;"'

@app.route("/prompts")
def prompts_page():
    # Pre-build tree selector HTML (reused in forms)
    tree_html = build_tree_selector_html("shared")

    rows = ""
    for p in PROMPTS:
        agg_labels = prompt_aggregated_labels(p)
        labels_html = render_tags_html(agg_labels)

        enabled = p.get("enabled", True)
        status_html = '<span class="ant-tag ant-tag-green">\u5df2\u542f\u7528</span>' if enabled else '<span class="ant-tag">\u672a\u542f\u7528</span>'

        if enabled:
            actions_html = icon_btn(f'/prompts/{p["id"]}/copy', ICON_COPY, "\u590d\u5236", "default")
        else:
            actions_html = (
                f'<a class="act-icon act-primary" href="javascript:;" onclick="showAddChild(\'{p["id"]}\')" title="\u589e\u52a0\u4e0b\u7ea7">{ICON_ADD_CHILD}</a>'
                + icon_btn(f'/prompts/{p["id"]}/toggle', ICON_ENABLE, "\u542f\u7528", "default")
                + icon_btn(f'/prompts/{p["id"]}/copy', ICON_COPY, "\u590d\u5236", "default")
                + icon_btn(f'/prompts/{p["id"]}/delete', ICON_DELETE, "\u5220\u9664", "danger")
            )

        labels_tip = _build_tip_text(agg_labels)
        rows += '<tr class="row-parent" data-id="' + p["id"] + '">'
        rows += f'<td><button class="expand-btn" data-target="sub-{p["id"]}">&#9654;</button></td>'
        rows += td_tip(p["high_level"], 'style="font-weight:600;"')
        rows += td_tip(p["high_level_en"])
        rows += td_tip(labels_html, tip_text=labels_tip)
        rows += f'<td>{status_html}</td>'
        rows += f'<td>{p["creator"]}</td>'
        rows += f'<td class="actions-cell">{actions_html}</td>'
        rows += '</tr>'

        for ll in p["low_levels"]:
            ll_labels_html = render_tags_html(ll.get("labels", []))
            ll_tip = _build_tip_text(ll.get("labels", []))
            child_actions = '' if enabled else icon_btn(f'/prompts/{p["id"]}/del-child/{ll["id"]}', ICON_DELETE, "\u5220\u9664", "danger")

            rows += f'<tr class="sub-row sub-{p["id"]} row-child">'
            rows += '<td class="child-line"></td>'
            rows += td_tip(ll["zh"])
            rows += td_tip(ll["en"])
            rows += td_tip(ll_labels_html, tip_text=ll_tip)
            rows += '<td></td>'
            rows += '<td></td>'
            rows += f'<td class="actions-cell">{child_actions}</td>'
            rows += '</tr>'

        # Hidden inline add-child row (shown by JS, with tree selector)
        if not enabled:
            child_tree = build_tree_selector_html(f"child-{p['id']}")
            rows += f'''<tr class="sub-row sub-{p['id']} row-child row-inline-child" id="add-child-{p['id']}" style="display:none;">
                <td class="child-line"></td>
                <td><input type="text" form="form-child-{p['id']}" name="zh" placeholder="\u8f93\u5165\u5b50\u6b65\u9aa4 (\u4e2d\u6587)" {INLINE_INPUT}></td>
                <td><input type="text" form="form-child-{p['id']}" name="en" placeholder="Sub-step (English)" {INLINE_INPUT}></td>
                <td>
                  <div class="ts-wrap" id="ts-child-{p['id']}">
                    <div class="ts-trigger" onclick="tsToggle('ts-child-{p['id']}')"><span class="ts-placeholder">\u9009\u62e9\u6807\u7b7e</span></div>
                    <div class="ts-panel">{child_tree}</div>
                    <input type="hidden" form="form-child-{p['id']}" name="labels" value="">
                  </div>
                </td>
                <td></td>
                <td></td>
                <td class="actions-cell">
                    <button type="submit" form="form-child-{p['id']}" class="ant-btn ant-btn-sm ant-btn-primary">\u4fdd\u5b58</button>
                    <button type="button" class="ant-btn ant-btn-sm" onclick="hideAddChild('{p['id']}')">\u53d6\u6d88</button>
                </td>
            </tr>
            <form id="form-child-{p['id']}" method="POST" action="/prompts/{p['id']}/add-child" style="display:none;"></form>'''

    # Build filter tag options (tree-style multi-select for filter)
    filter_tree = build_tree_selector_html("filter")

    # Collect unique creators
    creators_set = sorted(set(p["creator"] for p in PROMPTS))
    creator_options = "".join(f"<option>{c}</option>" for c in creators_set)

    content = f'''
    <form id="inline-add" method="POST" action="/prompts/create" style="display:none;"></form>
    <div class="filter-bar">
      <input type="text" placeholder="High level" style="min-width:140px;">
      <input type="text" placeholder="Low level" style="min-width:140px;">
      <div class="ts-wrap" id="ts-filter" style="min-width:200px;max-width:360px;">
        <div class="ts-trigger" onclick="tsToggle('ts-filter')" style="min-height:36px;"><span class="ts-placeholder">\u6807\u7b7e</span></div>
        <div class="ts-panel">{filter_tree}</div>
        <input type="hidden" name="filter_tags" value="">
      </div>
      <select style="min-width:120px;"><option value="">\u521b\u5efa\u4eba</option>{creator_options}</select>
      <button class="ant-btn" onclick="clearFilters()">\u6e05\u7a7a</button>
      <button class="ant-btn ant-btn-primary" onclick="doSearch()">\u641c\u7d22</button>
      <div style="flex:1;"></div>
      <button class="ant-btn ant-btn-primary" onclick="showNewParent()">+ \u65b0\u589e High Level</button>
    </div>
    <div class="ant-card ant-card-bordered">
      <table class="ant-table" id="prompt-table">
        <thead><tr>
            <th style="width:32px;"></th>
            <th>\u4efb\u52a1\u63d0\u793a\u8bcd</th>
            <th>Task Prompt</th>
            <th>\u6807\u7b7e</th>
            <th>\u72b6\u6001</th>
            <th>\u521b\u5efa\u4eba</th>
            <th>\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>
          <!-- New parent row (hidden, shown at top) -->
          <tr class="row-new-parent" id="new-parent-row" style="display:none;">
            <td></td>
            <td><input type="text" form="inline-add" name="high_level" placeholder="\u8f93\u5165\u4efb\u52a1\u540d\u79f0 (\u4e2d\u6587)" {INLINE_INPUT}></td>
            <td><input type="text" form="inline-add" name="high_level_en" placeholder="Task name (English)" {INLINE_INPUT}></td>
            <td>
              <div class="ts-wrap" id="ts-new-parent">
                <div class="ts-trigger" onclick="tsToggle('ts-new-parent')"><span class="ts-placeholder">\u9009\u62e9\u6807\u7b7e</span></div>
                <div class="ts-panel">{tree_html}</div>
                <input type="hidden" form="inline-add" name="parent_labels" value="">
              </div>
            </td>
            <td></td>
            <td style="color:rgba(0,0,0,0.45);font-size:13px;">Joanna Qiao</td>
            <td class="actions-cell">
                <a class="act-icon act-primary" href="javascript:;" onclick="addNewChildRow()" title="\u6dfb\u52a0\u5b50\u6b65\u9aa4">{ICON_ADD_CHILD}</a>
                <button type="submit" form="inline-add" class="ant-btn ant-btn-sm ant-btn-primary">\u4fdd\u5b58</button>
                <button type="button" class="ant-btn ant-btn-sm" onclick="cancelNewParent()">\u53d6\u6d88</button>
            </td>
          </tr>
          <!-- Dynamic new-child rows inserted here by JS -->
          <tr id="new-children-anchor" style="display:none;"></tr>
    <!-- Hidden tree-selector template for JS cloning -->
    <template id="tree-tpl">{tree_html}</template>
          {rows}
        </tbody>
      </table>
    </div>
    <div style="margin-top:16px;display:flex;justify-content:flex-end;align-items:center;gap:12px;font-size:13px;color:rgba(0,0,0,0.45);">
      <span>10\u6761/\u9875</span>
      <span style="display:inline-flex;gap:4px;">
        <span style="padding:4px 10px;background:#1F80A0;color:#fff;border-radius:8px;">1</span>
        <span style="padding:4px 10px;background:#f5f5f5;border-radius:8px;cursor:pointer;">2</span>
      </span>
    </div>

    <style>
      #prompt-table {{ table-layout: fixed; }}
      #prompt-table th:nth-child(1) {{ width: 32px; }}
      #prompt-table th:nth-child(2) {{ width: 22%; }}
      #prompt-table th:nth-child(3) {{ width: 24%; }}
      #prompt-table th:nth-child(4) {{ width: 20%; }}
      #prompt-table th:nth-child(5) {{ width: 72px; }}
      #prompt-table th:nth-child(6) {{ width: 80px; }}
      #prompt-table th:nth-child(7) {{ width: 120px; }}
      #prompt-table td {{ text-overflow: ellipsis; white-space: nowrap; max-width: 0; overflow: hidden; }}
      .row-parent td {{ font-weight: 500; }}
      .row-child td {{ font-size: 13px; background: #fafafa; }}
      .row-child td.child-line {{ border-left: 2px solid #e8e8e8; }}
      .row-child:hover td {{ background: #e6f4f8; }}
      .row-child:hover td.child-line {{ border-left-color: #1F80A0; }}
      .row-new-parent td, .row-new-child td {{ vertical-align: middle; white-space: normal !important; overflow: visible !important; }}
      .row-new-child td {{ background: #fafafa; }}
      .row-new-child td:first-child {{ border-left: 2px solid #1F80A0; }}
    </style>

    <script>
    // === New parent + children (combined creation) ===
    let newChildCount = 0;
    function showNewParent() {{
      document.getElementById('new-parent-row').style.display = 'table-row';
      if (newChildCount === 0) addNewChildRow();  // auto-add first child
    }}
    function cancelNewParent() {{
      document.getElementById('new-parent-row').style.display = 'none';
      document.querySelectorAll('.row-new-child').forEach(r => r.remove());
      newChildCount = 0;
    }}
    function addNewChildRow() {{
      const idx = newChildCount++;
      const tsId = 'ts-newchild-' + idx;
      const treeContent = document.getElementById('tree-tpl').innerHTML;
      const anchor = document.getElementById('new-children-anchor');
      const tr = document.createElement('tr');
      tr.className = 'row-new-child';
      tr.innerHTML = `
        <td style="border-left:2px solid #1F80A0;"></td>
        <td><input type="text" form="inline-add" name="child_zh_${{idx}}" placeholder="\u5b50\u6b65\u9aa4 (\u4e2d\u6587)" {INLINE_INPUT}></td>
        <td><input type="text" form="inline-add" name="child_en_${{idx}}" placeholder="Sub-step (English)" {INLINE_INPUT}></td>
        <td>
          <div class="ts-wrap" id="${{tsId}}">
            <div class="ts-trigger" onclick="tsToggle('${{tsId}}')"><span class="ts-placeholder">\u9009\u62e9\u6807\u7b7e</span></div>
            <div class="ts-panel">${{treeContent}}</div>
            <input type="hidden" form="inline-add" name="child_labels_${{idx}}" value="">
          </div>
        </td>
        <td></td><td></td>
        <td class="actions-cell">
          <a class="act-icon act-danger" href="javascript:;" onclick="this.closest('tr').remove()" title="\u5220\u9664">{ICON_DELETE}</a>
        </td>`;
      anchor.parentNode.insertBefore(tr, anchor);
      // bind checkbox events for the new tree selector
      tsInit(document.getElementById(tsId));
      let h = document.getElementById('inline-child-count');
      if (!h) {{ h = document.createElement('input'); h.type='hidden'; h.id='inline-child-count'; h.name='child_count'; document.getElementById('inline-add').appendChild(h); }}
      h.value = newChildCount;
    }}

    // === Existing parent: inline add child ===
    function showAddChild(pid) {{
      const btn = document.querySelector('tr[data-id="'+pid+'"] .expand-btn');
      if (btn && !btn.classList.contains('expanded')) btn.click();
      const row = document.getElementById('add-child-' + pid);
      if (row) {{ row.style.display = 'table-row'; tsInit(document.getElementById('ts-child-' + pid)); }}
    }}
    function hideAddChild(pid) {{
      const row = document.getElementById('add-child-' + pid);
      if (row) row.style.display = 'none';
    }}

    // === TreeSelect ===
    function tsToggle(wrapId) {{
      const w = document.getElementById(wrapId);
      w.classList.toggle('open');
    }}
    document.addEventListener('click', function(e) {{
      document.querySelectorAll('.ts-wrap.open').forEach(w => {{
        if (!w.contains(e.target)) w.classList.remove('open');
      }});
    }});
    function tsInit(wrap) {{
      if (!wrap || wrap.dataset.tsInit) return;
      wrap.dataset.tsInit = '1';
      // Arrow click → expand/collapse children
      wrap.querySelectorAll('.ts-arrow:not(.empty)').forEach(arrow => {{
        arrow.addEventListener('click', function(e) {{
          e.stopPropagation();
          this.classList.toggle('expanded');
          const children = this.closest('.ts-node').querySelector('.ts-children');
          if (children) children.classList.toggle('expanded');
        }});
      }});
      // Row click → select/deselect
      wrap.querySelectorAll('.ts-row[data-id]').forEach(row => {{
        row.addEventListener('click', function(e) {{
          if (e.target.classList.contains('ts-arrow')) return;
          this.classList.toggle('selected');
          tsSync(wrap);
        }});
      }});
    }}
    function tsSync(wrap) {{
      const trigger = wrap.querySelector('.ts-trigger');
      const hidden = wrap.querySelector('input[type="hidden"]');
      const selected = wrap.querySelectorAll('.ts-row.selected');
      const ids = []; let chips = '';
      selected.forEach(row => {{
        const id = row.dataset.id;
        const path = row.dataset.path;
        ids.push(id);
        chips += '<span class="ts-chip"><span class="ts-chip-text">' + path + '</span><span class="ts-chip-close" data-rid="'+id+'" onclick="event.stopPropagation();tsRemove(this)">&times;</span></span>';
      }});
      trigger.innerHTML = chips || '<span class="ts-placeholder">\u9009\u62e9\u6807\u7b7e</span>';
      if (hidden) hidden.value = ids.join(',');
    }}
    function tsRemove(closeBtn) {{
      const wrap = closeBtn.closest('.ts-wrap');
      const rid = closeBtn.dataset.rid;
      const row = wrap.querySelector('.ts-row[data-id="'+rid+'"]');
      if (row) row.classList.remove('selected');
      tsSync(wrap);
    }}
    // Init all on load
    document.querySelectorAll('.ts-wrap').forEach(w => tsInit(w));
    </script>
    '''
    return render_page("\u63d0\u793a\u8bcd\u7ba1\u7406", content, active="prompts")


@app.route("/prompts/create", methods=["POST"])
def prompts_create():
    hl = request.form.get("high_level", "").strip()
    hl_en = request.form.get("high_level_en", "").strip()
    parent_labels = [l.strip() for l in request.form.get("parent_labels", "").split(",") if l.strip()]
    if not hl:
        flash("\u4efb\u52a1\u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a", "error")
        return redirect(url_for("prompts_page"))
    new_id = f"p{len(PROMPTS)+1}"
    # Collect children
    child_count = int(request.form.get("child_count", 0))
    low_levels = []
    for i in range(child_count):
        zh = request.form.get(f"child_zh_{i}", "").strip()
        en = request.form.get(f"child_en_{i}", "").strip()
        cl = [l.strip() for l in request.form.get(f"child_labels_{i}", "").split(",") if l.strip()]
        if zh:
            low_levels.append({"id": f"{new_id}-{len(low_levels)+1}", "zh": zh, "en": en, "labels": cl or parent_labels})
    PROMPTS.insert(0, {
        "id": new_id,
        "high_level": hl,
        "high_level_en": hl_en,
        "enabled": False,
        "creator": "Joanna Qiao",
        "low_levels": low_levels,
    })
    flash(f"\u63d0\u793a\u8bcd\u300c{hl}\u300d\u521b\u5efa\u6210\u529f", "success")
    return redirect(url_for("prompts_page"))


@app.route("/prompts/<pid>/add-child", methods=["POST"])
def prompt_add_child_post(pid):
    p = next((p for p in PROMPTS if p["id"] == pid), None)
    if not p:
        flash("\u63d0\u793a\u8bcd\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("prompts_page"))
    zh = request.form.get("zh", "").strip()
    en = request.form.get("en", "").strip()
    labels = [l.strip() for l in request.form.get("labels", "").split(",") if l.strip()]
    if zh:
        child_id = f"{pid}-{len(p['low_levels'])+1}"
        p["low_levels"].append({"id": child_id, "zh": zh, "en": en, "labels": labels})
        flash(f"\u5b50\u7ea7\u300c{zh}\u300d\u6dfb\u52a0\u6210\u529f", "success")
    return redirect(url_for("prompts_page"))


@app.route("/prompts/<pid>/toggle")
def prompt_toggle(pid):
    p = next((p for p in PROMPTS if p["id"] == pid), None)
    if p:
        p["enabled"] = not p.get("enabled", False)
        state = "\u542f\u7528" if p["enabled"] else "\u53d6\u6d88\u542f\u7528"
        flash(f"\u300c{p['high_level']}\u300d\u5df2{state}", "success")
    return redirect(url_for("prompts_page"))


@app.route("/prompts/<pid>/copy")
def prompt_copy(pid):
    p = next((p for p in PROMPTS if p["id"] == pid), None)
    if p:
        import copy
        new_p = copy.deepcopy(p)
        new_p["id"] = f"p{len(PROMPTS)+1}"
        new_p["high_level"] = p["high_level"] + " (\u526f\u672c)"
        new_p["high_level_en"] = p["high_level_en"] + " (copy)"
        new_p["enabled"] = False
        # Update child ids
        for i, ll in enumerate(new_p["low_levels"]):
            ll["id"] = f"{new_p['id']}-{i+1}"
        PROMPTS.append(new_p)
        flash(f"\u300c{p['high_level']}\u300d\u590d\u5236\u6210\u529f", "success")
    return redirect(url_for("prompts_page"))


@app.route("/prompts/<pid>/delete")
def prompt_delete(pid):
    global PROMPTS
    p = next((p for p in PROMPTS if p["id"] == pid), None)
    if p:
        if p.get("enabled"):
            flash("\u5df2\u542f\u7528\u7684\u63d0\u793a\u8bcd\u4e0d\u53ef\u5220\u9664", "error")
        else:
            PROMPTS = [x for x in PROMPTS if x["id"] != pid]
            flash(f"\u300c{p['high_level']}\u300d\u5df2\u5220\u9664", "success")
    return redirect(url_for("prompts_page"))


@app.route("/prompts/<pid>/del-child/<cid>")
def prompt_del_child(pid, cid):
    p = next((p for p in PROMPTS if p["id"] == pid), None)
    if p:
        if p.get("enabled"):
            flash("\u5df2\u542f\u7528\u72b6\u6001\u4e0d\u53ef\u5220\u9664\u5b50\u7ea7", "error")
        else:
            p["low_levels"] = [ll for ll in p["low_levels"] if ll.get("id") != cid]
            flash("\u5b50\u7ea7\u63d0\u793a\u8bcd\u5df2\u5220\u9664", "success")
    return redirect(url_for("prompts_page"))


# ── Tag Management ──
@app.route("/tags")
def tags_page():
    dims = TAXONOMY["dimensions"]

    # Flatten taxonomy into tree rows (supports unlimited depth)
    all_rows = []
    counter = {"n": 0}

    def walk(node, level, parent_chain, is_dim=False):
        nid = node.get("id") or f"_n{counter['n']}"
        counter["n"] += 1
        children = (node.get("tags") if is_dim else node.get("sub_tags")) or []
        all_rows.append({
            "id": nid,
            "level": level,
            "name": node.get("name", ""),
            "name_en": node.get("name_en", ""),
            "description": node.get("description", ""),
            "children_count": len(children),
            "parent_chain": list(parent_chain),
            "has_children": bool(children),
            "is_dim": is_dim,
        })
        for c in children:
            walk(c, level + 1, parent_chain + [nid], False)

    for dim in dims:
        walk(dim, 0, [], is_dim=True)

    rows_html = ""
    for r in all_rows:
        indent_px = r["level"] * 20
        if r["has_children"]:
            caret = f'<span class="tree-caret" onclick="tagToggle(\'{r["id"]}\')">\u25be</span>'
        else:
            caret = '<span style="display:inline-block;width:16px;"></span>'

        if r["is_dim"]:
            name_style = "font-size:15px;font-weight:600;color:#1F80A0;"
        elif r["level"] == 1:
            name_style = "font-size:14px;font-weight:500;color:rgba(0,0,0,0.85);"
        else:
            name_style = "font-size:13px;color:rgba(0,0,0,0.65);"

        parent_attr = ",".join(r["parent_chain"])
        count_tag = f'<span class="ant-tag" style="font-size:11px;">{r["children_count"]}</span>' if r["has_children"] else ""
        desc = r["description"] or ("\u2014" if not r["is_dim"] else "")
        name_en_html = f'<span style="margin-left:8px;font-size:12px;color:rgba(0,0,0,0.35);">{r["name_en"]}</span>' if r["name_en"] else ""

        add_btn = icon_btn("#", ICON_ADD_CHILD, "\u65b0\u589e\u5b50\u6807\u7b7e", "default")
        edit_btn = icon_btn("#", ICON_EDIT, "\u7f16\u8f91", "default")
        del_btn = icon_btn("#", ICON_DELETE, "\u5220\u9664", "danger")

        rows_html += (
            f'<tr data-id="{r["id"]}" data-parent="{parent_attr}" data-level="{r["level"]}">'
            f'<td style="padding-left:{16 + indent_px}px;white-space:nowrap;">{caret} <span style="{name_style}">{r["name"]}</span>{name_en_html}</td>'
            f'<td style="color:rgba(0,0,0,0.65);">{desc}</td>'
            f'<td style="text-align:center;">{count_tag}</td>'
            f'<td class="actions-cell">{add_btn}{edit_btn}{del_btn}</td>'
            f'</tr>'
        )

    total_dims = len(dims)
    total_l2 = sum(len(d["tags"]) for d in dims)
    total_l3 = sum(sum(len(t.get("sub_tags", [])) for t in d["tags"]) for d in dims)

    content = f'''
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <div style="font-size:13px;color:rgba(0,0,0,0.45);">
        \u6807\u7b7e\u4f53\u7cfb v{TAXONOMY["version"]} &middot;
        {total_dims} \u4e2a\u7ef4\u5ea6 &middot; {total_l2} \u4e2a\u4e8c\u7ea7 &middot; {total_l3} \u4e2a\u4e09\u7ea7
      </div>
      <div style="display:flex;gap:8px;">
        <button class="ant-btn" onclick="tagExpandAll(true)">\u5168\u90e8\u5c55\u5f00</button>
        <button class="ant-btn" onclick="tagExpandAll(false)">\u5168\u90e8\u6536\u8d77</button>
        <button class="ant-btn ant-btn-primary">+ \u65b0\u589e\u7ef4\u5ea6</button>
      </div>
    </div>

    <div class="ant-card ant-card-bordered">
      <table class="ant-table" id="tag-tree-tbl">
        <thead><tr>
          <th>\u540d\u79f0</th>
          <th>\u63cf\u8ff0</th>
          <th style="width:60px;text-align:center;">\u5b50\u9879</th>
          <th style="width:120px;">\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>

    <style>
      .tree-caret {{ cursor:pointer; display:inline-block; width:16px; text-align:center; color:rgba(0,0,0,0.45); transition:transform 0.2s; user-select:none; margin-right:2px; font-size:10px; }}
      .tree-caret:hover {{ color:#1F80A0; }}
      .tree-caret.collapsed {{ transform:rotate(-90deg); }}
    </style>

    <script>
    function tagToggle(id) {{
      var caret = document.querySelector('tr[data-id="' + id + '"] .tree-caret');
      if (!caret) return;
      var wasCollapsed = caret.classList.contains('collapsed');
      caret.classList.toggle('collapsed');
      document.querySelectorAll('#tag-tree-tbl tbody tr[data-parent]').forEach(function(tr) {{
        var chain = (tr.getAttribute('data-parent') || '').split(',');
        if (chain.indexOf(id) >= 0) {{
          tr.style.display = wasCollapsed ? '' : 'none';
          var childCaret = tr.querySelector('.tree-caret');
          if (childCaret) {{
            if (wasCollapsed) childCaret.classList.remove('collapsed');
            else childCaret.classList.add('collapsed');
          }}
        }}
      }});
    }}
    function tagExpandAll(expand) {{
      document.querySelectorAll('.tree-caret').forEach(function(c) {{
        if (expand) c.classList.remove('collapsed');
        else c.classList.add('collapsed');
      }});
      document.querySelectorAll('#tag-tree-tbl tbody tr').forEach(function(tr) {{
        var p = tr.getAttribute('data-parent') || '';
        if (p) tr.style.display = expand ? '' : 'none';
      }});
    }}
    </script>
    '''
    return render_page("\u6807\u7b7e\u7ba1\u7406", content, active="tags")


# ── Criteria Management ──
@app.route("/criteria")
def criteria_page():
    rows = ""
    for c in CRITERIA:
        ct = CRITERIA_TYPES.get(c["type"], {})
        type_tag = f'<span class="ant-tag ant-tag-{ct.get("color","")}">{ct.get("label","")}</span>'
        form = c.get("form", {})
        type_items = len(form.get("type_module", {}).get("items", []))
        scale_items = len(form.get("scale_module", {}).get("items", []))
        has_note = "\u2713" if form.get("note") else "--"
        modules = []
        if type_items > 0:
            modules.append(f"{ct.get('label','')} \u00d7{type_items}")
        if scale_items > 0:
            modules.append(f"\u91cf\u8868 \u00d7{scale_items}")
        if form.get("note"):
            modules.append("\u5907\u6ce8")
        modules_html = " + ".join(modules) if modules else "--"

        edit_btn = icon_btn(f"/criteria/{c['id']}", ICON_VIEW, "\u67e5\u770b", "default")
        copy_btn = icon_btn("#", ICON_COPY, "\u590d\u5236", "default")
        del_btn = icon_btn("#", ICON_DELETE, "\u5220\u9664", "danger")

        rows += f'''<tr>
            <td style="font-weight:500;">{c["name"]}</td>
            <td>{type_tag}</td>
            <td title="{c['description']}">{c["description"][:40]}...</td>
            <td>{modules_html}</td>
            <td>{c["creator"]}</td>
            <td>{c["created_at"]}</td>
            <td class="actions-cell">{edit_btn}{copy_btn}{del_btn}</td>
        </tr>'''

    content = f'''
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-label">\u6807\u51c6\u603b\u6570</div><div class="stat-value">{len(CRITERIA)}</div></div>
      <div class="stat-card"><div class="stat-label">\u504f\u597d\u9009\u62e9</div><div class="stat-value">{sum(1 for c in CRITERIA if c["type"]=="preference")}</div></div>
      <div class="stat-card"><div class="stat-label">\u6210\u529f\u5931\u8d25</div><div class="stat-value">{sum(1 for c in CRITERIA if c["type"]=="pass_fail")}</div></div>
      <div class="stat-card"><div class="stat-label">\u91cf\u8868\u8bc4\u5206</div><div class="stat-value">{sum(1 for c in CRITERIA if c["type"]=="scale")}</div></div>
    </div>

    <div class="filter-bar">
      <input type="text" placeholder="\u641c\u7d22\u6807\u51c6\u540d\u79f0" style="min-width:180px;">
      <select style="min-width:130px;">
        <option value="">\u5168\u90e8\u7c7b\u578b</option>
        {"".join(f'<option value="{k}">{v["label"]}</option>' for k,v in CRITERIA_TYPES.items())}
      </select>
      <button class="ant-btn" onclick="clearFilters()">\u6e05\u7a7a</button>
      <button class="ant-btn ant-btn-primary" onclick="doSearch()">\u641c\u7d22</button>
      <div style="flex:1;"></div>
      <button class="ant-btn ant-btn-primary" onclick="openModal(\'create-criteria-drawer\')">+ \u65b0\u589e\u8bc4\u4ef7\u6807\u51c6</button>
    </div>

    <div class="ant-card ant-card-bordered">
      <table class="ant-table">
        <thead><tr>
          <th>\u6807\u51c6\u540d\u79f0</th>
          <th>\u7c7b\u578b</th>
          <th>\u63cf\u8ff0</th>
          <th>\u8868\u5355\u7ec4\u6210</th>
          <th>\u521b\u5efa\u4eba</th>
          <th>\u521b\u5efa\u65f6\u95f4</th>
          <th>\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <!-- Create Criteria Drawer -->
    <div class="ant-drawer-mask" id="create-criteria-drawer">
      <div class="ant-drawer-content">
        <div class="ant-drawer-header">
          <h3>\u65b0\u589e\u8bc4\u4ef7\u6807\u51c6</h3>
          <button class="ant-drawer-close" onclick="closeModal('create-criteria-drawer')">&times;</button>
        </div>
        <form method="POST" action="/criteria/create">
        <div class="ant-drawer-body">
          <div class="form-row">
            <div class="form-group"><label>\u6807\u51c6\u540d\u79f0</label><input type="text" name="name" required></div>
            <div class="form-group"><label>\u7c7b\u578b</label>
              <select name="type">
                {"".join(f'<option value="{k}">{v["label"]} ({v["label_en"]})</option>' for k,v in CRITERIA_TYPES.items())}
              </select>
            </div>
            <div class="form-group"></div>
          </div>
          <div class="form-group"><label>\u63cf\u8ff0</label><textarea name="description" rows="3"></textarea></div>
          <hr style="border:none;border-top:1px solid #f0f0f0;margin:20px 0;">
          <h4 style="font-size:15px;font-weight:500;margin-bottom:12px;">\u8868\u5355\u914d\u7f6e</h4>
          <div class="form-group"><label>\u7c7b\u578b\u6a21\u5757 - \u63d0\u793a\u8bcd</label><input type="text" name="type_prompt" placeholder="\u4f8b\u5982\uff1a\u54ea\u65b9\u66f4\u4f18\uff1f / \u4efb\u52a1\u662f\u5426\u5b8c\u6210\uff1f"></div>
          <div class="form-row">
            <div class="form-group"><label>\u91cf\u8868\u6307\u6807\u540d (\u53ef\u9009)</label><input type="text" name="scale_name" placeholder="\u4f8b\u5982\uff1aprogress_score"></div>
            <div class="form-group"><label>\u91cf\u8868\u8303\u56f4</label><input type="text" name="scale_range" placeholder="0.0-1.0"></div>
            <div class="form-group"><label>\u91cf\u8868\u63cf\u8ff0</label><input type="text" name="scale_desc" placeholder="\u4efb\u52a1\u5b8c\u6210\u8fdb\u5ea6"></div>
          </div>
          <div class="form-group"><label>\u5907\u6ce8 (\u53ef\u9009)</label><textarea name="note" rows="2" placeholder="\u8df8\u6a21\u578b\u586b\u5199\u4e00\u4efd\u7684\u6587\u5b57\u8bf4\u660e"></textarea></div>
        </div>
        <div class="ant-drawer-footer">
          <button type="button" class="ant-btn" onclick="closeModal('create-criteria-drawer')">\u53d6\u6d88</button>
          <button type="submit" class="ant-btn ant-btn-primary">\u521b\u5efa</button>
        </div>
        </form>
      </div>
    </div>
    '''
    return render_page("\u8bc4\u4ef7\u6807\u51c6\u7ba1\u7406", NOTICE_MVP + content, active="criteria")


@app.route("/criteria/create", methods=["POST"])
def criteria_create():
    name = request.form.get("name", "").strip()
    ctype = request.form.get("type", "preference")
    desc = request.form.get("description", "")
    type_prompt = request.form.get("type_prompt", "")
    scale_name = request.form.get("scale_name", "")
    scale_range = request.form.get("scale_range", "")
    scale_desc = request.form.get("scale_desc", "")
    note = request.form.get("note", "").strip() or None
    if not name:
        flash("\u6807\u51c6\u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a", "error")
        return redirect(url_for("criteria_page"))
    # Build type_module item
    if ctype == "pass_fail":
        type_item = {"prompt": type_prompt, "model": "", "result": ""}
    elif ctype == "preference":
        type_item = {"prompt": type_prompt, "winner": None, "is_tie": False}
    elif ctype == "baseline":
        type_item = {"prompt": type_prompt, "result": ""}
    else:
        sr = {"min": 0, "max": 5}
        type_item = {"prompt": type_prompt, "metric_name": scale_name or "score", "metric_description": scale_desc, "score_range": sr, "value": None}
    # Build scale_module
    scale_items = []
    if scale_name:
        sr_parts = scale_range.split("-") if "-" in scale_range else ["0", "5"]
        try:
            sr = {"min": float(sr_parts[0]), "max": float(sr_parts[1])}
        except (ValueError, IndexError):
            sr = {"min": 0, "max": 5}
        scale_items.append({"prompt": scale_desc or scale_name, "metric_name": scale_name, "metric_description": scale_desc, "score_range": sr, "value": None})
    new_id = f"c{len(CRITERIA)+1}"
    CRITERIA.append({
        "id": new_id, "name": name, "type": ctype, "description": desc,
        "creator": "Joanna Qiao", "created_at": datetime.now().strftime("%Y-%m-%d"),
        "form": {
            "type_module": {"items": [type_item]},
            "scale_module": {"items": scale_items},
            "note": note,
        },
    })
    flash(f"\u8bc4\u4ef7\u6807\u51c6\u300c{name}\u300d\u521b\u5efa\u6210\u529f", "success")
    return redirect(url_for("criteria_page"))


@app.route("/criteria/<cid>")
def criteria_detail(cid):
    c = next((x for x in CRITERIA if x["id"] == cid), None)
    if not c:
        flash("\u6807\u51c6\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("criteria_page"))
    ct = CRITERIA_TYPES.get(c["type"], {})
    form = c.get("form", {})

    # Type module visualization
    type_items = form.get("type_module", {}).get("items", [])
    type_section = ""
    for item in type_items:
        if c["type"] == "pass_fail":
            type_section += f'''
            <div style="padding:12px;background:#f6ffed;border:1px solid #b7eb8f;border-radius:8px;margin-bottom:8px;">
              <div style="font-weight:500;margin-bottom:8px;">{item.get("prompt","")}</div>
              <div style="display:flex;gap:12px;">
                <span class="ant-tag ant-tag-green" style="font-size:14px;padding:4px 16px;">\u2713 \u6210\u529f</span>
                <span class="ant-tag ant-tag-red" style="font-size:14px;padding:4px 16px;">\u2717 \u5931\u8d25</span>
              </div>
            </div>'''
        elif c["type"] == "preference":
            type_section += f'''
            <div style="padding:12px;background:#f9f0ff;border:1px solid #d3adf7;border-radius:8px;margin-bottom:8px;">
              <div style="font-weight:500;margin-bottom:8px;">{item.get("prompt","")}</div>
              <div style="display:flex;gap:12px;">
                <span class="ant-tag ant-tag-blue" style="font-size:14px;padding:4px 16px;">Policy A \u66f4\u4f18</span>
                <span class="ant-tag ant-tag-purple" style="font-size:14px;padding:4px 16px;">\u5e73\u5c40 Tie</span>
                <span class="ant-tag ant-tag-gold" style="font-size:14px;padding:4px 16px;">Policy B \u66f4\u4f18</span>
              </div>
            </div>'''
        elif c["type"] == "baseline":
            type_section += f'''
            <div style="padding:12px;background:#fff7e6;border:1px solid #ffd591;border-radius:8px;margin-bottom:8px;">
              <div style="font-weight:500;margin-bottom:8px;">{item.get("prompt","")}</div>
              <div style="display:flex;gap:12px;">
                <span class="ant-tag ant-tag-green" style="font-size:14px;padding:4px 16px;">\u80dc</span>
                <span class="ant-tag" style="font-size:14px;padding:4px 16px;">\u5e73</span>
                <span class="ant-tag ant-tag-red" style="font-size:14px;padding:4px 16px;">\u8d1f</span>
              </div>
            </div>'''
        else:  # scale
            sr = item.get("score_range", {})
            type_section += f'''
            <div style="padding:12px;background:#e6f7ff;border:1px solid #91d5ff;border-radius:8px;margin-bottom:8px;">
              <div style="font-weight:500;">{item.get("prompt","")}</div>
              <div style="font-size:13px;color:rgba(0,0,0,0.45);margin:4px 0;">{item.get("metric_description","")}</div>
              <div style="display:flex;align-items:center;gap:8px;">
                <span>{sr.get("min",0)}</span>
                <div style="flex:1;height:8px;background:#f0f0f0;border-radius:4px;"></div>
                <span>{sr.get("max",5)}</span>
              </div>
            </div>'''

    # Scale module
    scale_items = form.get("scale_module", {}).get("items", [])
    scale_section = ""
    if scale_items:
        for item in scale_items:
            sr = item.get("score_range", {})
            scale_section += f'''
            <div style="padding:12px;background:#e6f7ff;border:1px solid #91d5ff;border-radius:8px;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div style="font-weight:500;">{item.get("prompt","")}</div>
                  <div style="font-size:13px;color:rgba(0,0,0,0.45);">{item.get("metric_description","")}</div>
                </div>
                <span class="ant-tag ant-tag-blue">{sr.get("min",0)} ~ {sr.get("max",1)}</span>
              </div>
            </div>'''

    # Note
    note_section = ""
    if form.get("note"):
        note_section = f'<div style="padding:12px;background:#fafafa;border:1px solid #f0f0f0;border-radius:8px;"><div style="font-size:13px;color:rgba(0,0,0,0.65);">{form["note"]}</div></div>'

    # Pre-compute optional cards
    scale_card = ""
    if scale_items:
        scale_card = f'<div class="ant-card ant-card-bordered" style="margin-bottom:16px;"><div class="ant-card-head" style="padding:12px 20px;"><h3>\u91cf\u8868\u6a21\u5757</h3></div><div class="ant-card-body">{scale_section}</div></div>'
    note_card = ""
    if form.get("note"):
        note_card = f'<div class="ant-card ant-card-bordered"><div class="ant-card-head" style="padding:12px 20px;"><h3>\u5907\u6ce8\u6a21\u5757</h3></div><div class="ant-card-body">{note_section}</div></div>'

    content = f'''
    <div style="margin-bottom:16px;"><a href="/criteria" class="ant-btn">&larr; \u8fd4\u56de\u5217\u8868</a></div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
      <!-- Left: basic info -->
      <div class="ant-card ant-card-bordered">
        <div class="ant-card-head" style="padding:12px 20px;"><h3>\u57fa\u672c\u4fe1\u606f</h3></div>
        <div class="ant-card-body">
          <div style="display:grid;grid-template-columns:80px 1fr;gap:8px 16px;font-size:14px;">
            <span style="color:rgba(0,0,0,0.45);">\u6807\u8bc6</span><span>{c["id"]}</span>
            <span style="color:rgba(0,0,0,0.45);">\u540d\u79f0</span><span style="font-weight:500;">{c["name"]}</span>
            <span style="color:rgba(0,0,0,0.45);">\u7c7b\u578b</span><span><span class="ant-tag ant-tag-{ct.get("color","")}">{ct.get("label","")}</span> {ct.get("desc","")}</span>
            <span style="color:rgba(0,0,0,0.45);">\u63cf\u8ff0</span><span>{c["description"]}</span>
            <span style="color:rgba(0,0,0,0.45);">\u521b\u5efa\u4eba</span><span>{c["creator"]}</span>
            <span style="color:rgba(0,0,0,0.45);">\u65f6\u95f4</span><span>{c["created_at"]}</span>
          </div>
        </div>
      </div>

      <!-- Right: form preview -->
      <div>
        <div class="ant-card ant-card-bordered" style="margin-bottom:16px;">
          <div class="ant-card-head" style="padding:12px 20px;"><h3>\u7c7b\u578b\u6a21\u5757 \u2014 {ct.get("label","")}</h3></div>
          <div class="ant-card-body">{type_section if type_section else "--"}</div>
        </div>
        {scale_card}
        {note_card}
      </div>
    </div>
    '''
    return render_page(f"\u8bc4\u4ef7\u6807\u51c6 - {c['name']}", NOTICE_MVP + content, active="criteria")


# ── Scene Management ──
@app.route("/scenes")
def scenes_page():
    # Build table rows (only 5 fields: name, description, props, images, videos)
    rows = ""
    for sc in SCENES:
        # Props fallback from objects
        props_raw = sc.get("props", "").strip()
        if not props_raw:
            props_raw = "\u3001".join(o.get("name", "") for o in sc.get("objects", []) if o.get("name"))
        prop_tags = ""
        if props_raw:
            for prop in [x.strip() for x in props_raw.replace("\uff0c", ",").replace("\u3001", ",").split(",") if x.strip()][:4]:
                prop_tags += f'<span class="ant-tag">{prop}</span>'
            total_props = len([x for x in props_raw.replace("\uff0c", ",").replace("\u3001", ",").split(",") if x.strip()])
            if total_props > 4:
                prop_tags += f'<span class="ant-tag">+{total_props-4}</span>'
        if not prop_tags:
            prop_tags = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>'

        refs = sc.get("references", {})
        img_count = len(refs.get("images", []))
        vid_count = len(refs.get("capture_videos", [])) + len(refs.get("demo_videos", []))

        view_btn = icon_btn(f"/scenes/{sc['id']}", ICON_VIEW, "\u67e5\u770b", "default")
        copy_btn = icon_btn("#", ICON_COPY, "\u590d\u5236", "default")
        del_btn = icon_btn("#", ICON_DELETE, "\u5220\u9664", "danger")

        rows += (
            "<tr>"
            f'<td style="font-weight:500;">{sc["name"]}</td>'
            f'<td style="max-width:260px;color:rgba(0,0,0,0.65);" title="{sc.get("description","")}"><div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{sc.get("description","--") or "--"}</div></td>'
            f'<td style="max-width:260px;"><div style="display:flex;flex-wrap:wrap;gap:2px;">{prop_tags}</div></td>'
            f'<td style="text-align:center;">{img_count}</td>'
            f'<td style="text-align:center;">{vid_count}</td>'
            f'<td class="actions-cell">{view_btn}{copy_btn}{del_btn}</td>'
            "</tr>"
        )

    content = f'''
    <div class="filter-bar">
      <input type="text" placeholder="\u641c\u7d22\u573a\u666f\u540d\u79f0" style="min-width:180px;">
      <button class="ant-btn" onclick="clearFilters()">\u6e05\u7a7a</button>
      <button class="ant-btn ant-btn-primary" onclick="doSearch()">\u641c\u7d22</button>
      <div style="flex:1;"></div>
      <button class="ant-btn ant-btn-primary" onclick="openModal('create-scene-drawer')">+ \u65b0\u589e\u573a\u666f</button>
    </div>

    <div class="ant-card ant-card-bordered">
      <table class="ant-table">
        <thead><tr>
          <th>\u573a\u666f\u540d\u79f0</th>
          <th>\u573a\u666f\u63cf\u8ff0</th>
          <th>\u4efb\u52a1\u9053\u5177</th>
          <th style="width:80px;text-align:center;">\u573a\u666f\u56fe\u7247</th>
          <th style="width:80px;text-align:center;">\u573a\u666f\u89c6\u9891</th>
          <th style="width:120px;">\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <!-- Create Scene Drawer -->
    <div class="ant-drawer-mask" id="create-scene-drawer">
      <div class="ant-drawer-content">
        <div class="ant-drawer-header"><h3>\u65b0\u589e\u573a\u666f</h3><button class="ant-drawer-close" onclick="closeModal('create-scene-drawer')">&times;</button></div>
        <form method="POST" action="/scenes/create">
        <div class="ant-drawer-body">
          <div class="form-group"><label>\u573a\u666f\u540d\u79f0</label><input type="text" name="name" required></div>
          <div class="form-group"><label>\u573a\u666f\u63cf\u8ff0</label><textarea name="description" rows="3" placeholder="\u63cf\u8ff0\u573a\u666f\u73af\u5883\u3001\u5149\u7167\u6761\u4ef6\u3001\u684c\u9762\u7269\u4f53\u5e03\u7f6e\u7b49\u5173\u952e\u4fe1\u606f"></textarea></div>
          <div class="form-group"><label>\u4efb\u52a1\u9053\u5177</label><input type="text" name="props" placeholder="\u7528\u9017\u53f7\u5206\u9694\uff0c\u5982\uff1a\u7ea2\u8272\u7cd6\u679c\u3001\u84dd\u8272\u6876\u3001\u6728\u52fa"></div>

          <hr style="border:none;border-top:1px solid #f0f0f0;margin:20px 0;">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div>
              <label style="display:block;font-size:14px;color:rgba(0,0,0,0.85);margin-bottom:8px;">\u573a\u666f\u56fe\u7247</label>
              <div class="upload-zone" onclick="this.querySelector('input').click()">
                <input type="file" name="images" multiple accept="image/*" style="display:none;" onchange="window.showFileNames(this)">
                <div class="upload-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#bfbfbf" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg></div>
                <div class="upload-text">\u70b9\u51fb\u6216\u62d6\u62fd\u4e0a\u4f20</div>
                <div class="upload-hint">JPG / PNG\uff0c\u652f\u6301\u591a\u5f20</div>
                <div class="upload-files"></div>
              </div>
            </div>
            <div>
              <label style="display:block;font-size:14px;color:rgba(0,0,0,0.85);margin-bottom:8px;">\u573a\u666f\u89c6\u9891</label>
              <div class="upload-zone" onclick="this.querySelector('input').click()">
                <input type="file" name="videos" multiple accept="video/*" style="display:none;" onchange="window.showFileNames(this)">
                <div class="upload-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#bfbfbf" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg></div>
                <div class="upload-text">\u70b9\u51fb\u6216\u62d6\u62fd\u4e0a\u4f20</div>
                <div class="upload-hint">MP4\uff0c\u652f\u6301\u591a\u4e2a</div>
                <div class="upload-files"></div>
              </div>
            </div>
          </div>
        </div>
        <div class="ant-drawer-footer">
          <button type="button" class="ant-btn" onclick="closeModal('create-scene-drawer')">\u53d6\u6d88</button>
          <button type="submit" class="ant-btn ant-btn-primary">\u521b\u5efa</button>
        </div>
        </form>
      </div>
    </div>
    '''
    return render_page("\u573a\u666f\u7ba1\u7406", content, active="scenes")


@app.route("/scenes/create", methods=["POST"])
def scenes_create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("\u573a\u666f\u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a", "error")
        return redirect(url_for("scenes_page"))
    SCENES.append({
        "id": f"s{len(SCENES)+1}", "name": name,
        "description": request.form.get("description", ""),
        "props": request.form.get("props", ""),
        "creator": "Joanna Qiao", "created_at": datetime.now().strftime("%Y-%m-%d"),
        "environment": {},
        "objects": [],
        "references": {"images": [], "capture_videos": [], "demo_videos": []},
    })
    flash(f"\u573a\u666f\u300c{name}\u300d\u521b\u5efa\u6210\u529f", "success")
    return redirect(url_for("scenes_page"))


@app.route("/scenes/<sid>")
def scene_detail(sid):
    sc = next((x for x in SCENES if x["id"] == sid), None)
    if not sc:
        flash("\u573a\u666f\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("scenes_page"))
    refs = sc.get("references", {})

    # Props fallback
    props_raw = sc.get("props", "").strip()
    if not props_raw:
        props_raw = "\u3001".join(o.get("name", "") for o in sc.get("objects", []) if o.get("name"))
    props_html = ""
    if props_raw:
        for prop in [x.strip() for x in props_raw.replace("\uff0c", ",").replace("\u3001", ",").split(",") if x.strip()]:
            props_html += f'<span class="ant-tag">{prop}</span>'
    if not props_html:
        props_html = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>'

    # Images / videos grids using shared media-card pattern
    imgs_list = refs.get("images", [])
    videos_list = refs.get("capture_videos", []) + refs.get("demo_videos", [])
    _empty = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>'
    if imgs_list:
        img_items = ""
        for i, im in enumerate(imgs_list):
            desc = im.get("description", f"\u56fe\u7247 {i+1}")
            url = im.get("url", "")
            img_items += (
                f'<div class="media-card" onclick="window.openMediaViewer(\'image\', {i!r}, {desc!r}, {url!r})">'
                f'<div class="media-thumb"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#8dcde0" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></div>'
                f'<div class="media-desc">{desc}</div>'
                f'</div>'
            )
        img_html = f'<div class="media-grid">{img_items}</div>'
    else:
        img_html = _empty
    if videos_list:
        vid_items = ""
        for i, v in enumerate(videos_list):
            desc = v.get("description", f"\u89c6\u9891 {i+1}")
            url = v.get("url", "")
            dur = v.get("duration", 0)
            dur_str = f" &middot; {dur}s" if dur else ""
            vid_items += (
                f'<div class="media-card" onclick="window.openMediaViewer(\'video\', {i!r}, {desc!r}, {url!r})">'
                f'<div class="media-thumb media-thumb-video"><svg width="28" height="28" viewBox="0 0 24 24" fill="#1F80A0"><polygon points="6 4 20 12 6 20"/></svg></div>'
                f'<div class="media-desc">{desc}{dur_str}</div>'
                f'</div>'
            )
        vid_html = f'<div class="media-grid">{vid_items}</div>'
    else:
        vid_html = _empty

    scene_title = f"\u573a\u666f - {sc['name']}"
    desc_text = sc.get("description", "").strip() or "\u2014"

    content = f'''
    <div style="margin-bottom:16px;"><a href="/scenes" class="ant-btn">&larr; \u8fd4\u56de\u5217\u8868</a></div>

    <div class="ant-card ant-card-bordered" style="margin-bottom:20px;">
      <div class="ant-card-head" style="padding:12px 20px;"><h3>\u573a\u666f\u4fe1\u606f</h3></div>
      <div class="ant-card-body">
        <div style="display:grid;grid-template-columns:110px 1fr;gap:12px 16px;font-size:14px;align-items:start;margin-bottom:16px;">
          <span style="color:rgba(0,0,0,0.45);">\u573a\u666f\u540d\u79f0</span><span style="font-weight:500;font-size:15px;">{sc["name"]}</span>
          <span style="color:rgba(0,0,0,0.45);">\u573a\u666f\u63cf\u8ff0</span><span style="line-height:1.8;">{desc_text}</span>
          <span style="color:rgba(0,0,0,0.45);">\u4efb\u52a1\u9053\u5177</span><span style="display:flex;flex-wrap:wrap;gap:4px;">{props_html}</span>
          <span style="color:rgba(0,0,0,0.45);">\u521b\u5efa</span><span>{sc.get("creator","")} \u00b7 {sc.get("created_at","")}</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
          <div>
            <div style="font-size:13px;color:rgba(0,0,0,0.45);margin-bottom:8px;">\u573a\u666f\u56fe\u7247</div>
            {img_html}
          </div>
          <div>
            <div style="font-size:13px;color:rgba(0,0,0,0.45);margin-bottom:8px;">\u573a\u666f\u89c6\u9891</div>
            {vid_html}
          </div>
        </div>
      </div>
    </div>
    '''
    return render_page(scene_title, content, active="scenes")


# ── Benchmark Management ──
@app.route("/benchmarks")
def benchmarks_page():
    rows = ""
    for b in BENCHMARKS:
        cr = get_criterion(b.get("criteria_id", ""))
        cr_name = cr["name"] if cr else "--"
        cr_type = CRITERIA_TYPES.get(cr["type"], {}) if cr else {}
        prompt_count = len(b.get("prompt_ids", []))
        prompt_tags = ""
        for pid in b.get("prompt_ids", [])[:3]:
            p = get_prompt(pid)
            if p:
                prompt_tags += f'<span class="ant-tag" style="margin-right:2px;">{p["high_level"][:8]}</span>'
        if prompt_count > 3:
            prompt_tags += f'<span class="ant-tag">+{prompt_count-3}</span>'

        view_btn = icon_btn(f"/benchmarks/{b['id']}", ICON_VIEW, "\u67e5\u770b", "default")
        copy_btn = icon_btn("#", ICON_COPY, "\u590d\u5236", "default")
        del_btn = icon_btn("#", ICON_DELETE, "\u5220\u9664", "danger")

        rows += (
            "<tr>"
            f'<td style="font-weight:500;">{b["name"]}</td>'
            f"<td>{prompt_tags}</td>"
            f'<td><span class="ant-tag ant-tag-{cr_type.get("color","")}">{cr_name}</span></td>'
            f"<td>{b['creator']}</td>"
            f"<td>{b['created_at']}</td>"
            f'<td class="actions-cell">{view_btn}{copy_btn}{del_btn}</td>'
            "</tr>"
        )

    # Build select options
    scene_opts = "".join(f'<option value="{s["id"]}">{s["name"]}</option>' for s in SCENES)
    criteria_opts = "".join(f'<option value="{c["id"]}">{c["name"]} ({CRITERIA_TYPES.get(c["type"],{}).get("label","")})</option>' for c in CRITERIA)
    prompt_opts = "".join(f'<option value="{p["id"]}">{p["high_level"]}</option>' for p in PROMPTS)
    # Mselsync pattern for benchmarks create
    bm_create_prompt_ms_opts = "".join(
        f'<label class="er-opt"><input type="checkbox" value="{p["id"]}" data-name="{p["high_level"]}" onchange="mselSync(\'ms-bm-prompts\')"> <span>{p["high_level"]} &middot; {len(p.get("low_levels", []))} \u6b65</span></label>'
        for p in PROMPTS
    )
    bm_create_criteria_single_opts = "".join(
        f'<option value="{c["id"]}"{" selected" if c["id"] == "c1" else ""}>{c["name"]} ({CRITERIA_TYPES.get(c["type"],{}).get("label","")})</option>'
        for c in CRITERIA
    )

    content = f'''
    <div class="filter-bar">
      <input type="text" placeholder="\u641c\u7d22 Benchmark" style="min-width:180px;">
      <input type="text" placeholder="\u641c\u7d22\u63d0\u793a\u8bcd\uff08\u6a21\u7cca\u5339\u914d\uff09" style="min-width:200px;">
      <button class="ant-btn" onclick="clearFilters()">\u6e05\u7a7a</button>
      <button class="ant-btn ant-btn-primary" onclick="doSearch()">\u641c\u7d22</button>
      <div style="flex:1;"></div>
      <button class="ant-btn ant-btn-primary" onclick="openModal('create-bm-drawer')">+ \u65b0\u589e Benchmark</button>
    </div>

    <div class="ant-card ant-card-bordered">
      <table class="ant-table">
        <thead><tr>
          <th>\u540d\u79f0</th><th>\u63d0\u793a\u8bcd</th><th>\u8bc4\u4ef7\u6807\u51c6</th><th>\u521b\u5efa\u4eba</th><th>\u521b\u5efa\u65f6\u95f4</th><th>\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <!-- Create Benchmark Drawer -->
    <div class="ant-drawer-mask" id="create-bm-drawer">
      <div class="ant-drawer-content">
        <div class="ant-drawer-header"><h3>\u65b0\u589e Benchmark</h3><button class="ant-drawer-close" onclick="closeModal('create-bm-drawer')">&times;</button></div>
        <form method="POST" action="/benchmarks/create">
        <div class="ant-drawer-body">
          <!-- Section 1: Basic Info -->
          <h4 style="font-size:14px;font-weight:500;margin-bottom:12px;color:rgba(0,0,0,0.85);">\u57fa\u672c\u4fe1\u606f</h4>
          <div class="form-group"><label>\u540d\u79f0</label><input type="text" name="name" required></div>
          <div class="form-group"><label>\u63cf\u8ff0</label><textarea name="description" rows="2"></textarea></div>

          <hr style="border:none;border-top:1px solid #f0f0f0;margin:20px 0;">

          <!-- Section 2: Scene Config -->
          <h4 style="font-size:14px;font-weight:500;margin-bottom:12px;color:rgba(0,0,0,0.85);">\u573a\u666f\u914d\u7f6e</h4>
          <div class="form-group" style="margin-bottom:16px;">
            <label>\u573a\u666f\u63cf\u8ff0</label>
            <textarea name="scene_description" rows="3" placeholder="\u63cf\u8ff0\u573a\u666f\u73af\u5883\u3001\u5149\u7167\u6761\u4ef6\u3001\u684c\u9762\u7269\u4f53\u5e03\u7f6e\u7b49\u5173\u952e\u4fe1\u606f"></textarea>
          </div>
          <div class="form-group" style="margin-bottom:16px;">
            <label>\u4efb\u52a1\u9053\u5177</label>
            <input type="text" name="props" placeholder="\u7528\u9017\u53f7\u5206\u9694\uff0c\u5982\uff1a\u7ea2\u8272\u7cd6\u679c\u3001\u84dd\u8272\u6876\u3001\u6728\u52fa">
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
            <div>
              <label style="display:block;font-size:14px;color:rgba(0,0,0,0.85);margin-bottom:8px;">\u573a\u666f\u56fe\u7247</label>
              <div class="upload-zone" onclick="this.querySelector('input').click()">
                <input type="file" name="scene_images" multiple accept="image/*" style="display:none;" onchange="window.showFileNames(this)">
                <div class="upload-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#bfbfbf" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg></div>
                <div class="upload-text">\u70b9\u51fb\u6216\u62d6\u62fd\u4e0a\u4f20</div>
                <div class="upload-hint">JPG / PNG\uff0c\u652f\u6301\u591a\u5f20</div>
                <div class="upload-files"></div>
              </div>
            </div>
            <div>
              <label style="display:block;font-size:14px;color:rgba(0,0,0,0.85);margin-bottom:8px;">\u573a\u666f\u89c6\u9891</label>
              <div class="upload-zone" onclick="this.querySelector('input').click()">
                <input type="file" name="scene_videos" multiple accept="video/*" style="display:none;" onchange="window.showFileNames(this)">
                <div class="upload-icon"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#bfbfbf" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg></div>
                <div class="upload-text">\u70b9\u51fb\u6216\u62d6\u62fd\u4e0a\u4f20</div>
                <div class="upload-hint">MP4\uff0c\u73b0\u573a\u73af\u5883\u5b9e\u62cd</div>
                <div class="upload-files"></div>
              </div>
            </div>
          </div>

          <hr style="border:none;border-top:1px solid #f0f0f0;margin:20px 0;">

          <!-- Section 3: Related Config -->
          <h4 style="font-size:14px;font-weight:500;margin-bottom:12px;color:rgba(0,0,0,0.85);">\u5173\u8054\u914d\u7f6e</h4>
          <div class="form-group" style="margin-bottom:16px;">
            <label>\u63d0\u793a\u8bcd</label>
            <div style="position:relative;">
              <div class="er-dd-trigger" id="ms-bm-prompts-btn" onclick="mselToggle('ms-bm-prompts', event)">
                <div id="ms-bm-prompts-chips" class="er-chips"></div>
                <span style="margin-left:auto;color:rgba(0,0,0,0.35);font-size:10px;flex-shrink:0;padding-left:4px;">&#9660;</span>
              </div>
              <div class="er-dd-panel" id="ms-bm-prompts-panel" style="width:100%;">
                <div style="padding:8px 12px;border-bottom:1px solid #f0f0f0;display:flex;gap:16px;align-items:center;">
                  <a href="javascript:;" onclick="mselToggleAll('ms-bm-prompts', true)" style="font-size:12px;color:#1F80A0;">\u5168\u9009</a>
                  <a href="javascript:;" onclick="mselToggleAll('ms-bm-prompts', false)" style="font-size:12px;color:rgba(0,0,0,0.45);">\u6e05\u7a7a</a>
                </div>
                <div style="max-height:240px;overflow-y:auto;padding:6px 0;">
                  {bm_create_prompt_ms_opts}
                </div>
              </div>
              <input type="hidden" name="prompt_ids" id="ms-bm-prompts-hidden" value="">
            </div>
          </div>
          <div class="form-group">
            <label>\u8bc4\u4ef7\u6807\u51c6</label>
            <select name="criteria_id" class="has-value">{bm_create_criteria_single_opts}</select>
          </div>
        </div>
        <div class="ant-drawer-footer">
          <button type="button" class="ant-btn" onclick="closeModal('create-bm-drawer')">\u53d6\u6d88</button>
          <button type="submit" class="ant-btn ant-btn-primary">\u521b\u5efa</button>
        </div>
        </form>
      </div>
    </div>
    '''
    return render_page("Benchmark \u7ba1\u7406", content, active="benchmarks")


@app.route("/benchmarks/create", methods=["POST"])
def benchmarks_create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Benchmark \u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a", "error")
        return redirect(url_for("benchmarks_page"))
    BENCHMARKS.append({
        "id": f"b{len(BENCHMARKS)+1}",
        "name": name,
        "description": request.form.get("description", ""),
        "scene_description": request.form.get("scene_description", ""),
        "props": request.form.get("props", ""),
        "prompt_ids": [x.strip() for x in request.form.get("prompt_ids", "").split(",") if x.strip()],
        "criteria_id": request.form.get("criteria_id", "c1"),
        "creator": "Joanna Qiao",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    })
    flash(f"Benchmark\u300c{name}\u300d\u521b\u5efa\u6210\u529f", "success")
    return redirect(url_for("benchmarks_page"))


@app.route("/benchmarks/<bid>")
def benchmark_detail(bid):
    b = next((x for x in BENCHMARKS if x["id"] == bid), None)
    if not b:
        flash("Benchmark \u4e0d\u5b58\u5728", "error")
        return redirect(url_for("benchmarks_page"))
    sc = get_scene(b.get("scene_id", ""))
    cr = get_criterion(b.get("criteria_id", ""))
    cr_type = CRITERIA_TYPES.get(cr["type"], {}) if cr else {}

    # Scene card
    scene_card = "--"
    if sc:
        env = sc.get("environment", {})
        ws = env.get("workspace", {})
        scene_card = (
            f'<span style="font-weight:500;">{sc["name"]}</span>'
            f' <span class="ant-tag ant-tag-cyan">{env.get("type","")}</span>'
            f'<div style="font-size:13px;color:rgba(0,0,0,0.45);margin-top:4px;">'
            f'{ws.get("length",0)} x {ws.get("width",0)} x {ws.get("height",0)} cm'
            f' | {env.get("conditions",{}).get("lighting","")}</div>'
        )

    # Criteria card
    criteria_card = "--"
    if cr:
        criteria_card = (
            f'<span style="font-weight:500;">{cr["name"]}</span>'
            f' <span class="ant-tag ant-tag-{cr_type.get("color","")}">{cr_type.get("label","")}</span>'
            f'<div style="font-size:13px;color:rgba(0,0,0,0.45);margin-top:4px;">{cr["description"][:60]}</div>'
        )

    # Prompts as expandable tree
    prompt_rows = ""
    for pi, pid in enumerate(b.get("prompt_ids", [])):
        p = get_prompt(pid)
        if not p:
            continue
        lls = p.get("low_levels", [])
        child_count = len(lls)
        agg = prompt_aggregated_labels(p)
        tag_html = " ".join(render_tag(t) for t in agg[:3])
        if len(agg) > 3:
            tag_html += f' <span class="ant-tag">+{len(agg)-3}</span>'
        enabled_tag = '<span class="ant-tag ant-tag-green">\u5df2\u542f\u7528</span>' if p.get("enabled") else '<span class="ant-tag">\u672a\u542f\u7528</span>'
        uid = f"bm-prompt-{pi}"
        # Parent row
        prompt_rows += (
            f'<tr style="cursor:pointer;" onclick="var rows=document.querySelectorAll(\'.{uid}\');var a=this.querySelector(\'.bm-arrow\');var show=rows[0]&&rows[0].style.display===\'none\';rows.forEach(function(r){{r.style.display=show?\'\':\'none\';}});a.style.transform=show?\'rotate(90deg)\':\'\';">'
            f'<td><span class="bm-arrow" style="display:inline-block;font-size:10px;color:rgba(0,0,0,0.3);transition:transform 0.2s;margin-right:6px;">&#9654;</span><span style="font-weight:500;">{p["high_level"]}</span></td>'
            f"<td>{p['high_level_en']}</td>"
            f"<td>{child_count}</td>"
            f"<td>{tag_html}</td>"
            f"<td>{enabled_tag}</td>"
            "</tr>"
        )
        # Child rows (hidden)
        for si, ll in enumerate(lls):
            ll_tags = " ".join(render_tag(t) for t in ll.get("labels", [])[:2])
            prompt_rows += (
                f'<tr class="{uid}" style="display:none;">'
                f'<td style="padding-left:28px;color:rgba(0,0,0,0.45);">{si+1}. {ll["zh"]}</td>'
                f'<td style="color:rgba(0,0,0,0.45);">{ll["en"]}</td>'
                f'<td></td>'
                f'<td>{ll_tags}</td>'
                f'<td></td>'
                f'</tr>'
            )

    bm_title = f"Benchmark - {b['name']}"

    # Scene description fallback: use explicit field if present, else derive from linked scene
    scene_desc = b.get("scene_description", "").strip()
    if not scene_desc and sc:
        env = sc.get("environment", {})
        ws = env.get("workspace", {})
        scene_desc = f'{sc.get("description","")} \u00b7 \u5de5\u4f5c\u533a {ws.get("length",0)}x{ws.get("width",0)}x{ws.get("height",0)}cm \u00b7 {env.get("conditions",{}).get("lighting","")}'
    scene_desc_html = scene_desc if scene_desc else '<span style="color:rgba(0,0,0,0.25);">\u2014</span>'

    props_raw = b.get("props", "").strip()
    if not props_raw and sc:
        objs = sc.get("objects", [])
        props_raw = "\u3001".join(o.get("name", "") for o in objs if o.get("name"))
    props_html = ""
    if props_raw:
        for prop in [x.strip() for x in props_raw.replace("\uff0c", ",").replace("\u3001", ",").split(",") if x.strip()]:
            props_html += f'<span class="ant-tag">{prop}</span>'
    if not props_html:
        props_html = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>'

    # Images/videos from scene references
    _refs_full = sc.get("references", {}) if sc else {}
    imgs_list = _refs_full.get("images", [])
    videos_list = _refs_full.get("capture_videos", []) + _refs_full.get("demo_videos", [])
    _empty = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>'
    # Build clickable image grid
    if imgs_list:
        img_items = ""
        for i, im in enumerate(imgs_list):
            desc = im.get("description", f"\u56fe\u7247 {i+1}")
            url = im.get("url", "")
            img_items += (
                f'<div class="media-card" onclick="openMediaViewer(\'image\', {i!r}, {desc!r}, {url!r})">'
                f'<div class="media-thumb"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#8dcde0" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></div>'
                f'<div class="media-desc">{desc}</div>'
                f'</div>'
            )
        img_html = f'<div class="media-grid">{img_items}</div>'
    else:
        img_html = _empty
    # Build clickable video list
    if videos_list:
        vid_items = ""
        for i, v in enumerate(videos_list):
            desc = v.get("description", f"\u89c6\u9891 {i+1}")
            url = v.get("url", "")
            dur = v.get("duration", 0)
            dur_str = f" &middot; {dur}s" if dur else ""
            vid_items += (
                f'<div class="media-card" onclick="openMediaViewer(\'video\', {i!r}, {desc!r}, {url!r})">'
                f'<div class="media-thumb media-thumb-video"><svg width="28" height="28" viewBox="0 0 24 24" fill="#1F80A0"><polygon points="6 4 20 12 6 20"/></svg></div>'
                f'<div class="media-desc">{desc}{dur_str}</div>'
                f'</div>'
            )
        vid_html = f'<div class="media-grid">{vid_items}</div>'
    else:
        vid_html = _empty

    # Criteria info
    if cr:
        criteria_html = f'<span style="font-weight:500;">{cr["name"]}</span> <span class="ant-tag ant-tag-{cr_type.get("color","")}">{cr_type.get("label","")}</span>'
    else:
        criteria_html = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>'
    description_html = b["description"] if b.get("description") else "\u2014"

    content = f'''
    <div style="margin-bottom:16px;"><a href="/benchmarks" class="ant-btn">&larr; \u8fd4\u56de\u5217\u8868</a></div>

    <!-- Section 1: Basic Info -->
    <div class="ant-card ant-card-bordered" style="margin-bottom:20px;">
      <div class="ant-card-head" style="padding:12px 20px;"><h3>\u57fa\u672c\u4fe1\u606f</h3></div>
      <div class="ant-card-body">
        <div style="display:grid;grid-template-columns:110px 1fr;gap:10px 16px;font-size:14px;">
          <span style="color:rgba(0,0,0,0.45);">\u540d\u79f0</span><span style="font-weight:500;font-size:15px;">{b["name"]}</span>
          <span style="color:rgba(0,0,0,0.45);">\u63cf\u8ff0</span><span>{description_html}</span>
          <span style="color:rgba(0,0,0,0.45);">\u521b\u5efa</span><span>{b["creator"]} \u00b7 {b["created_at"]}</span>
        </div>
      </div>
    </div>

    <!-- Section 2: Scene Config -->
    <div class="ant-card ant-card-bordered" style="margin-bottom:20px;">
      <div class="ant-card-head" style="padding:12px 20px;"><h3>\u573a\u666f\u914d\u7f6e</h3></div>
      <div class="ant-card-body">
        <div style="display:grid;grid-template-columns:110px 1fr;gap:12px 16px;font-size:14px;align-items:start;margin-bottom:16px;">
          <span style="color:rgba(0,0,0,0.45);">\u573a\u666f\u63cf\u8ff0</span>
          <span style="line-height:1.8;">{scene_desc_html}</span>
          <span style="color:rgba(0,0,0,0.45);">\u4efb\u52a1\u9053\u5177</span>
          <span style="display:flex;flex-wrap:wrap;gap:4px;">{props_html}</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
          <div>
            <div style="font-size:13px;color:rgba(0,0,0,0.45);margin-bottom:8px;">\u573a\u666f\u56fe\u7247</div>
            {img_html}
          </div>
          <div>
            <div style="font-size:13px;color:rgba(0,0,0,0.45);margin-bottom:8px;">\u573a\u666f\u89c6\u9891</div>
            {vid_html}
          </div>
        </div>
      </div>
    </div>

    <!-- Section 3: Related Config -->
    <div class="ant-card ant-card-bordered" style="margin-bottom:20px;">
      <div class="ant-card-head" style="padding:12px 20px;"><h3>\u5173\u8054\u914d\u7f6e</h3></div>
      <div class="ant-card-body">
        <div style="display:grid;grid-template-columns:110px 1fr;gap:14px 16px;font-size:14px;align-items:start;">
          <span style="color:rgba(0,0,0,0.45);">\u8bc4\u4ef7\u6807\u51c6</span>
          <span>{criteria_html}</span>
          <span style="color:rgba(0,0,0,0.45);">\u63d0\u793a\u8bcd ({len(b.get("prompt_ids",[]))} \u7ec4)</span>
          <div>
            <table class="ant-table" style="margin-top:-4px;">
              <thead><tr><th>\u4efb\u52a1\u63d0\u793a\u8bcd</th><th>Task Prompt</th><th>\u5b50\u6b65\u9aa4</th><th>\u6807\u7b7e</th><th>\u72b6\u6001</th></tr></thead>
              <tbody>{prompt_rows}</tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    '''
    return render_page(bm_title, content, active="benchmarks")


# ── Evaluation Task Management ──
@app.route("/tasks")
def tasks_page():
    rows = ""
    for t in EVAL_TASKS:
        bm = get_benchmark(t["benchmark_id"])
        bm_name = bm["name"] if bm else "--"
        et = CRITERIA_TYPES.get(t.get("eval_type", ""), {})
        et_label = et.get("label", "--") if et else "--"
        model_text = ", ".join(get_model_name(mid) for mid in t["model_ids"])

        # Status
        status_colors = {"\u672a\u5f00\u59cb": "", "\u91c7\u96c6\u4e2d": "processing", "\u8bc4\u6d4b\u4e2d": "processing", "\u8bc4\u6d4b\u5b8c\u6210": "", "\u5206\u6790\u5b8c\u6210": "", "\u5df2\u6682\u505c": "", "\u5df2\u5e9f\u5f03": ""}
        s_color = status_colors.get(t["status"], "")
        status_tag = f'<span class="ant-tag ant-tag-{s_color}">{t["status"]}</span>' if s_color else f'<span class="ant-tag">{t["status"]}</span>'

        # Priority
        pri = PRIORITY_MAP.get(t.get("priority", "\u4e2d"), {})
        pri_tag = f'<span class="ant-tag ant-tag-{pri.get("color","")}">{pri.get("label","")}</span>' if pri.get("color") else f'<span class="ant-tag">{pri.get("label",t["priority"])}</span>'

        # Dual progress bars: collect + eval
        total = max(t.get("total_sessions", 1), 1)
        c_done = t.get("collect_done", 0)
        e_done = t.get("eval_done", 0)
        c_pct = round(c_done / total * 100)
        e_pct = round(e_done / total * 100)
        progress_html = (
            f'<div style="font-size:12px;line-height:1.8;">'
            f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<span style="color:rgba(0,0,0,0.45);min-width:24px;">\u91c7\u96c6</span>'
            f'<div style="flex:1;height:14px;background:#f0f0f0;border-radius:7px;overflow:hidden;position:relative;">'
            f'<div style="width:{c_pct}%;height:100%;background:#1F80A0;border-radius:7px;"></div>'
            f'<span class="pb-text" style="--pct:{c_pct}%;">{c_done}/{total}</span>'
            f'</div></div>'
            f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<span style="color:rgba(0,0,0,0.45);min-width:24px;">\u8bc4\u6d4b</span>'
            f'<div style="flex:1;height:14px;background:#f0f0f0;border-radius:7px;overflow:hidden;position:relative;">'
            f'<div style="width:{e_pct}%;height:100%;background:#1F80A0;border-radius:7px;"></div>'
            f'<span class="pb-text" style="--pct:{e_pct}%;">{e_done}/{total}</span>'
            f'</div></div>'
            f'</div>'
        )

        # Actions per status
        view_btn = icon_btn(f'/tasks/{t["id"]}', ICON_VIEW, "\u67e5\u770b", "default")
        data_btn = icon_btn(f'/eval-records?view=task&task={t["id"]}', ICON_DATA, "\u67e5\u770b\u6570\u636e", "default")
        st = t["status"]
        action_btns = view_btn + data_btn
        if st == "\u672a\u5f00\u59cb":
            action_btns += icon_btn(f'/tasks/{t["id"]}/delete', ICON_DELETE, "\u5220\u9664", "danger")
        elif st in ("\u91c7\u96c6\u4e2d", "\u8bc4\u6d4b\u4e2d"):
            action_btns += icon_btn(f'/tasks/{t["id"]}/pause', ICON_DISABLE, "\u6682\u505c", "default")
        elif st == "\u8bc4\u6d4b\u5b8c\u6210":
            action_btns += icon_btn(f'/tasks/{t["id"]}/analyze', ICON_ANALYZE, "\u5206\u6790", "primary")
        elif st == "\u5df2\u6682\u505c":
            action_btns += icon_btn(f'/tasks/{t["id"]}/delete', ICON_DELETE, "\u5220\u9664", "danger")

        # Enable switch: ON for started tasks, clickable only when 未开始
        is_enabled = st != "\u672a\u5f00\u59cb"
        if st == "\u672a\u5f00\u59cb":
            switch_html = f'<a href="/tasks/{t["id"]}/start" title="\u70b9\u51fb\u5f00\u542f" style="text-decoration:none;"><label class="capsule" style="cursor:pointer;"><span class="capsule-dot"></span></label></a>'
        elif st == "\u5df2\u5e9f\u5f03":
            switch_html = '<label class="capsule" style="opacity:0.3;cursor:not-allowed;"><span class="capsule-dot"></span></label>'
        else:
            switch_html = '<label class="capsule on" style="cursor:default;"><span class="capsule-dot"></span></label>'

        task_no = t.get("task_no", "")
        rows += (
            "<tr>"
            f'<td style="font-size:13px;color:rgba(0,0,0,0.45);">{task_no}</td>'
            f'<td style="font-weight:500;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{t["name"]}">{t["name"]}</td>'
            f"<td>{bm_name}</td>"
            f'<td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{model_text}">{model_text}</td>'
            f"<td style='text-align:center;'>{switch_html}</td>"
            f"<td>{status_tag}</td>"
            f"<td style='min-width:160px;'>{progress_html}</td>"
            f"<td>{pri_tag}</td>"
            f"<td>{t['created_by']}</td>"
            f'<td class="actions-cell">{action_btns}</td>'
            "</tr>"
        )

    # Pre-build select options
    bm_opts = '<option value="">\u8bf7\u9009\u62e9 Benchmark</option>' + "".join(f'<option value="{b["id"]}">{b["name"]}</option>' for b in BENCHMARKS)
    model_opts = "".join(f'<option value="{m["id"]}">{m["name"]} ({m["version"]})</option>' for m in MODELS)
    type_opts = "".join(f'<option value="{k}">{v["label"]}</option>' for k, v in CRITERIA_TYPES.items())
    # For inline benchmark section: prompts / criteria / tag-tree
    bm_prompt_ms_opts = "".join(
        f'<label class="er-opt"><input type="checkbox" value="{p["id"]}" data-name="{p["high_level"]}" onchange="mselSync(\'ms-prompts\')"> <span>{p["high_level"]} &middot; {len(p.get("low_levels", []))} \u6b65</span></label>'
        for p in PROMPTS
    )
    bm_criteria_opts = '<option value="">\u8bf7\u9009\u62e9</option>' + "".join(f'<option value="{c["id"]}">{c["name"]} ({CRITERIA_TYPES.get(c["type"],{}).get("label","")})</option>' for c in CRITERIA)

    # Build benchmark preview data for JS
    import json as _json
    bm_preview = {}
    for b in BENCHMARKS:
        sc = get_scene(b.get("scene_id", ""))
        prompts_info = []
        for pid in b.get("prompt_ids", []):
            p = get_prompt(pid)
            if p:
                prompts_info.append({
                    "name": p["high_level"],
                    "steps": len(p.get("low_levels", [])),
                    "low_levels": [{"zh": ll.get("zh", ""), "en": ll.get("en", "")} for ll in p.get("low_levels", [])],
                })
        cr = get_criterion(b.get("criteria_id", ""))
        cr_info = ""
        if cr:
            ct = CRITERIA_TYPES.get(cr["type"], {})
            cr_info = f'{cr["name"]} ({ct.get("label", "")})'
        # Scene description fallback from linked scene
        _scene_desc = b.get("scene_description", "").strip()
        if not _scene_desc and sc:
            _env = sc.get("environment", {})
            _ws = _env.get("workspace", {})
            _scene_desc = f'{sc.get("description","")} \u00b7 \u5de5\u4f5c\u533a {_ws.get("length",0)}x{_ws.get("width",0)}x{_ws.get("height",0)}cm \u00b7 {_env.get("conditions",{}).get("lighting","")}'
        # Props fallback
        _props = b.get("props", "").strip()
        if not _props and sc:
            _props = "\u3001".join(o.get("name", "") for o in sc.get("objects", []) if o.get("name"))
        _refs = sc.get("references", {}) if sc else {}
        _imgs = [{"url": x.get("url", ""), "description": x.get("description", "")} for x in _refs.get("images", [])]
        _caps = [{"url": x.get("url", ""), "description": x.get("description", ""), "duration": x.get("duration", 0)} for x in _refs.get("capture_videos", [])]
        _demos = [{"url": x.get("url", ""), "description": x.get("description", ""), "duration": x.get("duration", 0)} for x in _refs.get("demo_videos", [])]
        bm_preview[b["id"]] = {
            "id": b["id"],
            "name": b.get("name", ""),
            "description": b.get("description", ""),
            "scene": sc["name"] if sc else "--",
            "scene_type": sc.get("environment", {}).get("type", "") if sc else "",
            "scene_description": _scene_desc,
            "props": _props,
            "images": _imgs,
            "videos": _caps + _demos,
            "criteria": cr_info,
            "prompts": prompts_info,
            "creator": b.get("creator", ""),
            "created_at": b.get("created_at", ""),
        }
    bm_preview_json = _json.dumps(bm_preview, ensure_ascii=False)

    # Tag tree selector for task labels
    task_tag_tree = build_tree_selector_html("task-tags")

    # Checkpoint options (mselSync pattern)
    ckpt_ms_opts = "".join(
        f'<label class="er-opt"><input type="checkbox" value="{m["id"]}" data-name="{m["name"]}" onchange="mselSync(\'ms-ckpt\')"> <span>{m["name"]} <span style="color:rgba(0,0,0,0.35);">{m["version"]}</span></span></label>'
        for m in MODELS
    )
    type_filter_opts = "".join(f'<option value="{k}">{v["label"]}</option>' for k, v in CRITERIA_TYPES.items())
    bm_filter_opts = "".join(f'<option>{b["name"]}</option>' for b in BENCHMARKS)
    model_filter_opts = "".join(f'<option>{m["name"]}</option>' for m in MODELS)

    cnt_collecting = sum(1 for t in EVAL_TASKS if t["status"] == "\u91c7\u96c6\u4e2d")
    cnt_evaluating = sum(1 for t in EVAL_TASKS if t["status"] == "\u8bc4\u6d4b\u4e2d")
    cnt_done = sum(1 for t in EVAL_TASKS if t["status"] in ("\u8bc4\u6d4b\u5b8c\u6210", "\u5206\u6790\u5b8c\u6210"))

    content = f'''
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-label">\u603b\u4efb\u52a1\u6570</div><div class="stat-value">{len(EVAL_TASKS)}</div></div>
      <div class="stat-card"><div class="stat-label">\u91c7\u96c6\u4e2d</div><div class="stat-value" style="color:#1F80A0;">{cnt_collecting}</div></div>
      <div class="stat-card"><div class="stat-label">\u8bc4\u6d4b\u4e2d</div><div class="stat-value" style="color:#1F80A0;">{cnt_evaluating}</div></div>
      <div class="stat-card"><div class="stat-label">\u5df2\u5b8c\u6210</div><div class="stat-value" style="color:#1F80A0;">{cnt_done}</div></div>
    </div>

    <div class="filter-bar">
      <input type="text" placeholder="\u641c\u7d22\u4efb\u52a1" style="min-width:140px;">
      <select style="min-width:120px;"><option value="">Benchmark</option>{bm_filter_opts}</select>
      <select style="min-width:110px;"><option value="">Checkpoint</option>{model_filter_opts}</select>
      <select style="min-width:100px;"><option value="">\u5168\u90e8\u72b6\u6001</option><option>\u672a\u5f00\u59cb</option><option>\u91c7\u96c6\u4e2d</option><option>\u8bc4\u6d4b\u4e2d</option><option>\u8bc4\u6d4b\u5b8c\u6210</option><option>\u5206\u6790\u5b8c\u6210</option><option>\u5df2\u6682\u505c</option><option>\u5df2\u5e9f\u5f03</option></select>
      <select style="min-width:80px;"><option value="">\u4f18\u5148\u7ea7</option><option>\u9ad8</option><option>\u4e2d</option><option>\u4f4e</option></select>
      <button class="ant-btn" onclick="clearFilters()">\u6e05\u7a7a</button>
      <button class="ant-btn ant-btn-primary" onclick="doSearch()">\u641c\u7d22</button>
      <div style="flex:1;"></div>
      <button class="ant-btn ant-btn-primary" onclick="openModal('create-task-drawer')">+ \u65b0\u589e\u8bc4\u6d4b\u4efb\u52a1</button>
    </div>

    <div class="ant-card ant-card-bordered">
      <table class="ant-table">
        <thead><tr>
          <th style="width:50px;">ID</th><th>\u4efb\u52a1\u540d\u79f0</th><th>Benchmark</th><th>Checkpoint</th><th>\u542f\u7528</th><th>\u72b6\u6001</th><th>\u8fdb\u5ea6</th><th>\u4f18\u5148\u7ea7</th><th>\u521b\u5efa\u4eba</th><th>\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <!-- Create Task Drawer -->
    <div class="ant-drawer-mask" id="create-task-drawer">
      <div class="ant-drawer-content">
        <div class="ant-drawer-header"><h3>\u65b0\u589e\u8bc4\u6d4b\u4efb\u52a1</h3><button class="ant-drawer-close" onclick="closeModal('create-task-drawer')">&times;</button></div>
        <form method="POST" action="/tasks/create" onsubmit="return validateTaskForm()">
        <div class="ant-drawer-body">
          <!-- Section 1: Basic Info -->
          <h4 style="font-size:14px;font-weight:500;margin-bottom:12px;color:rgba(0,0,0,0.85);">\u57fa\u7840\u4fe1\u606f</h4>
          <div class="form-row">
            <div class="form-group"><label class="req">\u4efb\u52a1\u540d\u79f0</label><div class="input-clear-wrap"><input type="text" name="name" required><span class="input-clear" onclick="this.previousElementSibling.value=''">&times;</span></div></div>
            <div class="form-group"><label class="req">\u5411\u8bc4\u6d4b\u5458\u5c55\u793a\u540d\u79f0</label><div class="input-clear-wrap"><input type="text" name="display_name" required placeholder="\u5efa\u8bae\u4e0d\u8981\u5305\u542b\u6a21\u578b\u4fe1\u606f"><span class="input-clear" onclick="this.previousElementSibling.value=''">&times;</span></div></div>
            <div class="form-group"><label class="req">\u6240\u5c5e\u9879\u76ee</label><select name="project" required><option value="">\u8bf7\u9009\u62e9</option><option>\u57fa\u7840\u7814\u7a76</option><option>\u5b81\u5fb7\u5e94\u7528</option><option>moz1</option><option>spirit</option><option>demo\u91c7\u96c6</option><option>\u9884\u8bad\u7ec3\u91c7\u96c6</option><option>\u591a\u4efb\u52a1</option></select></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label class="req">\u91c7\u96c6\u7c7b\u578b</label><input type="text" value="test" disabled style="background:#f5f5f5;color:rgba(0,0,0,0.45);"></div>
            <div class="form-group"><label class="req">\u4f18\u5148\u7ea7</label><select name="priority" required><option value="">\u8bf7\u9009\u62e9</option><option value="\u9ad8">\u9ad8</option><option value="\u4e2d" selected>\u4e2d</option><option value="\u4f4e">\u4f4e</option></select></div>
            <div class="form-group"><label class="req">\u9884\u671f\u4ea4\u4ed8\u65e5\u671f</label><div class="input-clear-wrap"><input type="date" name="due_date" required style="width:100%;"><span class="input-clear" onclick="this.previousElementSibling.value=''">&times;</span></div></div>
          </div>
          <div class="form-group">
            <label class="req">\u4efb\u52a1\u6807\u7b7e (\u591a\u9009)</label>
            <div class="ts-wrap" id="ts-task-tags" style="max-width:100%;">
              <div class="ts-trigger" onclick="tsToggle('ts-task-tags')" style="min-height:36px;"><span class="ts-placeholder">\u9009\u62e9\u6807\u7b7e</span></div>
              <div class="ts-panel" style="max-height:280px;">{task_tag_tree}</div>
              <input type="hidden" name="task_tags" id="task-tags-hidden" value="">
            </div>
          </div>
          <div class="form-group"><label>\u4efb\u52a1\u63cf\u8ff0</label><textarea name="description" rows="2" placeholder="\u7b80\u8981\u63cf\u8ff0\u8be5\u4efb\u52a1\u7684\u76ee\u7684\u3001\u5173\u6ce8\u70b9\u7b49"></textarea></div>

          <hr style="border:none;border-top:1px solid #f0f0f0;margin:20px 0;">

          <!-- Section 2: Eval Config -->
          <h4 style="font-size:14px;font-weight:500;margin-bottom:12px;color:rgba(0,0,0,0.85);">\u8bc4\u6d4b\u914d\u7f6e</h4>
          <div class="form-row">
            <div class="form-group"><label class="req">\u8bc4\u6d4b\u672c\u4f53</label><select name="device" id="task-device" required onchange="syncDeployMode(this.value)"><option value="">\u8bf7\u9009\u62e9</option><option value="moz">moz</option><option value="Franka">Franka</option></select></div>
            <div class="form-group"><label class="req">\u90e8\u7f72\u65b9\u5f0f</label><input type="text" id="task-deploy-mode-text" value="--" disabled style="background:#f5f5f5;color:rgba(0,0,0,0.45);"><input type="hidden" name="deploy_mode" id="task-deploy-mode"></div>
            <div class="form-group"><label class="req">\u8bc4\u6d4b\u6b21\u6570</label><div class="input-clear-wrap"><input type="number" name="total_sessions" required value="30" min="1"><span class="input-clear" onclick="this.previousElementSibling.value=''">&times;</span></div></div>
          </div>
          <div class="form-row">
            <div class="form-group" style="grid-column:1/4;">
              <label class="req">Checkpoint (\u591a\u9009\uff0c\u81f3\u5c11\u9009\u62e9\u4e24\u4e2a)</label>
              <div style="position:relative;">
                <div class="er-dd-trigger" id="ms-ckpt-btn" onclick="mselToggle('ms-ckpt', event)">
                  <div id="ms-ckpt-chips" class="er-chips"></div>
                  <span style="margin-left:auto;color:rgba(0,0,0,0.35);font-size:10px;flex-shrink:0;padding-left:4px;">&#9660;</span>
                </div>
                <div class="er-dd-panel" id="ms-ckpt-panel" style="width:100%;">
                  <div style="padding:8px 12px;border-bottom:1px solid #f0f0f0;display:flex;gap:16px;align-items:center;">
                    <a href="javascript:;" onclick="mselToggleAll('ms-ckpt', true)" style="font-size:12px;color:#1F80A0;">\u5168\u9009</a>
                    <a href="javascript:;" onclick="mselToggleAll('ms-ckpt', false)" style="font-size:12px;color:rgba(0,0,0,0.45);">\u6e05\u7a7a</a>
                  </div>
                  <div style="max-height:240px;overflow-y:auto;padding:6px 0;">
                    {ckpt_ms_opts}
                  </div>
                </div>
                <input type="hidden" name="model_ids" id="ms-ckpt-hidden" value="">
              </div>
            </div>
          </div>

          <!-- Benchmark (merged into Eval Config) -->
          <div class="form-group" style="margin-top:4px;">
            <label class="req">Benchmark</label>
            <select name="benchmark_id" id="bm-select" required onchange="previewBm(this.value)" class="has-value">{bm_opts}</select>
          </div>
          <!-- Benchmark preview: 3 rows -->
          <div id="bm-preview" style="margin-top:8px;padding:14px 16px;background:#fafafa;border-radius:8px;border:1px solid #f0f0f0;display:none;position:relative;">
            <div style="display:grid;grid-template-columns:90px 1fr;gap:8px 12px;font-size:13px;align-items:start;">
              <span style="color:rgba(0,0,0,0.45);">\u573a\u666f\u63cf\u8ff0</span>
              <span id="bm-pv-scene" style="line-height:1.7;"></span>
              <span style="color:rgba(0,0,0,0.45);">\u8bc4\u4ef7\u6807\u51c6</span>
              <span id="bm-pv-criteria" style="font-weight:500;"></span>
              <span style="color:rgba(0,0,0,0.45);">\u63d0\u793a\u8bcd\u7ec4</span>
              <span id="bm-pv-prompts" style="display:flex;flex-wrap:wrap;gap:4px;"></span>
            </div>
            <a href="javascript:;" onclick="openBmDetail()" style="position:absolute;top:14px;right:16px;font-size:13px;color:#1F80A0;text-decoration:none;">\u67e5\u770b\u8be6\u60c5 &rarr;</a>
          </div>
        </div>
        <!-- Benchmark detail modal (inline drawer) -->
        <div class="ant-drawer-mask" id="bm-detail-modal" style="z-index:300;background:rgba(0,0,0,0.65);">
          <div class="ant-drawer-content" style="width:720px;max-width:90vw;">
            <div class="ant-drawer-header">
              <h3 id="bm-detail-title">Benchmark \u8be6\u60c5</h3>
              <button class="ant-drawer-close" onclick="closeBmDetail()">&times;</button>
            </div>
            <div class="ant-drawer-body">
              <div id="bm-detail-body" style="font-size:14px;"></div>
            </div>
          </div>
        </div>
        <div class="ant-drawer-footer">
          <button type="button" class="ant-btn" onclick="closeModal('create-task-drawer')">\u53d6\u6d88</button>
          <button type="submit" class="ant-btn ant-btn-primary">\u521b\u5efa\u4efb\u52a1</button>
        </div>
        </form>
      </div>
    </div>

    <script>
    var bmData = {bm_preview_json};
    var bmCurrentId = null;
    function previewBm(bid) {{
      bmCurrentId = bid;
      var pv = document.getElementById('bm-preview');
      var d = bmData[bid];
      if (!d) {{ pv.style.display='none'; return; }}
      pv.style.display='';
      document.getElementById('bm-pv-scene').textContent = d.scene_description || '\u2014';
      document.getElementById('bm-pv-criteria').textContent = d.criteria || '--';
      var ph = '';
      d.prompts.forEach(function(p) {{ ph += '<span class="ant-tag">'+p.name+' ('+p.steps+'\u6b65)</span>'; }});
      document.getElementById('bm-pv-prompts').innerHTML = ph;
    }}
    function closeBmDetail() {{
      closeModal('bm-detail-modal');
    }}
    // Hoist bm-detail-modal to document.body so it's not a DOM child of the task drawer
    // (otherwise it would inherit stacking/display from the parent drawer)
    (function() {{
      var bmMask = document.getElementById('bm-detail-modal');
      if (bmMask && bmMask.parentElement !== document.body) {{
        document.body.appendChild(bmMask);
      }}
    }})();
    function openBmDetail() {{
      if (!bmCurrentId) return;
      var d = bmData[bmCurrentId];
      if (!d) return;
      document.getElementById('bm-detail-title').textContent = 'Benchmark \u8be6\u60c5 - ' + d.name;
      function esc(s) {{ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }}
      function escAttr(s) {{ return esc(s).replace(/'/g, '&#39;'); }}
      // Expandable prompt list
      var promptsHtml = '';
      d.prompts.forEach(function(p, pi) {{
        var llId = 'bm-mo-prompt-' + pi;
        var llRows = '';
        (p.low_levels || []).forEach(function(ll, li) {{
          llRows += '<div style="padding:4px 0 4px 28px;font-size:12px;color:rgba(0,0,0,0.65);border-bottom:1px solid #fafafa;"><span style="color:rgba(0,0,0,0.25);margin-right:6px;">' + (li+1) + '.</span>' + esc(ll.zh) + ' <span style="color:rgba(0,0,0,0.35);">' + esc(ll.en) + '</span></div>';
        }});
        promptsHtml += ''
          + '<div style="border:1px solid #f0f0f0;border-radius:6px;margin-bottom:6px;background:#fff;overflow:hidden;">'
          + '<div style="padding:8px 12px;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:6px;" onclick="var c=document.getElementById(\\''+llId+'\\');var a=this.querySelector(\\'.ll-a\\');var show=c.style.display===\\'none\\';c.style.display=show?\\'\\':\\'none\\';a.style.transform=show?\\'rotate(90deg)\\':\\'\\';">'
          +   '<span class="ll-a" style="display:inline-block;font-size:10px;color:rgba(0,0,0,0.3);transition:transform 0.2s;">\u25B6</span>'
          +   '<span style="font-weight:500;">' + esc(p.name) + '</span>'
          +   '<span style="color:rgba(0,0,0,0.45);">\u00B7 ' + p.steps + ' \u6b65</span>'
          + '</div>'
          + '<div id="' + llId + '" style="display:none;padding:4px 12px 8px;border-top:1px solid #f5f5f5;">' + (llRows || '<div style="color:rgba(0,0,0,0.25);padding:4px 0;">\u6682\u65e0</div>') + '</div>'
          + '</div>';
      }});
      if (!promptsHtml) promptsHtml = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      // Props chips
      var propsHtml = '';
      if (d.props) {{
        d.props.split(/[,\uff0c\u3001]/).forEach(function(p) {{
          p = p.trim();
          if (p) propsHtml += '<span class="ant-tag">' + esc(p) + '</span>';
        }});
      }}
      if (!propsHtml) propsHtml = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      // Image grid
      var imgsHtml = '';
      (d.images || []).forEach(function(im, i) {{
        var desc = im.description || ('\u56fe\u7247 ' + (i+1));
        imgsHtml += ''
          + '<div class="media-card" onclick="window.openMediaViewer(\\'image\\', ' + i + ', \\'' + escAttr(desc) + '\\', \\'' + escAttr(im.url || '') + '\\')">'
          + '<div class="media-thumb"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#8dcde0" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></div>'
          + '<div class="media-desc">' + esc(desc) + '</div>'
          + '</div>';
      }});
      if (!imgsHtml) imgsHtml = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      else imgsHtml = '<div class="media-grid">' + imgsHtml + '</div>';
      // Video grid
      var vidsHtml = '';
      (d.videos || []).forEach(function(v, i) {{
        var desc = v.description || ('\u89c6\u9891 ' + (i+1));
        var dur = v.duration ? (' \u00B7 ' + v.duration + 's') : '';
        vidsHtml += ''
          + '<div class="media-card" onclick="window.openMediaViewer(\\'video\\', ' + i + ', \\'' + escAttr(desc) + '\\', \\'' + escAttr(v.url || '') + '\\')">'
          + '<div class="media-thumb media-thumb-video"><svg width="28" height="28" viewBox="0 0 24 24" fill="#1F80A0"><polygon points="6 4 20 12 6 20"/></svg></div>'
          + '<div class="media-desc">' + esc(desc) + dur + '</div>'
          + '</div>';
      }});
      if (!vidsHtml) vidsHtml = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      else vidsHtml = '<div class="media-grid">' + vidsHtml + '</div>';
      var sd = d.scene_description || '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      var cri = d.criteria || '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      var html = ''
        // Section 1: Basic Info
        + '<div style="margin-bottom:20px;">'
        + '<h4 style="margin:0 0 12px;font-size:14px;font-weight:500;color:rgba(0,0,0,0.85);">\u57fa\u672c\u4fe1\u606f</h4>'
        + '<div style="display:grid;grid-template-columns:110px 1fr;gap:10px 16px;font-size:13px;">'
        + '<span style="color:rgba(0,0,0,0.45);">\u540d\u79f0</span><span style="font-weight:500;font-size:14px;">' + esc(d.name || '--') + '</span>'
        + '<span style="color:rgba(0,0,0,0.45);">\u63cf\u8ff0</span><span>' + (d.description ? esc(d.description) : '\u2014') + '</span>'
        + '<span style="color:rgba(0,0,0,0.45);">\u521b\u5efa</span><span>' + esc(d.creator || '--') + ' \u00b7 ' + esc(d.created_at || '--') + '</span>'
        + '</div></div>'
        // Section 2: Scene Config
        + '<hr style="border:none;border-top:1px solid #f0f0f0;margin:16px 0;">'
        + '<div style="margin-bottom:20px;">'
        + '<h4 style="margin:0 0 12px;font-size:14px;font-weight:500;color:rgba(0,0,0,0.85);">\u573a\u666f\u914d\u7f6e</h4>'
        + '<div style="display:grid;grid-template-columns:110px 1fr;gap:12px 16px;font-size:13px;align-items:start;margin-bottom:16px;">'
        + '<span style="color:rgba(0,0,0,0.45);">\u573a\u666f\u63cf\u8ff0</span><span style="line-height:1.8;">' + sd + '</span>'
        + '<span style="color:rgba(0,0,0,0.45);">\u4efb\u52a1\u9053\u5177</span><span style="display:flex;flex-wrap:wrap;gap:4px;">' + propsHtml + '</span>'
        + '</div>'
        + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">'
        + '<div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:8px;">\u573a\u666f\u56fe\u7247</div>' + imgsHtml + '</div>'
        + '<div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:8px;">\u573a\u666f\u89c6\u9891</div>' + vidsHtml + '</div>'
        + '</div>'
        + '</div>'
        // Section 3: Related Config
        + '<hr style="border:none;border-top:1px solid #f0f0f0;margin:16px 0;">'
        + '<div>'
        + '<h4 style="margin:0 0 12px;font-size:14px;font-weight:500;color:rgba(0,0,0,0.85);">\u5173\u8054\u914d\u7f6e</h4>'
        + '<div style="display:grid;grid-template-columns:110px 1fr;gap:14px 16px;font-size:13px;align-items:start;">'
        + '<span style="color:rgba(0,0,0,0.45);">\u8bc4\u4ef7\u6807\u51c6</span><span>' + cri + '</span>'
        + '<span style="color:rgba(0,0,0,0.45);">\u63d0\u793a\u8bcd (' + d.prompts.length + ')</span><div>' + promptsHtml + '</div>'
        + '</div></div>';
      document.getElementById('bm-detail-body').innerHTML = html;
      openModal('bm-detail-modal');
    }}
    // Generic tree-selector initializer — used for both task-tags and bm-tags
    function tagTreeInit(wrapId, hiddenId, placeholder) {{
      var wrap = document.getElementById(wrapId);
      if (!wrap) return;
      wrap.querySelectorAll('.ts-arrow:not(.empty)').forEach(function(arrow) {{
        arrow.addEventListener('click', function(e) {{
          e.stopPropagation();
          this.classList.toggle('expanded');
          var children = this.closest('.ts-node').querySelector('.ts-children');
          if (children) children.classList.toggle('expanded');
        }});
      }});
      wrap.querySelectorAll('.ts-row[data-id]').forEach(function(row) {{
        row.addEventListener('click', function(e) {{
          if (e.target.classList.contains('ts-arrow')) return;
          this.classList.toggle('selected');
          tagTreeSync(wrapId, hiddenId, placeholder);
        }});
      }});
    }}
    function tagTreeSync(wrapId, hiddenId, placeholder) {{
      var wrap = document.getElementById(wrapId);
      var selected = wrap.querySelectorAll('.ts-row.selected');
      var trigger = wrap.querySelector('.ts-trigger');
      var hidden = document.getElementById(hiddenId);
      var ids = []; var chips = '';
      selected.forEach(function(r) {{
        ids.push(r.dataset.id);
        chips += '<span class="ts-chip"><span class="ts-chip-text">'+r.dataset.path+'</span><span class="ts-chip-close" data-rid="'+r.dataset.id+'" data-wrap="'+wrapId+'" data-hidden="'+hiddenId+'" data-placeholder="'+placeholder+'" onclick="event.stopPropagation();tagTreeRemove(this)">&times;</span></span>';
      }});
      trigger.innerHTML = chips || '<span class="ts-placeholder">'+placeholder+'</span>';
      if (hidden) hidden.value = ids.join(',');
    }}
    function tagTreeRemove(btn) {{
      var wrap = document.getElementById(btn.dataset.wrap);
      var row = wrap.querySelector('.ts-row[data-id="'+btn.dataset.rid+'"]');
      if (row) row.classList.remove('selected');
      tagTreeSync(btn.dataset.wrap, btn.dataset.hidden, btn.dataset.placeholder);
    }}
    tagTreeInit('ts-task-tags', 'task-tags-hidden', '\u9009\u62e9\u6807\u7b7e');
    function tsToggle(id) {{ document.getElementById(id).classList.toggle('open'); }}
    // Form validation: all fields required except \u4efb\u52a1\u63cf\u8ff0
    function validateTaskForm() {{
      function fail(msg, el) {{
        if (window.showToast) window.showToast(msg, 'warning');
        if (el) {{
          var targetEl = el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA' ? el : null;
          if (targetEl) {{
            targetEl.focus();
            targetEl.style.borderColor = '#ff4d4f';
            setTimeout(function() {{ targetEl.style.borderColor = ''; }}, 2500);
          }}
        }}
        return false;
      }}
      var form = document.querySelector('#create-task-drawer form');
      // Sequential required-field checks
      var nameEl = form.querySelector('input[name="name"]');
      if (!nameEl.value.trim()) return fail('\u8bf7\u586b\u5199\u4efb\u52a1\u540d\u79f0', nameEl);
      var disp = form.querySelector('input[name="display_name"]');
      if (!disp.value.trim()) return fail('\u8bf7\u586b\u5199\u5411\u8bc4\u6d4b\u5458\u5c55\u793a\u540d\u79f0', disp);
      var proj = form.querySelector('select[name="project"]');
      if (!proj.value) return fail('\u8bf7\u9009\u62e9\u6240\u5c5e\u9879\u76ee', proj);
      var pri = form.querySelector('select[name="priority"]');
      if (!pri.value) return fail('\u8bf7\u9009\u62e9\u4f18\u5148\u7ea7', pri);
      var due = form.querySelector('input[name="due_date"]');
      if (!due.value) return fail('\u8bf7\u9009\u62e9\u9884\u671f\u4ea4\u4ed8\u65e5\u671f', due);
      var tagHidden = document.getElementById('task-tags-hidden');
      if (!tagHidden.value) {{
        if (window.showToast) window.showToast('\u8bf7\u9009\u62e9\u4efb\u52a1\u6807\u7b7e', 'warning');
        var tagTrig = document.querySelector('#ts-task-tags .ts-trigger');
        if (tagTrig) {{
          tagTrig.style.borderColor = '#ff4d4f';
          setTimeout(function() {{ tagTrig.style.borderColor = ''; }}, 2500);
        }}
        return false;
      }}
      var dev = form.querySelector('select[name="device"]');
      if (!dev.value) return fail('\u8bf7\u9009\u62e9\u8bc4\u6d4b\u672c\u4f53', dev);
      var sessions = form.querySelector('input[name="total_sessions"]');
      if (!sessions.value || parseInt(sessions.value) < 1) return fail('\u8bf7\u586b\u5199\u8bc4\u6d4b\u6b21\u6570', sessions);
      var hidden = document.getElementById('ms-ckpt-hidden');
      var ids = (hidden && hidden.value) ? hidden.value.split(',').filter(Boolean) : [];
      if (ids.length < 2) {{
        if (window.showToast) window.showToast('Checkpoint \u81f3\u5c11\u9009 2 \u4e2a\uff0c\u5f53\u524d\u9009\u4e86 ' + ids.length + ' \u4e2a', 'warning');
        var trig = document.getElementById('ms-ckpt-btn');
        if (trig) {{
          trig.style.borderColor = '#ff4d4f';
          setTimeout(function() {{ trig.style.borderColor = ''; }}, 2500);
        }}
        return false;
      }}
      var bm = form.querySelector('select[name="benchmark_id"]');
      if (!bm.value) return fail('\u8bf7\u9009\u62e9 Benchmark', bm);
      return true;
    }}
    // Deploy mode auto-populated from device
    function syncDeployMode(device) {{
      var text = document.getElementById('task-deploy-mode-text');
      var hidden = document.getElementById('task-deploy-mode');
      var mode = '';
      if (device === 'moz') mode = '\u672c\u5730\u90e8\u7f72';
      else if (device === 'Franka') mode = '\u4e91\u7aef\u90e8\u7f72';
      text.value = mode || '--';
      hidden.value = mode;
    }}
    document.addEventListener('click', function(e) {{
      document.querySelectorAll('.ts-wrap.open').forEach(function(w) {{
        if (!w.contains(e.target)) w.classList.remove('open');
      }});
    }});

    </script>
    '''
    return render_page("\u8bc4\u6d4b\u4efb\u52a1\u7ba1\u7406", content, active="tasks")


@app.route("/tasks/create", methods=["POST"])
def tasks_create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("\u4efb\u52a1\u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a", "error")
        return redirect(url_for("tasks_page"))
    # Parse model_ids from hidden field (comma-separated) or form list
    model_raw = request.form.get("model_ids", "")
    model_ids = [m.strip() for m in model_raw.split(",") if m.strip()] if model_raw else request.form.getlist("model_ids")
    new_no = 1000 + len(EVAL_TASKS) + 1
    EVAL_TASKS.append({
        "id": f"t{len(EVAL_TASKS)+1}",
        "task_no": new_no,
        "name": name,
        "display_name": request.form.get("display_name", "").strip() or name,
        "project": request.form.get("project", "").strip(),
        "collect_type": "test",
        "due_date": request.form.get("due_date", "").strip(),
        "task_tags": [t.strip() for t in request.form.get("task_tags", "").split(",") if t.strip()],
        "description": request.form.get("description", "").strip(),
        "device": request.form.get("device", "").strip(),
        "deploy_mode": request.form.get("deploy_mode", "").strip(),
        "benchmark_id": request.form.get("benchmark_id", ""),
        "eval_type": request.form.get("eval_type", "preference"),
        "model_ids": model_ids,
        "status": "\u672a\u5f00\u59cb",
        "priority": request.form.get("priority", "\u4e2d"),
        "total_sessions": int(request.form.get("total_sessions", 30)),
        "collect_done": 0, "eval_done": 0, "completed_sessions": 0,
        "created_by": "Joanna Qiao",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    })
    flash(f"\u8bc4\u6d4b\u4efb\u52a1\u300c{name}\u300d\u521b\u5efa\u6210\u529f", "success")
    return redirect(url_for("tasks_page"))


# ── Collection Management ──
@app.route("/collections")
def collections_page():
    """Collection management: task split by checkpoint."""
    # Generate one row per (task, checkpoint) pair
    records = []
    for t in EVAL_TASKS:
        bm = get_benchmark(t["benchmark_id"])
        bm_name = bm["name"] if bm else "--"
        total = max(t.get("total_sessions", 1), 1)
        n_models = max(len(t["model_ids"]), 1)
        per_model_done = t.get("collect_done", 0) // n_models if n_models > 0 else 0
        # Mock due_date = created_at + 14 days
        try:
            _created = datetime.strptime(t.get("created_at", ""), "%Y-%m-%d")
            due_str = (_created + timedelta(days=14)).strftime("%Y-%m-%d")
        except Exception:
            due_str = "--"
        for mid in t["model_ids"]:
            m = next((x for x in MODELS if x["id"] == mid), None)
            if not m:
                continue
            records.append({
                "task_id": t["id"],
                "task_name": t["name"],
                "benchmark": bm_name,
                "model_name": m["name"],
                "model_version": m["version"],
                "total": total,
                "done": min(per_model_done, total),
                "created_at": t.get("created_at", "--"),
                "due_date": due_str,
            })

    rows = ""
    for r in records:
        pct = round(r["done"] / max(r["total"], 1) * 100)
        view_btn = icon_btn(f"/tasks/{r['task_id']}", ICON_VIEW, "\u67e5\u770b\u8bc4\u6d4b\u4efb\u52a1", "default")
        rows += (
            "<tr>"
            f'<td style="font-weight:500;">{r["task_name"]}</td>'
            f'<td>{r["benchmark"]}</td>'
            f'<td>{r["model_name"]} <span style="color:rgba(0,0,0,0.35);">{r["model_version"]}</span></td>'
            f'<td style="min-width:160px;">'
            f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<div style="flex:1;height:14px;background:#f0f0f0;border-radius:7px;overflow:hidden;position:relative;">'
            f'<div style="width:{pct}%;height:100%;background:#1F80A0;border-radius:7px;"></div>'
            f'<span class="pb-text" style="--pct:{pct}%;">{r["done"]}/{r["total"]}</span>'
            f'</div></div></td>'
            f'<td style="font-size:13px;color:rgba(0,0,0,0.65);">{r["created_at"]}</td>'
            f'<td style="font-size:13px;color:rgba(0,0,0,0.65);">{r["due_date"]}</td>'
            f'<td class="actions-cell">{view_btn}</td>'
            "</tr>"
        )
    empty = '<tr><td colspan="7" style="text-align:center;padding:40px;color:rgba(0,0,0,0.25);">\u6682\u65e0\u6570\u636e</td></tr>' if not rows else ""

    notice_info = '<div style="background:#e6f7ff;border:1px solid #91d5ff;border-radius:8px;padding:12px 16px;margin-bottom:20px;font-size:13px;color:#0050b3;display:flex;align-items:center;gap:8px;line-height:1.8;"><span style="font-size:16px;">&#8505;</span><div>\u91c7\u96c6\u4efb\u52a1\uff0c\u65b0\u589e Eval \u7c7b\u578b</div></div>'

    table_html = f'''
    <div class="filter-bar">
      <input type="text" id="col-f-task" placeholder="\u91c7\u96c6\u4efb\u52a1\u540d\u79f0" style="min-width:180px;">
      <input type="text" id="col-f-bm" placeholder="Benchmark" style="min-width:160px;">
      <input type="text" id="col-f-ckpt" placeholder="Checkpoint" style="min-width:160px;">
      <button class="ant-btn" onclick="colClear()">\u6e05\u7a7a</button>
      <button class="ant-btn ant-btn-primary" onclick="colFilter()">\u641c\u7d22</button>
    </div>
    <div class="ant-card ant-card-bordered">
      <table class="ant-table" id="col-tbl">
        <thead><tr>
          <th>\u8bc4\u6d4b\u4efb\u52a1\u540d\u79f0</th>
          <th>Benchmark</th>
          <th>Checkpoint</th>
          <th>\u91c7\u96c6\u8fdb\u5ea6</th>
          <th style="width:120px;">\u521b\u5efa\u65f6\u95f4</th>
          <th style="width:120px;">\u9884\u671f\u4ea4\u4ed8\u65f6\u95f4</th>
          <th style="width:120px;">\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}{empty}</tbody>
      </table>
    </div>
    <script>
    function colFilter() {{
      var ft = (document.getElementById('col-f-task').value || '').trim().toLowerCase();
      var fb = (document.getElementById('col-f-bm').value || '').trim().toLowerCase();
      var fc = (document.getElementById('col-f-ckpt').value || '').trim().toLowerCase();
      document.querySelectorAll('#col-tbl tbody tr').forEach(function(tr) {{
        if (tr.cells.length < 3) return;
        var task = (tr.cells[0].textContent || '').toLowerCase();
        var bm = (tr.cells[1].textContent || '').toLowerCase();
        var ck = (tr.cells[2].textContent || '').toLowerCase();
        var ok = (!ft || task.indexOf(ft) >= 0)
              && (!fb || bm.indexOf(fb) >= 0)
              && (!fc || ck.indexOf(fc) >= 0);
        tr.style.display = ok ? '' : 'none';
      }});
    }}
    function colClear() {{
      document.getElementById('col-f-task').value = '';
      document.getElementById('col-f-bm').value = '';
      document.getElementById('col-f-ckpt').value = '';
      colFilter();
    }}
    ['col-f-task','col-f-bm','col-f-ckpt'].forEach(function(id) {{
      var el = document.getElementById(id);
      if (el) el.addEventListener('keydown', function(e) {{ if (e.key === 'Enter') {{ e.preventDefault(); colFilter(); }} }});
    }});
    </script>
    '''
    return render_page("\u8bc4\u6d4b\u91c7\u96c6\u7ba1\u7406", notice_info + table_html, active="collections")

@app.route("/collections/<tid>/<mid>")
def collection_data(tid, mid):
    """View collection data records for a task+model pair."""
    task = next((t for t in EVAL_TASKS if t["id"] == tid), None)
    model = next((m for m in MODELS if m["id"] == mid), None)
    if not task or not model:
        flash("\u8bb0\u5f55\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("collections_page"))

    bm = get_benchmark(task["benchmark_id"])
    n_models = max(len(task["model_ids"]), 1)
    total = task.get("total_sessions", 30)
    done = min(task.get("collect_done", 0) // n_models, total)

    # Mock collection records
    import random as _rnd
    _rnd.seed(hash(tid + mid))
    data_rows = ""
    for i in range(done):
        rec_id = _rnd.randint(30000, 40000)
        uuid_short = f"{_rnd.randint(0x1000,0xffff):x}{_rnd.randint(0x1000,0xffff):x}"
        success = _rnd.random() > 0.2
        result_tag = '<span class="ant-tag ant-tag-green">\u6210\u529f</span>' if success else '<span class="ant-tag ant-tag-orange">\u5931\u8d25</span>'
        data_rows += (
            f'<tr style="vertical-align:top;">'
            f'<td>{i}</td>'
            f'<td>{rec_id}</td>'
            f'<td>'
            f'<div style="display:flex;gap:4px;">'
            f'<div style="width:160px;height:100px;background:#1a1a2e;border-radius:6px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:11px;position:relative;">\u5934\u90e8<span style="position:absolute;bottom:2px;right:4px;font-size:10px;color:rgba(255,255,255,0.3);">&#9654;</span></div>'
            f'<div style="width:160px;height:100px;background:#1a1a2e;border-radius:6px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:11px;position:relative;">\u5de6\u81c2<span style="position:absolute;bottom:2px;right:4px;font-size:10px;color:rgba(255,255,255,0.3);">&#9654;</span></div>'
            f'</div></td>'
            f'<td style="font-size:12px;color:rgba(0,0,0,0.45);">{uuid_short}</td>'
            f'<td>{result_tag}</td>'
            f'<td style="font-size:12px;color:rgba(0,0,0,0.45);">\u91c7\u96c6: root</td>'
        )
        trail_btn = icon_btn("#", ICON_VIEW, "\u8f68\u8ff9", "default")
        data_rows += (
            f'<td class="actions-cell">{trail_btn}</td>'
            f'</tr>'
        )

    if not data_rows:
        data_rows = '<tr><td colspan="7" style="text-align:center;color:rgba(0,0,0,0.25);padding:40px;">\u6682\u65e0\u91c7\u96c6\u6570\u636e</td></tr>'

    page_title = f"\u91c7\u96c6\u6570\u636e - {task['name']} - {model['name']}"

    content = f'''
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <div style="display:flex;align-items:center;gap:8px;">
        <a href="/collections" class="ant-btn ant-btn-sm">&larr; \u8fd4\u56de</a>
        <span style="font-size:15px;font-weight:500;">{task["name"]}</span>
        <span class="ant-tag ant-tag-blue">{model["name"]} {model["version"]}</span>
      </div>
      <span style="font-size:13px;color:rgba(0,0,0,0.45);">\u91c7\u96c6 {done} \u6761</span>
    </div>

    <div class="filter-bar">
      <input type="text" placeholder="ID\u641c\u7d22" style="min-width:120px;">
      <select style="min-width:130px;"><option value="">\u5e8f\u5217\u53f7</option><option>MOZ1-Y01</option><option>MOZ1-Y64</option></select>
      <select style="min-width:130px;"><option value="">\u64cd\u4f5c\u4eba</option><option>root</option></select>
      <button class="ant-btn" onclick="clearFilters()">\u6e05\u7a7a</button>
      <button class="ant-btn ant-btn-primary" onclick="doSearch()">\u641c\u7d22</button>
    </div>

    <div class="ant-card ant-card-bordered">
      <table class="ant-table">
        <thead><tr>
          <th style="width:40px;">\u5206\u7ec4</th>
          <th style="width:60px;">ID</th>
          <th>\u89c6\u9891\u533a\u57df</th>
          <th style="width:100px;">\u5e8f\u5217\u53f7</th>
          <th style="width:70px;">\u7ed3\u679c</th>
          <th style="width:100px;">\u64cd\u4f5c\u4eba</th>
          <th style="width:60px;">\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{data_rows}</tbody>
      </table>
    </div>
    '''
    notice_col = '<div style="background:#fff1f0;border:1px solid #ffa39e;border-radius:8px;padding:8px 16px;margin-bottom:12px;font-size:13px;color:#cf1322;display:flex;align-items:center;gap:8px;"><span style="font-size:16px;">&#9888;</span> MVP \u7248\u672c\uff0c\u6d4b\u8bd5\u6570\u636e\u91c7\u96c6\uff0c\u590d\u7528\u5f53\u524d\u300c\u91c7\u96c6\u9700\u6c42\u7ba1\u7406\u6a21\u5757 - \u6d4b\u8bd5\u4efb\u52a1\u7ba1\u7406\u300d\u7684\u80fd\u529b</div>'
    return render_page(page_title, notice_col + content, active="collections")


@app.route("/tasks/<tid>/start")
def task_start(tid):
    t = next((x for x in EVAL_TASKS if x["id"] == tid), None)
    msg = ""
    if t and t["status"] == "\u672a\u5f00\u59cb":
        t["status"] = "\u91c7\u96c6\u4e2d"
        msg = f"\u4efb\u52a1\u300c{t['name']}\u300d\u5df2\u5f00\u542f"
    return redirect(f"/tasks?toast={msg}" if msg else "/tasks")


@app.route("/tasks/<tid>/pause")
def task_pause(tid):
    t = next((x for x in EVAL_TASKS if x["id"] == tid), None)
    if t and t["status"] in ("\u91c7\u96c6\u4e2d", "\u8bc4\u6d4b\u4e2d"):
        t["status"] = "\u5df2\u6682\u505c"
        flash(f"\u4efb\u52a1\u300c{t['name']}\u300d\u5df2\u6682\u505c", "success")
    return redirect(url_for("tasks_page"))


@app.route("/tasks/<tid>/delete")
def task_delete(tid):
    t = next((x for x in EVAL_TASKS if x["id"] == tid), None)
    if t and t["status"] in ("\u672a\u5f00\u59cb", "\u5df2\u6682\u505c"):
        t["status"] = "\u5df2\u5e9f\u5f03"
        flash(f"\u4efb\u52a1\u300c{t['name']}\u300d\u5df2\u5e9f\u5f03", "success")
    return redirect(url_for("tasks_page"))


@app.route("/tasks/<tid>/analyze")
def task_analyze(tid):
    t = next((x for x in EVAL_TASKS if x["id"] == tid), None)
    if t and t["status"] == "\u8bc4\u6d4b\u5b8c\u6210":
        t["status"] = "\u5206\u6790\u5b8c\u6210"
        flash(f"\u4efb\u52a1\u300c{t['name']}\u300d\u5206\u6790\u5b8c\u6210", "success")
    return redirect(url_for("tasks_page"))


@app.route("/tasks/<tid>")
def task_detail(tid):
    t = next((x for x in EVAL_TASKS if x["id"] == tid), None)
    if not t:
        flash("\u4efb\u52a1\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("tasks_page"))
    bm = get_benchmark(t["benchmark_id"])
    et = CRITERIA_TYPES.get(t.get("eval_type", ""), {})
    pct = round(t["completed_sessions"] / t["total_sessions"] * 100) if t["total_sessions"] > 0 else 0
    bar_color = "green" if t["status"] == "\u5df2\u5b8c\u6210" else "blue" if t["status"] == "\u8fdb\u884c\u4e2d" else "yellow"

    # Benchmark info
    bm_name = bm["name"] if bm else "--"
    scene_name = "--"
    cr_name = "--"
    prompt_count = 0
    if bm:
        sc = get_scene(bm.get("scene_id", ""))
        cr = get_criterion(bm.get("criteria_id", ""))
        scene_name = sc["name"] if sc else "--"
        cr_name = cr["name"] if cr else "--"
        prompt_count = len(bm.get("prompt_ids", []))

    # Benchmark preview card data
    scene_type = ""
    prompt_tags_html = ""
    if bm:
        if sc:
            scene_type = sc.get("environment", {}).get("type", "")
        for pid in bm.get("prompt_ids", []):
            p = get_prompt(pid)
            if p:
                prompt_tags_html += f'<span class="ant-tag">{p["high_level"]} ({len(p.get("low_levels",[]))} \u6b65)</span>'

    # Build single-bm preview dict for modal (mirrors tasks_page bm_preview structure)
    import json as _json_td
    bm_preview_one = {}
    if bm:
        _prompts_info = []
        for pid in bm.get("prompt_ids", []):
            p = get_prompt(pid)
            if p:
                _prompts_info.append({
                    "name": p["high_level"],
                    "steps": len(p.get("low_levels", [])),
                    "low_levels": [{"zh": ll.get("zh", ""), "en": ll.get("en", "")} for ll in p.get("low_levels", [])],
                })
        _cr_obj = get_criterion(bm.get("criteria_id", ""))
        _cr_info = ""
        if _cr_obj:
            _ct = CRITERIA_TYPES.get(_cr_obj["type"], {})
            _cr_info = f'{_cr_obj["name"]} ({_ct.get("label", "")})'
        _scene_desc = bm.get("scene_description", "").strip()
        if not _scene_desc and sc:
            _env = sc.get("environment", {})
            _ws = _env.get("workspace", {})
            _scene_desc = f'{sc.get("description","")} \u00b7 \u5de5\u4f5c\u533a {_ws.get("length",0)}x{_ws.get("width",0)}x{_ws.get("height",0)}cm \u00b7 {_env.get("conditions",{}).get("lighting","")}'
        _props = bm.get("props", "").strip()
        if not _props and sc:
            _props = "\u3001".join(o.get("name", "") for o in sc.get("objects", []) if o.get("name"))
        _refs = sc.get("references", {}) if sc else {}
        _imgs = [{"url": x.get("url", ""), "description": x.get("description", "")} for x in _refs.get("images", [])]
        _caps = [{"url": x.get("url", ""), "description": x.get("description", ""), "duration": x.get("duration", 0)} for x in _refs.get("capture_videos", [])]
        _demos = [{"url": x.get("url", ""), "description": x.get("description", ""), "duration": x.get("duration", 0)} for x in _refs.get("demo_videos", [])]
        bm_preview_one[bm["id"]] = {
            "id": bm["id"],
            "name": bm.get("name", ""),
            "description": bm.get("description", ""),
            "scene": sc["name"] if sc else "--",
            "scene_type": scene_type,
            "scene_description": _scene_desc,
            "props": _props,
            "images": _imgs,
            "videos": _caps + _demos,
            "criteria": _cr_info,
            "prompts": _prompts_info,
            "creator": bm.get("creator", ""),
            "created_at": bm.get("created_at", ""),
        }
    bm_preview_one_json = _json_td.dumps(bm_preview_one, ensure_ascii=False)
    bm_current_id = bm["id"] if bm else ""

    # Model names as tags
    model_tags_html = ""
    for mid in t["model_ids"]:
        m = next((x for x in MODELS if x["id"] == mid), None)
        if m:
            model_tags_html += f'<span class="ant-tag ant-tag-blue">{m["name"]}</span>'

    # A/B checkpoint names (first two models)
    ckpt_a = get_model_name(t["model_ids"][0]) if len(t["model_ids"]) > 0 else "--"
    ckpt_b = get_model_name(t["model_ids"][1]) if len(t["model_ids"]) > 1 else "--"

    # Evaluation data records (mock from EVAL_SESSIONS matching this task's models)
    import random as _rnd2
    _rnd2.seed(hash(tid))
    eval_data_rows = []
    if bm and bm.get("prompt_ids"):
        for pi, ppid in enumerate(bm["prompt_ids"]):
            p = get_prompt(ppid)
            if not p:
                continue
            for si, ll in enumerate(p.get("low_levels", [])):
                result_val = _rnd2.choice([2, 1, 0])
                eval_data_rows.append({
                    "exec_id": f"E{_rnd2.randint(1000,9999)}",
                    "high_level": p["high_level"],
                    "low_level": ll["zh"],
                    "result": result_val,
                    "prog_a": _rnd2.randint(30, 100),
                    "prog_b": _rnd2.randint(30, 100),
                    "prompt_id": ppid,
                })
    eval_data_html = ""
    for dr in eval_data_rows:
        if dr["result"] == 2:
            r_tag = '<span class="ant-tag ant-tag-blue">A \u80dc</span>'
        elif dr["result"] == 0:
            r_tag = '<span class="ant-tag ant-tag-gold">B \u80dc</span>'
        else:
            r_tag = '<span class="ant-tag">\u5e73\u5c40</span>'
        detail_btn = icon_btn(f"/tasks/{tid}/data/{dr['exec_id']}?pid={dr['prompt_id']}", ICON_VIEW, "\u67e5\u770b\u8be6\u60c5", "default")
        eval_data_html += (
            "<tr>"
            f'<td style="font-size:13px;">{dr["exec_id"]}</td>'
            f'<td>{dr["high_level"]}</td>'
            f'<td>{dr["low_level"]}</td>'
            f"<td>{r_tag}</td>"
            f'<td style="text-align:center;color:#1890ff;">{dr["prog_a"]}</td>'
            f'<td style="text-align:center;color:#ad6800;">{dr["prog_b"]}</td>'
            f'<td class="actions-cell">{detail_btn}</td>'
            "</tr>"
        )
    if not eval_data_html:
        eval_data_html = '<tr><td colspan="7" style="text-align:center;color:rgba(0,0,0,0.25);padding:24px;">\u6682\u65e0\u8bc4\u6d4b\u6570\u636e</td></tr>'

    # Build prompt modal content
    prompt_modal_html = ""
    if bm and bm.get("prompt_ids"):
        for ppid in bm["prompt_ids"]:
            p = get_prompt(ppid)
            if not p:
                continue
            prompt_modal_html += f'<div style="margin-bottom:12px;"><div style="font-weight:500;margin-bottom:6px;">{p["high_level"]} <span style="color:rgba(0,0,0,0.35);">{p["high_level_en"]}</span></div>'
            for si, ll in enumerate(p.get("low_levels", [])):
                prompt_modal_html += f'<div style="padding:3px 0 3px 16px;font-size:13px;color:rgba(0,0,0,0.65);"><span style="color:rgba(0,0,0,0.25);margin-right:6px;">{si+1}.</span>{ll["zh"]} <span style="color:rgba(0,0,0,0.35);">{ll["en"]}</span></div>'
            prompt_modal_html += '</div>'

    # Status info
    status_colors = {"\u672a\u5f00\u59cb": "", "\u91c7\u96c6\u4e2d": "processing", "\u8bc4\u6d4b\u4e2d": "processing", "\u8bc4\u6d4b\u5b8c\u6210": "", "\u5206\u6790\u5b8c\u6210": "", "\u5df2\u6682\u505c": "", "\u5df2\u5e9f\u5f03": ""}
    s_color = status_colors.get(t["status"], "")
    status_cls = f"ant-tag ant-tag-{s_color}" if s_color else "ant-tag"
    task_no = t.get("task_no", tid)
    task_title = f"\u8bc4\u6d4b\u4efb\u52a1 - {task_no}"
    start_link = "" if t["status"] == "\u5df2\u5b8c\u6210" else f'<a href="/evaluate/{t["id"]}" class="ant-btn ant-btn-primary">\u5f00\u59cb\u8bc4\u6d4b</a>'

    # \u2500\u2500 Mirror create-task form structure \u2500\u2500
    # Pull stored fields with deterministic mock fallbacks for legacy tasks
    import random as _rndd
    _rndd.seed(hash(tid))
    _proj_pool = ["\u57fa\u7840\u7814\u7a76", "\u5b81\u5fb7\u5e94\u7528", "moz1", "spirit", "demo\u91c7\u96c6", "\u9884\u8bad\u7ec3\u91c7\u96c6", "\u591a\u4efb\u52a1"]
    _device_pool = ["moz", "Franka"]
    _deploy_map = {"moz": "\u672c\u5730\u90e8\u7f72", "Franka": "\u4e91\u7aef\u90e8\u7f72"}
    display_name = t.get("display_name") or t["name"]
    project = t.get("project") or _rndd.choice(_proj_pool)
    collect_type = t.get("collect_type") or "test"
    due_date = t.get("due_date") or (datetime.now() + timedelta(days=_rndd.randint(7, 30))).strftime("%Y-%m-%d")
    description = t.get("description") or ""
    device = t.get("device") or _rndd.choice(_device_pool)
    deploy_mode = t.get("deploy_mode") or _deploy_map.get(device, "--")

    # Resolve task_tags \u2192 display chips (lookup name in TAXONOMY)
    def _tag_name_lookup(tag_id):
        for _dim in TAXONOMY.get("dimensions", []):
            for _tg in _dim.get("tags", []):
                if _tg["id"] == tag_id:
                    return _tg["name"]
                for _st in _tg.get("sub_tags", []):
                    if _st["id"] == tag_id:
                        return _st["name"]
        return tag_id
    task_tag_ids = t.get("task_tags") or []
    if not task_tag_ids:
        # mock seed: pick 2 random capability tags
        _cap_dim = next((d for d in TAXONOMY.get("dimensions", []) if d["id"] == "capability"), None)
        if _cap_dim:
            _all_caps = [tg["id"] for tg in _cap_dim["tags"]]
            task_tag_ids = _rndd.sample(_all_caps, min(2, len(_all_caps)))
    task_tags_html = "".join(
        f'<span class="ant-tag ant-tag-blue">{_tag_name_lookup(tid_)}</span>' for tid_ in task_tag_ids
    ) or '<span style="color:rgba(0,0,0,0.25);">--</span>'

    desc_html = description if description else '<span style="color:rgba(0,0,0,0.25);">--</span>'

    content = f'''
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
      <span style="font-size:16px;font-weight:500;">{t["name"]}</span>
      <span class="ant-tag ant-tag-{et.get('color','')}">{et.get('label','')}</span>
      <span class="{status_cls}">{t["status"]}</span>
    </div>

    <!-- Task Info -->
    <div>
      <div class="ant-card ant-card-bordered">
        <div class="ant-card-body" style="padding:24px;">

          <!-- Section 1: \u57fa\u7840\u4fe1\u606f -->
          <h4 style="font-size:14px;font-weight:500;margin:0 0 16px;color:rgba(0,0,0,0.85);">\u57fa\u7840\u4fe1\u606f</h4>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px 32px;margin-bottom:16px;">
            <div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u4efb\u52a1\u540d\u79f0</div><div style="font-size:14px;">{t["name"]}</div></div>
            <div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u5411\u8bc4\u6d4b\u5458\u5c55\u793a\u540d\u79f0</div><div style="font-size:14px;">{display_name}</div></div>
            <div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u6240\u5c5e\u9879\u76ee</div><div style="font-size:14px;">{project}</div></div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px 32px;margin-bottom:16px;">
            <div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u91c7\u96c6\u7c7b\u578b</div><div style="font-size:14px;">{collect_type}</div></div>
            <div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u4f18\u5148\u7ea7</div><div style="font-size:14px;">{t["priority"]}</div></div>
            <div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u9884\u671f\u4ea4\u4ed8\u65e5\u671f</div><div style="font-size:14px;">{due_date}</div></div>
          </div>
          <div style="margin-bottom:16px;">
            <div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u4efb\u52a1\u6807\u7b7e</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">{task_tags_html}</div>
          </div>
          <div style="margin-bottom:24px;">
            <div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u4efb\u52a1\u63cf\u8ff0</div>
            <div style="font-size:14px;line-height:1.7;">{desc_html}</div>
          </div>

          <hr style="border:none;border-top:1px solid #f0f0f0;margin:0 0 20px;">

          <!-- Section 2: \u8bc4\u6d4b\u914d\u7f6e -->
          <h4 style="font-size:14px;font-weight:500;margin:0 0 16px;color:rgba(0,0,0,0.85);">\u8bc4\u6d4b\u914d\u7f6e</h4>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px 32px;margin-bottom:16px;">
            <div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u8bc4\u6d4b\u672c\u4f53</div><div style="font-size:14px;">{device}</div></div>
            <div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u90e8\u7f72\u65b9\u5f0f</div><div style="font-size:14px;">{deploy_mode}</div></div>
            <div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u8bc4\u6d4b\u6b21\u6570</div><div style="font-size:14px;">{t["total_sessions"]} \u6b21</div></div>
          </div>
          <div style="margin-bottom:20px;">
            <div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">Checkpoint (\u81f3\u5c11\u4e24\u4e2a)</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">{model_tags_html}</div>
          </div>
          <div>
            <div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:8px;">Benchmark</div>
            <div style="padding:14px 18px;background:#fafafa;border-radius:8px;border:1px solid #f0f0f0;position:relative;">
              <div style="font-size:15px;font-weight:500;margin-bottom:10px;">{bm_name}</div>
              <div style="display:grid;grid-template-columns:90px 1fr;gap:8px 12px;font-size:13px;align-items:start;">
                <span style="color:rgba(0,0,0,0.45);">\u573a\u666f\u63cf\u8ff0</span>
                <span style="line-height:1.7;">{scene_name} <span class="ant-tag ant-tag-cyan" style="font-size:11px;">{scene_type}</span></span>
                <span style="color:rgba(0,0,0,0.45);">\u8bc4\u4ef7\u6807\u51c6</span>
                <span style="font-weight:500;">{cr_name}</span>
                <span style="color:rgba(0,0,0,0.45);">\u63d0\u793a\u8bcd\u7ec4</span>
                <span style="display:flex;flex-wrap:wrap;gap:4px;">{prompt_tags_html}</span>
              </div>
              <a href="javascript:;" onclick="openBmDetail()" style="position:absolute;top:14px;right:16px;font-size:13px;color:#1F80A0;text-decoration:none;">\u67e5\u770b\u8be6\u60c5 &rarr;</a>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- Benchmark detail modal -->
    <div class="ant-drawer-mask" id="bm-detail-modal" style="background:rgba(0,0,0,0.45);">
      <div class="ant-drawer-content" style="width:720px;max-width:90vw;">
        <div class="ant-drawer-header">
          <h3 id="bm-detail-title">Benchmark \u8be6\u60c5</h3>
          <button class="ant-drawer-close" onclick="closeBmDetail()">&times;</button>
        </div>
        <div class="ant-drawer-body">
          <div id="bm-detail-body" style="font-size:14px;"></div>
        </div>
      </div>
    </div>

    <script>
    var bmData = {bm_preview_one_json};
    var bmCurrentId = "{bm_current_id}";
    function closeBmDetail() {{ closeModal('bm-detail-modal'); }}
    function openBmDetail() {{
      if (!bmCurrentId) return;
      var d = bmData[bmCurrentId];
      if (!d) return;
      document.getElementById('bm-detail-title').textContent = 'Benchmark \u8be6\u60c5 - ' + d.name;
      function esc(s) {{ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }}
      function escAttr(s) {{ return esc(s).replace(/'/g, '&#39;'); }}
      var promptsHtml = '';
      d.prompts.forEach(function(p, pi) {{
        var llId = 'bm-mo-prompt-' + pi;
        var llRows = '';
        (p.low_levels || []).forEach(function(ll, li) {{
          llRows += '<div style="padding:4px 0 4px 28px;font-size:12px;color:rgba(0,0,0,0.65);border-bottom:1px solid #fafafa;"><span style="color:rgba(0,0,0,0.25);margin-right:6px;">' + (li+1) + '.</span>' + esc(ll.zh) + ' <span style="color:rgba(0,0,0,0.35);">' + esc(ll.en) + '</span></div>';
        }});
        promptsHtml += ''
          + '<div style="border:1px solid #f0f0f0;border-radius:6px;margin-bottom:6px;background:#fff;overflow:hidden;">'
          + '<div style="padding:8px 12px;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:6px;" onclick="var c=document.getElementById(\\''+llId+'\\');var a=this.querySelector(\\'.ll-a\\');var show=c.style.display===\\'none\\';c.style.display=show?\\'\\':\\'none\\';a.style.transform=show?\\'rotate(90deg)\\':\\'\\';">'
          +   '<span class="ll-a" style="display:inline-block;font-size:10px;color:rgba(0,0,0,0.3);transition:transform 0.2s;">\u25b6</span>'
          +   '<span style="font-weight:500;">' + esc(p.name) + '</span>'
          +   '<span style="color:rgba(0,0,0,0.45);">\u00b7 ' + p.steps + ' \u6b65</span>'
          + '</div>'
          + '<div id="' + llId + '" style="display:none;padding:4px 12px 8px;border-top:1px solid #f5f5f5;">' + (llRows || '<div style="color:rgba(0,0,0,0.25);padding:4px 0;">\u6682\u65e0</div>') + '</div>'
          + '</div>';
      }});
      if (!promptsHtml) promptsHtml = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      var propsHtml = '';
      if (d.props) {{
        d.props.split(/[,\uff0c\u3001]/).forEach(function(p) {{
          p = p.trim();
          if (p) propsHtml += '<span class="ant-tag">' + esc(p) + '</span>';
        }});
      }}
      if (!propsHtml) propsHtml = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      var imgsHtml = '';
      (d.images || []).forEach(function(im, i) {{
        var desc = im.description || ('\u56fe\u7247 ' + (i+1));
        imgsHtml += ''
          + '<div class="media-card" onclick="window.openMediaViewer(\\'image\\', ' + i + ', \\'' + escAttr(desc) + '\\', \\'' + escAttr(im.url || '') + '\\')">'
          + '<div class="media-thumb"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#8dcde0" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></div>'
          + '<div class="media-desc">' + esc(desc) + '</div>'
          + '</div>';
      }});
      if (!imgsHtml) imgsHtml = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      else imgsHtml = '<div class="media-grid">' + imgsHtml + '</div>';
      var vidsHtml = '';
      (d.videos || []).forEach(function(v, i) {{
        var desc = v.description || ('\u89c6\u9891 ' + (i+1));
        var dur = v.duration ? (' \u00b7 ' + v.duration + 's') : '';
        vidsHtml += ''
          + '<div class="media-card" onclick="window.openMediaViewer(\\'video\\', ' + i + ', \\'' + escAttr(desc) + '\\', \\'' + escAttr(v.url || '') + '\\')">'
          + '<div class="media-thumb media-thumb-video"><svg width="28" height="28" viewBox="0 0 24 24" fill="#1F80A0"><polygon points="6 4 20 12 6 20"/></svg></div>'
          + '<div class="media-desc">' + esc(desc) + dur + '</div>'
          + '</div>';
      }});
      if (!vidsHtml) vidsHtml = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      else vidsHtml = '<div class="media-grid">' + vidsHtml + '</div>';
      var sd = d.scene_description || '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      var cri = d.criteria || '<span style="color:rgba(0,0,0,0.25);">\u2014</span>';
      var html = ''
        + '<div style="margin-bottom:20px;">'
        + '<h4 style="margin:0 0 12px;font-size:14px;font-weight:500;color:rgba(0,0,0,0.85);">\u57fa\u672c\u4fe1\u606f</h4>'
        + '<div style="display:grid;grid-template-columns:110px 1fr;gap:10px 16px;font-size:13px;">'
        + '<span style="color:rgba(0,0,0,0.45);">\u540d\u79f0</span><span style="font-weight:500;font-size:14px;">' + esc(d.name || '--') + '</span>'
        + '<span style="color:rgba(0,0,0,0.45);">\u63cf\u8ff0</span><span>' + (d.description ? esc(d.description) : '\u2014') + '</span>'
        + '<span style="color:rgba(0,0,0,0.45);">\u521b\u5efa</span><span>' + esc(d.creator || '--') + ' \u00b7 ' + esc(d.created_at || '--') + '</span>'
        + '</div></div>'
        + '<hr style="border:none;border-top:1px solid #f0f0f0;margin:16px 0;">'
        + '<div style="margin-bottom:20px;">'
        + '<h4 style="margin:0 0 12px;font-size:14px;font-weight:500;color:rgba(0,0,0,0.85);">\u573a\u666f\u914d\u7f6e</h4>'
        + '<div style="display:grid;grid-template-columns:110px 1fr;gap:12px 16px;font-size:13px;align-items:start;margin-bottom:16px;">'
        + '<span style="color:rgba(0,0,0,0.45);">\u573a\u666f\u63cf\u8ff0</span><span style="line-height:1.8;">' + sd + '</span>'
        + '<span style="color:rgba(0,0,0,0.45);">\u4efb\u52a1\u9053\u5177</span><span style="display:flex;flex-wrap:wrap;gap:4px;">' + propsHtml + '</span>'
        + '</div>'
        + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">'
        + '<div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:8px;">\u573a\u666f\u56fe\u7247</div>' + imgsHtml + '</div>'
        + '<div><div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:8px;">\u573a\u666f\u89c6\u9891</div>' + vidsHtml + '</div>'
        + '</div>'
        + '</div>'
        + '<hr style="border:none;border-top:1px solid #f0f0f0;margin:16px 0;">'
        + '<div>'
        + '<h4 style="margin:0 0 12px;font-size:14px;font-weight:500;color:rgba(0,0,0,0.85);">\u5173\u8054\u914d\u7f6e</h4>'
        + '<div style="display:grid;grid-template-columns:110px 1fr;gap:14px 16px;font-size:13px;align-items:start;">'
        + '<span style="color:rgba(0,0,0,0.45);">\u8bc4\u4ef7\u6807\u51c6</span><span>' + cri + '</span>'
        + '<span style="color:rgba(0,0,0,0.45);">\u63d0\u793a\u8bcd (' + d.prompts.length + ')</span><div>' + promptsHtml + '</div>'
        + '</div></div>';
      document.getElementById('bm-detail-body').innerHTML = html;
      openModal('bm-detail-modal');
    }}
    </script>
    '''
    bc = (
        '<a href="/tasks" style="color:#1F80A0;">\u8bc4\u6d4b\u7ba1\u7406</a>'
        ' <span class="ant-breadcrumb-separator">/</span> '
        '<a href="/tasks" style="color:#1F80A0;">\u8bc4\u6d4b\u4efb\u52a1\u7ba1\u7406</a>'
        ' <span class="ant-breadcrumb-separator">/</span> '
        f'\u8bc4\u6d4b\u4efb\u52a1{task_no}'
    )
    return render_page(task_title, content, active="tasks", breadcrumb=bc)


@app.route("/tasks/<tid>/data/<exec_id>")
def task_data_detail(tid, exec_id):
    """Readonly evaluation data detail — reuses workbench layout with mock data."""
    t = next((x for x in EVAL_TASKS if x["id"] == tid), None)
    if not t:
        flash("\u4efb\u52a1\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("tasks_page"))
    bm = get_benchmark(t["benchmark_id"])
    bm_name = bm["name"] if bm else "--"
    et = CRITERIA_TYPES.get(t.get("eval_type", ""), {})

    requested_pid = request.args.get("pid", "")
    prompt = get_prompt(requested_pid) if requested_pid else None
    if not prompt and bm and bm.get("prompt_ids"):
        prompt = get_prompt(bm["prompt_ids"][0])
    if not prompt:
        prompt = PROMPTS[0]

    steps = prompt.get("low_levels", [])
    n_steps = len(steps)

    # A/B model names
    ckpt_a = get_model_name(t["model_ids"][0]) if len(t["model_ids"]) > 0 else "--"
    ckpt_b = get_model_name(t["model_ids"][1]) if len(t["model_ids"]) > 1 else "--"

    current_step = int(request.args.get("step", 0))
    if current_step >= n_steps:
        current_step = n_steps - 1
    if current_step < 0:
        current_step = 0
    step = steps[current_step] if steps else None

    # Build the full flat list of records (same ordering as /eval-records task view)
    # Used both for \u4e0a\u4e00\u6761 / \u4e0b\u4e00\u6761 navigation AND as the source of truth
    # for result_val / prog_a / prog_b so list and detail display the same data.
    import random as _rnd_flat
    flat = []
    for _ft in EVAL_TASKS:
        _fbm = get_benchmark(_ft["benchmark_id"])
        if not _fbm:
            continue
        _rnd_flat.seed(hash(_ft["id"]))
        for _fpid in _fbm.get("prompt_ids", []):
            _fp = get_prompt(_fpid)
            if not _fp:
                continue
            for _fsi, _fll in enumerate(_fp.get("low_levels", [])):
                _fresult = _rnd_flat.choice([4, 3, 2, 1, 0])
                _fexec = f"E{_rnd_flat.randint(1000,9999)}"
                _fpa = _rnd_flat.randint(1, 5)
                _fpb = _rnd_flat.randint(1, 5)
                flat.append({
                    "tid": _ft["id"], "exec_id": _fexec, "pid": _fpid, "step": _fsi,
                    "result": _fresult, "prog_a": _fpa, "prog_b": _fpb,
                })

    cur_idx = -1
    for _i, _r in enumerate(flat):
        if _r["tid"] == tid and _r["exec_id"] == exec_id and _r["pid"] == requested_pid and _r["step"] == current_step:
            cur_idx = _i
            break

    # Source of truth for display: use the flat row if found, otherwise fall back to local seed
    if cur_idx >= 0:
        cur_row = flat[cur_idx]
        prog_a = cur_row["prog_a"]
        prog_b = cur_row["prog_b"]
        result_val = cur_row["result"]
    else:
        # Fallback for arbitrary exec_id not in flat list
        import random as _rnd3
        _rnd3.seed(hash(exec_id + str(current_step)))
        prog_a = _rnd3.randint(1, 5)
        prog_b = _rnd3.randint(1, 5)
        result_val = _rnd3.choice([4, 3, 2, 1, 0])

    # Note text (not shown in list, so independent random is fine)
    import random as _rnd_note
    _rnd_note.seed(hash(exec_id + "_note_" + str(current_step)))
    note_text = _rnd_note.choice(["Policy A \u62d3\u53d6\u66f4\u7cbe\u51c6", "\u4e24\u8005\u8868\u73b0\u63a5\u8fd1", "Policy B \u5b8c\u6210\u901f\u5ea6\u66f4\u5feb", "\u8def\u5f84\u89c4\u5212\u5408\u7406", ""])
    pct = round(current_step / max(n_steps, 1) * 100)

    pref_a_cls = "pref-a pref-active" if result_val == 4 else "pref-a"
    pref_tie_a_cls = "pref-tie pref-active" if result_val == 3 else "pref-tie"
    pref_tie_m_cls = "pref-tie pref-active" if result_val == 2 else "pref-tie"
    pref_tie_b_cls = "pref-tie pref-active" if result_val == 1 else "pref-tie"
    pref_b_cls = "pref-b pref-active" if result_val == 0 else "pref-b"

    task_no = t.get("task_no", tid)
    page_title = f"\u6267\u884c\u8bb0\u5f55{exec_id}"

    step_hl = prompt["high_level"] if prompt else "--"
    step_zh = step["zh"] if step else "--"
    step_en = step["en"] if step else ""

    def _url_of(r):
        return f'/tasks/{r["tid"]}/data/{r["exec_id"]}?pid={r["pid"]}&step={r["step"]}'

    if cur_idx > 0:
        prev_link = f'<a href="{_url_of(flat[cur_idx-1])}" style="color:#1F80A0;text-decoration:none;font-size:14px;">&larr; \u4e0a\u4e00\u6761</a>'
    else:
        prev_link = '<span style="color:rgba(0,0,0,0.15);font-size:14px;">&larr; \u4e0a\u4e00\u6761</span>'
    if cur_idx >= 0 and cur_idx < len(flat) - 1:
        next_link = f'<a href="{_url_of(flat[cur_idx+1])}" style="color:#1F80A0;text-decoration:none;font-size:14px;">\u4e0b\u4e00\u6761 &rarr;</a>'
    else:
        next_link = '<span style="color:rgba(0,0,0,0.15);font-size:14px;">\u4e0b\u4e00\u6761 &rarr;</span>'

    content = f'''
    <!-- Header -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:16px;font-weight:500;">{t["name"]}</span>
        <span class="ant-tag">{exec_id}</span>
        <span class="ant-tag">{et.get("label","")}</span>
      </div>
    </div>

    <!-- Top: themed prompt bar -->
    <div style="background:#e6f4f8;border:1px solid #b8dce8;border-radius:8px;padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;gap:10px;">
      <span style="font-size:12px;color:rgba(0,0,0,0.45);">High Level:</span>
      <span style="font-weight:600;color:#1F80A0;">{step_hl}</span>
      <span style="width:1px;height:16px;background:#b8dce8;"></span>
      <span style="font-size:12px;color:rgba(0,0,0,0.45);">Low Level:</span>
      <span style="font-weight:600;">{step_zh}</span>
      <span style="color:rgba(0,0,0,0.35);font-size:13px;">{step_en}</span>
    </div>

    <!-- Video area: grey bg, white A/B cards, fixed height -->
    <div style="background:#f0f0f0;border-radius:8px;padding:12px;margin-bottom:16px;">
      <div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:start;">
        <!-- Model A -->
        <div style="background:#fff;border-radius:8px;overflow:hidden;">
          <div style="display:flex;align-items:baseline;gap:8px;padding:8px 12px;">
            <span style="font-size:15px;font-weight:600;">\u6a21\u578b A</span>
            <span style="font-size:14px;color:#1F80A0;font-weight:500;">{ckpt_a}</span>
          </div>
          <div style="height:360px;background:#000;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.25);font-size:13px;">\u91c7\u96c6\u89c6\u9891\u56de\u653e &middot; 640x480</div>
        </div>
        <div style="padding:0 10px;font-size:14px;color:rgba(0,0,0,0.15);font-weight:600;align-self:center;">VS</div>
        <!-- Model B -->
        <div style="background:#fff;border-radius:8px;overflow:hidden;">
          <div style="display:flex;align-items:baseline;gap:8px;padding:8px 12px;">
            <span style="font-size:15px;font-weight:600;">\u6a21\u578b B</span>
            <span style="font-size:14px;color:#1F80A0;font-weight:500;">{ckpt_b}</span>
          </div>
          <div style="height:360px;background:#000;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.25);font-size:13px;">\u91c7\u96c6\u89c6\u9891\u56de\u653e &middot; 640x480</div>
        </div>
      </div>
    </div>

    <!-- Bottom white card: readonly progress + note + actions -->
    <div style="background:#fff;border-radius:8px;padding:20px;border:1px solid #f0f0f0;">
      <!-- Progress scores (readonly, 1-5) -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:16px;">
        <div style="display:flex;align-items:center;gap:10px;">
          <span style="color:rgba(0,0,0,0.85);font-weight:500;white-space:nowrap;">A:</span>
          <div class="ro-slider" style="flex:1;">
            <div class="ro-slider-fill" style="width:{(prog_a - 1) * 25}%;"></div>
            <div class="ro-slider-thumb" style="left:{(prog_a - 1) * 25}%;"></div>
          </div>
          <span style="font-weight:600;color:#1F80A0;min-width:14px;text-align:right;">{prog_a}</span>
          <span style="font-size:13px;color:rgba(0,0,0,0.35);">/ 5 \u5206</span>
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
          <span style="color:rgba(0,0,0,0.85);font-weight:500;white-space:nowrap;">B:</span>
          <div class="ro-slider" style="flex:1;">
            <div class="ro-slider-fill" style="width:{(prog_b - 1) * 25}%;"></div>
            <div class="ro-slider-thumb" style="left:{(prog_b - 1) * 25}%;"></div>
          </div>
          <span style="font-weight:600;color:#1F80A0;min-width:14px;text-align:right;">{prog_b}</span>
          <span style="font-size:13px;color:rgba(0,0,0,0.35);">/ 5 \u5206</span>
        </div>
      </div>
      <!-- Note (readonly) -->
      <div style="margin-bottom:20px;">
        <textarea rows="2" readonly style="width:100%;padding:10px 14px;border:1px solid #d9d9d9;border-radius:8px;font-size:14px;resize:vertical;box-sizing:border-box;background:#fafafa;color:rgba(0,0,0,0.65);">{note_text if note_text else "--"}</textarea>
      </div>
      <!-- Bottom actions: 5 preference options -->
      <div style="display:flex;align-items:center;">
        <div style="flex-shrink:0;">{prev_link}</div>
        <div style="display:flex;gap:6px;flex:1;justify-content:center;">
          <span class="pref-opt {pref_a_cls}" style="flex:1;max-width:140px;padding:10px 0;font-size:14px;text-align:center;cursor:default;">A \u80dc</span>
          <span class="pref-opt {pref_tie_a_cls}" style="flex:1;max-width:140px;padding:10px 0;font-size:14px;text-align:center;cursor:default;">\u90fd\u597d</span>
          <span class="pref-opt {pref_tie_m_cls}" style="flex:1;max-width:140px;padding:10px 0;font-size:14px;text-align:center;cursor:default;">\u90fd\u4e00\u822c</span>
          <span class="pref-opt {pref_tie_b_cls}" style="flex:1;max-width:140px;padding:10px 0;font-size:14px;text-align:center;cursor:default;">\u90fd\u5dee</span>
          <span class="pref-opt {pref_b_cls}" style="flex:1;max-width:140px;padding:10px 0;font-size:14px;text-align:center;cursor:default;">B \u80dc</span>
        </div>
        <div style="flex-shrink:0;">{next_link}</div>
      </div>
    </div>

    <style>
      .pref-opt {{ display:inline-block; padding:4px 16px; border:1px solid #d9d9d9; border-radius:8px; font-size:13px; background:#fff; color:rgba(0,0,0,0.65); white-space:nowrap; transition:all 0.2s; }}
      .pref-a.pref-active {{ background:#e6f4f8; color:#1F80A0; border-color:#1F80A0; font-weight:500; }}
      .pref-tie.pref-active {{ background:#f5f5f5; color:rgba(0,0,0,0.65); border-color:#8c8c8c; font-weight:500; }}
      .pref-b.pref-active {{ background:#e6f4f8; color:#1F80A0; border-color:#1F80A0; font-weight:500; }}
      .ro-slider {{ position:relative; height:14px; display:flex; align-items:center; }}
      .ro-slider::before {{ content:''; position:absolute; left:0; right:0; height:4px; background:rgba(31,128,160,0.15); border-radius:2px; top:50%; transform:translateY(-50%); }}
      .ro-slider-fill {{ position:absolute; left:0; height:4px; background:#1F80A0; border-radius:2px; top:50%; transform:translateY(-50%); }}
      .ro-slider-thumb {{ position:absolute; width:14px; height:14px; background:#fff; border:2px solid #1F80A0; border-radius:50%; top:50%; transform:translate(-50%,-50%); box-shadow:0 2px 4px rgba(0,0,0,0.08); }}
    </style>
    '''
    bc = (
        '<a href="/tasks" style="color:#1F80A0;">\u8bc4\u6d4b\u7ba1\u7406</a>'
        ' <span class="ant-breadcrumb-separator">/</span> '
        '<a href="/eval-records" style="color:#1F80A0;">\u8bc4\u6d4b\u7ed3\u679c\u8bb0\u5f55</a>'
        ' <span class="ant-breadcrumb-separator">/</span> '
        f'\u6267\u884c\u8bb0\u5f55{exec_id}'
    )
    return render_page(page_title, content, active="eval_records", breadcrumb=bc)


# ── Data Collection (Robot-side HMI) ──
@app.route("/collect")
def collect_list():
    active_tasks = [t for t in EVAL_TASKS if t["status"] in ("\u91c7\u96c6\u4e2d",)]
    cards = ""
    for t in active_tasks:
        bm = get_benchmark(t["benchmark_id"])
        bm_name = bm["name"] if bm else "--"
        et = CRITERIA_TYPES.get(t.get("eval_type", ""), {})
        total = max(t.get("total_sessions", 1), 1)
        pct = round(t.get("collect_done", 0) / total * 100)
        model_count = len(t["model_ids"])
        cards += (
            '<div class="ant-card ant-card-bordered" style="margin-bottom:12px;">'
            '<div class="ant-card-body" style="display:flex;align-items:center;padding:16px 20px;">'
            '<div style="flex:1;min-width:0;">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
            f'<span style="font-size:15px;font-weight:500;">{t["name"]}</span>'
            f'<span class="ant-tag ant-tag-{et.get("color","")}">{et.get("label","")}</span>'
            f'</div>'
            f'<div style="font-size:13px;color:rgba(0,0,0,0.45);">'
            f'Benchmark: {bm_name} &middot; \u91c7\u96c6\u8fdb\u5ea6: {t.get("collect_done",0)}/{t["total_sessions"]}'
            f'</div>'
            '</div>'
            f'<a href="/collect/{t["id"]}/setup" class="ant-btn ant-btn-primary" style="flex-shrink:0;margin-left:16px;">\u8fdb\u5165\u91c7\u96c6</a>'
            '</div></div>'
        )
    if not cards:
        cards = '<div style="text-align:center;padding:60px;color:rgba(0,0,0,0.25);">\u6682\u65e0\u5f85\u91c7\u96c6\u4efb\u52a1</div>'

    notice = '<div style="background:#fff1f0;border:1px solid #ffa39e;border-radius:8px;padding:8px 16px;margin-bottom:12px;font-size:13px;color:#cf1322;display:flex;align-items:center;gap:8px;"><span style="font-size:16px;">&#9888;</span> \u672c\u6a21\u5757\u4e3a\u91c7\u96c6\u7aef\u529f\u80fd\uff0c\u9875\u9762\u4ec5\u793a\u610f\u7528</div>'
    content = f'''
    {notice}
    <div style="margin-bottom:16px;font-size:13px;color:rgba(0,0,0,0.45);">\u5171 {len(active_tasks)} \u4e2a\u5f85\u91c7\u96c6\u4efb\u52a1</div>
    {cards}
    '''
    return render_page("\u8bc4\u6d4b\u6570\u636e\u91c7\u96c6", content, active="collect")


@app.route("/collect/<task_id>/setup")
def collect_setup(task_id):
    """Step 0: Task setup — select project / mode / device / deploy."""
    task = next((t for t in EVAL_TASKS if t["id"] == task_id), None)
    if not task:
        flash("\u4efb\u52a1\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("collect_list"))

    notice = '<div style="background:#fff1f0;border:1px solid #ffa39e;border-radius:8px;padding:8px 16px;margin-bottom:12px;font-size:13px;color:#cf1322;display:flex;align-items:center;gap:8px;"><span style="font-size:16px;">&#9888;</span> \u672c\u6a21\u5757\u4e3a\u91c7\u96c6\u7aef\u529f\u80fd\uff0c\u9875\u9762\u4ec5\u793a\u610f\u7528</div>'

    content = f'''
    {notice}
    <div style="background:#fff;border-radius:8px;padding:24px;border:1px solid #f0f0f0;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
      <span style="font-size:18px;font-weight:600;">\u91c7\u96c6\u4efb\u52a1</span>
      <a href="/collect" class="ant-btn">\u8fd4\u56de\u5217\u8868</a>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px 32px;margin-bottom:24px;">
      <div class="form-group">
        <label>\u9879\u76ee</label>
        <select class="has-value"><option>\u6210\u529f</option><option>Quanta-\u5ba4\u5185</option></select>
      </div>
      <div class="form-group">
        <label>\u6a21\u5f0f</label>
        <select class="has-value"><option>test</option><option>train</option><option>demo</option></select>
      </div>
      <div class="form-group">
        <label>\u4efb\u52a1</label>
        <select class="has-value"><option>{task["name"]}</option></select>
      </div>
      <div class="form-group">
        <label>\u8bbe\u5907</label>
        <select class="has-value" disabled style="background:#f5f5f5;color:rgba(0,0,0,0.25);cursor:not-allowed;"><option>Franka</option></select>
      </div>
      <div class="form-group">
        <label>\u90e8\u7f72</label>
        <select class="has-value" disabled style="background:#f5f5f5;color:rgba(0,0,0,0.25);cursor:not-allowed;"><option>\u4e91\u7aef\u90e8\u7f72</option></select>
      </div>
    </div>

    </div>
    <div style="text-align:center;padding:8px 0;margin-top:20px;">
      <a href="/collect/{task_id}" class="ant-btn ant-btn-primary ant-btn-lg" style="padding:10px 48px;font-size:15px;">\u4e0b\u4e00\u6b65</a>
    </div>
    '''
    return render_page("\u91c7\u96c6\u4efb\u52a1", content, active="collect")


@app.route("/collect/<task_id>")
def collect_prep(task_id):
    """Step 1: Scene preparation (same as old evaluate_prep)."""
    task = next((t for t in EVAL_TASKS if t["id"] == task_id), None)
    if not task:
        flash("\u4efb\u52a1\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("collect_list"))
    bm = get_benchmark(task["benchmark_id"])
    bm_name = bm["name"] if bm else "--"
    et = CRITERIA_TYPES.get(task.get("eval_type", ""), {})
    pct = round(task["completed_sessions"] / task["total_sessions"] * 100) if task["total_sessions"] > 0 else 0

    # Scene info — match the new benchmark scene structure (scene_description / props / images / videos)
    sc = get_scene(bm.get("scene_id", "")) if bm else None
    scene_html = ""
    if bm:
        # Scene description: explicit field, fallback to linked scene description
        scene_desc = bm.get("scene_description", "").strip() if bm else ""
        if not scene_desc and sc:
            env = sc.get("environment", {})
            ws = env.get("workspace", {})
            cond = env.get("conditions", {})
            scene_desc = f'{sc.get("description","")} \u00b7 \u5de5\u4f5c\u533a {ws.get("length",0)}x{ws.get("width",0)}x{ws.get("height",0)}cm \u00b7 {cond.get("lighting","")}'
        scene_desc_html = scene_desc if scene_desc else '<span style="color:rgba(0,0,0,0.25);">\u2014</span>'

        # Props
        props_raw = bm.get("props", "").strip() if bm else ""
        if not props_raw and sc:
            props_raw = "\u3001".join(o.get("name", "") for o in sc.get("objects", []) if o.get("name"))
        props_html = ""
        if props_raw:
            for prop in [x.strip() for x in props_raw.replace("\uff0c", ",").replace("\u3001", ",").split(",") if x.strip()]:
                props_html += f'<span class="ant-tag">{prop}</span>'
        if not props_html:
            props_html = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>'

        # Images / videos (from scene references)
        refs = sc.get("references", {}) if sc else {}
        imgs_list = refs.get("images", [])
        videos_list = refs.get("capture_videos", []) + refs.get("demo_videos", [])
        _empty = '<span style="color:rgba(0,0,0,0.25);">\u2014</span>'
        if imgs_list:
            img_items = ""
            for i, im in enumerate(imgs_list):
                desc = im.get("description", f"\u56fe\u7247 {i+1}")
                url = im.get("url", "")
                img_items += (
                    f'<div class="media-card" onclick="window.openMediaViewer(\'image\', {i!r}, {desc!r}, {url!r})">'
                    f'<div class="media-thumb"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#8dcde0" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></div>'
                    f'<div class="media-desc">{desc}</div>'
                    f'</div>'
                )
            img_grid = f'<div class="media-grid">{img_items}</div>'
        else:
            img_grid = _empty
        if videos_list:
            vid_items = ""
            for i, v in enumerate(videos_list):
                desc = v.get("description", f"\u89c6\u9891 {i+1}")
                url = v.get("url", "")
                dur = v.get("duration", 0)
                dur_str = f" &middot; {dur}s" if dur else ""
                vid_items += (
                    f'<div class="media-card" onclick="window.openMediaViewer(\'video\', {i!r}, {desc!r}, {url!r})">'
                    f'<div class="media-thumb media-thumb-video"><svg width="28" height="28" viewBox="0 0 24 24" fill="#1F80A0"><polygon points="6 4 20 12 6 20"/></svg></div>'
                    f'<div class="media-desc">{desc}{dur_str}</div>'
                    f'</div>'
                )
            vid_grid = f'<div class="media-grid">{vid_items}</div>'
        else:
            vid_grid = _empty

        scene_html = f'''
        <div class="ant-card ant-card-bordered" style="margin-bottom:16px;">
          <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;font-size:15px;font-weight:500;">\u573a\u666f\u4fe1\u606f</div>
          <div class="ant-card-body">
            <div style="display:grid;grid-template-columns:110px 1fr;gap:12px 16px;font-size:14px;align-items:start;margin-bottom:16px;">
              <span style="color:rgba(0,0,0,0.45);">\u573a\u666f\u63cf\u8ff0</span>
              <span style="line-height:1.8;">{scene_desc_html}</span>
              <span style="color:rgba(0,0,0,0.45);">\u4efb\u52a1\u9053\u5177</span>
              <span style="display:flex;flex-wrap:wrap;gap:4px;">{props_html}</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
              <div>
                <div style="font-size:13px;color:rgba(0,0,0,0.45);margin-bottom:8px;">\u573a\u666f\u56fe\u7247</div>
                {img_grid}
              </div>
              <div>
                <div style="font-size:13px;color:rgba(0,0,0,0.45);margin-bottom:8px;">\u573a\u666f\u89c6\u9891</div>
                {vid_grid}
              </div>
            </div>
          </div>
        </div>'''

    # Prompts tree
    prompt_list = ""
    if bm and bm.get("prompt_ids"):
        for pi, pid in enumerate(bm["prompt_ids"]):
            p = get_prompt(pid)
            if not p:
                continue
            lls = p.get("low_levels", [])
            sub_html = ""
            for si, ll in enumerate(lls):
                sub_html += f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0 5px 28px;font-size:13px;color:rgba(0,0,0,0.65);border-bottom:1px solid #fafafa;"><span style="color:rgba(0,0,0,0.25);min-width:16px;">{si+1}</span><span>{ll["zh"]}</span><span style="color:rgba(0,0,0,0.35);">{ll["en"]}</span></div>'
            uid = f"col-prompt-{pi}"
            prompt_list += f'<div style="border-bottom:1px solid #f0f0f0;"><div style="display:flex;align-items:center;gap:8px;padding:8px 0;cursor:pointer;" onclick="var c=document.querySelectorAll(\'.{uid}\');var show=c[0]&&c[0].style.display===\'none\';c.forEach(function(r){{r.style.display=show?\'\':\'none\';}});this.querySelector(\'.pa\').style.transform=show?\'rotate(90deg)\':\'\'"><span class="pa" style="font-size:10px;color:rgba(0,0,0,0.3);transition:transform 0.2s;display:inline-block;">&#9654;</span><span style="font-weight:500;">{p["high_level"]}</span><span style="color:rgba(0,0,0,0.35);">{p["high_level_en"]}</span><span class="ant-tag">{len(lls)} \u6b65</span></div><div class="{uid}" style="display:none;">{sub_html}</div></div>'
    if not prompt_list:
        prompt_list = '<span style="color:rgba(0,0,0,0.25);">\u672a\u5173\u8054\u63d0\u793a\u8bcd</span>'
    prompt_count = len(bm.get("prompt_ids", [])) if bm else 0

    # Criteria
    cr = get_criterion(bm.get("criteria_id", "")) if bm else None
    cr_html = ""
    if cr:
        cr_type = CRITERIA_TYPES.get(cr["type"], {})
        cr_html = f'<span class="ant-tag ant-tag-{cr_type.get("color","")}">{cr_type.get("label","")}</span> {cr["name"]}'

    content = f'''
    <div style="background:#fff1f0;border:1px solid #ffa39e;border-radius:8px;padding:8px 16px;margin-bottom:12px;font-size:13px;color:#cf1322;display:flex;align-items:center;gap:8px;"><span style="font-size:16px;">&#9888;</span> \u672c\u6a21\u5757\u4e3a\u91c7\u96c6\u7aef\u529f\u80fd\uff0c\u9875\u9762\u4ec5\u793a\u610f\u7528</div>
    {scene_html}
    <div class="ant-card ant-card-bordered" style="margin-bottom:20px;">
      <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;font-size:15px;font-weight:500;">\u63d0\u793a\u8bcd\u7ec4 ({prompt_count} \u7ec4)</div>
      <div class="ant-card-body" style="padding:12px 20px;">{prompt_list}</div>
    </div>
    <div style="text-align:center;padding:8px 0;">
      <a href="/collect/{task_id}/run" class="ant-btn ant-btn-primary ant-btn-lg" style="padding:10px 48px;font-size:15px;">\u573a\u666f\u5df2\u5c31\u7eea\uff0c\u5f00\u59cb\u91c7\u96c6</a>
      <div style="margin-top:8px;font-size:12px;color:rgba(0,0,0,0.35);">\u8bf7\u786e\u8ba4\u5df2\u6309\u573a\u666f\u8981\u6c42\u5e03\u7f6e\u597d\u73af\u5883\u548c\u7269\u4f53</div>
    </div>
    '''
    return render_page("\u91c7\u96c6\u51c6\u5907", content, active="collect")


@app.route("/collect/<task_id>/run")
def collect_run(task_id):
    """Step 2: HMI-style data collection interface."""
    task = next((t for t in EVAL_TASKS if t["id"] == task_id), None)
    if not task:
        flash("\u4efb\u52a1\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("collect_list"))
    bm = get_benchmark(task["benchmark_id"])
    # Pick a prompt
    prompt = None
    requested_pid = request.args.get("pid", "")
    if requested_pid:
        prompt = get_prompt(requested_pid)
    if not prompt and bm and bm.get("prompt_ids"):
        prompt = get_prompt(bm["prompt_ids"][0])
    if not prompt:
        prompt = PROMPTS[0]
    steps = prompt.get("low_levels", [])
    n_steps = len(steps)
    prompt_count = len(bm.get("prompt_ids", [])) if bm else 0
    current_group = min(task["completed_sessions"] + 1, prompt_count) if prompt_count > 0 else 1
    pct = round(task["completed_sessions"] / task["total_sessions"] * 100) if task["total_sessions"] > 0 else 0

    # Prompt group selector
    prompt_opts = ""
    if bm and bm.get("prompt_ids"):
        for ppid in bm["prompt_ids"]:
            pp = get_prompt(ppid)
            if pp:
                sel = "selected" if ppid == prompt["id"] else ""
                prompt_opts += f'<option value="/collect/{task_id}/run?pid={ppid}" {sel}>{pp["high_level"]}</option>'

    # Step list (clean style)
    step_rows = ""
    for i, ll in enumerate(steps):
        step_rows += (
            f'<div class="hmi-step" id="hmi-step-{i}" style="display:flex;align-items:center;padding:10px 14px;border-bottom:1px solid #f0f0f0;">'
            f'<span style="width:24px;height:24px;border-radius:50%;background:#1F80A0;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;margin-right:12px;flex-shrink:0;">{i+1}</span>'
            f'<span style="flex:1;font-size:14px;color:rgba(0,0,0,0.85);">{ll["zh"]}</span>'
            f'<div id="hmi-actions-{i}" style="display:flex;align-items:center;gap:6px;flex-shrink:0;">'
            f'<button type="button" class="ant-btn ant-btn-sm ant-btn-primary" onclick="hmiExec({i})">&#9654; \u6267\u884c</button>'
            f'</div>'
            f'</div>'
        )

    content = f'''
    <!-- Demo notice -->
    <div style="background:#fff1f0;border:1px solid #ffa39e;border-radius:8px;padding:8px 16px;margin-bottom:10px;font-size:13px;color:#cf1322;display:flex;align-items:center;gap:8px;">
      <span style="font-size:16px;">&#9888;</span> \u672c\u6a21\u5757\u4e3a\u91c7\u96c6\u7aef\u529f\u80fd\uff0c\u9875\u9762\u4ec5\u793a\u610f\u7528
    </div>
    <!-- Header -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <a href="/collect/{task_id}" class="ant-btn ant-btn-sm">&larr; \u5b8c\u6210</a>
        <span style="font-size:15px;font-weight:500;">{task["name"]}</span>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:13px;color:rgba(0,0,0,0.45);">\u8bbe\u5907: Franka</span>
        <span class="ant-tag ant-tag-green">\u91c7\u96c6\u4e2d</span>
      </div>
    </div>

    <!-- Three cameras -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:10px;">
      <div style="background:#141414;border-radius:8px;overflow:hidden;border:1px solid #333;">
        <div style="display:flex;justify-content:space-between;padding:6px 10px;font-size:12px;color:rgba(255,255,255,0.6);"><span>\u5de6\u624b\u6444\u50cf\u5934</span><span style="color:#1F80A0;">\u2022 \u5df2\u8fde\u63a5</span></div>
        <div style="height:260px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.12);">640x480</div>
        <div style="display:flex;justify-content:space-between;padding:4px 10px;font-size:11px;color:rgba(255,255,255,0.35);">\u5206\u8fa8\u7387:640x480<span>FPS: 28.9</span><span>13:51:46</span></div>
      </div>
      <div style="background:#141414;border-radius:8px;overflow:hidden;border:1px solid #333;">
        <div style="display:flex;justify-content:space-between;padding:6px 10px;font-size:12px;color:rgba(255,255,255,0.6);"><span>\u5934\u90e8\u6444\u50cf\u5934</span><span style="color:#1F80A0;">\u2022 \u5df2\u8fde\u63a5</span></div>
        <div style="height:260px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.12);">640x480</div>
        <div style="display:flex;justify-content:space-between;padding:4px 10px;font-size:11px;color:rgba(255,255,255,0.35);">\u5206\u8fa8\u7387:640x480<span>FPS: 28.9</span><span>13:51:46</span></div>
      </div>
      <div style="background:#141414;border-radius:8px;overflow:hidden;border:1px solid #333;">
        <div style="display:flex;justify-content:space-between;padding:6px 10px;font-size:12px;color:rgba(255,255,255,0.6);"><span>\u53f3\u624b\u6444\u50cf\u5934</span><span style="color:#1F80A0;">\u2022 \u5df2\u8fde\u63a5</span></div>
        <div style="height:260px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.12);">640x480</div>
        <div style="display:flex;justify-content:space-between;padding:4px 10px;font-size:11px;color:rgba(255,255,255,0.35);">\u5206\u8fa8\u7387:640x480<span>FPS: 28.9</span><span>13:51:46</span></div>
      </div>
    </div>

    <!-- Two-column: left=prompts, right=device control -->
    <div style="display:grid;grid-template-columns:1fr 260px;gap:12px;align-items:stretch;">
      <!-- Left: task prompts -->
      <div class="ant-card ant-card-bordered" style="display:flex;flex-direction:column;height:380px;">
        <div style="display:flex;align-items:center;gap:10px;padding:10px 16px;border-bottom:1px solid #f0f0f0;flex-shrink:0;">
          <span style="font-size:14px;font-weight:500;white-space:nowrap;">\u4efb\u52a1\u63d0\u793a</span>
          <select style="min-width:200px;height:32px;padding:4px 28px 4px 10px;border:1px solid #d9d9d9;border-radius:8px;font-size:13px;color:#1F80A0;-webkit-appearance:none;appearance:none;" onchange="if(this.value) window.location=this.value;">{prompt_opts}</select>
          <span style="flex:1;"></span>
          <span style="font-size:12px;color:rgba(0,0,0,0.45);white-space:nowrap;">\u7ec4: {current_group}/{prompt_count}</span>
          <span style="font-size:12px;color:rgba(0,0,0,0.45);white-space:nowrap;">\u6b21: {task["completed_sessions"]}/{task["total_sessions"]}</span>
        </div>
        <div style="padding:0;flex:1;overflow-y:auto;">{step_rows}</div>
      </div>

      <!-- Right: device control -->
      <div class="ant-card ant-card-bordered" style="height:380px;display:flex;flex-direction:column;">
        <div style="padding:10px 14px;border-bottom:1px solid #f0f0f0;font-size:14px;font-weight:500;flex-shrink:0;">\u5f00\u5173</div>
        <div style="padding:10px 14px;flex-shrink:0;">
          <div style="display:grid;grid-template-columns:1fr auto;gap:8px 10px;font-size:13px;align-items:center;">
            <span>\u8bbe\u5907\u4e0a\u7535</span><label class="capsule on" onclick="this.classList.toggle('on')"><span class="capsule-dot"></span></label>
            <span>\u968f\u52a8\u72b6\u6001</span><label class="capsule on" onclick="this.classList.toggle('on')"><span class="capsule-dot"></span></label>
          </div>
        </div>
        <div style="padding:10px 14px;border-top:1px solid #f0f0f0;font-size:14px;font-weight:500;flex-shrink:0;">\u8fde\u63a5\u72b6\u6001</div>
        <div style="padding:8px 14px;font-size:13px;flex-shrink:0;">
          <div style="display:flex;justify-content:space-between;padding:3px 0;"><span>&bull; Capturex</span><span style="color:#1F80A0;">\u2022 \u5df2\u8fde\u63a5</span></div>
          <div style="display:flex;justify-content:space-between;padding:3px 0;"><span>&bull; Franka</span><span style="color:#1F80A0;">\u2022 \u5df2\u8fde\u63a5</span></div>
          <div style="display:flex;justify-content:space-between;padding:3px 0;"><span>&bull; Teleop</span><span style="color:#1F80A0;">\u2022 \u5df2\u8fde\u63a5</span></div>
        </div>
        <div style="flex:1;"></div>
        <div style="padding:10px 14px;border-top:1px solid #f0f0f0;display:flex;gap:8px;flex-shrink:0;">
          <button type="button" class="ant-btn ant-btn-primary" style="flex:1;" onclick="alert('\u4f3a\u670d\u590d\u4f4d')">\u590d\u4f4d</button>
          <button type="button" class="ant-btn" style="flex:1;" onclick="hmiGlobalReset()">\u91cd\u7f6e</button>
          <button type="button" class="ant-btn" style="flex:1;color:#ff4d4f;border-color:#ff4d4f;" onclick="hmiGlobalStop()">\u505c\u6b62</button>
        </div>
        <div style="padding:6px 14px 10px;font-size:12px;color:rgba(0,0,0,0.35);line-height:1.6;flex-shrink:0;">
          \u590d\u4f4d\uff1a\u4f3a\u670d\u590d\u4f4d<br>
          \u91cd\u7f6e\uff1a\u91cd\u7f6e\u6574\u7ec4\u6570\u636e<br>
          \u505c\u6b62\uff1a\u624b\u52a8\u505c\u6b62\u6267\u884c\u548c\u63a8\u7406
        </div>
      </div>
    </div>

    <style>
      /* capsule styles in BASE_CSS */
    </style>

    <script>
    var hmiStepCount = {n_steps};
    var hmiLatestDone = -1;
    function hmiIdleHtml(idx) {{
      return '<button type="button" class="ant-btn ant-btn-sm ant-btn-primary" onclick="hmiExec('+idx+')">&#9654; \u6267\u884c</button>';
    }}
    function hmiStripCorrect(idx) {{
      // Remove correct and reset buttons from a previously-latest step, keep only tag
      var box = document.getElementById('hmi-actions-'+idx);
      if (!box) return;
      var cb = box.querySelector('.hmi-correct-btn');
      if (cb) cb.remove();
      var rb = box.querySelector('.hmi-reset-btn');
      if (rb) rb.remove();
    }}
    function hmiExec(idx) {{
      var box = document.getElementById('hmi-actions-'+idx);
      var step = document.getElementById('hmi-step-'+idx);
      step.style.background = '#f0f7f9';
      box.innerHTML = '<button type="button" class="ant-btn ant-btn-sm ant-btn-primary" disabled style="pointer-events:none;opacity:0.7;">'
        + '<span class="hmi-spin"></span> \u6267\u884c\u4e2d</button>';
      window['hmiTimer'+idx] = setTimeout(function() {{ hmiDone(idx); }}, 1500);
    }}
    function hmiDone(idx) {{
      var box = document.getElementById('hmi-actions-'+idx);
      var step = document.getElementById('hmi-step-'+idx);
      step.style.background = '#f0f7f9';
      box.innerHTML = '<button type="button" class="ant-btn ant-btn-sm" style="color:#1F80A0;border-color:#1F80A0;" onclick="hmiResult('+idx+',2)">\u2713 \u6210\u529f\u5e76\u4e0b\u4e00\u6761</button>'
        + '<button type="button" class="ant-btn ant-btn-sm" style="color:#52c41a;border-color:#52c41a;" onclick="hmiResult('+idx+',1)">\u2713 \u6210\u529f</button>'
        + '<button type="button" class="ant-btn ant-btn-sm" style="color:#ff4d4f;border-color:#ff4d4f;" onclick="hmiResult('+idx+',0)">\u2717 \u5931\u8d25</button>';
    }}
    function hmiResult(idx, code) {{
      // Strip correct button from previous latest
      if (hmiLatestDone >= 0 && hmiLatestDone !== idx) {{
        hmiStripCorrect(hmiLatestDone);
      }}
      hmiLatestDone = idx;
      var box = document.getElementById('hmi-actions-'+idx);
      var step = document.getElementById('hmi-step-'+idx);
      if (code >= 1) {{
        step.style.background = '';
        box.innerHTML = '<button type="button" class="ant-btn ant-btn-sm hmi-correct-btn" onclick="hmiCorrect('+idx+')">\u4fee\u6b63</button>'
          + '<span class="ant-tag" style="background:#52c41a;color:#fff;border-color:#52c41a;">\u2713 \u6210\u529f</span>';
        if (code === 2) {{
          var next = idx + 1;
          if (next < hmiStepCount) {{ hmiExec(next); }}
        }}
      }} else {{
        step.style.background = '';
        box.innerHTML = '<button type="button" class="ant-btn ant-btn-sm hmi-correct-btn" onclick="hmiCorrect('+idx+')">\u4fee\u6b63</button>'
          + '<button type="button" class="ant-btn ant-btn-sm hmi-reset-btn" onclick="hmiReset('+idx+')">\u91cd\u7f6e</button>'
          + '<span class="ant-tag" style="background:#ff4d4f;color:#fff;border-color:#ff4d4f;">\u2717 \u5931\u8d25</span>';
      }}
    }}
    function hmiCorrect(idx) {{
      var box = document.getElementById('hmi-actions-'+idx);
      var step = document.getElementById('hmi-step-'+idx);
      step.style.background = '#f0f7f9';
      box.innerHTML = '<button type="button" class="ant-btn ant-btn-sm" style="color:#1F80A0;border-color:#1F80A0;" onclick="hmiResult('+idx+',2)">\u2713 \u6210\u529f\u5e76\u4e0b\u4e00\u6761</button>'
        + '<button type="button" class="ant-btn ant-btn-sm" style="color:#52c41a;border-color:#52c41a;" onclick="hmiResult('+idx+',1)">\u2713 \u6210\u529f</button>'
        + '<button type="button" class="ant-btn ant-btn-sm" style="color:#ff4d4f;border-color:#ff4d4f;" onclick="hmiResult('+idx+',0)">\u2717 \u5931\u8d25</button>';
    }}
    function hmiReset(idx) {{
      var box = document.getElementById('hmi-actions-'+idx);
      var step = document.getElementById('hmi-step-'+idx);
      step.style.background = '';
      box.innerHTML = hmiIdleHtml(idx);
    }}
    function hmiGlobalStop() {{
      for (var i = 0; i < hmiStepCount; i++) {{
        if (window['hmiTimer'+i]) {{ clearTimeout(window['hmiTimer'+i]); }}
        var box = document.getElementById('hmi-actions-'+i);
        if (box.querySelector('.hmi-spin')) {{
          var step = document.getElementById('hmi-step-'+i);
          step.style.background = '';
          box.innerHTML = hmiIdleHtml(i);
        }}
      }}
    }}
    function hmiGlobalReset() {{
      for (var i = 0; i < hmiStepCount; i++) {{
        if (window['hmiTimer'+i]) {{ clearTimeout(window['hmiTimer'+i]); }}
        var box = document.getElementById('hmi-actions-'+i);
        var step = document.getElementById('hmi-step-'+i);
        step.style.background = '';
        box.innerHTML = hmiIdleHtml(i);
      }}
    }}
    </script>
    <style>.hmi-spin {{ display:inline-block;width:12px;height:12px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:hmiSp 0.6s linear infinite;margin-right:4px;vertical-align:middle; }} @keyframes hmiSp {{ to {{ transform:rotate(360deg); }} }}</style>
    '''
    return render_page("\u6570\u636e\u91c7\u96c6", content, active="collect")


# ── Evaluation Workbench ──
@app.route("/evaluate")
def evaluate_list():
    active_tasks = [t for t in EVAL_TASKS if t["status"] in ("\u8bc4\u6d4b\u4e2d",)]
    rows = ""
    for t in active_tasks:
        bm = get_benchmark(t["benchmark_id"])
        bm_name = bm["name"] if bm else "--"
        pri = PRIORITY_MAP.get(t.get("priority", "\u4e2d"), {})
        total = max(t.get("total_sessions", 1), 1)
        e_done = t.get("eval_done", 0)
        pct = round(e_done / total * 100)
        pri_tag = f'<span class="ant-tag ant-tag-{pri.get("color","")}">{pri.get("label","")}</span>' if pri.get("color") else f'<span class="ant-tag">{pri.get("label","")}</span>'
        rows += (
            "<tr>"
            f'<td style="font-weight:500;">{t["task_no"]}</td>'
            f'<td>{bm_name}</td>'
            f'<td style="min-width:180px;">'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="flex:1;height:14px;background:#f0f0f0;border-radius:7px;overflow:hidden;position:relative;">'
            f'<div style="width:{pct}%;height:100%;background:#1F80A0;border-radius:7px;"></div>'
            f'<span class="pb-text" style="--pct:{pct}%;">{e_done}/{total}</span>'
            f'</div></div></td>'
            f"<td>{pri_tag}</td>"
            f'<td class="actions-cell"><a href="/evaluate/{t["id"]}/run" class="ant-btn ant-btn-sm ant-btn-primary">\u5f00\u59cb\u8bc4\u6d4b</a></td>'
            "</tr>"
        )
    empty = '<tr><td colspan="5" style="text-align:center;padding:40px;color:rgba(0,0,0,0.25);">\u6682\u65e0\u5f85\u8bc4\u6d4b\u4efb\u52a1</td></tr>' if not rows else ""

    content = f'''
    <div class="filter-bar">
      <input type="text" id="f-id" placeholder="\u4efb\u52a1 ID" style="min-width:120px;">
      <select id="f-bm" style="min-width:140px;"><option value="">Benchmark</option>{"".join(f'<option>{b["name"]}</option>' for b in BENCHMARKS)}</select>
      <select id="f-pri" style="min-width:110px;"><option value="">\u4f18\u5148\u7ea7</option><option>\u9ad8</option><option>\u4e2d</option><option>\u4f4e</option></select>
      <button class="ant-btn" onclick="evalClear()">\u6e05\u7a7a</button>
      <button class="ant-btn ant-btn-primary" onclick="evalFilter()">\u641c\u7d22</button>
    </div>
    <div class="ant-card ant-card-bordered">
      <table class="ant-table" id="eval-tbl">
        <thead><tr>
          <th>\u4efb\u52a1 ID</th><th>Benchmark</th><th>\u8fdb\u5ea6</th><th>\u4f18\u5148\u7ea7</th><th>\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}{empty}</tbody>
      </table>
    </div>
    <script>
    function evalFilter() {{
      var idv = (document.getElementById('f-id').value || '').trim();
      var bmv = document.getElementById('f-bm').value || '';
      var pv  = document.getElementById('f-pri').value || '';
      var rs = document.querySelectorAll('#eval-tbl tbody tr');
      rs.forEach(function(r) {{
        if (r.cells.length < 4) return;
        var tid = (r.cells[0].textContent || '').trim();
        var bm  = (r.cells[1].textContent || '').trim();
        var pri = (r.cells[3].textContent || '').trim();
        var ok = (!idv || tid.indexOf(idv) >= 0)
              && (!bmv || bm === bmv)
              && (!pv  || pri === pv);
        r.style.display = ok ? '' : 'none';
      }});
    }}
    function evalClear() {{
      document.getElementById('f-id').value = '';
      document.getElementById('f-bm').selectedIndex = 0;
      document.getElementById('f-pri').selectedIndex = 0;
      evalFilter();
    }}
    </script>
    '''
    return render_page("\u8bc4\u6d4b\u5de5\u4f5c\u53f0-HL", content, active="evaluate")


@app.route("/evaluate/<task_id>")
def evaluate_prep(task_id):
    """Preparation page: show task config, benchmark, scene setup before evaluation."""
    task = next((t for t in EVAL_TASKS if t["id"] == task_id), None)
    if not task:
        flash("\u4efb\u52a1\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("evaluate_list"))

    bm = get_benchmark(task["benchmark_id"])
    bm_name = bm["name"] if bm else "--"
    et = CRITERIA_TYPES.get(task.get("eval_type", ""), {})
    pct = round(task["completed_sessions"] / task["total_sessions"] * 100) if task["total_sessions"] > 0 else 0

    # Scene info
    sc = get_scene(bm.get("scene_id", "")) if bm else None
    scene_html = ""
    if sc:
        env = sc.get("environment", {})
        ws = env.get("workspace", {})
        cond = env.get("conditions", {})
        objs = sc.get("objects", [])
        refs = sc.get("references", {})
        img_count = len(refs.get("images", []))
        demo_count = len(refs.get("demo_videos", []))

        obj_tags = " ".join(f'<span class="ant-tag">{o["name"]} \u00d7{o.get("count",1)}</span>' for o in objs)

        # Build reference media section
        ref_items = ""
        for img in refs.get("images", []):
            fname = img.get("url", "").split("/")[-1] or "image.jpg"
            ref_items += (
                '<div style="background:#f5f5f5;border-radius:8px;overflow:hidden;width:160px;flex-shrink:0;">'
                '<div style="height:100px;background:#e8e8e8;display:flex;align-items:center;justify-content:center;color:rgba(0,0,0,0.25);font-size:12px;">IMG</div>'
                f'<div style="padding:6px 8px;font-size:12px;color:rgba(0,0,0,0.65);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{img.get("description", fname)}</div>'
                '</div>'
            )
        for v in refs.get("demo_videos", []):
            fname = v.get("url", "").split("/")[-1] or "video.mp4"
            dur = f' ({v.get("duration",0)}s)' if v.get("duration") else ""
            ref_items += (
                '<div style="background:#f5f5f5;border-radius:8px;overflow:hidden;width:160px;flex-shrink:0;">'
                '<div style="height:100px;background:#1a1a2e;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.3);font-size:20px;">&#9654;</div>'
                f'<div style="padding:6px 8px;font-size:12px;"><span class="ant-tag ant-tag-purple" style="font-size:11px;">\u6f14\u793a</span> {v.get("description", fname)}{dur}</div>'
                '</div>'
            )
        for v in refs.get("capture_videos", []):
            fname = v.get("url", "").split("/")[-1] or "video.mp4"
            dur = f' ({v.get("duration",0)}s)' if v.get("duration") else ""
            ref_items += (
                '<div style="background:#f5f5f5;border-radius:8px;overflow:hidden;width:160px;flex-shrink:0;">'
                '<div style="height:100px;background:#1a1a2e;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.3);font-size:20px;">&#9654;</div>'
                f'<div style="padding:6px 8px;font-size:12px;"><span class="ant-tag ant-tag-green" style="font-size:11px;">\u91c7\u96c6</span> {v.get("description", fname)}{dur}</div>'
                '</div>'
            )
        if ref_items:
            scene_refs_html = (
                '<div style="margin-top:16px;">'
                '<div style="font-size:13px;font-weight:500;margin-bottom:8px;">\u53c2\u8003\u8d44\u6599</div>'
                f'<div style="display:flex;gap:12px;overflow-x:auto;padding-bottom:4px;">{ref_items}</div>'
                '</div>'
            )
        else:
            scene_refs_html = ""

        scene_html = f'''
        <div class="ant-card ant-card-bordered" style="margin-bottom:16px;">
          <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;font-size:15px;font-weight:500;">\u573a\u666f\u4fe1\u606f \u2014 {sc["name"]}</div>
          <div class="ant-card-body">
            <div style="font-size:13px;color:rgba(0,0,0,0.45);margin-bottom:12px;">{sc["description"]}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
              <div style="background:#fafafa;border-radius:8px;padding:14px;">
                <div style="font-size:13px;font-weight:500;margin-bottom:8px;">\u73af\u5883\u53c2\u6570</div>
                <div style="display:grid;grid-template-columns:auto 1fr;gap:4px 16px;font-size:13px;">
                  <span style="color:rgba(0,0,0,0.45);">\u7c7b\u578b</span><span><span class="ant-tag ant-tag-cyan">{env.get("type","")}</span></span>
                  <span style="color:rgba(0,0,0,0.45);">\u5de5\u4f5c\u533a</span><span>{ws.get("length",0)} \u00d7 {ws.get("width",0)} \u00d7 {ws.get("height",0)} cm</span>
                  <span style="color:rgba(0,0,0,0.45);">\u5149\u7167</span><span>{cond.get("lighting","--")}</span>
                  <span style="color:rgba(0,0,0,0.45);">\u53f0\u9762</span><span>{cond.get("surface","--")}</span>
                </div>
              </div>
              <div style="background:#fafafa;border-radius:8px;padding:14px;">
                <div style="font-size:13px;font-weight:500;margin-bottom:8px;">\u7269\u4f53\u6e05\u5355 ({len(objs)} \u79cd)</div>
                <div style="display:flex;flex-wrap:wrap;gap:4px;">{obj_tags if obj_tags else "--"}</div>
              </div>
            </div>
            {scene_refs_html}
          </div>
        </div>'''
    else:
        scene_html = '<div class="ant-card ant-card-bordered" style="margin-bottom:16px;"><div class="ant-card-body" style="color:rgba(0,0,0,0.25);text-align:center;padding:24px;">\u672a\u5173\u8054\u573a\u666f</div></div>'

    # Criteria info
    cr = get_criterion(bm.get("criteria_id", "")) if bm else None
    cr_html = ""
    if cr:
        cr_type = CRITERIA_TYPES.get(cr["type"], {})
        cr_html = f'<span class="ant-tag ant-tag-{cr_type.get("color","")}">{cr_type.get("label","")}</span> {cr["name"]}'
    else:
        cr_html = "--"

    # Prompts as tree list (collapsed by default)
    prompt_list = ""
    if bm and bm.get("prompt_ids"):
        for pi, pid in enumerate(bm["prompt_ids"]):
            p = get_prompt(pid)
            if not p:
                continue
            lls = p.get("low_levels", [])
            step_count = len(lls)
            # Build sub-steps (hidden by default)
            sub_html = ""
            for si, ll in enumerate(lls):
                sub_html += (
                    f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0 5px 28px;font-size:13px;color:rgba(0,0,0,0.65);border-bottom:1px solid #fafafa;">'
                    f'<span style="color:rgba(0,0,0,0.25);min-width:16px;">{si+1}</span>'
                    f'<span>{ll["zh"]}</span>'
                    f'<span style="color:rgba(0,0,0,0.35);">{ll["en"]}</span>'
                    f'</div>'
                )
            uid = f"prep-prompt-{pi}"
            prompt_list += (
                f'<div style="border-bottom:1px solid #f0f0f0;">'
                f'<div style="display:flex;align-items:center;gap:8px;padding:8px 0;cursor:pointer;" onclick="var c=document.getElementById(\'{uid}\');var a=this.querySelector(\'.prep-arrow\');if(c.style.display===\'none\'){{c.style.display=\'\';a.style.transform=\'rotate(90deg)\';}}else{{c.style.display=\'none\';a.style.transform=\'\';}}">'
                f'<span class="prep-arrow" style="font-size:10px;color:rgba(0,0,0,0.3);transition:transform 0.2s;display:inline-block;">&#9654;</span>'
                f'<span style="font-weight:500;">{p["high_level"]}</span>'
                f'<span style="color:rgba(0,0,0,0.35);">{p["high_level_en"]}</span>'
                f'<span class="ant-tag">{step_count} \u6b65</span>'
                f'</div>'
                f'<div id="{uid}" style="display:none;">{sub_html}</div>'
                f'</div>'
            )

    prompt_count = len(bm.get("prompt_ids", [])) if bm else 0
    if not prompt_list:
        prompt_list = '<span style="color:rgba(0,0,0,0.25);">\u672a\u5173\u8054\u63d0\u793a\u8bcd</span>'

    content = f'''
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:18px;font-weight:500;">{task["name"]}</span>
        <span class="ant-tag ant-tag-{et.get("color","")}">{et.get("label","")}</span>
      </div>
      <a href="/evaluate" class="ant-btn">\u8fd4\u56de\u5217\u8868</a>
    </div>

    <!-- Task config summary -->
    <div class="ant-card ant-card-bordered" style="margin-bottom:16px;">
      <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;font-size:15px;font-weight:500;">\u8bc4\u6d4b\u914d\u7f6e</div>
      <div class="ant-card-body">
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;">
          <div>
            <div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">Benchmark</div>
            <div style="font-size:14px;font-weight:500;">{bm_name}</div>
          </div>
          <div>
            <div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u8bc4\u4ef7\u6807\u51c6</div>
            <div style="font-size:14px;">{cr_html}</div>
          </div>
          <div>
            <div style="font-size:12px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u8bc4\u6d4b\u8fdb\u5ea6</div>
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="font-size:14px;font-weight:500;">{task["completed_sessions"]} / {task["total_sessions"]}</span>
              <div class="progress-bar" style="width:80px;"><div class="progress-bar-fill blue" style="width:{pct}%;"></div></div>
              <span style="font-size:12px;color:rgba(0,0,0,0.35);">{pct}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Scene (key section) -->
    {scene_html}

    <!-- Prompt groups -->
    <div class="ant-card ant-card-bordered" style="margin-bottom:20px;">
      <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;font-size:15px;font-weight:500;">\u63d0\u793a\u8bcd\u7ec4 ({prompt_count} \u7ec4)</div>
      <div class="ant-card-body" style="padding:12px 20px;">
        {prompt_list}
      </div>
    </div>

    <!-- Start button -->
    <div style="text-align:center;padding:8px 0;">
      <a href="/evaluate/{task_id}/run" class="ant-btn ant-btn-primary ant-btn-lg" style="padding:10px 48px;font-size:15px;">\u573a\u666f\u5df2\u5c31\u7eea\uff0c\u5f00\u59cb\u8bc4\u6d4b</a>
      <div style="margin-top:8px;font-size:12px;color:rgba(0,0,0,0.35);">\u8bf7\u786e\u8ba4\u5df2\u6309\u4e0a\u8ff0\u573a\u666f\u8981\u6c42\u5e03\u7f6e\u597d\u73af\u5883\u548c\u7269\u4f53</div>
    </div>
    '''
    return render_page("\u8bc4\u6d4b\u51c6\u5907", content, active="evaluate")


@app.route("/evaluate/<task_id>/run")
def evaluate_run(task_id):
    """Scoring-only workbench — no execution phase."""
    task = next((t for t in EVAL_TASKS if t["id"] == task_id), None)
    if not task:
        flash("\u4efb\u52a1\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("evaluate_list"))

    bm = get_benchmark(task["benchmark_id"])
    bm_name = bm["name"] if bm else "--"
    et = CRITERIA_TYPES.get(task.get("eval_type", ""), {})
    if len(task["model_ids"]) >= 2:
        pair = random.sample(task["model_ids"], 2)
    else:
        pair = task["model_ids"] * 2

    bm_name = bm["name"] if bm else "--"
    # Support ?pid= for prompt group switching
    requested_pid = request.args.get("pid", "")
    prompt = None
    if requested_pid:
        prompt = get_prompt(requested_pid)
    if not prompt and bm and bm.get("prompt_ids"):
        prompt = get_prompt(bm["prompt_ids"][0])
    if not prompt:
        prompt = PROMPTS[0]

    steps = prompt.get("low_levels", [])
    n_steps = len(steps)
    pct = round(task["completed_sessions"] / task["total_sessions"] * 100) if task["total_sessions"] > 0 else 0
    prompt_count = len(bm.get("prompt_ids", [])) if bm else 0
    current_group = min(task["completed_sessions"] + 1, prompt_count) if prompt_count > 0 else 1

    # Build scoring rows only
    scoring_rows = ""
    for i, ll in enumerate(steps):
        step_num = i + 1
        scoring_rows += (
            f'<tr>'
            f'<td style="font-weight:500;white-space:nowrap;">Step {step_num}: {ll["zh"]}</td>'
            f'<td style="white-space:nowrap;">'
            f'<button type="button" class="ant-btn ant-btn-sm" onclick="alert(\'[\u56de\u653e] Policy A Step {step_num}\')" style="font-size:12px;">\u56de\u653e A</button> '
            f'<button type="button" class="ant-btn ant-btn-sm" onclick="alert(\'[\u56de\u653e] Policy B Step {step_num}\')" style="font-size:12px;">\u56de\u653e B</button>'
            f'</td>'
            f'<td>'
            f'<div style="display:flex;align-items:center;gap:4px;font-size:13px;">'
            f'<span style="color:rgba(0,0,0,0.85);white-space:nowrap;">A:</span>'
            f'<input type="range" name="prog_a_{i}" min="0" max="100" step="1" value="0" style="width:70px;accent-color:#1F80A0;">'
            f'<span id="pa-{i}-v" style="min-width:24px;text-align:center;">0</span>'
            f'<span style="color:rgba(0,0,0,0.85);white-space:nowrap;margin-left:4px;">B:</span>'
            f'<input type="range" name="prog_b_{i}" min="0" max="100" step="1" value="0" style="width:70px;accent-color:#1F80A0;">'
            f'<span id="pb-{i}-v" style="min-width:24px;text-align:center;">0</span>'
            f'</div></td>'
            f'<td>'
            f'<input type="hidden" name="pref_{i}" id="pref-input-{i}" value="">'
            f'<div style="display:flex;gap:4px;white-space:nowrap;">'
            f'<button type="button" class="pref-opt pref-a" onclick="setPref({i},2,this)">A\u80dc</button>'
            f'<button type="button" class="pref-opt pref-tie" onclick="setPref({i},1,this)">\u5e73\u5c40</button>'
            f'<button type="button" class="pref-opt pref-b" onclick="setPref({i},0,this)">B\u80dc</button>'
            f'</div></td>'
            f'<td>'
            f'<textarea name="note_{i}" rows="1" placeholder="\u8bf4\u660e..." style="width:100%;padding:4px 8px;border:1px solid #d9d9d9;border-radius:6px;font-size:13px;resize:vertical;"></textarea>'
            f'</td>'
            f'</tr>'
        )

    # Prompt group as select options
    prompt_tabs = ""
    if bm and bm.get("prompt_ids"):
        for pi, ppid in enumerate(bm["prompt_ids"]):
            pp = get_prompt(ppid)
            if pp:
                sel = "selected" if ppid == prompt["id"] else ""
                prompt_tabs += f'<option value="/evaluate/{task_id}/run?pid={ppid}" {sel}>{pp["high_level"]}</option>'

    content = f'''
    <form method="POST" action="/evaluate/{task_id}/submit">
    <input type="hidden" name="policy_a" value="{pair[0]}">
    <input type="hidden" name="policy_b" value="{pair[1]}">
    <input type="hidden" name="prompt_id" value="{prompt['id']}">
    <input type="hidden" name="n_steps" value="{n_steps}">

    <!-- Top: themed prompt bar -->
    <div style="background:#e6f4f8;border:1px solid #b8dce8;border-radius:8px;padding:12px 20px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;">
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:13px;color:rgba(0,0,0,0.45);">\u63d0\u793a\u8bcd\u7ec4:</span>
        <select style="height:28px;padding:2px 24px 2px 8px;border:1px solid #b8dce8;border-radius:6px;font-size:13px;background:#fff;-webkit-appearance:none;appearance:none;" onchange="if(this.value) window.location=this.value;">{prompt_tabs}</select>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:13px;color:rgba(0,0,0,0.45);">\u5f53\u524d\u8bc4\u5206\u8fdb\u5ea6:</span>
        <div style="width:140px;height:8px;background:rgba(0,0,0,0.08);border-radius:4px;overflow:hidden;"><div style="width:{pct}%;height:100%;background:#1F80A0;border-radius:4px;"></div></div>
        <span style="font-weight:600;color:#1F80A0;">{task["completed_sessions"]}</span><span style="color:rgba(0,0,0,0.35);">/{task["total_sessions"]}</span>
      </div>
    </div>

    <!-- Video area: grey bg, white cards, fixed height -->
    <div style="background:#f0f0f0;border-radius:8px;padding:12px;margin-bottom:16px;">
      <div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:start;">
        <!-- Model A -->
        <div style="background:#fff;border-radius:8px;overflow:hidden;">
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;">
            <span style="font-size:15px;font-weight:600;">\u6a21\u578b A</span>
            <label style="display:flex;align-items:center;gap:6px;font-size:13px;color:rgba(0,0,0,0.45);cursor:pointer;">\u5c55\u5f00\u8155\u90e8\u89c6\u89d2
              <label class="capsule" id="sw1-a" onclick="this.classList.toggle('on');toggleWrist1('a');"><span class="capsule-dot"></span></label>
            </label>
          </div>
          <div style="height:360px;display:flex;gap:4px;padding:0 4px 4px;background:#000;">
            <div id="w1-main-a" style="flex:1;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.25);font-size:13px;">\u4e3b\u6444\u89c6\u89d2 &middot; 640x480</div>
            <div id="w1-wrist-a" style="display:none;flex-direction:column;gap:4px;width:180px;">
              <div style="flex:1;background:#1a1a2e;border-radius:4px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:10px;">\u5de6\u8155\u89c6\u89d2</div>
              <div style="flex:1;background:#1a1a2e;border-radius:4px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:10px;">\u53f3\u8155\u89c6\u89d2</div>
            </div>
          </div>
        </div>
        <div style="padding:0 10px;font-size:14px;color:rgba(0,0,0,0.15);font-weight:600;align-self:center;">VS</div>
        <!-- Model B -->
        <div style="background:#fff;border-radius:8px;overflow:hidden;">
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;">
            <span style="font-size:15px;font-weight:600;">\u6a21\u578b B</span>
            <label style="display:flex;align-items:center;gap:6px;font-size:13px;color:rgba(0,0,0,0.45);cursor:pointer;">\u5c55\u5f00\u8155\u90e8\u89c6\u89d2
              <label class="capsule" id="sw1-b" onclick="this.classList.toggle('on');toggleWrist1('b');"><span class="capsule-dot"></span></label>
            </label>
          </div>
          <div style="height:360px;display:flex;gap:4px;padding:0 4px 4px;background:#000;">
            <div id="w1-main-b" style="flex:1;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.25);font-size:13px;">\u4e3b\u6444\u89c6\u89d2 &middot; 640x480</div>
            <div id="w1-wrist-b" style="display:none;flex-direction:column;gap:4px;width:180px;">
              <div style="flex:1;background:#1a1a2e;border-radius:4px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:10px;">\u5de6\u8155\u89c6\u89d2</div>
              <div style="flex:1;background:#1a1a2e;border-radius:4px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:10px;">\u53f3\u8155\u89c6\u89d2</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Scoring card (white bg) -->
    <div style="background:#fff;border-radius:8px;padding:0;border:1px solid #f0f0f0;">
      <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;font-size:15px;font-weight:500;">\u8bc4\u5206</div>
      <table class="ant-table">
        <thead><tr><th>\u6b65\u9aa4</th><th style="width:110px;">\u56de\u653e</th><th style="width:220px;">\u8fdb\u5ea6\u5206 (0-100)</th><th style="width:160px;">\u504f\u597d\u9009\u62e9</th><th>\u6587\u5b57\u8bf4\u660e</th></tr></thead>
        <tbody>{scoring_rows}</tbody>
      </table>
      <div style="padding:16px 20px;border-top:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center;">
        <a href="/evaluate" style="color:#1F80A0;text-decoration:none;font-size:14px;">&larr; \u8fd4\u56de\u4e0a\u4e00\u6761</a>
        <a href="javascript:void(0)" onclick="v1ValidateSubmit(this)" style="color:#1F80A0;text-decoration:none;font-size:14px;">\u63d0\u4ea4\u5e76\u4e0b\u4e00\u6761 &rarr;</a>
      </div>
    </div>
    </form>

    <style>
      .pref-opt {{ display:inline-block; padding:4px 16px; border:1px solid #d9d9d9; border-radius:8px; font-size:13px; cursor:pointer; background:#fff; color:rgba(0,0,0,0.65); transition:all 0.2s; white-space:nowrap; }}
      .pref-opt:hover {{ border-color:#1F80A0; }}
      .pref-a.pref-active {{ background:#e6f4f8; color:#1F80A0; border-color:#1F80A0; font-weight:500; }}
      .pref-tie.pref-active {{ background:#f5f5f5; color:rgba(0,0,0,0.65); border-color:#8c8c8c; font-weight:500; }}
      .pref-b.pref-active {{ background:#e6f4f8; color:#1F80A0; border-color:#1F80A0; font-weight:500; }}
    </style>

    <script>
    function toggleWrist1(side) {{
      var wrist = document.getElementById('w1-wrist-'+side);
      var isOn = document.getElementById('sw1-'+side).classList.contains('on');
      wrist.style.display = isOn ? 'flex' : 'none';
    }}
    document.querySelectorAll('input[type="range"]').forEach(function(s) {{
      var vId = s.name.replace('prog_a_','pa-').replace('prog_b_','pb-') + '-v';
      var d = document.getElementById(vId);
      if (d) s.addEventListener('input', function() {{ d.textContent = Math.round(s.value); }});
    }});
    function v1ValidateSubmit(el) {{
      var form = el.closest('form');
      var nSteps = parseInt(form.querySelector('input[name="n_steps"]').value || '0', 10);
      for (var i = 0; i < nSteps; i++) {{
        var prefEl = document.getElementById('pref-input-'+i);
        if (!prefEl || !prefEl.value) {{
          window.showToast('\u7b2c ' + (i+1) + ' \u6b65\u672a\u9009\u62e9\u504f\u597d', 'warning');
          return;
        }}
        var noteEl = form.querySelector('textarea[name="note_'+i+'"]');
        if (!noteEl || !noteEl.value.trim()) {{
          window.showToast('\u7b2c ' + (i+1) + ' \u6b65\u6587\u5b57\u8bf4\u660e\u672a\u586b\u5199', 'warning');
          if (noteEl) {{ noteEl.focus(); }}
          return;
        }}
      }}
      form.submit();
    }}
    function setPref(step, val, btn) {{
      document.getElementById('pref-input-'+step).value = val;
      btn.closest('td').querySelectorAll('.pref-opt').forEach(function(b) {{ b.classList.remove('pref-active'); }});
      btn.classList.add('pref-active');
    }}
    </script>
    '''
    return render_page("\u8bc4\u6d4b\u5de5\u4f5c\u53f0", content, active="evaluate")


@app.route("/evaluate/<task_id>/submit", methods=["POST"])
def evaluate_submit(task_id):
    task = next((t for t in EVAL_TASKS if t["id"] == task_id), None)
    if not task:
        flash("任务不存在", "error")
        return redirect(url_for("evaluate_list"))

    pa = request.form.get("policy_a", "")
    pb = request.form.get("policy_b", "")
    pref = request.form.get("preference", "")
    explanation = request.form.get("explanation", "")
    prompt_id = request.form.get("prompt_id", "")

    if pref not in ("0", "1", "2"):
        flash("请选择偏好判断", "error")
        return redirect(f"/evaluate/{task_id}/run")

    # Collect progress scores
    prompt = get_prompt(prompt_id)
    n_steps = len(prompt["low_levels"]) if prompt else 0
    prog_a = [float(request.form.get(f"prog_a_{i}", 0.5)) for i in range(n_steps)]
    prog_b = [float(request.form.get(f"prog_b_{i}", 0.5)) for i in range(n_steps)]

    EVAL_SESSIONS.append({
        "id": f"s{len(EVAL_SESSIONS)+1}",
        "policy_a": pa,
        "policy_b": pb,
        "preference": int(pref),
        "progress_a": prog_a,
        "progress_b": prog_b,
        "overall_progress_a": round(sum(prog_a) / max(len(prog_a), 1), 2),
        "overall_progress_b": round(sum(prog_b) / max(len(prog_b), 1), 2),
        "explanation": explanation,
        "prompt_id": prompt_id,
        "evaluator": "Joanna Qiao",
        "timestamp": datetime.now().isoformat(),
    })

    task["completed_sessions"] = min(task["completed_sessions"] + 1, task["total_sessions"])
    if task["completed_sessions"] >= task["total_sessions"]:
        task["status"] = "已完成"
    elif task["status"] == "未开始":
        task["status"] = "进行中"

    flash("评测结果提交成功", "success")
    return redirect(f"/evaluate/{task_id}/run")


# ── Evaluation Workbench v2 (flat steps) ──
@app.route("/evaluate2")
def evaluate2_list():
    active_tasks = [t for t in EVAL_TASKS if t["status"] in ("\u8bc4\u6d4b\u4e2d",)]
    rows = ""
    for t in active_tasks:
        bm = get_benchmark(t["benchmark_id"])
        bm_name = bm["name"] if bm else "--"
        pri = PRIORITY_MAP.get(t.get("priority", "\u4e2d"), {})
        total = max(t.get("total_sessions", 1), 1)
        e_done = t.get("eval_done", 0)
        pct = round(e_done / total * 100)
        pri_tag = f'<span class="ant-tag ant-tag-{pri.get("color","")}">{pri.get("label","")}</span>' if pri.get("color") else f'<span class="ant-tag">{pri.get("label","")}</span>'
        rows += (
            "<tr>"
            f'<td style="font-weight:500;">{t["task_no"]}</td>'
            f'<td>{bm_name}</td>'
            f'<td style="min-width:180px;">'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="flex:1;height:14px;background:#f0f0f0;border-radius:7px;overflow:hidden;position:relative;">'
            f'<div style="width:{pct}%;height:100%;background:#1F80A0;border-radius:7px;"></div>'
            f'<span class="pb-text" style="--pct:{pct}%;">{e_done}/{total}</span>'
            f'</div></div></td>'
            f"<td>{pri_tag}</td>"
            f'<td class="actions-cell"><a href="/evaluate2/{t["id"]}/run?step=0" class="ant-btn ant-btn-sm ant-btn-primary">\u5f00\u59cb\u8bc4\u6d4b</a></td>'
            "</tr>"
        )
    empty = '<tr><td colspan="5" style="text-align:center;padding:40px;color:rgba(0,0,0,0.25);">\u6682\u65e0\u5f85\u8bc4\u6d4b\u4efb\u52a1</td></tr>' if not rows else ""

    content = f'''
    <div class="filter-bar">
      <input type="text" id="f2-id" placeholder="\u4efb\u52a1 ID" style="min-width:120px;">
      <select id="f2-bm" style="min-width:140px;"><option value="">Benchmark</option>{"".join(f'<option>{b["name"]}</option>' for b in BENCHMARKS)}</select>
      <select id="f2-pri" style="min-width:110px;"><option value="">\u4f18\u5148\u7ea7</option><option>\u9ad8</option><option>\u4e2d</option><option>\u4f4e</option></select>
      <button class="ant-btn" onclick="eval2Clear()">\u6e05\u7a7a</button>
      <button class="ant-btn ant-btn-primary" onclick="eval2Filter()">\u641c\u7d22</button>
    </div>
    <div class="ant-card ant-card-bordered">
      <table class="ant-table" id="eval2-tbl">
        <thead><tr>
          <th>\u4efb\u52a1 ID</th><th>Benchmark</th><th>\u8fdb\u5ea6</th><th>\u4f18\u5148\u7ea7</th><th>\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}{empty}</tbody>
      </table>
    </div>
    <script>
    function eval2Filter() {{
      var idv = (document.getElementById('f2-id').value || '').trim();
      var bmv = document.getElementById('f2-bm').value || '';
      var pv  = document.getElementById('f2-pri').value || '';
      var rs = document.querySelectorAll('#eval2-tbl tbody tr');
      rs.forEach(function(r) {{
        if (r.cells.length < 4) return;
        var tid = (r.cells[0].textContent || '').trim();
        var bm  = (r.cells[1].textContent || '').trim();
        var pri = (r.cells[3].textContent || '').trim();
        var ok = (!idv || tid.indexOf(idv) >= 0)
              && (!bmv || bm === bmv)
              && (!pv  || pri === pv);
        r.style.display = ok ? '' : 'none';
      }});
    }}
    function eval2Clear() {{
      document.getElementById('f2-id').value = '';
      document.getElementById('f2-bm').selectedIndex = 0;
      document.getElementById('f2-pri').selectedIndex = 0;
      eval2Filter();
    }}
    </script>
    '''
    return render_page("\u8bc4\u6d4b\u5de5\u4f5c\u53f0-LL", content, active="evaluate2")


@app.route("/evaluate2/<task_id>/run")
def evaluate2_run(task_id):
    task = next((t for t in EVAL_TASKS if t["id"] == task_id), None)
    if not task:
        flash("\u4efb\u52a1\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("evaluate2_list"))
    bm = get_benchmark(task["benchmark_id"])
    bm_name = bm["name"] if bm else "--"
    et = CRITERIA_TYPES.get(task.get("eval_type", ""), {})
    if len(task["model_ids"]) >= 2:
        pair = random.sample(task["model_ids"], 2)
    else:
        pair = task["model_ids"] * 2

    # Flatten all steps across all prompt groups
    flat_steps = []
    if bm and bm.get("prompt_ids"):
        for pid in bm["prompt_ids"]:
            p = get_prompt(pid)
            if not p:
                continue
            for ll in p.get("low_levels", []):
                flat_steps.append({"hl": p["high_level"], "zh": ll["zh"], "en": ll["en"], "pid": pid})

    total_steps = len(flat_steps)
    current_step = int(request.args.get("step", 0))
    if current_step >= total_steps:
        current_step = total_steps - 1
    if current_step < 0:
        current_step = 0

    step = flat_steps[current_step] if flat_steps else None
    pct = round((current_step) / max(total_steps, 1) * 100)

    if not step:
        content = '<div style="text-align:center;padding:60px;color:rgba(0,0,0,0.25);">\u6682\u65e0\u8bc4\u6d4b\u6b65\u9aa4</div>'
        return render_page("\u8bc4\u6d4b\u5de5\u4f5c\u53f0 2", content, active="evaluate2")

    is_last = current_step >= total_steps - 1
    next_url = f"/evaluate2/{task_id}/run?step={current_step + 1}" if not is_last else "/evaluate2"
    prev_url = f"/evaluate2/{task_id}/run?step={current_step - 1}" if current_step > 0 else ""
    submit_text = "\u63d0\u4ea4\u5e76\u4e0b\u4e00\u6761" if not is_last else "\u63d0\u4ea4\u5e76\u5b8c\u6210"

    prev_link = f'<a href="{prev_url}" style="color:#1F80A0;text-decoration:none;font-size:14px;">&larr; \u8fd4\u56de\u4e0a\u4e00\u6761</a>' if prev_url else '<span style="color:rgba(0,0,0,0.15);font-size:14px;">&larr; \u8fd4\u56de\u4e0a\u4e00\u6761</span>'

    content = f'''
    <!-- Top: themed prompt bar -->
    <div style="background:#e6f4f8;border:1px solid #b8dce8;border-radius:8px;padding:12px 20px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;">
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:12px;color:rgba(0,0,0,0.45);">High Level:</span>
        <span style="font-weight:600;color:#1F80A0;">{step["hl"]}</span>
        <span style="width:1px;height:16px;background:#b8dce8;"></span>
        <span style="font-size:12px;color:rgba(0,0,0,0.45);">Low Level:</span>
        <span style="font-weight:600;">{step["zh"]}</span>
        <span style="color:rgba(0,0,0,0.35);font-size:13px;">{step["en"]}</span>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:13px;color:rgba(0,0,0,0.45);">\u5f53\u524d\u8bc4\u5206\u8fdb\u5ea6:</span>
        <div style="width:140px;height:8px;background:rgba(0,0,0,0.08);border-radius:4px;overflow:hidden;"><div style="width:{pct}%;height:100%;background:#1F80A0;border-radius:4px;"></div></div>
        <span style="font-weight:600;color:#1F80A0;">{current_step + 1}</span><span style="color:rgba(0,0,0,0.35);">/{total_steps} \u7ec4</span>
      </div>
    </div>

    <!-- Video area: grey bg, white video cards, fixed height container -->
    <!-- Demo toggle: unpaired state -->
    <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
      <button type="button" class="ant-btn ant-btn-sm" onclick="togglePaired()" id="unpaired-btn">\u672a\u914d\u5bf9\u60c5\u51b5</button>
    </div>
    <div style="background:#f0f0f0;border-radius:8px;padding:12px;margin-bottom:16px;">
      <div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:start;">
        <!-- Model A -->
        <div id="v2-card-a" style="background:#fff;border-radius:8px;overflow:hidden;">
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;">
            <span style="font-size:15px;font-weight:600;">\u6a21\u578b A</span>
            <label style="display:flex;align-items:center;gap:6px;font-size:13px;color:rgba(0,0,0,0.45);cursor:pointer;">\u5c55\u5f00\u8155\u90e8\u89c6\u89d2
              <label class="capsule" id="sw-a" onclick="this.classList.toggle('on');toggleWrist('a');"><span class="capsule-dot"></span></label>
            </label>
          </div>
          <!-- Fixed height video zone -->
          <div id="v2-video-a" style="height:360px;display:flex;gap:4px;padding:0 4px 4px;background:#000;">
            <div id="v2-main-a" style="flex:1;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.25);font-size:13px;">\u4e3b\u6444\u89c6\u89d2 &middot; 640x480</div>
            <div id="v2-wrist-a" style="display:none;flex-direction:column;gap:4px;width:180px;">
              <div style="flex:1;background:#1a1a2e;border-radius:4px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:10px;">\u5de6\u8155\u89c6\u89d2</div>
              <div style="flex:1;background:#1a1a2e;border-radius:4px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:10px;">\u53f3\u8155\u89c6\u89d2</div>
            </div>
          </div>
        </div>

        <div style="padding:0 10px;font-size:14px;color:rgba(0,0,0,0.15);font-weight:600;align-self:center;">VS</div>

        <!-- Model B -->
        <div id="v2-card-b" style="background:#fff;border-radius:8px;overflow:hidden;">
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;">
            <span style="font-size:15px;font-weight:600;">\u6a21\u578b B</span>
            <label style="display:flex;align-items:center;gap:6px;font-size:13px;color:rgba(0,0,0,0.45);cursor:pointer;">\u5c55\u5f00\u8155\u90e8\u89c6\u89d2
              <label class="capsule" id="sw-b" onclick="this.classList.toggle('on');toggleWrist('b');"><span class="capsule-dot"></span></label>
            </label>
          </div>
          <div id="v2-video-b" style="height:360px;display:flex;gap:4px;padding:0 4px 4px;background:#000;">
            <div id="v2-main-b" style="flex:1;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.25);font-size:13px;">\u4e3b\u6444\u89c6\u89d2 &middot; 640x480</div>
            <div id="v2-wrist-b" style="display:none;flex-direction:column;gap:4px;width:180px;">
              <div style="flex:1;background:#1a1a2e;border-radius:4px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:10px;">\u5de6\u8155\u89c6\u89d2</div>
              <div style="flex:1;background:#1a1a2e;border-radius:4px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.2);font-size:10px;">\u53f3\u8155\u89c6\u89d2</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom white card: progress + note + buttons -->
    <div style="background:#fff;border-radius:8px;padding:20px;border:1px solid #f0f0f0;">
      <!-- Progress scores (1-5) -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:16px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="color:rgba(0,0,0,0.85);font-weight:500;">A:</span>
          <input type="range" id="v2-prog-a" min="1" max="5" step="1" value="1" style="flex:1;accent-color:#1F80A0;">
          <span id="v2-prog-a-v" style="font-weight:600;color:#1F80A0;min-width:14px;text-align:right;">1</span>
          <span style="font-size:13px;color:rgba(0,0,0,0.35);">/ 5 \u5206</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="color:rgba(0,0,0,0.85);font-weight:500;">B:</span>
          <input type="range" id="v2-prog-b" min="1" max="5" step="1" value="1" style="flex:1;accent-color:#1F80A0;">
          <span id="v2-prog-b-v" style="font-weight:600;color:#1F80A0;min-width:14px;text-align:right;">1</span>
          <span style="font-size:13px;color:rgba(0,0,0,0.35);">/ 5 \u5206</span>
        </div>
      </div>
      <!-- Note -->
      <div style="margin-bottom:20px;">
        <textarea id="v2-note" rows="2" placeholder="\u8bf7\u8f93\u5165\u9009\u62e9\u539f\u56e0\uff0c\u5fc5\u586b\u3002\u53ef\u4ee5\u4ece\u62d3\u53d6\u7cbe\u5ea6\u3001\u8def\u5f84\u89c4\u5212\u3001\u52a8\u4f5c\u6d41\u7545\u5ea6\u3001\u5f02\u5e38\u6062\u590d\u80fd\u529b\u3001\u4efb\u52a1\u5b8c\u6210\u5ea6\u7b49\u65b9\u9762\u8bc4\u4ef7" style="width:100%;padding:10px 14px;border:1px solid #d9d9d9;border-radius:8px;font-size:14px;resize:vertical;box-sizing:border-box;"></textarea>
      </div>
      <!-- Bottom actions: 5 preference options -->
      <div style="display:flex;align-items:center;">
        <div style="flex-shrink:0;">{prev_link}</div>
        <div style="display:flex;gap:6px;flex:1;justify-content:center;">
          <button type="button" class="pref-opt pref-a" onclick="v2SetPref(4,this)" style="flex:1;max-width:140px;padding:10px 0;font-size:14px;text-align:center;">A \u80dc</button>
          <button type="button" class="pref-opt pref-tie" onclick="v2SetPref(3,this)" style="flex:1;max-width:140px;padding:10px 0;font-size:14px;text-align:center;">\u90fd\u597d</button>
          <button type="button" class="pref-opt pref-tie" onclick="v2SetPref(2,this)" style="flex:1;max-width:140px;padding:10px 0;font-size:14px;text-align:center;">\u90fd\u4e00\u822c</button>
          <button type="button" class="pref-opt pref-tie" onclick="v2SetPref(1,this)" style="flex:1;max-width:140px;padding:10px 0;font-size:14px;text-align:center;">\u90fd\u5dee</button>
          <button type="button" class="pref-opt pref-b" onclick="v2SetPref(0,this)" style="flex:1;max-width:140px;padding:10px 0;font-size:14px;text-align:center;">B \u80dc</button>
        </div>
        <a href="javascript:;" onclick="v2Submit()" style="color:#1F80A0;text-decoration:none;font-size:14px;flex-shrink:0;">{submit_text} &rarr;</a>
      </div>
    </div>

    <style>
      .pref-opt {{ display:inline-block; padding:4px 16px; border:1px solid #d9d9d9; border-radius:8px; font-size:13px; cursor:pointer; background:#fff; color:rgba(0,0,0,0.65); transition:all 0.2s; white-space:nowrap; }}
      .pref-opt:hover {{ border-color:#1F80A0; }}
      .pref-a.pref-active {{ background:#e6f4f8; color:#1F80A0; border-color:#1F80A0; font-weight:500; }}
      .pref-tie.pref-active {{ background:#f5f5f5; color:rgba(0,0,0,0.65); border-color:#8c8c8c; font-weight:500; }}
      .pref-b.pref-active {{ background:#e6f4f8; color:#1F80A0; border-color:#1F80A0; font-weight:500; }}
    </style>

    <script>
    function toggleWrist(side) {{
      var wrist = document.getElementById('v2-wrist-'+side);
      var isOn = document.getElementById('sw-'+side).classList.contains('on');
      wrist.style.display = isOn ? 'flex' : 'none';
    }}
    // Demo: cycle unpaired state — normal -> A unpaired -> B unpaired -> normal
    var _pairedState = 0; // 0=normal, 1=A unpaired, 2=B unpaired
    var _videoOrigA = null, _videoOrigB = null;
    function _setVideoEmpty(side) {{
      var el = document.getElementById('v2-video-'+side);
      el.style.background = '#fafafa';
      el.style.border = '1px dashed #d9d9d9';
      el.innerHTML = '<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:rgba(0,0,0,0.35);gap:8px;"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#bfbfbf" stroke-width="1.2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg><div style="font-size:14px;">\u65e0\u6267\u884c\u7ed3\u679c</div><div style="font-size:12px;color:rgba(0,0,0,0.25);">\u6a21\u578b ' + side.toUpperCase() + ' \u672a\u8fd0\u884c\u6b64\u6761\u8bb0\u5f55</div></div>';
    }}
    function _restoreVideo(side, html) {{
      var el = document.getElementById('v2-video-'+side);
      el.style.background = '#000';
      el.style.border = '';
      el.innerHTML = html;
    }}
    function _setProgDisabled(side, disabled) {{
      var s = document.getElementById('v2-prog-'+side);
      s.disabled = disabled;
      s.style.opacity = disabled ? '0.4' : '';
      s.style.cursor = disabled ? 'not-allowed' : '';
    }}
    function _setPrefDisabled(disabled) {{
      document.querySelectorAll('.pref-opt').forEach(function(b) {{
        if (disabled) {{
          b.setAttribute('disabled', 'true');
          b.style.opacity = '0.4';
          b.style.cursor = 'not-allowed';
          b.style.pointerEvents = 'none';
        }} else {{
          b.removeAttribute('disabled');
          b.style.opacity = '';
          b.style.cursor = '';
          b.style.pointerEvents = '';
        }}
      }});
    }}
    function togglePaired() {{
      if (_videoOrigA === null) _videoOrigA = document.getElementById('v2-video-a').innerHTML;
      if (_videoOrigB === null) _videoOrigB = document.getElementById('v2-video-b').innerHTML;
      _pairedState = (_pairedState + 1) % 3;
      var btn = document.getElementById('unpaired-btn');
      if (_pairedState === 0) {{
        // Normal paired
        _restoreVideo('a', _videoOrigA);
        _restoreVideo('b', _videoOrigB);
        _setProgDisabled('a', false);
        _setProgDisabled('b', false);
        _setPrefDisabled(false);
        btn.textContent = '\u672a\u914d\u5bf9\u60c5\u51b5';
        btn.classList.remove('ant-btn-primary');
      }} else if (_pairedState === 1) {{
        // A unpaired
        _setVideoEmpty('a');
        _restoreVideo('b', _videoOrigB);
        _setProgDisabled('a', true);
        _setProgDisabled('b', false);
        _setPrefDisabled(true);
        btn.textContent = 'A \u672a\u914d\u5bf9 (\u70b9\u51fb\u5207\u6362)';
        btn.classList.add('ant-btn-primary');
      }} else {{
        // B unpaired
        _restoreVideo('a', _videoOrigA);
        _setVideoEmpty('b');
        _setProgDisabled('a', false);
        _setProgDisabled('b', true);
        _setPrefDisabled(true);
        btn.textContent = 'B \u672a\u914d\u5bf9 (\u70b9\u51fb\u5207\u6362)';
        btn.classList.add('ant-btn-primary');
      }}
    }}
    document.getElementById('v2-prog-a').addEventListener('input', function() {{
      document.getElementById('v2-prog-a-v').textContent = Math.round(this.value);
    }});
    document.getElementById('v2-prog-b').addEventListener('input', function() {{
      document.getElementById('v2-prog-b-v').textContent = Math.round(this.value);
    }});
    function v2Submit() {{
      if (v2Pref === null || v2Pref === undefined) {{
        window.showToast('\u8bf7\u9009\u62e9\u504f\u597d', 'warning');
        return;
      }}
      var noteEl = document.getElementById('v2-note');
      var note = noteEl.value.trim();
      if (!note) {{
        window.showToast('\u6587\u5b57\u8bf4\u660e\u4e0d\u80fd\u4e3a\u7a7a', 'warning');
        noteEl.style.borderColor = '#ff4d4f';
        noteEl.focus();
        setTimeout(function(){{ noteEl.style.borderColor = ''; }}, 2500);
        return;
      }}
      window.location.href = '{next_url}';
    }}
    var v2Pref = null;
    function v2SetPref(val, btn) {{
      v2Pref = val;
      document.querySelectorAll('.pref-opt').forEach(function(b) {{ b.classList.remove('pref-active'); }});
      btn.classList.add('pref-active');
    }}
    </script>
    '''
    return render_page("\u8bc4\u6d4b\u5de5\u4f5c\u53f0 2", content, active="evaluate2")


# ── Evaluation Records (task-view + checkpoint-view) ──
@app.route("/eval-records")
def eval_records_page():
    view = request.args.get("view", "task")  # task | ckpt
    if view not in ("task", "ckpt"):
        view = "task"

    import random as _rnd_er

    # ── View 1: Task-perspective rows (from task_detail mock) ──
    task_rows = []
    for t in EVAL_TASKS:
        bm = get_benchmark(t["benchmark_id"])
        if not bm:
            continue
        _rnd_er.seed(hash(t["id"]))
        mid_a = t["model_ids"][0] if len(t["model_ids"]) > 0 else ""
        mid_b = t["model_ids"][1] if len(t["model_ids"]) > 1 else ""
        name_a = get_model_name(mid_a) if mid_a else "--"
        name_b = get_model_name(mid_b) if mid_b else "--"
        for pid in bm.get("prompt_ids", []):
            p = get_prompt(pid)
            if not p:
                continue
            for ll in p.get("low_levels", []):
                result_val = _rnd_er.choice([4, 3, 2, 1, 0])
                exec_id = f"E{_rnd_er.randint(1000,9999)}"
                prog_a = _rnd_er.randint(1, 5)
                prog_b = _rnd_er.randint(1, 5)
                task_rows.append({
                    "task_id": t["id"],
                    "task_no": t.get("task_no", ""),
                    "task_name": t["name"],
                    "exec_id": exec_id,
                    "high_level": p["high_level"],
                    "low_level": ll["zh"],
                    "model_a": name_a,
                    "model_b": name_b,
                    "result": result_val,
                    "prog_a": prog_a,
                    "prog_b": prog_b,
                    "prompt_id": pid,
                })

    # ── View 2: Checkpoint-perspective rows ──
    ckpt_rows = []
    for t in EVAL_TASKS:
        bm = get_benchmark(t["benchmark_id"])
        if not bm:
            continue
        mid_a = t["model_ids"][0] if len(t["model_ids"]) > 0 else ""
        mid_b = t["model_ids"][1] if len(t["model_ids"]) > 1 else ""
        name_a = get_model_name(mid_a) if mid_a else "--"
        name_b = get_model_name(mid_b) if mid_b else "--"
        # Iterate both roles (A and B perspectives)
        for role, mid_self, name_self, name_opp in (("A", mid_a, name_a, name_b), ("B", mid_b, name_b, name_a)):
            if not mid_self:
                continue
            _rnd_er.seed(hash(t["id"]))  # reset seed per role — same session list
            for pid in bm.get("prompt_ids", []):
                p = get_prompt(pid)
                if not p:
                    continue
                for ll in p.get("low_levels", []):
                    result_val = _rnd_er.choice([4, 3, 2, 1, 0])
                    exec_id = f"E{_rnd_er.randint(1000,9999)}"
                    _rnd_er.randint(1, 5)  # consume prog_a
                    _rnd_er.randint(1, 5)  # consume prog_b
                    # Map 5-level result to model's perspective
                    if result_val == 4:
                        res_label = "\u80dc\u5229" if role == "A" else "\u5931\u8d25"
                    elif result_val == 0:
                        res_label = "\u5931\u8d25" if role == "A" else "\u80dc\u5229"
                    elif result_val == 3:
                        res_label = "\u90fd\u597d"
                    elif result_val == 2:
                        res_label = "\u90fd\u4e00\u822c"
                    else:  # result_val == 1
                        res_label = "\u90fd\u5dee"
                    ckpt_rows.append({
                        "task_id": t["id"],
                        "task_no": t.get("task_no", ""),
                        "task_name": t["name"],
                        "high_level": p["high_level"],
                        "low_level": ll["zh"],
                        "model_id": mid_self,
                        "model": name_self,
                        "result": res_label,
                        "opponent": name_opp,
                        "exec_id": exec_id,
                        "prompt_id": pid,
                    })

    # ── Render task view table ──
    task_rows_html = ""
    for r in task_rows:
        rv = r["result"]
        if rv == 4:
            r_tag = '<span class="ant-tag" style="background:#e6f4f8;color:#1F80A0;border-color:#8dcde0;">A \u80dc</span>'
            r_key = "A\u80dc"
        elif rv == 3:
            r_tag = '<span class="ant-tag">\u90fd\u597d</span>'
            r_key = "\u90fd\u597d"
        elif rv == 2:
            r_tag = '<span class="ant-tag">\u90fd\u4e00\u822c</span>'
            r_key = "\u90fd\u4e00\u822c"
        elif rv == 1:
            r_tag = '<span class="ant-tag">\u90fd\u5dee</span>'
            r_key = "\u90fd\u5dee"
        else:
            r_tag = '<span class="ant-tag" style="background:#fff7e6;color:#ad6800;border-color:#ffd591;">B \u80dc</span>'
            r_key = "B\u80dc"
        detail_url = f"/tasks/{r['task_id']}/data/{r['exec_id']}?pid={r['prompt_id']}"
        task_rows_html += (
            f'<tr data-taskid="{r["task_id"]}" data-result="{r_key}" data-hl="{r["high_level"]}" data-ll="{r["low_level"]}" data-model-a="{r["model_a"]}" data-model-b="{r["model_b"]}">'
            f'<td style="font-weight:500;">{r["task_no"]}</td>'
            f'<td>{r["task_name"]}</td>'
            f'<td>{r["high_level"]}</td>'
            f'<td>{r["low_level"]}</td>'
            f'<td>{r["model_a"]}</td>'
            f'<td>{r["model_b"]}</td>'
            f'<td>{r_tag}</td>'
            f'<td style="text-align:center;color:#1F80A0;">{r["prog_a"]}</td>'
            f'<td style="text-align:center;color:#1F80A0;">{r["prog_b"]}</td>'
            f'<td class="actions-cell"><a href="{detail_url}" class="ant-btn ant-btn-sm">\u67e5\u770b\u8be6\u60c5</a></td>'
            f'</tr>'
        )
    task_empty = '<tr><td colspan="10" style="text-align:center;padding:40px;color:rgba(0,0,0,0.25);">\u6682\u65e0\u6570\u636e</td></tr>' if not task_rows_html else ""

    # ── Render checkpoint view table ──
    ckpt_rows_html = ""
    for r in ckpt_rows:
        if r["result"] == "\u80dc\u5229":
            tag_html = '<span class="ant-tag" style="background:#f6ffed;color:#52c41a;border-color:#b7eb8f;">\u80dc\u5229</span>'
        elif r["result"] == "\u5931\u8d25":
            tag_html = '<span class="ant-tag" style="background:#fff1f0;color:#ff4d4f;border-color:#ffa39e;">\u5931\u8d25</span>'
        else:
            # \u90fd\u597d / \u90fd\u4e00\u822c / \u90fd\u5dee
            tag_html = f'<span class="ant-tag">{r["result"]}</span>'
        detail_url = f"/tasks/{r['task_id']}/data/{r['exec_id']}?pid={r['prompt_id']}"
        ckpt_rows_html += (
            f'<tr data-mid="{r["model_id"]}" data-result="{r["result"]}" data-taskno="{r["task_no"]}" data-taskname="{r["task_name"]}" data-hl="{r["high_level"]}" data-ll="{r["low_level"]}">'
            f'<td style="font-weight:500;">{r["task_no"]}</td>'
            f'<td>{r["task_name"]}</td>'
            f'<td>{r["high_level"]}</td>'
            f'<td>{r["low_level"]}</td>'
            f'<td>{r["model"]}</td>'
            f'<td>{tag_html}</td>'
            f'<td>{r["opponent"]}</td>'
            f'<td class="actions-cell"><a href="{detail_url}" class="ant-btn ant-btn-sm">\u67e5\u770b\u8be6\u60c5</a></td>'
            f'</tr>'
        )
    ckpt_empty = '<tr><td colspan="8" style="text-align:center;padding:40px;color:rgba(0,0,0,0.25);">\u6682\u65e0\u6570\u636e</td></tr>' if not ckpt_rows_html else ""

    # Pre-select from URL params (single task or ckpt)
    preselect_task = request.args.get("task", "")
    preselect_ckpt = request.args.get("ckpt", "")
    # ── Multi-select options for task view ──
    task_opts = "".join(
        f'<label class="er-opt"><input type="checkbox" value="{t["id"]}" data-name="{t.get("task_no","")} &middot; {t["name"]}"{" checked" if (not preselect_task or preselect_task == t["id"]) else ""} onchange="erApplyTask()"> <span>{t.get("task_no","")} &middot; {t["name"]}</span></label>'
        for t in EVAL_TASKS
    )
    # ── Multi-select options for ckpt view ──
    ckpt_opts = "".join(
        f'<label class="er-opt"><input type="checkbox" value="{m["id"]}" data-name="{m["name"]}"{" checked" if (not preselect_ckpt or preselect_ckpt == m["id"]) else ""} onchange="erApplyCkpt()"> <span>{m["name"]}</span></label>'
        for m in MODELS
    )

    # Tab styles
    task_tab_style = (
        "padding:10px 20px;font-size:14px;cursor:pointer;border:none;background:transparent;position:relative;"
        + ("color:#1F80A0;font-weight:500;" if view == "task" else "color:rgba(0,0,0,0.65);")
    )
    ckpt_tab_style = (
        "padding:10px 20px;font-size:14px;cursor:pointer;border:none;background:transparent;position:relative;"
        + ("color:#1F80A0;font-weight:500;" if view == "ckpt" else "color:rgba(0,0,0,0.65);")
    )
    task_underline = '<span style="position:absolute;left:20px;right:20px;bottom:-1px;height:2px;background:#1F80A0;border-radius:1px;"></span>' if view == "task" else ""
    ckpt_underline = '<span style="position:absolute;left:20px;right:20px;bottom:-1px;height:2px;background:#1F80A0;border-radius:1px;"></span>' if view == "ckpt" else ""

    task_view_display = "" if view == "task" else "display:none;"
    ckpt_view_display = "" if view == "ckpt" else "display:none;"

    content = f'''
    <!-- Tab bar -->
    <div style="display:flex;gap:0;border-bottom:1px solid #f0f0f0;margin-bottom:16px;">
      <a href="/eval-records?view=task" style="{task_tab_style}text-decoration:none;">\u8bc4\u6d4b\u4efb\u52a1\u89c6\u89d2{task_underline}</a>
      <a href="/eval-records?view=ckpt" style="{ckpt_tab_style}text-decoration:none;">Checkpoint \u89c6\u89d2{ckpt_underline}</a>
    </div>

    <!-- Task view -->
    <div id="er-task" style="{task_view_display}">
      <!-- Row 1: full-width multi-select with chips -->
      <div style="margin-bottom:12px;position:relative;">
        <div class="er-dd-trigger" onclick="erToggle('task')" id="er-task-btn">
          <div id="er-task-chips" class="er-chips"></div>
          <span style="margin-left:auto;color:rgba(0,0,0,0.35);font-size:10px;flex-shrink:0;padding-left:4px;">&#9660;</span>
        </div>
        <div class="er-dd-panel" id="er-task-panel" style="width:100%;">
          <div style="padding:8px 12px;border-bottom:1px solid #f0f0f0;display:flex;gap:16px;align-items:center;">
            <a href="javascript:;" onclick="erToggleAll('task', true)" style="font-size:12px;color:#1F80A0;">\u5168\u9009</a>
            <a href="javascript:;" onclick="erToggleAll('task', false)" style="font-size:12px;color:rgba(0,0,0,0.45);">\u53d6\u6d88</a>
          </div>
          <div style="max-height:280px;overflow-y:auto;padding:6px 0;">
            {task_opts}
          </div>
        </div>
      </div>
      <!-- Row 2: text filters + export -->
      <div class="filter-bar" style="margin-bottom:16px;">
        <input type="text" id="f-task-model" placeholder="\u8f93\u5165 checkpoint\uff0c\u641c\u7d22\u5176\u4f5c\u4e3a\u8bc4\u6d4b\u6a21\u578b\u7684\u8bb0\u5f55" style="min-width:300px;">
        <input type="text" id="f-task-hl" placeholder="High Level" style="min-width:180px;">
        <input type="text" id="f-task-ll" placeholder="Low Level" style="min-width:180px;">
        <button class="ant-btn" onclick="erTaskClear()">\u6e05\u7a7a</button>
        <button class="ant-btn ant-btn-primary" onclick="erApplyTask()">\u641c\u7d22</button>
        <span style="flex:1;"></span>
        <button class="ant-btn" onclick="erExport('task')" style="display:inline-flex;align-items:center;gap:6px;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          \u5bfc\u51fa
        </button>
      </div>
      <div class="ant-card ant-card-bordered">
        <table class="ant-table" id="er-task-tbl">
          <thead><tr>
            <th>\u4efb\u52a1ID</th><th>\u4efb\u52a1\u540d\u79f0</th><th>High Level</th><th>Low Level</th><th>A \u6a21\u578b</th><th>B \u6a21\u578b</th><th>\u8bc4\u6d4b\u7ed3\u679c</th><th>A \u8fdb\u5ea6\u5206</th><th>B \u8fdb\u5ea6\u5206</th><th>\u64cd\u4f5c</th>
          </tr></thead>
          <tbody>{task_rows_html}{task_empty}</tbody>
        </table>
        <div id="er-task-pg"></div>
      </div>
    </div>

    <!-- Ckpt view -->
    <div id="er-ckpt" style="{ckpt_view_display}">
      <!-- Row 1: full-width multi-select with chips -->
      <div style="margin-bottom:12px;position:relative;">
        <div class="er-dd-trigger" onclick="erToggle('ckpt')" id="er-ckpt-btn">
          <div id="er-ckpt-chips" class="er-chips"></div>
          <span style="margin-left:auto;color:rgba(0,0,0,0.35);font-size:10px;flex-shrink:0;padding-left:4px;">&#9660;</span>
        </div>
        <div class="er-dd-panel" id="er-ckpt-panel" style="width:100%;">
          <div style="padding:8px 12px;border-bottom:1px solid #f0f0f0;display:flex;gap:16px;align-items:center;">
            <a href="javascript:;" onclick="erToggleAll('ckpt', true)" style="font-size:12px;color:#1F80A0;">\u5168\u9009</a>
            <a href="javascript:;" onclick="erToggleAll('ckpt', false)" style="font-size:12px;color:rgba(0,0,0,0.45);">\u53d6\u6d88</a>
          </div>
          <div style="max-height:280px;overflow-y:auto;padding:6px 0;">
            {ckpt_opts}
          </div>
        </div>
      </div>
      <!-- Row 2: text filters + export -->
      <div class="filter-bar" style="margin-bottom:16px;">
        <input type="text" id="f-ckpt-tid" placeholder="\u4efb\u52a1ID" style="min-width:120px;">
        <input type="text" id="f-ckpt-tname" placeholder="\u4efb\u52a1\u540d\u79f0" style="min-width:140px;">
        <input type="text" id="f-ckpt-hl" placeholder="High Level" style="min-width:160px;">
        <input type="text" id="f-ckpt-ll" placeholder="Low Level" style="min-width:160px;">
        <button class="ant-btn" onclick="erCkptClear()">\u6e05\u7a7a</button>
        <button class="ant-btn ant-btn-primary" onclick="erApplyCkpt()">\u641c\u7d22</button>
        <span style="flex:1;"></span>
        <button class="ant-btn" onclick="erExport('ckpt')" style="display:inline-flex;align-items:center;gap:6px;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          \u5bfc\u51fa
        </button>
      </div>
      <div class="ant-card ant-card-bordered">
        <table class="ant-table" id="er-ckpt-tbl">
          <thead><tr>
            <th>\u4efb\u52a1ID</th><th>\u4efb\u52a1\u540d\u79f0</th><th>High Level</th><th>Low Level</th><th>Checkpoint</th><th>\u6bd4\u8f83\u7ed3\u679c</th><th>\u6bd4\u8f83\u5bf9\u624b</th><th>\u64cd\u4f5c</th>
          </tr></thead>
          <tbody>{ckpt_rows_html}{ckpt_empty}</tbody>
        </table>
        <div id="er-ckpt-pg"></div>
      </div>
    </div>


    <script>
    var ER_PAGE_SIZE = 20;
    window.erTaskPage = 1;
    window.erCkptPage = 1;
    function erToggle(kind) {{
      var panel = document.getElementById('er-'+kind+'-panel');
      panel.classList.toggle('open');
    }}
    function erToggleAll(kind, checked) {{
      document.querySelectorAll('#er-'+kind+'-panel input[type=checkbox]').forEach(function(cb) {{ cb.checked = checked; }});
      if (kind === 'task') erApplyTask(); else erApplyCkpt();
    }}
    function erEscAttr(s) {{
      return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }}
    function erUpdateChips(kind, allText) {{
      var cbs = document.querySelectorAll('#er-'+kind+'-panel input[type=checkbox]');
      var checked = Array.prototype.filter.call(cbs, function(cb) {{ return cb.checked; }});
      var total = cbs.length;
      var box = document.getElementById('er-'+kind+'-chips');
      box.innerHTML = '';
      if (checked.length === 0) {{
        var p = document.createElement('span'); p.style.color = 'rgba(0,0,0,0.35)'; p.style.fontSize = '14px'; p.textContent = '\u672a\u9009\u62e9';
        box.appendChild(p); return;
      }}
      if (checked.length === total) {{
        var chip = document.createElement('span'); chip.className = 'er-chip';
        chip.innerHTML = '<span class="er-chip-text">' + allText + '</span>';
        box.appendChild(chip); return;
      }}
      checked.forEach(function(cb) {{
        var name = cb.getAttribute('data-name') || cb.value;
        var chip = document.createElement('span'); chip.className = 'er-chip';
        chip.innerHTML = '<span class="er-chip-text">' + erEscAttr(name) + '</span><span class="er-chip-x" data-val="' + erEscAttr(cb.value) + '">\u00d7</span>';
        box.appendChild(chip);
      }});
      box.querySelectorAll('.er-chip-x').forEach(function(x) {{
        x.addEventListener('click', function(e) {{
          e.stopPropagation();
          var val = x.getAttribute('data-val');
          var tg = document.querySelector('#er-'+kind+'-panel input[value="'+val+'"]');
          if (tg) tg.checked = false;
          if (kind === 'task') erApplyTask(); else erApplyCkpt();
        }});
      }});
    }}
    function erPaginate(kind) {{
      var tbl = document.getElementById('er-'+kind+'-tbl');
      var pg = document.getElementById('er-'+kind+'-pg');
      if (!tbl || !pg) return;
      var rows = Array.prototype.filter.call(
        tbl.querySelectorAll('tbody tr'),
        function(tr) {{ return tr.dataset.match === '1' && (tr.dataset.taskid || tr.dataset.mid); }}
      );
      var total = rows.length;
      var totalPages = Math.max(1, Math.ceil(total / ER_PAGE_SIZE));
      var cur = (kind === 'task') ? window.erTaskPage : window.erCkptPage;
      if (cur > totalPages) cur = totalPages;
      if (cur < 1) cur = 1;
      if (kind === 'task') window.erTaskPage = cur; else window.erCkptPage = cur;
      var startIdx = (cur - 1) * ER_PAGE_SIZE;
      var endIdx = startIdx + ER_PAGE_SIZE;
      // Hide all matching rows first, then show the page slice
      tbl.querySelectorAll('tbody tr').forEach(function(tr) {{
        if (!tr.dataset.taskid && !tr.dataset.mid) return;
        tr.style.display = 'none';
      }});
      rows.forEach(function(tr, i) {{
        if (i >= startIdx && i < endIdx) tr.style.display = '';
      }});
      // Render pagination
      if (total === 0) {{ pg.innerHTML = ''; return; }}
      var html = '<div style="display:flex;justify-content:flex-end;align-items:center;gap:4px;padding:12px 16px;font-size:13px;">';
      html += '<span style="color:rgba(0,0,0,0.45);margin-right:12px;">\u5171 ' + total + ' \u6761</span>';
      html += '<button type="button" class="er-pg-btn" ' + (cur <= 1 ? 'disabled' : '') + ' onclick="erGoto(\\''+kind+'\\','+(cur-1)+')">&#8249;</button>';
      var shown = [];
      for (var p = 1; p <= totalPages; p++) {{
        if (p === 1 || p === totalPages || (p >= cur - 1 && p <= cur + 1)) shown.push(p);
      }}
      var lastP = 0;
      shown.forEach(function(p) {{
        if (lastP && p > lastP + 1) html += '<span style="padding:0 4px;color:rgba(0,0,0,0.35);">\u2026</span>';
        html += '<button type="button" class="er-pg-btn ' + (p === cur ? 'active' : '') + '" onclick="erGoto(\\''+kind+'\\','+p+')">' + p + '</button>';
        lastP = p;
      }});
      html += '<button type="button" class="er-pg-btn" ' + (cur >= totalPages ? 'disabled' : '') + ' onclick="erGoto(\\''+kind+'\\','+(cur+1)+')">&#8250;</button>';
      html += '</div>';
      pg.innerHTML = html;
    }}
    function erGoto(kind, page) {{
      if (kind === 'task') window.erTaskPage = page; else window.erCkptPage = page;
      erPaginate(kind);
    }}
    function erApplyTask() {{
      erUpdateChips('task', '\u5168\u90e8\u4efb\u52a1');
      var cbs = document.querySelectorAll('#er-task-panel input[type=checkbox]');
      var sel = Array.prototype.filter.call(cbs, function(cb) {{ return cb.checked; }}).map(function(cb) {{ return cb.value; }});
      var setSel = new Set(sel);
      var mdl = (document.getElementById('f-task-model').value || '').trim().toLowerCase();
      var hl = (document.getElementById('f-task-hl').value || '').trim().toLowerCase();
      var ll = (document.getElementById('f-task-ll').value || '').trim().toLowerCase();
      var matchCount = 0;
      document.querySelectorAll('#er-task-tbl tbody tr').forEach(function(tr) {{
        if (!tr.dataset.taskid) {{ tr.dataset.match = '1'; return; }}
        var ma = (tr.dataset.modelA || '').toLowerCase();
        var mb = (tr.dataset.modelB || '').toLowerCase();
        var ok = setSel.has(tr.dataset.taskid)
              && (!mdl || ma.indexOf(mdl) >= 0 || mb.indexOf(mdl) >= 0)
              && (!hl || (tr.dataset.hl || '').toLowerCase().indexOf(hl) >= 0)
              && (!ll || (tr.dataset.ll || '').toLowerCase().indexOf(ll) >= 0);
        tr.dataset.match = ok ? '1' : '0';
        if (ok) matchCount++;
      }});
      window.erTaskPage = 1;
      erPaginate('task');
      if (window.showToast && window._erInitDone) window.showToast('\u7b5b\u9009\u51fa ' + matchCount + ' \u6761\u8bb0\u5f55', 'info');
    }}
    function erTaskClear() {{
      document.getElementById('f-task-model').value = '';
      document.getElementById('f-task-hl').value = '';
      document.getElementById('f-task-ll').value = '';
      document.querySelectorAll('#er-task-panel input[type=checkbox]').forEach(function(cb) {{ cb.checked = true; }});
      erApplyTask();
    }}
    function erApplyCkpt() {{
      erUpdateChips('ckpt', '\u5168\u90e8 Checkpoint');
      var cbs = document.querySelectorAll('#er-ckpt-panel input[type=checkbox]');
      var sel = Array.prototype.filter.call(cbs, function(cb) {{ return cb.checked; }}).map(function(cb) {{ return cb.value; }});
      var setSel = new Set(sel);
      var tid = (document.getElementById('f-ckpt-tid').value || '').trim();
      var tname = (document.getElementById('f-ckpt-tname').value || '').trim().toLowerCase();
      var hl = (document.getElementById('f-ckpt-hl').value || '').trim().toLowerCase();
      var ll = (document.getElementById('f-ckpt-ll').value || '').trim().toLowerCase();
      var matchCount = 0;
      document.querySelectorAll('#er-ckpt-tbl tbody tr').forEach(function(tr) {{
        if (!tr.dataset.mid) {{ tr.dataset.match = '1'; return; }}
        var ok = setSel.has(tr.dataset.mid)
              && (!tid || (tr.dataset.taskno || '').indexOf(tid) >= 0)
              && (!tname || (tr.dataset.taskname || '').toLowerCase().indexOf(tname) >= 0)
              && (!hl || (tr.dataset.hl || '').toLowerCase().indexOf(hl) >= 0)
              && (!ll || (tr.dataset.ll || '').toLowerCase().indexOf(ll) >= 0);
        tr.dataset.match = ok ? '1' : '0';
        if (ok) matchCount++;
      }});
      window.erCkptPage = 1;
      erPaginate('ckpt');
      if (window.showToast && window._erInitDone) window.showToast('\u7b5b\u9009\u51fa ' + matchCount + ' \u6761\u8bb0\u5f55', 'info');
    }}
    function erCkptClear() {{
      ['f-ckpt-tid', 'f-ckpt-tname', 'f-ckpt-hl', 'f-ckpt-ll'].forEach(function(id) {{ document.getElementById(id).value = ''; }});
      document.querySelectorAll('#er-ckpt-panel input[type=checkbox]').forEach(function(cb) {{ cb.checked = true; }});
      erApplyCkpt();
    }}
    function erExport(kind) {{
      var tbl = document.getElementById('er-'+kind+'-tbl');
      var rows = [];
      // Header
      var hdrs = [];
      tbl.querySelectorAll('thead th').forEach(function(th) {{
        if (th.textContent.trim() !== '\u64cd\u4f5c') hdrs.push(th.textContent.trim());
      }});
      rows.push(hdrs);
      // Body (only visible)
      tbl.querySelectorAll('tbody tr').forEach(function(tr) {{
        if (tr.style.display === 'none') return;
        if (tr.cells.length < 2) return;
        var row = [];
        for (var i = 0; i < tr.cells.length - 1; i++) {{
          row.push((tr.cells[i].textContent || '').trim().replace(/\\s+/g, ' '));
        }}
        rows.push(row);
      }});
      if (rows.length <= 1) {{
        window.showToast('\u6682\u65e0\u6570\u636e\u53ef\u5bfc\u51fa', 'warning');
        return;
      }}
      var csv = rows.map(function(r) {{
        return r.map(function(c) {{
          var s = String(c).replace(/"/g, '""');
          return (s.indexOf(',') >= 0 || s.indexOf('"') >= 0 || s.indexOf('\\n') >= 0) ? '"' + s + '"' : s;
        }}).join(',');
      }}).join('\\n');
      var blob = new Blob(['\\uFEFF' + csv], {{ type: 'text/csv;charset=utf-8' }});
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      var ts = new Date().toISOString().slice(0,10);
      a.download = '\u8bc4\u6d4b\u7ed3\u679c\u8bb0\u5f55_' + (kind === 'task' ? '\u4efb\u52a1\u89c6\u89d2' : 'Checkpoint\u89c6\u89d2') + '_' + ts + '.csv';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function() {{ URL.revokeObjectURL(url); }}, 1000);
      window.showToast('\u5df2\u5bfc\u51fa ' + (rows.length - 1) + ' \u6761\u6570\u636e', 'success');
    }}
    // Close panels when clicking outside
    document.addEventListener('click', function(e) {{
      ['task', 'ckpt'].forEach(function(k) {{
        var btn = document.getElementById('er-'+k+'-btn');
        var panel = document.getElementById('er-'+k+'-panel');
        if (!btn || !panel) return;
        if (panel.classList.contains('open') && !btn.contains(e.target) && !panel.contains(e.target)) {{
          panel.classList.remove('open');
        }}
      }});
    }});
    // Enter key triggers search on filter inputs
    ['f-task-model', 'f-task-hl', 'f-task-ll'].forEach(function(id) {{
      var el = document.getElementById(id);
      if (el) el.addEventListener('keydown', function(e) {{ if (e.key === 'Enter') {{ e.preventDefault(); erApplyTask(); }} }});
    }});
    ['f-ckpt-tid', 'f-ckpt-tname', 'f-ckpt-hl', 'f-ckpt-ll'].forEach(function(id) {{
      var el = document.getElementById(id);
      if (el) el.addEventListener('keydown', function(e) {{ if (e.key === 'Enter') {{ e.preventDefault(); erApplyCkpt(); }} }});
    }});
    // Initial render — chips + paginate (suppress toast on first load)
    erApplyTask();
    erApplyCkpt();
    window._erInitDone = true;
    </script>
    '''
    return render_page("\u8bc4\u6d4b\u7ed3\u679c\u8bb0\u5f55", content, active="eval_records")


# ── Leaderboard ──
@app.route("/leaderboard")
def leaderboard_page():
    rankings = compute_rankings()
    max_score = max(r["score"] for r in rankings) if rankings else 1
    min_score = min(r["score"] for r in rankings) if rankings else 0

    # Ranking table
    rows = ""
    for r in rankings:
        rank_cls = f"rank-{r['rank']}" if r["rank"] <= 3 else "rank-other"
        bar_pct = max(0, (r["score"] - 1200) / (max_score - 1200) * 100) if max_score > 1200 else 50
        is_ours = "Spirit" in r["model_name"]
        name_style = "font-weight:600;color:#1F80A0;" if is_ours else "font-weight:500;"
        status_tag = f'<span class="ant-tag ant-tag-green">{r["status"]}</span>' if is_ours else f'<span class="ant-tag">{r["status"]}</span>'
        win_rate = round(r["wins"] / max(r["matches"], 1) * 100)

        view_btn = icon_btn(f'/eval-records?view=ckpt&ckpt={r["model_id"]}', ICON_VIEW, "\u67e5\u770b\u8be6\u60c5", "default")
        rows += (
            "<tr>"
            f'<td><span class="rank-badge {rank_cls}">{r["rank"]}</span></td>'
            f'<td style="{name_style}">{r["model_name"]}</td>'
            f'<td><span class="score-text">{r["score"]}</span></td>'
            f'<td style="text-align:center;color:rgba(0,0,0,0.45);">{r["sd"]}</td>'
            f'<td style="text-align:center;color:rgba(0,0,0,0.45);">\u00b1{r["se"]}</td>'
            f'<td style="text-align:center;">{win_rate}%</td>'
            f'<td style="text-align:center;">{r["wins"]}</td>'
            f'<td style="text-align:center;">{r["losses"]}</td>'
            f'<td style="text-align:center;">{r["ties"]}</td>'
            f'<td style="text-align:center;">{r["matches"]}</td>'
            f'<td class="actions-cell">{view_btn}</td>'
            "</tr>"
        )

    # Confidence intervals for chart
    # Sort ascending by score for the forest-style line chart (low → high)
    rankings_asc = sorted(rankings, key=lambda r: r["score"])
    chart_labels = [r["model_name"] for r in rankings_asc]
    chart_scores = [r["score"] for r in rankings_asc]
    chart_stds = [r["std"] for r in rankings_asc]
    chart_colors = ['#1F80A0' if 'Spirit' in r['model_name'] else '#91bfcf' for r in rankings]
    chart_wins = [r["wins"] for r in rankings]
    chart_losses = [r["losses"] for r in rankings]
    chart_ties = [r["ties"] for r in rankings]

    # Win rate data
    chart_winrates = [round(r["wins"] / max(r["matches"], 1) * 100) for r in rankings]

    # Pref distribution
    pref_a = sum(1 for s in EVAL_SESSIONS if s["preference"] == 2)
    pref_tie = sum(1 for s in EVAL_SESSIONS if s["preference"] == 1)
    pref_b = sum(1 for s in EVAL_SESSIONS if s["preference"] == 0)
    total_sess = len(EVAL_SESSIONS)

    # Top model info
    top = rankings[0] if rankings else None
    top_name = top["model_name"] if top else "--"
    top_score = top["score"] if top else 0

    # Avg win rate
    avg_wr = round(sum(r["wins"] for r in rankings) / max(sum(r["matches"] for r in rankings), 1) * 100, 1)
    # Worst task (mock)
    worst_task = "\u53cd\u624b\u7269\u54c1\u6293\u53d6"
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f'''
    <!-- Title row -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <div style="display:flex;align-items:baseline;gap:12px;">
        <span style="font-size:20px;font-weight:600;color:rgba(0,0,0,0.85);">\u6a21\u578b\u6392\u884c\u699c</span>
        <span style="font-size:12px;color:rgba(0,0,0,0.45);">\u66f4\u65b0\u65f6\u95f4: {update_time}</span>
      </div>
      <div style="display:flex;gap:10px;align-items:center;">
        <input type="text" placeholder="\u641c\u7d22\u6a21\u578b..." style="min-width:180px;height:36px;padding:5px 12px;border:1px solid #d9d9d9;border-radius:8px;font-size:14px;">
        <button class="ant-btn ant-btn-primary">\u5bfc\u51fa\u699c\u5355</button>
      </div>
    </div>

    <!-- Two-column: left=summary, right=ranking -->
    <div style="display:grid;grid-template-columns:320px 1fr;gap:20px;align-items:stretch;height:calc(100vh - 160px);">

      <!-- Left: summary cards -->
      <div style="display:flex;flex-direction:column;gap:16px;">
        <div class="ant-card ant-card-bordered">
          <div class="ant-card-body" style="padding:20px;">
            <div style="font-size:13px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u5e73\u53f0\u6700\u4f73\u6a21\u578b\u5f97\u5206</div>
            <div style="font-size:48px;font-weight:700;color:#1F80A0;line-height:1;">{top_score}<span style="font-size:20px;color:rgba(0,0,0,0.25);">.00</span></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px;">
              <div style="background:#fafafa;border-radius:8px;padding:10px;">
                <div style="font-size:12px;color:rgba(0,0,0,0.45);">\u603b\u6d4b\u8bc4\u6a21\u578b\u6570</div>
                <div style="font-size:22px;font-weight:600;">{len(rankings)}</div>
              </div>
              <div style="background:#fafafa;border-radius:8px;padding:10px;">
                <div style="font-size:12px;color:rgba(0,0,0,0.45);">\u79ef\u7d2f\u6d4b\u8bd5\u7ec4\u6570</div>
                <div style="font-size:22px;font-weight:600;">{total_sess:,}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="ant-card ant-card-bordered" style="flex:1;">
          <div class="ant-card-body" style="padding:20px;">
            <div style="font-size:13px;color:rgba(0,0,0,0.45);margin-bottom:4px;">\u5f53\u524d\u9738\u699c\u6a21\u578b</div>
            <div style="font-size:20px;font-weight:600;margin-bottom:12px;">{top_name}</div>
            <canvas id="radarChart" height="200"></canvas>
          </div>
        </div>
      </div>

      <!-- Right: ranking table / chart -->
      <div class="ant-card ant-card-bordered" style="display:flex;flex-direction:column;">
        <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;flex-shrink:0;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:15px;font-weight:500;">\u6392\u540d\u8be6\u60c5</span>
          <div style="display:inline-flex;background:#fafafa;border:1px solid #f0f0f0;border-radius:8px;padding:2px;">
            <button type="button" id="lb-tab-table" class="lb-view-btn active" onclick="lbSwitchView('table')">\u8868\u683c</button>
            <button type="button" id="lb-tab-chart" class="lb-view-btn" onclick="lbSwitchView('chart')">\u56fe\u8868</button>
          </div>
        </div>
        <div id="lb-table-view" style="flex:1;overflow:auto;">
          <table class="ant-table">
            <thead><tr>
              <th style="width:50px;">\u6392\u540d</th>
              <th>\u6a21\u578b\u540d\u79f0</th>
              <th>\u5f97\u5206</th>
              <th style="text-align:center;width:60px;" data-tip="Standard Deviation \u6807\u51c6\u5dee\uff1a\u5355\u573a\u5f97\u5206\u7684\u6ce2\u52a8\u5e45\u5ea6\uff0c\u53cd\u6620\u8868\u73b0\u7a33\u5b9a\u6027\u3002SD \u503c\u8d8a\u5c0f\u8868\u793a\u6a21\u578b\u5728\u5404\u6b21\u8bc4\u6d4b\u4e2d\u53d1\u6325\u8d8a\u7a33\u5b9a">SD</th>
              <th style="text-align:center;width:60px;" data-tip="Standard Error \u6807\u51c6\u8bef\uff1a\u5f97\u5206\u4f30\u8ba1\u503c\u7684\u4e0d\u786e\u5b9a\u5ea6\uff0cSE = SD \u00f7 \u221a\u573a\u6b21\u3002\u573a\u6b21\u8d8a\u591a SE \u8d8a\u5c0f\uff0c\u6392\u540d\u8d8a\u53ef\u9760">SE</th>
              <th style="text-align:center;width:55px;">\u80dc\u7387</th>
              <th style="text-align:center;width:40px;">\u80dc</th>
              <th style="text-align:center;width:40px;">\u8d1f</th>
              <th style="text-align:center;width:40px;">\u5e73</th>
              <th style="text-align:center;width:50px;">\u573a\u6b21</th>
              <th style="width:60px;">\u64cd\u4f5c</th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        <div id="lb-chart-view" style="display:none;flex:1;padding:20px;overflow:auto;">
          <canvas id="lbBarChart"></canvas>
        </div>
      </div>
    </div>

    <style>
      .lb-view-btn {{ padding:4px 14px;border:none;background:transparent;border-radius:6px;font-size:13px;color:rgba(0,0,0,0.65);cursor:pointer;transition:all 0.15s; }}
      .lb-view-btn:hover {{ color:#1F80A0; }}
      .lb-view-btn.active {{ background:#fff;color:#1F80A0;font-weight:500;box-shadow:0 1px 2px rgba(0,0,0,0.06); }}
    </style>

    <script>
    // Radar chart for top model
    new Chart(document.getElementById('radarChart'), {{
      type: 'radar',
      data: {{
        labels: ['\u62fe\u53d6', '\u653e\u7f6e', '\u5f00\u5408', '\u5de5\u5177', '\u7cbe\u7ec6\u64cd\u4f5c'],
        datasets: [{{
          label: '{top_name}',
          data: [85, 78, 72, 65, 80],
          borderColor: '#1F80A0',
          backgroundColor: 'rgba(31,128,160,0.15)',
          pointBackgroundColor: '#1F80A0',
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ r: {{ beginAtZero: true, max: 100, ticks: {{ stepSize: 25 }} }} }},
      }}
    }});

    // Leaderboard forest/line chart with error bars (lazy-init)
    var lbBarChart = null;
    var lbChartLabels = {chart_labels!r};
    var lbChartScores = {chart_scores!r};
    var lbChartSE = {chart_stds!r};
    // Error bar plugin — draws vertical T-shaped SE indicators at each point
    var lbErrorBarPlugin = {{
      id: 'lbErrorBars',
      afterDatasetsDraw: function(chart) {{
        var meta = chart.getDatasetMeta(0);
        if (!meta || !meta.data) return;
        var yScale = chart.scales.y;
        var ctx = chart.ctx;
        ctx.save();
        ctx.strokeStyle = '#1F80A0';
        ctx.lineWidth = 1.5;
        ctx.lineCap = 'round';
        meta.data.forEach(function(point, i) {{
          var se = lbChartSE[i];
          if (!se) return;
          var x = point.x;
          var yTop = yScale.getPixelForValue(lbChartScores[i] + se);
          var yBot = yScale.getPixelForValue(lbChartScores[i] - se);
          ctx.beginPath(); ctx.moveTo(x, yTop); ctx.lineTo(x, yBot); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(x - 5, yTop); ctx.lineTo(x + 5, yTop); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(x - 5, yBot); ctx.lineTo(x + 5, yBot); ctx.stroke();
        }});
        ctx.restore();
      }}
    }};
    function lbInitBarChart() {{
      if (lbBarChart) return;
      var canvas = document.getElementById('lbBarChart');
      canvas.height = 420;
      // Gradient fill under the line
      var canvasCtx = canvas.getContext('2d');
      var gradient = canvasCtx.createLinearGradient(0, 0, 0, 400);
      gradient.addColorStop(0, 'rgba(31,128,160,0.28)');
      gradient.addColorStop(1, 'rgba(31,128,160,0.02)');
      lbBarChart = new Chart(canvas, {{
        type: 'line',
        data: {{
          labels: lbChartLabels,
          datasets: [{{
            label: '\u5f97\u5206',
            data: lbChartScores,
            borderColor: '#1F80A0',
            backgroundColor: gradient,
            pointBackgroundColor: '#1F80A0',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 6,
            pointHoverRadius: 8,
            borderWidth: 2.5,
            tension: 0.3,
            fill: 'origin',
          }}]
        }},
        plugins: [lbErrorBarPlugin],
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          layout: {{ padding: {{ top: 10, right: 10, bottom: 60, left: 10 }} }},
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: function(ctx) {{
                  var se = lbChartSE[ctx.dataIndex];
                  return '\u5f97\u5206: ' + ctx.parsed.y + '   SE \u00b1' + se;
                }}
              }}
            }}
          }},
          scales: {{
            x: {{
              ticks: {{ maxRotation: 90, minRotation: 90, autoSkip: false, font: {{ size: 11 }}, color: 'rgba(0,0,0,0.65)' }},
              grid: {{ display: false }}
            }},
            y: {{
              title: {{ display: true, text: '\u5f97\u5206', color: 'rgba(0,0,0,0.65)', font: {{ size: 13 }} }},
              beginAtZero: false,
              grid: {{ color: '#f0f0f0' }}
            }}
          }}
        }}
      }});
    }}
    function lbSwitchView(view) {{
      var tv = document.getElementById('lb-table-view');
      var cv = document.getElementById('lb-chart-view');
      var tb = document.getElementById('lb-tab-table');
      var cb = document.getElementById('lb-tab-chart');
      if (view === 'chart') {{
        tv.style.display = 'none';
        cv.style.display = '';
        tb.classList.remove('active');
        cb.classList.add('active');
        lbInitBarChart();
      }} else {{
        tv.style.display = '';
        cv.style.display = 'none';
        tb.classList.add('active');
        cb.classList.remove('active');
      }}
    }}
    </script>
    '''
    return render_page("\u6392\u884c\u699c", content, active="leaderboard")


# ── Multi-dimensional Analysis ──
@app.route("/analysis")
def analysis_page():
    rankings = compute_rankings()
    ranked_model_ids = [r["model_id"] for r in rankings]
    default_selection = ranked_model_ids[:5]

    # Radar tag categories
    radar_tag_groups = {
        "capability": {
            "label": "能力维度",
            "axes": ["空间感知", "语言理解", "推理规划", "精细操作", "异常恢复"],
        },
        "action": {
            "label": "动作维度",
            "axes": ["拾取", "放置", "开合", "推拉", "工具使用"],
        },
        "object": {
            "label": "物体维度",
            "axes": ["刚体", "柔体", "液体", "容器", "工具"],
        },
    }

    # Per-model per-axis mock scores
    axis_scores = {}
    for mid in ranked_model_ids:
        mr = next((r for r in rankings if r["model_id"] == mid), None)
        base = mr["score"] if mr else 1500
        axis_scores[mid] = {}
        for grp in radar_tag_groups.values():
            for axis in grp["axes"]:
                random.seed(hash(mid + axis))
                axis_scores[mid][axis] = round(base + random.gauss(0, 80), 1)

    # Head-to-head
    h2h_raw = {}
    for a in ranked_model_ids:
        h2h_raw[a] = {}
        for b in ranked_model_ids:
            if a == b:
                h2h_raw[a][b] = None
                continue
            wins = sum(1 for s in EVAL_SESSIONS if
                       (s["policy_a"] == a and s["policy_b"] == b and s["preference"] == 2) or
                       (s["policy_a"] == b and s["policy_b"] == a and s["preference"] == 0))
            losses = sum(1 for s in EVAL_SESSIONS if
                         (s["policy_a"] == a and s["policy_b"] == b and s["preference"] == 0) or
                         (s["policy_a"] == b and s["policy_b"] == a and s["preference"] == 2))
            ties = sum(1 for s in EVAL_SESSIONS if
                       (s["policy_a"] == a and s["policy_b"] == b and s["preference"] == 1) or
                       (s["policy_a"] == b and s["policy_b"] == a and s["preference"] == 1))
            total = wins + losses + ties
            if total == 0:
                ra = next((r for r in rankings if r["model_id"] == a), None)
                rb = next((r for r in rankings if r["model_id"] == b), None)
                diff = (ra["score"] - rb["score"]) if (ra and rb) else 0
                rate = 0.5 + max(-0.4, min(0.4, diff / 800))
                h2h_raw[a][b] = {"wins": 0, "losses": 0, "ties": 0, "total": 0, "rate": round(rate, 2)}
            else:
                rate = (wins + 0.5 * ties) / total
                h2h_raw[a][b] = {"wins": wins, "losses": losses, "ties": ties, "total": total, "rate": round(rate, 2)}

    model_opts = "".join(
        f'<label class="er-opt"><input type="checkbox" class="an-model-cb" value="{r["model_id"]}" data-name="{r["model_name"]}"{" checked" if r["model_id"] in default_selection else ""}> <span>#{r["rank"]} {r["model_name"]}</span></label>'
        for r in rankings
    )
    tag_opts = "".join(
        f'<option value="{k}"{" selected" if k == "capability" else ""}>{v["label"]}</option>'
        for k, v in radar_tag_groups.items()
    )
    model_names_map = {r["model_id"]: r["model_name"] for r in rankings}
    model_ranks_map = {r["model_id"]: r["rank"] for r in rankings}

    # Trend data: (released_at_ms, score, family) per model
    trend_data = {}
    for m in MODELS:
        mr = next((r for r in rankings if r["model_id"] == m["id"]), None)
        if not mr:
            continue
        try:
            ts = int(datetime.strptime(m["released_at"], "%Y-%m-%d").timestamp() * 1000)
        except Exception:
            continue
        trend_data[m["id"]] = {
            "t": ts,
            "score": mr["score"],
            "family": m.get("family", m["name"]),
            "released": m["released_at"],
        }

    # Low-level win rate: per model × per low-level step
    all_low_levels = []
    for _p in PROMPTS:
        for _ll in _p.get("low_levels", []):
            all_low_levels.append({"id": _ll["id"], "zh": _ll["zh"], "hl": _p["high_level"]})
    ll_rates = {}
    for mid in ranked_model_ids:
        ll_rates[mid] = {}
        mr = next((r for r in rankings if r["model_id"] == mid), None)
        base_rate = min(0.85, max(0.15, 0.5 + ((mr["score"] if mr else 1500) - 1500) / 800))
        for _ll in all_low_levels:
            random.seed(hash(mid + "_" + _ll["id"]))
            total = random.randint(8, 30)
            # Bias win rate toward model's overall strength
            mean = base_rate + random.gauss(0, 0.12)
            mean = max(0.05, min(0.95, mean))
            wins = round(total * mean)
            ties = random.randint(0, max(1, total - wins))
            losses = max(0, total - wins - ties)
            rate = round((wins + 0.5 * ties) / max(total, 1), 2)
            ll_rates[mid][_ll["id"]] = {"wins": wins, "losses": losses, "ties": ties, "total": total, "rate": rate}

    # Serialize as JSON for JS (None -> null etc.)
    an_tag_groups_json = json.dumps(radar_tag_groups, ensure_ascii=False)
    an_axis_scores_json = json.dumps(axis_scores, ensure_ascii=False)
    an_h2h_json = json.dumps(h2h_raw, ensure_ascii=False)
    an_model_names_json = json.dumps(model_names_map, ensure_ascii=False)
    an_model_ranks_json = json.dumps(model_ranks_map, ensure_ascii=False)
    an_ranked_json = json.dumps(ranked_model_ids, ensure_ascii=False)
    an_trend_json = json.dumps(trend_data, ensure_ascii=False)
    an_ll_rates_json = json.dumps(ll_rates, ensure_ascii=False)
    an_low_levels_json = json.dumps(all_low_levels, ensure_ascii=False)

    content = f'''
    <!-- Top model filter -->
    <div style="margin-bottom:16px;position:relative;">
      <div class="er-dd-trigger" id="an-model-btn" onclick="anToggleModel()">
        <div id="an-model-chips" class="er-chips"></div>
        <span style="margin-left:auto;color:rgba(0,0,0,0.35);font-size:10px;flex-shrink:0;padding-left:4px;">&#9660;</span>
      </div>
      <div class="er-dd-panel" id="an-model-panel" style="width:100%;">
        <div style="padding:8px 12px;border-bottom:1px solid #f0f0f0;display:flex;gap:16px;align-items:center;">
          <a href="javascript:;" onclick="anToggleAllModels(true)" style="font-size:12px;color:#1F80A0;">\u5168\u9009</a>
          <a href="javascript:;" onclick="anToggleAllModels(false)" style="font-size:12px;color:rgba(0,0,0,0.45);">\u53d6\u6d88</a>
          <a href="javascript:;" onclick="anTopN(5)" style="font-size:12px;color:#1F80A0;">Top 5</a>
        </div>
        <div style="max-height:320px;overflow-y:auto;padding:6px 0;">
          {model_opts}
        </div>
      </div>
    </div>

    <!-- Row 1: Radar + Weakness radar -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:stretch;margin-bottom:20px;">
      <div class="ant-card ant-card-bordered" style="display:flex;flex-direction:column;">
        <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:15px;font-weight:500;">\u7ef4\u5ea6\u96f7\u8fbe\u56fe</span>
          <select id="an-tag-sel" onchange="anRenderRadar();anRenderWeakness();" class="has-value" style="height:32px;padding:4px 28px 4px 10px;border:1px solid #d9d9d9;border-radius:8px;font-size:13px;color:rgba(0,0,0,0.85);">
            {tag_opts}
          </select>
        </div>
        <div style="padding:20px;flex:1;min-height:380px;"><canvas id="radarChart"></canvas></div>
      </div>
      <div class="ant-card ant-card-bordered" style="display:flex;flex-direction:column;">
        <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:15px;font-weight:500;">\u80fd\u529b\u77ed\u677f\u96f7\u8fbe</span>
          <span style="font-size:12px;color:rgba(0,0,0,0.45);">\u503c\u8d8a\u5927 = \u8ddd\u79bb\u6700\u5f3a\u7684\u5dee\u8ddd\u8d8a\u5927</span>
        </div>
        <div style="padding:20px;flex:1;min-height:380px;"><canvas id="weaknessChart"></canvas></div>
      </div>
    </div>

    <!-- Row 2: Trend + H2H -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:stretch;margin-bottom:20px;">
      <div class="ant-card ant-card-bordered" style="display:flex;flex-direction:column;">
        <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:15px;font-weight:500;">\u5f97\u5206\u8d8b\u52bf</span>
          <span style="font-size:12px;color:rgba(0,0,0,0.45);">\u540c\u7cfb\u5217\u6309\u53d1\u5e03\u65f6\u95f4\u8fde\u7ebf</span>
        </div>
        <div style="padding:20px;flex:1;min-height:380px;"><canvas id="trendChart"></canvas></div>
      </div>
      <div class="ant-card ant-card-bordered" style="display:flex;flex-direction:column;">
        <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
          <span style="font-size:15px;font-weight:500;">\u6a21\u578b\u5bf9\u6218\u77e9\u9635</span>
          <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:rgba(0,0,0,0.45);">
            <span>\u884c\u5bf9\u5217\u80dc\u7387:</span>
            <span style="width:14px;height:14px;background:#f0f8fa;border:1px solid #e6f4f8;border-radius:2px;"></span>
            <span>0%</span>
            <span style="width:14px;height:14px;background:#8dcde0;border-radius:2px;"></span>
            <span>50%</span>
            <span style="width:14px;height:14px;background:#1F80A0;border-radius:2px;"></span>
            <span>100%</span>
          </div>
        </div>
        <div style="padding:20px;overflow:auto;"><div id="h2h-matrix"></div></div>
      </div>
    </div>

    <!-- Row 3: Low-level heatmap (full width) -->
    <div class="ant-card ant-card-bordered" style="display:flex;flex-direction:column;">
      <div style="padding:12px 20px;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <span style="font-size:15px;font-weight:500;">Low Level \u80dc\u7387\u70ed\u529b\u56fe</span>
        <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:rgba(0,0,0,0.45);">
          <span>\u80dc\u7387:</span>
          <span style="width:14px;height:14px;background:#f0f8fa;border:1px solid #e6f4f8;border-radius:2px;"></span>
          <span>0%</span>
          <span style="width:14px;height:14px;background:#8dcde0;border-radius:2px;"></span>
          <span>50%</span>
          <span style="width:14px;height:14px;background:#1F80A0;border-radius:2px;"></span>
          <span>100%</span>
        </div>
      </div>
      <div style="padding:20px;overflow:auto;"><div id="ll-heatmap"></div></div>
    </div>

    <script>
    var anTagGroups = {an_tag_groups_json};
    var anAxisScores = {an_axis_scores_json};
    var anH2H = {an_h2h_json};
    var anModelNames = {an_model_names_json};
    var anModelRanks = {an_model_ranks_json};
    var anRanked = {an_ranked_json};
    var anTrend = {an_trend_json};
    var anLLRates = {an_ll_rates_json};
    var anLowLevels = {an_low_levels_json};
    var anRadarChart = null;
    var anWeaknessChart = null;
    var anTrendChart = null;
    var anPalette = ['#1F80A0', '#5aa7bf', '#8dcde0', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#64748b'];

    function anGetSelected() {{
      return Array.prototype.filter.call(document.querySelectorAll('.an-model-cb'), function(cb) {{ return cb.checked; }}).map(function(cb) {{ return cb.value; }});
    }}
    function anUpdateChips() {{
      var cbs = document.querySelectorAll('.an-model-cb');
      var checked = Array.prototype.filter.call(cbs, function(cb) {{ return cb.checked; }});
      var total = cbs.length;
      var box = document.getElementById('an-model-chips');
      box.innerHTML = '';
      if (checked.length === 0) {{
        var p = document.createElement('span'); p.style.color = 'rgba(0,0,0,0.35)'; p.style.fontSize = '14px'; p.textContent = '\u672a\u9009\u62e9';
        box.appendChild(p); return;
      }}
      if (checked.length === total) {{
        var c = document.createElement('span'); c.className = 'er-chip';
        c.innerHTML = '<span class="er-chip-text">\u5168\u90e8\u6a21\u578b</span>';
        box.appendChild(c); return;
      }}
      checked.forEach(function(cb) {{
        var nm = cb.getAttribute('data-name') || cb.value;
        var chip = document.createElement('span'); chip.className = 'er-chip';
        chip.innerHTML = '<span class="er-chip-text">' + nm + '</span><span class="er-chip-x" data-val="' + cb.value + '">\u00d7</span>';
        box.appendChild(chip);
      }});
      box.querySelectorAll('.er-chip-x').forEach(function(x) {{
        x.addEventListener('click', function(e) {{
          e.stopPropagation();
          var tg = document.querySelector('.an-model-cb[value="' + x.getAttribute('data-val') + '"]');
          if (tg) tg.checked = false;
          anApply();
        }});
      }});
    }}
    function anToggleModel() {{ document.getElementById('an-model-panel').classList.toggle('open'); }}
    function anToggleAllModels(on) {{
      document.querySelectorAll('.an-model-cb').forEach(function(cb) {{ cb.checked = on; }});
      anApply();
    }}
    function anTopN(n) {{
      document.querySelectorAll('.an-model-cb').forEach(function(cb, i) {{ cb.checked = i < n; }});
      anApply();
    }}
    document.addEventListener('click', function(e) {{
      var btn = document.getElementById('an-model-btn');
      var panel = document.getElementById('an-model-panel');
      if (btn && panel && panel.classList.contains('open') && !btn.contains(e.target) && !panel.contains(e.target)) {{
        panel.classList.remove('open');
      }}
    }});
    document.querySelectorAll('.an-model-cb').forEach(function(cb) {{ cb.addEventListener('change', anApply); }});

    function anRenderRadar() {{
      var selected = anGetSelected();
      var grp = document.getElementById('an-tag-sel').value;
      var axes = anTagGroups[grp].axes;
      var datasets = selected.map(function(mid, i) {{
        var c = anPalette[i % anPalette.length];
        var data = axes.map(function(ax) {{ return (anAxisScores[mid] || {{}})[ax] || 0; }});
        return {{ label: anModelNames[mid], data: data, borderColor: c, backgroundColor: c + '22', pointBackgroundColor: c, borderWidth: 2 }};
      }});
      if (anRadarChart) anRadarChart.destroy();
      anRadarChart = new Chart(document.getElementById('radarChart'), {{
        type: 'radar',
        data: {{ labels: axes, datasets: datasets }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, pointStyle: 'rectRounded', boxWidth: 12, boxHeight: 12, font: {{ size: 12 }} }} }} }},
          scales: {{ r: {{ beginAtZero: false, min: 1100, ticks: {{ stepSize: 100 }}, grid: {{ color: '#f0f0f0' }}, angleLines: {{ color: '#f0f0f0' }} }} }}
        }}
      }});
    }}

    function anLerpColor(a, b, t) {{
      var r = Math.round(a[0] + (b[0] - a[0]) * t);
      var g = Math.round(a[1] + (b[1] - a[1]) * t);
      var bl = Math.round(a[2] + (b[2] - a[2]) * t);
      return 'rgb(' + r + ',' + g + ',' + bl + ')';
    }}
    function anRateColor(rate) {{
      if (rate <= 0.5) return anLerpColor([240, 248, 250], [141, 205, 224], rate / 0.5);
      return anLerpColor([141, 205, 224], [31, 128, 160], (rate - 0.5) / 0.5);
    }}
    function anRenderMatrix() {{
      var selected = anGetSelected();
      var box = document.getElementById('h2h-matrix');
      if (selected.length === 0) {{ box.innerHTML = '<div style="text-align:center;padding:40px;color:rgba(0,0,0,0.25);">\u8bf7\u9009\u62e9\u6a21\u578b</div>'; return; }}
      var html = '<table style="border-collapse:separate;border-spacing:2px;margin:0 auto;font-size:12px;"><thead><tr><th></th>';
      selected.forEach(function(mid) {{
        html += '<th style="padding:6px 4px;writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;font-weight:500;color:rgba(0,0,0,0.65);">' + anModelNames[mid] + '</th>';
      }});
      html += '</tr></thead><tbody>';
      selected.forEach(function(a) {{
        html += '<tr><td style="padding:6px 10px;font-weight:500;color:rgba(0,0,0,0.65);white-space:nowrap;text-align:right;">' + anModelNames[a] + '</td>';
        selected.forEach(function(b) {{
          if (a === b) {{
            html += '<td style="background:#fafafa;color:rgba(0,0,0,0.25);min-width:60px;height:40px;text-align:center;border-radius:4px;">-</td>';
          }} else {{
            var cell = (anH2H[a] || {{}})[b] || {{rate: 0.5, total: 0}};
            var rate = cell.rate;
            var bg = anRateColor(rate);
            var textColor = rate > 0.55 ? '#fff' : 'rgba(0,0,0,0.85)';
            var pct = Math.round(rate * 100);
            var tt = cell.total > 0 ? (cell.wins + 'W-' + cell.losses + 'L-' + cell.ties + 'T (' + cell.total + '\u573a)') : '\u9884\u4f30';
            html += '<td title="' + anModelNames[a] + ' vs ' + anModelNames[b] + ': ' + tt + '" style="background:' + bg + ';color:' + textColor + ';min-width:60px;height:40px;text-align:center;border-radius:4px;font-weight:500;padding:0 8px;">' + pct + '%</td>';
          }}
        }});
        html += '</tr>';
      }});
      html += '</tbody></table>';
      box.innerHTML = html;
    }}
    function anRenderWeakness() {{
      var selected = anGetSelected();
      var grp = document.getElementById('an-tag-sel').value;
      var axes = anTagGroups[grp].axes;
      // Max score per axis across all models (global benchmark)
      var maxPerAxis = {{}};
      axes.forEach(function(ax) {{
        var vals = Object.keys(anAxisScores).map(function(mid) {{ return (anAxisScores[mid] || {{}})[ax] || 0; }});
        maxPerAxis[ax] = vals.length ? Math.max.apply(null, vals) : 0;
      }});
      var datasets = selected.map(function(mid, i) {{
        var c = anPalette[i % anPalette.length];
        var data = axes.map(function(ax) {{
          var score = (anAxisScores[mid] || {{}})[ax] || 0;
          return Math.max(0, Math.round((maxPerAxis[ax] - score) * 10) / 10);
        }});
        return {{ label: anModelNames[mid], data: data, borderColor: c, backgroundColor: c + '22', pointBackgroundColor: c, borderWidth: 2 }};
      }});
      if (anWeaknessChart) anWeaknessChart.destroy();
      anWeaknessChart = new Chart(document.getElementById('weaknessChart'), {{
        type: 'radar',
        data: {{ labels: axes, datasets: datasets }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ usePointStyle: true, pointStyle: 'rectRounded', boxWidth: 12, boxHeight: 12, font: {{ size: 12 }} }} }},
            tooltip: {{ callbacks: {{ label: function(ctx) {{ return ctx.dataset.label + ': \u843d\u540e ' + ctx.parsed.r + ' \u5206'; }} }} }}
          }},
          scales: {{ r: {{ beginAtZero: true, grid: {{ color: '#f0f0f0' }}, angleLines: {{ color: '#f0f0f0' }}, ticks: {{ callback: function(v) {{ return '-' + v; }} }} }} }}
        }}
      }});
    }}

    function anRenderTrend() {{
      var selected = anGetSelected();
      // Group selected models by family, sort each family by release time
      var byFamily = {{}};
      selected.forEach(function(mid) {{
        var d = anTrend[mid];
        if (!d) return;
        if (!byFamily[d.family]) byFamily[d.family] = [];
        byFamily[d.family].push({{x: d.t, y: d.score, name: anModelNames[mid], released: d.released}});
      }});
      Object.keys(byFamily).forEach(function(f) {{
        byFamily[f].sort(function(a, b) {{ return a.x - b.x; }});
      }});
      var famNames = Object.keys(byFamily);
      var datasets = famNames.map(function(f, i) {{
        var c = anPalette[i % anPalette.length];
        return {{
          label: f,
          data: byFamily[f],
          borderColor: c,
          backgroundColor: c,
          pointBackgroundColor: c,
          pointRadius: 6,
          pointHoverRadius: 8,
          showLine: byFamily[f].length > 1,
          tension: 0.2,
          borderWidth: 2,
        }};
      }});
      if (anTrendChart) anTrendChart.destroy();
      var ctx = document.getElementById('trendChart');
      anTrendChart = new Chart(ctx, {{
        type: 'scatter',
        data: {{ datasets: datasets }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'bottom', labels: {{ usePointStyle: true, pointStyle: 'rectRounded', boxWidth: 12, boxHeight: 12, font: {{ size: 12 }} }} }},
            tooltip: {{
              callbacks: {{
                title: function(items) {{
                  return items[0].raw.name;
                }},
                label: function(ctx) {{
                  return '\u53d1\u5e03: ' + ctx.raw.released + '   \u5f97\u5206: ' + ctx.parsed.y;
                }}
              }}
            }}
          }},
          scales: {{
            x: {{
              type: 'linear',
              title: {{ display: true, text: '\u53d1\u5e03\u65f6\u95f4', color: 'rgba(0,0,0,0.65)', font: {{ size: 12 }} }},
              ticks: {{
                callback: function(v) {{
                  var d = new Date(v);
                  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
                }},
                maxRotation: 0,
                autoSkipPadding: 20,
              }},
              grid: {{ color: '#f0f0f0' }},
            }},
            y: {{
              title: {{ display: true, text: '\u5f97\u5206', color: 'rgba(0,0,0,0.65)', font: {{ size: 12 }} }},
              grid: {{ color: '#f0f0f0' }},
            }}
          }}
        }}
      }});
    }}

    function anRenderHeatmap() {{
      var selected = anGetSelected();
      var box = document.getElementById('ll-heatmap');
      if (selected.length === 0) {{ box.innerHTML = '<div style="text-align:center;padding:40px;color:rgba(0,0,0,0.25);">\u8bf7\u9009\u62e9\u6a21\u578b</div>'; return; }}
      function trunc(s, n) {{ return s.length > n ? s.slice(0, n) + '\u2026' : s; }}
      var html = '<table style="border-collapse:separate;border-spacing:2px;font-size:12px;"><tbody>';
      selected.forEach(function(mid) {{
        html += '<tr><td style="padding:6px 10px;font-weight:500;color:rgba(0,0,0,0.65);white-space:nowrap;text-align:right;">' + anModelNames[mid] + '</td>';
        anLowLevels.forEach(function(ll) {{
          var cell = (anLLRates[mid] || {{}})[ll.id] || {{rate: 0.5, total: 0}};
          var bg = anRateColor(cell.rate);
          var textColor = cell.rate > 0.55 ? '#fff' : 'rgba(0,0,0,0.85)';
          var pct = Math.round(cell.rate * 100);
          var tt = anModelNames[mid] + ' \u00b7 ' + ll.zh + ': ' + cell.wins + 'W-' + cell.losses + 'L-' + cell.ties + 'T (' + cell.total + '\u573a)';
          html += '<td title="' + tt + '" style="background:' + bg + ';color:' + textColor + ';min-width:48px;height:32px;text-align:center;border-radius:4px;font-weight:500;">' + pct + '%</td>';
        }});
        html += '</tr>';
      }});
      // Bottom row: low-level labels hanging down
      html += '<tr><td></td>';
      anLowLevels.forEach(function(ll) {{
        html += '<td title="' + ll.hl + ' \u00b7 ' + ll.zh + '" style="padding:6px 4px;writing-mode:vertical-rl;white-space:nowrap;font-weight:500;color:rgba(0,0,0,0.65);vertical-align:top;height:120px;">' + trunc(ll.zh, 12) + '</td>';
      }});
      html += '</tr>';
      html += '</tbody></table>';
      box.innerHTML = html;
    }}

    function anApply() {{
      anUpdateChips();
      anRenderRadar();
      anRenderWeakness();
      anRenderTrend();
      anRenderMatrix();
      anRenderHeatmap();
    }}
    anApply();
    </script>
    '''
    return render_page("\u591a\u7ef4\u5206\u6790", content, active="analysis")


# ════════════════════════════════════════════════════════════════
# Section 6: Main
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n  Quanta 双盲评测平台 (Demo)")
    print("  ─────────────────────────")
    print("  http://localhost:5001\n")
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, port=port, host="0.0.0.0")
