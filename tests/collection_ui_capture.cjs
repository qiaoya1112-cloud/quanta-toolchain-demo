/* Read-only capture of the running local demo using an empty Chrome profile. No production access. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const root = path.resolve(__dirname,'..');
const python = process.env.DEMO_PYTHON || path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const port = Number(process.env.TEST_PORT || 5041);
const debugPort = Number(process.env.DEBUG_PORT || 9341);
const origin = `http://127.0.0.1:${port}`;
const base = '/data/post-training-collection';
const api = '/api/post-training-collection/tasks';
const output = path.resolve(process.env.EVIDENCE_DIR || path.join(root,'instance/collection-browser-artifacts'));
const delay = ms => new Promise(r=>setTimeout(r,ms));
const assertions=[];
const check=(value,message)=>{assert.ok(value,message);assertions.push(message);};

async function main(){
  fs.mkdirSync(output,{recursive:true});
  const sandbox=fs.mkdtempSync(path.join(os.tmpdir(),'quanta-collection-'));
  const service={kill(){}};let serviceLog='';
  let chrome,socket;
  try{
    for(let i=0;i<120;i++){try{if((await fetch(origin+api)).ok)break;}catch(_){}await delay(100);}
    const health=await fetch(origin+api);if(!health.ok)throw new Error(`隔离服务响应 ${health.status}: ${serviceLog.slice(-5000)}`);
    check(health.ok,'隔离本地服务可用');
    chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',[
      '--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-extensions',
      '--window-size=1440,1000',`--user-data-dir=${path.join(sandbox,'chrome')}`,`--remote-debugging-port=${debugPort}`,origin+base
    ],{stdio:'ignore',windowsHide:true});
    let page;
    for(let i=0;i<100;i++){try{page=(await fetch(`http://127.0.0.1:${debugPort}/json/list`).then(r=>r.json())).find(p=>p.type==='page');if(page)break;}catch(_){}await delay(100);}
    check(Boolean(page),'独立 Chrome 页面已打开');
    socket=new WebSocket(page.webSocketDebuggerUrl);let seq=0;const pending=new Map(),exceptions=[];
    socket.onmessage=event=>{
      const m=JSON.parse(event.data);
      if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result);}
      if(m.method==='Runtime.exceptionThrown')exceptions.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);
      if(m.method==='Page.javascriptDialogOpening')call('Page.handleJavaScriptDialog',{accept:true});
    };
    await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
    const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;const timer=setTimeout(()=>{pending.delete(id);reject(new Error(`CDP timeout: ${method}`));},15000);pending.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw new Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;};
    const wait=async(expression,label)=>{for(let i=0;i<100;i++){try{if(await evaluate(expression))return;}catch(_){}await delay(100);}throw new Error(`等待失败: ${label||expression}`);};
    const nav=async url=>{await call('Page.navigate',{url:origin+url});await wait("document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'",url);};
    const click=async selector=>evaluate(`(()=>{const el=document.querySelector(${JSON.stringify(selector)});if(!el)throw new Error('找不到控件 '+${JSON.stringify(selector)});el.click()})()`);
    const fill=async(selector,value)=>evaluate(`(()=>{const el=document.querySelector(${JSON.stringify(selector)});if(!el)throw new Error('找不到字段 '+${JSON.stringify(selector)});el.value=${JSON.stringify(value)};el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    const text=selector=>evaluate(`document.querySelector(${JSON.stringify(selector)})?.textContent`);
    const count=selector=>evaluate(`document.querySelectorAll(${JSON.stringify(selector)}).length`);
    const shot=async name=>{await delay(120);const r=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(path.join(output,name+'.png'),Buffer.from(r.data,'base64'));};
    const resize=async(width,height=1000)=>{await call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await delay(100);};
    const noOverflow=async label=>check(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'),label);
    const taskData=id=>fetch(origin+api+'/'+id).then(r=>r.json()).then(d=>d.task);
    const taskId=()=>evaluate("location.pathname.split('/').pop()");
    await call('Runtime.enable');await call('Page.enable');
    await wait("document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'");

    const liveCheck=await fetch(origin+api+'/02602/collection-check?config_version=1');
    check(liveCheck.ok&&(await liveCheck.json()).task.id==='02602','运行中的本地服务具备任务卡核对接口');
    await resize(1440,1000);
    await nav(base+'?source=robot');
    check(await evaluate("[...document.querySelectorAll('.dc-task-table .dc-numeric-cell')].every(el=>getComputedStyle(el).textAlign==='left')"),'已上传数据和采集时长的表头及数值统一左对齐');
    check(await evaluate("[...document.querySelectorAll('.dc-task-table th,.dc-task-table td')].every(el=>['left','start'].includes(getComputedStyle(el).textAlign))&&[...document.querySelectorAll('.dc-task-table .dc-table-actions')].every(el=>getComputedStyle(el).justifyContent==='flex-start')"),'整张任务表的表头、内容和操作按钮统一左对齐');
    check(await evaluate("[...document.querySelectorAll('.dc-task-table th')].map(el=>el.textContent).slice(6,9).join('|')==='已上传数据|采集时长（小时）|最近采集'"),'列表将小时累计时长独立放在已上传数据之后');
    const accurateHours=()=>evaluate(`(async()=>{const results=await Promise.all([...document.querySelectorAll('.dc-task-table tbody tr')].map(async row=>{const id=row.querySelector('.dc-task-id').textContent;const {task}=await fetch('${api}/'+encodeURIComponent(id)).then(r=>r.json());const seconds=task.records.filter(r=>r.upload==='uploaded').reduce((sum,r)=>sum+r.seconds,0);const cell=row.querySelector('[data-label="采集时长（小时）"]').textContent.trim();return seconds>0&&seconds<36?cell==='<0.01':Math.abs(Number(cell)*3600-seconds)<=18.01;}));return results.every(Boolean);})()`);
    check(await accurateHours(),'机器人任务时长与已上传录制累计秒数一致，排除上传中录制');
    check(await evaluate("![...document.querySelectorAll('[data-label=\"已上传数据\"]')].some(el=>el.textContent.includes('条'))"),'列表已上传数量不再显示条单位');
    check(await evaluate("document.querySelector('#dc-list-results .dc-table-wrap').scrollWidth<=document.querySelector('#dc-list-results .dc-table-wrap').clientWidth+1"),'桌面新增时长列后表格无横向滚动');
    check(await evaluate("[...document.querySelectorAll('.dc-task-id')].every(el=>/^[0-9]{5}$/.test(el.textContent))"),'列表任务ID均为5位数字');
    await shot('01-list-robot');
    await nav(base+'?source=udas');check(await accurateHours(),'UDAS任务也显示正确的小时累计时长');await shot('02-list-udas');
    await nav(base+'/new?source=robot');await shot('03-create-normal');
    await click('[data-form=mode][value=DAGGER]');await shot('04-create-dagger');
    await evaluate("document.querySelector('#dc-model-section').scrollIntoView({block:'start'})");await shot('05-dagger-config');
    await click('[data-action=pick-prompts]');await shot('06-prompt-picker');
    if(await evaluate("document.querySelector('#dc-prompt-popup')?.matches(':popover-open')"))await click('[data-action=pick-prompts]');else await click('[data-action=close-dialog]');
    await click('[data-action=pick-checkpoint]');await shot('07-checkpoint-picker');await click('[data-action=close-dialog]');
    await nav(base+'/new?source=udas');await shot('08-create-udas');
    await nav(base+'/02602');
    check(await evaluate(`(async()=>{const {task}=await fetch('${api}/02602').then(r=>r.json());return [...document.querySelectorAll('.dc-stat')].find(el=>el.querySelector('.dc-stat-name').textContent==='已上传数据').querySelector('.dc-stat-value').textContent.trim()===String(task.metrics.uploaded);})()`),'详情已上传数据只展示数量');
    await shot('09-detail');
    await click('[data-action=record-detail]');await shot('10-record-detail');await click('[data-action=close-dialog]');
    await click('[data-action=detail-tab][data-value=config]');await shot('11-detail-config');
    await click('[data-action=detail-tab][data-value=activity]');await shot('12-detail-activity');
    await click('[data-action=share-task]');await wait("document.querySelector('.dc-share-card')");check((await text('#dc-dialog-title'))==='任务卡','实际端口任务卡成功打开');check((await text('.dc-share-id'))==='02602','任务卡展示同一五位任务ID');await shot('13-task-card');await click('[data-action=close-dialog]');
    await resize(390,844);await nav(base+'?source=robot');await noOverflow('手机列表增加时长后无横向溢出');await shot('14-mobile-list');
    await nav(base+'/new?source=robot');await click('[data-form=mode][value=DAGGER]');await shot('15-mobile-create');
    await nav(base+'/02602?card=1&version=1');await wait("document.querySelector('.dc-share-card')");await shot('16-mobile-card');
    fs.writeFileSync(path.join(output,'typography.json'),JSON.stringify(await evaluate("[...document.querySelectorAll('.dc-share-card h3,.dc-share-meta dt,.dc-share-meta dd,.dc-share-label,.dc-share-card p,.dc-dialog-foot .dc-btn')].map(el=>({text:el.textContent.slice(0,50),size:getComputedStyle(el).fontSize,family:getComputedStyle(el).fontFamily,color:getComputedStyle(el).color}))"),null,2));
    const collectionExceptions=exceptions.filter(error=>!error.includes('CodeMirror is not defined'));
    check(collectionExceptions.length===0,'采集规范模块无未捕获异常：'+collectionExceptions.join('; '));
    const report={passed:assertions.length,assertions,exceptions,screenshots:fs.readdirSync(output).filter(n=>n.endsWith('.png'))};
    fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify({passed:assertions.length,output},null,2));
  } finally {
    if(socket)socket.close();if(chrome)chrome.kill();service.kill();
    // Chrome may still hold its own temporary profile briefly. Never touch a user profile.
    await delay(500);try{if(path.dirname(path.resolve(sandbox))===path.resolve(os.tmpdir())&&path.basename(sandbox).startsWith('quanta-collection-'))fs.rmSync(sandbox,{recursive:true,force:true});}catch(_){}

  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
