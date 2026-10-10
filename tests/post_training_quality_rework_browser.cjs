const fs=require('fs'),path=require('path'),http=require('http'),os=require('os'),assert=require('node:assert/strict');
const {spawn}=require('child_process');
const root=path.resolve(__dirname,'..'),port=5027,debug=9347;
const server=http.createServer((req,res)=>{const pathname=new URL(req.url,'http://localhost').pathname;const file=pathname==='/data/workbench-v2/optimized'?path.join(root,'templates/annotation_workbench/optimized.html'):path.join(root,pathname);if(!fs.existsSync(file)){res.writeHead(404);return res.end();}res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':file.endsWith('.svg')?'image/svg+xml':'text/html');res.end(fs.readFileSync(file,'utf8').replace('{{ tag_tree | tojson }}','[]'));});
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function main(){
 await new Promise(resolve=>server.listen(port,'127.0.0.1',resolve));
 const profile=fs.mkdtempSync(path.join(os.tmpdir(),'quanta-rework-'));
 const chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=old','--disable-gpu','--no-first-run',`--window-size=${process.env.WINDOW_SIZE||'1440,900'}`,`--user-data-dir=${profile}`,`--remote-debugging-port=${debug}`,`http://127.0.0.1:${port}/data/workbench-v2/optimized`],{stdio:'ignore'});
 let socket;
 try{
  let page;for(let n=0;n<100;n++){try{page=(await fetch(`http://127.0.0.1:${debug}/json/list`).then(r=>r.json())).find(p=>p.url.includes('optimized'));if(page)break;}catch(_){}await delay(100);}
  socket=new WebSocket(page.webSocketDebuggerUrl);let seq=0;const pending=new Map(),errors=[];
  socket.onmessage=event=>{const message=JSON.parse(event.data);if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails.text);if(pending.has(message.id)){pending.get(message.id)(message.result);pending.delete(message.id);}};
  await new Promise(resolve=>socket.onopen=resolve);
  const call=(method,params={})=>new Promise(resolve=>{const id=++seq;pending.set(id,resolve);socket.send(JSON.stringify({id,method,params}));});
  const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
  await call('Runtime.enable');await call('Page.enable');
  for(let n=0;n<100;n++){if(await evaluate("document.querySelector('.main')?.getAttribute('aria-busy')==='false'"))break;await delay(100);}
  await evaluate("document.querySelector('[data-review-variant=post-quality-rework]').click()");
  assert.equal(await evaluate("document.querySelector('post-rework-training-quality-workspace').hidden"),false);
  assert.equal(await evaluate("document.querySelector('post-training-quality-workspace').hidden"),true);
  assert.equal(await evaluate("document.querySelectorAll('post-rework-training-quality-timeline .ptq-lane').length"),3);
  assert.equal(await evaluate("document.querySelectorAll('post-rework-training-quality-timeline .ptqw-track-issue').length"),3);
  assert.equal(await evaluate("document.querySelectorAll('post-rework-training-quality-sidebar .ptqr-issue-badge').length"),3);
  assert.equal(await evaluate("getComputedStyle(document.querySelector('post-rework-training-quality-sidebar .ptqr-issue-badge')).backgroundColor"),'rgb(255, 97, 119)');
  assert.equal(await evaluate("document.querySelector('post-rework-training-quality-sidebar [data-action=submit]').textContent"),'重新提交');
  assert.equal(await evaluate("document.querySelector('.ptqw-status').textContent.includes('【新】')"),false);
  assert.equal(await evaluate("getComputedStyle(document.querySelector('[data-review-variant=post-quality-rework]')).fontSize"),await evaluate("getComputedStyle(document.querySelector('[data-review-variant=post-quality-review]')).fontSize"));
  assert.equal(await evaluate("document.querySelectorAll('.ptqw-chip.is-error').length"),1);
  assert.equal(await evaluate("document.querySelectorAll('.ptqw-chip.is-correct').length"),0);
  assert.equal(await evaluate("document.querySelector('.ptqw-note-text').textContent.includes('请重点核对右臂视角')"),true);
  await delay(100);
  await evaluate("document.querySelector('.ptqw-feedback-note button').click()");
  assert.equal(await evaluate("document.querySelector('.ptqw-note-dialog').open"),true);
  assert.equal(await evaluate("document.querySelector('.ptqw-note-dialog>div').textContent===document.querySelector('.ptqw-note-text').textContent"),true);
  await evaluate("document.querySelector('.ptqw-note-dialog footer button').click()");
  assert.equal(await evaluate("document.querySelectorAll('.ptqw-chip.is-omitted').length"),1);
  const feedback=await evaluate("JSON.stringify(PostTrainingQualityReworkDemo.state.segments[0].feedback)");
  const original=await evaluate("JSON.stringify(PostTrainingQualityDemo.state.segments)");
  await evaluate("document.querySelector('post-rework-training-quality-workspace [data-action=remove-reason][data-reason-id=M02]').click()");
  assert.equal(await evaluate("PostTrainingQualityReworkDemo.state.segments[0].mistakeReasons.includes('M02')"),false);
  assert.equal(await evaluate("JSON.stringify(PostTrainingQualityReworkDemo.state.segments[0].feedback)"),feedback);
  assert.equal(await evaluate("JSON.stringify(PostTrainingQualityDemo.state.segments)"),original);
  await evaluate("document.querySelector('[data-rework-filter=issues]').click()");
  assert.equal(await evaluate("[...document.querySelectorAll('post-rework-training-quality-sidebar .ptq-list-item')].filter(x=>!x.hidden).length"),3);
  await evaluate("document.querySelector('post-rework-training-quality-sidebar [data-action=save]').click()");
  await call('Page.reload');await delay(1000);
  await evaluate("document.querySelector('[data-review-variant=post-quality-rework]').click()");
  assert.equal(await evaluate("PostTrainingQualityReworkDemo.state.segments[0].mistakeReasons.includes('M02')"),false);
  assert.equal(await evaluate("JSON.stringify(PostTrainingQualityReworkDemo.state.segments[0].feedback)"),feedback);
  await evaluate("document.querySelector('post-rework-training-quality-sidebar [data-action=submit]').click()");
  assert.equal(await evaluate("document.querySelector('#ptqwSubmitDialog').open"),true);
  await evaluate("document.querySelector('#ptqwSubmitDialog [data-action=confirm-submit]').click()");
  assert.equal(await evaluate("PostTrainingQualityReworkDemo.state.submitted"),true);
  assert.equal(await evaluate("document.querySelector('post-rework-training-quality-workspace [data-action=toggle-reasons]').disabled"),true);
  const bounds=await evaluate("(()=>{const e=document.querySelector('post-rework-training-quality-workspace').getBoundingClientRect(),s=document.querySelector('post-rework-training-quality-sidebar').getBoundingClientRect();return{bottom:e.bottom,right:s.right,width:innerWidth,height:innerHeight}})()");
  assert.ok(bounds.bottom<=bounds.height+1,JSON.stringify(bounds));assert.ok(bounds.right<=bounds.width+1);
  const screenshot=await call('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(root,'../03-requirements/S027-后训练质检平台/驳回处理-验收.png'),Buffer.from(screenshot.data,'base64'));
  assert.deepEqual(errors,[]);console.log('Rework browser passed',process.env.WINDOW_SIZE||'1440,900');
 }finally{socket?.close();chrome.kill();server.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
