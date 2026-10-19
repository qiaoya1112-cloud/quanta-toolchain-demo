class ListPagination extends HTMLElement {
  static get observedAttributes(){return ['total','page','page-size','total-only'];}
  connectedCallback(){this.render();}
  attributeChangedCallback(){if(this.isConnected)this.render();}
  get pageSize(){return Math.max(1,Number(this.getAttribute('page-size'))||10);}
  get pageCount(){return Math.max(1,Math.ceil((Number(this.getAttribute('total'))||0)/this.pageSize));}
  get page(){return Math.max(1,Math.min(this.pageCount,Number(this.getAttribute('page'))||1));}
  change(page,size=this.pageSize){
    if(!Number.isInteger(page)||page<1||page>Math.max(1,Math.ceil((Number(this.getAttribute('total'))||0)/size)))return;
    this.setAttribute('page-size',size);this.setAttribute('page',page);
    this.dispatchEvent(new CustomEvent('page-change',{bubbles:true,detail:{page:this.page,pageSize:this.pageSize}}));
  }
  render(){
    const current=this.page,count=this.pageCount,pages=new Set([1,count]);
    const start=Math.max(1,Math.min(current-2,count-4));
    for(let i=start;i<=Math.min(count,start+4);i++)pages.add(i);
    const sorted=[...pages].sort((a,b)=>a-b);
    const total=Math.max(0,Number(this.getAttribute('total'))||0);
    this.innerHTML=`<nav class="list-pagination" aria-label="分页"><span class="list-pagination__total">共 <strong>${total.toLocaleString('zh-CN')}</strong> 条</span><div class="list-pagination__controls"><label class="list-pagination__size"><select aria-label="每页条数">${[...new Set([10,15,20,50,this.pageSize])].sort((a,b)=>a-b).map(n=>`<option value="${n}" ${n===this.pageSize?'selected':''}>${n}条/页</option>`).join('')}</select><svg class="list-pagination__icon" viewBox="0 0 16 16" fill="none" aria-hidden="true" focusable="false"><path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></label><button type="button" data-prev aria-label="上一页" ${current===1?'disabled':''}><svg class="list-pagination__icon" viewBox="0 0 16 16" fill="none" aria-hidden="true" focusable="false"><path d="M10 4l-4 4 4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button>${sorted.map((n,i)=>`${i&&n-sorted[i-1]>1?'<span aria-hidden="true">…</span>':''}<button type="button" data-page="${n}" ${n===current?'aria-current="page"':''}>${n}</button>`).join('')}<button type="button" data-next aria-label="下一页" ${current===count?'disabled':''}><svg class="list-pagination__icon" viewBox="0 0 16 16" fill="none" aria-hidden="true" focusable="false"><path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button><span class="list-pagination__count">共 ${count} 页</span><label class="list-pagination__jump">跳至 <input type="number" min="1" max="${count}" value="${current}" aria-label="跳转页码"> 页</label></div></nav>`;
    if(this.hasAttribute('total-only')){this.querySelector('.list-pagination__controls').remove();this.querySelector('nav').setAttribute('aria-label','数据总数');return;}
    const jump=this.querySelector('input');
    const commitJump=()=>{const value=Number(jump.value);if(Number.isInteger(value)&&value>=1&&value<=count)this.change(value);else jump.value=String(current);};
    jump.onchange=commitJump;
    jump.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();commitJump();}};
    this.querySelector('select').onchange=e=>this.change(1,Number(e.target.value));
    this.querySelector('nav').onclick=e=>{const b=e.target.closest('button');if(!b||b.disabled)return;if(b.dataset.page)this.change(Number(b.dataset.page));else if(b.hasAttribute('data-next'))this.change(current+1);else if(b.hasAttribute('data-prev'))this.change(current-1);};
  }
}
customElements.define('list-pagination',ListPagination);
