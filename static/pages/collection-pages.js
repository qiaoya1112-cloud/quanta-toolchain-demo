(() => {
  const isPackage = document.body.dataset.pageId === 'command-package-management';
  const readOnly = document.body.dataset.pageId === 'collection-plans';
  const kitchen = '玻璃杯、橱柜、防滑垫、托盘、隔板、位置标签、餐盘、沥水架、餐具篮、操作台、定位贴';
  const study = '铅笔、笔筒、书桌、收纳盒、标签贴、托盘';
  const packages = [
    ['2609070001','厨房餐具归位','家庭','厨房',kitchen,'上线',2],
    ['2609070002','书房文具收纳','家庭','书房',study,'下线',1],
    ['2609070003','厨房清洁用品归位','家庭','厨房','—','待发布',0],
    ['2609070004','客厅日常收纳','家庭','客厅','遥控器、抽屉、收纳盒、茶几、定位贴、防滑垫','下线',1],
    ['2609070005','书房书本归位','家庭','书房','书本、书架、书挡、收纳篮、标签贴、防滑垫','上线',1],
    ['2609090001','家庭整理执行包','家庭','厨房',kitchen+'、铅笔、笔筒、书桌、收纳盒、标签贴、遥控器、抽屉、茶几、书本、书架、书挡、收纳篮、文件夹、档案袋、订书机、回形针盒、便签纸、剪刀、胶带座、充电线、插线板、桌面整理架、透明储物箱、带盖收纳桶、衣架、折叠毛巾、清洁海绵、洗碗刷、洗洁精、橡胶手套、垃圾分类桶、密封保鲜盒、量杯、调味罐、筷子筒、汤勺、锅盖架、砧板、隔热手套、杯垫、纸巾盒、桌面吸尘器、折叠置物架、分层文件盘、抽屉分隔板、备用标签纸、物品分类清单、收纳位置示意卡','上线',5],
    ['2609090002','厨房清洁已完成包','家庭','厨房','玻璃杯、橱柜、防滑垫、托盘、隔板、位置标签','上线',1],
    ['2608260001','厨房清洁用品归位','家庭','厨房','抹布、水槽、挂钩、收纳篮、清洁剂、定位贴','上线',1],
    ['2607150001','办公文具整理','办公','办公区','办公用纸、文件、档案袋、打印机、文件柜、分类标签','上线',1]
  ].map(([id,name,scene,workspace,props,status,count])=>({id,name,scene,workspace,props,status,count}));
  const plans = [
    ['CP260001','家庭通用数据采集','家庭','上线','演示方案管理员','2026-08-18 10:20:00'],
    ['CP260002','家庭长尾动作补采','家庭','待发布','演示方案管理员','2026-09-02 15:08:00'],
    ['CP260003','厨房清洁动作专项','家庭','暂停','演示运营专员','2026-08-26 13:40:18'],
    ['CP260004','办公桌面整理采集','办公','下线','演示方案管理员','2026-07-15 09:32:41']
  ].map(([id,name,scene,status,creator,created])=>({id,name,type:'指令包采集',scene,status,creator,created}));
  let rows = isPackage ? packages : plans.filter(row=>!readOnly || row.status!=='待发布');
  const fields = isPackage ? [['id','指令包 ID'],['name','指令包名称'],['scene','场景'],['workspace','工作区'],['props','道具'],['status','指令包状态'],['count','指令总数']] : [['id','采集方案 ID'],['name','采集方案名称'],['type','采集方案类型'],['scene','场景'],['status','状态'],...(!readOnly?[['creator','创建人'],['created','创建时间']]:[])];
  const form=document.querySelector('.command-filters'),tbody=document.querySelector('tbody'),pagination=document.querySelector('list-pagination'),dialog=document.querySelector('dialog'),content=document.querySelector('[data-dialog-content]'),feedback=document.querySelector('[data-feedback]');
  let filters={},page=1,pageSize=10;
  const escape=value=>String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const tag=status=>`<span class="table-outline-tag table-outline-tag--${({上线:'active',待发布:'warning',暂停:'paused',下线:'neutral'})[status]}">${status}</span>`;
  function render(){
    const matched=rows.filter(row=>Object.entries(filters).every(([key,value])=>!value || (['id','name'].includes(key)?row[key].toLowerCase().includes(value.toLowerCase()):row[key]===value)));
    page=Math.min(page,Math.max(1,Math.ceil(matched.length/pageSize)));
    tbody.innerHTML=matched.slice((page-1)*pageSize,page*pageSize).map(row=>{
      const link=key=>key==='id'?escape(row[key]):`<button type="button" class="collection-link" data-action="details">${escape(row[key])}</button>`;
      const cells=isPackage?[link('id'),link('name'),escape(row.scene),escape(row.workspace),`<span class="collection-props-summary" title="${escape(row.props)}">${escape(row.props)}</span>`,tag(row.status),row.count]:[link('id'),link('name'),row.type,escape(row.scene),tag(row.status),...(!readOnly?[`${escape(row.creator)}<span class="collection-created">${escape(row.created)}</span>`]:[])];
      const actions=[['details','详情'],...(!readOnly?(row.status==='待发布'?[['publish','发布'],['delete','删除']]:[[row.status==='下线'?'online':'offline',row.status==='下线'?'上线':'下线']]):[])];
      return `<tr data-id="${row.id}">${cells.map((cell,i)=>`<td${isPackage&&i===4?' class="collection-props"':''}>${cell}</td>`).join('')}<td>${actions.map(([action,label])=>`<button type="button" data-action="${action}"${isPackage&&action==='publish'&&!(row.count>0)?' disabled aria-disabled="true" title="请先导入指令"':''}>${label}</button>`).join('')}</td></tr>`;
    }).join('');
    document.querySelector('[data-empty]').hidden=matched.length>0;
    pagination.setAttribute('total',matched.length);pagination.setAttribute('page',page);
    if(isPackage){
      const frame=tbody.closest('.task-data-table');
      customElements.get('task-data-table').enhanceFixedEdges(frame,1,1);
      frame._updateFixedEdges?.();
    }
  }
  function openPublishedPlan(row){
    const main=document.querySelector('.process-page__main');
    const previous=[...main.children].map(el=>[el,el.hidden]);previous.forEach(([el])=>el.hidden=true);
    const ids=row.id==='CP260001'?['2609070001','2609070005','2609090001','2609090002']:row.scene==='办公'?['2607150001']:['2609070001','2608260001'];
    const items=(row.packages||packages.filter(p=>ids.includes(p.id))).map(p=>({...p}));
    if(!row.packages&&row.id==='CP260001')items.forEach(p=>{if(p.id==='2609090001')p.count=2;if(p.id==='2609090002'){p.status='暂停';p.count=0;}});
    const detail=document.createElement('section');detail.className='published-plan-detail';
    detail.innerHTML=`<task-page-header title="采集方案详情" back></task-page-header><div class="published-plan-body"><div class="task-data-table command-table"><div class="task-data-table__scroll"><table aria-label="采集方案指令包"><colgroup><col style="width:140px"><col style="width:180px"><col style="width:90px"><col style="width:90px"><col style="width:80px"><col></colgroup><thead><tr><th>指令包 ID</th><th>指令包名称</th><th>工作区</th><th>状态</th><th>指令数</th><th>道具</th></tr></thead><tbody>${items.map(p=>`<tr><td>${escape(p.id)}</td><td>${escape(p.name)}</td><td>${escape(p.workspace)}</td><td>${tag(p.status)}</td><td>${p.count}</td><td class="collection-props"><span class="collection-props-summary" title="${escape(p.props)}">${escape(p.props)}</span></td></tr>`).join('')}</tbody></table>${items.length?'':'<p class="command-empty">暂无指令包</p>'}</div></div></div>`;
    const body=detail.querySelector('.published-plan-body');
    const filter=document.createElement('task-filter-bar');
    filter.innerHTML='<form aria-label="指令包筛选"><form-input name="id" label="指令包 ID" placeholder="请输入指令包 ID"></form-input><form-input name="name" label="指令包名称" placeholder="请输入指令包名称"></form-input><form-select name="status" label="状态"><option value="">全部状态</option><option>上线</option><option>暂停</option><option>下线</option></form-select></form>';
    body.before(filter);
    main.append(detail);
    const filterForm=filter.querySelector('form'),tableRows=[...detail.querySelectorAll('tbody tr')];
    const empty=document.createElement('p');empty.className='command-empty';empty.textContent='暂无符合条件的指令包';empty.hidden=true;detail.querySelector('.task-data-table__scroll').append(empty);
    function applyDetailFilters(){const values=Object.fromEntries(new FormData(filterForm));let count=0;items.forEach((item,i)=>{const match=Object.entries(values).every(([key,value])=>!value||(key==='status'?item[key]===value:String(item[key]).toLowerCase().includes(value.trim().toLowerCase())));tableRows[i].hidden=!match;if(match)count++;});empty.hidden=count>0;}
    filterForm.addEventListener('value-change',applyDetailFilters);
    filterForm.addEventListener('submit',e=>{e.preventDefault();applyDetailFilters();});
    detail.addEventListener('header-back',()=>{detail.remove();previous.forEach(([el,hidden])=>el.hidden=hidden);});
  }
  function query(){filters=Object.fromEntries([...new FormData(form)].map(([key,value])=>[key,value.trim()]));page=1;feedback.textContent='';render();}
  form.addEventListener('value-change',query);form.addEventListener('submit',event=>{event.preventDefault();query();});
  pagination.addEventListener('page-change',event=>{page=event.detail.page;pageSize=event.detail.pageSize;render();});
  function show(title,html){document.querySelector('#dialog-title').textContent=title;content.innerHTML=html;dialog.showModal();}
  dialog.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>dialog.close()));
  tbody.addEventListener('click',event=>{
    const button=event.target.closest('[data-action]');if(!button||button.disabled)return;
    const row=rows.find(row=>row.id===button.closest('tr').dataset.id),action=button.dataset.action;
    if(action==='details'&&readOnly){openPublishedPlan(row);return;}
    if(action==='details'&&isPackage){window.openCommandPackage(row,data=>{Object.assign(row,data);render();});return;}
    if(action==='details'&&window.openCollectionPlan&&!readOnly){window.openCollectionPlan(row,data=>{Object.assign(row,data);render();},packages);return;}
    if(action==='details'){show(isPackage?'指令包详情':'采集方案详情',`<dl class="command-details">${fields.map(([key,label])=>`<div><dt>${label}</dt><dd>${key==='status'?tag(row.status):escape(row[key])}</dd></div>`).join('')}</dl>`);return;}
    if(readOnly||(isPackage&&action==='publish'&&!(row.count>0)))return;
    const label={publish:'发布',delete:'删除',online:'上线',offline:'下线'}[action];if(!label)return;
    const entity=isPackage?'指令包':'采集方案';
    const modal=document.createElement('process-action-dialog');modal.setAttribute('variant','collection-confirm');document.body.append(modal);
    const frame=modal.querySelector('dialog');frame.classList.add('command-dialog','collection-confirm-dialog');frame.setAttribute('aria-label',label+entity);
    modal.querySelector('h2').textContent=label+entity;
    const blocked=action==='publish'&&isPackage&&row.count===0;
    const note=blocked?'请先添加指令后再发布。':action==='delete'?'删除后无法恢复，请确认是否继续。':'';
    modal.querySelector('.flow-info-fields').innerHTML=`<p>确定${label}${entity}“${escape(row.name)}”？</p>${note?`<p class="collection-confirm-note">${note}</p>`:''}`;
    modal.querySelector('footer [data-dismiss] button').textContent='取消';
    const confirm=modal.querySelector('[data-confirm]');confirm.querySelector('button').textContent='确认'+label;if(action==='delete')confirm.setAttribute('variant','danger');if(blocked)confirm.setAttribute('disabled','');
    let submitted=false;
    modal.addEventListener('action-dialog-confirm',()=>{if(submitted||blocked)return;submitted=true;
     if(action==='delete'){rows=rows.filter(item=>item!==row);feedback.textContent='已删除（当前页面演示）';}
     else{row.status=action==='offline'?'下线':'上线';feedback.textContent=`${row.name}已${label}（当前页面演示）`;}
     frame.close();render();
    });frame.addEventListener('close',()=>modal.remove(),{once:true});modal.show();

  });
  document.addEventListener('header-action',()=>{
    if(readOnly)return;
    if(isPackage){window.openCommandPackage(null,data=>{rows.unshift(data);filters={};page=1;render();});return;}
    if(window.openCollectionPlan){window.openCollectionPlan(null,data=>{rows.unshift(data);filters={};page=1;render();},packages);return;}
    show(isPackage?'创建指令包':'新建采集方案',`<form class="collection-create-form"><label class="collection-wide">${isPackage?'指令包':'采集方案'}名称<form-input><input name="name" aria-label="名称" required maxlength="80" placeholder="请输入名称"></form-input></label><form-select name="scene" label="场景"><option>家庭</option><option>办公</option></form-select>${isPackage?'<form-select name="workspace" label="工作区"><option>厨房</option><option>书房</option><option>客厅</option><option>办公区</option></form-select>':'<form-select name="type" label="采集方案类型"><option>指令包采集</option></form-select>'}<p class="collection-wide">保存为待发布状态，仅用于当前页面演示。</p><button class="collection-wide" type="submit">保存</button></form>`);
    content.querySelector('form').addEventListener('submit',event=>{
      event.preventDefault();const data=Object.fromEntries(new FormData(event.target));if(!data.name.trim())return;
      rows.unshift({...data,name:data.name.trim(),id:(isPackage?'PK':'CP')+Date.now(),status:'待发布',props:'—',count:0,creator:'当前用户',created:new Date().toLocaleString('sv-SE')});
      form.querySelectorAll('form-input,form-select').forEach(control=>control.value='');filters={};page=1;dialog.close();render();feedback.textContent='已保存为待发布状态（当前页面演示）';
    });
  });
  render();
})();
