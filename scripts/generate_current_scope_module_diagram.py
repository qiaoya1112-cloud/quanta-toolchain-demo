from generate_quanta_product_plan_v2_diagrams import (
    ACCENT,
    ACCENT_BG,
    INK,
    LINE,
    LINE_DARK,
    MUTED,
    PANEL,
    WHITE,
    card,
    label,
    line,
    path,
    rect,
    save,
    section,
    text,
)

SMALL_ARROW_DEFS = """
<defs>
  <marker id="arrow-small-blue" markerWidth="8" markerHeight="8" refX="7" refY="4"
          orient="auto" markerUnits="userSpaceOnUse">
    <path d="M0,0 L7,4 L0,8 Z" fill="#2563EB"/>
  </marker>
  <marker id="arrow-small-gray" markerWidth="8" markerHeight="8" refX="7" refY="4"
          orient="auto" markerUnits="userSpaceOnUse">
    <path d="M0,0 L7,4 L0,8 Z" fill="#94A3B8"/>
  </marker>
</defs>
"""


def line(x1, y1, x2, y2, color=LINE_DARK, width=1.4, arrow=True, dash=None):
    marker = ""
    if arrow:
        marker_id = "arrow-small-blue" if color == ACCENT else "arrow-small-gray"
        marker = f' marker-end="url(#{marker_id})"'
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round" fill="none"{marker}{dash_attr}/>'
    )


def path(points, color=LINE_DARK, width=1.4, arrow=True, dash=None):
    marker = ""
    if arrow:
        marker_id = "arrow-small-blue" if color == ACCENT else "arrow-small-gray"
        marker = f' marker-end="url(#{marker_id})"'
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    d = " ".join(
        f'{"M" if index == 0 else "L"} {x} {y}'
        for index, (x, y) in enumerate(points)
    )
    return (
        f'<path d="{d}" stroke="{color}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round" fill="none"{marker}{dash_attr}/>'
    )


def main():
    width, height = 2100, 1180
    body = SMALL_ARROW_DEFS

    # 数据输入：本期只定义接口，不改造采集或导入产品。
    body += section(40, 126, 620, 404, "数据输入｜本期不涉及", "只约定输出统一 Recording")
    body += card(78, 222, 170, 190, "自由采集", ["后训练 / POC", "形成 Recording"], center=True)
    body += card(276, 222, 170, 82, "采集指令", ["模板与规则"], center=True, small=True)
    body += card(276, 330, 170, 82, "指令采集", ["按指令执行"], center=True, small=True)
    body += line(361, 304, 361, 330, LINE_DARK)
    body += card(474, 222, 150, 190, "数据导入", ["开源 / 外部", "历史数据"], center=True)

    # 数据资产：区分可持续维护的数据集与不可变的数据快照。
    body += section(40, 584, 620, 474, "数据资产｜本期部分涉及", "统一承接数据、结果和可消费版本")
    body += card(
        78,
        678,
        250,
        120,
        "数据湖",
        ["Recording · 元数据 · 标签", "检索 · 预览 · 处理状态"],
        active=True,
        center=True,
    )
    body += card(
        370,
        678,
        250,
        120,
        "结果版本与血缘",
        ["Processing Result Version", "结果 · 流程 · 节点血缘"],
        center=True,
    )
    body += line(328, 738, 370, 738, ACCENT)
    body += label(349, 721, "结果写回", MUTED)

    # 数据集是长期资产；每个数据集版本内部对应一份不可变的内容快照。
    body += rect(78, 830, 542, 162, WHITE, LINE, 12)
    body += text(100, 858, "数据集（长期资产，可发布多个版本）", 15, INK, 600)
    body += card(100, 874, 136, 92, "数据集", ["名称 · 范围"], center=True, small=True)
    body += card(258, 874, 146, 92, "数据集版本", ["v1 / v2 / v3"], center=True, small=True)
    body += card(
        426,
        874,
        172,
        92,
        "版本内容快照",
        ["Recording ID", "+ 结果版本"],
        center=True,
        small=True,
    )
    body += line(236, 920, 258, 920, ACCENT)
    body += line(404, 920, 426, 920, ACCENT)

    # 发布版本时，同时冻结所选 Recording 和对应处理结果版本。
    body += path([(203, 798), (203, 814), (331, 814)], ACCENT, arrow=False)
    body += path([(495, 798), (495, 814), (331, 814)], ACCENT, arrow=False)
    body += line(331, 814, 331, 874, ACCENT)
    body += label(349, 810, "发布时冻结", MUTED)

    # 数据处理 Pipeline：按任务层、流程层、执行层自上而下展开。
    body += section(
        714,
        126,
        1346,
        610,
        "数据处理 Pipeline｜本期核心",
        "任务定义处理范围与路径，流程形成运行实例，节点完成自动或人工作业",
        accent=True,
    )

    # 01 任务层：回答处理什么、经过哪些处理环节、使用哪个流程版本。
    body += rect(742, 202, 1290, 112, WHITE, LINE, 12)
    body += text(766, 235, "01  任务层", 15, INK, 600)
    body += text(766, 266, "定义范围与路径", 12, MUTED, 400)
    body += card(
        900,
        216,
        280,
        84,
        "数据处理任务",
        ["选数条件 · 处理水位 · 优先级"],
        center=True,
        small=True,
    )
    body += card(
        1220,
        216,
        300,
        84,
        "处理环节编排",
        ["启用处理环节 · 顺序 · 进入条件"],
        center=True,
        small=True,
    )
    body += card(
        1560,
        216,
        442,
        84,
        "流程版本绑定",
        ["各处理环节绑定 Flow Version · 定义输出 Key"],
        center=True,
        small=True,
    )
    body += line(1180, 258, 1220, 258, ACCENT)
    body += line(1520, 258, 1560, 258, ACCENT)

    # 02 流程层：每个处理环节生成独立 Flow Run，并按条件衔接。
    body += rect(742, 330, 1290, 166, WHITE, LINE, 12)
    body += text(766, 363, "02  流程层", 15, INK, 600)
    body += text(766, 394, "独立运行，条件衔接", 12, MUTED, 400)
    stages = [
        (900, "质检流程", ["清洗 · 自动 / 人工质检", "生成独立 Flow Run"], False),
        (1174, "标注流程", ["切分 · 人工标注", "生成独立 Flow Run"], False),
        (1448, "验收流程", ["抽样验收 · 一致性检查", "生成独立 Flow Run"], True),
        (1722, "后处理流程", ["翻译 · 坐标 / 格式转换", "生成独立 Flow Run"], True),
    ]
    for x, title, details, dashed in stages:
        body += card(
            x,
            354,
            244,
            118,
            title,
            details,
            center=True,
            dashed=dashed,
            small=True,
        )
    body += line(1144, 413, 1174, 413, ACCENT)
    body += line(1418, 413, 1448, 413, LINE_DARK)
    body += line(1692, 413, 1722, 413, LINE_DARK)
    body += label(1159, 397, "条件")
    body += label(1433, 397, "条件")
    body += label(1707, 397, "条件")

    # 03 执行层：流程节点落到两类运行时，最终统一产生 Node Run 和输出。
    body += rect(742, 512, 1290, 188, WHITE, LINE, 12)
    body += text(766, 545, "03  执行层", 15, INK, 600)
    body += text(766, 576, "节点实际完成作业", 12, MUTED, 400)
    body += card(
        900,
        528,
        188,
        68,
        "自动节点",
        ["算子 / 条件"],
        center=True,
        small=True,
    )
    body += card(
        1122,
        528,
        260,
        68,
        "Operator Runtime",
        ["参数 · 资源 · 执行"],
        center=True,
        small=True,
    )
    body += card(
        900,
        616,
        188,
        68,
        "人工节点",
        ["需人工处理"],
        center=True,
        small=True,
    )
    body += card(
        1122,
        616,
        260,
        68,
        "Human Task / 任务池",
        ["用户组 · 分配 · 锁"],
        center=True,
        small=True,
    )
    body += card(
        1416,
        616,
        250,
        68,
        "工作台",
        ["领取 · 暂离 · 提交"],
        center=True,
        small=True,
    )
    body += card(
        1710,
        548,
        292,
        116,
        "统一运行记录",
        ["Node Run · 状态 · 重试", "结果输出与血缘"],
        center=True,
        small=True,
    )
    body += line(1088, 562, 1122, 562, ACCENT)
    body += path([(1382, 562), (1676, 562), (1676, 582), (1710, 582)], ACCENT)
    body += line(1088, 650, 1122, 650, ACCENT)
    body += line(1382, 650, 1416, 650, ACCENT)
    body += path([(1666, 650), (1688, 650), (1688, 630), (1710, 630)], ACCENT)

    # 运营管理：提供组织、资格、调度和监控。
    body += section(
        714,
        790,
        1346,
        268,
        "运营管理｜本期部分涉及",
        "提供人员和组织支撑，不维护流程运行状态",
    )
    operations = [
        (756, "供应商与人员", ["组织 · 成员 · 技能", "状态 · 可用产能"]),
        (1072, "用户组", ["作业资格 · 成员", "节点处理范围"]),
        (1388, "任务分配调度", ["任务池 · SLA · 锁", "释放 · 改派"]),
        (1704, "生产监控", ["进度 · 积压 · 吞吐", "负载 · 周期 · 异常"]),
    ]
    for x, title, details in operations:
        body += card(x, 872, 272, 116, title, details, center=True)
    body += line(1028, 930, 1072, 930, ACCENT)
    body += line(1344, 930, 1388, 930, ACCENT)
    body += line(1660, 930, 1704, 930, ACCENT)

    # 模块间关系。
    body += path([(350, 530), (350, 556), (350, 584)], LINE_DARK)
    body += label(390, 560, "写入 Recording", INK, "start")

    # 输入与结果回写使用两条独立通道，避免反向连线重合。
    body += path([(660, 716), (674, 716), (674, 258), (900, 258)], ACCENT)
    body += label(682, 426, "读取命中数据", INK, "start")

    body += path([(742, 676), (700, 676), (700, 782), (660, 782)], ACCENT)
    body += label(708, 766, "结果与血缘写回", INK, "start")

    body += path([(1390, 790), (1390, 762), (1252, 762), (1252, 684)], ACCENT)
    body += label(1408, 770, "用户组与可用产能", INK, "start")

    body += path([(1856, 664), (1856, 748), (1817, 748), (1817, 790)], LINE_DARK)
    body += label(1835, 756, "任务量与运行指标", INK, "start")

    # 只保留结论，不再额外解释颜色或虚线。
    body += rect(40, 1102, 2020, 50, ACCENT_BG, ACCENT, 10)
    body += text(
        72,
        1133,
        "快照 = 某次发布实际包含的 Recording ID 和结果版本；数据集 = 持续维护这些版本的长期资产",
        13,
        INK,
        500,
    )
    body += text(
        2016,
        1133,
        "核心关系：任务选数据｜流程定处理｜运营供人员｜资产管版本",
        13,
        INK,
        600,
        "end",
    )

    save(
        "current-scope-module-relationship",
        width,
        height,
        "本期方案模块边界与协作关系",
        "数据输入不在本期改造范围；数据处理 Pipeline 是核心；数据资产和运营管理只建设必要协作能力。",
        body,
    )


if __name__ == "__main__":
    main()
