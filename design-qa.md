# 后训练质检工作台 Design QA

- Visual targets: 用户提供的原质检片段编辑栏与后训练片段编辑栏截图
- Demo capture: `03-requirements/S027-后训练质检平台/后训练质检工作台-demo.png`
- Viewports: 1440 × 900、1366 × 768 CSS px
- State: 后训练质检工作台，选中按时间排序后的第 1 个片段

## 本轮核对

1. 右侧列表继续显示两位序号 `01、02、03`；当前片段编辑栏按同一排序显示 `片段 1、片段 2、片段 3`，不暴露内部稳定 ID。
2. 调整片段时间导致排序变化时，列表和编辑栏都基于最新排序重新计算序号；数据关联仍使用稳定 ID。
3. 审核错误原因改为原质检工作台样式的单选下拉，复用原页面 7 个选项，支持选择和清除。
4. 下拉向上展开，完整位于视口内，不改变编辑区高度；提交后控件禁用。
5. 原质检工作台、语义标注入口和后训练轨道、结论、提交规则保持可用。

## 验证

- `node --check static/annotation_workbench/post-training-quality.js`：通过
- `node tests/post_training_quality_rules.cjs`：通过
- `node tests/post_training_quality_browser.cjs`：1440 × 900 通过
- 1366 × 768 浏览器全流程：通过
- 浏览器控制台：无运行时错误

final result: passed
