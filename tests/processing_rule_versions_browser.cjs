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
  const ev=async expression=>{const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error((r.exceptionDetails.exception?.description||r.exceptionDetails.text)+' :: '+expression);return r.result.value;};
  const wait=async expression=>{for(let i=0;i<100;i++){if(await ev(expression))return;await delay(100);}throw Error('Timeout '+expression+' '+await ev('location.href')+' errors='+errors.join(';')+' state='+JSON.stringify(await ev("({project:document.querySelector('#processingTaskProject')?.value,rules:(window.DPR_INLINE_RULES||[]).map(r=>r.value),options:[...document.querySelectorAll('.dpr-node-rule-select option')].map(o=>o.value)})")));};
  const click=selector=>ev(`(()=>{const el=document.querySelector(${JSON.stringify(selector)});if(!el)throw Error('Missing '+${JSON.stringify(selector)});const menu=el.closest('[popover]');if(menu&&!menu.matches(':popover-open'))menu.previousElementSibling.click();el.click();})()`);
  const fill=(selector,value)=>ev(`(()=>{const el=document.querySelector(${JSON.stringify(selector)});el.value=${JSON.stringify(value)};el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  const oldNav=async url=>{await call('Page.navigate',{url:origin+url});await wait(url.startsWith('/data/tasks/')?"!!document.querySelector('.dpr-record-table')":url.startsWith('/data/processing-tasks')?"!!document.querySelector('#dc-processing-confirm')&&document.querySelectorAll('[data-collection-processing]').length>0":"document.querySelector('#dc-app')?.getAttribute('aria-busy')==='false'");};
  const check=async(expression,label)=>{assert.ok(await ev(expression),label);checks.push(label);};
  const shot=async name=>{await delay(120);const r=await call('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(r.data,'base64'));};
  await call('Page.enable');await call('Page.addScriptToEvaluateOnNewDocument',{source:'window.confirm = () => true;'});
  await call('Runtime.enable');await call('Emulation.setFocusEmulationEnabled',{enabled:true});await call('Network.enable');await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*']});await call('Emulation.setDeviceMetricsOverride',{width:1440,height:960,deviceScaleFactor:1,mobile:false});


  const nav=async path=>{await call('Page.navigate',{url:origin+path});await wait("!!document.querySelector('#drawerRuleCreate')&&document.querySelector('#drawerRuleCreate').dataset.versionsReady==='true'");};
  const apiCall=async(path,method='GET',body)=>ev(`fetch(${JSON.stringify(path)},{method:${JSON.stringify(method)},headers:{'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID()},${body?'body:'+JSON.stringify(JSON.stringify(body))+',':''}}).then(async r=>({status:r.status,body:await r.json()}))`);
  await nav('/data/rules');
  await click('[data-rule-id="RL-009"][onclick*="openRuleDetail"]');await wait("!!document.querySelector('#ruleHistoryVersion')");
  await check("!document.querySelector('#ruleVersionChanges')&&document.querySelector('#ruleVersionPanel').getBoundingClientRect().height<115&&document.querySelector('#ruleVersionMeta').textContent.includes('发布人')",'版本栏只保留发布信息，不展示本次变更摘要');
  await shot('00-legacy-version-header');
  await click('[data-open-rule-records="events"]');await check("document.querySelector('#ruleRecordsDialog').open&&document.querySelector('#ruleRecordsEvents').textContent.includes('暂无操作记录')",'历史规则无日志时准确展示空状态');
  await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await wait("!document.querySelector('#ruleRecordsDialog').open");
  await check("document.querySelector('#drawerRuleCreate.active')&&document.activeElement.dataset.openRuleRecords==='events'",'Esc仅关闭记录弹窗，保留规则详情并恢复焦点');await ev("closeDrawer()");
  const body={name:'杯子抓取质检标准',project:'亮剑',stage:'质检',rule_type:'质检',quality_mistakes:['动作未完成','物体滑落','发生碰撞'],quality_unqualified:['画面遮挡','轨迹缺失'],error_reasons:[{name:'结论不准确'}],publish:true};
  let response=await apiCall('/api/processing-rules','POST',body);assert.equal(response.status,201);const ruleId=response.body.rule.id;
  const trigger=`[data-rule-id="${ruleId}"]`;
  const taskBody={name:'规则更新自动同步验证',source_ids:['02602'],filters:[['采集任务 ID','等于','02602']],stages:{质检:'双轮人工质检流程'},configs:{质检:{质检:{rule:'rule:'+ruleId+'@1',assignments:[{type:'supplier',target:'光轮智能'}]},抽检:{rule:'rule:'+ruleId+'@1',assignments:[{type:'supplier',target:'光轮智能'}]}}}};
  let linkedTask=(await apiCall('/api/post-training-collection/processing/tasks','POST',taskBody)).body.task;
  linkedTask=(await apiCall('/api/post-training-collection/processing/tasks/'+linkedTask.id+'/action','POST',{action:'publish',revision:linkedTask.revision})).body.task;
  await nav('/data/rules');
  await check(`!document.querySelector('${trigger}[onclick*="ruleUpdate"]')&&!document.querySelector('${trigger}[onclick*="rulePublish"]')`,'已发布规则无编辑或发布新版入口');
  response=await apiCall('/api/processing-rules/'+ruleId+'/revisions','POST',{...body,revision:response.body.rule.revision,quality_mistakes:['新标准']});
  assert.equal(response.status,403);checks.push('已发布规则修改被拒绝');
  const linkedAfter=(await apiCall('/api/post-training-collection/processing/tasks/'+linkedTask.id)).body.task;
  assert.equal(linkedAfter.configs['质检']['质检'].rule,'rule:'+ruleId+'@1');checks.push('关联任务保持原规则');
  await click(trigger+'[onclick*="openRuleDetail"]');await wait("!!document.querySelector('#ruleHistoryVersion')&&!document.querySelector('#ruleVersionPanel').hidden");
  await check("document.querySelector('#ruleHistoryVersion').textContent==='V1'&&document.querySelector('#ruleCreateName').disabled",'已发布规则详情只读');
  await click('[data-open-rule-records="versions"]');await check("document.querySelector('#ruleRecordsDialog').open&&document.querySelector('#ruleRecordsDialog').textContent.includes('V1')",'版本记录仍可查看');
  await click('#ruleRecordsDialog [data-close-rule-records]');await ev('closeDrawer()');
  await click(trigger+'[onclick*="ruleCopy"]');await wait("document.querySelector('#ruleCreateName').value.endsWith(' - 副本')&&!document.querySelector('#rulePublishUse').disabled");
  await check("!document.querySelector('#ruleCreateName').disabled&&document.querySelectorAll('#ruleMistakeRows tr').length===3",'复制规则保留内容并允许编辑');
  await click('#rulePublishUse');await wait("document.querySelector('#drawerRuleCreate')?.dataset.versionsReady==='true'&&!document.querySelector('#drawerRuleCreate.active')");
  await check("[...document.querySelectorAll('.rule-management-table tbody tr')].some(row=>row.textContent.includes('杯子抓取质检标准 - 副本')&&row.textContent.includes('未发布'))",'复制为独立未发布规则');
  await nav('/data/rules');
  await ev("document.fonts.ready");
  await check("document.documentElement.scrollWidth<=innerWidth+1",'页面不横向溢出');
  await check("document.querySelector('.rule-management-wrap').scrollWidth<=document.querySelector('.rule-management-wrap').clientWidth+1",'1440桌面整表无需左右滚动');
  await check("[...document.querySelectorAll('.rule-management-table tbody tr')].every(row=>[9,10,11].every(index=>{const cell=row.querySelector('td:nth-child('+index+')');return !cell||cell.scrollWidth<=cell.clientWidth+1}))",'1440桌面创建人、日期和操作完整展示');
  await check("getComputedStyle(document.querySelector('.rule-management-table')).fontFamily===getComputedStyle(document.body).fontFamily",'规则表沿用页面正文字体');
  await check("[...document.querySelectorAll('.actions-cell')].every(cell=>[...cell.querySelectorAll(':scope > a,:scope > .action-more > a')].map(a=>a.textContent.trim()).join('|')==='详情|⋯ 更多')",'公开操作保持详情、更多，复制和编辑收入菜单');
  await ev(`ruleOpenMenu(document.querySelector(${JSON.stringify(trigger)}).closest('tr').querySelector('[aria-haspopup="menu"]'))`);
  await check("document.querySelector('.rule-overflow-menu:popover-open')?.getBoundingClientRect().right<=innerWidth",'更多菜单不受滚动容器裁切');
  await shot('04-rule-list');
  await ev("document.querySelector('.rule-overflow-menu:popover-open').hidePopover()");
  await call('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
  await check("document.documentElement.scrollWidth<=innerWidth+1",'1920桌面列表不横向溢出');
  await check("document.querySelector('.rule-management-wrap').scrollWidth<=document.querySelector('.rule-management-wrap').clientWidth+1",'1920桌面表格完整展示无多余横滚');
  await shot('05-rule-list-1920');
  assert.deepEqual(errors,[]);checks.push('无浏览器异常');
  fs.writeFileSync(path.join(out,'versions-browser-report.json'),JSON.stringify({checks,passed:checks.length,errors},null,2));console.log(JSON.stringify({passed:checks.length,out}));
}
main().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>{socket?.close();chrome?.kill();if(service?.pid&&process.platform==='win32')spawnSync('taskkill',['/PID',String(service.pid),'/T','/F'],{stdio:'ignore',windowsHide:true});else service?.kill();});
