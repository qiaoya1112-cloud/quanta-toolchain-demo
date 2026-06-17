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
import os
import re
import sys
from flask import Flask, render_template_string, request, redirect

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
    {"id": "11092", "name": "20260529_河北省石家庄元氏县马村乡使庄村富强东路19号_光轮智能_UDASv2",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "标注",
     "collected": 180, "qc_pass": 171, "qc_warn": 4, "qc_fail": 5,
     "label_done": 0, "label_total": 176, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "11091", "name": "20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "采集",
     "collected": 18, "qc_pass": 0, "qc_warn": 0, "qc_fail": 18,
     "label_done": 0, "label_total": 18, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "11090", "name": "20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "采集",
     "collected": 42, "qc_pass": 0, "qc_warn": 0, "qc_fail": 42,
     "label_done": 0, "label_total": 42, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "11089", "name": "20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "质检",
     "collected": 56, "qc_pass": 0, "qc_warn": 0, "qc_fail": 56,
     "label_done": 0, "label_total": 56, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "11088", "name": "20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "质检",
     "collected": 28, "qc_pass": 0, "qc_warn": 0, "qc_fail": 28,
     "label_done": 0, "label_total": 28, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
    {"id": "11087", "name": "20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼",
     "project": "预训练采集", "status": "running", "priority": "中", "stage": "标注",
     "collected": 31, "qc_pass": 1, "qc_warn": 0, "qc_fail": 30,
     "label_done": 0, "label_total": 31, "sample_done": 0, "sample_total": 0,
     "created": "2026-06-07", "due": "2026-06-08"},
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
    {"id": "ds_501", "name": "clean_whiteboard_v4", "version": "v4", "type": "train",
     "episodes": 137, "frames": 51200, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "joanna.qiao", "status": "active", "created": "2026-06-14 10:00",
     "source_tasks": ["擦白板 · 第 3 批", "擦白板 · 补采"]},
    {"id": "ds_502", "name": "tidy_desk_v2", "version": "v2", "type": "train",
     "episodes": 118, "frames": 44600, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "Lance Li", "status": "active", "created": "2026-06-09 17:00",
     "source_tasks": ["整理桌面 · 导师演示"]},
    {"id": "ds_503", "name": "plant_pour_pilot", "version": "v1", "type": "train",
     "episodes": 0, "frames": 0, "train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1,
     "owner": "Min Chen", "status": "pending", "created": "2026-06-16 14:30",
     "source_tasks": ["浇花 · 试点"]},
    {"id": "ds_504", "name": "clean_whiteboard_eval_v1", "version": "v1", "type": "eval",
     "episodes": 12, "frames": 4400, "train_ratio": 0.0, "val_ratio": 0.0, "test_ratio": 1.0,
     "owner": "joanna.qiao", "status": "active", "created": "2026-06-14 11:00",
     "source_tasks": ["擦白板 · 评测留出"]},
]

# ── 模型平台 ──

EXPERIMENTS = [
    {"id": "exp_7916", "name": "robotwin_pi05_datamil_stack_blocks_two_top10pct_cotrain",
     "model_type": "Spirit v1.7", "dataset": "—", "tag": "—",
     "epochs": 50, "current_epoch": 35,
     "best_metric": 0.852, "metric_name": "成功率", "status": "running",
     "started": "2026-06-17 03:23:39", "dur": "—", "owner": "—"},
    {"id": "exp_7757", "name": "20260615_pi05_oldft_sortpill_newobs_centercrop_manip2",
     "model_type": "Spirit v1.7", "dataset": "—", "tag": "—",
     "epochs": 50, "current_epoch": 28,
     "best_metric": 0.821, "metric_name": "成功率", "status": "running",
     "started": "2026-06-16 11:57:35", "dur": "—", "owner": "—"},
    {"id": "exp_7560", "name": "20260615_HouseHold_newper_stop_32",
     "model_type": "Spirit v1.7", "dataset": "—", "tag": "—",
     "epochs": 50, "current_epoch": 33,
     "best_metric": 0.812, "metric_name": "成功率", "status": "running",
     "started": "2026-06-16 11:18:17", "dur": "—", "owner": "—"},
    {"id": "exp_7539", "name": "20260602_ManualDagger2_NarrowTable_Moz1WB",
     "model_type": "Spirit v1.6", "dataset": "tidy_desk_v2", "tag": "—",
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
    {"id": "ev_701", "exp": "spirit-v1.7-whiteboard-base", "benchmark": "clean_whiteboard_eval_v1",
     "success_rate": 0.873, "mse": 0.0142, "status": "passed", "at": "2026-06-15 10:30"},
    {"id": "ev_702", "exp": "spirit-v1.7-desk-sft", "benchmark": "tidy_desk_v2 (val split)",
     "success_rate": None, "mse": None, "status": "pending", "at": "—"},
    {"id": "ev_703", "exp": "spirit-v1.6-whiteboard-baseline", "benchmark": "clean_whiteboard_eval_v1",
     "success_rate": 0.792, "mse": 0.0187, "status": "passed", "at": "2026-06-14 08:30"},
    {"id": "ev_704", "exp": "spirit-v1.7-whiteboard-large-bs", "benchmark": "clean_whiteboard_eval_v1",
     "success_rate": 0.848, "mse": 0.0156, "status": "passed", "at": "2026-06-16 22:30"},
]

DEPLOYS = [
    {"id": "dp_801", "model": "spirit-v1.7-whiteboard-base", "version": "v1.7.0",
     "targets": ["moz1-002", "moz1-003", "moz1-005"],
     "status": "deployed", "at": "2026-06-15 14:00", "operator": "joanna.qiao"},
    {"id": "dp_802", "model": "spirit-v1.6-whiteboard-baseline", "version": "v1.6.0",
     "targets": ["moz1-001"],
     "status": "deployed", "at": "2026-06-13 10:00", "operator": "joanna.qiao"},
    {"id": "dp_803", "model": "spirit-v1.7-whiteboard-base", "version": "v1.7.1",
     "targets": ["moz1-003", "moz1-004", "moz1-005", "moz1-006", "moz1-007", "moz1-008"],
     "status": "pending", "at": "—", "operator": "Lance Li"},
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
    {"id": "7916", "name": "20260613_HouseHold_stop_32_40000",
     "status": "cached", "owner": "Lance Li", "created": "2026-06-16 18:39:01"},
    {"id": "7757", "name": "20260604_opd_exp1_sft_taskA_gpu8_50000",
     "status": "not_cached", "owner": "Hannah Wang", "created": "2026-06-15 16:08:33"},
    {"id": "7560", "name": "20260610_HouseHold_stop_32_50000",
     "status": "cached", "owner": "—", "created": "2026-06-13 09:42:33"},
    {"id": "7539", "name": "20260609_opd_exp5a_single_wobcloss_taskAB_gpu8_50000",
     "status": "cached", "owner": "—", "created": "2026-06-13 05:05:41"},
    {"id": "7466", "name": "20260610_HouseHold_stop_32_40000",
     "status": "merge_failed", "owner": "—", "created": "2026-06-12 17:18:42"},
    {"id": "7374", "name": "20260518_HouseHold_stop_24_50000",
     "status": "cached", "owner": "Lance Li", "created": "2026-06-11 19:30:46"},
    {"id": "7325", "name": "20260518_HouseHold_stop_24_40000",
     "status": "cached", "owner": "Lance Li", "created": "2026-06-11 03:42:38"},
    {"id": "7285", "name": "20260608_opd_exp4_cascade_taskAB_gpu8_50000",
     "status": "cached", "owner": "—", "created": "2026-06-10 15:08:00"},
    {"id": "6873", "name": "catl-ckpt-0608",
     "status": "cached", "owner": "Liquan Zheng", "created": "2026-06-08 18:12:22"},
    {"id": "6869", "name": "catl-liquanzheng-upload",
     "status": "not_cached", "owner": "Liquan Zheng", "created": "2026-06-08 17:26:35"},
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
    {"id": "moz1-001", "name": "moz1-001 · 实验室东", "type": "moz1", "status": "in_use",
     "location": "实验室 东区", "current_user": "Lance Li", "model": "spirit-v1.6 / v1.6.0",
     "last_seen": "now",
     "sw_dep": "Ubuntu 22.04 · ROS2 Humble · spirit-runtime ≥1.5",
     "hw_dep": "6-DOF 机械臂 · RealSense D455 · Jetson Orin"},
    {"id": "moz1-002", "name": "moz1-002 · 实验室西", "type": "moz1", "status": "in_use",
     "location": "实验室 西区", "current_user": "joanna.qiao", "model": "spirit-v1.7 / v1.7.0",
     "last_seen": "now",
     "sw_dep": "Ubuntu 22.04 · ROS2 Humble · spirit-runtime ≥1.7",
     "hw_dep": "6-DOF 机械臂 · RealSense D455 · Jetson Orin"},
    {"id": "moz1-003", "name": "moz1-003 · 二楼", "type": "moz1", "status": "online",
     "location": "二楼 工位 A", "current_user": "—", "model": "spirit-v1.6 / v1.5.2",
     "last_seen": "now",
     "sw_dep": "Ubuntu 22.04 · ROS2 Humble · spirit-runtime 1.5",
     "hw_dep": "6-DOF 机械臂 · RealSense D455 · Jetson Orin"},
    {"id": "moz2-001", "name": "moz2-001 · 一楼", "type": "moz2", "status": "in_use",
     "location": "一楼 测试区", "current_user": "Min Chen", "model": "—",
     "last_seen": "now",
     "sw_dep": "Ubuntu 22.04 · ROS2 Humble · mobi-runtime ≥2.0",
     "hw_dep": "双臂 7-DOF · 双目 D455 · Jetson Orin NX"},
    {"id": "moz2-002", "name": "moz2-002 · 一楼", "type": "moz2", "status": "offline",
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
            ]),
            ("训练", [
                ("/model/experiments", "训练任务", "&#9881;", "优化"),
                ("/model/checkpoints", "Checkpoint", "&#9783;", "优化"),
            ]),
            ("部署", [
                ("/model/deploy", "部署任务", "&#9654;", "新增"),
                ("/model/convert", "模型转换", "&#9881;", "新增"),
                ("/model/models", "模型仓库", "&#9776;", "新增"),
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


# ── 平台线形图标（统一用主色 stroke）──
ICON_DATA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5.5" rx="7" ry="2.5"/><path d="M5 5.5v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6"/><path d="M5 11.5v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6"/></svg>'
ICON_MODEL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="5" cy="6" r="1.8"/><circle cx="5" cy="18" r="1.8"/><circle cx="12" cy="12" r="1.8"/><circle cx="19" cy="6" r="1.8"/><circle cx="19" cy="18" r="1.8"/><path d="M6.7 7L10.3 10.7M6.7 17L10.3 13.3M13.7 10.7L17.3 7M13.7 13.3L17.3 17"/></svg>'
ICON_DEVICE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="6" width="12" height="12" rx="1.5"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M10 6V3M14 6V3M10 21v-3M14 21v-3M21 10h-3M21 14h-3M6 10H3M6 14H3"/></svg>'
ICON_ASSET = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="6" r="2.2"/><circle cx="12" cy="12" r="2.2"/><circle cx="19" cy="18" r="2.2"/><path d="M6.5 7.5L10.5 10.5M13.5 13.5L17.5 16.5"/></svg>'
ICON_APP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="6" height="4" rx="1"/><rect x="3" y="16" width="6" height="4" rx="1"/><rect x="15" y="10" width="6" height="4" rx="1"/><path d="M9 6 H12 V12 H15"/><path d="M9 18 H12 V12 H15"/></svg>'

PLATFORM_ICONS = {"data": ICON_DATA, "model": ICON_MODEL, "app": ICON_APP, "device": ICON_DEVICE}
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

/* ── Buttons ── */
.btn { display:inline-flex; align-items:center; gap:6px; height:34px; padding:0 16px; border-radius:8px; font-size:14px; cursor:pointer; border:1px solid #d9d9d9; background:#fff; color:rgba(0,0,0,0.85); text-decoration:none; box-sizing:border-box; }
.btn:hover { border-color:#149DAA; color:#149DAA; }
.btn-primary { background:#149DAA; border-color:#149DAA; color:#fff; }
.btn-primary:hover { background:#0F8190; border-color:#0F8190; color:#fff; }
.btn-sm { height:28px; padding:0 12px; font-size:13px; }

/* ── Table ── */
.ant-table { width:100%; border-collapse:collapse; font-size:14px; background:#fff; }
.ant-table thead th { background:#fafafa; padding:11px 16px; font-weight:500; color:rgba(0,0,0,0.85); text-align:left; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.ant-table tbody td { padding:11px 16px; border-bottom:1px solid #f0f0f0; color:rgba(0,0,0,0.65); vertical-align:middle; }
.ant-table tbody tr:hover td { background:#fafafa; }
.actions-cell { white-space:nowrap; }
.mono { font-family:'SF Mono',Menlo,monospace; font-size:12.5px; color:rgba(0,0,0,0.55); }
.table-wrap { background:#fff; border:1px solid #f0f0f0; border-radius:8px; overflow:hidden; }

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

/* ── Lineage (asset page) ── */
.lin-pick { display:flex; gap:10px; align-items:center; margin-bottom:18px; }
.lin-pick select { padding:7px 14px; border:1px solid #d9d9d9; border-radius:8px; font-size:14px; outline:none; min-width:280px; }
.lin-flow { display:grid; grid-template-columns:1fr 30px 1fr 30px 1fr 30px 1fr; gap:0; align-items:stretch; background:#fff; padding:24px 18px; border:1px solid #f0f0f0; border-radius:8px; }
.lin-col { display:flex; flex-direction:column; gap:8px; }
.lin-col h4 { font-size:12px; color:rgba(0,0,0,0.55); margin:0 0 8px; font-weight:500; text-transform:uppercase; letter-spacing:0.6px; }
.lin-node { padding:10px 14px; border-radius:8px; border:1px solid #d9d9d9; background:#fafafa; font-size:13px; line-height:1.55; }
.lin-node .ln-ttl { font-weight:500; color:rgba(0,0,0,0.85); }
.lin-node .ln-meta { color:rgba(0,0,0,0.45); font-size:12px; margin-top:3px; }
.lin-node.teal { background:#e1f5ee; border-color:#5dcaa5; }
.lin-node.purple { background:#eeedfe; border-color:#7F77DD; }
.lin-node.coral { background:#fef0eb; border-color:#f0997b; }
.lin-arr { display:flex; align-items:center; justify-content:center; color:rgba(0,0,0,0.4); font-size:22px; }

/* ── Labeled filter bar (训练任务/Checkpoint 列表用) ── */
.fb-labeled { background:#fff; padding:16px 18px; border:1px solid #f0f0f0; border-radius:8px; margin-bottom:14px; display:flex; gap:18px; align-items:flex-end; flex-wrap:wrap; }
.fb-labeled .ff { display:flex; flex-direction:column; gap:6px; }
.fb-labeled .ff > label { font-size:13px; color:rgba(0,0,0,0.72); }
.fb-labeled .ff input, .fb-labeled .ff select { height:34px; min-width:240px; padding:5px 12px; border:1px solid #d9d9d9; border-radius:6px; font-size:14px; outline:none; background:#fff; box-sizing:border-box; }
.fb-labeled .ff input::placeholder { color:rgba(0,0,0,0.32); }
.fb-labeled .ff input:focus, .fb-labeled .ff select:focus { border-color:#149DAA; box-shadow:0 0 0 2px rgba(20,157,170,0.12); }
.fb-labeled .ff-refresh { width:34px; height:34px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; cursor:pointer; display:flex; align-items:center; justify-content:center; color:rgba(0,0,0,0.55); font-size:15px; }
.fb-labeled .ff-refresh:hover { border-color:#149DAA; color:#149DAA; }

/* ── Page actions (top-right primary button) ── */
.page-actions { display:flex; justify-content:flex-end; margin-bottom:14px; }

/* ── Pill-style action buttons in tables (TEST / DAGGER / 复制) ── */
.tbtn { display:inline-flex; align-items:center; gap:5px; height:28px; padding:0 13px; border-radius:6px; font-size:12.5px; cursor:pointer; border:1px solid #d9d9d9; background:#fff; color:rgba(0,0,0,0.75); text-decoration:none; margin-right:4px; box-sizing:border-box; }
.tbtn:hover { border-color:#149DAA; color:#149DAA; }

/* ── Wide drawer (for 新增训练任务) ── */
.drawer.drawer-wide { width:680px; }

/* ── Drawer form: row 2-col ── */
.fg-row { display:flex; gap:14px; }
.fg-row > .fg { flex:1; }
.fg-hint { font-size:11px; color:rgba(0,0,0,0.4); margin-top:2px; }
.fg-req::before { content:'*'; color:#cf1322; margin-right:4px; }

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

/* ── 部署任务: 设备数胶囊 + 点击弹出清单 ── */
.devs-cell { position:relative; display:inline-block; }
.devs-pill { display:inline-flex; align-items:center; gap:5px; padding:3px 12px; border-radius:11px; background:#DEF6F9; border:1px solid #7BD8DF; color:#149DAA; font-size:13px; cursor:pointer; user-select:none; font-family:'SF Mono',Menlo,monospace; }
.devs-pill:hover { background:#cfeef2; }
.devs-pill .ca { font-size:9px; opacity:0.7; transition:transform 0.15s; }
.devs-pill.open .ca { transform:rotate(180deg); }
.devs-pop { display:none; position:absolute; top:calc(100% + 6px); left:0; background:#fff; border:1px solid #e5e7eb; border-radius:8px; box-shadow:0 6px 22px rgba(0,0,0,0.12); padding:6px; z-index:50; min-width:180px; max-height:260px; overflow-y:auto; }
.devs-pop.open { display:block; }
.devs-pop a { display:flex; justify-content:space-between; align-items:center; padding:6px 10px; border-radius:4px; font-size:13px; color:#149DAA; font-family:'SF Mono',Menlo,monospace; text-decoration:none; }
.devs-pop a:hover { background:#EBF8FA; color:#0F8190; }
.devs-pop a .arr { font-size:10px; color:rgba(0,0,0,0.3); }

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
.tm-subtab:hover { color:#149DAA; }
.tm-subtab.active { background:#fff; color:#149DAA; font-weight:500; box-shadow:0 1px 3px rgba(0,0,0,0.06); }
.tm-subtab .ct { font-size:11.5px; color:rgba(0,0,0,0.4); }
.tm-subtab.active .ct { color:#149DAA; opacity:0.8; }

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
.logs-subtabs { display:flex; gap:24px; padding-bottom:10px; border-bottom:1px solid #f0f0f0; margin-bottom:14px; }
.ls-tab { font-size:14px; color:rgba(0,0,0,0.55); cursor:pointer; padding-bottom:8px; border-bottom:2px solid transparent; margin-bottom:-11px; user-select:none; }
.ls-tab:hover { color:#149DAA; }
.ls-tab.active { color:#149DAA; font-weight:500; border-bottom-color:#149DAA; }
.logs-controls { display:flex; align-items:center; gap:14px; margin-bottom:10px; flex-wrap:wrap; }
.lc-pill { font-size:12px; padding:4px 12px; border-radius:11px; background:#DEF6F9; color:#149DAA; border:1px solid #7BD8DF; }
.lc-grp { display:flex; align-items:center; gap:8px; font-size:13px; color:rgba(0,0,0,0.65); }
.lc-grp select { height:30px; padding:0 10px; border:1px solid #d9d9d9; border-radius:5px; font-size:13px; background:#fff; min-width:140px; outline:none; }
.lc-right { margin-left:auto; display:flex; align-items:center; gap:14px; font-size:13px; color:rgba(0,0,0,0.65); }
.lc-right input.lc-num { width:50px; height:28px; padding:0 8px; border:1px solid #d9d9d9; border-radius:5px; font-size:13px; text-align:center; outline:none; }
.lc-toggle { display:inline-block; width:30px; height:16px; border-radius:8px; background:#d9d9d9; position:relative; cursor:pointer; vertical-align:middle; }
.lc-toggle.on { background:#149DAA; }
.lc-toggle::after { content:''; position:absolute; top:2px; left:2px; width:12px; height:12px; border-radius:50%; background:#fff; transition:transform 0.15s; }
.lc-toggle.on::after { transform:translateX(14px); }
.lc-icon { width:26px; height:26px; display:inline-flex; align-items:center; justify-content:center; color:rgba(0,0,0,0.55); border-radius:4px; cursor:pointer; }
.lc-icon:hover { color:#149DAA; background:#f5f7fa; }
.logs-body { background:#fafbfc; border:1px solid #e5e7eb; border-radius:6px; padding:14px 16px; font-family:'SF Mono',Menlo,monospace; font-size:12px; line-height:1.7; color:rgba(0,0,0,0.85); max-height:620px; overflow:auto; white-space:pre; margin:0; }

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
        <div class="tp-divider"></div>
        <a class="tp-item" href="#" onclick="toast('Demo: 账号管理');return false;">账号管理</a>
        <a class="tp-item" href="#" onclick="toast('Demo: 权限管理');return false;">权限管理</a>
        <a class="tp-item" href="#" onclick="toast('Demo: 资源管理');return false;">
          资源管理<span class="tp-sub">存储 · 算力资源</span>
        </a>
      </div>
    </div>
    <div class="tn-user">J</div>
  </div>
</header>

<div class="q-layout {% if portal %}portal-mode{% endif %}">
  {% if not portal %}
  <aside class="q-sider">
    <div class="smh-wrap">
      <div class="smh" onclick="toggleModSwitch()">
        <div class="smh-icon">{{ module_icon|safe }}</div>
        <div class="smh-name">{{ module_name }}</div>
        <span class="smh-caret">&#9662;</span>
      </div>
      <div class="mod-switch" id="modSwitch">{{ mod_switch_html|safe }}</div>
    </div>
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
<script>
function toast(msg){ var t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show'); setTimeout(function(){t.classList.remove('show');},1500); }
function openDrawer(id){ document.getElementById('drawerMask').classList.add('active'); var d=document.getElementById(id); if(d) d.classList.add('active'); }
function closeDrawer(){ document.getElementById('drawerMask').classList.remove('active'); document.querySelectorAll('.drawer.active').forEach(function(d){d.classList.remove('active');}); }
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
/* 新增训练任务: 抽屉打开时 lazy-init CodeMirror YAML 编辑器 + 字符计数 */
function openTrainDrawer(){
  openDrawer('drawerNewTrain');
  setTimeout(function(){
    var ta = document.getElementById('yamlEditor');
    if (ta && !ta._cmInited && window.CodeMirror){
      ta._cmInited = true;
      var cm = CodeMirror.fromTextArea(ta, { mode:'yaml', lineNumbers:false, lineWrapping:false, viewportMargin:Infinity });
      ta._cm = cm;
    } else if (ta && ta._cm){
      ta._cm.refresh();
    }
  }, 50);
}
function updateNameCount(input){
  var c = document.getElementById('nameCount');
  if (c) c.textContent = (input.value.length) + ' / 50';
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
}
function toggleLogToggle(el){ el.classList.toggle('on'); }
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
      <button class="ff-refresh" onclick="toast('Demo: 已刷新')" title="刷新">&#8635;</button>
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
      <button class="ff-refresh" onclick="toast('Demo: 已刷新')" title="刷新">&#8635;</button>
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
      <button class="ff-refresh" onclick="toast('Demo: 已刷新')" title="刷新">&#8635;</button>
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
            <a class="btn btn-primary" href="#" onclick="toast('Demo: 进入 {t['type']} 工作台');return false;">进入工作台 &rsaquo;</a>
          </div>
        </div>
        """
    content = f"""
    <div class="stat-grid">{stat_cards_html}</div>
    <div class="wb-list">{cards}</div>
    """
    return render_page("工作台", content, active="/data/workbench", module="data",
                       breadcrumb='数据平台 / <b>工作台</b>', mvp_note="MVP 一期")


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
        src_html = " · ".join(f'<span class="tag tag-teal">{s}</span>' for s in d["source_tasks"])
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
_DP_PATHS = ("lake", "raw", "query", "datasets", "operators", "pipelines", "runs", "tags")
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
    _dp_capture.clear()
    dp.query()
    inner = _rewrite_dp_links(_dp_capture.get("content", "") or "")
    extra = _dp_capture.get("extra_script")
    # 把「查看数据源」二级按钮塞进 .q-mode-tabs flex 行的尾部, 用 margin-left:auto 推到右侧
    # flex 默认 align-items:center, 自动与 Pretty/SQL 切换 tab 垂直居中
    btn_html = (
        '<a class="btn" href="/model/data/raw" '
        'style="margin-left:auto;align-self:center;padding:4px 12px;'
        'font-size:13px;line-height:1.6;">查看数据源 &rsaquo;</a>'
    )
    inner = re.sub(
        r'(<div class="q-mode-tabs">)(.*?)(</div>)',
        lambda m: m.group(1) + m.group(2) + btn_html + m.group(3),
        inner, count=1, flags=re.S,
    )
    return render_page(
        _dp_capture.get("title", "数据查询"),
        inner,
        active="/model/data/query", module="model", extra_script=extra,
    )


@app.route("/model/data/datasets")
def model_data_datasets():
    return _dp_render(dp.datasets, "/model/data/datasets")


@app.route("/model/data/raw")
def model_data_raw():
    # 数据资产是「数据查询」的二级页, 侧栏保持 数据查询 选中态
    return _dp_render(dp.raw_data, "/model/data/query")


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
    for e in EXPERIMENTS:
        # 训练任务名称作为可点击链接 (跳到任务详情 → checkpoint 列表)
        status_html = {
            "running": '<span class="tag tag-orange">运行中</span>',
            "done":    '<span class="tag tag-green">成功</span>',
            "failed":  '<span class="tag tag-red">失败</span>',
        }.get(e["status"], f'<span class="tag tag-gray">{e["status"]}</span>')
        dataset_html = '—' if e["dataset"] == "—" else f'<a href="/model/data/datasets" class="mono">{e["dataset"]}</a>'
        tag_html = '—' if e["tag"] == "—" else f'<span class="tag tag-gray">{e["tag"]}</span>'
        rows += f"""<tr>
          <td><a href="/model/experiments/{e['id']}" style="color:#149DAA">{e['name']}</a></td>
          <td>{dataset_html}</td>
          <td>{status_html}</td>
          <td>{tag_html}</td>
          <td>{e['owner']}</td>
          <td class="muted mono">{e['started']}</td>
          <td class="muted">{e['dur']}</td>
          <td class="actions-cell">
            <a class="tbtn" href="#" onclick="toast('Demo: 已复制配置');return false;">&#10697; 复制</a>
            <a class="tbtn" href="#" onclick="toast('Demo: 查看更多操作');return false;">⋯ 更多</a>
          </td>
        </tr>"""

    content = page_header(
        "训练任务",
        "数据集挂载 · 实验管理 · 超参 · Checkpoint",
        "分布式训练 · 训练监控 (loss 曲线)",
    ) + f"""
    <div class="page-actions">
      <a class="btn btn-primary" onclick="openTrainDrawer();return false;">+ 新增训练任务</a>
    </div>

    <div class="fb-labeled">
      <div class="ff"><label>训练任务名称</label><input placeholder="请输入训练任务名称"></div>
      <div class="ff"><label>标签</label><select><option>请选择标签</option><option>robotwin</option><option>HouseHold</option><option>pi05</option></select></div>
      <div class="ff"><label>数据集</label><select><option>请选择数据集</option><option>clean_whiteboard_v4</option><option>tidy_desk_v2</option></select></div>
      <button class="ff-refresh" onclick="toast('Demo: 已刷新')" title="刷新">&#8635;</button>
    </div>

    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr>
          <th>名称</th>
          <th>关联数据集</th>
          <th>状态 &#9662;</th>
          <th>标签</th>
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
          <label class="fg-req">训练任务名称</label>
          <input placeholder="请输入训练任务名称（A-z,0-9,_）" maxlength="50" oninput="updateNameCount(this)">
          <div class="fg-hint" style="text-align:right" id="nameCount">0 / 50</div>
        </div>

        <div class="fg">
          <label class="fg-req">镜像</label>
          <select><option>请选择镜像</option><option>spirit-train:v1.7-cuda12</option><option>spirit-train:v1.6-cuda11</option></select>
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
          <td class="actions-cell"><a href="#" style="color:#149DAA" onclick="toast('Demo: 已发起缓存');return false;">缓存</a></td>
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
        <span class="ls-tab" onclick="switchLogSubtab(this)">历史日志</span>
        <span class="ls-tab active" onclick="switchLogSubtab(this)">实时日志</span>
      </div>
      <div class="logs-controls">
        <span class="lc-pill">实时加载中</span>
        <div class="lc-grp"><label>实例</label><select><option>worker_0</option><option>worker_1</option><option>worker_2</option></select> <span style="color:rgba(0,0,0,0.3);font-size:12px;">&#9432;</span></div>
        <div class="lc-right">
          <span>查看最新 &#9432;</span>
          <input class="lc-num" value="100"> 行
          <span>时间戳</span><span class="lc-toggle on" onclick="toggleLogToggle(this)"></span>
          <span>自动更新</span><span class="lc-toggle on" onclick="toggleLogToggle(this)"></span>
          <span class="lc-icon">&#128269;</span>
          <span class="lc-icon">&#9728;</span>
          <span class="lc-icon">&#9974;</span>
        </div>
      </div>
      <pre class="logs-body">{log_text}</pre>
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

    # ── 血缘 tab: 从这个训练任务产出的模型出发, 反向追溯链路 ──
    _model_from_exp = next((m for m in MODELS if m["from_exp"] == e["id"]), None)
    if _model_from_exp:
        tab_lineage = f"""
        <div class="muted" style="font-size:12.5px;margin-bottom:14px;">
          以本任务产出模型 <b>{_model_from_exp['name']} {_model_from_exp['version']}</b> 为锚点的端到端血缘链路
        </div>
        {_lineage_flow_html(_model_from_exp)}
        """
    else:
        tab_lineage = """
        <div class="card" style="text-align:center;padding:50px 30px;">
          <div style="font-size:42px;color:rgba(0,0,0,0.15);margin-bottom:10px;">&#9783;</div>
          <p class="muted" style="margin:0;">本任务尚未产出已注册的模型版本, 暂无可追溯的血缘链路</p>
        </div>
        """

    # 顶层结构: 头卡片 + 4 顶 tab + 4 pane
    content = f"""
    <div class="tdh">
      <div class="tdh-name">{e['name']}</div>
      <div class="tdh-meta">
        <div><span class="lbl">创建人:</span><span class="val">{owner}</span></div>
        <div><span class="lbl">创建时间:</span><span class="val">{e['started']}</span></div>
      </div>
    </div>

    <div class="det-tabs">
      <span class="det-tab active" onclick="switchDetTab(this,'trials')">运行记录</span>
      <span class="det-tab" onclick="switchDetTab(this,'data')">实验看板</span>
      <span class="det-tab" onclick="switchDetTab(this,'lineage')">血缘</span>
      <span class="det-tab" onclick="switchDetTab(this,'basic')">基础信息</span>
    </div>

    <div id="det-pane-trials"  class="det-pane active">{pane_trials}</div>
    <div id="det-pane-data"    class="det-pane">{tab_data}</div>
    <div id="det-pane-lineage" class="det-pane">{tab_lineage}</div>
    <div id="det-pane-basic"   class="det-pane">{tab_basic}</div>
    """
    return render_page(e["name"], content, active="/model/experiments", module="model",
                       breadcrumb=f'模型平台 / 训练任务 / <b>{e["name"]}</b>', mvp_note="MVP 一期")


@app.route("/model/deploy")
def deploy():
    rows = ""
    for d in DEPLOYS:
        n = len(d["targets"])
        devs_links = "".join(
            f'<a href="/device/devices">{tgt}<span class="arr">&rsaquo;</span></a>'
            for tgt in d["targets"]
        )
        targets_cell = (
            f'<div class="devs-cell">'
            f'<span class="devs-pill" onclick="toggleDevsPop(this, event)">{n} 台设备 <span class="ca">&#9662;</span></span>'
            f'<div class="devs-pop">{devs_links}</div>'
            f'</div>'
        )
        rows += f"""<tr>
          <td class="mono">{d['id']}</td>
          <td><b>{d['model']}</b></td>
          <td class="mono">{d['version']}</td>
          <td>{targets_cell}</td>
          <td>{status_tag(d['status'])}</td>
          <td>{d['operator']}</td>
          <td class="muted mono">{d['at']}</td>
          <td class="actions-cell"><a href="#" onclick="toast('Demo: 查看部署日志');return false;">日志</a></td>
        </tr>"""
    content = page_header(
        "部署任务",
        "模型下发到指定设备 · 状态 + 操作历史",
        "灰度发布 · 回滚 · OTA 兼容性矩阵",
    ) + f"""
    <div class="filter-bar">
      <input class="grow" placeholder="搜索模型 / 设备...">
      <select><option>全部状态</option><option>已部署</option><option>待启动</option></select>
      <div class="right">
        <a href="#" class="btn" onclick="openDrawer('drawerDeploy');return false;">+ 新部署</a>
      </div>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>ID</th><th>模型</th><th>版本</th><th>目标设备</th><th>状态</th><th>操作人</th><th>完成时间</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <div class="drawer" id="drawerDeploy">
      <div class="drawer-head"><h3>新建部署</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
      <div class="drawer-body">
        <div class="fg"><label>模型</label><select>{''.join(f'<option>{m["name"]}</option>' for m in MODELS)}</select></div>
        <div class="fg"><label>版本</label><select><option>v1.7.1</option><option>v1.7.0</option><option>v1.6.0</option></select></div>
        <div class="fg">
          <label>目标设备（可多选）</label>
          <div style="border:1px solid #d9d9d9;border-radius:8px;padding:8px 12px;max-height:200px;overflow-y:auto;">
            {''.join(f'<label style="display:flex;align-items:center;gap:8px;padding:5px 0;font-size:13px;cursor:pointer;"><input type="checkbox" value="{d["id"]}" style="accent-color:#149DAA;"><span class="mono">{d["id"]}</span><span class="muted" style="font-size:12px;">{d["location"]}</span></label>' for d in DEVICES if d["status"] != "offline")}
          </div>
        </div>
        <div class="fg"><label>转换格式</label><select><option>onnx</option><option>tensorrt</option><option>原生</option></select></div>
        <div class="fg"><label>量化</label><select><option>fp16</option><option>int8</option><option>无</option></select></div>
        <div class="muted" style="font-size:12px;margin-top:6px;">一期: 直接下发到指定设备 (不含灰度 / 回滚)</div>
      </div>
      <div class="drawer-foot">
        <button class="btn" onclick="closeDrawer()">取消</button>
        <button class="btn btn-primary" onclick="toast('Demo: 部署已下发 → 设备平台 OTA 执行');closeDrawer()">下发</button>
      </div>
    </div>
    """
    return render_page("部署", content, active="/model/deploy", module="model",
                       breadcrumb='模型平台 / <b>部署</b>', mvp_note="MVP 一期")


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
    "cached":       '<span class="tag tag-green">已缓存</span>',
    "not_cached":   '<span class="tag tag-gray">未缓存</span>',
    "merge_failed": '<span class="tag tag-red">合并失败</span>',
}


@app.route("/model/checkpoints")
def checkpoints():
    # 模拟: 部分 ckpt 已被注册到模型仓库 (mock 数据: 前 2 个已注册)
    _registered_ids = {"7916", "7560"}
    rows = ""
    for c in CHECKPOINTS:
        reg_btn = (
            '<span class="tbtn" style="background:#f5f5f5;color:rgba(0,0,0,0.45);border-color:#e8e8e8;cursor:default;">已注册</span>'
            if c["id"] in _registered_ids
            else f'<a class="tbtn" href="#" onclick="openRegisterCkpt(\'{c["id"]}\', \'{c["name"]}\', \'{c["owner"]}\');return false;">注册到仓库</a>'
        )
        rows += f"""<tr>
          <td class="mono">{c['id']}</td>
          <td><a href="#" style="color:#149DAA" onclick="toast('Demo: 查看 ckpt 详情');return false;">{c['name']}</a></td>
          <td>{CKPT_STATUS_LABEL.get(c['status'], c['status'])}</td>
          <td>{c['owner']}</td>
          <td class="muted mono">{c['created']}</td>
          <td class="actions-cell">
            <a class="tbtn" href="#" onclick="toast('Demo: 发起 TEST');return false;">TEST</a>
            <a class="tbtn" href="#" onclick="toast('Demo: 发起 DAGGER');return false;">DAGGER</a>
            {reg_btn}
          </td>
        </tr>"""

    content = page_header(
        "Checkpoint",
        "跨任务 checkpoint 浏览 · 状态 / 缓存 / 续训",
        "自动保留策略 · 远程同步 · 自动分支评测",
    ) + f"""
    <div class="fb-labeled">
      <div class="ff"><label>名称</label><input placeholder="请输入名称"></div>
      <div class="ff"><label>ID</label><input placeholder="请输入ID"></div>
      <button class="ff-refresh" onclick="toast('Demo: 已刷新')" title="刷新">&#8635;</button>
    </div>

    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr>
          <th>ID</th>
          <th>名称</th>
          <th>状态 &#9662;</th>
          <th>创建人</th>
          <th>创建时间 &#x21F5;</th>
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
      <span class="pg-btn">13</span>
      <span class="pg-btn">&rsaquo;</span>
      <input class="pg-goto" placeholder=""><span class="pg-go">go</span>
    </div>

    <div class="drawer" id="drawerRegister">
      <div class="drawer-head"><h3>注册到模型仓库</h3><span class="dismiss" onclick="closeDrawer()">&times;</span></div>
      <div class="drawer-body">
        <div class="fg">
          <label>来源 Checkpoint</label>
          <div style="background:#fafbfc;border:1px solid #f0f0f0;border-radius:6px;padding:10px 12px;font-family:'SF Mono',Menlo,monospace;font-size:12.5px;">
            <div style="color:rgba(0,0,0,0.85);"><b id="regCkptName">—</b></div>
            <div style="margin-top:4px;color:rgba(0,0,0,0.45);font-size:11.5px;">ID: <span id="regCkptId">—</span> · 训练人: <span id="regCkptOwner">—</span></div>
          </div>
        </div>
        <div class="fg"><label class="fg-req">模型名称</label><input id="regModelName" placeholder="如: spirit-v1.7-whiteboard-base"></div>
        <div class="fg-row">
          <div class="fg"><label class="fg-req">版本号</label><input value="v1.0.0" placeholder="语义化版本"></div>
          <div class="fg"><label>基础模型</label>
            <select>
              <option>Spirit v1.7</option>
              <option>Spirit v1.7-SFT</option>
              <option>Spirit v1.6</option>
            </select>
          </div>
        </div>
        <div class="fg"><label>标签</label><input placeholder="逗号分隔: production, baseline"></div>
        <div class="fg"><label>发布描述</label><textarea rows="3" placeholder="该版本相比上版的改进 / 注意事项..."></textarea></div>
        <div class="muted" style="font-size:12px;margin-top:6px;">注册后会自动写入血缘 (数据集 → 训练任务 → ckpt → 模型版本)</div>
      </div>
      <div class="drawer-foot">
        <button class="btn" onclick="closeDrawer()">取消</button>
        <button class="btn btn-primary" onclick="toast('Demo: 已注册到模型仓库');closeDrawer()">注册</button>
      </div>
    </div>
    """
    extra_script = """<script>
    function openRegisterCkpt(id, name, owner){
      document.getElementById('regCkptId').textContent = id;
      document.getElementById('regCkptName').textContent = name;
      document.getElementById('regCkptOwner').textContent = owner;
      // 默认拿 ckpt 名第一段做模型名预填
      var seg = (name || '').split('_')[0] || '';
      var nameInput = document.getElementById('regModelName');
      if (nameInput && !nameInput.value) nameInput.value = seg.toLowerCase();
      openDrawer('drawerRegister');
    }
    </script>"""
    return render_page("Checkpoint", content, active="/model/checkpoints", module="model",
                       breadcrumb='模型平台 / <b>Checkpoint</b>', mvp_note="MVP 一期",
                       extra_script=extra_script)


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
# Section 8: 设备平台 (/device/*)
# ════════════════════════════════════════════════════════════════

@app.route("/device")
def device_home():
    # 概览页已下线, 默认落到「设备管理」菜单
    return redirect("/device/devices")


@app.route("/device/devices")
def devices_list():
    rows = ""
    for d in DEVICES:
        # 「占用中」枚举合并为「在线」, 只渲染 online / offline
        eff_status = "online" if d["status"] in ("online", "in_use") else d["status"]
        rows += f"""<tr>
          <td class="mono">{d['id']}</td>
          <td>{status_tag(eff_status)}</td>
          <td>{d['location']}</td>
          <td class="mono" style="font-size:12.5px;line-height:1.5;">{d['sw_dep']}</td>
          <td class="mono" style="font-size:12.5px;line-height:1.5;">{d['hw_dep']}</td>
          <td class="mono">{d['model']}</td>
          <td class="muted mono">{d['last_seen']}</td>
          <td class="actions-cell"><a href="/device/booking?device={d['id']}">预约</a></td>
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
      <input class="grow" placeholder="搜索设备 ID / 位置...">
      <select><option>全部状态</option><option>在线</option><option>离线</option></select>
    </div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>ID</th><th>状态</th><th>位置</th><th>软件依赖</th><th>硬件依赖</th><th>当前模型</th><th>最后心跳</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
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


def _lineage_flow_html(selected):
    """给定模型 dict, 生成 4 列血缘流图 HTML (采集任务 → 数据集 → 实验/模型 → 部署设备)."""
    ds = next((d for d in DATASETS if d["name"] == selected["from_dataset"]), None)
    src_tasks_html = ""
    if ds:
        for tn in ds["source_tasks"]:
            tk = next((c for c in COLLECT_TASKS if c["name"] == tn), None)
            if tk:
                src_tasks_html += f'<div class="lin-node teal"><div class="ln-ttl">{tk["name"]}</div><div class="ln-meta">{tk["current"]} EP · {tk["scene"]} · {tk["robot"]}</div></div>'
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


# ════════════════════════════════════════════════════════════════
# Section 10: Main
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    print(f"\n  具身云 · 工具链 MVP Demo — http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
