(() => {
 const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const outcomes=['直接成功','重试后成功','执行超时','环境异常','动作失败'];
 const badge=v=>`<span class="table-outline-tag table-outline-tag--${v.includes('成功')?'active':'danger'}">${v}</span>`;
 const table=(heads,body)=>`<div class="task-data-table eval-detail-table"><div class="task-data-table__scroll"><table><thead><tr>${heads.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div></div>`;
 window.openEvaluationTask=({host,row,mode,cases,sets,criteria,onSave})=>{
  const list=host.firstElementChild,header=document.querySelector('[data-model-title]').closest('header');list.hidden=true;header.hidden=true;
  const root=document.createElement('section');root.className='evaluation-detail';host.append(root);
  const back=()=>{root.remove();list.hidden=false;header.hidden=false;};
  root.innerHTML=`<task-page-header back title="${esc(mode==='create'?'新增评测任务':mode==='edit'?'编辑评测任务':mode==='data'?row.name:mode==='stats'?'评测统计':row.name)}" ${['data','stats'].includes(mode)?'action="导出"':''}></task-page-header><div class="evaluation-detail-body"></div>`;
  root.querySelector('task-page-header').addEventListener('header-back',back);
  const body=root.querySelector('.evaluation-detail-body');
  const selected=new Set(row?.caseIds||['BM_05','BM_07','BM_14','BM_37']);
  const records=Array.from({length:row?.done||0},(_,i)=>{const c=cases.filter(c=>selected.has(c.id))[i%selected.size]||cases[i%cases.length];return {id:String(600001+i),caseId:c.id,story:c.story,en:c.en,cn:c.cn,checkpoint:row.checkpoint.split(',')[i%row.checkpoint.split(',').length].trim(),result:outcomes[i%5],device:'MOZ1-'+row.id+'-'+String(i%4+1).padStart(2,'0'),operator:row.creator,time:'2026-04-05 '+String(10+i%10).padStart(2,'0')+':07'};});
  let exported=records;
  root.querySelector('task-page-header').addEventListener('header-action',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(exported,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`evaluation-${row.id}-${mode}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  if(mode==='data'||mode==='stats'){
   root.classList.add('evaluation-results-page');let page=1,pageSize=10;
   body.innerHTML=(mode==='stats'?`<div class="eval-metrics">${[['评测集',row.set],['Checkpoint',row.checkpoint],['Prompt 总数',new Set(records.map(r=>r.caseId)).size],['执行次数',records.length]].map(([l,v])=>`<div><span>${l}</span><strong>${esc(v)}</strong></div>`).join('')}</div>`:'')+`<form class="eval-detail-filters"><form-input name="caseId" label="用例 ID" placeholder="请输入用例 ID"></form-input>${mode==='data'?'<form-input name="id" label="数据 ID"></form-input><form-input name="story" label="Story"></form-input><form-select name="result" multiple label="评测结果（多选）">'+outcomes.map(v=>`<option>${v}</option>`).join('')+'</form-select>':''}${mode==='stats'?'<text-button variant="outline" icon="reset" icon-only aria-label="重置筛选" data-reset></text-button>':''}</form><div class="eval-results-frame"><div data-results></div><list-pagination total="0" page-size="10"></list-pagination></div>`;
   const expanded=new Set(mode==='stats'&&records.length?[records[0].story]:[]);let statisticsExpanded=false;
   const render=()=>{const form=body.querySelector('form'),data=new FormData(form),results=data.getAll('result');exported=records.filter(r=>['caseId','id','story'].every(k=>!data.get(k)||r[k].toLowerCase().includes(data.get(k).toLowerCase()))&&(!results.length||results.includes(r.result)));page=Math.min(page,Math.max(1,Math.ceil(exported.length/pageSize)));const pagination=body.querySelector('list-pagination');pagination.setAttribute('total',exported.length);pagination.setAttribute('page',page);const visible=exported.slice((page-1)*pageSize,page*pageSize);const target=body.querySelector('[data-results]');
    if(mode==='data'){target.classList.add('eval-media-results');target.innerHTML=table(['分组','数据 ID','用例 ID','视频','设备序列号','Checkpoint','评测结果','操作人','操作时间','操作'],visible.map((r,i)=>`<tr><td>1:2:${i+1}</td><td>${r.id}</td><td>${r.caseId}</td><td><div class="task-record-media"><div class="task-record-media-description"><strong class="task-record-media-description__label">${esc(r.cn)}</strong><span>${esc(r.en)}</span></div><div class="task-record-videos">${['cam_high','cam_left_wrist','cam_right_wrist'].map(c=>`<div class="task-record-video eval-media-empty" role="img" aria-label="${c} 暂无视频源"><span>${c}</span><small>暂无视频源</small></div>`).join('')}</div></div></td><td>${esc(r.device)}</td><td>${esc(r.checkpoint)}</td><td>${badge(r.result)}</td><td>${esc(r.operator)}</td><td>${r.time}</td><td><button data-preview="${r.id}">详情</button></td></tr>`).join(''));target.querySelectorAll('[data-preview]').forEach(b=>b.onclick=()=>{const r=exported.find(r=>r.id===b.dataset.preview);window.openDataPreview({...r,frames:0,duration:'—'});});}
    else{
     const groups=[...new Set(exported.map(r=>r.story))].map(story=>({story,ids:[...new Set(exported.filter(r=>r.story===story).map(r=>r.caseId))]}));
     page=Math.min(page,Math.max(1,Math.ceil(groups.length/pageSize)));pagination.setAttribute('total',groups.length);pagination.setAttribute('page',page);
     const visibleGroups=groups.slice((page-1)*pageSize,page*pageSize);
     const max=10;
     const cells=rows=>Array.from({length:max},(_,i)=>`<td>${rows[i]?badge(rows[i].result):'—'}</td>`).join('');
     const summary=rows=>!statisticsExpanded?`共 ${rows.length} 次`:`<div class="eval-result-breakdown">${['环境异常','动作失败','执行超时','重试后成功','直接成功'].map(result=>{const count=rows.filter(r=>r.result===result).length;return count?`<div>${badge(result)}<span>${count} 次</span><span>${(count/rows.length*100).toFixed(1)}%</span></div>`:'';}).join('')}</div>`;
     target.classList.add('eval-stat-results');
     target.innerHTML=table(['用例 ID','提示词',...Array.from({length:max},(_,i)=>'T'+(i+1)),`<div class="eval-result-heading"><span>结果统计</span><button data-statistics-toggle aria-expanded="${statisticsExpanded}">${statisticsExpanded?'收起详情':'展开详情'}</button></div>`],visibleGroups.map(g=>{
      const groupRows=exported.filter(r=>r.story===g.story),open=expanded.has(g.story);
      const parent=`<tr class="eval-stat-parent"><td></td><td><button data-expand="${esc(g.story)}" aria-expanded="${open}">${open?'▾':'▸'} ${esc(g.story)}</button></td>${cells(groupRows)}<td>${summary(groupRows)}</td></tr>`;
      return parent+(open?g.ids.map(id=>{const rows=exported.filter(r=>r.caseId===id),c=cases.find(c=>c.id===id);return `<tr class="eval-stat-child"><td>${esc(id)}</td><td><div><strong>${esc(c.cn)}</strong><small>${esc(c.en)}</small></div></td>${cells(rows)}<td>${summary(rows)}</td></tr>`;}).join(''):'');
     }).join(''));
     target.querySelectorAll('[data-expand]').forEach(b=>b.onclick=()=>{expanded.has(b.dataset.expand)?expanded.delete(b.dataset.expand):expanded.add(b.dataset.expand);render();});
     target.querySelector('[data-statistics-toggle]').onclick=()=>{statisticsExpanded=!statisticsExpanded;render();};
    }

    if(exported.length)customElements.get('task-data-table').enhanceFixedEdges(target.querySelector('.eval-detail-table'),1,1);
    if(!exported.length)target.innerHTML='<p class="command-empty">暂无符合条件的数据</p>';
   };body.querySelector('list-pagination').addEventListener('page-change',e=>{page=e.detail.page;pageSize=e.detail.pageSize;render();});body.querySelector('form').oninput=body.querySelector('form').onchange=()=>{page=1;render();};body.querySelector('form').onsubmit=e=>e.preventDefault();body.querySelector('[data-reset]')?.addEventListener('click',()=>{body.querySelector('form').reset();page=1;render();});render();return;
  }
  const editable=mode==='create'||mode==='edit';
  const input=(name,label,value='',type='text')=>`<form-input name="${name}" label="${label}" type="${type}" value="${esc(value)}" ${editable?'':'disabled'}></form-input>`;
  const select=(name,label,values,value)=>`<form-select name="${name}" label="${label}" ${editable?'':'disabled'}>${values.map(v=>`<option ${v===value?'selected':''}>${esc(v)}</option>`).join('')}</form-select>`;
  body.innerHTML=`<form class="eval-task-form"><details class="task-filter-group" open data-eval-step="0"><summary>基本信息</summary><div class="eval-group-content"><div class="eval-form-grid">${input('name','任务名称',row?.name||'')}${select('project','所属项目',['预训练评测','后训练评测'],row?.project)}${input('taskMode','任务模式','Evaluation')}${select('priority','优先级',['高','中','低'],row?.priority||'中')}${input('due','预期交付日期',row?.due||'','date')}${input('status','状态',row?.status||'未发布')}<label class="eval-form-wide">任务描述<textarea name="description" ${editable?'':'disabled'} placeholder="简要描述任务目的、关注点等">${esc(row?.description||'')}</textarea></label></div></div></details><details class="task-filter-group" open data-eval-step="1"><summary>评测配置</summary><div class="eval-group-content"><div class="eval-form-grid">${select('checkpoint','Checkpoint',['Spirit v1.5','Spirit v1.6-alpha','Spirit v1.6-rc1',...(row?.checkpoint?[row.checkpoint]:[])],row?.checkpoint)}${input('total','评测次数',row?.total||30,'number')}${select('criterion','评价标准',criteria.map(c=>c.name),row?.criterion)}${select('set','评测集',sets.map(s=>s.name),row?.set)}</div><h3>评测用例列表</h3><div data-cases></div></div></details><p role="alert" data-error></p></form>`;
  const form=body.querySelector('form');
  const layout=document.createElement('div');layout.className='creator-layout eval-creator-layout';
  const nav=document.createElement('task-step-nav');nav.setAttribute('steps','基本信息,评测配置');
  const main=document.createElement('main');main.className='creator-main';
  body.append(layout);layout.append(nav,main);main.append(form);
  const switchStep=index=>{nav.active=index;form.querySelectorAll('[data-eval-step]').forEach(section=>{section.hidden=Number(section.dataset.evalStep)!==index;});};
  nav.addEventListener('step-change',e=>switchStep(e.detail));switchStep(0);
  body.querySelector('[name=due] input').type='date';
  const countInput=body.querySelector('[name=total] input');countInput.type='number';countInput.min='1';countInput.step='1';
  body.querySelector('[name=taskMode] input').disabled=true;body.querySelector('[name=status] input').disabled=true;
  const drawCases=()=>{body.querySelector('[data-cases]').innerHTML=table(['评测项','用例 ID','Stage','Story','prompt_EN','prompt_CN','Skill 标签','Factor'],cases.filter(c=>editable||selected.has(c.id)).map(c=>`<tr><td><input type="checkbox" data-case="${c.id}" aria-label="选择 ${c.id}" ${selected.has(c.id)?'checked':''} ${editable?'':'disabled'}></td>${['id','stage','story','en','cn','skill','factor'].map(k=>`<td>${esc(c[k])}</td>`).join('')}</tr>`).join(''));};drawCases();
  body.querySelector('[data-cases]').onchange=e=>{if(e.target.dataset.case)e.target.checked?selected.add(e.target.dataset.case):selected.delete(e.target.dataset.case);};
  root.insertAdjacentHTML('beforeend',`<footer class="eval-detail-footer"><text-button variant="outline" data-cancel>${editable?'取消':'关闭'}</text-button>${editable?'<text-button variant="primary" data-save>保存任务</text-button>':''}</footer>`);root.querySelector('[data-cancel]').onclick=back;
  body.querySelector('form').onsubmit=e=>e.preventDefault();
  root.querySelector('[data-save]')?.addEventListener('click',()=>{const data=Object.fromEntries(new FormData(body.querySelector('form')));if(!data.name.trim()||!data.due||!Number.isInteger(Number(data.total))||Number(data.total)<1||!selected.size){switchStep(!data.name.trim()||!data.due?0:1);body.querySelector('[data-error]').textContent='请填写任务名称、交付日期、正整数评测次数，并选择至少一个用例。';return;}onSave({...data,total:Number(data.total),caseIds:[...selected]});back();});
 };
})();
