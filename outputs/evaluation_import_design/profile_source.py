"""Reproducible, read-only profile of Feishu exports. No remote writes."""
import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / 'source'

def read(name):
    return [json.loads(line) for line in (SRC / name).read_text().splitlines() if line.strip()]

def blank(v):
    return v is None or v == [] or (isinstance(v, str) and not v.strip())

def scalar(v):
    return v[0] if isinstance(v, list) and len(v) == 1 else v

def counts(rows, key):
    return dict(collections.Counter(str(scalar(r.get(key))) for r in rows if not blank(r.get(key))))

def fields(name):
    return json.loads((SRC / name).read_text())['data']['fields']

cases = read('cases-0000.ndjson')
scenes, skills, factors, values = [read(f'{n}.ndjson') for n in ('scenes', 'skills', 'factors', 'values')]
case_fields = [f['name'] for f in fields('case-fields.json')]
visible = json.loads((SRC / 'case-visible-fields.json').read_text())['data']['visible_fields']
result = {
    'source_url': 'https://nwd4iy9rd2s.feishu.cn/base/OQ2UbV65natigrstPbXcwhWinyb?table=tblnjRJV5JV5vLQr&view=vewi0Okt9f',
    'case_schema_fields': len(case_fields), 'visible_fields': len(visible),
    'hidden_fields': [f for f in case_fields if f not in visible],
    'records': {n: len(rows) for n, rows in [('cases', cases), ('scenes', scenes), ('skills', skills), ('factors', factors), ('values', values)]},
    'case_missing': {f: sum(blank(r.get(f)) for r in cases) for f in case_fields},
    'case_option_counts': {k: counts(cases, k) for k in ['Stage', 'Story', 'Skill标签', '数据归属', '来源', '版本', '是否采集过遥操数据', '是否在eval场景集']},
}
nonempty_ids = collections.Counter(r['用例ID'].strip() for r in cases if not blank(r.get('用例ID')))
result['duplicate_case_ids'] = {k: v for k, v in nonempty_ids.items() if v > 1}
result['invalid_case_ids'] = [{'record_id': r['record_id'], 'id': r['用例ID']} for r in cases if not blank(r.get('用例ID')) and not re.fullmatch(r'[-A-Za-z0-9_]+', r['用例ID'].strip())]
result['blank_business_rows'] = [r['record_id'] for r in cases if all(blank(r.get(f)) for f in case_fields)]
result['missing_required_rows'] = [{'record_id': r['record_id'], 'id': r.get('用例ID'), 'missing': [f for f in ['用例ID', 'Stage', 'Story', 'Prompt', 'prompt_ch', '数据归属'] if blank(r.get(f))]} for r in cases if any(blank(r.get(f)) for f in ['用例ID', 'Stage', 'Story', 'Prompt', 'prompt_ch', '数据归属'])]
result['attachments'] = {'cases': sum(bool(r.get('布置图片')) for r in cases), 'files': sum(len(r.get('布置图片') or []) for r in cases), 'max_per_case': max(len(r.get('布置图片') or []) for r in cases), 'over_1MB': sum(a.get('size', 0) > 1024*1024 for r in cases for a in r.get('布置图片') or [])}
result['props_ditto'] = [{'record_id': r['record_id'], 'id': r.get('用例ID'), 'props': r.get('道具')} for r in cases if '同上' in (r.get('道具') or '')]
result['invalid_yes_no'] = {k: [{'record_id': r['record_id'], 'id': r.get('用例ID'), 'value': r[k]} for r in cases if not blank(r.get(k)) and scalar(r[k]) not in ['是', '否']] for k in ['是否在eval场景集', '是否采集过遥操数据']}
json_errors, json_shapes, key_mismatch, details = [], [], [], []
for r in cases:
    text = r.get('Factor取值')
    if blank(text):
        continue
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError) as err:
        json_errors.append({'record_id': r['record_id'], 'id': r.get('用例ID'), 'value': text, 'error': str(err)})
        continue
    valid_shape = isinstance(parsed, dict) and all(isinstance(k, str) and k.strip() and (isinstance(v, str) or (isinstance(v, list) and all(isinstance(x, str) for x in v))) for k, v in parsed.items())
    if not valid_shape:
        json_shapes.append({'id': r.get('用例ID'), 'value': parsed})
        continue
    raw = (r.get('Factor') or '').strip()
    if len(parsed) == 1 and raw != next(iter(parsed)):
        key_mismatch.append({'id': r.get('用例ID'), 'Factor': raw, 'json_keys': list(parsed)})
    details.append({'id': r.get('用例ID'), 'factors': parsed})
result['factor_json'] = {'populated': sum(not blank(r.get('Factor取值')) for r in cases), 'invalid_json': json_errors, 'invalid_shape': json_shapes, 'single_key_text_mismatch': key_mismatch, 'parsed_records': len(details), 'multi_factor_records': sum(len(d['factors']) > 1 for d in details)}
result['factor_json']['combined_key_records'] = sum(any(',' in k or '，' in k or '\n' in k for k in d['factors']) for d in details)
result['factor_blank_asymmetry'] = [{'id': r.get('用例ID'), 'Factor': r.get('Factor'), 'Factor取值': r.get('Factor取值')} for r in cases if blank(r.get('Factor')) != blank(r.get('Factor取值'))]
result['related'] = {
    'scene_factor_links_populated': sum(bool(r.get('4级-factor')) for r in scenes),
    'scene_factor_value_populated': sum(not blank(r.get('factor取值')) for r in scenes),
    'skill_named_rows': sum(not blank(r.get('Skill')) or not blank(r.get('Skill_中文')) for r in skills),
    'skill_with_cn_en_category': sum(not blank(r.get('Skill_中文')) and not blank(r.get('Skill_EN')) and not blank(r.get('SKill类别')) for r in skills),
    'skill_category_counts': counts(skills, 'SKill类别'),
    'factor_named_rows': sum(not blank(r.get('Factor')) for r in factors),
    'value_named_rows': sum(not blank(r.get('取值')) for r in values),
    'value_extra_fields_populated': {f'字段 {i}': sum(not blank(r.get(f'字段 {i}')) for r in values) for i in range(2, 17)},
}
# Use schema spelling, not guessed whitespace in the exported extra-field names.
extra_fields = [f['name'] for f in fields('value-fields.json') if f['name'].startswith('字段')]
result['related']['value_extra_fields_populated'] = {f: sum(not blank(r.get(f)) for r in values) for f in extra_fields}
known_factor_ids = {r['record_id'] for r in factors}
result['related']['value_link_missing_targets'] = [{'record_id': r['record_id'], 'target': a['id']} for r in values for a in (r.get('Factor') or []) if a['id'] not in known_factor_ids]
result['related']['value_without_factor_link'] = sum(not blank(r.get('取值')) and not r.get('Factor') for r in values)
for table, rows, k in [('skills', skills, 'Skill'), ('factors', factors, 'Factor')]:
    names = collections.Counter(str(scalar(r[k])) for r in rows if not blank(r.get(k)))
    result['related'][f'{table}_duplicate_names'] = {n: c for n, c in names.items() if c > 1}
result['schema_other_tables'] = {n: [{'name': f['name'], 'type': f['type']} for f in fields(f'{n}-fields.json')] for n in ['evalset', 'legacy']}
(ROOT / 'source-profile.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps({k: v for k, v in result.items() if k not in ['case_option_counts', 'props_ditto', 'invalid_yes_no', 'factor_json']}, ensure_ascii=False, indent=2))
print('factor_json_counts', {k: len(v) if isinstance(v, list) else v for k, v in result['factor_json'].items()})
print('invalid_yes_no_counts', {k: len(v) for k, v in result['invalid_yes_no'].items()})
print('props_ditto', len(result['props_ditto']))
