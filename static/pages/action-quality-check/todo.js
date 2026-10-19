(() => {
  const root=document.querySelector('.annotation-todo');
  const layout=root.querySelector('.todo-layout');
  const groups=root.querySelector('.todo-groups');
  const sidebar=document.createElement('aside');
  sidebar.className='todo-sidebar';
  groups.before(sidebar);
  sidebar.append(groups);
  root.querySelector('.todo-results').prepend(root.querySelector('task-filter-bar'));
  const pool=[document.querySelector('.task-pool')];
  pool[0].querySelector('task-data-table').addEventListener('row-action',event=>{
    if(event.detail.action==='start'){const row=pool[0].querySelector(`tr[data-row="${event.detail.row}"]`);if(row)window.openPoolSetup(row.dataset.flow,row.dataset.node);}
  });
  pool[0].querySelector('task-filter-bar').addEventListener('filter-change',event=>{
    const {flow,node}=event.detail;let total=0;
    pool[0].querySelectorAll('tbody tr').forEach(row=>{row.hidden=!!((flow&&row.dataset.flow!==flow)||(node&&row.dataset.node!==node));if(!row.hidden)total++;});
    pool[0].querySelector('list-pagination').setAttribute('total',total);
  });
  const records=[
    {type:'rejected',taskId:'001',task:'预训练自动化质检流程',node:'采集质检',id:'7523785、7523786、7523787',processing:'批量处理',source:'驳回',note:'质检结果存在错误，请检查标记为错误的数据并修正后重新提交。',round:2,time:'2026-10-11 10:00'},
    ...[
      ['002','供应商抽验','001','驳回','切分起点与动作开始不一致',2,'2026-08-04 16:42'],
      ['002','供应商抽验','003','驳回','存在连续片段未完成切分',3,'2026-08-04 13:56'],
      ['002','供应商抽验','010','分配','驳回后重新分配，等待继续处理',2,'2026-08-04 12:30'],
      ['002','供应商抽验','002','驳回','切分结果需修正',2,'2026-08-04 11:20'],
      ['003','供应商复核','005','驳回','片段边界需修正',2,'2026-08-04 10:20']
    ].map(([taskId,node,id,source,note,round,time])=>({type:'rejected',taskId,node,id:'recording_e2e_'+id,processing:'单条处理',source,note,round,time,task:'端到端切分标注流程'}))
  ];
  records.push(
    {type:'review',taskId:'101',task:'预训练自动化质检流程',node:'质检验收',id:'7523785、7523786、7523787',processing:'批量处理',source:'提交',note:'质检结果存在错误，请检查标记为错误的数据并修正后重新提交。',round:2,time:'2026-10-11 10:00'},
    ...[
      ['102','供应商复核','004','复核发现片段边界仍需确认',2,'2026-08-03 18:20'],
      ['102','供应商复核','006','切分结果与规则不一致',3,'2026-08-03 11:48'],
      ['102','供应商复核','011','修正任务已重新分配，等待继续处理',2,'2026-08-01 16:40'],
      ...['007','008','009'].map((id,i)=>['103','内部验收',id,'修正结果待内部验收',2,`2026-08-01 1${5-i}:00`])
    ].map(([taskId,node,id,note,round,time])=>({type:'review',taskId,node,id:'recording_e2e_'+id,processing:'单条处理',source:'提交',note,round,time,task:'端到端切分标注流程'})),
    ...['采集质检','质检验收'].map((node,i)=>({type:'assigned',taskId:String(201+i),task:'预训练自动化质检流程',node,id:'7523785、7523786、7523787',processing:'批量处理',source:'分配',note:'—',round:2,time:'2026-10-11 10:00'})),
    {type:'assigned',taskId:'203',task:'端到端切分标注流程',node:'供应商抽验',id:'recording_e2e_012',processing:'单条处理',source:'分配',note:'—',round:1,time:'2026-08-01 10:20'}
  );

  records.push(...[
    ['7523788、7523789、7523790','批量处理','片段边界已修正，请再次审核',2,'2026-10-11 09:45'],
    ['7523791','单条处理','已补充缺失的质检原因，请确认',2,'2026-10-11 09:30'],
    ['7523792、7523793','批量处理','已重新核对动作描述与视频内容',3,'2026-10-11 09:10'],
    ['7523794','单条处理','不合格原因已修正，等待质检验收',2,'2026-10-11 08:50'],
    ['7523795、7523796、7523797','批量处理','已完成本批次修正，请复核质检结果',3,'2026-10-11 08:30']
  ].map(([id,processing,note,round,time])=>({type:'review',taskId:'101',task:'预训练自动化质检流程',node:'质检验收',id,processing,source:'提交',note,round,time})));
  const labels={rejected:'驳回待处理',review:'修正待审核',assigned:'其他分配任务'};
  let type='rejected',node='001',filters={},page=1,pageSize=20,totalPages=1;
  const pagination=root.querySelector('.todo-pagination');
  const tableViewport=root.querySelector('.todo-table-wrap');
  const tableFrame=document.createElement('div');
  tableFrame.className='table-component-frame task-data-table';
  tableViewport.before(tableFrame);
  tableViewport.classList.add('table-component-scroll','task-data-table__scroll');
  pagination.classList.add('table-component-footer');
  tableFrame.append(tableViewport,pagination);

  pagination.innerHTML='<list-pagination></list-pagination>';
  const pager=pagination.querySelector('list-pagination');
  pager.addEventListener('page-change',event=>{page=event.detail.page;pageSize=event.detail.pageSize;render();});
  function render(){
    const rows=records.filter(r=>r.type===type&&(!filters.taskId||r.taskId.includes(filters.taskId))&&(!filters.task||r.task===filters.task)&&(!filters.node||r.node===filters.node)&&(!filters.dataId||r.id.includes(filters.dataId)));
    const nodes=[...new Set(rows.map(r=>r.taskId))];
    if(!nodes.includes(node))node=nodes[0]||'';
    root.querySelectorAll('[data-type]').forEach(button=>{
      const label=labels[button.dataset.type];
      const tip={rejected:'对提交后被驳回的任务进行修正',review:'对修正后重新提交的任务进行再次审核',assigned:'处理分配给你的其他任务'}[button.dataset.type];
      button.textContent=label;
      button.dataset.description=tip;
      button.setAttribute('aria-label',label);
    });
    let hint=root.querySelector('.todo-type-hint');
    if(!hint){hint=document.createElement('span');hint.className='todo-type-hint';hint.setAttribute('role','status');root.querySelector('.todo-types').append(hint);}
    hint.textContent=root.querySelector(`[data-type="${type}"]`).dataset.description;
    const flows=[...new Set(rows.map(r=>r.task))];
    groups.innerHTML=flows.map(flow=>{
      const flowRows=rows.filter(r=>r.task===flow);
      const children=[...new Set(flowRows.map(r=>r.taskId))];
      return `<details class="todo-flow" open><summary><span class="todo-flow-arrow" aria-hidden="true">⌄</span><strong class="todo-flow-name" tabindex="0" data-full-id="${flow}">${flow}</strong><em>${flowRows.length} 条待办</em></summary>${children.map(n=>`<button type="button" class="todo-group ${n===node?'is-active':''}" data-node="${n}" aria-pressed="${n===node}"><strong>${flowRows.find(r=>r.taskId===n).node}</strong><em>${flowRows.filter(r=>r.taskId===n).length} 条待办</em></button>`).join('')}</details>`;
    }).join('');
    root.querySelector('tbody').innerHTML=rows.filter(r=>r.taskId===node).map(r=>`<tr><td><span class="todo-data-id" tabindex="0" data-full-id="${r.id}">${r.id}</span></td><td>${r.processing}</td><td><span class="table-source-tag ${r.source==='驳回'?'table-source-tag--returned':r.source==='分配'?'table-source-tag--assigned':'table-source-tag--submitted'}">${r.source}</span></td><td>${r.note}</td><td>第 ${r.round} 轮</td><td>${r.time}</td><td><text-button variant="text" data-handle="${r.id}">处理</text-button></td></tr>`).join('')||'<tr><td colspan="7" class="todo-empty">暂无符合条件的待办项</td></tr>';
    requestAnimationFrame(()=>tableFrame._sizeMiddleScroll?.());
    const resultRows=[...root.querySelectorAll('tbody tr')];
    totalPages=Math.max(1,Math.ceil(rows.filter(r=>r.taskId===node).length/pageSize));
    page=Math.min(page,totalPages);
    resultRows.forEach((row,index)=>row.hidden=index<(page-1)*pageSize||index>=page*pageSize);
    pager.setAttribute('total',rows.filter(r=>r.taskId===node).length);
    pager.setAttribute('page-size',pageSize);
    pager.setAttribute('page',page);
    pagination.hidden=false;
    root.querySelector('.todo-feedback').textContent='';
  }
  const idTooltip=document.createElement('div');
  idTooltip.className='todo-id-tooltip';idTooltip.id='todo-id-tooltip';idTooltip.role='tooltip';idTooltip.hidden=true;document.body.append(idTooltip);
  function showIds(target){
    if(!target.classList.contains('todo-status-help')&&target.scrollWidth<=target.clientWidth){hideIds();return;}
    idTooltip.textContent=target.dataset.fullId;idTooltip.hidden=false;
    target.setAttribute('aria-describedby',idTooltip.id);
    const rect=target.getBoundingClientRect(),tip=idTooltip.getBoundingClientRect();
    idTooltip.style.left=Math.max(8,Math.min(rect.left,window.innerWidth-tip.width-8))+'px';
    idTooltip.style.top=Math.max(8,rect.top-tip.height-8)+'px';
  }
  function hideIds(){idTooltip.hidden=true;root.querySelectorAll('[aria-describedby="todo-id-tooltip"]').forEach(el=>el.removeAttribute('aria-describedby'));}
  root.addEventListener('mouseover',event=>{const target=event.target.closest('.todo-data-id,.todo-flow-name,.todo-status-help');if(target)showIds(target);});
  root.addEventListener('mouseout',event=>{if(event.target.closest('.todo-data-id,.todo-flow-name,.todo-status-help'))hideIds();});
  root.addEventListener('focusin',event=>{const target=event.target.closest('.todo-data-id,.todo-flow-name,.todo-status-help');if(target)showIds(target);});
  root.addEventListener('focusout',hideIds);
  window.addEventListener('scroll',hideIds,true);
  window.addEventListener('resize',hideIds);
  root.addEventListener('keydown',event=>{if(event.key==='Escape')hideIds();});
  const viewStorageKey='action-quality-check:selected-view';
  const viewTabs=document.querySelector('[data-view-tabs]');
  function selectView(view){
    const selected=view==='pool'?'pool':'todo';
    const todo=selected==='todo';
    root.hidden=!todo;
    pool.forEach(el=>el.hidden=todo);
    viewTabs.setActive(selected,false);
    try{sessionStorage.setItem(viewStorageKey,selected);}catch{}
  }
  viewTabs.addEventListener('tab-change',event=>selectView(event.detail.value));
  root.querySelector('task-filter-bar').addEventListener('filter-change',event=>{
    filters=event.detail;
    Object.keys(filters).forEach(key=>filters[key]=filters[key].trim());
    page=1;render();
  });
  root.addEventListener('click',event=>{
    if(event.target.closest('.todo-status-help'))return;
    const tab=event.target.closest('[data-type]');if(tab){type=tab.dataset.type;page=1;root.querySelectorAll('[data-type]').forEach(b=>{b.classList.toggle('is-active',b===tab);b.setAttribute('aria-selected',String(b===tab));});render();}
    const group=event.target.closest('[data-node]');if(group){node=group.dataset.node;page=1;render();}
    const handle=event.target.closest('[data-handle]');if(handle){hideIds();window.openPoolData(root.closest('.task-list-view'),{todoType:type});}
  });
  let savedView="todo";
  try{savedView=sessionStorage.getItem(viewStorageKey)||savedView;}catch{}
  selectView(savedView);
  render();
  customElements.whenDefined('task-data-table').then(()=>customElements.get('task-data-table').enhanceFixedEdges(tableFrame,0,1));
})();
