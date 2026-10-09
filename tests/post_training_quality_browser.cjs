const assert=require('node:assert/strict');
const fs=require('node:fs');
const http=require('node:http');
const os=require('node:os');
const path=require('node:path');
const {spawn}=require('node:child_process');

const root=path.resolve(__dirname,'..');
const port=Number(process.env.TEST_PORT||5014);
const previewUrl=process.env.PREVIEW_URL||`http://127.0.0.1:${port}/data/workbench-v2/optimized`;
const external=Boolean(process.env.PREVIEW_URL);
const debugPort=Number(process.env.DEBUG_PORT||9335);
const browserExe=process.env.BROWSER_EXE||'C:/Program Files/Google/Chrome/Application/chrome.exe';
const windowSize=process.env.WINDOW_SIZE||'1440,900';
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg'};
const server=http.createServer((req,res)=>{
  const url=new URL(req.url,`http://127.0.0.1:${port}`);
  if(url.pathname==='/data/workbench-v2/optimized'){
    const html=fs.readFileSync(path.join(root,'templates/annotation_workbench/optimized.html'),'utf8').replace('{{ tag_tree | tojson }}','[]');
    res.writeHead(200,{'content-type':mime['.html']});res.end(html);return;
  }
  if(url.pathname.startsWith('/static/')){
    const file=path.resolve(root,'.'+url.pathname);
    if(!file.startsWith(root)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
    res.writeHead(200,{'content-type':mime[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));return;
  }
  res.writeHead(404);res.end();
});
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));

async function main(){
  if(!external)await new Promise(resolve=>server.listen(port,'127.0.0.1',resolve));
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'quanta-ptq-'));
  const chrome=spawn(browserExe,[process.env.HEADLESS_MODE||'--headless=old','--disable-gpu','--disable-gpu-compositing','--disable-gpu-rasterization','--disable-gpu-sandbox','--disable-features=Vulkan','--use-gl=disabled','--no-sandbox','--no-first-run','--no-default-browser-check',`--window-size=${windowSize}`,`--user-data-dir=${profile}`,`--remote-debugging-port=${debugPort}`,previewUrl],{stdio:process.env.BROWSER_DEBUG?'inherit':'ignore'});
  try{
    let page;
    for(let index=0;index<80;index+=1){try{const pages=await fetch(`http://127.0.0.1:${debugPort}/json/list`).then(response=>response.json());page=pages.find(item=>item.type==='page'&&item.url.includes('optimized'));if(page)break;}catch(_){}await delay(100);}
    assert.ok(page,'应打开新版工作台页面');
    const socket=new WebSocket(page.webSocketDebuggerUrl),pending=new Map(),pageErrors=[];let sequence=0;
    socket.onmessage=event=>{const message=JSON.parse(event.data);if(message.method==='Runtime.exceptionThrown')pageErrors.push(message.params.exceptionDetails?.exception?.description||message.params.exceptionDetails?.text||'Runtime exception');if(message.method==='Log.entryAdded'&&message.params.entry.level==='error'&&!String(message.params.entry.url||'').endsWith('/favicon.ico'))pageErrors.push(message.params.entry.text);if(message.id&&pending.has(message.id)){const task=pending.get(message.id);pending.delete(message.id);message.error?task.reject(new Error(message.error.message)):task.resolve(message.result);}};
    await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
    const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const result=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(result.exceptionDetails)throw new Error(result.exceptionDetails.text);return result.result.value;};
    await call('Runtime.enable');await call('Log.enable');await call('Page.enable');
    for(let index=0;index<100;index+=1){if(await evaluate("document.querySelector('.main')?.getAttribute('aria-busy')==='false'"))break;await delay(100);}

    console.log('browser check: tab and layout');
    assert.equal(await evaluate("document.querySelector('[data-review-variant=quality]').nextElementSibling.dataset.reviewVariant"),'pre-quality','预训练质检应位于原质检Tab下方');
    assert.equal(await evaluate("document.querySelector('[data-review-variant=pre-quality]').nextElementSibling.dataset.reviewVariant"),'post-quality','后训练质检应位于预训练质检下方');
    assert.match(await evaluate("document.querySelector('[data-review-variant=post-quality]').textContent"),/后训练质检/);
    assert.equal(await evaluate("(()=>{const tab=document.querySelector('[data-review-variant=post-quality]');return tab.scrollHeight<=tab.clientHeight})()"),true,'后训练质检工作台Tab文案必须完整显示');
    await evaluate("document.querySelector('[data-review-variant=post-quality]').click()");
    assert.equal(await evaluate("document.querySelector('[data-review-variant=post-quality]').classList.contains('is-active')"),true);
    assert.equal(await evaluate("document.querySelector('post-training-quality-workspace').hidden"),false);
    assert.equal(await evaluate("document.querySelectorAll('.ptq-public-timeline').length"),1,'后训练质检必须提供一条公共时间轴');
    assert.equal(await evaluate("document.querySelectorAll('.ptq-public-rail [data-segment-id]').length"),0,'公共时间轴只用于定位和创建，不重复展示已标记片段');
    assert.equal(await evaluate("document.querySelectorAll('.ptq-public-rail .ptq-range-handle').length"),2,'公共时间轴应提供待添加区间的左右调整手柄');
    assert.equal(await evaluate("document.body.innerText.includes('问题片段时间轴')"),false,'不应显示额外的问题片段时间轴标题行');
    assert.equal(await evaluate("document.querySelectorAll('.ptq-lane').length"),3,'时间轴必须固定三轨');
    assert.equal(await evaluate("document.querySelectorAll('.ptq-block').length"),8,'所有片段都应直接显示在三条轨道中');
    assert.equal(await evaluate("document.querySelectorAll('.ptq-cluster').length"),0,'新规则不得显示聚合入口');
    assert.equal(await evaluate("document.querySelectorAll('.ptq-list-item').length"),8,'右侧列表应显示全部片段');
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.ptq-list-item')].map(row=>row.dataset.segmentId)"),['A','B','C','D','E','F','G','H'],'右侧列表应按开始时间、结束时间和创建时间排序');
    await evaluate("document.querySelector('.ptq-list-item[data-segment-id=B]').click()");
    assert.equal(await evaluate("document.querySelector('.ptq-id').textContent.trim()"),'02','排序第二的片段应在编辑栏显示 02');
    await evaluate("window.PostTrainingQualityDemo.updateTime('B','start',0.5)");
    assert.equal(await evaluate("document.querySelector('.ptq-id').textContent.trim()"),'01','片段时间排序变化后编辑栏序号应同步变化');
    await evaluate("window.PostTrainingQualityDemo.updateTime('B','start',4.5)");
    assert.equal(await evaluate("document.querySelector('.ptq-block[data-segment-id=A]').closest('.ptq-lane')!==document.querySelector('.ptq-block[data-segment-id=B]').closest('.ptq-lane')"),true,'存在无重合轨道时应优先选择无重合轨道');
    assert.equal(await evaluate("document.querySelector('.ptq-block[data-segment-id=D]').closest('.ptq-lane')===document.querySelector('.ptq-block[data-segment-id=G]').closest('.ptq-lane')"),true,'三轨均重合时允许片段在重合最少的轨道叠加');
    assert.ok(await evaluate("Number(document.querySelector('.ptq-block[data-segment-id=G]').style.zIndex)>Number(document.querySelector('.ptq-block[data-segment-id=D]').style.zIndex)"),'同轨短片段应显示在长片段上方');
    await evaluate("document.querySelector('.ptq-list-item[data-segment-id=D]').click()");
    assert.ok(await evaluate("Number(document.querySelector('.ptq-block[data-segment-id=D]').style.zIndex)>Number(document.querySelector('.ptq-block[data-segment-id=G]').style.zIndex)"),'当前选中片段应临时置顶');
    const selectedBeforePlayback=await evaluate("window.PostTrainingQualityDemo.state.selectedId");
    await evaluate("document.dispatchEvent(new CustomEvent('post-quality-seek',{detail:{seconds:18.5}}))");
    assert.equal(await evaluate("document.querySelectorAll('.ptq-block.is-hit').length"),5,'播放到重叠位置时应同时高亮所有命中片段');
    assert.equal(await evaluate("document.querySelectorAll('.ptq-list-item.is-hit').length"),5,'右侧列表应同步高亮所有命中片段');
    assert.equal(await evaluate("window.PostTrainingQualityDemo.state.selectedId"),selectedBeforePlayback,'播放命中不得切换当前编辑片段');
    const existingTracks=await evaluate("window.PostTrainingQualityDemo.state.segments.filter(item=>item.id!=='C').map(item=>[item.id,item.track])");
    await evaluate("window.PostTrainingQualityDemo.updateTime('C','end',11.2)");
    assert.deepEqual(await evaluate("window.PostTrainingQualityDemo.state.segments.filter(item=>item.id!=='C').map(item=>[item.id,item.track])"),existingTracks,'边界调整不得改变其他片段的轨道');
    assert.notEqual(await evaluate("getComputedStyle(document.querySelector('.ptq-list-item[data-segment-id=F] .ptq-list-id')).borderColor"),await evaluate("getComputedStyle(document.querySelector('.ptq-list-item[data-segment-id=A] .ptq-list-id')).borderColor"),'待完善状态应保留在编号和行内提示中');

    console.log('browser check: editor and reasons');
    await evaluate("document.querySelector('.ptq-block[data-segment-id=A]').click()");
    assert.equal(await evaluate("window.PostTrainingQualityDemo.state.selectedId"),'A','点击业务轨道片段应同步选中对应记录');
    assert.equal(await evaluate("document.querySelector('.ptq-list-item[data-segment-id=A]').classList.contains('is-active')"),true,'业务轨道与右侧列表应同步选中');
    assert.equal(await evaluate("document.querySelector('.ptq-list-item[data-segment-id=A] .ptq-list-id').textContent"),'01','右侧列表应显示补零序号');
    assert.equal(await evaluate("document.querySelector('.ptq-id').textContent.trim()"),'01','编辑栏应显示与右侧列表一致的两位序号');
    assert.equal(await evaluate("document.querySelectorAll('.ptq-resize').length"),0,'业务轨道不应显示边界拖动手柄');
    assert.equal(await evaluate("document.querySelectorAll('.ptq-public-rail [data-segment-id]').length"),0,'选中片段后公共时间轴仍不显示问题片段');
    assert.equal(await evaluate("document.querySelector('.ptq-range-label.is-start').textContent"),'00:01.0','选中片段后公共时间轴应显示其开始时间');
    assert.equal(await evaluate("document.querySelector('.ptq-range-label.is-end').textContent"),'00:05.0','选中片段后公共时间轴应显示其结束时间');
    assert.equal(await evaluate("document.querySelector('.ptq-time-field').textContent"),'00:01.0','编辑栏时间只读展示应与公共时间轴一致');
    assert.equal(await evaluate("document.querySelectorAll('post-training-quality-workspace [data-field=start],[data-field=end]').length"),0,'编辑栏不应提供时间输入框');
    await evaluate("(()=>{const rail=document.querySelector('.ptq-public-rail'),rect=rail.getBoundingClientRect(),handle=document.querySelector('.ptq-range-handle.is-start');handle.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0,clientX:rect.left+rect.width*(1/40)}));document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,button:0,clientX:rect.left+rect.width*(1.5/40)}));document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,button:0,clientX:rect.left+rect.width*(1.5/40)}));})()");
    assert.equal(await evaluate("window.PostTrainingQualityDemo.state.segments.find(item=>item.id==='A').start"),1.5,'公共时间轴手柄应修改选中正式片段的开始时间');
    assert.equal(await evaluate("document.querySelector('.ptq-time-field').textContent"),'00:01.5','公共时间轴调整后编辑栏只读时间应同步更新');
    await evaluate("window.PostTrainingQualityDemo.updateTime('A','start',1)");
    assert.equal(await evaluate("document.querySelector('#ptqVideoConclusion').tagName"),'OUTPUT','整体结论必须自动显示');
    assert.equal(await evaluate("document.querySelector('#ptqVideoConclusion').textContent"),'不合格');
    assert.equal(await evaluate("document.querySelector('post-training-quality-timeline timeline-controls').nextElementSibling.classList.contains('ptq-track-stack')"),true,'平台播放操作区应位于公共时间轴和业务轨道上方');
    assert.equal(await evaluate("document.querySelector('.ptq-public-timeline').compareDocumentPosition(document.querySelector('.ptq-lanes'))&Node.DOCUMENT_POSITION_FOLLOWING"),4,'公共时间轴应位于三条业务轨道上方');
    assert.equal(await evaluate("document.querySelector('.ptq-public-timeline>span').textContent.trim()"),'','公共时间轴左侧不应显示文字');
    assert.equal(await evaluate("[...document.querySelectorAll('.ptq-block')].every(item=>item.textContent.trim()==='')"),true,'业务轨道片段块不应显示片段名或结论文字');
    assert.equal(await evaluate("document.querySelector('.ptq-lane').getBoundingClientRect().height < document.querySelector('.ptq-public-timeline').getBoundingClientRect().height"),true,'三条业务轨道应比公共时间轴更矮');
    assert.equal(await evaluate("document.body.innerText.includes('备注（选填）')"),false,'审核编辑区不应显示选填备注');
    assert.equal(await evaluate("document.body.innerText.includes('错误原因')"),true,'审核编辑区应显示错误原因');
    assert.equal(await evaluate("document.querySelectorAll('post-training-quality-workspace [data-review-error]').length"),7,'错误原因应复用原质检工作台的七个下拉选项');
    assert.equal(await evaluate("(()=>{const head=document.querySelector('.ptq-playhead').getBoundingClientRect(),pub=document.querySelector('.ptq-public-timeline').getBoundingClientRect(),lanes=document.querySelector('.ptq-lanes').getBoundingClientRect();return head.top<=pub.top&&head.bottom>=lanes.bottom})()"),true,'统一播放头应贯穿公共时间轴和三条业务轨道');
    assert.equal(await evaluate("(()=>{const control=document.querySelector('post-training-quality-timeline timeline-controls');control.dataset.identity='kept';document.dispatchEvent(new CustomEvent('post-quality-seek',{detail:{seconds:4.2}}));return document.querySelector('post-training-quality-timeline timeline-controls').dataset.identity})()"),'kept','播放位置更新不得重建平台播放操作区');
    assert.equal(await evaluate("(()=>{const label=document.querySelector('.ptq-conclusion-switch label');return label.scrollHeight<=label.clientHeight})()"),true,'片段结论按钮文字必须保持单行');
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.ptq-sidebar footer .workbench-footer-actions button')].map(button=>button.textContent.trim())"),['保存','释放','驳回','提交']);
    const footerLayout=await evaluate("(()=>{const panel=document.querySelector('.workbench-review'),footer=document.querySelector('.ptq-sidebar>footer'),button=document.querySelector('.ptq-sidebar footer .workbench-footer-actions button');return{panelBottom:panel.getBoundingClientRect().bottom,footerBottom:footer.getBoundingClientRect().bottom,buttonBottom:button.getBoundingClientRect().bottom,viewport:innerHeight}})()");
    assert.ok(footerLayout.buttonBottom<=footerLayout.panelBottom&&footerLayout.footerBottom<=footerLayout.panelBottom,'右侧底部操作区必须完整显示');
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.ptq-editor-actions button')].slice(0,4).map(button=>button.textContent.trim().replace(/\\s+/g,' '))"),['上一段 ⌘↑','下一段 ⌘↓','同轨左 ⌘←','同轨右 ⌘→']);
    assert.equal(await evaluate("document.querySelectorAll('.ptq-conclusion-switch label').length"),2,'片段结论只应显示失误和不合格');
    assert.equal(await evaluate("document.querySelector('.ptq-editor-meta-row').compareDocumentPosition(document.querySelector('.ptq-editor-fields-row'))&Node.DOCUMENT_POSITION_FOLLOWING"),4,'片段基础信息和导航操作应位于片段编辑区上一行');
    assert.equal(await evaluate("document.querySelector('.ptq-editor-meta-row').contains(document.querySelector('.ptq-editor-actions'))"),true,'片段导航与操作区应位于基础信息行');

    await evaluate("document.querySelector('post-training-quality-workspace [data-action=toggle-review-error]').click()");
    const reviewMenu=await evaluate("(()=>{const menu=document.querySelector('.ptq-review-error-menu'),rect=menu.getBoundingClientRect(),trigger=document.querySelector('post-training-quality-workspace [data-action=toggle-review-error]').getBoundingClientRect();return{hidden:menu.hidden,top:rect.top,bottom:rect.bottom,triggerTop:trigger.top,viewport:innerHeight}})()");
    assert.equal(reviewMenu.hidden,false,'错误原因下拉应能展开');
    assert.ok(reviewMenu.top>=0&&reviewMenu.bottom<=reviewMenu.triggerTop&&reviewMenu.bottom<=reviewMenu.viewport,'错误原因下拉应向上展开且完整位于视口内');
    await evaluate("document.querySelector('post-training-quality-workspace [data-review-error=\"动作开始边界偏晚\"]').click()");
    assert.equal(await evaluate("window.PostTrainingQualityDemo.state.segments.find(item=>item.id==='A').reviewErrorReason"),'动作开始边界偏晚','选择错误原因后应写入当前片段');
    assert.equal(await evaluate("document.querySelector('post-training-quality-workspace [data-action=toggle-review-error] span').textContent"),'动作开始边界偏晚','下拉触发器应显示已选错误原因');
    await evaluate("document.querySelector('post-training-quality-workspace [data-action=toggle-review-error]').click();document.querySelector('post-training-quality-workspace [data-action=clear-review-error]').click()");
    assert.equal(await evaluate("window.PostTrainingQualityDemo.segmentErrors(window.PostTrainingQualityDemo.state.segments.find(item=>item.id==='A')).some(error=>error.includes('错误原因'))"),true,'清空错误原因后必填校验应立即失败');
    await evaluate("document.querySelector('post-training-quality-workspace [data-action=toggle-review-error]').click();document.querySelector('post-training-quality-workspace [data-review-error=\"动作开始边界偏晚\"]').click()");

    const editorHeight=await evaluate("document.querySelector('.ptq-editor').getBoundingClientRect().height");
    await evaluate("document.querySelector('post-training-quality-workspace [data-action=toggle-reasons]').click()");
    assert.equal(await evaluate("document.querySelector('.ptq-reason-menu').hidden"),false);
    assert.equal(await evaluate("document.querySelectorAll('.ptq-reason-menu label').length"),4,'失误原因应完整渲染');
    const mistakeMenu=await evaluate("(()=>{const menu=document.querySelector('.ptq-reason-menu'),rect=menu.getBoundingClientRect(),topElement=document.elementFromPoint(rect.left+12,rect.top+12);return{top:rect.top,bottom:rect.bottom,viewport:innerHeight,scrollHeight:menu.scrollHeight,clientHeight:menu.clientHeight,triggerTop:document.querySelector('post-training-quality-workspace [data-action=toggle-reasons]').getBoundingClientRect().top,painted:topElement?.closest('.ptq-reason-menu')===menu}})()");
    assert.ok(mistakeMenu.top>=0&&mistakeMenu.bottom<=mistakeMenu.viewport,'失误原因浮层必须完整位于视口内');
    assert.ok(mistakeMenu.bottom<=mistakeMenu.triggerTop,'原因浮层应向上展开');
    assert.equal(mistakeMenu.painted,true,'失误原因浮层不得被父容器裁切或被其他区域遮挡');
    assert.equal(mistakeMenu.scrollHeight,mistakeMenu.clientHeight,'失误原因不应被内部裁切');
    if(process.env.CAPTURE_REASON_MENUS){
      const capture=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
      fs.writeFileSync(path.resolve(root,'../03-requirements/S027-后训练质检平台/后训练质检工作台-失误原因.png'),Buffer.from(capture.data,'base64'));
    }
    await evaluate("document.querySelector('post-training-quality-workspace input[data-field=reason][value=M01]').click()");
    assert.equal(await evaluate("document.querySelector('.ptq-editor').getBoundingClientRect().height"),editorHeight,'原因选择不应改变底部编辑区高度');
    await evaluate("document.querySelector('post-training-quality-workspace [data-action=toggle-reasons]').click();document.querySelector('post-training-quality-workspace input[data-field=reason][value=M01]').click()");

    await evaluate("document.querySelector('.ptq-list-item[data-segment-id=B]').click();document.querySelector('post-training-quality-workspace [data-action=toggle-reasons]').click()");
    assert.equal(await evaluate("document.querySelectorAll('.ptq-reason-menu label').length"),8,'不合格状态应完整渲染失误和不合格原因');
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.ptq-reason-menu section>header b')].map(item=>item.textContent)"),['不合格原因','失误原因'],'不合格原因应显示在失误原因之前');
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.ptq-selected-reasons .ptq-reason-chip')].map(item=>item.textContent)"),['设备穿戴不规范','手部脱离夹爪'],'已选原因应全部平铺展示，且不合格原因在前');
    assert.equal(await evaluate("document.querySelector('.ptq-selected-reasons').textContent.includes('+')"),false,'已选原因不得以 +N 折叠');
    const rejectedMenu=await evaluate("(()=>{const menu=document.querySelector('.ptq-reason-menu'),rect=menu.getBoundingClientRect(),topElement=document.elementFromPoint(rect.left+12,rect.top+12),last=menu.querySelector('label:last-child').getBoundingClientRect();menu.scrollTop=menu.scrollHeight;const lastAfter=menu.querySelector('label:last-child').getBoundingClientRect();return{top:rect.top,bottom:rect.bottom,viewport:innerHeight,scrollHeight:menu.scrollHeight,clientHeight:menu.clientHeight,painted:topElement?.closest('.ptq-reason-menu')===menu,lastInitiallyVisible:last.bottom<=rect.bottom,lastAccessible:lastAfter.bottom<=rect.bottom&&lastAfter.top>=rect.top}})()");
    assert.ok(rejectedMenu.top>=0&&rejectedMenu.bottom<=rejectedMenu.viewport,'不合格原因浮层必须完整位于视口内');
    assert.equal(rejectedMenu.painted,true,'不合格原因浮层不得被父容器裁切或被其他区域遮挡');
    assert.ok(rejectedMenu.lastInitiallyVisible||rejectedMenu.lastAccessible,'不合格原因最后一项必须可访问');
    assert.equal(await evaluate("document.querySelector('.ptq-editor').getBoundingClientRect().height"),editorHeight,'不合格原因浮层不应改变编辑区高度');
    if(process.env.CAPTURE_REASON_MENUS){
      const capture=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
      fs.writeFileSync(path.resolve(root,'../03-requirements/S027-后训练质检平台/后训练质检工作台-不合格原因.png'),Buffer.from(capture.data,'base64'));
    }
    await evaluate("document.querySelector('post-training-quality-workspace [data-action=toggle-reasons]').click();document.querySelector('.ptq-list-item[data-segment-id=A]').click()");

    console.log('browser check: screenshot');
    const screenshot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    fs.writeFileSync(path.resolve(root,'../03-requirements/S027-后训练质检平台/后训练质检工作台-demo.png'),Buffer.from(screenshot.data,'base64'));

    console.log('browser check: add and validate');
    const beforeDrag=await evaluate("window.PostTrainingQualityDemo.state.segments.length");
    await evaluate("(()=>{const rail=document.querySelector('.ptq-public-rail'),rect=rail.getBoundingClientRect();rail.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0,clientX:rect.left+rect.width*.82}));document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,button:0,clientX:rect.left+rect.width*.9}));})()");
    assert.equal(await evaluate("window.PostTrainingQualityDemo.state.segments.length"),beforeDrag,'公共时间轴拖拽只应更新待添加区间，不得直接创建片段');
    assert.deepEqual(await evaluate("[window.PostTrainingQualityDemo.state.rangeStart,window.PostTrainingQualityDemo.state.rangeEnd]"),[32.8,36],'公共时间轴拖拽应更新待添加片段区间');
    assert.equal(await evaluate("document.querySelector('.ptq-draft-range').hidden"),false,'待添加区间应持续显示，允许继续调整');
    assert.equal(await evaluate("document.querySelectorAll('.ptq-public-rail [data-segment-id]').length"),0,'待添加区间不得伪装成已创建片段');
    const before=await evaluate("window.PostTrainingQualityDemo.state.segments.length");
    await evaluate("document.querySelector('post-training-quality-timeline .segmented-timeline__tool[aria-label=添加]').click()");
    assert.equal(await evaluate("window.PostTrainingQualityDemo.state.segments.length"),before+1);
    assert.equal(await evaluate("document.querySelectorAll('.ptq-lanes [data-segment-id]').length"),before+1,'点击添加后新片段才应进入三条业务轨道');
    assert.equal(await evaluate("window.PostTrainingQualityDemo.state.segments.find(item=>item.id===window.PostTrainingQualityDemo.state.selectedId).conclusion"),'mistake','新增片段必须默认为失误');
    assert.deepEqual(await evaluate("window.PostTrainingQualityDemo.state.segments.find(item=>item.id===window.PostTrainingQualityDemo.state.selectedId).mistakeReasons"),[],'新增片段不得自动选择失误原因');

    await evaluate("document.querySelector('post-training-quality-sidebar [data-action=submit]').click()");
    assert.equal(await evaluate("document.querySelector('#ptqErrorDialog').open"),true);
    assert.match(await evaluate("document.querySelector('#ptqErrorDialog').textContent"),/标注有问题/);
    await evaluate("document.querySelector('#ptqErrorDialog footer button').click()");

    console.log('browser check: complete items without reasons');
    const incompleteMistakeIds=await evaluate("window.PostTrainingQualityDemo.state.segments.filter(item=>item.conclusion==='mistake'&&!item.mistakeReasons.length).map(item=>item.id)");
    for(const id of incompleteMistakeIds){
      await evaluate(`document.querySelector('.ptq-list-item[data-segment-id="${id}"]').click()`);
      await evaluate("document.querySelector('post-training-quality-workspace [data-action=toggle-reasons]').click()");
      await evaluate("document.querySelector('post-training-quality-workspace input[data-field=reason][value=M01]').click()");
      await evaluate("document.querySelector('post-training-quality-workspace [data-action=toggle-review-error]').click();document.querySelector('post-training-quality-workspace [data-review-error=\"片段范围错误\"]').click()");
    }
    const rejectedIds=await evaluate("window.PostTrainingQualityDemo.state.segments.filter(item=>item.conclusion==='rejected').map(item=>item.id)");
    for(const id of rejectedIds){
      await evaluate(`document.querySelector('.ptq-list-item[data-segment-id="${id}"]').click()`);
      const oldReasons=await evaluate("window.PostTrainingQualityDemo.state.segments.find(item=>item.id===window.PostTrainingQualityDemo.state.selectedId).rejectedReasons.slice()");
      await evaluate("document.querySelector('post-training-quality-workspace input[data-field=conclusion][value=mistake]').click()");
      assert.deepEqual(await evaluate("window.PostTrainingQualityDemo.state.segments.find(item=>item.id===window.PostTrainingQualityDemo.state.selectedId).rejectedReasons"),oldReasons,'切换结论不得静默清除原因');
      for(const reason of oldReasons)await evaluate(`document.querySelector('post-training-quality-workspace input[data-field=reason][value=${reason}]').click()`);
      if(!await evaluate("document.querySelector('post-training-quality-workspace input[data-field=reason][value=M01]').checked"))await evaluate("document.querySelector('post-training-quality-workspace input[data-field=reason][value=M01]').click()");
    }
    assert.equal(await evaluate("document.querySelector('#ptqVideoConclusion').textContent"),'失误','只有失误片段的视频结论应为失误');
    assert.equal(await evaluate("document.querySelector('#ptqCompleted')"),null,'不应显示整段检查确认复选框');
    await evaluate("document.querySelector('post-training-quality-sidebar [data-action=save]').click()");
    assert.match(await evaluate("document.querySelector('#workbenchNotice').textContent"),/草稿已保存/);
    await evaluate("document.querySelector('post-training-quality-sidebar [data-action=submit]').click()");
    assert.equal(await evaluate("document.querySelector('#ptqSubmitDialog').open"),true);
    assert.equal(await evaluate("document.querySelector('#ptqSubmitDialog [data-result]').textContent"),'失误');
    await evaluate("document.querySelector('#ptqSubmitDialog [data-action=confirm-submit]').click()");
    assert.equal(await evaluate("document.querySelector('post-training-quality-sidebar [data-action=submit]').disabled"),true,'提交成功后结果应只读');
    assert.equal(await evaluate("document.querySelector('.ptq-time-field')!==null&&document.querySelector('post-training-quality-workspace [data-action=toggle-review-error]').disabled"),true,'提交后时间展示和片段编辑控件应进入只读状态');

    console.log('browser check: original tabs regression');
    await evaluate("document.querySelector('[data-review-variant=quality]').click()");
    assert.equal(await evaluate("document.querySelector('post-training-quality-workspace').hidden"),true);
    assert.equal(await evaluate("document.querySelector('workbench-quality-track').hidden"),false,'原质检工作台应保持可用');
    if(process.env.CAPTURE_REFERENCE){
      const reference=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
      fs.writeFileSync(path.resolve(root,'../03-requirements/S027-后训练质检平台/原质检工作台-组件对照.png'),Buffer.from(reference.data,'base64'));
    }
    await evaluate("document.querySelector('[data-review-variant=segments]').click()");
    assert.equal(await evaluate("document.querySelector('semantic-annotation-track').hidden"),false,'原语义标注应保持可用');
    assert.deepEqual(pageErrors,[],'页面不应产生脚本或控制台错误');
    socket.close();
    console.log('post-training quality browser: passed');
  }finally{chrome.kill();if(!external)server.close();try{fs.rmSync(profile,{recursive:true,force:true});}catch(_){}}
}
main().catch(error=>{console.error(error);if(!external)server.close();process.exitCode=1;});
