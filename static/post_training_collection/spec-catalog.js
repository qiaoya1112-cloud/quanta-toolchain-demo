/* 【新】Local collection specification catalog: names and URLs only. */
(() => {
  'use strict';
  const api='/api/post-training-collection/specs', editor=document.getElementById('dc-spec-editor'), form=document.getElementById('dc-spec-editor-form');
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let specs=[],editing=null,saving=false,origin=null;
  async function request(url,options={}) {
    const response=await fetch(url,{...options,headers:{'Content-Type':'application/json'},cache:'no-store'});
    const data=await response.json();if(!response.ok)throw Object.assign(new Error(data.error||'请检查输入后重试'),{errors:data.errors});return data;
  }
  function render() {
    const q=document.getElementById('dc-catalog-search').value.trim().toLowerCase(), rows=specs.filter(s=>(s.name+' '+s.url).toLowerCase().includes(q));
    document.getElementById('dc-catalog-rows').innerHTML=rows.length?rows.map(s=>`<tr><td title="${esc(s.name)}">${esc(s.name)}</td><td><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer" title="${esc(s.url)}">${esc(s.url)}</a></td><td>${s.task_count}</td><td>${esc(s.creator)}</td><td>${esc(s.updated_at.replace('T',' '))}</td><td><button type="button" class="dc-catalog-edit" data-id="${esc(s.id)}">编辑</button></td></tr>`).join(''):'<tr><td class="dc-catalog-empty" colspan="6">'+(q?'没有匹配的采集规范':'暂无采集规范，点击“新增采集规范”添加')+'</td></tr>';
    document.getElementById('dc-catalog-count').textContent=`共 ${rows.length} 个规范`;
  }
  async function load() {
    const error=document.getElementById('dc-catalog-error');
    try{specs=(await request(api)).specs;error.textContent='';render();}catch(e){error.textContent=e.message;document.getElementById('dc-catalog-rows').innerHTML='<tr><td colspan="6" class="dc-catalog-empty">加载失败，请点击刷新重试</td></tr>';}
  }
  function open(spec=null) {
    editing=spec;origin=document.activeElement;form.reset();form.querySelectorAll('.error').forEach(e=>e.textContent='');
    document.getElementById('dc-spec-editor-title').textContent=spec?'编辑采集规范':'新增采集规范';
    document.getElementById('dc-spec-name').value=spec?.name||'';document.getElementById('dc-spec-url').value=spec?.url||'';
    const impact=document.getElementById('dc-spec-impact');impact.hidden=!spec?.task_count;impact.textContent=`保存后将同步更新 ${spec?.task_count||0} 个关联任务的规范名称或链接，并记录日志。`;
    editor.showModal();document.getElementById('dc-spec-name').focus();
  }
  editor.addEventListener('close',()=>origin?.focus());
  editor.addEventListener('cancel',e=>{if(saving)e.preventDefault();});
  editor.querySelectorAll('[data-spec-close]').forEach(b=>b.onclick=()=>{if(!saving)editor.close();});
  document.getElementById('dc-catalog-create').onclick=()=>open();document.getElementById('dc-catalog-refresh').onclick=load;
  document.getElementById('dc-catalog-search').addEventListener('input',render);
  document.getElementById('dc-catalog-rows').onclick=e=>{const b=e.target.closest('.dc-catalog-edit');if(b)open(specs.find(s=>s.id===b.dataset.id));};
  form.addEventListener('submit',async e=>{
    e.preventDefault();if(saving)return;saving=true;form.querySelectorAll('button').forEach(b=>b.disabled=true);form.querySelectorAll('.error').forEach(e=>e.textContent='');
    try{
      await request(api+(editing?'/'+editing.id:''),{method:editing?'PATCH':'POST',body:JSON.stringify({name:document.getElementById('dc-spec-name').value,url:document.getElementById('dc-spec-url').value,...(editing?{revision:editing.revision}:{})})});
      editor.close();await load();
    }catch(error){if(error.errors){for(const [key,value] of Object.entries(error.errors)){const el=form.querySelector(`[data-error="${key}"]`);if(el)el.textContent=value;}form.querySelector(`#dc-spec-${Object.keys(error.errors)[0]}`)?.focus();}else form.querySelector('[data-error="form"]').textContent=error.message;}
    finally{saving=false;form.querySelectorAll('button').forEach(b=>b.disabled=false);}
  });
  load();
})();
