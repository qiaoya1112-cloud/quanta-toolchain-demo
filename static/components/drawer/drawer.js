class AppDrawer extends HTMLElement {
  connectedCallback(){
    if(this.dialog)return;
    const content=[...this.childNodes];
    this.dialog=document.createElement('dialog');this.dialog.className='app-drawer';
    this.dialog.setAttribute('aria-label',this.getAttribute('heading')||'详情');
    this.dialog.innerHTML='<header class="app-drawer__header"><h2></h2><text-button variant="text" icon="close" icon-only aria-label="关闭抽屉"></text-button></header><div class="app-drawer__body"></div><footer class="app-drawer__footer"></footer>';
    this.dialog.querySelector('h2').textContent=this.getAttribute('heading')||'详情';
    content.forEach(node=>this.dialog.querySelector(node.nodeType===1&&node.hasAttribute('drawer-footer')?'.app-drawer__footer':'.app-drawer__body').append(node));
    this.append(this.dialog);
    this.dialog.querySelector('header text-button').addEventListener('click',()=>this.close());
    this.dialog.addEventListener('click',e=>{if(e.target===this.dialog&&e.clientX<this.dialog.getBoundingClientRect().left)this.close();});
    this.dialog.addEventListener('close',()=>{this.opener?.focus();this.dispatchEvent(new CustomEvent('drawer-close'));});
  }
  show(){this.opener=document.activeElement;this.dialog.showModal();this.dialog.querySelector('input:not([disabled]),textarea')?.focus();}
  close(){this.dialog.close();}
}
customElements.define('app-drawer',AppDrawer);
