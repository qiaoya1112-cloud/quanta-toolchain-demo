(() => {
  'use strict';
  let payload = JSON.parse(document.getElementById('jcPayload').textContent);
  const byId = id => document.getElementById(id);
  const escape = text => String(text ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  const base = '/data/job-centers/' + payload.center;
  const query = '?task=' + encodeURIComponent(payload.task.id);
  let busy = false, previousFocus;
  function filterTree() {
    const search = byId('jcTreeSearch').value.trim().toLocaleLowerCase();
    let matches = 0;
    payload.groups.forEach(group => {
      const parent = [...document.querySelectorAll('[data-group]')].find(item => item.dataset.group === String(group.id));
      const match = group.name.toLocaleLowerCase().includes(search) || (payload.center === 1 && String(group.id).includes(search));
      parent.hidden = !match;
      if (match) matches++;
    });
    byId('jcTreeEmpty').hidden = matches > 0;
  }
  byId('jcTreeSearch').addEventListener('input', filterTree);
  async function request(path, body) {
    const response = await fetch(base + path + query, body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '操作失败，请重试');
    return data;
  }
  function render() {
    const labels = {collection_task_id:'采集任务ID',supplier:'供应商',operator:'操作员'};
    const filters = Object.entries(payload.conditions).filter(([,value]) => value);
    byId('jcConditionSummary').textContent = filters.length ? filters.map(([key,value]) => labels[key] + '：' + value).join(' · ') : '无条件';
    const batch = payload.task.execution_unit === 'batch';
    byId('jcRows').innerHTML = payload.jobs.length ? payload.jobs.map(job => {
      const action = '<a class="btn btn-primary" href="'+escape(job.url)+'">处理</a>';
      const extra = batch ? '' : '<td>'+escape(job.description)+'</td><td>第 '+escape(job.current_round)+' 轮</td><td>'+escape(job.updated_at)+'</td>';
      return '<tr><td><code>'+escape(job.record_ids.slice(0,10).join('、'))+'</code></td><td>'+escape(job.source_action)+'</td>'+extra+'<td>'+action+'</td></tr>';
    }).join('') : '<tr><td colspan="'+(batch?3:6)+'" class="jc-empty"><b>暂无已领取数据</b>点击上方“领取数据”，获取当前节点的数据</td></tr>';
    payload.groups.forEach(group => {
      const parent = [...document.querySelectorAll('[data-group]')].find(item => item.dataset.group===group.id);
      parent.querySelector('.jc-parent-count').textContent=group.count;
      group.nodes.forEach(node => parent.querySelector('[data-node="'+node.id+'"]').querySelector('.jc-node-count').textContent=node.count);
    });
    filterTree();
  }
  function feedback(message) {
    const target=byId('jcError');target.textContent=message;target.hidden=!message;
  }
  async function run(action) {
    if (busy) return;
    busy=true;['jcClaim','jcConditions','jcSaveConditions','jcNoConditions'].forEach(id=>byId(id).disabled=true);
    try { await action(); } finally { busy=false;['jcClaim','jcConditions','jcSaveConditions','jcNoConditions'].forEach(id=>byId(id).disabled=false); }
  }
  byId('jcClaim').addEventListener('click',()=>run(async()=>{
    feedback('');
    try {payload=await request('/claim',{});render();}
    catch(error){feedback(error.message);try{payload=await request('/state');render();}catch{}}
  }));
  ['jcWorkbenchTab','jcHistoryTab'].forEach((id,index)=>byId(id).addEventListener('click',()=>{
    ['jcWorkbenchTab','jcHistoryTab'].forEach((tab,i)=>{byId(tab).classList.toggle('active',i===index);byId(tab).setAttribute('aria-selected',String(i===index));});
    byId('jcWorkbench').hidden=index!==0;byId('jcHistory').hidden=index!==1;
  }));
  const form=byId('jcConditionForm'), mask=byId('jcConditionMask');
  const close=()=>{if(busy)return;mask.hidden=true;previousFocus?.focus();};
  byId('jcConditions').addEventListener('click',()=>{
    previousFocus=document.activeElement;
    [...form.elements].filter(item=>item.name).forEach(item=>item.value=payload.conditions[item.name]||'');
    byId('jcConditionError').hidden=true;mask.hidden=false;form.querySelector('input').focus();
  });
  byId('jcCancelConditions').addEventListener('click',close);
  mask.addEventListener('click',event=>{if(event.target===mask)close();});
  mask.addEventListener('keydown',event=>{
    if(event.key==='Escape')close();
    if(event.key==='Tab'){
      const fields=[...mask.querySelectorAll('input,button')].filter(item=>!item.disabled);
      const first=fields[0],last=fields[fields.length-1];
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
    }
  });
  async function save(body){
    try{payload=await request('/state',body);render();mask.hidden=true;previousFocus?.focus();feedback('');}
    catch(error){byId('jcConditionError').textContent=error.message;byId('jcConditionError').hidden=false;}
  }
  form.addEventListener('submit',event=>{event.preventDefault();run(()=>save(Object.fromEntries(new FormData(form))));});
  byId('jcNoConditions').addEventListener('click',()=>run(()=>save({})));
  window.addEventListener('pageshow',event=>{if(event.persisted)location.reload();});
  render();
})();
