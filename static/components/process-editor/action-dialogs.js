window.addEventListener('DOMContentLoaded', () => {
  class GlobalParameterFields extends HTMLElement {
    connectedCallback(){
      if(this.childElementCount)return;
      this.innerHTML='<section class="global-parameter-group" aria-label="参数赋值"><h3>参数赋值</h3><div class="global-parameter-list"></div><text-button variant="text" icon="plus" data-add>添加参数</text-button></section>';
      this.querySelector('[data-add]').addEventListener('click',()=>this.add());
      this.insertAdjacentHTML('beforeend','<section class="global-parameter-group workflow-function-group" aria-label="工作流函数"><h3>工作流函数</h3><p class="action-dialog-note">供变量赋值和按条件循环选择，运行时入口固定为 main(params)。</p><div class="workflow-function-list"></div><text-button variant="text" icon="plus" data-add-function>添加函数</text-button></section>');
      this.querySelector('[data-add-function]').addEventListener('click',()=>this.addFunction());

      this.value=[{name:'current_order',type:'object',defaultValue:{},description:''}];
    }
    add(value={}){
      const row=document.createElement('section');row.className='global-parameter-card';
      row.innerHTML='<div class="global-parameter-top"><form-input label="参数名称" data-name placeholder="例如：user_id"></form-input><form-select label="类型" data-type><option>string</option><option>number</option><option>boolean</option><option>object</option><option>array</option></form-select><text-button variant="text" data-remove icon="delete" icon-only aria-label="删除参数"></text-button></div><div class="global-parameter-bottom"><form-input label="默认值 · 可选" data-default placeholder="未设置"></form-input><form-input label="描述 · 可选" data-description placeholder="说明这个参数的用途"></form-input></div>';
      this.querySelector('.global-parameter-list').append(row);
      row.querySelector('[data-name]').value=value.name||'';row.querySelector('[data-name] input').required=true;
      row.querySelector('[data-type]').value=value.type||'string';row.parameterRequired=!!value.required;
      row.querySelector('[data-default]').value=value.defaultValue==null?'':typeof value.defaultValue==='object'?JSON.stringify(value.defaultValue):String(value.defaultValue);
      row.querySelector('[data-description]').value=value.description||'';
      const remove=row.querySelector('[data-remove]');
      const wrapper=document.createElement('div');wrapper.className='global-parameter-item';row.before(wrapper);wrapper.append(row,remove);
      remove.addEventListener('click',()=>wrapper.remove());
      const input=row.querySelector('[data-name] input');
      const error=document.createElement('span');error.className='global-parameter-name-error';error.textContent='请输入参数名称';error.hidden=true;
      const errorId=`parameter-name-error-${Date.now()}-${Math.random().toString(36).slice(2)}`;error.id=errorId;
      row.querySelector('[data-name]').append(error);input.setAttribute('aria-describedby',errorId);
      const validate=()=>{const invalid=!input.value.trim();error.hidden=!invalid;input.setAttribute('aria-invalid',String(invalid));input.setCustomValidity(invalid?'请输入参数名称':'');};
      input.addEventListener('invalid',validate);input.addEventListener('blur',validate);input.addEventListener('input',()=>{input.setCustomValidity('');if(!error.hidden)validate();});

    }
    addFunction(value={}){
      const row=document.createElement('section');row.className='global-parameter-card workflow-function-card';
      row.innerHTML='<div class="global-parameter-top"><form-input label="函数名称" data-function-name placeholder="例如：parse_order"></form-input><form-select label="语言" data-language><option>Python</option></form-select><text-button variant="text" data-remove icon="delete" icon-only aria-label="删除函数"></text-button></div><form-input label="函数代码" data-code multiline></form-input><span class="global-parameter-name-error" role="alert" hidden>请输入函数名称</span>';
      this.querySelector('.workflow-function-list').append(row);
      row.querySelector('[data-function-name]').value=value.name||'';
      row.querySelector('[data-code]').value=value.code??'def main(params):\n    return params';
      const input=row.querySelector('[data-function-name] input');input.required=true;
      const error=row.querySelector('[role="alert"]');
      const validate=()=>{const invalid=!input.value.trim();error.hidden=!invalid;input.setAttribute('aria-invalid',String(invalid));input.setCustomValidity(invalid?'请输入函数名称':'');};
      input.addEventListener('invalid',validate);input.addEventListener('blur',validate);input.addEventListener('input',()=>{input.setCustomValidity('');if(!error.hidden)validate();});
      row.querySelector('[data-code] textarea').required=true;
      const remove=row.querySelector('[data-remove]');
      const wrapper=document.createElement('div');wrapper.className='global-parameter-item';row.before(wrapper);wrapper.append(row,remove);
      remove.addEventListener('click',()=>wrapper.remove());
    }
    set functions(values){this.querySelector('.workflow-function-list').replaceChildren();values.forEach(value=>this.addFunction(value));}
    get functions(){return [...this.querySelectorAll('.workflow-function-card')].map(row=>({name:row.querySelector('[data-function-name]').value.trim(),language:row.querySelector('[data-language]').value,code:row.querySelector('[data-code]').value}));}
    set value(values){this.querySelector('.global-parameter-list').replaceChildren();values.forEach(value=>this.add(value));}
    get value(){return [...this.querySelectorAll('.global-parameter-list .global-parameter-card')].map(row=>({name:row.querySelector('[data-name]').value.trim(),type:row.querySelector('[data-type]').value,required:row.parameterRequired,defaultValue:row.querySelector('[data-default]').value,description:row.querySelector('[data-description]').value}));}
  }
  customElements.define('global-parameter-fields',GlobalParameterFields);
  const definitions = {
    "collection-confirm": {title:"确认操作",body:"",confirm:"确认"},
    "command-package-info": {title:"创建指令包",body:"",confirm:"确认"},
    "approval-rejection": {title:"选择不合格原因",body:"",confirm:"确认"},
    parameters: {title:'全局参数', confirm:'保存参数', body:`<p class="action-dialog-note">定义流程中可被多个节点引用的参数。</p><div class="action-parameter-row"><span>参数名称</span><span>类型</span><span>默认值</span></div><div class="action-parameter-row"><input aria-label="参数名称" value="retry_count"><select aria-label="参数类型"><option>整数</option><option>字符串</option><option>布尔值</option></select><input aria-label="默认值" value="3"></div><text-button icon="plus" variant="text" data-add-parameter>添加参数</text-button>`},
    download: {title:'下载 YAML', confirm:'下载', body:`<p class="action-dialog-note">导出当前流程的节点、连接关系及全局参数。</p><label>文件名称<input value="workflow.yaml" required pattern=".+\\.ya?ml"></label><div class="action-dialog-summary"><span>导出范围</span><strong>完整流程</strong><span>文件格式</span><strong>YAML（.yaml）</strong></div><p class="action-dialog-note">请先检查配置，下载文件不改变当前发布状态。</p>`},
    save: {title:'保存流程', confirm:'保存', body:`<p class="action-dialog-note">保存当前编辑内容为草稿，不影响已发布版本。</p><div class="action-dialog-summary"><span>流程名称</span><strong>端到端切分标注流程</strong><span>保存版本</span><strong>v0.1 · 草稿</strong></div><label>变更说明<textarea placeholder="选填，记录本次修改内容" rows="3"></textarea></label>`},
    publish: {title:'发布流程', confirm:'发布', body:`<p class="action-dialog-note">发布前请确认节点配置、连接关系与全局参数完整。</p><label>版本号<input value="v0.2" required></label><label>发布说明<textarea placeholder="填写本次发布的变更内容" rows="3" required></textarea></label><label class="action-dialog-check"><input type="checkbox" required>我已检查流程配置，确认发布此版本</label>`},
    history: {title:'版本历史', body:`<p class="action-dialog-note">示例数据 · 查看流程的保存与发布记录。</p><ol class="action-dialog-history"><li><strong>v0.2 <span>草稿</span></strong><p>调整节点配置与全局参数</p><small>2026-09-14 14:30</small></li><li><strong>v0.1 <span>已发布</span></strong><p>创建端到端切分标注流程</p><small>2026-09-07 10:16</small></li></ol>`}
  };
  class ProcessActionDialog extends HTMLElement {
    connectedCallback() {
      if(this.childElementCount)return;
      const variant=this.getAttribute('variant');
      const def=definitions[variant];
      const frame=document.createElement(this.hasAttribute('preview')?'div':'dialog');
      frame.className='flow-info-dialog action-dialog-frame';
      if(variant==='edit') {
        const existing=document.querySelector('process-editor-header .flow-info-form');
        frame.append(existing.cloneNode(true));
        frame.querySelectorAll('[id]').forEach(el=>el.removeAttribute('id'));
        frame.querySelector('[name="flowName"]').value='端到端切分标注流程';
      } else {
        frame.innerHTML=`<form class="flow-info-form"><header><h2>${def.title}</h2><button type="button" data-dismiss aria-label="关闭">×</button></header><div class="flow-info-fields">${def.body}</div><footer><span class="action-dialog-feedback" role="status"></span><text-button variant="outline" data-dismiss>关闭</text-button>${def.confirm?`<text-button variant="primary" data-confirm>${def.confirm}</text-button>`:''}</footer></form>`;
      }
      frame.setAttribute('aria-label',variant==='edit'?'编辑流程信息':def.title);
      this.append(frame);
      if(variant==='parameters'){
        frame.classList.add('global-parameters-dialog');
        frame.querySelector('.flow-info-fields').replaceChildren(document.createElement('global-parameter-fields'));
      }
      this.addEventListener('click',event=>{
        if(event.target.closest('[data-dismiss]')) {if(frame.tagName==='DIALOG')frame.close();return;}
        if(event.target.closest('[data-add-parameter]')) {
          const row=frame.querySelectorAll('.action-parameter-row')[1].cloneNode(true);
          row.querySelectorAll('input').forEach(input=>input.value='');
          frame.querySelector('[data-add-parameter]').before(row);
        }
        if(event.target.closest('[data-confirm],[data-save-info]'))frame.querySelector('form').requestSubmit();
      });
      frame.querySelector('form').addEventListener('submit',event=>{
        event.preventDefault();
        let parameters,functions;
        if(variant==='parameters'){
          parameters=frame.querySelector('global-parameter-fields').value;
          functions=frame.querySelector('global-parameter-fields').functions;
          try{
            const functionNames=new Set();functions.forEach(item=>{if(!item.name||functionNames.has(item.name))throw Error('函数名称不能为空或重复');functionNames.add(item.name);});
            const names=new Set();parameters.forEach(item=>{if(!item.name||names.has(item.name))throw Error('参数名称不能为空或重复');names.add(item.name);if(item.defaultValue!==''&&item.type!=='string'){const value=JSON.parse(item.defaultValue);if(item.type==='array'?!Array.isArray(value):item.type==='object'?(value===null||Array.isArray(value)||typeof value!=='object'):typeof value!==item.type)throw Error('默认值与参数类型不匹配');item.defaultValue=value;}});
          }catch(error){frame.querySelector('.action-dialog-feedback').textContent=error.message;return;}
          this.savedFunctions=structuredClone(functions);this.savedParameters=parameters;frame.querySelector('.action-dialog-feedback').textContent='参数已保存（当前示例）';
        }
        this.dispatchEvent(new CustomEvent('action-dialog-confirm',{bubbles:true,detail:{action:variant,parameters,functions}}));
        if(variant==='parameters'&&frame.tagName==='DIALOG')frame.close();
      });
    }
    show(){
      const fields=this.querySelector('global-parameter-fields');
      if(fields){if(!this.savedParameters)this.savedParameters=structuredClone(fields.value);fields.value=structuredClone(this.savedParameters);fields.functions=structuredClone(this.savedFunctions||[]);this.querySelector('.action-dialog-feedback').textContent='';}
      this.querySelector('dialog')?.showModal();
    }
  }
  customElements.define('process-action-dialog',ProcessActionDialog);
  if(!document.querySelector('.component-gallery')){
    let parametersModal;
    document.addEventListener('process-action',event=>{
      if(event.detail.action!=='parameters')return;
      event.stopPropagation();
      if(!parametersModal){parametersModal=document.createElement('process-action-dialog');parametersModal.setAttribute('variant','parameters');(event.target.closest('.process-editor-components')||document.querySelector('.process-editor-components')).append(parametersModal);}
      parametersModal.show();
    },true);
    return;
  }
  const header=document.querySelector('process-editor-header');
  if(!header)return;
  const table=document.createElement('table');table.className='action-dialog-table';
  table.innerHTML='<thead><tr><th scope="col">按钮</th><th scope="col">触发的弹窗</th></tr></thead><tbody></tbody>';
  for(const [variant,label] of [['edit','编辑信息'],['parameters','全局参数'],['download','下载 YAML'],['save','保存'],['publish','发布'],['history','历史']]){
    const row=table.querySelector('tbody').insertRow();
    const left=row.insertCell(),right=row.insertCell();
    const source=variant==='edit'?header.querySelector('.process-title-edit'):header.querySelector(`[data-process-action="${variant}"]`);
    const button=source.cloneNode(true);button.removeAttribute('data-process-action');
    left.append(button);
    if(!['edit','parameters'].includes(variant))continue;
    const preview=document.createElement('process-action-dialog');preview.setAttribute('variant',variant);preview.setAttribute('preview','');right.append(preview);
    const modal=document.createElement('process-action-dialog');modal.setAttribute('variant',variant);left.append(modal);
    button.addEventListener('click',()=>modal.show());
    if(variant==='parameters'){
      document.addEventListener('process-action',event=>{if(event.detail.action==='parameters'){event.stopPropagation();modal.show();}},true);
      modal.addEventListener('action-dialog-confirm',event=>{preview.savedFunctions=structuredClone(event.detail.functions||[]);preview.querySelector('global-parameter-fields').functions=preview.savedFunctions;preview.savedParameters=structuredClone(event.detail.parameters);preview.querySelector('global-parameter-fields').value=structuredClone(event.detail.parameters);});
      preview.addEventListener('action-dialog-confirm',event=>{modal.savedFunctions=structuredClone(event.detail.functions||[]);modal.savedParameters=structuredClone(event.detail.parameters);});
    }
  }
  const title=document.createElement('h3');title.textContent='按钮与弹窗';
  const scroll=document.createElement('div');scroll.className='action-dialog-table-scroll';scroll.append(table);
  header.closest('section').append(title,scroll);
});
