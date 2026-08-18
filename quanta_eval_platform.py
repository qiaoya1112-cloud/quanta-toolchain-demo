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
import re
import uuid
import random
import html
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

# highlevel 维护场景示意图，lowlevel 继承所属 highlevel 的场景语境。
# Demo 中保存图片元数据和 data URL，便于直接预览交互。
PROMPT_SCENE_IMAGE_SEEDS = {
    "p1": [
        {"id": "si-p1-1", "name": "桌面初始状态.jpg", "role": "初始状态", "src": ""},
        {"id": "si-p1-2", "name": "目标摆放状态.jpg", "role": "目标状态", "src": ""},
    ],
    "p2": [
        {"id": "si-p2-1", "name": "桌面物体布置.jpg", "role": "初始状态", "src": ""},
        {"id": "si-p2-2", "name": "人手位置参考.jpg", "role": "关键步骤", "src": ""},
        {"id": "si-p2-3", "name": "整理完成效果.jpg", "role": "目标状态", "src": ""},
    ],
    "p4": [
        {"id": "si-p4-1", "name": "花盆与浇水壶初始位置.jpg", "role": "初始状态", "src": ""},
    ],
}
for _prompt in PROMPTS:
    _prompt["scene_images"] = PROMPT_SCENE_IMAGE_SEEDS.get(_prompt["id"], [])

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
        "tags": ["act_pick_place", "cap_precision_manipulation"],
        "creator": "Lance Li", "created_at": "2026-04-01",
    },
    {
        "id": "b2", "name": "\u5de5\u5177\u4f7f\u7528\u8bc4\u6d4b",
        "description": "\u8bc4\u6d4b\u6a21\u578b\u4f7f\u7528\u5de5\u5177\u5b8c\u6210\u4efb\u52a1\u7684\u80fd\u529b\uff0c\u5982\u6d47\u82b1\u3001\u64e6\u684c\u5b50\u7b49",
        "scene_id": "s2", "prompt_ids": ["p4", "p5"], "criteria_id": "c1",
        "tags": ["act_processing", "obj_tool"],
        "creator": "Lance Li", "created_at": "2026-04-03",
    },
    {
        "id": "b3", "name": "\u62bd\u5c49\u67dc\u4f53\u64cd\u4f5c\u8bc4\u6d4b",
        "description": "\u8bc4\u6d4b\u6a21\u578b\u5728\u5f00\u5173\u62bd\u5c49\u3001\u7269\u54c1\u642c\u79fb\u7b49\u590d\u6742\u64cd\u4f5c\u94fe\u4e0a\u7684\u80fd\u529b",
        "scene_id": "s3", "prompt_ids": ["p6"], "criteria_id": "c4",
        "tags": ["act_open_close", "cap_long_horizon"],
        "creator": "Rick Guo", "created_at": "2026-04-05",
    },
    {
        "id": "b4", "name": "\u7efc\u5408\u80fd\u529b\u8bc4\u6d4b v1",
        "description": "\u8986\u76d6\u6240\u6709\u573a\u666f\u7c7b\u578b\u7684\u7efc\u5408\u8bc4\u6d4b\u57fa\u51c6\uff0c\u7528\u4e8e RoboArena \u5bf9\u6807",
        "scene_id": "s1", "prompt_ids": ["p1", "p2", "p3", "p4", "p5", "p6"], "criteria_id": "c1",
        "tags": ["cap_reasoning", "cap_long_horizon"],
        "creator": "Lance Li", "created_at": "2026-04-08",
    },
]

for _benchmark in BENCHMARKS:
    _benchmark["publish_status"] = "已发布" if _benchmark.get("publish_status") in ("发布", "已发布") or (_benchmark.get("publish_status") is None and _benchmark.get("id") != "b4") else "未发布"

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

for _criterion in CRITERIA:
    _criterion["publish_status"] = "已发布" if _criterion.get("publish_status") in ("发布", "已发布") or (_criterion.get("publish_status") is None and _criterion.get("id") != "c4") else "未发布"
    _criterion.setdefault("result_definitions", {
        "成功": ["直接成功", "重试后成功"],
        "失败": ["执行超时", "动作失败", "环境异常"],
    })

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
        "ckpt_id": "7916",  # \u7528\u4e8e\u8840\u7f18\u5173\u8054
    },
    {
        "id": "t2", "task_no": 1002, "name": "Spirit v1.6 \u5168\u7248\u672c\u7efc\u5408\u8bc4\u6d4b",
        "benchmark_id": "b4", "eval_type": "preference",
        "model_ids": ["m1", "m2", "m3", "m4"],
        "status": "\u8bc4\u6d4b\u4e2d", "priority": "\u9ad8",
        "total_sessions": 60, "collect_done": 60, "eval_done": 42,
        "created_by": "Lance Li", "created_at": "2026-04-08",
        "ckpt_id": "7757",  # \u7528\u4e8e\u8840\u7f18\u5173\u8054
    },
    {
        "id": "t3", "task_no": 1003, "name": "Spirit v1.6-rc1 vs \u5916\u90e8\u57fa\u7ebf\u5bf9\u6807",
        "benchmark_id": "b3", "eval_type": "baseline",
        "model_ids": ["m4", "m5", "m6", "m7", "m8"],
        "status": "\u91c7\u96c6\u4e2d", "priority": "\u9ad8",
        "total_sessions": 80, "collect_done": 55, "eval_done": 0,
        "created_by": "Rick Guo", "created_at": "2026-04-10",
        "ckpt_id": "7560",  # \u7528\u4e8e\u8840\u7f18\u5173\u8054
    },
    {
        "id": "t4", "task_no": 1004, "name": "\u5de5\u5177\u4f7f\u7528\u573a\u666f\u4e13\u9879\u6d4b\u8bd5",
        "benchmark_id": "b2", "eval_type": "pass_fail",
        "model_ids": ["m3", "m4", "m5"],
        "status": "\u672a\u5f00\u59cb", "priority": "\u4e2d",
        "total_sessions": 30, "collect_done": 0, "eval_done": 0,
        "created_by": "Lance Li", "created_at": "2026-04-12",
        "ckpt_id": "7539",  # \u7528\u4e8e\u8840\u7f18\u5173\u8054
    },
    {
        "id": "t5", "task_no": 1005, "name": "Spirit v1.6-rc1 \u591a\u7ef4\u80fd\u529b\u91cf\u8868\u8bc4\u4f30",
        "benchmark_id": "b1", "eval_type": "scale",
        "model_ids": ["m3", "m4"],
        "status": "\u8bc4\u6d4b\u4e2d", "priority": "\u4f4e",
        "total_sessions": 40, "collect_done": 40, "eval_done": 18,
        "created_by": "Rick Guo", "created_at": "2026-04-14",
        "ckpt_id": "9001",  # \u7528\u4e8e\u8840\u7f18\u5173\u8054 (DEMO checkpoint)
    },
    # \u2500\u2500 DEMO \u6f14\u793a\u94fe\u8def\u8bc4\u6d4b\u4efb\u52a1 \u2500\u2500
    {
        "id": "t6", "task_no": 1006, "name": "\u767d\u677f\u6e05\u6d01\u57fa\u7840\u80fd\u529b\u8bc4\u6d4b_v5_checkpoint40k",
        "benchmark_id": "b1", "eval_type": "baseline",
        "model_ids": ["m3"],
        "status": "\u8bc4\u6d4b\u5b8c\u6210", "priority": "\u9ad8",
        "total_sessions": 20, "collect_done": 20, "eval_done": 20,
        "created_by": "joanna.qiao", "created_at": "2026-06-17",
        "ckpt_id": "9001",
    },
    {
        "id": "t7", "task_no": 1007, "name": "\u767d\u677f\u6e05\u6d01\u8fdb\u9636\u573a\u666f\u8bc4\u6d4b_v5_checkpoint40k",
        "benchmark_id": "b1", "eval_type": "baseline",
        "model_ids": ["m3"],
        "status": "\u8bc4\u6d4b\u5b8c\u6210", "priority": "\u9ad8",
        "total_sessions": 20, "collect_done": 20, "eval_done": 20,
        "created_by": "joanna.qiao", "created_at": "2026-06-17",
        "ckpt_id": "9001",
    },
    {
        "id": "t8", "task_no": 1008, "name": "\u767d\u677f\u6e05\u6d01\u57fa\u7840\u80fd\u529b\u8bc4\u6d4b_v5_checkpoint50k",
        "benchmark_id": "b1", "eval_type": "baseline",
        "model_ids": ["m3"],
        "status": "\u8bc4\u6d4b\u5b8c\u6210", "priority": "\u9ad8",
        "total_sessions": 20, "collect_done": 20, "eval_done": 20,
        "created_by": "joanna.qiao", "created_at": "2026-06-17",
        "ckpt_id": "9002",
    },
    {
        "id": "t9", "task_no": 1009, "name": "\u767d\u677f\u6e05\u6d01\u57fa\u7840\u80fd\u529b\u8bc4\u6d4b_v5ctrl_checkpoint45k",
        "benchmark_id": "b1", "eval_type": "baseline",
        "model_ids": ["m4"],
        "status": "\u8bc4\u6d4b\u5b8c\u6210", "priority": "\u9ad8",
        "total_sessions": 20, "collect_done": 20, "eval_done": 20,
        "created_by": "Lance Li", "created_at": "2026-06-18",
        "ckpt_id": "9003",
    },
    {
        "id": "t10", "task_no": 1010, "name": "\u684c\u9762\u6574\u7406\u7efc\u5408\u8bc4\u6d4b_joint_checkpoint35k",
        "benchmark_id": "b2", "eval_type": "baseline",
        "model_ids": ["m4"],
        "status": "\u8bc4\u6d4b\u5b8c\u6210", "priority": "\u4e2d",
        "total_sessions": 15, "collect_done": 15, "eval_done": 15,
        "created_by": "Lance Li", "created_at": "2026-06-19",
        "ckpt_id": "9004",
    },
    {
        "id": "t11", "task_no": 1011, "name": "\u684c\u9762\u6e05\u6d01\u57fa\u51c6\u8bc4\u6d4b_baseline_checkpoint30k",
        "benchmark_id": "b2", "eval_type": "baseline",
        "model_ids": ["m5"],
        "status": "\u8bc4\u6d4b\u5b8c\u6210", "priority": "\u4f4e",
        "total_sessions": 10, "collect_done": 10, "eval_done": 10,
        "created_by": "Min Chen", "created_at": "2026-06-20",
        "ckpt_id": "9005",
    },
]
# Backward compat: add completed_sessions alias
for _t in EVAL_TASKS:
    _t["publish_status"] = "已发布" if _t.get("publish_status") in ("发布", "已发布") or (_t.get("publish_status") is None and _t.get("id") != "t4") else "未发布"
    _t.setdefault("collect_done", 0)
    _t.setdefault("eval_done", 0)
    _benchmark = next((b for b in BENCHMARKS if b["id"] == _t.get("benchmark_id")), {})
    _t.setdefault("scene_id", _benchmark.get("scene_id", "s1"))
    _t.setdefault("criteria_id", _benchmark.get("criteria_id", "c2"))
    _t.setdefault("selected_prompt_ids", list(_benchmark.get("prompt_ids", [])))
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
.task-filter-bar .ff { flex:1 1 170px; min-width:170px; }
.task-filter-bar .ff input, .task-filter-bar .ff select { width:100%; min-width:0; }
.task-resource-label { display:flex !important; align-items:center; justify-content:space-between; gap:12px; width:100%; text-align:left; }
.task-resource-title { flex:1; min-width:0; text-align:left; }
.task-resource-actions { display:inline-flex; align-items:center; gap:16px; font-size:12px; font-weight:400; white-space:nowrap; }
.task-resource-link { display:inline-flex; align-items:center; gap:4px; color:#1F80A0; text-decoration:none; line-height:24px; }
.task-resource-link:hover { color:#176a88; text-decoration:underline; }
.task-resource-link.is-disabled { color:rgba(0,0,0,0.25); cursor:not-allowed; pointer-events:none; text-decoration:none; }
.task-resource-icon { font-size:13px; line-height:1; }
.er-dd-trigger.is-disabled { background:#f5f5f5; color:rgba(0,0,0,0.45); cursor:not-allowed; }
.task-view-mode .er-chip-x { pointer-events:none; opacity:0.45; }
.er-record-video-strip { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; min-width:0; }
.er-record-video { position:relative; min-width:0; height:86px; border:0; border-radius:7px; overflow:hidden; background:linear-gradient(145deg,#243447 0%,#101820 55%,#304352 100%); color:#fff; cursor:pointer; padding:0; display:flex; align-items:center; justify-content:center; }
.er-record-video::before { content:''; position:absolute; inset:18px 12px 10px; border:1px solid rgba(255,255,255,.22); border-radius:4px; background:linear-gradient(135deg,rgba(255,255,255,.10),transparent 50%),linear-gradient(25deg,transparent 50%,rgba(100,190,180,.24) 51%,rgba(100,190,180,.03) 78%); }
.er-record-video-play { position:relative; z-index:1; width:27px; height:27px; border-radius:50%; background:rgba(0,0,0,.48); display:flex; align-items:center; justify-content:center; font-size:11px; padding-left:2px; }
.er-record-video-label { position:absolute; left:7px; bottom:5px; z-index:1; font-size:10px; color:rgba(255,255,255,.82); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:calc(100% - 14px); }
.er-record-video:hover { box-shadow:0 0 0 2px rgba(31,128,160,.30); }
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
.action-more-wrap { position: relative; display: inline-block; }
.action-more-menu { display: none; position: absolute; right: 0; top: calc(100% + 4px); z-index: 50; min-width: 76px; padding: 4px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; box-shadow: 0 6px 18px rgba(0,0,0,.12); }
.action-more-wrap:hover .action-more-menu, .action-more-wrap:focus-within .action-more-menu { display: block; }
.action-more-menu .action-link { display: block; margin: 0; padding: 4px 8px; line-height: 22px; }

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
.benchmark-drawer-content { width:1000px; max-width:calc(100vw - 32px); }
.task-drawer-content { width:1000px; max-width:calc(100vw - 32px); }
.ant-drawer-content > form { display:flex; flex:1; flex-direction:column; min-height:0; }
.ant-drawer-content > form > .ant-drawer-body { flex:1; min-height:0; overflow-y:auto; }
.ant-drawer-content > form > .ant-drawer-footer { flex-shrink:0; }
.ant-drawer-mask.active .ant-drawer-content { transform: translateX(0); }
.ant-drawer-header { padding: 16px 24px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; }
.ant-drawer-header h3 { font-size: 16px; font-weight: 500; color: rgba(0,0,0,0.85); margin: 0; }
.ant-drawer-close { background: none; border: none; font-size: 16px; cursor: pointer; color: rgba(0,0,0,0.45); padding: 4px 8px; }
.ant-drawer-close:hover { color: rgba(0,0,0,0.85); }
.ant-drawer-body { padding: 24px; flex: 1; overflow-y: auto; }
.ant-drawer-footer { padding: 10px 24px; border-top: 1px solid #f0f0f0; display: flex; justify-content: flex-end; gap: 8px; flex-shrink:0; background:#fff; }

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
.benchmark-drawer-content .er-dd-panel { top:auto; bottom:calc(100% + 4px); z-index:1200; }
.er-opt { display:flex; align-items:center; gap:8px; padding:6px 14px; font-size:13px; cursor:pointer; color:rgba(0,0,0,0.85); }
.er-opt:hover { background:#fafafa; }
.er-opt input { accent-color:#1F80A0; }
.bm-prompt-execution-tree { margin-top:10px; border:1px solid #e5eaed; border-radius:8px; background:#fff; overflow:hidden; }
.bm-prompt-execution-head { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:9px 12px; border-bottom:1px solid #edf0f2; background:#f8fafb; }
.bm-prompt-execution-title { color:rgba(0,0,0,.72); font-size:13px; font-weight:500; }
.bm-prompt-execution-count { color:rgba(0,0,0,.42); font-size:12px; }
.bm-prompt-execution-actions { display:flex; align-items:center; gap:12px; margin-left:auto; }
.bm-prompt-execution-actions a { color:#1F80A0; font-size:12px; text-decoration:none; cursor:pointer; }
.bm-prompt-execution-actions a:hover { text-decoration:underline; }
.bm-prompt-execution-body { max-height:230px; overflow-y:auto; }
.bm-prompt-execution-group { border-bottom:1px solid #f3f4f5; }
.bm-prompt-execution-group:last-child { border-bottom:0; }
.bm-prompt-execution-group-head { display:flex; align-items:center; gap:8px; padding:9px 12px; color:rgba(0,0,0,.82); font-size:13px; font-weight:500; }
.bm-prompt-execution-group-head input, .bm-prompt-execution-child input { accent-color:#1F80A0; flex-shrink:0; }
.bm-prompt-execution-steps { padding:0 12px 8px 34px; border-top:1px solid #f7f7f7; }
.bm-prompt-execution-child { display:flex; align-items:flex-start; gap:8px; padding:7px 0; color:rgba(0,0,0,.68); font-size:12px; line-height:1.5; }
.bm-prompt-execution-child .bm-prompt-execution-en { display:block; color:rgba(0,0,0,.38); margin-top:1px; }
.bm-prompt-execution-empty { padding:18px 12px; color:rgba(0,0,0,.38); font-size:12px; text-align:center; }
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

/* ── End-side iPad simulation frame ── */
.eval2-ipad-shell { width:min(1400px, 100%); height:820px; margin:0 auto; border:1px solid #dfe5e9; border-radius:18px; background:#f7f8fa; box-shadow:0 10px 30px rgba(28,45,56,.08); overflow:hidden; box-sizing:border-box; }
.eval2-ipad-screen { width:100%; height:100%; overflow:auto; box-sizing:border-box; }
@media (max-height:900px) { .eval2-ipad-shell { height:calc(100vh - 96px); min-height:620px; } }
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
    <div class="nav-label">\u8bc4\u6d4b\u6267\u884c</div>
    <a href="/collect" class="nav-item {{ 'active' if active=='collect' }}"><span class="icon">&#9783;</span> \u8bc4\u6d4b\u6570\u636e\u91c7\u96c6</a>
    <a href="/evaluate2" class="nav-item {{ 'active' if active=='evaluate2' }}"><span class="icon">&#9878;</span> \u7aef\u4fa7\u793a\u610f</a>
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
  var trigger = document.getElementById(id + '-btn');
  if (trigger && trigger.classList.contains('is-disabled')) return;
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
  if (id === 'ms-ckpt' && typeof window.updateTaskResourceLinks === 'function') window.updateTaskResourceLinks();
  if (id === 'ms-bm-prompts' && typeof window.renderBenchmarkPromptExecutionTree === 'function') window.renderBenchmarkPromptExecutionTree();
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


def normalize_result_definitions(definitions):
    """Return ordered result types while accepting the legacy grouped structure."""
    rows = []
    if isinstance(definitions, list):
        source_rows = definitions
    elif isinstance(definitions, dict):
        source_rows = []
        for legacy_parent, values in definitions.items():
            values = values if isinstance(values, list) else [values]
            for value in values:
                if isinstance(value, dict):
                    source_rows.append({
                        "type": value.get("type") or value.get("name") or value.get("description") or legacy_parent,
                        "degree": value.get("degree"),
                    })
                else:
                    source_rows.append({"type": str(value or legacy_parent), "degree": None})
    else:
        source_rows = []

    for index, value in enumerate(source_rows, 1):
        if isinstance(value, dict):
            result_type = value.get("type") or value.get("name") or value.get("description") or ""
            degree = value.get("degree", index)
        else:
            result_type = str(value)
            degree = index
        result_type = str(result_type).strip()
        if not result_type:
            continue
        try:
            degree = int(degree)
        except (TypeError, ValueError):
            degree = index
        rows.append({"type": result_type[:20], "degree": degree})

    rows.sort(key=lambda item: item["degree"], reverse=True)
    total = len(rows)
    for index, item in enumerate(rows):
        item["degree"] = total - index
    return rows


def result_type_is_failure(value):
    """Keep legacy failure styling without imposing a fixed result taxonomy."""
    text = str(value or "")
    return any(marker in text for marker in ("失败", "异常", "超时", "未完成"))


ENDPOINT_MODES = (
    ("normal", "普通采集", "▣"),
    ("dagger", "DAgger 采集", "⌁"),
    ("assess", "模型评测", "▤"),
    ("eval", "对比评测", "⇄"),
    ("test", "测试任务", "☑"),
)


def endpoint_mode_buttons(css_class, selected_class, onclick):
    """Render the shared five-mode endpoint selector."""
    return "".join(
        f'<button type="button" class="{css_class}{" " + selected_class if index == 0 else ""}" '
        f'data-mode="{code}" onclick="{onclick}(this)"><b>{icon}</b>'
        f'<span class="endpoint-mode-copy"><strong>{label}</strong><small>{code}</small></span>'
        f'<i class="endpoint-mode-selected">✓</i></button>'
        for index, (code, label, icon) in enumerate(ENDPOINT_MODES)
    )


ENDPOINT_MODE_STYLE = '''<style>
  .wb-mode-grid,.eval2-mode-grid { display:flex;flex-direction:column;gap:10px;width:100%;max-width:860px;margin:24px auto; }
  .wb-mode,.eval2-mode { width:100%;min-height:68px;box-sizing:border-box;padding:0 18px;border:1px solid #dfe3e8;border-radius:8px;background:#fff;display:grid;grid-template-columns:42px minmax(0,1fr) 24px;align-items:center;gap:14px;color:#26323d;text-align:left;cursor:pointer;text-decoration:none;transition:border-color .15s,background .15s,box-shadow .15s; }
  .wb-mode:hover,.eval2-mode:hover { border-color:#8fc4d3;background:#f8fcfd; }
  .wb-mode.active,.eval2-mode.selected { border:2px solid #1F80A0;background:#eaf6f8;box-shadow:0 0 0 2px rgba(31,128,160,.08); }
  .wb-mode b,.eval2-mode b { display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:#e6f4f8;color:#1F80A0;font-size:21px;font-weight:500; }
  .endpoint-mode-copy { min-width:0;display:flex;align-items:baseline;gap:12px; }
  .endpoint-mode-copy strong { color:#26323d;font-size:16px;font-weight:600; }
  .endpoint-mode-copy small { color:#8a9099;font-size:13px;font-weight:500;text-transform:lowercase; }
  .endpoint-mode-selected { color:transparent;font-size:18px;font-style:normal;text-align:center; }
  .wb-mode.active .endpoint-mode-selected,.eval2-mode.selected .endpoint-mode-selected { color:#1F80A0; }
</style>'''


ENDPOINT_SETUP_MODE_SCRIPT = '''<script>
  function wbSelectSetupMode(button) {
    document.querySelectorAll('.wb-mode').forEach(function(item) { item.classList.remove('active'); });
    button.classList.add('active');
    var start = document.querySelector('.wb-step-page .wb-primary');
    if (start) start.href = '/evaluate2/setup?step=2&mode=' + encodeURIComponent(button.dataset.mode || 'normal');
  }
</script>'''


def get_criterion_metrics(criterion):
    """Return the current metric form rows, with a legacy form fallback."""
    metrics = criterion.get("metrics", []) or []
    if metrics:
        return metrics
    form = criterion.get("form", {}) or {}
    legacy_items = list(form.get("scale_module", {}).get("items", []) or [])
    for item in form.get("type_module", {}).get("items", []) or []:
        if item.get("metric_name"):
            legacy_items.append(item)
    return [
        {
            "name": item.get("metric_name") or item.get("prompt") or "",
            "description": item.get("description") or item.get("metric_description") or "",
            "type": "数字" if item.get("score_range") else "文本",
            "options": item.get("options", []) or [],
            "default_value": item.get("value") if item.get("value") is not None else "",
        }
        for item in legacy_items
        if item.get("metric_name") or item.get("prompt")
    ]

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
    tree_html = build_tree_selector_html("shared")
    filter_tree = build_tree_selector_html("filter")
    prompt_error = request.args.get("prompt_error", "").strip()
    creators_set = sorted(set(p["creator"] for p in PROMPTS))
    creator_options = "".join(f"<option>{c}</option>" for c in creators_set)

    difficulty_names = {1: "简单", 2: "较易", 3: "中等", 4: "较难", 5: "困难"}

    def difficulty_html(value):
        value = max(1, min(5, int(value or 3)))
        return f'<span class="prompt-difficulty">{value}（{difficulty_names[value]}）</span>'

    def prompt_action(href, label, style=""):
        style_class = f" {style}" if style else ""
        return f'<a class="prompt-action-link{style_class}" href="{href}" title="{label}" data-tip="{label}">{label}</a>'

    def scene_image_entry(prompt):
        images = prompt.get("scene_images", [])
        editable = not prompt.get("enabled", True)
        if not images:
            label = "添加场景图" if editable else "暂无场景图"
            if editable:
                return (
                    f'<a class="prompt-scene-add" href="javascript:;" '
                    f'onclick="openPromptSceneModal(\'{prompt["id"]}\')">{label}</a>'
                )
            return '<span class="prompt-scene-empty">—</span>'
        thumbs = "".join(
            '<span class="prompt-scene-thumb">'
            + (f'<img src="{html.escape(item.get("src", ""), quote=True)}" alt="">'
               if item.get("src") else '<span class="prompt-scene-placeholder">景</span>')
            + '</span>'
            for item in images[:3]
        )
        action = "维护" if editable else "查看"
        return (
            f'<button type="button" class="prompt-scene-entry" '
            f'onclick="openPromptSceneModal(\'{prompt["id"]}\')" '
            f'aria-label="{action}场景示意图，共{len(images)}张">'
            f'<span class="prompt-scene-thumbs">{thumbs}</span>'
            f'<span class="prompt-scene-count">{len(images)} 张</span>'
            '</button>'
        )

    scene_data_json = json.dumps(
        {
            p["id"]: {
                "id": p["id"],
                "name": p["high_level"],
                "editable": not p.get("enabled", True),
                "images": p.get("scene_images", []),
            }
            for p in PROMPTS
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")

    rows = ""
    for prompt_index, p in enumerate(PROMPTS):
        pid = p["id"]
        enabled = p.get("enabled", True)
        created_at = p.get("created_at", f"2026-07-{prompt_index + 1:02d} 10:00")
        agg_labels = prompt_aggregated_labels(p)
        labels_html = render_tags_html(agg_labels)
        labels_tip = _build_tip_text(agg_labels)
        if enabled:
            actions_html = prompt_action(f'/prompts/{pid}/copy', "复制", "prompt-action-muted")
        else:
            more_menu = (
                '<span class="prompt-more-wrap">'
                '<a class="prompt-action-link prompt-action-muted" href="javascript:;">更多</a>'
                '<span class="prompt-more-menu">'
                + prompt_action(f'/prompts/{pid}/copy', "复制", "prompt-action-muted")
                + prompt_action(f'/prompts/{pid}/delete', "删除", "prompt-action-danger")
                + '</span></span>'
            )
            actions_html = (
                f'<a class="prompt-action-link prompt-action-primary" href="javascript:;" onclick="showAddChild(\'{pid}\')" '
                f'title="增加下级" data-tip="增加下级">增加下级</a>'
                + prompt_action(f'/prompts/{pid}/toggle', "发布", "prompt-action-muted")
                + more_menu
            )

        rows += f'<tr class="row-parent prompt-parent-row" data-id="{pid}">'
        rows += f'<td class="prompt-tree-cell"><button class="expand-btn" data-target="sub-{pid}">&#9654;</button></td>'
        rows += td_tip(p["high_level"], 'style="font-weight:600;"')
        rows += td_tip(p["high_level_en"])
        rows += f'<td class="prompt-scene-cell">{scene_image_entry(p)}</td>'
        rows += f'<td class="prompt-id-cell">{html.escape(str(pid))}</td>'
        rows += '<td class="prompt-seq prompt-seq-parent prompt-seq-col">—</td>'
        rows += f'<td>{difficulty_html(p.get("difficulty", 3))}</td>'
        rows += td_tip(labels_html, tip_text=labels_tip)
        rows += f'<td><span class="prompt-status {"is-enabled" if enabled else "is-disabled"}">{"已发布" if enabled else "未发布"}</span></td>'
        rows += f'<td>{p["creator"]}</td>'
        rows += f'<td>{created_at}</td>'
        rows += f'<td class="actions-cell"><span class="prompt-action-group">{actions_html}</span></td>'
        rows += '</tr>'

        for index, ll in enumerate(p["low_levels"], start=1):
            child_actions = prompt_action(
                f'/prompts/{pid}/del-child/{ll["id"]}',
                "删除",
                "prompt-action-danger",
            )
            rows += (
                f'<tr class="sub-row sub-{pid} row-child prompt-child-row" '
                f'data-parent="{pid}" data-child-id="{ll["id"]}" draggable="true">'
            )
            rows += '<td class="prompt-drag-cell"><span class="prompt-drag-handle" title="拖拽调整顺序">&#8942;&#8942;</span></td>'
            rows += td_tip(ll["zh"])
            rows += td_tip(ll["en"])
            rows += '<td class="prompt-scene-cell"><span class="prompt-scene-inherited">继承上级</span></td>'
            child_id = str(ll.get("id") or f"{pid}-{index}")
            rows += f'<td class="prompt-id-cell">{html.escape(child_id)}</td>'
            rows += f'<td class="prompt-seq prompt-seq-col">{index}</td>'
            rows += f'<td>{difficulty_html(ll.get("difficulty", 3))}</td>'
            rows += td_tip(render_tags_html(ll.get("labels", [])), tip_text=_build_tip_text(ll.get("labels", [])))
            # 已发布/未发布只在 highlevel 父级生效，lowlevel 不展示状态。
            rows += '<td></td>'
            rows += f'<td>{p["creator"]}</td>'
            rows += f'<td>{created_at}</td>'
            rows += f'<td class="actions-cell">{child_actions}</td>'
            rows += '</tr>'

        child_tree = build_tree_selector_html(f"child-{pid}")
        next_child_id = f"{pid}-{len(p['low_levels']) + 1}"
        rows += f'''
        <tr class="row-child row-inline-child prompt-add-child-row" id="add-child-{pid}" data-parent="{pid}" style="display:none;">
          <td class="prompt-drag-cell"><span class="prompt-drag-placeholder"></span></td>
          <td><input type="text" form="form-child-{pid}" name="zh" placeholder="输入 Low level" {INLINE_INPUT}></td>
          <td><input type="text" form="form-child-{pid}" name="en" placeholder="输入 Task-Prompt" {INLINE_INPUT}></td>
          <td class="prompt-scene-cell"><span class="prompt-scene-inherited">继承上级</span></td>
          <td class="prompt-id-cell">{html.escape(next_child_id)}</td>
          <td class="prompt-seq prompt-seq-col">{len(p["low_levels"]) + 1}</td>
          <td>
            <div class="prompt-difficulty-stepper">
              <button type="button" onclick="stepPromptDifficulty(this,-1)">−</button>
              <input type="number" form="form-child-{pid}" name="difficulty" min="1" max="5" value="3" readonly>
              <button type="button" onclick="stepPromptDifficulty(this,1)">＋</button>
            </div>
          </td>
          <td></td>
          <td></td>
          <td>{p["creator"]}</td>
          <td>{created_at}</td>
          <td class="actions-cell prompt-save-actions">
            <button type="submit" form="form-child-{pid}" class="ant-btn ant-btn-sm ant-btn-primary">保存</button>
            <button type="button" class="ant-btn ant-btn-sm" onclick="hideAddChild('{pid}')">取消</button>
          </td>
        </tr>
        <form id="form-child-{pid}" method="POST" action="/prompts/{pid}/add-child" style="display:none;">
          <input type="hidden" name="labels" value="">
        </form>'''

    content = f'''
    {f'<div class="ant-alert ant-alert-error ant-alert-no-icon" style="margin-bottom:16px;"><div class="ant-alert-message">{html.escape(prompt_error)}</div></div>' if prompt_error else ''}
    <form id="inline-add" method="POST" action="/prompts/create" style="display:none;"></form>
    <div class="filter-bar fb-labeled prompt-filter-bar">
      <div class="ff"><label>任务提示词</label><input type="text" placeholder="搜索任务提示词"></div>
      <div class="ff"><label>Task-Prompt</label><input type="text" placeholder="搜索 Task-Prompt"></div>
      <div class="ff"><label>id</label><input type="text" placeholder="搜索 id"></div>
      <div class="ff"><label>标签</label>
        <div class="ts-wrap prompt-filter-select" id="ts-filter">
          <div class="ts-trigger" onclick="tsToggle('ts-filter')"><span class="ts-placeholder">选择标签</span></div>
          <div class="ts-panel">{filter_tree}</div>
          <input type="hidden" name="filter_tags" value="">
        </div>
      </div>
      <div class="ff"><label>创建人</label><select><option value="">请选择创建人</option>{creator_options}</select></div>
      <div class="filter-actions">
        <button class="ant-btn" type="button" onclick="clearFilters()">清空</button>
        <button class="ant-btn ant-btn-primary" type="button" onclick="doSearch()">搜索</button>
      </div>
      <div style="flex:1;"></div>
      <input id="prompt-json-file" type="file" accept="application/json,.json" hidden onchange="promptImportJson(this)">
      <button class="ant-btn" type="button" onclick="document.getElementById('prompt-json-file').click()">导入 JSON</button>
      <button class="ant-btn ant-btn-primary" type="button" onclick="showNewParent()">+ 新增任务提示词</button>
    </div>

    <div class="ant-card ant-card-bordered prompt-table-card">
      <div class="prompt-table-scroll">
      <table class="ant-table" id="prompt-table">
        <thead><tr>
          <th></th>
          <th>任务提示词</th>
          <th>Task-Prompt</th>
          <th>场景示意图</th>
          <th>id</th>
          <th class="prompt-seq-col">序号</th>
          <th>难度</th>
          <th>标签</th>
          <th>状态</th>
          <th>创建人</th>
          <th>创建时间</th>
          <th>操作</th>
        </tr></thead>
        <tbody>
          {rows}
          <tr class="row-new-parent" id="new-parent-row" style="display:none;">
            <td></td>
            <td><input type="text" form="inline-add" name="high_level" placeholder="输入任务提示词" {INLINE_INPUT}></td>
            <td><input type="text" form="inline-add" name="high_level_en" placeholder="输入 Task-Prompt" {INLINE_INPUT}></td>
            <td class="prompt-scene-cell"><span class="prompt-scene-after-save">保存后添加</span></td>
            <td><input type="text" form="inline-add" name="prompt_id" placeholder="输入 id" required {INLINE_INPUT}></td>
            <td class="prompt-seq prompt-seq-col">—</td>
            <td>
              <div class="prompt-difficulty-stepper">
                <button type="button" onclick="stepPromptDifficulty(this,-1)">−</button>
                <input type="number" form="inline-add" name="difficulty" min="1" max="5" value="3" readonly>
                <button type="button" onclick="stepPromptDifficulty(this,1)">＋</button>
              </div>
            </td>
            <td>
              <div class="ts-wrap" id="ts-new-parent">
                <div class="ts-trigger" onclick="tsToggle('ts-new-parent')"><span class="ts-placeholder">选择标签</span></div>
                <div class="ts-panel">{tree_html}</div>
                <input type="hidden" form="inline-add" name="parent_labels" value="">
              </div>
            </td>
            <td></td>
            <td class="prompt-muted">Joanna Qiao</td>
            <td class="prompt-muted">—</td>
            <td class="actions-cell prompt-save-actions">
              <a class="act-icon act-primary" href="javascript:;" onclick="addNewChildRow()" title="增加下级">{ICON_ADD_CHILD}</a>
              <button type="submit" form="inline-add" class="ant-btn ant-btn-sm ant-btn-primary">保存</button>
              <button type="button" class="ant-btn ant-btn-sm" onclick="cancelNewParent()">取消</button>
            </td>
          </tr>
          <tr id="new-children-anchor" style="display:none;"></tr>
        </tbody>
      </table>
      </div>
      <template id="tree-tpl">{tree_html}</template>
    </div>

    <div class="prompt-pagination">
      <select><option>10条/页</option><option>20条/页</option></select>
      <button disabled>&lsaquo;</button><button class="active">1</button><button>2</button><button>3</button><button>4</button><button>&rsaquo;</button>
      <input aria-label="跳转页码"><span>go</span>
    </div>

    <div class="prompt-scene-mask" id="prompt-scene-modal" aria-hidden="true">
      <section class="prompt-scene-modal" role="dialog" aria-modal="true" aria-labelledby="prompt-scene-title">
        <header class="prompt-scene-header">
          <div>
            <h3 id="prompt-scene-title">场景示意图</h3>
            <p id="prompt-scene-context"></p>
          </div>
          <button type="button" class="prompt-scene-close" onclick="closePromptSceneModal()" aria-label="关闭">&times;</button>
        </header>
        <div class="prompt-scene-body">
          <div class="prompt-scene-guidance">
            <span class="prompt-scene-guidance-icon">i</span>
            <span>场景图将展示在端侧的「任务信息」中，建议覆盖初始状态、目标状态和关键物体位置。</span>
          </div>
          <label class="prompt-scene-upload" id="prompt-scene-upload">
            <input id="prompt-scene-file" type="file" accept="image/*" multiple hidden onchange="addPromptSceneFiles(this.files)">
            <span class="prompt-scene-upload-icon">&#8682;</span>
            <strong>点击或拖拽上传场景图</strong>
            <small>支持 JPG、PNG、WebP，单张不超过 5MB，最多 3 张</small>
          </label>
          <div class="prompt-scene-toolbar">
            <strong id="prompt-scene-total">场景图（0/3）</strong>
          </div>
          <div class="prompt-scene-grid" id="prompt-scene-grid"></div>
          <div class="prompt-scene-empty-state" id="prompt-scene-empty">
            <span>图</span><strong>暂无场景图</strong><small>上传后可设置图片类型</small>
          </div>
        </div>
        <footer class="prompt-scene-footer">
          <button type="button" class="ant-btn" onclick="closePromptSceneModal()" id="prompt-scene-cancel">取消</button>
          <button type="button" class="ant-btn ant-btn-primary" onclick="savePromptSceneImages()" id="prompt-scene-save">保存</button>
        </footer>
      </section>
    </div>

    <style>
      .prompt-table-card {{ position:relative; z-index:1; border-radius:0; overflow:visible; }}
      .prompt-table-scroll {{ width:100%; overflow-x:auto; overflow-y:visible; }}
      .prompt-filter-bar {{ position:relative; z-index:30; overflow:visible; }}
      .prompt-filter-bar .ff, .prompt-filter-bar .ts-wrap {{ overflow:visible; }}
      .prompt-filter-bar .ts-panel {{ z-index:1200; }}
      .prompt-filter-bar .ff {{ flex:1 1 180px; min-width:180px; }}
      .prompt-filter-bar .ff input, .prompt-filter-bar .ff select {{ width:100%; min-width:0; }}
      .prompt-filter-bar .ff .prompt-filter-select {{ width:100%; min-width:0; }}
      #prompt-table {{ table-layout:fixed; min-width:1530px; }}
      #prompt-table th:nth-child(1) {{ width:42px; }}
      #prompt-table th:nth-child(2) {{ width:15%; }}
      #prompt-table th:nth-child(3) {{ width:18%; }}
      #prompt-table th:nth-child(4) {{ width:126px; }}
      #prompt-table th:nth-child(5), #prompt-table td:nth-child(5) {{ width:110px; }}
      #prompt-table th:nth-child(6), #prompt-table td:nth-child(6) {{ width:56px; }}
      #prompt-table th:nth-child(7) {{ width:112px; }}
      #prompt-table th:nth-child(8) {{ width:18%; }}
      #prompt-table th:nth-child(9) {{ width:86px; }}
      #prompt-table th:nth-child(10) {{ width:108px; }}
      #prompt-table th:nth-child(11) {{ width:145px; }}
      #prompt-table th:nth-child(12) {{ width:180px; }}
      #prompt-table td {{ text-overflow:ellipsis; white-space:nowrap; max-width:0; overflow:hidden; }}
      #prompt-table .actions-cell {{ overflow:visible; white-space:nowrap; }}
      .prompt-parent-row td {{ font-weight:500; background:#fff; }}
      .prompt-child-row td, .prompt-add-child-row td, .row-new-child td {{ background:#fff; font-size:13px; }}
      .prompt-child-row:hover td {{ background:#fafafa; }}
      .prompt-child-row.prompt-dragging td {{ opacity:.45; background:#e6f4f8; }}
      .prompt-child-row.prompt-drag-over td {{ border-top:2px solid #1F80A0; }}
      .prompt-drag-cell {{ text-align:center; overflow:visible !important; }}
      .prompt-drag-handle {{ display:inline-block; color:#1F80A0; font-size:15px; letter-spacing:-4px; cursor:grab; user-select:none; padding:6px 8px; }}
      .prompt-drag-handle:active {{ cursor:grabbing; }}
      .prompt-seq {{ text-align:center; color:rgba(0,0,0,.65); font-variant-numeric:tabular-nums; }}
      .prompt-seq-parent {{ color:rgba(0,0,0,.2); }}
      .prompt-id-cell {{ color:rgba(0,0,0,.58); font-family:SFMono-Regular,Menlo,Monaco,Consolas,monospace; font-size:12px; white-space:nowrap; }}
      .prompt-difficulty {{ color:#ad8b00; white-space:nowrap; }}
      .prompt-status {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:12px; line-height:1.5; white-space:nowrap; }}
      .prompt-status.is-enabled {{ color:#18794e; background:#e8f7ef; }}
      .prompt-status.is-disabled {{ color:#8a5a00; background:#fff4d6; }}
      .prompt-scene-cell {{ overflow:visible !important; }}
      .prompt-scene-entry {{ display:inline-flex; align-items:center; gap:7px; height:32px; padding:0; border:0; background:transparent; color:#1F80A0; cursor:pointer; }}
      .prompt-scene-entry:hover .prompt-scene-count {{ text-decoration:underline; }}
      .prompt-scene-thumbs {{ display:flex; align-items:center; padding-left:8px; }}
      .prompt-scene-thumb {{ width:28px; height:28px; margin-left:-8px; overflow:hidden; border:2px solid #fff; border-radius:6px; background:#e8f4f6; box-shadow:0 1px 4px rgba(25,96,116,.16); }}
      .prompt-scene-thumb img {{ width:100%; height:100%; object-fit:cover; display:block; }}
      .prompt-scene-placeholder {{ display:flex; width:100%; height:100%; align-items:center; justify-content:center; color:#1F80A0; background:linear-gradient(145deg,#d8eef2,#f5fbfc); font-size:12px; }}
      .prompt-scene-count {{ white-space:nowrap; font-size:12px; }}
      .prompt-scene-add {{ color:#1F80A0; font-size:12px; text-decoration:none; }}
      .prompt-scene-add:hover {{ text-decoration:underline; }}
      .prompt-scene-inherited, .prompt-scene-after-save, .prompt-scene-empty {{ color:rgba(0,0,0,.35); font-size:12px; white-space:nowrap; }}
      .prompt-difficulty-stepper {{ height:34px; display:inline-flex; align-items:center; border:1px solid #d9d9d9; border-radius:6px; overflow:hidden; background:#fff; }}
      .prompt-difficulty-stepper button {{ width:28px; height:32px; border:0; background:#fafafa; cursor:pointer; color:rgba(0,0,0,.55); }}
      .prompt-difficulty-stepper input {{ width:36px; height:32px; border:0; border-left:1px solid #f0f0f0; border-right:1px solid #f0f0f0; text-align:center; outline:0; appearance:textfield; }}
      .prompt-save-actions {{ display:table-cell; }}
      .prompt-action-group {{ display:inline-flex; align-items:center; gap:12px; white-space:nowrap; }}
      .prompt-action-link {{ display:inline-block; margin:0; color:#1f80a0; font-size:12px; line-height:24px; text-decoration:none; white-space:nowrap; cursor:pointer; }}
      .prompt-action-link:hover {{ color:#0b637b; text-decoration:underline; }}
      .prompt-action-primary {{ color:#1677ff; }}
      .prompt-action-muted {{ color:rgba(0,0,0,.62); }}
      .prompt-action-danger {{ color:#d4380d; }}
      .prompt-more-wrap {{ position:relative; display:inline-block; margin:0; }}
      .prompt-more-wrap > .prompt-action-link {{ margin-left:0; }}
      .prompt-more-menu {{ display:none; position:absolute; right:0; top:calc(100% + 4px); z-index:30; min-width:72px; padding:4px; border:1px solid #e5e7eb; border-radius:6px; background:#fff; box-shadow:0 6px 18px rgba(0,0,0,.12); }}
      .prompt-more-wrap:hover .prompt-more-menu {{ display:block; }}
      .prompt-more-menu .prompt-action-link {{ display:block; margin:0; padding:4px 8px; line-height:22px; }}
      .prompt-save-actions .ant-btn {{ margin-left:6px; }}
      .prompt-muted {{ color:rgba(0,0,0,.45); font-size:13px; }}
      .row-new-parent td, .row-new-child td, .prompt-add-child-row td {{ vertical-align:middle; white-space:normal !important; overflow:visible !important; }}
      .row-new-parent, .row-new-child, .prompt-add-child-row {{ position:relative; z-index:10; }}
      .row-new-parent .ts-wrap.open, .row-new-child .ts-wrap.open {{ z-index:1200; }}
      .row-new-parent .ts-panel, .row-new-child .ts-panel {{ z-index:1200; }}
      .row-new-parent td {{ border-top:2px solid #1F80A0; background:#f8fcfd; }}
      .row-new-child td:first-child, .prompt-add-child-row td:first-child {{ border-left:2px solid #1F80A0; }}
      .prompt-pagination {{ display:flex; justify-content:flex-end; align-items:center; gap:6px; margin-top:14px; }}
      .prompt-pagination select, .prompt-pagination button, .prompt-pagination input {{ height:32px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; color:rgba(0,0,0,.65); }}
      .prompt-pagination button {{ min-width:32px; cursor:pointer; }}
      .prompt-pagination button.active {{ color:#1F80A0; border-color:#1F80A0; }}
      .prompt-pagination input {{ width:48px; }}
      .prompt-pagination span {{ color:#1F80A0; font-size:13px; }}
      body.prompt-scene-modal-open {{ overflow:hidden; }}
      .prompt-scene-mask {{ display:none; position:fixed; inset:0; z-index:3000; align-items:center; justify-content:center; padding:24px; background:rgba(0,0,0,.42); }}
      .prompt-scene-mask.open {{ display:flex; }}
      .prompt-scene-modal {{ display:flex; flex-direction:column; width:min(860px,calc(100vw - 48px)); max-height:min(780px,calc(100vh - 48px)); overflow:hidden; border-radius:10px; background:#fff; box-shadow:0 18px 54px rgba(0,0,0,.22); }}
      .prompt-scene-header {{ display:flex; flex:0 0 auto; align-items:flex-start; justify-content:space-between; padding:20px 24px 16px; border-bottom:1px solid #f0f0f0; }}
      .prompt-scene-header h3 {{ margin:0; color:rgba(0,0,0,.88); font-size:18px; line-height:28px; }}
      .prompt-scene-header p {{ margin:3px 0 0; color:rgba(0,0,0,.45); font-size:13px; }}
      .prompt-scene-close {{ width:30px; height:30px; border:0; background:transparent; color:rgba(0,0,0,.45); font-size:24px; line-height:28px; cursor:pointer; }}
      .prompt-scene-body {{ flex:1 1 auto; overflow:auto; padding:20px 24px 24px; }}
      .prompt-scene-guidance {{ display:flex; align-items:flex-start; gap:10px; margin-bottom:16px; padding:10px 12px; border-radius:6px; color:#276677; background:#edf7f9; font-size:13px; line-height:20px; }}
      .prompt-scene-guidance-icon {{ display:inline-flex; flex:0 0 auto; align-items:center; justify-content:center; width:18px; height:18px; margin-top:1px; border-radius:50%; color:#fff; background:#1F80A0; font-size:12px; font-weight:700; }}
      .prompt-scene-upload {{ display:flex; min-height:116px; box-sizing:border-box; flex-direction:column; align-items:center; justify-content:center; gap:5px; border:1px dashed #86bccb; border-radius:8px; color:rgba(0,0,0,.65); background:#fbfefe; cursor:pointer; transition:.18s ease; }}
      .prompt-scene-upload:hover, .prompt-scene-upload.dragover {{ border-color:#1F80A0; background:#f1f9fa; }}
      .prompt-scene-upload-icon {{ color:#1F80A0; font-size:25px; line-height:24px; }}
      .prompt-scene-upload strong {{ font-size:14px; font-weight:500; }}
      .prompt-scene-upload small {{ color:rgba(0,0,0,.42); font-size:12px; }}
      .prompt-scene-toolbar {{ display:flex; align-items:center; justify-content:space-between; margin:20px 0 12px; }}
      .prompt-scene-toolbar strong {{ color:rgba(0,0,0,.78); font-size:14px; }}
      .prompt-scene-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
      .prompt-scene-card {{ position:relative; overflow:hidden; border:1px solid #e7e7e7; border-radius:8px; background:#fff; transition:.18s ease; }}
      .prompt-scene-preview {{ position:relative; height:118px; overflow:hidden; background:linear-gradient(145deg,#dbeef1,#f6fbfc); }}
      .prompt-scene-preview img {{ width:100%; height:100%; object-fit:cover; display:block; }}
      .prompt-scene-preview-fallback {{ display:flex; width:100%; height:100%; align-items:center; justify-content:center; color:#2c7d92; font-size:32px; }}
      .prompt-scene-card-body {{ padding:10px 12px 12px; }}
      .prompt-scene-name {{ overflow:hidden; margin-bottom:9px; color:rgba(0,0,0,.75); font-size:13px; font-weight:500; text-overflow:ellipsis; white-space:nowrap; }}
      .prompt-scene-role {{ width:100%; height:30px; padding:0 28px 0 9px; border:1px solid #d9d9d9; border-radius:6px; color:rgba(0,0,0,.68); background:#fff; font-size:12px; }}
      .prompt-scene-card-actions {{ display:flex; align-items:center; gap:12px; min-height:24px; margin-top:8px; }}
      .prompt-scene-card-actions button {{ padding:0; border:0; color:#1F80A0; background:transparent; font-size:12px; line-height:24px; cursor:pointer; }}
      .prompt-scene-card-actions button.danger {{ color:#d4380d; }}
      .prompt-scene-card-actions button:disabled {{ color:rgba(0,0,0,.25); cursor:not-allowed; }}
      .prompt-scene-empty-state {{ display:none; flex-direction:column; align-items:center; justify-content:center; min-height:190px; color:rgba(0,0,0,.32); }}
      .prompt-scene-empty-state span {{ display:flex; align-items:center; justify-content:center; width:48px; height:48px; margin-bottom:10px; border-radius:10px; background:#f1f5f6; font-size:20px; }}
      .prompt-scene-empty-state strong {{ color:rgba(0,0,0,.45); font-size:14px; font-weight:500; }}
      .prompt-scene-empty-state small {{ margin-top:4px; font-size:12px; }}
      .prompt-scene-footer {{ display:flex; flex:0 0 auto; justify-content:flex-end; gap:10px; padding:14px 24px; border-top:1px solid #f0f0f0; background:#fff; }}
      .prompt-scene-mask.readonly .prompt-scene-upload, .prompt-scene-mask.readonly #prompt-scene-save {{ display:none; }}
      @media (max-width:900px) {{ .prompt-scene-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
    </style>

    <script>
    let newChildCount = 0;
    let promptDraggedRow = null;
    const promptSceneData = {scene_data_json};
    const promptSceneRoles = ['初始状态','目标状态','关键步骤','其他'];
    let promptScenePid = '';
    let promptSceneDraft = [];

    function promptSceneCloneImages(images) {{
      return (images || []).map(image => ({{...image}}));
    }}
    function openPromptSceneModal(pid) {{
      const data = promptSceneData[pid];
      if (!data) return;
      promptScenePid = pid;
      promptSceneDraft = promptSceneCloneImages(data.images);
      const modal = document.getElementById('prompt-scene-modal');
      modal.classList.toggle('readonly', !data.editable);
      modal.classList.add('open');
      modal.setAttribute('aria-hidden','false');
      document.body.classList.add('prompt-scene-modal-open');
      document.getElementById('prompt-scene-title').textContent = data.editable ? '维护场景示意图' : '查看场景示意图';
      document.getElementById('prompt-scene-context').textContent = 'Highlevel：' + data.name + (data.editable ? '' : ' · 已发布，仅支持查看');
      document.getElementById('prompt-scene-cancel').textContent = data.editable ? '取消' : '关闭';
      renderPromptSceneImages();
    }}
    function closePromptSceneModal() {{
      const modal = document.getElementById('prompt-scene-modal');
      modal.classList.remove('open','readonly');
      modal.setAttribute('aria-hidden','true');
      document.body.classList.remove('prompt-scene-modal-open');
      promptScenePid = '';
      promptSceneDraft = [];
      document.getElementById('prompt-scene-file').value = '';
    }}
    function renderPromptSceneImages() {{
      const data = promptSceneData[promptScenePid] || {{editable:false}};
      const editable = !!data.editable;
      const grid = document.getElementById('prompt-scene-grid');
      const empty = document.getElementById('prompt-scene-empty');
      document.getElementById('prompt-scene-total').textContent = '场景图（' + promptSceneDraft.length + '/3）';
      grid.style.display = promptSceneDraft.length ? 'grid' : 'none';
      empty.style.display = promptSceneDraft.length ? 'none' : 'flex';
      grid.innerHTML = promptSceneDraft.map((image,index) => {{
        const roleOptions = promptSceneRoles.map(role => '<option value="'+role+'" '+(role === image.role ? 'selected' : '')+'>'+role+'</option>').join('');
        const preview = image.src
          ? '<img src="'+image.src+'" alt="'+escapePromptSceneText(image.name)+'">'
          : '<span class="prompt-scene-preview-fallback">景</span>';
        const actions = editable
          ? '<button type="button" class="danger" onclick="deletePromptSceneImage('+index+')">删除</button>'
          : '';
        return '<article class="prompt-scene-card" data-index="'+index+'">'
          + '<div class="prompt-scene-preview">'+preview+'</div>'
          + '<div class="prompt-scene-card-body"><div class="prompt-scene-name" title="'+escapePromptSceneText(image.name)+'">'+escapePromptSceneText(image.name)+'</div>'
          + '<select class="prompt-scene-role" onchange="setPromptSceneRole('+index+',this.value)" '+(editable ? '' : 'disabled')+'>'+roleOptions+'</select>'
          + '<div class="prompt-scene-card-actions">'+actions+'</div></div></article>';
      }}).join('');
    }}
    function escapePromptSceneText(text) {{
      const div = document.createElement('div');
      div.textContent = text || '';
      return div.innerHTML;
    }}
    function addPromptSceneFiles(files) {{
      const data = promptSceneData[promptScenePid];
      if (!data || !data.editable || !files || !files.length) return;
      const room = 3 - promptSceneDraft.length;
      if (room <= 0) {{ showToast('最多上传 3 张场景图','error'); return; }}
      const selected = Array.from(files).slice(0,room);
      let pending = selected.length;
      selected.forEach(file => {{
        if (!file.type.startsWith('image/')) {{ pending -= 1; return; }}
        if (file.size > 5 * 1024 * 1024) {{
          showToast(file.name + ' 超过 5MB，已跳过','error');
          pending -= 1;
          if (!pending) renderPromptSceneImages();
          return;
        }}
        const reader = new FileReader();
        reader.onload = event => {{
          promptSceneDraft.push({{
            id:'si-' + Date.now() + '-' + Math.random().toString(16).slice(2),
            name:file.name,
            role:'关键步骤',
            src:event.target.result
          }});
          pending -= 1;
          if (!pending) renderPromptSceneImages();
        }};
        reader.readAsDataURL(file);
      }});
      if (selected.length < files.length) showToast('最多保留 3 张场景图','error');
      document.getElementById('prompt-scene-file').value = '';
    }}
    function setPromptSceneRole(index,role) {{
      if (promptSceneDraft[index]) promptSceneDraft[index].role = role;
    }}
    function deletePromptSceneImage(index) {{
      promptSceneDraft.splice(index,1);
      renderPromptSceneImages();
    }}
    function savePromptSceneImages() {{
      const data = promptSceneData[promptScenePid];
      if (!data || !data.editable) return;
      const pid = promptScenePid;
      fetch('/prompts/' + pid + '/scene-images', {{
        method:'POST',
        headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{images:promptSceneDraft}})
      }}).then(async response => {{
        const result = await response.json();
        if (!response.ok) throw new Error(result.message || '保存失败');
        showToast('场景示意图已保存','success');
        window.setTimeout(() => window.location.href = window.location.pathname, 250);
      }}).catch(error => showToast(error.message || '保存失败，请重试','error'));
    }}

    function promptImportJson(input) {{
      if (!input.files || !input.files.length) return;
      showToast('已选择 ' + input.files[0].name + '，JSON 导入完成', 'success');
      input.value = '';
    }}
    function showNewParent() {{
      const row = document.getElementById('new-parent-row');
      row.style.display = 'table-row';
      if (newChildCount === 0) addNewChildRow();
      row.scrollIntoView({{behavior:'smooth', block:'center'}});
      row.querySelector('input[name="prompt_id"]').focus();
    }}
    function cancelNewParent() {{
      document.getElementById('new-parent-row').style.display = 'none';
      document.querySelectorAll('.row-new-child').forEach(r => r.remove());
      newChildCount = 0;
    }}
    function addNewChildRow() {{
      const idx = newChildCount++;
      const tsId = 'ts-newchild-' + idx;
      const anchor = document.getElementById('new-children-anchor');
      const tr = document.createElement('tr');
      tr.className = 'row-new-child';
      tr.innerHTML = `
        <td class="prompt-drag-cell"><span class="prompt-drag-placeholder"></span></td>
        <td><input type="text" form="inline-add" name="child_zh_${{idx}}" placeholder="输入任务提示词" {INLINE_INPUT}></td>
        <td><input type="text" form="inline-add" name="child_en_${{idx}}" placeholder="输入 Task-Prompt" {INLINE_INPUT}></td>
        <td class="prompt-scene-cell"><span class="prompt-scene-inherited">继承上级</span></td>
        <td class="prompt-id-cell">保存后生成</td>
        <td class="prompt-seq prompt-seq-col">${{idx + 1}}</td>
        <td><div class="prompt-difficulty-stepper"><button type="button" onclick="stepPromptDifficulty(this,-1)">−</button><input type="number" form="inline-add" name="child_difficulty_${{idx}}" min="1" max="5" value="3" readonly><button type="button" onclick="stepPromptDifficulty(this,1)">＋</button></div></td>
        <td>
          <div class="ts-wrap" id="${{tsId}}">
            <div class="ts-trigger" onclick="tsToggle('${{tsId}}')"><span class="ts-placeholder">选择标签</span></div>
            <div class="ts-panel">${{document.getElementById('tree-tpl').innerHTML}}</div>
            <input type="hidden" form="inline-add" name="child_labels_${{idx}}" value="">
          </div>
        </td>
        <td></td>
        <td class="prompt-muted">Joanna Qiao</td>
        <td class="prompt-muted">—</td>
        <td class="actions-cell"><button type="button" class="ant-btn ant-btn-sm" onclick="this.closest('tr').remove()">删除</button></td>`;
      anchor.parentNode.insertBefore(tr, anchor);
      tsInit(document.getElementById(tsId));
      let h = document.getElementById('inline-child-count');
      if (!h) {{
        h = document.createElement('input');
        h.type = 'hidden'; h.id = 'inline-child-count'; h.name = 'child_count';
        document.getElementById('inline-add').appendChild(h);
      }}
      h.value = newChildCount;
    }}
    function showAddChild(pid) {{
      const btn = document.querySelector('tr[data-id="'+pid+'"] .expand-btn');
      if (btn && !btn.classList.contains('expanded')) btn.click();
      const row = document.getElementById('add-child-' + pid);
      if (!row) return;
      row.style.display = 'table-row';
      row.scrollIntoView({{behavior:'smooth', block:'nearest'}});
      row.querySelector('input[name="zh"]').focus();
    }}
    function hideAddChild(pid) {{
      const row = document.getElementById('add-child-' + pid);
      if (row) row.style.display = 'none';
    }}
    function stepPromptDifficulty(btn, delta) {{
      const input = btn.parentElement.querySelector('input');
      input.value = Math.max(1, Math.min(5, Number(input.value || 3) + delta));
    }}
    function updatePromptSequence(pid) {{
      document.querySelectorAll('.prompt-child-row[data-parent="'+pid+'"]').forEach((row, idx) => {{
        row.querySelector('.prompt-seq').textContent = idx + 1;
      }});
      const addRow = document.getElementById('add-child-' + pid);
      if (addRow) addRow.querySelector('.prompt-seq').textContent =
        document.querySelectorAll('.prompt-child-row[data-parent="'+pid+'"]').length + 1;
    }}
    function persistPromptOrder(pid) {{
      const order = Array.from(document.querySelectorAll('.prompt-child-row[data-parent="'+pid+'"]')).map(row => row.dataset.childId);
      fetch('/prompts/' + pid + '/reorder-children', {{
        method:'POST',
        headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{order:order}})
      }}).then(response => {{
        if (!response.ok) throw new Error('save failed');
        showToast('顺序已保存，序号已自动更新', 'success');
      }}).catch(() => showToast('顺序保存失败，请重试', 'error'));
    }}
    function initPromptDrag() {{
      document.querySelectorAll('.prompt-child-row').forEach(row => {{
        row.addEventListener('dragstart', event => {{
          if (!event.target.closest('.prompt-drag-handle')) {{ event.preventDefault(); return; }}
          promptDraggedRow = row;
          row.classList.add('prompt-dragging');
          event.dataTransfer.effectAllowed = 'move';
        }});
        row.addEventListener('dragover', event => {{
          if (!promptDraggedRow || promptDraggedRow.dataset.parent !== row.dataset.parent) return;
          event.preventDefault();
          row.classList.add('prompt-drag-over');
          const rect = row.getBoundingClientRect();
          const tbody = row.parentElement;
          if (event.clientY < rect.top + rect.height / 2) tbody.insertBefore(promptDraggedRow, row);
          else tbody.insertBefore(promptDraggedRow, row.nextSibling);
        }});
        row.addEventListener('dragleave', () => row.classList.remove('prompt-drag-over'));
        row.addEventListener('drop', event => event.preventDefault());
        row.addEventListener('dragend', () => {{
          const pid = row.dataset.parent;
          document.querySelectorAll('.prompt-child-row').forEach(r => r.classList.remove('prompt-dragging','prompt-drag-over'));
          promptDraggedRow = null;
          updatePromptSequence(pid);
          persistPromptOrder(pid);
        }});
      }});
    }}

    function tsToggle(wrapId) {{
      const w = document.getElementById(wrapId);
      if (w) w.classList.toggle('open');
    }}
    document.addEventListener('click', function(e) {{
      document.querySelectorAll('.ts-wrap.open').forEach(w => {{
        if (!w.contains(e.target)) w.classList.remove('open');
      }});
    }});
    function tsInit(wrap) {{
      if (!wrap || wrap.dataset.tsInit) return;
      wrap.dataset.tsInit = '1';
      wrap.querySelectorAll('.ts-arrow:not(.empty)').forEach(arrow => {{
        arrow.addEventListener('click', function(e) {{
          e.stopPropagation();
          this.classList.toggle('expanded');
          const children = this.closest('.ts-node').querySelector('.ts-children');
          if (children) children.classList.toggle('expanded');
        }});
      }});
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
        ids.push(row.dataset.id);
        chips += '<span class="ts-chip"><span class="ts-chip-text">' + row.dataset.path + '</span><span class="ts-chip-close" data-rid="'+row.dataset.id+'" onclick="event.stopPropagation();tsRemove(this)">&times;</span></span>';
      }});
      trigger.innerHTML = chips || '<span class="ts-placeholder">选择标签</span>';
      if (hidden) hidden.value = ids.join(',');
    }}
    function tsRemove(closeBtn) {{
      const wrap = closeBtn.closest('.ts-wrap');
      const row = wrap.querySelector('.ts-row[data-id="'+closeBtn.dataset.rid+'"]');
      if (row) row.classList.remove('selected');
      tsSync(wrap);
    }}
    document.querySelectorAll('.ts-wrap').forEach(w => tsInit(w));
    initPromptDrag();
    const promptSceneUpload = document.getElementById('prompt-scene-upload');
    ['dragenter','dragover'].forEach(type => promptSceneUpload.addEventListener(type,event => {{
      event.preventDefault(); promptSceneUpload.classList.add('dragover');
    }}));
    ['dragleave','drop'].forEach(type => promptSceneUpload.addEventListener(type,event => {{
      event.preventDefault(); promptSceneUpload.classList.remove('dragover');
    }}));
    promptSceneUpload.addEventListener('drop',event => addPromptSceneFiles(event.dataTransfer.files));
    document.getElementById('prompt-scene-modal').addEventListener('click',event => {{
      if (event.target.id === 'prompt-scene-modal') closePromptSceneModal();
    }});
    document.addEventListener('keydown',event => {{
      if (event.key === 'Escape' && document.getElementById('prompt-scene-modal').classList.contains('open')) closePromptSceneModal();
    }});
    const promptSceneOpenPid = new URLSearchParams(window.location.search).get('scene_pid');
    if (promptSceneOpenPid && promptSceneData[promptSceneOpenPid]) openPromptSceneModal(promptSceneOpenPid);
    </script>
    '''
    return render_page("任务提示词", content, active="prompts")


@app.route("/prompts/create", methods=["POST"])
def prompts_create():
    hl = request.form.get("high_level", "").strip()
    hl_en = request.form.get("high_level_en", "").strip()
    prompt_id = request.form.get("prompt_id", "").strip()
    difficulty = max(1, min(5, request.form.get("difficulty", 3, type=int)))
    parent_labels = [l.strip() for l in request.form.get("parent_labels", "").split(",") if l.strip()]
    if not hl:
        flash("\u4efb\u52a1\u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a", "error")
        return redirect(url_for("prompts_page"))
    if not prompt_id:
        return redirect(url_for("prompts_page", prompt_error="请输入任务提示词 id"))

    # highlevel 与 lowlevel 共用同一套 id 命名空间，避免后续按 id 定位
    # 场景图、任务提示词或评测数据时出现歧义。
    all_prompt_ids = {
        str(item.get("id", "")).strip()
        for item in PROMPTS
        if str(item.get("id", "")).strip()
    }
    all_prompt_ids.update(
        str(child.get("id", "")).strip()
        for item in PROMPTS
        for child in item.get("low_levels", [])
        if str(child.get("id", "")).strip()
    )
    if prompt_id in all_prompt_ids:
        return redirect(url_for("prompts_page", prompt_error=f"任务提示词 id「{prompt_id}」已存在，请更换"))

    new_id = prompt_id
    # Collect children
    child_count = int(request.form.get("child_count", 0))
    low_levels = []
    generated_child_ids = set(all_prompt_ids)
    generated_child_ids.add(new_id)
    for i in range(child_count):
        zh = request.form.get(f"child_zh_{i}", "").strip()
        en = request.form.get(f"child_en_{i}", "").strip()
        child_difficulty = max(
            1,
            min(5, request.form.get(f"child_difficulty_{i}", 3, type=int)),
        )
        cl = [l.strip() for l in request.form.get(f"child_labels_{i}", "").split(",") if l.strip()]
        if zh:
            child_number = len(low_levels) + 1
            child_id = f"{new_id}-{child_number}"
            while child_id in generated_child_ids:
                child_number += 1
                child_id = f"{new_id}-{child_number}"
            generated_child_ids.add(child_id)
            low_levels.append({
                "id": child_id,
                "zh": zh,
                "en": en,
                "difficulty": child_difficulty,
                "labels": cl or parent_labels,
            })
    PROMPTS.append({
        "id": new_id,
        "high_level": hl,
        "high_level_en": hl_en,
        "difficulty": difficulty,
        "enabled": False,
        "creator": "Joanna Qiao",
        "scene_images": [],
        "low_levels": low_levels,
    })
    flash(f"\u63d0\u793a\u8bcd\u300c{hl}\u300d\u521b\u5efa\u6210\u529f\uff0c\u8bf7\u7ee7\u7eed\u7ef4\u62a4\u573a\u666f\u793a\u610f\u56fe", "success")
    return redirect(url_for("prompts_page", scene_pid=new_id))


@app.route("/prompts/<pid>/scene-images", methods=["POST"])
def prompt_scene_images_save(pid):
    prompt = next((item for item in PROMPTS if item["id"] == pid), None)
    if not prompt:
        return jsonify({"ok": False, "message": "Highlevel 不存在"}), 404
    if prompt.get("enabled", True):
        return jsonify({"ok": False, "message": "已发布的 Highlevel 不可修改场景图"}), 403

    payload = request.get_json(silent=True) or {}
    raw_images = payload.get("images")
    if not isinstance(raw_images, list):
        return jsonify({"ok": False, "message": "场景图数据格式错误"}), 400

    allowed_roles = {"初始状态", "目标状态", "关键步骤", "其他"}
    images = []
    for index, raw in enumerate(raw_images[:3]):
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name", "")).strip()[:120]
        if not name:
            continue
        role = str(raw.get("role", "关键步骤"))
        if role not in allowed_roles:
            role = "关键步骤"
        src = str(raw.get("src", ""))
        if src and not src.startswith("data:image/"):
            src = ""
        images.append({
            "id": str(raw.get("id") or f"si-{pid}-{index + 1}"),
            "name": name,
            "role": role,
            "src": src,
        })

    prompt["scene_images"] = images
    return jsonify({"ok": True, "count": len(images), "images": images})


@app.route("/prompts/<pid>/add-child", methods=["POST"])
def prompt_add_child_post(pid):
    p = next((p for p in PROMPTS if p["id"] == pid), None)
    if not p:
        flash("\u63d0\u793a\u8bcd\u4e0d\u5b58\u5728", "error")
        return redirect(url_for("prompts_page"))
    zh = request.form.get("zh", "").strip()
    en = request.form.get("en", "").strip()
    difficulty = max(1, min(5, request.form.get("difficulty", 3, type=int)))
    labels = [l.strip() for l in request.form.get("labels", "").split(",") if l.strip()]
    if zh:
        used_ids = {
            str(item.get("id", "")).strip()
            for item in PROMPTS
            if str(item.get("id", "")).strip()
        }
        used_ids.update(
            str(child.get("id", "")).strip()
            for item in PROMPTS
            for child in item.get("low_levels", [])
            if str(child.get("id", "")).strip()
        )
        child_number = len(p["low_levels"]) + 1
        child_id = f"{pid}-{child_number}"
        while child_id in used_ids:
            child_number += 1
            child_id = f"{pid}-{child_number}"
        p["low_levels"].append({
            "id": child_id,
            "zh": zh,
            "en": en,
            "difficulty": difficulty,
            "labels": labels,
        })
        flash(f"\u5b50\u7ea7\u300c{zh}\u300d\u6dfb\u52a0\u6210\u529f", "success")
    return redirect(url_for("prompts_page"))


@app.route("/prompts/<pid>/reorder-children", methods=["POST"])
def prompt_reorder_children(pid):
    p = next((item for item in PROMPTS if item["id"] == pid), None)
    if not p:
        return jsonify({"ok": False, "message": "提示词不存在"}), 404

    payload = request.get_json(silent=True) or {}
    order = payload.get("order") or []
    child_by_id = {child["id"]: child for child in p["low_levels"]}
    ordered = [child_by_id[cid] for cid in order if cid in child_by_id]
    ordered_ids = {child["id"] for child in ordered}
    ordered.extend(
        child for child in p["low_levels"] if child["id"] not in ordered_ids
    )
    p["low_levels"] = ordered
    return jsonify({"ok": True, "order": [child["id"] for child in ordered]})


@app.route("/prompts/<pid>/toggle")
def prompt_toggle(pid):
    p = next((p for p in PROMPTS if p["id"] == pid), None)
    if p:
        p["enabled"] = not p.get("enabled", False)
        state = "发布" if p["enabled"] else "取消发布"
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
            flash("已发布的提示词不可删除", "error")
        else:
            PROMPTS = [x for x in PROMPTS if x["id"] != pid]
            flash(f"\u300c{p['high_level']}\u300d\u5df2\u5220\u9664", "success")
    return redirect(url_for("prompts_page"))


@app.route("/prompts/<pid>/del-child/<cid>")
def prompt_del_child(pid, cid):
    p = next((p for p in PROMPTS if p["id"] == pid), None)
    if p:
        if p.get("enabled"):
            flash("发布状态不可删除子级", "error")
        else:
            p["low_levels"] = [ll for ll in p["low_levels"] if ll.get("id") != cid]
            flash("\u5b50\u7ea7\u63d0\u793a\u8bcd\u5df2\u5220\u9664", "success")
    return redirect(url_for("prompts_page"))


# ── Tag Management ──
@app.route("/tags")
def tags_page():
    base_dims = TAXONOMY["dimensions"]
    extra_dims = [
        {
            "id": "quality", "name": "质量标签", "name_en": "Quality Tags", "color": "red",
            "tags": [
                {"id": "q_collection", "name": "采集质量", "name_en": "Collection Quality",
                 "description": "记录采集阶段的数据有效性和异常类型",
                 "sub_tags": [{"id": "q_success", "name": "成功"}, {"id": "q_failed", "name": "失败"}, {"id": "q_operator_error", "name": "操作失误"}]},
                {"id": "q_upload", "name": "上传状态", "name_en": "Upload Status",
                 "description": "记录数据上传链路状态",
                 "sub_tags": [{"id": "q_not_uploaded", "name": "未上传"}, {"id": "q_uploading", "name": "上传中"}, {"id": "q_uploaded", "name": "上传成功"}, {"id": "q_upload_failed", "name": "上传失败"}]},
                {"id": "q_review", "name": "质检结论", "name_en": "QA Result",
                 "description": "人工或自动质检结果",
                 "sub_tags": [{"id": "q_passed", "name": "合格"}, {"id": "q_rejected", "name": "不合格"}, {"id": "q_need_review", "name": "需复核"}]},
            ],
        },
        {
            "id": "process", "name": "处理标签", "name_en": "Process Tags", "color": "purple",
            "tags": [
                {"id": "proc_stage", "name": "处理环节", "name_en": "Process Stage",
                 "description": "标识数据当前处理节点",
                 "sub_tags": [{"id": "proc_cleaning", "name": "清洗"}, {"id": "proc_qa", "name": "质检"}, {"id": "proc_annotation", "name": "标注"}, {"id": "proc_acceptance", "name": "验收"}]},
                {"id": "proc_annotation_status", "name": "标注状态", "name_en": "Annotation Status",
                 "description": "标注任务执行状态",
                 "sub_tags": [{"id": "proc_unlabeled", "name": "未标注"}, {"id": "proc_labeling", "name": "标注中"}, {"id": "proc_labeled", "name": "已标注"}]},
            ],
        },
        {
            "id": "project_delivery", "name": "项目交付标签", "name_en": "Project Delivery Tags", "color": "cyan",
            "tags": [
                {"id": "project_type", "name": "项目类型", "name_en": "Project Type",
                 "description": "区分数据归属项目和训练用途",
                 "sub_tags": [{"id": "project_pretrain", "name": "预训练"}, {"id": "project_posttrain", "name": "后训练"}, {"id": "project_demo", "name": "demo 项目"}, {"id": "project_ningde", "name": "宁德项目"}]},
                {"id": "delivery_status", "name": "交付状态", "name_en": "Delivery Status",
                 "description": "面向项目交付和验收的状态标签",
                 "sub_tags": [{"id": "delivery_pending", "name": "待验收"}, {"id": "delivery_accepted", "name": "验收通过"}, {"id": "delivery_rejected", "name": "验收退回"}]},
                {"id": "supplier_scope", "name": "供应商范围", "name_en": "Supplier Scope",
                 "description": "标识数据来源团队与供应商归属",
                 "sub_tags": [{"id": "supplier_internal", "name": "平台自有"}, {"id": "supplier_guanglun", "name": "光轮智能"}, {"id": "supplier_a", "name": "供应商 A"}]},
            ],
        },
    ]
    dim_by_id = {dim["id"]: dim for dim in base_dims + extra_dims}
    current_user = "joanna.qiao"
    tag_groups = [
        {
            "id": "platform_standard_taxonomy", "name": "平台通用标签体系",
            "desc": "由平台统一维护的标准标签体系，覆盖能力、动作、物体等基础语义，用于数据标注、检索、训练与评测",
            "owners": ["joanna.qiao", "Lance Li"], "enabled": True,
            "reference_count": 12, "dims": ["capability", "action", "object"],
        },
        {
            "id": "quality_tag_group", "name": "质量处理标签组",
            "desc": "用于采集结论、质检结论和处理状态",
            "owners": ["tao.wang", "包媛桐"], "enabled": True,
            "reference_count": 8, "dims": ["quality", "process"],
        },
        {
            "id": "delivery_tag_group", "name": "项目交付标签组",
            "desc": "用于项目、供应商和交付验收管理",
            "owners": ["Lance Li", "Joanna Qiao"], "enabled": False,
            "reference_count": 0, "dims": ["project_delivery"],
        },
        {
            "id": "custom_tag", "name": "自定义标签",
            "desc": "历史标签迁移",
            "owners": ["Alan Li", "Dream", "Raleigh", "Oasis", "Joanna"],
            "enabled": True, "reference_count": 0, "dims": [],
        },
    ]

    def group_dims(group):
        return [dim_by_id[dim_id] for dim_id in group["dims"] if dim_id in dim_by_id]

    def group_stats(dims):
        return (
            len(dims),
            sum(len(d["tags"]) for d in dims),
            sum(sum(len(t.get("sub_tags", [])) for t in d["tags"]) for d in dims),
        )

    group_payload = []
    for group in tag_groups:
        dims = group_dims(group)
        total_dims, total_l2, total_l3 = group_stats(dims)
        group_payload.append({
            **group,
            "dims_data": dims,
            "total_dims": total_dims,
            "total_l2": total_l2,
            "total_l3": total_l3,
            "total_rows": total_dims + total_l2 + total_l3,
        })

    active_group = group_payload[0]

    # Flatten taxonomy into tree rows (supports unlimited depth)
    rows_html = ""

    def build_rows_for_group(group, is_active):
        all_rows = []
        counter = {"n": 0}

        def walk(node, level, parent_chain, is_dim=False):
            raw_id = node.get("id") or f"_n{counter['n']}"
            nid = f"{group['id']}-{raw_id}"
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
            for child in children:
                walk(child, level + 1, parent_chain + [nid], False)

        for dim in group["dims_data"]:
            walk(dim, 0, [], is_dim=True)

        name_en_fallbacks = {
            "act_pick": "pick up", "act_place": "place", "act_put_in": "put in",
            "act_take_out": "take out", "act_stack": "stack", "act_throw": "throw",
            "act_push": "push", "act_pull": "pull", "act_rotate": "rotate",
            "act_flip": "flip", "act_drag": "drag", "act_swap": "swap",
            "act_open": "open", "act_close": "close", "act_twist_open": "twist open",
            "act_pull_open": "pull open", "act_push_open": "push open",
            "act_lift_open": "lift open", "act_fold": "fold", "act_unfold": "unfold",
            "act_assemble": "assemble", "act_disassemble": "disassemble",
            "act_stick": "attach", "act_peel_off": "peel off",
        }
        group_rows_html = ""
        for row_index, r in enumerate(all_rows):
            indent_px = r["level"] * 18
            if r["has_children"]:
                caret = f'<span class="tree-caret" onclick="event.stopPropagation();tagToggle(\'{r["id"]}\')">\u25be</span>'
            else:
                caret = '<span class="tree-caret empty"></span>'

            parent_attr = ",".join(r["parent_chain"])
            raw_id = r["id"].split("-", 1)[-1]
            name_en = r["name_en"] or name_en_fallbacks.get(raw_id, raw_id.replace("_", " "))
            level_number = r["level"] + 1
            checkbox = (
                '<span class="tag-row-check-placeholder"></span>'
                if r["level"] == 0
                else '<input class="tag-row-check" type="checkbox" aria-label="选择标签">'
            )
            created_at = f'2026-07-{18 + (row_index % 9):02d} {9 + (row_index % 8):02d}:{(row_index * 7) % 60:02d}'
            creator_id = group.get("owners", [current_user])[0]
            edit_btn = ''
            add_btn = '<a href="#" class="action-link">新增子标签</a>'
            detail_btn = ''
            del_btn = ''
            display_style = "" if is_active else "display:none;"

            group_rows_html += (
                f'<tr data-group="{group["id"]}" data-id="{r["id"]}" data-parent="{parent_attr}" data-level="{r["level"]}" style="{display_style}">'
                f'<td class="tag-name-cell" style="padding-left:{12 + indent_px}px;">'
                f'<span class="tag-drag-handle" title="拖动排序">&#8942;&#8942;</span>{checkbox}{caret}'
                f'<span class="tag-row-name {"is-root" if r["level"] == 0 else ""}">{r["name"]}</span></td>'
                f'<td><span class="tag-level-badge level-{min(level_number, 3)}">{level_number}</span></td>'
                f'<td class="tag-row-english">{name_en}</td>'
                f'<td><span class="tag-published-status">已发布</span></td>'
                f'<td class="tag-row-meta">{created_at}</td>'
                f'<td class="tag-row-meta">{creator_id}</td>'
                f'<td class="actions-cell tag-row-actions">{edit_btn}{add_btn}{detail_btn}{del_btn}</td>'
                f'</tr>'
            )
        return group_rows_html

    group_cards = ""
    def can_current_user_manage(owners):
        def normalize(value):
            normalized = re.sub(r"[^a-z0-9]", "", str(value).lower())
            return "joannaqiao" if normalized == "joanna" else normalized
        current_identity = normalize(current_user)
        return any(normalize(owner) == current_identity for owner in owners)

    for idx, group in enumerate(group_payload):
        is_active = idx == 0
        rows_html += build_rows_for_group(group, is_active)
        enabled = bool(group.get("enabled", True))
        owners = group.get("owners", [])
        owners_value = "|".join(owners)
        owners_html = "".join(f'<span class="tag-owner-pill">{owner}</span>' for owner in owners)
        reference_count = int(group.get("reference_count", 0))
        can_edit = can_current_user_manage(owners)
        edit_action = f'''
          <span class="tag-card-action-wrap tag-card-edit-wrap" data-tip="{'编辑' if can_edit else '仅支持负责人编辑'}">
            <button type="button" class="tag-card-action act-icon act-default" aria-label="编辑"
              {'onclick="tagOpenEditGroup(event,this)"' if can_edit else 'disabled'}>{ICON_EDIT}</button>
          </span>
        '''
        if reference_count:
            delete_action = f'''
              <span class="tag-card-action-wrap" data-tip="当前标签组已被引用，不支持删除">
                <button type="button" class="tag-card-action act-icon act-danger" aria-label="删除" disabled>{ICON_DELETE}</button>
              </span>
            '''
        else:
            delete_action = f'''
              <button type="button" class="tag-card-action act-icon act-danger" aria-label="删除"
                data-tip="删除" onclick="tagDeleteGroup(event,this)">{ICON_DELETE}</button>
            '''
        group_cards += f'''
          <div class="tag-group-card {'active' if is_active else ''}" data-group-id="{group["id"]}"
            data-title="{group["name"]}" data-identifier="{group["id"]}" data-desc="{group["desc"]}"
            data-dims="{group["total_dims"]}" data-l2="{group["total_l2"]}" data-l3="{group["total_l3"]}"
            data-rows="{group["total_rows"]}"
            data-owners="{owners_value}" data-references="{reference_count}"
            data-can-manage="{'true' if can_edit else 'false'}"
            data-enabled="{'true' if enabled else 'false'}"
            onclick="tagSelectGroup(this)">
            <div class="tag-card-actions" onclick="event.stopPropagation()">
              {edit_action}
              {delete_action}
            </div>
            <div class="tag-group-field"><span class="tag-group-key">名称</span><b>{group["name"]}</b></div>
            <div class="tag-group-field description"><span class="tag-group-key">描述</span><small data-tip="{group["desc"]}">{group["desc"]}</small></div>
            <div class="tag-group-field"><span class="tag-group-key">负责人</span><em class="tag-owner-list">{owners_html}</em></div>
            <div class="tag-group-field">
              <span class="tag-group-key">启用状态</span>
              <span class="tag-status-control" onclick="event.stopPropagation()">
                <label class="tag-status-switch">
                  <input type="checkbox" {'checked' if enabled else ''} onchange="tagToggleGroupStatus(event,this)">
                  <span class="tag-status-track"></span>
                </label>
                <span class="tag-status-copy">{'启用' if enabled else '停用'}</span>
              </span>
            </div>
          </div>
        '''

    total_rows = active_group["total_rows"]

    content = f'''
    <div class="tag-layout">
      <aside class="tag-group-panel">
        <div class="tag-group-head">
          <span>标签组</span>
          <button type="button" class="tag-group-create-button" onclick="tagOpenCreateGroup()">新增标签组</button>
        </div>
        <div class="tag-group-search">
          <label for="tagGroupSearchInput">标签组名称</label>
          <input class="ant-input" id="tagGroupSearchInput" placeholder="搜索标签组"
            oninput="tagFilterGroups(this.value)">
        </div>
        <div class="tag-group-list">{group_cards}</div>
      </aside>

      <div class="tag-main-panel">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px;">
          <div style="min-width:0;">
            <div id="tagGroupTitle" style="font-size:16px;font-weight:600;color:rgba(0,0,0,0.86);margin-bottom:5px;">{active_group["name"]}</div>
            <div id="tagGroupDesc" class="tag-group-description" data-tip="{active_group["desc"]}">{active_group["desc"]}</div>
          </div>
          <div class="tag-detail-actions" style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;">
            <button class="ant-btn" onclick="tagExpandAll(true)">\u5168\u90e8\u5c55\u5f00</button>
            <button class="ant-btn" onclick="tagExpandAll(false)">\u5168\u90e8\u6536\u8d77</button>
            <button class="ant-btn tag-publish-button" onclick="tagPublishLabels()">发布标签</button>
          </div>
        </div>

        <div class="ant-card ant-card-bordered tag-list-card">
          <div class="tag-list-toolbar">
            <div class="tag-list-filter">
              <label for="tagSearchInput">标签名称</label>
              <div class="tag-list-search">
                <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-4-4"></path></svg>
                <input class="ant-input" id="tagSearchInput" placeholder="请输入标签名称" oninput="tagSearchRows(this.value)">
              </div>
            </div>
            <button class="ant-btn tag-list-create-action" onclick="toast('Demo: 打开新增一级标签')">新增一级标签</button>
          </div>
          <div class="tag-list-table-wrap">
            <table class="ant-table" id="tag-tree-tbl">
              <thead><tr>
                <th style="width:270px;">标签名称</th>
                <th style="width:72px;">层级</th>
                <th style="width:190px;">英文名称</th>
                <th style="width:94px;">状态 <span class="tag-status-help" data-tip="发布后可在任务与数据处理中使用">?</span></th>
                <th style="width:150px;">创建时间</th>
                <th style="width:130px;">创建人 ID</th>
                <th style="width:136px;">操作</th>
              </tr></thead>
              <tbody>{rows_html}</tbody>
            </table>
          </div>
          <div class="tag-list-pagination">
            <span>共 <b id="tagPaginationTotal">{total_rows}</b> 条</span>
            <select aria-label="每页条数"><option>20条/页</option><option>50条/页</option><option>100条/页</option></select>
            <button type="button" aria-label="上一页" disabled>&lsaquo;</button>
            <b class="current-page">1</b>
            <button type="button" aria-label="下一页">&rsaquo;</button>
          </div>
        </div>
      </div>
    </div>

    <div class="ant-drawer-mask" id="create-tag-group-drawer">
      <div class="ant-drawer-content" style="width:480px;">
        <div class="ant-drawer-header">
          <h3 id="tagGroupDrawerTitle">新建标签组</h3>
          <button class="ant-drawer-close" onclick="closeModal('create-tag-group-drawer')">&times;</button>
        </div>
        <div class="ant-drawer-body">
          <div class="form-group"><label class="req">名称</label><input type="text" id="newTagGroupName" placeholder="请输入标签组名称"></div>
          <div class="form-group"><label class="req">标识</label><input type="text" id="newTagGroupIdentifier" placeholder="请输入英文唯一标识"></div>
          <div class="form-group"><label class="req">描述</label><textarea id="newTagGroupDescription" rows="3" placeholder="请输入标签组描述"></textarea></div>
          <div class="form-group">
            <label class="req">负责人</label>
            <div class="tag-owner-editor" onclick="document.getElementById('newTagGroupOwner').focus()">
              <span id="tagGroupOwnerChips"></span>
              <input type="text" id="newTagGroupOwner" placeholder="输入负责人后按回车"
                onkeydown="tagOwnerInputKeydown(event)" oninput="tagOwnerInputChanged(this)"
                onblur="tagCommitOwnerInput()">
            </div>
            <div class="tag-form-hint">支持添加多个负责人，按回车或逗号确认</div>
          </div>
          <div class="form-group">
            <label>启用状态</label>
            <div class="tag-form-status">
              <label class="tag-status-switch">
                <input type="checkbox" id="newTagGroupEnabled" checked onchange="tagSyncCreateStatus(this)">
                <span class="tag-status-track"></span>
              </label>
              <span id="newTagGroupEnabledCopy">启用</span>
            </div>
          </div>
        </div>
        <div class="ant-drawer-footer">
          <button class="ant-btn" onclick="closeModal('create-tag-group-drawer')">取消</button>
          <button class="ant-btn ant-btn-primary" id="tagGroupDrawerSubmit" onclick="tagSaveGroup()">创建</button>
        </div>
      </div>
    </div>

    <style>
      .tag-layout {{ display:grid; grid-template-columns:320px minmax(0,1fr); gap:16px; align-items:start; }}
      .tag-group-panel {{ position:sticky; top:68px; max-height:calc(100vh - 84px); min-height:600px; align-self:start; background:#f4fbfd; border:1px solid #dfecef; border-radius:8px; overflow:auto; }}
      .tag-group-head {{ display:flex; align-items:center; justify-content:space-between; gap:8px; padding:14px 16px; border-bottom:1px solid #dfecef; background:#f8fcfd; font-size:13px; font-weight:600; color:rgba(0,0,0,0.78); }}
      .tag-group-create-button {{ appearance:none; border:0; outline:0; padding:4px 0; background:transparent; color:#1F80A0; font:inherit; font-weight:500; cursor:pointer; }}
      .tag-group-create-button:hover {{ color:#176a88; }}
      .tag-group-search {{ padding:12px; display:flex; flex-direction:column; gap:6px; border-bottom:1px solid #f0f0f0; }}
      .tag-group-search label, .tag-list-filter > label {{ font-size:13px; color:rgba(0,0,0,.72); }}
      .tag-group-search .ant-input {{ width:100%; box-sizing:border-box; background:#fff; }}
      .tag-group-list {{ display:flex; flex-direction:column; gap:10px; padding:12px; }}
      .tag-group-card {{ position:relative; width:100%; padding:14px; border:1px solid transparent; border-radius:8px; background:rgba(255,255,255,0.58); text-align:left; cursor:pointer; transition:all .15s; box-sizing:border-box; }}
      .tag-group-card:hover {{ border-color:#b7e1e6; background:#fff; }}
      .tag-group-card.active {{ border-color:#8fd8e1; background:#e9f9fb; box-shadow:inset 3px 0 0 #1F80A0; }}
      .tag-card-actions {{ position:absolute; top:8px; right:8px; display:flex; align-items:center; gap:4px; padding:2px; border-radius:6px; background:rgba(255,255,255,.94); box-shadow:0 2px 8px rgba(0,0,0,.08); opacity:0; transform:translateY(-2px); pointer-events:none; transition:.15s; }}
      .tag-group-card:hover .tag-card-actions,.tag-group-card:focus-within .tag-card-actions {{ opacity:1; transform:translateY(0); pointer-events:auto; }}
      .tag-card-action-wrap {{ display:inline-flex; }}
      .tag-card-action[disabled] {{ pointer-events:none; cursor:not-allowed; opacity:.3; }}
      .tag-group-field {{ display:grid; grid-template-columns:58px minmax(0,1fr); align-items:center; gap:8px; margin-top:8px; }}
      .tag-card-actions + .tag-group-field {{ margin-top:0; padding-right:64px; }}
      .tag-group-field.description {{ align-items:center; min-width:0; }}
      .tag-group-key {{ color:rgba(0,0,0,0.38); font-size:11px; }}
      .tag-group-card b {{ color:rgba(0,0,0,0.86); font-size:14px; }}
      .tag-group-card small {{ display:block; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:rgba(0,0,0,0.58); font-size:12px; line-height:1.5; }}
      .tag-group-card em {{ color:rgba(0,0,0,0.65); font-size:12px; font-style:normal; }}
      .tag-owner-list {{ display:flex; flex-wrap:wrap; gap:4px; }}
      .tag-owner-pill {{ display:inline-flex; align-items:center; max-width:100%; padding:1px 6px; border-radius:4px; background:#eef4f5; color:rgba(0,0,0,.65); line-height:20px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
      .tag-status-control,.tag-form-status {{ display:inline-flex; align-items:center; gap:8px; color:rgba(0,0,0,.58); font-size:12px; }}
      .tag-status-switch {{ position:relative; display:inline-block; width:38px; height:20px; flex:none; cursor:pointer; }}
      .tag-status-switch input {{ position:absolute; opacity:0; width:0; height:0; }}
      .tag-status-track {{ position:absolute; inset:0; border-radius:20px; background:#bfbfbf; transition:.18s; }}
      .tag-status-track::before {{ content:''; position:absolute; left:3px; top:3px; width:14px; height:14px; border-radius:50%; background:#fff; box-shadow:0 1px 3px rgba(0,0,0,.18); transition:.18s; }}
      .tag-status-switch input:checked + .tag-status-track {{ background:#1F80A0; }}
      .tag-status-switch input:checked + .tag-status-track::before {{ transform:translateX(18px); }}
      .tag-form-status {{ min-height:32px; }}
      .tag-owner-editor {{ min-height:36px; display:flex; flex-wrap:wrap; align-items:center; gap:6px; padding:4px 8px; border:1px solid #d9d9d9; border-radius:8px; background:#fff; box-sizing:border-box; cursor:text; transition:border-color .15s,box-shadow .15s; }}
      .tag-owner-editor:focus-within {{ border-color:#1F80A0; box-shadow:0 0 0 2px rgba(31,128,160,.12); }}
      #tagGroupOwnerChips {{ display:contents; }}
      .tag-owner-edit-chip {{ display:inline-flex; align-items:center; gap:5px; padding:2px 6px 2px 8px; border-radius:5px; background:#eef7f8; color:#176a88; font-size:12px; line-height:22px; }}
      .tag-owner-edit-chip button {{ appearance:none; border:0; padding:0; background:transparent; color:rgba(0,0,0,.35); cursor:pointer; font-size:14px; line-height:1; }}
      .tag-owner-edit-chip button:hover {{ color:#ff4d4f; }}
      #newTagGroupOwner {{ flex:1; min-width:150px; width:auto; height:26px; padding:0; border:0; outline:0; box-shadow:none; }}
      #newTagGroupIdentifier:disabled {{ background:#f5f5f5; color:rgba(0,0,0,.38); cursor:not-allowed; }}
      .tag-form-hint {{ margin-top:6px; font-size:12px; color:rgba(0,0,0,.38); }}
      .tag-main-panel {{ min-width:0; }}
      .tag-main-panel.tag-readonly .tag-detail-actions {{ display:none !important; }}
      .tag-main-panel.tag-readonly .tag-list-create-action {{ display:none; }}
      .tag-main-panel.tag-readonly #tag-tree-tbl th:last-child,
      .tag-main-panel.tag-readonly #tag-tree-tbl td.actions-cell {{ display:none; }}
      .tag-publish-button {{ border:1px solid #d9d9d9; background:#fff; color:rgba(0,0,0,.65); box-shadow:none; }}
      .tag-publish-button:hover {{ border-color:#1F80A0; background:#fff; color:#1F80A0; }}
      .tag-group-description {{ max-width:760px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:13px; color:rgba(0,0,0,0.45); }}
      .tag-list-card {{ overflow:hidden; background:#fff; }}
      .tag-list-toolbar {{ min-height:76px; display:flex; align-items:flex-end; justify-content:space-between; gap:16px; padding:12px 14px; border-bottom:1px solid #f0f0f0; box-sizing:border-box; }}
      .tag-list-filter {{ display:flex; flex-direction:column; gap:6px; }}
      .tag-list-search {{ position:relative; width:240px; }}
      .tag-list-search svg {{ position:absolute; left:11px; top:50%; width:15px; height:15px; transform:translateY(-50%); fill:none; stroke:#a6adb4; stroke-width:1.8; pointer-events:none; z-index:1; }}
      .tag-list-search .ant-input {{ width:100%; padding-left:34px; box-sizing:border-box; }}
      .tag-list-create-action {{ border-color:#1F80A0; background:#fff; color:#1F80A0; }}
      .tag-list-create-action:hover {{ border-color:#176a88; background:#f4fbfd; color:#176a88; }}
      .tag-list-table-wrap {{ min-height:420px; max-height:calc(100vh - 330px); overflow:auto; }}
      #tag-tree-tbl {{ width:100%; min-width:1042px; table-layout:fixed; }}
      #tag-tree-tbl thead th {{ position:sticky; top:0; z-index:3; height:46px; padding-top:0; padding-bottom:0; background:#fafafa; color:rgba(0,0,0,.45); font-size:12px; font-weight:500; }}
      #tag-tree-tbl tbody td {{ height:54px; padding-top:0; padding-bottom:0; color:rgba(0,0,0,.72); font-size:13px; box-sizing:border-box; }}
      #tag-tree-tbl thead th:last-child,#tag-tree-tbl tbody td:last-child {{ position:sticky; right:0; z-index:2; background:#fff; box-shadow:-6px 0 10px rgba(0,0,0,.035); }}
      #tag-tree-tbl thead th:last-child {{ z-index:4; background:#fafafa; }}
      .tag-name-cell {{ display:flex; align-items:center; gap:8px; white-space:nowrap; overflow:hidden; }}
      .tag-drag-handle {{ flex:none; width:14px; color:#c6cdd3; font-size:13px; letter-spacing:-4px; cursor:grab; user-select:none; }}
      .tag-row-check,.tag-row-check-placeholder {{ width:16px; height:16px; margin:0; flex:none; box-sizing:border-box; }}
      .tag-row-check {{ appearance:none; border:1px solid #d9dfe5; border-radius:3px; background:#fff; cursor:pointer; }}
      .tag-row-check:checked {{ border-color:#1F80A0; background:#1F80A0; box-shadow:inset 0 0 0 3px #fff; }}
      .tag-row-name {{ min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:rgba(0,0,0,.82); }}
      .tag-row-name.is-root {{ font-weight:600; }}
      .tag-level-badge {{ display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border-radius:50%; font-size:12px; font-weight:500; }}
      .tag-level-badge.level-1 {{ background:#ffe8ea; color:#ff7a82; }}
      .tag-level-badge.level-2 {{ background:#fff1dc; color:#f2aa45; }}
      .tag-level-badge.level-3 {{ background:#e9f6ff; color:#4297c2; }}
      .tag-row-english {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:rgba(0,0,0,.72); }}
      .tag-published-status {{ display:inline-flex; align-items:center; padding:2px 9px; border-radius:10px; background:#f1fae9; color:#52b836; font-size:12px; font-weight:500; }}
      .tag-row-meta {{ color:rgba(0,0,0,.46) !important; font-size:12px !important; white-space:nowrap; }}
      .tag-status-help {{ display:inline-flex; align-items:center; justify-content:center; width:14px; height:14px; border-radius:50%; background:#989fa6; color:#fff; font-size:9px; cursor:help; vertical-align:middle; }}
      .tag-row-actions {{ white-space:nowrap; }}
      .tag-row-actions .act-icon {{ margin-right:5px; }}
      .tag-row-actions .act-icon:nth-child(2) svg {{ stroke:#52c41a; }}
      .tag-list-pagination {{ min-height:58px; display:flex; align-items:center; justify-content:flex-end; gap:14px; padding:10px 16px; border-top:1px solid #f0f0f0; color:rgba(0,0,0,.55); font-size:13px; box-sizing:border-box; }}
      .tag-list-pagination b {{ font-weight:500; color:rgba(0,0,0,.65); }}
      .tag-list-pagination select {{ height:34px; min-width:100px; padding:0 30px 0 12px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; color:rgba(0,0,0,.65); }}
      .tag-list-pagination button {{ appearance:none; width:30px; height:30px; border:0; background:transparent; color:#8c8c8c; cursor:pointer; font-size:18px; }}
      .tag-list-pagination button:disabled {{ color:#d9d9d9; cursor:not-allowed; }}
      .tag-list-pagination .current-page {{ color:#1F80A0; font-weight:600; }}
      .tree-caret {{ cursor:pointer; display:inline-block; width:16px; flex:none; text-align:center; color:rgba(0,0,0,0.55); transition:transform 0.2s; user-select:none; margin-right:0; font-size:10px; }}
      .tree-caret.empty {{ cursor:default; }}
      .tree-caret:hover {{ color:#1F80A0; }}
      .tree-caret.collapsed {{ transform:rotate(-90deg); }}
      @media (max-width: 980px) {{
        .tag-layout {{ grid-template-columns:1fr; }}
        .tag-group-panel {{ position:relative; top:auto; max-height:none; min-height:0; overflow:visible; }}
        .tag-group-list {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); }}
        .tag-list-table-wrap {{ max-height:none; }}
      }}
    </style>

    <script>
    var currentTagGroup = '{active_group["id"]}';
    var currentTagUser = '{current_user}';
    var tagEditingGroup = null;
    var tagGroupOwners = [];
    function tagRowsInCurrentGroup() {{
      return Array.prototype.slice.call(document.querySelectorAll('#tag-tree-tbl tbody tr[data-group="' + currentTagGroup + '"]'));
    }}
    function tagUpdatePaginationTotal(count) {{
      var target = document.getElementById('tagPaginationTotal');
      if (target) target.textContent = String(count);
    }}
    function tagToggle(id) {{
      var caret = document.querySelector('tr[data-id="' + id + '"] .tree-caret');
      if (!caret) return;
      var wasCollapsed = caret.classList.contains('collapsed');
      caret.classList.toggle('collapsed');
      document.querySelectorAll('#tag-tree-tbl tbody tr[data-parent][data-group="' + currentTagGroup + '"]').forEach(function(tr) {{
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
      tagRowsInCurrentGroup().forEach(function(tr) {{
        var c = tr.querySelector('.tree-caret');
        if (!c) return;
        if (expand) c.classList.remove('collapsed');
        else c.classList.add('collapsed');
      }});
      document.querySelectorAll('#tag-tree-tbl tbody tr').forEach(function(tr) {{
        if (tr.getAttribute('data-group') !== currentTagGroup) {{ tr.style.display = 'none'; return; }}
        var p = tr.getAttribute('data-parent') || '';
        if (p) tr.style.display = expand ? '' : 'none';
        else tr.style.display = '';
      }});
      tagSearchRows(document.getElementById('tagSearchInput').value);
    }}
    function tagSyncManagePermission(card) {{
      var canManage = !!card && card.dataset.canManage === 'true';
      var panel = document.querySelector('.tag-main-panel');
      panel.classList.toggle('tag-readonly', !canManage);
      panel.setAttribute('data-can-manage', canManage ? 'true' : 'false');
    }}
    function tagSelectGroup(btn) {{
      currentTagGroup = btn.dataset.groupId;
      document.querySelectorAll('.tag-group-card').forEach(function(item) {{
        item.classList.toggle('active', item === btn);
      }});
      document.getElementById('tagGroupTitle').textContent = btn.dataset.title;
      document.getElementById('tagGroupDesc').textContent = btn.dataset.desc;
      document.getElementById('tagGroupDesc').setAttribute('data-tip', btn.dataset.desc);
      tagSyncManagePermission(btn);
      tagUpdatePaginationTotal(Number(btn.dataset.rows || 0));
      document.querySelectorAll('#tag-tree-tbl tbody tr').forEach(function(tr) {{
        tr.style.display = tr.getAttribute('data-group') === currentTagGroup ? '' : 'none';
        var c = tr.querySelector('.tree-caret');
        if (c) c.classList.remove('collapsed');
      }});
      document.getElementById('tagSearchInput').value = '';
    }}
    function tagToggleGroupStatus(event, input) {{
      event.stopPropagation();
      var card = input.closest('.tag-group-card');
      var copy = input.closest('.tag-status-control').querySelector('.tag-status-copy');
      card.dataset.enabled = input.checked ? 'true' : 'false';
      copy.textContent = input.checked ? '启用' : '停用';
      toast(input.checked ? '标签组已启用' : '标签组已停用');
    }}
    function tagSyncCreateStatus(input) {{
      document.getElementById('newTagGroupEnabledCopy').textContent = input.checked ? '启用' : '停用';
    }}
    function tagRenderOwnerChips() {{
      var box = document.getElementById('tagGroupOwnerChips');
      box.innerHTML = '';
      tagGroupOwners.forEach(function(owner) {{
        var chip = document.createElement('span');
        chip.className = 'tag-owner-edit-chip';
        var copy = document.createElement('span');
        copy.textContent = owner;
        var remove = document.createElement('button');
        remove.type = 'button';
        remove.setAttribute('aria-label', '移除 ' + owner);
        remove.textContent = '\u00d7';
        remove.onclick = function(event) {{
          event.stopPropagation();
          tagGroupOwners = tagGroupOwners.filter(function(item) {{ return item !== owner; }});
          tagRenderOwnerChips();
        }};
        chip.appendChild(copy);
        chip.appendChild(remove);
        box.appendChild(chip);
      }});
    }}
    function tagAddOwners(raw) {{
      String(raw || '').split(/[,，]/).forEach(function(item) {{
        var owner = item.trim();
        if (owner && tagGroupOwners.indexOf(owner) < 0) tagGroupOwners.push(owner);
      }});
      tagRenderOwnerChips();
    }}
    function tagCommitOwnerInput() {{
      var input = document.getElementById('newTagGroupOwner');
      if (!input) return;
      tagAddOwners(input.value);
      input.value = '';
    }}
    function tagOwnerInputKeydown(event) {{
      if (event.key === 'Enter' || event.key === ',' || event.key === '，') {{
        event.preventDefault();
        tagCommitOwnerInput();
      }}
      if (event.key === 'Backspace' && !event.currentTarget.value && tagGroupOwners.length) {{
        tagGroupOwners.pop();
        tagRenderOwnerChips();
      }}
    }}
    function tagOwnerInputChanged(input) {{
      if (input.value.indexOf(',') >= 0 || input.value.indexOf('，') >= 0) tagCommitOwnerInput();
    }}
    function tagResetGroupForm() {{
      tagEditingGroup = null;
      tagGroupOwners = [];
      document.getElementById('tagGroupDrawerTitle').textContent = '新建标签组';
      document.getElementById('tagGroupDrawerSubmit').textContent = '创建';
      document.getElementById('newTagGroupName').value = '';
      document.getElementById('newTagGroupIdentifier').value = '';
      document.getElementById('newTagGroupIdentifier').disabled = false;
      document.getElementById('newTagGroupDescription').value = '';
      document.getElementById('newTagGroupOwner').value = '';
      document.getElementById('newTagGroupEnabled').checked = true;
      tagSyncCreateStatus(document.getElementById('newTagGroupEnabled'));
      tagRenderOwnerChips();
    }}
    function tagOpenCreateGroup() {{
      tagResetGroupForm();
      openModal('create-tag-group-drawer');
    }}
    function tagOpenEditGroup(event, button) {{
      event.stopPropagation();
      var card = button.closest('.tag-group-card');
      tagEditingGroup = card;
      tagGroupOwners = (card.dataset.owners || '').split('|').filter(Boolean);
      document.getElementById('tagGroupDrawerTitle').textContent = '编辑标签组';
      document.getElementById('tagGroupDrawerSubmit').textContent = '保存';
      document.getElementById('newTagGroupName').value = card.dataset.title || '';
      document.getElementById('newTagGroupIdentifier').value = card.dataset.identifier || '';
      document.getElementById('newTagGroupIdentifier').disabled = true;
      document.getElementById('newTagGroupDescription').value = card.dataset.desc || '';
      document.getElementById('newTagGroupOwner').value = '';
      document.getElementById('newTagGroupEnabled').checked = card.dataset.enabled === 'true';
      tagSyncCreateStatus(document.getElementById('newTagGroupEnabled'));
      tagRenderOwnerChips();
      openModal('create-tag-group-drawer');
    }}
    function tagRenderOwners(card, owners) {{
      var ownerList = card.querySelector('.tag-owner-list');
      ownerList.innerHTML = '';
      owners.forEach(function(owner) {{
        var item = document.createElement('span');
        item.className = 'tag-owner-pill';
        item.textContent = owner;
        ownerList.appendChild(item);
      }});
    }}
    function tagOwnerIdentity(value) {{
      var normalized = String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      return normalized === 'joanna' ? 'joannaqiao' : normalized;
    }}
    function tagCurrentUserOwns(owners) {{
      var currentIdentity = tagOwnerIdentity(currentTagUser);
      return owners.some(function(owner) {{ return tagOwnerIdentity(owner) === currentIdentity; }});
    }}
    function tagSyncEditPermission(card, owners) {{
      var canEdit = tagCurrentUserOwns(owners);
      var wrap = card.querySelector('.tag-card-edit-wrap');
      var button = wrap.querySelector('button');
      card.dataset.canManage = canEdit ? 'true' : 'false';
      wrap.setAttribute('data-tip', canEdit ? '编辑' : '仅支持负责人编辑');
      button.disabled = !canEdit;
      if (canEdit) button.setAttribute('onclick', 'tagOpenEditGroup(event,this)');
      else button.removeAttribute('onclick');
      if (card.classList.contains('active')) tagSyncManagePermission(card);
    }}
    function tagApplyGroupCard(card, name, description, owners, enabled) {{
      card.dataset.title = name;
      card.dataset.desc = description;
      card.dataset.owners = owners.join('|');
      card.dataset.enabled = enabled ? 'true' : 'false';
      card.querySelector('b').textContent = name;
      card.querySelector('small').textContent = description;
      card.querySelector('small').setAttribute('data-tip', description);
      tagRenderOwners(card, owners);
      tagSyncEditPermission(card, owners);
      var checkbox = card.querySelector('.tag-status-switch input');
      checkbox.checked = enabled;
      card.querySelector('.tag-status-copy').textContent = enabled ? '启用' : '停用';
    }}
    function tagBuildGroupCard() {{
      var card = document.createElement('div');
      card.className = 'tag-group-card';
      card.dataset.dims = '0';
      card.dataset.l2 = '0';
      card.dataset.l3 = '0';
      card.dataset.rows = '0';
      card.dataset.references = '0';
      card.onclick = function() {{ tagSelectGroup(card); }};
      card.innerHTML =
        '<div class="tag-card-actions" onclick="event.stopPropagation()">' +
          '<span class="tag-card-action-wrap tag-card-edit-wrap" data-tip="仅支持负责人编辑">' +
            '<button type="button" class="tag-card-action act-icon act-default" aria-label="编辑" disabled>{ICON_EDIT}</button>' +
          '</span>' +
          '<button type="button" class="tag-card-action act-icon act-danger" aria-label="删除" data-tip="删除" onclick="tagDeleteGroup(event,this)">{ICON_DELETE}</button>' +
        '</div>' +
        '<div class="tag-group-field"><span class="tag-group-key">名称</span><b></b></div>' +
        '<div class="tag-group-field description"><span class="tag-group-key">描述</span><small></small></div>' +
        '<div class="tag-group-field"><span class="tag-group-key">负责人</span><em class="tag-owner-list"></em></div>' +
        '<div class="tag-group-field"><span class="tag-group-key">启用状态</span><span class="tag-status-control" onclick="event.stopPropagation()">' +
          '<label class="tag-status-switch"><input type="checkbox" onchange="tagToggleGroupStatus(event,this)"><span class="tag-status-track"></span></label>' +
          '<span class="tag-status-copy"></span></span></div>';
      return card;
    }}
    function tagCreateGroup(name, identifier, description, owners, enabled) {{
      var id = 'tag_group_' + Date.now();
      var card = tagBuildGroupCard();
      card.dataset.groupId = id;
      card.dataset.identifier = identifier;
      tagApplyGroupCard(card, name, description, owners, enabled);
      document.querySelector('.tag-group-list').appendChild(card);
      tagSelectGroup(card);
      toast('标签组已创建');
    }}
    function tagUpdateGroup(card, name, description, owners, enabled) {{
      tagApplyGroupCard(card, name, description, owners, enabled);
      if (card.classList.contains('active')) {{
        document.getElementById('tagGroupTitle').textContent = name;
        document.getElementById('tagGroupDesc').textContent = description;
        document.getElementById('tagGroupDesc').setAttribute('data-tip', description);
      }}
      toast('标签组已更新');
    }}
    function tagIdentifierExists(identifier, excludedCard) {{
      var normalized = String(identifier || '').trim().toLowerCase();
      return Array.prototype.some.call(document.querySelectorAll('.tag-group-card'), function(card) {{
        return card !== excludedCard && String(card.dataset.identifier || '').trim().toLowerCase() === normalized;
      }});
    }}
    function tagSaveGroup() {{
      tagCommitOwnerInput();
      var name = document.getElementById('newTagGroupName').value.trim();
      var identifier = document.getElementById('newTagGroupIdentifier').value.trim();
      var description = document.getElementById('newTagGroupDescription').value.trim();
      var enabled = document.getElementById('newTagGroupEnabled').checked;
      if (!name || !identifier || !description || !tagGroupOwners.length) {{
        toast('请完整填写名称、标识、描述和负责人');
        return;
      }}
      if (tagIdentifierExists(identifier, tagEditingGroup)) {{
        toast('标识已存在，请更换');
        return;
      }}
      if (tagEditingGroup) tagUpdateGroup(tagEditingGroup, name, description, tagGroupOwners.slice(), enabled);
      else tagCreateGroup(name, identifier, description, tagGroupOwners.slice(), enabled);
      closeModal('create-tag-group-drawer');
      tagResetGroupForm();
      tagFilterGroups(document.getElementById('tagGroupSearchInput').value);
    }}
    function tagDeleteGroup(event, button) {{
      event.stopPropagation();
      var card = button.closest('.tag-group-card');
      var references = Number(card.dataset.references || 0);
      if (references > 0) {{
        toast('当前标签组已被引用，不支持删除');
        return;
      }}
      if (!window.confirm('确定删除标签组“' + card.dataset.title + '”吗？')) return;
      var wasActive = card.classList.contains('active');
      var fallback = card.nextElementSibling || card.previousElementSibling;
      document.querySelectorAll('#tag-tree-tbl tbody tr[data-group="' + card.dataset.groupId + '"]').forEach(function(row) {{ row.remove(); }});
      card.remove();
      if (wasActive && fallback) tagSelectGroup(fallback);
      toast('标签组已删除');
    }}
    function tagFilterGroups(keyword) {{
      var value = String(keyword || '').trim().toLowerCase();
      document.querySelectorAll('.tag-group-card').forEach(function(card) {{
        var searchable = [card.dataset.title, card.dataset.identifier, card.dataset.desc, card.dataset.owners].join(' ').toLowerCase();
        card.style.display = !value || searchable.indexOf(value) >= 0 ? '' : 'none';
      }});
    }}
    function tagPublishLabels() {{
      var active = document.querySelector('.tag-group-card.active');
      toast((active ? active.dataset.title : '当前标签组') + '已发布');
    }}
    function tagSearchRows(keyword) {{
      var kw = String(keyword || '').trim().toLowerCase();
      if (!kw) {{
        var total = 0;
        document.querySelectorAll('#tag-tree-tbl tbody tr').forEach(function(tr) {{
          var inCurrentGroup = tr.getAttribute('data-group') === currentTagGroup;
          tr.style.display = inCurrentGroup ? '' : 'none';
          if (inCurrentGroup) total += 1;
        }});
        tagUpdatePaginationTotal(total);
        return;
      }}
      var matches = 0;
      document.querySelectorAll('#tag-tree-tbl tbody tr').forEach(function(tr) {{
        if (tr.getAttribute('data-group') !== currentTagGroup) {{ tr.style.display = 'none'; return; }}
        var matched = tr.innerText.toLowerCase().indexOf(kw) >= 0;
        tr.style.display = matched ? '' : 'none';
        if (matched) matches += 1;
      }});
      tagUpdatePaginationTotal(matches);
    }}
    tagSyncManagePermission(document.querySelector('.tag-group-card.active'));
    </script>
    '''
    return render_page("\u6807\u7b7e\u7ba1\u7406", content, active="tags")


# ── Criteria Management ──
@app.route("/criteria")
def criteria_page():
    rows = ""
    for c in CRITERIA:
        status_label = c.get("publish_status", "已发布")
        is_unpublished = status_label == "未发布"
        status_class = "tag-gray" if is_unpublished else "tag-green"
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
        view_btn = f'<a href="javascript:void(0)" class="action-link" onclick="openCriteriaView(\'{c["id"]}\')">查看</a>'
        edit_btn = f'<a href="javascript:void(0)" class="action-link" onclick="openCriteriaEdit(\'{c["id"]}\')">编辑</a>' if is_unpublished else ''
        publish_btn = f'<a href="/criteria/{c["id"]}/publish" class="action-link" onclick="return confirm(\'发布后将不能编辑或删除，确认发布吗？\')">发布</a>' if is_unpublished else ''
        copy_btn = '<a href="#" class="action-link" onclick="toast(\'已复制评价标准\');return false;">复制</a>'
        del_btn = f'<a href="/criteria/{c["id"]}/delete" class="action-link danger" onclick="return confirm(\'确认删除该评价标准吗？\')">删除</a>' if is_unpublished else ''
        more_btn = f'<span class="action-more-wrap"><a href="javascript:void(0)" class="action-link">更多</a><span class="action-more-menu">{edit_btn}{del_btn}</span></span>' if is_unpublished else ''
        actions_html = view_btn + copy_btn + publish_btn + more_btn

        rows += f'''<tr>
            <td style="font-weight:500;">{c["name"]}</td>
            <td title="{c['description']}">{c["description"][:40]}...</td>
            <td><span class="tag {status_class}">{status_label}</span></td>
            <td>{c["creator"]}</td>
            <td>{c["created_at"]}</td>
            <td class="actions-cell">{actions_html}</td>
        </tr>'''

    criteria_view_data = json.dumps({
        c["id"]: {
            "name": c.get("name", ""),
            "description": c.get("description", ""),
            "publish_status": c.get("publish_status", "已发布"),
            "result_definitions": normalize_result_definitions(c.get("result_definitions", {})),
            "metrics": get_criterion_metrics(c),
        }
        for c in CRITERIA
    }, ensure_ascii=False)

    content = f'''
    <div style="display:none" class="stat-grid">
      <div class="stat-card"><div class="stat-label">\u6807\u51c6\u603b\u6570</div><div class="stat-value">{len(CRITERIA)}</div></div>
      <div class="stat-card"><div class="stat-label">\u504f\u597d\u9009\u62e9</div><div class="stat-value">{sum(1 for c in CRITERIA if c["type"]=="preference")}</div></div>
      <div class="stat-card"><div class="stat-label">\u6210\u529f\u5931\u8d25</div><div class="stat-value">{sum(1 for c in CRITERIA if c["type"]=="pass_fail")}</div></div>
      <div class="stat-card"><div class="stat-label">\u91cf\u8868\u8bc4\u5206</div><div class="stat-value">{sum(1 for c in CRITERIA if c["type"]=="scale")}</div></div>
    </div>

    <div style="display:none">
    <div class="ant-card ant-card-bordered" style="margin-bottom:16px;">
      <div class="ant-card-head"><div class="ant-card-head-title">评测结果</div></div>
      <div class="ant-card-body"><div class="muted" style="margin-bottom:12px;">选择评测任务允许使用的结果状态，成功和失败为系统必选项。</div>
        <div style="display:flex;gap:24px;flex-wrap:wrap;">
          <label><input type="checkbox" checked disabled> 成功 <span class="muted">（必选）</span></label>
          <label><input type="checkbox" checked disabled> 失败 <span class="muted">（必选）</span></label>
          <label><input type="checkbox" checked> 重试1次成功</label><label><input type="checkbox"> 重试2次成功</label><label><input type="checkbox"> 重试3次成功</label>
        </div>
      </div>
    </div>
    <div class="ant-card ant-card-bordered" style="margin-bottom:16px;">
      <div class="ant-card-head"><div class="ant-card-head-title">评测指标</div><button class="ant-btn ant-btn-primary" type="button" onclick="criteriaAddMetric()">+ 新增指标</button></div>
      <div class="ant-card-body" style="padding:0;"><table class="ant-table" id="criteria-metrics-table"><thead><tr><th>指标名称</th><th>字段类型</th><th>字段值</th><th>操作</th></tr></thead><tbody><tr><td>任务完成度</td><td>数值</td><td>0-100</td><td><button class="ant-btn" type="button" onclick="criteriaRemoveMetric(this)">删除</button></td></tr></tbody></table></div>
    </div>

    </div>
    <div class="filter-bar fb-labeled">
      <div class="ff"><label>\u6807\u51c6\u540d\u79f0</label><input type="text" placeholder="\u641c\u7d22\u6807\u51c6\u540d\u79f0"></div>
      <div class="ff"><label>\u521b\u5efa\u4eba</label><select><option value="">\u5168\u90e8\u521b\u5efa\u4eba</option>{"".join(f'<option>{c["creator"]}</option>' for c in CRITERIA)}</select></div>
      <div class="ff"><label>状态</label><select name="publish_status"><option value="">全部状态</option><option>未发布</option><option>已发布</option></select></div>
      <div class="filter-actions">
        <button class="ant-btn" onclick="clearFilters()">\u6e05\u7a7a</button>
        <button class="ant-btn ant-btn-primary" onclick="doSearch()">\u641c\u7d22</button>
      </div>
      <div style="flex:1;"></div>
      <button class="ant-btn ant-btn-primary" onclick="openCriteriaCreate()">\u65b0\u589e\u8bc4\u4ef7\u6807\u51c6</button>
    </div>

    <div class="ant-card ant-card-bordered criteria-list-card">
      <table class="ant-table">
        <thead><tr>
          <th>\u6807\u51c6\u540d\u79f0</th>
          <th>\u63cf\u8ff0</th>
          <th>\u72b6\u6001</th>
          <th>\u521b\u5efa\u4eba</th>
          <th>\u521b\u5efa\u65f6\u95f4</th>
          <th>\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <!-- Create Criteria Drawer -->
    <div class="ant-drawer-mask" id="create-criteria-drawer">
      <div class="ant-drawer-content criteria-drawer-content">
        <div class="ant-drawer-header">
          <h3>\u65b0\u589e\u8bc4\u4ef7\u6807\u51c6</h3>
          <button class="ant-drawer-close" onclick="closeModal('create-criteria-drawer')">&times;</button>
        </div>
        <form method="POST" action="/criteria/create">
        <input type="hidden" name="edit_id" value="">
        <div class="ant-drawer-body">
          <div class="form-group"><label>\u6807\u51c6\u540d\u79f0</label><input type="text" name="name" required placeholder="请输入评价标准名称"></div>
          <div class="form-group"><label>\u63cf\u8ff0</label><textarea name="description" rows="3"></textarea></div>
          <div class="form-group" id="criteria-publish-status-field" style="display:none;"><label>状态</label><select name="publish_status"><option value="未发布">未发布</option><option value="已发布">已发布</option></select></div>
          <hr style="border:none;border-top:1px solid #f0f0f0;margin:20px 0;">
          <div class="form-group"><label>评测结果</label>
            <table class="ant-table criteria-result-table" id="criteria-result-table">
              <thead><tr><th>结果类型</th><th style="width:110px;">完成度 <span class="criteria-completion-tip" data-tip="数值越高完成度越高" tabindex="0">i</span></th><th style="width:64px;">操作</th></tr></thead>
              <tbody></tbody>
            </table>
            <div class="criteria-result-add-actions"><a href="javascript:void(0)" class="action-link criteria-add-result" onclick="criteriaAddResultRow()">新增评测结果</a></div>
          </div>
          <div class="form-group"><label>评测指标</label>
          <table class="ant-table criteria-metrics-table" id="criteria-metrics-table"><thead><tr><th>指标名称</th><th>字段类型</th><th>选项（单选/多选）</th><th>默认值</th><th>指标说明</th><th>操作</th></tr></thead><tbody><tr class="criteria-metric-row"><td><input class="ant-input" name="metric_name" placeholder="请输入指标名称"></td><td><select class="ant-input metric-type" name="metric_type" onchange="criteriaMetricTypeChange(this)"><option>文本</option><option>单选</option><option>多选</option><option>数字</option></select></td><td><input class="ant-input metric-options" name="metric_options" placeholder="逗号分隔选项" disabled oninput="criteriaMetricOptionsChange(this)"></td><td class="metric-default-cell"><input class="ant-input" name="metric_default" placeholder="请输入默认值"></td><td><input class="ant-input" name="metric_description" placeholder="请输入指标说明"></td><td><a href="javascript:void(0)" class="action-link" onclick="criteriaRemoveMetric(this)">删除</a></td></tr></tbody></table>
          <a href="javascript:void(0)" class="action-link criteria-add-metric" onclick="criteriaAddMetric()">新增指标</a></div>
        </div>
        <div class="ant-drawer-footer">
          <button type="button" class="ant-btn" onclick="closeModal('create-criteria-drawer')">关闭</button>
          <button type="button" class="ant-btn criteria-preview-trigger" onclick="openCriteriaPreview()">预览</button>
          <button type="submit" class="ant-btn ant-btn-primary">\u521b\u5efa</button>
        </div>
        </form>
      </div>
    </div>
    <div class="criteria-preview-mask" id="criteria-preview-mask" hidden onclick="if(event.target===this) criteriaClosePreview()">
      <div class="hmi-result-dialog criteria-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="criteria-preview-title">
        <h3 id="criteria-preview-title">提交评测结果</h3>
        <section class="hmi-result-section">
          <h4>评测结果</h4>
          <div class="hmi-result-radios" id="criteria-preview-results"></div>
        </section>
        <section class="hmi-metric-section">
          <h4>评测指标</h4>
          <div id="criteria-preview-metrics"></div>
        </section>
        <div class="criteria-preview-actions">
          <button type="button" onclick="criteriaClosePreview()">取消</button>
          <button type="button" class="primary" onclick="criteriaPreviewSubmit()">提交</button>
        </div>
      </div>
    </div>
    <style>
      .criteria-drawer-content {{ width: 1000px; max-width: calc(100vw - 32px); }}
      .criteria-drawer-content .ant-drawer-body {{ padding: 20px 24px; }}
      .criteria-metrics-table {{ table-layout: fixed; font-size: 12px; }}
      .criteria-metrics-table th, .criteria-metrics-table td {{ padding: 8px 6px; }}
      .criteria-metrics-table th:nth-child(1) {{ width: 18%; }} .criteria-metrics-table th:nth-child(2) {{ width: 13%; }}
      .criteria-metrics-table th:nth-child(3) {{ width: 20%; }} .criteria-metrics-table th:nth-child(4) {{ width: 17%; }} .criteria-metrics-table th:nth-child(5) {{ width: 24%; }} .criteria-metrics-table th:nth-child(6) {{ width: 8%; }}
      .criteria-metrics-table .ant-input {{ width: 100%; min-width: 0; box-sizing: border-box; }}
      .criteria-metrics-table select.metric-type {{ padding-right: 30px; -webkit-appearance: none; appearance: none; }}
      .criteria-metrics-table select.metric-default-select[multiple] {{ height: 34px; overflow: hidden; }}
      .criteria-result-options {{ display:flex; align-items:center; gap:24px; min-height:32px; flex-wrap:wrap; }}
      .criteria-result-options label {{ margin:0; font-weight:400; }}
      .criteria-result-summary {{ display:flex;flex-direction:column;gap:4px;font-size:12px;color:rgba(0,0,0,.55);line-height:1.5; }}
      .criteria-result-summary b {{ color:rgba(0,0,0,.75);font-weight:600; }}
      .criteria-result-table {{ table-layout:fixed;font-size:12px;margin-top:8px; }}
      .criteria-result-table th,.criteria-result-table td {{ padding:8px 10px;vertical-align:middle; }}
      .criteria-result-table th:nth-child(1) {{ width:auto; }} .criteria-result-table th:nth-child(2) {{ width:110px; }} .criteria-result-table th:nth-child(3) {{ width:64px; }}
      .criteria-result-table .ant-input {{ width:100%;box-sizing:border-box; }}
      .criteria-result-table tbody tr {{ cursor:grab; }} .criteria-result-table tbody tr:active {{ cursor:grabbing; }} .criteria-result-table tbody tr.criteria-dragging {{ opacity:.45; }} .criteria-result-table tbody tr.criteria-drag-over {{ box-shadow:inset 0 2px 0 #1F80A0; }}
      .criteria-result-table tbody tr:hover {{ background:#fafcff; }} .criteria-result-empty td {{ text-align:center;color:rgba(0,0,0,.35);padding:22px 10px; }}
      .criteria-drag-handle {{ display:inline-block;margin-right:7px;color:rgba(0,0,0,.28);font-size:13px;letter-spacing:-2px;cursor:grab; }}
      .criteria-result-table .result-degree:disabled {{ background:#f5f5f5;color:rgba(0,0,0,.45);border-color:#d9d9d9;cursor:not-allowed;opacity:1;pointer-events:none;user-select:none; }}
      .criteria-result-type {{ min-width:0; }}
      .criteria-completion-tip {{ display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;border:1px solid #a9cbd4;border-radius:50%;color:#1F80A0;font-size:10px;font-weight:500;cursor:help; }}
      .criteria-result-add-actions {{ display:flex;gap:18px;margin-top:10px; }}
      .criteria-add-result {{ display:inline-block; }}
      .criteria-add-metric {{ display:inline-block; margin-top:10px; }}
      .criteria-preview-mask[hidden] {{ display:none; }}
      .criteria-preview-mask {{ position:fixed;inset:0;z-index:1500;background:rgba(0,0,0,.38);display:flex;align-items:center;justify-content:center; }}
      .criteria-preview-dialog {{ width:560px;max-width:calc(100vw - 32px);max-height:calc(100vh - 48px);overflow:auto;background:#fff;border-radius:9px;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.2);box-sizing:border-box; }}
      .criteria-preview-dialog h3 {{ margin:0 0 20px; }}
      .criteria-preview-dialog .hmi-result-section,.criteria-preview-dialog .hmi-metric-section {{ padding:14px 16px;border:1px solid #edf0f3;border-radius:7px;margin-bottom:14px; }}
      .criteria-preview-dialog .hmi-result-section {{ background:#f6f9ff; }}
      .criteria-preview-dialog .hmi-metric-section {{ background:#fafafa; }}
      .criteria-preview-dialog h4 {{ margin:0 0 12px;font-size:14px; }}
      .criteria-preview-dialog .hmi-result-radios {{ display:flex;gap:18px;flex-wrap:wrap; }}
      .criteria-preview-dialog .hmi-result-radios label {{ display:flex;align-items:center;gap:5px;color:#3f4752;font-size:13px; }}
      .criteria-preview-dialog .hmi-metric-section label {{ display:flex;flex-direction:column;gap:7px;margin-bottom:12px;color:#5f6670;font-size:13px; }}
      .criteria-preview-dialog .hmi-metric-section label:last-child {{ margin-bottom:0; }}
      .criteria-preview-dialog .hmi-metric-label {{ display:flex;align-items:center;gap:6px; }}
      .criteria-preview-dialog .hmi-metric-tip {{ display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;border:1px solid #a9cbd4;border-radius:50%;color:#1F80A0;font-size:10px;line-height:1;cursor:help; }}
      .criteria-preview-dialog select,.criteria-preview-dialog input[type="text"],.criteria-preview-dialog input[type="number"] {{ width:100%;height:38px;border:1px solid #d9dde3;border-radius:6px;padding:0 10px;background:#fff;box-sizing:border-box; }}
      .criteria-preview-dialog input[type="radio"],.criteria-preview-dialog input[type="checkbox"] {{ accent-color:#2463eb; }}
      .criteria-preview-multi {{ margin-bottom:12px; }}
      .criteria-preview-multi-title {{ display:block;margin-bottom:8px;color:#5f6670;font-size:13px; }}
      .criteria-preview-options {{ display:flex;gap:16px;flex-wrap:wrap;padding:9px 10px;border:1px solid #d9dde3;border-radius:6px;background:#fff; }}
      .criteria-preview-dialog .criteria-preview-options label {{ display:flex;flex-direction:row;align-items:center;gap:5px;margin:0;color:#3f4752; }}
      .criteria-preview-empty {{ color:rgba(0,0,0,.35);font-size:13px;padding:4px 0; }}
      .criteria-preview-actions {{ display:flex;justify-content:flex-end;gap:8px;margin-top:20px; }}
      .criteria-preview-actions button {{ padding:8px 18px;border:1px solid #d9dde3;background:#fff;border-radius:6px;cursor:pointer; }}
      .criteria-preview-actions button.primary {{ background:#2463eb;border-color:#2463eb;color:#fff; }}
    </style>
    <script>
    var criteriaViewData = {criteria_view_data};
    function criteriaMetricRow(metric) {{
      metric = metric || {{}};
      var tr = document.createElement('tr');
      tr.className = 'criteria-metric-row';
      tr.innerHTML = '<td><input class="ant-input" name="metric_name" placeholder="请输入指标名称"></td><td><select class="ant-input metric-type" name="metric_type" onchange="criteriaMetricTypeChange(this)"><option>文本</option><option>单选</option><option>多选</option><option>数字</option></select></td><td><input class="ant-input metric-options" name="metric_options" placeholder="逗号分隔选项" disabled oninput="criteriaMetricOptionsChange(this)"></td><td class="metric-default-cell"><input class="ant-input" name="metric_default" placeholder="请输入默认值"></td><td><input class="ant-input" name="metric_description" placeholder="请输入指标说明"></td><td><a href="javascript:void(0)" class="action-link" onclick="criteriaRemoveMetric(this)">删除</a></td>';
      document.querySelector('.criteria-drawer-content #criteria-metrics-table tbody').appendChild(tr);
      tr.querySelector('[name="metric_name"]').value = metric.name || metric.metric_name || '';
      tr.querySelector('[name="metric_description"]').value = metric.description || metric.metric_description || '';
      tr.querySelector('[name="metric_type"]').value = metric.type || metric.metric_type || '文本';
      tr.querySelector('[name="metric_options"]').value = Array.isArray(metric.options) ? metric.options.join(',') : (metric.options || '');
      criteriaMetricTypeChange(tr.querySelector('[name="metric_type"]'));
      var defaultControl = tr.querySelector('[name="metric_default"]');
      if (defaultControl) {{
        var defaultValue = Array.isArray(metric.default_value) ? metric.default_value : (metric.default_value || metric.default || '');
        if (defaultControl.multiple) {{
          var selectedDefaults = Array.isArray(defaultValue) ? defaultValue : String(defaultValue).split(',').map(function(v) {{ return v.trim(); }}).filter(Boolean);
          Array.from(defaultControl.options).forEach(function(option) {{ option.selected = selectedDefaults.indexOf(option.value) >= 0; }});
        }} else defaultControl.value = Array.isArray(defaultValue) ? defaultValue[0] || '' : defaultValue;
      }}
      return tr;
    }}
    function criteriaAddMetric() {{ criteriaMetricRow({{}}); }}
    function criteriaMetricTypeChange(select) {{
      var options = select.closest('tr').querySelector('.metric-options');
      var needsOptions = select.value === '单选' || select.value === '多选';
      options.disabled = !needsOptions;
      if (!needsOptions) options.value = '';
      criteriaRenderMetricDefault(select.closest('tr'));
    }}
    function criteriaMetricOptionsChange(input) {{ criteriaRenderMetricDefault(input.closest('tr')); }}
    function criteriaRenderMetricDefault(row) {{
      var type = row.querySelector('.metric-type').value;
      var cell = row.querySelector('.metric-default-cell');
      if (type === '单选' || type === '多选') {{
        var values = row.querySelector('.metric-options').value.split(',').map(function(v) {{ return v.trim(); }}).filter(Boolean);
        var multiAttr = type === '多选' ? ' multiple size="1"' : '';
        cell.innerHTML = '<select class="ant-input metric-default-select" name="metric_default"' + multiAttr + '><option value="">请选择默认值</option>' + values.map(function(v) {{ return '<option value="' + v.replace(/"/g, '&quot;') + '">' + v + '</option>'; }}).join('') + '</select>';
      }} else {{
        var inputType = type === '数字' ? 'number' : 'text';
        cell.innerHTML = '<input class="ant-input" type="' + inputType + '" name="metric_default" placeholder="请输入默认值">';
      }}
    }}
    function criteriaRemoveMetric(btn) {{ var row = btn.closest('tr'); if (row) row.remove(); }}
    function criteriaPreviewControlValue(control) {{
      if (!control) return '';
      if (control.multiple) return Array.from(control.selectedOptions).map(function(option) {{ return option.value; }}).filter(Boolean);
      return control.value || '';
    }}
    function criteriaPreviewMetricHtml(row, index) {{
      var name = row.querySelector('[name="metric_name"]').value.trim();
      if (!name) return '';
      var descriptionControl = row.querySelector('[name="metric_description"]');
      var description = descriptionControl ? descriptionControl.value.trim() : '';
      var metricLabel = criteriaEscape(name) + (description ? ' <span class="hmi-metric-tip" tabindex="0" data-tip="' + criteriaEscape(description) + '">i</span>' : '');
      var type = row.querySelector('[name="metric_type"]').value;
      var optionsControl = row.querySelector('[name="metric_options"]');
      var options = (optionsControl ? optionsControl.value : '').split(',').map(function(value) {{ return value.trim(); }}).filter(Boolean);
      var defaultValue = criteriaPreviewControlValue(row.querySelector('[name="metric_default"]'));
      var defaults = Array.isArray(defaultValue) ? defaultValue : [String(defaultValue)];
      var fieldName = 'criteria-preview-metric-' + index;
      if (type === '单选') {{
        var optionHtml = '<option value="">请选择</option>' + options.map(function(option) {{ return '<option' + (defaults.indexOf(option) >= 0 ? ' selected' : '') + '>' + criteriaEscape(option) + '</option>'; }}).join('');
        return '<label><span class="hmi-metric-label">' + metricLabel + '</span><select name="' + fieldName + '">' + optionHtml + '</select></label>';
      }}
      if (type === '多选') {{
        var checkboxHtml = options.map(function(option) {{ return '<label><input type="checkbox" name="' + fieldName + '" value="' + criteriaEscape(option) + '"' + (defaults.indexOf(option) >= 0 ? ' checked' : '') + '>' + criteriaEscape(option) + '</label>'; }}).join('');
        return '<div class="criteria-preview-multi"><span class="criteria-preview-multi-title hmi-metric-label">' + metricLabel + '</span><div class="criteria-preview-options">' + (checkboxHtml || '<span class="criteria-preview-empty">暂无可选项</span>') + '</div></div>';
      }}
      var inputType = type === '数字' ? 'number' : 'text';
      var placeholder = type === '数字' ? '请输入数字' : '请输入';
      return '<label><span class="hmi-metric-label">' + metricLabel + '</span><input type="' + inputType + '" name="' + fieldName + '" value="' + criteriaEscape(defaults[0] || '') + '" placeholder="' + placeholder + '"></label>';
    }}
    function openCriteriaPreview() {{
      var drawer = document.querySelector('.criteria-drawer-content');
      var results = Array.from(drawer.querySelectorAll('#criteria-result-table [name="result_type"]')).map(function(input) {{ return input.value.trim(); }}).filter(Boolean);
      var resultRoot = document.getElementById('criteria-preview-results');
      resultRoot.innerHTML = results.length ? results.map(function(result, index) {{ return '<label><input type="radio" name="criteria-preview-result" value="' + criteriaEscape(result) + '"' + (index === 0 ? ' checked' : '') + '>' + criteriaEscape(result) + '</label>'; }}).join('') : '<span class="criteria-preview-empty">暂无评测结果</span>';
      var metricRows = Array.from(drawer.querySelectorAll('#criteria-metrics-table tbody tr.criteria-metric-row'));
      var metricsHtml = metricRows.map(criteriaPreviewMetricHtml).filter(Boolean).join('');
      document.getElementById('criteria-preview-metrics').innerHTML = metricsHtml || '<div class="criteria-preview-empty">暂无评测指标</div>';
      document.getElementById('criteria-preview-mask').hidden = false;
    }}
    function criteriaClosePreview() {{ document.getElementById('criteria-preview-mask').hidden = true; }}
    function criteriaPreviewSubmit() {{
      criteriaClosePreview();
      if (window.showToast) window.showToast('当前为预览模式，不会提交数据', 'info');
    }}
    var criteriaDraggingRow = null;
    function criteriaBindResultDrag(tr) {{
      tr.draggable = true;
      tr.addEventListener('dragstart', function(event) {{
        criteriaDraggingRow = tr;
        tr.classList.add('criteria-dragging');
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', 'criteria-result');
      }});
      tr.addEventListener('dragover', function(event) {{
        event.preventDefault();
        if (!criteriaDraggingRow || criteriaDraggingRow === tr) return;
        var body = tr.parentElement;
        var rect = tr.getBoundingClientRect();
        tr.classList.toggle('criteria-drag-over', true);
        if (event.clientY < rect.top + rect.height / 2) body.insertBefore(criteriaDraggingRow, tr);
        else body.insertBefore(criteriaDraggingRow, tr.nextSibling);
        criteriaRenumberResults();
      }});
      tr.addEventListener('dragleave', function() {{ tr.classList.remove('criteria-drag-over'); }});
      tr.addEventListener('drop', function(event) {{ event.preventDefault(); tr.classList.remove('criteria-drag-over'); criteriaRenumberResults(); }});
      tr.addEventListener('dragend', function() {{ tr.classList.remove('criteria-dragging'); document.querySelectorAll('.criteria-drag-over').forEach(function(row) {{ row.classList.remove('criteria-drag-over'); }}); criteriaDraggingRow = null; criteriaRenumberResults(); }});
    }}
    function criteriaResultRow(resultType, item) {{
      item = item || {{}};
      var tr = document.createElement('tr'); tr.className = 'criteria-result-row';
      tr.dataset.resultType = resultType || '';
      var degree = item.degree || 1;
      tr.innerHTML = '<td><div style="display:flex;align-items:center;"><span class="criteria-drag-handle" aria-hidden="true">⋮⋮</span><input class="ant-input criteria-result-type" name="result_type" maxlength="20" required placeholder="请输入结果类型，最多20个字符" value="' + criteriaEscape(resultType) + '"></div></td><td><input class="ant-input result-degree" type="number" value="' + degree + '" disabled readonly tabindex="-1" aria-readonly="true" aria-label="完成度"><input type="hidden" class="result-degree-value" name="result_degree" value="' + degree + '"></td><td><a href="javascript:void(0)" class="action-link danger" onclick="criteriaRemoveResultRow(this)">删除</a></td>';
      document.querySelector('#criteria-result-table tbody').appendChild(tr);
      tr.querySelector('[name="result_type"]').addEventListener('input', function() {{ tr.dataset.resultType = this.value; }});
      criteriaBindResultDrag(tr);
      return tr;
    }}
    function criteriaEscape(value) {{ return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }}
    function criteriaRenumberResults() {{
      var rows = Array.from(document.querySelectorAll('#criteria-result-table tbody tr.criteria-result-row'));
      rows.forEach(function(row, index) {{ var value = rows.length - index; var degree = row.querySelector('.result-degree'); var hidden = row.querySelector('.result-degree-value'); if (degree) degree.value = value; if (hidden) hidden.value = value; }});
    }}
    function criteriaSortResults() {{
      var body = document.querySelector('#criteria-result-table tbody'); if (!body) return;
      Array.from(body.querySelectorAll('tr.criteria-result-row')).sort(function(a, b) {{
        return Number(b.querySelector('.result-degree').value || 0) - Number(a.querySelector('.result-degree').value || 0);
      }}).forEach(function(row) {{ body.appendChild(row); }});
    }}
    function criteriaAddResultRow() {{
      var tr = criteriaResultRow('', {{degree: 1}});
      criteriaRenumberResults();
      criteriaSortResults();
      tr.querySelector('[name="result_type"]').focus();
    }}
    function criteriaRemoveResultRow(btn) {{ var row = btn.closest('tr'); if (row) row.remove(); criteriaRenumberResults(); criteriaSortResults(); }}
    function criteriaResetRows(definitions) {{
      var body = document.querySelector('#criteria-result-table tbody'); if (!body) return;
      body.innerHTML = '';
      definitions = definitions || [];
      var items = Array.isArray(definitions) ? definitions.slice() : [];
      if (!items.length) items = [{{type:'', degree:1}}];
      items.sort(function(a, b) {{ return Number(b.degree || 0) - Number(a.degree || 0); }});
      items.forEach(function(item) {{ criteriaResultRow(item.type || '', item); }});
      criteriaRenumberResults();
      criteriaSortResults();
    }}
    function criteriaResetMetrics(metrics) {{
      var body = document.querySelector('.criteria-drawer-content #criteria-metrics-table tbody'); if (!body) return;
      body.innerHTML = '';
      (metrics && metrics.length ? metrics : [{{}}]).forEach(function(metric) {{ criteriaMetricRow(metric); }});
    }}
    function setCriteriaDrawerReadonly(readonly) {{
      var drawer = document.getElementById('create-criteria-drawer');
      drawer.querySelector('h3').textContent = readonly ? '查看评价标准' : '新增评价标准';
      drawer.querySelectorAll('input, textarea, select').forEach(function(el) {{
        // 完成度由系统按结果顺序自动生成，任何模式下都不可编辑；隐藏值仍需保持可提交。
        if (el.classList.contains('result-degree')) {{
          el.disabled = true;
          el.readOnly = true;
          el.tabIndex = -1;
          el.setAttribute('aria-readonly', 'true');
        }} else {{
          el.disabled = readonly;
        }}
      }});
      drawer.querySelectorAll('.criteria-add-result, .criteria-add-metric').forEach(function(el) {{ el.style.display = readonly ? 'none' : ''; }});
      drawer.querySelectorAll('.criteria-result-row .action-link, .criteria-metric-row .action-link').forEach(function(el) {{ el.style.display = readonly ? 'none' : ''; }});
      var submit = drawer.querySelector('button[type="submit"]'); if (submit) submit.style.display = readonly ? 'none' : '';
      var cancel = drawer.querySelector('.ant-drawer-footer button[type="button"]'); if (cancel) cancel.textContent = '关闭';
    }}
    function openCriteriaCreate() {{
      var drawer = document.getElementById('create-criteria-drawer');
      drawer.querySelector('form').reset();
      criteriaResetRows({{}}); criteriaResetMetrics([]); setCriteriaDrawerReadonly(false);
      document.getElementById('criteria-publish-status-field').style.display = 'none';
      drawer.querySelector('h3').textContent = '新增评价标准';
      drawer.querySelector('button[type="submit"]').textContent = '创建';
      openModal('create-criteria-drawer');
    }}
    function openCriteriaView(id) {{
      var data = criteriaViewData[id]; if (!data) return;
      var drawer = document.getElementById('create-criteria-drawer');
      drawer.querySelector('form').reset();
      drawer.querySelector('[name="name"]').value = data.name || '';
      drawer.querySelector('[name="description"]').value = data.description || '';
      drawer.querySelector('[name="publish_status"]').value = data.publish_status || '未发布';
      document.getElementById('criteria-publish-status-field').style.display = '';
      criteriaResetRows(data.result_definitions || {{}}); criteriaResetMetrics(data.metrics || []); setCriteriaDrawerReadonly(true); openModal('create-criteria-drawer');
    }}
    function openCriteriaEdit(id) {{
      openCriteriaView(id);
      var drawer = document.getElementById('create-criteria-drawer');
      setCriteriaDrawerReadonly(false);
      drawer.querySelector('[name="edit_id"]').value = id;
      drawer.querySelector('h3').textContent = '编辑评价标准';
      drawer.querySelector('button[type="submit"]').textContent = '保存';
    }}
    document.addEventListener('DOMContentLoaded', function() {{ criteriaResetRows({{}}); criteriaResetMetrics([]); }});
    </script>
    <style>
      .criteria-list-card {{ position:relative; z-index:10; overflow:visible; }}
      .criteria-list-card .ant-table,
      .criteria-list-card .actions-cell {{ overflow:visible; }}
      .criteria-list-card .action-more-wrap {{ position:relative; z-index:60; }}
      .criteria-list-card .action-more-menu {{ top:auto; bottom:calc(100% + 4px); z-index:120; }}
    </style>
    '''
    return render_page("\u8bc4\u4ef7\u6807\u51c6\u7ba1\u7406", content, active="criteria")


@app.route("/criteria/create", methods=["POST"])
def criteria_create():
    name = request.form.get("name", "").strip()
    edit_id = request.form.get("edit_id", "").strip()
    edit_target = next((item for item in CRITERIA if item["id"] == edit_id), None) if edit_id else None
    ctype = edit_target.get("type", "preference") if edit_target else request.form.get("type", "preference")
    desc = request.form.get("description", "")
    type_prompt = request.form.get("type_prompt", "")
    scale_name = request.form.get("scale_name", "")
    scale_range = request.form.get("scale_range", "")
    scale_desc = request.form.get("scale_desc", "")
    note = request.form.get("note", "").strip() or None
    result_types = request.form.getlist("result_type")
    result_degrees = request.form.getlist("result_degree")
    result_definitions = []
    for index, result_type in enumerate(result_types):
        result_type = result_type.strip()
        if len(result_type) > 20:
            flash("结果类型不能超过 20 个字符", "error")
            return redirect(url_for("criteria_page"))
        if result_type:
            degree = result_degrees[index] if index < len(result_degrees) else len(result_definitions) + 1
            result_definitions.append({"type": result_type, "degree": degree})
    # Backward-compatible fallback for callers that still submit the old comma-separated fields.
    if not result_definitions:
        legacy_values = [
            x.strip()
            for field in ("success_definitions", "failure_definitions")
            for x in request.form.get(field, "").replace("，", ",").split(",")
            if x.strip()
        ]
        result_definitions = [
            {"type": value[:20], "degree": len(legacy_values) - index}
            for index, value in enumerate(legacy_values)
        ]
    if not result_definitions:
        flash("请至少配置一个结果类型", "error")
        return redirect(url_for("criteria_page"))
    result_definitions = normalize_result_definitions(result_definitions)

    metric_names = request.form.getlist("metric_name")
    metric_descriptions = request.form.getlist("metric_description")
    metric_types = request.form.getlist("metric_type")
    metric_options = request.form.getlist("metric_options")
    metric_defaults = request.form.getlist("metric_default")
    metrics = []
    for index, metric_name in enumerate(metric_names):
        metric_name = metric_name.strip()
        if not metric_name:
            continue
        description = metric_descriptions[index].strip() if index < len(metric_descriptions) else ""
        metric_type = metric_types[index] if index < len(metric_types) else "文本"
        options = [x.strip() for x in (metric_options[index] if index < len(metric_options) else "").replace("，", ",").split(",") if x.strip()]
        default_value = metric_defaults[index] if index < len(metric_defaults) else ""
        metrics.append({"name": metric_name, "description": description, "type": metric_type, "options": options, "default_value": default_value})
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
    criterion_payload = {
        "name": name, "type": ctype, "description": desc,
        "publish_status": request.form.get("publish_status", "未发布") if request.form.get("publish_status") in ("未发布", "已发布") else "未发布",
        "result_definitions": result_definitions,
        "metrics": metrics,
        "form": {
            "type_module": {"items": [type_item]},
            "scale_module": {"items": scale_items},
            "note": note,
        },
    }
    if edit_target and edit_target.get("publish_status") == "未发布":
        edit_target.update(criterion_payload)
        flash(f"评价标准「{name}」保存成功", "success")
    elif edit_id:
        flash("仅未发布状态的评价标准支持编辑", "error")
    else:
        new_id = f"c{len(CRITERIA)+1}"
        CRITERIA.append({
            "id": new_id,
            "creator": "Joanna Qiao",
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "publish_status": "未发布",
            **criterion_payload,
        })
        flash(f"\u8bc4\u4ef7\u6807\u51c6\u300c{name}\u300d\u521b\u5efa\u6210\u529f", "success")
    return redirect(url_for("criteria_page"))


@app.route("/criteria/<cid>/publish")
def criteria_publish(cid):
    criterion = next((item for item in CRITERIA if item["id"] == cid), None)
    if criterion and criterion.get("publish_status") == "未发布":
        criterion["publish_status"] = "已发布"
        flash(f"评价标准「{criterion['name']}」已发布", "success")
    return redirect(url_for("criteria_page"))


@app.route("/criteria/<cid>/delete")
def criteria_delete(cid):
    criterion = next((item for item in CRITERIA if item["id"] == cid), None)
    if criterion and criterion.get("publish_status") == "未发布":
        CRITERIA.remove(criterion)
        flash(f"评价标准「{criterion['name']}」已删除", "success")
    elif criterion:
        flash("已发布状态的评价标准不支持删除", "error")
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
    definitions = normalize_result_definitions(c.get("result_definitions", {}))
    result_definition_rows = "".join(
        f'<tr><td><span class="criteria-readonly-result">{html.escape(item["type"])}</span></td><td>{item["degree"]}</td></tr>'
        for item in definitions
    ) or '<tr><td colspan="2" class="criteria-readonly-empty">暂无评测结果</td></tr>'
    metric_data = get_criterion_metrics(c) or [
        {"name": item.get("metric_name", "--"), "type": "数字", "options": [], "default_value": f'{item.get("score_range", {}).get("min", 0)} ~ {item.get("score_range", {}).get("max", 5)}'}
        for item in scale_items
    ]
    metric_rows = "".join(
        f'<tr><td>{html.escape(str(item.get("name", item.get("metric_name", "--"))))}</td><td>{html.escape(str(item.get("description", item.get("metric_description", ""))) or "--")}</td><td>{html.escape(str(item.get("type", "文本")))}</td><td>{html.escape(", ".join(item.get("options", [])) if isinstance(item.get("options", []), list) else str(item.get("options", "--")))}</td><td>{html.escape(str(item.get("default_value", item.get("default", ""))) or "--")}</td></tr>'
        for item in metric_data
    ) or '<tr><td colspan="5" class="criteria-readonly-empty">暂无评测指标</td></tr>'

    content = f'''
    <div class="criteria-readonly-page">
      <div class="criteria-readonly-top"><a href="/criteria" class="action-link">&larr; 返回评价标准</a><span>查看评价标准</span></div>
      <div class="criteria-readonly-drawer">
        <div class="ant-drawer-header"><h3>查看评价标准</h3></div>
        <div class="criteria-readonly-body">
          <div class="form-group"><label>标准名称</label><input class="ant-input" value="{html.escape(c.get("name", ""), quote=True)}" disabled></div>
          <div class="form-group"><label>描述</label><textarea class="ant-input" rows="3" disabled>{html.escape(c.get("description", ""))}</textarea></div>
          <hr style="border:none;border-top:1px solid #f0f0f0;margin:20px 0;">
          <div class="form-group"><label>评测结果</label><table class="ant-table criteria-result-table criteria-readonly-table"><thead><tr><th>结果类型</th><th>完成度</th></tr></thead><tbody>{result_definition_rows}</tbody></table></div>
          <div class="form-group"><label>评测指标</label><table class="ant-table criteria-metrics-table criteria-readonly-table"><thead><tr><th>指标名称</th><th>指标说明</th><th>字段类型</th><th>字段值</th><th>默认值</th></tr></thead><tbody>{metric_rows}</tbody></table></div>
          {('<div class="form-group"><label>备注</label><textarea class="ant-input" rows="2" disabled>' + html.escape(form.get("note", "")) + '</textarea></div>') if form.get("note") else ''}
        </div>
        <div class="ant-drawer-footer"><a href="/criteria" class="ant-btn">关闭</a></div>
      </div>
    </div>
    '''
    content += '''<style>
      .criteria-readonly-page { max-width:1000px; margin:0 auto; }
      .criteria-readonly-top { display:flex; align-items:center; gap:12px; margin-bottom:14px; color:rgba(0,0,0,.55); font-size:13px; }
      .criteria-readonly-drawer { background:#fff; border:1px solid #e6ebef; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,.04); }
      .criteria-readonly-body { padding:20px 24px; }
      .criteria-readonly-body .form-group { margin-bottom:16px; }
      .criteria-readonly-body .ant-input[disabled] { color:rgba(0,0,0,.72); background:#fafafa; cursor:default; }
      .criteria-readonly-table { margin-top:8px; }
      .criteria-readonly-table th,.criteria-readonly-table td { padding:9px 10px; }
      .criteria-readonly-result { display:inline-flex; padding:3px 9px; border-radius:4px; font-size:12px; color:#23677a; background:#eef8fa; }
      .criteria-readonly-empty { text-align:center; color:rgba(0,0,0,.35); padding:20px !important; }
    </style>'''
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

        view_btn = f'<a href="/scenes/{sc["id"]}" class="action-link">查看</a>'
        copy_btn = '<a href="#" class="action-link">复制</a>'
        del_btn = '<a href="#" class="action-link danger">删除</a>'

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
    <div class="filter-bar fb-labeled">
      <div class="ff"><label>\u573a\u666f\u540d\u79f0</label><input type="text" placeholder="\u641c\u7d22\u573a\u666f\u540d\u79f0"></div>
      <div class="filter-actions">
        <button class="ant-btn" onclick="clearFilters()">\u6e05\u7a7a</button>
        <button class="ant-btn ant-btn-primary" onclick="doSearch()">\u641c\u7d22</button>
      </div>
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
@app.route("/benchmarks/prompt-search")
def benchmark_prompt_search():
    query = request.args.get("q", "").strip().casefold()
    if not query:
        return jsonify({"items": []})

    items = []
    for prompt in PROMPTS:
        searchable_values = [
            prompt.get("high_level", ""),
            prompt.get("high_level_en", ""),
        ]
        for child in prompt.get("low_levels", []):
            searchable_values.extend((child.get("zh", ""), child.get("en", "")))
        if query not in " ".join(str(value) for value in searchable_values).casefold():
            continue
        items.append({
            "id": prompt["id"],
            "name": prompt.get("high_level", ""),
            "name_en": prompt.get("high_level_en", ""),
            "step_count": len(prompt.get("low_levels", [])),
        })
        if len(items) >= 20:
            break
    return jsonify({"items": items})


@app.route("/benchmarks")
def benchmarks_page():
    benchmark_filter = request.args.get("name", "").strip()
    prompt_filter_id = request.args.get("prompt_id", "").strip()
    prompt_filter_name = request.args.get("prompt_name", "").strip()
    publish_status_filter = request.args.get("publish_status", "").strip()
    selected_prompt = get_prompt(prompt_filter_id) if prompt_filter_id else None
    if selected_prompt:
        prompt_filter_name = selected_prompt.get("high_level", "")
    rows = ""
    for b in BENCHMARKS:
        if benchmark_filter and benchmark_filter.lower() not in b.get("name", "").lower():
            continue
        if prompt_filter_id and prompt_filter_id not in b.get("prompt_ids", []):
            continue
        if publish_status_filter and publish_status_filter != b.get("publish_status", "已发布"):
            continue
        prompt_count = len(b.get("prompt_ids", []))
        prompt_tags = ""
        for pid in b.get("prompt_ids", [])[:3]:
            p = get_prompt(pid)
            if p:
                prompt_tags += f'<span class="ant-tag" style="margin-right:2px;">{p["high_level"][:8]}</span>'
        if prompt_count > 3:
            prompt_tags += f'<span class="ant-tag">+{prompt_count-3}</span>'

        publish_status = b.get("publish_status", "已发布")
        is_unpublished = publish_status == "未发布"
        status_class = "tag-gray" if is_unpublished else "tag-green"
        view_btn = f'<a href="javascript:void(0)" class="action-link" onclick="openBenchmarkView(\'{b["id"]}\')">查看</a>'
        edit_btn = f'<a href="javascript:void(0)" class="action-link" onclick="openBenchmarkEdit(\'{b["id"]}\')">编辑</a>' if is_unpublished else ''
        publish_btn = f'<a href="/benchmarks/{b["id"]}/publish" class="action-link" onclick="return confirm(\'发布后将不能编辑或删除，确认发布吗？\')">发布</a>' if is_unpublished else ''
        copy_btn = '<a href="#" class="action-link" onclick="toast(\'已复制评测集\');return false;">复制</a>'
        del_btn = f'<a href="/benchmarks/{b["id"]}/delete" class="action-link danger" onclick="return confirm(\'确认删除该评测集吗？\')">删除</a>' if is_unpublished else ''
        more_btn = f'<span class="action-more-wrap"><a href="javascript:void(0)" class="action-link">更多</a><span class="action-more-menu">{edit_btn}{del_btn}</span></span>' if is_unpublished else ''
        actions_html = view_btn + copy_btn + publish_btn + more_btn

        rows += (
            "<tr>"
            f'<td style="font-weight:500;">{b["name"]}</td>'
            f"<td>{prompt_tags}</td>"
            f'<td><span class="tag {status_class}">{publish_status}</span></td>'
            f"<td>{b['creator']}</td>"
            f"<td>{b['created_at']}</td>"
            f'<td class="actions-cell">{actions_html}</td>'
            "</tr>"
        )

    benchmark_tag_tree = build_tree_selector_html("benchmark-tags")
    bm_create_prompt_ms_opts = "".join(
        f'<label class="er-opt"><input type="checkbox" value="{p["id"]}" data-name="{p["high_level"]}" onchange="mselSync(\'ms-bm-prompts\')"> <span>{p["high_level"]} &middot; {len(p.get("low_levels", []))} \u6b65</span></label>'
        for p in PROMPTS
    )
    import json as _json
    bm_prompt_tree_data = _json.dumps([
        {
            "id": p["id"],
            "name": p["high_level"],
            "children": [
                {"id": ll["id"], "zh": ll.get("zh", ""), "en": ll.get("en", "")}
                for ll in p.get("low_levels", [])
            ] or [{"id": p["id"], "zh": p["high_level"], "en": p.get("high_level_en", "")}],
        }
        for p in PROMPTS
    ], ensure_ascii=False)
    benchmark_view_data = _json.dumps({
        b["id"]: {
            "name": b.get("name", ""),
            "description": b.get("description", ""),
            "tags": b.get("tags", []),
            "prompt_ids": b.get("prompt_ids", []),
            "execution_prompt_ids": b.get("execution_prompt_ids", []),
            "publish_status": b.get("publish_status", "已发布"),
        }
        for b in BENCHMARKS
    }, ensure_ascii=False)
    content = f'''
    <form class="filter-bar fb-labeled benchmark-filter-bar" method="get" action="/benchmarks">
      <div class="ff"><label>评测集</label><input type="text" name="name" value="{html.escape(benchmark_filter, quote=True)}" placeholder="\u641c\u7d22评测集"></div>
      <div class="ff benchmark-prompt-filter"><label>\u63d0\u793a\u8bcd</label>
        <div class="benchmark-remote-select" id="benchmark-prompt-remote">
          <input type="text" id="benchmark-prompt-input" name="prompt_name" value="{html.escape(prompt_filter_name, quote=True)}" placeholder="请输入关键词搜索提示词组" autocomplete="off" oninput="benchmarkPromptRemoteInput(this.value)" onfocus="benchmarkPromptRemoteFocus()">
          <input type="hidden" id="benchmark-prompt-id" name="prompt_id" value="{html.escape(prompt_filter_id, quote=True)}">
          <div class="benchmark-remote-panel" id="benchmark-prompt-panel" hidden></div>
        </div>
      </div>
      <div class="ff"><label>状态</label><select name="publish_status"><option value="">全部状态</option><option value="未发布"{' selected' if publish_status_filter == '未发布' else ''}>未发布</option><option value="已发布"{' selected' if publish_status_filter == '已发布' else ''}>已发布</option></select></div>
      <div class="filter-actions">
        <a class="ant-btn" href="/benchmarks">\u6e05\u7a7a</a>
        <button class="ant-btn ant-btn-primary" type="submit">\u641c\u7d22</button>
      </div>
      <div style="flex:1;"></div>
      <button class="ant-btn ant-btn-primary" type="button" onclick="openBenchmarkCreate()">\u65b0\u589e评测集</button>
    </form>

    <div class="ant-card ant-card-bordered benchmark-list-card">
      <table class="ant-table">
        <thead><tr>
          <th>\u540d\u79f0</th><th>\u63d0\u793a\u8bcd</th><th>状态</th><th>\u521b\u5efa\u4eba</th><th>\u521b\u5efa\u65f6\u95f4</th><th>\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <!-- Create Benchmark Drawer -->
    <div class="ant-drawer-mask" id="create-bm-drawer">
      <div class="ant-drawer-content benchmark-drawer-content">
        <div class="ant-drawer-header"><h3>\u65b0\u589e评测集</h3><button class="ant-drawer-close" onclick="closeModal('create-bm-drawer')">&times;</button></div>
        <form method="POST" action="/benchmarks/create">
        <input type="hidden" name="edit_id" value="">
        <div class="ant-drawer-body">
          <!-- Section 1: Basic Info -->
          <h4 style="font-size:14px;font-weight:500;margin-bottom:12px;color:rgba(0,0,0,0.85);">\u57fa\u672c\u4fe1\u606f</h4>
          <div class="form-group"><label>\u540d\u79f0</label><input type="text" name="name" required></div>
          <div class="form-group"><label>\u63cf\u8ff0</label><textarea name="description" rows="2"></textarea></div>
          <div class="form-group" id="benchmark-publish-status-field" style="display:none;"><label>状态</label><select name="publish_status"><option value="未发布">未发布</option><option value="已发布">已发布</option></select></div>
          <div class="form-group">
            <label>\u6807\u7b7e</label>
            <div class="ts-wrap benchmark-tag-select" id="ts-benchmark-tags">
              <div class="ts-trigger" onclick="benchmarkTagsToggle(event)"><span class="ts-placeholder">请选择标签</span></div>
              <div class="ts-panel">{benchmark_tag_tree}</div>
              <input type="hidden" name="tags" id="benchmark-tags-hidden" value="">
            </div>
          </div>

          <hr style="border:none;border-top:1px solid #f0f0f0;margin:20px 0;">

          <h4 style="font-size:14px;font-weight:500;margin-bottom:12px;color:rgba(0,0,0,0.85);">\u63d0\u793a\u8bcd\u914d\u7f6e</h4>
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
          <div id="bm-prompt-execution-tree" class="bm-prompt-execution-tree">
            <div class="bm-prompt-execution-empty">选择提示词组后配置实际执行内容</div>
          </div>
          <input type="hidden" name="execution_prompt_ids" id="bm-execution-prompt-ids" value="">
        </div>
        <div class="ant-drawer-footer">
          <button type="button" class="ant-btn" onclick="closeModal('create-bm-drawer')">\u53d6\u6d88</button>
          <button type="submit" class="ant-btn ant-btn-primary">\u521b\u5efa</button>
        </div>
        </form>
      </div>
    </div>
    <script>
    var benchmarkPromptData = {bm_prompt_tree_data};
    var benchmarkViewData = {benchmark_view_data};
    var benchmarkExecutionSelections = new Set();
    var benchmarkInitializedGroups = new Set();
    var benchmarkPromptRemoteTimer = null;
    var benchmarkPromptRemoteController = null;
    document.addEventListener('DOMContentLoaded', function() {{
      if (new URLSearchParams(window.location.search).get('open') === 'create' && typeof openModal === 'function') openModal('create-bm-drawer');
      benchmarkTagsInit();
      window.renderBenchmarkPromptExecutionTree();
    }});
    function setBenchmarkDrawerReadonly(readonly) {{
      var drawer = document.getElementById('create-bm-drawer');
      drawer.querySelector('h3').textContent = readonly ? '查看评测集' : '新增评测集';
      drawer.querySelectorAll('input, textarea, select').forEach(function(el) {{ el.disabled = readonly; }});
      drawer.querySelectorAll('.er-dd-trigger, .ts-trigger').forEach(function(el) {{ el.style.pointerEvents = readonly ? 'none' : ''; el.style.background = readonly ? '#fafafa' : ''; }});
      var submit = drawer.querySelector('button[type="submit"]'); if (submit) submit.style.display = readonly ? 'none' : '';
      var cancel = drawer.querySelector('.ant-drawer-footer button[type="button"]'); if (cancel) cancel.textContent = '关闭';
    }}
    function resetBenchmarkDrawer() {{
      var drawer = document.getElementById('create-bm-drawer');
      drawer.querySelector('form').reset();
      drawer.querySelectorAll('#ms-bm-prompts-panel input[type=checkbox]').forEach(function(cb) {{ cb.checked = false; }});
      benchmarkExecutionSelections.clear();
      var hidden = document.getElementById('bm-execution-prompt-ids'); if (hidden) hidden.value = '';
      var tagWrap = document.getElementById('ts-benchmark-tags');
      if (tagWrap) {{ tagWrap.querySelectorAll('.ts-row.selected').forEach(function(row) {{ row.classList.remove('selected'); }}); benchmarkTagsSync(); }}
      window.mselSync('ms-bm-prompts');
      window.renderBenchmarkPromptExecutionTree();
    }}
    function openBenchmarkCreate() {{
      resetBenchmarkDrawer(); setBenchmarkDrawerReadonly(false);
      var drawer = document.getElementById('create-bm-drawer');
      drawer.querySelector('h3').textContent = '新增评测集';
      drawer.querySelector('button[type="submit"]').textContent = '创建';
      document.getElementById('benchmark-publish-status-field').style.display = 'none';
      openModal('create-bm-drawer');
    }}
    function openBenchmarkView(id) {{
      var data = benchmarkViewData[id]; if (!data) return;
      resetBenchmarkDrawer();
      var drawer = document.getElementById('create-bm-drawer');
      drawer.querySelector('[name="name"]').value = data.name || '';
      drawer.querySelector('[name="description"]').value = data.description || '';
      drawer.querySelector('[name="publish_status"]').value = data.publish_status || '未发布';
      document.getElementById('benchmark-publish-status-field').style.display = '';
      var promptSet = new Set(data.prompt_ids || []);
      drawer.querySelectorAll('#ms-bm-prompts-panel input[type=checkbox]').forEach(function(cb) {{ cb.checked = promptSet.has(cb.value); }});
      var tagSet = new Set(data.tags || []);
      var tagWrap = document.getElementById('ts-benchmark-tags');
      if (tagWrap) {{ tagWrap.querySelectorAll('.ts-row[data-id]').forEach(function(row) {{ if (tagSet.has(row.dataset.id) || tagSet.has(row.dataset.path)) row.classList.add('selected'); }}); benchmarkTagsSync(); }}
      window.mselSync('ms-bm-prompts');
      setBenchmarkDrawerReadonly(true);
      openModal('create-bm-drawer');
    }}
    function openBenchmarkEdit(id) {{
      openBenchmarkView(id);
      var drawer = document.getElementById('create-bm-drawer');
      setBenchmarkDrawerReadonly(false);
      drawer.querySelector('[name="edit_id"]').value = id;
      drawer.querySelector('h3').textContent = '编辑评测集';
      drawer.querySelector('button[type="submit"]').textContent = '保存';
    }}
    function benchmarkPromptEscape(value) {{
      return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }}
    function benchmarkPromptRemoteInput(value) {{
      document.getElementById('benchmark-prompt-id').value = '';
      window.clearTimeout(benchmarkPromptRemoteTimer);
      var keyword = String(value || '').trim();
      if (!keyword) {{ benchmarkPromptRemoteClose(); return; }}
      benchmarkPromptRemoteTimer = window.setTimeout(function() {{ benchmarkPromptRemoteSearch(keyword); }}, 250);
    }}
    function benchmarkPromptRemoteFocus() {{
      var input = document.getElementById('benchmark-prompt-input');
      if (input && input.value.trim() && !document.getElementById('benchmark-prompt-id').value) benchmarkPromptRemoteInput(input.value);
    }}
    function benchmarkPromptRemoteSearch(keyword) {{
      var panel = document.getElementById('benchmark-prompt-panel');
      panel.hidden = false;
      panel.innerHTML = '<div class="benchmark-remote-state">搜索中...</div>';
      if (benchmarkPromptRemoteController) benchmarkPromptRemoteController.abort();
      benchmarkPromptRemoteController = new AbortController();
      fetch('/benchmarks/prompt-search?q=' + encodeURIComponent(keyword), {{ signal: benchmarkPromptRemoteController.signal }})
        .then(function(response) {{ return response.json(); }})
        .then(function(data) {{
          var items = data.items || [];
          if (!items.length) {{ panel.innerHTML = '<div class="benchmark-remote-state">未找到匹配的提示词组</div>'; return; }}
          panel.innerHTML = items.map(function(item) {{
            return '<button type="button" class="benchmark-remote-option" data-id="' + benchmarkPromptEscape(item.id) + '" data-name="' + benchmarkPromptEscape(item.name) + '" onclick="benchmarkPromptRemoteSelect(this)"><span class="benchmark-remote-name">' + benchmarkPromptEscape(item.name) + '</span><span class="benchmark-remote-meta">' + benchmarkPromptEscape(item.name_en) + ' · ' + item.step_count + ' 个 lowlevel</span></button>';
          }}).join('');
        }})
        .catch(function(error) {{ if (error.name !== 'AbortError') panel.innerHTML = '<div class="benchmark-remote-state">搜索失败，请重试</div>'; }});
    }}
    function benchmarkPromptRemoteSelect(option) {{
      document.getElementById('benchmark-prompt-input').value = option.dataset.name || '';
      document.getElementById('benchmark-prompt-id').value = option.dataset.id || '';
      benchmarkPromptRemoteClose();
    }}
    function benchmarkPromptRemoteClose() {{
      var panel = document.getElementById('benchmark-prompt-panel');
      panel.hidden = true;
      panel.innerHTML = '';
    }}
    window.renderBenchmarkPromptExecutionTree = function() {{
      var tree = document.getElementById('bm-prompt-execution-tree');
      var groupPanel = document.getElementById('ms-bm-prompts-panel');
      if (!tree || !groupPanel) return;
      var selectedGroups = Array.from(groupPanel.querySelectorAll('input[type=checkbox]:checked')).map(function(cb) {{ return cb.value; }});
      var selectedSet = new Set(selectedGroups);
      var activeChildren = new Set();
      var html = '';
      benchmarkPromptData.forEach(function(group) {{
        if (!selectedSet.has(group.id)) return;
        var children = group.children || [];
        children.forEach(function(child) {{
          activeChildren.add(child.id);
          benchmarkExecutionSelections.add(child.id);
        }});
        benchmarkInitializedGroups.add(group.id);
        html += '<div class="bm-prompt-execution-group" data-group-id="' + benchmarkPromptEscape(group.id) + '">';
        html += '<div class="bm-prompt-execution-group-head"><span>' + benchmarkPromptEscape(group.name) + '</span></div>';
        html += '<div class="bm-prompt-execution-steps">';
        children.forEach(function(child, index) {{
          html += '<div class="bm-prompt-execution-child"><span>' + (index + 1) + '. ' + benchmarkPromptEscape(child.zh) + '<span class="bm-prompt-execution-en">' + benchmarkPromptEscape(child.en) + '</span></span></div>';
        }});
        html += '</div></div>';
      }});
      benchmarkInitializedGroups.forEach(function(id) {{ if (!selectedSet.has(id)) benchmarkInitializedGroups.delete(id); }});
      benchmarkExecutionSelections.forEach(function(id) {{ if (!activeChildren.has(id)) benchmarkExecutionSelections.delete(id); }});
      if (!html) {{
        tree.innerHTML = '<div class="bm-prompt-execution-empty">选择提示词后在这里查看内容</div>';
      }} else {{
        tree.innerHTML = '<div class="bm-prompt-execution-head"><span class="bm-prompt-execution-title">提示词</span><span class="bm-prompt-execution-count" id="bm-prompt-execution-count"></span></div><div class="bm-prompt-execution-body">' + html + '</div>';
      }}
      document.getElementById('bm-execution-prompt-ids').value = Array.from(benchmarkExecutionSelections).join(',');
      var count = document.getElementById('bm-prompt-execution-count');
      if (count) count.textContent = benchmarkExecutionSelections.size + ' 项';
    }};
    function benchmarkSyncPromptGroupToggle(groupCheckbox) {{
      var group = groupCheckbox.getAttribute('data-group-toggle');
      var children = Array.from(document.querySelectorAll('#bm-prompt-execution-tree .bm-prompt-execution-child input[data-group-id="' + group + '"]'));
      var checked = children.filter(function(cb) {{ return cb.checked; }}).length;
      groupCheckbox.checked = children.length > 0 && checked === children.length;
      groupCheckbox.indeterminate = checked > 0 && checked < children.length;
    }}
    function benchmarkTogglePromptGroup(groupCheckbox) {{
      var group = groupCheckbox.getAttribute('data-group-toggle');
      document.querySelectorAll('#bm-prompt-execution-tree .bm-prompt-execution-child input[data-group-id="' + group + '"]').forEach(function(cb) {{
        cb.checked = groupCheckbox.checked;
        if (groupCheckbox.checked) benchmarkExecutionSelections.add(cb.value); else benchmarkExecutionSelections.delete(cb.value);
      }});
      window.renderBenchmarkPromptExecutionTree();
    }}
    function benchmarkTogglePromptChild(childCheckbox) {{
      if (childCheckbox.checked) benchmarkExecutionSelections.add(childCheckbox.value); else benchmarkExecutionSelections.delete(childCheckbox.value);
      window.renderBenchmarkPromptExecutionTree();
    }}
    function benchmarkPromptBatch(checked) {{
      document.querySelectorAll('#ms-bm-prompts-panel input[type=checkbox]:checked').forEach(function(groupCheckbox) {{
        var group = benchmarkPromptData.find(function(item) {{ return item.id === groupCheckbox.value; }});
        (group ? group.children : []).forEach(function(child) {{ if (checked) benchmarkExecutionSelections.add(child.id); else benchmarkExecutionSelections.delete(child.id); }});
      }});
      window.renderBenchmarkPromptExecutionTree();
    }}
    function benchmarkTagsToggle(event) {{
      event.stopPropagation();
      document.getElementById('ts-benchmark-tags').classList.toggle('open');
    }}
    function benchmarkTagsInit() {{
      var wrap = document.getElementById('ts-benchmark-tags');
      if (!wrap || wrap.dataset.initialized) return;
      wrap.dataset.initialized = '1';
      wrap.querySelectorAll('.ts-arrow:not(.empty)').forEach(function(arrow) {{
        arrow.addEventListener('click', function(event) {{
          event.stopPropagation();
          this.classList.toggle('expanded');
          var children = this.closest('.ts-node').querySelector('.ts-children');
          if (children) children.classList.toggle('expanded');
        }});
      }});
      wrap.querySelectorAll('.ts-row[data-id]').forEach(function(row) {{
        row.addEventListener('click', function(event) {{
          if (event.target.classList.contains('ts-arrow')) return;
          this.classList.toggle('selected');
          benchmarkTagsSync();
        }});
      }});
      document.addEventListener('click', function(event) {{
        if (!wrap.contains(event.target)) wrap.classList.remove('open');
      }});
    }}
    function benchmarkTagsSync() {{
      var wrap = document.getElementById('ts-benchmark-tags');
      var rows = wrap.querySelectorAll('.ts-row.selected');
      var ids = []; var chips = '';
      rows.forEach(function(row) {{
        ids.push(row.dataset.id);
        chips += '<span class="ts-chip"><span class="ts-chip-text">' + row.dataset.path + '</span><span class="ts-chip-close" data-id="' + row.dataset.id + '" onclick="event.stopPropagation();benchmarkTagRemove(this)">&times;</span></span>';
      }});
      wrap.querySelector('.ts-trigger').innerHTML = chips || '<span class="ts-placeholder">请选择标签</span>';
      document.getElementById('benchmark-tags-hidden').value = ids.join(',');
    }}
    function benchmarkTagRemove(button) {{
      var wrap = document.getElementById('ts-benchmark-tags');
      var row = wrap.querySelector('.ts-row[data-id="' + button.dataset.id + '"]');
      if (row) row.classList.remove('selected');
      benchmarkTagsSync();
    }}
    document.addEventListener('click', function(event) {{
      var remote = document.getElementById('benchmark-prompt-remote');
      if (remote && !remote.contains(event.target)) benchmarkPromptRemoteClose();
    }});
    </script>
    <style>
      .benchmark-filter-bar {{ overflow:visible; position:relative; z-index:20; }}
      .benchmark-list-card {{ position:relative; z-index:10; overflow:visible; }}
      .benchmark-list-card .ant-table,
      .benchmark-list-card .actions-cell {{ overflow:visible; }}
      .benchmark-list-card .action-more-wrap {{ position:relative; z-index:60; }}
      .benchmark-list-card .action-more-menu {{ top:auto; bottom:calc(100% + 4px); z-index:120; }}
      .benchmark-prompt-filter {{ min-width:280px; }}
      .benchmark-remote-select {{ position:relative; }}
      .benchmark-remote-select > input[type="text"] {{ width:100%; padding-right:30px; }}
      .benchmark-remote-panel {{ position:absolute; z-index:1300; top:calc(100% + 4px); left:0; width:100%; max-height:280px; overflow-y:auto; padding:4px 0; border:1px solid #d9d9d9; border-radius:6px; background:#fff; box-shadow:0 6px 18px rgba(0,0,0,.12); }}
      .benchmark-remote-option {{ display:flex; width:100%; padding:9px 12px; border:0; background:#fff; flex-direction:column; align-items:flex-start; gap:3px; text-align:left; cursor:pointer; }}
      .benchmark-remote-option:hover {{ background:#f5f8f9; }}
      .benchmark-remote-name {{ color:rgba(0,0,0,.85); font-size:13px; line-height:1.4; }}
      .benchmark-remote-meta {{ max-width:100%; overflow:hidden; color:rgba(0,0,0,.45); font-size:11px; line-height:1.4; text-overflow:ellipsis; white-space:nowrap; }}
      .benchmark-remote-state {{ padding:18px 12px; color:rgba(0,0,0,.38); font-size:12px; text-align:center; }}
    </style>
    '''
    return render_page("评测集", content, active="benchmarks")


@app.route("/benchmarks/create", methods=["POST"])
def benchmarks_create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Benchmark \u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a", "error")
        return redirect(url_for("benchmarks_page"))
    edit_id = request.form.get("edit_id", "").strip()
    edit_target = next((item for item in BENCHMARKS if item["id"] == edit_id), None) if edit_id else None
    benchmark_payload = {
        "name": name,
        "description": request.form.get("description", ""),
        "publish_status": request.form.get("publish_status", "未发布") if request.form.get("publish_status") in ("未发布", "已发布") else "未发布",
        "tags": [x.strip() for x in request.form.get("tags", "").split(",") if x.strip()],
        "prompt_ids": [x.strip() for x in request.form.get("prompt_ids", "").split(",") if x.strip()],
        "execution_prompt_ids": [x.strip() for x in request.form.get("execution_prompt_ids", "").split(",") if x.strip()],
    }
    if edit_target and edit_target.get("publish_status") == "未发布":
        edit_target.update(benchmark_payload)
        flash(f"评测集「{name}」保存成功", "success")
    elif edit_id:
        flash("仅未发布状态的评测集支持编辑", "error")
    else:
        BENCHMARKS.append({
            "id": f"b{len(BENCHMARKS)+1}",
            "creator": "Joanna Qiao",
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "publish_status": "未发布",
            **benchmark_payload,
        })
        flash(f"Benchmark\u300c{name}\u300d\u521b\u5efa\u6210\u529f", "success")
    return redirect(url_for("benchmarks_page"))


@app.route("/benchmarks/<bid>/publish")
def benchmark_publish(bid):
    benchmark = next((item for item in BENCHMARKS if item["id"] == bid), None)
    if benchmark and benchmark.get("publish_status") == "未发布":
        benchmark["publish_status"] = "已发布"
        flash(f"评测集「{benchmark['name']}」已发布", "success")
    return redirect(url_for("benchmarks_page"))


@app.route("/benchmarks/<bid>/delete")
def benchmark_delete(bid):
    benchmark = next((item for item in BENCHMARKS if item["id"] == bid), None)
    if benchmark and benchmark.get("publish_status") == "未发布":
        BENCHMARKS.remove(benchmark)
        flash(f"评测集「{benchmark['name']}」已删除", "success")
    elif benchmark:
        flash("已发布状态的评测集不支持删除", "error")
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
        enabled_tag = '<span class="ant-tag ant-tag-green">已发布</span>' if p.get("enabled") else '<span class="ant-tag">未发布</span>'
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
    benchmark_tags_html = render_tags_html(b.get("tags", []))

    content = f'''
    <div style="margin-bottom:16px;"><a href="/benchmarks" class="ant-btn">&larr; \u8fd4\u56de\u5217\u8868</a></div>

    <!-- Section 1: Basic Info -->
    <div class="ant-card ant-card-bordered" style="margin-bottom:20px;">
      <div class="ant-card-head" style="padding:12px 20px;"><h3>\u57fa\u672c\u4fe1\u606f</h3></div>
      <div class="ant-card-body">
        <div style="display:grid;grid-template-columns:110px 1fr;gap:10px 16px;font-size:14px;">
          <span style="color:rgba(0,0,0,0.45);">\u540d\u79f0</span><span style="font-weight:500;font-size:15px;">{b["name"]}</span>
          <span style="color:rgba(0,0,0,0.45);">\u63cf\u8ff0</span><span>{description_html}</span>
          <span style="color:rgba(0,0,0,0.45);">\u6807\u7b7e</span><span>{benchmark_tags_html}</span>
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
    content = f'''
    <div style="margin-bottom:16px;"><a href="/benchmarks" class="ant-btn">&larr; 返回列表</a></div>
    <div class="ant-card ant-card-bordered" style="margin-bottom:20px;">
      <div class="ant-card-head" style="padding:12px 20px;"><h3>基本信息</h3></div>
      <div class="ant-card-body"><div style="display:grid;grid-template-columns:110px 1fr;gap:10px 16px;font-size:14px;">
        <span style="color:rgba(0,0,0,.45);">名称</span><span style="font-weight:500;">{b["name"]}</span>
        <span style="color:rgba(0,0,0,.45);">描述</span><span>{description_html}</span>
        <span style="color:rgba(0,0,0,.45);">标签</span><span>{benchmark_tags_html}</span>
        <span style="color:rgba(0,0,0,.45);">创建</span><span>{b["creator"]} · {b["created_at"]}</span>
      </div></div>
    </div>
    <div class="ant-card ant-card-bordered">
      <div class="ant-card-head" style="padding:12px 20px;"><h3>提示词（{len(b.get("prompt_ids", []))} 组）</h3></div>
      <div class="ant-card-body" style="padding:0;"><table class="ant-table">
        <thead><tr><th>任务提示词</th><th>Task-Prompt</th><th>子步骤</th><th>标签</th><th>状态</th></tr></thead>
        <tbody>{prompt_rows}</tbody>
      </table></div>
    </div>'''
    return render_page(bm_title, content, active="benchmarks")


# ── Evaluation Task Management ──
@app.route("/tasks")
def tasks_page():
    def task_action(href, label, danger=False):
        cls = "action-link danger" if danger else "action-link"
        return f'<a href="{href}" class="{cls}" title="{label}">{label}</a>'

    active_tasks = [t for t in EVAL_TASKS if t.get("status") in ("\u91c7\u96c6\u4e2d", "\u8bc4\u6d4b\u4e2d")]
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

        # Unified progress across collection and evaluation stages.
        total = max(t.get("total_sessions", 1), 1)
        c_done = t.get("collect_done", 0)
        e_done = t.get("eval_done", 0)
        progress_done = min(total, round((c_done + e_done) / 2))
        progress_pct = round(progress_done / total * 100)
        progress_html = (
            f'<div style="font-size:12px;line-height:1.8;">'
            f'<div style="display:flex;align-items:center;gap:6px;">'
            f'<div style="flex:1;height:14px;background:#f0f0f0;border-radius:7px;overflow:hidden;position:relative;">'
            f'<div style="width:{progress_pct}%;height:100%;background:#1F80A0;border-radius:7px;"></div>'
            f'<span class="pb-text" style="--pct:{progress_pct}%;">{progress_done}/{total}</span>'
            f'</div></div></div>'
        )

        publish_status = t.get("publish_status", "已发布")
        is_unpublished = publish_status == "未发布"
        publish_status_class = "tag-gray" if is_unpublished else "tag-green"

        # Actions per status
        view_btn = f'<a href="javascript:;" class="action-link" title="查看" onclick="openTaskView(\'{t["id"]}\')">查看</a>'
        data_btn = task_action(f'/tasks/{t["id"]}/data', "\u6570\u636e")
        st = t["status"]
        stats_btn = task_action(f'/tasks/{t["id"]}/statistics', "统计")
        if is_unpublished:
            action_btns = view_btn
            action_btns += f'<a href="javascript:;" class="action-link" title="编辑" onclick="openTaskEdit(\'{t["id"]}\')">编辑</a>'
            action_btns += f'<a href="/tasks/{t["id"]}/publish" class="action-link" title="发布" onclick="return confirm(\'发布后将不能编辑或删除，确认发布吗？\')">发布</a>'
            action_btns += f'<a href="/tasks/{t["id"]}/delete" class="action-link danger" title="删除" onclick="return confirm(\'确认删除该评测任务吗？\')">删除</a>'
        else:
            action_btns = view_btn + data_btn + stats_btn

        # Enable switch: ON for started tasks, clickable only when 未开始
        is_enabled = st != "\u672a\u5f00\u59cb"
        if is_unpublished:
            switch_html = '<label class="capsule" style="opacity:0.3;cursor:not-allowed;" title="发布后可开启评测"><span class="capsule-dot"></span></label>'
        elif st == "\u672a\u5f00\u59cb":
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
            f'<td><span class="tag {publish_status_class}">{publish_status}</span></td>'
            f"<td style='text-align:center;'>{switch_html}</td>"
            f"<td style='min-width:160px;'>{progress_html}</td>"
            f"<td>{pri_tag}</td>"
            f"<td>{t['created_by']}</td>"
            f'<td class="actions-cell">{action_btns}</td>'
            "</tr>"
        )

    # Pre-build select options
    bm_opts = '<option value="">\u8bf7\u9009\u62e9\u8bc4\u6d4b\u96c6</option>' + "".join(f'<option value="{b["id"]}">{b["name"]}</option>' for b in BENCHMARKS)
    model_opts = "".join(f'<option value="{m["id"]}">{m["name"]} ({m["version"]})</option>' for m in MODELS)
    scene_opts = '<option value="">\u8bf7\u9009\u62e9\u573a\u666f</option>' + "".join(f'<option value="{s["id"]}">{s["name"]}</option>' for s in SCENES)
    task_criteria_opts = '<option value="">\u8bf7\u9009\u62e9\u8bc4\u4ef7\u6807\u51c6</option>' + "".join(f'<option value="{c["id"]}">{c["name"]}</option>' for c in CRITERIA)
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
                    "id": p["id"],
                    "name": p["high_level"],
                    "steps": len(p.get("low_levels", [])),
                    "low_levels": [{"id": ll.get("id", f'{p["id"]}-ll-{index + 1}'), "zh": ll.get("zh", ""), "en": ll.get("en", "")} for index, ll in enumerate(p.get("low_levels", []))],
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

    # Data used by the shared create/view task drawer.
    task_view_data = {}
    for _task in EVAL_TASKS:
        _bm = get_benchmark(_task.get("benchmark_id", ""))
        _selected_prompt_ids = list(_task.get("selected_prompt_ids", []))
        _selected_lowlevel_ids = list(_task.get("selected_lowlevel_ids", []))
        if not _selected_lowlevel_ids:
            for _prompt_id in _selected_prompt_ids:
                _prompt = get_prompt(_prompt_id)
                if _prompt:
                    _selected_lowlevel_ids.extend(ll.get("id", "") for ll in _prompt.get("low_levels", []) if ll.get("id"))
        task_view_data[_task["id"]] = {
            "id": _task["id"],
            "name": _task.get("name", ""),
            "project": _task.get("project", ""),
            "task_mode": _task.get("task_mode", "Evaluaton"),
            "priority": _task.get("priority", ""),
            "due_date": _task.get("due_date", ""),
            "description": _task.get("description", ""),
            "total_sessions": _task.get("total_sessions", 0),
            "model_ids": list(_task.get("model_ids", [])),
            "model_names": [get_model_name(mid) for mid in _task.get("model_ids", [])],
            "benchmark_id": _task.get("benchmark_id", ""),
            "benchmark_name": _bm.get("name", "") if _bm else "",
            "criteria_id": _task.get("criteria_id", ""),
            "selected_prompt_ids": _selected_prompt_ids,
            "selected_lowlevel_ids": _selected_lowlevel_ids,
            "publish_status": _task.get("publish_status", "已发布"),
        }
    task_view_data_json = _json.dumps(task_view_data, ensure_ascii=False)

    # Checkpoint is a single-select resource for a new evaluation task.
    ckpt_select_opts = '<option value="">请选择 checkpoint</option>' + "".join(
        f'<option value="{html.escape(m["id"], quote=True)}" data-name="{html.escape(m["name"], quote=True)}">{html.escape(m["name"])} · {html.escape(m["version"])}</option>'
        for m in MODELS
    )
    type_filter_opts = "".join(f'<option value="{k}">{v["label"]}</option>' for k, v in CRITERIA_TYPES.items())
    bm_filter_opts = "".join(f'<option>{b["name"]}</option>' for b in BENCHMARKS)
    model_filter_opts = "".join(f'<option>{m["name"]}</option>' for m in MODELS)
    endpoint_modes_eval2 = endpoint_mode_buttons("eval2-mode", "selected", "eval2SelectMode")

    content = f'''
    <div style="display:none" class="eval2-flow" id="eval2-flow">
      <div class="eval2-flow-head"><div><h2>模式选择</h2><p>选择评测模式后开始端侧自检</p></div><span class="eval2-device" id="eval2-device">设备：未知设备</span></div>
      <div class="eval2-mode-grid">{endpoint_modes_eval2}</div>
      <button type="button" class="eval2-primary" id="eval2-self-check" onclick="eval2SelfCheck()">开始自检</button><div class="eval2-check-note">自检将检查机器人、相机、控制器与网络连接</div>
      <div class="eval2-setup" id="eval2-setup" hidden><div class="eval2-section-title">项目与任务 <span class="eval2-ok">● 设备自检通过</span></div><div class="eval2-select-row"><label>项目<select><option>eval</option><option>预训练</option><option>回归验证</option></select></label><label>任务<select id="eval2-task"><option value="">请选择任务</option>{"".join(f'<option value="{t["id"]}">{t["task_no"]}：{t.get("name", "评测任务")}</option>' for t in active_tasks)}</select></label></div><div class="eval2-section-title">场景和提示词</div><div class="eval2-context"><div><b>场景</b><p>选择任务后展示关联场景和参考素材</p></div><div><b>提示词</b><p>选择任务后展示待执行提示词组</p></div></div><button type="button" class="eval2-primary" onclick="eval2EnterTask()">确认进入任务</button></div>
    </div>
    <div class="filter-bar fb-labeled task-filter-bar">
      <div class="ff"><label>\u4efb\u52a1 ID</label><input id="eval-task-filter-id" type="text" placeholder="\u8bf7\u8f93\u5165\u4efb\u52a1 ID" onkeydown="if(event.key==='Enter')filterEvalTasks()"></div>
      <div class="ff"><label>\u4efb\u52a1\u540d\u79f0</label><input id="eval-task-filter-name" type="text" placeholder="\u8bf7\u8f93\u5165\u4efb\u52a1\u540d\u79f0" onkeydown="if(event.key==='Enter')filterEvalTasks()"></div>
      <div class="ff"><label>\u8bc4\u6d4b\u96c6</label><select name="benchmark"><option value="">\u8bc4\u6d4b\u96c6</option>{bm_filter_opts}</select></div>
      <div class="ff"><label>Checkpoint</label><select name="checkpoint"><option value="">Checkpoint</option>{model_filter_opts}</select></div>
      <div class="ff"><label>\u72b6\u6001</label><select name="publish_status"><option value="">\u5168\u90e8\u72b6\u6001</option><option>未发布</option><option>已发布</option></select></div>
      <div class="ff"><label>\u4f18\u5148\u7ea7</label><select name="priority"><option value="">\u4f18\u5148\u7ea7</option><option>\u9ad8</option><option>\u4e2d</option><option>\u4f4e</option></select></div>
      <div class="filter-actions">
        <button class="ant-btn" type="button" onclick="clearEvalTaskFilters()">\u6e05\u7a7a</button>
        <button class="ant-btn ant-btn-primary" type="button" onclick="filterEvalTasks()">\u641c\u7d22</button>
      </div>
      <div style="flex:1;"></div>
      <button class="ant-btn" type="button" onclick="exportEvalTasks()">导出</button>
      <button class="ant-btn ant-btn-primary" onclick="openTaskCreate()">+ \u65b0\u589e\u8bc4\u6d4b\u4efb\u52a1</button>
    </div>

    <div class="ant-card ant-card-bordered">
      <table class="ant-table" id="eval-task-table">
        <thead><tr>
          <th style="width:50px;">ID</th><th>\u4efb\u52a1\u540d\u79f0</th><th>\u8bc4\u6d4b\u96c6</th><th>Checkpoint</th><th>状态</th><th>评测状态</th><th>\u8fdb\u5ea6</th><th>\u4f18\u5148\u7ea7</th><th>\u521b\u5efa\u4eba</th><th>\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <!-- Create Task Drawer -->
    <div class="ant-drawer-mask" id="create-task-drawer">
      <div class="ant-drawer-content task-drawer-content">
        <div class="ant-drawer-header"><h3 id="task-drawer-title">\u65b0\u589e\u8bc4\u6d4b\u4efb\u52a1</h3><button class="ant-drawer-close" onclick="closeModal('create-task-drawer')">&times;</button></div>
        <form id="task-drawer-form" method="POST" action="/tasks/create" enctype="multipart/form-data" onsubmit="return validateTaskForm()">
        <input type="hidden" name="edit_id" value="">
        <div class="ant-drawer-body">
          <!-- Section 1: Basic Info -->
          <h4 style="font-size:14px;font-weight:500;margin-bottom:12px;color:rgba(0,0,0,0.85);">\u57fa\u7840\u4fe1\u606f</h4>
          <div class="form-row">
            <div class="form-group"><label class="req">\u4efb\u52a1\u540d\u79f0</label><div class="input-clear-wrap"><input type="text" name="name" required><span class="input-clear" onclick="this.previousElementSibling.value=''">&times;</span></div></div>
            <div class="form-group"><label class="req">\u6240\u5c5e\u9879\u76ee</label><select name="project" required><option value="">\u8bf7\u9009\u62e9</option><option>\u57fa\u7840\u7814\u7a76</option><option>\u5b81\u5fb7\u5e94\u7528</option><option>moz1</option><option>spirit</option><option>demo\u91c7\u96c6</option><option>\u9884\u8bad\u7ec3\u91c7\u96c6</option><option>\u591a\u4efb\u52a1</option></select></div>
            <div class="form-group"><label>\u4efb\u52a1\u6a21\u5f0f</label><input type="text" value="Evaluaton" disabled style="background:#f5f5f5;color:rgba(0,0,0,0.45);"><input type="hidden" name="task_mode" value="Evaluaton"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label class="req">\u4f18\u5148\u7ea7</label><select name="priority" required><option value="">\u8bf7\u9009\u62e9</option><option value="\u9ad8">\u9ad8</option><option value="\u4e2d" selected>\u4e2d</option><option value="\u4f4e">\u4f4e</option></select></div>
            <div class="form-group"><label class="req">\u9884\u671f\u4ea4\u4ed8\u65e5\u671f</label><div class="input-clear-wrap"><input type="date" name="due_date" required style="width:100%;"><span class="input-clear" onclick="this.previousElementSibling.value=''">&times;</span></div></div>
            <div class="form-group" id="task-publish-status-field" style="display:none;"><label>状态</label><select name="publish_status"><option value="未发布">未发布</option><option value="已发布">已发布</option></select></div>
          </div>
          <div class="form-group"><label>\u4efb\u52a1\u63cf\u8ff0</label><textarea name="description" rows="2" placeholder="\u7b80\u8981\u63cf\u8ff0\u8be5\u4efb\u52a1\u7684\u76ee\u7684\u3001\u5173\u6ce8\u70b9\u7b49"></textarea></div>

          <hr style="border:none;border-top:1px solid #f0f0f0;margin:20px 0;">

          <!-- Section 2: Eval Config -->
          <h4 style="font-size:14px;font-weight:500;margin-bottom:12px;color:rgba(0,0,0,0.85);">\u8bc4\u6d4b\u914d\u7f6e</h4>
          <div class="form-row">
            <div class="form-group" style="grid-column:1/4;">
              <label class="req task-resource-label"><span class="task-resource-title">Checkpoint</span><span class="task-resource-actions"><a id="task-ckpt-view" class="task-resource-link" href="/model/checkpoints"><span class="task-resource-icon" aria-hidden="true">↗</span>\u53bb\u67e5\u770b</a><a class="task-resource-link task-resource-create" href="/model/checkpoints?open=create"><span class="task-resource-icon" aria-hidden="true">＋</span>\u53bb\u521b\u5efa</a></span></label>
              <select name="model_ids" id="task-ckpt-select" required onchange="updateTaskResourceLinks()">{ckpt_select_opts}</select>
            </div>
          </div>

          <div class="form-row task-eval-config-row" style="margin-top:16px;">
            <div class="form-group"><label class="req">\u8bc4\u6d4b\u6b21\u6570</label><div class="input-clear-wrap"><input type="number" name="total_sessions" required value="30" min="1"><span class="input-clear" onclick="this.previousElementSibling.value=''">&times;</span></div></div>
            <div class="form-group"><label class="req">\u8bc4\u4ef7\u6807\u51c6</label><select name="criteria_id" required>{task_criteria_opts}</select></div>
          </div>

          <!-- Evaluation set (merged into Eval Config) -->
          <div class="form-group" style="margin-top:4px;">
            <label class="req task-resource-label"><span class="task-resource-title">\u8bc4\u6d4b\u96c6</span><span class="task-resource-actions"><a id="task-bm-view" class="task-resource-link" href="/model/eval/benchmarks"><span class="task-resource-icon" aria-hidden="true">↗</span>\u53bb\u67e5\u770b</a><a class="task-resource-link task-resource-create" href="/model/eval/benchmarks?open=create"><span class="task-resource-icon" aria-hidden="true">＋</span>\u53bb\u521b\u5efa</a></span></label>
            <select name="benchmark_id" id="bm-select" required onchange="previewBm(this.value)" class="has-value">{bm_opts}</select>
          </div>
          <div id="bm-preview" class="task-prompt-tree" style="display:none;">
            <div class="task-prompt-tree-head">
              <label><input id="task-prompt-all" type="checkbox" onchange="taskPromptToggleAll(this.checked)"> <b>\u672c\u6b21\u8bc4\u6d4b\u63d0\u793a\u8bcd</b></label>
              <span id="task-prompt-count">0 / 0 \u5df2\u9009</span>
            </div>
            <div id="bm-pv-prompts" class="task-prompt-tree-body"></div>
            <input type="hidden" name="selected_prompt_ids" id="selected-prompt-ids" value="">
            <input type="hidden" name="selected_lowlevel_ids" id="selected-lowlevel-ids" value="">
          </div>
        </div>
        <!-- Benchmark detail modal (inline drawer) -->
        <div class="ant-drawer-mask" id="bm-detail-modal" style="z-index:300;background:rgba(0,0,0,0.65);">
          <div class="ant-drawer-content" style="width:720px;max-width:90vw;">
            <div class="ant-drawer-header">
              <h3 id="bm-detail-title">\u8bc4\u6d4b\u96c6\u8be6\u60c5</h3>
              <button class="ant-drawer-close" onclick="closeBmDetail()">&times;</button>
            </div>
            <div class="ant-drawer-body">
              <div id="bm-detail-body" style="font-size:14px;"></div>
            </div>
          </div>
        </div>
        <div class="ant-drawer-footer">
          <button type="button" id="task-drawer-close-btn" class="ant-btn" onclick="closeModal('create-task-drawer')">\u53d6\u6d88</button>
          <button type="submit" id="task-drawer-submit" class="ant-btn ant-btn-primary">\u521b\u5efa\u4efb\u52a1</button>
        </div>
        </form>
      </div>
    </div>

    <style>
      .task-prompt-tree {{ margin-top:10px;border:1px solid #e3e8ec;border-radius:6px;background:#fff;overflow:hidden; }}
      .task-prompt-tree-head {{ display:flex;align-items:center;justify-content:space-between;padding:11px 14px;background:#f7f9fa;border-bottom:1px solid #e8ecef;font-size:13px; }}
      .task-prompt-tree-head label {{ display:flex;align-items:center;gap:7px;margin:0; }}
      .task-prompt-tree-head span {{ color:rgba(0,0,0,.45);font-size:12px; }}
      .task-prompt-tree-body {{ max-height:310px;overflow:auto;padding:6px 0; }}
      .task-prompt-node + .task-prompt-node {{ border-top:1px solid #f0f2f4; }}
      .task-prompt-parent {{ display:flex;align-items:flex-start;gap:4px;padding:10px 14px; }}
      .task-prompt-parent label {{ display:flex;align-items:flex-start;gap:8px;margin:0;cursor:pointer; }}
      .task-prompt-parent label > span {{ display:flex;flex-direction:column;gap:2px; }}
      .task-prompt-parent small {{ color:rgba(0,0,0,.42);font-size:11px; }}
      .task-prompt-parent-copy {{ display:flex;flex-direction:column;gap:2px; }}
      .task-prompt-expand {{ width:20px;height:20px;padding:0;border:0;background:transparent;color:rgba(0,0,0,.35);cursor:pointer;font-size:10px; }}
      .task-prompt-children {{ margin:0 14px 8px 46px;border-left:1px solid #dfe6ea; }}
      .task-prompt-child {{ display:grid;grid-template-columns:16px 24px minmax(180px,1fr) minmax(220px,1.2fr);align-items:start;gap:8px;padding:7px 10px;margin:0;color:rgba(0,0,0,.65);font-size:12px;cursor:pointer; }}
      .task-prompt-child>input {{ margin-top:2px;accent-color:#1F80A0; }} .task-prompt-child span:nth-child(2),.task-prompt-child small {{ color:rgba(0,0,0,.4); }}
      .task-eval-config-row {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
      .task-view-mode .form-group input:disabled,
      .task-view-mode .form-group select:disabled,
      .task-view-mode .form-group textarea:disabled {{ background-color:#f5f5f5 !important; border-color:#d9d9d9 !important; color:rgba(0,0,0,.38) !important; -webkit-text-fill-color:rgba(0,0,0,.38); box-shadow:none !important; cursor:not-allowed; opacity:1; }}
      .task-view-mode .form-group select:disabled {{ background-image:none !important; padding-right:12px; }}
      .task-view-mode .input-clear {{ display:none; }}
      .task-view-mode .upload-zone {{ pointer-events:none; cursor:not-allowed; border-style:solid; border-color:#d9d9d9; background:#f5f5f5; color:rgba(0,0,0,.3); }}
      .task-view-mode .upload-icon,
      .task-view-mode .upload-text,
      .task-view-mode .upload-hint,
      .task-view-mode .upload-files {{ color:rgba(0,0,0,.3) !important; }}
      .task-view-mode .er-dd-trigger.is-disabled {{ background:#f5f5f5 !important; border-color:#d9d9d9; color:rgba(0,0,0,.38); box-shadow:none; }}
      .task-view-mode .er-chip {{ background:#ededed; border-color:#dedede; color:rgba(0,0,0,.38); }}
      .task-view-mode .task-prompt-tree {{ border-color:#d9d9d9; background:#f5f5f5; }}
      .task-view-mode .task-prompt-tree-head {{ background:#ededed; color:rgba(0,0,0,.38); }}
      .task-view-mode .task-prompt-child,
      .task-view-mode .task-prompt-parent-copy {{ color:rgba(0,0,0,.38); cursor:not-allowed; }}
      .task-view-mode .task-prompt-child small,
      .task-view-mode .task-prompt-parent small {{ color:rgba(0,0,0,.28); }}
      .task-view-mode input[type="checkbox"]:disabled {{ filter:grayscale(1); opacity:.55; cursor:not-allowed; }}
    </style>
    <script>
    var bmData = {bm_preview_json};
    var taskViewData = {task_view_data_json};
    var bmCurrentId = null;
    function filterEvalTasks() {{
      var bar = document.querySelector('.task-filter-bar');
      var taskId = (document.getElementById('eval-task-filter-id').value || '').trim().toLowerCase();
      var taskName = (document.getElementById('eval-task-filter-name').value || '').trim().toLowerCase();
      var benchmark = bar.querySelector('select[name="benchmark"]').value || '';
      var checkpoint = bar.querySelector('select[name="checkpoint"]').value || '';
      var status = bar.querySelector('select[name="publish_status"]').value || '';
      var priority = bar.querySelector('select[name="priority"]').value || '';
      document.querySelectorAll('#eval-task-table tbody tr').forEach(function(row) {{
        if (row.cells.length < 8) return;
        var idText = (row.cells[0].textContent || '').trim().toLowerCase();
        var nameText = (row.cells[1].textContent || '').trim().toLowerCase();
        var benchmarkText = (row.cells[2].textContent || '').trim();
        var checkpointText = (row.cells[3].textContent || '').trim();
        var statusText = (row.cells[4].textContent || '').trim();
        var priorityText = (row.cells[7].textContent || '').trim();
        var matched = (!taskId || idText.indexOf(taskId) >= 0)
          && (!taskName || nameText.indexOf(taskName) >= 0)
          && (!benchmark || benchmarkText === benchmark)
          && (!checkpoint || checkpointText.indexOf(checkpoint) >= 0)
          && (!status || statusText === status)
          && (!priority || priorityText === priority);
        row.style.display = matched ? '' : 'none';
      }});
    }}
    function clearEvalTaskFilters() {{
      var bar = document.querySelector('.task-filter-bar');
      document.getElementById('eval-task-filter-id').value = '';
      document.getElementById('eval-task-filter-name').value = '';
      bar.querySelectorAll('select').forEach(function(select) {{
        select.selectedIndex = 0;
        select.classList.remove('has-value');
      }});
      filterEvalTasks();
    }}
    function exportEvalTasks() {{
      var table = document.getElementById('eval-task-table');
      if (!table) return;
      var rows = [];
      var headers = [];
      table.querySelectorAll('thead th').forEach(function(th, index) {{
        if (index < table.querySelector('thead tr').cells.length - 1) headers.push((th.textContent || '').trim());
      }});
      rows.push(headers);
      table.querySelectorAll('tbody tr').forEach(function(tr) {{
        if (tr.style.display === 'none' || tr.cells.length < 2) return;
        var row = [];
        for (var i = 0; i < tr.cells.length - 1; i++) row.push((tr.cells[i].textContent || '').replace(/\\s+/g, ' ').trim());
        rows.push(row);
      }});
      if (rows.length <= 1) {{
        if (window.showToast) window.showToast('暂无数据可导出', 'warning');
        return;
      }}
      var csv = rows.map(function(row) {{ return row.map(function(value) {{
        var text = String(value).replace(/"/g, '""');
        return /[,"\\n]/.test(text) ? '"' + text + '"' : text;
      }}).join(','); }}).join('\\n');
      var url = URL.createObjectURL(new Blob(['\\uFEFF' + csv], {{type:'text/csv;charset=utf-8'}}));
      var link = document.createElement('a');
      link.href = url;
      link.download = '评测任务_' + new Date().toISOString().slice(0, 10) + '.csv';
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(function() {{ URL.revokeObjectURL(url); }}, 1000);
      if (window.showToast) window.showToast('已导出 ' + (rows.length - 1) + ' 条数据', 'success');
    }}
    function setTaskDrawerReadonly(readonly) {{
      var drawer = document.getElementById('create-task-drawer');
      if (!drawer) return;
      drawer.classList.toggle('task-view-mode', readonly);
      drawer.querySelectorAll('#task-drawer-form input, #task-drawer-form select, #task-drawer-form textarea').forEach(function(el) {{
        if (el.type !== 'hidden') el.disabled = readonly;
      }});
      document.querySelectorAll('#bm-pv-prompts input, #task-prompt-all').forEach(function(cb) {{ cb.disabled = readonly; }});
      document.querySelectorAll('#bm-pv-prompts .task-prompt-expand').forEach(function(btn) {{ btn.disabled = readonly; btn.style.cursor = readonly ? 'default' : ''; }});
      document.querySelectorAll('#create-task-drawer .task-resource-create').forEach(function(a) {{ a.style.display = readonly ? 'none' : ''; }});
      document.getElementById('task-drawer-title').textContent = readonly ? '\u67e5\u770b\u8bc4\u6d4b\u4efb\u52a1' : '\u65b0\u589e\u8bc4\u6d4b\u4efb\u52a1';
      document.getElementById('task-drawer-submit').style.display = readonly ? 'none' : '';
      document.getElementById('task-drawer-close-btn').textContent = readonly ? '\u5173\u95ed' : '\u53d6\u6d88';
    }}
    function resetTaskDrawerForm() {{
      var form = document.getElementById('task-drawer-form');
      if (!form) return;
      form.reset();
      var ckptSelect = document.getElementById('task-ckpt-select');
      if (ckptSelect) ckptSelect.value = '';
      var bmSelect = document.getElementById('bm-select');
      if (bmSelect) {{ bmSelect.value = ''; bmSelect.classList.remove('has-value'); }}
      var promptHidden = document.getElementById('selected-prompt-ids');
      if (promptHidden) promptHidden.value = '';
      var lowlevelHidden = document.getElementById('selected-lowlevel-ids');
      if (lowlevelHidden) lowlevelHidden.value = '';
      bmCurrentId = null;
      var pv = document.getElementById('bm-preview');
      if (pv) pv.style.display = 'none';
      window.updateTaskResourceLinks();
    }}
    function openTaskCreate() {{
      resetTaskDrawerForm();
      setTaskDrawerReadonly(false);
      document.getElementById('task-publish-status-field').style.display = 'none';
      document.getElementById('task-drawer-title').textContent = '新增评测任务';
      document.getElementById('task-drawer-submit').textContent = '创建任务';
      openModal('create-task-drawer');
    }}
    function openTaskView(tid) {{
      var d = taskViewData[tid];
      if (!d) return;
      var form = document.getElementById('task-drawer-form');
      if (!form) return;
      resetTaskDrawerForm();
      form.querySelector('input[name="name"]').value = d.name || '';
      form.querySelector('select[name="project"]').value = d.project || '';
      form.querySelector('select[name="priority"]').value = d.priority || '';
      form.querySelector('input[name="due_date"]').value = d.due_date || '';
      form.querySelector('textarea[name="description"]').value = d.description || '';
      form.querySelector('input[name="total_sessions"]').value = d.total_sessions || '';
      form.querySelector('select[name="publish_status"]').value = d.publish_status || '未发布';
      document.getElementById('task-publish-status-field').style.display = '';
      var bmSelect = document.getElementById('bm-select');
      if (bmSelect) {{ bmSelect.value = d.benchmark_id || ''; bmSelect.classList.toggle('has-value', !!d.benchmark_id); }}
      form.querySelector('select[name="criteria_id"]').value = d.criteria_id || '';
      var ckptSelect = document.getElementById('task-ckpt-select');
      if (ckptSelect) ckptSelect.value = (d.model_ids || [])[0] || '';
      previewBm(d.benchmark_id || '', d.selected_lowlevel_ids || []);
      setTaskDrawerReadonly(true);
      openModal('create-task-drawer');
    }}
    function openTaskEdit(tid) {{
      openTaskView(tid);
      var form = document.getElementById('task-drawer-form');
      setTaskDrawerReadonly(false);
      form.querySelector('[name="edit_id"]').value = tid;
      document.getElementById('task-drawer-title').textContent = '编辑评测任务';
      document.getElementById('task-drawer-submit').textContent = '保存';
    }}
    window.updateTaskResourceLinks = function() {{
      var ckptLink = document.getElementById('task-ckpt-view');
      if (ckptLink) {{
        var ckptSelect = document.getElementById('task-ckpt-select');
        var selected = ckptSelect && ckptSelect.value ? ckptSelect.options[ckptSelect.selectedIndex] : null;
        var ckptName = selected ? (selected.getAttribute('data-name') || selected.textContent || '').trim() : '';
        if (ckptName) {{
          ckptLink.href = '/model/checkpoints?name=' + encodeURIComponent(ckptName);
          ckptLink.classList.remove('is-disabled');
          ckptLink.removeAttribute('aria-disabled');
          ckptLink.removeAttribute('tabindex');
        }} else {{
          ckptLink.removeAttribute('href');
          ckptLink.classList.add('is-disabled');
          ckptLink.setAttribute('aria-disabled', 'true');
          ckptLink.setAttribute('tabindex', '-1');
        }}
      }}
      var bmLink = document.getElementById('task-bm-view');
      var bmSelect = document.getElementById('bm-select');
      if (bmLink && bmSelect) {{
        var bm = bmData[bmSelect.value];
        var bmName = bm ? bm.name : '';
        if (bmName) {{
          bmLink.href = '/model/eval/benchmarks?name=' + encodeURIComponent(bmName);
          bmLink.classList.remove('is-disabled');
          bmLink.removeAttribute('aria-disabled');
          bmLink.removeAttribute('tabindex');
        }} else {{
          bmLink.removeAttribute('href');
          bmLink.classList.add('is-disabled');
          bmLink.setAttribute('aria-disabled', 'true');
          bmLink.setAttribute('tabindex', '-1');
        }}
      }}
    }};
    function taskPromptSync() {{
      var boxes = Array.from(document.querySelectorAll('#bm-pv-prompts .task-prompt-checkbox'));
      var selected = boxes.filter(function(cb) {{ return cb.checked; }});
      document.getElementById('selected-lowlevel-ids').value = selected.map(function(cb) {{ return cb.value; }}).join(',');
      document.getElementById('selected-prompt-ids').value = Array.from(new Set(selected.map(function(cb) {{ return cb.dataset.promptId; }}))).join(',');
      document.getElementById('task-prompt-count').textContent = selected.length + ' / ' + boxes.length + ' \u5df2\u9009';
      var all = document.getElementById('task-prompt-all');
      all.checked = boxes.length > 0 && selected.length === boxes.length;
      all.indeterminate = selected.length > 0 && selected.length < boxes.length;
    }}
    function taskPromptToggleAll(checked) {{
      document.querySelectorAll('#bm-pv-prompts .task-prompt-checkbox').forEach(function(cb) {{ if (!cb.disabled) cb.checked = checked; }});
      taskPromptSync();
    }}
    function taskPromptToggleNode(button) {{
      var children = button.closest('.task-prompt-node').querySelector('.task-prompt-children');
      children.hidden = !children.hidden;
      button.textContent = children.hidden ? '\u25b6' : '\u25bc';
    }}
    function previewBm(bid, selectedIds) {{
      bmCurrentId = bid;
      window.updateTaskResourceLinks();
      var pv = document.getElementById('bm-preview');
      var d = bmData[bid];
      if (!d) {{ pv.style.display='none'; return; }}
      pv.style.display='';
      selectedIds = Array.isArray(selectedIds) ? selectedIds : d.prompts.reduce(function(ids, p) {{ return ids.concat((p.low_levels || []).map(function(ll) {{ return ll.id; }})); }}, []);
      var ph = '';
      d.prompts.forEach(function(p) {{
        var lowLevels = (p.low_levels || []).map(function(ll, index) {{
          var checked = selectedIds.indexOf(ll.id) >= 0 ? ' checked' : '';
          return '<label class="task-prompt-child"><input class="task-prompt-checkbox" type="checkbox" value="' + ll.id + '" data-prompt-id="' + p.id + '"' + checked + ' onchange="taskPromptSync()"><span>' + (index + 1) + '</span><span>' + ll.zh + '</span><small>' + ll.en + '</small></label>';
        }}).join('');
        ph += '<div class="task-prompt-node"><div class="task-prompt-parent"><button type="button" class="task-prompt-expand" onclick="taskPromptToggleNode(this)">\u25bc</button><span class="task-prompt-parent-copy"><b>' + p.name + '</b><small>' + p.steps + ' \u4e2a Task-Prompt</small></span></div><div class="task-prompt-children">' + lowLevels + '</div></div>';
      }});
      document.getElementById('bm-pv-prompts').innerHTML = ph;
      taskPromptSync();
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
      document.getElementById('bm-detail-title').textContent = '\u8bc4\u6d4b\u96c6\u8be6\u60c5 - ' + d.name;
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
      var proj = form.querySelector('select[name="project"]');
      if (!proj.value) return fail('\u8bf7\u9009\u62e9\u6240\u5c5e\u9879\u76ee', proj);
      var pri = form.querySelector('select[name="priority"]');
      if (!pri.value) return fail('\u8bf7\u9009\u62e9\u4f18\u5148\u7ea7', pri);
      var due = form.querySelector('input[name="due_date"]');
      if (!due.value) return fail('\u8bf7\u9009\u62e9\u9884\u671f\u4ea4\u4ed8\u65e5\u671f', due);
      var sessions = form.querySelector('input[name="total_sessions"]');
      if (!sessions.value || parseInt(sessions.value) < 1) return fail('\u8bf7\u586b\u5199\u8bc4\u6d4b\u6b21\u6570', sessions);
      var ckptSelect = document.getElementById('task-ckpt-select');
      if (!ckptSelect || !ckptSelect.value) return fail('请选择 checkpoint', ckptSelect);
      var bm = form.querySelector('select[name="benchmark_id"]');
      if (!bm.value) return fail('\u8bf7\u9009\u62e9\u8bc4\u6d4b\u96c6', bm);
      var criteria = form.querySelector('select[name="criteria_id"]');
      if (!criteria.value) return fail('\u8bf7\u9009\u62e9\u8bc4\u4ef7\u6807\u51c6', criteria);
      var selectedLowlevels = (document.getElementById('selected-lowlevel-ids').value || '').split(',').filter(Boolean);
      if (!selectedLowlevels.length) return fail('请至少勾选一个本次需要评测的 lowlevel Prompt', document.getElementById('bm-preview'));
      return true;
    }}
    window.updateTaskResourceLinks();
    document.addEventListener('click', function(e) {{
      document.querySelectorAll('.ts-wrap.open').forEach(function(w) {{
        if (!w.contains(e.target)) w.classList.remove('open');
      }});
    }});

    </script>
    '''
    return render_page("\u8bc4\u6d4b\u4efb\u52a1", content, active="tasks")


@app.route("/tasks/create", methods=["POST"])
def tasks_create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("\u4efb\u52a1\u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a", "error")
        return redirect(url_for("tasks_page"))
    # Parse the single checkpoint value (keep compatibility with older clients).
    model_raw = request.form.get("model_ids", "")
    model_ids = [m.strip() for m in model_raw.split(",") if m.strip()] if model_raw else request.form.getlist("model_ids")
    # New evaluation tasks bind exactly one checkpoint. Keep the first value if
    # an older client still submits a comma-separated multi-select payload.
    model_ids = model_ids[:1]
    selected_prompt_ids = [p.strip() for p in request.form.get("selected_prompt_ids", "").split(",") if p.strip()]
    selected_lowlevel_ids = [p.strip() for p in request.form.get("selected_lowlevel_ids", "").split(",") if p.strip()]
    edit_id = request.form.get("edit_id", "").strip()
    edit_target = next((item for item in EVAL_TASKS if item["id"] == edit_id), None) if edit_id else None
    task_payload = {
        "name": name,
        "display_name": name,
        "publish_status": request.form.get("publish_status", "未发布") if request.form.get("publish_status") in ("未发布", "已发布") else "未发布",
        "project": request.form.get("project", "").strip(),
        "task_mode": request.form.get("task_mode", "Evaluaton").strip() or "Evaluaton",
        "collect_type": "test",
        "due_date": request.form.get("due_date", "").strip(),
        "task_tags": [],
        "description": request.form.get("description", "").strip(),
        "device": request.form.get("device", "").strip(),
        "deploy_mode": request.form.get("deploy_mode", "").strip(),
        "benchmark_id": request.form.get("benchmark_id", ""),
        "scene_id": "",
        "criteria_id": request.form.get("criteria_id", ""),
        "selected_prompt_ids": selected_prompt_ids,
        "selected_lowlevel_ids": selected_lowlevel_ids,
        "eval_type": request.form.get("eval_type", "preference"),
        "model_ids": model_ids,
        "priority": request.form.get("priority", "\u4e2d"),
        "total_sessions": int(request.form.get("total_sessions", 30)),
    }
    if edit_target and edit_target.get("publish_status") == "未发布":
        edit_target.update(task_payload)
        flash(f"评测任务「{name}」保存成功", "success")
        return redirect(url_for("tasks_page"))
    if edit_id:
        flash("仅未发布状态的评测任务支持编辑", "error")
        return redirect(url_for("tasks_page"))
    new_no = 1000 + len(EVAL_TASKS) + 1
    EVAL_TASKS.append({
        "id": f"t{len(EVAL_TASKS)+1}",
        "task_no": new_no,
        "status": "\u672a\u5f00\u59cb",
        "publish_status": "未发布",
        "collect_done": 0, "eval_done": 0, "completed_sessions": 0,
        "created_by": "Joanna Qiao",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        **task_payload,
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
    if t and t.get("publish_status") == "已发布" and t["status"] == "\u672a\u5f00\u59cb":
        t["status"] = "\u91c7\u96c6\u4e2d"
        msg = f"\u4efb\u52a1\u300c{t['name']}\u300d\u5df2\u5f00\u542f"
    return redirect(f"/tasks?toast={msg}" if msg else "/tasks")


@app.route("/tasks/<tid>/publish")
def task_publish(tid):
    task = next((item for item in EVAL_TASKS if item["id"] == tid), None)
    if task and task.get("publish_status") == "未发布":
        task["publish_status"] = "已发布"
        flash(f"评测任务「{task['name']}」已发布", "success")
    return redirect(url_for("tasks_page"))


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
    if t and t.get("publish_status") == "未发布":
        EVAL_TASKS.remove(t)
        flash(f"评测任务「{t['name']}」已删除", "success")
    elif t:
        flash("已发布状态的评测任务不支持删除", "error")
    return redirect(url_for("tasks_page"))


@app.route("/tasks/<tid>/analyze")
def task_analyze(tid):
    t = next((x for x in EVAL_TASKS if x["id"] == tid), None)
    if t and t["status"] == "\u8bc4\u6d4b\u5b8c\u6210":
        t["status"] = "\u5206\u6790\u5b8c\u6210"
        flash(f"\u4efb\u52a1\u300c{t['name']}\u300d\u5206\u6790\u5b8c\u6210", "success")
    return redirect(url_for("tasks_page"))


@app.route("/tasks/<tid>/statistics")
def task_statistics(tid):
    task = next((x for x in EVAL_TASKS if x["id"] == tid), None)
    if not task:
        return redirect(url_for("tasks_page"))
    benchmark = get_benchmark(task.get("benchmark_id", "")) or {}
    checkpoint_ids = list(task.get("model_ids", []))
    if not checkpoint_ids and task.get("ckpt_id"):
        checkpoint_ids = [str(task["ckpt_id"])]
    checkpoint_names = [get_model_name(checkpoint_id) for checkpoint_id in checkpoint_ids]
    requested_checkpoint_id = request.args.get("checkpoint", "")
    selected_checkpoint_id = (
        requested_checkpoint_id
        if requested_checkpoint_id in checkpoint_ids
        else (checkpoint_ids[0] if checkpoint_ids else "")
    )
    selected_checkpoint_index = (
        checkpoint_ids.index(selected_checkpoint_id)
        if selected_checkpoint_id in checkpoint_ids else 0
    )
    if checkpoint_names:
        checkpoint_control = (
            f'<b class="stat-checkpoint-static" title="{html.escape(checkpoint_names[selected_checkpoint_index], quote=True)}">'
            f'{html.escape(checkpoint_names[selected_checkpoint_index])}</b>'
        )
    else:
        checkpoint_control = '<b class="stat-checkpoint-static">--</b>'
    selected_prompt_ids = task.get("selected_prompt_ids", []) or benchmark.get("prompt_ids", [])
    criterion = get_criterion(task.get("criteria_id", "")) or {}
    result_definitions = normalize_result_definitions(criterion.get("result_definitions", {}))
    result_types = [item["type"] for item in result_definitions] or ["成功", "失败"]
    prompt_rows = []
    selected_lowlevel_ids = set(task.get("selected_lowlevel_ids", []))
    for prompt_id in selected_prompt_ids:
        prompt = get_prompt(prompt_id)
        if not prompt:
            continue
        low_levels = [low for low in prompt.get("low_levels", []) if not selected_lowlevel_ids or low.get("id") in selected_lowlevel_ids]
        if not low_levels:
            continue
        prompt_rows.append((prompt, low_levels))
    if not prompt_rows:
        prompt_rows = [(PROMPTS[0], PROMPTS[0].get("low_levels", []) or [{"zh": "--", "en": ""}])]
    secondary_values = result_types
    lowlevel_total = sum(max(len(low_levels), 1) for _, low_levels in prompt_rows)

    def make_statuses(seed_index, include_unexecuted=False):
        pattern = []
        for trial in range(10):
            # Low Level Prompt 可能在某个轮次未实际执行，该轮结果保持为空。
            if include_unexecuted and (seed_index * 5 + trial * 3) % 17 == 0:
                pattern.append(None)
                continue
            value_index = (seed_index * 3 + trial) % len(secondary_values)
            value = secondary_values[value_index]
            pattern.append(value)
        return pattern

    def render_result_cells(statuses):
        result_counts = {}
        status_cells = []
        for status in statuses:
            if status is None:
                status_cells.append('<td class="stat-result-empty"></td>')
                continue
            value = status
            result_counts[value] = result_counts.get(value, 0) + 1
            css_class = "fail" if result_type_is_failure(value) else "ok"
            status_cells.append(f'<td><span class="stat-result {css_class}">{html.escape(value)}</span></td>')
        executed_count = sum(result_counts.values())
        detail_html = "".join(
            f'<div class="stat-secondary-item"><span class="stat-result {"fail" if result_type_is_failure(value) else "ok"}">{html.escape(value)}</span><b>{count} 次</b><em>{count / executed_count * 100:.1f}%</em></div>'
            for value, count in result_counts.items()
        )
        summary_html = f'共 {executed_count} 次'
        secondary_html = f'<div class="stat-secondary-content"><div class="stat-secondary-summary">{summary_html}</div><div class="stat-secondary-details" hidden>{detail_html}</div></div>'
        return "".join(status_cells), secondary_html

    matrix_rows = []
    total_runs = 0
    for row_index, (prompt, low_levels) in enumerate(prompt_rows):
        prompt_text = prompt.get("high_level") or prompt.get("high_level_en") or "--"
        prompt_id = prompt.get("id", "")
        prompt_label = f"{prompt_text} #{prompt_id}" if prompt_id else prompt_text
        prompt_en = prompt.get("high_level_en", "")
        statuses = make_statuses(row_index + selected_checkpoint_index * 11)
        status_cells, secondary_html = render_result_cells(statuses)
        group_id = f'stat-group-{row_index}'
        prompt_tree_html = f'<div class="stat-tree-row stat-tree-parent-row"><button type="button" class="stat-tree-toggle" aria-label="展开 Prompt" aria-expanded="false" onclick="toggleStatPrompt(\'{group_id}\', this)">›</button><span><b>{html.escape(prompt_label)}</b>{("<em>" + html.escape(prompt_en) + "</em>") if prompt_en else ""}</span></div>'
        matrix_rows.append(
            f'<tr class="stat-highlevel-row"><td class="stat-prompt-tree-cell">{prompt_tree_html}</td>'
            + "".join(status_cells)
            + f'<td class="stat-secondary-cell">{secondary_html}</td></tr>'
        )
        for low_index, low in enumerate(low_levels):
            low_text = low.get("zh") or low.get("en") or "--"
            low_id = low.get("id", "")
            low_label = f"{low_text} #{low_id}" if low_id else low_text
            low_en = low.get("en", "")
            child_statuses = make_statuses(row_index * 7 + low_index + 1 + selected_checkpoint_index * 11, include_unexecuted=True)
            total_runs += sum(status is not None for status in child_statuses)
            child_cells, child_secondary = render_result_cells(child_statuses)
            child_html = f'<div class="stat-tree-row stat-tree-child-row"><span class="stat-tree-branch" aria-hidden="true"></span><span><b>{html.escape(low_label)}</b>{("<em>" + html.escape(low_en) + "</em>") if low_en and low_text != low_en else ""}</span></div>'
            matrix_rows.append(
                f'<tr class="stat-lowlevel-row" data-stat-group="{group_id}" style="display:none;"><td class="stat-prompt-tree-cell">{child_html}</td>'
                + child_cells
                + f'<td class="stat-secondary-cell">{child_secondary}</td></tr>'
            )
    rows = "".join(matrix_rows)
    headers = "".join(f"<th>T{i}</th>" for i in range(1, 11))
    content = f'''<div class="stat-page">
      <div class="stat-head"><h1>评测统计</h1><button class="ant-btn" type="button" onclick="exportEvalStatistics()">导出</button></div>
      <div class="stat-summary">
        <div><span>评测集</span><b title="{html.escape(benchmark.get("name", "--"), quote=True)}">{html.escape(benchmark.get("name", "--"))}</b></div>
        <div class="stat-summary-ckpt"><span>checkpoint</span>{checkpoint_control}</div>
        <div><span>Prompt 总数</span><b>{lowlevel_total}</b></div>
        <div><span>执行次数</span><b>{total_runs}</b></div>
      </div>
      <div class="stat-table-wrap"><table class="stat-matrix"><thead><tr><th class="stat-prompt-head">prompt</th>{headers}<th class="stat-secondary-head"><div class="stat-secondary-head-inner"><span>结果统计</span><a href="javascript:;" id="stat-detail-toggle" class="stat-detail-toggle" onclick="toggleStatDetails()">展开详情</a></div></th></tr></thead><tbody>{rows}</tbody></table></div>
    </div>
    <script>
      function toggleStatPrompt(groupId, button) {{
        var rows = document.querySelectorAll('[data-stat-group="' + groupId + '"]');
        var open = button.getAttribute('aria-expanded') !== 'true';
        rows.forEach(function(row) {{ row.style.display = open ? '' : 'none'; }});
        button.setAttribute('aria-expanded', open ? 'true' : 'false');
        button.textContent = open ? '⌄' : '›';
      }}
      function setStatDetails(show) {{
        document.querySelectorAll('.stat-secondary-details').forEach(function(details) {{ details.hidden = !show; }});
        document.querySelectorAll('.stat-secondary-summary').forEach(function(summary) {{ summary.hidden = show; }});
        var toggle = document.getElementById('stat-detail-toggle');
        if (toggle) toggle.textContent = show ? '收起详情' : '展开详情';
      }}
      function toggleStatDetails() {{
        var toggle = document.getElementById('stat-detail-toggle');
        setStatDetails(toggle && toggle.textContent === '展开详情');
      }}
      function exportEvalStatistics() {{
        var table = document.querySelector('.stat-matrix');
        if (!table) return;
        var rows = [];
        var headerCells = table.querySelectorAll('thead th');
        rows.push(Array.from(headerCells).map(function(cell) {{ return (cell.textContent || '').replace(/\\s+/g, ' ').trim(); }}));
        table.querySelectorAll('tbody tr').forEach(function(tr) {{
          if (tr.cells.length < 2) return;
          rows.push(Array.from(tr.cells).map(function(cell) {{ return (cell.textContent || '').replace(/\\s+/g, ' ').trim(); }}));
        }});
        if (rows.length <= 1) {{
          if (window.showToast) window.showToast('暂无数据可导出', 'warning');
          return;
        }}
        var csv = rows.map(function(row) {{ return row.map(function(value) {{
          var text = String(value).replace(/"/g, '""');
          return /[,"\\n]/.test(text) ? '"' + text + '"' : text;
        }}).join(','); }}).join('\\n');
        var url = URL.createObjectURL(new Blob(['\\uFEFF' + csv], {{type:'text/csv;charset=utf-8'}}));
        var link = document.createElement('a');
        link.href = url;
        link.download = '评测统计_' + new Date().toISOString().slice(0, 10) + '.csv';
        document.body.appendChild(link); link.click(); link.remove();
        setTimeout(function() {{ URL.revokeObjectURL(url); }}, 1000);
        if (window.showToast) window.showToast('已导出 ' + (rows.length - 1) + ' 条数据', 'success');
      }}
    </script>
    <style>
      .stat-page {{ background:#fff;border:1px solid #e6ebef;border-radius:8px;padding:22px 24px 24px; }}
      .stat-head {{ display:flex;align-items:center;justify-content:space-between;margin-bottom:20px; }}
      .stat-head h1 {{ margin:0;font-size:20px; }}
      .stat-summary {{ display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:20px;padding:14px 16px;background:#f8fafb;border:1px solid #edf0f2;border-radius:8px; }}
      .stat-summary>div {{ display:flex;flex-direction:column;gap:6px;min-width:0;padding-right:16px;border-right:1px solid #e7ebef; }} .stat-summary>div:last-child {{ border-right:0; }}
      .stat-summary span {{ color:rgba(0,0,0,.45);font-size:12px; }} .stat-summary b {{ overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:15px; }}
      .stat-checkpoint-static {{ display:block;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }}
      .stat-table-wrap {{ overflow:auto;border:1px solid #dfe5e9;border-radius:8px;background:#fff; }}
      .stat-matrix {{ border-collapse:separate;border-spacing:0;min-width:1650px;width:100%;font-size:12px;color:rgba(0,0,0,.72); }}
      .stat-matrix th,.stat-matrix td {{ border-right:1px solid #edf0f2;border-bottom:1px solid #edf0f2;padding:12px;white-space:nowrap;text-align:center;height:56px;box-sizing:border-box; }}
      .stat-matrix th {{ height:44px;background:#f5f7f9;color:rgba(0,0,0,.55);font-weight:600;position:sticky;top:0;z-index:3; }} .stat-matrix tr:last-child td {{ border-bottom:0; }} .stat-matrix th:last-child,.stat-matrix td:last-child {{ border-right:0; }} .stat-matrix tbody tr:hover td {{ background:#f8fbfc; }}
      .stat-matrix th:first-child,.stat-matrix td:first-child {{ text-align:left;position:sticky;left:0;z-index:2; }} .stat-matrix th:first-child {{ background:#f5f7f9;z-index:4; }} .stat-matrix td:first-child {{ background:#fff; }}
      .stat-prompt-head {{ min-width:420px; }} .stat-prompt-tree-cell {{ min-width:420px;max-width:520px;text-align:left !important;white-space:normal !important;vertical-align:top; }}
      .stat-tree-row {{ position:relative;display:flex;align-items:flex-start;gap:8px;min-height:42px;padding:3px 0 3px 2px;color:rgba(0,0,0,.72);font-size:12px;line-height:1.5; }} .stat-tree-row b {{ font-weight:500; }} .stat-tree-row em {{ display:block;color:rgba(0,0,0,.42);font-size:11px;font-style:normal;line-height:1.4;margin-top:2px; }} .stat-tree-parent-row {{ padding-bottom:7px;margin-bottom:3px;border-bottom:1px solid #edf0f2; }} .stat-tree-parent-row b {{ font-weight:600;color:rgba(0,0,0,.84); }} .stat-tree-child-row {{ margin-left:24px;padding-left:14px;border-left:1px solid #d9e5e8; }} .stat-tree-toggle {{ display:inline-flex;align-items:center;justify-content:center;width:18px;height:20px;padding:0;border:0;background:transparent;color:#1F80A0;font-size:16px;line-height:1;cursor:pointer;flex:none; }} .stat-tree-branch {{ position:absolute;left:-1px;top:20px;width:10px;border-top:1px solid #d9e5e8; }}
      .stat-result {{ display:inline-flex;align-items:center;justify-content:center;min-width:54px;border:1px solid transparent;border-radius:4px;padding:4px 8px;font-size:11px;line-height:1.2; }} .stat-result.ok {{ color:#237b3b;background:#f0f9f1;border-color:#b7e1bd; }} .stat-result.fail {{ color:#c9362b;background:#fff1f0;border-color:#ffccc7; }}
      .stat-secondary-head-inner {{ display:flex;align-items:center;justify-content:space-between;gap:10px; }} .stat-detail-toggle {{ color:#1F80A0;text-decoration:none;font-size:11px;font-weight:400;white-space:nowrap; }} .stat-detail-toggle:hover {{ text-decoration:underline; }}
      .stat-secondary-cell {{ min-width:200px;text-align:left !important;white-space:normal !important; }} .stat-secondary-content {{ min-height:22px; }} .stat-secondary-summary {{ color:rgba(0,0,0,.65);font-size:11px;line-height:1.5; }} .stat-secondary-item {{ display:flex;align-items:center;gap:6px;margin:3px 0; }} .stat-secondary-item .stat-result {{ min-width:68px; }} .stat-secondary-item b {{ color:rgba(0,0,0,.65);font-size:11px;font-weight:500; }} .stat-secondary-item em {{ color:rgba(0,0,0,.45);font-size:11px;font-style:normal;margin-left:auto; }}
    </style>'''
    return render_page("评测统计", content, active="tasks")
    prompt_rows = []
    for pid in benchmark.get("prompt_ids", []):
        prompt = get_prompt(pid)
        if not prompt:
            continue
        for low in prompt.get("low_levels", []):
            prompt_rows.append((low.get("en") or low.get("zh", "--"), low.get("zh", "--")))
    if not prompt_rows:
        prompt_rows = [("Pick up the cell phone", "拾取手机"), ("Pick up the big tape", "拾取胶带")]
    checkpoint_result_profiles = [
        ["成功", "失败", "成功", "成功", "失败", "成功", "重试1次成功", "成功", "失败", "成功"],
        ["成功", "成功", "重试1次成功", "成功", "失败", "成功", "成功", "重试2次成功", "失败", "成功"],
        ["失败", "成功", "失败", "成功", "重试1次成功", "失败", "成功", "成功", "失败", "成功"],
        ["成功", "成功", "成功", "重试1次成功", "成功", "成功", "失败", "成功", "重试2次成功", "成功"],
    ]
    status_values = checkpoint_result_profiles[selected_checkpoint_index % len(checkpoint_result_profiles)]
    status_html = lambda value: f'<span class="stat-result {"fail" if value == "失败" else "retry" if value.startswith("重试") else "ok"}">{value}</span>'
    table_rows = []
    row_totals = []
    for index, (en, zh) in enumerate(prompt_rows):
        trial_results = [status_values[(index + trial) % len(status_values)] for trial in range(10)]
        trial_scores = [0 if result == "失败" else 3 for result in trial_results]
        row_total = sum(trial_scores)
        row_totals.append(row_total)
        table_rows.append(
            f'<tr><td class="stat-text"><div class="stat-prompt-cell"><span class="stat-prompt-zh">{html.escape(zh)}</span><span class="stat-prompt-en">{html.escape(en)}</span></div></td>'
            + "".join(f'<td>{status_html(result)}</td>' for result in trial_results)
            + f'<td class="stat-score">{",".join(str(score) for score in trial_scores)}</td><td class="stat-total">{row_total}</td></tr>'
        )
    rows = "".join(table_rows)
    average_score = sum(row_totals) / len(row_totals) if row_totals else 0
    headers = "".join(f"<th>T{i}</th>" for i in range(1, 11))
    content = f'''<div class="stat-page">
      <div class="stat-head">
        <h1>评测统计</h1>
      </div>
      <div class="stat-summary">
        <div><span>评测集</span><b title="{html.escape(benchmark.get("name", "--"), quote=True)}">{html.escape(benchmark.get("name", "--"))}</b></div>
        <div class="stat-summary-ckpt"><span>checkpoint</span>{checkpoint_control}</div>
        <div><span>Prompt 总数</span><b>{len(prompt_rows)}</b></div>
        <div><span>执行次数</span><b>{len(prompt_rows) * 10}</b></div>
        <div><span>平均分</span><b>{average_score:.1f}</b></div>
      </div>
      <div class="stat-table-wrap">
        <table class="stat-matrix"><thead><tr><th class="stat-prompt-head">prompt</th>{headers}<th>分数列表</th><th class="stat-total-head">总分</th></tr></thead><tbody>{rows}</tbody></table>
      </div>
    </div>'''
    content += '''<script>
      function switchStatCheckpoint(checkpointId) {
        var url = new URL(window.location.href);
        url.searchParams.set('ckpt', checkpointId);
        window.location.href = url.toString();
      }
    </script>'''
    content += '''<style>
      .stat-page { background:#fff; border:1px solid #e6ebef; border-radius:8px; padding:22px 24px 24px; box-sizing:border-box; box-shadow:0 1px 2px rgba(16,24,40,.03); }
      .stat-head { margin-bottom:20px; }
      .stat-head h1 { margin:0; color:rgba(0,0,0,.85); font-size:20px; line-height:1.4; font-weight:600; }
      .stat-summary { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:12px; margin-bottom:20px; padding:14px 16px; background:#f8fafb; border:1px solid #edf0f2; border-radius:8px; }
      .stat-summary div { display:flex; flex-direction:column; align-items:flex-start; justify-content:center; gap:6px; min-width:0; padding-right:16px; border-right:1px solid #e7ebef; }
      .stat-summary div:last-child { padding-right:0; border-right:0; }
      .stat-summary span { flex:none; color:rgba(0,0,0,.45); font-size:12px; white-space:nowrap; }
      .stat-summary b { min-width:0; color:rgba(0,0,0,.85); font-size:15px; font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .stat-summary-ckpt { align-items:flex-start !important; flex-direction:column; justify-content:center !important; gap:6px !important; }
      .stat-ckpt-select { display:block; width:100%; min-width:0; max-width:100%; height:30px; box-sizing:border-box; border:1px solid #d9dfe4; border-radius:6px; padding:0 30px 0 9px; background-color:#fff; background-image:url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%23595959' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"); background-repeat:no-repeat; background-position:right 10px center; color:rgba(0,0,0,.82); font-size:13px; outline:none; cursor:pointer; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; appearance:none; -webkit-appearance:none; }
      .stat-ckpt-select:focus { border-color:#1F80A0; box-shadow:0 0 0 2px rgba(31,128,160,.12); }
      .stat-ckpt-select:disabled { border-color:#edf0f2; background-color:#fafbfc; color:rgba(0,0,0,.65); cursor:default; opacity:1; }
      .stat-table-wrap { overflow:auto; border:1px solid #dfe5e9; border-radius:8px; background:#fff; }
      .stat-matrix { border-collapse:separate; border-spacing:0; min-width:1500px; width:100%; font-size:12px; color:rgba(0,0,0,.72); }
      .stat-matrix th, .stat-matrix td { border-right:1px solid #edf0f2; border-bottom:1px solid #edf0f2; padding:12px 12px; white-space:nowrap; text-align:center; height:48px; box-sizing:border-box; }
      .stat-matrix th { height:44px; background:#f5f7f9; color:rgba(0,0,0,.55); font-weight:600; letter-spacing:0; position:sticky; top:0; z-index:3; }
      .stat-matrix tr:last-child td { border-bottom:0; }
      .stat-matrix th:last-child, .stat-matrix td:last-child { border-right:0; }
      .stat-matrix tbody tr:hover td { background:#f8fbfc; }
      .stat-matrix th:first-child, .stat-matrix td:first-child { text-align:left; position:sticky; left:0; z-index:2; }
      .stat-matrix th:first-child { background:#f5f7f9; z-index:4; }
      .stat-matrix td:first-child { background:#fff; }
      .stat-prompt-head { min-width:390px; }
      .stat-text { min-width:390px; max-width:460px; }
      .stat-prompt-cell { display:flex; flex-direction:column; gap:4px; min-width:0; white-space:normal; }
      .stat-prompt-zh { color:rgba(0,0,0,.82); font-size:13px; font-weight:500; line-height:1.45; }
      .stat-prompt-en { color:rgba(0,0,0,.45); font-size:11px; line-height:1.4; }
      .stat-result { display:inline-flex; align-items:center; justify-content:center; min-width:54px; border:1px solid transparent; border-radius:4px; padding:4px 8px; font-size:11px; line-height:1.2; }
      .stat-result.ok { color:#237b3b; background:#f0f9f1; border-color:#b7e1bd; }
      .stat-result.fail { color:#c9362b; background:#fff1f0; border-color:#ffccc7; }
      .stat-result.retry { color:#1769aa; background:#eaf5ff; border-color:#b7dcfa; }
      .stat-score { color:rgba(0,0,0,.55); font-family:'SF Mono',Menlo,Consolas,monospace; font-size:11px; }
      .stat-total-head, .stat-total { min-width:82px; }
      .stat-total { font-weight:600; color:#237b3b; background:#f6ffed; }
      @media (max-width:900px) { .stat-summary { grid-template-columns:repeat(2,minmax(0,1fr)); gap:0 16px; } .stat-summary div { padding:9px 0; border-right:0; border-bottom:1px solid #e7ebef; } .stat-summary div:nth-last-child(-n+2) { border-bottom:0; } }
      @media (max-width:700px) { .stat-page { padding:18px 16px 20px; } .stat-summary { grid-template-columns:1fr; } .stat-summary div:nth-last-child(2) { border-bottom:1px solid #e7ebef; } .stat-summary div:last-child { border-bottom:0; } }
    </style>'''
    return render_page("评测统计", content, active="tasks")


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
    endpoint_modes_wb = endpoint_mode_buttons("wb-mode", "active", "wbMode")

    content = f'''
    <div class="eval2-ipad-shell"><div class="eval2-ipad-screen">
    <div class="wb-landing" id="wb-landing"><h1>端侧示意</h1><p>端侧评测任务执行入口</p><a class="wb-enter" href="/evaluate2/setup?step=1">进入端侧示意</a></div>
    <div class="wb-wizard" id="wb-wizard" hidden>
      <div class="wb-stepper"><span class="active">1 模式选择</span><i>→</i><span>2 任务选择</span><i>→</i><span>3 场景与提示词</span><i>→</i><span>4 执行评测</span></div>
      <section class="wb-panel wb-panel-active" data-wb-step="1"><div class="wb-panel-title">模式选择 <small>选择任务类型后，将进行设备自检</small></div><div class="wb-mode-grid">{endpoint_modes_wb}</div><button class="wb-primary" onclick="wbSelfCheck(this)">开始自检</button><div class="wb-note">自检将检查机器人、相机、控制器与网络连接</div></section>
      <section class="wb-panel" data-wb-step="2"><div class="wb-panel-title">任务选择 <small class="wb-pass">● 设备自检通过</small></div><div class="wb-fields"><label>项目<select><option>eval</option><option>预训练</option><option>回归验证</option></select></label><label>任务<select id="wb-task"><option value="">请选择任务</option>{"".join(f'<option value="{t["id"]}">{t["task_no"]}：{t.get("name", "评测任务")}</option>' for t in active_tasks)}</select></label></div><button class="wb-primary" onclick="wbNext(3)">确认任务</button></section>
      <section class="wb-panel" data-wb-step="3"><div class="wb-panel-title">任务信息</div><div class="wb-task-section"><h2>场景准备</h2><div class="wb-scene"><div class="wb-scene-description"><b>场景描述</b><span>自然光，家庭场景，至少需要打开和放置两个房间</span></div><div class="wb-media"><div>场景图片<br><span>▧　▧　▧</span></div><div>场景视频<br><span>▶</span></div></div></div></div><div class="wb-task-section"><h2>提示词</h2><div class="wb-prompt-tree"><div class="wb-prompt-tree-group"><div class="wb-prompt-tree-parent">提示词组 1 · 房间整理</div><div class="wb-prompt-tree-children"><div class="wb-prompt-tree-child">抓住小猫 <small>Pick up the cat</small></div><div class="wb-prompt-tree-child">把小猫放进被窝 <small>Put the cat in the blanket</small></div></div></div><div class="wb-prompt-tree-group"><div class="wb-prompt-tree-parent">提示词组 2 · 床铺操作</div><div class="wb-prompt-tree-children"><div class="wb-prompt-tree-child">掀开被子 <small>Lift up the blanket</small></div><div class="wb-prompt-tree-child">盖上被子 <small>Cover it up</small></div></div></div></div></div><button class="wb-primary" onclick="wbNext(4)">场景已就绪，开始评测</button></section>
      <section class="wb-panel" data-wb-step="4"><div class="wb-panel-title">执行评测 <small>逐条完成任务，提交结果后进入下一条</small></div><div class="wb-camera-grid"><div>左手臂镜头<div class="wb-camera">640×480 · 已连接</div></div><div>头部镜头<div class="wb-camera">640×480 · 已连接</div></div><div>右手臂镜头<div class="wb-camera">640×480 · 已连接</div></div></div><div class="wb-task-list"><div class="active"><b>1</b> 把小猫放进被窝 <button onclick="wbResult()">▶</button></div><div><b>2</b> 掀开被子 <button onclick="wbResult()">▶</button></div><div><b>3</b> 把小猫放进被子 <button onclick="wbResult()">▶</button></div><div><b>4</b> 盖上被子 <button onclick="wbResult()">▶</button></div></div></section>
    </div>
    </div></div>
    <div class="filter-bar" style="display:none;">
      <input type="text" id="f2-id" placeholder="\u4efb\u52a1 ID" style="min-width:120px;">
      <select id="f2-bm" style="min-width:140px;"><option value="">Benchmark</option>{"".join(f'<option>{b["name"]}</option>' for b in BENCHMARKS)}</select>
      <select id="f2-pri" style="min-width:110px;"><option value="">\u4f18\u5148\u7ea7</option><option>\u9ad8</option><option>\u4e2d</option><option>\u4f4e</option></select>
      <button class="ant-btn" onclick="eval2Clear()">\u6e05\u7a7a</button>
      <button class="ant-btn ant-btn-primary" onclick="eval2Filter()">\u641c\u7d22</button>
    </div>
    <div class="ant-card ant-card-bordered" style="display:none;">
      <table class="ant-table" id="eval2-tbl">
        <thead><tr>
          <th>\u4efb\u52a1 ID</th><th>Benchmark</th><th>\u8fdb\u5ea6</th><th>\u4f18\u5148\u7ea7</th><th>\u64cd\u4f5c</th>
        </tr></thead>
        <tbody>{rows}{empty}</tbody>
      </table>
    </div>
    <script>
    function wbStart() {{ document.getElementById('wb-landing').hidden=true; document.getElementById('wb-wizard').hidden=false; }}
    function wbMode(btn) {{ document.querySelectorAll('.wb-mode').forEach(function(x){{x.classList.remove('active')}}); btn.classList.add('active'); }}
    function wbSelfCheck(btn) {{ btn.textContent='自检中...'; btn.disabled=true; setTimeout(function(){{ btn.textContent='设备自检通过'; btn.classList.add('passed'); wbNext(2); }},700); }}
    function wbNext(step) {{ document.querySelectorAll('[data-wb-step]').forEach(function(x){{x.classList.toggle('wb-panel-active', Number(x.dataset.wbStep)===step);}}); document.querySelectorAll('.wb-stepper span').forEach(function(x,i){{x.classList.toggle('active',i<step);}}); }}
    function wbResult() {{ var m=document.createElement('div'); m.className='wb-result-mask'; m.innerHTML='<div class="wb-result-dialog"><h3>填写评测结果</h3><label>评测结果<select><option>成功</option><option>失败</option><option>重试1次成功</option><option>重试2次成功</option><option>重试3次成功</option></select></label><label>评测指标<input placeholder="填写配置的指标"></label><div class="wb-result-actions"><button onclick="this.closest(\'.wb-result-mask\').remove()">取消</button><button class="primary" onclick="this.closest(\'.wb-result-mask\').remove();window.showToast(\'已提交，进入下一条\')">提交并下一条</button></div></div>'; document.body.appendChild(m); }}
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
    function eval2SelectMode(btn) {{ document.querySelectorAll('.eval2-mode').forEach(function(x){{x.classList.remove('selected')}}); btn.classList.add('selected'); }}
    function eval2SelfCheck() {{ var b=document.getElementById('eval2-self-check'); b.textContent='自检中...'; b.disabled=true; setTimeout(function(){{ b.textContent='设备自检通过'; b.classList.add('passed'); document.getElementById('eval2-setup').hidden=false; document.getElementById('eval2-device').textContent='设备：已连接'; }},700); }}
    function eval2EnterTask() {{ var id=document.getElementById('eval2-task').value; if(!id){{ alert('请选择任务'); return; }} window.location='/evaluate2/'+id+'/run?step=0'; }}
    </script>
    <style>
      .eval2-flow {{ background:#fff;border:1px solid #f0f0f0;border-radius:10px;padding:28px 32px;margin-bottom:20px; }}
      .eval2-flow-head {{ display:flex;justify-content:space-between;align-items:flex-start; }} .eval2-flow h2 {{ margin:0;font-size:22px; }} .eval2-flow-head p {{ margin:6px 0 0;color:rgba(0,0,0,.45); }} .eval2-device {{ color:#52a66d;font-size:13px; }}
      .eval2-mode-grid {{ display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0; }} .eval2-mode {{ min-height:130px;background:#fff;border:1px solid #d9d9d9;border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;font-size:16px;cursor:pointer; }} .eval2-mode.selected {{ border:2px solid #2463eb;background:#f4f7ff; }} .eval2-mode-icon {{ font-size:32px;color:#2463eb; }}
      .eval2-primary {{ width:100%;height:46px;border:0;border-radius:7px;background:#2463eb;color:#fff;font-size:16px;cursor:pointer; }} .eval2-primary.passed {{ background:#2eaf68; }} .eval2-check-note {{ text-align:center;color:rgba(0,0,0,.45);font-size:13px;margin-top:10px; }} .eval2-setup {{ margin-top:24px;border-top:1px solid #f0f0f0;padding-top:22px; }} .eval2-section-title {{ font-size:17px;font-weight:600;margin:16px 0; }} .eval2-ok {{ color:#2eaf68;font-size:13px;font-weight:400;margin-left:12px; }} .eval2-select-row {{ display:grid;grid-template-columns:1fr 2fr;gap:18px; }} .eval2-select-row label {{ display:flex;flex-direction:column;gap:7px;color:rgba(0,0,0,.65);font-size:13px; }} .eval2-select-row select {{ height:38px;border:1px solid #d9d9d9;border-radius:6px;padding:0 10px;background:#fff; }} .eval2-context {{ display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px; }} .eval2-context > div {{ background:#fafafa;border:1px solid #f0f0f0;border-radius:7px;padding:14px; }} .eval2-context p {{ color:rgba(0,0,0,.45);font-size:13px;margin:8px 0 0; }}
      @media(max-width:800px){{.eval2-mode-grid,.eval2-select-row,.eval2-context{{grid-template-columns:1fr 1fr}}}} @media(max-width:560px){{.eval2-mode-grid,.eval2-select-row,.eval2-context{{grid-template-columns:1fr}}}}
      .wb-landing {{ width:100%;height:100%;min-height:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#fff;border:0;border-radius:0;box-sizing:border-box; }} .wb-landing h1 {{ font-size:30px;margin:0 0 10px; }} .wb-landing p {{ color:rgba(0,0,0,.45);margin:0 0 34px; }} .wb-enter {{ width:min(760px,90%);height:64px;border:0;border-radius:8px;background:#2463eb;color:#fff;font-size:22px;cursor:pointer;display:flex;align-items:center;justify-content:center;text-decoration:none; }}
      .wb-wizard {{ width:100%;height:100%;overflow:auto;box-sizing:border-box;background:#f7f8fa;padding:22px;border-radius:0; }} .wb-stepper {{ display:flex;justify-content:center;gap:14px;align-items:center;margin-bottom:18px;color:#a0a5ad;font-size:13px; }} .wb-stepper span.active {{ color:#2463eb;font-weight:600; }} .wb-stepper i {{ color:#c5c9d0;font-style:normal; }} .wb-panel {{ display:none;background:#fff;border-radius:9px;padding:28px;border:1px solid #edf0f3; }} .wb-panel.wb-panel-active {{ display:block; }} .wb-panel-title {{ font-size:22px;font-weight:600;margin-bottom:20px; }} .wb-panel-title small {{ font-size:13px;color:#8a9099;font-weight:400;margin-left:10px; }} .wb-pass {{ color:#2eaf68 !important; }} .wb-mode-grid {{ display:grid;grid-template-columns:repeat(2,1fr);gap:18px;max-width:820px;margin:0 auto 28px; }} .wb-mode {{ min-height:150px;border:1px solid #dfe3e8;background:#fff;border-radius:8px;font-size:17px;display:flex;flex-direction:column;gap:15px;align-items:center;justify-content:center;cursor:pointer; }} .wb-mode.active {{ border:2px solid #2463eb;background:#f4f7ff; }} .wb-mode b {{ font-size:34px;color:#2463eb; }} .wb-primary {{ width:100%;height:48px;border:0;border-radius:7px;background:#2463eb;color:#fff;font-size:16px;cursor:pointer; }} .wb-primary.passed {{ background:#2eaf68; }} .wb-note {{ text-align:center;color:#7e8792;margin-top:10px;font-size:13px; }} .wb-fields {{ display:grid;grid-template-columns:1fr 2fr;gap:18px;margin-bottom:24px; }} .wb-fields label,.wb-result-dialog label {{ display:flex;flex-direction:column;gap:8px;color:#5f6670;font-size:13px; }} .wb-fields select,.wb-result-dialog select,.wb-result-dialog input {{ height:40px;border:1px solid #d9dde3;border-radius:6px;padding:0 10px;background:#fff; }} .wb-scene {{ display:grid;grid-template-columns:1fr 1fr;gap:22px;padding:18px;background:#fafbfc;border:1px solid #edf0f3;border-radius:8px;margin-bottom:22px; }} .wb-scene p {{ color:#69717c;margin:8px 0 18px; }} .wb-media {{ display:grid;grid-template-columns:1fr 1fr;gap:10px;color:#7a828d;font-size:13px; }} .wb-media div {{ border:1px dashed #cdd3db;border-radius:6px;padding:18px;text-align:center; }} .wb-media span {{ display:block;font-size:30px;color:#2463eb;margin-top:18px; }} .wb-prompts {{ border:1px solid #edf0f3;border-radius:7px;margin-bottom:20px; }} .wb-prompts div {{ padding:13px 16px;border-bottom:1px solid #f0f0f0; }} .wb-prompts div:last-child {{ border:0; }} .wb-prompts b {{ display:inline-flex;width:22px;height:22px;border-radius:4px;background:#e9efff;color:#2463eb;align-items:center;justify-content:center;margin-right:10px; }} .wb-prompts small {{ color:#8a9099;margin-left:12px; }} .wb-camera-grid {{ display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;font-weight:600; }} .wb-camera {{ height:180px;background:#15191f;border-radius:7px;margin-top:8px;color:#7f8995;display:flex;align-items:center;justify-content:center;font-weight:400; }} .wb-task-list {{ border:1px solid #edf0f3;border-radius:7px; }} .wb-task-list div {{ padding:14px 16px;border-bottom:1px solid #f0f0f0;display:flex;align-items:center;gap:12px; }} .wb-task-list div:last-child {{ border:0; }} .wb-task-list div.active {{ background:#f1f6ff;color:#2463eb; }} .wb-task-list b {{ width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;background:#edf1f7;border-radius:4px; }} .wb-task-list button {{ margin-left:auto;border:0;background:transparent;color:#2463eb;cursor:pointer;font-size:16px; }} .wb-result-mask {{ position:fixed;inset:0;z-index:1100;background:rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center; }} .wb-result-dialog {{ width:560px;max-width:calc(100vw - 32px);background:#fff;border-radius:9px;padding:24px; }} .wb-result-dialog h3 {{ margin:0 0 20px; }} .wb-result-dialog label {{ margin-bottom:16px; }} .wb-result-actions {{ display:flex;justify-content:flex-end;gap:8px; }} .wb-result-actions button {{ border:1px solid #d9dde3;background:#fff;border-radius:6px;padding:8px 18px;cursor:pointer; }} .wb-result-actions .primary {{ background:#2463eb;color:#fff;border-color:#2463eb; }}
    </style>
    '''
    content += ENDPOINT_MODE_STYLE
    return render_page("\u7aef\u4fa7\u793a\u610f", content, active="evaluate2")


@app.route("/evaluate2/setup")
def evaluate2_setup():
    step = max(1, min(4, int(request.args.get("step", "1"))))
    active_tasks = [t for t in EVAL_TASKS if t.get("status") == "评测中"]
    selected_task_id = request.args.get("task", "")
    selected_task = next((task for task in active_tasks if task.get("id") == selected_task_id), None)
    if not selected_task and step >= 3 and active_tasks:
        selected_task = active_tasks[0]
        selected_task_id = selected_task["id"]
    task_options = "".join(
        f'<option value="{t["id"]}"{" selected" if t["id"] == selected_task_id else ""}>'
        f'{t["task_no"]}：{html.escape(t.get("name", "评测任务"))}</option>'
        for t in active_tasks
    )
    prompt_group_count = 2
    endpoint_modes_setup = endpoint_mode_buttons("wb-mode", "active", "wbSelectSetupMode")
    if step == 1:
        body = f'<div class="wb-step-page"><h1>模式选择</h1><p class="wb-muted">请选择任务类型，选择模式后将进行设备自检</p><div class="wb-mode-grid">{endpoint_modes_setup}</div><a class="wb-primary wb-link" href="/evaluate2/setup?step=2">开始自检</a><div class="wb-note">自检将检查机器人、相机、控制器与网络连接</div></div>'
    elif step == 2:
        body = f'''<div class="wb-step-page"><h1>任务选择 <small class="wb-pass">● 设备自检通过</small></h1><div class="wb-fields"><label>项目<select><option value="">请选择项目</option><option>基础研究</option><option>宁德应用</option><option>moz1</option><option>spirit</option><option>demo采集</option><option>预训练采集</option><option>多任务</option></select></label><label>任务<select id="wb-task-select"><option value="">请选择任务</option>{task_options}</select></label></div><button type="button" class="wb-primary" onclick="wbConfirmEndpointTask()">确认进入任务</button><script>function wbConfirmEndpointTask(){{var select=document.getElementById('wb-task-select');if(!select.value){{if(window.showToast)window.showToast('请选择任务','warning');return;}}window.location='/evaluate2/setup?step=3&task='+encodeURIComponent(select.value);}}</script></div>'''
    elif step == 3:
        task = selected_task or {}
        benchmark = get_benchmark(task.get("benchmark_id", "")) or {}
        prompt_ids = task.get("selected_prompt_ids", []) or benchmark.get("prompt_ids", [])
        selected_lowlevel_ids = set(task.get("selected_lowlevel_ids", []))
        prompt_groups = []
        for prompt_index, prompt_id in enumerate(prompt_ids, 1):
            prompt = get_prompt(prompt_id)
            if not prompt:
                continue
            lowlevels = [
                item for item in prompt.get("low_levels", [])
                if not selected_lowlevel_ids or item.get("id") in selected_lowlevel_ids
            ]
            lowlevel_html = ''.join(
                f'<div class="wb-prompt-tree-child"><span class="wb-lowlevel-index">{index}</span>'
                f'<span>{html.escape(item.get("zh", ""))}<small>{html.escape(item.get("en", ""))}</small></span></div>'
                for index, item in enumerate(lowlevels, 1)
            ) or '<div class="wb-prompt-tree-empty">暂无 lowlevel</div>'
            scene_images = prompt.get("scene_images", [])
            scene_cards = []
            for image_index, image_item in enumerate(scene_images, 1):
                source = image_item.get("src", "")
                preview = (
                    f'<img src="{html.escape(source, quote=True)}" alt="{html.escape(image_item.get("name", "场景示意图"), quote=True)}">'
                    if source else '<span class="wb-highlevel-scene-placeholder">景</span>'
                )
                scene_cards.append(
                    f'<div class="wb-highlevel-scene-card"><div class="wb-highlevel-scene-preview">{preview}</div>'
                    f'<div><b>{html.escape(image_item.get("role", "关键步骤"))}</b>'
                    f'<small title="{html.escape(image_item.get("name", ""), quote=True)}">{html.escape(image_item.get("name", ""))}</small></div></div>'
                )
            scene_content = (
                '<div class="wb-highlevel-scenes">' + ''.join(scene_cards) + '</div>'
                if scene_cards
                else '<div class="wb-highlevel-scene-empty"><span>▧</span><small>暂无图片</small></div>'
            )
            scene_column = (
                '<div class="wb-prompt-scene-column"><div class="wb-highlevel-scene-title">场景示意图</div>'
                + scene_content + '</div>'
            )
            prompt_groups.append(
                f'<section class="wb-prompt-tree-group" data-prompt-id="{html.escape(prompt_id, quote=True)}">'
                f'<div class="wb-prompt-tree-parent-row"><button type="button" class="wb-prompt-tree-parent" onclick="toggleEndpointPromptGroup(this)" aria-expanded="true">'
                f'<span class="wb-prompt-caret">▾</span><span class="wb-prompt-parent-copy"><b>{html.escape(prompt.get("high_level", ""))}</b>'
                f'<small>{html.escape(prompt.get("high_level_en", ""))}</small></span></button></div>'
                f'<div class="wb-prompt-tree-children"><div class="wb-prompt-group-content{" has-scenes" if scene_cards else " no-scenes"}">'
                f'<div class="wb-prompt-lowlevel-column"><div class="wb-lowlevel-title">lowlevel 执行项</div><div class="wb-lowlevel-list">{lowlevel_html}</div></div>'
                f'{scene_column}</div></div></section>'
            )
        body = f'''<div class="wb-step-page wb-task-info-page"><div class="wb-task-info-head"><div><h1>任务信息</h1><p>{html.escape(str(task.get("task_no", "--")))} · {html.escape(task.get("name", "评测任务"))}</p></div></div><div class="wb-task-section"><div class="wb-prompt-tree">{"".join(prompt_groups) or '<div class="wb-prompt-tree-empty">当前任务暂无提示词</div>'}</div></div><a class="wb-primary wb-link" href="/evaluate2/setup?step=4&task={html.escape(selected_task_id, quote=True)}">开始评测</a><script>function toggleEndpointPromptGroup(button){{var group=button.closest('.wb-prompt-tree-group');var children=group.querySelector('.wb-prompt-tree-children');var expanded=button.getAttribute('aria-expanded')==='true';button.setAttribute('aria-expanded',expanded?'false':'true');children.hidden=expanded;button.querySelector('.wb-prompt-caret').textContent=expanded?'›':'▾';}}</script></div>'''
    else:
        active_task = selected_task or (active_tasks[0] if active_tasks else {})
        target = active_task.get("id", "t1")
        active_benchmark = get_benchmark(active_task.get("benchmark_id", "")) or {}
        execution_prompt_ids = active_task.get("selected_prompt_ids", []) or active_benchmark.get("prompt_ids", [])
        execution_prompt_items = [get_prompt(pid) for pid in execution_prompt_ids]
        execution_prompt_items = [item for item in execution_prompt_items if item]
        prompt_group_count = len(execution_prompt_items) or 1
        execution_prompt_options = "".join(
            f'<option value="{html.escape(item.get("id", ""), quote=True)}">{html.escape(item.get("high_level", "提示词组"))}</option>'
            for item in execution_prompt_items
        ) or '<option value="">暂无提示词组</option>'
        execution_scene_data_json = json.dumps(
            {
                item.get("id", ""): {
                    "name": item.get("high_level", "提示词组"),
                    "images": item.get("scene_images", [])[:3],
                }
                for item in execution_prompt_items
            },
            ensure_ascii=False,
        )
        body = f'''<div class="hmi-exec">
          <div class="hmi-exec-top"><a href="/evaluate2/setup?step=3" class="hmi-back">← 完成</a><div class="hmi-top-status">● <b>评测模式</b></div></div>
          <div class="hmi-camera-row"><div class="hmi-camera-card"><b>左手臂镜头</b><span>● 已连接</span><div class="hmi-camera-view">视频画面<br><small>分辨率：640×480　FPS：25</small></div></div><div class="hmi-camera-card"><b>头部镜头</b><span>● 已连接</span><div class="hmi-camera-view">视频画面<br><small>分辨率：640×480　FPS：24.3</small></div></div><div class="hmi-camera-card"><b>右手臂镜头</b><span>● 已连接</span><div class="hmi-camera-view">视频画面<br><small>分辨率：640×480　FPS：26.7</small></div></div></div>
          <div class="hmi-exec-grid"><div class="hmi-task-panel"><div class="hmi-panel-title"><select id="hmi-prompt-select">{execution_prompt_options}</select><a href="javascript:void(0)" class="hmi-scene-link" id="hmi-scene-link" onclick="hmiOpenScene()">场景示意</a><span class="hmi-progress">0 / 4 次</span></div><div class="hmi-task-row"><b>1</b><span class="hmi-prompt-text">抓住小猫</span><span class="hmi-result-summary"></span><button class="hmi-result-edit" type="button" hidden aria-label="编辑评测结果" title="编辑评测结果" onclick="hmiEditResult(this)"><span aria-hidden="true">✎</span></button><button class="hmi-icon-action" title="开始执行" aria-label="开始执行" onclick="hmiTogglePrompt(this)">▶</button></div><div class="hmi-task-row"><b>2</b><span class="hmi-prompt-text">掀开被子</span><span class="hmi-result-summary"></span><button class="hmi-result-edit" type="button" hidden aria-label="编辑评测结果" title="编辑评测结果" onclick="hmiEditResult(this)"><span aria-hidden="true">✎</span></button><button class="hmi-icon-action" title="开始执行" aria-label="开始执行" onclick="hmiTogglePrompt(this)">▶</button></div><div class="hmi-task-row"><b>3</b><span class="hmi-prompt-text">把小猫放进被子</span><span class="hmi-result-summary"></span><button class="hmi-result-edit" type="button" hidden aria-label="编辑评测结果" title="编辑评测结果" onclick="hmiEditResult(this)"><span aria-hidden="true">✎</span></button><button class="hmi-icon-action" title="开始执行" aria-label="开始执行" onclick="hmiTogglePrompt(this)">▶</button></div><div class="hmi-task-row"><b>4</b><span class="hmi-prompt-text">盖上被子</span><span class="hmi-result-summary"></span><button class="hmi-result-edit" type="button" hidden aria-label="编辑评测结果" title="编辑评测结果" onclick="hmiEditResult(this)"><span aria-hidden="true">✎</span></button><button class="hmi-icon-action" title="开始执行" aria-label="开始执行" onclick="hmiTogglePrompt(this)">▶</button></div></div><aside class="hmi-control-panel"><h3>开关</h3><div class="hmi-switches"><label>全部上电 <i>OFF</i></label><label>底座上电 <i>OFF</i></label><label>臂部上电 <i>OFF</i></label><label>左臂上电 <i>OFF</i></label><label>右臂上电 <i>OFF</i></label><label>障碍状态 <i>OFF</i></label></div><h3>连接状态</h3><p>Movax　<span>● 已连接</span></p><p>CaptureX　<span>● 已连接</span></p><p>Teleop　<span>● 已连接</span></p><div class="hmi-control-actions"><button>复位</button><button>重置</button><button disabled>停止</button></div></aside></div>
          <div class="hmi-scene-mask" id="hmi-scene-mask" hidden><div class="hmi-scene-dialog" role="dialog" aria-modal="true" aria-labelledby="hmi-scene-title"><div class="hmi-scene-dialog-head"><h3 id="hmi-scene-title">场景示意</h3><button type="button" onclick="hmiCloseScene()" aria-label="关闭">×</button></div><div class="hmi-scene-dialog-body" id="hmi-scene-body"></div></div></div>
          <div class="hmi-result-mask" id="hmi-result-mask" hidden><div class="hmi-result-dialog"><h3 id="hmi-result-title">提交评测结果</h3><section class="hmi-result-section"><h4>评测结果</h4><div class="hmi-result-radios"><label><input type="radio" name="hmi-result" value="成功">成功</label><label><input type="radio" name="hmi-result" value="失败">失败</label><label><input type="radio" name="hmi-result" value="重试1次成功">重试1次成功</label><label><input type="radio" name="hmi-result" value="重试2次成功">重试2次成功</label><label><input type="radio" name="hmi-result" value="重试3次成功">重试3次成功</label></div></section><section class="hmi-metric-section"><h4>评测指标</h4><label><span class="hmi-metric-label">任务完成度 <span class="hmi-metric-tip" tabindex="0" data-tip="任务目标完成的完整程度，按实际完成步骤评估">i</span></span><input type="number" min="0" max="100" placeholder="请输入 0-100"></label><label><span class="hmi-metric-label">执行质量 <span class="hmi-metric-tip" tabindex="0" data-tip="动作执行的准确性、稳定性和流畅度">i</span></span><select><option value="">请选择</option><option>优秀</option><option>合格</option><option>需改进</option></select></label><label><span class="hmi-metric-label">备注 <span class="hmi-metric-tip" tabindex="0" data-tip="补充记录本次评测中的异常、原因或其他说明">i</span></span><input placeholder="请输入评测备注"></label></section><div><button onclick="hmiCancelResult()">取消</button><button class="primary" onclick="hmiSubmitResult()">提交</button></div></div></div>
          <script>var hmiSceneData={execution_scene_data_json};var hmiActiveButton=null;var hmiEditing=false;function hmiSceneEscape(value){{return String(value||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}}function hmiPromptChanged(select){{var link=document.getElementById('hmi-scene-link');if(link)link.classList.toggle('is-empty',!(hmiSceneData[select.value]&&hmiSceneData[select.value].images&&hmiSceneData[select.value].images.length));}}function hmiOpenScene(){{var select=document.getElementById('hmi-prompt-select');var data=hmiSceneData[(select&&select.value)||'']||{{name:'当前提示词组',images:[]}};var body=document.getElementById('hmi-scene-body');var title=document.getElementById('hmi-scene-title');if(title)title.textContent=data.name+' · 场景示意';if(body)body.innerHTML=(data.images&&data.images.length)?data.images.map(function(image){{var preview=image.src?'<img src="'+hmiSceneEscape(image.src)+'" alt="'+hmiSceneEscape(image.name||'场景示意图')+'">':'<span class="hmi-scene-placeholder">景</span>';return '<article class="hmi-scene-card"><div class="hmi-scene-preview">'+preview+'</div><div><b>'+hmiSceneEscape(image.role||'关键步骤')+'</b><small>'+hmiSceneEscape(image.name||'场景示意图')+'</small></div></article>';}}).join(''):'<div class="hmi-scene-empty">暂无场景示意图</div>';document.getElementById('hmi-scene-mask').hidden=false;}}function hmiCloseScene(){{document.getElementById('hmi-scene-mask').hidden=true;}}function hmiResetResultFields(){{document.querySelectorAll('input[name="hmi-result"]').forEach(function(input){{input.checked=false;}});var number=document.querySelector('.hmi-metric-section input[type="number"]');if(number)number.value='';var quality=document.querySelector('.hmi-metric-section select');if(quality)quality.value='';var note=document.querySelector('.hmi-metric-section input[placeholder="请输入评测备注"]');if(note)note.value='';}}function hmiTogglePrompt(btn){{if(btn.dataset.running==='1'){{hmiActiveButton=btn;hmiEditing=false;document.getElementById('hmi-result-title').textContent='提交评测结果';document.getElementById('hmi-result-mask').hidden=false;return;}}hmiEditing=false;hmiResetResultFields();document.querySelectorAll('.hmi-task-row .hmi-icon-action').forEach(function(b){{if(b!==btn&&b.dataset.running==='1'){{b.dataset.running='0';b.textContent='▶';b.title='开始执行';b.closest('.hmi-task-row').classList.remove('running');}}}});btn.dataset.running='1';btn.textContent='■';btn.title='停止执行';btn.closest('.hmi-task-row').classList.add('running');}}function hmiEditResult(editButton){{var row=editButton.closest('.hmi-task-row');hmiActiveButton=row.querySelector('.hmi-icon-action');hmiEditing=true;var currentResult=row.dataset.result||'';document.querySelectorAll('input[name="hmi-result"]').forEach(function(input){{input.checked=input.value===currentResult;}});var number=document.querySelector('.hmi-metric-section input[type="number"]');if(number)number.value=row.dataset.completion||'';var quality=document.querySelector('.hmi-metric-section select');if(quality)quality.value=row.dataset.quality||'';var note=document.querySelector('.hmi-metric-section input[placeholder="请输入评测备注"]');if(note)note.value=row.dataset.note||'';document.getElementById('hmi-result-title').textContent='编辑评测结果';document.getElementById('hmi-result-mask').hidden=false;}}function hmiCancelResult(){{document.getElementById('hmi-result-mask').hidden=true;hmiEditing=false;}}function hmiSubmitResult(){{if(!hmiActiveButton)return;var result=document.querySelector('input[name="hmi-result"]:checked');if(!result){{alert('请选择评测结果');return;}}var row=hmiActiveButton.closest('.hmi-task-row');var summary=row.querySelector('.hmi-result-summary');var edit=row.querySelector('.hmi-result-edit');var number=document.querySelector('.hmi-metric-section input[type="number"]');var quality=document.querySelector('.hmi-metric-section select');var note=document.querySelector('input[placeholder="请输入评测备注"]');var failed=result.value==='失败';row.dataset.result=result.value;row.dataset.completion=number?number.value:'';row.dataset.quality=quality?quality.value:'';row.dataset.note=note?note.value:'';summary.textContent=result.value;summary.classList.toggle('failed',failed);summary.classList.toggle('passed',!failed);if(edit)edit.hidden=false;row.classList.toggle('result-failed',failed);row.classList.toggle('result-passed',!failed);row.classList.add('result-submitted');if(!hmiEditing){{hmiActiveButton.dataset.running='0';hmiActiveButton.style.display='none';hmiActiveButton.title='已提交';row.classList.remove('running');}}row.classList.add('completed');hmiEditing=false;document.getElementById('hmi-result-mask').hidden=true;}}</script>
        </div>'''
    body = f'<div class="eval2-ipad-shell"><div class="eval2-ipad-screen">{body}</div></div>'
    style = '<style>.wb-step-page{width:100%;min-height:100%;background:#fff;border:0;border-radius:0;padding:32px;max-width:none;margin:0;box-sizing:border-box;overflow:auto}.wb-step-page h1{font-size:26px;margin:0 0 22px}.wb-step-page h2{font-size:18px;margin:24px 0 14px}.wb-muted{color:#7e8792}.wb-link{display:flex;align-items:center;justify-content:center;text-decoration:none}.wb-pass{color:#2eaf68;font-size:13px;font-weight:400;margin-left:12px}.wb-fields{display:grid;grid-template-columns:1fr 2fr;gap:18px;margin:24px 0}.wb-fields label{display:flex;flex-direction:column;gap:8px;color:#5f6670;font-size:13px}.wb-fields select{height:40px;border:1px solid #d9dde3;border-radius:6px;padding:0 10px;background:#fff}.wb-mode-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin:28px auto;max-width:820px}.wb-mode{min-height:150px;border:1px solid #dfe3e8;background:#fff;border-radius:8px;font-size:17px;display:flex;flex-direction:column;gap:15px;align-items:center;justify-content:center;cursor:pointer;text-decoration:none;color:inherit}.wb-mode.active{border:2px solid #1F80A0;background:#e6f4f8}.wb-mode b{font-size:34px;color:#1F80A0}.wb-primary{width:100%;height:48px;border:0;border-radius:7px;background:#1F80A0;color:#fff;font-size:16px;cursor:pointer}.wb-note{text-align:center;color:#7e8792;margin-top:10px;font-size:13px}.wb-scene{display:grid;grid-template-columns:1fr;gap:18px;padding:18px;background:#fafbfc;border:1px solid #edf0f3;border-radius:8px}.wb-scene p{color:#69717c;margin:8px 0 18px}.wb-media{display:grid;grid-template-columns:1fr 1fr;gap:10px;color:#7a828d}.wb-media div{border:1px dashed #cdd3db;border-radius:6px;padding:30px;text-align:center}.wb-media span{display:block;font-size:30px;color:#1F80A0;margin-top:18px}.wb-prompts{border:1px solid #edf0f3;border-radius:7px;margin-bottom:20px}.wb-prompts div{padding:13px 16px;border-bottom:1px solid #f0f0f0}.wb-prompts b{display:inline-flex;width:22px;height:22px;border-radius:4px;background:#e6f4f8;color:#1F80A0;align-items:center;justify-content:center;margin-right:10px}.wb-prompts small{color:#8a9099;margin-left:12px}.wb-scene-description{display:flex;align-items:center;gap:14px;white-space:nowrap}.wb-scene-description span{color:#69717c;overflow:hidden;text-overflow:ellipsis}@media(max-width:560px){.wb-mode-grid{grid-template-columns:1fr}.wb-fields{grid-template-columns:1fr}.wb-scene-description{white-space:normal;align-items:flex-start;flex-direction:column;gap:4px}}</style>'
    style += '<style>.hmi-exec{height:100%;min-height:100%;overflow:auto;box-sizing:border-box;background:#f7f8fa;padding:14px}.hmi-exec-top{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #edf0f3;padding:10px 14px;margin-bottom:14px;font-size:13px}.hmi-exec-top span{color:#7e8792}.hmi-back{background:#1F80A0;color:#fff;padding:6px 12px;border-radius:5px;text-decoration:none}.hmi-top-status{margin-left:auto;color:#1F80A0}.hmi-camera-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:14px}.hmi-camera-card{background:#fff;border:1px solid #edf0f3;padding:10px;font-size:14px}.hmi-camera-card>span{float:right;color:#2eaf68;font-size:12px}.hmi-camera-view{height:260px;background:#101317;color:#75808d;margin-top:8px;display:flex;align-items:center;justify-content:center;text-align:center;line-height:2}.hmi-camera-view small{display:block}.hmi-exec-grid{display:grid;grid-template-columns:2fr 1fr;gap:14px}.hmi-task-panel,.hmi-control-panel{background:#fff;border:1px solid #edf0f3;padding:14px}.hmi-panel-title{font-weight:600;margin-bottom:12px;display:flex;justify-content:flex-start;align-items:center;flex-wrap:wrap;gap:10px}.hmi-panel-title select{border:1px solid #d9dde3;border-radius:5px;padding:5px}.hmi-task-row{padding:14px 10px;border:1px solid #edf0f3;margin-bottom:8px;display:flex;align-items:center;gap:10px}.hmi-task-row.active{border-color:#1F80A0;background:#e6f4f8}.hmi-task-row b{width:22px;height:22px;background:#edf1f7;display:inline-flex;align-items:center;justify-content:center}.hmi-task-row button{margin-left:auto;border:0;background:transparent;color:#2eaf68;font-size:18px}.hmi-control-panel h3{font-size:15px;margin:4px 0 14px}.hmi-switches{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px}.hmi-switches label{font-size:12px;display:flex;justify-content:space-between}.hmi-switches i{font-style:normal;color:#1F80A0;background:#e6f4f8;border:1px solid #b8dce8;border-radius:10px;padding:2px 8px}.hmi-control-panel p{font-size:12px;color:#69717c;margin:8px 0}.hmi-control-panel p span{color:#2eaf68}.hmi-control-actions{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:20px}.hmi-control-actions button{height:42px;border:1px solid #b8dce8;background:#fff;border-radius:5px;color:#1F80A0}.hmi-control-actions .hmi-stop-action{color:#e54863;border-color:#ff9c9c}.hmi-control-actions button:disabled{color:#aaa;background:#f0f1f3}.hmi-submit-group{width:100%;height:46px;margin-top:10px;border:0;border-radius:7px;background:#1F80A0;color:#fff;font-size:16px;cursor:pointer}@media(max-width:800px){.hmi-camera-row,.hmi-exec-grid{grid-template-columns:1fr}.hmi-camera-view{height:200px}}</style>'
    style += '<style>.hmi-task-row.running{border-color:#2463eb;background:#f3f7ff}.hmi-task-row.running button{color:#2463eb;font-weight:600}.hmi-task-row.completed{background:#f3fbf6;color:#2e8b57}.hmi-task-row button{font-size:16px}.hmi-panel-title{justify-content:flex-start;gap:10px}.hmi-panel-title select{min-width:220px}.hmi-ckpt-select{min-width:180px!important}.hmi-progress{margin-left:auto;color:#2463eb;font-size:12px}.hmi-icon-action{width:28px;height:28px;border:0;background:transparent;cursor:pointer}.hmi-result-mask[hidden]{display:none}.hmi-result-mask{position:fixed;inset:0;z-index:1200;background:rgba(0,0,0,.38);display:flex;align-items:center;justify-content:center}.hmi-result-dialog{width:560px;max-width:calc(100vw - 32px);background:#fff;border-radius:9px;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.2)}.hmi-result-dialog h3{margin:0 0 20px}.hmi-result-section,.hmi-metric-section{padding:14px 16px;border:1px solid #edf0f3;border-radius:7px;margin-bottom:14px}.hmi-result-section{background:#f6f9ff}.hmi-metric-section{background:#fafafa}.hmi-result-dialog h4{margin:0 0 12px;font-size:14px}.hmi-result-radios{display:flex;gap:18px;flex-wrap:wrap}.hmi-result-radios label{display:flex;align-items:center;gap:5px;color:#3f4752;font-size:13px}.hmi-metric-section label{display:flex;flex-direction:column;gap:7px;margin-bottom:12px;color:#5f6670;font-size:13px}.hmi-metric-label{display:flex;align-items:center;gap:6px}.hmi-metric-tip{display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;border:1px solid #a9cbd4;border-radius:50%;color:#1F80A0;font-size:10px;line-height:1;cursor:help}.hmi-result-dialog select,.hmi-result-dialog input{height:38px;border:1px solid #d9dde3;border-radius:6px;padding:0 10px;background:#fff}.hmi-result-dialog>div{display:flex;justify-content:flex-end;gap:8px;margin-top:20px}.hmi-result-dialog button{padding:8px 18px;border:1px solid #d9dde3;background:#fff;border-radius:6px}.hmi-result-dialog button.primary{background:#2463eb;border-color:#2463eb;color:#fff}</style>'
    style += '<style>.hmi-task-row{display:grid;grid-template-columns:28px minmax(0,1fr) minmax(150px,auto) 32px;align-items:center;gap:10px}.hmi-task-row.result-submitted{grid-template-columns:28px minmax(0,1fr) minmax(150px,auto)}.hmi-prompt-text{min-width:0}.hmi-result-summary{justify-self:end;text-align:right;color:#2eaf68;font-size:13px;white-space:nowrap}.hmi-result-summary.failed{color:#e54863}.hmi-result-summary.passed{color:#2eaf68}.hmi-icon-action{justify-self:end;margin-left:0!important}.hmi-task-row.result-failed{background:#fff1f0!important;border-color:#ffccc7!important}.hmi-task-row.result-passed{background:#f3fbf6!important}</style>'
    style += '<style>.hmi-result-edit{justify-self:end;margin-left:0!important;padding:0!important;border:0!important;background:transparent!important;color:#1F80A0!important;font-size:12px!important;cursor:pointer}.hmi-result-edit:hover{text-decoration:underline}.hmi-result-edit[hidden]{display:none!important}.hmi-task-row{grid-template-columns:28px minmax(0,1fr) minmax(150px,auto) 44px 32px}.hmi-task-row.result-submitted{grid-template-columns:28px minmax(0,1fr) minmax(150px,auto) 44px}</style>'
    style += '<style>.wb-scene{grid-template-columns:1fr}.wb-scene-description{display:flex;align-items:center;gap:14px;white-space:nowrap}.wb-scene-description span{color:#69717c;overflow:hidden;text-overflow:ellipsis}.hmi-panel-title{flex-wrap:nowrap;align-items:center;gap:8px;white-space:nowrap;overflow:hidden}.hmi-select-control{display:flex;align-items:center;gap:7px;min-width:0;flex:0 1 auto;padding:5px 8px;border:1px solid #d9dde3;border-radius:6px;background:#fff}.hmi-select-prefix{color:#1F80A0;font-size:12px;font-weight:600;flex-shrink:0}.hmi-select-control select{min-width:120px;max-width:260px;border:0!important;padding:4px 22px 4px 0!important;outline:0;overflow:hidden;text-overflow:ellipsis}.hmi-select-control em{color:#8a9099;font-size:11px;font-style:normal;white-space:nowrap}.hmi-progress{margin-left:auto;flex-shrink:0;padding:9px 13px;border-radius:7px;background:#e6f4f8;color:#5f6670!important;white-space:nowrap}.hmi-progress strong{color:#1F80A0;font-size:16px}.hmi-task-row button{color:#1F80A0}.hmi-switches i{color:#1F80A0!important;background:#e6f4f8!important;border:1px solid #b8dce8}.hmi-control-actions{grid-template-columns:repeat(3,1fr)!important}.hmi-control-actions button{height:42px!important;color:#1F80A0;border-color:#b8dce8!important;background:#fff!important}.hmi-control-actions .hmi-stop-action{color:#e54863;border-color:#ff9c9c!important}.hmi-submit-group{width:100%;height:46px;margin-top:10px;border:0;border-radius:7px;background:#1F80A0;color:#fff;font-size:16px;cursor:pointer}.hmi-submit-group:hover{background:#167b98}@media(max-width:800px){.hmi-select-control{flex:1;min-width:0}.hmi-progress{order:initial;width:auto;text-align:left;margin-left:auto}.wb-scene-description{white-space:normal;align-items:flex-start;flex-direction:column;gap:4px}}</style>'
    style += '<style>.wb-task-info-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:20px}.wb-task-info-head h1{margin-bottom:4px!important}.wb-task-info-head p{margin:0;color:#69717c;font-size:13px}.wb-task-info-head>span{padding:5px 10px;border-radius:12px;background:#e6f4f8;color:#1F80A0;font-size:12px;white-space:nowrap}.wb-task-section{margin-bottom:22px}.wb-task-section h2{display:flex;align-items:baseline;gap:8px;font-size:16px;margin:0 0 12px;color:#26323d}.wb-task-section h2 small{color:#8a9099;font-size:11px;font-weight:400}.wb-scene-task-only{display:grid!important;grid-template-columns:minmax(0,1fr) 300px!important;align-items:stretch}.wb-scene-task-only .wb-scene-description{align-items:flex-start;flex-direction:column;gap:6px;white-space:normal}.wb-scene-task-only .wb-scene-description span{line-height:1.7;white-space:normal}.wb-scene-video{display:flex;align-items:center;gap:12px;padding:12px 14px;border:1px solid #dce7ea;border-radius:7px;background:#fff}.wb-scene-video-icon{display:flex;align-items:center;justify-content:center;width:38px;height:38px;flex:none;border-radius:50%;background:#e6f4f8;color:#1F80A0;font-size:15px;padding-left:2px}.wb-scene-video>div{display:flex;flex-direction:column;gap:4px;min-width:0}.wb-scene-video b{color:#3f4b55;font-size:13px}.wb-scene-video small{color:#7a838c;font-size:11px;line-height:1.5}.wb-prompt-tree{border:1px solid #dfe8eb;border-radius:8px;overflow:hidden;background:#fff}.wb-prompt-tree-group{border-bottom:1px solid #dfe8eb}.wb-prompt-tree-group:last-child{border-bottom:0}.wb-prompt-tree-parent{width:100%;display:grid;grid-template-columns:18px minmax(0,1fr) auto;align-items:center;gap:9px;padding:13px 16px;border:0;background:#f7fbfc;color:#1F80A0;text-align:left;cursor:pointer}.wb-prompt-caret{font-size:16px;line-height:1}.wb-prompt-parent-copy{display:flex;flex-direction:column;gap:2px;min-width:0}.wb-prompt-parent-copy b{overflow:hidden;color:#2d5965;font-size:14px;text-overflow:ellipsis;white-space:nowrap}.wb-prompt-parent-copy small{overflow:hidden;color:#7a8b91;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.wb-prompt-parent-meta{color:#6d7b80;font-size:11px;font-weight:400;white-space:nowrap}.wb-prompt-tree-children{padding:14px 16px 16px 43px;background:#fff}.wb-prompt-group-content{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr);gap:18px;align-items:start}.wb-prompt-group-content.no-scenes{grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr)}.wb-prompt-scene-column,.wb-prompt-lowlevel-column{min-width:0}.wb-prompt-scene-column{padding-left:18px;border-left:1px solid #e3ecef}.wb-highlevel-scene-title,.wb-lowlevel-title{display:flex;align-items:baseline;gap:7px;margin-bottom:9px;color:#43525a;font-size:12px;font-weight:600}.wb-highlevel-scene-title small{color:#8a969b;font-size:10px;font-weight:400}.wb-highlevel-scenes{display:grid;grid-template-columns:minmax(0,1fr);gap:10px;margin-bottom:0}.wb-highlevel-scene-card{display:grid;grid-template-columns:80px minmax(0,1fr);gap:9px;min-width:0;padding:6px;border:1px solid #e1e8eb;border-radius:7px;background:#fafcfc}.wb-highlevel-scene-preview{position:relative;height:62px;overflow:hidden;border-radius:5px;background:linear-gradient(145deg,#d9ecef,#f3f9fa)}.wb-highlevel-scene-preview img{width:100%;height:100%;display:block;object-fit:cover}.wb-highlevel-scene-preview i{position:absolute;left:5px;top:5px;padding:1px 5px;border-radius:8px;background:#1F80A0;color:#fff;font-size:9px;font-style:normal}.wb-highlevel-scene-placeholder{display:flex;width:100%;height:100%;align-items:center;justify-content:center;color:#1F80A0;font-size:22px}.wb-highlevel-scene-card>div:last-child{display:flex;flex-direction:column;justify-content:center;gap:5px;min-width:0}.wb-highlevel-scene-card b{color:#40515a;font-size:11px}.wb-highlevel-scene-card small{overflow:hidden;color:#7a868c;font-size:10px;text-overflow:ellipsis;white-space:nowrap}.wb-highlevel-scene-empty{display:flex;min-height:72px;margin:0;align-items:center;justify-content:center;gap:8px;border:1px dashed #d5e0e3;border-radius:7px;color:#8a9499;background:#fafbfc}.wb-highlevel-scene-empty span{color:#9aabb0;font-size:20px}.wb-highlevel-scene-empty small{font-size:11px}.wb-lowlevel-list{border-left:1px solid #d9edf1;margin-left:10px}.wb-prompt-tree-child{display:grid;grid-template-columns:24px minmax(0,1fr);align-items:start;gap:7px;position:relative;padding:7px 0 7px 14px;color:#4f5964;font-size:12px}.wb-prompt-tree-child:before{content:"";position:absolute;left:0;top:17px;width:10px;height:1px;background:#d9edf1}.wb-prompt-tree-child>span:last-child{display:flex;flex-direction:column;gap:2px}.wb-prompt-tree-child small{display:block;margin:0;color:#8b969c;font-size:10px}.wb-lowlevel-index{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:4px;background:#edf5f6;color:#1F80A0;font-size:10px}.wb-prompt-tree-empty{padding:22px;color:#8a9499;text-align:center;font-size:12px}@media(max-width:760px){.wb-scene-task-only{grid-template-columns:1fr!important}.wb-prompt-tree-parent{grid-template-columns:18px minmax(0,1fr)}.wb-prompt-parent-meta{grid-column:2}.wb-prompt-tree-children{padding-left:24px}.wb-prompt-group-content,.wb-prompt-group-content.no-scenes{grid-template-columns:1fr}.wb-prompt-scene-column{padding-left:0;border-left:0}.wb-highlevel-scenes{grid-template-columns:1fr}}</style>'
    style += f'''<script>
      document.addEventListener('DOMContentLoaded', function() {{
        var title = document.querySelector('.hmi-panel-title');
        if (!title) return;
        var selects = title.querySelectorAll('select');
        if (selects.length >= 1) {{
          var promptOptions = selects[0].innerHTML;
          title.innerHTML = '<div class="hmi-select-control"><span class="hmi-select-prefix">Prompt</span><select id="hmi-prompt-select" aria-label="Prompt" onchange="hmiPromptChanged(this)">' + promptOptions + '</select><em>共 {prompt_group_count} 项</em></div>'
            + '<a href="javascript:void(0)" class="hmi-scene-link" id="hmi-scene-link" onclick="hmiOpenScene()">场景示意</a>'
            + '<span class="hmi-progress">执行进度：已提交任务数 / 全部任务数&nbsp;&nbsp;<strong>20/30</strong></span>';
          hmiPromptChanged(document.getElementById('hmi-prompt-select'));
        }}
        var actions = document.querySelector('.hmi-control-actions');
        if (actions) {{
          actions.innerHTML = '<button type="button">复位</button><button type="button">重置</button><button type="button" class="hmi-stop-action">停止</button>';
          var submit = document.createElement('button');
          submit.type = 'button'; submit.className = 'hmi-submit-group'; submit.textContent = '提交本组数据'; submit.onclick = function() {{ if (window.showToast) window.showToast('本组数据已提交', 'success'); }};
          actions.parentNode.insertBefore(submit, actions.nextSibling);
        }}
        document.querySelectorAll('.hmi-result-edit span[aria-hidden="true"]').forEach(function(icon) {{
          icon.innerHTML = '<svg class="hmi-edit-glyph" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 16.5 3 21l4.5-1L19 8.5 15.5 5 4 16.5Z"></path><path d="m14 6.5 3.5 3.5"></path></svg>';
        }});
      }});
    </script>'''
    style += '<style>.hmi-edit-glyph{display:block;width:15px;height:15px}.hmi-result-edit:hover{color:#166f88!important;text-decoration:none}</style>'
    style += '<style>.hmi-scene-link{flex:0 0 auto;color:#1F80A0;font-size:12px;text-decoration:none;white-space:nowrap}.hmi-scene-link:hover{text-decoration:underline}.hmi-scene-link.is-empty{color:#9aa3aa}.hmi-scene-mask[hidden]{display:none}.hmi-scene-mask{position:fixed;inset:0;z-index:1250;background:rgba(0,0,0,.38);display:flex;align-items:center;justify-content:center;padding:20px}.hmi-scene-dialog{width:720px;max-width:calc(100vw - 32px);max-height:calc(100vh - 40px);overflow:auto;background:#fff;border-radius:9px;box-shadow:0 12px 40px rgba(0,0,0,.2)}.hmi-scene-dialog-head{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;border-bottom:1px solid #edf0f3}.hmi-scene-dialog-head h3{margin:0;font-size:17px;color:#26323d}.hmi-scene-dialog-head button{border:0;background:transparent;color:#7f8993;font-size:24px;line-height:1;cursor:pointer}.hmi-scene-dialog-body{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;padding:20px}.hmi-scene-card{overflow:hidden;border:1px solid #e2eaec;border-radius:8px;background:#fff}.hmi-scene-preview{height:150px;background:linear-gradient(145deg,#d9ecef,#f4fafb);display:flex;align-items:center;justify-content:center}.hmi-scene-preview img{width:100%;height:100%;object-fit:cover;display:block}.hmi-scene-placeholder{color:#1F80A0;font-size:36px}.hmi-scene-card>div:last-child{display:flex;flex-direction:column;gap:5px;padding:10px 12px}.hmi-scene-card b{color:#40515a;font-size:12px}.hmi-scene-card small{overflow:hidden;color:#7a868c;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.hmi-scene-empty{grid-column:1/-1;padding:42px 12px;color:#8a9499;text-align:center}@media(max-width:680px){.hmi-scene-dialog-body{grid-template-columns:1fr 1fr}}@media(max-width:460px){.hmi-scene-dialog-body{grid-template-columns:1fr}}</style>'
    style += '<style>.wb-prompt-tree-parent-row{display:flex;align-items:stretch;background:#f7fbfc;border-bottom:1px solid #dfe8eb}.wb-prompt-tree-parent-row .wb-prompt-tree-parent{flex:1;width:auto}.wb-prompt-group-content.has-scenes{grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr)}.wb-prompt-group-content.no-scenes{grid-template-columns:minmax(0,1fr)}@media(max-width:760px){.wb-prompt-group-content.has-scenes{grid-template-columns:1fr}}</style>'
    style += ENDPOINT_MODE_STYLE + ENDPOINT_SETUP_MODE_SCRIPT
    return render_page("端侧示意", body + style, active="evaluate2")


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
        content = '<div class="eval2-ipad-shell"><div class="eval2-ipad-screen"><div style="text-align:center;padding:60px;color:rgba(0,0,0,0.25);">\u6682\u65e0\u8bc4\u6d4b\u6b65\u9aa4</div></div></div>'
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

    <div id="eval2-result-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:1000;align-items:center;justify-content:center;"><div style="background:#fff;width:560px;max-width:calc(100vw - 32px);border-radius:10px;padding:24px;"><h3 style="margin:0 0 18px;">填写评测结果</h3><div class="form-group"><label>评测结果</label><select id="eval2-result"><option>成功</option><option>失败</option><option>重试1次成功</option><option>重试2次成功</option><option>重试3次成功</option></select></div><div class="form-group"><label>评测指标</label><input class="ant-input" placeholder="填写本条评测指标"></div><div style="display:flex;justify-content:flex-end;gap:8px;margin-top:22px;"><button type="button" class="ant-btn" onclick="eval2CloseResult()">取消</button><button type="button" class="ant-btn ant-btn-primary" onclick="eval2ConfirmResult()">提交并进入下一条</button></div></div></div>
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
      document.getElementById('eval2-result-modal').style.display='flex';
    }}
    function eval2CloseResult() {{ document.getElementById('eval2-result-modal').style.display='none'; }}
    function eval2ConfirmResult() {{ window.location.href = '{next_url}'; }}
    var v2Pref = null;
    function v2SetPref(val, btn) {{
      v2Pref = val;
      document.querySelectorAll('.pref-opt').forEach(function(b) {{ b.classList.remove('pref-active'); }});
      btn.classList.add('pref-active');
    }}
    </script>
    '''
    content = f'<div class="eval2-ipad-shell"><div class="eval2-ipad-screen">{content}</div></div>'
    return render_page("\u7aef\u4fa7\u793a\u610f", content, active="evaluate2")


# ── Evaluation Records (task-view + checkpoint-view) ──
def _mock_eval_records():
    """Build the flat evaluation-record list used by the result list and detail view."""
    records = []
    import random as _rnd_records
    for task in EVAL_TASKS:
        benchmark = get_benchmark(task.get("benchmark_id", ""))
        if not benchmark:
            continue
        checkpoint_id = task.get("model_ids", [""])[0] if task.get("model_ids") else ""
        checkpoint_name = get_model_name(checkpoint_id) if checkpoint_id else "--"
        prompt_ids = task.get("selected_prompt_ids", []) or benchmark.get("prompt_ids", []) or [PROMPTS[0]["id"]]
        selected_lowlevel_ids = set(task.get("selected_lowlevel_ids", []))
        criterion = get_criterion(task.get("criteria_id", "")) or {}
        result_definitions = normalize_result_definitions(criterion.get("result_definitions", {}))
        result_types = [item["type"] for item in result_definitions] or ["成功", "失败"]
        failure_values = [value for value in result_types if result_type_is_failure(value)]
        success_values = [value for value in result_types if not result_type_is_failure(value)]
        if not success_values:
            success_values = result_types
        if not failure_values:
            failure_values = result_types
        row_index = 0
        _rnd_records.seed(sum(ord(ch) for ch in task.get("id", "")))
        for prompt_id in prompt_ids:
            prompt = get_prompt(prompt_id)
            if not prompt:
                continue
            for step_index, low_level in enumerate(prompt.get("low_levels", [])):
                if selected_lowlevel_ids and low_level.get("id") not in selected_lowlevel_ids:
                    continue
                row_index += 1
                record_id = f'{task.get("task_no", task.get("id", "record"))}-{row_index:03d}'
                # Recording IDs follow the data-platform convention: six-digit integers.
                recording_id = f'{600000 + len(records) + 1:06d}'
                is_success = _rnd_records.random() >= 0.22
                result = _rnd_records.choice(success_values if is_success else failure_values)
                result_parent = "失败" if result_type_is_failure(result) else "成功"
                completion = _rnd_records.randint(58, 98)
                quality = "优秀" if completion >= 88 else "合格" if completion >= 72 else "需改进"
                serial = f'MOZ1-{task.get("task_no", "0000")}-{row_index:02d}'
                operated_at = f'{task.get("created_at", "2026-06-17")} {10 + (row_index % 8):02d}:{(row_index * 7) % 60:02d}'
                records.append({
                    "id": record_id,
                    "recording_id": recording_id,
                    "group": f"1:2:{row_index + 3}",
                    "task_id": task.get("id", ""),
                    "task_no": str(task.get("task_no", "")),
                    "task_name": task.get("name", ""),
                    "prompt": prompt.get("high_level", ""),
                    "prompt_en": prompt.get("high_level_en", ""),
                    "instruction": low_level.get("zh", ""),
                    "instruction_en": low_level.get("en", ""),
                    "lowlevel_id": low_level.get("id", ""),
                    "prompt_id": prompt_id,
                    "labels": list(low_level.get("labels", [])),
                    "serial": serial,
                    "checkpoint_id": checkpoint_id,
                    "checkpoint": checkpoint_name,
                    "benchmark_id": benchmark.get("id", ""),
                    "benchmark": benchmark.get("name", ""),
                    "conclusion": result,
                    "conclusion_parent": result_parent,
                    "metrics": {"任务完成度": f"{completion}%", "执行质量": quality},
                    "operator": task.get("created_by", "Joanna Qiao"),
                    "operated_at": operated_at,
                    "videos": [
                        {"label": "头部相机", "url": "/static/eval-head.mp4"},
                        {"label": "左臂相机", "url": "/static/eval-left.mp4"},
                        {"label": "右臂相机", "url": "/static/eval-right.mp4"},
                    ],
                })
    return records


def _eval_record_video_html(record, compact=False):
    parts = []
    for index, video in enumerate(record.get("videos", [])):
        label = html.escape(video.get("label", f"视频 {index + 1}"))
        if compact:
            parts.append(
                f'<div class="vid-thumb er-record-video er-record-video-compact" aria-label="{label}"></div>'
            )
            continue
        parts.append(
            f'<div class="lab-vid er-record-video" aria-label="{label}">'
            f'<span class="vid-label">{label}</span><span class="vid-expand" aria-hidden="true">⛶</span>▶</div>'
        )
    if compact:
        prompt = html.escape(record.get("instruction_en") or record.get("prompt_en") or record.get("instruction") or "--")
        return '<div class="er-record-video-strip er-record-video-strip-compact"><div class="er-record-video-prompt">' + prompt + '</div>' + "".join(parts) + '</div>'
    return '<div class="er-record-video-strip">' + "".join(parts) + '</div>'


def _eval_record_conclusion_html(value):
    success_values = {"成功", "直接成功", "重试后成功", "重试1次成功", "重试2次成功"}
    failure_values = {"失败", "执行超时", "动作失败", "环境异常"}
    if value in success_values:
        return f'<span class="er-result-pill er-result-pass">{html.escape(value)}</span>'
    if value in failure_values:
        return f'<span class="er-result-pill er-result-fail">{html.escape(value)}</span>'
    return f'<span class="er-result-pill">{html.escape(value or "--")}</span>'


def _moztrace_chart_svg(title, series, x_label, y_label, height=260):
    """Small inline chart used for Moztrace views when Plotly is unavailable."""
    all_values = [value for _, values, _ in series for value in values]
    if not all_values:
        all_values = [0, 1]
    min_value = min(all_values)
    max_value = max(all_values)
    span = max(max_value - min_value, 1e-6)
    left, top, width, chart_height = 58, 30, 790, height - 66
    grid = ''.join(
        f'<line x1="{left}" y1="{top + (chart_height * index / 4):.1f}" x2="{left + width}" y2="{top + (chart_height * index / 4):.1f}" stroke="#e7eeee" stroke-width="1" />'
        for index in range(5)
    )
    paths = []
    for name, values, color in series:
        if not values:
            continue
        points = []
        for index, value in enumerate(values):
            x = left + (width * index / max(len(values) - 1, 1))
            y = top + chart_height - ((value - min_value) / span * chart_height)
            points.append(f'{x:.1f},{y:.1f}')
        paths.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />'
        )
    legend = ''.join(
        f'<span><i style="background:{color}"></i>{html.escape(name)}</span>'
        for name, _, color in series
    )
    return (
        f'<div class="moztrace-chart-wrap"><div class="moztrace-chart-title">{html.escape(title)}</div>'
        f'<svg class="moztrace-chart" viewBox="0 0 900 {height}" role="img" aria-label="{html.escape(title)}">'
        f'{grid}<line x1="{left}" y1="{top + chart_height}" x2="{left + width}" y2="{top + chart_height}" stroke="#9bb7b7" />'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" stroke="#9bb7b7" />'
        f'{"".join(paths)}<line class="moztrace-frame-line" x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" stroke="#1F80A0" stroke-width="2" stroke-dasharray="4 3" />'
        f'<text x="18" y="{top + chart_height / 2}" class="moztrace-chart-axis" transform="rotate(-90 18 {top + chart_height / 2})">{html.escape(y_label)}</text>'
        f'<text x="{left + width / 2}" y="{height - 8}" class="moztrace-chart-axis">{html.escape(x_label)}</text></svg>'
        f'<div class="moztrace-chart-legend">{legend}</div></div>'
    )


def _render_moztrace_detail(record):
    """Render a self-contained Moztrace session view for an evaluation record."""
    recording_id = str(record.get("recording_id") or "1")
    digits = ''.join(ch for ch in recording_id if ch.isdigit())
    numeric_id = int(digits or "1")
    session_suffix = f"{numeric_id % 100:02d}"
    operated_at = record.get("operated_at", "2026-05-28 13:41")
    try:
        start_dt = datetime.strptime(operated_at, "%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        start_dt = datetime(2026, 5, 28, 13, 41)
    start_time = start_dt.replace(second=46).strftime("%Y-%m-%d %H:%M:%S")
    end_time = (start_dt.replace(second=46) + timedelta(seconds=81)).strftime("%Y-%m-%d %H:%M:%S")
    action_chunks = 72 + numeric_id % 9
    action_steps = 1734 + numeric_id % 37
    task_name = record.get("instruction") or record.get("prompt") or "Sort the tablets and place them into the tray"
    task_name_en = record.get("instruction_en") or "Sort the tablets and place them into the tray"
    session_name = f"moztrace_20260528_1341{session_suffix}"
    task_rows = ''.join(
        f'<tr><td>{index}</td><td>{html.escape(name)}</td><td>{idle}</td><td>{timestamp}</td><td><span class="moztrace-result">{result}</span></td></tr>'
        for index, (name, idle, timestamp, result) in enumerate([
            (task_name_en, 0, "1779946969.1400146", "-"),
            (task_name_en, 1, "1779946983.7258635", "-"),
        ], 1)
    )
    info_rows = ''.join([
        f'<tr><th>Session Name</th><td>{html.escape(session_name)}</td><th>Platform</th><td>thor</td></tr>',
        f'<tr><th>Start Time</th><td>{html.escape(start_time)}</td><th>End Time</th><td>{html.escape(end_time)}</td></tr>',
        '<tr><th>Duration</th><td>1.34 minutes</td><th>Random Seed</th><td>42</td></tr>',
    ])
    stat_cells = ''.join([
        f'<div><b>Tasks (non-idle)</b><span>1</span></div>',
        f'<div><b>Action Chunks</b><span>{action_chunks}</span></div>',
        f'<div><b>Action Steps</b><span>{action_steps}</span></div>',
        f'<div><b>Avg Chunks/Task</b><span>{action_chunks}</span></div>',
        f'<div><b>Avg Steps/Task</b><span>{action_steps}</span></div>',
    ])
    schema_rows = ''.join([
        '<tr><td>observation.images.head</td><td>image</td><td>[480, 640, 3]</td><td>头部相机图像</td></tr>',
        '<tr><td>observation.state</td><td>float32</td><td>[32]</td><td>机器人关节状态</td></tr>',
        '<tr><td>action</td><td>float32</td><td>[16]</td><td>策略输出动作</td></tr>',
        '<tr><td>timestamp</td><td>float64</td><td>1</td><td>采样时间戳</td></tr>',
    ])
    action_rows = ''.join([
        '<tr><td>1</td><td>0.000 - 0.420 s</td><td>24</td><td>抓取目标</td><td><span class="moztrace-ok">完成</span></td></tr>',
        '<tr><td>2</td><td>0.421 - 0.870 s</td><td>26</td><td>移动到托盘</td><td><span class="moztrace-ok">完成</span></td></tr>',
        '<tr><td>3</td><td>0.871 - 1.340 s</td><td>22</td><td>释放物体</td><td><span class="moztrace-ok">完成</span></td></tr>',
    ])
    timeline_rows = ''.join([
        '<div><span class="moztrace-time">00:00.000</span><i></i><p><b>Session started</b><small>开始采集 observation stream</small></p></div>',
        '<div><span class="moztrace-time">00:00.420</span><i></i><p><b>Action chunk #1</b><small>策略输出第一段动作</small></p></div>',
        '<div><span class="moztrace-time">00:00.870</span><i></i><p><b>Action chunk #2</b><small>机器人移动至目标位置</small></p></div>',
        '<div><span class="moztrace-time">00:01.340</span><i></i><p><b>Session finished</b><small>任务执行完成</small></p></div>',
    ])
    latency_rows = ''.join([
        '<tr><td>Observation capture</td><td>12.4 ms</td><td><span class="moztrace-bar"><i style="width:32%"></i></span></td></tr>',
        '<tr><td>Policy inference</td><td>28.7 ms</td><td><span class="moztrace-bar"><i style="width:74%"></i></span></td></tr>',
        '<tr><td>Action dispatch</td><td>8.6 ms</td><td><span class="moztrace-bar"><i style="width:22%"></i></span></td></tr>',
        '<tr><td>End-to-end</td><td>49.7 ms</td><td><span class="moztrace-bar"><i style="width:100%"></i></span></td></tr>',
    ])
    chart_colors = ["#1F80A0", "#4f9d87", "#c18b42", "#a75d67", "#7569a8", "#6d8290"]
    action_chunk_series = [
        (f"Dim {index}", [0.3 - index * 0.28 + math.sin(step / 8 + index) * 0.03 - step * (index % 3) * 0.004 for step in range(60)], chart_colors[index % len(chart_colors)])
        for index in range(6)
    ]
    action_analysis_series = [
        (f"Dim {index}", [0.35 - index * 0.2 + math.sin(step / 7 + index) * 0.025 - step * (index % 4) * 0.005 for step in range(60)], chart_colors[index % len(chart_colors)])
        for index in range(17)
    ]
    timeline_series = [
        (f"Dim {index}", [0.34 - index * 0.3 + math.sin(step / 13 + index) * 0.012 - step * (index % 2) * 0.0007 for step in range(80)], chart_colors[index % len(chart_colors)])
        for index in range(3)
    ]
    latency_series = [
        ("Inference Latency (ms)", [90 + math.sin(index / 4) * 4 + (index % 11 == 0) * 11 for index in range(72)], "#1F80A0"),
        ("Inference Interval (ms)", [202 + math.sin(index / 5) * 0.8 + (index % 13 == 0) * 1.3 for index in range(72)], "#6b9f75"),
    ]
    action_chunk_chart = _moztrace_chart_svg("Action Chunk (60 steps x 20 dims)", action_chunk_series, "Step", "Value", 160)
    action_analysis_chart = _moztrace_chart_svg("Chunk 1_0 - Action Chunk (60 steps x 20 dims)", action_analysis_series, "Step", "Value", 180)
    timeline_chart = _moztrace_chart_svg("Action Steps Timeline (1734 steps)", timeline_series, "Step", "Value", 180)
    latency_chart = _moztrace_chart_svg("推理延迟与间隔时间序列", latency_series, "Chunk Index", "Inference Latency (ms)", 180)
    chunk_options = ''.join(
        f'<option value="1_{index}">1_{index} (task_id=1, seq={index})</option>'
        for index in range(72)
    )
    dim_options = ''.join(
        f'<option value="{index}"{ " selected" if index < 6 else ""}>Dim {index}</option>'
        for index in range(20)
    )
    latency_cards = ''.join([
        '<div><span>平均延迟</span><b>90.99 ms</b></div>',
        '<div><span>P50 延迟</span><b>89.89 ms</b></div>',
        '<div><span>P95 延迟</span><b>103.25 ms</b></div>',
        '<div><span>P99 延迟</span><b>104.33 ms</b></div>',
        '<div><span>最小延迟</span><b>84.43 ms</b></div>',
        '<div><span>最大延迟</span><b>104.33 ms</b></div>',
        '<div><span>平均推理间隔</span><b>202.03 ms</b></div>',
        '<div><span>推理间隔范围</span><b>201.5 - 203.2 ms</b></div>',
    ])
    return f'''
      <div class="moztrace-shell">
        <div class="moztrace-tabs" role="tablist">
          <button class="moztrace-tab active" type="button" onclick="switchMoztracePane('overview', this)">Overview</button>
          <button class="moztrace-tab" type="button" onclick="switchMoztracePane('obs-player', this)">Obs Player</button>
          <button class="moztrace-tab" type="button" onclick="switchMoztracePane('action-analysis', this)">Action Analysis</button>
          <button class="moztrace-tab" type="button" onclick="switchMoztracePane('timeline', this)">Timeline</button>
          <button class="moztrace-tab" type="button" onclick="switchMoztracePane('latency', this)">Latency</button>
          <button class="moztrace-tab" type="button" onclick="switchMoztracePane('schema', this)">Schema</button>
        </div>
        <section id="moztrace-pane-overview" class="moztrace-subpane">
          <div class="moztrace-section"><div class="moztrace-section-title">Session 信息</div><table class="moztrace-info-table"><tbody>{info_rows}</tbody></table></div>
          <div class="moztrace-section"><div class="moztrace-section-title">数据统计</div><div class="moztrace-stat-row">{stat_cells}</div></div>
          <div class="moztrace-section"><div class="moztrace-section-title">Tasks 列表</div><div class="moztrace-table-wrap"><table class="moztrace-table"><thead><tr><th>Task ID</th><th>Task</th><th>Is Idle</th><th>Timestamp</th><th>Result</th></tr></thead><tbody>{task_rows}</tbody></table></div></div>
        </section>
        <section id="moztrace-pane-schema" class="moztrace-subpane" style="display:none"><div class="moztrace-schema-diagram"><div class="moztrace-schema-table"><b>task_dump</b><span>task_id (INTEGER, PK)</span><span>task (TEXT)</span><span>is_idle (INTEGER)</span><span>timestamp (REAL)</span><span>result (TEXT)</span></div><div class="moztrace-schema-relation">1&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;N</div><div class="moztrace-schema-table moztrace-schema-table-wide"><b>action_chunk_dump</b><span>chunk_id (TEXT, PK)</span><span>task_id (INTEGER)</span><span>chunk_seq (INTEGER)</span><span>obs_timestamp (REAL)</span><span>inference_start_ts (REAL)</span><span>inference_end_ts (REAL)</span><span>robot_state (BLOB)</span><span>image_high (TEXT)</span><span>image_left_wrist (TEXT)</span><span>image_right_wrist (TEXT)</span><span>action_chunk (BLOB)</span><span>remaining_actions (BLOB)</span><span>noise (BLOB)</span><span>prefix_attention_start (INTEGER)</span><span>prefix_attention_end (INTEGER)</span><span>exec_actions (BLOB)</span><span>time_table (BLOB)</span></div><div class="moztrace-schema-relation">1&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;N</div><div class="moztrace-schema-table"><b>action_step_dump</b><span>step_id (TEXT, PK)</span><span>task_id (INTEGER)</span><span>chunk_id (TEXT)</span><span>action_idx (INTEGER)</span><span>dispatch_ts (REAL)</span><span>obs_timestamp (REAL)</span><span>action (BLOB)</span></div></div></section>
        <section id="moztrace-pane-obs-player" class="moztrace-subpane" style="display:none"><div class="moztrace-player-toolbar"><button type="button">|◀</button><button type="button">▶ Play</button><button type="button">▶|</button><select aria-label="播放速度"><option>0.25x</option><option>0.5x</option><option selected>1x</option><option>2x</option><option>4x</option></select><span>Chunk: 1/72&nbsp;&nbsp; Time: 0.000s&nbsp;|&nbsp;Infer: 103.8 ms</span></div><div class="moztrace-camera-grid"><div><div class="moztrace-camera-frame camera-left"><span>cam_left_wrist</span></div><small>cam_left_wrist</small></div><div><div class="moztrace-camera-frame camera-high"><span>cam_high</span></div><small>cam_high</small></div><div><div class="moztrace-camera-frame camera-right"><span>cam_right_wrist</span></div><small>cam_right_wrist</small></div></div><div class="moztrace-chart-panel">{action_chunk_chart}<div class="moztrace-segmented"><button class="active" type="button">Action Chunk</button><button type="button">Action Step</button><button type="button">维度: 6 selected⌄</button></div></div></section>
        <section id="moztrace-pane-action-analysis" class="moztrace-subpane" style="display:none"><div class="moztrace-analysis-toolbar"><label>选择 Chunk:<select aria-label="选择 Chunk">{chunk_options}</select></label></div>{action_analysis_chart}</section>
        <section id="moztrace-pane-timeline" class="moztrace-subpane" style="display:none"><div class="moztrace-timeline-toolbar"><label>Task:<select aria-label="Task"><option>All Tasks</option><option>Task 1: Sort the tablets and place them into the tray</option></select></label><label>维度:<select multiple size="4" aria-label="维度">{dim_options}</select></label><button type="button">全选</button><button type="button">清空</button><label class="moztrace-checkbox"><input type="checkbox"> 显示数据点</label></div>{timeline_chart}</section>
        <section id="moztrace-pane-latency" class="moztrace-subpane" style="display:none">{latency_chart}<div class="moztrace-latency-cards">{latency_cards}</div></section>
      </div>
    '''


def _render_eval_records_replacement(task_id=None):
    records = _mock_eval_records()
    task = next((item for item in EVAL_TASKS if item["id"] == task_id), None) if task_id else None
    if task_id:
        records = [record for record in records if record.get("task_id") == task_id]
    record_json = json.dumps({r["id"]: r for r in records}, ensure_ascii=False)
    benchmark_opts = ''.join(
        f'<option value="{html.escape(b["id"], quote=True)}">{html.escape(b["name"])}</option>'
        for b in BENCHMARKS
    )
    conclusion_opts = ''.join(
        f'<label class="er-opt"><input type="checkbox" value="{html.escape(value, quote=True)}" data-name="{html.escape(value)}" onchange="mselSync(\'er-filter-conclusion\')"> <span>{html.escape(value)}</span></label>'
        for value in sorted({str(record.get("conclusion", "")) for record in records if record.get("conclusion")})
    )
    rows = []
    for record in records:
        rid = html.escape(record["id"], quote=True)
        rows.append(
            f'<tr data-record-id="{rid}" data-task-id="{html.escape(record["task_no"], quote=True)}" '
            f'data-task-name="{html.escape(record["task_name"], quote=True)}" '
            f'data-data-id="{html.escape(record["recording_id"], quote=True)}" '
            f'data-benchmark-id="{html.escape(record["benchmark_id"], quote=True)}" '
            f'data-checkpoint-id="{html.escape(record["checkpoint_id"], quote=True)}" '
            f'data-highlevel="{html.escape(record.get("prompt", ""), quote=True)}" '
            f'data-lowlevel="{html.escape(record.get("instruction", ""), quote=True)}" '
            f'data-lowlevel-id="{html.escape(record.get("lowlevel_id", ""), quote=True)}" '
            f'data-conclusion="{html.escape(record.get("conclusion", ""), quote=True)}">'
            f'<td class="er-record-group">{html.escape(record["group"])}</td>'
            f'<td class="er-record-id">{html.escape(record["recording_id"])}</td>'
            f'<td>{_eval_record_video_html(record, compact=True)}</td>'
            f'<td class="er-record-serial">{html.escape(record["serial"])}</td>'
            f'<td>{html.escape(record["checkpoint"])}</td>'
            f'<td><div class="er-record-conclusion">{_eval_record_conclusion_html(record["conclusion"])}<span class="er-metric-info" tabindex="0" aria-label="评测指标" data-tip="任务完成度：{html.escape(record["metrics"]["任务完成度"])}；执行质量：{html.escape(record["metrics"]["执行质量"])}">i</span></div></td>'
            f'<td>{html.escape(record["operator"])}</td>'
            f'<td class="er-record-time">{html.escape(record["operated_at"])}</td>'
            f'<td class="actions-cell"><a href="/eval-records/{rid}" class="action-link">详情</a></td>'
            '</tr>'
        )
    row_html = ''.join(rows) or '<tr><td colspan="9" class="er-empty">暂无数据</td></tr>'
    task_context = (
        f'<div class="er-task-context"><a href="/tasks">← 返回评测任务</a><div><b class="er-task-context-id">{html.escape(task.get("task_no", "") and str(task.get("task_no")) or "--")}</b></div><div class="er-task-context-name"><b title="{html.escape(task.get("name", "--"), quote=True)}">{html.escape(task.get("name", "--"))}</b></div><button class="ant-btn er-export-button" type="button" onclick="exportEvalRecords()">导出</button></div>'
        if task else '<div class="er-page-head"><h1>评测数据</h1><button class="ant-btn" type="button" onclick="exportEvalRecords()">导出</button></div>'
    )
    content = f'''
    <div class="er-replacement">
      {task_context}
      <div class="filter-bar er-result-filter-bar">
        <div class="ff"><label>数据 ID</label><input id="er-filter-data-id" type="text" placeholder="请输入数据 ID"></div>
        <div class="ff"><label>highlevel</label><input id="er-filter-highlevel" type="text" placeholder="请输入 highlevel"></div>
        <div class="ff"><label>lowlevel</label><input id="er-filter-lowlevel" type="text" placeholder="请输入 lowlevel"></div>
        <div class="ff"><label>lowlevel_id</label><input id="er-filter-lowlevel-id" type="text" placeholder="请输入 lowlevel_id"></div>
        <div class="ff er-conclusion-filter"><label>评测结果（多选）</label><div class="er-dd-trigger" id="er-filter-conclusion-btn" onclick="mselToggle('er-filter-conclusion', event)" aria-label="评测结果（多选）"><div id="er-filter-conclusion-chips" class="er-chips"></div><span aria-hidden="true" style="color:rgba(0,0,0,.35);font-size:11px;margin-left:6px;">▼</span></div><div class="er-dd-panel" id="er-filter-conclusion-panel" style="width:100%;max-height:220px;overflow:auto;">{conclusion_opts}<div style="display:flex;justify-content:flex-end;gap:12px;padding:8px 14px;border-top:1px solid #f0f0f0;"><a href="javascript:;" onclick="mselToggleAll('er-filter-conclusion', true)" style="font-size:12px;color:#1F80A0;">全选</a><a href="javascript:;" onclick="mselToggleAll('er-filter-conclusion', false)" style="font-size:12px;color:rgba(0,0,0,.45);">清空</a></div></div><input type="hidden" id="er-filter-conclusion-hidden" value=""></div>
        <div class="filter-actions"><button type="button" class="ant-btn" onclick="erResultClear()">清空</button><button type="button" class="ant-btn ant-btn-primary" onclick="erResultApply()">搜索</button></div>
      </div>
      <div class="er-result-summary">共 <b id="er-result-count">{len(records)}</b> 条评测记录</div>
      <div class="ant-card ant-card-bordered er-result-card">
        <div class="er-result-table-wrap"><table class="ant-table er-result-table" id="er-result-table">
          <thead><tr><th style="width:90px;">分组</th><th style="width:120px;">数据 ID</th><th style="width:520px;">视频</th><th style="width:130px;">设备序列号</th><th style="width:130px;">checkpoint</th><th style="width:140px;">评测结果</th><th style="width:100px;">操作人</th><th style="width:145px;">操作时间</th><th style="width:60px;">操作</th></tr></thead>
          <tbody>{row_html}</tbody>
        </table></div>
        <div class="er-result-pagination"><span id="er-result-page-copy">1 / 12</span><button type="button" id="er-result-prev" onclick="erResultPageChange(-1)" aria-label="上一页">‹</button><button type="button" id="er-result-current" class="active">1</button><button type="button" id="er-result-next" onclick="erResultPageChange(1)" aria-label="下一页">›</button></div>
      </div>
    </div>
    <script>
    var evalRecordData = {record_json};
    var ER_RESULT_PAGE_SIZE = 10;
    var erResultPage = 1;
    var erResultMatches = [];
    function erResultApply() {{
      var dataId = (document.getElementById('er-filter-data-id').value || '').trim().toLowerCase();
      var highlevel = (document.getElementById('er-filter-highlevel').value || '').trim().toLowerCase();
      var lowlevel = (document.getElementById('er-filter-lowlevel').value || '').trim().toLowerCase();
      var lowlevelId = (document.getElementById('er-filter-lowlevel-id').value || '').trim().toLowerCase();
      var conclusions = Array.from(document.querySelectorAll('#er-filter-conclusion-panel input[type="checkbox"]:checked')).map(function(option) {{ return option.value; }});
      var count = 0;
      erResultMatches = [];
      document.querySelectorAll('#er-result-table tbody tr[data-record-id]').forEach(function(row) {{
        var match = (!dataId || (row.dataset.dataId || '').toLowerCase().indexOf(dataId) >= 0)
          && (!highlevel || (row.dataset.highlevel || '').toLowerCase().indexOf(highlevel) >= 0)
          && (!lowlevel || (row.dataset.lowlevel || '').toLowerCase().indexOf(lowlevel) >= 0)
          && (!lowlevelId || (row.dataset.lowlevelId || '').toLowerCase().indexOf(lowlevelId) >= 0)
          && (!conclusions.length || conclusions.indexOf(row.dataset.conclusion) >= 0);
        if (match) {{ erResultMatches.push(row); count += 1; }}
      }});
      document.getElementById('er-result-count').textContent = String(count);
      erResultPage = 1;
      erResultRenderPage();
    }}
    function erResultRenderPage() {{
      var totalPages = Math.max(1, Math.ceil(erResultMatches.length / ER_RESULT_PAGE_SIZE));
      if (erResultPage > totalPages) erResultPage = totalPages;
      document.querySelectorAll('#er-result-table tbody tr[data-record-id]').forEach(function(row) {{ row.style.display = 'none'; }});
      var start = (erResultPage - 1) * ER_RESULT_PAGE_SIZE;
      erResultMatches.slice(start, start + ER_RESULT_PAGE_SIZE).forEach(function(row) {{ row.style.display = ''; }});
      document.getElementById('er-result-page-copy').textContent = erResultMatches.length ? erResultPage + ' / ' + totalPages : '0 / 0';
      document.getElementById('er-result-current').textContent = erResultMatches.length ? String(erResultPage) : '0';
      document.getElementById('er-result-prev').disabled = !erResultMatches.length || erResultPage <= 1;
      document.getElementById('er-result-next').disabled = !erResultMatches.length || erResultPage >= totalPages;
    }}
    function erResultPageChange(delta) {{
      erResultPage += delta;
      erResultRenderPage();
    }}
    function erResultClear() {{
      document.getElementById('er-filter-data-id').value = '';
      document.getElementById('er-filter-highlevel').value = '';
      document.getElementById('er-filter-lowlevel').value = '';
      document.getElementById('er-filter-lowlevel-id').value = '';
      mselToggleAll('er-filter-conclusion', false);
      erResultApply();
    }}
    function exportEvalRecords() {{
      var table = document.getElementById('er-result-table');
      if (!table) return;
      var rows = [];
      var headerCells = table.querySelectorAll('thead th');
      var exportColumnCount = Math.max(0, headerCells.length - 1);
      rows.push(Array.from(headerCells).slice(0, exportColumnCount).map(function(cell) {{ return (cell.textContent || '').trim(); }}));
      // erResultMatches is maintained by the filter/pagination logic; export the
      // complete filtered result set rather than only the currently visible page.
      var sourceRows = erResultMatches;
      sourceRows.forEach(function(tr) {{
        if (tr.cells.length < 2) return;
        var row = [];
        for (var i = 0; i < exportColumnCount; i++) row.push((tr.cells[i].textContent || '').replace(/\\s+/g, ' ').trim());
        rows.push(row);
      }});
      if (rows.length <= 1) {{
        if (window.showToast) window.showToast('暂无数据可导出', 'warning');
        return;
      }}
      var csv = rows.map(function(row) {{ return row.map(function(value) {{
        var text = String(value).replace(/"/g, '""');
        return /[,"\\n]/.test(text) ? '"' + text + '"' : text;
      }}).join(','); }}).join('\\n');
      var url = URL.createObjectURL(new Blob(['\\uFEFF' + csv], {{type:'text/csv;charset=utf-8'}}));
      var link = document.createElement('a');
      link.href = url;
      link.download = '评测数据_' + new Date().toISOString().slice(0, 10) + '.csv';
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(function() {{ URL.revokeObjectURL(url); }}, 1000);
      if (window.showToast) window.showToast('已导出 ' + (rows.length - 1) + ' 条数据', 'success');
    }}
    function openEvalRecordVideo(button) {{
      var record = evalRecordData[button.dataset.recordId];
      var index = Number(button.dataset.videoIndex || 0);
      var video = record && record.videos ? record.videos[index] : null;
      if (window.openMediaViewer) window.openMediaViewer('video', index, video ? video.label : '评测视频', video ? video.url : '');
    }}
    erResultApply();
    </script>
    <style>
      .er-replacement {{ min-width:0; }}
      .er-task-context {{ display:flex;align-items:center;gap:18px;margin-bottom:14px;padding:12px 16px;border:1px solid #e4eaed;border-radius:8px;background:#fff; }}
      .er-task-context>a {{ color:#1F80A0;text-decoration:none;font-size:13px; }} .er-task-context>div {{ display:flex;align-items:center;min-width:0; }} .er-task-context-name {{ flex:1; }}
      .er-task-context .er-export-button {{ margin-left:auto; }}
      .er-page-head {{ display:flex;align-items:center;justify-content:space-between;margin-bottom:14px; }} .er-page-head h1 {{ margin:0;font-size:20px;font-weight:600;color:rgba(0,0,0,.85); }}
      .er-task-context b {{ font-size:15px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }} .er-task-context-id {{ font-family:'SF Mono',Menlo,Consolas,monospace;font-size:13px !important;color:rgba(0,0,0,.72); }}
      .er-result-filter-bar {{ display:grid; grid-template-columns:repeat(5,minmax(130px,1fr)) auto; gap:12px; align-items:end; padding:16px; background:#fff; border:1px solid #f0f0f0; border-radius:8px; margin-bottom:12px; }}
      .er-result-filter-bar .ff {{ min-width:0; }} .er-conclusion-filter {{ position:relative; }} .er-conclusion-filter .er-dd-trigger {{ min-height:32px; }} .er-conclusion-filter .er-chips {{ min-height:22px; }}
      .er-result-filter-bar .ff label {{ display:block; margin-bottom:5px; color:rgba(0,0,0,.55); font-size:12px; }}
      .er-result-filter-bar input, .er-result-filter-bar select {{ width:100%; }}
      .er-result-filter-bar .er-dd-panel input[type="checkbox"] {{ width:14px !important;height:14px !important;padding:0 !important;border:0 !important;border-radius:0 !important;appearance:auto !important;-webkit-appearance:auto !important;background:transparent !important;box-shadow:none !important; }}
      .er-result-summary {{ color:rgba(0,0,0,.55); font-size:13px; margin:0 0 10px 2px; }}
      .er-result-card {{ overflow:hidden; }}
      .er-result-table-wrap {{ overflow-x:auto; }}
      .er-result-table {{ min-width:1335px; table-layout:fixed; }}
      .er-result-table thead th {{ background:#f7f8fa; }}
      .er-result-table tbody td {{ height:156px; padding:10px 12px; }}
      .er-record-group, .er-record-id, .er-record-serial {{ font-family:'SF Mono',Menlo,Consolas,monospace; font-size:12px; color:rgba(0,0,0,.65); }}
      .er-record-video-strip {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:5px; min-width:0; }}
      .er-record-video-strip-compact {{ grid-template-rows:28px 120px; gap:0; min-width:500px; background:#050505; border-radius:8px; overflow:hidden; }}
      .er-record-video-prompt {{ grid-column:1/-1; display:flex; align-items:center; justify-content:center; padding:0 12px; background:#050505; color:rgba(255,255,255,.88); font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
      .er-record-video {{ position:relative; min-width:0; height:86px; border:0; border-radius:7px; overflow:hidden; background:linear-gradient(145deg,#243447 0%,#101820 55%,#304352 100%); color:#fff; cursor:default; padding:0; display:flex; align-items:center; justify-content:center; }}
      .er-record-video::before {{ content:''; position:absolute; inset:18px 12px 10px; border:1px solid rgba(255,255,255,.22); border-radius:4px; background:linear-gradient(135deg,rgba(255,255,255,.10),transparent 50%),linear-gradient(25deg,transparent 50%,rgba(100,190,180,.24) 51%,rgba(100,190,180,.03) 78%); }}
      .er-record-video-play {{ position:relative; z-index:1; width:27px; height:27px; border-radius:50%; background:rgba(0,0,0,.48); display:flex; align-items:center; justify-content:center; font-size:11px; padding-left:2px; }}
      .er-record-video-label {{ position:absolute; left:7px; bottom:5px; z-index:1; font-size:10px; color:rgba(255,255,255,.82); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:calc(100% - 14px); }}
      .er-record-video:hover {{ box-shadow:none; }}
      .er-record-video-compact {{ height:120px; border-radius:0; }}
      .er-record-video-compact .er-record-video-play {{ width:23px; height:23px; font-size:10px; }}
      .er-record-video-compact.vid-thumb {{ width:auto; height:120px; flex:none; }}
      .er-record-video-compact.vid-thumb::before {{ content:'▶'; position:absolute; left:50%; top:50%; inset:auto; transform:translate(-50%,-50%); color:rgba(255,255,255,.5); font-size:14px; border:0; border-radius:0; background:none; }}
      .er-record-video-compact .er-record-video-label {{ display:none; }}
      .er-record-conclusion {{ display:inline-flex; align-items:center; gap:7px; white-space:nowrap; }}
      .er-metric-info {{ display:inline-flex; align-items:center; justify-content:center; width:16px; height:16px; border:1px solid #a9cbd4; border-radius:50%; color:#1F80A0; font-size:11px; line-height:1; cursor:help; }}
      .er-metric-info:focus {{ outline:2px solid rgba(31,128,160,.2); outline-offset:1px; }}
      .er-result-pill {{ display:inline-flex; align-items:center; padding:3px 9px; border-radius:5px; font-size:12px; color:rgba(0,0,0,.55); background:#f5f5f5; }}
      .er-result-pass {{ color:#389e0d; background:#f0f9e8; border:1px solid #d9f0c5; }}
      .er-result-fail {{ color:#d4380d; background:#fff1f0; border:1px solid #ffccc7; }}
      .er-record-metrics {{ display:flex; flex-direction:column; gap:4px; color:rgba(0,0,0,.62); font-size:12px; line-height:1.5; }}
      .er-result-pagination {{ display:flex; justify-content:flex-end; align-items:center; gap:5px; padding:12px 16px; color:rgba(0,0,0,.45); font-size:12px; }}
      .er-result-pagination button {{ width:28px; height:28px; border:1px solid #d9d9d9; border-radius:5px; background:#fff; color:rgba(0,0,0,.65); cursor:pointer; }}
      .er-result-pagination button.active {{ color:#1F80A0; border-color:#1F80A0; }}
      .er-result-pagination button:disabled {{ color:#d9d9d9; cursor:not-allowed; }}
      .er-empty {{ text-align:center; padding:52px !important; color:rgba(0,0,0,.35) !important; }}
      @media (max-width:1400px) {{
        .er-result-table {{ min-width:1335px; }}
        .er-result-table th:nth-child(1) {{ width:90px !important; }}
        .er-result-table th:nth-child(2) {{ width:120px !important; }}
        .er-result-table th:nth-child(3) {{ width:520px !important; }}
        .er-result-table th:nth-child(4) {{ width:130px !important; }}
        .er-result-table th:nth-child(5) {{ width:130px !important; }}
        .er-result-table th:nth-child(6) {{ width:140px !important; }}
        .er-result-table th:nth-child(7) {{ width:100px !important; }}
        .er-result-table th:nth-child(8) {{ width:145px !important; }}
        .er-result-table th:nth-child(9) {{ width:60px !important; }}
        .er-record-video-strip-compact {{ min-width:500px; }}
        .er-result-table tbody td {{ padding:8px 7px; font-size:12px; }}
        .er-result-table tbody td:nth-child(5), .er-result-table tbody td:nth-child(7), .er-result-table tbody td:nth-child(8) {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
        .er-record-video-compact.vid-thumb {{ width:auto; height:120px; }}
      }}
      @media (max-width:1000px) {{ .er-result-filter-bar {{ grid-template-columns:repeat(2,minmax(150px,1fr)); }} .er-result-filter-bar .filter-actions {{ grid-column:1/-1; }} }}
    </style>
    '''
    return render_page("评测数据", content, active="eval_records")


@app.route("/eval-records")
def eval_records_page():
    return _render_eval_records_replacement()


@app.route("/tasks/<tid>/data")
def task_data_page(tid):
    if not any(task["id"] == tid for task in EVAL_TASKS):
        return redirect(url_for("tasks_page"))
    return _render_eval_records_replacement(tid)

    # Legacy implementation retained below for compatibility with old links.
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


@app.route("/eval-records/<record_id>")
def eval_record_detail(record_id):
    all_records = _mock_eval_records()
    record_index = next((index for index, item in enumerate(all_records) if item["id"] == record_id), -1)
    record = all_records[record_index] if record_index >= 0 else None
    if not record:
        flash("评测记录不存在", "error")
        return redirect(url_for("eval_records_page"))
    prompt_text = html.escape(record.get("instruction") or record.get("prompt") or "--")
    prompt_en = html.escape(record.get("instruction_en") or "")
    video_html = _eval_record_video_html(record)
    prompt_tags = render_tags_html(record.get("labels", []))
    metric_rows = ''.join(
        f'<tr><td>{html.escape(key)}</td><td>{html.escape(str(value))}</td></tr>'
        for key, value in record.get("metrics", {}).items()
    )
    selected_conclusion = str(record.get("conclusion", "--"))
    task = next((item for item in EVAL_TASKS if item.get("id") == record.get("task_id")), None) or {}
    criterion = get_criterion(task.get("criteria_id", "")) or {}
    result_options = [
        item["type"]
        for item in normalize_result_definitions(criterion.get("result_definitions", {}))
        if item.get("type")
    ]
    if selected_conclusion not in result_options:
        result_options.append(selected_conclusion)
    result_options_html = ''.join(
        f'<span class="er-record-result-option'
        f'{" is-selected" if option == selected_conclusion else ""}"'
        f' aria-current="{"true" if option == selected_conclusion else "false"}">'
        f'{html.escape(option)}</span>'
        for option in result_options
    )
    record_id_html = html.escape(record.get("id", ""))
    recording_id_html = html.escape(record.get("recording_id", "--"))
    checkpoint_html = html.escape(record.get("checkpoint", "--"))
    moztrace_html = _render_moztrace_detail(record)
    prev_record = all_records[record_index - 1] if record_index > 0 else None
    next_record = all_records[record_index + 1] if record_index >= 0 and record_index < len(all_records) - 1 else None
    prev_link = f'<a class="er-detail-nav-link" href="/eval-records/{html.escape(prev_record["id"], quote=True)}">← 上一条</a>' if prev_record else '<span class="er-detail-nav-link is-disabled">← 上一条</span>'
    next_link = f'<a class="er-detail-nav-link" href="/eval-records/{html.escape(next_record["id"], quote=True)}">下一条 →</a>' if next_record else '<span class="er-detail-nav-link is-disabled">下一条 →</span>'
    content = f'''
    <div class="er-detail-page">
      <div class="er-detail-head">
        <a class="er-detail-back" href="/tasks/{html.escape(record.get("task_id", ""), quote=True)}/data">← 返回任务数据</a>
        <span class="er-detail-title">评测记录</span>
        <div class="er-detail-inline-meta" aria-label="记录基本信息">
          <span><em>数据 ID</em><b class="mono">{recording_id_html}</b></span>
          <span><em>checkpoint</em><b>{checkpoint_html}</b></span>
        </div>
      </div>
      <section class="er-detail-prompt">
        <div class="er-detail-prompt-line"><span class="er-detail-prompt-main">{prompt_text}</span><span class="er-detail-prompt-en">{prompt_en}</span></div>
        <div class="er-detail-prompt-tags"><span class="er-detail-section-label">标签</span><div>{prompt_tags}</div></div>
      </section>
      <section class="er-detail-video-card">
        {video_html}
        <div class="er-detail-playback" aria-label="视频播放控制">
          <button type="button" class="er-playback-btn" id="er-playback-toggle" onclick="toggleEvalPlayback()" aria-label="播放视频">▶</button>
          <input id="er-detail-frame-range" type="range" min="0" max="71" value="0" step="1" oninput="setEvalPlaybackFrame(this.value)" aria-label="视频播放进度">
        </div>
      </section>
      <div class="er-detail-tabs" role="tablist">
        <button type="button" class="er-detail-tab active" role="tab" aria-selected="true" onclick="switchEvalRecordTab('record', this)">评测记录</button>
        <button type="button" class="er-detail-tab" role="tab" aria-selected="false" onclick="switchEvalRecordTab('moztrace', this)">moztrace</button>
      </div>
      <section id="er-detail-record-pane" class="er-detail-pane">
        <div class="er-record-summary">
          <div class="er-record-outcome"><span class="er-record-outcome-label">评测结果</span><div class="er-record-result-options">{result_options_html}</div></div>
          <div class="er-record-metrics">
            <table class="er-record-metric-table"><thead><tr><th>指标</th><th>结果</th></tr></thead><tbody>{metric_rows}</tbody></table>
          </div>
        </div>
      </section>
      <section id="er-detail-moztrace-pane" class="er-detail-pane" style="display:none;">{moztrace_html}</section>
      <div class="er-detail-nav">{prev_link}<span class="er-detail-nav-count">{record_index + 1} / {len(all_records)}</span>{next_link}</div>
    </div>
    <script>
    function switchEvalRecordTab(kind, button) {{
      document.querySelectorAll('.er-detail-tab').forEach(function(tab) {{ tab.classList.toggle('active', tab === button); tab.setAttribute('aria-selected', tab === button ? 'true' : 'false'); }});
      document.getElementById('er-detail-record-pane').style.display = kind === 'record' ? '' : 'none';
      document.getElementById('er-detail-moztrace-pane').style.display = kind === 'moztrace' ? '' : 'none';
      syncEvalRecordPaneHeights();
    }}
    function switchMoztracePane(kind, button) {{
      var shell = button.closest('.moztrace-shell');
      if (!shell) return;
      shell.querySelectorAll('.moztrace-tab').forEach(function(tab) {{ tab.classList.toggle('active', tab === button); }});
      shell.querySelectorAll('.moztrace-subpane').forEach(function(pane) {{ pane.style.display = pane.id === 'moztrace-pane-' + kind ? '' : 'none'; }});
      requestAnimationFrame(syncEvalRecordPaneHeights);
    }}
    var evalPlaybackFrame = 0;
    var evalPlaybackTimer = null;
    function setEvalPlaybackFrame(frame) {{
      evalPlaybackFrame = Math.max(0, Math.min(71, Number(frame) || 0));
      var range = document.getElementById('er-detail-frame-range');
      if (range) range.value = evalPlaybackFrame;
      var ratio = evalPlaybackFrame / 71;
      document.querySelectorAll('.moztrace-frame-line').forEach(function(line) {{
        var svg = line.closest('svg');
        if (!svg) return;
        var viewBox = svg.viewBox && svg.viewBox.baseVal;
        var x = 58 + (790 * ratio);
        line.setAttribute('x1', x.toFixed(1));
        line.setAttribute('x2', x.toFixed(1));
      }});
    }}
    function toggleEvalPlayback() {{
      var button = document.getElementById('er-playback-toggle');
      if (evalPlaybackTimer) {{
        clearInterval(evalPlaybackTimer);
        evalPlaybackTimer = null;
        if (button) {{ button.textContent = '▶'; button.setAttribute('aria-label', '播放视频'); }}
        return;
      }}
      if (evalPlaybackFrame >= 71) setEvalPlaybackFrame(0);
      evalPlaybackTimer = setInterval(function() {{
        if (evalPlaybackFrame >= 71) {{ toggleEvalPlayback(); return; }}
        setEvalPlaybackFrame(evalPlaybackFrame + 1);
      }}, 180);
      if (button) {{ button.textContent = 'Ⅱ'; button.setAttribute('aria-label', '暂停视频'); }}
    }}
    function syncEvalRecordPaneHeights() {{
      var panes = [document.getElementById('er-detail-record-pane'), document.getElementById('er-detail-moztrace-pane')];
      if (panes.some(function(pane) {{ return !pane; }})) return;
      panes.forEach(function(pane) {{ pane.style.removeProperty('height'); }});
    }}
    requestAnimationFrame(syncEvalRecordPaneHeights);
    setEvalPlaybackFrame(0);
    window.addEventListener('resize', syncEvalRecordPaneHeights);
    var evalRecordDetailData = {json.dumps({record["id"]: record}, ensure_ascii=False)};
    </script>
    <style>
      .er-detail-page {{ min-width:0; min-height:calc(100vh - 108px); display:flex; flex-direction:column; padding-bottom:0; }}
      .er-detail-head {{ display:flex; align-items:center; gap:12px; margin-bottom:10px; min-height:30px; }}
      .er-detail-back {{ color:#1F80A0; text-decoration:none; font-size:13px; }}
      .er-detail-back:hover {{ text-decoration:underline; }}
      .er-detail-title {{ font-size:18px; font-weight:600; color:rgba(0,0,0,.85); }}
      .er-detail-inline-meta {{ display:flex; align-items:center; gap:18px; min-width:0; margin-left:8px; padding-left:14px; border-left:1px solid #e8ecee; }}
      .er-detail-inline-meta span {{ display:inline-flex; align-items:baseline; gap:6px; min-width:0; }}
      .er-detail-inline-meta em {{ color:rgba(0,0,0,.42); font-size:11px; font-style:normal; }}
      .er-detail-inline-meta b {{ color:rgba(0,0,0,.78); font-size:12px; font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:260px; }}
      .er-detail-inline-meta b.mono {{ font-family:'SF Mono',Menlo,Consolas,monospace; font-size:11px; }}
      .er-detail-prompt {{ background:#e6f4f8; border:1px solid #b8dce8; border-radius:8px; padding:10px 14px; margin-bottom:10px; }}
      .er-detail-section-label {{ color:rgba(0,0,0,.45); font-size:11px; margin-bottom:5px; }}
      .er-detail-prompt-main {{ font-size:14px; font-weight:600; color:#1F80A0; line-height:1.4; }}
      .er-detail-prompt-line {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }}
      .er-detail-prompt-en {{ color:rgba(0,0,0,.45); font-size:12px; }}
      .er-detail-prompt-tags {{ display:flex; align-items:flex-start; gap:10px; margin-top:7px; padding-top:6px; border-top:1px solid rgba(31,128,160,.16); }}
      .er-detail-prompt-tags .er-detail-section-label {{ flex:none; margin:3px 0 0; }}
      .er-detail-prompt-tags > div {{ display:flex; flex-wrap:wrap; gap:4px; }}
      .er-detail-video-card {{ background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:10px 12px; margin-bottom:10px; }}
      .er-detail-video-head {{ display:flex; justify-content:space-between; align-items:center; font-size:13px; font-weight:500; margin-bottom:7px; }}
      .er-detail-video-card .er-record-video-strip {{ min-width:0; gap:8px; }}
      .er-detail-video-card .er-record-video {{ height:150px; }}
      .er-detail-playback {{ display:flex; align-items:center; gap:8px; margin-top:8px; padding:0 2px; color:rgba(0,0,0,.52); font-size:11px; }}
      .er-playback-btn {{ flex:0 0 28px; width:28px; height:28px; padding:0; border:1px solid #c9dddd; border-radius:5px; background:#fff; color:#1F80A0; cursor:pointer; }}
      .er-playback-btn:hover {{ border-color:#1F80A0; background:#f1f7f7; }}
      .er-detail-playback input[type=range] {{ flex:1; min-width:120px; accent-color:#1F80A0; cursor:pointer; }}
      .er-detail-tabs {{ display:flex; gap:4px; border-bottom:1px solid #f0f0f0; margin-bottom:10px; }}
      .er-detail-tab {{ border:0; border-bottom:2px solid transparent; background:transparent; padding:8px 16px; font-size:13px; color:rgba(0,0,0,.55); cursor:pointer; }}
      .er-detail-tab.active {{ color:#1F80A0; border-bottom-color:#1F80A0; font-weight:500; }}
      .er-detail-pane {{ background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:10px 12px; box-sizing:border-box; overflow:auto; max-height:260px; }}
      .er-detail-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:12px; font-size:13px; color:rgba(0,0,0,.72); }}
      .er-record-summary {{ display:flex; flex-direction:column; align-items:stretch; gap:10px; min-height:0; }}
      .er-record-outcome {{ width:100%; display:flex; align-items:flex-start; gap:14px; padding:0 0 12px 2px; border-right:0; border-bottom:1px solid #edf0f2; }}
      .er-record-outcome-label {{ flex:0 0 auto; padding-top:6px; color:rgba(0,0,0,.48); font-size:12px; }}
      .er-record-result-options {{ display:flex; flex-wrap:wrap; gap:8px; min-width:0; }}
      .er-record-result-option {{ display:inline-flex; align-items:center; gap:6px; min-height:30px; box-sizing:border-box; padding:4px 10px; border:1px solid #e1e5e8; border-radius:6px; color:rgba(0,0,0,.55); background:#fafafa; font-size:12px; line-height:20px; }}
      .er-record-result-option.is-selected {{ padding:3px 9px; border:2px solid #1F80A0; color:#1F80A0; background:#e6f4f8; font-weight:400; box-shadow:0 0 0 2px rgba(31,128,160,.08); }}
      .er-record-metrics {{ width:100%; display:flex; align-items:stretch; }}
      .er-record-metric-table {{ width:100%; height:100%; border-collapse:collapse; table-layout:fixed; font-size:13px; }}
      .er-record-metric-table th {{ height:28px; padding:0 10px; background:#f7f8fa; border-bottom:1px solid #edf0f2; color:rgba(0,0,0,.45); font-size:11px; font-weight:500; text-align:left; }}
      .er-record-metric-table th:last-child, .er-record-metric-table td:last-child {{ width:42%; }}
      .er-record-metric-table td {{ height:30px; padding:0 10px; border-bottom:1px solid #edf0f2; color:rgba(0,0,0,.68); text-align:left; }}
      .er-record-metric-table tbody tr:last-child td {{ border-bottom:0; }}
      .er-detail-label {{ display:block; color:rgba(0,0,0,.45); font-size:12px; margin-bottom:7px; }}
      .er-detail-metric-table {{ max-width:640px; }}
      .moztrace-shell {{ color:rgba(0,0,0,.78); min-width:0; }}
      .moztrace-tabs {{ display:inline-flex; align-items:center; gap:3px; max-width:100%; padding:3px; margin:0 0 8px; overflow-x:auto; background:#f1f7f7; border:1px solid #d7e9e9; border-radius:9px; }}
      .moztrace-tab {{ flex:none; border:0; border-radius:6px; background:transparent; color:rgba(0,0,0,.64); padding:7px 13px; font-size:12px; cursor:pointer; white-space:nowrap; transition:all .18s ease; }}
      .moztrace-tab:hover {{ color:#1F80A0; background:#e6f4f4; }}
      .moztrace-tab.active {{ color:#fff; background:#1F80A0; box-shadow:0 1px 2px rgba(31,128,160,.22); }}
      .moztrace-section {{ border:1px solid #e6e8eb; border-radius:4px; overflow:hidden; margin-bottom:8px; background:#fff; }}
      .moztrace-section:last-child {{ margin-bottom:0; }}
      .moztrace-section-title {{ background:#f7f8fa; border-bottom:1px solid #e6e8eb; color:rgba(0,0,0,.65); font-size:11px; padding:5px 8px; }}
      .moztrace-info-table, .moztrace-table {{ width:100%; border-collapse:collapse; table-layout:fixed; font-size:12px; }}
      .moztrace-info-table th, .moztrace-info-table td, .moztrace-table th, .moztrace-table td {{ border-bottom:1px solid #edf0f2; padding:5px 8px; text-align:left; vertical-align:middle; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
      .moztrace-info-table tr:last-child th, .moztrace-info-table tr:last-child td, .moztrace-table tbody tr:last-child td {{ border-bottom:0; }}
      .moztrace-info-table th {{ width:18%; background:#fafbfc; color:rgba(0,0,0,.78); font-weight:600; text-align:center; }}
      .moztrace-info-table td {{ width:32%; color:rgba(0,0,0,.68); }}
      .moztrace-table th {{ background:#f7f8fa; color:rgba(0,0,0,.58); font-weight:500; }}
      .moztrace-table th:nth-child(1) {{ width:12%; }}
      .moztrace-table th:nth-child(2) {{ width:42%; }}
      .moztrace-table th:nth-child(3) {{ width:14%; }}
      .moztrace-table th:nth-child(4) {{ width:22%; }}
      .moztrace-table th:nth-child(5) {{ width:10%; }}
      .moztrace-table-wrap {{ overflow-x:auto; }}
      .moztrace-stat-row {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); }}
      .moztrace-stat-row > div {{ display:flex; flex-direction:column; gap:7px; padding:11px 10px; border-right:1px solid #edf0f2; min-width:0; }}
      .moztrace-stat-row > div:last-child {{ border-right:0; }}
      .moztrace-stat-row b {{ font-size:11px; color:rgba(0,0,0,.58); font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
      .moztrace-stat-row span {{ color:rgba(0,0,0,.82); font-size:16px; font-weight:600; }}
      .moztrace-result {{ color:rgba(0,0,0,.4); }}
      .moztrace-ok {{ color:#389e0d; }}
      .moztrace-player {{ padding:14px; background:#fafbfc; }}
      .moztrace-player-screen {{ height:150px; border-radius:4px; background:linear-gradient(145deg,#244344,#112828); color:rgba(255,255,255,.58); display:flex; align-items:center; justify-content:center; flex-direction:column; gap:8px; }}
      .moztrace-player-screen b {{ width:40px; height:40px; display:flex; align-items:center; justify-content:center; border-radius:50%; color:#fff; background:rgba(255,255,255,.18); font-size:16px; padding-left:2px; }}
      .moztrace-player-controls {{ display:flex; align-items:center; gap:10px; margin-top:12px; color:rgba(0,0,0,.5); font-size:12px; }}
      .moztrace-player-controls button {{ border:0; background:transparent; color:rgba(0,0,0,.55); cursor:pointer; padding:2px 4px; }}
      .moztrace-player-track {{ position:relative; height:4px; background:#e1e5e8; border-radius:2px; flex:1; }}
      .moztrace-player-track i {{ display:block; height:100%; background:#1F80A0; border-radius:2px; }}
      .moztrace-timeline {{ padding:9px 16px 5px; }}
      .moztrace-timeline > div {{ display:grid; grid-template-columns:92px 16px 1fr; gap:10px; min-height:58px; }}
      .moztrace-time {{ color:rgba(0,0,0,.45); font-family:monospace; font-size:11px; padding-top:2px; }}
      .moztrace-timeline i {{ position:relative; width:8px; height:8px; margin-top:4px; background:#1F80A0; border-radius:50%; }}
      .moztrace-timeline i::after {{ content:''; position:absolute; top:8px; left:3px; width:2px; height:50px; background:#cce3e3; }}
      .moztrace-timeline > div:last-child i::after {{ display:none; }}
      .moztrace-timeline p {{ margin:0; display:flex; flex-direction:column; gap:4px; }}
      .moztrace-timeline p b {{ font-size:12px; font-weight:500; color:rgba(0,0,0,.75); }}
      .moztrace-timeline p small {{ font-size:11px; color:rgba(0,0,0,.45); }}
      .moztrace-schema-diagram {{ display:flex; align-items:center; justify-content:center; gap:10px; padding:16px 8px; overflow:auto; background:#fbfcfc; }}
      .moztrace-schema-table {{ flex:0 0 215px; border:1px solid #b8d8d8; border-radius:4px; background:#fff; overflow:hidden; font-family:'SF Mono',Menlo,Consolas,monospace; font-size:11px; color:rgba(0,0,0,.65); }}
      .moztrace-schema-table-wide {{ flex-basis:290px; }}
      .moztrace-schema-table b {{ display:block; padding:8px 10px; color:#fff; background:#1F80A0; font-size:12px; font-weight:600; }}
      .moztrace-schema-table span {{ display:block; padding:5px 10px; border-top:1px solid #edf2f2; white-space:nowrap; }}
      .moztrace-schema-relation {{ flex:0 0 36px; color:#1F80A0; font-size:12px; font-weight:600; text-align:center; white-space:nowrap; }}
      .moztrace-player-toolbar, .moztrace-analysis-toolbar, .moztrace-timeline-toolbar {{ display:flex; align-items:center; flex-wrap:wrap; gap:8px; min-height:38px; margin-bottom:12px; color:rgba(0,0,0,.65); font-size:12px; }}
      .moztrace-player-toolbar button, .moztrace-player-toolbar select, .moztrace-analysis-toolbar select, .moztrace-timeline-toolbar select, .moztrace-timeline-toolbar button {{ min-height:28px; border:1px solid #ccdcdc; border-radius:4px; background:#fff; color:rgba(0,0,0,.72); padding:3px 9px; font-size:12px; }}
      .moztrace-player-toolbar button, .moztrace-timeline-toolbar button {{ cursor:pointer; }}
      .moztrace-player-toolbar button:hover, .moztrace-timeline-toolbar button:hover {{ border-color:#1F80A0; color:#1F80A0; }}
      .moztrace-player-toolbar input[type=range] {{ flex:1; min-width:120px; accent-color:#1F80A0; }}
      .moztrace-player-toolbar > span {{ white-space:nowrap; color:rgba(0,0,0,.55); }}
      .moztrace-camera-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }}
      .moztrace-camera-grid > div {{ min-width:0; border:1px solid #dfe9e9; border-radius:5px; padding:5px; background:#fafcfc; text-align:center; }}
      .moztrace-camera-frame {{ height:130px; display:flex; align-items:flex-end; justify-content:center; border-radius:3px; overflow:hidden; position:relative; background-color:#263d3e; background-image:linear-gradient(155deg,rgba(255,255,255,.24) 0 7%,transparent 7% 28%,rgba(222,235,227,.16) 28% 31%,transparent 31%),linear-gradient(175deg,transparent 0 52%,rgba(195,173,135,.36) 52% 68%,rgba(74,100,92,.7) 68% 100%); }}
      .moztrace-camera-frame::before {{ content:''; position:absolute; left:9%; right:9%; top:18%; height:34%; border:1px solid rgba(255,255,255,.35); border-radius:4px; transform:perspective(180px) rotateX(8deg); }}
      .moztrace-camera-frame span {{ position:relative; z-index:1; width:100%; padding:5px 3px; background:rgba(0,0,0,.4); color:rgba(255,255,255,.82); font:11px monospace; }}
      .moztrace-camera-grid small {{ display:block; padding:5px 0 2px; color:rgba(0,0,0,.52); font-size:11px; }}
      .moztrace-chart-panel {{ margin-top:6px; }}
      .moztrace-chart-wrap {{ width:100%; min-width:520px; overflow:hidden; }}
      .moztrace-chart-title {{ padding:4px 0 1px; text-align:center; color:rgba(0,0,0,.7); font-size:13px; }}
      .moztrace-chart {{ display:block; width:100%; height:auto; max-height:180px; }}
      .moztrace-chart-axis {{ fill:rgba(0,0,0,.55); font-size:11px; text-anchor:middle; }}
      .moztrace-chart-legend {{ display:flex; flex-wrap:wrap; justify-content:flex-end; gap:8px 14px; padding:0 10px 8px; color:rgba(0,0,0,.55); font-size:11px; }}
      .moztrace-chart-legend span {{ display:inline-flex; align-items:center; gap:4px; }}
      .moztrace-chart-legend i {{ display:inline-block; width:18px; height:2px; border-radius:1px; }}
      .moztrace-segmented {{ display:flex; justify-content:center; gap:0; margin:5px 0 2px; }}
      .moztrace-segmented button {{ border:1px solid #c9dddd; background:#fff; color:rgba(0,0,0,.62); padding:6px 14px; font-size:12px; cursor:pointer; }}
      .moztrace-segmented button:first-child {{ border-radius:5px 0 0 5px; }}
      .moztrace-segmented button:last-child {{ border-radius:0 5px 5px 0; }}
      .moztrace-segmented button + button {{ border-left:0; }}
      .moztrace-segmented button.active {{ color:#fff; background:#1F80A0; border-color:#1F80A0; }}
      .moztrace-analysis-toolbar label, .moztrace-timeline-toolbar label {{ display:inline-flex; align-items:center; gap:6px; }}
      .moztrace-analysis-toolbar select {{ min-width:210px; }}
      .moztrace-timeline-toolbar select[multiple] {{ min-width:120px; }}
      .moztrace-checkbox {{ cursor:pointer; }}
      .moztrace-checkbox input {{ accent-color:#1F80A0; }}
      .moztrace-latency-cards {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-top:12px; }}
      .moztrace-latency-cards > div {{ display:flex; flex-direction:column; gap:5px; padding:10px 12px; min-width:0; border:1px solid #dfe9e9; border-radius:5px; background:#f8fbfb; }}
      .moztrace-latency-cards span {{ color:rgba(0,0,0,.52); font-size:11px; }}
      .moztrace-latency-cards b {{ color:#1F80A0; font-size:16px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
      .moztrace-latency-table th:first-child, .moztrace-latency-table td:first-child {{ width:36%; }}
      .moztrace-latency-table th:nth-child(2), .moztrace-latency-table td:nth-child(2) {{ width:18%; }}
      .moztrace-bar {{ display:block; height:6px; border-radius:3px; background:#eef1f4; overflow:hidden; }}
      .moztrace-bar i {{ display:block; height:100%; background:#1F80A0; border-radius:3px; }}
      .er-detail-nav {{ display:flex; align-items:center; justify-content:space-between; margin-top:auto; padding:10px 2px 0; min-height:40px; position:sticky; bottom:0; z-index:5; background:rgba(255,255,255,.96); border-top:1px solid #edf0f2; }}
      .er-detail-nav-link {{ color:#1F80A0; text-decoration:none; font-size:13px; }}
      .er-detail-nav-link:hover {{ text-decoration:underline; }}
      .er-detail-nav-link.is-disabled {{ color:rgba(0,0,0,.25); }}
      .er-detail-nav-count {{ color:rgba(0,0,0,.4); font-size:12px; }}
      .er-detail-video-card .lab-vid.er-record-video::before {{ content:none; }}
      .er-detail-video-card .lab-vid.er-record-video {{ color:rgba(255,255,255,.18); font-size:32px; }}
      @media (max-width:900px) {{ .er-detail-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .er-detail-video-card .er-record-video {{ height:170px; }} }}
      @media (max-width:620px) {{ .er-detail-head {{ flex-wrap:wrap; }} .er-detail-inline-meta {{ flex-basis:100%; margin-left:0; padding-left:0; border-left:0; }} .er-detail-video-card .er-record-video {{ height:160px; }} }}
      @media (max-width:620px) {{ .er-record-metrics {{ width:100%; }} }}
      @media (max-width:620px) {{ .er-detail-video-card .er-record-video-strip {{ grid-template-columns:1fr; }} }}
      @media (max-width:720px) {{ .moztrace-stat-row {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .moztrace-stat-row > div:nth-child(2n) {{ border-right:0; }} .moztrace-stat-row > div {{ border-bottom:1px solid #edf0f2; }} .moztrace-camera-grid {{ grid-template-columns:1fr; }} .moztrace-camera-frame {{ height:180px; }} .moztrace-latency-cards {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .moztrace-schema-diagram {{ justify-content:flex-start; }} }}
    </style>
    '''
    return render_page(f"评测记录 {record_id_html}", content, active="eval_records")


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
