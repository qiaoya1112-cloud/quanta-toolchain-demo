(()=>{
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 window.openEvaluationSet=({host,row,cases})=>{
  const list=host.firstElementChild,header=document.querySelector('[data-model-title]').closest('header');
  const listHidden=list.hidden,headerHidden=header.hidden;list.hidden=true;header.hidden=true;
  const drawer=document.createElement('section');drawer.className='evaluation-detail evaluation-set-detail';
  const back=()=>{drawer.remove();list.hidden=listHidden;header.hidden=headerHidden;};
  const ids=row.caseIds||[],selected=ids.map(id=>cases.find(c=>c.id===id)).filter(Boolean),tags=row.tags||[];
  const cols=[['序号',64],['用例 ID',110],['Stage',180],['Story',240],['prompt_EN',380],['prompt_CN',320],['Skill标签',220],['Factor',300],['布置图片',140],['数据归属',120],['分布类型',110]];
  drawer.innerHTML=`<task-page-header back title="评测集详情"></task-page-header><div class="evaluation-detail-body"><div class="eval-case-form"><section class="eval-case-section"><h3>基本信息</h3><form-input label="评测集名称 *" value="${esc(row.name)}" disabled></form-input><form-select label="所属项目 *" disabled><option>${esc(row.project)}</option></form-select><label><span class="form-input__label">描述</span><textarea class="form-input__control" readonly>${esc(row.description)}</textarea></label><form-select label="标签" multiple disabled>${tags.map(t=>`<option selected>${esc(t)}</option>`).join('')}</form-select></section><section class="eval-case-section eval-set-cases"><h3>评测用例配置</h3><div class="task-data-table eval-set-table"><div class="task-data-table__scroll"><table><thead><tr>${cols.map(([label,width])=>`<th style="width:${width}px">${label}</th>`).join('')}</tr></thead><tbody>${selected.map((c,i)=>`<tr><td>${i+1}</td><td>${esc(c.id)}</td><td>${esc(c.stage)}</td><td>${esc(c.story)}</td><td>${esc(c.en)}</td><td>${esc(c.cn)}</td><td>${esc(c.skill)}</td><td>${esc(c.factor)}</td><td>${c.images?.length?c.images.map(im=>`<img class="eval-set-image" src="${esc(im.src)}" alt="${esc(im.type||im.name)}">`).join(''):'—'}</td><td>${esc(c.owner||'—')}</td><td>${esc(row.distributions?.[c.id]||'ID')}</td></tr>`).join('')||'<tr><td colspan="11" class="eval-case-empty">暂无评测用例</td></tr>'}</tbody></table></div></div></section></div></div><footer class="app-drawer__footer eval-set-footer"><text-button variant="outline" data-close>关闭</text-button></footer>`;
  host.append(drawer);drawer.querySelector('task-page-header').addEventListener('header-back',back);drawer.querySelector('[data-close]').addEventListener('click',back);
  if(selected.length)customElements.get('task-data-table').enhanceFixedEdges(drawer.querySelector('.eval-set-table'),2,1);
 };
})();
