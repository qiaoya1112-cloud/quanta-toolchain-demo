(() => {
  function createReview(options = {}) {
  const tagBase=options.tagBase||"post-training-quality-review";
  const eventBase=options.eventBase||"post-quality-review";
  const domPrefix=options.domPrefix||"ptqr";
  const eventName=name=>`${eventBase}-${name}`;
  const storageKey=`quanta.${eventBase}.v1`;
  const SOURCE = window.PostTrainingQualityDemo;
  if (!SOURCE) return;
  const DURATION = 40;
  const REASONS = {
    M01:'夹爪超出画面', M02:'手部脱离夹爪', M03:'其他身体部位辅助', M04:'无意义动作或假动作',
    U01:'视频损坏或相机卡死', U02:'采集时长不足', U03:'画面全程完全遮挡', U04:'设备穿戴不规范'
  };
  const MISTAKE = ['M01','M02','M03','M04'];
  const REJECTED = ['U01','U02','U03','U04'];
  const REVIEW_ERROR_REASONS = ['片段范围错误','片段范围错位','动作开始边界偏早','动作开始边界偏晚','动作结束边界偏早','动作结束边界偏晚','描述与画面不一致'];
  const clone = value => JSON.parse(JSON.stringify(value));
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const format = value => `00:${Number(value).toFixed(1).padStart(4,'0')}`;
  const ordered = () => state.segments.slice().sort((a,b)=>a.start-b.start||a.end-b.end||a.order-b.order);
  const selected = () => state.segments.find(item=>item.id===state.selectedId);
  const originalIds = item => [...item.originalRejectedReasons,...item.originalMistakeReasons];
  const counts = item => ({
    correct: originalIds(item).filter(id=>!item.audit.removed.includes(id)).length,
    error: item.audit.removed.length,
    omitted: item.audit.added.length,
    reason: item.reviewErrorReason ? 1 : 0
  });
  const totals = () => state.segments.reduce((sum,item)=>{const value=counts(item);sum.correct+=value.correct;sum.error+=value.error;sum.omitted+=value.omitted;sum.reason+=value.reason;return sum;},{correct:0,error:0,omitted:0,reason:0});
  const descriptionChanged = item => Boolean(item.audit.removed.length||item.audit.added.length);
  const missingReasonSegments = () => state.segments.filter(item=>descriptionChanged(item)&&!item.reviewErrorReason);
  const hasIssues = () => state.segments.some(item=>descriptionChanged(item)||item.reviewErrorReason);
  const result = () => hasIssues() ? '不通过' : '通过';
  const qualityResult = () => state.segments.some(item=>item.conclusion==='rejected') ? '不合格' : state.segments.some(item=>item.conclusion==='mistake') ? '失误' : '合格';
  const issueSummary = item => {const value=counts(item), names=[];if(value.error)names.push(`错误 ${value.error}`);if(value.omitted)names.push(`遗漏 ${value.omitted}`);if(value.reason)names.push('有片段错误原因');return names.join(' · ');};
  const conclusion = value => value==='rejected'?'不合格':'失误';
  const allowed = () => [...REJECTED,...MISTAKE];
  const notify = () => document.dispatchEvent(new CustomEvent(eventName('state-change'),{detail:clone(state)}));
  const toast = message => document.dispatchEvent(new CustomEvent(eventName('toast'),{detail:{message}}));
  const demoReasons = (item, index) => {
    const mistake = [
      ['M01','M02'],
      ['M03','M04'],
      ['M01','M04'],
      ['M02','M03'],
      ['M01','M03']
    ][index % 5];
    const rejected = [
      {rejected:['U04','U01'],mistake:['M02']},
      {rejected:['U02','U03'],mistake:['M03']},
      {rejected:['U03','U04'],mistake:['M01','M02']}
    ][index % 3];
    return item.conclusion === 'rejected'
      ? {mistakeReasons:rejected.mistake,rejectedReasons:rejected.rejected}
      : {mistakeReasons:mistake,rejectedReasons:[]};
  };

  const state = {
    segments: options.segments ? clone(options.segments) : SOURCE.state.segments.map((item,index)=>{
      const reasons = demoReasons(item,index);
      return {
        id:item.id,start:item.start,end:item.end,track:item.track,order:item.order,conclusion:item.conclusion,
        originalMistakeReasons:reasons.mistakeReasons,originalRejectedReasons:reasons.rejectedReasons,
        reviewErrorReason:'',audit:{removed:[],added:[]}
      };
    }),
    selectedId:SOURCE.state.selectedId||SOURCE.state.segments[0]?.id||'',submitted:false,dirty:false,filter:'all'
  };

  if(options.restoreDraft){try{const saved=JSON.parse(localStorage.getItem(storageKey)||'null');if(saved&&Array.isArray(saved.segments)&&saved.segments.length===state.segments.length&&saved.segments.every(item=>state.segments.some(seed=>seed.id===item.id))){state.segments.forEach(item=>{const draft=saved.segments.find(row=>row.id===item.id);item.audit=clone(draft.audit||{removed:[],added:[]});item.reviewErrorReason=draft.reviewErrorReason||'';item.reviewNote=draft.reviewNote||'';});if(state.segments.some(item=>item.id===saved.selectedId))state.selectedId=saved.selectedId;}}catch(_){}}
  function select(id, seek=true){if(!state.segments.some(item=>item.id===id))return;state.selectedId=id;notify();if(seek)document.dispatchEvent(new CustomEvent(eventName('seek'),{detail:{seconds:selected().start}}));}
  function removeOriginal(reasonId){const item=selected();if(!item||state.submitted||!originalIds(item).includes(reasonId))return;if(!item.audit.removed.includes(reasonId))item.audit.removed.push(reasonId);item.audit.added=item.audit.added.filter(id=>id!==reasonId);state.dirty=true;notify();}
  function restoreOriginal(reasonId){const item=selected();if(!item||state.submitted)return;item.audit.removed=item.audit.removed.filter(id=>id!==reasonId);state.dirty=true;notify();}
  function addOmission(reasonId){const item=selected();if(!item||state.submitted||!allowed().includes(reasonId))return;if(originalIds(item).includes(reasonId)){restoreOriginal(reasonId);return;}if(!item.audit.added.includes(reasonId))item.audit.added.push(reasonId);state.dirty=true;notify();}
  function removeOmission(reasonId){const item=selected();if(!item||state.submitted)return;item.audit.added=item.audit.added.filter(id=>id!==reasonId);state.dirty=true;notify();}

  class ReviewTimeline extends HTMLElement {
    connectedCallback(){if(this.dataset.ready)return;this.dataset.ready='true';this.hidden=true;this.playTime=0;this.playing=false;this.addEventListener('click',event=>this.onClick(event));document.addEventListener(eventName('state-change'),()=>this.render());document.addEventListener(eventName('seek'),event=>{this.playTime=event.detail.seconds;this.render();});this.render();}
    disconnectedCallback(){clearInterval(this.timer);}
    set hidden(value){this.toggleAttribute('hidden',value);if(value){this.playing=false;clearInterval(this.timer);}else this.render();}
    get hidden(){return this.hasAttribute('hidden');}
    onClick(event){const block=event.target.closest('[data-segment-id]');if(block){select(block.dataset.segmentId);return;}if(event.target.closest('.segmented-timeline__play')){this.playing=!this.playing;clearInterval(this.timer);if(this.playing)this.timer=setInterval(()=>{this.playTime=Math.min(DURATION,this.playTime+.1);if(this.playTime>=DURATION){this.playing=false;clearInterval(this.timer);}this.render();},100);this.render();}}
    block(item){const active=item.id===state.selectedId;const issue=descriptionChanged(item)||item.reviewErrorReason;return `<button type="button" class="ptqr-block is-${item.conclusion}${active?' is-selected':''}${issue?' has-review-issue':''}" data-segment-id="${esc(item.id)}" style="left:${item.start/DURATION*100}%;width:${Math.max(.8,(item.end-item.start)/DURATION*100)}%;z-index:${active?30:2}" aria-label="${conclusion(item.conclusion)}片段${issue?' · 存在审核问题':''}">${issue?'<span class="ptqr-track-issue" aria-hidden="true">!</span>':''}</button>`;}
    render(){const hits=state.segments.filter(item=>item.start<=this.playTime&&this.playTime<item.end).map(item=>item.id);this.innerHTML=`<section class="ptqr-timeline"><timeline-controls hydrate standard-label="质检标准"><div class="segmented-timeline__controls"><div class="segmented-timeline__playback"><button type="button" class="segmented-timeline__play" aria-label="${this.playing?'暂停':'播放'}"></button><span><b>${format(this.playTime)}</b> <i>/</i> ${format(DURATION)}</span></div><div class="segmented-timeline__tools"><button type="button" class="segmented-timeline__standard">质检标准</button></div></div></timeline-controls><div class="ptqr-ruler"><span></span><div>${[0,10,20,30,40].map(n=>`<i style="left:${n/DURATION*100}%">${format(n)}</i>`).join('')}</div></div><div class="ptqr-lanes">${[0,1,2].map(track=>`<div class="ptqr-lane"><small>轨道 ${track+1}</small><div>${state.segments.filter(item=>item.track===track).map(item=>this.block(item)).join('')}</div></div>`).join('')}<i class="ptqr-playhead" style="left:calc(68px + (100% - 68px) * ${this.playTime/DURATION})"></i></div></section>`;this.querySelectorAll('.ptqr-block').forEach(node=>node.classList.toggle('is-hit',hits.includes(node.dataset.segmentId)));}
  }

  class ReviewWorkspace extends HTMLElement {
    connectedCallback(){if(this.dataset.ready)return;this.dataset.ready='true';this.timeline=document.createElement(`${tagBase}-timeline`);document.querySelector('.timeline-card')?.append(this.timeline);this.addEventListener('click',event=>this.onClick(event));document.addEventListener(eventName('state-change'),()=>this.render());document.addEventListener('keydown',event=>this.onKey(event));document.addEventListener('pointerdown',event=>{if(this.hidden)return;if(this.menuOpen&&!this.querySelector('.ptqr-add')?.contains(event.target)){this.menuOpen=false;this.render();return;}if(this.errorMenuOpen&&!this.querySelector('.ptqr-error-select')?.contains(event.target)){this.errorMenuOpen=false;this.render();}},true);this.render();}
    set hidden(value){this.toggleAttribute('hidden',value);if(this.timeline)this.timeline.hidden=value;}
    get hidden(){return this.hasAttribute('hidden');}
    move(delta){const list=ordered(),index=list.findIndex(item=>item.id===state.selectedId),target=list[index+delta];if(target)select(target.id);}
    moveTrack(delta){const item=selected();if(!item)return;const list=ordered().filter(candidate=>candidate.track===item.track),index=list.findIndex(candidate=>candidate.id===item.id),target=list[index+delta];if(target)select(target.id);}
    onKey(event){if(this.hidden||!(event.ctrlKey||event.metaKey))return;const action={ArrowUp:()=>this.move(-1),ArrowDown:()=>this.move(1),ArrowLeft:()=>this.moveTrack(-1),ArrowRight:()=>this.moveTrack(1)}[event.key];if(action){event.preventDefault();action();}}
    onClick(event){const action=event.target.closest('[data-action]')?.dataset.action,reason=event.target.closest('[data-reason-id]')?.dataset.reasonId,errorReason=event.target.closest('[data-review-error]')?.dataset.reviewError;if(errorReason&&!state.submitted){const item=selected();if(item){item.reviewErrorReason=errorReason;this.errorMenuOpen=false;state.dirty=true;notify();}return;}if(action==='previous')this.move(-1);if(action==='next')this.move(1);if(action==='track-left')this.moveTrack(-1);if(action==='track-right')this.moveTrack(1);if(action==='remove-original')removeOriginal(reason);if(action==='restore-original')restoreOriginal(reason);if(action==='remove-omission')removeOmission(reason);if(action==='toggle-add'&&!state.submitted){this.menuOpen=!this.menuOpen;this.errorMenuOpen=false;this.render();}if(action==='add-omission')addOmission(reason);if(action==='toggle-error'&&!state.submitted){this.errorMenuOpen=!this.errorMenuOpen;this.menuOpen=false;this.render();}if(action==='clear-error'&&!state.submitted){const item=selected();if(item){item.reviewErrorReason='';this.errorMenuOpen=false;state.dirty=true;notify();}}}
    chip(id,status){const action=status==='correct'?'remove-original':status==='error'?'restore-original':'remove-omission',label=status==='correct'?'去掉此项，记为错误项':'撤销',icon=status==='correct'?'×':'↶';return `<span class="ptqr-chip is-${status}"><span>${esc(REASONS[id]||id)}</span>${status==='error'?'<del>错误项</del>':''}<button type="button" class="ptqr-chip-action" data-action="${action}" data-reason-id="${esc(id)}" ${state.submitted?'disabled':''} aria-label="${label}：${esc(REASONS[id]||id)}" title="${label}"><span aria-hidden="true">${icon}</span></button></span>`;}
    render(){const item=selected();if(!item){this.innerHTML='<section class="ptqr-editor card">暂无片段</section>';return;}const list=ordered(),index=list.findIndex(row=>row.id===item.id),track=list.filter(row=>row.track===item.track),trackIndex=track.findIndex(row=>row.id===item.id),original=originalIds(item);const chips=[...original.filter(id=>!item.audit.removed.includes(id)).map(id=>this.chip(id,'correct')),...item.audit.removed.map(id=>this.chip(id,'error')),...item.audit.added.map(id=>this.chip(id,'omitted'))].join('');const options=allowed().filter(id=>!original.includes(id)&&!item.audit.added.includes(id));const groups=[['不合格描述',options.filter(id=>REJECTED.includes(id))],['失误描述',options.filter(id=>MISTAKE.includes(id))]].filter(group=>group[1].length);const addMenu=groups.length?groups.map(group=>`<section><b>${group[0]}</b>${group[1].map(id=>`<button type="button" data-action="add-omission" data-reason-id="${id}">${esc(REASONS[id])}</button>`).join('')}</section>`).join(''):'<span>没有可新增的描述</span>';const errorMenu=REVIEW_ERROR_REASONS.map(reason=>`<button type="button" data-review-error="${esc(reason)}" class="${item.reviewErrorReason===reason?'is-selected':''}">${esc(reason)}<span>✓</span></button>`).join('');this.innerHTML=`<section class="ptqr-editor card"><div class="ptqr-meta"><div><b class="ptqr-code is-${item.conclusion}">${String(index+1).padStart(2,'0')}</b><span>开始 <strong>${format(item.start)}</strong></span><span>结束 <strong>${format(item.end)}</strong></span><span>时长 <strong>${(item.end-item.start).toFixed(1)}s</strong></span><span class="ptqr-meta-legend" tabindex="0" aria-label="审核状态说明" data-tooltip="未操作的原始描述视为正确；点击标签右侧“×”去掉错选描述并保留错误记录，新增描述表示遗漏。"><i class="is-correct">正确项</i><i class="is-error">错误项</i><i class="is-omitted">遗漏项</i></span></div><div class="segment-actions"><button class="segment-action" data-action="previous" ${index<=0?'disabled':''}>上一段 <kbd>⌘↑</kbd></button><button class="segment-action" data-action="next" ${index>=list.length-1?'disabled':''}>下一段 <kbd>⌘↓</kbd></button><button class="segment-action" data-action="track-left" ${trackIndex<=0?'disabled':''}>同轨左 <kbd>⌘←</kbd></button><button class="segment-action" data-action="track-right" ${trackIndex>=track.length-1?'disabled':''}>同轨右 <kbd>⌘→</kbd></button></div></div><div class="ptqr-review-row"><span class="ptqr-conclusion is-${item.conclusion}">${conclusion(item.conclusion)}</span><span class="ptqr-label">失误描述</span><div class="ptqr-description-box">${chips||'<span class="ptqr-empty">质检员未选择描述</span>'}<div class="ptqr-add"><button type="button" data-action="toggle-add" aria-expanded="${Boolean(this.menuOpen)}" ${state.submitted?'disabled':''}>＋ 新增描述</button><div class="ptqr-add-menu" ${this.menuOpen?'':'hidden'}>${addMenu}</div></div></div></div><div class="ptqr-error-row${descriptionChanged(item)&&!item.reviewErrorReason?' is-required':''}"><span>错误原因${descriptionChanged(item)?'（必填）':'（选填）'}</span><div class="ptqr-error-select"><button type="button" data-action="toggle-error" aria-expanded="${Boolean(this.errorMenuOpen)}" ${state.submitted?'disabled':''}><span>${esc(item.reviewErrorReason||'请选择错误原因')}</span><img src="/static/annotation_workbench/assets/icon-chevron.svg" alt=""></button><div class="ptqr-error-menu" ${this.errorMenuOpen?'':'hidden'}>${errorMenu}<button type="button" class="ptqr-error-clear" data-action="clear-error">清除错误原因</button></div></div></div></section>`;}
  }

  class ReviewSidebar extends HTMLElement {
    connectedCallback(){if(this.dataset.ready)return;this.dataset.ready='true';this.addEventListener('click',event=>this.onClick(event));document.addEventListener(eventName('state-change'),()=>this.render());this.render();}
    save(){try{localStorage.setItem(storageKey,JSON.stringify({segments:state.segments,selectedId:state.selectedId,savedAt:new Date().toISOString()}));state.dirty=false;notify();toast('审核草稿已保存');}catch(_){toast('保存失败，请重试');}}
    moveIssue(direction){const issues=ordered().filter(item=>counts(item).error||counts(item).omitted||item.reviewErrorReason);if(!issues.length)return;const index=issues.findIndex(item=>item.id===state.selectedId),target=issues[(index<0?0:index+direction+issues.length)%issues.length];select(target.id);}
    onClick(event){const row=event.target.closest('[data-segment-id]');if(row){select(row.dataset.segmentId);return;}const action=event.target.closest('[data-action]')?.dataset.action;if(action==='filter-all'){state.filter='all';notify();}if(action==='filter-issues'){state.filter='issues';notify();}if(action==='previous-issue')this.moveIssue(-1);if(action==='next-issue')this.moveIssue(1);if(action==='save'&&!state.submitted)this.save();if(action==='leave'&&!state.submitted){this.save();toast('审核草稿已保存');}if((action==='submit'||action==='reject')&&!state.submitted){const missing=missingReasonSegments();if(missing.length){select(missing[0].id);this.querySelector(`#${domPrefix}ValidationDialog`)?.showModal();return;}this.querySelector(`#${domPrefix}SubmitDialog`)?.showModal();}if(action==='confirm-submit'&&!missingReasonSegments().length&&!state.submitted){state.submitted=true;state.dirty=false;this.querySelector(`#${domPrefix}SubmitDialog`)?.close();notify();toast(hasIssues()?'审核已驳回，问题已反馈给质检员':'审核已通过');}}
    render(){const all=ordered(),issues=all.filter(item=>counts(item).error||counts(item).omitted||item.reviewErrorReason),list=state.filter==='issues'?issues:all,sum=totals(),reviewResult=result(),qualityConclusion=qualityResult(),resultClass=hasIssues()?'is-rework':'is-pass';const rows=list.map(item=>{const index=all.indexOf(item),value=counts(item),issue=value.error||value.omitted||value.reason,summary=originalIds(item).map(id=>REASONS[id]||id).join('、');return `<button type="button" class="ptqr-list-item${item.id===state.selectedId?' is-active':''}${issue?' has-issue':''}" data-segment-id="${esc(item.id)}"><span class="ptqr-list-id">${String(index+1).padStart(2,'0')}</span><span class="ptqr-list-main"><span class="ptqr-list-time">${format(item.start)}–${format(item.end)} <em>${(item.end-item.start).toFixed(1)}s</em></span><span class="ptqr-list-summary"><b class="is-${item.conclusion}">${conclusion(item.conclusion)}</b><strong title="${esc(summary)}">${esc(summary)}</strong></span><span class="ptqr-counts"><span>审核情况</span><i class="is-error">错误项 ${value.error||'-'}</i><i class="is-omitted">遗漏项 ${value.omitted||'-'}</i></span><span class="ptqr-list-error" title="${esc(item.reviewErrorReason||'')}">错误原因：${esc(item.reviewErrorReason||'-')}</span></span>${issue?'<span class="ptqr-issue-badge" aria-label="该片段存在审核问题" title="该片段存在审核问题">!</span>':''}</button>`;}).join('');const impacted=issues.length,missing=missingReasonSegments(),changed=hasIssues();this.innerHTML=`<section class="ptqr-sidebar"><header><div><b>质检审核列表</b><span>共 ${all.length} 个片段</span></div><div class="ptqr-list-overview${missing.length?' has-warning':''}">${missing.length?`还有 ${missing.length} 个修改片段未选错误原因`:`正确 ${sum.correct} · 错误 ${sum.error} · 遗漏 ${sum.omitted} · 片段错误 ${sum.reason}`}</div></header><div class="ptqr-list-tools"><div><button type="button" data-action="filter-all" class="${state.filter==='all'?'is-active':''}">全部 ${all.length}</button><button type="button" data-action="filter-issues" class="${state.filter==='issues'?'is-active':''}">仅看有问题 ${issues.length}</button></div></div><div class="ptqr-list">${rows||'<div class="ptqr-list-empty">暂无审核问题</div>'}</div><footer><div class="ptqr-result"><span>质检结论</span><output class="${qualityConclusion==='合格'?'is-pass':qualityConclusion==='失误'?'is-mistake':'is-rejected'}">${qualityConclusion}</output></div><div class="workbench-footer-actions"><button type="button" data-action="save" ${state.submitted?'disabled':''}>保存</button><button type="button" data-action="leave" ${state.submitted?'disabled':''}>释放</button><button type="button" class="is-reject" data-action="reject" ${state.submitted||!changed?'disabled':''}>驳回</button><button type="button" class="is-submit" data-action="submit" ${state.submitted||changed?'disabled':''}>提交</button></div></footer></section><dialog id="${domPrefix}SubmitDialog" class="ptqr-dialog"><header><h2>${changed?'确认驳回':'确认提交审核'}</h2><button type="button" onclick="this.closest('dialog').close()">×</button></header><div><span>审核结论</span><strong class="${resultClass}">${reviewResult}</strong><p>${changed?`涉及 ${impacted} 个片段：错误项 ${sum.error} 个、遗漏项 ${sum.omitted} 个、片段错误原因 ${sum.reason} 个。提交后将驳回给质检员返修。`:`已完成 ${all.length} 个片段审核，未发现错误项、遗漏项或片段错误原因，任务将审核通过。`}</p><small>质检员返修时可查看对应片段、错误描述、遗漏描述和片段错误原因。</small></div><footer><button type="button" onclick="this.closest('dialog').close()">取消</button><button type="button" class="is-primary" data-action="confirm-submit">${changed?'确认驳回返修':'确认审核通过'}</button></footer></dialog><dialog id="${domPrefix}ValidationDialog" class="ptqr-dialog ptqr-validation-dialog"><header><h2>请补充错误原因</h2><button type="button" onclick="this.closest('dialog').close()">×</button></header><div><strong class="is-rework">信息未完善</strong><p>还有 ${missing.length} 个修改过描述的片段未选择错误原因。请补充完整后再${changed?'驳回':'提交审核'}。</p><small>已自动定位到第一个未完善片段。</small></div><footer><button type="button" class="is-primary" onclick="this.closest('dialog').close()">去补充</button></footer></dialog>`;}
  }

  const renderReviewWorkspace = ReviewWorkspace.prototype.render;
  ReviewWorkspace.prototype.render = function(){
    renderReviewWorkspace.call(this);
    options.decorateWorkspace?.(this, selected(), state);
  };

  customElements.define(`${tagBase}-timeline`,ReviewTimeline);
  customElements.define(`${tagBase}-workspace`,ReviewWorkspace);
  const originalSidebarRender=ReviewSidebar.prototype.render;
  ReviewSidebar.prototype.render=function(){originalSidebarRender.call(this);options.decorateSidebar?.(this,state);};
  customElements.define(`${tagBase}-sidebar`,ReviewSidebar);
  let timer;document.addEventListener(eventName('toast'),event=>{const node=document.getElementById('workbenchNotice');if(!node)return;node.textContent=event.detail.message;node.hidden=false;clearTimeout(timer);timer=setTimeout(()=>node.hidden=true,2600);});
  return {state,select,removeOriginal,restoreOriginal,addOmission,removeOmission,counts,totals,result};
  }
  window.createPostTrainingQualityReview=createReview;
  window.PostTrainingQualityReviewDemo=createReview();
})();
