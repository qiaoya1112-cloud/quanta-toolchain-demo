(() => {
  const trainingType = 'pre';
  const label = '预训练';
  const eventName = suffix => `${trainingType}-quality-${suffix}`;
  const elementName = suffix => `${trainingType}-training-quality-${suffix}`;
  const domPrefix = 'prq';
  const recordId = document.querySelector('workbench-task-header')?.dataset?.id || 'DT202609070126';
  const DURATION = 40;
  const TRACK_COUNT = 3;
  const PERMISSIONS = { canReviewErrorReason: true };
  const DRAFT_KEY = `quanta.${trainingType}-training-quality.v4.${recordId}`;
  const RULE = {
    id: 'RL-PRQC-001', version: 'v1', name: `${label}采集质检规则`,
    mistake: [
      {id:'M01', name:'夹爪超出画面', detail:'操作过程中夹爪短暂离开有效画面。'},
      {id:'M02', name:'手部脱离夹爪', detail:'采集动作中手部未按规范保持夹持。'},
      {id:'M03', name:'其他身体部位辅助', detail:'使用规定外的身体部位辅助完成动作。'},
      {id:'M04', name:'无意义动作或假动作', detail:'出现与任务目标无关或未真实执行的动作。'},
      {id:'M05', name:'可用时长太短', detail:'连续可用片段不足 3 秒，提交时自动标记为失误。'}
    ],
    rejected: [
      {id:'U01', name:'视频损坏或相机卡死', detail:'任一必要视角无法连续正常播放。'},
      {id:'U02', name:'采集时长不足', detail:'有效内容未覆盖完整任务。'},
      {id:'U03', name:'画面全程完全遮挡', detail:'关键视角全程不可用于判断。'},
      {id:'U04', name:'设备穿戴不规范', detail:'设备穿戴问题影响数据有效性。'}
    ]
  };
  const seedSegments = () => [
    {id:'A', start:1, end:5, conclusion:'mistake', mistakeReasons:['M01'], rejectedReasons:[], reviewErrorReason:'动作开始边界偏早'},
    {id:'B', start:4.5, end:8, conclusion:'rejected', mistakeReasons:['M02'], rejectedReasons:['U04'], reviewErrorReason:'片段范围错位'},
    {id:'C', start:9.4, end:10.8, conclusion:'mistake', mistakeReasons:['M03'], rejectedReasons:[], reviewErrorReason:'描述与画面不一致'},
    {id:'D', start:12, end:20, conclusion:'rejected', mistakeReasons:[], rejectedReasons:['U02'], reviewErrorReason:'片段范围错误'},
    {id:'E', start:17, end:22.5, conclusion:'mistake', mistakeReasons:['M04'], rejectedReasons:[], reviewErrorReason:'动作结束边界偏晚'},
    {id:'F', start:18, end:19.4, conclusion:'pending', mistakeReasons:[], rejectedReasons:[], reviewErrorReason:''},
    {id:'G', start:18.2, end:19, conclusion:'rejected', mistakeReasons:[], rejectedReasons:['U03'], reviewErrorReason:'片段范围错位'},
    {id:'H', start:18.4, end:19.2, conclusion:'mistake', mistakeReasons:['M02'], rejectedReasons:[], reviewErrorReason:'动作结束边界偏早'}
  ];

  const clone = value => JSON.parse(JSON.stringify(value));
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const format = value => {
    const seconds = clamp(Number(value) || 0, 0, DURATION);
    const minutes = Math.floor(seconds / 60);
    const remainder = seconds - minutes * 60;
    return `${String(minutes).padStart(2,'0')}:${remainder.toFixed(1).padStart(4,'0')}`;
  };
  const parseTime = value => {
    const raw = String(value ?? '').trim();
    if (/^\d+(\.\d+)?$/.test(raw)) return Number(raw);
    const parts = raw.split(':').map(Number);
    return parts.length === 2 && parts.every(Number.isFinite) ? parts[0] * 60 + parts[1] : NaN;
  };
  const conclusionLabel = value => value === 'mistake' ? '失误' : value === 'rejected' ? '不合格' : '待判定';
  const overlapDuration = (a, b) => Math.max(0, Math.min(a.end, b.end) - Math.max(a.start, b.start));
  const trackOverlap = (candidate, segments, track) => segments
    .filter(item => item.id !== candidate.id && item.track === track)
    .reduce((sum, item) => sum + overlapDuration(candidate, item), 0);
  const segmentErrors = segment => {
    const errors = [];
    if (!(segment.start >= 0 && segment.start < segment.end && segment.end <= DURATION)) errors.push('片段时间不合法');
    if (!['mistake','rejected'].includes(segment.conclusion)) errors.push('请选择片段结论');
    if (segment.conclusion === 'mistake' && !segment.mistakeReasons.length) errors.push('请选择失误原因');
    if (segment.conclusion === 'mistake' && segment.rejectedReasons.length) errors.push('请移除不合格原因');
    if (segment.conclusion === 'rejected' && !segment.rejectedReasons.length) errors.push('请选择不合格原因');
    if (!segment.autoShortDuration && PERMISSIONS.canReviewErrorReason && ['mistake','rejected'].includes(segment.conclusion) && !segment.reviewErrorReason?.trim()) errors.push('请填写错误原因');
    return errors;
  };
  const valid = segment => segmentErrors(segment).length === 0;
  const reasonName = id => [...RULE.mistake, ...RULE.rejected].find(item => item.id === id)?.name || id;
  const REVIEW_ERROR_REASONS = ['片段范围错误','片段范围错位','动作开始边界偏早','动作开始边界偏晚','动作结束边界偏早','动作结束边界偏晚','描述与画面不一致'];
  const reasonSummary = segment => {
    const names = [...segment.mistakeReasons, ...segment.rejectedReasons].map(reasonName);
    return names.length ? names.join('、') : segment.conclusion === 'pending' ? '选择结论后设置原因' : '请选择必选原因';
  };
  const sortSegments = list => list.slice().sort((a,b) => a.start - b.start || a.end - b.end || a.order - b.order);
  const segmentNumber = item => Math.max(1, sortSegments(state.segments).findIndex(candidate => candidate.id === item.id) + 1);

  function placeSegment(candidate, segments) {
    const scores = Array.from({length:TRACK_COUNT}, (_, track) => ({track, overlap:trackOverlap(candidate, segments, track)}));
    const target = scores.find(item => item.overlap === 0)
      || scores.reduce((best, item) => item.overlap < best.overlap ? item : best);
    candidate.track = target.track;
    return candidate;
  }

  function assignInitial(list) {
    return list.reduce((placed, raw, index) => {
      const segment = {...raw, order:index + 1, track:0};
      placeSegment(segment, placed);
      placed.push(segment);
      return placed;
    }, []);
  }

  const state = {
    segments: assignInitial(seedSegments()), selectedId:'A', submitted:false,
    dirty:false, revision:1, rangeStart:23, rangeEnd:26
  };
  const byId = id => state.segments.find(item => item.id === id);
  const selected = () => byId(state.selectedId);
  const pendingCount = () => state.segments.filter(item => item.conclusion === 'pending').length;
  const invalidCount = () => state.segments.filter(item => !valid(item)).length;
  const isShortDuration = item => item.conclusion === 'mistake' && item.mistakeReasons.includes('M05');

  // Problem segments occupy the video; their complement is the usable footage.
  function usableRanges(segments, duration = DURATION) {
    const occupied = sortSegments(segments.filter(item => item.conclusion !== 'pass'));
    const ranges = [];
    let cursor = 0;
    for (const item of occupied) {
      const start = clamp(item.start, 0, duration), end = clamp(item.end, 0, duration);
      if (start > cursor) ranges.push({start:cursor, end:start});
      cursor = Math.max(cursor, end);
    }
    if (cursor < duration) ranges.push({start:cursor, end:duration});
    return ranges;
  }
  function validateUsableDuration() {
    const manual = state.segments.filter(item => !item.autoShortDuration);
    const short = usableRanges(manual).filter(item => item.end - item.start < 3 - 1e-9);
    state.segments = manual;
    for (const range of short) {
      const item = {...range, id:nextId(), conclusion:'mistake', mistakeReasons:['M05'], rejectedReasons:[], reviewErrorReason:'', autoShortDuration:true, order:Math.max(0,...state.segments.map(item=>item.order))+1};
      placeSegment(item, state.segments);
      state.segments.push(item);
    }
    if (!state.segments.some(item=>item.id===state.selectedId)) state.selectedId=state.segments[0]?.id||'';
    if (short.length) state.dirty = true;
    notify();
    return short.length;
  }
  const calculateConclusion = (segments, completed) => segments.some(item => item.conclusion === 'rejected') ? '不合格'
    : segments.some(item => item.conclusion === 'mistake') ? '失误'
    : completed && segments.every(valid) ? '合格' : '待计算';
  const calculatedConclusion = () => calculateConclusion(state.segments, true);

  function normalizeSaved(raw, index) {
    return {
      id:String(raw.id || `P${index + 1}`), start:Number(raw.start), end:Number(raw.end),
      conclusion:['mistake','rejected'].includes(raw.conclusion) ? raw.conclusion : 'pending',
      mistakeReasons:Array.isArray(raw.mistakeReasons) ? raw.mistakeReasons : [],
      rejectedReasons:Array.isArray(raw.rejectedReasons) ? raw.rejectedReasons : [], reviewErrorReason:REVIEW_ERROR_REASONS.includes(String(raw.reviewErrorReason ?? raw.note ?? '')) ? String(raw.reviewErrorReason ?? raw.note ?? '') : '',
      autoShortDuration:raw.autoShortDuration === true && raw.conclusion === 'mistake' && raw.mistakeReasons?.includes('M05'),
      order:Number(raw.order) || index + 1, track:clamp(Number(raw.track ?? raw.lane) || 0,0,2)
    };
  }

  function restore() {
    try {
      const saved = JSON.parse(localStorage.getItem(DRAFT_KEY) || 'null');
      if (!saved || !Array.isArray(saved.segments)) return;
      state.segments = saved.segments.map(normalizeSaved);
      state.selectedId = state.segments.some(item => item.id === saved.selectedId) ? saved.selectedId : state.segments[0]?.id || '';
      state.revision = Number(saved.revision) || 1;
      state.dirty = false;
    } catch (_) {}
  }
  restore();

  function notify() {
    document.dispatchEvent(new CustomEvent(eventName('state-change'), {detail:clone(state)}));
  }
  function markDirty() {
    state.dirty = true;
    notify();
  }
  function selectSegment(id, seek = true) {
    const item = byId(id);
    if (!item) return;
    state.selectedId = id;
    state.rangeStart = item.start;
    state.rangeEnd = item.end;
    notify();
    if (seek) document.dispatchEvent(new CustomEvent(eventName('seek'), {detail:{seconds:item.start}}));
  }
  function nextId() {
    const used = new Set(state.segments.map(item => item.id));
    let index = 1;
    while (used.has(`N${index}`)) index += 1;
    return `N${index}`;
  }
  function addSegment(start = state.rangeStart, end = state.rangeEnd) {
    if (state.submitted || !Number.isFinite(start) || !Number.isFinite(end)) return;
    const safeStart = clamp(Math.min(start,end), 0, DURATION - .3);
    const safeEnd = clamp(Math.max(start,end), safeStart + .3, DURATION);
    const item = {
      id:nextId(), start:Math.round(safeStart * 10) / 10, end:Math.round(safeEnd * 10) / 10,
      conclusion:'pending', mistakeReasons:[], rejectedReasons:[], reviewErrorReason:'', order:Math.max(0,...state.segments.map(item=>item.order))+1, track:0
    };
    placeSegment(item, state.segments);
    state.segments.push(item);
    state.selectedId = item.id;
    markDirty();
    document.dispatchEvent(new CustomEvent(eventName('seek'), {detail:{seconds:item.start}}));
  }
  function updateTime(id, edge, value) {
    const item = byId(id);
    if (!item || state.submitted || !Number.isFinite(value)) return;
    const others = state.segments.filter(segment => segment.id !== id);
    const next = {...item, [edge]:Math.round(value * 10) / 10};
    placeSegment(next, others);
    Object.assign(item, next);
    markDirty();
  }
  function removeSelected() {
    const item = selected();
    if (!item || state.submitted || !window.confirm(`删除片段 ${segmentNumber(item)}（${format(item.start)}–${format(item.end)}）？`)) return;
    state.segments = state.segments.filter(segment => segment.id !== item.id);
    state.selectedId = sortSegments(state.segments)[0]?.id || '';
    markDirty();
  }

  class PreTrainingQualityTimeline extends HTMLElement {
    connectedCallback() {
      if (this.dataset.ready) return;
      this.dataset.ready = 'true';
      this.hidden = true;
      this.playTime = 0;
      this.playing = false;
      this.draft = null;
      this.rangeEdit = null;
      this.addEventListener('click', event => this.onClick(event));
      this.addEventListener('change', event => this.onChange(event));
      this.addEventListener('pointerdown', event => this.onPointerDown(event));
      document.addEventListener(eventName('state-change'), () => this.render());
      document.addEventListener(eventName('seek'), event => { this.pause(); this.playTime = event.detail.seconds; this.updatePlayback(); });
      this.addEventListener('keydown',event=>{
        if(!event.target.matches('.prq-playhead')||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
        event.preventDefault();this.pause();this.playTime=event.key==='Home'?0:event.key==='End'?DURATION:clamp(this.playTime+(event.key==='ArrowLeft'?-.1:.1),0,DURATION);this.updatePlayback();
      });
      this.render();
    }
    disconnectedCallback() { clearInterval(this.timer); }
    onChange(event) {
      const field = event.target.dataset.range;
      if (!field || state.submitted) return;
      const value = parseTime(event.target.value);
      if (!Number.isFinite(value)) { this.render(); return; }
      if (field === 'start') state.rangeStart = clamp(value,0,DURATION);
      if (field === 'end') state.rangeEnd = clamp(value,0,DURATION);
      if (state.rangeEnd - state.rangeStart < .3) {
        if (field === 'start') state.rangeStart = Math.max(0,state.rangeEnd-.3);
        else state.rangeEnd = Math.min(DURATION,state.rangeStart+.3);
      }
      this.render();
    }
    onClick(event) {
      const segment = event.target.closest('[data-segment-id]');
      if (segment) { selectSegment(segment.dataset.segmentId); return; }
      const control = event.target.closest('timeline-controls');
      if (control) {
        if (event.target.closest('.segmented-timeline__play')) this.togglePlay();
        const tool = event.target.closest('.segmented-timeline__tool')?.getAttribute('aria-label');
        if (tool === '添加' && !state.submitted) addSegment();
        if (tool === '添加并前进' && !state.submitted) { addSegment(); this.advanceRange(); }
        if (tool === '仅前进' && !state.submitted) this.advanceRange();
        if (tool === '清空') removeSelected();
        if (event.target.closest('.segmented-timeline__standard')) document.dispatchEvent(new CustomEvent(eventName('open-rules')));
      }
    }
    onPointerDown(event) {
      const playhead=event.target.closest('.prq-playhead');
      if(playhead){
        event.preventDefault();event.stopPropagation();this.pause();
        const rect=this.querySelector('.prq-public-rail').getBoundingClientRect();
        const move=e=>{this.playTime=clamp((e.clientX-rect.left)/rect.width*DURATION,0,DURATION);this.updatePlayback();};
        const up=()=>{document.removeEventListener('pointermove',move);document.removeEventListener('pointerup',up);};
        document.addEventListener('pointermove',move);document.addEventListener('pointerup',up);return;
      }
      const handle = event.target.closest('[data-resize]');
      // 正式片段的边界只允许在公共时间轴调整，业务轨道仅负责展示和选中。
      if (handle) return;
      if(event.target.closest('[data-segment-id]'))return;
      const publicRail = event.target.closest('.prq-public-rail');
      if (!publicRail || event.button !== 0 || state.submitted) return;
      this.pause();
      event.preventDefault();
      const rect = publicRail.getBoundingClientRect();
      const toTime = x => clamp((x - rect.left) / rect.width * DURATION, 0, DURATION);
      const rangeHandle = event.target.closest('[data-range-handle]');
      const rangeFill = event.target.closest('.prq-draft-range');
      if (rangeHandle || rangeFill) {
        const mode = rangeHandle?.dataset.rangeHandle || 'fill';
        const originX = event.clientX;
        const shown = selected() || {start:state.rangeStart,end:state.rangeEnd};
        const originStart = shown.start;
        const originEnd = shown.end;
        const targetId = selected()?.id || '';
        this.rangeEdit = {start:originStart,end:originEnd,targetId};
        const moveRange = moveEvent => {
          if (mode === 'start') this.rangeEdit.start = Math.min(toTime(moveEvent.clientX),this.rangeEdit.end-.3);
          else if (mode === 'end') this.rangeEdit.end = Math.max(toTime(moveEvent.clientX),this.rangeEdit.start+.3);
          else {
            const width = originEnd-originStart;
            const delta = (moveEvent.clientX-originX)/rect.width*DURATION;
            this.rangeEdit.start = clamp(originStart+delta,0,DURATION-width);
            this.rangeEdit.end = this.rangeEdit.start+width;
          }
          this.renderCandidate();
        };
        const endRange = () => {
          const nextStart=Math.round(this.rangeEdit.start*10)/10, nextEnd=Math.round(this.rangeEdit.end*10)/10;
          if (targetId) updateTime(targetId,'start',nextStart), updateTime(targetId,'end',nextEnd);
          else { state.rangeStart=nextStart; state.rangeEnd=nextEnd; }
          this.rangeEdit = null;
          document.removeEventListener('pointermove',moveRange);
          document.removeEventListener('pointerup',endRange);
          this.render();
        };
        document.addEventListener('pointermove',moveRange);
        document.addEventListener('pointerup',endRange);
        return;
      }
      const start = toTime(event.clientX);
      this.draft = {start,end:start};
      const move = moveEvent => { this.draft.end = toTime(moveEvent.clientX); this.renderDraft(); };
      const up = upEvent => {
        const end = toTime(upEvent.clientX);
        document.removeEventListener('pointermove',move); document.removeEventListener('pointerup',up);
        this.draft = null;
        if (Math.abs(end-start) >= .3) {
          state.selectedId = '';
          state.rangeStart = Math.round(Math.min(start,end)*10)/10;
          state.rangeEnd = Math.round(Math.max(start,end)*10)/10;
          this.render();
        }
        else { this.playTime = start; this.updatePlayback(); }
      };
      document.addEventListener('pointermove',move); document.addEventListener('pointerup',up);
    }
    renderDraft() {
      const node=this.querySelector('.prq-draft-range');
      if(!node||!this.draft)return;
      node.hidden=false;
      node.style.left=`${Math.min(this.draft.start,this.draft.end)/DURATION*100}%`;
      node.style.width=`${Math.abs(this.draft.end-this.draft.start)/DURATION*100}%`;
    }
    renderCandidate() {
      const node=this.querySelector('.prq-draft-range');
      if(!node)return;
      const range=this.rangeEdit || (selected()?selected():{start:state.rangeStart,end:state.rangeEnd});
      node.style.left=`${range.start/DURATION*100}%`;
      node.style.width=`${(range.end-range.start)/DURATION*100}%`;
      const start=node.querySelector('.prq-range-label.is-start');
      const end=node.querySelector('.prq-range-label.is-end');
      if(start)start.textContent=format(range.start);
      if(end)end.textContent=format(range.end);
    }
    advanceRange() {
      const width=state.rangeEnd-state.rangeStart;
      state.rangeStart=state.rangeEnd>=DURATION?0:Math.min(state.rangeEnd,DURATION-width);
      state.rangeEnd=Math.min(DURATION,state.rangeStart+width);
      this.playTime=state.rangeStart;
      this.render();
    }
    togglePlay() {
      this.playing = !this.playing;
      clearInterval(this.timer);
      if (this.playing) this.timer=setInterval(()=>{
        this.playTime = Math.min(DURATION,this.playTime+.1);
        if(this.playTime>=DURATION)this.pause();
        this.updatePlayback();
      },100);
      this.updatePlayback();
    }
    pause(){this.playing=false;clearInterval(this.timer);this.querySelector('timeline-controls')?.setPlaying(false);}
    updatePlayback(){
      const hits=state.segments.filter(item=>item.start<=this.playTime&&this.playTime<item.end).map(item=>item.id);
      this.querySelectorAll('.prq-block').forEach(block=>block.classList.toggle('is-hit',hits.includes(block.dataset.segmentId)));
      const head=this.querySelector('.prq-playhead');
      if(head){head.style.left=`calc(68px + (100% - 68px) * ${this.playTime/DURATION})`;head.setAttribute('aria-valuenow',this.playTime);head.setAttribute('aria-valuetext',format(this.playTime));}
      const playback=this.querySelector('.segmented-timeline__playback span');
      if(playback)playback.innerHTML=`<b>${format(this.playTime)}</b> <i>/</i> ${format(DURATION)}`;
      this.querySelector('timeline-controls')?.setPlaying(this.playing);
      document.dispatchEvent(new CustomEvent(eventName('playback'),{detail:{hits}}));
    }
    moveGlobal(direction) {
      const ordered=sortSegments(state.segments), index=ordered.findIndex(item=>item.id===state.selectedId);
      const target=ordered[index+direction]; if(target)selectSegment(target.id);
    }
    block(item,hits) {
      const isSelected=item.id===state.selectedId;
      const trackItems=state.segments.filter(candidate=>candidate.track===item.track);
      const overlaps=trackItems.some(candidate=>candidate.id!==item.id&&overlapDuration(candidate,item)>0);
      const duration=item.end-item.start;
      const layer=isSelected?trackItems.length+2:1+trackItems.filter(candidate=>{
        const otherDuration=candidate.end-candidate.start;
        return otherDuration>duration||(otherDuration===duration&&candidate.order<item.order);
      }).length;
      return `<button type="button" data-segment-id="${escape(item.id)}" class="prq-block is-${item.conclusion}${isShortDuration(item)?' is-short-duration':''}${isSelected?' is-selected':''}${overlaps?' is-overlap':''}${hits.includes(item.id)?' is-hit':''}${valid(item)?'':' has-error'}" style="left:${item.start/DURATION*100}%;width:${Math.max(0,(item.end-item.start)/DURATION*100)}%;z-index:${layer}" title="${String(segmentNumber(item)).padStart(2,'0')} · ${conclusionLabel(item.conclusion)} · ${format(item.start)}–${format(item.end)}"></button>`;
    }
    render() {
      const hits=state.segments.filter(item=>item.start<=this.playTime&&this.playTime<item.end).map(item=>item.id);
      const play=clamp(this.playTime/DURATION*100,0,100);
      const shown=selected()||{start:state.rangeStart,end:state.rangeEnd};
      this.innerHTML=`<section class="prq-timeline" aria-label="预训练质检公共时间轴">
        <timeline-controls standard-label="质检标准"></timeline-controls>
        <div class="prq-track-stack"><div class="prq-ruler"><span class="prq-ruler-label" aria-hidden="true"></span><div class="prq-ruler-rail">${[0,10,20,30,40].map(value=>`<span style="left:${value/DURATION*100}%">${format(value)}</span>`).join('')}</div></div><div class="prq-public-timeline"><span aria-hidden="true"></span><div class="segmented-timeline__range-rail prq-public-rail" aria-label="公共时间轴：调整当前片段或待添加片段区间"><i class="prq-draft-range" style="left:${shown.start/DURATION*100}%;width:${(shown.end-shown.start)/DURATION*100}%"><span class="prq-range-label is-start">${format(shown.start)}</span><span class="prq-range-label is-end">${format(shown.end)}</span><button type="button" class="prq-range-handle is-start" data-range-handle="start" aria-label="调整片段开始时间"></button><button type="button" class="prq-range-handle is-end" data-range-handle="end" aria-label="调整片段结束时间"></button></i></div></div><div class="prq-lanes">${Array.from({length:TRACK_COUNT},(_,track)=>`<div class="prq-lane"><small>轨道 ${track+1}</small><div class="prq-lane-rail">${state.segments.filter(item=>item.track===track).map(item=>this.block(item,hits)).join('')}</div></div>`).join('')}</div><i class="segmented-timeline__playhead prq-playhead" role="slider" tabindex="0" aria-label="公共播放位置" aria-valuemin="0" aria-valuemax="40" aria-valuenow="${this.playTime}" style="left:calc(68px + (100% - 68px) * ${play/100})"></i></div>
      </section>`;
      const playback=this.querySelector('.segmented-timeline__playback span');
      if(playback)playback.innerHTML=`<b>${format(this.playTime)}</b> <i>/</i> ${format(DURATION)}`;
      const playButton=this.querySelector('.segmented-timeline__play');
      if(playButton)playButton.setAttribute('aria-label',this.playing?'暂停':'播放');
      this.updatePlayback();
    }
  }

  class PreTrainingQualityWorkspace extends HTMLElement {
    connectedCallback() {
      if(this.dataset.ready)return;
      this.dataset.ready='true';
      this.timeline=document.createElement(elementName('timeline'));
      document.querySelector('.timeline-card')?.append(this.timeline);
      document.addEventListener(eventName('state-change'),()=>this.render());
      document.addEventListener(eventName('open-rules'),()=>this.querySelector(`#${domPrefix}RuleDialog`)?.showModal());
      this.addEventListener('click',event=>this.onClick(event));
      this.addEventListener('change',event=>this.onChange(event));
      document.addEventListener('keydown',event=>this.onKey(event));
      document.addEventListener('pointerdown',event=>{
        if(this.hidden)return;
        if(this.reasonsOpen&&!this.querySelector('.prq-reason-select')?.contains(event.target))this.closeMenus();
        if(this.reviewErrorOpen&&!this.querySelector('.prq-review-error-select')?.contains(event.target))this.closeMenus();
      },true);
      this.render();
    }
    closeMenus(){
      this.reasonsOpen=false;this.reviewErrorOpen=false;
      this.querySelectorAll('.prq-reason-menu,.prq-review-error-menu').forEach(menu=>{menu.hidden=true;});
      this.querySelectorAll('[data-action="toggle-reasons"],[data-action="toggle-review-error"]').forEach(trigger=>trigger.setAttribute('aria-expanded','false'));
    }
    set hidden(value){this.toggleAttribute('hidden',value);if(this.timeline){this.timeline.hidden=value;if(value)this.timeline.pause();}if(value)this.closeMenus();}
    get hidden(){return this.hasAttribute('hidden');}
    moveGlobal(direction){
      const ordered=sortSegments(state.segments),index=ordered.findIndex(item=>item.id===state.selectedId),target=ordered[index+direction];
      if(target)selectSegment(target.id);
    }
    moveTrack(direction){
      const item=selected(); if(!item)return;
      const ordered=sortSegments(state.segments.filter(candidate=>candidate.track===item.track));
      const target=ordered[ordered.findIndex(candidate=>candidate.id===item.id)+direction]; if(target)selectSegment(target.id);
    }
    onKey(event){
      if(!this.hidden&&event.key==='Escape'){this.closeMenus();return;}
      if(this.hidden||state.submitted||!(event.ctrlKey||event.metaKey))return;
      const action={ArrowUp:()=>this.moveGlobal(-1),ArrowDown:()=>this.moveGlobal(1),ArrowLeft:()=>this.moveTrack(-1),ArrowRight:()=>this.moveTrack(1)}[event.key];
      if(action){event.preventDefault();action();}
    }
    onClick(event){
      const action=event.target.closest('[data-action]')?.dataset.action;
      const reviewReason=event.target.closest('[data-review-error]')?.dataset.reviewError;
      if(reviewReason&&!state.submitted){const item=selected();if(item){item.reviewErrorReason=reviewReason;this.reviewErrorOpen=false;markDirty();}return;}
      if(!action)return;
      if(action==='previous')this.moveGlobal(-1);
      if(action==='next')this.moveGlobal(1);
      if(action==='track-left')this.moveTrack(-1);
      if(action==='track-right')this.moveTrack(1);
      if(action==='delete')removeSelected();
      if(action==='toggle-reasons'&&!state.submitted){this.reasonsOpen=!this.reasonsOpen;this.reviewErrorOpen=false;this.render();}
      if(action==='toggle-review-error'&&!state.submitted){this.reviewErrorOpen=!this.reviewErrorOpen;this.reasonsOpen=false;this.render();}
      if(action==='clear-review-error'&&!state.submitted){const item=selected();if(item){item.reviewErrorReason='';this.reviewErrorOpen=false;markDirty();}}
    }
    onChange(event){
      const item=selected(); if(!item||state.submitted)return;
      const field=event.target.dataset.field;
      if(field==='conclusion'){
        item.conclusion=event.target.value;
        item.autoShortDuration=false;
        this.reasonsOpen=item.conclusion!=='pending';
        markDirty(); return;
      }
      if(field==='reason'){
        const list=event.target.dataset.kind==='mistake'?item.mistakeReasons:item.rejectedReasons;
        if(event.target.checked&&!list.includes(event.target.value))list.push(event.target.value);
        if(!event.target.checked){const index=list.indexOf(event.target.value);if(index>=0)list.splice(index,1);}
        markDirty(); return;
      }
    }
    reasonGroup(title,requirement,kind,items,values){
      return `<section><header><b>${title}</b><em class="${requirement==='必选'?'is-required':''}">${requirement}</em></header>${items.map(item=>`<label title="${escape(item.detail)}"><input type="checkbox" data-field="reason" data-kind="${kind}" value="${item.id}" ${values.includes(item.id)?'checked':''}><span>${escape(item.name)}</span></label>`).join('')}</section>`;
    }
    render(){
      const item=selected();
      if(!item){this.innerHTML=`<section class="prq-editor card"><div class="prq-empty"><b>尚未记录问题片段</b><span>在时间轴刻度拖拽创建片段，或设置起止时间后点击添加。</span></div></section>${this.ruleDialog()}`;return;}
      const ordered=sortSegments(state.segments),globalIndex=ordered.findIndex(candidate=>candidate.id===item.id);
      const trackItems=sortSegments(state.segments.filter(candidate=>candidate.track===item.track));
      const trackIndex=trackItems.findIndex(candidate=>candidate.id===item.id),errors=segmentErrors(item);
      const reasons=[...item.mistakeReasons,...item.rejectedReasons].map(reasonName);
      const trigger=item.conclusion==='pending'?'选择结论后设置原因':reasons.length?`${escape(reasons[0])}${reasons.length>1?` <em>+${reasons.length-1}</em>`:''}`:'请选择必选原因';
      const menu=item.conclusion==='pending'||state.submitted?'':`<div class="prq-reason-menu" ${this.reasonsOpen?'':'hidden'}>${this.reasonGroup('失误原因',item.conclusion==='mistake'?'必选':'选填','mistake',RULE.mistake,item.mistakeReasons)}${item.conclusion==='rejected'||item.rejectedReasons.length?this.reasonGroup(item.conclusion==='rejected'?'不合格原因':'不兼容原因',item.conclusion==='rejected'?'必选':'请移除','rejected',item.conclusion==='rejected'?RULE.rejected:RULE.rejected.filter(reason=>item.rejectedReasons.includes(reason.id)),item.rejectedReasons):''}</div>`;
      const reviewTrigger=item.reviewErrorReason||'请选择错误原因';
      const reviewMenu=`<div class="prq-review-error-menu" ${this.reviewErrorOpen?'':'hidden'} role="listbox">${REVIEW_ERROR_REASONS.map(reason=>`<button type="button" data-review-error="${escape(reason)}" role="option" class="${item.reviewErrorReason===reason?'is-selected':''}">${escape(reason)}<span>✓</span></button>`).join('')}<button type="button" class="prq-review-error-clear" data-action="clear-review-error">清除错误原因</button></div>`;
      this.innerHTML=`<section class="prq-editor card">
        <header><div class="prq-editor-fields"><span class="prq-id is-${item.conclusion}${isShortDuration(item)?' is-short-duration':''}">${String(globalIndex+1).padStart(2,'0')}</span><label>开始<span class="prq-time-field">${format(item.start)}</span></label><label>结束<span class="prq-time-field">${format(item.end)}</span></label><span>时长 <b>${Math.max(0,item.end-item.start).toFixed(1)}s</b></span><div class="prq-conclusion-switch" aria-label="片段结论">${[['pending','待判定'],['mistake','失误'],['rejected','不合格']].map(([value,name])=>`<label class="is-${value}${item.conclusion===value?' is-active':''}"><input type="radio" name="${domPrefix}-conclusion" data-field="conclusion" value="${value}" ${item.conclusion===value?'checked':''} ${state.submitted?'disabled':''}>${name}</label>`).join('')}</div><div class="prq-reason-select"><button type="button" data-action="toggle-reasons" aria-expanded="${this.reasonsOpen}" ${item.conclusion==='pending'||state.submitted?'disabled':''}><span>${trigger}</span><img src="/static/annotation_workbench/assets/icon-chevron.svg" alt=""></button>${menu}</div></div>
        <div class="segment-actions prq-editor-actions"><button class="segment-action segment-action--navigate" data-action="previous" ${globalIndex<=0?'disabled':''}>上一段 <kbd>⌘↑</kbd></button><button class="segment-action segment-action--navigate" data-action="next" ${globalIndex>=ordered.length-1?'disabled':''}>下一段 <kbd>⌘↓</kbd></button><button class="segment-action" data-action="track-left" ${trackIndex<=0?'disabled':''}>同轨左 <kbd>⌘←</kbd></button><button class="segment-action" data-action="track-right" ${trackIndex>=trackItems.length-1?'disabled':''}>同轨右 <kbd>⌘→</kbd></button><button class="segment-action segment-action--danger" data-action="delete" ${state.submitted?'disabled':''}>删除</button></div></header>
        <div class="prq-editor-lower"><label><span>错误原因</span><div class="prq-review-error-select"><button type="button" data-action="toggle-review-error" aria-expanded="${this.reviewErrorOpen}" ${state.submitted?'disabled':''}><span>${escape(reviewTrigger)}</span><img src="/static/annotation_workbench/assets/icon-chevron.svg" alt=""></button>${reviewMenu}</div></label><div class="prq-field-state ${errors.length?'has-error':'is-complete'}">${errors.length?`${item.conclusion==='pending'?'待判定':'待补充'}：${errors.map(escape).join('、')}`:'当前片段已完善'}</div></div>
      </section>${this.ruleDialog()}`;
    }
    ruleDialog(){return `<dialog id="${domPrefix}RuleDialog" class="prq-dialog"><header><div><h2>${label}采集质检规则</h2><p>${RULE.name} · ${RULE.id} · ${RULE.version}</p></div><button type="button" onclick="this.closest('dialog').close()" aria-label="关闭">×</button></header><div class="prq-rule-body"><section><h3>失误标准</h3>${RULE.mistake.map(item=>`<article><b>${escape(item.name)}</b><p>${escape(item.detail)}</p></article>`).join('')}</section><section><h3>不合格标准</h3>${RULE.rejected.map(item=>`<article><b>${escape(item.name)}</b><p>${escape(item.detail)}</p></article>`).join('')}</section><div class="prq-fixed-rule"><b>固定汇总规则</b><p>无问题片段为合格；只有失误片段为失误；存在任意不合格片段为不合格。</p></div></div></dialog>`;}
  }

  class PreTrainingQualitySidebar extends HTMLElement {
    connectedCallback(){
      if(this.dataset.ready)return;
      this.dataset.ready='true';
      document.addEventListener(eventName('state-change'),()=>this.render());
      document.addEventListener(eventName('meta-change'),()=>this.render());
      document.addEventListener(eventName('playback'),event=>{
        this.hits=event.detail.hits;
        this.querySelectorAll('.prq-list-item').forEach(row=>row.classList.toggle('is-hit',this.hits.includes(row.dataset.segmentId)));
      });
      this.addEventListener('click',event=>this.onClick(event));
      this.addEventListener('confirm-dialog-confirm',event=>{
        if(event.detail.variant!=='reject')return;
        event.stopPropagation();
        if(!state.submitted&&this.save()){
          document.dispatchEvent(new CustomEvent(eventName('reject'),{detail:{reason:event.detail.value,segments:state.segments}}));
          this.toast('质检已驳回，草稿已保存');
        }
      });
      this.render();
    }
    toast(message){document.dispatchEvent(new CustomEvent(eventName('toast'),{detail:{message}}));}
    save(){
      try{localStorage.setItem(DRAFT_KEY,JSON.stringify({segments:state.segments,selectedId:state.selectedId,revision:state.revision,savedAt:new Date().toISOString()}));state.dirty=false;notify();this.toast('草稿已保存');return true;}
      catch(_){this.toast('保存失败，请重试');return false;}
    }
    onClick(event){
      const row=event.target.closest('[data-segment-id]');
      if(row){selectSegment(row.dataset.segmentId);return;}
      const action=event.target.closest('[data-action]')?.dataset.action;
      if(action==='save'&&!state.submitted)this.save();
      if(action==='leave'&&!state.submitted&&this.save())this.toast('草稿已保存');
      if(action==='reject'&&!state.submitted)this.querySelector('workbench-confirm-dialog[variant="reject"]')?.show();
      if(action==='submit'&&!state.submitted){
        if(invalidCount()){this.querySelector(`#${domPrefix}ErrorDialog`)?.showModal();return;}
        const shortCount=validateUsableDuration();
        const dialog=this.querySelector(`#${domPrefix}SubmitDialog`);
        dialog.querySelector('[data-result]').textContent=calculatedConclusion();
        dialog.querySelector('[data-counts]').textContent=`失误 ${state.segments.filter(item=>item.conclusion==='mistake').length} 条 · 不合格 ${state.segments.filter(item=>item.conclusion==='rejected').length} 条 · 规则 ${RULE.version}`;
        dialog.querySelector('[data-duration-check]').textContent=shortCount?`检测到 ${shortCount} 处可用片段不足 3 秒，已自动标记为失误，原因：可用时长太短。`:'可用片段时长校验通过。';
        dialog.showModal();
      }
      if(action==='confirm-submit'){
        if(invalidCount())return;
        state.submitted=true;state.dirty=false;state.revision+=1;
        try{localStorage.removeItem(DRAFT_KEY);}catch(_){}
        this.querySelector(`#${domPrefix}SubmitDialog`)?.close();notify();this.toast('质检已提交');
      }
    }
    render(){
      const ordered=sortSegments(state.segments),pending=pendingCount(),canSubmit=!pending&&!state.submitted;
      const conclusion=calculatedConclusion(),conclusionClass=conclusion==='合格'?'is-pass':conclusion==='失误'?'is-mistake':conclusion==='不合格'?'is-rejected':'is-pending';
      const rows=ordered.map(item=>{
        return `<button type="button" data-segment-id="${escape(item.id)}" class="prq-list-item${isShortDuration(item)?' is-short-duration':''}${item.id===state.selectedId?' is-active':''}${this.hits?.includes(item.id)?' is-hit':''}${valid(item)?'':' has-error'}"><span class="prq-list-id">${String(ordered.indexOf(item)+1).padStart(2,'0')}</span><span class="prq-list-main"><span class="prq-list-time">${format(item.start)}–${format(item.end)} <em>${(item.end-item.start).toFixed(1)}s</em></span><span class="prq-list-summary"><b class="is-${item.conclusion}">${conclusionLabel(item.conclusion)}</b><strong>${escape(reasonSummary(item))}</strong></span>${valid(item)?'':`<i>${escape(segmentErrors(item)[0])}</i>`}</span></button>`;
      }).join('');
      this.innerHTML=`<section class="prq-sidebar"><header><div><b>质检列表</b><span>共 ${ordered.length} 个问题片段</span></div></header><div class="prq-list">${ordered.length?rows:'<div class="prq-list-empty">尚未记录问题片段</div>'}</div><footer><div class="prq-video-conclusion"><span class="prq-conclusion-label">质检结论</span><output id="${domPrefix}VideoConclusion" class="${conclusionClass}" aria-label="质检结论，由系统自动计算">${conclusion}</output></div><div class="prq-conclusion-meta">系统自动计算 · 失误 ${state.segments.filter(item=>item.conclusion==='mistake').length} · 不合格 ${state.segments.filter(item=>item.conclusion==='rejected').length}${pending?` · 待判定 ${pending}`:''}</div><workbench-footer-actions hydrate><div class="workbench-footer-actions"><button type="button" data-action="save" ${state.submitted?'disabled':''}>保存</button><button type="button" data-action="leave" ${state.submitted?'disabled':''}>释放</button><button type="button" data-action="reject" ${state.submitted?'disabled':''}>驳回</button><button type="button" class="${canSubmit?'':'is-blocked'}" data-action="submit" ${canSubmit?'':'disabled'}>提交</button></div></workbench-footer-actions></footer></section><workbench-confirm-dialog variant="reject"></workbench-confirm-dialog>
        <dialog id="${domPrefix}ErrorDialog" class="prq-dialog prq-error-dialog"><header><h2>暂时无法提交</h2><button onclick="this.closest('dialog').close()" aria-label="关闭">×</button></header><div><b>标注有问题</b><p>${invalidCount()} 个问题片段存在待判定或必填项缺失，请检查后提交。</p></div><footer><button onclick="this.closest('dialog').close()">我知道了</button></footer></dialog>
        <dialog id="${domPrefix}SubmitDialog" class="prq-dialog prq-submit-dialog ${conclusionClass}"><header><h2>确认提交质检</h2><button onclick="this.closest('dialog').close()" aria-label="关闭">×</button></header><div><span>系统计算的视频结论</span><strong data-result></strong><p data-counts></p><p data-duration-check></p><small>提交后将保存全部片段和本次质检结果。</small></div><footer><button onclick="this.closest('dialog').close()">取消</button><button class="is-primary" data-action="confirm-submit">确认提交</button></footer></dialog>`;
    }
  }

  customElements.define(elementName('timeline'),PreTrainingQualityTimeline);
  customElements.define(elementName('workspace'),PreTrainingQualityWorkspace);
  customElements.define(elementName('sidebar'),PreTrainingQualitySidebar);

  let toastTimer;
  document.addEventListener(eventName('toast'),event=>{
    const notice=document.getElementById('workbenchNotice');
    if(!notice)return;
    notice.textContent=event.detail.message;notice.hidden=false;
    clearTimeout(toastTimer);toastTimer=setTimeout(()=>{notice.hidden=true;},2600);
  });

  window.__preTrainingQualityRules = {
    overlapDuration, trackOverlap, sortSegments, calculateConclusion, calculatedConclusion, usableRanges, validateUsableDuration, pendingCount, isShortDuration,
    placeSegment:(candidate,segments)=>placeSegment(clone(candidate),clone(segments)),
    segmentErrors:segment=>segmentErrors(clone(segment)),
    constants:{duration:DURATION,trackCount:TRACK_COUNT}
  };
  window.PreTrainingQualityDemo = {state,addSegment,updateTime,selectSegment,segmentErrors,placeSegment};
})();
