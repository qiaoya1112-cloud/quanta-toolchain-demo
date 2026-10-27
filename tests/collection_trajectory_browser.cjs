/* Read-only capture of the running local demo using an empty Chrome profile. No production access. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const root = path.resolve(__dirname,'..');
const python = process.env.DEMO_PYTHON || path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const port = Number(process.env.TEST_PORT || 5041);
const debugPort = Number(process.env.DEBUG_PORT || 9372);
const origin = `http://127.0.0.1:${port}`;
const base = '/data/post-training-collection';
const api = '/api/post-training-collection/tasks';
const output = path.resolve(process.env.EVIDENCE_DIR || path.join(root,'instance/collection-trajectory'));
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
    await call('Runtime.enable');await call('Page.enable');await call('Network.enable');await call('Emulation.setFocusEmulationEnabled',{enabled:true});await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*']});await nav(base);



    await nav(base+'/02602');
    check((await text('.dc-record-table thead')).includes('采集结论'),'列表显示独立采集结论列');
    check(await count('.dc-record-filters select[data-record-filter=conclusion]')===1&&await count('.dc-record-table th select[data-record-filter=conclusion]')===0,'采集结论筛选在工具栏直接可见且无重复入口');
    check(await evaluate("[...document.querySelector('[data-record-filter=conclusion]').options].map(o=>o.text).join('|')==='全部采集结论|成功|失败'"),'结论下拉仅提供全部成功失败');
    check(await count('[data-action=record-trajectory]')===8,'每条录制都有轨迹入口');
    const data=await taskData('02602');
    check(data.records[0].quality==='pending'&&data.records[0].collection_result==='success','采集结果独立于待质检状态');
    check((await text('.dc-record-table tbody tr:first-child [data-label=采集结论]')).includes('成功'),'待质检也可展示采集成功');
    check((await text('.dc-record-table tbody tr:nth-child(3) [data-label=采集结论]')).includes('失败'),'质检通过不覆盖采集失败');
    for(const [value,label] of [['success','成功'],['failure','失败']]){
      await fill('[data-record-filter=conclusion]',value);
      check(await evaluate(`[...document.querySelectorAll('[data-label=采集结论]')].every(el=>el.innerText.trim()===${JSON.stringify(label)})`),'采集结论筛选 '+label);
      check(await evaluate(`document.querySelector('[data-record-filter=conclusion]').value===${JSON.stringify(value)}&&document.activeElement.dataset.recordFilter==='conclusion'`),'已选结论保持并保留焦点 '+label);
    }
    await fill('#dc-record-id','does-not-exist');
    check(await count('.dc-record-empty-row')===1&&await count('.dc-record-filters [data-record-filter=conclusion]')===1,'零结果保留结论筛选入口');
    await fill('[data-record-filter=conclusion]','');
    check(await evaluate("document.querySelector('[data-record-filter=conclusion]').value===''"),'空结果时仍可切回全部');
    await click('[data-action=reset-record-filters]');
    await fill('#dc-record-operator',await text('.dc-record-table tbody tr:first-child [data-label=采集员]'));
    const before=await text('#dc-record-results');
    await click('[data-action=record-trajectory]');
    await wait("document.querySelector('#dc-dialog').open&&document.querySelectorAll('.dc-trajectory-chart canvas').length>=2",'轨迹图表加载');
    check(await count('.dc-trajectory-frame video')===3,'轨迹弹窗展示三路视频');
    check(await count('[data-trajectory-video]')===3,'每路视频提供独立播放按钮');
    check((await text('.dc-trajectory-meta')).includes(data.records[0].id),'弹窗对应所点记录');
    check(await count('[data-trajectory-action=part]')===5,'左臂躯干右臂Base及总览五种视图');
    check(await count('.dc-trajectory-demo')===1,'演示轨迹有示例标识');
    await wait("[...document.querySelectorAll('.dc-trajectory-frame video')].every(v=>v.readyState>=2)",'轨迹视频加载');
    await click('[data-trajectory-video="0"]');
    await wait("document.querySelector('.dc-trajectory-frame video').currentTime>.2",'单路视频播放');
    check(await evaluate("document.querySelectorAll('.dc-trajectory-frame video')[0].paused===false&&[...document.querySelectorAll('.dc-trajectory-frame video')].slice(1).every(v=>v.paused)"),'单路播放不联动其他视频');
    check(await evaluate("document.querySelector('[data-trajectory-seek]').value==='0'"),'单路播放不推进下方轨迹进度');
    await click('[data-trajectory-video="0"]');
    check(await evaluate("document.querySelector('.dc-trajectory-frame video').paused"),'单路视频可独立暂停');
    check(await count('[data-trajectory-fullscreen]')===3,'每路视频提供全屏入口');
    const fullBox=await evaluate("(()=>{const r=document.querySelector('[data-trajectory-fullscreen]').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()");
    await call('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...fullBox});
    await call('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...fullBox});
    await wait("document.fullscreenElement?.classList.contains('dc-trajectory-frame')",'单路视频全屏');
    check(await evaluate("document.fullscreenElement.querySelectorAll('video').length===1"),'全屏仅显示当前视频');
    await shot('06-single-video-fullscreen');
    await click('[data-trajectory-fullscreen]');await wait('!document.fullscreenElement','退出单视频全屏');
    check(await count('.dc-trajectory-frames video')===3,'退出全屏恢复三视角布局');
    await shot('02-trajectory-left-desktop');
    await click('[data-trajectory-action=part][data-part=base]');
    check(await evaluate("document.querySelector('[data-part=base]').getAttribute('aria-selected')==='true'"),'切换Base视图');
    check(await evaluate("echarts.getInstanceByDom(document.querySelector('[data-trajectory-chart=speed]')).getOption().series.filter(s=>s.name?.includes('Angular')).length===2"),'Base对比State和Cmd角速度');
    await shot('03-trajectory-base-desktop');
    await click('[data-trajectory-action=play]');
    await wait("document.querySelector('.dc-trajectory-frame video').currentTime>.2",'视频轨迹共同推进');
    check((await text('[data-trajectory-action=play]'))==='暂停','播放时显示暂停');
    await click('[data-trajectory-action=play]');
    check(await evaluate("[...document.querySelectorAll('.dc-trajectory-frame video')].every(v=>v.paused)"),'暂停三路视频');
    await fill('[data-trajectory-seek]','2');
    await wait("Math.abs(document.querySelector('.dc-trajectory-frame video').currentTime-2)<.2",'进度定位同步视频');
    check(await evaluate("echarts.getInstanceByDom(document.querySelector('[data-trajectory-chart=speed]')).getOption().series.find(s=>s.id==='cursor').markLine.data[0].xAxis===2"),'进度定位同步图表游标');
    await click('[data-trajectory-action=play]');await delay(180);
    await click('[data-trajectory-video="1"]');
    if(await evaluate("document.querySelectorAll('.dc-trajectory-frame video')[1].paused"))await click('[data-trajectory-video="1"]');
    await wait("!document.querySelectorAll('.dc-trajectory-frame video')[1].paused",'整体播放切换左臂独立播放');
    await evaluate("window.frozenTrajectory=Number(document.querySelector('[data-trajectory-seek]').value);true");await delay(220);
    check(await evaluate("Number(document.querySelector('[data-trajectory-seek]').value)===frozenTrajectory&&document.querySelectorAll('.dc-trajectory-frame video')[0].paused"),'单路接管暂停同步播放并冻结轨迹');
    await evaluate("document.querySelectorAll('.dc-trajectory-frame video')[1].currentTime=4");await delay(100);
    check(await evaluate("Number(document.querySelector('[data-trajectory-seek]').value)===frozenTrajectory"),'单路拖动进度不改变轨迹');
    await click('[data-trajectory-action=play]');await delay(180);
    check(await evaluate("Math.abs(document.querySelectorAll('.dc-trajectory-frame video')[1].currentTime-document.querySelectorAll('.dc-trajectory-frame video')[0].currentTime)<.3"),'恢复整体播放从轨迹时间重新对齐视频');
    await click('[data-trajectory-action=play]');
    await fill('[data-trajectory-rate]','2');
    check(await evaluate("[...document.querySelectorAll('.dc-trajectory-frame video')].every(v=>v.playbackRate===2)"),'三路视频统一倍速');
    await click('[data-trajectory-action=part][data-part=all]');
    check(await evaluate("echarts.getInstanceByDom(document.querySelector('[data-trajectory-chart=xy]')).getOption().series.filter(s=>s.type==='line').length===8"),'总览汇总四部件的State和Cmd轨迹');
    await click('[data-trajectory-action=replay]');
    await wait("document.querySelector('.dc-trajectory-frame video').currentTime>.05",'重播重新推进');
    await evaluate("window.trajectoryVideos=[...document.querySelectorAll('.dc-trajectory-frame video')];window.chartNode=document.querySelector('[data-trajectory-chart=xy]');true");
    await click('[data-action=close-dialog]');
    check(await evaluate("trajectoryVideos.every(v=>v.paused&&!v.getAttribute('src'))&&!echarts.getInstanceByDom(chartNode)"),'关闭释放媒体和图表');
    check((await text('#dc-record-results'))===before,'关闭保留列表和筛选');
    check(await evaluate("document.activeElement.dataset.action==='record-trajectory'"),'关闭后焦点返回对应轨迹按钮');
    await click('[data-action=reset-record-filters]');
    await shot('01-records-desktop');
    for(const width of [1366,1920,390,320]){
      await resize(width,width<760?844:1000);await noOverflow(width+'列表无页面横向溢出');
      if(width>=1366)check(await evaluate("document.querySelector('[data-action=record-trajectory]').getBoundingClientRect().right<innerWidth"),width+'轨迹入口在可见区');
      await click('[data-action=record-trajectory]');
      await wait("document.querySelectorAll('.dc-trajectory-chart canvas').length>=2",'响应式图表');
      await noOverflow(width+'轨迹弹窗无页面溢出');
      check(await evaluate("document.querySelector('#dc-dialog').scrollWidth<=document.querySelector('#dc-dialog').clientWidth+2"),width+'弹窗内部无横向溢出');
      await shot('04-trajectory-'+width);
      await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27,nativeVirtualKeyCode:27});
      await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27,nativeVirtualKeyCode:27});
      await wait("!document.querySelector('#dc-dialog').open",'Escape关闭弹窗');
    }
    await resize(1440,1000);
    const fixture=await call('Page.addScriptToEvaluateOnNewDocument',{source:`(()=>{const original=window.fetch;window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0]).endsWith('/tasks/02602')&&response.ok){const data=await response.clone().json();data.task.records[0]={...data.task.records[0],id:'REAL-RECORD-01',collection_result:null,quality:'passed',videos:{}};delete data.task.records[0].trajectory;data.task.records[1].collection_result=null;data.task.records[1].is_mistake=true;data.task.records[1].trajectory=null;return new Response(JSON.stringify(data),{status:response.status,headers:response.headers});}return response;};})();`});
    await nav(base+'/02602');
    check((await text('.dc-record-table tbody tr:first-child [data-label=采集结论]')).trim()==='-','缺少采集结果仅显示短横线，不添加第三种结论或使用质检结果');
    check((await text('.dc-record-table tbody tr:nth-child(2) [data-label=采集结论]')).includes('失败'),'兼容旧平台is_mistake布尔字段');
    await click('[data-action=record-trajectory]');
    check((await text('.dc-trajectory-empty')).includes('暂无轨迹数据'),'真实轨迹缺失显示空态');
    check(await count('.dc-trajectory-chart,.dc-trajectory-demo')===0,'缺失真实轨迹不伪造曲线');
    await shot('05-no-trajectory');await click('[data-action=close-dialog]');
    await call('Page.removeScriptToEvaluateOnNewDocument',{identifier:fixture.identifier});
    const onlyVideo=await call('Page.addScriptToEvaluateOnNewDocument',{source:`(()=>{const original=window.fetch;window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0]).endsWith('/tasks/02602')&&response.ok){const data=await response.clone().json();data.task.records[0]={...data.task.records[0],id:'REAL-VIDEO-ONLY',videos:{head:'/static/post_training_collection/media/head.webm'},trajectory:null};return new Response(JSON.stringify(data),{status:response.status,headers:response.headers});}return response;};})();`});
    await nav(base+'/02602');await click('[data-action=record-trajectory]');
    await wait("document.querySelector('.dc-trajectory-frame video')?.readyState>=2",'无轨迹但有单路视频');
    await click('[data-trajectory-video]');await wait("document.querySelector('.dc-trajectory-frame video').currentTime>.1",'无轨迹时仍可独立播放视频');
    check(await count('[data-trajectory-fullscreen]')===1&&await count('.dc-trajectory-chart')===0,'缺少轨迹和部分视角不影响已有视频控制');
    await click('[data-action=close-dialog]');await call('Page.removeScriptToEvaluateOnNewDocument',{identifier:onlyVideo.identifier});
    // A real trajectory without videos still supports replay and missing component states.
    const actual=await call('Page.addScriptToEvaluateOnNewDocument',{source:`(()=>{const original=window.fetch;window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0]).endsWith('/tasks/02602')&&response.ok){const data=await response.clone().json();data.task.records[0]={...data.task.records[0],id:'REAL-RECORD-02',videos:{},trajectory:{tracks:{base:{state:[{t:0,x:0,y:0,angle:0},{t:1,x:.1,y:.2,angle:.1},{t:3,x:.3,y:.2,angle:.2}],cmd:[]}}}};return new Response(JSON.stringify(data),{status:response.status,headers:response.headers});}return response;};})();`});
    await nav(base+'/02602');await click('[data-action=record-trajectory]');
    await wait("document.querySelectorAll('.dc-trajectory-chart canvas').length>=2",'真实轨迹可展示');
    check(await count('.dc-trajectory-demo')===0&&await count('[data-trajectory-action=part]:disabled')===3,'真实轨迹无演示标记且禁用缺失部件');
    await click('[data-trajectory-action=play]');await delay(400);
    check(await evaluate("Number(document.querySelector('[data-trajectory-seek]').value)>.1"),'没有视频也可播放已有轨迹');
    await click('[data-action=close-dialog]');await call('Page.removeScriptToEvaluateOnNewDocument',{identifier:actual.identifier});
    const collectionExceptions=exceptions.filter(error=>!error.includes('CodeMirror is not defined'));
    check(collectionExceptions.length===0,'无采集模块未捕获异常：'+collectionExceptions.join('; '));
    fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify({passed:assertions.length,assertions,exceptions},null,2));
    console.log(JSON.stringify({passed:assertions.length,output},null,2));
  } finally {if(socket)socket.close();if(chrome)chrome.kill();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
