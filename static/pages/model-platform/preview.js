(() => {
 window.openDataPreview=row=>{
  const drawer=document.createElement('app-drawer');drawer.className='data-preview-drawer';drawer.setAttribute('heading','#'+row.id);
  drawer.innerHTML='<task-status-tabs variant="episode"></task-status-tabs><section data-preview-content></section>';
  document.body.append(drawer);
  const content=drawer.querySelector('[data-preview-content]');
  const segments=[['接近水槽',0,6.70],['拿起碗具',6.70,13.31],['水流冲洗',13.31,23.74],['擦拭内壁',23.74,38],['放回原位',38,52],['手臂复位',52,64.20]];
  const colors=['#7bd3a2','#f2d65c','#eaa066','#5abbb9','#9c8bcc','#59a6e6'];
  const time=n=>n.toFixed(2)+'s';
  function render(tab){
   content.querySelector('dataset-trajectory')?.stop();
   if(tab==='trajectory'){content.innerHTML='<dataset-trajectory></dataset-trajectory>';return;}
   if(tab==='annotation'){
    content.innerHTML='<workbench-media-viewer variant="dataset"></workbench-media-viewer><p class="model-note">标注结构示例</p><div class="preview-track"><span>6</span><div>'+segments.map(([name,start,end],i)=>'<button data-segment="'+i+'" style="flex:'+(end-start)+';background:'+colors[i]+'" aria-label="'+name+' '+time(start)+' 至 '+time(end)+'"></button>').join('')+'</div></div><div class="preview-track"><span>1</span><div><button data-group style="flex:1;background:#efabab" aria-label="Default 全段"></button></div></div><h3>highlevel / lowlevel 标注 <small>点击分段查看对应标注</small></h3><div class="task-data-table preview-annotations"><table><thead><tr><th>描述</th><th>开始</th><th>结束</th><th>时长</th></tr></thead><tbody><tr><td><button data-collapse aria-expanded="true">▾ Default</button></td><td>0.00s</td><td>1:04.20</td><td>1:04.20</td></tr>'+segments.map(([name,start,end],i)=>'<tr data-row="'+i+'"><td>'+(i+1)+'　'+name+'</td><td>'+time(start)+'</td><td>'+time(end)+'</td><td>'+time(end-start)+'</td></tr>').join('')+'</tbody></table></div>';
    let expanded=true;const collapse=content.querySelector('[data-collapse]');
    function expand(value){expanded=value;collapse.textContent=(value?'▾':'▸')+' Default';collapse.setAttribute('aria-expanded',value);content.querySelectorAll('[data-row]').forEach(r=>r.hidden=!value);}
    collapse.onclick=()=>expand(!expanded);
    content.querySelector('[data-group]').onclick=()=>expand(!expanded);
    content.querySelectorAll('[data-segment]').forEach(b=>b.onclick=()=>{expand(true);content.querySelectorAll('[data-row]').forEach(r=>r.classList.toggle('is-selected',r.dataset.row===b.dataset.segment));content.querySelector('[data-row="'+b.dataset.segment+'"]').scrollIntoView({block:'nearest',behavior:'smooth'});});
    return;
   }
   content.replaceChildren();
  }
  drawer.addEventListener('tab-change',e=>render(e.detail.value));
  drawer.addEventListener('drawer-close',()=>drawer.remove());render('trajectory');drawer.show();
 };
})();
