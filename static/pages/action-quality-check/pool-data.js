(() => {
 window.openPoolData=(parent,context={})=>{
  const rejected=['rejected','review','assigned'].includes(context.todoType);
  parent.hidden=true;
  const page=document.createElement('section');page.className='pool-setup pool-data task-page-frame';
  page.innerHTML='<task-page-header title="数据列表" back></task-page-header><task-filter-bar><form>'+[['task','任务 ID'],['id','数据 ID'],['device','设备序列号'],['collector','采集员']].map(([name,label])=>`<form-input name="${name}" label="${label}" placeholder="请输入${label}"></form-input>`).join('')+'</form></task-filter-bar><div class="pool-data-toolbar"><span role="status"></span><text-button variant="primary" data-claim disabled>批量领取</text-button></div><task-data-table variant="task-records"></task-data-table><list-pagination total-only total="0"></list-pagination>';
  parent.after(page);
  const component=page.querySelector('task-data-table'),table=component.querySelector('table');
  const totalFooter=page.querySelector(':scope > list-pagination');
  totalFooter.classList.add('task-data-table__pagination');
  component.querySelector('.task-data-table__frame').append(totalFooter);
  const rows=[...table.querySelectorAll('tbody tr')].slice(0,6);
  if(rejected){const originals=[...rows];while(rows.length<10)rows.push(originals[rows.length%originals.length].cloneNode(true));}
  table.querySelector('colgroup')?.remove();table.style.minWidth='1480px';table.style.tableLayout='fixed';
  const widths=rejected?[40,110,100,660,145,190,190,180,225,90]:[40,64,82,660,90,160,190,145,225,180];table.dataset.columnWidths=widths.join(',');const cg=document.createElement('colgroup');cg.innerHTML=widths.map(w=>`<col style="width:${w}px">`).join('');table.prepend(cg);table.style.width=widths.reduce((sum,width)=>sum+width,0)+'px';table.style.minWidth='100%';table.querySelectorAll('th').forEach(th=>th.style.width='');
  table.querySelector('thead').innerHTML='<tr>'+['<input type="checkbox" data-all aria-label="全选当前页">','任务 ID','数据 ID','视频区域（头部 / 左臂 / 右臂）','状态','设备序列号','质检结论','操作员','操作时间','操作'].map(x=>`<th>${x}</th>`).join('')+'</tr>';
  const records=rows.map((row,i)=>{const media=row.children[1].innerHTML;return {row,id:String(7523785+i),task:rejected?'20456':'20455',device:`UDAS-0030${9+i}-151${1+i}`,collector:['郭文静','李燕','王敏'][i%3],claimed:false,media};});
  table.querySelector('tbody').replaceChildren(...rows);
  records.forEach((r,i)=>{r.row.innerHTML=`<td><input type="checkbox" data-select aria-label="选择 ${r.id}"></td><td>${r.task}</td><td>${r.id}</td><td>${r.media}</td><td><span data-status class="table-outline-tag table-outline-tag--neutral"></span></td><td>${r.device}</td><td>自动化质检：${i?'合格':'操作失误'}<br>采集质检：<span data-quality>未质检</span></td><td>采集：${r.collector}<br>采集质检：--</td><td class="pool-operation-time"><div>采集：2026-09-30 ${String(9+i).padStart(2,'0')}:20:00</div><div>采集质检：<span data-quality-time>--</span></div></td><td><button data-process>处理</button><button data-result="合格" hidden>合格</button><button data-result="不合格" hidden>不合格</button></td>`;});
  if(rejected){
    table.querySelectorAll('th')[1].textContent='采集任务 ID';
    table.querySelectorAll('th')[4].textContent='质检结论';
    table.querySelectorAll('th')[6].textContent='操作结论';
    records.forEach((r,i)=>{
      const collector=['郭文静（01）','李燕（03）','刘立斌（01）'][i%3];
      r.collector=collector;
      r.row.children[6].innerHTML=`采集自检：合格<br>自动化质检：${i===0?'操作失误':'合格'}`;
      r.row.children[7].innerHTML=`采集：${collector}<br>采集自检：李奕冲（03）`;
      r.row.children[8].innerHTML=`<div>采集：2026-09-30 ${String(9+i).padStart(2,'0')}:20:00</div><div>采集自检：2026-10-01 ${String(9+i).padStart(2,'0')}:30:00</div>`;
    });
    table.querySelectorAll('tr').forEach(row=>row.firstElementChild.remove());
    widths.shift();
    cg.firstElementChild.remove();
    table.dataset.columnWidths=widths.join(',');
    table.style.width=widths.reduce((sum,width)=>sum+width,0)+'px';
    page.classList.add('pool-data--rejected');
    page.querySelector('[data-claim] button').textContent=context.todoType==='review'?'提交':'重新提交';
    if(context.todoType==='review'){
      const buttons=document.createElement('div');buttons.className='pool-review-actions';
      const submit=page.querySelector('[data-claim]');submit.before(buttons);
      const reject=document.createElement('text-button');reject.setAttribute('variant','outline');reject.textContent='驳回';
      buttons.append(reject,submit);
      reject.addEventListener('click',()=>{page.querySelector('[role=status]').textContent='已驳回（演示操作）';});
    }
    page.querySelector('[role=status]').classList.add('pool-rejection-notice');
    if(context.todoType==='assigned'){page.querySelector('[role=status]').hidden=true;page.querySelector('.pool-data-toolbar').style.justifyContent='flex-end';}
  }
  const videoDescriptions=[
    ['将方块放入收纳盒','夹取桌面方块，将其完整放入收纳盒，最后松开夹爪。'],
    ['密封包装盒','将包装盒盖合拢，沿边缘压紧，确认盒盖不会松开。'],
    ['整理桌面工具','依次将桌面工具放入收纳袋，完成后封好袋口。'],
    ['将物品摆放到货架','将桌面的物品逐个摆放到货架指定位置。'],
    ['擦拭桌面','使用抹布擦拭桌面，覆盖整个工作区域。']
  ];
  records.forEach((record,index)=>{
    const content=videoDescriptions[index];
    if(!content)return;
    const description=record.row.querySelector('.task-record-media-description');
    description.querySelector('.task-record-media-description__label').textContent=content[0];
    const details=description.querySelector('dl');
    const item=document.createElement('div'),text=document.createElement('dd');
    text.textContent=content[1];item.append(text);details.replaceChildren(item);
  });
  page.querySelectorAll('.task-record-videos').forEach(group=>{
    [...group.children].forEach((media,index)=>{
      const frame=document.createElement('div');frame.className='pool-video-frame';
      const label=document.createElement('span');label.className='pool-video-label';label.textContent=['头部','左臂','右臂'][index];
      media.before(frame);frame.append(media,label);
    });
  });
  const selected=new Set(),form=page.querySelector('form'),summary=page.querySelector('[role=status]');let filters={};
  function render(){let count=0;records.forEach(r=>{r.row.hidden=Object.entries(filters).some(([k,v])=>v&&!r[k].includes(v));if(!r.row.hidden)count++;const status=r.row.querySelector('[data-status]');status.textContent=r.claimed?'已领取':'待领取';status.className='table-outline-tag table-outline-tag--'+(r.claimed?'active':'neutral');if(r.claimed)selected.delete(r.id);const checkbox=r.row.querySelector('[data-select]');if(rejected){const kind=records.indexOf(r)%3;status.className='pool-quality-result';status.innerHTML=`<span class="pool-quality-result__label is-${kind}">${['合格','操作失误','不合格'][kind]}</span>${kind!==1?`<span class="pool-quality-result__tags"><span class="pool-quality-result__error">1条错误</span>${kind===0?'<span class="pool-quality-result__modified">已修改</span>':''}</span>`:''}`;}if(checkbox){checkbox.disabled=r.claimed;checkbox.checked=selected.has(r.id);}r.row.querySelectorAll('[data-result]').forEach(button=>{button.hidden=!r.claimed;});});summary.textContent=`共 ${count} 条数据　已选 ${selected.size} 条，最多同时操作 20 条`;page.querySelector('[data-claim]').toggleAttribute('disabled',!rejected&&!selected.size);if(rejected)summary.textContent='驳回原因：质检结果存在错误，请检查标记为错误的数据并修正后重新提交。';page.querySelector('list-pagination').setAttribute('total',count);const visible=records.filter(r=>!r.row.hidden&&!r.claimed);const all=page.querySelector('[data-all]');if(!all)return;all.disabled=visible.length===0;all.checked=visible.length>0&&visible.every(r=>selected.has(r.id));all.indeterminate=!all.checked&&visible.some(r=>selected.has(r.id));}
  form.addEventListener('value-change',()=>{filters=Object.fromEntries(new FormData(form));render();});form.onsubmit=e=>e.preventDefault();
  page.querySelector('task-filter-bar').addEventListener('filter-refresh',()=>{filters=Object.fromEntries(new FormData(form));render();});
  table.addEventListener('change',e=>{if(e.target.matches('[data-all]'))records.filter(r=>!r.row.hidden&&!r.claimed).forEach(r=>e.target.checked?selected.add(r.id):selected.delete(r.id));else if(e.target.matches('[data-select]')){const r=records.find(r=>r.row===e.target.closest('tr'));if(!r.claimed)e.target.checked?selected.add(r.id):selected.delete(r.id);}render();});
  page.querySelector('[data-claim]').onclick=()=>{if(rejected){summary.textContent=context.todoType==='review'?'已提交（演示操作）':'已重新提交（演示操作）';return;}records.filter(r=>!r.claimed&&selected.has(r.id)).forEach(r=>r.claimed=true);selected.clear();render();};
  table.addEventListener('click',e=>{const r=records.find(r=>r.row===e.target.closest('tr'));if(!r)return;if(r.claimed&&e.target.matches('[data-result]'))r.row.querySelector('[data-quality]').textContent=e.target.dataset.result;if(e.target.matches('[data-process]'))location.href='../workbench/optimized.html';});
  page.addEventListener('header-back',()=>{page.remove();parent.hidden=false;});render();
 };
})();
