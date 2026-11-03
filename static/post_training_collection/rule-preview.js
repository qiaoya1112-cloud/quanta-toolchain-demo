/* Read-only, version-pinned rule preview shared by task creation and details. */
(() => {
  'use strict';
  const form=document.getElementById('drawerProcessingTaskForm');if(!form)return;
  const holder=document.getElementById('processingTaskAssignments');
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const dialog=document.createElement('dialog');dialog.id='processingRulePreview';dialog.className='dpr-rule-preview';
  dialog.setAttribute('aria-labelledby','processingRulePreviewTitle');
  dialog.innerHTML='<header><h3 id="processingRulePreviewTitle">规则预览</h3><button type="button" data-preview-close aria-label="关闭规则预览">×</button></header><div class="dpr-rule-preview-body" aria-live="polite"></div><footer><button type="button" class="btn" data-preview-close>关闭</button></footer>';
  document.body.append(dialog);
  const body=dialog.querySelector('.dpr-rule-preview-body');
  let trigger,query,controller,requestEpoch=0,mounted=[];
  function releaseDetail(){
    window.ruleCloseTagPicker?.();
    mounted.forEach(({element,parent,next})=>parent.insertBefore(element,next?.parentNode===parent?next:null));mounted=[];
  }
  async function render(rule,epoch){
    await window.dprLoadRuleEditor(rule.project);
    if(epoch!==requestEpoch||!dialog.open)return;
    const editor=document.getElementById('drawerRuleCreate');
    editor.dataset.mode='detail';editor.dataset.ruleId=rule.id||'';
    // Use the exact same fields, configuration tables and readonly renderer
    // as rule management; the task API supplies the pinned version's content.
    window.ruleApplyDetailContent(rule,true);
    const history=document.getElementById('ruleVersionPanel');if(history)history.hidden=true;
    editor.querySelectorAll('.rule-save-error,#ruleNameError').forEach(e=>e.hidden=true);
    body.replaceChildren();
    [editor,document.getElementById('ruleTagModal')].filter(Boolean).forEach(element=>{
      mounted.push({element,parent:element.parentNode,next:element.nextSibling});body.append(element);
    });
    document.getElementById('processingRulePreviewTitle').textContent=rule.name+' · '+String(rule.version||'').toUpperCase();
  }
  async function load(){
    controller?.abort();controller=new AbortController();const epoch=++requestEpoch;
    releaseDetail();body.setAttribute('aria-busy','true');body.innerHTML='<p class="dpr-rule-preview-empty" role="status">正在读取规则…</p>';
    try{
      const response=await fetch('/api/processing-rules/preview?'+query,{cache:'no-store',signal:controller.signal});
      const data=await response.json();if(!response.ok)throw Error(data.error||'规则读取失败，请重试');
      if(epoch===requestEpoch&&dialog.open)await render(data.rule,epoch);
    }catch(error){
      if(error.name==='AbortError'||epoch!==requestEpoch||!dialog.open)return;
      body.innerHTML='<div class="dpr-rule-preview-error" role="alert"><p>'+esc(error.message||'规则读取失败，请重试')+'</p><button type="button" class="btn" data-preview-retry>重试</button></div>';
    }finally{if(epoch===requestEpoch)body.removeAttribute('aria-busy');}
  }
  function sourceCard(card,flow){
    const nodes=flow?.human_nodes||[];let current=card;
    while(current&&window.dprNodeRuleConfig(flow,current.dataset.node).mode==='inherit'){
      const index=nodes.indexOf(current.dataset.node);
      if(index<=0)return null;
      current=[...holder.querySelectorAll('.dpr-flow-node-card')].find(c=>c.dataset.node===nodes[index-1]);
    }
    return current;
  }
  function decorate(){
    const flow=window.dprFlowByName(window.DPR_SELECTED_FLOWS[window.DPR_ACTIVE_ASSIGNMENT_STAGE]);
    holder.querySelectorAll('.dpr-flow-node-card').forEach(card=>{
      const module=card.querySelector('.dpr-node-rule-module');if(!module)return;
      let button=module.querySelector('.dpr-rule-preview-trigger');
      const config=window.dprNodeRuleConfig(flow,card.dataset.node);
      if(config.mode==='none'){button?.remove();return;}
      if(!button){
        button=document.createElement('button');button.type='button';button.className='dpr-rule-preview-trigger';button.textContent='预览规则';
        const select=module.querySelector('.dpr-node-rule-select');
        if(select){const field=document.createElement('div');field.className='dpr-rule-preview-field';select.before(field);field.append(select,button);}
        else module.append(button);
      }
      const selected=sourceCard(card,flow)?.querySelector('.dpr-node-rule-select')?.value;
      button.disabled=!selected;button.title=selected?'':'请先选择规则';
      button.setAttribute('aria-label','预览'+card.dataset.node+'节点规则');
    });
  }
  holder.addEventListener('click',event=>{
    const button=event.target.closest('.dpr-rule-preview-trigger');if(!button)return;
    const card=button.closest('.dpr-flow-node-card'),stage=window.DPR_ACTIVE_ASSIGNMENT_STAGE;
    const flow=window.dprFlowByName(window.DPR_SELECTED_FLOWS[stage]);
    const value=sourceCard(card,flow)?.querySelector('.dpr-node-rule-select')?.value;if(!value)return;
    query=new URLSearchParams({value,stage,project:document.getElementById('processingTaskProject').value});
    if(card.dataset.ruleTaskId&&form.dataset.mode!=='new'){query.set('task_id',card.dataset.ruleTaskId);query.set('node',card.dataset.node);}
    trigger=button;document.getElementById('processingRulePreviewTitle').textContent='规则预览';
    dialog.showModal();body.scrollTop=0;load();
  });
  holder.addEventListener('change',decorate);
  dialog.addEventListener('click',event=>{
    if(event.target.closest('[data-preview-close]'))dialog.close();
    if(event.target.closest('[data-preview-retry]'))load();
    if(event.target===dialog){const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right)dialog.close();}
  });
  dialog.addEventListener('close',()=>{controller?.abort();++requestEpoch;releaseDetail();body.replaceChildren();body.removeAttribute('aria-busy');if(trigger?.isConnected)trigger.focus();});
  dialog.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();if(document.getElementById('ruleTagModal')?.classList.contains('active'))window.ruleCloseTagPicker();else dialog.close();}},true);
  dialog.addEventListener('cancel',event=>{event.preventDefault();dialog.close();});
  // Cards are rebuilt on flow changes and restored from the original markup cache.
  new MutationObserver(decorate).observe(holder,{childList:true,subtree:true});
  decorate();
})();
