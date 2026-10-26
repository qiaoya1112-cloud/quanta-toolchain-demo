/* Independent, local-only collection workflow. All persisted writes use the demo API. */
(() => {
  'use strict';
  const boot = JSON.parse(document.getElementById('dc-bootstrap').textContent);
  const demoPeople = ['joanna','ben','tina','leo','lisa'];
  if(boot.user==='joanna.qiao')boot.user='joanna';
  // Keep existing local fixtures readable without resetting the demo database.
  function displayDemoPeople(task) {
    const seedIndex = /^(?:DC-26|026)(?:0[1-9]|10)$/.test(task.id) ? Number(task.id.slice(-2))-1 : -1;
    if(['joanna.qiao','演示创建人'].includes(task.creator))task.creator=seedIndex>=0?demoPeople[seedIndex%demoPeople.length]:'joanna';
    for(const event of task.events||[])if(event.actor==='joanna.qiao')event.actor=event.title==='创建采集任务'?task.creator:'joanna';
    for(const record of task.records||[]) {
      const index=['采集员 A','采集员 B','采集员 C'].indexOf(record.operator);
      if(index>=0)record.operator=demoPeople[index];
    }
    return task;
  }
  const root = document.getElementById('dc-app');
  const dialog = document.getElementById('dc-dialog');
  const specLink = window.CollectionSpecLink;
  const params = new URLSearchParams(location.search);
  const route = location.pathname.slice(boot.base.length).split('/').filter(Boolean);
  const view = !route.length ? 'list' : route[0] === 'new' || route[1] === 'edit' ? 'form' : 'detail';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const icons = {
    plus:'M8 3v10M3 8h10', search:'m11.5 11.5 3 3M7 1.5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11',
    back:'m10 3-5 5 5 5M5 8h9', copy:'M6 5h7v9H6zM3 11V2h7', chevron:'m6 4 4 4-4 4',
    folder:'M1 4h5l2 2h7v8H1zM1 4V2h5l2 2h7v2', clock:'M8 3v5l3 2M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13',
    upload:'M8 11V2m-4 4 4-4 4 4M2 10v4h12v-4', check:'m3 8 3 3 7-7', play:'m5 3 7 5-7 5z', pause:'M5 3v10M11 3v10', pause:'M5 3v10M11 3v10',
    reset:'M13.5 6A5.7 5.7 0 0 0 3.8 3.8L2 5.5M2 2v3.5h3.5M2.5 10a5.7 5.7 0 0 0 9.7 2.2l1.8-1.7M10.5 10.5H14V14',
    info:'M8 7v4M8 4h.01M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13',
    stop:'M4 4h8v8H4z', close:'m4 4 8 8m0-8-8 8', edit:'m10 2 4 4-8 8H2v-4zM8 4l4 4', trajectory:'M2 13.5 6 9l3 2 5-6M2 3v10h12'
  };
  const icon = key => `<svg class="dc-icon" viewBox="0 0 16 16" aria-hidden="true"><path d="${icons[key] || icons.info}"/></svg>`;
  const reviewExplanation='从本次开放或最近录制（取较晚时间）起，满48小时无新录制时提醒。重新开放重新计时；仅作提醒，不会自动关闭。';
  const reviewTip=document.createElement('div');
  reviewTip.id='dc-review-tooltip';reviewTip.className='dc-review-tooltip';reviewTip.setAttribute('role','tooltip');reviewTip.setAttribute('popover','manual');reviewTip.textContent=reviewExplanation;
  document.body.append(reviewTip);
  let reviewAnchor=null,reviewPinned=false;
  function hideReviewTip(){if(reviewTip.matches(':popover-open'))reviewTip.hidePopover();reviewAnchor=null;reviewPinned=false;}
  function showReviewTip(anchor,pinned=false){
    reviewAnchor=anchor;reviewPinned=reviewPinned||pinned;
    const rect=anchor.getBoundingClientRect(),width=Math.min(272,innerWidth-24);
    reviewTip.style.width=width+'px';reviewTip.style.left=Math.max(12,Math.min(rect.left-12,innerWidth-width-12))+'px';
    reviewTip.style.top=(rect.bottom+8)+'px';
    if(!reviewTip.matches(':popover-open'))reviewTip.showPopover();
    if(reviewTip.getBoundingClientRect().bottom>innerHeight-12)reviewTip.style.top=Math.max(12,rect.top-reviewTip.offsetHeight-8)+'px';
  }
  root.addEventListener('pointerover',event=>{const anchor=event.target.closest('[data-review-help]');if(anchor&&!anchor.contains(event.relatedTarget))showReviewTip(anchor);});
  root.addEventListener('pointerout',event=>{const anchor=event.target.closest('[data-review-help]');if(anchor&&!anchor.contains(event.relatedTarget)&&!reviewPinned&&document.activeElement!==anchor)hideReviewTip();});
  root.addEventListener('focusin',event=>{if(event.target.matches('[data-review-help]'))showReviewTip(event.target);});
  root.addEventListener('focusout',event=>{if(event.target.matches('[data-review-help]'))hideReviewTip();});
  root.addEventListener('click',event=>{const anchor=event.target.closest('[data-review-help]');if(anchor)showReviewTip(anchor,true);});
  document.addEventListener('pointerdown',event=>{if(reviewAnchor&&!reviewAnchor.contains(event.target)&&!reviewTip.contains(event.target))hideReviewTip();});
  document.addEventListener('keydown',event=>{if(event.key==='Escape')hideReviewTip();});
  addEventListener('resize',hideReviewTip);
  addEventListener('scroll',()=>{if(reviewAnchor?.isConnected)showReviewTip(reviewAnchor);else hideReviewTip();},true);
  const project = id => boot.projects.find(p => p.id === id)?.name || id;
  const checkpoint = id => boot.checkpoints.find(c => c.id === id)?.name || id || '未选择';
  const modeName = t => t.source === 'udas' ? 'UDAS' : t.mode === 'DAGGER' ? 'DAGGER' : 'NORMAL';
  const modeBadge = t => `<span class="dc-badge ${t.mode === 'DAGGER' ? 'purple' : ''}">${modeName(t)}</span>`;
  const stateBadge = t => `<span class="dc-badge ${t.status === 'open' ? 'teal' : ''}"><i class="dc-dot"></i>${t.status === 'open' ? '开放采集' : '已结束采集'}</span>`;
  const date = value => value ? new Date(value).toLocaleString('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}) : '—';
  const fullDate = value => value ? value.replace('T',' ') : '—';
  const duration = s => s >= 3600 ? `${(s / 3600).toFixed(1)} 小时` : `${Math.floor(s / 60)} 分 ${s % 60} 秒`;
  const collectionConclusion = record => {
    // 【新】采集事实与质检 quality 独立；旧平台 is_mistake=false 表示成功。
    let value=record?.collection_result;
    if(!['success','failure'].includes(value)&&typeof record?.is_mistake==='boolean')value=record.is_mistake?'failure':'success';
    if(!['success','failure'].includes(value))return {value:'',label:'-',tone:''};
    const [label,tone]={success:['成功','teal'],failure:['失败','red']}[value];
    return {label,tone,value};
  };
  const collectionConclusionBadge = record => {const result=collectionConclusion(record);return result.value?`<span class="dc-badge dc-conclusion-badge ${result.tone}"><i class="dc-dot"></i>${result.label}</span>`:'<span class="dc-muted">-</span>';};
  const hours = seconds => seconds > 0 && seconds < 36 ? '<0.01' : (seconds / 3600).toFixed(2);
  const option = (value, label, selected) => `<option value="${esc(value)}" ${value === selected ? 'selected' : ''}>${esc(label)}</option>`;
  const clone = value => JSON.parse(JSON.stringify(value));
  let generalizationEditor = null;
  let tasks = [], task = null, form = null, dirty = false, busy = false, formErrors = {}, specs = [];
  const priorityLabel = value => value >= 7 ? '高' : value >= 4 ? '中' : '低';
  const processingStatusLabel = value => ({draft:'未发布',waiting:'等待数据',pending:'待处理',processing:'处理中',completed:'已完成',paused:'已关闭'}[value] || value || '—');
  const processingStatusTone = value => ({completed:'teal',processing:'blue',pending:'amber',paused:'',waiting:''}[value] || '');
  let processingJobs = [], processingLoading = false, processingError='';
  const detailTabs = ['records','processing','config','activity'];
  let activeTab = detailTabs.includes(location.hash.slice(1)) ? location.hash.slice(1) : 'records';
  const detailScroll = {records:0, config:0, activity:0};
  const recordDefaults={id:'',device:'',operator:'',conclusion:'',upload:'uploaded'};
  const recordFilters = {...recordDefaults};
  if(['uploaded','uploading','failed','all'].includes(params.get('upload')))recordFilters.upload=params.get('upload');
  if(params.get('record'))recordFilters.id=params.get('record');
  let recordPage = 1;
  let checkpointSelection = '', modalOrigin = null;
  let formModeCache = {}, draft = null, formSource = null;
  // 【新】刷新只应用到当前浏览视图；播放器和弹窗使用期间暂存新数据。
  let refreshInFlight=false, pendingRefresh=null, lastRefreshedAt=0, refreshFailed=false;
  const createAttemptKey=`quanta.collection.create-attempt:${location.pathname}:${params.get('copy')||''}:${params.get('source')||''}`;
  let createAttempt=null;
  try{createAttempt=JSON.parse(sessionStorage.getItem(createAttemptKey));}catch(_){}
  const draftKey = `quanta.collection.draft:${location.pathname}:${params.get('copy') || ''}:${params.get('source') || ''}`;
  const list = {
    source: params.get('source') === 'udas' ? 'udas' : 'robot',
    mode: ['NORMAL','DAGGER'].includes(params.get('mode')) ? params.get('mode') : '',
    q: params.get('q') || '', creator: params.get('creator') || '', project: params.get('project') || '', status: params.get('status') || '',
    mineOnly: params.get('mine') === '1', reviewOnly: params.get('review') === '1' || params.get('quick') === 'review', page:Math.max(1,Math.floor(Number(params.get('page'))||1))
  };
  // Return only to this module's list, never to a supplied external URL.
  function listReturnHref() {
    try {
      const target=new URL(params.get('return')||'',location.origin);
      if(params.has('return')&&target.origin===location.origin&&target.pathname===boot.base)return target.pathname+target.search;
    } catch (_) { /* Invalid context falls back to the task's own source. */ }
    return boot.base+'?source='+(form?.source||task?.source||list.source);
  }
  function contextualPath(path) {
    const target=new URL(path,location.origin);
    target.searchParams.set('return',view==='list'?location.pathname+location.search:listReturnHref());
    return target.pathname+target.search;
  }
  const withListContext = path => esc(contextualPath(path));
  function rememberListPosition() {
    if(view!=='list')return;
    const scrolls=[];
    for(let el=root.parentElement;el;el=el.parentElement)scrolls.push(el.scrollTop);
    try{sessionStorage.setItem('dc-list-position:'+location.pathname+location.search,JSON.stringify({x:scrollX,y:scrollY,scrolls}));}catch(_){}
  }
  function restoreListPosition() {
    try{
      const state=JSON.parse(sessionStorage.getItem('dc-list-position:'+location.pathname+location.search));
      if(!state)return;
      requestAnimationFrame(()=>{let i=0;for(let el=root.parentElement;el;el=el.parentElement)el.scrollTop=state.scrolls[i++]||0;window.scrollTo(state.x,state.y);});
    }catch(_){}
  }
  root.addEventListener('click',event=>{if(event.target.closest('a[href]'))rememberListPosition();},true);
  window.addEventListener('pagehide',rememberListPosition);
  function toast(message) {
    const el = document.getElementById('dc-toast');
    el.textContent = message; el.classList.add('show');
    clearTimeout(toast.timer); toast.timer = setTimeout(() => el.classList.remove('show'), 3500);
  }
  async function request(path, method = 'GET', body, headers={}) {
    const response = await fetch(boot.api + path, {method, cache:'no-store', headers:{'Content-Type':'application/json',...headers}, body:body === undefined ? undefined : JSON.stringify(body)});
    let data;
    try { data = await response.json(); } catch (_) { throw new Error('服务暂时不可用，请稍后重试'); }
    if (!response.ok) { const error = new Error(data.error || '请检查填写内容'); error.errors = data.errors; error.status = response.status; throw error; }
    if(data.tasks)data.tasks.forEach(displayDemoPeople);
    if(data.task)displayDemoPeople(data.task);
    return data;
  }
  function ready(html) { root.dataset.view=view; root.innerHTML = html; root.setAttribute('aria-busy', 'false'); root.querySelectorAll('[role="tab"]').forEach(el=>el.tabIndex=el.getAttribute('aria-selected')==='true'?0:-1); }
  function refreshControl(){return `<button type="button" class="dc-btn dc-refresh-button" data-action="refresh-data" aria-label="刷新数据" title="刷新数据">${icon('reset')}<span>刷新</span></button>`;}
  function updateRefreshControl(){
    root.querySelectorAll('[data-action="refresh-data"]').forEach(button=>{
      button.disabled=refreshInFlight;button.classList.toggle('is-loading',refreshInFlight);
      const label=refreshFailed?'刷新失败，重试':pendingRefresh?'有新数据，播放结束或关闭弹窗后更新':'刷新数据';
      button.setAttribute('aria-label',label);button.title=label+(lastRefreshedAt?' · 上次更新 '+new Date(lastRefreshedAt).toLocaleTimeString('zh-CN',{hour12:false}):'');
      button.querySelector('span').textContent=refreshInFlight?'刷新中':refreshFailed?'重试':pendingRefresh?'有新数据':'刷新';
    });
  }
  function detailInfo(t){
    const m=t.metrics;
    return `<div class="dc-detail-meta"><button class="dc-link dc-mono dc-detail-id" data-action="copy-task-id" aria-label="复制任务 ID ${esc(t.id)}" title="复制任务 ID"><span>ID ${esc(t.id)}</span>${icon('copy')}</button><span>${esc(project(t.project))}</span>${modeBadge(t)}${stateBadge(t)}</div><div class="dc-stat-grid dc-detail-stats-inline"><div class="dc-stat"><span class="dc-stat-name">已上传数据</span><strong class="dc-stat-value">${m.uploaded}</strong></div><div class="dc-stat"><span class="dc-stat-name">采集时长</span><strong class="dc-stat-value">${esc(hours(m.seconds))}<small>小时</small></strong></div>${t.expected_hours!=null?`<div class="dc-stat"><span class="dc-stat-name">预期采集</span><strong class="dc-stat-value">${esc(t.expected_hours)}<small>小时</small></strong></div>`:''}</div>${m.needs_review?`<span class="dc-note amber dc-inline-note" title="${reviewExplanation}">${icon('clock')}<span>建议检查收尾</span></span>`:''}`;
  }
  async function loadProcessingLinks(render=true){
    if(!task||processingLoading)return;
    processingLoading=true;processingError='';
    try{
      const result=await request('/processing/tasks?collection='+encodeURIComponent(task.id));
      processingJobs=result.tasks||[];
      processingLoading=false;
      if(render&&activeTab==='processing'&&document.getElementById('dc-detail-body'))renderProcessingTab(document.getElementById('dc-detail-body'));
      return processingJobs;
    }catch(error){processingError=error.message;processingLoading=false;if(render&&activeTab==='processing')renderProcessingTab(document.getElementById('dc-detail-body'));return []}
    finally{processingLoading=false;}
  }
  function processingSummary(){
    const ids=new Set();processingJobs.forEach(job=>(job.records||[]).filter(record=>record.task_id===task.id).forEach(record=>ids.add(record.id+'@'+record.task_id)));
    return {count:processingJobs.length,active:processingJobs.filter(job=>job.status==='processing').length,completed:processingJobs.filter(job=>job.status==='completed').length,records:ids.size};
  }
  function showCreateSuccess(){
    openDialog('采集任务已创建',`<div class="dc-created-identity"><strong>${esc(task.name)}</strong><span>任务 ID ${esc(task.id)}</span></div>`,
      '<button class="dc-btn" data-action="creation-done">查看采集任务</button><button class="dc-btn primary" data-action="create-processing">继续创建处理任务</button>');
  }
  async function showRecordProcessing(id){
    const record=task.records.find(r=>r.id===id);if(!record)return;
    openDialog('关联处理任务','<p role="status">正在加载…</p>');
    try{
      const {tasks:jobs}=await request('/processing/tasks?collection='+encodeURIComponent(task.id)+'&record='+encodeURIComponent(id));
      if(!dialog.open)return;
      dialog.querySelector('.dc-dialog-body').innerHTML=`<p class="dc-processing-record-id">${esc(id)}</p>${jobs.length?jobs.map(job=>`<article class="dc-record-processing-card"><a href="${esc(job.href)}">${esc(job.name)}</a><span>${esc(job.id)}</span>${job.stage_progress.map(p=>`<div class="dc-processing-stage-status"><strong>${esc(p.stage)}</strong><span class="dc-badge ${processingStatusTone(p.status)}">${esc(p.label)}</span></div>`).join('')}</article>`).join(''):'<div class="dc-processing-empty">此条数据尚未纳入处理任务</div>'}`;
    }catch(error){dialog.querySelector('.dc-dialog-body').innerHTML=`<p role="alert">${esc(error.message)}</p><button class="dc-btn" data-action="record-processing" data-id="${esc(id)}">重试</button>`;}
  }
  function recordProcessingCell(record){
    const links=processingJobs.filter(job=>(job.records||[]).some(item=>item.id===record.id&&item.task_id===task.id));
    if(!links.length)return '<span class="dc-muted">-</span>';
    return `<button type="button" class="dc-link" data-action="record-processing" data-id="${esc(record.id)}">${links.length} 个任务</button>`;
  }
  function applyRefresh(result){
    if(view==='list'){
      tasks=result.tasks;const table=root.querySelector('.dc-table-wrap'),x=table?.scrollLeft||0,y=table?.scrollTop||0;
      renderListResults();const replacement=root.querySelector('.dc-table-wrap');if(replacement){replacement.scrollLeft=x;replacement.scrollTop=y;}
    }else{
      if(result.task.revision<task.revision)return;
      const oldTask=task;task=result.task;
      const linksChanged=result.processingJobs&&JSON.stringify(result.processingJobs)!==JSON.stringify(processingJobs);
      if(result.processingJobs)processingJobs=result.processingJobs;
      root.querySelector('.dc-detail-info-row').innerHTML=detailInfo(task);
      const stateButton=root.querySelector('[data-action="change-state"]');
      stateButton.textContent=task.status==='open'?'结束采集':'重新开放';stateButton.className='dc-btn '+(task.status==='open'?'danger':'primary');
      root.querySelector('[data-spec-shortcut]').innerHTML=task.spec_url?specLink.button(task.spec_url):'';
      const scroller=detailScroller(),position=scroller?.scrollTop||0,x=scroller?.scrollLeft||0;
      if(activeTab==='processing')loadProcessingLinks();
      else if(activeTab==='records'&&(linksChanged||oldTask.status!==task.status||JSON.stringify(oldTask.records)!==JSON.stringify(task.records)))renderRecords();
      else if(activeTab==='config'&&oldTask.revision!==task.revision)renderTaskConfiguration(document.getElementById('dc-detail-body'));
      else if(activeTab==='activity'&&oldTask.revision!==task.revision)renderDetailBody();
      const replacement=detailScroller();if(replacement){replacement.scrollTop=position;replacement.scrollLeft=x;}
    }
    lastRefreshedAt=Date.now();refreshFailed=false;updateRefreshControl();
  }
  function applyPendingRefresh(){
    if(!pendingRefresh||busy||dialog.open||activeRecordVideo)return;
    const result=pendingRefresh;pendingRefresh=null;applyRefresh(result);
  }
  async function refreshCollection(manual=false){
    if(view==='form'||(view==='detail'&&!task)||refreshInFlight||busy||(!manual&&document.hidden)||(!manual&&Date.now()-lastRefreshedAt<3000))return;
    refreshInFlight=true;updateRefreshControl();
    try{
      const result=await request(view==='list'?'/tasks':'/tasks/'+encodeURIComponent(task.id));
      if(view==='detail'){
        try{result.processingJobs=(await request('/processing/tasks?collection='+encodeURIComponent(task.id))).tasks;}catch(_){/* Keep existing relationships if this independent request fails. */}
      }
      if(busy)return;
      if(view==='detail'&&(dialog.open||activeRecordVideo)){
        if(JSON.stringify(result.task)!==JSON.stringify(task)||(result.processingJobs&&JSON.stringify(result.processingJobs)!==JSON.stringify(processingJobs)))pendingRefresh=result;
        else{pendingRefresh=null;lastRefreshedAt=Date.now();}
        if(manual&&pendingRefresh)toast('已获取最新数据，播放结束或关闭弹窗后更新');
      }else{pendingRefresh=null;applyRefresh(result);}
      refreshFailed=false;if(manual&&!pendingRefresh)toast('数据已刷新');
    }catch(error){refreshFailed=true;if(manual)toast('刷新失败，保留原有数据。'+error.message);}
    finally{refreshInFlight=false;updateRefreshControl();}
  }
  function empty(title, message, action = '') {
    return `<div class="dc-empty">${icon('folder')}<h3>${esc(title)}</h3><p>${esc(message)}</p>${action}</div>`;
  }
  function pageHead(title, subtitle, actions = '', back = false, meta = '') {
    if(view==='form')return `<header class="dc-form-page-head"><a class="dc-back" href="${esc(listReturnHref())}">‹ 返回</a><h1>${esc(title)}</h1></header>`;
    return `${back ? `<a class="dc-back" href="${esc(listReturnHref())}">${icon('back')}返回采集任务</a>` : ''}<header class="dc-head dc-between"><div><div class="dc-row"><h1>${esc(title)}</h1></div>${subtitle ? `<p>${subtitle}</p>` : ''}${meta}</div>${actions ? `<div class="dc-row dc-head-actions">${actions}</div>` : ''}</header>`;
  }
  function updateListUrl() {
    const q = new URLSearchParams();
    for (const key of ['source','mode','q','creator','project','status']) if (list[key]) q.set(key,list[key]);
    if (list.reviewOnly) q.set('review','1');
    if (list.mineOnly) q.set('mine','1');
    if (list.page>1) q.set('page',list.page);
    history.replaceState(null, '', boot.base + '?' + q);
  }
  function filteredTasks(ignoreReview = false) {
    const q = list.q.toLocaleLowerCase().trim();
    return tasks.filter(t => t.source === list.source && (!list.mode || list.source !== 'robot' || t.mode === list.mode)
      && (!q || [t.name,t.id, ...t.tags].join(' ').toLocaleLowerCase().includes(q))
      && (!list.creator || (t.creator || '').toLocaleLowerCase().includes(list.creator.toLocaleLowerCase().trim()))
      && (!list.mineOnly || t.creator === boot.user)
      && (!list.project || t.project === list.project) && (!list.status || t.status === list.status)
      && (ignoreReview || !list.reviewOnly || t.metrics.needs_review));
  }
  function renderList() {
    hideReviewTip();
    updateListUrl();
    ready(pageHead('数据采集', '', `${refreshControl()}<a class="dc-btn primary" data-list-create href="${withListContext(boot.base+'/new?source='+list.source)}">${icon('plus')}新建${list.source==='udas'?'UDAS':'机器人'}任务</a>`) + `
      <section class="dc-panel dc-list-panel">
        <div class="dc-tabs" role="tablist" aria-label="采集来源">
          ${[['udas','UDAS'],['robot','机器人采集']].map(([id,label])=>`<button class="dc-tab" role="tab" aria-selected="${list.source===id}" data-action="source-tab" data-value="${id}">${label}</button>`).join('')}
        </div>
        <div class="dc-list-filters" role="search" aria-label="筛选采集任务">
          <label class="dc-search">${icon('search')}<input class="dc-input" data-filter="q" aria-label="搜索任务名称、ID或标签" placeholder="任务名称 / ID" value="${esc(list.q)}"></label>
          <label class="dc-search">${icon('search')}<input class="dc-input" data-filter="creator" aria-label="搜索创建人" placeholder="创建人" value="${esc(list.creator)}"></label>
          <select class="dc-select" data-filter="project" aria-label="项目">${option('','全部项目',list.project)}${boot.projects.map(p=>option(p.id,p.name,list.project)).join('')}</select>
          <select class="dc-select" data-filter="status" aria-label="采集状态">${option('','全部状态',list.status)}${option('open','开放采集',list.status)}${option('closed','已结束采集',list.status)}</select>
          ${list.source==='robot' ? `<select class="dc-select" data-filter="mode" aria-label="采集模式">${option('','全部模式',list.mode)}${option('NORMAL','NORMAL',list.mode)}${option('DAGGER','DAGGER',list.mode)}</select>` : ''}
          <div class="dc-list-shortcuts" role="group" aria-label="快捷筛选">
            <button type="button" class="dc-review-filter dc-mine-filter${list.mineOnly?' active':''}" aria-pressed="${list.mineOnly}" data-action="mine-filter">我创建的</button>
            <button type="button" class="dc-review-filter${list.reviewOnly?' active':''}" aria-pressed="${list.reviewOnly}" data-action="review-filter" title="${reviewExplanation}">${icon('clock')}建议检查收尾 <span></span></button>
          </div>
          <button type="button" class="dc-btn dc-filter-reset" data-action="reset-filters" aria-label="重置筛选" title="重置筛选">${icon('reset')}</button>
        </div>
        <div id="dc-list-results"></div>
      </section>`);
    renderListResults();
    updateRefreshControl();
  }
  function renderListResults() {
    hideReviewTip();
    const filtered = filteredTasks(), pageCount = Math.max(1,Math.ceil(filtered.length/8));
    list.page = Math.min(list.page,pageCount);
    updateListUrl();
    root.querySelector('[data-action="review-filter"] span').textContent=filteredTasks(true).filter(t=>t.metrics.needs_review).length;
    root.querySelector('[data-list-create]').setAttribute('href',contextualPath(boot.base+'/new?source='+list.source));
    const rows = filtered.slice((list.page-1)*8,list.page*8);
    document.getElementById('dc-list-results').innerHTML = rows.length ? `<div class="dc-table-wrap"><table class="dc-table dc-task-table" aria-label="采集任务"><colgroup><col><col><col><col><col><col><col><col><col><col><col></colgroup><thead><tr><th>任务 ID</th><th>任务名称</th><th>所属项目</th><th>创建人</th><th>采集模式</th><th>优先级</th><th>采集状态</th><th class="dc-numeric-cell">已上传数据</th><th class="dc-numeric-cell">采集时长（小时）</th><th>最近采集</th><th class="dc-actions-heading">操作</th></tr></thead><tbody>${rows.map(t=>`<tr>
      <td class="dc-task-id-cell" data-label="任务 ID"><a class="dc-task-id" title="${esc(t.id)}" href="${withListContext(boot.base+'/'+t.id)}">${esc(t.id)}</a></td>
      <td class="dc-task-cell" data-label="任务名称"><div class="dc-task-name-row"><a class="dc-task-title" title="${esc(t.name)}" href="${withListContext(boot.base+'/'+t.id)}">${esc(t.name)}</a></div></td>
      <td class="dc-project-cell" data-label="所属项目"><span class="dc-project-name" title="${esc(project(t.project))}">${esc(project(t.project))}</span></td>
      <td data-label="创建人">${esc(t.creator||'-')}</td>
      <td data-label="采集模式">${t.source==='robot'?esc(modeName(t)):'-'}</td>
      <td data-label="优先级">${priorityLabel(t.priority??6)}</td>
      <td data-label="采集状态"><div class="dc-state-cell"><button type="button" class="dc-state-toggle" role="switch" aria-checked="${t.status==='open'}" aria-label="${esc(t.name)}的采集状态" title="${t.status==='open'?'结束采集':'重新开放采集'}" data-action="list-change-state" data-id="${esc(t.id)}"><i aria-hidden="true"></i></button>${t.metrics.needs_review?`<button type="button" class="dc-review-indicator" data-review-help aria-label="建议检查收尾" aria-describedby="dc-review-tooltip">${icon('clock')}</button>`:''}</div></td>
      <td class="dc-numeric-cell" data-label="已上传数据"><span class="dc-number">${t.metrics.uploaded}</span></td>
      <td class="dc-numeric-cell" data-label="采集时长（小时）"><span class="dc-number">${esc(hours(t.metrics.seconds))}</span></td>
      <td class="dc-muted" data-label="最近采集">${t.metrics.latest?date(t.metrics.latest):'-'}</td>
      <td class="dc-actions-cell"><div class="dc-table-actions"><a aria-label="查看 ${esc(t.name)}" href="${withListContext(boot.base+'/'+t.id)}">查看</a><a aria-label="复制 ${esc(t.name)}" href="${withListContext(boot.base+'/new?copy='+t.id)}">复制</a><button type="button" class="dc-list-share" aria-label="分享 ${esc(t.name)}" title="复制任务卡" data-action="list-share-task" data-id="${esc(t.id)}">分享</button></div></td>
    </tr>`).join('')}</tbody></table></div><footer class="dc-footer"><span>共 ${filtered.length} 个任务 · 每页 8 条</span><div class="dc-page-buttons"><button data-action="list-prev" aria-label="上一页" ${list.page===1?'disabled':''}>‹</button><span>${list.page} / ${pageCount}</span><button data-action="list-next" aria-label="下一页" ${list.page===pageCount?'disabled':''}>›</button></div></footer>` : empty('没有匹配的采集任务', '试试调整筛选条件，或创建新的采集任务。', `<button class="dc-btn small" data-action="reset-filters">清空筛选</button>`);
  }
  function defaultForm() {
    return {name:'',project:'',priority:3,expected_hours:null,spec_id:'',spec_name:'',source:params.get('source')==='udas'?'udas':'robot',mode:'NORMAL',description:'',spec_url:params.get('spec')==='example'?specLink.url:'',location:'',tags:[],prompts:[],checkpoint:'',generalization:[]};
  }
  function fromTask(t, copying = false) {
    const f = Object.fromEntries(['name','project','source','mode','description','spec_url','location','tags','prompts','checkpoint','generalization'].map(k=>[k,clone(t[k])]));
    Object.assign(f,{priority:t.priority??6,expected_hours:t.expected_hours??null,spec_id:t.spec_id||'',spec_name:t.spec_name||''});
    if (copying) f.name = (f.name.slice(0,92) + ' · 副本');
    f.mode ||= 'NORMAL';
    return f;
  }
  const isDagger = () => form.source === 'robot' && form.mode === 'DAGGER';
  const locked = () => Boolean(task);
  const editableFields = ['description','spec_url','spec_id','spec_name','tags','generalization','priority','expected_hours'];
  function specControl() {
    return `<div class="dc-spec-picker"><div class="dc-spec-link-row">${input('spec_url','粘贴飞书规范链接',2048)}<button type="button" class="dc-btn" data-action="pick-spec">选择已有规范</button>${specLink.button(form.spec_url)}</div>${form.spec_id?`<div class="dc-selected-spec">${esc(form.spec_name)}<button type="button" class="dc-link" data-action="clear-spec">移除</button></div>`:''}</div>`;
  }
  async function pickSpec() {
    openDialog('选择采集规范', '<div role="status">正在加载…</div>');
    try {
      specs=(await request('/specs')).specs;
      if(!dialog.open)return;
      dialog.querySelector('.dc-dialog-body').innerHTML=`<div class="dc-spec-library-head"><input class="dc-input" id="dc-spec-search" placeholder="搜索规范名称" aria-label="搜索规范名称"><a class="dc-link" href="/data/rules?category=collection" target="_blank" rel="noopener">管理规范 ↗</a></div><div id="dc-spec-options"></div>`;
      const render=()=>{
        const q=dialog.querySelector('#dc-spec-search').value.trim().toLowerCase();
        const rows=specs.filter(s=>s.name.toLowerCase().includes(q));
        dialog.querySelector('#dc-spec-options').innerHTML=rows.length?rows.map(s=>`<button type="button" class="dc-spec-option" data-action="select-spec" data-id="${esc(s.id)}"><strong>${esc(s.name)}</strong><span>${esc(s.url)}</span></button>`).join(''):'<div class="dc-empty">暂无匹配规范，可直接填写飞书链接</div>';
      };
      dialog.querySelector('#dc-spec-search').addEventListener('input',render);render();dialog.querySelector('#dc-spec-search').focus();
    } catch(error) {dialog.querySelector('.dc-dialog-body').innerHTML=`<p role="alert">${esc(error.message)}</p><button type="button" class="dc-btn" data-action="pick-spec">重试</button>`;}
  }
  function errorFor(key) { return `<div class="dc-error" id="dc-error-${key}" data-error="${key}">${esc(formErrors[key] || '')}</div>`; }
  function field(key, title, control, required = false, full = false, help = '') {
    return `<div class="dc-field ${full?'full':''}" data-field="${key}"><label class="dc-label" for="dc-${key}">${required?'<span class="dc-required">*</span>':''}${title}${required?'':'<span class="dc-optional">选填</span>'}</label>${control}${errorFor(key)}</div>`;
  }
  function input(key, placeholder = '', maximum = 200) {
    return `<input class="dc-input" id="dc-${key}" name="${key}" data-form="${key}" value="${esc(form[key])}" placeholder="${esc(placeholder)}" maxlength="${maximum}" aria-invalid="${!!formErrors[key]}">`;
  }
  function renderForm() {
    const previous=root.querySelector('#dc-create-form'),scroller=root.querySelector('.dc-processing-content');
    const oldFocus=document.activeElement,position=scroller?.scrollTop||0,windowPosition=scrollY;
    const ancestorPositions=[];for(let el=root.parentElement;el;el=el.parentElement)ancestorPositions.push([el,el.scrollTop]);
    let focusSelector=null;
    if(previous?.contains(oldFocus)){
      if(oldFocus.id)focusSelector='#'+CSS.escape(oldFocus.id);
      else if(oldFocus.dataset.g)focusSelector=`[data-g="${oldFocus.dataset.g}"][data-index="${oldFocus.dataset.index}"]`;
      else if(oldFocus.dataset.form)focusSelector=`[data-form="${oldFocus.dataset.form}"][value="${oldFocus.value}"]`;
      else if(oldFocus.dataset.action)focusSelector=`[data-action="${oldFocus.dataset.action}"]${oldFocus.dataset.index?`[data-index="${oldFocus.dataset.index}"]`:''}${oldFocus.dataset.id?`[data-id="${oldFocus.dataset.id}"]`:''}`;
    }
    const taskType = form.source === 'udas' ? ' UDAS 采集' : '机器人采集';
    const title = task ? `编辑${taskType}任务` : params.has('copy') ? `复制${taskType}任务` : `新建${taskType}任务`;
    ready(pageHead(title, '', '', true) + `
      ${draft?`<div class="dc-draft-banner" id="dc-draft-banner"><span>此页面有一份本地草稿${draft.savedAt?` · ${date(draft.savedAt)}`:''}，是否恢复？</span><div class="dc-row"><button class="dc-link" data-action="restore-draft">恢复草稿</button><button class="dc-link" data-action="discard-draft">忽略并删除</button></div></div>`:''}
      <form id="dc-create-form" novalidate>
        <div class="dc-form-error" id="dc-form-error" role="alert">${Object.keys(formErrors).length?'请检查下方标红的配置。':''}</div>
        <div class="dc-processing-layout"><div class="dc-processing-content"><section class="dc-processing-section" id="dc-basic-section"><div class="dc-section-head"><h2>基本信息</h2></div><div class="dc-fields">
            ${field('name','任务名称',input('name','例如：饮茶场景 · 饮料取放补采',100),true)}
            ${field('project','所属项目',`<select id="dc-project" class="dc-select" data-form="project" aria-invalid="${!!formErrors.project}">${option('','请选择项目',form.project)}${boot.projects.map(p=>option(p.id,p.name,form.project)).join('')}</select>`,true)}
            ${form.source==='robot'?field('mode','机器人采集模式',`<select id="dc-mode" class="dc-select" data-form="mode" ${locked()?'disabled':''}>${option('NORMAL','NORMAL',form.mode)}${option('DAGGER','DAGGER',form.mode)}</select>`,true):field('location','采集地点',input('location','例如：北京 · 家居采集场'),false)}
            ${field('priority','优先级',`<select class="dc-select" id="dc-priority" data-form="priority" aria-invalid="${!!formErrors.priority}">${[[9,'高'],[6,'中'],[3,'低']].map(([value,label])=>option(value,label,priorityLabel(form.priority)===label?value:null)).join('')}</select>`,true)}
            ${field('expected_hours','预期采集时长（小时）',`<input class="dc-input" id="dc-expected_hours" data-form="expected_hours" type="number" min="0.000001" max="1000000" step="any" placeholder="输入目标小时数" value="${esc(form.expected_hours??'')}">`)}
          </div></section>
          <section class="dc-processing-section" id="dc-requirements-section"><div class="dc-section-head"><h2>采集要求</h2></div><div class="dc-fields">
            ${field('description','任务说明',`<textarea class="dc-textarea" id="dc-description" data-form="description" maxlength="5000" aria-invalid="${!!formErrors.description}">${esc(form.description)}</textarea>`,true,true)}
            ${field('spec_url','采集规范',specControl(),false,true,'')}
            ${field('tags','任务标签',window.CollectionTagPicker.render(form.tags),false,true)}
          </div></section>
          ${form.source==='robot'?`<section class="dc-processing-section" id="dc-model-section"><div class="dc-section-head"><h2>采集配置</h2></div>
            ${isDagger()?`<div class="dc-fields">${field('prompts',`任务提示词 <span class="dc-prompt-selected-count">（已选择${form.prompts.length}组）</span>`,window.CollectionPromptPicker.render(form.prompts),true,true)}
              ${field('checkpoint','Checkpoint',`<button type="button" id="dc-checkpoint" class="dc-input dc-between" data-action="pick-checkpoint" style="text-align:left;cursor:pointer"><span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0" class="${form.checkpoint?'':'dc-muted'}">${esc(form.checkpoint?checkpoint(form.checkpoint):'选择可用的模型 Checkpoint')}</span>${icon('chevron')}</button>`,true,true,'使用 Demo 已有的可用模型资产；实际设备推理接入待联调。')}</div>`:''}
            <section class="dc-generalization" aria-labelledby="dc-generalization-title"><div class="dc-generalization-head"><h3 id="dc-generalization-title">位置泛化统计</h3><span class="dc-optional">选填</span></div><div class="dc-generalization-body"><div class="dc-generalization-scroll"><table class="dc-generalization-table" aria-label="位置泛化统计配置"><thead><tr><th>${isDagger()?'对应 Prompt':'统计项名称'}</th><th>取点规则</th><th>目标泛化区域</th><th>端侧调整</th><th>算子</th><th>操作</th></tr></thead><tbody id="dc-generalization">${form.generalization.length?form.generalization.map(renderGeneralization).join(''):`<tr><td colspan="6" class="dc-generalization-empty">${isDagger()&&!form.prompts.length?'请先选择任务提示词，再添加统计项':'尚未添加统计项'}</td></tr>`}</tbody></table></div><div class="dc-generalization-actions"><button type="button" class="dc-btn small" data-action="add-generalization" ${isDagger()&&!form.prompts.some(p=>!form.generalization.some(g=>g.prompt_id===p.id))?'disabled':''}>${icon('plus')}新增统计项</button></div>${errorFor('generalization')}</div></section>
          </section>`:''}
        </div></div>
        <footer class="dc-form-bottom"><span></span><div class="dc-row"><a class="dc-btn" href="${task?withListContext(boot.base+'/'+task.id):esc(listReturnHref())}">取消</a><button type="button" class="dc-btn" data-action="save-draft">保存本地草稿</button><button class="dc-btn primary" type="submit" id="dc-submit">${task?'保存修改':'创建任务'}</button></div></footer>
      </form>`);
    window.CollectionTagPicker.mount(document.getElementById('dc-tags'),form.tags,tags=>{form.tags=tags;clearFormError('tags');dirty=true;});
    window.CollectionPromptPicker.mount(task?null:document.getElementById('dc-prompts'),form.prompts,boot.prompts,prompts=>{
      form.prompts=clone(prompts);
      form.generalization=form.generalization.filter(g=>prompts.some(p=>p.id===g.prompt_id));
      clearFormError('prompts');clearFormError('generalization');dirty=true;renderForm();
    });
    if(task){
      root.querySelectorAll('[data-field]').forEach(field=>{
        if(editableFields.includes(field.dataset.field))return;
        field.dataset.readonly='true';
        field.querySelectorAll('input,textarea,select,button').forEach(control=>{
          if(control.matches('input:not([type="radio"]),textarea'))control.readOnly=true;
          else control.disabled=true;
          control.setAttribute('aria-readonly','true');
        });
      });
      root.querySelectorAll('#dc-prompts button,#dc-prompts .dc-prompt-create').forEach(el=>el.remove());
    }
    root.querySelectorAll('.dc-field').forEach(el=>{
      const key=el.dataset.field,label=el.querySelector('.dc-label'),control=document.getElementById('dc-'+key);
      label.id='dc-label-'+key;
      if(control?.matches('input,select,textarea,button')){
        control.setAttribute('aria-describedby','dc-error-'+key);
        if(label.querySelector('.dc-required')&&control.matches('input,select,textarea'))control.setAttribute('aria-required','true');
      }else if(control){
        label.removeAttribute('for');
        control.setAttribute('role','group');
        control.setAttribute('aria-labelledby',label.id);
        control.setAttribute('aria-describedby','dc-error-'+key);
      }
    });
    if(previous){
      const focus=focusSelector&&root.querySelector(focusSelector);
      (focus||root.querySelector('[data-action="pick-prompts"],[data-action="add-generalization"]'))?.focus({preventScroll:true});
      root.querySelector('.dc-processing-content').scrollTop=position;
      ancestorPositions.forEach(([el,top])=>{el.scrollTop=top;});
      window.scrollTo(scrollX,windowPosition);
    }
  }
  function renderGeneralization(g, i) {
    const name=isDagger()?form.prompts.find(p=>p.id===g.prompt_id)?.name||g.name:g.name;
    const operator=boot.operators.find(o=>o.id===g.operator)?.name||g.operator;
    const region=`${g.plane} · ${[...g.plane].map(axis=>`${axis}：${centimeters(g.bounds[axis]?.[0])} 至 ${centimeters(g.bounds[axis]?.[1])} cm`).join(' · ')}`;
    const regionCompact=`${g.plane} · ${[...g.plane].map(axis=>`${axis} ${centimeters(g.bounds[axis]?.[0])}~${centimeters(g.bounds[axis]?.[1])}`).join(' · ')} cm`;
    return `<tr class="dc-g-card" data-g-card="${i}"><td data-label="${isDagger()?'对应 Prompt':'统计项名称'}"><span class="dc-g-summary-name" title="${esc(name)}">${esc(name)}</span></td>
      <td data-label="取点规则">${g.arm==='left'?'左臂':'右臂'} · ${g.event==='close'?'夹爪闭合':'夹爪打开'}</td>
      <td data-label="目标泛化区域"><span class="dc-g-summary-region" title="${esc(region)}">${esc(regionCompact)}</span></td>
      <td data-label="端侧调整">${g.allow_adjust?'允许调整':'不允许'}</td>
      <td data-label="算子"><span class="dc-g-summary-name" title="${esc(operator)}">${esc(operator)}</span></td>
      <td data-label="操作"><div class="dc-g-summary-actions"><button type="button" class="dc-link" data-action="edit-generalization" data-index="${i}" aria-label="编辑统计项 ${i+1}">编辑</button><button type="button" class="dc-link" data-action="remove-generalization" data-index="${i}" aria-label="删除统计项 ${i+1}">删除</button></div></td></tr>`;
  }
  function centimeters(value) { return value===''||value==null?'':Number((value*100).toPrecision(12)); }
  function openGeneralizationEditor(index=-1) {
    if(index<0&&form.generalization.length>=20){toast('最多配置 20 个统计项');return;}
    const prompt=isDagger()?form.prompts.find(p=>!form.generalization.some(g=>g.prompt_id===p.id)):null;
    if(index<0&&isDagger()&&!prompt)return;
    generalizationEditor={index,errors:{},value:index>=0?clone(form.generalization[index]):{name:'',prompt_id:prompt?.id||'',arm:'left',event:'close',operator:boot.operators[0].id,plane:'XY',bounds:{X:['',''],Y:['','']},allow_adjust:true}};
    openDialog(index<0?'新增泛化统计项':'编辑泛化统计项','',`<button type="button" class="dc-btn" data-action="close-dialog">取消</button><button type="submit" form="dc-generalization-form" class="dc-btn primary">保存配置</button>`);
    dialog.classList.add('dc-generalization-dialog');
    renderGeneralizationEditor();
    dialog.querySelector('[data-g="name"],[data-g="prompt_id"]')?.focus();
  }
  function renderGeneralizationEditor(focusKey) {
    const {index,value:g,errors}=generalizationEditor;
    const inputField=(key,label,control,full=false,required=false)=>`<div class="dc-g-field${full?' full':''}"><label class="dc-label" for="dc-g-${key}">${required?'<span class="dc-required">*</span>':''}${label}</label>${control}<p class="dc-error" data-g-error="${key}" ${errors[key]?'':'hidden'}>${esc(errors[key]||'')}</p></div>`;
    const select=(key,choices)=>`<select id="dc-g-${key}" class="dc-select" data-g="${key}" aria-invalid="${!!errors[key]}" aria-describedby="dc-g-error-${key}">${choices}</select>`;
    const identity=isDagger()?inputField('prompt_id','对应 Prompt',select('prompt_id',form.prompts.filter(p=>!form.generalization.some((x,i)=>i!==index&&x.prompt_id===p.id)).map(p=>option(p.id,p.name,g.prompt_id)).join('')),true,true):inputField('name','统计项名称',`<input id="dc-g-name" class="dc-input" data-g="name" maxlength="80" value="${esc(g.name)}" placeholder="请输入统计项名称" aria-invalid="${!!errors.name}">`,true,true);
    const operators=boot.operators.filter(o=>o.arm===g.arm&&o.event===g.event);
    dialog.querySelector('.dc-dialog-body').innerHTML=`<form id="dc-generalization-form" novalidate><div class="dc-g-dialog-fields">${identity}
      ${inputField('arm','泛化对象',select('arm',option('left','左臂',g.arm)+option('right','右臂',g.arm)))}
      ${inputField('event','泛化统计事件',select('event',option('close','夹爪闭合',g.event)+option('open','夹爪打开',g.event)))}
      ${inputField('operator','算子',select('operator',operators.map(o=>option(o.id,o.name,g.operator)).join('')),true)}
      </div><section class="dc-g-dialog-region"><h3>目标泛化区域</h3><div class="dc-g-dialog-fields">
      ${inputField('plane','范围类型',select('plane',['XY','XZ','YZ','XYZ'].map(p=>option(p,p==='XYZ'?'三维空间 XYZ':`平面 ${p}`,g.plane)).join('')),true)}
      ${[...g.plane].map(axis=>[0,1].map(side=>inputField(axis+side,`${axis} ${side?'最大':'最小'}值（cm）`,`<input id="dc-g-${axis}${side}" class="dc-input" type="number" step="any" inputmode="decimal" data-bound="${axis}" data-side="${side}" value="${esc(centimeters(g.bounds[axis]?.[side]))}" aria-invalid="${!!errors[axis+side]}" aria-describedby="dc-g-error-${axis}${side}">`)).join('')).join('')}
      </div></section><label class="dc-g-dialog-adjust"><input type="checkbox" data-g="allow_adjust" ${g.allow_adjust?'checked':''}>允许端侧调整目标泛化区域</label></form>`;
    dialog.querySelectorAll('[data-g-error]').forEach(el=>el.id='dc-g-error-'+el.dataset.gError);
    if(focusKey)dialog.querySelector(`[data-g="${focusKey}"]`)?.focus({preventScroll:true});
  }
  function saveGeneralizationEditor() {
    const {index,value:g}=generalizationEditor,errors={};
    if(isDagger()){
      if(!form.prompts.some(p=>p.id===g.prompt_id)||form.generalization.some((x,i)=>i!==index&&x.prompt_id===g.prompt_id))errors.prompt_id='请选择尚未配置统计项的 Prompt';
      g.name=form.prompts.find(p=>p.id===g.prompt_id)?.name||'';
    }else if(!g.name.trim()||g.name.trim().length>80)errors.name='请填写统计项名称（最多 80 字）';
    if(!boot.operators.some(o=>o.id===g.operator&&o.arm===g.arm&&o.event===g.event))errors.operator='请选择与对象和事件匹配的算子';
    for(const axis of g.plane){
      const pair=g.bounds[axis]||['',''];
      pair.forEach((v,side)=>{if(v===''||!Number.isFinite(v))errors[axis+side]='请填写有效数值';});
      if(!errors[axis+'0']&&!errors[axis+'1']&&pair[0]>=pair[1])errors[axis+'1']='最大值须大于最小值';
    }
    generalizationEditor.errors=errors;
    if(Object.keys(errors).length){renderGeneralizationEditor();const invalid=dialog.querySelector('[aria-invalid="true"]');invalid?.focus();return;}
    const saved=clone(g);saved.name=saved.name.trim();saved.bounds=Object.fromEntries([...saved.plane].map(axis=>[axis,saved.bounds[axis]]));
    if(index<0)form.generalization.push(saved);else form.generalization[index]=saved;
    dirty=true;clearFormError('generalization');closeDialog();renderForm();
    modalOrigin=root.querySelector(`[data-action="edit-generalization"][data-index="${index<0?form.generalization.length-1:index}"]`);
    modalOrigin?.focus({preventScroll:true});
  }
  function clearGeneralizationError(key) {
    if(!generalizationEditor)return;
    delete generalizationEditor.errors[key];
    const control=dialog.querySelector('#dc-g-'+key),error=dialog.querySelector(`[data-g-error="${key}"]`);
    control?.setAttribute('aria-invalid','false');
    if(error){error.hidden=true;error.textContent='';}
  }
  function payload() {
    const data={...form, mode:form.source==='udas'?'':form.mode, checkpoint:isDagger()?form.checkpoint:'', prompt_ids:isDagger()?form.prompts.map(p=>p.id):[],
      generalization:form.source==='robot'?form.generalization.map(g=>({...g,bounds:Object.fromEntries([...g.plane].map(a=>[a,g.bounds[a]]))})):[]};
    data.priority=Number(form.priority);
    data.expected_hours=form.expected_hours==null||form.expected_hours===''?null:Number(form.expected_hours);
    return task?{...Object.fromEntries(editableFields.map(key=>[key,data[key]])),revision:task.revision}:data;
  }
  function showErrors(errors, message = '请检查标红的配置后重试。') {
    formErrors = errors || {};
    const alert = document.getElementById('dc-form-error'); alert.textContent = message;
    document.querySelectorAll('[data-error]').forEach(el=>el.textContent=errors?.[el.dataset.error]||'');
    document.querySelectorAll('[data-form]').forEach(el=>el.setAttribute('aria-invalid',!!errors?.[el.dataset.form]));
    for(const key of ['prompts','checkpoint'])document.getElementById('dc-'+key)?.setAttribute('aria-invalid',!!errors?.[key]);
    const first = [...root.querySelectorAll('[data-field]')].find(el=>errors?.[el.dataset.field]) || alert;
    const section=first.closest('.dc-processing-section');section?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
    first.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});
    first.querySelector('input,textarea,select,button')?.focus({preventScroll:true});
  }
  function clearFormError(key) {
    if (!formErrors[key]) return;
    delete formErrors[key];
    document.querySelectorAll(`[data-error="${key}"]`).forEach(el=>el.textContent='');
    document.querySelectorAll(`[data-form="${key}"]`).forEach(el=>el.setAttribute('aria-invalid','false'));
    document.getElementById('dc-'+key)?.setAttribute('aria-invalid','false');
    if (!Object.keys(formErrors).length) document.getElementById('dc-form-error').textContent='';
  }
  async function submitForm(event) {
    event.preventDefault(); if (busy) return;
    busy = true; document.getElementById('dc-submit').disabled=true; document.getElementById('dc-submit').textContent='正在保存…';
    try {
      const body=payload();let headers={};
      if(!task){
        const fingerprint=JSON.stringify(body);
        if(!createAttempt||createAttempt.fingerprint!==fingerprint){createAttempt={fingerprint,key:crypto.randomUUID()};try{sessionStorage.setItem(createAttemptKey,JSON.stringify(createAttempt));}catch(_){}}
        headers={'Idempotency-Key':createAttempt.key};
      }
      const result = await request(task?`/tasks/${task.id}`:'/tasks', task?'PATCH':'POST', body, headers);
      dirty=false; try { localStorage.removeItem(draftKey); } catch (_) { /* storage may be disabled */ }
      if(!task){createAttempt=null;try{sessionStorage.removeItem(createAttemptKey);}catch(_){}
        location.assign(contextualPath(boot.base+'/'+result.task.id+'?created=1'));return;
      }
      location.assign(contextualPath(boot.base+'/'+result.task.id+'?saved='+(result.unchanged?'unchanged':'1')));
    } catch (error) {
      showErrors(error.errors, error.status===409?'此任务已在其他页面更新。你的输入已保留，请先保存本地草稿，再刷新核对。':error.errors?'请检查标红的配置后重试。':error.message);
    } finally { busy=false; const button=document.getElementById('dc-submit'); if(button){button.disabled=false;button.textContent=task?'保存修改':'创建任务';} }
  }
  function openDialog(title, body, footer) {
    releaseRecordVideo();
    window.CollectionTrajectory?.release();
    if(!dialog.open)modalOrigin=document.activeElement;
    dialog.classList.remove('dc-share-dialog','dc-generalization-dialog','dc-trajectory-dialog');
    dialog.innerHTML=`<header class="dc-dialog-head"><h2 id="dc-dialog-title">${esc(title)}</h2><button class="dc-remove" data-action="close-dialog" aria-label="关闭弹窗">×</button></header><div class="dc-dialog-body">${body}</div><footer class="dc-dialog-foot">${footer || '<button class="dc-btn" data-action="close-dialog">关闭</button>'}</footer>`;
    dialog.showModal();
  }
  function closeDialog() { releaseRecordVideo();window.CollectionTrajectory?.release();dialog.close(); }
  dialog.addEventListener('close',()=>{if(dialog.open)return;releaseRecordVideo();window.CollectionTrajectory?.release();generalizationEditor=null;dialog.classList.remove('dc-generalization-dialog');applyPendingRefresh();if(modalOrigin?.isConnected)modalOrigin.focus({preventScroll:true});});
  function openCheckpointPicker() {
    checkpointSelection=form.checkpoint;
    openDialog('选择 Checkpoint', `<label class="dc-search" style="display:block;width:100%">${icon('search')}<input class="dc-input" id="dc-checkpoint-search" placeholder="搜索名称或 ID" aria-label="搜索 Checkpoint"></label><div id="dc-checkpoint-options" class="dc-picker-items"></div>`,`<button class="dc-btn" data-action="close-dialog">取消</button><button class="dc-btn primary" data-action="confirm-checkpoint">确认选择</button>`);
    renderCheckpointOptions(''); document.getElementById('dc-checkpoint-search').focus();
  }
  function renderCheckpointOptions(q) {
    const checkpoints=boot.checkpoints.filter(c=>c.status==='cached'&&`${c.id} ${c.name}`.toLowerCase().includes(q.toLowerCase()));
    document.getElementById('dc-checkpoint-options').innerHTML=checkpoints.length?checkpoints.map(c=>`<label class="dc-picker-option"><input type="radio" name="checkpoint-choice" data-checkpoint="${c.id}" ${checkpointSelection===c.id?'checked':''}><span><strong style="overflow-wrap:anywhere">${esc(c.name)}</strong><p>ID ${esc(c.id)} · 可用</p></span></label>`).join(''):empty('没有匹配的 Checkpoint','试试其他关键词。');
  }
  async function copyText(text, message = '已复制') {
    try { await navigator.clipboard.writeText(text); toast(message); }
    catch (_) { openDialog('复制内容', `<p class="dc-help" style="margin-bottom:12px">浏览器未授予剪贴板权限，请选中以下内容手动复制。</p><textarea class="dc-textarea" readonly style="width:100%;height:230px">${esc(text)}</textarea>`); dialog.querySelector('textarea').select(); }
  }
  const shareLink = t => `${location.origin}${boot.base}/${encodeURIComponent(t.id)}#config`;
  const shareModel = t => window.DCShareCard.model(t,{project:project(t.project),mode:modeName(t),link:shareLink(t)});
  function shareText(t) {
    return window.DCShareCard.text(shareModel(t));
  }
  async function shareFromList(button) {
    if(busy)return;busy=true;button.disabled=true;
    const id=button.dataset.id;
    try {
      const result=await request(`/tasks/${encodeURIComponent(id)}/collection-check`);
      tasks=tasks.map(t=>t.id===id?result.task:t);
      renderListResults();
      root.querySelector(`[data-action="list-share-task"][data-id="${id}"]`)?.focus({preventScroll:true});
      await copyText(shareText(result.task),'任务卡已复制，可粘贴到飞书');
    } catch(error){toast(`未能获取最新任务，未复制。${error.message}`);}
    finally{busy=false;button.disabled=false;}
  }
  async function openShareCard(checkedResult = null) {
    if(busy)return;busy=true;
    try{
      const result=checkedResult||await request(`/tasks/${encodeURIComponent(task.id)}/collection-check`);
      const changed=task.revision!==result.task.revision;
      task=result.task;
      if(changed&&view==='detail'){renderDetail();root.querySelector('[data-action="share-task"]')?.focus({preventScroll:true});}
      const message=result.reason==='closed'?'任务已结束，不能开始新录制':'当前任务开放';
      const preview=esc(shareText(task)).replace(`任务 ID：${esc(task.id)}`,`任务 ID：<span class="dc-share-id">${esc(task.id)}</span>`);
      openDialog('任务卡', `<div class="dc-note amber" data-collection-check="${result.reason}" role="status" ${result.reason==='ready'?'hidden':''}>${icon('info')}<span>${esc(message)}</span></div>
        <article class="dc-share-card"><div class="dc-share-text">${preview}</div></article>
        <div class="dc-share-live-links">${task.spec_url?`<a href="${esc(task.spec_url)}" target="_blank" rel="noopener noreferrer">打开规范 ↗</a>`:''}<button class="dc-link" data-action="copy-task-id">复制 ID</button><button class="dc-link" data-action="check-latest-task">刷新</button></div>`, `<button class="dc-btn" data-action="copy-task-link">复制链接</button><button class="dc-btn primary" data-action="copy-task-card">${icon('copy')}复制分享内容</button>`);
      dialog.classList.add('dc-share-dialog');
    }catch(error){toast(error.message);}finally{busy=false;}
  }
  async function copyShareCard(linkOnly=false) {
    if(busy)return;busy=true;
    const buttons=[...dialog.querySelectorAll('button[data-action]')].filter(b=>b.dataset.action!=='close-dialog');
    buttons.forEach(b=>b.disabled=true);
    try {
      const result=await request(`/tasks/${encodeURIComponent(task.id)}/collection-check`);
      if(!dialog.open)return;
      const changed=task.revision!==result.task.revision;
      task=result.task;
      if(changed){if(view==='detail')renderDetail();busy=false;await openShareCard(result);busy=true;}
      await copyText(linkOnly?shareLink(task):shareText(task));
    } catch(error){toast(`未能获取最新任务，未复制。${error.message}`);}
    finally{busy=false;buttons.forEach(b=>b.disabled=false);}
  }
  function renderDetail() {
    const previousScroller=detailScroller();
    if(previousScroller)detailScroll[activeTab]=previousScroller.scrollTop;
    ready(`<header class="dc-detail-header">
      <div class="dc-detail-title-row"><div class="dc-detail-identity"><div class="dc-detail-heading-line"><div class="dc-detail-breadcrumb"><a class="dc-back" href="${esc(listReturnHref())}">${icon('back')}返回</a></div><h1 title="${esc(task.name)}">${esc(task.name)}</h1></div></div><div class="dc-head-actions"><span data-spec-shortcut>${task.spec_url?specLink.button(task.spec_url):''}</span><button class="dc-btn" data-action="share-task">${icon('copy')}任务卡</button><a class="dc-btn" href="${withListContext(boot.base+'/new?copy='+task.id)}">复制</a><a class="dc-btn" href="${withListContext(boot.base+'/'+task.id+'/edit')}">${icon('edit')}编辑</a><button class="dc-btn ${task.status==='open'?'danger':'primary'}" data-action="change-state">${task.status==='open'?'结束采集':'重新开放'}</button></div></div>
      <div class="dc-detail-info-row">${detailInfo(task)}</div>
    </header>` + `
      <section class="dc-detail-shell dc-panel"><div class="dc-tabs" role="tablist" aria-label="采集任务详情">${[['records','采集数据'],['processing','关联处理'],['config','任务要求与配置'],['activity','日志']].map(([id,label])=>`<button class="dc-tab" id="dc-detail-tab-${id}" role="tab" aria-controls="dc-detail-body" data-action="detail-tab" data-value="${id}" aria-selected="${activeTab===id}">${label}</button>`).join('')}<div class="dc-detail-refresh">${refreshControl()}</div></div><div id="dc-detail-body" role="tabpanel" aria-labelledby="dc-detail-tab-${activeTab}" tabindex="0"></div></section>
`);
    renderDetailBody();
    detailScroller().scrollTop=detailScroll[activeTab];
    updateRefreshControl();
  }
  function detailScroller() {
    return activeTab==='records' ? root.querySelector('#dc-record-results .dc-table-wrap') || document.getElementById('dc-detail-body') : document.getElementById('dc-detail-body');
  }
  function selectDetailTab(value, updateUrl = true) {
    if(!detailTabs.includes(value)||value===activeTab)return;
    const body=document.getElementById('dc-detail-body');
    detailScroll[activeTab]=detailScroller().scrollTop;
    activeTab=value;
    root.querySelectorAll('[data-action="detail-tab"]').forEach(button=>{
      const selected=button.dataset.value===activeTab;
      button.setAttribute('aria-selected',String(selected));button.tabIndex=selected?0:-1;
    });
    body.setAttribute('aria-labelledby','dc-detail-tab-'+activeTab);
    renderDetailBody();detailScroller().scrollTop=detailScroll[activeTab];
    if(updateUrl)history.replaceState(null,'',location.pathname+location.search+'#'+activeTab);
  }
  function renderDetailBody() {
    releaseRecordVideo();
    const el=document.getElementById('dc-detail-body');
    el.dataset.tab=activeTab;
    if(activeTab==='records'){
      el.innerHTML=`<div class="dc-detail-toolbar dc-record-filters" role="search" aria-label="搜索和筛选采集数据">${[['id','ID搜索'],['device','设备搜索'],['operator','采集员搜索']].map(([key,label])=>`<label class="dc-search">${icon('search')}<input class="dc-input" type="search" id="dc-record-${key}" data-record-filter="${key}" placeholder="${label}" aria-label="${label}" value="${esc(recordFilters[key])}"></label>`).join('')}<select class="dc-select dc-upload-filter" data-record-filter="upload" aria-label="上传状态">${[['uploaded','已上传'],['uploading','上传中'],['failed','上传失败'],['all','全部上传状态']].map(([key,label])=>option(key,label,recordFilters.upload)).join('')}</select><select class="dc-select dc-conclusion-filter" data-record-filter="conclusion" aria-label="采集结论">${[['','全部采集结论'],['success','成功'],['failure','失败']].map(([key,label])=>option(key,label,recordFilters.conclusion)).join('')}</select><button type="button" class="dc-btn dc-record-reset" data-action="reset-record-filters" aria-label="重置采集数据筛选" title="重置筛选">${icon('reset')}</button></div><div id="dc-record-results"></div>`;
      renderRecords();
    }else if(activeTab==='processing'){
      renderProcessingTab(el);loadProcessingLinks();
    }else if(activeTab==='activity'){
      el.innerHTML=`<div class="dc-detail-content dc-activity-content"><h2>日志</h2><ol class="dc-timeline">${[...task.events].reverse().map(e=>`<li><div class="dc-between"><strong>${esc(e.title)}</strong><small>${esc(fullDate(e.at))}</small></div><p>${esc(e.actor)} · ${esc(e.detail)}</p>${renderLogChanges(e.changes)}</li>`).join('')}</ol></div>`;
    }else{
      renderTaskConfiguration(el);
    }
  }
  function renderProcessingTab(el){
    const summary=processingSummary();
    if(processingError){el.innerHTML=`<div class="dc-processing-empty"><p role="alert">关联处理任务加载失败：${esc(processingError)}</p><button class="dc-btn" data-action="retry-processing">重试</button></div>`;return;}
    if(processingLoading&&!processingJobs.length){el.innerHTML='<div class="dc-processing-loading">正在加载关联处理任务…</div>';return;}
    el.innerHTML=`<div class="dc-detail-content dc-processing-content-tab"><div class="dc-processing-tab-head"><div><h2>关联处理</h2></div><button class="dc-btn primary" data-action="create-processing">+ 创建处理任务</button></div>
      ${processingJobs.length?`<div class="dc-processing-summary"><div><span>关联处理任务</span><strong>${summary.count}</strong></div><div><span>处理中</span><strong>${summary.active}</strong></div><div><span>已完成</span><strong>${summary.completed}</strong></div><div><span>涉及数据</span><strong>${summary.records}</strong></div></div><div class="dc-processing-table-wrap"><table class="dc-table dc-processing-table"><thead><tr><th>处理任务</th><th>类型</th><th>数据范围</th><th>处理进度</th><th>状态</th><th>操作</th></tr></thead><tbody>${processingJobs.map(job=>`<tr><td><a class="dc-processing-task-name" href="/data/processing-tasks?linked=${encodeURIComponent(job.id)}">${esc(job.name)}</a><span class="dc-processing-task-id">${esc(job.id)}</span></td><td>${esc(Object.keys(job.stages).join(' / '))}</td><td><strong>${job.selected_count}</strong> / ${task.metrics.uploaded} 已纳入</td><td>${job.stage_progress.map(progress=>`<div class="dc-processing-progress"><span>${esc(progress.stage)}</span><i><b style="width:${progress.total?Math.round(progress.done/progress.total*100):0}%"></b></i><em>${progress.done}/${progress.total}</em></div>`).join('')}</td><td><span class="dc-badge ${processingStatusTone(job.status)}">${esc(job.status_label||processingStatusLabel(job.status))}</span>${job.new_count?`<small class="dc-processing-new-count">+${job.new_count} 条待纳入</small>`:''}</td><td><div class="dc-processing-row-actions"><a class="dc-link" href="/data/processing-tasks?linked=${encodeURIComponent(job.id)}">查看</a></div></td></tr>`).join('')}</tbody></table></div>`:'<div class="dc-processing-empty"><h3>还没有关联处理任务</h3></div>'}</div>`;
  }
  // 【新】日志描述平台内的修改事实，不作为飞书规范或录制执行版本证明。
  function renderLogChanges(changes) {
    if(!Array.isArray(changes)||!changes.length)return '';
    const value=(field,input)=>{
      if(field==='tags')return Array.isArray(input)&&input.length?input.join('、'):'—';
      if(field==='priority')return typeof input==='number'?priorityLabel(input):'—';
      if(field==='expected_hours')return typeof input==='number'?`${input} 小时`:'—';
      if(field==='generalization')return Array.isArray(input)&&input.length?input.map(g=>{
        const prompt=task.prompts?.find(p=>p.id===g.prompt_id);
        return [prompt?.name||g.name,g.arm==='left'?'左臂':'右臂',g.event==='open'?'夹爪打开':'夹爪闭合',g.operator,g.plane,...[...(g.plane||'')].map(axis=>`${axis} ${g.bounds?.[axis]?.[0]}~${g.bounds?.[axis]?.[1]} m`),g.allow_adjust?'允许调整':'不允许调整'].filter(Boolean).join(' · ');
      }).join('\n'):'—';
      return typeof input==='string'&&input?input:'—';
    };
    return `<details class="dc-log-changes"><summary>查看修改内容</summary>${changes.map(c=>`<section><h4>${esc(c.label)}</h4><dl><dt>修改前</dt><dd>${esc(value(c.field,c.before))}</dd><dt>修改后</dt><dd>${esc(value(c.field,c.after))}</dd></dl></section>`).join('')}</details>`;
  }
  function renderTaskConfiguration(el) {
    const dagger=task.source==='robot'&&task.mode==='DAGGER';
    const item=(key,label,content,full=false)=>`<div class="dc-config-field${full?' full':''}" data-config-field="${key}"><dt>${label}</dt><dd>${content}</dd></div>`;
    const prompts=task.prompts||[], generalization=task.generalization||[];
    el.innerHTML=`<div class="dc-detail-content dc-task-configuration">
      <section class="dc-configuration-section"><h3>基本信息</h3><dl class="dc-config-fields">
        ${item('name','任务名称',esc(task.name))}${item('project','所属项目',esc(project(task.project)))}
        ${item('source','采集类型',task.source==='udas'?'UDAS':'机器人采集')}
        ${task.source==='robot'?item('mode','机器人采集模式',esc(task.mode)):item('location','采集地点',esc(task.location||'—'))}
        ${item('id','任务 ID',esc(task.id))}${item('creator','创建人',esc(task.creator||'—'))}
        ${item('created_at','创建时间',esc(fullDate(task.created_at)))}
        ${item('priority','优先级',esc(priorityLabel(task.priority??6)))}
        ${item('expected_hours','预期采集时长（小时）',task.expected_hours==null?'—':esc(task.expected_hours))}
      </dl></section>
      <section class="dc-configuration-section"><h3>采集要求</h3><dl class="dc-config-fields">
        ${item('description','任务说明',`<p class="dc-description">${esc(task.description||'—')}</p>`,true)}
        ${item('spec_url','采集规范',task.spec_url?`${task.spec_name?`<strong class="dc-spec-name">${esc(task.spec_name)}</strong>`:''}${specLink.card(task.spec_url)}`:'—',true)}
        ${item('tags','任务标签',task.tags?.length?task.tags.map(t=>`<span class="dc-tag">${esc(t)}</span>`).join(''):'—',true)}
      </dl></section>
      ${task.source==='robot'?`<section class="dc-configuration-section"><h3>采集配置</h3>
        ${dagger?`<dl class="dc-config-fields">${item('prompts','任务提示词',prompts.length?prompts.map(p=>`<article class="dc-config-prompt"><div class="dc-config-prompt-heading"><strong>${esc(p.name)}</strong><span class="dc-tag">${esc(p.version)}</span></div><div class="dc-config-asset-id">${esc(p.id)}</div>${Array.isArray(p.steps)&&p.steps.length?`<ol>${p.steps.map(step=>`<li>${esc(typeof step==='string'?step:step.text??step.content??step.description??step.title??'')}</li>`).join('')}</ol>`:`<p class="dc-description">${esc(p.text||'—')}</p>`}</article>`).join(''):'—',true)}${item('checkpoint','Checkpoint',task.checkpoint?`<span>${esc(checkpoint(task.checkpoint))}</span><span class="dc-config-asset-id">${esc(task.checkpoint)}</span>`:'—',true)}</dl>`:''}
        <div class="dc-config-generalization"><h4>位置泛化统计</h4>${generalization.length?`<div class="dc-table-wrap"><table class="dc-table dc-config-generalization-table" aria-label="位置泛化统计配置"><thead><tr><th>${dagger?'对应 Prompt':'统计项名称'}</th><th>取点规则</th><th>目标泛化区域</th><th>端侧调整</th><th>算子</th></tr></thead><tbody>${generalization.map(g=>{
          const prompt=prompts.find(p=>p.id===g.prompt_id),operator=boot.operators.find(o=>o.id===g.operator);
          return `<tr><td data-label="${dagger?'对应 Prompt':'统计项名称'}">${esc(dagger?(prompt?.name||g.name||g.prompt_id||'—'):(g.name||'—'))}${dagger&&prompt?`<span class="dc-config-asset-id">${esc(prompt.id)} · ${esc(prompt.version)}</span>`:''}</td><td data-label="取点规则">${g.arm==='left'?'左臂':'右臂'}<span class="dc-config-line">夹爪${g.event==='open'?'打开':'闭合'}</span></td><td data-label="目标泛化区域"><span>${esc(g.plane)}</span>${[...(g.plane||'')].map(axis=>`<span class="dc-config-line">${axis}：${esc(g.bounds?.[axis]?.[0]??'—')} 至 ${esc(g.bounds?.[axis]?.[1]??'—')} m</span>`).join('')}</td><td data-label="端侧调整">${g.allow_adjust?'允许调整':'不允许调整'}</td><td data-label="算子">${esc(operator?.name||g.operator||'—')}${operator?`<span class="dc-config-asset-id">${esc(operator.id)}</span>`:''}</td></tr>`;
        }).join('')}</tbody></table></div>`:'<p class="dc-muted">未配置</p>'}</div>
      </section>`:''}
    </div>`;
  }
  // 【新】复用旧 Quanta 的表格内三视角快照、共用播放遮罩和 Plyr 控件。
  const recordVideoCameras=[
    {key:'head',view:'head',label:'头部',file:'head.webm'},
    {key:'left',view:'left_arm',label:'左臂',file:'left.webm'},
    {key:'right',view:'right_arm',label:'右臂',file:'right.webm'}
  ];
  let activeRecordVideo=null,recordVideoLibrary=null;
  const recordVideoPath=camera=>`/static/post_training_collection/media/${camera.file}`;
  function recordVideoSource(record,camera){
    if(record?.upload!=='uploaded')return {src:'',poster:'',demo:false};
    const videos=record?.videos;
    const source=Array.isArray(videos)?videos.find(item=>[camera.key,camera.view].includes(item?.camera)):(videos?.[camera.key]||videos?.[camera.view]);
    const explicitMedia=Object.hasOwn(record||{},'videos')||recordVideoCameras.some(c=>Object.hasOwn(record||{},`${c.view}_video_url`)||Object.hasOwn(record||{},`${c.view}_compressed_video_url`)||Object.hasOwn(record||{},`${c.view}_snapshot_url`));
    const synthetic=record&&!explicitMedia&&/^DEMO-R-\d+$/.test(record.id);
    const safe=value=>{try{const url=new URL(value,location.origin);return typeof value==='string'&&value&&['http:','https:'].includes(url.protocol)?url.href:'';}catch(_){return '';}};
    return {src:synthetic?recordVideoPath(camera):safe(typeof source==='string'?source:source?.url||record?.[`${camera.view}_compressed_video_url`]||record?.[`${camera.view}_video_url`]),poster:synthetic?`/static/post_training_collection/media/${camera.key}.png`:safe(source?.poster||record?.[`${camera.view}_snapshot_url`]),demo:synthetic};
  }
  function recordVideoTiles(record){
    if(record.upload!=='uploaded')return `<div class="dc-upload-placeholder ${record.upload==='failed'?'is-failed':''}"><span>${record.upload==='failed'?'上传失败':'上传中'}</span>${record.upload_error?`<span class="dc-upload-error" title="${esc(record.upload_error)}">${esc(record.upload_error)}</span>`:''}</div>`;
    const sources=recordVideoCameras.map(camera=>({...camera,...recordVideoSource(record,camera)})),available=sources.some(camera=>camera.src);
    return `<div class="dc-record-video-wrapper" data-record-video-id="${esc(record.id)}">${record.prompt?.name?`<div class="dc-video-prompt-bar" title="${esc(record.prompt.name)}">${esc(record.prompt.name)}</div>`:''}<div class="dc-video-row">${sources.map(camera=>`<div class="dc-video-item${camera.src?'':' is-missing'}"><div class="dc-video-poster">${camera.poster?`<img src="${esc(camera.poster)}" alt="${camera.label}快照" loading="lazy">`:''}<span>${camera.label}${camera.demo?' · 示例':camera.src?'':' · 暂无'}</span></div></div>`).join('')}</div>${available?`<div class="dc-video-play-mask"><button type="button" class="dc-video-group-play" data-action="record-video" data-id="${esc(record.id)}" aria-label="播放三个视频" title="播放三个视频">${icon('play')}</button></div>`:''}</div>`;
  }
  root.addEventListener('error',event=>{if(event.target.matches('.dc-video-poster img'))event.target.remove();},true);
  function releaseRecordVideo(){
    const state=activeRecordVideo;activeRecordVideo=null;
    if(!state)return;
    cancelAnimationFrame(state.frame);state.epoch++;
    for(const item of state.items){try{item.controller?.destroy();}catch(_){/* Player already gone. */}item.player.pause();item.player.removeAttribute('src');item.player.load();}
    if(state.wrapper.isConnected)state.wrapper.outerHTML=recordVideoTiles(state.record);
    queueMicrotask(applyPendingRefresh);
  }
  function usableRecordVideos(state){return state.items.filter(item=>!item.failed);}
  function playableRecordVideos(state){return usableRecordVideos(state).filter(item=>!item.player.ended);}
  function recordVideoDuration(state){const items=usableRecordVideos(state);return items.length&&items.every(item=>Number.isFinite(item.player.duration))?Math.max(...items.map(item=>item.player.duration)):0;}
  function updateRecordVideoControls(state){
    if(activeRecordVideo!==state)return;
    const button=state.wrapper.querySelector('[data-action="toggle-record-video"]'),status=state.wrapper.querySelector('[data-video-status]');
    if(!button)return;
    const loading=state.wanted&&(!state.ready||playableRecordVideos(state).some(item=>item.player.readyState<3));
    const mode=loading?'reset':state.wanted?'pause':'play';
    if(button.dataset.playbackMode!==mode){button.dataset.playbackMode=mode;button.innerHTML=icon(mode);button.classList.toggle('is-loading',loading);button.setAttribute('aria-label',loading?'视频加载中':state.wanted?'暂停三个视频':'播放三个视频');button.title=button.getAttribute('aria-label');button.setAttribute('aria-busy',String(loading));}
    status.textContent=state.message||'';
    state.wrapper.querySelector('[data-action="retry-record-video"]').hidden=!state.items.some(item=>item.failed);
  }
  function pauseRecordVideos(state){state.epoch++;for(const item of state.items)item.player.pause();}
  function startRecordVideos(state){
    const items=playableRecordVideos(state);if(activeRecordVideo!==state||!state.ready||!state.wanted||!items.length||state.items.some(item=>item.failed)||state.starting||items.some(item=>item.player.readyState<3||item.player.seeking))return;
    if(items.every(item=>!item.player.paused))return;
    state.message='';const epoch=++state.epoch;state.starting=true;
    Promise.all(items.map(item=>item.player.play())).catch(()=>{if(activeRecordVideo===state&&state.epoch===epoch){state.wanted=false;state.message='点击播放继续';pauseRecordVideos(state);}}).finally(()=>{if(activeRecordVideo===state){state.starting=false;updateRecordVideoControls(state);}});
  }
  function toggleRecordVideos(){
    const state=activeRecordVideo;if(!state)return;
    if(state.items.some(item=>item.failed)){recordVideo(state.recordId,state.wrapper);return;}
    state.wanted=!state.wanted;state.message='';
    if(state.wanted){if(usableRecordVideos(state).every(item=>item.player.ended||item.player.currentTime>=item.player.duration-.05))for(const item of state.items)item.player.currentTime=0;startRecordVideos(state);}else pauseRecordVideos(state);
    updateRecordVideoControls(state);
  }
  function seekRecordVideos(value){
    const state=activeRecordVideo;if(!state)return;
    const time=Math.max(0,Math.min(Number(value)||0,recordVideoDuration(state)));pauseRecordVideos(state);
    for(const {player} of usableRecordVideos(state))if(Number.isFinite(player.duration)&&Math.abs(player.currentTime-Math.min(time,player.duration))>.08)player.currentTime=Math.min(time,player.duration);
    updateRecordVideoControls(state);
  }
  async function recordVideo(id,origin){
    const record=task.records.find(item=>item.id===id),wrapper=origin?.closest('.dc-record-video-wrapper');
    if(!record||!wrapper||!recordVideoCameras.some(camera=>recordVideoSource(record,camera).src))return;
    const focusRequested=wrapper.contains(document.activeElement);
    if(activeRecordVideo?.wrapper===wrapper){activeRecordVideo.wanted=false;pauseRecordVideos(activeRecordVideo);for(const item of activeRecordVideo.items){item.failed=false;item.player.load();}activeRecordVideo.wanted=true;startRecordVideos(activeRecordVideo);return;}
    releaseRecordVideo();
    const sources=recordVideoCameras.map(camera=>({...camera,...recordVideoSource(record,camera)}));
    wrapper.classList.add('is-playing');
    wrapper.querySelector('.dc-video-row').innerHTML=sources.map(camera=>`<div class="dc-video-item">${camera.src?`<video class="dc-video-player" muted playsinline preload="auto" aria-label="${camera.label}视频" data-camera="${camera.key}" ${camera.poster?`poster="${esc(camera.poster)}"`:''} src="${esc(camera.src)}"></video>`:'<div class="dc-video-camera-status">暂无视频</div>'}<span class="dc-video-camera-label">${camera.label}${camera.demo?' · 示例':''}</span></div>`).join('');
    wrapper.querySelector('[data-action="record-video"]').dataset.action='toggle-record-video';
    wrapper.insertAdjacentHTML('beforeend','<div class="dc-video-feedback"><span data-video-status role="status"></span><button type="button" class="dc-link" data-action="retry-record-video" hidden>重新加载</button></div>');
    const state={recordId:record.id,record,wrapper,items:[...wrapper.querySelectorAll('.dc-video-player')].map(player=>({player,failed:false,controller:null})),wanted:true,ready:false,epoch:0,starting:false,message:'',frame:0};activeRecordVideo=state;
    if(focusRequested)wrapper.querySelector('[data-action="toggle-record-video"]').focus({preventScroll:true});
    for(const item of state.items){
      const {player}=item;
      player.addEventListener('waiting',()=>{if(activeRecordVideo===state&&state.wanted&&player.readyState<3){pauseRecordVideos(state);updateRecordVideoControls(state);}});
      player.addEventListener('error',()=>{if(activeRecordVideo!==state)return;item.failed=true;state.wanted=false;state.message='部分视频加载失败';pauseRecordVideos(state);updateRecordVideoControls(state);});
      for(const event of ['canplay','seeked','loadedmetadata'])player.addEventListener(event,()=>{if(activeRecordVideo===state){updateRecordVideoControls(state);startRecordVideos(state);}});
      player.addEventListener('seeking',()=>{if(activeRecordVideo===state&&!player.ended)seekRecordVideos(player.currentTime);});
      player.addEventListener('ratechange',()=>{if(activeRecordVideo===state)for(const other of state.items)if(other.player.playbackRate!==player.playbackRate)other.player.playbackRate=player.playbackRate;});
      player.addEventListener('ended',()=>{if(activeRecordVideo===state&&usableRecordVideos(state).every(other=>other.player.ended)){state.wanted=false;pauseRecordVideos(state);updateRecordVideoControls(state);if(pendingRefresh)releaseRecordVideo();}});
    }
    updateRecordVideoControls(state);
    if(!document.getElementById('dc-plyr-style')){const link=document.createElement('link');link.id='dc-plyr-style';link.rel='stylesheet';link.href='/static/post_training_collection/vendor/plyr-3.8.4.css';document.head.append(link);}
    try{
      recordVideoLibrary||=import('/static/post_training_collection/vendor/plyr-3.8.4.mjs');
      const {P:Plyr}=await recordVideoLibrary;if(activeRecordVideo!==state)return;
      for(const item of state.items)item.controller=new Plyr(item.player,{controls:['progress','mute','settings','fullscreen','download'],hideControls:true,clickToPlay:false,autopause:false,keyboard:{focused:false,global:false},storage:{enabled:false},blankVideo:'',iconUrl:'/static/post_training_collection/vendor/plyr.svg',tooltips:{controls:false},resetOnEnd:false,settings:['speed'],speed:{selected:1,options:[.5,.75,1,1.25,1.5,2,3]}});
    }catch(_){recordVideoLibrary=null;for(const item of state.items)item.player.controls=true;}
    if(activeRecordVideo!==state)return;
    state.ready=true;
    function tick(){
      if(activeRecordVideo!==state)return;
      const items=playableRecordVideos(state),master=items[0]?.player;
      if(state.wanted&&master&&!master.paused)for(const {player} of items.slice(1))if(!player.seeking&&Math.abs(player.currentTime-master.currentTime)>.2)player.currentTime=master.currentTime;
      updateRecordVideoControls(state);state.frame=requestAnimationFrame(tick);
    }
    startRecordVideos(state);tick();
  }
  window.addEventListener('pagehide',()=>{releaseRecordVideo();window.CollectionTrajectory?.release();});
  function renderRecords() {
    releaseRecordVideo();
    // 【新】默认已上传，异常独立筛选；累计小时只计上传完成的录制。
    const rows=task.records.filter(r=>Object.entries(recordFilters).every(([key,value])=>!value||(key==='upload'?(value==='all'||r.upload===value):key==='conclusion'?collectionConclusion(r).value===value:String(r[key]??'').toLowerCase().includes(value.toLowerCase().trim()))));
    const emptyTitle=task.records.length?'没有匹配的录制':task.status==='closed'?'任务已结束，暂无数据':'等待采集数据';
    const emptyMessage=task.records.length?'试试调整搜索条件、上传状态或采集结论。':task.status==='closed'?'':'先分享任务卡给采集员，确认任务后开始采集。';
    const emptyAction=!task.records.length&&task.status==='open'?'<button class="dc-btn small" data-action="share-task">分享任务卡</button>':'';
    root.querySelector('.dc-record-reset').disabled=!Object.entries(recordFilters).some(([key,value])=>value!==recordDefaults[key]);
    const pageCount=Math.max(1,Math.ceil(rows.length/8)); recordPage=Math.min(recordPage,pageCount);
    const resultSeconds=rows.filter(r=>r.upload==='uploaded').reduce((sum,r)=>sum+(Number.isFinite(r.seconds)?r.seconds:0),0);
    const showUpload=recordFilters.upload!=='uploaded';
    const uploadCell=r=>`<td data-label="上传状态"><span class="dc-badge ${r.upload==='failed'?'red':r.upload==='uploaded'?'teal':''}">${{uploaded:'已上传',failed:'上传失败',uploading:'上传中'}[r.upload]||'—'}</span></td>`;
    document.getElementById('dc-record-results').innerHTML=`<div class="dc-table-wrap"><table class="dc-table dc-record-table ${showUpload?'dc-record-with-upload':''}" aria-label="采集录制"><colgroup><col class="dc-record-id-column"><col class="dc-record-video-column"><col><col><col><col>${showUpload?'<col>':''}<col><col><col></colgroup><thead><tr><th>Recording ID</th><th>视频区域（头部 ｜ 左臂 ｜ 右臂）</th><th>设备</th><th>采集员</th><th>录制时间</th><th>时长</th>${showUpload?'<th>上传状态</th>':''}<th class="dc-record-conclusion-head">采集结论</th><th>关联处理</th><th>操作</th></tr></thead><tbody>${rows.slice((recordPage-1)*8,recordPage*8).map(r=>`<tr><td class="dc-record-cell"><div class="dc-record-identity"><button class="dc-link" data-action="record-detail" data-id="${esc(r.id)}" title="${esc(r.id)}">${esc(r.id)}</button></div></td><td class="dc-record-video-cell" data-label="视频">${recordVideoTiles(r)}</td><td data-label="设备">${esc(r.device)}</td><td data-label="采集员">${esc(r.operator)}</td><td class="dc-muted" data-label="录制时间">${date(r.recorded_at)}</td><td class="dc-muted" data-label="时长">${Number.isFinite(r.seconds)?duration(r.seconds):'—'}</td>${showUpload?uploadCell(r):''}<td data-label="采集结论">${collectionConclusionBadge(r)}</td><td data-label="关联处理">${recordProcessingCell(r)}</td><td data-label="操作"><button type="button" class="dc-link dc-record-trajectory" data-action="record-trajectory" data-id="${esc(r.id)}" ${r.upload!=='uploaded'?'disabled':''}>轨迹</button></td></tr>`).join('')||`<tr class="dc-record-empty-row"><td colspan="${showUpload?10:9}">${empty(emptyTitle,emptyMessage,emptyAction)}</td></tr>`}</tbody></table></div><footer class="dc-footer"><span class="dc-record-summary">共 ${rows.length} 条录制<span class="dc-result-hours">${recordFilters.upload==='uploaded'?'累计':'已上传累计'} ${esc(hours(resultSeconds))} 小时</span></span><div class="dc-page-buttons"><button data-action="record-prev" aria-label="上一页录制" ${recordPage===1?'disabled':''}>‹</button><span>${recordPage} / ${pageCount}</span><button data-action="record-next" aria-label="下一页录制" ${recordPage===pageCount?'disabled':''}>›</button></div></footer>`;
  }
  function recordDetail(id) {
    const r=task.records.find(r=>r.id===id); if(!r)return;
    const uploadLabel={uploaded:'已上传',uploading:'上传中',failed:'上传失败'}[r.upload]||'—';
    openDialog('录制详情',`<dl class="dc-kv"><dt>Recording</dt><dd>${esc(r.id)}</dd><dt>归属任务</dt><dd>${esc(task.id)} · ${esc(task.name)}</dd><dt>采集员 / 设备</dt><dd>${esc(r.operator)} / ${esc(r.device)}</dd><dt>录制时间</dt><dd>${esc(fullDate(r.recorded_at))}</dd><dt>录制时长</dt><dd>${Number.isFinite(r.seconds)?duration(r.seconds):'—'}</dd><dt>上传状态</dt><dd>${esc(uploadLabel)}</dd>${r.upload==='failed'&&r.upload_error?`<dt>失败原因</dt><dd>${esc(r.upload_error)}</dd>`:''}<dt>采集结论</dt><dd>${collectionConclusionBadge(r)}</dd>${r.prompt?`<dt>实际 Prompt</dt><dd>${esc(r.prompt.name)} · ${esc(r.prompt.version)}\n${esc(r.prompt.text)}</dd><dt>Checkpoint</dt><dd>${esc(checkpoint(r.checkpoint))} (${esc(r.checkpoint)})</dd>`:''}</dl>`, `<button class="dc-btn" data-action="copy-record-issue" data-id="${esc(r.id)}">复制问题信息</button><button class="dc-btn" data-action="close-dialog">关闭</button>`);
  }
  function recordIssueText(r) {
    const uploadLabel={uploaded:'已上传',uploading:'上传中',failed:'上传失败'}[r.upload]||'—';
    const link=new URL(boot.base+'/'+encodeURIComponent(task.id),location.origin);link.searchParams.set('record',r.id);link.searchParams.set('upload','all');link.hash='records';
    return [`采集数据问题`, `任务 ID：${task.id}`, `任务名称：${task.name}`, `Recording ID：${r.id}`, `设备：${r.device||'—'}`, `采集员：${r.operator||'—'}`, `录制时间：${fullDate(r.recorded_at)}`, `上传状态：${uploadLabel}${r.upload_error?`（${r.upload_error}）`:''}`, `采集结论：${collectionConclusion(r).label}`, `问题说明：请补充异常现象及处理建议。`, `数据链接：${link.href}`].join('\n');
  }
  function confirmState() {
    const closing=task.status==='open';
    const uploadWarning=closing&&(task.metrics.uploading||task.metrics.upload_failed)?`<div class="dc-note amber" data-upload-warning>${icon('info')}<span>当前有 ${task.metrics.uploading||0} 条上传中、${task.metrics.upload_failed||0} 条上传失败。结束后仍可继续上传或补传。</span></div>`:'';
    openDialog(closing?'结束此任务的采集？':'重新开放采集？',`<p class="dc-confirm-text"><strong>${esc(task.name)}</strong><br>${esc(task.id)}</p><dl class="dc-confirm-metrics"><div><dt>已上传数据</dt><dd data-metric="uploaded">${task.metrics.uploaded}</dd></div><div><dt>采集时长（小时）</dt><dd data-metric="hours">${esc(hours(task.metrics.seconds))}</dd></div><div><dt>最近采集</dt><dd data-metric="latest">${task.metrics.latest?esc(fullDate(task.metrics.latest)):'-'}</dd></div></dl>${uploadWarning}<div class="dc-note">${icon('info')}<span>${closing?'结束后停止新录制，已有数据和合法补传保留，关联处理任务继续按各自状态运行。':'重新开放后可继续采集，收尾提醒重新计时；已完成或关闭的处理任务不会自动重开。'}</span></div>`,`<button class="dc-btn" data-action="close-dialog">取消</button><button class="dc-btn primary" data-action="confirm-state">${closing?'确认结束采集':'确认重新开放'}</button>`);
  }
  async function mutateTask(path, body) {
    if(busy)return; busy=true;
    dialog.querySelectorAll('button').forEach(b=>b.disabled=true);
    try { const result=await request(`/tasks/${task.id}/${path}`,'POST',{...body,revision:task.revision}); task=result.task; closeDialog(); await refreshTaskView(); toast(task.status==='closed'?'已结束采集，已有数据继续处理':'已重新开放采集'); }
    catch(error){ if(error.status===409){try{task=(await request(`/tasks/${task.id}`)).task;closeDialog();await refreshTaskView();toast('任务已被更新，已刷新最新状态，请重新确认');}catch(_){toast('暂时无法刷新，请检查连接后重试');}}else toast(error.message); }
    finally{busy=false;dialog.querySelectorAll('button').forEach(b=>b.disabled=false);}
  }
  async function refreshTaskView() {
    if(view!=='list'){renderDetail();return;}
    tasks=(await request('/tasks')).tasks;renderList();
    root.querySelector(`[data-action="list-change-state"][data-id="${task.id}"]`)?.focus({preventScroll:true});
  }
  function changeFormField(el) {
    const key=el.dataset.form; if(!key)return;
    if(task&&!editableFields.includes(key))return;
    clearFormError(key);
    if(key==='mode'){
      clearFormError('prompts');clearFormError('checkpoint');clearFormError('generalization');
      formModeCache[`${form.source}:${form.mode}`]=clone(form.generalization);
      form[key]=el.value;
      form.generalization=clone(formModeCache[`${form.source}:${form.mode}`]||[]);
      if(isDagger()) form.generalization=form.generalization.filter(g=>form.prompts.some(p=>p.id===g.prompt_id));
      dirty=true;renderForm();root.querySelector('#dc-mode')?.focus({preventScroll:true});return;
    }
    form[key]=el.value;
    if(key==='spec_url'){
      form.spec_id='';form.spec_name='';root.querySelector('.dc-selected-spec')?.remove();
      root.querySelector('[data-spec-action="open"]').outerHTML=specLink.button(form.spec_url);
    }
    dirty=true;
  }
  document.addEventListener('input',event=>{
    const el=event.target;
    if(el.matches('#dc-app [data-form]') && el.dataset.form!=='mode' && el.type!=='hidden') changeFormField(el);
    if(el.dataset.filter==='q'||el.dataset.filter==='creator'){list[el.dataset.filter]=el.value;list.page=1;updateListUrl();renderListResults();}
    if(el.id==='dc-checkpoint-search')renderCheckpointOptions(el.value);
    if(el.matches('#dc-app input[data-record-filter]')){recordFilters[el.dataset.recordFilter]=el.value;recordPage=1;renderRecords();}
    if(generalizationEditor&&dialog.contains(el)){
      const g=generalizationEditor.value;
      if(el.dataset.bound){g.bounds[el.dataset.bound] ||= ['',''];g.bounds[el.dataset.bound][Number(el.dataset.side)]=el.value.trim()===''?'':Number(el.value)/100;clearGeneralizationError(el.dataset.bound+'0');clearGeneralizationError(el.dataset.bound+'1');}
      if(el.dataset.g==='name'){g.name=el.value;clearGeneralizationError('name');}
    }
  });
  document.addEventListener('change',event=>{
    const el=event.target;
    if(el.matches('#dc-app [data-form]')&&el.dataset.form==='mode')changeFormField(el);
    if(el.matches('#dc-app [data-record-filter]')){const key=el.dataset.recordFilter;recordFilters[key]=el.value;recordPage=1;renderRecords();if(key==='conclusion')root.querySelector('[data-record-filter=conclusion]')?.focus({preventScroll:true});}
    if(el.dataset.filter && el.dataset.filter!=='q'){list[el.dataset.filter]=el.value;list.page=1;updateListUrl();renderListResults();}
    if(el.dataset.checkpoint)checkpointSelection=el.dataset.checkpoint;
    if(generalizationEditor&&dialog.contains(el)&&el.dataset.g&&el.dataset.g!=='name'){
      const g=generalizationEditor.value;g[el.dataset.g]=el.type==='checkbox'?el.checked:el.value;
      clearGeneralizationError(el.dataset.g);
      if(['arm','event'].includes(el.dataset.g))g.operator=boot.operators.find(o=>o.arm===g.arm&&o.event===g.event).id;
      if(el.dataset.g==='plane')for(const axis of g.plane)g.bounds[axis]||=['',''];
      if(['arm','event','plane'].includes(el.dataset.g)){const scroll=dialog.querySelector('.dc-dialog-body').scrollTop;renderGeneralizationEditor(el.dataset.g);dialog.querySelector('.dc-dialog-body').scrollTop=scroll;}
    }
  });
  document.addEventListener('submit',event=>{if(event.target.id==='dc-create-form')submitForm(event);else if(event.target.id==='dc-generalization-form'){event.preventDefault();saveGeneralizationEditor();}});
  document.addEventListener('click',event=>{
    const button=event.target.closest('[data-action]');if(!button)return;
    if(button.dataset.action==='pick-spec'){event.preventDefault();pickSpec();}
    else if(button.dataset.action==='select-spec'){
      const spec=specs.find(s=>s.id===button.dataset.id);if(!spec)return;
      Object.assign(form,{spec_id:spec.id,spec_name:spec.name,spec_url:spec.url});dirty=true;clearFormError('spec_url');closeDialog();renderForm();
    }else if(button.dataset.action==='clear-spec'){
      Object.assign(form,{spec_id:'',spec_name:'',spec_url:''});dirty=true;renderForm();
    }
  });
  root.addEventListener('keydown',event=>{
    const tab=event.target.closest('[role="tab"]');
    if(!tab || !['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    event.preventDefault();
    const tabs=[...tab.parentElement.querySelectorAll('[role="tab"]')],index=tabs.indexOf(tab);
    const next=event.key==='Home'?tabs[0]:event.key==='End'?tabs.at(-1):tabs[(index+(event.key==='ArrowRight'?1:tabs.length-1))%tabs.length];
    const action=next.dataset.action,value=next.dataset.value;next.click();root.querySelector(`[data-action="${action}"][data-value="${value}"]`)?.focus();
  });
  document.addEventListener('click',async event=>{
    const button=event.target.closest('[data-action]');if(!button||!button.closest('#dc-app,#dc-dialog'))return;
    const action=button.dataset.action;
    event.preventDefault();
    if(action==='refresh-data')await refreshCollection(true);
    else if(action==='source-tab'){list.source=button.dataset.value;list.page=1;renderList();}
    else if(action==='reset-filters'){Object.assign(list,{q:'',creator:'',project:'',status:'',mode:'',mineOnly:false,reviewOnly:false,page:1});renderList();root.querySelector('[data-filter="q"]')?.focus({preventScroll:true});}
    else if(action==='mine-filter'||action==='review-filter'){const key=action==='mine-filter'?'mineOnly':'reviewOnly';list[key]=!list[key];list.page=1;renderList();root.querySelector(`[data-action="${action}"]`)?.focus({preventScroll:true});}
    else if(action==='list-prev'||action==='list-next'){list.page+=action==='list-prev'?-1:1;renderListResults();}
    else if(action==='retry')init();
    else if(action==='pick-prompts')window.CollectionPromptPicker.toggle();
    else if(action==='pick-checkpoint')openCheckpointPicker();
    else if(action==='close-dialog')closeDialog();
    else if(action==='confirm-checkpoint'){
      if(!checkpointSelection){toast('请选择一个 Checkpoint');return;}form.checkpoint=checkpointSelection;clearFormError('checkpoint');closeDialog();dirty=true;renderForm();document.getElementById('dc-checkpoint')?.focus({preventScroll:true});
    }
    else if(action==='add-generalization')openGeneralizationEditor();
    else if(action==='edit-generalization')openGeneralizationEditor(Number(button.dataset.index));
    else if(action==='remove-generalization'){form.generalization.splice(Number(button.dataset.index),1);dirty=true;renderForm();}
    else if(action==='save-draft'){
      try {localStorage.setItem(draftKey,JSON.stringify({form,baseRevision:task?.revision||null,savedAt:new Date().toISOString()}));dirty=false;toast('本地草稿已保存，尚未创建或更新任务');}catch(_){toast('浏览器存储不可用，草稿未保存');}
    }
    else if(action==='restore-draft'){
      if(task && draft.baseRevision!==task.revision){toast('任务已有更新，请核对后再保存草稿内容');}
      form=task?{...fromTask(task),...Object.fromEntries(editableFields.filter(key=>key in draft.form).map(key=>[key,clone(draft.form[key])]))}:{...defaultForm(),...draft.form};
      form.source=formSource;
      if(locked())form.mode=task.mode;
      if(!task)form.prompts=form.prompts.filter(p=>boot.prompts.some(v=>v.id===p.id));
      if(isDagger())form.generalization=form.generalization.filter(g=>form.prompts.some(p=>p.id===g.prompt_id));
      draft=null;formErrors={};dirty=true;renderForm();toast('草稿已恢复，请核对后提交');
    }
    else if(action==='discard-draft'){try{localStorage.removeItem(draftKey);}catch(_){}draft=null;renderForm();}
    else if(action==='create-processing')location.assign('/data/processing-tasks?collection='+encodeURIComponent(task.id)+'&new=1');
    else if(action==='creation-done'){closeDialog();const url=new URL(location.href);url.searchParams.delete('created');history.replaceState(null,'',url.pathname+url.search+url.hash);}
    else if(action==='record-processing')await showRecordProcessing(button.dataset.id);
    else if(action==='retry-processing')await loadProcessingLinks();
    else if(action==='detail-tab')selectDetailTab(button.dataset.value);
    else if(action==='reset-record-filters'){Object.assign(recordFilters,recordDefaults);recordPage=1;renderDetailBody();root.querySelector('[data-record-filter="id"]')?.focus({preventScroll:true});}
    else if(action==='record-prev'||action==='record-next'){recordPage+=action==='record-prev'?-1:1;renderRecords();}
    else if(action==='record-detail')recordDetail(button.dataset.id);
    else if(action==='copy-record-issue'){const r=task.records.find(record=>record.id===button.dataset.id);if(r)await copyText(recordIssueText(r),'问题信息已复制，可补充说明后交接');}
    else if(action==='record-trajectory'){
      const record=task.records.find(r=>r.id===button.dataset.id);if(!record)return;
      button.focus({preventScroll:true});
      openDialog('数据轨迹','',`<button class="dc-btn" data-action="copy-record-issue" data-id="${esc(record.id)}">复制问题信息</button><button class="dc-btn" data-action="close-dialog">关闭</button>`);
      window.CollectionTrajectory.open({dialog,record,cameras:recordVideoCameras.map(camera=>({...camera,...recordVideoSource(record,camera)})),conclusion:collectionConclusionBadge(record)});
    }
    else if(action==='record-video')recordVideo(button.dataset.id,button);
    else if(action==='toggle-record-video')toggleRecordVideos();
    else if(action==='retry-record-video'){if(activeRecordVideo){const {recordId}=activeRecordVideo;releaseRecordVideo();const replacement=[...root.querySelectorAll('.dc-record-video-wrapper')].find(el=>el.dataset.recordVideoId===recordId);recordVideo(recordId,replacement);}}
    else if(action==='list-share-task')await shareFromList(button);
    else if(action==='share-task'||action==='check-latest-task')await openShareCard();
    else if(action==='copy-task-card')await copyShareCard();
    else if(action==='copy-task-link')await copyShareCard(true);
    else if(action==='copy-task-id')copyText(task.id);
    else if(action==='change-state'){
      if(busy)return;busy=true;
      try{task=(await request('/tasks/'+task.id)).task;await loadProcessingLinks(false);confirmState();}catch(error){toast(error.message);}finally{busy=false;}
    }
    else if(action==='list-change-state'){
      if(busy)return;busy=true;button.disabled=true;
      try{task=(await request('/tasks/'+encodeURIComponent(button.dataset.id))).task;confirmState();}
      catch(error){toast(error.message);}finally{busy=false;button.disabled=false;}
    }
    else if(action==='confirm-state')await mutateTask('state',{status:task.status==='open'?'closed':'open'});
  });
  window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
  window.addEventListener('hashchange',()=>{if(view==='detail'&&task)selectDetailTab(location.hash.slice(1)||'records',false);});
  async function init() {
    root.setAttribute('aria-busy','true');
    try {
      if(view==='list'){tasks=(await request('/tasks')).tasks;lastRefreshedAt=Date.now();renderList();restoreListPosition();}
      else if(view==='form'){
        if(route[1]==='edit'){task=(await request('/tasks/'+encodeURIComponent(route[0]))).task;form=fromTask(task);}
        else if(params.get('copy')){const original=(await request('/tasks/'+encodeURIComponent(params.get('copy')))).task;form=fromTask(original,true);}
        else form=defaultForm();
        formSource=form.source;
        try{const stored=JSON.parse(localStorage.getItem(draftKey));if(stored?.form?.source===formSource&&Array.isArray(stored.form.prompts)&&Array.isArray(stored.form.generalization)&&Array.isArray(stored.form.tags))draft=stored;}catch(_){/* Ignore unavailable or invalid storage. */}
        renderForm();
      } else {task=(await request('/tasks/'+encodeURIComponent(route[0]))).task;await loadProcessingLinks(false);lastRefreshedAt=Date.now();renderDetail();if(params.has('saved')){toast(params.get('saved')==='unchanged'?'未发现修改':'任务已保存');const url=new URL(location.href);url.searchParams.delete('saved');history.replaceState(null,'',url.pathname+url.search);}if(params.get('card')==='1')await openShareCard();if(params.get('created')==='1')showCreateSuccess();if(params.has('processing_created'))toast('处理任务已创建，可在关联处理中查看并发布');}
    } catch(error) { ready(pageHead('数据采集','')+`<section class="dc-panel">${empty('暂时无法加载',error.message,'<button class="dc-btn" data-action="retry">重新加载</button>')}</section>`); }
  }
  init();
  // 【新】不重载表单；媒体使用期间暂存更新，不销毁播放器。
  window.addEventListener('focus',()=>refreshCollection());
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshCollection();});
  const refreshTimer=setInterval(()=>refreshCollection(),60000);
  window.addEventListener('pagehide',()=>clearInterval(refreshTimer));
})();
