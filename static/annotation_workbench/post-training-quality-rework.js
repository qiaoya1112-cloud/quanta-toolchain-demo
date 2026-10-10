(() => {
  const clone = value => JSON.parse(JSON.stringify(value));
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const source = clone(window.PostTrainingQualityReviewDemo.state.segments);
  // A fixed returned example; review suggestions never silently change the editable result.
  source.forEach((item, index) => {
    item.audit = {removed:[], added:[]};
    item.reviewErrorReason = '';
    if(index === 0){item.audit={removed:['M02'],added:['M03']};item.reviewErrorReason='描述与画面不一致';}
    if(index === 1){item.audit={removed:[item.originalRejectedReasons[0]],added:['U02']};item.reviewErrorReason='描述与画面不一致';}
    if(index === 2)item.reviewErrorReason='动作开始边界偏早';
  });
  const segments = source.map(item => ({...item,
    mistakeReasons:clone(item.originalMistakeReasons),rejectedReasons:clone(item.originalRejectedReasons),
    feedback:{original:[...item.originalRejectedReasons,...item.originalMistakeReasons],removed:clone(item.audit.removed),added:clone(item.audit.added),reason:item.reviewErrorReason}
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
    const details=document.createElement('details');details.className='ptqw-feedback';details.open=ui.feedbackOpen;
    const chip=(id,status)=>`<span class="ptqw-chip is-${status}">${esc(name(id))}${status==='error'?'<del>错误项</del>':status==='omitted'?'<small>遗漏项</small>':''}</span>`;
    details.innerHTML=`<summary>审核反馈 <small>上次驳回意见 · 只读</small></summary><div class="ptqw-feedback-chips">${feedback.original.map(id=>chip(id,feedback.removed.includes(id)?'error':'correct')).join('')}${feedback.added.map(id=>chip(id,'omitted')).join('')}</div><div class="ptqw-error-reason">错误原因：${esc(feedback.reason||'无')}</div>`;
    details.addEventListener('toggle',()=>{ui.feedbackOpen=details.open;});
    host.querySelector('.ptq-editor').append(details);
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
    const confirm=document.createElement('label');confirm.className='ptqr-complete';
    confirm.innerHTML=`<input type="checkbox" data-field="rework-complete" ${state.reworkComplete?'checked':''} ${state.submitted?'disabled':''}><span>已根据审核反馈完成检查</span>`;
    confirm.addEventListener('change',event=>{state.reworkComplete=event.target.checked;});
    host.querySelector('.ptq-sidebar>footer').prepend(confirm);
    host.querySelector('[data-action="submit"]').textContent=state.submitted?'已重新提交':'重新提交';
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
