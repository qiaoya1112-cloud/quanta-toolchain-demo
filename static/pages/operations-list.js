(() => {
  const page=document.body.dataset.pageId;
  const table=document.querySelector('task-data-table');
  const feedback=document.querySelector('[data-feedback]');
  document.addEventListener('filter-change',event=>{
    const {name='',owner='',status='',scene=''}=event.detail;
    let count=0;
    table.querySelectorAll('tbody tr').forEach(row=>{
      const cells=[...row.cells].map(cell=>cell.textContent.trim());
      const project=page==='project-management';
      const matches=cells[1].toLowerCase().includes(name.trim().toLowerCase())&&(project?(!owner||cells[3].includes(owner))&&(!status||cells[4]===status):!scene||cells[2].includes(scene));
      row.hidden=!matches;if(matches)count++;
    });
    document.querySelector('[data-empty]').hidden=count>0;
    feedback.textContent='';
  });
  document.addEventListener('header-action',()=>{feedback.textContent='当前为列表预览，新增表单尚未配置。';});
  table.addEventListener('row-action',()=>{if(page!=='permission-management')return;feedback.textContent='当前为列表预览，编辑表单尚未配置。';});
  document.addEventListener('tab-change',event=>{
    if(page!=='permission-management')return;
    const value=event.detail.value;
    if(!['roles','resources','grants'].includes(value))return;
    table.setAttribute('variant',`permission-${value}`);table.render();
    const button=document.querySelector('[data-permission-add]');
    button.querySelector('button').textContent={roles:'新增角色',resources:'新增资源',grants:'新增授权'}[value];
    feedback.textContent='';
  });
  document.querySelector('[data-permission-add]')?.addEventListener('click',()=>{feedback.textContent='当前为列表预览，新增表单尚未配置。';});
})();
