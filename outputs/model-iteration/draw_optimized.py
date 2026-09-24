from pathlib import Path
from html import escape
from math import hypot
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
W,H,S = 1960,1580,2
im = Image.new('RGB',(W*S,H*S),'white')
dr = ImageDraw.Draw(im)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/><g font-family="Arial Unicode MS, PingFang SC, Microsoft YaHei, sans-serif">']
fonts={}
INK='#233449'; MUTED='#65768A'; MAIN='#8593A6'; LOOP='#BD792F'; BLUE='#5C83AE'

def font(sz,bold=False):
    key=(sz,bold)
    if key not in fonts:
        p='/System/Library/Fonts/STHeiti Medium.ttc' if bold else '/Library/Fonts/Arial Unicode.ttf'
        fonts[key]=ImageFont.truetype(p,int(sz*S))
    return fonts[key]

def rect(x,y,w,h,fill='white',stroke=None,r=12):
    dr.rounded_rectangle((x*S,y*S,(x+w)*S,(y+h)*S),radius=r*S,fill=fill,outline=stroke,width=S)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke or "none"}"/>')

def txt(x,y,s,size=20,color=INK,bold=False,anchor='start'):
    f=font(size,bold)
    width=dr.textlength(s,font=f)
    px=x*S-(width/2 if anchor=='middle' else width if anchor=='end' else 0)
    dr.text((px,y*S),s,font=f,fill=color,anchor='ls')
    svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{600 if bold else 400}" text-anchor="{anchor}">{escape(s)}</text>')

def line(points,color=MAIN,width=2.3,dash=False,arrow=True):
    pts=[(x*S,y*S) for x,y in points]
    if dash:
        for (x,y),(xx,yy) in zip(pts,pts[1:]):
            L=hypot(xx-x,yy-y)
            for p in range(0,int(L),16*S):
                q=min(p+9*S,L)
                dr.line([(x+(xx-x)*p/L,y+(yy-y)*p/L),(x+(xx-x)*q/L,y+(yy-y)*q/L)],fill=color,width=int(width*S))
    else: dr.line(pts,fill=color,width=int(width*S),joint='curve')
    coords=' '.join(f'{x},{y}' for x,y in points)
    ds=' stroke-dasharray="9 7"' if dash else ''
    svg.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{ds}/>')
    if arrow:
        (a,b),(x,y)=points[-2:]; l=hypot(x-a,y-b); ux=(x-a)/l;uy=(y-b)/l
        tri=[(x,y),(x-12*ux+5*uy,y-12*uy-5*ux),(x-12*ux-5*uy,y-12*uy+5*ux)]
        dr.polygon([(x*S,y*S) for x,y in tri],fill=color)
        svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in tri)}" fill="{color}"/>')

def label(x,y,text,color=MUTED,size=18):
    w=dr.textlength(text,font=font(size))/S+22
    rect(x-w/2,y-23,w,32,'white',r=5)
    txt(x,y,text,size,color,anchor='middle')

def module(x,y,num,title,items,foot,tone):
    fill,stroke,accent=tone
    rect(x,y,500,340,'#FCFDFE','#DDE4EC',16)
    rect(x+22,y+22,38,34,fill,stroke,8)
    txt(x+41,y+47,num,18,accent,True,'middle')
    txt(x+74,y+48,title,25,INK,True)
    # Equal-size modules use three capability cells or two larger cells.
    n=len(items); hh=64 if n==3 else 101; gap=12
    for i,(heading,desc) in enumerate(items):
        yy=y+77+i*(hh+gap)
        rect(x+22,yy,456,hh,fill,stroke,9)
        txt(x+40,yy+(26 if n==3 else 39),heading,21,INK,True)
        txt(x+40,yy+(51 if n==3 else 72),desc,17,MUTED)
    txt(x+24,y+319,foot,16,accent)

goal=('#F0F4FC','#D5DFEF','#5376A5')
data=('#EFF8F3','#D2E6D9','#4B8565')
train=('#F4F0FB','#DFD5EF','#8264B0')
evaluation=('#FFF8E9','#ECDFBB','#A27B2F')

txt(180,64,'Quanta｜从业务目标到模型迭代',38,INK,True)
txt(180,101,'六步主流程 · 业务改进与 DAgger 双闭环 · 全流程版本血缘',21,MUTED)
line([(1270,83),(1310,83)]);txt(1322,90,'主流程',17,MUTED)
line([(1440,83),(1480,83)],LOOP,dash=True);txt(1492,90,'问题回流',17,MUTED)
line([(1625,83),(1665,83)],BLUE);txt(1677,90,'版本血缘',17,MUTED)

# Six steps follow a continuous clockwise reading path.
module(180,180,'01','明确迭代目标与方案',[
    ('业务目标','明确任务、场景与目标技能'),
    ('迭代方案','数据需求、基线模型与训练方案'),
    ('验收口径','成功定义、目标指标与固定评测集')],
    '输出：目标与执行方案',goal)
module(760,180,'02','采集并处理数据',[
    ('采集指令下发','复用指令包，下发场景、任务与采集规则'),
    ('质检、标注与验收','配置处理流程与规则，问题数据返工复核')],
    '输出：验收合格的数据与标注结果',data)
module(1340,180,'03','构建训练数据集',[
    ('数据筛选与可视化查看','按业务条件组合筛选，查看分布与轨迹'),
    ('后处理与版本化打包','确认数据配比，完成加工并固定数据快照')],
    '输出：可复用、可追溯的数据集版本',data)
module(1340,650,'04','执行训练并保存模型',[
    ('发起训练任务','选择适配模板、数据集版本与运行资源'),
    ('观测训练与保存 Checkpoint','查看日志与训练指标，保存候选模型版本')],
    '输出：训练记录与候选 Checkpoint',train)
module(760,650,'05','合并模型并下发',[
    ('Checkpoint 合并与压缩','按模型格式要求准备部署产物'),
    ('模型与推理环境下发','关联目标设备、模型与配套推理软件')],
    '输出：可执行的部署模型与下发记录',train)
module(180,650,'06','评测模型并定位问题',[
    ('评测用例与评分标准','使用预先约定的评测集与验收口径'),
    ('真机推理与过程记录','执行评测，记录过程数据与评分'),
    ('结果对比与 Badcase 分析','总体与分场景对比，回看失败证据')],
    '输出：评测结果、失败案例与改进依据',evaluation)

line([(685,350),(755,350)])
line([(1265,350),(1335,350)])
line([(1590,524),(1590,645)])
label(1590,584,'固定数据集版本')
line([(1335,820),(1265,820)])
line([(755,820),(685,820)])
txt(1300,798,'模型',16,MUTED,anchor='middle')
txt(720,798,'部署',16,MUTED,anchor='middle')
txt(720,850,'就绪',16,MUTED,anchor='middle')
txt(1300,850,'版本',16,MUTED,anchor='middle')

# Explicit release gate with two reason-based feedback routes.
line([(430,994),(430,1050)])
diamond=[(430,1055),(550,1115),(430,1175),(310,1115)]
dr.polygon([(x*S,y*S) for x,y in diamond],fill='#FFF7E4',outline='#D8BD83',width=S)
svg.append('<polygon points="430,1055 550,1115 430,1175 310,1115" fill="#FFF7E4" stroke="#D8BD83"/>')
txt(430,1110,'是否达到',21,INK,True,'middle')
txt(430,1140,'准出标准？',21,INK,True,'middle')
line([(430,1180),(430,1230)])
label(430,1211,'是',size=17)
rect(180,1235,500,84,'#EFF7F1','#D0E2D5')
txt(430,1270,'达标留存',24,'#446B52',True,'middle')
txt(430,1300,'候选模型 + 评测结果 + 适用范围',18,MUTED,anchor='middle')

line([(305,1115),(70,1115),(70,350),(175,350)],LOOP,dash=True)
label(234,1101,'否',LOOP,17)
rect(18,550,145,157,'#FFFFFF',r=0)
txt(90,577,'业务改进闭环',20,LOOP,True,'middle')
for i,s in enumerate(['更新目标与方案','定向补采','标注修正','数据重配']):txt(90,609+i*27,s,17,MUTED,anchor='middle')

# DAgger returns through quality control, preserving provenance.
rect(1340,1090,500,229,'#FFF8EF','#E6CFB0',15)
txt(1370,1131,'DAgger 纠正采集',27,'#8C622E',True)
txt(1370,1170,'指定 Checkpoint 执行，人工接管纠正',20,INK)
txt(1370,1203,'记录异常、回退与遥操作示教数据',19,MUTED)
txt(1370,1250,'来源记录：模型版本 / 设备 / 失败类型',18,'#8C622E')
txt(1370,1284,'纠正数据经质检、标注与验收后重新组配',18,'#8C622E')
line([(555,1115),(1220,1115),(1220,1182),(1335,1182)],LOOP,dash=True)
label(885,1100,'否：针对模型执行偏差开展纠正采集',LOOP)
txt(855,1187,'模型纠正闭环',24,LOOP,True,anchor='middle')
txt(855,1223,'问题定位 → 纠正数据 → 重新组配与训练',19,MUTED,anchor='middle')
line([(1720,994),(1720,1085)],LOOP,dash=True)
label(1710,1049,'指定来源 Checkpoint',LOOP,17)
line([(1845,1204),(1900,1204),(1900,139),(1010,139),(1010,175)],LOOP,dash=True)
label(1460,144,'纠正数据回到质检 / 标注 / 验收',LOOP,17)

# Separate provenance rail avoids confusing artifact links with task control.
rect(180,1374,1660,156,'#F6F9FE','#D7E2EF',14)
txt(204,1408,'全流程版本与血缘',23,'#3E658F',True)
txt(1816,1407,'追溯来源 · 比较版本 · 追踪数据影响',17,'#6481A0',anchor='end')
names=['源数据与标注','数据集版本','训练任务','Checkpoint','部署记录','评测与 Badcase']
for i,name in enumerate(names):
    x=204+i*271
    rect(x,1429,241,46,'#FFFFFF','#D3DFEE',8)
    txt(x+120.5,1459,name,20,'#395775',True,'middle')
    if i<5:line([(x+245,1452),(x+266,1452)],BLUE,2)
txt(204,1507,'跨轮关联：来源 Checkpoint → DAgger 任务 → 纠正数据 → 新数据集版本 → 新 Checkpoint',18,'#52769E')
txt(180,1560,'评测结果关联评测集与评分标准；各阶段保留来源 ID、版本及任务记录。',17,MUTED)

svg.append('</g></svg>')
(OUT/'quanta-iteration-optimized.svg').write_text('\n'.join(svg),encoding='utf-8')
im.save(OUT/'quanta-iteration-optimized.png')
print('Exported SVG and PNG to',OUT)
