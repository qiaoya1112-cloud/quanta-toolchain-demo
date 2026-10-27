/* Read-only capture of the running local demo using an empty Chrome profile. No production access. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const root = path.resolve(__dirname,'..');
const python = process.env.DEMO_PYTHON || path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const port = Number(process.env.TEST_PORT || 5046);
const debugPort = Number(process.env.DEBUG_PORT || 9378);
const origin = `http://127.0.0.1:${port}`;
const base = '/data/post-training-collection';
const api = '/api/post-training-collection/tasks';
const output = path.resolve(process.env.EVIDENCE_DIR || path.join(root,'instance/collection-logs'));
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
    const original=await taskData('02602');
    check(!Object.hasOwn(original,'config_version')&&!Object.hasOwn(original,'config_history'),'任务API不提供配置版本和快照');
    check(original.records.every(r=>!Object.hasOwn(r,'config_version')),'录制API不提供配置版本');
    check(await count('.dc-record-version')===0&&!(await text('#dc-app')).includes('配置 v'),'采集数据列表无V1/V2标记');
    await click('[data-action=record-detail]');
    check(!(await text('#dc-dialog')).includes('实际配置版本')&&!(await text('#dc-dialog')).includes('当时采集要求'),'录制详情不宣称可还原执行版本');
    check((await text('#dc-dialog')).includes('实际 Prompt'),'保留实际绑定Prompt信息');
    await click('[data-action=close-dialog]');
    await click('[data-action=detail-tab][data-value=config]');
    check(await count('[data-config-field=config_version]')===0,'任务配置不展示版本字段');
    check(await count('.dc-config-prompt .dc-tag')>0,'Prompt资源自身版本仍保留');
    await shot('01-config-no-task-version');
    await nav(base+'/02602?card=1&version=999');
    await wait("document.querySelector('.dc-share-text')");
    check(await count('[data-collection-check=version_changed]')===0,'旧带版本链接可打开任务卡，无过期门禁');
    check(!(await text('.dc-share-text')).includes('配置 v'),'任务卡正文无配置版本');
    await evaluate("window.copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>window.copied.push(text)}})");
    await click('[data-action=copy-task-card]');await wait('window.copied.length===1');
    check(await evaluate("window.copied[0]===document.querySelector('.dc-share-text').textContent"),'任务卡仍复制最新内容');
    await shot('02-share-no-version-warning');
    await click('[data-action=close-dialog]');
    const fixture=await call('Page.addScriptToEvaluateOnNewDocument',{source:`(()=>{const original=window.fetch;window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0]).endsWith('/tasks/02602')&&response.ok){const data=await response.clone().json();data.task.events.push({at:'2026-10-25T12:34:56',actor:'demo-editor',title:'更新采集任务',detail:'已更新：任务说明、采集规范、任务标签、位置泛化统计',changes:[{field:'description',label:'任务说明',before:'修改前要求',after:'修改后要求 <script>alert(1)</script>'},{field:'spec_url',label:'采集规范',before:'',after:'https://example.feishu.cn/wiki/new-spec'},{field:'tags',label:'任务标签',before:['场景采集'],after:['补采','新摆场']},{field:'generalization',label:'位置泛化统计',before:[],after:[{name:'目标区域',arm:'left',event:'close',operator:'demo-left-close@1',plane:'XY',bounds:{X:[0,.3],Y:[-.2,.2]},allow_adjust:true}]}]});return new Response(JSON.stringify(data),{status:response.status,headers:response.headers});}return response;};})();`});
    await nav(base+'/02602#activity');
    check((await text('.dc-activity-content')).includes('日志'),'日志入口保留');
    check((await text('.dc-timeline li:first-child')).includes('demo-editor')&&(await text('.dc-timeline li:first-child')).includes('2026-10-25 12:34:56'),'日志展示修改人及完整时间');
    check((await text('.dc-timeline li:first-child')).includes('已更新：任务说明、采集规范、任务标签、位置泛化统计'),'日志具体说明修改字段');
    check(await evaluate("!document.querySelector('.dc-log-changes').open"),'修改前后内容默认收起');
    await click('.dc-log-changes summary');
    check(await evaluate("document.querySelector('.dc-log-changes').open"),'可展开修改内容');
    check(await count('.dc-log-changes section')===4,'四类修改分别展示');
    check((await text('.dc-log-changes')).includes('修改前要求')&&(await text('.dc-log-changes')).includes('修改后要求 <script>alert(1)</script>')&&await count('.dc-log-changes script')===0,'保留修改前后原文并安全转义');
    check((await text('.dc-log-changes')).includes('补采、新摆场'),'标签修改可读');
    check((await text('.dc-log-changes')).includes('X 0~0.3 m')&&(await text('.dc-log-changes')).includes('允许调整'),'泛化修改以可读范围展示');
    check(await count('.dc-timeline li')===original.events.length+1,'旧日志保留且无需旧格式补造修改明细');
    await shot('03-change-log-expanded');
    for(const width of [1366,390,320]){await resize(width,width<760?844:1000);await noOverflow(width+'日志不横向溢出');await shot('04-logs-'+width);}
    await call('Page.removeScriptToEvaluateOnNewDocument',{identifier:fixture.identifier});
    await resize(1440,1000);await nav(base+'/02602?saved=unchanged');
    check((await text('#dc-toast')).includes('未发现修改')&&!(await text('#dc-toast')).includes('版本'),'无变更保存提示不包含版本概念');
    const after=await taskData('02602');check(JSON.stringify(after)===JSON.stringify(original),'浏览器验收未修改展示库');
    const collectionExceptions=exceptions.filter(error=>!error.includes('CodeMirror is not defined'));
    check(collectionExceptions.length===0,'无采集模块未捕获异常：'+collectionExceptions.join('; '));
    fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify({passed:assertions.length,assertions,exceptions},null,2));
    console.log(JSON.stringify({passed:assertions.length,output},null,2));
  } finally {if(socket)socket.close();if(chrome)chrome.kill();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
