(() => {
  const canvas=document.querySelector('process-flow-canvas');
  if(!canvas)return;
  canvas.setAttribute('variant','current');
  const root=canvas.closest('.process-editor-components'),scene=canvas.querySelector('.scene');
  const previousProperties=root.querySelector('process-node-properties');
  if(previousProperties){
    const properties=document.createElement('process-node-properties');
    properties.setAttribute('variant','workflow-human');
    previousProperties.replaceWith(properties);
  }
  const heading=root.querySelector('process-editor-header h1');
  if(heading){heading.textContent='京东单 SKU 拣放流程';document.title='京东单 SKU 拣放流程';}
  const previousLibrary=root.querySelector('process-node-library');
  if(previousLibrary&&previousLibrary.getAttribute('variant')!=='workflow'){
    const library=document.createElement('process-node-library');
    library.setAttribute('variant','workflow');
    library.setAttribute('no-flow','');
    previousLibrary.replaceWith(library);
  }
  root.querySelector('process-node-library')?.setAttribute('no-flow','');
  root.querySelectorAll('.graph-node,.loop-box').forEach(node=>node.remove());
  const assets=new URL('../../pages/process-editor/assets/',document.currentScript.src).href;
  const types={start:['start','green'],end:['end','gray'],api:['api','purple'],variable:['variable-yellow','yellow'],nav:['nav','green'],pose:['pose','green'],model:['omini','green'],human:['human','pink2'],condition:['condition-fix','blue'],loop:['loop','mint']};
  root.baseConnections=[];
  function node(id,type,title,x,y,description='',branches=[]){
    const [icon,color]=types[type],el=document.createElement('div');
    el.className='graph-node'+(branches.length?' current-condition':'');el.dataset.node=id;
    Object.assign(el.style,{left:x+'px',top:y+'px',width:'230px',height:(branches.length?52+branches.length*32:56)+'px'});
    el.innerHTML=`<span class="mini ${color}"><img src="${assets}${icon}.svg" alt=""></span><div class="node-text"><div class="graph-title"></div><div class="graph-sub"></div></div>`;
    el.querySelector('.graph-title').textContent=title;el.title=title;el.querySelector('.graph-sub').textContent=description;
    if(branches.length){
      el.style.display='block';
      const header=document.createElement('div');
      header.style.cssText='height:38px;display:flex;align-items:center;gap:10px';
      header.append(el.querySelector('.mini'),el.querySelector('.node-text'));
      header.querySelector('.graph-sub').remove();
      el.append(header);
      branches.forEach(label=>{const row=document.createElement('div');row.className='branch-row';row.textContent=label;el.append(row);});
    }
    const port=(left,top)=>{const p=document.createElement('span');p.className='port';p.style.cssText=`${left?'left':'right'}:-4px;top:${top}px`;el.append(p);};
    port(true,24);(branches.length?branches.map((_,i)=>52+i*32):[24]).forEach(y=>port(false,y));scene.append(el);return id;
  }
  const link=(a,b,p=1)=>root.baseConnections.push([a,p,b,0]);
  const standard=['IF · success','ELIF · timeout','ELIF · cancelled','ELIF · failed','ELSE','ON ERROR'];
  const check=(id,title,x,y,labels=standard)=>node(id,'condition',title,x,y,'',labels);
  const stop=(id,x,y)=>node(id,'end','Break',x,y,'退出当前循环');
  node('start','start','jd_single_sku_pick_place',0,400,'流程入口');node('get','api','GET_JD_ORDER',300,400,'GET · 获取京东订单');node('save','variable','SAVE_ORDER_TO_GLOBAL',600,400,'3 项变量赋值');node('order','loop','ORDER_LOOP',900,400,'Repeat · 订单任务循环');
  link('start','get');link('get','save');link('save','order');
  check('next','CHECK_HAS_NEXT_TASK',1200,180,['IF · 存在下一项任务','ELSE','ON ERROR']);link('order','next');
  node('assign','variable','ASSIGN_CURRENT_TASK',1500,180,'1 项变量赋值');link('next','assign');
  stop('next-break',1500,480);stop('next-error',1500,600);link('next','next-break',2);link('next','next-error',3);
  node('pick-nav','nav','NAVIGATE_TO_PICK_STATION',1800,180,'目标点位 · PICK_STATION');link('assign','pick-nav');check('pick-nav-check','CHECK_PICK_NAVIGATION',2100,180);link('pick-nav','pick-nav-check');
  node('pose','pose','PREPARE_PICK_POSE',2400,180,'工作点位 · VRMOV');link('pick-nav-check','pose');
  node('nav-human','human','PICK_NAVIGATION_HUMAN_INTERRUPT',2100,530,'120s · 拣选导航未成功');link('pick-nav-check','nav-human',2);
  check('nav-human-check','CHECK_PICK_NAVIGATION_HUMAN',2400,530,['IF · 人工处理成功','ELSE','ON ERROR']);link('nav-human','nav-human-check');link('nav-human-check','pose');stop('nav-break',2700,760);link('nav-human-check','nav-break',2);link('nav-human-check','nav-break',3);
  check('pose-check','CHECK_PICK_POSE',2700,180,['IF · success','ELSE','ON ERROR']);link('pose','pose-check');node('pick','model','PICK_SKU_VLA',3000,180,'1 个输入 · 30s 超时');link('pose-check','pick');stop('pose-break',3000,460);link('pose-check','pose-break',3);
  check('pick-check','CHECK_PICK_RESULT',3300,180);link('pick','pick-check');node('pick-human','human','PICK_HUMAN_INTERRUPT',3300,550,'120s · 抓取失败人工介入');link('pose-check','pick-human',2);link('pick-check','pick-human',2);check('pick-human-check','CHECK_PICK_HUMAN',3600,550,['IF · 人工处理成功','ELSE','ON ERROR']);link('pick-human','pick-human-check');
  check('route','ROUTE_PLACEMENT_POINT',3900,180,['IF · PLACE_1','ELIF · PLACE_2','ELIF · PLACE_3','ELIF · PLACE_4','ELIF · PLACE_5','ELSE','ON ERROR']);link('pick-check','route');link('pick-human-check','route');stop('pick-break',3900,700);link('pick-human-check','pick-break',2);link('pick-human-check','pick-break',3);
  for(let i=1;i<=5;i++){const y=(i-1)*340;node('place-nav-'+i,'nav','NAVIGATE_TO_PLACE_'+i,4200,y,'目标点位 · PLACE_'+i);check('place-check-'+i,'CHECK_PLACE_'+i+'_NAVIGATION',4500,y);link('route','place-nav-'+i,i);link('place-nav-'+i,'place-check-'+i);link('place-check-'+i,'place');link('place-check-'+i,'place-nav-human',2);stop('place-break-'+i,4800,y+160);for(let p=3;p<=6;p++)link('place-check-'+i,'place-break-'+i,p);}
  node('place','model','PLACE_SKU_VLA',5100,450,'2 个输入 · 30s 超时');node('place-nav-human','human','PLACE_NAVIGATION_HUMAN_INTERRUPT',4800,1770,'120s · 放置导航未成功');check('place-nav-human-check','CHECK_PLACE_NAVIGATION_HUMAN',5100,1770,['IF · 人工处理成功','ELSE','ON ERROR']);link('place-nav-human','place-nav-human-check');link('place-nav-human-check','place');
  check('place-result','CHECK_PLACE_RESULT',5400,450);link('place','place-result');node('place-human','human','PLACE_HUMAN_INTERRUPT',5700,850,'120s · VLA 放置未成功');link('place-result','place-human',2);check('place-human-check','CHECK_PLACE_HUMAN',6000,850,['IF · 人工处理成功','ELSE','ON ERROR']);link('place-human','place-human-check');
  check('progress','CHECK_ORDER_PROGRESS',6300,450,['IF · 还有任务','ELIF · 订单已完成','ELSE','ON ERROR']);link('place-result','progress');link('place-human-check','progress');node('continue','loop','CONTINUE_ORDER_LOOP',6600,300,'进入下一轮');link('progress','continue');link('continue','next');node('finished','variable','ORDER_FINISHED',6900,450,'2 项变量赋值');link('progress','finished',2);node('end','end','jd_single_sku_pick_place',7200,450,'End');link('finished','end');
  for(const id of ['pick-nav-check','pick-check','route','place-result','progress','place-human-check','place-nav-human-check']){const el=scene.querySelector(`[data-node="${id}"]`),count=el.querySelectorAll('.port').length-1;const b=id+'-error';stop(b,el.offsetLeft+300,el.offsetTop+1050);link(id,b,count);}
  // Keep the order wrapper separate from its entry node and its external steps.
  const entry=scene.querySelector('[data-node="order"]');
  entry.querySelector('.mini img').src=`${assets}start.svg`;
  entry.querySelector('.mini').className='mini green';
  entry.querySelector('.graph-title').textContent='循环入口';
  entry.querySelector('.graph-sub').textContent='ORDER_LOOP';
  const box=document.createElement('div');box.className='loop-box';
  box.innerHTML=`<div class="loop-title" style="font-size:14px"><img src="${assets}loop.svg" width="20" height="20" alt="">ORDER_LOOP <span style="font-weight:400;color:#78909c">订单任务循环</span></div><div class="loop-stage"></div>`;
  scene.prepend(box);
  root.loopNodeIds=new Set([...scene.querySelectorAll('.graph-node')].map(n=>n.dataset.node).filter(id=>!['start','get','save','finished','end'].includes(id)));
  const positions={start:[0,240],get:[320,240],save:[640,240],order:[1020,120],next:[1340,240],assign:[1680,240],'pick-nav':[2020,240],'pick-nav-check':[2360,240],pose:[2700,240],'pose-check':[3040,240],pick:[3380,240],'pick-check':[3720,240],route:[4400,240],
    'next-break':[1680,540],'next-error':[1680,700],'nav-human':[2360,650],'nav-human-check':[2700,650],'nav-break':[3040,900],'pose-break':[3380,560],'pick-human':[3720,650],'pick-human-check':[4060,650],'pick-break':[4400,900],
    place:[5480,240],'place-result':[5820,240],'place-human':[5820,700],'place-human-check':[6160,700],progress:[6500,240],continue:[6840,120],finished:[7260,240],end:[7580,240],
    'place-nav-human':[5140,2180],'place-nav-human-check':[5480,2180]};
  for(let i=1;i<=5;i++){positions['place-nav-'+i]=[4740,240+(i-1)*370];positions['place-check-'+i]=[5080,240+(i-1)*370];positions['place-break-'+i]=[5480,420+(i-1)*370];}
  ['pick-nav-check','pick-check','route','place-result','progress','place-human-check','place-nav-human-check'].forEach(id=>{const [x,y]=positions[id];positions[id+'-error']=[x+340,y+(id==='place-nav-human-check'?340:1100)];});
  positions['route-error']=[4740,2180];
  // Match the full reference: pick path across the top, placement fan-out
  // vertically in the middle, recovery underneath, completion on the right.
  Object.assign(positions,{
    start:[0,1050],get:[300,1120],save:[600,1190],order:[1020,150],
    next:[1160,260],assign:[1500,260],'pick-nav':[1840,260],
    'pick-nav-check':[2180,220],pose:[2520,220],'pose-check':[2860,220],
    pick:[3200,260],'pick-check':[3540,220],route:[4160,240],
    'next-break':[1500,540],'next-error':[1500,730],
    'nav-human':[2180,650],'nav-human-check':[2520,650],
    'pick-nav-check-error':[2520,930],'nav-break':[2860,930],
    'pose-break':[3200,500],'pick-human':[3540,650],
    'pick-human-check':[3880,650],'pick-break':[4220,960],
    'pick-check-error':[3880,990],'route-error':[4560,940],
    place:[5220,1040],'place-result':[5560,1000],
    'place-human':[5900,1560],'place-human-check':[6240,1510],
    'place-result-error':[5900,1400],'place-human-check-error':[6580,1790],
    'place-nav-human':[5340,1850],'place-nav-human-check':[5560,2230],
    'place-nav-human-check-error':[5900,2170],
    progress:[6580,1000],continue:[6920,1000],'progress-error':[6920,1510],
    finished:[7360,1140],end:[7700,1240]
  });
  for(let i=1;i<=5;i++){
    positions['place-nav-'+i]=[4600,180+(i-1)*410];
    positions['place-check-'+i]=[4940,140+(i-1)*440];
    positions['place-break-'+i]=[i===4?5460:5220,580+(i-1)*410];
  }
  // Continue represents the loop's next iteration, not a canvas-wide return wire.
  root.baseConnections=root.baseConnections.filter(([from,,to])=>!(from==='continue'&&to==='next'));
  stop('progress-else',6920,1320);positions['progress-else']=[6920,1320];root.loopNodeIds.add('progress-else');link('progress','progress-else',3);
  for(const id of ['pick-check','place-result']){
    const el=scene.querySelector(`[data-node="${id}"]`);
    const row=document.createElement('div');row.className='branch-row';row.textContent='ELIF · time insufficient';
    const rows=el.querySelectorAll('.branch-row');el.insertBefore(row,rows[2]);
    el.style.height='276px';el.querySelectorAll('.port').forEach(p=>p.remove());
    for(let i=0;i<8;i++){const p=document.createElement('span');p.className='port';p.style.cssText=`${i?'right':'left'}:-4px;top:${i?52+(i-1)*32:24}px`;el.append(p);}
    root.baseConnections.forEach(edge=>{if(edge[0]===id&&edge[1]>=3)edge[1]++;});
    for(let p=3;p<=6;p++)link(id,id==='pick-check'?'pick-human':'place-human',p);
  }
  // A compact entry belongs to the container; it is not another full workflow card.
  entry.style.width='56px';entry.querySelector('.node-text').style.display='none';
  positions.place=[5540,1040];positions['place-result']=[5900,1000];
  positions['place-human']=[6260,1580];positions['place-human-check']=[6600,1540];
  positions['place-result-error']=[6260,1390];positions['place-human-check-error']=[6960,1900];
  positions.progress=[6960,1000];positions.continue=[7320,1000];positions['progress-else']=[7320,1320];positions['progress-error']=[7320,1520];
  positions.finished=[7720,1140];positions.end=[8060,1240];
  positions['place-nav-human']=[5320,2360];positions['place-nav-human-check']=[5700,2360];positions['place-nav-human-check-error']=[6080,2660];
  for(let i=1;i<=5;i++)positions['place-break-'+i]=[5320,400+(i-1)*440];
  // Reference workflow.pdf: two placement routes and left-to-right recovery chains.
  const removeReferenceNode=id=>{scene.querySelector(`[data-node="${id}"]`)?.remove();delete positions[id];root.loopNodeIds.delete(id);};
  for(const id of ['next-error','pick-break','progress-else',...Array.from({length:3},(_,i)=>i+3).flatMap(i=>['place-nav-'+i,'place-check-'+i,'place-break-'+i])])removeReferenceNode(id);
  const referenceCheck=(id,labels)=>{
    const old=scene.querySelector(`[data-node="${id}"]`),title=old.querySelector('.graph-title').textContent;
    old.remove();check(id,title,0,0,labels);
  };
  const navigationCases=['IF · success','ELIF · timeout / cancelled / failed','ELSE','ON ERROR'];
  for(const id of ['pick-nav-check','place-check-1','place-check-2'])referenceCheck(id,navigationCases);
  for(const id of ['pick-check','place-result'])referenceCheck(id,['IF · success','ELIF · timeout / time insufficient / cancelled / failed','ELSE','ON ERROR']);
  referenceCheck('route',['IF · 放置点组 1 → PLACE_1','ELIF · 放置点组 2 → PLACE_2','ELSE','ON ERROR']);
  root.baseConnections=[];
  stop('pick-human-check-error',5800,670);root.loopNodeIds.add('pick-human-check-error');
  const chain=(...ids)=>ids.slice(1).forEach((id,i)=>link(ids[i],id));
  chain('start','get','save','order','next','assign','pick-nav','pick-nav-check','pose','pose-check','pick','pick-check','route');
  link('next','next-break',2);link('next','next-break',3);
  for(const p of [2,3])link('pick-nav-check','nav-human',p);
  link('pick-nav-check','pick-nav-check-error',4);chain('nav-human','nav-human-check','pose');
  for(const p of [2,3])link('nav-human-check','nav-break',p);
  link('pose-check','pick-human',2);link('pose-check','pose-break',3);
  for(const p of [2,3])link('pick-check','pick-human',p);
  link('pick-check','pick-check-error',4);chain('pick-human','pick-human-check','route');
  for(const p of [2,3])link('pick-human-check','pick-human-check-error',p);
  for(let i=1;i<=2;i++){
    link('route','place-nav-'+i,i);chain('place-nav-'+i,'place-check-'+i,'place');
    for(const p of [2,3])link('place-check-'+i,'place-nav-human',p);
    link('place-check-'+i,'place-break-'+i,4);
  }
  for(const p of [3,4])link('route','route-error',p);
  chain('place-nav-human','place-nav-human-check','place');
  for(const p of [2,3])link('place-nav-human-check','place-nav-human-check-error',p);
  chain('place','place-result','progress');
  for(const p of [2,3])link('place-result','place-human',p);
  link('place-result','place-result-error',4);chain('place-human','place-human-check','progress');
  for(const p of [2,3])link('place-human-check','place-human-check-error',p);
  link('progress','continue');for(const p of [2,3,4])link('progress','progress-error',p);
  // Completion is emitted by the loop container after its exit.
  link('order','finished');link('finished','end');
  Object.assign(positions,{
    start:[0,500],get:[340,500],save:[680,500],order:[1100,180],
    next:[1240,240],assign:[1620,240],'next-break':[1620,420],
    'pick-nav':[2000,240],'pick-nav-check':[2380,220],
    'nav-human':[2760,380],'pick-nav-check-error':[2760,610],
    'nav-human-check':[3140,320],pose:[3520,240],'nav-break':[3520,560],
    'pose-check':[3900,220],pick:[4280,240],'pose-break':[4280,480],
    'pick-check':[4660,220],'pick-human':[5040,380],'pick-human-check':[5420,300],
    'pick-check-error':[5040,620],'pick-human-check-error':[5800,670],route:[5800,220],'route-error':[6180,620],
    'place-nav-1':[6180,240],'place-nav-2':[6180,440],
    'place-check-1':[6560,220],'place-check-2':[6560,720],
    'place-break-1':[6940,400],'place-break-2':[6940,970],
    'place-nav-human':[6940,740],'place-nav-human-check':[7320,680],
    'place-nav-human-check-error':[7700,810],place:[7700,240],
    'place-result':[8080,220],'place-human':[8460,420],'place-result-error':[8460,630],
    'place-human-check':[8840,340],'place-human-check-error':[9220,670],
    progress:[9220,220],continue:[9600,220],'progress-error':[9600,440],
    finished:[10080,500],end:[10460,500]
  });
  const conditionSources={
    'pick-nav-check':'NAVIGATE_TO_PICK_STATION','nav-human-check':'PICK_NAVIGATION_HUMAN_INTERRUPT',
    'pose-check':'PREPARE_PICK_POSE','pick-check':'PICK_SKU_VLA','pick-human-check':'PICK_HUMAN_INTERRUPT',
    'place-check-1':'NAVIGATE_TO_PLACE_1','place-check-2':'NAVIGATE_TO_PLACE_2',
    'place-nav-human-check':'PLACE_NAVIGATION_HUMAN_INTERRUPT','place-result':'PLACE_SKU_VLA','place-human-check':'PLACE_HUMAN_INTERRUPT'
  };
  scene.querySelectorAll('.current-condition').forEach(card=>{
    card.classList.add('condition-cases');card.style.width='300px';
    const id=card.dataset.node,source=conditionSources[id];let caseIndex=0,totalHeight=56;
    const header=card.querySelector(':scope > div:not(.branch-row)');header.classList.add('condition-case-header');
    card.querySelectorAll('.branch-row').forEach(row=>{
      const label=row.textContent,kind=label.split(' · ')[0];row.replaceChildren();
      if(kind==='ELSE'||kind==='ON ERROR'){
        row.classList.add('condition-fallback');if(kind==='ON ERROR')row.classList.add('condition-error');
        row.textContent=kind;row.style.height='40px';totalHeight+=40;return;
      }
      const title=document.createElement('div');title.className='condition-case-label';
      const number=document.createElement('span');number.textContent=`CASE ${++caseIndex}`;
      const operator=document.createElement('span');operator.textContent=kind;title.append(number,operator);row.append(title);
      let expressions;
      if(id==='next')expressions=['当前 Loop 轮次 <= current_order.task_count'];
      else if(id==='progress')expressions=[`当前 Loop 轮次 ${caseIndex===1?'<':'=='} current_order.task_count`];
      else if(source){
        const failures=id==='pick-check'||id==='place-result'?['TimeoutError','TimeInsufficient','CancelError','failed']:['TimeoutError','CancelError','FailedError'];
        expressions=(caseIndex===1?['success']:failures).map(value=>`${source}.result == ${value}`);
      }else expressions=[label.split(' · ')[1]||label];
      expressions.forEach((expression,index)=>{
        const chip=document.createElement('div');chip.className='condition-expression';chip.title=expression;
        const text=document.createElement('span');text.textContent=expression;chip.append(text);
        if(index<expressions.length-1){const or=document.createElement('b');or.textContent='OR';chip.append(or);}
        row.append(chip);
      });
      const height=36+expressions.length*32;row.style.height=`${height}px`;totalHeight+=height;
    });
    card.style.height=`${totalHeight+2}px`;
  });
  const roundedRoute = points => {
    const clean=[];
    for(const point of points){
      const last=clean.at(-1);
      if(last&&last[0]===point[0]&&last[1]===point[1])continue;
      while(clean.length>1){
        const a=clean.at(-2),b=clean.at(-1);
        if((b[0]-a[0])*(point[1]-b[1])!==(b[1]-a[1])*(point[0]-b[0]) ||
          (b[0]-a[0])*(point[0]-b[0])+(b[1]-a[1])*(point[1]-b[1])<0)break;
        clean.pop();
      }
      clean.push(point);
    }
    let path=`M ${clean[0][0]} ${clean[0][1]}`;
    for(let i=1;i<clean.length-1;i++){
      const a=clean[i-1],b=clean[i],c=clean[i+1];
      const before=Math.hypot(b[0]-a[0],b[1]-a[1]),after=Math.hypot(c[0]-b[0],c[1]-b[1]);
      const radius=Math.min(64,before/2,after/2);
      path+=` L ${b[0]-(b[0]-a[0])*radius/before} ${b[1]-(b[1]-a[1])*radius/before}`;
      path+=` Q ${b[0]} ${b[1]} ${b[0]+(c[0]-b[0])*radius/after} ${b[1]+(c[1]-b[1])*radius/after}`;
    }
    const end=clean.at(-1);return `${path} L ${end[0]} ${end[1]}`;
  };
  root.routeWorkflowEdge=(from,to,connection=[])=>{
    if(connection[0]==='order'&&connection[2]==='finished'){
      const exit={x:box.offsetLeft+box.offsetWidth,y:box.offsetTop+box.offsetHeight-40};
      const bend=Math.max(24,(to.x-exit.x)/2);
      return `M ${exit.x} ${exit.y} C ${exit.x+bend} ${exit.y}, ${to.x-bend} ${to.y}, ${to.x} ${to.y}`;
    }
    const siblings=(root.layoutConnections||[]).filter(item=>item[2]===connection[2]);
    const lane=Math.max(0,siblings.findIndex(item=>item.every((value,index)=>value===connection[index])));
    const obstacles=[...scene.querySelectorAll('.graph-node')].filter(n=>n.dataset.node!==connection[0]&&n.dataset.node!==connection[2]).map(n=>({l:n.offsetLeft-20,r:n.offsetLeft+n.offsetWidth+20,t:n.offsetTop-20,b:n.offsetTop+n.offsetHeight+20}));
    // Spread converging curves and reject any curve that crosses another card.
    if(to.x>from.x){
      const gap=to.x-from.x;
      const bend=Math.min(gap*.8,Math.max(gap*.2,gap/2+(lane-(siblings.length-1)/2)*18));
      const clearCurve=Array.from({length:99},(_,i)=>(i+1)/100).every(t=>{
        const u=1-t,x=u*u*u*from.x+3*u*u*t*(from.x+bend)+3*u*t*t*(to.x-bend)+t*t*t*to.x;
        const y=u*u*u*from.y+3*u*u*t*from.y+3*u*t*t*to.y+t*t*t*to.y;
        return !obstacles.some(b=>x>b.l&&x<b.r&&y>b.t&&y<b.b);
      });
      if(clearCurve)return `M ${from.x} ${from.y} C ${from.x+bend} ${from.y}, ${to.x-bend} ${to.y}, ${to.x} ${to.y}`;
    }
    const origin={...from},destination={...to};
    const laneOffset=lane*12;
    from={x:from.x+32+laneOffset,y:from.y};to={x:to.x-32-laneOffset,y:to.y};
    const blocks=[...scene.querySelectorAll('.graph-node')].map(n=>({l:n.offsetLeft-18,r:n.offsetLeft+n.offsetWidth+18,t:n.offsetTop-12,b:n.offsetTop+n.offsetHeight+12}));
    const xs=[...new Set([from.x,to.x,...blocks.flatMap(b=>[b.l-18-laneOffset,b.r+18+laneOffset])])].sort((a,b)=>a-b);
    const ys=[...new Set([from.y,to.y,...blocks.flatMap(b=>[b.t-18-laneOffset,b.b+18+laneOffset])])].sort((a,b)=>a-b);
    const clear=(x,y,X,Y)=>!blocks.some(b=>x===X?x>b.l&&x<b.r&&Math.max(y,Y)>b.t&&Math.min(y,Y)<b.b:y>b.t&&y<b.b&&Math.max(x,X)>b.l&&Math.min(x,X)<b.r);
    const width=xs.length,key=(x,y)=>y*width+x,start=key(xs.indexOf(from.x),ys.indexOf(from.y)),goal=key(xs.indexOf(to.x),ys.indexOf(to.y));
    const costs=new Map([[start,0]]),prev=new Map(),open=[[0,start]],done=new Set();
    while(open.length){open.sort((a,b)=>b[0]-a[0]);const [,id]=open.pop();if(done.has(id))continue;if(id===goal)break;done.add(id);const x=id%width,y=Math.floor(id/width);
      for(const [X,Y] of [[x-1,y],[x+1,y],[x,y-1],[x,y+1]]){if(X<0||Y<0||X>=width||Y>=ys.length||!clear(xs[x],ys[y],xs[X],ys[Y]))continue;
        const next=key(X,Y),cost=costs.get(id)+Math.abs(xs[X]-xs[x])+Math.abs(ys[Y]-ys[y]);
        // Keep the port stems tangent to the route: never reverse along them.
        if(id===start && xs[X]<from.x)continue;
        if(next===goal && xs[x]>to.x)continue;
        if(cost<(costs.get(next)??Infinity)){costs.set(next,cost);prev.set(next,id);open.push([cost+Math.abs(xs[X]-to.x)+Math.abs(ys[Y]-to.y),next]);}
      }
    }
    if(!costs.has(goal))return roundedRoute([[origin.x,origin.y],[from.x,from.y],[from.x,to.y],[destination.x,destination.y]]);
    const points=[];for(let id=goal;id!==undefined;id=prev.get(id))points.push([xs[id%width],ys[Math.floor(id/width)]]);points.reverse();
    points.unshift([origin.x,origin.y]);points.push([destination.x,destination.y]);
    return roundedRoute(points);
  };
  root.alignWorkflowPorts=()=>{
    scene.querySelectorAll('.graph-node').forEach(el=>{
      const ports=[...el.querySelectorAll('.port')],rows=[...el.querySelectorAll('.branch-row')];
      ports.forEach((port,i)=>{
        const row=rows[i-1];
        const center=i>0&&row?row.offsetTop+row.offsetHeight/2:el.clientHeight/2;
        port.style.top=`${center-port.offsetHeight/2}px`;
      });
    });
  };
  root.arrangeWorkflow=()=>{
    const nodes=[...scene.querySelectorAll('.graph-node:not(.placement-ghost)')];
    const byId=new Map(nodes.map(n=>[n.dataset.node,n]));
    const edges=[...root.baseConnections,...(root.customConnections||[])].filter(e=>
      byId.has(e[0])&&byId.has(e[2])&&!(root.removedConnections||[]).some(r=>JSON.stringify(r)===JSON.stringify(e)));
    const placed=new Set();
    for(const [id,[x,y]] of Object.entries(positions)){const el=byId.get(id);if(el){Object.assign(el.style,{left:x+'px',top:y+'px'});placed.add(id);}}
    const pending=nodes.filter(n=>!placed.has(n.dataset.node));
    while(pending.length){
      let index=pending.findIndex(n=>edges.some(e=>e[2]===n.dataset.node&&placed.has(e[0])));
      if(index<0)index=0;
      const node=pending.splice(index,1)[0],id=node.dataset.node;
      const incoming=edges.find(e=>e[2]===id&&placed.has(e[0]));
      const source=incoming&&byId.get(incoming[0]);
      const targetEdge=edges.find(e=>e[0]===id&&placed.has(e[2]));
      const target=targetEdge&&byId.get(targetEdge[2]);
      const x=source?source.offsetLeft+source.offsetWidth+80:target?target.offsetLeft:node.offsetLeft;
      const y=source?source.offsetTop:target?target.offsetTop:node.offsetTop;
      // Open a column for each new node, including chains inserted on an edge.
      const boundary=target&&target.offsetLeft>=x?target.offsetLeft:x;
      const shift=Math.max(0,x+node.offsetWidth+80-boundary);
      nodes.forEach(other=>{if(placed.has(other.dataset.node)&&other!==source&&other.offsetLeft>=boundary)other.style.left=`${other.offsetLeft+shift}px`;});
      Object.assign(node.style,{left:x+'px',top:y+'px'});placed.add(id);
      if(node.dataset.loopScope==='outside')root.loopNodeIds.delete(id);
      else if(node.dataset.loopScope==='inside'||source&&root.loopNodeIds.has(source.dataset.node)||target&&root.loopNodeIds.has(target.dataset.node))root.loopNodeIds.add(id);
    }
    // Resolve collisions using actual card dimensions, not template heights.
    const occupied=[];
    nodes.sort((a,b)=>a.offsetLeft-b.offsetLeft||a.offsetTop-b.offsetTop).forEach(node=>{
      let y=node.offsetTop;
      for(;;){const hit=occupied.find(other=>node.offsetLeft<other.offsetLeft+other.offsetWidth+32&&node.offsetLeft+node.offsetWidth+32>other.offsetLeft&&y<other.offsetTop+other.offsetHeight+40&&y+node.offsetHeight+40>other.offsetTop);if(!hit)break;y=hit.offsetTop+hit.offsetHeight+40;}
      node.style.top=`${y}px`;occupied.push(node);
    });
  };
  const displayNames={start:'京东单品拣放开始',end:'京东单品拣放结束',get:'获取京东订单',save:'保存订单到全局变量',next:'检查是否还有任务',assign:'设置当前任务','pick-nav':'导航至拣选工位','pick-nav-check':'检查拣选导航结果',pose:'准备拣选位姿','pose-check':'检查拣选位姿',pick:'执行商品抓取','pick-check':'检查抓取结果','nav-human':'拣选导航人工接管','nav-human-check':'检查拣选导航人工处理结果','pick-human':'抓取人工接管','pick-human-check':'检查抓取人工处理结果',route:'选择放置点位',place:'执行商品放置','place-nav-human':'放置导航人工接管','place-nav-human-check':'检查放置导航人工处理结果','place-result':'检查放置结果','place-human':'放置人工接管','place-human-check':'检查放置人工处理结果',progress:'检查订单进度',continue:'继续订单循环',finished:'完成订单'};
  for(let i=1;i<=5;i++){displayNames['place-nav-'+i]=`导航至放置点 ${i}`;displayNames['place-check-'+i]=`检查放置点 ${i} 导航结果`;}
  scene.querySelectorAll('.graph-node').forEach(card=>{
    const title=card.querySelector('.graph-title');if(!title)return;
    const label=displayNames[card.dataset.node]||(title.textContent==='Break'?'退出循环':null);
    if(label){title.title=title.textContent;title.textContent=label;}
    const sub=card.querySelector('.graph-sub');if(sub?.textContent==='End')sub.textContent='流程结束';if(sub?.textContent==='ORDER_LOOP')sub.textContent='订单循环';
  });
  const loopTitle=box.querySelector('.loop-title');
  loopTitle.childNodes.forEach(node=>{if(node.nodeType===3)node.textContent=node.textContent.replace('ORDER_LOOP','订单循环');});
  scene.querySelectorAll('.condition-case-label span,.condition-fallback').forEach(label=>{
    label.textContent=label.textContent.replace(/^CASE (\d+)$/,'条件 $1').replace(/^ON ERROR$/,'发生错误');
  });
  root.arrangeWorkflow();
})();
