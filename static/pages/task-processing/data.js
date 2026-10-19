(() => {
  const params=new URLSearchParams(location.search);
  const header=document.querySelector('task-page-header');
  if(params.get('from')==='assignment')header.setAttribute('back-label','返回任务分配');
  const table=document.querySelector('task-data-table');
  const rows=[...table.querySelectorAll('tbody tr')];
  const name=params.get('name')||'端到端切分标注';
  const id=params.get('id')||'20455';
  const completed=Math.min(rows.length,Math.max(0,Number(params.get('completed'))||0));
  document.querySelector('task-page-header h1').textContent=name;
  document.title=name+' · 任务数据';
  const running=params.get('running')!=='false';
  header.setAttribute('status',running?'运行中':'已暂停');
  header.setAttribute('status-tone',running?'running':'paused');
  const pager=document.querySelector('list-pagination');
  table.querySelector('.task-data-table__frame').append(pager);
  const searchField=document.querySelector('search-input');
  const input=searchField.querySelector('input');
  let query='';
  const apply=()=>{
    const matched=rows.filter(row=>row.cells[0].textContent.toLowerCase().includes(query));
    pager.setAttribute('total',matched.length);
    const visible=new Set(matched.slice((pager.page-1)*pager.pageSize,pager.page*pager.pageSize));
    rows.forEach(row=>row.hidden=!visible.has(row));
    const done=matched.filter(row=>Number(row.dataset.row)<completed).length;
    document.querySelector('.task-record-summary').textContent=`${name}：命中 ${matched.length.toLocaleString()} 条 · 已完成 ${done.toLocaleString()} 条 · 待处理 ${(matched.length-done).toLocaleString()} 条`;
    document.querySelector('[data-empty]').hidden=matched.length>0;
    table.querySelector('.task-data-table__scroll').scrollTop=0;
  };
  const search=()=>{query=input.value.trim().toLowerCase();pager.setAttribute('page','1');apply();};
  searchField.addEventListener('search-change',search);
  document.querySelector('[data-refresh]').addEventListener('click',search);
  document.querySelector('form').addEventListener('submit',event=>{event.preventDefault();search();});
  input.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();search();}});
  pager.addEventListener('page-change',apply);
  header.addEventListener('header-back',()=>{
    location.href=(params.get('from')==='assignment'?'../assignment-management/index.html':'./index.html')+(params.has('embed')?'?embed=table-example':'');
  });
  table.addEventListener('row-action',event=>{
    if(event.detail.action!=='annotation')return;
    const url=new URL('../workbench/optimized.html',location.href);
    url.search=new URLSearchParams({taskId:id,dataId:rows[event.detail.row].cells[0].textContent}).toString();
    location.href=url.href;
  });
  apply();
})();
