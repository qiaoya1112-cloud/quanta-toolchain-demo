(() => {
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const templates=[
 ['14','台面纸品归入文件柜','书房','打印纸、文件、档案袋、文件柜','不少于3类办公用品（办公用纸、文件、档案袋等），同款每类不超过1件，散放在打印机旁台面上。','办公用品分类放入文件柜，台面无遗留物品。'],
 ['13','桌面文具归入抽屉笔筒','书房','笔、橡皮、便签、笔筒、文具盒、抽屉','不少于3类文具（笔、橡皮、便签等）散落在书桌台面上，同款每类不超过1件。','文具放入笔筒、文具盒或抽屉，桌面整洁。'],
 ['18','信封从文件夹转移归位','书房','信封、文件夹','文件夹里装着不少于3个信封，同款每类不超过1件，旁边另一个空文件夹敞开放着。','信封全部转入空文件夹内，原文件夹清空。'],
 ['100021','玻璃杯入柜','厨房','玻璃杯、橱柜、托盘','玻璃杯放在操作台，柜门打开。','玻璃杯平稳放入柜内指定位置，柜门闭合。'],
 ['100036','餐盘入架','厨房','餐盘、沥水架','餐盘放在台面，沥水架有空槽。','餐盘竖直插入空槽并保持稳定。'],
 ['100031','抹布归位','厨房','抹布、水槽、挂钩','抹布散放在水槽旁。','抹布整齐放回指定收纳位置。'],
 ['100044','遥控器收纳','客厅','遥控器、收纳盒','遥控器散放在茶几上。','遥控器放入收纳盒。'],
 ['100060','办公文具整理','办公区','办公用纸、文件、档案袋','办公文具散放在桌面。','文具分类放入收纳盒。']
 ];
 const catalog=templates.flatMap(([id,name,workspace,props,initial,target])=>[7,6,5].map(version=>({key:id+'-V'+version,id,name,iteration:'目标态',version:'V'+version,workspace,scene:workspace==='办公区'?'办公':'家庭',props,description:`【初始状态】${initial}【结束状态】${target}【时长上限】1分钟`,difficulty:3,mirror:'是'})));
 function packageInfo(data,editing,onConfirm){
  const modal=document.createElement('process-action-dialog');modal.setAttribute('variant','command-package-info');document.body.append(modal);
  const dialog=modal.querySelector('dialog');dialog.classList.add('command-dialog','package-info-dialog');dialog.setAttribute('aria-label',editing?'编辑指令包信息':'创建指令包');
  modal.querySelector('h2').textContent=editing?'编辑指令包信息':'创建指令包';
  const fields=modal.querySelector('.flow-info-fields');fields.innerHTML=`<form-input name="name" label="指令包名称" value="${esc(data.name)}" placeholder="请输入指令包名称" required></form-input><form-select name="scene" label="场景" value="${esc(data.scene)}" ${editing?'disabled':''}><option>家庭</option><option>办公</option>${data.scene==='—'?'<option>—</option>':''}</form-select><form-select name="workspace" label="工作区" value="${esc(data.workspace)}" ${editing?'disabled':''}></form-select>`;
  const scene=fields.querySelector('[name="scene"]'),workspace=fields.querySelector('[name="workspace"]');
  function workspaces(value){const options=editing?[data.workspace]:scene.value==='办公'?['办公区']:['书房','厨房','客厅'];workspace.control.innerHTML=options.map(v=>`<option>${esc(v)}</option>`).join('');workspace.value=options.includes(value)?value:options[0];workspace.syncSelect?.();}
  workspaces(data.workspace);scene.addEventListener('value-change',()=>workspaces(''));
  modal.querySelector('footer [data-dismiss] button').textContent='取消';modal.querySelector('[data-confirm] button').textContent=editing?'保存':'创建并进入';
  modal.addEventListener('action-dialog-confirm',()=>{const name=fields.querySelector('[name="name"]').value.trim();if(!name){modal.querySelector('.action-dialog-feedback').textContent='请填写指令包名称';return;}const next={...data,name,scene:editing?data.scene:scene.value,workspace:editing?data.workspace:workspace.value};dialog.close();onConfirm(next);});
  dialog.addEventListener('close',()=>modal.remove(),{once:true});modal.show();
 }
 window.openCommandPackage=(source,onSave,initial)=>{
  if(!source&&!initial){packageInfo({name:"",scene:"家庭",workspace:"书房"},false,data=>window.openCommandPackage(null,onSave,data));return;}
  const main=document.querySelector('.process-page__main'),previous=[...main.children].map(el=>[el,el.hidden]);previous.forEach(([el])=>el.hidden=true);
  const draft=source?{...source}:{...initial,status:'待发布',count:0,props:'—'};
  if(!draft.commands){const candidates=catalog.filter(r=>r.workspace===draft.workspace);draft.commands=candidates.slice(0,draft.count).map((r,i)=>({...r,enabled:i!==0||draft.count===1}));}
  else draft.commands=draft.commands.map(r=>({...r}));
  let isNew=!source,tab='imported',page=1,size=10,filters={},reorder=false;const selected=new Set();
  const host=document.createElement('section');host.className='package-detail';main.append(host);
  const input=(name,label,value='',required=false)=>`<form-input name="${name}" label="${label}" value="${esc(value)}" placeholder="请输入${label}" ${required?'required':''}></form-input>`;
  const select=(name,label,values,value='')=>`<form-select name="${name}" label="${label}" value="${esc(value)}">${values.map(v=>`<option value="${esc(v)}">${v||'全部'+label}</option>`).join('')}</form-select>`;
  host.innerHTML=`<task-page-header title="${isNew?'新建指令包':'指令包详情'}" back ${isNew?'action="创建指令包"':''}></task-page-header><task-status-tabs variant="command-package"></task-status-tabs><task-filter-bar><form>${input('id','指令 ID')}${input('name','指令名称')}${input('iteration','指令迭代')}${input('version','指令版本号')}${select('difficulty','难度',['',1,2,3,4,5])}${input('props','道具')}</form></task-filter-bar><div class="package-toolbar"><h2 data-table-title>已导入指令</h2><span data-selection></span><div><text-button variant="outline" data-reorder>调整顺序</text-button><text-button variant="outline" data-clear>清除全部</text-button><text-button variant="primary" data-import disabled>确认导入</text-button></div></div><div class="task-data-table command-table"><div class="task-data-table__scroll"><table aria-label="指令包指令列表"><colgroup></colgroup><thead></thead><tbody></tbody></table><p class="command-empty" hidden>暂无指令</p></div><list-pagination page-size="10" total="0"></list-pagination></div><p class="package-message" role="status"></p>`;
  const q=s=>host.querySelector(s),message=text=>q('.package-message').textContent=text;
  function commit(){draft.count=draft.commands.length;draft.props=[...new Set(draft.commands.flatMap(r=>r.props.split('、')))].join('、')||'—';if(!isNew)onSave(draft);}
  function syncInfo(){q('task-page-header h1').textContent=(isNew?'新建指令包':'指令包详情')+' - '+draft.name;}
  const edit=document.createElement('button');edit.type='button';edit.className='package-title-edit';edit.setAttribute('aria-label','编辑指令包信息');edit.title='编辑指令包信息';edit.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="m15 5 4 4M4 20l4-1L20 7a2.8 2.8 0 0 0-4-4L4 15v5Z"/></svg>';
  q('task-page-header h1').after(edit);edit.onclick=()=>packageInfo(draft,true,data=>{draft.name=data.name;syncInfo();commit();message('基础信息已保存');});
  function scope(){return draft;}
  function available(){const s=scope();return catalog.filter(r=>r.scene===s.scene&&r.workspace===s.workspace&&!draft.commands.some(c=>c.key===r.key));}
  function matched(){return(tab==='imported'?draft.commands:available()).filter(r=>Object.entries(filters).every(([k,v])=>!v||String(r[k]).toLowerCase().includes(v.toLowerCase())));}
  function render(){const imported=tab==='imported',data=matched();page=Math.min(page,Math.max(1,Math.ceil(data.length/size)));const visible=data.slice((page-1)*size,page*size);
   q('[data-table-title]').textContent=imported?'已导入指令':'可导入指令';q('[data-reorder]').hidden=!imported;q('[data-reorder] button').textContent=reorder?'完成排序':'调整顺序';q('[data-clear]').hidden=imported;q('[data-import]').hidden=imported;q('[data-import]').toggleAttribute('disabled',!selected.size);q('[data-selection]').textContent=imported?`共 ${draft.commands.length} 条`:`已选择 ${selected.size} 条`;
   const cols=[...(imported&&reorder?[['drag','',40]]:[]),...(!imported?[['select','',44]]:[]),['id','指令 ID',100],['name','指令名称',220],['iteration','指令迭代',100],['version','指令版本号',110],['description','指令描述',420],['difficulty','难度',70],['mirror','镜像',70],['props','道具',250],...(imported?[['status','状态',90],['action','操作',112]]:[])];
   q('colgroup').innerHTML=cols.map(c=>`<col style="width:${c[2]}px">`).join('');q('thead').innerHTML='<tr>'+cols.map(([k,l])=>`<th scope="col">${k==='select'?'<input type="checkbox" data-all aria-label="选择当前页全部指令">':l}</th>`).join('')+'</tr>';
   q('tbody').innerHTML=visible.map(r=>`<tr data-key="${r.key}">${cols.map(([k])=>{let value=esc(r[k]);if(k==='drag')value=`<button class="package-drag-handle" type="button" aria-label="拖动调整 ${esc(r.name)} ${r.version} 的顺序" title="拖动调整顺序"><svg viewBox="0 0 16 20" aria-hidden="true"><g fill="currentColor"><circle cx="5" cy="4" r="1.5"/><circle cx="11" cy="4" r="1.5"/><circle cx="5" cy="10" r="1.5"/><circle cx="11" cy="10" r="1.5"/><circle cx="5" cy="16" r="1.5"/><circle cx="11" cy="16" r="1.5"/></g></svg></button>`;if(k==='select')value=`<input type="checkbox" data-select aria-label="选择 ${esc(r.name)} ${r.version}" ${selected.has(r.key)?'checked':''}>`;if(k==='status')value=`<span class="table-outline-tag table-outline-tag--${r.enabled?'active':'neutral'}">${r.enabled?'上线':'下线'}</span>`;if(k==='action')value=`<button data-toggle>${r.enabled?'下线':'上线'}</button><button data-remove>移除</button>`;return `<td>${k==='description'?`<span class="package-description" title="${esc(r.description)}">${value}</span>`:value}</td>`;}).join('')}</tr>`).join('');q('.command-empty').hidden=!!data.length;q('.command-empty').textContent=imported?'暂无已导入指令，请切换至“可导入指令”添加。':'当前场景和工作区暂无可导入指令。';const pager=q('list-pagination');pager.setAttribute('total',data.length);pager.setAttribute('page',page);
   const all=q('[data-all]');if(all){all.checked=!!visible.length&&visible.every(r=>selected.has(r.key));all.indeterminate=visible.some(r=>selected.has(r.key))&&!all.checked;all.onchange=()=>{visible.forEach(r=>all.checked?selected.add(r.key):selected.delete(r.key));render();};}
   const frame=q('.command-table');frame._scrollObserver?.disconnect();frame.querySelector('.task-data-table__middle-scroll')?.remove();delete frame.dataset.fixedEdgesReady;customElements.get('task-data-table').enhanceFixedEdges(frame,imported?(reorder?2:1):2,imported?2:0);
  }
  let drag=null;
  const clearDrag=()=>{q('tbody').querySelectorAll('.package-drop-target,.package-dragging').forEach(r=>r.classList.remove('package-drop-target','package-dragging'));drag=null;};
  q('tbody').onpointerdown=e=>{
   const handle=e.target.closest('.package-drag-handle');
   if(!reorder||!handle||e.button!==0)return;
   e.preventDefault();
   const row=handle.closest('tr');
   drag={key:row.dataset.key,target:row.dataset.key,pointerId:e.pointerId,startY:e.clientY};
   q('tbody').setPointerCapture(e.pointerId);
   row.classList.add('package-dragging');
  };
  q('tbody').onpointermove=e=>{
   if(!drag||drag.pointerId!==e.pointerId)return;
   e.preventDefault();
   const viewport=q('.task-data-table__scroll'),bounds=viewport.getBoundingClientRect();
   if(e.clientY<bounds.top+36)viewport.scrollTop-=12;
   else if(e.clientY>bounds.bottom-36)viewport.scrollTop+=12;
   const rows=[...q('tbody').rows];
   const row=rows.find(r=>{const b=r.getBoundingClientRect();return e.clientY>=b.top&&e.clientY<=b.bottom;});
   if(!row)return;
   drag.target=row.dataset.key;
   rows.forEach(r=>r.classList.toggle('package-drop-target',r===row&&r.dataset.key!==drag.key));
  };
  q('tbody').onpointerup=e=>{
   if(!drag||drag.pointerId!==e.pointerId)return;
   const from=draft.commands.findIndex(r=>r.key===drag.key),to=draft.commands.findIndex(r=>r.key===drag.target);
   const moved=Math.abs(e.clientY-drag.startY)>3&&from>=0&&to>=0&&from!==to;
   if(q('tbody').hasPointerCapture(e.pointerId))q('tbody').releasePointerCapture(e.pointerId);
   clearDrag();
   if(moved){const [item]=draft.commands.splice(from,1);draft.commands.splice(to,0,item);commit();render();message('指令顺序已更新');}
  };
  q('tbody').onpointercancel=clearDrag;
  q('tbody').onlostpointercapture=clearDrag;
  q('tbody').onchange=e=>{if(!e.target.matches('[data-select]'))return;const key=e.target.closest('tr').dataset.key;e.target.checked?selected.add(key):selected.delete(key);render();};
  q('tbody').onclick=e=>{
   const b=e.target.closest('button');if(!b||b.classList.contains('package-drag-handle'))return;
   const key=b.closest('tr').dataset.key,i=draft.commands.findIndex(r=>r.key===key);if(i<0)return;
   if(b.hasAttribute('data-toggle')){
    const row=draft.commands[i],nextEnabled=!row.enabled,label=nextEnabled?'上线':'下线';
    const modal=document.createElement('process-action-dialog');modal.setAttribute('variant','collection-confirm');document.body.append(modal);
    const frame=modal.querySelector('dialog');frame.classList.add('command-dialog','collection-confirm-dialog');frame.setAttribute('aria-label',label+'指令');
    modal.querySelector('h2').textContent=label+'指令';
    const prompt=document.createElement('p');prompt.textContent=`确定${label}指令“${row.name} ${row.version}”？`;modal.querySelector('.flow-info-fields').replaceChildren(prompt);
    modal.querySelector('footer [data-dismiss] button').textContent='取消';modal.querySelector('[data-confirm] button').textContent='确认'+label;
    let confirmed=false;
    modal.addEventListener('action-dialog-confirm',()=>{if(confirmed)return;confirmed=true;row.enabled=nextEnabled;commit();render();frame.close();});
    frame.addEventListener('close',()=>modal.remove(),{once:true});modal.show();return;
   }
   if(b.hasAttribute('data-remove')){draft.commands.splice(i,1);commit();render();}
  };
  q('[data-reorder]').onclick=()=>{reorder=!reorder;if(reorder){filters={};q('task-filter-bar form').querySelectorAll('form-input,form-select').forEach(c=>c.value='');page=1;}render();};q('[data-clear]').onclick=()=>{selected.clear();render();};q('[data-import]').onclick=()=>{const add=available().filter(r=>selected.has(r.key));draft.commands.push(...add.map(r=>({...r,enabled:true})));selected.clear();commit();message(`已导入 ${add.length} 条指令`);tab='imported';page=1;q('task-status-tabs').setActive(tab,false);render();};
  q('task-status-tabs').addEventListener('tab-change',e=>{tab=e.detail.value;page=1;reorder=false;render();});const filterForm=q('task-filter-bar form');filterForm.onsubmit=e=>e.preventDefault();filterForm.addEventListener('value-change',()=>{filters=Object.fromEntries(new FormData(filterForm));page=1;render();});q('task-filter-bar').addEventListener('filter-refresh',()=>{filters=Object.fromEntries(new FormData(filterForm));page=1;render();});q('list-pagination').addEventListener('page-change',e=>{page=e.detail.page;size=e.detail.pageSize;render();});
  function close(){q('.command-table')._scrollObserver?.disconnect();q('.command-table')._middleScrollEvents?.abort();host.remove();previous.forEach(([el,hidden])=>el.hidden=hidden);}
  q('task-page-header').addEventListener('header-back',close);q('task-page-header').addEventListener('header-action',e=>{e.stopPropagation();if(!isNew)return;draft.id='PK'+Date.now();commit();onSave(draft);close();});
  syncInfo();render();
 };
})();
