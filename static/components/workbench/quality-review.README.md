# 质检流程片段编辑器

组件展示入口：`components/workbench/segmented-track.html` 的“片段编辑器”。

生产页面与展示区共用：
- `quality-review.js`：`createQualityReview({track, editor, list, actions, header, storageNamespace})`，拥有渲染、选项、导航、审核对照、接受和只读溢出逻辑。
- `quality-review.css`：编辑器及流程关联样式。
- `segmented-track.js/css`：基础 Web Components、主题与共享控件。

展示数据与装配在 `quality-review-preview.js`，不复制生产编辑器模板。五种模式分别为预训练质检、后训练质检、后训练质检审核、驳回处理、二次审核。预览使用独立的 component-preview 数据 ID，不覆盖业务草稿。

业务页 `pages/workbench/optimized.html` 直接加载本目录 JS/CSS。原页面目录的同名文件是兼容符号链接，不维护第二份实现。修改本目录组件后，两处同步变化。
