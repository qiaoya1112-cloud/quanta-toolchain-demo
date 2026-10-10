(() => {
  const clone = value => JSON.parse(JSON.stringify(value));
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const source = clone(window.PostTrainingQualityReviewDemo.state.segments);
  // A fixed returned example; review suggestions never silently change the editable result.
  source.forEach((item, index) => {
    item.audit = {removed:[], added:[]};
    item.reviewErrorReason = '';
    item.reviewNote = index===0?'请重点核对右臂视角：该片段夹爪仍位于画面内，但手部没有持续握住夹爪。请移除错误描述，并补充实际发生的身体辅助动作。':index===2?'开始边界应后移至动作真正开始的位置。请结合三个视角逐帧检查，避免将准备动作算入片段。\n修改后请重新播放该区间，检查起止时间与描述是否一致。':'';
    if(index === 0){item.audit={removed:['M02'],added:['M03']};item.reviewErrorReason='描述与画面不一致';}
    if(index === 1){item.audit={removed:[item.originalRejectedReasons[0]],added:['U02']};item.reviewErrorReason='描述与画面不一致';}
    if(index === 2)item.reviewErrorReason='动作开始边界偏早';
  });
  const segments = source.map(item => ({...item,
    mistakeReasons:clone(item.originalMistakeReasons),rejectedReasons:clone(item.originalRejectedReasons),
    feedback:{original:[...item.originalRejectedReasons,...item.originalMistakeReasons],removed:clone(item.audit.removed),added:clone(item.audit.added),reason:item.reviewErrorReason,note:item.reviewNote}
  }));
  const hasIssue = item => Boolean(item.feedback && (item.feedback.removed.length || item.feedback.added.length || item.feedback.reason));
  const ui = {filter:'all', feedbackOpen:true};
  let api;
  const name = id => ({M01:'夹爪超出画面',M02:'手部脱离夹爪',M03:'其他身体部位辅助',M04:'无意义动作或假动作',U01:'视频损坏或相机卡死',U02:'采集时长不足',U03:'画面全程完全遮挡',U04:'设备穿戴不规范'}[id] || id);
  function decorateWorkspace(host, item, state){
    const feedback=item.feedback;
    host.querySelector('.ptq-editor-lower')?.remove();
    const notice=document.createElement('div');notice.className='ptqw-status';
    notice.textContent=state.submitted?'已重新提交审核 · 当前结果只读':'已驳回，请根据审核反馈修改';
    host.querySelector('.ptq-editor').prepend(notice);
    if(!feedback)return;
    const details=document.createElement('div');details.className='ptqw-feedback';
    const chip=(id,status)=>`<span class="ptqw-chip is-${status}">${esc(name(id))}${status==='error'?'<del>错误项</del>':status==='omitted'?'<small>遗漏项</small>':''}</span>`;
    details.innerHTML=`<summary>审核反馈 <small>上次驳回意见 · 只读</small></summary><div class="ptqw-feedback-chips">${feedback.removed.map(id=>chip(id,'error')).join('')}${feedback.added.map(id=>chip(id,'omitted')).join('')}</div><div class="ptqw-error-reason">错误原因：${esc(feedback.reason||'无')}</div>`;
    const feedbackRow=document.createElement('div');feedbackRow.className='ptqw-feedback-row';
    const reason=details.querySelector('.ptqw-error-reason');
    reason.replaceChildren();
    const reasonLabel=document.createElement('span');reasonLabel.textContent='错误原因';
    const reasonValue=document.createElement('span');reasonValue.className='ptqw-reason-value';reasonValue.textContent=feedback.reason||'无';
    reason.append(reasonLabel,reasonValue);feedbackRow.append(reason);details.append(feedbackRow);
    if(feedback.note){
      const note=document.createElement('div');note.className='ptqw-feedback-note';
      const label=document.createElement('span');label.textContent='补充说明';
      const text=document.createElement('div');text.className='ptqw-note-text';text.textContent=feedback.note;
      text.dataset.fullDescription=feedback.note;
      note.append(label,text);feedbackRow.append(note);
    }
    const compare=document.createElement('div');compare.className='ptqw-compare';
    const current=document.createElement('div');current.className='ptqw-current';
    const title=document.createElement('div');title.className='ptqw-current-title';title.textContent='当前质检结果';
    const fields=host.querySelector('.ptq-editor-fields-row');
    const heading=document.createElement('div');heading.className='ptqw-current-heading';
    heading.append(title,fields.querySelector('.ptq-conclusion-switch'));
    fields.querySelector('.ptq-reason-label')?.remove();
    const feedbackTitle=document.createElement('span');feedbackTitle.className='ptqw-feedback-title';feedbackTitle.textContent='审核反馈';
    details.querySelector('summary').remove();
    const feedbackHeading=document.createElement('div');feedbackHeading.className='ptqw-feedback-heading';
    feedbackHeading.append(feedbackTitle,details.querySelector('.ptqw-feedback-chips'));
    details.prepend(feedbackHeading);
    current.append(heading,fields);compare.append(current,details);
    host.querySelector('.ptq-editor').append(compare);
  }
  function decorateSidebar(host,state){
    host.querySelector('[data-action="reject"]')?.remove();
    host.querySelector('.ptq-sidebar>header b').textContent='质检列表';
    const filters=document.createElement('div');filters.className='ptqr-list-tools';
    const issueCount=state.segments.filter(hasIssue).length;
    filters.innerHTML=`<div><button type="button" data-rework-filter="all" class="${ui.filter==='all'?'is-active':''}">全部 ${state.segments.length}</button><button type="button" data-rework-filter="issues" class="${ui.filter==='issues'?'is-active':''}">仅看有问题 ${issueCount}</button></div>`;
    filters.addEventListener('click',event=>{const value=event.target.closest('[data-rework-filter]')?.dataset.reworkFilter;if(value){ui.filter=value;host.render();}});
    host.querySelector('.ptq-sidebar>header').after(filters);
    host.querySelectorAll('.ptq-list-item').forEach(row=>{
      const item=state.segments.find(item=>item.id===row.dataset.segmentId),f=item.feedback;
      row.hidden=ui.filter==='issues'&&!hasIssue(item);
      if(!f)return;
      const feedback=document.createElement('span');feedback.className='ptqw-list-feedback';
      feedback.innerHTML=`<span>审核情况：错误项 ${f.removed.length||'-'}，遗漏项 ${f.added.length||'-'}</span><span>错误原因：${esc(f.reason||'-')}</span>`;
      row.querySelector('.ptq-list-main').append(feedback);
      if(hasIssue(item)){const badge=document.createElement('span');badge.className='ptqr-issue-badge';badge.textContent='!';badge.setAttribute('aria-label','上次审核有问题');row.append(badge);}
    });
    if(ui.filter==='issues'&&!issueCount){const empty=document.createElement('div');empty.className='ptq-list-empty';empty.textContent='暂无审核问题';host.querySelector('.ptq-list').append(empty);}
    host.querySelector('[data-action="submit"]').textContent=state.submitted?'已提交':'提交';
    host.querySelector('#ptqwSubmitDialog h2').textContent='确认重新提交审核';
    host.querySelector('#ptqwSubmitDialog small').textContent='将保存当前修改结果并重新交给审核员复核；上次审核意见保留。';
  }
  function decorateTimeline(host,state){
    host.querySelectorAll('.ptq-block').forEach(block=>{
      const item=state.segments.find(item=>item.id===block.dataset.segmentId);
      if(!hasIssue(item))return;
      const badge=document.createElement('span');badge.className='ptqw-track-issue';
      badge.textContent='!';badge.setAttribute('aria-hidden','true');block.append(badge);
      block.title+=' · 上次审核有问题';block.setAttribute('aria-label',block.title);
    });
  }
  api=window.createPostTrainingQualityWorkspace({trainingType:'post-rework',domPrefix:'ptqw',segments,selectedId:segments.find(hasIssue)?.id,decorateWorkspace,decorateSidebar,decorateTimeline});
  window.PostTrainingQualityReworkDemo=api;
})();
