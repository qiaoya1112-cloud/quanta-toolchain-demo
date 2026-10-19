(() => {
  const rows = [
    ['100008','靠垫归位','目标态','家庭','客厅',1,1],
    ['100021','玻璃杯入柜','目标态','家庭','厨房',2,1],
    ['100031','抹布归位','目标态','家庭','厨房',1,0],
    ['100036','餐盘入架','目标态','家庭','厨房',1,1],
    ['100044','遥控器收纳','目标态','家庭','客厅',1,1],
    ['100047','书本上架','目标态','家庭','书房',1,1],
    ['100060','办公文具整理','目标态','办公','办公区',1,1]
  ].map(([id,name,iteration,scene,workspace,versions,enabled]) => ({id,name,iteration,scene,workspace,versions,enabled}));
  const form = document.querySelector('form');
  const tbody = document.querySelector('tbody');
  const pagination = document.querySelector('list-pagination');
  const dialog = document.querySelector('dialog');
  const drawer = document.querySelector('app-drawer');
  let activeRow;
  const feedback = document.querySelector('[data-feedback]');
  let filters = {}, page = 1, pageSize = 10;
  const status = row => row.enabled ? '启用' : '停用';
  const tag = row => `<span class="table-outline-tag table-outline-tag--${row.enabled ? 'active' : 'neutral'}">${status(row)}</span>`;
  function render() {
    const matched = rows.filter(row => Object.entries(filters).every(([key,value]) => !value || (['id','name','iteration'].includes(key) ? row[key].toLowerCase().includes(value.toLowerCase()) : (key === 'status' ? status(row) : row[key]) === value)));
    page = Math.min(page,Math.max(1,Math.ceil(matched.length/pageSize)));
    tbody.innerHTML = matched.slice((page-1)*pageSize,page*pageSize).map(row => `<tr data-id="${row.id}"><td>${row.id}</td><td><button type="button" class="command-name-link" data-action="details" aria-label="查看${row.name}详情">${row.name}</button></td><td>${row.iteration}</td><td>${row.scene}</td><td>${row.workspace}</td><td>${row.versions}</td><td>${row.enabled}</td><td>${tag(row)}</td><td><button type="button" data-action="details" aria-label="查看${row.name}详情">详情</button><button type="button" data-action="toggle" aria-label="${row.enabled?'停用':'启用'}${row.name}">${row.enabled?'停用':'启用'}</button></td></tr>`).join('');
    document.querySelector('[data-empty]').hidden = matched.length > 0;
    pagination.setAttribute('total',matched.length);
    pagination.setAttribute('page',page);
  }
  function query() {
    filters = Object.fromEntries([...new FormData(form)].map(([key,value]) => [key,value.trim()]));
    page = 1; feedback.textContent = ''; render();
  }
  form.addEventListener('submit',event => {event.preventDefault();query();});
  form.addEventListener('value-change',query);
  pagination.addEventListener('page-change',event => {page=event.detail.page;pageSize=event.detail.pageSize;render();});
  function showDialog(title,content) {
    document.querySelector('#dialog-title').textContent=title;
    document.querySelector('[data-dialog-content]').innerHTML=content;
    dialog.showModal();
  }
  const descriptions = {
    '100008':['1 个靠垫平放在沙发座面，右侧扶手旁无其他物品。','靠垫竖直靠稳在沙发右侧扶手旁，座面其余区域无散落靠垫。','靠垫、沙发'],
    '100021':['玻璃杯放置在厨房台面，柜门已打开。','玻璃杯稳定放入柜内指定位置。','玻璃杯、橱柜、托盘'],
    '100031':['抹布放置在厨房台面。','抹布整齐放回指定收纳位置。','抹布、收纳架'],
    '100036':['餐盘放在台面，餐具架有空位。','餐盘稳定放入餐具架。','餐盘、餐具架'],
    '100044':['遥控器散放在客厅桌面。','遥控器放入指定收纳盒。','遥控器、收纳盒'],
    '100047':['书本平放在书桌上。','书本竖直放入书架指定区域。','书本、书架'],
    '100060':['办公文具散放在桌面。','文具分类放入收纳盒。','文具、收纳盒、办公桌']
  };
  function renderDetails(){
    const row=activeRow, [initial,target,props]=descriptions[row.id];
    row.versionStates ||= Array.from({length:row.versions},(_,i)=>i<row.enabled);
    const cards=Array.from({length:row.versions},(_,i)=>i).map(i=>{
      const enabled=row.versionStates[i], version=row.versions-i;
      const current=row.id==='100008'?0:i===0?18.5:8, total=row.id==='100008'?16:40;
      return `<article class="instruction-reference" aria-label="版本 V${version}">
        <header><span class="instruction-reference__status ${enabled?'is-enabled':''}">${enabled?'启用':'停用'}</span><strong>V${version}</strong><button type="button" data-version="${i}">${enabled?'停用':'启用'}</button></header>
        <dl><div class="instruction-reference__description"><dt>指令描述</dt><dd>【初始状态】${initial}【结束状态】${target}【时长上限】1分钟</dd></div>
        <div class="instruction-reference__metrics"><div><dt>镜像</dt><dd>1</dd></div><div><dt>难度</dt><dd>2</dd></div></div>
        <div><dt>道具</dt><dd>${props}</dd></div>
        <div><dt>采集进度</dt><dd class="instruction-reference__progress"><div class="instruction-reference__progress-summary"><strong>${current.toFixed(1)} / ${total.toFixed(1)} h</strong><span>${Math.round(current/total*100)}%</span></div><progress max="${total}" value="${current}" aria-label="V${version}采集进度"></progress><small>距目标 ${(total-current).toFixed(1)} h</small></dd></div></dl>
      </article>`;
    }).join('');
    drawer.querySelector('[data-command-detail]').innerHTML=cards;
  }
  function confirmStatus(name,enabled,onConfirm){
    const label=enabled?'停用':'启用';
    const modal=document.createElement('process-action-dialog');
    modal.setAttribute('variant','collection-confirm');document.body.append(modal);
    const frame=modal.querySelector('dialog');frame.classList.add('command-dialog','command-status-confirm');
    frame.setAttribute('aria-label',label+'指令');modal.querySelector('h2').textContent=label+'指令';
    const text=document.createElement('p');text.textContent=`确定${label}指令“${name}”？`;
    modal.querySelector('.flow-info-fields').replaceChildren(text);
    modal.querySelector('footer [data-dismiss] button').textContent='取消';
    modal.querySelector('[data-confirm] button').textContent='确认'+label;
    let confirmed=false;
    modal.addEventListener('action-dialog-confirm',()=>{if(confirmed)return;confirmed=true;onConfirm();frame.close();});
    frame.addEventListener('close',()=>modal.remove(),{once:true});modal.show();
  }
  drawer.addEventListener('click',event=>{
    const button=event.target.closest('[data-version]');if(!button)return;
    const index=Number(button.dataset.version);
    const row=activeRow;
    confirmStatus(`${row.name} V${row.versions-index}`,row.versionStates[index],()=>{
      row.versionStates[index]=!row.versionStates[index];
      row.enabled=row.versionStates.filter(Boolean).length;
      renderDetails();render();
      feedback.textContent=`${row.name}状态已更新（当前页面演示）`;
    });
  });
  tbody.addEventListener('click',event => {
    const button=event.target.closest('[data-action]');if(!button)return;
    const row=rows.find(item => item.id===button.closest('tr').dataset.id);
    if(button.dataset.action==='toggle') {
      confirmStatus(row.name,row.enabled,()=>{
        row.enabled=row.enabled?0:1;row.versionStates=Array.from({length:row.versions},(_,i)=>i<row.enabled);render();
        feedback.textContent=`${row.name}已${status(row)}（当前页面演示）`;
      });
    } else {
      activeRow=row;renderDetails();drawer.show();
    }
  });
  dialog.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click',()=>dialog.close()));
  render();
})();
