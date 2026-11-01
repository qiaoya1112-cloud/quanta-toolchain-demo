/* 【新】Local collection specification catalog: names, projects and URLs. */
(() => {
  'use strict';
  const api='/api/post-training-collection/specs', editor=document.getElementById('dc-spec-editor'), form=document.getElementById('dc-spec-editor-form');
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let specs=[],saving=false,origin=null;
  async function request(url,options={}) {
    const response=await fetch(url,{...options,headers:{'Content-Type':'application/json'},cache:'no-store'});
    const data=await response.json();if(!response.ok)throw Object.assign(new Error(data.error||'请检查输入后重试'),{errors:data.errors});return data;
  }
  function render() {
    const q=document.getElementById('dc-catalog-search').value.trim().toLowerCase(),project=document.getElementById('dc-catalog-project').value,owner=document.getElementById('dc-catalog-owner').value.trim().toLowerCase();
    const rows=specs.filter(s=>String(s.name||'').toLowerCase().includes(q)&&(!project||(s.project_names||[]).includes(project))&&(!owner||String(s.creator||'').toLowerCase().includes(owner)));
    document.getElementById('dc-catalog-rows').innerHTML=rows.length?rows.map(s=>{const project=(s.project_names||[]).join('、')||'—';return `<tr><td title="${esc(s.name)}">${esc(s.name)}</td><td title="${esc(project)}">${esc(project)}</td><td><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer" title="${esc(s.url)}">${esc(s.url)}</a></td><td>${esc(s.creator)}</td><td>${esc(s.updated_at.replace('T',' '))}</td></tr>`;}).join(''):'<tr><td class="dc-catalog-empty" colspan="5">'+(q||project||owner?'没有匹配的采集规范':'暂无采集规范，点击“新增采集规范”添加')+'</td></tr>';
  }
  async function load() {
    const error=document.getElementById('dc-catalog-error');
    try{const data=await request(api);specs=data.specs;document.getElementById('dc-spec-project').innerHTML='<option value="">请选择所属项目</option>'+(data.projects||[]).map(p=>`<option value="${esc(p.id)}">${esc(p.name)}</option>`).join('');const projectFilter=document.getElementById('dc-catalog-project'),selected=projectFilter.value;const projectNames=[...new Set([...(data.projects||[]).map(p=>p.name),...specs.flatMap(s=>s.project_names||[])])];projectFilter.innerHTML='<option value="">全部项目</option>'+projectNames.map(name=>`<option value="${esc(name)}">${esc(name)}</option>`).join('');projectFilter.value=projectNames.includes(selected)?selected:'';error.textContent='';render();}catch(e){error.textContent=e.message;document.getElementById('dc-catalog-rows').innerHTML='<tr><td colspan="5" class="dc-catalog-empty">加载失败，请点击查询重试</td></tr>';}
  }
  function open() {
    origin=document.activeElement;form.reset();form.querySelectorAll('.error').forEach(e=>e.textContent='');
    editor.showModal();document.getElementById('dc-spec-name').focus();
  }
  editor.addEventListener('close',()=>origin?.focus());
  editor.addEventListener('cancel',e=>{if(saving)e.preventDefault();});
  editor.querySelectorAll('[data-spec-close]').forEach(b=>b.onclick=()=>{if(!saving)editor.close();});
  document.getElementById('dc-catalog-create').onclick=()=>open();
  document.getElementById('dc-catalog-filters').addEventListener('submit',e=>{e.preventDefault();load();});
  document.getElementById('dc-catalog-clear').onclick=()=>{document.getElementById('dc-catalog-filters').reset();load();};
  document.getElementById('dc-catalog-search').addEventListener('input',render);
  document.getElementById('dc-catalog-project').addEventListener('change',render);
  document.getElementById('dc-catalog-owner').addEventListener('input',render);
  form.addEventListener('submit',async e=>{
    e.preventDefault();if(saving)return;saving=true;form.querySelectorAll('button').forEach(b=>b.disabled=true);form.querySelectorAll('.error').forEach(e=>e.textContent='');
    try{
      await request(api,{method:'POST',body:JSON.stringify({name:document.getElementById('dc-spec-name').value,project:document.getElementById('dc-spec-project').value,url:document.getElementById('dc-spec-url').value})});
      editor.close();await load();
    }catch(error){if(error.errors){for(const [key,value] of Object.entries(error.errors)){const el=form.querySelector(`[data-error="${key}"]`);if(el)el.textContent=value;}form.querySelector(`#dc-spec-${Object.keys(error.errors)[0]}`)?.focus();}else form.querySelector('[data-error="form"]').textContent=error.message;}
    finally{saving=false;form.querySelectorAll('button').forEach(b=>b.disabled=false);}
  });
  load();
})();
