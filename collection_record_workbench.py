"""Read-only collection record context for the shared detail workbench."""
import copy
import re
from urllib.parse import urlsplit

from flask import abort, current_app, request

from post_training_collection import BASE, database, get_task


def collection_workbench_context():
    task_id = request.args.get('collection_task_id', '')
    recording_id = request.args.get('recording_id', '')
    if not task_id or not recording_id:
        abort(404)
    with database() as conn:
        task = get_task(conn, task_id)
    record = next((r for r in task['records'] if r['id'] == recording_id), None)
    if record is None:
        abort(404)
    fallback = BASE + '/' + task['id'] + '#records'
    value = request.args.get('return_to', '')
    try:
        parsed = urlsplit(value)
        valid_return = (not parsed.scheme and not parsed.netloc and parsed.path == BASE + '/' + task['id']
                        and '\\' not in value and not any(ord(c) < 32 for c in value))
    except ValueError:
        valid_return = False
    projects = {p['id']: p['name'] for p in current_app.config['COLLECTION_PROJECTS']}
    cameras = []
    explicit = 'videos' in record or any(
        view + suffix in record for view in ('head', 'left_arm', 'right_arm')
        for suffix in ('_video_url', '_compressed_video_url', '_snapshot_url'))
    demo = not explicit and bool(re.fullmatch(r'DEMO-R-\d+', record['id']))

    def safe_url(value):
        if not isinstance(value, str) or not value or '\\' in value or any(ord(c) < 32 for c in value):
            return ''
        try:
            parsed = urlsplit(value)
            return value if (parsed.scheme in ('http', 'https') and parsed.netloc) or (not parsed.scheme and not parsed.netloc and value.startswith('/')) else ''
        except ValueError:
            return ''

    for key, view, label in [('head', 'head', '头部'), ('left', 'left_arm', '左臂'), ('right', 'right_arm', '右臂')]:
        videos = record.get('videos') or {}
        source = next((v for v in videos if isinstance(v, dict) and v.get('camera') in (key, view)), {}) if isinstance(videos, list) else videos.get(key, videos.get(view, {})) if isinstance(videos, dict) else {}
        media = source if isinstance(source, str) else (source.get('url') or source.get('src')) if isinstance(source, dict) else ''
        poster = source.get('poster') if isinstance(source, dict) else ''
        src = ('/static/post_training_collection/media/' + key + '.webm') if demo else safe_url(media or record.get(view + '_compressed_video_url') or record.get(view + '_video_url'))
        cameras.append(dict(key=key, label=label, src=src if record['upload'] == 'uploaded' else '',
                            poster='/static/post_training_collection/media/' + key + '.png' if demo else safe_url(poster or record.get(view + '_snapshot_url')), demo=demo))
    return dict(recording_id=record['id'], recording_device=record.get('device', '—'),
                recording_collector=record.get('operator', '—'), source_task_id=task['id'],
                source_task_name=task['name'], project=projects.get(task['project'], task['project']),
                collection_command=(record.get('prompt') or {}).get('text') or task.get('description') or '—',
                instruction=(record.get('prompt') or {}).get('text') or task.get('description') or '—',
                processing_task='', task_name='', stage='—', node='—', flow='—', pool='',
                task_pool='—', current_processor='—', user_group='—', processing_status='—',
                _no_processing_task=True, collection_record=copy.deepcopy(record), cameras=cameras,
                tags=copy.deepcopy(task.get('tags') or []), return_url=value if valid_return else fallback)
