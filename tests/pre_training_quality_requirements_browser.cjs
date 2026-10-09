const assert=require('node:assert/strict');
const fs=require('node:fs');
const http=require('node:http');
const os=require('node:os');
const path=require('node:path');
const {spawn}=require('node:child_process');

const root=path.resolve(__dirname,'..');
const port=Number(process.env.TEST_PORT||5015);
const debugPort=Number(process.env.DEBUG_PORT||9336);
const url=`http://127.0.0.1:${port}/data/workbench-v2/optimized`;
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml'};
const server=http.createServer((request,response)=>{
  const pathname=new URL(request.url,url).pathname;
  if(pathname==='/data/workbench-v2/optimized'){
    const html=fs.readFileSync(path.join(root,'templates/annotation_workbench/optimized.html'),'utf8').replace('{{ tag_tree | tojson }}','[]');
    response.writeHead(200,{'content-type':mime['.html']});response.end(html);return;
  }
  if(pathname.startsWith('/static/')){
    const file=path.resolve(root,'.'+pathname);
    if(file.startsWith(root)&&fs.existsSync(file)){response.writeHead(200,{'content-type':mime[path.extname(file)]||'application/octet-stream'});response.end(fs.readFileSync(file));return;}
  }
  response.writeHead(404);response.end();
});
const delay=milliseconds=>new Promise(resolve=>setTimeout(resolve,milliseconds));

async function main(){
  await new Promise(resolve=>server.listen(port,'127.0.0.1',resolve));
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'quanta-prq-'));
  const chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless=old','--disable-gpu','--no-sandbox','--no-first-run',`--window-size=${process.env.WINDOW_SIZE||'1440,900'}`,`--user-data-dir=${profile}`,`--remote-debugging-port=${debugPort}`,url],{stdio:'ignore'});
  try{
    let page;
    for(let index=0;index<80;index+=1){try{const pages=await fetch(`http://127.0.0.1:${debugPort}/json/list`).then(response=>response.json());page=pages.find(item=>item.type==='page'&&item.url.includes('optimized'));if(page)break;}catch(_){}await delay(100);}
    assert.ok(page,'应打开新版工作台页面');
    const socket=new WebSocket(page.webSocketDebuggerUrl),pending=new Map();let sequence=0;
    socket.onmessage=event=>{const message=JSON.parse(event.data);if(message.id&&pending.has(message.id)){const task=pending.get(message.id);pending.delete(message.id);message.error?task.reject(new Error(message.error.message)):task.resolve(message.result);}};
    await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
    const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const result=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(result.exceptionDetails)throw new Error(result.exceptionDetails.text);return result.result.value;};
    await call('Runtime.enable');
    for(let index=0;index<100;index+=1){if(await evaluate("document.querySelector('.main')?.getAttribute('aria-busy')==='false'"))break;await delay(100);}
    await evaluate("document.querySelector('[data-review-variant=pre-quality]').click()");

    assert.equal(await evaluate("document.querySelector('pre-training-quality-workspace').hidden"),false);
    assert.equal(await evaluate("document.querySelectorAll('.prq-conclusion-switch label').length"),2,'片段结论只显示失误和不合格');
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.prq-conclusion-switch label')].map(item=>item.textContent.trim())"),['失误','不合格']);
    assert.equal(await evaluate("document.querySelector('.prq-editor-meta-row').contains(document.querySelector('.prq-editor-actions'))"),true,'基础信息和导航操作应在同一行');
    assert.equal(await evaluate("document.querySelector('.prq-editor-meta-row').compareDocumentPosition(document.querySelector('.prq-editor-fields-row'))&Node.DOCUMENT_POSITION_FOLLOWING"),4,'结论和原因应位于下一行');
    assert.equal(await evaluate("document.querySelector('.prq-reason-label').textContent.trim()"),'失误描述');
    assert.equal(await evaluate("document.querySelector('.prq-reason-trigger').contains(document.querySelector('.prq-selected-reasons'))"),true,'已选原因应显示在原因选择框内');
    assert.ok(await evaluate("document.querySelector('.prq-reason-trigger').getBoundingClientRect().width>document.querySelector('.prq-conclusion-switch').getBoundingClientRect().width*3"),'原因选择框应占据该行主要宽度');
    assert.equal(await evaluate("document.body.innerText.includes('当前片段已完善')"),false,'错误原因旁不应显示完成状态');

    await evaluate("document.querySelector('.prq-list-item[data-segment-id=B]').click()");
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.prq-selected-reasons .prq-reason-chip')].map(item=>item.firstElementChild.textContent)"),['设备穿戴不规范','手部脱离夹爪'],'原因应全部平铺且不合格原因在前');
    assert.equal(await evaluate("document.querySelector('.prq-selected-reasons').textContent.includes('+')"),false,'原因不应折叠成 +N');
    assert.equal(await evaluate("document.querySelectorAll('.prq-selected-reasons .prq-reason-remove').length"),2,'每个已选原因应有独立删除按钮');
    assert.equal(await evaluate("document.querySelectorAll('.prq-selected-reasons .prq-reasons-clear').length"),1,'全部已选原因应有统一清空按钮');
    await evaluate("document.querySelector('pre-training-quality-workspace [data-action=toggle-reasons]').click()");
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.prq-reason-menu section>header b')].map(item=>item.textContent)"),['不合格原因','失误原因']);
    const menu=await evaluate("(()=>{const menu=document.querySelector('.prq-reason-menu'),rect=menu.getBoundingClientRect(),trigger=document.querySelector('pre-training-quality-workspace [data-action=toggle-reasons]').getBoundingClientRect();return{hidden:menu.hidden,top:rect.top,bottom:rect.bottom,triggerTop:trigger.top,viewport:innerHeight}})()");
    assert.equal(menu.hidden,false);assert.ok(menu.top>=0&&menu.bottom<=menu.triggerTop&&menu.bottom<=menu.viewport,'原因选择面板应向上完整展开');
    await evaluate("document.querySelector('.prq-selected-reasons .prq-reason-remove[data-reason-id=U04]').click()");
    assert.deepEqual(await evaluate("window.PreTrainingQualityDemo.state.segments.find(item=>item.id==='B').rejectedReasons"),[],'单个删除只移除目标原因');
    assert.deepEqual(await evaluate("window.PreTrainingQualityDemo.state.segments.find(item=>item.id==='B').mistakeReasons"),['M02'],'单个删除不影响其他原因');
    await evaluate("document.querySelector('.prq-selected-reasons .prq-reasons-clear').click()");
    assert.deepEqual(await evaluate("(()=>{const item=window.PreTrainingQualityDemo.state.segments.find(item=>item.id==='B');return[item.rejectedReasons,item.mistakeReasons]})()"),[[],[]],'统一删除应清空全部原因');

    const before=await evaluate("window.PreTrainingQualityDemo.state.segments.length");
    await evaluate("window.PreTrainingQualityDemo.addSegment(30,32)");
    assert.equal(await evaluate("window.PreTrainingQualityDemo.state.segments.length"),before+1);
    assert.equal(await evaluate("(()=>{const item=window.PreTrainingQualityDemo.state.segments.at(-1);return item.conclusion})()"),'mistake','新片段默认失误');
    assert.deepEqual(await evaluate("(()=>{const item=window.PreTrainingQualityDemo.state.segments.at(-1);return item.mistakeReasons})()"),[],'新片段不自动选择失误原因');
    assert.equal(await evaluate("window.PreTrainingQualityDemo.segmentErrors(window.PreTrainingQualityDemo.state.segments.at(-1)).some(error=>error.includes('失误原因'))"),true,'缺少失误原因时仍应阻止提交');
    assert.equal(await evaluate("window.PreTrainingQualityDemo.segmentErrors({...window.PreTrainingQualityDemo.state.segments.at(-1),mistakeReasons:['M01'],reviewErrorReason:''}).some(error=>error.includes('错误原因'))"),false,'审核错误原因应为选填');
    await evaluate("document.querySelector('pre-training-quality-sidebar [data-action=save]').click()");
    assert.match(await evaluate("document.querySelector('#workbenchNotice').textContent"),/草稿已保存/,'缺少原因时仍可保存草稿');
    await evaluate("document.querySelector('pre-training-quality-sidebar [data-action=submit]').click()");
    assert.equal(await evaluate("document.querySelector('#prqErrorDialog').open"),true,'缺少原因时阻止提交');
    socket.close();
    console.log('pre-training quality requirements 1-3 browser: passed');
  }finally{chrome.kill();server.close();try{fs.rmSync(profile,{recursive:true,force:true});}catch(_){}}
}
main().catch(error=>{console.error(error);server.close();process.exitCode=1;});
