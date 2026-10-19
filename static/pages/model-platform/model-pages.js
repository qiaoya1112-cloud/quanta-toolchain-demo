(() => {
  const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const raw=[['t1','Clean the whiteboard',1280,1180,940,'Lance Li','2026-05-21 10:12'],['t2','Tidy the desk',960,905,720,'Wei Zhang','2026-05-24 14:02'],['t3','Water the plant',640,600,410,'Min Chen','2026-05-27 11:10'],['t4','Pour the cup',520,510,0,'Lance Li','2026-05-29 09:33'],['t5','Fold the towel',410,0,0,'Wei Zhang','2026-06-02 16:48']].map(([id,name,collected,checked,annotated,creator,created])=>({id,name,collected,checked,annotated,creator,created}));
  const external=[['x1','Open Pick-Place (RT-1)','rt1_pickplace_v1','tos://3rd/rt1_pickplace.tar.gz','导入完成','Min Chen','2026-05-18 09:20'],['x2','Bridge Kitchen v2','bridge_kitchen_v2','tos://3rd/bridge_v2.parquet','导入完成','Lance Li','2026-05-22 13:05'],['x3','DROID subset','droid_subset_0610','tos://3rd/droid_subset.zip','导入中','Wei Zhang','2026-06-10 11:41'],['x4','Ego4D hands clips','—','tos://3rd/ego4d_hands.tar','导入失败','Min Chen','2026-06-12 15:58']].map(([id,name,dataset,file,status,creator,created])=>({id,name,dataset,file,status,creator,created}));
  const externalColumns=[['id','任务 ID',90],['name','任务名称',220],['dataset','数据集名称',210],['file','文件地址',310],['status','导入状态',120],['creator','创建人',130],['created','创建时间',180]];
  const episodes=[['120489','t1','uDAS','normal','是','是',1434,'47.8s'],['120502','t1','Moz','normal','是','否',1042,'34.7s'],['120513','t1','uDAS','normal','是','是',979,'32.6s'],['120521','t1','uDAS','dagger','是','否',56,'1.9s'],['120532','t1','Moz','normal','是','否',1310,'43.7s'],['121005','t2','uDAS','normal','是','是',1188,'39.6s'],['121014','t2','Moz','normal','是','是',1402,'46.7s']].map(([id,task,device,type,checked,annotated,frames,duration],i)=>({id,task,device,type,checked,annotated,frames,duration,batch:'B20250612-01',created:'2026-06-12',operator:i<5?'Lance Li':'Wei Zhang',tag:'桌面操作',dagger:type==='dagger'?'人工干预':'无',prompt:i<5?'Clean the whiteboard':'Tidy the desk'}));
  const training=[
    ['9001','20260617_pi05_cleanwhiteboard_v5_main','擦白板场景 PI0.5 主线微调，验证 v5 数据集收敛效果','成功','高','joanna.qiao','2026-06-17 03:00:00','8h 30m'],
    ['9003','20260618_pi05_tidydesk_joint_train','桌面整理 A/B 数据联合训练，提升跨场景泛化能力','成功','低','Lance Li','2026-06-18 14:00:00','9h 10m'],
    ['9005','20260621_pi05_cleanwhiteboard_v6_queued','擦白板 v6 增量数据训练，验证新增样本带来的收益','排队中','中','joanna.qiao','2026-06-21 10:00:00','—'],
    ['7757','20260615_pi05_oldft_scortip_cellphone_manip2','药丸分拣新观测输入微调，启用中心裁剪与双机械臂控制','运行中','高','hannah.wang','2026-06-16 11:57:35','—'],
    ['7539','20260602_ManualDagger2_NarrowTable_Moz1WB','窄桌场景 Manual Dagger 二阶段训练，适配 Moz1 全身控制','成功','低','Maple Liu','2026-06-16 01:52:20','9h 12m'],
    ['7374','20260615_PickBottle_Pico','Pico 机械臂瓶体抓取专项训练，优化抓取稳定性','成功','中','tao.wang','2026-06-15 13:04:06','8h 22m'],
    ['7285','20260615_pi05_up_Pen_1h_8','笔类物体抓取一小时数据快速微调，验证小样本收敛','成功','高','joanna.qiao','2026-06-15 11:38:44','9h 10m'],
    ['6869','20260614_pi05_SkewerFruits_0322_new_check_32','水果串签场景新数据回归训练，检查动作连续性与成功率','失败','低','Maple Liu','2026-06-14 23:32:34','1h 40m']
  ].map(([id,name,description,status,priority,creator,created,duration],i)=>({id,name,description,status,priority,creator,created,duration,tag:i<3?'桌面操作':'抓取',dataset:i<3?'桌面操作数据集':'抓取数据集'}));
  const kingsoftTraining=[['9002','20260618_pi05_cleanwhiteboard_v5_ctrl','中','Lance Li','2026-06-18 09:00:00'],['9004','20260620_pi05_cleantable_baseline','高','Min Chen','2026-06-20 08:00:00'],['7916','robotwin_pi05_datamil_stack_blocks_two_top10pct_cotrain','低','tao.wang','2026-06-17 03:23:39'],['7560','20260615_HouseHold_newper_stop_32','中','joanna.qiao','2026-06-16 11:18:17'],['7466','20260615_pi05_oldft_sortpill_newobs_centercrop','高','Min Chen','2026-06-15 19:54:01'],['7325','20260615_HouseHold_0601_5w_32','低','Lance Li','2026-06-15 11:39:45'],['6873','20260614_pi05_SkewerFruits_from_0322_8','中','Maple Liu','2026-06-15 00:46:53']].map(([id,name,priority,creator,created],i)=>({id,name,priority,creator,created,status:i===1?'成功':'运行中',duration:i===1?'7h 40m':'—',description:'金山云训练任务',dataset:'桌面操作数据集',tag:'桌面操作'}));
  const checkpoints=[['9001','20260617_clean_whiteboard_40000','HouseHold stop 32 任务 40k step 稳定版本','joanna.qiao','2026-06-17 12:00:00','joanna.qiao'],['9002','20260617_clean_whiteboard_50000','opd taskA SFT 50k step 候选版本','joanna.qiao','2026-06-17 18:00:00','joanna.qiao'],['9004','20260618_tidy_desk_joint','taskAB 单模型无 BC loss 版本','Lance Li','2026-06-18 23:00:00','Lance Li'],['7374','20260518_HouseHold_stop32','HouseHold stop 32 任务 40k step 稳定版本','Lance Li','2026-06-11 19:30:46','Lance Li'],['7285','20260608_opd_exp4_case','HouseHold stop 32 任务 50k step 对照版本','—','2026-06-10 15:08:00','Hannah Wang']].map(([id,name,description,creator,created,cacher])=>({id,name,description,creator,created,cacher,cached:created,asset:'—'}));
  const kingsoftCheckpoints=[
    ['9003','20260618_clean_whiteboard_v5_ctrl_45000','HouseHold stop 32 任务 50k step 对照版本','Lance Li','2026-06-18 20:00:00','Lance Li',45000,'9002'],
    ['9005','20260620_clean_table_baseline_40000','HouseHold stop 32 任务 40k step 合并失败待处理','Min Chen','2026-06-20 16:00:00','Min Chen',40000,'9004'],
    ['7916','20260613_HouseHold_stop32','HouseHold stop 32 任务 40k step 稳定版本','—','2026-06-13 00:00:02','tao.wang',40000,'7916'],
    ['7560','20260609_opd_exp5a_single','HouseHold stop 32 任务 50k step 对照版本','—','2026-06-13 05:05:41','tao.wang',50000,'7560'],
    ['7500','20260610_clean_whiteboard_joint','taskAB 单模型无 BC loss 版本','joanna.qiao','2026-06-11 10:00:00','joanna.qiao',40000,'7560'],
    ['7325','20260518_HouseHold_stop32','opd taskA SFT 50k step 候选版本','Lance Li','2026-06-11 03:42:38','Lance Li',50000,'7325'],
    ['6873','catl-checkpoint-0608','taskAB 单模型无 BC loss 版本','Liquan Zheng','2026-06-08 18:12:22','Liquan Zheng',40000,'6873'],
    ['7467','20260615_pi05_oldft_sortpill','HouseHold stop 32 任务 40k step 稳定版本','—','2026-06-15 22:10:00','Min Chen',40000,'7466']
  ].map(([id,name,description,creator,created,cacher,steps,trainingId])=>({id,name,description,creator,created,cacher,cached:created,steps,trainingId,asset:'—',model:'Spirit v1.7'}));
  checkpoints.forEach((row,i)=>{row.steps=i===1?50000:40000;row.model='Spirit v1.7';row.trainingId=i<2?'9001':i===2?'9003':row.id;});
  checkpoints[0].name='20260617_clean_whiteboard_v5_main_40000';
  checkpoints[1].name='20260617_clean_whiteboard_v5_main_50000';
  const configs={
    'model-data-query':{title:'数据查询',tabs:'model-query',rows:episodes,columns:[['id','数据 ID',120],['task','Task ID',100],['device','设备',100],['type','类型',110],['checked','是否质检',110],['annotated','是否标注',110],['frames','帧数',110],['duration','时长',90]],actions:['预览']},
    'model-raw-data':{title:'原始数据',tabs:'model-source',rows:raw,columns:[['id','任务 ID',110],['name','任务名称',240],['collected','已采集数',130],['checked','已质检数',130],['annotated','已标注数',130],['creator','创建人',150],['created','创建时间',190]],actions:[]},
    'model-training':{title:'训练任务',tabs:'model-cloud',rows:training,columns:[['id','ID',80],['name','名称',330],['description','描述',320],['status','状态',100],['priority','优先级',90],['creator','创建人',140],['created','创建时间',185],['duration','运行时长',110]],actions:['停止','复制','更多']},
    'model-checkpoints':{title:'Checkpoint',tabs:'model-cloud',rows:checkpoints,columns:[['id','ID',75],['name','Checkpoint',250],['asset','资产标记',110],['description','描述',300],['creator','创建人',130],['created','创建时间',180],['cacher','缓存人',130],['cached','缓存时间',180]],actions:['TEST','DAgger','血缘','标记为资产']}
  };
  const input=(name,label,placeholder='')=>`<form-input name="${name}" label="${label}" placeholder="${placeholder||'请输入'+label}"></form-input>`;
  const select=(name,label,options)=>`<form-select name="${name}" label="${label}"><option value="">全部</option>${options.map(x=>`<option>${x}</option>`).join('')}</form-select>`;
  const dates=label=>`<div class="model-date"><span>${label}</span><div><input class="is-empty" type="date" name="from" aria-label="${label}开始"><span>至</span><input class="is-empty" type="date" name="to" aria-label="${label}结束"></div></div>`;
  const button=(label,action=label,variant='outline')=>`<text-button variant="${variant}" data-model-action="${action}">${label}</text-button>`;
  const badge=(value,tone)=>`<span class="table-outline-tag table-outline-tag--${tone}">${esc(value)}</span>`;
  let jobs=[];
  window.renderModelPage = (host,id) => {
    const config=configs[id];if(!config){host.replaceChildren();return;}
    const query=id==='model-data-query',train=id==='model-training',check=id==='model-checkpoints';
    let tab=query?'fixed':train||check?'volcano':'self',filters={},page=1,pageSize=10,matched=[],sqlRows=null;
    const header=document.querySelector('[data-model-title]').closest('header');header.querySelector('[data-model-actions]')?.remove();
    const actions=document.createElement('div');actions.dataset.modelActions='';actions.className='model-actions';
    actions.innerHTML=train?button('新增训练任务','新增训练任务','primary'):check?button('查看缓存记录')+button('去部署','去部署','primary'):!query?button('查看采集任务'):'';header.append(actions);
    const filtersHTML=query?`<details open><summary>任务信息</summary><div class="model-filter-grid">${input('task','采集任务','如 t1,t2，多个逗号隔开')}${select('tag','任务标签',['桌面操作'])}${input('batch','批次编号','如 B20250612-01')}${select('device','设备序列号',['uDAS','Moz'])}${dates('采集时间')}${input('operator','操作员','搜索姓名 / ID')}${select('type','采集类型',['normal','dagger'])}${select('dagger','Dagger 类型',['人工干预','无'])}</div></details><details><summary>处理信息</summary><div class="model-filter-grid">${select('checked','是否质检',['是','否'])}${select('annotated','是否标注',['是','否'])}</div></details><details><summary>提示词</summary><div class="model-filter-grid">${input('prompt','提示词','输入提示词关键词')}</div></details><details><summary>导出要求</summary><div class="model-filter-grid">${select('export','导出格式',['JSON','CSV'])}</div></details>`: `<div class="model-filter-grid">${train?input('name','名称')+select('tag','标签',['桌面操作','抓取'])+select('dataset','数据集',['桌面操作数据集','抓取数据集'])+input('creator','创建人'):check?input('name','Checkpoint')+input('creator','创建人')+input('cacher','缓存人'):input('id','任务 ID','如 t1')+input('name','任务名称','任务名称关键词')+input('creator','创建人','搜索姓名 / ID')+dates('创建时间')}</div>`;
    host.innerHTML=`<section class="model-page"><task-status-tabs variant="${config.tabs}"></task-status-tabs>${query?'<task-filter-bar variant="grouped" columns="4" full-width>':''}<form class="model-filters" aria-label="${config.title}筛选">${filtersHTML}</form>${query?'</task-filter-bar>':''}${query?`<div class="model-sql" hidden><div class="model-sql-assistant"><label for="model-sql-prompt">✦ 用自然语言生成 SQL</label><div><input id="model-sql-prompt" autocomplete="off" placeholder="例如：查询擦白板任务，或数据 ID 120489"><text-button variant="primary" data-model-action="生成 SQL">生成 SQL</text-button></div></div><div class="model-sql-editor"><pre aria-hidden="true" data-sql-lines>1</pre><textarea id="model-sql" aria-label="SQL 查询" spellcheck="false" autocomplete="off" wrap="off">SELECT * FROM data;</textarea></div><div class="model-sql-footer"><span data-sql-status role="status"></span><text-button variant="primary" data-model-action="执行 SQL">执行</text-button></div></div>`:''}<div class="model-results"><span data-summary></span><div class="model-actions">${query?button('导出结果')+button('查看数据集创建进度')+button('用结果新建数据集'):''}</div></div><div class="task-data-table command-table"><div class="task-data-table__scroll"><table aria-label="${config.title}列表"><colgroup>${config.columns.map(c=>`<col style="width:${c[2]}px">`).join('')}${config.actions.length?`<col style="width:${check?300:train?170:100}px">`:''}</colgroup><thead><tr>${columns().map(([key,label])=>`<th scope="col">${label}</th>`).join('')}${config.actions.length?'<th scope="col">操作</th>':''}</tr></thead><tbody></tbody></table><p class="command-empty" data-empty hidden>暂无符合条件的数据</p></div><list-pagination total="0" page-size="10"></list-pagination></div><p role="status" data-model-feedback></p></section>`;
    if(id==='model-raw-data'||train||check)host.querySelector('.model-results').remove();
    let dialog=document.querySelector('#model-dialog');if(!dialog){dialog=document.createElement('dialog');dialog.id='model-dialog';dialog.className='command-dialog';document.body.append(dialog);}
    function show(title,html){dialog.innerHTML=`<header><h2 id="model-dialog-title">${esc(title)}</h2><text-button variant="text" data-close>关闭</text-button></header><div data-dialog-content>${html}</div><footer><text-button variant="outline" data-close>关闭</text-button></footer>`;dialog.setAttribute('aria-labelledby','model-dialog-title');dialog.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>dialog.close());dialog.showModal();}
    const feedback=host.querySelector('[data-model-feedback]');
    function source(){return tab==='external'?external:tab==='kingsoft'?(train?kingsoftTraining:check?kingsoftCheckpoints:[]):config.rows;}
    function columns(){return tab==='external'?externalColumns:train&&tab==='kingsoft'?config.columns.filter(c=>c[0]!=='description'):config.columns;}
    function render(){
      host.querySelector('colgroup').innerHTML=columns().map(c=>`<col style="width:${c[2]}px">`).join('')+(config.actions.length?`<col style="width:${check?300:train?170:100}px">`:'');
      host.querySelector('thead tr').innerHTML=columns().map(c=>`<th scope="col">${c[1]}</th>`).join('')+(config.actions.length?'<th scope="col">操作</th>':'');
      matched=(query&&tab==='sql'&&sqlRows!==null?sqlRows:source()).filter(row=>Object.entries(filters).every(([key,value])=>{
        if(!value||key==='export'||query&&tab==='sql')return true;
        if(key==='from')return row.created.slice(0,10)>=value;if(key==='to')return row.created.slice(0,10)<=value;
        if(key==='task')return value.split(/[,，]/).map(v=>v.trim()).includes(row.task);
        return String(row[key]??'').toLowerCase().includes(value.toLowerCase());
      }));
      page=Math.min(page,Math.max(1,Math.ceil(matched.length/pageSize)));
      host.querySelector('tbody').innerHTML=matched.slice((page-1)*pageSize,page*pageSize).map(row=>`<tr data-id="${row.id}">${columns().map(([key])=>{
        let value=esc(row[key]);if(typeof row[key]==='number')value=row[key].toLocaleString();
        if(key==='name'||!query&&!train&&!check&&key==='id')value=`<button class="model-name" data-row-action="详情">${value}</button>`;
        if(key==='status')value=badge(row[key],({导入完成:'active',导入中:'running',导入失败:'danger',成功:'active',失败:'danger',运行中:'running',排队中:'warning',已停止:'neutral'})[row[key]]||'neutral');
        if(key==='priority')value=badge(row[key],({高:'danger',中:'warning',低:'neutral'})[row[key]]);
        if(query&&['checked','annotated','type'].includes(key))value=badge(row[key],row[key]==='是'?'active':'neutral');
        if(key==='asset'&&row.asset!=='—')value=badge(row.asset,'active');
        return `<td${['name','description','created','cached'].includes(key)?' class="model-wrap"':''}>${value}</td>`;
      }).join('')}${config.actions.length?`<td>${config.actions.map(action=>`<button data-row-action="${action}" ${action==='停止'&&!['运行中','排队中'].includes(row.status)?'disabled':''}>${action==='标记为资产'&&row.asset!=='—'?'取消资产标记':action}</button>`).join('')}</td>`:''}</tr>`).join('');
      if(config.actions.length)customElements.get('task-data-table').enhanceFixedEdges(host.querySelector('.command-table'));
      host.querySelector('[data-empty]').hidden=matched.length>0;
      const summary=host.querySelector('[data-summary]');
      if(summary)summary.textContent=train?`运行中任务 ${source().filter(r=>r.status==='运行中').length} 条 · 全部任务 ${matched.length} 条`:`${query?'查询结果 · ':''}共 ${matched.length} 条`;
      const pagination=host.querySelector('list-pagination');pagination.setAttribute('total',matched.length);pagination.setAttribute('page',page);
    }
    host.querySelector('form').addEventListener('input',updateFilters);host.querySelector('form').addEventListener('change',updateFilters);host.querySelector('form').onsubmit=e=>e.preventDefault();
    function updateFilters(){host.querySelectorAll('.model-date input').forEach(input=>input.classList.toggle('is-empty',!input.value));filters=Object.fromEntries(new FormData(host.querySelector('form')));page=1;render();}
    host.querySelector('task-status-tabs').addEventListener('tab-change',e=>{tab=e.detail.value;page=1;if(train){filters={};host.querySelector('form').innerHTML=tab==='kingsoft'?`<div class="model-filter-grid">${input('name','名称')}${input('creator','创建人')}</div>`:filtersHTML;}if(id==='model-raw-data'){
        filters={};host.querySelector('form').innerHTML=tab==='external'?`<div class="model-filter-grid">${input('dataset','数据集名称','数据集名称关键词')}${select('status','导入状态',['导入完成','导入中','导入失败'])}${input('creator','创建人','搜索姓名 / ID')}${dates('创建时间')}</div>`:filtersHTML;
        actions.innerHTML=tab==='external'?button('+ 导入','导入三方数据','primary'):button('查看采集任务');
      }if(query){host.querySelector('form').hidden=tab==='sql';host.querySelector('task-filter-bar').hidden=tab==='sql';host.querySelector('.model-sql').hidden=tab!=='sql';}render();});
    host.querySelector('list-pagination').addEventListener('page-change',e=>{page=e.detail.page;pageSize=e.detail.pageSize;render();});
    host.querySelector('tbody').onclick=e=>{
      const b=e.target.closest('[data-row-action]');if(!b||b.disabled)return;const row=source().find(r=>r.id===b.closest('tr').dataset.id),action=b.dataset.rowAction;
      if(action==='停止'){row.status='已停止';render();feedback.textContent='已停止（当前页面演示）';return;}
      if(action==='标记为资产'){row.asset=row.asset==='—'?'已标记':'—';render();return;}
      if(action==='复制'){showCreate('复制训练任务',row.name+' 副本',name=>{config.rows.unshift({...row,id:String(Date.now()),name,status:'排队中',duration:'—'});render();});return;}
      if(action==='更多'){show('任务操作',button('查看详情','详情')+button('查看 Checkpoint','checkpoint'));dialog.querySelector('[data-model-action="详情"]').onclick=()=>{dialog.close();details(row);};dialog.querySelector('[data-model-action="checkpoint"]').onclick=()=>{dialog.close();location.hash='model-checkpoints';};return;}
      if(['TEST','DAgger','血缘'].includes(action)){show(action,`<p>Checkpoint：${esc(row.name)}</p><p>${action==='血缘'?'当前示例未提供完整训练血缘数据。':'当前为页面演示，未连接任务执行服务。'}</p>`);return;}
      details(row);
    };
    function details(row){if(check){checkpointDetails(row);return;}if(train){window.openTrainingDetail(host,row,tab);return;}if(query){window.openDataPreview(row);return;}show(query?'数据预览':config.title+'详情',`<dl class="command-details">${columns().map(([key,label])=>`<div><dt>${label}</dt><dd>${esc(row[key])}</dd></div>`).join('')}</dl>${query?'<p class="model-note">示例未提供对应视频文件，当前展示数据元信息。</p>':''}`);}
    function checkpointDetails(row){
      const task=(tab==='kingsoft'?kingsoftTraining:training).find(task=>task.id===row.trainingId);
      const drawer=document.createElement('app-drawer');drawer.className='checkpoint-detail-drawer';drawer.setAttribute('heading',row.name);
      const fields=[['Checkpoint',row.name],['描述',row.description],['训练任务',task?.name||'—'],['基础模型',row.model],['训练步数',row.steps],['创建人',row.creator],['创建时间',row.created]];
      drawer.innerHTML=`<dl class="checkpoint-detail-fields">${fields.map(([label,value])=>`<div><dt>${label}</dt><dd>${esc(value)}</dd></div>`).join('')}</dl><p role="status" data-lineage-info class="model-note"></p><div drawer-footer><text-button variant="outline" data-lineage>查看血缘</text-button><text-button variant="outline" data-dismiss>关闭</text-button></div>`;
      document.body.append(drawer);
      drawer.querySelector('[data-dismiss]').onclick=()=>drawer.close();
      drawer.querySelector('[data-lineage]').onclick=()=>{drawer.querySelector('[data-lineage-info]').textContent=`${task?.dataset||'数据集未提供'} → ${task?.name||'训练任务未提供'} → ${row.name}`;};
      drawer.addEventListener('drawer-close',()=>drawer.remove(),{once:true});drawer.show();
    }
    function showCreate(title,value,onSave){show(title,`<form class="model-create"><label>名称<input name="name" required maxlength="120" value="${esc(value)}"></label><p class="model-note">仅创建当前页面演示记录，不提交到后台。</p><button type="submit" class="model-submit">保存</button></form>`);dialog.querySelector('form').onsubmit=e=>{e.preventDefault();const name=new FormData(e.target).get('name').trim();if(!name)return;onSave(name);dialog.close();};}
    function syncSQLLines(){const editor=host.querySelector('#model-sql');if(!editor)return;host.querySelector('[data-sql-lines]').textContent=editor.value.split('\n').map((_,i)=>i+1).join('\n');}
    const sqlEditor=host.querySelector('#model-sql');
    if(sqlEditor){sqlEditor.addEventListener('input',syncSQLLines);sqlEditor.addEventListener('scroll',()=>{host.querySelector('[data-sql-lines]').scrollTop=sqlEditor.scrollTop;});}
    function actionHandler(e){const b=e.target.closest('[data-model-action]');if(!b)return;const action=b.dataset.modelAction;
      if(action==='导入三方数据'){
        show('导入三方数据',`<form class="model-create"><label>任务名称<input name="name" required maxlength="120" autocomplete="off"></label><label>数据集名称<input name="dataset" required maxlength="120" autocomplete="off"></label><label>文件地址<input name="file" required placeholder="tos:// 或 https://" autocomplete="off"></label><p class="model-note">当前为演示页面，仅保存导入记录，不传输文件。</p><button class="model-submit" type="submit">导入</button></form>`);
        dialog.querySelector('form').onsubmit=event=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.target));if(!data.name.trim()||!data.dataset.trim()||!data.file.trim())return;if(!/^(tos|https?):\/\/\S+$/.test(data.file)){event.target.querySelector('[name=file]').setCustomValidity('请输入有效的文件地址');event.target.reportValidity();return;}external.unshift({...data,id:'x'+Date.now(),status:'导入中',creator:'当前用户',created:new Date().toLocaleString('sv-SE').slice(0,16)});filters={};host.querySelector('form').reset();page=1;render();dialog.close();feedback.textContent='已添加演示导入记录';};
        dialog.querySelector('[name=file]').oninput=e=>e.target.setCustomValidity('');return;
      }
      if(action==='重置 SQL'){sqlEditor.value='SELECT * FROM data;';host.querySelector('#model-sql-prompt').value='';host.querySelector('[data-sql-status]').textContent='';sqlRows=null;page=1;syncSQLLines();render();return;}
      if(action==='生成 SQL'){
        const prompt=host.querySelector('#model-sql-prompt').value.trim(),status=host.querySelector('[data-sql-status]');
        const id=prompt.match(/(?:ID|编号)\s*[:：]?\s*(\d+)/i),task=prompt.match(/\bt\d+\b/i);
        let condition=id?"id = '"+id[1]+"'":task?"task = '"+task[0].toLowerCase()+"'":/擦白板/.test(prompt)?"task = 't1'":/整理桌面/.test(prompt)?"task = 't2'":'';
        if(!prompt){status.textContent='请先输入查询需求';return;}
        if(/近|时间|质检|标注/.test(prompt)||!condition&&!/全部|所有/.test(prompt)){status.textContent='当前示例支持按任务或数据 ID 生成查询，请输入任务编号或数据 ID。';return;}
        sqlEditor.value='SELECT * FROM data'+(condition?'\nWHERE '+condition:'')+';';syncSQLLines();status.textContent='已生成查询，可编辑后执行';return;
      }
      if(action==='执行 SQL'){const text=host.querySelector('textarea').value.trim();const match=text.match(/^select\s+\*\s+from\s+data(?:\s+where\s+(task|id)\s*=\s*'([^']*)')?\s*;?$/i);if(!match){host.querySelector('[data-sql-status]').textContent="支持 SELECT * FROM data，可使用 WHERE task = 't1' 或 WHERE id = '120489'。";return;}sqlRows=episodes.filter(row=>!match[1]||row[match[1].toLowerCase()]===match[2]);host.querySelector('[data-sql-status]').textContent='查询完成，共 '+sqlRows.length+' 条';feedback.textContent='';page=1;render();}
      else if(action==='新增训练任务')showCreate(action,'',name=>{config.rows.unshift({id:String(Date.now()),name,description:'新建演示任务',status:'排队中',priority:'中',creator:'当前用户',created:new Date().toLocaleString('sv-SE'),duration:'—',tag:'桌面操作',dataset:'桌面操作数据集'});tab='volcano';host.querySelector('task-status-tabs').setActive(tab,false);render();});
      else if(action==='用结果新建数据集'){if(!matched.length){feedback.textContent='当前结果为空，请先调整筛选条件。';return;}const count=matched.length;showCreate('用结果新建数据集','',name=>{jobs.push({name,count});feedback.textContent=`已创建“${name}”的演示记录，包含 ${count} 条数据。`;});}
      else if(action==='导出结果'){
        const csv=filters.export==='CSV',keys=config.columns.map(c=>c[0]);
        const safeCSV=value=>'"'+String(value??'').replace(/^[=+@-]/,"'$&").replace(/"/g,'""')+'"';
        const text=csv?'\ufeff'+[keys,...matched.map(row=>keys.map(key=>row[key]))].map(row=>row.map(safeCSV).join(',')).join('\r\n'):JSON.stringify(matched,null,2);
        const url=URL.createObjectURL(new Blob([text],{type:csv?'text/csv;charset=utf-8':'application/json'}));const a=document.createElement('a');a.href=url;a.download='model-query-results.'+(csv?'csv':'json');a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
      }
      else if(action==='查看数据集创建进度')show(action,jobs.length?jobs.map(job=>`<p>${esc(job.name)} · ${job.count} 条 · 演示记录已创建</p>`).join(''):'<p>暂无创建记录</p>');
      else if(action==='查看采集任务')location.href='../collection-plans/index.html';
      else if(action==='查看缓存记录')show(action,`<dl class="command-details">${source().map(row=>`<div><dt>${esc(row.name)}</dt><dd>${esc(row.cacher)} · ${esc(row.cached)}</dd></div>`).join('')||'暂无缓存记录'}</dl>`);
      else if(action==='去部署')show('部署 Checkpoint','<p>当前为页面演示，尚未连接部署服务。请先在列表中查看并确认 Checkpoint。</p>');
    }
    host.onclick=actionHandler;actions.onclick=actionHandler;render();
  };
})();
