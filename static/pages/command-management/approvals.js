(() => {
 const original=document.querySelector('.command-content');
 const tabs=document.createElement('task-status-tabs');tabs.setAttribute('variant','command-management');original.before(tabs);
 const panel=document.createElement('section');panel.className='command-content approval-content';panel.hidden=true;original.after(panel);
 const columns=[['id','指令表 ID',150],['versions','指令版本总数',120],['failed','不合格数',100],['result','审批结果',120],['status','状态',120],['reviewer','审核人',160],['reviewed','审核时间',190],['publisher','发布人',150],['operated','操作时间',190],['uploader','上传人',150],['uploaded','上传时间',190]];
 const rows=[['UP260907001',12,0,'待生成','审批中','—','—','当前演示用户','2026-09-28 15:36:32','演示算法员','2026-09-07 09:20:18'],['UP260905002',7,3,'部分合格','审批完成','当前演示审批员','2026-09-28 15:26:48','演示算法员','2026-09-05 11:16:02','演示算法员','2026-09-05 11:08:31'],['UP260903001',2,1,'部分合格','审批完成','演示审批员','2026-09-03 16:35:20','演示算法员','2026-09-03 14:02:36','演示运营专员','2026-09-03 13:56:08']].map(values=>Object.fromEntries(columns.map((c,i)=>[c[0],values[i]])));
 const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 panel.innerHTML=`<form class="command-filters"><div class="approval-filters"><form-input name="id" label="指令表 ID" placeholder="输入指令表 ID"></form-input><form-select name="result" label="审批结果"><option value="">全部审批结果</option><option>待生成</option><option>全部合格</option><option>部分合格</option><option>全部不合格</option></form-select><form-select name="status" label="状态"><option value="">全部状态</option><option>审批中</option><option>审批完成</option></form-select></div></form><div class="task-data-table command-table"><div class="task-data-table__scroll"><table aria-label="指令审批列表"><colgroup>${columns.map(c=>`<col style="width:${c[2]}px">`).join('')}<col style="width:130px"></colgroup><thead><tr>${columns.map(c=>`<th scope="col">${c[1]}</th>`).join('')}<th scope="col">操作</th></tr></thead><tbody></tbody></table><p class="command-empty" data-approval-empty hidden>暂无符合条件的审批记录</p></div><list-pagination total="3" page-size="10"></list-pagination></div><p data-approval-feedback role="status"></p>`;
 const header=document.querySelector('task-page-header header');const upload=document.createElement('text-button');upload.setAttribute('variant','primary');upload.textContent='上传指令表';upload.hidden=true;header.append(upload);
 const approvalTable=panel.querySelector('.command-table');
 function syncApprovalTable(){
   if(panel.hidden)return;
   customElements.get('task-data-table').enhanceFixedEdges(approvalTable,1,1);
 }
 let filters={},page=1,size=10;
 function render(){const filtered=rows.filter(r=>Object.entries(filters).every(([k,v])=>!v||(k==='id'?r.id.toLowerCase().includes(v.toLowerCase()):r[k]===v)));page=Math.min(page,Math.max(1,Math.ceil(filtered.length/size)));panel.querySelector('tbody').innerHTML=filtered.slice((page-1)*size,page*size).map(r=>`<tr data-id="${r.id}">${columns.map(([key])=>`<td>${['result','status'].includes(key)?`<span class="table-outline-tag table-outline-tag--${key==='status'?(r.status==='审批完成'?'active':'running'):(r.result==='待生成'?'neutral':r.failed?'paused':'active')}">${esc(r[key])}</span>`:esc(r[key])}</td>`).join('')}<td><button data-approval-action="view">查看</button>${r.status==='审批中'?'<button data-approval-action="approve">审批</button>':''}</td></tr>`).join('');panel.querySelector('[data-approval-empty]').hidden=filtered.length>0;panel.querySelector('list-pagination').setAttribute('total',filtered.length);panel.querySelector('list-pagination').setAttribute('page',page);syncApprovalTable();}
 panel.querySelector('form').addEventListener('value-change',()=>{filters=Object.fromEntries(new FormData(panel.querySelector('form')));page=1;render();});panel.querySelector('form').onsubmit=e=>e.preventDefault();
 panel.querySelector('list-pagination').addEventListener('page-change',e=>{page=e.detail.page;size=e.detail.pageSize;render();});
 tabs.addEventListener('tab-change',e=>{const approval=e.detail.value==='approvals';original.hidden=approval;panel.hidden=!approval;upload.hidden=!approval;if(approval)syncApprovalTable();document.querySelector('app-drawer')?.removeAttribute('open');});
 panel.querySelector('tbody').onclick=e=>{const b=e.target.closest('[data-approval-action]');if(!b)return;const row=rows.find(r=>r.id===b.closest('tr').dataset.id);window.openCommandApprovalDetail(row,{readonly:b.dataset.approvalAction==='view',onComplete:render});};
 upload.onclick=()=>window.openCommandUpload();
 render();
 document.querySelectorAll('.command-table').forEach(frame=>customElements.get('task-data-table').enhanceFixedEdges(frame));
})();
