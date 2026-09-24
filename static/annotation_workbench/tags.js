// Temporal labels are independent records: overlap never trims another label.
window.AnnotationTagWorkspace = class {
  constructor({timelineCard, workspace, sidebar, notify}) {
    this.duration = 70;
    this.catalog = workbenchTagCatalog;
    this.labels = [...this.catalog.leaves.keys()];
    this.colors = ['#36b9ca', '#9290ee', '#5bbd8b', '#d4a64f', '#d88291', '#729ee4', '#df8a50'];
    this.items = [
      {id: 'tag-home', label: 'obj_storage_box', start: 0, end: 70},
      {id: 'tag-books', label: 'act_pick', start: 8, end: 30},
      {id: 'tag-books-2', label: 'act_pick', start: 40, end: 49},
      {id: 'tag-books-3', label: 'act_pick', start: 55, end: 64},
      {id: 'tag-hands', label: 'act_place', start: 18, end: 42}
    ];
    this.additionalDemoItems=[
      {id:'tag-take-out',label:'act_take_out',start:3,end:16},
      {id:'tag-stack',label:'act_stack',start:45,end:61},
      {id:'tag-rotate',label:'act_rotate',start:24,end:36},
      {id:'tag-open',label:'act_open',start:1,end:12}
    ];
    this.items.push(...this.additionalDemoItems.map(item=>({...item})));
    // Seed distinct, stable colors for the seven demo tracks; edits never renumber them.
    this.labelColors=new Map();
    [...new Set(this.items.map(item=>item.label)),...this.labels].forEach(label=>{
      if(this.labelColors.has(label))return;
      const index=this.labelColors.size;
      this.labelColors.set(label,this.colors[index] || `hsl(${Math.round(index*137.508)%360} 55% 58%)`);
    });
    this.listMode='all';this.searchQuery='';
    this.notify = notify;
    this.selected = 'tag-books';
    this.dirty = false;
    this.position = 18;
    this.track = document.createElement('section');
    this.track.className = 'tag-timeline'; this.track.hidden = true;
    this.track.setAttribute('aria-label', '标签时间轴');
    this.track.innerHTML = `<timeline-controls class="tag-toolbar"></timeline-controls>
      <div class="tag-selection"><timeline-range-selector></timeline-range-selector></div>
      <div class="tag-lanes-window"><div class="tag-lanes"></div><div class="tag-playhead-track"><i class="segmented-timeline__playhead tag-playhead" role="slider" tabindex="0" aria-label="标签播放位置" aria-valuemin="0" aria-valuemax="70" aria-valuenow="18"></i></div></div>
      `;
    timelineCard.append(this.track);
    this.editor = document.createElement('section');
    this.editor.className = 'tag-editor-shell'; this.editor.hidden = true;
    this.editor.setAttribute('aria-label', '标签片段编辑');
    this.editor.innerHTML = `<section class="card form-card tag-editor">
      <div class="form-row form-row--meta"><div class="segment-meta"><span class="segment-current segment-current--code"><b class="current-segment-value" data-tag-title>01</b></span><label for="tag-start">开始时间</label><input id="tag-start" class="tag-time-input" data-tag-start type="text" placeholder="00:00" maxlength="5" required aria-label="开始时间（分:秒）"><label for="tag-end">结束时间</label><input id="tag-end" class="tag-time-input" data-tag-end type="text" placeholder="00:00" maxlength="5" required aria-label="结束时间（分:秒）"><span>时长</span><b data-tag-duration></b><span>颜色</span><i class="workbench-segment-color" data-tag-color aria-label="当前标签颜色"></i></div><div class="segment-actions" aria-label="片段操作"><button class="segment-action segment-action--navigate" type="button" data-tag-up title="上一条标签轨（⌘↑）" aria-label="上一条标签轨" aria-keyshortcuts="Meta+ArrowUp"><kbd aria-hidden="true">⌘↑</kbd></button><button class="segment-action segment-action--navigate" type="button" data-tag-down title="下一条标签轨（⌘↓）" aria-label="下一条标签轨" aria-keyshortcuts="Meta+ArrowDown"><kbd aria-hidden="true">⌘↓</kbd></button><button class="segment-action segment-action--navigate" type="button" data-tag-previous title="同轨上一段（⌘←）" aria-label="同轨上一段" aria-keyshortcuts="Meta+ArrowLeft"><kbd aria-hidden="true">⌘←</kbd></button><button class="segment-action segment-action--navigate" type="button" data-tag-next title="同轨下一段（⌘→）" aria-label="同轨下一段" aria-keyshortcuts="Meta+ArrowRight"><kbd aria-hidden="true">⌘→</kbd></button><button class="segment-action segment-action--danger" type="button" data-tag-delete-track>删除轨道</button><button class="segment-action segment-action--danger" type="button" data-tag-delete>删除本条</button><button class="segment-action" type="button" data-tag-undo hidden>撤销删除</button></div></div>
      <workbench-tag-tree-select class="tag-label-source" hidden aria-label="片段标签"></workbench-tag-tree-select>
      <div class="form-row form-row--error"><label class="field-label" for="tag-error">错误原因</label><span class="workbench-select-control"><select id="tag-error" class="input-like" aria-label="错误原因"><option value="">请选择错误原因</option><option>标签选择错误</option><option>标签遗漏</option><option>片段范围错误</option><option>片段范围错位</option><option>动作开始边界偏早</option><option>动作开始边界偏晚</option><option>动作结束边界偏早</option><option>动作结束边界偏晚</option></select><img src="/static/annotation_workbench/assets/icon-chevron.svg" alt=""></span></div>
      <span class="tag-editor-validation" data-tag-message role="status" hidden></span></section>`;
    workspace.append(this.editor);
    this.panel = document.createElement('section'); this.panel.className = 'tag-panel workbench-flat-list workbench-annotation-list'; this.panel.hidden = true;
    this.panel.innerHTML = '<header class="workbench-flat-list__header"><span>标签列表</span><div class="tag-tree-actions" aria-label="标签展示范围"><button type="button" class="tag-text-button" data-tag-expand="all" aria-pressed="true">全部展示</button><button type="button" class="tag-text-button" data-tag-expand="annotated" aria-pressed="false">仅展示已标注</button></div></header><div class="tag-search"><input class="input-like" type="search" data-tag-search placeholder="搜索标签" aria-label="搜索标签" autocomplete="off"></div><div class="tag-records workbench-flat-list__body" role="tree" aria-label="标签树"></div>';
    sidebar.prepend(this.panel);
    this.selector = this.track.querySelector('timeline-range-selector');
    this.selector._format = percent => this.time(percent * this.duration / 100);
    this.multi = this.editor.querySelector('workbench-tag-tree-select');
    this.startInput = this.editor.querySelector('[data-tag-start]');
    this.endInput = this.editor.querySelector('[data-tag-end]');
    this.expanded = new Set(['action','act_pick_place']);
    this.panel.querySelector('[data-tag-search]').addEventListener('input',event=>{
      this.searchQuery=event.target.value.trim().toLocaleLowerCase();this.renderList();
    });
    this.panel.querySelectorAll('[data-tag-expand]').forEach(button=>button.addEventListener('click',()=>this.expandTree(button.dataset.tagExpand)));
    document.addEventListener('keydown',event=>{
      if(this.editor.hidden || event.defaultPrevented || !event.metaKey || event.ctrlKey || event.altKey || event.shiftKey)return;
      if(event.target.closest('input,textarea,select,[contenteditable],dialog'))return;
      const action={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'previous',ArrowRight:'next'}[event.key];
      if(!action)return;
      // Handle label navigation before shared annotation shortcuts can consume it.
      event.preventDefault();event.stopImmediatePropagation();
      this.editor.querySelector(`[data-tag-${action}]`).click();
    },true);
    const playhead=this.track.querySelector('.tag-playhead');
    const playheadTrack=this.track.querySelector('.tag-playhead-track');
    const seekPointer=event=>{
      const bounds=playheadTrack.getBoundingClientRect();
      this.seek(this.round(Math.max(0,Math.min(this.duration,(event.clientX-bounds.left)/bounds.width*this.duration))));
    };
    playhead.addEventListener('pointerdown',event=>{
      if(event.button!==0)return;
      event.preventDefault(); playhead.setPointerCapture(event.pointerId);
      playhead.classList.add('is-dragging'); seekPointer(event);
    });
    playhead.addEventListener('pointermove',event=>{if(playhead.hasPointerCapture(event.pointerId))seekPointer(event);});
    const stopSeek=event=>{
      playhead.classList.remove('is-dragging');
      if(playhead.hasPointerCapture(event.pointerId))playhead.releasePointerCapture(event.pointerId);
    };
    playhead.addEventListener('pointerup',stopSeek);
    playhead.addEventListener('pointercancel',stopSeek);
    playhead.addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();
      this.seek(this.round(event.key==='Home'?0:event.key==='End'?this.duration:Math.max(0,Math.min(this.duration,this.position+(event.key==='ArrowLeft'?-.1:.1)))));
    });
    this.selector.addEventListener('range-change', event => {
      this.setTimeInput(this.startInput, this.round(event.detail.start * this.duration / 100));
      this.setTimeInput(this.endInput, this.round(event.detail.end * this.duration / 100));
      this.dirty = true; this.updateRange(false);
    });
    [this.startInput, this.endInput].forEach(input => input.addEventListener('input', () => {this.dirty = true; this.updateRange();}));
    this.multi.addEventListener('multi-select-change', () => {this.dirty = true; this.updateRange();});
    this.connectToolbar();
    this.editor.querySelector('[data-tag-up]').addEventListener('click',()=>this.navigateTrack(-1));
    this.editor.querySelector('[data-tag-down]').addEventListener('click',()=>this.navigateTrack(1));
    this.editor.querySelector('[data-tag-previous]').addEventListener('click',()=>this.navigate(-1));
    this.editor.querySelector('[data-tag-next]').addEventListener('click',()=>this.navigate(1));
    this.editor.querySelector('#tag-error').addEventListener('change',()=>{this.dirty=true;this.updateRange();});
    this.editor.querySelector('[data-tag-delete-track]').addEventListener('click',()=>this.remove(true));
    this.editor.querySelector('[data-tag-delete]').addEventListener('click', () => this.remove());
    this.editor.querySelector('[data-tag-undo]').addEventListener('click', () => this.undo());
    [this.track, this.panel].forEach(root => root.addEventListener('click', event => {
      const add = event.target.closest('[data-tag-add-label]');
      if (add) {this.beginForLabel(add.dataset.tagAddLabel); return;}
      const target = event.target.closest('[data-tag-id]');
      if (target && this.toolMode==='分割') {
        const rail=target.closest('.tag-lane-rail').getBoundingClientRect();
        this.split(target.dataset.tagId,this.round((event.clientX-rail.left)/rail.width*this.duration));return;
      }
      if (target && this.commitPending()) {
        this.selected = target.dataset.tagId;
        this.expandLabel(this.items.find(item=>item.id===this.selected).label);
        this.loadEditor(); this.render();
        this.seek(this.items.find(item => item.id === this.selected).start);
      }
    }));
    this.loadEditor(); this.render();
  }
  connectToolbar() {
    this.controls=this.track.querySelector('timeline-controls');
    this.speed=1;
    const button=label=>this.controls.querySelector(`[aria-label="${label}"]`);
    this.controls.querySelector('[data-playback-current]').parentNode.lastChild.textContent=` ${this.time(this.duration)}`;
    this.controls.querySelectorAll('.segmented-timeline__tool').forEach(item=>{
      item.dataset.tooltip=item.dataset.defaultTooltip=item.getAttribute('aria-label');
    });
    button('添加').dataset.tagNew='';
    button('添加').addEventListener('click',()=>this.beginNew());
    button('添加并前进').addEventListener('click',()=>{if(this.commitPending(true))this.advance();});
    button('仅前进').addEventListener('click',()=>this.advance());
    button('清空').dataset.tooltip='删除当前标签片段';
    button('清空').addEventListener('click',()=>this.remove());
    button('合并').dataset.tooltip='合并同标签相邻或重叠的片段';
    button('合并').addEventListener('click',()=>this.merge());
    // Leaf labels have no parent track, and distinct labels must remain independent.
    for(const label of ['父级分割','向上合并','向下合并']) {
      button(label).disabled=true;
      button(label).dataset.tooltip=label==='父级分割'?'标签轨无父级片段':'不同标签的片段独立保留';
    }
    button('倍速').addEventListener('click',()=>{
      const speeds=[.5,1,1.5,2];this.speed=speeds[(speeds.indexOf(this.speed)+1)%speeds.length];
      button('倍速').querySelector('span').textContent=`${this.speed}x`;
    });
    this.controls.addEventListener('play-toggle',event=>this.setPlaying(event.detail.playing));
    this.controls.addEventListener('tool-mode-change',event=>{
      this.toolMode=event.detail.mode;this.track.dataset.toolMode=this.toolMode || '';
    });
    const shortcuts=this.controls.querySelector('.segmented-timeline__shortcut-popover');
    shortcuts.setAttribute('aria-label','标签快捷键');
    shortcuts.querySelector('strong').textContent='标签快捷键';
    shortcuts.querySelector('.segmented-timeline__shortcut-list').innerHTML='<span><span>上一轨 / 下一轨</span><kbd>⌘↑ / ⌘↓</kbd></span><span><span>同轨上一段 / 下一段</span><kbd>⌘← / ⌘→</kbd></span><span><span>播放 / 暂停</span><kbd>Space</kbd></span><span><span>退出操作模式</span><kbd>Esc</kbd></span><span><span>定位（聚焦蓝色播放条）</span><kbd>← / →</kbd></span>';
    document.addEventListener('keydown',event=>{
      if(this.track.hidden || event.defaultPrevented || event.code!=='Space' || event.ctrlKey || event.metaKey || event.altKey)return;
      if(event.target.closest('input,textarea,select,button,[role="button"],[contenteditable="true"],dialog'))return;
      event.preventDefault();this.setPlaying(!this.playing);
    });
    this.controls.querySelector('.segmented-timeline__standard').addEventListener('click',()=>this.notify('暂未配置标签标注标准'));
    const lanes=this.track.querySelector('.tag-lanes');
    lanes.addEventListener('pointerdown',event=>{
      const block=event.target.closest('[data-tag-id]');
      if(this.toolMode!=='拖动' || !block || event.button!==0 || !this.commitPending())return;
      const item=this.items.find(row=>row.id===block.dataset.tagId);if(!item)return;
      event.preventDefault();
      const original={...item}, width=block.closest('.tag-lane-rail').getBoundingClientRect().width, x=event.clientX;
      lanes.setPointerCapture(event.pointerId);
      const move=e=>{
        const start=this.round(Math.max(0,Math.min(this.duration-(original.end-original.start),original.start+(e.clientX-x)/width*this.duration)));
        item.start=start;item.end=this.round(start+original.end-original.start);
        this.selected=item.id;this.dirty=false;this.loadEditor();this.render();
      };
      const stop=e=>{
        if(e.type==='pointercancel'){Object.assign(item,original);this.loadEditor();this.render();}
        lanes.removeEventListener('pointermove',move);lanes.removeEventListener('pointerup',stop);lanes.removeEventListener('pointercancel',stop);
        if(lanes.hasPointerCapture(event.pointerId))lanes.releasePointerCapture(event.pointerId);
      };
      lanes.addEventListener('pointermove',move);lanes.addEventListener('pointerup',stop);lanes.addEventListener('pointercancel',stop);
    });
  }
  setPlaying(playing) {
    cancelAnimationFrame(this.playFrame);this.playing=playing;this.controls.setPlaying(playing);
    if(!playing)return;
    if(this.position>=this.duration)this.seek(0);
    let last=performance.now();
    const tick=now=>{
      if(!this.playing)return;
      this.seek(Math.min(this.duration,this.position+(now-last)/1000*this.speed));last=now;
      if(this.position>=this.duration)this.setPlaying(false);else this.playFrame=requestAnimationFrame(tick);
    };
    this.playFrame=requestAnimationFrame(tick);
  }
  advance() {
    if(!this.commitPending())return;
    const start=this.readTimeInput(this.startInput),end=this.readTimeInput(this.endInput),labels=[...this.multi.values];
    if(end>=this.duration){this.notify('已到视频末尾');return;}
    this.selected=null;this.seek(end);this.loadEditor();this.multi.setValues(labels);
    this.setTimeInput(this.startInput,end);this.setTimeInput(this.endInput,Math.min(this.duration,end+end-start));
    this.updateRange();this.render();
  }
  split(id,position) {
    if(!this.commitPending())return;
    const item=this.items.find(row=>row.id===id);
    if(!item || position<=item.start || position>=item.end){this.notify('请在标签片段内部选择分割位置');return;}
    const next={...item,id:this.newId(),start:position};item.end=position;this.items.push(next);
    this.selected=next.id;this.loadEditor();this.render();this.seek(position);
  }
  merge() {
    if(!this.commitPending())return;
    const item=this.items.find(row=>row.id===this.selected);if(!item){this.notify('请先选择标签片段');return;}
    const merged=new Set([item.id]);let start=item.start,end=item.end,changed=true;
    while(changed){
      changed=false;
      for(const other of this.labelItems(item.label)){
        if(merged.has(other.id) || other.start>end || other.end<start)continue;
        if((other.error || '')!==(item.error || '') || Boolean(other.unavailable)!==Boolean(item.unavailable))continue;
        merged.add(other.id);start=Math.min(start,other.start);end=Math.max(end,other.end);changed=true;
      }
    }
    if(merged.size===1){this.notify('没有可合并的同标签片段（需相邻或重叠，且审核信息一致）');return;}
    item.start=start;item.end=end;this.items=this.items.filter(row=>row.id===item.id || !merged.has(row.id));
    this.loadEditor();this.render();
  }
  round(value) {return Math.round(value * 10) / 10;}
  newId() {return `tag-${globalThis.crypto?.randomUUID?.() || Date.now().toString(36)+'-'+Math.random().toString(36).slice(2)}`;}
  time(value) {const seconds=Math.floor(value);return `${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;}
  setTimeInput(input,seconds) {
    input.value=this.time(seconds);
    input.dataset.seconds=String(seconds); input.dataset.formatted=input.value;
  }
  readTimeInput(input) {
    if(!/^\d{2}:[0-5]\d$/.test(input.value))return NaN;
    // Keep existing subsecond boundaries when only labels or review fields change.
    if(input.value===input.dataset.formatted)return Number(input.dataset.seconds);
    const [minutes,seconds]=input.value.split(':').map(Number);return minutes*60+seconds;
  }
  name(id) {return this.catalog.leaves.get(id)?.name || id;}
  color(label) {return this.labelColors.get(label) || this.colors[0];}
  setVisible(visible) {
    this.track.hidden=!visible; this.editor.hidden=!visible; this.panel.hidden=!visible;
    if (!visible) {this.setPlaying(false);this.controls._setSettingsOpen(false);this.controls._setShortcutOpen(false);}
    if (visible) requestAnimationFrame(()=>this.revealSelection());
  }
  revealSelection() {
    if (!this.track.hidden) this.track.querySelector('.tag-block.is-selected')?.scrollIntoView({block:'nearest', inline:'nearest'});
  }
  loadEditor() {
    const item = this.items.find(item => item.id === this.selected);
    const start=item?.start ?? Math.min(this.position, this.duration-1);
    this.setTimeInput(this.startInput,start);
    this.setTimeInput(this.endInput,item?.end ?? Math.min(start+10,this.duration));
    this.multi.setValues(item ? [item.label] : []);
    const siblings = item ? this.labelItems(item.label) : [];
    const index=siblings.findIndex(row=>row.id===item?.id);
    const title=this.editor.querySelector('[data-tag-title]');
    title.textContent=item ? String(index+1).padStart(2,'0') : '新增';
    title.title=item ? `${this.name(item.label)} · 片段 ${index+1} / ${siblings.length}` : '新增标签片段';
    this.editor.querySelector('[data-tag-color]').style.background=item?this.color(item.label):'transparent';
    this.editor.querySelector('[data-tag-previous]').disabled=index<=0;
    this.editor.querySelector('[data-tag-next]').disabled=index<0 || index>=siblings.length-1;
    const usedLabels=this.labels.filter(label=>this.items.some(row=>row.label===label));
    const trackIndex=item ? usedLabels.indexOf(item.label) : -1;
    this.editor.querySelector('[data-tag-up]').disabled=trackIndex<=0;
    this.editor.querySelector('[data-tag-down]').disabled=trackIndex<0 || trackIndex>=usedLabels.length-1;
    this.editor.querySelector('#tag-error').value=item?.error || '';
    this.editor.querySelector('[data-tag-delete]').disabled = !item;
    this.editor.querySelector('[data-tag-delete-track]').disabled = !item;
    this.updateRange();
  }
  updateRange(syncSelector=true) {
    const start = this.readTimeInput(this.startInput), end = this.readTimeInput(this.endInput);
    const valid = this.validRange();
    if (syncSelector && valid) this.selector.setRange(start/this.duration*100, end/this.duration*100);
    this.editor.querySelector('[data-tag-duration]').textContent = valid ? this.time(this.round(end-start)) : '—';
    this.message(valid ? '' : `请输入 00:00–${this.time(this.duration)} 内的时间（分:秒），结束时间须晚于开始时间。`, !valid);
  }
  validRange() {
    const start = this.readTimeInput(this.startInput), end = this.readTimeInput(this.endInput);
    return Number.isFinite(start) && Number.isFinite(end) && start >= 0 && end <= this.duration && end > start;
  }
  message(text, error=false) {
    const message = this.editor.querySelector('[data-tag-message]');
    message.textContent=text; message.hidden=!text; message.classList.toggle('is-error', error);
  }
  navigate(direction) {
    if(!this.commitPending())return;
    const item=this.items.find(item=>item.id===this.selected);if(!item)return;
    const siblings=this.labelItems(item.label), next=siblings[siblings.findIndex(row=>row.id===item.id)+direction];
    if(!next)return;this.selected=next.id;this.expandLabel(next.label);this.loadEditor();this.render();this.seek(next.start);
  }
  navigateTrack(direction) {
    if(!this.commitPending())return;
    const item=this.items.find(row=>row.id===this.selected);if(!item)return;
    const labels=this.labels.filter(label=>this.items.some(row=>row.label===label));
    const targetLabel=labels[labels.indexOf(item.label)+direction];
    if(!targetLabel)return;
    const targetItems=this.labelItems(targetLabel);
    const next=targetItems.reduce((best,row)=>!best || Math.abs(row.start-item.start)<Math.abs(best.start-item.start)?row:best,null);
    if(!next)return;
    this.selected=next.id;this.expandLabel(next.label);this.loadEditor();this.render();this.seek(next.start);
  }
  labelItems(label) {return this.items.filter(item=>item.label===label).sort((a,b)=>a.start-b.start || a.end-b.end);}
  beginForLabel(label) {
    if (!this.labels.includes(label) || !this.commitPending()) return;
    this.selected=null; this.loadEditor(); this.multi.setValues([label]);
    this.editor.querySelector('[data-tag-title]').title=`${this.name(label)} · 添加一段`;
    this.editor.querySelector('[data-tag-color]').style.background=this.color(label);
    this.dirty=true;this.updateRange();
    this.render(); this.startInput.focus(); this.startInput.select();
  }
  beginNew() {
    if (!this.commitPending()) return;
    const label=this.items.find(item=>item.id===this.selected)?.label || this.multi.values[0];
    if(label){this.beginForLabel(label);return;}
    this.notify('请在右侧标签列表选择标签并点击「+添加轨道」');
  }
  commitPending(explicit=false) {
    if (!this.dirty && !explicit) return true;
    if (!this.validRange()) {this.updateRange(); this.startInput.focus(); this.notify('标签时间范围无效，请先修正'); return false;}
    if (!this.multi.values.length) {this.message('请至少选择一个标签。', true); this.notify('请至少选择一个标签'); return false;}
    const start=this.round(this.readTimeInput(this.startInput)), end=this.round(this.readTimeInput(this.endInput));
    if (end <= start) {this.message('片段时长至少为 0.1 秒。', true); return false;}
    // An exact duplicate is reused; overlapping intervals remain separate records.
    let nextSelected;
    const oldId=this.selected;
    const error=this.editor.querySelector('#tag-error').value;
    const unavailable=Boolean(this.items.find(item=>item.id===oldId)?.unavailable);
    this.items=this.items.filter(item=>item.id!==oldId);
    this.multi.values.forEach((label,index) => {
      let item=this.items.find(item=>item.label===label && item.start===start && item.end===end);
      if (!item) {item={id:index===0 && oldId ? oldId : this.newId(), label, start, end, error, unavailable}; this.items.push(item);}
      if (!nextSelected) nextSelected=item.id;
    });
    this.selected=nextSelected; this.dirty=false;
    this.expandLabel(this.items.find(item=>item.id===nextSelected).label);
    this.loadEditor(); this.render();
    if (explicit) this.notify('标签片段已应用，可点击「保存」保存草稿');
    return true;
  }
  remove(wholeTrack=false) {
    const item=this.items.find(item=>item.id===this.selected);
    if (!item) return;
    const removed=this.items.filter(row=>wholeTrack?row.label===item.label:row.id===item.id);
    const ids=new Set(removed.map(row=>row.id));
    this.deleted={items:removed.map(row=>({...row})),selected:item.id};
    this.items=this.items.filter(row=>!ids.has(row.id));
    this.selected=null; this.dirty=false;
    this.editor.querySelector('[data-tag-undo]').hidden=false;
    this.loadEditor(); this.render(); this.notify(wholeTrack?'已删除当前标签轨道及其全部片段，可撤销':'已删除当前片段，可撤销');
  }
  undo() {
    if (!this.deleted || !this.commitPending()) return;
    const existingIds=new Set(this.items.map(item=>item.id));
    this.items.push(...this.deleted.items.filter(item=>!existingIds.has(item.id)));
    this.selected=this.deleted.selected; this.deleted=null;
    this.editor.querySelector('[data-tag-undo]').hidden=true; this.loadEditor(); this.render();
  }
  render() {
    const lanes=this.track.querySelector('.tag-lanes'); lanes.replaceChildren();
    this.labels.filter(label=>this.items.some(item=>item.label===label)).forEach(label=>{
      const rows=[];
      const items=this.labelItems(label);
      const lane=document.createElement('div'); lane.className='tag-lane';
      lane.dataset.tagLabel=label;
      const name=document.createElement('span');name.className='tag-lane-name';name.textContent=this.name(label);name.title=this.catalog.leaves.get(label)?.path || this.name(label);
      lane.append(name);
      const rail=document.createElement('div'); rail.className='tag-lane-rail';
      items.forEach((item,index)=>{
        let row=rows.findIndex(end=>end<=item.start); if(row<0)row=rows.length; rows[row]=item.end;
        const block=document.createElement('button'); block.type='button'; block.dataset.tagId=item.id;
        block.className='tag-block'; block.classList.toggle('is-selected',item.id===this.selected);
        block.setAttribute('aria-pressed',String(item.id===this.selected));
        block.setAttribute('aria-label',`${this.name(label)} ${this.time(item.start)} 至 ${this.time(item.end)}`);
        block.title=block.getAttribute('aria-label'); block.textContent=`${index+1} · ${this.name(label)}`;
        block.style.cssText=`left:${item.start/this.duration*100}%;width:${(item.end-item.start)/this.duration*100}%;top:${row*24+4}px;--tag-color:${this.color(label)}`;
        rail.append(block);
      });
      rail.style.height=`${rows.length*24+6}px`;
      lane.append(rail); lanes.append(lane);
    });
    // Reserve five track slots without inventing annotations for empty slots.
    while(lanes.children.length<5){
      const empty=document.createElement('div');empty.className='tag-lane tag-lane--empty';
      empty.setAttribute('aria-hidden','true');
      const name=document.createElement('span');name.className='tag-lane-name';
      const rail=document.createElement('div');rail.className='tag-lane-rail';empty.append(name,rail);lanes.append(empty);
    }
    this.renderList(); this.seek(this.position); this.revealSelection();
  }
  renderList() {
    const list=this.panel.querySelector('.tag-records'); list.replaceChildren();
    const filter=nodes=>nodes.flatMap(node=>{
      if(node.leaf){
        if(this.listMode==='annotated' && !this.items.some(item=>item.label===node.id))return [];
        return node.path.toLocaleLowerCase().includes(this.searchQuery)?[node]:[];
      }
      const children=filter(node.children);
      return children.length?[{...node,children}]:[];
    });
    const build=(nodes,parent)=>nodes.forEach(node=>{
      if(!node.leaf){
        const branch=document.createElement('details'); branch.className='tag-list-branch';branch.dataset.tagBranch=node.id;branch.open=Boolean(this.searchQuery) || this.expanded.has(node.id);
        const summary=document.createElement('summary');summary.textContent=node.name;summary.setAttribute('role','treeitem');summary.setAttribute('aria-level',node.depth);summary.setAttribute('aria-expanded',String(branch.open));
        branch.addEventListener('toggle',()=>{if(!branch.isConnected)return;branch.open?this.expanded.add(node.id):this.expanded.delete(node.id);summary.setAttribute('aria-expanded',String(branch.open));});
        const children=document.createElement('div');children.setAttribute('role','group');build(node.children,children);branch.append(summary,children);parent.append(branch);return;
      }
      const label=node.id,items=this.labelItems(label);
      const group=document.createElement('section');group.className='tag-record-group';group.dataset.tagLabel=label;
      group.setAttribute('role','treeitem');group.setAttribute('aria-level',node.depth);group.setAttribute('aria-label',node.path);
      const header=document.createElement('header');header.className='tag-group-header';
      const title=document.createElement('span');title.className='tag-record-title';title.textContent=node.name;title.title=node.path;title.style.setProperty('--tag-color',this.color(label));
      header.append(title);
      if(!items.length){
        const add=document.createElement('button');add.type='button';add.className='tag-text-button';add.dataset.tagAddLabel=label;add.textContent='+添加轨道';add.setAttribute('aria-label',`为${node.name}添加轨道`);
        header.append(add);
      }
      group.append(header);
      items.forEach((item,index)=>{
        const button=document.createElement('button');button.type='button';button.dataset.tagId=item.id;
        button.className='tag-record workbench-flat-list__row workbench-annotation-list__row';button.classList.toggle('is-active',item.id===this.selected);
        button.setAttribute('aria-pressed',String(item.id===this.selected));
        button.setAttribute('aria-label',`${node.name} 片段 ${index+1}，${this.time(item.start)} 至 ${this.time(item.end)}`);
        const number=document.createElement('span');number.className='workbench-flat-list__index';number.textContent=String(index+1).padStart(2,'0');
        const content=document.createElement('span');content.className='workbench-flat-list__content';
        const time=document.createElement('span');time.className='workbench-annotation-list__time';time.textContent=`${this.time(item.start)} → ${this.time(item.end)}（${this.round(item.end-item.start)} 秒）`;
        content.append(time);button.append(number,content);group.append(button);
      });
      parent.append(group);
    });
    build(filter(this.catalog.tree),list);
    if(!list.children.length){
      const empty=document.createElement('p');empty.className='tag-empty';empty.setAttribute('role','status');
      empty.textContent=this.searchQuery?'未找到匹配标签':'暂无已标注标签';list.append(empty);
    }
  }
  expandTree(mode) {
    this.listMode=mode;
    const visit=nodes=>nodes.forEach(node=>{
      if(!node.leaf){this.expanded.add(node.id);visit(node.children);}
    });
    visit(this.catalog.tree);
    this.panel.querySelectorAll('[data-tag-expand]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.tagExpand===mode)));
    this.renderList();
  }
  expandLabel(id) {
    const visit=(nodes,path=[])=>{
      for(const node of nodes){
        if(node.id===id){path.forEach(parent=>this.expanded.add(parent));return true;}
        if(visit(node.children,[...path,node.id]))return true;
      }
      return false;
    };
    visit(this.catalog.tree);
  }

  seek(position) {
    this.position=position;
    if(this.controls)this.controls.querySelector('[data-playback-current]').textContent=this.time(position);
    const playhead=this.track.querySelector('.tag-playhead');
    playhead.style.left=`${position/this.duration*100}%`;
    playhead.setAttribute('aria-valuenow',String(position));
    playhead.setAttribute('aria-valuetext',this.time(position));

  }
  snapshot() {return {version:2, demoVersion:1, items:this.items, unlinked:this.unlinked || [], selected:this.selected};}
  restore(saved, legacyTags) {
    if ([1,2].includes(saved?.version) && Array.isArray(saved.items)) {
      // Resolve old name-based records only when the management leaf is unambiguous.
      saved.items=saved.items.map(item=>{
        if(!item || this.catalog.leaves.has(item.label))return item;
        const matches=[...this.catalog.leaves.values()].filter(node=>node.name===item.label);
        return matches.length===1 ? {...item,label:matches[0].id} : item;
      });
      this.unlinked=[...(saved.unlinked || []),...saved.items.filter(item=>item && !this.labels.includes(item.label))];
      const ids=new Set();
      this.items=saved.items.filter(item=>{
        if (!item || typeof item.id!=='string' || ids.has(item.id) || !this.labels.includes(item.label) || !Number.isFinite(item.start) || !Number.isFinite(item.end) || item.start<0 || item.end>this.duration || item.end<=item.start) return false;
        ids.add(item.id); return true;
      }).map(({id,label,start,end,error,unavailable})=>({id,label,start,end,error:typeof error==='string'?error:'',unavailable:Boolean(unavailable)}));
      this.selected=this.items.some(item=>item.id===saved.selected) ? saved.selected : this.items[0]?.id ?? null;
    } else if (Array.isArray(legacyTags) && legacyTags.length) {
      this.unlinked=legacyTags.map(label=>({id:this.newId(),label,start:0,end:this.duration}));
      this.items=[];
      this.selected=this.items[0]?.id ?? null;
    }
    // Upgrade older demo drafts once; saved deletions in the new version stay deleted.
    if(saved && !saved.demoVersion){
      const labels=new Set(this.items.map(item=>item.label)),ids=new Set(this.items.map(item=>item.id));
      this.items.push(...this.additionalDemoItems.filter(item=>!labels.has(item.label) && !ids.has(item.id)).map(item=>({...item})));
    }
    const selected=this.items.find(item=>item.id===this.selected);
    if(selected)this.expandLabel(selected.label);
    this.dirty=false; this.loadEditor(); this.render();
  }
};
