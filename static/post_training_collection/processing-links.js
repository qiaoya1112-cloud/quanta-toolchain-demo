/* Only collection-sourced processing tasks use this persistence adapter.
 * The original unrelated processing-task demonstrations remain unchanged. */
(() => {
  'use strict';
  const API='/api/post-training-collection/processing',BASE='/data/post-training-collection';
  const params=new URLSearchParams(location.search),drawer=document.getElementById('drawerProcessingTaskForm');
  if(!drawer)return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let source=null,jobs=[],activeJob=null,saving=false,requestKey=crypto.randomUUID(),collectionTasks=[];
  const configs={};
  const originalOpen=window.dprOpenProcessingTaskDrawer,originalSubmit=window.dprSubmitProcessingTask,originalClose=window.dprCloseProcessingTaskPage;
  const title=document.getElementById('processingTaskDrawerTitle');
  const sourceContext=document.createElement('div');sourceContext.className='dc-processing-source-context';sourceContext.hidden=true;
  drawer.querySelector('.dpr-processing-basic-grid').before(sourceContext);
  const detailActions=document.createElement('div');detailActions.className='dc-processing-actions';detailActions.hidden=true;
  drawer.querySelector('.dpr-processing-task-page-foot').append(detailActions);
  const message=document.createElement('div');message.className='dc-processing-message';message.setAttribute('role','alert');message.hidden=true;drawer.querySelector('.dpr-processing-task-page-foot').prepend(message);
  const showError=text=>{message.textContent=text;message.hidden=!text;};
  let sourceIds=[];
  const splitIds=value=>[...new Set(String(value).split(/[,，、]/).map(v=>v.trim()).filter(Boolean))];
  function lockSourceFilter(){
    if(!source||!params.has('collection'))return;
    drawer.querySelectorAll('#processingTaskBasicFilters .dpr-filter-row').forEach(row=>{
      if(row.querySelector('.dpr-task-filter-field')?.value!=='采集任务 ID')return;
      row.dataset.collectionSourceLocked='true';
      row.querySelectorAll('input,select,button').forEach(el=>el.disabled=true);
      const remove=row.querySelector('.dpr-task-config-remove');if(remove)remove.hidden=true;
    });
  }
  function defaultProcessingName(task){
    const base=task.name.slice(0,95)+'_处理任务';
    const related=jobs.filter(job=>job.source_ids.includes(task.id));
    const names=new Set(related.map(job=>job.name));
    if(!related.length)return base;
    let index=1;
    while(names.has(base.slice(0,100-String(index).length-1)+'_'+index))index++;
    return base.slice(0,100-String(index).length-1)+'_'+index;
  }
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
    if(!source)return;
    const nodes=(activeJob?.published?activeJob.configs:configs)[window.DPR_ACTIVE_ASSIGNMENT_STAGE]||{};
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
    sourceIds=job?.source_ids?.slice()||(sourceTask?[sourceTask.id]:[]);
    for(const key of Object.keys(configs))delete configs[key];Object.assign(configs,job?.configs||{});
    const linked=!!sourceTask;
    drawer.querySelectorAll('#processingTaskFilters+.dpr-task-filter-scope-help').forEach(el=>el.hidden=false);
    sourceContext.hidden=!job||drawer.dataset.mode!=='detail';
    detailActions.hidden=sourceContext.hidden;
    if(!sourceContext.hidden){
      sourceContext.innerHTML=`<span>来源采集任务</span><div class="dc-processing-sources">${job.source_ids.map(id=>{const task=collectionTasks.find(t=>t.id===id);return `<a href="${BASE}/${encodeURIComponent(id)}#processing">${esc(id)} · ${esc(task?.name||id)}</a>`;}).join('')}</div>`;
      const returnPath=params.get('return_to'),validReturn=returnPath?.startsWith('/data/tasks/')&&!returnPath.includes('\\');
      detailActions.innerHTML=`<a class="btn" href="${esc(validReturn?returnPath:'/data/tasks/'+encodeURIComponent(job.id))}">查看数据</a>${!job.published?`<button class="btn btn-primary" data-job-action="publish" data-job-id="${esc(job.id)}">发布</button>`:''}`;
    }else{sourceContext.replaceChildren();detailActions.replaceChildren();}
    drawer.dataset.collectionSource=sourceTask?.id||'';
    const sourceNotice=drawer.querySelector('.dpr-processing-filter-notice:not(.dpr-processing-filter-warning)');
    if(sourceNotice)sourceNotice.hidden=false;
    drawer.querySelector('[data-filter-group="processing"]').hidden=false;
    document.getElementById('processingTaskDrawerSubmit').textContent=job?'保存修改':'创建任务';
    if(job&&!job.published&&drawer.dataset.mode==='new')title.textContent='编辑处理任务';
    if(linked){
      window.DPR_TASK_FILTER_FIELDS['采集结论']={type:'single',options:['成功','失败']};
      const project=document.getElementById('processingTaskProject');
      const label=source.project_name||source.project;
      if(![...project.options].some(o=>o.value===label))project.add(new Option(label,label));project.value=label;project.disabled=true;
    }
    lockSourceFilter();
  }
  window.dprOpenProcessingTaskDrawer=function(mode,trigger){
    const isLinked=trigger?.dataset.collectionLinked==='true';
    // Clear the previous adapter context before the shared form renders its controls.
    source=null;activeJob=null;
    window.DPR_TASK_FILTER_FIELDS['采集结论']={type:'single',options:['成功','失败']};
    for(const config of Object.values(window.DPR_TASK_FILTER_FIELDS))config._collectionHidden=false;
    originalOpen(isLinked&&mode==='edit'&&!jobs.find(j=>j.id===trigger.dataset.taskId)?.published?'new':mode,trigger);
    if(!isLinked){context(null,null);return;}
    const job=jobs.find(j=>j.id===trigger.dataset.taskId);
    if(job){
      context({id:job.source_ids[0],name:trigger.dataset.sourceName||job.source_ids.join('、'),project:job.project,project_name:trigger.dataset.project},job);
      restoreSavedNodes();
      if(mode==='edit'&&job.published)drawer.querySelectorAll('#processingTaskFilters input,#processingTaskFilters select,#processingTaskFilters button').forEach(el=>el.disabled=true);
    }
  };
  const originalCopy=window.dprCopyProcessingTask;
  window.dprCopyProcessingTask=function(trigger){
    if(trigger?.dataset.collectionLinked!=='true')return originalCopy(trigger);
    const job=jobs.find(j=>j.id===trigger.dataset.taskId);if(!job)return;
    const more=trigger.closest('details')||window.DPR_OPEN_TASK_MORE;if(more)more.open=false;
    window.dprOpenProcessingTaskDrawer('new',trigger);
    activeJob=null;delete drawer.dataset.taskId;drawer.dataset.taskStatus='unpublished';
    sourceContext.hidden=true;detailActions.hidden=true;
    document.getElementById('processingTaskName').value=job.name+'（复制）';
    document.getElementById('processingTaskDrawerSubmit').textContent='创建任务';
    title.textContent='新建处理任务';
  };
  function sourceFromFilters(){
    if(activeJob||params.has('collection'))return;
    const filters=window.dprCurrentTaskFilters();
    const ids=filters.filter(f=>f[0]==='采集任务 ID'&&f[1]==='等于').flatMap(f=>splitIds(f[2]));
    const task=ids.length&&ids.every(id=>collectionTasks.some(t=>t.id===id))?collectionTasks.find(t=>t.id===ids[0]):null;
    if((task?.id||'')===(source?.id||'')){if(task){sourceIds=ids;}return;}
    context(task||null,null);
    if(task){sourceIds=ids;}
    if(!task)document.getElementById('processingTaskProject').disabled=false;
  }
  drawer.addEventListener('change',event=>{
    if(event.target.closest('#processingTaskBasicFilters'))sourceFromFilters();
  });
  window.dprCloseProcessingTaskPage=function(){
    if(saving)return;
    const returnTo=params.get('return_to');
    if(params.get('linked')===drawer.dataset.taskId&&returnTo&&returnTo.startsWith('/data/tasks/')&&!returnTo.includes('\\')){
      location.assign(returnTo);
      return;
    }
    if(source&&params.has('collection')&&!activeJob){location.assign(BASE+'/'+encodeURIComponent(source.id)+'#processing');return;}
    originalClose();showError('');
    if(activeJob){const url=new URL(location.href);url.searchParams.delete('linked');history.replaceState(null,'',url.pathname+url.search);}
    source=null;activeJob=null;
  };
  const originalRenderFilters=window.dprRenderTaskFilters;
  window.dprRenderTaskFilters=function(...args){const result=originalRenderFilters.apply(this,args);lockSourceFilter();return result;};
  const originalRemoveFilter=window.dprRemoveTaskFilter;
  window.dprRemoveTaskFilter=function(button){if(button.closest('[data-collection-source-locked]'))return;return originalRemoveFilter(button);};
  window.dprSubmitProcessingTask=async function(){
    sourceFromFilters();
    if(!source)return originalSubmit();
    if(saving)return;showError('');
    const button=document.getElementById('processingTaskDrawerSubmit');
    try{
      if(activeJob?.published){
        const expected=window.dprExpectedTaskValidation();if(!expected.valid)throw Error(expected.message);
        saving=true;button.disabled=true;button.textContent='正在保存…';
        await api('/tasks/'+activeJob.id,'PATCH',{revision:activeJob.revision,priority:Number(document.getElementById('processingTaskPriority').value),expected_value:document.getElementById('processingTaskExpectedValue').value});
        originalClose();source=null;activeJob=null;await loadJobs();window.toast('已保存处理任务');return;
      }
      if(drawer.querySelector('[data-processor-editing="true"]'))throw Error('请先保存或取消处理人修改');
      rememberNodes();
      const stages=Object.fromEntries(Object.entries(window.DPR_ENABLED_FLOW_STAGES).filter(([,enabled])=>enabled).map(([stage])=>[stage,window.DPR_SELECTED_FLOWS[stage]]));
      if(!Object.keys(stages).length){window.dprSwitchProcessingTaskPane(drawer.querySelector('[data-task-pane="flow"]'));throw Error('请至少开启并配置一个业务环节');}
      const selectedFilters=window.dprCurrentTaskFilters();
      const sourceFilter=selectedFilters.find(f=>f[0]==='采集任务 ID');
      if(!sourceFilter||sourceFilter[1]!=='等于')throw Error('请保留来源采集任务 ID 条件');
      sourceIds=splitIds(sourceFilter[2]);
      if(params.has('collection')&&(sourceIds.length!==1||sourceIds[0]!==params.get('collection')))throw Error('来源采集任务不可修改');
      if(!sourceIds.length||sourceIds.some(id=>!collectionTasks.some(t=>t.id===id&&t.project===source.project)))throw Error('采集来源必须属于同一项目');
      const name=document.getElementById('processingTaskName').value;
      saving=true;button.disabled=true;button.textContent='正在创建…';
      const expected=window.dprExpectedTaskValidation();if(!expected.valid)throw Error(expected.message);
      const body={name,source_ids:sourceIds,upstream_id:activeJob?.upstream_id||'',upstream_result:activeJob?.upstream_result||'合格',priority:Number(document.getElementById('processingTaskPriority').value),category:document.getElementById('processingTaskCategory').value,expected_mode:document.getElementById('processingTaskExpectedMode').value,expected_value:document.getElementById('processingTaskExpectedValue').value,filters:selectedFilters,stages,configs};
      if(activeJob)body.revision=activeJob.revision;
      const result=await api('/tasks'+(activeJob?'/'+activeJob.id:''),activeJob?'PATCH':'POST',body,{'Idempotency-Key':requestKey});
      window.location.assign(BASE+'/'+encodeURIComponent(source.id)+'?processing_created='+result.task.id+'#processing');
    }catch(error){showError(error.message);}
    finally{saving=false;button.disabled=false;button.textContent=activeJob?'保存修改':'创建任务';}
  };
  async function runAction(job,action){
    const labels={publish:`发布后开始按筛选条件处理数据。`,pause:'停止接收新数据，历史数据与处理结果保留。',resume:`重新开启后，符合条件的数据自动进入处理。采集状态不变。`};
    const dialog=document.getElementById('dc-processing-confirm');
    dialog.querySelector('h3').textContent={publish:'发布处理任务？',pause:'关闭处理任务？',resume:'开启处理任务？'}[action];
    dialog.querySelector('p').textContent=labels[action];dialog.querySelector('[data-confirm-error]').textContent='';
    dialog.querySelector('[data-existing-mode]')?.remove();
    if(action==='pause'){const choice=document.createElement('label');choice.dataset.existingMode='';choice.innerHTML='已有数据 <select><option value="continue">继续处理</option><option value="pause">暂停未完成数据</option></select>';dialog.querySelector('footer').before(choice);}
    const confirm=dialog.querySelector('[data-confirm-action]');confirm.disabled=false;
    confirm.onclick=async()=>{confirm.disabled=true;try{await api('/tasks/'+job.id+'/action','POST',{action,revision:job.revision,...(action==='admit'?{expected_count:job.new_count}:action==='publish'?{expected_count:job.candidate_count}:{}),...(action==='pause'?{existing_mode:dialog.querySelector('[data-existing-mode] select').value}:{})});dialog.close();await loadJobs();if(activeJob?.id===job.id&&drawer.getAttribute('aria-hidden')==='false')openJob(job.id);}catch(error){dialog.querySelector('[data-confirm-error]').textContent=error.message;confirm.disabled=false;}};
    dialog.showModal();
  }
  function flowBindings(job){return Object.entries(job.stages).map(([stage,name])=>[stage,name,window.DPR_PROCESSING_FLOWS.find(f=>f.name===name)?.version||'']);}
  function flowProgress(job){
    return `<div class="dpr-flow-binding-list">${job.stage_progress.map(p=>{
      const version=window.DPR_PROCESSING_FLOWS.find(f=>f.name===job.stages[p.stage])?.version||'';
      const percent=p.total?Math.round(p.done/p.total*100):0;
      return `<div class="dpr-flow-binding-chip" data-progress-stage="${esc(p.stage)}"><span>${esc(p.stage)}</span><div class="dpr-flow-binding-name"><b>${esc(job.stages[p.stage])}</b><code>${esc(version)}</code></div><div class="dpr-task-progress-line dpr-flow-progress-line"><i class="${p.stage==='质检'?'blue':'teal'}" style="width:${percent}%"></i><b>${p.done.toLocaleString()} / ${p.total.toLocaleString()} · ${percent}%</b></div></div>`;
    }).join('')}</div>`;
  }
  function row(job){
    const project=window.DPR_COLLECTION_PROJECTS?.find(p=>p.id===job.project)?.name||job.project;
    const data={taskId:job.id,taskName:job.name,project,taskCategory:job.category||'formal',priority:job.priority,enabled:String(job.enabled),expectedMode:job.expected_mode||'continuous',expectedValue:job.expected_value??'',flowedCount:job.total_count,filters:JSON.stringify(job.filters),flows:JSON.stringify(flowBindings(job)),assignments:JSON.stringify(Object.fromEntries(Object.entries(job.configs).map(([stage,nodes])=>[stage,Object.fromEntries(Object.entries(nodes).map(([name,node])=>[name,node.assignments]))]))),taskStatus:job.published?'published':'unpublished',collectionLinked:'true',sourceName:job.source_ids.join('、')};
    const attrs=Object.entries(data).map(([key,value])=>`data-${key.replace(/[A-Z]/g,c=>'-'+c.toLowerCase())}="${esc(value)}"`).join(' ');
    return `<tr data-collection-processing="${esc(job.id)}" data-processing-task-stage="${esc(Object.keys(job.stages).join(' '))}"><td><code>${esc(job.id)}</code></td><td><a class="dpr-task-name" href="/data/tasks/${encodeURIComponent(job.id)}"><b>${esc(job.name)}</b></a></td><td>${esc(project)}</td><td>${flowProgress(job)}</td><td>${job.published?`<label class="dpr-task-enable"><input type="checkbox" ${job.enabled?'checked':''} aria-label="切换任务 ${esc(job.id)} 状态" data-linked-toggle="${esc(job.id)}"><i></i></label>`:'-'}</td><td><span class="dpr-state ${job.published?'green':'gray'}">${job.published?'已发布':'未发布'}</span></td><td><span class="dpr-priority wb-priority ${job.priority>=7?'priority-high':job.priority>=4?'priority-medium':'priority-low'}">${job.priority}</span></td><td>${job.category==='informal'?'非正式':'正式'}</td><td>${esc(job.creator)}</td><td>${esc(job.created_at.replace('T',' ').slice(0,16))}</td><td><div class="dpr-task-actions"><a href="/data/tasks/${encodeURIComponent(job.id)}">数据</a><button ${attrs} onclick="dprOpenProcessingTaskDrawer('detail',this)">详情</button><button ${attrs} onclick="dprOpenProcessingTaskDrawer('edit',this)">编辑</button><details class="dpr-task-more" ontoggle="dprPositionTaskMore(this)"><summary>更多</summary><div class="dpr-task-more-menu"><button ${attrs} onclick="dprCopyProcessingTask(this)">复制</button><button ${attrs} data-job-action="publish" data-job-id="${esc(job.id)}" ${job.published?'disabled':''}>发布</button></div></details></div></td></tr>`;
  }
  async function loadJobs(){
    jobs=(await api('/tasks')).tasks;
    const body=document.querySelector('#dpr-processing-task-table tbody');body.querySelectorAll('[data-collection-processing]').forEach(e=>e.remove());body.insertAdjacentHTML('afterbegin',jobs.map(row).join(''));
  }
  async function openJob(id){
    try{
      const trigger=[...document.querySelectorAll('#dpr-processing-task-table .dpr-task-actions button[data-task-id]')].find(el=>el.dataset.taskId===id&&el.getAttribute('onclick')?.includes("'detail'"));
      if(!trigger)throw Error('处理任务不存在或已不可用');
      window.dprOpenProcessingTaskDrawer('detail',trigger);
      const url=new URL(location.href);url.searchParams.delete('new');url.searchParams.delete('collection');url.searchParams.set('linked',id);history.replaceState(null,'',url.pathname+url.search);
    }catch(error){window.toast(error.message);}
  }
  document.body.insertAdjacentHTML('beforeend','<dialog id="dc-processing-confirm"><h3></h3><p></p><p data-confirm-error role="alert"></p><footer><button class="btn" onclick="this.closest(\'dialog\').close()">取消</button><button class="btn btn-primary" data-confirm-action>确认</button></footer></dialog>');
  document.addEventListener('change',event=>{
    const toggle=event.target.closest('[data-linked-toggle]');if(!toggle)return;
    const job=jobs.find(j=>j.id===toggle.dataset.linkedToggle);if(!job)return;
    toggle.checked=job.enabled;
    runAction(job,job.enabled?'pause':'resume');
  });
  document.addEventListener('click',event=>{
    const el=event.target.closest('[data-job-action]');if(!el)return;event.preventDefault();
    const job=jobs.find(j=>j.id===el.dataset.jobId);if(job)runAction(job,el.dataset.jobAction);
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
      await loadJobs();
      if(params.get('linked')){await openJob(params.get('linked'));return;}
      if(params.get('collection')){
        const response=await fetch('/api/post-training-collection/tasks/'+encodeURIComponent(params.get('collection')),{cache:'no-store'});const data=await response.json();if(!response.ok)throw Error(data.error||'来源采集任务不可用');
        const t=data.task;t.project_name=shortNames[t.project]||t.project;
        originalOpen('new');context(t,null);
        if(params.get('collection_created')==='1'){
          sourceContext.hidden=false;
          sourceContext.innerHTML='<span role="status">采集任务已创建</span><div class="dc-processing-sources"><a href="'+BASE+'/'+encodeURIComponent(t.id)+'#records">'+esc(t.id)+' · '+esc(t.name)+'</a></div>';
        }
        const sourceNotice=drawer.querySelector('.dpr-processing-filter-notice:not(.dpr-processing-filter-warning)');
        if(sourceNotice)sourceNotice.hidden=false;
        drawer.querySelector('[data-filter-group="processing"]').hidden=false;
        // Reuse the complete original form; only prefill creation defaults.
        document.getElementById('processingTaskName').value=defaultProcessingName(t);
        document.getElementById('processingTaskPriority').value=String(t.priority>=7?9:t.priority>=4?6:3);
        document.getElementById('processingTaskCategory').value='formal';
        const expectedMode=document.getElementById('processingTaskExpectedMode');expectedMode.value='continuous';window.dprExpectedTaskModeChange(expectedMode);
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
