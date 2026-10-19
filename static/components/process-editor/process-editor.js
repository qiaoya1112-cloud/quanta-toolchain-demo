(() => {
  window.applyProcessNodeDefaultSummary=(node,label,workflow=false)=>{
    const summaries={'API Request':['GET','未配置接口地址'],'接口请求':['GET','未配置接口地址'],'Call Flow':['','未选择流程'],'调用流程':['','未选择流程'],'Human Interrupt':['','不限时 · 人工接管'],'人工接管':['','不限时 · 人工接管'],'Pose Set':['','工作点位 · VRMOV · 速度 0.2'],'位姿设置':['','工作点位 · VRMOV · 速度 0.2'],Navigation:['','未配置导航目标'],'导航':['','未配置导航目标']};
    if(!workflow&&['Human Interrupt','人工接管','人工节点'].includes(label)){node.querySelectorAll('.graph-sub').forEach(sub=>sub.remove());return;}
    const summary=workflow&&['Omini Model','Omni Model','自动化节点','全能模型'].includes(label)?['','待配置']:summaries[label==='人工节点'?'Human Interrupt':label];if(!summary)return;
    node.querySelectorAll('.graph-sub').forEach(sub=>sub.remove());
    const heading=node.querySelector('.graph-title');let text=node.querySelector('.node-text');
    if(!text){text=document.createElement('div');text.className='node-text';heading.replaceWith(text);text.append(heading);}
    const sub=document.createElement('div');sub.className='graph-sub';
    if(summary[0]){const method=document.createElement('b');method.className='node-request-method';method.textContent=summary[0];sub.append(method,' ');}
    sub.append(summary[1]);text.append(sub);
  };
  const nodeNames=window.processNodeNames={Start:'开始',start:'开始',End:'结束',Condition:'条件分支',Loop:'循环','Variable Assignment':'变量赋值','API Request':'接口请求','Call Flow':'调用流程','Human Interrupt':'人工接管','Pose Set':'位姿设置',Navigation:'导航','Omini Model':'全能模型','Omni Model':'全能模型',Delay:'延时','Wait For Input':'等待输入',RAG:'检索增强',Memory:'记忆',Function:'函数','WORKFLOW PRIMITIVE':'流程基础节点','ROBOT / AI CAPABILITY':'机器人 / AI 能力'};
  nodeNames['Human Interrupt']='人工节点';
  nodeNames['Omini Model']=nodeNames['Omni Model']='自动化节点';
  const assets = new URL('../../pages/process-editor/assets/', document.currentScript.src);
  class WorkflowSectionHeading extends HTMLElement {
    connectedCallback(){
      this.classList.add('workflow-section-heading');
      if(this.children.length)return;
      const title=document.createElement('h3');title.textContent=this.getAttribute('heading')||'';this.append(title);
      if(this.hasAttribute('description')){const description=document.createElement('p');description.className='interrupt-hint';description.textContent=this.getAttribute('description');this.append(description);}
    }
  }
  customElements.define('workflow-section-heading',WorkflowSectionHeading);
  class WorkflowOutputVariables extends HTMLElement {
    set items(value){this._items=Array.isArray(value)?value:[];if(this.isConnected)this.render();}
    get items(){return this._items||[];}
    connectedCallback(){this.render();}
    render(){
      this.replaceChildren();
      const section=document.createElement('section');section.className='api-output';
      const header=document.createElement('workflow-section-heading');
      if(!this.items.length){
        const title=document.createElement('h3');title.textContent='输出变量';
        const empty=document.createElement('p');empty.className='interrupt-hint';empty.textContent='暂无已配置的输出变量';
        header.append(title,empty);section.append(header);this.append(section);return;
      }
      const heading=document.createElement('button');heading.type='button';heading.className='workflow-output-toggle';heading.textContent='输出变量';header.append(heading);section.append(header);
      heading.insertAdjacentHTML('beforeend','<svg class="workflow-output-chevron" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true" focusable="false"><path d="M4 6 L8 10 L12 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>');
      let content;
      if(this.items.length){
        const list=document.createElement('dl');
        this.items.forEach(({name,type,description})=>{const term=document.createElement('dt');term.append(name||'');const badge=document.createElement('small');badge.textContent=type||'';term.append(' ',badge);const detail=document.createElement('dd');detail.textContent=description||'';list.append(term,detail);});section.append(list);content=list;
      }else{const empty=document.createElement('p');empty.className='interrupt-hint';empty.textContent='暂无已配置的输出变量';header.append(empty);content=empty;}
      const sync=()=>{const expanded=this._expanded??!this.hasAttribute('collapsed');heading.setAttribute('aria-expanded',String(expanded));content.hidden=!expanded;};
      heading.addEventListener('click',()=>{this._expanded=!(this._expanded??!this.hasAttribute('collapsed'));sync();});sync();
      this.append(section);
    }
  }
  customElements.define('workflow-output-variables',WorkflowOutputVariables);
  class WorkflowAddButton extends HTMLElement {
    connectedCallback(){
      if(this.firstElementChild)return;
      this.classList.add('start-properties__add');
      const button=document.createElement('text-button');button.setAttribute('variant','outline');
      button.textContent=`＋ ${this.getAttribute('label')||'添加并行节点'}`;this.append(button);
      this.addEventListener('click',()=>this.dispatchEvent(new CustomEvent(this.getAttribute('action')||'node-add-parallel',{bubbles:true,detail:{nodeId:this.closest('workflow-next-step')?.getAttribute('source-id')||'start'}})));
    }
  }
  customElements.define('workflow-add-button',WorkflowAddButton);
  // Render a panel region with its original components and event handlers intact.
  class WorkflowPanelPart extends HTMLElement {
    connectedCallback(){
      if(this.firstElementChild)return;
      const panel=document.createElement('process-node-properties');
      panel.setAttribute('variant',this.getAttribute('variant')||'start');
      this.append(panel);
      const target=panel.querySelector(this.getAttribute('selector')||'.interrupt-heading');
      if(!target)return;
      target.classList.add('panel-part-target');
      let branch=target;
      while(branch!==panel){
        const parent=branch.parentElement;
        for(const sibling of parent.children)if(sibling!==branch)sibling.classList.add('panel-part-hidden');
        parent.classList.add('panel-part-path');branch=parent;
      }
    }
  }
  customElements.define('workflow-panel-part',WorkflowPanelPart);
  class WorkflowNextStep extends HTMLElement {
    connectedCallback(){
      if(this.firstElementChild)return;
      if(this.hasAttribute('empty')){
        this.innerHTML='<div class="workflow-next-step-empty interrupt-hint">该节点没有后续出口</div>';
        return;
      }
      if(this.hasAttribute('unconnected')){
        this.innerHTML=`<div class="start-properties__next"><h4>循环完成后</h4><div class="start-properties__branch"><span class="start-properties__source condition-source"><img src="${assets}loop.svg" alt=""></span><workflow-add-button label="添加后续节点" action="node-add-next"></workflow-add-button></div></div>`;
        const sourceIcon={pose:'pose',navigation:'nav',automation:'omini',variable:'variable'}[this.getAttribute('source-type')];
        if(sourceIcon){this.querySelector('h4').textContent='下一步';const source=this.querySelector('.start-properties__source');source.classList.remove('condition-source');source.classList.add('workflow-pose-source');source.querySelector('img').src=`${assets}${sourceIcon}.svg`;}
        return;
      }
      this.innerHTML=`<div class="start-properties__next"><h4>下一步</h4><div class="start-properties__branch"><span class="start-properties__source"><img src="${assets}start.svg" alt=""></span><div class="start-properties__targets"><button type="button" class="start-properties__target"><span class="node-icon purple"><img src="${assets}api.svg" alt=""></span><span><strong></strong><small></small></span><span class="start-properties__chevron">›</span></button><workflow-add-button></workflow-add-button></div></div></div>`;
      this.querySelector('strong').textContent=this.getAttribute('target-name')||'获取京东订单';
      this.querySelector('small').textContent=this.getAttribute('target-type')||'接口请求';
      if(this.getAttribute('source-type')==='api'){this.querySelector('.start-properties__source img').src=`${assets}api.svg`;this.querySelector('.start-properties__source').classList.add('api-successor-source');}
      if(this.getAttribute('target-icon')==='variable'){this.querySelector('.node-icon').className='node-icon yellow';this.querySelector('.node-icon img').src=`${assets}variable-yellow.svg`;}
      if(this.getAttribute('source-type')==='human'){this.querySelector('.start-properties__source img').src=`${assets}human.svg`;this.querySelector('.start-properties__source').classList.add('workflow-human-source');}
      if(this.getAttribute('target-icon')==='condition'){this.querySelector('.node-icon').className='node-icon blue';this.querySelector('.node-icon img').src=`${assets}condition-fix.svg`;}
      this.querySelector('.start-properties__target').addEventListener('click',()=>this.dispatchEvent(new CustomEvent('node-select',{bubbles:true,detail:{nodeId:this.getAttribute('target-id')||'get'}})));
    }
  }
  customElements.define('workflow-next-step',WorkflowNextStep);
  class WorkflowParameterField extends HTMLElement {
    connectedCallback(){
      if(this.childElementCount||!this.field)return;
      const [key,label,value,hint,required,placeholder]=this.field;
      this.classList.add('workflow-human-field');
      if(['workpoint_name','gripper_positions','timeout_s'].includes(key))this.classList.add('workflow-pose-wide');
      const head=document.createElement('div');head.className='api-section-heading';
      const code=document.createElement('strong');code.textContent=label;
      const status=document.createElement('small');status.className='interrupt-hint';status.textContent=required?'必填':'可选';head.append(code,status);
      const input=document.createElement('form-input');input.setAttribute('aria-label',label);input.setAttribute('name',key);input.setAttribute('value',value);
      if(placeholder)input.setAttribute('placeholder',placeholder);
      const note=document.createElement('p');note.className='interrupt-hint';note.textContent=hint;
      this.append(head,input,note);
      const control=input.querySelector('input');control.required=!!required;
      if(['jog_vel','jog_acc','timeout_s','max_retries','retry_interval_s'].includes(key)){
        control.type='number';control.min='0';control.step=key==='max_retries'?'1':'any';
        if(key.startsWith('jog_'))control.max='1';
        if(key==='timeout_s'){control.max='300';control.addEventListener('input',()=>control.setCustomValidity(control.value!==''&&Number(control.value)<=0?'超时时间必须大于 0':''));}
        if(key==='retry_interval_s')control.max='60';
      }
    }
  }
  customElements.define('workflow-parameter-field',WorkflowParameterField);
  // Shared editable field collections: all controls come from the component library.
  class WorkflowFieldCollection extends HTMLElement {
    connectedCallback(){
      if(this.childElementCount)return;
      const kind=this.getAttribute('kind')||'inputs';
      const config={inputs:['自定义输入','为当前节点声明可复用的输入参数','添加'],assignments:['赋值规则','从固定值、全局参数、Flow 输入或可达上游输出取值','添加赋值'],outputs:['结构化输出','仅当 target 使用 outputs.<name> 时声明','添加输出字段']}[kind];
      this.innerHTML=`<section><workflow-section-heading><div class="start-properties__label"><h3>${config[0]}</h3><span data-count>0</span></div><p class="interrupt-hint">${config[1]}</p></workflow-section-heading><div data-collection-rows></div><text-button variant="text" icon="plus" data-collection-add>${config[2]}</text-button></section>`;
      this.querySelector('[data-collection-add]').addEventListener('click',()=>{this.addRow();this.changed();});
      if(kind==='outputs'){
        const warning=document.createElement('p');warning.className='workflow-navigation-warning';warning.hidden=true;warning.textContent='输出字段名必须是合法标识符，并选择支持的数据类型';this.querySelector('[data-collection-add]').before(warning);
      }
      this.addEventListener('input',()=>this.changed());
      this.addEventListener('change',()=>this.changed());
    }
    get value(){return [...this.querySelectorAll('[data-collection-row]')].map(row=>Object.fromEntries([...row.querySelectorAll('form-input,form-select')].map(control=>[control.getAttribute('name'),control.value])));}
    set value(rows){this.querySelector('[data-collection-rows]').replaceChildren();(rows||[]).forEach(row=>this.addRow(row));this.sync();}
    sync(){const rows=[...this.querySelector('[data-collection-rows]').children];this.querySelector('[data-count]').textContent=rows.length;rows.forEach((row,index)=>{const number=row.querySelector('[data-assignment-index]');if(number)number.textContent=index+1;});}
    changed(){
      if(this.getAttribute('kind')==='outputs'){
        const rows=this.value;const names=rows.map(row=>row.name);
        this.querySelector('.workflow-navigation-warning').hidden=!rows.some(row=>!/^[_a-zA-Z][_a-zA-Z0-9]*$/.test(row.name)||names.filter(name=>name===row.name).length>1||!row.type);
        const output=this.closest('process-node-properties')?.querySelector('workflow-output-variables');if(output)output.items=rows.filter(row=>/^[_a-zA-Z][_a-zA-Z0-9]*$/.test(row.name));
      }
      this.dispatchEvent(new CustomEvent('workflow-fields-change',{bubbles:true,detail:{kind:this.getAttribute('kind'),value:this.value}}));
    }
    addRow(values={}){
      const kind=this.getAttribute('kind');
      const row=document.createElement('div');row.className='workflow-human-input';row.setAttribute('data-collection-row','');
      const fields=kind==='assignments'?'<form-input name="target" label="目标变量" placeholder="输入状态变量路径或 outputs.name"></form-input><form-select name="source" label="取值方式"><option value="fixed">固定值</option><option value="global">全局参数</option><option value="flow">Flow 输入</option><option value="upstream">上游输出</option></form-select><form-input name="value" label="固定值" placeholder="输入值"></form-input>':'<form-input name="name" label="'+(kind==='outputs'?'输出名称':'输入名称')+'" placeholder="输入名称"></form-input><form-select name="type" label="类型"><option value="string">string</option><option value="number">number</option><option value="boolean">boolean</option><option value="array">array</option><option value="object">object</option></form-select><form-input name="'+(kind==='outputs'?'description':'defaultValue')+'" label="'+(kind==='outputs'?'描述':'默认值')+'" placeholder="可选"></form-input>';
      row.innerHTML=fields+'<text-button variant="text" icon="delete" aria-label="删除条目" data-collection-remove>×</text-button>';
      this.querySelector('[data-collection-rows]').append(row);
      if(kind!=='assignments'){
        const types=kind==='inputs'?'<option value="string">字符串</option><option value="number">数字</option><option value="boolean">布尔值</option><option value="array">列表</option><option value="object">字典</option>':'<option>string</option><option>int</option><option>float</option><option>bool</option><option>list</option><option>dict</option>';
        row.innerHTML=`<div class="workflow-field-row"><form-input name="name" label="${kind==='outputs'?'字段名':'输入名称'}" placeholder="${kind==='outputs'?'task_summary':'输入名称'}"></form-input><form-select name="type" label="类型">${types}</form-select>${kind==='inputs'?'<form-select name="source" label="取值方式"><option value="fixed">固定值</option><option value="variable">变量</option></form-select>':''}</div>${kind==='inputs'?'<form-input name="value" label="固定值" placeholder="请输入字符串"></form-input>':''}<text-button variant="text" aria-label="删除条目" data-collection-remove>×</text-button>`;
        if(kind==='inputs'&&values.name===undefined){let index=1;const names=this.value.map(item=>item.name);while(names.includes(`input_${index}`))index++;row.querySelector('[name="name"]').value=`input_${index}`;}
      }
      row.querySelectorAll('form-input,form-select').forEach(control=>{if(values[control.getAttribute('name')]!==undefined)control.value=values[control.getAttribute('name')];});
      if(kind==='inputs'){
        const source=row.querySelector('[name="source"]'),type=row.querySelector('[name="type"]');
        const update=()=>{const value=row.querySelector('[name="value"]');const label=source.value==='fixed'?'固定值':'变量';value.querySelector('.form-input__label').textContent=label;value.querySelector('input').setAttribute('aria-label',label);value.querySelector('input').placeholder=source.value==='fixed'?{string:'请输入字符串',number:'请输入数字',boolean:'true / false',array:'请输入列表',object:'请输入字典'}[type.value]:'输入变量路径';};
        source.addEventListener('change',update);type.addEventListener('change',update);update();
      }
      if(kind==='assignments'){
        row.className='workflow-case workflow-assignment';
        row.innerHTML='<div class="workflow-case__heading"><span data-assignment-index></span><strong>变量赋值</strong><text-button variant="text" aria-label="删除赋值" data-collection-remove>×</text-button></div><div class="workflow-assignment__fields"><div class="workflow-assignment__target"><form-input name="target" label="目标变量" placeholder="输入目标变量"></form-input><form-select name="type" label="数据类型"><option value="string">string</option><option value="int">int</option><option value="float">float</option><option value="bool">bool</option><option value="list">list</option><option value="dict">dict</option></form-select><form-select name="source" label="右值模式"><option value="expression">表达式</option><option value="fixed">直接赋值</option><option value="global">全局参数</option><option value="flow">Flow 输入</option><option value="upstream">上游输出</option></form-select></div><div class="workflow-assignment__value"><form-input name="value" label="表达式" placeholder="输入表达式"></form-input><div class="workflow-assignment__insert"><button type="button" data-insert-variable><span aria-hidden="true">{x}</span> 插入变量</button></div></div></div>';
        row.querySelectorAll('form-input,form-select').forEach(control=>{if(values[control.getAttribute('name')]!==undefined)control.value=values[control.getAttribute('name')];});
        const heading=row.querySelector('.workflow-case__heading');
        row.append(heading.querySelector('[data-collection-remove]'));
        heading.remove();
        const source=row.querySelector('[name="source"]');
        const type=row.querySelector('[name="type"]');
        const update=()=>{const value=row.querySelector('[name="value"]');const label=source.value==='expression'?'表达式':source.value==='fixed'?'固定值':'变量路径';value.querySelector('.form-input__label').textContent=label;value.querySelector('input').setAttribute('aria-label',label);value.querySelector('input').placeholder=source.value==='fixed'?({dict:'例如 {"count": 1}',list:'例如 [1, 2]',bool:'true / false',int:'例如 1',float:'例如 0.2'}[type.value]||'输入值'):source.value==='expression'?'例如 {{workflow.visit}} + 1':'输入变量路径';row.querySelector('.workflow-assignment__insert').hidden=source.value!=='expression';};
        source.addEventListener('change',update);type.addEventListener('change',update);update();
        row.querySelector('[data-insert-variable]').addEventListener('click',()=>{
          const control=row.querySelector('[name="value"]'),input=control.querySelector('input');
          const start=input.selectionStart??input.value.length,end=input.selectionEnd??start,token='{{变量}}';
          control.value=input.value.slice(0,start)+token+input.value.slice(end);
          input.focus();input.setSelectionRange(start+2,start+token.length-2);this.changed();
        });
      }
      row.querySelector('[data-collection-remove]').addEventListener('click',()=>{row.remove();this.sync();this.changed();});this.sync();
    }
  }
  customElements.define('workflow-field-collection',WorkflowFieldCollection);
  class WorkflowConditionRule extends HTMLElement {
    connectedCallback(){
      if(this.childElementCount)return;
      this.innerHTML='<div class="workflow-condition-rule"><div class="workflow-condition-rule__operand"><div class="workflow-condition-rule__source"><form-select label="取值方式" aria-label="左值类型"><option>变量</option><option>固定值</option></form-select><text-button variant="outline" data-not>NOT</text-button></div><form-input label="变量 / 左值" aria-label="条件变量" value="order_status"></form-input></div><div class="workflow-condition-rule__operand"><form-select label="操作符" aria-label="比较运算符"><option>=</option><option>!=</option><option>&gt;</option><option>&lt;</option><option>包含</option></form-select><form-select label="比较值类型" aria-label="右值类型"><option>固定值</option><option>变量</option></form-select><form-input label="比较值" aria-label="比较值"></form-input></div></div>';
      this.querySelectorAll('form-input')[1].value=this.getAttribute('value')||'';
      const remove=document.createElement('text-button');remove.setAttribute('variant','text');remove.setAttribute('aria-label','删除条件');remove.className='workflow-condition-rule__remove';remove.textContent='×';this.querySelector('.workflow-condition-rule').append(remove);remove.addEventListener('click',()=>this.remove());
      const not=this.querySelector('[data-not]');not.setAttribute('aria-pressed','false');not.addEventListener('click',()=>{const active=not.getAttribute('aria-pressed')!=='true';not.setAttribute('aria-pressed',active);not.setAttribute('variant',active?'secondary':'outline');});
    }
  }
  customElements.define('workflow-condition-rule',WorkflowConditionRule);
  const templates = {
  "process-editor-page": "<div class=\"editor-page process-editor-components\">\n    <aside class=\"editor-page__sidebar\"><platform-sidebar collapsed></platform-sidebar></aside>\n\n    <main class=\"workspace\">\n      <process-editor-header></process-editor-header>\n\n      <div class=\"body\">\n        <process-node-library></process-node-library>\n\n        <process-flow-canvas></process-flow-canvas>\n\n        <process-node-properties></process-node-properties>\n      </div>\n    </main>\n    <div class=\"toast\" role=\"status\" aria-live=\"polite\"></div>\n  </div>",
  "process-editor-header": "<header class=\"header\">\n        <img class=\"back\" src=\"assets/header-icon.svg\" alt=\"\">\n        <div class=\"divider\"></div>\n        <div class=\"title-block\"><h1>端到端切分标注流程</h1><p>v0.1-draft · 草稿 · 未保存变更</p></div>\n        <process-actions class=\"header-actions\"></process-actions>\n      </header>",
  "process-node-library": "<aside class=\"left-panel\">\n          <section class=\"flow-list\">\n            <search-input placeholder=\"搜索并聚焦 Flow\"></search-input>\n            <div class=\"flow-section\">\n              <div class=\"flow-head\"><div class=\"flow-label\"><img src=\"assets/chevron.svg\" alt=\"\"><span>正常流程</span><span>0/0</span></div><div class=\"flow-icons\"><img src=\"assets/add.svg\" alt=\"\"><img src=\"assets/layers.svg\" alt=\"\"></div></div>\n              <div class=\"main-flow\"><span>主流程</span><span><img src=\"assets/eye.svg\" alt=\"\" style=\"width:16px;vertical-align:middle;margin-right:12px\"><img src=\"assets/more.svg\" alt=\"\" style=\"width:16px;vertical-align:middle\"></span></div>\n            </div>\n            <div class=\"flow-section\" style=\"margin-top:0\"><div class=\"flow-head\"><div class=\"flow-label\"><img src=\"assets/chevron.svg\" alt=\"\"><span>异常流程</span><span>0/0</span></div><div class=\"flow-icons\"><img src=\"assets/add.svg\" alt=\"\"><img src=\"assets/layers.svg\" alt=\"\"></div></div></div>\n          </section>\n          <section class=\"palette\">\n            <div class=\"palette-group\">\n              <div class=\"group-head\"><img src=\"assets/chevron.svg\" alt=\"\"><span>流程控制</span><span class=\"count\">7</span></div>\n              <div class=\"palette-item\"><span class=\"node-icon green\"><img src=\"assets/start.svg\" alt=\"\"></span>Start</div>\n              <div class=\"palette-item\"><span class=\"node-icon gray\"><img src=\"assets/end.svg\" alt=\"\"></span>End</div>\n              <div class=\"palette-item\"><span class=\"node-icon blue\"><img src=\"assets/condition-fix.svg\" alt=\"\"></span>Condition</div>\n              <div class=\"palette-item\"><span class=\"node-icon mint\"><img src=\"assets/loop.svg\" alt=\"\"></span>Loop</div>\n              <div class=\"palette-item\"><span class=\"node-icon yellow\"><img src=\"assets/delay.svg\" alt=\"\"></span>Delay</div>\n              <div class=\"palette-item\"><span class=\"node-icon pink\"><img src=\"assets/wait.svg\" alt=\"\"></span>Wait For Input</div>\n              <div class=\"palette-item\"><span class=\"node-icon pink2\"><img src=\"assets/human.svg\" alt=\"\"></span>Human Interrupt</div>\n            </div>\n            <div class=\"palette-group\">\n              <div class=\"group-head\"><img src=\"assets/chevron.svg\" alt=\"\"><span>API、知识与数据</span><span class=\"count\">8</span></div>\n              <div class=\"palette-item\"><span class=\"node-icon purple\"><img src=\"assets/api.svg\" alt=\"\"></span>API Request</div>\n              <div class=\"palette-item\"><span class=\"node-icon purple\"><img src=\"assets/rag.svg\" alt=\"\"></span>RAG</div>\n              <div class=\"palette-item\"><span class=\"node-icon purple\"><img src=\"assets/memory.svg\" alt=\"\"></span>Memory</div>\n              <div class=\"palette-item\"><span class=\"node-icon purple\"><img src=\"assets/database.svg\" alt=\"\"></span>数据表查询</div>\n              <div class=\"palette-item\"><span class=\"node-icon purple\"><img src=\"assets/extract.svg\" alt=\"\"></span>参数提取</div>\n              <div class=\"palette-item\"><span class=\"node-icon purple\"><img src=\"assets/variable.svg\" alt=\"\"></span>Variable Assignment</div>\n              <div class=\"palette-item\"><span class=\"node-icon purple\"><img src=\"assets/variable.svg\" alt=\"\"></span>文本模板</div>\n              <div class=\"palette-item\"><span class=\"node-icon purple\"><img src=\"assets/function.svg\" alt=\"\"></span>Function</div>\n            </div>\n            <div class=\"palette-group\">\n              <div class=\"group-head\"><img src=\"assets/chevron.svg\" alt=\"\"><span>机器人技能</span><span class=\"count\">4</span></div>\n              <div class=\"palette-item\"><span class=\"node-icon green\"><img src=\"assets/nav.svg\" alt=\"\"></span>精准导航</div>\n              <div class=\"palette-item\"><span class=\"node-icon green\"><img src=\"assets/pose.svg\" alt=\"\"></span>位姿调整</div>\n              <div class=\"palette-item\"><span class=\"node-icon green\"><img src=\"assets/gripper.svg\" alt=\"\"></span>夹爪开合</div>\n              <div class=\"palette-item\"><span class=\"node-icon green\"><img src=\"assets/omini.svg?v=2\" alt=\"\"></span>Omini Model</div>\n            </div>\n          </section>\n        </aside>",
  "process-flow-canvas": "<section class=\"canvas\">\n          <div class=\"canvas-stage\" data-zoom=\"0.7\" data-pan-x=\"30\" data-pan-y=\"260\">\n            <div class=\"canvas-viewport\">\n              <svg class=\"edge-layer\" viewBox=\"0 0 1600 560\" aria-hidden=\"true\">\n                <defs>\n                  <marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"8.5\" refY=\"5\" markerWidth=\"4.5\" markerHeight=\"4.5\" orient=\"auto-start-reverse\">\n                    <path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#90a1b9\"></path>\n                  </marker>\n                </defs>\n              </svg>\n\n              <div class=\"scene\">\n                <div class=\"graph-node start-main\" data-node=\"start\" style=\"left:40px;top:90px\">\n                  <img src=\"assets/start.svg\" alt=\"\" style=\"width:12px;height:12px\">\n                  <div class=\"node-text\"><div class=\"graph-title\">京东项目 MVP</div><div class=\"graph-sub\">流程入口</div></div>\n                  <span class=\"port\" style=\"right:-4px;top:15px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"wait\" style=\"left:200px;top:90px\">\n                  <span class=\"mini pink\"><img src=\"assets/wait.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">Wait For Input</div><div class=\"graph-sub\">未配置路径</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:15px\"></span>\n                  <span class=\"port\" style=\"right:-4px;top:15px\"></span>\n                </div>\n\n                <div class=\"loop-box\">\n                  <div class=\"loop-title\">\n                    <span class=\"node-icon mint\" style=\"width:20px;height:20px\"><img src=\"assets/loop.svg\" alt=\"\" style=\"width:12px;height:12px\"></span>\n                    循环区域\n                    <span class=\"loop-chip\">Loop</span>\n                  </div>\n                  <div class=\"loop-stage\"></div>\n                </div>\n\n                <div class=\"graph-node\" data-node=\"nav-grasp\" style=\"left:376px;top:56px\">\n                  <span class=\"mini green\"><img src=\"assets/nav.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">精准导航</div><div class=\"graph-sub\">抓取点位</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:16px\"></span><span class=\"port\" style=\"right:-4px;top:16px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"pose\" style=\"left:376px;top:99px\">\n                  <span class=\"mini green\"><img src=\"assets/pose.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">位姿调整</div><div class=\"graph-sub\">抓取前位姿 init</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:16px\"></span><span class=\"port\" style=\"right:-4px;top:16px\"></span>\n                </div>\n                <div class=\"graph-node selected\" data-node=\"grasp\" style=\"left:376px;top:143px\">\n                  <span class=\"mini green\"><img src=\"assets/omini.svg?v=2\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">京东-SKU抓取</div><div class=\"graph-sub\">Spirit-v1.6 · 94%</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:15px\"></span><span class=\"port\" style=\"right:-4px;top:15px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"human-1\" style=\"left:533px;top:56px\">\n                  <span class=\"mini pink2\"><img src=\"assets/human.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">Human Interrupt</div><div class=\"graph-sub\">等待人工接管</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:16px\"></span><span class=\"port\" style=\"right:-4px;top:16px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"scan\" style=\"left:533px;top:129px\">\n                  <span class=\"mini green\"><img src=\"assets/omini.svg?v=2\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">京东-SKU扫码</div><div class=\"graph-sub\">Spirit-v1.6 · 91%</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:16px\"></span><span class=\"port\" style=\"right:-4px;top:16px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"human-2\" style=\"left:690px;top:56px\">\n                  <span class=\"mini pink2\"><img src=\"assets/human.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">Human Interrupt</div><div class=\"graph-sub\">等待人工接管</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:16px\"></span><span class=\"port\" style=\"right:-4px;top:16px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"condition\" style=\"left:690px;top:128px\">\n                  <span class=\"mini blue\"><img src=\"assets/condition-fix.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">IF/ELSE</div><div class=\"graph-sub\">CASE 1</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:17px\"></span><span class=\"port\" style=\"right:-4px;top:17px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"nav-place-1\" style=\"left:847px;top:56px;width:126px\">\n                  <span class=\"mini green\"><img src=\"assets/nav.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">精准导航</div><div class=\"graph-sub\">放置点位 1（槽位 1、2、4、5、7、8）</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:16px\"></span><span class=\"port\" style=\"right:-4px;top:16px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"nav-place-2\" style=\"left:847px;top:129px;width:126px\">\n                  <span class=\"mini green\"><img src=\"assets/nav.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">精准导航</div><div class=\"graph-sub\">放置点位 2（槽位 3、6、9）</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:16px\"></span><span class=\"port\" style=\"right:-4px;top:16px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"place\" style=\"left:1004px;top:94px\">\n                  <span class=\"mini green\"><img src=\"assets/omini.svg?v=2\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">京东-SKU放置</div><div class=\"graph-sub\">Spirit-v1.6 · 93%</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:16px\"></span><span class=\"port\" style=\"right:-4px;top:8px\"></span><span class=\"port\" style=\"right:-4px;top:24px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"human-3\" style=\"left:1160px;top:56px\">\n                  <span class=\"mini pink2\"><img src=\"assets/human.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">Human Interrupt</div><div class=\"graph-sub\">等待人工接管</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:16px\"></span><span class=\"port\" style=\"right:-4px;top:16px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"continue\" style=\"left:1160px;top:129px\">\n                  <span class=\"mini mint\"><img src=\"assets/loop.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">Continue</div><div class=\"graph-sub\">进入当前 Loop 下一轮</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:16px\"></span><span class=\"port\" style=\"right:-4px;top:16px\"></span>\n                </div>\n                <div class=\"graph-node\" data-node=\"end\" style=\"left:1337px;top:93px;width:129px\">\n                  <span class=\"mini gray\"><img src=\"assets/end.svg\" alt=\"\"></span>\n                  <div class=\"node-text\"><div class=\"graph-title\">End</div><div class=\"graph-sub\">End</div></div>\n                  <span class=\"port\" style=\"left:-4px;top:14px\"></span>\n                </div>\n              </div>\n            </div>\n          </div>\n          <process-canvas-tools></process-canvas-tools>\n          <div class=\"minimap\"><div class=\"minimap-frame\"><img src=\"assets/minimap.svg\" alt=\"\"></div></div>\n          <process-canvas-zoom></process-canvas-zoom>\n        </section>",
  "process-node-properties": "<aside class=\"right-panel\">\n          <div class=\"prop-head\"><div class=\"avatar\"><img src=\"assets/omini.svg?v=2\" alt=\"\"></div><div class=\"prop-title\"><h2>京东-SKU抓取</h2><p>添加备注</p></div><div class=\"prop-tools\"><button><img src=\"assets/toolbar-icon-1.svg\" alt=\"\"></button><button><img src=\"assets/toolbar-icon-2.svg\" alt=\"\"></button><button><img src=\"assets/toolbar-icon-3.svg\" alt=\"\"></button></div></div>\n          <task-status-tabs variant=\"process\" active=\"settings\"></task-status-tabs>\n          <div class=\"panel-scroll\" data-tab=\"settings\">\n            <section class=\"section\"><h3>Omini Model 能力</h3><div class=\"cap-card\"><div class=\"avatar\"><img src=\"assets/omini.svg?v=2\" alt=\"\"></div><div class=\"cap-info\"><strong>京东-SKU抓取</strong><span>Spirit-v1.6 · 仓储拣选 · p-sku-grasp-v4</span></div><div class=\"replace\">更换</div></div><p class=\"desc\">能力引用、Slot 与 Prompt 会随节点一起保存，运行时只读取这里的结构化配置。</p></section>\n            <section class=\"section\"><h3>模型与Prompt</h3><form-input class=\"field\" label=\"模型路径\" name=\"model\" value=\"Spirit-v1.6\"></form-input><form-input class=\"field\" label=\"代码分支\" name=\"branch\" placeholder=\"可选，例如 release/v1.6\"></form-input><form-input class=\"field\" label=\"Prompt\" name=\"prompt\" multiline></form-input></section>\n            <section class=\"section\"><div class=\"section-heading\"><h3>能力参数</h3><span class=\"badge\">1/3</span></div><div class=\"field\"><div class=\"slot-label\"><strong>SKU 形态</strong><span>sku_shape · 必填</span></div><div class=\"input\">rectangular box</div></div><div class=\"field\"><div class=\"slot-label\"><strong>来源槽位</strong><span>source_slot · 必填</span></div><div class=\"input\">A1</div></div><div class=\"field\"><div class=\"slot-label\"><strong>执行手</strong><span>hand · 必填</span></div><div class=\"input\">right<img src=\"assets/dropdown-icon.svg\" alt=\"\" style=\"width:16px;height:16px\"></div></div><div class=\"warning\"><img src=\"assets/warning-icon.svg\" alt=\"\">还有必填参数未配置：SKU 形态、来源槽位</div></section>\n          </div>\n          <div class=\"panel-scroll\" data-tab=\"recent\"><div class=\"recent-empty\">暂无运行记录</div></div>\n        </aside>",
  "process-canvas-tools": "<div class=\"toolbar-left\">\n            <button class=\"tool-btn\" title=\"选择\"><img src=\"assets/cursor.svg\" alt=\"\"></button>\n            <button class=\"tool-btn active\" data-action=\"hand\" title=\"拖拽平移\"><img src=\"assets/hand-tool.svg\" alt=\"\"></button>\n            <button class=\"tool-btn\" data-action=\"undo\" title=\"撤销\"><img src=\"assets/undo.svg\" alt=\"\"></button>\n            <button class=\"tool-btn\" data-action=\"redo\" title=\"重做\"><img src=\"assets/redo.svg\" alt=\"\"></button>\n          </div>",
  "process-canvas-zoom": "<div class=\"zoom\">\n            <button class=\"zoom-btn\" data-action=\"zoom-out\"><img src=\"assets/zoom-minus.svg\" alt=\"\"></button>\n            <div class=\"zoom-text\">70%</div>\n            <button class=\"zoom-btn\" data-action=\"zoom-in\"><img src=\"assets/zoom-plus.svg\" alt=\"\"></button>\n          </div>"
};
  function panelActions(panel) {
    panel.querySelectorAll('.api-properties__body>.workflow-navigation-warning').forEach(warning=>{
      const content=warning.previousElementSibling;
      if(!content)return;
      const group=document.createElement('div');group.className='workflow-validation-group';
      content.before(group);group.append(content,warning);
    });
    panel.querySelectorAll('.api-properties__body>section').forEach(section=>{
      if(section.querySelector(':scope>h3')?.textContent.trim()!=='输出变量')return;
      const output=document.createElement('workflow-output-variables');
      output.items=[...section.querySelectorAll('dt')].map(term=>({name:term.firstChild?.textContent.trim()||'',type:term.querySelector('small')?.textContent||'',description:term.nextElementSibling?.textContent||''}));
      section.replaceWith(output);
    });
    panel.querySelectorAll('.interrupt-content section,.interrupt-content.start-properties__body').forEach(section=>{
      const title=section.querySelector(':scope>h3,:scope>.api-section-heading,:scope>.start-properties__label');
      const description=title?.nextElementSibling;
      if(!title||!description?.matches('p.interrupt-hint'))return;
      const heading=document.createElement('workflow-section-heading');
      title.before(heading);heading.replaceChildren(title,description);
    });
    panel.querySelectorAll('.api-custom-inputs').forEach(section=>{
      const title=section.querySelector('.api-section-heading');
      const add=title?.querySelector('text-button');
      const rows=section.querySelector('[data-human-inputs],[data-custom-rows],[data-rows="custom"]');
      if(!add||!rows)return;
      title.classList.add('start-properties__label');
      const count=document.createElement('span');count.setAttribute('data-input-count','');
      title.append(count);
      const fields=document.createElement('div');fields.className='workflow-custom-input-fields';
      rows.before(fields);fields.append(rows,add);add.classList.add('form-add-action');
      const updateCount=()=>{
        count.textContent=rows.children.length;
        [...rows.children].forEach((row,index)=>{
          if(row.classList.contains('custom-input-card'))return;
          const inputs=[...row.querySelectorAll('form-input')],name=inputs[0],value=inputs[1],remove=row.querySelector('text-button');
          if(!name||!value||!remove)return;
          row.classList.add('custom-input-card');
          name.setAttribute('label','输入名称');
          if(!name.value)name.value='input_'+(index+1);
          let nameLabel=name.querySelector('.form-input__label');if(!nameLabel){nameLabel=document.createElement('span');nameLabel.className='form-input__label';name.querySelector('.form-input').prepend(nameLabel);}nameLabel.textContent='输入名称';name.querySelector('input')?.setAttribute('aria-label','输入名称');
          const top=document.createElement('div');top.className='custom-input-card__top';top.append(name,remove);
          const options=document.createElement('div');options.className='custom-input-card__options';
          options.innerHTML='<form-select name="source" label="取值方式"><option value="fixed">固定值</option><option value="variable">变量</option></form-select><form-select name="type" label="类型"><option value="string">字符串</option><option value="number">数字</option><option value="boolean">布尔值</option><option value="array">列表</option><option value="object">字典</option></form-select>';
          const field=document.createElement('label');field.className='custom-input-card__value';
          const caption=document.createElement('span');caption.textContent='固定值';
          const textarea=document.createElement('textarea');textarea.rows=3;textarea.value=value.value||'';textarea.placeholder='支持 string / number / boolean / array / object';
          textarea.addEventListener('input',()=>{value.value=textarea.value;value.dispatchEvent(new Event('change',{bubbles:true}));});
          value.hidden=true;field.append(caption,textarea);
          row.replaceChildren(top,options,field,value);
          options.querySelector('[name=source]').addEventListener('change',event=>{
            const variable=options.querySelector('[name=source]').value==='variable';
            caption.textContent=variable?'变量':'固定值';textarea.placeholder=variable?'输入变量路径':'支持 string / number / boolean / array / object';
          });
        });
      };
      updateCount();
      new MutationObserver(updateCount).observe(rows,{childList:true});
    });
    const surface=panel.querySelector('.right-panel');
    if(surface&&!surface.querySelector('.panel-resize-handle')){
      const handle=document.createElement('div');handle.className='panel-resize-handle';
      handle.tabIndex=0;handle.setAttribute('role','separator');handle.setAttribute('aria-orientation','vertical');handle.setAttribute('aria-label','调整面板宽度');handle.title='拖动调整宽度（320–640px）';
      const limits=()=>({min:Math.min(320,window.innerWidth-24),max:Math.min(640,window.innerWidth-24)});
      const resize=width=>{const {min,max}=limits();const next=Math.max(min,Math.min(max,width));surface.style.width=`${next}px`;handle.setAttribute('aria-valuemin',min);handle.setAttribute('aria-valuemax',max);handle.setAttribute('aria-valuenow',Math.round(next));};
      let drag=null;
      handle.addEventListener('pointerdown',event=>{if(event.button!==0)return;event.preventDefault();event.stopPropagation();drag={x:event.clientX,width:surface.getBoundingClientRect().width};handle.setPointerCapture(event.pointerId);});
      handle.addEventListener('pointermove',event=>{if(drag){event.preventDefault();resize(drag.width+drag.x-event.clientX);}});
      const finish=()=>{drag=null;};
      handle.addEventListener('pointerup',finish);handle.addEventListener('pointercancel',finish);handle.addEventListener('lostpointercapture',finish);
      handle.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const {min,max}=limits();resize(event.key==='Home'?min:event.key==='End'?max:surface.getBoundingClientRect().width+(event.key==='ArrowLeft'?16:-16));});
      surface.append(handle);
      handle.setAttribute('aria-valuemin','320');handle.setAttribute('aria-valuemax','640');handle.setAttribute('aria-valuenow',Math.round(surface.getBoundingClientRect().width));
    }
    const header=panel.querySelector('.interrupt-heading,.human-properties-header,.prop-head,.condition-panel__head,.start-properties__head');
    if(!header)return;
    if(header.querySelector('.panel-header-actions'))return;
    if(!header.querySelector('p')){const title=header.querySelector('h2');if(title){const description=document.createElement('p');title.after(description);}}
    for(const [selector,field,label] of [['h2','name','节点名称'],['p','description','节点描述']]){
      const text=header.querySelector(selector);if(!text)continue;
      text.contentEditable='plaintext-only';text.dataset.headerField=field;text.classList.add('panel-header-editable');
      if(field==='description'){text.dataset.placeholder='添加描述';text.setAttribute('aria-placeholder','添加描述');}
      text.setAttribute('role','textbox');text.setAttribute('aria-label',label);text.setAttribute('aria-multiline','false');text.tabIndex=0;text.title=`点击编辑${label}`;
      text.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.isComposing){event.preventDefault();text.blur();}});
      text.addEventListener('blur',()=>{text.textContent=text.textContent.replace(/[\r\n]+/g,' ').trim();});
    }
    panel.addEventListener('input',event=>{
      if(!event.target.matches('input[name="nodeName"],input[name="name"],textarea[name="description"],[data-header-field]'))return;
      const isDescription=(event.target.dataset.headerField||event.target.name)==='description';
      const value=event.target.dataset.headerField?event.target.textContent:event.target.value;
      if(!event.target.dataset.headerField){
        const heading=header.querySelector(isDescription?'p':'h2');
        if(heading)heading.textContent=value;
      }
      const owner=panel.closest('process-node-properties')||panel;
      const nodeId=owner.dataset.nodeId;
      const root=owner.closest('process-editor-page')||owner.closest('main')||document;
      const node=nodeId&&[...root.querySelectorAll('.graph-node[data-node]')].find(item=>item.dataset.node===nodeId);
      if(node){
        let text=node.querySelector(isDescription?'.graph-sub':'.graph-title');
        if(!text&&isDescription){text=document.createElement('div');text.className='graph-sub';node.querySelector('.graph-title')?.after(text);}
        if(text){text.textContent=value;text.title=value;text.hidden=!value;}
      }
      owner.dispatchEvent(new CustomEvent('node-properties-change',{bubbles:true,detail:{nodeId,field:isDescription?'description':'name',value}}));
    });
    const old=header.querySelector('.prop-tools');
    const close=header.querySelector('[data-close],[data-property-action="close"]')||document.createElement('button');
    if(!close.parentElement)close.addEventListener('click',()=>{close.closest('.right-panel,.condition-panel').style.display='none';close.dispatchEvent(new CustomEvent('node-properties-close',{bubbles:true}));});
    close.type='button';close.setAttribute('aria-label','关闭属性面板');close.title='关闭';
    close.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="m6 6 12 12M18 6 6 18"/></svg>';
    const group=document.createElement('div');group.className='panel-header-actions';
    const more=document.createElement('button');more.type='button';more.title='定位节点';more.setAttribute('aria-label','定位节点');
    more.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/><circle cx="12" cy="12" r="3"/></svg>';
    more.addEventListener('click',()=>panel.dispatchEvent(new CustomEvent('node-properties-locate',{bubbles:true,detail:{nodeId:panel.dataset.nodeId}})));
    group.append(more,close);old?.remove();header.append(group);
  }
  function bindDescription(panel, selector) {
    const trigger=panel.querySelector(selector);
    if(!trigger)return;
    trigger.textContent='添加描述';trigger.tabIndex=0;trigger.setAttribute('role','button');trigger.setAttribute('aria-label','编辑节点描述');
    const field=()=>panel.querySelector('textarea[name="description"]');
    const edit=()=>{const input=field();if(input){input.scrollIntoView({block:'nearest',behavior:'smooth'});input.focus({preventScroll:true});}};
    trigger.addEventListener('click',edit);
    trigger.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();edit();}});
    panel.addEventListener('input',event=>{if(event.target===field()){trigger.textContent=event.target.value.trim()||'添加描述';trigger.title=event.target.value.trim();}});
  }
  window.applyProcessPanelActions=panelActions;
  function basicPalette() {
    return `<div class="palette-group">${[['green','start.svg','开始节点'],['pink2','human.svg','人工节点'],['green','omini.svg','自动化节点'],['blue','condition-fix.svg','条件节点'],['gray','end.svg','结束节点']].map(([color, icon, label]) => `<div class="palette-item"><span class="node-icon ${color}"><img src="${assets}${icon}" alt=""></span>${label}</div>`).join('')}</div>`;
  }
  for (const [name, template] of Object.entries(templates)) {
    if (customElements.get(name)) continue;
    customElements.define(name, class extends HTMLElement {
      set previewFlow(flow) {
        this._previewFlow = flow;
        if (this.isConnected) this.renderPreview();
      }
      renderPreview() {
        if (name !== 'process-flow-canvas') return;
        const source = document.createElement('template');
        source.innerHTML = template.replace(/src="assets\//g, 'src="' + assets.href);
        const flow = this._previewFlow || {nodes:[]};
        const items = [{type:'start',title:'start',description:'Start'},
          ...(flow.auto ? [{type:'scan',title:flow.auto,description:'自动化节点'}] : []),
          ...flow.nodes.map(title=>({type:'human-1',title,description:'人工任务节点'})),
          {type:'end',title:'end',description:'End'}];
        const canvas = document.createElement('section');
        canvas.className = 'canvas process-preview-canvas';
        canvas.style.width = `${items.length * 270 - 30}px`;
        const edges = document.createElementNS('http://www.w3.org/2000/svg','svg');
        edges.classList.add('process-preview-edges');
        edges.setAttribute('aria-hidden','true');
        canvas.append(edges);
        items.forEach((item,index)=>{
          const node = source.content.querySelector(`[data-node="${item.type}"]`).cloneNode(true);
          node.removeAttribute('style');
          node.style.left = `${24 + index * 270}px`;
          node.style.top = '82px';
          node.dataset.node = `preview-${index}`;
          node.querySelector('.graph-title').textContent = item.title;
          node.querySelector('.graph-sub').textContent = item.description;
          node.querySelectorAll('.port').forEach(port=>{port.style.top='50%';port.style.transform='translateY(-50%)';});
          const icon = node.querySelector(':scope > img');
          if (icon) {icon.style.width='23px';icon.style.height='23px';}
          if(item.type==='human-1') {
            node.tabIndex=0;node.setAttribute('role','button');node.setAttribute('aria-label',`配置${item.title}`);
            const focus=()=>this.dispatchEvent(new CustomEvent('node-focus',{bubbles:true,detail:item.title}));
            node.addEventListener('click',focus);
            node.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();focus();}});
          }
          canvas.append(node);
          if(index) {
            const path=document.createElementNS('http://www.w3.org/2000/svg','path');
            path.classList.add('edge');
            path.setAttribute('d',`M ${24+(index-1)*270+210} 110 H ${24+index*270}`);
            edges.append(path);
          }
        });
        this.replaceChildren(canvas);
      }
      connectedCallback() {
        if(name==='process-flow-canvas' && this.getAttribute('variant')==='preview'){this.renderPreview();return;}
        if (this.dataset.rendered) return;
        this.dataset.rendered = 'true';
        if(name==='process-node-properties'&&this.getAttribute('variant')==='workflow-variable'){
          this.innerHTML=`<aside class="right-panel interrupt-properties api-properties"><header class="interrupt-heading"><span class="node-icon blue"><img src="${assets}variable.svg" alt=""></span><div class="start-properties__title"><h2>变量赋值</h2><p>写入 Workflow 状态变量</p></div></header><div class="interrupt-content api-properties__body"><workflow-field-collection kind="inputs"></workflow-field-collection><workflow-field-collection kind="assignments"></workflow-field-collection><workflow-field-collection kind="outputs"></workflow-field-collection><section><workflow-section-heading heading="后续节点" description="由画布连线自动生成"></workflow-section-heading><workflow-next-step source-id="variable" source-type="variable" unconnected></workflow-next-step></section></div></aside>`;
          const output=document.createElement('workflow-output-variables');
          this.querySelector('workflow-field-collection[kind="outputs"]').after(output);
          panelActions(this);return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='workflow-automation'){
          this.innerHTML=`<aside class="right-panel interrupt-properties api-properties"><header class="interrupt-heading"><span class="node-icon green"><img src="${assets}omini.svg" alt=""></span><div class="start-properties__title"><h2>自动化节点</h2><p>选择 Omni Model 能力与资源</p></div></header><div class="interrupt-content api-properties__body"><section class="api-custom-inputs"><div class="api-section-heading"><h3>自定义输入</h3><text-button variant="text" icon="plus" data-automation-add>添加</text-button></div><p class="interrupt-hint">为当前节点声明可复用的输入参数</p><div data-custom-rows></div><p class="api-empty">暂无自定义输入</p></section><section><h3>输入配置</h3><form-input label="Policy Path · 必填" name="policy_path" placeholder="/models/vla/model.pt"></form-input><form-input label="Prompt · 必填" name="prompt" multiline placeholder="可使用 {{custom_input}}"></form-input></section><section><h3>执行限制</h3><div class="api-retries"><form-input label="最短执行时间（秒）" name="min_duration" placeholder="未配置"></form-input><form-input label="超时时间（秒）" name="timeout_s" placeholder="阻塞等待"></form-input><form-input label="最大重试次数" name="max_retries" value="0"></form-input><form-input label="重试间隔（秒）" name="retry_interval_s" value="0"></form-input></div></section><section><h3>中断控制</h3><form-input name="monitor" aria-label="中断控制" multiline placeholder="配置 observers、rules 与 default_action"></form-input><p class="interrupt-hint">对应 YAML monitor；留空表示不配置中断监控。</p></section><p class="workflow-navigation-warning" role="status">Policy Path 与 Prompt 均为必填项。</p><section><h3>输出变量</h3><p class="interrupt-hint">暂无已配置的输出变量</p></section><section><h3>后续节点</h3><p class="interrupt-hint">由画布连线自动生成</p><workflow-next-step source-id="automation" source-type="automation" unconnected></workflow-next-step></section></div></aside>`;
          const required=[this.querySelector('[name="policy_path"] input'),this.querySelector('[name="prompt"] textarea')];
          required.forEach(input=>{input.required=true;input.addEventListener('input',()=>{this.querySelector('.workflow-navigation-warning').hidden=required.every(control=>control.value.trim());});});
          for(const key of ['min_duration','timeout_s','max_retries','retry_interval_s']){const input=this.querySelector(`[name="${key}"] input`);input.type='number';input.min='0';input.step=key==='max_retries'?'1':'any';}
          this.querySelector('[data-automation-add]').addEventListener('click',()=>{const row=document.createElement('div');row.className='api-pair';row.innerHTML='<form-input placeholder="输入名称"></form-input><form-input placeholder="默认值"></form-input><text-button variant="text" aria-label="删除输入">×</text-button>';this.querySelector('[data-custom-rows]').append(row);this.querySelector('.api-empty').hidden=true;row.querySelector('text-button').addEventListener('click',()=>{row.remove();this.querySelector('.api-empty').hidden=!!this.querySelector('[data-custom-rows]').children.length;});});
          panelActions(this);return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='workflow-navigation'){
          this.innerHTML=`<aside class="right-panel interrupt-properties api-properties"><header class="interrupt-heading"><span class="node-icon green"><img src="${assets}nav.svg" alt=""></span><div class="start-properties__title"><h2>导航</h2><p>绑定地图和目标点位</p></div></header><div class="interrupt-content api-properties__body"><section><form-select label="选择点位" name="targetPoint"><option value="" selected disabled hidden>请选择点位</option><option value="point_a">point_a</option><option value="point_a1">point_a1</option><option value="point_a2">point_a2</option><option value="point_b">point_b</option><option value="point_b1">point_b1</option><option value="point_b2">point_b2</option><option value="point_c">point_c</option><option value="point_c1">point_c1</option></form-select><form-select label="速度" name="speed"><option value="slow">低速</option><option value="medium" selected>中速</option><option value="fast">高速</option></form-select></section><section class="workflow-human-field"><h3>超时与重试</h3><div class="api-timeouts"><form-input label="超时时间（秒）" name="timeout" value="60"></form-input><form-input label="重试次数" name="retries" value="0"></form-input><form-input label="重试间隔（秒）" name="interval" value="0"></form-input></div></section><p class="workflow-navigation-warning" role="status">请选择点位。</p><section><h3>输出变量</h3><p class="interrupt-hint">暂无已配置的输出变量</p></section><section><h3>后续节点</h3><p class="interrupt-hint">由画布连线自动生成</p><workflow-next-step source-id="navigation" source-type="navigation" unconnected></workflow-next-step></section></div></aside>`;
          const navigationHeading=document.createElement('workflow-section-heading');
          navigationHeading.setAttribute('heading','导航配置');
          this.querySelector('.api-properties__body > section').prepend(navigationHeading);
          const pointSelect=this.querySelector('[name="targetPoint"] select');
          pointSelect.required=true;
          const validate=()=>{this.querySelector('.workflow-navigation-warning').hidden=!!pointSelect.value;};
          pointSelect.addEventListener('change',validate);
          validate();
          for(const key of ['timeout','retries','interval']){const input=this.querySelector(`[name="${key}"] input`);input.type='number';input.min='0';input.step=key==='retries'?'1':'any';}
          panelActions(this);return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='workflow-pose'){
          this.innerHTML=`<aside class="right-panel interrupt-properties api-properties"><header class="interrupt-heading"><span class="node-icon green"><img src="${assets}pose.svg" alt=""></span><div class="start-properties__title"><h2>位姿设置</h2><p>移动到机器人已注册的工作点位</p></div></header><div class="interrupt-content api-properties__body"><section class="api-custom-inputs"><div class="api-section-heading"><h3>自定义输入</h3><text-button variant="text" icon="plus" data-pose-add>添加</text-button></div><p class="interrupt-hint">为当前节点声明可复用的输入参数</p><div data-custom-rows></div><p class="api-empty">暂无自定义输入</p></section><section><h3>输入配置</h3><p class="interrupt-hint">对应 Pose Set workpoint 节点的 YAML 输入字段</p><div class="workflow-pose-fields"></div></section><section><h3>输出变量</h3><p class="interrupt-hint">暂无已配置的输出变量</p></section><section><h3>后续节点</h3><p class="interrupt-hint">由画布连线自动生成</p><workflow-next-step source-id="pose" source-type="pose" unconnected></workflow-next-step></section></div></aside>`;
          const fields=[['workpoint_name','工作点位名称','VRMOV','string · 机器人底层注册的非空工作点位名称，默认 VRMOV。',true],['gripper_positions','夹爪位置','','list[float] | None · 每项范围 [0, 100]，数量需与末端执行器自由度一致。',false,'留空表示不改变，例如 0, 80'],['jog_vel','移动速度','0.2','float · 范围 [0, 1]，默认 0.2。'],['jog_acc','加速度','0.2','float · 范围 [0, 1]，默认 0.2。'],['timeout_s','超时时间（秒）','','float | None · 取值范围 (0, 300]，留空时持续等待。',false,'留空表示阻塞等待'],['max_retries','重试次数','0','int · 非负整数，0 表示只执行一次。'],['retry_interval_s','重试间隔（秒）','0','float · 范围 [0, 60]，默认 0.0。']];
          fields.forEach(field=>{const card=document.createElement('workflow-parameter-field');card.field=field;this.querySelector('.workflow-pose-fields').append(card);});
          this.querySelector('[data-pose-add]').addEventListener('click',()=>{const row=document.createElement('div');row.className='api-pair';row.innerHTML='<form-input placeholder="输入名称"></form-input><form-input placeholder="默认值"></form-input><text-button variant="text" aria-label="删除输入">×</text-button>';this.querySelector('[data-custom-rows]').append(row);this.querySelector('.api-empty').hidden=true;row.querySelector('text-button').addEventListener('click',()=>{row.remove();this.querySelector('.api-empty').hidden=!!this.querySelector('[data-custom-rows]').children.length;});});
          panelActions(this);return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='workflow-loop'){
          this.innerHTML=`<aside class="right-panel interrupt-properties api-properties"><header class="interrupt-heading"><span class="node-icon mint"><img src="${assets}loop.svg" alt=""></span><div class="start-properties__title"><h2>循环</h2><p>按次数重复执行容器内节点</p></div></header><div class="interrupt-content api-properties__body"><section class="api-custom-inputs"><div class="api-section-heading"><h3>自定义输入</h3><text-button variant="text" icon="plus" data-loop-add>添加</text-button></div><p class="interrupt-hint">为当前节点声明可复用的输入参数</p><div data-custom-rows></div><p class="api-empty">暂无自定义输入</p></section><section><h3>输入配置</h3><p class="interrupt-hint">仅配置 Loop 节点的 YAML 输入字段</p><div class="workflow-human-field"><form-select label="循环模式 · 必填" name="loopMode"><option value="repeat">按次数</option></form-select></div><div class="workflow-human-field"><span class="form-input__label">重复次数 · 必填</span><div class="workflow-loop-count"><form-select aria-label="次数取值方式"><option value="fixed">固定值</option><option value="variable">变量</option></form-select><form-input aria-label="重复次数" value="1"></form-input></div></div></section><section><h3>后续节点</h3><p class="interrupt-hint">由画布连线自动生成</p><workflow-next-step source-id="loop" source-type="loop" unconnected></workflow-next-step></section></div></aside>`;
          const count=this.querySelector('.workflow-loop-count');const configure=()=>{const variable=count.querySelector('form-select').value==='variable';const input=count.querySelector('input');input.type=variable?'text':'number';if(variable){input.removeAttribute('min');input.removeAttribute('step');input.placeholder='输入变量路径';input.value='';}else{input.min='1';input.step='1';input.value='1';}input.required=true;};configure();count.querySelector('form-select').addEventListener('change',configure);
          this.querySelector('[data-loop-add]').addEventListener('click',()=>{const row=document.createElement('div');row.className='api-pair';row.innerHTML='<form-input placeholder="输入名称"></form-input><form-input placeholder="默认值"></form-input><text-button variant="text" aria-label="删除输入">×</text-button>';this.querySelector('[data-custom-rows]').append(row);this.querySelector('.api-empty').hidden=true;row.querySelector('text-button').addEventListener('click',()=>{row.remove();this.querySelector('.api-empty').hidden=!!this.querySelector('[data-custom-rows]').children.length;});});
          panelActions(this);return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='workflow-human'){
          this.innerHTML=`<aside class="right-panel interrupt-properties api-properties"><header class="interrupt-heading"><span class="node-icon pink2"><img src="${assets}human.svg" alt=""></span><div class="start-properties__title"><h2>抓取人工接管</h2><p>抓取前位姿调整或抓取动作异常，请求人工完成当前单件抓取。</p></div></header><div class="interrupt-content api-properties__body"><section class="api-custom-inputs"><div class="api-section-heading"><h3>自定义输入</h3><text-button variant="text" icon="plus" data-custom-add>添加</text-button></div><p class="interrupt-hint">为当前节点声明可复用的输入参数</p><div data-human-inputs></div><p class="api-empty">暂无自定义输入</p></section><section><h3>输入配置</h3><p class="interrupt-hint">配置人工接管节点的输入参数</p><div class="workflow-human-field"><form-input label="超时时间（秒）" name="timeout" value="120"></form-input><p class="interrupt-hint">取值范围为 0 到 100000，留空时持续等待。</p></div><div class="workflow-human-field"><form-input label="上报描述" name="report" multiline value="抓取前位姿调整或 VLA 抓取动作未成功，请人工完成当前单件抓取。"></form-input></div></section><section><h3>输出变量</h3><p class="interrupt-hint">暂无已配置的输出变量</p></section><section><div class="start-properties__label"><h3>后续节点</h3><span>1</span></div><p class="interrupt-hint">由画布连线自动生成</p><workflow-next-step source-id="pick-human" source-type="human" target-id="pick-human-check" target-name="判断抓取接管结果" target-type="条件分支" target-icon="condition"></workflow-next-step></section></div></aside>`;
          let inputIndex=0;
          this.querySelector('[data-custom-add]').addEventListener('click',()=>{
            const card=document.createElement('div');card.className='workflow-human-input';
            card.innerHTML='<div class="workflow-human-input__heading"><form-input label="输入名称"></form-input><form-select label="取值方式"><option value="fixed">固定值</option><option value="variable">变量</option></form-select><text-button variant="text" aria-label="删除输入">×</text-button></div><form-input data-input-value label="固定值" multiline placeholder="支持 string / number / bool / list / dict"></form-input><form-select label="类型"><option>字符串</option><option>数字</option><option>布尔值</option><option>列表</option><option>字典</option></form-select>';
            this.querySelector('[data-human-inputs]').append(card);card.querySelector('form-input').value=`input_${++inputIndex}`;this.querySelector('.api-empty').hidden=true;
            card.querySelector('text-button').addEventListener('click',()=>{card.remove();this.querySelector('.api-empty').hidden=!!this.querySelector('[data-human-inputs]').children.length;});
            card.querySelector('form-select').addEventListener('change',()=>{const variable=card.querySelector('form-select').value==='variable';const replacement=document.createElement('form-input');replacement.setAttribute('data-input-value','');replacement.setAttribute('label',variable?'变量':'固定值');replacement.setAttribute('placeholder',variable?'输入变量路径':'支持 string / number / bool / list / dict');if(!variable)replacement.setAttribute('multiline','');card.querySelector('[data-input-value]').replaceWith(replacement);});
          });
          const timeout=this.querySelector('[name="timeout"] input');timeout.type='number';timeout.min='0';timeout.max='100000';
          panelActions(this);return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='workflow-condition'){
          this.innerHTML=`<aside class="right-panel interrupt-properties api-properties"><header class="interrupt-heading"><span class="node-icon blue"><img src="${assets}condition-fix.svg" alt=""></span><div class="start-properties__title"><h2>判断订单最终状态</h2><p>Loop 退出后，根据 order_status 分发成功或失败的订单结果。</p></div></header><div class="interrupt-content api-properties__body"><section class="api-custom-inputs"><div class="api-section-heading"><h3>自定义输入</h3><text-button variant="text" icon="plus" data-custom-add>添加</text-button></div><p class="interrupt-hint">为当前节点声明可复用的输入参数</p><div data-custom-rows></div><p class="api-empty">暂无自定义输入</p></section><div data-workflow-cases></div><workflow-add-button label="添加分支" action="workflow-branch-add" data-branch-add></workflow-add-button><section><h3>默认分支</h3><p class="interrupt-hint">所有条件分支均不满足时执行 · 固定分支</p></section><section><h3>异常分支</h3><p class="interrupt-hint">条件求值发生异常时执行 · 固定分支</p></section><section><div class="start-properties__label"><h3>后续节点</h3><span data-branch-count>4</span></div><p class="interrupt-hint">由画布连线自动生成</p><div data-branch-next></div></section></div></aside>`;
          const cases=this.querySelector('[data-workflow-cases]');
          const sync=()=>{
            const names=[...cases.querySelectorAll('[data-case-name]')].map((input,i)=>`${i?'否则如果':'如果'} · ${input.value}`);
            names.push('默认分支','异常分支');this.querySelector('[data-branch-count]').textContent=names.length;
            const next=this.querySelector('[data-branch-next]');next.replaceChildren();
            names.forEach((label,i)=>{const step=document.createElement('workflow-next-step');step.setAttribute('source-id','condition');step.setAttribute('target-id',i?'failure':'success');step.setAttribute('target-name',i?'准备失败回传':'准备成功回传');step.setAttribute('target-type','变量赋值');step.setAttribute('target-icon','variable');next.append(step);step.querySelector('h4').textContent=label;step.querySelector('.start-properties__source img').src=`${assets}condition-fix.svg`;step.querySelector('.start-properties__source').classList.add('condition-source');step.querySelector('workflow-add-button .text-button').textContent='＋ 在当前分支中插入节点';if(i===names.length-1)step.classList.add('workflow-error-branch');});
          };
          const addCase=(value='')=>{const card=document.createElement('section');card.className='workflow-case';card.innerHTML='<div class="workflow-case__heading"><strong></strong><form-input data-case-name aria-label="分支名称"></form-input></div><div data-condition-rules></div><text-button variant="text" icon="plus" data-rule-add>添加条件</text-button>';cases.append(card);card.querySelector('form-input').value=`case_name_${cases.children.length}`;const addRule=()=>{const rule=document.createElement('workflow-condition-rule');rule.setAttribute('value',value);card.querySelector('[data-condition-rules]').append(rule);};addRule();card.querySelector('[data-rule-add]').addEventListener('click',addRule);card.addEventListener('input',sync);renumber();};
          const renumber=()=>{[...cases.children].forEach((card,i)=>{card.querySelector('strong').textContent=i?'否则如果':'如果';});sync();};
          addCase('success');addCase('failed');
          this.querySelector('[data-branch-add]').addEventListener('click',()=>addCase());
          this.querySelector('[data-custom-add]').addEventListener('click',()=>{const row=document.createElement('div');row.className='api-pair';row.innerHTML='<form-input placeholder="参数名"></form-input><form-input placeholder="默认值"></form-input><text-button variant="text">×</text-button>';this.querySelector('[data-custom-rows]').append(row);this.querySelector('.api-empty').hidden=true;row.querySelector('text-button').addEventListener('click',()=>{row.remove();this.querySelector('.api-empty').hidden=!!this.querySelector('[data-custom-rows]').children.length;});});
          panelActions(this);return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='api-request'){
          this.innerHTML=`<aside class="right-panel interrupt-properties api-properties"><header class="interrupt-heading"><span class="node-icon purple"><img src="${assets}api.svg" alt=""></span><div class="start-properties__title"><h2>获取京东订单</h2><p>从 WCS 获取一个单 SKU 订单</p></div></header><div class="interrupt-content api-properties__body"><section class="api-custom-inputs"><div class="api-section-heading"><h3>自定义输入</h3><text-button variant="text" icon="plus" data-add="custom">添加</text-button></div><p class="interrupt-hint">为当前节点声明可复用的输入参数</p><div data-rows="custom"></div><p data-custom-empty class="api-empty">暂无自定义输入</p></section><section><h3>请求</h3><form-select label="请求方法" name="method"><option>GET</option><option>POST</option><option>PUT</option><option>PATCH</option><option>DELETE</option><option>HEAD</option><option>OPTIONS</option></form-select><form-input label="接口地址（URL） · 必填" name="url" value="http://wcs.internal/api/jd/orders/next"></form-input></section><section><h3>查询参数</h3><div data-rows="query"></div><text-button variant="text" icon="plus" data-add="query">添加查询参数</text-button></section><section><h3>请求头</h3><div data-rows="headers"></div><text-button variant="text" icon="plus" data-add="headers">添加请求头</text-button></section><section><h3>高级设置</h3><div class="api-timeouts"><form-input label="连接超时（s）" name="connectTimeout" placeholder="运行时默认"></form-input><form-input label="读取超时（s）" name="readTimeout" value="30"></form-input><form-input label="写入超时（s）" name="writeTimeout" placeholder="运行时默认"></form-input></div><p class="interrupt-hint">留空时使用运行时默认值，前端不补网络层默认超时。</p><div class="api-retries"><form-input label="最大重试次数" name="retries" value="0"></form-input><form-input label="重试间隔（s）" name="retryInterval" value="0"></form-input></div></section><section class="api-output"><h3>输出变量</h3><dl><dt>body <small>string</small></dt><dd>响应内容</dd><dt>status_code <small>number</small></dt><dd>响应状态码</dd><dt>headers <small>object</small></dt><dd>响应头列表 JSON</dd></dl></section><div data-successors></div></div></aside>`;
          const addRow=(kind,key='',value='')=>{
            const row=document.createElement('div');row.className='api-pair';
            for(const [label,text] of [['参数名',key],['参数值',value]]){const input=document.createElement('form-input');input.setAttribute('placeholder',label);input.setAttribute('aria-label',label);input.setAttribute('value',text);row.append(input);}
            const remove=document.createElement('text-button');remove.setAttribute('variant','text');remove.textContent='×';remove.setAttribute('aria-label','删除参数');remove.addEventListener('click',()=>{row.remove();this.querySelector('[data-custom-empty]').hidden=!!this.querySelector('[data-rows="custom"]').children.length;});row.append(remove);
            this.querySelector(`[data-rows="${kind}"]`).append(row);this.querySelector('[data-custom-empty]').hidden=!!this.querySelector('[data-rows="custom"]').children.length;
          };
          addRow('query','sku_mode','single');addRow('headers','Accept','application/json');
          this.querySelectorAll('[data-add]').forEach(button=>button.addEventListener('click',()=>addRow(button.dataset.add)));
          this.querySelector('[data-successors]').innerHTML='<section class="start-properties__body"><div class="start-properties__label"><h3>后续节点</h3><span>1</span></div><p class="interrupt-hint start-properties__hint">由画布连线自动生成</p><workflow-next-step source-id="get" source-type="api" target-id="save" target-name="保存当前订单" target-type="变量赋值" target-icon="variable"></workflow-next-step></section>';
          panelActions(this);
          return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='end'){
          this.innerHTML=`<aside class="right-panel start-properties"><header class="interrupt-heading start-properties__head"><span class="start-properties__icon end-properties__icon"><img src="${assets}end.svg" alt=""></span><div class="start-properties__title"><h2>结束</h2><p>京东单 SKU 拣选放置流程结束。</p></div></header><section class="interrupt-content start-properties__body"><div class="start-properties__label"><h3>后续节点</h3></div><p class="interrupt-hint start-properties__hint">由画布连线自动生成</p><workflow-next-step empty></workflow-next-step></section></aside>`;
          panelActions(this);
          return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='start'){
          this.innerHTML=`<aside class="right-panel start-properties"><header class="interrupt-heading start-properties__head"><span class="start-properties__icon"><img src="${assets}start.svg" alt=""></span><div class="start-properties__title"><h2>开始</h2><p>开始处理京东单 SKU 拣选放置订单。</p></div></header><section class="interrupt-content start-properties__body"><div class="start-properties__label"><h3>后续节点</h3><span>1</span></div><p class="interrupt-hint start-properties__hint">由画布连线自动生成</p><workflow-next-step source-id="start"></workflow-next-step></section></aside>`;
          panelActions(this,this.querySelector('.start-properties__head'));
          return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='automation'){
          this.innerHTML=`<aside class="right-panel interrupt-properties"><header class="interrupt-heading"><h2>端到端切分</h2><button type="button" data-close aria-label="关闭属性面板">×</button></header><form class="interrupt-form"><div class="interrupt-content"><section><h3>基础信息</h3><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><label>节点名称<input name="nodeName" value="端到端切分" required></label><label>节点 ID<input name="nodeId" value="automatic_1" readonly></label></div><label>节点描述<textarea name="description">生成初始动作片段</textarea></label></section><section><h3>处理规则</h3><label>处理规则</label><div style="display:flex;gap:16px"><form-radio name="processingRule" value="custom" label="任务自定义"></form-radio><form-radio name="processingRule" value="none" label="无需配置" checked></form-radio></div><form-select label="执行算子" name="operator"><option value="end_to_end_segmentation">端到端切分标注处理算子</option></form-select></section></div><footer><span role="status"></span><text-button variant="outline" data-delete>删除节点</text-button><text-button variant="primary" data-save>保存</text-button></footer></form></aside>`;
          const heading=this.querySelector('.interrupt-heading');
          const title=heading.querySelector('h2'),text=document.createElement('div');
          const icon=document.createElement('span');icon.className='node-icon green';icon.innerHTML=`<img src="${assets}omini.svg" alt="">`;
          title.replaceWith(text);text.append(title);const subtitle=document.createElement('p');subtitle.textContent='自动化节点';text.append(subtitle);heading.prepend(icon);
          this.querySelector('[data-close]').addEventListener('click',()=>{this.querySelector('.right-panel').style.display='none';});
          this.querySelector('[data-save]').addEventListener('click',()=>this.querySelector('form').requestSubmit());
          this.querySelector('[data-delete]').addEventListener('click',()=>this.dispatchEvent(new CustomEvent('automation-node-delete',{bubbles:true})));
          this.querySelector('form').addEventListener('submit',event=>{
            event.preventDefault();const values=Object.fromEntries(new FormData(event.target));
            values.processingRule=this.querySelector('form-radio input:checked')?.value||'none';
            values.operator=this.querySelector('form-select').value;
            this.dispatchEvent(new CustomEvent('automation-node-save',{bubbles:true,detail:values}));
            this.querySelector('[role="status"]').textContent='已保存';
          });panelActions(this);return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='condition-sampling'){
          this.innerHTML='<condition-panel class="sampling-properties"></condition-panel>';
          const surface=this.querySelector('.condition-panel');surface.classList.add('right-panel');
          surface.querySelector('.condition-panel__head').classList.add('prop-head');
          panelActions(this);return;
        }
        if(name==='process-node-properties'&&this.getAttribute('variant')==='condition'){
          this.innerHTML=`<aside class="right-panel interrupt-properties"><header class="interrupt-heading"><span class="node-icon blue"><img src="${assets}condition-fix.svg" alt=""></span><div><h2>条件分支</h2><p>条件节点</p></div><button type="button" data-close aria-label="关闭属性面板">×</button></header><form class="interrupt-form"><div class="interrupt-content"><section><h3>节点信息</h3><label>节点名称<input name="nodeName" required></label><label>节点描述<textarea name="description" placeholder="可选，描述节点用途"></textarea></label></section><section><h3>条件分支</h3><p class="interrupt-hint">按顺序判断条件，匹配后进入对应下游；ELSE 为默认分支。</p><div data-condition-branches></div></section></div><footer><span role="status"></span><text-button variant="outline" data-close>关闭</text-button><text-button variant="primary" data-save>保存</text-button></footer></form></aside>`;
          this.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>{this.querySelector('.right-panel').style.display='none';}));
          this.querySelector('[data-save]').addEventListener('click',()=>this.querySelector('form').requestSubmit());
          this.querySelector('form').addEventListener('submit',event=>{event.preventDefault();this.dispatchEvent(new CustomEvent('condition-properties-save',{bubbles:true,detail:Object.fromEntries(new FormData(event.target))}));this.querySelector('[role="status"]').textContent='已保存';});
          panelActions(this);return;
        }
        this.innerHTML = template.replace('<platform-sidebar collapsed>', '<platform-sidebar collapsed variant="style-variant" palette="dark">').replace(/src="assets\//g, 'src="' + assets.href);
        const basic = this.getAttribute('variant') === 'basic';
        if(name==='process-node-properties'&&this.getAttribute('variant')==='human-interrupt'){
          this.innerHTML=`<aside class="right-panel interrupt-properties">
            <header class="interrupt-heading"><span class="node-icon pink2"><img src="${assets}human.svg" alt=""></span><div><h2>Human Interrupt</h2><p>主动发起人工接管</p></div><button type="button" aria-label="关闭属性面板" data-close>×</button></header>
            <form class="interrupt-form"><div class="interrupt-content">
              <p class="interrupt-hint">主动发起人工接管。request / ack / takeover / recovery 由 Robot Runtime 与仲裁系统实现。</p>
              <node-info name="HUMAN_INTERRUPT" type="human_interrupt"></node-info>
              <section class="interrupt-inputs"><div><h3>自定义输入</h3><small>对应 YAML custom_inputs.properties</small></div>
                <div class="interrupt-input-card"><div class="interrupt-input-key"><strong>timeout_s</strong><span>固定值</span></div><label>固定值<input name="timeout_s" type="number" step="any" max="100000" placeholder="留空表示阻塞等待"></label><div class="interrupt-input-meta"><label>类型<input value="float | None" readonly></label><label>默认值<input value="None" readonly></label></div><small>超时时间（秒） · 可选 · 取值范围 (0, 100000]</small></div>
                <div class="interrupt-input-card"><div class="interrupt-input-key"><strong>reason</strong><span>固定值</span></div><label>固定值<textarea name="reason" rows="2" placeholder="填写上报描述"></textarea></label><div class="interrupt-input-meta"><label>类型<input value="string" readonly></label><label>默认值<input value="None" readonly></label></div><small>上报描述 · 可选</small></div>
              </section>
              <p class="interrupt-note">输出字段见下方「结构化输出」，后续处理可通过下游节点与条件节点配置。</p>
              <section class="interrupt-output"><h3>结构化输出 <small>对应 YAML outputs.fields</small></h3>${['completed','reported','report_failed','timeout'].map(field=>`<div class="interrupt-output-row"><strong>${field}</strong><small>object</small></div>`).join('')}</section>
            </div><footer><span role="status"></span><text-button variant="outline" data-close>关闭</text-button><text-button variant="primary" data-save>保存</text-button></footer></form>
          </aside>`;
          this.querySelector('.interrupt-heading p').textContent='人工节点';
          const form=this.querySelector('form'),timeout=form.elements.timeout_s;
          this.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>{this.querySelector('.right-panel').style.display='none';this.dispatchEvent(new CustomEvent('node-properties-close',{bubbles:true}));}));
          this.querySelector('[data-save]').addEventListener('click',()=>form.requestSubmit());
          timeout.addEventListener('input',()=>timeout.setCustomValidity(timeout.value!==''&&Number(timeout.value)<=0?'等待超时必须大于 0':''));
          form.addEventListener('submit',event=>{
            event.preventDefault();const values=Object.fromEntries(new FormData(form));
            values.name=values.name.trim();values.transitions=values.transitions.trim();
            if(!values.name||!values.transitions){this.querySelector('[role="status"]').textContent='请填写节点名称和下游节点';return;}
            const peers=this.closest('.process-editor-components')?.querySelectorAll('.graph-node')||[];
            if([...peers].some(node=>node.dataset.node!==this.dataset.nodeId&&node.querySelector('.graph-title')?.textContent.trim()===values.name)){this.querySelector('[role="status"]').textContent='节点名称已存在';return;}
            values.timeout_s=values.timeout_s===''?null:Number(values.timeout_s);
            this.value=values;this.querySelector('[role="status"]').textContent='已保存';
            this.dispatchEvent(new CustomEvent('node-properties-save',{bubbles:true,detail:values}));
          });
          panelActions(this);
          window.enhancePropertyControls(this);
          return;
        }
        if (basic && name === 'process-node-properties') {
          this.innerHTML = `<aside class="right-panel human-properties">
            <header class="human-properties-header"><span class="avatar human-properties-icon"><img src="${assets}human.svg" alt=""></span><div class="human-properties-title"><h2>供应商抽验</h2><p>添加描述</p></div><div class="prop-tools"><button type="button" aria-label="关闭属性面板" data-property-action="close"><img src="${assets}toolbar-icon-3.svg" alt=""></button></div></header>
            <form class="human-properties-form">
              <node-info variant="basic" name-field="nodeName" name="供应商抽验" description="供应商抽验" node-id="human_2"></node-info>
              <section><h3>处理人</h3><p>处理人分配</p><div class="human-properties-grid"><label class="human-option"><input type="radio" name="assignee" value="custom" checked>任务自定义</label><label class="human-option"><input type="radio" name="assignee" value="inherit">继承前序节点</label></div></section>
              <section><h3>处理规则</h3><p>处理规则</p><div class="human-properties-grid"><label class="human-option"><input type="radio" name="rule" value="custom">任务自定义</label><label class="human-option"><input type="radio" name="rule" value="inherit">继承前序节点</label><label class="human-option"><input type="radio" name="rule" value="none" checked>无需配置</label></div></section>
              <section><h3>工作台</h3><label class="human-workbench">工作台<select name="workbench"><option value="semantic-v1">语义标注工作台 v1.0</option></select></label><p>可用操作</p><label class="human-option is-disabled"><input type="checkbox" disabled>驳回</label><p class="human-property-note">支持驳回到的节点（当前节点没有前序人工节点，暂不可开启驳回）</p></section>
            </form>
            <footer class="human-properties-footer"><span role="status"></span><text-button variant="outline" data-property-action="delete">删除节点</text-button><text-button variant="primary" data-property-action="save">保存</text-button></footer>
          </aside>`;
          const workbenchLabel=this.querySelector('.human-workbench');
          const rejectOption=this.querySelector('.human-option.is-disabled');
          rejectOption.classList.remove('is-disabled');
          const rejectInput=rejectOption.querySelector('input');rejectInput.disabled=false;rejectInput.name='allowReject';rejectInput.value='true';
          this.querySelector('.human-property-note').textContent='支持驳回到前序人工节点。';
          const humanVariants={review:{title:'供应商复核',id:'human_3',previous:['供应商抽验'],inherit:true},accept:{title:'供应商验收',id:'human_4',previous:['供应商复核']},internal:{title:'内部验收',id:'human_6',previous:['供应商抽验','供应商复核','供应商验收']}};
          const humanVariant=humanVariants[this.getAttribute('human-stage')];
          if(humanVariant){
            this.querySelector('h2').textContent=humanVariant.title;
            const info=document.createElement('node-info');
            Object.entries({variant:'basic','name-field':'nodeName',name:humanVariant.title,description:humanVariant.title,'node-id':humanVariant.id}).forEach(([key,value])=>info.setAttribute(key,value));
            this.querySelector('node-info').replaceWith(info);
            const assigneeSection=this.querySelector('input[name="assignee"]').closest('section');
            const inherited=document.createElement('div');
            inherited.innerHTML='<form-select label="继承节点" name="inheritNode">'+humanVariant.previous.map(value=>`<option>${value}</option>`).join('')+'</form-select><p class="human-property-note">可选择任意前序人工节点</p>';
            assigneeSection.append(inherited);
            this.querySelectorAll('input[name="assignee"]').forEach(input=>{input.checked=input.value===(humanVariant.inherit?'inherit':'custom');});
            const updateInheritance=()=>{inherited.hidden=!this.querySelector('input[name="assignee"][value="inherit"]').checked;};
            assigneeSection.addEventListener('change',updateInheritance);updateInheritance();
            rejectInput.checked=true;
            const targets=document.createElement('div');
            targets.innerHTML='<p class="human-property-note">支持驳回到的节点（仅可选择当前节点的前序所有人工节点）</p><form-select name="rejectTargets" aria-label="支持驳回到的节点" multiple>'+humanVariant.previous.map(value=>`<option value="${value}" selected>${value}</option>`).join('')+'</form-select>';
            rejectOption.parentElement.querySelector('.human-property-note')?.remove();
            rejectOption.after(targets);
            rejectInput.addEventListener('change',()=>{targets.hidden=!rejectInput.checked;});
          }
          [...workbenchLabel.childNodes].filter(node=>node.nodeType===Node.TEXT_NODE).forEach(node=>node.remove());
          workbenchLabel.querySelector('select').setAttribute('aria-label','工作台');
          this.querySelector('[data-property-action="save"]').addEventListener('click', () => {
            const detail = Object.fromEntries(new FormData(this.querySelector('form')));
            detail.rejectTargets=[...(this.querySelector('select[name="rejectTargets"]')?.selectedOptions||[])].map(option=>option.value);
            this.querySelectorAll('form-input').forEach(input => { detail[input.getAttribute('name')] = input.value; });
            this.savedValue = detail;
            this.querySelector('h2').textContent = detail.nodeName;
            this.querySelector('[role="status"]').textContent = '已保存';
            this.dispatchEvent(new CustomEvent('node-properties-save', { bubbles: true, detail }));
          });
          for (const action of ['close', 'delete']) this.querySelector(`[data-property-action="${action}"]`).addEventListener('click', () => {
            if(action==='close')this.querySelector('.right-panel').style.display='none';
            this.dispatchEvent(new CustomEvent(`node-properties-${action}`, { bubbles: true, detail: { nodeId: this.dataset.nodeId } }));
          });
        }
        if (basic && name === 'process-node-properties') {
          this.querySelector('.human-properties-title p').textContent='人工节点';
          window.enhancePropertyControls(this);
        }
        if (name === 'process-node-properties') panelActions(this);
        if (basic && name === 'process-node-library') {
          this.querySelector('.palette').innerHTML = basicPalette();
        }
        if ((basic || this.getAttribute('variant') === 'initial') && name === 'process-flow-canvas') {
          this.querySelector('.loop-box')?.remove();
          const originals = new Map([...this.querySelectorAll('.graph-node')].map(node => [node.dataset.node, node.cloneNode(true)]));
          this.querySelectorAll('.graph-node').forEach(node => node.remove());
          const flow = [
            ['start','start','start','Start'],
            ['split','grasp','端到端切分','生成初始动作片段'],
            ['sample','human-1','供应商抽验','供应商抽验'],
            ['review','human-1','供应商复核','供应商复核'],
            ['accept','human-1','供应商验收','供应商验收'],
            ['condition','condition','供应商抽样','供应商抽样 · IF'],
            ['internal','human-1','内部验收','内部验收'],
            ['end','end','end','End']
          ];
          const initial=this.getAttribute('variant')==='initial';
          (initial?flow.filter(([id])=>id==='start'||id==='end'):flow).forEach(([id, source, title, description], index) => {
            const node = originals.get(source).cloneNode(true);
            node.dataset.node = id;
            node.classList.remove('selected');
            node.querySelector('.graph-title').textContent = title;
            node.querySelector('.graph-sub').textContent = description;
            Object.assign(node.style, { left: `${40 + index * 160}px`, top: '160px' });
            // Keep the main input/output ports on the same baseline.
            node.querySelectorAll('.port').forEach(port => {
              port.style.top = '15px';
              port.style.bottom = 'auto';
            });
            if (id === 'condition') {
              node.classList.add('condition-cases');
              const header=document.createElement('div');header.className='condition-case-header';
              header.append(node.querySelector('.mini'),node.querySelector('.node-text'));
              header.querySelector('.graph-sub').textContent='供应商抽样';
              node.replaceChildren(header);
              node.insertAdjacentHTML('beforeend','<div class="branch-row" style="height:72px"><div class="condition-case-label"><span>条件 1</span><span>IF</span></div><div class="condition-expression"><span>条件未设置</span></div></div><div class="branch-row condition-fallback" style="height:40px">ELSE</div><span class="port" style="left:-4px"></span><span class="port" style="right:-4px"></span><span class="port" style="right:-4px"></span>');
              node.conditionConfig={cases:[{name:'供应商抽样',join:'OR',conditions:[{field:'供应商',operator:'等于',value:'供应商 A',ratio:50},{field:'供应商',operator:'等于',value:'供应商 B',ratio:30}]}]};
              const branch=node.querySelector('.branch-row');branch.style.height='106px';
              branch.querySelector('.condition-case-label span').textContent='供应商抽样';
              branch.querySelector('.condition-expression').innerHTML='<span>供应商 等于 供应商 A · 50%</span><b>OR</b>';
              branch.insertAdjacentHTML('beforeend','<div class="condition-expression"><span>供应商 等于 供应商 B · 30%</span></div>');
            }
            this.querySelector('.scene').append(node);
          });
          this.querySelector('process-canvas-tools')?.setAttribute('variant', 'basic');
        }
        if (name === 'process-flow-canvas') {
          const columns = [...new Set([...this.querySelectorAll('.graph-node')].map(node => parseFloat(node.style.left)))].sort((a,b) => a-b);
          const columnPositions = new Map();
          let columnX = columns[0] * 1.65;
          columns.forEach((left, index) => {
            const minimumGap = 62;
            if (index) columnX += 210 + Math.max(minimumGap, (left-columns[index-1])*1.65-210-23);
            columnPositions.set(left, columnX);
          });
          this.querySelectorAll('.graph-node').forEach(node => {
            node.style.removeProperty('width');
            const startIcon = node.querySelector(':scope.start-main > img');
            if (startIcon) {
              startIcon.style.width = '23px';
              startIcon.style.height = '23px';
              startIcon.style.flex = 'none';
            }
            node.style.left = `${columnPositions.get(parseFloat(node.style.left))}px`;
            node.style.top = `${parseFloat(node.style.top) * 1.65}px`;
            node.querySelectorAll('.port').forEach(port => {
              port.style.top = `${parseFloat(port.style.top) * 1.65 + (node.classList.contains('basic-condition') ? 3 : -1)}px`;
            });
            if (node.classList.contains('condition-cases')) {
              node.querySelectorAll('.port').forEach((port, index) => {
                port.style.top = `${[105, 105, 178][index]}px`;
              });
            }
          });
        }
        if (name === 'process-node-library') {
          if (this.getAttribute('variant') === 'workflow') {
            const groups = [
              ['逻辑', [['green','start','Start'],['gray','end','End'],['blue','condition-fix','Condition'],['blue','loop','Loop'],['blue','variable-yellow','Variable Assignment'],['blue','call-flow','Call Flow'],['blue','human','Human Interrupt']]],
              ['能力与服务', [['green','api','API Request'],['green','pose','Pose Set'],['green','nav','Navigation'],['green','omini','Omini Model']]]
            ];
            this.querySelector('.palette').innerHTML = groups.map(([label, items]) => `<div class="palette-group"><div class="group-head"><img src="${assets}chevron.svg" alt=""><span>${label}</span><span class="count">${items.length}</span></div>${items.map(([color, icon, text]) => `<div class="palette-item"><span class="node-icon ${color}"><img src="${assets}${icon}.svg" alt=""></span>${text}</div>`).join('')}</div>`).join('');
          }
          const panel = this.querySelector('.left-panel');
          const groupedItems=[[],[],[]];
          const groupLabels=['逻辑','数据与服务','机器人与 AI'];
          const robotIcons=new Set(['nav.svg','pose.svg','gripper.svg','omini.svg']);
          const logicTypes=new Set(['Start','End','Condition','Loop','Delay','Wait For Input','Variable Assignment','Call Flow','Human Interrupt','开始节点','结束节点','条件节点','人工节点']);
          this.querySelectorAll('.palette-item').forEach(item=>{
            const type=item.textContent.trim(),logic=logicTypes.has(type);
            const icon=item.querySelector('.node-icon');
            const filename=new URL(icon.querySelector('img').src).pathname.split('/').pop();
            const special=filename==='start.svg'||filename==='end.svg';
            icon.className='node-icon '+(filename==='start.svg'?'green':filename==='end.svg'?'gray':logic?'blue':robotIcons.has(filename)?'green':'purple')+(special?'':' group-colored-icon');
            groupedItems[logic?0:robotIcons.has(filename)?2:1].push(item);
          });
          const groupedPalette=this.querySelector('.palette');groupedPalette.replaceChildren();
          groupedItems.forEach((items,index)=>{
            if(!items.length)return;
            const group=document.createElement('div');group.className='palette-group';
            group.innerHTML=`<div class="group-head"><img src="${assets}chevron.svg" alt=""><span>${groupLabels[index]}</span><span class="count">${items.length}</span></div>`;
            group.append(...items);groupedPalette.append(group);
          });
          this.querySelectorAll('.palette-item,.group-head').forEach(item=>{
            item.dataset.nodeType=item.textContent.trim();
            const walker=document.createTreeWalker(item,NodeFilter.SHOW_TEXT);let text;
            while((text=walker.nextNode())){const key=text.textContent.trim();if(nodeNames[key])text.textContent=text.textContent.replace(key,nodeNames[key]);}
          });
          const palette=panel.querySelector('.palette');
          const heading=document.createElement('h3');heading.className='library-section-title';heading.textContent='节点库';
          panel.prepend(heading);
          const flows=panel.querySelector('.flow-list');
          flows.innerHTML='<h3 class="library-section-title">流程</h3><div class="library-flow-tree"><div class="library-flow-row is-current"><span>主流程</span><button type="button" aria-label="主流程更多操作">···</button></div><div class="library-subflows"><div class="library-flow-row"><span>子流程</span><button type="button" aria-label="子流程更多操作">···</button></div></div></div>';
          panel.prepend(flows);
          const more='<button type="button" class="flow-more" aria-label="更多操作"><svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg></button>';
          flows.innerHTML=`<h3 class="library-section-title">流程</h3><div class="library-flow-tree"><div class="library-flow-row is-current"><button class="flow-tree-toggle" type="button" aria-label="收起子流程" aria-expanded="true"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m4 6 4 4 4-4"/></svg></button><span class="flow-name" title="任务处理流程">任务处理流程</span><span class="flow-main-tag">主流程</span>${more}</div><div class="library-subflows"><div class="library-flow-row"><span class="flow-name">数据预处理</span>${more}</div><div class="library-flow-row"><span class="flow-name">质量验收</span>${more}</div></div></div>`;
          flows.querySelector('.flow-main-tag').textContent='主';
          const multiFlow=this.getAttribute('flow-variant')==='multiple';
          if(!multiFlow){
            flows.querySelector('.library-subflows').remove();
            flows.querySelector('.flow-tree-toggle').remove();
            flows.querySelector('.flow-main-tag').remove();
            const flowName=flows.querySelector('.flow-name');
            const variant=this.getAttribute('variant');
            flowName.textContent=variant==='basic'?'端到端切分标注':variant==='workflow'?'京东单 SKU 拣放':'通用工作流';
            flowName.title=flowName.textContent;
          }
          const flowHeading=flows.querySelector('.library-section-title');
          flowHeading.innerHTML='<span>流程 <span class="library-heading-count">'+flows.querySelectorAll('.library-flow-row').length+'</span></span>';
          const nodeCount=document.createElement('span');nodeCount.className='library-heading-count';nodeCount.textContent=String(palette.querySelectorAll('.palette-item').length);
          heading.append(' ',nodeCount);
          const search=document.createElement('label');search.className='library-node-search';
          search.innerHTML='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg><input type="search" placeholder="搜索节点" aria-label="搜索节点">';
          heading.after(search);
          const empty=document.createElement('div');empty.className='library-search-empty';empty.textContent='未找到匹配节点';empty.hidden=true;palette.append(empty);
          const groups=[...palette.querySelectorAll('.palette-group')];
          let collapsedBeforeSearch=null;
          search.querySelector('input').addEventListener('input',event=>{
            const query=event.target.value.trim().toLowerCase();
            if(query && !collapsedBeforeSearch)collapsedBeforeSearch=groups.map(group=>group.classList.contains('is-collapsed'));
            let count=0;
            palette.querySelectorAll('.palette-item').forEach(item=>{const match=!query || item.textContent.toLowerCase().includes(query);item.hidden=!match;if(match)count++;});
            groups.forEach((group,index)=>{
              group.hidden=!!query && ![...group.querySelectorAll('.palette-item')].some(item=>!item.hidden);
              if(query)group.classList.remove('is-collapsed');
              else if(collapsedBeforeSearch)group.classList.toggle('is-collapsed',collapsedBeforeSearch[index]);
              group.querySelector('.group-head')?.setAttribute('aria-expanded',String(!group.classList.contains('is-collapsed')));
            });
            if(!query)collapsedBeforeSearch=null;
            empty.hidden=count!==0;
          });
          if(multiFlow && this.getAttribute('tree-controls')!=='single'){
            const eye='<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>';
            const rows=[...flows.querySelectorAll('.library-flow-row')];
            const ids=['main','preprocess','quality'],hidden=new Set(),buttons=[];
            const actions=document.createElement('span');actions.className='flow-heading-actions';
            const all=document.createElement('button');all.type='button';all.innerHTML=eye;actions.append(all);
            const add=document.createElement('button');add.type='button';add.title='新增流程';add.setAttribute('aria-label','新增流程');
            add.innerHTML='<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M12 4v16M4 12h16"/></svg>';
            add.addEventListener('click',()=>this.dispatchEvent(new CustomEvent('flow-add',{bubbles:true})));
            actions.append(add);
            flows.querySelector('.library-section-title').append(actions);
            const refresh=()=>{
              buttons.forEach((button,index)=>{const visible=!hidden.has(ids[index]);button.classList.toggle('is-off',!visible);button.setAttribute('aria-pressed',String(visible));button.title=(visible?'隐藏':'显示')+rows[index].querySelector('.flow-name').textContent;button.setAttribute('aria-label',button.title);});
              all.title=hidden.size?'显示全部流程':'隐藏全部流程';all.setAttribute('aria-label',all.title);all.setAttribute('aria-pressed',String(!hidden.size));
              this.dispatchEvent(new CustomEvent('flow-visibility-change',{bubbles:true,detail:{hidden:[...hidden]}}));
            };
            rows.forEach((row,index)=>{const button=document.createElement('button');button.type='button';button.className='flow-visibility';button.innerHTML=eye;row.querySelector('.flow-more').before(button);buttons.push(button);button.addEventListener('click',event=>{event.stopPropagation();hidden.has(ids[index])?hidden.delete(ids[index]):hidden.add(ids[index]);refresh();});});
            all.addEventListener('click',()=>{if(hidden.size)hidden.clear();else ids.forEach(id=>hidden.add(id));refresh();});
            refresh();
          }
          flows.querySelectorAll('.library-flow-row').forEach(row=>{
            const more=row.querySelector('.flow-more');
            more.title='重命名';more.setAttribute('aria-label','重命名流程');
            more.addEventListener('click',event=>{
              event.stopPropagation();
              if(row.querySelector('.flow-rename-input'))return;
              const label=row.querySelector('.flow-name');
              const input=document.createElement('input');input.className='flow-rename-input';
              input.value=label.textContent;input.maxLength=100;input.setAttribute('aria-label','流程名称');
              label.hidden=true;label.after(input);
              let finished=false;
              const finish=save=>{
                if(finished)return;
                const value=input.value.trim();
                if(save&&!value){input.setCustomValidity('请输入流程名称');input.reportValidity();return;}
                finished=true;
                if(save){label.textContent=value;label.title=value;this.dispatchEvent(new CustomEvent('flow-rename',{bubbles:true,detail:{name:value}}));}
                label.hidden=false;input.remove();more.focus();
              };
              input.addEventListener('input',()=>input.setCustomValidity(''));
              input.addEventListener('keydown',event=>{
                event.stopPropagation();
                if(event.key==='Enter'){event.preventDefault();finish(true);}
                if(event.key==='Escape'){event.preventDefault();finish(false);}
              });
              input.addEventListener('blur',()=>finish(Boolean(input.value.trim())));
              input.focus();input.select();
            });
          });
          const treeToggle=flows.querySelector('.flow-tree-toggle');
          const categoryArrow=palette.querySelector('.group-head img');
          if(categoryArrow && treeToggle){const arrow=categoryArrow.cloneNode(true);arrow.alt='';treeToggle.replaceChildren(arrow);}
          const alignFlowArrow=()=>{
            if(!categoryArrow || !treeToggle || panel.classList.contains('is-library-collapsed'))return;
            treeToggle.style.transform='none';
            const target=categoryArrow.getBoundingClientRect();
            const scale=panel.getBoundingClientRect().width/panel.offsetWidth;
            if(!target.width || !scale)return;
            const row=treeToggle.closest('.library-flow-row');
            const rowRect=row.getBoundingClientRect();
            const inset=(target.left-rowRect.left)/scale;
            row.style.paddingLeft=`${inset}px`;
            // Use the category's icon-to-label gap for the flow name as well.
            row.style.gap=getComputedStyle(categoryArrow.parentElement).gap;
            const more=row.querySelector('.flow-more');
            const svg=more.querySelector('svg');
            const internalInset=(more.offsetWidth-svg.getBoundingClientRect().width/scale)/2;
            flows.querySelectorAll('.library-flow-row').forEach(item=>{item.style.paddingRight=`${Math.max(0,inset-internalInset)}px`;});
          };
          const arrowAlignmentObserver=new ResizeObserver(()=>requestAnimationFrame(alignFlowArrow));
          arrowAlignmentObserver.observe(panel);
          requestAnimationFrame(alignFlowArrow);
          treeToggle?.addEventListener('click',()=>{
            const expanded=treeToggle.getAttribute('aria-expanded')!=='true';
            treeToggle.setAttribute('aria-expanded',String(expanded));
            treeToggle.setAttribute('aria-label',expanded?'收起子流程':'展开子流程');
            flows.querySelector('.library-subflows').hidden=!expanded;
          });
          const divider=document.createElement('div');divider.className='library-resizer';divider.tabIndex=0;
          divider.setAttribute('role','separator');divider.setAttribute('aria-orientation','horizontal');divider.setAttribute('aria-label','调整流程区域高度');
          flows.after(divider);
          const resize=value=>{const height=Math.max(90,Math.min(value,Math.max(90,panel.clientHeight-160)));flows.style.height=`${height}px`;divider.setAttribute('aria-valuenow',String(Math.round(height)));};
          let resizeDrag=null;
          divider.addEventListener('pointerdown',event=>{if(event.button!==0)return;event.preventDefault();resizeDrag={y:event.clientY,height:flows.offsetHeight};divider.setPointerCapture(event.pointerId);});
          divider.addEventListener('pointermove',event=>{if(resizeDrag)resize(resizeDrag.height+event.clientY-resizeDrag.y);});
          const endResize=()=>{resizeDrag=null;};
          divider.addEventListener('pointerup',endResize);divider.addEventListener('pointercancel',endResize);
          divider.addEventListener('keydown',event=>{if(['ArrowUp','ArrowDown'].includes(event.key)){event.preventDefault();resize(flows.offsetHeight+(event.key==='ArrowUp'?-10:10));}});
          const toggle = document.createElement('button');
          toggle.type = 'button';
          toggle.className = 'node-library-toggle';
          toggle.style.display = 'none';
          toggle.textContent = '‹';
          toggle.title = '收起节点栏';
          toggle.setAttribute('aria-expanded', 'true');
          toggle.setAttribute('aria-label', '收起节点栏');
          panel.prepend(toggle);
          toggle.addEventListener('click', () => {
            const collapsed = panel.classList.toggle('is-library-collapsed');
            toggle.textContent = collapsed ? '›' : '‹';
            toggle.setAttribute('aria-expanded', String(!collapsed));
            toggle.setAttribute('aria-label', collapsed ? '展开节点栏' : '收起节点栏');
            toggle.title = collapsed ? '展开节点栏' : '收起节点栏';
            this.dispatchEvent(new CustomEvent('node-library-toggle',{bubbles:true}));
          });
        }
        if (name === 'process-canvas-tools') {
          this.querySelector('.toolbar-left').insertAdjacentHTML('beforeend', `
            <span class="toolbar-divider" aria-hidden="true"></span>
            <button type="button" class="tool-btn" data-action="add" title="添加" aria-label="添加">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></svg>
            </button>`);
          const addButton = this.querySelector('[data-action="add"]');
          addButton.insertAdjacentHTML('afterend','<button type="button" class="tool-btn" data-action="arrange" title="整理节点" aria-label="整理节点"><svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="3" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/><path d="M9 6h6M6 9v9h9"/></svg></button>');
          const menu = document.createElement('div');
          const toolLabels={fit:'选择 / 适应画布',hand:'拖动画布',undo:'撤销',redo:'重做',add:'展开 / 收起节点栏',arrange:'整理节点'};
          this.querySelectorAll('.tool-btn').forEach(button=>{
            const label=toolLabels[button.dataset.action] || button.getAttribute('aria-label') || '选择节点';
            button.title=label;button.setAttribute('aria-label',label);button.dataset.tooltip=label;
          });
          menu.className = 'canvas-add-menu';
          menu.hidden = true;
          menu.setAttribute('aria-label', '添加节点');
          addButton.setAttribute('aria-expanded', 'false');
          const syncLibraryButton=()=>{
            const scope=this.closest('process-editor-page')||this.closest('.process-editor-components');
            const library=this.closest('.canvas-stage')?.querySelector('process-node-library')||scope?.querySelector('process-node-library');
            const expanded=!!library?.querySelector('.left-panel:not(.is-library-collapsed)');
            addButton.classList.toggle('is-library-active',expanded);
            addButton.setAttribute('aria-pressed',String(expanded));
            addButton.setAttribute('aria-expanded',String(expanded));
          };
          (this.closest('process-editor-page')||this.closest('.process-editor-components'))?.addEventListener('node-library-toggle',syncLibraryButton);
          requestAnimationFrame(syncLibraryButton);
          this.querySelector('.toolbar-left').append(menu);
          const closeMenu = () => {
            menu.hidden = true;
            addButton.setAttribute('aria-expanded', 'false');
          };
          addButton.addEventListener('click', (event) => {
            if (!event.detail?.anchor) {
              const canvas=this.closest('.canvas-stage');
              const scope=this.closest('process-editor-page') || this.closest('.process-editor-components');
              let library=canvas?.querySelector('process-node-library') || scope?.querySelector('process-node-library');
              if (!library && canvas) {
                library=document.createElement('process-node-library');
                if(this.getAttribute('variant')==='basic')library.setAttribute('variant','basic');
                canvas.append(library);
                Object.assign(library.querySelector('.left-panel').style,{position:'absolute',left:'0',top:'0',bottom:'0',zIndex:'20'});
                library.querySelector('.left-panel').classList.add('is-library-collapsed');
              }
              library?.querySelector('.node-library-toggle')?.click();
              const expanded=!!library && !library.querySelector('.left-panel').classList.contains('is-library-collapsed');
              addButton.setAttribute('aria-expanded',String(expanded));
              syncLibraryButton();
              addButton.title=expanded?'收起节点栏':'展开节点栏';
              addButton.setAttribute('aria-label',addButton.title);
              return;
            }
            if (!menu.hidden) { closeMenu(); return; }
            menu.removeAttribute('style');
            const fragment = document.createElement('template');
            fragment.innerHTML = templates['process-node-library'].replace(/src="assets\//g, 'src="' + assets.href);
            if (this.getAttribute('variant') === 'basic') fragment.content.querySelector('.palette').innerHTML = basicPalette();
            menu.replaceChildren(fragment.content.querySelector('.palette'));
            if (event.detail?.anchor) {
              menu.querySelectorAll('.palette-item').forEach(item => {
                if (['start','end','开始节点','结束节点'].includes(item.textContent.trim().toLowerCase())) item.remove();
              });
              menu.querySelectorAll('.palette-group').forEach(group => {
                const count=group.querySelectorAll('.palette-item').length;
                const label=group.querySelector('.count');if(label)label.textContent=String(count);
                if(!count)group.remove();
              });
            }
            menu.querySelectorAll('.group-head').forEach(head => {
              head.tabIndex = 0;
              head.setAttribute('role', 'button');
              head.setAttribute('aria-expanded', 'true');
              head.addEventListener('click', () => {
                const collapsed = head.parentElement.classList.toggle('is-collapsed');
                head.setAttribute('aria-expanded', String(!collapsed));
              });
              head.addEventListener('keydown', event => {
                if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); head.click(); }
              });
            });
            menu.querySelectorAll('.palette-item').forEach((item, index) => {
              item.tabIndex = 0;
              item.setAttribute('role', 'button');
              item.addEventListener('click', () => {
                this.dispatchEvent(new CustomEvent('node-pick', { bubbles: true, detail: { label: item.textContent.trim(), icon: item.querySelector('.node-icon').innerHTML, color: item.querySelector('.node-icon').className } }));
                closeMenu();
                addButton.focus();
              });
              item.addEventListener('keydown', event => {
                if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); item.click(); }
              });
            });
            menu.hidden = false;
            const anchor = event.detail?.anchor;
            if (anchor) {
              const bounds = this.closest('.canvas-stage')?.getBoundingClientRect()
                || {left:0, top:0, right:window.innerWidth, bottom:window.innerHeight};
              menu.style.position = 'fixed';
              menu.style.bottom = 'auto';
              menu.style.maxHeight = `${Math.max(80, bounds.bottom-bounds.top-24)}px`;
              const rect = menu.getBoundingClientRect();
              const left = Math.max(bounds.left+12, Math.min(anchor.left, bounds.right-rect.width-12));
              const top = Math.max(bounds.top+12, Math.min(anchor.bottom+8, bounds.bottom-rect.height-12));
              menu.style.left = `${left}px`;
              menu.style.top = `${top}px`;
            }
            addButton.setAttribute('aria-expanded', 'true');
            this.dispatchEvent(new CustomEvent('canvas-add', { bubbles: true }));
          });
          menu.addEventListener('pointerdown', event => event.stopPropagation());
          menu.addEventListener('wheel', event => event.stopPropagation());
          document.addEventListener('pointerdown', event => {
            if (!menu.hidden && !menu.contains(event.target) && !addButton.contains(event.target)) closeMenu();
          });
          menu.addEventListener('keydown', event => {
            if (event.key === 'Escape') { event.stopPropagation(); closeMenu(); addButton.focus(); }
          });
          addButton.addEventListener('keydown', event => {
            if (event.key === 'Escape') closeMenu();
          });
        }
        if (name === 'process-editor-header') {
          this.querySelector('.title-block p').textContent = 'v0.1 · 草稿 · 未保存变更';
          const title = this.querySelector('h1');
          const titleRow = document.createElement('div');
          titleRow.className = 'process-title-row';
          title.replaceWith(titleRow);
          titleRow.append(title);
          titleRow.insertAdjacentHTML('beforeend', '<button type="button" class="process-title-edit" aria-label="编辑流程标题" title="编辑标题"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 5 4 4M4 20l4-1L20 7a2.8 2.8 0 0 0-4-4L4 15v5Z"/></svg></button>');
          const dialog = document.createElement('dialog');
          dialog.className = 'flow-info-dialog';
          dialog.setAttribute('aria-labelledby', 'flow-info-heading');
          dialog.innerHTML = `<form class="flow-info-form">
            <header><h2 id="flow-info-heading">编辑流程信息</h2><button type="button" data-dismiss aria-label="关闭">×</button></header>
            <div class="flow-info-fields">
              <label>流程标识<input value="e2e-split-annotation" readonly></label>
              <label>流程名称<input name="flowName" required maxlength="100" autocomplete="off"></label>
              <label>业务环节<select disabled><option>标注</option></select></label>
            </div>
            <footer><text-button variant="outline" data-dismiss>关闭</text-button><text-button variant="primary" data-save-info>保存</text-button></footer>
          </form>`;
          this.append(dialog);
          const nameInput = dialog.querySelector('[name="flowName"]');
          titleRow.querySelector('button').addEventListener('click', () => {
            nameInput.value = title.textContent.trim();
            nameInput.setCustomValidity('');
            dialog.showModal();
            nameInput.focus();
            nameInput.setSelectionRange(nameInput.value.length, nameInput.value.length);
          });
          dialog.querySelectorAll('[data-dismiss]').forEach(close => close.addEventListener('click', () => dialog.close()));
          nameInput.addEventListener('input', () => nameInput.setCustomValidity(''));
          dialog.querySelector('[data-save-info]').addEventListener('click', () => dialog.querySelector('form').requestSubmit());
          dialog.querySelector('form').addEventListener('submit', event => {
            event.preventDefault();
            const value = nameInput.value.trim();
            if (!value) { nameInput.setCustomValidity('请输入流程名称'); nameInput.reportValidity(); return; }
            title.textContent = value;
            this.dispatchEvent(new CustomEvent('flow-info-change', {bubbles:true, detail:{name:value}}));
            dialog.close();
          });
          const icon = this.querySelector('.back');
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'back-button';
          button.setAttribute('aria-label', '返回上一页');
          button.title = '返回上一页';
          icon.replaceWith(button);
          button.append(icon);
          button.addEventListener('click', () => window.history.back());
        }
        if (name === 'process-flow-canvas' && this.hasAttribute('external-controls')) {
          this.querySelectorAll('process-canvas-tools,process-canvas-zoom').forEach(control => control.remove());
        }
      }
    });
  }
  if(!customElements.get('process-flow-tree'))customElements.define('process-flow-tree',class extends HTMLElement{
    connectedCallback(){
      if(this.dataset.rendered)return;
      this.dataset.rendered='true';
      const library=document.createElement('process-node-library');
      library.setAttribute('variant','basic');
      library.setAttribute('flow-variant','multiple');
      if(this.getAttribute('variant')==='single')library.setAttribute('tree-controls','single');
      this.append(library);
      const tree=library.querySelector('.flow-list');
      if(tree){
        this.append(tree);library.remove();
        if(this.getAttribute('variant')==='single'){
          tree.querySelector('.library-subflows')?.remove();
          tree.querySelector('.flow-tree-toggle')?.remove();
          tree.querySelector('.flow-main-tag')?.remove();
          const count=tree.querySelector('.library-heading-count');if(count)count.textContent='1';
        }
      }
    }
  });
})();
