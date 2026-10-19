(() => {
  class DetailSection extends HTMLElement {
    connectedCallback(){
      if(this.dataset.ready)return;this.dataset.ready='true';
      const children=[...this.childNodes];
      const header=document.createElement('header');header.className='detail-section__header';
      const title=document.createElement('h3');title.textContent=this.getAttribute('heading')||'';header.append(title);
      const body=document.createElement('div');body.className='detail-section__body';
      children.forEach(node=>{if(node.nodeType===1&&node.hasAttribute('section-action'))header.append(node);else body.append(node);});
      this.append(header,body);
    }
  }
  class DetailFields extends HTMLElement {
    connectedCallback(){
      if(this.dataset.ready)return;this.dataset.ready='true';
      const list=document.createElement('dl');
      [...this.children].forEach(field=>{const row=document.createElement('div');const label=document.createElement('dt');label.textContent=field.getAttribute('label')||'';const value=document.createElement('dd');value.append(...field.childNodes);row.append(label,value);list.append(row);});
      this.replaceChildren(list);
      if(this.hasAttribute('heading')){
        const heading=document.createElement('h4');
        heading.className='detail-fields__heading';
        heading.textContent=this.getAttribute('heading');
        this.prepend(heading);
      }
    }
  }
  class MetricProgress extends HTMLElement {
    static get observedAttributes(){return ['value','total','label','unit'];}
    connectedCallback(){this.render();}
    attributeChangedCallback(){if(this.isConnected)this.render();}
    render(){
      const total=Math.max(0,Number(this.getAttribute('total'))||0),value=Math.min(total,Math.max(0,Number(this.getAttribute('value'))||0));
      const unit=this.getAttribute('unit')||'',label=this.getAttribute('label')||'进度';
      this.innerHTML='<div class="metric-progress__heading"><span></span><strong></strong></div><progress></progress><div class="metric-progress__caption"><span></span><span></span></div>';
      this.querySelector('.metric-progress__heading span').textContent=label;
      this.querySelector('strong').textContent=`${value.toFixed(1)} / ${total.toFixed(1)} ${unit}`;
      const bar=this.querySelector('progress');bar.max=total||1;bar.value=value;bar.setAttribute('aria-label',label);
      const captions=this.querySelectorAll('.metric-progress__caption span');captions[0].textContent=`已完成 ${total?Math.round(value/total*100):0}%`;captions[1].textContent=`距目标 ${(total-value).toFixed(1)} ${unit}`;
    }
  }
  customElements.define('detail-section',DetailSection);
  customElements.define('detail-fields',DetailFields);
  customElements.define('metric-progress',MetricProgress);
})();
