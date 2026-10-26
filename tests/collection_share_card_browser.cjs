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



    for(const [id,mode,kind] of [['02602','DAGGER','long'],['02601','NORMAL','short'],['02607','UDAS','empty']]){
      await nav(base+'/'+id);
      await evaluate(`(()=>{
        window.savedTexts=[];window.realFetch=window.fetch;
        window.fixtureKind='${kind}';window.closedFixture=false;
        Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>window.savedTexts.push(text)}});
        window.fetch=async(url,...args)=>{
          const response=await window.realFetch(url,...args);
          if(!String(url).includes('/collection-check'))return response;
          const data=await response.json();
          data.task.description=window.fixtureKind==='long'?(data.task.description+' ').repeat(30):window.fixtureKind==='short'?'Short requirement.':'';
          data.task.spec_url=window.fixtureKind==='empty'?'':'https://example.feishu.cn/docx/spec';
          if(window.closedFixture){data.task.status='closed';data.reason='closed';}
          window.serverDescription=data.task.description;
          return new Response(JSON.stringify(data),{status:200,headers:{'Content-Type':'application/json'}});
        };
      })()`);
      await click('[data-action=share-task]');await wait("document.querySelector('.dc-share-text')");
      check(await count('[data-action=copy-task-image],[data-action=download-task-image],.dc-share-image,pre,code')===0,mode+' no images or code frames');
      check(await count('.dc-dialog-foot [data-action]')===2,mode+' text and link share actions only');
      check(await evaluate("getComputedStyle(document.querySelector('.dc-share-card')).borderTopWidth==='0px'&&getComputedStyle(document.querySelector('.dc-share-text')).whiteSpace==='pre-wrap'"),mode+' plain unframed text layout');
      await click('[data-action=copy-task-card]');await wait('window.savedTexts.length===1');
      check(await evaluate("window.savedTexts[0]===document.querySelector('.dc-share-text').textContent"),mode+' preview exactly matches copied text');
      check(await evaluate(`window.savedTexts[0].includes('\u4efb\u52a1 ID\uff1a${id}')&&window.savedTexts[0].includes(String.fromCharCode(10,10))&&!window.savedTexts[0].includes('Prompt')&&!window.savedTexts[0].includes('Checkpoint')`),mode+' fields and paragraph breaks without execution details');
      if(kind==='long'){
        check(await evaluate("window.savedTexts[0].includes('\u91c7\u96c6\u8981\u6c42\uff08\u8282\u9009\uff09')&&window.savedTexts[0].includes(Array.from(window.serverDescription.replace(/\\s+/g,' ').trim()).slice(0,100).join('')+'\u2026')&&window.savedTexts[0].includes('\u5b8c\u6574\u91c7\u96c6\u8981\u6c42\u8bf7\u67e5\u770b\u4efb\u52a1\u8be6\u60c5\u3002')"),'long text is a verbatim 100 character excerpt with ellipsis and detail instruction');
        check(await evaluate('window.savedTexts[0].length<600'),'thousand character source stays compact');
      }else if(kind==='short')check(await evaluate("window.savedTexts[0].includes('Short requirement.')&&!window.savedTexts[0].includes('\u8282\u9009')&&!window.savedTexts[0].includes('\u2026')"),'short requirements retain full text without excerpt label');
      else check(await evaluate("!window.savedTexts[0].includes('\u91c7\u96c6\u89c4\u8303\uff1a')&&!document.querySelector('.dc-share-live-links a[href*=feishu]')&&window.savedTexts[0].includes('\u89c1\u4efb\u52a1\u8be6\u60c5\u3002')"),'empty requirements and missing spec handled without placeholders');
      await click('[data-action=copy-task-link]');await wait('window.savedTexts.length===2');
      check(await evaluate(`window.savedTexts[1].endsWith('/${id}#config')`),mode+' link opens full requirements without reopening the share card');
      await shot(mode+'-desktop');
      for(const width of [390,320]){await resize(width,844);await noOverflow(mode+' '+width+' page fits');check(await evaluate("document.querySelector('#dc-dialog').scrollWidth<=document.querySelector('#dc-dialog').clientWidth+1"),mode+' '+width+' dialog fits');await shot(mode+'-'+width);}
      await resize(1440,1000);
      if(kind==='long'){
        await evaluate('window.closedFixture=true');await click('[data-action=check-latest-task]');
        await wait("document.querySelector('[data-collection-check]')?.getAttribute('data-collection-check')==='closed'");
        check(await evaluate("!document.querySelector('[data-collection-check]').hidden&&document.querySelector('.dc-share-text').textContent.includes('\u5df2\u7ed3\u675f\u91c7\u96c6')"),'closed tasks retain visible warning in preview and copied content');
        await click('[data-action=copy-task-card]');await wait('window.savedTexts.length===3');
        check(await evaluate("window.savedTexts[2]===document.querySelector('.dc-share-text').textContent&&window.savedTexts[2].includes('\u5df2\u7ed3\u675f\u91c7\u96c6')"),'copy uses latest closed state and still matches preview');
      }
      await click('[data-action=close-dialog]');
    }
    await nav(base+'/02602');await click('[data-action=share-task]');await wait("document.querySelector('.dc-share-text')");
    await evaluate(`(()=>{window.savedTexts=[];window.originalFetch=window.fetch;Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async t=>window.savedTexts.push(t)}});window.fetch=(url,...args)=>String(url).includes('/collection-check')?Promise.reject(new Error('offline')):window.originalFetch(url,...args);})()`);
    await click('[data-action=copy-task-card]');await wait("document.querySelector('#dc-toast').textContent.includes('\u672a\u590d\u5236')");
    check(await evaluate('window.savedTexts.length===0'),'latest fetch failure does not copy stale content');
    await evaluate("window.fetch=window.originalFetch;Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('denied')}}})");
    await click('[data-action=copy-task-card]');await wait("document.querySelector('#dc-dialog textarea')");
    check(await evaluate("document.querySelector('#dc-dialog textarea').value.includes('02602')"),'clipboard denial allows manual text copying');
    check(await evaluate(`(()=>{const t={id:'12345',name:'Test',description:'x'.repeat(99)+'\u{1f600}'+'tail',source:'robot',status:'open'};const model=DCShareCard.model(t,{project:'Demo',mode:'NORMAL',link:'test'});return model.excerpted&&Array.from(model.description).length===101&&model.description.endsWith('\u{1f600}\u2026');})()`),'excerpt does not split surrogate pairs');
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
