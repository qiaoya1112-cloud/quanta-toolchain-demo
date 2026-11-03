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
    await call('Runtime.enable');await call('Page.enable');await call('Network.enable');
    await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*']});await nav(base);

    await resize(1440,1000);
    await nav(base+'/new?source=robot');
    check(await evaluate("document.querySelector('#dc-spec_url').value===''&&document.querySelector('[data-spec-action=open]').disabled"),'空链接时打开规范按钮不可用，不回退到示例');
    check((await count('#dc-spec-viewer,iframe[data-spec]'))===0,'不创建规范预览抽屉或正文框架');
    await fill('#dc-name','规范外链测试');
    await fill('#dc-description','保留已填写采集要求');
    for(const bad of ['javascript:alert(1)','data:text/html,test','https://','随便写的文本']) {
      await fill('#dc-spec_url',bad);
      check(await evaluate("document.querySelector('[data-spec-action=open]').disabled&&!document.querySelector('[data-spec-action=open]').hasAttribute('href')"),'无效链接不能打开：'+bad);
    }
    const example='https://nwd4iy9rd2s.feishu.cn/wiki/R1yZwxGaFiTs34koqYDcoKPmnk2?from=copy';
    await fill('#dc-spec_url',example);
    check(await evaluate(`document.querySelector('[data-spec-action=open]').href===${JSON.stringify(example)}&&document.querySelector('[data-spec-action=open]').target==='_blank'&&document.querySelector('[data-spec-action=open]').rel.includes('noopener')`),'有效链接直接指向飞书原文并在新标签页打开');
    check(await evaluate("!document.querySelector('#dc-app').textContent.includes('预览规范')&&!document.querySelector('#dc-app').textContent.includes('阅读示例')"),'创建页移除预览和模拟文档卡片');
    // Cancel external navigation after recording the chosen destination; do not access Feishu.
    await evaluate("document.addEventListener('click',e=>{const a=e.target.closest('a[data-spec-action=open]');if(a){window.selectedSpecUrl=a.href;e.preventDefault();}},true)");
    await click('[data-spec-action=open]');
    check(await evaluate(`window.selectedSpecUrl===${JSON.stringify(example)}&&document.querySelector('#dc-name').value==='规范外链测试'&&document.querySelector('#dc-description').value==='保留已填写采集要求'&&!document.querySelector('#dc-spec-viewer')`),'点击原文入口保留表单，不提交或打开抽屉');
    await evaluate("document.querySelector('#dc-requirements-section').scrollIntoView()");
    await shot('01-spec-link-desktop');
    await fill('#dc-spec_url','');
    check(await evaluate("document.querySelector('[data-spec-action=open]').disabled"),'清空链接立即禁用入口');
    await fill('#dc-spec_url',example);
    await fill('#dc-project','PRJ-MOZ1-SFT-07');
    await click('#dc-submit');
    await wait("/^[0-9]{5}$/.test(location.pathname.split('/').pop())&&document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'");
    const id=await taskId();
    const savedExample=example.split('?')[0];
    check((await taskData(id)).spec_url===savedExample,'创建标准化规范链接，去除分享参数用于规范库去重');
    check(await evaluate("!document.querySelector('#dc-dialog').open"),'创建后直接进入详情，不再弹出询问');
    await click('[data-action=detail-tab][data-value=config]');
    check(await evaluate(`document.querySelector('[data-spec-action=open]').href===${JSON.stringify(savedExample)}&&!document.querySelector('#dc-spec-viewer')`),'详情打开规范直达同一原文，无平台正文');
    await shot('02-spec-link-detail');
    await nav(base+'/'+id+'/edit');
    check(await evaluate(`document.querySelector('#dc-spec_url').value===${JSON.stringify(savedExample)}&&document.querySelector('[data-spec-action=open]').href===${JSON.stringify(savedExample)}`),'编辑页回显已保存的规范链接');
    const another='https://nwd4iy9rd2s.feishu.cn/docx/another-document';
    await fill('#dc-spec_url',another);
    check(await evaluate(`document.querySelector('[data-spec-action=open]').href===${JSON.stringify(another)}`),'修改链接后入口立即使用新地址');
    await nav(base+'/new?source=udas');
    check(await evaluate("document.querySelector('[data-spec-action=open]').disabled"),'UDAS空链接使用相同规则');
    await fill('#dc-spec_url',another);
    check(await evaluate(`document.querySelector('[data-spec-action=open]').href===${JSON.stringify(another)}`),'UDAS同样直达用户填写的原文');
    await nav(base+'/new?source=robot&spec=example');
    check(await evaluate("document.querySelector('#dc-spec_url').value===CollectionSpecLink.url"),'显式示例URL仍可预填链接，不加载模拟正文');
    await fill('#dc-mode','DAGGER');
    await click('[data-action=pick-prompts]');
    check(await evaluate("document.querySelector('#dc-prompt-popup').matches(':popover-open')")&&(await count('[data-prompt-choice]'))>0,'DAGGER Prompt选择不受影响');
    await click('[data-action=pick-prompts]');
    await resize(390,844);
    await noOverflow('390px创建页无横向溢出');
    await evaluate("document.querySelector('#dc-spec_url').scrollIntoView({block:'center'})");
    check(await evaluate("(()=>{const a=document.querySelector('[data-spec-action=open]'),pick=document.querySelector('[data-action=pick-spec]'),i=document.querySelector('#dc-spec_url'),r=i.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&a.getBoundingClientRect().right<=innerWidth&&pick.getBoundingClientRect().right<=innerWidth&&Math.abs(a.getBoundingClientRect().top-pick.getBoundingClientRect().top)<5&&a.getBoundingClientRect().top>=r.bottom})()"),'390px规范链接完整展示，选择已有规范和打开原文在下方同行');
    await shot('03-spec-link-mobile');
    const collectionExceptions=exceptions.filter(error=>!error.includes('CodeMirror is not defined'));
    check(collectionExceptions.length===0,'采集规范模块无未捕获异常：'+collectionExceptions.join('; '));
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
