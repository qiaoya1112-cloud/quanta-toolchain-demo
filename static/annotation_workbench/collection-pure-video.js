/* Read-only playback inside the shared workbench. */
(() => {
  'use strict';
  const data=JSON.parse(document.getElementById('collection-pure-video-data').textContent);
  const viewer=document.querySelector('workbench-media-viewer');
  const sources=Object.fromEntries(data.cameras.map(camera=>[camera.key,camera]));
  const players=[],play=document.querySelector('[data-video-action="play"]'),seek=document.querySelector('[data-video-seek]');
  const rate=document.querySelector('[data-video-rate]'),time=document.querySelector('[data-video-time]'),status=document.querySelector('[data-video-status]');
  let synced=false,epoch=0,activeVideo=null;
  const available=()=>players.filter(video=>!video.error&&video.readyState>=1);
  const duration=()=>Math.max(0,...available().map(video=>Number.isFinite(video.duration)?video.duration:0));
  const clock=value=>`${String(Math.floor(value/60)).padStart(2,'0')}:${String(Math.floor(value%60)).padStart(2,'0')}`;
  function update(){
    const all=available(),end=duration(),master=synced?all.reduce((longest,video)=>!longest||video.duration>longest.duration?video:longest,null):(all.includes(activeVideo)?activeVideo:all[0]);
    const playing=all.some(video=>!video.paused);
    seek.max=end;seek.disabled=!end;seek.value=master?.currentTime||0;
    time.textContent=`${clock(master?.currentTime||0)} / ${clock(end)}`;
    play.textContent=playing?'Ⅱ':'▶';play.setAttribute('aria-label',playing?'暂停全部视频':'播放全部视频');play.disabled=!all.length;
  }
  const stop=()=>{epoch++;for(const video of players)video.pause();update();};
  const videoMap=[['.workbench-feed--arm:first-child','left','左臂视角'],['.workbench-feed--arm:last-child','right','右臂视角'],['.workbench-feed--three-panel','head','头部视角']];
  for(const [selector,key,label] of videoMap){
    const feed=viewer.querySelector(selector),camera=sources[key];
    feed.querySelector(':scope>img')?.remove();
    if(!camera?.src){const empty=document.createElement('span');empty.className='collection-video-empty';empty.textContent='暂无视频';feed.prepend(empty);feed.querySelector('figcaption img')?.remove();continue;}
    const video=document.createElement('video');video.controls=true;video.playsInline=true;video.muted=true;video.preload='auto';video.src=camera.src;video.setAttribute('aria-label',label+'视频');if(camera.poster)video.poster=camera.poster;feed.prepend(video);players.push(video);
    const caption=feed.querySelector('figcaption'),icon=caption.querySelector('img');
    const fullscreen=document.createElement('button');fullscreen.type='button';fullscreen.className='collection-video-fullscreen';fullscreen.setAttribute('aria-label','全屏查看'+label);if(icon)fullscreen.append(icon);caption.append(fullscreen);
    fullscreen.addEventListener('click',async()=>{try{if(document.fullscreenElement===feed)await document.exitFullscreen();else await feed.requestFullscreen();}catch{status.textContent='暂时无法切换全屏';}});
    const independent=()=>{synced=false;epoch++;activeVideo=video;status.textContent='';for(const other of players)if(other!==video)other.pause();update();};
    video.addEventListener('pointerdown',independent);
    video.addEventListener('keydown',independent);
    video.addEventListener('play',()=>{if(!synced){activeVideo=video;for(const other of players)if(other!==video)other.pause();}update();});
    for(const event of ['loadedmetadata','pause','ended','durationchange'])video.addEventListener(event,update);
    video.addEventListener('timeupdate',()=>{
      const all=available(),master=all.reduce((longest,item)=>!longest||item.duration>longest.duration?item:longest,null);
      if(synced&&video===master)for(const other of all)if(other!==video&&!other.ended&&Math.abs(other.currentTime-video.currentTime)>.3)other.currentTime=Math.min(video.currentTime,other.duration);
      update();
    });
    video.addEventListener('error',()=>{status.textContent='视频加载失败';update();});
  }
  play.addEventListener('click',async()=>{
    const all=available();if(!all.length)return;
    if(all.some(video=>!video.paused)){stop();return;}
    synced=true;const attempt=++epoch;status.textContent='';
    const start=Number(seek.value)>=duration()-.1?0:Number(seek.value);
    for(const video of all){video.currentTime=Math.min(start,video.duration);video.playbackRate=Number(rate.value);}
    try{await Promise.all(all.map(video=>video.play()));if(attempt!==epoch)for(const video of all)video.pause();}
    catch{if(attempt===epoch){stop();status.textContent='视频暂时无法播放，请重试';}}update();
  });
  seek.addEventListener('input',()=>{const position=Number(seek.value);for(const video of available())video.currentTime=Math.min(position,video.duration);update();});
  rate.addEventListener('change',()=>{for(const video of players)video.playbackRate=Number(rate.value);});
  document.addEventListener('fullscreenchange',()=>{for(const button of document.querySelectorAll('.collection-video-fullscreen'))button.setAttribute('aria-label',document.fullscreenElement===button.closest('figure')?'退出全屏':'全屏查看视频');});
  const main=document.querySelector('.main');main.classList.remove('is-loading');main.setAttribute('aria-busy','false');main.querySelectorAll('[inert]').forEach(node=>node.removeAttribute('inert'));main.querySelector('.workbench-loading')?.remove();document.body.classList.remove('theme-pending');
  window.addEventListener('pagehide',()=>{stop();for(const video of players){video.removeAttribute('src');video.load();}});
  update();
})();
