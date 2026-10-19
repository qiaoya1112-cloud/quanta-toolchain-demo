(() => {
 const esc=value=>String(value??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const field=(label,value)=>'<div><dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd></div>';
 window.openProcessingTaskDetail=(record)=>{
  const [id,name,project,flows,enabled,priority,creator,time,nature='正式']=record;
  let saved;try{saved=JSON.parse(localStorage.getItem('quanta-processing-tasks')||'[]').find(t=>String(t.id)===String(id));}catch{}
  const main=document.querySelector('.process-page__main'),previous=[...main.children].map(el=>[el,el.hidden]);
  previous.forEach(([el])=>el.hidden=true);
  const detail=document.createElement('section');detail.className='processing-detail';
  const conditions=saved?.filters;
  const stages=saved?.stages||flows.map(([stage,flow,version,completed,total])=>({stage,flow,version,completed,total}));
  detail.innerHTML='<task-page-header title="处理任务详情" back back-label="返回任务处理"></task-page-header><div class="creator-layout"><task-step-nav></task-step-nav><div class="creator-main">'+
   '<section data-detail-panel="0"><h2>基本信息</h2><dl class="creator-card processing-detail-fields">'+field('任务名称',name)+field('所属项目',project)+field('任务性质',nature)+field('优先级',priority)+field('预期任务量',saved?.volume||'未配置')+(saved?.quantity?field('任务量',saved.quantity):'')+field('任务 ID',id)+field('处理状态',enabled?'启用':'停用')+field('任务状态',enabled?'已发布':'未发布')+field('创建人',creator)+field('创建时间',time)+'</dl></section>'+
   '<section data-detail-panel="1" hidden><h2>筛选条件</h2><div class="creator-notice form-feedback form-feedback--info">满足筛选条件的数据将分批进入处理任务，每 30 分钟进入一批，每批最多 2000 条。</div><div class="creator-card">'+(conditions?.length?'<div class="task-data-table"><div class="task-data-table__scroll"><table><thead><tr><th>筛选项</th><th>操作符</th><th>值</th></tr></thead><tbody>'+conditions.map(f=>'<tr><td>'+esc(f.field)+'</td><td>'+esc(f.operator)+'</td><td>'+esc(f.value)+'</td></tr>').join('')+'</tbody></table></div></div>':'<p class="creator-empty">'+(saved?'不限制：所有新入湖数据均可进入该任务':'该示例任务未提供筛选条件')+'</p>')+'</div></section>'+
   '<section data-detail-panel="2" hidden><h2>业务环节</h2>'+stages.map(stage=>'<section class="creator-card processing-detail-stage"><h3>'+esc(stage.stage)+'</h3><dl class="processing-detail-fields">'+field('处理流程',stage.flow)+field('流程版本',stage.version)+(stage.total!==undefined?field('处理进度',stage.completed+' / '+stage.total):'')+'</dl><h3>节点配置</h3>'+(stage.nodes?.length?stage.nodes.map(node=>'<dl class="processing-detail-fields">'+Object.entries(node).map(([key,value])=>field(({name:'节点名称',inherit:'继承分配',assignees:'处理人',heading:'节点名称',rule:'处理规则'})[key]||key,Array.isArray(value)?(value.map(person=>[person.type,person.name].filter(Boolean).join('：')).join('、')||'未配置'):typeof value==='boolean'?(value?'是':'否'):value)).join('')+'</dl>').join(''):'<p class="creator-empty">未提供节点配置</p>')+'</section>').join('')+'</section>'+
   '</div></div><footer class="creator-footer"><text-button variant="outline" data-detail-close>关闭</text-button></footer>';
  main.append(detail);main.classList.add('has-processing-detail');
  const close=()=>{detail.remove();main.classList.remove('has-processing-detail');previous.forEach(([el,hidden])=>el.hidden=hidden);};
  detail.addEventListener('header-back',close);
  detail.querySelector('[data-detail-close]').addEventListener('click',close);
  detail.addEventListener('step-change',e=>{detail.querySelector('task-step-nav').active=e.detail;detail.querySelectorAll('[data-detail-panel]').forEach(p=>p.hidden=Number(p.dataset.detailPanel)!==e.detail);detail.querySelector('.creator-main').scrollTop=0;});
 };
})();
