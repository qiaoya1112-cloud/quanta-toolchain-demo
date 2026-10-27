/* Read-only capture of the running local demo using an empty Chrome profile. No production access. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const root = path.resolve(__dirname,'..');
const python = process.env.DEMO_PYTHON || path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const port = Number(process.env.TEST_PORT || 5041);
const debugPort = Number(process.env.DEBUG_PORT || 9364);
const origin = `http://127.0.0.1:${port}`;
const base = '/data/post-training-collection';
const api = '/api/post-training-collection/tasks';
const output = path.resolve(process.env.EVIDENCE_DIR || path.join(root,'instance/detail-layout-refresh'));
const delay = ms => new Promise(r=>setTimeout(r,ms));
const assertions=[];
const check=(value,message)=>{assert.ok(value,message);assertions.push(message);};

async function main(){
  fs.mkdirSync(output,{recursive:true});
  const sandbox=fs.mkdtempSync(path.join(output,'chrome-'));
  const service={kill(){}};let serviceLog='';
  let chrome,socket;
  try{
    for(let i=0;i<120;i++){try{if((await fetch(origin+api)).ok)break;}catch(_){}await delay(100);}
    const health=await fetch(origin+api);if(!health.ok)throw new Error(`隔离服务响应 ${health.status}: ${serviceLog.slice(-5000)}`);
    check(health.ok,'隔离本地服务可用');
    chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',[
      '--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-extensions',
      '--window-size=1440,1000',`--user-data-dir=${path.join(sandbox,'chrome')}`,`--remote-debugging-port=${debugPort}`,'about:blank'
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
    await call('Runtime.enable');await call('Page.enable');await call('Network.enable');await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*']});await nav(base);



    await resize(1440,1000);
    await call('Page.navigate',{url:origin+'/data/processing-tasks'});await wait("typeof dprOpenProcessingTaskDrawer==='function'",'处理任务');
    const detailSelector='#dpr-processing-task-table .dpr-task-actions button';
    console.log('processing-actions',await evaluate("[...document.querySelectorAll('#dpr-processing-task-table .dpr-task-actions button')].slice(0,6).map(el=>({text:el.textContent,onclick:el.getAttribute('onclick')}))"));
    await evaluate("[...document.querySelectorAll('#dpr-processing-task-table .dpr-task-actions button')].find(el=>el.getAttribute('onclick')?.includes(\"'detail'\"))?.click()");
    await wait("document.querySelector('#drawerProcessingTaskForm')?.getAttribute('aria-hidden')==='false'",'处理任务详情');await shot('ref-processing-detail');
    console.log('processing-layout',await evaluate("[...document.querySelectorAll('.dpr-processing-task-page-head,.dpr-processing-task-page-head h2,.dpr-processing-task-form,.dpr-processing-basic-grid')].map(el=>({selector:el.className,font:getComputedStyle(el).fontSize,padding:getComputedStyle(el).padding,background:getComputedStyle(el).backgroundColor}))"));
    await call('Page.navigate',{url:origin+'/data/tasks/20454'});await wait("document.querySelector('.dpr-record-top')",'处理任务数据页');await shot('ref-processing-records');

    await call('Emulation.setFocusEmulationEnabled',{enabled:true});
    await nav(base+'/02604');
    check(await evaluate("getComputedStyle(document.querySelector('.dc-detail-header')).backgroundColor==='rgb(255, 255, 255)'"),'详情采用白色二级页顶栏');
    check(await evaluate("parseFloat(getComputedStyle(document.querySelector('.dc-detail-header h1')).fontSize)===18"),'标题复用处理任务二级页18px层级');
    check(await evaluate("document.querySelector('.dc-stat-grid').offsetHeight<45&&!document.querySelector('.dc-stat.dc-panel')"),'大统计卡改为紧凑摘要');
    check(await evaluate("(()=>{const notice=document.querySelector('.dc-inline-note');const noticeSpace=notice?notice.getBoundingClientRect().height+parseFloat(getComputedStyle(notice).marginTop):0;return document.querySelector('.dc-detail-shell').getBoundingClientRect().top-noticeSpace<270})()"),'主工作区保持紧凑，允许已有收尾提醒占用一行');
    check(await evaluate("getComputedStyle(document.body).overflow==='hidden'"),'外层页面不出现第二个滚动区域');
    await shot('after-detail-1440');
    const oldHeader=await evaluate("window.layoutHeader=document.querySelector('.dc-detail-header');true");
    await click('[data-action=detail-tab][data-value=config]');
    check(await evaluate("window.layoutHeader===document.querySelector('.dc-detail-header')"),'切Tab只更新内容，不重建标题和操作');
    check(await evaluate("location.hash==='#config'&&document.querySelector('#dc-detail-body').getAttribute('aria-labelledby')==='dc-detail-tab-config'"),'Tab定位与可访问标签同步');
    await evaluate("document.querySelector('#dc-detail-body').scrollTop=280");
    const configScroll=await evaluate("document.querySelector('#dc-detail-body').scrollTop");
    check(configScroll>0,'完整配置支持独立滚动');
    await click('[data-action=detail-tab][data-value=activity]');await shot('after-activity-1440');
    await click('[data-action=detail-tab][data-value=config]');
    check(await evaluate(`Math.abs(document.querySelector('#dc-detail-body').scrollTop-${configScroll})<2`),'切回配置保留阅读位置');
    await evaluate("document.querySelector('#dc-detail-body').scrollTop=0");await shot('after-config-1440');
    await call('Page.reload',{ignoreCache:true});await wait("document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'");
    check(await evaluate("document.querySelector('[data-value=config]').getAttribute('aria-selected')==='true'"),'刷新页面保留当前配置Tab');
    await click('[data-action=detail-tab][data-value=records]');
    await fill('#dc-record-device','MOZ1-001');await fill('#dc-record-operator','joanna');
    check(await evaluate("!document.querySelector('.dc-record-reset').disabled"),'有筛选时允许一键重置');
    await click('[data-action=reset-record-filters]');
    check(await evaluate("[...document.querySelectorAll('input[data-record-filter]')].every(el=>el.value==='')&&document.querySelector('[data-record-filter=upload]').value==='uploaded'&&document.querySelector('[data-record-filter=conclusion]').value===''&&document.activeElement.id==='dc-record-id'&&document.querySelector('.dc-record-reset').disabled"),'重置清空搜索和采集结论、恢复已上传并聚焦ID搜索');
    await evaluate("document.querySelector('[data-value=records]').focus()");
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowRight',code:'ArrowRight'});await call('Input.dispatchKeyEvent',{type:'keyUp',key:'ArrowRight',code:'ArrowRight'});
    check(await evaluate("document.activeElement.dataset.value==='processing'&&document.activeElement.getAttribute('aria-selected')==='true'"),'键盘方向键切换到相邻关联处理Tab并保留焦点');
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'End',code:'End'});await call('Input.dispatchKeyEvent',{type:'keyUp',key:'End',code:'End'});
    check(await evaluate("document.activeElement.dataset.value==='activity'"),'End跳到最后一个Tab');
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Home',code:'Home'});await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Home',code:'Home'});
    check(await evaluate("document.activeElement.dataset.value==='records'"),'Home回到采集数据');
    await nav(base+'/02602');
    await evaluate("document.querySelector('#dc-record-results .dc-table-wrap').scrollTop=120");
    const recordsScroll=await evaluate("document.querySelector('#dc-record-results .dc-table-wrap').scrollTop");
    await click('[data-action=detail-tab][data-value=config]');await click('[data-action=detail-tab][data-value=records]');
    check(await evaluate(`Math.abs(document.querySelector('#dc-record-results .dc-table-wrap').scrollTop-${recordsScroll})<2`),'切回数据保留表格阅读位置');
    await click('[data-action=record-next]');
    check((await text('.dc-page-buttons')).includes('2 /'),'分页工作正常');
    await click('[data-action=detail-tab][data-value=config]');await click('[data-action=detail-tab][data-value=records]');
    check((await text('.dc-page-buttons')).includes('2 /'),'切Tab保留数据页码');
    await click('[data-action=record-detail]');await shot('after-record-dialog');await click('[data-action=close-dialog]');
    await click('[data-action=share-task]');await wait("document.querySelector('.dc-share-text')");check(await evaluate("document.querySelector('.dc-share-text').textContent.includes('任务 ID：02602')"),'任务卡正常打开并展示当前任务ID');await click('[data-action=close-dialog]');
    await click('[data-action=change-state]');await wait("document.querySelector('.dc-confirm-metrics')");check(await count('[data-action=confirm-state]')===1,'结束采集仍经过明确确认');await click('[data-action=close-dialog]');
    await nav(base+'/02601#config');check(await count('[data-config-field=prompts],[data-config-field=checkpoint]')===0,'NORMAL配置没有模型字段');
    await nav(base+'/02607#config');check(await count('[data-config-field=location]')===1,'UDAS配置展示地点');await shot('after-udas-config');
    await nav(base+'/02605');check((await text('#dc-record-results')).includes('等待采集数据'),'无采集数据空态正常');await shot('after-empty');
    await nav(base+'/02603');check(await count('.dc-inline-note')===1,'开放且超过48小时无录制的任务显示收尾提醒');await shot('after-review-notice');
    await nav(base+'/02606');check(await count('.dc-inline-note')===0,'已结束任务不显示收尾提醒');
    await nav(base+'/02604');
    for(const [width,height] of [[1920,1080],[1440,1000],[1280,800],[1024,768],[768,900],[390,844],[320,720],[667,375]]){
      await resize(width,height);await noOverflow(width+'x'+height+'详情无横向溢出');
      check(await evaluate("document.querySelector('.dc-head-actions').getBoundingClientRect().right<=innerWidth+1"),width+'标题操作不越界');
      if(height>650){
        check(await evaluate("document.querySelector('.dc-footer').getBoundingClientRect().bottom<=innerHeight+1"),width+'分页固定可见');
        const toolbarTop=await evaluate("document.querySelector('.dc-record-filters').getBoundingClientRect().top");
        await evaluate("document.querySelector('#dc-record-results .dc-table-wrap').scrollTop=500");
        check(await evaluate(`Math.abs(document.querySelector('.dc-record-filters').getBoundingClientRect().top-${toolbarTop})<1`),width+'滚动数据保留搜索区域');
      }
      await evaluate("document.querySelector('#dc-record-results .dc-table-wrap').scrollTop=0");await shot('after-records-'+width+'x'+height);
      await click('[data-action=detail-tab][data-value=config]');await noOverflow(width+'x'+height+'完整配置无横向溢出');await shot('after-config-'+width+'x'+height);
      await click('[data-action=detail-tab][data-value=records]');
    }
    await resize(1440,1000);await nav(base+'?source=robot');
    check(await evaluate("document.querySelector('.dc-task-table')&&getComputedStyle(document.body).overflow!=='hidden'&&!document.querySelector('.dc-detail-header')"),'任务列表样式和滚动不受详情影响');
    await nav(base+'/new?source=robot');check(await count('#dc-create-form')===1,'创建页正常保留');
    check(await evaluate("getComputedStyle(document.querySelector('#dc-app')).zIndex==='260'"),'创建页原有页面层级不受影响');
    const collectionExceptions=exceptions.filter(error=>!error.includes('CodeMirror is not defined'));
    check(collectionExceptions.length===0,'采集详情无未捕获异常：'+collectionExceptions.join('; '));
    fs.writeFileSync(path.join(output,'layout-report.json'),JSON.stringify({passed:assertions.length,assertions,exceptions},null,2));
    console.log(JSON.stringify({passed:assertions.length,output},null,2));
  } finally {if(socket)socket.close();if(chrome)chrome.kill();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
