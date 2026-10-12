"""Task-pool demo records and atomic state transitions, scoped to each node."""
from copy import deepcopy
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


class PoolConflict(ValueError):
    """Another session claimed or completed a record after the list was loaded."""

REJECTION_REASONS = ("视频缺失或损坏", "画面遮挡或模糊", "指令与采集动作不一致", "动作不完整", "重复数据", "其他")
PRETRAINING_TASKS = [
    {
        "id": task_id, "v2_only": True, "pool": pool_id,
        "task_name": f"预训练数据{node}任务", "processing_task": "20456",
        "project": "预训练采集", "user_group": group,
        "workbench": "质检工作台 v1.0", "flow": "预训练数据质检流程",
        "stage": "质检", "node": node, "priority": "P0", "count": 4, "processing": 2,
        "filters": [], "mistake_rules": ["采集动作不规范", "画面短暂遮挡"],
        "rejection_rules": list(REJECTION_REASONS[:-1]),
    }
    for task_id, pool_id, node, group in (
        ("WB-PRETRAINING-QC", "POOL-PRETRAINING-QC", "采集质检", "采集质检用户组"),
        ("WB-PRETRAINING-ACCEPTANCE", "POOL-PRETRAINING-ACCEPTANCE", "采集验收", "采集验收用户组"),
    )
]

def demo_records(task):
    instructions = (
        ("将方块放入收纳盒", "夹取桌面方块，将其完整放入收纳盒，最后松开夹爪。"),
        ("密封包装盒", "将包装盒盖合拢，沿边缘压紧，确认盒盖不会松开。"),
        ("整理桌面工具", "依次将桌面工具放入收纳袋，完成后封好袋口。"),
        ("将物品摆放到货架", "将桌面的物品逐个摆放到货架指定位置。"),
        ("擦拭桌面", "使用抹布擦拭桌面，覆盖整个工作区域。"),
        ("收纳线缆", "将线缆整理成圈并放入收纳盒，避免缠绕。"),
    )
    return [dict(
        id=str(7523785 + index), task_id=task["processing_task"],
        instruction=name, description=description,
        device=f"UDAS-{309 + index:05d}-{1511 + index}",
        supplier="宁波博登智能科技有限公司" if index % 2 == 0 else "千寻智能",
        collector=("郭文静", "李燕", "刘立斌", "张龙龙", "周宇帆", "柳少龙")[index],
        collected_at=f"2026-09-30 {9 + index:02d}:20:00",
        supplier_id="SUP-001" if index % 2 == 0 else "SUP-003",
        self_check_result="合格" if index < 4 else "未自检",
        self_checker="李奕冲" if index < 4 else "",
        self_checker_supplier_id="SUP-003" if index < 4 else "",
        reviewer_supplier_id="SUP-003",
        self_checked_at=f"2026-10-01 {9 + index:02d}:30:00" if index < 4 else "",
        standard="自动质检 V4 · 家庭目标态",
        auto_result="操作失误" if index % 3 == 0 else "合格",
        auto_reason="画面短暂遮挡" if index % 3 == 0 else "—",
        operators={"采集人": ("郭文静", "李燕", "刘立斌", "张龙龙", "周宇帆", "柳少龙")[index],
                   "质检人": "李奕冲", "验收人": "张苗苗"},
        status="processing" if index < 2 else "pending",
    ) for index, (name, description) in enumerate(instructions)]

def pool_records(task, saved):
    records = demo_records(task)
    states = saved.get(task["pool"] + ":" + task["id"], {})
    for record in records:
        record.update(states.get(record["id"], {}))
    return sorted(records, key=lambda item: item["status"] != "processing")

def transition(task, saved, action, ids, result="", reason="", remark="", owner=None, reasons=None):
    """Validate the entire request before changing any record."""
    if not isinstance(ids, list) or not ids or len(ids) != len(set(map(str, ids))):
        raise ValueError("请选择有效且不重复的数据")
    records = {item["id"]: item for item in pool_records(task, saved)}
    if any(not isinstance(item, str) or item not in records for item in ids):
        raise ValueError("数据不属于当前任务池")
    if owner and any(records[item].get("owner") not in (None, "", owner) for item in ids):
        raise PoolConflict("数据已被其他人占用或处理，无法继续操作，请选择其他数据")
    if action == "start":
        if any(records[item]["status"] == "completed" for item in ids):
            raise ValueError("数据已经处理完成，请刷新列表")
        changes = {item: {"status": "processing"} for item in ids}
    elif action == "finish":
        if len(ids) != 1 or records[ids[0]]["status"] != "processing":
            raise ValueError("仅可提交正在处理的数据，请刷新列表")
        if result not in ("合格", "不合格"):
            raise ValueError("请选择有效结论")
        selected_reasons = reasons if reasons is not None else ([reason] if reason else [])
        if result == "不合格" and (
            not isinstance(selected_reasons, list) or not selected_reasons
            or any(not isinstance(item, str) or item not in REJECTION_REASONS for item in selected_reasons)
            or len(selected_reasons) != len(set(selected_reasons))
        ):
            raise ValueError("请选择有效且不重复的不合格原因")
        selected_reasons = selected_reasons if result == "不合格" else []
        changes = {ids[0]: {"status": "completed", "result": result,
                           "reasons": selected_reasons, "reason": "、".join(selected_reasons),
                           "reviewed_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(sep=" ", timespec="seconds"),
                           "remark": remark.strip() if result == "不合格" else ""}}
    else:
        raise ValueError("无效操作")
    if owner:
        for change in changes.values():
            change["owner"] = owner
    updated = deepcopy(saved)
    updated.setdefault(task["pool"] + ":" + task["id"], {}).update(changes)
    return updated


@contextmanager
def shared_state(path, task, legacy, owner):
    """Serialize claims across browser sessions and server workers; retain old demo drafts."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    scope = task["pool"] + ":" + task["id"]
    with sqlite3.connect(path, timeout=10) as db:
        db.execute("CREATE TABLE IF NOT EXISTS pool_states (scope TEXT PRIMARY KEY, state TEXT NOT NULL)")
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT state FROM pool_states WHERE scope=?", (scope,)).fetchone()
        state = json.loads(row[0]) if row else {}
        for record_id, change in legacy.get(scope, {}).items():
            if record_id not in state:
                state[record_id] = dict(change, owner=owner)
        saved = {scope: state}
        yield saved
        db.execute("INSERT OR REPLACE INTO pool_states VALUES (?, ?)", (scope, json.dumps(saved[scope])))


def shared_records(path, task, legacy, owner):
    with shared_state(path, task, legacy, owner) as saved:
        return pool_records(task, saved)


def shared_transition(path, task, legacy, owner, action, ids, result="", reason="", remark="", reasons=None):
    with shared_state(path, task, legacy, owner) as saved:
        updated = transition(task, saved, action, ids, result, reason, remark, owner, reasons)
        saved.update(updated)
        return pool_records(task, updated)


def public_records(records, owner):
    return [dict({key: value for key, value in item.items() if key != "owner"},
                 occupied=bool(item.get("owner") and item["owner"] != owner)) for item in records]
