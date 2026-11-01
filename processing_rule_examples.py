"""Small deterministic revision example; never overwrite saved user rules."""
import copy
import hashlib
import json
from processing_rule_versions import changes, content

RULE_ID = 'RL-011'


def examples():
    v1=dict(name='饮茶Demo质检标准',project='亮剑',stage='质检',rule_type='质检',semantic_mode='',
        rule_config='',semantic_text='',quality_mistakes=['抓取动作未完成','物体在移动中滑落','出现明显碰撞'],
        quality_unqualified=['关键操作被遮挡','轨迹数据不完整'],annotation_tags=[],action_elements=[],
        action_descriptions=[],error_reasons=[dict(name='结论判断不准确'),dict(name='标准遗漏')],desc='质检')
    v2=copy.deepcopy(v1);v2['quality_unqualified'].append('视频严重模糊')
    stamps=['2026-10-28 10:20:00','2026-10-29 14:30:00']
    versions=[dict(number=i+1,content=copy.deepcopy(c),published_by='joanna.qiao',published_at=stamps[i],
        changes=['首次发布'] if i==0 else changes(v1,v2)) for i,c in enumerate([v1,v2])]
    result = [dict(v2,id=RULE_ID,owner='joanna.qiao',created=stamps[0],status='enabled',enabled=True,
        publish_status='已发布',versions=versions,draft=None,revision=2,demo_fixture='rule-versions-v1',
        events=[dict(action='发布',actor='joanna.qiao',at=stamps[i],version='v'+str(i+1),changes=v['changes'])
                for i,v in enumerate(versions)])]
    base=dict(project='亮剑',stage='标注',semantic_mode='',rule_config='',semantic_text='',
        quality_mistakes=[],quality_unqualified=[],annotation_tags=[],action_elements=[],action_descriptions=[],
        error_reasons=[dict(name='动作边界不准确'),dict(name='操作对象或目标位置错误'),dict(name='关键动作遗漏')])
    samples=[
        dict(id='RL-012',name='杯子抓取动作标注规范',rule_type='动作标注',
            action_elements=[
                dict(name='操作对象',key='object',values=[dict(name='陶瓷杯',key='ceramic_cup'),dict(name='玻璃杯',key='glass_cup')]),
                dict(name='目标位置',key='target',values=[dict(name='托盘',key='tray'),dict(name='桌面标记区',key='table_mark')])],
            action_descriptions=[dict(zh='抓取{操作对象}',en='Grasp {object}'),
                dict(zh='将{操作对象}放置到{目标位置}',en='Place {object} on {target}'),
                dict(zh='松开夹爪并退回安全位置',en='Release the gripper and return to the safe position')]),
        dict(id='RL-013',name='饮料取放质量标签规范',rule_type='标签标注',
            annotation_tags=['q_success','q_failed','q_operator_error'],
            error_reasons=[dict(name='采集结论标签与画面不符'),dict(name='同一段数据标记了互斥结论')]),
        dict(id='RL-014',name='饮茶动作语义切分规范',rule_type='语义标注',semantic_mode='text',
            semantic_text='将一次完整饮茶动作切分为“拿杯—送至嘴边—饮用—放回”四个阶段。\n\n1. 拿杯：从夹爪开始接近杯子，到杯子离开桌面；描述中标明操作手和杯子。\n2. 送至嘴边：杯子离开桌面后，到杯口到达嘴边；不要把明显停顿合并到饮用阶段。\n3. 饮用：从杯口接触嘴边或杯身开始倾斜，到杯子离开嘴边。\n4. 放回：从杯子离开嘴边，到杯子稳定放回且夹爪松开。\n\n以画面实际发生的动作为准；失败或中止的片段保留实际动作，不补写未发生的阶段。相邻阶段边界不得重叠。'),
        dict(id='RL-015',name='饮茶动作采集飞书说明',rule_type='语义标注',semantic_mode='link',
            rule_config='https://nwd4iy9rd2s.feishu.cn/wiki/R1yZwxGaFiTs34koqYDcoKPmnk2',
            error_reasons=[dict(name='与规范中的动作要求不一致'),dict(name='遗漏关键阶段')]),
    ]
    for sample in samples:
        rule=dict(base,**{k:v for k,v in sample.items() if k!='id'})
        rule['desc']=rule.get('semantic_text','')[:120] or rule['rule_type']
        published=dict(number=1,content=copy.deepcopy(rule),published_by='joanna.qiao',published_at=stamps[1],changes=['首次发布'])
        result.append(dict(rule,id=sample['id'],owner='joanna.qiao',created=stamps[1],status='enabled',enabled=True,
            publish_status='已发布',versions=[published],draft=None,revision=1,demo_fixture='rule-preview-examples-v1',
            events=[dict(action='发布',actor='joanna.qiao',at=stamps[1],version='v1',changes=['首次发布'])]))
    # The original processing form opens in this project. Give its existing
    # legacy choices real, explicitly synthetic content as well.
    for rule_id, name, template, count in [
        ('RL-016', '通用质检规则', result[0], 3),
        ('RL-017', '自动化质检规则', result[0], 2),
        ('RL-018', '通用动作标注规则', result[1], 3),
        ('RL-019', 'DAgger 质检规则', result[0], 1),
    ]:
        rule = content(template)
        rule.update(name=name, project='预训练采集')
        if rule['stage'] == '质检':
            rule.update(quality_mistakes=[
                '夹爪未稳定抓住目标物体，或搬运过程中物体滑落。',
                '物体未放入指定区域，或放置后倾倒。',
                '机械臂与桌面、容器或其他物体发生明显碰撞。'],
                quality_unqualified=[
                    '抓取或放置的关键阶段被遮挡，无法判断动作结果。',
                    '视频缺帧或轨迹时间戳不连续，无法完整回放。'],
                error_reasons=[dict(name='采集结果判断错误'),dict(name='遗漏不合格标准'),dict(name='问题时间段定位不准确')])
        versions=[]
        previous=None
        for number in range(1,count+1):
            published=copy.deepcopy(rule)
            if number>=2 and rule['stage']=='质检':
                published['quality_unqualified'].append('画面持续模糊，无法辨认夹爪与物体接触状态。')
            if number>=3 and rule['stage']=='质检':
                published['quality_unqualified'].append('主要相机与轨迹时间未对齐，无法对应关键动作。')
            if number>=2 and rule['rule_type']=='动作标注':
                published['action_descriptions'].append(dict(zh='接近{操作对象}',en='Approach {object}'))
            if number>=3 and rule['rule_type']=='动作标注':
                published['action_descriptions'].append(dict(zh='移动至{目标位置}',en='Move to {target}'))
            versions.append(dict(number=number,content=published,published_by='joanna.qiao',
                published_at=f'2026-10-{26+number:02d} 10:20:00',
                changes=changes(previous,published) if previous else ['首次发布']))
            previous=published
        result.append(dict(previous,id=rule_id,owner='joanna.qiao',created=versions[0]['published_at'],
            status='enabled',enabled=True,publish_status='已发布',versions=versions,draft=None,
            revision=count,demo_fixture='rule-preview-examples-v1',
            events=[dict(action='发布',actor=v['published_by'],at=v['published_at'],
                version='v'+str(v['number']),changes=v['changes']) for v in versions]))
    return result


def link_demo_jobs(conn):
    from flask import current_app
    from processing_rule_versions import snapshot_reference
    import collection_processing as processing
    if not any(r['id']==RULE_ID for r in current_app.config.get('PROCESSING_RULE_SEEDS',[])):
        return
    marker='rule-version-links-v1'
    if not conn.execute('SELECT 1 FROM collection_meta WHERE key=?',(marker,)).fetchone():
        versions={'杯子抓取首批复核':1,'饮料取放质检与标注':2}
        for job in processing.all_jobs(conn):
            version=versions.get(job['name'])
            if not version or job.get('revision')!=1 or not job.get('demo_fixture','').startswith('collection-linked-demo-'):
                continue
            for config in job.get('configs',{}).get('质检',{}).values():
                config.update(rule=f'rule:{RULE_ID}@{version}',rule_identity=snapshot_reference(conn,f'rule:{RULE_ID}@{version}'))
            processing.save_job(conn,job)
        conn.execute('INSERT INTO collection_meta VALUES (?,?)',(marker,'1'))
    seed_preview_examples(conn)
    # Older owned collection fixtures only stored generic rule names. Complete
    # untouched fixture bindings; never rewrite user jobs or an existing binding.
    for job in processing.all_jobs(conn):
        if job.get('revision') != 1 or not job.get('demo_fixture', '').startswith('collection-linked-demo-'):
            continue
        changed=False
        for stage,nodes in job.get('configs', {}).items():
            for config in nodes.values():
                if config.get('rule_identity', {}).get('content') or str(config.get('rule', '')).startswith('rule:'):
                    continue
                if stage=='质检' and config.get('rule') in ('通用质检规则','通用质检规则 v3'):
                    value='rule:RL-011@2'
                elif stage=='标注' and config.get('rule') in ('通用动作标注规则','通用动作标注规则 v3'):
                    value='rule:RL-013@1' if job['name']=='饮料取放质检与标注' else 'rule:RL-012@1'
                else:
                    continue
                identity=snapshot_reference(conn,value)
                project=next((p['name'] for p in current_app.config['COLLECTION_PROJECTS'] if p['id']==job['project']),job['project'])
                if identity and identity.get('content',{}).get('project')==project:
                    config.update(rule=value,rule_identity=identity);changed=True
        if changed:
            processing.save_job(conn,job)


def seed_preview_examples(conn):
    """Complete a small number of owned fixtures, and add two useful walkthroughs."""
    from flask import current_app
    import collection_processing as processing
    import post_training_collection as collection
    from processing_rule_versions import snapshot_reference
    marker='rule-preview-examples-v1'
    if conn.execute('SELECT 1 FROM collection_meta WHERE key=?',(marker,)).fetchone():
        return
    if not {'RL-012','RL-013','RL-014','RL-015'}.issubset({r['id'] for r in current_app.config.get('PROCESSING_RULE_SEEDS',[])}):
        return
    for job in processing.all_jobs(conn):
        if job.get('revision')!=1 or not job.get('demo_fixture','').startswith('collection-linked-demo-'):
            continue
        rule_id={'杯子抓取动作标注':'RL-012','饮料取放质检与标注':'RL-013'}.get(job['name'])
        if not rule_id:
            continue
        changed=False
        for config in job.get('configs',{}).get('标注',{}).values():
            if config.get('rule_identity', {}).get('content') or str(config.get('rule','')).startswith('rule:'):
                continue
            value=f'rule:{rule_id}@1'
            config.update(rule=value,rule_identity=snapshot_reference(conn,value));changed=True
        if changed:
            processing.save_job(conn,job)
    flows=current_app.config['COLLECTION_PROCESSING_FLOWS']
    for index,(name,stage,flow_name,refs) in enumerate([
        ('杯子抓取补采复核','质检','双轮人工质检流程',['rule:RL-011@2','rule:RL-011@2']),
        ('饮茶动作语义标注','标注','双轮人工标注流程',['rule:RL-014@1','rule:RL-015@1'])]):
        key=marker+'-'+str(index)
        if conn.execute('SELECT 1 FROM collection_processing WHERE request_key=?',(key,)).fetchone():
            continue
        flow=next((f for f in flows if f['name']==flow_name and f['stage']==stage),None)
        if not flow:
            continue
        configs={stage:{node:dict(rule=refs[min(i,len(refs)-1)],percent=100,
            assignments=[dict(type='user_group',target='质检复核用户组' if stage=='质检' else '标注员用户组')])
            for i,node in enumerate(flow['human_nodes'])}}
        task=collection.get_task(conn,'02602')
        records=[r for r in task['records'] if r['upload']=='uploaded'][10:14]
        if not records:
            continue
        body=dict(name=name,source_ids=['02602'],priority=6,category='formal',expected_mode='continuous',
            filters=[['采集任务 ID','等于','02602'],['数据 ID','等于',','.join(r['id'] for r in records)]],
            stages={stage:flow_name},configs=configs)
        job,error=processing.validate(conn,body,flows)
        if error:
            # User may have disabled or edited a sample rule. Never overwrite it.
            continue
        job_id=str(max([30000,*[int(r['id']) for r in conn.execute('SELECT id FROM collection_processing')]])+1)
        if len(job_id)>5:
            continue
        stamp=collection.now()
        job.update(id=job_id,published=True,enabled=True,revision=1,records=[],creator='joanna.qiao',
            created_at=stamp,updated_at=stamp,demo_fixture=marker,
            events=[dict(at=stamp,actor='joanna.qiao',title='创建处理任务')])
        processing.admit(conn,job)
        payload=json.dumps(job,ensure_ascii=False)
        conn.execute('INSERT INTO collection_processing VALUES (?,?,?,?)',
            (job_id,key,hashlib.sha256(payload.encode()).hexdigest(),payload))
    conn.execute('INSERT INTO collection_meta VALUES (?,?)',(marker,'1'))
