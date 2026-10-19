class StatCards extends HTMLElement {
  static get observedAttributes(){return ['gpu-price'];}
  attributeChangedCallback(){const value=this.querySelector('[data-remaining-hours]');if(value)value.textContent=(1590/(Number(this.getAttribute('gpu-price'))||5)).toFixed(1);}

  connectedCallback() {
    if (this.dataset.ready) return;
    this.dataset.ready = "true";
    if(this.getAttribute('variant')==='resources'){
      this.innerHTML='<div class="stat-cards stat-cards--resources" aria-label="资源统计"><section><div class="stat-cards-values"><div><span>余额（元）</span><strong>1,590.00</strong><small>可用金额</small></div><div><span>累计充值（元）</span><strong>5,000.00</strong><small>已到账金额</small></div><div><span>剩余卡时（卡时）</span><strong data-remaining-hours>318.0</strong><small>按所选 GPU 参考单价估算</small></div><div><span>已消耗卡时（卡时）</span><strong>585.5</strong><small>各 GPU 型号用量合计</small></div></div></section></div>';
      this.attributeChangedCallback();return;
    }
    if (this.getAttribute("variant") === "capacity") {
      const total = Number(this.getAttribute("total")) || 0;
      const consumed = Number(this.getAttribute("consumed")) || 0;
      this.innerHTML = `<div class="stat-cards stat-cards--capacity" aria-label="产能统计"><section><div class="stat-cards-values"><div class="stat-card--period"><span>当前周期</span><strong></strong></div><div class="stat-card--total"><span>总产能</span><strong>${total} 条</strong></div><div class="stat-card--consumed"><span>已消耗产能</span><strong>${consumed} 条</strong></div><div><span>剩余产能</span><strong>${total-consumed} 条</strong></div></div></section></div>`;
      const period = this.querySelector(".stat-card--period strong");
      period.textContent = this.getAttribute("period") || "—";
      period.title = period.textContent;
      return;
    }
    this.innerHTML = `<div class="stat-cards" aria-label="数据统计">
          <section><h2>数据维度</h2><div class="stat-cards-values"><div><span>处理中</span><strong>3,126</strong><small>已进入处理任务，但暂未有任意任务产出结果</small></div><div><span>已产出结果</span><strong>9,408</strong><small>只要任意一个处理任务有产出结果即可计入</small></div></div></section>
          <section><h2>数据处理任务维度</h2><div class="stat-cards-values"><div><span>待处理</span><strong>1,206</strong><small>尚未开始处理的处理任务</small></div><div><span>处理中</span><strong>488</strong><small>已开始但尚未完成的处理任务</small></div><div><span>已完成</span><strong>842</strong><small>已完成处理并产出结果的处理任务</small></div></div></section>
        </div>`;
    this.querySelectorAll("small").forEach(description => { description.title = description.textContent; });
  }
}
customElements.define("stat-cards", StatCards);
