const taskTableAssetBase = new URL("../../pages/action-quality-check/assets/", document.currentScript?.src || location.href).href;
const taskTableSidebarAssetBase = new URL("../platform-sidebar/assets/", document.currentScript?.src || location.href).href;
const taskTablePageBase = new URL("../../pages/task-processing/", document.currentScript?.src || location.href);
let taskTableMenuId = 0;

class TaskDataTable extends HTMLElement {
  // Apply the shared fixed-edge scrolling to an existing table without replacing its rows.
  static enhanceFixedEdges(frame, leftColumnCount=1, rightColumnCount=1){
    if(frame.dataset.fixedEdgesReady){frame._sizeMiddleScroll?.();return;}
    frame.dataset.fixedEdgesReady='true';
    frame.dataset.fixedRightCount=String(rightColumnCount);
    frame._updateFixedEdges=()=>{
      const viewport=frame.querySelector('.task-data-table__scroll');
      const overflow=viewport.scrollWidth>viewport.clientWidth+1;
      frame.classList.toggle('task-data-table--fixed-edges',overflow);
      const headers=[...viewport.querySelectorAll('thead th')];
      let offset=0;
      headers.slice(0,leftColumnCount).forEach((header,index)=>{
        viewport.querySelectorAll('tr').forEach(row=>{
          const cell=row.children[index];
          if(!cell)return;
          cell.classList.add('task-table-fixed-left');
          cell.style.setProperty('--fixed-left-offset',offset+'px');
          cell.classList.toggle('task-table-fixed-left-end',index===leftColumnCount-1);
        });
        offset+=header.getBoundingClientRect().width;
      });
      let rightOffset=0;
      (rightColumnCount?headers.slice(-rightColumnCount):[]).reverse().forEach((header,index)=>{
        viewport.querySelectorAll('tr').forEach(row=>{
          const cell=row.children[headers.length-1-index];
          if(!cell)return;
          cell.classList.add('task-table-fixed-right');
          cell.style.setProperty('--fixed-right-offset',rightOffset+'px');
          cell.classList.toggle('task-table-fixed-right-start',index===rightColumnCount-1);
        });
        rightOffset+=header.getBoundingClientRect().width;
      });
      const scrollbar=frame.querySelector('.task-data-table__middle-scroll');
      scrollbar.hidden=!overflow;
      if(!overflow)viewport.scrollLeft=0;
    };
    TaskDataTable.prototype.setupMiddleScroll.call(frame,leftColumnCount,rightColumnCount);
  }
  connectedCallback(){
    // Hydrate business-owned rows using the shared table surface and density.
    if(this.hasAttribute('hydrate')){
      if(this.dataset.ready)return;
      this.dataset.ready='true';
      const table=this.querySelector('table');
      if(!table)return;
      const surface=document.createElement('div');surface.className='task-data-table';
      const frame=document.createElement('div');frame.className='task-data-table__frame';
      const viewport=document.createElement('div');viewport.className='task-data-table__scroll';
      const pager=this.querySelector('list-pagination');
      table.before(surface);surface.append(frame);frame.append(viewport);viewport.append(table);
      if(pager)frame.append(pager);
      return;
    }
    if(this.dataset.ready)return;this.dataset.ready="true";this.menuPrefix='task-menu-'+(++taskTableMenuId);this.render();
    this.setupLayout();
    this.setupPagination();
    if(this.querySelector('.task-data-table__scroll')){
      const frame=document.createElement('div');
      frame.className='task-data-table__frame';
      const viewport=this.querySelector('.task-data-table__scroll');
      viewport.before(frame);
      frame.append(...[viewport,this.querySelector('.task-data-table__middle-scroll'),this.querySelector('list-pagination')].filter(Boolean));
    }
    this.addEventListener('click',event=>{
      const trigger=event.target.closest('.task-data-table__more');
      if(trigger){
        const menu=this.querySelector('#'+trigger.getAttribute('popovertarget'));
        const rect=trigger.getBoundingClientRect();
        this.querySelectorAll('.task-data-table__menu:popover-open').forEach(open=>{if(open!==menu)open.hidePopover();});
        menu.style.left=Math.max(8,Math.min(rect.right-120,innerWidth-128))+'px';
        menu.style.top=(rect.bottom+132>innerHeight?Math.max(8,rect.top-132):rect.bottom+6)+'px';
      }
      const menu=event.target.closest('.task-data-table__menu');
      if(menu&&event.target.closest('[data-action]'))menu.hidePopover();
    });
    this.addEventListener("click",event=>{const action=event.target.closest("[data-action]");const page=event.target.closest("[data-page]");if(action){this.dispatchEvent(new CustomEvent("row-action",{bubbles:true,detail:{action:action.dataset.action,row:Number(action.closest("tr")?.dataset.row)}}));if(action.dataset.action==="edit"&&this.getAttribute("editor-url")){const url=new URL(this.getAttribute("editor-url"),location.href);if(this.getAttribute("variant")==="process-management"&&action.closest("tr")?.dataset.row==="1")url.pathname=url.pathname.replace(/index\.html$/, "simple.html");location.href=url.href;}}if(page&&!page.closest("list-pagination"))this.selectPage(page.dataset.page);});
  }
  setupLayout(){
    if(this.getAttribute('layout')!=='split-stats')return;
    const container=this.querySelector('.task-data-table');
    container.insertAdjacentHTML('afterbegin', `<div class="task-table-summary" aria-label="示例统计">
          <section><h2>数据维度</h2><div class="task-table-summary-values"><div><span>处理中</span><strong>3,126</strong><small>已进入处理任务，但暂未有任意任务产出结果</small></div><div><span>已产出结果</span><strong>9,408</strong><small>只要任意一个处理任务有产出结果即可计入</small></div></div></section>
          <section><h2>数据处理任务维度</h2><div class="task-table-summary-values"><div><span>待处理</span><strong>1,206</strong><small>尚未开始处理的处理任务</small></div><div><span>处理中</span><strong>488</strong><small>已开始但尚未完成的处理任务</small></div><div><span>已完成</span><strong>842</strong><small>已完成处理并产出结果的处理任务</small></div></div></section>
        </div>
        <div class="task-table-heading"><h2>数据列表</h2><div><span data-selected-count>已选择 0 条</span><button type="button" data-batch="start" disabled>批量发起处理任务</button><button type="button" data-batch="reassign" disabled>批量重新分配</button></div></div>`);
    const all=this.querySelector('[data-select-all]');
    const rows=[...this.querySelectorAll('[data-select-row]')];
    const update=()=>{
      const selected=rows.filter(input=>input.checked);
      this.querySelector('[data-selected-count]').textContent=`已选择 ${selected.length} 条`;
      all.checked=rows.length>0&&selected.length===rows.length;
      all.indeterminate=selected.length>0&&selected.length<rows.length;
      this.querySelectorAll('[data-batch]').forEach(button=>button.disabled=!selected.length);
      this.dispatchEvent(new CustomEvent('selection-change',{bubbles:true,detail:{rows:selected.map(input=>Number(input.closest('tr').dataset.row))}}));
    };
    all.addEventListener('change',()=>{rows.forEach(input=>input.checked=all.checked);update();});
    rows.forEach(input=>input.addEventListener('change',update));
    this.querySelectorAll('[data-batch]').forEach(button=>button.addEventListener('click',()=>{
      this.dispatchEvent(new CustomEvent('batch-action',{bubbles:true,detail:{action:button.dataset.batch,rows:rows.filter(input=>input.checked).map(input=>Number(input.closest('tr').dataset.row))}}));
    }));
  }
  setupPagination(){
    if(['task-management','task-records'].includes(this.getAttribute('variant')))return;
    let pager=this.querySelector('list-pagination');
    if(!pager){pager=document.createElement('list-pagination');pager.className='task-data-table__pagination';this.querySelector('.task-data-table').append(pager);}
    const rows=[...this.querySelectorAll('tbody tr')];
    pager.setAttribute('total',rows.length);
    if(this.getAttribute('variant')==='data-management')pager.setAttribute('page-size','20');
    const apply=()=>rows.forEach((row,index)=>row.hidden=index<(pager.page-1)*pager.pageSize||index>=pager.page*pager.pageSize);
    pager.addEventListener('page-change',apply);apply();
  }
  setupMiddleScroll(leftColumnCount=2,rightColumnCount=1){
      const viewport=this.querySelector('.task-data-table__scroll');
      this._middleScrollEvents?.abort();
      this._middleScrollEvents=new AbortController();
      const signal=this._middleScrollEvents.signal;
      viewport.classList.add('has-middle-scroll');
      const scrollbar=document.createElement('div');
      scrollbar.className='task-data-table__middle-scroll';
      scrollbar.tabIndex=0;scrollbar.setAttribute('role','region');scrollbar.setAttribute('aria-label','中间列横向滚动');
      const spacer=document.createElement('div');scrollbar.append(spacer);viewport.after(scrollbar);
      const sizeScrollbar=()=>{
        if(!viewport.clientWidth)return;
        this._updateFixedEdges?.();
        const container=viewport.parentElement.getBoundingClientRect();
        const bounds=viewport.getBoundingClientRect();
        const leftCells=[...viewport.querySelectorAll('thead th')].slice(0,leftColumnCount);
        const leftWidth=leftCells.reduce((sum,cell)=>sum+cell.getBoundingClientRect().width,0);
        const rightWidth=[...viewport.querySelectorAll('thead th')].slice(rightColumnCount?-rightColumnCount:Infinity).reduce((sum,cell)=>sum+cell.getBoundingClientRect().width,0);
        scrollbar.style.marginLeft=`${bounds.left-container.left+leftWidth}px`;
        scrollbar.style.marginRight=`${container.right-bounds.left-viewport.clientWidth+rightWidth}px`;
        spacer.style.width=`${Math.max(0,viewport.scrollWidth-viewport.clientWidth)+scrollbar.clientWidth}px`;
        scrollbar.scrollLeft=viewport.scrollLeft;
      };
      scrollbar.addEventListener('scroll',()=>{viewport.scrollLeft=scrollbar.scrollLeft;},{passive:true,signal});
      viewport.addEventListener('scroll',()=>{scrollbar.scrollLeft=viewport.scrollLeft;},{passive:true,signal});
      viewport.addEventListener('wheel',event=>{
        const x=event.clientX-viewport.getBoundingClientRect().left;
        const delta=event.deltaX||(event.shiftKey?event.deltaY:0);
        const rightWidth=[...viewport.querySelectorAll('thead th')].slice(rightColumnCount?-rightColumnCount:Infinity).reduce((sum,cell)=>sum+cell.getBoundingClientRect().width,0);
        const leftWidth=[...viewport.querySelectorAll('thead th')].slice(0,leftColumnCount).reduce((sum,cell)=>sum+cell.getBoundingClientRect().width,0);
        if(delta&&x>=leftWidth&&x<=viewport.clientWidth-rightWidth){
          event.preventDefault();scrollbar.scrollLeft+=delta;
        }
      },{passive:false,signal});
      this._sizeMiddleScroll=sizeScrollbar;
      this._scrollObserver?.disconnect();
      this._scrollObserver=new ResizeObserver(sizeScrollbar);
      this._scrollObserver.observe(viewport);
      this._scrollObserver.observe(viewport.querySelector("table"));
      requestAnimationFrame(sizeScrollbar);
  }
  renderTaskRows(data){
    const generic=this.getAttribute('variant')==='task-management-many';
    const headers=generic?['序号','文字','类型 Tag','进度条','开关','状态','来源 Tag','发布状态','描边状态 Tag','优先级','文字','日期时间','标注类型 Tag','人员 Tag','版本 Tag','操作']:['任务 ID','名称','所属项目','处理流程','处理状态','任务状态','优先级','任务性质','创建人','创建时间','操作'];
    this.taskRecords=data;
    const rows=data.map(([id,name,project,flows,enabled,priority,creator,time,nature='正式'],index)=>{
      const dataUrl=new URL('data.html',taskTablePageBase);
      dataUrl.search=new URLSearchParams({id,name,total:flows[0]?.[4]||0,completed:flows[0]?.[3]||0,running:String(enabled),stage:flows[0]?.[0]||'标注',...(new URLSearchParams(location.search).has('embed')?{embed:'table-example'}:{})}).toString();
      const stages=['采集','标注','质检','抽检','验收'];
      const progressTypes=Array.from({length:1+index%2},(_,step)=>stages[(index+step)%stages.length]);
      const progressClass=type=>({'采集':'is-collection','质检':'is-quality','抽检':'is-inspection','验收':'is-acceptance'}[type]||'');
      const flowHTML=flows.map(([type,label,version,value,total])=>`<div class="task-flow"><span class="task-flow__name"><span class="table-outline-tag table-progress-type ${progressClass(type)}">${type}</span> ${label} <small>${version}</small></span><span class="task-flow__progress ${progressClass(type)}" role="progressbar" aria-label="${label}" aria-valuenow="${value}" aria-valuemin="0" aria-valuemax="${total}"><span class="task-flow__track"><b style="width:${(total?Math.round(value/total*100):0)}%"></b></span><span class="task-flow__progress-label"><span>${value.toLocaleString('en-US')} / ${total.toLocaleString('en-US')}</span><span>${(total?Math.round(value/total*100):0)}%</span></span></span></div>`).join('');
      const cells=[id,`<a class="task-data-table__name-link" href="${dataUrl.href.replaceAll('&','&amp;')}">${name}</a>`,project,flowHTML,`<button class="task-processing-switch" role="switch" aria-label="${name}处理状态" aria-checked="${enabled}"></button>`,`<span class="table-outline-tag ${enabled?'table-outline-tag--success':''}">${enabled?'已发布':'未发布'}</span>`,`<span class="task-priority" style="--priority-hue:${48-(priority-1)*6}">${priority}</span>`,nature,`<span class="table-person-tag">${creator}</span>`,time,[['data','数据'],['details','详情'],['edit','编辑']].map(([action,label])=>action==='data'?`<a class="task-data-table__data-link" href="${dataUrl.href.replaceAll('&','&amp;')}">${label}</a>`:`<button data-action="${action}">${label}</button>`).join('')];
      if(generic){
        priority=index%9+1;
        cells[6]=`<span class="task-priority" style="--priority-hue:${48-(priority-1)*6}" aria-label="优先级 ${priority}">${priority}</span>`;
        cells[0]=String(index+1).padStart(2,'0');
        cells[1]=`<strong>示例文字 ${index+1}</strong>`;
        cells[2]=`<span class="task-publish-state ${enabled?'is-published':''}">${enabled?'已发布':'未发布'}</span>`;
        cells[3]=progressTypes.map((type,step)=>{const value=(index*7+step*23)%101;return `<div class="task-flow table-progress-line"><span class="task-flow__progress ${progressClass(type)}" role="progressbar" aria-label="${type}进度" aria-valuenow="${value}" aria-valuemin="0" aria-valuemax="100"><span class="task-flow__track"><b style="width:${value}%"></b></span><span class="task-flow__progress-label"><span>${value} / 100</span><span>${value}%</span></span></span></div>`;}).join('');
        cells[4]=`<button class="task-processing-switch" role="switch" aria-label="示例开关 ${index+1}" aria-checked="${enabled}"></button>`;
        cells[5]=`<span class="task-publish-state ${enabled?'is-published':''}">${enabled?'启用':'禁用'}</span>`;
        cells[7]='<button data-action="example">示例按钮</button>';
        cells[8]='普通文本';
        cells[10]=`<button data-action="enable">启用</button><button data-action="edit">编辑</button><button data-action="copy">复制</button><button class="task-data-table__more" popovertarget="${this.menuPrefix}-${index}">更多<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></button><div class="task-data-table__menu" id="${this.menuPrefix}-${index}" popover><button data-action="detail">详情</button><button data-action="rename">重命名</button><button data-action="delete">删除</button></div>`;
      }
      if(generic){
        cells.splice(7,1);cells.splice(2,1);
        cells.splice(5,0,`<span class="table-outline-tag ${index%3===0?'table-outline-tag--active':'table-outline-tag--neutral'}">${index%3===0?'启用':'草稿'}</span>`);
        const outlineStates=[['active','启用'],['active','上线'],['annotated','已标注'],['paused','暂停'],['annotating','标注中'],['running','处理中'],['warning','待发布'],['neutral','未标注'],['archived','已归档'],['warning','待处理']];
        const [tone,label]=outlineStates[index%outlineStates.length];
        cells.splice(6,0,`<span class="table-outline-tag table-outline-tag--${tone}">${label}</span>`);
        const rules=['语义标注','—','动作标注','—'];
        const people=[['Lance Li','Wei Zhang'],['Min Chen'],['joanna.qiao','包媛桐']];
        cells.splice(10,0,
          progressTypes.map(type=>`<div class="table-progress-line"><span class="table-outline-tag table-progress-type ${progressClass(type)}">${type}</span></div>`).join(''),
          rules[index%4]==='—'?'—':`<span class="table-outline-tag ${rules[index%4]==='语义标注'?'table-outline-tag--semantic':'table-outline-tag--motion'}">${rules[index%4]}</span>`,
          `<span class="table-person-tags">${people[index%3].map(person=>`<span class="table-person-tag">${person}</span>`).join('')}</span>`,
          `<span class="table-source-tag ${index%3===2?'table-source-tag--assigned':'table-source-tag--returned'}">${index%3===2?'分配':'驳回'}</span>`,
          `<span class="table-outline-tag table-outline-tag--version">v1.${index%3+2}.0</span>`);
        cells.splice(2,0,cells.splice(10,1)[0]);
        cells.splice(5,1);
        const releaseStates=[['active','上线'],['warning','待发布'],['paused','暂停'],['neutral','下线']];
        const [releaseTone,releaseLabel]=releaseStates[index%releaseStates.length];
        cells.splice(cells.length-1,0,`<span class="table-outline-tag table-outline-tag--${releaseTone}">${releaseLabel}</span>`);
        const orderedCells=[0,1,2,3,4,5,12,14,6,7,8,9,10,11,13,15].map(column=>cells[column]);
        cells.splice(0,cells.length,...orderedCells);
      }
      return `<tr data-row="${index}">${cells.map(cell=>`<td>${cell}</td>`).join('')}</tr>`;
    }).join('');
    this.innerHTML=`<section class="task-data-table task-data-table--tasks"><div class="task-data-table__scroll" tabindex="0" role="region" aria-label="任务表格，可横向滚动"><table><thead><tr>${headers.map(label=>`<th>${label}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div></section>`;
  }
  render(){
    if(this.getAttribute('variant')==='task-records'){
      const params=new URLSearchParams(location.search);
      const requestedTotal=Number(params.get('total')??1200);
      const total=Number.isFinite(requestedTotal)?Math.min(10000,Math.max(0,Math.floor(requestedTotal))):1200;
      const completed=Math.min(total,Math.max(0,Number(params.get('completed'))||0));
      const stage=['采集','标注','质检','抽检','验收'].includes(params.get('stage'))?params.get('stage'):'标注';
      const stageClass={'采集':'is-collection','质检':'is-quality','抽检':'is-inspection','验收':'is-acceptance'}[stage]||'';
      const recordDescriptions=[
        ['衣物归拢','衣物散放在桌面。','归拢至桌面左侧。','1 分钟'],
        ['折叠上衣','一件上衣平铺在桌面。','折好并放在桌角。','1.5 分钟'],
        ['整理桌面','桌面中央散放着两件上衣、一条毛巾和一个收纳袋，右侧留有空位。','将上衣分别折好并叠放在右侧，毛巾放入收纳袋，整理后桌面中央保持空置。','2 分钟'],
        ['毛巾收纳','毛巾展开。','折叠后放入收纳袋。','45 秒'],
        ['衣物分类','三件深色衣物与两件浅色衣物混放，部分衣袖交叠。','逐件分开衣物，按深浅色放在桌面两侧，同组衣物叠放整齐，袖口不得垂出桌边。','1 分钟'],
        ['移放收纳袋','收纳袋位于桌边。','移至桌面中央并放稳。','30 秒'],
        ['铺平衣物','衣物有褶皱。','展开并抚平。','45 秒'],
        ['叠放毛巾','两条毛巾散放。','分别折好，整齐叠放。','1 分钟'],
        ['整理外套','外套堆在桌面右侧，衣袖向外展开，旁边放有一件已折好的上衣。','展开外套并抚平褶皱，将两侧衣袖向内收拢后对折，放在上衣旁边，避免压住其他物品。','1.5 分钟'],
        ['清理操作区域','桌面中央被衣物占用。','将衣物移至一侧，留出操作空间。','1 分钟'],
        ['收拢衣袖','上衣展开，袖口朝外。','将两侧衣袖向内折齐。','40 秒'],
        ['检查收纳结果','衣物已折好。','检查边缘并整理叠放位置。','30 秒']
      ];
      const headers=['数据 ID','视频区域（头部 / 左臂 / 右臂）','序列号','采集结论','质检结论','标注状态','业务环节','当前节点','操作'];
      this.innerHTML=`<section class="task-data-table task-data-table--records"><div class="task-data-table__scroll" role="region" aria-label="任务数据列表" tabindex="0"><table><thead><tr>${headers.map(label=>`<th>${label}</th>`).join('')}</tr></thead><tbody>${Array.from({length:total},(_,i)=>{
        const id='recording_e2e_'+String(i+1).padStart(3,'0');
        const [recordTitle,initialState,endState,timeLimit]=recordDescriptions[i%recordDescriptions.length];
        const done=i<completed;
        const error=i%3===1;
        return `<tr data-row="${i}"><td><code>${id}</code></td><td><div class="task-record-media-description"><strong class="task-record-media-description__label">${recordTitle} · ${timeLimit}</strong> <dl><div><dt>初始状态</dt><dd>${initialState}</dd></div><div><dt>结束状态</dt><dd>${endState}</dd></div></dl></div><div class="task-record-videos">${['头部','左臂','右臂'].map((view,index)=>i===4?`<div class="task-record-video task-record-video--loading" role="status" aria-label="${view}：加载中" aria-busy="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9" opacity=".2"/><path d="M12 3a9 9 0 0 1 9 9" stroke-linecap="round"/></svg><small>加载中</small></div>`:i===3?`<div class="task-record-video task-record-video--failed" role="img" aria-label="${view}：上传失败" title="${view}：上传失败"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6m0 3v1"/></svg><small>上传失败</small></div>`:`<img class="task-record-video task-record-video--image" src="${new URL('../../assets/task-records/record-'+(i%2+1)+'-'+['head','left-arm','right-arm'][index]+'.png',taskTablePageBase).href}" alt="${view}视角图片" title="${view}" loading="lazy">`).join('')}</div></td><td><code>MOZ2-20197-${String(i+1).padStart(2,'0')}</code></td><td><span class="task-data-table__status table-result--success table-result--passed">成功</span></td><td><span class="task-data-table__status table-result--${error?'danger table-result--error':'success table-result--passed'}">${error?'操作错误':'合格'}</span></td><td><span class="table-outline-tag table-outline-tag--${done?'annotated':'neutral'}">${done?'已标注':'未标注'}</span></td><td><span class="table-outline-tag table-progress-type ${stageClass}">${stage}</span></td><td>${done?'内部验收':['供应商抽验','供应商复核','供应商验收'][i%3]}</td><td><button type="button" data-action="annotation">查看标注</button></td></tr>`;
      }).join('')}</tbody></table></div></section>`;
      return;
    }
    const operation=this.getAttribute('variant');
    if(operation==='data-management'){
      this.records=[
        ['417001','261071','','','','','—','—','—','—','—','预训练采集'],
        ['405708','261071','020454','厨房数据质检任务','厨房数据质检流程v3','','合格','未标注','处理中','质检复核','Olivia Davis','demo 项目'],
        ['405709','261071','020453','家居动作标注任务','','家居动作标注流程v2','合格','已标注','已归档','标注完成','Emma Wilson','demo 项目'],
        ['405761','261071','020454','厨房数据质检任务','厨房数据质检流程v3','','操作错误','未标注','处理中','人工质检','Olivia Davis','demo 项目'],
        ['405711','261071','020453','家居动作标注任务','','家居动作标注流程v2','合格','标注中','待处理','供应商标注','James Miller','demo 项目'],
        ['406006','261197','020455','端到端切分标注任务','多级质检复核流程v3','端到端切分标注流程v2','合格','已标注','处理中','供应商验收','Noah Brown','预训练采集'],
        ['412001','261042','020451','三方数据处理任务','导入数据质检流程v4','','待质检','未标注','已归档','已归档','—','宁德项目']
      ];
      const samples=this.records.slice();
      for(let index=samples.length;index<100;index++){
        const record=[...samples[index%samples.length]];
        record[0]=String(418000+index);
        this.records.push(record);
      }
      const tag=(value,column)=>{
        if(!value||value==='—')return '<span class="table-empty-value">—</span>';
        if(column===6){
          const tone=value==='合格'?'success':['不合格','操作错误'].includes(value)?'danger':'neutral';
          return `<span class="task-data-table__status table-result--${tone} table-result--${value==='合格'?'passed':value==='不合格'?'failed':value==='操作错误'?'error':'pending'}">${value}</span>`;
        }
        const tone=({'未标注':'neutral','标注中':'annotating','已标注':'annotated','待处理':'warning','处理中':'running','暂停':'paused','已归档':'archived'})[value]||'neutral';
        return `<span class="table-outline-tag table-outline-tag--${tone}">${value}</span>`;
      };
      const headers=['数据 ID','采集任务 ID','处理任务 ID','处理任务名称','质检流程','标注流程','质检结果','标注状态','处理状态','当前节点','当前处理人','操作'];
      this.innerHTML=`<section class="task-data-table task-data-table--data"><div class="task-data-table__scroll" role="region" aria-label="数据列表，可横向滚动" tabindex="0"><table><thead><tr><th><input type="checkbox" data-select-all aria-label="选择本页全部数据"></th>${headers.map(label=>`<th>${label}</th>`).join('')}</tr></thead><tbody>${this.records.map((record,index)=>`<tr data-row="${index}"><td><input type="checkbox" data-select-row aria-label="选择数据 ${record[0]}"></td>${record.slice(0,11).map((value,col)=>`<td>${col>=6&&col<=8?tag(value,col):col===3?`<strong>${value||'—'}</strong>`:col===10&&value&&value!=='—'?`<span class="table-person-tag">${value}</span>`:value||'—'}</td>`).join('')}<td><button type="button" data-action="view">查看</button><button type="button" data-action="reassign" ${!record[2]||record[8]==='已归档'?'disabled':''}>重新分配</button></td></tr>`).join('')}</tbody></table></div></section>`;
      this.querySelector('.task-data-table').insertAdjacentHTML('beforeend','<list-pagination class="task-data-table__pagination"></list-pagination>');
      this.setupMiddleScroll();
      return;
    }
    if(['project-management','user-group-management','supplier-management','permission-roles','permission-resources','permission-grants'].includes(operation)){
      const tags=values=>values.map(value=>`<span class="table-outline-tag table-progress-type ${value==='质检'?'is-quality':value==='验收'?'is-acceptance':''}">${value}</span>`).join(' ');
      const people=values=>`<span class="table-person-tags">${values.map(value=>`<span class="table-person-tag">${value}</span>`).join('')}</span>`;
      const edit='<button type="button" data-action="edit">编辑</button>';
      const state=value=>`<span class="table-outline-tag ${value==='启用'?'table-outline-tag--success':''}">${value}</span>`;
      const configs={
        'project-management':{headers:['项目 ID','项目名称','描述','负责人','状态','操作'],rows:[
          ['PRJ–001','预训练采集','面向基础模型预训练的数据采集与持续扩充项目',people(['Lance Li','Wei Zhang']),state('启用'),edit],
          ['PRJ–002','demo 项目','面向客户演示和场景验证的快速数据生产项目',people(['Min Chen']),state('启用'),edit],
          ['PRJ–003','宁德项目','宁德时代现场任务的数据采集与处理项目',people(['Emma Wilson','Olivia Davis']),state('停用'),edit]
        ]},
        'user-group-management':{headers:['用户组标识','用户组名称','支持业务环节','成员','操作'],rows:[
          ['group.annotation','标注员用户组',tags(['标注']),'10 人',edit],
          ['group.annotation-sampling','标注抽验员用户组',tags(['标注']),'20 人',edit],
          ['group.experimental-annotation','新规实验标注员用户组',tags(['标注']),'8 人',edit],
          ['group.quality-review','质检复核用户组',tags(['质检']),'12 人',edit],
          ['group.acceptance','内部验收用户组',tags(['质检','标注']),'6 人',edit],
          ['group.e2e-split-acceptance','验收-端到端切分标注',tags(['标注']),'6 人',edit]
        ]},
        'supplier-management':{headers:['供应商 ID','供应商名称','支持业务环节','操作'],rows:[
          ['SUP–001','光轮智能',tags(['质检','标注']),edit],['SUP–002','供应商 A',tags(['标注']),edit],['SUP–003','千寻数据',tags(['质检']),edit]
        ]},
        'permission-roles':{headers:['角色 ID','角色名称','成员','数据范围','更新时间','操作'],rows:[
          ['ROLE-DATA-ADMIN','数据管理员','12 人','数据平台全部菜单','2026-07-21',edit],
          ['ROLE-OPERATOR','生产执行人员','46 人','任务、工作台','2026-07-18',edit],
          ['ROLE-VENDOR','供应商人员','40 人','已授权任务与数据','2026-07-16',edit]
        ]},
        'permission-resources':{headers:['资源 ID','资源名称','资源类型','操作'],rows:[]},
        'permission-grants':{headers:['授权对象','角色','数据范围','操作'],rows:[]}
      };
      const config=configs[operation];
      this.innerHTML=`<section class="task-data-table task-data-table--operations" data-kind="${operation}"><div class="task-data-table__scroll" role="region" aria-label="管理列表" tabindex="0"><table><thead><tr>${config.headers.map(label=>`<th>${label}</th>`).join('')}</tr></thead><tbody>${config.rows.map((cells,index)=>`<tr data-row="${index}">${cells.map((value,column)=>`<td>${column===0?`<code>${value}</code>`:column===1?`<strong>${value}</strong>`:value}</td>`).join('')}</tr>`).join('')}</tbody></table>${config.rows.length?'':'<p class="operations-empty">暂无示例数据</p>'}</div></section>`;
      return;
    }
    if(['rule-management','workbench-management'].includes(this.getAttribute('variant'))){
      const rule=this.getAttribute('variant')==='rule-management';
      const tag=(label,tone='')=>`<span class="table-outline-tag ${tone}">${label}</span>`;
      const headers=rule?['规则 ID','适用环节','规则名称','类型','描述','状态','创建人','创建时间','操作']:['工作台 ID','名称','描述','业务类型','规则类型','状态'];
      const rows=rule?[
        ['RL–009',tag('标注','table-progress-type'),'<strong>端到端切分标注规则</strong>','语义标注','仅切分 High-level 与 Low-level 时间片段，不配置动作元素和动作描述','<span class="table-outline-tag table-outline-tag--active">启用</span>','<span class="table-person-tag">Emma Wilson</span>','2026-08-03','<button type="button" data-action="details">详情</button>']
      ]:[
        ['wb.semantic-annotation@1.0','<strong>语义标注工作台</strong>','面向语义标注 E/F/G 的低高层级语义编辑工作台。',tag('标注','table-progress-type'),tag('语义标注'),tag('启用','table-outline-tag--success')],
        ['wb.quality-review@2.0','<strong>质检工作台</strong>','面向质检节点的多视角视频与质检问题处理工作台。',tag('质检','table-progress-type is-quality'),'—',tag('启用','table-outline-tag--success')],
        ['wb.action-annotation@4.1','<strong>动作标注工作台</strong>','面向动作元素标注的分段、动作描述与提交工作台。',tag('标注','table-progress-type'),tag('动作标注'),tag('停用')],
        ['wb.data-detail@1.0','<strong>详情工作台</strong>','用于验收节点查看处理结果与数据详情的工作台。',tag('验收','table-progress-type is-acceptance'),'—',tag('草稿')]
      ];
      this.innerHTML=`<section class="task-data-table task-data-table--configuration ${rule?'is-rules':'is-workbenches'}"><div class="task-data-table__scroll" role="region" aria-label="${rule?'规则':'工作台'}列表" tabindex="0"><table><thead><tr>${headers.map(text=>`<th>${text}</th>`).join('')}</tr></thead><tbody>${rows.map((cells,index)=>`<tr data-row="${index}">${cells.map((text,column)=>`<td>${column===0?`<code>${text}</code>`:text}</td>`).join('')}</tr>`).join('')}</tbody></table></div></section>`;
      return;
    }
    if(this.getAttribute('variant')==='operator-management'){
      this.innerHTML=`<section class="task-data-table task-data-table--operators"><div class="task-data-table__scroll" role="region" aria-label="算子列表" tabindex="0"><table><thead><tr>${['算子','当前版本','版本数','描述','创建人','更新时间','操作'].map(label=>`<th>${label}</th>`).join('')}</tr></thead><tbody><tr data-row="0"><td><strong>端到端切分标注处理算子</strong><code>e2e_segment_annotation</code></td><td><span class="table-outline-tag table-outline-tag--version">v1.2.0</span></td><td><button type="button" data-action="versions">3 个版本</button></td><td><span class="task-data-table__description">完成端到端数据切分、动作片段标注与结构化结果输出。</span></td><td><span class="table-person-tag">Emma Wilson</span></td><td><time>2026-08-28 16:40</time></td><td><button type="button" data-action="details">详情</button></td></tr></tbody></table></div></section>`;
      return;
    }
    if(['task-management','task-management-many'].includes(this.getAttribute('variant'))){
      const data=[
        ['20455','端到端切分标注','预训练采集',[[ '标注','端到端切分标注流程','v2',420,1200]],true,9,'Emma Wilson','2026-08-03 10:00'],
        ['20454','厨房数据标准化处理','demo 项目',[[ '质检','多级质检复核流程','v3',842,1206],['标注','端到端切分标注流程','v2',488,842]],true,9,'James Miller','2026-07-24 09:42'],
        ['20453','家居动作分段标注','demo 项目',[[ '标注','双轮人工标注流程','v2',488,842]],true,9,'Olivia Davis','2026-07-25 16:20'],
        ['20452','通用评测集季度构建','宁德项目',[[ '质检','标准训练数据自动质检流程','v1',488,488]],false,6,'Noah Brown','2026-07-23 11:08']
      ];
      if(this.getAttribute('variant')==='task-management-many'){
        const samples=data.slice();
        data.splice(0,data.length,...Array.from({length:32},(_,index)=>{
          const sample=samples[index%samples.length];
          const total=1200+index*120;
          return [String(20500-index),`${sample[1]} · 第 ${index+1} 批`,['预训练采集','家庭服务机器人','仓储拣选专项','通用评测集'][index%4],Array.from({length:1+index%2},(_,step)=>[step%2?'质检':'标注',step%2?'多级质检复核流程':'端到端切分标注流程',`v${step+1}`,Math.round(total*((index*7+step*13)%101)/100),total]),index%5!==0,index%3?9:6,['Emma Wilson','James Miller','Olivia Davis','Noah Brown'][index%4],`2026-09-${String(1+index%16).padStart(2,'0')} 10:00`];
        }));
      }
      if(operation==='task-management'){
        const samples=data.slice();
        const names=['餐桌物品识别','仓储拣选动作','室内导航轨迹','厨房操作分段','家居场景复核','机器人抓取评测','多视角动作标注','交互指令采集'];
        for(let index=data.length;index<100;index++){
          const sample=samples[index%samples.length];
          data.push([String(20455-index),`${names[(index-4)%names.length]} · 第 ${Math.floor((index-4)/names.length)+1} 批`,sample[2],sample[3].map(flow=>[...flow.slice(0,3),Math.round(flow[4]*((index*13)%101)/100),flow[4]]),index%5!==0,1+index%9,sample[6],sample[7]]);
        }
      }
      if(operation==='task-management'){
        const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
        try{
          const created=JSON.parse(localStorage.getItem('quanta-processing-tasks')||'[]');
          data.unshift(...created.map(task=>[escape(task.id),escape(task.name),escape(task.project),task.stages.map(stage=>[escape(stage.stage),escape(stage.flow),escape(stage.version),0,task.quantity||0]),false,task.priority,'Aria.Pei',escape(task.createdAt),escape(task.nature)]));
        }catch{}
      }
      this.renderTaskRows(data);
      this.setupMiddleScroll();
      this.querySelectorAll('.task-processing-switch').forEach(button=>button.addEventListener('click',()=>{
        const enabled=button.getAttribute('aria-checked')!=='true';button.setAttribute('aria-checked',String(enabled));
        this.dispatchEvent(new CustomEvent('processing-change',{bubbles:true,detail:{row:Number(button.closest('tr').dataset.row),enabled}}));
      }));
      return;
    }
    if(this.getAttribute("variant")==="process-management"){
      const data=[
        {id:"e2e-split-annotation",name:"端到端切分标注流程",status:"enabled",statusText:"启用",time:"2026-07-29 10:16"},
        {id:"e2e-split-annotation",name:"端到端切分标注简洁版",status:"draft",statusText:"草稿",time:"2026-08-04 11:30"},
        {id:"e2e-split-annotation-complex",name:"多阶段任务处理复杂版",status:"draft",statusText:"草稿",time:"2026-09-07 10:16"}
      ];
const rows=data.map((item,index)=>`<tr data-row="${index}"><td><code>${item.id}</code></td><td><strong>${item.name}</strong></td><td><span class="task-data-table__scene">标注</span></td><td><span class="task-data-table__description">自动切分，完成供应商审核与抽样，按条件进入内部验收。</span></td><td><span class="table-person-tag">${['Emma Wilson','James Miller','Olivia Davis'][index]}</span></td><td><span class="table-outline-tag ${item.status==='enabled'?'table-outline-tag--active':'table-outline-tag--neutral'}">${item.statusText}</span></td><td><time>${item.time}</time></td><td><button data-action="${item.status==='enabled'?'disable':'enable'}">${item.status==='enabled'?'停用':'启用'}</button>${item.status==='draft'?'<button data-action="edit">编辑</button>':''}<button data-action="copy">复制</button><button class="task-data-table__more" popovertarget="${this.menuPrefix}-${index}">更多<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></button><div class="task-data-table__menu" id="${this.menuPrefix}-${index}" popover><button data-action="detail">详情</button><button data-action="rename">重命名</button><button data-action="delete">删除</button></div></td></tr>`).join("");
      this.innerHTML=`<section class="task-data-table task-data-table--process task-data-table--fixed-edges"><div class="task-data-table__scroll"><table><thead><tr><th>流程标识</th><th>名称</th><th><span class="task-data-table__sortable">业务环节<img src="${taskTableSidebarAssetBase}icon-sidebar-section-chevron.svg" alt=""></span></th><th>描述</th><th>创建人</th><th><span class="task-data-table__sortable">状态<img src="${taskTableSidebarAssetBase}icon-sidebar-section-chevron.svg" alt=""></span></th><th>更新时间</th><th>操作</th></tr></thead><tbody>${rows}</tbody></table></div><list-pagination class="task-data-table__pagination"></list-pagination></section>`;
      this.setupMiddleScroll(1);
      return;
    }
    if(this.getAttribute('variant')==='workbench-pool'){
      const data=[['端到端切分标注流程','供应商抽验',242,59],['端到端切分标注流程','内部验收',86,18],['预训练数据质检流程','采集质检',4,2],['预训练数据质检流程','质检验收',4,2]];
      this.innerHTML=`<section class="task-data-table"><div class="task-data-table__scroll"><table><thead><tr>${['流程','节点','处理类型','待领取','处理中','操作'].map(t=>`<th>${t}</th>`).join('')}</tr></thead><tbody>${data.map(([flow,node,pending,active],i)=>`<tr data-row="${i}" data-flow="${flow}" data-node="${node}"><td>${flow}</td><td><span class="task-data-table__tag">${node}</span></td><td><span class="task-data-table__tag">${i<2?'单条处理':'批量处理'}</span></td><td>${pending}</td><td>${active}</td><td><button data-action="start">开始处理</button></td></tr>`).join('')}</tbody></table></div><list-pagination class="task-data-table__pagination" total="4"></list-pagination></section>`;return;
    }
    const rows=Array.from({length:Number(this.getAttribute("rows")||4)},(_,index)=>`<tr data-row="${index}"><td>端到端切分标注流程</td><td><span class="task-data-table__tag">供应商抽检</span></td><td>243</td><td>39</td><td>3.4小时</td><td><span class="task-data-table__priority">9级 164·7级36·6级42</span></td><td><button data-action="start">开始处理</button><button data-action="more">更多操作</button></td></tr>`).join("");
    this.innerHTML=`<section class="task-data-table"><div class="task-data-table__scroll"><table><thead><tr><th>流程</th><th>节点</th><th>待领取</th><th>处理中</th><th>最长滞留</th><th>优先级分布</th><th>操作</th></tr></thead><tbody>${rows}</tbody></table></div><list-pagination class="task-data-table__pagination"></list-pagination></section>`;
  }
  selectPage(value){if(/^\d+$/.test(value))this.querySelectorAll("[data-page]").forEach(button=>button.classList.toggle("is-current",button.dataset.page===value));this.dispatchEvent(new CustomEvent("page-change",{bubbles:true,detail:{page:value}}));}
}
customElements.define("task-data-table",TaskDataTable);
