/* Collection record playback in the shared workbench, with an isolated database. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{spawn,spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),python=path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const out=path.resolve(process.env.EVIDENCE_DIR||path.join(root,'instance/collection-processing-navigation'));
const testPort=Number(process.env.RECORD_TEST_PORT||5122),debugPort=Number(process.env.RECORD_DEBUG_PORT||9522),origin='http://127.0.0.1:'+testPort;
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


  const base='/data/post-training-collection/02602#processing';
  await call('Page.navigate',{url:origin+base});
  await wait("document.querySelector('.dc-processing-task-name')&&document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'");
  const name=await ev("document.querySelector('.dc-processing-task-name').textContent");
  const jobId=await ev("new URL(document.querySelector('.dc-processing-task-name').href).searchParams.get('linked')");
  await check("[...document.querySelectorAll('.dc-processing-task-name')].every(a=>a.pathname==='/data/processing-tasks'&&new URL(a.href).searchParams.get('linked')===a.nextElementSibling.textContent)",'每行名称进入对应配置详情');
  await check("[...document.querySelectorAll('.dc-processing-row-actions a')].every(a=>a.pathname.startsWith('/data/tasks/')&&new URL(a.href).searchParams.get('collection')==='02602')",'查看数据保留来源过滤');
  await click('.dc-processing-task-name');
  await wait("location.pathname==='/data/processing-tasks'&&document.querySelector('#drawerProcessingTaskForm')?.getAttribute('aria-hidden')==='false'");
  await wait("document.querySelector('#processingTaskName')?.value==="+JSON.stringify(name));
  await check("document.querySelector('#processingTaskDrawerTitle').textContent==="+JSON.stringify(name)+"&&document.querySelector('#processingTaskHeaderId').textContent.includes("+JSON.stringify(jobId)+")",'详情顶部显示处理任务名称和 ID');
  await check("document.querySelector('#drawerProcessingTaskForm').dataset.taskId==="+JSON.stringify(jobId),'打开点击的任务');
  await check("document.querySelector('#processingTaskName').disabled",'配置以只读方式展示');
  await check("['basic','filter','flow'].every(p=>document.querySelector('#drawerProcessingTaskForm [data-task-pane='+p+']'))",'保留完整原页面区域');
  await check("(()=>{const buttons=[...document.querySelectorAll('.dpr-processing-task-menu button')],r=buttons.map(b=>b.getBoundingClientRect());return r.every(x=>Math.abs(x.top-r[0].top)<1)&&r[0].right<r[1].left&&r[1].right<r[2].left})()",'详情三个栏目横向排列');
  await click('[data-task-pane=filter]');await check("document.querySelector('[data-task-pane-content=filter]').classList.contains('active')",'筛选条件 Tab 可切换');
  await click('[data-task-pane=flow]');await check("document.querySelector('[data-task-pane-content=flow]').classList.contains('active')",'业务环节 Tab 可切换');
  await click('[data-task-pane=basic]');
  await shot('config-from-collection');
  await click('.dpr-processing-back');
  await wait("location.pathname==='/data/post-training-collection/02602'&&location.hash==='#processing'&&document.querySelector('.dc-processing-task-name')");
  checks.push('配置返回原采集任务关联处理Tab');
  await click('.dc-processing-row-actions a');
  await wait("location.pathname.startsWith('/data/tasks/')&&document.querySelector('.dpr-record-page')");
  await check("new URLSearchParams(location.search).get('collection')==='02602'",'查看数据仍进入原处理数据页面并限定采集来源');
  await call('Page.navigate',{url:origin+'/data/processing-tasks?new=1'});
  await wait("document.querySelector('#drawerProcessingTaskForm')?.dataset.mode==='new'&&document.querySelector('#drawerProcessingTaskForm')?.getAttribute('aria-hidden')==='false'");
  await check("getComputedStyle(document.querySelector('.dpr-processing-task-page-body')).display==='grid'&&document.querySelector('#processingTaskHeaderId').hidden&&document.querySelector('#processingTaskHeaderStatus').hidden",'新建任务保留原侧边导航');
  const unexpectedErrors=errors.filter(error=>!String(error).includes('ViewTransition opt-in disabled'));
  assert.deepEqual(unexpectedErrors,[]);checks.push('无未捕获脚本异常');
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({passed:checks.length,checks},null,2));
  console.log(JSON.stringify({passed:checks.length,checks},null,2));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(()=>{socket?.close();chrome?.kill();service?.kill();});
