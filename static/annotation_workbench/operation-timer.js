(() => {
  const MODES = {'pre-quality':'预训练质检','post-quality':'后训练质检',segments:'语义标注',action:'动作标注'};
  class OperationClock {
    constructor({now = Date.now, totals = {}, idleMs = 30000} = {}) {
      this.now = now;
      this.idleMs = idleMs;
      this.totals = Object.fromEntries(Object.keys(MODES).map(mode => [mode, Number.isFinite(totals[mode]) ? Math.max(0, totals[mode]) : 0]));
      this.mode = null;
      this.visible = true;
      this.checkpoint = this.lastActivity = now();
    }
    settle() {
      const now = this.now();
      if (this.visible && MODES[this.mode]) this.totals[this.mode] += Math.max(0, Math.min(now, this.lastActivity + this.idleMs) - this.checkpoint);
      this.checkpoint = now;
    }
    setMode(mode) { this.settle(); this.mode = mode; this.lastActivity = this.now(); }
    activity() { this.settle(); this.lastActivity = this.now(); }
    setVisible(visible) { this.settle(); this.visible = visible; this.lastActivity = this.now(); }
    get running() { return Boolean(this.visible && MODES[this.mode] && this.now() < this.lastActivity + this.idleMs); }
    elapsed(mode = this.mode) {
      const pending = this.visible && mode === this.mode && MODES[mode] ? Math.max(0, Math.min(this.now(), this.lastActivity + this.idleMs) - this.checkpoint) : 0;
      return (this.totals[mode] || 0) + pending;
    }
  }
  if (typeof module !== 'undefined' && module.exports) { module.exports = {OperationClock, MODES}; return; }
  const header = document.querySelector('workbench-task-header');
  const list = document.querySelector('workbench-segment-list');
  if (!header || !list) return;
  const key = `quanta.operation-time.v1.${header.dataset.id}`;
  let totals = {};
  try { totals = JSON.parse(localStorage.getItem(key) || '{}') || {}; } catch (_) {}
  const clock = new OperationClock({totals});
  clock.setMode(list.variant);
  clock.setVisible(document.visibilityState !== 'hidden');
  const panel = document.createElement('div');
  panel.className = 'workbench-operation-timer';
  panel.title = '连续 30 秒无操作自动暂停；再次操作继续计时。切换到后台不计时。';
  panel.setAttribute('aria-label', '操作计时');
  panel.innerHTML = '<span data-operation-status></span><strong data-operation-time></strong>';
  header.querySelector('.workbench-task-info').append(panel);
  header.querySelector('.workbench-task-info').classList.add('has-operation-timer');
  const render = () => {
    panel.hidden = !MODES[clock.mode];
    panel.dataset.mode = clock.mode;
    panel.dataset.running = String(clock.running);
    const seconds = Math.floor(clock.elapsed() / 1000);
    panel.querySelector('[data-operation-time]').textContent = [Math.floor(seconds / 3600), Math.floor(seconds / 60) % 60, seconds % 60].map(value => String(value).padStart(2, '0')).join(':');
    panel.querySelector('[data-operation-status]').textContent = clock.running ? '计时中' : '已暂停';
  };
  const save = () => { clock.settle(); try { localStorage.setItem(key, JSON.stringify(clock.totals)); } catch (_) {} };
  list.addEventListener('review-variant-change', event => { clock.setMode(event.detail.variant); save(); render(); });
  for (const type of ['pointerdown', 'pointermove', 'keydown', 'input', 'wheel']) document.addEventListener(type, () => { clock.activity(); render(); }, {capture:true, passive:true});
  document.addEventListener('visibilitychange', () => { clock.setVisible(document.visibilityState !== 'hidden'); save(); render(); });
  window.addEventListener('blur', () => { clock.setVisible(false); save(); render(); });
  window.addEventListener('focus', () => { clock.setVisible(document.visibilityState !== 'hidden'); render(); });
  window.addEventListener('pagehide', save);
  let ticks = 0;
  setInterval(() => { clock.settle(); render(); if (++ticks % 5 === 0) save(); }, 1000);
  render();
})();
