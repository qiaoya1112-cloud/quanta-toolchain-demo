/* Shared processing-record details; keeps the originating collection page intact. */
(() => {
  'use strict';
  const API='/api/post-training-collection/processing',esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let dialog=null,origin=null,requestId=0;
  const safe=value=>{try{const u=new URL(value,location.origin);return value&&['http:','https:'].includes(u.protocol)?u.href:'';}catch{return '';}};
  function close(){requestId++;window.CollectionTrajectory?.release();dialog?.close();dialog?.remove();dialog=null;origin?.focus({preventScroll:true});}
  function open(title,trigger){
    if(dialog)close();origin=trigger||document.activeElement;dialog=document.createElement('dialog');dialog.className='cp-dialog dc-dialog';dialog.setAttribute('aria-label',title);
    dialog.innerHTML=`<header><h2>${esc(title)}</h2><button type="button" aria-label="关闭" data-cp-close>×</button></header><div class="dc-dialog-body"><p role="status">正在加载…</p></div><footer><button type="button" class="btn" data-cp-close>关闭</button></footer>`;
    document.body.append(dialog);dialog.addEventListener('cancel',event=>{event.preventDefault();close();});dialog.addEventListener('click',event=>{if(event.target.closest('[data-cp-close]'))close();});dialog.showModal();return dialog;
  }
  async function read(job,source,id){const response=await fetch(`${API}/tasks/${encodeURIComponent(job)}/records/${encodeURIComponent(source)}/${encodeURIComponent(id)}`,{cache:'no-store'});const data=await response.json();if(!response.ok)throw Error(data.error||'加载失败');return data.record;}
  async function detail(job,source,id,trigger){
    const el=open('数据处理详情',trigger),token=++requestId;
    try{const row=await read(job,source,id);if(token!==requestId||!el.open)return;
      el.querySelector('.dc-dialog-body').innerHTML=`<div class="cp-detail-identity"><strong>${esc(row.id)}</strong><span>${esc(row.processing_name)} · ${esc(job)}</span><span>来源 ${esc(source)} · ${esc(row.source_name)}</span></div>
      <div class="cp-detail-stages">${Object.entries(row.stages).map(([stage,flow])=>{const state=stage==='质检'?row.quality:row.annotation,result=row.member?.results?.[stage];return `<section><div class="cp-stage-head"><h3>${esc(stage)}</h3><span>${esc(state)}</span></div><dl><dt>处理流程</dt><dd>${esc(flow)}</dd><dt>处理结果</dt><dd>${esc(state)}</dd>${result?.summary?`<dt>结果说明</dt><dd>${esc(result.summary)}</dd>`:''}${result?.completed_at?`<dt>完成时间</dt><dd>${esc(result.completed_at.replace('T',' '))}</dd>`:''}</dl></section>`;}).join('')}</div>
      <div class="cp-detail-actions"><button class="btn" data-detail-media>视频 / 轨迹</button></div>`;
      el.querySelector('[data-detail-media]').onclick=()=>media(job,source,id,trigger);
    }catch(error){if(token===requestId)el.querySelector('.dc-dialog-body').innerHTML=`<p role="alert">${esc(error.message)}</p><button class="btn" data-detail-retry>重试</button>`;el.querySelector('[data-detail-retry]')?.addEventListener('click',()=>detail(job,source,id,trigger));}
  }
  async function media(job,source,id,trigger){
    const el=open('视频与轨迹',trigger),token=++requestId;
    try{let row;try{row=await read(job,source,id);}catch{const response=await fetch('/api/post-training-collection/tasks/'+encodeURIComponent(source));const data=await response.json();if(!response.ok)throw Error(data.error||'数据不可用');row={recording:data.task.records.find(r=>r.id===id)};}
      if(token!==requestId||!el.open)return;const record=row.recording;if(!record)throw Error('原始采集数据不存在');
      const cameras=[['head','head','头部'],['left','left_arm','左臂'],['right','right_arm','右臂']].map(([key,view,label])=>{const value=Array.isArray(record.videos)?record.videos.find(v=>[key,view].includes(v.camera)):record.videos?.[key]||record.videos?.[view];const explicit=Object.hasOwn(record,'videos')||['head','left_arm','right_arm'].some(k=>Object.hasOwn(record,k+'_video_url')||Object.hasOwn(record,k+'_compressed_video_url'));const demo=!explicit&&/^DEMO-R-\d+$/.test(record.id);return {key,label,src:safe(typeof value==='string'?value:value?.url||value?.src||record[view+'_compressed_video_url']||record[view+'_video_url']||(demo?'/static/post_training_collection/media/'+key+'.webm':'')),poster:safe(value?.poster||record[view+'_snapshot_url']||''),demo};});
      const previous=document.createElement('button');previous.className='btn';previous.textContent='返回处理详情';previous.onclick=()=>detail(job,source,id,trigger);el.querySelector('footer').prepend(previous);
      await window.CollectionTrajectory.open({dialog:el,record,cameras,conclusion:''});
    }catch(error){if(token===requestId)el.querySelector('.dc-dialog-body').innerHTML=`<p role="alert">${esc(error.message)}</p>`;}
  }
  window.CollectionProcessing={detail,media};
  const boot=document.getElementById('cp-data-context');if(!boot)return;const context=JSON.parse(boot.textContent);
  const scrollKey='quanta.processing.position:'+location.pathname+location.search;
  const scrollElements=()=>[document.scrollingElement,...document.querySelectorAll('main,.q-main,.main-content,.content,.cp-table-wrap')].filter(Boolean);
  try{const saved=JSON.parse(sessionStorage.getItem(scrollKey));if(saved)requestAnimationFrame(()=>scrollElements().forEach((el,i)=>{el.scrollTop=saved[i]?.top||0;el.scrollLeft=saved[i]?.left||0;}));}catch{}
  window.addEventListener('pagehide',()=>{try{sessionStorage.setItem(scrollKey,JSON.stringify(scrollElements().map(el=>({top:el.scrollTop,left:el.scrollLeft}))));}catch{}});
  document.addEventListener('click',event=>{
    const button=event.target.closest('[data-cp-detail],[data-cp-media],[data-linked-video]');if(!button)return;
    if(button.hasAttribute('data-cp-detail'))detail(context.job_id,button.dataset.source,button.dataset.cpDetail,button);
    else if(button.hasAttribute('data-cp-media'))media(context.job_id,button.dataset.source,button.dataset.cpMedia,button);
    else playVideo(button);
  });
  async function playVideo(button){
    if(button.disabled)return;button.disabled=true;
    try{
      const record=(await read(context.job_id,button.dataset.source,button.dataset.linkedVideo)).recording;
      const key=button.dataset.camera,view={head:'head',left:'left_arm',right:'right_arm'}[key];
      const value=Array.isArray(record.videos)?record.videos.find(v=>[key,view].includes(v.camera)):record.videos?.[key]||record.videos?.[view];
      const explicit=Object.hasOwn(record,'videos')||['head','left_arm','right_arm'].some(k=>Object.hasOwn(record,k+'_video_url')||Object.hasOwn(record,k+'_compressed_video_url'));
      const src=safe(typeof value==='string'?value:value?.url||value?.src||record[view+'_compressed_video_url']||record[view+'_video_url']||(!explicit&&/^DEMO-R-\d+$/.test(record.id)?'/static/post_training_collection/media/'+key+'.webm':''));
      if(!src)throw Error('暂无视频');
      const video=document.createElement('video');video.className='dpr-linked-video-player';video.src=src;video.controls=true;video.playsInline=true;video.setAttribute('aria-label',button.getAttribute('aria-label'));button.replaceWith(video);await video.play().catch(()=>{});
      video.addEventListener('error',()=>{video.replaceWith(button);button.disabled=false;button.title='视频加载失败，点击重试';});
    }catch(error){button.disabled=false;button.title=error.message;button.setAttribute('aria-label',error.message);}
  }
  window.addEventListener('pagehide',close);
})();
