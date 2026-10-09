const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const previewUrl = process.env.PREVIEW_URL || 'http://127.0.0.1:5004/data/workbench-v2/optimized';
const debugPort = Number(process.env.DEBUG_PORT || 9337);
(async () => {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'quanta-action-'));
  const chrome = spawn(process.env.BROWSER_EXE || 'C:/Program Files/Google/Chrome/Application/chrome.exe', ['--headless=old','--disable-gpu','--no-sandbox','--no-first-run','--no-default-browser-check','--window-size=1574,900',`--user-data-dir=${profile}`,`--remote-debugging-port=${debugPort}`,previewUrl], {stdio:'ignore'});
  try {
    let target;
    for (let i=0;i<100;i+=1) { try { const pages=await fetch(`http://127.0.0.1:${debugPort}/json/list`).then(r=>r.json()); target=pages.find(p=>p.type==='page'&&p.url.includes('optimized')); if(target)break; } catch(_){} await delay(100); }
    assert.ok(target,'应打开动作标注工作台');
    const socket=new WebSocket(target.webSocketDebuggerUrl), pending=new Map(), errors=[]; let sequence=0;
    socket.onmessage=event=>{const message=JSON.parse(event.data);if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails?.exception?.description||message.params.exceptionDetails?.text);if(message.id&&pending.has(message.id)){const task=pending.get(message.id);pending.delete(message.id);message.error?task.reject(new Error(message.error.message)):task.resolve(message.result);}};
    await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
    const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const result=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(result.exceptionDetails)throw new Error(result.exceptionDetails.text);return result.result.value;};
    await call('Runtime.enable');
    for(let i=0;i<100;i+=1){if(await evaluate("document.querySelector('.main')?.getAttribute('aria-busy')==='false'"))break;await delay(100);}
    await evaluate("document.querySelector('[data-review-variant=action]').click()");
    assert.equal(await evaluate("document.querySelectorAll('workbench-segment-editor[variant=variant-3] .action-element-group').length"),5);
    assert.deepEqual(await evaluate("[...document.querySelectorAll('workbench-segment-editor[variant=variant-3] .action-element-group__title')].map(e=>e.textContent)"),['物体Object','位置Location','容器Container','水果Fruit','工具Tool']);
    assert.equal(await evaluate("[...document.querySelectorAll('workbench-segment-editor[variant=variant-3] workbench-multi-select[aria-label=\"动作描述\"] [data-multi-option]')].some(e=>e.textContent.includes('{Object}'))"),true);
    await evaluate(`(()=>{const e=document.querySelector('workbench-segment-editor[variant=variant-3]');const a=e.querySelector('workbench-multi-select[aria-label="动作元素"]'),d=e.querySelector('workbench-multi-select[aria-label="动作描述"]');a.querySelector('.workbench-multi-select__clear').click();d.querySelector('.workbench-multi-select__clear').click();a.querySelector('[data-multi-option="书本"]').click();a.querySelector('[data-multi-option="笔记本"]').click();d.querySelector('.workbench-multi-select__trigger').click()})()`);
    assert.deepEqual(await evaluate("[...document.querySelectorAll('workbench-segment-editor[variant=variant-3] workbench-multi-select[aria-label=\"动作描述\"] [data-multi-option]:not([hidden])')].map(e=>e.textContent)"),['整理 {Object} 和 {Object}✓']);
    assert.equal(await evaluate("document.querySelector('workbench-segment-editor[variant=variant-3] workbench-multi-select[aria-label=\"动作描述\"] [data-multi-option=\"整理\"]').hidden"),true);
    await evaluate(`document.querySelector('workbench-segment-editor[variant=variant-3] workbench-multi-select[aria-label="动作描述"] [data-multi-option="整理两个物体"]').click()`);
    assert.equal(await evaluate("document.querySelector('workbench-segment-editor[variant=variant-3] workbench-multi-select[aria-label=\"动作描述\"] .workbench-multi-select__tag').textContent.replace('×','').trim()"),'整理 {书本} 和 {笔记本}');
    await evaluate(`document.querySelector('workbench-segment-editor[variant=variant-3] workbench-multi-select[aria-label="动作元素"]').setValues(['书本','苹果'],true)`);
    assert.equal(await evaluate("[...document.querySelectorAll('workbench-segment-editor[variant=variant-3] workbench-multi-select[aria-label=\"动作描述\"] [data-multi-option]')].filter(e=>!e.hidden).length"),0);
    assert.equal(await evaluate("document.querySelectorAll('workbench-segment-editor[variant=variant-3] workbench-multi-select[aria-label=\"动作描述\"] .workbench-multi-select__tag').length"),0);
    assert.equal(await evaluate("(()=>{const e=document.querySelector('workbench-segment-editor[variant=variant-3]');return window.ActionAnnotationRules.validate(e._actionData[e._index-1]).valid})()"),false);
    await evaluate("document.querySelector('workbench-segment-list .workbench-review__main > workbench-footer-actions button[data-action=submit]').click()");
    assert.equal(await evaluate("document.querySelector('.action-rule-error-dialog')?.open"),true);
    assert.match(await evaluate("document.querySelector('.action-rule-error-dialog').textContent"),/标注内容有误，请检查动作元素和动作描述/);
    await evaluate(`(()=>{const e=document.querySelector('workbench-segment-editor[variant=variant-3]');const a=e.querySelector('workbench-multi-select[aria-label="动作元素"]'),d=e.querySelector('workbench-multi-select[aria-label="动作描述"]');a.querySelector('.workbench-multi-select__clear').click();return d.values.length})()`);
    await evaluate("document.querySelector('.action-rule-error-dialog [data-close]').click()");
    assert.equal(await evaluate("[...document.querySelectorAll('workbench-segment-editor[variant=variant-3] workbench-multi-select[aria-label=\"动作描述\"] [data-multi-option]')].filter(e=>!e.hidden).length"),0);
    await evaluate(`(()=>{const e=document.querySelector('workbench-segment-editor[variant=variant-3]');const a=e.querySelector('workbench-multi-select[aria-label="动作元素"]'),d=e.querySelector('workbench-multi-select[aria-label="动作描述"]');a.querySelector('[data-multi-option="苹果"]').click();a.querySelector('[data-multi-option="草莓"]').click();a.querySelector('[data-multi-option="杯子"]').click();d.querySelector('[data-multi-option="将两种水果放入容器"]').click()})()`);
    assert.deepEqual(await evaluate("[...document.querySelectorAll('workbench-segment-editor[variant=variant-3] .action-element-group:not([hidden])')].map(e=>e.dataset.elementType)"),['Object','Location','Container','Fruit','Tool']);
    assert.equal(await evaluate("document.querySelector('workbench-segment-editor[variant=variant-3] [data-multi-option=\"香蕉\"]').disabled"),false);
    assert.equal(await evaluate("document.querySelector('workbench-segment-editor[variant=variant-3] [data-multi-option=\"碗\"]').disabled"),false);
    assert.equal(await evaluate("document.querySelector('workbench-segment-editor[variant=variant-3] workbench-multi-select[aria-label=\"动作描述\"] .workbench-multi-select__tag').textContent.replace('×','').trim()"),'将 {苹果}、{草莓} 放入 {杯子}');
    assert.equal(await evaluate("window.ActionAnnotationRules.validate(document.querySelector('workbench-segment-editor[variant=variant-3]')._actionData[1]).valid"),true);
    assert.deepEqual(errors,[]);
    console.log('PASS: grouped elements, one-way description filtering, placeholder filling and submit blocking.');
  } finally {
    chrome.kill();
    await delay(300);
    try { fs.rmSync(profile,{recursive:true,force:true}); } catch (_) {}
  }
})().catch(error=>{console.error(error);process.exit(1);});
