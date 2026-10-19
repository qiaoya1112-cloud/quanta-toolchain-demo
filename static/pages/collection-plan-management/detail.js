(() => {
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const tag=s=>`<span class="table-outline-tag table-outline-tag--${s==='上线'?'active':s==='待发布'?'warning':'neutral'}">${esc(s)}</span>`;
 const input=(name,label,value='')=>`<form-input name="${name}" label="${label}" value="${esc(value)}" placeholder="请输入${label}"></form-input>`;
 const select=(name,label,values,value)=>`<form-select name="${name}" label="${label}" value="${esc(value)}">${values.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('')}</form-select>`;
 const vendors=[['1','采集工厂'],['25','金华途祥网络科技有限公司'],['15','宁波博登智能科技有限公司'],['4','北京集纳盛广网络科技有限公司'],['2','生产工厂'],['3','产研'],['5','北京百度网讯科技有限公司'],['6','北京禹擎科技有限公司'],['7','苏州珀瑞缇信息科技有限公司'],['8','北京万同人力资源有限公司'],['9','京东科技信息技术有限公司'],['13','北京安才汇人力资源有限公司'],['14','安徽飞数信息科技有限公司'],['16','北京海天瑞声科技股份有限公司']].map(([id,name])=>({id,name}));
 window.openCollectionPlan=(source,onSave,packages)=>{
  const main=document.querySelector('.process-page__main'),previous=[...main.children].map(el=>[el,el.hidden]);previous.forEach(([el])=>el.hidden=true);
  const draft=source?JSON.parse(JSON.stringify(source)):{name:'',type:'指令包采集',scene:'家庭',status:'待发布',packages:[],strategies:[],vendors:[]};
  draft.packages??=packages.filter(p=>p.scene===draft.scene&&p.count>0).filter((p,i)=>i===0||p.id==='2609090001').map(p=>({...p}));
  draft.strategies??=[{version:'V1',status:'上线',skip:'无限制',period:'每人每天',single:10,same:1,creator:'Lila Lu',created:'2026-09-29 09:37:58',publisher:'Lila Lu',published:'2026-09-29 09:39:14'}];
  draft.vendors??=vendors.slice(0,4);
  let basicSaved=!!source,section='basic',tab='imported',editing=!source,page=1,size=10,filters={},selection=new Set();
  const host=document.createElement('section');host.className='plan-detail task-page-frame';main.append(host);
  host.innerHTML=`<task-page-header title="${source?'采集方案详情':'新建采集方案'}" back></task-page-header><div class="plan-layout"><nav class="plan-nav" aria-label="方案配置">${[['basic','基础信息'],['packages','指令包配置'],['strategies','策略配置'],['vendors','供应商配置']].map(([key,label])=>`<button data-section="${key}">${label}</button>`).join('')}</nav><div class="plan-panel"></div></div><footer class="plan-footer task-page-footer"><span role="status"></span><text-button variant="outline" data-back>返回</text-button>${!source?'<text-button variant="primary" data-create>创建方案</text-button>':''}</footer>`;
  const q=s=>host.querySelector(s),panel=q('.plan-panel'),notify=t=>q('[role=status]').textContent=t;
  const header=q('task-page-header .task-page-header');header.insertAdjacentHTML('beforeend',tag(draft.status));
  function commit(){if(source)onSave({...draft});}
  function close(){host.remove();previous.forEach(([el,hidden])=>el.hidden=hidden);}
  q('[data-back]').onclick=close;q('task-page-header').addEventListener('header-back',close);
  function saveBasic(){
   const form=panel.querySelector('form');if(!form)return !!draft.name;
   const values=Object.fromEntries(new FormData(form));
   if(!values.name?.trim()){notify('请填写采集方案名称');return false;}
   if(draft.packages.some(p=>p.scene!==values.scene)){notify('场景与已导入指令包不一致，请先移除不匹配的指令包');return false;}
   Object.assign(draft,values,{name:values.name.trim()});editing=false;basicSaved=true;commit();notify('基础信息已保存');return true;
  }
  q('[data-create]')?.addEventListener('click',()=>{
   if(section==='basic'&&editing&&!saveBasic())return;
   if(!draft.name){notify('请先填写并保存基础信息');return;}
   draft.id='CP'+Date.now();draft.creator='当前用户';draft.created=new Date().toLocaleString('sv-SE');onSave(draft);close();
  });
  function draw(){
   q('.plan-nav').querySelectorAll('button').forEach(b=>{b.disabled=b.dataset.section!=='basic'&&!source&&!basicSaved;b.setAttribute('aria-disabled',String(b.disabled));b.classList.toggle('is-active',b.dataset.section===section);b.setAttribute('aria-current',b.dataset.section===section?'page':'false');});
   if(section==='basic'){
    panel.innerHTML=`<h2>基础信息</h2><p class="plan-hint">完成后可继续配置指令包、策略和供应商</p><form class="plan-basic">${input('name','采集方案名称',draft.name)}${select('type','采集方案类型',['指令包采集'],draft.type)}${select('scene','场景',['家庭','办公'],draft.scene)}<div class="plan-basic-actions"><text-button variant="primary" data-save>${editing?'保存':'修改方案'}</text-button>${editing&&source?'<text-button variant="outline" data-cancel>取消</text-button>':''}</div></form>`;
    panel.querySelectorAll('input,select,.form-select__trigger').forEach(e=>e.disabled=!editing);
    panel.querySelector('form').onsubmit=e=>{e.preventDefault();if(editing&&saveBasic())draw();};
    panel.querySelector('[data-save]').onclick=()=>{if(!editing){editing=true;draw();}else if(saveBasic())draw();};
    panel.querySelector('[data-cancel]')?.addEventListener('click',()=>{editing=false;draw();});
    return;
   }
   const pk=section==='packages',st=section==='strategies';
   panel.innerHTML=`${pk?`<task-status-tabs variant="plan-packages" active="${tab}"></task-status-tabs>`:''}<div class="plan-toolbar"><h2>${pk?'指令包配置':st?'策略配置':'供应商配置'}</h2><span data-count></span><div>${pk?(tab==='available'?'<text-button variant="outline" data-clear>清除全部</text-button><text-button variant="primary" data-import disabled>确认导入</text-button>':''):st?'<text-button variant="primary" data-strategy>新建采集策略</text-button>':'<text-button variant="primary" data-vendors>导入供应商</text-button>'}</div></div>${!st?`<form class="plan-filters">${pk?select('workspace','工作区',['全部工作区','书房','厨房','客厅','办公区'],filters.workspace||'全部工作区')+input('id','指令包 ID',filters.id)+input('name','指令包名称',filters.name)+select('status','状态',['全部状态','待发布','上线','下线'],filters.status||'全部状态'):input('name','供应商名称',filters.name)}<text-button variant="outline" icon="reset" icon-only aria-label="重置筛选" data-reset></text-button></form>`:''}<div class="task-data-table command-table plan-table"><div class="task-data-table__scroll"><table><thead></thead><tbody></tbody></table><p class="command-empty" hidden>暂无数据</p></div><list-pagination page-size="${size}"></list-pagination></div>`;
   panel.querySelector('task-status-tabs')?.addEventListener('tab-change',e=>{tab=e.detail.value;page=1;filters={};selection.clear();draw();});
   const form=panel.querySelector('form');
   if(form){form.onsubmit=e=>e.preventDefault();form.addEventListener('value-change',()=>{filters=Object.fromEntries(new FormData(form));page=1;drawRows();});panel.querySelector('[data-reset]').onclick=()=>{filters={};page=1;draw();};}
   panel.querySelector('[data-clear]')?.addEventListener('click',()=>{selection.clear();drawRows();});
   panel.querySelector('[data-import]')?.addEventListener('click',()=>{draft.packages.push(...packages.filter(p=>selection.has(p.id)&&!draft.packages.some(r=>r.id===p.id)).map(p=>({...p})));selection.clear();tab='imported';page=1;commit();draw();notify('指令包已导入');});
   panel.querySelector('[data-strategy]')?.addEventListener('click',openStrategy);
   panel.querySelector('[data-vendors]')?.addEventListener('click',openVendors);
   panel.querySelector('list-pagination').addEventListener('page-change',e=>{page=e.detail.page;size=e.detail.pageSize;drawRows();});
   drawRows();
  }
  function drawRows(){
   const pk=section==='packages',st=section==='strategies',available=pk&&tab==='available';
   let rows=pk?(available?packages.filter(p=>p.scene===draft.scene&&!draft.packages.some(r=>r.id===p.id)):draft.packages):st?draft.strategies:draft.vendors;
   rows=rows.filter(r=>Object.entries(filters).every(([k,v])=>!v||v.startsWith('全部')||String(r[k]??'').includes(v)));
   page=Math.min(page,Math.max(1,Math.ceil(rows.length/size)));const visible=rows.slice((page-1)*size,page*size);
   const headers=pk?[...(available?['']:[]),'指令包 ID','指令包名称','工作区','道具','指令总数','状态','可下发数',...(!available?['操作']:[])]:st?['版本号','状态','策略配置','创建人及创建时间','发布人及发布时间','操作']:['供应商 ID','供应商名称','操作'];
   const table=panel.querySelector('.plan-table table');
   table.classList.toggle('plan-package-table',pk);table.querySelector('colgroup')?.remove();
   if(pk){const widths=[...(available?[44]:[]),140,180,90,360,100,90,100,...(!available?[120]:[])];const group=document.createElement('colgroup');group.innerHTML=widths.map(width=>`<col style="width:${width}px">`).join('');table.prepend(group);table.style.minWidth=widths.reduce((sum,width)=>sum+width,0)+'px';}else table.style.minWidth='';
   panel.querySelector('thead').innerHTML='<tr>'+headers.map((h,i)=>`<th>${available&&i===0?'<input type="checkbox" data-all aria-label="全选当前页">':h}</th>`).join('')+'</tr>';
   panel.querySelector('tbody').innerHTML=visible.map(r=>{
    const cells=pk?[...(available?[`<input type="checkbox" data-check="${r.id}" aria-label="选择 ${esc(r.name)}" ${selection.has(r.id)?'checked':''}>`]:[]),esc(r.id),esc(r.name),esc(r.workspace),`<span class="plan-props-summary" title="${esc(r.props)}">${esc(r.props)}</span>`,r.count,tag(r.status),r.status==='上线'?r.count:0,...(!available?[`<button data-detail="${r.id}">详情</button><button data-remove="${r.id}">移除</button>`]:[])]:st?[r.version,tag(r.status),`跳过 ${esc(r.skip)} / ${esc(r.period)} · 单条采集 ${r.single} · 单任务相同指令 ${r.same}`,`${esc(r.creator)}<small>${r.created}</small>`,`${esc(r.publisher||'—')}<small>${r.published||'—'}</small>`,`<button data-toggle="${r.version}">${r.status==='上线'?'下线':'上线'}</button>`]:[r.id,esc(r.name),`<button data-remove="${r.id}">删除</button>`];
    return '<tr>'+cells.map(c=>'<td>'+c+'</td>').join('')+'</tr>';
   }).join('');
   panel.querySelector('.command-empty').hidden=!!rows.length;
   const pager=panel.querySelector('list-pagination');pager.setAttribute('total',rows.length);pager.setAttribute('page',page);
   const all=panel.querySelector('[data-all]');if(all){all.checked=visible.length>0&&visible.every(r=>selection.has(r.id));all.indeterminate=!all.checked&&visible.some(r=>selection.has(r.id));all.onchange=()=>{visible.forEach(r=>all.checked?selection.add(r.id):selection.delete(r.id));drawRows();};}
   panel.querySelectorAll('[data-check]').forEach(c=>c.onchange=()=>{c.checked?selection.add(c.dataset.check):selection.delete(c.dataset.check);drawRows();});
   panel.querySelector('[data-import]')?.toggleAttribute('disabled',selection.size===0);
   panel.querySelector('[data-count]').textContent=available?'已选择 '+selection.size+' 个':'共 '+rows.length+' 条';
   panel.querySelectorAll('[data-remove]').forEach(b=>b.onclick=()=>{const key=pk?'packages':'vendors';draft[key]=draft[key].filter(r=>r.id!==b.dataset.remove);commit();drawRows();});
   panel.querySelectorAll('[data-toggle]').forEach(b=>b.onclick=()=>{const r=draft.strategies.find(r=>r.version===b.dataset.toggle);if(r.status!=='上线'){draft.strategies.forEach(s=>s.status='下线');r.publisher='当前用户';r.published=new Date().toLocaleString('sv-SE');r.status='上线';}else r.status='下线';commit();drawRows();});
   panel.querySelectorAll('[data-detail]').forEach(b=>b.onclick=()=>{const r=draft.packages.find(p=>p.id===b.dataset.detail);drawer('指令包详情',`<dl class="command-details">${[['指令包 ID',r.id],['指令包名称',r.name],['工作区',r.workspace],['道具',r.props],['指令总数',r.count],['状态',r.status]].map(([k,v])=>`<div><dt>${k}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>`);});
  }
  function drawer(title,html,footer=''){
   const el=document.createElement('app-drawer');el.className='plan-drawer';el.setAttribute('heading',title);el.innerHTML=html+footer;document.body.append(el);el.addEventListener('drawer-close',()=>el.remove());el.show();return el;
  }
  function openStrategy(){
   const el=drawer('新建采集策略',`<form class="plan-strategy-form">${select('skip','跳过限制',['无限制','不允许跳过'],'无限制')}${select('period','采集周期',['每人每天','每人每任务'],'每人每天')}${input('single','单条采集次数',10)}${input('same','单任务相同指令次数',1)}<p role="alert"></p></form>`,'<text-button drawer-footer variant="outline" data-cancel>取消</text-button><text-button drawer-footer variant="primary" data-save>保存</text-button>');
   el.querySelector('[data-cancel]').onclick=()=>el.close();
   el.querySelector('[data-save]').onclick=()=>{const data=Object.fromEntries(new FormData(el.querySelector('form')));if(!['single','same'].every(k=>Number.isInteger(Number(data[k]))&&Number(data[k])>0)){el.querySelector('[role=alert]').textContent='采集次数请填写正整数';return;}draft.strategies.unshift({...data,version:'V'+(Math.max(0,...draft.strategies.map(s=>Number(s.version.slice(1))))+1),status:'待发布',creator:'当前用户',created:new Date().toLocaleString('sv-SE')});commit();el.close();draw();};
   el.querySelector('form').onsubmit=e=>{e.preventDefault();el.querySelector('[data-save]').click();};
  }
  function openVendors(){
   const chosen=new Set();let term='',vp=1,vs=10;
   const el=drawer('导入供应商',`<form class="plan-filters">${input('name','供应商名称')}</form><div class="task-data-table command-table"><div class="task-data-table__scroll"><table><thead><tr><th><input type="checkbox" data-all aria-label="全选当前页"></th><th>供应商 ID</th><th>供应商名称</th></tr></thead><tbody></tbody></table><p class="command-empty" hidden>暂无可导入供应商</p></div><list-pagination page-size="10"></list-pagination></div>`,'<text-button drawer-footer variant="outline" data-cancel>取消</text-button><text-button drawer-footer variant="primary" data-import disabled>导入</text-button>');
   function render(){
    const rows=vendors.filter(v=>!draft.vendors.some(r=>r.id===v.id)&&v.name.includes(term)),visible=rows.slice((vp-1)*vs,vp*vs);
    el.querySelector('tbody').innerHTML=visible.map(r=>`<tr><td><input type="checkbox" data-id="${r.id}" aria-label="选择 ${esc(r.name)}" ${chosen.has(r.id)?'checked':''}></td><td>${r.id}</td><td>${esc(r.name)}</td></tr>`).join('');
    el.querySelector('.command-empty').hidden=!!rows.length;const pager=el.querySelector('list-pagination');pager.setAttribute('total',rows.length);pager.setAttribute('page',vp);
    el.querySelectorAll('[data-id]').forEach(c=>c.onchange=()=>{c.checked?chosen.add(c.dataset.id):chosen.delete(c.dataset.id);render();});
    const all=el.querySelector('[data-all]');all.checked=!!visible.length&&visible.every(r=>chosen.has(r.id));all.indeterminate=!all.checked&&visible.some(r=>chosen.has(r.id));all.onchange=()=>{visible.forEach(r=>all.checked?chosen.add(r.id):chosen.delete(r.id));render();};el.querySelector('[data-import]').toggleAttribute('disabled',!chosen.size);
   }
   el.querySelector('form').onsubmit=e=>e.preventDefault();el.querySelector('form').addEventListener('value-change',()=>{term=el.querySelector('form-input').value;vp=1;render();});
   el.querySelector('list-pagination').addEventListener('page-change',e=>{vp=e.detail.page;vs=e.detail.pageSize;render();});
   el.querySelector('[data-cancel]').onclick=()=>el.close();el.querySelector('[data-import]').onclick=()=>{draft.vendors.push(...vendors.filter(v=>chosen.has(v.id)));commit();el.close();draw();notify('供应商已导入');};render();
  }
  q('.plan-nav').onclick=e=>{const b=e.target.closest('[data-section]');if(!b||b.disabled||(b.dataset.section!=='basic'&&!source&&!basicSaved))return;if(section==='basic'&&editing&&!saveBasic())return;section=b.dataset.section;page=1;filters={};selection.clear();draw();};draw();
 };
})();
