(() => {
  const host=document.querySelector('[data-model-content]');
  const heading=document.querySelector('[data-model-title]').closest('header');
  function render(){
    const datasets=location.hash==='#model-datasets';
    heading.querySelector('[data-model-actions]')?.remove();
    const dialog=document.querySelector('#model-dialog');if(dialog?.open)dialog.close();
    heading.hidden=datasets;
    if(datasets&&!host.querySelector('dataset-browser'))host.replaceChildren(document.createElement('dataset-browser'));
    else if(!datasets){const id=location.hash.slice(1)||'model-data-query';if(!window.renderAdminPage(host,id)&&!window.renderEvaluationPage(host,id))window.renderModelPage(host,id);}
  }
  window.addEventListener('hashchange',render);render();
})();
