const taskHeader = document.querySelector('workbench-task-header');
const instruction = document.querySelector('workbench-instruction');
const mediaViewer = document.querySelector('workbench-media-viewer');
const semanticTimeline = document.querySelector('semantic-annotation-track');
const actionTimeline = document.querySelector('action-annotation-track');
const qualityTimeline = document.querySelector('workbench-quality-track:not([data-pretraining])');
const pretrainingTimeline = document.querySelector('[data-pretraining]');
const pretrainingEditor = document.querySelector('.quality-review-editor');
const segmentEditors = [...document.querySelectorAll('workbench-segment-editor:not([hydrate])')];
const semanticEditor = segmentEditors.find(editor => !editor.hasAttribute('variant'));
const qualityEditor = segmentEditors.find(editor => editor.getAttribute('variant') === 'variant-2');
const actionEditor = segmentEditors.find(editor => editor.getAttribute('variant') === 'variant-3');
const segmentList = document.querySelector('workbench-segment-list');
let activeWorkbenchMode = 'quality';
let activeSegmentIndex = 1;
pretrainingEditor.setAttribute('data-no-error-reason','');
segmentList.querySelector('[data-pretraining-list]').setAttribute('data-no-error-reason','');
const qualityReview = createQualityReview({track:pretrainingTimeline,editor:pretrainingEditor,list:segmentList.querySelector('[data-pretraining-list]'),actions:segmentList.querySelector('[data-pretraining-actions]'),header:taskHeader});
const reviewCopies={};
for(const mode of ["posttraining", "posttraining-review", "rejection", "secondary-review"]){
const auditTimeline=document.createElement('workbench-quality-track');auditTimeline.setAttribute('duration','40');auditTimeline.hidden=true;pretrainingTimeline.after(auditTimeline);
const auditEditor=document.createElement('workbench-segment-editor');auditEditor.setAttribute('hydrate','');auditEditor.className='quality-review-editor';auditEditor.hidden=true;pretrainingEditor.after(auditEditor);
const auditList=document.createElement('workbench-annotation-list');auditList.setAttribute('variant','pretraining');auditList.setAttribute('data-posttraining-review-list','');auditList.dataset.reviewCopy=mode;auditList.hidden=true;
const auditActions=document.createElement('div');auditActions.className='workbench-quality-actions';auditActions.setAttribute('data-posttraining-review-actions','');auditActions.dataset.reviewCopy=mode;auditActions.hidden=true;auditActions.innerHTML='<workbench-quality-conclusion></workbench-quality-conclusion><workbench-footer-actions variant="quality"></workbench-footer-actions>';
segmentList.querySelector('.workbench-review__main').append(auditList,auditActions);
if(mode==='posttraining'){auditEditor.setAttribute('data-no-error-reason','');auditList.setAttribute('data-no-error-reason','');}
const auditReview=createQualityReview({track:auditTimeline,editor:auditEditor,list:auditList,actions:auditActions,header:taskHeader,storageNamespace:`workbench-${mode}-v1`});
reviewCopies[mode]={track:auditTimeline,editor:auditEditor,review:auditReview};
}
const qualityList = segmentList.querySelector('[data-quality-list]');
// Share each record so navigation and error-reason edits use the same data.
qualityEditor._segments = qualityList._items;
qualityList._items.forEach(item => {
  Object.defineProperty(item, 'error', {get(){return this.reason;},set(value){this.reason=value;}, configurable:true});
  return item;
});
const qualityRange=qualityTimeline.querySelector('timeline-range-selector');
qualityTimeline.classList.add('quality-review-track');
qualityTimeline.querySelectorAll('.segmented-timeline__range-fragment,.segmented-timeline__selection-label').forEach(node=>node.remove());
const qualityLanes=document.createElement('div');qualityLanes.className='quality-lanes';
qualityTimeline.querySelector('.segmented-timeline__body').append(qualityLanes);
const qualitySeconds=value=>value.split(':').reduce((total,part)=>total*60+Number(part),0);
const qualityTime=value=>{const rounded=Math.round(value*10)/10;return String(Math.floor(rounded/60)).padStart(2,'0')+':'+(rounded%60).toFixed(1).padStart(4,'0').replace(/\.0$/,'');};
qualityRange._format=percent=>qualityTime(percent*.9);
let qualityDraftSeverity='轻微';
function drawQualityTrack(){
  qualityLanes.replaceChildren();
  const assigned=[[]];
  const entries=qualityList._items.map((item,index)=>({item,index,start:qualitySeconds(item.start),end:qualitySeconds(item.end)}));
  if(qualityTimeline.classList.contains('is-adjusting-range')&&qualityRange._end>qualityRange._start)entries.push({item:{severity:qualityDraftSeverity},index:-1,start:qualityRange._start*.9,end:qualityRange._end*.9});
  entries.sort((a,b)=>a.start-b.start||a.end-b.end).forEach(entry=>{
    assigned[0].push(entry);
  });
  assigned.forEach((entries,index)=>{
    const lane=document.createElement('div');lane.className='quality-lane';
    entries.sort((a,b)=>(b.end-b.start)-(a.end-a.start)).forEach(entry=>{
      const block=document.createElement('button');block.type='button';
      block.className='quality-fragment '+(entry.item.severity==='严重'?'failure':'mistake')+(entry.index===activeSegmentIndex?' selected':'')+(entry.index<0?' quality-draft':'');
      block.style.left=entry.start/90*100+'%';block.style.width=(entry.end-entry.start)/90*100+'%';
      block.setAttribute('aria-label',entry.item.severity+' '+qualityTime(entry.start)+'至'+qualityTime(entry.end));
      if(entry.index>=0)block.addEventListener('click',()=>selectSegment(entry.index));
      lane.append(block);
    });qualityLanes.append(lane);
  });
}
function addQualitySegment(){
  const start=qualityRange._start*.9,end=qualityRange._end*.9;if(end<=start)return;
  const item={start:qualityTime(start),end:qualityTime(end),duration:qualityTime(end-start),severity:qualityDraftSeverity,description:'',reason:''};
  Object.defineProperty(item,'error',{get(){return this.reason;},set(value){this.reason=value;},configurable:true});
  qualityList._items.push(item);qualityTimeline.classList.remove('is-adjusting-range');
  selectSegment(qualityList._items.length-1);
}
qualityRange.addEventListener('range-change',()=>{
  if(qualityTimeline.classList.contains('is-adjusting-range')){drawQualityTrack();return;}
  const item=qualityList._items[activeSegmentIndex];if(!item||qualityRange._end<=qualityRange._start)return;
  item.start=qualityTime(qualityRange._start*.9);item.end=qualityTime(qualityRange._end*.9);item.duration=qualityTime((qualityRange._end-qualityRange._start)*.9);
  qualityEditor.setSegment(activeSegmentIndex+1,false);qualityList.render();drawQualityTrack();
});
qualityRange.addEventListener('range-commit',()=>{if(qualityTimeline.classList.contains('is-adjusting-range'))addQualitySegment();});
qualityTimeline.querySelector('[aria-label="添加"]').addEventListener('click',addQualitySegment);
function deleteQualitySegment(){
  qualityList._items.splice(activeSegmentIndex,1);selectSegment(Math.max(0,activeSegmentIndex-1));drawQualityTrack();
}
qualityTimeline.querySelector('[aria-label="清空"]').addEventListener('click',deleteQualitySegment);
qualityEditor.addEventListener('click',event=>{if(event.target.closest('[data-action=delete]'))deleteQualitySegment();});
qualityList.addEventListener('segment-delete',()=>{selectSegment(Math.max(0,activeSegmentIndex-1));drawQualityTrack();});
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
  qualityList.render();drawQualityTrack();
}
qualityEditor.addEventListener('input',updateQualityList);
qualityEditor.addEventListener('change',updateQualityList);
qualityEditor.addEventListener('segment-update',updateQualityList);

taskHeader.addEventListener('workbench-close', () => {
  window.location.assign('../action-quality-check/index.html');
});

function selectSegment(index, source = 'page') {
  if(reviewCopies[activeWorkbenchMode]){reviewCopies[activeWorkbenchMode].review.select(Number(index)||0);return;}
  if(activeWorkbenchMode==='pretraining'){qualityReview.select(Number(index)||0);return;}
  if(activeWorkbenchMode==='quality'){
    activeSegmentIndex=Math.max(0,Math.min(qualityList._items.length-1,Number(index)||0));
    qualityTimeline.classList.remove('is-adjusting-range');
    const item=qualityList._items[activeSegmentIndex];
    if(item){qualityEditor.hidden=false;qualityEditor.setSegment(activeSegmentIndex+1,false);qualityList.selectSegment(activeSegmentIndex+1,false);syncQualityEditor();qualityRange.setRange(qualitySeconds(item.start)/.9,qualitySeconds(item.end)/.9);qualityTimeline.seek?.(qualitySeconds(item.start)/.9);}
    else {qualityEditor.hidden=true;qualityList.render();}
    drawQualityTrack();return;
  }
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
  if (Object.hasOwn(reviewCopies,variant) || variant === 'pretraining' || variant === 'quality' || variant === 'segments' || variant === 'action') activeWorkbenchMode = variant;
  instruction.setMode((activeWorkbenchMode==='pretraining'||Object.hasOwn(reviewCopies,activeWorkbenchMode))?'quality':activeWorkbenchMode);
  const auditMode=Object.hasOwn(reviewCopies,activeWorkbenchMode);
  const pretrainingMode=activeWorkbenchMode==='pretraining'||auditMode;
  Object.entries(reviewCopies).forEach(([mode,copy])=>{const active=mode===activeWorkbenchMode;copy.track.hidden=!active;copy.editor.hidden=!active;if(active)requestAnimationFrame(()=>copy.review.activate());else copy.review.deactivate();});
  pretrainingTimeline.hidden=!pretrainingMode||auditMode;pretrainingEditor.hidden=!pretrainingMode||auditMode;
  const qualityMode = activeWorkbenchMode === 'quality';
  if (qualityMode||pretrainingMode) mediaViewer.setAttribute('variant', 'three-panel');
  else mediaViewer.removeAttribute('variant');
  const actionMode = activeWorkbenchMode === 'action';
  semanticTimeline.hidden = qualityMode || pretrainingMode || actionMode;
  actionTimeline.hidden = !actionMode;
  qualityTimeline.hidden = !qualityMode;
  const timelineCard = actionTimeline.closest('.timeline-card');
  timelineCard.classList.toggle('is-quality-mode', qualityMode);
  timelineCard.classList.toggle('is-pretraining-mode',pretrainingMode);
  timelineCard.classList.toggle('is-action-mode', actionMode);
  semanticEditor.hidden = qualityMode || pretrainingMode || actionMode;
  qualityEditor.hidden = !qualityMode;
  actionEditor.hidden = !actionMode;
  if(pretrainingMode&&!auditMode)requestAnimationFrame(()=>qualityReview.activate());
  else {qualityReview.deactivate();requestAnimationFrame(() => selectSegment(activeSegmentIndex, 'mode'));}
});

segmentList.setVariant('quality');
selectSegment(1);

// Reveal the complete workspace together after its initial media has settled.
async function revealWorkbench() {
  const main=document.querySelector('.main');
  const minimumDisplay=new Promise(resolve=>setTimeout(resolve,1500));
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

// Severity shortcuts belong only to the quality tab and never intercept typing.
document.addEventListener('keydown',event=>{
  if(segmentList.getAttribute('variant')!=='quality'||!event.ctrlKey||event.metaKey||event.altKey||event.shiftKey)return;
  if(event.target.closest('input,textarea,select,[contenteditable="true"]'))return;
  const severity={a:'轻微',s:'严重'}[event.key.toLowerCase()];
  if(!severity)return;
  const input=[...qualityEditor.querySelectorAll('.workbench-severity-options input')].find(input=>input.value===severity);
  if(!input)return;
  event.preventDefault();event.stopImmediatePropagation();
  qualityDraftSeverity=severity;
  qualityTimeline.activateRangeAdjustment?.();drawQualityTrack();
},true);
