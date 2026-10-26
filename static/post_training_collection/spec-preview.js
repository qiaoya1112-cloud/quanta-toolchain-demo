/* Specification content stays in Feishu; Quanta stores and opens the link only. */
(() => {
  'use strict';
  const url = 'https://nwd4iy9rd2s.feishu.cn/wiki/R1yZwxGaFiTs34koqYDcoKPmnk2';
  const escape = value => String(value || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeUrl = value => { try { const parsed = new URL(value.trim()); return ['https:', 'http:'].includes(parsed.protocol) && parsed.hostname ? parsed.href : ''; } catch (_) { return ''; } };
  function button(value) {
    const href = safeUrl(value);
    return href ? `<a class="dc-btn" data-spec-action="open" href="${escape(href)}" target="_blank" rel="noopener noreferrer">打开规范 ↗</a>` : '<button type="button" class="dc-btn" data-spec-action="open" disabled>打开规范 ↗</button>';
  }
  function card(value) {
    const href = safeUrl(value);
    return href ? `<div class="dc-spec-external">${button(href)}<span class="dc-spec-url">${escape(value)}</span></div>` : '';
  }
  window.CollectionSpecLink = Object.freeze({url, button, card});
})();
