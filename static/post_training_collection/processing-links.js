/* Only collection-sourced processing tasks use this persistence adapter.
 * The original unrelated processing-task demonstrations remain unchanged. */
(() => {
  'use strict';
  const API='/api/post-training-collection/processing',BASE='/data/post-training-collection';
  const params=new URLSearchParams(location.search),drawer=document.getElementById('drawerProcessingTaskForm');
  if(!drawer)return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let source=null,jobs=[],activeJob=null,saving=false,requestKey=crypto.randomUUID(),loadToken=0,collectionTasks=[];
  const configs={};
  const originalOpen=window.dprOpenProcessingTaskDrawer,originalSubmit=window.dprSubmitProcessingTask,originalClose=window.dprCloseProcessingTaskPage;
  const title=document.getElementById('processingTaskDrawerTitle');
  const sourceBox=document.createElement('div');sourceBox.id='dc-processing-source';sourceBox.className='dc-processing-source';sourceBox.hidden=true;
  title.parentElement.append(sourceBox);
  const message=document.createElement('div');message.className='dc-processing-message';message.setAttribute('role','alert');message.hidden=true;drawer.querySelector('.dpr-processing-task-page-foot').prepend(message);
  const showError=text=>{message.textContent=text;message.hidden=!text;};
  const actionNote=document.createElement('p');actionNote.className='dc-processing-scope-note';actionNote.hidden=true;
  document.getElementById('processingTaskFilters').before(actionNote);
  const sourceField=document.createElement('label');sourceField.className='fg';sourceField.id='dc-processing-source-field';
  sourceField.innerHTML='<span>来源采集任务</span><select id="dc-processing-source-select"><option value="">不指定来源采集任务</option></select>';
  drawer.querySelector('.dpr-processing-basic-grid').append(sourceField);
  async function api(path,method='GET',body,headers={}){
    const response=await fetch(API+path,{method,cache:'no-store',headers:{'Content-Type':'application/json',...headers},body:body===undefined?undefined:JSON.stringify(body)});
    let data;try{data=await response.json()}catch{throw Error('服务暂时不可用，请稍后重试')}
    if(!response.ok)throw Error(data.error||'操作失败');return data;
  }
  function rememberNodes(){
    if(activeJob?.published)return;
    const stage=window.DPR_ACTIVE_ASSIGNMENT_STAGE;
    if(!stage||!window.DPR_ENABLED_FLOW_STAGES[stage])return;
    configs[stage]={};
    drawer.querySelectorAll('#processingTaskAssignments .dpr-flow-node-card').forEach(card=>{
      configs[stage][card.dataset.node]={rule:card.querySelector('.dpr-node-rule-select')?.value||'',
        percent:Number(card.querySelector('.dpr-node-percent-input')?.value??100),
        assignments:[...card.querySelectorAll('.dpr-flow-assignment-row')].map(row=>({type:row.querySelector('.dpr-flow-assignment-type').value,target:row.querySelector('.dpr-flow-assignment-target').value}))};
    });
  }
  function restoreSavedNodes(){
    if(!activeJob)return;
    const nodes=(activeJob.published?activeJob.configs:configs)[window.DPR_ACTIVE_ASSIGNMENT_STAGE]||{};
    drawer.querySelectorAll('#processingTaskAssignments .dpr-flow-node-card').forEach(card=>{
      const node=nodes[card.dataset.node];if(!node)return;
      const rule=card.querySelector('.dpr-node-rule-select'),percent=card.querySelector('.dpr-node-percent-input');
      if(rule&&node.rule){if(![...rule.options].some(o=>o.value===node.rule))rule.add(new Option(node.rule,node.rule));rule.value=node.rule;}
      if(percent)percent.value=node.percent;
    });
  }
  // The existing form caches markup. Persist current property values to avoid
  // losing the user's node choices when switching stages.
  drawer.addEventListener('change',event=>{
    const el=event.target;if(el.matches('#processingTaskAssignments select'))[...el.options].forEach(o=>o.toggleAttribute('selected',o.selected));
    if(el.matches('#processingTaskAssignments input'))el.setAttribute('value',el.value);
    if(source)rememberNodes();
  });
  for(const name of ['dprShowAssignmentsForStage','dprToggleFlowStage','dprProcessingFlowChange']){
    const original=window[name];window[name]=function(...args){if(source)rememberNodes();const result=original.apply(this,args);restoreSavedNodes();return result;};
  }
  function context(sourceTask,job){
    source=sourceTask;activeJob=job||null;showError('');requestKey=crypto.randomUUID();
    for(const key of Object.keys(configs))delete configs[key];Object.assign(configs,job?.configs||{});
    const linked=!!sourceTask;sourceBox.hidden=!linked;actionNote.hidden=!linked;
    const sourceSelect=sourceField.querySelector('select');sourceSelect.value=sourceTask?.id||'';sourceSelect.disabled=!!job;
    sourceField.hidden=drawer.dataset.mode==='detail';
    const sourceNotice=drawer.querySelector('.dpr-processing-filter-notice:not(.dpr-processing-filter-warning)');
    if(sourceNotice)sourceNotice.hidden=linked;
    drawer.querySelector('[data-filter-group="processing"]').hidden=linked;
    sourceBox.innerHTML=linked?`来源采集任务 <a href="${BASE}/${esc(source.id)}#processing">${esc(source.id)} · ${esc(source.name)}</a>`:'';
    actionNote.textContent=linked?'采集任务只限定数据来源，筛选条件可进一步缩小范围。创建后先保存为未发布，发布时才纳入数据。':'';
    document.getElementById('processingTaskDrawerSubmit').textContent=job?'保存修改':'创建任务';
    if(job&&!job.published&&drawer.dataset.mode==='new')title.textContent='编辑处理任务';
    if(linked){
      window.DPR_TASK_FILTER_FIELDS['采集结论']={type:'single',options:['成功','失败']};
      const project=document.getElementById('processingTaskProject');
      const label=source.project_name||source.project;
      if(![...project.options].some(o=>o.value===label))project.add(new Option(label,label));project.value=label;project.disabled=true;
      // Scope remains on the original filter page. Unsupported rule-result
      // predicates are kept out of this local collection-only adapter.
      for(const [key,config] of Object.entries(window.DPR_TASK_FILTER_FIELDS)){
        config._collectionHidden=!['采集任务 ID','数据 ID','采集员','采集时间','采集结论'].includes(key);
      }
      drawer.querySelectorAll('.dpr-task-filter-field option').forEach(o=>o.disabled=!!window.DPR_TASK_FILTER_FIELDS[o.value]?._collectionHidden);
    }
  }
  window.dprOpenProcessingTaskDrawer=function(mode,trigger){
    const isLinked=trigger?.dataset.collectionLinked==='true';
    originalOpen(mode,trigger);
    if(!isLinked){context(null,null);return;}
    const job=jobs.find(j=>j.id===trigger.dataset.taskId);
    if(job){context({id:job.source_ids[0],name:trigger.dataset.sourceName||job.source_ids.join('、'),project:job.project,project_name:trigger.dataset.project},job);restoreSavedNodes();if(mode==='new'){const first=drawer.querySelector('.dpr-filter-row');first?.querySelectorAll('input,select,button').forEach(el=>el.disabled=true);}}
  };
  sourceField.querySelector('select').addEventListener('change',event=>{
    const t=collectionTasks.find(t=>t.id===event.target.value);
    context(t||null,null);
    if(t){
      window.dprRenderTaskFilters([['采集任务 ID','等于',t.id]]);
      const first=drawer.querySelector('.dpr-filter-row');first.querySelectorAll('input,select,button').forEach(el=>el.disabled=true);
      document.getElementById('processingTaskPriority').value=String(t.priority||3);
    }else{
      window.dprRenderTaskFilters([]);document.getElementById('processingTaskProject').disabled=false;
      document.getElementById('processingTaskExpectedMode').disabled=false;
    }
  });
  window.dprCloseProcessingTaskPage=function(){
    if(saving)return;
    if(source&&params.has('collection')&&!activeJob){location.assign(BASE+'/'+encodeURIComponent(source.id)+'#processing');return;}
    originalClose();sourceBox.hidden=true;showError('');
    if(activeJob&&params.has('linked')){const url=new URL(location.href);url.searchParams.delete('linked');history.replaceState(null,'',url.pathname+url.search);}
    source=null;activeJob=null;
  };
  const originalFilterRow=window.dprTaskFilterRow;
  window.dprTaskFilterRow=function(...args){const html=originalFilterRow.apply(this,args);if(!source)return html;const box=document.createElement('div');box.innerHTML=html;box.querySelectorAll('.dpr-task-filter-field option').forEach(o=>o.disabled=!!window.DPR_TASK_FILTER_FIELDS[o.value]?._collectionHidden);return box.innerHTML;};
  const originalAddFilter=window.dprAddTaskFilter;
  window.dprAddTaskFilter=function(group){
    if(!source)return originalAddFilter(group);
    if(group==='processing'){showError('此入口按采集事实筛选数据；处理结果条件请在原处理任务模块配置。');return;}
    document.getElementById('processingTaskBasicFilters').insertAdjacentHTML('beforeend',window.dprTaskFilterRow('数据 ID','等于',''));
    window.dprRefreshFilterRelationLabels();window.dprUpdateDuplicateFilterWarning();
  };
  window.dprSubmitProcessingTask=async function(){
    if(!source)return originalSubmit();
    if(saving)return;showError('');
    const button=document.getElementById('processingTaskDrawerSubmit');
    try{
      if(activeJob?.published){showError('任务已发布，请创建新的处理任务配置。');return;}
      if(drawer.querySelector('[data-processor-editing="true"]'))throw Error('请先保存或取消处理人修改');
      rememberNodes();
      const stages=Object.fromEntries(Object.entries(window.DPR_ENABLED_FLOW_STAGES).filter(([,enabled])=>enabled).map(([stage])=>[stage,window.DPR_SELECTED_FLOWS[stage]]));
      if(!Object.keys(stages).length){window.dprSwitchProcessingTaskPane(drawer.querySelector('[data-task-pane="flow"]'));throw Error('请至少开启并配置一个业务环节');}
      const selectedFilters=window.dprCurrentTaskFilters();
      const unsupported=selectedFilters.some(f=>!['采集任务 ID','数据 ID','采集员','采集时间','采集结论'].includes(f[0]));
      if(unsupported){window.dprSwitchProcessingTaskPane(drawer.querySelector('[data-task-pane="filter"]'));throw Error('请使用采集任务 ID、数据 ID、采集员、采集时间或采集结论筛选');}
      const sourceFilter=selectedFilters.find(f=>f[0]==='采集任务 ID');
      if(!sourceFilter||sourceFilter[1]!=='等于'||sourceFilter[2]!==source.id)throw Error('请保留来源采集任务 ID 条件；其他条件可继续缩小数据范围');
      const name=document.getElementById('processingTaskName').value;
      saving=true;button.disabled=true;button.textContent='正在创建…';
      const expected=window.dprExpectedTaskValidation();if(!expected.valid)throw Error(expected.message);
      const body={name,source_ids:[source.id],priority:Number(document.getElementById('processingTaskPriority').value),category:document.getElementById('processingTaskCategory').value,expected_mode:document.getElementById('processingTaskExpectedMode').value,expected_value:document.getElementById('processingTaskExpectedValue').value,filters:selectedFilters,stages,configs};
      if(activeJob)body.revision=activeJob.revision;
      const result=await api('/tasks'+(activeJob?'/'+activeJob.id:''),activeJob?'PATCH':'POST',body,{'Idempotency-Key':requestKey});
      window.location.assign(BASE+'/'+encodeURIComponent(source.id)+'?processing_created='+result.task.id+'#processing');
    }catch(error){showError(error.message);}
    finally{saving=false;button.disabled=false;button.textContent='创建任务';}
  };
  async function runAction(job,action){
    const labels={publish:'发布后会纳入当前匹配的已上传数据。',pause:'关闭接收后，已纳入的数据和处理结果保留。',resume:'重新开启处理任务。采集任务的开放状态不会改变。',admit:'将当前新增且匹配的数据纳入该处理任务。'};
    const dialog=document.getElementById('dc-processing-confirm');
    dialog.querySelector('h3').textContent={publish:'发布处理任务？',pause:'关闭处理任务？',resume:'开启处理任务？',admit:'纳入新数据？'}[action];
    dialog.querySelector('p').textContent=labels[action];dialog.querySelector('[data-confirm-error]').textContent='';
    const confirm=dialog.querySelector('[data-confirm-action]');confirm.disabled=false;
    confirm.onclick=async()=>{confirm.disabled=true;try{await api('/tasks/'+job.id+'/action','POST',{action,revision:job.revision});dialog.close();await loadJobs();if(new URLSearchParams(location.search).get('linked')===job.id)openJob(job.id);}catch(error){dialog.querySelector('[data-confirm-error]').textContent=error.message;confirm.disabled=false;}};
    dialog.showModal();
  }
  function flowBindings(job){return Object.entries(job.stages).map(([stage,name])=>[stage,name,window.DPR_PROCESSING_FLOWS.find(f=>f.name===name)?.version||'']);}
  function row(job){
    const project=window.DPR_COLLECTION_PROJECTS?.find(p=>p.id===job.project)?.name||job.project;
    const data={taskId:job.id,taskName:job.name,project,taskCategory:job.category||'formal',priority:job.priority,enabled:String(job.enabled),expectedMode:job.expected_mode||'continuous',expectedValue:job.expected_value??'',filters:JSON.stringify(job.filters),flows:JSON.stringify(flowBindings(job)),assignments:JSON.stringify(Object.fromEntries(Object.entries(job.configs).map(([stage,nodes])=>[stage,Object.fromEntries(Object.entries(nodes).map(([name,node])=>[name,node.assignments]))]))),taskStatus:job.published?'published':'unpublished',collectionLinked:'true',sourceName:job.source_ids.join('、')};
    const attrs=Object.entries(data).map(([key,value])=>`data-${key.replace(/[A-Z]/g,c=>'-'+c.toLowerCase())}="${esc(value)}"`).join(' ');
    return `<tr data-collection-processing="${esc(job.id)}" data-processing-task-stage="${esc(Object.keys(job.stages).join(' '))}"><td><code>${esc(job.id)}</code></td><td><button class="dc-processing-link" data-open-job="${esc(job.id)}">${esc(job.name)}</button></td><td>${esc(project)}</td><td>${job.stage_progress.map(p=>`<div class="dc-processing-stage"><span>${esc(p.stage)}</span><b>${p.done} / ${p.total}</b><span>${esc(p.label)}</span></div>`).join('')}</td><td>${job.published?`<button class="dc-processing-link" data-job-action="${job.enabled?'pause':'resume'}" data-job-id="${esc(job.id)}">${job.enabled?'开启':'关闭'}</button>`:'-'}</td><td>${job.published?'已发布':'未发布'}</td><td>${job.priority>=7?'高':job.priority>=4?'中':'低'}</td><td>${job.category==='informal'?'非正式':'正式'}</td><td>${esc(job.creator)}</td><td>${esc(job.created_at.replace('T',' '))}</td><td><div class="dpr-task-actions"><button data-open-job="${esc(job.id)}">数据</button><button ${attrs} onclick="dprOpenProcessingTaskDrawer('detail',this)">配置</button>${!job.published?`<button ${attrs} onclick="dprOpenProcessingTaskDrawer('new',this)">编辑</button>`:''}${!job.published?`<button data-job-action="publish" data-job-id="${esc(job.id)}">发布</button>`:job.enabled&&job.new_count?`<button data-job-action="admit" data-job-id="${esc(job.id)}">纳入新数据</button>`:''}</div></td></tr>`;
  }
  async function loadJobs(){
    jobs=(await api('/tasks')).tasks;
    const body=document.querySelector('#dpr-processing-task-table tbody');body.querySelectorAll('[data-collection-processing]').forEach(e=>e.remove());body.insertAdjacentHTML('afterbegin',jobs.map(row).join(''));
  }
  async function openJob(id){
    const token=++loadToken;
    const panel=document.getElementById('dc-processing-detail');panel.hidden=false;panel.innerHTML='<p role="status">正在加载处理任务…</p>';
    originalClose();
    try{
      const {task:job,sources}=await api('/tasks/'+id);if(token!==loadToken)return;
      const url=new URL(location.href);url.searchParams.delete('new');url.searchParams.delete('collection');url.searchParams.set('linked',id);history.replaceState(null,'',url.pathname+url.search);
      panel.innerHTML=`<header><div><button class="dc-processing-link" data-close-job>‹ 返回处理任务</button><h2>${esc(job.name)}</h2><p>ID ${esc(job.id)} <span class="dc-processing-status">${esc(job.status_label)}</span></p></div><div class="dc-processing-actions"><button class="btn" data-open-job="${esc(id)}">刷新</button>${!job.published?`<button class="btn btn-primary" data-job-action="publish" data-job-id="${esc(id)}">发布</button>`:job.enabled?`<button class="btn" data-job-action="pause" data-job-id="${esc(id)}">关闭处理</button>${job.new_count?`<button class="btn btn-primary" data-job-action="admit" data-job-id="${esc(id)}">纳入新数据（${job.new_count}）</button>`:''}`:`<button class="btn btn-primary" data-job-action="resume" data-job-id="${esc(id)}">开启处理</button>`}</div></header><section class="dc-processing-detail-card"><h3>来源采集任务</h3><div class="dc-processing-sources">${sources.map(s=>`<a href="${BASE}/${esc(s.id)}#processing">${esc(s.id)} · ${esc(s.name)}</a>`).join('')}</div><dl class="dc-processing-numbers"><div><dt>已纳入数据</dt><dd>${job.total_count}</dd></div><div><dt>当前匹配数据</dt><dd>${job.candidate_count}</dd></div><div><dt>待纳入新数据</dt><dd>${job.new_count}</dd></div></dl>${!job.published?'<p>任务未发布，尚未接收数据。</p>':''}</section><section class="dc-processing-detail-card"><h3>业务环节</h3>${job.stage_progress.map(p=>`<div class="dc-processing-stage"><strong>${esc(p.stage)}</strong><span>${esc(job.stages[p.stage])}</span><b>${p.done} / ${p.total}</b><span>${esc(p.label)}</span></div>`).join('')}</section><section class="dc-processing-detail-card"><h3>筛选条件</h3><div class="dc-processing-condition-list">${job.filters.map(f=>`<span>${esc(f.join(' '))}</span>`).join('')}</div></section><section class="dc-processing-detail-card"><h3>已纳入数据</h3>${job.records.length?`<div class="dc-processing-detail-table"><table><thead><tr><th>Recording ID</th><th>来源任务</th><th>纳入时间</th>${Object.keys(job.stages).map(stage=>`<th>${esc(stage)}</th>`).join('')}</tr></thead><tbody>${job.records.map(r=>`<tr><td><a href="${BASE}/${esc(r.task_id)}?record=${encodeURIComponent(r.id)}#records">${esc(r.id)}</a></td><td>${esc(r.task_id)}</td><td>${esc(r.admitted_at.replace('T',' '))}</td>${Object.keys(job.stages).map(stage=>`<td>${{pending:'待处理',processing:'处理中',completed:'已完成'}[r.stages[stage]]||'-'}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:'<div class="dc-processing-empty">'+(job.published?'等待符合筛选条件的数据':'发布后将纳入匹配数据')+'</div>'}</section>`;
    }catch(error){if(token===loadToken)panel.innerHTML=`<p role="alert">${esc(error.message)}</p><button class="btn" data-open-job="${esc(id)}">重试</button><button class="btn" data-close-job>返回</button>`;}
  }
  document.body.insertAdjacentHTML('beforeend','<section id="dc-processing-detail" hidden></section><dialog id="dc-processing-confirm"><h3></h3><p></p><p data-confirm-error role="alert"></p><footer><button class="btn" onclick="this.closest(\'dialog\').close()">取消</button><button class="btn btn-primary" data-confirm-action>确认</button></footer></dialog>');
  document.addEventListener('click',event=>{
    const el=event.target.closest('[data-open-job],[data-close-job],[data-job-action]');if(!el)return;event.preventDefault();
    if(el.hasAttribute('data-open-job'))openJob(el.dataset.openJob);
    else if(el.hasAttribute('data-close-job')){loadToken++;document.getElementById('dc-processing-detail').hidden=true;const url=new URL(location.href);url.searchParams.delete('linked');history.replaceState(null,'',url.pathname+url.search);loadJobs().catch(e=>window.toast(e.message));}
    else{const job=jobs.find(j=>j.id===el.dataset.jobId);if(job)runAction(job,el.dataset.jobAction);}
  });
  async function init(){
    const creatingFromSource=params.has('collection');
    if(creatingFromSource)document.getElementById('processingTaskDrawerSubmit').disabled=true;
    try{
      const response=await fetch('/api/post-training-collection/tasks',{cache:'no-store'});const all=(await response.json()).tasks;
      window.DPR_COLLECTION_PROJECTS=[...new Map(all.map(t=>[t.project,{id:t.project,name:t.project}])).values()];
      // Public bootstrap on collection pages contains the short project names.
      const shortNames={'PRJ-LIANGJIAN':'亮剑','PRJ-MOZ1-SFT-07':'demo采集','PRJ-MOZ2-PRE-03':'预训练','PRJ-POST-TRAINING':'后训练','PRJ-EVAL-GEN-02':'宁德时代','PRJ-JD':'京东项目'};
      window.DPR_COLLECTION_PROJECTS.forEach(p=>p.name=shortNames[p.id]||p.id);
      collectionTasks=all.map(t=>({...t,project_name:shortNames[t.project]||t.project}));
      sourceField.querySelector('select').innerHTML='<option value="">不指定来源采集任务</option>'+collectionTasks.map(t=>`<option value="${esc(t.id)}">${esc(t.id)} · ${esc(t.name)}</option>`).join('');
      await loadJobs();
      if(params.get('linked')){await openJob(params.get('linked'));return;}
      if(params.get('collection')){
        const response=await fetch('/api/post-training-collection/tasks/'+encodeURIComponent(params.get('collection')),{cache:'no-store'});const data=await response.json();if(!response.ok)throw Error(data.error||'来源采集任务不可用');
        const t=data.task;t.project_name=shortNames[t.project]||t.project;
        originalOpen('new');context(t,null);
        const sourceNotice=drawer.querySelector('.dpr-processing-filter-notice:not(.dpr-processing-filter-warning)');
        if(sourceNotice)sourceNotice.hidden=true;
        drawer.querySelector('[data-filter-group="processing"]').hidden=true;
        // 处理任务是独立对象，名称由处理负责人按本次处理目的填写；仅带入来源项目、任务 ID 和优先级。
        document.getElementById('processingTaskName').value='';document.getElementById('processingTaskPriority').value=String(t.priority||3);
        window.dprRenderTaskFilters([['采集任务 ID','等于',t.id]]);
        // Make source condition fixed; extra conditions remain fully editable.
        const first=drawer.querySelector('.dpr-filter-row');first.querySelectorAll('input,select,button').forEach(el=>el.disabled=true);
        document.getElementById('processingTaskProject').disabled=true;
        document.getElementById('processingTaskDrawerSubmit').disabled=false;
        document.getElementById('processingTaskName').focus();
      }
    }catch(error){showError(error.message);window.toast(error.message);if(creatingFromSource)document.getElementById('processingTaskDrawerSubmit').disabled=true;}
  }
  init();
})();
