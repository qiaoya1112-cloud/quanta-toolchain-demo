# 采集任务日志替代配置版本 Design QA（最新，2026-10-25）

- 用户决定一期不做任务配置V1/V2；列表、任务配置、录制详情、任务卡已移除相关展示和版本门禁。Prompt资源自身版本保留。
- 操作日志显示修改人、完整时间及改动字段，默认摘要，展开查看修改前后。旧日志保留，飞书正文不补造平台更新记录。
- 1440/1366桌面及390/320手机目检，日志长文本与链接正常换行，展开内容内部滚动；没有新增备注横幅。
- 26项Python、28项日志、82项视频详情、68项布局、42项任务卡、50项轨迹通过；语法/diff检查通过。
- 证据：../../02-evidence/2026-10-25/collection-logs-only/。新版验证端口5046；旧5041进程停止重启被审批策略拒绝，保持原样。

final result: passed（本地 Demo）

---

# 位置泛化统计弹窗 Design QA（历史，2026-10-24）

### 后续同行展示修正

- 目标区域摘要改为单行紧凑格式（如 `XYZ · X -40~40 · Y -40~40 · Z 0~100 cm`），完整范围放在 `title`。
- 六列保持一行，数据行垂直居中；390/320px窄屏才允许区域文字自然换行。
- 更新证据：`../../02-evidence/2026-10-24/collection-generalization-single-line/02-editable-table.png`；33项专项仍通过。

- Source visual truth: `C:/Users/tinab/AppData/Local/Temp/codex-clipboard-a49901d8-d459-43ee-a3a3-d4c6fa175b3c.png`，1502×1062px。
- Implementation: `../../02-evidence/2026-10-24/collection-generalization-modal/final/02a-config-dialog.png`，1440×1000 CSS px，deviceScaleFactor=1。
- Focused dialog: 同目录`02a-dialog-crop.png`，762×748px（含边框）；内容宽760 CSS px。
- Full/region comparison: 同目录`reference-comparison.png`；参考等比归一到760×537px，与最终弹窗并排。参考截图没有可验证DPR，不声称绝对物理尺寸一致。
- State: NORMAL新增统计，已填XYZ范围；另有DAGGER、摘要、390/320px窄屏证据。复用平台14px正文、36px控件，保留既有端侧调整字段。

## 核对与修正

- 旧行内密集控件替换为摘要，参考图的分区和双列范围输入落实。
- 初版弹窗纵向间距偏大，XYZ末尾及端侧调整需要滚动；压缩头部、字段间距、控件和分区，最终桌面截图完整显示全部配置及保存/取消。
- 最终对比无待修复P0/P1/P2问题。较矮视口允许内部滚动；没有要求窄屏一次显示所有字段。
- 33项独立Chrome专项验证新增、编辑、取消、Esc焦点、校验、cm→m持久化、Prompt关联；无采集模块未捕获异常。Python21项、语法/diff通过。
- 未运行成功旧全量主脚本（历史Prompt选择器不匹配）；没有生产及内置浏览器验证，以上为独立本地Chrome证据。

final result: passed

---

# 2026-10-24 采集结论与轨迹 Design QA

- 参考：用户本轮旧平台采集结论、逐条轨迹入口和 Base 图表截图；旧平台当前发布源码仅作为实现线索，未冒称已操作登录页。
- 保留列表内三视角播放；新增独立采集结论、筛选及逐条轨迹弹窗，表头/内容左对齐。
- 轨迹采用大弹窗，保留列表筛选与分页；三路视频、部件、State/Cmd、Base 角速度、共同播放和进度联动；关闭后释放资源并返回入口焦点。
- 修正弹窗双滚动条和时间轴过多小数；桌面左右图表、窄屏纵向图表，1366/1920/390/320 均无页面横向溢出。示例标识保留，防止曲线被误认为真实数据。
- 未接旧 Moz-Play 三维模型，汇总曲线标「总览」；真实无轨迹显示空态，采集结论不依赖质检状态。
- 45项轨迹、83项视频、68项布局、25项Python和语法/diff检查通过。目检桌面和手机截图，证据：项目根目录02-evidence/2026-10-24/collection-conclusion-trajectory/。

final result: passed（本地 Demo 范围，生产数据解析未接入）

---

# 后训练质检工作台 Design QA（历史保留）

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
