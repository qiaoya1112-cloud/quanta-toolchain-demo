(() => {
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const seed=[
 ['100008','铅笔归位','书房','V2',2,40,'铅笔、笔筒、书桌、收纳盒、标签贴、托盘','1 支铅笔平放在书桌台面，笔筒直立且有空位。','铅笔插入笔筒并保持稳定，桌面无散落铅笔。','1分钟'],
 ['100021','玻璃杯入柜','厨房','V2',3,12,'玻璃杯、橱柜、防滑垫、托盘、隔板、位置标签','1 个空玻璃杯放在操作台，下层橱柜柜门打开，指定位置为空。','玻璃杯平稳放在下层橱柜指定位置，柜门闭合，杯体无碰撞或倾倒。','2分钟'],
 ['100021','玻璃杯入柜','厨房','V3',4,24,'玻璃杯、橱柜、防滑垫、托盘、隔板、位置标签','1 个空玻璃杯放在操作台，上层橱柜柜门打开，指定位置为空。','玻璃杯平稳放在上层橱柜指定位置，柜门闭合，杯体无碰撞或倾倒。','2.5分钟'],
 ['100031','抹布归位','厨房','V1',2,30,'抹布、水槽、挂钩、收纳篮、清洁剂、定位贴','1 块抹布散放在水槽左侧台面，右侧标记区域为空且干净。','抹布展开并平铺在水槽右侧标记区域内，无折叠、无悬垂。','1.5分钟'],
 ['100036','餐盘入架','厨房','V2',3,36,'餐盘、沥水架、防滑垫、餐具篮、操作台、定位贴','1 个餐盘平放在操作台，沥水架有空槽且放置稳定。','餐盘竖直插入沥水架空槽并保持稳定，台面无遗留餐盘。','2分钟']
 ];
 const cols=[['id','指令 ID',100],['name','指令名称',130],['iteration','指令迭代',100],['scene','场景',80],['workspace','工作区',90],['version','指令版本号',110],['description','指令描述',480],['difficulty','难度',70],['mirrors','镜像',70],['duration','目标采集时长',120],['props','道具',180],['reason','不合格原因',180],['result','审批结果',100]];
 window.openCommandApprovalDetail=(batch,{readonly=false,onBack,onComplete}={})=>{
  const main=document.querySelector('.process-page__main');
  const previous=[...main.children].map(el=>[el,el.hidden]);previous.forEach(([el])=>el.hidden=true);
  const detail=document.createElement('section');detail.className='command-content approval-detail';main.append(detail);
  const records=batch.details||(batch.details=Array.from({length:batch.versions},(_,i)=>{const s=seed[i%seed.length];return {key:i,id:s[0],name:s[1],iteration:'目标态',scene:'家庭',workspace:s[2],version:i<5?s[3]:'V'+(Math.floor(i/5)+3),difficulty:s[4],mirrors:1,duration:s[5]+' h',props:s[6],description:`【初始状态】${s[7]}【结束状态】${s[8]}【时长上限】${s[9]}`,reason:i<batch.failed?'指令描述需补充验收条件':'',result:i<batch.failed?'不合格':'合格'};}));
  const editable=!readonly&&batch.status==='审批中';let page=1,size=5,filters={};
  const input=(key,label)=>`<form-input name="${key}" label="${label}" placeholder="输入${label}"></form-input>`;
  const select=(key,label,values)=>`<form-select name="${key}" label="${label}"><option value="">全部${label}</option>${values.map(v=>`<option>${v}</option>`).join('')}</form-select>`;
  detail.innerHTML=`<task-page-header title="指令审批详情" back status="${batch.status}" ${editable?'action="完成审批"':''}></task-page-header><task-filter-bar><form>${input('id','指令 ID')}${input('name','指令名称')}${input('iteration','指令迭代')}${input('version','指令版本号')}${select('difficulty','难度',[1,2,3,4,5])}${input('props','道具')}${select('scene','场景',['家庭','办公'])}${select('workspace','工作区',['书房','厨房','客厅','办公区'])}${select('result','审批结果',['合格','不合格'])}</form></task-filter-bar><div class="task-data-table command-table"><div class="task-data-table__scroll"><table aria-label="指令审批详情"><colgroup>${cols.map(c=>`<col style="width:${c[2]}px">`).join('')}<col style="width:112px"></colgroup><thead><tr>${cols.map(c=>`<th scope="col">${c[1]}</th>`).join('')}<th scope="col">操作</th></tr></thead><tbody></tbody></table><p class="command-empty" hidden>暂无符合条件的指令</p></div><list-pagination page-size="5"></list-pagination></div>`;
  const close=()=>{detail.querySelector('.command-table')._scrollObserver?.disconnect();detail.remove();previous.forEach(([el,hidden])=>el.hidden=hidden);onBack?.();};
  detail.addEventListener('header-back',close);
  function render(){const matched=records.filter(r=>Object.entries(filters).every(([k,v])=>!v||(['difficulty','scene','workspace','result'].includes(k)?String(r[k])===v:String(r[k]).toLowerCase().includes(v.toLowerCase()))));page=Math.min(page,Math.max(1,Math.ceil(matched.length/size)));
   detail.querySelector('tbody').innerHTML=matched.slice((page-1)*size,page*size).map(r=>`<tr data-key="${r.key}">${cols.map(([key])=>`<td${['description','props','reason'].includes(key)?' class="approval-detail-wrap"':''}>${key==='result'?`<span class="table-outline-tag table-outline-tag--${r.result==='合格'?'active':'danger'}">${r.result}</span>`:esc(r[key]||'—')}</td>`).join('')}<td>${editable?`<text-button variant="text" data-review="${r.key}">${r.result==='合格'?'不合格':'恢复合格'}</text-button>`:'—'}</td></tr>`).join('');detail.querySelector('.command-empty').hidden=matched.length>0;const pager=detail.querySelector('list-pagination');pager.setAttribute('total',matched.length);pager.setAttribute('page',page);customElements.get('task-data-table').enhanceFixedEdges(detail.querySelector('.command-table'),1,2);}
  const form=detail.querySelector('form');form.onsubmit=e=>e.preventDefault();form.addEventListener('value-change',()=>{filters=Object.fromEntries(new FormData(form));page=1;render();});detail.querySelector('task-filter-bar').addEventListener('filter-refresh',()=>{filters=Object.fromEntries(new FormData(form));page=1;render();});detail.querySelector('list-pagination').addEventListener('page-change',e=>{page=e.detail.page;size=e.detail.pageSize;render();});
  detail.querySelector('tbody').onclick=e=>{const b=e.target.closest('[data-review]');if(!b||!editable)return;const r=records[Number(b.dataset.review)];if(r.result==='不合格'){r.result='合格';r.reason='';r.reasons=[];r.note='';render();return;}
   const reasons=['指令关键要素不完整','指令描述有不清晰或存在歧义','指令名称和描述不一致','道具要求不合理','场景或工作区不适配','指令无法执行','设备操作不便','单一动作操作时长过短','其他'];
   const modal=document.createElement('process-action-dialog');modal.setAttribute('variant','approval-rejection');document.body.append(modal);
   const dialog=modal.querySelector('dialog');dialog.classList.add('command-dialog','approval-rejection-dialog');
   modal.querySelector('.flow-info-fields').innerHTML=`<fieldset><legend>不合格原因（必填，可多选）</legend><div class="approval-reason-options">${reasons.map(reason=>`<form-checkbox name="reason" value="${esc(reason)}" label="${esc(reason)}"></form-checkbox>`).join('')}</div></fieldset><label class="approval-reason-note">自定义说明（选填）<textarea name="note" maxlength="50" placeholder="选填，最多 50 字"></textarea></label><div class="approval-reason-count">0 / 50</div>`;
   modal.querySelector('footer [data-dismiss] button').textContent='取消';
   const note=modal.querySelector('textarea'),feedback=modal.querySelector('.action-dialog-feedback');feedback.setAttribute('role','alert');
   note.oninput=()=>{modal.querySelector('.approval-reason-count').textContent=note.value.length+' / 50';};
   modal.addEventListener('action-dialog-confirm',()=>{
    const selected=[...modal.querySelectorAll('form-checkbox')].filter(c=>c.checked).map(c=>c.value);
    if(!selected.length){feedback.textContent='请至少选择一个不合格原因';modal.querySelector('input[type="checkbox"]').focus();return;}
    if(note.value.length>50){feedback.textContent='自定义说明最多 50 字';return;}
    r.result='不合格';r.reasons=selected;r.note=note.value.trim();r.reason=[...selected,r.note].filter(Boolean).join('；');dialog.close();render();
   });
   modal.addEventListener('change',()=>{feedback.textContent='';});
   dialog.addEventListener('close',()=>modal.remove(),{once:true});modal.show();

  };
  detail.addEventListener('header-action',()=>{if(!editable)return;const failed=records.filter(r=>r.result==='不合格').length;Object.assign(batch,{failed,result:failed===0?'全部合格':failed===records.length?'全部不合格':'部分合格',status:'审批完成',reviewer:'当前演示审批员',reviewed:new Date().toLocaleString('sv-SE')});onComplete?.();close();});
  render();
 };
})();
