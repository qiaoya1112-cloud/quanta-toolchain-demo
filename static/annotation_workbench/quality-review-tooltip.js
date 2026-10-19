(() => {
  const selector = '.ptqr-list-summary strong, .ptqw-note-text, .ptqw-reason-value, .ptqs-change';
  let tip, active;
  const hide = () => {
    if (tip) tip.hidden = true;
    active?.removeAttribute('aria-describedby');
    active = null;
  };
  const position = event => {
    if (!tip || tip.hidden) return;
    tip.style.left = `${Math.max(10, Math.min(innerWidth - tip.offsetWidth - 10, event.clientX + 12))}px`;
    tip.style.top = `${Math.max(10, Math.min(innerHeight - tip.offsetHeight - 10, event.clientY + 14))}px`;
  };
  document.addEventListener('pointerover', event => {
    const target = event.target.closest(selector);
    if (!target) return;
    hide();
    target.removeAttribute('title');
    if (!tip) {
      tip = document.createElement('div');
      tip.id = 'ptqrDescriptionTooltip';
      tip.className = 'ptq-description-tooltip';
      tip.setAttribute('role', 'tooltip');
      document.body.append(tip);
    }
    const content = document.createElement('span');
    content.textContent = target.dataset.fullDescription || target.textContent;
    tip.replaceChildren(content);
    active = target;
    target.setAttribute('aria-describedby', tip.id);
    tip.hidden = false;
    position(event);
  });
  document.addEventListener('pointermove', position);
  document.addEventListener('pointerout', event => {
    if (active && active.contains(event.target) && !active.contains(event.relatedTarget)) hide();
  });
  document.addEventListener('click', hide);
  document.addEventListener('scroll', hide, true);
  window.addEventListener('blur', hide);
})();
