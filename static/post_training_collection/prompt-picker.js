/* Prompt references retain their original IDs, versions and text. */
(() => {
  'use strict';
  const esc = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let control, selected=[], catalog=[], onChange, query='';
  const popup=document.createElement('div');
  popup.id='dc-prompt-popup';popup.className='dc-prompt-popup';popup.setAttribute('popover','auto');
  popup.setAttribute('role','dialog');popup.setAttribute('aria-label','选择任务提示词');
  document.body.append(popup);
  const isOpen=()=>popup.matches(':popover-open');
  function steps(prompt) {
    if(Array.isArray(prompt.steps)&&prompt.steps.length)return prompt.steps.map(step=>typeof step==='string'?step:step.text||step.content||'').filter(Boolean);
    return String(prompt.text||'').split(/\r?\n/).map(line=>line.trim()).filter(Boolean);
  }
  function render(prompts) {
    return `<div class="dc-prompt-field" id="dc-prompts"><a class="dc-prompt-create" href="/data/prompts" target="_blank" rel="noopener">+ 去创建</a><div class="dc-prompt-select"><div class="dc-prompt-chips">${prompts.map(p=>`<span class="dc-prompt-chip"><span title="${esc(p.name)}">${esc(p.name)}</span><button type="button" data-prompt-remove="${esc(p.id)}" aria-label="移除 ${esc(p.name)}">×</button></span>`).join('')}</div><button type="button" class="dc-prompt-trigger" data-action="pick-prompts" aria-label="选择任务提示词" aria-haspopup="dialog" aria-controls="dc-prompt-popup" aria-expanded="false"><span>${prompts.length?'':'请选择任务提示词'}</span><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></button></div>${prompts.length?`<div class="dc-prompt-preview" tabindex="0" role="region" aria-label="已选任务提示词内容">${prompts.map(p=>{const lines=steps(p);return `<section class="dc-prompt-group"><div class="dc-prompt-group-head"><strong>${esc(p.name)}</strong><span class="dc-prompt-step-count">${lines.length}步</span></div><ol>${lines.map(line=>`<li>${esc(line.replace(/^\d+[.、)）]\s*/,''))}</li>`).join('')}</ol></section>`;}).join('')}</div>`:''}</div>`;
  }
  function mount(container,prompts,options,change) {
    control=container;selected=prompts;catalog=options;onChange=change;
    if(!control){if(isOpen())popup.hidePopover();return;}
    control.addEventListener('click',event=>{
      const remove=event.target.closest('[data-prompt-remove]');
      if(remove){event.preventDefault();commit(selected.filter(p=>p.id!==remove.dataset.promptRemove));control.querySelector('[data-action="pick-prompts"]').focus({preventScroll:true});return;}
      if(event.target.closest('.dc-prompt-select')&&!event.target.closest('button'))toggle();
    });
    if(isOpen()){drawOptions();position();control.querySelector('[data-action="pick-prompts"]').setAttribute('aria-expanded','true');}
  }
  function position() {
    if(!control?.isConnected)return;
    const rect=control.querySelector('.dc-prompt-select').getBoundingClientRect();
    const width=Math.min(rect.width,innerWidth-24), height=Math.min(320,innerHeight-24);
    const below=innerHeight-rect.bottom-12,above=rect.top-12;
    const down=below>=height||below>=above,available=Math.max(120,down?below:above);
    popup.style.width=width+'px';popup.style.maxHeight=Math.min(height,available)+'px';
    popup.style.left=Math.max(12,Math.min(rect.left,innerWidth-width-12))+'px';
    popup.style.top=(down?rect.bottom+6:Math.max(12,rect.top-Math.min(height,available)-6))+'px';
  }
  function drawOptions() {
    const matches=catalog.filter(p=>[p.name,p.text,p.scene,p.version,...steps(p)].join(' ').toLocaleLowerCase().includes(query.toLocaleLowerCase()));
    popup.querySelector('.dc-prompt-options').innerHTML=matches.length?matches.map(p=>`<label class="dc-prompt-option"><input type="checkbox" data-prompt-choice="${esc(p.id)}" ${selected.some(x=>x.id===p.id)?'checked':''}><span><strong>${esc(p.name)}</strong><small>${esc(p.version)}${p.scene?' · '+esc(p.scene):''}</small></span></label>`).join(''):'<p class="dc-prompt-no-results">没有匹配的任务提示词</p>';
  }
  function toggle() {
    if(!control)return;
    if(isOpen()){popup.hidePopover();return;}
    query='';popup.innerHTML='<input type="search" class="dc-input dc-prompt-search" aria-label="搜索任务提示词" placeholder="搜索名称、内容或场景"><div class="dc-prompt-options"></div>';
    drawOptions();position();popup.showPopover();popup.querySelector('input[type="search"]').focus({preventScroll:true});
  }
  function commit(prompts) { selected=prompts;onChange(prompts); }
  popup.addEventListener('input',event=>{if(event.target.type==='search'){query=event.target.value;drawOptions();}});
  popup.addEventListener('change',event=>{
    const input=event.target;if(!input.hasAttribute('data-prompt-choice'))return;
    const id=input.dataset.promptChoice;
    commit(input.checked?[...selected,catalog.find(p=>p.id===id)]:selected.filter(p=>p.id!==id));
    [...popup.querySelectorAll('[data-prompt-choice]')].find(el=>el.dataset.promptChoice===id)?.focus({preventScroll:true});
  });
  popup.addEventListener('toggle',()=>control?.querySelector('[data-action="pick-prompts"]')?.setAttribute('aria-expanded',String(isOpen())));
  popup.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();popup.hidePopover();control?.querySelector('[data-action="pick-prompts"]')?.focus({preventScroll:true});}});
  addEventListener('resize',()=>{if(isOpen())position();});
  addEventListener('scroll',()=>{if(isOpen())position();},true);
  window.CollectionPromptPicker=Object.freeze({render,mount,toggle});
})();
