"""Immutable published processing-rule contents and one revision draft per rule."""
import copy
import hashlib
import json
import re
import uuid
from collections import Counter
from datetime import datetime

from flask import abort, current_app, jsonify, request
import post_training_collection as collection

API = '/api/processing-rules'
IDENTITY = ('name', 'project', 'stage', 'rule_type')
FIELDS = IDENTITY + ('semantic_mode', 'rule_config', 'semantic_text', 'quality_mistakes',
    'quality_unqualified', 'annotation_tags', 'action_elements', 'action_descriptions', 'error_reasons', 'desc')
LABELS = {'quality_mistakes':'失误标准', 'quality_unqualified':'不合格标准', 'annotation_tags':'标签',
    'action_elements':'动作元素', 'action_descriptions':'动作描述', 'error_reasons':'错误原因',
    'semantic_mode':'说明方式', 'rule_config':'文档链接', 'semantic_text':'文本说明'}


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def content(rule):
    return {k: copy.deepcopy(rule[k]) for k in FIELDS if k in rule}


def normalize(raw):
    rule = copy.deepcopy(raw)
    if 'versions' not in rule:
        published = rule.get('publish_status') == '已发布'
        rule['versions'] = [dict(number=1, content=content(rule), published_by=rule.get('owner', ''),
                                 published_at='', changes=['历史已发布内容'])] if published else []
        rule['draft'] = None if published else content(rule)
        rule['events'] = []
        rule['revision'] = 1
    return rule


def all_rules(conn, seeds=None):
    from processing_rule_store import stored
    saved = stored(conn)
    ids = {r['id'] for r in saved}
    seeds = current_app.config.get('PROCESSING_RULE_SEEDS', []) if seeds is None else seeds
    return [normalize(r) for r in saved + [r for r in seeds if r['id'] not in ids]]


def view(rule, version=None):
    rule = normalize(rule)
    selected = next((v for v in rule['versions'] if v['number'] == version), None) if version else (rule['versions'][-1] if rule['versions'] else None)
    result = copy.deepcopy(rule)
    result.update(selected['content'] if selected else rule.get('draft') or content(rule))
    result.update(version='v'+str(selected['number']) if selected else '',
                  value='rule:'+rule['id']+'@'+str(selected['number']) if selected else 'rule:'+rule['id']+'@0',
                  has_draft=rule.get('draft') is not None,
                  publish_status='已发布' if rule['versions'] else '未发布')
    result['pending_changes'] = changes(rule['versions'][-1]['content'],rule['draft']) if rule['versions'] and rule.get('draft') is not None else []
    return result


def catalog(seeds):
    with collection.database() as conn:
        return [view(r) for r in all_rules(conn, seeds) if not r.get('deleted')]


def resolve(conn, value):
    match = re.fullmatch(r'rule:([^@]+)@([1-9]\d*)', str(value))
    if not match:
        return None
    rule = next((r for r in all_rules(conn) if r['id'] == match[1] and not r.get('deleted')), None)
    if rule and any(v['number'] == int(match[2]) for v in rule['versions']):
        return view(rule, int(match[2]))
    return None


def legacy(value, stage=None):
    import data_platform_refactor as platform
    items = current_app.config.get('PROCESSING_RULE_LEGACY', platform.PROCESSING_RULES)
    candidates = [r for r in items if (not stage or r['stage'] == stage)
                  and str(value) in (r['name'], r['name']+' '+r['version'])]
    return candidates[0] if len(candidates)==1 else None


def reference_error(conn, value, project, stage, flow=None, allow_historical=False):
    from processing_rule_store import allowed_types, permissions
    if not permissions(project)['use']:
        return '没有使用该项目规则的权限'
    if not str(value).startswith('rule:'):
        old = legacy(value, stage)
        if old:
            # Once a legacy identity belongs to the managed catalog, aliases must
            # obey the same availability/version checks as stable references.
            managed = [r for r in all_rules(conn) if r['name']==old['name'] and r['project']==project
                       and r['stage']==stage and not r.get('deleted')]
            if len(managed)==1:
                version=str(old['version']).lower().removeprefix('v')
                return reference_error(conn,'rule:'+managed[0]['id']+'@'+version,project,stage,flow,allow_historical)
            if flow and old.get('rule_type') not in allowed_types(flow):
                return '处理规则类型不适用于当前处理流程'
            return None  # Known unmigrated Demo identities; no invented body.
        return '处理规则不存在或版本无效，请重新选择'
    rule = resolve(conn, value)
    if not rule or rule.get('status') != 'enabled':
        return '处理规则已删除、未发布或已停用，请重新选择'
    if not allow_historical and rule['version'] != 'v' + str(rule['versions'][-1]['number']):
        return '处理规则已发布新版，请重新选择当前版本'
    if rule['project'] != project or rule['stage'] != stage:
        return '处理规则与任务项目或业务环节不匹配'
    if flow and rule['rule_type'] not in allowed_types(flow):
        return '处理规则类型不适用于当前处理流程'
    return None


def snapshot_reference(conn, value, project=None, stage=None):
    rule = resolve(conn, value)
    if rule:
        return dict(id=rule['id'], name=rule['name'], version=rule['version'], rule_type=rule['rule_type'], content=content(rule))
    old = legacy(value)
    if old:
        managed=[r for r in all_rules(conn) if not r.get('deleted') and r['name']==old['name']
                 and (not project or r['project']==project) and (not stage or r['stage']==stage)]
        if len(managed)==1:
            return snapshot_reference(conn,'rule:'+managed[0]['id']+'@'+str(old['version']).lower().removeprefix('v'))
    return dict(name=old['name'], version=old['version'], legacy=True) if old else None


def changes(before, after):
    result = []
    for key, label in LABELS.items():
        a, b = before.get(key), after.get(key)
        if a == b:
            continue
        if isinstance(a, list) and isinstance(b, list):
            aa = Counter(json.dumps(v, sort_keys=True, ensure_ascii=False) for v in a)
            bb = Counter(json.dumps(v, sort_keys=True, ensure_ascii=False) for v in b)
            added, removed = sum((bb-aa).values()), sum((aa-bb).values())
            result.append(label + ('：调整顺序' if not added and not removed else '：' + '，'.join(
                s for s in (f'新增{added}项' if added else '', f'移除{removed}项' if removed else '') if s)))
        else:
            result.append(label+'：已修改')
    return result


def event(rule, action, before=None, after=None, **extra):
    rule.setdefault('events', []).append(dict(action=action, actor=collection.USER, at=now(),
        changes=changes(before or {}, after or {}) if before is not None else [],
        before=copy.deepcopy(before), after=copy.deepcopy(after), **extra))


def persist(conn, rule):
    conn.execute('INSERT INTO processing_rules VALUES(?,NULL,NULL,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',
                 (rule['id'], json.dumps(rule, ensure_ascii=False)))


def validate_content(body):
    from processing_rule_store import validate
    return validate(dict(body, document_link=body.get('document_link', body.get('rule_config', ''))))


def same_content(a,b):
    # Old seeds omit empty optional fields. Derived descriptions do not create a version.
    lists={'quality_mistakes','quality_unqualified','annotation_tags','action_elements','action_descriptions','error_reasons'}
    return all(a.get(key,[] if key in lists else '')==b.get(key,[] if key in lists else '') for key in FIELDS if key!='desc')


def publish(rule):
    if rule.get('draft') is None:
        raise ValueError('没有待发布修改')
    proposed = validate_content(rule['draft'])
    previous = rule['versions'][-1]['content'] if rule['versions'] else {}
    if rule['versions'] and same_content(proposed,previous):
        raise ValueError('内容未变化，无需发布新版')
    number = len(rule['versions'])+1
    rule['versions'].append(dict(number=number, content=copy.deepcopy(proposed), published_by=collection.USER,
                                 source_version=rule.get('draft_source_version'),
                                 published_at=now(), changes=changes(previous, proposed) if previous else ['首次发布']))
    rule.update(proposed)
    rule['draft'] = None
    source_version = rule.pop('draft_source_version', None)
    if number == 1:
        rule.update(status='enabled', enabled=True)
    rule['publish_status'] = '已发布'
    event(rule, '发布', previous, proposed, version='v'+str(number), source_version=source_version)


def migrate_task_bindings(conn):
    """Bring existing demo tasks forward once, retaining their record snapshots."""
    marker='processing-rule-follow-latest-v1'
    if conn.execute('SELECT 1 FROM collection_meta WHERE key=?', (marker,)).fetchone():
        return
    from collection_processing import apply_rule_publication
    for rule in all_rules(conn):
        if rule.get('versions') and not rule.get('deleted'):
            apply_rule_publication(conn, rule)
    conn.execute('INSERT INTO collection_meta VALUES (?,?)', (marker,'1'))


def register(app, seeds, legacy_rules, editor):
    from processing_rule_store import permissions, allowed_types, name_conflict, setup
    import data_platform_refactor as platform
    app.config.update(PROCESSING_RULE_SEEDS=seeds, PROCESSING_RULE_LEGACY=legacy_rules)
    app.config['PROCESSING_RULE_PROJECTS'] = list(dict.fromkeys(
        [p['name'] for p in app.config.get('COLLECTION_PROJECTS', [])] +
        [p['name'] for p in platform.PROJECT_MANAGEMENT_ITEMS] + [r['project'] for r in seeds]))

    def find(conn, rule_id):
        return next((r for r in all_rules(conn) if r['id'] == rule_id and not r.get('deleted')), None)

    def conflict(rule, body):
        return type(body.get('revision')) is not int or body['revision'] != rule['revision']

    @app.get(API)
    def list_processing_rule_versions():
        project = request.args.get('project', '')
        rules = [r for r in catalog(seeds) if (not project or r['project'] == project) and permissions(r['project'])['view']]
        versions = [view(r, v['number']) for r in rules for v in r['versions']]
        return jsonify(rules=[r for r in rules if r['versions'] and r.get('status') == 'enabled' and permissions(r['project'])['use']],
                       published_versions=versions, rule_labels={r['value']:r['name']+' · '+r['version'] for r in versions},
                       permissions=permissions(project))

    @app.get(API+'/<rule_id>')
    def get_processing_rule_version(rule_id):
        with collection.database() as conn:
            rule = find(conn, rule_id)
        if rule and not permissions(rule['project'])['view']:
            return jsonify(error='没有查看规则权限'),403
        return (jsonify(rule=view(rule), permissions=permissions(rule['project'])) if rule else (jsonify(error='规则不存在'),404))

    @app.get(API+'/preview')
    def preview_processing_rule():
        """Read exactly the selected publication or the server-owned task binding."""
        value = request.args.get('value', '')
        project = request.args.get('project', '')
        stage = request.args.get('stage', '')
        identity = None
        with collection.database() as conn:
            if task_id := request.args.get('task_id'):
                import collection_processing as processing
                job = processing.get_job(conn, task_id)
                project = next((p['name'] for p in current_app.config['COLLECTION_PROJECTS']
                                if p['id'] == job['project']), job['project'])
                if not permissions(project)['view']:
                    return jsonify(error='没有查看规则权限'),403
                node = request.args.get('node', '')
                flow = next((f for f in current_app.config['COLLECTION_PROCESSING_FLOWS']
                             if f['name'] == job['stages'].get(stage) and f['stage'] == stage), None)
                if not flow or node not in flow.get('human_nodes', []):
                    return jsonify(error='任务节点不存在'),404
                # Inherited nodes use the preceding node's binding; never a catalog default.
                while flow.get('node_rule_configs', {}).get(node, {}).get('mode') == 'inherit':
                    position = flow['human_nodes'].index(node)
                    if position == 0:
                        return jsonify(error='未找到继承的规则'),404
                    node = flow['human_nodes'][position-1]
                if flow.get('node_rule_configs', {}).get(node, {}).get('mode') == 'none':
                    return jsonify(error='该节点无需配置规则'),404
                config = job.get('configs', {}).get(stage, {}).get(node, {})
                value = config.get('rule', '')
                identity = config.get('rule_identity')
            if not project or not permissions(project)['view']:
                return jsonify(error='没有查看规则权限'),403
            if identity and identity.get('content'):
                preview = dict(identity['content'], id=identity.get('id'), version=identity['version'])
            else:
                rule = resolve(conn, value)
                if not rule and not str(value).startswith('rule:'):
                    old = legacy(value, stage)
                    matches = [r for r in all_rules(conn) if old and not r.get('deleted')
                               and r['name'] == old['name'] and r['project'] == project
                               and r['stage'] == stage]
                    if len(matches) == 1:
                        rule = resolve(conn, 'rule:'+matches[0]['id']+'@'+str(old['version']).lower().removeprefix('v'))
                if not rule:
                    return jsonify(error='该版本的规则内容暂不可用，请联系规则维护人'),404
                preview = dict(content(rule), id=rule['id'], version=rule['version'])
            if preview.get('project') != project or (stage and preview.get('stage') != stage):
                return jsonify(error='规则与任务项目或业务环节不匹配'),403
            if preview.get('rule_type') == '标签标注':
                import quanta_eval_platform as ep
                labels = {}
                def collect_labels(items, parents=()):
                    for item in items:
                        path = (*parents, item.get('name', item.get('id', '')))
                        labels[item.get('id')] = ' / '.join(path)
                        collect_labels(item.get('tags', item.get('sub_tags', [])), path)
                collect_labels(ep.tag_management_dimensions())
                preview['annotation_tag_labels'] = [labels.get(tag, tag) for tag in preview.get('annotation_tags', [])]
            # Return only the bound content, never draft bodies or other versions.
            return jsonify(rule=preview)

    @app.get(API+'/<rule_id>/usage')
    def processing_rule_usage(rule_id):
        import collection_processing as processing
        with collection.database() as conn:
            rule = find(conn,rule_id)
            if not rule:
                return jsonify(error='规则不存在'),404
            if not permissions(rule['project'])['view']:
                return jsonify(error='没有查看规则权限'),403
            tasks = [dict(id=job['id'],name=job['name']) for job in processing.all_jobs(conn)
                     if any(str(config.get('rule','')).startswith('rule:'+rule_id+'@')
                            for nodes in job.get('configs',{}).values() for config in nodes.values())]
        return jsonify(tasks=tasks)

    @app.get('/data/rules/editor-fragment')
    def editor_fragment():
        project = request.args.get('project', '')
        if request.args.get('readonly') == '1':
            if not permissions(project)['view']:
                abort(403)
            # Share the detail template without loading other rules or drafts.
            return editor([], project)
        if not (permissions(project)['create'] or permissions(project)['edit']):
            abort(403)
        return editor([r for r in catalog(seeds) if permissions(r['project'])['view']], project)

    @app.get(API+'/check-name')
    def check_processing_rule_name():
        project = request.args.get('project', '').strip()
        if not (permissions(project)['create'] or permissions(project)['edit']):
            return jsonify(error='没有创建规则权限'),403
        duplicate = name_conflict(catalog(seeds),project,request.args.get('name','').strip(),request.args.get('exclude_id'))
        return jsonify(duplicate=duplicate,message='同一项目已有同名规则，请更换名称' if duplicate else '')

    @app.post(API)
    @app.put(API+'/<rule_id>')
    @app.post(API+'/<rule_id>/revisions')
    def save_processing_rule_version(rule_id=None):
        body = request.get_json(silent=True)
        if not isinstance(body,dict):
            return jsonify(error='规则内容无效'),422
        if not permissions(body.get('project',''))['edit' if rule_id else 'create']:
            return jsonify(error='没有创建或编辑规则权限'),403
        if type(body.get('publish',False)) is not bool:
            return jsonify(error='发布选项无效'),422
        if body.get('publish') and not permissions(body.get('project',''))['publish']:
            return jsonify(error='没有发布规则权限'),403
        try:
            proposed = validate_content(body)
            context = body.get('node_context')
            if context is not None:
                if not permissions(proposed['project'])['edit'] or not permissions(proposed['project'])['publish']:
                    return jsonify(error='没有新建并使用规则的权限'),403
                if not isinstance(context,dict):
                    raise ValueError('节点上下文无效')
                if context.get('stage', proposed['stage']) != proposed['stage']:
                    raise ValueError('规则与当前业务环节不匹配')
                flow = next((f for f in platform.PROCESSING_FLOWS if f['name']==context.get('flow') and f['stage']==proposed['stage']),None)
                node = context.get('node')
                if not flow or node not in flow.get('human_nodes',[]) or flow.get('node_rule_configs',{}).get(node,{}).get('mode','task_custom')!='task_custom':
                    raise ValueError('当前流程节点不允许新建规则')
                if context.get('project')!=proposed['project'] or proposed['rule_type'] not in allowed_types(flow):
                    raise ValueError('规则与当前项目或流程类型不匹配')
        except ValueError as error:
            return jsonify(error=str(error)),422
        key = request.headers.get('Idempotency-Key','')
        fingerprint = hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        with collection.database() as conn, conn:
            setup(conn)
            conn.execute('BEGIN IMMEDIATE')
            if rule_id:
                rule = find(conn,rule_id)
                if not rule:
                    return jsonify(error='规则不存在'),404
                if not permissions(rule['project'])['edit']:
                    return jsonify(error='没有编辑规则权限'),403
                if rule['versions']:
                    if not permissions(rule['project'])['publish']:
                        return jsonify(error='编辑已发布规则需要发布权限'),403
                    body['publish'] = True
                if rule['versions'] and any(proposed[k]!=rule[k] for k in IDENTITY):
                    return jsonify(error='名称、项目、业务环节和规则类型发布后不可修改，请创建新规则'),409
                if name_conflict(all_rules(conn),proposed['project'],proposed['name'],rule_id):
                    return jsonify(error='同一项目已有同名规则，请更换名称',field='name'),409
                if request.method=='PUT' and rule['versions']:
                    return jsonify(error='已发布内容不可覆盖，请通过编辑保存待发布修改'),403
                if conflict(rule,body):
                    return jsonify(error='规则已被其他操作更新，请重新打开后编辑'),409
                if body.get('restore_from') is not None:
                    return jsonify(error='历史版本仅供查看，编辑只能基于最新版本'),422
                before = rule.get('draft') or (rule['versions'][-1]['content'] if rule['versions'] else content(rule))
                if rule['versions'] and same_content(rule['versions'][-1]['content'],proposed):
                    if rule.get('draft') is not None:
                        event(rule,'撤销待发布修改',rule['draft'],proposed)
                        rule['draft']=None;rule.pop('draft_source_version',None)
                        rule['revision']+=1;rule['updated_at']=now();persist(conn,rule)
                        return jsonify(rule=view(rule),unchanged=True),200
                    return jsonify(rule=view(rule), unchanged=True),200
                if same_content(before,proposed) and not rule['versions']:
                    return jsonify(rule=view(rule), unchanged=True),200
                rule['draft'] = proposed
                rule.pop('draft_source_version',None)
                if rule['versions'] and not body.get('publish') and same_content(proposed,rule['versions'][-1]['content']):
                    rule['draft'] = None
                    rule.pop('draft_source_version',None)
                if not body.get('publish'):
                    event(rule,'保存修改' if rule.get('draft') is not None else '撤销待发布修改',before,proposed)
                    rule['pending_saved_by']=collection.USER; rule['pending_saved_at']=now()
            else:
                if not key or len(key)>100:
                    return jsonify(error='缺少有效的创建请求标识'),422
                old = conn.execute('SELECT fingerprint,payload FROM processing_rules WHERE request_key=?',(collection.USER+':'+key,)).fetchone()
                if old:
                    if old['fingerprint']!=fingerprint or json.loads(old['payload']).get('deleted'):
                        return jsonify(error='请求内容已变化或规则已删除，请重新提交'),409
                    return jsonify(rule=view(json.loads(old['payload']))),200
                if name_conflict(all_rules(conn),proposed['project'],proposed['name']):
                    return jsonify(error='同一项目已有同名规则，请更换名称',field='name'),409
                rule=dict(proposed,id='PR-'+uuid.uuid4().hex[:12],owner=collection.USER,created=now(),
                          publish_status='未发布',status='disabled',enabled=False,versions=[],draft=proposed,events=[],revision=0,
                          pending_saved_by=collection.USER,pending_saved_at=now())
                event(rule,'创建')
            try:
                if body.get('publish'):
                    publish(rule)
            except ValueError as error:
                return jsonify(error=str(error)),422
            rule['revision']+=1
            rule['updated_at']=now()
            if not rule['versions']:
                rule.update(proposed)
            if rule_id:
                persist(conn,rule)
                if body.get('publish'):
                    from collection_processing import apply_rule_publication
                    apply_rule_publication(conn, rule)
            else:
                conn.execute('INSERT INTO processing_rules VALUES(?,?,?,?)',(rule['id'],collection.USER+':'+key,fingerprint,json.dumps(rule,ensure_ascii=False)))
            return jsonify(rule=view(rule)),200 if rule_id else 201

    @app.delete(API+'/<rule_id>/draft')
    def discard_processing_revision(rule_id):
        body = request.get_json(silent=True) or {}
        if not isinstance(body,dict):
            return jsonify(error='操作内容无效'),422
        with collection.database() as conn,conn:
            setup(conn); conn.execute('BEGIN IMMEDIATE')
            rule=find(conn,rule_id)
            if not rule:
                return jsonify(error='规则不存在'),404
            if not permissions(rule['project'])['edit']:
                return jsonify(error='没有编辑规则权限'),403
            if conflict(rule,body):
                return jsonify(error='规则已更新，请重新打开'),409
            if not rule['versions'] or rule.get('draft') is None:
                return jsonify(error='没有待发布修改'),422
            event(rule,'撤销待发布修改',rule['draft'],None)
            rule.pop('draft_source_version',None)
            rule['draft']=None; rule['revision']+=1; persist(conn,rule)
        return jsonify(rule=view(rule))

    @app.before_request
    def mutate_versioned_rule():
        match=re.fullmatch(r'/data/rules/([^/]+)(?:/(publish|status))?',request.path)
        if not match or request.method not in ('POST','DELETE'):
            return None
        rule_id,action=match.groups()
        body=request.get_json(silent=True) or {}
        if not isinstance(body,dict):
            return jsonify(error='操作内容无效'),422
        with collection.database() as conn,conn:
            setup(conn); conn.execute('BEGIN IMMEDIATE')
            rule=find(conn,rule_id)
            if not rule:
                return jsonify(error='规则不存在'),404
            permission='publish' if action=='publish' else 'manage' if action=='status' else 'edit'
            if not permissions(rule['project'])[permission]:
                return jsonify(error='没有操作规则的权限'),403
            if request.method=='DELETE' and rule['versions']:
                return jsonify(error='已发布规则不可删除'),403
            if action!='status' and conflict(rule,body):
                return jsonify(error='规则已更新，请重新打开'),409
            if action=='status' and 'revision' in body and conflict(rule,body):
                return jsonify(error='规则已更新，请重新打开'),409
            if request.method=='DELETE':
                rule['deleted']=True; event(rule,'删除')
            elif action=='publish':
                try:
                    if name_conflict(all_rules(conn),rule['project'],rule['name'],rule_id):
                        raise ValueError('同一项目已有同名规则，请更换名称')
                    publish(rule)
                except ValueError as error:
                    return jsonify(error=str(error)),422
            elif action=='status':
                status=body.get('status')
                if status not in ('enabled','disabled') or (status=='enabled' and not rule['versions']):
                    return jsonify(error='启用状态无效或规则尚未发布'),422
                event(rule,'启用' if status=='enabled' else '停用',status_before=rule.get('status'),status_after=status)
                rule.update(status=status,enabled=status=='enabled')
            else:
                return None
            rule['revision']+=1; persist(conn,rule)
            if action == 'publish':
                from collection_processing import apply_rule_publication
                apply_rule_publication(conn, rule)
            return jsonify(rule=view(rule),status=rule['status'],publish_status=rule['publish_status'])

    @app.after_request
    def inject_versioned_rules_ui(response):
        if request.path=='/data/processing-tasks' and response.status_code==200 and response.mimetype=='text/html':
            response.set_data(response.get_data(as_text=True).replace('</body>','<link rel="stylesheet" href="/static/post_training_collection/inline-rules.css"><link rel="stylesheet" href="/static/post_training_collection/rule-preview.css"><script src="/static/post_training_collection/inline-rules.js" defer></script><script src="/static/post_training_collection/rule-preview.js" defer></script></body>'))
        return response
