(() => {
  class ConfirmDialog extends HTMLElement {
    connectedCallback(){
      if(this.dialog)return;
      this.innerHTML='<dialog class="confirm-dialog"><h2></h2><p></p><footer><text-button variant="outline" data-cancel>取消</text-button><text-button variant="primary" data-confirm></text-button></footer></dialog>';
      this.dialog=this.querySelector('dialog');
      this.querySelector('h2').textContent=this.getAttribute('heading')||'确认操作';
      this.querySelector('p').textContent=this.getAttribute('message')||'';
      this.querySelector('[data-confirm] button').textContent=this.getAttribute('confirm-label')||'确认';
      this.querySelector('[data-cancel]').onclick=()=>this.dialog.close();
      this.querySelector('[data-confirm]').onclick=()=>{this.dialog.close();this.dispatchEvent(new CustomEvent('confirm'));};
      this.dialog.setAttribute('aria-label',this.querySelector('h2').textContent);
    }
    show(){this.dialog.showModal();}
  }
  customElements.define('confirm-dialog',ConfirmDialog);
})();
