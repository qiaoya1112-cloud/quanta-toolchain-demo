(() => {
  const options=values=>values.map(value=>`<option>${value}</option>`).join('');
  const select=(label,values,field='')=>`<form-select label="${label}" data-field="${field}">${options(values)}</form-select>`;
  const remove=label=>`<text-button variant="text" icon="delete" icon-only aria-label="${label}" data-remove></text-button>`;
  const projects=['预训练采集','demo 项目','宁德项目'];
  const suppliers=['光轮智能','千寻数据','供应商 A'];
  const groups=['质检复核用户组','内部验收用户组','标注用户组'];
  const flows={
    quality:[{name:'多级质检复核流程',version:'v3',nodes:['抽检复核','供应商复核','申诉复核']},{name:'标准训练数据自动质检流程',version:'v1',nodes:[]}],
    annotation:[{name:'端到端切分标注流程',version:'v2',nodes:['供应商抽验','供应商复核','供应商验收','内部验收'],auto:'端到端切分'},{name:'双轮人工标注流程',version:'v2',nodes:['第一轮标注','第二轮标注']}]
  };
  class TaskStepNav extends HTMLElement {
    connectedCallback(){
      this.innerHTML='<nav aria-label="新建任务步骤">'+(this.getAttribute('steps')?.split(',')||['基本信息','筛选条件','业务环节']).map((name,index)=>`<button type="button" data-step="${index}"><span>${index+1}</span>${name}</button>`).join('')+'</nav>';
      this.addEventListener('click',e=>{const button=e.target.closest('[data-step]');if(button)this.dispatchEvent(new CustomEvent('step-change',{bubbles:true,detail:Number(button.dataset.step)}));});this.active=0;
    }
    set active(index){this.querySelectorAll('button').forEach((button,i)=>{button.classList.toggle('is-active',i===index);if(i===index)button.setAttribute('aria-current','step');else button.removeAttribute('aria-current');});}
  }
  customElements.define('task-step-nav',TaskStepNav);
  class TaskFilterConditions extends HTMLElement {
    connectedCallback(){
      this.innerHTML='<div class="creator-notice form-feedback form-feedback--info" role="note"><span>满足筛选条件的数据将分批进入处理任务，每 30 分钟进入一批，每批最多 2000 条。</span></div><section class="creator-card"><div data-rows></div><p class="creator-empty">不限制：所有新入湖数据均可进入该任务</p><text-button variant="text" icon="plus" data-add>添加条件</text-button></section>';
      this.querySelector('[data-add]').addEventListener('click',()=>this.add());
    }
    add(){
      const row=document.createElement('div');row.className='creator-condition';
      row.innerHTML=select('筛选项',['所属项目','供应商','采集结论','数据 ID'],'field')+select('操作符',['等于','不等于','包含'],'operator')+'<div data-value></div>'+remove('删除条件');
      this.querySelector('[data-rows]').append(row);
      const sync=()=>{const field=row.querySelector('[data-field="field"]').value;row.querySelector('[data-value]').innerHTML=field==='数据 ID'?'<form-input label="值" placeholder="请输入数据 ID"></form-input>':select('值',field==='所属项目'?projects:field==='供应商'?suppliers:['成功','失败']);};
      row.querySelector('[data-field="field"]').addEventListener('change',sync);sync();
      row.querySelector('[data-remove]').addEventListener('click',()=>{row.remove();this.sync();});this.sync();
    }
    sync(){this.querySelector('.creator-empty').hidden=!!this.querySelector('[data-rows]').children.length;}
    get value(){return [...this.querySelectorAll('.creator-condition')].map(row=>({field:row.querySelector('[data-field="field"]').value,operator:row.querySelector('[data-field="operator"]').value,value:row.querySelector('[data-value] > *').value.trim()}));}
  }
  customElements.define('task-filter-conditions',TaskFilterConditions);
  class TaskNodeConfig extends HTMLElement {
    connectedCallback(){
      const inherited=this.hasAttribute('inherit');
      this.innerHTML='<article class="creator-node"><h4></h4><section class="creator-handler-section"><div class="creator-section-heading"><strong>处理人</strong><small>'+ (inherited?'继承前序节点':'多个处理人之间为竞争关系')+'</small></div><div data-assignees></div>'+ (inherited?'<p>继承供应商抽验节点</p>':'<text-button variant="text" icon="plus" data-add>添加处理人</text-button>')+'</section><div class="creator-rule">'+select('规则',this.getAttribute('stage')==='quality'?['通用质检规则 · v3','严格质检规则 · v1']:['端到端切分标注规则 · v1','通用标注规则 · v1'],'rule')+'</div></article>';
      this.querySelector('h4').textContent=this.getAttribute('heading');
      const badge=document.createElement('span');badge.className='creator-node-tag';badge.textContent='人工任务节点';this.querySelector('h4').append(badge);
      if(!inherited){this.add();this.querySelector('[data-add]').addEventListener('click',()=>this.add());}
    }
    add(){
      const row=document.createElement('div');row.className='creator-assignee';row.innerHTML=select('类型',this.getAttribute('stage')==='quality'?['用户组','供应商']:['供应商','用户组'],'type')+'<div data-person></div>'+remove('删除处理人');this.querySelector('[data-assignees]').append(row);
      const sync=()=>row.querySelector('[data-person]').innerHTML=select('处理人',row.querySelector('[data-field="type"]').value==='供应商'?suppliers:groups);row.querySelector('[data-field="type"]').addEventListener('change',sync);sync();row.querySelector('[data-remove]').addEventListener('click',()=>row.remove());
    }
    get value(){return {name:this.getAttribute('heading'),inherit:this.hasAttribute('inherit'),assignees:[...this.querySelectorAll('.creator-assignee')].map(row=>({type:row.querySelector('[data-field="type"]').value,name:row.querySelector('[data-person] form-select').value})),rule:this.querySelector('[data-field="rule"]').value};}
  }
  customElements.define('task-node-config',TaskNodeConfig);
  class TaskFlowPreview extends HTMLElement {
    set flow(flow){
      this.classList.add('process-editor-components');
      const canvas=document.createElement('process-flow-canvas');
      canvas.setAttribute('variant','preview');
      canvas.previewFlow=flow;
      this.replaceChildren(canvas);
    }
  }
  customElements.define('task-flow-preview',TaskFlowPreview);
  class TaskBusinessStages extends HTMLElement {
    connectedCallback(){
      this.innerHTML='<div class="creator-stages"><div class="creator-stage-list"></div><div class="creator-card creator-stage-detail"><div data-prompt></div><div data-details></div></div></div>';
      this.active=null;
      ['quality','annotation'].forEach((key,index)=>{
        const card=document.createElement('section');card.className='creator-card creator-stage-card';card.dataset.stage=key;
        card.innerHTML=`<div class="creator-stage-heading"><button type="button" data-select>${index?'标注':'质检'}环节</button><form-checkbox class="creator-switch" label="未开启"></form-checkbox></div><div data-picker hidden>${select('处理流程',flows[key].map(flow=>flow.name))}</div>`;
        this.querySelector('.creator-stage-list').append(card);
        const detail=document.createElement('div');detail.dataset.stageDetail=key;detail.hidden=true;this.querySelector('[data-details]').append(detail);
        card.querySelector('form-checkbox').addEventListener('change',()=>{const enabled=card.querySelector('form-checkbox').checked;card.querySelector('.form-choice span').textContent=enabled?'已开启':'未开启';card.querySelector('[data-picker]').hidden=!enabled;if(enabled){this.render(key);this.show(key);}else if(this.active===key){const other=['quality','annotation'].find(k=>this.enabled(k));this.show(other);}});
        card.querySelector('[data-select]').addEventListener('click',()=>{if(this.enabled(key))this.show(key);});
        card.querySelector('form-select').addEventListener('change',()=>{this.render(key);this.show(key);});
      });this.show(null);
      this.addEventListener('node-focus',e=>{const config=[...this.querySelectorAll(`[data-stage-detail="${this.active}"] task-node-config`)].find(node=>node.getAttribute('heading')===e.detail);config?.scrollIntoView({behavior:'smooth',block:'center'});config?.focus({preventScroll:true});});
    }
    enabled(key){return this.querySelector(`[data-stage="${key}"] form-checkbox`).checked;}
    render(key){
      const panel=this.querySelector(`[data-stage-detail="${key}"]`),name=this.querySelector(`[data-stage="${key}"] form-select`).value;
      if(panel.dataset.flow===name)return;panel.dataset.flow=name;const flow=flows[key].find(f=>f.name===name);
      panel.innerHTML='<h3></h3><section class="creator-flow"><div class="creator-section-heading"><strong>流程图</strong><small>点击人工任务节点定位下方节点配置</small></div><task-flow-preview></task-flow-preview></section><section class="creator-node-section"><div class="creator-section-heading"><strong>节点配置</strong><small>按节点配置处理人和规则</small></div><div data-nodes></div></section>';
      panel.querySelector('h3').textContent=`${flow.name}　${flow.version} · ${flow.nodes.length} 个人工任务节点`;panel.querySelector('task-flow-preview').flow=flow;
      flow.nodes.forEach((name,i)=>{const node=document.createElement('task-node-config');node.setAttribute('heading',name);node.setAttribute('stage',key);node.tabIndex=-1;if(key==='annotation'&&name==='供应商复核')node.setAttribute('inherit','');panel.querySelector('[data-nodes]').append(node);});
      if(!flow.nodes.length)panel.querySelector('[data-nodes]').innerHTML='<p class="creator-empty">该流程没有人工任务节点，无需配置节点。</p>';
    }
    show(key){this.active=key;this.querySelectorAll('[data-stage]').forEach(card=>card.classList.toggle('is-active',card.dataset.stage===key));this.querySelectorAll('[data-stage-detail]').forEach(panel=>panel.hidden=panel.dataset.stageDetail!==key);this.querySelector('[data-prompt]').hidden=!!key;if(!key)this.querySelector('[data-prompt]').innerHTML='<p class="creator-flow-hint">请选择左侧流程</p><section class="creator-node-section"><div class="creator-section-heading"><strong>节点配置</strong></div><p class="creator-empty">选择流程后，可在此配置人工任务节点。</p></section>';}
    get value(){return ['quality','annotation'].filter(key=>this.enabled(key)).map(key=>{const panel=this.querySelector(`[data-stage-detail="${key}"]`);return {stage:key==='quality'?'质检':'标注',flow:panel.dataset.flow,version:flows[key].find(f=>f.name===panel.dataset.flow).version,nodes:[...panel.querySelectorAll('task-node-config')].map(node=>node.value)};});}
  }
  customElements.define('task-business-stages',TaskBusinessStages);
  class TaskCreator extends HTMLElement {
    connectedCallback(){
      this.innerHTML=`<task-page-header title="新建处理任务" back back-label="返回任务处理"></task-page-header><div class="creator-layout"><task-step-nav></task-step-nav><main class="creator-main"><section data-panel="0"><h2>基本信息</h2><form class="creator-card creator-basic"><form-input label="任务名称" name="name" placeholder="请输入处理任务名称" data-required></form-input>${select('所属项目',projects,'project')}${select('任务性质',['正式','测试'],'nature')}<div>${select('优先级',['6','9','8','7','5','4','3','2','1'],'priority')}<p class="creator-hint">数字越大越先处理：1–3 低，4–6 中，7–9 高</p></div>${select('预期任务量',['持续任务','固定任务量'],'volume')}<form-input label="任务量" name="quantity" placeholder="请输入任务量" hidden></form-input></form></section><section data-panel="1" hidden><h2>筛选条件</h2><task-filter-conditions></task-filter-conditions></section><section data-panel="2" hidden><h2>业务环节</h2><task-business-stages></task-business-stages></section></main></div><footer class="creator-footer"><span role="alert"></span><text-button variant="outline" data-cancel>取消</text-button><text-button variant="primary" data-create>创建任务</text-button></footer>`;
      const basicForm=this.querySelector('.creator-basic');
      const basicFields=[...basicForm.children];
      [[0,2,4,5],[1,3]].forEach(indices=>{
        const column=document.createElement('div');column.className='creator-basic-column';
        indices.forEach(index=>column.append(basicFields[index]));basicForm.append(column);
      });
      this.querySelectorAll('.creator-basic form-select').forEach(el=>el.setAttribute('data-required',''));
      const name=this.querySelector('[name="name"] input');name.required=true;name.maxLength=100;
      const quantity=this.querySelector('[name="quantity"] input');quantity.type='number';quantity.min=1;quantity.step=1;quantity.disabled=true;
      this.querySelector('[data-field="volume"]').addEventListener('change',e=>{const fixed=this.querySelector('[data-field="volume"]').value==='固定任务量';quantity.closest('form-input').hidden=!fixed;quantity.required=fixed;quantity.disabled=!fixed;});
      const embedded=new URLSearchParams(location.search).get('embed')==='create-example';
      if(embedded){this.querySelector('[data-cancel]').hidden=true;this.querySelector('task-page-header .task-page-header__back')?.remove();}
      const back=()=>{if(!embedded)location.assign('./index.html');};this.addEventListener('header-back',back);this.querySelector('[data-cancel]').addEventListener('click',back);
      this.addEventListener('step-change',e=>this.show(e.detail));this.querySelector('[data-create]').addEventListener('click',()=>this.save());this.querySelector('form').addEventListener('submit',e=>{e.preventDefault();this.save();});
    }
    show(index){this.querySelector('task-step-nav').active=index;this.querySelectorAll('[data-panel]').forEach(panel=>panel.hidden=Number(panel.dataset.panel)!==index);this.querySelector('.creator-main').scrollTop=0;}
    save(){
      const name=this.querySelector('[name="name"] input');name.value=name.value.trim();
      const basic=this.querySelector('form');if(!basic.checkValidity()){this.show(0);basic.reportValidity();return;}
      const filters=this.querySelector('task-filter-conditions').value;const alert=this.querySelector('[role="alert"]');
      if(filters.some(filter=>!filter.value)){this.show(1);alert.textContent='请填写筛选条件的值';return;}
      const stages=this.querySelector('task-business-stages').value;
      if(!stages.length){this.show(2);alert.textContent='请至少开启一个业务环节';return;}
      if(stages.some(stage=>stage.nodes.some(node=>!node.inherit&&!node.assignees.length))){this.show(2);alert.textContent='请为人工任务节点添加处理人';return;}
      const field=key=>this.querySelector(`[data-field="${key}"]`).value;
      const task={id:String(Date.now()),name:name.value,project:field('project'),nature:field('nature'),priority:Number(field('priority')),volume:field('volume'),quantity:field('volume')==='固定任务量'?Number(this.querySelector('[name="quantity"]').value):null,filters,stages,createdAt:new Date().toLocaleString('sv-SE').slice(0,16)};
      try{const saved=JSON.parse(localStorage.getItem('quanta-processing-tasks')||'[]');saved.unshift(task);localStorage.setItem('quanta-processing-tasks',JSON.stringify(saved));if(new URLSearchParams(location.search).get('embed')==='create-example'){alert.textContent='任务已创建';}else{location.assign('./index.html?created='+task.id);}}catch{alert.textContent='保存失败，请检查浏览器存储设置后重试';}
    }
  }
  customElements.define('task-creator',TaskCreator);
})();
