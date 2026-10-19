(() => {
  // Button components share this entry point; process-actions is the workflow button group.
  const assets = new URL('../../pages/process-editor/assets/', document.currentScript.src);
  class ProcessActions extends HTMLElement {
    connectedCallback() {
      if (this.querySelector('.process-actions')) return;
      const actions = [['parameters','全局参数','parameters-icon.svg'],['download','下载 YAML','download-icon.svg'],['history','历史版本','history-icon.svg'],['save','保存','save-icon.svg'],['publish','发布','publish-icon.svg']];
      this.innerHTML = `<div class="process-actions" role="group" aria-label="流程操作">${actions.map(([action,label,icon]) => `<button type="button" class="process-actions__button${action==='publish'?' process-actions__button--primary':''}" data-process-action="${action}" aria-label="${label}" title="${label}"><img src="${new URL(icon,assets)}" alt="">${label}</button>`).join('')}</div>`;
      const inlineIcons={publish:'<path d="m22 2-7 20-4-9-9-4 20-7ZM22 2 11 13"/>',history:'<rect x="7" y="3" width="14" height="16" rx="2"/><path d="M3 7v12a2 2 0 0 0 2 2h12M11 7h6M11 11h6M11 15h4"/>'};
      Object.entries(inlineIcons).forEach(([action,paths])=>{
        const img=this.querySelector(`[data-process-action="${action}"] img`);
        img.outerHTML=`<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
      });
      this.querySelectorAll('button').forEach(button => button.addEventListener('click', () => {
        this.dispatchEvent(new CustomEvent('process-action', {bubbles:true, detail:{action:button.dataset.processAction}}));
      }));
    }
  }
  if (!customElements.get('process-actions')) customElements.define('process-actions', ProcessActions);
  class TextButton extends HTMLElement {
    static get observedAttributes() { return ['variant', 'disabled', 'icon']; }
    connectedCallback() {
      if (this.button) return;
      const label = this.textContent.trim() || '按钮';
      const deleteOnly=label==='×'&&!/关闭|取消/.test(this.getAttribute('aria-label')||'')&&!this.hasAttribute('data-close')&&!this.hasAttribute('data-dismiss');
      if(deleteOnly){this.setAttribute('icon','delete');if(!this.hasAttribute('aria-label'))this.setAttribute('aria-label','删除');}
      this.button = document.createElement('button');
      this.button.type = 'button';
      this.button.textContent = deleteOnly||this.hasAttribute('icon-only')?'':label;
      if(this.hasAttribute('aria-label'))this.button.setAttribute('aria-label',this.getAttribute('aria-label'));
      this.replaceChildren(this.button);
      this.attributeChangedCallback();
    }
    attributeChangedCallback() {
      if (!this.button) return;
      const variant = ['primary', 'secondary', 'outline', 'text', 'danger'].includes(this.getAttribute('variant')) ? this.getAttribute('variant') : 'outline';
      this.button.className = `text-button text-button--${variant}`;
      this.button.disabled = this.hasAttribute('disabled');
      this.button.querySelector('svg')?.remove();
      const icons = {
        'chevron-left': '<path d="m15 5-7 7 7 7"/>',
        upload: '<path d="M12 16V3m-6 6 6-6 6 6M4 20h16"/>',
        save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h12l4 4v12a2 2 0 0 1-2 2Z"/><path d="M7 3v6h10V3M7 21v-8h10v8"/>',
        play: '<path d="m9 6 9 6-9 6V6Z" fill="currentColor" stroke="none"/>',
        pause: '<rect x="7" y="6" width="3" height="12" rx="1" fill="currentColor" stroke="none"/><rect x="14" y="6" width="3" height="12" rx="1" fill="currentColor" stroke="none"/>',
        reset: '<path d="M3.5 12a8.5 8.5 0 1 0 3-6.5"/><path d="M3.5 4v5h5"/>',
        plus: '<path d="M12 5v14M5 12h14"/>',
        close: '<path d="m6 6 12 12M18 6 6 18"/>',
        eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
        delete: '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/>'
      };
      const icon = icons[this.getAttribute('icon')];
      if (icon) this.button.insertAdjacentHTML('afterbegin', `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${icon}</svg>`);
    }
  }
  if (!customElements.get('text-button')) customElements.define('text-button', TextButton);
})();
