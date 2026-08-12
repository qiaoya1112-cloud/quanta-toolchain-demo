"""
具身数据管理平台 - Demo Version
Embodied Data Management Platform (interactive prototype)

Framework: Flask + HTML/CSS (inline templates), Ant Design v4 theme (primary #1F80A0)
参考「Quanta 双盲评测平台」的代码规则与样式规则编写。这是交互演示 demo,非生产级应用。

三大模块:
  一、数据湖        (recording 级原料池, 左树右Tab)
  二、数据集        (生成+管理, 左树右Tab, 新建走列表按钮)
  三、自动化任务    (算子广场 / 任务编排 / 任务执行)

Usage:
  pip install flask
  python3 data_platform.py
  # Open http://localhost:5002
"""

import os
import json
import datetime
import re
import html
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
app.secret_key = "embodied-data-platform-demo"

# ════════════════════════════════════════════════════════════════
# Section 1: Mock Data
# ════════════════════════════════════════════════════════════════

# —— 数据湖: recording 级原料 (按 task 聚合) ——
TASKS = [
    {"id": "t1", "name": "clean_the_whiteboard", "zh": "擦白板"},
    {"id": "t2", "name": "tidy_the_desk", "zh": "整理桌面"},
    {"id": "t3", "name": "water_the_plant", "zh": "浇花"},
]

# recording: 1 条采集 ≈ 1 episode (parquet + 3 路 mp4)
RECORDINGS = [
    # task t1
    {"id": 120489, "task": "t1", "collection": 3635, "robot": "moz1", "type": "采集", "frames": 1434, "fps": 30, "dur": 47.8, "at": "2026-05-21 10:12", "qa": "pass", "life": "active"},
    {"id": 120502, "task": "t1", "collection": 3635, "robot": "moz1", "type": "采集", "frames": 1042, "fps": 30, "dur": 34.7, "at": "2026-05-21 10:31", "qa": "pass", "life": "active"},
    {"id": 120513, "task": "t1", "collection": 3635, "robot": "moz1", "type": "采集", "frames": 979, "fps": 30, "dur": 32.6, "at": "2026-05-21 10:48", "qa": "warn", "life": "active"},
    {"id": 120521, "task": "t1", "collection": 3653, "robot": "moz1", "type": "dagger", "frames": 56, "fps": 30, "dur": 1.9, "at": "2026-05-22 09:05", "qa": "fail", "life": "quarantined"},
    {"id": 120532, "task": "t1", "collection": 3653, "robot": "moz1", "type": "采集", "frames": 1310, "fps": 30, "dur": 43.7, "at": "2026-05-22 09:24", "qa": "pass", "life": "active"},
    # task t2
    {"id": 121005, "task": "t2", "collection": 3702, "robot": "moz1", "type": "采集", "frames": 1188, "fps": 30, "dur": 39.6, "at": "2026-05-24 14:02", "qa": "pass", "life": "active"},
    {"id": 121014, "task": "t2", "collection": 3702, "robot": "moz1", "type": "采集", "frames": 1402, "fps": 30, "dur": 46.7, "at": "2026-05-24 14:20", "qa": "pass", "life": "active"},
    {"id": 121023, "task": "t2", "collection": 3702, "robot": "moz1", "type": "test", "frames": 905, "fps": 30, "dur": 30.2, "at": "2026-05-24 14:39", "qa": "warn", "life": "active"},
    # task t3
    {"id": 121120, "task": "t3", "collection": 3760, "robot": "moz1", "type": "采集", "frames": 1521, "fps": 30, "dur": 50.7, "at": "2026-05-27 11:10", "qa": "pass", "life": "active"},
    {"id": 121131, "task": "t3", "collection": 3760, "robot": "moz1", "type": "采集", "frames": 1098, "fps": 30, "dur": 36.6, "at": "2026-05-27 11:28", "qa": "pass", "life": "active"},
]

CAMERAS = ["cam_high", "cam_left_wrist", "cam_right_wrist"]
# 14 维双臂特征 (左臂7 + 右臂7), 用于轨迹预览曲线分组
ARM_DIMS = {
    "左臂关节 (leftarm_state/cmd_joint_pos)": ["joint0", "joint1", "joint2", "joint3", "joint4", "joint5", "joint6"],
    "右臂关节 (rightarm_state/cmd_joint_pos)": ["joint0", "joint1", "joint2", "joint3", "joint4", "joint5", "joint6"],
    "夹爪 (gripper_cmd/state_pos)": ["left_gripper", "right_gripper"],
}

# —— episode 标签体系 (场景 / 技能 / 质量) ——
TAG_DEFS = [
    ("sc_whiteboard", "白板区", "场景"), ("sc_desk", "桌面", "场景"), ("sc_plant", "绿植区", "场景"),
    ("sk_wipe", "擦拭", "技能"), ("sk_pick", "抓取", "技能"), ("sk_place", "放置", "技能"), ("sk_pour", "倒水", "技能"),
    ("q_high", "高质量", "质量"), ("q_review", "待复核", "质量"),
]
TAG_LABEL = {tid: lab for tid, lab, grp in TAG_DEFS}
TAG_GROUP_ORDER = ["场景", "技能", "质量"]
TASK_TAGS = {
    "t1": ["sc_whiteboard", "sk_wipe"],
    "t2": ["sc_desk", "sk_pick", "sk_place"],
    "t3": ["sc_plant", "sk_pour", "sk_pick"],
}

# 数据集标签统一使用完整层级路径展示，避免多个级联下拉框割裂选择结果。
DATASET_TAG_PATH_BY_ID = {
    "sc_whiteboard": "场景标签 > 作业区域 > 白板区",
    "sc_desk": "场景标签 > 作业区域 > 桌面",
    "sc_plant": "场景标签 > 作业区域 > 绿植区",
    "sk_wipe": "动作标签 > 清洁类 > 擦拭",
    "sk_pick": "动作标签 > 拿放类 > 拿取",
    "sk_place": "动作标签 > 拿放类 > 放置",
    "sk_pour": "动作标签 > 操作类 > 倾倒",
    "q_high": "质量标签 > 数据质量 > 高质量",
    "q_review": "质量标签 > 数据质量 > 待复核",
}
DATASET_TAG_PATH_OPTIONS = [
    "能力标签 > 方位理解 > 左右",
    "能力标签 > 方位理解 > 前后",
    "能力标签 > 动作理解",
    "动作标签 > 拿放类 > 拿取",
    "动作标签 > 拿放类 > 放置",
    "动作标签 > 清洁类 > 擦拭",
    "动作标签 > 操作类 > 倾倒",
    "场景标签 > 作业区域 > 白板区",
    "场景标签 > 作业区域 > 桌面",
    "场景标签 > 作业区域 > 绿植区",
    "质量标签 > 数据质量 > 高质量",
    "质量标签 > 数据质量 > 待复核",
]

def rec_tags(r):
    """每条 recording(=episode) 的标签: 场景+技能(按 task) + 质量(按质检)。"""
    tags = list(TASK_TAGS.get(r["task"], []))
    tags.append("q_high" if r["qa"] == "pass" else "q_review")
    return tags

def rec_tag_labels(r):
    return [TAG_LABEL[t] for t in rec_tags(r)]

# —— 标签体系 (标签管理页) ——
TAG_SYSTEM = {
    "version": "1.0.0",
    "dimensions": [
        {"name": "动作标签", "en": "Action Tags", "desc": "机器人可执行的原子动作", "leaves": [
            "拿取", "放置", "放入", "取出", "抽出", "取下", "捡起", "靠放", "放倒", "立起", "叠放", "扔", "递送", "换持",
            "移动", "拖拽", "推动", "拉动", "旋转", "翻转", "复位", "交换", "折叠", "展开", "平铺", "撑开", "抚平", "拉直",
            "卷", "挤", "拧干", "打结", "打开", "关闭", "拉开", "推开", "翻开", "掀起", "拧开", "拉上", "合上", "拆分",
            "安装", "插入", "扣紧", "拧紧", "组装", "贴", "揭下", "倒", "搅拌", "翻炒", "刮", "切", "剥", "撕", "泡", "撒",
            "盖", "穿戴", "套", "包裹", "浇水", "磨", "铲", "质检", "冲洗", "刷洗", "搓洗", "擦拭", "扫", "清理", "启动",
            "按压", "拨动", "调整", "整理", "收纳", "抖动", "拍打", "悬挂", "书写"]},
        {"name": "场景标签", "en": "Scene Tags", "desc": "采集/任务所处场景", "leaves": [
            "厨房", "客厅", "卧室", "书房", "餐厅", "卫生间", "阳台", "玄关"]},
        {"name": "物体标签", "en": "Object Tags", "desc": "操作对象的物体分类", "groups": [
            {"category": "包装类", "items": ["包装袋", "包装盒", "湿巾包装袋", "酒精棉片包装袋", "塑料袋", "纸盒", "纸袋", "礼品盒", "快递盒", "泡沫盒", "保鲜袋", "密封袋"]},
            {"category": "容器类", "items": ["塑料杯", "陶瓷杯", "玻璃杯", "马克杯", "保温杯", "纸杯", "编织篮", "收纳篮", "托盘", "餐盘", "碗", "碟子", "盒子", "罐子", "瓶子", "水壶", "茶壶", "花瓶", "垃圾桶", "收纳盒"]},
            {"category": "工具类", "items": ["剪刀", "螺丝刀", "钳子", "扳手", "笔", "铅笔", "记号笔", "刷子", "夹子", "订书机", "胶带", "胶水", "尺子", "美工刀", "锤子", "起子", "镊子", "量杯", "漏斗"]},
            {"category": "布料类", "items": ["布块", "毛巾", "抹布", "垫子", "桌垫", "餐巾", "手帕", "围裙", "袖套", "地毯", "窗帘", "床单", "枕套", "被套", "衣服", "T恤", "裤子", "袜子", "手套"]},
            {"category": "机械类", "items": ["机械臂", "金属架", "链条", "齿轮", "螺丝", "螺母", "弹簧", "轴承", "电机", "传感器", "电路板", "导线", "插头", "开关", "按钮"]},
            {"category": "日用品", "items": ["钥匙串", "挂绳", "雨伞", "鞋子", "皮鞋", "运动鞋", "拖鞋", "皮带", "钱包", "手表", "眼镜", "手机", "充电器", "耳机", "遥控器", "电池", "灯泡", "蜡烛", "香皂", "洗发水", "牙刷", "牙膏", "梳子", "镜子"]},
            {"category": "食物类", "items": ["面包", "芝士片", "水果", "苹果", "香蕉", "橙子", "葡萄", "蔬菜", "番茄", "黄瓜", "胡萝卜", "土豆", "肉类", "鸡肉", "牛肉", "鱼", "虾", "鱼豆腐", "木签", "饼干", "蛋糕", "糖果", "巧克力", "薯片", "坚果", "饮料", "牛奶", "果汁"]},
            {"category": "文具类", "items": ["书本", "笔记本", "文件夹", "信封", "便签", "回形针", "图钉", "橡皮", "修正带", "计算器", "印章", "名片", "卡片"]},
            {"category": "厨房用品", "items": ["锅", "平底锅", "炒锅", "汤锅", "刀", "菜刀", "水果刀", "砧板", "筷子", "勺子", "叉子", "铲子", "漏勺", "打蛋器", "开瓶器", "保鲜膜", "锡纸", "烤盘", "微波炉盒"]},
            {"category": "电子产品", "items": ["手机", "平板", "笔记本电脑", "键盘", "鼠标", "U盘", "硬盘", "相机", "音箱", "耳机", "充电宝", "数据线", "适配器"]},
            {"category": "玩具类", "items": ["积木", "拼图", "玩偶", "毛绒玩具", "小汽车", "球", "魔方", "飞盘", "风筝", "气球"]},
            {"category": "办公用品", "items": ["文件", "文件夹", "档案袋", "打印纸", "复印纸", "标签", "胶带座", "笔筒", "名片夹", "证件", "工牌"]},
        ]},
    ],
}

# —— 数据集管理: 业务语义目录 (用户可自建管理) ——
V2_FOLDERS = ["预训练", "后训练", "自定义01", "自定义02"]
V2_FOLDER_MAP = {
    "预训练": ["ds1", "ds4", "ds5", "ds6"],
    "后训练": ["ds2", "ds7", "ds8", "ds9"],
    "自定义01": ["ds3", "ds10"],
    "自定义02": ["ds11", "ds12"],
}

# —— 数据集: 生成成品 ——
DATASETS = [
    {
        "id": "ds1", "name": "clean_whiteboard_v3", "version": "v3", "type": "train",
        "robot": "moz1", "fps": 30, "episodes": 48, "frames": 52310, "quality": "pass",
        "status": "生效中", "tos": "tos://embodied/datasets/clean_whiteboard_v3/",
        "created": "2026-05-28 16:40", "owner": "joanna.qiao",
        "recordings": [120489, 120502, 120532], "tasks": ["t1"],
        "recipe": {"groups": [{"name": "擦白板-采集", "weight": 1.0, "frames": 52310, "ratio": 1.0}], "alpha": 0.6, "train_ratio": 0.95, "seed": 42},
        "src": "采集任务 #3635 / #3653", "used_by": ["train_job_0421 (Spirit v1.6-beta)", "train_job_0455 (Spirit v1.6-rc1)"],
    },
    {
        "id": "ds2", "name": "tidy_desk_mix_v1", "version": "v1", "type": "train",
        "robot": "moz1", "fps": 30, "episodes": 36, "frames": 41880, "quality": "warn",
        "status": "待发布", "tos": "—",
        "created": "2026-06-01 09:15", "owner": "joanna.qiao",
        "recordings": [121005, 121014], "tasks": ["t2"],
        "recipe": {"groups": [{"name": "整理桌面-采集", "weight": 0.7, "frames": 29300, "ratio": 0.7}, {"name": "整理桌面-dagger", "weight": 0.3, "frames": 12580, "ratio": 0.3}], "alpha": 0.6, "train_ratio": 0.9, "seed": 7},
        "src": "采集任务 #3702", "used_by": [],
    },
    {
        "id": "ds3", "name": "whiteboard_eval_bench", "version": "v1", "type": "eval-benchmark",
        "robot": "moz1", "fps": 30, "episodes": 12, "frames": 13200, "quality": "pass",
        "status": "生效中", "tos": "tos://embodied/datasets/whiteboard_eval_bench/",
        "created": "2026-05-30 18:02", "owner": "joanna.qiao",
        "recordings": [120513], "tasks": ["t1"],
        "recipe": {"groups": [{"name": "擦白板-留出评测", "weight": 1.0, "frames": 13200, "ratio": 1.0}], "alpha": 1.0, "train_ratio": 0.0, "seed": 42},
        "src": "专用评测采集 #3653", "used_by": ["eval_job_0510 (双盲评测)"],
    },
    {"id": "ds4", "name": "whiteboard_pretrain_mix", "version": "v2", "type": "train", "robot": "moz1", "fps": 30,
     "episodes": 52, "frames": 56800, "quality": "pass", "status": "生效中", "tos": "tos://embodied/datasets/whiteboard_pretrain_mix/",
     "created": "2026-05-26 14:10", "owner": "Lance Li", "recordings": [120489, 120502, 120532], "tasks": ["t1"],
     "recipe": {"groups": [{"name": "擦白板-采集", "weight": 1.0, "frames": 56800, "ratio": 1.0}], "alpha": 0.6, "train_ratio": 0.95, "seed": 42},
     "src": "采集任务 #3635 / #3653", "used_by": ["train_job_0388 (Spirit v1.5)"]},
    {"id": "ds5", "name": "desk_pretrain", "version": "v1", "type": "train", "robot": "moz1", "fps": 30,
     "episodes": 30, "frames": 35200, "quality": "warn", "status": "待发布", "tos": "—",
     "created": "2026-05-29 11:42", "owner": "Wei Zhang", "recordings": [121005, 121014], "tasks": ["t2"],
     "recipe": {"groups": [{"name": "整理桌面-采集", "weight": 1.0, "frames": 35200, "ratio": 1.0}], "alpha": 0.6, "train_ratio": 0.95, "seed": 1},
     "src": "采集任务 #3702", "used_by": []},
    {"id": "ds6", "name": "plant_pour_pretrain", "version": "v1", "type": "train", "robot": "moz1", "fps": 30,
     "episodes": 26, "frames": 31900, "quality": "pass", "status": "生效中", "tos": "tos://embodied/datasets/plant_pour_pretrain/",
     "created": "2026-05-31 09:20", "owner": "Min Chen", "recordings": [121120, 121131], "tasks": ["t3"],
     "recipe": {"groups": [{"name": "浇花-采集", "weight": 1.0, "frames": 31900, "ratio": 1.0}], "alpha": 0.6, "train_ratio": 0.95, "seed": 3},
     "src": "采集任务 #3760", "used_by": []},
    {"id": "ds7", "name": "whiteboard_sft", "version": "v1", "type": "train", "robot": "moz1", "fps": 30,
     "episodes": 24, "frames": 26400, "quality": "pass", "status": "生效中", "tos": "tos://embodied/datasets/whiteboard_sft/",
     "created": "2026-06-02 16:05", "owner": "joanna.qiao", "recordings": [120513, 120532], "tasks": ["t1"],
     "recipe": {"groups": [{"name": "擦白板-精选", "weight": 1.0, "frames": 26400, "ratio": 1.0}], "alpha": 0.8, "train_ratio": 0.95, "seed": 42},
     "src": "采集任务 #3653", "used_by": ["train_job_0461 (Spirit v1.6-rc1)"]},
    {"id": "ds8", "name": "desk_dagger_sft", "version": "v1", "type": "train", "robot": "moz1", "fps": 30,
     "episodes": 18, "frames": 19800, "quality": "warn", "status": "待发布", "tos": "—",
     "created": "2026-06-03 10:30", "owner": "Wei Zhang", "recordings": [121023], "tasks": ["t2"],
     "recipe": {"groups": [{"name": "整理桌面-dagger", "weight": 1.0, "frames": 19800, "ratio": 1.0}], "alpha": 0.8, "train_ratio": 0.9, "seed": 11},
     "src": "DAgger 采集 #3702", "used_by": []},
    {"id": "ds9", "name": "mix_finetune", "version": "v2", "type": "train", "robot": "moz1", "fps": 30,
     "episodes": 40, "frames": 44200, "quality": "pass", "status": "生效中", "tos": "tos://embodied/datasets/mix_finetune/",
     "created": "2026-06-03 19:50", "owner": "joanna.qiao", "recordings": [120489, 121005], "tasks": ["t1", "t2"],
     "recipe": {"groups": [{"name": "擦白板", "weight": 0.5, "frames": 22100, "ratio": 0.5}, {"name": "整理桌面", "weight": 0.5, "frames": 22100, "ratio": 0.5}], "alpha": 0.6, "train_ratio": 0.95, "seed": 42},
     "src": "采集任务 #3635 / #3702", "used_by": ["train_job_0470 (Spirit v1.6-rc1)"]},
    {"id": "ds10", "name": "custom_eval_set", "version": "v1", "type": "eval-benchmark", "robot": "moz1", "fps": 30,
     "episodes": 10, "frames": 11000, "quality": "pass", "status": "生效中", "tos": "tos://embodied/datasets/custom_eval_set/",
     "created": "2026-06-01 13:00", "owner": "Min Chen", "recordings": [121131], "tasks": ["t3"],
     "recipe": {"groups": [{"name": "浇花-留出评测", "weight": 1.0, "frames": 11000, "ratio": 1.0}], "alpha": 1.0, "train_ratio": 0.0, "seed": 42},
     "src": "专用评测采集 #3760", "used_by": ["eval_job_0521 (双盲评测)"]},
    {"id": "ds11", "name": "ablation_small", "version": "v1", "type": "train", "robot": "moz1", "fps": 30,
     "episodes": 8, "frames": 8800, "quality": "warn", "status": "待发布", "tos": "—",
     "created": "2026-06-04 08:15", "owner": "Lance Li", "recordings": [120502], "tasks": ["t1"],
     "recipe": {"groups": [{"name": "擦白板-小样本", "weight": 1.0, "frames": 8800, "ratio": 1.0}], "alpha": 0.6, "train_ratio": 0.9, "seed": 99},
     "src": "采集任务 #3635", "used_by": []},
    {"id": "ds12", "name": "smoke_test", "version": "v1", "type": "train", "robot": "moz1", "fps": 30,
     "episodes": 6, "frames": 6600, "quality": "pass", "status": "生效中", "tos": "tos://embodied/datasets/smoke_test/",
     "created": "2026-06-04 09:02", "owner": "joanna.qiao", "recordings": [121014], "tasks": ["t2"],
     "recipe": {"groups": [{"name": "整理桌面-冒烟", "weight": 1.0, "frames": 6600, "ratio": 1.0}], "alpha": 0.6, "train_ratio": 0.95, "seed": 5},
     "src": "采集任务 #3702", "used_by": []},
]

# DOCTOR 质检检查项 (复用 episode_stats / check 脚本逻辑)
def doctor_checks(quality):
    base = [
        ("Metadata & Format Compliance", "pass", "info.json / 字段 schema 校验通过"),
        ("Temporal Consistency", "pass", "时间戳单调, 无跳变"),
        ("Frame Integrity (掉帧)", "pass", "meta 帧数 = parquet 行数 (check_evalset_split)"),
        ("Frozen Action (冻结动作)", "pass", "无某维 std≈0 (psi 维已知全 0, 已豁免)"),
        ("Camera Resolution", "pass", "三路相机均 240×320 一致"),
        ("Annotation 合规 (中文混入)", "pass", "tasks.jsonl 无中文混入 (check_chinese)"),
    ]
    if quality == "warn":
        base[3] = ("Frozen Action (冻结动作)", "warn", "2 个 episode 右臂全程 std≈0, 疑似静止, 建议复核")
        base[2] = ("Frame Integrity (掉帧)", "warn", "1 个 episode meta 1402 / parquet 1399, 缺 3 帧")
    if quality == "fail":
        base[2] = ("Frame Integrity (掉帧)", "fail", "缺帧严重, 必须修复")
    return base

# —— 自动化任务: 算子 / 编排 / 执行 ——
# 算子 = frontdesk_scripts 里一个「原子处理能力」的封装 (调度类 .sh 不作算子, 归任务编排)
OPERATORS = [
    # 切分
    {"id": "op_split", "name": "切分 Split", "ident": "batch_split", "script": "batch_split_datasets.py", "cat": "切分", "creator": "joanna.qiao",
     "desc": "把数据集随机切 train/val: 按 train_ratio 划分 episode → 重编号 → 改写 meta(info/episodes/stats) → 输出 _split/train、_split/val 及清单 JSON",
     "params": "--train-ratio 0.95 / --seed 42 / --force",
     "returns": "_split/train、_split/val + xxx_train.json / xxx_val.json 清单",
     "io_in": "LeRobot 数据集 + 权重清单 JSON", "io_out": "train/val 数据集 + 清单"},
    # 配方
    {"id": "op_sample", "name": "采样配比 Sampling", "ident": "adjust_sampling", "script": "adjust_sampling_ratio.py", "cat": "配方", "creator": "Wei Zhang",
     "desc": "采样比例核心算法: 读权重 JSON + 各数据集帧数 → GROUP_RULES 分组 → GROUP_CONFIG 设占比 → power-law(alpha) 组内分配 → 写回采样权重",
     "params": "INPUT_JSON / GROUP_RULES / GROUP_CONFIG",
     "returns": "{数据集: 调整后采样权重} JSON",
     "io_in": "{数据集: 权重} JSON", "io_out": "{数据集: 采样权重} JSON"},
    {"id": "op_sample_verify", "name": "采样验证 Validate", "ident": "analyze_sampling", "script": "analyze_sampling_frames.py", "cat": "配方", "creator": "Wei Zhang",
     "desc": "采样配套验证: 算「权重占比 vs 帧数占比 vs 实际采样帧数占比」, 按主类别/组/子类别多维汇总 → 打印 + 导出 CSV",
     "params": "CONFIG_JSON / OUTPUT_CSV / GROUP_RULES",
     "returns": "占比对比 CSV (权重/帧数/实际采样)",
     "io_in": "{数据集: 权重} JSON", "io_out": "占比对比 CSV"},
    # 统计
    {"id": "op_stats", "name": "统计 Statistics", "ident": "dataset_stats", "script": "dataset_statistics.py", "cat": "统计", "creator": "Min Chen",
     "desc": "全面统计: 扫 parquet 统计每 task_folder 总帧数、每 prompt 帧数占比+recording 列表、换算时长 → 详细 CSV + 汇总 CSV",
     "params": "--input / --output / --summary",
     "returns": "详细 CSV + 汇总 CSV",
     "io_in": "{数据集: 权重} JSON", "io_out": "统计 CSV"},
    # 质检
    {"id": "op_check_chinese", "name": "中文标注质检", "ident": "check_chinese", "script": "check_chinese.py", "cat": "质检", "creator": "joanna.qiao",
     "desc": "扫各数据集 tasks.jsonl, 用正则查英文标注里混入的中文, 报告 + 导出 JSON (退出码区分有无中文)",
     "params": "input_json / -v / --export",
     "returns": "含中文的数据集报告 JSON + 退出码(0/1/2)",
     "io_in": "LeRobot 数据集 (tasks.jsonl)", "io_out": "质检报告 JSON"},
    {"id": "op_check_evalset", "name": "完整性质检", "ident": "check_evalset", "script": "check_evalset_split.py", "cat": "质检", "creator": "Min Chen",
     "desc": "对比每个数据集 episodes.jsonl 记录帧数 vs 实际 parquet 行数, 查数据完整性 / 缺帧",
     "params": "input_json",
     "returns": "一致性报告: 已检查/跳过数 + 缺帧数据集列表",
     "io_in": "LeRobot 数据集 (episodes.jsonl + parquet)", "io_out": "完整性报告"},
]

# 算子管理中实际维护、允许数据处理流程绑定的算子。
MANAGED_OPERATORS = [
    {
        "id": "op_e2e_segment_annotation",
        "name": "端到端切分标注处理算子",
        "ident": "e2e_segment_annotation",
        "script": "e2e_segment_annotation.py",
        "cat": "标注",
        "creator": "joanna.qiao",
        "desc": "完成端到端数据切分、动作片段标注与结构化结果输出。",
        "params": "--recording-id / --flow-version / --annotation-schema",
        "returns": "切分片段、动作标注与处理结果 JSON",
    }
]

PIPELINES = [
    {"id": "pl1", "name": "标准训练数据流水线", "creator": "joanna.qiao", "status": "已保存", "updated": "2026-06-03 18:22",
     "stages": ["op_split", "op_sample", "op_sample_verify", "op_check_evalset", "op_check_chinese"],
     "schedules": ["每天 02:00", "每周一 06:00"],
     "desc": "导出 → 切分 → 配比 → 采样验证 → 完整性质检 → 中文质检, 一键生成训练就绪数据集"},
    {"id": "pl2", "name": "DAgger 数据流水线", "creator": "Wei Zhang", "status": "已保存", "updated": "2026-06-02 10:05",
     "stages": ["op_check_evalset", "op_stats"],
     "schedules": ["每天 22:00"],
     "desc": "DAgger 导出 → 完整性质检 → 统计"},
    {
        "id": "pl3",
        "name": "多级复核数据处理流程",
        "creator": "joanna.qiao",
        "status": "已保存",
        "updated": "2026-07-27 15:20",
        "stages": [],
        "schedules": [],
        "phase_count": 3,
        "node_count": 8,
        "desc": "自动质检、抽检、供应商复核、申诉复核、端到端切分、双轮标注复核与验收。",
        "phases": [
            {
                "name": "数据质检环节",
                "short_name": "质检环节",
                "desc": "含人工与自动化节点，人工节点支持多轮和驳回",
                "nodes": [
                    {"name": "自动化质检", "kind": "automatic", "meta": "自动化节点"},
                    {"name": "不合格 100% 等", "kind": "condition", "meta": "条件 · 比例"},
                    {"name": "抽检复核", "kind": "human", "meta": "人工复核"},
                    {"name": "不合格 / 失误", "kind": "condition", "meta": "条件 · 比例"},
                    {
                        "name": "供应商复核",
                        "kind": "human",
                        "meta": "人工 1-N 轮 · 支持驳回",
                    },
                    {"name": "不认可结论", "kind": "condition", "meta": "条件 · 比例"},
                    {"name": "申诉复核", "kind": "human", "meta": "人工复核"},
                ],
            },
            {
                "name": "数据标注环节",
                "short_name": "标注环节",
                "desc": "自动切分与人工复核组合，人工节点支持多轮和驳回",
                "nodes": [
                    {"name": "端到端切分", "kind": "automatic", "meta": "自动化节点"},
                    {"name": "100% 进入复核", "kind": "condition", "meta": "条件 · 比例"},
                    {
                        "name": "供应商复核",
                        "kind": "group",
                        "meta": "2 轮 · 支持驳回",
                        "children": ["一轮复核", "二轮复核"],
                        "bidirectional": True,
                    },
                    {"name": "通过 100%", "kind": "condition", "meta": "条件 · 比例"},
                    {"name": "内部验收", "kind": "human", "meta": "人工验收"},
                ],
            },
            {
                "name": "验收环节",
                "short_name": "验收环节",
                "desc": "对完成质检和标注的数据进行最终验收",
                "nodes": [
                    {"name": "验收", "kind": "acceptance", "meta": "最终验收"},
                ],
            },
        ],
    },
    {
        "id": "pl4",
        "name": "双轮人工数据处理流程",
        "creator": "joanna.qiao",
        "status": "已保存",
        "updated": "2026-07-27 15:22",
        "stages": [],
        "schedules": [],
        "phase_count": 3,
        "node_count": 5,
        "desc": "人工质检与人工标注各执行两轮处理，不支持驳回，完成后进入验收。",
        "phases": [
            {
                "name": "数据质检环节",
                "short_name": "质检环节",
                "desc": "两轮人工质检，不支持驳回",
                "nodes": [
                    {
                        "name": "人工质检",
                        "kind": "group",
                        "meta": "2 轮 · 不支持驳回",
                        "children": ["质检", "抽检"],
                        "bidirectional": False,
                    },
                ],
            },
            {
                "name": "数据标注环节",
                "short_name": "标注环节",
                "desc": "两轮人工标注，不支持驳回",
                "nodes": [
                    {
                        "name": "人工标注",
                        "kind": "group",
                        "meta": "2 轮 · 不支持驳回",
                        "children": ["标注", "抽验"],
                        "bidirectional": False,
                    },
                ],
            },
            {
                "name": "验收环节",
                "short_name": "验收环节",
                "desc": "对质检和标注完成的数据进行最终验收",
                "nodes": [
                    {"name": "验收", "kind": "acceptance", "meta": "最终验收"},
                ],
            },
        ],
    },
]

# 标准训练与 DAgger 流程沿用原算子顺序，但环节仅作为目录标签。
# 流程引擎只保存 input / 节点 / 边 / output，不再保存环节容器。
_operator_by_id = {operator["id"]: operator for operator in OPERATORS}
for _pipeline in PIPELINES:
    if _pipeline["id"] not in {"pl1", "pl2"}:
        continue
    _automatic_nodes = []
    for _stage_id in _pipeline["stages"]:
        _operator = _operator_by_id[_stage_id]
        _automatic_nodes.append(
            {
                "name": _operator["name"].split(" ")[0],
                "kind": "automatic",
                "meta": _operator["desc"],
                "ident": _operator["ident"],
                "image": "frontdesk-py3.10:latest",
                "script": "python " + _operator["script"],
                "params": _operator["params"],
                "returns": _operator["returns"],
            }
        )
    _pipeline["business_stage"] = "质检"
    _pipeline["input_contract"] = "完整 Recording 元数据"
    _pipeline["output_contract"] = "quality_conclusion + 完整 Recording 元数据"
    _pipeline["flow_nodes"] = _automatic_nodes
    _pipeline["node_count"] = len(_automatic_nodes)

_review_flows = [
    {
        "id": "pl3q",
        "name": "多级质检复核流程",
        "creator": "joanna.qiao",
        "status": "已保存",
        "updated": "2026-07-29 10:12",
        "stages": [],
        "schedules": [],
        "business_stage": "质检",
        "input_contract": "完整 Recording 元数据",
        "output_contract": "quality_conclusion + quality_records",
        "desc": "自动化质检后按条件进入抽检、供应商复核和申诉复核。",
        "flow_nodes": [
            {"name": "自动化质检", "kind": "automatic", "meta": "执行质检规则集 v3"},
            {"name": "抽检条件", "kind": "condition", "meta": "不合格 100% 或按抽样比例进入"},
            {
                "name": "抽检复核",
                "kind": "human",
                "meta": "人工复核自动质检结果",
                "workbench": "质检工作台 v2.0",
                "user_groups": ["质检复核用户组"],
                "allowed_actions": ["提交", "暂离"],
            },
            {"name": "复核条件", "kind": "condition", "meta": "不合格或操作失误进入复核"},
            {
                "name": "供应商复核",
                "kind": "human",
                "meta": "供应商复核质量结论",
                "workbench": "质检工作台 v2.0",
                "user_groups": ["质检复核用户组"],
                "allowed_actions": ["提交", "驳回", "暂离"],
                "reject_enabled": True,
                "reject_targets": ["抽检复核"],
            },
            {"name": "申诉条件", "kind": "condition", "meta": "不认可结论时进入申诉"},
            {
                "name": "申诉复核",
                "kind": "human",
                "meta": "内部申诉与最终复核",
                "workbench": "质检工作台 v2.0",
                "user_groups": ["内部验收用户组"],
                "allowed_actions": ["提交", "驳回", "暂离"],
                "reject_enabled": True,
                "reject_targets": ["抽检复核", "供应商复核"],
            },
        ],
    },
    {
        "id": "pl3a",
        "ident": "e2e-split-annotation",
        "name": "端到端切分标注流程",
        "creator": "joanna.qiao",
        "status": "启用",
        "updated": "2026-07-29 10:16",
        "stages": [],
        "schedules": [],
        "business_stage": "标注",
        "input_contract": "quality_conclusion=合格/操作失误",
        "output_contract": "annotation_payload + annotation_version",
        "desc": "自动切分后依次完成供应商抽验、供应商复核、供应商验收与内部验收。",
        "flow_nodes": [
            {
                "name": "端到端切分",
                "kind": "automatic",
                "meta": "生成初始动作片段",
                "operator_id": "op_e2e_segment_annotation",
            },
            {
                "name": "供应商抽验",
                "kind": "human",
                "meta": "供应商抽验",
                "workbench": "语义标注工作台 v1.0",
                "user_groups": ["光轮智能", "供应商 A"],
                "assignee_type": "supplier",
                "assignee_mode": "task_custom",
                "allowed_actions": ["提交", "暂离"],
            },
            {
                "name": "供应商复核",
                "kind": "human",
                "meta": "供应商复核",
                "workbench": "语义标注工作台 v1.0",
                "user_groups": ["供应商 A"],
                "assignee_type": "supplier",
                "assignee_mode": "inherit",
                "inherit_assignee_node": "供应商抽验",
                "allowed_actions": ["提交", "驳回", "暂离"],
                "reject_enabled": True,
                "reject_targets": ["供应商抽验"],
            },
            {
                "name": "供应商验收",
                "kind": "human",
                "meta": "供应商验收",
                "workbench": "语义标注工作台 v1.0",
                "user_groups": ["供应商 A", "光轮智能"],
                "assignee_type": "supplier",
                "assignee_mode": "task_custom",
                "allowed_actions": ["提交", "驳回", "暂离"],
                "reject_enabled": True,
                "reject_targets": ["供应商复核"],
            },
            {
                "name": "供应商抽样",
                "kind": "condition",
                "meta": "供应商 A 抽 50%，供应商 B 抽 30%",
                "branches": [
                    {
                        "name": "供应商抽样",
                        "logic": "or",
                        "rules": [
                            {
                                "field": "供应商",
                                "operator": "等于",
                                "value": "供应商 A",
                                "percent": 50,
                            },
                            {
                                "field": "供应商",
                                "operator": "等于",
                                "value": "供应商 B",
                                "percent": 30,
                            },
                        ],
                    }
                ],
            },
            {
                "name": "内部验收",
                "kind": "human",
                "meta": "内部验收",
                "workbench": "语义标注工作台 v1.0",
                "user_groups": ["内部验收用户组"],
                "assignee_type": "user_group",
                "assignee_mode": "task_custom",
                "allowed_actions": ["提交", "驳回", "暂离"],
                "reject_enabled": True,
                "reject_targets": ["供应商抽验", "供应商复核", "供应商验收"],
            },
        ],
    },
    {
        "id": "pl3v",
        "name": "数据验收流程",
        "creator": "joanna.qiao",
        "status": "已保存",
        "updated": "2026-07-29 10:18",
        "stages": [],
        "schedules": [],
        "business_stage": "验收",
        "input_contract": "质检与标注流程输出",
        "output_contract": "acceptance_conclusion",
        "desc": "对完成质检和标注的数据执行最终验收。",
        "flow_nodes": [
            {
                "name": "验收",
                "kind": "human",
                "meta": "确认数据达到交付标准",
                "workbench": "详情工作台 v1.0",
                "user_groups": ["内部验收用户组"],
                "allowed_actions": ["提交", "驳回", "暂离"],
            },
        ],
    },
    {
        "id": "pl4q",
        "name": "双轮人工质检流程",
        "creator": "joanna.qiao",
        "status": "已保存",
        "updated": "2026-07-29 10:20",
        "stages": [],
        "schedules": [],
        "business_stage": "质检",
        "input_contract": "完整 Recording 元数据",
        "output_contract": "quality_conclusion + quality_records",
        "desc": "人工质检与抽检两轮处理。",
        "flow_nodes": [
            {
                "name": "质检",
                "kind": "human",
                "meta": "第一轮人工质检",
                "workbench": "质检工作台 v2.0",
                "user_groups": ["质检复核用户组"],
                "allowed_actions": ["提交", "暂离"],
            },
            {
                "name": "抽检",
                "kind": "human",
                "meta": "第二轮人工抽检",
                "workbench": "质检工作台 v2.0",
                "user_groups": ["内部验收用户组"],
                "allowed_actions": ["提交", "暂离"],
            },
        ],
    },
    {
        "id": "pl4a",
        "name": "双轮人工标注流程",
        "creator": "joanna.qiao",
        "status": "已保存",
        "updated": "2026-07-29 10:22",
        "stages": [],
        "schedules": [],
        "business_stage": "标注",
        "input_contract": "quality_conclusion=合格/操作失误",
        "output_contract": "annotation_payload + annotation_version",
        "desc": "人工标注与人工抽验两轮处理。",
        "flow_nodes": [
            {
                "name": "标注",
                "kind": "human",
                "meta": "动作切分与描述",
                "workbench": "标注工作台 v4.1",
                "user_groups": ["标注员用户组", "新规实验标注员用户组"],
                "allowed_actions": ["提交", "暂离"],
            },
            {
                "name": "抽验",
                "kind": "human",
                "meta": "标注结果抽验",
                "workbench": "详情工作台 v1.0",
                "user_groups": ["标注抽验员用户组"],
                "allowed_actions": ["提交", "暂离"],
            },
        ],
    },
]

PIPELINES = sorted(_review_flows, key=lambda pipeline: pipeline["id"] != "pl3a") + [
    pipeline for pipeline in PIPELINES if pipeline["id"] in {"pl1", "pl2"}
]

RUNS = [
    {"id": "run_0612a", "pipeline": "pl1", "name": "标准训练数据流水线", "target": "clean_whiteboard_v4", "status": "running", "progress": 62, "stage": "采样配比 (3/5)", "at": "2026-06-04 01:40", "dur": "进行中 8m", "trigger": "manual", "by": "joanna.qiao"},
    {"id": "run_0611b", "pipeline": "pl1", "name": "标准训练数据流水线", "target": "tidy_desk_mix_v1", "status": "done", "progress": 100, "stage": "完成", "at": "2026-06-01 09:02", "dur": "13m 24s", "trigger": "scheduled"},
    {"id": "run_0610c", "pipeline": "pl2", "name": "DAgger 数据流水线", "target": "whiteboard_dagger_v2", "status": "failed", "progress": 40, "stage": "质检 Doctor (FAIL: 缺帧)", "at": "2026-05-31 20:11", "dur": "4m 02s", "trigger": "scheduled"},
    {"id": "run_0609d", "pipeline": "pl1", "name": "标准训练数据流水线", "target": "whiteboard_eval_bench", "status": "done", "progress": 100, "stage": "完成", "at": "2026-05-30 17:50", "dur": "9m 41s", "trigger": "manual", "by": "Min Chen"},
]

# ════════════════════════════════════════════════════════════════
# Section 2: HTML / CSS Templates
# ════════════════════════════════════════════════════════════════

BASE_CSS = """
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif; }
.ant-btn,.ant-input,.ant-select-selector,.ant-card,.ant-tag,.ant-alert,.ant-table-wrapper { border-radius:8px !important; }
.ant-btn-primary,.ant-btn-primary:focus { background:#1F80A0; border-color:#1F80A0; }
.ant-btn-primary:hover { background:#176a88; border-color:#176a88; }
a { color:#1F80A0; text-decoration:none; } a:hover { color:#176a88; }

/* ── Layout ── */
.q-layout { display:flex; min-height:calc(100vh - 52px); background:#001529; }
/* ── 顶部导航 ── */
.top-nav { position:fixed; top:0; left:0; right:0; height:52px; background:#001529; display:flex; align-items:center; gap:0; padding:0; z-index:200; }
.top-nav .tn-brand { width:192px; box-sizing:border-box; padding:0 16px; flex:none; display:flex; align-items:center; gap:10px; color:rgba(255,255,255,0.92); font-weight:600; font-size:15px; }
.top-nav .tn-brand .logo-icon { width:30px; height:30px; background:linear-gradient(135deg,#1F80A0,#36cfc9); border-radius:7px; display:flex; align-items:center; justify-content:center; font-size:15px; font-weight:700; color:#fff; }
.top-nav .tn-nav { display:flex; align-items:center; gap:8px; height:100%; }
.top-nav .tn-item { position:relative; display:flex; align-items:center; height:100%; padding:0 8px; color:rgba(255,255,255,0.6); font-size:14px; cursor:pointer; transition:color 0.15s; }
.top-nav .tn-item:hover { color:rgba(255,255,255,0.9); }
.top-nav .tn-item.active { color:#fff; font-weight:600; }
.top-nav .tn-item.active::after { content:''; position:absolute; left:50%; transform:translateX(-50%); bottom:0; width:18px; height:3px; background:#1F80A0; border-radius:2px; }
.top-nav .tn-sep { width:1px; height:18px; background:rgba(255,255,255,0.16); margin:0 8px; }
.top-nav .tn-right { margin-left:auto; margin-right:20px; color:rgba(255,255,255,0.55); font-size:12px; border:1px solid rgba(255,255,255,0.22); padding:2px 12px; border-radius:11px; letter-spacing:0.5px; }
.q-layout { padding-top:52px; }
.q-sider { width:192px; min-width:192px; background:#001529; position:fixed; top:52px; left:0; bottom:0; z-index:100; display:flex; flex-direction:column; overflow-y:auto; }
.q-sider .logo { height:64px; display:flex; align-items:center; gap:10px; padding:0 16px; border-bottom:1px solid rgba(255,255,255,0.08); }
.q-sider .logo-icon { width:36px; height:36px; background:linear-gradient(135deg,#1F80A0,#36cfc9); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:700; color:#fff; }
.q-sider .logo-text { font-size:14px; font-weight:600; color:rgba(255,255,255,0.9); }
.q-sider .nav-section { padding:8px 0; flex:1; }
.q-sider .nav-label { padding:14px 24px 4px; font-size:11px; color:rgba(255,255,255,0.35); text-transform:uppercase; letter-spacing:0.8px; font-weight:600; }
.q-sider .nav-item { display:flex; align-items:center; gap:10px; padding:10px 24px; color:rgba(255,255,255,0.65); font-size:14px; transition:all 0.2s; margin:2px 8px; border-radius:6px; }
.q-sider .nav-item:hover { color:#fff; background:rgba(255,255,255,0.06); }
.q-sider .nav-item.active { color:#fff; background:#1F80A0; }
.q-sider .nav-item .icon { width:16px; text-align:center; }
.q-sider .nav-item.sub { padding-left:40px; font-size:13px; }
.q-sider .user-block { padding:12px 16px; border-top:1px solid rgba(255,255,255,0.08); display:flex; align-items:center; gap:10px; }
.q-sider .user-avatar { width:32px; height:32px; border-radius:50%; background:#1F80A0; color:#fff; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:600; }
.q-sider .user-name { color:rgba(255,255,255,0.85); font-size:13px; font-weight:500; }
.q-sider .user-role { color:rgba(255,255,255,0.35); font-size:11px; }

.q-main { margin-left:192px; flex:1; min-width:0; background:#f0f2f5; min-height:calc(100vh - 52px); border-top-left-radius:8px; transition:margin-left 0.2s, margin-right 0.22s; }
.q-sider { transition:width 0.2s, min-width 0.2s; }
/* 折叠按钮: 底部用户旁, 仅图标 */
.sider-collapse-btn { margin-left:auto; cursor:pointer; color:rgba(255,255,255,0.45); width:26px; height:26px; display:flex; align-items:center; justify-content:center; border-radius:6px; font-size:15px; flex:none; }
.sider-collapse-btn:hover { color:#fff; background:rgba(255,255,255,0.08); }
.sc-exp { display:none; }
/* 折叠态: icon rail (只留图标) */
body.sider-collapsed .q-sider { width:64px; min-width:64px; }
body.sider-collapsed .q-main { margin-left:64px; }
body.sider-collapsed .logo-text,
body.sider-collapsed .nav-label,
body.sider-collapsed .nav-txt,
body.sider-collapsed .user-info { display:none; }
body.sider-collapsed .nav-item { justify-content:center; padding-left:0; padding-right:0; gap:0; }
body.sider-collapsed .logo { justify-content:center; padding:0; }
body.sider-collapsed .user-block { flex-direction:column; gap:10px; padding:12px 0; }
body.sider-collapsed .sider-collapse-btn { margin-left:0; }
body.sider-collapsed .sc-col { display:none; }
body.sider-collapsed .sc-exp { display:inline; }
.q-header { background:#fff; padding:0 24px; height:48px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #f0f0f0; position:sticky; top:0; z-index:50; }
.q-header .crumb { font-size:14px; color:rgba(0,0,0,0.45); }
.q-header .crumb b { color:rgba(0,0,0,0.85); font-weight:500; }
.q-content { padding:24px; }

/* ── Stat cards ── */
.stat-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:16px; margin-bottom:24px; }
.stat-card { background:#fff; border-radius:8px; padding:18px 22px; border:1px solid #f0f0f0; }
.stat-card .stat-label { font-size:13px; color:rgba(0,0,0,0.45); margin-bottom:4px; }
.stat-card .stat-value { font-size:28px; font-weight:600; color:rgba(0,0,0,0.85); }
.stat-card .stat-sub { font-size:12px; color:rgba(0,0,0,0.45); margin-top:4px; }

/* ── Card ── */
.card { background:#fff; border-radius:8px; border:1px solid #f0f0f0; padding:20px 24px; margin-bottom:16px; }
.card h3 { font-size:16px; font-weight:500; margin:0 0 16px; color:rgba(0,0,0,0.85); }
.card h4 { font-size:14px; font-weight:500; margin:0 0 12px; color:rgba(0,0,0,0.85); }
.muted { color:rgba(0,0,0,0.45); font-size:13px; }

/* ── Filter bar ── */
.filter-bar { display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; align-items:center; }
.filter-bar input,.filter-bar select { padding:5px 12px; height:34px; border:1px solid #d9d9d9; border-radius:8px; font-size:14px; color:rgba(0,0,0,0.85); outline:none; background:#fff; }
.filter-bar input:focus,.filter-bar select:focus { border-color:#1F80A0; box-shadow:0 0 0 2px rgba(31,128,160,0.12); }
input::placeholder, textarea::placeholder { color:rgba(0,0,0,0.32); opacity:1; }
select.select-empty { color:rgba(0,0,0,0.32) !important; }
select option { color:rgba(0,0,0,0.85); }
select option:disabled { color:rgba(0,0,0,0.32); }
/* ---- 数据查询: 筛选区 ---- */
.q-filters { position:relative; background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:18px 20px; margin-bottom:16px; }
.q-mode-tabs { display:flex; gap:24px; border-bottom:1px solid #f0f0f0; margin:-4px 0 16px; }
.q-mode-tabs .qm-tab { position:relative; border:none; background:none; padding:4px 2px 12px; font-size:14px; cursor:pointer; color:rgba(0,0,0,0.55); }
.q-mode-tabs .qm-tab:hover { color:rgba(0,0,0,0.85); }
.q-mode-tabs .qm-tab.active { color:#1F80A0; font-weight:600; }
.q-mode-tabs .qm-tab.active::after { content:''; position:absolute; left:0; right:0; bottom:-1px; height:2px; background:#1F80A0; border-radius:1px; }
#qModeSql .CodeMirror { border:1px solid #2a2a2a; border-radius:8px; font-size:12.5px; line-height:1.6; font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace; height:220px; }
#qModeSql .CodeMirror-gutters { border-right:1px solid #333; }
#info_full .CodeMirror { border:1px solid #2a2a2a; border-radius:8px; font-size:12.5px; line-height:1.55; min-height:320px; font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace; }
#info_full .CodeMirror-gutters { border-right:1px solid #333; }
.qf-group { border:1px solid #f0f0f0; border-radius:8px; padding:12px 14px 4px; margin-bottom:12px; background:#fafafa; }
.qf-group-title { font-size:13px; font-weight:600; color:rgba(0,0,0,0.78); margin-bottom:10px; padding-left:8px; border-left:3px solid #1F80A0; line-height:1.2; cursor:pointer; user-select:none; }
.qf-caret { display:inline-block; font-size:10px; color:rgba(0,0,0,0.4); margin-right:6px; transition:transform .15s; }
.qf-group.collapsed .qf-caret { transform:rotate(-90deg); }
.qf-group.collapsed { padding-bottom:12px; }
.qf-group.collapsed .qf-group-title { margin-bottom:0; }
.qf-group.collapsed .qf-group-body { display:none; }
.sql-bar { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.sql-ai { border:1px solid #ecdff7; border-radius:8px; background:#faf7fd; padding:12px 14px; margin-bottom:10px; }
.sql-ai-head { font-size:13px; font-weight:600; color:#7c4dca; margin-bottom:8px; }
.sql-ai-row { display:flex; gap:8px; }
.sql-ai-input { flex:1; height:34px; border:1px solid #e2e4e8; border-radius:8px; padding:0 12px; font-size:13px; color:rgba(0,0,0,0.85); outline:none; background:#fff; }
.sql-ai-input:focus { border-color:#9b59b6; box-shadow:0 0 0 2px rgba(155,89,182,0.12); }
.sql-ai-note { margin-top:8px; font-size:12px; color:#2e9e5b; }
.sql-status { margin-top:10px; border-radius:8px; padding:10px 12px; font-size:12.5px; display:flex; align-items:flex-start; gap:8px; }
.sql-status.running { background:#f0f7fb; color:#1F80A0; border:1px solid #d7ebf3; }
.sql-status.ok { background:#f0faf4; color:#2e9e5b; border:1px solid #cdeedb; }
.sql-status.err { background:#fdf3f3; color:#d4504e; border:1px solid #f3d6d5; flex-direction:column; }
.sql-status .sql-err-log { margin-top:6px; font-family:'SFMono-Regular',Consolas,Menlo,monospace; font-size:12px; color:#a23b39; white-space:pre-wrap; background:#fff; border:1px solid #f3d6d5; border-radius:6px; padding:8px 10px; width:100%; box-sizing:border-box; }
.sql-spin { width:13px; height:13px; border:2px solid rgba(31,128,160,0.3); border-top-color:#1F80A0; border-radius:50%; animation:sqlspin .7s linear infinite; flex:0 0 auto; margin-top:1px; }
@keyframes sqlspin { to { transform:rotate(360deg); } }
.ai-fab.active { border-color:#9b59b6; color:#9b59b6; background:#f7f0fc; }
.qf-dep { transition:opacity .15s; }
.qf-dep.qf-off { opacity:.45; pointer-events:none; }
.q-filter-row { display:flex; gap:14px 18px; flex-wrap:wrap; align-items:flex-end; }
.q-field { display:flex; flex-direction:column; gap:6px; }
.q-field > label { font-size:12px; color:rgba(0,0,0,0.45); padding-left:1px; }
.q-field select, .q-field input:not([type=checkbox]) { height:36px; min-width:158px; box-sizing:border-box; border:1px solid #e2e4e8; border-radius:8px; padding:0 12px; font-size:13.5px; color:rgba(0,0,0,0.85); background:#fff; outline:none; }
.q-field select { padding-right:32px; cursor:pointer; -webkit-appearance:none; appearance:none; background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' stroke='%23999' stroke-width='1.4' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>"); background-repeat:no-repeat; background-position:right 12px center; }
.q-field select:hover, .q-field input:hover { border-color:#bcc0c6; }
.q-field select:focus, .q-field input:focus { border-color:#1F80A0; box-shadow:0 0 0 2px rgba(31,128,160,0.12); }
.q-field select.has-value, .q-field input.has-value { border-color:#1F80A0; color:#1F80A0; background-color:#f3f9fb; }
/* 字段内多选下拉 */
.q-field .ms-wrap .ms-trigger { height:36px; min-width:158px; border-color:#e2e4e8; }
.q-field .ms-wrap .ms-trigger.has-value { border-color:#1F80A0; color:#1F80A0; background:#f3f9fb; }
.ms-grp { padding:8px 14px 3px; font-size:11px; color:rgba(0,0,0,0.4); font-weight:600; }
.q-table-scroll { overflow-x:auto; }
.q-table-scroll table { min-width:760px; }
.q-table-scroll th, .q-table-scroll td { white-space:nowrap; }
.q-table-scroll td .tg { white-space:nowrap; }
/* 时间区间 */
.q-range { display:flex; align-items:center; gap:8px; }
.q-range input[type=date] { min-width:140px; }
.q-range-sep { color:rgba(0,0,0,0.35); }
.q-actions { display:flex; gap:8px; margin-left:auto; align-items:flex-end; }
.rule-filter-panel { margin-bottom:12px; padding:16px 18px; }
.rule-filter-panel .q-filter-row { align-items:flex-end; }
.rule-filter-panel .q-field input, .rule-filter-panel .q-field select { min-width:220px; }
.rule-filter-panel .q-field .ms-trigger { min-width:220px; }
.q-field.grow { flex:1 1 240px; min-width:220px; }
.q-field.grow > input, .q-field.grow .ms-wrap, .q-field.grow .ms-wrap .ms-trigger { width:100%; }
/* 高级筛选行: 各项撑满整行 */
.q-adv-row .q-field { flex:1 1 0; min-width:0; }
.q-adv-row .q-field select, .q-adv-row .q-field > input, .q-adv-row .q-field .ms-wrap, .q-adv-row .q-field .ms-wrap .ms-trigger { width:100%; min-width:0; }
.q-adv-row .q-field .q-range { width:100%; }
.q-adv-row .q-field .q-range input { flex:1; min-width:0; }
.drawer-body .q-adv-row { margin-top:14px; }
.q-filter-tools { display:flex; gap:8px; align-items:center; justify-content:flex-end; margin-top:14px; padding-top:14px; border-top:1px solid #f0f0f0; }
.tools-divider { width:1px; height:22px; background:#e2e4e8; margin:0 6px; }
.q-adv-note { flex-basis:100%; font-size:12px; margin-top:2px; }
/* 配方助手 */
.rc-intro { font-size:12.5px; color:rgba(0,0,0,0.6); line-height:1.7; margin-bottom:8px; }
.rc-sec { font-size:13px; font-weight:600; color:rgba(0,0,0,0.85); margin:18px 0 10px; padding-left:8px; border-left:3px solid #1F80A0; display:flex; gap:8px; align-items:baseline; }
.rc-sec .muted { font-weight:400; font-size:12px; }
.rc-row { margin-bottom:14px; }
.rc-label { display:flex; justify-content:space-between; font-size:13px; margin-bottom:5px; }
.rc-label .rc-pct { color:#1F80A0; font-weight:600; font-family:'SF Mono',Menlo,monospace; }
.rc-track { position:relative; height:6px; background:#eef2f4; border-radius:3px; cursor:ew-resize; }
.rc-base-mark { position:absolute; top:-3px; bottom:-3px; width:2px; background:#c2ccd2; left:50%; }
.rc-fill { position:absolute; left:0; top:0; height:100%; background:linear-gradient(90deg,#3aa6c4,#1F80A0); border-radius:3px; min-width:6px; }
.rc-handle { position:absolute; right:-6px; top:50%; width:12px; height:12px; margin-top:-6px; background:#fff; border:2px solid #1F80A0; border-radius:50%; box-shadow:0 1px 3px rgba(0,0,0,0.2); cursor:ew-resize; }
.rc-sub { font-size:11.5px; color:rgba(0,0,0,0.4); margin-top:4px; }
.rc-sub b { color:rgba(0,0,0,0.7); }
.rc-foot { border-top:1px solid #f0f0f0; padding:14px 16px; display:flex; flex-direction:column; gap:10px; }
.rc-count { font-size:14px; color:rgba(0,0,0,0.85); }
.rc-count b { color:#1F80A0; font-size:18px; }
.ai-fab, .recipe-btn { display:inline-flex; align-items:center; gap:6px; height:34px; padding:0 14px; border-radius:8px; border:1px solid #e2e4e8; cursor:pointer; font-size:13.5px; color:rgba(0,0,0,0.7); background:#fff; }
.ai-fab:hover, .recipe-btn:hover { border-color:#1F80A0; color:#1F80A0; background:#f7fbfc; }
.ai-fab span, .recipe-btn span { font-size:14px; }
.ai-fab .ic-ai { color:#9b59b6; }
/* ---- AI 辅助 侧栏 (固定推开, 不占页面宽度, 满屏高) ---- */
.ai-side { position:fixed; top:52px; right:0; bottom:0; width:0; overflow:hidden; background:#fff; border-left:1px solid #eee; box-shadow:-6px 0 24px rgba(0,0,0,0.07); transition:width 0.22s ease; z-index:1000; }
.ai-side.active { width:400px; }
.ai-inner { position:absolute; top:0; right:0; width:400px; height:100%; display:flex; flex-direction:column; }
.q-main.ai-pushed { margin-right:400px; }
.ai-head { display:flex; align-items:center; justify-content:space-between; padding:15px 18px; border-bottom:1px solid #f0f0f0; font-size:15px; }
.ai-body { flex:1; overflow-y:auto; padding:18px 16px; display:flex; flex-direction:column; gap:16px; background:#fafbfc; }
.ai-msg { display:flex; flex-direction:column; gap:8px; }
.ai-msg.ai-bot { align-items:flex-start; }
.ai-msg.ai-user { align-items:flex-end; }
.ai-bubble { padding:10px 14px; border-radius:12px; font-size:13.5px; line-height:1.6; max-width:90%; }
.ai-bot .ai-bubble { background:#fff; color:rgba(0,0,0,0.82); border:1px solid #eee; border-top-left-radius:3px; }
.ai-user .ai-bubble { background:#1F80A0; color:#fff; border-top-right-radius:3px; }
.ai-chips { display:flex; flex-wrap:wrap; gap:7px; }
.ai-chip { font-size:12px; padding:5px 11px; border:1px solid #cfe4ec; color:#1F80A0; background:#fff; border-radius:14px; cursor:pointer; }
.ai-chip:hover { background:#e6f4f8; }
.ai-sql { align-self:stretch; background:#1e1e1e; color:#d4d4d4; padding:11px 13px; border-radius:8px; font-size:12px; line-height:1.55; overflow-x:auto; white-space:pre; margin:0; font-family:'SF Mono',Menlo,monospace; }
.ai-run { align-self:flex-start; height:30px; padding:0 14px; font-size:13px; }
.ai-input { position:relative; border-top:1px solid #f0f0f0; padding:12px 14px; }
.ai-input textarea { width:100%; min-height:44px; max-height:120px; border:1px solid #d9d9d9; border-radius:8px; padding:9px 44px 9px 12px; font-size:13.5px; outline:none; resize:none; font-family:inherit; line-height:1.5; box-sizing:border-box; }
.ai-input textarea:focus { border-color:#1F80A0; }
.ai-send { position:absolute; right:24px; bottom:21px; width:28px; height:28px; border:none; border-radius:7px; background:#1F80A0; color:#fff; cursor:pointer; display:flex; align-items:center; justify-content:center; font-size:14px; line-height:1; }
.ai-send:hover { background:#176a88; }
.btn { display:inline-flex; align-items:center; gap:6px; height:34px; padding:0 16px; border-radius:8px; font-size:14px; cursor:pointer; border:1px solid #d9d9d9; background:#fff; color:rgba(0,0,0,0.85); }
.btn:hover { border-color:#1F80A0; color:#1F80A0; }
.btn-secondary { background:#fff; border-color:#1F80A0; color:#1F80A0; }
.btn-secondary:hover { background:#f3f9fb; border-color:#176a88; color:#176a88; }
.btn-primary { background:#1F80A0; border-color:#1F80A0; color:#fff; }
.btn-primary:hover { background:#176a88; border-color:#176a88; color:#fff; }
.btn-secondary { background:#fff; border-color:#1F80A0; color:#1F80A0; }
.btn-secondary:hover { background:#e6f4f8; border-color:#176a88; color:#176a88; }
/* 多选下拉 (创建人) */
.ms-wrap { position:relative; }
.ms-trigger { height:34px; min-width:120px; padding:5px 28px 5px 12px; border:1px solid #d9d9d9; border-radius:8px; font-size:14px; color:rgba(0,0,0,0.65); background:#fff; cursor:pointer; display:flex; align-items:center; position:relative; }
.ms-trigger:hover { border-color:#1F80A0; }
.ms-trigger::after { content:''; position:absolute; right:11px; top:50%; border:5px solid transparent; border-top-color:#bfbfbf; transform:translateY(-2px); }
.ms-label { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ms-panel { display:none; position:absolute; top:calc(100% + 4px); left:0; min-width:160px; max-height:300px; overflow-y:auto; background:#fff; border:1px solid #f0f0f0; border-radius:8px; box-shadow:0 6px 16px rgba(0,0,0,0.08); z-index:100; padding:4px 0; }
.ms-uid { color:rgba(0,0,0,0.35); font-size:11px; }
.ps-wrap { position:relative; }
.ps-control { display:flex; flex-wrap:wrap; align-items:center; gap:5px; min-height:36px; border:1px solid #e2e4e8; border-radius:8px; padding:3px 8px; background:#fff; cursor:text; box-sizing:border-box; }
.ps-control:focus-within { border-color:#1F80A0; box-shadow:0 0 0 2px rgba(31,128,160,0.12); }
.ps-chip { display:inline-flex; align-items:center; gap:4px; background:#eef3f8; color:#1F80A0; border-radius:4px; padding:1px 4px 1px 8px; font-size:12px; line-height:20px; }
.ps-chip .ps-x { cursor:pointer; color:rgba(31,128,160,0.55); font-style:normal; font-size:14px; padding:0 2px; }
.ps-chip .ps-x:hover { color:#d4504e; }
.ps-input { flex:1; min-width:90px; border:none; outline:none; height:28px; font-size:13px; background:transparent; color:rgba(0,0,0,0.85); }
.q-field .ps-control .ps-input, .q-field .ps-control .ps-input:hover, .q-field .ps-control .ps-input:focus { border:none; background:transparent; height:28px; min-width:90px; padding:0; box-shadow:none; }
.ps-panel { display:none; position:absolute; top:calc(100% + 4px); left:0; right:0; min-width:230px; max-height:260px; overflow-y:auto; background:#fff; border:1px solid #f0f0f0; border-radius:8px; box-shadow:0 6px 16px rgba(0,0,0,0.08); z-index:100; padding:4px; }
.ps-wrap.open .ps-panel { display:block; }
.ps-opt { padding:8px 10px; border-radius:6px; cursor:pointer; font-size:13px; color:rgba(0,0,0,0.8); }
.ps-opt:hover { background:#f3f9fb; color:#1F80A0; }
.ps-empty { display:none; padding:14px; text-align:center; font-size:12px; color:rgba(0,0,0,0.35); }
.q-adv-row .q-field .ps-wrap { width:100%; }
.ms-wrap.open .ms-panel { display:block; }
.ms-panel label { display:flex; align-items:center; gap:8px; padding:6px 14px; font-size:13px; cursor:pointer; color:rgba(0,0,0,0.8); }
.ms-panel label:hover { background:#fafafa; }
.ms-panel input { accent-color:#1F80A0; }

/* 数据集标签：单一多选框内展示完整层级路径 */
.dataset-tag-picker { position:relative; width:100%; }
.dataset-tag-picker-control { min-height:42px; box-sizing:border-box; display:flex; align-items:center; gap:8px; padding:7px 38px 7px 9px; border:1px solid #d9d9d9; border-radius:8px; background:#fff; cursor:pointer; position:relative; transition:border-color .15s,box-shadow .15s; }
.dataset-tag-picker-control:hover,.dataset-tag-picker.open .dataset-tag-picker-control { border-color:#1F80A0; }
.dataset-tag-picker.open .dataset-tag-picker-control { box-shadow:0 0 0 2px rgba(31,128,160,0.12); }
.dataset-tag-picker-chips { display:flex; flex:1; min-width:0; flex-wrap:wrap; gap:6px; }
.dataset-tag-picker-placeholder { color:rgba(0,0,0,0.32); font-size:13px; line-height:26px; }
.dataset-tag-chip { display:inline-flex; align-items:center; gap:6px; max-width:100%; min-height:26px; box-sizing:border-box; padding:2px 8px 2px 10px; border:1px solid #b8e2e8; border-radius:5px; background:#eef9fa; color:#176a88; font-size:12.5px; line-height:20px; }
.dataset-tag-chip-text { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.dataset-tag-chip-remove { width:18px; height:18px; padding:0; border:0; background:transparent; color:#1F80A0; font-size:16px; line-height:18px; cursor:pointer; }
.dataset-tag-picker-arrow { position:absolute; right:13px; top:50%; width:8px; height:8px; border-right:1.5px solid #9ca3af; border-bottom:1.5px solid #9ca3af; transform:translateY(-65%) rotate(45deg); transition:transform .15s; }
.dataset-tag-picker.open .dataset-tag-picker-arrow { transform:translateY(-20%) rotate(225deg); }
.dataset-tag-picker-panel { display:none; position:absolute; z-index:180; top:calc(100% + 5px); left:0; right:0; max-height:290px; overflow-y:auto; padding:6px; border:1px solid #e2e4e8; border-radius:8px; background:#fff; box-shadow:0 10px 28px rgba(0,0,0,0.12); }
.dataset-tag-picker.open .dataset-tag-picker-panel { display:block; }
.dataset-tag-picker-group { padding:7px 9px 4px; color:rgba(0,0,0,0.42); font-size:11px; font-weight:600; }
.dataset-tag-picker-option { display:flex; align-items:flex-start; gap:8px; padding:7px 9px; border-radius:6px; color:rgba(0,0,0,0.75); font-size:12.5px; line-height:20px; cursor:pointer; }
.dataset-tag-picker-option:hover { background:#f3f9fb; }
.dataset-tag-picker-option input { width:auto; margin:3px 0 0; padding:0; accent-color:#1F80A0; box-shadow:none; }
.dataset-tag-picker.readonly .dataset-tag-picker-control { cursor:default; padding-right:9px; background:#fff; }
.dataset-tag-picker.readonly .dataset-tag-chip { padding-right:10px; }
.dataset-tag-picker.readonly .dataset-tag-chip-remove,.dataset-tag-picker.readonly .dataset-tag-picker-arrow { display:none; }
[data-dataset-info-field="tags"] .dataset-tag-picker.readonly .dataset-tag-picker-control { min-height:0; padding:0; border:0; background:transparent; }

/* ── Table ── */
.ant-table { width:100%; border-collapse:collapse; font-size:14px; background:#fff; }
.ant-table thead th { background:#fafafa; padding:9px 16px; font-weight:500; color:rgba(0,0,0,0.85); text-align:left; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.ant-table tbody td { padding:9px 16px; border-bottom:1px solid #f0f0f0; color:rgba(0,0,0,0.65); vertical-align:middle; }
.ant-table tbody tr:hover td { background:#fafafa; }
.actions-cell { white-space:nowrap; }
/* 统一行高 = 两行 */
.row2 tbody td { vertical-align:middle; }
.row2 .desc-clamp { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; line-height:1.5; min-height:42px; }
.row2 .wf-desc-clamp { display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:380px; }
.status-head-filter { position:relative; display:inline-flex; align-items:center; height:26px; }
.status-head-trigger { display:inline-flex; align-items:center; gap:6px; border:0; background:transparent; padding:0; color:rgba(0,0,0,0.85); font:inherit; font-weight:600; cursor:pointer; }
.status-head-trigger .caret { font-size:15px; line-height:1; transform:translateY(-1px); color:rgba(0,0,0,0.78); }
.status-head-menu { display:none; position:absolute; top:calc(100% + 9px); left:42px; z-index:180; min-width:118px; padding:6px 0; border:1px solid #e5e7eb; border-radius:6px; background:#fff; box-shadow:0 12px 28px rgba(0,0,0,0.14); overflow:hidden; }
.status-head-filter.open .status-head-menu { display:block; }
.status-head-option { display:block; width:100%; height:34px; padding:0 14px; border:0; background:#fff; color:rgba(0,0,0,0.88); text-align:left; font-size:14px; line-height:34px; cursor:pointer; white-space:nowrap; }
.status-head-option:hover { background:#f5f7fa; }
.status-head-option.active { background:#238da3; color:#fff; }
.status-with-log { display:inline-flex; align-items:center; gap:6px; white-space:nowrap; }
.status-log-icon { width:18px; height:18px; padding:0; border:1px solid #f3d6d5; border-radius:50%; background:#fff; color:#d4504e; font-size:12px; line-height:16px; cursor:pointer; display:inline-flex; align-items:center; justify-content:center; }
.status-log-icon:hover { border-color:#d4504e; background:#fdf3f3; }
.dp-log-pre { height:260px; margin:0; padding:12px 14px; border:1px solid #e5e7eb; border-radius:6px; background:#fafbfc; color:rgba(0,0,0,0.78); font-family:'SFMono-Regular',Consolas,Menlo,monospace; font-size:12.5px; line-height:1.65; white-space:pre-wrap; overflow:auto; box-sizing:border-box; }

/* ── Tags / status ── */
.tag { display:inline-block; padding:1px 8px; border-radius:4px; font-size:12px; line-height:20px; border:1px solid transparent; }
.tag-blue { color:#1F80A0; background:#e6f4f8; border-color:#8dcde0; }
.tag-gray { color:#8c8c8c; background:#f5f5f5; border-color:#e8e8e8; }
.tag-green { color:#2e9e5b; background:#f0faf4; border-color:#cdeedb; }
.tag.imp-fail { color:#d4504e; background:#fdf3f3; border-color:#f3d6d5; }
.tag-purple { color:#722ed1; background:#f9f0ff; border-color:#d3adf7; }
.tag-orange { color:#ad6800; background:#fffbe6; border-color:#ffe58f; }
.qa { display:inline-flex; align-items:center; gap:5px; font-size:13px; }
.qa::before { content:''; width:7px; height:7px; border-radius:50%; }
.qa-pass { color:#389e0d; } .qa-pass::before { background:#52c41a; }
.qa-warn { color:#d48806; } .qa-warn::before { background:#faad14; }
.qa-fail { color:#cf1322; } .qa-fail::before { background:#ff4d4f; }

/* ── Tree + Tab split layout (左树右Tab, 两面板各自独立滚动) ── */
.split { display:flex; gap:16px; align-items:stretch; height:calc(100vh - 96px); }
.tree-panel { width:300px; min-width:300px; background:#fff; border:1px solid #f0f0f0; border-radius:8px; overflow:hidden; display:flex; flex-direction:column; transition:width 0.2s,min-width 0.2s; }
.th-left { display:flex; align-items:center; gap:8px; min-width:0; }
.th-actions { display:flex; align-items:center; gap:8px; }
.tp-toggle { cursor:pointer; color:#1F80A0; font-size:15px; flex:none; width:18px; text-align:center; }
.tp-toggle:hover { color:#176a88; }
.tp-toggle .sc-exp { display:none; }
.tree-panel.tp-collapsed { width:34px; min-width:34px; }
/* 折叠: 仅保留头部的 toggle icon (展开/收起合一) */
.tree-panel.tp-collapsed > *:not(.tree-head) { display:none; }
.tree-panel.tp-collapsed .tree-head { justify-content:center; padding:10px 0; }
.tree-panel.tp-collapsed .th-title, .tree-panel.tp-collapsed .th-actions { display:none; }
.tree-panel.tp-collapsed .sc-col { display:none; }
.tree-panel.tp-collapsed .sc-exp { display:inline; }
.tree-panel .tree-head { padding:10px 14px; border-bottom:1px solid #f0f0f0; font-size:13px; font-weight:600; color:rgba(0,0,0,0.85); display:flex; justify-content:space-between; align-items:center; }
.tree-panel .tree-search { padding:8px 10px; border-bottom:1px solid #f5f5f5; }
.tree-panel .tree-search input { width:100%; box-sizing:border-box; height:30px; padding:4px 10px; border:1px solid #d9d9d9; border-radius:6px; font-size:13px; outline:none; }
.tree-panel .tree-tag-search { padding:0 10px 8px; border-bottom:1px solid #f5f5f5; }
.tree-panel .tree-tag-search select { width:100%; min-width:0; height:30px; padding:4px 28px 4px 10px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; color:rgba(0,0,0,0.72); font-size:13px; outline:none; }
.tree-panel .tree-search input:focus,.tree-panel .tree-tag-search select:focus { border-color:#1F80A0; box-shadow:0 0 0 2px rgba(31,128,160,0.10); }
.tree-body { flex:1; overflow-y:auto; padding:6px 0; }
.tree-grp { padding:7px 14px; font-size:13px; color:rgba(0,0,0,0.85); cursor:pointer; display:flex; align-items:center; gap:6px; font-weight:500; }
.tree-grp:hover { background:#fafafa; }
.tree-grp .caret { font-size:10px; color:rgba(0,0,0,0.35); transition:transform 0.2s; display:inline-block; }
.tree-grp.collapsed .caret { transform:rotate(-90deg); }
.tree-leaf { padding:6px 14px 6px 34px; font-size:13px; color:rgba(0,0,0,0.65); display:block; border-left:2px solid transparent; }
.tree-leaf:hover { background:#fafafa; color:#1F80A0; }
.tree-leaf.active { background:#e6f4f8; color:#1F80A0; border-left-color:#1F80A0; font-weight:500; }
.tree-leaf .sub { color:rgba(0,0,0,0.35); font-size:11px; }
.tree-modes { display:flex; gap:4px; padding:8px 10px; border-bottom:1px solid #f5f5f5; }
.tree-mode { flex:1; text-align:center; font-size:12px; padding:5px 0; border-radius:6px; cursor:pointer; color:rgba(0,0,0,0.55); }
.tree-mode:hover { background:#f5f5f5; }
.tree-mode.active { background:#e6f4f8; color:#1F80A0; font-weight:500; }
.tg { display:inline-block; padding:0 6px; font-size:11px; line-height:17px; border-radius:3px; background:#eef3f8; color:#5b7083; margin-right:3px; }
.tree-children.collapsed { display:none; }
.tree-grp .folder-act { color:rgba(0,0,0,0.25); font-size:14px; padding:0 4px; border-radius:4px; cursor:pointer; }
.tree-grp .folder-act:hover { color:#1F80A0; background:#eef3f8; }
.tree-grp { justify-content:flex-start; position:relative; }
/* 行内操作菜单 (目录/数据集) — 操作图标统一固定在右侧同一列 */
.tree-grp .row-act-wrap { position:absolute; right:8px; top:50%; transform:translateY(-50%); }
.row-act-wrap { display:inline-flex; align-items:center; }
.tree-leaf-wrap { position:relative; display:block; }
.tree-leaf-wrap .tree-leaf { display:block; padding-right:26px; }
.tree-leaf-wrap .leaf-act { position:absolute; right:8px; top:50%; transform:translateY(-50%); opacity:0; color:rgba(0,0,0,0.3); padding:0 4px; cursor:pointer; font-size:14px; }
.tree-leaf-wrap:hover .leaf-act { opacity:1; }
.tree-leaf-wrap .leaf-act:hover { color:#1F80A0; }
.row-menu { display:none; position:absolute; right:0; top:100%; z-index:40; background:#fff; border:1px solid #eee; border-radius:8px; box-shadow:0 6px 20px rgba(0,0,0,0.12); min-width:120px; padding:4px; }
.row-act-wrap.open { z-index:1000; }
.row-act-wrap.open .row-menu { display:block; }
.rm-item { padding:7px 12px; font-size:13px; border-radius:6px; cursor:pointer; color:rgba(0,0,0,0.8); white-space:nowrap; }
.rm-item:hover { background:#f3f9fb; color:#1F80A0; }
.rm-item.danger:hover { background:#fdf3f3; color:#d4504e; }
.rm-item.disabled { color:rgba(0,0,0,0.25); cursor:not-allowed; }
.rm-item.disabled:hover { background:none; color:rgba(0,0,0,0.25); }
.fg input:disabled, .fg select:disabled { background:#f5f5f5; color:rgba(0,0,0,0.4); cursor:not-allowed; border-color:#ececec; }

.detail-panel { flex:1; min-width:0; background:#fff; border:1px solid #f0f0f0; border-radius:8px; height:100%; overflow-y:auto; }
.detail-head { padding:16px 24px; border-bottom:1px solid #f0f0f0; display:flex; justify-content:space-between; align-items:flex-start; }
.detail-head .dh-title { font-size:18px; font-weight:600; color:rgba(0,0,0,0.85); display:flex; align-items:center; gap:10px; }
.ver-select { font-size:13px; font-weight:400; padding:3px 8px; border:1px solid #d9d9d9; border-radius:6px; color:rgba(0,0,0,0.7); background:#fff; cursor:pointer; outline:none; }
.ver-select:hover { border-color:#1F80A0; }
.detail-head .dh-meta { font-size:12px; color:rgba(0,0,0,0.45); margin-top:6px; display:flex; gap:18px; flex-wrap:wrap; }

/* ── Tabs ── */
.tabs { display:flex; gap:4px; padding:0 24px; border-bottom:1px solid #f0f0f0; position:sticky; top:0; background:#fff; z-index:5; }
.tab { padding:11px 14px; font-size:14px; color:rgba(0,0,0,0.65); cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-1px; }
.tab:hover { color:#1F80A0; }
.tab.active { color:#1F80A0; border-bottom-color:#1F80A0; font-weight:500; }
.tab-pane { display:none; padding:24px; }
.tab-pane.active { display:block; }
/* 数据预览 Tab: episode 列表 与 右侧内容各自滚动 (固定高度区) */
#pane-preview .preview-split { height:calc(100vh - 230px); }
#pane-preview .ep-strip { height:100%; max-height:none; }
#pane-preview .preview-main { height:100%; overflow-y:auto; padding-right:4px; }
/* episode 预览子 tab */
.ep-tabs { display:flex; gap:2px; border-bottom:1px solid #f0f0f0; margin-bottom:14px; }
.raw-head { display:flex; align-items:flex-end; justify-content:space-between; border-bottom:1px solid #f0f0f0; margin-bottom:18px; }
.raw-head .raw-tabs { border-bottom:none; margin-bottom:0; }
.raw-head .btn { margin-bottom:7px; }
.upload-box { display:flex; align-items:center; gap:10px; border:1px dashed #d0d5dd; border-radius:8px; padding:13px 16px; cursor:pointer; color:rgba(0,0,0,0.5); font-size:13px; background:#fafbfc; transition:border-color .15s,background .15s,color .15s; }
.upload-box:hover { border-color:#1F80A0; background:#f3f9fb; color:#1F80A0; }
.upload-box .up-icon { font-size:16px; line-height:1; }
.upload-box.has-file { border-style:solid; border-color:#1F80A0; color:rgba(0,0,0,0.82); background:#fff; }
.upload-box.has-file .up-icon { color:#1F80A0; }
.ep-tab { border:none; background:none; padding:8px 16px; font-size:13.5px; color:rgba(0,0,0,0.6); cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-1px; }
.ep-tab:hover { color:rgba(0,0,0,0.85); }
.ep-tab.active { color:#1F80A0; font-weight:600; border-bottom-color:#1F80A0; }
/* 标注信息: 分段时间轴 */
.seg-timeline { margin:18px 0 6px; }
.seg-row { display:flex; align-items:center; gap:8px; margin:8px 0; }
.seg-badge { width:22px; height:22px; border-radius:50%; background:#eef3f8; color:#1F80A0; font-size:11px; font-weight:600; display:flex; align-items:center; justify-content:center; flex:0 0 auto; }
.seg-track { flex:1; display:flex; height:14px; border-radius:4px; overflow:hidden; gap:2px; background:#f5f5f5; }
.seg { height:100%; display:flex; align-items:center; justify-content:center; font-size:11px; color:#fff; overflow:hidden; white-space:nowrap; cursor:pointer; transition:filter .12s; }
.seg:hover { filter:brightness(1.06); }
.anno-cap { font-size:14px; font-weight:600; color:rgba(0,0,0,0.8); margin:18px 0 4px; }
.anno-table { width:100%; border-collapse:collapse; margin-top:8px; font-size:13px; }
.anno-table th { text-align:left; padding:9px 12px; color:rgba(0,0,0,0.45); font-weight:500; border-bottom:1px solid #f0f0f0; }
.anno-table td { padding:9px 12px; border-bottom:1px solid #f7f7f7; color:rgba(0,0,0,0.8); }
.anno-table tr:hover td { background:#fafcfd; }
.anno-table .ann-parent td { font-weight:600; background:#fafafa; }
.anno-table .ann-caret { color:rgba(0,0,0,0.4); margin-right:8px; font-size:11px; }
.anno-table .ann-num { display:inline-block; width:20px; height:20px; border-radius:50%; background:#f0f2f5; text-align:center; line-height:20px; font-size:11px; color:rgba(0,0,0,0.5); margin-right:8px; }

/* ── Descriptions (key-value) ── */
.desc-grid { display:grid; grid-template-columns:max-content 1fr; gap:0; border:1px solid #f0f0f0; border-radius:8px; overflow:hidden; }
.desc-grid .dk { background:#fafafa; padding:10px 16px; font-size:13px; color:rgba(0,0,0,0.45); border-bottom:1px solid #f0f0f0; border-right:1px solid #f0f0f0; white-space:nowrap; }
.desc-grid .dv { padding:10px 16px; font-size:13px; color:rgba(0,0,0,0.85); border-bottom:1px solid #f0f0f0; }

/* ── Camera + curve preview ── */
.camera-row { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-bottom:16px; }
.camera-cell { position:relative; background:#141414; height:150px; border-radius:8px; display:flex; align-items:center; justify-content:center; color:rgba(255,255,255,0.35); flex-direction:column; gap:6px; font-size:12px; }
.camera-cell .cam-label { position:absolute; top:8px; left:8px; background:rgba(0,0,0,0.6); color:#fff; padding:2px 8px; border-radius:4px; font-size:11px; }
.play-bar { display:flex; align-items:center; gap:12px; background:#fafafa; border:1px solid #f0f0f0; border-radius:8px; padding:8px 14px; margin-bottom:16px; font-size:13px; color:rgba(0,0,0,0.65); }
.play-bar .play-btn { width:30px; height:30px; border-radius:50%; background:#1F80A0; color:#fff; display:flex; align-items:center; justify-content:center; cursor:pointer; }
.play-bar .track { flex:1; height:6px; background:#e8e8e8; border-radius:3px; position:relative; }
.play-bar .track .cursor { position:absolute; left:38%; top:-3px; width:2px; height:12px; background:#1F80A0; }
.kbd { display:inline-block; padding:1px 6px; border:1px solid #d9d9d9; border-bottom-width:2px; border-radius:4px; font-size:11px; color:rgba(0,0,0,0.55); background:#fafafa; }
.frame-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:8px; }
.frame-thumb { aspect-ratio:4/3; background:linear-gradient(135deg,#2b3a4a,#1a2530); border-radius:6px; display:flex; align-items:center; justify-content:center; color:rgba(255,255,255,0.4); font-size:11px; position:relative; }
.frame-thumb .ft-tag { position:absolute; bottom:4px; left:4px; background:rgba(0,0,0,0.55); color:#fff; padding:0 5px; border-radius:3px; font-size:10px; }

/* ── Episode strip (lerobot 风格) ── */
.preview-split { display:flex; gap:16px; align-items:flex-start; }
.ep-strip { width:150px; min-width:150px; max-height:600px; overflow-y:auto; border:1px solid #f0f0f0; border-radius:8px; }
.ep-strip .ep-head { padding:9px 14px; font-size:11px; color:rgba(0,0,0,0.45); text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid #f5f5f5; position:sticky; top:0; background:#fff; }
.ep-item { padding:8px 14px; font-size:13px; color:rgba(0,0,0,0.65); cursor:pointer; border-left:2px solid transparent; border-bottom:1px solid #fafafa; }
.ep-item:hover { background:#fafafa; }
.ep-item.active { background:#e6f4f8; color:#1F80A0; border-left-color:#1F80A0; font-weight:500; }
.ep-item .er { font-size:11px; color:rgba(0,0,0,0.35); margin-top:2px; }
.preview-main { flex:1; min-width:0; }
.lang-instr { background:#fafafa; border:1px solid #f0f0f0; border-radius:8px; padding:13px 18px; margin:16px 0; }
.lang-instr .li-label { font-size:11px; color:rgba(0,0,0,0.45); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px; }
.lang-instr .li-text { font-size:16px; color:rgba(0,0,0,0.85); }
.combine-btn { float:right; font-size:12px; color:rgba(0,0,0,0.55); border:1px solid #d9d9d9; border-radius:6px; padding:3px 10px; cursor:pointer; }
.combine-btn:hover { border-color:#1F80A0; color:#1F80A0; }

/* ── 轨迹工具条 + 视图 ── */
.traj-bar { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:12px 0; border-bottom:1px solid #f0f0f0; margin-bottom:12px; }
.traj-tabs { display:flex; gap:6px; align-items:center; }
.tbtn { padding:5px 14px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; font-size:13px; cursor:pointer; color:rgba(0,0,0,0.65); }
.tbtn:hover { border-color:#1F80A0; color:#1F80A0; }
.tbtn.on { background:#1F80A0; border-color:#1F80A0; color:#fff; }
.tbar-sep { width:1px; height:18px; background:#e8e8e8; margin:0 4px; }
.traj-play { display:flex; gap:8px; }
.traj-play .pbtn { width:30px; height:30px; border:1px solid #e0e0e0; border-radius:6px; background:#fff; cursor:pointer; color:#1F80A0; display:flex; align-items:center; justify-content:center; font-size:14px; }
.traj-play .pbtn:hover { border-color:#1F80A0; }
.traj-legend { display:flex; gap:14px; font-size:12px; color:rgba(0,0,0,0.6); }
.traj-legend i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:4px; vertical-align:middle; }
.traj-grid { width:100%; border-collapse:collapse; table-layout:fixed; }
.traj-grid th { font-size:13px; font-weight:600; color:rgba(0,0,0,0.8); text-align:center; padding:6px 10px; border-bottom:1px solid #f0f0f0; }
.traj-grid th.rlab, .traj-grid td.rlab { width:34px; }
.traj-grid td { padding:3px 10px; border-bottom:1px solid #fafafa; vertical-align:middle; }
.traj-grid td.rlab { font-size:12px; color:rgba(0,0,0,0.45); text-align:center; }
.traj-grid { height:100%; }
.spark { width:100%; height:100%; min-height:18px; display:block; }
.base-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; height:100%; }
.base-card { border:1px solid #f0f0f0; border-radius:8px; padding:14px; height:100%; box-sizing:border-box; }
.base-card canvas { width:100% !important; height:100% !important; }
/* 切 tab 时下方区域定高, 内部图表随容器拉伸填满 */
.traj-views { height:340px; overflow:hidden; }
.traj-views .tview { height:100%; }
.moz-view { display:flex; flex-direction:column; }
/* ── 3D Replay ── */
.moz-stage { position:relative; flex:1; min-height:0; border:1px solid #f0f0f0; border-radius:8px; overflow:hidden; background:#fbfcfd; }
.moz-floor { position:absolute; left:50%; top:58%; width:1400px; height:1400px; margin-left:-700px;
  transform:translateY(-34%) perspective(720px) rotateX(60deg);
  background-image:linear-gradient(#e3e8ee 1px,transparent 1px),linear-gradient(90deg,#e3e8ee 1px,transparent 1px);
  background-size:50px 50px; }
.moz-axis-y { position:absolute; left:54%; top:40%; color:#52c41a; font-size:13px; }
.moz-robot { position:absolute; left:50%; top:48%; transform:translate(-50%,-60%); z-index:2; }
.moz-info-wrap { position:absolute; right:14px; top:14px; width:300px; z-index:3; }
.moz-info { background:#fff; border:1px solid #e8eef3; border-radius:10px; padding:12px 14px; box-shadow:0 4px 16px rgba(0,0,0,0.06); max-height:420px; overflow-y:auto; }
.moz-info-wrap.collapsed .moz-info { display:none; }
.moz-collapse { position:absolute; left:-26px; top:8px; width:24px; height:38px; border:1px solid #d9e3ea; border-right:none; border-radius:8px 0 0 8px; background:#fff; color:#1F80A0; cursor:pointer; font-size:14px; }
.moz-collapse:hover { background:#f0f9fb; }
.mz-row { margin-bottom:9px; }
.mz-k { font-size:12px; color:rgba(0,0,0,0.55); margin-bottom:3px; }
.mz-v { font-size:12px; font-family:monospace; color:rgba(0,0,0,0.82); border:1px solid #eef1f4; border-radius:6px; padding:5px 8px; background:#fafbfc; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.traj-slider { width:100%; margin-top:16px; accent-color:#1F80A0; }

/* ── 可视化分析 (标题层级: L1 区块 > L2 模块 > L3 子标题 > L4 图表) ── */
.va-section { margin-top:0; padding-top:0; }
.va-title, .va-h { font-size:15px; font-weight:600; color:rgba(0,0,0,0.82); margin:28px 0 14px; padding-bottom:8px; border-bottom:1px solid #f0f0f0; }
.va-title { margin-top:6px; }
.va-sub { font-size:13px; font-weight:600; color:rgba(0,0,0,0.6); margin:16px 0 6px; }
.va-ct { font-size:12px; font-weight:400; color:rgba(0,0,0,0.45); margin-bottom:5px; }
.va-box { height:190px; }
.va-box-lg { height:210px; margin-bottom:12px; }
.va-box canvas { width:100% !important; height:100% !important; }
.va-grid2 { display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-bottom:18px; }
.va-trail { height:380px; border:1px solid #f0f0f0; border-radius:8px; background:#fff; }
.va-trail canvas { width:100%; height:100%; display:block; }
.va-trailbar { display:flex; gap:8px; margin-bottom:8px; justify-content:flex-end; }
.va-trailfoot { display:flex; justify-content:space-between; align-items:center; margin-top:8px; }
.va-legend2 { display:flex; gap:16px; font-size:12px; color:rgba(0,0,0,0.6); }
.va-legend2 i { display:inline-block; width:14px; height:3px; border-radius:2px; margin-right:5px; vertical-align:middle; }
.va-armtoggle { display:flex; gap:6px; margin-bottom:14px; }
.va-params { background:#fafbfc; border:1px solid #f0f0f0; border-radius:8px; padding:10px 14px; font-size:13px; color:rgba(0,0,0,0.7); margin-bottom:14px; }
.va-params input { accent-color:#1F80A0; vertical-align:middle; }

/* ── Progress ── */
.progress-bar { height:6px; background:#f0f0f0; border-radius:100px; overflow:hidden; width:140px; display:inline-block; vertical-align:middle; }
.progress-bar-fill { height:100%; border-radius:100px; background:#1F80A0; }
.progress-bar-fill.warn { background:#faad14; }
.progress-bar-fill.fail { background:#ff4d4f; }

/* ── Doctor banner ── */
.doctor-banner { padding:12px 18px; border-radius:8px; font-size:14px; margin-bottom:16px; display:flex; align-items:center; gap:10px; }
.doctor-banner.pass { background:#f6ffed; border:1px solid #b7eb8f; color:#389e0d; }
.doctor-banner.warn { background:#fffbe6; border:1px solid #ffe58f; color:#d48806; }
.doctor-banner.fail { background:#fff2f0; border:1px solid #ffccc7; color:#cf1322; }
.check-row { display:flex; align-items:center; gap:12px; padding:10px 14px; border:1px solid #f0f0f0; border-radius:8px; margin-bottom:8px; font-size:13px; }
.check-row .badge { font-size:11px; font-weight:600; padding:1px 8px; border-radius:4px; min-width:42px; text-align:center; }
.check-row .badge.pass { color:#389e0d; background:#f6ffed; }
.check-row .badge.warn { color:#d48806; background:#fffbe6; }
.check-row .badge.fail { color:#cf1322; background:#fff2f0; }
.check-row .cname { font-weight:500; color:rgba(0,0,0,0.85); min-width:230px; }
.check-row .cdesc { color:rgba(0,0,0,0.45); }
.check-row .check-pct { margin-left:auto; display:flex; align-items:center; gap:8px; white-space:nowrap; }
.check-row .cp-bar { width:84px; height:6px; background:#f0f0f0; border-radius:3px; overflow:hidden; }
.check-row .cp-bar i { display:block; height:100%; border-radius:3px; }
.check-row .cp-bar.ok i { background:#52c41a; }
.check-row .cp-bar.warn i { background:#faad14; }
.check-row .cp-bar.bad i { background:#ff4d4f; }
.check-row .cp-num { font-size:12px; color:rgba(0,0,0,0.55); min-width:34px; text-align:right; }
.drawer.qp-drawer { width:1200px; max-width:92vw; }
.qp-wrap .ep-strip { display:none; }
.qp-wrap .va-section { display:none; }
.qp-wrap .preview-split { display:block; }
.qp-wrap .preview-main { padding:0; }
.sched-badge { display:inline-flex; align-items:center; justify-content:center; min-width:22px; height:22px; padding:0 6px; border-radius:11px; background:#e6f4f8; color:#1F80A0; font-size:12px; font-weight:600; cursor:default; }
.sch-group { border:1px solid #f0f0f0; border-radius:8px; padding:6px 12px; margin-bottom:10px; background:#fafbfc; }
.sch-group-head { display:flex; align-items:center; font-size:12px; font-weight:600; color:rgba(0,0,0,0.65); padding:6px 0 2px; }
.sch-group-head .sch-del { margin-left:auto; color:#bfbfbf; cursor:pointer; font-weight:400; }
.sch-group-head .sch-del:hover { color:#ff4d4f; }
.sch-group .param-table td { border-bottom:none; padding:5px 0; }
.param-mode { display:inline-flex; border:1px solid #e2e4e8; border-radius:6px; overflow:hidden; margin-bottom:10px; }
.param-mode .pm-btn { border:none; background:#fff; padding:4px 12px; font-size:12.5px; cursor:pointer; color:rgba(0,0,0,0.6); }
.param-mode .pm-btn.active { background:#1F80A0; color:#fff; }
.proc-params-area { height:240px; overflow-y:auto; }
.ds-hint { background:#f3f9fb; border:1px solid #cfe4ec; border-radius:8px; padding:10px 14px; font-size:13px; color:rgba(0,0,0,0.7); line-height:1.6; margin-bottom:16px; }
.ds-hint a { color:#1F80A0; }

/* ── Recipe bars ── */
.recipe-row { display:flex; align-items:center; gap:12px; margin-bottom:10px; font-size:13px; }
.recipe-row .rname { width:160px; color:rgba(0,0,0,0.85); }
.recipe-row .rbar { flex:1; height:22px; background:#f5f5f5; border-radius:4px; overflow:hidden; position:relative; }
.recipe-row .rbar .fill { height:100%; background:#1F80A0; display:flex; align-items:center; padding-left:8px; color:#fff; font-size:12px; }

/* ── 标签构成 饼图 (一行三个) ── */
.lvl-sel { float:right; height:28px; font-size:12px; border:1px solid #e2e4e8; border-radius:6px; padding:0 28px 0 10px; color:rgba(0,0,0,0.7); background:#fff; cursor:pointer; -webkit-appearance:none; appearance:none; background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' stroke='%23999' stroke-width='1.4' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>"); background-repeat:no-repeat; background-position:right 10px center; }
.lvl-sel:hover { border-color:#1F80A0; }
.pie-row { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }
.pie-box canvas { max-width:100%; }
.pie-cell { border:1px solid #f0f0f0; border-radius:8px; padding:12px 12px 8px; }
.pie-title { text-align:center; font-weight:600; font-size:13px; color:rgba(0,0,0,0.75); margin-bottom:6px; }
.pie-box { position:relative; height:200px; }
.pie-legend { width:100%; border-collapse:collapse; margin-top:10px; font-size:12px; }
.pie-legend td { padding:4px 4px; border-bottom:1px solid #fafafa; color:rgba(0,0,0,0.72); }
.pie-legend td.pct { text-align:right; color:rgba(0,0,0,0.45); white-space:nowrap; }
.pie-legend i { display:inline-block; width:9px; height:9px; border-radius:2px; margin-right:6px; vertical-align:middle; }
@media (max-width:1100px){ .pie-row { grid-template-columns:1fr; } }

/* ── 标签构成 树 ── */
.tagtree-grp { font-size:13px; font-weight:600; color:#1F80A0; margin:16px 0 8px; display:flex; align-items:center; gap:6px; }
.tagtree-grp .caret-d { font-size:10px; color:rgba(0,0,0,0.3); }
.tagtree-row { display:flex; align-items:center; gap:12px; margin-bottom:8px; padding-left:20px; font-size:13px; }
.tagtree-row .ttname { width:120px; color:rgba(0,0,0,0.75); }

/* ── Wizard steps ── */
.steps { display:flex; gap:0; margin-bottom:24px; }
.step { flex:1; text-align:center; position:relative; padding:8px 0; }
.step .sn { width:28px; height:28px; border-radius:50%; background:#f0f0f0; color:rgba(0,0,0,0.45); display:inline-flex; align-items:center; justify-content:center; font-size:13px; font-weight:600; }
.step.active .sn { background:#1F80A0; color:#fff; }
.step.done .sn { background:#e6f4f8; color:#1F80A0; }
.step .st { font-size:13px; color:rgba(0,0,0,0.65); margin-top:6px; }
.step.active .st { color:#1F80A0; font-weight:500; }
.step::after { content:''; position:absolute; top:21px; left:60%; width:80%; height:1px; background:#f0f0f0; }
.step:last-child::after { display:none; }

/* ── Operator cards ── */
.op-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; }
.op-card { background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:16px 18px; transition:all 0.2s; }
.op-card:hover { border-color:#1F80A0; box-shadow:0 2px 10px rgba(31,128,160,0.1); }
.op-card .op-name { font-size:15px; font-weight:600; color:rgba(0,0,0,0.85); margin-bottom:4px; display:flex; align-items:center; gap:8px; }
.op-card .op-script { font-size:12px; color:#1F80A0; background:#e6f4f8; padding:1px 6px; border-radius:4px; font-family:monospace; }
.op-card .op-desc { font-size:13px; color:rgba(0,0,0,0.55); margin:8px 0; line-height:1.5; }
.op-card .op-params { font-size:12px; color:rgba(0,0,0,0.35); font-family:monospace; }

/* ── DAG / 工作流画布 ── */
.dag { display:flex; align-items:center; gap:8px; flex-wrap:wrap; padding:18px; background:#fafafa; border:1px solid #f0f0f0; border-radius:8px; }
.dag-node { background:#fff; border:1px solid #8dcde0; border-radius:8px; padding:10px 14px; font-size:13px; color:rgba(0,0,0,0.85); text-align:center; min-width:110px; }
.dag-node .dn-cat { font-size:11px; color:#1F80A0; }
.dag-arrow { color:#bfbfbf; font-size:18px; }

/* ── Workflow canvas (画布编辑器) ── */
.wf-topbar { display:flex; align-items:center; justify-content:space-between; background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:10px 16px; margin-bottom:12px; }
.wf-title { display:flex; align-items:center; gap:10px; font-size:16px; font-weight:600; color:rgba(0,0,0,0.85); }
.wf-title .back { color:rgba(0,0,0,0.45); text-decoration:none; font-size:18px; }
.wf-tabs { display:flex; gap:4px; }
.wf-tab { padding:5px 14px; border-radius:6px; font-size:14px; cursor:pointer; color:rgba(0,0,0,0.65); }
.wf-tab.active { background:#e6f4f8; color:#1F80A0; font-weight:500; }
.wf-actions { display:flex; gap:8px; }
.wf-effective-tag { display:inline-flex; align-items:center; height:22px; padding:0 8px; border-radius:11px; background:#edf8ef; color:#4b9b5f; font-size:11px; font-weight:500; white-space:nowrap; }
/* ---- 自由画布 (free-form DAG canvas) ---- */
.wf-stage { display:flex; gap:0; height:calc(100vh - 200px); }
.wf-canvas { position:relative; flex:1; background:#fafbfc; background-image:radial-gradient(#e1e4e8 1px, transparent 1px); background-size:18px 18px; border:1px solid #f0f0f0; border-radius:8px; overflow:hidden; outline:none; }
.wf-pan { position:absolute; left:0; top:0; transform-origin:0 0; }
.wf-edges { position:absolute; left:0; top:0; width:4000px; height:3000px; overflow:visible; pointer-events:none; z-index:1; }
.wf-edges path.edge { pointer-events:stroke; cursor:pointer; }
.wf-node { position:absolute; width:240px; box-sizing:border-box; background:#fff; border:1px solid #e8e8e8; border-radius:10px; box-shadow:0 2px 10px rgba(0,0,0,0.06); z-index:2; user-select:none; }
.wf-node.sel { box-shadow:0 0 0 2px rgba(31,128,160,.12),0 4px 16px rgba(31,128,160,.18); }
.wf-selection-box { display:none; position:absolute; z-index:6; box-sizing:border-box; border:1px solid #1F80A0; background:rgba(31,128,160,.10); pointer-events:none; }
.wf-selection-box.active { display:block; }
.wf-node-head { display:flex; align-items:center; gap:8px; padding:11px 13px; font-weight:600; font-size:14px; color:rgba(0,0,0,0.85); border-bottom:1px solid #f5f5f5; cursor:move; }
.wf-node-del { margin-left:auto; color:rgba(0,0,0,0.25); cursor:pointer; font-size:16px; line-height:1; padding:0 2px; }
.wf-node-del:hover { color:#ff4d4f; }
.wf-node-ic { width:30px; height:30px; border-radius:8px; background:#e6f4f8; color:#1F80A0; display:flex; align-items:center; justify-content:center; font-size:12px; flex:none; }
.wf-node-ic svg { width:17px; height:17px; fill:none; stroke:currentColor; stroke-width:1.9; stroke-linecap:round; stroke-linejoin:round; }
.wf-node-row { display:flex; padding:6px 13px; font-size:12px; align-items:center; }
.wf-node-row .k { color:rgba(0,0,0,0.4); width:40px; flex:none; }
.wf-node-row .v { color:rgba(0,0,0,0.75); flex:1; text-align:right; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.wf-port { position:absolute; top:50%; width:13px; height:13px; margin-top:-6.5px; border-radius:50%; background:#fff; border:2px solid #36967e; cursor:crosshair; z-index:3; }
.wf-port:hover { border-color:#247d68; background:#e9f7f2; }
.wf-port.in { left:-7px; }
.wf-port.out { right:-7px; }
.wf-empty { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; color:rgba(0,0,0,0.3); gap:10px; z-index:0; }
.wf-toolbar { position:absolute; left:16px; bottom:16px; display:flex; align-items:center; gap:6px; background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:6px 10px; box-shadow:0 2px 8px rgba(0,0,0,0.08); z-index:4; }
.wf-toolbar .zbtn { width:26px; height:26px; border:none; background:none; cursor:pointer; color:rgba(0,0,0,0.55); border-radius:5px; font-size:15px; }
.wf-toolbar .zbtn:hover { background:#f5f5f5; }
.wf-toolbar .zlvl { font-size:13px; color:rgba(0,0,0,0.65); min-width:42px; text-align:center; }
.wf-toolbar .sep { width:1px; height:18px; background:#f0f0f0; margin:0 4px; }
/* ---- 右侧节点配置面板 ---- */
.wf-config { width:0; flex:none; background:#fff; border:1px solid #f0f0f0; border-left:none; border-radius:0 8px 8px 0; overflow:hidden; transition:width 0.18s; display:flex; flex-direction:column; }
.wf-config.open { width:340px; border-left:1px solid #f0f0f0; }
.wf-config.open.human-mode { width:min(520px,46vw); }
.wf-config-head { display:flex; align-items:center; justify-content:space-between; padding:14px 16px; border-bottom:1px solid #f5f5f5; font-size:15px; }
.wf-config-body { flex:1; overflow:auto; padding:6px 16px 16px; }
.wf-cfg-sec { font-size:13px; font-weight:600; color:rgba(0,0,0,0.85); margin:16px 0 6px; padding-left:8px; border-left:3px solid #1F80A0; }
.wf-cfg-row { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; padding:7px 0; font-size:13px; border-bottom:1px dashed #f5f5f5; }
.wf-cfg-row > span:first-child { color:rgba(0,0,0,0.45); flex:none; }
.wf-cfg-row.lft { justify-content:flex-start; }
.wf-cfg-row.lft > span:first-child { width:62px; }
.wf-cfg-row.lft > :last-child { flex:1; text-align:left; }
.wf-cfg-col { padding:7px 0; font-size:13px; border-bottom:1px dashed #f5f5f5; }
.wf-cfg-col > span { color:rgba(0,0,0,0.45); display:block; margin-bottom:5px; }
.wf-cfg-code { margin:0; background:#1e1e1e; color:#d4d4d4; font-family:'SF Mono',Menlo,monospace; font-size:11.5px; line-height:1.55; padding:8px 10px; border-radius:6px; white-space:pre-wrap; word-break:break-all; }
.wf-cfg-sec { display:flex; align-items:center; gap:8px; }
.wf-advanced-toggle { margin-left:auto; display:inline-flex; align-items:center; gap:8px; color:rgba(0,0,0,0.58); font-size:12px; font-weight:400; cursor:pointer; }
.wf-advanced-toggle .switch { flex:none; }
.wf-sec-tag { font-weight:400; font-size:11px; padding:1px 7px; border-radius:4px; }
.wf-sec-tag.ro { color:rgba(0,0,0,0.4); background:#f0f0f0; }
.wf-sec-tag.ed { color:#1F80A0; background:#e6f4f8; }
.wf-sec-link { margin-left:auto; font-size:12px; color:#1F80A0; cursor:pointer; font-weight:400; }
.wf-param-sub { display:flex; align-items:center; gap:8px; font-size:12px; color:rgba(0,0,0,0.55); margin:6px 0 2px; }
.wf-param { padding:8px 0; border-bottom:1px dashed #f5f5f5; }
.wf-param-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:5px; }
.wf-param-k { font-family:'SF Mono',Menlo,monospace; font-size:12px; color:rgba(0,0,0,0.78); }
.wf-param-src { font-size:11px; border:1px solid #e8e8e8; border-radius:4px; padding:1px 4px; outline:none; cursor:pointer; background:#fafafa; color:rgba(0,0,0,0.45); }
.wf-param-src.ov { color:#1F80A0; background:#e6f4f8; border-color:#bfe0ec; }
.wf-param-src.rf { color:#9b59b6; background:#f6edfa; border-color:#e3cdee; }
.wf-param-v { width:100%; box-sizing:border-box; height:30px; padding:3px 9px; border:1px solid #d9d9d9; border-radius:6px; outline:none; font-size:12.5px; font-family:'SF Mono',Menlo,monospace; }
.wf-param-v:focus { border-color:#1F80A0; }
.fp-key, .fp-val { width:100%; box-sizing:border-box; height:30px; padding:3px 8px; border:1px solid #d9d9d9; border-radius:6px; outline:none; font-family:'SF Mono',Menlo,monospace; font-size:12px; }
.fp-key:focus, .fp-val:focus { border-color:#1F80A0; }
.fp-key:disabled, .fp-val:disabled { background:#f5f5f5; color:rgba(0,0,0,0.4); cursor:not-allowed; }
.param-table { width:100%; border-collapse:collapse; }
.param-table td { padding:7px 0; border-bottom:1px dashed #f5f5f5; vertical-align:top; }
.param-table td.pk { width:120px; padding:13px 12px 0 0; color:rgba(0,0,0,0.6); font-size:13px; }
.param-table input, .param-table select { width:100%; box-sizing:border-box; height:32px; padding:4px 9px; border:1px solid #d9d9d9; border-radius:6px; outline:none; font-size:13px; background:#fff; }
.param-table input:focus, .param-table select:focus { border-color:#1F80A0; }
.param-table input:disabled { background:#f5f5f5; color:rgba(0,0,0,0.4); cursor:not-allowed; }
.param-table .hint { margin-top:4px; }
.switch { position:relative; display:inline-block; width:40px; height:22px; vertical-align:middle; }
.switch input { opacity:0; width:0; height:0; }
.switch .slider { position:absolute; cursor:pointer; inset:0; background:#bfbfbf; border-radius:22px; transition:0.2s; }
.switch .slider::before { content:''; position:absolute; height:16px; width:16px; left:3px; bottom:3px; background:#fff; border-radius:50%; transition:0.2s; }
.switch input:checked + .slider { background:#1F80A0; }
.switch input:checked + .slider::before { transform:translateX(18px); }
.foot-check { margin-right:auto; display:flex; align-items:center; gap:6px; font-size:13px; color:rgba(0,0,0,0.65); cursor:pointer; }
.foot-check input { cursor:pointer; }
.wf-config-foot { display:flex; gap:8px; justify-content:flex-end; padding:12px 16px; border-top:1px solid #f5f5f5; }
.wf-edit-field { width:100%; box-sizing:border-box; height:32px; padding:4px 9px; border:1px solid #d9d9d9; border-radius:6px; outline:none; background:#fff; font-size:13px; font-family:inherit; }
textarea.wf-edit-field { min-height:64px; height:auto; resize:vertical; line-height:1.55; }
.wf-edit-field:focus { border-color:#1F80A0; box-shadow:0 0 0 2px rgba(31,128,160,.09); }
.wf-human-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.wf-human-grid .full { grid-column:1/-1; }
.wf-human-label { display:block; margin-bottom:5px; color:rgba(0,0,0,.52); font-size:12px; }
.wf-mode-tabs { display:inline-flex; padding:3px; border-radius:7px; background:#f3f5f6; margin:2px 0 10px; }
.wf-mode-tab { border:0; border-radius:5px; padding:4px 14px; background:transparent; color:rgba(0,0,0,.5); font-size:12px; cursor:pointer; }
.wf-mode-tab.active { background:#fff; color:#1F80A0; box-shadow:0 1px 4px rgba(0,0,0,.1); font-weight:600; }
.wf-condition-row { display:grid; grid-template-columns:1.18fr 1fr 24px; align-items:center; gap:6px; margin-bottom:7px; }
.wf-condition-row .wf-edit-field { min-width:0; }
.wf-ratio-rule { display:grid; grid-template-columns:1.08fr .92fr 82px 24px; align-items:center; gap:6px; margin-bottom:7px; }
.wf-ratio-rule .wf-edit-field { min-width:0; }
.wf-rule-empty { margin-bottom:8px; padding:10px 12px; border:1px dashed #dfe5e7; border-radius:7px; background:#fafbfc; color:rgba(0,0,0,.42); font-size:12px; }
.wf-row-del { width:24px; height:24px; padding:0; border:0; background:transparent; color:#bfbfbf; cursor:pointer; font-size:17px; }
.wf-row-del:hover { color:#ff4d4f; }
.wf-add-link { display:inline-flex; align-items:center; gap:3px; margin-top:3px; border:0; padding:0; background:transparent; color:#1F80A0; cursor:pointer; font-size:12px; }
.wf-component-list { display:grid; grid-template-columns:1fr 1fr; gap:7px; margin-top:9px; }
.wf-component-check { display:flex; align-items:flex-start; gap:7px; min-height:46px; padding:8px 9px; border:1px solid #edf0f1; border-radius:7px; background:#fafbfc; cursor:pointer; box-sizing:border-box; }
.wf-component-check:has(input:checked) { border-color:#add5df; background:#f3fafc; }
.wf-component-check input { margin-top:2px; accent-color:#1F80A0; }
.wf-component-check b { display:block; font-size:12px; color:rgba(0,0,0,.72); }
.wf-component-check small { display:block; margin-top:2px; color:rgba(0,0,0,.4); font-size:10px; line-height:1.35; }
.wf-reject-enable { display:flex; align-items:center; gap:8px; width:max-content; color:rgba(0,0,0,.72); font-size:13px; cursor:pointer; }
.wf-reject-enable input { margin:0; accent-color:#1F80A0; }
.wf-reject-enable:has(input:disabled) { color:rgba(0,0,0,.3); cursor:not-allowed; }
.wf-reject-hint { margin-top:7px; color:rgba(0,0,0,.4); font-size:11px; line-height:1.5; }
.wf-reject-wrap { margin-top:5px; }
.wf-operation-reject { margin-top:4px; padding-top:4px; border-top:1px dashed #edf0f1; }
.wf-reject-target-list { position:relative; margin-top:7px; }
.wf-reject-target-list .ms-trigger { width:100%; min-width:0; box-sizing:border-box; }
.wf-reject-target-list .ms-panel { left:0; right:0; width:100%; max-height:220px; box-sizing:border-box; }
.wf-reject-target-list .ms-panel label { display:flex; align-items:center; gap:8px; min-width:0; padding:7px 12px; border:0; border-radius:0; background:#fff; cursor:pointer; }
.wf-reject-target-list .ms-panel label:hover { background:#f7f9fa; }
.wf-reject-target-list .ms-panel label input { flex:none; margin:0; accent-color:#1F80A0; }
.wf-reject-target-list .ms-panel label span { overflow:hidden; color:rgba(0,0,0,.72); font-size:12px; text-overflow:ellipsis; white-space:nowrap; }
.wf-reject-empty { padding:12px; color:rgba(0,0,0,.38); font-size:12px; text-align:center; }
.wf-phase-options { display:grid; gap:10px; }
.wf-phase-option { display:flex; align-items:center; gap:12px; width:100%; padding:14px; border:1px solid #e6eaec; border-radius:9px; background:#fff; color:rgba(0,0,0,.78); text-align:left; cursor:pointer; }
.wf-phase-option:hover:not(:disabled) { border-color:#1F80A0; background:#f5fbfc; }
.wf-phase-option:disabled { color:rgba(0,0,0,.3); background:#f6f7f8; cursor:not-allowed; }
.wf-phase-option i { display:flex; align-items:center; justify-content:center; width:30px; height:30px; border-radius:50%; background:#e6f4f8; color:#1F80A0; font-style:normal; font-weight:700; }
.wf-phase-option:disabled i { background:#e8eaeb; color:#aeb5b8; }
.wf-phase-option b { display:block; font-size:14px; }
.wf-phase-option small { display:block; margin-top:3px; color:rgba(0,0,0,.4); font-size:11px; }
.wf-phase-option .state { margin-left:auto; padding:2px 7px; border-radius:10px; background:#eceff0; color:#8c969a; font-size:11px; }

/* ── Processing phase frames on the workflow canvas ── */
.wf-phase-frame { position:absolute; z-index:0; box-sizing:border-box; border:2px dashed #91b8bf; border-radius:14px; background:transparent; pointer-events:none; }
.wf-phase-label { position:absolute; top:18px; left:20px; display:flex; align-items:center; gap:9px; color:#256d78; }
.wf-phase-label i { display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:#149DAA; color:#fff; font-size:11px; font-style:normal; }
.wf-phase-label b { font-size:15px; }
.wf-phase-label small { color:rgba(0,0,0,.4); font-size:11px; font-weight:400; }
.wf-phase-port { position:absolute; left:50%; width:14px; height:14px; margin-left:-7px; border:2px solid #75aab3; border-radius:50%; background:#fff; box-sizing:border-box; }
.wf-phase-port.in { top:-8px; }
.wf-phase-port.out { bottom:-8px; }
.wf-edges path.phase-edge { stroke:#5f9fac; stroke-width:3; }
.wf-phase-terminal { position:absolute; top:50%; width:76px; height:40px; margin-top:-20px; display:flex; align-items:center; justify-content:center; box-sizing:border-box; border:1.5px solid #8fb6bd; border-radius:22px; background:#fff; color:#397783; font-size:12px; font-weight:600; pointer-events:auto; z-index:2; }
.wf-phase-terminal.input { left:24px; }
.wf-phase-terminal.output { right:24px; }
.wf-phase-terminal .wf-port { top:50%; }
.wf-node.automatic,.wf-node.human,.wf-node.acceptance,.wf-node.flow-terminal { height:104px; min-height:104px; border:1px solid #d7e1e5; background:#fff; border-radius:10px; box-shadow:0 3px 10px rgba(37,73,87,.10); }
.wf-node.automatic { border-left:5px solid #19a9d1; }
.wf-node.automatic .wf-node-ic { background:#e8f7fb; color:#168fb2; }
.wf-node.human,.wf-node.acceptance { border-left:5px solid #48a86b; }
.wf-node.human .wf-node-ic,.wf-node.acceptance .wf-node-ic { background:#eaf7ee; color:#348d56; }
.wf-node-head { min-height:52px; box-sizing:border-box; border-bottom:0; padding:14px 14px 5px; color:#315064; }
.wf-node-subtitle { padding:0 14px 15px 52px; overflow:hidden; color:#6f818a; font-size:12px; line-height:1.45; text-overflow:ellipsis; white-space:nowrap; }
.wf-node.condition { min-height:180px; height:auto; border:1px solid #d7e1e5; border-left:5px solid #ee9b32; border-radius:10px; background:#fff; box-shadow:0 3px 10px rgba(37,73,87,.10); overflow:visible; }
.wf-node.condition.sel { box-shadow:0 0 0 2px rgba(31,128,160,.12),0 4px 14px rgba(19,78,94,.12); }
.wf-condition-head { display:flex; align-items:center; gap:9px; height:56px; box-sizing:border-box; padding:11px 14px; border-bottom:1px solid #edf1f2; }
.wf-condition-head i { display:flex; align-items:center; justify-content:center; width:30px; height:30px; border-radius:8px; background:#fff3e4; color:#dc8125; font-style:normal; }
.wf-condition-head i svg { width:17px; height:17px; fill:none; stroke:currentColor; stroke-width:1.9; stroke-linecap:round; stroke-linejoin:round; }
.wf-condition-head strong { color:#26363d; font-size:13px; }
.wf-condition-branch-list { padding:0 14px 10px; }
.wf-condition-branch { position:relative; display:flex; align-items:center; justify-content:space-between; min-height:38px; border-bottom:1px solid #f1f3f4; color:#66747c; font-size:11px; }
.wf-condition-branch:last-child { border-bottom:0; }
.wf-condition-branch b { margin-right:3px; color:#34444c; font-size:11px; }
.wf-condition-branch .wf-branch-port { position:absolute; right:-22px; top:50%; width:14px; height:14px; margin-top:-7px; border:2px solid #36967e; border-radius:50%; background:#fff; box-shadow:0 0 0 3px #fff; cursor:crosshair; box-sizing:border-box; }
.wf-node.condition .wf-node-del { position:absolute; top:8px; right:9px; z-index:3; }
.wf-node.condition .wf-port.in { left:-8px; top:75px; }
.wf-node.condition .wf-port.out { display:none; }
.wf-node.condition .wf-port.branch { display:none; }
.wf-edges path.edge.no-branch { stroke:#8c969a; stroke-dasharray:6 4; }
.wf-branch-editor { border:1px solid #e6eaec; border-radius:10px; margin-bottom:12px; background:#fff; overflow:hidden; }
.wf-branch-editor-head { display:flex; align-items:center; gap:8px; padding:10px 12px; background:#f8fafb; border-bottom:1px solid #edf0f1; }
.wf-branch-editor-head b { font-size:13px; color:#2f3e46; }
.wf-branch-editor-head input { flex:1; }
.wf-branch-editor-head .wf-row-del { margin-left:auto; }
.wf-branch-rules { padding:10px 12px 4px; }
.wf-branch-rule-head { display:grid; grid-template-columns:1.05fr 88px 1.12fr 64px 24px; gap:7px; padding:0 0 6px; color:#7a898f; font-size:10.5px; }
.wf-branch-rule { display:grid; grid-template-columns:1.05fr 88px 1.12fr 64px 24px; gap:7px; align-items:center; }
.wf-branch-rule .wf-edit-field { min-width:0; }
.wf-branch-logic { position:relative; display:flex; align-items:center; justify-content:center; height:24px; color:#198da2; font-size:10px; font-weight:600; }
.wf-branch-logic::before,.wf-branch-logic::after { content:''; height:1px; background:#e3e9eb; flex:1; }
.wf-branch-logic span { display:inline-flex; align-items:center; justify-content:center; min-width:24px; height:18px; margin:0 8px; border-radius:9px; background:#eaf7f8; color:#178493; }
.wf-branch-add-condition { margin:0 12px 11px; }
.wf-fallback-box { margin-top:15px; padding:14px; border-top:1px solid #edf0f1; background:#fafbfc; color:#65747c; font-size:12px; line-height:1.6; }
.wf-fallback-box b { display:block; margin-bottom:4px; color:#33444c; font-size:14px; }
.wf-node.acceptance { border-color:#d7e1e5; border-left-color:#48a86b; background:#fff; }
.wf-node.automatic.sel,.wf-node.human.sel,.wf-node.acceptance.sel { box-shadow:0 0 0 2px rgba(31,128,160,.12),0 4px 14px rgba(19,78,94,.16); }
.wf-node .wf-node-phase { margin-left:auto; padding:1px 6px; border-radius:4px; background:#f2f5f6; color:rgba(0,0,0,.42); font-size:10px; font-weight:400; }
.wf-node.flow-terminal { width:240px; display:block; cursor:move; }
.wf-node.flow-input { border-left:5px solid #16a39a; }
.wf-node.flow-input .wf-node-ic { background:#e7f7f5; color:#11877f; }
.wf-node.flow-output { border-left:5px solid #756fd0; }
.wf-node.flow-output .wf-node-ic { background:#efedfb; color:#635bc0; }
.wf-node.flow-terminal .wf-node-head { cursor:move; }
.wf-choice-grid { display:grid; grid-template-columns:1fr 1fr; gap:7px; margin-top:8px; }
.wf-choice-grid label { display:flex; align-items:center; gap:7px; min-height:34px; box-sizing:border-box; padding:7px 9px; border:1px solid #e0e6e8; border-radius:7px; background:#fff; color:#40565e; font-size:11px; }
.wf-choice-grid label:has(input:disabled) { background:#f5f6f7; color:rgba(0,0,0,.28); cursor:not-allowed; }
.wf-choice-grid.actions { grid-template-columns:repeat(3,1fr); }
.wf-user-group-select .ms-trigger { width:100%; box-sizing:border-box; min-height:34px; height:auto; }
.wf-user-group-select .ms-label { overflow:visible; text-overflow:clip; white-space:normal; line-height:20px; padding:2px 0; }
.wf-user-group-select .ms-panel { left:0; right:0; width:100%; max-height:220px; box-sizing:border-box; }
.wf-node-type-options { display:grid; gap:10px; }
.wf-node-type-option { display:flex; align-items:center; gap:12px; width:100%; padding:14px; border:1px solid #d7e1e5; border-left-width:5px; border-radius:10px; background:#fff; color:rgba(0,0,0,.78); text-align:left; cursor:pointer; }
.wf-node-type-option:hover { border-color:#9bcbd3; background:#f7fbfb; }
.wf-node-type-option .wf-node-ic { width:30px; height:30px; border-radius:8px; display:flex; align-items:center; justify-content:center; flex:none; }
.wf-node-type-option .wf-node-ic svg { width:17px; height:17px; fill:none; stroke:currentColor; stroke-width:1.9; stroke-linecap:round; stroke-linejoin:round; }
.wf-node-type-option.human { border-left-color:#48a86b; }
.wf-node-type-option.human .wf-node-ic { background:#eaf7ee; color:#348d56; }
.wf-node-type-option.automatic { border-left-color:#19a9d1; }
.wf-node-type-option.automatic .wf-node-ic { background:#e8f7fb; color:#168fb2; }
.wf-node-type-option.condition { border-left-color:#ee9b32; }
.wf-node-type-option.condition .wf-node-ic { background:#fff3e4; color:#dc8125; }
.wf-node-type-option.human:hover { border-left-color:#48a86b; }
.wf-node-type-option.automatic:hover { border-left-color:#19a9d1; }
.wf-node-type-option.condition:hover { border-left-color:#ee9b32; }
.wf-node-type-option b { display:block; font-size:14px; }
.wf-node-type-option small { display:block; margin-top:3px; color:rgba(0,0,0,.42); font-size:11px; }
.wf-add-node-popover { display:none; position:fixed; left:16px; top:16px; z-index:320; width:min(420px,calc(100vw - 32px)); max-height:calc(100vh - 112px); box-sizing:border-box; overflow:hidden; background:#fff; border:1px solid #dfe7e9; border-radius:10px; box-shadow:0 10px 28px rgba(37,73,87,.16); }
.wf-add-node-popover.active { display:flex; flex-direction:column; }
.wf-add-node-popover-head { display:flex; align-items:center; justify-content:space-between; flex:none; padding:12px 14px; border-bottom:1px solid #edf1f2; color:#26363d; }
.wf-add-node-popover-head b { font-size:14px; }
.wf-add-node-popover-body { overflow:auto; padding:14px; }
.wf-add-node-popover-body .wf-node-type-options { margin:0; }
.wf-add-node-popover-body .wf-node-type-option,
.wf-add-node-popover-body .wf-node-type-option.human,
.wf-add-node-popover-body .wf-node-type-option.automatic,
.wf-add-node-popover-body .wf-node-type-option.condition { height:auto; min-height:0; padding:11px 10px; border:0; border-left:0; border-radius:6px; box-shadow:none; background:transparent; }
.wf-add-node-popover-body .wf-node-type-option:hover,
.wf-add-node-popover-body .wf-node-type-option.human:hover,
.wf-add-node-popover-body .wf-node-type-option.automatic:hover,
.wf-add-node-popover-body .wf-node-type-option.condition:hover { border:0; border-left:0; box-shadow:none; background:#f5fbfc; }
.wf-add-node-popover-body .op-pick { margin-bottom:2px; padding:10px 6px; border:0; border-radius:6px; background:transparent; }
.wf-add-node-popover-body .op-pick:hover { border-color:transparent; background:#f5fbfc; }
.wf-context-menu { display:none; position:absolute; z-index:20; min-width:120px; padding:4px; box-sizing:border-box; border:1px solid #dfe7e9; border-radius:8px; background:#fff; box-shadow:0 8px 22px rgba(37,73,87,.16); }
.wf-context-menu.active { display:block; }
.wf-context-menu button { display:flex; align-items:center; width:100%; height:34px; padding:0 10px; border:0; border-radius:5px; background:#fff; color:#35484f; font-size:13px; text-align:left; cursor:pointer; }
.wf-context-menu button:hover { background:#f2f8f9; color:#1F80A0; }
.wf-context-menu button.danger:hover { background:#fff3f2; color:#d4504e; }
.wf-structure-count { white-space:nowrap; }

/* ── 标签管理 树表 ── */
.tg-table td { padding:7px 16px; }
.tg-name { display:flex; align-items:center; gap:6px; }
.tg-caret { cursor:pointer; font-size:10px; color:rgba(0,0,0,0.35); transition:transform 0.15s; display:inline-block; width:14px; text-align:center; }
.tg-caret.open { transform:rotate(90deg); }
.tg-caret-none { display:inline-block; width:14px; }
.tg-dim { color:#1F80A0; font-weight:600; }
.tg-l2 { font-weight:600; color:rgba(0,0,0,0.85); }
.tg-l3 { color:rgba(0,0,0,0.6); }
.tg-en { color:rgba(0,0,0,0.3); font-size:12px; margin-left:4px; }
.tg-badge { display:inline-block; min-width:22px; text-align:center; background:#f0f0f0; border-radius:10px; padding:1px 8px; font-size:12px; color:#888; }
.tg-ops span { cursor:pointer; color:rgba(0,0,0,0.3); margin-right:12px; font-size:14px; }
.tg-ops span:hover { color:#1F80A0; }
.tg-ops .del:hover { color:#ff4d4f; }

/* ── Toast ── */
.q-toast { position:fixed; top:24px; left:50%; transform:translate(-50%,-12px); min-width:240px; background:#fff; color:rgba(0,0,0,0.85); padding:12px 18px; border-radius:10px; font-size:14px; z-index:9999; opacity:0; box-shadow:0 6px 24px rgba(0,0,0,0.12); border:1px solid #f0f0f0; border-left:4px solid #1F80A0; transition:opacity 0.25s,transform 0.25s; }
.q-toast.show { opacity:1; transform:translate(-50%,0); }

/* ── Drawer ── */
.drawer-mask { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:300; }
.drawer-mask.active { display:block; }
.drawer { position:fixed; top:0; right:0; bottom:0; width:560px; max-width:94vw; background:#fff; box-shadow:-6px 0 16px rgba(0,0,0,0.08); transform:translateX(100%); transition:transform 0.3s cubic-bezier(0.23,1,0.32,1); display:flex; flex-direction:column; z-index:301; }
.drawer-mask.active .drawer { transform:translateX(0); }
.drawer-head { padding:16px 24px; border-bottom:1px solid #f0f0f0; display:flex; justify-content:space-between; align-items:center; }
.drawer-head h3 { margin:0; font-size:16px; color:rgba(0,0,0,0.85); }
.drawer-close { cursor:pointer; color:rgba(0,0,0,0.45); font-size:18px; background:none; border:none; line-height:1; }
.drawer-close:hover { color:rgba(0,0,0,0.85); }
.drawer-body { padding:20px 24px; flex:1; overflow-y:auto; }
.drawer-foot { padding:12px 24px; border-top:1px solid #f0f0f0; display:flex; justify-content:flex-end; gap:8px; }
/* ── Modal (居中弹窗) ── */
.modal-mask { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:1500; align-items:center; justify-content:center; }
.modal-mask.active { display:flex; }
.modal-box { background:#fff; border-radius:12px; max-height:86vh; display:flex; flex-direction:column; box-shadow:0 16px 56px rgba(0,0,0,0.2); overflow:hidden; }
.q-pager { display:flex; align-items:center; justify-content:space-between; margin-top:14px; }
.q-pager .pg-btns { display:flex; gap:6px; }
.pg-btn { min-width:30px; height:30px; padding:0 8px; border:1px solid #e2e4e8; background:#fff; border-radius:6px; font-size:13px; cursor:pointer; color:rgba(0,0,0,0.7); }
.pg-btn:hover { border-color:#1F80A0; color:#1F80A0; }
.pg-btn.active { background:#1F80A0; border-color:#1F80A0; color:#fff; }
.fg { margin-bottom:14px; }
.fg label { display:block; font-size:13px; color:rgba(0,0,0,0.85); margin-bottom:5px; }
.fg label .req { color:#ff4d4f; margin-right:2px; }
.fg input, .fg select, .fg textarea { width:100%; box-sizing:border-box; padding:6px 11px; border:1px solid #d9d9d9; border-radius:8px; font-size:14px; outline:none; font-family:inherit; background:#fff; }
.fg input:focus, .fg select:focus, .fg textarea:focus { border-color:#1F80A0; box-shadow:0 0 0 2px rgba(31,128,160,0.12); }
.fg textarea { min-height:60px; resize:vertical; }
.fg .hint { font-size:12px; color:rgba(0,0,0,0.35); margin-top:3px; }
.fg-row { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
/* 新建算子抽屉: 加宽 + 表单一行一列 */
.op-drawer { width:680px; }
.op-drawer .fg-row { grid-template-columns:1fr; }
/* 脚本编辑器样式 (入口脚本 / 出入参) */
.fg textarea.code-editor { font-family:'SF Mono',Monaco,Menlo,Consolas,monospace; font-size:12.5px; background:#1e1e1e; color:#d4d4d4; border-color:#2a2a2a; line-height:1.7; tab-size:2; white-space:pre; overflow:auto; min-height:64px; }
.fg textarea.code-editor:focus { border-color:#1F80A0; box-shadow:0 0 0 2px rgba(31,128,160,0.2); }
.fg textarea.code-editor::placeholder { color:rgba(255,255,255,0.28); }
.op-pick { padding:10px 12px; border:1px solid #f0f0f0; border-radius:8px; margin-bottom:8px; cursor:pointer; transition:all 0.15s; }
.op-pick:hover { border-color:#1F80A0; background:#f7fbfc; }
.section-label { font-size:12px; color:#1F80A0; font-weight:600; margin:18px 0 12px; padding-bottom:5px; border-bottom:1px solid #f0f0f0; }
.section-label:first-child { margin-top:0; }
"""

BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} - Quanta</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/antd@4.24.16/dist/antd.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/lib/codemirror.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/theme/material-darker.min.css">
<style>""" + BASE_CSS + """</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/lib/codemirror.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/sql/sql.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/javascript/javascript.min.js"></script>
</head>
<body>
<header class="top-nav">
  <div class="tn-brand"><div class="logo-icon">Q</div><span>Quanta</span></div>
  <nav class="tn-nav">
    <a class="tn-item {{ 'active' if top=='data' }}" href="/query">数据</a>
    <a class="tn-item" href="#" onclick="toast('Demo: 训练模块占位');return false;">训练</a>
    <a class="tn-item" href="#" onclick="toast('Demo: 部署模块占位');return false;">部署</a>
    <a class="tn-item" href="#" onclick="toast('Demo: 评测模块占位');return false;">评测</a>
    <span class="tn-sep"></span>
    <a class="tn-item {{ 'active' if top=='asset' }}" href="/tags">资产</a>
    <a class="tn-item" href="#" onclick="toast('Demo: 资源模块占位');return false;">资源</a>
  </nav>
  <div class="tn-right">demo</div>
</header>
<div class="q-layout">
<aside class="q-sider">
  {% if top=='data' %}
  <nav class="nav-section">
    <div class="nav-label">数据准备</div>
    <a href="/query" class="nav-item {{ 'active' if active=='query' }}"><span class="icon">&#9906;</span><span class="nav-txt">数据查询</span></a>
    <a href="/datasets" class="nav-item {{ 'active' if active=='datasets' }}"><span class="icon">&#9776;</span><span class="nav-txt">数据集</span></a>
    <a href="/raw" class="nav-item {{ 'active' if active=='raw' }}"><span class="icon">&#9783;</span><span class="nav-txt">原始数据</span></a>
    <div class="nav-label">自动化任务</div>
    <a href="/operators" class="nav-item {{ 'active' if active=='operators' }}"><span class="icon">&#9881;</span><span class="nav-txt">算子管理</span></a>
    <a href="/pipelines" class="nav-item {{ 'active' if active=='pipelines' }}"><span class="icon">&#9783;</span><span class="nav-txt">工作流管理</span></a>
    <a href="/runs" class="nav-item {{ 'active' if active=='runs' }}"><span class="icon">&#9654;</span><span class="nav-txt">执行记录</span></a>
  </nav>
  {% elif top=='asset' %}
  <nav class="nav-section">
    <div class="nav-label">资产</div>
    <a href="/tags" class="nav-item {{ 'active' if active=='tags' }}"><span class="icon">&#9873;</span><span class="nav-txt">标签管理</span></a>
  </nav>
  {% else %}
  <nav class="nav-section"></nav>
  {% endif %}
  <div class="user-block">
    <div class="user-avatar">J</div>
    <div class="user-info"><div class="user-name">joanna.qiao</div><div class="user-role">数据工程师</div></div>
    <span class="sider-collapse-btn" onclick="toggleSider()" title="折叠/展开菜单"><span class="sc-col">&#171;</span><span class="sc-exp">&#187;</span></span>
  </div>
</aside>
<main class="q-main">
  <div class="q-content">""" + "{{ content|safe }}" + """</div>
</main>
</div>
<div class="q-toast" id="toast"></div>
<script>
function toast(msg){ var t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show'); setTimeout(function(){t.classList.remove('show');},2200); }
function resetFilters(btn){
  var root = btn.closest('.filter-bar,.q-filters');
  if(!root){ toast('Demo: 已重置'); return; }
  root.querySelectorAll('input, textarea').forEach(function(el){ el.value=''; });
  root.querySelectorAll('select').forEach(function(el){ el.selectedIndex = 0; });
  root.querySelectorAll('.ms-wrap input[type="checkbox"]').forEach(function(el){ el.checked = false; });
  root.querySelectorAll('.ms-trigger').forEach(function(el){
    var base = el.getAttribute('data-base') || '筛选';
    el.classList.remove('has-value');
    var label = el.querySelector('.ms-label');
    if(label) label.textContent = base.replace(/\\s*\\(\\d+\\)$/, '');
  });
  refreshSelectPlaceholders(root);
  toast('Demo: 已重置');
}
function queryFilters(btn){ toast('Demo: 已查询'); }
function isPlaceholderSelectValue(sel){
  if(!sel) return false;
  var opt = sel.options[sel.selectedIndex];
  if(!opt) return false;
  var txt = (opt.textContent || '').trim();
  return opt.disabled || opt.value === '' || /^请选择/.test(txt) || /^全部/.test(txt);
}
function refreshSelectPlaceholderState(sel){ sel.classList.toggle('select-empty', isPlaceholderSelectValue(sel)); }
function refreshSelectPlaceholders(root){
  (root || document).querySelectorAll('select').forEach(refreshSelectPlaceholderState);
}
document.addEventListener('DOMContentLoaded', function(){ refreshSelectPlaceholders(document); });
document.addEventListener('change', function(e){
  if(e.target && e.target.tagName === 'SELECT') refreshSelectPlaceholderState(e.target);
}, true);
function msUpdate(cb){
  var wrap=cb.closest('.ms-wrap'); var checked=wrap.querySelectorAll('input:checked'); var n=checked.length;
  var trig=wrap.querySelector('.ms-trigger'); var base=trig.getAttribute('data-base')||''; var lab=wrap.querySelector('.ms-label');
  trig.classList.toggle('has-value', n>0);
  if(!n){ lab.textContent=base; return; }
  var names=[]; checked.forEach(function(c){ names.push(c.parentNode.textContent.trim()); });
  lab.textContent=names.join(', ');
  if(lab.scrollWidth > lab.clientWidth + 1){ lab.textContent=base+' ('+n+')'; }
}
function datasetTagSyncPicker(picker){
  if(!picker || picker.classList.contains('readonly')) return;
  var chips=picker.querySelector('.dataset-tag-picker-chips');
  var selected=Array.prototype.slice.call(picker.querySelectorAll('.dataset-tag-picker-panel input:checked'));
  chips.innerHTML='';
  selected.forEach(function(cb){
    var chip=document.createElement('span');
    chip.className='dataset-tag-chip';
    chip.setAttribute('data-path',cb.value);
    var text=document.createElement('span');
    text.className='dataset-tag-chip-text';
    text.textContent=cb.value;
    var remove=document.createElement('button');
    remove.type='button';
    remove.className='dataset-tag-chip-remove';
    remove.setAttribute('aria-label','移除 '+cb.value);
    remove.textContent='×';
    remove.onclick=function(event){ datasetTagRemove(event,remove); };
    chip.appendChild(text);
    chip.appendChild(remove);
    chips.appendChild(chip);
  });
  if(!selected.length){
    var placeholder=document.createElement('span');
    placeholder.className='dataset-tag-picker-placeholder';
    placeholder.textContent='请选择或创建标签';
    chips.appendChild(placeholder);
  }
}
function datasetTagTogglePicker(event,picker){
  event.stopPropagation();
  if(!picker || picker.classList.contains('readonly')) return;
  var opening=!picker.classList.contains('open');
  document.querySelectorAll('.dataset-tag-picker.open').forEach(function(item){ item.classList.remove('open'); });
  picker.classList.toggle('open',opening);
}
function datasetTagToggleOption(checkbox){ datasetTagSyncPicker(checkbox.closest('.dataset-tag-picker')); }
function datasetTagRemove(event,button){
  event.stopPropagation();
  var picker=button.closest('.dataset-tag-picker');
  var path=button.closest('.dataset-tag-chip').getAttribute('data-path');
  picker.querySelectorAll('.dataset-tag-picker-panel input').forEach(function(cb){ if(cb.value===path) cb.checked=false; });
  datasetTagSyncPicker(picker);
}
function datasetTagSetValues(id,values){
  var picker=document.getElementById(id);
  if(!picker) return;
  values=values||[];
  picker.querySelectorAll('.dataset-tag-picker-panel input').forEach(function(cb){ cb.checked=values.indexOf(cb.value)>=0; });
  datasetTagSyncPicker(picker);
}
function psEsc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function psOpen(ctrl){ var i=ctrl.closest('.ps-wrap').querySelector('.ps-input'); if(i) i.focus(); }
function psSelectedNames(w){ return Array.prototype.map.call(w.querySelectorAll('.ps-chip'), function(c){ return c.getAttribute('data-v'); }); }
function psSearch(inp){
  var w=inp.closest('.ps-wrap');
  var pool=JSON.parse(w.getAttribute('data-pool'));
  var q=inp.value.trim().toLowerCase();
  var res=w.querySelector('.ps-results'), empty=w.querySelector('.ps-empty');
  if(!q){ w.classList.remove('open'); res.innerHTML=''; empty.style.display='none'; return; }
  w.classList.add('open');
  var sel=psSelectedNames(w);
  var hits=pool.filter(function(p){ return sel.indexOf(p.nm)<0 && ((p.nm.toLowerCase().indexOf(q)>=0)||(p.id.toLowerCase().indexOf(q)>=0)); });
  if(!hits.length){ res.innerHTML=''; empty.style.display='block'; empty.textContent='无匹配人员'; return; }
  empty.style.display='none';
  res.innerHTML=hits.map(function(p){ return '<div class="ps-opt" data-nm="'+psEsc(p.nm)+'" onclick="psSelect(this)">'+psEsc(p.nm)+' <span class="ms-uid">#'+p.id+'</span></div>'; }).join('');
}
function psSelect(opt){
  var w=opt.closest('.ps-wrap'); var nm=opt.getAttribute('data-nm'); var name=w.getAttribute('data-name');
  var chip=document.createElement('span'); chip.className='ps-chip'; chip.setAttribute('data-v',nm);
  chip.innerHTML='<span>'+psEsc(nm)+'</span><input type="hidden" name="'+name+'" value="'+psEsc(nm)+'"><i class="ps-x" onclick="psRemove(event,this)">&times;</i>';
  w.querySelector('.ps-chips').appendChild(chip);
  var inp=w.querySelector('.ps-input'); inp.value=''; psSearch(inp); inp.focus();
}
function psRemove(e, x){ e.stopPropagation(); x.closest('.ps-chip').remove(); }
document.addEventListener('click', function(e){
  document.querySelectorAll('.ps-wrap.open').forEach(function(w){ if(!w.contains(e.target)) w.classList.remove('open'); });
  document.querySelectorAll('.ms-wrap.open').forEach(function(w){ if(!w.contains(e.target)) w.classList.remove('open'); });
  document.querySelectorAll('.dataset-tag-picker.open').forEach(function(w){ if(!w.contains(e.target)) w.classList.remove('open'); });
  document.querySelectorAll('.row-act-wrap.open').forEach(function(w){ if(!w.contains(e.target)) w.classList.remove('open'); });
});
function openDrawerById(id){ document.getElementById(id).classList.add('active'); }
function closeDrawerById(id){ document.getElementById(id).classList.remove('active'); }
function qfDep(id, val){ var el=document.getElementById(id); if(el) el.classList.toggle('qf-off', val!=='yes'); }
function dsCreating(modalId){
  var box=document.querySelector('#'+modalId+' .modal-box'); if(!box) return;
  box.innerHTML='<div style="padding:46px 28px;text-align:center;">'
    +'<div style="font-size:42px;line-height:1;margin-bottom:14px;">&#9203;</div>'
    +'<h3 style="margin:0 0 8px;">数据集创建中</h3>'
    +'<div class="muted" style="font-size:13px;max-width:380px;margin:0 auto;">已提交创建任务，正在后台异步处理，可在「数据集创建进度」查看状态。</div>'
    +'<div style="margin-top:22px;display:flex;gap:10px;justify-content:center;">'
    +'<button class="btn btn-secondary" onclick="location.reload()">关闭</button>'
    +'<a href="/ds_progress" class="btn-primary btn">查看进度</a>'
    +'</div></div>';
}
function qfToggleGroup(t){ t.closest('.qf-group').classList.toggle('collapsed'); }
/* episode 预览三 tab: 轨迹信息 / 标注信息 / 可视化分析 */
function epTab(btn, prefix, which){
  var bar=btn.parentNode; bar.querySelectorAll('.ep-tab').forEach(function(b){ b.classList.remove('active'); });
  btn.classList.add('active');
  ['traj','anno','va'].forEach(function(k){ var el=document.getElementById(prefix+'_tab_'+k); if(el) el.style.display=(k===which)?'':'none'; });
}
/* 行内操作菜单 (目录 / 数据集) */
function toggleRowMenu(el){ var w=el.closest('.row-act-wrap'); var open=w.classList.contains('open'); document.querySelectorAll('.row-act-wrap.open').forEach(function(x){x.classList.remove('open');}); if(!open) w.classList.add('open'); }
function rmClose(){ document.querySelectorAll('.row-act-wrap.open').forEach(function(x){x.classList.remove('open');}); }
function openFolderEdit(name){ var m=(window._folderMeta||{})[name]||{}; var n=document.getElementById('folderEditName'); if(n)n.value=m.name||name; var idn=document.getElementById('folderEditIdent'); if(idn)idn.value=m.ident||''; var p=document.getElementById('folderEditParent'); if(p){ if(m.parent){ p.value=m.parent; } else { p.selectedIndex=0; } } openDrawerById('folderEditModal'); }
function delFolder(name){ if(confirm('确定删除空目录「'+name+'」?')){ toast('Demo: 已删除目录「'+name+'」'); } }
function openDsEdit(id){
  var m=(window._dsMeta||{})[id]||{};
  var n=document.getElementById('dsEditName'); if(n)n.value=m.name||'';
  var idn=document.getElementById('dsEditIdent'); if(idn)idn.value=m.ident||'';
  var f=document.getElementById('dsEditFolder'); if(f&&m.folder)f.value=m.folder;
  datasetTagSetValues('dsEditTags',m.tags||[]);
  openDrawerById('dsEditModal');
}
function switchTab(el, pane){
  var tabs=el.parentNode.querySelectorAll('.tab'); tabs.forEach(function(t){t.classList.remove('active');}); el.classList.add('active');
  var root=el.closest('.detail-panel')||document; root.querySelectorAll('.tab-pane').forEach(function(p){p.classList.remove('active');});
  var target=root.querySelector('#pane-'+pane); if(target) target.classList.add('active');
  if(window._charts && window._charts[pane]) window._charts[pane]();
  try{ localStorage.setItem('detailTab', pane); }catch(e){}
}
function toggleTree(el){ el.classList.toggle('collapsed'); var ch=el.nextElementSibling; if(ch&&ch.classList.contains('tree-children')) ch.classList.toggle('collapsed'); }
function toggleSider(){ document.body.classList.toggle('sider-collapsed'); try{localStorage.setItem('siderCollapsed', document.body.classList.contains('sider-collapsed')?'1':'0');}catch(e){} }
function toggleTP(el){ var p=el.closest('.tree-panel'); if(p){ p.classList.toggle('tp-collapsed'); try{localStorage.setItem('tpCollapsed', p.classList.contains('tp-collapsed')?'1':'0');}catch(e){} } }
(function(){ try{ if(localStorage.getItem('siderCollapsed')==='1') document.body.classList.add('sider-collapsed');
  if(localStorage.getItem('tpCollapsed')==='1'){ var p=document.querySelector('.tree-panel'); if(p) p.classList.add('tp-collapsed'); } }catch(e){} })();
// 重载后恢复上次选中的详情 Tab (切换 episode/数据集 不回到第一个)
// 用 DOMContentLoaded 确保此时 window._charts 已定义, 图表能正常渲染; URL 带 tab 参数时跳过
document.addEventListener('DOMContentLoaded', function(){ try{
  if(/[?&]tab=/.test(location.search)) return;
  var t=localStorage.getItem('detailTab'); if(!t) return;
  var tabs=document.querySelectorAll('.tab');
  for(var i=0;i<tabs.length;i++){ var oc=tabs[i].getAttribute('onclick')||''; if(oc.indexOf("'"+t+"'")>=0){ tabs[i].click(); break; } }
}catch(e){} });
</script>
{{ extra_script|safe if extra_script else '' }}
</body>
</html>"""


def render_page(title, content, active="", breadcrumb=None, extra_script=None, top="data"):
    return render_template_string(BASE_TEMPLATE, title=title, content=content,
                                  active=active, breadcrumb=breadcrumb, extra_script=extra_script, top=top)


# ════════════════════════════════════════════════════════════════
# Section 3: Helpers
# ════════════════════════════════════════════════════════════════

def task_name(tid):
    for t in TASKS:
        if t["id"] == tid:
            return t["name"] + " (" + t["zh"] + ")"
    return tid

def qa_html(qa):
    m = {"pass": ("qa-pass", "PASS"), "warn": ("qa-warn", "WARN"), "fail": ("qa-fail", "FAIL")}
    c, t = m.get(qa, ("qa-pass", "PASS"))
    return f'<span class="qa {c}">{t}</span>'

def ds_type_tag(t):
    m = {"train": ("tag-blue", "train"), "val": ("tag-orange", "val"), "eval-benchmark": ("tag-purple", "eval-benchmark")}
    c, txt = m.get(t, ("tag-gray", t))
    return f'<span class="tag {c}">{txt}</span>'

def get_rec(rid):
    for r in RECORDINGS:
        if r["id"] == rid:
            return r
    return None

def get_ds(did):
    for d in DATASETS:
        if d["id"] == did:
            return d
    return None

def task_instr(tid):
    m = {"t1": "Clean the whiteboard", "t2": "Tidy the desk", "t3": "Water the plant"}
    return m.get(tid, tid)

def dataset_episodes(d):
    """数据集: 展开到 episode/recording 维度 (每个 episode ← 一条原始 recording)。"""
    recs = d["recordings"]
    n = min(d["episodes"], 12)
    instr = task_instr(d["tasks"][0])
    eps = []
    for i in range(n):
        rid = recs[i % len(recs)]
        r = get_rec(rid)
        tags = rec_tag_labels(r) if r else []
        eps.append({"idx": i, "rec": rid, "length": r["frames"] if r else 1200, "instr": instr, "tags": tags})
    return eps

def recs_to_episodes(recs, instr=None):
    """把一组 recording 转成 episode 列表 (用于数据湖右侧 strip)。"""
    eps = []
    for i, r in enumerate(recs):
        eps.append({"idx": i, "rec": r["id"], "length": r["frames"],
                    "instr": instr or task_instr(r["task"]), "tags": rec_tag_labels(r)})
    return eps


def _dataset_recs(d):
    return [r for r in (get_rec(i) for i in d["recordings"]) if r]


def dataset_label_names(d):
    """Return the distinct business labels attached to a dataset's recordings."""
    return sorted({
        DATASET_TAG_PATH_BY_ID.get(tag_id, TAG_LABEL.get(tag_id, tag_id))
        for r in _dataset_recs(d)
        for tag_id in rec_tags(r)
    })


def dataset_tag_picker_html(element_id, selected_paths=None, editable=True, input_name=""):
    """Render a reusable full-path multi-select for dataset labels."""
    selected_paths = [path for path in (selected_paths or []) if path]
    selected_set = set(selected_paths)
    chips = "".join(
        f'<span class="dataset-tag-chip" data-path="{html.escape(path, quote=True)}">'
        f'<span class="dataset-tag-chip-text">{html.escape(path)}</span>'
        + (
            f'<button type="button" class="dataset-tag-chip-remove" aria-label="移除 {html.escape(path, quote=True)}" '
            'onclick="datasetTagRemove(event,this)">&times;</button>'
            if editable else ""
        )
        + '</span>'
        for path in selected_paths
    )
    placeholder = (
        '<span class="dataset-tag-picker-placeholder"'
        + (' style="display:none;"' if selected_paths else "")
        + '>请选择或创建标签</span>'
    )
    readonly_class = "" if editable else " readonly"
    arrow = '<span class="dataset-tag-picker-arrow"></span>' if editable else ""
    panel = ""
    if editable:
        option_groups = {}
        for path in DATASET_TAG_PATH_OPTIONS:
            option_groups.setdefault(path.split(" > ", 1)[0], []).append(path)
        options_html = ""
        for group_name, paths in option_groups.items():
            options_html += f'<div class="dataset-tag-picker-group">{html.escape(group_name)}</div>'
            for path in paths:
                checked = " checked" if path in selected_set else ""
                name_attr = f' name="{html.escape(input_name, quote=True)}"' if input_name else ""
                options_html += (
                    f'<label class="dataset-tag-picker-option"><input type="checkbox"{name_attr} '
                    f'value="{html.escape(path, quote=True)}"{checked} onchange="datasetTagToggleOption(this)">'
                    f'<span>{html.escape(path)}</span></label>'
                )
        panel = f'<div class="dataset-tag-picker-panel">{options_html}</div>'
    click = (
        ' onclick="datasetTagTogglePicker(event,this.closest(\'.dataset-tag-picker\'))"'
        if editable else ""
    )
    return (
        f'<div class="dataset-tag-picker{readonly_class}" id="{html.escape(element_id, quote=True)}">'
        f'<div class="dataset-tag-picker-control"{click}>'
        f'<div class="dataset-tag-picker-chips">{chips}{placeholder}</div>{arrow}</div>{panel}</div>'
    )


def dataset_prompt_composition(d):
    """数据集按 prompt(任务指令) 的帧数构成。"""
    recs = _dataset_recs(d)
    total = sum(r["frames"] for r in recs) or 1
    by = {}
    for r in recs:
        by[r["task"]] = by.get(r["task"], 0) + r["frames"]
    return [{"name": task_instr(t), "ratio": fr / total} for t, fr in sorted(by.items(), key=lambda x: -x[1])]

def dataset_tag_composition(d):
    """数据集按标签(场景/技能/质量) 的帧数构成 (标签可重叠, 占比可 >100%)。"""
    recs = _dataset_recs(d)
    total = sum(r["frames"] for r in recs) or 1
    by = {}
    for r in recs:
        for lab in rec_tag_labels(r):
            by[lab] = by.get(lab, 0) + r["frames"]
    return [{"name": lab, "ratio": fr / total} for lab, fr in sorted(by.items(), key=lambda x: -x[1])]

def comp_rows_html(items, total_frames):
    html = ""
    for it in items:
        pct = round(it["ratio"] * 100)
        fr = int(it["ratio"] * total_frames)
        html += (f'<div class="recipe-row"><div class="rname">{it["name"]}</div>'
                 f'<div class="rbar"><div class="fill" style="width:{min(max(pct,4),100)}%">{pct}%</div></div>'
                 f'<div class="muted">{fr:,}f</div></div>')
    return html or '<div class="muted">—</div>'

_TAG_GROUP = {tid: grp for tid, lab, grp in TAG_DEFS}

def dataset_tag_tree(d):
    """数据集标签按 维度(场景/技能/质量) → 标签 的树状构成 + 帧数占比。"""
    recs = _dataset_recs(d)
    total = sum(r["frames"] for r in recs) or 1
    by = {}
    for r in recs:
        for tid in rec_tags(r):
            by[tid] = by.get(tid, 0) + r["frames"]
    groups = {}
    for tid, fr in by.items():
        groups.setdefault(_TAG_GROUP.get(tid, "其他"), []).append(
            {"name": TAG_LABEL.get(tid, tid), "ratio": fr / total})
    out = []
    for grp in TAG_GROUP_ORDER:
        if grp in groups:
            out.append({"group": grp, "tags": sorted(groups[grp], key=lambda x: -x["ratio"])})
    return out

def tag_tree_html(d):
    html = ""
    for g in dataset_tag_tree(d):
        html += (f'<div class="tagtree-grp"><span class="caret-d">&#9662;</span>{g["group"]} '
                 f'<span class="muted" style="font-weight:400;font-size:12px;">{len(g["tags"])} 个标签</span></div>')
        for t in g["tags"]:
            pct = round(t["ratio"] * 100)
            fr = int(t["ratio"] * d["frames"])
            html += (f'<div class="tagtree-row"><div class="ttname">{t["name"]}</div>'
                     f'<div class="rbar"><div class="fill" style="width:{min(max(pct,4),100)}%">{pct}%</div></div>'
                     f'<div class="muted">{fr:,}f</div></div>')
    return html or '<div class="muted">—</div>'


# 通用: lerobot 风格 episode 级预览 (数据湖 + 数据集详情共用)
# 术语/结构对齐 out_182_unchecked: Episode / cam_high·cam_left_wrist·cam_right_wrist /
#   leftarm·rightarm_state(cmd)_joint_pos / LANGUAGE INSTRUCTION
def preview_block(prefix, eps):
    ep0 = eps[0]
    ep_items = ""
    for e in eps:
        ep_items += (f'<div class="ep-item {"active" if e["idx"]==0 else ""}" onclick="window.setEp_{prefix}({e["idx"]})">'
                     f'Episode {e["idx"]}<div class="er">{e["length"]:,}f · #{e["rec"]}</div></div>')
    cams = "".join(
        f'<div class="camera-cell"><span class="cam-label">{c}</span>'
        f'&#9658; 240×320</div>'
        for c in CAMERAS
    )

    # —— 标注信息: highlevel / lowlevel 分段 (demo) ——
    HL_SEGS = [
        ("接近水槽", 0.00, 6.70, "#7ed3a2"),
        ("拿起碗具", 6.70, 13.31, "#f4d35e"),
        ("水流冲洗", 13.31, 23.74, "#e8a06a"),
        ("擦拭内壁", 23.74, 38.00, "#5bc0be"),
        ("放回原位", 38.00, 52.00, "#9b8cce"),
        ("手臂复位", 52.00, 64.20, "#5aa9e6"),
    ]
    seg_total = HL_SEGS[-1][2]

    def _fmt_t(t):
        if t >= 60:
            m = int(t // 60); s = t - 60 * m
            return f"{m}:{s:05.2f}"
        return f"{t:.2f}s"

    hl_bars = "".join(
        f'<div class="seg" style="flex:{(e - s):.3f} 1 0;background:{c};" title="{lab} · {_fmt_t(s)}~{_fmt_t(e)}"></div>'
        for lab, s, e, c in HL_SEGS)
    ll_bar = '<div class="seg" style="flex:1;background:#f3b0b0;" title="Default"></div>'
    anno_rows = (f'<tr class="ann-parent"><td><span class="ann-caret">&#9662;</span>Default</td>'
                 f'<td>{_fmt_t(0)}</td><td>{_fmt_t(seg_total)}</td><td>{_fmt_t(seg_total)}</td></tr>')
    for i, (lab, s, e, c) in enumerate(HL_SEGS, 1):
        anno_rows += (f'<tr><td><span class="ann-num">{i}</span>{lab}</td>'
                      f'<td>{_fmt_t(s)}</td><td>{_fmt_t(e)}</td><td>{(e - s):.2f}s</td></tr>')
    p_left = HL_SEGS[1][1] / seg_total * 100
    p_w = (HL_SEGS[1][2] - HL_SEGS[1][1]) / seg_total * 100

    html = f"""
    <div class="preview-split">
      <div class="ep-strip" id="{prefix}_strip">
        <div class="ep-head">Episodes ({len(eps)})</div>
        {ep_items}
      </div>
      <div class="preview-main">
        <div class="ep-tabs">
          <button class="ep-tab active" onclick="epTab(this,'{prefix}','traj')">轨迹信息</button>
          <button class="ep-tab" onclick="epTab(this,'{prefix}','anno')">标注信息</button>
          <button class="ep-tab" onclick="epTab(this,'{prefix}','va')">可视化分析</button>
        </div>

        <!-- Tab① 轨迹信息: 视频 + 轨迹 -->
        <div class="ep-tabpane" id="{prefix}_tab_traj">
        <div class="camera-row">{cams}</div>

        <!-- 轨迹 -->
        <div class="traj-bar">
          <div class="traj-tabs">
            <button class="tbtn" id="{prefix}_btn_LeftArm" onclick="window.clickArm_{prefix}('LeftArm')">LeftArm</button>
            <button class="tbtn" id="{prefix}_btn_Torso" onclick="window.clickArm_{prefix}('Torso')">Torso</button>
            <button class="tbtn" id="{prefix}_btn_RightArm" onclick="window.clickArm_{prefix}('RightArm')">RightArm</button>
            <span class="tbar-sep"></span>
            <button class="tbtn" id="{prefix}_btn_Base" onclick="window.setMode_{prefix}('base')">Base</button>
            <button class="tbtn" id="{prefix}_btn_Moz" onclick="window.setMode_{prefix}('moz')">3D Replay</button>
          </div>
          <div class="traj-play">
            <button class="pbtn" onclick="toast('Demo: 播放')">&#9658;</button>
            <button class="pbtn" onclick="toast('Demo: 重置')">&#8635;</button>
          </div>
          <div class="traj-legend" id="{prefix}_legend"></div>
        </div>

        <div class="traj-views">
        <div class="tview" id="{prefix}_armView"></div>

        <div class="tview" id="{prefix}_baseView" style="display:none;">
          <div class="base-grid">
            <div class="base-card"><canvas id="{prefix}_baseSpeed" height="220"></canvas></div>
            <div class="base-card"><canvas id="{prefix}_baseXY" height="220"></canvas></div>
          </div>
        </div>

        <div class="tview moz-view" id="{prefix}_mozView" style="display:none;">
          <div style="display:flex;gap:8px;margin-bottom:10px;flex:none;">
            <button class="tbtn on">&#9673; Joint</button>
            <button class="tbtn" onclick="toast('Demo: 运动朝向')">&#9650; 运动朝向</button>
          </div>
          <div class="moz-stage">
            <div class="moz-floor"></div>
            <div class="moz-axis-y">Y</div>
            <div class="moz-robot">
              <svg width="74" height="128" viewBox="0 0 74 128">
                <ellipse cx="37" cy="120" rx="28" ry="6" fill="rgba(0,0,0,0.08)"/>
                <rect x="17" y="92" width="40" height="24" rx="5" fill="#cfd4d9"/>
                <rect x="22" y="84" width="30" height="10" rx="3" fill="#c2c8ce"/>
                <rect x="30" y="58" width="14" height="30" rx="4" fill="#c7ccd2"/>
                <rect x="25" y="36" width="24" height="26" rx="7" fill="#cdd2d8"/>
                <circle cx="37" cy="24" r="10" fill="#cdd2d8"/>
                <rect x="17" y="38" width="7" height="24" rx="3.5" fill="#bcc2c8"/>
                <rect x="50" y="38" width="7" height="24" rx="3.5" fill="#bcc2c8"/>
              </svg>
            </div>
            <div class="moz-info-wrap" id="{prefix}_mozWrap">
              <button class="moz-collapse" onclick="document.getElementById('{prefix}_mozWrap').classList.toggle('collapsed')">&raquo;</button>
              <div class="moz-info" id="{prefix}_mozInfo"></div>
            </div>
          </div>
        </div>
        </div><!-- /traj-views -->

        <input type="range" class="traj-slider" min="0" max="100" value="38" oninput="this.title=this.value+'%'">
        </div><!-- /Tab① 轨迹信息 -->

        <!-- Tab② 标注信息: 视频 + highlevel / lowlevel 分段 + 标注表 -->
        <div class="ep-tabpane" id="{prefix}_tab_anno" style="display:none;">
          <div class="camera-row">{cams}</div>
          <div class="seg-timeline">
            <div class="seg-row"><span class="seg-badge" title="highlevel 分段数">{len(HL_SEGS)}</span><div class="seg-track">{hl_bars}</div></div>
            <div class="seg-row"><span class="seg-badge">1</span><div class="seg-track">{ll_bar}</div></div>
          </div>
          <div class="anno-cap">highlevel / lowlevel 标注 <span class="muted" style="font-weight:400;font-size:12px;">点击分段查看对应标注</span></div>
          <table class="anno-table">
            <thead><tr><th>描述</th><th>开始</th><th>结束</th><th>时长</th></tr></thead>
            <tbody>{anno_rows}</tbody>
          </table>
        </div><!-- /Tab② 标注信息 -->

        <!-- Tab③ 可视化分析 -->
        <div class="ep-tabpane" id="{prefix}_tab_va" style="display:none;">
        <div class="va-section">
          <div id="{prefix}_vaStart" style="padding:2px 0;">
            <button class="btn-primary btn" onclick="window.vaStart_{prefix}()">&#9654; 开始分析</button>
            <span class="muted" style="font-size:12px;margin-left:10px;">基于位置数据计算速度/加速度、延迟与抖动, 点击后加载</span>
          </div>
          <div id="{prefix}_vaContent" style="display:none;"></div>
        </div>
        </div><!-- /Tab③ 可视化分析 -->
      </div>
    </div>
    """
    eps_json = json.dumps(eps)
    js = _PREVIEW_JS.replace("__PREFIX__", prefix).replace("__EPS__", eps_json)
    return html + js


_PREVIEW_JS = """
<script>
(function(){
  var EPS = __EPS__, PREFIX = "__PREFIX__";
  var mode = 'arm';                       // arm | base | moz
  var arms = new Set(['LeftArm','RightArm']);
  var curEp = 0, baseCharts = [], mozSrc = 'STATE';
  var ARM_ROWS = ['X','Y','Z','r','p','y','G'];
  var ARM_ORDER = ['LeftArm','Torso','RightArm'];

  // —— SVG sparkline: State(绿) + Cmd(蓝, 滞后) ——
  function spark(seed, a, r){
    var w=200, h=38, n=46, ptS=[], ptC=[];
    for(var i=0;i<n;i++){
      var x=(i/(n-1)*w);
      var vC=Math.sin(i/4 + seed*0.6 + a*1.3 + r*0.9)*0.7 + Math.sin(i/2 + r)*0.15;
      var vS=Math.sin((i-2)/4 + seed*0.6 + a*1.3 + r*0.9)*0.7 + Math.sin((i-2)/2 + r)*0.15;
      ptC.push(x.toFixed(1)+','+((0.5 - vC/2)*h*0.8 + h*0.1).toFixed(1));
      ptS.push(x.toFixed(1)+','+((0.5 - vS/2)*h*0.8 + h*0.1).toFixed(1));
    }
    return '<svg class="spark" viewBox="0 0 200 38" preserveAspectRatio="none">'+
      '<polyline points="'+ptC.join(' ')+'" fill="none" stroke="#1F80A0" stroke-width="1.2" vector-effect="non-scaling-stroke"/>'+
      '<polyline points="'+ptS.join(' ')+'" fill="none" stroke="#52c41a" stroke-width="1.2" vector-effect="non-scaling-stroke"/></svg>';
  }
  function renderArm(){
    var order = ARM_ORDER.filter(function(a){ return arms.has(a); });
    var html = '<table class="traj-grid"><thead><tr><th class="rlab"></th>';
    order.forEach(function(a){ html += '<th>'+a+'</th>'; });
    html += '</tr></thead><tbody>';
    ARM_ROWS.forEach(function(rn, ri){
      html += '<tr><td class="rlab">'+rn+'</td>';
      order.forEach(function(a, ai){
        if(rn==='G' && a==='Torso') html += '<td></td>';
        else html += '<td>'+spark(curEp, ai, ri)+'</td>';
      });
      html += '</tr>';
    });
    html += '</tbody></table>';
    document.getElementById(PREFIX+'_armView').innerHTML = html;
  }
  function renderBase(){
    baseCharts.forEach(function(c){c.destroy();}); baseCharts=[];
    var L=Array.from({length:60},function(_,i){return i;});
    function ser(sd,amp,lag){ return L.map(function(i){ return Math.sin((i-lag)/8 + sd)*amp; }); }
    var sp=document.getElementById(PREFIX+'_baseSpeed');
    if(sp) baseCharts.push(new Chart(sp,{type:'line',data:{labels:L,datasets:[
      {label:'State X',data:ser(curEp,0.4,0),borderColor:'#52c41a',borderWidth:1,pointRadius:0},
      {label:'State Y',data:ser(curEp+1,0.3,0),borderColor:'#95de64',borderWidth:1,pointRadius:0},
      {label:'Cmd X',data:ser(curEp,0.4,2),borderColor:'#1F80A0',borderWidth:1,borderDash:[3,2],pointRadius:0},
      {label:'Cmd Y',data:ser(curEp+1,0.3,2),borderColor:'#69c0ff',borderWidth:1,borderDash:[3,2],pointRadius:0}
    ]},options:{animation:false,responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{boxWidth:12,font:{size:10}}}},scales:{y:{title:{display:true,text:'Speed'},ticks:{font:{size:9}}},x:{ticks:{font:{size:9}}}}}}));
    var xy=document.getElementById(PREFIX+'_baseXY');
    if(xy){ var path=L.map(function(i){ return {x:Math.cos(i/9+curEp)*0.03+0.11, y:Math.sin(i/9+curEp)*0.03+0.11}; });
      baseCharts.push(new Chart(xy,{type:'scatter',data:{datasets:[
        {label:'State轨迹',data:path,borderColor:'#52c41a',backgroundColor:'#52c41a',showLine:true,pointRadius:0,borderWidth:1.5},
        {label:'Cmd轨迹',data:path.map(function(p){return{x:p.x+0.004,y:p.y+0.004};}),borderColor:'#1F80A0',backgroundColor:'#1F80A0',showLine:true,pointRadius:0,borderWidth:1.5,borderDash:[3,2]}
      ]},options:{animation:false,responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{boxWidth:12,font:{size:10}}}},scales:{x:{title:{display:true,text:'X(m)'},ticks:{font:{size:9}}},y:{title:{display:true,text:'Y'},ticks:{font:{size:9}}}}}}));
    }
  }
  function fmt(arr){ return arr.map(function(v){return v.toFixed(3);}).join(', '); }
  function renderMoz(){
    var d=(mozSrc==='CMD')?0.012:0, e=curEp*0.002;
    var rows=[
      ['左臂关节位置', fmt([0,0,0,0,0,0,0])],
      ['右臂关节位置', fmt([0,0,0,0,0,0,0])],
      ['左臂笛卡尔', fmt([0.215+d+e,-0.261+d,-0.052,-1.138,-1.654,-1.176])],
      ['右臂笛卡尔', fmt([-0.174-d+e,-0.292,-0.050,-1.370,-1.308,-0.968])],
      ['躯干关节位置', fmt([0,0,0,0,0,0,0])],
      ['躯干笛卡尔', fmt([-0.001,-0.000,1.094,0.360,0.069,-0.010])],
      ['底盘速度', fmt([0,0,0])],
      ['底盘位置','N/A'], ['底盘角度','N/A']
    ];
    var el=document.getElementById(PREFIX+'_mozInfo');
    if(el) el.innerHTML=rows.map(function(r){
      return '<div class="mz-row"><div class="mz-k">'+r[0]+':</div><div class="mz-v">'+r[1]+'</div></div>'; }).join('');
  }
  window['mozSrc_'+PREFIX]=function(s){
    mozSrc=s;
    var a=document.getElementById(PREFIX+'_mozState'), b=document.getElementById(PREFIX+'_mozCmd');
    if(a) a.classList.toggle('on', s==='STATE'); if(b) b.classList.toggle('on', s==='CMD');
    renderMoz();
  };
  function updateUI(){
    ['LeftArm','Torso','RightArm'].forEach(function(a){
      var b=document.getElementById(PREFIX+'_btn_'+a);
      if(b) b.classList.toggle('on', mode==='arm' && arms.has(a));
    });
    var bb=document.getElementById(PREFIX+'_btn_Base'); if(bb) bb.classList.toggle('on', mode==='base');
    var bm=document.getElementById(PREFIX+'_btn_Moz'); if(bm) bm.classList.toggle('on', mode==='moz');
    document.getElementById(PREFIX+'_armView').style.display = mode==='arm'?'':'none';
    document.getElementById(PREFIX+'_baseView').style.display = mode==='base'?'':'none';
    document.getElementById(PREFIX+'_mozView').style.display = mode==='moz'?'':'none';
    var lg=document.getElementById(PREFIX+'_legend');
    if(lg){
      if(mode==='arm') lg.innerHTML='<span><i style="background:#1F80A0"></i>CMD</span><span><i style="background:#52c41a"></i>State</span>';
      else if(mode==='moz') lg.innerHTML='<button class="tbtn '+(mozSrc==='STATE'?'on':'')+'" id="'+PREFIX+'_mozState" onclick="window.mozSrc_'+PREFIX+'(\\'STATE\\')">STATE</button>'+
                                         '<button class="tbtn '+(mozSrc==='CMD'?'on':'')+'" id="'+PREFIX+'_mozCmd" onclick="window.mozSrc_'+PREFIX+'(\\'CMD\\')">CMD</button>';
      else lg.innerHTML='';
    }
  }
  window['setMode_'+PREFIX]=function(m){ mode=m; updateUI(); if(m==='base') renderBase(); if(m==='moz') renderMoz(); };
  window['clickArm_'+PREFIX]=function(a){
    if(mode!=='arm'){ mode='arm'; arms=new Set([a]); }
    else if(arms.has(a)){ if(arms.size>1) arms.delete(a); }
    else arms.add(a);
    updateUI(); renderArm();
  };
  window['setEp_'+PREFIX]=function(i){
    curEp=i;
    var items=document.querySelectorAll('#'+PREFIX+'_strip .ep-item');
    items.forEach(function(e,idx){ e.classList.toggle('active', idx===i); });
    if(mode==='arm') renderArm(); else if(mode==='base') renderBase(); else if(mode==='moz') renderMoz();
  };
  // ════ 可视化分析 ════
  var vaArm='left', velCharts=[], latCharts=[];
  function rnd(s){ var x=Math.sin(s*12.9898)*43758.5453; return x-Math.floor(x); }
  function gam(sd,scale){ var u=rnd(sd)+0.001; return Math.max(0,(-Math.log(u))*scale*(0.5+rnd(sd*1.7+3))); }
  function gss(sd,s){ var u=rnd(sd)+1e-4,v=rnd(sd*2.1+7); return Math.sqrt(-2*Math.log(u))*Math.cos(6.2832*v)*s; }
  function samp(n,fn){ var a=[]; for(var i=0;i<n;i++)a.push(fn(i)); return a; }
  function tline(n,sd,base,amp,abs){ var a=[]; for(var i=0;i<n;i++){ var v=base+amp*Math.sin(i/9+sd)+amp*0.6*Math.sin(i/3+sd*2)+amp*0.5*(rnd(i+sd)-0.5); a.push(abs?Math.abs(v):v);} return a; }
  function destroyArr(arr){ arr.forEach(function(c){try{c.destroy();}catch(e){}}); arr.length=0; }

  function makeTime(arr,id,series,color,xl,yl){
    var ctx=document.getElementById(id); if(!ctx)return;
    arr.push(new Chart(ctx,{type:'line',data:{labels:series.map(function(_,i){return (i*0.2).toFixed(0);}),
      datasets:[{label:'State',data:series,borderColor:color,borderWidth:1,pointRadius:0}]},
      options:{animation:false,maintainAspectRatio:false,plugins:{legend:{labels:{boxWidth:12,font:{size:10}}}},
        scales:{x:{title:{display:true,text:xl},ticks:{font:{size:9},maxTicksLimit:9}},y:{title:{display:true,text:yl},ticks:{font:{size:9}}}}}}));
  }
  var mlPlugin={id:'ml',afterDraw:function(ch){ var o=ch.$ml; if(!o)return; var ca=ch.chartArea,c=ch.ctx;
    [['mean','#cf1322'],['median','#389e0d']].forEach(function(k){ var px=ca.left+(o[k[0]]-o.mn)/(o.mx-o.mn)*(ca.right-ca.left);
      c.save(); c.strokeStyle=k[1]; c.setLineDash([5,4]); c.beginPath(); c.moveTo(px,ca.top); c.lineTo(px,ca.bottom); c.stroke(); c.restore(); }); }};
  function makeHist(arr,id,samps,color,label,unit){
    var ctx=document.getElementById(id); if(!ctx)return;
    var mn=Math.min.apply(null,samps),mx=Math.max.apply(null,samps),bins=30,w=(mx-mn)/bins||1,cnt=new Array(bins).fill(0);
    samps.forEach(function(v){ var b=Math.floor((v-mn)/w); if(b<0)b=0; if(b>=bins)b=bins-1; cnt[b]++; });
    var labels=[]; for(var i=0;i<bins;i++)labels.push((mn+i*w).toFixed(2));
    var mean=samps.reduce(function(s,x){return s+x;},0)/samps.length;
    var srt=samps.slice().sort(function(a,b){return a-b;}), median=srt[Math.floor(srt.length/2)];
    var ch=new Chart(ctx,{type:'bar',data:{labels:labels,datasets:[{label:label,data:cnt,backgroundColor:color}]},
      options:{animation:false,maintainAspectRatio:false,plugins:{legend:{labels:{boxWidth:12,font:{size:10},
        generateLabels:function(c){ var d=Chart.defaults.plugins.legend.labels.generateLabels(c);
          d.push({text:'均值: '+mean.toFixed(3),fillStyle:'#cf1322'},{text:'中位数: '+median.toFixed(3),fillStyle:'#389e0d'}); return d; }}}},
        scales:{x:{title:{display:true,text:unit},ticks:{font:{size:9},maxTicksLimit:8}},y:{title:{display:true,text:'频数'},ticks:{font:{size:9}}}}},plugins:[mlPlugin]});
    ch.$ml={mean:mean,median:median,mn:mn,mx:mx}; ch.update(); arr.push(ch);
  }
  function renderVel(){
    destroyArr(velCharts);
    var sd=(vaArm==='left'?1:5)+curEp, N=400;
    makeTime(velCharts,PREFIX+'_lv_t',tline(N,sd,0.2,0.18,true),'#ff4d4f','时间 (s)','线速度 (m/s)');
    makeHist(velCharts,PREFIX+'_lv_cmd',samp(2000,function(i){return gam(i+sd,0.12);}),'#2f54eb','CMD','线速度 (m/s)');
    makeHist(velCharts,PREFIX+'_lv_st',samp(2000,function(i){return gam(i+sd,0.12);}),'#ff4d4f','State','线速度 (m/s)');
    makeTime(velCharts,PREFIX+'_av_t',tline(N,sd+1,0.7,0.6,true),'#faad14','时间 (s)','角速度 (rad/s)');
    makeHist(velCharts,PREFIX+'_av_cmd',samp(2000,function(i){return gam(i+sd+1,0.45);}),'#52c41a','CMD','角速度 (rad/s)');
    makeHist(velCharts,PREFIX+'_av_st',samp(2000,function(i){return gam(i+sd+1,0.45);}),'#faad14','State','角速度 (rad/s)');
    makeTime(velCharts,PREFIX+'_la_t',tline(N,sd+2,0,1.2,false),'#ff7875','时间 (s)','线加速度 (m/s²)');
    makeHist(velCharts,PREFIX+'_la_cmd',samp(2000,function(i){return gss(i+sd+2,1.0);}),'#91d5ff','CMD','线加速度 (m/s²)');
    makeHist(velCharts,PREFIX+'_la_st',samp(2000,function(i){return gss(i+sd+2,1.0);}),'#ff7875','State','线加速度 (m/s²)');
    makeTime(velCharts,PREFIX+'_aa_t',tline(N,sd+3,0,8,false),'#ffa940','时间 (s)','角加速度 (rad/s²)');
    makeHist(velCharts,PREFIX+'_aa_cmd',samp(2000,function(i){return gss(i+sd+3,7);}),'#95de64','CMD','角加速度 (rad/s²)');
    makeHist(velCharts,PREFIX+'_aa_st',samp(2000,function(i){return gss(i+sd+3,7);}),'#ffa940','State','角加速度 (rad/s²)');
  }
  function makeLat(arr,id,base,lag,aligned){
    var ctx=document.getElementById(id); if(!ctx)return;
    var labels=base.map(function(_,i){return (i*0.2).toFixed(0);});
    var cmd=base.map(function(v,i){return v+0.008*Math.sin(i/5);});
    var state=base.map(function(v,i){return (i-lag>=0?base[i-lag]:base[0])+0.008*Math.sin(i/5);});
    var bands=[]; if(aligned){ for(var i=0;i<base.length;i++){ if(rnd(i+curEp)>0.62) bands.push(i); } }
    var bandP={id:'bd',afterDraw:function(ch){ if(!aligned)return; var x=ch.scales.x,ca=ch.chartArea,c=ch.ctx; c.save(); c.fillStyle='rgba(255,77,79,0.10)';
      bands.forEach(function(i){ var px=x.getPixelForValue(labels[i]); c.fillRect(px-1,ca.top,3,ca.bottom-ca.top); }); c.restore(); }};
    arr.push(new Chart(ctx,{type:'line',data:{labels:labels,datasets:[
      {label:'CMD',data:cmd,borderColor:'#2f54eb',borderWidth:1,pointRadius:0},
      {label:'State',data:state,borderColor:'#ff4d4f',borderWidth:1,pointRadius:0}]},
      options:{animation:false,maintainAspectRatio:false,plugins:{legend:{labels:{boxWidth:12,font:{size:9}}}},
        scales:{x:{title:{display:true,text:'时间(秒)'},ticks:{font:{size:9},maxTicksLimit:7}},y:{title:{display:true,text:'位置 (m)'},ticks:{font:{size:9}}}}},plugins:[bandP]}));
  }
  function renderLat(){
    destroyArr(latCharts);
    var sd=10+curEp,N=400, xr=tline(N,sd,0.2,0.08,false), yr=tline(N,sd+1,-0.45,0.06,false);
    makeLat(latCharts,PREFIX+'_lat_xr',xr,2,false); makeLat(latCharts,PREFIX+'_lat_xa',xr,2,true);
    makeLat(latCharts,PREFIX+'_lat_yr',yr,2,false); makeLat(latCharts,PREFIX+'_lat_ya',yr,2,true);
  }
  // 轨迹拖尾 (custom 3D canvas, 带坐标轴)
  var trailTimer=null,trailIdx=200,trailSpeed=1,trailPath=null;
  var XR=[-0.4,0.4], YR=[-0.6,0.2], ZR=[-0.2,0.2];
  function buildTrail(){
    var n=200, Lc=[],Ls=[],Rc=[],Rs=[];
    for(var i=0;i<n;i++){
      var t=i/n;
      var lx=-0.05+0.16*Math.sin(i/14+curEp)*Math.exp(-t*0.25), ly=-0.32+0.10*Math.cos(i/18+curEp), lz=0.0+0.12*Math.sin(i/10+curEp);
      Ls.push({x:lx,y:ly,z:lz}); Lc.push({x:lx+0.012,y:ly+0.010,z:lz+0.008});
      var rx=0.10+0.16*Math.sin(i/12+curEp+1)*Math.exp(-t*0.25), ry=-0.30+0.10*Math.cos(i/16+curEp+1), rz=0.08+0.12*Math.sin(i/11+curEp+1);
      Rs.push({x:rx,y:ry,z:rz}); Rc.push({x:rx+0.012,y:ry+0.010,z:rz+0.008});
    }
    trailPath={Lc:Lc,Ls:Ls,Rc:Rc,Rs:Rs};
  }
  function drawTrail(){
    var cv=document.getElementById(PREFIX+'_trail'); if(!cv||!trailPath)return;
    var W=cv.width=cv.clientWidth||700, H=cv.height=380, c=cv.getContext('2d'); c.clearRect(0,0,W,H);
    var ex=[0.86,0.5], ey=[-0.86,0.5], ez=[0,-1], s=Math.min(W,H)*0.62, ox=W*0.46, oy=H*0.60;
    function P(x,y,z){ return [ox+(x*ex[0]+y*ey[0]+z*ez[0])*s, oy+(x*ex[1]+y*ey[1]+z*ez[1])*s]; }
    function L(a,b,col,w){ c.beginPath(); c.strokeStyle=col; c.lineWidth=w; c.moveTo(a[0],a[1]); c.lineTo(b[0],b[1]); c.stroke(); }
    var g, x, y, z;
    for(g=0;g<=4;g++){ x=XR[0]+(XR[1]-XR[0])*g/4; L(P(x,YR[0],ZR[0]),P(x,YR[1],ZR[0]),'#eef1f4',1);
                       y=YR[0]+(YR[1]-YR[0])*g/4; L(P(XR[0],y,ZR[0]),P(XR[1],y,ZR[0]),'#eef1f4',1); }
    for(g=0;g<=4;g++){ z=ZR[0]+(ZR[1]-ZR[0])*g/4; L(P(XR[0],YR[0],z),P(XR[0],YR[1],z),'#f2f5f8',1); L(P(XR[0],YR[1],z),P(XR[1],YR[1],z),'#f2f5f8',1); }
    for(g=0;g<=4;g++){ x=XR[0]+(XR[1]-XR[0])*g/4; L(P(x,YR[1],ZR[0]),P(x,YR[1],ZR[1]),'#f2f5f8',1);
                       y=YR[0]+(YR[1]-YR[0])*g/4; L(P(XR[0],y,ZR[0]),P(XR[0],y,ZR[1]),'#f2f5f8',1); }
    L(P(XR[0],YR[0],ZR[0]),P(XR[1],YR[0],ZR[0]),'#9aa3ad',1.3);
    L(P(XR[0],YR[0],ZR[0]),P(XR[0],YR[1],ZR[0]),'#9aa3ad',1.3);
    L(P(XR[0],YR[0],ZR[0]),P(XR[0],YR[0],ZR[1]),'#9aa3ad',1.3);
    c.fillStyle='#888'; c.font='11px sans-serif';
    var xe=P(XR[1],YR[0],ZR[0]); c.fillText('X (m)',xe[0]+4,xe[1]+12);
    var ye=P(XR[0],YR[1],ZR[0]); c.fillText('Y (m)',ye[0]-40,ye[1]+12);
    var ze=P(XR[0],YR[0],ZR[1]); c.fillText('Z (m)',ze[0]-36,ze[1]-2);
    c.fillStyle='#aab'; c.font='9px sans-serif';
    for(g=0;g<=4;g++){ x=XR[0]+(XR[1]-XR[0])*g/4; var px=P(x,YR[0],ZR[0]); c.fillText(x.toFixed(1),px[0]-6,px[1]+13); }
    for(g=0;g<=4;g++){ y=YR[0]+(YR[1]-YR[0])*g/4; var py=P(XR[0],y,ZR[0]); c.fillText(y.toFixed(1),py[0]-24,py[1]+9); }
    for(g=0;g<=4;g++){ z=ZR[0]+(ZR[1]-ZR[0])*g/4; var pz=P(XR[0],YR[0],z); c.fillText(z.toFixed(1),pz[0]-24,pz[1]+3); }
    function path(arr,col,up){ c.beginPath(); c.strokeStyle=col; c.lineWidth=2;
      for(var i=0;i<up&&i<arr.length;i++){ var q=P(arr[i].x,arr[i].y,arr[i].z); i?c.lineTo(q[0],q[1]):c.moveTo(q[0],q[1]); } c.stroke();
      if(up>0){ var h=arr[Math.min(up-1,arr.length-1)], hp=P(h.x,h.y,h.z); c.fillStyle=col; c.beginPath(); c.arc(hp[0],hp[1],3.5,0,6.2832); c.fill(); } }
    path(trailPath.Lc,'#ff4d4f',trailIdx); path(trailPath.Ls,'#2f54eb',trailIdx);
    path(trailPath.Rc,'#389e0d',trailIdx); path(trailPath.Rs,'#fa8c16',trailIdx);
    var fl=document.getElementById(PREFIX+'_frame'); if(fl) fl.textContent='帧: '+Math.min(trailIdx,200);
  }
  window['vaTrail_'+PREFIX]=function(act){
    if(act==='play'){ if(trailTimer)return; trailTimer=setInterval(function(){ trailIdx+=trailSpeed; if(trailIdx>200)trailIdx=0; drawTrail(); },60); }
    else if(act==='pause'){ clearInterval(trailTimer); trailTimer=null; }
    else if(act==='speed'){ trailSpeed=trailSpeed>=4?1:trailSpeed*2; var s=document.getElementById(PREFIX+'_spd'); if(s)s.textContent=trailSpeed+'x'; } };
  window['vaSetArm_'+PREFIX]=function(a){ vaArm=a;
    var l=document.getElementById(PREFIX+'_vaL'),r=document.getElementById(PREFIX+'_vaR');
    if(l)l.classList.toggle('on',a==='left'); if(r)r.classList.toggle('on',a==='right'); renderVel(); };
  function vaHTML(){
    function metric(k,name,unit){
      return '<h5 class="va-sub">'+(vaArm==='left'?'左臂':'右臂')+name+'随时间变化</h5>'+
        '<div class="va-box va-box-lg"><canvas id="'+PREFIX+'_'+k+'_t"></canvas></div>'+
        '<div class="va-grid2">'+
          '<div><div class="va-ct">CMD '+name+'分布</div><div class="va-box"><canvas id="'+PREFIX+'_'+k+'_cmd"></canvas></div></div>'+
          '<div><div class="va-ct">State '+name+'分布</div><div class="va-box"><canvas id="'+PREFIX+'_'+k+'_st"></canvas></div></div>'+
        '</div>';
    }
    return '<h4 class="va-h">轨迹拖尾动画</h4>'+
      '<div class="va-trailbar"><button class="btn" onclick="window.vaTrail_'+PREFIX+'(\\'play\\')">播放</button>'+
        '<button class="btn" onclick="window.vaTrail_'+PREFIX+'(\\'speed\\')">倍速 <span id="'+PREFIX+'_spd">1x</span></button>'+
        '<button class="btn" onclick="window.vaTrail_'+PREFIX+'(\\'pause\\')">暂停</button></div>'+
      '<div class="va-trail"><canvas id="'+PREFIX+'_trail"></canvas></div>'+
      '<div class="va-trailfoot"><span class="muted" id="'+PREFIX+'_frame">帧: 0</span>'+
        '<div class="va-legend2">'+
          '<span><i style="background:#ff4d4f"></i>左臂指令</span><span><i style="background:#2f54eb"></i>左臂状态</span>'+
          '<span><i style="background:#389e0d"></i>右臂指令</span><span><i style="background:#fa8c16"></i>右臂状态</span>'+
        '</div></div>'+
      '<h4 class="va-h">机械臂速度加速度分析</h4>'+
      '<div class="va-armtoggle"><button class="tbtn '+(vaArm==='left'?'on':'')+'" id="'+PREFIX+'_vaL" onclick="window.vaSetArm_'+PREFIX+'(\\'left\\')">左臂</button>'+
        '<button class="tbtn '+(vaArm==='right'?'on':'')+'" id="'+PREFIX+'_vaR" onclick="window.vaSetArm_'+PREFIX+'(\\'right\\')">右臂</button></div>'+
      metric('lv','线速度','m/s')+metric('av','角速度','rad/s')+metric('la','线加速度','m/s²')+metric('aa','角加速度','rad/s²')+
      '<h4 class="va-h">延迟对比与抖动分析</h4>'+
      '<div class="va-params">延迟步数 <b>8</b> &nbsp;·&nbsp; 抖动检测阈值 <b>0.03</b> &nbsp;·&nbsp; 静止数据阈值 <b>0.01</b> &nbsp;·&nbsp; <label><input type="checkbox" checked> 启用抖动检测</label></div>'+
      '<div class="va-ct" style="font-weight:600;margin-bottom:8px;">'+(vaArm==='left'?'左':'右')+'臂状态与指令延迟对比 (抖动率 62.9%, 红色为抖动区间)</div>'+
      '<div class="va-grid2">'+
        '<div><div class="va-ct">X维度 - 原始数据</div><div class="va-box"><canvas id="'+PREFIX+'_lat_xr"></canvas></div></div>'+
        '<div><div class="va-ct">X维度 - 延迟对齐后 (延迟8步)</div><div class="va-box"><canvas id="'+PREFIX+'_lat_xa"></canvas></div></div>'+
        '<div><div class="va-ct">Y维度 - 原始数据</div><div class="va-box"><canvas id="'+PREFIX+'_lat_yr"></canvas></div></div>'+
        '<div><div class="va-ct">Y维度 - 延迟对齐后 (延迟8步)</div><div class="va-box"><canvas id="'+PREFIX+'_lat_ya"></canvas></div></div>'+
      '</div>';
  }
  window['vaStart_'+PREFIX]=function(){
    document.getElementById(PREFIX+'_vaStart').style.display='none';
    var c=document.getElementById(PREFIX+'_vaContent'); c.style.display='block'; c.innerHTML=vaHTML();
    setTimeout(function(){ buildTrail(); trailIdx=200; drawTrail(); renderVel(); renderLat(); }, 40);
  };

  setTimeout(function(){ if(document.getElementById(PREFIX+'_armView')){ updateUI(); renderArm(); } }, 60);
})();
</script>
"""


# ════════════════════════════════════════════════════════════════
# Section 4: Routes
# ════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    # 概览页已去掉, 默认进入「数据查询」
    return redirect("/query")


@app.route("/lake")
def lake():
    mode = request.args.get("mode", "task")        # task | tag | flat
    sel = request.args.get("sel", "")
    if mode not in ("task", "tag", "flat"):
        mode = "task"

    # —— 左树: 三种聚合模式 ——
    pills = "".join(
        f'<a class="tree-mode {"active" if mode==m else ""}" href="/lake?mode={m}">{lab}</a>'
        for m, lab in [("tag", "标签聚合"), ("task", "任务聚合"), ("flat", "平铺")]
    )
    tree = ('<div class="tree-head">'
            '<span class="th-left"><span class="tp-toggle" onclick="toggleTP(this)" title="折叠/展开目录"><span class="sc-col">&laquo;</span><span class="sc-exp">&raquo;</span></span><span class="th-title">数据管理</span></span>'
            '<span class="th-actions">'
            '<a href="#" onclick="toast(\'Demo: 导出入湖任务已提交\');return false;" style="font-size:12px;">+ 导出入湖</a></span></div>'
            f'<div class="tree-modes">{pills}</div>'
            '<div class="tree-search"><input placeholder="搜索..."></div><div class="tree-body">')

    if mode == "task":
        if sel not in [t["id"] for t in TASKS]:
            sel = TASKS[0]["id"]
        for t in TASKS:
            n = len([r for r in RECORDINGS if r["task"] == t["id"]])
            cls = "active" if t["id"] == sel else ""
            tree += (f'<a class="tree-leaf {cls}" style="padding-left:16px;" href="/lake?mode=task&sel={t["id"]}">'
                     f'{t["name"]} <span class="sub">· {n} ep</span></a>')
        recs = [r for r in RECORDINGS if r["task"] == sel]
        tt = next(x for x in TASKS if x["id"] == sel)
        title, sub = tt["name"], tt["zh"]
        scope = f"任务 {tt['name']}"

    elif mode == "tag":
        # 按标签分组(场景/技能/质量), 叶子=标签
        all_tags = [tid for tid, lab, grp in TAG_DEFS
                    if any(tid in rec_tags(r) for r in RECORDINGS)]
        if sel not in all_tags:
            sel = all_tags[0]
        for grp in TAG_GROUP_ORDER:
            grp_tags = [(tid, lab) for tid, lab, g in TAG_DEFS if g == grp and tid in all_tags]
            if not grp_tags:
                continue
            tree += f'<div class="tree-grp" onclick="toggleTree(this)"><span class="caret">&#9656;</span>{grp}</div><div class="tree-children">'
            for tid, lab in grp_tags:
                n = sum(1 for r in RECORDINGS if tid in rec_tags(r))
                cls = "active" if tid == sel else ""
                tree += (f'<a class="tree-leaf {cls}" href="/lake?mode=tag&sel={tid}">'
                         f'{lab} <span class="sub">· {n} ep</span></a>')
            tree += '</div>'
        recs = [r for r in RECORDINGS if sel in rec_tags(r)]
        title, sub = TAG_LABEL.get(sel, sel), "标签"
        scope = f"标签「{TAG_LABEL.get(sel, sel)}」"

    else:  # flat 平铺: 每条 episode 一个叶子
        all_ids = [str(r["id"]) for r in RECORDINGS]
        if sel not in all_ids:
            sel = all_ids[0]
        for r in RECORDINGS:
            cls = "active" if str(r["id"]) == sel else ""
            tags = " ".join(f'<span class="tg">{x}</span>' for x in rec_tag_labels(r)[:2])
            tree += (f'<a class="tree-leaf {cls}" style="padding-left:16px;" href="/lake?mode=flat&sel={r["id"]}">'
                     f'#{r["id"]} <span class="sub">· {r["task"]}</span><div style="margin-top:2px;">{tags}</div></a>')
        rsel = get_rec(int(sel))
        recs = [rsel] if rsel else []
        title, sub = f'Episode #{sel}', (rsel["task"] if rsel else "")
        scope = f"Episode #{sel}"
    tree += '</div>'

    total_frames = sum(r["frames"] for r in recs)
    collections = sorted(set(r["collection"] for r in recs))
    tasks_in = sorted(set(r["task"] for r in recs))
    tag_union = sorted(set(t for r in recs for t in rec_tag_labels(r)))
    eps = recs_to_episodes(recs)

    # 数据预览 Tab
    preview = (f'<div class="tab-pane active" id="pane-preview">'
               f'<div class="muted" style="margin-bottom:12px;">{scope} · 共 {len(recs)} 个 episode，左侧逐个预览</div>'
               f'{preview_block("lake", eps)}</div>')

    # 质检 Tab
    qa_rows = ""
    for i, r in enumerate(recs):
        life_html = "active" if r["life"] == "active" else '<span class="tag tag-orange">已隔离</span>'
        tags = " ".join(f'<span class="tg">{x}</span>' for x in rec_tag_labels(r))
        qa_rows += (f'<tr><td>Ep {i} · #{r["id"]}</td><td>{r["task"]}</td>'
                    f'<td><span class="tag tag-gray">{r["type"]}</span></td>'
                    f'<td>{r["frames"]:,}</td><td>{tags}</td><td>{qa_html(r["qa"])}</td>'
                    f'<td>{life_html}</td></tr>')
    n_pass = sum(1 for r in recs if r["qa"] == "pass")
    n_warn = sum(1 for r in recs if r["qa"] == "warn")
    n_fail = sum(1 for r in recs if r["qa"] == "fail")
    qa = f"""
    <div class="tab-pane" id="pane-qa">
      <div style="display:flex;gap:10px;margin-bottom:14px;">
        <span class="tag" style="color:#389e0d;background:#f6ffed;border-color:#b7eb8f;">PASS {n_pass}</span>
        <span class="tag" style="color:#d48806;background:#fffbe6;border-color:#ffe58f;">WARN {n_warn}</span>
        <span class="tag" style="color:#cf1322;background:#fff2f0;border-color:#ffccc7;">FAIL {n_fail}</span>
      </div>
      <table class="ant-table"><thead><tr><th>Episode</th><th>Task</th><th>类型</th><th>帧数</th><th>标签</th><th>质检</th><th>生命周期</th></tr></thead>
      <tbody>{qa_rows}</tbody></table>
    </div>
    """

    # 基本信息 Tab
    tags_html = "".join(f'<span class="tg">{x}</span>' for x in tag_union) or "—"
    info = f"""
    <div class="tab-pane" id="pane-info">
      <div class="desc-grid">
        <div class="dk">范围</div><div class="dv">{scope}</div>
        <div class="dk">episode 数</div><div class="dv">{len(recs)} 条</div>
        <div class="dk">总帧数</div><div class="dv">{total_frames:,} frames · {round(total_frames/30/60,1) if total_frames else 0} min</div>
        <div class="dk">涉及 task</div><div class="dv">{", ".join(tasks_in) or "—"}</div>
        <div class="dk">涉及标签</div><div class="dv">{tags_html}</div>
        <div class="dk">采集批次</div><div class="dv">{", ".join("#"+str(c) for c in collections) or "—"}</div>
        <div class="dk">本体 / 帧率</div><div class="dv">moz1 · 30 fps</div>
        <div class="dk">相机</div><div class="dv">cam_high · cam_left_wrist · cam_right_wrist (240×320)</div>
      </div>
    </div>
    """
    head = f"""
    <div class="detail-head">
      <div><div class="dh-title">{title} <span class="muted" style="font-size:13px;font-weight:400;">{sub}</span></div>
      <div class="dh-meta"><span>{len(recs)} episodes</span><span>{total_frames:,} frames</span><span>{len(tag_union)} 个标签</span></div></div>
    </div>
    <div class="tabs">
      <div class="tab active" onclick="switchTab(this,'preview')">数据预览</div>
      <div class="tab" onclick="switchTab(this,'qa')">质检</div>
      <div class="tab" onclick="switchTab(this,'info')">基本信息</div>
    </div>
    <div class="pane-wrap">{preview}{qa}{info}</div>
    """
    content = f'<div class="split"><div class="tree-panel">{tree}</div><div class="detail-panel">{head}</div></div>'
    return render_page("数据管理", content, active="lake",
                       breadcrumb=f'数据湖 / 数据管理 / <b>{title}</b>')


DEVICES = ["Moz", "uDAS"]
OPERATORS_LIST = ["Lance Li", "Wei Zhang", "Min Chen"]
OP_POOL = [
    ("E1042", "Lance Li"), ("E1077", "Wei Zhang"), ("E1093", "Min Chen"),
    ("E1105", "Yang Liu"), ("E1118", "Hao Wang"), ("E1126", "Jing Zhao"),
    ("E1134", "Fang Sun"), ("E1149", "Lei Chen"), ("E1153", "Xin Guo"),
    ("E1162", "Tao Huang"), ("E1170", "Bo Zhou"), ("E1188", "Qian Wu"),
]
CREATOR_POOL = [
    ("U2001", "Will Xiao"), ("U2002", "Vivian Luo"), ("U2003", "Lance Li"),
    ("U2004", "Wei Zhang"), ("U2005", "Min Chen"), ("U2006", "Yang Liu"),
    ("U2007", "Hao Wang"), ("U2008", "Jing Zhao"),
]


def ms_search_html(name, base, pool, selected=None):
    """远程搜索式多选: 输入姓名/ID 后选择成 chip。"""
    selected = selected or []
    pool_json = json.dumps([{"id": uid, "nm": nm} for uid, nm in pool], ensure_ascii=False).replace('"', "&quot;")
    chips = "".join(
        f'<span class="ps-chip" data-v="{nm}"><span>{nm}</span>'
        f'<input type="hidden" name="{name}" value="{nm}"><i class="ps-x" onclick="psRemove(event,this)">&times;</i></span>'
        for nm in selected)
    return (f'<div class="ps-wrap" data-name="{name}" data-pool="{pool_json}">'
            f'<div class="ps-control" onclick="psOpen(this)">'
            f'<span class="ps-chips">{chips}</span>'
            f'<input class="ps-input" placeholder="搜索姓名 / ID" oninput="psSearch(this)">'
            f'</div>'
            f'<div class="ps-panel"><div class="ps-results"></div>'
            f'<div class="ps-empty">输入姓名 / ID 搜索</div></div>'
            f'</div>')

def rec_device(r):
    return "Moz" if r["id"] % 2 == 0 else "uDAS"

def rec_operator(r):
    return OPERATORS_LIST[r["id"] % 3]

def rec_type_enum(r):
    # 采集类型枚举: normal / dagger / test / eval (内部「采集」对应 normal)
    t = r.get("type", "")
    return "normal" if t in ("采集", "normal", "") else t

def rec_qc(r):
    # 是否质检 (demo)
    return (r["id"] % 7) != 0

def rec_anno(r):
    # 是否标注 (demo)
    return (r["id"] % 3) == 0


def build_query_filters():
    """新建数据集筛选字段, 按 采集 / 指令Prompt / 质检与标注 / 数据量 分组。"""
    def _ms(base, items):
        # items: list of (value, label)
        checks = "".join(f'<label><input type="checkbox" value="{v}" onchange="msUpdate(this)">{lab}</label>' for v, lab in items)
        return ('<div class="ms-wrap"><div class="ms-trigger" data-base="' + base + '" onclick="this.closest(\'.ms-wrap\').classList.toggle(\'open\')">'
                '<span class="ms-label">' + base + '</span></div><div class="ms-panel">' + checks + '</div></div>')

    # 任务标签 (按组)
    tag_checks = ""
    for grp in TAG_GROUP_ORDER:
        tag_checks += f'<div class="ms-grp">{grp}</div>'
        for tid, lab, g in TAG_DEFS:
            if g == grp:
                tag_checks += f'<label><input type="checkbox" value="{tid}" onchange="msUpdate(this)">{lab}</label>'
    tag_ms = ('<div class="ms-wrap"><div class="ms-trigger" data-base="不限" onclick="this.closest(\'.ms-wrap\').classList.toggle(\'open\')">'
              '<span class="ms-label">不限</span></div><div class="ms-panel">' + tag_checks + '</div></div>')

    op = ms_search_html("operator", "不限", OP_POOL, [])
    typ = _ms("不限", [(t, t) for t in ["normal", "dagger", "test", "eval"]])
    dagger_typ = _ms("不限", [("policy", "policy"), ("teleop", "teleop")])
    qa_ms = _ms("不限", [("pass", "合格"), ("fail", "不合格"), ("warn", "操作失误")])
    hi_tag = _ms("不限", [("grab", "抓取"), ("place", "放置"), ("pour", "倾倒"), ("wipe", "擦拭")])
    lo_tag = _ms("不限", [("reach", "靠近"), ("grip", "夹取"), ("lift", "抬起"), ("release", "松开")])
    dev = '<select><option value="">不限</option>' + "".join(f'<option>{d}</option>' for d in DEVICES) + '</select>'
    rng = '<div class="q-range"><input type="date"><span class="q-range-sep">~</span><input type="date"></div>'

    def tri(dep):  # 三态: 不限 / 是 / 否; dep=依赖字段id, 选「是」才启用
        return (f'<select onchange="qfDep(\'{dep}\',this.value)">'
                '<option value="">不限</option><option value="yes">是</option><option value="no">否</option></select>')
    anno_ver = '<input type="number" min="1" name="annover" placeholder="留空默认最新版本">'

    return (
        # —— 采集 ——
        '<div class="qf-group"><div class="qf-group-title">采集</div>'
        '<div class="q-filter-row q-adv-row">'
        '<div class="q-field"><label>采集任务</label><input placeholder="如 t1,t2 多个逗号隔开"></div>'
        '<div class="q-field"><label>批次编号</label><input placeholder="如 B20250612-01"></div></div>'
        f'<div class="q-filter-row q-adv-row"><div class="q-field"><label>采集时间</label>{rng}</div>'
        f'<div class="q-field"><label>设备序列号</label>{dev}</div></div>'
        f'<div class="q-filter-row q-adv-row"><div class="q-field"><label>操作员</label>{op}</div>'
        f'<div class="q-field"><label>任务标签</label>{tag_ms}</div></div>'
        f'<div class="q-filter-row q-adv-row"><div class="q-field"><label>采集类型</label>{typ}</div>'
        f'<div class="q-field"><label>Dagger 类型</label>{dagger_typ}</div></div>'
        '</div>'
        # —— 指令 Prompt ——
        '<div class="qf-group"><div class="qf-group-title">指令 Prompt</div>'
        '<div class="q-filter-row q-adv-row">'
        '<div class="q-field grow"><label>Highlevel (模糊搜索)</label><input placeholder="输入关键词"></div>'
        f'<div class="q-field"><label>Highlevel 标签</label>{hi_tag}</div></div>'
        '<div class="q-filter-row q-adv-row">'
        '<div class="q-field grow"><label>Lowlevel (模糊搜索)</label><input placeholder="输入关键词"></div>'
        f'<div class="q-field"><label>Lowlevel 标签</label>{lo_tag}</div></div>'
        '</div>'
        # —— 质检与标注 ——
        '<div class="qf-group"><div class="qf-group-title">质检与标注</div>'
        f'<div class="q-filter-row q-adv-row"><div class="q-field"><label>是否质检</label>{tri("dep_qc")}</div>'
        f'<div class="q-field qf-dep qf-off" id="dep_qc"><label>质检结论</label>{qa_ms}</div></div>'
        f'<div class="q-filter-row q-adv-row"><div class="q-field"><label>是否标注</label>{tri("dep_anno")}</div>'
        f'<div class="q-field qf-dep qf-off" id="dep_anno"><label>标注版本</label>{anno_ver}</div></div>'
        '</div>'
        # —— 数据量 ——
        '<div class="qf-group"><div class="qf-group-title">数据量</div>'
        '<div class="q-filter-row q-adv-row"><div class="q-field"><label>Episode 上限</label>'
        '<input type="number" min="1" placeholder="留空则不限制"></div></div>'
        '</div>'
    )


@app.route("/raw")
def raw_data():
    # —— 自采数据 (demo) ——
    self_rows = ""
    _self = [
        ("t1", "Clean the whiteboard", 1280, 1180, 940, "Lance Li", "2026-05-21 10:12"),
        ("t2", "Tidy the desk", 960, 905, 720, "Wei Zhang", "2026-05-24 14:02"),
        ("t3", "Water the plant", 640, 600, 410, "Min Chen", "2026-05-27 11:10"),
        ("t4", "Pour the cup", 520, 510, 0, "Lance Li", "2026-05-29 09:33"),
        ("t5", "Fold the towel", 410, 0, 0, "Wei Zhang", "2026-06-02 16:48"),
    ]
    for tid, name, coll, qc, anno, by, at in _self:
        self_rows += (f'<tr><td><a href="#" onclick="toast(\'Demo: 跳转至 采集任务列表 - 任务详情页 ({tid})\');return false;" style="color:#1F80A0;">{tid}</a></td><td>{name}</td>'
                      f'<td>{coll:,}</td><td>{qc:,}</td><td>{anno:,}</td>'
                      f'<td>{by}</td><td>{at}</td></tr>')

    # —— 三方数据 (demo) ——
    def imp_badge(st):
        m = {"doing": ("tag-blue", "导入中"), "done": ("tag-green", "导入完成"),
             "fail": ("imp-fail", "导入失败")}
        cls, txt = m.get(st, m["done"])
        return f'<span class="tag {cls}">{txt}</span>'
    third_rows = ""
    _third = [
        ("x1", "Open Pick-Place (RT-1)", "rt1_pickplace_v1", "tos://3rd/rt1_pickplace.tar.gz", "done", "Min Chen", "2026-05-18 09:20"),
        ("x2", "Bridge Kitchen v2", "bridge_kitchen_v2", "tos://3rd/bridge_v2.parquet", "done", "Lance Li", "2026-05-22 13:05"),
        ("x3", "DROID subset", "droid_subset_0610", "tos://3rd/droid_subset.zip", "doing", "Wei Zhang", "2026-06-10 11:41"),
        ("x4", "Ego4D hands clips", "--", "tos://3rd/ego4d_hands.tar", "fail", "Min Chen", "2026-06-12 15:58"),
    ]
    for tid, name, dsname, faddr, st, by, at in _third:
        third_rows += (f'<tr><td>{tid}</td><td>{name}</td><td>{dsname}</td>'
                       f'<td><a href="#" onclick="rawDownload(\'{faddr}\');return false;" style="font-family:monospace;font-size:12px;color:#1F80A0;">{faddr}</a></td>'
                       f'<td>{imp_badge(st)}</td>'
                       f'<td>{by}</td><td>{at}</td></tr>')

    creator_ms = ms_search_html("creator", "全部", CREATOR_POOL, [])
    date_range = '<div class="q-range"><input type="date"><span class="q-range-sep">~</span><input type="date"></div>'
    content = f"""
    <div class="raw-head">
      <div class="ep-tabs raw-tabs">
        <button class="ep-tab active" onclick="rawTab(this,'self')">自采数据</button>
        <button class="ep-tab" onclick="rawTab(this,'third')">三方数据</button>
      </div>
      <button class="btn btn-secondary" id="rawCollectBtn" onclick="toast('Demo: 跳转至 采集任务列表')">查看采集任务</button>
      <button class="btn-primary btn" id="rawImportBtn" style="display:none;" onclick="openDrawerById('rawImportModal')">&#43; 导入</button>
    </div>
    <div>
      <div id="pane-self">
        <div class="q-filters" style="margin-bottom:16px;">
          <div class="q-filter-row q-adv-row">
            <div class="q-field"><label>任务 ID</label><input placeholder="如 t1"></div>
            <div class="q-field"><label>任务名称</label><input placeholder="任务名称关键词"></div>
            <div class="q-field"><label>创建人</label>{creator_ms}</div>
            <div class="q-field"><label>创建时间</label>{date_range}</div>
          </div>
          <div class="q-filter-tools">
            <button type="button" class="btn" onclick="toast('Demo: 已重置')">重置</button>
            <button type="button" class="btn-primary btn" onclick="toast('Demo: 已查询')">查询</button>
          </div>
        </div>
        <div class="card">
          <table class="ant-table">
            <thead><tr><th>任务 ID</th><th>任务名称</th><th>已采集数</th><th>已质检数</th><th>已标注数</th><th>创建人</th><th>创建时间</th></tr></thead>
            <tbody>{self_rows}</tbody>
          </table>
        </div>
      </div>
      <div id="pane-third" style="display:none;">
        <div class="q-filters" style="margin-bottom:16px;">
          <div class="q-filter-row q-adv-row">
            <div class="q-field"><label>数据集名称</label><input placeholder="数据集名称关键词"></div>
            <div class="q-field"><label>导入状态</label><select><option value="">全部</option><option>导入中</option><option>导入完成</option><option>导入失败</option></select></div>
            <div class="q-field"><label>创建人</label>{creator_ms}</div>
            <div class="q-field"><label>创建时间</label>{date_range}</div>
          </div>
          <div class="q-filter-tools">
            <button type="button" class="btn" onclick="toast('Demo: 已重置')">重置</button>
            <button type="button" class="btn-primary btn" onclick="toast('Demo: 已查询')">查询</button>
          </div>
        </div>
        <div class="card">
          <table class="ant-table">
            <thead><tr><th>任务 ID</th><th>任务名称</th><th>数据集名称</th><th>文件地址</th><th>导入状态</th><th>创建人</th><th>创建时间</th></tr></thead>
            <tbody>{third_rows}</tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="modal-mask" id="rawImportModal" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="modal-box" style="width:460px;">
        <div class="drawer-head"><h3>导入三方数据</h3><button class="drawer-close" onclick="closeDrawerById('rawImportModal')">&times;</button></div>
        <div class="drawer-body">
          <div class="fg"><label><span class="req">*</span>任务名称</label><input placeholder="如 Open Pick-Place"></div>
          <div class="fg"><label><span class="req">*</span>导入文件</label>
            <label class="upload-box">
              <input type="file" id="rawFile" onchange="rawFilePick(this)" hidden>
              <span class="up-icon">&#8679;</span>
              <span class="up-text" id="rawFileText">点击选择文件</span>
            </label>
            <div class="hint">支持 .tar.gz / .zip / .parquet, 上传后开始异步导入</div>
          </div>
        </div>
        <div class="drawer-foot">
          <button class="btn" onclick="closeDrawerById('rawImportModal')">取消</button>
          <button class="btn-primary btn" onclick="closeDrawerById('rawImportModal');toast('Demo: 已开始异步导入, 可在列表查看导入状态')">开始导入</button>
        </div>
      </div>
    </div>
    <div class="modal-mask" id="rawDownloadModal" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="modal-box" style="width:420px;">
        <div class="drawer-head"><h3>下载文件</h3><button class="drawer-close" onclick="closeDrawerById('rawDownloadModal')">&times;</button></div>
        <div class="drawer-body">
          <div class="muted" style="font-size:13px;">即将下载原始文件:</div>
          <div id="rawDlName" style="font-family:monospace;font-size:13px;margin-top:8px;color:rgba(0,0,0,0.8);word-break:break-all;"></div>
        </div>
        <div class="drawer-foot">
          <button class="btn" onclick="closeDrawerById('rawDownloadModal')">取消</button>
          <button class="btn-primary btn" onclick="closeDrawerById('rawDownloadModal');toast('Demo: 开始下载文件')">下载</button>
        </div>
      </div>
    </div>
    <script>
      function rawDownload(f){{ var el=document.getElementById('rawDlName'); if(el) el.textContent=f; openDrawerById('rawDownloadModal'); }}
      function rawFilePick(inp){{ var t=document.getElementById('rawFileText'), box=inp.closest('.upload-box'); if(inp.files&&inp.files.length){{ t.textContent=inp.files[0].name; box.classList.add('has-file'); }} else {{ t.textContent='点击选择文件'; box.classList.remove('has-file'); }} }}
      function rawTab(btn, which){{
        btn.parentNode.querySelectorAll('.ep-tab').forEach(function(b){{ b.classList.remove('active'); }});
        btn.classList.add('active');
        document.getElementById('pane-self').style.display=(which==='self')?'':'none';
        document.getElementById('pane-third').style.display=(which==='third')?'':'none';
        document.getElementById('rawCollectBtn').style.display=(which==='self')?'':'none';
        document.getElementById('rawImportBtn').style.display=(which==='third')?'':'none';
      }}
    </script>
    """
    return render_page("原始数据", content, active="raw", breadcrumb="数据湖 / <b>原始数据</b>")


@app.route("/ds_progress")
def ds_progress():
    rows_data = [
        (81, "20260420_CarryBox_PutDown_ExhibitionDemo_Moz1Y1", "done", "2026-06-25 16:50:25", "Will Xiao"),
        (80, "20260420_CarryBox_PutDown_ExhibitionDemo_Moz1Ytest", "fail", "2026-06-25 16:46:45", "Will Xiao"),
        (79, "20260521_Unlock_V1_Demo_Moz1WB6", "fail", "2026-06-25 16:38:18", "Will Xiao"),
        (78, "20260521_Unlock_V1_Demo_Moz1WB5", "fail", "2026-06-25 16:24:07", "Will Xiao"),
        (77, "20260521_Unlock_V1_Demo_Moz1WB4", "todo", "2026-06-26 20:00:00", "Will Xiao"),
        (76, "20260521_Unlock_V1_Demo_Moz1WB3", "fail", "2026-06-25 16:18:07", "Will Xiao"),
        (75, "20260521_Unlock_V1_Demo_Moz1WB2", "done", "2026-06-25 16:11:38", "Will Xiao"),
        (74, "20260521_Unlock_V1_Demo_Moz1WB1", "fail", "2026-06-25 15:59:25", "Will Xiao"),
        (73, "20260521_Unlock_V1_Demo_Moz1WB", "fail", "2026-06-25 15:43:38", "Will Xiao"),
        (72, "20260616_test", "fail", "2026-06-16 16:47:47", "Vivian Luo"),
    ]
    st_map = {"done": ("tag-green", "成功"), "fail": ("imp-fail", "失败"), "todo": ("tag-gray", "未开始")}

    def fail_log(did, name, at):
        return "\n".join([
            f"[{at}] dataset_builder: start create dataset {name}",
            f"[{at}] dataset_builder: task_id={did}, status=failed",
            "export_dataset: source recording manifest validation failed",
            "doctor_check: missing parquet segments in 3 episodes",
            "suggestion: 检查源 recording 完整性后重新提交数据集创建任务",
        ])

    def status_cell(did, name, st, at):
        cls, txt = st_map[st]
        tag = f'<span class="tag {cls}">{txt}</span>'
        if st != "fail":
            return tag
        log_attr = html.escape(fail_log(did, name, at), quote=True)
        return (
            f'<span class="status-with-log">{tag}'
            f'<button type="button" class="status-log-icon" title="查看失败日志" '
            f'data-log="{log_attr}" onclick="openDsProgressLog(this)">i</button>'
            f'</span>'
        )

    rows = ""
    for did, name, st, at, by in rows_data:
        if st == "done":
            view_btn = f'<button class="btn" onclick="location.href=\'/datasets\'">查看数据集</button>'
        else:
            view_btn = '<button class="btn" disabled style="opacity:.4;cursor:not-allowed;">查看数据集</button>'
        rows += (f'<tr data-status="{st}"><td>{did}</td>'
                 f'<td>{name}</td>'
                 f'<td>{status_cell(did, name, st, at)}</td>'
                 f'<td>--</td><td>{at}</td><td>{by}</td>'
                 f'<td><div style="display:flex;gap:6px;">'
                 f'<button class="btn" onclick="dpDetail(\'{name}\')">任务详情</button>'
                 f'{view_btn}'
                 f'</div></td></tr>')
    creator_ms = ms_search_html("creator", "请选择创建人", CREATOR_POOL, [])
    content = f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
      <a href="/query" class="btn">&#8249; 返回</a>
      <div style="font-size:16px;font-weight:600;">数据集创建进度</div>
    </div>
    <div class="q-filters" style="margin-bottom:16px;">
      <div class="q-filter-row q-adv-row">
        <div class="q-field"><label>数据集名称</label><input placeholder="请输入数据集名称"></div>
        <div class="q-field"><label>创建人</label>{creator_ms}</div>
      </div>
      <div class="q-filter-tools">
        <button type="button" class="btn" onclick="toast('Demo: 已重置')">重置</button>
        <button type="button" class="btn-primary btn" onclick="toast('Demo: 已查询')">查询</button>
      </div>
    </div>
    <div class="card">
      <table class="ant-table">
        <thead><tr><th>ID</th><th>数据集名称</th><th>
          <div class="status-head-filter">
            <button type="button" class="status-head-trigger" onclick="toggleDsProgressStatusFilter(this)">状态 <span class="caret">&#8963;</span></button>
            <div class="status-head-menu">
              <button type="button" class="status-head-option active" data-value="" onclick="selectDsProgressStatus(this)">全部</button>
              <button type="button" class="status-head-option" data-value="todo" onclick="selectDsProgressStatus(this)">未开始</button>
              <button type="button" class="status-head-option" data-value="done" onclick="selectDsProgressStatus(this)">成功</button>
              <button type="button" class="status-head-option" data-value="fail" onclick="selectDsProgressStatus(this)">失败</button>
            </div>
          </div>
        </th><th>标签</th><th>创建时间</th><th>创建人</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div class="drawer-mask" id="dpDetailModal" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="drawer">
        <div class="drawer-head"><h3>任务详情 · 创建筛选条件</h3><button class="drawer-close" onclick="closeDrawerById('dpDetailModal')">&times;</button></div>
        <div class="drawer-body">
          <div class="muted" style="font-size:12px;margin-bottom:12px;">数据集 <b id="dpDsName"></b> 创建时使用的筛选条件:</div>
          <div class="desc-grid">
            <div class="dk">采集任务</div><div class="dv">t1, t2</div>
            <div class="dk">任务标签</div><div class="dv">擦拭 · 高质量</div>
            <div class="dk">采集类型</div><div class="dv">normal · dagger</div>
            <div class="dk">质检结论</div><div class="dv">合格</div>
            <div class="dk">是否标注</div><div class="dv">是 · 标注版本 v2</div>
            <div class="dk">采集时间</div><div class="dv">2026-05-01 ~ 2026-05-31</div>
            <div class="dk">Prompt 语言</div><div class="dv">中文</div>
            <div class="dk">Episode 上限</div><div class="dv">500</div>
          </div>
        </div>
        <div class="drawer-foot">
          <button class="btn btn-secondary" onclick="closeDrawerById('dpDetailModal')">关闭</button>
        </div>
      </div>
    </div>
    <div class="modal-mask" id="dpLogModal" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="modal-box" style="width:620px;max-width:92vw;">
        <div class="drawer-head"><h3>日志</h3><button class="drawer-close" onclick="closeDrawerById('dpLogModal')">&times;</button></div>
        <div class="drawer-body">
          <pre class="dp-log-pre" id="dpLogBody"></pre>
        </div>
      </div>
    </div>
    <script>
      function dpDetail(name){{ var el=document.getElementById('dpDsName'); if(el) el.textContent=name; openDrawerById('dpDetailModal'); }}
      function toggleDsProgressStatusFilter(btn){{
        var wrap=btn.closest('.status-head-filter');
        if(!wrap) return;
        document.querySelectorAll('.status-head-filter.open').forEach(function(item){{ if(item!==wrap) item.classList.remove('open'); }});
        wrap.classList.toggle('open');
      }}
      function selectDsProgressStatus(btn){{
        var filter=btn.closest('.status-head-filter');
        if(!filter) return;
        filter.querySelectorAll('.status-head-option').forEach(function(item){{ item.classList.remove('active'); }});
        btn.classList.add('active');
        var value=btn.getAttribute('data-value') || '';
        document.querySelectorAll('.ant-table tbody tr[data-status]').forEach(function(row){{
          row.style.display = (!value || row.dataset.status === value) ? '' : 'none';
        }});
        filter.classList.remove('open');
      }}
      function openDsProgressLog(btn){{
        var body=document.getElementById('dpLogBody');
        if(body) body.textContent=btn.getAttribute('data-log') || '';
        openDrawerById('dpLogModal');
      }}
      document.addEventListener('click', function(e){{
        document.querySelectorAll('.status-head-filter.open').forEach(function(wrap){{
          if(!wrap.contains(e.target)) wrap.classList.remove('open');
        }});
      }});
    </script>
    """
    return render_page("数据集创建进度", content, active="query",
                       breadcrumb='数据湖 / 数据查询 / <b>数据集创建进度</b>')


@app.route("/query")
def query():
    # 筛选条件对齐数据拉取脚本 export_dataset.py 的参数
    f_task = request.args.get("task", "")          # 多个 task id, 逗号隔开
    f_device = request.args.get("device", "")
    f_operators = request.args.getlist("operator")  # 多选操作员
    f_types = request.args.getlist("type")          # 多选采集类型
    f_qas = request.args.getlist("qa")             # 多选: pass/fail/warn
    f_tags = request.args.getlist("tag")           # 多选标签
    f_from = request.args.get("from", "")
    f_to = request.args.get("to", "")
    nl = request.args.get("nl", "")

    task_list = [t.strip() for t in f_task.split(",") if t.strip()]

    # —— 过滤 ——
    res = []
    for r in RECORDINGS:
        if task_list and r["task"] not in task_list:
            continue
        if f_tags and not any(t in rec_tags(r) for t in f_tags):
            continue
        if f_device and rec_device(r) != f_device:
            continue
        if f_operators and rec_operator(r) not in f_operators:
            continue
        if f_types and rec_type_enum(r) not in f_types:
            continue
        if f_qas and r["qa"] not in f_qas:
            continue
        if f_from and r["at"][:10] < f_from:
            continue
        if f_to and r["at"][:10] > f_to:
            continue
        res.append(r)

    # 展示用结果集: 模拟较大命中量 (用于分页演示), 由筛选结果循环铺开
    disp = [res[i % len(res)] for i in range(47)] if res else []

    # —— 配方助手: 当前筛选结果的 提示词 / 标签 构成 ——
    prompt_counts = {}
    for r in disp:
        prompt_counts[r["task"]] = prompt_counts.get(r["task"], 0) + 1
    prompt_comp = [{"key": k, "label": task_instr(k), "count": c} for k, c in prompt_counts.items()]
    skill_defs = [(tid, lab) for tid, lab, grp in TAG_DEFS if grp == "技能"]
    tag_comp = []
    for tid, lab in skill_defs:
        c = sum(1 for r in disp if tid in rec_tags(r))
        if c:
            tag_comp.append({"key": tid, "label": lab, "count": c})
    recipe_data_js = (f"window._rcPrompt={json.dumps(prompt_comp, ensure_ascii=False)};"
                      f"window._rcTag={json.dumps(tag_comp, ensure_ascii=False)};"
                      f"window._rcBaseN={len(disp)};")
    # 预览抽屉: id → episode 序号 (复用 preview_block 的轨迹组件)
    qprev_map = {r["id"]: {"idx": i, "qa": r["qa"]} for i, r in enumerate(res)}
    recipe_data_js += f"window._qprevMap={json.dumps(qprev_map, ensure_ascii=False)};"
    prev_eps = recs_to_episodes(res) if res else recs_to_episodes([RECORDINGS[0]])

    # —— 生成 SQL (服务端, 反映当前筛选) ——
    qa_sql = {"pass": "PASS", "fail": "FAIL", "warn": "WARN"}
    conds = ["robot_type = 'moz1'"]
    if task_list:
        conds.append("task IN (" + ", ".join(f"'{t}'" for t in task_list) + ")")
    if f_device:
        conds.append(f"capture_device = '{f_device}'")
    if f_operators:
        conds.append("operator IN (" + ", ".join(f"'{o}'" for o in f_operators) + ")")
    if f_types:
        conds.append("type IN (" + ", ".join(f"'{t}'" for t in f_types) + ")")
    if f_qas:
        conds.append("qa_status IN (" + ", ".join(f"'{qa_sql.get(q, q.upper())}'" for q in f_qas) + ")")
    if f_tags:
        for t in f_tags:
            conds.append(f"array_contains(tags, '{TAG_LABEL.get(t, t)}')")
    if f_from:
        conds.append(f"collected_at >= '{f_from}'")
    if f_to:
        conds.append(f"collected_at <= '{f_to}'")
    where = "\n  AND ".join(conds)
    sql = ("SELECT episode_index, recording_id, task, collection_id, capture_device,\n"
           "       operator, frames, duration_s, collected_at, qa_status\n"
           "FROM   lake.recordings\n"
           f"WHERE  {where}\n"
           "ORDER BY collected_at DESC;")

    # —— 选择器 ——
    def sel(name, cur, options, placeholder):
        opts = f'<option value="">{placeholder}</option>'
        for v, lab in options:
            s = " selected" if v == cur else ""
            opts += f'<option value="{v}"{s}>{lab}</option>'
        cls = "has-value" if cur else ""
        return f'<select name="{name}" class="{cls}">{opts}</select>'

    # 任务: 文本输入, 多个 task id 逗号隔开
    task_cls = "has-value" if f_task else ""
    task_input = f'<input name="task" class="{task_cls}" value="{f_task}" placeholder="如 t1,t2 多个逗号隔开">'

    # 多选下拉 (ms-wrap)
    def ms(name, base, items, selected):
        n = len(selected)
        label = f"{base} ({n})" if n else base
        checks = "".join(
            f'<label><input type="checkbox" name="{name}" value="{v}"'
            f'{" checked" if v in selected else ""} onchange="msUpdate(this)">{lab}</label>'
            for v, lab in items)
        return (f'<div class="ms-wrap"><div class="ms-trigger {"has-value" if n else ""}" data-base="{base}" '
                f'onclick="this.closest(\'.ms-wrap\').classList.toggle(\'open\')">'
                f'<span class="ms-label">{label}</span></div><div class="ms-panel">{checks}</div></div>')

    # 标签多选 (按 场景/技能/质量 分组)
    tag_checks = ""
    for grp in TAG_GROUP_ORDER:
        tag_checks += f'<div class="ms-grp">{grp}</div>'
        for tid, lab, g in TAG_DEFS:
            if g == grp:
                ck = " checked" if tid in f_tags else ""
                tag_checks += (f'<label><input type="checkbox" name="tag" value="{tid}"{ck} '
                               f'onchange="msUpdate(this)">{lab}</label>')
    n_tag = len(f_tags)
    tag_ms = (f'<div class="ms-wrap"><div class="ms-trigger {"has-value" if n_tag else ""}" data-base="标签" '
              f'onclick="this.closest(\'.ms-wrap\').classList.toggle(\'open\')">'
              f'<span class="ms-label">{("标签 ("+str(n_tag)+")") if n_tag else "标签"}</span></div>'
              f'<div class="ms-panel">{tag_checks}</div></div>')

    qa_ms = ms("qa", "全部", [("pass", "合格"), ("fail", "不合格"), ("warn", "操作失误")], f_qas)
    dev_sel = sel("device", f_device, [(d, d) for d in DEVICES], "全部")
    op_sel = ms_search_html("operator", "全部", OP_POOL, f_operators)
    type_sel = ms("type", "全部", [("normal", "normal"), ("dagger", "dagger"), ("test", "test"), ("eval", "eval")], f_types)

    # —— 新增分组字段 (与「新建数据集」弹窗一致; 部分为 demo 展示, 暂不参与后端过滤) ——
    batch_input = '<input name="batch" placeholder="如 B20250612-01">'
    hl_input = '<input name="hl" placeholder="输入关键词">'
    ll_input = '<input name="ll" placeholder="输入关键词">'
    dagger_ms = ms("dtype", "全部", [("policy", "policy"), ("teleop", "teleop")], [])
    hltag_ms = ms("hltag", "全部", [("grab", "抓取"), ("place", "放置"), ("pour", "倾倒"), ("wipe", "擦拭")], [])
    lltag_ms = ms("lltag", "全部", [("reach", "靠近"), ("grip", "夹取"), ("lift", "抬起"), ("release", "松开")], [])

    def tri_q(dep):  # 三态: 不限 / 是 / 否; 选「是」才启用依赖字段 dep
        return (f'<select onchange="qfDep(\'{dep}\',this.value)">'
                '<option value="">不限</option><option value="yes">是</option><option value="no">否</option></select>')
    annover_sel = '<input type="number" min="1" name="annover" placeholder="留空默认最新版本">'
    lang_ms = ms("lang", "全部", [("zh", "中文"), ("en", "英文")], [])

    # 所有筛选条件默认全部展开 (不再折叠)
    adv_fd = ""

    top_card = f"""
    <div class="q-filters">
      <div class="q-mode-tabs">
        <button class="qm-tab active" data-m="filter" onclick="qSetMode('filter')">固定筛选</button>
        <button class="qm-tab" data-m="sql" onclick="qSetMode('sql')">执行 SQL</button>
      </div>

      <div id="qModeFilter">
        <form method="get" action="/query" id="qform">
          <input type="hidden" name="nl" id="nlField" value="{nl}">
          <div class="qf-group"><div class="qf-group-title" onclick="qfToggleGroup(this)"><span class="qf-caret">&#9662;</span>任务信息</div><div class="qf-group-body">
            <div class="q-filter-row q-adv-row">
              <div class="q-field"><label>采集任务</label>{task_input}</div>
              <div class="q-field"><label>任务标签</label>{tag_ms}</div>
            </div>
            <div class="q-filter-row q-adv-row">
              <div class="q-field"><label>批次编号</label>{batch_input}</div>
              <div class="q-field"><label>设备序列号</label>{dev_sel}</div>
              <div class="q-field"><label>采集时间</label>
                <div class="q-range">
                  <input type="date" name="from" value="{f_from}">
                  <span class="q-range-sep">~</span>
                  <input type="date" name="to" value="{f_to}">
                </div>
              </div>
              <div class="q-field"><label>操作员</label>{op_sel}</div>
            </div>
            <div class="q-filter-row q-adv-row">
              <div class="q-field"><label>采集类型</label>{type_sel}</div>
              <div class="q-field"><label>Dagger 类型</label>{dagger_ms}</div>
            </div>
          </div></div>
          <div class="qf-group collapsed"><div class="qf-group-title" onclick="qfToggleGroup(this)"><span class="qf-caret">&#9662;</span>处理信息</div><div class="qf-group-body">
            <div class="q-filter-row q-adv-row">
              <div class="q-field"><label>是否质检</label>{tri_q('q_dep_qc')}</div>
              <div class="q-field qf-dep qf-off" id="q_dep_qc"><label>质检结论</label>{qa_ms}</div>
              <div class="q-field"><label>是否标注</label>{tri_q('q_dep_anno')}</div>
              <div class="q-field qf-dep qf-off" id="q_dep_anno"><label>标注版本</label>{annover_sel}</div>
            </div>
          </div></div>
          <div class="qf-group collapsed"><div class="qf-group-title" onclick="qfToggleGroup(this)"><span class="qf-caret">&#9662;</span>指令信息</div><div class="qf-group-body">
            <div class="q-filter-row q-adv-row">
              <div class="q-field grow"><label>Highlevel (模糊搜索)</label>{hl_input}</div>
              <div class="q-field"><label>Highlevel 标签</label>{hltag_ms}</div>
            </div>
            <div class="q-filter-row q-adv-row">
              <div class="q-field grow"><label>Lowlevel (模糊搜索)</label>{ll_input}</div>
              <div class="q-field"><label>Lowlevel 标签</label>{lltag_ms}</div>
            </div>
          </div></div>
          <div class="qf-group collapsed"><div class="qf-group-title" onclick="qfToggleGroup(this)"><span class="qf-caret">&#9662;</span>导出要求</div><div class="qf-group-body">
            <div class="q-filter-row q-adv-row">
              <div class="q-field"><label>Episode 上限</label><input type="number" min="1" name="limit" placeholder="留空则不限制"></div>
              <div class="q-field"><label>Prompt 语言</label>{lang_ms}</div>
            </div>
          </div></div>
          <div class="q-filter-tools">
            <a href="/query" class="btn">重置</a>
            <button type="submit" class="btn-primary btn">查询</button>
          </div>
        </form>
      </div>

      <div id="qModeSql" style="display:none;">
        <div id="qSqlAi" class="sql-ai">
          <div class="sql-ai-head"><span class="ic-ai" style="color:#9b59b6;">&#10022;</span> 用自然语言生成 SQL</div>
          <div class="sql-ai-row">
            <input id="qSqlNl" class="sql-ai-input" placeholder="例如：擦白板任务、近一周、已质检合格的 episode" onkeydown="if(event.key==='Enter'){{event.preventDefault();qSqlAiGen();}}">
            <button type="button" class="btn-primary btn" onclick="qSqlAiGen()">生成 SQL</button>
          </div>
          <div id="qSqlAiNote" class="sql-ai-note" style="display:none;"></div>
        </div>
        <textarea id="qSqlEditor" class="code-editor" rows="9" style="width:100%;box-sizing:border-box;">{sql}</textarea>
        <div id="qSqlStatus" class="sql-status" style="display:none;"></div>
        <div class="q-filter-tools">
          <button type="button" class="btn" onclick="qSqlReset()">重置</button>
          <button type="button" class="btn-primary btn" onclick="qSqlRun()">执行</button>
        </div>
      </div>
    </div>
    <script>window._defaultSql={json.dumps(sql)};</script>
    """

    # —— AI 辅助 侧栏 (聊天式, 支持多轮; 同排推开, 无遮挡) ——
    ai_panel = f"""
    <aside class="ai-side" id="aiDrawer">
      <div class="ai-inner">
        <div class="ai-head"><b><span class="ic-ai" style="color:#9b59b6;">&#10022;</span> AI 助手</b><button class="drawer-close" onclick="aiClose()">&times;</button></div>
        <div class="ai-body" id="aiMsgs">
          <div class="ai-msg ai-bot">
            <div class="ai-bubble">你好 &#128075; 用自然语言描述你想找的数据, 我帮你翻译成 SQL 并执行。试试这些:</div>
            <div class="ai-chips">
              <span class="ai-chip" onclick="aiSend('擦白板任务、近一周、已质检通过的 episode')">擦白板·近一周·合格</span>
              <span class="ai-chip" onclick="aiSend('Moz 设备、Lance Li 采集、帧数大于 1000 的 episode')">Moz·Lance·帧数&gt;1000</span>
              <span class="ai-chip" onclick="aiSend('近一周采集、操作失误的 episode')">近一周·操作失误</span>
            </div>
          </div>
        </div>
        <div class="ai-input">
          <textarea id="aiInput" placeholder="描述要查询的数据, 回车发送 (Shift+回车换行)" onkeydown="aiKey(event)"></textarea>
          <button class="ai-send" onclick="aiSend()" title="发送">&#10148;</button>
        </div>
      </div>
    </aside>
    """

    # —— 配方助手 侧栏: 提示词/标签构成比例条, 拖动调比例, 按比例随机采样 ——
    recipe_panel = """
    <aside class="ai-side" id="recipeDrawer">
      <div class="ai-inner">
        <div class="ai-head"><b>&#129514; 配方助手</b><button class="drawer-close" onclick="recipeClose()">&times;</button></div>
        <div class="ai-body">
          <div class="rc-intro">基于当前筛选的 <b id="rcBase">0</b> 个 episode。每类权重默认 <b>&times;1</b>(保持原始构成), 拖动调整某类的<b>相对权重</b>(其余不变), 系统按相对比例随机采样。</div>
          <div class="rc-sec">提示词构成 <span class="muted">按任务 prompt</span></div>
          <div id="rcPrompt"></div>
          <div class="rc-sec">标签构成 <span class="muted">按技能标签</span></div>
          <div id="rcTag"></div>
        </div>
        <div class="rc-foot">
          <div class="rc-count">采样后约 <b id="rcCount">0</b> 个 episode <span class="muted" id="rcOf"></span></div>
          <div style="display:flex;gap:8px;justify-content:flex-end;">
            <button class="btn" onclick="recipeReset()">重置</button>
            <button class="btn-primary btn" onclick="recipeApply()">确认采样</button>
          </div>
        </div>
      </div>
    </aside>
    """

    # —— 结果: 按 episode 平铺 (每页 20 条) ——
    PAGE_SIZE = 20
    rows = ""
    def yn(flag):
        return ('<span class="tag tag-green">是</span>' if flag
                else '<span class="tag tag-gray">否</span>')
    for i, r in enumerate(disp):
        pg = i // PAGE_SIZE
        rows += (f'<tr data-pg="{pg}" style="{"display:none;" if pg else ""}"><td>#{r["id"]}</td><td>{r["task"]}</td>'
                 f'<td>{rec_device(r)}</td>'
                 f'<td><span class="tag tag-gray">{rec_type_enum(r)}</span></td>'
                 f'<td>{yn(rec_qc(r))}</td>'
                 f'<td>{yn(rec_anno(r))}</td>'
                 f'<td>{r["frames"]:,}</td><td>{r["dur"]}s</td>'
                 f'<td><a href="#" onclick="qPreview({r["id"]});return false;">预览</a></td></tr>')
    if not rows:
        rows = '<tr><td colspan="9" class="muted" style="text-align:center;padding:30px;">无匹配 episode, 调整筛选条件试试</td></tr>'
    total_frames = sum(r["frames"] for r in disp)
    n_disp = len(disp)
    n_pages = max(1, (n_disp + PAGE_SIZE - 1) // PAGE_SIZE)
    pager = ""
    if n_pages > 1:
        btns = "".join(
            f'<button class="pg-btn{" active" if p == 0 else ""}" data-p="{p}" onclick="qGoPage({p})">{p+1}</button>'
            for p in range(n_pages))
        pager = (f'<div class="q-pager"><span class="muted" style="font-size:12px;">共 {n_disp} 条 · 每页 {PAGE_SIZE} 条</span>'
                 f'<div class="pg-btns">{btns}</div></div>')
    result_card = f"""
    <div class="card">
      <h3>查询结果
        <span class="muted" id="qResMeta" style="font-size:13px;font-weight:400;">默认展示 20 条, 更多请输入筛选条件查询</span>
        <span style="float:right;display:inline-flex;gap:8px;">
          <a href="/ds_progress" class="btn">查看数据集创建进度</a>
          <button class="btn btn-secondary" onclick="document.getElementById('buildDsDrawer').classList.add('active')">用结果建数据集</button>
        </span>
      </h3>
      <div class="q-table-scroll">
        <table class="ant-table">
          <thead><tr><th>数据 ID</th><th>Task ID</th><th>设备</th><th>类型</th><th>是否质检</th><th>是否标注</th><th>帧数</th><th>时长</th><th>操作</th></tr></thead>
          <tbody id="qbody">{rows}</tbody>
        </table>
      </div>
      {pager}
    </div>
    """

    prev_drawer = f"""
    <div class="drawer-mask" id="qPrevDrawer" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="drawer qp-drawer">
        <div class="drawer-head"><h3 id="qPrevTitle">Episode 预览</h3><button class="drawer-close" onclick="document.getElementById('qPrevDrawer').classList.remove('active')">&times;</button></div>
        <div class="drawer-body"><div class="qp-wrap">{preview_block("qprev", prev_eps)}</div></div>
      </div>
    </div>
    """
    build_folder_opts = "".join(f"<option>{f}</option>" for f in V2_FOLDERS)
    build_selected_tag_paths = [
        DATASET_TAG_PATH_BY_ID.get(tag_id, TAG_LABEL.get(tag_id, tag_id))
        for tag_id in f_tags
    ]
    build_tag_selector = dataset_tag_picker_html(
        "buildDsTags",
        build_selected_tag_paths,
        editable=True,
        input_name="dataset_tag",
    )
    build_ds_drawer = f"""
    <div class="modal-mask" id="buildDsDrawer" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="modal-box" style="width:460px;">
        <div class="drawer-head"><h3>用结果建数据集</h3><button class="drawer-close" onclick="document.getElementById('buildDsDrawer').classList.remove('active')">&times;</button></div>
        <div class="drawer-body">
          <div class="muted" style="font-size:12px;margin-bottom:14px;">将当前查询结果（{n_disp} 个 episode）打包为一个新数据集。</div>
          <div class="fg"><label><span class="req">*</span>标识</label><input id="buildDsIdent" placeholder="英文唯一标识" oninput="var n=document.getElementById('buildDsName'); if(n) n.value=this.value;"><div class="hint">全局唯一</div></div>
          <div class="fg"><label><span class="req">*</span>数据集名称</label><input id="buildDsName" placeholder="填写标识后自动带入, 可修改"></div>
          <div class="fg"><label>生成格式</label><select><option>LeRobot</option><option>Mozdataset</option></select></div>
          <div class="fg"><label>选择目录</label><select>{build_folder_opts}</select></div>
          <div class="fg"><label>标签</label>{build_tag_selector}</div>
        </div>
        <div class="drawer-foot">
          <button class="btn" onclick="document.getElementById('buildDsDrawer').classList.remove('active')">取消</button>
          <button class="btn-primary btn" onclick="dsCreating('buildDsDrawer')">确认创建</button>
        </div>
      </div>
    </div>
    """
    content = top_card + result_card + ai_panel + recipe_panel + prev_drawer + build_ds_drawer
    script = """<script>__RECIPE_DATA__
    function toggleAdv(){
      var p=document.getElementById('advPanel'), b=document.getElementById('advBtn');
      var open=p.style.display!=='none';
      p.style.display=open?'none':'flex';
      b.innerHTML=open?'高级筛选 +':'收起筛选 −';
    }
    function pushMain(on){ var m=document.querySelector('.q-main'); if(m) m.classList.toggle('ai-pushed', on); }
    function aiOpen(){ recipeClose(); document.getElementById('aiDrawer').classList.add('active'); pushMain(true); var i=document.getElementById('aiInput'); if(i) setTimeout(function(){i.focus();},220); }
    function aiClose(){ document.getElementById('aiDrawer').classList.remove('active'); pushMain(false); }
    function aiKey(e){ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); aiSend(); } }
    function aiEsc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
    function msUpdate(cb){
      var wrap=cb.closest('.ms-wrap');
      var checked=wrap.querySelectorAll('input:checked'); var n=checked.length;
      var trig=wrap.querySelector('.ms-trigger'); var base=trig.getAttribute('data-base')||'';
      var lab=wrap.querySelector('.ms-label');
      trig.classList.toggle('has-value', n>0);
      if(!n){ lab.textContent=base; return; }
      var names=[]; checked.forEach(function(c){ names.push(c.parentNode.textContent.trim()); });
      lab.textContent=names.join(', ');
      // 回显放不下时折叠为个数
      if(lab.scrollWidth > lab.clientWidth + 1){ lab.textContent=base+' ('+n+')'; }
    }
    document.addEventListener('DOMContentLoaded', function(){
      document.querySelectorAll('.ms-wrap').forEach(function(w){ var c=w.querySelector('input:checked'); if(c) msUpdate(c); });
    });
    document.addEventListener('click', function(e){
      document.querySelectorAll('.ms-wrap.open').forEach(function(w){ if(!w.contains(e.target)) w.classList.remove('open'); });
    });
    function aiGenSQL(nl){
      var conds=["robot_type = 'moz1'"];
      var te=document.querySelector('input[name=task]'); var tv=te?te.value.trim():'';
      if(tv){ var ts=tv.split(',').map(function(s){return s.trim();}).filter(Boolean); conds.push("task IN ("+ts.map(function(x){return "'"+x+"'";}).join(", ")+")"); }
      else if(/擦白板|whiteboard/.test(nl)) conds.push("task = 'clean_the_whiteboard'");
      if(/moz/i.test(nl)) conds.push("capture_device = 'Moz'");
      if(/udas/i.test(nl)) conds.push("capture_device = 'uDAS'");
      if(/lance/i.test(nl)) conds.push("operator = 'Lance Li'");
      if(/不合格|fail/i.test(nl)) conds.push("qa_status = 'FAIL'");
      else if(/操作失误|warn/i.test(nl)) conds.push("qa_status = 'WARN'");
      else if(/合格|通过|pass/i.test(nl)) conds.push("qa_status = 'PASS'");
      if(/近一周|近7天|近 7 天/.test(nl)) conds.push("collected_at >= DATE_SUB(CURRENT_DATE, 7)");
      var m=nl.match(/帧数(大于|>|超过)\\s*(\\d+)/); if(m) conds.push("frames > "+m[2]);
      return "SELECT episode_index, recording_id, task, collection_id, capture_device,\\n       operator, frames, duration_s, collected_at, qa_status\\nFROM   lake.recordings\\nWHERE  "+conds.join("\\n  AND ")+"\\nORDER BY collected_at DESC;";
    }
    function aiSend(preset){
      var inp=document.getElementById('aiInput');
      var text=(preset!==undefined?preset:inp.value).trim();
      if(!text) return;
      inp.value='';
      var msgs=document.getElementById('aiMsgs');
      msgs.insertAdjacentHTML('beforeend', '<div class="ai-msg ai-user"><div class="ai-bubble">'+aiEsc(text)+'</div></div>');
      var sql=aiGenSQL(text);
      window._aiNL=text;
      msgs.insertAdjacentHTML('beforeend',
        '<div class="ai-msg ai-bot"><div class="ai-bubble">已理解你的描述, 生成如下 SQL:</div>'+
        '<pre class="ai-sql">'+aiEsc(sql)+'</pre>'+
        '<button class="btn-primary btn ai-run" onclick="aiRun()">执行查询 &#8594;</button></div>');
      msgs.scrollTop=msgs.scrollHeight;
    }
    function aiRun(){ document.getElementById('nlField').value=window._aiNL||''; document.getElementById('qform').submit(); }
    function qGoPage(p){
      document.querySelectorAll('#qbody tr').forEach(function(tr){ tr.style.display = (+tr.getAttribute('data-pg')===p)?'':'none'; });
      document.querySelectorAll('.pg-btn').forEach(function(b){ b.classList.toggle('active', +b.getAttribute('data-p')===p); });
      var sc=document.querySelector('.q-table-scroll'); if(sc) sc.scrollTop=0;
    }
    var _qcm=null;
    function qInitCM(){
      if(_qcm) return;
      var ta=document.getElementById('qSqlEditor');
      if(!ta || !window.CodeMirror) return;
      _qcm=CodeMirror.fromTextArea(ta,{mode:'text/x-sql',theme:'material-darker',lineNumbers:true,lineWrapping:true,indentUnit:2,tabSize:2});
      _qcm.setSize('100%', 220);
    }
    function qSetMode(m){
      document.getElementById('qModeFilter').style.display = m==='filter'?'':'none';
      document.getElementById('qModeSql').style.display = m==='sql'?'':'none';
      document.querySelectorAll('.qm-tab').forEach(function(t){ t.classList.toggle('active', t.getAttribute('data-m')===m); });
      if(m==='sql'){ qInitCM(); if(_qcm) setTimeout(function(){_qcm.refresh();},10); }
    }
    function qSqlReset(){
      if(_qcm){ _qcm.setValue(window._defaultSql||''); } else { var e=document.getElementById('qSqlEditor'); if(e) e.value=window._defaultSql||''; }
      var st=document.getElementById('qSqlStatus'); if(st) st.style.display='none';
    }
    var _qsqlTimer=null;
    function qSqlRun(){
      var sql=(_qcm?_qcm.getValue():(document.getElementById('qSqlEditor')||{}).value)||'';
      var st=document.getElementById('qSqlStatus');
      st.style.display='flex'; st.className='sql-status running';
      st.innerHTML='<span class="sql-spin"></span><span>执行中…</span>';
      if(_qsqlTimer) clearTimeout(_qsqlTimer);
      _qsqlTimer=setTimeout(function(){
        var s=sql.toLowerCase(), err=null;
        if(!/select/.test(s)) err="SQL 解析失败 (line 1): 缺少 SELECT 关键字";
        else if(!/from/.test(s)) err="SQL 解析失败: 缺少 FROM 子句";
        else if(!/lake\\.recordings/.test(s)) err="执行失败: 表不存在或无访问权限\\n  仅支持查询数据湖表 lake.recordings";
        if(err){
          st.className='sql-status err';
          st.innerHTML='<span>&#10007; 执行失败</span><div class="sql-err-log">'+aiEsc(err)+'</div>';
        } else {
          var n=(sql.length*7)%53+12, ms=(sql.length*3)%180+62;
          st.className='sql-status ok';
          st.innerHTML='<span>&#10003; 执行成功 · 命中 '+n+' 条 · 耗时 '+ms+' ms</span>';
        }
      }, 700);
    }
    function qSqlAiToggle(){
      var p=document.getElementById('qSqlAi'), b=document.getElementById('qSqlAiBtn');
      var open=p.style.display!=='none';
      p.style.display=open?'none':'block';
      if(b) b.classList.toggle('active', !open);
      if(!open){ var i=document.getElementById('qSqlNl'); if(i) setTimeout(function(){i.focus();},10); }
    }
    function qSqlAiChip(t){ document.getElementById('qSqlNl').value=t; qSqlAiGen(); }
    function qSqlAiGen(){
      var nl=(document.getElementById('qSqlNl').value||'').trim();
      if(!nl){ toast('请先输入描述'); return; }
      var sql=aiGenSQL(nl);
      qInitCM();
      if(_qcm){ _qcm.setValue(sql); _qcm.refresh(); } else { document.getElementById('qSqlEditor').value=sql; }
      var note=document.getElementById('qSqlAiNote');
      note.style.display='block';
      note.innerHTML='&#10003; 已生成 SQL 并填入下方编辑器, 可继续编辑后点「执行」';
    }

    /* ===== Episode 预览抽屉 (复用轨迹组件: 三视频 + 5 tab 轨迹) ===== */
    function qPreview(id){
      var m=(window._qprevMap||{})[id]; if(!m) return;
      document.getElementById('qPrevTitle').innerHTML='#'+id;
      document.getElementById('qPrevDrawer').classList.add('active');
      if(window.setEp_qprev) window.setEp_qprev(m.idx);
    }

    /* ===== 配方助手 (相对比例: 每类独立权重 ×倍数, 默认 ×1 保持原始构成) ===== */
    var RC={prompt:[], tag:[], baseN:0}; var RC_MAX=2;
    function rcInitGroup(src){ return src.map(function(c){ return {key:c.key,label:c.label,avail:c.count,base:c.count,weight:1}; }); }
    function rcProps(arr){ var tot=0; arr.forEach(function(c){tot+=c.base*c.weight;}); return arr.map(function(c){ return tot>0 ? (c.base*c.weight)/tot : 0; }); }
    function rcGroupTotal(arr,props){ var t=Infinity; arr.forEach(function(c,i){ if(props[i]>0.001) t=Math.min(t, c.avail/props[i]); }); return isFinite(t)?Math.floor(t):0; }
    function recipeOpen(){
      aiClose();
      RC.baseN=window._rcBaseN||0;
      RC.prompt=rcInitGroup(window._rcPrompt||[]);
      RC.tag=rcInitGroup(window._rcTag||[]);
      document.getElementById('rcBase').textContent=RC.baseN;
      rcUpdateCount();
      document.getElementById('recipeDrawer').classList.add('active'); pushMain(true);
    }
    function recipeClose(){ document.getElementById('recipeDrawer').classList.remove('active'); if(!document.getElementById('aiDrawer').classList.contains('active')) pushMain(false); }
    function rcRender(grp,cid,props){
      var arr=RC[grp]; var cnt=window._rcLastCount||0;
      var h=arr.map(function(c,i){
        var fill=Math.round(c.weight/RC_MAX*100), p=props[i];
        return '<div class="rc-row">'+
          '<div class="rc-label"><span>'+c.label+'</span><span class="rc-pct">&times;'+c.weight.toFixed(1)+'</span></div>'+
          '<div class="rc-track" data-grp="'+grp+'" data-i="'+i+'"><div class="rc-base-mark"></div><div class="rc-fill" style="width:'+fill+'%"><span class="rc-handle"></span></div></div>'+
          '<div class="rc-sub">占比 '+Math.round(p*100)+'% · 可用 '+c.avail+' · 采样 <b>'+Math.round(p*cnt)+'</b></div>'+
        '</div>';
      }).join('');
      document.getElementById(cid).innerHTML=h;
    }
    function rcUpdateCount(){
      var pp=rcProps(RC.prompt), tp=rcProps(RC.tag);
      var pt=rcGroupTotal(RC.prompt,pp), tt=rcGroupTotal(RC.tag,tp);
      var cnt=Math.min(pt,tt); if(!isFinite(cnt)) cnt=0;
      window._rcLastCount=cnt;
      document.getElementById('rcCount').textContent=cnt;
      document.getElementById('rcOf').textContent='/ '+RC.baseN+' 个';
      rcRender('prompt','rcPrompt',pp); rcRender('tag','rcTag',tp);
    }
    function rcSetWeight(grp,idx,w){ RC[grp][idx].weight=Math.max(0,Math.min(RC_MAX,w)); rcUpdateCount(); }
    document.addEventListener('mousedown', function(e){
      var track=e.target.closest('.rc-track'); if(!track) return;
      e.preventDefault();
      var grp=track.getAttribute('data-grp'), idx=+track.getAttribute('data-i');
      function move(ev){ var rect=track.getBoundingClientRect(); rcSetWeight(grp,idx,(ev.clientX-rect.left)/rect.width*RC_MAX); }
      move(e);
      function up(){ document.removeEventListener('mousemove',move); document.removeEventListener('mouseup',up); }
      document.addEventListener('mousemove',move); document.addEventListener('mouseup',up);
    });
    function recipeReset(){ RC.prompt.forEach(function(c){c.weight=1;}); RC.tag.forEach(function(c){c.weight=1;}); rcUpdateCount(); document.querySelectorAll('#qbody tr').forEach(function(tr){tr.style.display='';}); toast('已重置配方'); }
    function recipeApply(){
      var target=window._rcLastCount||0;
      var body=document.getElementById('qbody'); if(body){
        var trs=Array.prototype.slice.call(body.querySelectorAll('tr'));
        for(var i=trs.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=trs[i]; trs[i]=trs[j]; trs[j]=t; }
        trs.forEach(function(tr,i){ tr.style.display = i<target ? '' : 'none'; });
      }
      var hd=document.getElementById('qResMeta'); if(hd) hd.textContent='配方采样后 '+target+' 个 episode';
      recipeClose();
      toast('已按配方随机采样 '+target+' 个 episode');
    }
    </script>"""
    script = script.replace("__RECIPE_DATA__", recipe_data_js)
    return render_page("数据查询", content, active="query",
                       breadcrumb="数据湖 / <b>数据查询</b>", extra_script=script)



# ════════════════════════════════════════════════════════════════
#  数据集管理  (独立副本, 可单独迭代)
# ════════════════════════════════════════════════════════════════

DS_VERSIONS = {}   # ds_id -> [版本记录] (最新在前)
_PROC_SEQ = [0]

def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def ds_versions(d):
    """数据集版本历史: 未发布草稿(最新) + 当前版本 + 历史归档。"""
    if d["id"] not in DS_VERSIONS:
        vtxt = d["version"].lstrip("v")
        n = int(vtxt) if vtxt.isdigit() else 1
        recs = len(d["recordings"])
        notes = {1: "初版采集", 2: "增补采集 + 调整配方", 3: "扩充数据", 4: "修复缺帧"}
        owners = ["Lance Li", "Wei Zhang", "Min Chen"]
        vers = [
            # 未发布草稿 (最新)
            {"version": f"v{n+1}", "created": d["created"], "recordings": recs + 1,
             "status": "待发布", "note": "新增 dagger 数据 (草稿)", "creator": d["owner"]},
            # 当前版本
            {"version": d["version"], "created": d["created"], "recordings": recs,
             "status": "生效中", "note": notes.get(n, "迭代版本"), "creator": d["owner"]},
        ]
        for k in range(n - 1, 0, -1):  # 历史归档
            vers.append({"version": f"v{k}", "created": f"2026-05-{11+k:02d} 10:00",
                         "recordings": max(1, recs - (n - k)), "status": "已归档",
                         "note": notes.get(k, "迭代版本"), "creator": owners[k % len(owners)]})
        DS_VERSIONS[d["id"]] = vers
    return DS_VERSIONS[d["id"]]

@app.route("/datasets")
def datasets():
    sel = request.args.get("sel", "")
    # 默认选中第一个数据集 (在建树前确定, 保证树高亮与详情一致)
    if not sel:
        sel = DATASETS[0]["id"]
    # 业务语义目录 (用户可自建管理), 而非按 train/eval 分
    tree = ('<div class="tree-head">'
            '<span class="th-left"><span class="tp-toggle" onclick="toggleTP(this)" title="折叠/展开目录"><span class="sc-col">&laquo;</span><span class="sc-exp">&raquo;</span></span><span class="th-title">数据集目录</span></span>'
            '<span class="th-actions">'
            '<a href="#" onclick="openDrawerById(\'newFolderDrawer\');return false;" style="font-size:12px;">+ 目录</a>'
            '<a href="#" onclick="openDrawerById(\'newDsDrawer\');return false;" style="font-size:12px;">+ 数据集</a></span></div>')
    all_dataset_tags = sorted({tag for d in DATASETS for tag in dataset_label_names(d)})
    dataset_tag_options = "".join(
        f'<option value="{html.escape(tag, quote=True)}">{html.escape(tag)}</option>'
        for tag in all_dataset_tags
    )
    tree += (
        '<div class="tree-search"><input id="datasetTreeKeyword" placeholder="搜索数据集 / 目录..." '
        'oninput="filterDatasetTree()"></div>'
        '<div class="tree-tag-search">'
        f'<select id="datasetTreeTagFilter" aria-label="标签筛选" onchange="filterDatasetTree()">'
        f'<option value="">请选择标签</option>{dataset_tag_options}</select></div>'
        '<div class="tree-body dataset-tree-body">'
    )
    for folder in V2_FOLDERS:
        dss = [get_ds(i) for i in V2_FOLDER_MAP.get(folder, []) if get_ds(i)]
        empty = len(dss) == 0
        del_item = (f'<div class="rm-item danger" onclick="rmClose();delFolder(\'{folder}\')">删除</div>'
                    if empty else
                    '<div class="rm-item disabled" title="目录不为空, 不可删除">删除</div>')
        tree += (f'<div class="tree-grp" onclick="toggleTree(this)"><span class="caret">&#9656;</span>{folder} '
                 f'<span class="sub" style="color:rgba(0,0,0,0.35);font-weight:400;">({len(dss)})</span>'
                 f'<span class="row-act-wrap" onclick="event.stopPropagation();">'
                 f'<span class="folder-act" onclick="toggleRowMenu(this)">&#8943;</span>'
                 f'<div class="row-menu">'
                 f'<div class="rm-item" onclick="rmClose();openFolderEdit(\'{folder}\')">编辑</div>'
                 f'{del_item}</div></span></div>')
        tree += '<div class="tree-children">'
        if dss:
            for d in dss:
                cls = "active" if d["id"] == sel else ""
                dataset_tags = dataset_label_names(d)
                tags_attr = html.escape("|".join(dataset_tags), quote=True)
                name_attr = html.escape(d["name"].lower(), quote=True)
                tree += (f'<div class="tree-leaf-wrap row-act-wrap dataset-tree-item" '
                         f'data-dataset-name="{name_attr}" data-dataset-tags="{tags_attr}">'
                         f'<a class="tree-leaf {cls}" href="/datasets?sel={d["id"]}">{d["name"]} <span class="sub">· {d["version"]}</span></a>'
                         f'<span class="leaf-act" onclick="event.stopPropagation();toggleRowMenu(this)">&#8943;</span>'
                         f'<div class="row-menu">'
                         f'<div class="rm-item" onclick="rmClose();openDsEdit(\'{d["id"]}\')">编辑</div>'
                         f'</div></div>')
        else:
            tree += '<div class="tree-leaf muted dataset-empty-folder" style="cursor:default;">（空目录）</div>'
        tree += '</div>'
    tree += '</div>'

    if sel == "new":
        right = dataset_new_panel_v2()
    else:
        if not sel:
            sel = DATASETS[0]["id"]
        right = dataset_detail_panel_v2(get_ds(sel) or DATASETS[0], request.args.get("ver", ""))

    folder_opts = "".join(f"<option>{f}</option>" for f in V2_FOLDERS)
    # 数据集 → {名称, 所属目录} 映射 (供编辑/移动弹窗回填)
    ds_folder_of = {}
    for _f, _ids in V2_FOLDER_MAP.items():
        for _i in _ids:
            ds_folder_of[_i] = _f
    ds_meta = {
        d["id"]: {
            "name": d["name"],
            "ident": d["id"],
            "folder": ds_folder_of.get(d["id"], ""),
            "tags": dataset_label_names(d),
        }
        for d in DATASETS
    }
    _folder_slug = {"预训练": "pretrain", "后训练": "posttrain", "自定义01": "custom01", "自定义02": "custom02"}
    folder_meta = {f: {"name": f, "ident": _folder_slug.get(f, f), "parent": ""} for f in V2_FOLDERS}
    ds_meta_js = (f'<script>window._dsMeta={json.dumps(ds_meta, ensure_ascii=False)};'
                  f'window._folderMeta={json.dumps(folder_meta, ensure_ascii=False)};</script>')
    edit_tag_selector = dataset_tag_picker_html("dsEditTags", [], editable=True)
    new_folder_drawer = f"""
    <div class="modal-mask" id="newFolderDrawer" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="modal-box" style="width:440px;">
        <div class="drawer-head"><h3>新建目录</h3><button class="drawer-close" onclick="closeDrawerById('newFolderDrawer')">&times;</button></div>
        <div class="drawer-body">
          <div class="fg"><label><span class="req">*</span>标识</label><input id="newFolderIdent" placeholder="英文唯一标识 如 pretrain_sweep" oninput="var n=document.getElementById('newFolderName'); if(n) n.value=this.value;"><div class="hint">全局唯一, 用于引用</div></div>
          <div class="fg"><label><span class="req">*</span>目录名称</label><input id="newFolderName" placeholder="填写标识后自动带入, 可修改"></div>
          <div class="fg"><label>上级目录</label><select><option>无 (一级目录)</option>{folder_opts}</select><div class="hint">目录最多两层, 仅可挂到一级目录下</div></div>
        </div>
        <div class="drawer-foot">
          <button class="btn" onclick="closeDrawerById('newFolderDrawer')">取消</button>
          <button class="btn-primary btn" onclick="closeDrawerById('newFolderDrawer');toast('Demo: 已创建目录')">确认创建</button>
        </div>
      </div>
    </div>
    <div class="modal-mask" id="folderEditModal" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="modal-box" style="width:440px;">
        <div class="drawer-head"><h3>编辑目录</h3><button class="drawer-close" onclick="closeDrawerById('folderEditModal')">&times;</button></div>
        <div class="drawer-body">
          <div class="fg"><label><span class="req">*</span>目录名称</label><input id="folderEditName"></div>
          <div class="fg"><label>标识</label><input id="folderEditIdent" disabled><div class="hint">标识创建后不可修改</div></div>
          <div class="fg"><label>上级目录</label><select id="folderEditParent"><option>无 (一级目录)</option>{folder_opts}</select><div class="hint">目录最多两层, 仅可挂到一级目录下</div></div>
        </div>
        <div class="drawer-foot">
          <button class="btn" onclick="closeDrawerById('folderEditModal')">取消</button>
          <button class="btn-primary btn" onclick="closeDrawerById('folderEditModal');toast('Demo: 已保存')">确认</button>
        </div>
      </div>
    </div>
    <div class="modal-mask" id="dsEditModal" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="modal-box" style="width:440px;">
        <div class="drawer-head"><h3>编辑数据集</h3><button class="drawer-close" onclick="closeDrawerById('dsEditModal')">&times;</button></div>
        <div class="drawer-body">
          <div class="fg"><label><span class="req">*</span>数据集名称</label><input id="dsEditName"></div>
          <div class="fg"><label>标识</label><input id="dsEditIdent" disabled><div class="hint">标识创建后不可修改</div></div>
          <div class="fg"><label>目录</label><select id="dsEditFolder">{folder_opts}</select></div>
          <div class="fg"><label>标签</label>{edit_tag_selector}</div>
        </div>
        <div class="drawer-foot">
          <button class="btn" onclick="closeDrawerById('dsEditModal')">取消</button>
          <button class="btn-primary btn" onclick="closeDrawerById('dsEditModal');toast('Demo: 已保存')">确认</button>
        </div>
      </div>
    </div>
    """
    new_ds_drawer = f"""
    <div class="modal-mask" id="newDsDrawer" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="modal-box" style="width:780px;max-width:94vw;">
        <div class="drawer-head"><h3>新建数据集</h3><button class="drawer-close" onclick="closeDrawerById('newDsDrawer')">&times;</button></div>
        <div class="drawer-body">
          <div class="ds-hint">&#128161; 可以前往 <a href="/query">数据查询</a> 页面使用 <b>AI 助手</b>, 筛选想要的数据, 一键生成数据集。</div>
          <div class="section-label">数据集信息</div>
          <div class="fg-row">
            <div class="fg"><label><span class="req">*</span>标识</label><input id="newDsIdent" placeholder="英文唯一标识" oninput="var n=document.getElementById('newDsName'); if(n) n.value=this.value;"></div>
            <div class="fg"><label><span class="req">*</span>数据集名称</label><input id="newDsName" placeholder="填写标识后自动带入, 可修改"></div>
          </div>
          <div class="fg"><label>目录</label><select>{folder_opts}</select></div>
          <div class="section-label">筛选条件 <span class="muted" style="font-weight:400;font-size:12px;">不传的条件默认不限制</span></div>
          {build_query_filters()}
        </div>
        <div class="drawer-foot">
          <button class="btn" onclick="closeDrawerById('newDsDrawer')">取消</button>
          <button class="btn-primary btn" onclick="dsCreating('newDsDrawer')">确认创建</button>
        </div>
      </div>
    </div>
    """
    content = (f'<div class="split"><div class="tree-panel">{tree}</div><div class="detail-panel">{right}</div></div>'
               + new_folder_drawer + new_ds_drawer + ds_meta_js)
    # 处理数据后跳到「版本」Tab 并提示
    landed = request.args.get("tab", "")
    land_js = ("""
      var vt=Array.prototype.slice.call(document.querySelectorAll('.tab')).filter(function(x){return x.textContent.trim()==='版本';})[0];
      if(vt) vt.click();
      toast('处理完成: 已生成新版本');
    """ if landed == "version" else "")
    script = """<script>
    function filterDatasetTree(){
      var keyword=(document.getElementById('datasetTreeKeyword').value||'').trim().toLowerCase();
      var tag=document.getElementById('datasetTreeTagFilter').value||'';
      var filtering=Boolean(keyword||tag), anyVisible=false;
      document.querySelectorAll('.dataset-tree-body .tree-children').forEach(function(children){
        var visibleInFolder=0;
        children.querySelectorAll('.dataset-tree-item').forEach(function(item){
          var name=item.getAttribute('data-dataset-name')||'';
          var tags=(item.getAttribute('data-dataset-tags')||'').split('|').filter(Boolean);
          var show=(!keyword||name.indexOf(keyword)>=0||tags.some(function(x){return x.toLowerCase().indexOf(keyword)>=0;}))
            &&(!tag||tags.indexOf(tag)>=0);
          item.style.display=show?'':'none';
          if(show){ visibleInFolder+=1; anyVisible=true; }
        });
        var empty=children.querySelector('.dataset-empty-folder');
        var showEmpty=Boolean(empty&&!filtering);
        if(empty) empty.style.display=showEmpty?'':'none';
        var group=children.previousElementSibling;
        var showGroup=visibleInFolder>0||showEmpty;
        if(group) group.style.display=showGroup?'':'none';
        children.style.display=showGroup?'':'none';
        if(filtering&&showGroup){
          children.classList.remove('collapsed');
          if(group) group.classList.remove('collapsed');
        }
      });
      var emptyState=document.getElementById('datasetTreeFilterEmpty');
      if(!emptyState){
        emptyState=document.createElement('div');
        emptyState.id='datasetTreeFilterEmpty';
        emptyState.className='muted';
        emptyState.style.cssText='display:none;padding:22px 14px;text-align:center;font-size:12px;';
        emptyState.textContent='暂无匹配的数据集';
        document.querySelector('.dataset-tree-body').appendChild(emptyState);
      }
      emptyState.style.display=filtering&&!anyVisible?'':'none';
    }
    window._charts = {
      info: function(){
        var c=document.getElementById('dsHist');
        if(c && window.Chart && !c._drawn){ c._drawn=true;
          new Chart(c,{type:'bar',
            data:{labels:['<900','900-1100','1100-1300','1300-1500','>1500'],datasets:[{label:'episode 数',data:[3,12,18,11,4],backgroundColor:'#1F80A0'}]},
            options:{plugins:{legend:{display:false}},scales:{y:{ticks:{font:{size:10}}},x:{ticks:{font:{size:10}}}}}});
        }
      },
      compose: function(){ if(window._renderPies) window._renderPies(window.__tagPies,'tagPie'); }
    };
    window._renderPies = function(pies, pfx){
      if(!pies||!window.Chart) return;
      var pal=['#1F80A0','#36cfc9','#faad14','#52c41a','#722ed1','#ff7a45','#13c2c2','#eb2f96','#a0d911','#2f54eb','#ff85c0','#ffc53d'];
      var tot=function(a){return a.reduce(function(s,x){return s+x;},0)||1;};
      var pieLabels={id:'pieLabels', afterDatasetsDraw:function(chart){
        var ctx=chart.ctx, meta=chart.getDatasetMeta(0), ds=chart.data.datasets[0];
        var sum=ds.data.reduce(function(s,x){return s+x;},0)||1;
        ctx.save(); ctx.font='11px sans-serif'; ctx.textAlign='center'; ctx.textBaseline='middle';
        meta.data.forEach(function(arc,i){
          if(ds.data[i]/sum < 0.06) return;        // 太小的扇区不标, 避免重叠
          var ang=(arc.startAngle+arc.endAngle)/2, r=(arc.innerRadius+arc.outerRadius)/2;
          var x=arc.x+Math.cos(ang)*r, y=arc.y+Math.sin(ang)*r;
          ctx.lineWidth=2.5; ctx.strokeStyle='rgba(0,0,0,0.40)'; ctx.strokeText(chart.data.labels[i],x,y);
          ctx.fillStyle='#fff'; ctx.fillText(chart.data.labels[i],x,y);
        });
        ctx.restore();
      }};
      pies.forEach(function(p,i){
        var c=document.getElementById(pfx+i); if(!c||c._drawn) return; c._drawn=true;
        var sum=tot(p.vals);
        new Chart(c,{type:'pie',
          data:{labels:p.labels,datasets:[{data:p.vals,backgroundColor:(p.colors||p.labels.map(function(_,j){return pal[j%pal.length];})),borderWidth:1,borderColor:'#fff'}]},
          options:{maintainAspectRatio:false,plugins:{legend:{display:false},
            tooltip:{callbacks:{label:function(x){return x.label+': '+Math.round(x.parsed/sum*100)+'%';}}}}},
          plugins:[pieLabels]});
      });
    };
    function cmpTab(btn, which){
      var bar=btn.parentNode; bar.querySelectorAll('.ep-tab').forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      document.getElementById('cmp_high').style.display=(which==='high')?'':'none';
      document.getElementById('cmp_low').style.display=(which==='low')?'':'none';
      if(which==='low' && window._renderPies) window._renderPies(window.__tagPiesLow,'tagPieL');
    }
    function levelSel(sel, dim){
      var l2=document.getElementById('tag_'+dim+'_l2'), l3=document.getElementById('tag_'+dim+'_l3');
      var isL3=sel.value==='l3';
      if(l2) l2.style.display=isL3?'none':'';
      if(l3) l3.style.display=isL3?'':'none';
      if(isL3 && window._renderPies) window._renderPies(window.__tagPies3, dim==='high'?'tagPie3':'tagPieL3');
    }
    var _infoCM=null;
    function initInfoJson(){
      if(_infoCM) return;
      var ta=document.getElementById('dsFullJson');
      if(!ta || !window.CodeMirror) return;
      _infoCM=CodeMirror.fromTextArea(ta,{mode:{name:'javascript',json:true},theme:'material-darker',lineNumbers:true,readOnly:true,lineWrapping:false});
      _infoCM.setSize('100%','auto');
    }
    function infoTab(btn, which){
      var bar=btn.parentNode; bar.querySelectorAll('.ep-tab').forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      document.getElementById('info_sum').style.display=(which==='sum')?'':'none';
      document.getElementById('info_full').style.display=(which==='full')?'':'none';
      if(which==='full'){ initInfoJson(); if(_infoCM) setTimeout(function(){_infoCM.refresh();},10); }
    }
    document.addEventListener('DOMContentLoaded', function(){""" + land_js + """});
    </script>"""
    return render_page("数据集管理", content, active="datasets",
                       breadcrumb='数据集 / <b>数据集管理</b>', extra_script=script)


def dataset_detail_panel_v2(d, viewed_ver=""):
    ds_format = "Mozdataset" if d.get("type") in ("eval-benchmark", "custom") or "eval" in d["name"].lower() or "smoke" in d["name"].lower() else "LeRobot"
    eps = dataset_episodes(d)
    dataset_labels = dataset_label_names(d)
    dataset_labels_html = dataset_tag_picker_html(
        f'datasetInfoTags-{d["id"]}',
        dataset_labels,
        editable=False,
    )
    _hl_items = dataset_prompt_composition(d)   # highlevel prompt 构成 (info / compose 共用)
    preview = (f'<div class="tab-pane active" id="pane-preview">'
               f'<div class="muted" style="margin-bottom:12px;">数据集共 {d["episodes"]} 个 episode，每个 episode ← 一条原始 recording，可在左侧逐条预览</div>'
               f'{preview_block("dsv2", eps)}</div>')
    # 完整信息: 贴合「LeRobot v2.1 完整结构」的真实元数据实例 (纯 key/value, 无说明)
    _joint_names = [f"joint{k}" for k in range(7)]
    _cart_names = ["x", "y", "z", "rx", "ry", "rz"]
    _features = {}
    for _side in ("leftarm", "rightarm"):
        _features[f"{_side}_cmd_cart_pos"] = {"dtype": "float32", "shape": [6], "names": _cart_names}
        _features[f"{_side}_state_cart_pos"] = {"dtype": "float32", "shape": [6], "names": _cart_names}
        _features[f"{_side}_cmd_joint_pos"] = {"dtype": "float32", "shape": [7], "names": _joint_names}
        _features[f"{_side}_state_joint_pos"] = {"dtype": "float32", "shape": [7], "names": _joint_names}
        _features[f"{_side}_cmd_psi"] = {"dtype": "float32", "shape": [1], "names": None}
        _features[f"{_side}_state_psi"] = {"dtype": "float32", "shape": [1], "names": None}
        _features[f"{_side}_gripper_cmd_pos"] = {"dtype": "float32", "shape": [1], "names": None}
        _features[f"{_side}_gripper_state_pos"] = {"dtype": "float32", "shape": [1], "names": None}
    for _cam in ("cam_high", "cam_left_wrist", "cam_right_wrist"):
        _features[_cam] = {"dtype": "video", "shape": [240, 320, 3], "names": ["height", "width", "channels"],
                           "info": {"video.codec": "h264", "video.fps": 30, "video.pix_fmt": "yuv420p"}}
    for _sys, _dt in (("timestamp", "float32"), ("frame_index", "int64"), ("episode_index", "int64"),
                      ("index", "int64"), ("task_index", "int64")):
        _features[_sys] = {"dtype": _dt, "shape": [1], "names": None}

    _eps_meta = dataset_episodes(d)
    _task0 = _hl_items[0]["name"] if _hl_items else "Moz1 Exoskeleton Collection"
    _info = {
        "codebase_version": "v2.1",
        "robot_type": d["robot"],
        "version": d["version"],
        "fps": 30,
        "chunks_size": 1000,
        "data_path": "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet",
        "video_path": "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        "total_episodes": d["episodes"],
        "total_frames": d["frames"],
        "total_tasks": len(_hl_items),
        "total_videos": d["episodes"] * 3,
        "total_chunks": (d["episodes"] + 999) // 1000,
        "splits": {"train": f"0:{d['episodes']}"},
        "features": _features,
    }
    _tasks = [{"task_index": i, "task": it["name"]} for i, it in enumerate(_hl_items)] or [{"task_index": 0, "task": _task0}]
    _episodes = [{"episode_index": e["idx"], "length": e["length"], "tasks": [_task0],
                  "task_id_map": None, "annotation": None, "inspection": None,
                  "dagger_type": None, "dagger_group_idx": None} for e in _eps_meta[:3]]
    _len0 = _eps_meta[0]["length"] if _eps_meta else 1434
    _episodes_stats = [{
        "episode_index": 0,
        "stats": {
            "leftarm_state_joint_pos": {
                "min": [-1.21, -0.83, -1.05, -2.10, -1.34, -0.92, -1.47],
                "max": [1.18, 0.95, 1.12, 0.41, 1.29, 0.88, 1.51],
                "mean": [0.02, 0.11, -0.07, -0.88, 0.05, -0.03, 0.12],
                "std": [0.44, 0.38, 0.41, 0.52, 0.47, 0.33, 0.49],
                "count": [_len0],
            },
            "cam_high": {
                "min": [[[0.0]], [[0.0]], [[0.0]]],
                "max": [[[1.0]], [[1.0]], [[1.0]]],
                "mean": [[[0.43]], [[0.41]], [[0.39]]],
                "std": [[[0.24]], [[0.22]], [[0.25]]],
                "count": [_len0],
            },
        },
    }]
    ds_full = {
        "dataset_name": d["name"],
        "meta/info.json": _info,
        "meta/tasks.jsonl": _tasks,
        "meta/episodes.jsonl": _episodes,
        "meta/episodes_stats.jsonl": _episodes_stats,
    }
    ds_full_json = json.dumps(ds_full, ensure_ascii=False, indent=2)
    info = f"""
    <div class="tab-pane" id="pane-info">
      <div class="ep-tabs">
        <button class="ep-tab active" onclick="infoTab(this,'sum')">摘要信息</button>
        <button class="ep-tab" onclick="infoTab(this,'full')">完整信息</button>
      </div>
      <div class="info-pane" id="info_sum">
        <div class="desc-grid">
          <div class="dk">名称</div><div class="dv">{d['name']}</div>
          <div class="dk">标识</div><div class="dv" style="font-family:monospace;">{d['id']}</div>
          <div class="dk">数据格式</div><div class="dv">{ds_format}</div>
          <div class="dk">标签</div><div class="dv" data-dataset-info-field="tags">{dataset_labels_html}</div>
          <div class="dk">本体</div><div class="dv">{d['robot']}</div>
          <div class="dk">规模</div><div class="dv">{d['episodes']} episodes · {d['frames']:,} frames · {round(d['frames']/30/60,1)} min</div>
          <div class="dk">创建人</div><div class="dv">{d['owner']}</div>
          <div class="dk">创建时间</div><div class="dv">{d['created']}</div>
          <div class="dk">TOS</div><div class="dv" style="font-family:monospace;font-size:12px;">{d['tos']}</div>
        </div>
      </div>
      <div class="info-pane" id="info_full" style="display:none;">
        <textarea id="dsFullJson" class="code-editor">{ds_full_json}</textarea>
      </div>
    </div>
    """
    prompt_rows = comp_rows_html(_hl_items, d["frames"])
    # 按一级维度的标签帧数 (三个饼图 + 表格图例)
    _byp = {}
    for r in _dataset_recs(d):
        for tid in rec_tags(r):
            _byp[tid] = _byp.get(tid, 0) + r["frames"]
    _pal = ["#1F80A0", "#36cfc9", "#faad14", "#52c41a", "#722ed1", "#ff7a45",
            "#13c2c2", "#eb2f96", "#a0d911", "#2f54eb", "#ff85c0", "#ffc53d"]
    pies = []
    for grp in TAG_GROUP_ORDER:
        items = sorted([(TAG_LABEL[t], fr) for t, fr in _byp.items() if _TAG_GROUP.get(t) == grp], key=lambda x: -x[1])
        if items:
            total = sum(v for _, v in items) or 1
            labels = [i[0] for i in items]
            vals = [i[1] for i in items]
            colors = [_pal[j % len(_pal)] for j in range(len(items))]
            pcts = [round(v / total * 100) for v in vals]
            pies.append({"group": grp, "labels": labels, "vals": vals, "colors": colors, "pcts": pcts})
    pies_json = json.dumps([{"labels": p["labels"], "vals": p["vals"], "colors": p["colors"]} for p in pies])
    # 三级: 每个二级标签再拆两个细分 (demo)
    pies3 = []
    for p in pies:
        labels3, vals3, colors3 = [], [], []
        for lab, v, c in zip(p["labels"], p["vals"], p["colors"]):
            a = round(v * 0.6); b = v - a
            labels3 += [lab + "·细分A", lab + "·细分B"]
            vals3 += [a, b]
            colors3 += [c, c + "88"]
        tot3 = sum(vals3) or 1
        pcts3 = [round(x / tot3 * 100) for x in vals3]
        pies3.append({"group": p["group"], "labels": labels3, "vals": vals3, "colors": colors3, "pcts": pcts3})
    pies3_json = json.dumps([{"labels": p["labels"], "vals": p["vals"], "colors": p["colors"]} for p in pies3])

    def pie_legend(p):
        rows = "".join(
            f'<tr><td><i style="background:{c}"></i>{lab}</td><td class="pct">{pct}%</td></tr>'
            for lab, c, pct in zip(p["labels"], p["colors"], p["pcts"]))
        return f'<table class="pie-legend"><tbody>{rows}</tbody></table>'

    def pie_cells_html(idpfx, plist):
        return "".join(
            f'<div class="pie-cell"><div class="pie-title">{p["group"]}</div>'
            f'<div class="pie-box"><canvas id="{idpfx}{i}"></canvas></div>{pie_legend(p)}</div>'
            for i, p in enumerate(plist))
    pie_cells_h2 = pie_cells_html("tagPie", pies)
    pie_cells_h3 = pie_cells_html("tagPie3", pies3)
    pie_cells_l2 = pie_cells_html("tagPieL", pies)
    pie_cells_l3 = pie_cells_html("tagPieL3", pies3)

    def level_sel(dim):
        return (f'<select class="lvl-sel" onchange="levelSel(this,\'{dim}\')">'
                '<option value="l2">展示层级：二级</option>'
                '<option value="l3">展示层级：三级</option></select>')
    # Lowlevel(子动作)维度 prompt 构成 (demo)
    _low_defs = [("接近/对准目标", 0.18), ("抓取物体", 0.22), ("移动/搬运", 0.20),
                 ("放置/对位", 0.16), ("擦拭/操作", 0.14), ("复位/收回", 0.10)]
    low_prompt_rows = comp_rows_html([{"name": n, "ratio": r} for n, r in _low_defs], d["frames"])
    compose = f"""
    <div class="tab-pane" id="pane-compose">
      <div class="muted" style="margin-bottom:14px;">数据集共 {d['episodes']} episode · {len(_hl_items)} highlevel · {len(_low_defs)} lowlevel <span style="color:rgba(0,0,0,0.3);">(highlevel / lowlevel 按去重计数)</span></div>
      <div class="ep-tabs">
        <button class="ep-tab active" onclick="cmpTab(this,'high')">HighLevel 维度</button>
        <button class="ep-tab" onclick="cmpTab(this,'low')">Lowlevel 维度</button>
      </div>
      <div class="cmp-pane" id="cmp_high">
        <h4 class="va-h" style="margin-top:6px;">Prompt 构成 <span class="muted" style="font-weight:400;font-size:12px;">按 highlevel 任务 prompt 的帧数占比</span></h4>
        {prompt_rows}
        <h4 class="va-h">标签构成 <span class="muted" style="font-weight:400;font-size:12px;">各维度内标签的帧数占比</span>{level_sel('high')}</h4>
        <div class="pie-row" id="tag_high_l2">{pie_cells_h2}</div>
        <div class="pie-row" id="tag_high_l3" style="display:none;">{pie_cells_h3}</div>
      </div>
      <div class="cmp-pane" id="cmp_low" style="display:none;">
        <h4 class="va-h" style="margin-top:6px;">Prompt 构成 <span class="muted" style="font-weight:400;font-size:12px;">按 lowlevel 子动作 prompt 的帧数占比</span></h4>
        {low_prompt_rows}
        <h4 class="va-h">标签构成 <span class="muted" style="font-weight:400;font-size:12px;">各维度内标签的帧数占比</span>{level_sel('low')}</h4>
        <div class="pie-row" id="tag_low_l2">{pie_cells_l2}</div>
        <div class="pie-row" id="tag_low_l3" style="display:none;">{pie_cells_l3}</div>
      </div>
      <script>window.__tagPies={pies_json};window.__tagPiesLow={pies_json};window.__tagPies3={pies3_json};</script>
    </div>
    """
    checks = doctor_checks(d["quality"])
    n_ep = d["episodes"] or 1
    def _rule_pct(st, desc):
        if st == "pass":
            return 100
        m = re.search(r"(\d+)\s*个 episode", desc)
        if m:
            return max(0, round((n_ep - int(m.group(1))) / n_ep * 100))
        return 82 if st == "fail" else 96
    crows = ""
    for n, st, dd in checks:
        pct = _rule_pct(st, dd)
        barcls = "ok" if pct >= 99 else ("warn" if pct >= 85 else "bad")
        crows += (f'<div class="check-row"><span class="badge {st}">{st.upper()}</span>'
                  f'<span class="cname">{n}</span><span class="cdesc">{dd}</span>'
                  f'<span class="check-pct"><span class="cp-bar {barcls}"><i style="width:{pct}%"></i></span>'
                  f'<span class="cp-num">{pct}%</span></span></div>')
    banner_txt = {"pass": "检查通过, 可进训练队列", "warn": "部分规则校验不通过", "fail": "必须修复才能用"}[d["quality"]]
    quality = f"""
    <div class="tab-pane" id="pane-quality">
      <div class="doctor-banner {d['quality']}">{d['quality'].upper()} — {banner_txt}</div>
      {crows}
    </div>
    """
    # 上游来源表: 按采集批次分组
    up_groups = {}
    for rid in d["recordings"]:
        r = get_rec(rid)
        if not r:
            continue
        up_groups.setdefault((r["collection"], r["type"]), []).append(rid)
    up_rows = ""
    for (coll, typ), rids in up_groups.items():
        links = " · ".join(f'<a href="/lake?mode=flat&sel={x}">#{x}</a>' for x in rids)
        up_rows += (f'<tr><td>采集任务 task {coll}</td><td><span class="tag tag-gray">{typ}</span></td>'
                    f'<td>{len(rids)}</td><td>{links}</td></tr>')
    if not up_rows:
        up_rows = '<tr><td colspan="4" class="muted">—</td></tr>'

    # 下游引用表: 记录引用的版本
    _pubvers = [v["version"] for v in ds_versions(d) if v["status"] != "待发布"] or [d["version"]]
    down_rows = ""
    for i, u in enumerate(d["used_by"]):
        kind = "评测" if u.startswith("eval") else "训练"
        ver = _pubvers[i % len(_pubvers)]
        down_rows += (f'<tr><td>{u}</td><td><span class="tag tag-gray">{kind}</span></td>'
                      f'<td><b>{ver}</b></td></tr>')
    if not down_rows:
        down_rows = '<tr><td colspan="3" class="muted">暂未被训练/评测任务引用</td></tr>'

    vrows = ""
    for v in ds_versions(d):
        if v["status"] == "待发布":
            name_cell = f'<span class="muted">{v["version"]}</span>'
            op = f'<a href="/datasets/{d["id"]}/version/{v["version"]}/publish">发布</a>'
        elif v["status"] == "已归档":
            name_cell = f'<span class="muted">{v["version"]}</span>'
            op = f'<a href="/datasets/{d["id"]}/version/{v["version"]}/rollback">回退</a>'
        else:  # 生效中
            name_cell = (f'<b>{v["version"]}</b> <span class="tag tag-blue">生效中</span>'
                         if v["version"] == d["version"] else f'<span class="muted">{v["version"]}</span>')
            op = '<span class="muted">—</span>'
        vrows += (f'<tr><td>{name_cell}</td><td class="muted">{v.get("note","")}</td>'
                  f'<td>{v["recordings"]}</td><td>{v.get("creator","—")}</td>'
                  f'<td class="muted">{v["created"]}</td><td>{v["status"]}</td>'
                  f'<td class="actions-cell">{op}</td></tr>')
    version = f"""
    <div class="tab-pane" id="pane-version">
      <table class="ant-table"><thead><tr><th>版本</th><th>说明</th><th>数据数</th><th>创建人</th><th>创建时间</th><th>状态</th><th>操作</th></tr></thead>
      <tbody>{vrows}</tbody></table>
      <div class="muted" style="margin-top:12px;">改配方 / 处理数据 = 出新版本, 被训练引用的版本不可变, 保证实验可复现。</div>
    </div>
    """
    publish_btn = ('<button class="btn-primary btn" onclick="toast(\'Demo: 已开始发布并上传 TOS...\')">发布 / 上传 TOS</button>'
                   if d["status"] != "生效中" else "")

    # 处理数据抽屉: 选任务 + 参数(结构化/代码) → 执行生成新版本
    pl_opts = "".join(f'<option value="task|{p["name"]}">{p["name"]}</option>' for p in PIPELINES)
    cur_ver = ds_versions(d)[0]["version"]
    # 每个工作流已配置好的参数 key (来自其算子定义, 不可改, 只能填 value)
    task_params = {}
    for p in PIPELINES:
        keys = []
        for sid in p["stages"]:
            op = next((o for o in OPERATORS if o["id"] == sid), None)
            if not op:
                continue
            for item in op["params"].split(" / "):
                k = item.strip().split(" ")[0]
                if k and k not in keys:
                    keys.append(k)
        task_params[p["name"]] = keys
    task_params_js = json.dumps(task_params, ensure_ascii=False)
    drawer = f"""
    <div class="modal-mask" id="procDrawer" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="modal-box" style="width:600px;max-width:94vw;">
        <div class="drawer-head"><h3>处理数据 — {d['name']} ({cur_ver})</h3>
          <button class="drawer-close" onclick="document.getElementById('procDrawer').classList.remove('active')">&times;</button></div>
        <form method="post" action="/datasets/{d['id']}/process" style="display:flex;flex-direction:column;min-height:0;flex:1;">
          <div class="drawer-body">
            <div class="section-label">工作流</div>
            <div class="fg">
              <select name="op" onchange="procRenderParams()">{pl_opts}</select>
              <div class="hint">在当前数据集 {cur_ver} 上执行该工作流, 产出一个新版本</div>
            </div>
            <div class="section-label">处理说明</div>
            <div class="fg"><input name="note" placeholder="本次处理做了什么 (可选)"></div>
            <div class="section-label">请求参数</div>
            <div class="param-mode">
              <button type="button" class="pm-btn active" data-m="code" onclick="procMode('code')">代码</button>
              <button type="button" class="pm-btn" data-m="struct" onclick="procMode('struct')">结构化</button>
            </div>
            <div class="proc-params-area">
              <div id="procCode">
                <div class="fg" style="margin-bottom:0;"><textarea name="params_code" class="code-editor" rows="8" placeholder="# 命令行参数 / JSON&#10;--train-ratio 0.95 --seed 42"></textarea></div>
              </div>
              <div id="procStruct" style="display:none;">
                <div class="hint" style="margin-bottom:8px;">参数名由所选工作流的算子配置决定, 此处仅填写取值。</div>
                <div id="procParamBox"></div>
              </div>
            </div>
          </div>
          <div class="drawer-foot">
            <button type="button" class="btn" onclick="document.getElementById('procDrawer').classList.remove('active')">取消</button>
            <button type="submit" class="btn-primary btn">确认执行</button>
          </div>
        </form>
      </div>
      <script>
      function procMode(m){{
        document.getElementById('procStruct').style.display = m==='struct'?'':'none';
        document.getElementById('procCode').style.display = m==='code'?'':'none';
        document.querySelectorAll('.param-mode .pm-btn').forEach(function(b){{ b.classList.toggle('active', b.getAttribute('data-m')===m); }});
      }}
      window._taskParams = {task_params_js};
      function procRenderParams(){{
        var sel=document.querySelector('#procDrawer select[name=op]');
        var name=(sel.value.split('|')[1]||sel.value);
        var keys=(window._taskParams||{{}})[name]||[];
        var box=document.getElementById('procParamBox');
        if(!keys.length){{ box.innerHTML='<div class="muted" style="font-size:12px;padding:4px 0;">该工作流无可配置参数</div>'; return; }}
        box.innerHTML='<table class="param-table"><tbody>'+keys.map(function(k){{
          return '<tr><td class="pk" style="font-family:monospace;font-size:12px;color:rgba(0,0,0,0.7);">'+k+'</td>'+
            '<td><input class="fp-val" placeholder="填写值"></td></tr>';
        }}).join('')+'</tbody></table>';
      }}
      procRenderParams();
      </script>
    </div>
    """
    # 版本号下拉 (可切换查看)
    _vlist = ds_versions(d)
    viewed = viewed_ver if any(v["version"] == viewed_ver for v in _vlist) else d["version"]
    _vopts = ""
    for v in _vlist:
        lab = v["version"]
        s = " selected" if v["version"] == viewed else ""
        _vopts += f'<option value="{v["version"]}"{s}>{lab}</option>'
    ver_select = (f'<select class="ver-select" onchange="if(this.value)location.href=\'/datasets?sel={d["id"]}&ver=\'+this.value">'
                  f'{_vopts}</select>')
    head = f"""
    <div class="detail-head">
      <div><div class="dh-title">{d['name']} <span class="tag tag-blue">{ds_format}</span> {ver_select}</div>
      <div class="dh-meta"><span>{d['episodes']} ep · {d['frames']:,} f</span></div></div>
      <div class="dataset-detail-actions"><button class="btn btn-secondary" onclick="document.getElementById('procDrawer').classList.add('active')">&#9881; 处理数据</button> {publish_btn}</div>
    </div>
    <div class="tabs">
      <div class="tab active" onclick="switchTab(this,'preview')">数据预览</div>
      <div class="tab" onclick="switchTab(this,'compose')">构成分析</div>
      <div class="tab" onclick="switchTab(this,'version')">版本</div>
      <div class="tab" onclick="switchTab(this,'info')">基本信息</div>
    </div>
    <div class="pane-wrap">{preview}{compose}{version}{info}</div>
    {drawer}
    """
    return head


@app.route("/datasets/<did>/version/<ver>/publish")
def datasets_publish(did, ver):
    d = get_ds(did)
    if not d:
        return redirect("/datasets")
    vers = ds_versions(d)
    # 旧的当前发布版 → 归档
    for v in vers:
        if v["version"] == d["version"] and v["status"] == "生效中":
            v["status"] = "已归档"
    # 目标草稿 → 生效中, 成为当前
    for v in vers:
        if v["version"] == ver and v["status"] == "待发布":
            v["status"], v["created"] = "生效中", _now()
            d["version"], d["status"] = ver, "生效中"
    return redirect(f"/datasets?sel={did}&tab=version")


@app.route("/datasets/<did>/version/<ver>/rollback")
def datasets_rollback(did, ver):
    d = get_ds(did)
    if not d:
        return redirect("/datasets")
    vers = ds_versions(d)
    src = next((v for v in vers if v["version"] == ver), None)
    if src:
        nums = [int(v["version"].lstrip("v")) for v in vers if v["version"].lstrip("v").isdigit()]
        newn = (max(nums) + 1) if nums else 1
        vers.insert(0, {"version": f"v{newn}", "created": _now(), "recordings": src["recordings"],
                        "status": "待发布", "note": f"回退自 {ver}", "creator": "joanna.qiao"})
    return redirect(f"/datasets?sel={did}&tab=version")


@app.route("/datasets/<did>/process", methods=["POST"])
def datasets_process(did):
    d = get_ds(did)
    if not d:
        return redirect("/datasets")
    raw = request.form.get("op", "op|处理算子")
    kind, op_name = (raw.split("|", 1) + [""])[:2] if "|" in raw else ("op", raw)
    note = request.form.get("note", "").strip() or f"经「{op_name}」处理生成"
    now = _now()
    # 1) 生成新版本
    vers = ds_versions(d)
    prev = vers[0]["version"]
    try:
        new_ver = "v" + str(int(prev.lstrip("v")) + 1)
    except ValueError:
        new_ver = prev + ".1"
    vers.insert(0, {"version": new_ver, "created": now, "recordings": len(d["recordings"]),
                    "status": "待发布", "note": note, "creator": "joanna.qiao"})
    d["version"], d["created"], d["status"] = new_ver, now, "待发布"
    # 2) 写一条执行记录
    _PROC_SEQ[0] += 1
    RUNS.insert(0, {
        "id": f"proc_{_PROC_SEQ[0]:04d}", "pipeline": "", "name": op_name,
        "target": f"{d['name']} {new_ver}", "status": "done", "progress": 100,
        "stage": "完成", "at": now, "dur": "1m 20s",
    })
    return redirect(f"/datasets?sel={did}&tab=version")


def dataset_new_panel_v2():
    steps = ["筛选", "配方", "切分", "生成"]
    step_html = ""
    for i, s in enumerate(steps):
        cls = "active" if i == 1 else ("done" if i == 0 else "")
        step_html += f'<div class="step {cls}"><span class="sn">{i+1}</span><div class="st">{s}</div></div>'
    rec_rows = ""
    for r in RECORDINGS[:6]:
        rec_rows += f"""<tr><td><input type="checkbox" checked></td><td>#{r['id']}</td><td>{task_name(r['task'])}</td>
        <td>{r['type']}</td><td>{r['frames']:,}</td></tr>"""
    return f"""
    <div class="detail-head"><div class="dh-title">新建数据集 <span class="tag tag-blue">向导</span></div></div>
    <div style="padding:24px;flex:1;min-height:0;overflow-y:auto;">
      <div class="steps">{step_html}</div>
      <div class="card" style="margin-bottom:16px;">
        <h4>① 筛选 — 从数据湖挑 recording <span class="muted">(三层: 硬指标滑块 / 排行榜+flag / 诊断标签 · 诊断不删)</span></h4>
        <div class="filter-bar">
          <select class="has-value"><option>task: 擦白板</option></select>
          <select class="has-value"><option>类型: 采集</option></select>
          <select class="has-value"><option>状态: 可用</option></select>
          <button class="btn" onclick="resetFilters(this)">重置</button>
          <button class="btn-primary btn" onclick="queryFilters(this)">查询</button>
          <span class="muted">动作量排行榜 / smoothness 诊断标签可在此 flag 异常</span>
        </div>
        <table class="ant-table"><thead><tr><th></th><th>ID</th><th>Task</th><th>类型</th><th>帧数</th></tr></thead><tbody>{rec_rows}</tbody></table>
      </div>
      <div class="card" style="margin-bottom:16px;">
        <h4>② 配方 — 采样权重 + 分组 <span class="muted">(右侧实时显示 权重 vs 帧数 vs 实际采样占比 = 采样验证 ⓥ)</span></h4>
        <div class="recipe-row"><div class="rname">擦白板-采集</div><div class="rbar"><div class="fill" style="width:70%">70%</div></div><div class="muted">权重 0.7</div></div>
        <div class="recipe-row"><div class="rname">擦白板-dagger</div><div class="rbar"><div class="fill" style="width:30%">30%</div></div><div class="muted">权重 0.3</div></div>
      </div>
      <div class="card" style="margin-bottom:16px;">
        <h4>③ 切分 — train / val / eval</h4>
        <div class="filter-bar"><select class="has-value"><option>类型: train</option></select>
        <input value="train_ratio = 0.95" style="width:160px;"><input value="seed = 42" style="width:120px;">
        <button class="btn" onclick="resetFilters(this)">重置</button>
        <button class="btn-primary btn" onclick="queryFilters(this)">查询</button>
        <span class="qa qa-warn">eval 泄漏检查: 通过, 未碰评测集 recording</span></div>
      </div>
      <button class="btn-primary btn" onclick="toast('Demo: 已提交生成任务, 见执行记录')">④ 生成快照</button>
    </div>
    """


@app.route("/operators")
def operators():
    displayed_operators = MANAGED_OPERATORS
    cat_order = ["标注"]

    rows = ""
    for cat in cat_order:
        for op in [o for o in displayed_operators if o["cat"] == cat]:
            rows += f"""<tr>
              <td><b>{op['name']}</b></td>
              <td><span class="op-script">{op['ident']}</span></td>
              <td class="muted" style="max-width:460px;"><span class="desc-clamp">{op['desc']}</span></td>
              <td>{op['creator']}</td>
              <td class="actions-cell"><a href="/pipelines?op={op['id']}">关联工作流</a></td>
            </tr>"""

    ops_js = json.dumps({o["id"]: {"name": o["name"], "ident": o["ident"], "script": o["script"],
                                   "cat": o["cat"], "creator": o["creator"], "desc": o["desc"],
                                   "params": o["params"], "returns": o["returns"]} for o in displayed_operators})

    creator_checks = "".join(
        f'<label><input type="checkbox" value="{c}" onchange="msUpdate(this)">{c}</label>'
        for c in sorted(set(o["creator"] for o in displayed_operators)))
    content = f"""
    <div class="dpr-intro"><div><h1>算子管理</h1></div></div>
    <div class="q-filters rule-filter-panel">
      <div class="q-filter-row">
        <div class="q-field">
          <label>算子名称</label>
          <input placeholder="请输入算子名称 / 标识">
        </div>
        <div class="q-field">
          <label>创建人</label>
          <div class="ms-wrap">
            <div class="ms-trigger" onclick="this.closest('.ms-wrap').classList.toggle('open')"><span class="ms-label">全部创建人</span></div>
            <div class="ms-panel">{creator_checks}</div>
          </div>
        </div>
        <div class="q-actions">
          <button type="button" class="btn" onclick="resetFilters(this)">清空</button>
          <button type="button" class="btn btn-primary" onclick="queryFilters(this)">查询</button>
        </div>
      </div>
    </div>
    <div class="muted" style="margin-bottom:12px;">每个算子 = 一个「原子处理能力」的封装, 可被编排到工作流。</div>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr><th>名称</th><th>标识</th><th>描述</th><th>创建人</th><th>操作</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <!-- 新建 / 编辑 算子 抽屉 -->
    <div class="drawer-mask" id="opFormDrawer" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="drawer op-drawer">
        <div class="drawer-head"><h3 id="opFormTitle">新建算子</h3><button class="drawer-close" onclick="document.getElementById('opFormDrawer').classList.remove('active')">&times;</button></div>
        <div class="drawer-body">
          <div class="section-label">基本信息</div>
          <div class="fg"><label><span class="req">*</span>名称</label><input id="of_name" placeholder="如: 通用导出 Export"></div>
          <div class="fg"><label><span class="req">*</span>标识</label><input id="of_ident" placeholder="英文唯一标识, 如 export_dataset"><div class="hint">编排/调用时引用, 全局唯一</div></div>
          <div class="fg"><label>描述</label><textarea id="of_desc" placeholder="算子做什么 / 核心逻辑"></textarea></div>
          <div class="fg"><label>是否启用</label><select id="of_enabled"><option>启用</option><option>停用</option></select></div>

          <div class="section-label">执行配置</div>
          <div class="fg"><label>运行镜像</label><select id="of_image"><option>frontdesk-py3.10:latest</option><option>lerobot-base:v2.1</option><option>自定义...</option></select></div>
          <div class="fg"><label><span class="req">*</span>入口脚本 / 命令</label><textarea id="of_script" class="code-editor" rows="4" placeholder="# 入口脚本 / 命令&#10;python export_dataset.py --task-ids 3635 --include-unchecked"></textarea></div>

          <div class="section-label">接口定义</div>
          <div class="fg"><label>请求参数</label><textarea id="of_params" class="code-editor" rows="4" placeholder="# 每行一个&#10;--task-ids        采集任务 id (必填)&#10;--output-dir      输出目录"></textarea></div>
          <div class="fg"><label>返回结果</label><textarea id="of_returns" class="code-editor" rows="3" placeholder="# 算子产出&#10;LeRobot 数据集目录 / 报告 JSON / CSV"></textarea></div>
        </div>
        <div class="drawer-foot">
          <label id="of_syncTaskWrap" class="foot-check"><input type="checkbox" id="of_syncTask" checked> 同步创建工作流</label>
          <button class="btn" onclick="document.getElementById('opFormDrawer').classList.remove('active')">取消</button>
          <button class="btn btn-secondary" onclick="document.getElementById('opFormDrawer').classList.remove('active');toast('Demo: 已保存')">保存</button>
          <button class="btn-primary btn" id="of_saveNewVer" onclick="document.getElementById('opFormDrawer').classList.remove('active');toast('Demo: 已保存为新版本')">保存为新版本</button>
        </div>
      </div>
    </div>

    <!-- 算子详情 抽屉 -->
    <div class="drawer-mask" id="opDetailDrawer" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="drawer op-drawer">
        <div class="drawer-head"><h3 id="opDetailTitle">算子详情</h3><button class="drawer-close" onclick="document.getElementById('opDetailDrawer').classList.remove('active')">&times;</button></div>
        <div class="drawer-body" id="opDetailBody"></div>
        <div class="drawer-foot">
          <button class="btn" onclick="toast('Demo: 运行算子')">运行</button>
          <button class="btn-primary btn" id="opDetailEdit">编辑</button>
        </div>
      </div>
    </div>
    <script>
    window.OPS = {ops_js};
    function msUpdate(cb){{
      var wrap=cb.closest('.ms-wrap'); var n=wrap.querySelectorAll('input:checked').length;
      wrap.querySelector('.ms-label').textContent = n ? ('创建人 ('+n+')') : '创建人';
    }}
    document.addEventListener('click', function(e){{
      document.querySelectorAll('.ms-wrap.open').forEach(function(w){{ if(!w.contains(e.target)) w.classList.remove('open'); }});
    }});
    function openOpForm(id){{
      var o = id ? window.OPS[id] : null;
      document.getElementById('opFormTitle').textContent = o ? '编辑算子' : '新建算子';
      var set=function(k,v){{ document.getElementById(k).value = v||''; }};
      set('of_name', o&&o.name); set('of_ident', o&&o.ident); set('of_desc', o&&o.desc);
      // 脚本/参数/返回结果 格式化为多行
      document.getElementById('of_script').value = o ? ('python ' + o.script) : '';
      document.getElementById('of_params').value = o ? o.params.split(' / ').join('\\n') : '';
      document.getElementById('of_returns').value = o ? o.returns.split(/ \\+ | \\/ /).join('\\n') : '';
      // 「保存为新版本」仅编辑时显示; 「同步创建工作流」仅新建时显示, 默认勾选
      document.getElementById('of_saveNewVer').style.display = o ? '' : 'none';
      document.getElementById('of_syncTaskWrap').style.display = o ? 'none' : '';
      document.getElementById('of_syncTask').checked = true;
      document.getElementById('opDetailDrawer').classList.remove('active');
      document.getElementById('opFormDrawer').classList.add('active');
    }}
    function openOpDetail(id){{
      var o=window.OPS[id]; if(!o) return;
      document.getElementById('opDetailTitle').textContent = o.name;
      var rows=[['标识',o.ident],['脚本',o.script],['创建人',o.creator],
                ['描述',o.desc],['请求参数',o.params],['返回结果',o.returns]];
      document.getElementById('opDetailBody').innerHTML =
        '<div class="desc-grid">'+rows.map(function(r){{ return '<div class="dk">'+r[0]+'</div><div class="dv">'+r[1]+'</div>'; }}).join('')+'</div>';
      document.getElementById('opDetailEdit').onclick=function(){{ openOpForm(id); }};
      document.getElementById('opDetailDrawer').classList.add('active');
    }}
    </script>
    """
    return render_page("算子管理", content, active="operators", breadcrumb="自动化任务 / <b>算子管理</b>")


@app.route("/pipelines")
def pipelines():
    flow_ident = request.args.get("ident", "").strip()
    keyword = request.args.get("q", "").strip()
    creator = request.args.get("creator", "").strip()
    business_stage = request.args.get("stage", "").strip()
    status_filter = request.args.get("status", "").strip()
    enabled_pipeline = next(
        pl for pl in PIPELINES if pl["name"] == "端到端切分标注流程"
    )
    draft_pipeline = {
        **enabled_pipeline,
        "name": "端到端切分标注流程（草稿）",
        "status": "草稿",
        "updated": "2026-08-04 11:30",
    }
    def pipeline_status(pl):
        status = pl.get("status", "草稿")
        return status if status in {"草稿", "启用", "停用"} else "草稿"

    pls = [
        pl
        for pl in (enabled_pipeline, draft_pipeline)
        if (
            not flow_ident
            or flow_ident.lower() in pl.get("ident", pl["id"]).lower()
        )
        and (
            not keyword
            or keyword.lower() in pl["name"].lower()
            or keyword.lower() in pl["desc"].lower()
        )
        and (
            not creator
            or creator.lower() in pl["creator"].lower()
        )
        and (
            not business_stage
            or pl.get("business_stage", "通用") == business_stage
        )
        and (
            not status_filter
            or pipeline_status(pl) == status_filter
        )
    ]
    rows = ""
    for pl in pls:
        flow_status = pipeline_status(pl)
        status_class = {
            "草稿": "qa-pend",
            "启用": "qa-pass",
            "停用": "qa-fail",
        }[flow_status]
        if flow_status == "启用":
            actions = (
                '<a href="#" onclick="toast(\'Demo: 流程已停用\');return false;">停用</a> '
                f'<a href="/pipelines/{pl["id"]}?mode=view">详情</a> '
                '<a href="#" onclick="toast(\'Demo: 已复制流程\');return false;">复制</a>'
            )
        else:
            actions = (
                '<a href="#" onclick="toast(\'Demo: 流程已启用\');return false;">启用</a> '
                f'<a href="/pipelines/{pl["id"]}?version=draft">编辑</a> '
                f'<a href="/pipelines/{pl["id"]}?mode=view&amp;version=draft">详情</a> '
                '<a href="#" onclick="toast(\'Demo: 已复制流程\');return false;">复制</a>'
            )
        rows += f"""<tr>
          <td><code>{html.escape(pl.get('ident', pl['id']))}</code></td>
          <td><b>{pl['name']}</b></td>
          <td><span class="tag tag-cyan">{pl.get('business_stage', '通用')}</span></td>
          <td class="muted pipeline-desc-cell" style="max-width:380px;"><span class="wf-desc-clamp" title="{html.escape(pl['desc'], quote=True)}">{pl['desc']}</span></td>
          <td>{pl['creator']}</td>
          <td><span class="qa {status_class}">{flow_status}</span></td>
          <td class="muted">{pl['updated']}</td>
          <td class="actions-cell">{actions}</td>
        </tr>"""
    if not rows:
        rows = '<tr><td colspan="8" class="muted" style="text-align:center;padding:24px;">无匹配工作流</td></tr>'
    ident_value = html.escape(flow_ident, quote=True)
    keyword_value = html.escape(keyword, quote=True)
    creator_value = html.escape(creator, quote=True)
    def pipeline_header_options(filter_name, current, options):
        option_rows = []
        for value, label in options:
            selected = " selected" if current == value else ""
            value_attr = html.escape(value, quote=True)
            option_rows.append(
                f'<button type="button" class="pipeline-th-filter-option{selected}" '
                f'data-filter-name="{filter_name}" data-filter-value="{value_attr}" '
                f'onclick="pipelineApplyHeaderFilter(this)">{html.escape(label)}</button>'
            )
        return "".join(option_rows)
    stage_header_options = pipeline_header_options(
        "stage",
        business_stage,
        [("", "全部"), ("质检", "质检"), ("标注", "标注"), ("验收", "验收")],
    )
    status_header_options = pipeline_header_options(
        "status",
        status_filter,
        [("", "全部"), ("启用", "启用"), ("草稿", "草稿"), ("停用", "停用")],
    )
    content = f"""
    <div class="dpr-intro dpr-intro-inline-action">
      <div>
        <div class="dpr-intro-title-row">
          <h1>流程管理</h1>
          <div class="dpr-intro-actions"><button type="button" class="btn-primary btn" onclick="openPipelineCreateDrawer()">新增流程</button></div>
        </div>
      </div>
    </div>
    <form id="pipelineFilterForm" class="q-filters rule-filter-panel" method="get" action="/pipelines">
      <div class="q-filter-row">
        <input type="hidden" name="stage" id="pipelineStageFilterValue" value="{html.escape(business_stage, quote=True)}">
        <input type="hidden" name="status" id="pipelineStatusFilterValue" value="{html.escape(status_filter, quote=True)}">
        <div class="q-field">
          <label for="pipelineFilterIdent">流程标识</label>
          <input id="pipelineFilterIdent" name="ident" value="{ident_value}" placeholder="请输入流程标识">
        </div>
        <div class="q-field">
          <label for="pipelineFilterName">流程名称</label>
          <input id="pipelineFilterName" name="q" value="{keyword_value}" placeholder="请输入流程名称">
        </div>
        <div class="q-field">
          <label for="pipelineFilterCreator">创建人</label>
          <input id="pipelineFilterCreator" name="creator" value="{creator_value}" placeholder="请输入创建人">
        </div>
        <div class="q-actions">
          <a class="btn" href="/pipelines">清空</a>
          <button class="btn btn-primary" type="submit">查询</button>
        </div>
      </div>
    </form>
    <div class="table-wrap">
      <table class="ant-table">
        <thead><tr>
          <th>流程标识</th><th>名称</th>
          <th><div class="pipeline-th-filter" data-filter-menu="stage">
            <button type="button" class="pipeline-th-filter-trigger" aria-expanded="false" onclick="pipelineToggleHeaderFilter(this)">业务环节<span class="pipeline-th-filter-chevron"></span></button>
            <div class="pipeline-th-filter-menu" role="listbox" aria-label="按业务环节筛选" title="全部业务环节">{stage_header_options}</div>
          </div></th>
          <th>描述</th><th>创建人</th>
          <th><div class="pipeline-th-filter" data-filter-menu="status">
            <button type="button" class="pipeline-th-filter-trigger" aria-expanded="false" onclick="pipelineToggleHeaderFilter(this)">状态<span class="pipeline-th-filter-chevron"></span></button>
            <div class="pipeline-th-filter-menu" role="listbox" aria-label="按状态筛选">{status_header_options}</div>
          </div></th>
          <th>更新时间</th><th>操作</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <div class="drawer-mask" id="pipelineCreateDrawer" onclick="if(event.target===this)closePipelineCreateDrawer()">
      <div class="drawer pipeline-create-drawer">
        <div class="drawer-head"><h3>新增流程</h3><button type="button" class="drawer-close" onclick="closePipelineCreateDrawer()">&times;</button></div>
        <div class="drawer-body">
          <div class="fg"><label><span class="req">*</span>流程标识</label><input id="pipelineCreateIdent" placeholder="请输入英文流程标识，如 e2e-split-annotation"></div>
          <div class="fg"><label><span class="req">*</span>流程名称</label><input id="pipelineCreateName" placeholder="请输入流程名称"></div>
          <div class="fg"><label><span class="req">*</span>业务环节</label><select id="pipelineCreateStage"><option value="质检">质检</option><option value="标注">标注</option><option value="验收">验收</option></select></div>
          <div class="fg"><label>描述</label><textarea id="pipelineCreateDesc" rows="4" placeholder="请输入流程描述"></textarea></div>
        </div>
        <div class="drawer-foot"><button type="button" class="btn" onclick="closePipelineCreateDrawer()">取消</button><button type="button" class="btn btn-primary" onclick="submitPipelineCreate()">创建并进入画布</button></div>
      </div>
    </div>
    <style>.pipeline-create-drawer{{width:560px;max-width:calc(100vw - 24px)}}.pipeline-create-drawer .fg{{margin-bottom:18px}}.pipeline-create-drawer .fg input,.pipeline-create-drawer .fg select{{height:38px;box-sizing:border-box}}.pipeline-desc-cell .wf-desc-clamp{{display:block;max-width:380px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.pipeline-th-filter{{position:relative;display:inline-flex;align-items:center}}.pipeline-th-filter-trigger{{display:inline-flex;align-items:center;gap:9px;padding:0;border:0;background:transparent;color:inherit;font:inherit;font-weight:600;cursor:pointer;white-space:nowrap}}.pipeline-th-filter-trigger:hover{{color:#1f80a0}}.pipeline-th-filter-chevron{{width:8px;height:8px;margin-top:-4px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg);transition:transform .15s}}.pipeline-th-filter.open .pipeline-th-filter-chevron{{margin-top:4px;transform:rotate(225deg)}}.pipeline-th-filter-menu{{display:none;position:absolute;top:calc(100% + 10px);left:-10px;z-index:30;min-width:160px;padding:6px 0;border:1px solid #e9edf1;border-radius:3px;background:#fff;box-shadow:0 8px 22px rgba(31,52,68,.14);font-weight:400}}.pipeline-th-filter.open .pipeline-th-filter-menu{{display:block}}.pipeline-th-filter-option{{display:block;width:100%;padding:11px 16px;border:0;background:#fff;color:#26343b;font-size:14px;line-height:1.4;text-align:left;cursor:pointer}}.pipeline-th-filter-option:hover{{background:#f2f7f9;color:#1f80a0}}.pipeline-th-filter-option.selected{{background:#2b87a4;color:#fff}}.pipeline-th-filter-option.selected:hover{{background:#247a95;color:#fff}}</style>
    <script>
    function openPipelineCreateDrawer(){{
      document.getElementById('pipelineCreateDrawer').classList.add('active');
      document.getElementById('pipelineCreateIdent').focus();
    }}
    function closePipelineCreateDrawer(){{ document.getElementById('pipelineCreateDrawer').classList.remove('active'); }}
    function submitPipelineCreate(){{
      var ident=document.getElementById('pipelineCreateIdent').value.trim();
      var name=document.getElementById('pipelineCreateName').value.trim();
      var stage=document.getElementById('pipelineCreateStage').value;
      var desc=document.getElementById('pipelineCreateDesc').value.trim();
      if(!ident){{toast('请输入流程标识');return;}}
      if(!/^[a-z][a-z0-9._-]*$/.test(ident)){{toast('流程标识需以小写字母开头，仅支持小写字母、数字、点、下划线和短横线');return;}}
      if(!name){{toast('请输入流程名称');return;}}
      location.href='/pipelines/new?flow_ident='+encodeURIComponent(ident)+'&flow_name='+encodeURIComponent(name)+'&business_stage='+encodeURIComponent(stage)+'&desc='+encodeURIComponent(desc);
    }}
    function pipelineToggleHeaderFilter(trigger){{
      var wrap=trigger.closest('.pipeline-th-filter');
      var wasOpen=wrap.classList.contains('open');
      document.querySelectorAll('.pipeline-th-filter.open').forEach(function(item){{
        item.classList.remove('open');
        var button=item.querySelector('.pipeline-th-filter-trigger');
        if(button) button.setAttribute('aria-expanded','false');
      }});
      if(!wasOpen){{
        wrap.classList.add('open');
        trigger.setAttribute('aria-expanded','true');
      }}
    }}
    function pipelineApplyHeaderFilter(option){{
      var form=document.getElementById('pipelineFilterForm');
      var name=option.dataset.filterName;
      var input=document.getElementById(name==='stage'?'pipelineStageFilterValue':'pipelineStatusFilterValue');
      if(input) input.value=option.dataset.filterValue||'';
      if(form) form.submit();
    }}
    document.addEventListener('click',function(event){{
      if(!event.target.closest('.pipeline-th-filter')){{
        document.querySelectorAll('.pipeline-th-filter.open').forEach(function(item){{
          item.classList.remove('open');
          var button=item.querySelector('.pipeline-th-filter-trigger');
          if(button) button.setAttribute('aria-expanded','false');
        }});
      }}
    }});
    </script>
    """
    return render_page("工作流管理", content, active="pipelines", breadcrumb="自动化任务 / <b>工作流管理</b>")


WF_CANVAS_JS = r"""
(function(){
  var NODES = __NODES__, EDGES = __EDGES__, FRAMES = __FRAMES__;
  var seq = NODES.length;
  var W = 240, NODE_H = 104, DEF_H = NODE_H, CONDITION_H = 180, TERM_W = 76, TERM_H = 40;
  var canvas = document.getElementById('wfCanvas');
  var pan = document.getElementById('wfPan');
  var framesLayer = document.getElementById('wfFrames');
  var nodesLayer = document.getElementById('wfNodes');
  var edgesSvg = document.getElementById('wfEdges');
  var emptyEl = document.getElementById('wfEmpty');
  var selectionBoxEl = document.getElementById('wfSelectionBox');
  var viewOnly = !!canvas.closest('.wf-stage.view-only');
  var z = 1, panX = 0, panY = 0;
  var selId = null, selectedIds = [], drag = null, conn = null, panning = null, selectionMarquee = null;

  function wfPadTime(value){ return value<10?'0'+value:String(value); }
  function wfFormatSaveTime(date){
    return date.getFullYear()+'-'+wfPadTime(date.getMonth()+1)+'-'+wfPadTime(date.getDate())+' '+
      wfPadTime(date.getHours())+':'+wfPadTime(date.getMinutes());
  }
  window.wfSaveDraft=function(showToast){
    if(viewOnly) return;
    var saved=document.getElementById('wfLastSaved');
    if(saved) saved.textContent='保存时间：'+wfFormatSaveTime(new Date());
    if(showToast) toast('已保存');
  };
  if(!viewOnly) setInterval(function(){ window.wfSaveDraft(false); },300000);

  function byId(id){ for(var i=0;i<NODES.length;i++) if(NODES[i].id===id) return NODES[i]; return null; }
  function isNodeSelected(id){ return selectedIds.indexOf(id)>=0; }
  function selectedNodeIds(){
    var ids=selectedIds.filter(function(id){ return !!byId(id); });
    if(!ids.length&&selId&&byId(selId)) ids=[selId];
    return ids;
  }
  function setSelectedNodes(ids){
    selectedIds=ids.filter(function(id,index){
      var node=byId(id);
      return node&&node.kind!=='flow-input'&&node.kind!=='flow-output'&&ids.indexOf(id)===index;
    });
    selId=selectedIds.length===1?selectedIds[0]:null;
  }
  function frameById(id){ for(var i=0;i<FRAMES.length;i++) if(FRAMES[i].id===id) return FRAMES[i]; return null; }
  function frameTerminalById(id){
    for(var i=0;i<FRAMES.length;i++){
      var frame=FRAMES[i], inputId=frame.inputId||frame.id+'-input', outputId=frame.outputId||frame.id+'-output';
      if(id===inputId) return {id:id,kind:'phase-input',phaseId:frame.id,x:frame.x+24,y:frame.y+(frame.h-TERM_H)/2};
      if(id===outputId) return {id:id,kind:'phase-output',phaseId:frame.id,x:frame.x+frame.w-24-TERM_W,y:frame.y+(frame.h-TERM_H)/2};
    }
    return null;
  }
  function entityById(id){ return byId(id)||frameTerminalById(id); }
  function applyPan(){ pan.style.transform = 'translate('+panX+'px,'+panY+'px) scale('+z+')'; }
  function toLocal(cx, cy){ var r=canvas.getBoundingClientRect(); return { x:(cx-r.left-panX)/z, y:(cy-r.top-panY)/z }; }
  function nodeH(n){ var el=nodesLayer.querySelector('.wf-node[data-id="'+n.id+'"]'); return (el&&el.offsetHeight)||DEF_H; }
  function nodeRectOverlaps(x,y,w,h,other,margin){
    var oh=nodeH(other);
    return x < other.x+w+margin && x+w+margin > other.x &&
      y < other.y+oh+margin && y+h+margin > other.y;
  }
  function pickNodePosition(h){
    var r=canvas.getBoundingClientRect();
    var center=toLocal(r.left+r.width/2,r.top+r.height/2);
    var startX=center.x-W/2, startY=center.y-h/2;
    var visibleTopLeft=toLocal(r.left+28,r.top+28);
    var visibleBottomRight=toLocal(r.right-28,r.bottom-72);
    var minVisibleX=Math.max(32,visibleTopLeft.x);
    var maxVisibleX=Math.min(4000-W-32,visibleBottomRight.x-W);
    var minVisibleY=Math.max(32,visibleTopLeft.y);
    var maxVisibleY=Math.min(3000-h-32,visibleBottomRight.y-h);
    var candidates=[];
    for(var ring=0;ring<=6;ring++){
      for(var row=-ring;row<=ring;row++){
        for(var col=-ring;col<=ring;col++){
          if(Math.max(Math.abs(row),Math.abs(col))!==ring) continue;
          candidates.push({x:startX+col*280,y:startY+row*150});
        }
      }
    }
    for(var i=0;i<candidates.length;i++){
      var x=Math.max(minVisibleX,Math.min(maxVisibleX,candidates[i].x));
      var y=Math.max(minVisibleY,Math.min(maxVisibleY,candidates[i].y));
      var blocked=false;
      for(var j=0;j<NODES.length;j++){
        if(nodeRectOverlaps(x,y,W,h,NODES[j],22)){ blocked=true; break; }
      }
      if(!blocked) return {x:x,y:y};
    }
    return {x:Math.max(minVisibleX,Math.min(maxVisibleX,startX)),y:Math.max(minVisibleY,Math.min(maxVisibleY,startY))};
  }
  function updateSelectionMarquee(clientX,clientY){
    if(!selectionMarquee||!selectionBoxEl) return;
    var r=canvas.getBoundingClientRect();
    var x=Math.max(0,Math.min(r.width,clientX-r.left));
    var y=Math.max(0,Math.min(r.height,clientY-r.top));
    selectionMarquee.ex=x; selectionMarquee.ey=y;
    selectionBoxEl.style.left=Math.min(selectionMarquee.sx,x)+'px';
    selectionBoxEl.style.top=Math.min(selectionMarquee.sy,y)+'px';
    selectionBoxEl.style.width=Math.abs(x-selectionMarquee.sx)+'px';
    selectionBoxEl.style.height=Math.abs(y-selectionMarquee.sy)+'px';
    selectionBoxEl.classList.add('active');
  }
  function finishSelectionMarquee(){
    if(!selectionMarquee) return;
    var r=canvas.getBoundingClientRect();
    var left=r.left+Math.min(selectionMarquee.sx,selectionMarquee.ex);
    var right=r.left+Math.max(selectionMarquee.sx,selectionMarquee.ex);
    var top=r.top+Math.min(selectionMarquee.sy,selectionMarquee.ey);
    var bottom=r.top+Math.max(selectionMarquee.sy,selectionMarquee.ey);
    var ids=[];
    NODES.forEach(function(node){
      if(node.kind==='flow-input'||node.kind==='flow-output') return;
      var el=nodesLayer.querySelector('.wf-node[data-id="'+node.id+'"]');
      if(!el) return;
      var nr=el.getBoundingClientRect();
      if(nr.right>=left&&nr.left<=right&&nr.bottom>=top&&nr.top<=bottom) ids.push(node.id);
    });
    setSelectedNodes(ids);
    selectionMarquee=null;
    selectionBoxEl.classList.remove('active');
    document.getElementById('wfConfig').classList.remove('open','human-mode');
    renderNodes();
  }
  function ports(n){
    if(n.kind==='phase-input'||n.kind==='phase-output'){
      return {
        inp:{x:n.x, y:n.y+TERM_H/2},
        out:{x:n.x+TERM_W, y:n.y+TERM_H/2}
      };
    }
    if(n.kind==='flow-input'||n.kind==='flow-output'){
      var terminalPorts={
        inp:{x:n.x, y:n.y+NODE_H/2},
        out:{x:n.x+W, y:n.y+NODE_H/2}
      };
      return terminalPorts;
    }
    var h=nodeH(n);
    if(n.kind==='condition'){
      var conditionPorts={
        inp:{x:n.x, y:n.y+76},
        out:{x:n.x+W, y:n.y+76},
        branch:{x:n.x+W, y:n.y+h}
      };
      var branchCount=(n.branches&&n.branches.length?n.branches.length:1);
      for(var branchIndex=0;branchIndex<branchCount;branchIndex++){
        conditionPorts['branch-'+branchIndex]={x:n.x+W,y:n.y+57+19+branchIndex*38};
      }
      conditionPorts.branch={x:n.x+W,y:n.y+57+19+branchCount*38};
      return conditionPorts;
    }
    return {
      inp:{x:n.x, y:n.y+NODE_H/2},
      out:{x:n.x+W, y:n.y+h/2},
      branch:{x:n.x+W/2, y:n.y+h}
    };
  }
  function orthogonalPath(s,t){
    if(Math.abs(t.y-s.y)<2 && t.x>=s.x) return 'M'+s.x+' '+s.y+' H'+t.x;
    if(t.x>=s.x+56){
      var middle=(s.x+t.x)/2;
      return 'M'+s.x+' '+s.y+' H'+middle+' V'+t.y+' H'+t.x;
    }
    var lane=Math.min(s.y,t.y)-52;
    return 'M'+s.x+' '+s.y+' H'+(s.x+34)+' V'+lane+' H'+(t.x-34)+' V'+t.y+' H'+t.x;
  }
  function branchPath(s,t,source,target,fromPort){
    if(Math.abs(t.y-s.y)<2 && t.x>=s.x) return 'M'+s.x+' '+s.y+' H'+t.x;
    var branchIndex=fromPort==='branch'?((source.branches&&source.branches.length)||1):parseInt(String(fromPort||'branch-0').replace('branch-',''),10)||0;
    if(target&&target.kind==='flow-output' && t.x>s.x){
      var lane=source.y+nodeH(source)+28+branchIndex*30;
      var leave=s.x+24+branchIndex*12;
      var approach=t.x-24-branchIndex*12;
      return 'M'+s.x+' '+s.y+' H'+leave+' V'+lane+' H'+approach+' V'+t.y+' H'+t.x;
    }
    var middle=t.x>=s.x?(s.x+t.x)/2:s.x+42;
    return 'M'+s.x+' '+s.y+' H'+middle+' V'+t.y+' H'+t.x;
  }
  function bezier(s,t){ return orthogonalPath(s,t); }
  function branchBezier(s,t,source,target,fromPort){ return branchPath(s,t,source,target,fromPort); }

  function renderFrames(){
    if(!framesLayer) return;
    framesLayer.innerHTML=FRAMES.map(function(frame,index){
      var inputId=frame.inputId||frame.id+'-input', outputId=frame.outputId||frame.id+'-output';
      return '<div class="wf-phase-frame" data-phase-id="'+frame.id+'" style="left:'+frame.x+'px;top:'+frame.y+'px;width:'+frame.w+'px;height:'+frame.h+'px;">'+
        (index?'<div class="wf-phase-port in"></div>':'')+
        (index<FRAMES.length-1?'<div class="wf-phase-port out"></div>':'')+
        '<div class="wf-phase-label"><i>'+(index+1)+'</i><b>'+frame.name+'</b><small>'+frame.desc+'</small></div>'+
        '<div class="wf-phase-terminal input" data-terminal-id="'+inputId+'"><span>输入</span><div class="wf-port out" data-port="out" data-id="'+inputId+'"></div></div>'+
        '<div class="wf-phase-terminal output" data-terminal-id="'+outputId+'"><div class="wf-port in" data-port="in" data-id="'+outputId+'"></div><span>输出</span></div>'+
      '</div>';
    }).join('');
  }

  function renderEdges(extra){
    var p='';
    for(var frameIndex=0;frameIndex<FRAMES.length-1;frameIndex++){
      var sourceFrame=FRAMES[frameIndex], targetFrame=FRAMES[frameIndex+1];
      var sourceX=sourceFrame.x+sourceFrame.w/2, sourceY=sourceFrame.y+sourceFrame.h;
      var targetX=targetFrame.x+targetFrame.w/2, targetY=targetFrame.y;
      p+='<path class="phase-edge" d="M'+sourceX+' '+sourceY+' L'+targetX+' '+targetY+'" fill="none" marker-end="url(#wfPhaseArrow)" pointer-events="none"/>';
    }
    for(var i=0;i<EDGES.length;i++){
      var a=entityById(EDGES[i].from), b=entityById(EDGES[i].to); if(!a||!b) continue;
      var fromPort=EDGES[i].fromPort||'out', toPort=EDGES[i].toPort||'inp';
      var sourcePorts=ports(a), targetPorts=ports(b);
      var s=sourcePorts[fromPort]||sourcePorts.out, t=targetPorts[toPort]||targetPorts.inp;
      var path=fromPort.indexOf('branch')===0?branchBezier(s,t,a,b,fromPort):bezier(s,t);
      var edgeClass='edge'+(EDGES[i].branch==='no'?' no-branch':'');
      p+='<path class="'+edgeClass+'" data-i="'+i+'" d="'+path+'" fill="none" stroke="#9ec3d6" stroke-width="2" marker-end="url(#wfArrow)"/>';
    }
    if(extra) p+=extra;
    edgesSvg.innerHTML='<defs>'+
      '<marker id="wfArrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#9ec3d6"/></marker>'+
      '<marker id="wfPhaseArrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#5f9fac"/></marker>'+
      '</defs>'+p;
  }
  function nodeIcon(kind){
    var icons={
      'flow-input':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 6.5 17 12l-9 5.5z" fill="currentColor" stroke="none"/></svg>',
      'flow-output':'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="6.5" width="11" height="11" rx="1.5" fill="currentColor" stroke="none"/></svg>',
      automatic:'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3.2"/><path d="M12 3.5v2M12 18.5v2M3.5 12h2M18.5 12h2M6 6l1.5 1.5M16.5 16.5 18 18M18 6l-1.5 1.5M7.5 16.5 6 18"/></svg>',
      human:'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.2"/><path d="M5.5 19c.8-4 3-6 6.5-6s5.7 2 6.5 6"/></svg>',
      acceptance:'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.2"/><path d="M5.5 19c.8-4 3-6 6.5-6s5.7 2 6.5 6"/></svg>',
      condition:'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="7" cy="5" r="2"/><circle cx="17" cy="12" r="2"/><circle cx="17" cy="19" r="2"/><path d="M7 7v7a5 5 0 0 0 5 5h3M7 10a5 5 0 0 0 5 2h3"/></svg>'
    };
    return icons[kind]||icons.automatic;
  }
  function renderNodes(){
    var h='';
    for(var i=0;i<NODES.length;i++){
      var n=NODES[i];
      var kind=n.kind||'operator';
      if(kind==='flow-input'||kind==='flow-output'){
        h+='<div class="wf-node flow-terminal '+kind+'" data-id="'+n.id+
          '" data-node-kind="'+kind+'" style="left:'+n.x+'px;top:'+n.y+'px;">'+
          (kind==='flow-output'?'<div class="wf-port in" data-port="in" data-id="'+n.id+'"></div>':'')+
          '<div class="wf-node-head"><span class="wf-node-ic">'+nodeIcon(kind)+'</span>'+n.name+'</div>'+
          '<div class="wf-node-subtitle">'+(kind==='flow-input'?'Start':'End')+'</div>'+
          (kind==='flow-input'?'<div class="wf-port out" data-port="out" data-id="'+n.id+'"></div>':'')+
        '</div>';
        continue;
      }
      if(kind==='condition'){
        var branches=(n.branches&&n.branches.length?n.branches:[{name:'CASE 1',rules:[]}]);
        branches=[branches[0]];
        var branchRows=branches.map(function(branch,index){
          return '<div class="wf-condition-branch"><span>'+esc(branch.name||'CASE 1')+'</span><b>IF</b><span class="wf-port wf-branch-port" data-port="branch-0" data-id="'+n.id+'"></span></div>';
        }).join('')+'<div class="wf-condition-branch"><span>其他</span><b>ELSE</b><span class="wf-port wf-branch-port" data-port="branch" data-id="'+n.id+'"></span></div>';
        h+='<div class="wf-node condition'+(isNodeSelected(n.id)?' sel':'')+'" data-id="'+n.id+'" data-node-kind="condition" style="left:'+n.x+'px;top:'+n.y+'px;">'+
          '<div class="wf-port in" data-port="in" data-id="'+n.id+'"></div>'+
          '<span class="wf-node-del" data-del="'+n.id+'" title="删除">&times;</span>'+
          '<div class="wf-condition-head"><i>'+nodeIcon('condition')+'</i><strong>'+n.name+'</strong></div>'+
          '<div class="wf-condition-branch-list">'+branchRows+'</div>'+
        '</div>';
        continue;
      }
      h+='<div class="wf-node '+kind+(isNodeSelected(n.id)?' sel':'')+'" data-id="'+n.id+'" data-node-kind="'+kind+'" style="left:'+n.x+'px;top:'+n.y+'px;">'+
        '<div class="wf-port in" data-port="in" data-id="'+n.id+'"></div>'+
        '<div class="wf-port out" data-port="out" data-id="'+n.id+'"></div>'+
        '<div class="wf-node-head"><span class="wf-node-ic">'+nodeIcon(kind)+'</span>'+n.name+
          (n.phase?'<span class="wf-node-phase">'+n.phase+'</span>':'')+
          '<span class="wf-node-del" data-del="'+n.id+'" title="删除">&times;</span></div>'+
        '<div class="wf-node-subtitle">'+esc(n.desc||n.ident||kind)+'</div>'+
      '</div>';
    }
    nodesLayer.innerHTML=h;
    if(emptyEl) emptyEl.style.display = NODES.length ? 'none' : '';
    renderEdges();
  }

  canvas.addEventListener('contextmenu', function(e){ e.preventDefault(); });
  canvas.addEventListener('click', function(e){
    var action=e.target.closest('#wfNodeContextMenu button');
    if(!action) return;
    var actionType=action.getAttribute('data-action');
    e.preventDefault(); e.stopPropagation();
    var menu=document.getElementById('wfNodeContextMenu');
    if(menu&&menu.getAttribute('data-node-id')) setSelectedNodes([menu.getAttribute('data-node-id')]);
    if(actionType==='copy') wfAddTypedNode('copy');
    if(actionType==='delete') wfDeleteSel();
  });
  canvas.addEventListener('mousedown', function(e){
    if(e.target.closest('#wfNodeContextMenu')||e.target.closest('#addTaskDrawer')||e.target.closest('.wf-toolbar')) return;
    canvas.focus({preventScroll:true});
    if(e.button===2){
      e.preventDefault();
      var rightNodeEl=e.target.closest('.wf-node');
      var rightNode=rightNodeEl&&byId(rightNodeEl.getAttribute('data-id'));
      if(rightNode) wfOpenNodeContextMenu(rightNode,e); else wfHideNodeContextMenu();
      return;
    }
    wfHideNodeContextMenu();
    if(viewOnly){
      var viewNodeEl=e.target.closest('.wf-node');
      if(viewNodeEl){
        var viewNode=byId(viewNodeEl.getAttribute('data-id'));
        if(viewNode&&viewNode.kind!=='flow-input'&&viewNode.kind!=='flow-output'){
          setSelectedNodes([viewNode.id]); openConfig(viewNode); renderNodes();
        }
        e.preventDefault();
        return;
      }
      panning={sx:e.clientX, sy:e.clientY, ox:panX, oy:panY};
      return;
    }
    var del=e.target.getAttribute('data-del');
    if(del){ setSelectedNodes([del]); wfDeleteSel(); return; }
    var port=e.target.closest('.wf-port');
    if(port){ conn={from:port.getAttribute('data-id'), side:port.getAttribute('data-port')}; e.preventDefault(); return; }
    var ep=e.target.closest('path.edge');
    if(ep){ var idx=+ep.getAttribute('data-i'); EDGES.splice(idx,1); renderNodes(); return; }
    var nodeEl=e.target.closest('.wf-node');
    if(e.shiftKey&&!nodeEl){
      var canvasRect=canvas.getBoundingClientRect();
      selectionMarquee={sx:e.clientX-canvasRect.left,sy:e.clientY-canvasRect.top,ex:e.clientX-canvasRect.left,ey:e.clientY-canvasRect.top};
      updateSelectionMarquee(e.clientX,e.clientY);
      e.preventDefault(); return;
    }
    if(nodeEl){
      var n=byId(nodeEl.getAttribute('data-id'));
      if(n.kind==='flow-input'||n.kind==='flow-output'){
        drag={id:n.id,ids:[n.id],starts:[{id:n.id,x:n.x,y:n.y}],sx:e.clientX,sy:e.clientY,moved:false,terminal:true};
      }else{
        var dragIds=isNodeSelected(n.id)?selectedNodeIds():[n.id];
        if(!e.shiftKey&&!isNodeSelected(n.id)){ setSelectedNodes([n.id]); renderNodes(); }
        drag={id:n.id,ids:dragIds,starts:dragIds.map(function(id){var item=byId(id);return {id:id,x:item.x,y:item.y};}),sx:e.clientX,sy:e.clientY,moved:false,toggleOnly:e.shiftKey};
      }
      e.preventDefault(); return;
    }
    setSelectedNodes([]);
    document.getElementById('wfConfig').classList.remove('open','human-mode');
    renderNodes();
    panning={sx:e.clientX, sy:e.clientY, ox:panX, oy:panY};
  });
  document.addEventListener('mousemove', function(e){
    if(drag){
      var dx=(e.clientX-drag.sx)/z, dy=(e.clientY-drag.sy)/z;
      if(Math.abs(e.clientX-drag.sx)+Math.abs(e.clientY-drag.sy)>3) drag.moved=true;
      drag.starts.forEach(function(start){
        var n=byId(start.id); if(!n) return;
        n.x=start.x+dx; n.y=start.y+dy;
        var el=nodesLayer.querySelector('.wf-node[data-id="'+start.id+'"]');
        if(el){ el.style.left=n.x+'px'; el.style.top=n.y+'px'; }
      });
      renderEdges();
    } else if(selectionMarquee){
      updateSelectionMarquee(e.clientX,e.clientY);
    } else if(conn){
      var a=entityById(conn.from); if(!a) return;
      var s=ports(a)[conn.side]||ports(a).out;
      var m=toLocal(e.clientX,e.clientY);
      var previewPath=conn.side.indexOf('branch')===0?branchBezier(s,m,a,null,conn.side):bezier(s,m);
      renderEdges('<path d="'+previewPath+'" fill="none" stroke="#1F80A0" stroke-width="2" stroke-dasharray="5 4"/>');
    } else if(panning){
      panX=panning.ox+(e.clientX-panning.sx); panY=panning.oy+(e.clientY-panning.sy); applyPan();
    }
  });
  document.addEventListener('mouseup', function(e){
    if(selectionMarquee){ finishSelectionMarquee(); return; }
    if(conn){
      var port=e.target.closest('.wf-port');
      var portSide=port&&port.getAttribute('data-port');
      var sourceSide=conn.side==='out'||conn.side.indexOf('branch')===0;
      var validPair=port&&(
        (sourceSide&&portSide==='in')||
        (!sourceSide&&(portSide==='out'||portSide==='branch'))
      );
      if(validPair){
        var other=port.getAttribute('data-id');
        var f=sourceSide?conn.from:other, t=sourceSide?other:conn.from;
        var fromPort=sourceSide?conn.side:portSide;
        var toPort=sourceSide?portSide:'inp';
        if(f!==t && !EDGES.some(function(x){return x.from===f&&x.to===t&&((x.fromPort||'out')===fromPort);})) EDGES.push({from:f,to:t,fromPort:fromPort,toPort:toPort});
      }
      conn=null; renderNodes(); return;
    }
    if(drag){
      if(!drag.moved&&!drag.terminal){
        var selectedNode=byId(drag.id);
        if(drag.toggleOnly){
          var nextIds=selectedNodeIds().slice();
          var selectedIndex=nextIds.indexOf(drag.id);
          if(selectedIndex>=0) nextIds.splice(selectedIndex,1); else nextIds.push(drag.id);
          setSelectedNodes(nextIds);
          document.getElementById('wfConfig').classList.remove('open','human-mode');
          renderNodes();
        }else{
          setSelectedNodes([drag.id]);
          openConfig(selectedNode); renderNodes();
        }
      }
      drag=null; return;
    }
    panning=null;
  });

  var CONDITION_VALUES={
    '所属项目':['预训练采集','宁德项目','demo 项目'],
    '供应商':['供应商 A','供应商 B'],
    '质检结论':['合格','不合格','操作失误'],
    '标注状态':['未标注','已标注'],
    '采集结论':['成功','失败'],
    '上传状态':['未上传','上传中','上传成功','上传失败'],
    '数据来源':['采集','导入']
  };
  var CONDITION_OPERATORS=['等于','不等于','属于','不属于'];
  var USER_GROUPS=[
    '标注员用户组','标注抽验员用户组','新规实验标注员用户组',
    '质检复核用户组','内部验收用户组'
  ];
  var HUMAN_ACTIONS=['驳回'];
  function esc(v){ return String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); }
  function optionList(items,selected){
    return items.map(function(item){ return '<option'+(item===selected?' selected':'')+'>'+esc(item)+'</option>'; }).join('');
  }
  function isHumanNode(n){ return n&&(n.kind==='human'||n.kind==='acceptance'); }
  function isConditionNode(n){ return n&&n.kind==='condition'; }
  function isAutomaticNode(n){ return n&&(n.kind==='automatic'||n.kind==='operator'||!n.kind); }
  function renderAutomaticOperatorOptions(selectedId){
    var select=document.getElementById('wfaOperator');
    var operatorIds=Object.keys(OPS);
    select.innerHTML=operatorIds.length?operatorIds.map(function(operatorId){
      return '<option value="'+esc(operatorId)+'">'+esc(OPS[operatorId].name)+'</option>';
    }).join(''):'<option value="">暂无可用算子</option>';
    select.disabled=!operatorIds.length;
    var resolved=OPS[selectedId]?selectedId:(operatorIds[0]||'');
    select.value=resolved;
    return resolved;
  }
  function defaultWorkbench(n){
    if((n.businessStage||'').indexOf('验收')>=0) return '详情工作台 v1.0';
    if((n.businessStage||'').indexOf('标注')>=0) return '标注工作台 v4.1';
    return '质检工作台 v2.0';
  }
  function workflowFrameIndex(phaseId){
    for(var i=0;i<FRAMES.length;i++) if(FRAMES[i].id===phaseId) return i;
    return FRAMES.length;
  }
  function previousHumanNodes(n){
    if(!n) return [];
    var reverse={};
    function addReverseEdge(from,to){
      if(!from||!to) return;
      if(!reverse[to]) reverse[to]=[];
      reverse[to].push(from);
    }
    EDGES.forEach(function(edge){ addReverseEdge(edge.from,edge.to); });
    for(var i=0;i<FRAMES.length-1;i++){
      var source=FRAMES[i], target=FRAMES[i+1];
      addReverseEdge(
        source.outputId||source.id+'-output',
        target.inputId||target.id+'-input'
      );
    }
    var seen={}, stack=[n.id];
    while(stack.length){
      var current=stack.pop();
      (reverse[current]||[]).forEach(function(parent){
        if(seen[parent]) return;
        seen[parent]=true;
        stack.push(parent);
      });
    }
    return NODES.filter(function(node){
      return node.id!==n.id&&isHumanNode(node)&&!!seen[node.id];
    }).sort(function(a,b){ return (a.x-b.x)||(a.y-b.y); });
  }
  function renderRejectTargets(n,selectedIds){
    var candidates=previousHumanNodes(n);
    var selected=(selectedIds||[]).filter(function(id){
      return candidates.some(function(item){return item.id===id;});
    });
    var panel=document.getElementById('wfhRejectPanel');
    panel.innerHTML=candidates.length?'<div class="ms-trigger" data-base="请选择驳回节点" onclick="this.closest(\'.ms-wrap\').classList.toggle(\'open\')"><span class="ms-label">请选择驳回节点</span></div><div class="ms-panel">'+candidates.map(function(item){
      return '<label><input type="checkbox" value="'+esc(item.id)+'"'+
        (selected.indexOf(item.id)>=0?' checked':'')+
        ' onchange="wfRejectTargetsUpdate(this)"><span>'+esc(item.name)+'</span></label>';
    }).join('')+'</div>':'<div class="wf-reject-empty">当前节点没有前序人工节点</div>';
    wfRejectTargetsUpdate(panel.querySelector('input'));
    return candidates;
  }
  function renderConditionRows(items){
    var rows=items||[];
    document.getElementById('wfhConditionRows').innerHTML=rows.map(function(item){
      var fields=Object.keys(CONDITION_VALUES);
      var field=CONDITION_VALUES[item.field]?item.field:'质检结论';
      var value=(CONDITION_VALUES[field].indexOf(item.value)>=0)?item.value:CONDITION_VALUES[field][0];
      return '<div class="wf-condition-row">'+
        '<select class="wf-edit-field wf-cond-field" onchange="wfConditionFieldChange(this)">'+optionList(fields,field)+'</select>'+
        '<select class="wf-edit-field wf-cond-value">'+optionList(CONDITION_VALUES[field],value)+'</select>'+
        '<button type="button" class="wf-row-del" onclick="wfRemoveCondition(this)" title="删除">&times;</button>'+
      '</div>';
    }).join('');
    document.getElementById('wfhConditionEmpty').style.display=rows.length?'none':'block';
  }
  function renderRatioRules(items){
    var rows=items||[];
    document.getElementById('wfhRatioRuleRows').innerHTML=rows.map(function(item){
      var fields=Object.keys(CONDITION_VALUES);
      var field=CONDITION_VALUES[item.field]?item.field:'质检结论';
      var value=(CONDITION_VALUES[field].indexOf(item.value)>=0)?item.value:CONDITION_VALUES[field][0];
      return '<div class="wf-ratio-rule">'+
        '<select class="wf-edit-field wf-ratio-field" onchange="wfRatioFieldChange(this)">'+optionList(fields,field)+'</select>'+
        '<select class="wf-edit-field wf-ratio-value">'+optionList(CONDITION_VALUES[field],value)+'</select>'+
        '<div style="position:relative;"><input class="wf-edit-field wf-ratio-percent" type="number" min="1" max="100" value="'+(item.percent==null?100:item.percent)+'" style="padding-right:21px;"><span style="position:absolute;right:8px;top:7px;color:#999;font-size:12px;">%</span></div>'+
        '<button type="button" class="wf-row-del" onclick="wfRemoveRatioRule(this)" title="删除">&times;</button>'+
      '</div>';
    }).join('');
    document.getElementById('wfhRatioRuleEmpty').style.display=rows.length?'none':'block';
  }
  function normalizedBranches(n){
    if(n.branches&&n.branches.length) return [Object.assign({logic:'or'},n.branches[0])];
    var legacyRules=(n.ratioRules&&n.ratioRules.length?n.ratioRules:(n.entryConditions||[]).map(function(item){
      return {field:item.field,operator:item.operator||'等于',value:item.value,percent:n.entryRatio==null?100:n.entryRatio};
    }));
    return [{name:'CASE 1',logic:'or',rules:legacyRules.length?legacyRules:[{field:'供应商',operator:'等于',value:'供应商 A',percent:50}]}];
  }
  function branchRuleHtml(item,index){
    var fields=Object.keys(CONDITION_VALUES);
    var field=CONDITION_VALUES[item.field]?item.field:'供应商';
    var operator=CONDITION_OPERATORS.indexOf(item.operator)>=0?item.operator:'等于';
    var value=(CONDITION_VALUES[field].indexOf(item.value)>=0)?item.value:CONDITION_VALUES[field][0];
    return (index?'<div class="wf-branch-logic"><span>或</span></div>':'')+'<div class="wf-branch-rule">'+
      '<select class="wf-edit-field wf-branch-field" onchange="wfBranchFieldChange(this)">'+optionList(fields,field)+'</select>'+
      '<select class="wf-edit-field wf-branch-operator">'+optionList(CONDITION_OPERATORS,operator)+'</select>'+
      '<select class="wf-edit-field wf-branch-value">'+optionList(CONDITION_VALUES[field],value)+'</select>'+
      '<div style="position:relative"><input class="wf-edit-field wf-branch-percent" type="number" min="1" max="100" value="'+(item.percent==null?100:item.percent)+'" style="padding-right:19px"><span style="position:absolute;right:7px;top:7px;color:#999;font-size:11px">%</span></div>'+
      '<button type="button" class="wf-row-del" onclick="wfRemoveBranchRule(this)" title="删除">&times;</button></div>';
  }
  function renderConditionBranches(branches){
    var items=branches&&branches.length?[branches[0]]:[{name:'CASE 1',rules:[]}];
    document.getElementById('wfConditionBranches').innerHTML=items.map(function(branch,index){
      var rules=branch.rules&&branch.rules.length?branch.rules:[{field:'供应商',operator:'等于',value:'供应商 A',percent:50}];
      return '<section class="wf-branch-editor" data-branch-index="'+index+'">'+
        '<div class="wf-branch-editor-head"><b>IF</b><input class="wf-edit-field wf-branch-name" value="'+esc(branch.name||'CASE 1')+'"></div>'+
        '<div class="wf-branch-rules"><div class="wf-branch-rule-head"><span>筛选项</span><span>操作符</span><span>值</span><span>比例</span><span></span></div>'+rules.map(branchRuleHtml).join('')+'</div>'+
        '<button type="button" class="wf-add-link wf-branch-add-condition" onclick="wfAddBranchRule(this)">&plus; 添加条件与比例</button></section>';
    }).join('');
  }
  function renderHumanChoices(holderId,items,selected,onchange,disabledItems){
    var selectedItems=selected||[];
    var disabled=disabledItems||[];
    var isUserGroup=holderId==='wfhUserGroups';
    document.getElementById(holderId).innerHTML=items.map(function(item){
      var isReject=holderId==='wfhAllowedActions'&&item==='驳回';
      var itemOnchange=isReject?'wfToggleReject(this.checked)':onchange;
      var checked=isUserGroup?selectedItems[0]===item:selectedItems.indexOf(item)>=0;
      return '<label><input type="'+(isUserGroup?'radio':'checkbox')+'"'+
        (isUserGroup?' name="wfhUserGroup"':'')+' value="'+esc(item)+'"'+
        (isReject?' id="wfhRejectEnabled"':'')+
        (checked?' checked':'')+
        (disabled.indexOf(item)>=0?' disabled':'')+
        (itemOnchange?' onchange="'+itemOnchange+'"':'')+'><span>'+esc(item)+'</span></label>';
    }).join('');
  }
  function wfHumanAssigneeMode(){
    var checked=document.querySelector('input[name="wfhAssigneeMode"]:checked');
    return checked?checked.value:'task_custom';
  }
  function wfRefreshAssigneeInheritance(){
    var n=byId(selId);
    var mode=wfHumanAssigneeMode();
    var previous=previousHumanNodes(n);
    var wrap=document.getElementById('wfhAssigneeInheritWrap');
    var select=document.getElementById('wfhAssigneeInheritNode');
    var hint=document.getElementById('wfhAssigneeInheritHint');
    if(!wrap||!select||!hint) return;
    wrap.style.display=mode==='inherit'?'block':'none';
    select.innerHTML=previous.length?previous.map(function(item){ return '<option value="'+esc(item.id)+'">'+esc(item.name||item.id)+'</option>'; }).join(''):'<option value="">暂无前序人工节点</option>';
    select.disabled=mode!=='inherit'||!previous.length;
    select.required=mode==='inherit'&&!!previous.length;
    if(mode==='inherit'&&previous.length&&!select.value) select.value=previous[0].id;
    hint.textContent=previous.length?'可选择任意前序人工节点':'当前没有前序人工节点，请选择任务自定义';
  }
  window.wfRefreshAssigneeInheritance=wfRefreshAssigneeInheritance;
  function lockViewOnlyConfig(){
    if(!viewOnly) return;
    var config=document.getElementById('wfConfig');
    config.querySelectorAll('.wf-config-body input, .wf-config-body select, .wf-config-body textarea, .wf-config-body button').forEach(function(control){
      control.disabled=true;
    });
    config.querySelectorAll('.wf-config-body .ms-trigger').forEach(function(trigger){
      trigger.setAttribute('aria-disabled','true');
      trigger.classList.add('disabled');
    });
  }
  function openConfig(n){
    var config=document.getElementById('wfConfig');
    var human=isHumanNode(n);
    var condition=isConditionNode(n);
    var automatic=isAutomaticNode(n);
    config.classList.add('open');
    config.classList.toggle('human-mode',human||condition||automatic);
    document.getElementById('wfcName').textContent=n.name;
    document.getElementById('wfHumanConfig').style.display=human?'block':'none';
    document.getElementById('wfConditionNodeConfig').style.display=condition?'block':'none';
    document.getElementById('wfGenericConfig').style.display=automatic?'block':'none';
    if(human){
      document.getElementById('wfhName').value=n.name||'';
      document.getElementById('wfhIdent').value=n.ident||'';
      document.getElementById('wfhDesc').value=n.desc||'';
      var assigneeMode=n.assigneeMode||'task_custom';
      document.querySelectorAll('input[name="wfhAssigneeMode"]').forEach(function(input){ input.checked=input.value===assigneeMode; });
      wfRefreshAssigneeInheritance();
      document.getElementById('wfhAssigneeInheritNode').value=n.inheritAssigneeNodeId||'';
      var previousNodes=previousHumanNodes(n);
      var inferredReject=/支持驳回|可驳回/.test(n.desc||'')&&!/不支持驳回/.test(n.desc||'');
      var rejectEnabled=n.rejectEnabled==null?inferredReject:!!n.rejectEnabled;
      renderHumanChoices(
        'wfhAllowedActions',
        HUMAN_ACTIONS,
        rejectEnabled?['驳回']:[],
        null,
        previousNodes.length?[]:['驳回']
      );
      var rejectToggle=document.getElementById('wfhRejectEnabled');
      rejectToggle.disabled=!previousNodes.length;
      rejectToggle.checked=!!previousNodes.length&&rejectEnabled;
      document.getElementById('wfhRejectHint').textContent=previousNodes.length?
        '支持驳回到的节点（仅可选择当前节点的前序所有人工节点）':
        '支持驳回到的节点（当前节点没有前序人工节点，暂不可开启驳回）';
      renderRejectTargets(
        n,
        n.rejectTargets&&n.rejectTargets.length?
          n.rejectTargets:
          (rejectToggle.checked?previousNodes.map(function(item){return item.id;}):[])
      );
      wfToggleReject(rejectToggle.checked);
      lockViewOnlyConfig();
      return;
    }
    if(condition){
      document.getElementById('wfcndName').value=n.name||'';
      document.getElementById('wfcndIdent').value=n.ident||'';
      document.getElementById('wfcndDesc').value=n.desc||'';
      renderConditionBranches(normalizedBranches(n));
      lockViewOnlyConfig();
      return;
    }
    if(automatic){
      document.getElementById('wfaName').value=n.name||'';
      document.getElementById('wfaIdent').value=n.ident||'';
      document.getElementById('wfaDesc').value=n.desc||'';
      var selectedOperatorId=n.operatorId||Object.keys(OPS).filter(function(operatorId){
        return OPS[operatorId].ident===n.ident;
      })[0]||'';
      renderAutomaticOperatorOptions(selectedOperatorId);
    }
    lockViewOnlyConfig();
  }
  window.wfConditionMode=function(mode){
    document.querySelectorAll('#wfhConditionModes .wf-mode-tab').forEach(function(btn){ btn.classList.toggle('active',btn.getAttribute('data-mode')===mode); });
    document.getElementById('wfhConditionConfig').style.display=mode==='config'?'block':'none';
    document.getElementById('wfhConditionExpression').style.display=mode==='expression'?'block':'none';
  };
  window.wfConditionFieldChange=function(sel){
    var valueSelect=sel.closest('.wf-condition-row').querySelector('.wf-cond-value');
    valueSelect.innerHTML=optionList(CONDITION_VALUES[sel.value]||[],null);
  };
  window.wfAddCondition=function(){
    var holder=document.getElementById('wfhConditionRows'), wrap=document.createElement('div');
    wrap.innerHTML='<div class="wf-condition-row">'+
      '<select class="wf-edit-field wf-cond-field" onchange="wfConditionFieldChange(this)">'+optionList(Object.keys(CONDITION_VALUES),'质检结论')+'</select>'+
      '<select class="wf-edit-field wf-cond-value">'+optionList(CONDITION_VALUES['质检结论'],'合格')+'</select>'+
      '<button type="button" class="wf-row-del" onclick="wfRemoveCondition(this)" title="删除">&times;</button></div>';
    holder.appendChild(wrap.firstChild);
    document.getElementById('wfhConditionEmpty').style.display='none';
  };
  window.wfRemoveCondition=function(btn){
    btn.closest('.wf-condition-row').remove();
    if(!document.querySelector('#wfhConditionRows .wf-condition-row')) document.getElementById('wfhConditionEmpty').style.display='block';
  };
  window.wfRatioMode=function(mode){
    document.querySelectorAll('#wfhRatioModes .wf-mode-tab').forEach(function(btn){ btn.classList.toggle('active',btn.getAttribute('data-mode')===mode); });
    document.getElementById('wfhRatioConfig').style.display=mode==='config'?'block':'none';
    document.getElementById('wfhRatioExpressionWrap').style.display=mode==='expression'?'block':'none';
  };
  window.wfToggleRatioAdvanced=function(enabled){
    document.getElementById('wfhRatioDirect').style.display=enabled?'none':'block';
    document.getElementById('wfhRatioAdvancedWrap').style.display=enabled?'block':'none';
  };
  window.wfRatioFieldChange=function(sel){
    var valueSelect=sel.closest('.wf-ratio-rule').querySelector('.wf-ratio-value');
    valueSelect.innerHTML=optionList(CONDITION_VALUES[sel.value]||[],null);
  };
  window.wfAddRatioRule=function(){
    var holder=document.getElementById('wfhRatioRuleRows'), wrap=document.createElement('div');
    wrap.innerHTML='<div class="wf-ratio-rule">'+
      '<select class="wf-edit-field wf-ratio-field" onchange="wfRatioFieldChange(this)">'+optionList(Object.keys(CONDITION_VALUES),'质检结论')+'</select>'+
      '<select class="wf-edit-field wf-ratio-value">'+optionList(CONDITION_VALUES['质检结论'],'合格')+'</select>'+
      '<div style="position:relative;"><input class="wf-edit-field wf-ratio-percent" type="number" min="1" max="100" value="100" style="padding-right:21px;"><span style="position:absolute;right:8px;top:7px;color:#999;font-size:12px;">%</span></div>'+
      '<button type="button" class="wf-row-del" onclick="wfRemoveRatioRule(this)" title="删除">&times;</button></div>';
    holder.appendChild(wrap.firstChild);
    document.getElementById('wfhRatioRuleEmpty').style.display='none';
  };
  window.wfRemoveRatioRule=function(btn){
    btn.closest('.wf-ratio-rule').remove();
    if(!document.querySelector('#wfhRatioRuleRows .wf-ratio-rule')) document.getElementById('wfhRatioRuleEmpty').style.display='block';
  };
  window.wfBranchFieldChange=function(sel){
    var valueSelect=sel.closest('.wf-branch-rule').querySelector('.wf-branch-value');
    valueSelect.innerHTML=optionList(CONDITION_VALUES[sel.value]||[],null);
  };
  window.wfAddBranchRule=function(btn){
    var rules=btn.closest('.wf-branch-editor').querySelector('.wf-branch-rules');
    var wrap=document.createElement('div');
    var index=rules.querySelectorAll('.wf-branch-rule').length;
    wrap.innerHTML=branchRuleHtml({field:'供应商',operator:'等于',value:'供应商 B',percent:30},index);
    while(wrap.firstChild) rules.appendChild(wrap.firstChild);
  };
  window.wfRemoveBranchRule=function(btn){
    var editor=btn.closest('.wf-branch-editor');
    var rules=editor.querySelectorAll('.wf-branch-rule');
    if(rules.length<=1){ toast('每个分支至少保留一组条件与比例'); return; }
    var row=btn.closest('.wf-branch-rule');
    var logic=row.previousElementSibling&&row.previousElementSibling.classList.contains('wf-branch-logic')?row.previousElementSibling:null;
    if(!logic&&row.nextElementSibling&&row.nextElementSibling.classList.contains('wf-branch-logic')) logic=row.nextElementSibling;
    if(logic) logic.remove();
    row.remove();
  };
  function collectBranchRules(editor){
    return [].map.call(editor.querySelectorAll('.wf-branch-rule'),function(row){
      return {field:row.querySelector('.wf-branch-field').value,operator:row.querySelector('.wf-branch-operator').value,value:row.querySelector('.wf-branch-value').value,percent:Number(row.querySelector('.wf-branch-percent').value)||0};
    });
  }
  window.wfUserGroupsUpdate=function(cb){
    var wrap=document.getElementById('wfhUserGroupSelect');
    var checked=wrap.querySelectorAll('input:checked');
    var trigger=wrap.querySelector('.ms-trigger');
    var label=wrap.querySelector('.ms-label');
    var names=[].map.call(checked,function(input){return input.value;});
    trigger.classList.toggle('has-value',checked.length>0);
    label.textContent=names.length?names.join('、'):'请选择用户组';
    if(cb&&cb.checked) wrap.classList.remove('open');
  };
  window.wfToggleReject=function(enabled){
    var wrap=document.getElementById('wfhRejectWrap');
    wrap.style.display=enabled?'block':'none';
  };
  window.wfRejectTargetsUpdate=function(){
    var wrap=document.getElementById('wfhRejectPanel');
    var trigger=wrap.querySelector('.ms-trigger');
    if(!trigger) return;
    var checked=wrap.querySelectorAll('input:checked');
    var label=trigger.querySelector('.ms-label');
    var names=[].map.call(checked,function(input){return input.parentNode.textContent.trim();});
    trigger.classList.toggle('has-value',checked.length>0);
    label.textContent=names.length?names.join('、'):'请选择驳回节点';
  };
  window.wfSaveConfig=function(){
    var n=byId(selId); if(!n) return;
    if(isHumanNode(n)){
      var humanName=document.getElementById('wfhName').value.trim();
      if(!humanName){ toast('请填写节点名称'); return; }
      var rejectEnabled=document.getElementById('wfhRejectEnabled').checked;
      var rejectTargets=rejectEnabled?[].map.call(
        document.querySelectorAll('#wfhRejectPanel input:checked'),
        function(input){return input.value;}
      ):[];
      if(rejectEnabled&&!rejectTargets.length){ toast('请选择至少一个驳回节点'); return; }
      var assigneeMode=wfHumanAssigneeMode();
      var inheritNodeId=document.getElementById('wfhAssigneeInheritNode').value;
      if(assigneeMode==='inherit'&&!inheritNodeId){ toast('请选择前序人工节点'); return; }
      n.name=humanName;
      n.ident=document.getElementById('wfhIdent').value.trim();
      n.desc=document.getElementById('wfhDesc').value.trim();
      n.allowedActions=rejectEnabled?['驳回']:[];
      n.rejectEnabled=rejectEnabled;
      n.rejectTargets=rejectTargets;
      n.assigneeMode=assigneeMode;
      n.inheritAssigneeNodeId=assigneeMode==='inherit'?inheritNodeId:'';
      delete n.rounds;
      document.getElementById('wfcName').textContent=n.name;
      renderNodes(); toast('已保存人工节点配置'); return;
    }
    if(isConditionNode(n)){
      var conditionName=document.getElementById('wfcndName').value.trim();
      if(!conditionName){ toast('请填写节点名称'); return; }
      n.name=conditionName;
      n.ident=document.getElementById('wfcndIdent').value.trim();
      n.desc=document.getElementById('wfcndDesc').value.trim();
      n.branches=[].map.call(document.querySelectorAll('#wfConditionBranches .wf-branch-editor'),function(editor,index){
        return {name:editor.querySelector('.wf-branch-name').value.trim()||('CASE '+(index+1)),logic:'or',rules:collectBranchRules(editor)};
      });
      n.entryConditions=n.branches[0]?n.branches[0].rules.map(function(rule){return {field:rule.field,operator:rule.operator,value:rule.value};}):[];
      syncConditionNoBranch(n);
      document.getElementById('wfcName').textContent=n.name;
      renderNodes(); toast('已保存条件节点配置'); return;
    }
    if(isAutomaticNode(n)){
      var automaticName=document.getElementById('wfaName').value.trim();
      var automaticIdent=document.getElementById('wfaIdent').value.trim();
      var operatorId=document.getElementById('wfaOperator').value;
      if(!automaticName){ toast('请填写节点名称'); return; }
      if(!automaticIdent){ toast('请填写节点 ID'); return; }
      if(!operatorId||!OPS[operatorId]){ toast('请选择执行算子'); return; }
      n.name=automaticName;
      n.ident=automaticIdent;
      n.desc=document.getElementById('wfaDesc').value.trim();
      n.operatorId=operatorId;
      n.operatorName=OPS[operatorId].name;
      document.getElementById('wfcName').textContent=n.name;
      renderNodes(); toast('已保存自动化节点配置'); return;
    }
  };
  window.wfSrcChange=function(sel){
    sel.className='wf-param-src '+sel.value;
    var inp=sel.closest('.wf-param').querySelector('.wf-param-v');
    if(sel.value==='rf' && inp.value.indexOf('${')<0){ inp.value='${target_datasets}'; }
  };
  window.wfMarkOv=function(inp){
    var sel=inp.closest('.wf-param').querySelector('.wf-param-src');
    if(sel.value==='df'){ sel.value='ov'; sel.className='wf-param-src ov'; }
  };
  window.wfAddFlowParam=function(){
    var tb=document.getElementById('flowParamBody');
    var tr=document.createElement('tr');
    tr.innerHTML='<td><input class="fp-key" placeholder="英文标识"></td>'+
      '<td><input class="fp-val" placeholder="变量值"></td>'+
      '<td><a href="#" onclick="wfDelFlowParam(this);return false;" style="color:#bfbfbf;">删</a></td>';
    tb.appendChild(tr);
    tr.querySelector('.fp-key').focus();
  };
  window.wfDelFlowParam=function(a){ var tr=a.closest('tr'); if(tr) tr.remove(); };
  window.wfCloseConfig=function(){ document.getElementById('wfConfig').classList.remove('open','human-mode'); setSelectedNodes([]); renderNodes(); };
  window.wfDeleteSel=function(){
    wfHideNodeContextMenu();
    var ids=selectedNodeIds(); if(!ids.length) return;
    EDGES=EDGES.filter(function(edge){return ids.indexOf(edge.from)<0&&ids.indexOf(edge.to)<0;});
    NODES=NODES.filter(function(node){return ids.indexOf(node.id)<0;});
    document.getElementById('wfConfig').classList.remove('open','human-mode');
    setSelectedNodes([]); renderNodes();
    toast(ids.length>1?'已删除 '+ids.length+' 个节点':'已删除节点');
  };
  var OPS = __OPS__;
  window.wfOpenNodeDrawer=function(){
    var panel=document.getElementById('addTaskDrawer');
    if(!panel) return;
    panel.classList.add('active');
    var canvasRect=canvas.getBoundingClientRect();
    var panelHeight=panel.getBoundingClientRect().height||360;
    panel.style.left=(canvasRect.left+16)+'px';
    panel.style.top=Math.max(canvasRect.top+16,canvasRect.bottom-64-panelHeight)+'px';
    var search=panel.querySelector('input[placeholder^="搜索"]');
    if(search) setTimeout(function(){ search.focus(); },0);
  };
  window.wfCloseNodeDrawer=function(){
    var panel=document.getElementById('addTaskDrawer');
    if(panel) panel.classList.remove('active');
  };
  function wfHideNodeContextMenu(){
    var menu=document.getElementById('wfNodeContextMenu');
    if(menu) menu.classList.remove('active');
  }
  function wfOpenNodeContextMenu(node,event){
    if(viewOnly||!node||node.kind==='flow-input'||node.kind==='flow-output') return;
    var menu=document.getElementById('wfNodeContextMenu');
    if(!menu) return;
    setSelectedNodes([node.id]);
    menu.setAttribute('data-node-id',node.id);
    renderNodes();
    var r=canvas.getBoundingClientRect();
    menu.classList.add('active');
    var menuWidth=menu.offsetWidth||120, menuHeight=menu.offsetHeight||76;
    var left=Math.max(8,Math.min(r.width-menuWidth-8,event.clientX-r.left));
    var top=Math.max(8,Math.min(r.height-menuHeight-8,event.clientY-r.top));
    menu.style.left=left+'px';
    menu.style.top=top+'px';
  }
  document.addEventListener('click',function(event){
    var panel=document.getElementById('addTaskDrawer');
    if(panel&&panel.classList.contains('active')&&!event.target.closest('#addTaskDrawer')) wfCloseNodeDrawer();
    var menu=document.getElementById('wfNodeContextMenu');
    if(menu&&menu.classList.contains('active')&&!event.target.closest('#wfNodeContextMenu')) wfHideNodeContextMenu();
  });
  document.addEventListener('keydown',function(event){
    if(viewOnly) return;
    var target=event.target;
    if(target&&(target.matches('input,textarea,select')||target.isContentEditable)) return;
    var ids=selectedNodeIds();
    var shortcutKey=String(event.key).toLowerCase();
    if((event.metaKey||event.ctrlKey)&&(shortcutKey==='c'||shortcutKey==='d')&&ids.length){
      event.preventDefault(); wfCopySelection(); return;
    }
    if((event.key==='Delete'||event.key==='Backspace')&&ids.length){
      event.preventDefault(); wfDeleteSel(); return;
    }
    if(event.key==='Escape'){
      wfHideNodeContextMenu(); setSelectedNodes([]);
      document.getElementById('wfConfig').classList.remove('open','human-mode');
      renderNodes();
    }
  });
  function syncConditionNoBranch(n){
    var branchCount=(n.branches&&n.branches.length?n.branches.length:1);
    var primary=EDGES.filter(function(edge){
      return edge.from===n.id&&(edge.fromPort||'out')==='branch-0';
    })[0];
    if(!primary){
      var next=NODES.filter(function(node){return node.id!==n.id&&node.kind!=='flow-input'&&node.x>n.x;})
        .sort(function(a,b){return a.x-b.x;})[0];
      if(next) primary={from:n.id,to:next.id,fromPort:'branch-0'};
    }
    EDGES=EDGES.filter(function(edge){
      return !(edge.from===n.id&&((edge.fromPort||'out').indexOf('branch')===0));
    });
    if(primary) EDGES.push(primary);
    for(var branchIndex=1;branchIndex<branchCount;branchIndex++){
      EDGES.push({from:n.id,to:'flow-output',fromPort:'branch-'+branchIndex});
    }
    EDGES.push({from:n.id,to:'flow-output',fromPort:'branch',branch:'no'});
  }
  function wfCopySelection(){
    var sourceIds=selectedNodeIds(); if(!sourceIds.length) return;
    var copiedIds=[];
    sourceIds.forEach(function(sourceId){
      var original=byId(sourceId); if(!original) return;
      var clone=JSON.parse(JSON.stringify(original));
      seq++; clone.id='n'+seq;
      clone.name=(original.name||'节点')+'（副本）';
      clone.ident=(original.ident||original.kind||'node')+'_copy_'+seq;
      var position=pickNodePosition(original.kind==='condition'?CONDITION_H:NODE_H);
      clone.x=position.x; clone.y=position.y;
      NODES.push(clone); copiedIds.push(clone.id);
    });
    if(!copiedIds.length) return;
    setSelectedNodes(copiedIds);
    document.getElementById('wfConfig').classList.remove('open','human-mode');
    wfHideNodeContextMenu(); renderNodes();
    toast(copiedIds.length>1?'已复制 '+copiedIds.length+' 个节点':'已复制节点');
  }
  window.wfAddTypedNode=function(kind){
    if(kind==='copy'){
      wfCopySelection(); return;
    }
    var defs={
      human:{name:'人工节点',desc:'使用工作台进行人工处理',icon:'人'},
      automatic:{name:'自动化节点',desc:'通过算子自动处理数据',icon:'⚙'},
      condition:{name:'条件节点',desc:'按条件判断结果进行分流',icon:'◇'}
    };
    var def=defs[kind]; if(!def) return;
    var nodePosition=pickNodePosition(kind==='condition'?CONDITION_H:NODE_H);
    seq++; var id='n'+seq;
    var node={
      id:id,name:def.name,ident:kind+'_'+seq,desc:def.desc,enabled:'启用',creator:'当前用户',
      image:kind==='automatic'?'frontdesk-py3.10:latest':(kind==='condition'?'规则引擎':'人工工作台'),
      script:kind==='automatic'?'请选择算子':(kind==='condition'?'条件表达式':'人工任务'),
      operatorId:kind==='automatic'?(Object.keys(OPS)[0]||''):'',
      params:'',returns:'处理结果',kind:kind,
      businessStage:'通用',workbench:'质检工作台',userGroups:[],
      assigneeType:'supplier',assigneeMode:'task_custom',inheritAssigneeNodeId:'',
      allowedActions:['提交','暂离'],x:nodePosition.x,y:nodePosition.y
    };
    NODES.push(node);
    setSelectedNodes([id]);
    wfCloseNodeDrawer();
    renderNodes(); toast('已添加'+def.name);
  };
  window.wfAddNode=function(opId){
    var o=OPS[opId]; if(!o) return;
    seq++; var id='n'+seq;
    var nodePosition=pickNodePosition(NODE_H);
    NODES.push({id:id, name:o.name, ident:o.ident, desc:o.desc, enabled:o.enabled, creator:o.creator,
                image:o.image, script:o.script, params:o.params, returns:o.returns,
                x:nodePosition.x, y:nodePosition.y});
    setSelectedNodes([id]);
    wfCloseNodeDrawer();
    renderNodes(); toast('已添加算子: '+o.name);
  };
  window.wfZoom=function(d){ z=Math.min(1.6, Math.max(0.25, Math.round((z+d)*10)/10)); document.getElementById('wfZlvl').textContent=Math.round(z*100)+'%'; applyPan(); };
  window.wfFit=function(){
    var minX=Infinity,minY=Infinity,maxX=0,maxY=0;
    if(FRAMES.length){
      FRAMES.forEach(function(f){ minX=Math.min(minX,f.x); minY=Math.min(minY,f.y); maxX=Math.max(maxX,f.x+f.w); maxY=Math.max(maxY,f.y+f.h); });
    } else {
      NODES.forEach(function(n){ minX=Math.min(minX,n.x); minY=Math.min(minY,n.y); maxX=Math.max(maxX,n.x+W); maxY=Math.max(maxY,n.y+nodeH(n)); });
    }
    if(minX===Infinity){ z=1; panX=0; panY=0; }
    else {
      var r=canvas.getBoundingClientRect(), cw=Math.max(1,maxX-minX), ch=Math.max(1,maxY-minY);
      z=Math.min(1,Math.max(.25,Math.min((r.width-56)/cw,(r.height-56)/ch)));
      panX=(r.width-cw*z)/2-minX*z;
      panY=(r.height-ch*z)/2-minY*z;
    }
    document.getElementById('wfZlvl').textContent=Math.round(z*100)+'%';
    applyPan();
  };

  renderFrames(); applyPan(); renderNodes();
  if(FRAMES.length) setTimeout(function(){ wfFit(); },0);
})();
"""


def _processing_canvas_payload_legacy(pl):
    frame_x = 50
    frame_y = 70
    frame_gap = 50
    frame_height = 230
    node_width = 220
    node_gap = 260
    flattened_phases = []

    for phase in pl["phases"]:
        flattened = []
        for node in phase["nodes"]:
            children = node.get("children", [])
            if children:
                for child_index, child in enumerate(children):
                    child_meta = f"{node['name']} · {node.get('meta', '')}"
                    if child_index and node.get("bidirectional"):
                        child_meta += " · 可驳回至上一轮"
                    flattened.append(
                        {
                            "name": child,
                            "kind": "human",
                            "meta": child_meta,
                        }
                    )
            else:
                flattened.append(node)
        flattened_phases.append(flattened)

    max_nodes = max((len(nodes) for nodes in flattened_phases), default=1)
    # 每个环节左右各保留一个明确的输入 / 输出端点。
    frame_width = 240 + max_nodes * node_gap
    frames = []
    canvas_nodes = []
    canvas_edges = []

    for phase_index, (phase, phase_nodes) in enumerate(
        zip(pl["phases"], flattened_phases)
    ):
        y = frame_y + phase_index * (frame_height + frame_gap)
        frames.append(
            {
                "id": f"phase-{phase_index + 1}",
                "name": phase["name"],
                "shortName": phase["short_name"],
                "desc": phase["desc"],
                "x": frame_x,
                "y": y,
                "w": frame_width,
                "h": frame_height,
                "inputId": f"phase-{phase_index + 1}-input",
                "outputId": f"phase-{phase_index + 1}-output",
            }
        )
        phase_ids = []
        condition_ids = []
        for node_index, node in enumerate(phase_nodes):
            node_id = f"p{phase_index + 1}n{node_index + 1}"
            kind = node.get("kind", "operator")
            executor = {
                "automatic": ("frontdesk-py3.10:latest", "自动化算子"),
                "condition": ("规则引擎", "条件表达式"),
                "human": ("人工工作台", "人工任务"),
                "acceptance": ("验收工作台", "人工验收"),
            }.get(kind, ("frontdesk-py3.10:latest", "处理节点"))
            canvas_nodes.append(
                {
                    "id": node_id,
                    "name": node["name"],
                    "ident": node.get(
                        "ident",
                        f"{kind}_{phase_index + 1}_{node_index + 1}",
                    ),
                    "desc": node.get("meta", ""),
                    "enabled": "启用",
                    "creator": pl["creator"],
                    "image": node.get("image", executor[0]),
                    "script": node.get("script", executor[1]),
                    "params": node.get("params", node.get("meta", "")),
                    "returns": node.get("returns", "处理结果"),
                    "kind": kind,
                    "phase": phase["short_name"],
                    "phaseId": f"phase-{phase_index + 1}",
                    "x": frame_x + 130 + node_index * node_gap,
                    "y": y + 82,
                }
            )
            phase_ids.append(node_id)
            if kind == "condition":
                condition_ids.append(node_id)
            if node_index:
                canvas_edges.append(
                    {"from": phase_ids[node_index - 1], "to": node_id}
                )
        phase_input_id = f"phase-{phase_index + 1}-input"
        phase_output_id = f"phase-{phase_index + 1}-output"
        if phase_ids:
            canvas_edges.append({"from": phase_input_id, "to": phase_ids[0]})
            canvas_edges.append({"from": phase_ids[-1], "to": phase_output_id})
        else:
            canvas_edges.append({"from": phase_input_id, "to": phase_output_id})
        for condition_id in condition_ids:
            canvas_edges.append(
                {
                    "from": condition_id,
                    "to": phase_output_id,
                    "fromPort": "branch",
                    "branch": "no",
                }
            )

    return canvas_nodes, canvas_edges, frames


def _processing_canvas_payload(pl):
    """Build a flow-engine graph without business-stage containers."""
    flow_nodes = pl.get("flow_nodes", [])
    canvas_nodes = [
        {
            "id": "flow-input",
            "name": "start",
            "ident": "input",
            "desc": "Start",
            "kind": "flow-input",
            "x": 60,
            "y": 260,
        }
    ]
    canvas_edges = []
    node_name_to_id = {}
    for index, node in enumerate(flow_nodes):
        node_id = f"n{index + 1}"
        kind = node.get("kind", "automatic")
        executor = {
            "automatic": ("frontdesk-py3.10:latest", "自动化算子"),
            "condition": ("规则引擎", "条件表达式"),
            "human": ("人工工作台", "人工任务"),
        }.get(kind, ("frontdesk-py3.10:latest", "处理节点"))
        canvas_node = {
            "id": node_id,
            "name": node["name"],
            "ident": node.get("ident", f"{kind}_{index + 1}"),
            "desc": node.get("meta", ""),
            "enabled": "启用",
            "creator": pl["creator"],
            "image": node.get("image", executor[0]),
            "script": node.get("script", executor[1]),
            "params": node.get("params", node.get("meta", "")),
            "returns": node.get("returns", "处理结果"),
            "operatorId": node.get("operator_id", ""),
            "kind": kind,
            "businessStage": pl.get("business_stage", "通用"),
            "workbench": node.get("workbench"),
            "userGroups": node.get("user_groups", []),
            "assigneeType": node.get("assignee_type", "supplier"),
            "assigneeMode": node.get("assignee_mode", "task_custom"),
            "inheritAssigneeNodeId": node_name_to_id.get(
                node.get("inherit_assignee_node", ""),
                node.get("inherit_assignee_node_id", ""),
            ),
            "allowedActions": node.get("allowed_actions", ["提交", "暂离"]),
            "rejectEnabled": node.get("reject_enabled", False),
            "rejectTargetNames": node.get("reject_targets", []),
            "x": 360 + index * 300,
            "y": 236 if kind == "condition" else 260,
        }
        if kind == "condition":
            canvas_node["branches"] = [
                (node.get("branches") or [
                    {
                        "name": "供应商抽样",
                        "logic": "or",
                        "rules": [
                            {
                                "field": "供应商",
                                "operator": "等于",
                                "value": "供应商 A",
                                "percent": 50,
                            },
                            {
                                "field": "供应商",
                                "operator": "等于",
                                "value": "供应商 B",
                                "percent": 30,
                            },
                        ],
                    }
                ])[0]
            ]
        canvas_nodes.append(canvas_node)
        node_name_to_id[node["name"]] = node_id

    output_x = 420 + len(flow_nodes) * 300
    canvas_nodes.append(
        {
            "id": "flow-output",
            "name": "end",
            "ident": "output",
            "desc": "End",
            "kind": "flow-output",
            "x": output_x,
            "y": 260,
        }
    )
    sequence_ids = ["flow-input"] + [
        f"n{index + 1}" for index in range(len(flow_nodes))
    ] + ["flow-output"]
    node_by_id = {node["id"]: node for node in canvas_nodes}
    for source, target in zip(sequence_ids, sequence_ids[1:]):
        edge = {"from": source, "to": target}
        if node_by_id[source].get("kind") == "condition":
            edge["fromPort"] = "branch-0"
        canvas_edges.append(edge)
    for node in canvas_nodes:
        if node.get("kind") == "condition":
            branch_count = len(node.get("branches", [])) or 1
            for branch_index in range(1, branch_count):
                canvas_edges.append(
                    {
                        "from": node["id"],
                        "to": "flow-output",
                        "fromPort": f"branch-{branch_index}",
                    }
                )
            canvas_edges.append(
                {
                    "from": node["id"],
                    "to": "flow-output",
                    "fromPort": "branch",
                    "branch": "no",
                }
            )
        target_names = node.pop("rejectTargetNames", [])
        node["rejectTargets"] = [
            node_name_to_id[name]
            for name in target_names
            if name in node_name_to_id
        ]
    return canvas_nodes, canvas_edges, []


@app.route("/pipelines/<pid>")
def pipeline_editor(pid):
    pl = next((p for p in PIPELINES if p["id"] == pid), None)
    is_draft_version = request.args.get("version") == "draft" and pl is not None
    if is_draft_version:
        pl = {**pl, "name": f'{pl["name"]}（草稿）', "status": "草稿"}
    is_new = pid == "new" or pl is None
    view_mode = request.args.get("mode") == "view" and not is_new
    is_processing_flow = is_new or bool(pl and pl.get("flow_nodes"))
    flow_ident = (
        request.args.get("flow_ident", "").strip()
        if is_new
        else pl.get("ident", pl["id"])
    ) or "new-flow"
    name = (
        request.args.get("flow_name", "").strip() or "新建流程"
        if is_new
        else pl["name"]
    )
    flow_business_stage = (
        request.args.get("business_stage", "").strip() or "质检"
        if is_new
        else pl.get("business_stage", "通用")
    )
    flow_desc = (
        request.args.get("desc", "").strip()
        if is_new
        else pl.get("desc", "")
    )
    flow_status = "草稿" if is_new else pl.get("status", "草稿")
    if flow_status not in {"草稿", "启用", "停用"}:
        flow_status = "草稿"
    can_edit_flow_name = flow_status == "草稿"
    stages = [] if is_new else pl["stages"]

    # 初始节点 (自由画布: 左→右铺开), 以及顺序连线
    init_nodes, init_edges, phase_frames = [], [], []
    if is_processing_flow and pl:
        init_nodes, init_edges, phase_frames = _processing_canvas_payload(pl)
    elif is_processing_flow:
        init_nodes = [
            {
                "id": "flow-input",
                "name": "input",
                "ident": "input",
                "desc": "请配置流程输入契约",
                "kind": "flow-input",
                "x": 60,
                "y": 210,
            },
            {
                "id": "flow-output",
                "name": "output",
                "ident": "output",
                "desc": "请配置流程输出契约",
                "kind": "flow-output",
                "x": 500,
                "y": 210,
            },
        ]
        init_edges = [{"from": "flow-input", "to": "flow-output"}]
    elif not is_processing_flow:
        for i, sid in enumerate(stages):
            op = next((o for o in OPERATORS if o["id"] == sid), None)
            if not op:
                continue
            nid = f"n{i}"
            init_nodes.append({
                "id": nid, "name": op["name"].split(" ")[0], "ident": op["ident"],
                "desc": op["desc"], "enabled": "启用", "creator": op["creator"],
                "image": "frontdesk-py3.10:latest", "script": "python " + op["script"],
                "params": op["params"], "returns": op["returns"],
                "x": 60 + i * 280, "y": 150 + (i % 2) * 50,
            })
            if i > 0:
                init_edges.append({"from": f"n{i-1}", "to": nid})
    nodes_json = json.dumps(init_nodes, ensure_ascii=False)
    edges_json = json.dumps(init_edges, ensure_ascii=False)
    frames_json = json.dumps(phase_frames, ensure_ascii=False)
    operator_source = MANAGED_OPERATORS if is_processing_flow else OPERATORS
    ops_map = {o["id"]: {"name": o["name"] if is_processing_flow else o["name"].split(" ")[0], "ident": o["ident"], "desc": o["desc"],
                         "enabled": "启用", "creator": o["creator"], "image": "frontdesk-py3.10:latest",
                         "script": "python " + o["script"], "params": o["params"], "returns": o["returns"]}
               for o in operator_source}
    ops_json = json.dumps(ops_map, ensure_ascii=False)

    # 数据处理流程先选择节点类型；旧工作流仍从算子库选择算子。
    node_label = "节点" if is_processing_flow else "算子"
    if is_processing_flow:
        op_items = """
          <div class="wf-node-type-options">
            <button type="button" class="wf-node-type-option human" data-node-type="human" onclick="wfAddTypedNode('human')"><span class="wf-node-ic"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.2"/><path d="M5.5 19c.8-4 3-6 6.5-6s5.7 2 6.5 6"/></svg></span><span><b>人工节点</b><small>通过工作台由操作员完成处理</small></span></button>
            <button type="button" class="wf-node-type-option automatic" data-node-type="automatic" onclick="wfAddTypedNode('automatic')"><span class="wf-node-ic"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3.2"/><path d="M12 3.5v2M12 18.5v2M3.5 12h2M18.5 12h2M6 6l1.5 1.5M16.5 16.5 18 18M18 6l-1.5 1.5M7.5 16.5 6 18"/></svg></span><span><b>自动化节点</b><small>绑定算子自动完成数据处理</small></span></button>
            <button type="button" class="wf-node-type-option condition" data-node-type="condition" onclick="wfAddTypedNode('condition')"><span class="wf-node-ic"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="7" cy="5" r="2"/><circle cx="17" cy="12" r="2"/><circle cx="17" cy="19" r="2"/><path d="M7 7v7a5 5 0 0 0 5 5h3M7 10a5 5 0 0 0 5 2h3"/></svg></span><span><b>条件节点</b><small>配置条件并从“是 / 否”分支流转</small></span></button>
          </div>
        """
        node_drawer_controls = ""
        node_button_handler = "wfOpenNodeDrawer();event.stopPropagation()"
    else:
        op_items = ""
        for o in OPERATORS:
            op_items += (
                f"""<div class="op-pick" onclick="wfAddNode('{o['id']}')">"""
                f'<div><b>{o["name"]}</b> <span class="op-script">{o["ident"]}</span></div>'
                f'<div class="muted" style="font-size:12px;">{o["cat"]} · {o["creator"]}</div></div>'
            )
        node_drawer_controls = (
            f'<input placeholder="搜索{node_label}..." '
            'style="width:100%;box-sizing:border-box;height:34px;padding:5px 12px;'
            'border:1px solid #d9d9d9;border-radius:8px;margin-bottom:12px;outline:none;">'
        )
        node_button_handler = "wfOpenNodeDrawer();event.stopPropagation()"

    initial_saved_at = (pl.get("updated") if pl else "") or "未保存"
    flow_data_attr = " ".join(
        item
        for item in (
            (
                f'data-processing-flow="{html.escape(pl["id"] if pl else "new", quote=True)}"'
                if is_processing_flow
                else ""
            ),
            f'data-flow-ident="{html.escape(flow_ident, quote=True)}"',
            f'data-business-stage="{html.escape(flow_business_stage, quote=True)}"',
            f'data-flow-description="{html.escape(flow_desc, quote=True)}"',
            f'data-last-saved="{html.escape(initial_saved_at, quote=True)}"',
        )
        if item
    )
    empty_copy = (
        "画布为空, 点击「+ 添加节点」开始编排"
        if is_processing_flow
        else "画布为空, 点击「+ 添加算子」开始编排"
    )
    phase_button = ""
    stage_class = "wf-stage view-only" if view_mode else "wf-stage"
    node_action_button = (
        ""
        if view_mode
        else f'<button class="btn-primary btn" onclick="{node_button_handler}">'
        f'&plus; 添加{node_label}</button>'
    )
    editor_actions = (
        ""
        if view_mode
        else """
        <button class="btn" onclick="document.getElementById('flowParamDrawer').classList.add('active')">&#123;&#125; 流程参数</button>
        <button class="btn" onclick="wfSaveDraft(true)">&#128190; 保存</button>
        <button class="btn-primary btn" onclick="wfConfirmPublish()">发布</button>
        """
    )
    rename_control = (
        '<button type="button" class="wf-title-edit" title="编辑流程信息" '
        'aria-label="编辑流程信息" onclick="openFlowEditModal()">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 16.5V20h3.5L18.8 8.7l-3.5-3.5L4 16.5Z"/>'
        '<path d="m13.8 6.7 3.5 3.5"/></svg></button>'
    )
    flow_ident_value = html.escape(flow_ident, quote=True)
    flow_name_value = html.escape(name, quote=True)
    flow_stage_options = "".join(
        f'<option value="{stage}"{" selected" if flow_business_stage == stage else ""}>{stage}</option>'
        for stage in ("质检", "标注", "验收")
    )
    flow_name_disabled = "" if can_edit_flow_name else " disabled"
    flow_edit_save = (
        '<button type="button" class="btn btn-primary" onclick="saveFlowEditModal()">保存</button>'
        if can_edit_flow_name
        else ""
    )
    content = f"""
    <style>
      .wf-stage.view-only .wf-node-del,
      .wf-stage.view-only .wf-config-foot {{ display:none; }}
      .wf-stage.view-only .wf-config-body input,
      .wf-stage.view-only .wf-config-body select,
      .wf-stage.view-only .wf-config-body textarea,
      .wf-stage.view-only .wf-config-body button {{ pointer-events:none; }}
      .wf-stage.view-only .wf-config-body input:disabled,
      .wf-stage.view-only .wf-config-body select:disabled,
      .wf-stage.view-only .wf-config-body textarea:disabled {{background:#f5f6f7;color:rgba(0,0,0,.38);border-color:#e3e7e9;cursor:not-allowed}}
      .wf-stage.view-only .wf-config-body button:disabled {{opacity:.45;cursor:not-allowed}}
      .wf-stage.view-only .wf-config-body .ms-trigger.disabled {{pointer-events:none;background:#f5f6f7;color:rgba(0,0,0,.38);border-color:#e3e7e9;cursor:not-allowed}}
      .wf-title-edit{{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;padding:0;border:1px solid #b9dfe2;border-radius:7px;background:#f2fbfb;color:#147a83;cursor:pointer;transition:.15s}}
      .wf-title-edit:hover{{border-color:#149daa;background:#e5f6f7;color:#0f6971;box-shadow:0 0 0 2px rgba(20,157,170,.1)}}
      .wf-title-edit svg{{width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}}
      .wf-save-time{{color:rgba(0,0,0,.45);font-size:12px;font-weight:400;white-space:nowrap}}
      .wf-effective-tag.draft{{background:#fff4dc;color:#a86808}}.wf-effective-tag.disabled{{background:#f1f3f4;color:#728188}}
      .wf-flow-edit-modal{{width:480px;max-width:calc(100vw - 24px)}}.wf-flow-edit-modal .fg{{margin-bottom:18px}}.wf-flow-edit-modal .fg input,.wf-flow-edit-modal .fg select{{height:38px;box-sizing:border-box}}.wf-flow-edit-modal .fg input:disabled,.wf-flow-edit-modal .fg select:disabled{{background:#f5f6f7;color:#7c898e;cursor:not-allowed}}
    </style>
    <script>
      function wfConfirmPublish() {{
        document.getElementById('wfPublishConfirmModal').classList.add('active');
      }}
      function closeWfPublishConfirm() {{
        document.getElementById('wfPublishConfirmModal').classList.remove('active');
      }}
      function confirmWfPublish() {{
        closeWfPublishConfirm();
        toast('已发布');
      }}
      function openFlowEditModal() {{ document.getElementById('flowEditModal').classList.add('active'); }}
      function closeFlowEditModal() {{ document.getElementById('flowEditModal').classList.remove('active'); }}
      function saveFlowEditModal() {{
        var nameInput=document.getElementById('flowEditName');
        if(!nameInput.value.trim()){{toast('请输入流程名称');return;}}
        document.getElementById('wfFlowTitleName').textContent=nameInput.value.trim();
        toast('Demo: 已保存流程信息');
        closeFlowEditModal();
      }}
    </script>
    <div class="wf-topbar">
      <div class="wf-title"><a href="/pipelines" class="back">&#8249;</a> <span id="wfFlowTitleName">{flow_name_value}</span>{rename_control}
        <span id="wfEffectiveTag" class="wf-effective-tag{' draft' if flow_status == '草稿' else (' disabled' if flow_status == '停用' else '')}">{flow_status}</span>
        <span id="wfLastSaved" class="wf-save-time">保存时间：{html.escape(initial_saved_at)}</span>
      </div>
      <div class="wf-actions">{editor_actions}</div>
    </div>
    <div class="modal-mask" id="flowEditModal" onclick="if(event.target===this)closeFlowEditModal()">
      <div class="modal-box wf-flow-edit-modal">
        <div class="drawer-head"><h3>编辑流程信息</h3><button type="button" class="drawer-close" onclick="closeFlowEditModal()">&times;</button></div>
        <div class="drawer-body">
          <div class="fg"><label>流程标识</label><input id="flowEditIdent" value="{flow_ident_value}" disabled></div>
          <div class="fg"><label>流程名称</label><input id="flowEditName" value="{flow_name_value}"{flow_name_disabled}></div>
          <div class="fg"><label>业务环节</label><select id="flowEditStage" disabled>{flow_stage_options}</select></div>
        </div>
        <div class="drawer-foot"><button type="button" class="btn" onclick="closeFlowEditModal()">关闭</button>{flow_edit_save}</div>
      </div>
    </div>
    <div class="modal-mask" id="wfPublishConfirmModal" onclick="if(event.target===this)closeWfPublishConfirm()">
      <div class="modal-box wf-flow-edit-modal" role="dialog" aria-modal="true" aria-labelledby="wfPublishConfirmTitle">
        <div class="drawer-head"><h3 id="wfPublishConfirmTitle">发布流程</h3><button type="button" class="drawer-close" onclick="closeWfPublishConfirm()" aria-label="关闭">&times;</button></div>
        <div class="drawer-body"><p style="margin:0;color:#263238;font-size:14px;line-height:1.7;">发布后不可修改，确认发布？</p></div>
        <div class="drawer-foot"><button type="button" class="btn" onclick="closeWfPublishConfirm()">取消</button><button type="button" class="btn btn-primary" onclick="confirmWfPublish()">确认发布</button></div>
      </div>
    </div>
    <div class="{stage_class}" {flow_data_attr}>
      <div class="wf-canvas" id="wfCanvas" tabindex="0" aria-label="流程画布">
        <div class="wf-pan" id="wfPan" style="width:4000px;height:3000px;">
          <div id="wfFrames"></div>
          <svg class="wf-edges" id="wfEdges"></svg>
          <div id="wfNodes"></div>
        </div>
        <div class="wf-selection-box" id="wfSelectionBox"></div>
        <div class="wf-empty" id="wfEmpty"><div style="font-size:32px;">&#9783;</div><div>{empty_copy}</div></div>
        <div class="wf-toolbar">
          <button class="zbtn" onclick="wfZoom(-0.1)">&minus;</button>
          <span class="zlvl" id="wfZlvl">100%</span>
          <button class="zbtn" onclick="wfZoom(0.1)">&plus;</button>
          <button class="zbtn" onclick="wfFit()" title="适应画布">&#9974;</button>
          <span class="sep"></span>
          {phase_button}
          {node_action_button}
        </div>
        <div class="wf-add-node-popover" id="addTaskDrawer" onclick="event.stopPropagation()">
          <div class="wf-add-node-popover-head"><b>添加{node_label}</b><button type="button" class="drawer-close" aria-label="关闭" onclick="wfCloseNodeDrawer();event.stopPropagation()">&times;</button></div>
          <div class="wf-add-node-popover-body">
            {node_drawer_controls}
            {op_items}
          </div>
        </div>
        <div class="wf-context-menu" id="wfNodeContextMenu">
          <button type="button" data-action="copy">复制</button>
          <button type="button" class="danger" data-action="delete">删除</button>
        </div>
      </div>

      <div class="wf-config" id="wfConfig">
        <div class="wf-config-head"><b id="wfcName">节点</b><button class="drawer-close" onclick="wfCloseConfig()">&times;</button></div>
        <div class="wf-config-body">
          <div id="wfHumanConfig" style="display:none;">
            <div class="wf-cfg-sec">基础信息</div>
            <div class="wf-human-grid">
              <label><span class="wf-human-label">节点名称</span><input id="wfhName" class="wf-edit-field" placeholder="请输入节点名称"></label>
              <label><span class="wf-human-label">标识</span><input id="wfhIdent" class="wf-edit-field" placeholder="英文标识"></label>
              <label class="full"><span class="wf-human-label">描述</span><textarea id="wfhDesc" class="wf-edit-field" placeholder="请输入节点描述"></textarea></label>
            </div>

            <div class="wf-cfg-sec">处理人</div>
            <div class="wf-human-label">处理人分配</div>
            <div class="wf-choice-grid" id="wfhAssigneeMode">
              <label><input type="radio" name="wfhAssigneeMode" value="task_custom" checked onchange="wfRefreshAssigneeInheritance()"><span>任务自定义</span></label>
              <label><input type="radio" name="wfhAssigneeMode" value="inherit" onchange="wfRefreshAssigneeInheritance()"><span>继承前序节点</span></label>
            </div>
            <div id="wfhAssigneeInheritWrap" style="display:none; margin-top:10px;">
              <label><span class="wf-human-label">继承节点</span><select id="wfhAssigneeInheritNode" class="wf-edit-field"></select></label>
              <div id="wfhAssigneeInheritHint" class="wf-reject-hint"></div>
            </div>

            <div class="wf-cfg-sec">可用操作</div>
            <div class="wf-choice-grid actions" id="wfhAllowedActions"></div>

            <div class="wf-operation-reject">
              <div id="wfhRejectHint" class="wf-human-label">支持驳回到的节点（仅可选择当前节点的前序所有人工节点）</div>
              <div id="wfhRejectWrap" class="wf-reject-wrap" style="display:none;">
                <div class="ms-wrap wf-reject-target-list" id="wfhRejectPanel"></div>
              </div>
            </div>
          </div>

          <div id="wfConditionNodeConfig" style="display:none;">
            <div class="wf-cfg-sec">基础信息</div>
            <div class="wf-human-grid">
              <label><span class="wf-human-label">节点名称</span><input id="wfcndName" class="wf-edit-field" placeholder="请输入节点名称"></label>
              <label><span class="wf-human-label">标识</span><input id="wfcndIdent" class="wf-edit-field" placeholder="英文标识"></label>
              <label class="full"><span class="wf-human-label">描述</span><textarea id="wfcndDesc" class="wf-edit-field" placeholder="请输入节点描述"></textarea></label>
            </div>

            <div class="wf-cfg-sec">分支设置</div>
            <div class="wf-human-label">IF 分支内多组规则为「或（OR）」关系；每条条件由「筛选项 / 操作符 / 值」三元组组成，比例独立生效。</div>
            <div id="wfConditionBranches"></div>
            <div class="wf-fallback-box"><b>ELSE · 其他</b>未命中以上任一分支的数据统一进入兜底分支。</div>
          </div>

          <div id="wfGenericConfig">
            <div class="wf-cfg-sec">基础信息</div>
            <div class="wf-human-grid">
              <label><span class="wf-human-label">节点名称</span><input id="wfaName" class="wf-edit-field" placeholder="请输入节点名称"></label>
              <label><span class="wf-human-label">节点 ID</span><input id="wfaIdent" class="wf-edit-field" placeholder="请输入节点 ID"></label>
              <label class="full"><span class="wf-human-label">节点描述</span><textarea id="wfaDesc" class="wf-edit-field" placeholder="请输入节点描述"></textarea></label>
              <label class="full"><span class="wf-human-label">执行算子</span><select id="wfaOperator" class="wf-edit-field"></select></label>
            </div>
          </div>
        </div>
        <div class="wf-config-foot">
          <button class="btn" onclick="wfDeleteSel()">删除节点</button>
          <button class="btn-primary btn" onclick="wfSaveConfig()">保存</button>
        </div>
      </div>
    </div>

    <!-- 流程级全局参数: 被多个节点引用, 跑同一流程换不同输入 -->
    <div class="drawer-mask" id="flowParamDrawer" onclick="if(event.target===this)this.classList.remove('active')">
      <div class="drawer" style="width:480px;">
        <div class="drawer-head"><h3>流程参数</h3><button class="drawer-close" onclick="document.getElementById('flowParamDrawer').classList.remove('active')">&times;</button></div>
        <div class="drawer-body">
          <div class="muted" style="font-size:12px;margin-bottom:14px;line-height:1.6;">流程级全局变量, 被多个节点以 <code>${{变量名}}</code> 引用。改这里 = 同一流程换不同输入跑, 无需逐个节点改。</div>
          <table class="ant-table" style="font-size:13px;">
            <thead><tr><th style="width:150px;">变量名</th><th>值</th><th style="width:60px;"></th></tr></thead>
            <tbody id="flowParamBody">
              <tr><td><input class="fp-key" value="target_datasets" placeholder="英文标识"></td><td><input class="fp-val" value="pretrain_v3,posttrain_v2,custom_01"><div class="hint">支持多个, 英文逗号分隔</div></td><td><a href="#" onclick="wfDelFlowParam(this);return false;" style="color:#bfbfbf;">删</a></td></tr>
              <tr><td><input class="fp-key" value="tos_bucket" disabled></td><td><input class="fp-val" value="tos://embodied-datasets" disabled><div class="hint">系统内置, 只读</div></td><td><span style="color:#d9d9d9;cursor:not-allowed;">删</span></td></tr>
            </tbody>
          </table>
          <button class="btn" style="margin-top:12px;" onclick="wfAddFlowParam()">新增变量</button>
        </div>
        <div class="drawer-foot">
          <button class="btn" onclick="document.getElementById('flowParamDrawer').classList.remove('active')">取消</button>
          <button class="btn-primary btn" onclick="document.getElementById('flowParamDrawer').classList.remove('active');toast('Demo: 已保存流程参数')">保存</button>
        </div>
      </div>
    </div>

    <script>{WF_CANVAS_JS.replace("__NODES__", nodes_json).replace("__EDGES__", edges_json).replace("__FRAMES__", frames_json).replace("__OPS__", ops_json)}</script>
    """
    return render_page(name, content, active="pipelines",
                       breadcrumb=f'自动化任务 / 工作流管理 / <b>{name}</b>', extra_script=None)


@app.route("/runs")
def runs():
    # 执行记录: 每行 = 一次工作流执行实例 (一个工作流里可能含多个算子, 故不展开到算子)
    st_map = {"running": ("qa-warn", "运行中", ""), "done": ("qa-pass", "成功", ""),
              "failed": ("qa-fail", "失败", "fail")}
    pl_creator = {p["id"]: p["creator"] for p in PIPELINES}
    rows = ""
    for r in RUNS:
        cls, label, barcls = st_map[r["status"]]
        if r["trigger"] == "manual":
            trig = '<span class="tag tag-blue">手动触发</span>'
            by = r.get("by", "—")
        else:
            trig = '<span class="tag tag-gray">定时触发</span>'
            by = pl_creator.get(r["pipeline"], "—")
        rows += f"""<tr>
        <td style="font-family:monospace;font-size:12px;">{r['id']}</td>
        <td><b>{r['name']}</b></td>
        <td>{r['target']}</td>
        <td><span class="qa {cls}">{label}</span></td>
        <td>{trig}</td>
        <td>{by}</td>
        <td class="muted">{r['at']}</td>
        <td class="muted">{r['dur']}</td>
        <td class="actions-cell"><a href="#" onclick="toast('Demo: 查看工作流日志');return false;">日志</a> · <a href="#" onclick="toast('Demo: 重跑');return false;">重跑</a></td></tr>"""
    n_run = sum(1 for r in RUNS if r["status"] == "running")
    n_fail = sum(1 for r in RUNS if r["status"] == "failed")
    content = f"""
    <div class="filter-bar">
      <select class="has-value"><option value="">全部工作流</option><option>标准训练数据流水线</option><option>DAgger 数据流水线</option></select>
      <select class="has-value"><option value="">全部状态</option><option>成功</option><option>运行中</option><option>失败</option></select>
      <select class="has-value"><option value="">全部触发方式</option><option>手动触发</option><option>定时触发</option></select>
      <input placeholder="搜索工作流 / 产出数据集...">
      <button class="btn" onclick="resetFilters(this)">重置</button>
      <button class="btn-primary btn" onclick="queryFilters(this)">查询</button>
    </div>
    <div class="muted" style="margin-bottom:12px;">共 {len(RUNS)} 次执行 · 运行中 {n_run} · 失败 {n_fail} · 每行 = 一次工作流执行实例</div>
    <table class="ant-table">
      <thead><tr><th>实例 ID</th><th>工作流名称</th><th>产出数据集</th><th>状态</th><th>触发方式</th><th>触发人</th><th>开始时间</th><th>耗时</th><th>操作</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """
    return render_page("执行记录", content, active="runs", breadcrumb="自动化任务 / <b>执行记录</b>")


@app.route("/tags")
def tags():
    dims = TAG_SYSTEM["dimensions"]
    n_dim = len(dims)
    n_l2 = sum(len(d.get("leaves", d.get("groups", []))) for d in dims)
    n_l3 = sum(sum(len(g["items"]) for g in d.get("groups", [])) for d in dims)

    ops = ('<span class="tg-ops">'
           '<span onclick="toast(\'Demo: 复制\')" title="复制">&#10697;</span>'
           '<span onclick="toast(\'Demo: 编辑\')" title="编辑">&#9998;</span>'
           '<span class="del" onclick="toast(\'Demo: 删除\')" title="删除">&#128465;</span>'
           '</span>')

    def row(level, rid, parent, name, en, desc, child_count, has_children, expanded, visible):
        indent = 14 + level * 22
        if has_children:
            caret = (f'<span class="tg-caret {"open" if expanded else ""}" data-caret="{rid}" '
                     f'onclick="tgToggle(\'{rid}\')">&#9656;</span>')
        else:
            caret = '<span class="tg-caret-none"></span>'
        ncls = "tg-dim" if level == 0 else ("tg-l2" if level == 1 else "tg-l3")
        en_html = f'<span class="tg-en">{en}</span>' if en else ''
        badge = f'<span class="tg-badge">{child_count}</span>' if has_children else ''
        disp = '' if visible else 'display:none;'
        return (f'<tr class="tg-row" data-id="{rid}" data-parent="{parent}" style="{disp}">'
                f'<td><div class="tg-name" style="padding-left:{indent}px;">{caret}'
                f'<span class="{ncls}">{name}</span>{en_html}</div></td>'
                f'<td class="muted">{desc or "—"}</td><td>{badge}</td><td>{ops}</td></tr>')

    rows = ""
    for i, d in enumerate(dims):
        did = f"d{i}"
        if "groups" in d:
            n_child = len(d["groups"])
        else:
            n_child = len(d["leaves"])
        # 维度行 (默认展开)
        rows += row(0, did, "", d["name"], d["en"], d["desc"], n_child, True, True, True)
        if "leaves" in d:
            for j, leaf in enumerate(d["leaves"]):
                rows += row(1, f"{did}-{j}", did, leaf, "", "", 0, False, False, True)
        else:
            for j, g in enumerate(d["groups"]):
                gid = f"{did}-{j}"
                # 类目行 (默认收起 -> 三级隐藏)
                rows += row(1, gid, did, g["category"], "", "", len(g["items"]), True, False, True)
                for k, it in enumerate(g["items"]):
                    rows += row(2, f"{gid}-{k}", gid, it, "", "", 0, False, False, False)

    content = f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
      <div class="muted">标签体系 v{TAG_SYSTEM['version']} · {n_dim} 个维度 · {n_l2} 个二级 · {n_l3} 个三级</div>
      <div style="display:flex;gap:8px;">
        <button class="btn" onclick="tgAll(true)">全部展开</button>
        <button class="btn" onclick="tgAll(false)">全部收起</button>
        <button class="btn-primary btn" onclick="toast('Demo: 新增维度')">新增维度</button>
      </div>
    </div>
    <table class="ant-table tg-table">
      <thead><tr><th>名称</th><th>描述</th><th>子项</th><th>操作</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """
    script = """<script>
    function tgCollapseDesc(id){
      document.querySelectorAll('[data-parent="'+id+'"]').forEach(function(r){
        r.style.display='none';
        var c=document.querySelector('[data-caret="'+r.getAttribute('data-id')+'"]'); if(c) c.classList.remove('open');
        tgCollapseDesc(r.getAttribute('data-id'));
      });
    }
    function tgToggle(id){
      var caret=document.querySelector('[data-caret="'+id+'"]');
      var expanded=caret.classList.toggle('open');
      document.querySelectorAll('[data-parent="'+id+'"]').forEach(function(r){
        if(expanded){ r.style.display=''; }
        else { tgCollapseDesc(id); }
      });
    }
    function tgAll(expand){
      document.querySelectorAll('.tg-caret').forEach(function(c){ c.classList.toggle('open', expand); });
      document.querySelectorAll('.tg-row').forEach(function(r){
        var p=r.getAttribute('data-parent');
        r.style.display = (expand || p==='') ? '' : 'none';
      });
    }
    </script>"""
    return render_page("标签管理", content, active="tags",
                       breadcrumb="资产 / <b>标签管理</b>", extra_script=script, top="asset")


# ════════════════════════════════════════════════════════════════
# Section 5: Main
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=False)
