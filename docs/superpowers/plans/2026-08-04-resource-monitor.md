# 资源监控页面 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在模型平台侧边栏新增「管理 > 资源监控」页面，以表格展示火山云资源队列的使用情况。

**Architecture:** 单文件 Flask 原型 `toolchain_demo.py` 内新增 Mock 数据、CSS 类、渲染 helper、路由与导航项。页面为纯展示表格 + toast 占位交互，无详情页、无创建入口。

**Tech Stack:** Flask 3.0+, Python 3.11+, 内联 HTML 模板（Ant Design v4 主题, 主色 #149DAA）。

## Global Constraints

- 所有改动集中在单文件 `toolchain_demo.py`，遵循现有内联模板 + Mock 数据模式。
- 无数据库、无持久化、无真实接口；筛选/搜索/刷新均为 `toast()` 占位。
- 主题色 `#149DAA`；代码注释用英文；commit 用英文约定式提交。
- 无测试框架：每个任务的验证 = `ast.parse` 语法检查 + 浏览器人工验证。
- 手术式改动：不重构无关代码，不新增需求外功能。

---

## File Structure

- Modify: `toolchain_demo.py`
  - Section 1 (Mock Data): 新增 `RESOURCE_QUEUES` 列表
  - Section 2 (Platform Config): `PLATFORMS["model"]["nav"]` 追加「管理」组
  - Section 3 (BASE CSS): 新增资源单元格 / 状态圆点 / 横向滚动容器样式
  - Section 4 (Helpers): 新增 `res_bar()` helper
  - Section 7 (模型平台路由): 新增 `/model/resource-monitor` 路由

---

### Task 1: Mock 数据 + 侧边栏导航

**Files:**
- Modify: `toolchain_demo.py` (Section 1, EXPERIMENTS/CHECKPOINTS 之间, 约 439-441 行附近)
- Modify: `toolchain_demo.py` (Section 2, `PLATFORMS["model"]["nav"]` 结尾, 约 650 行 `]),` 之后)

**Interfaces:**
- Produces: 模块级常量 `RESOURCE_QUEUES: list[dict]`。每项字段:
  - `name: str`
  - `status: str` — 取值 `"running" | "stopped" | "closed"`
  - `gpu: dict` — `{"used": num, "total": num, "unit": str, "model": str}`
  - `vcpu / disk / mem / ssd_flex / ssd_pl0: dict` — `{"used": num, "total": num, "unit": str}`
- Produces: 导航项 `("/model/resource-monitor", "资源监控", "&#9736;", "新增")`，供 Task 4 路由的 `active` 匹配。

- [ ] **Step 1: 在 Section 1 新增 RESOURCE_QUEUES**

在 `toolchain_demo.py` 第 439 行 `]`（MODELS 列表结尾）之后、第 441 行 `# ── 训练 · Checkpoint ──` 之前插入。数据覆盖三种状态与四档占用率（含 0%、中段、100%）:

```python

# ── 管理 · 资源监控（火山云资源队列 Mock）──

RESOURCE_QUEUES = [
    {"name": "Demo",
     "status": "closed",
     "gpu":      {"used": 6,   "total": 6,   "unit": "",     "model": "NVIDIA-A800-SXM4-80GB"},  # 100% -> red
     "vcpu":     {"used": 112, "total": 112, "unit": "vCPU"},                                     # 100% -> red
     "disk":     {"used": 0,   "total": 2.0, "unit": "TiB"},                                      # 0%   -> low
     "mem":      {"used": 1.9, "total": 1.9, "unit": "TiB"},                                       # 100% -> red
     "ssd_flex": {"used": 0,   "total": 2.0, "unit": "TiB"},
     "ssd_pl0":  {"used": 0,   "total": 0,   "unit": "GiB"}},
    {"name": "GPU-DataCollecting",
     "status": "closed",
     "gpu":      {"used": 8,   "total": 8,   "unit": "",     "model": "NVIDIA-A800-SXM4-80GB"},   # 100% -> red
     "vcpu":     {"used": 0,   "total": 0,   "unit": "vCPU"},
     "disk":     {"used": 0,   "total": 0,   "unit": "GiB"},
     "mem":      {"used": 0,   "total": 0,   "unit": "GiB"},
     "ssd_flex": {"used": 0,   "total": 0,   "unit": "GiB"},
     "ssd_pl0":  {"used": 960, "total": 960, "unit": "GiB"}},                                      # 100% -> red
    {"name": "train-pi05-main",
     "status": "running",
     "gpu":      {"used": 24,  "total": 32,  "unit": "",     "model": "NVIDIA-A800-SXM4-80GB"},   # 75%  -> mid
     "vcpu":     {"used": 320, "total": 512, "unit": "vCPU"},                                      # 62%  -> mid
     "disk":     {"used": 4.2, "total": 8.0, "unit": "TiB"},                                       # 52%  -> low
     "mem":      {"used": 6.1, "total": 8.0, "unit": "TiB"},                                       # 76%  -> mid
     "ssd_flex": {"used": 1.2, "total": 4.0, "unit": "TiB"},                                       # 30%  -> low
     "ssd_pl0":  {"used": 1.6, "total": 2.0, "unit": "TiB"}},                                      # 80%  -> mid
    {"name": "train-household-32",
     "status": "running",
     "gpu":      {"used": 30,  "total": 32,  "unit": "",     "model": "NVIDIA-H800-SXM5-80GB"},   # 93%  -> high
     "vcpu":     {"used": 448, "total": 512, "unit": "vCPU"},                                      # 87%  -> high
     "disk":     {"used": 6.8, "total": 8.0, "unit": "TiB"},                                       # 85%  -> high
     "mem":      {"used": 3.0, "total": 8.0, "unit": "TiB"},                                       # 37%  -> low
     "ssd_flex": {"used": 3.9, "total": 4.0, "unit": "TiB"},                                       # 97%  -> high
     "ssd_pl0":  {"used": 0.8, "total": 2.0, "unit": "TiB"}},                                      # 40%  -> low
    {"name": "eval-sandbox",
     "status": "stopped",
     "gpu":      {"used": 0,   "total": 8,   "unit": "",     "model": "NVIDIA-A800-SXM4-80GB"},   # 0%   -> low
     "vcpu":     {"used": 0,   "total": 128, "unit": "vCPU"},
     "disk":     {"used": 0.5, "total": 4.0, "unit": "TiB"},                                       # 12%  -> low
     "mem":      {"used": 0.2, "total": 4.0, "unit": "TiB"},                                       # 5%   -> low
     "ssd_flex": {"used": 0,   "total": 2.0, "unit": "TiB"},
     "ssd_pl0":  {"used": 0,   "total": 1.0, "unit": "TiB"}},
    {"name": "train-skewer-8",
     "status": "running",
     "gpu":      {"used": 5,   "total": 8,   "unit": "",     "model": "NVIDIA-A800-SXM4-80GB"},   # 62%  -> mid
     "vcpu":     {"used": 96,  "total": 128, "unit": "vCPU"},                                      # 75%  -> mid
     "disk":     {"used": 1.0, "total": 4.0, "unit": "TiB"},                                       # 25%  -> low
     "mem":      {"used": 2.0, "total": 4.0, "unit": "TiB"},                                       # 50%  -> low
     "ssd_flex": {"used": 0.4, "total": 2.0, "unit": "TiB"},                                       # 20%  -> low
     "ssd_pl0":  {"used": 0.6, "total": 1.0, "unit": "TiB"}},                                      # 60%  -> low
]
```

- [ ] **Step 2: 在 Section 2 追加「管理」导航组**

在 `PLATFORMS["model"]["nav"]` 的「公共配置」组 `]),`（约第 650 行）之后、闭合 `],`（约第 651 行）之前插入:

```python
            ("管理", [
                ("/model/resource-monitor", "资源监控", "&#9736;", "新增"),
            ]),
```

- [ ] **Step 3: 语法检查**

Run: `python -c "import ast; ast.parse(open('toolchain_demo.py', encoding='utf-8').read())"`
Expected: 无输出（退出码 0）

- [ ] **Step 4: 验证常量可加载且导航已注册**

Run: `python -c "import toolchain_demo as t; print(len(t.RESOURCE_QUEUES)); print([g[0] for g in t.PLATFORMS['model']['nav']])"`
Expected: 打印 `6` 及包含 `'管理'` 的分组名列表（末尾为 `'管理'`）

- [ ] **Step 5: Commit**

```bash
git add toolchain_demo.py
git commit -m "feat: add resource queue mock data and management nav entry"
```

---

### Task 2: CSS 样式 + res_bar() helper

**Files:**
- Modify: `toolchain_demo.py` (Section 3 BASE CSS, 进度条区 `.bar.fail` 之后, 约 1045 行)
- Modify: `toolchain_demo.py` (Section 4 Helpers, `progress_bar()` 之后, 约 2929 行)

**Interfaces:**
- Consumes: `RESOURCE_QUEUES` 各资源列的 dict 结构（Task 1）。
- Produces: helper `res_bar(used, total, unit, model=None) -> str`。返回一个 `<div class="res-cell">` HTML 片段：首行数字 `已用/总量 单位`（GPU 列追加型号），次行按占用率四档着色的细进度条。
- Produces: CSS 类 `.res-scroll`（表格横向滚动容器）、`.res-cell` / `.res-cell .num` / `.res-cell .model` / `.res-cell .rtrack` / `.res-cell .rfill`、四档色 `.rfill.lv-low/.lv-mid/.lv-high/.lv-full`、状态圆点 `.res-dot` / `.res-dot.running/.stopped/.closed`。

- [ ] **Step 1: 在 Section 3 新增 CSS**

在 `.bar.fail .fill { ... }`（约第 1045 行）之后插入:

```css
/* ── 管理 · 资源监控 ── */
.res-scroll { background:#fff; border:1px solid #f0f0f0; border-radius:8px; overflow-x:auto; }
.res-scroll .ant-table { min-width:1180px; border:0; }
.res-dot { display:inline-flex; align-items:center; gap:6px; font-size:13px; color:rgba(0,0,0,0.72); white-space:nowrap; }
.res-dot::before { content:''; width:7px; height:7px; border-radius:50%; display:inline-block; background:#bfbfbf; }
.res-dot.running::before { background:#52c41a; }
.res-dot.stopped::before { background:#E29845; }
.res-dot.closed::before  { background:#bfbfbf; }
.res-cell { min-width:130px; }
.res-cell .num { font-size:13px; color:rgba(0,0,0,0.78); font-family:'SF Mono',Menlo,monospace; white-space:nowrap; }
.res-cell .model { font-size:11px; color:rgba(0,0,0,0.42); margin-left:6px; font-family:inherit; }
.res-cell .rtrack { margin-top:6px; height:6px; background:#eef2f4; border-radius:3px; overflow:hidden; }
.res-cell .rfill { height:100%; border-radius:3px; background:#149DAA; }
.res-cell .rfill.lv-low  { background:#149DAA; }
.res-cell .rfill.lv-mid  { background:#d4a017; }
.res-cell .rfill.lv-high { background:#E29845; }
.res-cell .rfill.lv-full { background:#cf1322; }
```

- [ ] **Step 2: 在 Section 4 新增 res_bar() helper**

在 `progress_bar()` 函数（约第 2929 行结束）之后插入:

```python
def res_bar(used, total, unit, model=None):
    """Resource usage cell: number line + 4-level colored progress bar.
    Level thresholds by utilization: <60% low, <85% mid, <100% high, ==100% full."""
    pct = 0 if total == 0 else int(round(used * 100 / total))
    pct = min(pct, 100)
    if pct >= 100:
        lv = "lv-full"
    elif pct >= 85:
        lv = "lv-high"
    elif pct >= 60:
        lv = "lv-mid"
    else:
        lv = "lv-low"

    def _fmt(v):
        return str(int(v)) if float(v) == int(v) else f"{v:g}"

    unit_txt = f" {unit}" if unit else ""
    num = f'{_fmt(used)}/{_fmt(total)}{unit_txt}'
    model_html = f'<span class="model">{model}</span>' if model else ''
    return (f'<div class="res-cell"><div class="num">{num}{model_html}</div>'
            f'<div class="rtrack"><div class="rfill {lv}" style="width:{pct}%"></div></div></div>')
```

- [ ] **Step 3: 语法检查**

Run: `python -c "import ast; ast.parse(open('toolchain_demo.py', encoding='utf-8').read())"`
Expected: 无输出（退出码 0）

- [ ] **Step 4: 验证四档配色逻辑**

Run: `python -c "import toolchain_demo as t; [print(u, '->', 'lv-full' if 'lv-full' in t.res_bar(u,100,'') else 'lv-high' if 'lv-high' in t.res_bar(u,100,'') else 'lv-mid' if 'lv-mid' in t.res_bar(u,100,'') else 'lv-low') for u in (0,50,60,84,85,99,100)]"`
Expected:
```
0 -> lv-low
50 -> lv-low
60 -> lv-mid
84 -> lv-mid
85 -> lv-high
99 -> lv-high
100 -> lv-full
```

- [ ] **Step 5: 验证 total=0 与 GPU 型号透传**

Run: `python -c "import toolchain_demo as t; print('lv-low' in t.res_bar(0,0,'GiB')); print('NVIDIA-A800' in t.res_bar(6,8,'','NVIDIA-A800'))"`
Expected:
```
True
True
```

- [ ] **Step 6: Commit**

```bash
git add toolchain_demo.py
git commit -m "feat: add resource cell styles and res_bar helper"
```

---

### Task 3: /model/resource-monitor 路由 + 页面

**Files:**
- Modify: `toolchain_demo.py` (Section 7 模型平台路由末尾, `模型推理监测` 路由 `return` 之后、`# ── 评测 · Benchmark ──` 注释之前, 约 6550 行)

**Interfaces:**
- Consumes: `RESOURCE_QUEUES`（Task 1）、`res_bar()`（Task 2）、`render_page()`、`toast()`（现有）。
- Produces: Flask 路由 `GET /model/resource-monitor`，`active="/model/resource-monitor"` 与 Task 1 导航项匹配。

- [ ] **Step 1: 新增路由函数**

在第 6549 行（模型推理监测 `return` 语句）之后、第 6552 行 `# ── 评测 · Benchmark ──` 之前插入:

```python

# ── 管理 · 资源监控 ──

@app.route("/model/resource-monitor")
def resource_monitor():
    status_map = {
        "running": ("running", "运行中"),
        "stopped": ("stopped", "已停止"),
        "closed":  ("closed",  "已关闭"),
    }
    rows = ""
    for q in RESOURCE_QUEUES:
        cls, txt = status_map.get(q["status"], ("closed", q["status"]))
        g = q["gpu"]
        rows += f"""<tr>
          <td>{q['name']}</td>
          <td><span class="res-dot {cls}">{txt}</span></td>
          <td>{res_bar(g['used'], g['total'], g['unit'], g['model'])}</td>
          <td>{res_bar(q['vcpu']['used'], q['vcpu']['total'], q['vcpu']['unit'])}</td>
          <td>{res_bar(q['disk']['used'], q['disk']['total'], q['disk']['unit'])}</td>
          <td>{res_bar(q['mem']['used'], q['mem']['total'], q['mem']['unit'])}</td>
          <td>{res_bar(q['ssd_flex']['used'], q['ssd_flex']['total'], q['ssd_flex']['unit'])}</td>
          <td>{res_bar(q['ssd_pl0']['used'], q['ssd_pl0']['total'], q['ssd_pl0']['unit'])}</td>
        </tr>"""

    content = f"""
    <div class="filter-bar">
      <select onchange="toast('Demo: 状态筛选')">
        <option>全部状态</option><option>运行中</option><option>已停止</option><option>已关闭</option>
      </select>
      <input class="grow" placeholder="输入队列名称搜索" onkeydown="if(event.key==='Enter')toast('Demo: 搜索')">
      <div class="right">
        <button class="btn btn-tertiary" onclick="toast('Demo: 已刷新')">刷新</button>
      </div>
    </div>

    <div class="res-scroll">
      <table class="ant-table">
        <thead><tr>
          <th>名称</th>
          <th>状态 &#9662;</th>
          <th>GPU</th>
          <th>vCPU</th>
          <th>云盘</th>
          <th>MEM</th>
          <th>极速型SSD flexPL</th>
          <th>极速型SSD PL0</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return render_page("资源监控", content, active="/model/resource-monitor", module="model",
                       breadcrumb='模型平台 / <b>资源监控</b>', mvp_note="MVP 一期")
```

- [ ] **Step 2: 语法检查**

Run: `python -c "import ast; ast.parse(open('toolchain_demo.py', encoding='utf-8').read())"`
Expected: 无输出（退出码 0）

- [ ] **Step 3: 验证路由已注册且能渲染**

Run: `python -c "import toolchain_demo as t; c=t.app.test_client(); r=c.get('/model/resource-monitor'); print(r.status_code); print('资源监控' in r.get_data(as_text=True)); print('NVIDIA-A800-SXM4-80GB' in r.get_data(as_text=True)); print('lv-full' in r.get_data(as_text=True))"`
Expected:
```
200
True
True
True
```

- [ ] **Step 4: 浏览器人工验证**

Run: `python toolchain_demo.py`（另开终端），浏览器访问 `http://localhost:5004/model/resource-monitor`

验证清单:
- 左侧栏最末出现「管理」组，下有「资源监控」，当前项高亮
- 顶部工具栏：状态下拉 + 名称搜索框 + 刷新按钮；无「创建队列」按钮
- 表格 8 列齐全，列名与顺序正确
- 状态列圆点颜色：运行中=绿，已停止=橙，已关闭=灰
- 资源列显示 `已用/总量 单位` + 细进度条；GPU 列同行显示型号
- 进度条颜色随占用率变化（Demo 行 GPU 满载=红，train-pi05-main GPU 75%=黄，eval-sandbox GPU 0%=蓝绿，train-household-32 GPU 93%=橙）
- 8 列过宽时表格容器可横向滚动
- 点击筛选/搜索/刷新弹出 toast，无页面跳转

- [ ] **Step 5: Commit**

```bash
git add toolchain_demo.py
git commit -m "feat: add resource monitor page to model platform"
```

---

## Self-Review

**1. Spec coverage:**
- 导航「管理 > 资源监控」置于末尾 → Task 1 Step 2 ✅
- 只做队列列表, 无创建 / 无详情页 → Task 3（无创建按钮、无详情链接）✅
- 8 列表格字段 → Task 3 Step 1 表头 ✅
- 状态三值 + 彩色圆点 → Task 1 数据 + Task 2 `.res-dot` + Task 3 status_map ✅
- 资源列 `已用/总量` + 进度条, GPU 列型号 → Task 2 `res_bar()` ✅
- 进度条四档配色 → Task 2 `res_bar()` + `.rfill.lv-*` ✅
- 顶部状态筛选 / 名称搜索 / 刷新, toast 占位 → Task 3 filter-bar ✅
- 横向滚动 → Task 2 `.res-scroll` + Task 3 容器 ✅
- 样式对齐（白底 / 浅灰表头 / 细分割线 / 紧凑行高 / 低饱和状态 / 细进度条）→ 复用 `.ant-table` + Task 2 CSS ✅

**2. Placeholder scan:** 无 TBD / TODO / 模糊描述；所有 code step 含完整代码。✅

**3. Type consistency:** `res_bar(used, total, unit, model=None)` 签名在 Task 2 定义、Task 3 调用一致；`RESOURCE_QUEUES` 字段名（gpu/vcpu/disk/mem/ssd_flex/ssd_pl0 + used/total/unit/model）Task 1 定义、Task 3 引用一致；CSS 类名 `.res-cell/.rfill/.lv-*/.res-dot/.res-scroll` Task 2 定义、Task 3 使用一致。✅

无缺口。计划完整。
