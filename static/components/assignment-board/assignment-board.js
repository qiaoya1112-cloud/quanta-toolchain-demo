(() => {
  const taskDataPage=new URL('../../pages/task-processing/data.html',document.currentScript.src);
  const taskLink=(task,index)=>{
    const url=new URL(taskDataPage);
    url.search=new URLSearchParams({id:String(index+1),name:task.name,total:task.total,completed:task.current+task.other,running:String(!task.paused),stage:'质检',from:'assignment',...(new URLSearchParams(location.search).has('embed')?{embed:'table-example'}:{})});
    return url.href.replaceAll('&','&amp;');
  };
  class AssignmentBoard extends HTMLElement {
    get supplier(){return this.suppliers[this.supplierIndex];}
    get tasks(){return this.supplier.tasks;}
    set tasks(value){this.supplier.tasks=value;}
    get total(){return this.supplier.total;}
    set total(value){this.supplier.total=value;}
    connectedCallback(){
      if(this.ready)return;this.ready=true;this.tab='suppliers';this.filters={};this.supplierIndex=0;
      this.suppliers=[{name:'光轮智能',total:17200,consumed:234,tasks:[]}];
      this.tasks=[{name:'厨房数据质检',flow:'厨房数据质检流程',node:'供应商复核',priority:9,current:96,other:36,total:240,limit:180,paused:false},{name:'三方数据导入质检',flow:'三方数据导入质检流程',node:'格式校验',priority:6,current:138,other:72,total:388,limit:260,paused:false}];
      this.suppliers.push(
        {name:'供应商 A',total:12000,consumed:72,tasks:[{...this.tasks[0],current:72,other:48,limit:150}]},
        {name:'千寻数据',total:9600,consumed:108,tasks:[{...this.tasks[1],current:108,other:62,limit:200}]},
        {name:'供应商 B（示例）',total:8000,consumed:100,tasks:this.tasks.map(task=>({...task,current:50,other:30,limit:120}))}
      );
      this.suppliers.forEach(supplier=>{
        const samples=supplier.tasks.slice();
        supplier.tasks=Array.from({length:100},(_,index)=>({...samples[index%samples.length],name:index<samples.length?samples[index%samples.length].name:`${samples[index%samples.length].name} · 第 ${index+1} 批`,priority:9-index%9}));
      });
      this.innerHTML='<div class="assignment-board"><aside class="assignment-resources"><h2>处理资源</h2><p>选择供应商或用户组查看产能分布</p><task-status-tabs variant="resources"></task-status-tabs><div data-resources></div></aside><section class="assignment-detail" aria-label="资源任务详情"></section></div><dialog class="assignment-dialog"><form><h2 data-dialog-title></h2><p>仅修改当前页面的演示数据</p><form-input name="capacity" label="产能（条）"></form-input><p class="assignment-error" role="alert"></p><div class="assignment-dialog-actions"><text-button data-cancel>取消</text-button><text-button variant="primary" data-save>保存</text-button></div></form></dialog><p class="assignment-feedback" role="status"></p>';
      this.addEventListener('tab-change',event=>{this.tab=event.detail.value;this.render();});
      this.addEventListener('click',event=>{
        const trigger=event.target.closest('[data-action]');if(!trigger)return;
        const {action,index}=trigger.dataset;
        if(action==='supplier'){this.supplierIndex=Number(index);this.render();this.querySelector('[role=status]').textContent='';}
        if(action==='pause'){const task=this.tasks[Number(index)];task.paused=!task.paused;this.render();this.querySelector('[role=status]').textContent=`${task.name}已${task.paused?'暂停分配，数据仍可流入':'恢复处理'}（本地预览）`;}
        if(action==='capacity'||action==='limit')this.openEditor(action,index);
      });
      const dialog=this.querySelector('dialog');
      dialog.querySelector('[data-cancel]').addEventListener('click',()=>dialog.close());
      const save=()=>{
        const input=dialog.querySelector('input');const value=Number(input.value);
        if(!input.value.trim()||!Number.isSafeInteger(value)||value<0||(this.editAction==='capacity'&&value<this.supplier.consumed)){dialog.querySelector('[role=alert]').textContent=this.editAction==='capacity'?`请输入不小于已消耗产能 ${this.supplier.consumed} 的整数`:'请输入非负整数';return;}
        if(this.editAction==='capacity')this.total=value;else this.tasks[this.editIndex].limit=value;
        dialog.close();this.render();this.querySelector('[role=status]').textContent='已更新本地产能预览，未提交到服务器。';
      };
      dialog.querySelector('[data-save]').addEventListener('click',save);
      dialog.querySelector('form').addEventListener('submit',event=>{event.preventDefault();save();});
      this.render();
    }
    setFilters(filters){this.filters=filters;this.render();}
    openEditor(action,index){
      this.editAction=action;this.editIndex=Number(index);
      const dialog=this.querySelector('dialog');dialog.querySelector('[data-dialog-title]').textContent=action==='capacity'?'产能分配':'设置产能上限';
      dialog.querySelector('input').value=action==='capacity'?this.total:this.tasks[this.editIndex].limit;
      dialog.querySelector('[role=alert]').textContent='';dialog.showModal();dialog.querySelector('input').focus();
    }
    setupMiddleScroll(){
      const viewport=this.querySelector('.assignment-table-wrap');
      const scrollbar=document.createElement('div');
      scrollbar.className='assignment-middle-scroll';
      scrollbar.tabIndex=0;scrollbar.setAttribute('role','region');scrollbar.setAttribute('aria-label','中间列横向滚动');
      const spacer=document.createElement('div');scrollbar.append(spacer);viewport.after(scrollbar);
      const sizeScrollbar=()=>{
        const container=viewport.parentElement.getBoundingClientRect();
        const bounds=viewport.getBoundingClientRect();
        const leftWidth=viewport.querySelector('thead th:first-child').getBoundingClientRect().width;
        const rightWidth=viewport.querySelector('thead th:last-child').getBoundingClientRect().width;
        scrollbar.style.marginLeft=`${bounds.left-container.left+leftWidth}px`;
        scrollbar.style.marginRight=`${container.right-bounds.left-viewport.clientWidth+rightWidth}px`;
        spacer.style.width=`${Math.max(0,viewport.scrollWidth-viewport.clientWidth)+scrollbar.clientWidth}px`;
        scrollbar.scrollLeft=viewport.scrollLeft;
      };
      scrollbar.addEventListener('scroll',()=>{viewport.scrollLeft=scrollbar.scrollLeft;},{passive:true});
      viewport.addEventListener('scroll',()=>{scrollbar.scrollLeft=viewport.scrollLeft;},{passive:true});
      viewport.addEventListener('wheel',event=>{
        const delta=event.deltaX||(event.shiftKey?event.deltaY:0);
        if(delta){event.preventDefault();scrollbar.scrollLeft+=delta;}
      },{passive:false});
      this._scrollObserver?.disconnect();
      this._scrollObserver=new ResizeObserver(sizeScrollbar);
      this._scrollObserver.observe(viewport);
      this._scrollObserver.observe(viewport.querySelector("table"));
      requestAnimationFrame(sizeScrollbar);
    }
    render(){
      const detail=this.querySelector('.assignment-detail');
      const board=this.querySelector('.assignment-board');
      const detailFilter=board.querySelector('task-filter-bar');
      if(detailFilter)board.prepend(detailFilter);
      board.querySelector('.assignment-pagination')?.remove();
      const resources=document.createElement('resource-list');resources.selected=String(this.supplierIndex);
      resources.items=this.tab==='suppliers'?this.suppliers.map((supplier,index)=>({id:String(index),label:supplier.name,meta:`${supplier.tasks.length} 个任务`})) : [];
      resources.addEventListener('resource-select',event=>{this.supplierIndex=Number(event.detail.value);this.render();});
      this.querySelector('[data-resources]').replaceChildren(resources);
      if(this.tab!=='suppliers'){detail.innerHTML='<p class="assignment-empty">暂无用户组分配数据</p>';return;}
      const visible=this.tasks.map((task,index)=>({task,index})).filter(({task})=>(!this.filters.scene||this.filters.scene==='质检')&&(!this.filters.task||task.name===this.filters.task)&&(!this.filters.node||task.node===this.filters.node));
      detail.innerHTML=`<task-page-header class="assignment-overview" title="${this.supplier.name}" description="任务优先级相同，优先分配靠前的任务；暂停会停止分配，不会停止数据流入" action="产能分配"></task-page-header><stat-cards variant="capacity" period="2026-07-01 至 2026-07-31" total="${this.total}" consumed="${this.supplier.consumed}"></stat-cards><div class="assignment-list-heading"><h2>任务分配</h2><span>${visible.length} 个任务</span></div><div class="assignment-table-wrap" tabindex="0" role="region" aria-label="任务分配表格，可横向滚动"><table class="assignment-table"><colgroup><col style="width:180px"><col style="width:100px"><col style="width:190px"><col style="width:120px"><col style="width:80px"><col style="width:320px"><col style="width:110px"><col style="width:220px"></colgroup><thead><tr>${['任务名称','状态','处理流程','节点','优先级','节点整体进度','产能上限','操作'].map(label=>`<th scope="col">${label}</th>`).join('')}</tr></thead><tbody>${visible.map(({task:t,index})=>`<tr><th scope="row"><a class="assignment-task-link" href="${taskLink(t,index)}">${t.name}</a></th><td><span class="table-outline-tag ${t.paused?'table-outline-tag--paused':'table-outline-tag--running'}">${t.paused?'已暂停':'处理中'}</span></td><td>${t.flow}</td><td>${t.node}</td><td><span class="task-priority" style="--priority-hue:${48-(t.priority-1)*6}">${t.priority}</span></td><td><capacity-progress current="${t.current}" other="${t.other}" total="${t.total}"></capacity-progress></td><td>${t.limit} 条</td><td><div class="assignment-table-actions"><text-button variant="text" data-action="limit" data-index="${index}">设置产能上限</text-button><text-button variant="text" data-action="pause" data-index="${index}">${t.paused?'恢复分配':'暂停分配'}</text-button></div></td></tr>`).join('')||'<tr><td colspan="8" class="assignment-empty">暂无符合条件的任务</td></tr>'}</tbody></table></div>`;
      const overview=detail.querySelector('.assignment-overview');
      overview.addEventListener('header-action',()=>this.openEditor('capacity'));
      if(detailFilter)overview.after(detailFilter);
      this.setupMiddleScroll();
      board.insertAdjacentHTML('beforeend','<list-pagination class="assignment-pagination" page-size="20"></list-pagination>');
      const pager=board.querySelector('list-pagination');
      const frame=document.createElement('div');
      frame.className='assignment-table-frame';
      const viewport=detail.querySelector('.assignment-table-wrap');
      viewport.before(frame);
      frame.append(viewport,detail.querySelector('.assignment-middle-scroll'),pager);
      pager.setAttribute('total',visible.length);
      const paginate=()=>detail.querySelectorAll('tbody tr').forEach((row,i)=>row.hidden=i<(pager.page-1)*pager.pageSize||i>=pager.page*pager.pageSize);
      pager.addEventListener('page-change',paginate);paginate();
    }
  }
  customElements.define('assignment-board',AssignmentBoard);
})();
