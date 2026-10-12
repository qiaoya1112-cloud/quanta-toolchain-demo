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
    if(index===1)reasons=[...new Set([...reasons,...previous.added])];
    const start=index===2?Math.min(item.end-.1,item.start+.3):item.start;
    return {id:item.id,start,end:item.end,track:item.track,order:item.order,conclusion:item.conclusion,
      originalMistakeReasons:reasons.filter(id=>id.startsWith('M')),originalRejectedReasons:reasons.filter(id=>id.startsWith('U')),
      previousFeedback:previous,reviewNote:'',reviewErrorReason:'',audit:{removed:[],added:[]}};
  });
  const chip=(id,type)=>`<span class="ptqw-chip is-${type}">${esc(names[id]||id)}<small>${type==='error'?'错误项':'遗漏项'}</small></span>`;
  function decorateWorkspace(host,item){
    if(!item)return;
    const editor=host.querySelector('.ptqr-editor'),review=host.querySelector('.ptqr-review-row');
    const current=document.createElement('div');current.className='ptqs-current';
    const heading=document.createElement('div');heading.className='ptqs-current-heading';
    heading.innerHTML='<span>本次质检结果</span>';
    const conclusionEditor=review.querySelector('.ptqr-conclusion-review')||review.querySelector('.ptqr-conclusion');
    heading.append(conclusionEditor);
    current.append(heading,review.querySelector('.ptqr-description-box'));
    const previous=item.previousFeedback,removed=previous.original.filter(id=>![...item.originalRejectedReasons,...item.originalMistakeReasons].includes(id)),added=[...item.originalRejectedReasons,...item.originalMistakeReasons].filter(id=>!previous.original.includes(id));
    const delta=[removed.length?`已删除：${removed.map(id=>names[id]||id).join('、')}`:'',added.length?`已新增：${added.map(id=>names[id]||id).join('、')}`:'',previous.start!==item.start||previous.end!==item.end?`时间：${time(previous.start)}–${time(previous.end)} → ${time(item.start)}–${time(item.end)}`:''].filter(Boolean).join('；')||'描述及时间未修改';
    const change=document.createElement('span');change.className='ptqs-change';change.textContent='本次修改';change.dataset.fullDescription=delta;heading.append(change);
    const feedback=document.createElement('div');feedback.className='ptqs-previous';
    feedback.innerHTML=`<div class="ptqw-feedback-heading"><span class="ptqw-feedback-title">上次审核反馈</span><span class="ptqr-suggested-result">建议 ${esc({pass:'合格',mistake:'失误',rejected:'不合格'}[previous.suggestedConclusion||previous.conclusion])}</span><div class="ptqw-feedback-chips">${previous.removed.map(id=>chip(id,'error')).join('')}${previous.added.map(id=>chip(id,'omitted')).join('')}${!previous.removed.length&&!previous.added.length?'<span class="ptqs-muted">无描述问题</span>':''}</div></div><div class="ptqs-feedback-row"><span class="ptqs-field"><small>错误原因</small><span class="ptqw-reason-value" data-full-description="${esc(previous.reason||'无')}">${esc(previous.reason||'无')}</span></span>${previous.note?`<span class="ptqs-field"><small>补充说明</small><span class="ptqw-note-text" data-full-description="${esc(previous.note)}">${esc(previous.note)}</span></span>`:''}</div>`;
    const compare=document.createElement('div');compare.className='ptqs-compare';compare.append(current,feedback);review.replaceWith(compare);
    editor.querySelector('.ptqr-error-row>span').textContent='本次错误原因';
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
    const previousButton=document.createElement('button');previousButton.type='button';previousButton.dataset.action='filter-previous';previousButton.textContent=`上次有问题 ${state.segments.filter(hasPreviousIssue).length}`;
    previousButton.classList.toggle('is-active',state.filter==='previous');
    previousButton.addEventListener('click',()=>{state.filter='previous';api.select(state.selectedId,false);});
    host.querySelector('.ptqr-list-tools>div').append(previousButton);
    for(const row of host.querySelectorAll('.ptqr-list-item')){
      const item=state.segments.find(item=>item.id===row.dataset.segmentId);
      if(state.filter==='previous'&&!hasPreviousIssue(item))row.remove();
    }
  }
  const api=window.createPostTrainingQualityReview({tagBase:'post-training-quality-second-review',eventBase:'post-quality-second-review',domPrefix:'ptqs',segments,restoreDraft:true,decorateWorkspace,decorateSidebar});
  window.PostTrainingQualitySecondReviewDemo=api;
  window.installQualityReviewNote?.({api,hostTag:'post-training-quality-second-review-workspace',eventName:'post-quality-second-review-state-change',observeRenders:true});
})();
