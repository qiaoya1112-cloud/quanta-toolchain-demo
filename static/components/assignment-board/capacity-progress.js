(() => {
  class CapacityProgress extends HTMLElement {
    connectedCallback(){
      const total=Math.max(0,Number(this.getAttribute('total'))||0);
      const current=Math.min(total,Math.max(0,Number(this.getAttribute('current'))||0));
      const other=Math.min(total-current,Math.max(0,Number(this.getAttribute('other'))||0));
      const done=current+other,percent=total?Math.round(done/total*100):0;
      this.innerHTML=`<div class="assignment-progress" role="progressbar" aria-label="节点整体进度" aria-valuemin="0" aria-valuemax="${total}" aria-valuenow="${done}"><i style="width:${total?current/total*100:0}%"></i><i style="width:${total?other/total*100:0}%"></i><span class="assignment-progress-value"><span>${done} / ${total}</span><span>${percent}%</span></span></div><div class="assignment-legend"><span>当前处理人 ${current}</span><span>其他处理人 ${other}</span><span>未完成 ${total-done}</span></div>`;
    }
  }
  customElements.define('capacity-progress',CapacityProgress);
})();
