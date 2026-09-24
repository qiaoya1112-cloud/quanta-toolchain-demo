(()=>{
  // Values restored from local drafts must be rendered as text.
  const escapeText=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  function applyWorkbenchTheme(theme,persist){
    const resolved=['dark','blue','light'].includes(theme)?theme:'dark';
    const light=resolved==='light',preview=document.body.classList.contains('component-preview');
    document.documentElement.dataset.workbenchTheme=resolved;
    document.documentElement.dataset.theme=light?'light':'dark';
    [document.documentElement,document.body].forEach(el=>{el.classList.toggle('theme-light',light);el.classList.toggle('component-dark',!light&&preview);});
    document.body.classList.remove('theme-pending');
    document.querySelectorAll('.workbench-theme-tabs [data-theme],timeline-controls [data-theme]').forEach(button=>{const active=button.dataset.theme===resolved;button.classList.toggle('is-active',active);button.setAttribute('aria-pressed',String(active));});
    if(persist)try{localStorage.setItem(preview?'workbench-component-theme':'workbench-theme',resolved);}catch(_){}
  }
  const splitLaneColors=[
    '#8ECCE4','#EAAC90','#AACB90','#BDA0D8','#E9CD81',
    '#86C7B3','#DC96AE','#9AACDD','#CCBC94','#A8D4CC',
    '#DBA197','#A7CFE9','#BED080','#D5A5CC','#E6BF90',
    '#95BFA7','#A7A0D0','#DFD8A2','#8DC6CD','#D1A0BB',
    '#A6BC92','#E3B3B5','#97A6C7','#C9B7A3','#B9E1AA',
    '#D0B7E5','#E3AE7A','#A4D5BB','#E0CBB2','#BDC2E4'
  ];
  class SplitLanePalette extends HTMLElement{
    connectedCallback(){
      if(this.childElementCount)return;
      this.classList.add('split-lane-palette');
      splitLaneColors.forEach((color,index)=>{const item=document.createElement('div'),swatch=document.createElement('span'),label=document.createElement('code');item.className='segment-color-palette__item';swatch.style.backgroundColor=color;label.textContent=`${String(index+1).padStart(2,'0')} · ${color}`;item.append(swatch,label);this.append(item);});
    }
  }
  if(!customElements.get('split-lane-palette'))customElements.define('split-lane-palette',SplitLanePalette);
  const assets=new URL("./assets/",document.currentScript?.src||location.href).href;
  const segments=[['15','#42a8d2'],['5.5','#ff9559'],['4.6','#9850d7'],['4.2','#48c98a'],['8.5','#8fd04c'],['6.5','#d7a23b'],['4.3','#3d8fd8'],['8.5','#4c63df'],['8.2','#42bd7d'],['8.7','#4eabe0'],['4.8','#dd8b43'],['4.4','#45c97b'],['6.3','#db405f'],['4','#cf3ba8']];
  const tools=[['figma-2x.svg','倍速',' is-2x'],['figma-plus.svg','添加',''],['figma-plus-arrow.svg','添加并前进',''],['figma-forward.svg','仅前进',''],['figma-trash.svg','清空',''],['figma-forward-alt.svg','拖动',''],['figma-scissors-rotate.svg','分割',' is-rotate-neg'],['figma-scissors.svg','父级分割',''],['figma-merge.svg','合并',''],['figma-merge-up.svg','向上合并',''],['figma-merge-down.svg','向下合并',' is-rotate-180'],['figma-keyboard.svg','快捷键',''],['figma-settings.svg','设置','']];
  const macShortcutItems=[['切分','J'],['拖动模式','⌃ + E'],['分割','⌃ + X'],['多选','⌥ + 点击'],['合并','↵'],['向上合并','⌘ + ←'],['向下合并','⌘ + →'],['上一段','⌘ + ↑'],['下一段','⌘ + ↓'],['删除','⌘ + ⌫'],['无法标注','⌘ + /'],['退出','Esc'],['提交标注','↵ + S'],['添加并前进','⌃ + S'],['仅前进','⌃ + D'],['标记首帧','⌃ + Q'],['标记尾帧','⌃ + W'],['播放/暂停','空格'],['调整时间范围','← →'],['撤销','⌘ + Z'],['重做','⌘ + ⇧ + Z']];
  const windowsShortcutItems=[['切分','J'],['拖动模式','Alt + E'],['分割','Alt + X'],['多选','Ctrl + 点击'],['合并','Enter'],['向上合并','Alt + ←'],['向下合并','Alt + →'],['上一段','Ctrl + ↑'],['下一段','Ctrl + ↓'],['删除','Ctrl + Backspace'],['无法标注','Ctrl + /'],['退出','Esc'],['提交标注','Enter + S'],['添加并前进','Alt + S'],['仅前进','Alt + D'],['标记首帧','Alt + Q'],['标记尾帧','Alt + W'],['播放/暂停','Space'],['调整时间范围','← →'],['撤销','Ctrl + Z'],['重做','Ctrl + Shift + Z']];
  macShortcutItems.splice(3,0,['父级分割','⌃ + ⇧ + X']);
  windowsShortcutItems.splice(3,0,['父级分割','Alt + Shift + X']);
  const shortcutItems=/Mac|iPhone|iPad|iPod/i.test(navigator.platform||navigator.userAgent)?macShortcutItems:windowsShortcutItems;

  class WorkbenchEmptyState extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      const variant=this.getAttribute('variant')||'list';
      const paths={media:'<rect x="8" y="11" width="48" height="36" rx="6"/><path d="m27 22 14 7-14 8Z"/><path d="M22 54h20"/>',editor:'<rect x="12" y="9" width="40" height="46" rx="6"/><path d="M22 22h20M22 31h14M22 40h9"/>',list:'<path d="M10 29 18 13h28l8 16v20a5 5 0 0 1-5 5H15a5 5 0 0 1-5-5Z"/><path d="M10 30h13l4 7h10l4-7h13M24 21h16"/>'};
      this.innerHTML=`<div class="workbench-empty-state" role="status"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[variant]||paths.list}</svg><span>暂无信息</span></div>`;
    }
  }
  customElements.define('workbench-empty-state',WorkbenchEmptyState);

  class TimelineTimeScale extends HTMLElement{
    connectedCallback(){if(this.dataset.rendered)return;this.dataset.rendered="true";this.innerHTML=`<div class="segmented-timeline__ruler">${['00:00','00:10','00:20','00:30','00:40','00:50','01:00','01:10'].map((time,index)=>`<span style="left:${index===7?100:index*14.28}%">${time}</span>`).join('')}</div>`;}
  }

  class TimelineRangeSelector extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered="true";
      this._marked=this.getAttribute('variant')==='marked';
      this._start=this._marked?17.8:0;
      this._end=this._marked?33.7:14.28;
      this._snapPoints=[];
      this.innerHTML=`<div class="segmented-timeline__range${this._marked?' segmented-timeline__range--marked':''}"><span class="segmented-timeline__range-label is-start">00:00s</span><span class="segmented-timeline__range-label is-end">00:10s</span>${this._marked?'<span class="segmented-timeline__selection-label">00:10:79-3:04:58</span>':''}<div class="segmented-timeline__range-rail"><span class="segmented-timeline__range-fill"></span>${this._marked?'<span class="segmented-timeline__range-fragment is-orange"></span><span class="segmented-timeline__range-fragment is-red"></span><span class="segmented-timeline__range-selection"></span>':''}<button type="button" class="segmented-timeline__range-handle is-start" aria-label="调整开始时间"></button><button type="button" class="segmented-timeline__range-handle is-end" aria-label="调整结束时间"></button></div></div>`;
      this._rail=this.querySelector('.segmented-timeline__range-rail');
      this._fill=this.querySelector('.segmented-timeline__range-fill');
      this._startHandle=this.querySelector('.segmented-timeline__range-handle.is-start');
      this._endHandle=this.querySelector('.segmented-timeline__range-handle.is-end');
      this._startLabel=this.querySelector('.segmented-timeline__range-label.is-start');
      this._endLabel=this.querySelector('.segmented-timeline__range-label.is-end');
      this._selection=this.querySelector('.segmented-timeline__range-selection');
      this._dragMode='';
      this._dragX=0;
      this._dragStart=0;
      this._dragEnd=0;
      this._startHandle.addEventListener('pointerdown',event=>this._beginDrag(event,'start'));
      this._endHandle.addEventListener('pointerdown',event=>this._beginDrag(event,'end'));
      this._startLabel.addEventListener('pointerdown',event=>this._beginDrag(event,'start'));
      this._endLabel.addEventListener('pointerdown',event=>this._beginDrag(event,'end'));
      for(const label of [this._startLabel,this._endLabel]){label.style.cursor='ew-resize';label.style.touchAction='none';label.style.userSelect='none';}
      (this._selection||this._fill).addEventListener('pointerdown',event=>this._beginDrag(event,'fill'));
      this.addEventListener('pointermove',event=>this._moveDrag(event));
      this.addEventListener('pointerup',event=>this._endDrag(event));
      this.addEventListener('pointercancel',event=>this._endDrag(event));
      this.setRange(this._start,this._end);
      this._labelObserver=new ResizeObserver(()=>this._layoutLabels());
      this._labelObserver.observe(this._rail);
    }
    disconnectedCallback(){this._labelObserver?.disconnect();}
    _layoutLabels(){
      const width=this._rail.clientWidth;
      if(!width||this._marked)return;
      const startWidth=this._startLabel.offsetWidth,endWidth=this._endLabel.offsetWidth,gap=6;
      let start=Math.max(0,Math.min(width-startWidth,width*this._start/100-startWidth/2));
      let end=Math.max(0,Math.min(width-endWidth,width*this._end/100-endWidth/2));
      if(end<start+startWidth+gap){
        end=Math.min(width-endWidth,start+startWidth+gap);
        start=Math.max(0,Math.min(start,end-startWidth-gap));
      }
      this._startLabel.style.left=`${start}px`;
      this._endLabel.style.left=`${end}px`;
      this._endLabel.style.transform='none';
    }
    _format(percent){const total=Math.round(percent*.7);return `${String(Math.floor(total/60)).padStart(2,'0')}:${String(total%60).padStart(2,'0')}s`;}
    setSnapPoints(points){this._snapPoints=[...new Set(points.map(value=>Math.max(0,Math.min(100,value))))];}
    _snap(value){
      if(!this._snapPoints.length)return {value,snapped:false};
      const threshold=this._rail.clientWidth?8/this._rail.clientWidth*100:0;
      const nearest=this._snapPoints.reduce((best,point)=>Math.abs(point-value)<Math.abs(best-value)?point:best,this._snapPoints[0]);
      const snapped=Math.abs(nearest-value)<=threshold;
      return {value:snapped?nearest:value,snapped};
    }
    setRange(start,end,emit=false){
      this._start=Math.max(0,Math.min(this._marked?99:100,start));
      this._end=Math.max(this._start+(this._marked?1:0),Math.min(100,end));
      this._fill.style.left=`${this._start}%`;
      this._fill.style.width=`${this._end-this._start}%`;
      this._startHandle.style.left=`${this._start}%`;
      this._endHandle.style.left=`${this._end}%`;
      this._startLabel.style.left=`${this._start}%`;
      this._endLabel.style.left=`${this._end}%`;
      if(this._selection){this._selection.style.left=`${this._start}%`;this._selection.style.width=`${this._end-this._start}%`;this.style.setProperty('--range-selection-center',`${(this._start+this._end)/2}%`);}
      this._startLabel.textContent=this._format(this._start);
      this._endLabel.textContent=this._format(this._end);
      this._layoutLabels();
      if(emit)this.dispatchEvent(new CustomEvent('range-change',{bubbles:true,detail:{start:this._start,end:this._end,dragMode:this._dragMode||'range'}}));
    }
    _beginDrag(event,mode){if(event.button!==0)return;event.preventDefault();event.stopPropagation();this._dragMode=mode;this._dragX=event.clientX;this._dragStart=this._start;this._dragEnd=this._end;this._dragTarget=event.currentTarget;this._dragFromLabel=this._dragTarget===this._startLabel||this._dragTarget===this._endLabel;event.currentTarget.setPointerCapture(event.pointerId);event.currentTarget.classList.add('is-dragging');}
    _moveDrag(event){
      if(!this._dragMode)return;
      const bounds=this._rail.getBoundingClientRect();
      if(!bounds.width)return;
      const value=this._dragFromLabel?(this._dragMode==='start'?this._dragStart:this._dragEnd)+(event.clientX-this._dragX)/bounds.width*100:(event.clientX-bounds.left)/bounds.width*100;
      const pointer=Math.max(0,Math.min(100,value));
      let snapped=false;
      if(this._dragMode==='start'){const result=this._snap(pointer);snapped=result.snapped;this.setRange(Math.min(result.value,this._end-(this._marked?1:0)),this._end,true);}
      if(this._dragMode==='end'){const result=this._snap(pointer);snapped=result.snapped;this.setRange(this._start,Math.max(result.value,this._start+(this._marked?1:0)),true);}
      if(this._dragMode==='fill'){
        const width=this._dragEnd-this._dragStart;
        const delta=(event.clientX-this._dragX)/bounds.width*100;
        let start=Math.max(0,Math.min(100-width,this._dragStart+delta));
        const left=this._snap(start),right=this._snap(start+width);
        if(left.snapped){start=left.value;snapped=true;}else if(right.snapped){start=right.value-width;snapped=true;}
        start=Math.max(0,Math.min(100-width,start));
        this.setRange(start,start+width,true);
      }
      const target=this._dragMode==='start'?this._startHandle:this._dragMode==='end'?this._endHandle:(this._selection||this._fill);
      target.classList.toggle('is-snapped',snapped);
    }
    _endDrag(event){
      if(!this._dragMode)return;
      const target=this._dragMode==='start'?this._startHandle:this._dragMode==='end'?this._endHandle:(this._selection||this._fill);
      target.classList.remove('is-dragging','is-snapped');
      this._dragTarget?.classList.remove('is-dragging','is-snapped');
      if(this._dragTarget?.hasPointerCapture(event.pointerId))this._dragTarget.releasePointerCapture(event.pointerId);
      this._dragTarget=null;
      this._dragMode='';
    }
  }

  class TimelineRangeRuler extends HTMLElement{
    connectedCallback(){if(this.dataset.rendered)return;this.dataset.rendered="true";this.innerHTML='<timeline-time-scale></timeline-time-scale><timeline-range-selector></timeline-range-selector>';this._selector=this.querySelector('timeline-range-selector');}
    get _rail(){return this._selector?._rail;}
    get _start(){return this._selector?._start;}
    get _end(){return this._selector?._end;}
    setSnapPoints(points){this._selector?.setSnapPoints(points);}
    setRange(start,end,emit=false){this._selector?.setRange(start,end,emit);}
  }

  class AnnotationSegmentRow extends HTMLElement{
    _setupMerge(){
      this._selected=new Set([0]);
      this._undoStack=[];
      this._activateHistory=()=>{AnnotationSegmentRow.activeHistory=this;};
      this.closest('segmented-track').addEventListener('pointerdown',this._activateHistory);
      this._undoKey=event=>{
        const mac=/Mac|iPhone|iPad|iPod/i.test(navigator.platform||navigator.userAgent);
        if(event.defaultPrevented)return;
        if(AnnotationSegmentRow.activeHistory!==this||!this.isConnected||!this.getClientRects().length)return;
        if(event.composedPath().some(target=>target instanceof HTMLElement&&(target.matches('input,textarea,select,[role="textbox"]')||target.isContentEditable)))return;
        if(['ArrowLeft','ArrowRight'].includes(event.key)&&(mac?event.metaKey&&!event.altKey&&!event.ctrlKey:event.altKey&&!event.metaKey&&!event.ctrlKey)&&!event.shiftKey){
          event.preventDefault();this.mergeAdjacent(event.key==='ArrowLeft'?-1:1);return;
        }
        if(event.key.toLowerCase()!=='z'||!(mac?event.metaKey:event.ctrlKey)||event.shiftKey||event.altKey)return;
        if(!this._undoStack.length)return;
        event.preventDefault();this.undoMerge();
      };
      document.addEventListener('keydown',this._undoKey);
      this._merge=document.createElement('button');
      this._merge.type='button';this._merge.className='segmented-timeline__merge';this._merge.hidden=true;
      this.querySelector('.segmented-timeline__row').append(this._merge);
      this.addEventListener('click',event=>{
        const button=event.target.closest('.segmented-timeline__segments>button');
        if(!button)return;
        event.stopImmediatePropagation();
        if(this.classList.contains('is-splitting')){this.splitAt(button,event.clientX);return;}
        const index=this.buttons.indexOf(button);
        if(event.altKey){
          if(this._selected.has(index))this._selected.delete(index);else this._selected.add(index);
          if(this._selected.size>1){const values=[...this._selected];for(let i=Math.min(...values);i<=Math.max(...values);i++)this._selected.add(i);}
          this._paintSelection();
        }else this.selectIndex(index,true);
      },true);
      this._merge.addEventListener('click',()=>this.mergeSelection());
      this.addEventListener('keydown',event=>{
        if(event.key==='Enter'&&this._selected.size>1){event.preventDefault();event.stopPropagation();this.mergeSelection();}
        if(event.key==='Escape'){this.selectIndex(Math.min(...this._selected)||0,false);}
      });
    }
    _paintSelection(){
      this.classList.toggle('is-multi-select',this._selected.size>1);
      const track=this.closest('segmented-track');
      const selected=[...this._selected];
      const up=track?.querySelector('[aria-label="向上合并"]'),down=track?.querySelector('[aria-label="向下合并"]');
      if(up)up.disabled=!selected.length||Math.min(...selected)===0;
      if(down)down.disabled=!selected.length||Math.max(...selected)===this.buttons.length-1;
      this.buttons.forEach((button,index)=>{button.classList.toggle('is-active',this._selected.has(index));button.setAttribute('aria-pressed',String(this._selected.has(index)));});
      this._merge.hidden=this._selected.size<2;
      this._merge.textContent=`合并 (${this._selected.size})`;
      if(this._selected.size>1){
        const indices=[...this._selected],first=this.buttons[Math.min(...indices)],last=this.buttons[Math.max(...indices)];
        this._merge.style.left=`${(first.offsetLeft+last.offsetLeft+last.offsetWidth)/2}px`;
      }
    }
    splitAt(button,clientX){
      const bounds=button.getBoundingClientRect();
      if(bounds.width<4)return;
      const ratio=(clientX-bounds.left)/bounds.width;
      if(ratio<=0||ratio>=1||Math.min(clientX-bounds.left,bounds.right-clientX)<2)return;
      this._activateHistory();
      this._undoStack.push({html:this.querySelector('.segmented-timeline__segments').innerHTML,selected:[...this._selected],label:this.querySelector('.segmented-timeline__index').textContent});
      if(this._undoStack.length>50)this._undoStack.shift();
      const weight=Number(button.style.flexGrow),right=button.cloneNode(true);
      if(this.closest('segmented-track')?.hasAttribute('split-lane')){
        const group=button.dataset.splitGroup||`split-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        button.dataset.splitGroup=group;right.dataset.splitGroup=group;
        const colorIndex=button.dataset.splitColorIndex!==undefined?Number(button.dataset.splitColorIndex):Math.max(-1,...this.buttons.map(item=>Number(item.dataset.splitColorIndex??-1)))+1;
        button.dataset.splitColorIndex=String(colorIndex);right.dataset.splitColorIndex=String(colorIndex);
        const color=splitLaneColors[colorIndex%splitLaneColors.length];
        button.dataset.splitColor=color;right.dataset.splitColor=color;
      }
      const currentColor=button.style.getPropertyValue('--segment-color').trim();
      const nextColor=button.nextElementSibling?.style.getPropertyValue('--segment-color').trim();
      const palette=segments.map(([,color])=>color);
      const start=palette.indexOf(currentColor);
      for(let offset=1;offset<=palette.length;offset++){
        const color=palette[(start+offset+palette.length)%palette.length];
        if(color!==currentColor&&color!==nextColor){right.style.setProperty('--segment-color',color);break;}
      }
      button.style.flex=String(weight*ratio);right.style.flex=String(weight*(1-ratio));
      button.after(right);
      this.buttons=[...this.querySelectorAll('.segmented-timeline__segments>button')];
      this.buttons.forEach((item,index)=>{item.dataset.index=index;item.setAttribute('aria-label',`片段 ${index+1}`);});
      this.querySelector('.segmented-timeline__index').textContent=this.buttons.length;
      const index=this.buttons.indexOf(right);
      this.selectIndex(index,true);right.focus({preventScroll:true});
      this.dispatchEvent(new CustomEvent('segments-split',{bubbles:true,detail:{index:index-1,ratio,count:this.buttons.length}}));
    }
    mergeAdjacent(direction){
      if(!this._selected.size)return;
      const indices=[...this._selected].sort((a,b)=>a-b);
      const adjacent=direction<0?indices[0]-1:indices[indices.length-1]+1;
      if(adjacent<0||adjacent>=this.buttons.length)return;
      this.mergeSelection([...indices,adjacent]);
    }
    mergeSelection(selection=[...this._selected]){
      if(selection.length<2)return;
      this._activateHistory();
      this._undoStack.push({html:this.querySelector('.segmented-timeline__segments').innerHTML,selected:[...this._selected],label:this.querySelector('.segmented-timeline__index').textContent});
      if(this._undoStack.length>50)this._undoStack.shift();
      const indices=[...selection].sort((a,b)=>a-b),index=indices[0],first=this.buttons[index];
      first.style.flex=String(indices.reduce((sum,i)=>sum+Number(this.buttons[i].style.flexGrow),0));
      if(indices.some(i=>this.buttons[i].querySelector('.segmented-timeline__warning'))&&!first.querySelector('.segmented-timeline__warning'))first.append(this.buttons.find((button,i)=>indices.includes(i)&&button.querySelector('.segmented-timeline__warning')).querySelector('.segmented-timeline__warning').cloneNode(true));
      indices.slice(1).forEach(i=>this.buttons[i].remove());
      this.buttons=[...this.querySelectorAll('.segmented-timeline__segments>button')];
      this.buttons.forEach((button,i)=>{button.dataset.index=i;button.setAttribute('aria-label',`片段 ${i+1}`);});
      this.querySelector('.segmented-timeline__index').textContent=this.buttons.length;
      this.selectIndex(index,true);first.focus();
      this.dispatchEvent(new CustomEvent('segments-merge',{bubbles:true,detail:{indices,index,count:this.buttons.length}}));
    }
    undoMerge(){
      const snapshot=this._undoStack.pop();
      if(!snapshot)return;
      this.querySelector('.segmented-timeline__segments').innerHTML=snapshot.html;
      this.buttons=[...this.querySelectorAll('.segmented-timeline__segments>button')];
      this.querySelector('.segmented-timeline__index').textContent=snapshot.label;
      const index=Math.min(...snapshot.selected);
      this.selectIndex(index,true);
      this._selected=new Set(snapshot.selected);this._paintSelection();
      this.buttons[index].focus({preventScroll:true});
      this.dispatchEvent(new CustomEvent('segments-undo',{bubbles:true,detail:{index,count:this.buttons.length}}));
    }
    disconnectedCallback(){
      document.removeEventListener('keydown',this._undoKey);
      if(AnnotationSegmentRow.activeHistory===this)AnnotationSegmentRow.activeHistory=null;
    }
    connectedCallback(){if(this.dataset.rendered)return;this.dataset.rendered="true";this.innerHTML=`<div class="segmented-timeline__row"><span class="segmented-timeline__index">${this.getAttribute('label')||'14'}</span><div class="segmented-timeline__track"><div class="segmented-timeline__segments">${segments.map(([flex,color],index)=>`<button type="button" data-index="${index}" style="flex:${flex};--segment-color:${color}" aria-label="片段 ${index+1}"${index===0?' class="is-active"':''}>${index===1||index===5?'<b class="segmented-timeline__warning" aria-label="该色块存在问题"></b>':''}${index===3||index===6?`<svg class="segmented-timeline__location ${index===6?'is-severe':''}" viewBox="0 0 24 24" role="img" aria-label="${index===6?'严重':'轻微'}问题定位"><title>${index===6?'严重':'轻微'}问题定位</title><path fill="currentColor" fill-rule="evenodd" d="M12 2a8 8 0 0 0-8 8c0 6 8 12 8 12s8-6 8-12a8 8 0 0 0-8-8Zm0 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"/><circle cx="12" cy="10" r="1.5" fill="currentColor"/></svg>`:''}</button>`).join('')}</div></div></div>`;this.buttons=[...this.querySelectorAll('.segmented-timeline__segments>button')];this.buttons.forEach(button=>button.addEventListener('click',()=>this.selectIndex(Number(button.dataset.index),true)));}
    selectIndex(index,emit=false){const safe=Math.max(0,Math.min(this.buttons.length-1,index));this.buttons.forEach((button,buttonIndex)=>button.classList.toggle('is-active',buttonIndex===safe));if(this._merge){this._selected=new Set([safe]);this._paintSelection();}if(emit)this.dispatchEvent(new CustomEvent('segment-select',{bubbles:true,detail:{index:safe}}));}
  }

  class AnnotationBaseRow extends HTMLElement{
    connectedCallback(){if(this.dataset.rendered)return;this.dataset.rendered="true";this.innerHTML=`<div class="segmented-timeline__row"><span class="segmented-timeline__index">${this.getAttribute('label')||'1'}</span><div class="segmented-timeline__track"><div class="segmented-timeline__segments"><button type="button" style="flex:100;--segment-color:#4fbd91" aria-label="连续轨道"></button></div></div></div>`;}
  }

  class TimelineControls extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered="true";
      const standardLabel=this.getAttribute('standard-label')||'标注标准';
      const shortcutMenu=`<span class="segmented-timeline__shortcut-anchor"><button type="button" class="segmented-timeline__tool segmented-timeline__shortcut-trigger" aria-label="快捷键" aria-expanded="false"><img src="${assets}figma-keyboard.svg" alt=""></button><span class="segmented-timeline__shortcut-popover" role="dialog" aria-label="分割模式快捷键" hidden><strong>分割模式快捷键</strong><span class="segmented-timeline__shortcut-list">${shortcutItems.map(([name,key])=>`<span><span>${escapeText(name)}</span><kbd>${key}</kbd></span>`).join('')}</span></span></span>`;
      const toolButtons=tools.slice(0,-1).map(([icon,label,extra])=>label==='快捷键'?`<i class="segmented-timeline__tool-divider" aria-hidden="true"></i>${shortcutMenu}`:`<button type="button" class="segmented-timeline__tool${extra}" aria-label="${label}"><img src="${assets}${icon}" alt=""></button>`).join('');
      this.innerHTML=`<div class="segmented-timeline__tools"><div class="segmented-timeline__playback"><button type="button" class="segmented-timeline__play" aria-label="播放"><img src="${assets}icon-play.svg" alt=""></button><span><b data-playback-current>00:06:15</b> <i>/</i> 08:47:00</span></div><div class="segmented-timeline__tool-group">${toolButtons}<span class="segmented-timeline__settings-anchor"><button type="button" class="segmented-timeline__tool segmented-timeline__settings-trigger" aria-label="源视频" aria-expanded="false"><img src="${assets}figma-video.svg" alt=""></button><span class="segmented-timeline__settings-popover" role="dialog" aria-label="源视频设置" hidden><span class="segmented-timeline__settings-row"><span>源视频优先</span><button class="segmented-timeline__settings-switch is-on" type="button" role="switch" aria-checked="true"><span></span></button></span></span></span></div><a href="#" class="segmented-timeline__standard">${standardLabel}</a></div>`;
      this._play=this.querySelector('.segmented-timeline__play');
      const speedButton=this.querySelector('.is-2x');
      speedButton.classList.add('segmented-timeline__speed');
      speedButton.innerHTML='<svg viewBox="0 0 20 20" aria-hidden="true"><path d="m12 4-6 6 6 6M17 4l-6 6 6 6"/></svg><span>1x</span><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m8 4 6 6-6 6M3 4l6 6-6 6"/></svg>';
      const shortcutAliases={'添加':'切分','清空':'删除','拖动':'拖动模式'};
      const modeButtons=[...this.querySelectorAll('.segmented-timeline__tool')].filter(button=>['拖动','分割','父级分割'].includes(button.getAttribute('aria-label')));
      this._parentSplitKey=event=>{
        if(event.key==='Escape'&&!event.defaultPrevented&&this.getClientRects().length){
          const active=modeButtons.find(button=>button.getAttribute('aria-pressed')==='true');
          if(active)active.click();
          return;
        }
        const mac=/Mac|iPhone|iPad|iPod/i.test(navigator.platform||navigator.userAgent);
        if(event.defaultPrevented||event.key.toLowerCase()!=='x'||!event.shiftKey||event.metaKey||!(mac?event.ctrlKey&&!event.altKey:event.altKey&&!event.ctrlKey))return;
        if(!this.getClientRects().length||!this.closest('segmented-track'))return;
        const track=this.closest('segmented-track');
        if(!track.contains(document.activeElement)&&AnnotationSegmentRow.activeHistory?.closest('segmented-track')!==track)return;
        if(event.composedPath().some(target=>target instanceof HTMLElement&&(target.matches('input,textarea,select,[role="textbox"]')||target.isContentEditable)))return;
        event.preventDefault();modeButtons.find(button=>button.getAttribute('aria-label')==='父级分割')?.click();
      };
      document.addEventListener('keydown',this._parentSplitKey);
      modeButtons.forEach(button=>{
        button.dataset.toolMode='true';
        button.setAttribute('aria-pressed','false');
        button.addEventListener('click',()=>{
          const selected=button.getAttribute('aria-pressed')!=='true';
          modeButtons.forEach(item=>{
            const active=selected&&item===button;
            item.setAttribute('aria-pressed',String(active));
            item.dataset.tooltip=active?`取消${item.dataset.defaultTooltip}\n退出快捷键：Esc`:item.dataset.defaultTooltip;
          });
          this.dispatchEvent(new CustomEvent('tool-mode-change',{bubbles:true,detail:{mode:selected?button.getAttribute('aria-label'):null}}));
        });
      });
      this.querySelectorAll('.segmented-timeline__tool').forEach(button=>{
        const label=button.getAttribute('aria-label');
        const shortcut=shortcutItems.find(([name])=>name===(shortcutAliases[label]||label))?.[1];
        button.dataset.tooltip=shortcut?`${label}（${shortcut}）`:label;
        button.dataset.defaultTooltip=button.dataset.tooltip;
      });
      this._current=this.querySelector('[data-playback-current]');
      this._settings=this.querySelector('.segmented-timeline__settings-popover');
      this._settingsTrigger=this.querySelector('.segmented-timeline__settings-trigger');
      this._shortcutMenu=this.querySelector('.segmented-timeline__shortcut-popover');
      this._shortcutTrigger=this.querySelector('.segmented-timeline__shortcut-trigger');
      this.querySelector('a').addEventListener('click',event=>event.preventDefault());
      this._play.addEventListener('click',()=>{this.setPlaying(this._play.getAttribute('aria-label')!=='暂停');this.dispatchEvent(new CustomEvent('play-toggle',{bubbles:true,detail:{playing:this._play.getAttribute('aria-label')==='暂停'}}));});
      this._settingsTrigger.addEventListener('click',event=>{event.stopPropagation();this._setSettingsOpen(this._settings.hidden);});
      this._shortcutTrigger.addEventListener('click',event=>{event.stopPropagation();this._setShortcutOpen(this._shortcutMenu.hidden);});
      const sourceSwitch=this.querySelector('.segmented-timeline__settings-switch');
      sourceSwitch.addEventListener('click',()=>{const enabled=sourceSwitch.getAttribute('aria-checked')!=='true';sourceSwitch.setAttribute('aria-checked',String(enabled));sourceSwitch.classList.toggle('is-on',enabled);});
      this.querySelectorAll('[data-theme]').forEach(button=>button.addEventListener('click',()=>this._applyTheme(button.dataset.theme,true)));
      this._outsideClick=event=>{if(!this.contains(event.target)){this._setSettingsOpen(false);this._setShortcutOpen(false);}};
      this._escapeKey=event=>{if(event.key==='Escape'){this._setSettingsOpen(false);this._setShortcutOpen(false);}};
      document.addEventListener('click',this._outsideClick);document.addEventListener('keydown',this._escapeKey);
      const themeKey=document.body.classList.contains('component-preview')?'workbench-component-theme':'workbench-theme';let stored=document.documentElement.dataset.workbenchTheme||(document.documentElement.dataset.theme==='dark'?'dark':'light');try{stored=localStorage.getItem(themeKey)||stored;}catch(_){}this._applyTheme(stored,false);
    }
    disconnectedCallback(){document.removeEventListener('click',this._outsideClick);document.removeEventListener('keydown',this._escapeKey);document.removeEventListener('keydown',this._parentSplitKey);}
    setPlaying(playing){if(!this._play)return;this._play.setAttribute('aria-label',playing?'暂停':'播放');this._play.setAttribute('aria-pressed',String(playing));this._play.classList.toggle('is-playing',playing);}
    setCurrentTime(percent){const total=Math.max(0,Math.min(100,percent))*.7,minutes=Math.floor(total/60),seconds=Math.floor(total%60),centiseconds=Math.floor(total%1*100);if(this._current)this._current.textContent=`${String(minutes).padStart(2,'0')}:${String(seconds).padStart(2,'0')}:${String(centiseconds).padStart(2,'0')}`;}
    _setSettingsOpen(open){
      if(!this._settings)return;
      const panel=this._settings;
      panel.setAttribute('popover','manual');
      if(!open){if(panel.matches(':popover-open'))panel.hidePopover();panel.hidden=true;}
      else{
        panel.hidden=false;
        Object.assign(panel.style,{position:'fixed',inset:'auto',margin:'0',transform:'none'});
        if(!panel.matches(':popover-open'))panel.showPopover();
        const anchor=this._settingsTrigger.getBoundingClientRect();
        panel.style.left=`${Math.max(8,Math.min(window.innerWidth-panel.offsetWidth-8,anchor.left+anchor.width/2-panel.offsetWidth/2))}px`;
        panel.style.top=`${Math.max(8,anchor.top-panel.offsetHeight-10)}px`;
      }
      this._settingsTrigger.setAttribute('aria-expanded',String(open));
    }
    _setShortcutOpen(open){
      if(!this._shortcutMenu)return;
      const panel=this._shortcutMenu;
      panel.setAttribute('popover','manual');
      if(!open){if(panel.matches(':popover-open'))panel.hidePopover();panel.hidden=true;}
      else{
        this._setSettingsOpen(false);
        panel.hidden=false;
        Object.assign(panel.style,{position:'fixed',inset:'auto',margin:'0',transform:'none'});
        if(!panel.matches(':popover-open'))panel.showPopover();
        const anchor=this._shortcutTrigger.getBoundingClientRect(),width=panel.offsetWidth,height=panel.offsetHeight;
        panel.style.left=`${Math.max(8,Math.min(window.innerWidth-width-8,anchor.left+anchor.width/2-width/2))}px`;
        panel.style.top=`${Math.max(8,anchor.top-height-10)}px`;
      }
      this._shortcutTrigger.setAttribute('aria-expanded',String(open));
    }
    _applyTheme(theme,persist){applyWorkbenchTheme(theme,persist);}
  }

  class WorkbenchMultiSelect extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      this._options=(this.getAttribute('options')||'').split('|').filter(Boolean);
      this._selected=new Set((this.getAttribute('value')||'').split('|').filter(value=>this._options.includes(value)));
      this.innerHTML=`<div class="workbench-multi-select__trigger input-like" role="button" tabindex="0" aria-haspopup="listbox" aria-expanded="false"><span class="workbench-multi-select__value"></span><img src="${assets}icon-chevron.svg" alt=""></div><div class="workbench-multi-select__popover" hidden><div class="workbench-multi-select__options" role="listbox" aria-multiselectable="true">${this._options.map(option=>`<button type="button" data-multi-option="${option}" role="option">${option}<span>✓</span></button>`).join('')}</div><button class="workbench-multi-select__clear" type="button">清除已选项</button></div>`;
      this._trigger=this.querySelector('.workbench-multi-select__trigger');this._popover=this.querySelector('.workbench-multi-select__popover');
      this._renderValue();
      this._trigger.addEventListener('click',event=>{if(event.target.closest('[data-remove-value]'))return;this._setOpen(this._popover.hidden);});
      this._trigger.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();this._setOpen(this._popover.hidden);}});
      this.addEventListener('click',event=>{const remove=event.target.closest('[data-remove-value]');if(remove){event.stopPropagation();this._selected.delete(remove.dataset.removeValue);this._renderValue();this._emitChange();return;}const option=event.target.closest('[data-multi-option]');if(option){const value=option.dataset.multiOption;this._selected.has(value)?this._selected.delete(value):this._selected.add(value);this._renderValue();this._emitChange();return;}if(event.target.closest('.workbench-multi-select__clear')){this._selected.clear();this._renderValue();this._emitChange();}});
      this._outsideClick=event=>{if(!this.contains(event.target))this._setOpen(false);};
      this._escapeKey=event=>{if(event.key==='Escape')this._setOpen(false);};
      this._viewportChange=()=>{if(!this._popover.hidden)this._positionPopover();};
      document.addEventListener('click',this._outsideClick);document.addEventListener('keydown',this._escapeKey);window.addEventListener('resize',this._viewportChange);window.addEventListener('scroll',this._viewportChange,true);
    }
    disconnectedCallback(){document.removeEventListener('click',this._outsideClick);document.removeEventListener('keydown',this._escapeKey);window.removeEventListener('resize',this._viewportChange);window.removeEventListener('scroll',this._viewportChange,true);}
    _renderValue(){const value=this.querySelector('.workbench-multi-select__value'),placeholder=this.getAttribute('placeholder')||'请选择';value.innerHTML=this._selected.size?[...this._selected].map(item=>`<span class="workbench-multi-select__tag">${item}<button type="button" data-remove-value="${item}" aria-label="移除${item}">×</button></span>`).join(''):`<span class="workbench-multi-select__placeholder">${placeholder}</span>`;this.querySelectorAll('[data-multi-option]').forEach(option=>{const active=this._selected.has(option.dataset.multiOption);option.classList.toggle('is-selected',active);option.setAttribute('aria-selected',String(active));});}
    _positionPopover(){const bounds=this._trigger.getBoundingClientRect(),width=Math.min(bounds.width,window.innerWidth-bounds.left-12);this._popover.style.width=`${width}px`;this._popover.style.left=`${Math.max(12,bounds.left)}px`;this._popover.style.top=`${Math.max(12,bounds.top-this._popover.offsetHeight-8)}px`;}
    _setOpen(open){this._popover.hidden=!open;this._trigger.setAttribute('aria-expanded',String(open));this._trigger.classList.toggle('is-open',open);if(open)requestAnimationFrame(()=>this._positionPopover());}
    _emitChange(){this.dispatchEvent(new CustomEvent('multi-select-change',{bubbles:true,detail:{values:[...this._selected]}}));}
    get values(){return [...this._selected];}
    setValues(values,emit=false){this._selected=new Set((values||[]).filter(value=>this._options.includes(value)));this._renderValue();if(emit)this._emitChange();}
  }

  class WorkbenchTaskHeader extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      if(this.hasAttribute('hydrate')){this.dataset.rendered='true';return;}
      this.dataset.rendered='true';
      const isLongReject=this.getAttribute('variant')==='long-reject';
      const rejectReason=isLongReject?'驳回原因：High-level片段范围需要调整，动作起止边界与任务要求不一致，请重新检查完整操作过程后修正并再次提交':'驳回原因：High-level片段范围需要调整';
      this.innerHTML=`<header class="workbench-task-info"><div class="workbench-task-info__left"><button class="workbench-task-info__close" type="button" aria-label="关闭"><img src="${assets}icon-close.svg" alt=""></button><div class="workbench-task-info__identity"><span>任务ID</span><b>17782</b></div><i class="workbench-task-info__divider" aria-hidden="true"></i><div class="workbench-task-info__workflow"><div class="workbench-task-info__step"><span>当前节点</span><b>内部验收</b></div><i class="workbench-task-info__divider" aria-hidden="true"></i><div class="workbench-task-info__step"><span>上一节点</span><b>供应商验收</b><em>·</em><b>Aria提交</b><em>·</em></div></div><div class="workbench-task-info__reject"${isLongReject?` tabindex="0" aria-label="${rejectReason}" data-tooltip="${rejectReason}"`:` title="${rejectReason}"`}><span>${rejectReason}</span></div></div></header>`;
      const taskIdentity=this.querySelector('.workbench-task-info__identity');
      for(const [label,attribute] of [['数据处理 ID','data-processing-id'],['数据 ID','data-id']]){
        const identity=document.createElement('div');
        identity.className='workbench-task-info__identity';
        const name=document.createElement('span');name.textContent=label;
        const value=document.createElement('b');value.textContent=this.getAttribute(attribute)||'—';
        identity.append(name,value);
        const divider=document.createElement('i');divider.className='workbench-task-info__divider';divider.setAttribute('aria-hidden','true');
        taskIdentity.before(identity,divider);
      }
      this.querySelector('.workbench-task-info__close').addEventListener('click',()=>this.dispatchEvent(new CustomEvent('workbench-close',{bubbles:true})));
      if(isLongReject){
        const trigger=this.querySelector('.workbench-task-info__reject');
        const tooltip=document.createElement('div');
        tooltip.className='workbench-reject-tooltip';
        tooltip.setAttribute('popover','manual');
        tooltip.setAttribute('role','tooltip');
        tooltip.id=`reject-tooltip-${Math.random().toString(36).slice(2)}`;
        tooltip.textContent=rejectReason;
        this.append(tooltip);
        trigger.setAttribute('aria-describedby',tooltip.id);
        const hide=()=>{if(tooltip.matches(':popover-open'))tooltip.hidePopover();};
        const show=()=>{
          if(!tooltip.matches(':popover-open'))tooltip.showPopover();
          const bounds=trigger.getBoundingClientRect();
          const left=Math.max(8,Math.min(bounds.right-tooltip.offsetWidth,window.innerWidth-tooltip.offsetWidth-8));
          const top=bounds.bottom+8+tooltip.offsetHeight<=window.innerHeight-8?bounds.bottom+8:Math.max(8,bounds.top-tooltip.offsetHeight-8);
          tooltip.style.left=`${left}px`;tooltip.style.top=`${top}px`;
        };
        trigger.addEventListener('mouseenter',show);
        trigger.addEventListener('mouseleave',hide);
        trigger.addEventListener('focus',show);
        trigger.addEventListener('blur',hide);
        trigger.addEventListener('keydown',event=>{if(event.key==='Escape')hide();});
      }
    }
  }

  class WorkbenchInstruction extends HTMLElement{
    static get observedAttributes(){return ['mode','variant'];}
    attributeChangedCallback(name,oldValue,newValue){
      if(oldValue===newValue||this.dataset.rendered!=='true')return;
      if(name==='mode')this.setMode(newValue);
      if(name==='variant'&&!this.hasAttribute('hydrate'))this.render();
    }
    connectedCallback(){
      if(this.dataset.rendered)return;
      if(this.hasAttribute('hydrate')){this.dataset.rendered='true';return;}
      this.dataset.rendered='true';
      this.render();
      this.setMode(this.getAttribute('mode')||'segments');
    }
    render(){
      const isLong=this.getAttribute('variant')==='long';
      const instruction=isLong
        ?'归位书本与笔记本：将散落在桌面、椅面和地面的书本与笔记本逐一整理，按照书本、笔记本分类后放回书架指定位置；摆放时保持书脊朝外、整体竖直，同类物品集中排列，并确保书架前方及周边没有遗漏物品，完成后将双手移出操作区域。'
        :'归位书本与笔记本：将散落的书本和笔记本整理并放回书架指定位置，保持竖立排列或按类别分层摆放，便于查找和取用';
      this.innerHTML=`<div class="workbench-instruction${isLong?' workbench-instruction--expandable':''}"${isLong?' aria-expanded="false"':''}><span class="workbench-instruction__inline"><b>采集指令</b><i aria-hidden="true"></i><span>${instruction}</span></span>${isLong?'<button class="workbench-instruction__expand" type="button" aria-expanded="false"><span>展开</span><i aria-hidden="true"></i></button>':''}</div>`;
      const button=this.querySelector('.workbench-instruction__expand');
      if(button)button.addEventListener('click',()=>{
        const panel=this.querySelector('.workbench-instruction');
        const expanded=button.getAttribute('aria-expanded')!=='true';
        button.setAttribute('aria-expanded',String(expanded));
        button.querySelector('span').textContent=expanded?'收起':'展开';
        panel.setAttribute('aria-expanded',String(expanded));
        panel.classList.toggle('is-expanded',expanded);
      });
    }
    setMode(mode){this.dataset.mode=['quality','action','tags'].includes(mode)?mode:'segments';this.setAttribute('aria-label',`${mode==='quality'?'质检':mode==='action'?'动作标注':mode==='tags'?'标签':'语义标注'}视频采集指令`);}
  }

  class WorkbenchMediaViewer extends HTMLElement{
    static get observedAttributes(){return ['variant'];}
    attributeChangedCallback(name,oldValue,newValue){
      if(name==='variant'&&oldValue!==newValue&&this.dataset.rendered==='true'&&!this.hasAttribute('hydrate'))this._render();
    }
    connectedCallback(){
      if(this.dataset.rendered)return;
      if(this.hasAttribute('hydrate')){this.dataset.rendered='true';return;}
      this.dataset.rendered='true';
      this._render();
    }
    _render(){
      this._resizeObserver?.disconnect();
      if(this.getAttribute('variant')==='dataset'){
        this.innerHTML='<div class="workbench-dataset-feeds">'+['cam_high','cam_left_wrist','cam_right_wrist'].map(label=>`<figure><figcaption>${label}</figcaption><span>暂无视频源</span></figure>`).join('')+'</div>';
        return;
      }
      const feed=(label,className)=>`<figure class="workbench-feed ${className}"><img src="${assets}frame.png" alt=""><figcaption>${label} <img src="${assets}icon-fullscreen.svg" alt=""></figcaption></figure>`;
      const threePanel=this.getAttribute('variant')==='three-panel';
      this.innerHTML=threePanel
        ?`<div class="workbench-media-preview"><div class="workbench-video-grid workbench-video-grid--three-panel"><div class="workbench-video-grid__arms">${feed('左臂视角','workbench-feed--arm')}${feed('右臂视角','workbench-feed--arm')}</div>${feed('头部视角','workbench-feed--three-panel')}</div></div>`
        :`<div class="workbench-media-preview"><div class="workbench-video-grid"><div class="workbench-video-grid__arms">${feed('左臂视角','workbench-feed--arm')}${feed('右臂视角','workbench-feed--arm')}</div>${feed('头部视角','workbench-feed--head')}${feed('头部结束帧','workbench-feed--head')}</div></div>`;
      const grid=this.querySelector('.workbench-video-grid');
      const resize=()=>{
        const width=Math.max(0,grid.clientWidth),gap=8;
        if(threePanel){
          const availableHeight=grid.closest('.media-card')?grid.clientHeight:Infinity;
          const layoutHeight=Math.max(0,Math.floor(Math.min(availableHeight,(width-gap*.25)/2.25))),armHeight=Math.max(0,(layoutHeight-gap)/2),armWidth=armHeight*1.5,largeWidth=layoutHeight*1.5;
          grid.style.setProperty('--head-video-size',`${layoutHeight}px`);grid.style.setProperty('--arm-video-width',`${armWidth}px`);grid.style.setProperty('--arm-video-height',`${armHeight}px`);grid.style.setProperty('--three-panel-width',`${largeWidth}px`);
          return;
        }
        const height=Math.max(0,grid.clientHeight),layoutHeight=Math.floor(Math.min(height,Math.max(0,(width-10)/2.75))),armHeight=Math.floor((layoutHeight-gap)/2),armWidth=Math.floor(armHeight*1.5);
        grid.style.setProperty('--head-video-size',`${layoutHeight}px`);grid.style.setProperty('--arm-video-width',`${armWidth}px`);grid.style.setProperty('--arm-video-height',`${armHeight}px`);
      };
      this._resizeObserver=new ResizeObserver(resize);
      this._resizeObserver.observe(grid);
      resize();
    }
    disconnectedCallback(){this._resizeObserver?.disconnect();}
  }

  class WorkbenchSegmentEditor extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      if(this.hasAttribute('hydrate')){this.dataset.rendered='true';return;}
      this.dataset.rendered='true';
      this._index=2;
      this._segments=[
        {start:'00:00',end:'00:11',duration:'00:11',description:'观察并整理桌面物品（前端测试V4 预标注片段 1）',error:'片段范围错误',unavailable:false},
        {start:'00:11',end:'00:15',duration:'00:04',description:'选择错移动遥控器到目标位置（前端测试V4 预标注片段 2）',error:'片段范围错位',unavailable:false},
        {start:'00:15',end:'00:18',duration:'00:03',description:'打开或关闭抽屉（前端测试V4 预标注片段 3）',error:'',unavailable:false},
        {start:'00:18',end:'00:21',duration:'00:03',description:'调整纸盒摆放位置（前端测试V4 预标注片段 4）',error:'动作结束边界偏晚',unavailable:false},
        {start:'00:21',end:'00:27',duration:'00:06',description:'将散落书本整理并竖直放回书架（前端测试V4 预标注片段 5）',error:'',unavailable:false},
        {start:'00:27',end:'00:32',duration:'00:05',description:'将笔记本按类别放回指定位置（前端测试V4 预标注片段 6）',error:'',unavailable:false}
      ];
      const reasons=['片段范围错误','片段范围错位','动作开始边界偏早','动作开始边界偏晚','动作结束边界偏早','动作结束边界偏晚','描述与画面不一致'];
      const errorSelector=`<button type="button" class="input-like error-trigger is-placeholder" data-action="error" aria-haspopup="listbox" aria-expanded="false"><span data-error>请选择错误原因</span><img src="${assets}icon-chevron.svg" alt=""></button></div></section><div class="error-popover" role="dialog" aria-label="选择错误原因" hidden><div class="error-options" role="listbox">${reasons.map(reason=>`<button class="error-option" type="button" data-reason="${reason}" role="option">${reason}<span>✓</span></button>`).join('')}</div><button class="error-popover__clear" type="button" data-action="clear-error">清除错误原因</button></div>`;
      if(this.getAttribute('variant')==='variant-2'){
        this.innerHTML=`<div class="segment-editor-component"><section class="card form-card"><div class="form-row form-row--meta"><div class="segment-meta"><span class="segment-current segment-current--code"><b class="current-segment-value" data-number>02</b></span><span>开始时间</span><b data-start>00:11</b><span>结束时间</span><b data-end>00:15</b><span>时长</span><b data-duration>00:04</b></div><div class="segment-actions" aria-label="片段操作"><button class="segment-action segment-action--navigate" type="button" data-action="previous">上一段 <kbd>⌘↑</kbd></button><button class="segment-action segment-action--navigate" type="button" data-action="next">下一段 <kbd>⌘↓</kbd></button><button class="segment-action segment-action--danger" type="button" data-action="delete">删除 <kbd>⌘⌫</kbd></button><button class="segment-action" type="button" data-action="unavailable" aria-pressed="false">无法标注 <kbd>⌘/</kbd></button></div></div><div class="form-row"><span class="field-label">失误程度</span><div class="input-like input-like--description workbench-severity-options" role="radiogroup" aria-label="失误程度"><label><input type="radio" name="mistake-severity-${Math.random().toString(36).slice(2)}" value="轻微" checked><span>轻微</span></label><label><input type="radio" name="mistake-severity-${Math.random().toString(36).slice(2)}" value="严重"><span>严重</span></label></div></div><div class="form-row form-row--error"><label class="field-label" for="mistake-description-${Math.random().toString(36).slice(2)}">失误描述</label><input class="input-like workbench-mistake-description" id="mistake-description-${Math.random().toString(36).slice(2)}" type="text" placeholder="请输入失误描述"></div><div class="form-row form-row--error"><span class="field-label">错误原因</span>${errorSelector}</div>`;
        const radios=[...this.querySelectorAll('.workbench-severity-options input')],radioName=`mistake-severity-${Math.random().toString(36).slice(2)}`;
        radios.forEach(radio=>{radio.name=radioName;});
        const description=this.querySelector('.workbench-mistake-description'),descriptionId=`mistake-description-${Math.random().toString(36).slice(2)}`;
        description.id=descriptionId;this.querySelector('label[for^="mistake-description-"]').htmlFor=descriptionId;
        this._variantClick=event=>{const action=event.target.closest('[data-action]')?.dataset.action;if(action==='previous')this._setSeveritySegment(this._index-1,true);if(action==='next')this._setSeveritySegment(this._index+1,true);if(action==='delete'){const button=this.querySelector('[data-action=delete]');button.classList.add('is-active');window.setTimeout(()=>button.classList.remove('is-active'),260);}if(action==='unavailable'){const button=this.querySelector('[data-action=unavailable]'),active=button.getAttribute('aria-pressed')!=='true';button.classList.toggle('is-active',active);button.setAttribute('aria-pressed',String(active));}if(action==='error')this._setErrorOpen(this.querySelector('.error-popover').hidden);if(action==='clear-error'){this._segments[this._index-1].error='';this._setSeveritySegment(this._index,false);this._emitUpdate();this._setErrorOpen(false);}const reason=event.target.closest('[data-reason]')?.dataset.reason;if(reason){this._segments[this._index-1].error=reason;this._setSeveritySegment(this._index,false);this._emitUpdate();this._setErrorOpen(false);}};
        this.addEventListener('click',this._variantClick);
        this._externalChange=event=>{if(event.target!==this&&event.detail?.index)this._setSeveritySegment(event.detail.index,false);};
        this._documentKeydown=event=>{if(this.hidden||!event.metaKey)return;const action=event.key==='ArrowUp'?'previous':event.key==='ArrowDown'?'next':event.key==='Backspace'?'delete':event.key==='/'?'unavailable':'';if(!action)return;event.preventDefault();this.querySelector(`[data-action="${action}"]`)?.click();};
        this._documentClick=event=>{if(!this.contains(event.target))this._setErrorOpen(false);};
        this._windowResize=()=>{if(!this.querySelector('.error-popover').hidden)this._positionErrorPopover();};
        document.addEventListener('segment-change',this._externalChange);document.addEventListener('click',this._documentClick);document.addEventListener('keydown',this._documentKeydown);window.addEventListener('resize',this._windowResize);this._setSeveritySegment(2,false);
        return;
      }
      if(this.getAttribute('variant')==='variant-3'){
this.innerHTML=`<div class="segment-editor-component"><section class="card form-card"><div class="form-row form-row--meta"><div class="segment-meta"><span class="segment-current segment-current--code"><b class="current-segment-value" data-number>02</b></span><span>开始时间</span><b data-start>00:11</b><span>结束时间</span><b data-end>00:15</b><span>时长</span><b data-duration>00:04</b><span>颜色</span><i class="workbench-segment-color" data-segment-color aria-label="当前片段颜色"></i></div><div class="segment-actions" aria-label="片段操作"><button class="segment-action segment-action--navigate" type="button" data-action="previous">上一段 <kbd>⌘↑</kbd></button><button class="segment-action segment-action--navigate" type="button" data-action="next">下一段 <kbd>⌘↓</kbd></button><button class="segment-action segment-action--danger" type="button" data-action="delete">删除 <kbd>⌘⌫</kbd></button><button class="segment-action" type="button" data-action="unavailable" aria-pressed="false">无法标注 <kbd>⌘/</kbd></button></div></div><div class="form-row"><span class="field-label">动作元素</span><div class="workbench-editor-selects"><workbench-multi-select aria-label="动作元素" placeholder="请选择动作元素" options="遥控器|纸盒|书本|笔记本|桌面|抽屉|把手|书架" value="书本"></workbench-multi-select><span class="field-label workbench-action-description-label">动作描述</span><workbench-multi-select aria-label="动作描述" placeholder="请选择动作描述" options="观察并整理桌面物品|选择并移动遥控器到目标位置|打开或关闭抽屉|调整纸盒摆放位置|整理散落书本|将书本竖直放回书架|按类别整理笔记本|放回指定位置|拿起|移动|放置|整理"></workbench-multi-select><span class="field-label workbench-action-description-label">缩略图</span><img class="workbench-action-thumbnail" src="${assets}frame.png" alt="动作片段缩略图"></div></div><div class="form-row form-row--error"><span class="field-label">错误原因</span>${errorSelector}</div>`;
        this._actionData=[
          {elements:['书本','桌面'],descriptions:['观察并整理桌面物品']},
          {elements:['遥控器'],descriptions:['选择并移动遥控器到目标位置']},
          {elements:['抽屉','把手'],descriptions:['打开或关闭抽屉']},
          {elements:['纸盒'],descriptions:['调整纸盒摆放位置']},
          {elements:['书本','书架'],descriptions:['整理散落书本','将书本竖直放回书架']},
          {elements:['笔记本'],descriptions:['按类别整理笔记本','放回指定位置']}
        ];
        this._variantClick=event=>{const action=event.target.closest('[data-action]')?.dataset.action;if(action==='previous')this._setSeveritySegment(this._index-1,true);if(action==='next')this._setSeveritySegment(this._index+1,true);if(action==='delete'){const button=this.querySelector('[data-action=delete]');button.classList.add('is-active');window.setTimeout(()=>button.classList.remove('is-active'),260);}if(action==='unavailable'){const button=this.querySelector('[data-action=unavailable]'),active=button.getAttribute('aria-pressed')!=='true';button.classList.toggle('is-active',active);button.setAttribute('aria-pressed',String(active));}if(action==='error')this._setErrorOpen(this.querySelector('.error-popover').hidden);if(action==='clear-error'){this._segments[this._index-1].error='';this._setSeveritySegment(this._index,false);this._emitUpdate();this._setErrorOpen(false);}const reason=event.target.closest('[data-reason]')?.dataset.reason;if(reason){this._segments[this._index-1].error=reason;this._setSeveritySegment(this._index,false);this._emitUpdate();this._setErrorOpen(false);}};
        this.addEventListener('click',this._variantClick);
        this._multiSelectChange=()=>{const elements=this.querySelector('workbench-multi-select[aria-label="动作元素"]')?.values||[],descriptions=this.querySelector('workbench-multi-select[aria-label="动作描述"]')?.values||[];this._actionData[this._index-1]={elements:[...elements],descriptions:[...descriptions]};this.dispatchEvent(new CustomEvent('action-annotation-change',{bubbles:true,detail:{index:this._index,elements,descriptions}}));};
        this.addEventListener('multi-select-change',this._multiSelectChange);
        this._externalChange=event=>{if(event.target!==this&&event.detail?.index)this._setSeveritySegment(event.detail.index,false);};
        this._documentKeydown=event=>{if(event.key==='Escape')this._setErrorOpen(false);if(!event.metaKey)return;const action=event.key==='ArrowUp'?'previous':event.key==='ArrowDown'?'next':event.key==='Backspace'?'delete':event.key==='/'?'unavailable':'';if(!action)return;event.preventDefault();this.querySelector(`[data-action="${action}"]`)?.click();};
        this._documentClick=event=>{if(!this.contains(event.target))this._setErrorOpen(false);};
        this._windowResize=()=>{if(!this.querySelector('.error-popover').hidden)this._positionErrorPopover();};
        document.addEventListener('segment-change',this._externalChange);document.addEventListener('click',this._documentClick);document.addEventListener('keydown',this._documentKeydown);window.addEventListener('resize',this._windowResize);this._setSeveritySegment(2,false);
        return;
      }
      this.innerHTML=`<div class="segment-editor-component"><section class="card form-card"><div class="form-row form-row--meta"><div class="segment-meta"><span class="segment-current segment-current--code">01-<b class="current-segment-value" data-number>02</b></span><span>开始时间</span><b data-start>00:11</b><span>结束时间</span><b data-end>00:15</b><span>时长</span><b data-duration>00:04</b></div><div class="segment-actions" aria-label="片段操作"><button class="segment-action segment-action--navigate" type="button" data-action="previous">上一段 <kbd>⌘↑</kbd></button><button class="segment-action segment-action--navigate" type="button" data-action="next">下一段 <kbd>⌘↓</kbd></button><button class="segment-action segment-action--danger" type="button" data-action="delete">删除 <kbd>⌘⌫</kbd></button><button class="segment-action" type="button" data-action="unavailable" aria-pressed="false">无法标注 <kbd>⌘/</kbd></button></div></div><div class="form-row"><span class="field-label">描述</span><div class="input-like input-like--description"><span class="description-value" data-description></span><span class="unavailable-tag" hidden>无法标注<button type="button" data-action="clear-unavailable" aria-label="关闭无法标注状态">×</button></span></div></div><div class="form-row form-row--error"><span class="field-label">错误原因</span><button type="button" class="input-like error-trigger" data-action="error" aria-haspopup="listbox" aria-expanded="false"><span data-error></span><img src="${assets}icon-chevron.svg" alt=""></button></div></section><div class="error-popover" role="dialog" aria-label="选择错误原因" hidden><div class="error-options" role="listbox">${reasons.map(reason=>`<button class="error-option" type="button" data-reason="${reason}" role="option">${reason}<span>✓</span></button>`).join('')}</div><button class="error-popover__clear" type="button" data-action="clear-error">清除错误原因</button></div></div>`;
      this.addEventListener('click',event=>this._handleClick(event));
      this._externalChange=event=>{if(event.target!==this&&event.detail?.index)this.setSegment(event.detail.index,false);};
      this._documentClick=event=>{if(!this.contains(event.target))this._setErrorOpen(false);};
      this._documentKeydown=event=>{
        if(event.key==='Escape')this._setErrorOpen(false);
        if(this.hidden||!event.metaKey)return;
        const action=event.key==='ArrowUp'?'previous':event.key==='ArrowDown'?'next':event.key==='Backspace'?'delete':event.key==='/'?'unavailable':'';
        if(!action)return;
        event.preventDefault();
        this.querySelector(`[data-action="${action}"]`)?.click();
      };
      this._windowResize=()=>{if(!this.querySelector('.error-popover').hidden)this._positionErrorPopover();};
      document.addEventListener('segment-change',this._externalChange);
      document.addEventListener('click',this._documentClick);
      document.addEventListener('keydown',this._documentKeydown);
      window.addEventListener('resize',this._windowResize);
      this.setSegment(2,false);
    }
    disconnectedCallback(){document.removeEventListener('segment-change',this._externalChange);document.removeEventListener('click',this._documentClick);document.removeEventListener('keydown',this._documentKeydown);window.removeEventListener('resize',this._windowResize);if(this._variantClick)this.removeEventListener('click',this._variantClick);if(this._multiSelectChange)this.removeEventListener('multi-select-change',this._multiSelectChange);}
    _setSeveritySegment(index,emit=true){const safe=Math.max(1,Math.min(this._segments.length,Number(index)||1)),{start,end,duration,error}=this._segments[safe-1],colors=['#42a8d2','#ff9559','#9850d7','#48c98a','#8fd04c','#d7a23b'];this._index=safe;this.querySelector('[data-number]').textContent=String(safe).padStart(2,'0');this.querySelector('[data-start]').textContent=start;this.querySelector('[data-end]').textContent=end;this.querySelector('[data-duration]').textContent=duration;const trigger=this.querySelector('.error-trigger');if(trigger){trigger.querySelector('[data-error]').textContent=error||'请选择错误原因';trigger.classList.toggle('is-placeholder',!error);this.querySelectorAll('[data-reason]').forEach(button=>button.classList.toggle('is-selected',button.dataset.reason===error));}const color=this.querySelector('[data-segment-color]');if(color){color.style.backgroundColor=colors[safe-1];color.setAttribute('aria-label',`当前片段颜色 ${colors[safe-1]}`);}if(this.getAttribute('variant')==='variant-3'&&this._actionData){const data=this._actionData[safe-1];this.querySelector('workbench-multi-select[aria-label="动作元素"]')?.setValues(data.elements);this.querySelector('workbench-multi-select[aria-label="动作描述"]')?.setValues(data.descriptions);}if(emit)this.dispatchEvent(new CustomEvent('segment-change',{bubbles:true,detail:{index:safe}}));}
    _handleClick(event){
      const action=event.target.closest('[data-action]')?.dataset.action;
      if(action==='previous')this.setSegment(this._index-1,true);
      if(action==='next')this.setSegment(this._index+1,true);
      if(action==='delete'){const button=this.querySelector('[data-action=delete]');button.classList.add('is-active');window.setTimeout(()=>button.classList.remove('is-active'),260);this.dispatchEvent(new CustomEvent('segment-delete',{bubbles:true,detail:{index:this._index}}));}
      if(action==='unavailable')this._setUnavailable(!this._unavailable);
      if(action==='clear-unavailable'){event.stopPropagation();this._setUnavailable(false);}
      if(action==='error')this._setErrorOpen(this.querySelector('.error-popover').hidden);
      if(action==='clear-error'){this._segments[this._index-1].error='';this.setSegment(this._index,false);this._emitUpdate();this._setErrorOpen(false);}
      const reason=event.target.closest('[data-reason]')?.dataset.reason;
      if(reason){this._segments[this._index-1].error=reason;this.setSegment(this._index,false);this._emitUpdate();this._setErrorOpen(false);}
    }
    _setUnavailable(value,persist=true){this._unavailable=value;if(persist)this._segments[this._index-1].unavailable=value;const description=this.querySelector('.input-like--description'),descriptionValue=description?.querySelector('[data-description]');description?.classList.toggle('is-unavailable',value);descriptionValue?.setAttribute('aria-disabled',String(value));this.querySelector('.unavailable-tag').hidden=!value;const button=this.querySelector('[data-action=unavailable]');button.classList.toggle('is-active',value);button.setAttribute('aria-pressed',String(value));if(persist)this._emitUpdate();}
    _positionErrorPopover(){const trigger=this.querySelector('.error-trigger'),popover=this.querySelector('.error-popover'),bounds=trigger.getBoundingClientRect(),left=Math.max(12,bounds.left),width=Math.min(bounds.width,window.innerWidth-left-12);popover.style.width=`${width}px`;popover.style.left=`${left}px`;popover.style.top=`${Math.max(12,bounds.top-popover.offsetHeight-8)}px`;}
    _setErrorOpen(open){const popover=this.querySelector('.error-popover'),trigger=this.querySelector('.error-trigger');popover.hidden=!open;trigger.classList.toggle('is-open',open);trigger.setAttribute('aria-expanded',String(open));this.querySelectorAll('[data-reason]').forEach(button=>button.setAttribute('aria-selected',String(button.classList.contains('is-selected'))));if(open)requestAnimationFrame(()=>this._positionErrorPopover());}
    _emitUpdate(){const data=this._segments[this._index-1];this.dispatchEvent(new CustomEvent('segment-update',{bubbles:true,detail:{index:this._index,error:data.error,unavailable:data.unavailable}}));}
    setSegment(index,emit=true){if(this.getAttribute('variant')==='variant-2'||this.getAttribute('variant')==='variant-3')return this._setSeveritySegment(index,emit);const safe=Math.max(1,Math.min(this._segments.length,Number(index)||1)),{start,end,duration,description,error,unavailable}=this._segments[safe-1];this._index=safe;this.querySelector('[data-number]').textContent=String(safe).padStart(2,'0');this.querySelector('[data-start]').textContent=start;this.querySelector('[data-end]').textContent=end;this.querySelector('[data-duration]').textContent=duration;this.querySelector('[data-description]').textContent=description;this.querySelector('[data-error]').textContent=error||'请选择错误原因';this.querySelector('.error-trigger').classList.toggle('is-placeholder',!error);this.querySelectorAll('[data-reason]').forEach(button=>button.classList.toggle('is-selected',button.dataset.reason===error));this._setUnavailable(unavailable,false);if(emit)this.dispatchEvent(new CustomEvent('segment-change',{bubbles:true,detail:{index:safe}}));}
  }

  const reviewSegments=[
    ['00:00','00:11','00:11','观察并整理桌面物品（前端测试V4 预标注片段 1）','片段范围错误'],
    ['00:11','00:15','00:04','选择错移动遥控器到目标位置（前端测试V4 预标注片段 2）','片段范围错位'],
    ['00:15','00:18','00:03','打开或关闭抽屉（前端测试V4 预标注片段 3）',''],
    ['00:18','00:21','00:03','调整纸盒摆放位置（前端测试V4 预标注片段 4）','动作结束边界偏晚'],
    ['00:21','00:27','00:06','将散落书本整理并竖直放回书架（前端测试V4 预标注片段 5）',''],
    ['00:27','00:32','00:05','将笔记本按类别放回指定位置（前端测试V4 预标注片段 6）','']
  ];

  function enableListResize(host,surface){
    host.style.position='relative';
    const handle=document.createElement('div');
    handle.className='workbench-list-resize';handle.tabIndex=0;
    handle.setAttribute('role','separator');handle.setAttribute('aria-orientation','vertical');
    handle.setAttribute('aria-label','调整列表宽度');handle.title='拖动调整宽度（320–600px）';
    host.append(handle);
    const limits=()=>{const available=host.parentElement.clientWidth;const max=Math.min(600,host.parentElement.classList.contains('main')?available-480:available);return {min:Math.min(320,Math.max(0,max)),max:Math.max(0,max)};};
    const update=value=>{const {min,max}=limits();const width=Math.max(min,Math.min(max,value));host.style.width=`${width}px`;host.style.flex=`0 0 ${width}px`;surface.style.width='100%';handle.setAttribute('aria-valuemin',min);handle.setAttribute('aria-valuemax',max);handle.setAttribute('aria-valuenow',Math.round(width));};
    let drag=null;
    handle.addEventListener('pointerdown',event=>{if(event.button!==0)return;event.preventDefault();drag={x:event.clientX,width:host.getBoundingClientRect().width};handle.classList.add('is-dragging');handle.setPointerCapture(event.pointerId);});
    handle.addEventListener('pointermove',event=>{if(drag)update(drag.width+drag.x-event.clientX);});
    const stop=event=>{drag=null;handle.classList.remove('is-dragging');if(handle.hasPointerCapture(event.pointerId))handle.releasePointerCapture(event.pointerId);};
    handle.addEventListener('pointerup',stop);handle.addEventListener('pointercancel',stop);
    handle.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const {min,max}=limits();update(event.key==='Home'?min:event.key==='End'?max:host.getBoundingClientRect().width+(event.key==='ArrowLeft'?16:-16));});
  }

  class WorkbenchSegmentListPanel extends HTMLElement{
    static get observedAttributes(){return ['variant'];}
    attributeChangedCallback(name,oldValue,newValue){
      if(name==='variant'&&oldValue!==newValue&&this.dataset.rendered==='true'&&!this.hasAttribute('hydrate'))this.setVariant(newValue,false);
    }
    connectedCallback(){
      if(this.dataset.rendered)return;
      if(this.hasAttribute('hydrate')){this.dataset.rendered='true';return;}
      this.dataset.rendered='true';
      this._segments=reviewSegments.map(item=>[...item]);
      this.innerHTML=`<section class="workbench-review__panel"><div class="workbench-review__content"><header class="workbench-review__header" data-review-title>片段列表</header><div class="workbench-review__list" data-workbench-review-view="segments"><button class="workbench-review__parent" type="button" aria-expanded="true"><span class="workbench-review__parent-index">01 <i>⌄</i></span><span class="workbench-review__parent-cell"><b>完成整段录制的前端测试V4预标注抽验任务</b><em>6 个子片段</em></span></button><div class="workbench-review__children"></div></div><div class="review-log" data-workbench-review-view="log" hidden><div class="review-log__summary"><span>当前数据处理记录</span><span>共 2 条</span></div><div class="review-log__table" aria-label="当前数据处理记录"><article class="review-log__card"><header><time>2026-08-03 10:42</time><span class="review-log__action">提交</span></header><dl><div><dt>操作人</dt><dd>供应商 A-017</dd></div><div><dt>节点</dt><dd>供应商抽验</dd></div><div><dt>说明</dt><dd>完成首次切分标注并提交</dd></div></dl></article><article class="review-log__card"><header><time>2026-08-03 11:02</time><span class="review-log__action">提交</span></header><dl><div><dt>操作人</dt><dd>供应商 A-017</dd></div><div><dt>节点</dt><dd>供应商抽验</dd></div><div><dt>说明</dt><dd>补充调整后再次提交</dd></div></dl></article></div></div><div class="review-info" data-workbench-review-view="info" hidden><dl class="review-info__list"><div><dt>任务 ID</dt><dd class="review-info__code">20455</dd></div><div><dt>处理任务</dt><dd>端到端切分标注供应商 A 任务</dd></div><div><dt>序列号</dt><dd class="review-info__code">UDAS-00002-2983</dd></div><div><dt>采集员</dt><dd>柳少龙</dd></div><div><dt>数据 ID</dt><dd class="review-info__code">3298698</dd></div><div><dt>版本</dt><dd>第1版</dd></div></dl></div></div></section>`;
      if(!this.closest('workbench-segment-list'))enableListResize(this,this.querySelector('.workbench-review__panel'));
      this.querySelectorAll('.review-log__card').forEach(card=>{
        const operatorRow=card.querySelector('dl > div');
        const nodeRow=operatorRow.nextElementSibling;
        const operator=document.createElement('span');operator.className='review-log__operator';
        operator.textContent=nodeRow.querySelector('dd').textContent;
        const header=card.querySelector('header');
        header.style.justifyContent='flex-start';
        header.append(operator);nodeRow.remove();
      });
      const logTable=this.querySelector('.review-log__table');
      const rejected=logTable.lastElementChild.cloneNode(true);
      rejected.classList.add('review-log__card--rejected');
      rejected.querySelector('time').textContent='2026-08-03 11:18';
      rejected.querySelector('.review-log__action').textContent='驳回';
      rejected.querySelector('.review-log__operator').textContent='内部验收';
      rejected.querySelector('dl > div dd').textContent='内部验收员 Aria';
      rejected.querySelector('dl > div:last-child dt').textContent='驳回原因';
      rejected.querySelector('dl > div:last-child dd').textContent='High-level片段范围需要调整，请修正动作起止边界后重新提交。';
      logTable.append(rejected);
      this.querySelector('.review-log__summary > span:last-child').textContent=`共 ${logTable.children.length} 条`;
      const taskHeader=document.querySelector('workbench-task-header');
      const information=[
        ['任务描述','归位书本与笔记本：将散落的书本和笔记本整理并放回书架指定位置，保持竖立排列或按类别分层摆放，便于查找和取用。'],
        ['数据 ID',taskHeader?.getAttribute('data-id')||'DT202609070126'],
        ['数据处理 ID',taskHeader?.getAttribute('data-processing-id')||'DP202609070018'],
        ['采集任务 ID','CT202608030042'],
        ['采集时间','2026-08-03 09:30:00'],
        ['采集员','柳少龙'],
        ['设备序列号','UDAS-00002-2983'],
        ['指令版本','v1.0'],
        ['处理任务 ID','20455'],
        ['标注流程','端到端切分标注简洁版'],
        ['标注规则','端到端切分标注规则 v1.0'],
        ['标注归档时间','未归档']
      ];
      const infoList=this.querySelector('.review-info__list');
      infoList.replaceChildren(...information.map(([label,value])=>{
        const row=document.createElement('div'),term=document.createElement('dt'),detail=document.createElement('dd');
        term.textContent=label;detail.textContent=value;
        if(label.includes('ID')||label==='设备序列号')detail.className='review-info__code';
        row.append(term,detail);return row;
      }));
      this._children=this.querySelector('.workbench-review__children');
      const listHeading=this.querySelector('[data-review-title]');
      listHeading.innerHTML='<span data-review-heading></span><span class="workbench-list-fold-actions"></span>';
      const foldButton=document.createElement('button');foldButton.type='button';
      const foldTip=document.createElement('span');foldTip.className='workbench-fold-tooltip';foldTip.setAttribute('popover','manual');foldTip.setAttribute('role','tooltip');listHeading.append(foldTip);
      const hideFoldTip=()=>{if(foldTip.matches(':popover-open'))foldTip.hidePopover();};
      const showFoldTip=()=>{
        foldTip.textContent=foldButton.dataset.tooltip;
        const rect=foldButton.getBoundingClientRect();
        foldTip.showPopover();
        const tipBounds=foldTip.getBoundingClientRect();
        foldTip.style.left=`${Math.max(4,Math.min(window.innerWidth-tipBounds.width-4,rect.left+(rect.width-tipBounds.width)/2))}px`;
        foldTip.style.top=`${Math.max(4,rect.top-tipBounds.height-6)}px`;
      };
      foldButton.addEventListener('mouseenter',showFoldTip);foldButton.addEventListener('mouseleave',hideFoldTip);
      foldButton.addEventListener('focus',showFoldTip);foldButton.addEventListener('blur',hideFoldTip);
      const updateFoldButton=()=>{
        const expanded=this._allDetails===true,label=expanded?'收起全部':'展开全部';
        foldButton.setAttribute('aria-label',label);foldButton.dataset.tooltip=label;foldButton.setAttribute('aria-expanded',String(expanded));
        foldTip.textContent=label;
        foldButton.innerHTML=`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${expanded?'m7 3 5 5 5-5M7 21l5-5 5 5':'m7 8 5-5 5 5M7 16l5 5 5-5'}"/></svg>`;
      };
      foldButton.addEventListener('click',()=>{
        this._allDetails=this._allDetails!==true;
        this._children.hidden=false;this.querySelector('.workbench-review__parent').setAttribute('aria-expanded','true');
        this.selectSegment(this._activeIndex,false);updateFoldButton();
      });
      updateFoldButton();listHeading.querySelector('.workbench-list-fold-actions').append(foldButton);
      this.selectSegment(2,false);
      const parent=this.querySelector('.workbench-review__parent');
      parent.addEventListener('click',()=>{const expanded=parent.getAttribute('aria-expanded')==='true';parent.setAttribute('aria-expanded',String(!expanded));this._children.hidden=expanded;});
      this.setVariant(this.getAttribute('variant')||'segments',false);
      this._segmentUpdate=event=>{const item=this._segments[event.detail?.index-1];if(!item||event.target.matches('workbench-segment-editor[variant]'))return;item[4]=event.detail.error||'';item[5]=Boolean(event.detail.unavailable);this.selectSegment(event.detail.index,false);};
      document.addEventListener('segment-update',this._segmentUpdate);
    }
    disconnectedCallback(){document.removeEventListener('segment-update',this._segmentUpdate);}
    get variant(){return this.getAttribute('variant')||'segments';}
    set variant(value){this.setAttribute('variant',this._normalizeVariant(value));}
    _normalizeVariant(value){return value==='log'||value==='info'?value:'segments';}
    setVariant(value,emit=true){
      if(!this.querySelector('[data-review-title]'))return;
      const variant=this._normalizeVariant(value);
      this.querySelector('[data-review-heading]').textContent={segments:'标注列表',log:'日志',info:'基本信息'}[variant];
      this.querySelector('.workbench-list-fold-actions').hidden=variant!=='segments';
      this.querySelectorAll('[data-workbench-review-view]').forEach(view=>{view.hidden=view.dataset.workbenchReviewView!==variant;});
      if(emit)this.dispatchEvent(new CustomEvent('review-variant-change',{bubbles:true,detail:{variant}}));
    }
    selectSegment(activeIndex,emit=true){
      this._activeIndex=activeIndex;
      this._children.innerHTML=this._segments.map(([start,end,duration,description,error,unavailable],index)=>`<button class="workbench-review__row${index+1===activeIndex?' is-active':''}" type="button" data-index="${index+1}"><span class="workbench-review__index">${String(index+1).padStart(2,'0')}</span><span class="workbench-review__cell">${(this._allDetails===true||(this._allDetails===undefined&&index+1===activeIndex))?`<span class="workbench-review__time"><span>${start}~${end}（${duration}）</span><img src="${assets}icon-trash.svg?v=2" alt="删除片段"></span>`:''}${unavailable?'':`<b>${escapeText(description)}</b>`}${error||unavailable?`<span class="workbench-review__tags">${unavailable?'<em class="workbench-review__unavailable">无法标注</em>':''}${error?`<em>错误原因：${escapeText(error)}</em>`:''}</span>`:''}</span></button>`).join('');
      this._children.querySelectorAll('.workbench-review__row').forEach(row=>row.addEventListener('click',()=>this.selectSegment(Number(row.dataset.index),true)));
      if(emit)this.dispatchEvent(new CustomEvent('segment-change',{bubbles:true,detail:{index:activeIndex}}));
    }
  }

  class WorkbenchFlatSegmentList extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      const title=this.getAttribute('title')||'片段列表';
      const count=Math.max(1,Number(this.getAttribute('rows')||3));
      this.innerHTML=`<section class="workbench-flat-list"><header class="workbench-flat-list__header">${title}</header><div class="workbench-flat-list__body">${Array.from({length:count},(_,index)=>`<button class="workbench-flat-list__row${index===1?' is-active':''}" type="button" data-index="${index+1}"><span class="workbench-flat-list__index">${String(index+1).padStart(2,'0')}</span><span class="workbench-flat-list__content">内容待补充</span></button>`).join('')}</div></section>`;
      this.querySelectorAll('.workbench-flat-list__row').forEach(row=>row.addEventListener('click',()=>this.selectSegment(Number(row.dataset.index),true)));
    }
    selectSegment(index,emit=true){
      const rows=[...this.querySelectorAll('.workbench-flat-list__row')];
      const safe=Math.max(1,Math.min(rows.length,Number(index)||1));
      rows.forEach(row=>row.classList.toggle('is-active',Number(row.dataset.index)===safe));
      if(emit)this.dispatchEvent(new CustomEvent('segment-change',{bubbles:true,detail:{index:safe}}));
    }
  }

  class WorkbenchAnnotationList extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      this._items=[
        {severity:'轻微',description:'动作开始位置略有偏差',reason:'动作开始边界偏早',start:'00:03',end:'00:07',duration:'00:04'},
        {severity:'严重',description:'遥控器未移动到目标位置',reason:'片段范围错位',start:'00:11',end:'00:15',duration:'00:04'},
        {severity:'轻微',description:'动作结束后保留了多余画面',reason:'动作结束边界偏晚',start:'00:18',end:'00:21',duration:'00:03'},
        {severity:'轻微',description:'抓取过程中手部短暂停顿',reason:'',start:'00:24',end:'00:29',duration:'00:05'},
        {severity:'严重',description:'物品放置方向与要求不一致',reason:'动作执行错误',start:'00:33',end:'00:39',duration:'00:06'},
        {severity:'轻微',description:'完成动作后未及时收回手臂',reason:'',start:'00:42',end:'00:46',duration:'00:04'}
      ];
      this._activeIndex=0;
      this.render();
    }
    render(){
      const title=this.getAttribute('title')||'标注列表';
      this.innerHTML=`<section class="workbench-flat-list workbench-annotation-list"><header class="workbench-flat-list__header">${title}</header><div class="workbench-flat-list__body">${this._items.map((item,index)=>`<article class="workbench-flat-list__row workbench-annotation-list__row${index+1===this._activeIndex?' is-active':''}" data-index="${index+1}" tabindex="0"><span class="workbench-flat-list__index">${String(index+1).padStart(2,'0')}</span><span class="workbench-flat-list__content">${index+1===this._activeIndex?`<span class="workbench-annotation-list__time"><span>${item.start}~${item.end}（${item.duration}）</span><button type="button" class="workbench-annotation-list__delete" aria-label="删除标注"><img src="${assets}icon-trash.svg?v=2" alt=""></button></span>`:''}<span class="workbench-annotation-list__summary"><b class="workbench-annotation-list__severity${item.severity==='严重'?' is-severe':''}">${escapeText(item.severity)}</b><span class="workbench-annotation-list__description">${escapeText(item.description)}</span></span>${item.reason?`<em class="workbench-annotation-list__tag">错误原因：${escapeText(item.reason)}</em>`:''}</span></article>`).join('')}</div></section>`;
      this.querySelectorAll('.workbench-annotation-list__row').forEach(row=>{
        row.addEventListener('click',()=>this.selectSegment(Number(row.dataset.index),true));
        row.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();this.selectSegment(Number(row.dataset.index),true);}});
      });
      this.querySelectorAll('.workbench-annotation-list__delete').forEach(button=>button.addEventListener('click',event=>{
        event.stopPropagation();
        const row=button.closest('.workbench-annotation-list__row');
        const removedIndex=Number(row.dataset.index);
        this._items.splice(removedIndex-1,1);
        this._activeIndex=0;
        this.render();
        this.dispatchEvent(new CustomEvent('segment-delete',{bubbles:true,detail:{index:removedIndex}}));
      }));
    }
    selectSegment(index,emit=true){
      const safe=Math.max(1,Math.min(this._items.length,Number(index)||1));
      this._activeIndex=safe;
      this.render();
      if(emit)this.dispatchEvent(new CustomEvent('segment-change',{bubbles:true,detail:{index:safe}}));
    }
  }
  class WorkbenchQualityList extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      this._items=[
        {color:'#55bce5',elements:['书本','桌面'],description:'观察并整理桌面物品',reason:'片段范围错误',start:'00:00',end:'00:11',duration:'00:11'},
        {color:'#ff9254',elements:['遥控器'],description:'选择并移动遥控器到目标位置',reason:'片段范围错位',start:'00:11',end:'00:15',duration:'00:04'},
        {color:'#8d52ca',elements:['抽屉','把手'],description:'打开或关闭抽屉',reason:'',start:'00:15',end:'00:18',duration:'00:03'},
        {color:'#50bf83',elements:['纸盒'],description:'调整纸盒摆放位置',reason:'动作结束边界偏晚',start:'00:18',end:'00:21',duration:'00:03'},
        {color:'#8cc84b',elements:['书本','书架'],description:['整理散落书本','将书本竖直放回书架'],reason:'动作执行错误',start:'00:21',end:'00:28',duration:'00:07'},
        {color:'#c99a38',elements:['笔记本'],description:['按类别整理笔记本','放回指定位置'],reason:'',start:'00:28',end:'00:34',duration:'00:06'}
      ];
      this._activeIndex=0;
      this.render();
      this._actionAnnotationChange=event=>{const item=this._items[event.detail?.index-1];if(!item)return;item.elements=[...event.detail.elements];item.description=[...event.detail.descriptions];this.render();};
      this._segmentUpdate=event=>{if(event.target?.getAttribute?.('variant')!=='variant-3')return;const item=this._items[event.detail?.index-1];if(!item)return;item.reason=event.detail.error||'';this.render();};
      document.addEventListener('action-annotation-change',this._actionAnnotationChange);
      document.addEventListener('segment-update',this._segmentUpdate);
    }
    disconnectedCallback(){document.removeEventListener('action-annotation-change',this._actionAnnotationChange);document.removeEventListener('segment-update',this._segmentUpdate);}
    render(){
      const title=this.getAttribute('title')||'质检列表';
      this.innerHTML=`<section class="workbench-flat-list workbench-quality-list"><header class="workbench-flat-list__header">${title}</header><div class="workbench-flat-list__body">${this._items.map((item,index)=>`<article class="workbench-flat-list__row workbench-quality-list__row${index+1===this._activeIndex?' is-active':''}" data-index="${index+1}" tabindex="0"><span class="workbench-flat-list__index">${String(index+1).padStart(2,'0')}</span><span class="workbench-flat-list__content">${index+1===this._activeIndex?`<span class="workbench-quality-list__time"><span>${item.start}~${item.end}（${item.duration}）</span><button type="button" class="workbench-quality-list__delete" aria-label="删除标注"><img src="${assets}icon-trash.svg?v=2" alt=""></button></span>`:''}<span class="workbench-quality-list__summary"><span class="workbench-quality-list__element-line"><i class="workbench-quality-list__color" style="--quality-color:${item.color}" aria-label="颜色 ${item.color}"></i><span class="workbench-quality-list__elements">${item.elements.map(name=>`<span class="workbench-quality-list__element">${escapeText(name)}</span>`).join('')}</span></span><span class="workbench-quality-list__description">${escapeText(Array.isArray(item.description)?item.description.join('、'):item.description)}</span><span class="workbench-quality-list__preview"><img class="workbench-quality-list__thumbnail" src="${assets}frame.png" alt="动作片段缩略图">${item.reason?`<em class="workbench-quality-list__reason">错误原因：${escapeText(item.reason)}</em>`:''}</span></span></span></article>`).join('')}</div></section>`;
      this.querySelectorAll('.workbench-quality-list__row').forEach(row=>{
        row.addEventListener('click',()=>this.selectSegment(Number(row.dataset.index),true));
        row.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();this.selectSegment(Number(row.dataset.index),true);}});
      });
      this.querySelectorAll('.workbench-quality-list__delete').forEach(button=>button.addEventListener('click',event=>{
        event.stopPropagation();
        const row=button.closest('.workbench-quality-list__row');
        const removedIndex=Number(row.dataset.index);
        this._items.splice(removedIndex-1,1);
        this._activeIndex=0;
        this.render();
        this.dispatchEvent(new CustomEvent('segment-delete',{bubbles:true,detail:{index:removedIndex}}));
      }));
    }
    selectSegment(index,emit=true){
      const safe=Math.max(1,Math.min(this._items.length,Number(index)||1));
      this._activeIndex=safe;
      this.render();
      if(emit)this.dispatchEvent(new CustomEvent('segment-change',{bubbles:true,detail:{index:safe}}));
    }
  }

  class WorkbenchSegmentTabs extends HTMLElement{
    static get observedAttributes(){return ['active'];}
    attributeChangedCallback(name,oldValue,newValue){if(name==='active'&&oldValue!==newValue&&this.dataset.rendered==='true')this.setActive(newValue,false);}
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      this.innerHTML='<nav class="workbench-review__tabs" aria-label="复核侧栏"><button type="button" data-review-variant="quality">质检</button><button type="button" data-review-variant="segments">语义标注</button><button type="button" data-review-variant="action">动作标注</button><button type="button" data-review-variant="tags">标签</button><button type="button" data-review-variant="log">日志</button><button type="button" data-review-variant="info">基本信息</button></nav>';
      this.querySelectorAll('[data-review-variant]').forEach(tab=>tab.addEventListener('click',()=>this.setActive(tab.dataset.reviewVariant,true)));
      this.setActive(this.getAttribute('active')||'segments',false);
    }
    _normalize(value){return value==='quality'||value==='action'||value==='tags'||value==='log'||value==='info'?value:'segments';}
    setActive(value,emit=true){const active=this._normalize(value);if(this.getAttribute('active')!==active)this.setAttribute('active',active);this.querySelectorAll('[data-review-variant]').forEach(tab=>{const selected=tab.dataset.reviewVariant===active;tab.classList.toggle('is-active',selected);tab.setAttribute('aria-pressed',String(selected));});if(emit)this.dispatchEvent(new CustomEvent('review-variant-change',{bubbles:true,detail:{variant:active}}));}
  }

  class WorkbenchSegmentList extends HTMLElement{
    static get observedAttributes(){return ['variant'];}
    attributeChangedCallback(name,oldValue,newValue){if(name==='variant'&&oldValue!==newValue&&this.dataset.rendered==='true'&&!this.hasAttribute('hydrate'))this.setVariant(newValue,false);}
    connectedCallback(){
      if(this.dataset.rendered)return;
      if(this.hasAttribute('hydrate')){this.dataset.rendered='true';return;}
      this.dataset.rendered='true';
      const variant=this._normalizeVariant(this.getAttribute('variant'));
      this.innerHTML=`<aside class="workbench-review"><div class="workbench-review__main"><workbench-segment-list-panel variant="${variant}"></workbench-segment-list-panel><workbench-annotation-list title="质检列表" data-quality-list hidden></workbench-annotation-list><workbench-quality-list title="标注列表" data-action-list hidden></workbench-quality-list><div class="workbench-quality-actions" data-quality-actions hidden><workbench-quality-conclusion></workbench-quality-conclusion><workbench-footer-actions variant="quality"></workbench-footer-actions></div><workbench-footer-actions></workbench-footer-actions></div><div class="workbench-review__rail"><workbench-segment-tabs active="${variant}"></workbench-segment-tabs><div class="workbench-theme-tabs" role="group" aria-label="工作台主题"><button type="button" data-theme="dark" title="深色" aria-label="深色"><span class="workbench-theme-switch__moon" aria-hidden="true"></span></button><button type="button" data-theme="blue" title="深蓝" aria-label="深蓝"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m10 2 7 4-7 4-7-4 7-4Zm-7 8 7 4 7-4M3 14l7 4 7-4"/></svg></button><button type="button" data-theme="light" title="浅色" aria-label="浅色"><span class="workbench-theme-switch__sun" aria-hidden="true"></span></button></div></div></aside>`;
      this._panel=this.querySelector('workbench-segment-list-panel');
      enableListResize(this,this.querySelector('.workbench-review'));
      this._quality=this.querySelector('[data-quality-list]');
      this._action=this.querySelector('[data-action-list]');
      this._qualityActions=this.querySelector('[data-quality-actions]');
      this._tabs=this.querySelector('workbench-segment-tabs');
      this._footer=this.querySelector('.workbench-review__main > workbench-footer-actions');
      this._themeSwitch=this.querySelector('.workbench-theme-tabs');
      this._tabs.addEventListener('review-variant-change',event=>{event.stopPropagation();this.setVariant(event.detail.variant,false);this.dispatchEvent(new CustomEvent('review-variant-change',{bubbles:true,detail:event.detail}));});
      this._themeSwitch.addEventListener('click',event=>{const button=event.target.closest('[data-theme]');if(button)this._setPageTheme(button.dataset.theme,true);});
      this._syncThemeSwitch();
    }
    get variant(){return this.getAttribute('variant')||'segments';}
    set variant(value){this.setAttribute('variant',this._normalizeVariant(value));}
    _normalizeVariant(value){return value==='quality'||value==='action'||value==='tags'||value==='log'||value==='info'?value:'segments';}
    setVariant(value,emit=true){const variant=this._normalizeVariant(value);if(this.getAttribute('variant')!==variant)this.setAttribute('variant',variant);const quality=variant==='quality',action=variant==='action';if(this._panel){this._panel.hidden=quality||action||variant==='tags';if(!quality&&!action&&variant!=='tags')this._panel.setVariant(variant,false);}if(this._quality)this._quality.hidden=!quality;if(this._action)this._action.hidden=!action;if(this._qualityActions)this._qualityActions.hidden=!quality;this._tabs?.setActive(variant,false);if(this._footer)this._footer.hidden=quality||variant==='log'||variant==='info';if(emit)this.dispatchEvent(new CustomEvent('review-variant-change',{bubbles:true,detail:{variant}}));}
    _setPageTheme(theme,persist){applyWorkbenchTheme(theme,persist);}
    _syncThemeSwitch(){if(!this._themeSwitch)return;let theme=document.documentElement.dataset.workbenchTheme||(document.body.classList.contains('theme-light')?'light':'dark');try{theme=localStorage.getItem(document.body.classList.contains('component-preview')?'workbench-component-theme':'workbench-theme')||theme;}catch(_){}applyWorkbenchTheme(theme,false);}

    selectSegment(index,emit=true){if(this.variant==='quality')this._quality?.selectSegment(index,emit);else if(this.variant==='action')this._action?.selectSegment(index,emit);else this._panel?.selectSegment(index,emit);}
  }

  class WorkbenchConfirmDialog extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      const variant=['unqualified','reject','task-description','standards'].includes(this.getAttribute('variant'))?this.getAttribute('variant'):'submit';
      const rejectId=`reject-reason-${Math.random().toString(36).slice(2)}`;
      const header=title=>`<header><h2>${title}</h2><button type="button" data-dialog-action="close" aria-label="关闭">×</button></header>`;
      const actions=(confirm='确定',single=false)=>`<footer>${single?'':`<button type="button" data-dialog-action="cancel">取消</button>`}<button type="button" data-dialog-action="confirm">${confirm}</button></footer>`;
      const content=variant==='unqualified'
        ?`${header('提示')}<div class="workbench-submit-dialog__body"><span class="workbench-submit-dialog__icon is-warning" aria-hidden="true">!</span><p>是否将此条数据判定为不合格数据？</p></div>${actions()}`
        :variant==='reject'
          ?`${header('错误原因')}<div class="workbench-submit-dialog__reject"><div><textarea id="${rejectId}" aria-label="错误原因" maxlength="500" placeholder="请输入错误原因（可选）"></textarea><span><b>0</b> / 500</span></div></div>${actions('确定驳回')}`
          :variant==='task-description'
            ?`${header('任务描述')}<div class="workbench-submit-dialog__task-description"><p>归位书本与笔记本：将散落的书本和笔记本整理并放回书架指定位置，保持竖立排列或按类别分层摆放，便于查找和取用。</p></div>${actions('我已了解',true)}`
          :variant==='standards'
            ?`${header('质检标准')}<div class="workbench-submit-dialog__standards"><section><h3><i>✓</i>失误标准</h3><ol><li>夹爪超出画面（自动化）</li><li>采集动作不规范：手部脱离夹爪（自动化）</li><li>采集动作不规范：其它身体部位辅助</li><li>画面异常：全程部分遮挡/部分时间完全遮挡</li></ol></section><section><h3><i>×</i>不合格标准</h3><ol><li>一致性检测（自动化）</li><li>改造设备（自动化）</li><li>采集时长不足（自动化）</li><li>视频损坏（自动化）</li><li>相机卡死（自动化）</li><li>画面异常：全程完全遮挡（自动化）</li><li>设备穿戴不规范（全程）（自动化）</li><li>改造设备进行采集（自动化）</li><li>头显穿戴不规范（全程）</li></ol></section></div>${actions('我已了解',true)}`
            :`${header('提示')}<div class="workbench-submit-dialog__body"><span class="workbench-submit-dialog__icon" aria-hidden="true"></span><p>确定要提交当前标注吗？</p></div>${actions()}`;
      this.innerHTML=`<dialog class="workbench-submit-dialog workbench-submit-dialog--${variant}" aria-label="${variant==='standards'?'质检标准':variant==='reject'?'驳回原因':variant==='task-description'?'任务描述':'确认提示'}">${content}</dialog>`;
      this._dialog=this.querySelector('dialog');
      if(this.hasAttribute('preview'))this._dialog.setAttribute('open','');
      const textarea=this.querySelector('textarea'),counter=this.querySelector('.workbench-submit-dialog__reject b');
      textarea?.addEventListener('input',()=>{counter.textContent=String(textarea.value.length);});
      this.addEventListener('click',event=>{
        const action=event.target.closest('[data-dialog-action]')?.dataset.dialogAction;
        if(action==='close'||action==='cancel'){this.close();return;}
        if(action==='confirm'){this.close();this.dispatchEvent(new CustomEvent('confirm-dialog-confirm',{bubbles:true,detail:{variant,value:textarea?.value||''}}));return;}
        if(event.target===this._dialog&&!this.hasAttribute('preview'))this.close();
      });
    }
    show(){if(!this._dialog.open)this._dialog.showModal();}
    close(){if(this.hasAttribute('preview'))return;if(this._dialog.open)this._dialog.close();}
  }

  class WorkbenchShortcutDialog extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      const platform=this.getAttribute('platform')==='windows'?'windows':'mac';
      const items=platform==='windows'?windowsShortcutItems:macShortcutItems;
      this.innerHTML=`<section class="workbench-shortcut-dialog__panel" aria-label="${platform==='windows'?'Windows':'Mac'} 分割模式快捷键"><strong>分割模式快捷键</strong><div class="workbench-shortcut-dialog__list">${items.map(([name,key])=>`<div><span>${escapeText(name)}</span><kbd>${key}</kbd></div>`).join('')}</div></section>`;
    }
  }

  class WorkbenchFooterActions extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      if(this.hasAttribute('hydrate')){this.dataset.rendered='true';return;}
      this.dataset.rendered='true';
      const quality=this.getAttribute('variant')==='quality';
      this.innerHTML=`<footer class="workbench-footer-actions"><button type="button" data-action="submit">提交</button><button type="button" data-action="${quality?'leave':'reject'}">${quality?'暂离':'驳回'}</button><button type="button" data-action="save">保存</button></footer><workbench-confirm-dialog></workbench-confirm-dialog>`;
      this._dialog=this.querySelector('workbench-confirm-dialog');
      this._dialog.addEventListener('confirm-dialog-confirm',event=>{event.stopPropagation();this.dispatchEvent(new CustomEvent('workbench-action',{bubbles:true,detail:{action:'submit'}}));});
      this.addEventListener('click',event=>{
        const button=event.target.closest('button[data-action]');
        if(!button)return;
        if(button.dataset.action==='submit'){this._dialog.show();return;}
        this.dispatchEvent(new CustomEvent('workbench-action',{bubbles:true,detail:{action:button.dataset.action}}));
      });
    }
  }

  class WorkbenchQualityConclusion extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      this.innerHTML=`<div class="workbench-quality-conclusion"><label for="quality-conclusion-select">质检结论</label><span class="workbench-quality-conclusion__control"><select id="quality-conclusion-select" aria-label="质检结论"><option value="合格">合格</option><option value="不合格" selected>不合格</option></select><img src="${assets}icon-chevron.svg" alt=""></span></div>`;
      this.querySelector('select').addEventListener('change',event=>this.dispatchEvent(new CustomEvent('quality-conclusion-change',{bubbles:true,detail:{value:event.target.value}})));
    }
  }

  class WorkbenchQualityTrack extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      this.innerHTML='<section class="segmented-timeline segmented-timeline--quality" style="--play-position:.18"><div class="segmented-timeline__body"><timeline-range-selector variant="marked"></timeline-range-selector><i class="segmented-timeline__playhead" role="slider" aria-label="播放位置" aria-valuemin="0" aria-valuemax="100" aria-valuenow="18" tabindex="0"></i></div><timeline-controls standard-label="质检标准"></timeline-controls></section>';
      requestAnimationFrame(()=>this._connectInteractions());
    }
    _connectInteractions(){
      const section=this.querySelector('.segmented-timeline');
      const ruler=this.querySelector('timeline-range-selector');
      const rail=ruler._rail;
      const playhead=this.querySelector('.segmented-timeline__playhead');
      const controls=this.querySelector('timeline-controls');
      const snapPoints=[0,17.8,33.7,47.5,55.5,65.5,76.5,100];
      ruler.setSnapPoints(snapPoints);
      const playbackStart=0,playbackEnd=100;
      let playPercent=playbackStart;
      let dragging=false,moved=false,startX=0;
      const setPlayPercent=(value,snap=false)=>{
        const bounds=rail.getBoundingClientRect();
        let percent=Math.max(0,Math.min(100,value));
        const threshold=bounds.width?8/bounds.width*100:0;
        const nearest=snapPoints.reduce((best,point)=>Math.abs(point-percent)<Math.abs(best-percent)?point:best,snapPoints[0]);
        const snapped=snap&&Math.abs(nearest-percent)<=threshold;
        if(snapped)percent=nearest;
        playPercent=percent;
        section.style.setProperty('--play-position',percent/100);
        playhead.classList.toggle('is-snapped',snapped);
        playhead.setAttribute('aria-valuenow',String(Math.round(percent)));
        controls.setCurrentTime(percent);
        this.dispatchEvent(new CustomEvent('playhead-change',{bubbles:true,detail:{percent}}));
      };
      const setPlayPosition=clientX=>{const bounds=rail.getBoundingClientRect();setPlayPercent((clientX-bounds.left)/bounds.width*100,true);};
      const selectRange=(start,end)=>{
        ruler.setRange(start,end,true);
      };
      this.querySelector('.segmented-timeline__range-fragment.is-orange')?.addEventListener('click',()=>selectRange(47.5,55.5));
      this.querySelector('.segmented-timeline__range-fragment.is-red')?.addEventListener('click',()=>selectRange(65.5,76.5));
      playhead.addEventListener('pointerdown',event=>{event.preventDefault();dragging=true;moved=false;startX=event.clientX;playhead.setPointerCapture(event.pointerId);playhead.classList.add('is-dragging');});
      playhead.addEventListener('pointermove',event=>{if(!dragging)return;if(Math.abs(event.clientX-startX)>2)moved=true;setPlayPosition(event.clientX);});
      playhead.addEventListener('pointerup',event=>{if(!dragging)return;dragging=false;playhead.classList.remove('is-dragging','is-snapped');if(playhead.hasPointerCapture(event.pointerId))playhead.releasePointerCapture(event.pointerId);});
      playhead.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const percent=event.key==='Home'?0:event.key==='End'?100:playPercent+(event.key==='ArrowLeft'?-1:1);setPlayPercent(percent,true);});
      let playing=false,lastFrame=0;
      const animate=now=>{if(!playing)return;if(lastFrame)setPlayPercent(Math.min(playbackEnd,playPercent+(now-lastFrame)/900),false);lastFrame=now;if(playPercent>=playbackEnd){playing=false;controls.setPlaying(false);return;}requestAnimationFrame(animate);};
      controls.addEventListener('play-toggle',event=>{playing=event.detail.playing;if(playing){if(playPercent<playbackStart||playPercent>=playbackEnd)setPlayPercent(playbackStart,false);lastFrame=0;requestAnimationFrame(animate);}});
      setPlayPercent(playbackStart,false);
    }
  }

  class SegmentedTrack extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered="true";
      const position=Math.max(0,Math.min(100,Number(this.getAttribute('position')||19)))/100;
      const action=this.getAttribute('variant')==='action';
      this.innerHTML=`<section class="segmented-timeline" aria-label="${action?'动作标注':'语义标注'}" style="--play-position:${position}"><div class="segmented-timeline__body"><timeline-time-scale></timeline-time-scale><timeline-range-selector></timeline-range-selector><annotation-segment-row label="${this.getAttribute('label')||'14'}"></annotation-segment-row>${action?'':'<annotation-base-row label="1"></annotation-base-row>'}<i class="segmented-timeline__playhead" role="slider" aria-label="播放位置" tabindex="0"></i></div><timeline-controls></timeline-controls></section>`;
      requestAnimationFrame(()=>this._connectInteractions());
    }
    _connectInteractions(){
      const section=this.querySelector('.segmented-timeline');
      const ruler=this.querySelector('timeline-range-selector');
      const row=this.querySelector('annotation-segment-row');
      row._setupMerge();
      if(this.hasAttribute('split-lane')){
        if(this.hasAttribute('split-lane-preview')){
          // Seed real split groups so the preview uses the same rendering and editing path.
          const previewGroups=[0,0,0,1,1,2,2,2,3,3,4,4,4,4];
          row.buttons.forEach((button,index)=>{
            const group=previewGroups[index];
            if(group==null)return;
            button.dataset.splitGroup=`preview-${group}`;
            button.dataset.splitColorIndex=String(group);
            button.dataset.splitColor=splitLaneColors[group%splitLaneColors.length];
          });
        }
        const lane=document.createElement('div');lane.className='segmented-timeline__row segmented-timeline__split-lane';lane.hidden=true;
        row.after(lane);
        const renderLane=()=>{
          const rail=row.querySelector('.segmented-timeline__track').getBoundingClientRect();
          if(!rail.width)return;
          const groups=new Map();
          row.buttons.forEach(button=>{
            const id=button.dataset.splitGroup;if(!id)return;
            const box=button.getBoundingClientRect();
            const group=groups.get(id)||{left:box.left,right:box.right,color:button.dataset.splitColor||splitLaneColors[0]};
            group.left=Math.min(group.left,box.left);group.right=Math.max(group.right,box.right);groups.set(id,group);
          });
          lane.replaceChildren();lane.hidden=!groups.size;this.classList.toggle('has-split-lane',Boolean(groups.size));
          const count=document.createElement('span');count.className='segmented-timeline__index';count.textContent=groups.size;
          const laneTrack=document.createElement('div');laneTrack.className='segmented-timeline__track';
          lane.append(count,laneTrack);
          groups.forEach(group=>{
            const bar=document.createElement('span');bar.className='segmented-timeline__split-group';bar.setAttribute('aria-label','分割范围');
            bar.style.left=`${(group.left-rail.left)/rail.width*100}%`;bar.style.width=`${(group.right-group.left)/rail.width*100}%`;bar.style.setProperty('--group-color',group.color);laneTrack.append(bar);
          });
        };
        ['segments-split','segments-merge','segments-undo'].forEach(name=>this.addEventListener(name,()=>requestAnimationFrame(renderLane)));
        const laneObserver=new ResizeObserver(renderLane);laneObserver.observe(row);
      }
      const splitPreview=document.createElement('div');
      splitPreview.className='segmented-timeline__split-preview';splitPreview.hidden=true;
      splitPreview.innerHTML='<span class="segmented-timeline__split-time"></span><i></i><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="7" r="3"/><circle cx="5" cy="17" r="3"/><path d="m8 8 13 9M8 16 13 12 21 7"/></svg>';
      row.querySelector('.segmented-timeline__row').append(splitPreview);
      let splitMode=false;
      this.addEventListener('tool-mode-change',event=>{splitMode=event.detail.mode==='分割'||event.detail.mode==='父级分割';splitPreview.hidden=true;row.classList.toggle('is-splitting',splitMode);});
      row.addEventListener('pointermove',event=>{
        if(!splitMode||!event.target.closest('.segmented-timeline__track')){splitPreview.hidden=true;return;}
        const bounds=row.querySelector('.segmented-timeline__track').getBoundingClientRect();
        const x=Math.max(0,Math.min(bounds.width,event.clientX-bounds.left));
        splitPreview.style.left=`${x}px`;
        splitPreview.querySelector('span').textContent=`${(x/bounds.width*70).toFixed(2)}s`;
        splitPreview.hidden=false;
      });
      row.addEventListener('pointerleave',()=>{splitPreview.hidden=true;});
      this.querySelector('timeline-controls').addEventListener('click',event=>{
        const button=event.target.closest('button');
        if(!button||button.disabled)return;
        const label=button.getAttribute('aria-label');
        if(label==='合并')row.mergeSelection();
        if(label==='向上合并')row.mergeAdjacent(-1);
        if(label==='向下合并')row.mergeAdjacent(1);
      });
      const track=row.querySelector('.segmented-timeline__track');
      const playhead=this.querySelector('.segmented-timeline__playhead');
      const controls=this.querySelector('timeline-controls');
      const syncGeometry=()=>{
        const bounds=track.getBoundingClientRect();
        const points=[];
        const boxes=row.buttons.map(button=>button.getBoundingClientRect());
        for(let index=0;index<boxes.length-1;index+=1){
          const connection=(boxes[index].right+boxes[index+1].left)/2;
          points.push((connection-bounds.left)/bounds.width*100);
        }
        ruler.setSnapPoints(points);
      };
      let playbackStart=0,playbackEnd=100;
      const syncRange=(index,emit=true,movePlayhead=false)=>{
        syncGeometry();
        const rail=ruler._rail.getBoundingClientRect();
        const box=row.buttons[index].getBoundingClientRect();
        const start=(box.left-rail.left)/rail.width*100;
        const end=(box.right-rail.left)/rail.width*100;
        playbackStart=start;playbackEnd=end;
        ruler.setRange(start,end,false);
        if(movePlayhead)setPlayPercent(start,false);
        if(emit)this.dispatchEvent(new CustomEvent('track-change',{bubbles:true,detail:{index,start:ruler._start,end:ruler._end,source:'segment'}}));
      };
      this._row=row;this._syncRange=syncRange;
      syncGeometry();
      row.addEventListener('segment-select',event=>{syncRange(event.detail.index,true,true);controls.setPlaying(false);controls.dispatchEvent(new CustomEvent('play-toggle',{bubbles:true,detail:{playing:false}}));});
      ruler.addEventListener('range-change',event=>{
        playbackStart=event.detail.start;playbackEnd=event.detail.end;
        if(['start','end','fill'].includes(event.detail.dragMode)){
          controls.setPlaying(false);
          controls.dispatchEvent(new CustomEvent('play-toggle',{bubbles:true,detail:{playing:false}}));
        }
        const activeIndex=row.buttons.findIndex(button=>button.classList.contains('is-active'));
        const index=activeIndex<0?0:activeIndex;
        this.dispatchEvent(new CustomEvent('track-range-change',{bubbles:true,detail:{...event.detail,index}}));
        this.dispatchEvent(new CustomEvent('track-change',{bubbles:true,detail:{...event.detail,index,source:'range'}}));
      });
      let dragging=false,moved=false,startX=0;
      let playPercent=Math.max(0,Math.min(100,Number(this.getAttribute('position')||19)));
      const setPlayPercent=(value,snap=false)=>{
        const bounds=track.getBoundingClientRect();
        const points=ruler._snapPoints;
        let percent=Math.max(0,Math.min(100,value));
        const threshold=8/bounds.width*100;
        const nearest=points.length?points.reduce((best,point)=>Math.abs(point-percent)<Math.abs(best-percent)?point:best,points[0]):percent;
        const snapped=snap&&points.length>0&&Math.abs(nearest-percent)<=threshold;
        if(snapped)percent=nearest;
        playPercent=percent;
        section.style.setProperty('--play-position',percent/100);
        playhead.classList.toggle('is-snapped',snapped);
        playhead.setAttribute('aria-valuenow',String(Math.round(percent)));
        controls.setCurrentTime(percent);
        this.dispatchEvent(new CustomEvent('playhead-change',{bubbles:true,detail:{percent}}));
      };
      const setPlayPosition=clientX=>{const bounds=track.getBoundingClientRect();setPlayPercent((clientX-bounds.left)/bounds.width*100,true);};
      let railClick=null;
      ruler._rail.addEventListener('pointerdown',event=>{
        railClick=event.button===0&&!event.target.closest('.segmented-timeline__range-handle')?{id:event.pointerId,x:event.clientX,y:event.clientY,moved:false}:null;
      },true);
      ruler._rail.addEventListener('pointermove',event=>{
        if(railClick&&event.pointerId===railClick.id&&Math.hypot(event.clientX-railClick.x,event.clientY-railClick.y)>3)railClick.moved=true;
      },true);
      ruler._rail.addEventListener('pointerup',event=>{
        if(railClick&&event.pointerId===railClick.id&&!railClick.moved){const bounds=ruler._rail.getBoundingClientRect();if(bounds.width){controls.setPlaying(false);controls.dispatchEvent(new CustomEvent('play-toggle',{bubbles:true,detail:{playing:false}}));setPlayPercent((event.clientX-bounds.left)/bounds.width*100,false);}}
        railClick=null;
      },true);
      ruler._rail.addEventListener('pointercancel',()=>{railClick=null;});
      playhead.addEventListener('pointerdown',event=>{event.preventDefault();controls.setPlaying(false);controls.dispatchEvent(new CustomEvent('play-toggle',{bubbles:true,detail:{playing:false}}));dragging=true;moved=false;startX=event.clientX;playhead.setPointerCapture(event.pointerId);playhead.classList.add('is-dragging');});
      playhead.addEventListener('pointermove',event=>{
        if(!dragging)return;
        if(Math.abs(event.clientX-startX)>2)moved=true;
        setPlayPosition(event.clientX);
      });
      playhead.addEventListener('pointerup',event=>{if(!dragging)return;dragging=false;playhead.classList.remove('is-dragging','is-snapped');if(playhead.hasPointerCapture(event.pointerId))playhead.releasePointerCapture(event.pointerId);});
      playhead.addEventListener('keydown',event=>{
        if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
        event.preventDefault();
        const current=Number(playhead.getAttribute('aria-valuenow')||Number(this.getAttribute('position')||19));
        const percent=event.key==='Home'?0:event.key==='End'?100:current+(event.key==='ArrowLeft'?-1:1);
        const bounds=track.getBoundingClientRect();
        setPlayPosition(bounds.left+bounds.width*Math.max(0,Math.min(100,percent))/100);
      });
      playhead.setAttribute('aria-valuemin','0');
      playhead.setAttribute('aria-valuemax','100');
      playhead.setAttribute('aria-valuenow',String(Math.round(Number(this.getAttribute('position')||19))));
      let playing=false,lastFrame=0,activePlaybackEnd=100;
      const animate=now=>{if(!playing)return;if(lastFrame)setPlayPercent(Math.min(activePlaybackEnd,playPercent+(now-lastFrame)/900),false);lastFrame=now;if(playPercent>=activePlaybackEnd){playing=false;controls.setPlaying(false);return;}requestAnimationFrame(animate);};
      controls.addEventListener('play-toggle',event=>{playing=event.detail.playing;if(playing){const rangeStart=ruler._start,rangeEnd=ruler._end;activePlaybackEnd=playPercent>=rangeStart&&playPercent<rangeEnd?rangeEnd:100;lastFrame=0;requestAnimationFrame(animate);}});
      controls.setCurrentTime(playPercent);
      const resizeObserver=new ResizeObserver(()=>{syncGeometry();});
      resizeObserver.observe(track);
      syncRange(0,false,true);
    }
    selectSegment(index,emit=true){if(!this._row||!this._syncRange){requestAnimationFrame(()=>this.selectSegment(index,emit));return;}const safe=Math.max(0,Math.min(this._row.buttons.length-1,Number(index)||0));this._row.selectIndex(safe,false);this._syncRange(safe,emit,true);}
  }

  class SemanticAnnotationTrack extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      this.innerHTML=`<segmented-track label="${this.getAttribute('label')||'14'}" position="${this.getAttribute('position')||'19'}"></segmented-track>`;
    }
    selectSegment(index,emit=true){this.querySelector('segmented-track')?.selectSegment(index,emit);}
  }

  class ActionAnnotationTrack extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      const variant=this.getAttribute('variant');
      this.innerHTML=`<segmented-track variant="action" ${['split-lane','split-lane-preview'].includes(variant)?'split-lane':''} ${variant==='split-lane-preview'?'split-lane-preview':''} label="${this.getAttribute('label')||'14'}" position="${this.getAttribute('position')||'19'}"></segmented-track>`;
    }
    selectSegment(index,emit=true){this.querySelector('segmented-track')?.selectSegment(index,emit);}
  }

  class WorkbenchFormControlStates extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      const chevron=`<img src="${assets}icon-chevron.svg" alt="">`;
      this.innerHTML=`<div class="workbench-control-showcase">
        <section class="workbench-control-showcase__group" aria-labelledby="input-states-title">
          <h3 id="input-states-title">输入框</h3>
          <div class="workbench-control-showcase__states">
            <label class="workbench-control-state"><span>默认</span><input class="workbench-control" type="text" placeholder="请输入内容"></label>
            <label class="workbench-control-state"><span>选择</span><input class="workbench-control is-selected" type="text" value="选择错移动遥控器到目标位置"></label>
            <label class="workbench-control-state"><span>禁用</span><input class="workbench-control" type="text" value="选择错移动遥控器到目标位置" disabled></label>
          </div>
        </section>
        <section class="workbench-control-showcase__group" aria-labelledby="select-states-title">
          <h3 id="select-states-title">下拉框</h3>
          <div class="workbench-control-showcase__states">
            <div class="workbench-control-state"><span>默认</span><button class="workbench-control workbench-control--select is-placeholder" type="button" aria-haspopup="listbox">请选择错误原因${chevron}</button></div>
            <div class="workbench-control-state"><span>选择</span><button class="workbench-control workbench-control--select is-selected" type="button" aria-haspopup="listbox">片段范围错位${chevron}</button></div>
            <div class="workbench-control-state"><span>禁用</span><button class="workbench-control workbench-control--select" type="button" disabled>片段范围错位${chevron}</button></div>
          </div>
        </section>
      </div>`;
    }
  }

  class SegmentColorPalette extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered="true";
      const count=Math.max(1,Number(this.getAttribute('count')||50));
      const palette=['#D5B486','#A6E0F2','#ADD586','#A1ABE8','#A8DEC9','#D5CA86','#A9B2D9','#86D5BA','#CDA0DD','#D5869A','#D2B660','#4EABE0','#8FD04C','#7584DE','#60C9D2','#E6DC72','#668FB8','#39CDB1','#AC6AC7','#D26069','#FF9559','#42A8D2','#B7E23C','#4C63DF','#168F78','#D7A23B','#3D8FD8','#48C98A','#9850D7','#DB405F','#C44F3A','#167C9A','#9A9F18','#3048B8','#45C97B','#DD8B43','#24507A','#42BD7D','#7932A6','#CF3BA8','#9A3F1F','#1E718A','#788F18','#263DA5','#159E94','#946219','#1D4478','#198F45','#543075','#B52B7A'];
      const colors=palette.slice(0,count);
      const luminance=color=>{const [r,g,b]=color.match(/[\dA-F]{2}/gi).map(value=>parseInt(value,16));return .2126*r+.7152*g+.0722*b;};
      const familyNames=['橙棕','蓝色','黄绿色','靛蓝','青绿色','金黄色','深蓝','绿色','紫色','红色'];
      const familyOrder=[0,5,2,7,4,1,6,3,8,9];
      const families=familyOrder.map(family=>({name:familyNames[family],items:Array.from({length:5},(_,tone)=>{const index=tone*10+family;return {color:colors[index],index};}).filter(item=>item.color).sort((a,b)=>luminance(a.color)-luminance(b.color))}));
      const rgb=color=>color.match(/[\dA-F]{2}/gi).map(value=>parseInt(value,16));
      const distance=(a,b)=>Math.hypot(...rgb(a).map((value,index)=>value-rgb(b)[index]));
      const hueOf=color=>{const [r,g,b]=rgb(color).map(value=>value/255),max=Math.max(r,g,b),min=Math.min(r,g,b),delta=max-min;if(!delta)return 0;const raw=max===r?((g-b)/delta)%6:max===g?(b-r)/delta+2:(r-g)/delta+4;return (raw*60+360)%360;};
      const hueDistance=(a,b)=>{const gap=Math.abs(hueOf(a)-hueOf(b));return Math.min(gap,360-gap);};
      const stripColors=[];
      let randomSeed=20260903;
      const fixedRandom=()=>{randomSeed=(randomSeed*1664525+1013904223)>>>0;return randomSeed/4294967296;};
      const darkestIndexes=new Set(families.map(family=>family.items[0]?.index).filter(index=>index!==undefined));
      const segmentPaletteIndexes=[21,20,28,27,12,25,26,23,37,11,35,34,29,39].filter(index=>index<colors.length);
      const leadingIndexes=new Set(segmentPaletteIndexes);
      const darkest=colors.map((color,index)=>({color,index})).filter(item=>darkestIndexes.has(item.index));
      const unused=colors.map((color,index)=>({color,index})).filter(item=>!darkestIndexes.has(item.index)&&!leadingIndexes.has(item.index));
      stripColors.push(...segmentPaletteIndexes.map(index=>({color:colors[index],index})));
      const appendGentle=source=>{
        while(source.length){
          const previous=stripColors.at(-1);
          const choices=source.map((item,index)=>{const hueGap=hueDistance(previous.color,item.color),rgbGap=distance(previous.color,item.color);return {item,index,score:Math.abs(hueGap-58)+Math.max(0,58-rgbGap)*3+Math.max(0,hueGap-112)*2};}).sort((a,b)=>a.score-b.score).slice(0,3);
          const choice=choices[Math.floor(fixedRandom()*choices.length)];
          stripColors.push(source.splice(choice.index,1)[0]);
        }
      };
      appendGentle(unused);
      const harmonyOrder=[4,44,36,13,18,33,14];
      const harmonySet=new Set(harmonyOrder);
      const harmonySlots=stripColors.map((item,index)=>harmonySet.has(item.index)?index:-1).filter(index=>index>=0);
      harmonySlots.forEach((slot,index)=>{stripColors[slot]={color:colors[harmonyOrder[index]],index:harmonyOrder[index]};});
      appendGentle(darkest);
      const tailOrder=[9,0,15,32,31,46,43,48,49,40,45,42,47,24,41];
      const tailSet=new Set(tailOrder);
      const tailSlots=stripColors.map((item,index)=>tailSet.has(item.index)?index:-1).filter(index=>index>=0);
      tailSlots.forEach((slot,index)=>{stripColors[slot]={color:colors[tailOrder[index]],index:tailOrder[index]};});
      this.innerHTML=`<div class="segment-color-palette__strip" aria-label="50 色随机连续效果">${stripColors.map(({color,index})=>`<span style="--palette-color:${color}" title="${String(index+1).padStart(2,'0')} · ${color}"></span>`).join('')}</div><div class="segment-color-palette">${families.map(family=>`<div class="segment-color-palette__family"><strong>${family.name}</strong>${family.items.map(({color,index})=>`<div class="segment-color-palette__item"><span style="--palette-color:${color}"></span><code>${String(index+1).padStart(2,'0')} · ${color}</code></div>`).join('')}</div>`).join('')}</div>`;
    }
  }

  if(!customElements.get('timeline-time-scale'))customElements.define('timeline-time-scale',TimelineTimeScale);
  if(!customElements.get('timeline-range-selector'))customElements.define('timeline-range-selector',TimelineRangeSelector);
  if(!customElements.get('timeline-range-ruler'))customElements.define('timeline-range-ruler',TimelineRangeRuler);
  if(!customElements.get('annotation-segment-row'))customElements.define('annotation-segment-row',AnnotationSegmentRow);
  if(!customElements.get('annotation-base-row'))customElements.define('annotation-base-row',AnnotationBaseRow);
  if(!customElements.get('timeline-controls'))customElements.define('timeline-controls',TimelineControls);
  if(!customElements.get('workbench-multi-select'))customElements.define('workbench-multi-select',WorkbenchMultiSelect);
  if(!customElements.get('workbench-task-header'))customElements.define('workbench-task-header',WorkbenchTaskHeader);
  if(!customElements.get('workbench-instruction'))customElements.define('workbench-instruction',WorkbenchInstruction);
  if(!customElements.get('workbench-media-viewer'))customElements.define('workbench-media-viewer',WorkbenchMediaViewer);
  if(!customElements.get('workbench-segment-editor'))customElements.define('workbench-segment-editor',WorkbenchSegmentEditor);
  if(!customElements.get('workbench-segment-list-panel'))customElements.define('workbench-segment-list-panel',WorkbenchSegmentListPanel);
  if(!customElements.get('workbench-annotation-list'))customElements.define('workbench-annotation-list',WorkbenchAnnotationList);
  if(!customElements.get('workbench-quality-list'))customElements.define('workbench-quality-list',WorkbenchQualityList);
  if(!customElements.get('workbench-segment-tabs'))customElements.define('workbench-segment-tabs',WorkbenchSegmentTabs);
  if(!customElements.get('workbench-segment-list'))customElements.define('workbench-segment-list',WorkbenchSegmentList);
  if(!customElements.get('workbench-quality-conclusion'))customElements.define('workbench-quality-conclusion',WorkbenchQualityConclusion);
  if(!customElements.get('workbench-quality-track'))customElements.define('workbench-quality-track',WorkbenchQualityTrack);
  if(!customElements.get('workbench-confirm-dialog'))customElements.define('workbench-confirm-dialog',WorkbenchConfirmDialog);
  if(!customElements.get('workbench-shortcut-dialog'))customElements.define('workbench-shortcut-dialog',WorkbenchShortcutDialog);
  if(!customElements.get('workbench-footer-actions'))customElements.define('workbench-footer-actions',WorkbenchFooterActions);
  if(!customElements.get('segmented-track'))customElements.define('segmented-track',SegmentedTrack);
  if(!customElements.get('semantic-annotation-track'))customElements.define('semantic-annotation-track',SemanticAnnotationTrack);
  if(!customElements.get('action-annotation-track'))customElements.define('action-annotation-track',ActionAnnotationTrack);
  if(!customElements.get('workbench-form-control-states'))customElements.define('workbench-form-control-states',WorkbenchFormControlStates);
  if(!customElements.get('segment-color-palette'))customElements.define('segment-color-palette',SegmentColorPalette);

  const gallery=document.querySelector('.workbench-component-preview .component-gallery');
  if(gallery&&!document.querySelector('.component-quick-nav')){
    const groups=[
      {label:'任务信息',target:document.querySelector('#component-major-task')},
      {label:'采集指令',target:document.querySelector('#component-major-instruction')},
      {label:'媒体预览',target:document.querySelector('#component-major-media')},
      {label:'质检标注操作',target:document.querySelector('#component-major-annotation')},
      {label:'列表',target:document.querySelector('#component-major-list')},
      {label:'弹窗',target:document.querySelector('#component-major-dialog')},
      {label:'快捷键',target:document.querySelector('#component-major-shortcuts')},
      {label:'时间轴',target:document.querySelector('#component-major-timeline')},
      {label:'空状态',target:document.querySelector('#component-major-empty')}
    ].filter(group=>group.target);
    const nav=document.createElement('nav');
    nav.className='component-quick-nav';
    nav.setAttribute('aria-label','组件快捷导航');
    nav.innerHTML=`<strong>快捷导航</strong><div>${groups.map((group,index)=>`<a href="#${group.target.id}"${index===0?' class="is-active"':''}>${group.label}</a>`).join('')}</div>`;
    document.body.appendChild(nav);
    const links=[...nav.querySelectorAll('a')];
    links.forEach(link=>link.addEventListener('click',event=>{event.preventDefault();document.querySelector(link.getAttribute('href'))?.scrollIntoView({behavior:'smooth',block:'start'});}));
    const syncActive=()=>{const marker=window.innerHeight*.22;let active=0;groups.forEach((group,index)=>{if(group.target.getBoundingClientRect().top<=marker)active=index;});links.forEach((link,index)=>link.classList.toggle('is-active',index===active));};
    let frame=0;
    window.addEventListener('scroll',()=>{if(frame)return;frame=requestAnimationFrame(()=>{frame=0;syncActive();});},{passive:true});
    syncActive();
  }
})();
