"""Shared local rule catalog; permissions are resolved on the server, never from query flags."""
import json
import re

from flask import current_app
import post_training_collection as collection

API = '/api/processing-rules'


def permissions(project=''):
    resolver = current_app.config.get('PROCESSING_RULE_PERMISSION_RESOLVER')
    values = resolver(project) if resolver else current_app.config.get('PROCESSING_RULE_PERMISSIONS', {'create': True, 'publish': True})
    return dict(create=bool(values.get('create', False)), publish=bool(values.get('publish', False)),
                edit=bool(values.get('edit', values.get('create', False))),
                manage=bool(values.get('manage', values.get('create', False))),
                view=bool(values.get('view', True)), use=bool(values.get('use', True)))


def setup(conn):
    conn.execute('CREATE TABLE IF NOT EXISTS processing_rules (id TEXT PRIMARY KEY, request_key TEXT UNIQUE, fingerprint TEXT, payload TEXT NOT NULL)')


def stored(conn):
    setup(conn)
    return [json.loads(row['payload']) for row in conn.execute('SELECT payload FROM processing_rules ORDER BY rowid DESC')]


def catalog(seeds):
    from processing_rule_versions import catalog as version_catalog
    return version_catalog(seeds)


def ref(rule):
    from processing_rule_versions import view
    return view(rule)['value']


def name_conflict(records, project, name, exclude_id=None):
    return any(r['id'] != exclude_id and not r.get('deleted')
               and r['project'] == project and r['name'].strip().casefold() == name.strip().casefold()
               for r in records)


def allowed_types(flow):
    return flow.get('rule_types') or (['质检'] if flow['stage'] == '质检' else ['语义标注'] if '端到端' in flow['name'] else ['语义标注', '动作标注', '标签标注'])


def reference_error(conn, value, project, stage, flow=None, allow_historical=False):
    from processing_rule_versions import reference_error as check
    return check(conn, value, project, stage, flow, allow_historical=allow_historical)


def snapshot_reference(conn, value, project=None, stage=None):
    from processing_rule_versions import snapshot_reference as snapshot
    return snapshot(conn, value, project=project, stage=stage)


def validate(body):
    if not isinstance(body, dict):
        raise ValueError('规则内容无效')
    rule = {}
    for key in ('name', 'project', 'stage', 'rule_type', 'semantic_mode', 'document_link', 'semantic_text'):
        value = body.get(key, '')
        if not isinstance(value, str) or len(value) > (30000 if key == 'semantic_text' else 2000):
            raise ValueError('规则字段无效')
        rule[key] = value.strip()
    if not rule['name'] or len(rule['name']) > 100 or not rule['project']:
        raise ValueError('请填写规则名称和所属项目')
    projects = current_app.config.get('PROCESSING_RULE_PROJECTS')
    if projects is not None and rule['project'] not in projects:
        raise ValueError('请选择有效的所属项目')
    allowed = {'质检': ('质检',), '标注': ('语义标注', '动作标注', '标签标注')}
    if rule['rule_type'] not in allowed.get(rule['stage'], ()):
        raise ValueError('规则类型与业务环节不匹配')
    for key in ('quality_mistakes', 'quality_unqualified', 'annotation_tags', 'action_elements', 'action_descriptions', 'error_reasons'):
        values = body.get(key, [])
        if not isinstance(values, list) or len(values) > 500:
            raise ValueError('规则配置无效')
        rule[key] = values
    def strings(values):
        return bool(values) and all(isinstance(v, str) and v.strip() and len(v) <= 2000 for v in values)
    if rule['stage'] == '质检' and not all(strings(rule[k]) for k in ('quality_mistakes', 'quality_unqualified')):
        raise ValueError('失误标准和不合格标准至少各填写一条')
    if rule['rule_type'] == '标签标注' and not strings(rule['annotation_tags']):
        raise ValueError('请至少选择一个要打的标签')
    if rule['rule_type'] == '语义标注':
        if rule['semantic_mode'] == 'link':
            if not re.match(r'^https?://[^\s]+$', rule['document_link']):
                raise ValueError('请输入有效的文档链接')
        elif rule['semantic_mode'] != 'text' or not rule['semantic_text']:
            raise ValueError('请输入文本说明')
    if rule['rule_type'] == '动作标注':
        zh, en = set(), set()
        if not rule['action_elements']:
            raise ValueError('请至少添加一个动作元素')
        for element in rule['action_elements']:
            if not isinstance(element, dict) or not all(isinstance(element.get(k), str) and element[k].strip() for k in ('name', 'key')):
                raise ValueError('请完整填写动作元素名称和 Key')
            if element['name'] in zh or element['key'] in en:
                raise ValueError('动作元素名称和 Key 不可重复')
            zh.add(element['name']); en.add(element['key'])
            values = element.get('values')
            if not isinstance(values, list) or not values or any(not isinstance(v, dict) or not all(isinstance(v.get(k), str) and v[k].strip() for k in ('name', 'key')) for v in values):
                raise ValueError('每个动作元素至少需要一个完整的枚举值')
        if not rule['action_descriptions']:
            raise ValueError('请至少填写一条动作描述')
        for description in rule['action_descriptions']:
            if not isinstance(description, dict) or not any(description.get(k) for k in ('zh', 'en')):
                raise ValueError('请至少填写一条动作描述')
            for language, tokens in (('zh', zh), ('en', en)):
                text = description.get(language, '')
                if not isinstance(text, str) or '{}' in text or any(t not in tokens for t in re.findall(r'\{([^{}]+)\}', text)):
                    raise ValueError('请补全动作描述并使用对应语言的元素')
    if not rule['error_reasons'] or any(not isinstance(v, dict) or not isinstance(v.get('name'), str) or not v['name'].strip() for v in rule['error_reasons']):
        raise ValueError('请至少添加一个错误原因')
    # Hidden inputs from the shared form do not belong to another rule type.
    if rule['stage'] != '质检':
        rule['quality_mistakes']=[];rule['quality_unqualified']=[]
    if rule['rule_type'] != '标签标注':
        rule['annotation_tags']=[]
    if rule['rule_type'] != '动作标注':
        rule['action_elements']=[];rule['action_descriptions']=[]
    if rule['rule_type'] != '语义标注':
        rule['semantic_mode']='';rule['document_link']='';rule['semantic_text']=''
    elif rule['semantic_mode']=='link':
        rule['semantic_text']=''
    else:
        rule['document_link']=''
    rule['rule_config'] = rule.pop('document_link')
    rule['desc'] = rule['semantic_text'][:120] or rule['rule_type']
    return rule


def register_rules(app, seeds, legacy_rules, editor):
    from processing_rule_versions import register
    return register(app, seeds, legacy_rules, editor)
