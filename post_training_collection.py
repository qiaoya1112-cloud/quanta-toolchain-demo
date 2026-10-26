"""Local-only post-training collection demo; no production or device calls.

Task configuration is stored independently from the existing S026 workflow.
Recording facts are simulated fixtures; closing collection never changes them.
"""
import copy
import json
import hashlib
import math
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
from urllib.parse import urlparse, urlunparse
import re
import uuid

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request

BASE = "/data/post-training-collection"
API = "/api/post-training-collection"
USER = "joanna"
DEMO_PEOPLE = ["joanna", "ben", "tina", "leo", "lisa"]
DEMO_PROJECTS = [
    {"id": "PRJ-LIANGJIAN", "name": "亮剑"},
    {"id": "PRJ-MOZ1-SFT-07", "name": "demo采集"},
    {"id": "PRJ-MOZ2-PRE-03", "name": "预训练"},
    {"id": "PRJ-POST-TRAINING", "name": "后训练"},
    {"id": "PRJ-EVAL-GEN-02", "name": "宁德时代"},
    {"id": "PRJ-JD", "name": "京东项目"},
]
PROMPTS = [
    {"id": "demo-prompt-pick-cup", "version": "v2", "name": "拿取杯子并放入托盘", "text": "Pick up the cup from the marked area and place it upright in the tray.", "scene": "桌面操作"},
    {"id": "demo-prompt-drink", "version": "v3", "name": "取出饮料并放到桌面", "text": "Open the refrigerator, take out the beverage and place it on the marked area of the table.", "scene": "厨房操作"},
    {"id": "demo-prompt-whiteboard", "version": "v1", "name": "擦净白板并归还板擦", "text": "Wipe the marked area of the whiteboard clean, then return the eraser to the tray.", "scene": "办公场景"},
    {"id": "demo-prompt-tidy", "version": "v2", "name": "整理桌面物品", "text": "Place each item on the desk into its designated storage tray.", "scene": "桌面操作"},
    {"id": "demo-prompt-drawer", "version": "v1", "name": "打开抽屉并取出物品", "text": "Open the drawer, take out the object and place it in the tray, then close the drawer.", "scene": "家居操作"},
]
OPERATORS = [
    {"id": "demo-left-close@1", "name": "左臂夹爪闭合取点", "arm": "left", "event": "close"},
    {"id": "demo-left-open@1", "name": "左臂夹爪打开取点", "arm": "left", "event": "open"},
    {"id": "demo-right-close@1", "name": "右臂夹爪闭合取点", "arm": "right", "event": "close"},
    {"id": "demo-right-open@1", "name": "右臂夹爪打开取点", "arm": "right", "event": "open"},
]


def now():
    return datetime.now().replace(microsecond=0).isoformat()


def seed_tasks(projects, checkpoints):
    """Synthetic fixtures with aggregate metrics calculated from their records."""
    project_ids = [p["id"] for p in projects]
    ckpt = next((c["id"] for c in checkpoints if c.get("status") == "cached"), checkpoints[0]["id"])
    specs = [
        ("DC-2601", "饮茶场景 · 饮料取放遥操采集", "robot", "NORMAL", 0, 16, 2),
        ("DC-2602", "桌面杯子抓取 · DAGGER 补采", "robot", "DAGGER", 0, 12, 1),
        ("DC-2603", "白板清洁 · 遥操动作采集", "robot", "NORMAL", 0, 10, 78),
        ("DC-2604", "桌面物品整理 · DAGGER 采集", "robot", "DAGGER", 0, 8, 6),
        ("DC-2605", "抽屉取物 · 遥操补采", "robot", "NORMAL", 0, 0, None),
        ("DC-2606", "厨房收纳 · 遥操采集", "robot", "NORMAL", 0, 14, 48),
        ("DC-2607", "家庭厨房 · 饮料取放采集", "udas", "", 0, 14, 3),
        ("DC-2608", "仓储货架 · 物品搬运采集", "udas", "", min(1, len(project_ids)-1), 12, 76),
        ("DC-2609", "办公室 · 桌面整理采集", "udas", "", 0, 9, 7),
        ("DC-2610", "家庭客厅 · 物品收纳采集", "udas", "", 0, 0, None),
    ]
    result = []
    for index, (tid, name, source, mode, project_index, count, hours) in enumerate(specs):
        created = (datetime.now() - timedelta(days=7 + index)).replace(microsecond=0).isoformat()
        closed = tid == "DC-2606"
        prompts = [copy.deepcopy(PROMPTS[0 if tid == "DC-2602" else 3])] if mode == "DAGGER" else []
        records = []
        for i in range(count):
            stamp = (datetime.now() - timedelta(hours=hours or 0, minutes=i * 12)).replace(microsecond=0).isoformat()
            records.append({
                "id": f"DEMO-R-{index + 1:02d}{i + 1:04d}", "task_id": tid,
                "operator": DEMO_PEOPLE[i % len(DEMO_PEOPLE)],
                "device": f'{"UDAS" if source == "udas" else "MOZ1"}-{i % 2 + 1:03d}',
                "recorded_at": stamp, "seconds": 110 + i * 17 if source == "udas" else 35 + i * 5,
                "upload": "uploading" if i == count-1 and not closed else "uploaded",
                "collection_result": ["success", "success", "failure", "success", None][i % 5],
                "quality": ["pending", "processing", "passed", "passed", "rejected"][i % 5],
                "annotation": "已标注" if i % 5 in (2, 3) else "未标注",
                "prompt": copy.deepcopy(prompts[0]) if prompts else None,
                "checkpoint": str(ckpt) if mode == "DAGGER" else "",
            })
        description = ("采集规范约定的取放动作，覆盖不同物品位置和左右手操作。\n"
                       "开始前确认摆场；物品稳定放入目标区域后结束单条录制，并复位。\n"
                       "掉落、碰撞等异常按现场要求记录，避免重复上传。")
        result.append({
            "id": tid, "name": name, "project": project_ids[project_index], "source": source, "mode": mode,
            "description": description, "spec_url": "", "tags": ["补采"] if "补采" in name else ["场景采集"],
            "location": "北京 · 家居采集场" if source == "udas" else "",
            "prompts": prompts, "checkpoint": str(ckpt) if mode == "DAGGER" else "", "generalization": [],
            "status": "closed" if closed else "open", "creator": DEMO_PEOPLE[index % len(DEMO_PEOPLE)],
            "created_at": created, "updated_at": created,
            "revision": 1, "records": records,
            "events": [{"at": created, "actor": DEMO_PEOPLE[index % len(DEMO_PEOPLE)], "title": "创建采集任务", "detail": "已生成任务 ID，可分享采集要求。"}],
        })
    return result


@contextmanager
def database():
    path = Path(current_app.config["COLLECTION_DEMO_DB"])
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS collection_tasks (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS collection_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS collection_task_aliases (legacy_id TEXT PRIMARY KEY, task_id TEXT NOT NULL)")
        # 【新】同一次创建重试不重复生成开放任务；与任务写入同一事务提交。
        conn.execute("CREATE TABLE IF NOT EXISTS collection_create_requests (actor TEXT NOT NULL, request_key TEXT NOT NULL, fingerprint TEXT NOT NULL, task_id TEXT NOT NULL, PRIMARY KEY(actor, request_key))")
        conn.execute("CREATE TABLE IF NOT EXISTS collection_specs (id TEXT PRIMARY KEY, document_key TEXT UNIQUE NOT NULL, payload TEXT NOT NULL)")
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            if not conn.execute("SELECT 1 FROM collection_meta WHERE key='seeded'").fetchone():
                for task in seed_tasks(current_app.config["COLLECTION_PROJECTS"], current_app.config["COLLECTION_CHECKPOINTS"]):
                    conn.execute("INSERT INTO collection_tasks VALUES (?, ?)", (task["id"], json.dumps(task, ensure_ascii=False)))
                conn.execute("INSERT INTO collection_meta VALUES ('seeded', '1')")
            if not conn.execute("SELECT 1 FROM collection_meta WHERE key='five_digit_ids'").fetchone():
                migrate_task_ids(conn)
                conn.execute("INSERT INTO collection_meta VALUES ('five_digit_ids', '1')")
            if not conn.execute("SELECT 1 FROM collection_meta WHERE key='spec_catalog'").fetchone():
                for row in conn.execute("SELECT id, payload FROM collection_tasks").fetchall():
                    task = json.loads(row['payload'])
                    if document_identity(task.get('spec_url', '')):
                        bind_spec(conn, task)
                        conn.execute("UPDATE collection_tasks SET payload=? WHERE id=?", (json.dumps(task, ensure_ascii=False), row['id']))
                conn.execute("INSERT INTO collection_meta VALUES ('spec_catalog', '1')")
        yield conn
    finally:
        conn.close()


def is_task_id(value):
    return len(value) == 5 and value.isascii() and value.isdigit()


def migrate_task_ids(conn):
    """Keep task contents and row order while retaining old links as aliases."""
    rows = conn.execute("SELECT id, payload FROM collection_tasks ORDER BY rowid").fetchall()
    used = {row["id"] for row in rows if is_task_id(row["id"])}
    legacy_numbers = [int(row["id"][3:]) for row in rows if row["id"].startswith("DC-")
                      and row["id"][3:].isascii() and row["id"][3:].isdigit()
                      and 0 <= int(row["id"][3:]) <= 99999]
    next_number = max([2600, *legacy_numbers, *(int(value) for value in used)]) + 1
    for row in rows:
        old_id = row["id"]
        if is_task_id(old_id):
            continue
        candidate = old_id[3:].zfill(5) if old_id.startswith("DC-") and old_id[3:].isascii() and old_id[3:].isdigit() else ""
        if not is_task_id(candidate) or candidate in used:
            while f"{next_number:05d}" in used:
                next_number += 1
            if next_number > 99999:
                raise ValueError("五位任务编号已用完")
            candidate = f"{next_number:05d}"
            next_number += 1
        task = json.loads(row["payload"])
        task["id"] = candidate
        for record in task.get("records", []):
            record["task_id"] = candidate
        conn.execute("UPDATE collection_tasks SET id=?, payload=? WHERE id=?",
                     (candidate, json.dumps(task, ensure_ascii=False), old_id))
        conn.execute("INSERT INTO collection_task_aliases VALUES (?, ?)", (old_id, candidate))
        used.add(candidate)
    conn.execute("INSERT OR REPLACE INTO collection_meta VALUES ('next_task_id', ?)",
                 (str(max([2600, *(int(value) for value in used)]) + 1),))


def get_task(conn, task_id):
    row = conn.execute("SELECT payload FROM collection_tasks WHERE id=?", (task_id,)).fetchone()
    if row is None:
        row = conn.execute("SELECT payload FROM collection_tasks JOIN collection_task_aliases "
                           "ON collection_tasks.id=collection_task_aliases.task_id WHERE legacy_id=?", (task_id,)).fetchone()
    if row is None:
        abort(404, description="任务不存在或已不可访问")
    task = json.loads(row["payload"])
    task.setdefault("priority", 6)
    task.setdefault("expected_hours", None)
    task.setdefault("spec_id", "")
    task.setdefault("spec_name", "")
    return task


def document_identity(value):
    """Deduplicate document URLs without fetching Feishu or persisting share queries."""
    try:
        url = urlparse(value)
        host = (url.hostname or '').lower()
        match = re.fullmatch(r'/(docx|wiki)/([A-Za-z0-9]+)/?', url.path)
        if url.scheme != 'https' or url.username or url.password or url.port or not match:
            return None
        if not any(host == domain or host.endswith('.' + domain) for domain in ('feishu.cn', 'larksuite.com')):
            return None
        clean = urlunparse(('https', host, '/' + match[1] + '/' + match[2], '', '', ''))
        return match[1] + ':' + match[2], clean
    except (ValueError, TypeError):
        return None


def bind_spec(conn, data):
    """Called only inside a successful task write transaction."""
    identity = document_identity(data.get('spec_url', ''))
    if not identity:
        data.update(spec_id='', spec_name='')
        return
    row = conn.execute('SELECT payload FROM collection_specs WHERE document_key=?', (identity[0],)).fetchone()
    if row:
        spec = json.loads(row['payload'])
    else:
        spec = dict(id=uuid.uuid4().hex, name=data.get('spec_name') or data['name'] + ' · 采集规范',
                    url=identity[1], creator=USER, created_at=now(), updated_at=now(), revision=1)
        conn.execute('INSERT INTO collection_specs VALUES (?, ?, ?)', (spec['id'], identity[0], json.dumps(spec, ensure_ascii=False)))
    data.update(spec_id=spec['id'], spec_name=spec['name'], spec_url=spec['url'])


def resolve_spec(conn, body):
    if not isinstance(body, dict) or not body.get('spec_id'):
        return body, {}
    if not isinstance(body['spec_id'], str):
        return body, {'spec_url': '请选择有效的采集规范'}
    row = conn.execute('SELECT payload FROM collection_specs WHERE id=?', (body['spec_id'],)).fetchone()
    if not row:
        return body, {'spec_url': '采集规范不存在，请重新选择'}
    spec = json.loads(row['payload'])
    if body.get('spec_url') and body['spec_url'] != spec['url']:
        return body, {'spec_url': '规范链接已更新，请重新选择规范'}
    return {**body, 'spec_url': spec['url'], 'spec_name': spec['name']}, {}


def task_metrics(task):
    records = task["records"]
    uploaded = [r for r in records if r["upload"] == "uploaded"]
    failed = [r for r in records if r.get("upload") == "failed"]
    uploading = [r for r in records if r.get("upload") == "uploading"]
    latest = max((r["recorded_at"] for r in records), default=None)
    # 【新】重开从本次开放重新计时；旧任务从现有重开日志兼容读取。
    opened = max([task["created_at"], *[e["at"] for e in task.get("events", [])
                  if e.get("title") == "重新开放采集" and e.get("at")]])
    stale = max(opened, latest) if latest else opened
    needs_review = task["status"] == "open" and datetime.now() - datetime.fromisoformat(stale) >= timedelta(hours=48)
    return {"uploaded": len(uploaded), "uploading": len(uploading), "upload_failed": len(failed),
            "seconds": sum(r["seconds"] for r in uploaded), "latest": latest, "needs_review": needs_review,
            "review_since": stale, "review_due_at": (datetime.fromisoformat(stale) + timedelta(hours=48)).isoformat(),
            "pending": sum(r["quality"] == "pending" for r in uploaded),
            "processing": sum(r["quality"] == "processing" for r in uploaded),
            "passed": sum(r["quality"] == "passed" for r in uploaded),
            "rejected": sum(r["quality"] == "rejected" for r in uploaded)}


def public_task(task, detail=False):
    result = copy.deepcopy(task)
    for key, default in [('priority', 6), ('expected_hours', None), ('spec_id', ''), ('spec_name', '')]:
        result.setdefault(key, default)
    # 【新】一期只提供修改日志；旧库版本快照原样保留，不作为当前产品能力返回。
    result.pop("config_version", None)
    result.pop("config_history", None)
    if detail:
        for record in result.get("records", []):
            record.pop("config_version", None)
            if "collection_result" not in record and "is_mistake" not in record and record.get("id", "").startswith("DEMO-R-"):
                try:
                    index = int(record["id"][-4:]) - 1
                    record["collection_result"] = ["success", "success", "failure", "success", None][index % 5]
                except ValueError:
                    pass
    result["metrics"] = task_metrics(task)
    result.pop("followers", None)
    if not detail:
        result.pop("records")
        result.pop("events")
    return result


def validate_payload(body, existing=None):
    errors = {}
    if not isinstance(body, dict):
        return {}, {"form": "请求内容必须为对象"}
    if existing:
        fixed = {key: copy.deepcopy(existing[key]) for key in
                 ("name", "project", "source", "mode", "location", "checkpoint")}
        fixed["prompt_ids"] = [p["id"] for p in existing["prompts"]]
        fixed["prompts"] = copy.deepcopy(existing["prompts"])
        for key, value in fixed.items():
            incoming = body.get(key, value)
            if isinstance(incoming, str):
                incoming = incoming.strip()
            if incoming != value:
                errors["prompts" if key == "prompt_ids" else key] = "此项创建后不可修改，请复制创建新任务"
        editable = {key: copy.deepcopy(existing.get(key, '' if key.startswith('spec_') else None)) for key in
                    ("description", "spec_url", "spec_id", "spec_name", "tags", "generalization", "priority", "expected_hours")}
        editable['priority'] = existing.get('priority', 6)
        allowed = set(fixed) | set(editable) | {"revision"}
        if set(body) - allowed:
            errors["form"] = "仅支持修改优先级、预期采集时长、采集规范、位置泛化统计、标签和任务说明"
        body = {**fixed, **editable, **body}
    def text(key, maximum, required=False):
        value = body.get(key, "")
        if not isinstance(value, str):
            errors[key] = "请输入文字"
            return ""
        value = value.strip()
        if required and not value:
            errors[key] = "请填写此项"
        if len(value) > maximum:
            errors[key] = f"最多 {maximum} 个字符"
        return value
    data = {"name": text("name", 100, True), "project": text("project", 120, True),
            "source": text("source", 16, True), "mode": text("mode", 16),
            "description": text("description", 5000, True), "spec_url": text("spec_url", 2048),
            "location": text("location", 200), "checkpoint": text("checkpoint", 120)}
    data.update(spec_id=text('spec_id', 64), spec_name=text('spec_name', 160))
    priority = body.get('priority', 3)
    if type(priority) is not int or not 1 <= priority <= 9:
        errors['priority'] = '请选择高、中或低的优先级'
    data['priority'] = priority
    expected = body.get('expected_hours')
    if expected == '':
        expected = None
    if expected is not None and (isinstance(expected, bool) or not isinstance(expected, (int, float)) or not math.isfinite(expected) or expected <= 0 or expected > 1000000):
        errors['expected_hours'] = '请输入大于 0、不超过 1000000 的小时数'
    data['expected_hours'] = expected
    projects = current_app.config["COLLECTION_PROJECTS"]
    if data["project"] not in {p["id"] for p in projects}:
        errors["project"] = "请选择已有项目"
    if data["source"] not in ("udas", "robot"):
        errors["source"] = "请选择 UDAS 或机器人采集"
    if data["source"] == "robot" and data["mode"] not in ("NORMAL", "DAGGER"):
        errors["mode"] = "请选择机器人采集模式"
    if data["spec_url"]:
        if not document_identity(data['spec_url']) and (not existing or data['spec_url'] != existing.get('spec_url')):
            errors['spec_url'] = '请填写飞书文档或知识库的 https 链接'
        try:
            url = urlparse(data["spec_url"])
            if url.scheme not in ("https", "http") or not url.netloc or url.username or url.password:
                raise ValueError()
        except ValueError:
            errors["spec_url"] = "请填写有效的 http / https 规范链接"
    tags = body.get("tags", [])
    if not isinstance(tags, list) or len(tags) > 8 or any(not isinstance(t, str) or not t.strip() or len(t) > 20 for t in tags):
        errors["tags"] = "最多 8 个标签，每个 1—20 字"
        tags = []
    data["tags"] = list(dict.fromkeys(t.strip() for t in tags))
    data["prompts"] = []
    if data["source"] == "robot" and data["mode"] == "DAGGER":
        refs = body.get("prompt_ids", [])
        if not isinstance(refs, list) or not refs or any(not isinstance(p, str) for p in refs):
            errors["prompts"] = "请选择至少一条模型 Prompt"
        else:
            prompts = {p["id"]: p for p in (existing["prompts"] if existing else PROMPTS)}
            if any(p not in prompts for p in refs):
                errors["prompts"] = "Prompt 不存在，请重新选择"
            else:
                data["prompts"] = [copy.deepcopy(prompts[p]) for p in dict.fromkeys(refs)]
        if not existing and data["checkpoint"] not in {str(c["id"]) for c in current_app.config["COLLECTION_CHECKPOINTS"] if c.get("status") == "cached"}:
            errors["checkpoint"] = "请选择可用的 Checkpoint"
    else:
        data["checkpoint"] = ""
    if data["source"] == "udas":
        data["mode"] = ""
    else:
        data["location"] = ""
    data["generalization"] = []
    configs = body.get("generalization", []) if data["source"] == "robot" else []
    if not isinstance(configs, list) or len(configs) > 20:
        configs = []
        errors["generalization"] = "统计项格式无效或超过 20 项"
    used_prompts = set()
    for item in configs:
        if not isinstance(item, dict):
            errors["generalization"] = "统计项格式无效"
            continue
        g = {k: item.get(k, "") for k in ("name", "prompt_id", "arm", "event", "operator", "plane")}
        if any(not isinstance(v, str) for v in g.values()):
            errors["generalization"] = "统计项配置格式无效"
            continue
        if data["mode"] == "DAGGER":
            if g["prompt_id"] not in {p["id"] for p in data["prompts"]} or g["prompt_id"] in used_prompts:
                errors["generalization"] = "每个已选 Prompt 最多配置一个统计项"
            used_prompts.add(g["prompt_id"])
            g["name"] = next((p["name"] for p in data["prompts"] if p["id"] == g["prompt_id"]), "")
        elif not g["name"].strip() or len(g["name"]) > 80:
            errors["generalization"] = "请填写统计项名称（最多 80 字）"
        if data["mode"] != "DAGGER":
            g["prompt_id"] = ""
        if not any(op["id"] == g["operator"] and op["arm"] == g["arm"] and op["event"] == g["event"] for op in OPERATORS):
            errors["generalization"] = "请选择与对象和事件匹配的算子"
        if g["plane"] not in ("XY", "XZ", "YZ", "XYZ"):
            errors["generalization"] = "请选择统计维度"
        bounds = item.get("bounds", {})
        g["bounds"] = {}
        try:
            for axis in g["plane"]:
                pair = bounds[axis]
                if not isinstance(pair, list) or len(pair) != 2 or any(isinstance(v, bool) or not isinstance(v, (float, int)) for v in pair):
                    raise ValueError()
                low, high = pair
                if not math.isfinite(low) or not math.isfinite(high) or low >= high:
                    raise ValueError()
                g["bounds"][axis] = [low, high]
        except (KeyError, TypeError, ValueError):
            errors["generalization"] = "请填写参与轴的有效上下界，最小值必须小于最大值"
        g["allow_adjust"] = item.get("allow_adjust", True) is True
        data["generalization"].append(g)
    if existing and existing["records"] and (data["source"], data["mode"]) != (existing["source"], existing["mode"]):
        errors["source"] = "已有录制数据，变更采集方式请复制新建任务"
    return data, errors


def register_collection(app, render_page, projects, checkpoints):
    app.config.setdefault("COLLECTION_DEMO_DB", os.environ.get("COLLECTION_DEMO_DB", str(Path(app.root_path) / "instance" / "post-training-collection.sqlite3")))
    app.config["COLLECTION_PROJECTS"] = copy.deepcopy(projects)
    app.config["COLLECTION_CHECKPOINTS"] = copy.deepcopy(checkpoints)
    bp = Blueprint("post_training_collection", __name__)

    @bp.errorhandler(404)
    def not_found(error):
        if request.path.startswith(API):
            return jsonify(error=error.description), 404
        return render_page("任务不存在", '<section style="padding:40px"><h2>任务不存在或已不可访问</h2><a href="'+BASE+'">返回数据采集</a></section>', active=BASE, module="data"), 404

    @bp.get(BASE)
    @bp.get(BASE + "/new")
    @bp.get(BASE + "/<task_id>")
    @bp.get(BASE + "/<task_id>/edit")
    def page(task_id=None):
        if task_id:
            with database() as conn:
                canonical_id = get_task(conn, task_id)["id"]
            if task_id != canonical_id:
                target = BASE + "/" + canonical_id + ("/edit" if request.path.endswith("/edit") else "")
                if request.query_string:
                    target += "?" + request.query_string.decode("ascii")
                return redirect(target, code=302)
        bootstrap = {"base": BASE, "api": API, "user": USER,
                     "projects": [{"id": p["id"], "name": p["name"]} for p in projects],
                     "checkpoints": [{"id": str(c["id"]), "name": c["name"], "status": c["status"]} for c in checkpoints],
                     "prompts": PROMPTS, "operators": OPERATORS}
        content = render_template("post_training_collection/page.html", bootstrap=bootstrap)
        return render_page("数据采集", content, active=BASE, module="data", breadcrumb='数据平台 / <a href="'+BASE+'">数据采集</a>', mvp_note=None)

    @bp.get(API + "/tasks")
    def list_tasks():
        with database() as conn:
            tasks = [public_task(json.loads(row["payload"])) for row in conn.execute("SELECT payload FROM collection_tasks ORDER BY rowid DESC")]
        return jsonify(tasks=tasks)

    # 【新】采集规范与处理规则分开管理；这里只保存名称和飞书链接。
    @bp.get(API + '/specs')
    def list_specs():
        with database() as conn:
            tasks = [json.loads(r['payload']) for r in conn.execute('SELECT payload FROM collection_tasks')]
            specs = [json.loads(r['payload']) for r in conn.execute('SELECT payload FROM collection_specs ORDER BY rowid DESC')]
            for spec in specs:
                spec['task_count'] = sum(t.get('spec_id') == spec['id'] for t in tasks)
        return jsonify(specs=specs)

    @bp.post(API + '/specs')
    @bp.patch(API + '/specs/<spec_id>')
    def save_spec(spec_id=None):
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error='请求内容无效'), 422
        name, url = body.get('name'), body.get('url')
        errors = {}
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 160:
            errors['name'] = '请填写规范名称，最多 160 字'
        identity = document_identity(url) if isinstance(url, str) and len(url) <= 2048 else None
        if not identity:
            errors['url'] = '请填写飞书文档或知识库的 https 链接'
        if errors:
            return jsonify(errors=errors), 422
        with database() as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            duplicate = conn.execute('SELECT id FROM collection_specs WHERE document_key=?', (identity[0],)).fetchone()
            if duplicate and duplicate['id'] != spec_id:
                return jsonify(error='该文档已在规范库中，请使用已有规范'), 409
            old = None
            if spec_id:
                row = conn.execute('SELECT payload FROM collection_specs WHERE id=?', (spec_id,)).fetchone()
                if not row:
                    abort(404, description='规范不存在')
                old = json.loads(row['payload'])
                if type(body.get('revision')) is not int or body['revision'] != old['revision']:
                    return jsonify(error='规范已被更新，请刷新后重试'), 409
                if old['name'] == name.strip() and old['url'] == identity[1]:
                    return jsonify(spec=old, unchanged=True)
            stamp = now()
            spec = dict(old or dict(id=uuid.uuid4().hex, creator=USER, created_at=stamp),
                        name=name.strip(), url=identity[1], updated_at=stamp, revision=(old['revision'] + 1 if old else 1))
            if old:
                conn.execute('UPDATE collection_specs SET document_key=?, payload=? WHERE id=?', (identity[0], json.dumps(spec, ensure_ascii=False), spec_id))
                for row in conn.execute('SELECT id, payload FROM collection_tasks').fetchall():
                    task = json.loads(row['payload'])
                    if task.get('spec_id') != spec_id:
                        continue
                    changes = [{'field': key, 'label': label, 'before': task.get(key, ''), 'after': spec[source]}
                               for key, label, source in [('spec_name', '规范名称', 'name'), ('spec_url', '采集规范', 'url')]
                               if task.get(key, '') != spec[source]]
                    task.update(spec_name=spec['name'], spec_url=spec['url'], updated_at=stamp, revision=task['revision'] + 1)
                    task['events'].append(dict(at=stamp, actor=USER, title='更新采集规范', detail='规则管理更新了关联规范。', changes=changes))
                    conn.execute('UPDATE collection_tasks SET payload=? WHERE id=?', (json.dumps(task, ensure_ascii=False), task['id']))
            else:
                conn.execute('INSERT INTO collection_specs VALUES (?, ?, ?)', (spec['id'], identity[0], json.dumps(spec, ensure_ascii=False)))
        return jsonify(spec=spec), 200 if old else 201

    @bp.get(API + "/tasks/<task_id>")
    def detail(task_id):
        with database() as conn:
            return jsonify(task=public_task(get_task(conn, task_id), detail=True))

    @bp.post(API + "/tasks")
    def create():
        body = request.get_json(silent=True)
        request_key = request.headers.get("Idempotency-Key", "")
        if request_key and (len(request_key) > 128 or not request_key.isascii() or not all(c.isalnum() or c in "-_:" for c in request_key)):
            return jsonify(error="创建请求标识无效，请重新打开创建页"), 400
        fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        with database() as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            if request_key:
                previous = conn.execute("SELECT fingerprint, task_id FROM collection_create_requests WHERE actor=? AND request_key=?", (USER, request_key)).fetchone()
                if previous:
                    if previous["fingerprint"] != fingerprint:
                        return jsonify(error="本次创建请求已成功，内容与原请求不同，请先核对已创建的任务", task_id=previous["task_id"]), 409
                    return jsonify(task=public_task(get_task(conn, previous["task_id"]), True), replayed=True), 200
            resolved, errors = resolve_spec(conn, body)
            data, validation_errors = validate_payload(resolved)
            errors.update(validation_errors)
            if errors:
                return jsonify(errors=errors), 422
            stamp = now()
            data.update(status="open", creator=USER, created_at=stamp, updated_at=stamp,
                        revision=1, records=[], events=[{"at": stamp, "actor": USER, "title": "创建采集任务", "detail": "已生成任务 ID，等待采集。"}])
            number = int(conn.execute("SELECT value FROM collection_meta WHERE key='next_task_id'").fetchone()["value"])
            if number > 99999:
                return jsonify(error="五位任务编号已用完，无法创建新任务"), 409
            data["id"] = f"{number:05d}"
            bind_spec(conn, data)
            conn.execute("INSERT INTO collection_tasks VALUES (?, ?)", (data["id"], json.dumps(data, ensure_ascii=False)))
            conn.execute("UPDATE collection_meta SET value=? WHERE key='next_task_id'", (str(number + 1),))
            if request_key:
                conn.execute("INSERT INTO collection_create_requests VALUES (?, ?, ?, ?)", (USER, request_key, fingerprint, data["id"]))
        return jsonify(task=public_task(data, True)), 201

    @bp.get(API + "/tasks/<task_id>/collection-check")
    def collection_check(task_id):
        """Read-only preflight contract; real recording clients must check at start.

        A successful check is not a recording permit or a reserved session. No
        device is connected by this demo, and the returned task is a snapshot.
        """
        with database() as conn:
            task = get_task(conn, task_id)
        # 兼容历史卡片URL，但不再根据其版本参数拦截；始终读取最新任务与开关状态。
        reason = "closed" if task["status"] != "open" else "ready"
        response = jsonify(can_start=reason == "ready", reason=reason,
                           checked_at=now(), task=public_task(task, True))
        response.headers["Cache-Control"] = "no-store"
        return response

    def recording_payload(body, stamp):
        """Validate the small recording-start contract used by the local demo."""
        if not isinstance(body, dict):
            return None, {"form": "请求内容必须为对象"}
        record_id = body.get("record_id", body.get("id", ""))
        if not isinstance(record_id, str) or not record_id.strip() or len(record_id.strip()) > 128:
            return None, {"record_id": "请提供有效的 Recording ID"}
        record_id = record_id.strip()
        if any(ord(char) < 32 or ord(char) == 127 or char in "/\\?#" for char in record_id):
            return None, {"record_id": "Recording ID 包含无效字符"}
        recorded_at = body.get("recorded_at", stamp)
        if not isinstance(recorded_at, str):
            return None, {"recorded_at": "录制时间无效"}
        try:
            parsed = datetime.fromisoformat(recorded_at)
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone().replace(tzinfo=None)
            if parsed > datetime.fromisoformat(stamp) + timedelta(minutes=5):
                raise ValueError()
            recorded_at = parsed.isoformat()
        except ValueError:
            return None, {"recorded_at": "录制时间无效"}
        seconds = body.get("seconds", 0)
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
            return None, {"seconds": "录制时长无效"}
        operator = body.get("operator", "")
        device = body.get("device", "")
        if not isinstance(operator, str) or len(operator) > 120 or not isinstance(device, str) or len(device) > 120:
            return None, {"operator": "采集员或设备信息无效"}
        return {"id": record_id, "recorded_at": recorded_at, "seconds": seconds,
                "operator": operator.strip() or "未填写", "device": device.strip() or "未填写"}, {}

    @bp.post(API + "/tasks/<task_id>/recordings/start")
    def start_recording(task_id):
        """Admit a new recording only while the task is open.

        The returned upload session is the server's admission fact. Closing the
        task after this point does not invalidate the session.
        """
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(errors={"form": "请求内容必须为对象"}), 422
        stamp = now()
        with database() as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            task = get_task(conn, task_id)
            record, errors = recording_payload(body, now())
            if errors:
                return jsonify(errors=errors), 422
            existing = next((item for item in task["records"]
                             if item.get("id") == record["id"]), None)
            if existing:
                # Retry may recover an admitted session, never reassign its identity.
                for key in ("operator", "device", "recorded_at"):
                    if key in body and record[key] != existing.get(key):
                        return jsonify(error="Recording ID 已被其他录制信息使用", code="recording_conflict"), 409
                if "prompt_id" in body and body["prompt_id"] != (existing.get("prompt") or {}).get("id"):
                    return jsonify(error="Recording ID 对应的 Prompt 不一致", code="recording_conflict"), 409
                return jsonify(recording=copy.deepcopy(existing), task=public_task(task, True), replayed=True), 200
            if task["status"] != "open":
                response = jsonify(error="任务已结束，不能开始新的录制", code="task_closed", can_start=False,
                                   task=public_task(task, True))
                return response, 409
            stamp = now()
            prompts = task.get("prompts", [])
            prompt = None
            if prompts:
                prompt = next((p for p in prompts if p["id"] == body.get("prompt_id")), None)
                if not prompt and len(prompts) == 1 and "prompt_id" not in body:
                    prompt = prompts[0]
                if not prompt:
                    return jsonify(errors={"prompt_id": "请选择任务绑定的实际执行 Prompt"}), 422
            record.update({"task_id": task["id"], "accepted_at": stamp, "upload": "uploading",
                           "quality": "pending", "collection_result": None,
                           "prompt": copy.deepcopy(prompt),
                           "checkpoint": task.get("checkpoint", "")})
            task["records"].append(record)
            task["updated_at"] = stamp
            conn.execute("UPDATE collection_tasks SET payload=? WHERE id=?",
                         (json.dumps(task, ensure_ascii=False), task["id"]))
        return jsonify(recording=copy.deepcopy(record), task=public_task(task, True)), 201

    @bp.post(API + "/tasks/<task_id>/recordings/<record_id>/upload-complete")
    @bp.post(API + "/tasks/<task_id>/recordings/<record_id>/upload-failed")
    def complete_recording_upload(task_id, record_id):
        """Complete an admitted upload, including after the task is closed.

        Completion is idempotent. A closed task rejects sessions that were never
        admitted while it was open, but keeps an admitted in-flight session.
        """
        body = request.get_json(silent=True)
        if body is None:
            body = {}
        if not isinstance(body, dict):
            return jsonify(error="请求内容必须为对象"), 422
        if "collection_result" in body and body["collection_result"] not in (None, "success", "failure"):
            return jsonify(errors={"collection_result": "采集结论仅支持成功或失败"}), 422
        failed = request.path.endswith("/upload-failed")
        error_message = body.get("error", "")
        if not isinstance(error_message, str) or len(error_message) > 500:
            return jsonify(errors={"error": "失败信息最多500个字符"}), 422
        stamp = now()
        with database() as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            task = get_task(conn, task_id)
            record = next((item for item in task["records"] if item.get("id") == record_id), None)
            if record is None:
                return jsonify(error="Recording 不存在或未被任务接收", code="recording_not_admitted"), 404
            if record.get("upload") == "uploaded":
                return jsonify(recording=copy.deepcopy(record), task=public_task(task, True), replayed=True), 200
            if task["status"] == "closed" and record.get("accepted_at") and (not task.get("closed_at") or record["accepted_at"] > task["closed_at"]):
                return jsonify(error="任务结束后未接收该上传，不能写入", code="upload_not_admitted"), 409
            if body.get("seconds") is not None:
                seconds = body.get("seconds")
                if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
                    return jsonify(errors={"seconds": "录制时长无效"}), 422
                record["seconds"] = seconds
            record["upload"] = "failed" if failed else "uploaded"
            if failed:
                record["upload_error"] = error_message.strip()
                record["upload_failed_at"] = stamp
            else:
                record["uploaded_at"] = stamp
                record.pop("upload_error", None)
            if body.get("collection_result") in ("success", "failure"):
                record["collection_result"] = body["collection_result"]
            task["updated_at"] = stamp
            conn.execute("UPDATE collection_tasks SET payload=? WHERE id=?",
                         (json.dumps(task, ensure_ascii=False), task["id"]))
        return jsonify(recording=copy.deepcopy(record), task=public_task(task, True)), 200

    @bp.patch(API + "/tasks/<task_id>")
    @bp.post(API + "/tasks/<task_id>/state")
    def update(task_id):
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error="请求内容无效"), 400
        with database() as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            task = get_task(conn, task_id)
            if type(body.get("revision")) is not int or body["revision"] != task["revision"]:
                return jsonify(error="任务已被更新，请刷新后重试"), 409
            title, description, changes = "", "", []
            stamp = now()
            if request.path.endswith("/state"):
                state = body.get("status")
                if state not in ("open", "closed"):
                    return jsonify(error="采集状态无效"), 422
                if task["status"] == state:
                    return jsonify(task=public_task(task, True))
                task["status"] = state
                task["closed_at"] = stamp if state == "closed" else None
                title = "结束采集" if state == "closed" else "重新开放采集"
                description = "停止新录制，保留在途录制、合法补传和后续处理。" if state == "closed" else "允许继续采集，原有录制和处理结果保持。"
            else:
                resolved, errors = resolve_spec(conn, body)
                data, validation_errors = validate_payload(resolved, task)
                errors.update(validation_errors)
                if errors:
                    return jsonify(errors=errors), 422
                # Changing a direct link clears the old reference; bind only after validation.
                bind_spec(conn, data)
                old_config = {key: copy.deepcopy(task.get(key, '' if key.startswith('spec_') else None)) for key in data}
                old_config['priority'] = task.get('priority', 6)
                # 等价保存不产生无意义日志，也不修改并发修订号或更新时间。
                if data == old_config:
                    return jsonify(task=public_task(task, True), unchanged=True)
                labels = {"description": "任务说明", "spec_url": "采集规范", "spec_name": "规范名称", "priority": "优先级", "expected_hours": "预期采集时长（小时）", "tags": "任务标签", "generalization": "位置泛化统计"}
                changes = [{"field": key, "label": label, "before": old_config[key], "after": copy.deepcopy(data[key])}
                           for key, label in labels.items() if old_config[key] != data[key]]
                task.update(data)
                title, description = "更新采集任务", "已更新：" + "、".join(change["label"] for change in changes)
            task["revision"] += 1
            task["updated_at"] = stamp
            if title:
                event = {"at": stamp, "actor": USER, "title": title, "detail": description}
                if changes:
                    event["changes"] = changes
                task["events"].append(event)
            conn.execute("UPDATE collection_tasks SET payload=? WHERE id=?", (json.dumps(task, ensure_ascii=False), task["id"]))
        return jsonify(task=public_task(task, True))

    app.register_blueprint(bp)
