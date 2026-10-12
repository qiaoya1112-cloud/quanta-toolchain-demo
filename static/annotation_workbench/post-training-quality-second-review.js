(() => {
  const clone=value=>JSON.parse(JSON.stringify(value));
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const names={M01:'夹爪超出画面',M02:'手部脱离夹爪',M03:'其他身体部位辅助',M04:'无意义动作或假动作',U01:'视频损坏或相机卡死',U02:'采集时长不足',U03:'画面全程完全遮挡',U04:'设备穿戴不规范'};
  const time=value=>`00:${Number(value).toFixed(1).padStart(4,'0')}`;
  // Fixed resubmission examples: complete correction, partial correction and a time correction.
  // Review evidence and the submitted revision remain immutable during the second audit.
  const segments=clone(window.PostTrainingQualityReworkDemo.state.segments).map((item,index)=>{
    const previous=clone(item.feedback);
    previous.start=item.start;previous.end=item.end;previous.conclusion=item.conclusion;
    let reasons=[...previous.original];
    if(index===0)reasons=[...reasons.filter(id=>!previous.removed.includes(id)),...previous.added];
    if(index===1){previous.added=['U04'];reasons=[...new Set([...reasons,'M04'])];}
    const start=index===2?Math.min(item.end-.1,item.start+.3):item.start;
    const expected=[...new Set(previous.original.filter(id=>!previous.removed.includes(id)).concat(previous.added))];
    return {id:item.id,start,end:item.end,track:item.track,order:item.order,conclusion:item.conclusion,
      originalMistakeReasons:reasons.filter(id=>id.startsWith('M')),originalRejectedReasons:reasons.filter(id=>id.startsWith('U')),
      previousFeedback:previous,reviewNote:'',reviewErrorReason:'',audit:{removed:reasons.filter(id=>!expected.includes(id)),added:expected.filter(id=>!reasons.includes(id))}};
  });
  function decorateWorkspace(host,item,state){
    if(!item)return;
    const editor=host.querySelector('.ptqr-editor'),review=host.querySelector('.ptqr-review-row');
    if(!review)return;
    const currentPanel=document.createElement('div');currentPanel.className='ptqs-current';
    const heading=document.createElement('div');heading.className='ptqs-current-heading';
    heading.innerHTML='<span>质检结果</span>';
    const conclusionEditor=review.querySelector('.ptqr-conclusion-review')||review.querySelector('.ptqr-conclusion');
    conclusionEditor.innerHTML=`<output class="ptqr-feedback-conclusion is-${item.conclusion}">${esc({pass:'合格',mistake:'失误',rejected:'不合格'}[item.conclusion])}</output>`;heading.append(conclusionEditor);
    const previous=item.previousFeedback,baseline=[...previous.original.filter(id=>!previous.removed.includes(id)),...previous.added],currentIds=[...item.originalRejectedReasons,...item.originalMistakeReasons],removed=baseline.filter(id=>!currentIds.includes(id)),added=currentIds.filter(id=>!baseline.includes(id));
    // Current QC and previous feedback are immutable snapshots; reviewer edits live in audit.
    const qualityDescriptions=document.createElement('div');qualityDescriptions.className='ptqr-description-box';qualityDescriptions.innerHTML=currentIds.map(id=>`<span class="ptqr-chip is-correct"><span>${esc(names[id]||id)}</span></span>`).join('')||'<span class="ptqr-empty">质检员未选择描述</span>';
    currentPanel.append(heading,qualityDescriptions);
    const delta=[removed.length?`已删除：${removed.map(id=>names[id]||id).join('、')}`:'',added.length?`已新增：${added.map(id=>names[id]||id).join('、')}`:'',previous.start!==item.start||previous.end!==item.end?`时间：${time(previous.start)}–${time(previous.end)} → ${time(item.start)}–${time(item.end)}`:''].filter(Boolean).join('；')||'描述及时间未修改';
    const change=document.createElement('span');change.className='ptqs-change';change.textContent='本次修改';change.dataset.fullDescription=delta;heading.append(change);
    const feedback=document.createElement('div');feedback.className='ptqs-previous';
    const displayed=currentIds.filter(id=>!item.audit.removed.includes(id)).concat(item.audit.added),comparison=currentIds;
    // The comparison is always against the last accepted audit feedback:
    // removed QC descriptions are error items (purple), newly added ones are omissions (blue).
    const activeRemoved=item.audit.removed;
    const activeAdded=item.audit.added;
    item.reviewDiff={removed:[...activeRemoved],added:[...activeAdded]};
    const feedbackChip=(id,type)=>{
      const action=type==='error'?'restore-original':type==='correct'?'remove-original':'remove-omission';
      const icon=type==='correct'?'×':'↶';
      const label=type==='correct'?'去掉此项，记为错误项':type==='error'?'撤销错误项':'撤销遗漏项';
      return `<span class="ptqr-chip is-${type}"><span>${esc(names[id]||id)}</span>${type==='error'?'<del>错误项</del>':type==='omitted'?'<small>遗漏项</small>':''}<button type="button" class="ptqr-chip-action" data-action="${action}" data-reason-id="${esc(id)}" ${state.submitted?'disabled':''} aria-label="${label}：${esc(names[id]||id)}" title="${label}"><span aria-hidden="true">${icon}</span></button></span>`;
    };
    const diffChips=[...displayed.filter(id=>comparison.includes(id)).map(id=>feedbackChip(id,'correct')),...activeRemoved.map(id=>feedbackChip(id,'error')),...activeAdded.map(id=>feedbackChip(id,'omitted'))].join('');
    const feedbackConclusionKey=displayed.some(id=>id.startsWith('U'))?'rejected':displayed.some(id=>id.startsWith('M'))?'mistake':'pass';
    const feedbackConclusion={pass:'合格',mistake:'失误',rejected:'不合格'}[feedbackConclusionKey];
    feedback.innerHTML=`<div class="ptqw-feedback-heading"><span class="ptqw-feedback-title">审核反馈</span><span class="ptqr-feedback-conclusion is-${feedbackConclusionKey}">${feedbackConclusion}</span><div class="ptqw-feedback-chips">${diffChips||'<span class="ptqs-muted">无描述</span>'}</div></div>`;
    if(activeRemoved.length||activeAdded.length){const accept=document.createElement('button');accept.type='button';accept.className='ptqs-accept';accept.textContent='接受';accept.disabled=state.submitted;accept.addEventListener('click',()=>{item.acceptedBaseline=[...currentIds];item.reviewErrorReason='';item.audit.removed=[];item.audit.added=[];state.dirty=true;api.select(item.id,false);});host.querySelector('.ptqr-meta .segment-actions').prepend(accept);}
    const compare=document.createElement('div');compare.className='ptqs-compare';compare.append(currentPanel,feedback);review.replaceWith(compare);
    const errorRow=editor.querySelector('.ptqr-error-row');errorRow.querySelector(':scope>span').textContent='错误原因';feedback.append(errorRow);
    feedback.querySelector('.ptqs-feedback-row')?.remove();
    const add=review.querySelector('.ptqr-add');feedback.querySelector('.ptqw-feedback-heading').append(add);
    if(host.menuOpen)requestAnimationFrame(()=>{
      const trigger=host.querySelector('.ptqr-add>button'),menu=host.querySelector('.ptqr-add-menu');
      if(!trigger||!menu)return;const rect=trigger.getBoundingClientRect();
      menu.style.left=`${Math.max(8,Math.min(innerWidth-menu.offsetWidth-8,rect.right-menu.offsetWidth))}px`;
      menu.style.top=`${Math.max(8,rect.top-menu.offsetHeight-4)}px`;
    });
  }
  function decorateSidebar(host,state){
    host.querySelector('.ptqr-sidebar>header b').textContent='二次审核列表';
    const dialog=host.querySelector('#ptqsSubmitDialog');
    dialog.querySelector('[data-action="confirm-submit"]').textContent='确认';
    const hasPreviousIssue=item=>item.previousFeedback.removed.length||item.previousFeedback.added.length||item.previousFeedback.reason||item.previousFeedback.suggestedConclusion!==(item.previousFeedback.originalConclusion||item.previousFeedback.conclusion);
    const previousButton=document.createElement('button');previousButton.type='button';previousButton.dataset.action='filter-previous';previousButton.textContent='上次有问题';
    previousButton.classList.toggle('is-active',state.filter==='previous');
    previousButton.addEventListener('click',()=>{state.filter='previous';api.select(state.selectedId,false);});
    host.querySelector('.ptqr-list-tools>div').append(previousButton);
    for(const row of host.querySelectorAll('.ptqr-list-item')){
      const item=state.segments.find(item=>item.id===row.dataset.segmentId);
      if(state.filter==='previous'&&!hasPreviousIssue(item))row.remove();
    }
  }
  const api=window.createPostTrainingQualityReview({tagBase:'post-training-quality-second-review',eventBase:'post-quality-second-review',domPrefix:'ptqs',segments,storageVersion:'v2',restoreDraft:true,decorateWorkspace,decorateSidebar});
  window.PostTrainingQualitySecondReviewDemo=api;
  // Open on a revised sample so the second-review action is immediately discoverable.
  const revised=segments.find(item=>item.previousFeedback&&(
    item.previousFeedback.original.filter(id=>!item.previousFeedback.removed.includes(id)).concat(item.previousFeedback.added).some(id=>![...item.originalRejectedReasons,...item.originalMistakeReasons].includes(id)) ||
    [...item.originalRejectedReasons,...item.originalMistakeReasons].some(id=>!item.previousFeedback.original.filter(x=>!item.previousFeedback.removed.includes(x)).concat(item.previousFeedback.added).includes(id))
  ));
  if(revised)api.select(revised.id,false);
})();
