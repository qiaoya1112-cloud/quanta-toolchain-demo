"""
具身云 · 开发者工具链 MVP Demo
Embodied Cloud · Developer Toolchain MVP (interactive prototype)

Framework: Flask + HTML/CSS (inline templates), Ant Design v4 theme (primary #149DAA)
参考「火山引擎控制台」的门户 + 多平台架构, 以及「具身数据管理平台」的代码与样式规则。

架构 (火山引擎风格):
  / (门户)                  控制台总览 · 平台入口卡片 · 数据飞轮总览 · 资源概览
  /data/*  (数据平台)        采集任务 / 自动处理 / 质检 / 标注 / 数据集
  /model/* (模型平台)        训练实验 / 评测 / 部署 / 模型仓库
  /device/* (设备平台)       设备列表 / 真机预约
  /asset/* (资产平台)        端到端血缘

  每个子平台拥有独立的左侧栏 (含平台 logo + 自己的导航树);
  顶部 nav 始终有「总览」按钮可一键回到门户。

Usage:
  pip install flask
  python3 toolchain_demo.py
  # Open http://localhost:5004
"""

import math
import html
import os
import re
import sys
import json
from urllib.parse import quote
from flask import Flask, render_template_string, request, redirect, jsonify

app = Flask(__name__)
app.secret_key = "embodied-toolchain-mvp-demo"

# ── 引入 data_platform 模块, 作为模型平台 -> 数据子模块的实现 ──
# 注意: 只 import 它的 handler 函数 + 静态资源, 不让它启动自己的 Flask app
_DP_DIR = os.environ.get("DP_DIR", os.path.dirname(os.path.abspath(__file__)))
try:
    if _DP_DIR not in sys.path:
        sys.path.insert(0, _DP_DIR)
    import data_platform as dp
    DP_AVAILABLE = True
except Exception as e:
    print(f"[warn] data_platform 模块导入失败: {e}")
    dp = None
    DP_AVAILABLE = False

# ── 引入 quanta_eval_platform 模块, 作为模型平台 -> 评测子模块的实现 ──
_EP_DIR = os.environ.get("EP_DIR", os.path.dirname(os.path.abspath(__file__)))
try:
    if _EP_DIR not in sys.path:
        sys.path.insert(0, _EP_DIR)
    import quanta_eval_platform as ep
    EP_AVAILABLE = True
except Exception as e:
    print(f"[warn] quanta_eval_platform 模块导入失败: {e}")
    ep = None
    EP_AVAILABLE = False

# ════════════════════════════════════════════════════════════════
# Section 1: Mock Data
# ════════════════════════════════════════════════════════════════

# ── 数据平台 ──

COLLECT_TASKS = [
    # ── DEMO 演示链路采集任务（勿删，用于血缘全功能覆盖）──
    {"id": "19001", "name": "20260610_CleanWhiteboard_Moz1WB_original",
     "project": "DEMO预训练采集", "status": "completed", "priority": "中", "stage": "标注",
     "source_type": "original",
     "collected": 120, "qc_pass": 115, "qc_warn": 3, "qc_fail": 2,
     "label_done": 115, "label_total": 120, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-10", "due": "2026-06-12"},
    {"id": "19002", "name": "20260614_CleanWhiteboard_Moz1WB_dagger",
     "project": "DEMO Dagger 数据聚合", "status": "completed", "priority": "高", "stage": "标注",
     "source_type": "dagger", "src_checkpoint_id": "9001", "src_experiment_id": "—",
     "src_dagger_at": "2026-06-14 09:00", "src_failure_type": "抓取失败", "src_trigger_device": "moz1-003",
     "collected": 45, "qc_pass": 42, "qc_warn": 2, "qc_fail": 1,
     "label_done": 42, "label_total": 45, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-18", "due": "2026-06-20"},
    {"id": "19003", "name": "20260611_CleanWhiteboard_Moz1WB_originalB",
     "project": "DEMO预训练采集", "status": "completed", "priority": "中", "stage": "标注",
     "source_type": "original",
     "collected": 60, "qc_pass": 58, "qc_warn": 1, "qc_fail": 1,
     "label_done": 58, "label_total": 60, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-11", "due": "2026-06-13"},
    {"id": "19004", "name": "20260608_DeskOrganize_Moz1Desk_original",
     "project": "DEMO预训练采集", "status": "completed", "priority": "中", "stage": "标注",
     "source_type": "original",
     "collected": 90, "qc_pass": 85, "qc_warn": 3, "qc_fail": 2,
     "label_done": 85, "label_total": 90, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-08", "due": "2026-06-10"},
    {"id": "19005", "name": "20260615_DeskOrganize_Moz1Desk_dagger",
     "project": "DEMO Dagger 数据聚合", "status": "completed", "priority": "高", "stage": "质检",
     "source_type": "dagger", "src_checkpoint_id": "9001", "src_experiment_id": "—",
     "src_dagger_at": "2026-06-15 11:00", "src_failure_type": "物体遮挡", "src_trigger_device": "moz1-005",
     "collected": 30, "qc_pass": 28, "qc_warn": 1, "qc_fail": 1,
     "label_done": 28, "label_total": 30, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-15", "due": "2026-06-17"},
    {"id": "19006", "name": "20260609_DeskOrganize_Moz1Desk_originalB",
     "project": "DEMO预训练采集", "status": "completed", "priority": "中", "stage": "标注",
     "source_type": "original",
     "collected": 55, "qc_pass": 52, "qc_warn": 2, "qc_fail": 1,
     "label_done": 52, "label_total": 55, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-09", "due": "2026-06-11"},
    {"id": "19007", "name": "20260605_DeskClean_Moz1Desk_baseline",
     "project": "DEMO预训练采集", "status": "completed", "priority": "低", "stage": "标注",
     "source_type": "original",
     "collected": 50, "qc_pass": 48, "qc_warn": 1, "qc_fail": 1,
     "label_done": 48, "label_total": 50, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-05", "due": "2026-06-07"},
    {"id": "11092", "name": "20260529_河北省石家庄元氏县马村乡使庄村富强东路19号_光轮智能_UDASv2",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "标注",
     "source_type": "original",
     "collected": 180, "qc_pass": 171, "qc_warn": 4, "qc_fail": 5,
     "label_done": 0, "label_total": 176, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "11091", "name": "20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "采集",
     "source_type": "original",
     "collected": 18, "qc_pass": 0, "qc_warn": 0, "qc_fail": 18,
     "label_done": 0, "label_total": 18, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "11090", "name": "20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "采集",
     "source_type": "original",
     "collected": 42, "qc_pass": 0, "qc_warn": 0, "qc_fail": 42,
     "label_done": 0, "label_total": 42, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "11089", "name": "20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "质检",
     "source_type": "original",
     "collected": 56, "qc_pass": 0, "qc_warn": 0, "qc_fail": 56,
     "label_done": 0, "label_total": 56, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "11088", "name": "20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "质检",
     "source_type": "original",
     "collected": 28, "qc_pass": 0, "qc_warn": 0, "qc_fail": 28,
     "label_done": 0, "label_total": 28, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "11087", "name": "20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "标注",
     "source_type": "original",
     "collected": 31, "qc_pass": 1, "qc_warn": 0, "qc_fail": 30,
     "label_done": 0, "label_total": 31, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "12088", "name": "20260618_Dagger回流_擦白板抓取失败案例",
     "project": "Dagger 数据聚合", "status": "running", "priority": "高", "stage": "标注",
     "source_type": "dagger",
     "src_checkpoint_id": "7500",
     "src_experiment_id": "exp_7560",
     "src_dagger_at": "2026-06-18 14:30",
     "src_failure_type": "抓取失败",
     "src_trigger_device": "moz1-003",
     "collected": 45, "qc_pass": 40, "qc_warn": 3, "qc_fail": 2,
     "label_done": 12, "label_total": 43,
     "created": "2026-06-18", "due": "2026-06-20", "owner": "system_dagger",
     "robot": "moz1-003", "scene": "办公室", "current": 45, "target": 50},
    {"id": "12089", "name": "20260619_Dagger回流_整理桌面物体遮挡",
     "project": "Dagger 数据聚合", "status": "completed", "priority": "中", "stage": "质检",
     "source_type": "dagger",
     "src_checkpoint_id": "7757",
     "src_experiment_id": "exp_7757",
     "src_dagger_at": "2026-06-19 09:15",
     "src_failure_type": "物体遮挡",
     "src_trigger_device": "moz1-005",
     "collected": 28, "qc_pass": 25, "qc_warn": 2, "qc_fail": 1,
     "label_done": 25, "label_total": 27,
     "created": "2026-06-19", "due": "2026-06-21", "owner": "system_dagger",
     "robot": "moz1-005", "scene": "办公室", "current": 28, "target": 30},
]


# 数据管理: recording 拍平的列表 (节点流转 质检→切分→标注)
RECORDINGS = [
    {"id": "4057808", "task_id": "11092", "collection_id": "C-3635",
     "serial": "UDAS-007 96-E579", "stage": "质检",
     "collect_result": "成功", "qc_result": "合格", "label_status": "未标注",
     "op_collect": "刘素粉", "op_qc": "包媛桐"},
    {"id": "4057761", "task_id": "11092", "collection_id": "C-3635",
     "serial": "UDAS-007 96-E579", "stage": "质检",
     "collect_result": "成功", "qc_result": "合格", "label_status": "未标注",
     "op_collect": "刘素粉", "op_qc": "包媛桐"},
    {"id": "4057711", "task_id": "11092", "collection_id": "C-3635",
     "serial": "UDAS-007 96-E579", "stage": "切分",
     "collect_result": "成功", "qc_result": "合格", "label_status": "未标注",
     "op_collect": "刘素粉", "op_qc": "包媛桐"},
    {"id": "4057669", "task_id": "11092", "collection_id": "C-3635",
     "serial": "UDAS-007 96-E579", "stage": "标注",
     "collect_result": "成功", "qc_result": "合格", "label_status": "标注中",
     "op_collect": "刘素粉", "op_qc": "包媛桐"},
    {"id": "4057625", "task_id": "11091", "collection_id": "C-3641",
     "serial": "UDAS-007 96-E579", "stage": "质检",
     "collect_result": "成功", "qc_result": "合格", "label_status": "未标注",
     "op_collect": "李明", "op_qc": "包媛桐"},
    {"id": "4057588", "task_id": "11091", "collection_id": "C-3641",
     "serial": "UDAS-007 96-E579", "stage": "质检",
     "collect_result": "失败", "qc_result": "—", "label_status": "—",
     "op_collect": "李明", "op_qc": "—"},
    {"id": "4057499", "task_id": "11090", "collection_id": "C-3642",
     "serial": "UDAS-007 96-E579", "stage": "切分",
     "collect_result": "成功", "qc_result": "合格", "label_status": "未标注",
     "op_collect": "王芳", "op_qc": "包媛桐"},
    {"id": "4057422", "task_id": "11089", "collection_id": "C-3643",
     "serial": "UDAS-007 96-E579", "stage": "标注",
     "collect_result": "成功", "qc_result": "合格", "label_status": "已完成",
     "op_collect": "王芳", "op_qc": "包媛桐"},
]

PROCESS_JOBS = [
    {"id": "pj_201", "task": "擦白板 · 第 3 批", "steps": "时间戳对齐 · 抽帧 · 切 Episode",
     "status": "done", "ep_count": 156, "dur": "23m", "at": "2026-06-13 10:30"},
    {"id": "pj_202", "task": "整理桌面 · 导师演示", "steps": "时间戳对齐 · 抽帧 · 切 Episode",
     "status": "done", "ep_count": 120, "dur": "18m", "at": "2026-06-09 09:15"},
    {"id": "pj_203", "task": "浇花 · 试点", "steps": "时间戳对齐 · 抽帧",
     "status": "running", "ep_count": 0, "dur": "—", "at": "2026-06-16 14:08"},
    {"id": "pj_204", "task": "擦白板 · 补采", "steps": "时间戳对齐 · 抽帧 · 切 Episode",
     "status": "done", "ep_count": 50, "dur": "8m", "at": "2026-06-06 10:00"},
    {"id": "pj_205", "task": "擦白板 · 第 3 批 (重跑)", "steps": "时间戳对齐 · 抽帧 · 切 Episode",
     "status": "failed", "ep_count": 0, "dur": "—", "at": "2026-06-13 09:42"},
    {"id": "pj_206", "task": "擦白板 · 评测留出", "steps": "时间戳对齐 · 抽帧 · 切 Episode",
     "status": "done", "ep_count": 12, "dur": "3m", "at": "2026-06-13 11:00"},
]

QC_RUNS = [
    {"id": "qc_301", "task": "擦白板 · 第 3 批", "ep_count": 156, "auto_pass": 142, "auto_warn": 11, "auto_fail": 3,
     "human_done": 14, "human_total": 14, "reviewer": "joanna.qiao", "status": "in_review", "at": "2026-06-13 11:00"},
    {"id": "qc_302", "task": "整理桌面 · 导师演示", "ep_count": 120, "auto_pass": 118, "auto_warn": 2, "auto_fail": 0,
     "human_done": 2, "human_total": 2, "reviewer": "Lance Li", "status": "done", "at": "2026-06-09 11:00"},
    {"id": "qc_303", "task": "擦白板 · 补采", "ep_count": 50, "auto_pass": 48, "auto_warn": 2, "auto_fail": 0,
     "human_done": 2, "human_total": 2, "reviewer": "joanna.qiao", "status": "done", "at": "2026-06-06 14:00"},
    {"id": "qc_304", "task": "浇花 · 试点", "ep_count": 32, "auto_pass": 0, "auto_warn": 0, "auto_fail": 0,
     "human_done": 0, "human_total": 0, "reviewer": "—", "status": "pending", "at": "—"},
    {"id": "qc_305", "task": "擦白板 · 评测留出", "ep_count": 12, "auto_pass": 12, "auto_warn": 0, "auto_fail": 0,
     "human_done": 0, "human_total": 0, "reviewer": "—", "status": "done", "at": "2026-06-13 11:10"},
]

LABEL_TASKS = [
    {"id": "lt_401", "name": "擦白板 · 第 3 批", "template": "动作分段 + 关键帧", "ep_count": 142,
     "labeled": 89, "annotator": "joanna.qiao", "status": "in_progress", "created": "2026-06-13 14:00"},
    {"id": "lt_402", "name": "整理桌面 · 导师演示", "template": "动作分段 + 关键帧", "ep_count": 118,
     "labeled": 118, "annotator": "Lance Li", "status": "done", "created": "2026-06-09 15:30"},
    {"id": "lt_403", "name": "擦白板 · 补采", "template": "动作分段 + 关键帧", "ep_count": 48,
     "labeled": 48, "annotator": "joanna.qiao", "status": "done", "created": "2026-06-07 09:00"},
    {"id": "lt_404", "name": "整理桌面 · 新场景", "template": "动作分段 + 关键帧", "ep_count": 0,
     "labeled": 0, "annotator": "—", "status": "pending", "created": "2026-06-15 09:00"},
    {"id": "lt_405", "name": "擦白板 · 评测留出", "template": "动作分段 + 关键帧", "ep_count": 12,
     "labeled": 12, "annotator": "joanna.qiao", "status": "done", "created": "2026-06-13 14:30"},
]

DATASETS = [
    # ── DEMO 演示链路数据集（勿删）──
    {"id": "DEMO_DS_9001", "name": "clean_whiteboard", "version": "v5", "type": "train",
     "episodes": 225, "frames": 81000, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "joanna.qiao", "status": "active", "created": "2026-06-16 10:00",
     "source_tasks": ["19001", "19002", "19003"]},
    {"id": "DEMO_DS_9002", "name": "tidy_desk_A", "version": "v2", "type": "train",
     "episodes": 120, "frames": 43200, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "Lance Li", "status": "active", "created": "2026-06-16 11:00",
     "source_tasks": ["19004", "19005"]},
    {"id": "DEMO_DS_9003", "name": "tidy_desk_B", "version": "v1", "type": "train",
     "episodes": 55, "frames": 19800, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "Lance Li", "status": "active", "created": "2026-06-16 12:00",
     "source_tasks": ["19006"]},
    {"id": "DEMO_DS_9004", "name": "clean_table_baseline", "version": "v1", "type": "train",
     "episodes": 50, "frames": 18000, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "Min Chen", "status": "active", "created": "2026-06-16 13:00",
     "source_tasks": ["19007"]},
    {"id": "ds_500", "name": "clean_whiteboard_v3", "version": "v3", "type": "train",
     "episodes": 95, "frames": 34200, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "joanna.qiao", "status": "active", "created": "2026-06-10 10:00",
     "source_tasks": ["11092"]},
    {"id": "ds_501", "name": "clean_whiteboard_v4", "version": "v4", "type": "train",
     "episodes": 137, "frames": 51200, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "joanna.qiao", "status": "active", "created": "2026-06-14 10:00",
     "source_tasks": ["11092", "11091"]},
    {"id": "ds_502", "name": "tidy_desk_v2", "version": "v2", "type": "train",
     "episodes": 118, "frames": 44600, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "Lance Li", "status": "active", "created": "2026-06-09 17:00",
     "source_tasks": ["11089", "12089"]},
    {"id": "ds_503", "name": "plant_pour_pilot", "version": "v1", "type": "train",
     "episodes": 0, "frames": 0, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "Min Chen", "status": "pending", "created": "2026-06-16 14:30",
     "source_tasks": ["11090"]},
    {"id": "ds_504", "name": "clean_whiteboard_eval_v1", "version": "v1", "type": "eval",
     "episodes": 12, "frames": 4400, "train_ratio": 0.0, "val_ratio": 0.0, "test_ratio": 1.0,
     "owner": "joanna.qiao", "status": "active", "created": "2026-06-14 11:00",
     "source_tasks": ["11087"]},
    {"id": "ds_505", "name": "clean_whiteboard_v5", "version": "v5", "type": "train",
     "episodes": 182, "frames": 65400, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "joanna.qiao", "status": "active", "created": "2026-06-19 10:00",
     "source_tasks": ["11092", "11091", "12088"]},
]

# ── 模型平台 ──

EXPERIMENTS = [
    # ── DEMO 演示链路训练任务（勿删）──
    {"id": "DEMO_EXP_9001", "name": "20260617_pi05_cleanwhiteboard_v5_main",
     "model_type": "Spirit v1.7", "dataset": "clean_whiteboard", "dataset_id": "DEMO_DS_9001",
     "dataset_ids": ["DEMO_DS_9001"], "tag": "—",
     "epochs": 50, "current_epoch": 50,
     "best_metric": 0.873, "metric_name": "成功率", "status": "done",
     "started": "2026-06-17 03:00:00", "dur": "8h 30m", "owner": "joanna.qiao"},
    {"id": "DEMO_EXP_9002", "name": "20260618_pi05_cleanwhiteboard_v5_ctrl",
     "model_type": "Spirit v1.7", "dataset": "clean_whiteboard", "dataset_id": "DEMO_DS_9001",
     "dataset_ids": ["DEMO_DS_9001"], "tag": "—",
     "epochs": 50, "current_epoch": 45,
     "best_metric": 0.851, "metric_name": "成功率", "status": "running",
     "started": "2026-06-18 09:00:00", "dur": "—", "owner": "Lance Li"},
    {"id": "DEMO_EXP_9003", "name": "20260618_pi05_tidydesk_joint_train",
     "model_type": "Spirit v1.7", "dataset": "tidy_desk_A + tidy_desk_B", "dataset_id": "DEMO_DS_9002",
     "dataset_ids": ["DEMO_DS_9002", "DEMO_DS_9003"], "tag": "—",
     "epochs": 50, "current_epoch": 50,
     "best_metric": 0.828, "metric_name": "成功率", "status": "done",
     "started": "2026-06-18 14:00:00", "dur": "9h 10m", "owner": "Lance Li"},
    {"id": "DEMO_EXP_9004", "name": "20260620_pi05_cleantable_baseline",
     "model_type": "Spirit v1.7", "dataset": "clean_table_baseline", "dataset_id": "DEMO_DS_9004",
     "dataset_ids": ["DEMO_DS_9004"], "tag": "—",
     "epochs": 50, "current_epoch": 50,
     "best_metric": 0.781, "metric_name": "成功率", "status": "done",
     "started": "2026-06-20 08:00:00", "dur": "7h 40m", "owner": "Min Chen"},
    {"id": "DEMO_EXP_9005", "name": "20260621_pi05_cleanwhiteboard_v6_queued",
     "model_type": "Spirit v1.7", "dataset": "clean_whiteboard", "dataset_id": "DEMO_DS_9001",
     "dataset_ids": ["DEMO_DS_9001"], "tag": "—",
     "epochs": 50, "current_epoch": 0,
     "best_metric": 0.0, "metric_name": "成功率", "status": "queued",
     "started": "2026-06-21 10:00:00", "dur": "—", "owner": "joanna.qiao"},
    {"id": "exp_7916", "name": "robotwin_pi05_datamil_stack_blocks_two_top10pct_cotrain",
     "model_type": "Spirit v1.7", "dataset": "—", "dataset_id": "ds_505", "dataset_ids": ["ds_505", "ds_502"], "tag": "—",
     "epochs": 50, "current_epoch": 35,
     "best_metric": 0.852, "metric_name": "成功率", "status": "running",
     "started": "2026-06-17 03:23:39", "dur": "—", "owner": "—"},
    {"id": "exp_7757", "name": "20260615_pi05_oldft_sortpill_newobs_centercrop_manip2",
     "model_type": "Spirit v1.7", "dataset": "—", "dataset_id": "ds_505", "tag": "—",
     "epochs": 50, "current_epoch": 28,
     "best_metric": 0.821, "metric_name": "成功率", "status": "running",
     "started": "2026-06-16 11:57:35", "dur": "—", "owner": "—"},
    {"id": "exp_7560", "name": "20260615_HouseHold_newper_stop_32",
     "model_type": "Spirit v1.7", "dataset": "—", "dataset_id": "ds_501", "tag": "—",
     "epochs": 50, "current_epoch": 33,
     "best_metric": 0.812, "metric_name": "成功率", "status": "running",
     "started": "2026-06-16 11:18:17", "dur": "—", "owner": "—"},
    {"id": "exp_7539", "name": "20260602_ManualDagger2_NarrowTable_Moz1WB",
     "model_type": "Spirit v1.6", "dataset": "tidy_desk_v2", "dataset_id": "ds_502", "tag": "—",
     "epochs": 50, "current_epoch": 50,
     "best_metric": 0.873, "metric_name": "成功率", "status": "done",
     "started": "2026-06-16 01:52:20", "dur": "9h 12m", "owner": "—"},
    {"id": "exp_7466", "name": "20260615_pi05_oldft_sortpill_newobs_centercrop",
     "model_type": "Spirit v1.7", "dataset": "—", "tag": "—",
     "epochs": 50, "current_epoch": 32,
     "best_metric": 0.795, "metric_name": "成功率", "status": "running",
     "started": "2026-06-15 19:54:01", "dur": "—", "owner": "—"},
    {"id": "exp_7374", "name": "20260615_PickBottle_Pico",
     "model_type": "Spirit v1.7", "dataset": "—", "tag": "—",
     "epochs": 50, "current_epoch": 50,
     "best_metric": 0.848, "metric_name": "成功率", "status": "done",
     "started": "2026-06-15 13:04:06", "dur": "8h 22m", "owner": "—"},
    {"id": "exp_7325", "name": "20260615_HouseHold_0601_5w_32",
     "model_type": "Spirit v1.7", "dataset": "—", "tag": "—",
     "epochs": 50, "current_epoch": 33,
     "best_metric": 0.815, "metric_name": "成功率", "status": "running",
     "started": "2026-06-15 11:39:45", "dur": "—", "owner": "Lance Li"},
    {"id": "exp_7285", "name": "20260615_pi05_up_Pen_1h_8",
     "model_type": "Spirit v1.7", "dataset": "—", "tag": "—",
     "epochs": 50, "current_epoch": 50,
     "best_metric": 0.792, "metric_name": "成功率", "status": "done",
     "started": "2026-06-15 11:38:44", "dur": "9h 10m", "owner": "—"},
    {"id": "exp_6873", "name": "20260614_pi05_SkewerFruits_from_0322_8",
     "model_type": "Spirit v1.7", "dataset": "—", "tag": "—",
     "epochs": 50, "current_epoch": 22,
     "best_metric": 0.621, "metric_name": "成功率", "status": "running",
     "started": "2026-06-15 00:46:53", "dur": "—", "owner": "Maple Liu"},
    {"id": "exp_6869", "name": "20260614_pi05_SkewerFruits_0322_new_check_32",
     "model_type": "Spirit v1.7", "dataset": "—", "tag": "—",
     "epochs": 50, "current_epoch": 12,
     "best_metric": 0.0, "metric_name": "成功率", "status": "failed",
     "started": "2026-06-14 23:32:34", "dur": "1h 40m", "owner": "Maple Liu"},
]

EVALS = [
    # ── 评测任务数据来自 quanta_eval_platform.EVAL_TASKS ──
    # 这里作为血缘系统的数据源，保持与评测平台同步
    {"id": "t1", "task_no": 1001, "name": "Spirit v1.5 vs v1.6-alpha 基础能力横测",
     "benchmark": "基础能力横测", "status": "评测完成", "at": "2026-04-05", "ckpt_id": "7916", "success_rate": 0.873},
    {"id": "t2", "task_no": 1002, "name": "Spirit v1.6 全版本综合评测",
     "benchmark": "综合评测", "status": "评测中", "at": "2026-04-08", "ckpt_id": "7757", "success_rate": 0.792},
    {"id": "t3", "task_no": 1003, "name": "Spirit v1.6-rc1 vs 外部基线对标",
     "benchmark": "外部基线对标", "status": "采集中", "at": "2026-04-10", "ckpt_id": "7560", "success_rate": 0.848},
    {"id": "t4", "task_no": 1004, "name": "工具使用场景专项测试",
     "benchmark": "工具使用测试", "status": "未开始", "at": "2026-04-12", "ckpt_id": "7466", "success_rate": None},
    {"id": "t5", "task_no": 1005, "name": "Spirit v1.6-rc1 多维能力量表评估",
     "benchmark": "多维能力评估", "status": "评测中", "at": "2026-04-14", "ckpt_id": "9001", "success_rate": 0.889},
    # ── DEMO 演示链路评测（用于完整血缘展示）──
    {"id": "t6", "task_no": 1006, "name": "白板清洁基础能力评测_v5_ckpt40k",
     "benchmark": "白板清洁基础", "status": "评测完成", "at": "2026-06-17", "ckpt_id": "9001", "success_rate": 0.873},
    {"id": "t7", "task_no": 1007, "name": "白板清洁进阶场景评测_v5_ckpt40k",
     "benchmark": "白板清洁进阶", "status": "评测完成", "at": "2026-06-17", "ckpt_id": "9001", "success_rate": 0.865},
    {"id": "t8", "task_no": 1008, "name": "白板清洁基础能力评测_v5_ckpt50k",
     "benchmark": "白板清洁基础", "status": "评测完成", "at": "2026-06-17", "ckpt_id": "9002", "success_rate": 0.889},
    {"id": "t9", "task_no": 1009, "name": "白板清洁基础能力评测_v5ctrl_ckpt45k",
     "benchmark": "白板清洁基础", "status": "评测完成", "at": "2026-06-18", "ckpt_id": "9003", "success_rate": 0.842},
    {"id": "t10", "task_no": 1010, "name": "桌面整理综合评测_joint_ckpt35k",
     "benchmark": "桌面整理综合", "status": "评测完成", "at": "2026-06-19", "ckpt_id": "9004", "success_rate": 0.828},
    {"id": "t11", "task_no": 1011, "name": "桌面清洁基准评测_baseline_ckpt30k",
     "benchmark": "桌面清洁基准", "status": "评测完成", "at": "2026-06-20", "ckpt_id": "9005", "success_rate": 0.781},
]

DEPLOYS = [
    {"id": "dp_801", "model": "spirit-v1.7-whiteboard-base", "version": "v1.7.0",
     "targets": ["moz1-002", "moz1-003", "moz1-005"],
     "status": "deployed", "progress": {"success": 3, "failed": 0, "running": 0},
     "trigger": "手动部署", "at": "2026-06-15 14:00", "operator": "joanna.qiao"},
    {"id": "dp_802", "model": "spirit-v1.6-whiteboard-baseline", "version": "v1.6.0",
     "targets": ["moz1-001"],
     "status": "deployed", "progress": {"success": 1, "failed": 0, "running": 0},
     "trigger": "TEST 任务", "at": "2026-06-13 10:00", "operator": "joanna.qiao"},
    {"id": "dp_803", "model": "spirit-v1.7-whiteboard-base", "version": "v1.7.1",
     "targets": ["moz1-003", "moz1-004", "moz1-005", "moz1-006", "moz1-007", "moz1-008"],
     "status": "in_progress", "progress": {"success": 3, "failed": 1, "running": 2},
     "trigger": "DAgger 任务", "at": "—", "operator": "Lance Li"},
]

MODELS = [
    {"id": "md_901", "name": "spirit-v1.7-whiteboard-base", "version": "v1.7.0",
     "base": "Spirit v1.7", "from_exp": "exp_601", "from_dataset": "clean_whiteboard_v4",
     "owner": "joanna.qiao", "created": "2026-06-15 11:00", "deployed_to": ["moz1-002"]},
    {"id": "md_902", "name": "spirit-v1.6-whiteboard-baseline", "version": "v1.6.0",
     "base": "Spirit v1.6", "from_exp": "exp_605", "from_dataset": "clean_whiteboard_v4",
     "owner": "joanna.qiao", "created": "2026-06-14 09:00", "deployed_to": ["moz1-001"]},
    {"id": "md_903", "name": "spirit-v1.7-whiteboard-base", "version": "v1.7.1",
     "base": "Spirit v1.7", "from_exp": "exp_604", "from_dataset": "clean_whiteboard_v4",
     "owner": "joanna.qiao", "created": "2026-06-16 23:30", "deployed_to": []},
    {"id": "md_904", "name": "spirit-v1.7-desk-sft", "version": "v0.1.0",
     "base": "Spirit v1.7-SFT", "from_exp": "exp_602", "from_dataset": "tidy_desk_v2",
     "owner": "Lance Li", "created": "2026-06-16 18:30", "deployed_to": []},
]

# ── 训练 · Checkpoint ──

CHECKPOINTS = [
    # ── DEMO 演示链路 Checkpoint（勿删；名称末尾数字为 step）──
    {"id": "9001", "name": "20260617_clean_whiteboard_v5_main_40000",
     "status": "cached", "owner": "joanna.qiao", "created": "2026-06-17 12:00:00", "exp_id": "DEMO_EXP_9001",
     "parent_checkpoint_id": "7916", "parent_type": "finetune"},
    {"id": "9002", "name": "20260617_clean_whiteboard_v5_main_50000",
     "status": "cached", "owner": "joanna.qiao", "created": "2026-06-17 18:00:00", "exp_id": "DEMO_EXP_9001",
     "parent_checkpoint_id": "9001", "parent_type": "finetune"},
    {"id": "9003", "name": "20260618_clean_whiteboard_v5_ctrl_45000",
     "status": "cached", "owner": "Lance Li", "created": "2026-06-18 20:00:00", "exp_id": "DEMO_EXP_9002",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "9004", "name": "20260618_tidy_desk_joint_train_35000",
     "status": "cached", "owner": "Lance Li", "created": "2026-06-18 23:00:00", "exp_id": "DEMO_EXP_9003",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "9005", "name": "20260620_clean_table_baseline_30000",
     "status": "cached", "owner": "Min Chen", "created": "2026-06-20 16:00:00", "exp_id": "DEMO_EXP_9004",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "7916", "name": "20260613_HouseHold_stop_32_40000",
     "status": "cached", "owner": "—", "created": "2026-06-13 00:00:02", "exp_id": "exp_7916",
     "parent_checkpoint_id": "7500", "parent_type": "dagger"},
    {"id": "7757", "name": "20260604_opd_exp1_sft_taskA_gpu8_50000",
     "status": "not_cached", "owner": "—", "created": "2026-06-12 19:26:39", "exp_id": "exp_7757",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "7560", "name": "20260609_opd_exp5a_single_wobcloss_taskAB_gpu8_50000",
     "status": "cached", "owner": "—", "created": "2026-06-13 05:05:41", "exp_id": "exp_7560",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "7500", "name": "20260610_clean_whiteboard_v4_baseline",
     "status": "cached", "owner": "joanna.qiao", "created": "2026-06-11 10:00:00", "exp_id": "exp_7560",
     "parent_checkpoint_id": "7285", "parent_type": "finetune"},
    {"id": "7466", "name": "20260610_HouseHold_stop_32_40000",
     "status": "merge_failed", "owner": "—", "created": "2026-06-12 17:18:42", "exp_id": "exp_7539",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "7374", "name": "20260518_HouseHold_stop_24_50000",
     "status": "cached", "owner": "Lance Li", "created": "2026-06-11 19:30:46", "exp_id": "exp_7374",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "7325", "name": "20260518_HouseHold_stop_24_40000",
     "status": "cached", "owner": "Lance Li", "created": "2026-06-11 03:42:38", "exp_id": "exp_7325",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "7285", "name": "20260608_opd_exp4_cascade_taskAB_gpu8_50000",
     "status": "cached", "owner": "—", "created": "2026-06-10 15:08:00", "exp_id": "exp_7285",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "6873", "name": "catl-ckpt-0608",
     "status": "cached", "owner": "Liquan Zheng", "created": "2026-06-08 18:12:22", "exp_id": "exp_6873",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "6869", "name": "catl-liquanzheng-upload",
     "status": "not_cached", "owner": "Liquan Zheng", "created": "2026-06-08 17:26:35", "exp_id": "exp_6869",
     "parent_checkpoint_id": None, "parent_type": None},
    {"id": "7467", "name": "20260615_pi05_oldft_sortpill_newobs_centercrop_30000",
     "status": "cached", "owner": "—", "created": "2026-06-15 22:10:00", "exp_id": "exp_7466",
     "parent_checkpoint_id": None, "parent_type": None},
]

# ── 部署 · 模型转换 / 推理服务 ──

CONVERT_JOBS = [
    {"id": "cv_a01", "source": "spirit-v1.7-whiteboard-base", "version": "v1.7.0",
     "target": "tensorrt", "quant": "fp16", "size_mb": 1080, "status": "done",
     "owner": "joanna.qiao", "at": "2026-06-15 13:45"},
    {"id": "cv_a02", "source": "spirit-v1.7-whiteboard-base", "version": "v1.7.1",
     "target": "tensorrt", "quant": "fp16", "size_mb": 1085, "status": "done",
     "owner": "joanna.qiao", "at": "2026-06-17 00:15"},
    {"id": "cv_b01", "source": "spirit-v1.6-whiteboard-baseline", "version": "v1.6.0",
     "target": "tensorrt", "quant": "fp16", "size_mb": 980, "status": "done",
     "owner": "joanna.qiao", "at": "2026-06-14 09:30"},
    {"id": "cv_c01", "source": "spirit-v1.7-desk-sft", "version": "v0.1.0",
     "target": "onnx", "quant": "fp16", "size_mb": 1100, "status": "running",
     "owner": "Lance Li", "at": "2026-06-17 19:00"},
]

INFERENCE_SVCS = [
    {"id": "svc_a01", "device": "moz1-001", "model": "spirit-v1.6-whiteboard-baseline",
     "version": "v1.6.0", "format": "tensorrt fp16", "status": "online",
     "p95_ms": 42, "rps": 18, "since": "2026-06-13 10:00"},
    {"id": "svc_a02", "device": "moz1-002", "model": "spirit-v1.7-whiteboard-base",
     "version": "v1.7.0", "format": "tensorrt fp16", "status": "online",
     "p95_ms": 38, "rps": 22, "since": "2026-06-15 14:00"},
    {"id": "svc_a03", "device": "moz1-003", "model": "spirit-v1.5",
     "version": "v1.5.2", "format": "onnx", "status": "online",
     "p95_ms": 56, "rps": 0, "since": "2026-06-12 09:00"},
]

# ── 评测 · Benchmark ──

BENCHMARKS = [
    {"id": "bm_001", "name": "clean_whiteboard_eval_v1", "source": "擦白板 · 评测留出",
     "episodes": 12, "metrics": "成功率 · MSE", "used_by": 3,
     "owner": "joanna.qiao", "created": "2026-06-14 11:00"},
    {"id": "bm_002", "name": "tidy_desk_val_split", "source": "整理桌面 · val split",
     "episodes": 12, "metrics": "成功率", "used_by": 1,
     "owner": "Lance Li", "created": "2026-06-09 17:30"},
]

# ── 设备 ──

DEVICES = [
    {"id": "moz1-001", "name": "新感知 Y18", "type": "moz1", "status": "in_use",
     "location": "实验室 东区", "current_user": "Lance Li", "model": "spirit-v1.6 / v1.6.0",
     "last_seen": "now",
     "sw_dep": "Ubuntu 22.04 · ROS2 Humble · spirit-runtime ≥1.5",
     "hw_dep": "6-DOF 机械臂 · RealSense D455 · Jetson Orin"},
    {"id": "moz1-002", "name": "旧感知 Y36", "type": "moz1", "status": "in_use",
     "location": "实验室 西区", "current_user": "joanna.qiao", "model": "spirit-v1.7 / v1.7.0",
     "last_seen": "now",
     "sw_dep": "Ubuntu 22.04 · ROS2 Humble · spirit-runtime ≥1.7",
     "hw_dep": "6-DOF 机械臂 · RealSense D455 · Jetson Orin"},
    {"id": "moz1-003", "name": "新感知 Y22", "type": "moz1", "status": "online",
     "location": "二楼 工位 A", "current_user": "—", "model": "spirit-v1.6 / v1.5.2",
     "last_seen": "now",
     "sw_dep": "Ubuntu 22.04 · ROS2 Humble · spirit-runtime 1.5",
     "hw_dep": "6-DOF 机械臂 · RealSense D455 · Jetson Orin"},
    {"id": "moz2-001", "name": "双臂 M12", "type": "moz2", "status": "in_use",
     "location": "一楼 测试区", "current_user": "Min Chen", "model": "—",
     "last_seen": "now",
     "sw_dep": "Ubuntu 22.04 · ROS2 Humble · mobi-runtime ≥2.0",
     "hw_dep": "双臂 7-DOF · 双目 D455 · Jetson Orin NX"},
    {"id": "moz2-002", "name": "备用本体 R08", "type": "moz2", "status": "offline",
     "location": "一楼 备用", "current_user": "—", "model": "—",
     "last_seen": "2026-06-15 18:32",
     "sw_dep": "Ubuntu 22.04 · ROS2 Humble · mobi-runtime 2.0",
     "hw_dep": "双臂 7-DOF · 双目 D455 · Jetson Orin NX"},
]

BOOKINGS = [
    {"id": "bk_a01", "device": "moz1-002", "user": "joanna.qiao", "purpose": "真机评测",
     "start": "2026-06-17 14:00", "end": "2026-06-17 18:00", "status": "approved"},
    {"id": "bk_a02", "device": "moz1-003", "user": "Lance Li", "purpose": "真机评测",
     "start": "2026-06-17 19:00", "end": "2026-06-17 22:00", "status": "approved"},
    {"id": "bk_a03", "device": "moz1-001", "user": "Wei Zhang", "purpose": "采集",
     "start": "2026-06-18 09:00", "end": "2026-06-18 17:00", "status": "approved"},
    {"id": "bk_a04", "device": "moz1-002", "user": "Min Chen", "purpose": "真机评测",
     "start": "2026-06-18 14:00", "end": "2026-06-18 16:00", "status": "pending"},
    {"id": "bk_a05", "device": "moz2-001", "user": "Min Chen", "purpose": "采集",
     "start": "2026-06-17 10:00", "end": "2026-06-17 16:00", "status": "approved"},
]


# ════════════════════════════════════════════════════════════════
# Section 2: Platform Config (定义 4 个平台的元信息 + 左侧栏)
# ════════════════════════════════════════════════════════════════

PLATFORMS = {
    "data": {
        "name": "数据平台",
        "short": "数",
        "color": "data",
        "tagline": "采集 → 质检 → 标注 → 数据集",
        "home": "/data",
        "nav": [
            ("概览", [
                ("/data", "快速入门", "&#9728;", "新增"),
            ]),
            ("管理", [
                ("/data/collect", "任务管理", "&#9776;", "优化"),
                ("/data/recordings", "数据管理", "&#9783;", "优化"),
                ("/data/dashboard", "分析看板", "&#9636;", "不对外"),
            ]),
            ("工作台", [
                ("/data/workbench", "工作台", "&#9881;", "优化"),
            ]),
            ("工作流", [
                ("/data/operators", "算子管理", "&#9881;", "不对外"),
                ("/data/pipelines", "工作流管理", "&#9783;", "不对外"),
                ("/data/runs", "执行记录", "&#9654;", "不对外"),
            ]),
            ("模块配置", [
                ("/data/instructions", "采集指令", "&#9881;", "不对外"),
                ("/data/rules", "规则管理", "&#9745;", "新增"),
            ]),
            ("公共配置", [
                ("/data/scenes",  "场景管理",   "&#9711;", "新增"),
                ("/data/prompts", "提示词管理", "&#9998;", "优化"),
                ("/data/tags",    "标签管理",   "&#9873;", "优化"),
            ]),
        ],
    },
    "model": {
        "name": "模型平台",
        "short": "模",
        "color": "model",
        "tagline": "数据 → 训练 → 部署 → 评测",
        "home": "/model",
        "nav": [
            ("概览", [
                ("/model", "快速入门", "&#9728;", "新增"),
            ]),
            ("数据", [
                ("/model/data/query", "数据查询", "&#9906;", "优化"),
                ("/model/data/datasets", "数据集", "&#9776;", "优化"),
                ("/model/data/raw", "原始数据", "&#9783;", "新增"),
            ]),
            ("训练", [
                ("/model/experiments", "训练任务", "&#9881;", "优化"),
            ]),
            ("部署", [
                ("/model/checkpoints", "Checkpoint", "&#9783;", "优化"),
                ("/model/deploy", "部署任务", "&#9654;", "新增"),
            ]),
            ("评测", [
                ("/model/eval/tasks",        "评测任务", "&#9881;", "待定"),
                ("/model/eval/eval-records", "评测结果", "&#9776;", "待定"),
                ("/model/eval/evaluate2",    "工作台",   "&#9878;", "待定"),
            ]),
            ("公共配置", [
                ("/model/eval/benchmarks",   "Benchmark 管理", "&#9776;", "优化"),
                ("/model/eval/scenes",       "场景管理",     "&#9711;", "新增"),
                ("/model/eval/prompts",      "提示词管理",   "&#9998;", "优化"),
                ("/model/eval/tags",         "标签管理",     "&#9873;", "优化"),
            ]),
        ],
    },
    "app": {
        "name": "应用编排平台",
        "short": "应",
        "color": "app",
        "tagline": "模型服务 · 编排 · 资产",
        "home": "/app",
        "nav": [
            ("概览", [
                ("/app", "快速入门", "&#9728;", "新增"),
            ]),
            ("模型服务", [
                ("/app/services", "模型服务", "&#9728;", "新增"),
            ]),
            ("生态市场", [
                ("/app/market/demos",  "demo 市场",   "&#9776;", "新增"),
                ("/app/market/skills", "skills 市场", "&#9776;", "新增"),
            ]),
            ("应用编排", [
                ("/app/orchestrate/workflow", "workflow", "&#9783;", "新增"),
                ("/app/orchestrate/agent",    "agent",    "&#9881;", "新增"),
            ]),
            ("资产管理", [
                ("/app/assets/prompts",   "提示词",   "&#9998;", "新增"),
                ("/app/assets/knowledge", "知识库",   "&#9783;", "新增"),
            ]),
        ],
    },
    "device": {
        "name": "设备管理平台",
        "short": "设",
        "color": "device",
        "tagline": "设备 · 监测 · OTA",
        "home": "/device",
        "nav": [
            ("设备", [
                ("/device/devices", "设备管理", "&#9776;", "优化"),
                ("/device/booking",  "设备预约", "&#9745;", "不对外"),
            ]),
            ("监测", [
                ("/device/monitor/run",       "设备运行监测", "&#9728;", "新增"),
                ("/device/monitor/inference", "模型推理监测", "&#9881;", "新增"),
            ]),
            ("OTA", [
                ("/device/ota", "OTA", "&#9783;", "优化"),
            ]),
        ],
    },
}

# 设备型号选择下拉 (仅在 module=="device" 时显示在 sider 平台切换器下方)
DEVICE_MODELS = ["Moz 墨子", "Mobi 莫比", "uDAS 1.0", "uDAS 2.0"]

# 租户管理: 独立 module, 不出现在平台切换下拉里 (顶导单独入口进入)
PLATFORMS["tenant"] = {
    "name": "租户管理",
    "short": "管",
    "color": "tenant",
    "tagline": "租户 · 人员 · 权限 · 资源",
    "home": "/tenant",
    "nav": [
        ("管理", [
            ("/tenant/members",   "人员管理", "&#9786;"),
            ("/tenant/roles",     "权限管理", "&#9919;"),
            ("/tenant/resources", "资源管理", "&#9784;"),
            ("/tenant/queues",    "队列管理", "&#9783;"),
        ]),
    ],
}


# ── 平台线形图标（统一用主色 stroke）──
ICON_DATA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5.5" rx="7" ry="2.5"/><path d="M5 5.5v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6"/><path d="M5 11.5v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6"/></svg>'
ICON_MODEL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="5" cy="6" r="1.8"/><circle cx="5" cy="18" r="1.8"/><circle cx="12" cy="12" r="1.8"/><circle cx="19" cy="6" r="1.8"/><circle cx="19" cy="18" r="1.8"/><path d="M6.7 7L10.3 10.7M6.7 17L10.3 13.3M13.7 10.7L17.3 7M13.7 13.3L17.3 17"/></svg>'
ICON_DEVICE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="6" width="12" height="12" rx="1.5"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M10 6V3M14 6V3M10 21v-3M14 21v-3M21 10h-3M21 14h-3M6 10H3M6 14H3"/></svg>'
ICON_ASSET = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="6" r="2.2"/><circle cx="12" cy="12" r="2.2"/><circle cx="19" cy="18" r="2.2"/><path d="M6.5 7.5L10.5 10.5M13.5 13.5L17.5 16.5"/></svg>'
ICON_APP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="6" height="4" rx="1"/><rect x="3" y="16" width="6" height="4" rx="1"/><rect x="15" y="10" width="6" height="4" rx="1"/><path d="M9 6 H12 V12 H15"/><path d="M9 18 H12 V12 H15"/></svg>'
ICON_TENANT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3.2"/><path d="M19.4 15a1.6 1.6 0 0 0 .32 1.76l.06.06a1.94 1.94 0 1 1-2.74 2.74l-.06-.06a1.6 1.6 0 0 0-1.76-.32 1.6 1.6 0 0 0-.97 1.46V21a1.94 1.94 0 1 1-3.88 0v-.1a1.6 1.6 0 0 0-1.05-1.46 1.6 1.6 0 0 0-1.76.32l-.06.06a1.94 1.94 0 1 1-2.74-2.74l.06-.06a1.6 1.6 0 0 0 .32-1.76 1.6 1.6 0 0 0-1.46-.97H3a1.94 1.94 0 1 1 0-3.88h.1a1.6 1.6 0 0 0 1.46-1.05 1.6 1.6 0 0 0-.32-1.76l-.06-.06a1.94 1.94 0 1 1 2.74-2.74l.06.06a1.6 1.6 0 0 0 1.76.32H9a1.6 1.6 0 0 0 .97-1.46V3a1.94 1.94 0 1 1 3.88 0v.1a1.6 1.6 0 0 0 .97 1.46 1.6 1.6 0 0 0 1.76-.32l.06-.06a1.94 1.94 0 1 1 2.74 2.74l-.06.06a1.6 1.6 0 0 0-.32 1.76V9a1.6 1.6 0 0 0 1.46.97H21a1.94 1.94 0 1 1 0 3.88h-.1a1.6 1.6 0 0 0-1.46.97z"/></svg>'

PLATFORM_ICONS = {"data": ICON_DATA, "model": ICON_MODEL, "app": ICON_APP, "device": ICON_DEVICE, "tenant": ICON_TENANT}
PLATFORM_ORDER = [("data", "数据平台"), ("model", "模型平台"), ("app", "应用编排平台"), ("device", "设备管理平台")]


# ════════════════════════════════════════════════════════════════
# Section 3: BASE CSS + Template
# ════════════════════════════════════════════════════════════════

BASE_CSS = """
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif; background:#f5f7fa; color:rgba(0,0,0,0.85); }
.ant-btn,.ant-input,.ant-select-selector,.ant-card,.ant-tag,.ant-alert,.ant-table-wrapper { border-radius:8px !important; }
a { color:#149DAA; text-decoration:none; } a:hover { color:#0F8190; }

/* ── Top nav (52px, dark navy) ── */
.top-nav { position:fixed; top:0; left:0; right:0; height:52px; background:#001529; border-bottom:none; display:flex; align-items:center; padding:0 16px; z-index:200; }
.tn-brand { display:flex; align-items:center; gap:8px; padding-left:6px; }
.tn-brand .brand-name { font-size:17px; font-weight:700; color:#fff; letter-spacing:0.4px; }
.tn-overview { margin-left:20px; padding:4px 10px; font-size:13.5px; color:rgba(255,255,255,0.70); border-radius:6px; display:inline-flex; align-items:center; gap:7px; cursor:pointer; transition:background 0.15s, color 0.15s; letter-spacing:0.2px; }
.tn-overview:hover { background:rgba(255,255,255,0.06); color:#fff; }
.tn-overview.active { color:#fff; background:rgba(255,255,255,0.10); font-weight:500; }
.tn-overview.active .ic { color:#5DE5EC; }
.tn-overview .ic { display:inline-flex; align-items:center; justify-content:center; width:15px; height:15px; color:rgba(255,255,255,0.55); }
.tn-overview .ic svg { width:15px; height:15px; }
.tn-mod-crumb { display:flex; align-items:center; gap:8px; margin-left:14px; font-size:14px; color:rgba(255,255,255,0.65); }
.tn-mod-crumb .sep { color:rgba(255,255,255,0.25); }
.tn-mod-crumb .cur { color:#fff; font-weight:500; }
.tn-right { display:flex; align-items:center; gap:16px; margin-left:auto; }
.tn-link { color:rgba(255,255,255,0.65); font-size:14px; cursor:pointer; }
.tn-link:hover { color:#fff; }
.tn-divider { width:1px; height:18px; background:rgba(255,255,255,0.14); margin:0 4px; flex:none; }
.tn-tenant-admin { display:inline-flex; align-items:center; gap:6px; padding:5px 9px; border-radius:6px; }
.tn-tenant-admin svg { color:rgba(255,255,255,0.65); }
.tn-tenant-admin:hover { background:rgba(255,255,255,0.06); color:#fff; }
.tn-tenant-admin:hover svg { color:#fff; }
.tn-pill { font-size:11px; color:rgba(255,255,255,0.85); background:transparent; border:1px solid rgba(255,255,255,0.25); padding:2px 12px; border-radius:11px; letter-spacing:0.4px; }
.brand-demo { font-size:10.5px; font-weight:500; color:rgba(255,255,255,0.85); background:rgba(20,157,170,0.30); border:1px solid rgba(93,229,236,0.50); padding:1px 7px; border-radius:8px; letter-spacing:0.6px; text-transform:uppercase; margin-left:4px; }
.tn-tenant { display:flex; align-items:center; gap:8px; cursor:pointer; padding:4px 6px 4px 2px; border-radius:6px; user-select:none; position:relative; background:transparent; border:none; transition:background 0.15s; }
.tn-tenant:hover { background:rgba(255,255,255,0.06); }
.tn-tenant.open { background:rgba(255,255,255,0.08); }
.tn-tenant .tt-av { width:22px; height:22px; border-radius:50%; background:#149DAA; color:#fff; font-size:11.5px; font-weight:600; display:flex; align-items:center; justify-content:center; flex:none; }
.tn-tenant .tt-name { font-size:13.5px; color:#fff; font-weight:500; letter-spacing:0.2px; }
.tn-tenant .caret { font-size:9px; opacity:0.55; color:#fff; }
.tenant-pop { display:none; position:absolute; top:calc(100% + 6px); right:0; min-width:260px; background:#fff; border:1px solid #E0E4E7; border-radius:10px; box-shadow:0 12px 32px rgba(0,0,0,0.25); padding:6px; z-index:300; }
.tenant-pop.open { display:block; }
.tenant-pop .tp-section { font-size:11px; color:rgba(0,0,0,0.40); padding:8px 12px 4px; letter-spacing:0.5px; }
.tenant-pop .tp-divider { height:1px; background:#eef0f2; margin:6px 4px; }
.tenant-pop .tp-tenant { display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:6px; color:rgba(0,0,0,0.78); cursor:pointer; text-decoration:none; margin:1px 0; }
.tenant-pop .tp-tenant:hover { background:#EEF2F4; }
.tenant-pop .tp-tenant .tp-av { width:24px; height:24px; border-radius:50%; font-size:11px; font-weight:600; display:flex; align-items:center; justify-content:center; background:#e3e8eb; color:rgba(0,0,0,0.62); flex:none; }
.tenant-pop .tp-tenant.active { background:#D9EEF1; color:#0B6B78; font-weight:500; }
.tenant-pop .tp-tenant.active .tp-av { background:#149DAA; color:#fff; }
.tenant-pop .tp-tenant .tp-check { margin-left:auto; color:#149DAA; font-size:13px; display:none; }
.tenant-pop .tp-tenant.active .tp-check { display:inline; }
.tenant-pop .tp-item { display:flex; flex-direction:column; gap:2px; padding:9px 12px; border-radius:6px; color:rgba(0,0,0,0.78); cursor:pointer; text-decoration:none; }
.tenant-pop .tp-item:hover { background:#EEF2F4; color:#0B6B78; }
.tenant-pop .tp-item .tp-sub { font-size:11.5px; color:rgba(0,0,0,0.42); }
.tn-user { width:32px; height:32px; border-radius:50%; background:#149DAA; color:#fff; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:600; cursor:pointer; }

/* ── Layout root ── */
.q-layout { padding-top:52px; display:flex; min-height:100vh; background:#001529; }

/* ── Module sider (220px, dark navy) ── */
.q-sider { width:220px; min-width:220px; background:#001529; border-right:none; position:fixed; top:52px; left:0; bottom:0; overflow:hidden; display:flex; flex-direction:column; z-index:100; }
.smh-wrap { padding:14px; border-bottom:1px solid rgba(255,255,255,0.08); position:relative; flex:none; background:#001529; }
.smh { display:flex; align-items:center; gap:10px; padding:9px 12px; border:1px solid rgba(255,255,255,0.14); border-radius:8px; background:rgba(255,255,255,0.04); cursor:pointer; transition:all 0.15s; user-select:none; }
.smh:hover { border-color:#149DAA; background:rgba(255,255,255,0.08); }
.smh.open { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.28); background:rgba(255,255,255,0.08); }
.smh-icon { width:28px; height:28px; border-radius:6px; display:flex; align-items:center; justify-content:center; flex:none; background:rgba(20,157,170,0.20); color:#5DE5EC; }
.smh-icon svg { width:17px; height:17px; }
.smh-name { font-size:14px; font-weight:500; color:rgba(255,255,255,0.92); flex:1; min-width:0; }
.smh-caret { color:rgba(255,255,255,0.42); font-size:10px; transition:transform 0.2s; flex:none; }
.smh.open .smh-caret { transform:rotate(180deg); color:#5DE5EC; }
.smh-static { cursor:default; }
.smh-static:hover { border-color:rgba(255,255,255,0.14); background:rgba(255,255,255,0.04); }
.mod-switch { display:none; position:absolute; top:calc(100% - 4px); left:14px; right:14px; background:#fff; border:1px solid #E0E4E7; border-radius:8px; box-shadow:0 12px 32px rgba(0,0,0,0.45); padding:6px; z-index:300; }
.mod-switch.open { display:block; }
.ms-item { display:flex; align-items:center; gap:10px; padding:8px 10px; border-radius:6px; font-size:14px; color:rgba(0,0,0,0.78); cursor:pointer; text-decoration:none; margin:1px 0; }
.ms-item:hover { background:#EEF2F4; color:#0B6B78; }
.ms-item.active { background:#D9EEF1; color:#0B6B78; font-weight:500; }
.dev-wrap { padding:10px 14px 14px; border-bottom:1px solid rgba(255,255,255,0.08); position:relative; flex:none; background:#001529; }
.dev-wrap .smh-icon { background:rgba(255,255,255,0.08); color:rgba(255,255,255,0.85); font-size:12px; font-weight:600; }
.dev-wrap .dev-label { font-size:11px; color:rgba(255,255,255,0.40); letter-spacing:0.3px; margin-bottom:6px; }
.dev-switch { display:none; position:absolute; top:calc(100% - 4px); left:14px; right:14px; background:#fff; border:1px solid #E0E4E7; border-radius:8px; box-shadow:0 12px 32px rgba(0,0,0,0.45); padding:6px; z-index:300; }
.dev-switch.open { display:block; }
.ms-ic { width:26px; height:26px; border-radius:6px; display:flex; align-items:center; justify-content:center; flex:none; background:#D9EEF1; color:#0B6B78; }
.ms-ic svg { width:16px; height:16px; }
.sider-nav { flex:1; padding:10px 0 24px; overflow-y:auto; }
.sn-label { padding:14px 24px 4px; font-size:11px; color:rgba(255,255,255,0.38); text-transform:uppercase; letter-spacing:0.6px; font-weight:500; }
.sn-label:first-child { padding-top:6px; }
.sn-item { display:flex; align-items:center; gap:10px; padding:9px 24px; color:rgba(255,255,255,0.68); font-size:14px; cursor:pointer; margin:1px 8px; border-radius:6px; }
.sn-item:hover { color:#fff; background:rgba(255,255,255,0.06); }
.sn-item.active { color:#fff; background:#149DAA; font-weight:600; }
.sn-item .ic { width:14px; text-align:center; font-size:12px; color:rgba(255,255,255,0.48); }
.sn-item.active .ic { color:#fff; }
.sn-tag { margin-left:auto; font-size:10px; padding:1px 7px; border-radius:9px; background:rgba(255,255,255,0.10); color:rgba(255,255,255,0.55); font-weight:400; line-height:1.5; letter-spacing:0.2px; flex:none; }
.sn-tag.t-new { background:rgba(82,196,116,0.20); color:rgba(160,230,176,0.95); }
.sn-tag.t-opt { background:rgba(70,160,235,0.18); color:rgba(150,205,250,0.95); }
.sn-tag.t-tbd { background:rgba(245,180,70,0.20); color:rgba(255,215,150,0.95); }
.sn-item.active .sn-tag { background:rgba(255,255,255,0.22); color:rgba(255,255,255,0.85); }
.sn-item.active .sn-tag.t-new { background:rgba(82,196,116,0.42); color:#fff; }
.sn-item.active .sn-tag.t-opt { background:rgba(70,160,235,0.42); color:#fff; }
.sn-item.active .sn-tag.t-tbd { background:rgba(245,180,70,0.42); color:#fff; }

/* ── Main area ── */
.q-main { margin-left:220px; flex:1; min-width:0; min-height:calc(100vh - 52px); background:#f5f7fa; border-top-left-radius:10px; }
.q-layout.portal-mode .q-main { margin-left:0; border-top-left-radius:0; }
.q-content { padding:28px 28px 32px; }
.portal-mode .q-content { padding:32px 40px; max-width:1380px; margin:0 auto; }

/* ── Portal: welcome + cards ── */
.pw { background:#fff; border-radius:12px; padding:28px 32px; margin-bottom:20px; border:1px solid #f0f0f0; display:flex; align-items:center; justify-content:space-between; gap:32px; flex-wrap:wrap; }
.pw-l { flex:1; min-width:280px; }
.pw-l h1 { margin:0 0 6px; font-size:22px; font-weight:600; color:rgba(0,0,0,0.85); }
.pw-l p { margin:0; font-size:13px; color:rgba(0,0,0,0.55); line-height:1.6; }
.pw-acc { display:flex; align-items:center; gap:14px; }
.pw-acc .av { width:48px; height:48px; border-radius:50%; background:linear-gradient(135deg,#149DAA,#5DE5EC); color:#fff; font-size:18px; font-weight:600; display:flex; align-items:center; justify-content:center; }
.pw-acc .info { display:flex; flex-direction:column; gap:3px; }
.pw-acc .info .nm { font-size:14px; font-weight:600; color:rgba(0,0,0,0.85); display:flex; align-items:center; gap:8px; }
.pw-acc .info .nm .role { font-size:11px; color:#149DAA; background:#DEF6F9; border:1px solid #7BD8DF; padding:1px 6px; border-radius:8px; font-weight:400; }
.pw-acc .info .id { font-size:12px; color:rgba(0,0,0,0.45); font-family:'SF Mono',Menlo,monospace; }
.pw-stats { display:flex; gap:32px; padding-left:24px; border-left:1px solid #f0f0f0; }
.pw-st { text-align:center; }
.pw-st .v { font-size:24px; font-weight:600; color:rgba(0,0,0,0.85); line-height:1.1; }
.pw-st .l { font-size:12px; color:rgba(0,0,0,0.45); margin-top:3px; }

/* ── Portal: flywheel banner ── */
.pfw { background:linear-gradient(135deg,#149DAA 0%,#5DE5EC 100%); color:#fff; padding:18px 24px; border-radius:10px; margin-bottom:24px; display:flex; align-items:center; gap:18px; flex-wrap:wrap; }
.pfw-ttl { font-size:14px; font-weight:600; flex:none; }
.pfw-ttl .sub { font-weight:400; opacity:0.8; font-size:12.5px; margin-left:8px; }
.pfw-loop { flex:1; display:flex; align-items:center; flex-wrap:wrap; gap:0; min-width:300px; }
.pfw-step { padding:6px 12px; background:rgba(255,255,255,0.14); border-radius:5px; font-size:12.5px; }
.pfw-arr { padding:0 6px; opacity:0.65; font-size:13px; }
.pfw-link { color:#fff; opacity:0.85; font-size:12.5px; padding:5px 12px; border:1px solid rgba(255,255,255,0.35); border-radius:6px; }
.pfw-link:hover { opacity:1; background:rgba(255,255,255,0.12); color:#fff; }

/* ── Portal: section title ── */
.p-sec { font-size:16px; font-weight:600; color:rgba(0,0,0,0.85); margin:20px 0 14px; display:flex; align-items:center; gap:10px; }
.p-sec::before { content:''; display:inline-block; width:3px; height:14px; background:#149DAA; border-radius:2px; }

/* ── Portal: 平台入口 cards ── */
.p-mods { display:grid; grid-template-columns:repeat(2, 1fr); gap:16px; }
.mc { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:20px 22px 18px; cursor:pointer; transition:all 0.2s; display:flex; flex-direction:column; gap:14px; text-decoration:none; color:inherit; }
.mc:hover { border-color:#149DAA; box-shadow:0 4px 18px rgba(20,157,170,0.08); transform:translateY(-2px); color:inherit; }
.mc-hd { display:flex; align-items:center; gap:14px; }
.mc-ic { width:46px; height:46px; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600; font-size:18px; flex:none; }
.mc-ic.data { background:linear-gradient(135deg,#0F6E56,#1D9E75); }
.mc-ic.model { background:linear-gradient(135deg,#534AB7,#7F77DD); }
.mc-ic.app { background:linear-gradient(135deg,#1F6C90,#3A98C7); }
.mc-ic.device { background:linear-gradient(135deg,#993C1D,#D85A30); }
.mc-ic.asset { background:linear-gradient(135deg,#5F5E5A,#888780); }
.mc-t { flex:1; min-width:0; }
.mc-tn { font-size:16px; font-weight:600; color:rgba(0,0,0,0.85); margin-bottom:2px; }
.mc-tg { font-size:12.5px; color:rgba(0,0,0,0.5); }
.mc-ar { color:#149DAA; font-size:16px; }
.mc-st { display:flex; gap:24px; padding:10px 0 4px; border-top:1px solid #f5f5f5; }
.mc-stt { display:flex; flex-direction:column; }
.mc-stt .v { font-size:18px; font-weight:600; color:rgba(0,0,0,0.85); line-height:1.1; font-family:'SF Mono',Menlo,monospace; }
.mc-stt .l { font-size:11px; color:rgba(0,0,0,0.45); margin-top:3px; }
.mc-tags { display:flex; flex-wrap:wrap; gap:6px; }
.mc-tags span { font-size:11.5px; padding:2px 9px; background:#f5f7fa; color:rgba(0,0,0,0.6); border-radius:10px; border:1px solid #f0f0f0; }
.mc-tags span.k { background:#DEF6F9; color:#149DAA; border-color:#B5E5EA; }

/* ── Page title (inside module page) ── */
.page-title { font-size:20px; font-weight:600; color:rgba(0,0,0,0.85); margin:0 0 4px; }
.page-sub { font-size:13px; color:rgba(0,0,0,0.55); margin-bottom:20px; }
.page-sub .deferred { color:rgba(0,0,0,0.35); }
.welcome-card { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:24px 28px; margin-bottom:20px; }
.welcome-card h2 { margin:0 0 6px; font-size:20px; font-weight:600; color:rgba(0,0,0,0.85); }
.welcome-card p { margin:0; font-size:13px; color:rgba(0,0,0,0.55); line-height:1.7; }

/* ── Stat cards ── */
.stat-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:16px; margin-bottom:24px; }
.stat-card { background:#fff; border-radius:8px; padding:18px 22px; border:1px solid #f0f0f0; }
.stat-card .stat-label { font-size:13px; color:rgba(0,0,0,0.45); margin-bottom:4px; }
.stat-card .stat-value { font-size:28px; font-weight:600; color:rgba(0,0,0,0.85); }
.stat-card .stat-sub { font-size:12px; color:rgba(0,0,0,0.45); margin-top:4px; }
.stat-card .stat-sub .ok { color:#389e0d; } .stat-card .stat-sub .warn { color:#d48806; } .stat-card .stat-sub .err { color:#cf1322; }
.trend-up { color:#2e9e5b; font-weight:500; font-family:'SF Mono',Menlo,monospace; }
.trend-down { color:#d4504e; font-weight:500; font-family:'SF Mono',Menlo,monospace; }
.trend-flat { color:#8c8c8c; font-weight:500; font-family:'SF Mono',Menlo,monospace; }

/* ── Card ── */
.card { background:#fff; border-radius:8px; border:1px solid #f0f0f0; padding:20px 24px; margin-bottom:16px; }
.card h3 { font-size:16px; font-weight:500; margin:0 0 16px; color:rgba(0,0,0,0.85); }
.card h4 { font-size:14px; font-weight:500; margin:0 0 12px; color:rgba(0,0,0,0.85); }
.muted { color:rgba(0,0,0,0.45); font-size:13px; }

/* ── Module entry cards (used in 平台 overview) ── */
.mod-entries { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; margin-bottom:24px; }
.me { background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:16px 18px; cursor:pointer; transition:all 0.18s; display:block; text-decoration:none; color:inherit; }
.me:hover { border-color:#149DAA; box-shadow:0 2px 10px rgba(20,157,170,0.06); color:inherit; }
.me .me-no { font-size:11px; color:#149DAA; font-weight:600; letter-spacing:0.4px; }
.me .me-nm { font-size:15px; font-weight:600; color:rgba(0,0,0,0.85); margin-top:2px; margin-bottom:6px; }
.me .me-sub { font-size:12px; color:rgba(0,0,0,0.5); line-height:1.5; min-height:32px; }
.me .me-st { font-size:12px; color:#149DAA; margin-top:10px; font-family:'SF Mono',Menlo,monospace; }

/* ── Filter bar ── */
.filter-bar { display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; align-items:center; background:#fff; padding:14px 16px; border:1px solid #f0f0f0; border-radius:8px; }
.filter-bar input,.filter-bar select { padding:5px 12px; height:34px; border:1px solid #d9d9d9; border-radius:8px; font-size:14px; color:rgba(0,0,0,0.85); outline:none; background:#fff; }
.filter-bar input:focus,.filter-bar select:focus { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.12); }
.filter-bar .grow { flex:1; min-width:200px; }
.filter-bar .right { margin-left:auto; display:flex; gap:8px; }
.filter-actions { display:flex; gap:8px; align-items:center; }
.filter-bar.deploy-filters { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)) auto; gap:12px; align-items:start; overflow:visible; }
.remote-filter { position:relative; min-width:0; }
.remote-filter .rf-hidden { display:none; }
.rf-control { min-height:34px; box-sizing:border-box; border:1px solid #d9d9d9; border-radius:8px; background:#fff; padding:3px 8px; display:flex; align-items:center; gap:6px; flex-wrap:wrap; cursor:text; }
.rf-control:focus-within, .remote-filter.open .rf-control { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.12); }
.rf-control input { flex:1; min-width:82px; height:26px; padding:0 2px; border:0; box-shadow:none !important; outline:none; font-size:13.5px; }
.rf-chip { display:inline-flex; align-items:center; gap:5px; max-width:100%; height:24px; padding:0 8px; border:1px solid #dfe3e8; border-radius:5px; background:#f7f8fa; color:rgba(0,0,0,0.72); font-size:12.5px; }
.rf-chip span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:180px; }
.rf-chip i { font-style:normal; color:rgba(0,0,0,0.35); cursor:pointer; line-height:1; }
.rf-menu { display:none; position:absolute; z-index:120; left:0; right:0; top:calc(100% + 6px); max-height:220px; overflow-y:auto; padding:5px; border:1px solid #e5e7eb; border-radius:8px; background:#fff; box-shadow:0 8px 24px rgba(0,0,0,0.12); }
.remote-filter.open .rf-menu { display:block; }
.rf-option { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:8px 9px; border-radius:6px; color:rgba(0,0,0,0.72); font-size:13px; cursor:pointer; }
.rf-option:hover { background:#EBF8FA; }
.rf-option.on { background:#DEF6F9; color:#149DAA; }
.rf-option .rf-value { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.rf-option .rf-check { display:none; font-size:12px; color:#149DAA; }
.rf-option.on .rf-check { display:inline; }
@media (max-width: 1180px) { .filter-bar.deploy-filters { grid-template-columns:1fr; } .filter-bar.deploy-filters .filter-actions { justify-content:flex-end; } }
input::placeholder, textarea::placeholder { color:rgba(0,0,0,0.32); opacity:1; }
select.select-empty { color:rgba(0,0,0,0.32) !important; }
select option { color:rgba(0,0,0,0.85); }
select option:disabled { color:rgba(0,0,0,0.32); }

/* ── Buttons ── */
.btn { display:inline-flex; align-items:center; gap:6px; height:34px; padding:0 16px; border-radius:8px; font-size:14px; cursor:pointer; border:1px solid #d9d9d9; background:#fff; color:rgba(0,0,0,0.85); text-decoration:none; box-sizing:border-box; }
.btn:hover { border-color:#149DAA; color:#149DAA; }
.btn-secondary { background:#fff; border-color:#149DAA; color:#149DAA; }
.btn-secondary:hover { background:#EBF8FA; border-color:#0F8190; color:#0F8190; }
.btn-tertiary { background:#fff; border-color:#d9d9d9; color:rgba(0,0,0,0.85); }
.btn-tertiary:hover { border-color:#149DAA; color:#149DAA; background:#fff; }
.btn-primary { background:#149DAA; border-color:#149DAA; color:#fff; }
.btn-primary:hover { background:#0F8190; border-color:#0F8190; color:#fff; }
.btn-sm { height:28px; padding:0 12px; font-size:13px; }

/* ── Table ── */
.ant-table { width:100%; border-collapse:collapse; font-size:14px; background:#fff; }
.ant-table thead th { background:#fafafa; padding:11px 16px; font-weight:500; color:rgba(0,0,0,0.85); text-align:left; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.ant-table tbody td { padding:11px 16px; border-bottom:1px solid #f0f0f0; color:rgba(0,0,0,0.65); vertical-align:middle; }
.ant-table tbody tr:hover td { background:#fafafa; }
.actions-cell { white-space:nowrap; position:relative; overflow:visible; }
.actions-cell a, .actions-cell .tbtn, .action-link { display:inline-flex; align-items:center; height:24px; padding:0; border:0; background:transparent; color:#149DAA; font-size:13px; line-height:24px; text-decoration:none; cursor:pointer; margin-right:14px; border-radius:0; vertical-align:middle; }
.actions-cell a:hover, .actions-cell .tbtn:hover, .action-link:hover { color:#0F8190; background:transparent; border:0; }
.actions-cell a:last-child, .actions-cell .tbtn:last-child, .action-link:last-child { margin-right:0; }
.actions-cell .action-disabled { color:rgba(0,0,0,0.28); cursor:not-allowed; pointer-events:none; }
.action-more { position:relative; display:inline-flex; align-items:center; height:24px; vertical-align:middle; }
.action-more-trigger { display:inline-flex; align-items:center; gap:3px; height:24px; color:#149DAA; font-size:13px; line-height:24px; cursor:pointer; user-select:none; }
.action-more-trigger:hover { color:#0F8190; }
.action-more-trigger .caret { font-size:10px; transition:transform 0.2s; }
.action-more:hover .action-more-trigger .caret { transform:rotate(180deg); }
/* 透明桥接区域，避免 trigger 与菜单间隙导致 hover 中断，无法点击菜单项 */
.action-more:hover::after { content:''; position:absolute; top:100%; right:0; width:100%; height:10px; }
.action-menu { display:none; position:absolute; right:0; top:calc(100% + 8px); z-index:160; min-width:100%; padding:4px; background:#fff; border:1px solid #eef0f2; border-radius:8px; box-shadow:0 6px 20px rgba(0,0,0,0.10); animation:actionMenuIn 0.15s ease; }
.action-more:hover .action-menu { display:block; }
.action-menu a, .action-menu span { display:flex; align-items:center; justify-content:center; height:auto; padding:7px 10px; margin:0; color:rgba(0,0,0,0.72); font-size:13px; line-height:1.4; white-space:nowrap; text-decoration:none; border-radius:6px; transition:all 0.15s; }
.action-menu a:hover { background:rgba(20,157,170,0.08); color:#149DAA; }
.action-menu .disabled { color:rgba(0,0,0,0.28); cursor:not-allowed; }
@keyframes actionMenuIn { from { opacity:0; transform:translateY(-4px); } to { opacity:1; transform:translateY(0); } }
.mono { font-family:'SF Mono',Menlo,monospace; font-size:12.5px; color:rgba(0,0,0,0.55); }
.table-wrap { background:#fff; border:1px solid #f0f0f0; border-radius:8px; overflow:visible; }
.table-wrap.deploy-table-wrap { overflow:visible; }
.ckpt-table { table-layout:fixed; }
.ckpt-name-cell { display:block; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#149DAA; text-decoration:none; }
.ckpt-name-cell:hover { color:#0F8190; }
.ckpt-status-filter { position:relative; display:inline-flex; align-items:center; height:26px; }
.ckpt-status-trigger { display:inline-flex; align-items:center; gap:6px; border:0; background:transparent; padding:0; color:rgba(0,0,0,0.85); font:inherit; font-weight:600; cursor:pointer; }
.ckpt-status-trigger .caret { font-size:15px; line-height:1; transform:translateY(-1px); color:rgba(0,0,0,0.78); }
.ckpt-status-menu { display:none; position:absolute; top:calc(100% + 9px); left:50px; z-index:180; min-width:128px; padding:6px 0; border:1px solid #e5e7eb; border-radius:6px; background:#fff; box-shadow:0 12px 28px rgba(0,0,0,0.14); overflow:hidden; }
.ckpt-status-filter.open .ckpt-status-menu { display:block; }
.ckpt-status-option { display:block; width:100%; height:34px; padding:0 14px; border:0; background:#fff; color:rgba(0,0,0,0.88); text-align:left; font-size:14px; line-height:34px; cursor:pointer; white-space:nowrap; }
.ckpt-status-option:hover { background:#f5f7fa; }
.ckpt-status-option.active { background:#238da3; color:#fff; }
.status-with-log { display:inline-flex; align-items:center; gap:6px; white-space:nowrap; }
.status-log-icon { width:18px; height:18px; padding:0; border:1px solid #f3d6d5; border-radius:50%; background:#fff; color:#d4504e; font-size:12px; line-height:16px; cursor:pointer; display:inline-flex; align-items:center; justify-content:center; }
.status-log-icon:hover { border-color:#d4504e; background:#fdf3f3; }
.ckpt-log-pre { margin:0; padding:12px 14px; border:1px solid #e5e7eb; border-radius:6px; background:#fafbfc; color:rgba(0,0,0,0.78); font-family:'SF Mono',Menlo,Consolas,monospace; font-size:12.5px; line-height:1.65; white-space:pre-wrap; max-height:260px; overflow:auto; }

/* ── Tags / status ── */
.tag { display:inline-block; padding:1px 8px; border-radius:4px; font-size:12px; line-height:20px; border:1px solid transparent; }
.tag-blue { color:#149DAA; background:#DEF6F9; border-color:#7BD8DF; }
.tag-gray { color:#8c8c8c; background:#f5f5f5; border-color:#e8e8e8; }
.tag-green { color:#2e9e5b; background:#f0faf4; border-color:#cdeedb; }
.tag-red { color:#d4504e; background:#fdf3f3; border-color:#f3d6d5; }
.tag-purple { color:#722ed1; background:#f9f0ff; border-color:#d3adf7; }
.tag-orange { color:#ad6800; background:#fffbe6; border-color:#ffe58f; }
.tag-coral { color:#993c1d; background:#fef0eb; border-color:#f0997b; }
.tag-teal { color:#0f6e56; background:#e1f5ee; border-color:#5dcaa5; }
.qa { display:inline-flex; align-items:center; gap:5px; font-size:13px; }
.qa::before { content:''; width:7px; height:7px; border-radius:50%; }
.qa-pass { color:#389e0d; } .qa-pass::before { background:#52c41a; }
.qa-warn { color:#d48806; } .qa-warn::before { background:#faad14; }
.qa-fail { color:#cf1322; } .qa-fail::before { background:#ff4d4f; }
.qa-pend { color:#8c8c8c; } .qa-pend::before { background:#bfbfbf; }

/* ── Progress ── */
.bar { display:flex; align-items:center; gap:10px; min-width:140px; }
.bar .track { flex:1; height:6px; background:#eef2f4; border-radius:3px; overflow:hidden; min-width:80px; }
.bar .fill { height:100%; background:linear-gradient(90deg,#3aa6c4,#149DAA); border-radius:3px; }
.bar .pct { font-size:12px; color:rgba(0,0,0,0.55); font-family:'SF Mono',Menlo,monospace; min-width:40px; text-align:right; }
.bar.warn .fill { background:linear-gradient(90deg,#facc8c,#d48806); }
.bar.done .fill { background:linear-gradient(90deg,#73d896,#2e9e5b); }
.bar.fail .fill { background:linear-gradient(90deg,#f0a3a1,#cf1322); }

/* ── Toast ── */
.q-toast { position:fixed; top:24px; bottom:auto; left:50%; transform:translate(-50%,-8px); background:#fff; color:rgba(0,0,0,0.85); padding:8px 16px; border-radius:6px; font-size:13px; line-height:1.4; opacity:0; transition:opacity 0.2s, transform 0.2s; pointer-events:none; z-index:9999; border:1px solid #e5e7eb; box-shadow:0 4px 16px rgba(0,0,0,0.08); white-space:nowrap; max-width:none; min-width:0; border-left:3px solid #149DAA; }
.q-toast.show { opacity:1; transform:translate(-50%,0); }

/* ── Drawer ── */
.drawer-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:1500; display:none; }
.drawer-mask.active { display:block; }
.drawer { position:fixed; top:0; right:0; bottom:0; width:540px; background:#fff; z-index:1600; transform:translateX(100%); transition:transform 0.22s; display:flex; flex-direction:column; }
.drawer.active { transform:translateX(0); }
.drawer-head { padding:18px 24px; border-bottom:1px solid #f0f0f0; display:flex; justify-content:space-between; align-items:center; }
.drawer-head h3 { font-size:16px; margin:0; font-weight:500; }
.drawer-body { flex:1; overflow-y:auto; padding:20px 24px; }
.drawer-foot { padding:14px 24px; border-top:1px solid #f0f0f0; display:flex; justify-content:flex-end; gap:8px; }
.fg { display:flex; flex-direction:column; gap:6px; margin-bottom:14px; }
.fg label { font-size:13px; color:rgba(0,0,0,0.65); }
.fg input, .fg select, .fg textarea { padding:7px 12px; border:1px solid #d9d9d9; border-radius:8px; font-size:14px; outline:none; font-family:inherit; }
.fg input:focus, .fg select:focus, .fg textarea:focus { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.12); }
.dismiss { font-size:18px; color:rgba(0,0,0,0.45); cursor:pointer; line-height:1; }
.dismiss:hover { color:rgba(0,0,0,0.85); }

/* ── Modal ── */
.modal-mask { position:fixed; inset:0; z-index:1700; display:none; align-items:center; justify-content:center; background:rgba(0,0,0,0.42); }
.modal-mask.active { display:flex; }
.modal { width:480px; max-width:calc(100vw - 40px); background:#fff; border-radius:10px; box-shadow:0 16px 48px rgba(0,0,0,0.18); overflow:hidden; }
.modal-head { padding:18px 22px; border-bottom:1px solid #f0f0f0; display:flex; align-items:center; justify-content:space-between; }
.modal-head h3 { margin:0; font-size:16px; font-weight:500; color:rgba(0,0,0,0.86); }
.modal-body { padding:20px 22px; }
.modal-foot { padding:13px 22px; border-top:1px solid #f0f0f0; display:flex; justify-content:flex-end; gap:8px; }
.cache-state { display:flex; gap:12px; align-items:flex-start; }
.cache-hourglass { width:32px; height:32px; border-radius:50%; background:#DEF6F9; color:#149DAA; display:inline-flex; align-items:center; justify-content:center; font-size:18px; line-height:1; flex:none; }
.cache-state h4 { margin:1px 0 6px; font-size:15px; color:rgba(0,0,0,0.86); font-weight:500; }
.cache-state p { margin:0; font-size:13px; color:rgba(0,0,0,0.55); line-height:1.7; }

/* ── Lineage (asset page) ── */
.lin-pick { display:flex; gap:10px; align-items:center; margin-bottom:18px; }
.lin-pick select { padding:7px 14px; border:1px solid #d9d9d9; border-radius:8px; font-size:14px; outline:none; min-width:280px; }
.lin-flow { display:grid; grid-template-columns:1fr 1fr 1fr; gap:24px; align-items:center; background:#fff; padding:24px 18px; border:1px solid #f0f0f0; border-radius:8px; }
.lin-col { display:flex; flex-direction:column; gap:8px; position:relative; }
.lin-col h4 { font-size:12px; color:rgba(0,0,0,0.55); margin:0 0 8px; font-weight:500; text-transform:uppercase; letter-spacing:0.6px; }
.lin-col h4.lin-col-title { display:flex; align-items:center; justify-content:center; gap:6px; font-size:12px; color:#64748B; margin:0 0 16px; font-weight:600; letter-spacing:0.8px; text-transform:uppercase; text-align:center; padding:0; background:transparent; border:none; }
.lin-node { padding:10px 12px; border-radius:8px; border:1px solid #E2E8F0; background:#F8FAFC; font-size:13px; line-height:1.55; position:relative; z-index:2; transition:all 0.2s ease; }
.lin-node .ln-ttl { font-weight:500; color:#1E293B; font-size:14px; line-height:1.5; letter-spacing:0.02em; word-break:break-all; margin-bottom:6px; }
.lin-node .ln-footer { display:flex; justify-content:space-between; align-items:center; gap:8px; }
.lin-node .ln-meta { color:#64748B; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1; }
.lin-node .ln-icon-actions { position:absolute; bottom:8px; right:8px; display:flex; gap:4px; opacity:0; transform:translateY(4px); transition:opacity 0.2s ease, transform 0.2s ease; pointer-events:none; background:rgba(255,255,255,0.98); backdrop-filter:blur(8px); padding:4px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.08); }
.lin-node:hover .ln-icon-actions { opacity:1; transform:translateY(0); pointer-events:auto; }
.ln-icon-btn { height:28px; width:28px; padding:0; display:inline-flex; align-items:center; justify-content:center; background:rgba(255,255,255,0.95); border:1px solid #E2E8F0; border-radius:6px; cursor:pointer; transition:all 0.2s ease; text-decoration:none; color:#64748B; position:relative; backdrop-filter:blur(4px); box-shadow:0 1px 3px rgba(0,0,0,0.08); }
.ln-icon-btn .icon { width:16px; height:16px; flex-shrink:0; stroke-width:1.5; transition:transform 0.2s ease; }
.ln-icon-btn .btn-label { display:none; }
.ln-icon-btn:hover { background:#EFF6FF; border-color:#3B82F6; color:#3B82F6; transform:translateY(-1px); box-shadow:0 2px 8px rgba(59,130,246,0.25); }
.ln-icon-btn:hover .icon { transform:scale(1.1); }
.ln-icon-btn:first-child:hover { background:#3B82F6; border-color:#3B82F6; color:#fff; }
.ln-icon-btn:first-child:hover .icon { transform:scale(1.1); }
/* Custom Tooltip */
.ln-icon-btn::before { content:attr(data-tooltip); position:absolute; bottom:calc(100% + 8px); left:50%; transform:translateX(-50%) translateY(4px); background:rgba(0,0,0,0.9); color:#fff; padding:6px 10px; border-radius:6px; font-size:12px; white-space:nowrap; opacity:0; pointer-events:none; transition:opacity 0.2s ease, transform 0.2s ease; z-index:1000; }
.ln-icon-btn::after { content:''; position:absolute; bottom:calc(100% + 2px); left:50%; transform:translateX(-50%); border:4px solid transparent; border-top-color:rgba(0,0,0,0.9); opacity:0; pointer-events:none; transition:opacity 0.2s ease; z-index:1000; }
.ln-icon-btn:hover::before { opacity:1; transform:translateX(-50%) translateY(0); }
.ln-icon-btn:hover::after { opacity:1; }
.lin-node:hover { box-shadow:0 4px 12px rgba(0,0,0,0.08); border-color:#CBD5E1; }
.lin-node.teal, .lin-node.purple, .lin-node.coral, .lin-node.blue, .lin-node.amber, .lin-node.green { background:#F8FAFC; border-color:#E2E8F0; }
.lin-node.dagger { background:#F8FAFC; border-left:3px solid #ff9500; border-top:1px solid #E2E8F0; border-right:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0; }
.lin-node.anchor { background:#EFF6FF; border:2px solid #3B82F6; box-shadow:0 0 0 3px rgba(59,130,246,0.1); transform:scale(1.02); z-index:10; }
.lin-node.dagger.anchor { background:#EFF6FF; border:2px solid #3B82F6; border-left:3px solid #ff9500; box-shadow:0 0 0 3px rgba(59,130,246,0.1); }

/* 卡片固定高度 + 相对定位（供浮层锚定）*/
.lin-node { position:relative; }

/* 卡片操作按钮区（常驻）*/
.ln-actions { display:flex; flex-wrap:wrap; gap:10px; margin-top:8px; padding-top:6px; border-top:1px solid rgba(0,0,0,0.06); }
.ln-actions a.btn-link { font-size:12px; color:#149DAA; text-decoration:none; white-space:nowrap; cursor:pointer; }
.ln-actions a.btn-link:hover { text-decoration:underline; }

/* 悬停浮层（只读详情）*/
.lin-node[data-lineage-tip] { cursor:default; }
.lin-node.muted { background:#fafafa; border-style:dashed; }
/* 图例 */
.lineage-hint { display:flex; gap:24px; margin-bottom:12px; padding:8px 12px; background:#FAFBFC; border-radius:6px; font-size:12px; color:#64748B; align-items:center; }
.lineage-hint .hint-section { display:flex; align-items:center; gap:12px; }
.lineage-hint .hint-label { font-weight:600; color:#475569; }
.lineage-hint .hint-item { display:flex; align-items:center; gap:6px; }
.lineage-hint .hint-dot { width:10px; height:10px; border-radius:2px; display:inline-block; }
.lineage-hint .hint-dot.blue { background:#EFF6FF; border:2px solid #3B82F6; }
.lineage-hint .hint-dot.gray { background:#F8FAFC; border:1px solid #E2E8F0; }
.lineage-hint .hint-bar { width:3px; height:16px; border-radius:1px; display:inline-block; }
.lineage-hint .hint-bar.dagger { background:#ff9500; }
/* 锚点"当前"角标 */
.lin-node.anchor { position:relative; }
.lin-node.anchor::before { content:"当前"; position:absolute; top:-8px; left:10px; background:#149DAA; color:#fff; font-size:10px; padding:1px 6px; border-radius:3px; z-index:3; }

/* 链路高亮系统 */
.lin-node { transition:opacity 0.3s ease, box-shadow 0.3s ease; }
.lin-node.highlight { opacity:1; box-shadow:0 0 0 3px rgba(20,157,170,0.3); position:relative; z-index:10; }
.lin-node.dimmed { opacity:0.4; filter:grayscale(60%); }
.lin-node.locked { box-shadow:0 0 0 3px rgba(20,157,170,0.5); }
.lin-flow.lin-flow-5 { grid-template-columns:1fr 1fr 1.1fr 1fr 1fr; align-items:stretch; }
.lin-col-body { flex:1; display:flex; flex-direction:column; justify-content:center; gap:8px; }
.lin-summary { display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:14px; }
.lin-sum-card { background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:14px 16px; }
.lin-sum-card .k { font-size:12px; color:rgba(0,0,0,0.45); }
.lin-sum-card .v { margin-top:4px; font-size:20px; font-weight:600; color:rgba(0,0,0,0.85); font-family:'SFMono-Regular',Consolas,monospace; }
.lin-actions { display:flex; justify-content:flex-end; gap:8px; margin-bottom:14px; }
.lin-table { margin-top:16px; }
.lin-filter { background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:14px 16px; margin-bottom:14px; }
.lin-filter .lf-input-group { display:flex; gap:8px; align-items:center; max-width:600px; }
.lin-filter .lf-dimension-select { height:34px; border:1px solid #d9d9d9; border-radius:6px; padding:0 11px; font-size:13px; outline:none; background:#fff; min-width:120px; }
.lin-filter .lf-dimension-select:focus { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.10); }
.lin-filter input { flex:1; height:34px; border:1px solid #d9d9d9; border-radius:6px; padding:0 11px; font-size:13px; outline:none; box-sizing:border-box; min-width:200px; }
.lin-filter input:focus { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.10); }

/* Checkpoint History Modal */
.ckpt-history-modal { position:fixed; top:0; left:0; width:100%; height:100%; z-index:9999; display:flex; align-items:center; justify-content:center; }
.ckpt-history-overlay { position:absolute; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); }
.ckpt-history-content { position:relative; width:90%; max-width:600px; max-height:80vh; background:#fff; border-radius:8px; box-shadow:0 4px 20px rgba(0,0,0,0.3); display:flex; flex-direction:column; z-index:10000; }
.ckpt-history-header { display:flex; justify-content:space-between; align-items:center; padding:20px 24px; border-bottom:1px solid #f0f0f0; }
.ckpt-history-header h3 { margin:0; font-size:18px; font-weight:600; color:#1a1a1a; }
.ckpt-history-close { background:none; border:none; font-size:24px; color:#999; cursor:pointer; padding:0; width:32px; height:32px; display:flex; align-items:center; justify-content:center; border-radius:4px; }
.ckpt-history-close:hover { background:#f5f5f5; color:#333; }
.ckpt-history-body { padding:24px; overflow-y:auto; flex:1; }

/* 骨架屏加载 */
.ckpt-timeline-skeleton { position:relative; }
.skeleton-item { position:relative; padding-left:40px; margin-bottom:24px; }
.skeleton-item:last-child { margin-bottom:0; }
.skeleton-dot { position:absolute; left:0; top:8px; width:24px; height:24px; border-radius:50%; background:#e5e7eb; }
.skeleton-card { background:#f9fafb; border:1px solid #e5e7eb; border-radius:6px; padding:12px 16px; }
.skeleton-line { height:12px; background:#e5e7eb; border-radius:4px; margin-bottom:8px; }
.skeleton-line:last-child { margin-bottom:0; }
.skeleton-line.w-1-2 { width:50%; }
.skeleton-line.w-3-4 { width:75%; }
@keyframes skeleton-pulse { 0%, 100% { opacity:1; } 50% { opacity:0.5; } }
.animate-pulse { animation:skeleton-pulse 2s cubic-bezier(0.4,0,0.6,1) infinite; }
.ckpt-timeline { position:relative; }
.ckpt-timeline-item { position:relative; padding-left:40px; margin-bottom:24px; }
.ckpt-timeline-item:last-child { margin-bottom:0; }
.ckpt-timeline-item::before { content:''; position:absolute; left:11px; top:32px; bottom:0; width:2px; background:#e5e7eb; }
.ckpt-timeline-item:last-child::before { display:none; }
.ckpt-timeline-dot { position:absolute; left:0; top:8px; width:24px; height:24px; border-radius:50%; background:#fff; border:3px solid #d1d5db; z-index:1; transition:all 0.2s ease; }
.ckpt-timeline-item:hover .ckpt-timeline-dot { transform:scale(1.15); border-color:#f59e0b; }
.ckpt-timeline-item.current .ckpt-timeline-dot { background:#f59e0b; border-color:#f59e0b; box-shadow:0 0 0 4px rgba(245,158,11,0.15); transform:scale(1.1); }
.ckpt-timeline-node { background:#fff; border:1px solid #e5e7eb; border-radius:6px; padding:12px 16px; cursor:pointer; transition:all 0.2s ease; }
.ckpt-timeline-node:hover { border-color:#f59e0b; box-shadow:0 2px 8px rgba(0,0,0,0.08); transform:translateX(2px); }
.ckpt-timeline-item.current .ckpt-timeline-node { border-color:#f59e0b; background:#fffbeb; }
.ckpt-timeline-node-id { font-size:11px; color:#9ca3af; margin-bottom:4px; font-family:'SF Mono',Menlo,monospace; }
.ckpt-timeline-node-name { font-size:14px; font-weight:500; color:#1a1a1a; margin-bottom:6px; word-break:break-word; overflow-wrap:break-word; }
.ckpt-timeline-node-meta { font-size:12px; color:#6b7280; display:flex; gap:12px; }
.ckpt-timeline-node-time { color:#9ca3af; font-size:11px; }
.ckpt-timeline-connector { padding-left:40px; margin:8px 0; font-size:12px; color:#9ca3af; display:flex; align-items:center; gap:8px; }
.ckpt-timeline-connector::before { content:'↓'; font-size:14px; color:#d1d5db; }
.ckpt-timeline-connector.dagger { color:#f59e0b; }
.kv-grid { display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:12px; }
.kv { background:#fafbfc; border:1px solid #f0f0f0; border-radius:8px; padding:12px 14px; min-width:0; }
.kv span { display:block; font-size:12px; color:rgba(0,0,0,0.45); margin-bottom:5px; }
.kv b { display:block; font-size:13.5px; color:rgba(0,0,0,0.82); font-weight:500; word-break:break-word; }

/* ── Labeled filter bar (训练任务/Checkpoint 列表用) ── */
.fb-labeled { background:#fff; padding:16px 18px; border:1px solid #f0f0f0; border-radius:8px; margin-bottom:14px; display:flex; gap:18px; align-items:flex-end; flex-wrap:wrap; }
.fb-labeled .ff { display:flex; flex-direction:column; gap:6px; }
.fb-labeled .ff > label { font-size:13px; color:rgba(0,0,0,0.72); }
.fb-labeled .ff input, .fb-labeled .ff select { height:34px; min-width:240px; padding:5px 12px; border:1px solid #d9d9d9; border-radius:6px; font-size:14px; outline:none; background:#fff; box-sizing:border-box; }
.fb-labeled .ff .remote-filter { min-width:240px; }
.fb-labeled .ff .rf-control input { height:26px; min-width:82px; padding:0 2px; border:0; border-radius:0; box-shadow:none !important; background:transparent; }
.fb-labeled .ff input::placeholder { color:rgba(0,0,0,0.32); }
.fb-labeled .ff input:focus, .fb-labeled .ff select:focus { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.12); }
.list-summarybar { display:flex; align-items:center; justify-content:space-between; gap:16px; margin:0 2px 14px; }
.list-summarybar .txt { font-size:13.5px; color:rgba(0,0,0,0.62); }
.list-summarybar .txt b { color:rgba(0,0,0,0.85); font-family:'SF Mono',Menlo,monospace; font-weight:600; }

/* ── Page actions (top-right primary button) ── */
.page-actions { display:flex; justify-content:flex-end; margin-bottom:14px; }
.cache-page-head { display:flex; align-items:center; gap:12px; margin-bottom:18px; }
.cache-page-title { font-size:16px; font-weight:600; color:rgba(0,0,0,0.85); }

/* ── Pill-style action buttons in tables (TEST / DAgger / 复制) ── */
.tbtn { display:inline-flex; align-items:center; gap:5px; height:28px; padding:0 13px; border-radius:6px; font-size:12.5px; cursor:pointer; border:1px solid #d9d9d9; background:#fff; color:rgba(0,0,0,0.75); text-decoration:none; margin-right:4px; box-sizing:border-box; }
.tbtn:hover { border-color:#149DAA; color:#149DAA; }

/* ── Wide drawer (for 新增训练任务) ── */
.drawer.drawer-wide { width:680px; }

/* ── Drawer form: row 2-col ── */
.fg-row { display:flex; gap:14px; }
.fg-row > .fg { flex:1; }
.fg-hint { font-size:11px; color:rgba(0,0,0,0.4); margin-top:2px; }
.fg-req::before { content:'*'; color:#cf1322; margin-right:4px; }
.image-path-hint { margin-top:8px; padding:9px 11px; border:1px solid #f0f0f0; border-radius:6px; background:#fafbfc; color:rgba(0,0,0,0.45); font-size:12px; line-height:1.5; }
.image-path-hint .path { display:block; color:rgba(0,0,0,0.62); font-family:'SF Mono',Menlo,monospace; word-break:break-all; }
.image-mode-tabs { margin:0 0 12px; width:max-content; max-width:100%; }
.image-mode-panel { display:none; }
.image-mode-panel.active { display:block; }
.image-mode-panel input:disabled { background:#f5f7fa; color:rgba(0,0,0,0.58); cursor:not-allowed; }

/* ── Drawer: dataset row table ── */
.ds-table { border:1px solid #f0f0f0; border-radius:8px; overflow:hidden; }
.ds-table .ds-head { display:grid; grid-template-columns:1fr 100px 80px; padding:10px 14px; background:#fafafa; font-size:13px; color:rgba(0,0,0,0.7); border-bottom:1px solid #f0f0f0; }
.ds-table .ds-row { display:grid; grid-template-columns:1fr 100px 80px; padding:10px 14px; gap:8px; align-items:center; }
.ds-table .ds-row select { height:32px; border:1px solid #d9d9d9; border-radius:6px; padding:0 10px; font-size:13px; outline:none; background:#fff; }
.ds-table .ds-row input { height:32px; border:1px solid #d9d9d9; border-radius:6px; padding:0 10px; font-size:13px; outline:none; background:#fff; width:80px; }
.ds-table .ds-confirm { color:#149DAA; cursor:pointer; font-size:13px; }
.ds-table .ds-confirm:hover { color:#0F8190; }

/* ── Drawer: advanced config tabs ── */
.adv-tabs { display:flex; gap:4px; border-bottom:1px solid #f0f0f0; margin-bottom:10px; align-items:flex-end; }
.adv-tabs .at { padding:6px 14px 8px; font-size:13px; color:rgba(0,0,0,0.6); border-bottom:2px solid transparent; margin-bottom:-1px; cursor:pointer; }
.adv-tabs .at:hover { color:rgba(0,0,0,0.85); }
.adv-tabs .at.active { color:#149DAA; border-bottom-color:#149DAA; font-weight:500; }
.adv-tabs .at-reset { margin-left:auto; font-size:12px; color:rgba(0,0,0,0.55); padding:4px 10px; border:1px solid #d9d9d9; border-radius:5px; cursor:pointer; background:#fff; }
.adv-tabs .at-reset:hover { border-color:#149DAA; color:#149DAA; }
.yaml-area { width:100%; min-height:300px; padding:12px 14px; font-family:'SF Mono',Menlo,Consolas,monospace; font-size:12.5px; line-height:1.65; background:#fafbfc; border:1px solid #e5e7eb; border-radius:8px; resize:vertical; outline:none; color:rgba(0,0,0,0.85); box-sizing:border-box; white-space:pre; overflow:auto; }
.yaml-area:focus { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.12); }
.entry-command-area { width:100%; min-height:220px; padding:12px 14px; font-family:'SF Mono',Menlo,Consolas,monospace; font-size:12.5px; line-height:1.65; background:#fafbfc; border:1px solid #e5e7eb; border-radius:8px; resize:vertical; outline:none; color:rgba(0,0,0,0.85); box-sizing:border-box; white-space:pre; overflow:auto; }
.entry-command-area:focus { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.12); }

/* ── 部署任务: 设备数胶囊 + hover/click 弹出清单 ── */
.devs-cell { position:relative; display:inline-block; }
.devs-pill { display:inline-flex; align-items:center; gap:5px; padding:3px 12px; border-radius:11px; background:#DEF6F9; border:1px solid #7BD8DF; color:#149DAA; font-size:13px; cursor:pointer; user-select:none; font-family:'SF Mono',Menlo,monospace; }
.devs-pill:hover { background:#cfeef2; }
.devs-pill .ca { font-size:9px; opacity:0.7; transition:transform 0.15s; }
.devs-pill.open .ca { transform:rotate(180deg); }
.devs-pop { display:none; position:absolute; top:calc(100% + 6px); left:0; background:#fff; border:1px solid #e5e7eb; border-radius:8px; box-shadow:0 6px 22px rgba(0,0,0,0.12); padding:6px; z-index:50; min-width:230px; max-height:260px; overflow-y:auto; }
.devs-cell:hover .devs-pop, .devs-pop.open { display:block; }
.devs-pop a { display:flex; justify-content:space-between; align-items:center; gap:14px; padding:6px 10px; border-radius:4px; font-size:13px; color:#149DAA; font-family:'SF Mono',Menlo,monospace; text-decoration:none; }
.devs-pop a:hover { background:#EBF8FA; color:#0F8190; }
.devs-pop .dev-id { min-width:84px; }
.devs-pop .dev-state { display:inline-flex; align-items:center; gap:5px; font-family:inherit; font-size:12px; color:rgba(0,0,0,0.65); white-space:nowrap; }
.devs-pop .dev-state::before { content:''; width:7px; height:7px; border-radius:50%; display:inline-block; }
.devs-pop .dev-state.success::before { background:#389e0d; }
.devs-pop .dev-state.failed::before { background:#cf1322; }
.devs-pop .dev-state.running::before { background:#d48806; }
.deploy-progress { position:relative; display:inline-flex; align-items:center; font-family:'SF Mono',Menlo,monospace; font-size:12.5px; white-space:nowrap; }
.deploy-progress .dp-success-num { color:#389e0d; font-weight:600; }
.deploy-progress .dp-failed-num { color:#cf1322; font-weight:600; }
.deploy-progress .dp-total-num { color:rgba(0,0,0,0.72); font-weight:600; }
.deploy-progress .dp-sep { color:rgba(0,0,0,0.28); padding:0 2px; }
.deploy-progress .dp-tip { display:none; position:absolute; left:0; top:calc(100% + 8px); z-index:80; min-width:190px; padding:8px 10px; border:1px solid #e5e7eb; border-radius:6px; background:#fff; box-shadow:0 6px 18px rgba(0,0,0,0.12); font-family:inherit; font-size:12px; line-height:1.8; color:rgba(0,0,0,0.72); pointer-events:none; }
.deploy-progress:hover .dp-tip { display:block; }
.deploy-progress .dp-tip span { display:flex; align-items:center; gap:6px; white-space:nowrap; }
.deploy-progress .dp-dot { width:7px; height:7px; border-radius:50%; display:inline-block; flex:none; }
.deploy-progress .dp-dot.success { background:#389e0d; }
.deploy-progress .dp-dot.failed { background:#cf1322; }
.deploy-progress .dp-dot.total { background:rgba(0,0,0,0.55); }
.deploy-progress .dp-dot.running { background:#d48806; }
.deploy-device-picker, .deploy-checkpoint-picker { position:relative; background:transparent; overflow:visible; }
.ddp-control { min-height:38px; padding:5px 34px 5px 8px; display:flex; align-items:center; gap:6px; flex-wrap:wrap; border:1px solid #d9d9d9; border-radius:8px; background:#fff; box-sizing:border-box; cursor:text; position:relative; }
.ddp-control::after { content:'⌄'; position:absolute; right:12px; top:50%; transform:translateY(-56%); color:rgba(0,0,0,0.45); font-size:15px; pointer-events:none; }
.deploy-device-picker.open .ddp-control, .deploy-checkpoint-picker.open .ddp-control, .ddp-control:focus-within { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.12); }
.ddp-control .picked { display:inline-flex; align-items:center; gap:6px; max-width:100%; height:26px; padding:0 8px; border:1px solid #dfe3e8; border-radius:5px; background:#f7f8fa; color:rgba(0,0,0,0.70); font-size:12.5px; }
.ddp-control .picked .picked-text { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:230px; }
.ddp-control .picked i { font-style:normal; color:rgba(0,0,0,0.35); cursor:pointer; }
.ddp-control input { flex:1; min-width:130px; height:26px; border:0; outline:none; padding:0 4px; font-size:13px; font-family:inherit; background:transparent; }
.fg .ddp-control input, .fg .ddp-control input:focus { border:0; border-radius:0; box-shadow:none !important; padding:0 4px; background:transparent; }
.ddp-menu { display:none; position:absolute; left:0; right:0; top:calc(100% + 6px); z-index:180; max-height:260px; overflow-y:auto; padding:6px; border:1px solid #e5e7eb; border-radius:8px; background:#fff; box-shadow:0 8px 24px rgba(0,0,0,0.12); }
.deploy-device-picker.open .ddp-menu, .deploy-checkpoint-picker.open .ddp-menu { display:block; }
.ddp-item { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; padding:9px 10px; border-radius:6px; cursor:pointer; color:rgba(0,0,0,0.72); }
.ddp-item:hover { background:#EBF8FA; }
.ddp-item.on { background:#DEF6F9; color:#149DAA; }
.ddp-copy { min-width:0; display:flex; flex-direction:column; gap:3px; }
.ddp-main { font-size:13.5px; color:rgba(0,0,0,0.84); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ddp-item.on .ddp-main { color:#149DAA; }
.ddp-main .serial { font-family:'SF Mono',Menlo,monospace; color:rgba(0,0,0,0.58); }
.ddp-sub { font-size:12px; color:rgba(0,0,0,0.45); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ddp-check { display:none; flex:none; padding-top:2px; color:#149DAA; font-size:12px; }
.ddp-item.on .ddp-check { display:inline; }

/* ── Mini pagination (visual only) ── */
.mini-pager { display:flex; align-items:center; justify-content:flex-end; gap:8px; padding:12px 8px 0; font-size:13px; color:rgba(0,0,0,0.65); }
.mini-pager select { height:28px; padding:0 10px; border:1px solid #d9d9d9; border-radius:5px; background:#fff; font-size:13px; outline:none; }
.mini-pager .pg-btn { width:28px; height:28px; border:1px solid #d9d9d9; border-radius:5px; background:#fff; display:inline-flex; align-items:center; justify-content:center; cursor:pointer; color:rgba(0,0,0,0.55); }
.mini-pager .pg-btn.active { border-color:#149DAA; color:#149DAA; }
.mini-pager .pg-btn:hover { border-color:#149DAA; color:#149DAA; }
.mini-pager input.pg-goto { width:42px; height:28px; border:1px solid #d9d9d9; border-radius:5px; padding:0 8px; font-size:13px; outline:none; }
.mini-pager .pg-go { padding:0 12px; color:#149DAA; cursor:pointer; }

/* ── 训练任务详情 ── */
.tdsplit { display:flex; gap:14px; align-items:flex-start; }
.tlp { width:240px; background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:10px 8px; flex:none; position:relative; min-height:300px; }
.tlp .tlp-collapse { position:absolute; right:-12px; top:18px; width:22px; height:22px; border-radius:50%; background:#fff; border:1px solid #e5e7eb; cursor:pointer; display:flex; align-items:center; justify-content:center; font-size:11px; color:rgba(0,0,0,0.5); box-shadow:0 1px 4px rgba(0,0,0,0.06); z-index:5; }
.tlp .tlp-collapse:hover { color:#149DAA; border-color:#149DAA; }
.tlp-item { display:flex; align-items:flex-start; gap:8px; padding:9px 12px; border-radius:6px; cursor:pointer; color:rgba(0,0,0,0.75); font-size:13px; text-decoration:none; line-height:1.5; word-break:break-all; }
.tlp-item:hover { background:#fafafa; color:#149DAA; }
.tlp-item.active { background:#DEF6F9; color:#149DAA; font-weight:500; border-left:3px solid #149DAA; padding-left:9px; }
.tlp-item .ti-ic { color:rgba(0,0,0,0.4); flex:none; font-size:14px; margin-top:1px; }
.tlp-item.active .ti-ic { color:#149DAA; }
.tdm { flex:1; min-width:0; }
.tdh { background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:20px 24px; margin-bottom:18px; position:relative; }
.tdh .tdh-name { font-size:18px; font-weight:600; color:rgba(0,0,0,0.85); margin-bottom:12px; word-break:break-all; padding-right:80px; }
.tdh .tdh-meta { display:flex; gap:40px; font-size:13px; flex-wrap:wrap; }
.tdh .tdh-meta .lbl { color:rgba(0,0,0,0.5); margin-right:8px; }
.tdh .tdh-meta .val { color:rgba(0,0,0,0.85); }
.tdh-actions { position:absolute; top:34px; right:28px; display:flex; gap:8px; align-items:center; }
.wandb-btn { position:absolute; top:18px; right:20px; padding:7px 18px; background:#149DAA; color:#fff; font-size:13px; border:none; border-radius:18px; cursor:pointer; font-weight:500; }
.wandb-btn:hover { background:#0F8190; }
.sec-title { font-size:16px; font-weight:600; color:rgba(0,0,0,0.85); margin:0 0 14px; }
.ckpt-loc { display:inline-flex; align-items:center; gap:6px; color:#149DAA; font-size:12.5px; font-family:'SF Mono',Menlo,monospace; cursor:pointer; text-decoration:none; }
.ckpt-loc:hover { color:#0F8190; }
.ckpt-loc .ll-ic { color:rgba(0,0,0,0.4); font-size:13px; }
.ckpt-loc:hover .ll-ic { color:#149DAA; }

/* CodeMirror in YAML drawer: align padding/border with our look */
.CodeMirror { border:1px solid #e5e7eb; border-radius:8px; font-family:'SF Mono',Menlo,Consolas,monospace; font-size:12.5px; line-height:1.65; min-height:300px; background:#fafbfc; }
.CodeMirror-focused { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.12); }
.CodeMirror-gutters { background:transparent; border:none; }

/* ── 训练详情 Tabs ── */
.det-tabs { display:flex; gap:2px; background:#fff; padding:0 24px; border:1px solid #f0f0f0; border-radius:8px; margin-bottom:14px; }
.det-tab { padding:13px 18px; font-size:14px; color:rgba(0,0,0,0.65); cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-1px; user-select:none; }
.det-tab:hover { color:#149DAA; }
.det-tab.active { color:#149DAA; border-bottom-color:#149DAA; font-weight:500; }
.det-pane { display:none; }
.det-pane.active { display:block; }

/* ── 分析看板: 漏斗 + 处理能力 (两列, 等高) ── */
.dash-row { display:grid; grid-template-columns:1fr 1fr; gap:16px; align-items:stretch; }
@media (max-width: 1100px) { .dash-row { grid-template-columns:1fr; } }
.dash-row > .card { display:flex; flex-direction:column; margin-bottom:0; }
.dash-row > .card > .funnel { flex:1; justify-content:center; }
.dash-row > .card > .table-wrap { flex:1; }
.funnel { padding:10px 0 6px; display:flex; flex-direction:column; gap:0; }
.funnel-row { display:flex; justify-content:center; padding:2px 0; }
.funnel-bar { padding:10px 16px; color:#fff; border-radius:6px; display:flex; align-items:center; justify-content:space-between; gap:14px; min-width:140px; box-sizing:border-box; transition:width 0.3s, transform 0.15s; }
.funnel-bar:hover { transform:translateY(-1px); }
.funnel-bar .fb-stage { font-size:13px; font-weight:500; letter-spacing:0.3px; white-space:nowrap; }
.funnel-bar .fb-num { font-size:15px; font-weight:600; font-family:'SF Mono',Menlo,monospace; letter-spacing:0.2px; white-space:nowrap; }
.funnel-drop { text-align:center; font-size:11.5px; color:rgba(0,0,0,0.5); padding:3px 0; display:flex; justify-content:center; align-items:center; gap:12px; }
.funnel-drop .pct { color:#149DAA; font-weight:500; font-family:'SF Mono',Menlo,monospace; }
.funnel-drop .loss { color:#d4504e; font-family:'SF Mono',Menlo,monospace; }
.funnel-drop .arr { color:rgba(0,0,0,0.3); font-size:13px; }
.fk-cap { display:inline-flex; align-items:center; gap:6px; padding:2px 10px; border-radius:11px; background:#f5f7fa; font-size:12px; color:rgba(0,0,0,0.65); }
.fk-cap b { font-family:'SF Mono',Menlo,monospace; color:rgba(0,0,0,0.85); }
.fk-ratio { font-family:'SF Mono',Menlo,monospace; font-size:13px; }
.fk-ratio.ok { color:#2e9e5b; } .fk-ratio.warn { color:#d48806; } .fk-ratio.bad { color:#d4504e; }

/* ── 工作台: 任务卡片列表 (一行一张) ── */
.wb-list { display:flex; flex-direction:column; gap:12px; }
.wb-card { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:18px 22px; border-left:4px solid #149DAA; display:flex; gap:24px; align-items:center; transition:box-shadow 0.18s, transform 0.15s; }
.wb-card:hover { box-shadow:0 4px 18px rgba(0,0,0,0.06); transform:translateY(-1px); }
.wb-card .wb-main { flex:1; min-width:0; }
.wb-card .wb-head { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
.wb-card .wb-name { font-size:15.5px; font-weight:500; color:rgba(0,0,0,0.85); }
.wb-card .wb-desc { font-size:13px; color:rgba(0,0,0,0.55); line-height:1.65; }
.wb-card .wb-side { display:flex; align-items:center; gap:22px; flex:none; }
.wb-card .wb-progress { width:260px; display:flex; flex-direction:column; gap:8px; }
.wb-card .wb-progress .wp-bar { position:relative; height:10px; background:#f0f0f0; border-radius:5px; overflow:hidden; }
.wb-card .wb-progress .wp-fill { height:100%; background:#149DAA; border-radius:5px; transition:width 0.3s; }
.wb-card .wb-progress .wp-meta { display:flex; align-items:baseline; gap:14px; font-size:12.5px; color:rgba(0,0,0,0.65); }
.wb-card .wb-progress .wp-meta b { font-family:'SF Mono',Menlo,monospace; font-weight:500; }
.wb-card .wb-progress .wp-meta .done b { color:#149DAA; }
.wb-card .wb-progress .wp-meta .pend b { color:rgba(0,0,0,0.78); }
.wb-card .wb-progress .wp-meta .pct { margin-left:auto; color:rgba(0,0,0,0.45); font-family:'SF Mono',Menlo,monospace; }
.wb-badge { font-size:13px; font-weight:500; padding:4px 12px; border-radius:6px; border:1px solid transparent; line-height:1.4; flex:none; }
.wb-badge.blue   { background:#DEF6F9; color:#0F8190; border-color:#7BD8DF; }
.wb-card.blue    { border-left-color:#149DAA; }
.wb-badge.teal   { background:#e1f5ee; color:#0f6e56; border-color:#5dcaa5; }
.wb-card.teal    { border-left-color:#0f6e56; }
.wb-badge.purple { background:#eeedfe; color:#534AB7; border-color:#aea7f0; }
.wb-card.purple  { border-left-color:#7F77DD; }
.wb-badge.orange { background:#fef0eb; color:#993c1d; border-color:#f0997b; }
.wb-card.orange  { border-left-color:#D85A30; }
.wb-badge.amber  { background:#fffbe6; color:#ad6800; border-color:#ffe58f; }
.wb-card.amber   { border-left-color:#d48806; }
.wb-badge.green  { background:#f0faf4; color:#2e9e5b; border-color:#a3dbb8; }
.wb-card.green   { border-left-color:#389e0d; }

/* ── 任务管理: stage 切换 tab + 新建按钮同一行 ── */
.tm-bar { display:flex; align-items:flex-end; justify-content:space-between; border-bottom:1px solid #f0f0f0; margin:0 2px 16px; padding:0 4px; gap:24px; }
.tm-tabs { display:flex; gap:4px; align-items:flex-end; flex-wrap:wrap; }
.tm-tab { padding:11px 18px; font-size:14px; color:rgba(0,0,0,0.65); cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-1px; text-decoration:none; transition:color 0.15s; display:inline-flex; align-items:center; gap:7px; user-select:none; }
.tm-tab:hover { color:#149DAA; }
.tm-tab.active { color:#149DAA; border-bottom-color:#149DAA; font-weight:500; }
.tm-tab .ct { font-size:11px; padding:1px 8px; border-radius:10px; background:#f0f0f0; color:rgba(0,0,0,0.5); line-height:1.6; font-weight:400; min-width:14px; text-align:center; }
.tm-tab:hover .ct { background:#EBF8FA; color:#149DAA; }
.tm-tab.active .ct { background:#DEF6F9; color:#149DAA; }
.tm-bar > .btn { margin-bottom:8px; flex:none; }
.tm-subtabs { display:inline-flex; gap:0; padding:3px; background:#f5f7fa; border-radius:8px; margin:0 2px 14px; }
.tm-subtab { padding:6px 16px; font-size:13px; color:rgba(0,0,0,0.6); text-decoration:none; border-radius:6px; transition:all 0.15s; display:inline-flex; align-items:center; gap:6px; }
button.tm-subtab { border:0; background:transparent; font-family:inherit; cursor:pointer; }
.tm-subtab:hover { color:#149DAA; }
.tm-subtab.active { background:#fff; color:#149DAA; font-weight:500; box-shadow:0 1px 3px rgba(0,0,0,0.06); }
.tm-subtab .ct { font-size:11.5px; color:rgba(0,0,0,0.4); }
.tm-subtab.active .ct { color:#149DAA; opacity:0.8; }
.ckpt-listbar { display:flex; align-items:center; justify-content:space-between; gap:16px; margin:0 2px 14px; }
.ckpt-listbar .tm-subtabs { margin:0; }
.ckpt-listnote { font-size:13px; color:rgba(0,0,0,0.55); }
.ckpt-actions { display:flex; align-items:center; gap:10px; margin-left:auto; }
.ckpt-detail-title { font-size:18px; font-weight:600; color:rgba(0,0,0,0.86); margin:0 0 18px; word-break:break-all; }
.ckpt-form { display:flex; flex-direction:column; gap:16px; }
.ckpt-form-row { display:grid; grid-template-columns:92px minmax(0,1fr); gap:14px; align-items:flex-start; }
.ckpt-form-row label { padding-top:2px; font-size:13px; color:rgba(0,0,0,0.56); text-align:left; }
.ckpt-form-value { min-height:22px; display:block; box-sizing:border-box; padding:0; background:transparent; color:rgba(0,0,0,0.84); font-size:13.5px; line-height:1.65; word-break:break-word; }
.ckpt-form-value.mono { font-size:13px; color:rgba(0,0,0,0.72); }

/* ── 租户管理 · 权限管理 (角色 + 详情 + API 三栏) ── */
.tn-mgmt-tt { font-size:20px; font-weight:600; color:rgba(0,0,0,0.85); margin:0 0 14px; }
.role-mgmt { display:grid; grid-template-columns:300px 1fr 1fr; gap:14px; align-items:flex-start; }
.rm-list, .rm-detail, .rm-api { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:18px; }
.rm-list-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
.rm-list-head h3 { margin:0; font-size:15px; font-weight:600; color:rgba(0,0,0,0.85); }
.rm-roles { display:flex; flex-direction:column; gap:10px; max-height:720px; overflow-y:auto; }
.rm-role { border:1px solid #e8eaed; border-radius:8px; padding:14px 14px 12px; cursor:pointer; position:relative; background:#fff; transition:all 0.15s; }
.rm-role:hover { border-color:#149DAA; }
.rm-role.active { border-color:#149DAA; background:linear-gradient(180deg, #f0fbfc, #fff); box-shadow:0 0 0 3px rgba(20,157,170,0.10); }
.rm-rc-nm { font-size:14px; font-weight:500; color:rgba(0,0,0,0.85); padding-right:28px; }
.rm-rc-bot { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-top:8px; }
.rm-rc-tm { font-size:12px; color:rgba(0,0,0,0.45); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1; min-width:0; }
.rm-rc-del { position:absolute; top:14px; right:14px; color:#e25c5c; font-size:14px; cursor:pointer; display:none; padding:2px; line-height:1; }
.rm-role.active .rm-rc-del { display:inline-flex; }
.rm-d-row { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:18px; }
.rm-d-fg label { display:block; font-size:13px; color:rgba(0,0,0,0.78); margin-bottom:6px; }
.rm-d-fg label .req { color:#e25c5c; margin-right:3px; }
.rm-d-fg input { width:100%; height:34px; padding:0 12px; border:1px solid #e2e4e8; border-radius:6px; font-size:13px; box-sizing:border-box; }
.rm-d-fg input:focus { border-color:#149DAA; outline:none; }
.rm-d-perm-head { display:flex; align-items:center; gap:12px; margin-bottom:12px; }
.rm-d-perm-head h4 { margin:0; font-size:14px; font-weight:600; color:rgba(0,0,0,0.85); }
.rm-d-perm-head .grow { flex:1; }
.rm-d-perm-head .btn { padding:5px 12px; font-size:12.5px; }
.rm-perm-tree { font-size:13.5px; }
.rm-pt-group { margin-bottom:6px; }
.rm-pt-grp-head { display:flex; align-items:center; gap:8px; padding:8px 4px; cursor:pointer; user-select:none; }
.rm-pt-grp-head .caret { color:rgba(0,0,0,0.40); font-size:10px; transition:transform 0.15s; }
.rm-pt-group.collapsed .rm-pt-grp-head .caret { transform:rotate(-90deg); }
.rm-pt-group.collapsed .rm-pt-children { display:none; }
.rm-pt-grp-head input[type=checkbox] { accent-color:#149DAA; }
.rm-pt-children { padding-left:30px; display:flex; flex-direction:column; gap:2px; }
.rm-pt-leaf { display:flex; align-items:center; gap:8px; padding:7px 10px; border-radius:6px; cursor:pointer; color:rgba(0,0,0,0.72); }
.rm-pt-leaf:hover { background:#f7fafa; }
.rm-pt-leaf.active { background:#EAF7F8; color:#0B6B78; font-weight:500; }
.rm-pt-leaf input[type=checkbox] { accent-color:#149DAA; }
.rm-api h4 { margin:0 0 12px; font-size:15px; font-weight:600; color:rgba(0,0,0,0.85); }
.rm-api .sub-ttl { font-size:12.5px; color:rgba(0,0,0,0.50); margin-bottom:10px; }
.rm-api-tabs { display:flex; gap:0; border-bottom:1px solid #f0f0f0; margin-bottom:12px; padding-bottom:0; }
.rm-api-tab { padding:8px 18px 12px; font-size:13.5px; color:rgba(0,0,0,0.55); cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-1px; user-select:none; letter-spacing:0.4px; }
.rm-api-tab:hover { color:#149DAA; }
.rm-api-tab.active { color:#149DAA; border-bottom-color:#149DAA; font-weight:600; }
.rm-api .empty { padding:48px 12px; text-align:center; color:rgba(0,0,0,0.35); font-size:13px; }
.rm-foot { display:flex; justify-content:flex-end; margin-top:18px; }
.rm-foot .btn-primary { padding:7px 28px; }

/* ── 通用 toggle switch ── */
.toggle-sw { position:relative; display:inline-block; width:34px; height:18px; flex:none; }
.toggle-sw input { opacity:0; width:0; height:0; }
.toggle-sw .slider { position:absolute; cursor:pointer; inset:0; background:#cfd6db; border-radius:34px; transition:0.2s; }
.toggle-sw .slider::before { position:absolute; content:''; height:14px; width:14px; left:2px; top:2px; background:#fff; border-radius:50%; transition:0.2s; box-shadow:0 1px 3px rgba(0,0,0,0.20); }
.toggle-sw input:checked + .slider { background:#149DAA; }
.toggle-sw input:checked + .slider::before { transform:translateX(16px); }

/* ── 资源管理 ── */
.res-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.res-card { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:20px; }
.res-card h3 { margin:0 0 4px; font-size:16px; font-weight:600; color:rgba(0,0,0,0.85); }
.res-card .sub { font-size:12.5px; color:rgba(0,0,0,0.50); margin-bottom:18px; }
.res-topbar { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:14px; }
.res-card-grid { display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:14px; margin-bottom:18px; }
.res-over-card { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:16px 18px; min-width:0; }
.res-over-card .k { font-size:12.5px; color:rgba(0,0,0,0.50); margin-bottom:8px; }
.res-over-card .v { font-size:25px; line-height:1.1; font-weight:600; color:rgba(0,0,0,0.86); font-family:'SF Mono',Menlo,monospace; white-space:nowrap; }
.res-over-card .s { margin-top:8px; font-size:12px; color:rgba(0,0,0,0.42); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.res-group-head { display:flex; align-items:center; justify-content:space-between; gap:14px; margin:20px 0 12px; }
.res-group-head h3 { margin:0; font-size:16px; color:rgba(0,0,0,0.85); font-weight:600; }
.res-quota { display:flex; flex-direction:column; gap:6px; min-width:170px; }
.res-quota-line { display:grid; grid-template-columns:54px 1fr 58px; gap:8px; align-items:center; font-size:12px; color:rgba(0,0,0,0.54); }
.res-quota-line .track { height:6px; background:#eef0f2; border-radius:3px; overflow:hidden; }
.res-quota-line .fill { display:block; height:100%; border-radius:3px; background:#149DAA; }
.res-quota-line .fill.warn { background:#E29845; }
.res-stat-row { display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin-bottom:18px; }
.res-stat { padding:14px; background:#fafbfc; border-radius:8px; }
.res-stat .l { font-size:12px; color:rgba(0,0,0,0.50); }
.res-stat .v { font-size:22px; font-weight:600; color:rgba(0,0,0,0.85); margin-top:4px; font-family:'SFMono-Regular',Consolas,monospace; }
.res-stat .v.warn { color:#E29845; }
.res-stat .v.ok { color:#3DC470; }
.res-bd-row { display:flex; align-items:center; gap:14px; margin-bottom:12px; }
.res-bd-row:last-child { margin-bottom:0; }
.res-bd-nm { width:120px; flex:none; font-size:13px; color:rgba(0,0,0,0.78); }
.res-bd-bar { flex:1; height:8px; background:#eef0f2; border-radius:4px; overflow:hidden; }
.res-bd-bar > div { height:100%; background:#149DAA; border-radius:4px; }
.res-bd-bar > div.warn { background:#E29845; }
.res-bd-meta { width:140px; flex:none; font-size:12.5px; color:rgba(0,0,0,0.55); font-family:'SFMono-Regular',Consolas,monospace; text-align:right; }

/* ── 租户管理 · 队列管理 ── */
.queue-layout { display:grid; grid-template-columns:minmax(0, 1fr) 340px; gap:18px; align-items:start; }
.queue-layout.queue-layout-single { grid-template-columns:minmax(0, 1fr); }
.drawer.drawer-queue { width:1080px; max-width:88vw; }
.drawer.drawer-queue .drawer-body { background:#f5f7fa; }
.queue-main, .queue-summary { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:22px 24px; }
.queue-section { margin-bottom:28px; }
.queue-section:last-child { margin-bottom:0; }
.queue-sec-title { display:flex; align-items:center; gap:8px; font-size:16px; font-weight:600; color:rgba(0,0,0,0.86); margin:0 0 18px; }
.queue-sec-title::before { content:''; width:3px; height:18px; border-radius:2px; background:#149DAA; display:inline-block; }
.queue-form-row { display:grid; grid-template-columns:120px minmax(0, 1fr); gap:16px; align-items:flex-start; margin-bottom:16px; }
.queue-form-row label { font-size:13.5px; color:rgba(0,0,0,0.72); padding-top:8px; }
.queue-form-row label.req::after { content:'*'; color:#cf1322; margin-left:4px; }
.queue-input, .queue-select, .queue-textarea { width:100%; box-sizing:border-box; border:1px solid #dfe3e8; border-radius:6px; background:#fff; color:rgba(0,0,0,0.82); font-size:14px; outline:none; }
.queue-input, .queue-select { height:38px; padding:0 12px; }
.queue-select[multiple] { height:auto; min-height:88px; padding:8px 12px; }
.queue-textarea { min-height:64px; padding:10px 12px; resize:vertical; font-family:inherit; }
.queue-input:focus, .queue-select:focus, .queue-textarea:focus { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.10); }
.remote-picker { border:1px solid #dfe3e8; border-radius:6px; background:#fff; min-height:38px; padding:5px 8px; display:flex; align-items:center; gap:6px; flex-wrap:wrap; box-sizing:border-box; }
.remote-picker:focus-within { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.10); }
.remote-picker .picked { display:inline-flex; align-items:center; gap:6px; height:26px; padding:0 8px; border:1px solid #dfe3e8; border-radius:5px; background:#f7f8fa; color:rgba(0,0,0,0.70); font-size:12.5px; }
.remote-picker .picked i { font-style:normal; color:rgba(0,0,0,0.35); cursor:pointer; }
.remote-picker input { flex:1; min-width:150px; height:26px; border:0; outline:none; padding:0 4px; font-size:13px; font-family:inherit; }
.queue-chip { display:inline-flex; align-items:center; gap:6px; height:28px; padding:0 9px; border:1px solid #e5e7eb; border-radius:6px; background:#f7f8fa; color:rgba(0,0,0,0.68); font-size:13px; }
.queue-table { border:1px solid #f0f0f0; border-radius:8px; overflow:hidden; }
.queue-table table { width:100%; border-collapse:collapse; font-size:13.5px; }
.queue-table th { background:#f7f8fa; color:rgba(0,0,0,0.72); text-align:left; font-weight:600; padding:12px 14px; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.queue-table td { padding:12px 14px; border-bottom:1px solid #f5f5f5; color:rgba(0,0,0,0.68); }
.queue-table tr:last-child td { border-bottom:none; }
.queue-num { width:92px; height:30px; border:1px solid #dfe3e8; border-radius:6px; padding:0 8px; font-size:13px; box-sizing:border-box; }
.queue-help { margin:10px 0 0 120px; font-size:12px; color:rgba(0,0,0,0.42); }
.queue-summary-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:18px; }
.queue-summary-head h3 { margin:0; font-size:16px; font-weight:600; color:rgba(0,0,0,0.86); display:flex; align-items:center; gap:8px; }
.queue-summary-head h3::before { content:''; width:3px; height:18px; border-radius:2px; background:#149DAA; display:inline-block; }
.queue-clear { font-size:12.5px; color:rgba(0,0,0,0.45); cursor:pointer; }
.queue-sum-list { display:flex; flex-direction:column; gap:10px; }
.queue-sum-item { display:flex; justify-content:space-between; align-items:center; padding:11px 12px; background:#fafbfc; border:1px solid #f0f0f0; border-radius:8px; }
.queue-sum-item span { font-size:12.5px; color:rgba(0,0,0,0.5); }
.queue-sum-item b { font-size:13.5px; color:rgba(0,0,0,0.82); font-family:'SF Mono',Menlo,monospace; }
.queue-foot { position:sticky; bottom:0; display:flex; justify-content:flex-end; gap:10px; margin-top:18px; padding:14px 0 0; background:#f5f7fa; }
.queue-status { display:inline-flex; align-items:center; gap:5px; font-size:13px; }
.queue-status::before { content:''; width:7px; height:7px; border-radius:50%; display:inline-block; }
.queue-status.active { color:#389e0d; }
.queue-status.active::before { background:#52c41a; }
.queue-status.paused { color:#8c8c8c; }
.queue-status.paused::before { background:#bfbfbf; }
.queue-name-link { color:#149DAA; font-weight:600; text-decoration:none; }
.queue-name-link:hover { color:#0F8190; }
.queue-detail { display:flex; flex-direction:column; gap:18px; }
.queue-detail-section { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:18px 20px; }
.queue-detail-section h3 { margin:0 0 14px; font-size:16px; font-weight:600; color:rgba(0,0,0,0.86); display:flex; align-items:center; gap:8px; }
.queue-detail-section h3::before { content:''; width:3px; height:16px; border-radius:2px; background:#149DAA; display:inline-block; }
.queue-info-grid { display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:14px 24px; }
.queue-info-item span { display:block; font-size:12.5px; color:rgba(0,0,0,0.46); margin-bottom:5px; }
.queue-info-item b { display:block; font-size:13.5px; color:rgba(0,0,0,0.84); font-weight:500; word-break:break-word; }
.queue-member-add { display:grid; grid-template-columns:1fr 140px 96px; gap:10px; align-items:center; margin-bottom:14px; }
.device-detail-pane, .dev-record-pane { display:none; }
.device-detail-pane.active, .dev-record-pane.active { display:block; }
.device-detail-pane .queue-detail-section + .queue-detail-section { margin-top:16px; }
.device-version-list { display:flex; flex-direction:column; gap:8px; }
.device-version-list b { display:block; font-size:13.5px; color:rgba(0,0,0,0.84); font-weight:500; word-break:break-word; }

/* ── 数据平台 · 工作台 · 标注 editor ── */
.lab-meta { background:#1f2933; color:rgba(255,255,255,0.92); padding:11px 18px; border-radius:8px; display:flex; flex-wrap:wrap; gap:8px 22px; align-items:center; font-size:13px; margin-bottom:10px; }
.lab-meta .lf { display:inline-flex; align-items:center; gap:6px; }
.lab-meta .lf .lbl { color:rgba(255,255,255,0.55); font-size:12.5px; }
.lab-meta .lf .val { color:#fff; font-weight:500; }
.lab-meta .lf.mono .val { font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace; }
.lab-meta .grow { flex:1; }
.lab-meta .ver { display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.08); padding:4px 12px; border-radius:6px; cursor:pointer; font-size:12.5px; }
.lab-meta .ver:hover { background:rgba(255,255,255,0.14); }
.lab-meta .ver .caret { font-size:9px; opacity:0.55; }
.lab-meta .status-pass { background:#3DC470; color:#fff; padding:3px 12px; border-radius:6px; font-size:12px; font-weight:500; letter-spacing:0.5px; }
.lab-vid-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; background:#0d0d0d; padding:6px; border-radius:8px; margin-bottom:14px; position:relative; }
.lab-vid { background:linear-gradient(135deg,#262b31,#1c2025); border-radius:6px; position:relative; min-height:300px; display:flex; align-items:center; justify-content:center; color:rgba(255,255,255,0.18); font-size:32px; overflow:hidden; }
.lab-vid .vid-label { position:absolute; top:10px; left:14px; color:#fff; font-size:12.5px; z-index:2; padding:0; background:transparent; }
.lab-vid .vid-expand { position:absolute; top:10px; right:14px; color:rgba(255,255,255,0.65); font-size:13px; cursor:pointer; z-index:2; }
.lab-fab { position:absolute; right:14px; bottom:14px; width:38px; height:38px; border-radius:50%; background:#1F8AC9; color:#fff; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 12px rgba(0,0,0,0.4); cursor:pointer; z-index:3; }
.lab-fab:hover { background:#176aa0; }
.lab-tools-card { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:14px 18px 12px; margin-bottom:14px; }
.lab-timeline { position:relative; padding:0; }
.lab-tl-ticks { position:relative; height:16px; margin-bottom:6px; font-size:11px; color:rgba(0,0,0,0.45); font-family:'SFMono-Regular',Consolas,monospace; }
.lab-tl-tick { position:absolute; transform:translateX(-50%); }
.lab-tl-bar { position:relative; height:14px; margin-bottom:6px; background:#eef0f2; border-radius:7px; overflow:hidden; }
.lab-tl-bar:last-child { margin-bottom:0; }
.lab-tl-seg { position:absolute; top:0; bottom:0; }
.lab-tl-seg.orange { background:#F5A623; }
.lab-tl-seg.red { background:#E45A52; }
.lab-tl-seg.purple { background:#8B47C7; }
.lab-tl-pin { position:absolute; top:-3px; transform:translateX(-50%); color:#5D4A8C; font-size:16px; line-height:1; pointer-events:none; }
.lab-tools { display:flex; align-items:center; justify-content:center; padding-top:10px; margin-top:8px; border-top:1px solid #f5f5f5; gap:14px; position:relative; }
.lab-tools-left { display:flex; align-items:center; gap:4px; }
.lab-tools .lab-tools-right { position:absolute; right:0; top:50%; transform:translateY(-50%); margin-top:5px; }
.lab-tool { display:inline-flex; align-items:center; justify-content:center; width:30px; height:30px; border-radius:6px; cursor:pointer; color:rgba(0,0,0,0.65); transition:all 0.15s; font-size:13px; user-select:none; }
.lab-tool:hover { background:#f5f7fa; color:#149DAA; }
.lab-tool.danger:hover { color:#e25c5c; background:#fff0f0; }
.lab-tool.play { background:#149DAA; color:#fff; width:32px; height:32px; border-radius:50%; margin:0 4px; }
.lab-tool.play:hover { background:#0F8190; color:#fff; }
.lab-speed { padding:0 8px; font-size:13px; color:rgba(0,0,0,0.55); user-select:none; }
.lab-tools-right { display:inline-flex; align-items:center; gap:6px; color:#149DAA; font-size:13px; cursor:pointer; text-decoration:none; }
.lab-tools-right:hover { color:#0F8190; }
.lab-tbl { background:#fff; border:1px solid #f0f0f0; border-radius:10px; overflow:hidden; margin-bottom:14px; }
.lab-tbl table { width:100%; border-collapse:separate; border-spacing:0; }
.lab-tbl th { padding:12px 14px; font-size:12.5px; color:rgba(0,0,0,0.55); font-weight:500; text-align:left; background:#fafbfc; border-bottom:1px solid #f0f0f0; }
.lab-tbl td { padding:14px 14px; font-size:13px; color:rgba(0,0,0,0.78); border-bottom:1px solid #f5f5f5; vertical-align:middle; }
.lab-tbl tr:last-child td { border-bottom:none; }
.lab-tbl .color-chip { width:20px; height:20px; border-radius:3px; display:inline-block; vertical-align:middle; }
.lab-tbl select.mock, .lab-tbl input.mock { width:100%; height:32px; padding:0 28px 0 12px; font-size:13px; color:rgba(0,0,0,0.55); border:1px solid #e2e4e8; border-radius:6px; background:#fff; box-sizing:border-box; appearance:none; cursor:pointer; }
.lab-tbl select.mock { background-image:linear-gradient(45deg, transparent 50%, rgba(0,0,0,0.4) 50%), linear-gradient(135deg, rgba(0,0,0,0.4) 50%, transparent 50%); background-position:calc(100% - 14px) 50%, calc(100% - 9px) 50%; background-size:5px 5px, 5px 5px; background-repeat:no-repeat; }
.lab-tbl input.mock { padding:0 12px; color:rgba(0,0,0,0.78); cursor:text; }
.lab-act-cell { display:flex; align-items:center; justify-content:center; gap:6px; }
.lab-tbl .nowrap { white-space:nowrap; }
.lab-act-btn { display:inline-flex; align-items:center; justify-content:center; width:30px; height:30px; border-radius:6px; color:#fff; cursor:pointer; border:none; font-size:14px; }
.lab-act-btn.blue { background:#149DAA; } .lab-act-btn.blue:hover { background:#0F8190; }
.lab-act-btn.orange { background:#F39C12; } .lab-act-btn.orange:hover { background:#D88A0B; }
.lab-act-btn.red { background:#E25C5C; } .lab-act-btn.red:hover { background:#C44949; }
.lab-foot { display:flex; justify-content:center; gap:14px; padding:6px 0 8px; }
.lab-foot .btn { padding:8px 28px; font-size:14px; min-width:120px; justify-content:center; }
.lab-foot .btn-primary { background:#149DAA; color:#fff; border-color:#149DAA; }
.lab-foot .btn-primary:hover { background:#0F8190; border-color:#0F8190; }

/* ── 设备预约: 占用看板 tab + Gantt ── */
.bk-tabs { display:flex; border-bottom:1px solid #f0f0f0; margin:0 2px 18px; padding:0 4px; gap:4px; }
.bk-tab { padding:11px 18px; font-size:14px; color:rgba(0,0,0,0.65); cursor:pointer; border:none; background:none; border-bottom:2px solid transparent; margin-bottom:-1px; user-select:none; }
.bk-tab:hover { color:#149DAA; }
.bk-tab.active { color:#149DAA; border-bottom-color:#149DAA; font-weight:500; }
.bk-pane { display:none; }
.bk-pane.active { display:block; }
.occ-board { background:#fff; border:1px solid #f0f0f0; border-radius:10px; overflow:hidden; }
.ob-scroll { overflow-x:auto; }
.ob-head { display:flex; height:36px; background:#fafafa; border-bottom:1px solid #f0f0f0; font-size:12.5px; color:rgba(0,0,0,0.55); }
.ob-th-dev { padding:0 16px; height:36px; display:flex; align-items:center; font-weight:500; width:160px; flex:none; background:#fafafa; position:sticky; left:0; z-index:2; border-right:1px solid #f0f0f0; }
.ob-th-timeline { display:flex; align-items:center; flex:none; }
.ob-tick { width:70px; flex:none; padding-left:8px; font-size:11.5px; color:rgba(0,0,0,0.45); box-sizing:border-box; }
.ob-row { display:flex; min-height:62px; border-bottom:1px solid #f5f5f5; }
.ob-row:last-child { border-bottom:none; }
.ob-dev { padding:10px 16px; display:flex; flex-direction:column; gap:3px; border-right:1px solid #f0f0f0; box-sizing:border-box; width:160px; flex:none; background:#fff; position:sticky; left:0; z-index:1; }
.ob-dev-name { font-size:13.5px; font-weight:500; color:rgba(0,0,0,0.85); font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace; }
.ob-dev-meta { font-size:11.5px; color:rgba(0,0,0,0.45); }
.ob-track { position:relative; flex:none; min-height:62px; background-image:linear-gradient(to right, #f5f5f5 1px, transparent 1px); background-size:70px 100%; }
.ob-block { position:absolute; top:6px; bottom:6px; padding:6px 10px; background:rgba(20,157,170,0.10); border:1px solid rgba(20,157,170,0.40); border-left:3px solid #149DAA; border-radius:4px; overflow:hidden; cursor:pointer; box-sizing:border-box; }
.ob-block.pending { background:rgba(245,180,70,0.12); border:1px solid rgba(245,180,70,0.50); border-left:3px solid #E29845; }
.ob-block:hover { box-shadow:0 2px 6px rgba(20,157,170,0.25); }
.ob-bk-ttl { font-size:12.5px; color:#0B6B78; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; line-height:1.3; }
.ob-bk-user { font-size:11.5px; color:rgba(0,0,0,0.55); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-top:1px; }
.ob-block.pending .ob-bk-ttl { color:#A05B0F; }

/* ── 采集任务: 表格里的圆角开关 ── */
.ct-switch { position:relative; display:inline-block; width:38px; height:20px; cursor:pointer; }
.ct-switch input { opacity:0; width:0; height:0; }
.ct-switch .ct-slider { position:absolute; inset:0; background:#d9d9d9; border-radius:11px; transition:0.2s; }
.ct-switch .ct-slider::before { content:''; position:absolute; left:2px; top:2px; width:16px; height:16px; background:#fff; border-radius:50%; transition:0.2s; }
.ct-switch input:checked + .ct-slider { background:#149DAA; }
.ct-switch input:checked + .ct-slider::before { transform:translateX(18px); }

/* ── 数据管理: 视频缩略图 (头部 / 左臂 / 右臂) ── */
.vid-thumb { width:106px; height:64px; background:linear-gradient(135deg,#3a4555,#1f2733); border-radius:6px; display:inline-block; vertical-align:middle; position:relative; overflow:hidden; }
.vid-thumb::before { content:'▶'; position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); color:rgba(255,255,255,0.5); font-size:14px; }
.vid-thumb + .vid-thumb { margin-left:6px; }

/* ── 评测结果页 (er): tabs + 内容融为一体的卡片 ── */
.er-wrap { background:#fff; border:1px solid #f0f0f0; border-radius:10px; overflow:hidden; }
.er-wrap .er-tabs { background:transparent; border:none; border-radius:0; border-bottom:1px solid #f0f0f0; margin:0; padding:0 18px; }
.er-wrap .det-tab { padding:14px 20px; font-size:14.5px; }
.er-wrap .det-pane { padding:18px 22px 22px; }
.er-wrap .det-pane.active { animation:fadeInUp 0.18s ease; }
@keyframes fadeInUp { from { opacity:0; transform:translateY(2px); } to { opacity:1; transform:none; } }
/* 排行榜 / 结果数据 顶部如果有 grid 满高度 (calc(100vh - 160px)), 在 tab 下会撑出长条空白, 收紧一下 */
.er-wrap [style*="height:calc(100vh - 160px)"] { height:auto !important; min-height:560px; }

/* 结果数据页内的二级 tab (评测任务视角 / Checkpoint 视角) */
.er-subtabs { display:inline-flex; gap:0; padding:3px; background:#f5f7fa; border-radius:8px; margin-bottom:18px; }
.er-subtab { padding:7px 18px; font-size:13.5px; color:rgba(0,0,0,0.6); text-decoration:none; border-radius:6px; transition:all 0.15s; }
.er-subtab:hover { color:#149DAA; background:rgba(20,157,170,0.06); }
.er-subtab.active { color:#149DAA; background:#fff; font-weight:500; box-shadow:0 1px 3px rgba(0,0,0,0.06); }

/* ── Trial 内 3 个子 tab (Checkpoint / 日志 / 时间线) ── */
.ts-tabs { display:flex; gap:2px; background:#fff; padding:0 20px; border:1px solid #f0f0f0; border-radius:8px; margin-bottom:14px; }
.ts-tab { padding:11px 16px; font-size:13.5px; color:rgba(0,0,0,0.65); cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-1px; user-select:none; }
.ts-tab:hover { color:#149DAA; }
.ts-tab.active { color:#149DAA; border-bottom-color:#149DAA; font-weight:500; }
.ts-pane { display:none; }
.ts-pane.active { display:block; }

/* ── 实验数据: charts grid ── */
.metric-row { display:flex; align-items:center; gap:14px; margin-bottom:12px; }
.metric-row .mr-group { font-size:14px; color:rgba(0,0,0,0.78); font-weight:500; display:flex; align-items:center; gap:4px; }
.metric-row .mr-pill { padding:4px 12px; font-size:13px; border-radius:5px; cursor:pointer; color:rgba(0,0,0,0.62); border:1px solid transparent; }
.metric-row .mr-pill.active { color:#149DAA; background:#DEF6F9; border-color:#7BD8DF; }
.metric-row .mr-pill.dim { color:rgba(0,0,0,0.32); cursor:default; }
.metric-row input.mr-search { height:34px; padding:0 12px; border:1px solid #d9d9d9; border-radius:6px; font-size:13px; width:280px; outline:none; }
.metric-row input.mr-search:focus { border-color:#149DAA; }
.metric-row .mr-right { margin-left:auto; display:flex; gap:8px; align-items:center; color:rgba(0,0,0,0.45); }
.charts-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:14px; }
@media (max-width: 1280px){ .charts-grid { grid-template-columns:repeat(3, 1fr); } }
@media (max-width: 980px){ .charts-grid { grid-template-columns:repeat(2, 1fr); } }
.chart-card { background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:12px 14px 10px; }
.chart-title { font-size:13px; color:rgba(0,0,0,0.7); margin-bottom:4px; }
.chart-body { height:170px; }
.chart-body svg { width:100%; height:100%; }
.chart-foot { font-size:11px; color:rgba(0,0,0,0.4); text-align:center; margin-top:6px; display:flex; align-items:center; justify-content:center; gap:6px; }
.chart-foot .dot { width:10px; height:2px; background:#F08080; border-radius:1px; display:inline-block; }

/* ── 日志 ── */
.logs-pane { background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:14px 18px 18px; }
.logs-subtabs { display:flex; gap:6px; margin-bottom:18px; }
.ls-tab { height:30px; display:inline-flex; align-items:center; padding:0 13px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; font-size:13px; color:rgba(0,0,0,0.58); cursor:pointer; user-select:none; }
.ls-tab:hover { color:#149DAA; border-color:#149DAA; }
.ls-tab.active { color:#149DAA; font-weight:500; background:#EBF8FA; border-color:#B5E5EA; }
.log-subpane { display:none; }
.log-subpane.active { display:block; }
.logs-controls { display:flex; align-items:center; gap:10px; padding:10px 16px; border-bottom:1px solid #f0f0f0; margin-bottom:0; flex-wrap:wrap; }
.lc-pill { font-size:12px; height:26px; display:inline-flex; align-items:center; padding:0 12px; border-radius:5px; background:#EBF8FA; color:#149DAA; border:1px solid #B5E5EA; font-weight:500; }
.lc-grp { display:flex; align-items:center; gap:8px; font-size:13px; color:rgba(0,0,0,0.65); }
.lc-grp select { height:30px; padding:0 28px 0 10px; border:1px solid #d9d9d9; border-radius:6px; font-size:13px; background:#fff; min-width:140px; outline:none; }
.lc-grp select:focus { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.12); }
.lc-btn { height:30px; display:inline-flex; align-items:center; gap:5px; padding:0 12px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; color:rgba(0,0,0,0.66); font-size:13px; text-decoration:none; cursor:pointer; }
.lc-btn:hover { border-color:#149DAA; color:#149DAA; }
.lc-link { height:30px; display:inline-flex; align-items:center; color:#149DAA; font-size:13px; text-decoration:none; }
.lc-right { margin-left:auto; display:flex; align-items:center; gap:10px; font-size:13px; color:rgba(0,0,0,0.65); flex-wrap:wrap; }
.lc-right input.lc-num { width:64px; height:30px; padding:0 8px; border:1px solid #d9d9d9; border-radius:5px; font-size:13px; text-align:center; outline:none; }
.lc-toggle { display:inline-block; width:30px; height:16px; border-radius:8px; background:#d9d9d9; position:relative; cursor:pointer; vertical-align:middle; }
.lc-toggle.on { background:#149DAA; }
.lc-toggle::after { content:''; position:absolute; top:2px; left:2px; width:12px; height:12px; border-radius:50%; background:#fff; transition:transform 0.15s; }
.lc-toggle.on::after { transform:translateX(14px); }
.lc-icon { width:28px; height:28px; display:inline-flex; align-items:center; justify-content:center; color:rgba(0,0,0,0.55); border:1px solid #e5e7eb; border-radius:4px; cursor:pointer; background:#fff; }
.lc-icon:hover { color:#149DAA; border-color:#149DAA; background:#f5f7fa; }
.logs-body { background:#fafbfc; border:0; border-radius:0; padding:14px 16px; font-family:'SF Mono',Menlo,monospace; font-size:12px; line-height:1.7; color:rgba(0,0,0,0.85); max-height:620px; overflow:auto; white-space:pre; margin:0; }
.logs-box { border:1px solid #e5e7eb; border-radius:6px; overflow:hidden; background:#fafbfc; }
.logs-empty { min-height:260px; display:flex; flex-direction:column; align-items:center; justify-content:center; color:rgba(0,0,0,0.45); font-size:13px; border:1px solid #e5e7eb; border-top:0; border-radius:0 0 6px 6px; background:#fff; padding:0 16px; box-sizing:border-box; }
.logs-empty .emp-icon { width:54px; height:68px; border:1px solid #e5e7eb; border-radius:6px; background:#fafbfc; color:#9aa5b1; display:flex; align-items:center; justify-content:center; font-size:12px; margin-bottom:10px; }
.logs-pager { display:flex; justify-content:flex-end; gap:8px; padding:10px 0 0; align-items:center; color:rgba(0,0,0,0.55); font-size:12px; }
.logs-pager .pg-btn { width:28px; height:28px; border:1px solid #d9d9d9; border-radius:5px; background:#fff; display:inline-flex; align-items:center; justify-content:center; cursor:pointer; color:rgba(0,0,0,0.55); }
.logs-pager .pg-btn.active { border-color:#149DAA; color:#149DAA; }
.logs-pager select { height:28px; padding:0 10px; border:1px solid #d9d9d9; border-radius:5px; background:#fff; font-size:12px; outline:none; }

/* ── 时间线 ── */
.timeline-pane { background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:20px 28px 28px; }
.tl-section-title { font-size:14px; font-weight:500; color:rgba(0,0,0,0.85); margin:0 0 22px; display:flex; align-items:center; gap:8px; }
.tl-section-title .tl-ic { width:18px; height:18px; border-radius:50%; background:#149DAA; color:#fff; display:inline-flex; align-items:center; justify-content:center; font-size:11px; }
.tl-events { display:flex; flex-direction:column; gap:30px; padding-left:8px; }
.tl-evt { display:flex; gap:14px; position:relative; }
.tl-evt:not(:last-child)::before { content:''; position:absolute; left:5px; top:18px; width:1px; height:calc(100% + 18px); background:#e5e7eb; }
.tl-dot { width:12px; height:12px; border-radius:50%; flex:none; margin-top:4px; background:#bfbfbf; }
.tl-dot.running { background:#149DAA; }
.tl-dot.done { background:#52c41a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:9px; line-height:1; }
.tl-name { font-size:14px; color:rgba(0,0,0,0.85); margin-bottom:6px; }
.tl-meta { font-size:12.5px; color:rgba(0,0,0,0.5); display:flex; gap:24px; }

/* ── 基础信息 (详情样式 - 非禁用输入) ── */
.basic-info { background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:24px 28px; }
.bi-section { margin-bottom:22px; }
.bi-section .bi-label { font-size:13px; color:rgba(0,0,0,0.5); margin-bottom:6px; }
.bi-section .bi-value { font-size:14px; color:rgba(0,0,0,0.85); word-break:break-all; line-height:1.6; }
.bi-section .bi-value.code { font-family:'SF Mono',Menlo,monospace; font-size:13px; }
.bi-row { display:flex; gap:48px; }
.bi-row > .bi-section { flex:1; margin-bottom:22px; }
.bi-dstable { border:1px solid #f0f0f0; border-radius:8px; overflow:hidden; }
.bi-dstable .ds-head, .bi-dstable .ds-row { display:grid; grid-template-columns:1fr 100px; padding:10px 14px; gap:8px; align-items:center; font-size:13px; }
.bi-dstable .ds-head { background:#fafafa; color:rgba(0,0,0,0.7); border-bottom:1px solid #f0f0f0; font-weight:500; }
.yaml-readonly { background:#fafbfc; border:1px solid #e5e7eb; border-radius:8px; padding:14px 16px; font-family:'SF Mono',Menlo,monospace; font-size:12.5px; line-height:1.65; color:rgba(0,0,0,0.85); white-space:pre; overflow:auto; max-height:420px; margin:0; }
"""

# 将 data_platform / quanta_eval_platform 的 BASE_CSS 拼在前面 — 它们的 chrome 规则会被
# 我们后定义的 Quanta 规则覆盖, 但内容类规则 (.tree-panel / .q-filters / .ep-* / .seg-* /
# .tg / 评测平台的卡片样式 等) 会保留下来供子模块使用.
_extra_css_parts = []
if DP_AVAILABLE:
    _extra_css_parts.append("/* ── data_platform CSS ── */\n" + dp.BASE_CSS)
if EP_AVAILABLE:
    _extra_css_parts.append("/* ── quanta_eval_platform CSS ── */\n" + ep.BASE_CSS)
if _extra_css_parts:
    BASE_CSS = "\n\n".join(_extra_css_parts) + "\n\n/* ════ Quanta chrome overrides ════ */\n" + BASE_CSS


# 从两个原 BASE_TEMPLATE 里抽出内联 <script> 块, 后面注入到我们的模板里,
# 这样 dp 的 switchTab/toggleTP/epTab、ep 的 openModal/closeModal/expand-btn 监听等
# 都可以在我们的 chrome 下正常工作.
def _extract_inline_script(tmpl):
    if not tmpl:
        return ""
    m = re.search(r'<script>(.*?)</script>', tmpl, re.DOTALL)
    return m.group(1).strip() if m else ""


DP_INLINE_JS = _extract_inline_script(dp.BASE_TEMPLATE) if DP_AVAILABLE else ""
EP_INLINE_JS = _extract_inline_script(ep.BASE_TEMPLATE) if EP_AVAILABLE else ""

BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} - Quanta</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/antd@4.24.16/dist/antd.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/lib/codemirror.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/theme/material-darker.min.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/lib/codemirror.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/sql/sql.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/javascript/javascript.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/yaml/yaml.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/shell/shell.min.js"></script>
<style>""" + BASE_CSS + """</style>
</head>
<body>
<header class="top-nav">
  <div class="tn-brand">
    <span class="brand-name">Quanta</span>
    <span class="brand-demo">Demo</span>
  </div>
  <a class="tn-overview {% if portal %}active{% endif %}" href="/">
    <span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="3.5" width="7" height="7" rx="1"/><rect x="13.5" y="3.5" width="7" height="7" rx="1"/><rect x="3.5" y="13.5" width="7" height="7" rx="1"/><rect x="13.5" y="13.5" width="7" height="7" rx="1"/></svg></span>总览
  </a>
  <div class="tn-right">
    <a class="tn-link" href="#" onclick="toast('Demo: 文档');return false;">文档</a>
    <a class="tn-link" href="#" onclick="toast('Demo: 工单');return false;">工单</a>
    <a class="tn-link" href="#" onclick="toast('Demo: 客服');return false;">客服</a>
    <div class="tn-divider"></div>
    <a class="tn-link tn-tenant-admin" href="/tenant" title="租户管理">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><circle cx="12" cy="12" r="2.4"/><path d="M19 12c0-.5-.05-.95-.13-1.4l2-1.55-2-3.45-2.36.95c-.7-.6-1.5-1.05-2.4-1.32L13.7 2.6h-3.4l-.4 2.63c-.9.27-1.7.72-2.4 1.32L5.13 5.6l-2 3.45 2 1.55c-.08.45-.13.9-.13 1.4s.05.95.13 1.4l-2 1.55 2 3.45 2.36-.95c.7.6 1.5 1.05 2.4 1.32l.4 2.63h3.4l.4-2.63c.9-.27 1.7-.72 2.4-1.32l2.36.95 2-3.45-2-1.55c.08-.45.13-.9.13-1.4z"/></svg>
      <span>租户管理</span>
    </a>
    <div class="tn-tenant" onclick="toggleTenantPop(event)">
      <span class="tt-av" id="ttAv">宁</span>
      <span class="tt-name" id="ttName">宁德时代</span>
      <span class="caret">&#9662;</span>
      <div class="tenant-pop" id="tenantPop" onclick="event.stopPropagation()">
        <div class="tp-section">切换租户</div>
        <a class="tp-tenant active" data-tenant="宁德时代" data-av="宁" onclick="selectTenant(this);return false;">
          <span class="tp-av">宁</span>宁德时代<span class="tp-check">&#10003;</span>
        </a>
        <a class="tp-tenant" data-tenant="千寻智能" data-av="千" onclick="selectTenant(this);return false;">
          <span class="tp-av">千</span>千寻智能<span class="tp-check">&#10003;</span>
        </a>
      </div>
    </div>
    <div class="tn-user">J</div>
  </div>
</header>

<div class="q-layout {% if portal %}portal-mode{% endif %}">
  {% if not portal %}
  <aside class="q-sider">
    {% if module != "tenant" %}
    <div class="smh-wrap">
      <div class="smh" onclick="toggleModSwitch()">
        <div class="smh-icon">{{ module_icon|safe }}</div>
        <div class="smh-name">{{ module_name }}</div>
        <span class="smh-caret">&#9662;</span>
      </div>
      <div class="mod-switch" id="modSwitch">{{ mod_switch_html|safe }}</div>
    </div>
    {% endif %}
    {% if device_models %}
    <div class="dev-wrap">
      <div class="dev-label">选择设备</div>
      <div class="smh smh-dev" onclick="toggleDevSwitch()">
        <div class="smh-icon">{{ device_models[0][0] }}</div>
        <div class="smh-name" id="devName">{{ device_models[0] }}</div>
        <span class="smh-caret">&#9662;</span>
      </div>
      <div class="dev-switch" id="devSwitch">
        {% for dm in device_models %}
        <a class="ms-item {% if loop.first %}active{% endif %}" onclick="selectDev(this, '{{ dm }}')">{{ dm }}</a>
        {% endfor %}
      </div>
    </div>
    {% endif %}
    <nav class="sider-nav">
      {% for group_label, items in module_nav %}
      <div class="sn-label">{{ group_label }}</div>
      {% for entry in items %}
      {% set _badge = entry[3] if entry|length > 3 else None %}
      <a href="{{ entry[0] }}" class="sn-item {% if active==entry[0] %}active{% endif %}"><span class="ic">{{ entry[2]|safe }}</span>{{ entry[1] }}{% if _badge %}<span class="sn-tag{% if _badge == '新增' %} t-new{% elif _badge == '优化' %} t-opt{% elif _badge == '待定' %} t-tbd{% endif %}">{{ _badge }}</span>{% endif %}</a>
      {% endfor %}
      {% endfor %}
    </nav>
  </aside>
  {% endif %}
  <main class="q-main">
    <div class="q-content">{{ content|safe }}</div>
  </main>
</div>
<div class="q-toast" id="toast"></div>
<div class="drawer-mask" id="drawerMask" onclick="closeDrawer()"></div>
<div class="modal-mask" id="taskCapabilityModalMask" onclick="closeTaskCapabilityModal()">
  <div class="modal" onclick="event.stopPropagation()">
    <div class="modal-head">
      <h3>能力复用说明</h3>
      <span class="dismiss" onclick="closeTaskCapabilityModal()">&times;</span>
    </div>
    <div class="modal-body">
      <ol style="margin:0;padding-left:20px;color:rgba(0,0,0,0.72);font-size:14px;line-height:1.9;">
        <li>复用当前 TEST、DAgger 能力</li>
        <li>增加 ckpt 对应的训练镜像，端侧选择任务，会自动带出模型和镜像</li>
        <li>TEST、DAgger 支持选择机器（可选），如果选了，会异步发起该机器的 ckpt 部署任务，不选择现场拉</li>
      </ol>
    </div>
    <div class="modal-foot">
      <button class="btn btn-primary" onclick="closeTaskCapabilityModal()">知道了</button>
    </div>
  </div>
</div>
<div class="modal-mask" id="stopExperimentModalMask" onclick="closeStopExperimentModal()">
  <div class="modal" onclick="event.stopPropagation()">
    <div class="modal-head">
      <h3>停止训练任务</h3>
      <span class="dismiss" onclick="closeStopExperimentModal()">&times;</span>
    </div>
    <div class="modal-body">
      <p style="margin:0;color:rgba(0,0,0,0.72);font-size:14px;line-height:1.8;">
        确认停止训练任务「<span id="stopExperimentName" style="font-weight:600;color:rgba(0,0,0,0.86);"></span>」？
      </p>
      <p style="margin:8px 0 0;color:rgba(0,0,0,0.45);font-size:13px;line-height:1.6;">停止后任务将不再继续运行，已产生的日志和 checkpoint 仍可查看。</p>
    </div>
    <div class="modal-foot">
      <button class="btn btn-tertiary" onclick="closeStopExperimentModal()">取消</button>
      <button class="btn btn-primary" onclick="submitStopExperiment()">确认停止</button>
    </div>
  </div>
</div>
<script>
function toast(msg){ var t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show'); setTimeout(function(){t.classList.remove('show');},1500); }
function resetFilters(btn){
  var root = btn.closest('.filter-bar,.fb-labeled,.lin-filter,.q-filters');
  if(!root){ toast('Demo: 已重置'); return; }
  root.querySelectorAll('input, textarea').forEach(function(el){ el.value=''; });
  root.querySelectorAll('select').forEach(function(el){ el.selectedIndex = 0; });
  refreshSelectPlaceholders(root);
  toast('Demo: 已重置');
}
function queryFilters(btn){ toast('Demo: 已查询'); }
function queryDeployFilters(btn){
  var root = btn.closest('.filter-bar,.fb-labeled');
  if(!root){ toast('Demo: 已查询'); return; }
  var params = new URLSearchParams();
  root.querySelectorAll('[name]').forEach(function(el){
    var v = (el.value || '').trim();
    if(v) params.set(el.name, v);
  });
  var url = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
  window.location.href = url;
}
function resetDeployFilters(){
  window.location.href = '/model/deploy';
}
function openRemoteFilter(input){
  document.querySelectorAll('.remote-filter.open').forEach(function(w){
    if(!w.contains(input)) w.classList.remove('open');
  });
  var wrap = input.closest('.remote-filter');
  if(wrap) wrap.classList.add('open');
}
function focusRemoteFilter(control){
  var input = control.querySelector('input[type="text"]');
  if(input) input.focus();
}
function syncRemoteFilterHidden(wrap){
  var hidden = wrap.querySelector('.rf-hidden');
  if(!hidden) return;
  var values = Array.prototype.map.call(wrap.querySelectorAll('.rf-chip'), function(chip){
    return chip.dataset.value || '';
  }).filter(Boolean);
  hidden.value = values.join(',');
}
function addRemoteFilterChip(wrap, value){
  if(wrap.querySelector('.rf-chip[data-value="' + CSS.escape(value) + '"]')) return;
  var chip = document.createElement('span');
  chip.className = 'rf-chip';
  chip.dataset.value = value;
  var text = document.createElement('span');
  text.textContent = value;
  var close = document.createElement('i');
  close.textContent = '×';
  close.onclick = function(ev){ removeRemoteFilterChip(close, ev); };
  chip.appendChild(text);
  chip.appendChild(close);
  var input = wrap.querySelector('.rf-control input[type="text"]');
  input.parentNode.insertBefore(chip, input);
}
function toggleRemoteFilterOption(item){
  var wrap = item.closest('.remote-filter');
  var value = item.dataset.value || '';
  if(!wrap || !value) return;
  var existing = wrap.querySelector('.rf-chip[data-value="' + CSS.escape(value) + '"]');
  if(existing){
    existing.remove();
    item.classList.remove('on');
  } else {
    addRemoteFilterChip(wrap, value);
    item.classList.add('on');
  }
  var input = wrap.querySelector('.rf-control input[type="text"]');
  if(input) input.value = '';
  wrap.querySelectorAll('.rf-option').forEach(function(opt){ opt.style.display=''; });
  syncRemoteFilterHidden(wrap);
}
function removeRemoteFilterChip(close, ev){
  if(ev) ev.stopPropagation();
  var chip = close.closest('.rf-chip');
  var wrap = close.closest('.remote-filter');
  var value = chip ? chip.dataset.value : '';
  if(chip) chip.remove();
  if(wrap && value){
    var item = wrap.querySelector('.rf-option[data-value="' + CSS.escape(value) + '"]');
    if(item) item.classList.remove('on');
    syncRemoteFilterHidden(wrap);
  }
}
function filterRemoteFilterOptions(input){
  var q = (input.value || '').trim().toLowerCase();
  var wrap = input.closest('.remote-filter');
  if(!wrap) return;
  wrap.classList.add('open');
  wrap.querySelectorAll('.rf-option').forEach(function(item){
    item.style.display = item.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
  });
}
document.addEventListener('click', function(e){
  document.querySelectorAll('.remote-filter.open').forEach(function(wrap){
    if(!wrap.contains(e.target)) wrap.classList.remove('open');
  });
  document.querySelectorAll('.ckpt-status-filter.open').forEach(function(wrap){
    if(!wrap.contains(e.target)) wrap.classList.remove('open');
  });
  document.querySelectorAll('.deploy-device-picker.open').forEach(function(wrap){
    if(!wrap.contains(e.target)) wrap.classList.remove('open');
  });
  document.querySelectorAll('.deploy-checkpoint-picker.open').forEach(function(wrap){
    if(!wrap.contains(e.target)) wrap.classList.remove('open');
  });
});
function openTaskCapabilityModal(){
  var m=document.getElementById('taskCapabilityModalMask');
  if(m) m.classList.add('active');
}
function closeTaskCapabilityModal(){
  var m=document.getElementById('taskCapabilityModalMask');
  if(m) m.classList.remove('active');
}
function filterCkptStatus(source, status){
  var wrap = source.closest('.table-wrap');
  if(!wrap) return;
  status = status || '';
  wrap.querySelectorAll('tbody tr[data-status]').forEach(function(row){
    row.style.display = (!status || row.dataset.status === status) ? '' : 'none';
  });
}
function toggleCkptStatusFilter(btn){
  var wrap = btn.closest('.ckpt-status-filter');
  if(!wrap) return;
  document.querySelectorAll('.ckpt-status-filter.open').forEach(function(item){
    if(item !== wrap) item.classList.remove('open');
  });
  wrap.classList.toggle('open');
}
function selectCkptStatusFilter(btn){
  var filter = btn.closest('.ckpt-status-filter');
  if(!filter) return;
  filter.querySelectorAll('.ckpt-status-option').forEach(function(item){ item.classList.remove('active'); });
  btn.classList.add('active');
  filterCkptStatus(filter, btn.getAttribute('data-value') || '');
  filter.classList.remove('open');
}
function openCkptStatusLog(btn){
  var title = btn.getAttribute('data-title') || '日志';
  var log = btn.getAttribute('data-log') || '';
  var titleEl = document.getElementById('ckptStatusLogTitle');
  var bodyEl = document.getElementById('ckptStatusLogBody');
  if(titleEl) titleEl.textContent = title;
  if(bodyEl) bodyEl.textContent = log;
  var m = document.getElementById('ckptStatusLogModalMask');
  if(m) m.classList.add('active');
}
function closeCkptStatusLog(){
  var m = document.getElementById('ckptStatusLogModalMask');
  if(m) m.classList.remove('active');
}
function confirmStopExperiment(name){
  var nameEl=document.getElementById('stopExperimentName');
  if(nameEl) nameEl.textContent=name;
  var m=document.getElementById('stopExperimentModalMask');
  if(m) m.classList.add('active');
}
function closeStopExperimentModal(){
  var m=document.getElementById('stopExperimentModalMask');
  if(m) m.classList.remove('active');
}
function submitStopExperiment(){
  closeStopExperimentModal();
  toast('Demo: 已提交停止任务');
}
function isPlaceholderSelectValue(sel){
  if(!sel) return false;
  var opt = sel.options[sel.selectedIndex];
  if(!opt) return false;
  var txt = (opt.textContent || '').trim();
  return opt.disabled || opt.value === '' || /^请选择/.test(txt) || /^全部/.test(txt) || txt === '镜像名称' || txt === '镜像版本';
}
function refreshSelectPlaceholderState(sel){ sel.classList.toggle('select-empty', isPlaceholderSelectValue(sel)); }
function refreshSelectPlaceholders(root){
  (root || document).querySelectorAll('select').forEach(refreshSelectPlaceholderState);
}
document.addEventListener('DOMContentLoaded', function(){ refreshSelectPlaceholders(document); });
document.addEventListener('change', function(e){
  if(e.target && e.target.tagName === 'SELECT') refreshSelectPlaceholderState(e.target);
}, true);
function openDrawer(id){ document.getElementById('drawerMask').classList.add('active'); var d=document.getElementById(id); if(d) d.classList.add('active'); }
function closeDrawer(){ document.getElementById('drawerMask').classList.remove('active'); document.querySelectorAll('.drawer.active').forEach(function(d){d.classList.remove('active');}); }
function openCacheModal(step, location){
  var m=document.getElementById('cacheModalMask'); if(!m) return;
  var head=document.getElementById('cacheModalHead'); if(head) head.style.display='flex';
  var stepEl=document.getElementById('cacheStepText'); if(stepEl) stepEl.textContent=step;
  var locEl=document.getElementById('cacheLocText'); if(locEl) locEl.textContent=location || '-';
  var desc=document.getElementById('cacheDesc'); if(desc) desc.value='';
  var form=document.getElementById('cacheModalForm'); if(form) form.style.display='block';
  var doing=document.getElementById('cacheModalDoing'); if(doing) doing.style.display='none';
  var footForm=document.getElementById('cacheModalFootForm'); if(footForm) footForm.style.display='flex';
  var footDoing=document.getElementById('cacheModalFootDoing'); if(footDoing) footDoing.style.display='none';
  m.classList.add('active');
}
function confirmCacheModal(){
  var form=document.getElementById('cacheModalForm'); if(form) form.style.display='none';
  var doing=document.getElementById('cacheModalDoing'); if(doing) doing.style.display='block';
  var footForm=document.getElementById('cacheModalFootForm'); if(footForm) footForm.style.display='none';
  var footDoing=document.getElementById('cacheModalFootDoing'); if(footDoing) footDoing.style.display='flex';
}
function closeCacheModal(){ var m=document.getElementById('cacheModalMask'); if(m) m.classList.remove('active'); }
function toggleModSwitch(){ var p=document.getElementById('modSwitch'); var smh=document.querySelector('.smh-wrap .smh'); if(p&&smh){ var open=p.classList.toggle('open'); smh.classList.toggle('open', open); } }
function toggleTenantPop(ev){ if (ev) ev.stopPropagation(); var p=document.getElementById('tenantPop'); var t=document.querySelector('.tn-tenant'); if(p&&t){ var open=p.classList.toggle('open'); t.classList.toggle('open', open); } }
function selectTenant(el){
  var name = el.dataset.tenant; var av = el.dataset.av;
  document.querySelectorAll('.tenant-pop .tp-tenant').forEach(function(it){ it.classList.remove('active'); });
  el.classList.add('active');
  var n = document.getElementById('ttName'); if (n) n.textContent = name;
  var a = document.getElementById('ttAv'); if (a) a.textContent = av;
  try { sessionStorage.setItem('qTenant', JSON.stringify({name:name,av:av})); } catch(e){}
  var p=document.getElementById('tenantPop'); var t=document.querySelector('.tn-tenant');
  if (p) p.classList.remove('open'); if (t) t.classList.remove('open');
  toast('已切换至 ' + name);
}
(function(){
  try {
    var v = sessionStorage.getItem('qTenant'); if (!v) return;
    var o = JSON.parse(v);
    document.querySelectorAll('.tenant-pop .tp-tenant').forEach(function(it){
      var on = it.dataset.tenant === o.name;
      it.classList.toggle('active', on);
    });
    var n = document.getElementById('ttName'); if (n) n.textContent = o.name;
    var a = document.getElementById('ttAv'); if (a) a.textContent = o.av;
  } catch(e){}
})();
document.addEventListener('click', function(e){
  var t=document.querySelector('.tn-tenant'); var p=document.getElementById('tenantPop');
  if(t && p && p.classList.contains('open') && !t.contains(e.target)){
    p.classList.remove('open'); t.classList.remove('open');
  }
});
function toggleDevSwitch(){ var p=document.getElementById('devSwitch'); var smh=document.querySelector('.dev-wrap .smh'); if(p&&smh){ var open=p.classList.toggle('open'); smh.classList.toggle('open', open); } }
function selectDev(el, name){
  var sib = el.parentNode.querySelectorAll('.ms-item');
  sib.forEach(function(s){ s.classList.remove('active'); });
  el.classList.add('active');
  var nm = document.getElementById('devName'); if (nm) nm.textContent = name;
  var ic = document.querySelector('.dev-wrap .smh-icon'); if (ic) ic.textContent = name[0];
  try { sessionStorage.setItem('qDevSel', name); } catch(e){}
  var p=document.getElementById('devSwitch'); var smh=document.querySelector('.dev-wrap .smh');
  if (p) p.classList.remove('open'); if (smh) smh.classList.remove('open');
  toast('已切换到 ' + name);
}
(function(){
  try {
    var saved = sessionStorage.getItem('qDevSel');
    if (!saved) return;
    var items = document.querySelectorAll('.dev-switch .ms-item');
    items.forEach(function(it){
      if (it.textContent.trim() === saved){
        items.forEach(function(s){ s.classList.remove('active'); });
        it.classList.add('active');
        var nm = document.getElementById('devName'); if (nm) nm.textContent = saved;
        var ic = document.querySelector('.dev-wrap .smh-icon'); if (ic) ic.textContent = saved[0];
      }
    });
  } catch(e){}
})();
document.addEventListener('click', function(e){
  var wraps = document.querySelectorAll('.smh-wrap, .dev-wrap');
  wraps.forEach(function(wrap){
    var smh = wrap.querySelector('.smh');
    var p = wrap.querySelector('.mod-switch, .dev-switch');
    if (wrap && smh && p && smh.classList.contains('open') && !wrap.contains(e.target)){
      p.classList.remove('open'); smh.classList.remove('open');
    }
  });
});
/* 新增训练任务: 抽屉打开时 lazy-init CodeMirror 代码编辑器 + 字符计数 */
function initTrainCodeEditor(id, mode){
  var ta = document.getElementById(id);
  if (ta && !ta._cmInited && window.CodeMirror){
    ta._cmInited = true;
    var cm = CodeMirror.fromTextArea(ta, { mode:mode, lineNumbers:false, lineWrapping:false, viewportMargin:Infinity });
    ta._cm = cm;
  } else if (ta && ta._cm){
    ta._cm.refresh();
  }
}
function openTrainDrawer(){
  openDrawer('drawerNewTrain');
  updateTrainImagePath();
  setTimeout(function(){
    initTrainCodeEditor('yamlEditor', 'yaml');
    initTrainCodeEditor('entryCommandEditor', 'shell');
  }, 50);
}
function updateNameCount(input){
  var c = document.getElementById('nameCount');
  if (c) c.textContent = (input.value.length) + ' / 50';
}
var TRAIN_IMAGE_MODE = 'default';
var DEFAULT_TRAIN_IMAGE = {
  name: 'mozbrain',
  version: 'thor-v1.0.0',
  path: 'spirit-ai-cn-beijing.cr.volces.com/spirit-ai/mozbrain:thor-v1.0.0'
};
var TRAIN_IMAGE_VERSIONS = {
  'mozbrain_release': ['thor-v1.0.0', 'thor-v0.9.8', 'latest'],
  'mozbrain': ['thor-v1.0.0', 'thor-v0.9.8', 'latest'],
  'mozbrain_base': ['thor-v1.0.0', 'thor-v0.9.8', 'latest']
};
function switchTrainImageMode(el, mode){
  TRAIN_IMAGE_MODE = mode;
  el.parentNode.querySelectorAll('.tm-subtab').forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
  var def = document.getElementById('trainImageDefault');
  var custom = document.getElementById('trainImageCustom');
  if (def) def.classList.toggle('active', mode === 'default');
  if (custom) custom.classList.toggle('active', mode === 'custom');
  updateTrainImagePath();
}
function updateTrainImageVersions(){
  var nameSel = document.getElementById('trainImageName');
  var versionSel = document.getElementById('trainImageVersion');
  if (!nameSel || !versionSel) return;
  var versions = TRAIN_IMAGE_VERSIONS[nameSel.value] || [];
  versionSel.innerHTML = '<option value="" selected disabled>镜像版本</option>' + versions.map(function(v){ return '<option value="' + v + '">' + v + '</option>'; }).join('');
  refreshSelectPlaceholderState(nameSel);
  refreshSelectPlaceholderState(versionSel);
  updateTrainImagePath();
}
function updateTrainImagePath(){
  var nameSel = document.getElementById('trainImageName');
  var versionSel = document.getElementById('trainImageVersion');
  var pathEl = document.getElementById('trainImagePath');
  if (!pathEl) return;
  if (TRAIN_IMAGE_MODE === 'default'){
    pathEl.textContent = DEFAULT_TRAIN_IMAGE.path;
    return;
  }
  if (!nameSel || !versionSel) return;
  if (!nameSel.value || !versionSel.value){
    pathEl.textContent = '请选择镜像名称和版本';
    return;
  }
  pathEl.textContent = 'spirit-ai-cn-beijing.cr.volces.com/spirit-ai/' + nameSel.value + ':' + versionSel.value;
}
function switchAdvTab(el){
  var tabs = el.parentNode.querySelectorAll('.at');
  tabs.forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
}
/* 训练详情 5 个 tab 切换 */
function switchDetTab(el, tabId){
  el.parentNode.querySelectorAll('.det-tab').forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
  document.querySelectorAll('.det-pane').forEach(function(p){ p.classList.remove('active'); });
  var pane = document.getElementById('det-pane-' + tabId);
  if (pane) pane.classList.add('active');
}
function switchLogSubtab(el){
  el.parentNode.querySelectorAll('.ls-tab').forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
  var pane = el.closest('.logs-pane');
  if(!pane) return;
  pane.querySelectorAll('.log-subpane').forEach(function(p){ p.classList.remove('active'); });
  var target = pane.querySelector('[data-log-pane="' + el.dataset.logTab + '"]');
  if(target) target.classList.add('active');
}
function toggleLogToggle(el){ el.classList.toggle('on'); }
function openDeployCheckpointPicker(el){
  var picker = el.closest('.deploy-checkpoint-picker');
  if(!picker) return;
  document.querySelectorAll('.deploy-checkpoint-picker.open').forEach(function(wrap){
    if(wrap !== picker) wrap.classList.remove('open');
  });
  picker.classList.add('open');
  var input = picker.querySelector('.dcp-search');
  if(input && el !== input) input.focus();
}
function selectDeployCheckpoint(el){
  var picker = el.closest('.deploy-checkpoint-picker');
  if(!picker) return;
  var value = el.dataset.value || '';
  picker.querySelectorAll('.ddp-item').forEach(function(item){ item.classList.remove('on'); item.style.display = ''; });
  el.classList.add('on');
  var input = picker.querySelector('.dcp-search');
  var hidden = picker.querySelector('.dcp-hidden');
  if(input) input.value = value;
  if(hidden) hidden.value = value;
  picker.classList.remove('open');
}
function filterDeployCheckpoints(input){
  var q = (input.value || '').trim().toLowerCase();
  var picker = input.closest('.deploy-checkpoint-picker');
  if(!picker) return;
  picker.classList.add('open');
  picker.querySelectorAll('.ddp-item').forEach(function(item){
    var hay = ((item.dataset.value || '') + ' ' + (item.dataset.desc || '')).toLowerCase();
    item.style.display = hay.indexOf(q) >= 0 ? '' : 'none';
  });
}
function openDeployDevicePicker(el){
  var picker = el.closest('.deploy-device-picker');
  if(!picker) return;
  document.querySelectorAll('.deploy-device-picker.open').forEach(function(wrap){
    if(wrap !== picker) wrap.classList.remove('open');
  });
  picker.classList.add('open');
  var input = picker.querySelector('.ddp-search');
  if(input && el !== input) input.focus();
}
function toggleDeployDevice(el){
  el.classList.toggle('on');
  var picker = el.closest('.deploy-device-picker');
  if(!picker) return;
  var id = el.dataset.id;
  var label = el.dataset.label || id;
  var chips = picker.querySelector('.ddp-chips');
  var exists = chips.querySelector('[data-id="' + id + '"]');
  if(el.classList.contains('on') && !exists){
    var chip = document.createElement('span');
    chip.className = 'picked';
    chip.dataset.id = id;
    var text = document.createElement('span');
    text.className = 'picked-text';
    text.textContent = label;
    var close = document.createElement('i');
    close.textContent = '×';
    close.onclick = function(ev){ removeDeployDevice(close, ev); };
    chip.appendChild(text);
    chip.appendChild(close);
    chips.insertBefore(chip, picker.querySelector('.ddp-search'));
  } else if(!el.classList.contains('on') && exists) {
    exists.remove();
  }
  var input = picker.querySelector('.ddp-search');
  if(input) input.value = '';
  picker.querySelectorAll('.ddp-item').forEach(function(item){ item.style.display = ''; });
}
function removeDeployDevice(x, ev){
  if(ev) ev.stopPropagation();
  var chip = x.closest('.picked');
  var picker = x.closest('.deploy-device-picker');
  var id = chip.dataset.id;
  chip.remove();
  var item = picker.querySelector('.ddp-item[data-id="' + id + '"]');
  if(item) item.classList.remove('on');
}
function filterDeployDevices(input){
  var q = (input.value || '').trim().toLowerCase();
  var picker = input.closest('.deploy-device-picker');
  if(!picker) return;
  picker.classList.add('open');
  picker.querySelectorAll('.ddp-item').forEach(function(item){
    item.style.display = (item.dataset.id || '').toLowerCase().indexOf(q) >= 0 ? '' : 'none';
  });
}
function switchDeviceDeployTab(el, boxId, tab){
  el.parentNode.querySelectorAll('.ep-tab').forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
  var box = document.getElementById(boxId);
  if(!box) return;
  box.querySelectorAll('.dev-deploy-pane').forEach(function(p){ p.style.display='none'; });
  var pane = box.querySelector('[data-pane="' + tab + '"]');
  if(pane) pane.style.display='';
}
function switchDeviceDetailTab(el, boxId, tab){
  el.parentNode.querySelectorAll('.tm-subtab').forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
  var box = document.getElementById(boxId);
  if(!box) return;
  box.querySelectorAll('.device-detail-pane').forEach(function(p){ p.classList.remove('active'); });
  var pane = box.querySelector('[data-detail-pane="' + tab + '"]');
  if(pane) pane.classList.add('active');
}
function switchDeviceRecordTab(el, boxId, tab){
  el.parentNode.querySelectorAll('.tm-subtab').forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
  var box = document.getElementById(boxId);
  if(!box) return;
  box.querySelectorAll('.dev-record-pane').forEach(function(p){ p.classList.remove('active'); });
  var pane = box.querySelector('[data-record-type="' + tab + '"]');
  if(pane) pane.classList.add('active');
}
function switchDeviceModelRecordTab(el, boxId, tab){
  el.parentNode.querySelectorAll('.tm-subtab').forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
  var box = document.getElementById(boxId);
  if(!box) return;
  box.querySelectorAll('.dev-model-record-pane').forEach(function(p){ p.style.display='none'; });
  var pane = box.querySelector('[data-record-pane="' + tab + '"]');
  if(pane) pane.style.display='';
}
/* 部署任务: 设备数胶囊点击展开 */
function toggleDevsPop(el, ev){
  if (ev) ev.stopPropagation();
  var pop = el.nextElementSibling;
  document.querySelectorAll('.devs-pop.open').forEach(function(p){
    if (p !== pop) { p.classList.remove('open'); p.previousElementSibling.classList.remove('open'); }
  });
  pop.classList.toggle('open');
  el.classList.toggle('open');
}
document.addEventListener('click', function(e){
  if (!e.target.closest('.devs-cell')) {
    document.querySelectorAll('.devs-pop.open').forEach(function(p){ p.classList.remove('open'); p.previousElementSibling.classList.remove('open'); });
  }
});
/* 运行记录 trial 列表 + Checkpoint/日志/时间线 子 tab */
function selectTrial(el){
  el.parentNode.querySelectorAll('.tlp-item').forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
}
function bkTab(el, name){
  el.parentNode.querySelectorAll('.bk-tab').forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
  document.querySelectorAll('.bk-pane').forEach(function(p){ p.classList.remove('active'); });
  var pane = document.getElementById('bk-pane-'+name); if (pane) pane.classList.add('active');
}
function switchTrialTab(el, tabId){
  el.parentNode.querySelectorAll('.ts-tab').forEach(function(t){ t.classList.remove('active'); });
  el.classList.add('active');
  document.querySelectorAll('.ts-pane').forEach(function(p){ p.classList.remove('active'); });
  var pane = document.getElementById('ts-pane-' + tabId);
  if (pane) pane.classList.add('active');
}
/* 侧栏滚动位置保留 (按模块前缀, 避免跨模块串位置) */
(function(){
  function siderKey(){ return 'qSiderScroll-' + (location.pathname.split('/')[1] || 'root'); }
  function init(){
    var s = document.querySelector('.sider-nav'); if (!s) return;
    try { var v = sessionStorage.getItem(siderKey()); if (v) s.scrollTop = parseInt(v, 10) || 0; } catch(e){}
    var t = null;
    s.addEventListener('scroll', function(){
      clearTimeout(t);
      t = setTimeout(function(){ try { sessionStorage.setItem(siderKey(), s.scrollTop); } catch(e){} }, 80);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
</script>
<!-- data_platform 内联脚本 (switchTab / toggleTP / epTab / msUpdate / row menu ...) -->
<script>""" + DP_INLINE_JS + """</script>
<!-- quanta_eval_platform 内联脚本 (openModal / closeModal / expand-btn / pref-btn ...) -->
<script>""" + EP_INLINE_JS + """</script>
<script>// (placeholder to keep extra_script slot below)
</script>
{{ extra_script|safe if extra_script else '' }}
</body>
</html>"""


def _build_mod_switch_html(active_module):
    items = []
    for key, name in PLATFORM_ORDER:
        cls = " active" if key == active_module else ""
        items.append(
            f'<a class="ms-item{cls}" href="/{key}">'
            f'<div class="ms-ic">{PLATFORM_ICONS[key]}</div>{name}</a>'
        )
    return "".join(items)


def render_page(title, content, active="", breadcrumb=None, extra_script=None,
                module=None, mvp_note=None):
    """
    module: 平台 key ('data' / 'model' / 'device' / 'asset' / None for portal)
    active: 当前激活的 sidebar leaf url (用于高亮)
    """
    portal = module is None
    if portal:
        return render_template_string(
            BASE_TEMPLATE, title=title, content=content, portal=True, module=None,
            module_name=None, module_icon=None, module_nav=None, mod_switch_html=None,
            active="", breadcrumb=breadcrumb, extra_script=extra_script, mvp_note=mvp_note,
            device_models=None,
        )
    pf = PLATFORMS[module]
    dev_models = DEVICE_MODELS if module == "device" else None
    return render_template_string(
        BASE_TEMPLATE, title=title, content=content, portal=False, module=module,
        module_name=pf["name"], module_icon=PLATFORM_ICONS[module],
        module_nav=pf["nav"], mod_switch_html=_build_mod_switch_html(module),
        active=active, breadcrumb=breadcrumb,
        extra_script=extra_script, mvp_note=mvp_note,
        device_models=dev_models,
    )


# ════════════════════════════════════════════════════════════════
# Section 4: Helpers
# ════════════════════════════════════════════════════════════════

STATUS_TAG = {
    "running":  '<span class="qa qa-warn">运行中</span>',
    "done":     '<span class="qa qa-pass">已完成</span>',
    "paused":   '<span class="qa qa-pend">已暂停</span>',
    "failed":   '<span class="qa qa-fail">失败</span>',
    "pending":  '<span class="qa qa-pend">待启动</span>',
    "in_review":'<span class="qa qa-warn">复核中</span>',
    "in_progress": '<span class="qa qa-warn">进行中</span>',
    "passed":   '<span class="qa qa-pass">通过</span>',
    "active":   '<span class="qa qa-pass">已生效</span>',
    "deployed": '<span class="qa qa-pass">已部署</span>',
    "approved": '<span class="qa qa-pass">已批准</span>',
    "online":   '<span class="qa qa-pass">在线</span>',
    "offline":  '<span class="qa qa-pend">离线</span>',
    "in_use":   '<span class="qa qa-warn">占用中</span>',
}


def status_tag(s):
    return STATUS_TAG.get(s, f'<span class="tag tag-gray">{s}</span>')


def get_node_chain_ids(node, node_type):
    """
    返回节点所属的所有 chain-id 列表
    node_type: "task" | "dataset" | "experiment" | "checkpoint" | "eval"
    """
    if node_type == "task":
        # 采集任务 → 找所有使用它的数据集
        datasets = [ds for ds in DATASETS if node["id"] in ds.get("source_tasks", [])]
        return [f"chain_{ds['id']}" for ds in datasets]

    elif node_type == "dataset":
        # 数据集本身就是链路锚点
        return [f"chain_{node['id']}"]

    elif node_type == "experiment":
        # 训练任务 → 找它使用的数据集
        ds = _dataset_by_id_or_name(node.get("dataset", ""))
        return [f"chain_{ds['id']}"] if ds else []

    elif node_type == "checkpoint":
        # Checkpoint → 通过训练任务找数据集
        exp = _exp_by_id(f"exp_{node['id']}")
        if exp:
            ds = _dataset_by_id_or_name(exp.get("dataset", ""))
            return [f"chain_{ds['id']}"] if ds else []
        return []

    elif node_type == "eval":
        # 评测任务暂时不追踪链路
        return []

    return []


def progress_bar(cur, total, cls=""):
    pct = 0 if total == 0 else int(cur * 100 / total)
    cls_attr = f" {cls}" if cls else ""
    return (f'<div class="bar{cls_attr}"><div class="track"><div class="fill" style="width:{pct}%"></div></div>'
            f'<span class="pct">{cur}/{total}</span></div>')


def page_header(title, sub_mvp, sub_deferred=None):
    """详情页标题已统一去掉, 返回空串. 调用点保持原签名兼容."""
    return ""


def stat_grid(items):
    cards = ""
    for label, value, sub in items:
        sub_html = f'<div class="stat-sub">{sub}</div>' if sub else ''
        cards += f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value">{value}</div>{sub_html}</div>'
    return f'<div class="stat-grid">{cards}</div>'


def welcome_card(platform_name, tagline, description):
    return f"""
    <div class="welcome-card">
      <h2>欢迎来到{platform_name}</h2>
      <p>{tagline}。{description}</p>
    </div>
    """


def mod_entry(href, no, name, sub, stat_text=None):
    """平台概览页里, 每个 MVP 模块的入口卡"""
    st = f'<div class="me-st">{stat_text}</div>' if stat_text else ''
    return f"""
    <a class="me" href="{href}">
      <div class="me-no">模块 {no}</div>
      <div class="me-nm">{name}</div>
      <div class="me-sub">{sub}</div>
      {st}
    </a>
    """


# ════════════════════════════════════════════════════════════════
# Section 5: Portal Home  (/  门户总览)
# ════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    # 跨平台 stats
    n_collect = len(COLLECT_TASKS)
    n_collect_running = sum(1 for c in COLLECT_TASKS if c["status"] == "running")
    n_episodes = sum(p["ep_count"] for p in PROCESS_JOBS if p["status"] == "done")
    n_datasets_active = sum(1 for d in DATASETS if d["status"] == "active")
    n_exp_running = sum(1 for e in EXPERIMENTS if e["status"] == "running")
    n_models = len(MODELS)
    n_deployed = sum(1 for d in DEPLOYS if d["status"] == "deployed")
    n_devices_online = sum(1 for d in DEVICES if d["status"] in ("online", "in_use"))
    n_devices_total = len(DEVICES)
    n_bookings_today = sum(1 for b in BOOKINGS if b["start"].startswith("2026-06-17"))

    # 平台入口卡数据
    cards = [
        ("data", "数据平台", "采集 → 质检 → 标注 → 数据集", "/data", "数",
         [("任务", n_collect), ("Episode", n_episodes), ("数据集", n_datasets_active)],
         ["采集任务", "自动处理", "质检", "标注", "数据集"]),
        ("model", "模型平台", "训练 → 评测 → 部署", "/model", "模",
         [("训练实验", len(EXPERIMENTS)), ("模型版本", n_models), ("已部署", n_deployed)],
         ["训练实验", "评测", "部署", "模型仓库"]),
        ("app", "应用编排平台", "模型服务 · 编排 · 资产", "/app", "应",
         [("模型服务", 0), ("编排", 0), ("资产", 0)],
         ["模型服务", "生态市场", "应用编排", "资产管理"]),
        ("device", "设备管理平台", "设备 · 监测 · OTA", "/device", "设",
         [("设备", n_devices_total), ("在线", n_devices_online), ("今日预约", n_bookings_today)],
         ["设备管理", "设备预约", "监测", "OTA"]),
    ]
    cards_html = ""
    for color, name, tag, href, short, stats, mods in cards:
        st_html = "".join(f'<div class="mc-stt"><div class="v">{v}</div><div class="l">{l}</div></div>' for l, v in stats)
        tg_html = "".join(f'<span>{m}</span>' for m in mods)
        cards_html += f"""
        <a class="mc" href="{href}">
          <div class="mc-hd">
            <div class="mc-ic {color}">{short}</div>
            <div class="mc-t">
              <div class="mc-tn">{name}</div>
              <div class="mc-tg">{tag}</div>
            </div>
            <span class="mc-ar">→</span>
          </div>
          <div class="mc-tags">{tg_html}</div>
          <div class="mc-st">{st_html}</div>
        </a>
        """

    content = f"""
    <div class="pw">
      <div class="pw-l">
        <h1>欢迎来到 Quanta 控制台</h1>
        <p>面向算法 / 数据 / 标注开发者的工具链 · 端到端打通采集 → 训练 → 部署 → 真机回流</p>
      </div>
      <div class="pw-acc">
        <div class="av">J</div>
        <div class="info">
          <div class="nm">joanna.qiao <span class="role">算法 / 数据工程师</span></div>
          <div class="id">账号 ID: 2105778518</div>
        </div>
      </div>
      <div class="pw-stats">
        <div class="pw-st"><div class="v">0</div><div class="l">待办事项</div></div>
        <div class="pw-st"><div class="v">{n_collect_running}</div><div class="l">进行中任务</div></div>
        <div class="pw-st"><div class="v">{n_exp_running}</div><div class="l">运行中实验</div></div>
      </div>
    </div>

    <div class="pfw">
      <div class="pfw-ttl">具身数据飞轮 <span class="sub">· 一期端到端打通</span></div>
      <div class="pfw-loop">
        <span class="pfw-step">采集</span><span class="pfw-arr">→</span>
        <span class="pfw-step">质检</span><span class="pfw-arr">→</span>
        <span class="pfw-step">标注</span><span class="pfw-arr">→</span>
        <span class="pfw-step">训练</span><span class="pfw-arr">→</span>
        <span class="pfw-step">评测</span><span class="pfw-arr">→</span>
        <span class="pfw-step">部署</span><span class="pfw-arr">→</span>
        <span class="pfw-step">真机回流</span>
      </div>
      <a href="/model/lineage" class="pfw-link">查看端到端血缘 →</a>
    </div>

    <div class="p-sec">平台入口</div>
    <div class="p-mods">{cards_html}</div>

    <div class="p-sec">资源概览</div>
    {stat_grid([
        ("数据集 (生效)", str(n_datasets_active), f"已切分 {n_episodes:,} EP"),
        ("模型仓库", str(n_models), f"已部署 {n_deployed} 台"),
        ("设备在线", f"{n_devices_online} / {n_devices_total}", f"今日预约 {n_bookings_today}"),
        ("GPU 资源池", "3 / 8", "由底座统一调度"),
    ])}
    """
    return render_page("控制台总览", content, module=None, mvp_note="MVP 一期")


# ════════════════════════════════════════════════════════════════
# Section 6: 数据平台 (/data/*)
# ════════════════════════════════════════════════════════════════

@app.route("/data")
def data_home():
    desc = "数据平台覆盖一条完整 pipeline: 从采集任务管理、自动处理 (时间戳对齐 / 抽帧 / 切 Episode), 到质检、标注, 最终沉淀为可被训练引用的数据集。"
    content = welcome_card("数据平台", "采集 → 质检 → 标注 → 数据集", desc)
    return render_page("数据平台 · 快速入门", content, active="/data", module="data",
                       breadcrumb='<b>数据平台</b> / 快速入门', mvp_note="MVP 一期")


@app.route("/data/collect")
def collect():
    stage = request.args.get("stage", "all")
    substage = request.args.get("sub", "all")
    if stage not in ("all", "采集", "质检", "标注"):
        stage = "all"
    if substage not in ("all", "未到达", "进行中", "已完成"):
        substage = "all"

    # 子状态推导: 任务当前阶段 vs 选中的主阶段, 决定是 未到达/进行中/已完成
    _stage_order = ["采集", "质检", "标注"]
    def task_substage(c, main):
        cur = c.get("stage", "采集")
        cur_i = _stage_order.index(cur) if cur in _stage_order else 0
        main_i = _stage_order.index(main)
        return "未到达" if cur_i < main_i else ("进行中" if cur_i == main_i else "已完成")

    counts = {
        "all": len(COLLECT_TASKS),
        "采集": sum(1 for c in COLLECT_TASKS if c.get("stage") == "采集"),
        "质检": sum(1 for c in COLLECT_TASKS if c.get("stage") == "质检"),
        "标注": sum(1 for c in COLLECT_TASKS if c.get("stage") == "标注"),
    }
    # 当 stage 选了某主阶段, 计算 3 个 substage 计数
    sub_counts = {"all": 0, "未到达": 0, "进行中": 0, "已完成": 0}
    if stage in _stage_order:
        for c in COLLECT_TASKS:
            sub = task_substage(c, stage)
            sub_counts[sub] += 1
        sub_counts["all"] = len(COLLECT_TASKS)

    filtered_tasks = COLLECT_TASKS if stage == "all" else [c for c in COLLECT_TASKS if c.get("stage") == stage]
    if stage in _stage_order and substage != "all":
        filtered_tasks = [c for c in COLLECT_TASKS if task_substage(c, stage) == substage]
    rows = ""
    for c in filtered_tasks:
        toggle_on = c["status"] == "running"
        prio_color = {"高": "#cf1322", "中": "#d48806", "低": "#8c8c8c"}.get(c["priority"], "#8c8c8c")
        prio_bg = {"高": "#fff1f0", "中": "#fffbe6", "低": "#f5f5f5"}.get(c["priority"], "#f5f5f5")
        prio_bd = {"高": "#ffa39e", "中": "#ffe58f", "低": "#d9d9d9"}.get(c["priority"], "#d9d9d9")

        def _pbar(label, value_text, done, total, color="#7B8FE5"):
            pct = round(done / total * 100) if total else 0
            return (
                f'<div style="display:flex;align-items:center;gap:8px;font-size:11.5px;line-height:1.4;">'
                f'<span class="muted" style="width:30px;flex:none;">{label}</span>'
                f'<div style="flex:1;height:18px;background:#f0f0f0;border-radius:9px;overflow:hidden;position:relative;">'
                f'<div style="width:{pct}%;height:100%;background:{color};border-radius:9px;"></div>'
                f'<span style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:11px;color:rgba(0,0,0,0.78);font-weight:500;font-family:\'SF Mono\',Menlo,monospace;">{value_text}</span>'
                f'</div></div>'
            )

        qc_sum = c["qc_pass"] + c["qc_warn"] + c["qc_fail"]
        qc_text = f"{c['qc_pass']}/{c['qc_warn']}/{c['qc_fail']}"
        label_text = f"{c['label_done']}/{c['label_total']}"
        progress_cell = (
            '<div style="display:flex;flex-direction:column;gap:4px;min-width:220px;">'
            + _pbar("采集", str(c["collected"]), c["collected"], max(c["collected"], 1), "#7B8FE5")
            + _pbar("质检", qc_text, qc_sum, max(c["collected"], 1), "#5DCAA5")
            + _pbar("标注", label_text, c["label_done"], max(c["label_total"], 1), "#F0AF7D")
            + '</div>'
        )

        rows += f"""<tr>
          <td class="mono">{c['id']}</td>
          <td style="max-width:280px;"><a href="/data/recordings?task={c['id']}" style="color:#149DAA;">{c['name']}</a></td>
          <td>{progress_cell}</td>
          <td><span style="display:inline-flex;width:30px;height:30px;align-items:center;justify-content:center;background:{prio_bg};border:1px solid {prio_bd};color:{prio_color};border-radius:6px;font-size:13px;font-weight:500;">{c['priority']}</span></td>
          <td class="muted mono">{c['created']}</td>
          <td class="muted mono">{c['due']}</td>
          <td class="actions-cell">
            <div style="display:grid;grid-template-columns:auto auto;gap:4px;">
              <a class="tbtn" href="#" onclick="toast('Demo: 编辑');return false;">&#9998; 编辑</a>
              <a class="tbtn" href="#" onclick="toast('Demo: 复制');return false;">&#10697; 复制</a>
              <a class="tbtn" href="/data/recordings?task={c['id']}">&#128065; 详情</a>
              <a class="tbtn" href="#" onclick="toast('Demo: 删除');return false;">&#128465; 删除</a>
            </div>
          </td>
        </tr>"""

    def _tm_tab(key, label):
        cls = "tm-tab active" if stage == key else "tm-tab"
        return f'<a class="{cls}" href="/data/collect?stage={key}">{label}<span class="ct">{counts[key]}</span></a>'

    def _tm_subtab(key, label):
        cls = "tm-subtab active" if substage == key else "tm-subtab"
        return f'<a class="{cls}" href="/data/collect?stage={stage}&sub={key}">{label}<span class="ct">{sub_counts[key]}</span></a>'

    subtabs_html = ""
    if stage in _stage_order:
        # 采集是第一个阶段, 不存在「未到达」
        sub_keys = ["all", "进行中", "已完成"] if stage == "采集" else ["all", "未到达", "进行中", "已完成"]
        sub_labels = {"all": "全部", "未到达": "未到达", "进行中": "进行中", "已完成": "已完成"}
        subtabs_html = '<div class="tm-subtabs">' + "".join(_tm_subtab(k, sub_labels[k]) for k in sub_keys) + '</div>'

    content = f"""
    <div class="tm-bar">
      <div class="tm-tabs">
        {_tm_tab("all", "全部")}
        {_tm_tab("采集", "采集")}
        {_tm_tab("质检", "质检")}
        {_tm_tab("标注", "标注")}
      </div>
      <a class="btn btn-primary" onclick="openDrawer('drawerCollect');return false;">+ 新增任务</a>
    </div>
    {subtabs_html}

    <div class="fb-labeled">
      <div class="ff"><label>所属项目</label>
        <select><option>请选择所属项目</option><option>预训练采集</option><option>SFT 采集</option></select>
      </div>
      <div class="ff"><label>任务ID</label><input placeholder="请填写任务ID"></div>
      <div class="ff"><label>任务名称</label><input placeholder="请填写任务名称"></div>
      <div class="ff"><label>checkpoint</label>
        <select><option>请选择checkpoint</option></select>
      </div>
      <div class="ff"><label>标签</label>
        <select><option>请选择标签</option></select>
      </div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr>
          <th>任务ID</th>
          <th>任务名称</th>
          <th>任务进度 &#9432;</th>
          <th>优先级 &#x21F5;</th>
          <th>创建时间 &#x21F5;</th>
          <th>预期交付日期</th>
          <th>操作</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div class="mini-pager">
      <select><option>10条/页</option></select>
      <span class="pg-btn">&lsaquo;</span>
      <span class="pg-btn">1</span>
      <span class="muted">...</span>
      <span class="pg-btn">199</span>
      <span class="pg-btn active">200</span>
      <span class="pg-btn">201</span>
      <span class="muted">...</span>
      <span class="pg-btn">1240</span>
      <span class="pg-btn">&rsaquo;</span>
      <input class="pg-goto" value="200"><span class="pg-go">go</span>
    </div>

    <div class="drawer" id="drawerCollect">
      <div class="drawer-head"><h3>新增任务</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
      <div class="drawer-body">
        <div class="fg"><label class="fg-req">任务名称</label><input placeholder="如: 20260610_xxx_采集"></div>
        <div class="fg"><label class="fg-req">所属项目</label><select><option>预训练采集</option><option>SFT 采集</option></select></div>
        <div class="fg-row">
          <div class="fg"><label class="fg-req">优先级</label><select><option>中</option><option>高</option><option>低</option></select></div>
          <div class="fg"><label>预期交付日期</label><input type="date"></div>
        </div>
        <div class="fg"><label>采集 SOP 说明</label><textarea rows="3" placeholder="动作描述 / 物料清单..."></textarea></div>
      </div>
      <div class="drawer-foot">
        <button class="btn" onclick="closeDrawer()">取消</button>
        <button class="btn btn-primary" onclick="toast('Demo: 已创建采集任务');closeDrawer()">创建</button>
      </div>
    </div>
    """
    return render_page("任务管理", content, active="/data/collect", module="data",
                       breadcrumb='数据平台 / <b>任务管理</b>', mvp_note="MVP 一期")


# ── 数据管理: recording 拍平的列表 ──
_STAGE_TAG = {
    "质检": '<span class="tag tag-blue">质检</span>',
    "切分": '<span class="tag tag-purple">切分</span>',
    "标注": '<span class="tag tag-orange">标注</span>',
}
_COLLECT_TAG = {
    "成功": '<span class="tag tag-green">成功</span>',
    "失败": '<span class="tag tag-red">失败</span>',
    "—":   '<span class="muted">—</span>',
}
_QC_TAG = {
    "合格":   '<span class="tag tag-green">合格</span>',
    "不合格": '<span class="tag tag-red">不合格</span>',
    "—":     '<span class="muted">—</span>',
}
_LABEL_TAG = {
    "未标注": '<span class="tag tag-gray">未标注</span>',
    "标注中": '<span class="tag tag-orange">标注中</span>',
    "已完成": '<span class="tag tag-green">已完成</span>',
    "—":     '<span class="muted">—</span>',
}


# 三方数据 mock
THIRD_PARTY_DATASETS = [
    {"id": "TP-2026-001", "source": "HuggingFace", "name": "lerobot/OrganizePencilCase",
     "license": "CC-BY-4.0", "episodes": 1240, "size_gb": 48.2,
     "pulled_at": "2026-06-01", "status": "已入湖", "owner": "joanna.qiao"},
    {"id": "TP-2026-002", "source": "Bytedance Open", "name": "ByteRobot-HD-Pickup-v2",
     "license": "Apache-2.0", "episodes": 3200, "size_gb": 156.8,
     "pulled_at": "2026-05-28", "status": "已入湖", "owner": "Lance Li"},
    {"id": "TP-2026-003", "source": "HuggingFace", "name": "lerobot/AlohaSimTransferCube",
     "license": "Apache-2.0", "episodes": 800, "size_gb": 22.5,
     "pulled_at": "2026-05-25", "status": "已入湖", "owner": "joanna.qiao"},
    {"id": "TP-2026-004", "source": "外部供应商", "name": "千寻_厨房场景_合作采集_batch3",
     "license": "商业授权", "episodes": 560, "size_gb": 89.4,
     "pulled_at": "2026-06-05", "status": "入湖中", "owner": "Wei Zhang"},
    {"id": "TP-2026-005", "source": "Open X-Embodiment", "name": "berkeley_autolab_ur5",
     "license": "CC-BY-4.0", "episodes": 896, "size_gb": 34.7,
     "pulled_at": "2026-04-20", "status": "已入湖", "owner": "Min Chen"},
]


@app.route("/data/recordings")
def data_recordings():
    task_filter = request.args.get("task", "")
    recordings = [r for r in RECORDINGS if not task_filter or r["task_id"] == task_filter]

    # ── Tab 1: 自采数据 ──
    rec_rows = ""
    for r in recordings:
        rec_rows += f"""<tr>
          <td class="mono">{r['id']}</td>
          <td>
            <span class="vid-thumb"></span>
            <span class="vid-thumb"></span>
            <span class="vid-thumb"></span>
          </td>
          <td class="mono"><a href="/data/collect" style="color:#149DAA;">{r['task_id']}</a></td>
          <td class="mono">{r['collection_id']}</td>
          <td>{_STAGE_TAG.get(r['stage'], r['stage'])}</td>
          <td>{_COLLECT_TAG.get(r['collect_result'], r['collect_result'])}</td>
          <td>{_QC_TAG.get(r['qc_result'], r['qc_result'])}</td>
          <td>{_LABEL_TAG.get(r['label_status'], r['label_status'])}</td>
          <td>
            <div style="font-size:12.5px;line-height:1.6;">
              <div><span class="muted">采集:</span> {r['op_collect']}</div>
              <div><span class="muted">质检:</span> {r['op_qc']}</div>
            </div>
          </td>
          <td class="actions-cell">
            <a class="tbtn" href="#" onclick="toast('Demo: 查看轨迹');return false;">轨迹</a>
            <a class="tbtn" href="#" onclick="toast('Demo: 更多');return false;">⋯ 更多</a>
          </td>
        </tr>"""

    summary = ""
    if task_filter:
        ct = next((c for c in COLLECT_TASKS if c["id"] == task_filter), None)
        if ct:
            summary = f"""
            <div style="margin:0 0 14px;color:rgba(0,0,0,0.7);font-size:13px;">
              {ct['name']}: 采集 <b>{ct['collected']}</b> 条 · 质检 <b>{ct['qc_pass']}</b> 条 · 标注 <b>{ct['label_done']}</b>/<b>{ct['label_total']}</b>
            </div>
            """

    tab_self = f"""
    <div class="fb-labeled">
      <div class="ff"><label>ID 搜索</label><input placeholder="请输入ID"></div>
      <div class="ff"><label>序列号</label><select><option>请选择设备序列号</option><option>UDAS-007</option></select></div>
      <div class="ff"><label>操作人</label><select><option>请选择操作类型/操作人</option></select></div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>
    {summary}
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr>
          <th>recording_id</th><th>视频</th><th>Task ID</th><th>collection_id</th>
          <th>当前节点 &#9662;</th><th>采集结论 &#9662;</th><th>质检结论 &#9662;</th>
          <th>标注状态 &#9662;</th><th>操作人</th><th>操作</th>
        </tr></thead>
        <tbody>{rec_rows or '<tr><td colspan="10" style="text-align:center;padding:40px;color:rgba(0,0,0,0.25);">暂无数据</td></tr>'}</tbody>
      </table>
    </div>
    <div class="mini-pager">
      <select><option>10条/页</option></select>
      <span class="pg-btn">&lsaquo;</span>
      <span class="pg-btn active">1</span>
      <span class="pg-btn">2</span>
      <span class="pg-btn">3</span>
      <span class="muted">...</span>
      <span class="pg-btn">18</span>
      <span class="pg-btn">&rsaquo;</span>
      <input class="pg-goto" placeholder=""><span class="pg-go">go</span>
    </div>
    """

    # ── Tab 2: 三方数据 ──
    tp_rows = ""
    for d in THIRD_PARTY_DATASETS:
        status_tag = ('<span class="tag tag-green">已入湖</span>' if d["status"] == "已入湖"
                      else '<span class="tag tag-orange">入湖中</span>')
        tp_rows += f"""<tr>
          <td class="mono">{d['id']}</td>
          <td><span class="tag tag-purple">{d['source']}</span></td>
          <td><b>{d['name']}</b></td>
          <td><span class="tag tag-gray">{d['license']}</span></td>
          <td class="mono">{d['episodes']:,}</td>
          <td class="mono">{d['size_gb']} GB</td>
          <td class="muted mono">{d['pulled_at']}</td>
          <td>{status_tag}</td>
          <td>{d['owner']}</td>
          <td class="actions-cell">
            <a class="tbtn" href="#" onclick="toast('Demo: 查看数据卡片');return false;">详情</a>
            <a class="tbtn" href="#" onclick="toast('Demo: 引用');return false;">引用</a>
          </td>
        </tr>"""

    total_eps = sum(d["episodes"] for d in THIRD_PARTY_DATASETS)
    total_size = sum(d["size_gb"] for d in THIRD_PARTY_DATASETS)

    tab_thirdparty = f"""
    <div class="fb-labeled">
      <div class="ff"><label>名称</label><input placeholder="请输入数据集名称"></div>
      <div class="ff"><label>来源</label>
        <select><option>全部来源</option><option>HuggingFace</option><option>Bytedance Open</option><option>Open X-Embodiment</option><option>外部供应商</option></select>
      </div>
      <div class="ff"><label>License</label>
        <select><option>全部 License</option><option>CC-BY-4.0</option><option>Apache-2.0</option><option>商业授权</option></select>
      </div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>
    <div style="margin:0 0 14px;color:rgba(0,0,0,0.7);font-size:13px;">
      共 <b>{len(THIRD_PARTY_DATASETS)}</b> 个数据集 · <b>{total_eps:,}</b> episode · 总大小 <b>{total_size:.1f}</b> GB
      <a href="#" class="btn btn-sm" style="margin-left:14px;color:#149DAA;border-color:#149DAA;" onclick="toast('Demo: 拉取新的三方数据集');return false;">+ 拉取数据集</a>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr>
          <th>ID</th><th>来源</th><th>数据集名称</th><th>License</th>
          <th>Episodes</th><th>大小</th><th>拉取时间</th><th>状态</th><th>负责人</th><th>操作</th>
        </tr></thead>
        <tbody>{tp_rows}</tbody>
      </table>
    </div>
    """

    content = f"""
    <div class="det-tabs">
      <span class="det-tab active" onclick="switchDetTab(this,'self')">自采数据</span>
      <span class="det-tab" onclick="switchDetTab(this,'thirdparty')">三方数据</span>
    </div>
    <div id="det-pane-self"        class="det-pane active">{tab_self}</div>
    <div id="det-pane-thirdparty"  class="det-pane">{tab_thirdparty}</div>
    """
    return render_page("数据管理", content, active="/data/recordings", module="data",
                       breadcrumb='数据平台 / <b>数据管理</b>', mvp_note="MVP 一期")


# ── 工作台: 任务卡片列表 ──
WB_TASKS = [
    {"type": "人工质检", "color": "blue",
     "name": "20260529_河北省石家庄_白板区采集 · 合格性判定",
     "desc": "对采集后的 recording 进行人工合格性判定 (画面 / 动作 / 物料 是否符合 SOP)",
     "pending": 9, "done": 171},
    {"type": "质检抽检", "color": "teal",
     "name": "20260607_山东德州_批次抽检",
     "desc": "对自动质检结果做 5% 抽检, 校验自动质检准确率",
     "pending": 28, "done": 0},
    {"type": "切分", "color": "purple",
     "name": "20260605_白板补采_episode 切分",
     "desc": "按动作分段把 recording 切成 episode (起始 / 结束 / 关键帧标记)",
     "pending": 50, "done": 0},
    {"type": "标注", "color": "orange",
     "name": "20260529_白板区_动作分段标注",
     "desc": "对切分后的 episode 做动作分段 + 关键帧 + 抓取点标注",
     "pending": 142, "done": 89},
    {"type": "标注验收", "color": "amber",
     "name": "20260518_HouseHold_标注成果验收",
     "desc": "对标注员产出的标注结果做一致性验收, 不合格回流到标注重做",
     "pending": 24, "done": 118},
    {"type": "终验", "color": "green",
     "name": "20260529_数据集 v4_入湖前终验",
     "desc": "数据集入湖前的最终验收, 抽检通过后正式发布到数据湖",
     "pending": 3, "done": 12},
]


@app.route("/data/workbench")
def data_workbench():
    # 顶部 stat 卡: 今日 / 本周 / 合格率, 每张带同比变化
    wb_stats = [
        {"label": "今日完成任务量", "value": "127",  "base": "昨日 113",  "delta": "+12.4%", "dir": "up"},
        {"label": "本周完成任务量", "value": "856",  "base": "上周 790",  "delta": "+8.4%",  "dir": "up"},
        {"label": "任务合格率",     "value": "92.4%", "base": "上周 93.6%", "delta": "-1.2%", "dir": "down"},
    ]
    stat_cards_html = ""
    for s in wb_stats:
        arrow = "&uarr;" if s["dir"] == "up" else ("&darr;" if s["dir"] == "down" else "&minus;")
        trend_cls = f"trend-{s['dir']}"
        stat_cards_html += f"""
        <div class="stat-card">
          <div class="stat-label">{s['label']}</div>
          <div class="stat-value">{s['value']}</div>
          <div class="stat-sub"><span class="{trend_cls}">{arrow} {s['delta']}</span> 同比{s['base']}</div>
        </div>
        """

    cards = ""
    for t in WB_TASKS:
        total = t["pending"] + t["done"]
        pct = round(t["done"] / total * 100) if total else 0
        cards += f"""
        <div class="wb-card {t['color']}">
          <div class="wb-main">
            <div class="wb-head">
              <span class="wb-badge {t['color']}">{t['type']}</span>
              <span class="wb-name">{t['name']}</span>
            </div>
            <div class="wb-desc">{t['desc']}</div>
          </div>
          <div class="wb-side">
            <div class="wb-progress">
              <div class="wp-bar"><div class="wp-fill" style="width:{pct}%;"></div></div>
              <div class="wp-meta">
                <span class="done">已处理 <b>{t['done']}</b></span>
                <span class="pend">待处理 <b>{t['pending']}</b></span>
                <span class="pct">{pct}%</span>
              </div>
            </div>
            <a class="btn btn-primary" href="/data/workbench/edit">进入工作台 &rsaquo;</a>
          </div>
        </div>
        """
    content = f"""
    <div class="stat-grid">{stat_cards_html}</div>
    <div class="wb-list">{cards}</div>
    """
    return render_page("工作台", content, active="/data/workbench", module="data",
                       breadcrumb='数据平台 / <b>工作台</b>', mvp_note="MVP 一期")


# ── 工作台 · 标注 editor (单条任务进入后的标注界面) ──
@app.route("/data/workbench/edit")
def data_workbench_edit():
    DUR_TOTAL = 42.80
    rows = [
        {"no": 1, "start": 0.00,  "end": 1.94,  "color": "#E45A52", "desc": "无法标注",       "el_placeholder": "选择动作元素"},
        {"no": 2, "start": 1.94,  "end": 42.80, "color": "#8B47C7", "desc": "分捡药片放入盘中", "el_placeholder": "选择动作元素"},
    ]
    tick_secs = [0, 5, 10, 15, 20, 25, 30, 35, 40]
    ticks_html = "".join(
        f'<span class="lab-tl-tick" style="left:{t / DUR_TOTAL * 100:.2f}%;">{t:.2f}s</span>'
        for t in tick_secs
    )
    # 顶部 orange 短带 (前 5s 当前播放窗口) + 主时间线 (按标注段铺色)
    seg1_pct = 5.0 / DUR_TOTAL * 100
    main_segs = ""
    for r in rows:
        left = r["start"] / DUR_TOTAL * 100
        width = (r["end"] - r["start"]) / DUR_TOTAL * 100
        cls = "red" if r["color"] == "#E45A52" else "purple"
        main_segs += f'<div class="lab-tl-seg {cls}" style="left:{left:.2f}%;width:{width:.2f}%;"></div>'
    # 两个 pin marker (示意书签 / 关键帧)
    pin_pcts = [14.0 / DUR_TOTAL * 100, 17.0 / DUR_TOTAL * 100]
    pins_html = "".join(f'<span class="lab-tl-pin" style="left:{p:.2f}%;">&#9873;</span>' for p in pin_pcts)

    body_rows = ""
    for r in rows:
        dur = r["end"] - r["start"]
        body_rows += f"""<tr>
          <td>{r['no']}</td>
          <td>{r['start']:.2f}s</td>
          <td>{r['end']:.2f}s</td>
          <td>{dur:.2f}s</td>
          <td><span class="color-chip" style="background:{r['color']};"></span></td>
          <td><select class="mock"><option>{r['el_placeholder']}</option><option>抓取</option><option>放置</option><option>移动</option></select></td>
          <td><input class="mock" type="text" value="{r['desc']}"></td>
          <td>—</td>
          <td>
            <div class="lab-act-cell">
              <button class="lab-act-btn blue"   title="跳到此段">&#10162;</button>
              <button class="lab-act-btn orange" title="编辑">&#9998;</button>
              <button class="lab-act-btn red"    title="删除">&#128465;</button>
            </div>
          </td>
        </tr>"""

    content = f"""
    <div class="lab-meta">
      <div class="lf"><span class="lbl">任务ID:</span><span class="val">9805</span></div>
      <div class="lf"><span class="lbl">任务名称:</span><span class="val">20260601_SortPills_V2_NarrowTable_FrontDeskDemo_Udas</span></div>
      <div class="grow"></div>
      <div class="lf mono"><span class="lbl">序列号:</span><span class="val">UDAS-00002-2983</span></div>
      <div class="lf"><span class="lbl">采集员:</span><span class="val">柳少龙</span></div>
      <div class="lf mono"><span class="lbl">数据ID:</span><span class="val">3298698</span></div>
      <div class="ver" onclick="toast('Demo: 切换版本')">第1版<span class="caret">&#9662;</span></div>
      <div class="lf"><span class="lbl">状态:</span><span class="status-pass">通过</span></div>
    </div>

    <div class="lab-vid-grid">
      <div class="lab-vid">
        <span class="vid-label">左臂视角</span>
        <span class="vid-expand" onclick="toast('Demo: 放大')" title="放大">&#9974;</span>
        &#9658;
      </div>
      <div class="lab-vid">
        <span class="vid-label">头部视角</span>
        <span class="vid-expand" onclick="toast('Demo: 放大')" title="放大">&#9974;</span>
        &#9658;
      </div>
      <div class="lab-vid">
        <span class="vid-label">右臂视角</span>
        <span class="vid-expand" onclick="toast('Demo: 放大')" title="放大">&#9974;</span>
        &#9658;
      </div>
      <div class="lab-fab" onclick="toast('Demo: 录屏')" title="录屏">&#9209;</div>
    </div>

    <div class="lab-tools-card">
      <div class="lab-timeline">
        <div class="lab-tl-ticks">{ticks_html}</div>
        <div class="lab-tl-bar"><div class="lab-tl-seg orange" style="left:0;width:{seg1_pct:.2f}%;"></div></div>
        <div class="lab-tl-bar">{main_segs}{pins_html}</div>
      </div>
      <div class="lab-tools">
        <div class="lab-tools-left">
          <span class="lab-tool" title="上一帧" onclick="toast('Demo: 上一帧')">&laquo;</span>
          <span class="lab-speed">1x</span>
          <span class="lab-tool" title="下一帧" onclick="toast('Demo: 下一帧')">&raquo;</span>
          <span class="lab-tool play" title="播放" onclick="toast('Demo: 播放')">&#9654;</span>
          <span class="lab-tool" title="截帧" onclick="toast('Demo: 截帧')">&#9783;</span>
          <span class="lab-tool" title="在前插入" onclick="toast('Demo: 在前插入')">&#10133;</span>
          <span class="lab-tool" title="在后插入" onclick="toast('Demo: 在后插入')">&#10133;</span>
          <span class="lab-tool" title="跳到末尾" onclick="toast('Demo: 跳到末尾')">&#10142;</span>
          <span class="lab-tool danger" title="删除选段" onclick="toast('Demo: 删除选段')">&#128465;</span>
          <span class="lab-tool" title="区间编辑" onclick="toast('Demo: 区间编辑')">&#8596;</span>
          <span class="lab-tool" title="切分" onclick="toast('Demo: 切分')">&#9986;</span>
          <span class="lab-tool" title="书签" onclick="toast('Demo: 书签')">&#9873;</span>
        </div>
        <a class="lab-tools-right" href="#" onclick="toast('Demo: 任务描述');return false;">&#10140; 任务描述</a>
      </div>
    </div>

    <div class="lab-tbl">
      <table>
        <thead><tr>
          <th class="nowrap" style="width:72px;">序号</th>
          <th class="nowrap" style="width:80px;">开始</th>
          <th class="nowrap" style="width:80px;">结束</th>
          <th class="nowrap" style="width:80px;">时长</th>
          <th class="nowrap" style="width:60px;">颜色</th>
          <th class="nowrap" style="width:200px;">动作元素</th>
          <th class="nowrap">动作描述</th>
          <th class="nowrap" style="width:80px;">缩略图</th>
          <th class="nowrap" style="width:140px;text-align:center;">操作</th>
        </tr></thead>
        <tbody>{body_rows}</tbody>
      </table>
    </div>

    <div class="lab-foot">
      <a class="btn btn-primary" href="#" onclick="toast('Demo: 已提交');return false;">&#9729; 提交</a>
      <a class="btn" href="#" onclick="toast('Demo: 下一条');return false;">下一条 &rsaquo;</a>
    </div>
    """
    return render_page("工作台 · 标注", content, active="/data/workbench", module="data",
                       breadcrumb='数据平台 / 工作台 / <b>标注 #9805</b>', mvp_note="MVP 一期")


# ── 数据看板: 漏斗 + 各环节处理能力 ──
PIPELINE_FUNNEL = [
    {"stage": "采集",     "count": 1250, "daily": 200, "pass_rate": 88, "color": "#7B8FE5"},
    {"stage": "质检",     "count": 1100, "daily": 250, "pass_rate": 92, "color": "#5DCAA5"},
    {"stage": "切分",     "count": 1012, "daily": 180, "pass_rate": 90, "color": "#9B6DBF"},
    {"stage": "标注",     "count":  911, "daily": 120, "pass_rate": 88, "color": "#F0AF7D"},
    {"stage": "标注验收", "count":  802, "daily": 200, "pass_rate": 95, "color": "#E8B940"},
    {"stage": "终验",     "count":  762, "daily": 250, "pass_rate": 98, "color": "#5BB87E"},
]


@app.route("/data/dashboard")
def data_dashboard():
    max_count = max(s["count"] for s in PIPELINE_FUNNEL)
    n = len(PIPELINE_FUNNEL)
    funnel_rows = ""
    for i, s in enumerate(PIPELINE_FUNNEL):
        # 宽度 = min(数量占比, 索引强制收缩) — 保证一定有漏斗形状
        ratio_pct = s["count"] / max_count * 100
        max_pct = 100 - i * (60 / max(n - 1, 1))  # 第一行 100, 最后一行 ~40
        width_pct = round(min(ratio_pct, max_pct))
        funnel_rows += f"""
        <div class="funnel-row">
          <div class="funnel-bar" style="width:{width_pct}%; background:{s['color']};">
            <span class="fb-stage">{s['stage']}</span>
            <span class="fb-num">{s['count']:,} 条</span>
          </div>
        </div>
        """
        # drop indicator (除了最后一个环节)
        if i < len(PIPELINE_FUNNEL) - 1:
            next_count = PIPELINE_FUNNEL[i + 1]["count"]
            loss = s["count"] - next_count
            funnel_rows += f"""
            <div class="funnel-drop">
              <span class="pct">通过率 {s['pass_rate']}%</span>
              <span class="arr">&darr;</span>
              <span class="loss">-{loss:,} 条</span>
            </div>
            """

    cap_rows = ""
    for s in PIPELINE_FUNNEL:
        # 日吞吐率 = daily / count
        ratio = round(s["daily"] / s["count"] * 100, 1)
        ratio_cls = "ok" if ratio >= 25 else ("warn" if ratio >= 12 else "bad")
        # 预计周期 = count / daily days
        days = s["count"] / s["daily"] if s["daily"] else 0
        # 通过率颜色
        pr_cls = "ok" if s["pass_rate"] >= 92 else ("warn" if s["pass_rate"] >= 85 else "bad")
        cap_rows += f"""<tr>
          <td><span class="fk-cap" style="background:{s['color']}22;color:{s['color']};"><b>{s['stage']}</b></span></td>
          <td class="mono"><b>{s['count']:,}</b> 条</td>
          <td class="mono">{s['daily']} / 天</td>
          <td class="fk-ratio {ratio_cls}">{ratio}%</td>
          <td class="mono">{days:.1f} 天</td>
          <td class="fk-ratio {pr_cls}">{s['pass_rate']}%</td>
        </tr>"""

    # Summary stats
    total_in = PIPELINE_FUNNEL[0]["count"]
    total_out = PIPELINE_FUNNEL[-1]["count"]
    e2e_rate = round(total_out / total_in * 100, 1)
    weakest = min(PIPELINE_FUNNEL, key=lambda x: x["daily"] / x["count"])

    content = f"""
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-label">采集端入口</div><div class="stat-value">{total_in:,}</div><div class="stat-sub">条 recording</div></div>
      <div class="stat-card"><div class="stat-label">终验入湖</div><div class="stat-value">{total_out:,}</div><div class="stat-sub">条 episode</div></div>
      <div class="stat-card"><div class="stat-label">端到端通过率</div><div class="stat-value">{e2e_rate}%</div><div class="stat-sub">采集 → 终验</div></div>
      <div class="stat-card"><div class="stat-label">瓶颈环节</div><div class="stat-value" style="color:#d4504e;">{weakest['stage']}</div><div class="stat-sub">日吞吐率最低</div></div>
    </div>

    <div class="dash-row">
      <div class="card">
        <h3>采集 → 标注 数据漏斗</h3>
        <div class="muted" style="font-size:12.5px;margin-bottom:4px;">每个环节的当前数据量 + 通过率 + 流转损耗</div>
        <div class="funnel">{funnel_rows}</div>
      </div>

      <div class="card">
        <h3>各环节处理能力</h3>
        <div class="muted" style="font-size:12.5px;margin-bottom:14px;">日吞吐率 = 日处理量 / 当前积压</div>
        <div class="table-wrap">
          <table class="ant-table">
            <thead><tr>
              <th>环节</th>
              <th>当前</th>
              <th>日处理</th>
              <th>吞吐率</th>
              <th>周期</th>
              <th>通过率</th>
            </tr></thead>
            <tbody>{cap_rows}</tbody>
          </table>
        </div>
      </div>
    </div>
    """
    return render_page("分析看板", content, active="/data/dashboard", module="data",
                       breadcrumb='数据平台 / <b>分析看板</b>', mvp_note="MVP 一期")


# ── 规则管理 ──
RULES = [
    {"id": "RL-001", "name": "缺帧检测规则",       "category": "质检规则",     "stage": "质检",     "type": "自动", "owner": "joanna.qiao", "created": "2026-05-12", "enabled": True,  "desc": "检测 recording 中是否存在缺失帧, 超过 3% 自动判定不合格"},
    {"id": "RL-002", "name": "图像模糊度检测",     "category": "质检规则",     "stage": "质检",     "type": "自动", "owner": "Lance Li",   "created": "2026-05-15", "enabled": True,  "desc": "用 Laplacian 算子检测画面模糊度, 阈值 < 100 自动告警"},
    {"id": "RL-003", "name": "动作分段必备字段",   "category": "标注规则",     "stage": "标注",     "type": "自动", "owner": "joanna.qiao", "created": "2026-05-20", "enabled": True,  "desc": "校验动作分段是否包含起始/结束时间戳, 缺失则不允许提交"},
    {"id": "RL-004", "name": "关键帧标注完整性",   "category": "标注规则",     "stage": "标注",     "type": "自动", "owner": "Wei Zhang",  "created": "2026-05-22", "enabled": False, "desc": "校验关键帧标注数量 >= 5, 缺失关键帧无法通过验收"},
    {"id": "RL-005", "name": "Episode 时长阈值",   "category": "切分规则",     "stage": "切分",     "type": "自动", "owner": "Min Chen",   "created": "2026-05-25", "enabled": True,  "desc": "切分后的 episode 时长 [3s, 60s] 区间外自动标红"},
    {"id": "RL-006", "name": "切分起止动作检测",   "category": "切分规则",     "stage": "切分",     "type": "自动", "owner": "Min Chen",   "created": "2026-05-26", "enabled": True,  "desc": "用动作分类器自动检测 episode 起始/结束姿态"},
    {"id": "RL-007", "name": "标注一致性校验",     "category": "标注验收规则", "stage": "标注验收", "type": "自动", "owner": "joanna.qiao", "created": "2026-05-28", "enabled": True,  "desc": "同一 episode 多个标注员结果一致性 < 0.85 则打回"},
    {"id": "RL-008", "name": "终验抽检比例",       "category": "终验规则",     "stage": "终验",     "type": "手动", "owner": "joanna.qiao", "created": "2026-06-01", "enabled": True,  "desc": "每批次终验抽检 10% (最少 20 条), 不合格则整批退回"},
]


@app.route("/data/rules")
def data_rules():
    cat = request.args.get("cat", "全部")
    all_cats = ["全部", "质检规则", "切分规则", "标注规则", "标注验收规则", "终验规则"]
    if cat not in all_cats:
        cat = "全部"
    counts = {c: sum(1 for r in RULES if c == "全部" or r["category"] == c) for c in all_cats}
    counts["全部"] = len(RULES)
    rules = RULES if cat == "全部" else [r for r in RULES if r["category"] == cat]

    cat_color = {
        "质检规则":     "blue",
        "切分规则":     "purple",
        "标注规则":     "orange",
        "标注验收规则": "amber",
        "终验规则":     "green",
    }

    def _cat_tab(key):
        cls = "tm-tab active" if cat == key else "tm-tab"
        return f'<a class="{cls}" href="/data/rules?cat={key}">{key}<span class="ct">{counts[key]}</span></a>'

    tabs_html = "".join(_cat_tab(c) for c in all_cats)

    rows = ""
    for r in rules:
        color = cat_color.get(r["category"], "blue")
        type_tag = ('<span class="tag tag-blue">自动</span>' if r["type"] == "自动"
                    else '<span class="tag tag-gray">手动</span>')
        enabled_tag = ('<span class="qa qa-pass">启用</span>' if r["enabled"]
                       else '<span class="qa qa-pend">已禁用</span>')
        rows += f"""<tr>
          <td class="mono">{r['id']}</td>
          <td><span class="wb-badge {color}">{r['category']}</span></td>
          <td><b>{r['name']}</b></td>
          <td class="muted" style="max-width:380px;font-size:12.5px;line-height:1.55;">{r['desc']}</td>
          <td>{type_tag}</td>
          <td>{enabled_tag}</td>
          <td>{r['owner']}</td>
          <td class="muted mono">{r['created']}</td>
          <td class="actions-cell">
            <a class="tbtn" href="#" onclick="toast('Demo: 编辑');return false;">编辑</a>
            <a class="tbtn" href="#" onclick="toast('Demo: 启用/禁用');return false;">{'禁用' if r['enabled'] else '启用'}</a>
          </td>
        </tr>"""

    content = f"""
    <div class="tm-bar">
      <div class="tm-tabs">{tabs_html}</div>
      <a class="btn btn-primary" href="#" onclick="toast('Demo: 新增规则');return false;">+ 新增规则</a>
    </div>

    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr>
          <th>规则 ID</th>
          <th>分类</th>
          <th>规则名称</th>
          <th>描述</th>
          <th>执行方式</th>
          <th>状态</th>
          <th>创建人</th>
          <th>创建时间</th>
          <th>操作</th>
        </tr></thead>
        <tbody>{rows or '<tr><td colspan="9" style="text-align:center;padding:30px;color:rgba(0,0,0,0.25);">暂无数据</td></tr>'}</tbody>
      </table>
    </div>
    """
    return render_page("规则管理", content, active="/data/rules", module="data",
                       breadcrumb='数据平台 / <b>规则管理</b>', mvp_note="MVP 一期")


# ── 采集指令 (占位) ──
@app.route("/data/instructions")
def data_instructions():
    content = """
    <div class="card" style="text-align:center;padding:60px 30px;">
      <div style="font-size:48px;color:rgba(0,0,0,0.15);margin-bottom:14px;">&#9881;</div>
      <h3 style="font-size:18px;color:rgba(0,0,0,0.75);margin:0 0 8px;">采集指令</h3>
      <p class="muted" style="max-width:560px;margin:0 auto;line-height:1.7;">
        采集任务下发到边端/外包前的指令模板:<br>
        动作指令树 · 多模态触发条件 · 物料清单 · 异常回报规则
      </p>
      <p class="muted" style="margin-top:16px;font-size:12px;">具体形态待产品定义</p>
    </div>
    """
    return render_page("采集指令", content, active="/data/instructions", module="data",
                       breadcrumb='数据平台 / <b>采集指令</b>', mvp_note="MVP 一期")


# ── 公共配置: 场景/提示词/标签 复用评测平台 handler, 渲染到数据平台 chrome ──
def _ep_to_data(handler, active):
    if not EP_AVAILABLE:
        return render_page("未启用", '<div class="card"><p class="muted">quanta_eval_platform 模块未导入成功。</p></div>',
                           active=active, module="data")
    _eval_capture.clear()
    handler()
    return render_page(
        _eval_capture.get("title", ""),
        _rewrite_ep_links(_eval_capture.get("content", "") or ""),
        active=active, module="data",
    )


@app.route("/data/scenes")
def data_scenes():
    return _ep_to_data(ep.scenes_page, "/data/scenes")


@app.route("/data/prompts")
def data_prompts():
    return _ep_to_data(ep.prompts_page, "/data/prompts")


@app.route("/data/tags")
def data_tags():
    return _ep_to_data(ep.tags_page, "/data/tags")


# ── 公共配置 (旧占位, 保留 URL 不再出现在侧栏) ──
@app.route("/data/config")
def data_config():
    content = """
    <div class="card" style="text-align:center;padding:60px 30px;">
      <div style="font-size:48px;color:rgba(0,0,0,0.15);margin-bottom:14px;">&#9881;</div>
      <h3 style="font-size:18px;color:rgba(0,0,0,0.75);margin:0 0 8px;">公共配置</h3>
      <p class="muted" style="max-width:520px;margin:0 auto;line-height:1.7;">
        跨任务的可复用配置项:<br>
        项目字典 · 标签体系 · 设备型号 · 采集 SOP 模板 · 标注模板
      </p>
      <p class="muted" style="margin-top:16px;font-size:12px;">具体形态待产品定义</p>
    </div>
    """
    return render_page("公共配置", content, active="/data/config", module="data",
                       breadcrumb='数据平台 / <b>公共配置</b>', mvp_note="MVP 一期")


@app.route("/data/process")
def process():
    rows = ""
    for p in PROCESS_JOBS:
        rows += f"""<tr>
          <td class="mono">{p['id']}</td>
          <td><b>{p['task']}</b></td>
          <td>{p['steps']}</td>
          <td>{status_tag(p['status'])}</td>
          <td class="mono">{p['ep_count'] if p['ep_count'] else '—'}</td>
          <td class="muted">{p['dur']}</td>
          <td class="muted mono">{p['at']}</td>
          <td class="actions-cell"><a href="#" onclick="toast('Demo: 查看日志');return false;">日志</a> · <a href="#" onclick="toast('Demo: 重跑');return false;">重跑</a></td>
        </tr>"""
    n_running = sum(1 for p in PROCESS_JOBS if p["status"] == "running")
    n_done = sum(1 for p in PROCESS_JOBS if p["status"] == "done")
    n_failed = sum(1 for p in PROCESS_JOBS if p["status"] == "failed")
    total_eps = sum(p["ep_count"] for p in PROCESS_JOBS if p["status"] == "done")

    content = page_header(
        "自动处理",
        "时间戳对齐 · 抽帧 · 切 Episode",
        "清洗 · 自动预标注 · 数据增强 · 隐私脱敏",
    ) + stat_grid([
        ("处理任务", str(len(PROCESS_JOBS)), f'<span class="ok">成功 {n_done}</span> · <span class="warn">运行 {n_running}</span> · <span class="err">失败 {n_failed}</span>'),
        ("已切分 Episode", f"{total_eps:,}", "供下游质检"),
        ("处理算子", "3 个", "对齐 / 抽帧 / 切片"),
        ("一期 SLA", "P95 < 30m", "100 episode/任务"),
    ]) + f"""
    <div class="filter-bar">
      <input class="grow" placeholder="搜索来源采集任务 / 执行 ID...">
      <select><option>全部状态</option><option>成功</option><option>运行中</option><option>失败</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
      <div class="right">
        <a href="#" class="btn" onclick="toast('Demo: 触发批量重跑');return false;">批量重跑</a>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>执行 ID</th><th>来源采集任务</th><th>处理步骤</th><th>状态</th><th>产出 EP</th><th>耗时</th><th>开始时间</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return render_page("自动处理", content, active="/data/process", module="data",
                       breadcrumb='数据平台 / <b>自动处理</b>', mvp_note="MVP 一期")


@app.route("/data/qc")
def qc():
    rows = ""
    for q in QC_RUNS:
        if q["ep_count"]:
            auto_html = (f'<span class="qa qa-pass">通过 {q["auto_pass"]}</span> · '
                         f'<span class="qa qa-warn">告警 {q["auto_warn"]}</span> · '
                         f'<span class="qa qa-fail">失败 {q["auto_fail"]}</span>')
        else:
            auto_html = '<span class="muted">—</span>'
        human_html = (f'<span class="mono">{q["human_done"]}/{q["human_total"]}</span>'
                      if q["human_total"] else '<span class="muted">无需复核</span>')
        rows += f"""<tr>
          <td class="mono">{q['id']}</td>
          <td><b>{q['task']}</b></td>
          <td class="mono">{q['ep_count']}</td>
          <td>{auto_html}</td>
          <td>{human_html}</td>
          <td>{q['reviewer']}</td>
          <td>{status_tag(q['status'])}</td>
          <td class="muted mono">{q['at']}</td>
          <td class="actions-cell"><a href="#" onclick="toast('Demo: 进入复核界面');return false;">复核</a></td>
        </tr>"""

    total_auto_pass = sum(q["auto_pass"] for q in QC_RUNS)
    total_auto_warn = sum(q["auto_warn"] for q in QC_RUNS)
    total_auto_fail = sum(q["auto_fail"] for q in QC_RUNS)
    total_checked = total_auto_pass + total_auto_warn + total_auto_fail
    pass_rate = f"{total_auto_pass / total_checked * 100:.1f}%" if total_checked else "—"

    content = page_header(
        "质检",
        "自动质检（缺帧 / 异常）+ 人工复核",
        "抖动检测 · 多人复核打回工作流 · 质检看板",
    ) + stat_grid([
        ("质检批次", str(len(QC_RUNS)), "已发起"),
        ("自动通过率", pass_rate, f"通过 {total_auto_pass} / {total_checked}"),
        ("告警 Episode", str(total_auto_warn), "需人工复核"),
        ("失败 Episode", str(total_auto_fail), "已隔离"),
    ]) + f"""
    <div class="filter-bar">
      <input class="grow" placeholder="搜索来源任务...">
      <select><option>全部状态</option><option>复核中</option><option>已完成</option><option>待启动</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>批次 ID</th><th>来源任务</th><th>EP 数</th><th>自动质检</th><th>人工复核</th><th>复核人</th><th>状态</th><th>完成时间</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return render_page("质检", content, active="/data/qc", module="data",
                       breadcrumb='数据平台 / <b>质检</b>', mvp_note="MVP 一期")


@app.route("/data/label")
def label():
    rows = ""
    for lt in LABEL_TASKS:
        bar_cls = "done" if lt["status"] == "done" else ""
        rows += f"""<tr>
          <td class="mono">{lt['id']}</td>
          <td><b>{lt['name']}</b></td>
          <td><span class="tag tag-purple">{lt['template']}</span></td>
          <td>{progress_bar(lt['labeled'], lt['ep_count'], bar_cls) if lt['ep_count'] else '<span class="muted">待数据</span>'}</td>
          <td>{lt['annotator']}</td>
          <td>{status_tag(lt['status'])}</td>
          <td class="muted mono">{lt['created']}</td>
          <td class="actions-cell"><a href="#" onclick="toast('Demo: 进入标注工作台');return false;">标注</a></td>
        </tr>"""

    total_eps = sum(lt["ep_count"] for lt in LABEL_TASKS)
    total_labeled = sum(lt["labeled"] for lt in LABEL_TASKS)
    progress_pct = f"{total_labeled / total_eps * 100:.0f}%" if total_eps else "—"
    n_done = sum(1 for lt in LABEL_TASKS if lt["status"] == "done")

    content = page_header(
        "标注",
        "人工标注: 动作分段 + 关键帧（1 套基础模板）",
        "语言指令 · 抓取点 · 自动预标注 · 多人协同",
    ) + stat_grid([
        ("标注任务", str(len(LABEL_TASKS)), f'<span class="ok">已完成 {n_done}</span>'),
        ("总体进度", progress_pct, f"{total_labeled}/{total_eps} EP"),
        ("启用模板", "1 套", "动作分段 + 关键帧"),
        ("活跃标注员", "3 人", "本周"),
    ]) + f"""
    <div class="filter-bar">
      <input class="grow" placeholder="搜索标注任务...">
      <select><option>全部状态</option><option>进行中</option><option>已完成</option><option>待启动</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
      <div class="right">
        <a href="#" class="btn" onclick="toast('Demo: 新建标注任务');return false;">+ 新建</a>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>任务 ID</th><th>任务名</th><th>模板</th><th>进度</th><th>标注员</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return render_page("标注", content, active="/data/label", module="data",
                       breadcrumb='数据平台 / <b>标注</b>', mvp_note="MVP 一期")


@app.route("/data/datasets")
def datasets():
    rows = ""
    for d in DATASETS:
        src_html = " · ".join(f'<span class="tag tag-teal">{resolve_task_name(s)}</span>' for s in d["source_tasks"])
        split = f'{int(d["train_ratio"]*100)} / {int(d["val_ratio"]*100)} / {int(d["test_ratio"]*100)}'
        type_tag = '<span class="tag tag-blue">训练</span>' if d["type"] == "train" else '<span class="tag tag-purple">评测</span>'
        rows += f"""<tr>
          <td class="mono">{d['id']}</td>
          <td><b>{d['name']}</b></td>
          <td class="mono">{d['version']}</td>
          <td>{type_tag}</td>
          <td class="mono">{d['episodes']}</td>
          <td class="mono">{d['frames']:,}</td>
          <td class="mono">{split}</td>
          <td>{src_html}</td>
          <td>{d['owner']}</td>
          <td>{status_tag(d['status'])}</td>
          <td class="actions-cell"><a href="/model/lineage?ds={d['id']}">血缘</a> · <a href="#" onclick="toast('Demo: 下载');return false;">下载</a></td>
        </tr>"""
    n_active = sum(1 for d in DATASETS if d["status"] == "active")
    n_train = sum(1 for d in DATASETS if d["type"] == "train")
    total_eps = sum(d["episodes"] for d in DATASETS)
    total_frames = sum(d["frames"] for d in DATASETS)

    content = page_header(
        "数据集",
        "数据集版本管理 · train / val / test 划分 · 血缘",
        "数据湖分层 · 数据集卡片 · 语义检索",
    ) + stat_grid([
        ("已生效数据集", str(n_active), f"共 {len(DATASETS)} 个"),
        ("训练数据集", str(n_train), "供训练实验引用"),
        ("总 Episode", f"{total_eps:,}", "覆盖全部数据集"),
        ("总帧数", f"{total_frames:,}", ""),
    ]) + f"""
    <div class="filter-bar">
      <input class="grow" placeholder="搜索数据集...">
      <select><option>全部类型</option><option>训练</option><option>评测</option></select>
      <select><option>全部状态</option><option>已生效</option><option>待启动</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
      <div class="right">
        <a href="#" class="btn" onclick="toast('Demo: 进入数据集构建向导');return false;">+ 新建数据集</a>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>ID</th><th>数据集名</th><th>版本</th><th>类型</th><th>EP</th><th>帧数</th><th>train/val/test</th><th>来源采集任务</th><th>负责人</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return render_page("数据集", content, active="/data/datasets", module="data",
                       breadcrumb='数据平台 / <b>数据集</b>', mvp_note="MVP 一期")


# ── 数据平台 · 复用 data_platform 的 raw / operators / pipelines / runs handler ──
@app.route("/data/raw")
def data_raw():
    return _dp_render(dp.raw_data, "/data/raw", prefix="/data", module="data")


@app.route("/data/operators")
def data_operators():
    return _dp_render(dp.operators, "/data/operators", prefix="/data", module="data")


@app.route("/data/pipelines")
def data_pipelines():
    return _dp_render(dp.pipelines, "/data/pipelines", prefix="/data", module="data")


@app.route("/data/pipelines/<pid>")
def data_pipeline_editor(pid):
    return _dp_render(lambda: dp.pipeline_editor(pid), "/data/pipelines", prefix="/data", module="data")


@app.route("/data/runs")
def data_runs():
    return _dp_render(dp.runs, "/data/runs", prefix="/data", module="data")


# ════════════════════════════════════════════════════════════════
# Section 7: 模型平台 (/model/*)
# ════════════════════════════════════════════════════════════════

@app.route("/model")
def model_home():
    desc = "模型平台承载数据 → 训练 → 部署 → 评测的端到端流水线。挂载数据集、用 GPU 资源池训练、离线 Benchmark 评测后下发到设备平台。"
    content = welcome_card("模型平台", "数据 → 训练 → 部署 → 评测", desc)
    return render_page("模型平台 · 快速入门", content, active="/model", module="model",
                       breadcrumb='<b>模型平台</b> / 快速入门', mvp_note="MVP 一期")


# ════════════════════════════════════════════════════════════════
# 模型平台 · 数据子模块 (集成 data_platform.py 的页面到 Quanta chrome)
# ════════════════════════════════════════════════════════════════
# 做法: 拦截 dp.render_page 收集 (title, content), 然后用 Quanta 的 render_page
# 重新渲染. 这样 data_platform 内部链接/内容保留, 但顶部/侧边导航走 Quanta.

_dp_capture = {}


def _dp_intercept(title, content, active="", breadcrumb=None, extra_script=None, top="data"):
    _dp_capture["title"] = title
    _dp_capture["content"] = content
    _dp_capture["extra_script"] = extra_script
    return ""  # 不参与实际响应, 只是占位


if DP_AVAILABLE:
    dp.render_page = _dp_intercept


# 把 data_platform 内部 href 重写到 /model/data/<...> 前缀
_DP_PATHS = ("lake", "raw", "query", "datasets", "ds_progress", "operators", "pipelines", "runs", "tags")
_DP_LINK_RE = re.compile(r'''(["'])/(''' + "|".join(_DP_PATHS) + r''')([/?"'])''')


def _rewrite_dp_links(html, prefix="/model/data"):
    return _DP_LINK_RE.sub(rf'\1{prefix}/\2\3', html)


def _dp_render(handler_func, active, prefix="/model/data", module="model"):
    if not DP_AVAILABLE:
        return render_page("数据子模块未启用", '<div class="card"><p class="muted">data_platform 模块未导入成功, 请检查 DP_DIR 环境变量或文件路径。</p></div>',
                           active=active, module=module)
    _dp_capture.clear()
    handler_func()
    content = _rewrite_dp_links(_dp_capture.get("content", ""), prefix=prefix)
    if active == "/model/data/raw":
        content = (
            content
            .replace('<div class="ep-tabs raw-tabs">', '<div class="tm-subtabs raw-tabs">', 1)
            .replace('<button class="ep-tab active" onclick="rawTab(this,\'self\')">自采数据</button>',
                     '<button class="ep-tab tm-subtab active" onclick="rawTab(this,\'self\')">自采数据</button>', 1)
            .replace('<button class="ep-tab" onclick="rawTab(this,\'third\')">三方数据</button>',
                     '<button class="ep-tab tm-subtab" onclick="rawTab(this,\'third\')">三方数据</button>', 1)
        )
    extra = _dp_capture.get("extra_script")
    return render_page(_dp_capture.get("title", ""), content,
                       active=active, module=module, extra_script=extra)


@app.route("/model/data")
def model_data_root():
    return redirect("/model/data/datasets")


@app.route("/model/data/query")
def model_data_query():
    if not DP_AVAILABLE:
        return _dp_render(dp.query, "/model/data/query")
    return _dp_render(dp.query, "/model/data/query")


# ── 数据集 ID 映射表（data_platform → toolchain_demo）──
DATA_PLATFORM_DS_MAP = {
    # data_platform 的 ds1, ds4 等映射到 toolchain_demo 的实际数据集
    "ds1": "ds_505",   # clean_whiteboard_v3 → clean_whiteboard_v5 (最接近)
    "ds4": "ds_501",   # 其他数据集的映射（根据实际需要调整）
    # 已存在的 ID 保持不变
    "ds_501": "ds_501",
    "ds_502": "ds_502",
    "ds_503": "ds_503",
    "ds_504": "ds_504",
    "ds_505": "ds_505",
    "DEMO_DS_9001": "DEMO_DS_9001",
    "DEMO_DS_9002": "DEMO_DS_9002",
    "DEMO_DS_9003": "DEMO_DS_9003",
}

def _resolve_dataset_id(dp_id):
    """将 data_platform 的数据集 ID 映射到 toolchain_demo 的 ID"""
    return DATA_PLATFORM_DS_MAP.get(dp_id, dp_id)


@app.route("/model/data/datasets")
def model_data_datasets():
    if not DP_AVAILABLE:
        return _dp_render(dp.datasets, "/model/data/datasets")
    _dp_capture.clear()
    dp.datasets()
    inner = _rewrite_dp_links(_dp_capture.get("content", "") or "")
    extra = _dp_capture.get("extra_script")
    sel = request.args.get("sel") or "ds1"

    # 使用映射后的 ID 生成血缘链接
    resolved_id = _resolve_dataset_id(sel)
    lineage_btn = f'<a class="btn btn-secondary" href="/model/lineage/dataset/{resolved_id}">查看血缘</a> '
    raw_action = (
        '<div><button class="btn btn-secondary" onclick="document.getElementById('
        "'procDrawer').classList.add('active')\">"
    )
    inner = inner.replace(
        raw_action,
        raw_action.replace("<div>", f"<div>{lineage_btn}"),
        1,
    )
    return render_page(_dp_capture.get("title", "数据集"), inner,
                       active="/model/data/datasets", module="model", extra_script=extra)


@app.route("/model/data/datasets/<ds_id>")
def model_data_dataset_detail(ds_id):
    ds = _dataset_by_id_or_name(ds_id) or DATASETS[0]
    src_html = " · ".join(f'<span class="tag tag-teal">{resolve_task_name(s)}</span>' for s in ds["source_tasks"])
    split = f'{int(ds["train_ratio"]*100)} / {int(ds["val_ratio"]*100)} / {int(ds["test_ratio"]*100)}'
    related_exps = [e for e in EXPERIMENTS if e["dataset"] == ds["name"]]
    if not related_exps:
        related_exps = [e for e in EXPERIMENTS if any(m["from_exp"] == e["id"] and m["from_dataset"] == ds["name"] for m in MODELS)]
    exp_rows = "".join(
        f'<tr><td><a href="/model/experiments/{e["id"]}">{e["name"]}</a></td><td>{e["status"]}</td><td>{e["owner"]}</td><td class="mono muted">{e["started"]}</td></tr>'
        for e in related_exps
    ) or '<tr><td colspan="4" class="muted" style="text-align:center;padding:24px;">暂无关联训练任务</td></tr>'
    content = page_header(
        ds["name"],
        f'{ds["version"]} · {ds["type"]} · {ds["episodes"]} episodes',
        "数据集详情 · 版本 · 来源采集任务 · 下游训练",
    ) + f"""
    <div class="lin-actions">
      <a class="btn" href="/model/data/datasets">返回数据集</a>
      <a class="btn btn-secondary" href="/model/lineage/dataset/{ds['id']}">查看血缘</a>
    </div>
    {stat_grid([
        ("Episode", str(ds["episodes"]), ""),
        ("Frames", f'{ds["frames"]:,}', ""),
        ("划分", split, "train / val / test"),
        ("负责人", ds["owner"], status_tag(ds["status"])),
    ])}
    <div class="card">
      <h3 style="margin-top:0;">基本信息</h3>
      <div class="kv-grid">
        <div class="kv"><span>数据集 ID</span><b class="mono">{ds["id"]}</b></div>
        <div class="kv"><span>数据集版本</span><b class="mono">{ds["version"]}</b></div>
        <div class="kv"><span>创建时间</span><b class="mono">{ds["created"]}</b></div>
        <div class="kv"><span>来源采集任务</span><b>{src_html}</b></div>
      </div>
    </div>
    <div class="card" style="margin-top:14px;">
      <h3 style="margin-top:0;">下游训练任务</h3>
      <div class="table-wrap">
        <table class="ant-table">
          <thead><tr><th>训练任务</th><th>状态</th><th>负责人</th><th>开始时间</th></tr></thead>
          <tbody>{exp_rows}</tbody>
        </table>
      </div>
    </div>
    """
    return render_page(ds["name"], content, active="/model/data/datasets", module="model",
                       breadcrumb=f'模型平台 / 数据集 / <b>{ds["name"]}</b>', mvp_note="MVP 一期")


@app.route("/model/data/ds_progress")
def model_data_ds_progress():
    return _dp_render(dp.ds_progress, "/model/data/query")


@app.route("/model/data/raw")
def model_data_raw():
    return _dp_render(dp.raw_data, "/model/data/raw")


@app.route("/model/data/lake")
def model_data_lake():
    return _dp_render(dp.lake, "/model/data/lake")


@app.route("/model/data/operators")
def model_data_operators():
    return _dp_render(dp.operators, "/model/data/operators")


@app.route("/model/data/pipelines")
def model_data_pipelines():
    return _dp_render(dp.pipelines, "/model/data/pipelines")


@app.route("/model/data/pipelines/<pid>")
def model_data_pipeline_editor(pid):
    return _dp_render(lambda: dp.pipeline_editor(pid), "/model/data/pipelines")


@app.route("/model/data/runs")
def model_data_runs():
    return _dp_render(dp.runs, "/model/data/runs")


@app.route("/model/data/tags")
def model_data_tags():
    return _dp_render(dp.tags, "/model/data/tags")


# ════════════════════════════════════════════════════════════════
# 模型平台 · 评测子模块 (集成 quanta_eval_platform.py 的页面到 Quanta chrome)
# ════════════════════════════════════════════════════════════════
# 做法: 拦截 ep.render_page, 自动遍历 ep.app.url_map 把所有路由按 /model/eval/ 前缀
# 重新注册到本应用. endpoint 名保留原名, 这样 ep 内部的 url_for(...) 调用直接生效,
# redirect 也不需要改 Location header. 内容里硬编码的 /tasks /prompts ... 等链接走
# 正则改写.

_eval_capture = {}


def _eval_intercept(title, content, active="", breadcrumb=None):
    _eval_capture["title"] = title
    _eval_capture["content"] = content
    return ""


_EP_PATHS = ("prompts", "tags", "criteria", "scenes", "benchmarks", "tasks",
             "collections", "collect", "evaluate2", "evaluate", "eval-records",
             "leaderboard", "analysis")
_EP_LINK_RE = re.compile(r'''(["'])/(''' + "|".join(_EP_PATHS) + r''')(?=[/?"' #])''')

# 去除评测平台页面里嵌入的浅蓝色提示条 (inline style background:#e6f7ff)
_EP_BLUE_BANNER_RE = re.compile(
    r'<div\b[^>]*style="[^"]*background:\s*#e6f7ff[^"]*"[^>]*>.*?</div>\s*</div>',
    flags=re.DOTALL | re.IGNORECASE,
)


def _rewrite_ep_links(html):
    html = _EP_BLUE_BANNER_RE.sub("", html)
    return _EP_LINK_RE.sub(r'\1/model/eval/\2', html)


def _ep_active_for(path):
    parts = path.strip("/").split("/")
    if len(parts) >= 3:
        return "/" + "/".join(parts[:3])
    return path


def _make_eval_wrapper(orig_view):
    def wrapper(**kwargs):
        _eval_capture.clear()
        resp = orig_view(**kwargs)
        # 1) 若 handler 已经调用了 (被拦截的) render_page, 用我们的 chrome 包一次
        if _eval_capture.get("content") is not None:
            return render_page(
                _eval_capture.get("title", ""),
                _rewrite_ep_links(_eval_capture["content"]),
                active=_ep_active_for(request.path),
                module="model",
            )
        # 2) 若是 redirect/Response, 直接透传 (url_for 已经返回 /model/eval/ 前缀的 URL)
        return resp
    return wrapper


# 不走自动注册的 endpoint, 由下面手动定义 (例如要嵌成 2-tab 的详情页)
_EP_SKIP_AUTO = {"task_detail", "eval_records_page", "leaderboard_page"}

if EP_AVAILABLE:
    ep.render_page = _eval_intercept
    # 自动遍历 ep 的 url_map, 用「原 endpoint 名」注册到本 app, URL 加 /model/eval 前缀.
    # 这样 ep 内部 url_for("xxx_page") 仍能解析, 因为 endpoint 名一致.
    for _rule in list(ep.app.url_map.iter_rules()):
        if _rule.endpoint == "static" or _rule.endpoint in _EP_SKIP_AUTO:
            continue
        _view = ep.app.view_functions.get(_rule.endpoint)
        if not _view:
            continue
        _old = str(_rule)
        if _old == "/":
            continue  # ep 的 home 跳过, 我们有自己的入口
        _new = "/model/eval" + _old
        _methods = sorted(_rule.methods - {"HEAD", "OPTIONS"})
        app.add_url_rule(_new, endpoint=_rule.endpoint,
                         view_func=_make_eval_wrapper(_view), methods=_methods)


@app.route("/model/eval")
def model_eval_root():
    return redirect("/model/eval/tasks")


# 评测任务详情 → 2 tab (基本信息 + 采集任务)
# 采集任务原本是顶层菜单 /collections, 现在按任务维度作为详情页 tab 呈现.

def _eval_task_collections_html(tid):
    """为单个评测任务渲染采集任务表格 (沿用 ep.collections_page 的字段口径)."""
    from datetime import datetime, timedelta
    t = next((x for x in ep.EVAL_TASKS if x["id"] == tid), None)
    if not t:
        return '<div class="muted" style="padding:20px;">未找到该任务</div>'
    bm = ep.get_benchmark(t["benchmark_id"])
    bm_name = bm["name"] if bm else "—"
    total = max(t.get("total_sessions", 1), 1)
    n_models = max(len(t["model_ids"]), 1)
    per_model_done = t.get("collect_done", 0) // n_models if n_models > 0 else 0
    try:
        _c = datetime.strptime(t.get("created_at", ""), "%Y-%m-%d")
        due_str = (_c + timedelta(days=14)).strftime("%Y-%m-%d")
    except Exception:
        due_str = "—"

    rows = ""
    for mid in t["model_ids"]:
        m = next((x for x in ep.MODELS if x["id"] == mid), None)
        if not m:
            continue
        done = min(per_model_done, total)
        pct = round(done / max(total, 1) * 100)
        rows += f"""<tr>
          <td><b>{m["name"]}</b> <span class="muted mono">{m["version"]}</span></td>
          <td>{bm_name}</td>
          <td style="min-width:200px;">
            <div style="display:flex;align-items:center;gap:8px;">
              <div style="flex:1;height:12px;background:#f0f0f0;border-radius:6px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:#149DAA;border-radius:6px;"></div>
              </div>
              <span class="mono" style="font-size:12px;color:rgba(0,0,0,0.65);">{done}/{total}</span>
            </div>
          </td>
          <td class="muted mono">{t.get('created_at', '—')}</td>
          <td class="muted mono">{due_str}</td>
          <td class="actions-cell">
            <a class="tbtn" href="/model/eval/collections/{tid}/{mid}">查看采集</a>
          </td>
        </tr>"""

    return f"""
    <div class="muted" style="margin-bottom:10px;font-size:13px;">
      该任务包含 {n_models} 个模型 × {total} 次 / 模型 = {n_models*total} 个采集 session
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr>
          <th>模型</th><th>Benchmark</th><th>采集进度</th>
          <th>创建时间</th><th>截止时间</th><th>操作</th>
        </tr></thead>
        <tbody>{rows or '<tr><td colspan="6" style="text-align:center;padding:30px;color:rgba(0,0,0,0.25);">暂无数据</td></tr>'}</tbody>
      </table>
    </div>
    """


# 评测结果 = 结果数据 + 排行榜 (2 tab 合并)
# 排行榜内部的 "模型排行榜" 大标题在 tab 下已经冗余 -> 用正则去掉
_EP_LEADERBOARD_TITLE_RE = re.compile(
    r'<span\s+style="font-size:20px;font-weight:600;[^"]*">\s*模型排行榜\s*</span>\s*',
    re.IGNORECASE,
)

# 结果数据页内嵌的 "评测任务视角 / Checkpoint 视角" 二级 tab 用了 ep 的旧蓝色 #1F80A0
# + 简陋 inline 样式. 整段替换成 Quanta 主题色 tab.
_EP_RECORDS_TABBAR_RE = re.compile(
    r'<!--\s*Tab bar\s*-->\s*<div[^>]*display:flex;gap:0;border-bottom[^>]*>\s*'
    r'<a[^>]*view=task[^>]*>.*?</a>\s*'
    r'<a[^>]*view=ckpt[^>]*>.*?</a>\s*</div>',
    re.DOTALL,
)


def _ep_capture_html(handler):
    """调用一个 ep handler, 返回 (title, rewritten_content)."""
    _eval_capture.clear()
    handler()
    title = _eval_capture.get("title", "")
    content = _rewrite_ep_links(_eval_capture.get("content", "") or "")
    return title, content


def _quanta_records_subtabs(view):
    """生成 Quanta 风格的 评测任务视角 / Checkpoint 视角 二级 tab."""
    a_cls = "er-subtab active" if view == "task" else "er-subtab"
    b_cls = "er-subtab active" if view == "ckpt" else "er-subtab"
    return f'''<div class="er-subtabs">
      <a href="/model/eval/eval-records?view=task" class="{a_cls}">评测任务视角</a>
      <a href="/model/eval/eval-records?view=ckpt" class="{b_cls}">Checkpoint 视角</a>
    </div>'''


@app.route("/model/eval/eval-records", endpoint="eval_records_page")
def _eval_results_with_tabs():
    if not EP_AVAILABLE:
        return redirect("/model/eval/tasks")
    _, records_content = _ep_capture_html(ep.eval_records_page)
    _, leaderboard_content = _ep_capture_html(ep.leaderboard_page)
    # 去掉 ep 内嵌的「模型排行榜」标题 (跟 tab 名重复)
    leaderboard_content = _EP_LEADERBOARD_TITLE_RE.sub("", leaderboard_content)
    # 替换结果数据页内的二级 tab 为 Quanta 风格
    view = request.args.get("view", "task")
    if view not in ("task", "ckpt"):
        view = "task"
    records_content = _EP_RECORDS_TABBAR_RE.sub(_quanta_records_subtabs(view), records_content, count=1)
    content = f"""
    <div class="er-wrap">
      <div class="det-tabs er-tabs">
        <span class="det-tab active" onclick="switchDetTab(this,'records')">结果数据</span>
        <span class="det-tab" onclick="switchDetTab(this,'leaderboard')">排行榜</span>
      </div>
      <div id="det-pane-records"     class="det-pane active">{records_content}</div>
      <div id="det-pane-leaderboard" class="det-pane">{leaderboard_content}</div>
    </div>
    """
    return render_page("评测结果", content,
                       active="/model/eval/eval-records", module="model")


# 保留 /model/eval/leaderboard 给 ep 内部 url_for("leaderboard_page") 仍能解析,
# 直接重定向到合并页 (默认结果数据 tab; 用户可手动切换到排行榜).
@app.route("/model/eval/leaderboard", endpoint="leaderboard_page")
def _eval_leaderboard_redirect():
    return redirect("/model/eval/eval-records")


@app.route("/model/eval/tasks/<tid>", endpoint="task_detail")
def _eval_task_detail_with_tabs(tid):
    if not EP_AVAILABLE:
        return redirect("/model/eval/tasks")
    _eval_capture.clear()
    ep.task_detail(tid)
    if _eval_capture.get("content") is None:
        return redirect("/model/eval/tasks")
    basic_content = _rewrite_ep_links(_eval_capture["content"])
    collections_content = _eval_task_collections_html(tid)
    content = f"""
    <div class="det-tabs">
      <span class="det-tab active" onclick="switchDetTab(this,'basic')">基本信息</span>
      <span class="det-tab" onclick="switchDetTab(this,'collections')">采集任务</span>
    </div>
    <div id="det-pane-basic" class="det-pane active">{basic_content}</div>
    <div id="det-pane-collections" class="det-pane">{collections_content}</div>
    """
    return render_page(
        _eval_capture.get("title", "评测任务详情"),
        content,
        active="/model/eval/tasks",
        module="model",
    )


@app.route("/model/experiments")
def experiments():
    rows = ""
    owner_fallbacks = ["tao.wang", "hannah.wang", "joanna.qiao", "Maple Liu", "Min Chen"]
    priority_fallbacks = ["高", "中", "低"]
    for idx, e in enumerate(EXPERIMENTS):
        # 训练任务名称作为可点击链接 (跳到任务详情 → checkpoint 列表)
        status_html = {
            "running": '<span class="tag tag-orange">运行中</span>',
            "done":    '<span class="tag tag-green">成功</span>',
            "failed":  '<span class="tag tag-red">失败</span>',
            "queued":  '<span class="tag tag-blue">排队中</span>',
        }.get(e["status"], f'<span class="tag tag-gray">{e["status"]}</span>')
        owner = e["owner"] if e["owner"] != "—" else owner_fallbacks[idx % len(owner_fallbacks)]
        priority = e.get("priority", priority_fallbacks[idx % len(priority_fallbacks)])
        priority_html = {
            "高": '<span class="tag tag-red">高</span>',
            "中": '<span class="tag tag-orange">中</span>',
            "低": '<span class="tag tag-gray">低</span>',
        }.get(priority, f'<span class="tag tag-gray">{priority}</span>')
        stop_action = (
            f'<a href="#" onclick="confirmStopExperiment({html.escape(e["name"]).__repr__()});return false;">停止</a>'
            if e["status"] == "running"
            else '<span class="action-link action-disabled">停止</span>'
        )
        # 编辑仅在「排队中」状态显示，其余状态不出现在「更多」菜单中
        edit_item = (
            f'<a href="#" onclick="toast(\'Demo: 编辑训练任务\');return false;">编辑</a>'
            if e["status"] in ("queued", "排队中")
            else ''
        )
        more_menu = (
            f'<span class="action-more">'
            f'<span class="action-more-trigger">更多<span class="caret">&#9662;</span></span>'
            f'<span class="action-menu">'
            f'<a href="/model/lineage/train/{e["id"]}">血缘</a>'
            f'{edit_item}'
            f'</span>'
            f'</span>'
        )
        rows += f"""<tr>
          <td><a href="/model/experiments/{e['id']}" style="color:#149DAA">{e['name']}</a></td>
          <td>{status_html}</td>
          <td>{priority_html}</td>
          <td>{owner}</td>
          <td class="muted mono">{e['started']}</td>
          <td class="muted">{e['dur']}</td>
          <td class="actions-cell">
            {stop_action}
            <a href="#" onclick="toast('Demo: 已复制配置');return false;">复制</a>
            {more_menu}
          </td>
        </tr>"""

    running_count = sum(1 for e in EXPERIMENTS if e["status"] == "running")
    total_count = len(EXPERIMENTS)
    content = page_header(
        "训练任务",
        "数据集挂载 · 实验管理 · 超参 · Checkpoint",
        "分布式训练 · 训练监控 (loss 曲线)",
    ) + f"""
    <div class="fb-labeled">
      <div class="ff"><label>名称</label><input placeholder="请输入名称"></div>
      <div class="ff"><label>描述</label><input placeholder="请输入描述"></div>
      <div class="ff"><label>标签</label><select><option>请选择标签</option><option>robotwin</option><option>HouseHold</option><option>pi05</option></select></div>
      <div class="ff"><label>数据集</label><select><option>请选择数据集</option><option>clean_whiteboard_v4</option><option>tidy_desk_v2</option></select></div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>

    <div class="list-summarybar">
      <div class="txt">运行中任务 <b>{running_count}</b> 条，全部任务 <b>{total_count}</b> 条</div>
      <a class="btn btn-primary" onclick="openTrainDrawer();return false;">+ 新增训练任务</a>
    </div>

    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr>
          <th>名称</th>
          <th>状态 &#9662;</th>
          <th>优先级</th>
          <th>创建人</th>
          <th>创建时间 &#x21F5;</th>
          <th>运行时长</th>
          <th>操作</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div class="mini-pager">
      <select><option>10条/页</option><option>20条/页</option><option>50条/页</option></select>
      <span class="pg-btn">&lsaquo;</span>
      <span class="pg-btn active">1</span>
      <span class="pg-btn">2</span>
      <span class="pg-btn">3</span>
      <span class="pg-btn">4</span>
      <span class="muted">...</span>
      <span class="pg-btn">40</span>
      <span class="pg-btn">&rsaquo;</span>
      <input class="pg-goto" placeholder=""><span class="pg-go">go</span>
    </div>

    <div class="drawer drawer-wide" id="drawerNewTrain">
      <div class="drawer-head"><h3>新增训练任务</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
      <div class="drawer-body">

        <div class="fg">
          <label class="fg-req">名称</label>
          <input placeholder="请输入名称（A-z,0-9,_）" maxlength="50" oninput="updateNameCount(this)">
          <div class="fg-hint" style="text-align:right" id="nameCount">0 / 50</div>
        </div>

        <div class="fg">
          <label>描述</label>
          <textarea rows="3" placeholder="请输入训练任务描述，例如任务目标、数据范围或备注说明"></textarea>
        </div>

        <div class="fg">
          <label class="fg-req">镜像</label>
          <div class="tm-subtabs image-mode-tabs">
            <button type="button" class="tm-subtab active" onclick="switchTrainImageMode(this,'default')">默认镜像</button>
            <button type="button" class="tm-subtab" onclick="switchTrainImageMode(this,'custom')">自定义镜像</button>
          </div>
          <div id="trainImageDefault" class="image-mode-panel active">
            <div class="fg-row">
              <div class="fg" style="margin-bottom:0;">
                <label>名称</label>
                <input value="mozbrain" disabled>
              </div>
              <div class="fg" style="margin-bottom:0;">
                <label>版本</label>
                <input value="thor-v1.0.0" disabled>
              </div>
            </div>
          </div>
          <div id="trainImageCustom" class="image-mode-panel">
            <div class="fg-row">
              <div class="fg" style="margin-bottom:0;">
                <label>名称</label>
                <select id="trainImageName" onchange="updateTrainImageVersions()">
                  <option value="" selected disabled>镜像名称</option>
                  <option value="mozbrain_release">mozbrain_release</option>
                  <option value="mozbrain">mozbrain</option>
                  <option value="mozbrain_base">mozbrain_base</option>
                </select>
              </div>
              <div class="fg" style="margin-bottom:0;">
                <label>版本</label>
                <select id="trainImageVersion" onchange="updateTrainImagePath()">
                  <option value="" selected disabled>镜像版本</option>
                </select>
              </div>
            </div>
          </div>
          <div class="image-path-hint">
            <span class="path" id="trainImagePath">spirit-ai-cn-beijing.cr.volces.com/spirit-ai/mozbrain:thor-v1.0.0</span>
          </div>
        </div>

        <div class="fg-row">
          <div class="fg"><label class="fg-req">训练队列</label>
            <select><option>CPU</option><option>GPU-A100</option><option>GPU-H100</option></select>
          </div>
          <div class="fg"><label class="fg-req">实例规格</label>
            <select><option>请选择实例规格</option><option>2 × A100 80GB</option><option>4 × A100 80GB</option><option>8 × H100 80GB</option></select>
          </div>
        </div>

        <div class="fg">
          <label>数据集</label>
          <div class="ds-table">
            <div class="ds-head"><span>数据集名称</span><span>权重</span><span>操作</span></div>
            <div class="ds-row">
              <select><option>请选择数据集</option><option>clean_whiteboard_v4</option><option>tidy_desk_v2</option><option>plant_pour_pilot</option></select>
              <input value="1">
              <span class="ds-confirm" onclick="toast('Demo: 已添加')">确定</span>
            </div>
          </div>
        </div>

        <div class="fg">
          <label class="fg-req">高级配置</label>
          <div class="adv-tabs">
            <span class="at active" onclick="switchAdvTab(this)">Custom configuration</span>
            <span class="at" onclick="switchAdvTab(this)">Base configuration</span>
            <button class="at-reset" onclick="toast('Demo: 已恢复默认')">恢复默认</button>
          </div>
          <textarea id="yamlEditor" class="yaml-area" spellcheck="false"># Quanta 会自动填充 dataset 相关的内容, 不需要填写 dataset 下的 repo_id、root、sample_weights_cfg
# 请确认是否需要修改 checkpoint.tos.prefix, checkpoint 上传到 tos 的路径为 tos://{{bucket}}/{{prefix}}/{{job_

# === Dataset configuration ===
extends: ./base.yaml
use_raw_dataset: true
dataset:
  num_stats_samples: 20000

# eval_dataset:
#   repo_id: "lerobot/OrganizePencilCase"
#   root: "/mnt/vepfs01/output/multi_task/datasets/lerobot/OrganizePencilCase/"
#   sample_weights_cfg: "/mnt/vepfs01/output/multi_task/datasets/lerobot/OrganizePencilCase/2

# === Basic configuration ===
</textarea>
        </div>

        <div class="fg">
          <label class="fg-req">入口命令</label>
          <textarea id="entryCommandEditor" class="entry-command-area" spellcheck="false"># 需要填写个人的 WANDB_API_KEY，如 export WANDB_API_KEY=aaffxxxx
export WANDB_API_KEY=put_your_wandb_api_key_here
export WANDB_BASE_URL=https://api.bandw.top

export XDG_CACHE_HOME=${{XDG_CACHE_HOME:-/mnt/vepfs01/output/qhj/cache/}}
export HF_HOME=${{HF_HOME:-/mnt/vepfs01/output/lmz/cache}}
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_OFFLINE=1

export ENABLE_REPORT_QUANTA=True
export QUANTA_SERVICE_URL="https://quanta.i.spirit-ai.com"

# Quanta 会自动填充 experiment_id 为实际的 experiment_id，请不要修改 yaml 文件路径
bash lerobot/scripts/train_unified.sh --gpus 8 --cuda-devices "0,1,2,3,4,5,6,7" /mnt/vepfs01/output/configs/train.yaml</textarea>
        </div>

      </div>
      <div class="drawer-foot">
        <button class="btn" onclick="closeDrawer()">取消</button>
        <button class="btn btn-primary" onclick="toast('Demo: 训练任务已提交');closeDrawer()">提交创建</button>
      </div>
    </div>
    """
    return render_page("训练任务", content, active="/model/experiments", module="model",
                       breadcrumb='模型平台 / <b>训练任务</b>', mvp_note="MVP 一期")


# ── 训练任务详情 (Checkpoint 列表) ──
def _task_ckpts(exp):
    """根据训练任务生成它的 checkpoint 列表 (step 50000→5000, 每 5000 一档)."""
    prefix = exp["name"][:8]
    return [
        {"step": step, "storage": "18.99GB", "training_loss": "0",
         "validation_loss": "0", "state": "not_cached",
         "location": f"{step:06d}-{prefix}..."}
        for step in range(50000, 0, -5000)
    ]


# ── 实验数据图表: 生成 8 个 mock 时序曲线 ──
def _curve(kind, n=40):
    pts = []
    for i in range(n):
        x = 50 + i * 1000
        if kind == "loss":
            y = 1.5 * math.exp(-i * 0.20) + 0.04 + 0.015 * math.sin(i * 1.3)
        elif kind == "grad_norm":
            y = 8.5 * math.exp(-i * 0.25) + 0.35 + 0.18 * math.cos(i * 1.7)
        elif kind == "lr":
            # warmup -> cosine decay
            if i < 3:
                y = (i + 1) / 3 * 2.5e-5
            else:
                t = (i - 3) / (n - 3)
                y = 2.5e-5 * 0.5 * (1 + math.cos(math.pi * t))
        elif kind == "samples":
            y = i * 80000 + 5000
        elif kind == "episodes":
            y = i * 60 + 5
        elif kind == "epochs":
            y = i * 0.1
        elif kind == "compute_mfu":
            y = 0.187 + 0.012 * math.sin(i * 1.4) + 0.005 * math.sin(i * 4.7)
        elif kind == "dataloading_s":
            y = 0.004 + (0.13 if i in (12, 15, 17, 22) else 0.0)
        else:
            y = i
        pts.append((x, y))
    return pts


def _fmt_num(v):
    if v == 0:
        return "0"
    av = abs(v)
    if av < 1e-3:
        return f"{v:.1e}"
    if av < 1:
        s = f"{v:.3f}".rstrip("0").rstrip(".")
        return s or "0"
    if av < 100:
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return s or "0"
    return f"{int(v)}"


def _sparkline(data, w=240, h=160, color="#F08080"):
    if not data:
        return ""
    xs = [p[0] for p in data]
    ys = [p[1] for p in data]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if y_max == y_min:
        y_max = y_min + 1
    if x_max == x_min:
        x_max = x_min + 1
    pl, pr, pt, pb = 44, 12, 8, 26
    iw, ih = w - pl - pr, h - pt - pb
    pts = []
    for x, y in data:
        px = pl + (x - x_min) / (x_max - x_min) * iw
        py = pt + ih - (y - y_min) / (y_max - y_min) * ih
        pts.append((px, py))
    path = "M " + " L ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts)
    # area fill
    area = path + f" L {pts[-1][0]:.1f},{pt+ih} L {pts[0][0]:.1f},{pt+ih} Z"
    return f'''<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
  <path d="{area}" fill="{color}" fill-opacity="0.08" stroke="none"/>
  <path d="{path}" stroke="{color}" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="{pl-6}" y="{pt+6}" text-anchor="end" font-size="10" fill="#999">{_fmt_num(y_max)}</text>
  <text x="{pl-6}" y="{pt+ih/2+3}" text-anchor="end" font-size="10" fill="#bbb">{_fmt_num((y_max+y_min)/2)}</text>
  <text x="{pl-6}" y="{pt+ih+3}" text-anchor="end" font-size="10" fill="#999">{_fmt_num(y_min)}</text>
  <text x="{pl}" y="{h-10}" font-size="10" fill="#999">{int(x_min)}</text>
  <text x="{(pl+w-pr)/2}" y="{h-10}" text-anchor="middle" font-size="10" fill="#999">{int((x_min+x_max)/2)}</text>
  <text x="{w-pr}" y="{h-10}" text-anchor="end" font-size="10" fill="#999">{int(x_max)}</text>
  <text x="{(pl+w-pr)/2}" y="{h-1}" text-anchor="middle" font-size="10" fill="#666">Step</text>
</svg>'''


# 实验数据 8 个指标 (train/...)
_EXP_METRICS = [
    ("train/compute_mfu",    "compute_mfu"),
    ("train/dataloading_s",  "dataloading_s"),
    ("train/episodes",       "episodes"),
    ("train/epochs",         "epochs"),
    ("train/grad_norm",      "grad_norm"),
    ("train/loss",           "loss"),
    ("train/lr",             "lr"),
    ("train/samples",        "samples"),
]


# 日志 (取截图里的 NCCL timeout pattern, 替换 rank 模拟多条)
def _log_lines():
    base_ts = "2026-06-18 01:53:"
    seqs = [
        ("35", "5", "880874045", "2252", "Rank 5"),
        ("35", "5", "880890395", "732",  None),
        ("35", "6", "908789747", "685",  "Rank 6"),
        ("35", "6", "908877386", "2252", "Rank 6"),
        ("35", "6", "908892744", "732",  None),
        ("36", "4", "075071550", "685",  "Rank 4"),
        ("36", "4", "075199015", "2252", "Rank 4"),
        ("36", "4", "075219614", "732",  None),
        ("36", "0", "253758308", "1376", "Rank 0"),
        ("36", "3", "272805169", "685",  "Rank 3"),
        ("36", "3", "272908455", "2252", "Rank 3"),
        ("36", "3", "272931990", "732",  None),
        ("36", "7", "293760209", "685",  "Rank 7"),
        ("36", "7", "293865705", "2252", "Rank 7"),
        ("36", "7", "293925903", "732",  None),
    ]
    out = []
    for sec, rank, micro, cpp_line, rank_lbl in seqs:
        ts = f"[{base_ts}{sec}] [rank{rank}]:[E617 17:53:{sec}.{micro} ProcessGroupNCCL.cpp:{cpp_line}]"
        if cpp_line == "685":
            out.append(f"{ts} [{rank_lbl}] Watchdog caught collective operation timeout: WorkNCCL(SeqNum=2, OpType=ALLREDUCE, NumelIn=1, NumelOut=1, Timeout(ms)=600000) ran for 60005{rank} milliseconds before timing out.")
        elif cpp_line == "2252":
            out.append(f"{ts} [PG ID 0 PG GUID 0(default_pg) {rank_lbl}]  failure detected by watchdog at work sequence id: 2 PG status: last enqueued work: 2, last completed work: 1")
        elif cpp_line == "732":
            out.append(f"{ts} Stack trace of the failed collective not found, potentially because FlightRecorder is disabled. You can enable it by setting TORCH_NCCL_TRACE_BUFFER_SIZE to a non-zero value.")
        elif cpp_line == "1376":
            out.append(f"{ts} [{rank_lbl}] Future for ProcessGroup abort timed out after 600000 ms")
    return "\n".join(out)


# 时间线 (基于训练任务 3 个生命周期事件)
def _task_timeline(exp):
    return [
        {"state": "running",  "name": "运行中",  "time": exp["started"],            "op": "平台"},
        {"state": "pending",  "name": "开始排队", "time": exp["started"][:-2] + "00", "op": "平台"},
        {"state": "done",     "name": "创建完成", "time": "2026-06-08 00:27:42",     "op": exp["owner"] if exp["owner"] != "—" else "tao.wang"},
    ]


# 训练任务的 trials (一个实验下的多次运行)
def _task_trials(exp):
    base = exp["name"]
    creator = exp["owner"] if exp["owner"] != "—" else "tao.wang"
    return [
        {"name": base, "owner": creator,       "created": exp["started"]},
        {"name": base, "owner": "hannah.wang", "created": "2026-06-09 19:33:51"},
        {"name": base, "owner": "tao.wang",    "created": "2026-06-08 00:27:42"},
    ]


@app.route("/model/experiments/<exp_id>")
def experiment_detail(exp_id):
    e = next((x for x in EXPERIMENTS if x["id"] == exp_id), None)
    if e is None:
        return redirect("/model/experiments")

    owner = e["owner"] if e["owner"] != "—" else "tao.wang"

    # ──── Tab 1: Checkpoint ────
    ckpts = _task_ckpts(e)
    ckpt_rows = ""
    for c in ckpts:
        ckpt_rows += f"""<tr>
          <td class="mono">{c['step']}</td>
          <td class="mono">{c['storage']}</td>
          <td class="mono">{c['training_loss']}</td>
          <td class="mono">{c['validation_loss']}</td>
          <td><span class="tag tag-gray">未缓存</span></td>
          <td><a class="ckpt-loc" href="#" onclick="toast('Demo: 已复制 TOS 路径');return false;"><span class="ll-ic">&#10697;</span>{c['location']}</a></td>
          <td class="actions-cell"><a href="#" style="color:#149DAA" onclick="openCacheModal('{c['step']}', '{c['location']}');return false;">缓存</a></td>
        </tr>"""
    tab_ckpt = f"""
    <h3 class="sec-title">Check point 列表</h3>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr>
          <th>Step</th><th>Storage space</th><th>Training Loss</th>
          <th>Validation loss</th><th>State</th><th>Location</th><th>操作</th>
        </tr></thead>
        <tbody>{ckpt_rows}</tbody>
      </table>
    </div>
    <div class="mini-pager">
      <select><option>10条/页</option><option>20条/页</option></select>
      <span class="pg-btn">&lsaquo;</span><span class="pg-btn active">1</span><span class="pg-btn">2</span><span class="pg-btn">&rsaquo;</span>
      <input class="pg-goto" placeholder=""><span class="pg-go">go</span>
    </div>
    """

    # ──── Tab 2: 实验数据 ────
    chart_cards = ""
    for label, kind in _EXP_METRICS:
        chart_cards += f"""
        <div class="chart-card">
          <div class="chart-title">{label}</div>
          <div class="chart-body">{_sparkline(_curve(kind), color="#F08080")}</div>
          <div class="chart-foot"><span class="dot"></span>{e['name'][:32]}{'...' if len(e['name'])>32 else ''}</div>
        </div>"""
    tab_data = f"""
    <div class="metric-row">
      <input class="mr-search" placeholder="请输入表头名称">
      <div class="mr-right">
        <span class="lc-icon">&#8730;</span>
        <span class="lc-icon">&#9881;</span>
        <span class="lc-icon">&#8635;</span>
      </div>
    </div>
    <div class="metric-row">
      <span class="mr-group">&#9656; train</span>
      <span class="mr-pill active">全部 {len(_EXP_METRICS)}</span>
      <span class="mr-pill">Scalar {len(_EXP_METRICS)}</span>
      <span class="mr-pill dim">Histogram 0</span>
    </div>
    <div class="charts-grid">{chart_cards}</div>
    """

    # ──── Tab 3: 日志 ────
    log_text = _log_lines()
    tab_logs = f"""
    <div class="logs-pane">
      <div class="logs-subtabs">
        <span class="ls-tab active" data-log-tab="history" onclick="switchLogSubtab(this)">历史日志</span>
        <span class="ls-tab" data-log-tab="realtime" onclick="switchLogSubtab(this)">实时日志</span>
      </div>

      <div class="log-subpane active" data-log-pane="history">
        <div class="logs-box">
          <div class="logs-controls">
            <div class="lc-grp"><select><option>全部实例</option><option>worker-0</option><option>worker-1</option><option>worker-2</option></select></div>
            <div class="lc-grp"><select><option>all</option><option>stdout</option><option>stderr</option></select></div>
            <button class="lc-btn" onclick="toast('Demo: 选择时间范围')">&#9719; 近24小时</button>
            <div class="lc-right">
              <span>时间戳</span><span class="lc-toggle on" onclick="toggleLogToggle(this)"></span>
            </div>
          </div>
          <pre class="logs-body">{log_text}</pre>
        </div>
        <div class="logs-pager">
          <span class="pg-btn active">1</span><span class="pg-btn">2</span><span class="muted">...</span><span class="pg-btn">&rsaquo;</span>
          <select><option>500 条/页</option><option>100 条/页</option></select>
        </div>
      </div>

      <div class="log-subpane" data-log-pane="realtime">
        <div class="logs-box">
          <div class="logs-controls">
            <span class="lc-pill">实时加载中</span>
            <div class="lc-grp"><select><option>请选择实例</option><option>worker-0</option><option>worker-1</option><option>worker-2</option></select></div>
            <span style="color:rgba(0,0,0,0.35);font-size:13px;">&#9432;</span>
            <div class="lc-right">
              <span>查看最新 &#9432;</span>
              <input class="lc-num" value="100"> <span>行</span>
              <span>时间戳</span><span class="lc-toggle on" onclick="toggleLogToggle(this)"></span>
              <span>自动更新</span><span class="lc-toggle on" onclick="toggleLogToggle(this)"></span>
            </div>
          </div>
          <div class="logs-empty">
            <div class="emp-icon">EMP</div>
            <div>暂无实时日志，详情请查看历史日志</div>
          </div>
        </div>
      </div>
    </div>
    """

    # ──── Tab 4: 时间线 ────
    tl_html = ""
    for ev in _task_timeline(e):
        dot_inner = "&#10003;" if ev["state"] == "done" else ""
        tl_html += f"""
        <div class="tl-evt">
          <div class="tl-dot {ev['state']}">{dot_inner}</div>
          <div>
            <div class="tl-name">{ev['name']}</div>
            <div class="tl-meta"><span>{ev['time']}</span><span>操作人: {ev['op']}</span></div>
          </div>
        </div>"""
    tab_timeline = f"""
    <div class="timeline-pane">
      <div class="tl-section-title"><span class="tl-ic">&#9776;</span>任务</div>
      <div class="tl-events">{tl_html}</div>
    </div>
    """

    # ──── Tab 5: 基础信息 (复用新建抽屉里的内容, 只读展示) ────
    yaml_text = """# Quanta 会自动填充 dataset 相关的内容, 不需要填写 dataset 下的 repo_id、root、sample_weights_cfg
# 请确认是否需要修改 checkpoint.tos.prefix, checkpoint 上传到 tos 的路径为 tos://{bucket}/{prefix}/{job_

# === Dataset configuration ===
extends: ./base.yaml
use_raw_dataset: true
dataset:
  num_stats_samples: 20000

# eval_dataset:
#   repo_id: "lerobot/OrganizePencilCase"
#   root: "/mnt/vepfs01/output/multi_task/datasets/lerobot/OrganizePencilCase/"
#   sample_weights_cfg: "/mnt/vepfs01/output/multi_task/datasets/lerobot/OrganizePencilCase/2

# === Basic configuration ===
"""
    ds_name = e["dataset"] if e["dataset"] != "—" else "clean_whiteboard_v4"
    tab_basic = f"""
    <div class="basic-info">
      <div class="bi-section">
        <div class="bi-label">训练任务名称</div>
        <div class="bi-value code">{e['name']}</div>
      </div>
      <div class="bi-section">
        <div class="bi-label">镜像</div>
        <div class="bi-value code">spirit-train:v1.7-cuda12</div>
      </div>
      <div class="bi-row">
        <div class="bi-section">
          <div class="bi-label">训练队列</div>
          <div class="bi-value">GPU-A100</div>
        </div>
        <div class="bi-section">
          <div class="bi-label">实例规格</div>
          <div class="bi-value">2 &times; A100 80GB</div>
        </div>
      </div>
      <div class="bi-section">
        <div class="bi-label">数据集</div>
        <div class="bi-dstable">
          <div class="ds-head"><span>数据集名称</span><span>权重</span></div>
          <div class="ds-row"><span class="mono">{ds_name}</span><span class="mono">1</span></div>
        </div>
      </div>
      <div class="bi-section">
        <div class="bi-label">高级配置</div>
        <div class="adv-tabs">
          <span class="at active" onclick="switchAdvTab(this)">Custom configuration</span>
          <span class="at" onclick="switchAdvTab(this)">Base configuration</span>
        </div>
        <pre class="yaml-readonly">{yaml_text}</pre>
      </div>
    </div>
    """

    # 运行记录 (trials) 列表
    trials = _task_trials(e)
    trial_items = ""
    for i, t in enumerate(trials):
        cls = " active" if i == 0 else ""
        trial_items += f"""
        <a class="tlp-item{cls}" href="#" onclick="selectTrial(this);return false;">
          <span class="ti-ic">&#9783;</span>
          <span>{t['name']}</span>
        </a>"""

    pane_trials = f"""
    <div class="tdsplit">
      <div class="tlp">
        <span class="tlp-collapse" onclick="toast('Demo: 收起左侧')" title="收起">&lsaquo;</span>
        {trial_items}
      </div>
      <div class="tdm">
        <div class="ts-tabs">
          <span class="ts-tab active" onclick="switchTrialTab(this,'ckpt')">Checkpoint</span>
          <span class="ts-tab" onclick="switchTrialTab(this,'logs')">日志</span>
          <span class="ts-tab" onclick="switchTrialTab(this,'timeline')">时间线</span>
        </div>
        <div id="ts-pane-ckpt"     class="ts-pane active">{tab_ckpt}</div>
        <div id="ts-pane-logs"     class="ts-pane">{tab_logs}</div>
        <div id="ts-pane-timeline" class="ts-pane">{tab_timeline}</div>
      </div>
    </div>
    """

    # 顶层结构: 头卡片 + 3 顶 tab + 3 pane
    content = f"""
    <div class="tdh">
      <div class="tdh-name">{e['name']}</div>
      <div class="tdh-actions">
        <a class="btn" href="/model/lineage/train/{e['id']}">查看血缘</a>
      </div>
      <div class="tdh-meta">
        <div><span class="lbl">创建人:</span><span class="val">{owner}</span></div>
        <div><span class="lbl">创建时间:</span><span class="val">{e['started']}</span></div>
      </div>
    </div>

    <div class="det-tabs">
      <span class="det-tab active" onclick="switchDetTab(this,'trials')">运行记录</span>
      <span class="det-tab" onclick="switchDetTab(this,'data')">实验看板</span>
      <span class="det-tab" onclick="switchDetTab(this,'basic')">基础信息</span>
    </div>

    <div id="det-pane-trials"  class="det-pane active">{pane_trials}</div>
    <div id="det-pane-data"    class="det-pane">{tab_data}</div>
    <div id="det-pane-basic"   class="det-pane">{tab_basic}</div>

    <div class="modal-mask" id="cacheModalMask" onclick="closeCacheModal()">
      <div class="modal" id="cacheModalBox" onclick="event.stopPropagation()">
        <div class="modal-head" id="cacheModalHead">
          <h3>缓存 Checkpoint</h3>
          <span class="dismiss" onclick="closeCacheModal()">&times;</span>
        </div>
        <div class="modal-body">
          <div id="cacheModalForm">
            <div class="fg">
              <label class="fg-req">描述</label>
              <textarea id="cacheDesc" rows="4" placeholder="请输入本次缓存说明，例如候选版本用途、关联评测或保留原因"></textarea>
            </div>
          </div>
          <div id="cacheModalDoing" style="display:none;">
            <div class="cache-state">
              <span class="cache-hourglass">&#8987;</span>
              <div>
                <h4>缓存中</h4>
                <p>可在「缓存进度列表」查看</p>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-foot" id="cacheModalFootForm">
          <button class="btn btn-tertiary" onclick="closeCacheModal()">取消</button>
          <button class="btn btn-primary" onclick="confirmCacheModal()">确认</button>
        </div>
        <div class="modal-foot" id="cacheModalFootDoing" style="display:none;">
          <button class="btn btn-secondary" onclick="closeCacheModal()">关闭</button>
          <a class="btn btn-primary" href="/model/checkpoints/cache-records">查看进度</a>
        </div>
      </div>
    </div>
    """
    return render_page(e["name"], content, active="/model/experiments", module="model",
                       breadcrumb=f'模型平台 / 训练任务 / <b>{e["name"]}</b>', mvp_note="MVP 一期")


@app.route("/model/deploy")
def deploy():
    def _multi_query(name, alias=None):
        values = []
        raw_values = request.args.getlist(name)
        if alias:
            raw_values += request.args.getlist(alias)
        for raw in raw_values:
            for item in raw.split(","):
                item = item.strip()
                if item:
                    values.append(item)
        return list(dict.fromkeys(values))

    checkpoint_filters = _multi_query("checkpoint", "ckpt")
    people_filters = _multi_query("people", "operator")
    device_filters = _multi_query("device")
    deploy_checkpoint = request.args.get("deploy_checkpoint", "").strip()
    open_deploy_drawer = request.args.get("open") == "deploy" or bool(deploy_checkpoint)

    def _remote_filter_html(name, placeholder, options, selected):
        selected_set = set(selected)
        value_attr = html.escape(",".join(selected), quote=True)
        chips = "".join(
            f'<span class="rf-chip" data-value="{html.escape(item, quote=True)}"><span>{html.escape(item)}</span><i onclick="removeRemoteFilterChip(this,event)">×</i></span>'
            for item in selected
        )
        option_html = "".join(
            f'<div class="rf-option {"on" if opt in selected_set else ""}" data-value="{html.escape(opt, quote=True)}" onclick="toggleRemoteFilterOption(this)">'
            f'<span class="rf-value">{html.escape(opt)}</span><span class="rf-check">✓</span></div>'
            for opt in options
        )
        return f"""
        <div class="remote-filter" data-name="{name}">
          <input class="rf-hidden" type="hidden" name="{name}" value="{value_attr}">
          <div class="rf-control" onclick="focusRemoteFilter(this)">
            {chips}
            <input type="text" placeholder="{html.escape(placeholder, quote=True)}" onfocus="openRemoteFilter(this)" oninput="filterRemoteFilterOptions(this)">
          </div>
          <div class="rf-menu">{option_html}</div>
        </div>
        """

    def deploy_progress_html(d):
        total = max(len(d["targets"]), 1)
        progress = d.get("progress") or {}
        success = min(progress.get("success", total if d["status"] == "deployed" else 0), total)
        failed = min(progress.get("failed", 0), total - success)
        running = min(progress.get("running", max(total - success - failed, 0)), total - success - failed)
        running_tip = f'<span><i class="dp-dot running"></i>部署中: {running}</span>' if running else ""
        return (
            f'<span class="deploy-progress">'
            f'<span class="dp-success-num">{success}</span><span class="dp-sep">/</span>'
            f'<span class="dp-failed-num">{failed}</span><span class="dp-sep">/</span>'
            f'<span class="dp-total-num">{total}</span>'
            f'<span class="dp-tip">'
            f'<span><i class="dp-dot success"></i>部署成功: {success}</span>'
            f'<span><i class="dp-dot failed"></i>部署失败: {failed}</span>'
            f'<span><i class="dp-dot total"></i>全部: {total}</span>'
            f'{running_tip}'
            f'</span>'
            f'</span>'
        )

    def fmt_dt_seconds(value):
        if not value or value == "—":
            return "—"
        return value if re.search(r"\d{2}:\d{2}:\d{2}$", value) else f"{value}:00"

    rows = ""
    for d in DEPLOYS:
        n = len(d["targets"])
        ckpt_name = f"{d['model']}_{d['version']}"
        if checkpoint_filters and not any(item.lower() in ckpt_name.lower() for item in checkpoint_filters):
            continue
        if people_filters and not any(item.lower() in d["operator"].lower() for item in people_filters):
            continue
        if device_filters and not any(item.lower() in tgt.lower() for item in device_filters for tgt in d["targets"]):
            continue
        created_at = fmt_dt_seconds(d.get("created") or ("2026-07-02 10:24" if d["status"] == "in_progress" else d["at"]))
        finished_at = fmt_dt_seconds(d["at"])
        progress = d.get("progress") or {}
        dev_states = (
            ["success"] * progress.get("success", 0)
            + ["failed"] * progress.get("failed", 0)
            + ["running"] * progress.get("running", 0)
        )
        state_labels = {"success": "成功", "failed": "失败", "running": "部署中"}
        devs_links = "".join(
            f'<a href="/device/devices"><span class="dev-id">{tgt}</span>'
            f'<span class="dev-state {state}">{state_labels[state]}</span></a>'
            for tgt, state in zip(d["targets"], dev_states + ["running"] * max(0, n - len(dev_states)))
        )
        targets_cell = (
            f'<div class="devs-cell">'
            f'<span class="devs-pill" onclick="toggleDevsPop(this, event)">{n}台 <span class="ca">&#9662;</span></span>'
            f'<div class="devs-pop">{devs_links}</div>'
            f'</div>'
        )
        rows += f"""<tr>
          <td class="mono">{d['id']}</td>
          <td><b>{ckpt_name}</b></td>
          <td><span class="tag tag-gray">{d.get('trigger', '手动部署')}</span></td>
          <td>{targets_cell}</td>
          <td>{deploy_progress_html(d)}</td>
          <td>{d['operator']}</td>
          <td class="muted mono">{created_at}</td>
          <td class="muted mono">{finished_at}</td>
        </tr>"""
    running_count = sum(1 for d in DEPLOYS if d["status"] == "in_progress")
    deploy_ckpt_names = [c["name"] for c in CHECKPOINTS]
    selected_deploy_ckpt = deploy_checkpoint if deploy_checkpoint in deploy_ckpt_names else ""
    ckpt_items = ""
    for c in CHECKPOINTS:
        value = c["name"]
        desc = _ckpt_desc(c)
        active = " on" if value == selected_deploy_ckpt else ""
        ckpt_items += (
            f'<div class="ddp-item{active}" data-value="{html.escape(value, quote=True)}" '
            f'data-desc="{html.escape(desc, quote=True)}" onclick="selectDeployCheckpoint(this)">'
            f'<span class="ddp-copy"><span class="ddp-main">{html.escape(value)}</span>'
            f'<span class="ddp-sub">{html.escape(desc)}</span></span>'
            f'<span class="ddp-check">已选</span></div>'
        )
    checkpoint_filter_options = sorted({f"{d['model']}_{d['version']}" for d in DEPLOYS})
    people_filter_options = sorted({d["operator"] for d in DEPLOYS})
    device_filter_options = sorted({target for d in DEPLOYS for target in d["targets"]})
    purpose_map = {"moz1-001": "真机评测", "moz1-002": "部署验证", "moz1-003": "训练回归", "moz2-001": "采集", "moz2-002": "备用"}
    device_items = ""
    for d in DEVICES:
        if d["status"] == "offline":
            continue
        serial = d["id"]
        device_name = d["name"].replace(serial, "", 1).strip(" ·") or d["name"]
        option_label = f"{device_name} · {serial}"
        purpose = purpose_map.get(serial, "训练回归")
        device_items += (
            f'<div class="ddp-item" data-id="{html.escape(serial, quote=True)}" '
            f'data-label="{html.escape(option_label, quote=True)}" onclick="toggleDeployDevice(this)">'
            f'<span class="ddp-copy"><span class="ddp-main">{html.escape(device_name)} · '
            f'<span class="serial">{html.escape(serial)}</span></span>'
            f'<span class="ddp-sub">{html.escape(purpose)}</span></span>'
            f'<span class="ddp-check">已选</span></div>'
        )
    content = page_header(
        "部署任务",
        "Checkpoint 下发到指定设备 · 状态 + 操作历史",
        "灰度发布 · 回滚 · OTA 兼容性矩阵",
    ) + f"""
    <div class="fb-labeled">
      <div class="ff"><label>checkpoint</label>{_remote_filter_html("checkpoint", "请输入 checkpoint", checkpoint_filter_options, checkpoint_filters)}</div>
      <div class="ff"><label>操作人</label>{_remote_filter_html("people", "请输入操作人", people_filter_options, people_filters)}</div>
      <div class="ff"><label>设备序列号</label>{_remote_filter_html("device", "请输入设备序列号", device_filter_options, device_filters)}</div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetDeployFilters()">重置</button>
        <button class="btn btn-primary" onclick="queryDeployFilters(this)">查询</button>
      </div>
    </div>
    <div class="list-summarybar">
      <div class="txt">进行中任务 <b>{running_count}</b> 条</div>
      <a href="#" class="btn btn-primary" onclick="openDrawer('drawerDeploy');return false;">新建部署任务</a>
    </div>
    <div class="table-wrap deploy-table-wrap">
      <table class="ant-table">
        <thead><tr><th>ID</th><th>checkpoint</th><th>触发方式</th><th>目标设备</th><th>部署进度</th><th>操作人</th><th>创建时间</th><th>完成时间</th></tr></thead>
        <tbody>{rows or '<tr><td colspan="8" style="text-align:center;padding:40px;color:rgba(0,0,0,0.25);">暂无匹配部署任务</td></tr>'}</tbody>
      </table>
    </div>
    <div class="drawer" id="drawerDeploy">
      <div class="drawer-head"><h3>新建部署</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
      <div class="drawer-body">
        <div class="fg"><label>checkpoint</label>
          <div class="deploy-checkpoint-picker">
            <input type="hidden" class="dcp-hidden" value="{html.escape(selected_deploy_ckpt, quote=True)}">
            <div class="ddp-control" onclick="openDeployCheckpointPicker(this)">
              <input class="dcp-search" placeholder="请选择 checkpoint" value="{html.escape(selected_deploy_ckpt, quote=True)}" onfocus="openDeployCheckpointPicker(this)" oninput="filterDeployCheckpoints(this)">
            </div>
            <div class="ddp-menu">{ckpt_items}</div>
          </div>
        </div>
        <div class="fg">
          <label>部署设备</label>
          <div class="deploy-device-picker">
            <div class="ddp-control ddp-chips" onclick="openDeployDevicePicker(this)">
              <input class="ddp-search" placeholder="搜索设备序列号" onfocus="openDeployDevicePicker(this)" oninput="filterDeployDevices(this)">
            </div>
            <div class="ddp-menu">{device_items}</div>
          </div>
        </div>
      </div>
      <div class="drawer-foot">
        <button class="btn" onclick="closeDrawer()">取消</button>
        <button class="btn btn-primary" onclick="toast('Demo: 部署已下发 → 设备平台 OTA 执行');closeDrawer()">部署</button>
      </div>
    </div>
    """
    extra_script = ""
    if open_deploy_drawer:
        extra_script = """
        <script>
        document.addEventListener('DOMContentLoaded', function(){
          openDrawer('drawerDeploy');
        });
        </script>
        """
    return render_page("部署", content, active="/model/deploy", module="model",
                       breadcrumb='模型平台 / <b>部署</b>', mvp_note="MVP 一期",
                       extra_script=extra_script)


@app.route("/model/models")
def models():
    rows = ""
    for m in MODELS:
        deploy_html = " · ".join(f'<span class="tag tag-coral">{d}</span>' for d in m["deployed_to"]) if m["deployed_to"] else '<span class="muted">未部署</span>'
        rows += f"""<tr>
          <td class="mono">{m['id']}</td>
          <td><b>{m['name']}</b></td>
          <td class="mono">{m['version']}</td>
          <td><span class="tag tag-purple">{m['base']}</span></td>
          <td class="mono"><a href="/model/experiments">{m['from_exp']}</a></td>
          <td class="mono"><a href="/data/datasets">{m['from_dataset']}</a></td>
          <td>{deploy_html}</td>
          <td>{m['owner']}</td>
          <td class="muted mono">{m['created']}</td>
          <td class="actions-cell"><a href="/model/lineage?model={m['id']}">血缘</a></td>
        </tr>"""
    content = page_header(
        "模型仓库",
        "模型 Registry · 版本 · 血缘 (数据集 → 实验 → 模型)",
        "Prompt 管理 · 镜像 · 标签体系",
    ) + f"""
    <div class="filter-bar">
      <input class="grow" placeholder="搜索模型名...">
      <select><option>全部基础模型</option><option>Spirit v1.7</option><option>Spirit v1.6</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>ID</th><th>模型名</th><th>版本</th><th>基础模型</th><th>来源实验</th><th>来源数据集</th><th>已部署设备</th><th>负责人</th><th>创建时间</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return render_page("模型仓库", content, active="/model/models", module="model",
                       breadcrumb='模型平台 / <b>模型仓库</b>', mvp_note="MVP 一期")


# ── 训练 · Checkpoint ──
CKPT_STATUS_LABEL = {
    "unmerged":     '<span class="tag tag-gray">未合并</span>',
    "merging":      '<span class="tag tag-blue">合并中</span>',
    "merge_failed": '<span class="tag tag-red">合并失败</span>',
    "not_cached":   '<span class="tag tag-gray">未缓存</span>',
    "caching":      '<span class="tag tag-blue">缓存中</span>',
    "cached":       '<span class="tag tag-green">已缓存</span>',
    "cache_failed": '<span class="tag tag-red">缓存失败</span>',
}

CKPT_DESC_FALLBACKS = [
    "HouseHold stop 32 任务 40k step 稳定版本",
    "opd taskA SFT 50k step 候选版本",
    "HouseHold stop 32 任务 50k step 对照版本",
    "taskAB 单模型无 BC loss 版本",
    "HouseHold stop 32 任务 40k step 合并失败待处理",
]


def _ckpt_desc(ckpt):
    if ckpt.get("description"):
        return ckpt["description"]
    idx = next((i for i, item in enumerate(CHECKPOINTS) if item["id"] == ckpt["id"]), 0)
    return CKPT_DESC_FALLBACKS[idx % len(CKPT_DESC_FALLBACKS)]


def _ckpt_train_step(ckpt):
    m = re.search(r"_(\d{4,7})$", ckpt["name"])
    return m.group(1) if m else "—"


def _ckpt_status_log(ckpt):
    if ckpt["status"] == "merge_failed":
        return "\n".join([
            f"[{ckpt['created']}] merge_worker: start merge checkpoint {ckpt['id']}",
            "merge_worker: safetensors index mismatch, missing shard model-00007-of-00008",
            "merge_worker: checksum validation failed, output checkpoint has been discarded",
            "suggestion: 重新拉取源 checkpoint 后重试合并任务",
        ])
    if ckpt["status"] == "cache_failed":
        return "\n".join([
            f"[{ckpt['created']}] cache_worker: start cache checkpoint {ckpt['id']}",
            "cache_worker: TOS object fetch timeout after 3 retries",
            "cache_worker: failed to materialize checkpoint files to cache volume",
            "suggestion: 检查源路径权限和对象完整性后重新发起缓存",
        ])
    return ""


def _ckpt_status_cell_html(ckpt, with_log=False):
    tag = CKPT_STATUS_LABEL.get(ckpt["status"], ckpt["status"])
    if not with_log or ckpt["status"] not in {"merge_failed", "cache_failed"}:
        return tag
    title = "日志"
    log = html.escape(_ckpt_status_log(ckpt), quote=True)
    title_attr = html.escape(title, quote=True)
    return (
        f'<span class="status-with-log">{tag}'
        f'<button type="button" class="status-log-icon" title="查看日志" '
        f'data-title="{title_attr}" data-log="{log}" onclick="openCkptStatusLog(this)">i</button>'
        f'</span>'
    )


def _ckpt_detail_drawers(items):
    drawers = ""
    for c in items:
        exp = _ckpt_exp(c)
        train_name = exp["name"] if exp else "—"
        base_model = exp["model_type"] if exp else "—"
        desc = _ckpt_desc(c)
        step = _ckpt_train_step(c)
        drawers += f"""
        <div class="drawer" id="drawerCkpt{c['id']}">
          <div class="drawer-head"><h3>Checkpoint 详情</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
          <div class="drawer-body">
            <h2 class="ckpt-detail-title">{c['name']}</h2>
            <div class="ckpt-form">
              <div class="ckpt-form-row"><label>checkpoint</label><div class="ckpt-form-value">{c['name']}</div></div>
              <div class="ckpt-form-row"><label>描述</label><div class="ckpt-form-value">{desc}</div></div>
              <div class="ckpt-form-row"><label>训练任务</label><div class="ckpt-form-value">{train_name}</div></div>
              <div class="ckpt-form-row"><label>基础模型</label><div class="ckpt-form-value">{base_model}</div></div>
              <div class="ckpt-form-row"><label>训练步数</label><div class="ckpt-form-value mono">{step}</div></div>
              <div class="ckpt-form-row"><label>创建人</label><div class="ckpt-form-value">{c['owner']}</div></div>
              <div class="ckpt-form-row"><label>创建时间</label><div class="ckpt-form-value mono">{c['created']}</div></div>
            </div>
          </div>
          <div class="drawer-foot">
            <a class="btn btn-secondary" href="/model/lineage/checkpoint/{c['id']}">查看血缘</a>
            <button class="btn" onclick="closeDrawer()">关闭</button>
          </div>
        </div>
        """
    return drawers


def _ckpt_rows_html(items, show_actions=True, show_status=True, status_logs=False):
    rows = ""
    for idx, c in enumerate(items):
        desc = _ckpt_desc(c)
        status_cell = f"<td>{_ckpt_status_cell_html(c, status_logs)}</td>" if show_status else ""
        actions_cell = ""
        if show_actions:
            deploy_href = f"/model/deploy?open=deploy&deploy_checkpoint={quote(c['name'], safe='')}"
            actions_cell = f"""<td class="actions-cell">
            <a href="#" onclick="openTaskCapabilityModal();return false;">TEST</a>
            <a href="#" onclick="openTaskCapabilityModal();return false;">DAgger</a>
            <a href="{deploy_href}">部署</a>
            <a href="/model/lineage/checkpoint/{c['id']}">血缘</a>
          </td>"""
        rows += f"""<tr data-status="{c['status']}">
          <td class="mono">{c['id']}</td>
          <td><a class="ckpt-name-cell" href="#" onclick="openDrawer('drawerCkpt{c['id']}');return false;" title="{c['name']}">{c['name']}</a></td>
          <td class="muted">{desc}</td>
          {status_cell}
          <td>{c['owner']}</td>
          <td class="muted mono">{c['created']}</td>
          {actions_cell}
        </tr>"""
    return rows


def _ckpt_table_html(items, show_actions=True, show_status=True, status_filter=False, status_logs=False):
    status_col = '<col style="width:150px;">' if show_status and status_filter else ('<col style="width:110px;">' if show_status else "")
    if show_status and status_filter:
        status_head = """<th>
            <div class="ckpt-status-filter">
              <button type="button" class="ckpt-status-trigger" onclick="toggleCkptStatusFilter(this)">状态 <span class="caret">&#8963;</span></button>
              <div class="ckpt-status-menu">
                <button type="button" class="ckpt-status-option active" data-value="" onclick="selectCkptStatusFilter(this)">全部</button>
                <button type="button" class="ckpt-status-option" data-value="unmerged" onclick="selectCkptStatusFilter(this)">未合并</button>
                <button type="button" class="ckpt-status-option" data-value="merging" onclick="selectCkptStatusFilter(this)">合并中</button>
                <button type="button" class="ckpt-status-option" data-value="merge_failed" onclick="selectCkptStatusFilter(this)">合并失败</button>
                <button type="button" class="ckpt-status-option" data-value="not_cached" onclick="selectCkptStatusFilter(this)">未缓存</button>
                <button type="button" class="ckpt-status-option" data-value="caching" onclick="selectCkptStatusFilter(this)">缓存中</button>
                <button type="button" class="ckpt-status-option" data-value="cached" onclick="selectCkptStatusFilter(this)">已缓存</button>
                <button type="button" class="ckpt-status-option" data-value="cache_failed" onclick="selectCkptStatusFilter(this)">缓存失败</button>
              </div>
            </div>
          </th>"""
    else:
        status_head = "<th>状态 &#9662;</th>" if show_status else ""
    actions_col = '<col style="width:230px;">' if show_actions else ""
    actions_head = "<th>操作</th>" if show_actions else ""
    return f"""
    <div class="table-wrap">
      <table class="ant-table ckpt-table">
        <colgroup>
          <col style="width:82px;">
          <col style="width:260px;">
          <col>
          {status_col}
          <col style="width:120px;">
          <col style="width:180px;">
          {actions_col}
        </colgroup>
        <thead><tr>
          <th>ID</th>
          <th>checkpoint</th>
          <th>描述</th>
          {status_head}
          <th>创建人</th>
          <th>创建时间 &#x21F5;</th>
          {actions_head}
        </tr></thead>
        <tbody>{_ckpt_rows_html(items, show_actions, show_status, status_logs)}</tbody>
      </table>
    </div>
    {_ckpt_detail_drawers(items)}
    """


def _ckpt_pager_html():
    return """
    <div class="mini-pager">
      <select><option>10条/页</option><option>20条/页</option><option>50条/页</option></select>
      <span class="pg-btn">&lsaquo;</span>
      <span class="pg-btn active">1</span>
      <span class="pg-btn">2</span>
      <span class="pg-btn">3</span>
      <span class="pg-btn">4</span>
      <span class="muted">...</span>
      <span class="pg-btn">13</span>
      <span class="pg-btn">&rsaquo;</span>
      <input class="pg-goto" placeholder=""><span class="pg-go">go</span>
    </div>
    """


def _new_checkpoint_drawer_html():
    return """
    <div class="drawer drawer-wide" id="drawerNewCheckpoint">
      <div class="drawer-head"><h3>新建 Checkpoint</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
      <div class="drawer-body">
        <div class="fg-row">
          <div class="fg"><label class="fg-req">Checkpoint 名称</label><input value="manual_ckpt_20260702_40000" placeholder="如 robotwin_stack_blocks_40000"></div>
          <div class="fg"><label>Checkpoint ID</label><input placeholder="自动生成"></div>
        </div>
        <div class="fg"><label class="fg-req">描述</label><textarea rows="3" placeholder="说明训练阶段、适用场景、效果备注...">手动登记的稳定候选版本, 用于部署前评测和缓存追踪。</textarea></div>
        <div class="fg-row">
          <div class="fg"><label class="fg-req">来源训练任务</label>
            <select>
              <option>robotwin_pi05_datamil_stack_blocks_two_top10pct_cotrain</option>
              <option>20260615_HouseHold_newper_stop_32</option>
              <option>20260602_ManualDagger2_NarrowTable_Moz1WB</option>
            </select>
          </div>
          <div class="fg"><label class="fg-req">训练 Step</label><input value="40000" placeholder="如 40000"></div>
        </div>
        <div class="fg"><label class="fg-req">Artifact URI</label><input value="tos://quanta-model/checkpoints/manual_ckpt_20260702_40000.pt" placeholder="tos://bucket/path/to/ckpt.pt"></div>
        <div class="fg-row">
          <div class="fg"><label>状态</label>
            <select>
              <option>未合并</option>
              <option>合并中</option>
              <option>合并失败</option>
              <option>未缓存</option>
              <option>缓存中</option>
              <option>已缓存</option>
              <option>缓存失败</option>
            </select>
          </div>
          <div class="fg"><label>缓存策略</label>
            <select>
              <option>长期保留</option>
              <option>30 天保留</option>
              <option>仅登记不缓存</option>
            </select>
          </div>
        </div>
        <div class="fg-row">
          <div class="fg"><label>创建人</label><input value="tao.wang" placeholder="请输入创建人"></div>
          <div class="fg"><label>标签</label><input value="candidate, deploy-ready" placeholder="逗号分隔"></div>
        </div>
        <div class="muted" style="font-size:12px;margin-top:6px;">提交后会登记 Checkpoint 资产, 并记录来源训练任务与 artifact 路径的血缘。</div>
      </div>
      <div class="drawer-foot">
        <button class="btn" onclick="closeDrawer()">取消</button>
        <button class="btn btn-primary" onclick="toast('Demo: Checkpoint 已创建');closeDrawer()">创建</button>
      </div>
    </div>
    """


@app.route("/model/checkpoints")
def checkpoints():
    # 获取 URL 参数
    filter_name = request.args.get("name", "")
    filter_owner = request.args.get("owner", "")

    visible_checkpoints = [c for c in CHECKPOINTS if c["status"] == "cached"]
    cached_count = sum(1 for c in CHECKPOINTS if c["status"] == "cached")
    all_count = len(CHECKPOINTS)

    content = page_header(
        "Checkpoint",
        "仅展示已缓存 checkpoint · 续训 / 评测 / 部署",
        "自动保留策略 · 远程同步 · 自动分支评测",
    ) + f"""
    <div class="fb-labeled">
      <div class="ff"><label>checkpoint</label><input id="filterCheckpointName" value="{filter_name}" placeholder="请输入 checkpoint"></div>
      <div class="ff"><label>创建人</label><input id="filterCheckpointOwner" value="{filter_owner}" placeholder="请输入创建人"></div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>

    <div class="ckpt-listbar">
      <div class="ckpt-listnote">已缓存 {cached_count} 个，缓存记录共 {all_count} 条</div>
      <div class="ckpt-actions">
        <a href="/model/checkpoints/cache-records" class="btn btn-secondary">查看缓存记录</a>
      </div>
    </div>

    {_ckpt_table_html(visible_checkpoints, show_status=False)}

    {_ckpt_pager_html()}

    """
    return render_page("Checkpoint", content, active="/model/checkpoints", module="model",
                       breadcrumb='模型平台 / 部署 / <b>Checkpoint</b>', mvp_note="MVP 一期")


@app.route("/model/checkpoints/cache-records")
def checkpoint_cache_records():
    cache_items = [
        {"id": "8032", "name": "20260701_opd_taskC_raw_shards",
         "description": "训练产物已登记, 尚未触发 checkpoint 合并。",
         "status": "unmerged", "owner": "joanna.qiao", "created": "2026-07-01 10:30:00"},
        {"id": "8028", "name": "20260630_HouseHold_stop_48_merging",
         "description": "checkpoint 分片合并中, 完成后进入缓存流程。",
         "status": "merging", "owner": "Min Chen", "created": "2026-06-30 22:18:44"},
        {"id": "7916", "name": "robotwin_pi05_datamil_stack_blocks_two_top10pct_cotrain_50000",
         "description": "训练任务详情手动发起缓存, 用于后续评测与部署前确认。",
         "status": "caching", "owner": "tao.wang", "created": "2026-07-02 14:20:00"},
        {"id": "7757", "name": "20260604_opd_exp1_sft_taskA_gpu8_50000_cache",
         "description": "缓存任务拉取源文件失败, 待确认 TOS 路径与权限后重试。",
         "status": "cache_failed", "owner": "Hannah Wang", "created": "2026-06-15 16:12:09"},
    ] + CHECKPOINTS
    content = f"""
    <div class="cache-page-head">
      <a class="btn" href="/model/checkpoints">&#8249; 返回</a>
      <div class="cache-page-title">checkpoint 缓存记录</div>
    </div>

    <div class="fb-labeled">
      <div class="ff"><label>checkpoint</label><input placeholder="请输入 checkpoint"></div>
      <div class="ff"><label>创建人</label><input placeholder="请输入创建人"></div>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>

    {_ckpt_table_html(cache_items, show_actions=False, status_filter=True, status_logs=True)}
    {_ckpt_pager_html()}
    <div class="modal-mask" id="ckptStatusLogModalMask" onclick="closeCkptStatusLog()">
      <div class="modal" onclick="event.stopPropagation()">
        <div class="modal-head">
          <h3 id="ckptStatusLogTitle">日志</h3>
          <span class="dismiss" onclick="closeCkptStatusLog()">&times;</span>
        </div>
        <div class="modal-body">
          <pre class="ckpt-log-pre" id="ckptStatusLogBody"></pre>
        </div>
      </div>
    </div>
    <script>
    // 自动筛选逻辑（如果有 URL 参数）
    document.addEventListener('DOMContentLoaded', function() {{
      var filterName = document.getElementById('filterCheckpointName').value;
      var filterOwner = document.getElementById('filterCheckpointOwner').value;

      if (filterName || filterOwner) {{
        // 筛选表格行
        var rows = document.querySelectorAll('.data-table tbody tr');
        rows.forEach(function(row) {{
          var cells = row.querySelectorAll('td');
          if (cells.length === 0) return;

          var nameCell = cells[1]; // checkpoint 名称列
          var ownerCell = cells[2]; // 创建人列

          var nameMatch = !filterName || (nameCell && nameCell.textContent.toLowerCase().includes(filterName.toLowerCase()));
          var ownerMatch = !filterOwner || (ownerCell && ownerCell.textContent.toLowerCase().includes(filterOwner.toLowerCase()));

          if (nameMatch && ownerMatch) {{
            row.style.display = '';
            // 高亮匹配的行
            if (filterName && nameCell && nameCell.textContent.toLowerCase().includes(filterName.toLowerCase())) {{
              row.style.background = '#fffbe6';
            }}
          }} else {{
            row.style.display = 'none';
          }}
        }});

        // 滚动到第一个匹配的行
        var firstVisible = document.querySelector('.data-table tbody tr[style=""]');
        if (firstVisible) {{
          firstVisible.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
      }}
    }});
    </script>
    """
    return render_page("checkpoint 缓存记录", content, active="/model/checkpoints", module="model",
                       breadcrumb='模型平台 / 部署 / Checkpoint / <b>checkpoint 缓存记录</b>', mvp_note="MVP 一期")


@app.route("/model/checkpoints/<ckpt_id>")
def checkpoint_detail(ckpt_id):
    ckpt = _ckpt_by_id(ckpt_id)
    if ckpt is None:
        return redirect("/model/checkpoints")
    exp = _ckpt_exp(ckpt)
    ds = _exp_dataset(exp)
    status_html = CKPT_STATUS_LABEL.get(ckpt["status"], ckpt["status"])
    content = page_header(
        ckpt["name"],
        f'Checkpoint #{ckpt["id"]} · {ckpt["created"]}',
        "训练产物 · 缓存状态 · 注册模型仓库 · 血缘",
    ) + f"""
    <div class="lin-actions">
      <a class="btn" href="/model/checkpoints">返回 Checkpoint</a>
      <a class="btn" href="/model/lineage/checkpoint/{ckpt['id']}">查看血缘</a>
    </div>
    {stat_grid([
        ("状态", status_html, ""),
        ("创建人", ckpt["owner"], ""),
        ("来源训练任务", exp["id"] if exp else "—", exp["name"][:38] if exp else ""),
        ("来源数据集", ds["name"], ds["version"]),
    ])}
    <div class="card">
      <h3 style="margin-top:0;">基础信息</h3>
      <div class="kv-grid">
        <div class="kv"><span>Checkpoint ID</span><b class="mono">{ckpt["id"]}</b></div>
        <div class="kv"><span>名称</span><b>{ckpt["name"]}</b></div>
        <div class="kv"><span>训练任务</span><b><a href="/model/experiments/{exp['id'] if exp else ''}">{exp['name'] if exp else '—'}</a></b></div>
        <div class="kv"><span>数据集</span><b><a href="/model/data/datasets/{ds['id']}">{ds['name']} · {ds['version']}</a></b></div>
      </div>
    </div>
    <div class="det-tabs" style="margin-top:14px;">
      <a class="det-tab active" href="/model/checkpoints/{ckpt['id']}" style="text-decoration:none;">详情</a>
      <a class="det-tab" href="/model/lineage/checkpoint/{ckpt['id']}" style="text-decoration:none;">血缘</a>
    </div>
    """
    return render_page(ckpt["name"], content, active="/model/checkpoints", module="model",
                       breadcrumb=f'模型平台 / Checkpoint / <b>{ckpt["id"]}</b>', mvp_note="MVP 一期")


# ── 部署 · 模型转换 ──
@app.route("/model/convert")
def convert():
    rows = ""
    for cv in CONVERT_JOBS:
        rows += f"""<tr>
          <td class="mono">{cv['id']}</td>
          <td><b>{cv['source']}</b> <span class="mono muted">{cv['version']}</span></td>
          <td><span class="tag tag-blue">{cv['target']}</span></td>
          <td><span class="tag tag-purple">{cv['quant']}</span></td>
          <td class="mono">{cv['size_mb']:,} MB</td>
          <td>{status_tag(cv['status'])}</td>
          <td>{cv['owner']}</td>
          <td class="muted mono">{cv['at']}</td>
          <td class="actions-cell"><a href="#" onclick="toast('Demo: 下载 artifact');return false;">下载</a> · <a href="/model/deploy" >→ 下发</a></td>
        </tr>"""
    content = page_header(
        "模型转换",
        "ONNX / TensorRT 转换 · FP16 量化",
        "INT8 校准 · 自适应 batch · 多目标格式批处理",
    ) + f"""
    <div class="filter-bar">
      <input class="grow" placeholder="搜索模型 / ID...">
      <select><option>全部格式</option><option>tensorrt</option><option>onnx</option></select>
      <select><option>全部状态</option><option>已完成</option><option>运行中</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
      <div class="right">
        <a href="#" class="btn" onclick="openDrawer('drawerConvert');return false;">+ 新建转换</a>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>ID</th><th>源模型</th><th>目标格式</th><th>量化</th><th>输出大小</th><th>状态</th><th>负责人</th><th>完成时间</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <div class="drawer" id="drawerConvert">
      <div class="drawer-head"><h3>新建模型转换</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
      <div class="drawer-body">
        <div class="fg"><label>源模型</label><select>{''.join(f'<option>{m["name"]} {m["version"]}</option>' for m in MODELS)}</select></div>
        <div class="fg"><label>目标格式</label><select><option>tensorrt</option><option>onnx</option></select></div>
        <div class="fg"><label>量化</label><select><option>fp16</option><option>无</option></select></div>
      </div>
      <div class="drawer-foot">
        <button class="btn" onclick="closeDrawer()">取消</button>
        <button class="btn btn-primary" onclick="toast('Demo: 转换任务已提交');closeDrawer()">提交</button>
      </div>
    </div>
    """
    return render_page("模型转换", content, active="/model/convert", module="model",
                       breadcrumb='模型平台 / 部署 / <b>模型转换</b>', mvp_note="MVP 一期")


# ── 部署 · 推理服务 ──
@app.route("/model/inference")
def inference_legacy_redirect():
    return redirect("/device/inference")


@app.route("/device/monitor/inference")
def inference():
    rows = ""
    for s in INFERENCE_SVCS:
        rps_html = f'<span class="mono">{s["rps"]}</span>' if s["rps"] > 0 else '<span class="muted">空闲</span>'
        p95_color = "ok" if s["p95_ms"] < 50 else ("warn" if s["p95_ms"] < 100 else "err")
        rows += f"""<tr>
          <td class="mono">{s['id']}</td>
          <td><a href="/device/devices" class="mono">{s['device']}</a></td>
          <td><b>{s['model']}</b> <span class="mono muted">{s['version']}</span></td>
          <td><span class="tag tag-blue">{s['format']}</span></td>
          <td>{status_tag(s['status'])}</td>
          <td>{rps_html}</td>
          <td class="mono"><span class="{p95_color}">{s['p95_ms']} ms</span></td>
          <td class="muted mono">{s['since']}</td>
          <td class="actions-cell"><a href="#" onclick="toast('Demo: 查看推理日志');return false;">日志</a></td>
        </tr>"""
    n_online = sum(1 for s in INFERENCE_SVCS if s["status"] == "online")
    avg_p95 = sum(s["p95_ms"] for s in INFERENCE_SVCS) / len(INFERENCE_SVCS) if INFERENCE_SVCS else 0
    total_rps = sum(s["rps"] for s in INFERENCE_SVCS)
    n_models = len(set(s["model"] for s in INFERENCE_SVCS))

    content = page_header(
        "模型推理监测",
        "已部署设备上运行的模型推理 · 状态 + 延迟",
        "A/B 流量切分 · 推理质量回流 · 自动重启",
    ) + stat_grid([
        ("在线服务", str(n_online), f"共 {len(INFERENCE_SVCS)} 个"),
        ("平均 P95", f"{avg_p95:.0f} ms", "推理延迟"),
        ("当前 RPS", str(total_rps), "全部加和"),
        ("覆盖模型", str(n_models), "个版本"),
    ]) + f"""
    <div class="filter-bar">
      <input class="grow" placeholder="搜索设备 / 模型...">
      <select><option>全部状态</option><option>在线</option><option>离线</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>ID</th><th>运行设备</th><th>模型</th><th>格式</th><th>状态</th><th>RPS</th><th>P95 延迟</th><th>启动时间</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return render_page("模型推理监测", content, active="/device/monitor/inference", module="device",
                       breadcrumb='设备管理平台 / <b>模型推理监测</b>', mvp_note="MVP 一期")


# ── 评测 · Benchmark ──
# ════════════════════════════════════════════════════════════════
# Section 7.5: 应用编排平台 (/app/*) — 占位
# ════════════════════════════════════════════════════════════════

def _app_placeholder(title, active, sub="规划中, 页面建设中"):
    content = f"""
    <div class="card" style="padding:72px 24px;text-align:center;">
      <div style="font-size:52px;color:rgba(0,0,0,0.16);margin-bottom:14px;">&#9745;</div>
      <h3 style="font-size:18px;color:rgba(0,0,0,0.78);margin:0 0 6px;">{title}</h3>
      <p style="color:rgba(0,0,0,0.45);margin:0;font-size:13.5px;">{sub}</p>
    </div>
    """
    return render_page(title, content, active=active, module="app",
                       breadcrumb=f'应用编排平台 / <b>{title}</b>', mvp_note="规划中")


@app.route("/app")
def app_home():
    desc = "应用编排平台聚焦把模型与组件组装成可调用的应用: 模型服务化、demo / skills 市场、workflow / agent 编排, 以及提示词、知识库等运行时资产。"
    content = welcome_card("应用编排平台", "模型服务 · 编排 · 资产", desc)
    return render_page("应用编排平台 · 快速入门", content, active="/app", module="app",
                       breadcrumb='<b>应用编排平台</b> / 快速入门', mvp_note="规划中")


@app.route("/app/services")
def app_services():
    return _app_placeholder("模型服务", "/app/services", "把训练好的模型一键发布为可调用服务, 配套路由 / 限流 / 监控")


@app.route("/app/market/demos")
def app_market_demos():
    return _app_placeholder("demo 市场", "/app/market/demos", "样例 demo 与最佳实践集合, 一键体验 · fork 复用")


@app.route("/app/market/skills")
def app_market_skills():
    return _app_placeholder("skills 市场", "/app/market/skills", "原子技能 (Skill) 资产库, 编排时可被 workflow / agent 引用")


@app.route("/app/orchestrate/workflow")
def app_orchestrate_workflow():
    return _app_placeholder("workflow", "/app/orchestrate/workflow", "把模型服务 + skills 组装为流程, 节点串联 / 条件分支")


@app.route("/app/orchestrate/agent")
def app_orchestrate_agent():
    return _app_placeholder("agent", "/app/orchestrate/agent", "以 agent 为中心组装 prompt / tools / 记忆, 形成可调用应用")


@app.route("/app/assets/prompts")
def app_assets_prompts():
    return _app_placeholder("提示词", "/app/assets/prompts", "提示词资产库, 可被 workflow / agent / 模型服务复用")


@app.route("/app/assets/knowledge")
def app_assets_knowledge():
    return _app_placeholder("知识库", "/app/assets/knowledge", "知识库 (RAG) 资产, 支持 agent / workflow 在线检索调用")


# ════════════════════════════════════════════════════════════════
# Section 7.6: 租户管理 (/tenant/*)  — 顶导入口
# ════════════════════════════════════════════════════════════════

TENANT_LIST = [
    {"name": "宁德时代", "av": "宁", "status": "active",  "created": "2025-12-08 10:21:33",
     "users": 38, "storage": "12.4 TB / 50 TB", "gpu": "16 / 32 卡"},
    {"name": "千寻智能", "av": "千", "status": "active",  "created": "2026-03-15 14:08:12",
     "users": 21, "storage": "5.8 TB / 30 TB",  "gpu": "8 / 16 卡"},
]

TENANT_MEMBERS = [
    {"name": "joanna.qiao",  "email": "qiaoya1112@gmail.com",  "role": "管理员",     "joined": "2025-12-08", "status": "active"},
    {"name": "Lance Li",     "email": "lance.li@catl.com",     "role": "算法工程师",  "joined": "2026-01-12", "status": "active"},
    {"name": "Min Chen",     "email": "min.chen@catl.com",     "role": "数据工程师",  "joined": "2026-02-04", "status": "active"},
    {"name": "Wei Zhang",    "email": "wei.zhang@catl.com",    "role": "标注员",     "joined": "2026-03-20", "status": "active"},
    {"name": "柳少龙",        "email": "shaolong.liu@catl.com", "role": "采集员",     "joined": "2026-04-02", "status": "active"},
    {"name": "Evelyn Zhang", "email": "evelyn@catl.com",       "role": "质检员",     "joined": "2026-05-11", "status": "active"},
    {"name": "Drake Cao",    "email": "drake@catl.com",        "role": "外部员工",    "joined": "2026-06-01", "status": "paused"},
]

TENANT_ROLES = [
    {"key": "cdn_user",   "name": "CDN访问用户",     "created": "2026-06-16 17:17:31", "enabled": True},
    {"key": "tos_user",   "name": "TOS加速访问用户",  "created": "2026-06-16 17:17:31", "enabled": True},
    {"key": "qc_inner",   "name": "内部质检员",      "created": "2026-06-16 17:17:31", "enabled": True},
    {"key": "tool_admin", "name": "采集道具管理员",   "created": "2026-06-04 16:31:42", "enabled": True},
    {"key": "admin",      "name": "管理员",         "created": "2026-06-04 16:30:22", "enabled": True},
    {"key": "ext_emp",    "name": "外部员工",        "created": "2026-06-01 20:19:19", "enabled": True},
    {"key": "out_emp",    "name": "外包员工",        "created": "2026-06-01 20:19:19", "enabled": True},
    {"key": "qa_label",   "name": "标注抽验员",      "created": "2026-06-01 20:19:19", "enabled": True},
]

TENANT_PERM_TREE = [
    ("系统设置", "open", [
        ("权限点列表",  False, "leaf"),
        ("角色列表",    False, "leaf"),
        ("组织列表",    False, "leaf"),
        ("组织权限管理", False, "leaf"),
        ("页面API列表", False, "active"),
    ]),
    ("用户管理", "open", [
        ("用户列表",      False, "leaf"),
        ("供应商用户列表", False, "leaf"),
    ]),
    ("采集任务", "open", [
        ("采集任务列表",   False, "leaf"),
        ("测试任务列表",   False, "leaf"),
        ("全部批次列表",   False, "leaf"),
        ("任务数据-采集任务", False, "leaf"),
        ("任务信息-采集任务", False, "leaf"),
    ]),
]


@app.route("/tenant")
def tenant_home():
    return redirect("/tenant/members")


@app.route("/tenant/tenants")
def tenant_tenants():
    rows = ""
    for t in TENANT_LIST:
        status_pill = '<span class="qa qa-pass">已启用</span>' if t["status"] == "active" else '<span class="qa qa-pend">已禁用</span>'
        rows += f"""<tr>
          <td><div style="display:flex;align-items:center;gap:10px;">
            <span style="width:28px;height:28px;border-radius:50%;background:#149DAA;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;flex:none;">{t['av']}</span>
            <b>{t['name']}</b>
          </div></td>
          <td>{status_pill}</td>
          <td class="muted mono">{t['created']}</td>
          <td class="mono">{t['users']}</td>
          <td class="mono">{t['storage']}</td>
          <td class="mono">{t['gpu']}</td>
          <td class="actions-cell">
            <a href="#" onclick="toast('Demo: 配置');return false;">配置</a>
            <a href="#" onclick="toast('Demo: 切换');return false;" style="margin-left:8px;">切换</a>
          </td>
        </tr>"""
    content = f"""
    <h2 class="tn-mgmt-tt">租户管理</h2>
    <div class="filter-bar">
      <input class="grow" placeholder="搜索租户名称...">
      <select><option>全部状态</option><option>已启用</option><option>已禁用</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
      <div class="right">
        <a href="#" class="btn btn-primary" onclick="toast('Demo: 新增租户');return false;">+ 新增租户</a>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>租户</th><th>状态</th><th>创建时间</th><th>成员数</th><th>存储用量</th><th>GPU 配额</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return render_page("租户管理", content, active="/tenant/tenants", module="tenant",
                       breadcrumb='<b>租户管理</b> / 租户管理', mvp_note="规划中")


@app.route("/tenant/members")
def tenant_members():
    rows = ""
    for m in TENANT_MEMBERS:
        status_pill = '<span class="qa qa-pass">在职</span>' if m["status"] == "active" else '<span class="qa qa-pend">已停用</span>'
        av = m["name"][0]
        rows += f"""<tr>
          <td><div style="display:flex;align-items:center;gap:10px;">
            <span style="width:30px;height:30px;border-radius:50%;background:#5DA9D9;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;flex:none;">{av}</span>
            <b>{m['name']}</b>
          </div></td>
          <td class="mono muted">{m['email']}</td>
          <td><span class="tag tag-teal">{m['role']}</span></td>
          <td class="muted mono">{m['joined']}</td>
          <td>{status_pill}</td>
          <td class="actions-cell">
            <a href="#" onclick="toast('Demo: 编辑角色');return false;">编辑角色</a>
            <a href="#" onclick="toast('Demo: 移除');return false;" style="margin-left:8px;color:#e25c5c;">移除</a>
          </td>
        </tr>"""
    n_active = sum(1 for m in TENANT_MEMBERS if m["status"] == "active")
    role_counts = {}
    for m in TENANT_MEMBERS:
        role_counts[m["role"]] = role_counts.get(m["role"], 0) + 1
    content = f"""
    <h2 class="tn-mgmt-tt">人员管理</h2>
    """ + stat_grid([
        ("成员总数", str(len(TENANT_MEMBERS)), ""),
        ("在职",     str(n_active), ""),
        ("已停用",   str(len(TENANT_MEMBERS) - n_active), ""),
        ("覆盖角色", str(len(role_counts)), " · ".join(f"{k} {v}" for k, v in list(role_counts.items())[:3])),
    ]) + f"""
    <div class="filter-bar">
      <input class="grow" placeholder="搜索姓名 / 邮箱...">
      <select><option>全部角色</option>{''.join(f'<option>{r}</option>' for r in role_counts)}</select>
      <select><option>全部状态</option><option>在职</option><option>已停用</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
      <div class="right">
        <a href="#" class="btn btn-primary" onclick="toast('Demo: 邀请成员');return false;">+ 邀请成员</a>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>姓名</th><th>邮箱</th><th>角色</th><th>加入时间</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return render_page("人员管理", content, active="/tenant/members", module="tenant",
                       breadcrumb='<b>租户管理</b> / 人员管理', mvp_note="规划中")


@app.route("/tenant/roles")
def tenant_roles():
    # 角色列表 (默认第一条选中)
    roles_html = ""
    for i, r in enumerate(TENANT_ROLES):
        cls = "rm-role active" if i == 0 else "rm-role"
        roles_html += f"""<div class="{cls}" onclick="rmSelectRole(this)">
          <div class="rm-rc-nm">{r['name']}</div>
          <div class="rm-rc-bot">
            <span class="rm-rc-tm">创建时间: <span class="mono">{r['created']}</span></span>
            <label class="toggle-sw" onclick="event.stopPropagation()"><input type="checkbox" {"checked" if r['enabled'] else ""}><span class="slider"></span></label>
          </div>
          <span class="rm-rc-del" title="删除">&#128465;</span>
        </div>"""

    # 权限树
    tree_html = ""
    for grp_name, state, leaves in TENANT_PERM_TREE:
        leaves_html = ""
        for leaf_name, checked, leaf_state in leaves:
            leaf_cls = "rm-pt-leaf active" if leaf_state == "active" else "rm-pt-leaf"
            ck = "checked" if checked or leaf_state == "active" else ""
            leaves_html += f'<label class="{leaf_cls}"><input type="checkbox" {ck}>{leaf_name}</label>'
        tree_html += f"""<div class="rm-pt-group {state}">
          <div class="rm-pt-grp-head" onclick="this.parentNode.classList.toggle('collapsed')">
            <span class="caret">&#9662;</span>
            <input type="checkbox" onclick="event.stopPropagation()">
            <span>{grp_name}</span>
          </div>
          <div class="rm-pt-children">{leaves_html}</div>
        </div>"""

    content = f"""
    <h2 class="tn-mgmt-tt">权限管理</h2>
    <div class="role-mgmt">

      <div class="rm-list">
        <div class="rm-list-head">
          <h3>角色列表</h3>
          <a class="btn btn-primary" href="#" onclick="toast('Demo: 新增角色');return false;">新增角色</a>
        </div>
        <div class="rm-roles">{roles_html}</div>
      </div>

      <div class="rm-detail">
        <div class="rm-list-head">
          <h3>角色详情</h3>
        </div>
        <div class="rm-d-row">
          <div class="rm-d-fg"><label><span class="req">*</span>角色名称</label><input value="CDN访问用户"></div>
          <div class="rm-d-fg"><label><span class="req">*</span>角色描述</label><input value="CDN访问用户"></div>
        </div>
        <div class="rm-d-perm-head">
          <h4>权限配置</h4>
          <div class="grow"></div>
          <a class="btn" href="#" onclick="toast('Demo: 全选');return false;">&#10003; 全选</a>
          <a class="btn" href="#" onclick="toast('Demo: 收起所有');return false;">&#8678; 收起所有</a>
        </div>
        <div class="rm-perm-tree">{tree_html}</div>
        <div class="rm-foot">
          <a class="btn btn-primary" href="#" onclick="toast('Demo: 已保存');return false;">确定</a>
        </div>
      </div>

      <div class="rm-api">
        <h4>页面API列表</h4>
        <div class="sub-ttl">权限点类型</div>
        <div class="rm-api-tabs">
          <span class="rm-api-tab active" onclick="rmApiTab(this)">BUTTON</span>
          <span class="rm-api-tab" onclick="rmApiTab(this)">筛选</span>
          <span class="rm-api-tab" onclick="rmApiTab(this)">列表字段</span>
          <span class="rm-api-tab" onclick="rmApiTab(this)">表单字段</span>
        </div>
        <div class="table-wrap">
          <table class="ant-table">
            <thead><tr><th>按钮名称</th><th>字段名称</th><th>路径</th><th>显示/隐藏</th></tr></thead>
            <tbody><tr><td colspan="4" class="empty">暂无数据</td></tr></tbody>
          </table>
        </div>
      </div>

    </div>
    <script>
    function rmSelectRole(el){{
      el.parentNode.querySelectorAll('.rm-role').forEach(function(r){{ r.classList.remove('active'); }});
      el.classList.add('active');
      var nm = el.querySelector('.rm-rc-nm').textContent;
      toast('已选中角色: ' + nm);
    }}
    function rmApiTab(el){{
      el.parentNode.querySelectorAll('.rm-api-tab').forEach(function(t){{ t.classList.remove('active'); }});
      el.classList.add('active');
    }}
    </script>
    """
    return render_page("权限管理", content, active="/tenant/roles", module="tenant",
                       breadcrumb='<b>租户管理</b> / 权限管理', mvp_note="规划中")


@app.route("/tenant/resources")
def tenant_resources():
    resource_cards = [
        ("GPU 总配额", "32 卡", "已使用 16 卡 · 空闲 16 卡"),
        ("vCPU 总配额", "384 核", "已使用 156 核"),
        ("内存总配额", "2.8 TB", "已使用 1.1 TB"),
        ("存储总配额", "50 TB", "已使用 12.4 TB"),
        ("资源组", "3 个", "2 个启用中 · 1 个已停用"),
    ]
    card_html = "".join(
        f"""<div class="res-over-card">
          <div class="k">{k}</div>
          <div class="v">{v}</div>
          <div class="s">{s}</div>
        </div>"""
        for k, v, s in resource_cards
    )

    groups = [
        ("账号全部资源", "默认资源组", "joanna.qiao", 16, 32, 12.4, 50, 4, "active", "2026-06-14 10:12"),
        ("宁德时代资源组", "训练专用", "tao.wang", 8, 12, 6.8, 20, 2, "active", "2026-06-28 16:05"),
        ("eval_shared_group", "评测共享", "Lance Li", 3, 8, 2.2, 10, 1, "paused", "2026-06-21 09:12"),
    ]

    def _quota_lines(gpu_used, gpu_total, storage_used, storage_total):
        gpu_pct = min(round(gpu_used / gpu_total * 100), 100) if gpu_total else 0
        storage_pct = min(round(storage_used / storage_total * 100), 100) if storage_total else 0
        storage_used_s = f"{storage_used:g}"
        storage_total_s = f"{storage_total:g}"
        return f"""
        <div class="res-quota">
          <div class="res-quota-line">
            <span>GPU</span><span class="track"><i class="fill" style="width:{gpu_pct}%"></i></span><span>{gpu_used}/{gpu_total}</span>
          </div>
          <div class="res-quota-line">
            <span>存储</span><span class="track"><i class="fill warn" style="width:{storage_pct}%"></i></span><span>{storage_used_s}/{storage_total_s}TB</span>
          </div>
        </div>
        """

    rows = ""
    for name, kind, admin, gpu_used, gpu_total, storage_used, storage_total, queues, status, created in groups:
        status_html = (
            '<span class="queue-status active">启用中</span>'
            if status == "active" else '<span class="queue-status paused">已停用</span>'
        )
        rows += f"""<tr>
          <td><b>{name}</b><div class="muted" style="font-size:12px;margin-top:3px;">{kind}</div></td>
          <td>{admin}</td>
          <td>{_quota_lines(gpu_used, gpu_total, storage_used, storage_total)}</td>
          <td class="mono">{queues}</td>
          <td>{status_html}</td>
          <td class="muted mono">{created}</td>
          <td class="actions-cell">
            <a href="#" onclick="openDrawer('drawerResourceGroup');return false;">编辑</a>
          </td>
        </tr>"""

    compute_rows = [
        ("A100-2x-80G", "24", "192 GB", "2 x A100", "6 / 12", "1"),
        ("A100-4x-80G", "48", "384 GB", "4 x A100", "2 / 4", "0"),
        ("H100-8x-80G", "96", "768 GB", "8 x H100", "1 / 2", "0"),
    ]
    disk_rows = [
        ("高性能云盘", "50000", "350 MB/s", "12 / 40", "200 GiB"),
        ("SSD 云盘", "30000", "250 MB/s", "20 / 80", "100 GiB"),
    ]
    compute_html = "".join(
        f"""<tr>
          <td>{name}</td><td class="mono">{vcpu}</td><td>{mem}</td><td>{gpu}</td>
          <td class="mono">{quota}</td><td><input class="queue-num" value="{count}"></td>
        </tr>"""
        for name, vcpu, mem, gpu, quota, count in compute_rows
    )
    disk_html = "".join(
        f"""<tr>
          <td>{kind}</td><td class="mono">{iops}</td><td>{throughput}</td>
          <td class="mono">{quota}</td><td><input class="queue-num" value="{cap}"></td>
        </tr>"""
        for kind, iops, throughput, quota, cap in disk_rows
    )

    content = f"""
    <div class="page-actions">
      <a href="#" class="btn btn-primary" onclick="openDrawer('drawerResourceGroup');return false;">+ 新增资源组</a>
    </div>

    <div class="res-card-grid">{card_html}</div>

    <div class="res-group-head">
      <h3>资源组列表</h3>
    </div>
    <div class="filter-bar">
      <input placeholder="资源组">
      <input placeholder="管理员">
      <input placeholder="状态">
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>资源组</th><th>管理员</th><th>资源使用</th><th>队列数</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div class="drawer drawer-queue" id="drawerResourceGroup">
      <div class="drawer-head"><h3>新增资源组</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
      <div class="drawer-body">
        <div class="queue-layout queue-layout-single">
          <div class="queue-main">
            <div class="queue-section">
              <h3 class="queue-sec-title">基本信息</h3>
              <div class="queue-form-row">
                <label class="req">名称</label>
                <input class="queue-input" value="pi05_train_resource_group" placeholder="请输入资源组名称">
              </div>
              <div class="queue-form-row">
                <label>描述</label>
                <textarea class="queue-textarea" placeholder="说明资源组用途">PI05 训练任务专用资源组，用于训练、评测和缓存任务的资源隔离。</textarea>
              </div>
              <div class="queue-form-row">
                <label>管理员</label>
                <div>
                  <div class="remote-picker">
                    <span class="picked">joanna.qiao <i>&times;</i></span>
                    <input placeholder="请搜索用户名">
                  </div>
                </div>
              </div>
              <div class="queue-form-row">
                <label>状态</label>
                <select class="queue-select"><option>启用中</option><option>已停用</option></select>
              </div>
            </div>
            <div class="queue-section">
              <h3 class="queue-sec-title">资源配置</h3>
              <div class="queue-form-row">
                <label>计算规格</label>
                <div class="queue-table">
                  <table>
                    <thead><tr><th>实例规格</th><th>vCPU</th><th>内存</th><th>GPU卡</th><th>可分配量/总量</th><th>实例数量</th></tr></thead>
                    <tbody>{compute_html}</tbody>
                  </table>
                </div>
              </div>
              <div class="queue-help">云盘用于持久化运行环境及存放训练过程中的临时数据。</div>
              <div class="queue-form-row" style="margin-top:16px;">
                <label>云盘</label>
                <div class="queue-table">
                  <table>
                    <thead><tr><th>云盘种类</th><th>单盘最大 IOPS</th><th>单盘最大吞吐量</th><th>可分配量/总量</th><th>云盘容量</th></tr></thead>
                    <tbody>{disk_html}</tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="drawer-foot">
        <button class="btn btn-tertiary" onclick="closeDrawer()">取消</button>
        <button class="btn btn-primary" onclick="toast('Demo: 资源组已创建');closeDrawer()">确认创建</button>
      </div>
    </div>
    """
    return render_page("资源管理", content, active="/tenant/resources", module="tenant",
                       breadcrumb='<b>租户管理</b> / 资源管理', mvp_note="规划中")


@app.route("/tenant/queues")
def tenant_queues():
    queue_rows = [
        ("pi05_train_a100_queue", "账号全部资源", "joanna.qiao", "2 x A100", "1", "200 GiB", "active", "2026-07-01 10:24"),
        ("dagger_h100_priority", "宁德时代资源组", "tao.wang", "8 x H100", "0", "500 GiB", "active", "2026-06-28 16:05"),
        ("eval_l40s_shared", "账号全部资源", "Lance Li", "4 x L40S", "3", "100 GiB", "paused", "2026-06-21 09:12"),
    ]
    rows = ""
    detail_drawers = ""
    for idx, (name, group, admin, gpu, instances, disk, status, created) in enumerate(queue_rows):
        status_html = (
            '<span class="queue-status active">启用中</span>'
            if status == "active" else '<span class="queue-status paused">已停用</span>'
        )
        detail_id = f"drawerQueueDetail{idx}"
        desc = "PI05 训练任务专用队列，承载 SFT、DAGGER 和部署前回归训练。" if idx == 0 else "面向训练 / 评测任务的共享资源队列。"
        member_rows = "".join(
            f"""<tr>
              <td>{member}</td>
              <td>{role}</td>
              <td><span class="queue-status active">启用中</span></td>
              <td class="actions-cell">
                <a href="#" onclick="toast('Demo: 删除成员');return false;" style="color:#d4504e;">删除</a>
              </td>
            </tr>"""
            for member, role in [
                (admin, "管理员"),
                ("tao.wang", "成员"),
                ("hannah.wang", "成员"),
            ]
        )
        detail_drawers += f"""
        <div class="drawer drawer-queue" id="{detail_id}">
          <div class="drawer-head"><h3>队列详情</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
          <div class="drawer-body">
            <div class="queue-detail">
              <div class="queue-detail-section">
                <h3>基本信息</h3>
                <div class="queue-info-grid">
                  <div class="queue-info-item"><span>名称</span><b>{name}</b></div>
                  <div class="queue-info-item"><span>资源组</span><b>{group}</b></div>
                  <div class="queue-info-item"><span>描述</span><b>{desc}</b></div>
                  <div class="queue-info-item"><span>管理员</span><b>{admin}</b></div>
                  <div class="queue-info-item"><span>状态</span><b>{status_html}</b></div>
                  <div class="queue-info-item"><span>创建时间</span><b class="mono">{created}</b></div>
                </div>
              </div>

              <div class="queue-detail-section">
                <h3>资源</h3>
                <div class="queue-info-grid">
                  <div class="queue-info-item"><span>GPU</span><b class="mono">{gpu}</b></div>
                  <div class="queue-info-item"><span>实例数</span><b class="mono">{instances}</b></div>
                  <div class="queue-info-item"><span>云盘容量</span><b class="mono">{disk}</b></div>
                  <div class="queue-info-item"><span>调度策略</span><b>按优先级排队，空闲资源自动回收</b></div>
                </div>
              </div>

              <div class="queue-detail-section">
                <h3>成员</h3>
                <div class="queue-member-add">
                  <div class="remote-picker">
                    <input placeholder="请搜索用户名">
                  </div>
                  <select class="queue-select"><option>成员</option><option>管理员</option></select>
                  <button class="btn btn-secondary" onclick="toast('Demo: 成员已添加')">添加</button>
                </div>
                <div class="queue-table">
                  <table>
                    <thead><tr><th>账号</th><th>角色</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody>{member_rows}</tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
          <div class="drawer-foot">
            <button class="btn btn-tertiary" onclick="closeDrawer()">关闭</button>
            <button class="btn btn-primary" onclick="toast('Demo: 队列详情已保存');closeDrawer()">保存</button>
          </div>
        </div>
        """
        rows += f"""<tr>
          <td><a href="#" class="queue-name-link" onclick="openDrawer('{detail_id}');return false;">{name}</a></td>
          <td>{group}</td>
          <td>{admin}</td>
          <td class="mono">{gpu}</td>
          <td class="mono">{instances}</td>
          <td class="mono">{disk}</td>
          <td>{status_html}</td>
          <td class="muted mono">{created}</td>
          <td class="actions-cell">
            <a href="#" onclick="openDrawer('drawerQueueCreate');return false;">编辑</a>
          </td>
        </tr>"""

    compute_rows = [
        ("A100-2x-80G", "24", "192 GB", "2 x A100", "6 / 12", "1"),
        ("A100-4x-80G", "48", "384 GB", "4 x A100", "2 / 4", "0"),
        ("H100-8x-80G", "96", "768 GB", "8 x H100", "1 / 2", "0"),
    ]
    disk_rows = [
        ("高性能云盘", "50000", "350 MB/s", "12 / 40", "200 GiB"),
        ("SSD 云盘", "30000", "250 MB/s", "20 / 80", "100 GiB"),
    ]
    compute_html = "".join(
        f"""<tr>
          <td>{name}</td><td class="mono">{vcpu}</td><td>{mem}</td><td>{gpu}</td>
          <td class="mono">{quota}</td><td><input class="queue-num" value="{count}"></td>
        </tr>"""
        for name, vcpu, mem, gpu, quota, count in compute_rows
    )
    disk_html = "".join(
        f"""<tr>
          <td>{kind}</td><td class="mono">{iops}</td><td>{throughput}</td>
          <td class="mono">{quota}</td><td><input class="queue-num" value="{cap}"></td>
        </tr>"""
        for kind, iops, throughput, quota, cap in disk_rows
    )
    queue_form = f"""
    <div class="queue-layout queue-layout-single">
      <div class="queue-main">
        <div class="queue-section">
          <h3 class="queue-sec-title">基本信息</h3>
          <div class="queue-form-row">
            <label class="req">名称</label>
            <input class="queue-input" value="pi05_train_a100_queue" placeholder="支持1~200位可见字符，且只包含大小写字母、中文、数字、中划线、下划线">
          </div>
          <div class="queue-form-row">
            <label>描述</label>
            <textarea class="queue-textarea" placeholder="支持1~500位字符">PI05 训练任务专用队列，优先承载 SFT、DAGGER 和部署前回归训练。</textarea>
          </div>
          <div class="queue-form-row">
            <label>管理员</label>
            <div>
              <div class="remote-picker">
                <span class="picked">joanna.qiao <i>&times;</i></span>
                <input placeholder="请搜索用户名">
              </div>
            </div>
          </div>
          <div class="queue-form-row">
            <label class="req">资源组</label>
            <select class="queue-select"><option>账号全部资源</option><option>宁德时代资源组</option><option>eval_shared_group</option></select>
          </div>
        </div>

        <div class="queue-section">
          <h3 class="queue-sec-title">资源配置</h3>
          <div class="queue-form-row">
            <label>计算规格</label>
            <div class="queue-table">
              <table>
                <thead><tr><th>实例规格</th><th>vCPU</th><th>内存</th><th>GPU卡</th><th>可分配量/总量</th><th>实例数量</th></tr></thead>
                <tbody>{compute_html}</tbody>
              </table>
            </div>
          </div>
          <div class="queue-help">云盘用于持久化开发机运行环境及存放训练过程中的临时数据，建议单队列最小容量为 20GiB。</div>
          <div class="queue-form-row" style="margin-top:16px;">
            <label>云盘</label>
            <div class="queue-table">
              <table>
                <thead><tr><th>云盘种类</th><th>单盘最大 IOPS</th><th>单盘最大吞吐量</th><th>可分配量/总量</th><th>云盘容量</th></tr></thead>
                <tbody>{disk_html}</tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

    </div>
    """

    content = f"""
    <h2 class="tn-mgmt-tt">队列管理</h2>
    <div class="filter-bar">
      <input placeholder="名称">
      <input placeholder="管理员">
      <input placeholder="资源组">
      <input placeholder="状态">
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>
    <div class="list-summarybar">
      <div class="txt">全部队列 <b>{len(queue_rows)}</b> 条</div>
      <a href="#" class="btn btn-primary" onclick="openDrawer('drawerQueueCreate');return false;">+ 新建队列</a>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>队列名称</th><th>资源组</th><th>管理员</th><th>GPU</th><th>实例数</th><th>云盘容量</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <div class="drawer drawer-queue" id="drawerQueueCreate">
      <div class="drawer-head"><h3>新建队列</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
      <div class="drawer-body">{queue_form}</div>
      <div class="drawer-foot">
        <button class="btn" onclick="closeDrawer()">取消</button>
        <button class="btn btn-primary" onclick="toast('Demo: 队列已创建');closeDrawer()">确认创建</button>
      </div>
    </div>
    {detail_drawers}
    """
    return render_page("队列管理", content, active="/tenant/queues", module="tenant",
                       breadcrumb='<b>租户管理</b> / 队列管理', mvp_note="规划中")


# ════════════════════════════════════════════════════════════════
# Section 8: 设备平台 (/device/*)
# ════════════════════════════════════════════════════════════════

@app.route("/device")
def device_home():
    # 概览页已下线, 默认落到「设备管理」菜单
    return redirect("/device/devices")


@app.route("/device/devices")
def devices_list():
    rows = ""
    detail_drawers = ""

    def device_meta(d):
        purpose_map = {"moz1-001": "真机评测", "moz1-002": "部署验证", "moz1-003": "训练回归", "moz2-001": "采集", "moz2-002": "备用"}
        admin_map = {"moz1-001": "Lance Li", "moz1-002": "joanna.qiao", "moz1-003": "tao.wang", "moz2-001": "Min Chen", "moz2-002": "joanna.qiao"}
        image_map = {
            "moz1-001": "spirit-ai-cn-beijing.cr.volces.com/spirit-ai/mozbrain:thor-v0.9.8",
            "moz1-002": "spirit-ai-cn-beijing.cr.volces.com/spirit-ai/mozbrain:thor-v1.0.0",
            "moz1-003": "spirit-ai-cn-beijing.cr.volces.com/spirit-ai/mozbrain_base:thor-v1.0.0",
            "moz2-001": "spirit-ai-cn-beijing.cr.volces.com/spirit-ai/mozbrain_release:latest",
            "moz2-002": "—",
        }
        deploy = next((dp for dp in DEPLOYS if d["id"] in dp["targets"]), None)
        model = f"{deploy['model']}_{deploy['version']}" if deploy else d["model"]
        return purpose_map.get(d["id"], "训练回归"), admin_map.get(d["id"], d["current_user"]), model, image_map.get(d["id"], "—")

    def deploy_record_status_tag(status):
        return {
            "deployed": '<span class="tag tag-green">成功</span>',
            "in_progress": '<span class="tag tag-blue">部署中</span>',
            "failed": '<span class="tag tag-red">失败</span>',
            "pending": '<span class="tag tag-gray">未开始</span>',
            "not_deployed": '<span class="tag tag-gray">未开始</span>',
        }.get(status, f'<span class="tag tag-gray">{status}</span>')

    for idx, d in enumerate(DEVICES):
        purpose, admin, deployed_model, deployed_image = device_meta(d)
        software_version = deployed_image.rsplit(":", 1)[-1] if deployed_image != "—" else "—"
        detail_id = f"drawerDeviceDetail{idx}"
        related_deploys = [dp for dp in DEPLOYS if d["id"] in dp["targets"]]
        model_version_map = {
            "moz1-001": ["spirit-v1.6-whiteboard-baseline_v1.6.0", "spirit-grasp-policy_v0.9.8"],
            "moz1-002": ["spirit-v1.7-whiteboard-base_v1.7.0", "spirit-desk-policy_v1.2.1"],
            "moz1-003": ["spirit-v1.7-whiteboard-base_v1.7.1", "spirit-v1.6-whiteboard-baseline_v1.6.0"],
            "moz2-001": ["spirit-dualarm-base_v2.0.0", "spirit-mobile-nav_v1.4.2"],
            "moz2-002": ["—"],
        }
        current_model_versions = model_version_map.get(d["id"]) or list(dict.fromkeys(
            f"{dp['model']}_{dp['version']}" for dp in related_deploys if dp["status"] in ("deployed", "in_progress")
        )) or [deployed_model]
        software_version_map = {
            "moz1-001": [("thor-v0.9.8", "deployed"), ("runtime-v1.5.4", "deployed")],
            "moz1-002": [("thor-v1.0.0", "deployed"), ("runtime-v1.7.2", "deployed")],
            "moz1-003": [("thor-v1.0.0", "in_progress"), ("runtime-v1.5.8", "deployed")],
            "moz2-001": [("latest", "deployed"), ("mobi-runtime-v2.0.3", "deployed")],
            "moz2-002": [("—", "not_deployed")],
        }
        software_versions = software_version_map.get(d["id"], [(software_version, "deployed" if software_version != "—" else "not_deployed")])
        current_model_html = "".join(f"<b>{html.escape(value)}</b>" for value in current_model_versions)
        current_software_html = "".join(f"<b class=\"mono\">{html.escape(value)}</b>" for value, state in software_versions if state != "not_deployed") or '<b class="mono">—</b>'
        model_pop_items = "".join(
            f'<a href="#" onclick="return false;"><span class="dev-id">{html.escape(value)}</span></a>'
            for value in current_model_versions if value != "—"
        ) or '<a href="#" onclick="return false;"><span class="dev-id">暂无</span></a>'
        software_pop_items = "".join(
            f'<a href="#" onclick="return false;"><span class="dev-id">{html.escape(value)}</span></a>'
            for value, state in software_versions if state != "not_deployed"
        ) or '<a href="#" onclick="return false;"><span class="dev-id">暂无</span></a>'
        model_count = sum(1 for value in current_model_versions if value != "—")
        software_count = sum(1 for value, state in software_versions if state != "not_deployed")
        model_count_cell = (
            f'<div class="devs-cell">'
            f'<span class="devs-pill" onclick="toggleDevsPop(this, event)">{model_count}<span class="ca">&#9662;</span></span>'
            f'<div class="devs-pop">{model_pop_items}</div>'
            f'</div>'
        )
        software_count_cell = (
            f'<div class="devs-cell">'
            f'<span class="devs-pill" onclick="toggleDevsPop(this, event)">{software_count}<span class="ca">&#9662;</span></span>'
            f'<div class="devs-pop">{software_pop_items}</div>'
            f'</div>'
        )

        def _model_record_rows(items, empty_text):
            body = "".join(
                f"""<tr>
                  <td class="mono">{dp['id']}</td>
                  <td>{dp['model']}_{dp['version']}</td>
                  <td>{deploy_record_status_tag(dp['status'])}</td>
                  <td>{dp['operator']}</td>
                  <td class="muted mono">{dp['at']}</td>
                </tr>"""
                for dp in items
            )
            return body or f'<tr><td colspan="5" class="empty">{empty_text}</td></tr>'

        model_records_all = _model_record_rows(related_deploys, "暂无模型部署记录")
        software_records = "".join(
            f"""<tr>
              <td class="mono">soft_{idx + 1:03d}-{soft_idx}</td>
              <td>{html.escape(version)}</td>
              <td>{deploy_record_status_tag(state)}</td>
              <td>{admin}</td>
              <td class="muted mono">{'2026-07-02 10:30' if state != 'not_deployed' else '—'}</td>
            </tr>"""
            for soft_idx, (version, state) in enumerate(software_versions, 1)
        )
        detail_drawers += f"""
        <div class="drawer drawer-queue" id="{detail_id}">
          <div class="drawer-head"><h3>设备详情</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
          <div class="drawer-body">
            <div id="deviceDetailTabs{idx}">
              <div class="tm-subtabs" style="margin:0 0 16px;">
                <button class="tm-subtab active" onclick="switchDeviceDetailTab(this,'deviceDetailTabs{idx}','basic')">基本信息</button>
                <button class="tm-subtab" onclick="switchDeviceDetailTab(this,'deviceDetailTabs{idx}','records')">部署记录</button>
              </div>
              <div class="device-detail-pane active" data-detail-pane="basic">
                <div class="queue-detail-section">
                  <h3>设备信息</h3>
                  <div class="queue-info-grid">
                    <div class="queue-info-item"><span>序列号</span><b class="mono">{d['id']}</b></div>
                    <div class="queue-info-item"><span>设备名称</span><b>{d['name']}</b></div>
                    <div class="queue-info-item"><span>用途</span><b>{purpose}</b></div>
                    <div class="queue-info-item"><span>管理员</span><b>{admin}</b></div>
                  </div>
                </div>
                <div class="queue-detail-section">
                  <h3>部署信息</h3>
                  <div class="queue-info-grid">
                    <div class="queue-info-item"><span>模型版本</span><div class="device-version-list">{current_model_html}</div></div>
                    <div class="queue-info-item"><span>软件版本</span><div class="device-version-list">{current_software_html}</div></div>
                  </div>
                </div>
              </div>
              <div class="device-detail-pane" data-detail-pane="records">
                <div class="queue-detail-section">
                  <div id="deviceRecordTabs{idx}">
                    <div class="tm-subtabs" style="margin:0 0 12px;">
                      <button class="tm-subtab active" onclick="switchDeviceRecordTab(this,'deviceRecordTabs{idx}','model')">模型部署记录</button>
                      <button class="tm-subtab" onclick="switchDeviceRecordTab(this,'deviceRecordTabs{idx}','software')">软件部署记录</button>
                    </div>
                    <div class="dev-record-pane active" data-record-type="model">
                      <div class="table-wrap">
                        <table class="ant-table">
                          <thead><tr><th>部署任务</th><th>模型版本</th><th>状态</th><th>操作人</th><th>时间</th></tr></thead>
                          <tbody>{model_records_all}</tbody>
                        </table>
                      </div>
                    </div>
                    <div class="dev-record-pane" data-record-type="software">
                      <div class="table-wrap">
                        <table class="ant-table">
                          <thead><tr><th>记录 ID</th><th>软件版本</th><th>状态</th><th>操作人</th><th>时间</th></tr></thead>
                          <tbody>{software_records}</tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="drawer-foot">
            <button class="btn btn-tertiary" onclick="closeDrawer()">关闭</button>
          </div>
        </div>
        """
        rows += f"""<tr>
          <td><a href="#" class="queue-name-link mono" onclick="openDrawer('{detail_id}');return false;">{d['id']}</a></td>
          <td>{d['name']}</td>
          <td>{purpose}</td>
          <td>{admin}</td>
          <td>{model_count_cell}</td>
          <td>{software_count_cell}</td>
        </tr>"""
    n_online = sum(1 for d in DEVICES if d["status"] in ("online", "in_use"))
    n_offline = sum(1 for d in DEVICES if d["status"] == "offline")

    content = page_header(
        "设备管理",
        "设备清单 · 软硬件依赖 · 在线状态",
        "Fleet 分组 · 远程诊断 · 急停 · 故障告警",
    ) + stat_grid([
        ("总设备数", str(len(DEVICES)), ""),
        ("在线", str(n_online), ""),
        ("离线", str(n_offline), '<span class="err">需运维介入</span>' if n_offline else ""),
        ("设备类型", "2 种", "moz1 · moz2"),
    ]) + f"""
    <div class="filter-bar">
      <input class="grow" placeholder="搜索设备 ID / 名称...">
      <select><option>全部状态</option><option>在线</option><option>离线</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>序列号</th><th>设备名称</th><th>用途</th><th>管理员</th><th>部署模型</th><th>部署镜像</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    {detail_drawers}
    """
    return render_page("设备管理", content, active="/device/devices", module="device",
                       breadcrumb='设备管理平台 / <b>设备管理</b>', mvp_note="MVP 一期")


@app.route("/device/booking")
def booking():
    pre_device = request.args.get("device", "")

    # ── 占用看板 (tab 1) ──
    board_date = "2026-06-18"
    HOUR_START, HOUR_END, HOUR_W = 9, 22, 70
    TIMELINE_W = (HOUR_END - HOUR_START) * HOUR_W

    def _hm(s):
        p = s.split(" ")[1].split(":")
        return int(p[0]) + int(p[1]) / 60.0

    hour_ticks = "".join(f'<span class="ob-tick">{h:02d}:00</span>' for h in range(HOUR_START, HOUR_END))

    board_rows = ""
    for d in DEVICES:
        bks = [b for b in BOOKINGS if b["device"] == d["id"] and b["start"].startswith(board_date)]
        blocks = ""
        for b in bks:
            sh, eh = _hm(b["start"]), _hm(b["end"])
            left = int((sh - HOUR_START) * HOUR_W)
            width = int((eh - sh) * HOUR_W)
            cls = "ob-block" + (" pending" if b["status"] == "pending" else "")
            title_attr = f"{b['purpose']} · {b['user']} · {b['start'][11:]} – {b['end'][11:]}"
            blocks += (f'<div class="{cls}" style="left:{left}px;width:{width}px;" '
                       f'title="{title_attr}" onclick="toast(\'Demo: {b["purpose"]} · {b["user"]}\')">'
                       f'<div class="ob-bk-ttl">{b["purpose"]}</div>'
                       f'<div class="ob-bk-user">{b["user"]}</div></div>')
        board_rows += (f'<div class="ob-row">'
                       f'<div class="ob-dev"><div class="ob-dev-name">{d["id"]}</div>'
                       f'<div class="ob-dev-meta">{d["location"]}</div></div>'
                       f'<div class="ob-track" style="width:{TIMELINE_W}px;">{blocks}</div></div>')

    dev_select_opts = "".join(
        f'<option>{name}</option>' for name in DEVICE_MODELS
    )
    board_html = f"""
    <div class="filter-bar">
      <a href="#" class="btn" onclick="toast('Demo: 跳到今天');return false;">今天</a>
      <a href="#" class="btn" onclick="toast('Demo: 上一天');return false;">&lsaquo;</a>
      <a href="#" class="btn" onclick="toast('Demo: 下一天');return false;">&rsaquo;</a>
      <span class="mono" style="font-weight:500;padding:0 8px;color:rgba(0,0,0,0.85);">{board_date} (周四)</span>
      <select><option>全部设备型号</option>{dev_select_opts}</select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
      <div class="right">
        <a href="#" class="btn btn-primary" onclick="openDrawer('drawerBooking');return false;">+ 新预约</a>
      </div>
    </div>
    <div class="occ-board">
      <div class="ob-scroll">
        <div class="ob-head" style="width:{160 + TIMELINE_W}px;">
          <div class="ob-th-dev">设备</div>
          <div class="ob-th-timeline">{hour_ticks}</div>
        </div>
        {board_rows}
      </div>
    </div>
    """

    # ── 预约列表 (tab 2) ──
    rows = ""
    for bk in BOOKINGS:
        rows += f"""<tr>
          <td class="mono">{bk['id']}</td>
          <td><b>{bk['device']}</b></td>
          <td>{bk['user']}</td>
          <td><span class="tag tag-{'coral' if bk['purpose']=='真机评测' else 'teal'}">{bk['purpose']}</span></td>
          <td class="muted mono">{bk['start']}</td>
          <td class="muted mono">{bk['end']}</td>
          <td>{status_tag(bk['status'])}</td>
          <td class="actions-cell"><a href="#" onclick="toast('Demo: 取消预约');return false;">取消</a></td>
        </tr>"""
    list_html = f"""
    <div class="filter-bar">
      <select><option>全部设备</option>{''.join(f'<option {"selected" if d["id"]==pre_device else ""}>' + d["id"] + '</option>' for d in DEVICES)}</select>
      <select><option>全部用途</option><option>真机评测</option><option>采集</option></select>
      <select><option>全部状态</option><option>已批准</option><option>待审批</option></select>
      <div class="filter-actions">
        <button class="btn btn-tertiary" onclick="resetFilters(this)">重置</button>
        <button class="btn btn-primary" onclick="queryFilters(this)">查询</button>
      </div>
      <div class="right">
        <a href="#" class="btn" onclick="openDrawer('drawerBooking');return false;">+ 新预约</a>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>ID</th><th>设备</th><th>预约人</th><th>用途</th><th>开始</th><th>结束</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """

    n_today = sum(1 for bk in BOOKINGS if bk["start"].startswith(board_date))
    n_pending = sum(1 for bk in BOOKINGS if bk["status"] == "pending")

    content = page_header(
        "设备预约",
        "占用看板 · 预约列表",
        "审批工作流 · 冲突推荐 · Fleet 利用率看板",
    ) + stat_grid([
        ("总预约数", str(len(BOOKINGS)), ""),
        ("今日预约", str(n_today), board_date),
        ("待审批", str(n_pending), ""),
        ("评测用途", str(sum(1 for bk in BOOKINGS if bk["purpose"] == "真机评测")),
         "+ 采集用途 " + str(sum(1 for bk in BOOKINGS if bk["purpose"] == "采集"))),
    ]) + f"""
    <div class="bk-tabs">
      <button class="bk-tab active" onclick="bkTab(this,'board')">占用看板</button>
      <button class="bk-tab" onclick="bkTab(this,'list')">预约列表</button>
    </div>
    <div id="bk-pane-board" class="bk-pane active">{board_html}</div>
    <div id="bk-pane-list" class="bk-pane">{list_html}</div>
    <div class="drawer" id="drawerBooking">
      <div class="drawer-head"><h3>新建预约</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
      <div class="drawer-body">
        <div class="fg"><label>设备</label><select>{''.join(f'<option {"selected" if d["id"]==pre_device else ""}>' + d["id"] + ' · ' + d["location"] + '</option>' for d in DEVICES if d["status"] != "offline")}</select></div>
        <div class="fg"><label>用途</label><select><option>真机评测</option><option>采集</option></select></div>
        <div class="fg"><label>开始时间</label><input type="datetime-local" value="2026-06-18T14:00"></div>
        <div class="fg"><label>结束时间</label><input type="datetime-local" value="2026-06-18T16:00"></div>
        <div class="fg"><label>备注</label><textarea rows="2" placeholder="模型版本 / 联系人..."></textarea></div>
      </div>
      <div class="drawer-foot">
        <button class="btn" onclick="closeDrawer()">取消</button>
        <button class="btn btn-primary" onclick="toast('Demo: 预约已提交');closeDrawer()">提交</button>
      </div>
    </div>
    """
    return render_page("设备预约", content, active="/device/booking", module="device",
                       breadcrumb='设备管理平台 / <b>设备预约</b>', mvp_note="MVP 一期")


def _device_placeholder(title, active, sub):
    content = f"""
    <div class="card" style="padding:72px 24px;text-align:center;">
      <div style="font-size:52px;color:rgba(0,0,0,0.16);margin-bottom:14px;">&#9745;</div>
      <h3 style="font-size:18px;color:rgba(0,0,0,0.78);margin:0 0 6px;">{title}</h3>
      <p style="color:rgba(0,0,0,0.45);margin:0;font-size:13.5px;">{sub}</p>
    </div>
    """
    return render_page(title, content, active=active, module="device",
                       breadcrumb=f'设备管理平台 / <b>{title}</b>', mvp_note="规划中")


@app.route("/device/monitor/run")
def device_monitor_run():
    return _device_placeholder("设备运行监测", "/device/monitor/run",
                               "设备心跳 · CPU / 内存 / GPU 利用率 · 异常告警 · Fleet 视图")


@app.route("/device/ota")
def device_ota():
    return _device_placeholder("OTA", "/device/ota",
                               "固件 / 模型版本下发 · 灰度策略 · 一键回滚 · 进度看板")


# /device/inference 老 URL: 302 转到 模型推理监测
@app.route("/device/inference")
def _device_inference_legacy_redirect():
    return redirect("/device/monitor/inference")


# ════════════════════════════════════════════════════════════════
# Section 9: 资产平台 (/asset/*)
# ════════════════════════════════════════════════════════════════

# /asset/lineage 老 URL 兼容: 302 转到 /model/lineage
@app.route("/asset/lineage")
def _asset_lineage_legacy_redirect():
    qs = request.query_string.decode() if request.query_string else ""
    return redirect(f"/model/lineage{('?' + qs) if qs else ''}")


# ── 血缘系统配置 ──
LINEAGE_CONFIG = {
    'dataset': {
        'find_fn': lambda val: next((d for d in DATASETS if d["name"] == val or d["id"] == val), None),
        'title': '血缘',
        'subtitle': '数据集的上游采集与下游训练链路',
        'list_path': '/model/data/datasets',
        'detail_url_fn': lambda obj: f'/model/data/datasets?sel={obj["id"]}',
        'breadcrumb_fn': lambda obj: f'模型平台 / 数据集 / {obj["name"]} / <b>血缘</b>',
    },
    'train': {
        'find_fn': lambda val: next((e for e in EXPERIMENTS if e["name"] == val or e["id"] == val), None),
        'title': '血缘',
        'subtitle': '训练任务 → Checkpoint 的输入输出链路',
        'list_path': '/model/experiments',
        'detail_url_fn': lambda obj: f'/model/experiments',
        'breadcrumb_fn': lambda obj: f'模型平台 / 训练任务 / {obj["name"]} / <b>血缘</b>',
    },
    'checkpoint': {
        'find_fn': lambda val: next((c for c in CHECKPOINTS if c["name"] == val or c["id"] == val), None),
        'title': '血缘',
        'subtitle': 'Checkpoint 的训练来源与数据来源',
        'list_path': '/model/checkpoints',
        'detail_url_fn': lambda obj: f'/model/checkpoints',
        'breadcrumb_fn': lambda obj: f'模型平台 / Checkpoint / {obj["id"]} / <b>血缘</b>',
    },
    'eval': {
        'find_fn': lambda val: next((e for e in EVALS if e.get("name") == val or e["id"] == val), None),
        'title': '血缘',
        'subtitle': '评测任务的 Checkpoint 来源与数据链路',
        'list_path': '/model/eval/tasks',
        'detail_url_fn': lambda obj: f'/model/eval/tasks/{obj["id"]}',
        'breadcrumb_fn': lambda obj: f'模型平台 / 评测任务 / {obj.get("name", obj["id"])} / <b>血缘</b>',
    },
    'task': {
        'find_fn': lambda task_id: _task_by_id(task_id),
        'title': '血缘',
        'subtitle': '采集任务的下游数据集与训练链路',
        'list_path': '/data/collect',
        'detail_url_fn': lambda obj: f'/data/recordings?task={obj["id"]}',
        'breadcrumb_fn': lambda obj: f'数据平台 / 采集任务 / {obj.get("name", obj["id"])} / <b>血缘</b>',
    },
}

LINEAGE_FILTERS = [
    {'key': 'dataset', 'label': '数据集', 'placeholder': '输入数据集名称', 'route': '/model/lineage/dataset/'},
    {'key': 'train', 'label': '训练任务', 'placeholder': '输入训练任务名称', 'route': '/model/lineage/train/'},
    {'key': 'checkpoint', 'label': 'Checkpoint', 'placeholder': '输入 Checkpoint 名称', 'route': '/model/lineage/checkpoint/'},
    {'key': 'eval', 'label': '评测任务', 'placeholder': '输入评测任务名称', 'route': '/model/lineage/eval/'},
    {'key': 'task', 'label': '采集任务', 'placeholder': '输入采集任务 ID / 名称', 'route': '/model/lineage/task/'},
]


def _dataset_by_id_or_name(value):
    return next((d for d in DATASETS if d["id"] == value or d["name"] == value), None)


def resolve_task_name(task_id):
    task = next((t for t in COLLECT_TASKS if t["id"] == task_id), None)
    return (task["name"][:20] + "...") if task else task_id


def _exp_by_id(value):
    return next((e for e in EXPERIMENTS if e["id"] == value), None)


def _exp_by_id_or_name(value):
    return next((e for e in EXPERIMENTS if e["id"] == value or e["name"] == value), None)


def _ckpt_by_id(value):
    return next((c for c in CHECKPOINTS if c["id"] == value or c["name"] == value), None)


def _eval_by_id(value):
    return next((e for e in EVALS if e["id"] == value or e.get("name") == value), None)


def _task_by_id(value):
    return next((t for t in COLLECT_TASKS if t["id"] == value or t["name"] == value), None)


def get_tasks_for_dataset(ds):
    """数据集 → 采集任务列表（按 source_tasks ID）"""
    if not ds:
        return []
    return [t for t in COLLECT_TASKS if t["id"] in ds.get("source_tasks", [])]


def get_experiments_for_dataset(ds_id):
    """数据集 → 训练任务列表（全量，按 dataset_id 或 dataset_ids 列表）"""
    def _matches(e):
        if e.get("dataset_id") == ds_id:
            return True
        return ds_id in (e.get("dataset_ids") or [])
    return [e for e in EXPERIMENTS if _matches(e)]


def get_checkpoints_for_experiment(exp_id):
    """训练任务 → Checkpoint 列表（全量，按 exp_id）"""
    return [c for c in CHECKPOINTS if c.get("exp_id") == exp_id]


def get_evals_for_checkpoint(ckpt_id):
    """Checkpoint → 评测任务列表（全量，按 ckpt_id）"""
    return [ev for ev in EVALS if ev.get("ckpt_id") == ckpt_id]


def _ckpt_exp(ckpt):
    if not ckpt:
        return None
    return _exp_by_id(f"exp_{ckpt['id']}") or EXPERIMENTS[0]


def _exp_dataset(exp):
    if not exp:
        return DATASETS[0]
    if exp["dataset"] != "—":
        return _dataset_by_id_or_name(exp["dataset"]) or DATASETS[0]
    model = next((m for m in MODELS if m["from_exp"] == exp["id"]), None)
    if model:
        return _dataset_by_id_or_name(model["from_dataset"]) or DATASETS[0]
    return DATASETS[0]


def _exp_datasets(exp):
    """训练任务 → 它挂载的所有数据集对象（支持多数据集）。

    仅返回该训练任务真实挂载的数据集；无挂载时返回空列表，
    不再 fallback 到 DATASETS[0]（否则会给无数据集的训练任务
    凭空接上 DEMO_DS_9001 及其无关采集任务，污染血缘图）。
    """
    if not exp:
        return []
    ds_ids = exp.get("dataset_ids") or ([exp.get("dataset_id")] if exp.get("dataset_id") else [])
    result = [_dataset_by_id_or_name(did) for did in ds_ids if did]
    return [d for d in result if d]


def _lineage_context(anchor_type, anchor_id):
    """以锚点为中心的定向闭包取数：上游只往上、下游只往下，不掉头。

    层级方向：采集任务 → 数据集 → 训练任务 → checkpoint → 评测
    """
    # 用 dict 按 id 去重且保持插入顺序
    def dedupe(items):
        seen = {}
        for it in items:
            if it and it["id"] not in seen:
                seen[it["id"]] = it
        return list(seen.values())

    # ── 上游收集器（从某层往采集任务方向回溯）──
    def up_from_datasets(ds_list):
        tasks = []
        for ds in ds_list:
            tasks.extend(get_tasks_for_dataset(ds))
        return dedupe(tasks)

    def up_from_experiments(exp_list):
        ds_list = []
        for e in exp_list:
            ds_list.extend(_exp_datasets(e))
        ds_list = dedupe(ds_list)
        return ds_list, up_from_datasets(ds_list)

    def up_from_checkpoints(ckpt_list):
        exp_list = dedupe([_exp_by_id(c.get("exp_id") or "") for c in ckpt_list])
        ds_list, task_list = up_from_experiments(exp_list)
        return exp_list, ds_list, task_list

    # ── 下游收集器（从某层往评测方向扩散）──
    def down_from_datasets(ds_list):
        exp_list = []
        for ds in ds_list:
            exp_list.extend(get_experiments_for_dataset(ds["id"]))
        exp_list = dedupe(exp_list)
        return (exp_list,) + down_from_experiments(exp_list)

    def down_from_experiments(exp_list):
        ckpt_list = []
        for e in exp_list:
            ckpt_list.extend(get_checkpoints_for_experiment(e["id"]))
        ckpt_list = dedupe(ckpt_list)
        return ckpt_list, down_from_checkpoints(ckpt_list)

    def down_from_checkpoints(ckpt_list):
        evals_list = []
        for c in ckpt_list:
            evals_list.extend(get_evals_for_checkpoint(c["id"]))
        return dedupe(evals_list)

    # ── 按锚点类型组装 5 个维度 ──
    if anchor_type == "train":
        exp = _exp_by_id(anchor_id) or EXPERIMENTS[0]
        experiments = [exp]
        datasets, tasks = up_from_experiments(experiments)
        checkpoints, evals = down_from_experiments(experiments)
    elif anchor_type == "dataset":
        ds = _dataset_by_id_or_name(anchor_id) or DATASETS[0]
        datasets = [ds]
        tasks = up_from_datasets(datasets)
        experiments, checkpoints, evals = down_from_datasets(datasets)
    elif anchor_type == "checkpoint":
        ckpt = _ckpt_by_id(anchor_id) or CHECKPOINTS[0]
        checkpoints = [ckpt]
        experiments, datasets, tasks = up_from_checkpoints(checkpoints)
        evals = down_from_checkpoints(checkpoints)
    elif anchor_type == "eval":
        ev = _eval_by_id(anchor_id) or EVALS[0]
        evals = [ev]
        ckpt = _ckpt_by_id(ev.get("ckpt_id") or "")
        checkpoints = [ckpt] if ckpt else []
        experiments, datasets, tasks = up_from_checkpoints(checkpoints)
    elif anchor_type == "task":
        task = _task_by_id(anchor_id) or COLLECT_TASKS[0]
        tasks = [task]
        datasets = dedupe([ds for ds in DATASETS if task["id"] in ds.get("source_tasks", [])])
        experiments, checkpoints, evals = down_from_datasets(datasets)
    else:
        task = COLLECT_TASKS[0]
        tasks = [task]
        datasets = dedupe([ds for ds in DATASETS if task["id"] in ds.get("source_tasks", [])])
        experiments, checkpoints, evals = down_from_datasets(datasets)

    return {
        "anchor_type": anchor_type,
        "anchor_id": anchor_id,
        "datasets": datasets,
        "tasks": tasks,
        "experiments": experiments,
        "checkpoints": checkpoints,
        "evals": evals,
    }


def _lineage_detail_html(anchor_type, anchor_id):
    ctx = _lineage_context(anchor_type, anchor_id)
    datasets = ctx["datasets"]
    tasks = ctx["tasks"]
    experiments = ctx["experiments"]
    checkpoints = ctx["checkpoints"]
    evals = ctx["evals"]

    # ── Build chain_id mapping: per-dataset and per-checkpoint chains ──
    chain_map = {}  # {node_id: set of chain_ids}

    def add_to_chain(node_id, chain_id):
        """Helper to add chain_id to a node"""
        if node_id not in chain_map:
            chain_map[node_id] = set()
        chain_map[node_id].add(chain_id)

    # Step 1: 为每个训练的每个数据集分配基础 chain_id (用于区分多数据集路径)
    for e in experiments:
        ds_ids = e.get("dataset_ids", [])
        if not ds_ids and e.get("dataset_id"):
            ds_ids = [e.get("dataset_id")]
        if not ds_ids:
            ds_ids = [datasets[0]["id"]] if datasets else []

        for ds_id in ds_ids:
            if not ds_id:
                continue

            # 数据集维度的 chain_id
            ds_chain = f"chain_{e['id']}_ds_{ds_id}"

            # 标记数据集节点
            add_to_chain(f'dataset_{ds_id}', ds_chain)

            # 标记数据集的上游采集任务
            ds_obj = next((d for d in datasets if d["id"] == ds_id), None)
            if ds_obj:
                for task_id in ds_obj.get("source_tasks", []):
                    add_to_chain(f'task_{task_id}', ds_chain)

            # 标记训练任务（会有多个 ds_chain，因为可能多个数据集）
            add_to_chain(e['id'], ds_chain)

    # Step 2: 为每个 Checkpoint 分配独立 chain_id，并继承所有数据集的 chain_id
    for e in experiments:
        ds_ids = e.get("dataset_ids", [])
        if not ds_ids and e.get("dataset_id"):
            ds_ids = [e.get("dataset_id")]
        if not ds_ids:
            ds_ids = [datasets[0]["id"]] if datasets else []

        for c in checkpoints:
            if c.get('exp_id') != e['id']:
                continue

            # Checkpoint 独立 chain_id
            ckpt_chain = f"chain_{e['id']}_ckpt_{c['id']}"

            # 标记 Checkpoint 节点（拥有自己的 chain_id + 继承所有数据集的 chain_id）
            add_to_chain(f'checkpoint_{c["id"]}', ckpt_chain)

            # 继承所有数据集的 chain_id（这样悬停数据集时 Checkpoint 会高亮）
            for ds_id in ds_ids:
                if ds_id:
                    ds_chain = f"chain_{e['id']}_ds_{ds_id}"
                    add_to_chain(f'checkpoint_{c["id"]}', ds_chain)

            # 标记该 Checkpoint 的评测（继承 Checkpoint chain_id + 所有数据集 chain_id）
            for ev in evals:
                if ev.get('ckpt_id') == c['id']:
                    add_to_chain(f'eval_{ev["id"]}', ckpt_chain)
                    # 评测也继承所有数据集的 chain_id
                    for ds_id in ds_ids:
                        if ds_id:
                            ds_chain = f"chain_{e['id']}_ds_{ds_id}"
                            add_to_chain(f'eval_{ev["id"]}', ds_chain)

            # 标记训练任务（继承 Checkpoint chain_id）
            add_to_chain(e['id'], ckpt_chain)

    # Helper to get chain_id string
    def get_chains(node_id):
        return ' '.join(sorted(chain_map.get(node_id, set())))

    def cls(kind, base):
        return base + (" anchor" if anchor_type == kind else "")

    # ── 图标 SVG 定义（Lucide Icons） ──
    ICON_GIT_BRANCH = '<svg class="icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="3" x2="6" y2="15"></line><circle cx="18" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><path d="M18 9a9 9 0 0 1-9 9"></path></svg>'
    ICON_ARROW_UP_RIGHT = '<svg class="icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>'
    ICON_CORNER_UP_LEFT = '<svg class="icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 14 4 9 9 4"></polyline><path d="M20 20v-7a4 4 0 0 0-4-4H4"></path></svg>'
    ICON_HISTORY = '<svg class="icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path><path d="M12 7v5l4 2"></path></svg>'

    # ── 采集任务卡片 ──
    def _task_card(t):
        is_dagger = t.get("source_type") == "dagger"
        task_node_id = f'task_{t["id"]}'
        # 找到该任务所属的数据集
        ds_id = next((ds["id"] for ds in datasets if t["id"] in ds.get("source_tasks", [])), None)
        if is_dagger:
            src_ckpt = t.get("src_checkpoint_id", "")
            tip = (f'失败类型: {t.get("src_failure_type","—")}｜触发时间: {t.get("src_dagger_at","—")}'
                   f'｜触发设备: {t.get("src_trigger_device","—")}｜质检通过: {t.get("qc_pass","—")}/{t.get("collected","—")}')
            return (
                f'<div class="{cls("task","lin-node dagger")}" data-chain-id="{get_chains(task_node_id)}" data-node-id="{task_node_id}" data-lineage-tip="{tip}">'
                f'<div class="ln-ttl">{t["name"]}</div>'
                f'<div class="ln-footer">'
                f'<div class="ln-meta">Task ID: {t["id"]}</div>'
                f'</div>'
                f'<div class="ln-icon-actions">'
                f'<a class="ln-icon-btn" href="/model/lineage/task/{t["id"]}" data-tooltip="查看血缘关系图">{ICON_GIT_BRANCH}</a>'
                f'<a class="ln-icon-btn" href="/data/recordings?task={t["id"]}" target="_blank" rel="noopener" data-tooltip="查看任务详情">{ICON_ARROW_UP_RIGHT}</a>'
                f'<a class="ln-icon-btn" href="/model/lineage/checkpoint/{src_ckpt}" data-tooltip="查看来源Checkpoint">{ICON_CORNER_UP_LEFT}</a>'
                f'</div>'
                f'</div>'
            )
        tip = (f'项目: {t.get("project","—")}｜阶段: {t.get("stage","—")}｜创建人: {t.get("owner","joanna.qiao")}'
               f'｜创建时间: {t.get("created","—")}｜质检通过: {t.get("qc_pass","—")}')
        return (
            f'<div class="{cls("task","lin-node teal")}" data-chain-id="{get_chains(task_node_id)}" data-node-id="{task_node_id}" data-lineage-tip="{tip}">'
            f'<div class="ln-ttl">{t["name"]}</div>'
            f'<div class="ln-footer">'
            f'<div class="ln-meta">Task ID: {t["id"]}</div>'
            f'</div>'
            f'<div class="ln-icon-actions">'
            f'<a class="ln-icon-btn" href="/model/lineage/task/{t["id"]}" data-tooltip="查看血缘关系图">{ICON_GIT_BRANCH}</a>'
            f'<a class="ln-icon-btn" href="/data/recordings?task={t["id"]}" target="_blank" rel="noopener" data-tooltip="查看任务详情">{ICON_ARROW_UP_RIGHT}</a>'
            f'</div>'
            f'</div>'
        )

    # Group tasks by dataset when multiple datasets exist
    if len(datasets) > 1:  # Multi-dataset: group by source
        task_html = ""
        rendered_task_ids = set()
        for ds in datasets:
            ds_tasks = [t for t in tasks if t["id"] in ds.get("source_tasks", []) and t["id"] not in rendered_task_ids]
            if ds_tasks:
                task_html += "".join(_task_card(t) for t in ds_tasks)
                rendered_task_ids.update(t["id"] for t in ds_tasks)
    else:  # Single dataset: no grouping
        task_html = "".join(_task_card(t) for t in tasks)

    # ── 数据集卡片（支持多个）──
    def _ds_card(ds):
        segment_count = max(1, round(ds["frames"] / 1200)) if ds.get("frames") else 1
        ds_tip = (f'版本: {ds["version"]}｜EP: {ds["episodes"]}｜Segment: {segment_count}'
                  f'｜创建人: {ds["owner"]}｜划分: {ds.get("train_ratio",0)}/{ds.get("val_ratio",0)}/{ds.get("test_ratio",0)}')
        ds_node_id = f'dataset_{ds["id"]}'
        return (
            f'<div class="{cls("dataset","lin-node blue")}" data-chain-id="{get_chains(ds_node_id)}" data-node-id="{ds_node_id}" data-lineage-tip="{ds_tip}">'
            f'<div class="ln-ttl">{ds["name"]} {ds["version"]}</div>'
            f'<div class="ln-footer">'
            f'<div class="ln-meta">{ds["episodes"]} Episode</div>'
            f'</div>'
            f'<div class="ln-icon-actions">'
            f'<a class="ln-icon-btn" href="/model/lineage/dataset/{ds["id"]}" data-tooltip="查看血缘关系图">{ICON_GIT_BRANCH}</a>'
            f'<a class="ln-icon-btn" href="/model/data/datasets?sel={ds["id"]}" target="_blank" rel="noopener" data-tooltip="查看数据集详情">{ICON_ARROW_UP_RIGHT}</a>'
            f'</div>'
            f'</div>'
        )
    ds_html = "".join(_ds_card(ds) for ds in datasets)

    # ── 训练任务卡片（全量）──
    def _exp_card(e):
        ename = e["name"]
        status_map = {"running": "运行中", "done": "成功", "failed": "失败", "运行中": "运行中", "成功": "成功", "失败": "失败"}
        status_display = status_map.get(e.get("status", ""), e.get("status", "—"))
        tip = (f'模型: {e.get("model_type","—")}｜状态: {status_display}'
               f'｜进度: {e.get("current_epoch","—")}/{e.get("epochs","—")}｜最佳{e.get("metric_name","指标")}: {e.get("best_metric","—")}')
        return (
            f'<div class="{cls("train","lin-node purple")}" data-chain-id="{get_chains(e["id"])}" data-node-id="{e["id"]}" data-lineage-tip="{tip}">'
            f'<div class="ln-ttl">{ename}</div>'
            f'<div class="ln-footer">'
            f'<div class="ln-meta">{status_display}</div>'
            f'</div>'
            f'<div class="ln-icon-actions">'
            f'<a class="ln-icon-btn" href="/model/lineage/train/{e["id"]}" data-tooltip="查看血缘关系图">{ICON_GIT_BRANCH}</a>'
            f'<a class="ln-icon-btn" href="/model/experiments/{e["id"]}" target="_blank" rel="noopener" data-tooltip="查看训练详情">{ICON_ARROW_UP_RIGHT}</a>'
            f'</div>'
            f'</div>'
        )
    exp_html = "".join(_exp_card(e) for e in experiments)

    # ── Checkpoint 卡片（全量，去掉 step）──
    def _ckpt_card(c):
        import re
        step_match = re.search(r'[_-](\d{4,6})$', c.get("name", ""))
        step = step_match.group(1) if step_match else "—"
        name_parts = c.get("name", "").split("_")
        desc = "_".join(name_parts[1:-1]) if len(name_parts) > 2 else ""

        tip = f'名称: {c.get("name","—")}｜状态: {c.get("status","—")}｜创建时间: {c.get("created","—")}｜owner: {c.get("owner","—")}'
        ckpt_node_id = f'checkpoint_{c["id"]}'
        ckpt_name = c.get("name", c["id"])

        # History button only if parent exists
        history_btn = ""
        if c.get("parent_checkpoint_id"):
            history_btn = f'<a class="ln-icon-btn" data-ckpt-id="{c["id"]}" onclick="showCkptHistory(this.dataset.ckptId); return false;" href="#" data-tooltip="查看历史版本">{ICON_HISTORY}</a>'

        return (
            f'<div class="{cls("checkpoint","lin-node amber")}" data-chain-id="{get_chains(ckpt_node_id)}" data-node-id="{ckpt_node_id}" data-lineage-tip="{tip}">'
            f'<div class="ln-ttl">{ckpt_name}</div>'
            f'<div class="ln-footer">'
            f'<div class="ln-meta">Step {step}{(" · " + desc) if desc else ""}</div>'
            f'</div>'
            f'<div class="ln-icon-actions">'
            f'<a class="ln-icon-btn" href="/model/lineage/checkpoint/{c["id"]}" data-tooltip="查看血缘关系图">{ICON_GIT_BRANCH}</a>'
            f'<a class="ln-icon-btn" href="/model/checkpoints?name={ckpt_name}" target="_blank" rel="noopener" data-tooltip="查看Checkpoint详情">{ICON_ARROW_UP_RIGHT}</a>'
            f'{history_btn}'
            f'</div>'
            f'</div>'
        )
    ckpt_html = "".join(_ckpt_card(c) for c in checkpoints)

    # ── 评测卡片（全量）──
    def _eval_card(ev):
        sr = ev["success_rate"] if ev.get("success_rate") is not None else "—"
        tip = f'benchmark: {ev.get("benchmark","—")}｜成功率: {sr}｜状态: {ev.get("status","—")}｜时间: {ev.get("at","—")}'
        eval_node_id = f'eval_{ev["id"]}'
        task_name = ev.get("name", "—")
        task_no = ev.get("task_no", ev.get("id", "—"))
        return (
            f'<div class="{cls("eval","lin-node green")}" data-chain-id="{get_chains(eval_node_id)}" data-node-id="{eval_node_id}" data-lineage-tip="{tip}">'
            f'<div class="ln-ttl">{task_name}</div>'
            f'<div class="ln-footer">'
            f'<div class="ln-meta">ID {task_no}</div>'
            f'</div>'
            f'<div class="ln-icon-actions">'
            f'<a class="ln-icon-btn" href="/model/lineage/eval/{ev["id"]}" data-tooltip="查看血缘关系图">{ICON_GIT_BRANCH}</a>'
            f'<a class="ln-icon-btn" href="/model/eval/tasks/{ev["id"]}" target="_blank" rel="noopener" data-tooltip="查看评测详情">{ICON_ARROW_UP_RIGHT}</a>'
            f'</div>'
            f'</div>'
        )
    eval_html = "".join(_eval_card(ev) for ev in evals) if evals else '<div class="lin-node muted"><div class="ln-meta">暂无评测</div></div>'

    # ── 构建连线边关系 (child_node_id, parent_node_id)，parent=左列、child=右列 ──
    edges = []
    # 采集任务(左) → 数据集(右): parent=task, child=dataset
    for ds in datasets:
        for t in tasks:
            if t["id"] in ds.get("source_tasks", []):
                edges.append((f'dataset_{ds["id"]}', f'task_{t["id"]}'))  # (child=dataset, parent=task)
    # 数据集(左) → 训练任务(右): parent=dataset, child=exp
    for ds in datasets:
        for e in experiments:
            e_ds_ids = e.get("dataset_ids") or ([e.get("dataset_id")] if e.get("dataset_id") else [])
            if ds["id"] in e_ds_ids:
                edges.append((e["id"], f'dataset_{ds["id"]}'))  # (child=exp, parent=dataset)
    # 训练任务(左) → Checkpoint(右): parent=exp, child=ckpt
    for c in checkpoints:
        pid = c.get("exp_id")
        if pid:
            edges.append((f'checkpoint_{c["id"]}', pid))  # (child=ckpt, parent=exp)
    # Checkpoint(左) → 评测(右): parent=ckpt, child=eval
    for ev in evals:
        pid = ev.get("ckpt_id")
        if pid:
            edges.append((f'eval_{ev["id"]}', f'checkpoint_{pid}'))  # (child=eval, parent=ckpt)
    edges_json = json.dumps(edges)

    # 候选数据：各维度的 name→id 映射，用于模糊搜索
    suggestions_data = {
        "task":       [{"label": t["name"], "id": t["id"]} for t in COLLECT_TASKS],
        "dataset":    [{"label": f'{d["name"]} {d["version"]}', "id": d["id"]} for d in DATASETS],
        "train":      [{"label": e["name"], "id": e["id"]} for e in EXPERIMENTS],
        "checkpoint": [{"label": c["name"], "id": c["id"]} for c in CHECKPOINTS],
        "eval":       [{"label": ev["name"], "id": ev["id"]} for ev in EVALS],
    }
    suggestions_json = json.dumps(suggestions_data, ensure_ascii=False)

    # ── 构建筛选器（下拉框 + 输入框版本）──
    # 根据当前维度确定输入框的值（始终显示可识别的名称）
    input_value = ""
    if anchor_type == "dataset":
        input_value = datasets[0]["name"] if datasets else ""
    elif anchor_type == "train":
        input_value = experiments[0]["name"] if experiments else ""
    elif anchor_type == "checkpoint":
        input_value = next((c["name"] for c in checkpoints), anchor_id)
    elif anchor_type == "eval":
        ev = _eval_by_id(anchor_id)
        input_value = ev["name"] if ev else anchor_id
    elif anchor_type == "task":
        t = _task_by_id(anchor_id)
        input_value = t["name"] if t else anchor_id

    filter_html = f"""
    <div class="lin-filter">
      <div class="lf-input-group">
        <select id="linDimension" class="lf-dimension-select">
          <option value="task" {'selected' if anchor_type == 'task' else ''}>采集任务</option>
          <option value="dataset" {'selected' if anchor_type == 'dataset' else ''}>数据集</option>
          <option value="train" {'selected' if anchor_type == 'train' else ''}>训练任务</option>
          <option value="checkpoint" {'selected' if anchor_type == 'checkpoint' else ''}>Checkpoint</option>
          <option value="eval" {'selected' if anchor_type == 'eval' else ''}>评测任务</option>
        </select>
        <input id="linInput" value="{input_value}" placeholder="输入名称进行搜索" list="linInputSuggestions">
        <datalist id="linInputSuggestions"></datalist>
        <button class="btn btn-primary" onclick="linApplyFilter()">确认</button>
      </div>
    </div>"""

    legend_html = """
    <div class="lineage-hint">
      <span class="hint-section">
        <span class="hint-label">节点状态：</span>
        <span class="hint-item"><span class="hint-dot blue"></span>当前查看</span>
        <span class="hint-item"><span class="hint-dot gray"></span>关联节点</span>
      </span>
      <span class="hint-section">
        <span class="hint-label">特殊类型：</span>
        <span class="hint-item"><span class="hint-bar dagger"></span>Dagger 回流</span>
      </span>
    </div>
    """

    modal_html = """
    <!-- Checkpoint History Modal -->
    <div id="ckptHistoryModal" class="ckpt-history-modal" style="display:none;">
      <div class="ckpt-history-overlay" onclick="closeCkptHistoryModal()"></div>
      <div class="ckpt-history-content">
        <div class="ckpt-history-header">
          <h3>Checkpoint 演进历史</h3>
          <button class="ckpt-history-close" onclick="closeCkptHistoryModal()">✕</button>
        </div>
        <div class="ckpt-history-body" id="ckptHistoryBody">
          <!-- Timeline will be inserted here by JS -->
        </div>
      </div>
    </div>
    """

    return filter_html + legend_html + f"""
    <div class="lin-flow lin-flow-5" id="linFlow" style="position:relative;">
      <svg id="linSvg" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;"></svg>
      <div class="lin-col"><h4 class="lin-col-title">采集任务 ({len(tasks)})</h4><div class="lin-col-body">{task_html}</div></div>
      <div class="lin-col"><h4 class="lin-col-title">训练数据集 ({len(datasets)})</h4><div class="lin-col-body">{ds_html}</div></div>
      <div class="lin-col"><h4 class="lin-col-title">训练任务 ({len(experiments)})</h4><div class="lin-col-body">{exp_html}</div></div>
      <div class="lin-col"><h4 class="lin-col-title">Checkpoint ({len(checkpoints)})</h4><div class="lin-col-body">{ckpt_html}</div></div>
      <div class="lin-col"><h4 class="lin-col-title">TEST任务 ({len(evals)})</h4><div class="lin-col-body">{eval_html}</div></div>
    </div>
    """ + modal_html + f"""
    <script>
    window.__linEdges = {edges_json};
    var __linSuggestions = {suggestions_json};

    // 根据当前维度填充 datalist 候选项
    function linFillSuggestions(dimension) {{
      var dl = document.getElementById('linInputSuggestions');
      dl.innerHTML = '';
      var items = __linSuggestions[dimension] || [];
      items.forEach(function(item) {{
        var opt = document.createElement('option');
        opt.value = item.label;
        opt.dataset.id = item.id;
        dl.appendChild(opt);
      }});
    }}

    function linApplyFilter(){{
      var dimension = document.getElementById('linDimension').value;
      var rawValue = (document.getElementById('linInput').value || '').trim();
      if (!rawValue) {{
        toast('请输入名称或 ID');
        return;
      }}
      // 优先从候选列表中匹配 label→id（支持名称输入）
      var items = __linSuggestions[dimension] || [];
      var matched = items.find(function(item) {{
        return item.label === rawValue || item.id === rawValue;
      }});
      // 如果没精确匹配，尝试模糊匹配第一个
      if (!matched) {{
        var lv = rawValue.toLowerCase();
        matched = items.find(function(item) {{
          return item.label.toLowerCase().indexOf(lv) >= 0 || item.id.toLowerCase().indexOf(lv) >= 0;
        }});
      }}
      var value = matched ? matched.id : rawValue;
      if (dimension === 'task') {{
        location.href = '/model/lineage/task/' + encodeURIComponent(value);
      }} else if (dimension === 'dataset') {{
        location.href = '/model/lineage/dataset/' + encodeURIComponent(value);
      }} else if (dimension === 'train') {{
        location.href = '/model/lineage/train/' + encodeURIComponent(value);
      }} else if (dimension === 'checkpoint') {{
        location.href = '/model/lineage/checkpoint/' + encodeURIComponent(value);
      }} else if (dimension === 'eval') {{
        location.href = '/model/lineage/eval/' + encodeURIComponent(value);
      }}
    }}

    // 下拉框切换时清空输入框并刷新候选项
    document.getElementById('linDimension').addEventListener('change', function() {{
      var dimension = this.value;
      var input = document.getElementById('linInput');
      var placeholders = {{
        task: '输入采集任务 ID / 名称',
        dataset: '输入数据集名称',
        train: '输入训练任务名称',
        checkpoint: '输入 Checkpoint 名称',
        eval: '输入评测任务名称',
      }};
      input.placeholder = placeholders[dimension] || '输入名称';
      input.value = '';
      linFillSuggestions(dimension);
    }});

    // 初始化当前维度的候选项
    linFillSuggestions(document.getElementById('linDimension').value);

    // 回车键触发跳转
    document.getElementById('linInput').addEventListener('keypress', function(e) {{
      if (e.key === 'Enter') {{
        linApplyFilter();
      }}
    }});
    // 链路高亮系统
    (function() {{
        const nodes = document.querySelectorAll('.lin-node[data-chain-id]');
        nodes.forEach(node => {{
            node.addEventListener('mouseenter', function() {{
                if (isAnyNodeLocked()) return;
                const chainIds = this.dataset.chainId.split(' ').filter(Boolean);
                if (chainIds.length === 0) return;
                highlightChain(chainIds);
            }});
            node.addEventListener('mouseleave', function() {{
                if (isAnyNodeLocked()) return;
                clearHighlight();
            }});
            node.addEventListener('dblclick', function(e) {{
                if (e.target.closest('.btn-link')) return;
                const chainIds = this.dataset.chainId.split(' ').filter(Boolean);
                if (chainIds.length === 0) return;
                if (this.classList.contains('locked')) {{
                    clearHighlight(); clearLock();
                }} else {{
                    clearLock(); highlightChain(chainIds); lockChain(chainIds);
                }}
            }});
        }});
        function highlightChain(chainIds) {{
            // 判断当前悬停的节点类型（通过 chainIds 中的模式判断）
            const hasCkptChain = chainIds.some(id => id.includes('_ckpt_'));
            const hasDsChain = chainIds.some(id => id.includes('_ds_'));

            nodes.forEach(node => {{
                const nodeChains = node.dataset.chainId.split(' ').filter(Boolean);
                if (nodeChains.length === 0) return;

                let isInChain = false;

                // 判断当前节点类型
                const nodeId = node.dataset.nodeId || '';
                const nodeIsCheckpoint = nodeId.startsWith('checkpoint_');
                const nodeIsEval = nodeId.startsWith('eval_');

                if (hasCkptChain && (nodeIsCheckpoint || nodeIsEval)) {{
                    // 悬停的是 Checkpoint/评测，当前节点也是 Checkpoint/评测
                    // 只检查 Checkpoint 维度的 chain_id
                    const nodeCkptChains = nodeChains.filter(id => id.includes('_ckpt_'));
                    const activeCkptChains = chainIds.filter(id => id.includes('_ckpt_'));
                    isInChain = activeCkptChains.some(id => nodeCkptChains.includes(id));
                }} else {{
                    // 其他情况：检查所有 chain_id
                    isInChain = chainIds.some(id => nodeChains.includes(id));
                }}

                if (isInChain) {{ node.classList.add('highlight'); node.classList.remove('dimmed'); }}
                else {{ node.classList.add('dimmed'); node.classList.remove('highlight'); }}
            }});
            if (window.__linEdgeHighlight) window.__linEdgeHighlight(true, chainIds);
        }}
        function clearHighlight() {{
            nodes.forEach(n => n.classList.remove('highlight','dimmed'));
            if (window.__linEdgeHighlight) window.__linEdgeHighlight(false, []);
        }}
        function lockChain(chainIds) {{
            nodes.forEach(node => {{
                const nodeChains = node.dataset.chainId.split(' ').filter(Boolean);
                if (nodeChains.length === 0) return;
                if (chainIds.some(id => nodeChains.includes(id))) node.classList.add('locked');
            }});
        }}
        function clearLock() {{ nodes.forEach(n => n.classList.remove('locked')); }}
        function isAnyNodeLocked() {{ return document.querySelector('.lin-node.locked') !== null; }}
    }})();
    // ── SVG 连线绘制 ──
    (function() {{
        const svg = document.getElementById('linSvg');
        const flow = document.getElementById('linFlow');
        if (!svg || !flow) return;

        // 父子关系：child data-node-id -> parent data-node-id 前缀匹配规则
        // 由后端在卡片上已注入 data-node-id；父子关系通过 data-parent 属性传递
        function nodeEl(id) {{ return flow.querySelector('[data-node-id="'+id+'"]'); }}

        function draw() {{
            svg.innerHTML = '';
            const flowRect = flow.getBoundingClientRect();
            const edges = window.__linEdges || [];
            edges.forEach(([childId, parentId]) => {{
                const c = nodeEl(childId), p = nodeEl(parentId);
                if (!c || !p) return;  // 父级找不到不画
                const cr = c.getBoundingClientRect(), pr = p.getBoundingClientRect();
                // 从父卡片右缘中点 → 子卡片左缘中点
                const x1 = pr.right - flowRect.left, y1 = pr.top + pr.height/2 - flowRect.top;
                const x2 = cr.left - flowRect.left, y2 = cr.top + cr.height/2 - flowRect.top;
                const dx = Math.max(24, (x2 - x1) / 2);
                const path = document.createElementNS('http://www.w3.org/2000/svg','path');
                path.setAttribute('d', `M ${{x1}} ${{y1}} C ${{x1+dx}} ${{y1}}, ${{x2-dx}} ${{y2}}, ${{x2}} ${{y2}}`);
                path.setAttribute('fill','none');
                path.setAttribute('stroke','#CBD5E1');
                path.setAttribute('stroke-width','2');
                path.setAttribute('data-edge-child', childId);
                path.setAttribute('data-edge-parent', parentId);
                svg.appendChild(path);
            }});
        }}

        // 首次绘制：多次延迟确保卡片布局完全稳定后再画连线
        function scheduleDraw() {{ setTimeout(draw, 50); }}
        window.addEventListener('load', () => setTimeout(draw, 80));
        document.addEventListener('DOMContentLoaded', () => setTimeout(draw, 120));
        setTimeout(draw, 200);
        setTimeout(draw, 500);  // 兜底：防止字体/图片加载导致布局偏移
        window.addEventListener('resize', () => setTimeout(draw, 80));
        // 监听容器尺寸变化（卡片内容加载完成后自动重绘）
        if (window.ResizeObserver) {{
          new ResizeObserver(() => setTimeout(draw, 30)).observe(flow);
        }}
        function setEdgesHighlight(on, activeChainIds) {{
            const paths = svg.querySelectorAll('path');
            activeChainIds = activeChainIds || [];
            paths.forEach(p => {{
                if (!on) {{
                    // 恢复默认灰线
                    p.setAttribute('stroke', '#ddd');
                    p.setAttribute('stroke-width', '2');
                    p.setAttribute('opacity', '1');
                    return;
                }}
                // 高亮态：检查连线两端节点是否都高亮 AND 共享对应维度的 chain_id
                const childId = p.getAttribute('data-edge-child');
                const parentId = p.getAttribute('data-edge-parent');
                const childEl = nodeEl(childId), parentEl = nodeEl(parentId);
                const bothHighlighted = childEl && parentEl
                    && childEl.classList.contains('highlight')
                    && parentEl.classList.contains('highlight');

                if (bothHighlighted) {{
                    const childChains = (childEl.dataset.chainId || '').split(' ').filter(Boolean);
                    const parentChains = (parentEl.dataset.chainId || '').split(' ').filter(Boolean);

                    let hasActiveSharedChain = false;

                    // 判断连线类型
                    const childIsCheckpoint = childId.startsWith('checkpoint_');
                    const childIsEval = childId.startsWith('eval_');
                    const parentIsCheckpoint = parentId.startsWith('checkpoint_');

                    if (childIsEval) {{
                        // 评测相关连线：只检查 Checkpoint 维度的 chain_id
                        const childCkptChains = childChains.filter(id => id.includes('_ckpt_'));
                        const parentCkptChains = parentChains.filter(id => id.includes('_ckpt_'));
                        const activeCkptChains = activeChainIds.filter(id => id.includes('_ckpt_'));

                        hasActiveSharedChain = activeCkptChains.some(activeId =>
                            childCkptChains.includes(activeId) && parentCkptChains.includes(activeId)
                        );
                    }} else if (childIsCheckpoint) {{
                        // Checkpoint 相关连线：优先检查 Checkpoint 维度的 chain_id
                        const childCkptChains = childChains.filter(id => id.includes('_ckpt_'));
                        const parentCkptChains = parentChains.filter(id => id.includes('_ckpt_'));
                        const activeCkptChains = activeChainIds.filter(id => id.includes('_ckpt_'));

                        hasActiveSharedChain = activeCkptChains.some(activeId =>
                            childCkptChains.includes(activeId) && parentCkptChains.includes(activeId)
                        );

                        // 如果没有 Checkpoint chain_id 匹配，尝试数据集 chain_id（兼容从数据集悬停的情况）
                        if (!hasActiveSharedChain) {{
                            const childDsChains = childChains.filter(id => id.includes('_ds_'));
                            const parentDsChains = parentChains.filter(id => id.includes('_ds_'));
                            const activeDsChains = activeChainIds.filter(id => id.includes('_ds_'));

                            hasActiveSharedChain = activeDsChains.some(activeId =>
                                childDsChains.includes(activeId) && parentDsChains.includes(activeId)
                            );
                        }}
                    }} else {{
                        // 其他连线（采集任务 → 数据集 → 训练任务）：只检查数据集维度的 chain_id
                        const childDsChains = childChains.filter(id => id.includes('_ds_'));
                        const parentDsChains = parentChains.filter(id => id.includes('_ds_'));
                        const activeDsChains = activeChainIds.filter(id => id.includes('_ds_'));

                        hasActiveSharedChain = activeDsChains.some(activeId =>
                            childDsChains.includes(activeId) && parentDsChains.includes(activeId)
                        );
                    }}

                    if (hasActiveSharedChain) {{
                        p.setAttribute('stroke', '#3B82F6');
                        p.setAttribute('stroke-width', '3');
                        p.setAttribute('opacity', '1');
                    }} else {{
                        // 两端都高亮，但不共享对应维度的 chain_id → 弱化
                        p.setAttribute('stroke', '#E2E8F0');
                        p.setAttribute('stroke-width', '1.5');
                        p.setAttribute('opacity', '0.5');
                    }}
                }} else {{
                    p.setAttribute('stroke', '#e8e8e8');
                    p.setAttribute('stroke-width', '1.5');
                    p.setAttribute('opacity', '0.5');
                }}
            }});
        }}
        window.__linEdgeHighlight = setEdgesHighlight;
        window.__linDraw = draw;
    }})();
    </script>
    """ + """
    <script>
    function showCkptHistory(ckptId) {
      var modal = document.getElementById('ckptHistoryModal');
      var body = document.getElementById('ckptHistoryBody');

      // Show modal with skeleton loading
      modal.style.display = 'flex';
      body.innerHTML = '<div class="ckpt-timeline-skeleton animate-pulse">' +
        '<div class="skeleton-item"><div class="skeleton-dot"></div><div class="skeleton-card"><div class="skeleton-line w-3-4"></div><div class="skeleton-line w-1-2"></div></div></div>' +
        '<div class="skeleton-item"><div class="skeleton-dot"></div><div class="skeleton-card"><div class="skeleton-line w-3-4"></div><div class="skeleton-line w-1-2"></div></div></div>' +
        '<div class="skeleton-item"><div class="skeleton-dot"></div><div class="skeleton-card"><div class="skeleton-line w-3-4"></div><div class="skeleton-line w-1-2"></div></div></div>' +
        '</div>';

      // Fetch history chain
      fetch('/model/lineage/checkpoint/' + ckptId + '/history')
        .then(function(r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(function(chain) {
          if (!Array.isArray(chain) || chain.length === 0) {
            body.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">无历史记录</div>';
            return;
          }

          // Build timeline HTML
          var html = '<div class="ckpt-timeline">';

          chain.forEach(function(ckpt, idx) {
            var isCurrent = idx === chain.length - 1;
            var currentClass = isCurrent ? ' current' : '';

            html += '<div class="ckpt-timeline-item' + currentClass + '">';
            html += '<div class="ckpt-timeline-dot"></div>';
            html += '<div class="ckpt-timeline-node" data-ckpt-nav="' + escapeHtml(ckpt.id) + '" onclick="navToCheckpoint(this.dataset.ckptNav)">';
            html += '<div class="ckpt-timeline-node-name">' + escapeHtml(ckpt.name) + '</div>';
            html += '<div class="ckpt-timeline-node-meta">';
            html += '<span>Step ' + extractStep(ckpt.name) + '</span>';
            if (ckpt.description) html += '<span> · ' + escapeHtml(ckpt.description) + '</span>';
            if (ckpt.created) html += '<span class="ckpt-timeline-node-time">' + escapeHtml(ckpt.created) + '</span>';
            html += '</div>';
            html += '</div></div>';

            // Add connector between nodes (not after last)
            if (idx < chain.length - 1) {
              var nextCkpt = chain[idx + 1];
              var connectorClass = nextCkpt.parent_type === 'dagger' ? ' dagger' : '';
              var label = nextCkpt.parent_type === 'dagger' ? 'dagger 回流' : 'test任务';
              html += '<div class="ckpt-timeline-connector' + connectorClass + '">' + label + '</div>';
            }
          });

          html += '</div>';
          body.innerHTML = html;
        })
        .catch(function(err) {
          console.error('Failed to load checkpoint history:', err);
          body.innerHTML = '<div style="text-align:center;padding:40px;color:#e74c3c;">加载失败，请重试</div>';
        });
    }

    function navToCheckpoint(id) {
      closeCkptHistoryModal();
      window.location.href = '/model/lineage/checkpoint/' + id;
    }

    function closeCkptHistoryModal() {
      document.getElementById('ckptHistoryModal').style.display = 'none';
    }

    function escapeHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }

    function extractStep(name) {
      var match = name.match(/[_-]([0-9]{4,6})$/);
      return match ? match[1] : '—';
    }

    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        closeCkptHistoryModal();
      }
    });
    </script>
    """


def _lineage_flow_html(selected):
    """给定模型 dict, 生成 4 列血缘流图 HTML (采集任务 → 数据集 → 实验/模型 → 部署设备)."""
    ds = next((d for d in DATASETS if d["name"] == selected["from_dataset"]), None)
    src_tasks_html = ""
    if ds:
        for tn in ds["source_tasks"]:
            tk = next((c for c in COLLECT_TASKS if c["id"] == tn), None)
            if tk:
                ep_count = tk.get("current", tk.get("collected", "—"))
                scene = tk.get("scene", "—")
                robot = tk.get("robot", "—")
                src_tasks_html += f'<div class="lin-node teal"><div class="ln-ttl">{tk["name"]}</div><div class="ln-meta">{ep_count} EP · {scene} · {robot}</div></div>'
            else:
                src_tasks_html += f'<div class="lin-node teal"><div class="ln-ttl">{tn}</div><div class="ln-meta">采集任务</div></div>'
    ds_html = (f'<div class="lin-node teal"><div class="ln-ttl">{ds["name"]}</div>'
               f'<div class="ln-meta">{ds["version"]} · {ds["episodes"]} EP · {ds["frames"]:,} 帧</div></div>') if ds else ''

    exp = next((e for e in EXPERIMENTS if e["id"] == selected["from_exp"]), None)
    exp_html = (f'<div class="lin-node purple"><div class="ln-ttl">{exp["name"]}</div>'
                f'<div class="ln-meta">{exp["model_type"]} · {exp["best_metric"]:.3f} ({exp["metric_name"]})</div></div>') if exp else ''

    deploys_for_model = [d for d in DEPLOYS if d["model"] == selected["name"] and d["version"] == selected["version"]]
    dp_html = ""
    if deploys_for_model:
        for dp in deploys_for_model:
            for tgt in dp["targets"]:
                dev = next((dv for dv in DEVICES if dv["id"] == tgt), None)
                loc = f' · {dev["location"]}' if dev else ''
                dp_html += f'<div class="lin-node coral"><div class="ln-ttl">{tgt}{loc}</div><div class="ln-meta">{status_tag(dp["status"])} · {dp["at"]}</div></div>'
    else:
        dp_html = '<div class="lin-node"><div class="muted">尚未部署</div></div>'

    return f"""
    <div class="lin-flow">
      <div class="lin-col">
        <h4>采集任务</h4>
        {src_tasks_html or '<div class="lin-node muted">—</div>'}
      </div>
      <div class="lin-arr">→</div>
      <div class="lin-col">
        <h4>数据集</h4>
        {ds_html or '<div class="lin-node muted">—</div>'}
      </div>
      <div class="lin-arr">→</div>
      <div class="lin-col">
        <h4>训练实验 / 模型</h4>
        {exp_html}
        <div class="lin-node purple"><div class="ln-ttl">{selected['name']}</div><div class="ln-meta">{selected['version']} · {selected['owner']}</div></div>
      </div>
      <div class="lin-arr">→</div>
      <div class="lin-col">
        <h4>部署设备</h4>
        {dp_html}
      </div>
    </div>
    """


@app.route("/model/lineage")
def lineage():
    ds_id = request.args.get("ds", "")
    if ds_id:
        return redirect(f"/model/lineage/dataset/{ds_id}")

    selected_id = request.args.get("model", "md_901")
    selected = next((m for m in MODELS if m["id"] == selected_id), MODELS[0])

    options = "".join(
        f'<option value="{m["id"]}" {"selected" if m["id"] == selected_id else ""}>{m["name"]} · {m["version"]}</option>'
        for m in MODELS
    )

    content = page_header(
        "端到端血缘",
        "数据集 → 模型 → 部署 · 双向追溯一条链路",
        "影响分析 · 跨平台资产目录 · 语义检索",
    ) + f"""
    <div class="lin-pick">
      <span class="muted">选择模型版本:</span>
      <select onchange="location.href='/model/lineage?model='+this.value">{options}</select>
    </div>
    {_lineage_flow_html(selected)}
    <div class="card" style="margin-top:18px;">
      <h4>说明</h4>
      <p class="muted">一期血缘覆盖「数据集 → 模型 → 部署」三段, 可双向追溯。二期补: 影响分析 (一条数据集变更, 会影响哪些模型 / 部署) · 跨平台资产目录 · 语义检索。</p>
    </div>
    """
    return render_page("端到端血缘", content, active="/model/models", module="model",
                       breadcrumb='模型平台 / 模型仓库 / <b>端到端血缘</b>', mvp_note="MVP 一期")


def _lineage_page(anchor_type, anchor_id):
    """通用血缘页渲染函数"""
    cfg = LINEAGE_CONFIG[anchor_type]
    anchor = cfg['find_fn'](anchor_id)

    if anchor is None:
        empty_content = page_header(cfg['title'], cfg['subtitle'], "") + f"""
        <div style="text-align:center;padding:80px 0;color:rgba(0,0,0,0.45);">
          <div style="font-size:40px;margin-bottom:16px;">&#128269;</div>
          <div style="font-size:15px;font-weight:500;margin-bottom:8px;color:rgba(0,0,0,0.65);">未找到匹配的节点</div>
          <div style="font-size:13px;">"{anchor_id}" 不存在，请检查名称是否正确</div>
          <a href="{cfg['list_path']}" class="btn" style="margin-top:24px;display:inline-block;">返回列表</a>
        </div>
        """
        return render_page(cfg['title'], empty_content, active=cfg['list_path'], module="model")

    content = page_header(
        cfg['title'],
        cfg['subtitle'],
        "采集任务 · 训练数据集 · 训练任务 · checkpoint · 评测任务",
    ) + f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
      <a href="{cfg['detail_url_fn'](anchor)}" class="btn">&#8249; 返回</a>
    </div>
    {_lineage_detail_html(anchor_type, anchor_id)}
    """

    return render_page(
        cfg['title'],
        content,
        active=cfg['list_path'],
        module="model",
        breadcrumb=cfg['breadcrumb_fn'](anchor),
        mvp_note="MVP 一期"
    )


@app.route("/model/lineage/train/<exp_id>")
def lineage_train(exp_id):
    return _lineage_page('train', exp_id)


@app.route("/model/lineage/checkpoint/<ckpt_id>")
def lineage_checkpoint(ckpt_id):
    return _lineage_page('checkpoint', ckpt_id)


@app.route("/model/lineage/dataset/<ds_id>")
def lineage_dataset(ds_id):
    return _lineage_page('dataset', ds_id)


@app.route("/model/lineage/eval/<ev_id>")
def lineage_eval(ev_id):
    return _lineage_page('eval', ev_id)


@app.route("/model/lineage/task/<task_id>")
def lineage_task(task_id):
    return _lineage_page('task', task_id)


@app.route("/model/lineage/checkpoint/<ckpt_id>/history")
def checkpoint_history(ckpt_id):
    """Return the full ancestor chain for a checkpoint as JSON"""
    # First check if checkpoint exists
    ckpt = _ckpt_by_id(ckpt_id)
    if not ckpt:
        return jsonify({"error": "Checkpoint not found"}), 404

    chain = []
    current_id = ckpt_id
    visited = set()  # Prevent circular references

    while current_id and current_id not in visited:
        visited.add(current_id)
        ckpt = _ckpt_by_id(current_id)
        if not ckpt:
            break

        chain.append({
            "id": ckpt["id"],
            "name": ckpt["name"],
            "status": ckpt.get("status", "—"),
            "owner": ckpt.get("owner", "—"),
            "created": ckpt.get("created", "—"),
            "parent_checkpoint_id": ckpt.get("parent_checkpoint_id"),
            "parent_type": ckpt.get("parent_type")
        })

        current_id = ckpt.get("parent_checkpoint_id")

    # Reverse to show root → current (oldest to newest)
    chain.reverse()

    return jsonify(chain)


# ════════════════════════════════════════════════════════════════
# Section 10: Main
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    print(f"\n  具身云 · 工具链 MVP Demo — http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
