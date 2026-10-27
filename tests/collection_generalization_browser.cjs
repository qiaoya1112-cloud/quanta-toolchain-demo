/* Run against an isolated Flask process and an empty Chrome profile. No production access. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const root = path.resolve(__dirname,'..');
const python = process.env.DEMO_PYTHON || path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const port = Number(process.env.TEST_PORT || 5042);
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
  const databasePath=path.join(root,'instance',`collection-browser-${process.pid}.sqlite3`);
  const service=spawn(python,['-c',`from toolchain_demo import app; app.run(host='127.0.0.1',port=${port},debug=False)`],
    {cwd:root,env:{...process.env,COLLECTION_DEMO_DB:databasePath},stdio:['ignore','pipe','pipe'],windowsHide:true});
  let serviceLog='';service.stdout.on('data',chunk=>serviceLog+=chunk);service.stderr.on('data',chunk=>serviceLog+=chunk);
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
      if(m.method==='Runtime.exceptionThrown')exceptions.push(JSON.stringify({text:m.params.exceptionDetails.text,description:m.params.exceptionDetails.exception?.description,stack:m.params.exceptionDetails.exception?.details?.stackTrace?.callFrames?.slice(0,2)}));
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
    await nav(base+'/new?source=robot');
    check(await count('details.dc-generalization, .dc-generalization summary')===0,'统计配置没有折叠入口');
    check(await count('.dc-generalization-table th')===6,'空表常驻显示六列表头');
    check(await count('.dc-generalization-empty')===1,'空态直接显示');
    await evaluate("document.querySelector('.dc-generalization').scrollIntoView({block:'start'})");await shot('01-empty-table');
    await click('[data-action=add-generalization]');
    check(await count('#dc-generalization-form')===1&&await count('.dc-g-card')===0,'新增打开弹窗，保存前不插入统计项');
    await click('[data-action=close-dialog]');
    check(await count('.dc-g-card')===0,'取消新增不产生空统计项');
    await click('[data-action=add-generalization]');await click('[form=dc-generalization-form]');
    check(await count('#dc-generalization-form [aria-invalid=true]')===5,'弹窗保存校验名称及参与轴必填');
    await fill('[data-g=name]','左手放杯位置');
    for(const axis of ['X','Y']){await fill(`[data-bound="${axis}"][data-side="0"]`,'-40');await fill(`[data-bound="${axis}"][data-side="1"]`,'40');}
    await fill('[data-g=arm]','right');
    check(await evaluate("document.querySelector('[data-g=operator]').value.includes('right')"),'取点规则变化正确关联算子');
    await fill('[data-g=plane]','XYZ');check(await count('[data-bound=Z]')===2,'三维统计显示Z轴范围');
    await fill('[data-bound=Z][data-side="0"]','0');await fill('[data-bound=Z][data-side="1"]','100');
    check(await count('#dc-generalization-form [aria-invalid=true]')===0,'修正输入后清除过期错误提示');
    await fill('[data-bound=Z][data-side="1"]','0');await click('[form=dc-generalization-form]');
    check(await evaluate("document.querySelector('#dc-g-Z1').getAttribute('aria-invalid')==='true'"),'最小值等于最大值阻止保存');
    await fill('[data-bound=Z][data-side="1"]','100');
    await shot('02a-config-dialog');
    const clip=await evaluate("(()=>{const r=document.querySelector('#dc-dialog').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1}})()");
    const crop=await call('Page.captureScreenshot',{format:'png',clip});fs.writeFileSync(path.join(output,'02a-dialog-crop.png'),Buffer.from(crop.data,'base64'));
    await resize(390,844);await noOverflow('390px配置弹窗无横向溢出');await shot('02b-mobile-dialog');
    await resize(320,844);await noOverflow('320px配置弹窗无横向溢出');
    await resize(1440,1000);await click('[form=dc-generalization-form]');
    check(await count('.dc-g-card')===1&&await count('.dc-generalization-empty')===0,'保存后主表展示统计摘要');
    check(await count('.dc-generalization-table input,.dc-generalization-table select')===0,'主表不再包含配置表单');
    await click('[data-action=edit-generalization]');
    check(await evaluate("document.querySelector('[data-bound=Z][data-side=\"1\"]').value==='100'"),'编辑回显厘米范围');
    await fill('[data-g=name]','取消的修改');await click('[data-action=close-dialog]');
    check((await text('.dc-g-card')).includes('左手放杯位置')&&!(await text('.dc-g-card')).includes('取消的修改'),'取消编辑保留原统计项');
    await click('[data-action=edit-generalization]');await fill('[data-g=name]','左手放杯位置已编辑');await click('[form=dc-generalization-form]');
    check((await text('.dc-g-card')).includes('左手放杯位置已编辑'),'保存编辑更新原统计项');
    await click('[data-action=edit-generalization]');
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await wait("!document.querySelector('#dc-dialog').open");
    check(await evaluate("document.activeElement.matches('[data-action=edit-generalization]')"),'Esc取消编辑并回到编辑入口');
    await fill('#dc-name','常驻展开专项验证');await fill('#dc-project','PRJ-MOZ1-SFT-07');await fill('#dc-description','统计表增删及保存验证');
    await evaluate("document.querySelector('.dc-generalization').scrollIntoView({block:'start'})");await shot('02-editable-table');
    await resize(390,844);await evaluate("document.querySelector('.dc-generalization').scrollIntoView({block:'start'})");await noOverflow('390px有统计配置的页面无横向溢出');await shot('03-mobile-table');
    await resize(320,844);await noOverflow('320px有统计配置的页面无横向溢出');
    await resize(1440,1000);await click('#dc-submit');await wait("/^[0-9]{5}$/.test(location.pathname.split('/').pop())&&!location.pathname.endsWith('/edit')");await wait("document.querySelector('[data-action=share-task]')");
    const normalId=await taskId(),normal=await taskData(normalId);
    check(normal.generalization.length===1&&normal.generalization[0].plane==='XYZ'&&normal.generalization[0].arm==='right','配置创建保存且参数正确');
    check(normal.generalization[0].bounds.X[0]===-.4&&normal.generalization[0].bounds.Z[1]===1,'厘米输入正确转换为米保存');
    await nav(base+'/'+normalId+'/edit');check(await count('.dc-g-card')===1&&await count('[data-action=edit-generalization]')===1,'编辑任务回显统计摘要');
    await click('[data-action=remove-generalization]');check(await count('.dc-g-card')===0&&await count('.dc-generalization-empty')===1,'删光后恢复常驻空表');
    await click('#dc-submit');await wait("/^[0-9]{5}$/.test(location.pathname.split('/').pop())&&!location.pathname.endsWith('/edit')");await wait("document.querySelector('[data-action=share-task]')");
    check((await taskData(normalId)).generalization.length===0,'删除统计项可保存');
    await nav(base+'/new?source=robot');await fill('#dc-mode','DAGGER');
    check(await evaluate("document.querySelector('[data-action=add-generalization]').disabled"),'DAGGER无Prompt时禁止添加关联统计');
    await evaluate("document.querySelector('.dc-generalization').scrollIntoView({block:'center'})");await shot('04a-dagger-empty-table');
    if(process.env.CAPTURE_GENERALIZATION_CROP){
      const clip=await evaluate("(()=>{const r=document.querySelector('.dc-generalization').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1}})()");
      const crop=await call('Page.captureScreenshot',{format:'png',clip});fs.writeFileSync(path.join(output,'04b-dagger-panel.png'),Buffer.from(crop.data,'base64'));
    }
    await click('[data-action=pick-prompts]');await wait("document.querySelector('[data-prompt-choice]')");
    await click('[data-prompt-choice="demo-prompt-pick-cup"]');await click('[data-action=pick-prompts]');
    await click('[data-action=add-generalization]');
    check(await evaluate("document.querySelector('[data-g=prompt_id]').value==='demo-prompt-pick-cup'"),'DAGGER弹窗关联已选Prompt');
    for(const axis of ['X','Y']){await fill(`[data-bound="${axis}"][data-side="0"]`,'-40');await fill(`[data-bound="${axis}"][data-side="1"]`,'40');}
    await click('[form=dc-generalization-form]');
    check(await evaluate("document.querySelector('[data-action=add-generalization]').disabled"),'DAGGER统计项保存后保持Prompt一对一');
    await evaluate("document.querySelector('.dc-generalization').scrollIntoView({block:'start'})");await shot('04-dagger-table');
    await click('[data-prompt-remove="demo-prompt-pick-cup"]');
    check(await count('.dc-g-card')===0&&await count('.dc-generalization-empty')===1,'移除Prompt清除关联统计并恢复空表');
    await nav(base+'/new?source=udas');check(await count('.dc-generalization')===0,'UDAS不引入机器人位置统计');
    const collectionExceptions=exceptions.filter(error=>!error.includes('CodeMirror is not defined'));
    check(collectionExceptions.length===0,'浏览器运行无采集模块未捕获异常：'+collectionExceptions.join('; '));
    const report={passed:assertions.length,assertions,exceptions,screenshots:fs.readdirSync(output).filter(n=>n.endsWith('.png'))};
    fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify({passed:assertions.length,output},null,2));
  } finally {
    if(socket)socket.close();if(chrome)chrome.kill();service.kill();
    // Chrome may still hold its own temporary profile briefly. Never touch a user profile.
    await delay(500);try{if(path.dirname(path.resolve(sandbox))===path.resolve(os.tmpdir())&&path.basename(sandbox).startsWith('quanta-collection-'))fs.rmSync(sandbox,{recursive:true,force:true});}catch(_){}
    try{fs.rmSync(databasePath,{force:true});}catch(_){}
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
