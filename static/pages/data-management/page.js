(() => {
  const table=document.querySelector('task-data-table');
  const rows=[...table.querySelectorAll('tbody tr')];
  const all=table.querySelector('[data-select-all]');
  const selected=new Set();
  let filters={};
  const pager=table.querySelector("list-pagination");
  let page=1,pageSize=20;
  const feedback=document.querySelector('[data-feedback]');
  const updateSelection=()=>{
    const visible=rows.filter(row=>!row.hidden);
    const checked=visible.filter(row=>selected.has(row.dataset.row)).length;
    all.checked=visible.length>0&&checked===visible.length;
    all.indeterminate=checked>0&&checked<visible.length;all.disabled=!visible.length;
    document.querySelector('[data-selected-count]').textContent=`已选择 ${selected.size} 条`;
    document.querySelectorAll('[data-batch]').forEach(button=>{button.disabled=!selected.size;});
  };
  const apply=()=>{
    const scene=document.querySelector('task-page-header select').value;
    const includes=(value,search)=>!search||value.toLowerCase().includes(search.trim().toLowerCase());
    let count=0;
    const matched=[];
    rows.forEach((row,index)=>{
      const r=table.records[index];
      const match=includes(r[0],filters.dataId)&&includes(r[1],filters.collectionId)&&includes(r[2],filters.processingId)&&includes(r[4],filters.qualityFlow)&&includes(r[5],filters.annotationFlow)&&includes(r[9],filters.qualityNode)&&includes(r[9],filters.annotationNode)&&includes(r[10],filters.currentAssignee)&&includes(r[10],filters.allAssignees)&&(!filters.project||r[11]===filters.project)&&(!scene||(scene==='质检'?!!r[4]:scene==='标注'?!!r[5]:r[9].includes('验收')));
      row.hidden=true;if(match){count++;matched.push(row);}
      if(!match){selected.delete(row.dataset.row);row.querySelector('[data-select-row]').checked=false;}
    });
    page=Math.min(page,Math.max(1,Math.ceil(count/pageSize)));
    matched.slice((page-1)*pageSize,page*pageSize).forEach(row=>row.hidden=false);
    pager.setAttribute('total',count);pager.setAttribute('page',page);pager.setAttribute('page-size',pageSize);
    document.querySelector('[data-empty]').hidden=count>0;feedback.textContent='';updateSelection();
  };
  pager.addEventListener('page-change',event=>{page=event.detail.page;pageSize=event.detail.pageSize;apply();});
  document.addEventListener('filter-change',event=>{filters=event.detail;page=1;apply();});
  document.addEventListener('scene-change',apply);
  table.addEventListener('change',event=>{
    if(event.target===all){rows.filter(row=>!row.hidden).forEach(row=>{row.querySelector('[data-select-row]').checked=all.checked;if(all.checked)selected.add(row.dataset.row);else selected.delete(row.dataset.row);});}
    else if(event.target.matches('[data-select-row]')){const id=event.target.closest('tr').dataset.row;if(event.target.checked)selected.add(id);else selected.delete(id);}
    updateSelection();
  });
  table.addEventListener('row-action',event=>{feedback.textContent=`当前为数据列表预览，${event.detail.action==='view'?'查看详情':'重新分配'}尚未接入。`;});
  document.querySelectorAll('[data-batch]').forEach(button=>button.addEventListener('click',()=>{feedback.textContent=`已选择 ${selected.size} 条数据，${button.textContent}尚未接入。`;}));
  apply();
})();
