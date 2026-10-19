// Place all form-control groups in the same spacing and heading layout.
const formShowcase=document.querySelector('workbench-form-control-states .workbench-control-showcase');
if(formShowcase)document.querySelectorAll('.quality-control-preview').forEach(preview=>{
  const group=preview.parentElement;
  group.className='workbench-control-showcase__group';
 formShowcase.append(group);
});
/* Preview mounts the production controller; no duplicate editor markup or handlers. */
document.querySelectorAll('[data-quality-editor-preview]').forEach(host=>{
  const mode=host.dataset.qualityEditorPreview;
  const editor=document.createElement('workbench-segment-editor');
  editor.setAttribute('hydrate','');editor.className='quality-review-editor';
  if(mode==='secondary-review')editor.setAttribute('data-overflow-demo','');
  const support=document.createElement('div');support.hidden=true;
  support.innerHTML='<workbench-quality-track duration="40"></workbench-quality-track><workbench-annotation-list variant="pretraining"></workbench-annotation-list><div class="preview-actions"><workbench-quality-conclusion></workbench-quality-conclusion><workbench-footer-actions variant="quality"></workbench-footer-actions></div>';
  host.append(editor,support);
  const header=document.createElement('div');header.setAttribute('data-processing-id','component-preview');header.setAttribute('data-id','shared-demo');
  const list=support.querySelector('workbench-annotation-list');
  if(['pretraining','posttraining'].includes(mode)){editor.setAttribute('data-no-error-reason','');list.setAttribute('data-no-error-reason','');}
  const controller=createQualityReview({editor,track:support.querySelector('workbench-quality-track'),list,actions:support.querySelector('.preview-actions'),header,storageNamespace:mode==='pretraining'?'workbench-quality-v1':`workbench-${mode}-v1`});
  controller.select(mode==='pretraining'?0:1);
  if(host.dataset.qualityControl==='feedback'){
    editor.querySelector('[data-remove-group="mistakes"]')?.click();
    const option=editor.querySelector('[data-reason-group="failures"][value="1"]');
    if(option){option.checked=true;option.dispatchEvent(new Event('change',{bubbles:true}));}
    editor.querySelectorAll('details[open]').forEach(details=>details.open=false);
  }
});

if(formShowcase){
 const group=document.createElement('section');group.className='workbench-control-showcase__group';
 group.innerHTML='<h3>Tag 标签</h3><div class="quality-tag-examples"></div>';
 const examples=group.querySelector('.quality-tag-examples');
 [['default','正确项','设备穿戴不规范'],['blue','遗漏项','采集时长不足'],['purple','错误项','手部脱离夹爪'],['orange','失误','夹爪超出画面'],['red','不合格','关键操作过程缺失']].forEach(([tone,label,text])=>{
  const cell=document.createElement('div');cell.className='workbench-control-state';cell.innerHTML=`<span>${label}</span>${QualityFormControls.tag(text,{tone,action:tone==='yellow'?'':tone==='purple'?'restore':'remove'})}`;examples.append(cell);
 });
 const clear=document.createElement('div');clear.className='workbench-control-state';clear.innerHTML='<span>全部删除</span>'+QualityFormControls.clearAll();examples.append(clear);
 formShowcase.append(group);
}

if(formShowcase){
 const group=document.createElement('section');
 group.className='workbench-control-showcase__group';
 group.innerHTML='<h3>悬浮提示</h3><span class="quality-audit-legend quality-hover-example" tabindex="0">'+QualityFormControls.legend()+'</span>';
 formShowcase.append(group);
}

if(formShowcase){
 const group=document.createElement('section');group.className='workbench-control-showcase__group';
 group.innerHTML='<h3>片段导航按钮</h3><workbench-segment-editor hydrate class="quality-navigation-preview"><div class="segment-actions" aria-label="片段导航按钮示例">'+QualityFormControls.navigation()+'</div></workbench-segment-editor>';
 formShowcase.append(group);
}

// Keep the live controls and their handlers while arranging examples by state.
if(formShowcase){
 const table=document.createElement('table');table.className='workbench-control-table';
 table.innerHTML='<colgroup><col class="workbench-control-table__name"><col><col></colgroup><thead><tr><th scope="col">控件</th><th scope="col">默认</th><th scope="col">禁用</th></tr></thead><tbody></tbody>';
 const body=table.tBodies[0];
 const addRow=(name)=>{const row=body.insertRow();row.className='workbench-control-showcase__group';const heading=document.createElement('th');heading.scope='row';heading.textContent=name;row.append(heading);return row;};
 const moveState=(cell,state)=>{if(!state){cell.textContent='—';cell.className='workbench-control-table__empty';return;}const label=state.querySelector(':scope > span');if(label)label.hidden=true;cell.append(state);};
 const reasonPreview=formShowcase.querySelector('[data-quality-control="reasons"]');
 const feedbackPreview=formShowcase.querySelector('[data-quality-control="feedback"]');
 if(reasonPreview&&feedbackPreview){
  const reasonGroup=reasonPreview.parentElement,feedbackGroup=feedbackPreview.parentElement;
  reasonGroup.querySelector('h3').textContent='原因与审核反馈多选';
  const examples=document.createElement('div');examples.className='quality-multiselect-examples';
  [['质检原因',reasonPreview],['审核反馈',feedbackPreview]].forEach(([label,preview])=>{
   const example=document.createElement('div');example.className='quality-multiselect-example';
   const caption=document.createElement('span');caption.className='quality-multiselect-example__label';caption.textContent=label;
   example.append(caption,preview);examples.append(example);
  });
  reasonGroup.append(examples);feedbackGroup.remove();
 }
 const groups=Array.from(formShowcase.children);
 groups.forEach(group=>{
  if(group.classList.contains('workbench-tag-state-pair')){
   const states=group.querySelectorAll('.workbench-control-state');const row=addRow('带 Tag 多选');
   moveState(row.insertCell(),states[0]);moveState(row.insertCell(),states[1]);
   return;
  }
  const heading=group.querySelector(':scope > h3');if(!heading)return;
  const row=addRow(heading.textContent);
  const states=group.querySelector(':scope > .workbench-control-showcase__states');
  if(states){[states.children[0],states.children[2]].forEach(state=>moveState(row.insertCell(),state));}
  else{const cell=row.insertCell();cell.colSpan=2;Array.from(group.childNodes).filter(node=>node!==heading).forEach(node=>cell.append(node));}
 });
 formShowcase.replaceChildren(table);
}

// List variants use the same custom elements, controller and mode rules as the workbench.
document.querySelectorAll('[data-quality-list-preview],[data-quality-footer-preview]').forEach(host=>{
 const mode=host.dataset.qualityListPreview||host.dataset.qualityFooterPreview;
 const panel=document.createElement('workbench-segment-list');panel.dataset.rendered='true';
 panel.className=host.hasAttribute('data-quality-footer-preview')?'quality-footer-preview':'quality-list-preview';
 panel.innerHTML='<aside class="workbench-review"><div class="workbench-review__main"><workbench-annotation-list variant="pretraining"></workbench-annotation-list><div class="workbench-quality-actions"><workbench-quality-conclusion></workbench-quality-conclusion><workbench-footer-actions variant="quality"></workbench-footer-actions></div></div></aside>';
 const support=document.createElement('div');support.hidden=true;
 support.innerHTML='<workbench-quality-track duration="40"></workbench-quality-track><workbench-segment-editor hydrate class="quality-review-editor"></workbench-segment-editor>';
 host.append(panel,support);
 const list=panel.querySelector('workbench-annotation-list'),actions=panel.querySelector('.workbench-quality-actions'),editor=support.querySelector('workbench-segment-editor');
 list.setAttribute(mode==='pretraining'?'data-pretraining-list':'data-posttraining-review-list','');
 actions.setAttribute(mode==='pretraining'?'data-pretraining-actions':'data-posttraining-review-actions','');
 list.dataset.reviewCopy=mode;actions.dataset.reviewCopy=mode;
 if(['pretraining','posttraining'].includes(mode)){list.setAttribute('data-no-error-reason','');editor.setAttribute('data-no-error-reason','');}
 const header=document.createElement('div');header.dataset.processingId='component-list-preview';header.dataset.id='shared-list-demo';
 const controller=createQualityReview({list,actions,editor,track:support.querySelector('workbench-quality-track'),header,storageNamespace:mode==='pretraining'?'workbench-quality-v1':`workbench-${mode}-v1`});
 controller.select(mode==='pretraining'?0:1);
});

// Use the live quality controller for the multi-lane timeline example.
document.querySelectorAll('[data-quality-track-preview]').forEach(host=>{
  const track=document.createElement('workbench-quality-track');track.setAttribute('duration','40');
  const support=document.createElement('div');support.hidden=true;
  support.innerHTML='<workbench-segment-editor hydrate></workbench-segment-editor><workbench-annotation-list variant="pretraining"></workbench-annotation-list><div class="preview-actions"><workbench-quality-conclusion></workbench-quality-conclusion><workbench-footer-actions variant="quality"></workbench-footer-actions></div>';
  host.append(track,support);
  const editor=support.querySelector('workbench-segment-editor');editor.classList.add('quality-review-editor');
  const header=document.createElement('div');header.setAttribute('data-processing-id','component-track-preview');header.setAttribute('data-id','multi-lane-demo');
  const controller=createQualityReview({track,editor,list:support.querySelector('workbench-annotation-list'),actions:support.querySelector('.preview-actions'),header,storageNamespace:'workbench-quality-v1'});
  controller.select(0);
});

document.querySelectorAll('[data-quality-single-track-preview]').forEach(host=>{
  const track=document.createElement('workbench-quality-track');track.setAttribute('duration','90');
  host.append(track);track.classList.add('quality-review-track');
  track.querySelector('timeline-controls').hidden=true;
  track.querySelectorAll('.segmented-timeline__range-fragment,.segmented-timeline__selection-label').forEach(node=>node.remove());
  const lanes=document.createElement('div');lanes.className='quality-lanes';
  lanes.innerHTML='<div class="quality-lane"></div>';track.querySelector('.segmented-timeline__body').append(lanes);
  const range=track.querySelector('timeline-range-selector');
  range._format=percent=>{const seconds=percent*.9;return String(Math.floor(seconds/60)).padStart(2,'0')+':'+(seconds%60).toFixed(1).padStart(4,'0');};
  const samples=[[3,7,'mistake'],[11,15,'failure'],[18,21,'mistake'],[24,29,'mistake'],[33,39,'failure'],[42,46,'mistake']];
  const select=index=>{
    const [start,end]=samples[index];range.setRange(start/90*100,end/90*100,false);track.seek?.(start/90*100);
    lanes.querySelectorAll('button').forEach((button,i)=>{button.classList.toggle('selected',i===index);button.setAttribute('aria-pressed',String(i===index));});
  };
  samples.forEach(([start,end,type],index)=>{
    const button=document.createElement('button');button.type='button';button.className='quality-fragment '+type;
    button.style.left=start/90*100+'%';button.style.width=(end-start)/90*100+'%';
    button.setAttribute('aria-label',(type==='failure'?'严重失误':'轻微失误')+' '+start+'至'+end+'秒');
    button.addEventListener('click',()=>select(index));lanes.firstElementChild.append(button);
  });
  requestAnimationFrame(()=>select(1));
});

// Expanded dropdown panels in the form-control catalog.
if(formShowcase){
 const body=formShowcase.querySelector('tbody');
 const addPanel=(title)=>{
   const row=document.createElement('tr'),heading=document.createElement('th'),cell=document.createElement('td');
   heading.scope='row';heading.textContent=title;cell.colSpan=2;cell.className='form-dropdown-preview';
   row.append(heading,cell);body.append(row);return cell;
 };
 for(const [title,attrs] of [
   ['物体选择面板',{bilingual:'',options:'遥控器|纸盒|书本|笔记本|桌面|抽屉|把手|书架|杯子|碗|收纳盒',value:'遥控器'}],
   ['动作描述面板',{bilingual:'',single:'',options:'选择并移动 {Object}|调整 {Object} 的摆放位置|整理散落的 {Object}|按类别整理 {Object}|拿起 {Object}|整理 {Object}|整理 {Object} 和 {Object}',value:'选择并移动 {Object}'}]
 ]){
   const cell=addPanel(title),select=document.createElement('workbench-multi-select');
   for(const [name,value] of Object.entries(attrs))select.setAttribute(name,value);
   select.setAttribute('aria-label',title==='动作描述面板'?'动作描述':'动作元素');
   const context=document.createElement('workbench-segment-editor');context.setAttribute('hydrate','');context.className='dropdown-select-context';
   cell.append(context);context.append(select);
 }
 for(const [title,kind,index] of [['不合格与失误原因面板','combined',1],['失误原因面板','mistake',0]]){
   const cell=addPanel(title),editor=document.createElement('workbench-segment-editor');
   editor.setAttribute('hydrate','');editor.className='quality-review-editor dropdown-panel-editor';editor.dataset.panelKind=kind;editor.setAttribute('data-expanded-preview','');
   const support=document.createElement('div');support.hidden=true;
   support.innerHTML='<workbench-quality-track duration="40"></workbench-quality-track><workbench-annotation-list variant="pretraining"></workbench-annotation-list><div class="preview-actions"><workbench-quality-conclusion></workbench-quality-conclusion><workbench-footer-actions variant="quality"></workbench-footer-actions></div>';
   cell.append(editor,support);
   const header=document.createElement('div');header.setAttribute('data-processing-id','dropdown-preview');header.setAttribute('data-id',kind);
   const controller=createQualityReview({editor,track:support.querySelector('workbench-quality-track'),list:support.querySelector('workbench-annotation-list'),actions:support.querySelector('.preview-actions'),header});
   const expand=()=>editor.querySelectorAll('details').forEach(details=>details.open=true);
   new MutationObserver(expand).observe(editor,{childList:true});
   controller.select(index);expand();
 }
}

if(formShowcase){
 formShowcase.querySelectorAll('td:not(.form-dropdown-preview) workbench-multi-select').forEach(select=>{
   if(select.closest('workbench-segment-editor'))return;
   const context=document.createElement('workbench-segment-editor');context.setAttribute('hydrate','');
   select.before(context);context.append(select);
 });
}

// Long-copy cases keep the same controls and option values as the live examples.
document.querySelectorAll('.form-dropdown-preview').forEach(cell=>{
 const caption=document.createElement('p');caption.className='dropdown-long-copy-caption';caption.textContent='长文本换行示例';cell.prepend(caption);
 const decorate=()=>{
   const object=cell.querySelector('workbench-multi-select:not([single]) [data-multi-option] .action-option-label');
   const action=cell.querySelector('workbench-multi-select[single] [data-multi-option] .action-option-label');
   const label=object||action;
   if(label&&!label.dataset.longCopy){
     label.dataset.longCopy='true';
     label.firstChild.textContent=object?'用于控制桌面设备并切换多种工作模式的多功能无线遥控器（含可拆卸电池保护盖）':'选择并移动 {Object} 到指定收纳区域，调整摆放方向并确认物体保持稳定且完整位于画面中';
     label.querySelector('.action-label-en').textContent=object?'Multifunction wireless remote control for desktop equipment with a removable protective battery cover':'Select and move {Object} to the designated storage area, adjust its orientation, and ensure it remains stable and fully visible in the camera frame';
   }
   cell.querySelectorAll('.quality-reason-options,.error-options').forEach(options=>{
     const option=options.querySelector('.error-option');if(!option||option.dataset.longCopy)return;
     option.dataset.longCopy='true';
     const node=[...option.childNodes].find(node=>node.nodeType===3&&node.textContent.trim());
     if(node)node.textContent+='：动作开始与结束边界未完整覆盖实际操作过程，且关键步骤存在遮挡或超出画面范围，需要结合完整视频重新检查并修正。';
   });
 };
 const editor=cell.querySelector('.dropdown-panel-editor');
 if(editor)new MutationObserver(decorate).observe(editor,{childList:true});
 decorate();
});

if(formShowcase){
 const rows=[...formShowcase.querySelectorAll('tbody>tr')];
 const navigation=rows.find(row=>row.querySelector('th')?.textContent==='片段导航按钮');
 const row=document.createElement('tr');row.innerHTML='<th scope="row">标签溢出悬浮</th><td colspan="2"><div class="overflow-hover-examples"></div></td>';
 const examples=row.querySelector('.overflow-hover-examples');
 for(const expanded of [false,true]){
   const example=document.createElement('div');example.className='overflow-hover-example';
   const caption=document.createElement('span');caption.textContent=expanded?'悬浮状态':'默认状态';
   const tags=document.createElement('div');tags.className='overflow-hover-example__tags';
   tags.innerHTML=QualityFormControls.tag('设备穿戴不规范')+QualityFormControls.tag('手部脱离夹爪')+'<span class="audit-overflow'+(expanded?' is-preview-open':'')+'" tabindex="0" aria-label="另外 3 项质检原因">'+QualityFormControls.overflowCount('+3')+'<span class="audit-overflow-popover quality-hover-popover" role="tooltip">'+['采集时长不足','视频与采集任务不符','关键操作过程缺失'].map(text=>QualityFormControls.tag(text)).join('')+'</span></span>';
   example.append(caption,tags);examples.append(example);
   QualityFormControls.fitPopover(tags.querySelector('.audit-overflow'));
 }
 if(navigation)navigation.after(row);else formShowcase.querySelector('tbody').append(row);
}
