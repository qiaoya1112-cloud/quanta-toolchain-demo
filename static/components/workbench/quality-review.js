const qualityReviewAssetRoot=new URL('../../pages/workbench/assets/',document.currentScript?.src||new URL('components/workbench/quality-review.js',location.origin+'/')).href;
/* Quality review owns one shared model for the list, editor and three lanes. */
window.createQualityReview=({track,editor,list,actions,header,storageNamespace='workbench-quality-v1'})=>{
  const M=window.QualityModel,duration=40;
  const listTitles={'workbench-quality-v1':'预训练质检列表','workbench-posttraining-v1':'后训练质检列表','workbench-posttraining-review-v1':'后训练质检审核列表','workbench-rejection-v1':'驳回处理列表','workbench-secondary-review-v1':'二次审核列表'};
  list.setAttribute('title',listTitles[storageNamespace]||'质检列表');
  const isAudit=['workbench-posttraining-review-v1','workbench-rejection-v1','workbench-secondary-review-v1'].includes(storageNamespace);
  const isPretraining=storageNamespace==='workbench-quality-v1';
  const isRejection=storageNamespace==='workbench-rejection-v1';
  const isSecondary=storageNamespace==='workbench-secondary-review-v1';
  const fixedRanges=isSecondary||storageNamespace==='workbench-posttraining-review-v1';
  if(isAudit)editor.classList.add('quality-audit-editor');
  const time=value=>`${String(Math.floor(value/60)).padStart(2,'0')}:${(value%60).toFixed(1).padStart(4,'0')}`;
  const listTime=value=>{const tenths=Math.round(value*10),seconds=Math.floor(tenths/10);return `${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}${tenths%10?'.'+tenths%10:''}`;};
  const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const errorReasons=['片段范围错误','片段范围错位','动作开始边界偏早','动作开始边界偏晚','动作结束边界偏早','动作结束边界偏晚','描述与画面不一致'];
  const seeds=[
    [1,5,'mistake',[0],[],'动作开始边界偏早'],
    [4.5,8,'failure',[1],[3],'片段范围错位'],
    [9.4,10.8,'mistake',[2],[]],
    [12,20,'failure',[],[1]],
    [17,22.5,'mistake',[3],[]],
    [18,19.4,'mistake',isAudit?[0,1]:[],[]],
    [18.2,19,'failure',[],[2]],
    [18.4,19.2,'mistake',[1],[]]
  ];
  let items=seeds.map(([start,end,type,m,f,errorReason=''],i)=>({errorReason:isAudit?errorReason:'',id:`quality-${i+1}`,start,end,type,mistakes:m.map(i=>M.mistakes[i]),failures:f.map(i=>M.failures[i])}));
  const storageKey=`${storageNamespace}:${header.getAttribute('data-processing-id')}:${header.getAttribute('data-id')}`;
  try{const saved=JSON.parse(localStorage.getItem(storageKey));if(saved&&Array.isArray(saved.items)&&saved.items.every(x=>x&&typeof x.id==='string'&&Number.isFinite(x.start)&&Number.isFinite(x.end)&&x.start>=0&&x.end<=duration&&x.start<x.end&&['mistake','failure'].includes(x.type)&&Array.isArray(x.mistakes)&&Array.isArray(x.failures)&&x.mistakes.every(r=>M.mistakes.includes(r))&&x.failures.every(r=>M.failures.includes(r))))items=saved.items;}catch(_){}
  if(isSecondary){
    try{
      const own=JSON.parse(localStorage.getItem(storageKey)||'null');
      if(!own?.secondaryInitialized){
        const source=JSON.parse(localStorage.getItem(storageKey.replace(storageNamespace,'workbench-rejection-v1'))||'null');
        if(source?.items?.length)items=JSON.parse(JSON.stringify(source.items));
        items.forEach(item=>{item.errorReason='';item.secondaryInitialized=true;});
      }
    }catch(_){}
  }
  // Migrate the previous demo reasons once without resetting the saved annotations.
  const reasonMigrationKey=storageKey+':two-example-reasons-v1';
  try{
    if(!localStorage.getItem(reasonMigrationKey)){
      const legacyReasons={'quality-4':'动作结束边界偏早','quality-5':'描述与画面不一致','quality-8':'动作结束边界偏晚'};
      items.forEach(item=>{if(legacyReasons[item.id]===item.errorReason)item.errorReason='';});
      const saved=JSON.parse(localStorage.getItem(storageKey)||'null');
      if(saved&&Array.isArray(saved.items))localStorage.setItem(storageKey,JSON.stringify({...saved,items}));
      localStorage.setItem(reasonMigrationKey,'1');
    }
  }catch(_){}
  // Complete the old empty audit demo without overwriting reviewer changes.
  if(isAudit){
    const demo=items.find(item=>item.id==='quality-6');
    const base=demo?.auditOriginal;
    if(demo&&(!base||(base.mistakes.length===0&&base.failures.length===0))){
      if(demo.mistakes.length===0&&demo.failures.length===0){demo.mistakes=[M.mistakes[0],M.mistakes[1]];demo.type='mistake';}
      demo.auditOriginal={type:'mistake',mistakes:[M.mistakes[0],M.mistakes[1]],failures:[]};
    }
  }
  if(isAudit)items.forEach(item=>{
    const base=item.auditOriginal;
    if(!base||!['mistake','failure','passed'].includes(base.type)||!Array.isArray(base.mistakes)||!Array.isArray(base.failures))
      item.auditOriginal={type:item.type,mistakes:[...item.mistakes],failures:[...item.failures]};
  });
  if(isRejection||isSecondary)items.forEach(item=>{
    if(!item.auditReference)item.auditReference=JSON.parse(JSON.stringify(item.auditOriginal));
    if(!item.rejectionFeedbackSeeded){
      if(item.id==='quality-2'){item.mistakes=item.mistakes.filter(reason=>reason!==M.mistakes[1]);item.failures=[...new Set([...item.failures,M.failures[1]])];item.errorReason='片段范围错位';}
      if(item.id==='quality-6'){item.mistakes=item.mistakes.filter(reason=>reason!==M.mistakes[1]);item.failures=[M.failures[4]];item.type='failure';item.errorReason='描述与画面不一致';}
      if(item.id==='quality-8'){item.mistakes=[...new Set([...item.mistakes,M.mistakes[0]])];item.errorReason='动作结束边界偏晚';}
      item.rejectionFeedbackSeeded=true;
    }
    if(item.id==='quality-2'&&!item.rejectionOverflowSeeded){
      item.failures=[...new Set([...item.failures,M.failures[4],M.failures[5],M.failures[6]])];
      item.mistakes=[...new Set([...item.mistakes,M.mistakes[2],M.mistakes[3]])];
      item.rejectionOverflowSeeded=true;
    }
    if(isSecondary&&!item.secondaryReasonReset){item.errorReason='';item.secondaryReasonReset=true;}
  });
  if(editor.hasAttribute('data-overflow-demo')){
    const base=items[1]?.auditOriginal;
    if(base){base.failures=[...new Set([...base.failures,M.failures[1],M.failures[4]])];base.mistakes=[...new Set([...base.mistakes,M.mistakes[0]])];}
  }
  function syncAudit(item){if(isAudit)item.type=item.failures.length?'failure':'mistake';}
  const sharedReasonKey=`workbench-review-reasons:${header.getAttribute('data-processing-id')}:${header.getAttribute('data-id')}${isSecondary?':secondary-session':''}`;
  window.workbenchReviewReasons=window.workbenchReviewReasons||new Map();
  // Secondary-review demo reasons reset on reload and stay local to this view.
  let sharedReasons=isSecondary?Object.fromEntries(items.map(item=>[item.id,['quality-2','quality-4'].includes(item.id)?'动作开始边界偏早':''])):window.workbenchReviewReasons.get(sharedReasonKey);
  if(isSecondary)items.forEach(item=>{item.errorReasonConfirmed=false;});
  if(isAudit&&!sharedReasons){
    try{sharedReasons=JSON.parse(localStorage.getItem(sharedReasonKey)||'null');}catch(_){}
    if(!sharedReasons||typeof sharedReasons!=='object'||Array.isArray(sharedReasons))sharedReasons=Object.fromEntries(items.map(item=>[item.id,item.errorReason||'']));
    window.workbenchReviewReasons.set(sharedReasonKey,sharedReasons);
  }
  function syncSharedReasons(){
    if(isAudit)items.forEach(item=>{item.errorReason=String(sharedReasons[item.id]||'');});
  }
  syncSharedReasons();
  const hasErrorReason=item=>isAudit&&!!String(sharedReasons[item.id]||'').trim();
  function publishReason(item){
    if(!isAudit)return;
    item.errorReasonConfirmed=!!String(item.errorReason||'').trim();
    sharedReasons[item.id]=item.errorReason||'';
    if(!isSecondary)try{localStorage.setItem(sharedReasonKey,JSON.stringify(sharedReasons));}catch(_){}
    window.dispatchEvent(new CustomEvent('workbench-review-reasons-change',{detail:sharedReasonKey}));
  }
  window.addEventListener('workbench-review-reasons-change',event=>{if(isAudit&&event.detail===sharedReasonKey){syncSharedReasons();render();}});
  const initialLanes=M.lanes(items);items.forEach(item=>item.lane=initialLanes.get(item.id));
  let active=items[0]?.id,enabled=false;
  const ruler=track.querySelector('timeline-range-selector');
  if(fixedRanges){
    track.classList.add('quality-review-track--fixed-ranges');
    ruler.inert=true;
    track.querySelectorAll('timeline-controls [aria-label="添加"],timeline-controls [aria-label="清空"],timeline-controls [aria-label="拖动"]').forEach(button=>{button.hidden=true;button.disabled=true;button.style.display='none';});
    track.activateRangeAdjustment=()=>{};
  }
  ruler._format=percent=>time(percent*duration/100);
  track.querySelectorAll('.segmented-timeline__range-fragment,.segmented-timeline__selection-label').forEach(el=>el.remove());
  track.classList.add('quality-review-track');
  const lanes=document.createElement('div');lanes.className='quality-lanes';track.querySelector('.segmented-timeline__body').append(lanes);
  const footer=actions.querySelector('workbench-footer-actions');
  actions.querySelector('workbench-quality-conclusion').innerHTML='<div class="workbench-quality-conclusion"><label>质检结论</label><output data-conclusion></output></div>';
  footer.setVariant(isPretraining?'pretraining':isRejection?'rejection':isSecondary?'secondary-review':isAudit?'posttraining-review':'posttraining');
  const footerBar=footer.querySelector('footer');
  const reject=footer.querySelector('[data-action="reject"]');
  const submitButton=footer.querySelector('[data-action="submit"]');
  footerBar.classList.add('quality-mode-footer');
  if(storageNamespace==='workbench-posttraining-review-v1'){reject.disabled=true;reject.setAttribute('aria-disabled','true');}
  if(isSecondary){reject.classList.add('quality-reject-primary');submitButton.disabled=true;submitButton.setAttribute('aria-disabled','true');}

  const rejectDialog=document.createElement('workbench-confirm-dialog');rejectDialog.setAttribute('variant','reject');actions.append(rejectDialog);
  const releaseDialog=document.createElement('workbench-confirm-dialog');actions.append(releaseDialog);releaseDialog.querySelector('p').textContent='保存当前草稿并释放此任务？';
  function saveState(state,extra={}){
    try{localStorage.setItem(storageKey,JSON.stringify({items,secondaryInitialized:isSecondary,conclusion:M.conclusion(items),status:state,...extra}));return true;}
    catch(_){notify('浏览器存储不可用，未能保存，请保留当前页面。');return false;}
  }
  rejectDialog.addEventListener('confirm-dialog-confirm',e=>{e.stopPropagation();if(saveState('rejected',{rejectReason:e.detail.value}))notify('驳回信息已保存到当前浏览器（演示操作）。');});
  releaseDialog.addEventListener('confirm-dialog-confirm',e=>{e.stopPropagation();if(saveState('released')){notify('草稿和释放状态已保存到当前浏览器（演示操作）。');}});
  const summary=document.createElement('div');summary.className='quality-summary';actions.prepend(summary);
  const status=document.createElement('p');status.className='quality-feedback';status.setAttribute('role','status');actions.append(status);
  const notify=message=>{status.textContent=message;};
  const current=()=>items.find(x=>x.id===active);
  const label=item=>item.type==='failure'?'不合格':'失误';
  const reasons=item=>[...item.failures,...item.mistakes];
  const hasProblemFilter=isRejection||isSecondary||storageNamespace==='workbench-posttraining-review-v1';
  const previousProblemIds=new Set(items.filter(hasErrorReason).map(item=>item.id));
  let problemFilter='all';
  const matchesProblemFilter=item=>problemFilter==='all'||(problemFilter==='previous'?previousProblemIds.has(item.id):hasErrorReason(item));
  let selectedNeutral=null;
  function select(id){selectedNeutral=null;track.classList.remove('is-adjusting-range');active=id;render();const item=current();if(item){ruler.setRange(item.start/duration*100,item.end/duration*100);track.seek?.(item.start/duration*100);}}
  let draftType='mistake';
  function drawDraft(){
    lanes.querySelectorAll('.quality-draft').forEach(el=>el.remove());
    if(!track.classList.contains('is-adjusting-range')||ruler._end<=ruler._start)return;
    const draft={id:'draft-preview',start:ruler._start*duration/100,end:ruler._end*duration/100};
    const lane=M.lanes([...items,draft]).get(draft.id);
    const preview=document.createElement('span');
    preview.className='quality-fragment quality-draft '+draftType;
    preview.style.left=ruler._start+'%';preview.style.width=(ruler._end-ruler._start)+'%';
    lanes.children[lane].append(preview);
  }
  ruler.addEventListener('range-change',()=>{
    if(fixedRanges)return;
    if(selectedNeutral){ruler.setRange(selectedNeutral.start/duration*100,selectedNeutral.end/duration*100);return;}
    if(track.classList.contains('is-adjusting-range')){drawDraft();return;}
    const item=current();
    if(!item)return;
    const start=Number((ruler._start*duration/100).toFixed(1));
    const end=Number((ruler._end*duration/100).toFixed(1));
    if(end<=start)return;
    item.start=start;item.end=end;
    draw();
    editor.querySelector('[data-start]').textContent=listTime(start);
    editor.querySelector('[data-end]').textContent=listTime(end);
    editor.querySelector('[data-duration]').textContent=listTime(end-start);
  });
  function draw(){
    const assigned=M.lanes(items);
    // Paint shorter fragments last so overlapping long fragments never block them.
    lanes.innerHTML=[0,1,2].map(lane=>`<div class="quality-lane"><span>轨道 ${lane+1}</span>${items.filter(x=>assigned.get(x.id)===lane).sort((a,b)=>(b.end-b.start)-(a.end-a.start)||a.id.localeCompare(b.id)).map(x=>`<button type="button" class="quality-fragment ${x.type}${M.complete(x)?'':' incomplete'}${x.id===active?' selected':''}" data-id="${escape(x.id)}" style="left:${x.start/duration*100}%;width:${(x.end-x.start)/duration*100}%" aria-label="${escape(label(x)+' '+time(x.start)+'至'+time(x.end)+' '+(reasons(x).join('、')||'未选择原因'))}" aria-pressed="${x.id===active}" title="${escape(reasons(x).join('、')||'请选择原因')}"></button>`).join('')}</div>`).join('');
    if(isPretraining){
      // Show neutral intervals between reviewed fragments on the first lane.
      const intervals=items.filter(item=>assigned.get(item.id)===0).sort((a,b)=>a.start-b.start);
      const gaps=intervals.slice(1).map((item,index)=>item.start-intervals[index].end).filter(gap=>gap>0);
      const neutralDuration=gaps.length?Math.min(...gaps):1;
      let cursor=0;
      intervals.forEach(item=>{
        if(item.start>cursor){
          const neutral=document.createElement('button');
          neutral.type='button';
          neutral.className='quality-fragment quality-fragment--neutral';
          const neutralStart=Math.max(cursor,item.start-neutralDuration);
          neutral.dataset.neutralStart=neutralStart;
          neutral.dataset.neutralEnd=item.start;
          const selected=selectedNeutral?.start===neutralStart&&selectedNeutral?.end===item.start;
          neutral.classList.toggle('selected',selected);
          neutral.setAttribute('aria-pressed',String(selected));
          neutral.style.left=(neutralStart/duration*100)+'%';
          neutral.style.width=((item.start-neutralStart)/duration*100)+'%';
          neutral.setAttribute('aria-label','未标记片段 '+time(neutralStart)+'至'+time(item.start));
          lanes.firstElementChild.append(neutral);
        }
        cursor=Math.max(cursor,item.end);
      });
    }
    if(isAudit)lanes.querySelectorAll('.quality-fragment[data-id]').forEach(fragment=>{
      if(!hasErrorReason(items.find(item=>item.id===fragment.dataset.id)))return;
      const badge=document.createElement('span');badge.className='quality-audit-alert quality-audit-alert--timeline';badge.textContent='!';badge.title='错误原因：'+sharedReasons[fragment.dataset.id];badge.setAttribute('aria-label',badge.title);fragment.append(badge);
    });
    drawDraft();
    list.setReviewItems(items.map(x=>({...x,errorReason:isAudit?(sharedReasons[x.id]||''):'',time:`${listTime(x.start)}~${listTime(x.end)}`,duration:listTime(x.end-x.start),label:label(x),description:(x.unavailable?'无法标注 · ':'')+(reasons(x).join('、')||'请选择原因'),complete:M.complete(x)})),active);
    if(hasProblemFilter){
      const tabs=document.createElement('div');tabs.className='quality-problem-tabs';tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','问题片段筛选');
      tabs.innerHTML=[['all','全部'],['problems','仅看有问题'],...(isSecondary?[['previous','上次有问题']]:[])].map(([value,label])=>`<button type="button" role="tab" data-problem-filter="${value}" aria-selected="${problemFilter===value}">${label}</button>`).join('');
      list.querySelector('.workbench-flat-list__header').after(tabs);
      let visible=0;
      list.querySelectorAll('.quality-item').forEach(row=>{row.hidden=!matchesProblemFilter(items.find(item=>item.id===row.dataset.id));if(!row.hidden)visible++;});
      if(!visible){const empty=document.createElement('p');empty.className='quality-empty';empty.textContent='暂无有错误原因的片段';list.querySelector('.workbench-flat-list__body').append(empty);}
    }
    const failures=items.filter(x=>x.type==='failure').length;
    summary.textContent=`系统自动计算 · 失误 ${items.length-failures} · 不合格 ${failures}`;
    const output=actions.querySelector('[data-conclusion]');output.textContent=M.conclusion(items);output.className=failures?'failure':'passed';
    const submit=submitButton;
    const canReject=storageNamespace==='workbench-posttraining-review-v1'&&items.some(item=>item.errorReasonConfirmed&&String(item.errorReason||'').trim());
    const submitBlocked=canReject||items.some(x=>!M.complete(x))||isSecondary;
    submit.setAttribute('aria-disabled',String(submitBlocked));
    if(isSecondary||storageNamespace==='workbench-posttraining-review-v1'){
      submit.disabled=submitBlocked;
      submit.classList.toggle('text-button--primary',!submitBlocked);
      submit.classList.toggle('text-button--outline',submitBlocked);
    }
    if(storageNamespace==='workbench-posttraining-review-v1'){
      reject.disabled=!canReject;
      reject.setAttribute('aria-disabled',String(!canReject));
      reject.classList.toggle('quality-reject-primary',canReject);
    }
  }
  function neighbor(direction){
    const item=current();if(!item)return;
    const assigned=M.lanes(items),same=items.filter(x=>assigned.get(x.id)===assigned.get(item.id)).sort((a,b)=>a.start-b.start||a.end-b.end||a.id.localeCompare(b.id));
    return same[same.indexOf(item)+direction];
  }
  const reasonTags=item=>QualityFormControls.reasonTags(item,{isAudit,isRejection,isSecondary,M,escape,qualityReviewAssetRoot});
  function fitReasonTags(){
    editor.querySelectorAll('details .quality-reason-tags').forEach(row=>{
      row.querySelectorAll('.quality-reason-tag').forEach(tag=>tag.hidden=tag.classList.contains('quality-reason-more'));
    });
  }
  const tagResizeObserver=new ResizeObserver(fitReasonTags);
  tagResizeObserver.observe(editor);

  function render(){
    draw();const item=current();
    if(selectedNeutral){editor.innerHTML=QualityFormControls.automaticSegment(selectedNeutral);return;}
    if(!item){editor.innerHTML='<section class="card form-card quality-empty">已选择时间范围，点击时间轴加号添加片段，或点击已有片段进行编辑。</section>';return;}
    const index=items.indexOf(item);
    editor.innerHTML=`<section class="card form-card"><div class="form-row form-row--meta"><div class="segment-meta"><b class="segment-current segment-current--code">${String(index+1).padStart(2,'0')}</b><span>开始时间</span><b data-start>${listTime(item.start)}</b><span>结束时间</span><b data-end>${listTime(item.end)}</b><span>时长</span><b data-duration>${listTime(item.end-item.start)}</b></div><div class="segment-actions">${QualityFormControls.navigation({previous:index>0,next:index<items.length-1,left:!!neighbor(-1),right:!!neighbor(1)})}<button class="segment-action segment-action--danger" data-delete>删除 <kbd>⌘⌫</kbd></button></div></div><div class="form-row"><span class="field-label">片段类型</span>${QualityFormControls.typeSwitch(item.type)}<details class="quality-reasons"><summary class="input-like error-trigger">${reasonTags(item)}</summary><div class="quality-reason-popover error-popover">${(isAudit||item.type==='failure'?['failures','mistakes']:['mistakes']).map(key=>`<fieldset data-reason-section="${key}"><legend>${key==='failures'?'不合格原因':'失误原因'} <small>${key==='failures'||item.type==='mistake'?'必选':'选填'}</small></legend><div class="quality-reason-options">${M[key].map((reason,i)=>`<label class="error-option${item[key].includes(reason)?' is-selected':''}"><input type="checkbox" data-reason-group="${key}" value="${i}" ${item[key].includes(reason)?'checked':''}>${escape(reason)}<span aria-hidden="true">✓</span></label>`).join('')}</div></fieldset>`).join('')}${QualityFormControls.clearFooter('data-clear-reasons')}</div></details></div><div class="form-row form-row--error"><span class="field-label">错误原因</span><details class="quality-reasons quality-error-reasons"><summary class="input-like error-trigger${item.errorReason?'':' is-placeholder'}"><span>${escape(item.errorReason||'请选择错误原因')}</span><img src="${qualityReviewAssetRoot}icon-chevron.svg" alt="" aria-hidden="true"></summary><div class="quality-reason-popover error-popover"><div class="error-options" role="listbox" aria-label="错误原因">${errorReasons.map((reason,i)=>`<button type="button" class="error-option${item.errorReason===reason?' is-selected':''}" role="option" aria-selected="${item.errorReason===reason}" data-error-reason="${i}">${reason}<span>${item.errorReason===reason?'✓':''}</span></button>`).join('')}</div>${QualityFormControls.clearFooter('data-clear-error')}</div></details></div></section>`;
    if(isAudit){
      const card=editor.querySelector('.form-card'),meta=card.querySelector('.form-row--meta');
      const feedback=card.querySelector('.form-row:not(.form-row--meta)'),error=card.querySelector('.form-row--error');
      const base=item.auditOriginal||{type:item.type,mistakes:[],failures:[]};
      feedback.querySelector('.field-label').textContent='审核反馈';
      feedback.querySelector('.quality-types').outerHTML=`<span class="audit-status ${item.type}">${label(item)}</span>`;
      const columns=document.createElement('div');columns.className='quality-audit-columns';
      columns.innerHTML=`<div class="quality-audit-original"><div class="audit-original-heading"><span class="field-label">质检结果</span> <span class="audit-status ${base.type}">${label(base)}</span></div><div class="audit-original-tags input-like audit-disabled-input" role="textbox" aria-label="质检原因" aria-disabled="true">${reasons(base).map(reason=>QualityFormControls.tag(reason)).join('')||'未选择原因'}</div></div><div class="quality-audit-feedback"></div>`;
      if(isRejection){
        const heading=columns.querySelector('.audit-original-heading');
        heading.querySelector('.audit-status').outerHTML=QualityFormControls.typeSwitch(base.type,true);
        columns.querySelector('.audit-original-tags').outerHTML=`<details class="quality-reasons audit-original-select"><summary class="input-like error-trigger"><span class="quality-reason-tags">${reasons(base).map(reason=>QualityFormControls.tag(reason)).join('')||'请选择原因'}${reasons(base).length?QualityFormControls.clearAll().replace('data-clear-reasons','data-clear-original-reasons'):''}</span><img src="${qualityReviewAssetRoot}icon-chevron.svg" alt=""></summary><div class="quality-reason-popover error-popover">${['failures','mistakes'].map(group=>`<fieldset data-reason-section="${group}"><legend>${group==='failures'?'不合格原因':'失误原因'}</legend>${M[group].map((reason,index)=>`<label class="error-option${base[group].includes(reason)?' is-selected':''}"><input type="checkbox" data-original-group="${group}" value="${index}" ${base[group].includes(reason)?'checked':''}>${escape(reason)}<span aria-hidden="true">✓</span></label>`).join('')}</fieldset>`).join('')}${QualityFormControls.clearFooter('data-clear-original-reasons')}</div></details>`;
      }
      columns.lastElementChild.append(feedback,error);card.append(columns);
      if(isRejection){
        const readonly=columns.lastElementChild;
        readonly.classList.add('quality-audit-feedback--disabled');
        readonly.querySelectorAll('details').forEach(details=>{
          const summary=details.querySelector('summary');
          const display=document.createElement('div');display.className=summary.className+' audit-disabled-input';
          display.setAttribute('aria-disabled','true');
          display.setAttribute('role','textbox');
          display.setAttribute('aria-label',details.classList.contains('quality-error-reasons')?'错误原因':'审核反馈原因');
          display.innerHTML=summary.innerHTML;
          display.querySelectorAll('button,img,.quality-reason-more').forEach(control=>control.remove());
          if(display.querySelector('.quality-reason-tags'))display.classList.add('audit-disabled-tags');
          details.replaceWith(display);
        });
      }
      const legend=document.createElement('span');legend.className='quality-audit-legend';legend.tabIndex=0;legend.innerHTML=QualityFormControls.legend();
      meta.querySelector('.segment-actions').prepend(legend);
      if(isSecondary&&hasErrorReason(item)){const accept=document.createElement('button');accept.type='button';accept.className='segment-action segment-action--navigate';accept.dataset.acceptOriginal='';accept.textContent='接受';accept.title='接受左侧质检结果';legend.after(accept);}

      meta.querySelector('[data-delete]').remove();
    }
    fitReasonTags();
  }
  lanes.addEventListener('click',e=>{const neutral=e.target.closest('[data-neutral-start]');if(neutral){selectedNeutral={start:Number(neutral.dataset.neutralStart),end:Number(neutral.dataset.neutralEnd)};active=null;track.classList.remove('is-adjusting-range');ruler.setRange(selectedNeutral.start/duration*100,selectedNeutral.end/duration*100);track.seek?.(selectedNeutral.start/duration*100);render();return;}const id=e.target.closest('[data-id]')?.dataset.id;if(id)select(id);});
  list.addEventListener('click',e=>{const filter=e.target.closest('[data-problem-filter]');if(filter){problemFilter=filter.dataset.problemFilter;if(!items.some(item=>item.id===active&&matchesProblemFilter(item)))select(items.find(matchesProblemFilter)?.id);else draw();list.querySelector(`[data-problem-filter="${problemFilter}"]`)?.focus();return;}const id=e.target.closest('[data-id]')?.dataset.id;if(id)select(id);});
  // Close the other dropdown before the clicked summary opens its own panel.
  editor.addEventListener('click',e=>{
    if(editor.hasAttribute('data-expanded-preview'))return;
    const summary=e.target.closest('summary');
    if(!summary||e.target.closest('button'))return;
    const currentDetails=summary.parentElement;
    editor.querySelectorAll('details[open]').forEach(detail=>{
      if(detail!==currentDetails)detail.open=false;
    });
  });
  editor.addEventListener('toggle',e=>{
    if(editor.hasAttribute('data-expanded-preview')||!e.target.matches('details[open]'))return;
    editor.querySelectorAll('details[open]').forEach(detail=>{
      if(detail!==e.target)detail.open=false;
    });
  },true);
  editor.addEventListener('click',e=>{const button=e.target.closest('button');if(!button)return;const item=current();if(!item)return;if(isSecondary&&button.hasAttribute('data-accept-original')){const base=item.auditOriginal;item.mistakes=[...base.mistakes];item.failures=[...base.failures];item.type=base.type==='failure'?'failure':'mistake';item.secondaryAccepted=true;item.errorReason='';publishReason(item);render();return;}if(isRejection&&button.hasAttribute('data-clear-original-reasons')){e.preventDefault();e.stopPropagation();item.auditOriginal.mistakes=[];item.auditOriginal.failures=[];render();return;}if(isRejection&&button.dataset.originalType){item.auditOriginal.type=button.dataset.originalType;render();return;}if(button.dataset.restoreGroup){e.preventDefault();e.stopPropagation();const group=button.dataset.restoreGroup;item[group]=[...new Set([...item[group],M[group][Number(button.dataset.restoreReason)]])];syncAudit(item);render();return;}if(button.dataset.removeGroup){e.preventDefault();e.stopPropagation();const group=button.dataset.removeGroup;item[group]=item[group].filter(reason=>reason!==M[group][Number(button.dataset.removeReason)]);syncAudit(item);render();return;}if(button.hasAttribute('data-error-reason')){item.errorReason=errorReasons[Number(button.dataset.errorReason)];publishReason(item);render();return;}if(button.hasAttribute('data-clear-reasons')){e.preventDefault();e.stopPropagation();item.mistakes=[];item.failures=[];syncAudit(item);render();return;}if(button.hasAttribute('data-clear-error')){item.errorReason='';publishReason(item);render();return;}if(button.dataset.laneNav){const next=neighbor(Number(button.dataset.laneNav));if(next)select(next.id);return;}if(button.dataset.type){M.changeType(item,button.dataset.type);render();}if(button.hasAttribute('data-delete')){const i=items.indexOf(item);items=items.filter(x=>x!==item);select(items[Math.min(i,items.length-1)]?.id);}if(button.dataset.nav)select(items[items.indexOf(item)+Number(button.dataset.nav)]?.id);});
  editor.addEventListener('change',e=>{
    const item=current();if(!item)return;const group=e.target.dataset.reasonGroup;
    if(isRejection&&e.target.matches('[data-original-type],[data-original-group]')){
      const base=item.auditOriginal;
      if(e.target.hasAttribute('data-original-type'))base.type=e.target.value;
      else{const key=e.target.dataset.originalGroup,reason=M[key][Number(e.target.value)];base[key]=e.target.checked?[...new Set([...base[key],reason])]:base[key].filter(value=>value!==reason);}
      const reopen=e.target.hasAttribute('data-original-group');render();if(reopen)editor.querySelector('.audit-original-select').open=true;return;
    }

    if(group){e.target.closest('label').classList.toggle('is-selected',e.target.checked);const reason=M[group][Number(e.target.value)];item[group]=e.target.checked?[...new Set([...item[group],reason])]:item[group].filter(x=>x!==reason);if(isAudit){syncAudit(item);render();editor.querySelector('.quality-audit-feedback details').open=true;return;}draw();editor.querySelector('summary').innerHTML=reasonTags(item);fitReasonTags();}
    if(e.target.dataset.time){if(fixedRanges)return;const key=e.target.dataset.time,value=Number(e.target.value);if(e.target.value===''||!Number.isFinite(value)||value<0||value>duration||(key==='start'?value>=item.end:value<=item.start)){notify('开始时间必须早于结束时间，且范围在 0～40 秒内。');render();return;}item[key]=value;select(item.id);}
  });
  // Shortcut-created ranges are drafts; otherwise range edits update the selected segment.
  function add(){if(fixedRanges)return;const start=ruler._start*duration/100,end=ruler._end*duration/100;if(end<=start)return;const item={id:`quality-${Date.now()}-${Math.random().toString(36).slice(2)}`,start:Number(start.toFixed(1)),end:Number(end.toFixed(1)),type:track.classList.contains('is-adjusting-range')?draftType:'mistake',mistakes:[],failures:[]};track.classList.remove('is-adjusting-range');item.lane=M.lanes([...items,item]).get(item.id);items.push(item);select(item.id);}
  ruler.addEventListener('range-commit',()=>{if(track.classList.contains('is-adjusting-range'))add();});
  const addButton=track.querySelector('[aria-label="添加"]');addButton?.addEventListener('click',add);if(addButton)addButton.dataset.tooltip='添加问题片段';
  track.querySelector('[aria-label="清空"]')?.addEventListener('click',()=>editor.querySelector('[data-delete]')?.click());
  // Keep native confirmation UI, but prevent it opening before required reasons are complete.
  footer.addEventListener('click',e=>{if(e.target.closest('[data-action="submit"]')&&items.some(x=>!M.complete(x))){e.preventDefault();e.stopImmediatePropagation();select(items.find(x=>!M.complete(x)).id);notify('请补全所有片段的必选原因后再提交；当前内容可以保存为草稿。');}},true);
  footer.addEventListener('workbench-action',e=>{
    const action=e.detail.action;if(action==='reject'){rejectDialog.show();return;}if(action==='release'){releaseDialog.show();return;}if(!['save','submit'].includes(action))return;
    if(action==='submit'&&footer.querySelector('[data-action="submit"]').disabled)return;
    if(action==='submit'&&(items.some(x=>!M.complete(x))||isSecondary)){notify('原因未填写完整，无法提交。');return;}
    if(saveState(action==='save'?'draft':'submitted'))notify(action==='save'?'草稿已保存到当前浏览器。':'质检结果已保存到当前浏览器（演示提交）。');
  });
  document.addEventListener('keydown',e=>{
    if(!enabled||editor.hidden||!(e.metaKey||e.ctrlKey)||e.target.closest('input,textarea,select,[contenteditable="true"]'))return;
    if(e.ctrlKey&&!e.metaKey&&!e.altKey&&!e.shiftKey&&['a','s'].includes(e.key.toLowerCase())){
      e.preventDefault();e.stopImmediatePropagation();
      editor.querySelector(e.key.toLowerCase()==='a'?'[data-type=mistake]':'[data-type=failure]')?.click();
      if(fixedRanges)return;
      draftType=e.key.toLowerCase()==='a'?'mistake':'failure';
      track.activateRangeAdjustment?.();drawDraft();
      return;
    }
    const selector={ArrowUp:'[data-nav="-1"]',ArrowDown:'[data-nav="1"]',ArrowLeft:'[data-lane-nav="-1"]',ArrowRight:'[data-lane-nav="1"]',Backspace:'[data-delete]'}[e.key];
    if(!selector)return;e.preventDefault();e.stopImmediatePropagation();editor.querySelector(selector)?.click();
  },true);
  document.addEventListener('click',e=>{if(!editor.hasAttribute('data-expanded-preview')&&!editor.contains(e.target))editor.querySelectorAll('details').forEach(detail=>detail.removeAttribute('open'));});
  render();
  return {activate(){enabled=true;select(active);},deactivate(){enabled=false;},select(index){select(items[index]?.id);}};
};
