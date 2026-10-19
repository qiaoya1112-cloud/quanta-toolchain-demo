class TaskPageHeader extends HTMLElement {
  static get observedAttributes() { return ['status', 'status-tone', 'back-label']; }
  attributeChangedCallback() {
    const status = this.querySelector('.task-page-header__status');
    if (status) {
      status.textContent = this.getAttribute('status') || '';
      status.hidden = !status.textContent;
      const tone = this.getAttribute('status-tone') === 'paused' ? 'paused' : 'running';
      status.className = `task-page-header__status table-outline-tag table-outline-tag--${tone}`;
    }
    const back = this.querySelector('.task-page-header__back');
    if (back) {
      const label = this.getAttribute('back-label') || '返回';
      back.title = label;
      back.setAttribute('aria-label', label);
      back.querySelector('button')?.setAttribute('aria-label', label);
    }
  }
  connectedCallback() {
    if (this.dataset.ready) return;
    this.dataset.ready = "true";
    const title = this.getAttribute("title") || "采集任务列表";
    const action = this.getAttribute("action");
    this.innerHTML = `<header class="task-page-header"><h1>${title}</h1>${action ? `<text-button class="task-page-header__action" variant="primary" ${action==='新增流程'?'icon="plus"':''}>${action}</text-button>` : ""}</header>`;
    if(this.hasAttribute('scene-filter')){
      const heading=this.querySelector('header');
      heading.classList.add('task-page-header--with-filter');
      const selected=this.getAttribute('scene')||'';
      const filter=document.createElement('form-select');
      filter.className='task-page-header__filter';
      filter.setAttribute('name','scene');filter.setAttribute('label','业务环节');
      filter.innerHTML=[['','全部业务环节'],['质检','质检环节'],['标注','标注环节'],['验收','验收环节']].map(([value,label])=>`<option value="${value}" ${selected===value?'selected':''}>${label}</option>`).join('');
      this.querySelector('h1').after(filter);
      filter.addEventListener('change',()=>this.dispatchEvent(new CustomEvent('scene-change',{bubbles:true,detail:{value:filter.querySelector('select').value}})));
    }
    const subtitle = this.getAttribute('subtitle');
    const description = this.getAttribute('description');
    if (subtitle || description) {
      const header = this.querySelector('header');
      header.classList.add('task-page-header--with-description');
      const content = document.createElement('div');
      content.className = 'task-page-header__content';
      const row = document.createElement('div');
      row.className = 'task-page-header__title-row';
      header.prepend(content);
      row.append(this.querySelector('h1'));
      if (subtitle) {
        const secondary = document.createElement('span');
        secondary.className = 'task-page-header__subtitle';
        secondary.textContent = subtitle;
        row.append(secondary);
      }
      const filter = header.querySelector('.task-page-header__filter');
      if (filter) row.append(filter);
      content.append(row);
      if (description) {
        const hint = document.createElement('p');
        hint.className = 'task-page-header__description';
        hint.textContent = description;
        content.append(hint);
      }
    }
    if (this.hasAttribute('back')) {
      const back = document.createElement('text-button');
      back.className = 'task-page-header__back';
      back.setAttribute('variant', 'text');
      back.setAttribute('icon', 'chevron-left');
      back.setAttribute('icon-only', '');
      back.setAttribute('aria-label', this.getAttribute('back-label') || '返回');
      back.addEventListener('click', () => this.dispatchEvent(new CustomEvent('header-back', { bubbles: true })));
      this.querySelector('header').prepend(back);
      this.querySelector('header').classList.add('task-page-header--with-back');
    }
    if (this.hasAttribute('status')) {
      const status = document.createElement('span');
      status.className = 'task-page-header__status';
      this.querySelector('h1').after(status);
      this.querySelector('header').classList.add('task-page-header--with-status');
    }
    this.attributeChangedCallback();
    this.querySelector(".task-page-header__action")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("header-action", { bubbles: true }));
    });
    if (this.hasAttribute('yaml-upload')) {
      const actions=document.createElement('div');actions.className='task-page-header__actions';
      this.querySelector('.task-page-header__action')?.remove();
      const primary=document.createElement('text-button');primary.setAttribute('variant','primary');primary.setAttribute('icon','plus');primary.textContent=action;
      primary.addEventListener('click',()=>this.dispatchEvent(new CustomEvent('header-action',{bubbles:true})));
      const upload=document.createElement('text-button');upload.setAttribute('variant','outline');upload.setAttribute('icon','upload');upload.textContent='上传已有 YAML';
      const input=document.createElement('input');input.type='file';input.accept='.yaml,.yml';input.hidden=true;
      upload.addEventListener('click',()=>input.click());
      input.addEventListener('change',()=>{const file=input.files[0];if(file)this.dispatchEvent(new CustomEvent('yaml-upload',{bubbles:true,detail:{file}}));input.value='';});
      actions.append(upload);if(primary)actions.append(primary);actions.append(input);
      this.querySelector('header').append(actions);
    }
  }
}
customElements.define("task-page-header", TaskPageHeader);
