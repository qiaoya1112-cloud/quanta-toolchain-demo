/* Shared small form controls used by workflow editors and their previews. */
window.QualityFormControls=(()=>{
const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function tag(text,{tone='default',group='',index=0,action='',audit=false,secondaryText=''}={}){
 const removed=tone==='purple';
 const attrs=action?`data-${action}-group="${escape(group)}" data-${action}-reason="${index}"`:'';
 return `<span class="quality-reason-tag quality-tag ${audit?'audit-tag':''} ${removed?'is-removed':tone==='blue'?'is-added':'is-correct'}" data-tag-tone="${tone}" ${group?`data-reason-kind="${group}"`:''}><span class="quality-tag__label">${escape(text)}${secondaryText?` <span class="quality-tag__secondary">${escape(secondaryText)}</span>`:''}</span>${removed?'<small>错误项</small>':''}${action?`<button type="button" ${attrs} aria-label="${removed?'恢复':'移除'}${escape(text)}"><svg class="quality-tag__icon" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${removed?'<path d="M6 3 2.5 6.5 6 10M3 6.5h6.5a4 4 0 0 1 0 8H8"/>':'<path d="m4 4 8 8M12 4l-8 8"/>'}</svg></button>`:''}</span>`;
}
function navigation({previous=true,next=true,left=false,right=true}={}){return `<button class="segment-action segment-action--navigate" data-nav="-1" ${previous?'':'disabled'}>上一段 <kbd>⌘↑</kbd></button><button class="segment-action segment-action--navigate" data-nav="1" ${next?'':'disabled'}>下一段 <kbd>⌘↓</kbd></button><button class="segment-action segment-action--navigate" data-lane-nav="-1" ${left?'':'disabled'}>同轨左 <kbd>⌘←</kbd></button><button class="segment-action segment-action--navigate" data-lane-nav="1" ${right?'':'disabled'}>同轨右 <kbd>⌘→</kbd></button>`;}
function errorBadge(reason){return String(reason||'').trim()?`<span class="quality-audit-alert" title="${escape('错误原因：'+reason)}" aria-label="${escape('错误原因：'+reason)}">!</span>`:'';}
function clearFooter(attribute='data-clear-reasons',value=''){
 return `<button type="button" class="error-popover__clear" ${attribute}${value?`="${escape(value)}"`:''}>清除已选原因</button>`;
}
function clearAll(){return '<button type="button" class="quality-reasons-clear quality-tag-clear" data-clear-reasons aria-label="清除全部原因" title="清除全部原因"><svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="m4 4 8 8M12 4l-8 8"/></svg></button>';}
function typeSwitch(type,original=false){return `<div class="quality-types" role="group" aria-label="${original?'质检结果':'片段类型'}">${['mistake','failure'].map(value=>`<button type="button" class="${value}" ${original?'data-original-type':'data-type'}="${value}" aria-pressed="${type===value}">${value==='mistake'?'失误':'不合格'}</button>`).join('')}</div>`;}
function hoverHint(label,tip){return `<span class="quality-audit-legend__item" tabindex="0">${escape(label)}<span class="quality-audit-legend__tooltip quality-hover-popover" role="tooltip">${escape(tip)}</span></span>`;}
function legend(){return [
 ['正确项','未修改的原始描述视为正确项。'],
 ['错误项','原始标注中错选的描述。点击标签右侧“×”标记为错误项并保留记录，点击撤回图标可恢复。'],
 ['遗漏项','原始标注中缺失的描述。审核时新增的描述标记为遗漏项。']
].map(([label,tip])=>hoverHint(`● ${label}`,tip)).join('');}
  function reasonTags(item,{isAudit=false,isRejection=false,isSecondary=false,M,escape,qualityReviewAssetRoot}){
    if(isAudit){
      const base=((isRejection||isSecondary)?item.auditReference:item.auditOriginal)||{mistakes:[],failures:[]};
      const tags=['failures','mistakes'].flatMap(group=>[...new Set([...base[group],...item[group]])].map(reason=>{
        const removed=!item[group].includes(reason),added=!base[group].includes(reason);
        return tag(reason,{tone:removed?'purple':added?'blue':'default',group,index:M[group].indexOf(reason),action:removed?'restore':'remove',audit:true});
      })).join('');
      return `<span class="quality-reason-tags">${tags||'请选择原因'}${item.failures.length||item.mistakes.length?clearAll():''}</span><img src="${qualityReviewAssetRoot}icon-chevron.svg" alt="" aria-hidden="true">`;
    }
    const tags=['failures','mistakes'].flatMap(group=>item[group].map(reason=>tag(reason,{tone:group==='failures'?'red':'orange',group,index:M[group].indexOf(reason),action:'remove'}))).join('');
    return `<span class="quality-reason-tags">${tags||'请选择原因'}${tags?'<span class="quality-reason-tag quality-reason-more" hidden></span>'+clearAll():''}</span><img src="${qualityReviewAssetRoot}icon-chevron.svg" alt="" aria-hidden="true">`;
  }
function bindDescriptionHints(root){
 root.querySelectorAll('.workbench-annotation-list__description[title]').forEach(el=>{el.dataset.hoverDescription=el.title;el.removeAttribute('title');});
 if(root.dataset.descriptionHints)return;
 root.dataset.descriptionHints='true';
 let popup;
 const hide=()=>{popup?.remove();popup=null;};
 const show=event=>{
  const target=event.target.closest('[data-hover-description]')||event.target.closest('.workbench-annotation-list__row')?.querySelector('[data-hover-description]');
  hide();
  if(!target||(target.scrollWidth<=target.clientWidth&&target.scrollHeight<=target.clientHeight))return;
  popup=document.createElement('div');popup.className='quality-hover-popover quality-description-tooltip';popup.setAttribute('role','tooltip');popup.textContent=target.dataset.hoverDescription;document.body.append(popup);
  const rect=target.getBoundingClientRect(),box=popup.getBoundingClientRect();
  popup.style.left=Math.max(8,Math.min(rect.left,innerWidth-box.width-8))+'px';
  popup.style.top=Math.max(8,rect.top-box.height-8)+'px';
 };
 root.addEventListener('mouseover',show);root.addEventListener('mouseout',hide);
 root.addEventListener('focusin',show);root.addEventListener('focusout',hide);
 root.addEventListener('click',hide);window.addEventListener('scroll',hide,true);window.addEventListener('resize',hide);
 root.addEventListener('keydown',event=>{if(event.key==='Escape')hide();});
}
function automaticSegment({start,end}){
 const format=value=>`${String(Math.floor(value/60)).padStart(2,'0')}:${(value%60).toFixed(1).padStart(4,'0')}`;
 const controls=typeSwitch('mistake').replaceAll('<button ', '<button disabled ');
 return `<section class="card form-card quality-automatic-segment"><div class="form-row form-row--meta"><div class="segment-meta">${tag('自动')}<span>开始</span><b>${format(start)}</b><span>结束</span><b>${format(end)}</b><span>时长</span><b>${(end-start).toFixed(1)}s</b></div><span class="quality-automatic-segment__notice">系统判定 · 只读</span></div><div class="form-row"><span class="field-label">片段类型</span>${controls}<span class="field-label">失误描述</span><div class="input-like quality-automatic-segment__description" role="textbox" aria-label="失误描述" aria-readonly="true">片段时长过短</div></div></section>`;
}
function overflowCount(count=''){return tag(count).replace('quality-tag__label','quality-tag__label audit-overflow-count');}
function fitPopover(trigger){
 const fit=()=>{
  const panel=trigger.querySelector('.audit-overflow-popover');
  panel.style.width='';
  if(!panel.getClientRects().length)return;
  const rect=panel.getBoundingClientRect();
  const edge=Math.max(...Array.from(panel.children,tag=>tag.getBoundingClientRect().right-rect.left));
  if(Number.isFinite(edge))panel.style.width=Math.ceil(edge+5)+'px';
 };
 trigger.addEventListener('mouseenter',fit);
 trigger.addEventListener('focusin',fit);
}
return {clearFooter,bindDescriptionHints,automaticSegment,overflowCount,errorBadge,hoverHint,navigation,tag,clearAll,typeSwitch,legend,reasonTags,fitPopover};
})();
