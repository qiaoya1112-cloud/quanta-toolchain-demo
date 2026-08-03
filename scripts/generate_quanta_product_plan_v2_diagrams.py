from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "product-plan-v2"
OUT.mkdir(parents=True, exist_ok=True)

BG = "#FFFFFF"
INK = "#1E293B"
MUTED = "#64748B"
LINE = "#CBD5E1"
LINE_DARK = "#94A3B8"
PANEL = "#F8FAFC"
ACCENT = "#2563EB"
ACCENT_BG = "#EFF6FF"
SOFT = "#F1F5F9"
WHITE = "#FFFFFF"


def svg_start(width, height, title, subtitle=""):
    subtitle_svg = ""
    if subtitle:
        subtitle_svg = text(48, 82, [subtitle], 18, MUTED)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <title>{escape(title)}</title>
  <desc>{escape(subtitle)}</desc>
  <defs>
    <marker id="arrow-blue" markerWidth="10" markerHeight="10" refX="9" refY="3.5" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,7 L9,3.5 z" fill="{ACCENT}"/>
    </marker>
    <marker id="arrow-gray" markerWidth="10" markerHeight="10" refX="9" refY="3.5" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,7 L9,3.5 z" fill="{LINE_DARK}"/>
    </marker>
    <style>
      text {{ font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", Arial, sans-serif; }}
    </style>
  </defs>
  <rect width="{width}" height="{height}" fill="{BG}"/>
  {text(48, 48, [title], 30, INK, 600)}
  {subtitle_svg}
"""


def svg_end():
    return "</svg>\n"


def text(x, y, lines, size=18, color=INK, weight=400, anchor="start", line_height=None):
    if isinstance(lines, str):
        lines = [lines]
    line_height = line_height or int(size * 1.45)
    spans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else line_height
        spans.append(
            f'<tspan x="{x}" dy="{dy}">{escape(str(line))}</tspan>'
        )
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
        f'font-weight="{weight}" text-anchor="{anchor}">'
        + "".join(spans)
        + "</text>"
    )


def rect(x, y, w, h, fill=WHITE, stroke=LINE, radius=12, stroke_width=1.5, dash=None):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr}/>'
    )


def line(
    x1,
    y1,
    x2,
    y2,
    color=LINE_DARK,
    width=2,
    arrow=True,
    dash=None,
    marker_id=None,
):
    marker = ""
    if arrow:
        resolved_marker_id = marker_id or (
            "arrow-blue" if color == ACCENT else "arrow-gray"
        )
        marker = f' marker-end="url(#{resolved_marker_id})"'
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="{width}" fill="none"{marker}{dash_attr}/>'
    )


def path(points, color=LINE_DARK, width=2, arrow=True, dash=None):
    marker = ""
    if arrow:
        marker_id = "arrow-blue" if color == ACCENT else "arrow-gray"
        marker = f' marker-end="url(#{marker_id})"'
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    d = " ".join(
        [f"M {points[0][0]} {points[0][1]}"]
        + [f"L {x} {y}" for x, y in points[1:]]
    )
    return (
        f'<path d="{d}" stroke="{color}" stroke-width="{width}" '
        f'fill="none"{marker}{dash_attr}/>'
    )


def section(x, y, w, h, title, subtitle="", accent=False, dash=None):
    border = ACCENT if accent else LINE
    fill = ACCENT_BG if accent else PANEL
    parts = [rect(x, y, w, h, fill, border, 16, 1.5, dash)]
    parts.append(text(x + 22, y + 35, title, 21, INK, 600))
    if subtitle:
        parts.append(text(x + 22, y + 62, subtitle, 14, MUTED))
    return "".join(parts)


def card(
    x,
    y,
    w,
    h,
    title,
    details=None,
    active=False,
    dashed=False,
    small=False,
    center=False,
    tag=None,
):
    border = ACCENT if active else LINE_DARK
    fill = ACCENT_BG if active else WHITE
    dash = "7 6" if dashed else None
    parts = [rect(x, y, w, h, fill, border, 10, 1.5, dash)]
    if center:
        tx = x + w / 2
        anchor = "middle"
    else:
        tx = x + 16
        anchor = "start"
    title_y = y + (h / 2 + 7 if not details else 30)
    parts.append(text(tx, title_y, title, 16 if small else 18, INK, 600, anchor))
    if details:
        parts.append(
            text(tx, y + 56, details, 13 if small else 14, MUTED, 400, anchor, 21)
        )
    if tag:
        parts.append(
            f'<rect x="{x + w - 74}" y="{y + 12}" width="58" height="24" rx="12" fill="{SOFT}"/>'
        )
        parts.append(text(x + w - 45, y + 29, tag, 12, MUTED, 500, "middle"))
    return "".join(parts)


def label(x, y, value, color=MUTED, anchor="middle"):
    return text(x, y, value, 13, color, 500, anchor)


def phase_header(x, y, w, index, title, subtitle=""):
    parts = [
        f'<circle cx="{x + 22}" cy="{y + 22}" r="18" fill="{ACCENT}"/>',
        text(x + 22, y + 28, str(index), 14, WHITE, 600, "middle"),
        text(x + 54, y + 20, title, 18, INK, 600),
    ]
    if subtitle:
        parts.append(text(x + 54, y + 45, subtitle, 13, MUTED))
    parts.append(line(x + 8, y + 64, x + w - 8, y + 64, LINE, 1, False))
    return "".join(parts)


def save(name, width, height, title, subtitle, body):
    output = OUT / f"{name}.svg"
    output.write_text(
        svg_start(width, height, title, subtitle) + body + svg_end(),
        encoding="utf-8",
    )


def diagram_product_boundary():
    w, h = 1900, 930
    body = ""
    body += section(42, 118, 250, 500, "数据输入", "形成统一 Recording")
    body += card(72, 190, 190, 76, "采集任务", ["指令 / 自由 / DAgger"], center=True)
    body += card(72, 294, 190, 76, "导入任务", ["文件 / 对象存储 / API"], center=True)
    body += card(72, 414, 190, 110, "Recording", ["唯一标识", "来源与校验和"], active=True, center=True)

    body += section(338, 118, 900, 500, "数据 Pipeline", "任务负责选数，流程负责执行，节点负责处理", accent=True)
    body += card(374, 190, 244, 98, "任务管理", ["采集任务 · 处理任务", "分配管理"], center=True)
    body += card(660, 190, 244, 98, "流程与配置", ["流程 · 算子 · 工作台", "规则 · 场景 · 标签"], center=True)
    body += card(946, 190, 244, 98, "人工协作", ["用户组 · 任务池", "领取 · 锁定 · 提交"], center=True)
    body += card(374, 352, 236, 116, "持续接入", ["筛选条件", "开启状态 · 处理水位"], active=True, center=True)
    body += card(666, 352, 236, 116, "工作流引擎", ["自动 / 人工 / 条件节点", "独立 Flow Run"], active=True, center=True)
    body += card(958, 352, 236, 116, "执行运行时", ["Operator Runtime", "Workbench Runtime"], active=True, center=True)
    body += line(610, 410, 666, 410, ACCENT, 3)
    body += line(902, 410, 958, 410, ACCENT, 3)
    body += label(784, 507, "处理结果与血缘写回数据资产")

    body += section(1284, 118, 568, 500, "数据资产", "管理数据事实与可消费版本")
    body += card(1320, 190, 230, 98, "数据管理", ["Recording 检索", "处理结果 · 版本 · 血缘"], center=True)
    body += card(1582, 190, 230, 98, "数据集管理", ["筛选 · 快照 · 构建", "发布 · 回滚 · 消费"], center=True)
    body += card(1320, 352, 492, 116, "版本化数据资产", ["Processing Result Version → Data Snapshot → Dataset Version"], active=True, center=True)
    body += line(1238, 408, 1320, 408, ACCENT, 3)
    body += path([(292, 468), (324, 468), (324, 410), (374, 410)], ACCENT, 3)
    body += path([(1320, 250), (1264, 250), (1264, 334), (492, 334), (492, 352)], LINE_DARK, 2)
    body += label(915, 323, "处理任务持续读取命中数据", MUTED)

    body += section(338, 670, 1514, 176, "运营与平台支撑", "提供组织与治理能力，不承载流程运行状态")
    support = [
        ("供应商与人员", "组织、技能、产能"),
        ("用户组与权限", "菜单、数据范围、作业资格"),
        ("平台底座", "存储、队列、检索、开放接口"),
        ("治理与审计", "租户、日志、监控、告警"),
    ]
    for i, (title, detail) in enumerate(support):
        body += card(374 + i * 356, 735, 310, 76, title, [detail], center=True, small=True)
    body += path([(1040, 618), (1040, 646), (1095, 646), (1095, 670)], LINE_DARK, 2, False, "7 6")
    save(
        "product-boundary",
        w,
        h,
        "产品边界与核心模块关系",
        "数据 Pipeline 负责持续接入与执行；数据资产负责数据集生命周期；运营管理提供人员和组织支撑。",
        body,
    )


def diagram_end_to_end():
    w, h = 2000, 900
    body = ""
    phases = [
        ("项目与配置", "发布可复用版本"),
        ("数据进入", "采集或导入"),
        ("持续筛选", "处理任务"),
        ("流程执行", "独立环节流程"),
        ("人工协作", "任务池与工作台"),
        ("结果沉淀", "版本与血缘"),
        ("构建发布", "数据集资产"),
    ]
    x0, col_w, gap = 30, 260, 18
    xs = [x0 + i * (col_w + gap) for i in range(len(phases))]
    for i, (title, subtitle) in enumerate(phases):
        body += rect(xs[i], 116, col_w, 686, PANEL, LINE, 14)
        body += phase_header(xs[i] + 10, 132, col_w - 20, i + 1, title, subtitle)

    body += card(xs[0] + 25, 238, 210, 82, "项目", ["范围 · 成员 · 交付标准"], center=True)
    body += card(xs[0] + 25, 354, 210, 82, "发布配置版本", ["流程 · 工作台 · 规则"], active=True, center=True)

    body += card(xs[1] + 25, 238, 210, 74, "采集任务", center=True)
    body += card(xs[1] + 25, 338, 210, 74, "导入任务", center=True)
    body += card(xs[1] + 25, 464, 210, 94, "Recording", ["统一标识与来源"], active=True, center=True)

    body += card(xs[2] + 25, 238, 210, 124, "数据处理任务", ["状态：开启", "筛选条件 · 处理水位"], active=True, center=True)
    body += card(xs[2] + 25, 406, 210, 92, "匹配新数据", ["持续进入，不固定批次"], dashed=True, center=True)

    body += card(xs[3] + 20, 218, 220, 92, "质检流程", ["独立 Flow Version"], center=True)
    body += card(xs[3] + 20, 346, 220, 92, "标注流程", ["独立 Flow Version"], center=True)
    body += card(xs[3] + 20, 474, 220, 92, "验收流程", ["独立 Flow Version"], center=True)
    body += path([(xs[3] + 130, 310), (xs[3] + 130, 346)], ACCENT, 3)
    body += path([(xs[3] + 130, 438), (xs[3] + 130, 474)], ACCENT, 3)
    body += label(xs[3] + 218, 332, "按条件进入")
    body += label(xs[3] + 218, 460, "按条件进入")

    body += card(xs[4] + 25, 238, 210, 88, "Human Task", ["人工节点生成"], center=True)
    body += card(xs[4] + 25, 360, 210, 88, "用户组任务池", ["多组可见 · 首领锁定"], active=True, center=True)
    body += card(xs[4] + 25, 482, 210, 88, "工作台执行", ["暂离 · 驳回 · 提交"], center=True)
    body += line(xs[4] + 130, 326, xs[4] + 130, 360, ACCENT, 3)
    body += line(xs[4] + 130, 448, xs[4] + 130, 482, ACCENT, 3)

    body += card(xs[5] + 25, 238, 210, 88, "Flow Output", ["按流程写入结果 Key"], center=True)
    body += card(xs[5] + 25, 360, 210, 88, "结果版本", ["不覆盖历史"], active=True, center=True)
    body += card(xs[5] + 25, 482, 210, 88, "Data Snapshot", ["固定成员与校验和"], center=True)
    body += line(xs[5] + 130, 326, xs[5] + 130, 360, ACCENT, 3)
    body += line(xs[5] + 130, 448, xs[5] + 130, 482, ACCENT, 3)

    body += card(xs[6] + 25, 238, 210, 88, "数据集构建", ["筛选 · 划分 · 元数据"], center=True)
    body += card(xs[6] + 25, 360, 210, 88, "Dataset Version", ["冻结 · 发布 · 回滚"], active=True, center=True)
    body += card(xs[6] + 25, 482, 210, 88, "训练 / 评测 / 交付", ["固定引用版本"], center=True)
    body += line(xs[6] + 130, 326, xs[6] + 130, 360, ACCENT, 3)
    body += line(xs[6] + 130, 448, xs[6] + 130, 482, ACCENT, 3)

    main_y = 642
    main_nodes = [
        "配置发布",
        "形成数据",
        "持续命中",
        "流程运行",
        "人工回写",
        "沉淀版本",
        "发布消费",
    ]
    for i, name in enumerate(main_nodes):
        cx = xs[i] + col_w / 2
        body += f'<circle cx="{cx}" cy="{main_y}" r="9" fill="{ACCENT}"/>'
        body += label(cx, main_y + 34, name, INK)
        if i < len(main_nodes) - 1:
            body += line(cx + 10, main_y, xs[i + 1] + col_w / 2 - 10, main_y, ACCENT, 4)

    body += path([(xs[0] + 235, 395), (xs[1] + 25, 275)], ACCENT, 3)
    body += path([(xs[1] + 235, 510), (xs[2] + 25, 300)], ACCENT, 3)
    body += path([(xs[2] + 235, 452), (xs[3] + 20, 264)], ACCENT, 3)
    body += path([(xs[3] + 240, 392), (xs[4] + 25, 282)], LINE_DARK, 2, True, "7 6")
    body += path([(xs[4] + 235, 526), (xs[5] + 25, 282)], LINE_DARK, 2, True, "7 6")
    body += path([(xs[5] + 235, 526), (xs[6] + 25, 282)], ACCENT, 3)

    body += rect(48, 744, 1898, 112, ACCENT_BG, ACCENT, 14)
    body += text(72, 782, "关键约束", 17, INK, 600)
    body += text(
        72,
        812,
        [
            "处理任务关闭后只停止接收新数据；已进入流程的数据继续执行。各流程独立保存输入、输出和运行状态，结果通过版本和血缘串联。",
        ],
        15,
        MUTED,
    )
    save(
        "end-to-end-flow",
        w,
        h,
        "端到端业务流程",
        "从配置、持续进数、独立流程执行到数据集发布的完整链路。",
        body,
    )


def diagram_swimlane():
    w, h = 2060, 1120
    body = f"""
<defs>
  <marker id="swimlane-arrow" markerWidth="7" markerHeight="7"
          refX="6.5" refY="3.5" orient="auto"
          markerUnits="userSpaceOnUse">
    <path d="M0,0 L6.5,3.5 L0,7 Z" fill="{ACCENT}"/>
  </marker>
</defs>
"""
    left = 310
    top = 164
    col_w = 278
    headers = ["项目准备", "数据进入", "任务与流程配置", "执行与协作", "数据资产发布", "运行与运营"]
    for i, header in enumerate(headers):
        x = left + i * col_w
        body += rect(x, top, col_w - 8, 76, ACCENT_BG if i < 5 else PANEL, LINE, 10)
        body += text(x + (col_w - 8) / 2, top + 34, header, 17, INK, 600, "middle")
        body += text(x + (col_w - 8) / 2, top + 58, str(i + 1).zfill(2), 12, MUTED, 500, "middle")

    body += rect(34, top, 246, 76, SOFT, LINE, 10)
    body += text(157, top + 33, "用户角色", 18, INK, 600, "middle")
    body += text(157, top + 58, "角色决定菜单与数据范围", 12, MUTED, 400, "middle")

    rows = [
        (
            "项目 / 数据运营负责人",
            "对范围、进度和交付负责",
            ["定义目标与范围", "确认输入口径", "选择处理方案", "跟踪核心进度", "确认版本交付", "复盘周期与成本"],
            [0, 2, 4, 5],
            [0],
        ),
        (
            "工厂管理员",
            "组织生产与资源",
            ["配置组织与人员", "查看数据进入", "开启处理任务", "处理积压与异常", "查看交付进度", "分析产能与 SLA"],
            [0, 2, 3, 5],
            [2],
        ),
        (
            "平台管理员",
            "维护平台执行能力",
            ["准备平台边界", "保障接入能力", "发布流程与工作台", "监控运行与告警", "控制发布权限", "治理权限与审计"],
            [0, 2, 3, 5],
            [],
        ),
        (
            "算法 / 数据工程师",
            "建设自动化与数据资产",
            ["明确样本需求", "验证数据格式", "开发算子与规则", "诊断自动节点", "构建数据集版本", "跟踪下游反馈"],
            [0, 2, 3, 4, 5],
            [4, 5],
        ),
        (
            "供应商管理员",
            "维护本组织人员和产能",
            ["确认承接范围", "查看组织数据", "维护用户组成员", "处理组内积压", "确认组织产出", "查看效率与异常"],
            [1, 2, 3, 5],
            [],
        ),
        (
            "操作员",
            "按用户组领取人工任务",
            ["", "", "查看任务规则", "领取 → 工作台 → 提交", "查看个人结果", "查看个人表现"],
            [3],
            [3],
        ),
    ]
    row_h = 124
    for r, (role, subtitle, cells, primary, core) in enumerate(rows):
        y = top + 94 + r * row_h
        body += rect(34, y, 246, row_h - 10, WHITE, LINE, 10)
        body += text(54, y + 38, role, 17, INK, 600)
        body += text(54, y + 68, subtitle, 13, MUTED)
        for c, value in enumerate(cells):
            x = left + c * col_w
            if not value:
                body += rect(x, y, col_w - 8, row_h - 10, BG, LINE, 8, 1, "6 7")
                continue
            is_primary = c in primary
            is_core = c in core
            body += rect(
                x,
                y,
                col_w - 8,
                row_h - 10,
                ACCENT_BG if is_core else WHITE,
                ACCENT if is_core else LINE,
                8,
                1.5,
                None if is_primary else "6 7",
            )
            body += text(
                x + 18,
                y + 42,
                value,
                15,
                INK,
                600 if is_core else (500 if is_primary else 400),
            )
            body += text(
                x + 18,
                y + 72,
                "核心主线" if is_core else ("主责" if is_primary else "参与 / 支持"),
                12,
                ACCENT if is_core else MUTED,
                500,
            )

    main_y = 1018
    body += text(40, main_y - 12, "核心业务主线", 15, INK, 600)
    names = ["配置项目", "形成 Recording", "开启处理任务", "运行流程与人工任务", "发布 Dataset Version", "消费反馈"]
    for i, name in enumerate(names):
        cx = left + i * col_w + (col_w - 8) / 2
        body += f'<circle cx="{cx}" cy="{main_y}" r="5.5" fill="{ACCENT}"/>'
        body += label(cx, main_y + 32, name, INK)
        if i < len(names) - 1:
            body += line(
                cx + 7,
                main_y,
                left + (i + 1) * col_w + (col_w - 8) / 2 - 7,
                main_y,
                ACCENT,
                1.5,
                marker_id="swimlane-arrow",
            )
    save(
        "user-business-swimlane",
        w,
        h,
        "用户 × 业务流程泳道",
        "角色控制菜单和数据范围；用户组控制人工任务领取资格。",
        body,
    )


def diagram_object_model():
    w, h = 2100, 1350
    body = f"""
<defs>
  <marker id="object-arrow-blue" markerWidth="7" markerHeight="7" refX="6.5" refY="3.5"
          orient="auto" markerUnits="userSpaceOnUse">
    <path d="M0,0 L6.5,3.5 L0,7 Z" fill="{ACCENT}"/>
  </marker>
  <marker id="object-arrow-gray" markerWidth="7" markerHeight="7" refX="6.5" refY="3.5"
          orient="auto" markerUnits="userSpaceOnUse">
    <path d="M0,0 L6.5,3.5 L0,7 Z" fill="{LINE_DARK}"/>
  </marker>
</defs>
"""

    def object_line(x1, y1, x2, y2, color=LINE_DARK, arrow=True, dash=None):
        marker_id = "object-arrow-blue" if color == ACCENT else "object-arrow-gray"
        marker = f' marker-end="url(#{marker_id})"' if arrow else ""
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        return (
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="1.35" stroke-linecap="round" '
            f'fill="none"{marker}{dash_attr}/>'
        )

    def object_path(points, color=LINE_DARK, arrow=True, dash=None):
        marker_id = "object-arrow-blue" if color == ACCENT else "object-arrow-gray"
        marker = f' marker-end="url(#{marker_id})"' if arrow else ""
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        d = " ".join(
            [f"M {points[0][0]} {points[0][1]}"]
            + [f"L {x} {y}" for x, y in points[1:]]
        )
        return (
            f'<path d="{d}" stroke="{color}" stroke-width="1.35" '
            f'stroke-linecap="round" stroke-linejoin="round" '
            f'fill="none"{marker}{dash_attr}/>'
        )

    layers = [
        (122, "业务与接入对象", "定义范围、来源和持续处理规则"),
        (402, "流程定义与任务配置对象", "流程仅定义节点拓扑；规则配置归属处理任务"),
        (722, "运行与人工协作对象", "记录每次实际执行和领取"),
        (1042, "数据资产对象", "保存不可覆盖的结果、快照和版本"),
    ]
    heights = [260, 300, 300, 220]
    for (y, title, subtitle), height in zip(layers, heights):
        body += section(32, y, 2036, height, title, subtitle)

    # 业务层：主干对象横向推进，来源任务与任务级定义收拢为两个子域。
    body += card(62, 218, 180, 90, "项目", ["Project", "权限与交付边界"], center=True)
    body += rect(270, 178, 270, 166, WHITE, LINE, 12)
    body += text(290, 204, "数据接入", 14, INK, 600)
    body += card(290, 216, 230, 50, "采集任务", ["data_collection_task"], center=True, small=True)
    body += card(290, 278, 230, 50, "导入任务", ["data_import_task"], center=True, small=True)
    body += card(580, 218, 210, 90, "数据记录", ["Recording", "统一数据记录"], active=True, center=True)
    body += card(
        840,
        198,
        260,
        130,
        "处理任务",
        ["Processing Task", "开启状态 · 选数游标 · 规则配置", "data_processing_task"],
        active=True,
        center=True,
    )
    body += rect(1140, 178, 868, 166, WHITE, LINE, 12)
    body += text(1160, 204, "处理定义", 14, INK, 600)
    body += card(
        1160,
        216,
        220,
        104,
        "选数规则",
        ["Selection Rule", "版本化 · 筛选条件 · 抽样规则"],
        center=True,
    )
    body += card(
        1410,
        216,
        288,
        104,
        "任务环节",
        ["Task Stage", "处理环节 · Flow Version", "顺序 · 进入条件"],
        center=True,
    )
    body += card(1730, 228, 250, 82, "处理环节", ["Business Stage", "产品分组"], dashed=True, center=True)

    body += object_line(242, 252, 290, 241)
    body += object_line(242, 264, 290, 303)
    body += object_line(520, 241, 580, 251, ACCENT)
    body += object_line(520, 303, 580, 275, ACCENT)
    body += object_line(790, 263, 840, 263, ACCENT)
    body += object_line(1100, 250, 1160, 250)
    body += object_path([(1020, 328), (1020, 350), (1490, 350), (1490, 320)])
    body += object_line(1698, 268, 1730, 268)
    body += label(260, 224, "1:N")
    body += label(260, 292, "1:N")
    body += label(550, 230, "1:N")
    body += label(550, 294, "1:N")
    body += label(815, 250, "1:N")
    body += label(1115, 236, "1:N")
    body += label(1255, 344, "1:N")
    body += label(1714, 252, "N:1")

    # 流程与配置层：流程模板、任务专属配置、人工节点绑定三块并列，
    # 通过归属和引用关系连接，而不是把所有对象排成一条直线。
    body += rect(62, 482, 860, 170, WHITE, LINE, 12)
    body += text(84, 508, "流程编排", 14, INK, 600)
    body += card(92, 520, 220, 94, "流程", ["Flow", "可编辑模板"], center=True)
    body += card(
        356,
        510,
        238,
        114,
        "流程版本",
        ["Flow Version", "节点 · 连线 · 条件", "发布后不可变 · 不含任务规则"],
        active=True,
        center=True,
    )
    body += card(650, 520, 230, 94, "节点", ["Node", "operator / human / gateway"], center=True)

    body += rect(960, 482, 360, 170, WHITE, LINE, 12)
    body += text(982, 508, "任务配置", 14, INK, 600)
    body += card(
        998,
        510,
        284,
        114,
        "任务节点配置",
        ["Task Node Config", "规则引用 · 参数值 · 处理环节", "按目标节点运行时读取"],
        center=True,
    )

    body += rect(1358, 482, 650, 170, WHITE, LINE, 12)
    body += text(1380, 508, "人工节点配置", 14, INK, 600)
    body += card(
        1390,
        510,
        280,
        114,
        "工作台版本",
        ["Workbench Version", "人工节点单选 · 组件布局", "数据绑定"],
        center=True,
    )
    body += card(1710, 510, 250, 114, "用户组", ["User Group", "人工节点多选 · 作业资格"], center=True)

    body += object_line(312, 567, 356, 567, ACCENT)
    body += object_line(594, 567, 650, 567, ACCENT)
    body += object_path([(970, 328), (970, 440), (1140, 440), (1140, 510)])
    body += label(986, 434, "拥有 1:N")
    body += object_line(998, 567, 880, 567)
    body += label(334, 552, "1:N")
    body += label(622, 552, "1:N")
    body += label(914, 548, "N:1 配置目标")
    body += object_path([(765, 614), (765, 668), (1530, 668), (1530, 624)])
    body += object_path([(795, 614), (795, 686), (1835, 686), (1835, 624)])
    body += label(1090, 662, "每个 human 节点：1 个工作台版本")
    body += label(1390, 683, "每个 human 节点：1 个用户组")
    body += object_path([(1600, 320), (1600, 414), (475, 414), (475, 510)])
    body += label(1000, 408, "N:1 引用流程版本")

    # 运行层：主运行实例在左，人工节点的领取与执行收拢成闭环子域。
    body += card(70, 824, 210, 100, "流程运行", ["Flow Run", "一次流程执行"], active=True, center=True)
    body += card(330, 824, 210, 100, "节点运行", ["Node Run", "一次节点执行"], center=True)
    body += rect(590, 770, 760, 204, WHITE, LINE, 12)
    body += text(612, 798, "人工作业", 14, INK, 600)
    body += card(
        630,
        822,
        220,
        110,
        "人工任务",
        ["Human Task", "人工节点生成", "唯一业务工作单元"],
        active=True,
        center=True,
    )
    body += card(930, 792, 220, 84, "任务池", ["Task Pool", "按用户组形成领取视图"], center=True)
    body += card(930, 888, 220, 72, "任务锁", ["Task Lock"], center=True, small=True)
    body += card(1500, 824, 220, 100, "流程输出", ["Flow Output", "结构化结果"], active=True, center=True)
    body += object_line(280, 874, 330, 874, ACCENT)
    body += object_line(540, 874, 630, 874, ACCENT)
    body += object_path([(850, 877), (890, 877), (890, 834), (930, 834)], ACCENT)
    body += object_line(1040, 876, 1040, 888, ACCENT)
    body += object_path([(1150, 924), (1220, 924), (1220, 874), (1500, 874)], ACCENT)
    body += object_path([(740, 822), (740, 790), (435, 790), (435, 824)], arrow=True, dash="6 6")
    body += label(515, 782, "回写对应 Node Run")
    body += label(305, 860, "1:N")
    body += label(565, 860, "human 节点 1:1")
    body += label(888, 822, "N:1")
    body += label(1090, 886, "每个任务 0..1 个有效锁")
    body += label(1360, 862, "按工作台版本执行并提交；流程完成后输出")

    # 资产层：先固化不可覆盖结果，再组织为可发布的数据集资产。
    body += rect(62, 1110, 690, 130, WHITE, LINE, 12)
    body += text(84, 1136, "结果版本", 14, INK, 600)
    body += card(92, 1142, 240, 88, "记录版本", ["Recording Version", "原始数据不可覆盖"], center=True)
    body += card(
        382,
        1142,
        320,
        88,
        "结果版本",
        ["Result Version", "每条流程独立结果 Key"],
        active=True,
        center=True,
    )
    body += rect(790, 1110, 1218, 130, WHITE, LINE, 12)
    body += text(812, 1136, "数据集发布", 14, INK, 600)
    body += card(820, 1142, 230, 88, "数据快照", ["Data Snapshot", "Recording ID + 结果版本"], center=True)
    body += card(1100, 1142, 220, 88, "数据集", ["Dataset", "逻辑资产"], center=True)
    body += card(1370, 1142, 260, 88, "数据集版本", ["Dataset Version", "冻结 · 发布 · 可引用"], active=True, center=True)
    body += card(1680, 1142, 280, 88, "数据血缘", ["Data Lineage", "连接输入、运行和输出"], dashed=True, center=True)
    body += object_line(332, 1186, 382, 1186, ACCENT)
    body += object_line(702, 1186, 820, 1186, ACCENT)
    body += object_line(1050, 1186, 1100, 1186, ACCENT)
    body += object_line(1320, 1186, 1370, 1186, ACCENT)
    body += object_line(1630, 1186, 1680, 1186, ACCENT)
    body += object_path([(1610, 924), (1610, 1064), (542, 1064), (542, 1142)], ACCENT)
    body += label(357, 1172, "1:N")
    body += label(760, 1172, "N:M 成员")
    body += label(1075, 1172, "N:1")
    body += label(1345, 1172, "1:N")
    body += label(1655, 1172, "1:N")
    body += label(1200, 1058, "1:N 结果条目")

    # 节点颜色、边框和关系线图例。
    body += rect(32, 1282, 2036, 48, PANEL, LINE, 10)
    body += text(54, 1312, "图例", 14, INK, 600)

    body += rect(112, 1296, 28, 20, ACCENT_BG, ACCENT, 4)
    body += text(152, 1312, "核心主线对象", 13, INK, 500)

    body += rect(326, 1296, 28, 20, WHITE, LINE_DARK, 4)
    body += text(366, 1312, "支撑与配置对象", 13, INK, 500)

    body += rect(566, 1296, 28, 20, WHITE, LINE_DARK, 4, 1.5, "5 4")
    body += text(606, 1312, "逻辑关系对象", 13, INK, 500)

    body += object_line(806, 1306, 858, 1306, ACCENT)
    body += text(878, 1312, "核心业务流转", 13, INK, 500)

    body += object_line(1086, 1306, 1138, 1306)
    body += text(1158, 1312, "引用 / 绑定关系", 13, INK, 500)

    body += object_line(1392, 1306, 1444, 1306, arrow=False, dash="6 5")
    body += text(1464, 1312, "回写 / 追溯关系", 13, INK, 500)

    save(
        "core-object-model",
        w,
        h,
        "核心概念与对象关系",
        "处理任务负责选数和规则配置；流程版本负责定义执行；运行实例记录事实；数据资产保存版本与血缘。",
        body,
    )


def diagram_product_architecture():
    w, h = 2000, 1180
    body = ""
    layer_specs = [
        (124, 252, "业务应用层", "面向角色的产品入口"),
        (406, 196, "配置与定义层", "发布不可变配置版本"),
        (632, 244, "核心引擎层", "维护运行状态与执行语义"),
        (906, 166, "数据与平台底座", "提供共享技术能力"),
    ]
    for y, height, name, subtitle in layer_specs:
        body += rect(32, y, 210, height, SOFT, LINE, 14)
        body += text(137, y + 44, name, 21, INK, 600, "middle")
        body += text(137, y + 76, subtitle, 13, MUTED, 400, "middle")
        body += rect(262, y, 1706, height, WHITE, LINE, 14)

    app_modules = [
        ("任务管理", ["采集任务", "处理任务", "分配管理"]),
        ("数据资产", ["数据管理", "数据集管理"]),
        ("工作台", ["工作台", "个人看板"]),
        ("运营管理", ["供应商管理", "人员管理", "权限管理"]),
    ]
    for i, (title, items) in enumerate(app_modules):
        x = 292 + i * 414
        body += section(x, 158, 372, 184, title)
        for j, item in enumerate(items):
            body += card(x + 18, 210 + j * 40, 336, 32, item, center=True, small=True)

    config_modules = [
        ("工作流", ["流程管理", "执行记录", "算子管理", "工作台管理"]),
        ("配置管理", ["项目管理", "规则管理", "场景管理", "标签管理"]),
        ("组织与授权", ["人员", "角色", "用户组", "授权（静态资源）"]),
    ]
    for i, (title, items) in enumerate(config_modules):
        x = 292 + i * 552
        body += section(x, 438, 510, 132, title)
        for j, item in enumerate(items):
            col = j % 2
            row = j // 2
            body += card(x + 18 + col * 242, 482 + row * 39, 224, 31, item, center=True, small=True)

    engines = [
        ("持续接入服务", ["筛选版本", "处理水位"]),
        ("工作流引擎", ["Flow / Node Run", "条件与回流"]),
        ("算子运行时", ["镜像与参数", "重试与资源"]),
        ("人工任务服务", ["用户组路由", "任务池与锁"]),
        ("工作台运行时", ["组件渲染", "校验与提交"]),
        ("数据版本服务", ["结果版本", "快照与血缘"]),
    ]
    for i, (title, details) in enumerate(engines):
        x = 286 + i * 276
        body += card(x, 684, 246, 142, title, details, center=True, small=True)

    base_items = [
        ("对象与元数据存储", "Recording · 版本 · 配置"),
        ("事件与任务队列", "持续接入 · 异步执行"),
        ("权限与审计", "租户 · 项目 · 操作日志"),
        ("检索与开放接口", "查询 · Webhook · API"),
    ]
    for i, (title, detail) in enumerate(base_items):
        body += card(292 + i * 414, 948, 372, 80, title, [detail], center=True, small=True)

    body += text(
        1000,
        1120,
        "页面发起命令并读取状态；配置层产出版本；引擎层维护运行事实；底座不承载业务状态机。",
        15,
        MUTED,
        400,
        "middle",
    )
    save(
        "product-architecture",
        w,
        h,
        "产品架构",
        "通过业务应用、配置定义、核心引擎和平台底座四层划分职责。",
        body,
    )


def diagram_processing_task_flow_binding():
    w, h = 2040, 1050
    body = ""
    body += section(34, 126, 342, 808, "数据湖", "同一数据可命中多个处理任务")
    recs = [
        ("rec-001", "项目 A · 合格"),
        ("rec-002", "项目 A · 待处理"),
        ("rec-003", "项目 B · DAgger"),
        ("rec-004", "项目 A · 合格"),
        ("rec-005", "项目 C · 导入"),
    ]
    for i, (rid, meta) in enumerate(recs):
        body += card(70, 220 + i * 112, 270, 82, rid, [meta], center=True, small=True)

    body += section(420, 126, 514, 808, "数据处理任务", "持续筛选与流程绑定")
    tasks = [
        ("处理任务 A", ["状态：开启", "项目=A 且结论=合格", "水位：2026-07-29 10:30"]),
        ("处理任务 B", ["状态：开启", "来源=DAgger", "水位：2026-07-29 10:27"]),
        ("处理任务 C", ["状态：关闭", "项目=C", "不再接收新数据"]),
    ]
    task_y = [210, 446, 682]
    for i, (name, details) in enumerate(tasks):
        body += card(462, task_y[i], 430, 174, name, details, active=i < 2, center=True)
        body += card(506, task_y[i] + 116, 342, 40, "筛选版本 + Flow Binding", center=True, small=True)
    body += path([(340, 261), (402, 261), (402, 286), (462, 286)], ACCENT, 3)
    body += path([(340, 485), (402, 485), (402, 522), (462, 522)], ACCENT, 3)
    body += path([(340, 709), (402, 709), (402, 758), (462, 758)], LINE_DARK, 2, True, "7 6")

    body += section(978, 126, 1028, 808, "业务环节与独立流程", "每个绑定引用已发布的 Flow Version")
    stages = [("质检", 1030), ("标注", 1365), ("验收", 1700)]
    for title, x in stages:
        body += section(x, 190, 260, 650, f"{title}环节", "产品侧分组", dash="7 6")

    flows = {
        1030: [
            ("自动质检 v3", 252),
            ("人工抽检 v2", 394),
            ("DAgger 检查 v1", 536),
        ],
        1365: [
            ("端到端标注 v2", 252),
            ("两轮人工标注 v2", 394),
            ("新规实验标注 v1", 536),
        ],
        1700: [
            ("数据验收 v1", 252),
            ("抽样验收 v2", 394),
        ],
    }
    for x, items in flows.items():
        for title, y in items:
            body += card(x + 22, y, 216, 86, title, ["独立 Input / Output"], center=True, small=True)

    body += path([(892, 280), (956, 280), (956, 295), (1052, 295)], ACCENT, 3)
    body += path([(892, 522), (956, 522), (956, 579), (1052, 579)], ACCENT, 3)
    body += path([(892, 302), (940, 302), (940, 295), (1387, 295)], LINE_DARK, 2)
    body += path([(892, 544), (926, 544), (926, 437), (1387, 437)], LINE_DARK, 2)
    body += path([(892, 324), (912, 324), (912, 295), (1722, 295)], LINE_DARK, 2)
    body += path([(892, 566), (900, 566), (900, 437), (1722, 437)], LINE_DARK, 2)
    body += label(1098, 898, "处理任务 A：自动质检 v3 → 端到端标注 v2 → 数据验收 v1", INK)
    body += label(1592, 898, "处理任务 B：DAgger 检查 v1 → 两轮人工标注 v2 → 抽样验收 v2", INK)

    body += rect(420, 966, 1586, 58, ACCENT_BG, ACCENT, 10)
    body += text(
        1213,
        1003,
        "业务环节只负责组织和衔接；底层引擎最终执行的仍是统一 Node + Transition 图。",
        15,
        INK,
        500,
        "middle",
    )
    save(
        "processing-task-flow-binding",
        w,
        h,
        "数据处理任务与流程绑定",
        "处理任务持续筛选数据，并分别绑定各业务环节的独立流程。",
        body,
    )


def diagram_task_allocation():
    w, h = 2000, 980
    body = ""
    body += section(42, 126, 1916, 228, "流程运行", "不同流程的人工节点可以路由到相同用户组")
    flow_nodes = [
        ("流程 A", "人工节点 A", 90),
        ("流程 A", "人工节点 B", 400),
        ("流程 B", "人工节点 C", 710),
        ("流程 C", "人工节点 D", 1020),
        ("流程 C", "人工节点 E", 1330),
        ("流程 D", "人工节点 F", 1640),
    ]
    for flow, node, x in flow_nodes:
        body += card(x, 210, 250, 88, node, [flow], center=True, small=True)

    body += section(42, 398, 1916, 246, "用户组任务池", "节点配置用户组；任务池是可领取视图，不复制业务任务")
    pools = [
        ("标注员用户组", "10 人", 180),
        ("标注抽检员用户组", "20 人", 700),
        ("新规实验标注员用户组", "8 人", 1220),
    ]
    for title, people, x in pools:
        body += card(x, 486, 420, 106, title, [f"任务池 · {people}", "pending Human Task"], active=True, center=True)

    mappings = [
        (215, 180 + 210),
        (525, 700 + 210),
        (835, 180 + 210),
        (1145, 700 + 210),
        (1455, 1220 + 210),
        (1765, 1220 + 210),
    ]
    for x1, x2 in mappings:
        body += path([(x1, 298), (x1, 380), (x2, 380), (x2, 486)], LINE_DARK, 2)

    body += section(42, 688, 1916, 214, "领取与执行", "组内成员领取后进入节点绑定的工作台")
    users = [
        ("用户 A", "标注员组", 160),
        ("用户 B", "标注员 + 抽检员组", 570),
        ("用户 C", "抽检员组", 980),
        ("用户 D", "新规实验组", 1390),
    ]
    for name, groups, x in users:
        body += card(x, 760, 300, 88, name, [groups], center=True, small=True)
    body += path([(390, 592), (390, 672), (310, 672), (310, 760)], ACCENT, 3)
    body += path([(910, 592), (910, 672), (720, 672), (720, 760)], ACCENT, 3)
    body += path([(910, 592), (910, 672), (1130, 672), (1130, 760)], ACCENT, 3)
    body += path([(1430, 592), (1430, 672), (1540, 672), (1540, 760)], ACCENT, 3)
    body += label(1000, 934, "多组可见时仍是同一个 Human Task；首个成功领取者获得任务锁，提交结果回写原 Node Run。", INK)
    save(
        "task-allocation",
        w,
        h,
        "人工任务分配",
        "节点绑定用户组，任务进入用户组任务池，组内成员领取并在工作台执行。",
        body,
    )


def diagram_workbench():
    w, h = 2000, 1060
    body = ""
    body += section(40, 126, 1920, 252, "组件注册表", "组件定义输入、输出、校验和渲染能力")
    components = [
        ("数据信息", "任务与 Recording"),
        ("多视角视频", "三路同步"),
        ("单路视频", "头部摄像头"),
        ("时间轴", "逐帧与区间"),
        ("动作编辑器", "动作元素 + 描述"),
        ("层级编辑器", "High-level / Low-level"),
        ("辅助信息", "轨迹与日志"),
        ("任务操作", "提交 / 驳回 / 暂离"),
    ]
    for i, (name, detail) in enumerate(components):
        col = i % 4
        row = i // 4
        body += card(82 + col * 468, 206 + row * 84, 420, 64, name, [detail], center=True, small=True)

    body += section(40, 420, 1180, 414, "工作台定义与版本", "从组件库中选择、布局、校验并发布")
    body += section(82, 488, 520, 290, "工作台 A · 动作标注", "wb.action@2.0", accent=True)
    body += card(112, 550, 460, 48, "数据信息", center=True, small=True)
    body += card(112, 612, 216, 68, "三路视频", center=True, small=True)
    body += card(356, 612, 216, 68, "时间轴", center=True, small=True)
    body += card(112, 696, 296, 52, "动作元素 + 动作描述", center=True, small=True)
    body += card(424, 696, 148, 52, "提交 / 驳回", center=True, small=True)

    body += section(658, 488, 520, 290, "工作台 B · 层级语义", "wb.hierarchy@1.0")
    body += card(688, 550, 460, 48, "数据信息", center=True, small=True)
    body += card(688, 612, 460, 68, "单路视频", center=True, small=True)
    body += card(688, 696, 296, 52, "High-level / Low-level", center=True, small=True)
    body += card(1000, 696, 148, 52, "提交", center=True, small=True)

    body += section(1264, 420, 696, 414, "人工节点配置", "节点决定谁处理、如何处理和允许做什么")
    body += card(1306, 496, 612, 76, "基础信息", ["节点名称 · 节点 ID · 输入输出"], center=True)
    body += card(1306, 594, 612, 62, "工作台版本：单选", ["wb.action@2.0"], active=True, center=True, small=True)
    body += card(1306, 678, 612, 62, "处理用户组：多选", ["标注员组 · 新规实验组"], center=True, small=True)
    body += card(1306, 762, 612, 44, "允许动作：submit · reject · leave", center=True, small=True)

    body += path([(518, 378), (518, 420)], ACCENT, 3)
    body += path([(984, 378), (984, 420)], ACCENT, 3)
    body += line(1220, 626, 1306, 626, ACCENT, 3)

    body += section(40, 874, 1920, 122, "工作台运行时", "根据节点绑定版本渲染页面，并按节点允许动作校验提交")
    body += card(84, 922, 380, 48, "加载 Human Task 与数据", center=True, small=True)
    body += card(550, 922, 380, 48, "渲染 Workbench Version", center=True, small=True)
    body += card(1016, 922, 380, 48, "校验字段与动作", center=True, small=True)
    body += card(1482, 922, 430, 48, "提交结果并回写 Node Run", active=True, center=True, small=True)
    body += line(464, 946, 550, 946, ACCENT, 3)
    body += line(930, 946, 1016, 946, ACCENT, 3)
    body += line(1396, 946, 1482, 946, ACCENT, 3)
    save(
        "workbench-configuration",
        w,
        h,
        "工作台组件化配置",
        "组件库组成工作台版本；人工节点单选工作台、多选用户组，并声明允许动作。",
        body,
    )


def diagram_cases():
    w, h = 2000, 900
    body = ""
    cases = [
        (42, "Case 1｜自动与人工混合", "适用于正式生产流程"),
        (686, "Case 2｜纯算子编排", "适用于批处理与标准化"),
        (1330, "Case 3｜多轮人工处理", "适用于新规则或复杂数据"),
    ]
    for x, title, subtitle in cases:
        body += section(x, 132, 610, 676, title, subtitle)

    # Case 1
    x = 92
    mixed = [
        ("input", "输入数据", False),
        ("operator", "自动检查", False),
        ("gateway", "是否需人工", True),
        ("human", "人工处理", False),
        ("operator", "自动切分", False),
        ("output", "结果版本", False),
    ]
    ys = [224, 316, 408, 500, 592, 684]
    for (kind, title, dash), y in zip(mixed, ys):
        body += card(x + 108, y, 294, 58, title, center=True, small=True, dashed=dash, active=kind == "output")
    for y1, y2 in zip(ys[:-1], ys[1:]):
        body += line(x + 255, y1 + 58, x + 255, y2, ACCENT, 3)
    body += label(x + 430, 452, "人工节点生成任务")
    body += label(x + 430, 544, "提交后回写流程")

    # Case 2
    x = 736
    auto_nodes = ["输入数据", "格式校验", "时间对齐", "Episode 切分", "统计与过滤", "结果版本"]
    for i, title in enumerate(auto_nodes):
        y = 224 + i * 92
        body += card(x + 108, y, 294, 58, title, center=True, small=True, active=i == len(auto_nodes) - 1)
        if i < len(auto_nodes) - 1:
            body += line(x + 255, y + 58, x + 255, y + 92, ACCENT, 3)
    body += label(x + 255, 782, "不生成 Human Task", INK)

    # Case 3
    x = 1380
    manual_nodes = ["输入数据", "人工标注", "抽样检查", "是否通过", "退回原节点 / 继续", "结果版本"]
    for i, title in enumerate(manual_nodes):
        y = 224 + i * 92
        body += card(
            x + 108,
            y,
            294,
            58,
            title,
            center=True,
            small=True,
            dashed=i == 3,
            active=i == len(manual_nodes) - 1,
        )
        if i < len(manual_nodes) - 1:
            body += line(x + 255, y + 58, x + 255, y + 92, ACCENT, 3)
    body += path([(x + 108, 622), (x + 58, 622), (x + 58, 345), (x + 108, 345)], LINE_DARK, 2, True, "7 6")
    body += label(x + 50, 494, "退回", MUTED, "end")

    body += rect(42, 838, 1898, 42, ACCENT_BG, ACCENT, 8)
    body += text(
        991,
        865,
        "三类 Case 共用同一套 Flow、Node、Run 和 Result Version 对象，只改变节点组合、条件和人工协作配置。",
        14,
        INK,
        500,
        "middle",
    )
    save(
        "processing-cases",
        w,
        h,
        "典型处理流程 Case",
        "人工与自动化混排、纯算子编排和多轮人工流程共用统一引擎模型。",
        body,
    )


def diagram_state_model():
    w, h = 2000, 900
    body = ""
    lanes = [
        ("数据处理任务", ["草稿", "开启", "关闭"], ["发布并开启", "停止接收新数据"]),
        ("Flow Run", ["待开始", "运行中", "已完成", "已终止", "失败"], ["触发", "节点完成", "人工终止", "异常"]),
        ("Node Run", ["未开始", "待处理", "处理中", "已跳过", "已完成", "失败"], ["依赖满足", "执行", "条件跳过", "产出"]),
        ("Human Task", ["待领取", "已领取", "处理中", "已提交", "已退回", "已取消"], ["入池", "领取锁定", "打开工作台", "提交"]),
    ]
    y0 = 150
    lane_h = 165
    for i, (lane_name, states, transitions) in enumerate(lanes):
        y = y0 + i * lane_h
        body += rect(36, y, 246, 122, SOFT, LINE, 12)
        body += text(159, y + 48, lane_name, 19, INK, 600, "middle")
        body += text(159, y + 80, "独立状态域", 13, MUTED, 400, "middle")
        available = 1640
        gap = 22
        state_w = (available - gap * (len(states) - 1)) / len(states)
        sx = 320
        centers = []
        for s, state in enumerate(states):
            active = state in ("开启", "运行中", "处理中", "待领取")
            body += card(sx, y + 26, state_w, 66, state, center=True, small=True, active=active)
            centers.append(sx + state_w / 2)
            if s < len(states) - 1:
                body += line(sx + state_w, y + 59, sx + state_w + gap, y + 59, ACCENT if s < 2 else LINE_DARK, 2)
            sx += state_w + gap
        for t, transition in enumerate(transitions[: len(centers) - 1]):
            mx = (centers[t] + centers[t + 1]) / 2
            body += label(mx, y + 116, transition)

    body += rect(36, 822, 1928, 52, ACCENT_BG, ACCENT, 10)
    body += text(
        1000,
        855,
        "关闭处理任务不等于终止 Flow Run；Human Task 提交不等于流程完成。各层状态分别维护，通过领域事件关联。",
        15,
        INK,
        500,
        "middle",
    )
    save(
        "state-model",
        w,
        h,
        "分层状态模型",
        "处理任务、流程、节点和人工任务分别维护状态，避免一个状态承担多层语义。",
        body,
    )


def main():
    diagram_product_boundary()
    diagram_end_to_end()
    diagram_swimlane()
    diagram_object_model()
    diagram_product_architecture()
    diagram_processing_task_flow_binding()
    diagram_task_allocation()
    diagram_workbench()
    diagram_cases()
    diagram_state_model()
    print(f"generated 10 diagrams in {OUT}")


if __name__ == "__main__":
    main()
