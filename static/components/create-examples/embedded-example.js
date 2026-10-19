// Embedded examples own their layout so file previews also work without iframe DOM access.
if (new URLSearchParams(location.search).get('embed') === 'create-example') {
  const style = document.createElement('style');
  style.textContent = `
    .task-create-sidebar,.process-page__sidebar,.page-sidebar{display:none!important}
    .task-create-shell>task-creator,.process-page__main,.page-workspace{border-radius:0!important;width:100%!important;max-width:none!important}
    .process-page,.page-shell{grid-template-columns:minmax(0,1fr)!important}
  `;
  document.head.append(style);
  document.addEventListener('DOMContentLoaded', async () => {
    const drawer = document.querySelector('#create-process');
    if (drawer) {
      await customElements.whenDefined('app-drawer');
      drawer.show();
    }
  });
}
