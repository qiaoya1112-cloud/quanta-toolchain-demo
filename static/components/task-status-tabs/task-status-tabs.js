class TaskStatusTabs extends HTMLElement {
  connectedCallback() {
    if (this.dataset.ready) return;
    this.dataset.ready = "true";
    const layered = this.getAttribute('variant') === 'layered';
    const pills = this.getAttribute('variant') === 'dataset-scope' || this.getAttribute('appearance') === 'pills';
    const process = this.getAttribute('variant') === 'process';
    const datasetItems={'training-detail':[['checkpoint','Checkpoint'],['logs','日志'],['timeline','时间线'],['dashboard','实验看板'],['info','基础信息']],'training-kingsoft':[['checkpoint','Checkpoint']],'training-config':[['default','默认参数'],['overrides','参数覆盖']],'dataset-dimension':[['high','Highlevel 维度'],['low','Lowlevel 维度']],'dataset-information':[['summary','摘要信息'],['full','完整信息']],'plan-packages':[['imported','已导入指令包'],['available','可导入指令包']],'command-package':[['imported','已导入指令'],['available','可导入指令']],'task-view':[['todo','待办项'],['pool','任务池']],'command-management':[['commands','指令列表'],['approvals','指令审批']],'model-resources':[['metered','计量付费'],['dedicated','独占资源']],'model-scenes':[['scenes','场景库定义'],['elements','要素定义']],'model-query':[['fixed','固定筛选'],['sql','执行 SQL']],'model-source':[['self','自采数据'],['external','三方数据']],'model-cloud':[['volcano','火山云'],['kingsoft','金山云']],'dataset-scope':[['all','全部'],['mine','我创建的']],dataset:[['preview','数据预览'],['analysis','构成分析'],['versions','版本'],['info','基本信息']],episode:[['trajectory','轨迹信息'],['annotation','标注信息'],['visual','可视化分析']]};
    const items = datasetItems[this.getAttribute('variant')] || (layered ? [['todo','待办项'],['pool','任务池']] : this.getAttribute('variant')==='resources' ? [['suppliers','供应商'],['groups','用户组']] : this.getAttribute('variant')==='permissions' ? [['roles','角色管理'],['resources','资源管理'],['grants','授权管理']] : process ? [['settings','设置'],['recent','最近运行']] : [['pool','任务池'],['todo','待办项']]);
    this.innerHTML = `<div class="${pills ? 'task-status-subtabs' : 'task-status-tabs'}" role="tablist">${items.map(([value,label])=>`<button type="button" role="tab" data-value="${value}">${label}</button>`).join('')}</div>`;
    if (layered) {
      this.insertAdjacentHTML('beforeend', `<div class="task-status-subtabs" role="tablist" aria-label="任务状态"><button type="button" role="tab" data-sub-value="returned">驳回待处理</button><button type="button" role="tab" data-sub-value="review">修正待审核</button></div>`);
      this.setSubActive(this.getAttribute('sub-active') || 'review', false);
    }
    this.querySelector('[role=tablist]').setAttribute('aria-label', pills ? '目录范围' : '任务分类');
    this.addEventListener('keydown', event => {
      const button = event.target.closest('button[role="tab"]');
      if (!button || !['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
      const buttons = [...button.parentElement.querySelectorAll('button')];
      const index = buttons.indexOf(button);
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length;
      event.preventDefault();
      buttons[next].click();
      buttons[next].focus();
    });
    this.setActive(this.getAttribute("active") || items[0][0], false);
    this.addEventListener("click", event => { const button=event.target.closest("button[data-value]"); if(button) this.setActive(button.dataset.value,true); const sub=event.target.closest("button[data-sub-value]"); if(sub) this.setSubActive(sub.dataset.subValue,true); });
  }
  setSubActive(value, emit) {
    this.setAttribute('sub-active', value);
    this.querySelectorAll('button[data-sub-value]').forEach(button => {
      const selected = button.dataset.subValue === value;
      button.classList.toggle('is-active', selected);
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
    });
    if (emit) this.dispatchEvent(new CustomEvent('sub-tab-change', {bubbles:true, detail:{value, parentValue:this.getAttribute('active')}}));
  }
  setActive(value, emit) {
    this.setAttribute("active",value);
    this.querySelectorAll("button[data-value]").forEach(button=>{const selected=button.dataset.value===value;button.classList.toggle("is-active",selected);button.setAttribute("aria-selected",String(selected));button.tabIndex=selected?0:-1;});
    if(emit)this.dispatchEvent(new CustomEvent("tab-change",{bubbles:true,detail:{value}}));
  }
}
customElements.define("task-status-tabs",TaskStatusTabs);
