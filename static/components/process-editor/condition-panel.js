(() => {
  window.syncConditionNodePreview=(node,config)=>{
    if(!node?.classList.contains('condition-cases'))return;
    const row=node.querySelector('.branch-row:not(.condition-fallback)');if(!row)return;
    row.querySelectorAll('.condition-expression').forEach(element=>element.remove());
    const branch=config.cases?.[0],conditions=branch?.conditions||[];
    const label=row.querySelector('.condition-case-label span');if(label)label.textContent=branch?.name||'条件 1';
    (conditions.length?conditions:[null]).forEach((condition,index)=>{
      const expression=document.createElement('div');expression.className='condition-expression';
      const text=document.createElement('span');text.textContent=condition?`${condition.field} ${condition.operator} ${condition.value} · ${condition.ratio}%`:'条件未设置';text.title=text.textContent;expression.append(text);
      if(index<conditions.length-1){const join=document.createElement('b');join.textContent='OR';expression.append(join);}
      row.append(expression);
    });
    const height=42+Math.max(1,conditions.length)*32;row.style.height=height+'px';node.style.height=(56+height+40)+'px';
    const ports=node.querySelectorAll(':scope > .port');
    ports.forEach((port,index)=>{port.style.top=((index<2?56+height/2:56+height+20)-4)+'px';});
  };
  const icon=new URL('../../pages/process-editor/assets/condition-fix.svg',document.currentScript.src).href;
  class ConditionPanel extends HTMLElement {
    connectedCallback(){
      if(this.childElementCount)return;
      this.innerHTML=`<aside class="condition-panel"><header class="condition-panel__head"><span class="node-icon blue"><img src="${icon}" alt=""></span><div><h2>条件分支</h2><p>根据配置条件进入对应分支</p></div></header><form><div class="condition-panel__body"><node-info variant="basic" name="供应商抽验" description="供应商抽验"></node-info><div data-cases></div><text-button variant="outline" icon="plus" data-add-case>添加条件</text-button><section class="condition-panel__else"><strong>ELSE</strong><span>固定分支</span><p>所有 IF / ELIF 条件均不满足时执行</p></section></div><footer><span role="status"></span><text-button variant="primary" data-save>保存</text-button></footer></form></aside>`;
      this.querySelector('[data-add-case]').remove();
      this.querySelector('.condition-panel__else').innerHTML='<strong>ELSE · 其他</strong><p>未命中以上任一分支的数据统一进入兜底分支。</p>';
      const originalInfo=this.querySelector('node-info');
      const info=document.createElement('node-info');
      for(const attribute of originalInfo.attributes)info.setAttribute(attribute.name,attribute.value);
      info.setAttribute('node-id','condition_1');originalInfo.replaceWith(info);
      this.querySelector('h2').textContent=info.querySelector('input[name="name"]').value;
      this.addCase(true);
      this.querySelector('.condition-panel__head p').textContent='条件节点';
      window.applyProcessPanelActions?.(this);
      this.addEventListener('click',event=>{
        const removeCase=event.target.closest('[data-remove-case]');if(removeCase){removeCase.closest('.condition-panel__case').remove();this.renumber();}
        if(event.target.closest('[data-save]'))this.querySelector('form').requestSubmit();
      });
      this.querySelector('form').addEventListener('submit',event=>{
        event.preventDefault();this.savedValue=this.value;
        this.dispatchEvent(new CustomEvent('node-properties-save',{bubbles:true,detail:this.savedValue}));
        this.querySelector('[role="status"]').textContent='配置已保存到当前示例';
      });
    }
    addCase(initial=false){
      const card=document.createElement('section');card.className='condition-panel__case';
      card.innerHTML='<div class="condition-panel__branch-intro"><h3>分支设置</h3><p>IF 分支内多组规则为「或（OR）」关系；每条条件由「筛选项 / 操作符 / 值」三元组组成，比例独立生效。</p></div><form-condition-group></form-condition-group>';
      this.querySelector('[data-cases]').append(card);this.renumber();
    }
    renumber(){this.querySelectorAll('.condition-panel__case').forEach((card,i)=>{card.querySelector('[data-branch-kind]').textContent=i?'ELIF':'IF';});}
    get value(){return {...this.querySelector('node-info').value,cases:[...this.querySelectorAll('form-condition-group')].map(group=>group.value),customInputs:[]};}
  }
  customElements.define('condition-panel',ConditionPanel);
})();
