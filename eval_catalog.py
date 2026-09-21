"""Scene-library definitions and executable case composition for the local demo.

Source examples: 模型评测体系-场景库 / 场景库目录、skill标签、Factor配置、
Factor取值说明、eval场景集. Descriptions/acceptance criteria are demo supplements.
Browser-specific data is stored locally; no writes to the source Feishu base.
"""
from flask import abort, render_template, request, redirect
from data_platform_refactor import USER_GROUPS

BASE = '/model/eval/'
CATALOG_PATH = BASE + 'catalog'
ENTITIES = {
    'stages': ('Stage 定义', '维护评测大类与场景域，组织 Story。'),
    'stories': ('Story 定义', '定义任务目标、专项类型及所属 Stage。'),
    'skills': ('Skill 定义', '维护可跨场景复用的能力标签与判定说明。'),
    'factors': ('Factor 定义', '定义影响因素、标准取值与取值说明。'),
    'test-cases': ('评测用例', '组合场景、能力和条件，形成可执行的评测用例。'),
}
SOURCE = 'https://nwd4iy9rd2s.feishu.cn/base/WEMab2WMyaeVUfsTQJlc7WrFn2d'


def seed_data():
    def record(code, name, **fields):
        return dict(id=code, name=name, publish_status='已发布', enabled=True, description='', owner='评测团队',
                    created_at='2026-09-17 09:00', updated_at='2026-09-17 09:00', **fields)
    stages = [record('ST_BM', '预训练Benchmark评测', category='能力专项'),
              record('ST_BASIC', '基础能力评测', category='能力专项'),
              record('ST_STUDY', '书房', category='场景专项'),
              record('ST_KITCHEN', '厨房餐厅', category='场景专项')]
    stories = [record(code, name, stage_id=stage, category=category, goal=goal) for code,name,stage,category,goal in [
        ('SR_IDENTIFY','【专项】物品识别基准测试','ST_BM','能力专项','根据尺寸、颜色等属性识别目标物体'),
        ('SR_PICK','【专项】抓取基准测试','ST_BM','能力专项','按指令抓取目标物体'),
        ('SR_PLACE','【专项】放置基准测试','ST_BM','能力专项','将目标物体放置到指定位置'),
        ('SR_READ','看书','ST_STUDY','场景专项','取书、开书并翻到指定页面'),
        ('SR_STORE','放书','ST_STUDY','场景专项','打开柜门，将书放入柜中并关门'),
        ('SR_POUCH','拉链','ST_STUDY','场景专项','打开收纳袋并放入文具'),
        ('SR_BREAKFAST','准备早餐','ST_KITCHEN','场景专项','拿取杯子和牛奶，倒奶并清理溢出液体'),
        ('SR_FOLD','MopFolding','ST_KITCHEN','场景专项','折叠与展开抹布'),
        ('SR_KETTLE','WaterKettle','ST_KITCHEN','场景专项','按动水壶开关启动烧水'),
    ]]
    skills = [record(code,name,name_en=en,category=cat,criterion=criterion) for code,name,en,cat,criterion in [
        ('SK_PICK','抓取能力','Pick','操作能力','稳定抓起指定物体，无掉落'),
        ('SK_PLACE','放置能力','Place','操作能力','物体稳定落在指定目标区域'),
        ('SK_SIZE','物品尺寸辨别','Sizing','感知能力','从不同尺寸物体中选择符合指令的目标'),
        ('SK_COLOR','物品颜色辨别','Color','感知能力','正确识别指令指定的颜色'),
        ('SK_SHAPE','物品形状辨别','Shape','感知能力','正确识别指定形状物体'),
        ('SK_PULL','拉动','Pull','操作能力','沿预期方向拉开目标'),
        ('SK_PUSH','推动','Push/Close','操作能力','推至指定位置或关闭目标'),
        ('SK_TURN','翻','Turn','操作能力','完成指定的翻转或翻页动作'),
        ('SK_FOLD','折叠','Fold','操作能力','按目标形状完成折叠'),
        ('SK_UNFOLD','展开','Unfold','操作能力','将折叠物展开并放平'),
        ('SK_PRESS','按','Press','操作能力','按下目标开关'),
        ('SK_POUR','倾倒','Pour','操作能力','液体进入指定容器'),
        ('SK_TOOL','工具操作','Tool Use','操作能力','使用指定工具完成任务'),
        ('SK_CLEAN','打扫','Clean','操作能力','清除指定区域的污渍或液体'),
    ]]
    factors = []
    for code,name,category,dimension,values in [
        ('FC_SIZE','尺寸','被操作物品属性','几何属性',[('小','同组物体中尺寸较小'),('适中','同组物体中尺寸居中'),('大','同组物体中尺寸较大')]),
        ('FC_MATERIAL','物体材质','被操作物品属性','物体材质',[(v,v+'材质的目标物') for v in ['塑料','木头','金属','陶瓷','纸','布料','玻璃']]),
        ('FC_COLOR','颜色','被操作物品属性','视觉属性',[(v,'目标物体颜色为'+v) for v in ['橙色','绿色','红色','紫色']]),
        ('FC_SHAPE','物体形状','被操作物品属性','几何属性',[(v,'目标物体呈'+v) for v in ['圆柱','长方体','球体','圆形']]),
        ('FC_POSITION','目标位置','任务结构','空间约束',[('受限空间','放入柜子、袋子等受限空间'),('特定位置','放入指定目标区域'),('任意位置','无特定目标位置要求')]),
        ('FC_DIRECTION','方位理解','指令语言','空间表达',[(v,'指令指定'+v+'方向') for v in ['左','中','右','左前','右后']]),
        ('FC_DISTRACTOR','干扰物','环境条件','场景布局',[('同类异例','存在同类别的其他实例'),('无干扰','无其他干扰物')]),
        ('FC_BACKGROUND','背景复杂度','环境条件','场景布局',[('简单','背景物体稀少'),('中等','存在多个背景物体'),('稠密','背景物体密集')]),
        ('FC_COUNT','对象数量','任务结构','对象数量',[('单一对象','一个操作对象'),('固定多对象','固定数量的多个对象')]),
        ('FC_PHYSICS','物理属性','被操作物品属性','物理属性',[('刚性','操作中形状稳定'),('柔性','操作中可变形'),('流体','液体操作')]),
        ('FC_EXPRESSION','动作表达方式','指令语言','语义表达',[('标准表达','常规动作描述'),('同义替换','使用同义词描述相同动作')]),
        ('FC_OCCLUSION','遮挡','环境条件','场景布局',[('无遮挡','目标物完整可见'),('部分遮挡','目标部分被遮挡'),('遮挡','目标大部分被遮挡')]),
    ]:
        factors.append(record(code,name,category=category,dimension=dimension,data_type='枚举',
                              values=[{'value':v,'description':d} for v,d in values],default_value=values[0][0]))
    cases=[]
    def case(code,name,story,prompt,skills,conditions,props,previous=None,priority='P1'):
        cases.append(record(code,name,story_id=story,prompt=prompt,skill_ids=skills,
                     factors=[{'factor_id':f,'value':v} for f,v in conditions],props=props,
                     prerequisite_ids=previous or [],priority=priority,
                     setup='按道具与 Factor 配置准备初始场景。',
                     expected_result='完成指令指定动作；目标物保持稳定，操作过程中无掉落。',
                     notes='参考场景库样例；布置说明与预期结果为演示补充。',attachments=[]))
    case('BM_05','中等大小碗入盒','SR_IDENTIFY','Pick up the medium-sized bowl and place it in the box',['SK_SIZE','SK_PICK','SK_PLACE'],[('FC_SIZE','适中')],'大、中、小三个碗；盒子',priority='P0')
    case('BM_06','最小碗入盒','SR_IDENTIFY','Pick up the smallest bowl and place it into the box',['SK_SIZE','SK_PICK','SK_PLACE'],[('FC_SIZE','小')],'大、中、小三个碗；盒子',priority='P0')
    case('BM_07','塑料勺放入架子','SR_IDENTIFY','Pick up the plastic spoon and place it into the wire rack',['SK_PICK','SK_PLACE'],[('FC_MATERIAL','塑料')],'陶瓷勺子、塑料勺子、金属勺子；置物架',priority='P0')
    case('BM_10','陶瓷勺入盒','SR_IDENTIFY','Pick up the ceramic spoon and place it into the box',['SK_PICK','SK_PLACE'],[('FC_MATERIAL','陶瓷'),('FC_POSITION','受限空间')],'陶瓷勺子、塑料勺子；盒子',priority='P0')
    case('BM_14','橙色糖果入盒','SR_IDENTIFY','Pick up the orange candy and put the candy into the box',['SK_PICK','SK_PLACE','SK_COLOR'],[('FC_COLOR','橙色')],'多种颜色糖果；盒子',priority='P0')
    case('BM_22','抓取紫色物品','SR_IDENTIFY','Pick up the purple item',['SK_PICK','SK_COLOR'],[('FC_COLOR','紫色')],'紫色物品（茄子）及其他物品',priority='P0')
    case('BM_31','抓取盒后糖果','SR_PICK',"Get the candy that’s behind the box",['SK_PICK'],[('FC_EXPRESSION','同义替换')],'盒子；盒子后方的一颗糖',priority='P0')
    case('BM_37','抓取左前方瓶子','SR_PICK','Pick up the bottle on the left-front',['SK_PICK'],[('FC_DIRECTION','左前')],'桌子；四个瓶子（2×2）',priority='P0')
    case('BM_51','仿真饺子入盒','SR_PLACE','Pick up the simulated dumpling and put it in the plastic box',['SK_SIZE','SK_PICK','SK_PLACE','SK_SHAPE'],[('FC_DISTRACTOR','同类异例')],'仿真饺子；纸盒子、塑料盒子',priority='P0')
    case('Study_47','从书架取书','SR_READ','Grab a book from the bookshelf and put it on the table',['SK_PICK'],[('FC_SHAPE','长方体'),('FC_MATERIAL','纸')],'书架；书；桌子')
    case('Study_48','打开书本','SR_READ','Grasp and lift the book cover to open the book',['SK_TURN'],[('FC_MATERIAL','纸')],'书',['Study_47'])
    case('Study_49','翻到书本中间','SR_READ','Flip to the middle of the book',['SK_TURN'],[('FC_MATERIAL','纸')],'书',['Study_48'])
    case('Study_54','打开柜门','SR_STORE','Open the door of the cabinet',['SK_PULL'],[],'可开关柜门的柜子')
    case('Study_55','从人手中接书','SR_STORE','Take the book from the person',['SK_PICK'],[('FC_SHAPE','长方体')],'书')
    case('Study_56','把书放入柜子','SR_STORE','Put the book into the cabinet',['SK_PLACE'],[('FC_POSITION','受限空间')],'书；柜子')
    case('Study_57','关闭柜门','SR_STORE','Close the door of the cabinet',['SK_PUSH'],[],'柜子',['Study_54'])
    case('Kit_05','折叠抹布','SR_FOLD','Fold the rag on the table into a quarter-sized square',['SK_FOLD'],[('FC_MATERIAL','布料')],'一块展开的抹布')
    case('Kit_06','展开抹布','SR_FOLD','Unfold the rag and lay it flat on the table',['SK_UNFOLD'],[('FC_MATERIAL','布料')],'一块抹布',['Kit_05'])
    case('Kit_11','按动水壶开关','SR_KETTLE','Flip the switch to start boiling the water.',['SK_PRESS'],[],'水壶')
    case('Kit_20','左手拿杯子','SR_BREAKFAST','Pick up a glass with the left hand',['SK_PICK'],[('FC_MATERIAL','玻璃'),('FC_SHAPE','圆柱')],'玻璃杯')
    case('Kit_21','右手拿牛奶瓶','SR_BREAKFAST','Pick up the milk bottle with the right hand',['SK_PICK'],[('FC_MATERIAL','塑料')],'牛奶瓶')
    case('Kit_22','倒牛奶','SR_BREAKFAST','Pour milk into the glass',['SK_POUR'],[('FC_PHYSICS','流体'),('FC_POSITION','特定位置')],'牛奶；玻璃杯',['Kit_21'])
    case('Kit_23','擦拭溢出液体','SR_BREAKFAST','Wipe spill with napkin',['SK_TOOL','SK_CLEAN'],[('FC_MATERIAL','纸')],'纸巾',['Kit_22'])
    prompt_translations = {
        'BM_05': '拿起中等大小的碗，将它放入盒子中。',
        'BM_06': '拿起最小的碗，将它放入盒子中。',
        'BM_07': '拿起塑料勺，将它放入金属丝置物架中。',
        'BM_10': '拿起陶瓷勺，将它放入盒子中。',
        'BM_14': '拿起橙色糖果，将它放入盒子中。',
        'BM_22': '拿起紫色物品。',
        'BM_31': '拿取盒子后面的糖果。',
        'BM_37': '拿起左前方的瓶子。',
        'BM_51': '拿起仿真饺子，将它放入塑料盒中。',
        'Study_47': '从书架上拿一本书，将它放在桌子上。',
        'Study_48': '抓住并掀起书的封面，打开书本。',
        'Study_49': '翻到书本的中间位置。',
        'Study_54': '打开柜门。',
        'Study_55': '从对方手中接过书。',
        'Study_56': '把书放入柜子中。',
        'Study_57': '关闭柜门。',
        'Kit_05': '将桌上的抹布折成面积为原来四分之一的正方形。',
        'Kit_06': '展开抹布，将它平铺在桌子上。',
        'Kit_11': '拨动开关，开始烧水。',
        'Kit_20': '用左手拿起玻璃杯。',
        'Kit_21': '用右手拿起牛奶瓶。',
        'Kit_22': '将牛奶倒入玻璃杯中。',
        'Kit_23': '用餐巾纸擦去洒出的液体。',
    }
    for row in cases:
        row['prompt_cn'] = prompt_translations[row['id']]
    stage_descriptions = {
        'ST_BM': '通过标准化指令验证预训练模型的物品识别、抓取与放置表现。',
        'ST_BASIC': '按原子能力组织基准测试，覆盖抓取、放置和物品辨别。',
        'ST_STUDY': '书房内的书本、柜门与文具操作场景。',
        'ST_KITCHEN': '厨房餐厅内的早餐准备、清洁和日常物品操作。',
    }
    for row in stages:
        row['description'] = stage_descriptions[row['id']]
    for row in stories:
        row['description'] = row['goal']
    for row in skills:
        row['description'] = row['criterion']
    for row in factors:
        row['description'] = f"{row['category']} / {row['dimension']}下的{row['name']}测试维度。"
    # Source field names are preserved in the UI; system IDs remain stable.
    for row in skills:
        row.update(name_zh=row['name'], action_descriptions=[], tool_usage=[], notes='', key_factor='')
        row['category'] = '辨别类' if row['category'] == '感知能力' else '动作类'
        row['action_descriptions'] = {
            'SK_PICK':['pick up','grasp','grab'], 'SK_PLACE':['place','put','set','lay','position'],
            'SK_TURN':['open','turn','flip','leaf','overturn'], 'SK_PULL':['pull','drag','draw','tug'],
            'SK_PRESS':['press','push down','depress'], 'SK_POUR':['pour','tip','spill','empty'],
            'SK_CLEAN':['clean','sweep','brush','wipe off'],
        }.get(row['id'],[])
        if row['id']=='SK_CLEAN': row['tool_usage']=['SK_TOOL']
    for row in factors:
        row['level3']=row['name']
        row['name']='-'.join([row['category'],row['dimension'],row['level3']])
        row['value_range']=' / '.join(v['value'] for v in row['values'])
        row['parent_id']=''
        for v in row['values']:
            v.update(example='', factor_id=row['id'], linked_factor_ids=[row['id']])
            for index in range(2,17):v['field_'+str(index)]=''
    for row in stories:
        related=[c for c in cases if c['story_id']==row['id']]
        row.update(skill_ids=list(dict.fromkeys(sk for c in related for sk in c['skill_ids'])),
                   factor_ids=list(dict.fromkeys(f['factor_id'] for c in related for f in c['factors'])),
                   factor_values='',notes='',text3='',parent_id='')
    for row in cases:
        row.update(data_owner='Eval-白盒',project='预训练评测',tag_ids=[],visibility='受限',updated_by='评测团队',factor_option_ids=[f['factor_id'] for f in row['factors']],text8='',
                   attributes='',attribute_values='',lookup_reference='',t4='',t5='')
    # Keep several draft cases visible in the catalog so publish-state filtering
    # and the disabled delete action have representative demo records.
    for row in cases:
        if row['id'] in {'Study_55', 'Kit_20', 'Kit_23'}:
            row['publish_status'] = '未发布'
            row['enabled'] = False
    draft_ids = {'ST_BASIC', 'SR_PICK', 'SR_KETTLE', 'SK_PRESS', 'SK_CLEAN', 'FC_COUNT', 'FC_OCCLUSION'}
    for rows in (stages, stories, skills, factors):
        for index, row in enumerate(rows, start=1):
            if rows is stages:
                row['project'] = '预训练评测' if row['id'] in ('ST_BM', 'ST_BASIC') else '后训练评测'
            elif rows is stories:
                row['project'] = next(stage['project'] for stage in stages if stage['id'] == row['stage_id'])
            else:
                row['project'] = '预训练评测' if index <= len(rows) // 2 else '后训练评测'
            if row['id'] in draft_ids:
                row['publish_status'] = '未发布'
            row['display_id'] = index
            row['created_by'] = ('Joanna Qiao', 'Lance Li', 'Min Chen')[(index - 1) % 3]
            row['updated_by'] = ('Joanna Qiao', 'Lance Li', 'Min Chen')[(index - 1) % 3]
            # Explicit demo history; snapshots end at the current seeded field values.
            if rows is stages:
                history_field, history_label = 'name', 'Stage 场域'
            elif rows is stories:
                history_field, history_label = 'name', 'Story 任务'
            elif rows is skills:
                history_field, history_label = 'name_zh', 'Skill_中文'
            else:
                history_field, history_label = 'level3', '三级（具体 factor）'
            current_value = row[history_field]
            row['update_history'] = [
                {'mock': True, 'updated_at': row['updated_at'], 'updated_by': row['updated_by'],
                 'changes': [{'field': history_field, 'label': history_label,
                              'before': current_value + '（初稿）', 'after': current_value,
                              'before_text': current_value + '（初稿）', 'after_text': current_value}]},
                {'mock': True, 'updated_at': '2026-09-16 16:30:00', 'updated_by': 'Lance Li',
                 'changes': [{'field': 'project', 'label': '所属项目',
                              'before': '后训练评测' if row['project'] == '预训练评测' else '预训练评测',
                              'after': row['project'],
                              'before_text': '后训练评测' if row['project'] == '预训练评测' else '预训练评测',
                              'after_text': row['project']}]},
            ]
    return {'stages':stages,'stories':stories,'skills':skills,'factors':factors,'test-cases':cases}


def register_catalog(app, render_page):
    def catalog_page(kind, section='elements'):
        if kind not in ENTITIES:
            abort(404)
        if section == 'scenario':
            kind = 'stories'
        title,description=ENTITIES[kind]
        page_title = '评测用例' if kind == 'test-cases' else '场景库'
        if section not in ('scenario', 'elements'):
            abort(404)
        user_groups=[{'id': group['id'], 'name': group['name']} for group in USER_GROUPS]
        from quanta_eval_platform import tag_management_dimensions
        tag_tree = tag_management_dimensions()
        tag_options = []
        def collect_tags(nodes, path):
            for node in nodes:
                names = path + [node['name']]
                tag_options.append({'id': node['id'], 'name': ' / '.join(names)})
                collect_tags(node.get('sub_tags', []), names)
        for dimension in tag_tree:
            collect_tags(dimension['tags'], [dimension['name']])
        content=render_template('eval_catalog/page.html',kind=kind,title=title,page_title=page_title,
                                description=description,section=section,seed=seed_data(),entities=ENTITIES,
                                source=SOURCE,user_groups=user_groups,tag_options=tag_options,tag_tree=tag_tree)
        return render_page(page_title,content,active=BASE+kind if kind == 'test-cases' else CATALOG_PATH,module='model')
    def catalog_home():
        kind=request.args.get('tab','stages')
        if kind not in ('stages','stories','skills','factors'):
            abort(404)
        section=request.args.get('section', 'elements' if 'tab' in request.args else 'scenario')
        return catalog_page(kind, section=section)
    app.add_url_rule(CATALOG_PATH, endpoint='catalog_home', view_func=catalog_home)
    for kind in ENTITIES:
        if kind == 'test-cases':
            app.add_url_rule(BASE+kind,endpoint='catalog_'+kind,view_func=catalog_page,defaults={'kind':kind})
        else:
            app.add_url_rule(BASE+kind,endpoint='catalog_'+kind,view_func=lambda kind=kind: redirect(CATALOG_PATH+'?section=elements&tab='+kind))
