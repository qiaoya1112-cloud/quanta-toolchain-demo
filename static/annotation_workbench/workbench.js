// Local integration of the user-provided workbench reference. All assets are served locally.
const taskHeader = document.querySelector('workbench-task-header');
const instruction = document.querySelector('workbench-instruction');
const mediaViewer = document.querySelector('workbench-media-viewer');
const semanticTimeline = document.querySelector('semantic-annotation-track');
const actionTimeline = document.querySelector('action-annotation-track');
const qualityTimeline = document.querySelector('workbench-quality-track');
const segmentEditors = [...document.querySelectorAll('workbench-segment-editor')];
const semanticEditor = segmentEditors.find(editor => !editor.hasAttribute('variant'));
const qualityEditor = segmentEditors.find(editor => editor.getAttribute('variant') === 'variant-2');
const actionEditor = segmentEditors.find(editor => editor.getAttribute('variant') === 'variant-3');
const segmentList = document.querySelector('workbench-segment-list');
let activeWorkbenchMode = 'segments';
let activeSegmentIndex = 1;
const qualityList = segmentList.querySelector('[data-quality-list]');
// Share each record so navigation and error-reason edits use the same data.
qualityEditor._segments = qualityList._items.map(item => {
  Object.defineProperty(item, 'error', {get(){return this.reason;},set(value){this.reason=value;}, configurable:true});
  return item;
});
function syncQualityEditor() {
  const item = qualityList._items[activeSegmentIndex];
  if (!item) return;
  qualityEditor.querySelector('.workbench-mistake-description').value = item.description;
  qualityEditor.querySelectorAll('.workbench-severity-options input').forEach(input => {input.checked=input.value===item.severity;});
}
function updateQualityList() {
  const item=qualityList._items[activeSegmentIndex];
  if (!item) return;
  item.description=qualityEditor.querySelector('.workbench-mistake-description').value;
  item.severity=qualityEditor.querySelector('.workbench-severity-options input:checked')?.value || '轻微';
  qualityList.render();
}
qualityEditor.addEventListener('input',updateQualityList);
qualityEditor.addEventListener('change',updateQualityList);
qualityEditor.addEventListener('segment-update',updateQualityList);

taskHeader.addEventListener('workbench-close', () => {
  window.location.assign('/data/workbench-v2');
});

function selectSegment(index, source = 'page') {
  const safeIndex = Math.max(0, Math.min(5, Number(index) || 0));
  activeSegmentIndex = safeIndex;
  const activeTimeline = activeWorkbenchMode === 'action' ? actionTimeline : semanticTimeline;
  if (activeWorkbenchMode !== 'quality' && source !== activeTimeline) activeTimeline.selectSegment(safeIndex, false);
  segmentEditors.forEach(editor => {
    if (editor !== source) editor.setSegment(safeIndex + 1, false);
  });
  if (source !== 'list') segmentList.selectSegment(safeIndex + 1, false);
  syncQualityEditor();
}

[semanticTimeline, actionTimeline].forEach(track => track.addEventListener('track-change', event => {
  selectSegment(event.detail.index, track);
}));

segmentEditors.forEach(editor => editor.addEventListener('segment-change', event => {
  selectSegment(event.detail.index - 1, editor);
}));

segmentList.addEventListener('segment-change', event => {
  selectSegment(event.detail.index - 1, 'list');
});

segmentList.addEventListener('review-variant-change', event => {
  const variant = event.detail.variant;
  if (['quality', 'segments', 'action', 'tags'].includes(variant)) activeWorkbenchMode = variant;
  instruction.setMode(activeWorkbenchMode);
  const tagMode = activeWorkbenchMode === 'tags';
  tagsWorkspace.setVisible(tagMode);
  tagsWorkspace.panel.hidden = variant !== 'tags';
  const qualityMode = activeWorkbenchMode === 'quality';
  const actionMode = activeWorkbenchMode === 'action';
  mediaViewer.setAttribute('variant', qualityMode || tagMode ? 'three-panel' : 'default');
  semanticTimeline.hidden = qualityMode || actionMode || tagMode;
  actionTimeline.hidden = !actionMode;
  qualityTimeline.hidden = !qualityMode;
  const timelineCard = actionTimeline.closest('.timeline-card');
  timelineCard.classList.toggle('is-tags-mode', tagMode);
  timelineCard.classList.toggle('is-quality-mode', qualityMode);
  timelineCard.classList.toggle('is-action-mode', actionMode);
  semanticEditor.hidden = qualityMode || actionMode || tagMode;
  qualityEditor.hidden = !qualityMode;
  actionEditor.hidden = !actionMode;
  requestAnimationFrame(() => selectSegment(activeSegmentIndex, 'mode'));
});

selectSegment(1);

// Reveal the complete workspace together after its initial media has settled.
async function revealWorkbench() {
  const main=document.querySelector('.main');
  const minimumDisplay=Promise.resolve();
  const pending=[...mediaViewer.querySelectorAll('img')].map(img=>img.complete?Promise.resolve():new Promise(resolve=>{
    img.addEventListener('load',resolve,{once:true});
    img.addEventListener('error',resolve,{once:true});
  }));
  let timeout;
  await Promise.race([Promise.all(pending),new Promise(resolve=>{timeout=setTimeout(resolve,10000);})]);
  clearTimeout(timeout);
  await minimumDisplay;
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    main.classList.remove('is-loading');
    main.setAttribute('aria-busy','false');
    main.querySelectorAll(':scope > [inert]').forEach(element=>element.removeAttribute('inert'));
    main.querySelector('.workbench-loading')?.remove();
  }));
}
revealWorkbench();

// Drafts and actions belong to this local demo, scoped to the displayed record.
const draftKey = 'quanta.annotation-workbench.v1.' + taskHeader.dataset.id;
const annotationPanel = segmentList.querySelector('workbench-segment-list-panel');
const actionList = segmentList.querySelector('[data-action-list]');
const tagsWorkspace = new AnnotationTagWorkspace({
  timelineCard: semanticTimeline.closest('.timeline-card'),
  workspace: document.querySelector('.workspace'),
  sidebar: segmentList.querySelector('.workbench-review__main'),
  notify: notifyWorkbench
});
let noticeTimer;
function notifyWorkbench(message) {
  const notice = document.getElementById('workbenchNotice');
  notice.textContent = message; notice.hidden = false;
  clearTimeout(noticeTimer); noticeTimer = setTimeout(() => { notice.hidden = true; }, 3500);
}
function snapshotDraft() {
  return {
    semantic: semanticEditor._segments,
    quality: qualityList._items,
    action: actionEditor._segments,
    actionData: actionEditor._actionData,
    tagAnnotations: tagsWorkspace.snapshot(),
    conclusion: segmentList.querySelector('#quality-conclusion-select').value,
    selected: activeSegmentIndex,
    savedAt: new Date().toISOString()
  };
}
function saveDraft() {
  if (!tagsWorkspace.commitPending()) {
    segmentList.setVariant('tags');
    return false;
  }
  try { localStorage.setItem(draftKey, JSON.stringify(snapshotDraft())); return true; }
  catch (_) { notifyWorkbench('浏览器存储不可用，草稿尚未保存'); return false; }
}
function refreshSemanticList() {
  annotationPanel._segments = semanticEditor._segments.map(item => [item.start, item.end, item.duration, item.description, item.error, item.unavailable]);
  annotationPanel.selectSegment(activeSegmentIndex + 1, false);
}
function refreshActionList() {
  actionList._items.forEach((item, index) => {
    const data = actionEditor._actionData[index];
    item.elements = [...data.elements]; item.description = [...data.descriptions];
    item.reason = actionEditor._segments[index].error;
  });
  actionList.render();
}
// The reference dispatches updates from every editor. Keep updates mode-specific.
semanticEditor.addEventListener('segment-update', refreshSemanticList);
actionEditor.addEventListener('segment-update', refreshActionList);
actionEditor.addEventListener('action-annotation-change', refreshActionList);
document.addEventListener('segment-update', refreshSemanticList);
try {
  const saved = JSON.parse(localStorage.getItem(draftKey) || 'null');
  const validItems = items => Array.isArray(items) && items.length === 6 && items.every(item => item && typeof item.start === 'string' && typeof item.end === 'string');
  if (saved && validItems(saved.semantic) && validItems(saved.quality) && validItems(saved.action) && Array.isArray(saved.actionData) && saved.actionData.length === 6) {
    semanticEditor._segments = saved.semantic;
    qualityList._items = saved.quality;
    qualityEditor._segments = qualityList._items.map(item => {
      Object.defineProperty(item, 'error', { get() { return this.reason; }, set(value) { this.reason = value; }, configurable: true });
      return item;
    });
    actionEditor._segments = saved.action; actionEditor._actionData = saved.actionData;
    tagsWorkspace.restore(saved.tagAnnotations, saved.tags);
    segmentList.querySelector('#quality-conclusion-select').value = saved.conclusion === '合格' ? '合格' : '不合格';
    activeSegmentIndex = Math.max(0, Math.min(5, Number(saved.selected) || 0));
    refreshSemanticList(); refreshActionList(); qualityList.render(); selectSegment(activeSegmentIndex);
  }
} catch (_) { /* A damaged or incompatible draft leaves the initial demo usable. */ }
const rejectDialog = document.createElement('workbench-confirm-dialog');
rejectDialog.setAttribute('variant', 'reject'); document.body.append(rejectDialog);
function recordAction(action, reason = '') {
  if (!saveDraft()) return;
  const table = annotationPanel.querySelector('.review-log__table');
  const card = document.createElement('article'); card.className = 'review-log__card';
  const head = document.createElement('header');
  const time = document.createElement('time'); time.textContent = new Date().toLocaleString('zh-CN', { hour12: false });
  const badge = document.createElement('span'); badge.className = 'review-log__action'; badge.textContent = action;
  head.append(time, badge); card.append(head);
  const details = document.createElement('dl');
  for (const [name, value] of [['操作人', 'Joanna Qiao'], ['节点', '内部验收'], ['说明', reason || '本地演示操作']]) {
    const row = document.createElement('div'), term = document.createElement('dt'), detail = document.createElement('dd');
    term.textContent = name; detail.textContent = value; row.append(term, detail); details.append(row);
  }
  card.append(details); table.prepend(card);
  annotationPanel.querySelector('.review-log__summary > span:last-child').textContent = `共 ${table.children.length} 条`;
  notifyWorkbench(action === '保存' ? '草稿已保存到本机' : `已记录${action}演示，草稿已保存`);
}
rejectDialog.addEventListener('confirm-dialog-confirm', event => recordAction('驳回', event.detail.value));
segmentList.addEventListener('workbench-action', event => {
  const action = event.detail.action;
  if (action === 'reject') { rejectDialog.show(); return; }
  if (action === 'save') recordAction('保存');
  if (action === 'submit') recordAction('提交');
  if (action === 'leave' && saveDraft()) window.location.assign('/data/workbench-v2');
});
