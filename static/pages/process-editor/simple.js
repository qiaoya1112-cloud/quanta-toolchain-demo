// Page-specific composition; the complex editor keeps its existing references.
document.querySelector('process-editor-header h1').textContent = '端到端切分标注简洁版';
const library = document.querySelector('process-node-library');
library.querySelector('.node-library-toggle').click();
const libraryToggle = library.querySelector('.node-library-toggle');
libraryToggle.style.display = 'none';
const sidebarButton = document.querySelector('.canvas-stage [data-action="add"]');
sidebarButton.innerHTML = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></svg>';
const syncSidebarButton = () => {
  const expanded = !library.querySelector('.left-panel').classList.contains('is-library-collapsed');
  sidebarButton.setAttribute('aria-expanded', String(expanded));
  sidebarButton.setAttribute('aria-label', expanded ? '收起节点栏' : '展开节点栏');
  sidebarButton.title = expanded ? '收起节点栏' : '展开节点栏';
};
sidebarButton.addEventListener('click', event => {
  // Edge insertion retains its anchored node picker.
  if (event.detail?.anchor) return;
  event.preventDefault();event.stopImmediatePropagation();
  libraryToggle.click();syncSidebarButton();
}, true);
syncSidebarButton();
const properties = document.querySelector('process-node-properties');
const panel = properties.querySelector('.right-panel');
panel.style.display = 'none';
// controller.js owns node selection and chooses the matching properties variant.
// Do not retain a second click handler tied to the initial human panel.

const draftId=new URLSearchParams(location.search).get('draft');
if(draftId){
  const draft=JSON.parse(localStorage.getItem('quanta-process-drafts')||'[]').find(item=>item.identifier===draftId);
  if(draft){
    document.querySelector('process-editor-header h1').textContent=draft.name;document.title=draft.name;
    const info=document.querySelector('process-editor-header .flow-info-form');
    info.querySelector('input[readonly]').value=draft.identifier;
    info.querySelector('select').replaceChildren(new Option(draft.stage,draft.stage));
    const canvas=document.querySelector('process-flow-canvas');
    const initial=document.createElement('process-flow-canvas');initial.setAttribute('variant','initial');canvas.replaceWith(initial);
    document.querySelector('.process-editor-components').dataset.flowDescription=draft.description;
  }
}
