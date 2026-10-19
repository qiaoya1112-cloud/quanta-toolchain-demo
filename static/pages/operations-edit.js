(() => {
 const page=document.body.dataset.pageId;
 const kinds={'project-management':'项目','user-group-management':'用户组','supplier-management':'供应商'};
 if(!kinds[page])return;
 const table=document.querySelector('task-data-table'),key='quanta-operations-edits-v1-'+page;
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const people=['joanna.qiao','刘燕新','包媛桐','供应商 A-017','Wei Zhang','供应商 A-026','标注抽验-008','光轮-QC-021','王一帆','陈晨','Lance Li','Min Chen','Emma Wilson','Olivia Davis'];
 let saved={};try{saved=JSON.parse(localStorage.getItem(key)||'{}');}catch{}
 const tags=values=>values.map(v=>'<span class="table-person-tag">'+esc(v)+'</span>').join(' ');
 function apply(row,data){
  row.cells[1].innerHTML='<strong>'+esc(data.name)+'</strong>';
  if(page==='project-management'){
   row.cells[2].textContent=data.description;
   row.cells[3].innerHTML=tags(data.owners);
   row.cells[4].innerHTML='<span class="table-outline-tag '+(data.status==='启用'?'table-outline-tag--success':'')+'">'+esc(data.status)+'</span>';
  }else if(page==='user-group-management')row.cells[3].textContent=data.members.length+' 人';
  else row.cells[2].innerHTML=data.stages.map(s=>'<span class="table-outline-tag table-progress-type '+(s==='质检'?'is-quality':'')+'">'+esc(s)+'</span>').join(' ');
 }
 table.querySelectorAll('tbody tr').forEach(row=>{const data=saved[row.cells[0].textContent.trim()];if(data)apply(row,data);});
 const input=(name,label,value,extra='')=>'<form-input name="'+name+'" label="'+label+'" value="'+esc(value)+'" '+extra+'></form-input>';
 table.addEventListener('row-action',event=>{
  if(event.detail.action!=='edit')return;
  const row=table.querySelector('tr[data-row="'+event.detail.row+'"]');if(!row)return;
  const id=row.cells[0].textContent.trim(),project=page==='project-management',group=page==='user-group-management';
  const data=saved[id]||{name:row.cells[1].textContent.trim(),description:project?row.cells[2].textContent.trim():'',status:project?row.cells[4].textContent.trim():'',owners:project?[...row.cells[3].querySelectorAll('.table-person-tag')].map(t=>t.textContent):[],admins:['joanna.qiao','包媛桐'],members:group?Array.from({length:parseInt(row.cells[3].textContent)||0},(_,i)=>people[i]||'演示成员 '+(i+1)):[],stages:['质检','标注'].filter(s=>row.cells[2].textContent.includes(s))};
  const drawer=document.createElement('app-drawer');drawer.className='operations-edit';drawer.setAttribute('heading','编辑'+kinds[page]);
  drawer.innerHTML='<form class="operations-edit-form">'+(group?input('id','用户组标识',id,'disabled'):'')+input('name',(page==='supplier-management'?'':'* ')+kinds[page]+'名称',data.name)+(project?input('description','描述',data.description,'multiline')+'<form-select name="status" label="状态"><option>启用</option><option>停用</option></form-select><div data-picker="owners"></div><div data-picker="admins"></div>':group?'<div data-picker="members"></div>':'<fieldset><legend>支持业务环节</legend>'+['质检','标注'].map(s=>'<form-checkbox label="'+s+'" name="stage" value="'+s+'" '+(data.stages.includes(s)?'checked':'')+'></form-checkbox>').join('')+'</fieldset>')+'<p role="alert"></p></form><div drawer-footer><text-button variant="outline" data-cancel>取消</text-button><text-button variant="primary" data-save>保存</text-button></div>';
  document.body.append(drawer);
  const form=drawer.querySelector('form'),selection={};
  drawer.querySelectorAll('[data-picker]').forEach(host=>{
   const field=host.dataset.picker,label=({owners:'负责人',admins:'管理员',members:'成员'})[field];
   selection[field]=new Set(data[field]);
   const candidates=[...new Set([...people,...data[field]])];
   host.innerHTML='<div class="operations-picker-heading"><span>'+(field==='members'?'':'<span class="operations-required">*</span> ')+label+'</span><small data-count></small></div><div class="operations-picker-control"><div class="operations-picker-tags"></div><input class="operations-picker-search" aria-label="搜索并选择'+label+'" placeholder="搜索并选择'+label+'" autocomplete="off" aria-expanded="false"><button type="button" class="operations-picker-toggle" aria-label="展开'+label+'选项" aria-expanded="false">⌄</button></div><div class="operations-picker-options" hidden></div>';
   const searchInput=host.querySelector('.operations-picker-search'),menu=host.querySelector('.operations-picker-options');
   const setOpen=open=>{menu.hidden=!open;searchInput.setAttribute('aria-expanded',String(open));host.querySelector('.operations-picker-toggle').setAttribute('aria-expanded',String(open));};
   searchInput.addEventListener('focus',()=>setOpen(true));
   host.querySelector('.operations-picker-toggle').onclick=()=>setOpen(menu.hidden);
   host.addEventListener('keydown',e=>{if(e.key==='Escape'&&!menu.hidden){e.preventDefault();e.stopPropagation();searchInput.focus();setOpen(false);}if(e.key==='Enter'&&e.target===searchInput)e.preventDefault();});
   drawer.addEventListener('click',e=>{if(!host.contains(e.target))setOpen(false);});
   host.addEventListener('focusout',e=>{if(e.relatedTarget&&!host.contains(e.relatedTarget))setOpen(false);});
   const refresh=()=>{
    host.querySelector('[data-count]').textContent='已选 '+selection[field].size+' 人';
    host.querySelector('.operations-picker-tags').innerHTML=[...selection[field]].map(v=>'<button type="button" class="table-person-tag" data-person="'+esc(v)+'" aria-label="移除 '+esc(v)+'">'+esc(v)+' ×</button>').join('');
    const search=searchInput.value.toLowerCase();
    host.querySelector('.operations-picker-options').innerHTML=candidates.filter(v=>v.toLowerCase().includes(search)).map(v=>'<label><input type="checkbox" value="'+esc(v)+'" '+(selection[field].has(v)?'checked':'')+'>'+esc(v)+'</label>').join('');
   };
   host.addEventListener('input',e=>{if(e.target.type!=='checkbox')refresh();});
   host.addEventListener('change',e=>{if(e.target.type==='checkbox'){e.target.checked?selection[field].add(e.target.value):selection[field].delete(e.target.value);refresh();}});
   host.addEventListener('click',e=>{const b=e.target.closest('[data-person]');if(b){selection[field].delete(b.dataset.person);refresh();}});
   refresh();
  });
  if(project)form.querySelector('form-select').value=data.status;
  drawer.querySelector('[data-cancel]').onclick=()=>drawer.close();
  drawer.addEventListener('drawer-close',()=>drawer.remove(),{once:true});
  const save=()=>{
   const next={...data,name:form.querySelector('[name="name"]').value.trim()};
   const alert=form.querySelector('[role="alert"]');
   if(!next.name){alert.textContent='请填写'+kinds[page]+'名称';form.querySelector('[name="name"] input').focus();return;}
   if(project){
    next.description=form.querySelector('[name="description"]').value.trim();next.status=form.querySelector('form-select').value;
    next.owners=[...selection.owners];next.admins=[...selection.admins];
    if(!next.owners.length||!next.admins.length){alert.textContent='请至少选择一位负责人和管理员';return;}
   }else if(group)next.members=[...selection.members];
   else next.stages=[...form.querySelectorAll('form-checkbox')].filter(c=>c.checked).map(c=>c.value);
   const updated={...saved,[id]:next};
   try{localStorage.setItem(key,JSON.stringify(updated));}catch{alert.textContent='本地保存失败，请检查浏览器存储后重试';return;}
   saved=updated;apply(row,next);drawer.close();document.querySelector('[data-feedback]').textContent='已保存';
  };
  drawer.querySelector('[data-save]').onclick=save;
  form.onsubmit=e=>{e.preventDefault();save();};
  document.querySelector('[data-feedback]').textContent='';
  drawer.show();
 });
})();
