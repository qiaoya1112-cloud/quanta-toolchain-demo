const assert=require('node:assert/strict');
const fs=require('node:fs');
const http=require('node:http');
const os=require('node:os');
const path=require('node:path');
const {spawn}=require('node:child_process');

const root=path.resolve(__dirname,'..');
const port=Number(process.env.TEST_PORT||5034);
const url=`http://127.0.0.1:${port}/data/workbench-v2/optimized`;
const debugPort=Number(process.env.DEBUG_PORT||9354);
const browserExe=process.env.BROWSER_EXE||'C:/Program Files/Google/Chrome/Application/chrome.exe';
const size=process.env.WINDOW_SIZE||'1440,900';
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.png':'image/png'};
const server=http.createServer((req,res)=>{const target=new URL(req.url,`http://127.0.0.1:${port}`);if(target.pathname==='/data/workbench-v2/optimized'){res.writeHead(200,{'content-type':mime['.html']});res.end(fs.readFileSync(path.join(root,'templates/annotation_workbench/optimized.html'),'utf8').replace('{{ tag_tree | tojson }}','[]'));return;}if(target.pathname.startsWith('/static/')){const file=path.resolve(root,'.'+target.pathname);if(file.startsWith(root)&&fs.existsSync(file)){res.writeHead(200,{'content-type':mime[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));return;}}res.writeHead(404);res.end();});
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));

async function main(){
  await new Promise(resolve=>server.listen(port,'127.0.0.1',resolve));
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'quanta-ptqr-'));
  const chrome=spawn(browserExe,['--headless=old','--disable-gpu','--no-sandbox','--no-first-run',`--window-size=${size}`,`--user-data-dir=${profile}`,`--remote-debugging-port=${debugPort}`,url],{stdio:'ignore'});
  try{
    let page;for(let i=0;i<100;i++){try{page=(await fetch(`http://127.0.0.1:${debugPort}/json/list`).then(r=>r.json())).find(item=>item.url.includes('optimized'));if(page)break;}catch(_){}await delay(100);}assert.ok(page,'工作台页面应打开');
    const socket=new WebSocket(page.webSocketDebuggerUrl),pending=new Map(),errors=[];let seq=0;
    socket.onmessage=event=>{const message=JSON.parse(event.data);if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails?.exception?.description||message.params.exceptionDetails?.text);if(message.id&&pending.has(message.id)){const task=pending.get(message.id);pending.delete(message.id);message.error?task.reject(new Error(message.error.message)):task.resolve(message.result);}};
    await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
    const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const response=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(response.exceptionDetails)throw new Error(response.exceptionDetails.text);return response.result.value;};
    await call('Runtime.enable');await call('Page.enable');for(let i=0;i<100;i++){if(await evaluate("document.querySelector('.main')?.getAttribute('aria-busy')==='false'"))break;await delay(100);}
    await evaluate("document.querySelector('[data-review-variant=post-quality-second-review]').click()");
    const host='post-training-quality-second-review-workspace',side='post-training-quality-second-review-sidebar';
    assert.equal(await evaluate("document.querySelector('post-training-quality-second-review-workspace').hidden"),false);
    assert.equal(await evaluate("document.querySelector('post-training-quality-review-workspace').hidden"),true);
    assert.equal(await evaluate("document.querySelectorAll('post-training-quality-second-review-timeline .ptqr-lane').length"),3);
    assert.equal(await evaluate("document.querySelector('post-training-quality-second-review-sidebar header b').textContent"),'二次审核列表');
    assert.equal(await evaluate("PostTrainingQualitySecondReviewDemo.state.segments[0].originalMistakeReasons.includes('M02')"),false);
    assert.equal(await evaluate("PostTrainingQualitySecondReviewDemo.state.segments[0].originalMistakeReasons.includes('M03')"),true);
    assert.equal(await evaluate("PostTrainingQualitySecondReviewDemo.state.segments[1].originalMistakeReasons.includes('M03')"),true);
    assert.equal(await evaluate("document.querySelector('post-training-quality-second-review-workspace .ptqs-previous').textContent.includes('手部脱离夹爪')"),true);
    await evaluate("document.querySelector('post-training-quality-second-review-sidebar [data-action=filter-previous]').click()");
    assert.equal(await evaluate("[...document.querySelectorAll('post-training-quality-second-review-sidebar .ptqr-list-item')].filter(row=>row.getClientRects().length>0&&getComputedStyle(row).display!=='none').length"),3);
    assert.deepEqual(await evaluate("[...document.querySelectorAll('post-training-quality-second-review-sidebar .ptqr-list-item')].map(row=>row.dataset.segmentId)"),await evaluate("PostTrainingQualitySecondReviewDemo.state.segments.slice(0,3).map(item=>item.id)"));
    assert.equal(await evaluate("document.querySelector('.ptqs-previous-marker')===null"),true);
    await evaluate("document.querySelector('post-training-quality-second-review-sidebar [data-action=filter-all]').click()");
    assert.equal(await evaluate("document.querySelectorAll('post-training-quality-second-review-sidebar .ptqr-list-item').length"),8);
    const previous=await evaluate("JSON.stringify(PostTrainingQualitySecondReviewDemo.state.segments.map(item=>item.previousFeedback))");
    const firstAudit=await evaluate("JSON.stringify(PostTrainingQualityReviewDemo.state)");
    await evaluate("document.querySelector('post-training-quality-second-review-workspace .ptqr-chip.is-correct button').click()");
    assert.equal(await evaluate("PostTrainingQualitySecondReviewDemo.state.segments[0].audit.removed.length"),1);
    assert.equal(await evaluate("JSON.stringify(PostTrainingQualityReviewDemo.state)"),firstAudit);
    await evaluate("document.querySelector('post-training-quality-second-review-sidebar [data-action=reject]').click()");
    assert.equal(await evaluate("document.querySelector('#ptqsValidationDialog').open"),true);
    await evaluate("document.querySelector('#ptqsValidationDialog').close();document.querySelector('post-training-quality-second-review-workspace [data-action=toggle-error]').click();document.querySelector('post-training-quality-second-review-workspace [data-review-error]').click()");
    await evaluate("document.querySelector('post-training-quality-second-review-workspace [data-action=toggle-add]').click()");
    await delay(100);
    assert.equal(await evaluate("(()=>{const r=document.querySelector('post-training-quality-second-review-workspace .ptqr-add-menu').getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&r.right<=innerWidth})()"),true);
    await evaluate("document.querySelector('post-training-quality-second-review-workspace [data-action=add-omission]').click()");
    const feedback=await evaluate("PostTrainingQualitySecondReviewDemo.state.segments[0].audit.added.length");assert.equal(feedback,1);
    await evaluate("document.querySelector('post-training-quality-second-review-workspace .ptqr-note-field input').value='二次复核说明';document.querySelector('post-training-quality-second-review-workspace .ptqr-note-field input').dispatchEvent(new Event('input',{bubbles:true}))");
    await evaluate("document.querySelector('post-training-quality-second-review-sidebar [data-action=save]').click()");
    await call('Page.reload');await delay(1000);await evaluate("document.querySelector('[data-review-variant=post-quality-second-review]').click()");
    assert.equal(await evaluate("PostTrainingQualitySecondReviewDemo.state.segments[0].reviewNote"),'二次复核说明');
    assert.equal(await evaluate("PostTrainingQualitySecondReviewDemo.state.segments[0].audit.added.length"),1);
    assert.equal(await evaluate("JSON.stringify(PostTrainingQualitySecondReviewDemo.state.segments.map(item=>item.previousFeedback))"),previous);
    await evaluate("document.querySelector('post-training-quality-second-review-sidebar [data-action=reject]').click()");
    assert.equal(await evaluate("document.querySelector('#ptqsSubmitDialog').open"),true);
    await evaluate("document.querySelector('#ptqsSubmitDialog [data-action=confirm-submit]').click()");
    assert.equal(await evaluate("PostTrainingQualitySecondReviewDemo.state.submitted"),true);
    assert.equal(await evaluate("document.querySelector('post-training-quality-second-review-workspace .ptqr-chip button').disabled"),true);
    assert.equal(await evaluate("(()=>{const r=document.querySelector('post-training-quality-second-review-workspace').getBoundingClientRect();return r.bottom<=innerHeight+1&&r.right<=innerWidth})()"),true);
    assert.deepEqual(errors,[]);
    const capture=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(path.resolve(root,'../03-requirements/S027-后训练质检平台/二次审核-验收.png'),Buffer.from(capture.data,'base64'));
    socket.close();console.log(`Second review browser passed at ${size}`);
  }finally{chrome.kill();server.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
