(() => {
  const sidebar = document.querySelector('platform-sidebar');
  const buttons = [...sidebar.querySelectorAll('.platform-sidebar__item')];
  const main = document.querySelector('.process-page__main');
  const header = main.querySelector('task-page-header');
  const content = main.querySelector('.process-page__content');
  const select = (title) => {
    const filterPages={'资源库':'resource-library','分配管理':'assignment-management','数据管理':'data-management','算子管理':'operator-management','规则管理':'rule-management','工作台管理':'workbench-management','项目管理':'project-management','用户组管理':'user-group-management','供应商管理':'supplier-management','权限管理':'permission-management'};
    if(filterPages[title]){
      window.location.assign(new URL(`../${filterPages[title]}/index.html`,window.location.href).href);
      return;
    }
    if (title === '任务处理') {
      window.location.assign(new URL('../task-processing/index.html', window.location.href).href);
      return;
    }
    if (title === '标注工作台') {
      window.location.assign(new URL('../action-quality-check/index.html', window.location.href).href);
      return;
    }
    const selected = buttons.find(button => button.title === title) || buttons.find(button => button.title === '流程管理');
    buttons.forEach(button => {
      const active = button === selected;
      button.classList.toggle('platform-sidebar__item--active', active);
      if (active) button.setAttribute('aria-current', 'page');
      else button.removeAttribute('aria-current');
    });
    document.title = selected.title;
    header.setAttribute('title', selected.title);
    header.querySelector('h1').textContent = selected.title;
    main.setAttribute('aria-label', `${selected.title}内容区`);
    content.setAttribute('aria-label', selected.title);
    const isProcess = selected.title === '流程管理';
    [...content.children].forEach(child => { child.hidden = !isProcess; });
    const actions = header.querySelector('.task-page-header__actions');
    if (actions) actions.hidden = !isProcess;
  };
  const readHash = () => {
    let title = '';
    try { title = decodeURIComponent(location.hash.slice(1)); } catch {}
    select(title);
  };
  buttons.forEach(button => button.addEventListener('click', () => {
    if (button.title === '标注工作台') {
      select(button.title);
      return;
    }
    select(button.title);
    location.hash = encodeURIComponent(button.title);
  }));
  window.addEventListener('hashchange', readHash);
  readHash();
})();

(() => {
  const drawer=document.querySelector('#create-process'),form=document.querySelector('#create-process-form');
  const name=form.querySelector('[name="name"] input'),identifier=form.querySelector('[name="identifier"] input');
  name.required=true;name.maxLength=100;identifier.required=true;identifier.pattern='[A-Za-z][A-Za-z0-9_-]*';identifier.title='以英文字母开头，仅包含英文字母、数字、连字符或下划线';identifier.maxLength=100;
  document.querySelector('task-page-header').addEventListener('header-action',()=>drawer.show());
  drawer.querySelector('[data-create-cancel]').addEventListener('click',()=>drawer.close());
  drawer.querySelector('[data-create-submit]').addEventListener('click',()=>form.requestSubmit());
  form.addEventListener('input',()=>{name.setCustomValidity('');identifier.setCustomValidity('');form.querySelector('[role="alert"]').textContent='';});
  form.addEventListener('submit',event=>{
    event.preventDefault();name.value=name.value.trim();identifier.value=identifier.value.trim();
    if(!name.value){name.setCustomValidity('请输入流程名称');name.reportValidity();return;}
    if(!form.reportValidity())return;
    try{
      const drafts=JSON.parse(localStorage.getItem('quanta-process-drafts')||'[]');
      const existing=[...document.querySelectorAll('task-data-table tbody td:first-child')].map(cell=>cell.textContent.trim());
      if(drafts.some(d=>d.identifier===identifier.value)||existing.includes(identifier.value)){identifier.setCustomValidity('流程标识已存在，请使用其他标识');identifier.reportValidity();return;}
      const draft={name:name.value,identifier:identifier.value,stage:form.querySelector('[name="stage"]').value,description:form.querySelector('[name="description"]').value.trim()};
      localStorage.setItem('quanta-process-drafts',JSON.stringify([...drafts,draft]));
      location.assign('../process-editor/simple.html?draft='+encodeURIComponent(draft.identifier));
    }catch{form.querySelector('[role="alert"]').textContent='无法保存草稿，请检查浏览器存储设置后重试。';}
  });
})();
