/* Real browser acceptance, isolated local DB and a fresh Chrome profile. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{spawn}=require('node:child_process');
const root=path.resolve(__dirname,'..'),python=path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const origin='http://127.0.0.1:5063',base='/data/post-training-collection',api='/api/post-training-collection';
const out=path.resolve(process.env.EVIDENCE_DIR||path.join(root,'instance/collection-processing')),delay=ms=>new Promise(r=>setTimeout(r,ms)),checks=[];
const check=(v,label)=>{assert.ok(v,label);checks.push(label)};
async function main(){
  fs.mkdirSync(out,{recursive:true});const sandbox=fs.mkdtempSync(path.join(out,'sandbox-'));
  const service=spawn(python,['-m','flask','--app','toolchain_demo','run','--host','127.0.0.1','--port','5063','--no-reload','--no-debugger'],{cwd:root,env:{...process.env,COLLECTION_DEMO_DB:path.join(sandbox,'collection.sqlite3')},stdio:'ignore',windowsHide:true});
  let chrome,socket;
  try{
    for(let i=0;i<100;i++){try{if((await fetch(origin+api+'/tasks')).ok)break}catch{}await delay(100)}
    chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-extensions',`--user-data-dir=${path.join(sandbox,'chrome')}`,'--remote-debugging-port=9408','about:blank'],{stdio:'ignore',windowsHide:true});
    let page;for(let i=0;i<100;i++){try{page=(await fetch('http://127.0.0.1:9408/json/list').then(r=>r.json())).find(x=>x.type==='page');if(page)break}catch{}await delay(100)}
    if(!page)throw Error('Chrome not ready');
    socket=new WebSocket(page.webSocketDebuggerUrl);let seq=0;const pending=new Map(),errors=[];
    socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(Error(m.error.message)):p.resolve(m.result)}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);if(m.method==='Page.javascriptDialogOpening')call('Page.handleJavaScriptDialog',{accept:true})};
    await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j});
    const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP '+method))},15000);pending.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params}))});
    const ev=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value};
    const wait=async expression=>{for(let i=0;i<100;i++){try{if(await ev(expression))return}catch{}await delay(100)}console.log(await ev("({url:location.href,message:document.querySelector('.dc-processing-message')?.textContent,body:document.querySelector('#dc-app')?.textContent.slice(0,1200)})"));throw Error('等待失败 '+expression)};
    const click=sel=>ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)throw Error('missing '+${JSON.stringify(sel)});e.click()})()`);
    const fill=(sel,value)=>ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)throw Error('missing '+${JSON.stringify(sel)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))})()`);
    const nav=async url=>{await call('Page.navigate',{url:origin+url});await wait(url.startsWith('/data/processing-tasks')?"typeof dprSubmitProcessingTask==='function'&&!!document.querySelector('#dc-processing-confirm')":url.startsWith('/data/rules?')?"document.querySelector('#dc-catalog-count')?.textContent.includes('共')":url==='/data/rules'?"!!document.querySelector('#drawerRuleCreate')":"document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'");};
    const shot=async name=>{await delay(120);const r=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(r.data,'base64'))};
    const size=async(width,height=950)=>{await call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await delay(180);};
    const noOverflow=async label=>{const fits=await ev('document.documentElement.scrollWidth<=innerWidth+1');if(!fits){await shot('overflow');console.log(await ev("[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,20).map(e=>[e.tagName,e.className,e.getBoundingClientRect().width])"));}check(fits,label);};
    const get=async url=>fetch(origin+api+url).then(r=>r.json());
    await call('Runtime.enable');await call('Page.enable');await call('Network.enable');await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*']});await size(1440);
    await nav(base+'/02602#processing');await wait("document.querySelector('[data-action=create-processing]')");
    check(await ev("document.querySelectorAll('[data-action=create-processing]').length===1"),'关联处理空态只保留右上角一个创建入口');
    check(await ev("document.querySelector('#dc-detail-tab-processing').getAttribute('aria-selected')==='true'"),'采集详情有可直接定位的关联处理Tab');await shot('01-empty');
    await click('[data-action=create-processing]');await wait("location.pathname==='/data/processing-tasks'&&document.querySelector('#drawerProcessingTaskForm').dataset.collectionSource");
    check(await ev("document.querySelector('#processingTaskProject').value==='亮剑'&&document.querySelector('#processingTaskProject').disabled"),'连续创建自动带入并锁定来源项目');
    check(await ev("document.querySelector('.dpr-task-filter-value').value==='02602'&&document.querySelector('.dpr-task-filter-value').disabled"),'来源任务ID准确带入，不能误删');
    check(await ev("document.querySelector('#processingTaskName').value.endsWith('_处理任务')"),'从采集发起处理任务自动填写关联名称');
    check(await ev("!document.querySelector('#dc-processing-source')&&!document.querySelector('#dc-processing-source-field')"),'处理创建页不展示重复来源提示或来源下拉框');
    await click('[data-task-pane=flow]');await click('[data-toggle-stage="质检"]');
    await fill('[data-flow-stage="质检"]','标准训练数据自动质检流程');
    await fill('#processingTaskName','');await click('#processingTaskDrawerSubmit');await wait("document.querySelector('.dc-processing-message')?.textContent.includes('请填写处理任务名称')");
    check((await get('/processing/tasks?collection=02602')).tasks.length===0,'处理任务名称为空时阻止创建且不生成半成品');
    await fill('#processingTaskName','桌面采集 · 自动质检');await shot('02-processing-form');
    await click('#processingTaskDrawerSubmit');await wait("location.pathname==='/data/post-training-collection/02602'&&!!document.querySelector('.dc-processing-table')");
    const list=(await get('/processing/tasks?collection=02602')).tasks;check(list.length===1&&list[0].status==='draft','创建处理任务真实持久化，未发布不接收数据');const job=list[0];
    check(await ev("document.querySelector('.dc-processing-table').textContent.includes('未发布')&&document.querySelector('.dc-processing-table').textContent.includes('0 / 11')"),'关联表区分来源和实际纳入量');await shot('03-related-draft');
    await click('.dc-processing-task-name');await wait("!!document.querySelector('.dpr-record-page')");check(await ev("location.pathname.startsWith('/data/tasks/')&&!document.querySelector('#drawerProcessingTaskForm')"),'关联任务默认查看处理数据');await nav('/data/processing-tasks?linked='+job.id);await wait("!!document.querySelector('#drawerProcessingTaskForm [data-job-action=publish]')");
    await click('#drawerProcessingTaskForm [data-job-action=publish]');await wait("document.querySelector('#dc-processing-confirm').open");await click('[data-confirm-action]');
    await wait("document.querySelector('#drawerProcessingTaskForm').dataset.taskStatus==='published'");
    check((await get('/processing/tasks/'+job.id)).task.total_count===11,'处理侧发布确认并纳入已上传数据，上传中不混入');check(await ev("!document.querySelector('#dc-processing-detail')&&document.querySelector('#processingTaskDrawerTitle').textContent==='处理任务详情'&&document.querySelector('.dc-processing-source-context a').textContent.includes('02602')"),'关联任务复用原详情并保留来源，不再生成独立详情页');await shot('04-job-data');
    await nav(base+'/02602#records');await wait("!!document.querySelector('[data-action=record-processing]')");
    for(const width of [1440,1920,1024,390]){
      await size(width,width<760?844:950);
      for(const upload of ['uploaded','all']){
        await fill('[data-record-filter=upload]',upload);
        await noOverflow(width+' '+upload+'采集数据无页面横向溢出');
        check(await ev("(()=>{const row=document.querySelector('.dc-record-table tbody tr');return ['时长','采集结论','关联处理','操作'].every(label=>row.querySelectorAll('[data-label=\"'+label+'\"]').length===1)&&row.children.length===document.querySelectorAll('.dc-record-table th').length})()"),width+' '+upload+'采集数据各列独立且表头数量一致');
        if(width>760){
          for(const edge of ['left','right']){
            await ev(`(()=>{const wrap=document.querySelector('#dc-record-results .dc-table-wrap');wrap.scrollLeft=${edge==='left'?'0':'wrap.scrollWidth'};})()`);await delay(80);
            check(await ev("(()=>{const row=document.querySelector('.dc-record-table tbody tr'),heads=[...document.querySelectorAll('.dc-record-table th')];return heads.every((head,i)=>{const a=head.getBoundingClientRect(),b=row.children[i].getBoundingClientRect();return Math.abs(a.left-b.left)<2&&Math.abs(a.width-b.width)<2})})()"),width+' '+upload+' '+edge+'滚动表头与数据逐列对齐');
            check(await ev("(()=>{const row=document.querySelector('.dc-record-table tbody tr'),linked=row.querySelector('[data-label=关联处理]').getBoundingClientRect(),action=row.querySelector('[data-label=操作]').getBoundingClientRect();return linked.right<=action.left+1&&action.right<=innerWidth&&action.width>=60})()"),width+' '+upload+' '+edge+'固定关联处理与操作列无遮挡');
          }
        }
      }
      await shot('record-layout-'+width);
    }
    await size(1440);await fill('[data-record-filter=upload]','uploaded');
    await click('[data-action=record-processing]');await wait("!!document.querySelector('.dc-record-processing-card')");
    check(await ev("document.querySelector('.dc-record-processing-card').textContent.includes('质检')&&document.querySelector('.dc-record-processing-card').textContent.includes('待处理')"),'单条数据可查看实际进入的任务及该条数据的环节状态');await shot('05-record-trace');await click('[data-action=close-dialog]');
    await click('[data-action=change-state]');await wait("document.querySelector('#dc-dialog').open");check(await ev("document.querySelector('#dc-dialog').textContent.includes('关联处理任务继续按各自状态运行')"),'结束采集明确告知处理状态独立');await click('[data-action=confirm-state]');await wait("document.querySelector('[data-action=change-state]').textContent==='重新开放'");
    check((await get('/processing/tasks/'+job.id)).task.status==='pending','关闭采集保留处理任务与纳入数据');
    await click('[data-action=change-state]');await wait("document.querySelector('#dc-dialog').open");check(await ev("document.querySelector('#dc-dialog').textContent.includes('处理任务不会自动重开')"),'重开采集不默默重开处理任务');await click('[data-action=confirm-state]');await wait("document.querySelector('[data-action=change-state]').textContent==='结束采集'");
    await click('[data-action=detail-tab][data-value=processing]');await wait("!!document.querySelector('.dc-processing-table')");await shot('06-related-active');await noOverflow('1440采集关联处理无页面横向溢出');
    await size(1366,900);await noOverflow('1366采集关联处理无页面横向溢出');await shot('07-related-1366');await size(390,844);await noOverflow('390采集关联处理无页面横向溢出');await shot('08-related-mobile');await size(1440);
    await nav(base+'/new?source=udas');await fill('#dc-name','连续创建入口验证');await fill('#dc-project','PRJ-LIANGJIAN');await fill('#dc-description','根据现场规范执行');await click('#dc-submit-processing');
    await wait("location.pathname==='/data/processing-tasks'&&!!document.querySelector('#drawerProcessingTaskForm').dataset.collectionSource");
    const createdId=await ev("new URLSearchParams(location.search).get('collection')");
    check(await ev("document.querySelector('.dc-processing-source-context').textContent.includes('采集任务已创建')"),'组合创建直接进入处理配置，采集成功不弹窗');await shot('09-create-success');
    await click('.dpr-processing-back');await wait("location.pathname==='/data/post-training-collection/"+createdId+"'&&!!document.querySelector('.dc-processing-empty')");
    check((await get('/tasks/'+createdId)).task.status==='open'&&(await get('/processing/tasks?collection='+createdId)).tasks.length===0,'取消后续创建不会撤销采集任务或生成半成品处理任务');
    // Partial scope: another processing task only receives one exact recording.
    await nav(base+'/02602#processing');await click('[data-action=create-processing]');await wait("!!document.querySelector('#drawerProcessingTaskForm').dataset.collectionSource");await fill('#processingTaskName','仅一条数据质检');await click('[data-task-pane=filter]');await click('[data-filter-group=basic] .dpr-filter-add-bottom');
    const record=(await get('/tasks/02602')).task.records[0];await fill('#processingTaskBasicFilters .dpr-filter-row:nth-child(2) .dpr-task-filter-value',record.id);
    await click('[data-task-pane=flow]');await click('[data-toggle-stage="质检"]');await fill('[data-flow-stage="质检"]','标准训练数据自动质检流程');await click('#processingTaskDrawerSubmit');await wait("location.pathname==='/data/post-training-collection/02602'&&document.querySelectorAll('.dc-processing-table tbody tr').length===2");
    const partial=(await get('/processing/tasks?collection=02602')).tasks.find(t=>t.name==='仅一条数据质检');check(partial.candidate_count===1,'部分数据范围未扩大为整个采集任务');
    await nav('/data/processing-tasks?linked='+partial.id);await wait("!!document.querySelector('#drawerProcessingTaskForm [data-job-action=publish]')");await click('#drawerProcessingTaskForm [data-job-action=publish]');await click('[data-confirm-action]');await wait("document.querySelector('#drawerProcessingTaskForm').dataset.taskStatus==='published'");
    await nav(base+'/02602#processing');check(await ev("document.querySelector('.dc-processing-summary').textContent.includes('涉及数据11')"),'多个任务覆盖同一数据按唯一Recording去重');await shot('10-partial-scope');
    await nav('/data/processing-tasks');await wait("document.querySelectorAll('#dpr-processing-task-table tbody tr[data-collection-processing]').length===2");check(await ev("document.querySelectorAll('#dpr-processing-task-table tbody tr[data-collection-processing]').length===2&&document.querySelectorAll('#dpr-processing-task-table tbody tr:not([data-collection-processing])').length>0"),'处理任务列表合并展示关联任务并保留原有任务');await shot('11-processing-list');
    await nav('/data/processing-tasks?linked='+partial.id);await wait("document.querySelector('#drawerProcessingTaskForm')?.getAttribute('aria-hidden')==='false'");await size(390,844);check(await ev("document.documentElement.scrollWidth<=innerWidth+1&&getComputedStyle(document.querySelector('.q-sider')).display==='none'"),'390处理任务详情无页面横向溢出且不被侧栏遮挡');await shot('12-job-mobile');
    await size(1440);await nav('/data/processing-tasks?new=1');await wait("document.querySelector('#drawerProcessingTaskForm').getAttribute('aria-hidden')==='false'");
    await click('[data-task-pane=filter]');await click('[data-filter-group=basic] .dpr-filter-add-bottom');
    await fill('#processingTaskBasicFilters .dpr-task-filter-field','采集任务 ID');await fill('#processingTaskBasicFilters .dpr-task-filter-value','02602');
    check(await ev("document.querySelector('#drawerProcessingTaskForm').dataset.collectionSource==='02602'&&document.querySelector('#processingTaskProject').value==='亮剑'"),'独立创建通过原筛选条件指定采集任务，不额外增加来源字段');
    await fill('#processingTaskName','人工质检和标注配置');await click('[data-task-pane=flow]');await click('[data-toggle-stage="质检"]');await fill('[data-flow-stage="质检"]','双轮人工质检流程');await click('[data-toggle-stage="标注"]');await fill('[data-flow-stage="标注"]','双轮人工标注流程');
    await click('#processingTaskDrawerSubmit');await wait("location.pathname==='/data/post-training-collection/02602'&&document.querySelectorAll('.dc-processing-table tbody tr').length===3");
    const human=(await get('/processing/tasks?collection=02602')).tasks.find(t=>t.name==='人工质检和标注配置');check(Object.keys(human.stages).length===2&&Object.keys(human.configs['质检']).length===2&&Object.keys(human.configs['标注']).length===2,'人工质检与标注配置跨环节切换后均完整保存');
    await nav('/data/processing-tasks');await wait("document.querySelector('#dpr-processing-task-table tbody tr[data-collection-processing=\""+human.id+"\"]')");await click('[data-collection-processing="'+human.id+'"] .dpr-task-actions button:nth-child(3)');await wait("document.querySelector('#processingTaskDrawerTitle').textContent==='编辑处理任务'");await fill('#processingTaskName','人工质检和标注配置（调整）');await click('#processingTaskDrawerSubmit');await wait("location.pathname==='/data/post-training-collection/02602'");check((await get('/processing/tasks/'+human.id)).task.name==='人工质检和标注配置（调整）','未发布处理任务可回到原配置页修改，保存不重复创建');
    await nav('/data/processing-tasks?collection=02602&new=1');await wait("!!document.querySelector('#drawerProcessingTaskForm').dataset.collectionSource");await size(390,844);check(await ev("document.querySelector('#processingTaskExpectedValueField').hidden&&getComputedStyle(document.querySelector('#processingTaskExpectedValueField')).display==='none'"),'持续任务隐藏固定任务量输入');check(await ev("document.querySelector('.dpr-processing-task-page').getBoundingClientRect().left===0&&getComputedStyle(document.querySelector('.q-sider')).display==='none'"),'390连续创建不被公共侧栏遮挡');await shot('13-create-mobile');
    check(errors.filter(e=>!e.includes('CodeMirror is not defined')).length===0,'新链路无未捕获浏览器异常');
    fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify({passed:checks.length,checks,errors,note:'5063独立临时SQLite与空Chrome profile；不修改5046展示库或生产数据。'},null,2));console.log(JSON.stringify({passed:checks.length,out}));
  }finally{socket?.close();chrome?.kill();service.kill()}
}
main().catch(e=>{console.error(e);process.exitCode=1});
