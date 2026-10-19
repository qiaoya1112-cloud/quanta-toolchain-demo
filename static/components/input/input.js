(() => {
  let selectId=0;
  function styleSelect(host,control){
    const trigger=document.createElement('button');trigger.type='button';trigger.className='form-select__trigger';
    trigger.setAttribute('role','combobox');trigger.setAttribute('aria-haspopup','listbox');trigger.setAttribute('aria-expanded','false');
    trigger.setAttribute('aria-label',host.getAttribute('label')||control.getAttribute('aria-label')||control.name||'选择选项');
    const menu=document.createElement('div');menu.className='form-select__menu';menu.id=`form-select-menu-${++selectId}`;
    menu.setAttribute('popover','auto');menu.setAttribute('role','listbox');menu.setAttribute('aria-label',trigger.getAttribute('aria-label'));
    if(control.multiple)menu.setAttribute('aria-multiselectable','true');
    trigger.setAttribute('aria-controls',menu.id);
    control.classList.add('form-select__native');control.tabIndex=-1;control.setAttribute('aria-hidden','true');
    control.after(trigger);host.append(menu);
    let active=control.selectedIndex;
    const isOpen=()=>menu.matches(':popover-open');
    const sync=()=>{trigger.textContent=[...control.selectedOptions].map(option=>option.textContent).join('、')||'请选择';trigger.disabled=control.disabled;trigger.setAttribute('aria-required',String(control.required));};
    const highlight=()=>{
      [...menu.children].forEach(el=>el.classList.toggle('is-active',Number(el.dataset.optionIndex)===active));
      const option=menu.querySelector(`[data-option-index="${active}"]`);if(option){trigger.setAttribute('aria-activedescendant',option.id);option.scrollIntoView({block:'nearest'});}
    };
    const choose=index=>{
      const option=control.options[index];if(!option||option.disabled||option.parentElement.disabled)return;
      if(control.multiple)option.selected=!option.selected;else control.selectedIndex=index;
      sync();control.dispatchEvent(new Event('input',{bubbles:true}));control.dispatchEvent(new Event('change',{bubbles:true}));
      if(control.multiple){open();active=index;highlight();}else menu.hidePopover();trigger.focus();
    };
    const open=()=>{
      if(control.disabled)return;
      menu.replaceChildren();
      [...control.options].forEach((option,index)=>{
        if(option.hidden)return;
        const item=document.createElement('div');item.className='form-select__option';item.dataset.optionIndex=index;item.id=`${menu.id}-${index}`;item.setAttribute('role','option');
        item.setAttribute('aria-selected',String(option.selected));item.setAttribute('aria-disabled',String(option.disabled||Boolean(option.parentElement.disabled)));
        const text=document.createElement('span');text.textContent=option.textContent;item.append(text);
        if(option.selected)item.insertAdjacentHTML('beforeend','<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>');
        item.addEventListener('mousedown',event=>event.preventDefault());item.addEventListener('click',event=>{event.preventDefault();choose(index);});menu.append(item);
      });
      const rect=trigger.getBoundingClientRect();menu.style.width=Math.min(rect.width,innerWidth-16)+'px';menu.style.left=Math.max(8,Math.min(rect.left,innerWidth-rect.width-8))+'px';
      const height=Math.min(248,control.options.length*38+10);const below=innerHeight-rect.bottom-8,above=rect.top-8;
      const up=below<height&&above>below;menu.style.maxHeight=Math.max(38,Math.min(248,up?above-6:below-6))+'px';
      menu.style.top=up?'auto':rect.bottom+6+'px';menu.style.bottom=up?innerHeight-rect.top+6+'px':'auto';
      active=control.selectedIndex;menu.showPopover();trigger.setAttribute('aria-expanded','true');highlight();
    };
    trigger.addEventListener('click',()=>isOpen()?menu.hidePopover():open());
    trigger.addEventListener('keydown',event=>{
      if(['ArrowDown','ArrowUp','Home','End','Enter',' '].includes(event.key)){
        event.preventDefault();if(!isOpen()){open();return;}
        if(event.key==='Enter'||event.key===' '){choose(active);return;}
        const enabled=[...control.options].map((o,i)=>!o.hidden&&!o.disabled&&!o.parentElement.disabled?i:-1).filter(i=>i>=0);
        let pos=enabled.indexOf(active);
        if(event.key==='Home')pos=0;else if(event.key==='End')pos=enabled.length-1;else pos=Math.max(0,Math.min(enabled.length-1,pos+(event.key==='ArrowDown'?1:-1)));
        active=enabled[pos];highlight();
      }
      if((event.key==='Escape'||event.key==='Tab')&&isOpen())menu.hidePopover();
    });
    const close=()=>{if(isOpen())menu.hidePopover();};
    const scrollClose=event=>{if(!menu.contains(event.target))close();};
    menu.addEventListener('toggle',()=>{
      trigger.setAttribute('aria-expanded',String(isOpen()));
      if(isOpen()){window.addEventListener('resize',close);document.addEventListener('scroll',scrollClose,true);}
      else{trigger.removeAttribute('aria-activedescendant');window.removeEventListener('resize',close);document.removeEventListener('scroll',scrollClose,true);}
    });
    control.addEventListener('change',sync);control.addEventListener('invalid',()=>trigger.focus());
    control.form?.addEventListener('reset',()=>setTimeout(sync,0));
    new MutationObserver(sync).observe(control,{attributes:true,childList:true,subtree:true});
    host.syncSelect=sync;sync();
  }
  class FormInput extends HTMLElement {
    connectedCallback() {
      if (this.control) return;
      const existing=this.querySelector('input,textarea');
      if(existing){
        this.control=existing;existing.classList.add('form-input__control');
        existing.setAttribute('autocomplete',this.getAttribute('autocomplete')||existing.getAttribute('autocomplete')||'off');
        existing.addEventListener('input',()=>this.dispatchEvent(new CustomEvent('value-change',{bubbles:true,detail:{name:existing.name,value:existing.value}})));
        return;
      }
      const label = document.createElement('label');
      label.className = 'form-input';
      const caption = document.createElement('span');
      caption.className = 'form-input__label';
      caption.textContent = this.getAttribute('label') || '';
      const control = document.createElement(this.hasAttribute('multiline') ? 'textarea' : 'input');
      control.className = 'form-input__control';
      control.setAttribute('autocomplete',this.getAttribute('autocomplete')||'off');
      if (control.tagName === 'INPUT') control.type = 'text';
      control.value = this.getAttribute('value') || '';
      control.placeholder = this.getAttribute('placeholder') || '';
      control.name = this.getAttribute('name') || '';
      control.disabled = this.hasAttribute('disabled');
      control.readOnly = this.hasAttribute('readonly');
      control.setAttribute('aria-label', this.getAttribute('label') || this.getAttribute('aria-label') || '输入内容');
      if (caption.textContent) label.append(caption);
      label.append(control);
      this.append(label);
      this.control = control;
      control.addEventListener('input', () => this.dispatchEvent(new CustomEvent('value-change', {bubbles:true, detail:{name:control.name,value:control.value}})));
    }
    get value() { return this.control?.value ?? this.getAttribute('value') ?? ''; }
    set value(value) { if(this.control) this.control.value=value; else this.setAttribute('value',value); }
  }
  if (!customElements.get('form-input')) customElements.define('form-input', FormInput);
  for(const [tag,type] of [['form-select','select'],['form-radio','radio'],['form-checkbox','checkbox']]){
    if(customElements.get(tag))continue;
    customElements.define(tag,class extends HTMLElement{
      connectedCallback(){
        if(this.control)return;
        let control=this.querySelector(type==='select'?'select':'input');
        if(!control){
          control=document.createElement(type==='select'?'select':'input');
          if(type==='select')control.append(...this.querySelectorAll('option'));
          else control.type=type;
          for(const attr of ['name','value','disabled','required','checked','multiple'])if(this.hasAttribute(attr))control.setAttribute(attr,this.getAttribute(attr));
          const label=document.createElement('label');label.className=type==='select'?'form-input':'form-choice';
          const caption=document.createElement('span');caption.textContent=this.getAttribute('label')||'';
          if(type==='select'){caption.className='form-input__label';if(caption.textContent)label.append(caption);label.append(control);}
          else label.append(control,caption);
          this.append(label);
          if(type==='select'&&this.hasAttribute('value'))control.value=this.getAttribute('value');
        }
        this.control=control;control.classList.add(type==='select'?'form-select__control':'form-choice__control');
        if(type==='select')styleSelect(this,control);
        control.addEventListener('change',()=>this.dispatchEvent(new CustomEvent('value-change',{bubbles:true,detail:{name:control.name,value:control.value,checked:control.checked}})));
      }
      get value(){return this.control?.value||'';}
      set value(value){if(this.control){this.control.value=value;this.syncSelect?.();}else this.setAttribute('value',value);}
      get checked(){return Boolean(this.control?.checked);}
      set checked(value){if(this.control)this.control.checked=Boolean(value);else this.toggleAttribute('checked',Boolean(value));}
    });
  }
  // Adopt native controls without replacing them: keep labels, validation,
  // radio grouping, FormData and existing event handlers intact.
  window.enhancePropertyControls=root=>{
    root.querySelectorAll('input,textarea,select').forEach(control=>{
      if(control.closest('form-input,form-select,form-radio,form-checkbox'))return;
      const tag=control.tagName==='SELECT'?'form-select':control.type==='radio'?'form-radio':control.type==='checkbox'?'form-checkbox':'form-input';
      const wrapper=document.createElement(tag);wrapper.setAttribute('adopted','');
      if(control.name)wrapper.setAttribute('name',control.name);
      const marker=document.createTextNode('');control.replaceWith(marker);
      wrapper.append(control);marker.replaceWith(wrapper);
    });
  };
  class NodeInfo extends HTMLElement{
    connectedCallback(){
      if(this.querySelector('.node-info'))return;
      this.innerHTML='<section class="node-info"><h3>节点信息</h3><label>节点名称<input name="name" required><small>workflow 内唯一的非空字符串</small></label><label>节点描述<textarea name="description" rows="3" placeholder="可选，描述节点用途"></textarea></label><label>下游节点<input name="transitions" required placeholder="输入下游节点名称"><small>对应 transitions</small></label><label>节点类型<input name="type" readonly></label></section>';
      for(const key of ['name','description','transitions','type'])this.querySelector(`[name="${key}"]`).value=this.getAttribute(key)||'';
      if(this.getAttribute('variant')==='basic'){
        this.querySelector('h3').textContent='基础信息';
        this.querySelector('[name="transitions"]').closest('label').remove();
        this.querySelector('[name="type"]').closest('label').remove();
        this.querySelector('small').remove();
        this.querySelector('[name="description"]').closest('label').firstChild.textContent='描述';
      }
      if(this.hasAttribute('name-field'))this.querySelector('[name="name"]').name=this.getAttribute('name-field');
      if(this.hasAttribute('description-label'))this.querySelector('[name="description"]').closest('label').firstChild.textContent=this.getAttribute('description-label');
      if(this.hasAttribute('node-id')){
        const nameLabel=this.querySelector('input').closest('label');
        const row=document.createElement('div');row.style.cssText='display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px';
        nameLabel.replaceWith(row);row.append(nameLabel);
        const label=document.createElement('label');label.textContent='节点 ID';
        const input=document.createElement('input');input.name='nodeId';input.value=this.getAttribute('node-id');input.readOnly=true;
        label.append(input);row.append(label);
      }
      window.enhancePropertyControls(this);
      this.addEventListener('input',()=>this.dispatchEvent(new CustomEvent('node-info-change',{bubbles:true,detail:this.value})));
    }
    get value(){return Object.fromEntries([...this.querySelectorAll('input,textarea')].map(control=>[control.name,control.value]));}
    set value(values){for(const [key,value] of Object.entries(values)){const control=[...this.querySelectorAll('input,textarea')].find(item=>item.name===key);if(control)control.value=value??'';else if(['name','description','transitions','type'].includes(key))this.setAttribute(key,value??'');}}
  }
  if(!customElements.get('node-info'))customElements.define('node-info',NodeInfo);
})();
(() => {
  class FormConditionGroup extends HTMLElement {
    connectedCallback(){
      if(this.querySelector('[data-rules]'))return;
      this.innerHTML='<div class="condition-panel__case-content"><div class="condition-panel__branch-head"><strong data-branch-kind>IF</strong><form-input value="供应商抽样" aria-label="分支名称"></form-input></div><div class="form-condition-body"><div data-rules></div><text-button variant="text" icon="plus" class="form-condition-add" data-add-rule>添加条件与比例</text-button></div></div>';
      const empty=document.createElement('p');empty.className='form-condition-empty';empty.textContent='尚未配置条件';this.querySelector('[data-rules]').after(empty);
      if(!this.hasAttribute('empty')){this.addRule(this,'供应商 A',50);this.addRule(this,'供应商 B',30);}
      this.updateRules(this);
      this.addEventListener('click',event=>{
        if(event.target.closest('[data-add-rule]'))this.addRule(this);
        const remove=event.target.closest('[data-remove-rule]');
        if(remove&&!remove.disabled){remove.closest('.condition-panel__rule').remove();this.updateRules(this);}
        if(event.target.closest('[data-add-rule],[data-remove-rule]'))this.dispatchEvent(new Event('change',{bubbles:true}));
      });
    }
    addRule(card,supplier='供应商 A',ratio=50){
      const row=document.createElement('div');row.className='condition-panel__rule';
      row.innerHTML=`<span class="condition-panel__or">或</span><div class="condition-panel__rule-fields"><form-select label="筛选项"><option>供应商</option><option>任务类型</option></form-select><form-select label="操作符"><option>等于</option><option>不等于</option></form-select><form-select label="值"><option>供应商 A</option><option>供应商 B</option></form-select><label>比例<div class="condition-panel__ratio"><input type="number" min="0" max="100" value="${ratio}" required aria-label="抽样比例"><span>%</span></div></label><button type="button" data-remove-rule aria-label="删除条件">×</button></div>`;
      // This example demonstrates supplier sampling only.
      row.querySelector('[data-remove-rule]').innerHTML='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/></svg>';
      row.querySelector('form-select').querySelector('option:last-child').remove();
      card.querySelector('[data-rules]').append(row);row.querySelectorAll('form-select')[2].value=supplier;this.updateRules(card);
    }
    updateRules(card){const rows=card.querySelectorAll('.condition-panel__rule');rows.forEach((row,i)=>{row.querySelector('.condition-panel__or').hidden=i===0;row.querySelector('[data-remove-rule]').disabled=false;});card.querySelector('.form-condition-empty').hidden=rows.length>0;}

    get value(){return {name:this.querySelector('form-input').value,join:'OR',conditions:[...this.querySelectorAll('.condition-panel__rule')].map(row=>({field:row.querySelectorAll('form-select')[0].value,operator:row.querySelectorAll('form-select')[1].value,value:row.querySelectorAll('form-select')[2].value,ratio:Number(row.querySelector('input').value)}))};}
  }
  customElements.define('form-condition-group',FormConditionGroup);
})();
