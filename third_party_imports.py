"""Persistent import jobs for the third-party source prototype."""

import datetime
import json
import os
import re
import sqlite3
import tarfile
import threading
import uuid
import zipfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

import dataset_import_parser


_running = set()
_running_lock = threading.Lock()


def _open_connection(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS imports (
        id TEXT PRIMARY KEY, source_id TEXT UNIQUE NOT NULL,
        source_name TEXT NOT NULL, dataset_id TEXT UNIQUE NOT NULL,
        dataset_name TEXT NOT NULL, dataset_ident TEXT NOT NULL, folder TEXT NOT NULL, format TEXT NOT NULL,
        file_name TEXT NOT NULL, file_path TEXT NOT NULL, file_size INTEGER NOT NULL,
        status TEXT NOT NULL, stage TEXT NOT NULL, error TEXT NOT NULL DEFAULT '',
        owner TEXT NOT NULL, created_at TEXT NOT NULL, completed_at TEXT NOT NULL DEFAULT '',
        attempts INTEGER NOT NULL DEFAULT 1, episode_count INTEGER NOT NULL DEFAULT 0,
        parsed_json TEXT NOT NULL DEFAULT '{}'
    )""")
    if "storage_location" not in {row[1] for row in conn.execute("PRAGMA table_info(imports)")}:
        conn.execute("ALTER TABLE imports ADD COLUMN storage_location TEXT NOT NULL DEFAULT 'local'")
        for location in ("tos", "vepfs", "ks3"):
            conn.execute("UPDATE imports SET storage_location=? WHERE storage_location='local' AND file_path LIKE ?",
                         (location, location + "://%"))
    if "dataset_ident" not in {row[1] for row in conn.execute("PRAGMA table_info(imports)")}:
        conn.execute("ALTER TABLE imports ADD COLUMN dataset_ident TEXT NOT NULL DEFAULT ''")
    if "parsed_json" not in {row[1] for row in conn.execute("PRAGMA table_info(imports)")}:
        conn.execute("ALTER TABLE imports ADD COLUMN parsed_json TEXT NOT NULL DEFAULT '{}'")
    conn.execute("UPDATE imports SET dataset_ident=dataset_id WHERE dataset_ident=''")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS import_source_name ON imports(lower(source_name))")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS import_dataset_name ON imports(lower(dataset_name))")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS import_dataset_ident ON imports(lower(dataset_ident))")
    for source_id, source_name, dataset_id, dataset_name, ds_format, file_name, file_path, owner, created_at in (
        ("x1", "Open Pick-Place (RT-1)", "third_x1", "rt1_pickplace_v1",
         "LeRobort", "rt1_pickplace.tar.gz", "tos://3rd/rt1_pickplace.tar.gz", "Min Chen", "2026-05-18 09:20"),
        ("x2", "Bridge Kitchen v2", "third_x2", "bridge_kitchen_v2",
         "LeRobort", "bridge_v2.parquet", "tos://3rd/bridge_v2.parquet", "Lance Li", "2026-05-22 13:05"),
        ("x5", "Open X-Embodiment subset", "third_x5", "open_x_embodiment_v1",
         "Mozdataset v2", "open_x_embodiment_v1", "tos://3rd/open_x_embodiment_v1/", "Joanna Qiao", "2026-06-26 10:40:00"),
        ("x6", "RoboMimic kitchen", "third_x6", "robomimic_kitchen_v1",
         "Mozdataset v2", "robomimic_kitchen_v1", "tos://3rd/robomimic_kitchen_v1/", "Min Chen", "2026-06-25 16:55:00"),
    ):
        conn.execute("""INSERT OR IGNORE INTO imports
            (id, source_id, source_name, dataset_id, dataset_name, dataset_ident, folder, format,
             file_name, file_path, file_size, status, stage, owner, created_at, completed_at, storage_location)
            VALUES (?, ?, ?, ?, ?, ?, '预训练', ?, ?, ?, 0, 'done', '已完成', ?, ?, ?, 'tos')""",
            ("import_" + source_id, source_id, source_name, dataset_id, dataset_name, dataset_id, ds_format,
             file_name, file_path, owner, created_at, created_at))
        sample = dataset_import_parser.sample_dataset(source_id)
        current = conn.execute("SELECT parsed_json FROM imports WHERE id=?", ("import_" + source_id,)).fetchone()
        previous = json.loads(current["parsed_json"]) if current else {}
        if not previous or (previous.get("sample_data") and previous.get("sample_schema_version", 0) < 4):
            conn.execute("""UPDATE imports SET parsed_json=?, episode_count=?, stage='已完成'
                WHERE id=?""",
                (json.dumps(sample, ensure_ascii=False), len(sample["episodes"]), "import_" + source_id))
    conn.execute("UPDATE imports SET stage='已完成' WHERE stage='示例映射数据'")
    conn.commit()
    return conn


@contextmanager
def _connect(db_path):
    conn = _open_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_imports(db_path):
    with _connect(db_path) as conn:
        rows = [dict(row) for row in conn.execute("SELECT * FROM imports ORDER BY created_at DESC, id DESC")]
    for row in rows:
        if row["status"] in ("queued", "running"):
            start_import(db_path, row["id"])
    return rows


def get_import(db_path, task_id):
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM imports WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def get_import_by_dataset(db_path, dataset_id):
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM imports WHERE dataset_id = ?", (dataset_id,)).fetchone()
    return dict(row) if row else None


def create_import(db_path, source_name, dataset_ident, dataset_name, folder, ds_format, file_name,
                  file_path, file_size, owner, storage_location="local"):
    ident = uuid.uuid4().hex[:12]
    task_id = "import_" + ident
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect(db_path) as conn:
        conn.execute("""INSERT INTO imports
            (id, source_id, source_name, dataset_id, dataset_name, dataset_ident, folder, format,
             file_name, file_path, file_size, status, stage, owner, created_at, storage_location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', '等待校验', ?, ?, ?)""",
            (task_id, "tp_" + ident, source_name, "third_" + ident, dataset_name, dataset_ident,
             folder, ds_format, file_name, file_path, file_size, owner, now, storage_location))
    start_import(db_path, task_id)
    return get_import(db_path, task_id)


def _inspect_file(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("导入文件不存在或为空")
    name = path.name.lower()
    if name.endswith(".zip"):
        with zipfile.ZipFile(path) as archive:
            members = [item.filename for item in archive.infolist() if not item.is_dir()]
            if not members:
                raise ValueError("压缩包内没有文件")
            bad = archive.testzip()
            if bad:
                raise ValueError("压缩包中的文件校验失败：" + bad)
    elif name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            members = [item.name for item in archive if item.isfile()]
            if not members:
                raise ValueError("压缩包内没有文件")
    elif name.endswith(".parquet"):
        with path.open("rb") as stream:
            start = stream.read(4)
            stream.seek(-4, os.SEEK_END)
            end = stream.read(4)
        if start != b"PAR1" or end != b"PAR1":
            raise ValueError("Parquet 文件格式校验失败")
        members = [path.name]
    else:
        raise ValueError("仅支持 .tar.gz、.zip 或 .parquet 文件")
    return len({Path(name).stem for name in members
                if name.lower().endswith(".parquet") and Path(name).stem.startswith("episode_")})


def validate_storage_address(location, address):
    if location not in ("tos", "vepfs", "ks3") or not address or len(address) > 2048:
        raise ValueError("请选择有效的存储位置并填写存储地址")
    if any(char.isspace() or ord(char) < 32 for char in address):
        raise ValueError("存储地址不能包含空格或控制字符")
    if location == "vepfs" and re.fullmatch(r"/mnt/vepfs[^/]+/.+", address):
        return address
    parsed = urlsplit(address)
    if parsed.scheme != location or not parsed.netloc or not parsed.path.strip("/") or parsed.query or parsed.fragment:
        raise ValueError(f"存储地址应为有效的 {location} 路径")
    return address


def _worker(db_path, task_id):
    try:
        with _connect(db_path) as conn:
            conn.execute("UPDATE imports SET status='running', stage='校验存储地址', error='' WHERE id=? AND status IN ('queued', 'running')", (task_id,))
        task = get_import(db_path, task_id)
        if not task or task["status"] != "running":
            return
        parsed = {}
        if task["storage_location"] == "local":
            _inspect_file(task["file_path"])
            parsed = dataset_import_parser.parse_local_dataset(task["file_path"])
        elif task["storage_location"] == "vepfs" and Path(task["file_path"]).exists():
            parsed = dataset_import_parser.parse_local_dataset(task["file_path"])
        else:
            validate_storage_address(task["storage_location"], task["file_path"])
        episode_count = len(parsed.get("episodes", []))
        with _connect(db_path) as conn:
            conn.execute("UPDATE imports SET stage='登记数据源并创建数据集' WHERE id=?", (task_id,))
            completed_stage = ("已解析" if episode_count else
                               "已登记，远端内容待解析" if task["storage_location"] != "local" else
                               "未发现可解析的 Episode")
            conn.execute("""UPDATE imports SET status='done', stage=?, episode_count=?,
                parsed_json=?, completed_at=?, error='' WHERE id=?""",
                (completed_stage, episode_count, json.dumps(parsed, ensure_ascii=False),
                 datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id))
    except Exception as error:
        with _connect(db_path) as conn:
            conn.execute("UPDATE imports SET status='fail', stage='导入失败', error=? WHERE id=?",
                         (str(error), task_id))
    finally:
        with _running_lock:
            _running.discard((db_path, task_id))


def start_import(db_path, task_id):
    key = (db_path, task_id)
    with _running_lock:
        if key in _running:
            return
        _running.add(key)
    threading.Thread(target=_worker, args=key, daemon=True).start()


def retry_import(db_path, task_id, file_name=None, file_path=None, file_size=None):
    with _connect(db_path) as conn:
        changed = conn.execute("""UPDATE imports SET status='queued', stage='等待校验', error='',
            attempts=attempts+1, file_name=COALESCE(?, file_name),
            file_path=COALESCE(?, file_path), file_size=COALESCE(?, file_size)
            WHERE id=? AND status='fail'""", (file_name, file_path, file_size, task_id)).rowcount
    if changed:
        start_import(db_path, task_id)
    return bool(changed)
