(() => {
  class ResourceList extends HTMLElement {
    connectedCallback(){if(this.ready)return;this.ready=true;this.addEventListener('click',event=>{const button=event.target.closest('[data-resource-id]');if(!button)return;this.selected=button.dataset.resourceId;this.render();this.dispatchEvent(new CustomEvent('resource-select',{bubbles:true,detail:{value:this.selected}}));});this.render();}
    set items(value){this._items=value;this.render();}
    get items(){return this._items||[];}
    render(){const fragment=document.createDocumentFragment();
      const row=item=>{const button=document.createElement('button');button.type='button';button.className='resource-list__item';button.dataset.resourceId=item.id;button.setAttribute('aria-pressed',String(String(item.id)===String(this.selected)));const title=document.createElement('strong');title.textContent=item.label;const meta=document.createElement('span');meta.textContent=item.meta||'';if(item.trailing||item.status){const heading=document.createElement('div');heading.className='resource-list__heading';const trailing=document.createElement('span');trailing.className='resource-list__trailing';trailing.textContent=item.trailing;heading.append(title);if(item.status){const tag=document.createElement('span');tag.className='resource-list__status table-outline-tag '+(item.status==='pass'?'table-outline-tag--success':'table-outline-tag--danger');tag.textContent=item.status==='pass'?'校验通过':'校验失败';heading.append(tag);}if(item.trailing)heading.append(trailing);button.append(heading,meta);}else button.append(title,meta);if(item.description){const description=document.createElement('span');description.className='resource-list__description';description.textContent=item.description;button.append(description);}return button;};
      this.items.forEach(item=>{if(item.children){const group=document.createElement('details');group.open=true;const summary=document.createElement('summary');summary.textContent=`${item.label} (${item.children.length})`;group.append(summary,...item.children.map(row));fragment.append(group);}else fragment.append(row(item));});
      if(!this.items.length){const empty=document.createElement('p');empty.className='resource-list__empty';empty.textContent='暂无匹配项';fragment.append(empty);}this.replaceChildren(fragment);
    }
  }
  customElements.define('resource-list',ResourceList);
})();
