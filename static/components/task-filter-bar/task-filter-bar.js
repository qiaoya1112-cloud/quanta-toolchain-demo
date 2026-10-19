const taskFilterAssetBase = new URL("../../pages/action-quality-check/assets/", document.currentScript?.src || location.href).href;

class TaskFilterBar extends HTMLElement {
  connectedCallback(){
    if(this.dataset.ready)return;this.dataset.ready="true";
    const suppliedForm=this.querySelector('form');
    if(suppliedForm && this.getAttribute('variant')==='grouped'){
      suppliedForm.classList.add('task-filter-groups');
      suppliedForm.querySelectorAll('details').forEach(group=>{
        group.classList.add('task-filter-group');
        const fields=group.querySelector('summary + div');
        if(fields){fields.classList.add('task-filter-group__fields');fields.style.setProperty('--group-columns',this.getAttribute('columns')||4);}
      });
      const query=()=>this.emit('filter-change',Object.fromEntries(new FormData(suppliedForm)));
      suppliedForm.addEventListener('value-change',query);
      suppliedForm.addEventListener('submit',event=>{event.preventDefault();query();});
      return;
    }
    if(suppliedForm){
      const grid=suppliedForm.querySelector(':scope > .task-filter-grid');
      if(grid) grid.replaceWith(...grid.children);
      suppliedForm.classList.add('task-filter-grid');
      this.addEventListener('filter-refresh',()=>suppliedForm.requestSubmit());
    } else this.renderFilters();
    if(this.getAttribute('variant')!=='grouped') this.setupLayout();
  }
  setupLayout(){
    const form=this.querySelector('form');
    if(!form)return;
    form.querySelector('.task-filter-bar__refresh')?.remove();
    const fields=document.createElement('div');
    fields.className='task-filter-fields';
    fields.append(...form.children);
    const count=fields.children.length;
    form.classList.add('task-filter-layout');
    form.classList.toggle('task-filter-layout--full',count>=6);
    form.style.setProperty('--filter-columns',Math.min(count,6));
    const actions=document.createElement('div');
    actions.className='task-filter-actions';
    actions.innerHTML=`<button class="task-filter-refresh" type="button" aria-label="刷新列表" title="刷新列表"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 5v5h-5M20 10a8 8 0 1 0-.6 5"/></svg></button>${count>6?'<button class="task-filter-expand" type="button" aria-expanded="false" aria-label="展开更多筛选" title="展开更多筛选"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></button>':''}`;
    form.append(fields,actions);
    actions.querySelector('.task-filter-refresh').addEventListener('click',()=>{
      const values=Object.fromEntries(new FormData(form));
      this.emit(this.getAttribute('variant')==='task-management'?'task-query':'filter-change',values);
      this.emit('filter-refresh',values);
    });
    actions.querySelector('.task-filter-expand')?.addEventListener('click',event=>{
      const expanded=form.classList.toggle('is-expanded');
      event.currentTarget.setAttribute('aria-expanded',String(expanded));
      const label=expanded?'收起更多筛选':'展开更多筛选';
      event.currentTarget.setAttribute('aria-label',label);
      event.currentTarget.title=label;
    });
  }
  renderFilters(){
    const variant=this.getAttribute('variant');
    if(variant==='grouped'){
      const input=(name,label,placeholder)=>`<form-input name="${name}" label="${label}" placeholder="${placeholder}"></form-input>`;
      const select=(name,label,options)=>`<form-select name="${name}" label="${label}"><option value="">不限</option>${options.map(value=>`<option>${value}</option>`).join('')}</form-select>`;
      const group=(title,fields,columns,open=true)=>`<details class="task-filter-group" ${open?'open':''}><summary>${title}</summary><div class="task-filter-group__fields" style="--group-columns:${columns}">${fields}</div></details>`;
      this.innerHTML=`<form class="task-filter-groups">${
        group('任务信息',input('taskId','任务 ID','请输入任务 ID')+input('taskName','任务名称','请输入任务名称')+input('project','所属项目','请输入所属项目'),3,false)+
        group('处理信息',select('qualityChecked','是否质检',['是','否'])+select('qualityResult','质检结论',['通过','不通过'])+select('annotated','是否标注',['是','否'])+input('annotationVersion','标注版本','留空默认最新版本'),4)+
        group('提示词',input('highlevel','Highlevel（模糊搜索）','输入关键词')+input('lowlevel','Lowlevel（模糊搜索）','输入关键词'),2)+
        group('导出要求',input('episodeLimit','Episode 上限','留空则不限制')+select('promptLanguage','Prompt 语言',['中文','英文']),2)
      }</form>`;
      const form=this.querySelector('form');
      const query=()=>this.emit('filter-change',Object.fromEntries(new FormData(form)));
      form.addEventListener('value-change',query);
      form.addEventListener('submit',event=>{event.preventDefault();query();});
      return;
    }

    if(variant==='workbench-pool'){
      this.innerHTML='<form class="task-filter-grid"><form-select name="flow" label="流程"><option value="">全部流程</option><option>端到端切分标注流程</option><option>预训练数据质检流程</option></form-select><form-select name="node" label="节点"><option value="">全部节点</option><option>供应商抽验</option><option>内部验收</option><option>采集质检</option><option>采集验收</option></form-select></form>';
      const form=this.querySelector('form');form.addEventListener('change',()=>this.emit('filter-change',Object.fromEntries(new FormData(form))));form.addEventListener('submit',e=>e.preventDefault());return;
    }
    if(variant==='annotation-todo'){
      this.innerHTML='<form class="task-filter-grid task-filter-grid--annotation"><form-input label="任务 ID" name="taskId" placeholder="请输入任务 ID"></form-input><form-select label="处理任务" name="task"><option value="">全部处理任务</option><option>端到端切分标注任务</option></form-select><form-select label="当前节点" name="node"><option value="">全部当前节点</option><option>供应商抽验</option><option>供应商复核</option><option>内部验收</option></form-select><form-input label="数据 ID" name="dataId" placeholder="请输入数据 ID"></form-input></form>';
      const form=this.querySelector('form');
      const query=()=>this.emit('filter-change',Object.fromEntries(new FormData(form)));
      form.addEventListener('input',event=>{if(!event.isComposing)query();});
      form.addEventListener('compositionend',query);
      form.addEventListener('change',query);
      form.addEventListener('submit',event=>{event.preventDefault();query();});
      return;
    }
    if(['project-management','user-group-management','supplier-management'].includes(variant)){
      const project=variant==='project-management';
      const label=project?'项目名称':variant==='user-group-management'?'用户组名称':'供应商名称';
      this.innerHTML=`<form class="task-filter-grid task-filter-grid--configuration"><form-input name="name" label="${label}" placeholder="请输入${label}"></form-input>${project?'<form-select name="owner" label="负责人"><option value="">全部负责人</option><option>Lance Li</option><option>Wei Zhang</option><option>Min Chen</option><option>Emma Wilson</option><option>Olivia Davis</option></form-select><form-select name="status" label="状态"><option value="">全部状态</option><option>启用</option><option>停用</option></form-select>':'<form-select name="scene" label="支持业务环节"><option value="">全部业务环节</option><option>标注</option><option>质检</option><option>验收</option></form-select>'}</form>`;
      const form=this.querySelector('form');
      const query=()=>this.emit('filter-change',Object.fromEntries(new FormData(form)));
      form.addEventListener('input',event=>{if(!event.isComposing)query();});
      form.addEventListener('compositionend',query);form.addEventListener('change',query);
      form.addEventListener('submit',event=>{event.preventDefault();query();});
      return;
    }
    if(['rule-management','workbench-management'].includes(variant)){
      const rule=variant==='rule-management';
      this.innerHTML=`<form class="task-filter-grid task-filter-grid--configuration"><form-input name="name" label="${rule?'规则名称':'工作台名称'}" placeholder="请输入${rule?'规则':'工作台'}名称"></form-input>${rule?'<form-select name="scene" label="适用环节"><option value="">全部环节</option><option>标注</option><option>质检</option><option>验收</option></form-select><form-input name="creator" label="创建人" placeholder="请输入创建人"></form-input>':''}</form>`;
      const form=this.querySelector('form');
      const query=()=>this.emit('filter-change',Object.fromEntries(new FormData(form)));
      form.addEventListener('input',event=>{if(!event.isComposing)query();});
      form.addEventListener('compositionend',query);form.addEventListener('change',query);
      form.addEventListener('submit',event=>{event.preventDefault();query();});
      return;
    }
    if(variant==='operator-management'){
      this.innerHTML='<form class="task-filter-grid task-filter-grid--assignment"><form-input name="name" label="算子名称" placeholder="请输入算子名称 / 标识"></form-input><form-select name="creator" label="创建人"><option value="">全部创建人</option><option>Emma Wilson</option></form-select></form>';
      const form=this.querySelector('form');
      const query=()=>this.emit('filter-change',Object.fromEntries(new FormData(form)));
      form.addEventListener('input',event=>{if(!event.isComposing)query();});
      form.addEventListener('compositionend',query);form.addEventListener('change',query);
      form.addEventListener('submit',event=>{event.preventDefault();query();});
      return;
    }
    if(['assignment-management','data-management'].includes(variant)){
      const input=(name,label,placeholder)=>`<form-input name="${name}" label="${label}" placeholder="${placeholder}"></form-input>`;
      const select=(name,label,placeholder,options=[],disabled=false)=>`<form-select name="${name}" label="${label}"${disabled?' disabled':''}><option value="">${placeholder}</option>${options.map(text=>`<option>${text}</option>`).join('')}</form-select>`;
      const tasks=['厨房数据质检','三方数据导入质检'];
      const qualityFlows=['厨房数据质检流程','多级质检复核流程','导入数据质检流程','标准训练数据自动质检流程'];
      const annotationFlows=['家居动作标注流程','端到端切分标注流程','双轮人工标注流程'];
      const assignment=variant==='assignment-management';
      this.innerHTML=`<form class="task-filter-grid${assignment?' task-filter-grid--assignment':''}">${assignment
        ?select('task','处理任务','全部处理任务',tasks)+select('node','节点','全部节点',[],true)
        :input('collectionId','采集任务 ID','请输入 6 位任务 ID')+input('processingId','处理任务 ID','请输入 6 位任务 ID')+select('qualityFlow','质检流程','全部',qualityFlows)+select('qualityNode','质检节点','请先选择质检流程',[],true)+select('annotationFlow','标注流程','全部',annotationFlows)+select('annotationNode','标注节点','请先选择标注流程',[],true)+input('dataId','数据 ID','请输入 6 位数据 ID')+input('currentAssignee','当前处理人','请输入当前处理人')+input('allAssignees','全部处理人','请输入历史处理人')+select('project','所属项目','全部项目',['预训练采集','demo 项目','宁德项目'])}</form>`;
      const form=this.querySelector('form');
      const links=assignment?[['task','node','全部节点',['供应商复核','格式校验']]]:[['qualityFlow','qualityNode','请先选择质检流程',['质检复核','人工质检','供应商抽验','内部验收']],['annotationFlow','annotationNode','请先选择标注流程',['供应商标注','供应商验收','标注完成','内部验收']]];
      form.addEventListener('change',event=>{
        const relation=links.find(([name])=>name===event.target.name);
        if(relation){
          const [,name,placeholder,options]=relation;
          const host=form.querySelector(`form-select[name="${name}"]`);
          const replacement=document.createElement('form-select');
          replacement.setAttribute('name',name);replacement.setAttribute('label',host.getAttribute('label'));
          if(!event.target.value)replacement.setAttribute('disabled','');
          replacement.innerHTML=`<option value="">${event.target.value?'全部节点':placeholder}</option>${event.target.value?options.map(text=>`<option>${text}</option>`).join(''):''}`;
          host.replaceWith(replacement);
        }
        this.emit('filter-change',Object.fromEntries(new FormData(form)));
      });
      form.addEventListener('input',event=>{if(!event.isComposing)this.emit('filter-change',Object.fromEntries(new FormData(form)));});
      form.addEventListener('submit',event=>event.preventDefault());
      return;
    }
    if(this.getAttribute('variant')==='task-management'){
      const select=(name,label,values)=>`<form-select name="${name}" label="${label}"><option value="">全部${label==='任务性质'?'':label}</option>${values.map(value=>`<option>${value}</option>`).join('')}</form-select>`;
      this.innerHTML=`<form class="task-filter-grid"><form-input name="id" label="任务 ID" placeholder="请输入任务 ID，多个英文逗号隔开"></form-input><form-input name="name" label="名称" placeholder="请输入名称"></form-input>${select('project','所属项目',['预训练采集','demo 项目','宁德项目'])}${select('flow','处理流程',['端到端切分标注流程','多级质检复核流程','双轮人工标注流程','标准训练数据自动质检流程'])}${select('processing','处理状态',['启用','停用'])}${select('published','任务状态',['已发布','未发布'])}${select('nature','任务性质',['正式','测试'])}<form-input name="creator" label="创建人" placeholder="请输入创建人"></form-input></form>`;
      const form=this.querySelector('form');
      const query=()=>this.emit('task-query',Object.fromEntries(new FormData(form)));
      form.addEventListener('submit',event=>{event.preventDefault();query();});
      form.addEventListener('input',event=>{if(!event.isComposing)query();});
      form.addEventListener('compositionend',query);
      form.addEventListener('change',query);
      return;
    }
    const process = this.getAttribute("variant") === "process-management";
    this.innerHTML=process
      ? `<form class="task-filter-bar task-filter-bar--process"><label><span>流程标识</span><input name="id" type="search" placeholder="请输入流程标识"></label><label><span>流程名称</span><input name="name" type="search" placeholder="请输入流程名称"></label><label><span>创建人</span><input name="creator" type="search" placeholder="请输入创建人"></label></form>`
      : `<form class="task-filter-bar"><label><span>ID搜索</span><input name="id" type="search" placeholder="请输入ID"></label><label><span>序列号</span><button type="button" data-field="serial">请选择设备序列号<img src="${taskFilterAssetBase}icon-list-chevron.svg" alt=""></button></label><label><span>ID搜索</span><button type="button" data-field="operator">请选择操作类型/操作人<img src="${taskFilterAssetBase}icon-list-chevron.svg" alt=""></button></label><button class="task-filter-bar__refresh" type="button" aria-label="刷新列表"><img src="${taskFilterAssetBase}icon-list-refresh.svg" alt=""></button></form>`;
    this.querySelector("input").addEventListener("input",event=>this.emit("filter-change",{id:event.target.value}));
    this.querySelectorAll("[data-field]").forEach(button=>button.addEventListener("click",()=>this.emit("filter-open",{field:button.dataset.field})));
    this.querySelector(".task-filter-bar__refresh")?.addEventListener("click",()=>this.emit("filter-refresh"));
    this.querySelector("form").addEventListener("submit",event=>event.preventDefault());
  }
  emit(name,detail={}){this.dispatchEvent(new CustomEvent(name,{bubbles:true,detail}));}
}
customElements.define("task-filter-bar",TaskFilterBar);
