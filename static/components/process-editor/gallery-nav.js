(() => {
  const nodeInfo=document.querySelector('#process-node-info');
  if(new URLSearchParams(location.search).get('view')==='forms'&&nodeInfo){
    document.title='输入与表单';
    document.body.classList.add('forms-gallery-view');
    const main=document.querySelector('main');
    const header=document.createElement('header');header.className='component-gallery__header';
    header.innerHTML='<h1>输入与表单</h1>';
    main.replaceChildren(header,nodeInfo);
    nodeInfo.querySelector(':scope > h2')?.remove();
    return;
  }
  const workflowSection=[...document.querySelectorAll('main > .component-gallery__group')].find(section=>section.querySelector('h2')?.textContent.trim()==='京东sku');
  if(nodeInfo&&workflowSection)workflowSection.before(nodeInfo);
  const sections=[...document.querySelectorAll('main > .component-gallery__group')];
  const ids=['process-header','process-flow-tree','process-library','process-node-styles','process-standard-node-styles','process-canvas','process-properties','process-human-interrupt'];
  const sidebar=document.createElement('aside');sidebar.className='process-gallery-nav';
  sidebar.innerHTML='<h1>流程编辑器</h1><p>流程编辑器中使用的组件及状态</p><nav aria-label="组件分类"></nav>';
  const nav=sidebar.querySelector('nav');
  sections.forEach((section,index)=>{
    section.id=section.id||(section.querySelector('.form-control-samples')?'process-form-controls':ids[index]||`process-section-${index}`);
    const link=document.createElement('a');link.href=`#${section.id}`;
    link.textContent=section.querySelector('h2').textContent.replace(' · 节点库与拖入画布后','');nav.append(link);
  });
  document.body.prepend(sidebar);
  const links=[...nav.querySelectorAll('a')];
  const update=()=>{let active=0;sections.forEach((section,index)=>{if(section.getBoundingClientRect().top<=120)active=index;});links.forEach((link,index)=>{if(index===active)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});};
  window.addEventListener('scroll',update,{passive:true});
  window.addEventListener('hashchange',()=>{const section=sections.find(item=>`#${item.id}`===location.hash);section?.scrollIntoView();update();});
  requestAnimationFrame(()=>{sections.find(item=>`#${item.id}`===location.hash)?.scrollIntoView();update();});
})();
