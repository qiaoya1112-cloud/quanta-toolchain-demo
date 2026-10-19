class SearchInput extends HTMLElement {
  connectedCallback() {
    if (this.querySelector('input')) return;
    this.innerHTML = '<label class="search-input"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg><input type="search"></label>';
    const input = this.querySelector('input');
    input.placeholder = this.getAttribute('placeholder') || '搜索';
    input.setAttribute('aria-label', this.getAttribute('aria-label') || input.placeholder);
    input.value = this.getAttribute('value') || '';
    input.addEventListener('input', () => this.dispatchEvent(new CustomEvent('search-change', {bubbles:true, detail:{value:input.value}})));
  }
  get value() { return this.querySelector('input')?.value || ''; }
  set value(value) { if(this.querySelector('input')) this.querySelector('input').value=value; }
}
customElements.define('search-input', SearchInput);
