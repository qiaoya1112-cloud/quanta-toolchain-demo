from pathlib import Path
from html import escape

OUT = Path(__file__).parent
parts = ['''<svg xmlns="http://www.w3.org/2000/svg" width="1820" height="1810" viewBox="0 0 1820 1810">
<defs>
<marker id="main" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9Z" fill="#718096"/></marker>
<marker id="loop" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9Z" fill="#C67A35"/></marker>
<marker id="lineage" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8Z" fill="#6088B5"/></marker>
</defs>
<rect width="1820" height="1810" fill="#FFFFFF"/>
<g font-family="PingFang SC, Microsoft YaHei, Arial, sans-serif">
''']

def text(x,y,s,size=20,color='#253449',weight=400,anchor='start'):
    parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(s)}</text>')

def rect(x,y,w,h,fill,stroke='#DFE5ED',r=14):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')

def path(d,kind='main',width=2.4):
    colors={'main':'#718096','loop':'#C67A35','lineage':'#6088B5'}
    dash=' stroke-dasharray="8 7"' if kind=='loop' else ''
    parts.append(f'<path d="{d}" fill="none" stroke="{colors[kind]}" stroke-width="{width}"{dash} marker-end="url(#{kind})"/>')

def card(x,y,w,title,detail,fill,stroke):
    rect(x,y,w,86,fill,stroke,10)
    text(x+w/2,y+34,title,22,weight=500,anchor='middle')
    text(x+w/2,y+64,detail,17,'#65758A',anchor='middle')

text(280,65,'Quanta｜模型迭代闭环与版本血缘',36,weight=600)
text(280,102,'从业务目标出发，以评测证据驱动改进，让每份数据与每个模型版本可追溯',20,'#68788C')
path('M1185 91 H1230'); text(1242,98,'主流程',17,'#65758A')
path('M1350 91 H1395','loop'); text(1407,98,'改进回流',17,'#65758A')
path('M1540 91 H1585','lineage'); text(1597,98,'版本血缘',17,'#65758A')

rows = [
    (150,'01','明确迭代目标与方案','#F1F4FC','#D6DEEE',[
        ('业务目标','明确任务 / 场景 / 技能'),('验收口径','成功定义 / 固定评测集'),('迭代方案','数据需求 / 基线模型 / 训练方案')],
        '迭代编号  ·  基线 Checkpoint  ·  评测集版本'),
    (400,'02','数据采集与处理','#EEF8F3','#CFE4D8',[
        ('采集指令下发','指令包 / 采集方案 / 任务分配'),('数据处理与验收','质检 / 动作与语义标注 / 复核返工')],
        '采集任务 ID  ·  数据 ID  ·  标注与处理版本'),
    (650,'03','构建训练数据集','#EFF8F3','#CFE4D8',[
        ('数据筛选','场景 / 标签 / 质量条件'),('可视化数据查看','样本内容 / 数量 / 分布'),('组配与版本化打包','示教 + DAgger / 配比 / 快照')],
        '数据集版本  ·  数据快照  ·  样本与来源关联'),
    (900,'04','训练执行','#F3EFFB','#DDD3ED',[
        ('训练发起','数据集 / 推荐配置 / 运行资源'),('训练观测与产物管理','进度 / 日志 / Checkpoint'),('模型部署','候选版本 / 目标设备')],
        '训练任务 ID  ·  配置与起点模型  ·  Checkpoint ID'),
    (1150,'05','模型评测与验收','#FFF7E7','#ECDEB9',[
        ('场景库与评价标准','目标场景 / 用例 / 评分标准'),('真机执行与记录','固定条件 / 执行过程 / 结果'),('结果分析与失败定位','总体对比 / 分场景 / Badcase')],
        '评测任务 ID  ·  评测记录 ID  ·  关联 Checkpoint / Badcase'),
]
for y,num,title,fill,stroke,cards,asset in rows:
    rect(280,y,1070,210,'#FBFCFE')
    rect(303,y+20,40,32,fill,stroke,8)
    text(323,y+43,num,18,weight=600,anchor='middle')
    text(360,y+46,title,25,weight=600)
    gap=24; w=(1006-gap*(len(cards)-1))/len(cards)
    for i,(t,d) in enumerate(cards):
        card(312+i*(w+gap),y+70,w,t,d,fill,stroke)
    text(313,y+189,'版本记录',16,'#6088B5',500)
    text(403,y+189,asset,17,'#68788C')

for y,label in [(360,'目标与执行方案'),(610,'验收合格数据'),(860,'固定数据集版本'),(1110,'候选模型')]:
    path(f'M815 {y+3} V{y+34}')
    text(836,y+28,label,16,'#748296')

# Evaluation feedback remains outside the forward workflow.
path('M280 1260 H145 V998','loop')
rect(30,790,230,200,'#FFF8EF','#E8D0B3')
text(145,830,'下一轮改进任务',23,'#82562B',600,'middle')
for i,s in enumerate(['定向补采 · 标注修正','数据重配 · 补充评测','依据问题证据安排迭代']):
    text(145,877+i*32,s,18,'#896D50',anchor='middle')
path('M145 790 V263 Q145 255 155 255 H276','loop')
text(32,729,'业务改进闭环',20,'#A46A32',500)
text(32,759,'更新目标与执行方案',17,'#8F7C65')

# DAgger consumes a specific checkpoint and diagnosed failure scenarios.
rect(1430,440,310,280,'#FFF8EF','#E5C9A7')
text(1585,482,'DAgger 纠正采集',25,'#82562B',600,'middle')
text(1585,525,'指定 Checkpoint 上机执行',19,'#79634B',anchor='middle')
text(1585,559,'人工接管，记录纠正过程',19,'#79634B',anchor='middle')
parts.append('<path d="M1454 589 H1716" stroke="#EAD8C1"/>')
text(1585,624,'保留来源模型 / 设备 / 失败类型',17,'#79634B',anchor='middle')
text(1585,658,'纠正数据经过质检与加工',18,'#82562B',500,'middle')
text(1585,691,'进入下一版训练数据集',18,'#82562B',500,'middle')
path('M1350 1020 H1585 V725','loop')
text(1604,833,'指定来源',18,'#A46A32')
text(1604,863,'Checkpoint',18,'#A46A32')
path('M1350 1260 H1777 V558 H1745','loop')
text(1460,1228,'失败场景与纠正需求',18,'#A46A32')
path('M1430 545 H1356','loop')
text(1390,390,'模型纠正闭环',20,'#A46A32',500)
text(1390,418,'纠正数据回到处理环节',17,'#8F7C65')

path('M815 1364 V1406')
rect(495,1412,640,64,'#F0F7F2','#D2E2D7',10)
text(815,1452,'达标留存：候选模型 + 验收证据 + 适用范围',22,'#385A45',500,'middle')

# Lineage is an object relationship, not a second process lane.
rect(30,1520,1740,245,'#F7FAFE','#D5E1EF')
text(60,1563,'全流程版本与血缘',26,'#365C87',600)
text(1740,1561,'向前追踪数据影响  /  向后追溯结果来源',18,'#6480A0',anchor='end')
items=[('源数据与标注','数据 ID / 标注版本'),('数据集版本','样本范围 / 数据快照'),('训练任务','起点模型 / 配置'),('Checkpoint','模型版本 / 训练来源'),('评测结果与 Badcase','用例 / 标准 / 执行记录')]
for i,(title,detail) in enumerate(items):
    x=60+i*342
    card(x,1595,302,title,detail,'#FFFFFF','#CEDCEB')
    if i<4:path(f'M{x+307} 1638 H{x+335}','lineage',2)
text(60,1720,'跨轮关联',18,'#365C87',600)
text(180,1720,'来源 Checkpoint → DAgger 采集任务 → 纠正数据 → 下一版数据集 → 新 Checkpoint',20,'#466A94')
text(60,1749,'评测结果同时关联评测集与评分标准；关联信息用于核对数据、配置或评测口径的变化。',17,'#6A8099')
parts.append('</g></svg>')
(OUT/'quanta-iteration-loop-lineage.svg').write_text('\n'.join(parts),encoding='utf-8')
print(OUT/'quanta-iteration-loop-lineage.svg')
