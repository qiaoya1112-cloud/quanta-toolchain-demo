// Run the rendered demo's business logic without changing browser-local data.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(0, 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)]
  .map(match => match[1]).find(code => code.includes('var S026_STORAGE_KEY='));
assert.ok(script, 'The demo must render its application script');
const context = vm.createContext({
  URLSearchParams, Date, console,
  window: {location: {search: '', href: ''}},
  document: {addEventListener() {}},
  localStorage: {getItem() {return null;}, setItem() {}},
});
vm.runInContext(script.replace(/\ns026RenderAll\(\);\s*$/, ''), context);
const clone = value => JSON.parse(JSON.stringify(value));
let state = context.s026State;

// All pending versions, including later pages, are unreviewed. Opening them is read-only.
const batch = state.batches.find(item => item.status === '待审批');
const before = JSON.stringify(state);
const pending = context.s026PendingBatchVersions(batch);
assert.equal(pending.length, batch.count);
assert.equal(new Set(pending.map(item => item.id + '-' + item.version)).size, batch.count);
assert.ok(pending.every(item => item.decision === '待审批' && item.reason === ''));
assert.equal(JSON.stringify(state), before);

// Starting approval preserves the exact version set, and cannot be submitted twice.
context.s026CloseModal = () => {};
context.s026Save = () => {};
const count = state.approvals.length;
context.s026CreateApproval(batch.id);
assert.equal(state.approvals.length, count + 1);
assert.equal(batch.status, '已发起审批');
assert.deepEqual(clone(state.approvals[0].versions.map(v => [v.id, v.version, v.description])),
  clone(pending.map(v => [v.id, v.version, v.description])));
assert.ok(context.window.location.href.includes('mode=approve'));
context.s026CreateApproval(batch.id);
assert.equal(state.approvals.length, count + 1);

// Saved explicit upload rows must be used, not replaced by the demo seed pool.
const customBatch = {count: 1, versions: [{...pending[0], id: 'custom', description: 'custom description'}]};
assert.equal(context.s026PendingBatchVersions(customBatch)[0].id, 'custom');
assert.equal(context.s026PendingBatchVersions(customBatch)[0].description, 'custom description');

// Migrate legacy descriptions without resetting drafts, execution counts or formatted edits.
state = clone(context.S026_DEFAULT);
state.packages.unshift({id: 'my-draft', name: '保留我的草稿', keys: [], status: '待发布'});
const version = state.library[0].versions[0];
version.description = '旧的简短描述';
const customDescription = '【初始状态】用户自定义。【结束状态】完成。【时长上限】3分钟';
state.library[1].versions[0].description = customDescription;
const edge = JSON.stringify(state.edge);
context.s026NormalizeInstructionData(state);
assert.equal(state.packages[0].name, '保留我的草稿');
assert.equal(JSON.stringify(state.edge), edge);
assert.equal(state.library[1].versions[0].description, customDescription);
const descriptions = [
  ...state.library.flatMap(item => item.versions),
  ...state.approvals.flatMap(item => item.versions),
  ...state.projectInstructions,
];
assert.ok(descriptions.every(item => ['【初始状态】', '【结束状态】', '【时长上限】'].every(label => item.description.includes(label))));

// Flattened package/plan rows inherit iteration from the instruction, not the version.
context.s026State = state;
state.library[0].iteration = '第二轮';
state.library[0].versions[0].iteration = '错误的版本字段';
const key = state.library[0].id + '-' + state.library[0].versions[0].version;
assert.equal(context.s026LibraryVersionRecord(key).iteration, '第二轮');
assert.equal(context.s026PlanPackageRecord('CP260001', key).iteration, '第二轮');
// Model the requested five-record execution flow, including interrupted sessions.
const elements = new Map();
let centered = '';
const element = id => {
  if (!elements.has(id)) elements.set(id, {
    value: '', innerHTML: '', textContent: '', disabled: false, hidden: false,
    style: {}, classList: {add() {}, remove() {}, toggle() {}},
    setAttribute(name, value) {this[name] = value;},
    setCustomValidity(value) {this.validityMessage = value;},
    scrollIntoView() {centered = id;},
  });
  return elements.get(id);
};
const navigation = [element('packagesNav'), element('strategiesNav'), element('suppliersNav')];
context.document.getElementById = element;
context.document.querySelectorAll = selector => selector === '.s026PlanLockedNav' ? navigation : [];
context.document.querySelector = () => null;
context.requestAnimationFrame = callback => callback();
context.toast = () => {};
state = context.s026PrepareEdgeWorkflow(clone(context.S026_DEFAULT));
context.s026State = state;
state.edge.connected = true;
state.edge.wifiConnected = true;
const pkg = state.packages.find(item => item.id === 'CIP2609090001');
const task = context.s026EdgeTaskRecords(pkg, 'CP260001');
assert.equal(task.length, 5, 'Task snapshots retain all five assigned versions despite package deduplication');
assert.deepEqual(clone(task.map(record => state.edge.instances[record.instanceKey].status)),
  ['待采集', '待采集', '已跳过', '已采满', '未采满']);
const first = task[0].instanceKey, second = task[1].instanceKey;
context.s026Collect(first);
assert.equal(state.edge.instances[first].collected, 0, 'Starting collection must not collect a sample');
assert.equal(state.edge.instances[first].status, '采集中');
context.s026DemoCollectOne(first);
assert.equal(state.edge.instances[first].collected, 1);
assert.equal(state.edge.instances[first].elapsedSeconds, 30);
context.s026SetConnection('bluetooth', false);
assert.equal(state.edge.instances[first].status, '待采集');
context.s026Collect(first);
context.s026DemoCollectOne(first);
assert.equal(state.edge.instances[first].collected, 1, 'Disconnected actions cannot add data');
assert.equal(state.edge.instances[first].elapsedSeconds, 30);
context.s026SetConnection('bluetooth', true);
assert.equal(state.edge.instances[first].status, '待采集', 'Reconnect does not silently resume');
context.s026Collect(first);
for (let i=0; i<4; i++) context.s026DemoCollectOne(first);
assert.equal(state.edge.instances[first].status, '已采满');
assert.equal(state.edge.instances[first].collected, 5);
assert.equal(state.edge.instances[first].elapsedSeconds, 150);
assert.equal(state.edge.instances[second].status, '待采集');
assert.ok(Object.values(state.edge.instances).every(item => item.status !== '采集中'));
assert.equal(centered, 's026Instance-' + encodeURIComponent(first));
context.s026Collect(second);
context.s026DemoCollectOne(second);
element('s026SkipReason').value = '当前工作区不适配';
element('s026SkipNote').value = '测试';
context.s026ConfirmSkip(second);
assert.equal(state.edge.instances[second].status, '未采满');
assert.equal(state.edge.instances[second].collected, 1);
assert.ok(Object.values(state.edge.instances).every(item => item.status !== '采集中'));
context.s026WithdrawInstance(task[2].instanceKey);
context.s026Collect(task[2].instanceKey);
context.s026SetConnection('wifi', false);
assert.equal(state.edge.instances[task[2].instanceKey].status, '待采集');
assert.equal(context.s026EdgeReady(), false);
const disconnectedCard = context.s026RenderEdgeInstance(context.s026EdgeEntries(pkg,'CP260001',true)[0],true);
assert.ok([...disconnectedCard.matchAll(/<button\b[^>]*>/g)].every(match => match[0].includes('disabled')));
const savedExecution = JSON.stringify(state.edge.instances);
context.s026PrepareEdgeWorkflow(state);
assert.equal(JSON.stringify(state.edge.instances), savedExecution, 'Migration must not reseed on later page loads');

// Filling the three base fields unlocks actions without a save button or blur cycle.
context.S026_PAGE_MODE = 'package-detail';
context.window.location.search = '?id=CIP2609070003';
const draft = state.packages.find(item => item.id === 'CIP2609070003');
element('s026PackageBaseName').value = '自动保存测试';
element('s026PackageBaseScene').value = '';
element('s026PackageBaseZone').value = '';
context.s026AutoSavePackageBase();
assert.equal(element('s026PackageImportButton').disabled, true);
element('s026PackageBaseScene').value = '家庭';
element('s026PackageBaseZone').value = '厨房';
context.s026AutoSavePackageBase();
assert.equal(element('s026PackageImportButton').disabled, false);
assert.equal(draft.name, '自动保存测试');
assert.equal(draft.configured, true);
context.s026SelectedProject = 'CP260002';
element('s026PlanBaseName').value = '新的唯一方案名称';
element('s026PlanBaseType').value = '指令包采集';
element('s026PlanBaseScene').value = '家庭';
context.s026AutoSavePlanBase();
assert.ok(navigation.every(button => !button.disabled));
element('s026PlanBaseName').value = state.projects[0].name;
context.s026AutoSavePlanBase();
assert.ok(navigation.every(button => button.disabled));
assert.equal(element('s026PlanBaseName').validityMessage, '采集方案名称已存在');

// Pending approval renders the sole applicable result and the requested column order.
context.S026_PAGE_MODE = 'approval-detail';
context.window.location.search = '?batch=UP260907001';
context.s026RenderApprovalDetail();
const approvalHTML = element('s026ApprovalDetail').innerHTML;
const resultOptions = approvalHTML.match(/<select id="s026ApprovalDetailDecision">([\s\S]*?)<\/select>/)[1];
assert.equal((resultOptions.match(/<option/g)||[]).length, 1);
assert.ok(resultOptions.includes('待审批'));
assert.ok(approvalHTML.includes('<th>指令 ID</th><th>指令名称</th><th>指令迭代</th><th>场景</th><th>工作区</th><th>指令版本号</th><th>指令描述</th>'));
assert.ok(element('s026DetailStatus').innerHTML.includes('待审批'));
const limit = context.s026StrategyLimitField('s026StrategyInstruction','单条指令采集条数','无限制','条 / 指令');
assert.ok(!limit.includes('value="unlimited"'));
assert.ok(limit.includes('value="1"'));

// Skipping another waiting row must not create two simultaneous recordings.
state = context.s026PrepareEdgeWorkflow(clone(context.S026_DEFAULT));
context.s026State = state;
state.edge.connected = true;
state.edge.wifiConnected = true;
context.s026Collect(first);
context.s026ConfirmSkip(second);
assert.equal(state.edge.instances[second].status, '已跳过');
assert.equal(Object.values(state.edge.instances).filter(item => item.status === '采集中').length, 1);
assert.equal(state.edge.instances[first].status, '采集中');

// Skipping exits collection, preserves data, and waits for a manual next selection.
state = context.s026PrepareEdgeWorkflow(clone(context.S026_DEFAULT));
context.s026State = state;
state.edge.connected = true;
state.edge.wifiConnected = true;
context.s026Collect(first);
context.s026DemoCollectOne(first);
context.s026ConfirmSkip(first);
assert.equal(state.edge.instances[first].status, '未采满');
assert.equal(state.edge.instances[first].elapsedSeconds, 30);
assert.equal(state.edge.instances[second].status, '待采集');
assert.ok(Object.values(state.edge.instances).every(item => item.status !== '采集中'));
assert.equal(centered, 's026Instance-' + encodeURIComponent(first));
context.s026Collect(second);
assert.equal(centered, 's026Instance-' + encodeURIComponent(second));
const ordered = context.s026EdgeEntries(pkg, 'CP260001', true);
assert.equal(ordered[0].instance.status, '采集中');
assert.ok(ordered.slice(1).every(entry => ['已跳过','已采满','未采满'].includes(entry.instance.status)));

// Render all existing panes against minimal DOM sinks to catch missing handlers/fields.
context.document.querySelector = selector => element(selector);
context.s026RenderAll();
assert.ok(element('s026EdgeWork').innerHTML.includes('仅供演示'));
assert.ok(!element('s026EdgeWork').innerHTML.includes('s026-device-bar'));
const statusBar = element('s026EdgeWork').innerHTML.match(/<div class="s026-edge-progress">([\s\S]*?)<\/div>/)[1];
assert.equal((statusBar.match(/<button/g)||[]).length, 5);
assert.ok(!statusBar.includes('<span>采集中</span>'));
assert.ok(!element('s026EdgeWork').innerHTML.includes('已执行数据'));

// Compact card headings: no difficulty, inline index, and no duplicate active status.
const currentEntry = context.s026EdgeEntries(pkg, 'CP260001', true)[0];
const currentCard = context.s026RenderEdgeInstance(currentEntry, true);
assert.ok(!currentCard.includes('难度'));
assert.ok(!currentCard.includes('s026-instance-side'));
assert.ok(currentCard.includes('s026-collecting-banner'));
assert.ok(currentCard.includes('role="progressbar"'));
assert.ok(currentCard.includes('<span class="s026-instance-id"><i class="s026-instance-index">'));
context.s026ExitCollection(currentEntry.record.instanceKey);
const exitedCard = context.s026RenderEdgeInstance(currentEntry, true);
assert.ok(exitedCard.includes('s026-instance-count'));
assert.ok(exitedCard.includes('待采集'));
assert.ok(!exitedCard.includes('s026-collecting-banner'));
assert.ok(!exitedCard.includes('难度'));

// Connection actions use the app-contained dialog, never the web modal.
context.s026Modal = () => {throw new Error('Connection dialog escaped the app surface');};
context.s026OpenConnection('bluetooth');
assert.equal(element('s026EdgeConnectionMask')['aria-hidden'], 'false');
assert.equal(element('s026EdgeConnectionTitle').textContent, '蓝牙连接');
assert.ok(element('s026EdgeConnectionFoot').innerHTML.includes('断开连接'));
assert.ok(element('s026EdgeConnectionBody').innerHTML.includes(state.edge.device));
context.s026SetConnection('bluetooth', false);
assert.equal(element('s026EdgeConnectionMask')['aria-hidden'], 'true');
context.s026OpenConnection('bluetooth');
assert.ok(!element('s026EdgeConnectionFoot').innerHTML.includes('断开连接'));
context.s026CloseConnection();
assert.equal(element('s026EdgeConnectionMask')['aria-hidden'], 'true');
// Published package membership is immutable; per-package availability and props persist.
state = context.s026PrepareEdgeWorkflow(clone(context.S026_DEFAULT));
context.s026State = state;
context.S026_PAGE_MODE = 'plan-detail';
context.s026SelectedProject = 'CP260001';
context.s026PageParams = new URLSearchParams('id=CP260001');
const sourcePackage = state.packages.find(item => item.id === 'CIP2609070001');
context.s026ActivePackage = sourcePackage.id;
context.s026PackageReorderMode = false;
const membership = JSON.stringify(sourcePackage.keys);
const sourceKey = sourcePackage.keys[0];
assert.notEqual(sourcePackage.status, '待发布');
context.s026RemoveFromPackage(sourceKey);
assert.equal(JSON.stringify(sourcePackage.keys), membership);
context.s026RenderPackageDetail();
assert.ok(!element('s026PackageDetailRows').innerHTML.includes('>删除</button>'));
assert.equal(element('s026PackageVersionStatusHeader').hidden, false);
assert.ok(element('s026PackageDetailRows').innerHTML.includes('s026TogglePackageVersion'));
const sourceVersion = state.library.find(item => sourceKey.startsWith(item.id + '-')).versions
  .find(item => sourceKey.endsWith('-' + item.version));
sourceVersion.props = '专用道具、共享道具、专用道具';
const otherKey = sourcePackage.keys[1];
const otherVersion = state.library.find(item => otherKey.startsWith(item.id + '-')).versions
  .find(item => otherKey.endsWith('-' + item.version));
otherVersion.props = '共享道具，备用道具';
assert.equal(context.s026PackageProps(sourcePackage), '专用道具、共享道具、备用道具');
context.s026TogglePackageVersion(sourceKey);
assert.equal(context.s026PackageProps(sourcePackage), '共享道具、备用道具');
assert.equal(JSON.stringify(sourcePackage.keys), membership);
assert.equal(context.s026PlanVersionState('CP260001', sourcePackage.id, sourceKey), '下线');
const reference = context.s026PlanReference('CP260001', sourcePackage.id);
reference.versionOverrides = {[sourceKey]: '上线'};
assert.equal(context.s026PlanVersionState('CP260001', sourcePackage.id, sourceKey), '下线', 'Plan overrides cannot bypass source offline state');
const restored = context.s026PrepareEdgeWorkflow(context.s026NormalizeInstructionData(clone(state)));
assert.ok(restored.packages.find(item => item.id === sourcePackage.id).offlineKeys.includes(sourceKey));
context.s026TogglePackageVersion(sourceKey);
assert.equal(context.s026PackageProps(sourcePackage), '专用道具、共享道具、备用道具');
sourcePackage.status = '下线';
context.s026RemoveFromPackage(sourceKey);
assert.equal(JSON.stringify(sourcePackage.keys), membership, 'Offline published packages still cannot delete versions');
sourcePackage.status = '上线';
const draftPackage = {...clone(sourcePackage), id: 'draft-test', status: '待发布'};
state.packages.push(draftPackage);
context.s026ActivePackage = draftPackage.id;
context.s026RenderPackageDetail();
assert.ok(element('s026PackageDetailRows').innerHTML.includes('>删除</button>'));
assert.equal(element('s026PackageVersionStatusHeader').hidden, true);
assert.ok(!element('s026PackageDetailRows').innerHTML.includes('s026-status'));
context.s026RemoveFromPackage(sourceKey);
assert.ok(!draftPackage.keys.includes(sourceKey));

// Plan search accepts partial iteration text; mirror and version ordering agree with headers.
state.library.find(item => sourceKey.startsWith(item.id + '-')).iteration = '第二轮采集';
sourceVersion.image = '';
context.s026PlanInstructionFilters = {iteration: '二轮'};
context.s026RenderPlanInstructions();
const planTable = element('s026PlanInstructionTable').innerHTML;
assert.ok(planTable.includes('<th>指令名称</th><th>指令迭代</th><th>指令版本号</th>'));
assert.ok(planTable.includes('第二轮采集</td><td><span class="s026-code">'));
assert.ok(planTable.includes('<th>难度</th><th>镜像</th><th>道具</th>'));
assert.equal(context.s026CollectPlanInstructionVersions().find(item => item.key === sourceKey).mirror, 0);
sourceVersion.image = 'quanta-collect:2026.09';
assert.equal(context.s026CollectPlanInstructionVersions().find(item => item.key === sourceKey).mirror, 1);
context.s026PlanInstructionFilters = {iteration: '不存在的迭代'};
context.s026RenderPlanInstructions();
assert.ok(element('s026PlanInstructionTable').innerHTML.includes('没有匹配的指令版本'));
const planFilters = html.split('id="s026PlanInstructionView"')[1].split('id="s026PlanInstructionTable"')[0];
assert.ok(planFilters.includes('<input id="s026PlanInstructionIteration"'));
assert.ok(planFilters.indexOf('s026PlanInstructionIteration') < planFilters.indexOf('s026PlanInstructionVersionQuery'));
context.s026PageParams = new URLSearchParams('plan=CP260001&package=' + sourcePackage.id);
context.s026RenderPlanPackageDetail();
const detailRows = element('s026PlanPackageDetailRows').innerHTML;
assert.ok(!/draggable|ondrag|ondrop|⋮/.test(detailRows));
assert.equal(typeof context.s026DropPlanPackageVersion, 'undefined');
assert.ok(html.includes('<th>目标时长</th><th>已采时长</th>'));

// Threshold hint uses the exact collected lower bound, and saves reject lower values.
let modalBody = '';
context.s026Modal = (title, body) => {modalBody = body;};
const controlled = context.s026EnsurePlanPackageRecord('CP260001', sourceKey);
controlled.collected = 7.25;
controlled.threshold = 9;
context.s026OpenThresholdAdjust(sourcePackage.id, sourceKey);
assert.ok(modalBody.includes('阈值不能小于 7.25 小时'));
assert.ok(modalBody.includes('min="7.25"'));
assert.ok(modalBody.includes('aria-describedby="s026ThresholdHint"'));
element('s026ThresholdValue').value = '7.24';
context.s026SaveThreshold(sourcePackage.id, sourceKey);
assert.equal(controlled.threshold, 9);
element('s026ThresholdValue').value = '7.25';
context.s026SaveThreshold(sourcePackage.id, sourceKey);
assert.equal(controlled.threshold, 7.25);

// Viewing another package is connection-free; claiming then exposes connection controls.
state = context.s026PrepareEdgeWorkflow(clone(context.S026_DEFAULT));
context.s026State = state;
context.s026PageParams = new URLSearchParams('project=CP260001&package=CIP2609070001');
state.edge.connected = false;
state.edge.wifiConnected = false;
context.s026EdgeStatusFilter = '已跳过';
context.s026RenderEdgeWork();
assert.equal(element('s026EdgeConnections').hidden, true);
assert.equal(element('s026EdgeConnections').innerHTML, '');
assert.equal(element('s026EdgeConnectionWarning').hidden, true);
assert.ok(element('s026EdgeWork').innerHTML.includes('s026-instance-heading'), 'Preview ignores the active task filter');
state.edge.activePackage = '';
context.s026RenderEdgeWork();
assert.ok(!element('s026EdgeWork').innerHTML.includes('s026-edge-submit" disabled'));
context.s026ClaimPackage('CIP2609070001');
assert.equal(state.edge.activePackage, 'CIP2609070001');
context.s026RenderEdgeWork();
assert.equal(element('s026EdgeConnections').hidden, false);
assert.ok(element('s026EdgeConnections').innerHTML.includes('蓝牙'));
assert.equal(element('s026EdgeConnectionWarning').hidden, false);
const claimed = context.s026EdgeTaskRecords(state.packages.find(item => item.id === state.edge.activePackage), 'CP260001');
context.s026Collect(claimed[0].instanceKey);
assert.equal(state.edge.instances[claimed[0].instanceKey].status, '待采集', 'Claiming disconnected must not permit collection');
context.s026SetConnection('bluetooth', true);
context.s026SetConnection('wifi', true);
context.s026RenderEdgeWork();
assert.equal(element('s026EdgeConnectionWarning').hidden, true);
context.s026Collect(claimed[0].instanceKey);
assert.equal(state.edge.instances[claimed[0].instanceKey].status, '采集中');
// Imports into published packages stay pending across reloads and package off/on cycles.
state = context.s026PrepareEdgeWorkflow(clone(context.S026_DEFAULT));
context.s026State = state;
context.S026_PAGE_MODE = 'plan-detail';
context.s026ActivePackage = 'CIP2609070001';
let publishingPackage = context.s026ActivePackageRecord();
const importedKey = '100031-V1';
assert.ok(!publishingPackage.keys.includes(importedKey));
context.document.querySelectorAll = selector => selector === '.s026-package-choice:checked' ? [{value: importedKey}] : [];
context.s026ImportPackageVersions();
context.s026ImportPackageVersions();
assert.equal(publishingPackage.keys.filter(key => key === importedKey).length, 1);
assert.equal(publishingPackage.pendingKeys.filter(key => key === importedKey).length, 1);
context.s026RenderPackageDetail();
let importedRow = element('s026PackageDetailRows').innerHTML.split('<tr').find(row => row.includes('100031'));
assert.ok(importedRow.includes('待发布') && importedRow.includes('>发布</button>') && importedRow.includes('>删除</button>'));
assert.ok(!importedRow.includes('s026TogglePackageVersion'));
context.s026TogglePackageVersion(importedKey);
assert.equal(context.s026PackageVersionState(publishingPackage, importedKey), '待发布');
context.s026SetPackageStatus(publishingPackage.id, '下线', '下线');
context.s026SetPackageStatus(publishingPackage.id, '上线', '上线');
context.s026State = context.s026PrepareEdgeWorkflow(context.s026NormalizeInstructionData(clone(state)));
publishingPackage = context.s026ActivePackageRecord();
assert.equal(context.s026PackageVersionState(publishingPackage, importedKey), '待发布');
context.s026PlanReference('CP260001', publishingPackage.id).versionOverrides[importedKey] = '上线';
assert.equal(context.s026PlanVersionState('CP260001', publishingPackage.id, importedKey), '待发布', 'Plan overrides cannot publish a pending source version');
assert.ok(!context.s026EdgeEntries(publishingPackage, 'CP260001', false).some(entry => entry.record.key === importedKey));
context.s026RemoveFromPackage(importedKey);
assert.ok(!publishingPackage.keys.includes(importedKey) && !publishingPackage.pendingKeys.includes(importedKey));
context.s026ImportPackageVersions();
context.s026PublishPackageVersion(importedKey);
assert.equal(context.s026PackageVersionState(publishingPackage, importedKey), '上线');
context.s026RenderPackageDetail();
importedRow = element('s026PackageDetailRows').innerHTML.split('<tr').find(row => row.includes('100031'));
assert.ok(importedRow.includes('>下线</button>') && !importedRow.includes('>删除</button>'));
context.s026RemoveFromPackage(importedKey);
assert.ok(publishingPackage.keys.includes(importedKey), 'Published versions cannot be deleted');
context.s026TogglePackageVersion(importedKey);
assert.equal(context.s026PackageVersionState(publishingPackage, importedKey), '下线');
context.s026TogglePackageVersion(importedKey);
assert.equal(context.s026PackageVersionState(publishingPackage, importedKey), '上线');

context.s026ActivePackage = 'CIP2609070003';
const initialDraft = context.s026ActivePackageRecord();
context.s026ImportPackageVersions();
context.s026RenderPackageDetail();
assert.equal(element('s026PackageVersionStatusHeader').hidden, true);
assert.ok(!element('s026PackageDetailRows').innerHTML.includes('s026-status'));
context.s026SetPackageStatus(initialDraft.id, '上线', '发布');
assert.equal(initialDraft.pendingKeys.length, 0, 'Initial package publication publishes all imported versions');
context.s026RenderPackageDetail();
assert.equal(element('s026PackageVersionStatusHeader').hidden, false);
assert.ok(!element('s026PackageDetailRows').innerHTML.includes('>删除</button>'));
// Rejection reasons are required multi-select; optional notes always show and round-trip.
context.s026ActiveApproval = context.s026State.approvals[0].id;
const rejectedVersion = context.s026State.approvals[0].versions[0];
let selectedReasons = [];
context.document.querySelectorAll = selector => selector === '.s026-reject-reason:checked' ? selectedReasons.map(value => ({value})) : [];
context.s026OpenReject(0);
assert.equal((modalBody.match(/class="s026-reject-reason"/g) || []).length, 9);
assert.ok(!modalBody.includes('id="s026RejectNoteField" hidden'));
assert.ok(modalBody.includes('自定义说明（选填）'));
assert.ok(modalBody.includes('maxlength="50"'));
const rejectionBefore = JSON.stringify(rejectedVersion);
element('s026RejectNote').value = '仅填写说明不能替代必填原因';
context.s026ConfirmReject(0);
assert.equal(JSON.stringify(rejectedVersion), rejectionBefore);
assert.equal(element('s026RejectError').hidden, false);
selectedReasons = ['指令关键要素不完整', '设备操作不便'];
context.s026UpdateRejectSelection();
assert.equal(element('s026RejectError').hidden, true);
element('s026RejectNote').value = '字'.repeat(51);
context.s026ConfirmReject(0);
assert.equal(JSON.stringify(rejectedVersion), rejectionBefore);
element('s026RejectNote').value = '字'.repeat(50);
context.s026UpdateRejectNoteCount();
assert.equal(element('s026RejectNoteCount').textContent, '50 / 50');
context.s026ConfirmReject(0);
assert.equal(rejectedVersion.reason, selectedReasons.join('；') + '；' + '字'.repeat(50));
assert.equal(rejectedVersion.decision, '审批不合格');
const reloadedRejection = context.s026RejectValues(clone(rejectedVersion));
assert.deepEqual(clone(reloadedRejection.reasons), selectedReasons);
assert.equal(reloadedRejection.note, '字'.repeat(50));
context.s026OpenReject(0);
assert.equal((modalBody.match(/ checked/g) || []).length, 2);
assert.ok(modalBody.includes('>' + '字'.repeat(50) + '</textarea>'));
element('s026RejectNote').value = '<script>测试</script>';
context.s026ConfirmReject(0);
context.s026OpenReject(0);
assert.ok(modalBody.includes('&lt;script&gt;测试&lt;/script&gt;'));
context.window.location.search = '?id=' + context.s026ActiveApproval + '&mode=view';
context.s026RenderApprovalDetail();
assert.ok(element('s026ApprovalDetail').innerHTML.includes(selectedReasons.join('；') + '；&lt;script&gt;测试&lt;/script&gt;'));
element('s026RejectNote').value = '';
context.s026ConfirmReject(0);
assert.equal(rejectedVersion.reason, selectedReasons.join('；'), 'Custom text is optional for every selection');
selectedReasons = ['其他'];
context.s026ConfirmReject(0);
assert.equal(rejectedVersion.reason, '其他');
assert.deepEqual(clone(context.s026RejectValues({reason:'其他：旧的补充说明'})), {reasons:['其他'], note:'旧的补充说明'});
assert.deepEqual(clone(context.s026RejectValues({reason:'初始或结束状态不明确'})), {reasons:['其他'], note:'初始或结束状态不明确'});
context.s026SetDecision(0, '审批合格');
assert.equal(rejectedVersion.reason, '');
assert.equal(rejectedVersion.rejectionReasons.length, 0);
assert.equal(rejectedVersion.rejectionNote, '');

// Both duplicate packages and overlapping instruction versions remain visible and disabled.
state = context.s026PrepareEdgeWorkflow(clone(context.S026_DEFAULT));
context.s026State = state;
context.s026SelectedProject = 'CP260001';
const duplicateSource = state.packages.find(item => item.id === 'CIP2609070001');
const duplicateCandidate = {...clone(duplicateSource), id:'DUPLICATE-INSTRUCTIONS', name:'重复指令候选'};
const allowedCandidate = {...clone(duplicateSource), id:'NEW-INSTRUCTIONS', name:'可导入候选', keys:['100031-V1']};
const batchDuplicate = {...clone(allowedCandidate), id:'BATCH-DUPLICATE'};
state.packages.push(duplicateCandidate, allowedCandidate, batchDuplicate);
context.s026OpenPlanPackageImport();
const candidateRow = id => modalBody.split('<label class="s026-choice-row').find(row => row.includes('data-id="' + id + '"'));
assert.ok(candidateRow(duplicateSource.id).includes('>已导入</span>'));
assert.ok(candidateRow(duplicateSource.id).includes('disabled'));
assert.ok(candidateRow(duplicateCandidate.id).includes('>已导入</span>'));
assert.ok(candidateRow(duplicateCandidate.id).includes('disabled'));
assert.ok(candidateRow(allowedCandidate.id).includes('可导入'));
assert.ok(!candidateRow(allowedCandidate.id).includes('disabled'));
let packagesToImport = [duplicateSource.id, duplicateCandidate.id];
context.document.querySelectorAll = selector => selector === '.s026-plan-package-choice:checked' ? packagesToImport.map(value => ({value})) : [];
const referencesBefore = state.projectPackages.length;
context.s026ImportPlanPackages();
assert.equal(state.projectPackages.length, referencesBefore, 'Disabled choices cannot bypass duplicate checks');
packagesToImport = [allowedCandidate.id, batchDuplicate.id];
context.s026ImportPlanPackages();
assert.equal(state.projectPackages.length, referencesBefore + 1, 'Same-batch imports cannot add overlapping versions twice');
assert.ok(context.s026PlanReference('CP260001', allowedCandidate.id));
assert.ok(!context.s026PlanReference('CP260001', batchDuplicate.id));
assert.ok(['上线', '暂停'].includes(context.s026PlanReference('CP260001', allowedCandidate.id).status));

// Legacy imported drafts become operational references, without touching source drafts.
const migratedReference = context.s026PlanReference('CP260001', allowedCandidate.id);
migratedReference.status = '待发布';
context.s026SyncPlanPackage(migratedReference);
assert.notEqual(migratedReference.status, '待发布');

// Total progress and plan-local duration remain distinct, including newly imported versions.
state = context.s026PrepareEdgeWorkflow(clone(context.S026_DEFAULT));
context.s026State = state;
context.s026SelectedProject = 'CP260001';
const hoursSource = state.library.find(item => item.id === '100021').versions.find(item => item.version === 'V3');
const hoursLocal = state.projectInstructions.find(item => item.projectId === 'CP260001' && item.key === '100021-V3');
hoursSource.collected = 10;
hoursLocal.collected = 3;
const hoursRecord = context.s026PlanPackageRecord('CP260001', '100021-V3');
assert.equal(hoursRecord.collected, 10);
assert.equal(hoursRecord.planCollected, 3);
assert.equal(context.s026PlanPackageRecord('CP260002', '100021-V3').planCollected, 0);
context.s026EnsurePlanPackageRecord('CP260002', '100021-V3');
assert.equal(context.s026PlanPackageRecord('CP260002', '100021-V3').planCollected, 0, 'Setting a threshold must not copy global hours into the plan');
const compactProgress = context.s026PlanProgress(6.3, 10);
assert.ok(compactProgress.includes('6.3/10h'));
assert.ok(compactProgress.indexOf('<b>') < compactProgress.indexOf('s026-progress-track'));
assert.ok(compactProgress.indexOf('s026-progress-track') < compactProgress.indexOf('<small>'));
assert.ok(context.s026PlanProgress(12, 10).includes('超目标 2.0h'));
assert.ok(context.s026PlanProgress(10, 10).includes('已达目标'));
context.s026RenderPlanInstructions();
assert.ok(element('s026PlanInstructionTable').innerHTML.includes('本方案内的已采集时长'));
assert.ok(element('s026PlanInstructionTable').innerHTML.includes('s026-plan-collected-cell'));

// Props are the actual eligible union: no filler, no completed/paused/offline props.
const previewPackage = state.packages.find(item => item.id === 'CIP2609070001');
const previewRecords = context.s026EdgeClaimableRecords(previewPackage, 'CP260001');
const expectedProps = [...new Set(previewRecords.flatMap(record => record.props.split('、')))];
assert.deepEqual(clone(context.s026EdgePackageProps(previewPackage, 'CP260001')), expectedProps);
const executedKey = context.s026EdgeInstanceKey(previewPackage, previewRecords[0].key, 'CP260001');
state.edge.instances[executedKey] = {packageId: previewPackage.id, status:'已采满', collected:5, required:5, reason:''};
assert.ok(!context.s026EdgeClaimableRecords(previewPackage, 'CP260001').some(record => record.key === previewRecords[0].key));
const previewEntries = context.s026EdgeEntries(previewPackage, 'CP260001', false);
const executedEntry = previewEntries.find(entry => entry.record.instanceKey === executedKey);
assert.equal(executedEntry.instance.status, '已采满');
const executedCard = context.s026RenderEdgeInstance(executedEntry, false);
assert.ok(executedCard.includes(executedEntry.record.instructionName));
assert.ok(!executedCard.includes('<p>') && !executedCard.includes('s026-instance-meta'));
const waitingEntry = previewEntries.find(entry => entry.instance.status === '待领取');
assert.ok(context.s026RenderEdgeInstance(waitingEntry, false).includes('s026-instance-meta'));
state.edge.activePackage = '';
context.s026ClaimPackage(previewPackage.id);
assert.equal(state.edge.instances[executedKey].status, '已采满', 'Claiming must preserve executed rows');
assert.ok(context.s026EdgeEntries(previewPackage, 'CP260001', true).some(entry => entry.record.instanceKey === executedKey));
state.edge.completedPackages.push('CP260001::' + previewPackage.id);
context.s026RenderEdge();
const completedCard = element('s026EdgePackages').innerHTML.split('<article').find(card => card.includes('completed') && card.includes(previewPackage.name));
assert.ok(completedCard && !completedCard.includes('s026-props'));
// Submitting full and partial collection records archives both as collected, not skipped.
state = context.s026PrepareEdgeWorkflow(clone(context.S026_DEFAULT));
context.s026State = state;
state.edge.connected = state.edge.wifiConnected = true;
const submittedPackage = state.packages.find(item => item.id === state.edge.activePackage);
const submittedTask = context.s026EdgeTaskRecords(submittedPackage, 'CP260001');
submittedTask.forEach((record, index) => {state.edge.instances[record.instanceKey].status = index === 0 ? '已采满' : index === 1 ? '未采满' : '已跳过';});
context.s026FinishPackage();
assert.equal(state.edge.instances[submittedTask[0].instanceKey].status, '已采集');
assert.equal(state.edge.instances[submittedTask[1].instanceKey].status, '已采集');
assert.equal(state.edge.instances[submittedTask[2].instanceKey].status, '已跳过');
const archivedEntries = context.s026EdgeEntries(submittedPackage, 'CP260001', false).filter(entry => entry.instance.status === '已采集');
assert.equal(archivedEntries.length, 2);
assert.ok(archivedEntries.every(entry => !context.s026RenderEdgeInstance(entry, false).includes('s026-instance-meta')));
context.s026State = context.s026PrepareEdgeWorkflow(clone(state));
assert.equal(context.s026EdgeEntries(submittedPackage, 'CP260001', false).filter(entry => entry.instance.status === '已采集').length, 2);
const fixture = context.s026EdgeEntries(previewPackage, 'CP260001', false).find(entry => entry.record.key === '100021-V2');
assert.equal(fixture.instance.status, '已采集');

// Upload failures share a label; content errors retain their detailed error action.
let pendingTimers = new Map(), timerId = 0;
context.setTimeout = callback => {pendingTimers.set(++timerId, callback); return timerId;};
context.clearTimeout = id => pendingTimers.delete(id);
const flushTimers = () => {while(pendingTimers.size){const [id, callback] = pendingTimers.entries().next().value;pendingTimers.delete(id);callback();}};
context.s026LoadInvalidDemoFile();
flushTimers();
assert.equal(context.s026DemoFileStatus, 'validation-error');
assert.ok(element('s026UploadState').innerHTML.includes('上传失败'));
assert.ok(!element('s026UploadState').innerHTML.includes('校验失败'));
assert.ok(element('s026UploadState').innerHTML.includes('查看错误'));
assert.equal(element('s026UploadConfirm').disabled, true);
assert.ok(!script.includes('载入过大文件'));
context.s026QueueUpload('too-large.xlsx', 21 * 1024 * 1024, false);
flushTimers();
assert.equal(context.s026DemoFileStatus, 'upload-error');
assert.ok(element('s026UploadState').innerHTML.includes('上传失败'));
assert.ok(!element('s026UploadState').innerHTML.includes('查看错误'));
assert.equal(element('s026UploadConfirm').disabled, true);
context.s026LoadCompliantDemoFile();
flushTimers();
assert.equal(context.s026DemoFileStatus, 'success');
assert.equal(element('s026UploadConfirm').disabled, false);
context.s026LoadInvalidDemoFile();
context.s026DeleteUploadFile();
flushTimers();
assert.equal(context.s026DemoFileStatus, 'empty');
console.log('Approval, imports, publication, progress, uploads and submitted collection history checks passed');
