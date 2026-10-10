(() => {
  const api=window.PostTrainingQualityReviewDemo;
  const selected=()=>api.state.segments.find(item=>item.id===api.state.selectedId);
  let dialog;
  function openEditor(){
    const item=selected();if(!item)return;
    if(!dialog){
      dialog=document.createElement('dialog');dialog.className='ptqr-dialog ptqr-note-dialog';
      dialog.innerHTML='<header><h2>补充说明（选填）</h2><button type="button" aria-label="关闭">×</button></header><div><textarea maxlength="500" aria-label="补充说明" placeholder="请补充具体问题或修改建议（最多500字）"></textarea><small></small></div><footer><button type="button">完成</button></footer>';
      document.body.append(dialog);
      dialog.querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>dialog.close()));
      dialog.addEventListener('close',()=>document.dispatchEvent(new CustomEvent('post-quality-review-state-change')));
      dialog.querySelector('textarea').addEventListener('input',event=>{
        const target=api.state.segments.find(item=>item.id===dialog.dataset.segmentId);
        if(target&&!api.state.submitted){target.reviewNote=event.target.value;api.state.dirty=true;}
        dialog.querySelector('small').textContent=`${event.target.value.length}/500`;
      });
    }
    dialog.dataset.segmentId=item.id;dialog.querySelector('textarea').value=item.reviewNote||'';
    dialog.querySelector('textarea').disabled=api.state.submitted;
    dialog.querySelector('small').textContent=`${(item.reviewNote||'').length}/500`;
    dialog.showModal();dialog.querySelector('textarea').focus();
  }
  function render(){
    const host=document.querySelector('post-training-quality-review-workspace'),row=host?.querySelector('.ptqr-error-row'),item=selected();
    if(!row||!item||row.querySelector('.ptqr-note-field'))return;
    const label=document.createElement('label');label.className='ptqr-note-field';
    label.innerHTML='<span>补充说明</span><input type="text" maxlength="500" placeholder="具体问题或修改建议（选填）" aria-label="补充说明"><button type="button">展开</button>';
    const input=label.querySelector('input');input.value=item.reviewNote||'';input.disabled=api.state.submitted;
    input.addEventListener('input',()=>{if(!api.state.submitted){item.reviewNote=input.value;api.state.dirty=true;}});
    label.querySelector('button').addEventListener('click',openEditor);
    row.append(label);
  }
  document.addEventListener('post-quality-review-state-change',render);
  render();
})();
