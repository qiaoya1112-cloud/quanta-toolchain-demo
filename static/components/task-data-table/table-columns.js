/* Shared column sizing for business tables, independent of pagination. */
(() => {
  const selector='task-data-table table,.assignment-table,.todo-table';
  const canvas=document.createElement('canvas'),context=canvas.getContext('2d');
  context.font='400 14px Inter, "PingFang SC", sans-serif';
  const measure=text=>Math.ceil(context.measureText(text.trim()).width);
  const states=new Map();
  function configure(table){
    const heads=[...table.querySelectorAll('thead th')];
    if(!heads.length)return;
    const rows=[...table.querySelectorAll('tbody tr')].filter(row=>row.cells.length===heads.length);
    const columns=heads.map((head,index)=>{
      const label=head.textContent.trim(),cells=rows.map(row=>row.cells[index]);
      const header=measure(label)+32;
      let width=100,flex=0,max=Infinity;
      if(index===heads.length-1&&/操作/.test(label)){
        width=Math.max(64,header,...cells.map(cell=>{
          const buttons=[...cell.querySelectorAll('button,a.task-data-table__data-link')].filter(button=>!button.closest('[popover]'));
          return 32+Math.max(0,buttons.length-1)*12+buttons.reduce((sum,button)=>sum+measure(button.textContent)+(button.querySelector('svg,img')?18:0),0);
        }));
      }else if(head.querySelector('input[type=checkbox]'))width=48;
      else if(label==='序号'||label==='开关')width=64;
      else if(label.includes('优先级'))width=label==='优先级'?80:180;
      else if(label.startsWith('视频区域'))width=588;
      else if(label==='序列号')width=180;
      else if(label.includes('进度'))width=table.matches('.assignment-table')?292:180;
      else if(/时间|日期/.test(label))width=180;
      else if(/ID|标识/i.test(label))width=Math.min(320,Math.max(120,header,...cells.map(cell=>{const content=cell.querySelector("code")||cell;const style=getComputedStyle(content);context.font=style.fontWeight+" "+style.fontSize+" "+style.fontFamily;const width=measure(content.textContent)+32;context.font='400 14px Inter, "PingFang SC", sans-serif';return width;})));
      else if(label==='算子'){width=260;flex=1;max=320;}
      else if(/描述|说明|数据范围/.test(label)){width=240;flex=2;}
      else if(/处理流程/.test(label)&&table.closest('[variant="task-management"]')){width=500;flex=1;}
      else if(/名称|文字|流程|节点|所属项目/.test(label)){width=180;flex=1;max=Infinity;}
      else if(cells.some(cell=>cell.querySelector('.table-person-tags'))){
        width=Math.max(header,...cells.map(cell=>{
          const tags=[...cell.querySelectorAll('.table-person-tag')];
          if(!tags.length)return measure(cell.textContent)+32;
          cell.querySelector('.table-person-tags')?.style.setProperty('grid-template-columns',`repeat(${Math.min(5,tags.length)},max-content)`);
          const tracks=Array(Math.min(5,tags.length)).fill(0);
          tags.forEach((tag,i)=>{
            const style=getComputedStyle(tag);
            context.font=style.font || `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
            tracks[i%5]=Math.max(tracks[i%5],measure(tag.textContent)+parseFloat(style.paddingLeft)+parseFloat(style.paddingRight));
          });
          context.font='400 14px Inter, "PingFang SC", sans-serif';
          return 32+tracks.reduce((sum,value)=>sum+value,0)+(tracks.length-1)*6;
        }));
      }
      else if(/Tag|状态|标签|性质|轮次|处理人|创建人/.test(label)){
        width=Math.max(80,header,...cells.map(cell=>{
          const tags=[...cell.querySelectorAll('.table-outline-tag,.table-source-tag,.table-person-tag')];
          return tags.length?Math.max(...tags.map(tag=>measure(tag.textContent)+46)):measure(cell.textContent)+48;
        }));
      }else width=Math.max(100,header);
      if(table.closest('[variant="task-records"]')){
        // Keep the final status and action columns together on wide screens.
        // The generic "节点" rule above is flexible, which otherwise pours all
        // spare desktop width into this column and leaves a large visual gap.
        if(label==='当前节点'){width=140;flex=0;max=Infinity;}
        // Let the visual content consume spare desktop width so the table still
        // reaches the right edge without stretching the compact status columns.
        if(label.startsWith('视频区域')){width=588;flex=1;max=Infinity;}
        if(label==='序列号'){width=Math.max(header,...cells.map(cell=>measure(cell.textContent)+32));flex=0;}
      }
      if(table.closest('[variant="workbench-pool"]')){
        // Spread spare width across all six columns instead of only flow/node.
        const poolWidths=[260,160,140,140,140,160];
        width=poolWidths[index]||140;flex=width;max=Infinity;
      }
      const configuredWidth=Number((table.dataset.columnWidths||'').split(',')[index]);
      if(Number.isFinite(configuredWidth)&&configuredWidth>0){width=configuredWidth;flex=label.startsWith('视频区域')?1:0;max=Infinity;}
      return {width:Math.ceil(width),flex,max};
    });
    states.get(table)?.observer.disconnect();
    const viewport=table.parentElement;
    const apply=()=>{
      if(!table.isConnected)return;
      const widths=columns.map(c=>c.width);
      let remaining=Math.max(0,viewport.clientWidth-widths.reduce((a,b)=>a+b,0));
      let eligible=columns.map((c,i)=>i).filter(i=>columns[i].flex);
      while(remaining>0.5&&eligible.length){
        const weight=eligible.reduce((n,i)=>n+columns[i].flex,0);let used=0;
        eligible.forEach(i=>{const add=Math.min(remaining*columns[i].flex/weight,columns[i].max-widths[i]);widths[i]+=add;used+=add;});
        remaining-=used;eligible=eligible.filter(i=>widths[i]<columns[i].max-0.5);if(!used)break;
      }
      table.style.setProperty('table-layout','fixed','important');
      const total=widths.reduce((a,b)=>a+b,0);
      table.closest('.task-data-table--records')?.classList.toggle('is-horizontally-scrollable',total>viewport.clientWidth+1);
      table.style.setProperty('width',total+'px','important');table.style.setProperty('min-width',total+'px','important');
      const cols=[...table.querySelectorAll('col')];
      widths.forEach((width,index)=>{
        cols[index]?.style.setProperty('width',width+'px','important');
        [heads[index],...rows.map(row=>row.cells[index])].forEach(cell=>{
          for(const prop of ['width','min-width','max-width'])cell.style.setProperty(prop,width+'px','important');
          cell.style.boxSizing='border-box';
          if(columns[index].flex||/ID|标识/i.test(heads[index].textContent)){cell.style.whiteSpace='normal';cell.style.overflowWrap='anywhere';}
          if(index===heads.length-1){cell.style.whiteSpace='nowrap';cell.querySelectorAll('button,a.task-data-table__data-link').forEach((button,i)=>{if(!button.closest('[popover]'))button.style.marginLeft=i?'12px':'0';});
            if(cell.querySelector('.assignment-table-actions'))cell.querySelectorAll('button,a.task-data-table__data-link').forEach(button=>button.style.marginLeft='0');
          }
          if(getComputedStyle(cell).position==='sticky'&&getComputedStyle(cell).left!=='auto')cell.style.left=widths.slice(0,index).reduce((a,b)=>a+b,0)+'px';
        });
      });
      table.dispatchEvent(new CustomEvent('column-widths-change',{bubbles:true,detail:heads.map((head,index)=>({label:head.textContent.trim(),minimum:columns[index].width,width:Math.round(head.getBoundingClientRect().width),flex:columns[index].flex,max:Number.isFinite(columns[index].max)?columns[index].max:null}))}));
    };
    const observer=new ResizeObserver(apply);observer.observe(viewport);states.set(table,{observer});apply();
  }
  let queued=false;
  const scan=()=>{queued=false;for(const [table,state] of states)if(!table.isConnected){state.observer.disconnect();states.delete(table);}document.querySelectorAll(selector).forEach(configure);};
  const schedule=()=>{if(!queued){queued=true;requestAnimationFrame(scan);}};
  new MutationObserver(records=>{if(records.some(r=>[...r.addedNodes,...r.removedNodes].some(node=>node.nodeType===1&&(node.matches?.('table,tbody,tr')||node.querySelector?.(selector)))))schedule();}).observe(document.documentElement,{childList:true,subtree:true});
  schedule();document.fonts?.ready.then(schedule);
})();
