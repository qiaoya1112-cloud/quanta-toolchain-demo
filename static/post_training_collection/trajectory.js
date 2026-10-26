/* 【新】Recording 轨迹只读查看；真实记录只使用显式 trajectory，不根据质量或视频推测轨迹。 */
(() => {
  'use strict';
  let current=null, library=null;
  const parts=[['left','左臂'],['torso','躯干'],['right','右臂'],['base','Base'],['all','总览']];
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const clock=value=>`${Math.floor(value/60)}:${String(Math.floor(value%60)).padStart(2,'0')}`;
  const colors=['#62b642','#a0ce74','#3c7657','#248aa1','#66b8d5','#245f78'];
  function loadCharts(){
    if(window.echarts)return Promise.resolve(window.echarts);
    return library||=new Promise((resolve,reject)=>{
      const script=document.createElement('script');script.src='/static/post_training_collection/vendor/echarts-5.6.0.min.js';
      script.onload=()=>resolve(window.echarts);script.onerror=()=>{script.remove();library=null;reject(new Error('图表加载失败'));};document.head.append(script);
    });
  }
  function demoData(id,duration=8){
    const seed=[...id].reduce((sum,c)=>sum+c.charCodeAt(0),0)%19/10;
    const tracks={};
    for(const [index,[key]] of parts.slice(0,4).entries()){
      const track={state:[],cmd:[]},scale=key==='base'?.14:.35;
      for(let i=0;i<=240;i++){
        const p=i/240,t=p*duration,a=p*Math.PI*2;
        for(const [type,offset] of [['state',0],['cmd',.045]]){
          const phase=a+index*.8+seed+offset;
          track[type].push({t,x:scale*(Math.sin(phase)-Math.sin(index*.8+seed+offset)),y:scale*.65*(Math.cos(phase*.8)-Math.cos((index*.8+seed+offset)*.8)),angle:Math.sin(phase)*.15});
        }
      }
      tracks[key]=track;
    }
    return {duration,tracks,demo:true};
  }
  function normalizeData(record){
    // Explicit media or trajectory prevents a real record from silently inheriting fixtures.
    if(!Object.hasOwn(record,'trajectory')&&/^DEMO-R-\d+$/.test(record.id)&&!Object.hasOwn(record,'videos'))return demoData(record.id);
    const input=record.trajectory;
    if(!input||typeof input!=='object')return null;
    const tracks={};let end=0;
    for(const [key] of parts.slice(0,4)){
      const source=input.tracks?.[key];if(!source)continue;
      const track={};
      for(const type of ['state','cmd']){
        track[type]=(Array.isArray(source[type])?source[type]:[]).filter(p=>[p?.t,p?.x,p?.y].every(Number.isFinite)&&p.t>=0).map(p=>({t:p.t,x:p.x,y:p.y,angle:Number.isFinite(p.angle)?p.angle:null})).sort((a,b)=>a.t-b.t);
        // Bound rendering cost without manufacturing missing samples.
        if(track[type].length>4000){const source=track[type],step=Math.ceil(source.length/4000);track[type]=source.filter((_,i)=>i%step===0||i===source.length-1);}
        end=Math.max(end,track[type].at(-1)?.t||0);
      }
      if(track.state.length||track.cmd.length)tracks[key]=track;
    }
    return Object.keys(tracks).length&&end>0?{tracks,duration:end,demo:false}:null;
  }
  function release(){
    const state=current;if(!state)return;current=null;
    cancelAnimationFrame(state.frame);state.observer?.disconnect();state.abort.abort();
    if(document.fullscreenElement&&state.dialog.contains(document.fullscreenElement))document.exitFullscreen().catch(()=>{});
    for(const video of state.videos){video.pause();video.removeAttribute('src');video.load();}
    state.speed?.dispose();state.xy?.dispose();
  }
  function setStatus(state,message){if(current===state)state.dialog.querySelector('[data-trajectory-status]').textContent=message;}
  function pause(state){state.playing=false;state.resume=false;state.mode='independent';state.playEpoch++;for(const video of state.videos)video.pause();updateControls(state);}
  // 【新】每路原生控件独立播放；图表停在同步进度，不跟随单视频。
  function independent(state,video){
    if(current!==state)return;
    state.playing=false;state.resume=false;state.mode='independent';state.playEpoch++;
    for(const other of state.videos)if(other!==video)other.pause();
    updateControls(state);
  }
  function updateControls(state){
    if(current!==state)return;
    for(const video of state.videos){const button=video.closest('.dc-trajectory-frame').querySelector('[data-trajectory-video]');if(!button)continue;button.textContent=video.paused?'▶':'Ⅱ';button.setAttribute('aria-label',`${video.paused?'播放':'暂停'}${video.getAttribute('aria-label')||''}`);button.title=button.getAttribute('aria-label');button.classList.toggle('is-playing',!video.paused);}
    if(!state.data)return;
    const button=state.dialog.querySelector('[data-trajectory-action="play"]');
    button.textContent=state.playing?'暂停':state.time>=state.data.duration?'重播':'播放';button.setAttribute('aria-label',state.playing?'暂停轨迹与视频':'播放轨迹与视频');
    state.dialog.querySelector('[data-trajectory-time]').textContent=`${clock(state.time)} / ${clock(state.data.duration)}`;
    const slider=state.dialog.querySelector('[data-trajectory-seek]');slider.value=state.time;slider.setAttribute('aria-valuetext',clock(state.time));
  }
  function seek(state,time){
    if(state.mode!=='sync'){pause(state);state.mode='sync';}
    state.time=Math.max(0,Math.min(Number(time)||0,state.data.duration));
    for(const video of state.videos)if(video.readyState>=1&&Number.isFinite(video.duration))video.currentTime=Math.min(state.time,video.duration);
    if(state.time>=state.data.duration)pause(state);
    paintCursor(state);updateControls(state);
  }
  async function play(state){
    if(current!==state)return;
    if(state.playing){pause(state);return;}
    if(state.failed){setStatus(state,'视频加载失败，请重新加载');return;}
    pause(state);state.mode='sync';
    if(state.time>=state.data.duration)seek(state,0);
    const rate=Number(state.dialog.querySelector('[data-trajectory-rate]').value);
    for(const video of state.videos){video.playbackRate=rate;if(Number.isFinite(video.duration)&&Math.abs(video.currentTime-Math.min(state.time,video.duration))>.04)video.currentTime=Math.min(state.time,video.duration);}
    if(state.videos.some(v=>v.readyState<2)){state.resume=true;setStatus(state,'视频加载中…');return;}
    state.resume=false;state.playing=true;state.last=performance.now();updateControls(state);
    const epoch=++state.playEpoch;
    try{
      await Promise.all(state.videos.filter(v=>!v.ended).map(v=>v.play()));
      if(current!==state||state.playEpoch!==epoch||!state.playing)return;
      setStatus(state,'');
    }catch(_){if(current===state&&state.playEpoch===epoch){pause(state);setStatus(state,'视频暂时无法播放，请重试');}}
  }
  function selectedTracks(state){return state.part==='all'?Object.entries(state.data.tracks):[[state.part,state.data.tracks[state.part]]];}
  function paintCharts(state){
    if(!state.speed||current!==state)return;
    const selected=selectedTracks(state),all=state.part==='all',speed=[],xy=[];
    for(const [key,track] of selected){
      const prefix=all?`${parts.find(p=>p[0]===key)[1]} · `:'';
      for(const [type,label,base] of [['state','State',0],['cmd','Cmd',3]]){
        const points=track[type]||[];
        const axes=all?['x']:state.part==='base'?['x','y','angle']:['x','y'];
        axes.forEach((axis,index)=>{
          if(axis==='angle'&&!points.some(p=>p.angle!==null))return;
          const values=points.map((p,i)=>{const before=points[Math.max(0,i-1)],dt=p.t-before.t;return [p.t,dt>0&&p[axis]!==null&&before[axis]!==null?(p[axis]-before[axis])/dt:0];});
          speed.push({name:prefix+label+' '+(axis==='angle'?'Angular':axis.toUpperCase()),type:'line',showSymbol:false,lineStyle:{width:1.5,type:type==='cmd'?'dashed':'solid'},color:all?colors[speed.length%colors.length]:colors[base+index],yAxisIndex:axis==='angle'?1:0,data:values});
        });
        if(points.length)xy.push({name:prefix+label+'轨迹',type:'line',showSymbol:false,lineStyle:{width:2,type:type==='cmd'?'dashed':'solid'},color:all?colors[xy.length%colors.length]:colors[base],data:points.map(p=>[p.x,p.y])});
      }
    }
    const common={animation:false,textStyle:{fontFamily:'system-ui, Microsoft YaHei, sans-serif',fontSize:11,color:'#70818a'},legend:{top:4,left:12,right:12,itemWidth:14,itemHeight:7,textStyle:{fontSize:11}},tooltip:{trigger:'axis'},grid:{left:58,right:state.part==='base'?56:24,top:64,bottom:46},aria:{enabled:true}};
    state.speed.setOption({...common,xAxis:{type:'value',name:'时间 (s)',nameLocation:'middle',nameGap:26,min:0,max:state.data.duration,axisLabel:{formatter:value=>Number(value.toFixed(1)),hideOverlap:true},splitLine:{lineStyle:{color:'#edf1f3'}}},yAxis:[{type:'value',name:'m/s',splitLine:{lineStyle:{color:'#edf1f3'}}},{type:'value',name:'rad/s',show:state.part==='base',splitLine:{show:false}}],series:[...speed,{id:'cursor',type:'line',data:[],markLine:{symbol:'none',silent:true,label:{show:false},lineStyle:{color:'#80979f',width:1},data:[{xAxis:state.time}]}}]},true);
    // Keep identical X/Y metric scale, avoiding visual distortion of the path.
    const points=xy.flatMap(series=>series.data),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
    const span=Math.max(Math.max(...xs)-Math.min(...xs),Math.max(...ys)-Math.min(...ys),.1)*1.25,cx=(Math.max(...xs)+Math.min(...xs))/2,cy=(Math.max(...ys)+Math.min(...ys))/2;
    const layout={top:54,bottom:46,left:58,right:24},width=Math.max(60,state.xy.getWidth()-82),height=Math.max(60,state.xy.getHeight()-100),square=Math.min(width,height);
    layout.left=58+(width-square)/2;layout.right=24+(width-square)/2;layout.top=54+(height-square)/2;layout.bottom=46+(height-square)/2;
    state.xy.setOption({...common,grid:layout,tooltip:{trigger:'item',valueFormatter:value=>Number(value).toFixed(3)},xAxis:{type:'value',name:'X (m)',nameLocation:'middle',nameGap:26,min:cx-span/2,max:cx+span/2,axisLabel:{formatter:v=>v.toFixed(2)},splitLine:{lineStyle:{color:'#edf1f3'}}},yAxis:{type:'value',name:'Y (m)',min:cy-span/2,max:cy+span/2,axisLabel:{formatter:v=>v.toFixed(2)},splitLine:{lineStyle:{color:'#edf1f3'}}},series:[...xy,...xy.map((series,i)=>({id:'point-'+i,name:series.name+'当前位置',type:'scatter',symbol:'triangle',symbolSize:10,color:series.color,data:[]}))]},true);
    paintCursor(state);
  }
  function paintCursor(state){
    if(!state.speed||current!==state)return;
    state.speed.setOption({series:[{id:'cursor',markLine:{data:[{xAxis:state.time}]}}]});
    let i=0;const markers=[];
    for(const [,track] of selectedTracks(state))for(const type of ['state','cmd']){
      const points=track[type];if(!points.length)continue;
      const point=points.reduce((nearest,p)=>Math.abs(p.t-state.time)<Math.abs(nearest.t-state.time)?p:nearest,points[0]);
      const before=points[Math.max(0,points.indexOf(point)-1)];
      markers.push({id:'point-'+i++,data:[[point.x,point.y]],symbolRotate:-Math.atan2(point.y-before.y,point.x-before.x)*180/Math.PI+90});
    }
    state.xy.setOption({series:markers});
  }
  async function open({dialog,record,cameras,conclusion}){
    release();dialog.classList.add('dc-trajectory-dialog');
    const data=normalizeData(record),abort=new AbortController();
    const state={dialog,record,data,abort,videos:[],playing:false,failed:false,resume:false,mode:'independent',playEpoch:0,time:0,part:Object.keys(data?.tracks||{})[0],frame:0};current=state;
    const body=dialog.querySelector('.dc-dialog-body');
    body.innerHTML=`<div class="dc-trajectory-meta"><strong>${esc(record.id)}</strong><span>${esc(record.device)} · ${esc(record.operator)}</span>${conclusion}${data?.demo?'<span class="dc-trajectory-demo">示例数据</span>':''}</div>
      <div class="dc-trajectory-frames">${cameras.map((camera,index)=>`<div class="dc-trajectory-frame"><span>${esc(camera.label)}</span>${camera.src?`<video controls muted playsinline preload="auto" aria-label="${esc(camera.label)}视频" src="${esc(camera.src)}" ${camera.poster?`poster="${esc(camera.poster)}"`:''}></video><button type="button" class="dc-trajectory-video-play" data-trajectory-video="${index}" aria-label="播放${esc(camera.label)}视频" title="播放${esc(camera.label)}视频">▶</button>`:'<div class="dc-trajectory-no-video">暂无视频</div>'}</div>`).join('')}</div>
      ${data?`<div class="dc-trajectory-toolbar"><div class="dc-trajectory-tabs" role="tablist" aria-label="轨迹部件">${parts.map(([key,label])=>`<button type="button" role="tab" id="dc-trajectory-tab-${key}" aria-controls="dc-trajectory-plots" aria-selected="${key===state.part}" tabindex="${key===state.part?0:-1}" data-trajectory-action="part" data-part="${key}" ${key!=='all'&&!data.tracks[key]?'disabled':''}>${label}</button>`).join('')}</div><div class="dc-trajectory-buttons"><button type="button" class="dc-btn small" data-trajectory-action="play">播放</button><button type="button" class="dc-btn small" data-trajectory-action="replay">重播</button><select class="dc-select" data-trajectory-rate aria-label="播放速度"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></div></div>
      <div class="dc-trajectory-timeline"><input type="range" min="0" max="${data.duration}" step="0.01" value="0" data-trajectory-seek aria-label="轨迹播放进度"><span data-trajectory-time>0:00 / ${clock(data.duration)}</span></div>
      <div class="dc-trajectory-status" role="status"><span data-trajectory-status>图表加载中…</span><button type="button" class="dc-link" data-trajectory-action="retry" hidden>重新加载</button></div>
      <div class="dc-trajectory-plots" id="dc-trajectory-plots" role="tabpanel" aria-labelledby="dc-trajectory-tab-${state.part}"><section><h3>速度</h3><div class="dc-trajectory-chart" data-trajectory-chart="speed" role="img" aria-label="State 与 Cmd 速度随时间对比"></div></section><section><h3>XY 轨迹</h3><div class="dc-trajectory-chart" data-trajectory-chart="xy" role="img" aria-label="State 与 Cmd 平面运动轨迹"></div></section></div>`:'<div class="dc-trajectory-empty" role="status">暂无轨迹数据</div>'}`;
    state.videos=[...body.querySelectorAll('video')];
    const on=(node,event,listener)=>node.addEventListener(event,listener,{signal:abort.signal});
    for(const video of state.videos){
      on(video,'pointerdown',()=>independent(state,video));
      on(video,'keydown',event=>{if([' ','k','K','ArrowLeft','ArrowRight','Home','End'].includes(event.key))independent(state,video);});
      on(video,'play',()=>{if(state.mode!=='sync'||!state.playing)independent(state,video);});
      on(video,'play',()=>updateControls(state));
      on(video,'pause',()=>updateControls(state));
    }
    for(const video of state.videos){
      const button=document.createElement('button');button.type='button';button.className='dc-trajectory-video-fullscreen';button.setAttribute('data-trajectory-fullscreen','');button.setAttribute('aria-label',`全屏查看${video.getAttribute('aria-label')||''}`);button.title=button.getAttribute('aria-label');button.innerHTML='<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 2H2v4m8-4h4v4M2 10v4h4m8-4v4h-4"/></svg>';video.closest('.dc-trajectory-frame').append(button);
    }
    on(document,'fullscreenchange',()=>{for(const video of state.videos){const frame=video.closest('.dc-trajectory-frame'),button=frame.querySelector('[data-trajectory-fullscreen]');button.setAttribute('aria-label',document.fullscreenElement===frame?'退出全屏':`全屏查看${video.getAttribute('aria-label')||''}`);button.title=button.getAttribute('aria-label');}});
    on(body,'click',event=>{
      const fullButton=event.target.closest('[data-trajectory-fullscreen]');
      if(fullButton){const frame=fullButton.closest('.dc-trajectory-frame'),video=frame.querySelector('video');independent(state,video);const action=document.fullscreenElement===frame?document.exitFullscreen():frame.requestFullscreen();action.catch(()=>{if(state.data)setStatus(state,'暂时无法切换全屏，请重试');});return;}
      const button=event.target.closest('[data-trajectory-video]');if(!button)return;
      const video=button.closest('.dc-trajectory-frame').querySelector('video');if(!video)return;
      event.preventDefault();independent(state,video);if(video.paused)video.play().catch(()=>{if(state.data)setStatus(state,'视频暂时无法播放，请重试');});else video.pause();
    });
    if(!data)return;
    const retry=body.querySelector('[data-trajectory-action="retry"]');
    for(const video of state.videos){
      on(video,'error',()=>{state.failed=true;state.resume=false;if(state.mode==='sync')pause(state);setStatus(state,'视频加载失败');retry.hidden=false;});
      on(video,'waiting',()=>{if(state.playing){pause(state);state.mode='sync';state.resume=true;setStatus(state,'视频缓冲中…');}});
      on(video,'canplay',()=>{if(state.mode==='sync'&&state.resume&&!state.failed)play(state);});
      on(video,'loadedmetadata',()=>{
        if(state.data.demo&&video===state.videos[0]&&Number.isFinite(video.duration)&&video.duration>0){state.data=demoData(record.id,video.duration);body.querySelector('[data-trajectory-seek]').max=video.duration;paintCharts(state);updateControls(state);}
      });
    }
    on(body,'click',event=>{
      const button=event.target.closest('[data-trajectory-action]');if(!button||button.disabled)return;
      switch(button.dataset.trajectoryAction){
        case 'play':play(state);break;
        case 'replay':pause(state);seek(state,0);play(state);break;
        case 'retry':pause(state);state.failed=false;retry.hidden=true;setStatus(state,'视频加载中…');for(const video of state.videos)video.load();break;
        case 'part':state.part=button.dataset.part;for(const tab of body.querySelectorAll('[role="tab"]')){const selected=tab===button;tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1;}body.querySelector('[role="tabpanel"]').setAttribute('aria-labelledby',button.id);paintCharts(state);break;
      }
    });
    on(body,'keydown',event=>{
      const tab=event.target.closest('[role="tab"]');if(!tab||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();const tabs=[...body.querySelectorAll('[role="tab"]:not(:disabled)')],i=tabs.indexOf(tab),next=event.key==='Home'?tabs[0]:event.key==='End'?tabs.at(-1):tabs[(i+(event.key==='ArrowRight'?1:tabs.length-1))%tabs.length];next.click();next.focus();
    });
    on(body.querySelector('[data-trajectory-seek]'),'input',event=>seek(state,event.target.value));
    on(body.querySelector('[data-trajectory-rate]'),'change',event=>{if(state.mode!=='sync')pause(state);for(const video of state.videos)video.playbackRate=Number(event.target.value);});
    function tick(now){
      if(current!==state)return;
      if(state.playing){
        const master=state.videos[0],rate=Number(body.querySelector('[data-trajectory-rate]').value);
        state.time=master&&!master.ended?master.currentTime:Math.min(state.data.duration,state.time+(now-state.last)/1000*rate);
        for(const video of state.videos.slice(1))if(video.readyState>=2&&!video.ended&&Math.abs(video.currentTime-state.time)>.2)video.currentTime=Math.min(state.time,video.duration);
        if(state.time>=state.data.duration)pause(state);
        if(now-(state.painted||0)>70){paintCursor(state);updateControls(state);state.painted=now;}
      }
      state.last=now;state.frame=requestAnimationFrame(tick);
    }
    state.last=performance.now();state.frame=requestAnimationFrame(tick);
    try{
      const charts=await loadCharts();if(current!==state)return;
      state.speed=charts.init(body.querySelector('[data-trajectory-chart="speed"]'));state.xy=charts.init(body.querySelector('[data-trajectory-chart="xy"]'));paintCharts(state);setStatus(state,state.failed?'视频加载失败':'');
      state.observer=new ResizeObserver(()=>{if(current!==state)return;state.speed.resize();state.xy.resize();paintCharts(state);});state.observer.observe(body.querySelector('.dc-trajectory-plots'));
    }catch(_){if(current===state){setStatus(state,'图表加载失败');retry.hidden=false;retry.onclick=()=>open({dialog,record,cameras,conclusion});}}
  }
  window.CollectionTrajectory={open,release};
})();
