(() => {
 const image=new URL('../../assets/maps/point-floorplan.png',document.currentScript.src).href;
 const points=[['P-01',180,140,0],['P-02',310,200,90],['P-03',250,290,180],['DOCK',120,320,270],['INS-01',380,130,45],['P-04',420,240,90],['P-05',480,390,180],['INS-02',350,460,0],['WAIT-01',200,420,270],['DOCK-02',540,310,45]];
 const labelMeasure=document.createElement('canvas').getContext('2d');
 const pointLabel=name=>{
  labelMeasure.font='700 20px "PingFang SC", "Microsoft YaHei", sans-serif';
  const width=Math.ceil(labelMeasure.measureText(name).width)+24;
  const text=name.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  return `<rect x="${-width/2}" y="-59" width="${width}" height="38" rx="8" fill="#0095b6"/><text x="0" y="-40" text-anchor="middle" dominant-baseline="central" fill="white" style="font:700 20px 'PingFang SC','Microsoft YaHei',sans-serif">${text}</text>`;
 };
 window.resourceMapPoints=points;
 window.resourceMapOverview=(zoom=1)=>`<div class="resource-map-overview" aria-label="地图缩略图"><img src="${image}" alt="地图缩略图"><span style="width:${Math.min(64,64/zoom)}px;height:${Math.min(66,66/zoom)}px"></span></div><div class="resource-map-scale"><span>${Number((10/zoom).toFixed(1))} m</span><i></i></div>`;
 window.resourceMapPreview=(selected='0')=>`<svg class="map-drawing" viewBox="0 0 1000 620" role="img" aria-label="地图与点位"><image href="${image}" width="1000" height="620" preserveAspectRatio="xMidYMid meet"/>${points.map(([name,x,y,heading],i)=>`<g data-point="${i}" role="button" tabindex="0" aria-label="选择 ${name}" aria-pressed="${String(i)===String(selected)}" transform="translate(${x+170} ${y})"><g class="map-marker-artwork">${String(i)===String(selected)?'<circle r="23" fill="#0095b614" stroke="#0095b6"/>':''}<circle r="9" fill="#0095b6" stroke="white" stroke-width="2"/><path class="map-point-direction" data-heading="${heading}" transform="rotate(${-heading})" d="M13-6 23 0 13 6Z" fill="#0095b6" stroke="white" stroke-width="1.5" stroke-linejoin="round"/>${String(i)===String(selected)?`<g class="map-point-label">${pointLabel(name)}</g>`:''}</g></g>`).join('')}<g transform="translate(500 280)" aria-label="机器人位置"><g class="map-marker-artwork"><circle r="31" fill="#d9f0f5"/><circle r="18" fill="white" stroke="#0095b6" stroke-width="3"/><path d="M0-16 10 14 0 8-10 14Z" fill="#0095b6"/></g></g></svg>`;
 const previews=new Map();
 function mountPreviews(){
  for(const [svg,dispose] of previews)if(!svg.isConnected){dispose();previews.delete(svg);}
  document.querySelectorAll('.map-drawing').forEach(svg=>{
   if(previews.has(svg))return;
   let frame=0;
   const update=()=>{
    const matrix=svg.getScreenCTM();if(!matrix)return;
    const scale=Math.hypot(matrix.a,matrix.b);if(!scale)return;
    const angle=Math.atan2(matrix.b,matrix.a)*180/Math.PI;
    const reference=svg.closest('.resource-detail')?.querySelector('.point-row .version-select');
    const fontSize=Math.max(1,(reference?parseFloat(getComputedStyle(reference).fontSize):14)-2)/0.7;
    svg.querySelectorAll('.map-point-label > text').forEach(text=>{
     text.style.fontSize=`${fontSize}px`;
     const width=Math.ceil(text.getComputedTextLength())+24;
     const background=text.parentElement.querySelector(':scope > rect');
     background.setAttribute('x',-width/2);background.setAttribute('width',width);
    });
    svg.querySelectorAll('.map-marker-artwork').forEach(art=>art.setAttribute('transform',`rotate(${-angle}) scale(${0.7/scale})`));
    svg.querySelectorAll('.map-point-direction').forEach(arrow=>arrow.setAttribute('transform',`rotate(${angle-Number(arrow.dataset.heading)})`));
    const selected=svg.querySelector('[data-point][aria-pressed="true"]');
    if(selected&&svg.lastElementChild!==selected)svg.append(selected);
    const label=selected?.querySelector('.map-point-label');
    if(label){
     const obstacles=[...svg.querySelectorAll('[data-point], [aria-label="机器人位置"]')].filter(marker=>marker!==selected).map(marker=>marker.querySelector('.map-marker-artwork').getBoundingClientRect());
     let best=null;
     for(const [x,y] of [[0,0],[0,80],[100,40],[-100,40],[0,-40],[0,120]]){
      label.setAttribute('transform',`translate(${x} ${y})`);
      const rect=label.getBoundingClientRect();
      const overlap=obstacles.reduce((sum,b)=>sum+Math.max(0,Math.min(rect.right+5,b.right)-Math.max(rect.left-5,b.left))*Math.max(0,Math.min(rect.bottom+5,b.bottom)-Math.max(rect.top-5,b.top)),0);
      if(!best||overlap<best.overlap)best={x,y,overlap};
      if(!overlap)break;
     }
     label.setAttribute('transform',`translate(${best.x} ${best.y})`);
    }
   };
   const resize=new ResizeObserver(update);resize.observe(svg);
   const changes=new MutationObserver(update);changes.observe(svg,{attributes:true,attributeFilter:['style','transform']});
   const animate=()=>{update();frame=requestAnimationFrame(animate);};
   const start=event=>{if(event.target===svg){cancelAnimationFrame(frame);animate();}};
   const finish=()=>{cancelAnimationFrame(frame);update();};
   svg.addEventListener('transitionrun',start);svg.addEventListener('transitionend',finish);svg.addEventListener('transitioncancel',finish);
   previews.set(svg,()=>{resize.disconnect();changes.disconnect();cancelAnimationFrame(frame);});update();
  });
 }
 const observe=()=>{new MutationObserver(mountPreviews).observe(document.body,{childList:true,subtree:true});mountPreviews();};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',observe,{once:true});else observe();
})();
