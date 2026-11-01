/* Collection-processing integration on a temporary database and a fresh Chrome profile. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{spawn,spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),python=path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const out=path.resolve(process.env.EVIDENCE_DIR||path.join(root,'instance/collection-unified-regression'));
const testPort=Number(process.env.RULE_TEST_PORT||5087),debugPort=Number(process.env.RULE_DEBUG_PORT||9437);
const origin='http://127.0.0.1:'+testPort,base='/data/post-training-collection',api='/api/post-training-collection';
const delay=ms=>new Promise(r=>setTimeout(r,ms)),checks=[];let service,chrome,socket;
const http=require('node:http');
function getJson(url){return new Promise((resolve,reject)=>{http.get(url,response=>{let data='';response.setEncoding('utf8');response.on('data',chunk=>data+=chunk);response.on('end',()=>{try{resolve(JSON.parse(data));}catch(error){reject(error);}});}).on('error',reject);});}
async function main(){
  fs.mkdirSync(out,{recursive:true});const sandbox=fs.mkdtempSync(path.join(out,'isolated-'));
  const env={...process.env,COLLECTION_DEMO_DB:path.join(sandbox,'collection.sqlite3'),PYTHONIOENCODING:'utf-8'};
  // Start with an empty database: deployed demos must show links without a seed command.
  service=spawn(python,['-c',`from toolchain_demo import app; app.config['PROCESSING_RULE_PERMISSIONS']={'create':${process.env.RULE_PERMISSION_CASE==='no-create'?'False':'True'},'publish':${process.env.RULE_PERMISSION_CASE==='no-publish'?'False':'True'}}; app.run(host='127.0.0.1',port=${testPort},debug=False,use_reloader=False)`],{cwd:root,env,stdio:'ignore',windowsHide:true});
  for(let i=0;i<100;i++){try{if((await getJson(origin+api+'/tasks')).tasks)break;}catch{}await delay(100);}
  chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless','--disable-gpu','--no-first-run','--disable-extensions','--no-default-browser-check','--user-data-dir='+path.join(sandbox,'chrome'),'--remote-debugging-port='+debugPort,'about:blank'],{stdio:'ignore',windowsHide:true});
  let page;for(let i=0;i<100;i++){try{page=(await getJson('http://127.0.0.1:'+debugPort+'/json/list')).find(p=>p.type==='page');if(page)break;}catch{}await delay(100);}assert.ok(page);
  socket=new WebSocket(page.webSocketDebuggerUrl);let id=0;const pending=new Map(),errors=[];
  socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Page.javascriptDialogOpening')socket.send(JSON.stringify({id:++id,method:'Page.handleJavaScriptDialog',params:{accept:true}}));if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);};
  await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
  const call=(method,params={})=>new Promise((resolve,reject)=>{const key=++id,timer=setTimeout(()=>reject(Error(method+' '+(params.expression||''))),20000);pending.set(key,{resolve,reject,timer});socket.send(JSON.stringify({id:key,method,params}));});
  const ev=async expression=>{const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;};
  const wait=async expression=>{for(let i=0;i<100;i++){if(await ev(expression))return;await delay(100);}throw Error('Timeout '+expression+' '+await ev('location.href'));};
  const click=selector=>ev(`(()=>{const el=document.querySelector(${JSON.stringify(selector)});if(!el)throw Error('Missing '+${JSON.stringify(selector)});el.click();})()`);
  const fill=(selector,value)=>ev(`(()=>{const el=document.querySelector(${JSON.stringify(selector)});el.value=${JSON.stringify(value)};el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  const oldNav=async url=>{await call('Page.navigate',{url:origin+url});await wait(url.startsWith('/data/tasks/')?"!!document.querySelector('.dpr-record-table')":url.startsWith('/data/processing-tasks')?"!!document.querySelector('#dc-processing-confirm')&&document.querySelectorAll('[data-collection-processing]').length>0":"document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'");};
  const check=async(expression,label)=>{assert.ok(await ev(expression),label);checks.push(label);};
  const shot=async name=>{await delay(120);const r=await call('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(r.data,'base64'));};
  await call('Page.enable');await call('Page.addScriptToEvaluateOnNewDocument',{source:'window.confirm = () => true;'});
  await call('Runtime.enable');await call('Emulation.setFocusEmulationEnabled',{enabled:true});await call('Network.enable');await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*']});await call('Emulation.setDeviceMetricsOverride',{width:1440,height:960,deviceScaleFactor:1,mobile:false});

  const nav=async url=>{await call('Page.navigate',{url:origin+url});await wait("!!document.querySelector('#drawerProcessingTaskForm')&&!!window.DPR_INLINE_RULES");};
  const enableQuality=async()=>{await wait("document.querySelector('#drawerProcessingTaskForm').dataset.mode==='new'");await click('[data-toggle-stage="质检"]');await wait("!!document.querySelector('.dpr-inline-rule-create')");};
  const completeQuality=async name=>{await fill('#ruleCreateName',name);await fill('#ruleMistakeRows .rule-quality-value','未完成动作');await fill('#ruleUnqualifiedRows .rule-quality-value','画面不完整');await fill('#ruleErrorReasonRows .rule-error-name','判断错误');};
  await nav('/data/processing-tasks?collection=02602&new=1');
  await wait("document.querySelector('#processingTaskProject').disabled&&document.querySelector('#processingTaskName').value.includes('_处理任务')");

  if(process.env.RULE_PERMISSION_CASE){
    await click('[data-toggle-stage="质检"]');await delay(300);
    await check("!document.querySelector('.dpr-inline-rule-create')",'无创建或发布权限时不显示任务内新建入口');
    await check("fetch('/api/processing-rules',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:'亮剑',publish:true})}).then(r=>r.status===403)",'直接请求创建接口仍拒绝越权');
    assert.deepEqual(errors,[]);console.log(JSON.stringify({permissionCase:process.env.RULE_PERMISSION_CASE,passed:checks.length}));return;
  }
  await fill('#processingTaskName','规则抽屉保留任务名');await enableQuality();
  await ev("document.querySelectorAll('.dpr-flow-node-card')[0].querySelector('.dpr-node-percent-input')?.setAttribute('value','83')");
  const before=await ev("[...document.querySelectorAll('.dpr-node-rule-select')].map(s=>s.value)");
  assert.ok(before.length>0&&before.every(value=>value===''));checks.push('新建处理任务的规则默认留空');
  await check("document.querySelector('.dpr-node-rule-select').selectedOptions[0].textContent==='请选择规则'&&!dprProcessingAssignmentsValid()",'显示请选择规则，未选择时节点配置不通过校验');
  await click('.dpr-inline-rule-create');await wait("!!document.querySelector('#drawerRuleCreate.active')&&!!window.inlineRuleContext&&!document.querySelector('#rulePublishUse').disabled");
  await check("document.querySelector('#ruleCreateProject').disabled&&document.querySelector('#ruleCreateStage').disabled&&document.querySelector('#ruleCreateStage').value==='质检'&&!document.querySelector('#ruleCreateType').disabled",'当前项目/环节锁定，规则类型可选');
  await check("[...document.querySelector('#ruleCreateType').options].map(o=>o.value).join(',')==='质检'",'质检节点只提供质检规则类型');
  await check("document.querySelector('#drawerProcessingTaskForm').inert&&document.querySelector('#rulePublishUse').textContent==='发布并使用'",'抽屉隔离背景，发布动作明确');

  await completeQuality('桌面连续创建质检规则');await shot('inline-rule-drawer');
  await click('#rulePublishUse');await wait("!window.inlineRuleContext&&!document.querySelector('#drawerRuleCreate.active')");
  const selected=await ev("document.querySelector('.dpr-node-rule-select').value");assert.ok(selected.startsWith('rule:'));
  await check("document.querySelector('#processingTaskName').value==='规则抽屉保留任务名'&&!document.querySelector('#drawerProcessingTaskForm').inert",'创建规则后原任务输入保留，背景恢复');
  assert.deepEqual(await ev("[...document.querySelectorAll('.dpr-node-rule-select')].slice(1).map(s=>s.value)"),before.slice(1),'只回填发起节点');checks.push('只回填发起节点');
  await click('.dpr-inline-rule-create');await wait("!!window.inlineRuleContext&&!document.querySelector('#rulePublishUse').disabled");
  await fill('#ruleCreateName','桌面连续创建质检规则');
  await wait("!document.querySelector('#ruleNameError').hidden");
  await check("document.querySelector('#ruleCreateName').getAttribute('aria-invalid')==='true'&&document.querySelector('#ruleNameError').textContent.includes('同名')",'任务内新建规则填写后即时提示重名，无需提交');
  await shot('inline-duplicate-name');
  await check("!document.querySelector('#ruleDrawerSubmit')",'任务内新建规则不提供保存草稿或保存未发布入口');
  await completeQuality('取消不应入库');await click('#drawerRuleCreate .drawer-foot .btn');await wait("!window.inlineRuleContext");
  assert.equal(await ev("document.querySelector('.dpr-node-rule-select').value"),selected);checks.push('取消未发布修改不覆盖节点选择');
  await click('.dpr-inline-rule-create');await wait("!!window.inlineRuleContext&&!document.querySelector('#rulePublishUse').disabled");await fill('#ruleCreateName','取消不应入库');await click('#drawerRuleCreate .drawer-foot .btn');await wait("!window.inlineRuleContext");
  await check("document.querySelector('.dpr-node-rule-select').value.startsWith('rule:')&&document.querySelector('#processingTaskName').value==='规则抽屉保留任务名'",'取消不改变节点和任务输入');
  await click('.dpr-inline-rule-create');await wait("!!window.inlineRuleContext&&!document.querySelector('#rulePublishUse').disabled");
  await completeQuality('桌面连续创建质检规则');await wait("!document.querySelector('#ruleNameError').hidden");await click('#rulePublishUse');
  await check("document.querySelector('#drawerRuleCreate').classList.contains('active')&&document.querySelector('#ruleCreateName').value==='桌面连续创建质检规则'&&!document.querySelector('#rulePublishUse').disabled&&document.querySelector('#ruleNameError').textContent.includes('同名')",'同名规则阻止提交，保留输入并允许改名重试');
  await fill('#ruleCreateName','失败后修改重试');await click('#rulePublishUse');await wait("!window.inlineRuleContext");
  await check("fetch('/api/post-training-collection/processing/tasks').then(r=>r.json()).then(d=>!d.tasks.some(t=>t.name==='规则抽屉保留任务名'))",'规则先保存，尚未生成处理任务');
  const ruleValue=await ev("document.querySelector('.dpr-node-rule-select').value");
  await check("[...document.querySelectorAll('.dpr-node-rule-select option')].every(o=>!o.textContent.includes('通用动作标注规则')&&!o.textContent.includes('端到端切分标注规则'))",'质检节点规则列表不显示标注规则');
  await ev("DPR_ENABLED_FLOW_STAGES['标注']=true;dprShowAssignmentsForStage('标注');dprShowAssignmentsForStage('质检');DPR_ENABLED_FLOW_STAGES['标注']=false");
  await check(`document.querySelector('.dpr-node-rule-select').value===${JSON.stringify(ruleValue)}&&[...document.querySelectorAll('.dpr-node-rule-select')].slice(1).every(s=>s.value==='')`,'切换环节保留新规则，其他节点继续留空');
  // Complete the remaining required node rules explicitly before creating the task.
  await ev("document.querySelectorAll('.dpr-node-rule-select').forEach(s=>{if(!s.value){s.value=[...s.options].find(o=>o.value&&!o.disabled).value;s.dispatchEvent(new Event('change',{bubbles:true}));}})");
  await click('[data-task-pane=flow]');await click('#processingTaskDrawerSubmit');
  await wait("location.search.includes('processing_created=')");
  await check(`fetch('/api/post-training-collection/processing/tasks?collection=02602').then(r=>r.json()).then(d=>d.tasks.some(t=>t.name==='规则抽屉保留任务名'&&Object.values(t.configs['质检']).some(c=>c.rule===${JSON.stringify(ruleValue)}&&c.rule_identity?.name==='失败后修改重试')))`,'快捷创建的规则以稳定ID和可读身份保存到处理任务');
  await call('Page.navigate',{url:origin+'/data/rules'});await wait("!!window.rulePersist&&!!document.querySelector('#ruleFilterName')");
  await check("document.querySelector('tbody').textContent.includes('桌面连续创建质检规则')&&document.querySelector('tbody').textContent.includes('失败后修改重试')&&!document.querySelector('tbody').textContent.includes('取消不应入库')",'任务未创建，成功保存的规则仍在规则管理；取消规则不存在');
  await shot('rule-management-persisted');
  await ev('openRuleCreate()');await wait("!document.querySelector('#rulePublishUse').disabled");
  await fill('#ruleCreateProject','亮剑');await fill('#ruleCreateName','桌面连续创建质检规则');
  await wait("!document.querySelector('#ruleNameError').hidden");
  await check("document.querySelector('#ruleCreateName').getAttribute('aria-invalid')==='true'",'规则管理入口同样检查已发布规则重名');
  await fill('#ruleCreateName','修改名称后不重名');await delay(400);
  await check("document.querySelector('#ruleNameError').hidden&&document.querySelector('#ruleCreateName').getAttribute('aria-invalid')==='false'",'更换名称后清除重名提示');
  await fill('#ruleCreateName','桌面连续创建质检规则');await wait("!document.querySelector('#ruleNameError').hidden");
  await fill('#ruleCreateProject','京东项目');await delay(400);
  await check("document.querySelector('#ruleNameError').hidden",'切换项目后重新检查，不错误拦截其他项目同名');
  await ev('closeDrawer()');
  await nav('/data/processing-tasks?new=1');await fill('#processingTaskProject','demo 项目');await enableQuality();
  await check("[...document.querySelectorAll('.dpr-node-rule-select')].every(s=>s.value==='')",'直接创建处理任务同样默认留空，不沿用上一任务的规则');
  await check("document.querySelector('.dpr-inline-rule-create')?.textContent==='新建规则'",'直接创建处理任务同样提供快捷入口');
  // A fixed/inherited node must not acquire a create entry.
  await ev("DPR_ENABLED_FLOW_STAGES['标注']=true;DPR_SELECTED_FLOWS['标注']='端到端切分标注流程';dprShowAssignmentsForStage('标注')");
  await wait("document.querySelectorAll('.dpr-flow-node-card').length===4");
  await check("[...document.querySelectorAll('.dpr-flow-node-card')].map(c=>!!c.querySelector('.dpr-inline-rule-create')).join(',')==='true,false,false,false'",'固定/继承/无需规则的节点不出现入口');
  await check("[...document.querySelectorAll('.dpr-node-rule-select option')].every(o=>!o.textContent.includes('通用质检规则')&&!o.textContent.includes('桌面连续创建质检规则'))",'标注节点规则列表不显示质检规则');
  await click('.dpr-inline-rule-create');await wait("!!window.inlineRuleContext&&!document.querySelector('#rulePublishUse').disabled");
  await check("document.querySelector('#ruleCreateStage').disabled&&document.querySelector('#ruleCreateStage').value==='标注'&&!document.querySelector('#ruleCreateType').disabled&&document.querySelector('#ruleCreateType').value==='语义标注'&&document.querySelector('#ruleCreateType').options.length===1",'标注节点锁定环节，规则类型可选且符合流程限制');
  await fill('#ruleCreateName','端到端新规则');await fill('#ruleDocumentLink','https://example.com/spec');await fill('#ruleErrorReasonRows .rule-error-name','边界错误');await click('#rulePublishUse');await wait("!window.inlineRuleContext");
  await check("document.querySelector('.dpr-node-rule-select').selectedOptions[0].textContent.includes('端到端新规则')",'语义规则完整创建并自动选用');
  const annotationRule=await ev("document.querySelector('.dpr-node-rule-select').value");
  await ev("DPR_ENABLED_FLOW_STAGES['质检']=true;dprShowAssignmentsForStage('质检')");
  await wait("!!document.querySelector('.dpr-inline-rule-create')");
  await ev(`(()=>{const select=document.querySelector('.dpr-node-rule-select');select.add(new Option('伪造标注规则',${JSON.stringify(annotationRule)}));select.value=${JSON.stringify(annotationRule)};})()`);
  await ev("(async()=>{window.__capturedRuleError='';const original=window.toast;window.toast=message=>{window.__capturedRuleError=message};try{await window.dprSubmitProcessingTask()}finally{window.toast=original}})()");
  await check("window.__capturedRuleError.includes('规则已变化或不可用')",'篡改质检节点为标注规则时提交前拒绝');
  await click('.dpr-inline-rule-create');await wait("!!window.inlineRuleContext&&!document.querySelector('#rulePublishUse').disabled");
  await check("document.querySelector('#ruleCreateStage').disabled&&document.querySelector('#ruleCreateStage').value==='质检'&&!document.querySelector('#ruleCreateType').disabled&&[...document.querySelector('#ruleCreateType').options].map(o=>o.value).join(',')==='质检'",'从标注切回质检后环节锁定、规则类型可选');
  await click('#drawerRuleCreate .drawer-foot .btn');await wait("!window.inlineRuleContext");
  await ev("DPR_SELECTED_FLOWS['标注']='双轮人工标注流程';dprShowAssignmentsForStage('标注')");
  await wait("document.querySelectorAll('.dpr-flow-node-card').length===2&&!!document.querySelector('.dpr-inline-rule-create')");
  await click('.dpr-inline-rule-create');await wait("!!window.inlineRuleContext&&!document.querySelector('#rulePublishUse').disabled");
  await check("document.querySelector('#ruleCreateStage').disabled&&!document.querySelector('#ruleCreateType').disabled&&[...document.querySelector('#ruleCreateType').options].map(o=>o.value).join(',')==='语义标注,动作标注,标签标注'",'双轮标注节点允许选择三种适用规则类型');
  await fill('#ruleCreateType','动作标注');
  await check("document.querySelector('#ruleActionConfig').style.display==='block'&&document.querySelector('#ruleDocumentConfig').style.display==='none'",'选择动作标注后展示对应配置');
  await fill('#ruleCreateName','双轮标注动作规则');
  await fill('.rule-action-element-name','物品');await fill('.rule-action-element-key','item');
  await fill('.rule-enum-value-name','杯子');await fill('.rule-enum-value-key','cup');
  await fill('.rule-action-desc-zh','拿起物品');await fill('#ruleErrorReasonRows .rule-error-name','动作不准确');
  await click('#rulePublishUse');await wait("!window.inlineRuleContext");
  await check("document.querySelector('.dpr-node-rule-select').selectedOptions[0].textContent.includes('双轮标注动作规则')",'手动选择动作标注后可发布并自动引用');
  assert.deepEqual(errors,[]);checks.push('无浏览器未捕获异常');
  fs.writeFileSync(path.join(out,'inline-rule-report.json'),JSON.stringify({checks,passed:checks.length,errors},null,2));console.log(JSON.stringify({passed:checks.length,out}));
}
main().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>{socket?.close();chrome?.kill();if(service?.pid&&process.platform==='win32')spawnSync('taskkill',['/PID',String(service.pid),'/T','/F'],{stdio:'ignore',windowsHide:true});else service?.kill();});
