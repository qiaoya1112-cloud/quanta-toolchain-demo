"""Map readable third-party dataset files to the platform's episode model."""

import io
import json
import re
import tarfile
import zipfile
from pathlib import Path


def _members(path):
    path = Path(path)
    if path.is_dir():
        files = {item.relative_to(path).as_posix(): item for item in path.rglob("*") if item.is_file()}
        return files, lambda name: files[name].read_bytes()
    if path.name.lower().endswith(".zip"):
        archive = zipfile.ZipFile(path)
        files = {name: name for name in archive.namelist() if not name.endswith("/")}
        return files, lambda name: archive.read(name)
    if path.name.lower().endswith(".tar.gz"):
        archive = tarfile.open(path, "r:gz")
        files = {item.name: item for item in archive if item.isfile()}
        return files, lambda name: archive.extractfile(files[name]).read()
    return {path.name: path}, lambda name: path.read_bytes()


def read_media_member(path, member):
    """Read a media member only after the caller has checked parsed membership."""
    path = Path(path)
    if path.is_dir():
        root = path.resolve()
        target = (root / member).resolve()
        if root not in target.parents or not target.is_file():
            raise FileNotFoundError(member)
        return target.read_bytes()
    if path.name.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as archive:
            return archive.read(member)
    if path.name.lower().endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            entry = archive.getmember(member)
            if not entry.isfile():
                raise FileNotFoundError(member)
            return archive.extractfile(entry).read()
    raise FileNotFoundError(member)


def _find(files, suffix):
    return next((name for name in files if name.endswith(suffix)), None)


def _jsonl(data):
    return [json.loads(line) for line in data.decode("utf-8-sig").splitlines() if line.strip()]


def _parquet_rows(data, columns):
    try:
        import pyarrow.parquet as parquet
    except ImportError as error:
        raise ValueError("解析 Parquet 需要安装 pyarrow") from error
    source = parquet.ParquetFile(io.BytesIO(data))
    available = [column for column in columns if column in source.schema.names]
    return source.metadata.num_rows, source.read(columns=available).to_pylist() if available else []


def _text(value):
    if isinstance(value, list):
        return _text(value[0]) if value else ""
    if isinstance(value, dict):
        return _text(value.get("text") or value.get("name") or value.get("task"))
    return str(value).strip() if value is not None else ""


def _prompt(row, tasks):
    for key in ("language_instruction", "prompt", "instruction", "task", "text", "tasks"):
        value = _text(row.get(key))
        if value:
            return value
    task_index = row.get("task_index")
    try:
        return tasks.get(int(task_index), "")
    except (TypeError, ValueError):
        return ""


def _episode(idx, length, prompt, metadata=None):
    metadata = metadata or {}
    tags = metadata.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    lowlevel = _text(metadata.get("lowlevel_prompt") or metadata.get("subtask"))
    segments = ([{"prompt_id": lowlevel, "name": lowlevel, "start_frame": 0, "end_frame": length}]
                if lowlevel and length else [])
    return {
        "idx": idx, "rec": _text(metadata.get("recording_id")) or f"episode_{idx:06d}",
        "length": length, "instr": prompt or "未提供 Prompt", "tags": tags,
        "annotation": {"episode_id": f"episode_{idx:06d}", "recording_id": _text(metadata.get("recording_id")),
                       "highlevel_prompt_id": _text(metadata.get("task_index")) or f"task_{idx}",
                       "lowlevel_segments": segments},
        "quality_rule": _text(metadata.get("quality_rule")),
        "quality_result": _text(metadata.get("quality_result")),
        "annotation_rule": _text(metadata.get("annotation_rule")),
        "annotation_status": _text(metadata.get("annotation_status")),
    }


def parse_local_dataset(path):
    """Read available metadata and Parquet columns without inventing absent values."""
    files, read = _members(path)
    info_name = _find(files, "meta/info.json")
    tasks_name = _find(files, "meta/tasks.jsonl")
    episodes_name = _find(files, "meta/episodes.jsonl")
    info = json.loads(read(info_name).decode("utf-8-sig")) if info_name else {}
    task_rows = _jsonl(read(tasks_name)) if tasks_name else []
    tasks = {int(item["task_index"]): _prompt(item, {}) for item in task_rows if "task_index" in item}
    metadata_rows = _jsonl(read(episodes_name)) if episodes_name else []
    rows = {}
    for position, item in enumerate(metadata_rows):
        idx = int(item.get("episode_index", position))
        length = int(item.get("length") or item.get("num_frames") or 0)
        rows[idx] = _episode(idx, length, _prompt(item, tasks), item)

    parquet_names = sorted(name for name in files if name.lower().endswith(".parquet"))
    columns = ("episode_index", "task_index", "language_instruction", "prompt", "instruction",
               "task", "text", "lowlevel_prompt", "subtask", "tags", "recording_id",
               "quality_rule", "quality_result", "annotation_rule", "annotation_status")
    for name in parquet_names:
        match = re.search(r"episode_(\d+)\.parquet$", name)
        if match and int(match.group(1)) in rows and rows[int(match.group(1))]["length"]:
            continue
        frame_count, frames = _parquet_rows(read(name), columns)
        if not frames:
            idx = int(match.group(1)) if match else len(rows)
            rows.setdefault(idx, _episode(idx, frame_count, ""))
            continue
        grouped = {}
        for frame in frames:
            idx = int(frame.get("episode_index") if frame.get("episode_index") is not None
                      else match.group(1) if match else 0)
            entry = grouped.setdefault(idx, {"count": 0, "metadata": frame})
            entry["count"] += 1
        for idx, entry in grouped.items():
            if idx not in rows:
                metadata = entry["metadata"]
                rows[idx] = _episode(idx, entry["count"], _prompt(metadata, tasks), metadata)
            elif not rows[idx]["length"]:
                rows[idx]["length"] = entry["count"]

    video_names = sorted(name for name in files if name.lower().endswith((".mp4", ".webm")))
    for row in rows.values():
        suffix = f'episode_{row["idx"]:06d}'
        row["videos"] = {Path(name).parent.name: name for name in video_names
                         if Path(name).stem == suffix}
    fps = info.get("fps") or info.get("video.fps") or 0
    return {"info": info, "tasks": task_rows, "episodes": [rows[key] for key in sorted(rows)],
            "fps": float(fps), "robot": _text(info.get("robot_type")),
            "video_members": video_names, "sample_data": False}


def sample_dataset(source_id):
    """Explicit preview fixtures for the four built-in, unreachable tos://3rd examples."""
    examples = {
        "x1": ("Pick up the block and place it in the tray", "Pick and place", ["抓取", "放置", "高质量"], "Everyday Robots"),
        "x2": ("Move the cup to the kitchen counter", "Move the cup", ["抓取", "放置", "桌面"], "WidowX"),
        "x5": ("Grasp the object and move it to the target", "Grasp and move", ["抓取", "放置", "高质量"], "多机器人"),
        "x6": ("Place the mug beside the plate", "Place the mug", ["放置", "桌面", "高质量"], "Franka Panda"),
    }
    prompt, lowlevel, tags, robot = examples[source_id]
    sample_video = "sample://dataset-sample-preview.webm"
    cameras = ("cam_high", "cam_left_wrist", "cam_right_wrist")
    rows = []
    for idx in range(8):
        row = _episode(idx, 720 + idx * 45, prompt,
                       {"tags": tags, "task_index": 0, "lowlevel_prompt": lowlevel})
        row["videos"] = {camera: sample_video for camera in cameras}
        rows.append(row)
    return {"info": {"codebase_version": "v2.1", "fps": 30, "robot_type": robot, "sample_data": True},
            "tasks": [{"task_index": 0, "task": prompt}], "episodes": rows,
            "fps": 30, "robot": robot, "video_members": [sample_video],
            "sample_data": True, "sample_schema_version": 4}
