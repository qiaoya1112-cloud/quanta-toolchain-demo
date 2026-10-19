(() => {
  window.openPoolSetup=(flow,node)=>{
    const page=document.createElement('section');page.className='pool-setup task-page-frame';page.setAttribute('aria-label','开始处理配置');
    page.innerHTML=`<task-page-header title="开始处理" back></task-page-header><div class="pool-setup-body"><details class="task-filter-group" open><summary>基本信息</summary><dl class="pool-setup-info"><div><dt>流程</dt><dd data-flow></dd></div><div><dt>节点</dt><dd data-node></dd></div><div><dt>用户组</dt><dd>供应商 A</dd></div><div><dt>处理模式</dt><dd>单条处理</dd></div></dl></details><task-filter-bar variant="grouped"></task-filter-bar><div class="pool-claimed-notice"><span><strong>您有一条已领取的数据待完成。</strong> 开始处理将优先继续当前数据，完成后按筛选条件领取新数据。</span><text-button variant="outline" data-release>释放</text-button></div><div class="pool-setup-results" hidden></div></div><footer class="task-page-footer"><span role="status"></span><text-button variant="outline" icon="reset" icon-only aria-label="重置筛选" title="重置筛选" data-reset></text-button><text-button variant="primary" data-start>开始处理</text-button></footer>`;
    const workspace=document.querySelector('.page-workspace');const previous=[...workspace.children].map(el=>[el,el.hidden]);previous.forEach(([el])=>el.hidden=true);workspace.append(page);page.querySelector('[data-flow]').textContent=flow+' v2';page.querySelector('[data-node]').textContent=node;
    const form=page.querySelector('form');
    form.querySelector('details').outerHTML='<details class="task-filter-group" open><summary>筛选条件</summary><div class="task-filter-group__fields" style="--group-columns:3"><form-select name="rule" label="处理规则"><option value="">全部处理规则</option><option>端到端切分标注规则</option><option>采集质检规则</option></form-select><form-input name="processingTaskId" label="处理任务 ID" placeholder="请输入处理任务 ID"></form-input><form-input name="collectionTaskId" label="采集任务 ID" placeholder="请输入采集任务 ID"></form-input><form-input name="supplier" label="供应商" placeholder="请输入供应商"></form-input><form-input name="collector" label="采集员" placeholder="请输入采集员"></form-input><label class="pool-date-field">采集时间<input type="datetime-local" name="collectedFrom" aria-label="采集开始时间"></label><label class="pool-date-field">至<input type="datetime-local" name="collectedTo" aria-label="采集结束时间"></label></div></details>';
    form.querySelectorAll('details').forEach((group,index)=>{if(index>0)group.remove();});
    form.querySelector('.task-filter-group__fields').classList.add('pool-setup-filters');
    form.querySelector('.pool-setup-filters').append(page.querySelector('[data-reset]'));
    const feedback=page.querySelector('[role=status]'),results=page.querySelector('.pool-setup-results');
    const values=()=>Object.fromEntries(new FormData(form));
    const close=()=>{page.remove();previous.forEach(([el,hidden])=>el.hidden=hidden);document.querySelector('.task-pool [data-action="start"]')?.focus();};
    page.addEventListener('header-back',close);
    page.querySelector('[data-reset]').onclick=()=>{form.querySelectorAll('form-input,form-select').forEach(el=>el.value='');form.querySelectorAll('input[type="datetime-local"]').forEach(el=>el.value='');results.hidden=true;feedback.textContent='筛选条件已重置';};
    const releaseDialog=document.createElement('confirm-dialog');
    releaseDialog.setAttribute('heading','确认释放');
    releaseDialog.setAttribute('message','释放后，当前已领取的数据将返回任务池。');
    releaseDialog.setAttribute('confirm-label','确认释放');
    page.append(releaseDialog);
    page.querySelector('[data-release]').onclick=()=>releaseDialog.show();
    releaseDialog.addEventListener('confirm',()=>{page.querySelector('.pool-claimed-notice').hidden=true;feedback.textContent='已释放当前数据（演示操作）';});
    page.querySelector('[data-start]').onclick=()=>{
      const data=values();
      const url=new URL('../workbench/optimized.html',location.href);url.searchParams.set('flow',flow);url.searchParams.set('node',node);Object.entries(data).forEach(([key,value])=>{if(value)url.searchParams.set(key,value);});location.href=url.href;
    };
    page.querySelector('task-page-header button')?.focus();
  };
})();
