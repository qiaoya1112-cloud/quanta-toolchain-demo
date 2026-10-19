(() => {
  const table=document.querySelector('task-data-table');
  const row=table.querySelector('tbody tr');
  document.addEventListener('filter-change',event=>{
    const {name='',creator=''}=event.detail;
    row.hidden=!row.cells[0].textContent.toLowerCase().includes(name.trim().toLowerCase())||(creator&&row.cells[4].textContent!==creator);
    document.querySelector('[data-empty]').hidden=!row.hidden;
    document.querySelector('[data-feedback]').textContent='';
  });
  table.addEventListener('row-action',event=>{
    document.querySelector('[data-feedback]').textContent=event.detail.action==='versions'?'当前为列表预览，版本列表尚未配置。':'当前为列表预览，算子详情尚未配置。';
  });
})();
