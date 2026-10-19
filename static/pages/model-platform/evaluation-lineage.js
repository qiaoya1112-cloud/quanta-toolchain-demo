(() => {
 const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 window.openEvaluationLineage=({host,row})=>{
  const list=host.firstElementChild,header=document.querySelector('[data-model-title]').closest('header');
  const old=[list.hidden,header.hidden];list.hidden=true;header.hidden=true;
  const root=document.createElement('section');root.className='eval-lineage';host.append(root);
  const groups=['数据任务','数据集','训练任务','Checkpoint','评测任务'];
  const nodes=[
   {group:0,name:'20260529_河北省石家庄元氏县马村乡使庄村富强东路19号_光轮智能_UDASv2',tag:'NORMAL',meta:'Task ID: 11092',y:70},
   {group:0,name:'20260607_山东省德州市陵城区安德街道马颊河路德州科技职业学院B10宿舍楼',tag:'NORMAL',meta:'Task ID: 11091',y:200},
   {group:0,name:'20260618_Dagger回流_擦白板抓取失败案例',tag:'DAGGER',meta:'Task ID: 12088',y:330},
   {group:1,name:'clean_whiteboard_v5 v5',meta:'标识: · 182 Episode',y:145},
   {group:1,name:'tidy_desk_v2 v2',meta:'标识: test3 · 118 Episode',y:225},
   {group:1,name:'clean_whiteboard_v3 v3',meta:'标识: test1 · 95 Episode',y:305},
   {group:2,name:'robotwin_pi05_datamil_stack_blocks_two_top10pct_cotrain',meta:'ID exp_7916',y:215},
   {group:3,name:'20260613_HouseHold_stop_32_40000',meta:'ID 7916 · Step 40000',y:225},
   {group:4,name:String(row.id)==='1001'?'Spirit v1.5 vs v1.6-alpha 基础能力横测':row.name,tag:'TEST',meta:'ID '+row.id,y:195,current:true}
  ].map(n=>({...n,x:24+n.group*340,height:n.tag?120:n.group===2?90:70}));
  const width=1720,height=470,edges=[[0,3],[1,3],[1,4],[2,5],[3,6],[4,6],[5,6],[6,7],[7,8]];
  root.innerHTML=`<task-page-header title="评测任务血缘" back></task-page-header><form class="eval-lineage-locate"><label for="lineage-type">定位节点</label><form-select id="lineage-type" label="节点类型" value="4">${groups.map((g,i)=>`<option value="${i}" ${i===4?'selected':''}>${g}</option>`).join('')}</form-select><input aria-label="节点名称" value="${esc(nodes[8].name)}" list="lineage-names"><datalist id="lineage-names"></datalist><span role="status"></span></form><div class="eval-lineage-layout"><div class="eval-lineage-canvas" tabindex="0" aria-label="血缘画布"><details class="eval-lineage-legend" open><summary>图例</summary><div>节点状态： <span class="current-key">当前查看</span><span>关联节点</span></div></details><div class="eval-lineage-world" style="width:${width}px;height:${height}px"><svg width="${width}" height="${height}" aria-hidden="true">${edges.map(([a,b])=>{const p=nodes[a],q=nodes[b],sx=p.x+310,sy=p.y+p.height/2,tx=q.x,ty=q.y+q.height/2;return `<path d="M${sx} ${sy} C${(sx+tx)/2} ${sy} ${(sx+tx)/2} ${ty} ${tx} ${ty}"/>`;}).join('')}</svg>${groups.map((g,i)=>`<h3 class="eval-lineage-column" style="left:${24+i*340}px">${g}（${nodes.filter(n=>n.group===i).length}）</h3>`).join('')}${nodes.map((n,i)=>`<button class="eval-lineage-node ${n.current?'is-current':''} ${n.tag==='DAGGER'?'is-dagger':''}" data-node="${i}" style="left:${n.x}px;top:${n.y}px;height:${n.height}px">${n.current?'<span class="eval-lineage-current">当前</span>':''}${n.tag?`<span class="eval-lineage-tag tag-${n.tag.toLowerCase()}">${n.tag}</span>`:''}<strong>${esc(n.name)}</strong><small>${esc(n.meta)}</small></button>`).join('')}</div><div class="eval-lineage-tools"><button data-zoom="out" aria-label="缩小">−</button><output>100%</output><button data-zoom="in" aria-label="放大">＋</button><button data-fit>适应</button></div><p class="eval-lineage-hint">拖动空白区域移动 · 滚轮平移 · Ctrl + 滚轮缩放</p></div><aside class="eval-lineage-inspector" aria-label="节点详情" hidden></aside></div>`;
  const canvas=root.querySelector('.eval-lineage-canvas'),world=root.querySelector('.eval-lineage-world'),inspector=root.querySelector('aside'),form=root.querySelector('form'),type=form.querySelector('form-select'),input=form.querySelector('input');
  const topbar=document.createElement('div');topbar.className='eval-lineage-topbar';root.prepend(topbar);topbar.append(root.querySelector('task-page-header'),form);
  const icon=(name)=>`<img src="../process-editor/assets/${name}.svg" alt="">`;
  const toolbar=document.createElement('div');toolbar.className='eval-lineage-toolbar';
  toolbar.innerHTML=[['select','选择','cursor'],['hand','拖拽平移','hand-tool'],['undo','撤销视图移动','undo'],['redo','重做视图移动','redo']].map(([action,label,img])=>`<button data-tool="${action}" title="${label}" aria-label="${label}">${icon(img)}</button>`).join('')+'<span></span><button data-tool="map" title="显示或隐藏缩略图" aria-label="显示或隐藏缩略图"><svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="14" rx="2"/><path d="M10 5v14"/></svg></button><button data-tool="fit" title="适应画布" aria-label="适应画布"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="6" height="5" rx="1"/><rect x="15" y="3" width="6" height="5" rx="1"/><rect x="15" y="16" width="6" height="5" rx="1"/><path d="M6 8v10h9M9 5h6"/></svg></button>';
  canvas.append(toolbar);root.querySelector('.eval-lineage-hint').remove();root.querySelector('[data-fit]').remove();
  root.querySelector('[data-zoom="out"]').innerHTML=icon('zoom-minus');root.querySelector('[data-zoom="in"]').innerHTML=icon('zoom-plus');
  const mini=document.createElement('button');mini.className='eval-lineage-minimap';mini.title='点击缩略图定位';mini.setAttribute('aria-label','血缘缩略图，点击定位');
  mini.innerHTML=`<svg viewBox="0 0 ${width} ${height}">${nodes.map(n=>`<rect x="${n.x}" y="${n.y}" width="310" height="${n.height}" rx="8" fill="#cbd3db"/>`).join('')}<rect data-viewport fill="#009bb70a" stroke="#91a9bc" stroke-width="10"/></svg>`;canvas.append(mini);
  let scale=1,x=0,y=0,drag,mode='hand',history=[],future=[];
  const snapshot=()=>({x,y,scale});
  const historyButtons=()=>{toolbar.querySelector('[data-tool="undo"]').disabled=!history.length;toolbar.querySelector('[data-tool="redo"]').disabled=!future.length;};
  const remember=()=>{history.push(snapshot());if(history.length>50)history.shift();future=[];historyButtons();};
  toolbar.querySelector('[data-tool="hand"]').classList.add('active');historyButtons();
  const draw=()=>{world.style.transform=`translate(${x}px,${y}px) scale(${scale})`;root.querySelector('output').textContent=Math.round(scale*100)+'%';
   const vp=mini.querySelector('[data-viewport]');vp.setAttribute('x',-x/scale);vp.setAttribute('y',-y/scale);vp.setAttribute('width',canvas.clientWidth/scale);vp.setAttribute('height',canvas.clientHeight/scale);};
  const fit=()=>{scale=Math.max(.2,Math.min(1,(canvas.clientWidth-48)/width,(canvas.clientHeight-180)/height));x=(canvas.clientWidth-width*scale)/2;y=Math.max(100,(canvas.clientHeight-height*scale)/2);draw();};
  const select=index=>{
   const n=nodes[index];inspector.hidden=false;root.querySelectorAll('[data-node]').forEach(b=>{b.classList.toggle('is-selected',+b.dataset.node===index);b.setAttribute('aria-pressed',String(+b.dataset.node===index));});
   inspector.innerHTML=`<header><span class="eval-lineage-panel-icon"><img src="../process-editor/assets/condition.svg" alt=""></span><div class="eval-lineage-panel-title"><strong title="${esc(n.name)}">${esc(n.name)}</strong><small>${groups[n.group]}</small></div><div class="eval-lineage-panel-actions"><button data-focus title="定位节点" aria-label="定位节点"><svg viewBox="0 0 24 24"><path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m8 0h3a2 2 0 0 0 2-2v-3"/><circle cx="12" cy="12" r="3"/></svg></button><button data-close title="关闭节点详情" aria-label="关闭节点详情"><svg viewBox="0 0 24 24"><path d="m5 5 14 14M19 5 5 19"/></svg></button></div></header><section><h3>基础信息</h3><dl>${[['名称',n.name],['类型',groups[n.group]],['节点信息',n.meta],...(n.current?[['所属项目',row.project],['发布状态',row.status]]:[])].map(([k,v])=>`<div><dt>${k}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl></section>`;
   inspector.querySelector('[data-focus]').onclick=()=>{x=(canvas.clientWidth-310*scale)/2-n.x*scale;y=(canvas.clientHeight-n.height*scale)/2-n.y*scale;draw();};
   inspector.querySelector('[data-close]').onclick=()=>{inspector.hidden=true;root.querySelectorAll('[data-node]').forEach(b=>{b.classList.remove('is-selected');b.setAttribute('aria-pressed','false');});fit();};
   requestAnimationFrame(()=>{x=(canvas.clientWidth-310*scale)/2-n.x*scale;y=(canvas.clientHeight-n.height*scale)/2-n.y*scale;draw();});
  };
  const suggestions=()=>{form.querySelector('datalist').innerHTML=nodes.filter(n=>n.group===+type.value).map(n=>`<option value="${esc(n.name)}"></option>`).join('');};
  type.onchange=()=>{input.value='';suggestions();};suggestions();
  const locate=e=>{e.preventDefault();const query=input.value.trim().toLowerCase(),index=nodes.findIndex(n=>n.group===+type.value&&query&&(n.name.toLowerCase().includes(query)||n.meta.toLowerCase().includes(query)));form.querySelector('[role=status]').textContent=index<0?'未找到匹配节点':'';if(index>=0)select(index);};
  form.onsubmit=locate;input.onchange=locate;
  const lineageIcon='<svg viewBox="0 0 24 24"><circle cx="6" cy="18" r="3"/><circle cx="18" cy="5" r="3"/><path d="M6 15V3m3 15c6 0 9-4 9-10"/></svg>';
  const detailIcon='<svg viewBox="0 0 24 24"><path d="M6 18 18 6M7 6h11v11"/></svg>';
  const showRelations=index=>{
   const related=new Set([index]);
   const trace=(start,reverse)=>{const seen=new Set([start]),queue=[start];while(queue.length){const current=queue.shift();edges.forEach(([a,b])=>{const from=reverse?b:a,to=reverse?a:b;if(from===current&&!seen.has(to)){seen.add(to);related.add(to);queue.push(to);}});}};
   trace(index,false);trace(index,true);
   root.querySelectorAll('[data-node]').forEach(b=>{b.classList.toggle('is-relation-focus',+b.dataset.node===index);b.closest('.eval-lineage-node-wrap').classList.toggle('is-unrelated',!related.has(+b.dataset.node));});
   world.querySelectorAll(':scope > svg > path').forEach((p,i)=>{const [a,b]=edges[i];p.classList.toggle('is-related',related.has(a)&&related.has(b));p.classList.toggle('is-unrelated',!related.has(a)||!related.has(b));});
   type.value=String(nodes[index].group);input.value=nodes[index].name;suggestions();
  };
  root.querySelectorAll('[data-node]').forEach(b=>{
   const index=+b.dataset.node,wrap=document.createElement('div');wrap.className='eval-lineage-node-wrap';wrap.style.cssText=b.style.cssText;wrap.style.width='310px';b.before(wrap);wrap.append(b);b.style.left='0';b.style.top='0';
   const actions=document.createElement('div');actions.className='eval-lineage-node-actions';
   actions.innerHTML=`<button data-relation aria-label="查看血缘关系图" data-tooltip="查看血缘关系图">${lineageIcon}</button><button data-detail aria-label="查看${groups[nodes[index].group]}详情" data-tooltip="查看${groups[nodes[index].group]}详情">${detailIcon}</button>`;
   wrap.append(actions);b.onclick=()=>select(index);
   actions.querySelector('[data-relation]').onclick=e=>{e.stopPropagation();showRelations(index);};
   actions.querySelector('[data-detail]').onclick=e=>{e.stopPropagation();select(index);};
  });
  const zoom=(next,cx=canvas.clientWidth/2,cy=canvas.clientHeight/2)=>{next=Math.max(.2,Math.min(2,next));const ratio=next/scale;x=cx-(cx-x)*ratio;y=cy-(cy-y)*ratio;scale=next;draw();};
  root.querySelectorAll('[data-zoom]').forEach(b=>b.onclick=()=>{remember();zoom(scale+(b.dataset.zoom==='in'?.1:-.1));});
  toolbar.onclick=e=>{const b=e.target.closest('[data-tool]');if(!b)return;const a=b.dataset.tool;
   if(a==='select'||a==='hand'){mode=a;canvas.style.cursor=a==='hand'?'grab':'default';toolbar.querySelectorAll('[data-tool="select"],[data-tool="hand"]').forEach(t=>{t.classList.toggle('active',t===b);t.setAttribute('aria-pressed',String(t===b));});}
   else if(a==='map'){mini.hidden=!mini.hidden;b.setAttribute('aria-pressed',String(!mini.hidden));}
   else if(a==='fit'){remember();fit();}
   else{const from=a==='undo'?history:future,to=a==='undo'?future:history;if(from.length){to.push(snapshot());({x,y,scale}=from.pop());draw();historyButtons();}}
  };
  mini.onclick=e=>{const r=mini.querySelector('svg').getBoundingClientRect();remember();x=canvas.clientWidth/2-(e.clientX-r.left)/r.width*width*scale;y=canvas.clientHeight/2-(e.clientY-r.top)/r.height*height*scale;draw();};
  canvas.onpointerdown=e=>{if(mode!=='hand'||e.button||e.target.closest('button,text-button,details'))return;remember();drag={px:e.clientX,py:e.clientY,x,y};canvas.setPointerCapture(e.pointerId);};
  canvas.onpointermove=e=>{if(drag){x=drag.x+e.clientX-drag.px;y=drag.y+e.clientY-drag.py;draw();}};
  canvas.onpointerup=canvas.onpointercancel=()=>drag=null;
  canvas.addEventListener('wheel',e=>{e.preventDefault();if(e.ctrlKey||e.metaKey){const r=canvas.getBoundingClientRect();zoom(scale*Math.exp(-e.deltaY*.002),e.clientX-r.left,e.clientY-r.top);}else{x-=e.deltaX;y-=e.deltaY;draw();}},{passive:false});
  canvas.onkeydown=e=>{if(e.target!==canvas)return;const d={ArrowLeft:[30,0],ArrowRight:[-30,0],ArrowUp:[0,30],ArrowDown:[0,-30]}[e.key];if(d){e.preventDefault();x+=d[0];y+=d[1];draw();}};
  const observer=new ResizeObserver(()=>fit());observer.observe(canvas);
  root.querySelector('task-page-header').addEventListener('header-back',()=>{observer.disconnect();root.remove();list.hidden=old[0];header.hidden=old[1];});
  requestAnimationFrame(fit);
 };
})();
