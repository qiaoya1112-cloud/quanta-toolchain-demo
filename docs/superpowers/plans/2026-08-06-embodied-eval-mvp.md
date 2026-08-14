# 具身评测模块 MVP 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为模型平台新增"具身评测"独立模块，支持提示词库、Metric模板、评测集、评测任务的配置管理，以及Segment评测记录的查看和导出，形成完整的评测配置→执行→结果闭环。

**Architecture:** 
- 基于现有 toolchain_demo.py Flask 应用扩展
- 使用内联 HTML/CSS 模板，沿用 Quanta teal (#149DAA) 主题色
- 前端使用 vanilla JavaScript 实现可交互原型（行内编辑、动态表单、树形结构）
- 后端使用 Python 全局变量 Mock 数据存储（刷新后数据丢失，符合原型定位）

**Tech Stack:** 
- Python 3 + Flask
- HTML5 + inline CSS + vanilla JavaScript
- Ant Design v4 风格（已有样式复用）

## Global Constraints

- 主题色: Quanta teal #149DAA
- 所有路由前缀: `/model/embodied-eval/*`
- 导航分组名: "具身评测"
- 样式: 复用现有 toolchain_demo.py 的 CSS classes（.q-sider, .q-main, .card, .table 等）
- Mock 数据: 使用 Python 全局变量存储，格式参照设计文档 Mock 数据结构
- 数据持久化: 不做（原型特性）
- 提示词库布局: 参照用户提供截图的表格合并单元格风格

---

## 文件结构

### 修改文件
- `toolchain_demo.py` - 主应用文件，新增路由、Mock数据、页面渲染函数

### 不新增独立文件
本次实现全部在 toolchain_demo.py 中完成，保持与现有架构一致。

---

## Task 1: 基础架构 - 导航配置与Mock数据结构

**Files:**
- Modify: `toolchain_demo.py` (在 PLATFORM_CONFIG["model"]["nav"] 区域，约618-652行)
- Modify: `toolchain_demo.py` (在全局Mock数据区域，约100-400行之间插入)

**Interfaces:**
- Produces: 
  - `PROMPTS: List[Dict]` - 提示词库数据
  - `METRIC_TEMPLATES: List[Dict]` - Metric模板数据
  - `EVAL_SETS: List[Dict]` - 评测集数据
  - `EVAL_TASKS: List[Dict]` - 评测任务数据
  - `SEGMENTS: List[Dict]` - Segment记录数据

- [ ] **Step 1: 添加导航配置**

在 `PLATFORM_CONFIG["model"]["nav"]` 中添加"具身评测"分组：

```python
# 在 line 640 附近（"评测"分组后）插入
("具身评测", [
    ("/model/embodied-eval/prompts",     "提示词库",      "&#128221;", "新增"),
    ("/model/embodied-eval/metrics",     "Metric 模板",   "&#128202;", "新增"),
    ("/model/embodied-eval/sets",        "评测集",        "&#128203;", "新增"),
    ("/model/embodied-eval/tasks",       "评测任务",      "&#9881;",  "新增"),
    ("/model/embodied-eval/segments",    "评测记录",      "&#128196;", "新增"),
]),
```

- [ ] **Step 2: 定义Mock数据结构**

在 toolchain_demo.py 顶部全局变量区域（约100行后）添加：

```python
# ━━━ 具身评测模块 Mock 数据 ━━━

# 提示词库
EMBODIED_PROMPTS = [
    {"id": "ep001", "scene": "冰箱", "task": "冰柜任务", "prompt": "打开冰柜门", 
     "tags": ["开门动作"], "creator": "Lance Li", "created_at": "2026-06-10"},
    {"id": "ep002", "scene": "冰箱", "task": "冰柜任务", "prompt": "放置可乐到第二层", 
     "tags": ["放置"], "creator": "Lance Li", "created_at": "2026-06-10"},
    {"id": "ep003", "scene": "冰箱", "task": "冰柜任务", "prompt": "关闭冰柜门", 
     "tags": ["开门动作"], "creator": "Lance Li", "created_at": "2026-06-10"},
    {"id": "ep004", "scene": "洗碗机", "task": "洗碗任务", "prompt": "拉开洗碗机门", 
     "tags": ["开门动作"], "creator": "Rick Guo", "created_at": "2026-06-12"},
    {"id": "ep005", "scene": "洗碗机", "task": "洗碗任务", "prompt": "放置碗碟", 
     "tags": ["放置"], "creator": "Rick Guo", "created_at": "2026-06-12"},
    {"id": "ep006", "scene": "桌面", "task": "整理任务", "prompt": "整齐摆放书籍", 
     "tags": ["整理"], "creator": "Lance Li", "created_at": "2026-06-15"},
]

# Metric 模板
EMBODIED_METRIC_TEMPLATES = [
    {
        "id": "emt001",
        "name": "基础能力评测 5 项",
        "fields": [
            {"name": "碰撞次数", "type": "integer"},
            {"name": "执行状态", "type": "enum", "options": ["success", "timeout", "error"]},
            {"name": "耗时", "type": "float"},
            {"name": "成功率", "type": "percentage"},
            {"name": "是否重试", "type": "boolean"}
        ],
        "created_at": "2026-06-01"
    },
    {
        "id": "emt002",
        "name": "稳定性测试 3 项",
        "fields": [
            {"name": "执行次数", "type": "integer"},
            {"name": "方差", "type": "float"},
            {"name": "稳定性等级", "type": "enum", "options": ["高", "中", "低"]}
        ],
        "created_at": "2026-06-05"
    },
]

# 评测集
EMBODIED_EVAL_SETS = [
    {
        "id": "ees001",
        "name": "厨房基础能力 v1.0",
        "version": "v1.0",
        "is_benchmark": True,
        "scene_tags": ["冰箱", "洗碗机"],
        "description": "厨房场景基础动作能力评测",
        "metric_template_id": "emt001",
        "custom_metrics": [],
        "prompts": [
            {
                "scene": "冰箱",
                "task": "冰柜任务",
                "items": [
                    {"prompt_id": "ep001", "text": "打开冰柜门", "edited": False},
                    {"prompt_id": "ep002", "text": "放置可乐到第二层（已编辑版本）", "edited": True},
                    {"prompt_id": None, "text": "关闭冰柜门", "edited": False}
                ]
            },
            {
                "scene": "洗碗机",
                "task": "洗碗任务",
                "items": [
                    {"prompt_id": "ep004", "text": "拉开洗碗机门", "edited": False},
                    {"prompt_id": "ep005", "text": "放置碗碟", "edited": False}
                ]
            }
        ],
        "created_at": "2026-06-10"
    },
]

# 评测任务
EMBODIED_EVAL_TASKS = [
    {
        "id": "eet001",
        "name": "Spirit v1.6 基础能力测试",
        "eval_set_id": "ees001",
        "models": [
            {"name": "Spirit_v1.6", "version": "ckpt_40k", "ckpt_path": "/models/spirit/ckpt40k", "code_branch": "release/1.0"},
            {"name": "Spirit_v1.6_ctrl", "version": "ckpt_45k", "ckpt_path": "/models/spirit/ckpt45k", "code_branch": "feature/control"}
        ],
        "exec_params": {"repeat_count": 3, "timeout": 300},
        "status": "completed",
        "created_at": "2026-06-12",
        "started_at": "2026-06-12 10:00",
        "ended_at": "2026-06-12 15:30"
    },
]

# Segment 记录
EMBODIED_SEGMENTS = [
    {
        "segment_id": "eseg001",
        "task_id": "eet001",
        "task_name": "Spirit v1.6 基础能力测试",
        "eval_set_id": "ees001",
        "prompt_id": "ep001",
        "prompt_text": "打开冰柜门",
        "scene": "冰箱",
        "task_group": "冰柜任务",
        "policy_name": "Spirit_v1.6",
        "policy_version": "ckpt_40k",
        "repeat_index": 1,
        "repeat_total": 3,
        "metrics": {"碰撞次数": 0, "执行状态": "success", "耗时": 12.5, "成功率": 100.0, "是否重试": False},
        "status": "completed",
        "is_badcase": False,
        "video_url": "/mock/video_eseg001.mp4",
        "robot_state_file": "/mock/robot_eseg001.parquet",
        "moz_trace_file": "/mock/moztrace_eseg001.json",
        "created_at": "2026-06-12 10:15:23"
    },
    {
        "segment_id": "eseg002",
        "task_id": "eet001",
        "task_name": "Spirit v1.6 基础能力测试",
        "eval_set_id": "ees001",
        "prompt_id": "ep001",
        "prompt_text": "打开冰柜门",
        "scene": "冰箱",
        "task_group": "冰柜任务",
        "policy_name": "Spirit_v1.6",
        "policy_version": "ckpt_40k",
        "repeat_index": 2,
        "repeat_total": 3,
        "metrics": {"碰撞次数": 1, "执行状态": "timeout", "耗时": 300.0, "成功率": 0.0, "是否重试": True},
        "status": "timeout",
        "is_badcase": True,
        "video_url": "/mock/video_eseg002.mp4",
        "robot_state_file": "/mock/robot_eseg002.parquet",
        "moz_trace_file": "/mock/moztrace_eseg002.json",
        "created_at": "2026-06-12 10:20:45"
    },
]
```

- [ ] **Step 3: 验证导航显示**

启动应用并访问 `http://localhost:5004/model`，检查左侧栏是否出现"具身评测"分组及5个子菜单项。

Run: `python toolchain_demo.py`
Expected: 左侧栏显示"具身评测"分组，包含5个菜单项

- [ ] **Step 4: Commit基础架构**

```bash
git add toolchain_demo.py
git commit -m "feat(embodied-eval): add navigation and mock data structure"
```

---

## Task 2: 提示词库页面 - 列表展示与筛选

**Files:**
- Modify: `toolchain_demo.py` (新增路由函数，约4500行后插入)

**Interfaces:**
- Consumes: `EMBODIED_PROMPTS: List[Dict]`
- Produces: `/model/embodied-eval/prompts` 页面路由

- [ ] **Step 1: 创建提示词库列表页面路由**

在 toolchain_demo.py 约4500行（模型平台路由区域末尾）插入：

```python
# ━━━ 具身评测模块路由 ━━━

@app.route("/model/embodied-eval/prompts")
def embodied_eval_prompts():
    """提示词库列表页面"""
    # 获取筛选参数
    scene_filter = request.args.get("scene", "")
    task_filter = request.args.get("task", "")
    search_query = request.args.get("q", "")
    
    # 筛选数据
    filtered = EMBODIED_PROMPTS
    if scene_filter:
        filtered = [p for p in filtered if p["scene"] == scene_filter]
    if task_filter:
        filtered = [p for p in filtered if p["task"] == task_filter]
    if search_query:
        filtered = [p for p in filtered if search_query.lower() in p["prompt"].lower()]
    
    # 按场景分组（用于合并单元格显示）
    grouped = {}
    for p in filtered:
        scene_key = p["scene"]
        if scene_key not in grouped:
            grouped[scene_key] = []
        grouped[scene_key].append(p)
    
    # 获取所有唯一的场景和任务（用于筛选下拉）
    all_scenes = sorted(list(set(p["scene"] for p in EMBODIED_PROMPTS)))
    all_tasks = sorted(list(set(p["task"] for p in EMBODIED_PROMPTS)))
    
    content = f"""
    <div class="page-header">
      <h2>提示词库</h2>
      <div class="actions">
        <button class="btn-secondary" onclick="showImportDialog()">导入 JSON</button>
        <button class="btn-primary" onclick="addPromptRow()">+ 新增提示词</button>
      </div>
    </div>
    
    <div class="filter-bar">
      <select id="scene-filter" onchange="applyFilter()">
        <option value="">全部场景</option>
        {''.join(f'<option value="{s}" {"selected" if s == scene_filter else ""}>{s}</option>' for s in all_scenes)}
      </select>
      <select id="task-filter" onchange="applyFilter()">
        <option value="">全部任务</option>
        {''.join(f'<option value="{t}" {"selected" if t == task_filter else ""}>{t}</option>' for t in all_tasks)}
      </select>
      <input type="text" id="search-input" placeholder="搜索 Prompt 文本" value="{html.escape(search_query)}" onkeyup="onSearchKeyup(event)">
      <button class="btn-icon" onclick="applyFilter()">🔍</button>
      <button class="btn-icon" onclick="window.location.reload()">🔄</button>
    </div>
    
    <table class="data-table">
      <thead>
        <tr>
          <th width="12%">Labels</th>
          <th width="15%">任务名称</th>
          <th width="35%">Prompt 文本</th>
          <th width="15%">标签</th>
          <th width="10%">创建人</th>
          <th width="13%">操作</th>
        </tr>
      </thead>
      <tbody id="prompt-table-body">
    """
    
    # 渲染分组数据
    for scene, prompts in grouped.items():
        scene_rowspan = len(prompts)
        for idx, p in enumerate(prompts):
            content += f"""
        <tr data-id="{p['id']}">
          {'<td rowspan="' + str(scene_rowspan) + '">' + html.escape(scene) + '</td>' if idx == 0 else ''}
          <td>{html.escape(p['task'])}</td>
          <td class="prompt-text">{html.escape(p['prompt'])}</td>
          <td>{', '.join(p['tags'])}</td>
          <td>{html.escape(p['creator'])}</td>
          <td>
            <button class="btn-icon" onclick="copyPrompt('{p['id']}')" title="复制">📋</button>
            <button class="btn-icon" onclick="deletePrompt('{p['id']}')" title="删除">🗑</button>
          </td>
        </tr>
            """
    
    content += """
      </tbody>
    </table>
    
    <div class="pagination">
      <span>共 {total} 条</span>
    </div>
    
    <style>
    .page-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
    .page-header h2 {{ margin: 0; color: #262626; font-size: 20px; font-weight: 600; }}
    .page-header .actions {{ display: flex; gap: 10px; }}
    .filter-bar {{ display: flex; gap: 10px; margin-bottom: 16px; padding: 16px; background: #fafafa; border-radius: 4px; }}
    .filter-bar select, .filter-bar input {{ padding: 6px 12px; border: 1px solid #d9d9d9; border-radius: 4px; }}
    .filter-bar input {{ flex: 1; }}
    .btn-primary {{ padding: 6px 16px; background: #149DAA; color: white; border: none; border-radius: 4px; cursor: pointer; }}
    .btn-primary:hover {{ background: #117A85; }}
    .btn-secondary {{ padding: 6px 16px; background: white; color: #262626; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer; }}
    .btn-secondary:hover {{ border-color: #149DAA; color: #149DAA; }}
    .btn-icon {{ background: none; border: none; cursor: pointer; font-size: 16px; padding: 4px 8px; }}
    .btn-icon:hover {{ opacity: 0.7; }}
    .data-table {{ width: 100%; border-collapse: collapse; background: white; }}
    .data-table th {{ background: #fafafa; padding: 12px; text-align: left; font-weight: 600; border-bottom: 1px solid #f0f0f0; }}
    .data-table td {{ padding: 12px; border-bottom: 1px solid #f0f0f0; }}
    .data-table tbody tr:hover {{ background: #f5f5f5; }}
    .prompt-text {{ color: #595959; }}
    .pagination {{ margin-top: 16px; text-align: right; color: #8c8c8c; }}
    </style>
    
    <script>
    function applyFilter() {{
      const scene = document.getElementById('scene-filter').value;
      const task = document.getElementById('task-filter').value;
      const q = document.getElementById('search-input').value;
      const params = new URLSearchParams();
      if (scene) params.set('scene', scene);
      if (task) params.set('task', task);
      if (q) params.set('q', q);
      window.location.href = '/model/embodied-eval/prompts?' + params.toString();
    }}
    
    function onSearchKeyup(event) {{
      if (event.key === 'Enter') applyFilter();
    }}
    
    function copyPrompt(id) {{
      alert('复制功能：将复制 Prompt ID ' + id + ' 的数据（待实现）');
    }}
    
    function deletePrompt(id) {{
      if (confirm('确定删除该 Prompt？')) {{
        fetch('/api/embodied-eval/prompts/' + id, {{ method: 'DELETE' }})
          .then(() => window.location.reload());
      }}
    }}
    
    function addPromptRow() {{
      alert('新增功能：在表格底部展开编辑行（下个 Task 实现）');
    }}
    
    function showImportDialog() {{
      alert('导入功能：弹窗上传 JSON 文件（下个 Task 实现）');
    }}
    </script>
    """.format(total=len(filtered))
    
    return render_page(
        "提示词库 - 具身评测",
        content,
        active="/model/embodied-eval/prompts",
        module="model"
    )
```

- [ ] **Step 2: 测试页面渲染**

Run: `python toolchain_demo.py`  
访问: `http://localhost:5004/model/embodied-eval/prompts`  
Expected: 显示提示词列表，场景列使用rowspan合并单元格，筛选和搜索按钮可点击

- [ ] **Step 3: 测试筛选功能**

操作: 选择场景"冰箱"，点击搜索图标  
Expected: 页面刷新，只显示场景为"冰箱"的Prompt

- [ ] **Step 4: Commit提示词库列表页**

```bash
git add toolchain_demo.py
git commit -m "feat(embodied-eval): add prompts list page with filters"
```

---

## Task 3: 提示词库 - 行内新增与API

**Files:**
- Modify: `toolchain_demo.py` (新增API路由和行内编辑JS)

**Interfaces:**
- Consumes: `EMBODIED_PROMPTS: List[Dict]`
- Produces: 
  - `POST /api/embodied-eval/prompts` - 创建Prompt
  - `DELETE /api/embodied-eval/prompts/<id>` - 删除Prompt

- [ ] **Step 1: 添加Prompt API路由**

在提示词库页面路由后插入：

```python
@app.route("/api/embodied-eval/prompts", methods=["POST"])
def api_embodied_prompts_create():
    """创建新Prompt"""
    data = request.json
    new_id = f"ep{len(EMBODIED_PROMPTS) + 1:03d}"
    new_prompt = {
        "id": new_id,
        "scene": data.get("scene", ""),
        "task": data.get("task", ""),
        "prompt": data.get("prompt", ""),
        "tags": data.get("tags", []),
        "creator": "Current User",
        "created_at": "2026-08-06"
    }
    EMBODIED_PROMPTS.append(new_prompt)
    return jsonify({"ok": True, "id": new_id})

@app.route("/api/embodied-eval/prompts/<prompt_id>", methods=["DELETE"])
def api_embodied_prompts_delete(prompt_id):
    """删除Prompt"""
    global EMBODIED_PROMPTS
    EMBODIED_PROMPTS = [p for p in EMBODIED_PROMPTS if p["id"] != prompt_id]
    return jsonify({"ok": True})
```

- [ ] **Step 2: 更新行内新增功能**

修改提示词库页面中的 `addPromptRow()` 函数：

```javascript
function addPromptRow() {
  const tbody = document.getElementById('prompt-table-body');
  const newRow = document.createElement('tr');
  newRow.className = 'edit-row';
  newRow.innerHTML = `
    <td><input type="text" id="new-scene" placeholder="场景" style="width:100%"></td>
    <td><input type="text" id="new-task" placeholder="任务" style="width:100%"></td>
    <td><input type="text" id="new-prompt" placeholder="Prompt文本" style="width:100%"></td>
    <td><input type="text" id="new-tags" placeholder="标签(逗号分隔)" style="width:100%"></td>
    <td>-</td>
    <td>
      <button class="btn-icon" onclick="saveNewPrompt()" title="保存">✓</button>
      <button class="btn-icon" onclick="cancelNewPrompt()" title="取消">✕</button>
    </td>
  `;
  tbody.appendChild(newRow);
}

function saveNewPrompt() {
  const scene = document.getElementById('new-scene').value;
  const task = document.getElementById('new-task').value;
  const prompt = document.getElementById('new-prompt').value;
  const tagsStr = document.getElementById('new-tags').value;
  
  if (!scene || !task || !prompt) {
    alert('场景、任务、Prompt 为必填项');
    return;
  }
  
  const tags = tagsStr.split(',').map(t => t.trim()).filter(t => t);
  
  fetch('/api/embodied-eval/prompts', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({scene, task, prompt, tags})
  }).then(res => res.json())
    .then(() => window.location.reload());
}

function cancelNewPrompt() {
  const editRow = document.querySelector('.edit-row');
  if (editRow) editRow.remove();
}
```

- [ ] **Step 3: 测试行内新增**

Run: 启动应用  
操作: 点击"+ 新增提示词"，填写表单，点击✓保存  
Expected: 页面刷新，新Prompt出现在列表中

- [ ] **Step 4: 测试删除功能**

操作: 点击某个Prompt的🗑按钮，确认删除  
Expected: 该Prompt从列表中消失

- [ ] **Step 5: Commit行内编辑功能**

```bash
git add toolchain_demo.py
git commit -m "feat(embodied-eval): add inline create and delete for prompts"
```

---

## Task 4: Metric 模板页面

**Files:**
- Modify: `toolchain_demo.py`

**Interfaces:**
- Consumes: `EMBODIED_METRIC_TEMPLATES: List[Dict]`
- Produces: `/model/embodied-eval/metrics` 路由、Metric 模板 CRUD API

由于篇幅限制，Task 4-9 的详细步骤与 Task 1-3 类似，包括：
- Task 4: Metric 模板列表、创建/编辑页面、枚举行内展开
- Task 5: 评测集列表、创建页面（单页长表单、固定三层 Prompt 树）
- Task 6: 评测集 - Metric 配置与 Prompt 选择弹窗
- Task 7: 评测任务列表、创建页面
- Task 8: Segment 列表、筛选、导出 CSV
- Task 9: Segment 详情页（Tab 分栏）

每个 Task 遵循相同模式：
1. 创建页面路由和 HTML 模板
2. 添加相应的 API 端点（CRUD）
3. 实现前端交互（JS）
4. 测试功能
5. Commit

---

## 简化实施路径

考虑到这是一个大型功能（7个页面），建议分阶段实施：

### Phase 1: 配置管理核心（2周）
- ✅ Task 1-3: 提示词库（已详细规划）
- Task 4: Metric 模板
- Task 5-6: 评测集管理

### Phase 2: 任务与结果（1周）
- Task 7: 评测任务
- Task 8-9: Segment 展示

### 每个 Task 的通用模式

1. **创建路由**: 在 toolchain_demo.py 添加 `@app.route` 函数
2. **构建 HTML**: 使用内联模板，复用现有 CSS classes
3. **添加 JS 交互**: 在 `<script>` 标签中实现
4. **创建 API**: 添加 `/api/embodied-eval/*` 端点操作 Mock 数据
5. **测试**: 手动验证功能
6. **Commit**: `git commit -m "feat(embodied-eval): ..."`

---

## 完整功能清单（验收标准）

### 提示词库
- [x] 列表展示（场景合并单元格）
- [x] 筛选（场景/任务/搜索）
- [x] 行内新增
- [x] 删除
- [ ] 批量导入 JSON
- [ ] 复制

### Metric 模板
- [ ] 卡片式列表
- [ ] 创建/编辑页面
- [ ] 枚举类型行内展开
- [ ] 删除

### 评测集
- [ ] 列表（含 Benchmark 标记）
- [ ] 创建页面（单页长表单）
- [ ] 基本信息配置
- [ ] Metric 字段配置（从模板选择 or 自定义）
- [ ] 固定三层 Prompt 树
- [ ] Prompt 选择弹窗（从库选择 / 手动输入）
- [ ] Benchmark 标记

### 评测任务
- [ ] 列表（状态筛选）
- [ ] 创建页面
- [ ] 选择评测集
- [ ] 配置被测模型
- [ ] 设置执行参数

### Segment
- [ ] 列表（多维筛选）
- [ ] 导出 CSV
- [ ] 详情页（4个Tab）
- [ ] BadCase 标记

---

## 后续步骤

**选择执行方式：**

1. **Subagent-Driven (推荐)** - 我为每个 Task 派发独立 subagent，任务间 review
2. **Inline Execution** - 在当前会话按 Task 顺序执行

请选择执行方式，或者让我继续详细展开 Task 4-9 的完整步骤。

