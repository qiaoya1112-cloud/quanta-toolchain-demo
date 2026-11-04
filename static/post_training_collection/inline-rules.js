/* Add inline creation to the original processing form without replacing its layout. */
(() => {
  const form=document.getElementById('drawerProcessingTaskForm'); if(!form)return;
  const holder=document.getElementById('processingTaskAssignments'), projectControl=document.getElementById('processingTaskProject');
  const legacyChoices=(window.DPR_NODE_RULES || []).map(r=>({...r}));
  let project='', rights={create:false,publish:false}, epoch=0, editorPromise;
  const typesFor = flow => flow.rule_types || (flow.stage==='质检'?['质检']:flow.name.includes('端到端')?['语义标注']:['语义标注','动作标注','标签标注']);
  function currentReference(value, rules) {
    const match=String(value || '').match(/^rule:([^@]+)@[1-9]\d*$/);
    return match ? (rules || []).find(rule=>rule.id===match[1])?.value || value : value;
  }
  function addOptions() {
    const flow=window.dprFlowByName(window.DPR_SELECTED_FLOWS[window.DPR_ACTIVE_ASSIGNMENT_STAGE]);
    if(!flow)return;
    holder.querySelectorAll('.dpr-flow-node-card').forEach(card=>{
      const select=card.querySelector('.dpr-node-rule-select');if(!select)return;
      const config=window.dprNodeRuleConfig(flow,card.dataset.node);
      if(!['task_custom','fixed'].includes(config.mode))return;
      const fixed=config.mode==='fixed',isNew=form.dataset.mode==='new';
      const selected=fixed ? (isNew ? currentReference(config.rule,window.DPR_INLINE_RULES) : select.value || config.rule) : select.value;
      const oldLabel=select.selectedOptions[0]?.textContent;
      select.replaceChildren(new Option(fixed?'流程指定规则':'请选择规则',''));
      legacyChoices.filter(r=>r.stage===flow.stage && typesFor(flow).includes(r.rule_type) && (!isNew || !(window.DPR_INLINE_PUBLISHED_VERSIONS||[]).some(p=>p.name===r.name&&p.project===project&&p.stage===flow.stage))).forEach(r=>select.add(new Option(isNew?r.name:r.name+' · '+r.version,r.name+' '+r.version)));
      const choices = [...(window.DPR_INLINE_RULES||[])];
      const pinned = (window.DPR_INLINE_PUBLISHED_VERSIONS||[]).find(r=>r.value===selected);
      if (pinned && (!isNew || fixed) && !choices.some(r=>r.value===selected)) choices.push(pinned);
      choices.filter(r=>r.project===project&&r.stage===flow.stage&&typesFor(flow).includes(r.rule_type)).forEach(r=>select.add(new Option(isNew?r.name:r.name+' · '+r.version.toUpperCase()+(fixed?' · 流程固定':''),r.value)));
      if([...select.options].some(o=>o.value===selected))select.value=selected;
      else if(selected){
        const unavailable=new Option((window.DPR_INLINE_RULE_LABELS?.[selected]||oldLabel||selected).replace(/（[^）]+）$/,'')+'（请重新选择）',selected,true,true);
        unavailable.disabled=true;select.add(unavailable);select.value=selected;
      }
      if(fixed)select.disabled=true;
      const validate=()=>{
        const invalid=!!select.value&&!!select.selectedOptions[0]?.disabled || (fixed&&pinned?.status!=='enabled');
        select.dataset.unavailable=String(isNew&&invalid);
        select.setCustomValidity(isNew&&invalid?'规则已变化或停用，请重新选择当前启用版本':'');
        select.setAttribute('aria-invalid',String(isNew&&invalid));
      };
      select.onchange=validate;validate();
    });
  }
  function decorate() {
    const flow=window.dprFlowByName(window.DPR_SELECTED_FLOWS[window.DPR_ACTIVE_ASSIGNMENT_STAGE]);
    holder.querySelectorAll('.dpr-inline-rule-create').forEach(e=>e.remove());
    holder.querySelectorAll('.dpr-inline-rule-refresh').forEach(e=>e.remove());
    holder.querySelectorAll('.dpr-inline-rule-hint').forEach(e=>e.remove());
    if(!flow||!project||form.dataset.mode!=='new')return;
    holder.querySelectorAll('.dpr-flow-node-card').forEach(card=>{
      const select=card.querySelector('.dpr-node-rule-select');
      if(!select||!['task_custom','fixed'].includes(window.dprNodeRuleConfig(flow,card.dataset.node).mode))return;
      const head=card.querySelector('.dpr-node-rule-module .dpr-node-config-module-head');
      const hint=document.createElement('span');hint.className='dpr-inline-rule-hint';hint.textContent='请选择已发布规则';head.append(hint);
      if(select.disabled||window.dprNodeRuleConfig(flow,card.dataset.node).mode!=='task_custom')return;
      if(!rights.create||!rights.edit||!rights.publish)return;
      const button=document.createElement('button');button.type='button';button.className='dpr-inline-rule-create';button.textContent='新建规则';
      button.onclick=()=>openEditor(button,card,flow);
      head.append(button);
    });
  }
  async function refresh() {
    const current=++epoch;project=projectControl.value;rights={create:false,publish:false};decorate();
    try{
      const response=await fetch('/api/processing-rules?project='+encodeURIComponent(project),{cache:'no-store'});
      if(!response.ok)throw Error('规则读取失败');
      const data=await response.json();if(current!==epoch)return;
      rights=data.permissions;window.DPR_INLINE_RULES=data.rules;window.DPR_INLINE_PUBLISHED_VERSIONS=data.published_versions;window.DPR_INLINE_RULE_LABELS=data.rule_labels;addOptions();decorate();
      // The original processing-result filters use name/version as their scope.
      // Register the same saved catalog there, without changing selected conditions.
      for(const rule of data.published_versions || data.rules){
        if(!window.DPR_NODE_RULES.some(r=>r.stage===rule.stage&&r.name===rule.name&&r.version===rule.version&&r.inlineProject===rule.project))
          window.DPR_NODE_RULES.push({stage:rule.stage,name:rule.name,version:rule.version,inlineProject:rule.project});
      }
    }catch(e){if(current===epoch)window.toast('规则读取失败，请重试');}
  }
  async function loadEditor(readonlyProject) {
    if(document.getElementById('drawerRuleCreate'))return;
    if(editorPromise)return editorPromise;
    editorPromise=(async()=>{
      const response=await fetch('/data/rules/editor-fragment?'+new URLSearchParams({project:readonlyProject??project,...(readonlyProject!==undefined?{readonly:'1'}:{})}),{cache:'no-store'});
      if(!response.ok)throw Error(response.status===403?'没有创建规则权限':'规则表单加载失败，请重试');
      const host=document.createElement('div');host.innerHTML=await response.text();
      const scripts=[...host.querySelectorAll('script')];scripts.forEach(s=>s.remove());document.body.append(host);
      for(const script of scripts){const node=document.createElement('script');
        if(script.src){await new Promise((resolve,reject)=>{node.src=script.src;node.onload=resolve;node.onerror=reject;document.body.append(node);});}
        else{node.textContent=script.textContent;document.body.append(node);}
      }
    })();
    try{await editorPromise;}catch(e){document.getElementById('drawerRuleCreate')?.parentElement.remove();throw e;}finally{editorPromise=null;}
  }
  window.dprLoadRuleEditor=loadEditor;
  async function openEditor(button,card,flow) {
    if(!rights.create||!rights.edit||!rights.publish){window.toast('没有创建、编辑或发布规则权限');return;}
    button.disabled=true;
    try{
      await loadEditor();
      const node=card.dataset.node,stage=flow.stage,capturedProject=projectControl.value,types=typesFor(flow);
      if(!card.isConnected||capturedProject!==project)return;
      window.openRuleCreate();
      const select=card.querySelector('.dpr-node-rule-select');
      window.inlineRuleContext={project:capturedProject,stage,types,flow:flow.name,node,trigger:button,use:async rule=>{
        if(projectControl.value!==capturedProject||!select.isConnected||card.dataset.node!==node||window.DPR_ACTIVE_ASSIGNMENT_STAGE!==stage||window.DPR_SELECTED_FLOWS[stage]!==flow.name||rule.project!==capturedProject||rule.stage!==stage||!types.includes(rule.rule_type))throw Error('规则已保存，请在当前节点重新选择');
        window.DPR_INLINE_RULES=window.DPR_INLINE_RULES||[];window.DPR_INLINE_RULES.unshift(rule);if(!window.DPR_NODE_RULES.some(r=>r.stage===rule.stage&&r.name===rule.name&&r.version===rule.version&&r.inlineProject===rule.project))window.DPR_NODE_RULES.push({stage:rule.stage,name:rule.name,version:rule.version,inlineProject:rule.project});
        if(![...select.options].some(o=>o.value===rule.value))select.add(new Option(rule.name,rule.value));
        select.value=rule.value;select.dispatchEvent(new Event('change',{bubbles:true}));
      }};
      const p=document.getElementById('ruleCreateProject');if(![...p.options].some(o=>o.value===capturedProject))p.add(new Option(capturedProject,capturedProject));p.value=capturedProject;p.disabled=true;
      const s=document.getElementById('ruleCreateStage');s.value=stage;window.ruleCreateStageChanged(stage);s.disabled=true;
      const t=document.getElementById('ruleCreateType');[...t.options].filter(o=>!types.includes(o.value)).forEach(o=>o.remove());t.value=types[0];t.disabled=false;window.ruleCreateTypeChanged(t.value);
      button.disabled=false;form.setAttribute('inert','');await window.ruleRefreshPermissions();
      window.ruleMarkClean?.();
    }catch(e){window.toast(e.message||'规则表单加载失败，请重试');}finally{button.disabled=false;}
  }
  // These hooks run after the existing adapter restores user-entered node values.
  for(const name of ['dprShowAssignmentsForStage','dprToggleFlowStage','dprProcessingFlowChange','dprOpenProcessingTaskDrawer']){
    const original=window[name];if(!original)continue;
    window[name]=function(...args){const result=original.apply(this,args);queueMicrotask(()=>{addOptions();decorate();});if(name==='dprOpenProcessingTaskDrawer')queueMicrotask(refresh);return result;};
  }
  // Check the catalog again at submission, including nodes cached in other stages.
  // The persistent collection adapter also repeats this check on the server.
  const submit=window.dprSubmitProcessingTask;let checking=false;
  window.dprSubmitProcessingTask=async function(...args){
    if(form.dataset.mode!=='new')return submit.apply(this,args);
    if(checking)return;checking=true;
    try{
      const response=await fetch('/api/processing-rules?project='+encodeURIComponent(projectControl.value),{cache:'no-store'});
      const data=await response.json();if(!response.ok)throw Error(data.error||'规则校验失败，请重试');
      window.DPR_INLINE_RULES=data.rules;window.DPR_INLINE_PUBLISHED_VERSIONS=data.published_versions;window.DPR_INLINE_RULE_LABELS=data.rule_labels;
      for(const [stage,enabled] of Object.entries(window.DPR_ENABLED_FLOW_STAGES)){
        if(!enabled)continue;
        const flow=window.dprFlowByName(window.DPR_SELECTED_FLOWS[stage]);if(!flow)continue;
        const host=stage===window.DPR_ACTIVE_ASSIGNMENT_STAGE?holder:document.createElement('div');
        if(host!==holder)host.innerHTML=window.DPR_FLOW_ASSIGNMENT_CACHE[flow.name]||'';
        for(const card of host.querySelectorAll('.dpr-flow-node-card')){
          const config=window.dprNodeRuleConfig(flow,card.dataset.node),select=card.querySelector('.dpr-node-rule-select');
          if(!select||['inherit','none'].includes(config.mode))continue;
          const selected=config.mode==='fixed'?currentReference(config.rule,data.rules):select.value;
          if(!selected)continue; // Required-field validation stays in the original form.
          const managed=(data.published_versions||[]).find(r=>r.value===selected);
          const current=(data.rules||[]).find(r=>r.value===selected);
          const legacy=legacyChoices.find(r=>r.name+' '+r.version===selected&&r.stage===flow.stage);
          const migratedLegacy=legacy&&(data.published_versions||[]).some(r=>r.name===legacy.name&&r.project===projectControl.value&&r.stage===flow.stage);
          const applicable=rule=>rule&&rule.project===projectControl.value&&rule.stage===stage&&flow.stage===stage&&typesFor(flow).includes(rule.rule_type);
          const valid=data.permissions.use&&(selected.startsWith('rule:')
            ? applicable(current)
            : !!legacy&&typesFor(flow).includes(legacy.rule_type)&&!migratedLegacy);
          if(!valid){
            window.dprShowAssignmentsForStage(stage);addOptions();decorate();
            throw Error('规则已变化或不可用，请重新选择当前启用版本');
          }
        }
      }
      addOptions();decorate();
      return await submit.apply(this,args);
    }catch(e){window.toast(e.message||'规则校验失败，请重试');}
    finally{checking=false;}
  };
  projectControl.addEventListener('change',refresh);
  new MutationObserver(()=>{if(projectControl.value!==project)refresh();else decorate();}).observe(form,{attributes:true,attributeFilter:['data-mode','data-collection-source','aria-hidden']});
  refresh();
})();
