# 组件目录与使用规范

本文说明组件的文件组织、预览入口、接入接口和样式约定。路径均相对项目根目录。

## 目录

- [文件组织与维护约定](#文件组织与维护约定)
- [预览入口](#预览入口)
- [基础输入与表单](#基础输入与表单)
- [任务列表与表格配套](#任务列表与表格配套)
- [流程编辑器](#流程编辑器)
- [工作台与时间轴](#工作台与时间轴)

## 文件组织与维护约定

所有组件统一放在 `components/`，每个组件及其变体由一个独立文件夹管理。

```text
components/
├── _template/                 # 新组件模板
│   ├── component.html
│   └── component.css
└── <component-name>/          # 文件夹与文件使用小写 kebab-case
    ├── <component-name>.html  # 组件与变体预览
    ├── <component-name>.css   # 组件样式
    └── <component-name>.js    # 需要行为时提供
```

- **一个组件一个文件夹**：例如 `components/button/`。
- **变体与组件放在一起**：同一组件的尺寸、颜色、状态或样式变体，都写在该组件的 HTML 与 CSS 文件中，不单独拆分目录。
- **文件命名一致**：组件文件夹、HTML 和 CSS 文件均使用小写 kebab-case 命名。例如：
  - `components/icon-button/icon-button.html`
  - `components/icon-button/icon-button.css`
- **HTML 文件**：展示组件基础结构和全部可用变体。
- **CSS 文件**：只包含该组件所需的样式；使用组件名称作为 CSS 类前缀，避免与其他组件冲突。
- **底部操作区**：包含操作栏或底栏的组件，应采用纵向 Flex 布局；组件主体设置 `height: 100vh`，内容区使用 `flex: 1` 并允许滚动，底部操作区保持在页面最下方。无论内容条数多少，操作区都固定在组件底部；内容超出时仅内容区滚动，不挤压或覆盖操作区。
- **模板目录**：新增组件时，可复制 `components/_template/` 后重命名，并按组件需求填充内容。

## 预览入口

| 分类 | 入口 | 说明 |
| --- | --- | --- |
| 通用组件导航 | `components/common.html` | 设计规范总入口 |
| 按钮 | `components/button/button.html` | 基础按钮及流程操作变体 |
| 输入与表单 | `components/input/input.html` | 转入工作流的 `?view=forms` 视图 |
| 表格配套 | `components/table-controls/table-controls.html` | 页面分区、标题栏、筛选、Tab、表格与分页 |
| 任务列表组合 | `components/task-list-components-preview.html` | 任务列表组件组合预览 |
| 流程编辑器 | `components/process-editor/process-editor.html` | 流程编辑器与节点组件 |
| 工作台 | `components/workbench/` | 工作台组件定义与演示 |

通用组件导航中的「表格配套」统一预览筛选栏、Tab 切换和分页，入口为 `components/table-controls/table-controls.html`。原组件目录继续提供可复用的 CSS 和 JS。输入与表单的展示内容见下节。旧通用组件路由 `#task-filter-bar`、`#task-status-tabs`、`#pagination` 均跳转至 `#table-controls`。

## 基础输入与表单

### 输入框与搜索框

输入框统一放在 `components/input/`，预览页为 `input.html`。使用 `<form-input label="模型路径" value="Spirit-v1.6">`；`multiline` 属性切换多行输入，支持 `placeholder`、`name`、`disabled`、`readonly` 及 `.value`。输入时触发 `value-change`，携带 `detail.name` 与 `detail.value`。

搜索框与筛选框统一放在 `components/task-filter-bar/`，共同预览入口为 `task-filter-bar.html`。搜索框仍使用 `<search-input>`，资源为同目录下 `search-input.css`、`search-input.js`，保留 `search-change` 事件。

「输入与表单」入口复用工作流组件页的 `?view=forms` 视图，与「节点信息」使用同一份原子组件、间距规范及业务表单构建代码，并保留搜索框示例；不复制组件快照。

### 按钮与表单操作

所有新增按钮组件及其变体统一放在 `components/button/`，预览页为 `button.html`，样式和行为入口为 `button.css`、`button.js`。流程操作按钮作为其中一个变体，使用 `<process-actions>`，点击触发 `process-action` 事件，`detail.action` 分别为 `preview`、`functions`、`publish`、`history`。流程编辑器已引用该组件。

原子级组件包含「添加」「删除」的普通与禁用示例，复用 `text-button`：添加使用 `form-add-action`、`icon="plus"`；删除使用 `form-delete-action`、`icon="delete"`、`icon-only`，并提供明确的 `aria-label`。

节点配置的「添加处理人」：末条信息底部到按钮点击区域顶部为 `--node-space-add: 4px`；文字字号 12px、行高 12px、字重 400，点击区域高 28px，内部保留留白。间距不按加号或文字边缘测量。

删除按钮图标为 16px，点击区域为 24 × 24px；删除单行时与输入框居中对齐，删除整卡时放在卡片右侧居中。

### 表单反馈

表单提示支持警告（原有 `workflow-navigation-warning` 或 `form-feedback`）、信息（`form-feedback--info`）、成功（`form-feedback--success`）、错误（`form-feedback--error`）；后三种与 `form-feedback` 组合使用。统一字号 12px、行高 20px、内边距 4px 12px、圆角 6px。原子级组件展示全部四种语义颜色。

四种表单提示均带前置语义图标（警告三角、信息圆圈、成功勾、错误叉），尺寸 16px，与文字间距 8px，颜色继承提示文字；多行时与首行居中对齐。

## 任务列表与表格配套

### 表格尺寸规范与页面分区

对应预览：`components/table-controls/table-controls.html` 中的「表格尺寸规范与页面分区」。以下尺寸均为实际 **CSS px**；参考视口为 1440 × 900，示意图可等比例缩小，不能按截图像素替代规范数值。

页面从上到下依次为：页面标题栏 → Tab（可选）→ 筛选区域 → 统计区域（可选）→ 表格 → 分页。

| 区域 | 尺寸与留白 |
| --- | --- |
| 左侧导航 | 宽 230px，不计入内容区留白 |
| 内容区 | 上下 12px、左右 24px，由页面容器统一提供，内部组件不重复叠加 |
| 页面标题栏 | 默认高 54px；描述型标题随内容增高，副文本到下方字段间距 8px |
| Tab | 高 44px，按需展示 |
| 筛选区域 | 单行高 56px，可随换行增高 |
| 统计区域 | 图中示意高 64px，按需展示 |
| 表格 | 填充剩余高度，超出时在内部滚动；行高随内容撑开 |
| 单元格 | 上下内边距 12px、左右内边距 16px |
| 分页 | 高 40px，与表格共用外框，以分隔线区分 |

| 相邻区域 | 区域间距 |
| --- | --- |
| 标题 → Tab | 0px，组件自身保留内部边距 |
| Tab → 筛选 | 12px |
| 筛选 → 统计 | 12px |
| 统计 → 表格 | 12px |
| 表格 → 分页 | 0px |

可选区域隐藏后不保留占位，也不叠加间距：隐藏 Tab 时，标题直接接筛选，间距为 0px；隐藏统计时，筛选直接接表格，仅保留一次 12px。

表格承接页面剩余高度，表格主体内部滚动，分页留在底部。接入时复用表格配套组件，避免通过整页滚动或固定表格高度破坏上述分区。

### 页面标题栏

`task-page-header`：统一页面标题栏，使用 `title` 属性设置标题；`scene-filter` 按需展示标题旁的业务环节筛选（`scene` 设置选中值），`description` 按需展示副文本，`action` 按需展示右侧操作按钮。不传对应属性时不展示且不占位，各项可独立组合。筛选触发 `scene-change`，操作按钮触发 `header-action`。表格配套页中的「筛选、副文本与操作」为统一完整示例。

`task-page-header` 支持 `back`、`back-label` 和 `header-back` 事件；`status` / `status-tone="running|paused"` 在右侧展示共享状态标签（引用 task-data-table.css）。返回箭头沿用文字主色、加粗线条，与标题间隔 8px。预览页包含返回标题与状态示例。

### 筛选、Tab 与分页

- `task-status-tabs`：任务池/待办项切换，触发 `tab-change` 事件。
- `task-filter-bar`：ID、序列号、操作人筛选，触发 `filter-change`、`filter-open`、`filter-refresh` 事件。
- `task-data-table`：任务表格与分页，触发 `row-action`、`page-change` 事件；使用 `rows` 属性控制演示行数。

双层 Tab 使用 `<task-status-tabs variant="layered" active="todo" sub-active="review">`：上层待办项/任务池沿用 `tab-change`，下层驳回待处理/修正待审核触发 `sub-tab-change`，携带 `value` 和 `parentValue`。两层均支持方向键、Home 和 End 切换。

分页组件位于 `components/pagination/`，预览入口为 `pagination.html`，并已加入通用组件导航。使用 `<list-pagination total="1050" page="1" page-size="10"></list-pagination>`，引入同目录 CSS 和 JS。监听 `page-change`，事件 `detail` 包含 `page` 和 `pageSize`，由页面负责加载对应数据。空列表与单页列表仍显示分页，下一页自动禁用。

### 表格布局与事件

`task-data-table` 用 `variant` 选择数据类型，独立的 `layout` 属性标识布局，后续布局继续在此组件扩展：

- 变体一「经典布局」：`variant="task-management" layout="classic"`。
- 变体二「左右统计布局」：`variant="data-management" layout="split-stats"`，包含左右两组统计、勾选计数与批量操作。

统计数值为演示数据。勾选触发 `selection-change`，批量按钮触发 `batch-action`（`action`、`rows`），由接入页面处理业务动作。

表格预览排序约定：**「通用表格 · 多内容固定列」始终放在最上面**，所有布局变体及后续新增布局均放在其下方。

### 接入示例

任务数据页 `pages/task-processing/data.html` 复用 `task-data-table variant="task-records"`、`task-page-header`、`search-input`、`text-button`、`list-pagination` 及现有结果/状态标签。任务名称和操作列“数据”链接进入同一页面；视频区域支持真实图片、加载中和上传失败状态。该页面同时作为「表格示例」中的「媒体列表」展示。

## 流程编辑器

### 组成与接入

完整页面使用 `<process-editor-page>` 组合入口，内部引用顶部信息栏、节点栏、画布、属性面板及平台侧栏；按钮、搜索、输入和 Tab 继续复用公共组件。预览专用外框不进入页面组件。

统一放在 `components/process-editor/`，预览入口为 `process-editor.html`，模板为 `process-editor.js`，样式为 `process-editor.css`，交互为 `controller.js`。

- `process-editor-header`：顶部信息栏，复用 button 中的流程按钮。
- `process-node-library`：左侧流程与节点栏，复用 search-input。
- `process-flow-canvas`：可拖拽流程画布，默认包含操作栏与缩放控件；`external-controls` 可使用外置控件。
- `process-node-properties`：右侧属性面板，复用 input 与 task-status-tabs。
- `process-canvas-tools`：选择、平移、撤销、重做。
- `process-canvas-zoom`：缩放比例与加减按钮。

将组合包裹在 `.process-editor-components` 容器中，加载模板和控制器即可初始化交互；样式限定在该容器内。原流程编辑器页面使用相同组件，保留节点拖拽、循环框自适应及键盘撤销。

### 节点表单间距

以下对应组件页「节点信息 · 间距规范」的八项规则，单位均为 CSS px。按内容层级区分间距，不将所有空隙设为同一数值。

| 编号 | 场景 | 变量 | 尺寸 |
| --- | --- | --- | --- |
| 01 | 小标题 → 信息 | `--node-space-label` | 8px |
| 02 | 信息组 → 信息组 | `--node-space-field` | 12px |
| 03 | 组合组 → 组合组 | `--node-space-section` | 18px |
| 04 | 信息 → 添加按钮 | `--node-space-add` | 4px |
| 05 | 模块标题 → 信息 | `--node-space-title` | 8px |
| 06 | 灰底参数卡片内边距 | `--node-card-padding` | 8px |
| 07 | 内容 → 校验提示 | `--node-space-feedback` | 8px |
| 08 | 副文本 → 信息 | `--node-space-description` | 8px |

#### 测量口径与适用范围

1. **小标题 → 信息**：从字段标签底部量到输入框、下拉框或信息内容顶部。标签和内容一起构成一个信息组。
2. **信息组 → 信息组**：从上一组内容底部量到下一组标签顶部，例如「节点名称」与「下游节点」；不是两组标签之间的距离。
3. **组合组 → 组合组**：从上一模块整体底部量到下一模块标题顶部，例如「输入配置」与「后续节点」。标题、说明及内部信息组属于同一组合组。
4. **信息 → 添加按钮**：从最后一条信息或条件卡片底部量到添加按钮点击区域顶部。按钮内部保留点击留白，不按加号图形边缘测量。
5. **模块标题 → 信息**：从带色条的模块标题底部量到第一条信息顶部。有字段标签时量到标签，无标签时量到输入框或信息行，例如「请求 → 请求方法」与「请求头 → Accept」。与字段小标题到控件的间距独立管理。
6. **灰底参数卡片内边距**：从灰底边框内侧量到内容，上、下、左、右均为 8px。适用于人工、位姿、循环及超时重试参数卡片。公用外框、卡片之间及字段之间的间距保持各自规范，不叠加到卡片内边距。
7. **内容 → 校验提示**：从内容或参数卡片底部量到校验提示顶部，两者属于同一组合组。提示到下一个独立模块保持 18px；不改变提示框自身内边距。
8. **副文本 → 信息**：从副文本最后一行的行盒底部量到下一块信息的外边界顶部。适用于后续节点卡片、无出口空状态、自定义输入及参数配置。下方带字段标签时量到标签顶部，不是输入框顶部；多行副文本不增加额外间距。

#### 实现规则

- 间距由共同父容器的 `gap` 控制，同一间隙不叠加子元素的 `margin`、额外 `padding` 或空占位容器。
- 隐藏、空内容不保留额外间隔；实际面板与组件示例遵循同一规则。
- 标题到副文本为 8px；没有副文本时沿用标题到信息的 8px 规范。
- 信息组之间为 12px，独立模块之间为 18px，不能混用。
- 卡片内边距、同行列距、说明文字及添加按钮间距独立管理，不并入字段、信息组或模块间距。

## 工作台与时间轴

### 工作台组件

工作台组件的定义与演示均收纳在 `components/workbench/` 中。

| 组件 | 内容与变体 |
| --- | --- |
| `workbench-task-header` | 任务信息头 |
| `workbench-instruction` | 指令栏 |
| `workbench-media-viewer` | `three-panel` 为左侧两块、右侧一块的三画面布局；所有画面保持 `3:2` |
| `workbench-segment-editor` | 默认、`variant-2`、`variant-3` 三个变体 |
| `workbench-segment-list-panel` | `segments`（默认）、`log`、`info` 三种内容变体 |
| `workbench-annotation-list`、`workbench-quality-list` | 无树结构的并列片段列表骨架 |
| `workbench-segment-tabs` | 独立右侧 Tab |
| `workbench-segment-list` | 列表与 Tab 保持联动的兼容组合壳 |
| `workbench-footer-actions` | 底部操作栏 |

实际工作台 `pages/workbench/optimized.html` 通过上述工作台自定义元素承载原页面结构；生产页面继续使用 `optimized.css` 与 `optimized.js`，保证组件宿主不改变原样式和既有联动。

### 时间轴与标注轨道

动作标注时间轴由 `segmented-track` 与以下子组件及兼容组合壳组成：

- `timeline-time-scale`：独立时间刻度。
- `timeline-range-selector`：独立范围选择、拖动与吸附；`variant="marked"` 增加选取高亮与定位标记。
- `timeline-range-ruler`：兼容旧引用的时间刻度与范围选择组合壳。
- `annotation-segment-row`：彩色分段轨道与告警标记。
- `annotation-base-row`：动作标注的连续绿色基础轨道。
- `timeline-controls`：播放时间、编辑工具与标注标准入口。

`semantic-annotation-track` 是三轨语义标注组件；`action-annotation-track` 是独立的两轨动作标注组件，不包含连续绿色基础轨道。

## 数据集页面

页面入口：`pages/model-platform/index.html#model-datasets`，在现有模型平台导航与页面容器内组合 `<dataset-browser>`。上下 12px、左右 24px 留白由平台容器统一提供，数据集组件位于 `components/dataset/`，复用 `task-page-header`、`task-status-tabs`、`form-select`、`search-input`、`text-button`。

| 组件 | 职责 |
| --- | --- |
| `dataset-browser` | 页面布局、数据集与版本切换、演示导出 |
| `dataset-catalog` | 目录、搜索、范围和标签筛选；触发 `dataset-select`、`directory-create`、`dataset-create` |
| `dataset-episodes` | Episode 列表；触发 `episode-select` |
| `dataset-trajectory` | 引用 `workbench-media-viewer variant="dataset"`，组合部位曲线与播放进度 |

公共 Tab 新增 `variant="dataset"` 与 `variant="episode"`，沿用 `tab-change` 和键盘操作。当前页面使用本地演示数据，曲线不代表真实采集结果；视频、新建与分析等待数据服务接入，导出仅包含示例元数据。

数据集目录与分配管理资源列表共同引用 `resource-list`。通过 `.items` 传入 `{id, label, meta}`，分组使用 `{label, children}`；`.selected` 指定当前项，`resource-select` 事件的 `detail.value` 返回选中 ID。目录标题引用标准 `task-page-header`，范围筛选引用 `task-status-tabs variant="dataset-scope"`，标签与搜索引用 `form-select`、`search-input`；“＋目录”和“＋数据集”引用 `text-button.form-add-action`。

数据集与 Episode 的 Tab 示例同步展示在「表格配套 → Tab 切换」。页面和示例均引用 `task-status-tabs` 同一实现，使用 `surface="transparent"` 继承页面背景；标准字号 14px、行高 20px、项间距 24px，容器总高 44px。

### 表格详情入口颜色

可点击进入详情的名称默认使用深蓝色 `var(--color-detail-link, #174A78)`；操作列的“详情”、数据链接等操作保持主色 `var(--color-brand)`。普通不可点击文本保持正文色，禁用入口保持禁用色。
