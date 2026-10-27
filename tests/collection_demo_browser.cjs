/* Read-only checks against an explicitly seeded local preview. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawn}=require('node:child_process'),http=require('node:http');
const origin=process.env.COLLECTION_ORIGIN||'http://127.0.0.1:5081';
const out=path.resolve(__dirname,'../instance/collection-multi-examples');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const checks=[];
const check=(value,label)=>{assert.ok(value,label);checks.push(label)};
function get(url){return new Promise((resolve,reject)=>http.get(url,response=>{
  const data=[];response.on('data',chunk=>data.push(chunk));
  response.on('end',()=>{try{resolve(JSON.parse(Buffer.concat(data).toString('utf8')))}catch(error){reject(error)}});
}).on('error',reject));}
async function main(){
  fs.mkdirSync(out,{recursive:true});
  const sandbox=fs.mkdtempSync(path.join(out,'chrome-'));
  const chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',[
    '--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-extensions',
    '--user-data-dir='+sandbox,'--remote-debugging-port=9417','about:blank'],{stdio:'ignore',windowsHide:true});
  let socket;
  try{
    let page;
    for(let i=0;i<100;i++){try{page=(await get('http://127.0.0.1:9417/json/list')).find(p=>p.type==='page');if(page)break}catch{}await delay(100)}
    assert.ok(page,'Chrome ready');
    socket=new WebSocket(page.webSocketDebuggerUrl);
    let id=0;const pending=new Map(),errors=[];
    socket.onmessage=event=>{
      const message=JSON.parse(event.data);
      if(message.id&&pending.has(message.id)){const entry=pending.get(message.id);pending.delete(message.id);clearTimeout(entry.timer);message.error?entry.reject(Error(message.error.message)):entry.resolve(message.result)}
      if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails.exception?.description||message.params.exceptionDetails.text);
    };
    await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject});
    const call=(method,params={})=>new Promise((resolve,reject)=>{
      const key=++id,timer=setTimeout(()=>{pending.delete(key);reject(Error(method))},15000);
      pending.set(key,{resolve,reject,timer});socket.send(JSON.stringify({id:key,method,params}));
    });
    const ev=async expression=>{const result=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw Error(result.exceptionDetails.text);return result.result.value};
    const wait=async expression=>{for(let i=0;i<100;i++){if(await ev(expression))return;await delay(100)}throw Error(expression)};
    const nav=async url=>{await call('Page.navigate',{url:origin+url});await wait(url.startsWith('/data/processing-tasks')?"!!document.querySelector('#dc-processing-confirm')&&!!document.querySelector('[data-collection-processing]')":url.startsWith('/data/tasks/')?"!!document.querySelector('.dpr-record-page')":"document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'")};
    const shot=async name=>{await delay(180);const result=await call('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(result.data,'base64'))};
    const size=(width,height=950)=>call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
    await call('Runtime.enable');await call('Network.enable');await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*']});
    const tasks=(await get(origin+'/api/post-training-collection/tasks')).tasks;
    check(tasks.slice(0,3).map(t=>t.id).join(',')==='02602,02607,02601','关联采集任务按关联数优先、组内保持原顺序');
    check(tasks.slice(3).every(t=>!t.processing_task_count),'未关联任务仍全部保留');
    const jobs=(await get(origin+'/api/post-training-collection/processing/tasks')).tasks;
    check(jobs.length===5,'演示处理任务总量为5个');
    check(jobs.filter(j=>j.source_ids.length===2).length===2,'两个处理任务共用机器人与UDAS来源');
    await size(1440);
    for(const [source,first] of [['robot','02602'],['udas','02607']]){
      await nav('/data/post-training-collection?source='+source);
      check(await ev(`document.querySelector('.dc-task-id')?.textContent===${JSON.stringify(first)}`),source+'列表第一条可见关联示例');
      if(source==='robot')check(await ev("[...document.querySelectorAll('.dc-task-id')].slice(0,2).map(e=>e.textContent).join(',')==='02602,02601'"),'机器人列表前两条均关联处理');
      await shot('list-'+source+'-1440');
    }
    for(const [taskId,recordId,count] of [['02602','DEMO-R-020006',3],['02601','DEMO-R-010001',2],['02607','DEMO-R-070001',2]]){
      await nav('/data/post-training-collection/'+taskId+'#records');
      const selector=`[data-action="record-processing"][data-id="${recordId}"]`;
      await wait(`!!document.querySelector(${JSON.stringify(selector)})`);
      check(await ev(`document.querySelector(${JSON.stringify(selector)}).textContent.trim()===${JSON.stringify(count+' 个任务')}`),taskId+'首屏录制显示正确关联数');
      await ev(`document.querySelector(${JSON.stringify(selector)}).click()`);
      await wait(`document.querySelectorAll('.dc-record-processing-card').length===${count}`);
      check(await ev("[...document.querySelectorAll('.dc-record-processing-card a')].every(a=>a.pathname.startsWith('/data/tasks/')&&new URL(a.href).searchParams.get('data_id')==="+JSON.stringify(recordId)+")"),taskId+'关联弹窗进入处理数据并筛选当前录制');
      const destination=await ev("document.querySelector('.dc-record-processing-card a').getAttribute('href')");
      await nav(destination);
      check(await ev("document.querySelectorAll('.dpr-record-table tbody tr').length===1&&document.querySelector('.dpr-record-table tbody').textContent.includes("+JSON.stringify(recordId)+")"),taskId+'从关联弹窗进入后只展示当前录制');
      await shot('record-'+taskId+'-relations');
      await nav('/data/post-training-collection/'+taskId+'#processing');
      await wait(`document.querySelectorAll('.dc-processing-table tbody tr').length===${count}`);
      check(await ev("[...document.querySelectorAll('.dc-processing-task-name,.dc-processing-row-actions a')].every(a=>a.pathname.startsWith('/data/tasks/')&&new URL(a.href).searchParams.get('collection')==="+JSON.stringify(taskId)+")"),taskId+'关联任务摘要默认查看本采集任务数据');
    }
    // Existing processing configuration and task-data pages are the only destinations.
    for(const [sourceId,prefix] of [['02601','DEMO-R-01'],['02607','DEMO-R-07']]){
      await nav('/data/tasks/30004?collection='+sourceId);
      check(await ev("document.querySelectorAll('.dpr-record-table tbody tr').length===8&&[...document.querySelectorAll('.dpr-record-table tbody tr td:first-child')].every(e=>e.textContent.startsWith("+JSON.stringify(prefix)+"))"),sourceId+'多来源处理只展示当前采集任务八条数据');
      check(await ev("document.querySelector('.dpr-record-summary').textContent.includes('命中 8 条')&&document.querySelector('.dpr-linked-current-source').textContent.includes("+JSON.stringify(sourceId)+")"),sourceId+'数据汇总与当前来源范围一致');
      check(await ev("[...document.querySelectorAll('.dpr-linked-sources a')].some(a=>a.textContent==='查看全部数据'&&a.pathname==='/data/tasks/30004'&&!new URL(a.href).searchParams.has('collection'))&&new URL(document.querySelector('.filter-actions a').href).searchParams.get('collection')==="+JSON.stringify(sourceId)),sourceId+'查看全部可解除来源限制，清空ID筛选保留来源');
      check(await ev("document.querySelector('.dpr-record-top a').getAttribute('href')==='/data/post-training-collection/'+"+JSON.stringify(sourceId)+"+'#processing'"),sourceId+'返回入口回到当前采集任务关联处理页');
      const allPath=await ev("[...document.querySelectorAll('.dpr-linked-sources a')].find(a=>a.textContent==='查看全部数据').getAttribute('href')");
      await nav(allPath);
      check(await ev("document.querySelector('.mini-pager').textContent.includes('共 16 条')&&document.querySelector('.dpr-record-top a').getAttribute('href')==='/data/post-training-collection/'+"+JSON.stringify(sourceId)+"+'#processing'"),sourceId+'查看全部数据后仍保留原采集任务返回入口');
      await ev("document.querySelector('.dpr-record-top a').click()");
      await wait("document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'&&document.querySelector('#dc-detail-tab-processing')?.getAttribute('aria-selected')==='true'");
    }
    await nav('/data/processing-tasks?linked=30004');
    await wait("document.querySelector('#drawerProcessingTaskForm').getAttribute('aria-hidden')==='false'");
    check(await ev("!document.querySelector('#dc-processing-detail')&&document.querySelector('#processingTaskDrawerTitle').textContent==='处理任务详情'"),'关联入口复用原处理详情，不存在额外独立详情层');
    check(await ev("document.querySelector('#processingTaskName').value==='饮料取放数据质检'&&document.querySelector('#processingTaskName').disabled"),'关联任务配置按原详情只读展示');
    check(await ev("[...document.querySelectorAll('.dc-processing-source-context a')].map(a=>a.textContent.slice(0,5)).sort().join(',')==='02601,02607'"),'配置详情保留两个来源采集任务返回链接');
    await shot('processing-shared-config-1440');
    await ev("document.querySelector('[data-task-pane=filter]').click()");
    check(await ev("[...document.querySelectorAll('.dpr-task-filter-field')].some(el=>el.value==='采集任务 ID')&&[...document.querySelectorAll('.dpr-task-filter-value')].some(el=>el.value.includes('02601')&&el.value.includes('02607'))"),'来源过滤条件正确恢复多来源配置');
    await ev("document.querySelector('.dpr-processing-back').click()");
    check(await ev("document.querySelector('#drawerProcessingTaskForm').getAttribute('aria-hidden')==='true'&&!new URLSearchParams(location.search).has('linked')"),'关闭详情返回处理列表且清理详情定位');
    check(await ev("document.querySelector('[data-collection-processing=\"30004\"] .dpr-task-name').getAttribute('href')==='/data/tasks/30004'&&document.querySelector('[data-collection-processing=\"30004\"] .dpr-task-actions a').getAttribute('href')==='/data/tasks/30004'"),'处理列表名称和数据按钮沿用原数据页面入口');
    await ev("document.querySelector('#dpr-processing-task-table tbody tr:not([data-collection-processing]) button[onclick*=\"detail\"]').click()");
    check(await ev("document.querySelector('#drawerProcessingTaskForm').dataset.collectionSource===''&&document.querySelector('.dc-processing-source-context').hidden&&document.querySelector('.dc-processing-actions').hidden"),'查看原有处理任务不残留关联任务上下文');
    for(const width of [1440,1024,390]){
      await size(width,width<760?844:950);
      await nav('/data/processing-tasks?linked=30004');
      await wait("document.querySelector('#drawerProcessingTaskForm').getAttribute('aria-hidden')==='false'");
      check(await ev('document.documentElement.scrollWidth<=innerWidth+1'),width+'统一配置详情无页面溢出');
      await nav('/data/tasks/30004');
      check(await ev('document.documentElement.scrollWidth<=innerWidth+1'),width+'统一处理数据列表无页面溢出');
      if(width===390)check(await ev("document.querySelector('.q-main').getBoundingClientRect().left===0&&document.querySelector('.dpr-record-page').clientWidth>340"),'手机数据页使用完整宽度，不保留隐藏侧栏占位');
      check(await ev("document.querySelectorAll('.dpr-linked-sources a[href*=\"post-training-collection\"]').length===2&&document.querySelectorAll('.dpr-record-table tbody tr').length===10"),width+'数据页面显示全部来源和实际成员分页');
      await shot('processing-shared-data-'+width);
    }
    await size(1440);
    await nav('/data/tasks/30004?page=2');
    check(await ev("document.querySelectorAll('.dpr-record-table tbody tr').length===6&&document.querySelector('.mini-pager .active').textContent==='2'"),'纳入数据分页展示剩余六条，不生成假页数');
    await nav('/data/tasks/30004?data_id=DEMO-R-070001');
    check(await ev("document.querySelectorAll('.dpr-record-table tbody tr').length===1&&document.querySelector('.dpr-record-table tbody').textContent.includes('DEMO-R-070001')"),'处理数据支持查询来源录制');
    check(await ev("document.querySelector('.dpr-record-table tbody td:nth-child(5)').textContent==='-'&&!document.querySelector('.dpr-record-actions a').href.includes('WB-2026')"),'环节完成不伪造质检结论或工作台任务');
    const sourceRecord=(await get(origin+'/api/post-training-collection/tasks/02607')).task.records.find(r=>r.id==='DEMO-R-070001');
    check(await ev("document.querySelector('.dpr-record-table tbody td:nth-child(4)').textContent==="+JSON.stringify({success:'成功',failure:'失败'}[sourceRecord.collection_result]||'-')),'处理数据采集结论与来源采集记录展示一致');
    await nav('/data/tasks/30004?data_id=NO-MATCH');
    check(await ev("document.querySelector('.dpr-empty').textContent==='暂无记录'&&document.querySelector('.mini-pager').textContent.includes('共 0 条')"),'处理数据查询零结果正常展示');
    const originalId=await ev("document.querySelector('.dpr-record-top a').getAttribute('href')");
    check(originalId==='/data/processing-tasks','处理数据返回原处理列表');
    await nav('/data/processing-tasks');
    const originalPath=await ev("document.querySelector('#dpr-processing-task-table tbody tr:not([data-collection-processing]) .dpr-task-name').getAttribute('href')");
    await nav(originalPath);
    check(await ev("!!document.querySelector('.dpr-record-page')&&!document.querySelector('.dpr-linked-sources')"),'原有处理数据页面继续使用原数据和布局');
    await size(1920);await nav('/data/post-training-collection?source=robot');await shot('list-robot-1920');
    await size(390,844);await nav('/data/post-training-collection?source=robot');
    check(await ev('document.documentElement.scrollWidth<=innerWidth+1'),'手机列表无页面横向溢出');await shot('list-robot-390');
    check(errors.filter(e=>!e.includes('CodeMirror is not defined')).length===0,'无新增浏览器错误');
    fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify({passed:checks.length,checks,errors},null,2));
    console.log(JSON.stringify({passed:checks.length,out}));
  }finally{socket?.close();chrome.kill()}
}
main().catch(error=>{console.error(error);process.exitCode=1});
