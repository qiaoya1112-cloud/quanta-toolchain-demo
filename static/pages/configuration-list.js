(() => {
  const rule=document.body.dataset.pageId==='rule-management';
  const table=document.querySelector('task-data-table');
  const feedback=document.querySelector('[data-feedback]');
  document.addEventListener('filter-change',event=>{
    const {name='',scene='',creator=''}=event.detail;
    let count=0;
    table.querySelectorAll('tbody tr').forEach(row=>{
      const cells=[...row.cells].map(cell=>cell.textContent.trim());
      const matches=cells[rule?2:1].toLowerCase().includes(name.trim().toLowerCase())&&(!rule||((!scene||cells[1]===scene)&&cells[6].toLowerCase().includes(creator.trim().toLowerCase())));
      row.hidden=!matches;if(matches)count++;
    });
    document.querySelector('[data-empty]').hidden=count>0;
    feedback.textContent='';
  });
  document.addEventListener('header-action',()=>{feedback.textContent=`当前为列表预览，新增${rule?'规则':'工作台'}表单尚未配置。`;});
  table.addEventListener('row-action',()=>{feedback.textContent='当前为列表预览，规则详情尚未配置。';});
})();
