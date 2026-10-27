/* Local demo taxonomy. Existing task tags remain available when editing. */
(() => {
  'use strict';
  const taxonomy = [
    {name:'通用标签体系',categories:[
      {name:'任务类别',tags:['拿取','放置','递送','立放','旋转','开合','擦拭']},
      {name:'场景类别',tags:['家庭','厨房','客厅','办公室','仓储']},
      {name:'物体类别',tags:['饮料','杯子','抽屉','冰箱','白板']},
      {name:'是否移动',tags:['原地操作','移动操作']}
    ]},
    {name:'自定义标签',categories:[{name:'采集需求',tags:['补采','场景采集','饮茶场景','回归']}]},
    {name:'后训练组标签体系',categories:[
      {name:'采集类型',tags:['遥操采集','模型干预']},
      {name:'数据用途',tags:['SFT','评测']}
    ]},
    {name:'大小脑融合',categories:[{name:'执行阶段',tags:['导航','操作','交互']}]}
  ];
  const esc = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const arrow = '<span class="dc-tag-arrow" aria-hidden="true">›</span>';
  let control, selected=[], change, groups=taxonomy, group=-1, category=-1, query='', warning='';
  const popup=document.createElement('div');
  popup.id='dc-tag-popup';popup.className='dc-tag-popup';popup.setAttribute('popover','auto');
  popup.setAttribute('role','dialog');popup.setAttribute('aria-label','选择任务标签');
  document.body.append(popup);
  function chips(tags) {
    return tags.map(tag=>`<span class="dc-selected-tag"><span>${esc(tag)}</span><button type="button" data-tag-remove="${esc(tag)}" aria-label="移除标签 ${esc(tag)}">×</button></span>`).join('');
  }
  function render(tags) {
    return `<div id="dc-tags" class="dc-tag-control"><div class="dc-tag-values">${chips(tags)}</div><button type="button" class="dc-tag-trigger" data-tag-open aria-haspopup="dialog" aria-controls="dc-tag-popup" aria-expanded="false"><span>${tags.length?'继续选择':'请选择标签'}</span><span class="dc-tag-down" aria-hidden="true">⌄</span></button></div>`;
  }
  function mount(container,tags,onChange) {
    if(popup.matches(':popover-open'))popup.hidePopover();
    control=container;selected=[...tags];change=onChange;
    const known=new Set(taxonomy.flatMap(g=>g.categories.flatMap(c=>c.tags)));
    const legacy=tags.filter(tag=>!known.has(tag));
    groups=legacy.length?[...taxonomy,{name:'已关联标签',categories:[{name:'已有任务标签',tags:legacy}]}]:taxonomy;
    container.addEventListener('click',event=>{
      const remove=event.target.closest('[data-tag-remove]');
      if(remove){event.stopPropagation();selected=selected.filter(tag=>tag!==remove.dataset.tagRemove);commit();container.querySelector('[data-tag-open]').focus({preventScroll:true});return;}
      if(!event.target.closest('button')||event.target.closest('[data-tag-open]'))toggle();
    });
  }
  function position() {
    if(!control?.isConnected)return;
    const columns=query?2:1+(group>=0?1:0)+(category>=0?1:0);
    const rect=control.getBoundingClientRect(), width=Math.min(210*columns,innerWidth-24);
    let viewportBottom=innerHeight;
    const footer=document.querySelector('.dc-form-bottom');
    const footerTop=footer?.getBoundingClientRect().top;
    if(footerTop>0&&footerTop<innerHeight)viewportBottom=footerTop;
    const below=viewportBottom-rect.bottom-12, above=Math.min(rect.top,viewportBottom)-12;
    const bottomSide=below>=320||below>=above;
    const height=Math.min(360,Math.max(160,(bottomSide?below:above)-8));
    popup.style.width=width+'px';popup.style.maxHeight=height+'px';
    popup.style.left=Math.max(12,Math.min(rect.left,innerWidth-width-12))+'px';
    popup.style.top=(bottomSide?rect.bottom+6:Math.max(8,Math.min(rect.top,viewportBottom)-height-6))+'px';
    popup.style.height=height+'px';
  }
  function toggle() {
    if(popup.matches(':popover-open')){popup.hidePopover();return;}
    group=-1;category=-1;query='';warning='';draw();position();popup.showPopover();
    control.querySelector('[data-tag-open]').setAttribute('aria-expanded','true');
    popup.querySelector('input[type=search]').focus({preventScroll:true});
  }
  function leaf(tag,path='') {
    return `<label class="dc-tag-leaf"><input type="checkbox" data-tag-value="${esc(tag)}" ${selected.includes(tag)?'checked':''}><span>${esc(tag)}${path?`<small>${esc(path)}</small>`:''}</span></label>`;
  }
  function content() {
    if(query){
      const results=groups.flatMap(g=>g.categories.flatMap(c=>c.tags.map(tag=>({tag,path:g.name+' / '+c.name})))).filter(r=>(r.tag+' '+r.path).toLowerCase().includes(query.toLowerCase()));
      return `<div class="dc-tag-results">${results.length?results.map(r=>leaf(r.tag,r.path)).join(''):'<p class="dc-tag-empty">没有匹配的标签</p>'}</div>`;
    }
    // Match the old Quanta cascader: keep ancestors visible and append a column
    // only after its parent is activated. Opening never preselects a branch.
    let columns=`<div class="dc-tag-column" role="group" aria-label="标签体系">${groups.map((g,i)=>`<button type="button" class="dc-tag-branch${i===group?' active':''}" data-tag-group="${i}" aria-expanded="${i===group}"><span>${esc(g.name)}</span>${arrow}</button>`).join('')}</div>`;
    if(group>=0)columns+=`<div class="dc-tag-column" role="group" aria-label="标签类别">${groups[group].categories.map((c,i)=>`<div class="dc-tag-category-row${i===category?' active':''}"><input type="checkbox" data-tag-category-check="${i}" aria-label="选择全部${esc(c.name)}标签" ${c.tags.every(t=>selected.includes(t))?'checked':''}><button type="button" class="dc-tag-branch" data-tag-category="${i}" aria-expanded="${i===category}"><span>${esc(c.name)}</span>${arrow}</button></div>`).join('')}</div>`;
    if(category>=0)columns+=`<div class="dc-tag-column" role="group" aria-label="具体标签">${groups[group].categories[category].tags.map(t=>leaf(t)).join('')}</div>`;
    return `<div class="dc-tag-columns">${columns}</div>`;
  }
  function drawContent() {
    const scrolls=[...popup.querySelectorAll('.dc-tag-column,.dc-tag-results')].map(el=>el.scrollTop);
    popup.querySelector('.dc-tag-options').innerHTML=content();
    popup.querySelectorAll('.dc-tag-column,.dc-tag-results').forEach((el,i)=>{el.scrollTop=scrolls[i]||0;});
    popup.querySelectorAll('[data-tag-category-check]').forEach(input=>{
      const tags=groups[group].categories[Number(input.dataset.tagCategoryCheck)].tags;
      input.indeterminate=tags.some(t=>selected.includes(t))&&!tags.every(t=>selected.includes(t));
    });
    popup.querySelector('[role=status]').textContent=warning||`已选择 ${selected.length} / 8 个标签`;
    position();
  }
  function draw() {
    popup.innerHTML=`<div class="dc-tag-search"><input type="search" placeholder="搜索标签" aria-label="搜索标签" autocomplete="off"></div><div class="dc-tag-options"></div><footer class="dc-tag-picker-foot"><span role="status"></span><div><button type="button" data-tag-clear>清空</button><button type="button" data-tag-done>完成</button></div></footer>`;
    drawContent();
  }
  function commit() {
    warning='';change([...selected]);
    control.querySelector('.dc-tag-values').innerHTML=chips(selected);
    control.querySelector('[data-tag-open]>span').textContent=selected.length?'继续选择':'请选择标签';
    if(popup.matches(':popover-open'))drawContent();
  }
  function choose(tags,checked) {
    const next=checked?[...new Set([...selected,...tags])]:selected.filter(tag=>!tags.includes(tag));
    if(next.length>8){warning='最多选择 8 个标签，请先移除部分已选标签。';drawContent();return;}
    selected=next;commit();
  }
  popup.addEventListener('input',event=>{if(event.target.type==='search'){query=event.target.value.trim();warning='';drawContent();}});
  popup.addEventListener('click',event=>{
    const button=event.target.closest('button');if(!button)return;
    if(button.hasAttribute('data-tag-group')){group=Number(button.dataset.tagGroup);category=-1;drawContent();popup.querySelector(`[data-tag-group="${group}"]`)?.focus({preventScroll:true});}
    if(button.hasAttribute('data-tag-category')){category=Number(button.dataset.tagCategory);drawContent();popup.querySelector(`[data-tag-category="${category}"]`)?.focus({preventScroll:true});}
    if(button.hasAttribute('data-tag-clear')){selected=[];commit();}
    if(button.hasAttribute('data-tag-done')){popup.hidePopover();control.querySelector('[data-tag-open]').focus({preventScroll:true});}
  });
  popup.addEventListener('change',event=>{
    const input=event.target;
    if(input.hasAttribute('data-tag-value')){const value=input.dataset.tagValue;choose([value],input.checked);[...popup.querySelectorAll('[data-tag-value]')].find(el=>el.dataset.tagValue===value)?.focus({preventScroll:true});}
    if(input.hasAttribute('data-tag-category-check')){const index=Number(input.dataset.tagCategoryCheck);choose(groups[group].categories[index].tags,input.checked);popup.querySelector(`[data-tag-category-check="${index}"]`)?.focus({preventScroll:true});}
  });
  popup.addEventListener('toggle',()=>{control?.querySelector('[data-tag-open]')?.setAttribute('aria-expanded',String(popup.matches(':popover-open')));});
  popup.addEventListener('keydown',event=>{
    if(event.key==='Escape'){popup.hidePopover();control?.querySelector('[data-tag-open]').focus({preventScroll:true});return;}
    const button=event.target.closest('[data-tag-group],[data-tag-category]');
    if(event.key==='ArrowRight'&&button){event.preventDefault();button.click();popup.querySelector(button.hasAttribute('data-tag-group')?'[data-tag-category]':'[data-tag-value]')?.focus({preventScroll:true});}
    if(event.key==='ArrowLeft'){
      const column=event.target.closest('.dc-tag-column');
      const parent=column?.previousElementSibling?.querySelector('[aria-expanded="true"]');
      if(parent){event.preventDefault();parent.focus({preventScroll:true});}
    }
  });
  addEventListener('resize',()=>{if(popup.matches(':popover-open'))position();});
  addEventListener('scroll',()=>{if(popup.matches(':popover-open'))position();},true);
  window.CollectionTagPicker=Object.freeze({render,mount});
})();
