(() => {
const resources=[
{id:'MAP-001',type:'maps',name:'test_map',project:'京东仓内导航',description:'京东仓内导航地图，包含拣选区域 Point。',valid:true,pin:'V5',versions:[{id:'V6',date:'2026-10-12 14:30',points:10},{id:'V5',date:'2026-09-18 09:20',points:10}]},
{id:'MAP-002',type:'maps',name:'京东测试场',project:'京东仓内导航',description:'用于仓内导航测试。',valid:false,error:'Point 文件缺失：waypoints.yaml',versions:[{id:'V1',date:'2026-10-10 10:20',points:0}]},
{id:'MAP-003',type:'maps',name:'宁德产线 3F',project:'宁德产线',description:'三层产线地图。',valid:false,error:'地图文件尚未提供',versions:[{id:'V1',date:'2026-10-09 16:00',points:0}]}];
const versionExtras={
 'MAP-001:V6':{
  workflows:[['京东单品拣放流程','精准导航 · 拣选工位 · V6','草稿'],['京东仓储移动流程','VLN · 移动指令 · V6','已发布']],
  files:[['map.pgm','PGM','73,763 B'],['map_high.pgm','PGM','73,763 B'],['map_low.pgm','PGM','73,763 B'],['map.ply','PLY','66,562 B'],['map.yaml','YAML','155 B'],['map_high.yaml','YAML','160 B'],['map_low.yaml','YAML','159 B'],['waypoints.yaml','YAML','544 B']]
 }
};
function extraSections(r,version){
 const data=versionExtras[r.id+':'+version]||{workflows:[],files:[]};
 const section=(title,count,headers,widths,rows)=>`<details class="panel resource-fold" open><summary class="panel-heading"><span class="section-label">${title}</span><span class="muted">${count} · ${version}</span></summary><task-data-table hydrate class="resource-table"><table><colgroup>${widths.map(w=>`<col style="width:${w}%">`).join('')}</colgroup><thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows||`<tr><td colspan="3">暂无该版本的示例记录</td></tr>`}</tbody></table></task-data-table></details>`;
 return section('Workflow 引用',`${data.workflows.length} 个引用`,['Flow 名称','引用节点','状态'],[45,40,15],data.workflows.map(([name,node,status])=>`<tr><td>${escape(name)}</td><td>${escape(node)}</td><td><span class="badge ${status==='已发布'?'pass':'neutral'}">${status}</span></td></tr>`).join(''))+
 section('文件清单',`${data.files.length} 个文件`,['文件名称','格式','大小'],[65,15,20],data.files.map(row=>`<tr>${row.map(cell=>`<td>${escape(cell)}</td>`).join('')}</tr>`).join(''));
}
const $=s=>document.querySelector(s),list=$('resource-list'),detail=$('#detail');
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const tooltip=document.createElement('div');tooltip.id='point-cell-tooltip';tooltip.className='point-cell-tooltip';tooltip.setAttribute('role','tooltip');tooltip.hidden=true;document.body.append(tooltip);
let tooltipCell=null;
const hideTooltip=()=>{tooltip.hidden=true;tooltipCell?.removeAttribute('aria-describedby');tooltipCell=null;};
const showTooltip=event=>{
 const cell=event.target.closest('.resource-table [data-full-text]');if(!cell)return;
 const content=cell.querySelector('.version-select')||cell;
 const shortened=content.textContent.trim()!==cell.dataset.fullText;
 const clipped=content.scrollWidth>content.clientWidth+1;
 if(!shortened&&!clipped){hideTooltip();return;}
 if(cell===tooltipCell)return;
 hideTooltip();tooltipCell=cell;tooltip.textContent=cell.dataset.fullText;tooltip.hidden=false;cell.setAttribute('aria-describedby',tooltip.id);
 const range=document.createRange();range.selectNodeContents(content);
 const rect=range.getBoundingClientRect();const box=tooltip.getBoundingClientRect();
 tooltip.style.left=Math.max(8,Math.min(rect.left,innerWidth-box.width-8))+'px';
 tooltip.style.top=(rect.top>box.height+8?rect.top-box.height-4:Math.min(innerHeight-box.height-8,rect.bottom+4))+'px';
};
detail.addEventListener('pointerover',showTooltip);detail.addEventListener('focusin',showTooltip);
detail.addEventListener('pointerout',event=>{if(tooltipCell&&!tooltipCell.contains(event.relatedTarget))hideTooltip();});
detail.addEventListener('focusout',hideTooltip);detail.addEventListener('click',hideTooltip);
document.addEventListener('scroll',hideTooltip,true);window.addEventListener('resize',hideTooltip);
document.addEventListener('keydown',event=>{if(event.key==='Escape')hideTooltip();});
let tab='maps',status='all',selected='MAP-001',version='V6',zoom=1,rotation=0,point='',detailTab='points';
const current=()=>resources.find(r=>r.id===selected);
const badge=r=>`<span class="table-outline-tag ${r.valid?'table-outline-tag--success':'table-outline-tag--danger'}">${r.valid?'校验通过':'校验失败'}</span>`;
function filtered(){const term=$('#search').value.trim().toLowerCase();return resources.filter(r=>r.type===tab&&(!$('#project').value||r.project===$('#project').value)&&(!term||(r.name+' '+r.id).toLowerCase().includes(term)));}
function render(){
 const isModels=tab==='models';
 $('.filters').hidden=isModels;$('.resource-workspace').hidden=isModels;$('#notice').hidden=isModels;
 if(isModels){detail.replaceChildren();list.items=[];return;}
 const all=filtered(),shown=all.filter(r=>status==='all'||r.valid===(status==='pass'));
 $('#statuses').innerHTML=[['all','全部',all.length],['pass','校验通过',all.filter(r=>r.valid).length],['fail','校验失败',all.filter(r=>!r.valid).length]].map(([id,label,n])=>`<button data-status="${id}" aria-pressed="${id===status}">${label} ${n}</button>`).join('');
 if(!shown.some(r=>r.id===selected)){selected=shown[0]?.id;version=current()?.versions?.[0].id;zoom=1;rotation=0;point='';}
 $('#list-title').textContent=tab==='maps'?'地图资源':'模型能力';$('#count').textContent=`共 ${shown.length} 个资源`;
 list.selected=selected;list.items=shown.map(r=>({id:r.id,label:r.name,status:r.valid?'pass':'fail',meta:`${r.versions[0].id} · ${r.valid?'PGM 地图 · Point 只读':r.error}`}));renderDetail();
}
function arrangeDetail(){
 const panels=[...detail.querySelectorAll(':scope > .panel')];
 const versionPanel=panels.shift();
 const mapPanel=panels.shift();
 if(!versionPanel||!mapPanel)return;
 const layout=document.createElement('div');layout.className='resource-detail-layout';
 const side=document.createElement('div');side.className='resource-info';
 const tabs=document.createElement('div');tabs.className='detail-tabs task-status-tabs';tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','地图资源信息');
 const resource=current(),activeVersion=resource.versions.find(item=>item.id===version),extras=versionExtras[resource.id+':'+version];
 const counts={points:activeVersion?.points||0,versions:resource.versions.length,workflows:extras?.workflows.length||0,files:extras?.files.length||0};
 const entries=[['points','Point 列表',panels[0]],['versions','地图版本',versionPanel],['workflows','Workflow 引用',panels[1]],['files','文件清单',panels[2]]];
 entries.forEach(([id,label,panel])=>{
  if(!panel){panel=document.createElement('section');panel.className='panel';panel.innerHTML='<div class="empty">暂无可用数据</div>';}
  const button=document.createElement('button');button.type='button';button.dataset.detailTab=id;button.id='detail-tab-'+id;button.textContent=label;button.setAttribute('role','tab');button.setAttribute('aria-controls','detail-panel-'+id);button.setAttribute('aria-selected',String(detailTab===id));button.tabIndex=detailTab===id?0:-1;const count=document.createElement('span');count.className='detail-tab-count';count.textContent=counts[id];button.append(count);tabs.append(button);
  const content=document.createElement('section');content.className='detail-tab-panel';content.id='detail-panel-'+id;content.setAttribute('role','tabpanel');content.setAttribute('aria-labelledby',button.id);content.hidden=detailTab!==id;
  // Transfer the shared table out of its previous collapsible section.
  const heading=panel.querySelector('.panel-heading');
  if(heading)heading.remove();
  content.append(...panel.childNodes);panel.remove();side.append(content);
 });
 side.prepend(tabs);mapPanel.classList.add('resource-map-panel');layout.append(mapPanel,side);
 detail.querySelector('.detail-heading').after(layout);
}
function renderDetail(){hideTooltip();const r=current();if(!r){detail.innerHTML='<div class="empty">暂无匹配资源<br>请调整搜索词或筛选条件</div>';return;}
 detail.innerHTML=`<div class="detail-heading"><div class="detail-heading-copy"><div class="detail-title"><h2>${escape(r.name)}</h2>${badge(r)}</div><p class="detail-subtitle">${escape(r.description)}</p></div><div class="detail-actions"><text-button variant="outline" data-edit>编辑信息</text-button></div></div>`;
 const v=r.versions.find(v=>v.id===version)||r.versions[0];version=v.id;
 const sorted=[...r.versions].sort((a,b)=>Number(b.id===r.pin)-Number(a.id===r.pin));
 detail.insertAdjacentHTML('beforeend',`<section class="panel"><div class="panel-heading"><h2>地图版本</h2><span class="muted">置顶 · 其余按新到旧 · 点击查看</span></div><task-data-table hydrate class="resource-table"><table class="resource-version-table"><colgroup><col style="width:64px"><col><col style="width:96px"><col style="width:176px"><col style="width:104px"></colgroup><thead><tr><th>版本</th><th>版本说明</th><th>Point 数量</th><th>上传时间</th><th>推荐版本</th></tr></thead><tbody>${sorted.map(v=>`<tr data-version="${v.id}" class="${v.id===version?'selected':''}"><td><button class="version-select" data-version="${v.id}">${v.id}</button></td><td>${v.id===r.versions[0].id?'最新上传':'历史版本'}</td><td>${v.points} Point</td><td class="muted">${v.date}</td><td><button type="button" class="text-button ${r.pin===v.id?'text-button--secondary':'text-button--outline'} resource-pin-button" data-pin="${v.id}" aria-pressed="${r.pin===v.id}" title="${r.pin===v.id?'取消置顶':'置顶此版本'}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6l-1 7 4 4v2H6v-2l4-4-1-7ZM12 16v5"/></svg>${r.pin===v.id?'已置顶':'置顶'}</button></td></tr>`).join('')}</tbody></table></task-data-table></section>`);
 if(!r.valid){detail.insertAdjacentHTML('beforeend',`<div class="panel empty"><strong>资源暂不可预览</strong><span>${escape(r.error)}</span></div>`);arrangeDetail();return;}
 detail.insertAdjacentHTML('beforeend',`<section class="panel"><div class="panel-heading"><div class="section-title"><h2>地图示意</h2><span class="muted">${version}</span></div><div class="map-tools"><button class="text-button small-button" data-map="rotate-right" aria-label="向右旋转" title="向右旋转 90°"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 10a9 9 0 1 0-2.6 8.4M21 4v6h-6"/></svg></button><button class="text-button small-button" data-map="minus" aria-label="缩小">−</button><button class="text-button small-button" data-map="reset">${Math.round(zoom*100)}%</button><button class="text-button small-button" data-map="plus" aria-label="放大">＋</button></div></div><div class="map-stage">${resourceMapPreview(point||"0")}${resourceMapOverview(zoom)}</div></section><details class="panel resource-fold" open><summary class="panel-heading"><span class="section-label">Point 列表</span><span class="muted">${v.points} 个 Point · ${version}</span></summary><task-data-table hydrate class="resource-table"><table class="resource-point-table"><colgroup><col style="width:24%"><col style="width:30%"><col style="width:46%"></colgroup><thead><tr><th>Point Name</th><th>Position x / y / z</th><th>Orientation qx / qy / qz / qw</th></tr></thead><tbody>${Array.from({length:v.points},(_,i)=>`<tr data-point="${i}" class="point-row ${point===String(i)?'selected':''}"><td><button class="version-select" data-point="${i}">${resourceMapPoints[i][0]}</button></td><td>${resourceMapPoints[i][1]} / ${resourceMapPoints[i][2]} / 0</td><td>0 / 0 / ${Math.sin(resourceMapPoints[i][3]*Math.PI/360).toFixed(5)} / ${Math.cos(resourceMapPoints[i][3]*Math.PI/360).toFixed(5)}</td></tr>`).join('')}</tbody></table></task-data-table></details>${extraSections(r,version)}`);
 arrangeDetail();
 detail.querySelectorAll('.resource-info .resource-table th,.resource-info .resource-table td').forEach(cell=>{cell.dataset.fullText=cell.textContent.trim();});
 detail.querySelectorAll('.resource-point-table th,.resource-point-table td').forEach(cell=>{
  const full=cell.textContent.trim();cell.dataset.fullText=full;cell.tabIndex=0;
  const button=cell.querySelector('button');
  if(button){button.setAttribute('aria-label',full);button.textContent=Array.from(full).length>10?Array.from(full).slice(0,10).join('')+'…':full;}
 });
 $('.map-drawing').style.transform=`rotate(${rotation}deg) scale(${zoom})`;
}
detail.addEventListener('wheel',event=>{
 const stage=event.target.closest('.map-stage');
 if(!stage||!event.deltaY)return;
 event.preventDefault();
 const delta=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?stage.clientHeight:1);
 const next=Math.max(.5,Math.min(2,zoom*Math.exp(-Math.max(-100,Math.min(100,delta))*.002)));
 if(next===zoom)return;
 zoom=next;
 stage.querySelector('.map-drawing').style.transform=`rotate(${rotation}deg) scale(${zoom})`;
 detail.querySelector('[data-map="reset"]').textContent=Math.round(zoom*100)+'%';
 const frame=stage.querySelector('.resource-map-overview span');
 frame.style.width=Math.min(64,64/zoom)+'px';frame.style.height=Math.min(66,66/zoom)+'px';
 stage.querySelector('.resource-map-scale span').textContent=Number((10/zoom).toFixed(1))+' m';
},{passive:false});
detail.addEventListener('keydown',e=>{const b=e.target.closest('[role=tab]');if(!b||!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const tabs=[...detail.querySelectorAll('[role=tab]')];const i=tabs.indexOf(b);tabs[e.key==='Home'?0:e.key==='End'?tabs.length-1:(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length].click();});
list.addEventListener('resource-select',e=>{selected=e.detail.value;version=current().versions?.[0].id;zoom=1;rotation=0;point='';render();});
$('.resource-tabs').addEventListener('click',e=>{const b=e.target.closest('[data-tab]');if(!b)return;tab=b.dataset.tab;status='all';selected=null;document.querySelectorAll('[data-tab]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));$('#notice').textContent='';render();});
$('#statuses').addEventListener('click',e=>{const b=e.target.closest('[data-status]');if(b){status=b.dataset.status;render();}});
$('#search').addEventListener('input',render);$('#project').addEventListener('value-change',render);
$('#validate').addEventListener('click',()=>{const data=filtered();$('#notice').textContent=`示例资源校验完成：通过 ${data.filter(r=>r.valid).length} 项，失败 ${data.filter(r=>!r.valid).length} 项。${data.some(r=>!r.valid)?'请选择失败资源查看缺失信息。':''}`;});
detail.addEventListener('click',e=>{const b=e.target.closest('[data-edit],button,[data-point],[data-version]');if(!b)return;if(b.dataset.detailTab){detailTab=b.dataset.detailTab;renderDetail();detail.querySelector('[data-detail-tab="'+detailTab+'"]').focus();return;}const r=current();if(b.closest('[data-edit]')){$('#edit-name').value=r.name;$('#edit-description').value=r.description;$('#edit').showModal();return;}if(b.dataset.version){version=b.dataset.version;point='';}if(b.dataset.pin)r.pin=r.pin===b.dataset.pin?null:b.dataset.pin;if(b.dataset.point!==undefined){point=b.dataset.point;detailTab='points';}const action=b.dataset.map;if(action==='plus')zoom=Math.min(2,zoom+.25);if(action==='minus')zoom=Math.max(.5,zoom-.25);if(action==='reset'){zoom=1;rotation=0;}if(action==='rotate-right')rotation+=90;renderDetail();});
$('#cancel-edit').addEventListener('click',()=>$('#edit').close());
detail.addEventListener('keydown',e=>{const marker=e.target.closest('g[data-point]');if(marker&&(e.key==='Enter'||e.key===' ')){e.preventDefault();marker.dispatchEvent(new MouseEvent('click',{bubbles:true}));}});
$('#edit-form').addEventListener('submit',e=>{e.preventDefault();const name=$('#edit-name').value.trim();if(!name){$('#edit-name').setCustomValidity('请输入资源名称');$('#edit-name').reportValidity();return;}current().name=name;current().description=$('#edit-description').value.trim();$('#edit').close();render();$('#notice').textContent='资源信息已更新（本次预览有效）。';});$('#edit-name').addEventListener('input',()=>$('#edit-name').setCustomValidity(''));
render();
})();
