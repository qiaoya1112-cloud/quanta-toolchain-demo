(() => {
  const table=document.querySelector('task-data-table');
  let filters={};
  let scene='';
  const pagination=document.querySelector('.task-processing-pagination');
  document.querySelector('task-data-table .task-data-table__frame').append(pagination);
  let currentPage=1,pageSize=20,totalPages=1;
  const apply=()=>{
    const matched=[];
    table.querySelectorAll('tbody tr').forEach(row=>{
      const cells=[...row.cells].map(cell=>cell.textContent.trim());
      const ids=(filters.id||'').split(/[,，]/).map(value=>value.trim()).filter(Boolean);
      const matches=(!ids.length||ids.includes(cells[0]))&&(!filters.name||cells[1].toLowerCase().includes(filters.name.toLowerCase()))&&(!filters.project||cells[2]===filters.project)&&(!filters.flow||cells[3].includes(filters.flow))&&(!filters.processing||(row.querySelector('[role=switch]').getAttribute('aria-checked')==='true')===(filters.processing==='启用'))&&(!filters.published||cells[5]===filters.published)&&(!filters.nature||cells[7]===filters.nature)&&(!filters.creator||cells[8].toLowerCase().includes(filters.creator.toLowerCase()));
      row.hidden=true;if(matches&&(!scene||cells[3].includes(scene)))matched.push(row);
    });
    const filtered=Boolean(scene)||Object.values(filters).some(value=>String(value).trim());
    totalPages=Math.max(1,Math.ceil(matched.length/pageSize));
    currentPage=Math.min(currentPage,totalPages);
    matched.slice((currentPage-1)*pageSize,currentPage*pageSize).forEach(row=>{row.hidden=false;});
    const hasRows=matched.length>(currentPage-1)*pageSize;
    document.getElementById('task-empty').hidden=hasRows;
    document.getElementById('task-empty').textContent=filtered?'暂无符合条件的任务':'当前页暂无示例数据';
    document.getElementById('task-feedback').textContent='';
    pagination.setAttribute('total',matched.length);
    pagination.setAttribute('page',currentPage);
    pagination.setAttribute('page-size',pageSize);
  };
  pagination.addEventListener('page-change',event=>{currentPage=event.detail.page;pageSize=event.detail.pageSize;apply();});
  document.addEventListener('task-query',event=>{filters=event.detail;currentPage=1;apply();});
  table.addEventListener('processing-change',apply);
  document.addEventListener('scene-change',event=>{scene=event.detail.value;currentPage=1;apply();});
  table.addEventListener('row-action',event=>{
    if(event.detail.action==='details'){window.openProcessingTaskDetail(table.taskRecords[event.detail.row]);return;}
    const labels={data:'数据',details:'详情',edit:'编辑'};
    document.getElementById('task-feedback').textContent=`${labels[event.detail.action]||'操作'}页面尚未配置，当前为组件预览。`;
  });
  document.querySelectorAll('platform-sidebar .platform-sidebar__item:not([data-page-id])').forEach(button=>button.addEventListener('click',()=>{
    location.href='../process-management/index.html#'+encodeURIComponent(button.title);
  }));
  document.addEventListener('header-action',()=>{
    location.assign('./create.html');
  });
  apply();
})();
