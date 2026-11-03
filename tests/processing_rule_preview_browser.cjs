/* Version-specific task rule previews, isolated from the user's demo database. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{spawn,spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),python=path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const out=path.resolve(process.env.EVIDENCE_DIR||path.join(root,'instance/rule-preview-regression'));
const testPort=Number(process.env.RULE_TEST_PORT||5112),debugPort=Number(process.env.RULE_DEBUG_PORT||9512),origin='http://127.0.0.1:'+testPort;
const delay=ms=>new Promise(r=>setTimeout(r,ms)),checks=[];let service,chrome,socket;
const http=require('node:http');
const request=(url,method='GET',body)=>new Promise((resolve,reject)=>{const data=body===undefined?undefined:JSON.stringify(body);const req=http.request(url,{method,agent:false,headers:{'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID(),...(data?{'Content-Length':Buffer.byteLength(data)}:{})}},r=>{let text='';r.setEncoding('utf8');r.on('data',c=>text+=c);r.on('end',()=>{try{resolve({status:r.statusCode,ok:r.statusCode<400,body:JSON.parse(text)})}catch(e){reject(e)}});});req.on('error',reject);req.end(data);});
async function main(){
  fs.mkdirSync(out,{recursive:true});const sandbox=fs.mkdtempSync(path.join(out,'isolated-'));
  service=spawn(python,['-c',`from toolchain_demo import app; app.run(host='127.0.0.1',port=${testPort},debug=False,use_reloader=False)`],{cwd:root,env:{...process.env,COLLECTION_DEMO_DB:path.join(sandbox,'collection.sqlite3'),PYTHONIOENCODING:'utf-8'},stdio:'ignore',windowsHide:true});
  for(let i=0;i<100;i++){try{if((await request(origin+'/api/post-training-collection/tasks')).ok)break;}catch{}await delay(100);}
  chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless','--disable-gpu','--no-first-run','--disable-extensions','--no-default-browser-check','--user-data-dir='+path.join(sandbox,'chrome'),'--remote-debugging-port='+debugPort,'about:blank'],{stdio:'ignore',windowsHide:true});
  let page;for(let i=0;i<100;i++){try{page=(await request('http://127.0.0.1:'+debugPort+'/json/list')).body.find(p=>p.type==='page');if(page)break;}catch{}await delay(100);}assert.ok(page);
  socket=new WebSocket(page.webSocketDebuggerUrl);let id=0;const pending=new Map(),errors=[];
  socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);};
  await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
  const call=(method,params={})=>new Promise((resolve,reject)=>{const key=++id,timer=setTimeout(()=>reject(Error(method)),20000);pending.set(key,{resolve,reject,timer});socket.send(JSON.stringify({id:key,method,params}));});
  const ev=async expression=>{const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;};
  const wait=async expression=>{for(let i=0;i<100;i++){if(await ev(expression))return;await delay(100);}throw Error('Timeout '+expression);};
  const click=selector=>ev(`document.querySelector(${JSON.stringify(selector)}).click()`);
  const fill=(selector,value)=>ev(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  const check=async(expression,label)=>{assert.ok(await ev(expression),label);checks.push(label);};
  const previewContent="(document.querySelector('.dpr-rule-preview-body').textContent+' '+[...document.querySelectorAll('.dpr-rule-preview-body input,.dpr-rule-preview-body textarea')].map(e=>e.value).join(' '))";
  const shot=async name=>{await delay(150);const r=await call('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(r.data,'base64'));};
  const api=async(url,method='GET',body)=>{const r=await request(origin+url,method,body);assert.ok(r.ok,JSON.stringify(r.body));return r.body;};
  const nav=async query=>{await call('Page.navigate',{url:origin+'/data/processing-tasks'+query});await wait("!!document.querySelector('#processingRulePreview')&&document.querySelectorAll('[data-collection-processing]').length>0");};
  await call('Page.enable');await call('Runtime.enable');await call('Network.enable');await call('Network.setBlockedURLs',{urls:['https://cdn.jsdelivr.net/*']});await call('Emulation.setDeviceMetricsOverride',{width:1440,height:960,deviceScaleFactor:1,mobile:false});
  // The shipped examples must be usable without first creating test-only rules.
  const seeded=(await api('/api/post-training-collection/processing/tasks')).tasks;
  for(const name of ['杯子抓取首批复核','杯子抓取补采复核','杯子抓取动作标注','饮料取放质检与标注','饮茶动作语义标注']){
    const task=seeded.find(t=>t.name===name);assert.ok(task,name);
    for(const [stage,nodes] of Object.entries(task.configs))for(const node of Object.keys(nodes)){
      const r=await api('/api/processing-rules/preview?'+new URLSearchParams({task_id:task.id,stage,node}));
      assert.ok(r.rule.name&&r.rule.version,JSON.stringify(r));
    }
    checks.push('内置示例规则内容可读：'+name);
  }
  for(const [value,stage] of [['通用质检规则 v3','质检'],['自动化质检规则 v2','质检'],['DAgger 质检规则 v1','质检'],['通用动作标注规则 v3','标注']]){
    const r=await api('/api/processing-rules/preview?'+new URLSearchParams({value,stage,project:'预训练采集'}));
    assert.ok(r.rule.name&&r.rule.version);checks.push('原页面示例可预览：'+value);
  }
  const fixtureScreens=[['杯子抓取首批复核','质检','07-example-quality-v1'],['杯子抓取补采复核','质检','08-example-quality-v2'],['杯子抓取动作标注','标注','09-example-action'],['饮料取放质检与标注','标注','10-example-tags'],['饮茶动作语义标注','标注','11-example-semantic']];
  for(const [name,stage,file] of fixtureScreens){
    const task=seeded.find(t=>t.name===name);await nav('?linked='+task.id);
    await wait("document.querySelector('#drawerProcessingTaskForm').dataset.mode==='detail'");await click('[data-task-pane="flow"]');
    await ev(`window.dprShowAssignmentsForStage(${JSON.stringify(stage)})`);
    await wait("!!document.querySelector('.dpr-rule-preview-trigger')&&!document.querySelector('.dpr-rule-preview-trigger').disabled");
    await click('.dpr-rule-preview-trigger');await wait("document.querySelector('#processingRulePreviewTitle').textContent!=='规则预览'&&document.querySelector('#processingRulePreview').open");
    const expectedTitles=Object.values(task.configs[stage]).map(c=>c.rule_identity).filter(Boolean).map(r=>r.name+' · '+r.version.toUpperCase());
    await check(`${JSON.stringify(expectedTitles)}.includes(document.querySelector('#processingRulePreviewTitle').textContent)&&!document.querySelector('.dpr-rule-preview-body').textContent.includes('暂不可用')`,'示例详情预览：'+name);await shot(file);await click('[data-preview-close]');
  }
  const body={name:'杯子抓取质检标准',project:'亮剑',stage:'质检',rule_type:'质检',quality_mistakes:['动作未完成'],quality_unqualified:['画面遮挡'],error_reasons:[{name:'结论不准确'}],publish:true};
  const v1=(await api('/api/processing-rules','POST',body)).rule;
  const jobBody=rule=>({name:'杯子抓取首批质检',source_ids:['02602'],filters:[['采集任务 ID','等于','02602']],stages:{质检:'双轮人工质检流程'},configs:{质检:{质检:{rule,assignments:[{type:'supplier',target:'光轮智能'}]},抽检:{rule,assignments:[{type:'supplier',target:'光轮智能'}]}}}});
  const a=(await api('/api/post-training-collection/processing/tasks','POST',jobBody(v1.value))).task;
  await api('/api/post-training-collection/processing/tasks/'+a.id+'/action','POST',{action:'publish',revision:a.revision});
  const v2=(await api('/api/processing-rules/'+v1.id+'/revisions','POST',{...body,revision:v1.revision,quality_mistakes:['动作未完成','出现碰撞']})).rule;
  const b=(await api('/api/post-training-collection/processing/tasks','POST',{...jobBody(v2.value),name:'杯子抓取补采质检'})).task;
  await nav('?collection=02602&new=1');await wait("document.querySelector('#processingTaskName').value.includes('_处理任务')");
  await fill('#processingTaskName','预览后保留任务名称');await click('[data-task-pane="flow"]');await click('[data-toggle-stage="质检"]');
  await fill('[data-flow-stage="质检"]','双轮人工质检流程');await wait(`!!document.querySelector('.dpr-node-rule-select option[value="${v2.value}"]')`);
  await check("document.querySelector('.dpr-rule-preview-trigger').disabled",'未选规则时预览禁用');
  await fill('.dpr-node-rule-select',v2.value);await click('.dpr-rule-preview-trigger');await wait("document.querySelector('#processingRulePreviewTitle').textContent.endsWith('V2')");
  await check(`${previewContent}.includes('出现碰撞')&&[...document.querySelectorAll('#processingRulePreview input,#processingRulePreview select,#processingRulePreview textarea')].every(e=>e.disabled)`,'创建时预览所选V2完整只读内容');
  await shot('01-create-preview-v2');await ev("document.querySelector('#processingRulePreview').dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))");await wait("!document.querySelector('#processingRulePreview').open");
  await check("document.querySelector('#processingTaskName').value==='预览后保留任务名称'&&document.querySelector('.dpr-node-rule-select').value.includes('@2')&&document.activeElement.classList.contains('dpr-rule-preview-trigger')",'关闭后任务输入与规则选择保留，焦点返回');
  // A transient failure must not show previous content; retry loads the same selection.
  await ev("window.previewFetch=window.fetch;window.fetch=(url,...args)=>{if(String(url).startsWith('/api/processing-rules/preview')){window.fetch=window.previewFetch;return Promise.reject(Error('网络暂时不可用'))}return window.previewFetch(url,...args)}");
  await click('.dpr-rule-preview-trigger');await wait("!!document.querySelector('[data-preview-retry]')");
  await check(`!${previewContent}.includes('出现碰撞')`,'读取失败不显示上次规则正文');
  await click('[data-preview-retry]');await wait(`${previewContent}.includes('出现碰撞')`);checks.push('失败重试成功且不丢任务输入');await click('[data-preview-close]');
  await nav('?linked='+a.id);await wait("document.querySelector('#drawerProcessingTaskForm').dataset.mode==='detail'");await click('[data-task-pane="flow"]');await wait("!!document.querySelector('.dpr-rule-preview-trigger')&&!document.querySelector('.dpr-rule-preview-trigger').disabled");
  await click('.dpr-rule-preview-trigger');await wait("document.querySelector('#processingRulePreviewTitle').textContent.endsWith('V2')");
  await check(`${previewContent}.includes('出现碰撞')`,'规则升V2后关联任务预览最新正文');await shot('02-task-a-preview-v2');await click('[data-preview-close]');
  await nav('?linked='+b.id);await wait("document.querySelector('#drawerProcessingTaskForm').dataset.mode==='detail'");await click('[data-task-pane="flow"]');await wait("!!document.querySelector('.dpr-rule-preview-trigger')&&!document.querySelector('.dpr-rule-preview-trigger').disabled");
  await click('.dpr-rule-preview-trigger');await wait("document.querySelector('#processingRulePreviewTitle').textContent.endsWith('V2')");await check(`${previewContent}.includes('出现碰撞')`,'新任务详情预览V2正文');await shot('03-task-b-preview-v2');await click('[data-preview-close]');
  await api('/data/rules/'+v1.id+'/status','POST',{status:'disabled'});
  await click('.dpr-rule-preview-trigger');await wait("document.querySelector('#processingRulePreviewTitle').textContent.endsWith('V2')");checks.push('规则停用后原任务仍能预览所绑定内容');await click('[data-preview-close]');
  const semantic=(await api('/api/processing-rules','POST',{...body,name:'饮茶动作说明',stage:'标注',rule_type:'语义标注',semantic_mode:'link',document_link:'https://nwd4iy9rd2s.feishu.cn/wiki/R1yZwxGaFiTs34koqYDcoKPmnk2'})).rule;
  await nav('?collection=02602&new=1');await wait("document.querySelector('#drawerProcessingTaskForm').dataset.mode==='new'&&document.querySelector('#processingTaskName').value.includes('_处理任务')&&document.querySelector('#processingTaskProject').value==='亮剑'");await click('[data-task-pane="flow"]');await click('[data-toggle-stage="标注"]');
  await fill('[data-flow-stage="标注"]','端到端切分标注流程');await wait(`!!document.querySelector('.dpr-node-rule-select option[value="${semantic.value}"]')`);await fill('.dpr-node-rule-select',semantic.value);
  await click('.dpr-rule-preview-trigger');await wait("!!document.querySelector('#processingRulePreview #ruleDocumentOpen:not([hidden])')");
  await check("document.querySelector('#ruleDocumentOpen').target==='_blank'&&document.querySelector('#ruleDocumentOpen').rel.includes('noopener')",'飞书链接预览只显示绑定链接并可打开原文');await shot('04-semantic-link-preview');await click('[data-preview-close]');
  await check("[...document.querySelectorAll('.dpr-flow-node-card')].filter(c=>c.querySelector('.dpr-flow-inherit-note')?.textContent.startsWith('继承前序节点')).every(c=>!c.querySelector('.dpr-rule-preview-trigger').disabled)",'继承节点可预览前序规则');
  await click('[data-node="供应商复核"] .dpr-rule-preview-trigger');await wait("document.querySelector('#processingRulePreviewTitle').textContent.includes('饮茶动作说明')");checks.push('点击继承节点打开同一版本内容');await click('[data-preview-close]');
  const action=(await api('/api/processing-rules','POST',{...body,name:'杯子动作规则',stage:'标注',rule_type:'动作标注',action_elements:[{name:'物品',key:'item',values:[{name:'杯子',key:'cup'}]}],action_descriptions:[{zh:'拿起{物品}',en:'Pick up {item}'}]})).rule;
  const tags=(await api('/api/processing-rules','POST',{...body,name:'质量标签规则',stage:'标注',rule_type:'标签标注',annotation_tags:['q_success']})).rule;
  await fill('[data-flow-stage="标注"]','双轮人工标注流程');await click('.dpr-inline-rule-refresh');await wait(`!!document.querySelector('.dpr-node-rule-select option[value="${action.value}"]')`);
  await fill('.dpr-node-rule-select',action.value);await click('.dpr-rule-preview-trigger');await wait(`${previewContent}.includes('Pick up {item}')`);await check(`${previewContent}.includes('杯子')`,'动作规则显示元素、枚举及中英文描述');await shot('05-action-preview');await click('[data-preview-close]');
  await fill('.dpr-node-rule-select',tags.value);await click('.dpr-rule-preview-trigger');await wait("document.querySelector('#processingRulePreviewTitle').textContent.includes('质量标签规则')");await click('#ruleTagView');await wait("document.querySelector('#ruleTagModal').classList.contains('active')");await check("!!document.querySelector('#ruleTagModal input[aria-label=\"质量标签 / 采集质量 / 成功\"]:checked:disabled')",'标签规则复用只读标签查看');await shot('06-tag-preview');await ev("document.querySelector('#processingRulePreview').dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))");await check("document.querySelector('#processingRulePreview').open&&!document.querySelector('#ruleTagModal').classList.contains('active')",'Esc先关闭标签查看，保留规则预览');await click('[data-preview-close]');
  await check("document.documentElement.scrollWidth<=innerWidth+1",'1440桌面表单无新增横向溢出');
  assert.deepEqual(errors,[]);checks.push('无浏览器运行异常');
  fs.writeFileSync(path.join(out,'preview-browser-report.json'),JSON.stringify({passed:checks.length,checks,errors},null,2));console.log(JSON.stringify({passed:checks.length,out}));
}
main().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>{socket?.close();chrome?.kill();if(service?.pid&&process.platform==='win32')spawnSync('taskkill',['/PID',String(service.pid),'/T','/F'],{stdio:'ignore',windowsHide:true});else service?.kill();});
