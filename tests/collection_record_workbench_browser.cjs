/* Collection record playback in the shared workbench, with an isolated database. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{spawn,spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),python=path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const out=path.resolve(process.env.EVIDENCE_DIR||path.join(root,'instance/collection-workbench-regression'));
const testPort=Number(process.env.RECORD_TEST_PORT||5121),debugPort=Number(process.env.RECORD_DEBUG_PORT||9521),origin='http://127.0.0.1:'+testPort;
const delay=ms=>new Promise(r=>setTimeout(r,ms)),checks=[];let service,chrome,socket;
const http=require('node:http');
const request=(url,method='GET',body)=>new Promise((resolve,reject)=>{const data=body===undefined?undefined:JSON.stringify(body);const req=http.request(url,{method,agent:false,headers:{'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID(),...(data?{'Content-Length':Buffer.byteLength(data)}:{})}},r=>{let text='';r.setEncoding('utf8');r.on('data',c=>text+=c);r.on('end',()=>{try{resolve({status:r.statusCode,ok:r.statusCode<400,body:JSON.parse(text)})}catch(e){reject(e)}});});req.on('error',reject);req.end(data);});
async function main(){
  fs.mkdirSync(out,{recursive:true});const sandbox=fs.mkdtempSync(path.join(out,'isolated-'));
  service=spawn(python,['-c',`from toolchain_demo import app; app.run(host='127.0.0.1',port=${testPort},debug=False,use_reloader=False)`],{cwd:root,env:{...process.env,COLLECTION_DEMO_DB:path.join(sandbox,'collection.sqlite3'),PYTHONIOENCODING:'utf-8'},stdio:'ignore',windowsHide:true});
  for(let i=0;i<100;i++){try{if((await request(origin+'/api/post-training-collection/tasks')).ok)break;}catch{}await delay(100);}
  chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless','--disable-gpu','--no-first-run','--disable-extensions','--no-default-browser-check','--user-data-dir='+path.join(sandbox,'chrome'),'--remote-debugging-port='+debugPort,'about:blank'],{stdio:'ignore',windowsHide:true});
  let page;for(let i=0;i<100;i++){try{page=(await request('http://127.0.0.1:'+debugPort+'/json/list')).body.find(p=>p.type==='page');if(page)break;}catch{}await delay(100);}assert.ok(page);
  socket=new WebSocket(page.webSocketDebuggerUrl);let id=0;const pending=new Map(),errors=[];
  socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);};
  await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
  const call=(method,params={})=>new Promise((resolve,reject)=>{const key=++id,timer=setTimeout(()=>reject(Error(method)),20000);pending.set(key,{resolve,reject,timer});socket.send(JSON.stringify({id:key,method,params}));});
  const ev=async expression=>{const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;};
  const wait=async expression=>{for(let i=0;i<100;i++){if(await ev(expression))return;await delay(100);}throw Error('Timeout '+expression);};
  const click=selector=>ev(`document.querySelector(${JSON.stringify(selector)}).click()`);
  const fill=(selector,value)=>ev(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  const check=async(expression,label)=>{assert.ok(await ev(expression),label);checks.push(label);};
  const previewContent="(document.querySelector('.dpr-rule-preview-body').textContent+' '+[...document.querySelectorAll('.dpr-rule-preview-body input,.dpr-rule-preview-body textarea')].map(e=>e.value).join(' '))";
  const shot=async name=>{await delay(150);const r=await call('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(r.data,'base64'));};
  const api=async(url,method='GET',body)=>{const r=await request(origin+url,method,body);assert.ok(r.ok,JSON.stringify(r.body));return r.body;};
  const nav=async query=>{await call('Page.navigate',{url:origin+'/data/processing-tasks'+query});await wait("!!document.querySelector('#processingRulePreview')&&document.querySelectorAll('[data-collection-processing]').length>0");};
  await call('Page.enable');await call('Runtime.enable');await call('Network.enable');await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*']});await call('Emulation.setDeviceMetricsOverride',{width:1440,height:960,deviceScaleFactor:1,mobile:false});

  const base='/data/post-training-collection/02602#records';
  await call('Page.navigate',{url:origin+base});
  await wait("document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'&&document.querySelector('[data-action=record-workbench]')");
  await check("[...document.querySelectorAll('[data-label=操作]')].every(e=>e.textContent.trim()==='详情')",'操作列统一详情');
  const rid=await ev("document.querySelector('[data-action=record-workbench]').dataset.id");
  await fill('#dc-record-operator','joanna');
  await click('[data-action=record-workbench]');
  await wait("location.pathname==='/data/workbench-v2/edit'&&document.querySelectorAll('body.collection-pure-video video').length===3");
  await check(`new URLSearchParams(location.search).get('recording_id')===${JSON.stringify(rid)}`,'工作台打开对应录制');
  await check("new URLSearchParams(location.search).get('collection_task_id')==='02602'",'保留归属采集任务');
  await check("document.querySelector('workbench-task-header').getAttribute('data-return-url')==='/data/post-training-collection/02602#records'",'明确返回采集数据');
  await wait("[...document.querySelectorAll('video')].every(v=>v.readyState>=2)");
  await check("document.querySelectorAll('video[controls]').length===3&&document.querySelectorAll('.collection-video-fullscreen').length===3",'三路视频支持独立播放和全屏');
  await check("!document.querySelector('workbench-segment-list,workbench-segment-editor,.timeline-card')",'不渲染质检列表及编辑时间轴');
  await check("!document.querySelector('script[src$=\"/workbench.js\"]')&&!document.querySelector('.wbx-submit')",'不启用处理快捷键和提交逻辑');
  await check("!document.querySelector('.workbench-task-info__left').innerText.includes('数据处理 ID')&&!document.querySelector('.workbench-task-info__left').innerText.includes('内部验收')",'顶部不展示处理信息');
  await check(`document.querySelector('.workbench-task-info__left').innerText.includes(${JSON.stringify(rid)})&&document.querySelector('.workbench-task-info__left').innerText.includes('02602')`,'顶部对应当前录制和采集任务');
  await ev("document.querySelector('video').play()");
  await wait("document.querySelector('video').currentTime>.15");
  await check("[...document.querySelectorAll('video')].slice(1).every(v=>v.paused)&&!document.querySelector('.dc-trajectory-chart')",'独立播放不联动其他视频且无轨迹');
  await ev("document.querySelector('video').pause()");
  await click('[data-video-action=play]');
  await wait("Number(document.querySelector('[data-video-seek]').value)>.3");
  await check("[...document.querySelectorAll('video')].every(v=>!v.paused)",'全部播放三路视频');
  await click('[data-video-action=play]');
  await check("document.querySelector('[data-video-status]').textContent===''",'暂停不误报播放失败');
  await fill('[data-video-rate]','1.5');
  await check("[...document.querySelectorAll('video')].every(v=>v.playbackRate===1.5)",'播放速度可调整');
  await ev("(()=>{const e=document.querySelector('[data-video-seek]');e.value='2';e.dispatchEvent(new Event('input',{bubbles:true}));})()");
  await check("[...document.querySelectorAll('video')].every(v=>Math.abs(v.currentTime-2)<.1)",'公共进度可定位三路视频');
  await click('.collection-video-fullscreen');
  await wait("!!document.fullscreenElement");
  await check("document.fullscreenElement.classList.contains('workbench-feed')",'单路视频实际进入全屏');
  await ev("document.exitFullscreen()");
  await wait("!document.fullscreenElement");
  checks.push('全屏可退出恢复三窗');
  for(const width of [1440,1920,1024]){
    await call('Emulation.setDeviceMetricsOverride',{width,height:960,deviceScaleFactor:1,mobile:false});await delay(100);
    await check("document.documentElement.scrollWidth<=innerWidth+1",width+'工作台无横向溢出');
    await check("(()=>{const a=document.querySelector('.workbench-feed--arm').getBoundingClientRect(),h=document.querySelector('.workbench-feed--three-panel').getBoundingClientRect();return a.width>200&&h.width>a.width*1.9&&h.bottom<=innerHeight-40})()",width+'三窗布局完整');
    await shot('workbench-'+width);
  }
  await click('.workbench-task-info__close');
  await wait("document.querySelector('[data-action=record-workbench]')&&document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'");
  await check("location.pathname==='/data/post-training-collection/02602'&&location.hash==='#records'",'返回正确采集数据页');
  await check("document.querySelector('#dc-record-operator').value==='joanna'",'返回保留筛选条件');
  await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*','*/static/post_training_collection/media/*.webm']});
  await call('Page.navigate',{url:origin+'/data/workbench-v2/edit?source=collection-data&collection_task_id=02602&recording_id='+rid});
  await wait("document.querySelector('[data-video-status]')?.textContent==='视频加载失败'");
  await check("document.querySelector('[data-video-action=play]').disabled",'媒体失败明确提示且不能假播放');
  await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*']});
  await call('Page.navigate',{url:origin+'/data/workbench-v2/optimized'});
  await wait("document.querySelector('workbench-segment-list')&&document.querySelector('workbench-segment-editor')");
  await check("!document.body.classList.contains('collection-pure-video')&&!!document.querySelector('.timeline-card')",'普通工作台保留编辑区域');
  // Invalid IDs never fall back to unrelated workbench fixtures.
  for(const [collection,record] of [['02601',rid],['99999',rid],['02602','missing']]){
    const result=await new Promise((resolve,reject)=>{http.get(origin+'/data/workbench-v2/edit?source=collection-data&collection_task_id='+collection+'&recording_id='+record,{agent:false},r=>{r.resume();resolve(r.statusCode)}).on('error',reject);});
    assert.equal(result,404);checks.push('无效或跨任务录制返回404 '+collection+'/'+record);
  }
  const unexpectedErrors=errors.filter(error=>!String(error).includes('ViewTransition opt-in disabled'));
  assert.deepEqual(unexpectedErrors,[]);checks.push('无浏览器脚本异常');
  console.log(JSON.stringify({passed:checks.length,checks},null,2));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(()=>{socket?.close();chrome?.kill();service?.kill();});
