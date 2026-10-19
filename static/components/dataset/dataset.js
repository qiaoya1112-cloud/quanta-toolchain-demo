(() => {
  const groups=[['预训练',['clean_whiteboard_v3','whiteboard_pretrain_mix','desk_pretrain','plant_pour_pretrain']],['后训练',['tidy_desk_mix_v1','whiteboard_sft','desk_dagger_sft','mix_finetune']],['自定义01',['whiteboard_eval_bench','custom_eval_set']],['自定义02',['ablation_small','smoke_test']]];
  const emit=(el,name,detail)=>el.dispatchEvent(new CustomEvent(name,{bubbles:true,detail}));
  class DatasetCatalog extends HTMLElement{
    connectedCallback(){
      this.innerHTML='<task-page-header title="数据集目录"></task-page-header><div class="dataset-catalog-controls"><task-status-tabs variant="dataset-scope" surface="transparent"></task-status-tabs><search-input placeholder="搜索数据集…"></search-input><form-select aria-label="筛选标签" data-tag><option value="">全部标签</option><option>预训练</option><option>后训练</option><option>自定义</option></form-select></div><resource-list></resource-list>';
      const actions=document.createElement('div');actions.className='task-page-header__actions';
      actions.innerHTML='<text-button class="form-add-action" variant="text" icon="plus" data-create-directory>目录</text-button><text-button class="form-add-action" variant="text" icon="plus" data-create-dataset>数据集</text-button>';
      this.querySelector('task-page-header header').append(actions);
      actions.querySelector('[data-create-directory]').addEventListener('click',()=>emit(this,'directory-create',{}));
      actions.querySelector('[data-create-dataset]').addEventListener('click',()=>emit(this,'dataset-create',{}));
      this.query='';this.selected=groups[0][1][0];this.render();
      this.querySelector('search-input').addEventListener('input',e=>{this.query=e.target.value.toLowerCase();this.render();});
      this.addEventListener('change',()=>this.render());
      this.querySelector('[variant=dataset-scope]').addEventListener('tab-change',e=>{e.stopPropagation();this.render();});
      this.querySelector('resource-list').addEventListener('resource-select',e=>{this.selected=e.detail.value;this.render();emit(this,'dataset-select',{name:this.selected});});
    }
    render(){const mine=this.querySelector('[variant=dataset-scope]').getAttribute('active')==='mine',tag=this.querySelector('[data-tag]').value;
      const list=this.querySelector('resource-list');list.selected=this.selected;list.items=groups.map(([label,names],i)=>({label,children:names.filter(n=>n.toLowerCase().includes(this.query)&&(!mine||i>=2)&&(!tag||label.startsWith(tag))).map(n=>({id:n,label:n,meta:'v3'}))})).filter(g=>g.children.length);}

  }
  class DatasetEpisodes extends HTMLElement{
    connectedCallback(){this.select(0);this.addEventListener('click',e=>{const b=e.target.closest('[data-episode]');if(b){this.select(Number(b.dataset.episode));emit(this,'episode-select',{index:Number(b.dataset.episode)});}});}
    select(index){this.innerHTML='<strong>EPISODES (12)</strong>'+Array.from({length:12},(_,i)=>`<button data-episode="${i}" aria-current="${i===index}">Episode ${i}<small>${[1434,1042,1310][i%3].toLocaleString()} f · #${120489+i*13}</small></button>`).join('');}
  }
  class DatasetTrajectory extends HTMLElement{
    connectedCallback(){this.episode=0;this.parts=new Set(['LeftArm','RightArm']);this.innerHTML='<workbench-media-viewer variant="dataset"></workbench-media-viewer><div class="dataset-toolbar"><div data-parts>'+['LeftArm','Torso','RightArm','Base'].map(n=>`<text-button variant="outline" data-part="${n}">${n}</text-button>`).join('')+'</div><div data-transport><text-button variant="outline" icon="play" icon-only aria-label="播放曲线" title="播放曲线" data-play></text-button><text-button variant="outline" icon="reset" icon-only aria-label="重置" title="重置" data-reset></text-button></div><small class="dataset-legend"><span class="dataset-legend__cmd"></span>CMD<span class="dataset-legend__state"></span>State（示例）</small></div><div class="dataset-charts"></div><input class="dataset-range" type="range" min="0" max="100" value="0" aria-label="轨迹播放进度"><p class="dataset-status" aria-live="polite">示例轨迹 · 0%</p>';
      this.querySelector('[data-parts]').addEventListener('click',e=>{const b=e.target.closest('[data-part]');if(!b)return;const n=b.dataset.part;if(this.parts.has(n))this.parts.delete(n);else this.parts.add(n);this.render();});
      this.querySelector('[data-play]').addEventListener('click',()=>{if(this.timer)this.stop();else{this.querySelector('[data-play]').setAttribute('icon','pause');this.querySelector('[data-play]').button.setAttribute('aria-label','暂停曲线');this.querySelector('[data-play]').button.title='暂停曲线';this.timer=setInterval(()=>{const r=this.querySelector('input');r.value=(Number(r.value)+1)%101;this.progress();},100);}});
      this.querySelector('[data-reset]').addEventListener('click',()=>{this.stop();this.querySelector('input').value=0;this.progress();});this.querySelector('input').addEventListener('input',()=>this.progress());this.render();
    }
    stop(){clearInterval(this.timer);this.timer=null;this.querySelector('[data-play]').setAttribute('icon','play');this.querySelector('[data-play]').button.setAttribute('aria-label','播放曲线');this.querySelector('[data-play]').button.title='播放曲线';}
    disconnectedCallback(){clearInterval(this.timer);}
    progress(){const value=this.querySelector('input').value;this.querySelector('.dataset-status').textContent=`Episode ${this.episode} · 示例轨迹 ${value}%`;this.querySelectorAll('[data-cursor]').forEach(c=>{c.setAttribute('x1',40+Number(value)*4.5);c.setAttribute('x2',40+Number(value)*4.5);});}
    render(){this.querySelectorAll('[data-part]').forEach(b=>b.setAttribute('variant',this.parts.has(b.dataset.part)?'primary':'outline'));this.querySelector('.dataset-charts').innerHTML=[...this.parts].map((part,j)=>`<section class="dataset-chart"><h3>${part}</h3><svg viewBox="0 0 510 300" role="img" aria-label="${part} XYZ 示例轨迹">${['X','Y','Z'].map((axis,k)=>`<path d="M40 ${k*100+90}H500" stroke="#e7edf1"/><text x="8" y="${k*100+50}">${axis}</text>${['#38a0c0','#82c657'].map((color,n)=>`<polyline fill="none" stroke="${color}" stroke-width="1.5" points="${Array.from({length:61},(_,i)=>`${40+i*7.5},${k*100+48+27*Math.sin(i/6+j+k+this.episode*.2+n*.5)}`).join(' ')}"/>`).join('')}`).join('')}<line data-cursor x1="40" x2="40" y1="0" y2="300" stroke="#9aaab5" stroke-dasharray="3 3"/></svg></section>`).join('')||'<p class="dataset-empty">请选择要查看的部位</p>';this.progress();}
  }
  function setupDatasetDetails(browser){
    const versions=[['v4','新增 dagger 数据（草稿）',4,'joanna.qiao','2026-05-28 16:40','待发布'],['v3','扩充数据',3,'joanna.qiao','2026-05-28 16:40','生效中'],['v2','增补采集 + 调整配方',2,'Min Chen','2026-05-13 10:00','已归档'],['v1','初版采集',1,'Wei Zhang','2026-05-12 10:00','已归档']];
    const low=[['接近/对准目标',17256,48],['抓取物体',5968,24],['移动/搬运',5424,24],['放置/对位',4336,24],['擦拭/操作',13425,48],['复位/收回',5901,32]];
    let dimension='high',level='二级',info='summary';
    const analysis=browser.querySelector('[data-view="analysis"]'),versionPanel=browser.querySelector('[data-view="versions"]'),infoPanel=browser.querySelector('[data-view="info"]');
    function metadata(){return {name:browser.name,identifier:'test1',format:'LeRobot',robot:'moz1',episodes:48,frames:52310,duration_minutes:29.1,creator:'joanna.qiao',created_at:'2026-05-28 16:40',version:browser.querySelector('[data-version]').value,tags:['动作标签 > 清洁类 > 擦拭','场景标签 > 作业区域 > 白板区','质量标签 > 数据质量 > 高质量'],tos:'tos://embodied/datasets/'+browser.name+'/',demo:true};}
    function drawAnalysis(){
      const rows=dimension==='high'?[['Clean the whiteboard',52310,48]]:low;
      analysis.innerHTML='<p class="dataset-note">数据集共 48 episode · 1 highlevel · 6 lowlevel（按去重计数）</p><task-status-tabs variant="dataset-dimension" active="'+dimension+'"></task-status-tabs><div class="dataset-section-title"><h3>Prompt 构成</h3><span>按 '+(dimension==='high'?'highlevel 任务':'lowlevel 子动作')+' prompt 的帧数占比</span></div><div class="dataset-bars">'+rows.map(([name,frames,count])=>{const percent=frames/52310*100;return '<div class="dataset-bar-row"><span>'+name+'</span><div class="dataset-bar-track"><span style="width:'+percent+'%">'+Math.round(percent)+'%</span></div><span>'+frames.toLocaleString()+' f</span><span>'+count+' 条</span></div>';}).join('')+'</div><div class="dataset-section-title"><h3>标签构成</h3><span>各维度内标签的帧数占比</span><form-select label="展示层级" value="'+level+'" data-level><option>一级</option><option>二级</option><option>三级</option></form-select></div><div class="dataset-distributions">'+[['场景',['场景标签','作业区域','白板区']],['技能',['动作标签','清洁类','擦拭']],['质量',['质量标签','数据质量','高质量']]].map(([name,labels])=>{const label=labels[['一级','二级','三级'].indexOf(level)];return '<article><h3>'+name+'</h3><div class="dataset-pie" role="img" aria-label="'+label+' 100%"><span>'+label+'</span></div><div class="dataset-pie-legend"><span>'+label+'</span><span>100%</span></div></article>';}).join('')+'</div>';
      analysis.querySelector('task-status-tabs').addEventListener('tab-change',e=>{e.stopPropagation();dimension=e.detail.value;drawAnalysis();});
      analysis.querySelector('[data-level]').addEventListener('value-change',e=>{level=e.detail.value;drawAnalysis();});
    }
    function drawVersions(){
      versionPanel.innerHTML='<div class="task-data-table dataset-version-table"><table><thead><tr>'+['版本','说明','数据数','创建人','创建时间','状态','操作'].map(t=>'<th>'+t+'</th>').join('')+'</tr></thead><tbody>'+versions.map(v=>'<tr><td>'+v[0]+'</td><td>'+v[1]+'</td><td>'+v[2]+'</td><td>'+v[3]+'</td><td>'+v[4]+'</td><td><span class="table-outline-tag table-outline-tag--'+(v[5]==='生效中'?'active':v[5]==='待发布'?'warning':'neutral')+'">'+v[5]+'</span></td><td>'+(v[5]==='生效中'?'—':'<button data-version-action="'+v[0]+'">'+(v[5]==='待发布'?'发布':'回退')+'</button>')+'</td></tr>').join('')+'</tbody></table></div><p class="dataset-note">修改配方或处理数据会生成新版本；被训练引用的版本保持不变，保证实验可复现。</p>';
      versionPanel.querySelectorAll('[data-version-action]').forEach(b=>b.onclick=()=>{versions.forEach(v=>{if(v[0]===b.dataset.versionAction)v[5]='生效中';else if(v[5]==='生效中')v[5]='已归档';});const selector=browser.querySelector('[data-version]');selector.value=b.dataset.versionAction;drawVersions();drawInfo();browser.message('当前演示生效版本已切换为 '+b.dataset.versionAction);});
    }
    function drawInfo(){
      const data=metadata();
      infoPanel.innerHTML='<task-status-tabs variant="dataset-information" active="'+info+'"></task-status-tabs><div data-info-content></div>';
      const target=infoPanel.querySelector('[data-info-content]');
      if(info==='full'){const pre=document.createElement('pre');pre.className='dataset-json';pre.textContent=JSON.stringify(data,null,2);target.append(pre);}
      else {
       const table=document.createElement('table');table.className='dataset-metadata';
       [['名称',data.name],['标识',data.identifier],['数据格式',data.format],['标签',data.tags],['本体',data.robot],['规模','48 episodes · 52,310 frames · 29.1 min'],['创建人',data.creator],['创建时间',data.created_at],['TOS',data.tos]].forEach(([label,value])=>{const tr=table.insertRow(),th=document.createElement('th');th.scope='row';th.textContent=label;tr.append(th);const td=tr.insertCell();if(Array.isArray(value)){value.forEach(t=>{const tag=document.createElement('span');tag.className='table-outline-tag table-outline-tag--blue';tag.textContent=t;td.append(tag);});}else td.textContent=value;});
       target.append(table);
      }
      infoPanel.querySelector('task-status-tabs').addEventListener('tab-change',e=>{e.stopPropagation();info=e.detail.value;drawInfo();});
    }
    const selector=browser.querySelector('[data-version]'),option=document.createElement('option');option.value='v4';option.textContent='v4';selector.control.prepend(option);selector.syncSelect?.();
    selector.addEventListener('value-change',drawInfo);
    browser.addEventListener('dataset-select',drawInfo);
    browser.querySelector('.dataset-heading task-page-header .task-page-header__description').textContent='48 episodes · 52,310 frames · LeRobot';
    browser.querySelector('[data-view="preview"]>.dataset-note').textContent='展示 12 个示例 episode，可在左侧逐条预览。';
    drawAnalysis();drawVersions();drawInfo();
  }

  class DatasetBrowser extends HTMLElement{
    connectedCallback(){this.name='clean_whiteboard_v3';this.innerHTML='<dataset-catalog></dataset-catalog><section class="dataset-main" aria-label="数据集详情"><div class="dataset-heading"><task-page-header title="clean_whiteboard_v3" description="12 episodes · LeRobot · 示例数据"></task-page-header><form-select aria-label="数据集版本" data-version><option>v3</option><option>v2</option><option>v1</option></form-select><text-button variant="outline" data-lineage>查看血缘</text-button><text-button variant="outline" data-export>导出数据</text-button></div><task-status-tabs surface="transparent" variant="dataset"></task-status-tabs><div class="dataset-body"><section data-view="preview"><p class="dataset-note">共 12 个示例 episode，每个 episode 对应一条原始 recording，可在左侧逐条预览。</p><div class="dataset-preview"><dataset-episodes></dataset-episodes><div class="dataset-detail"><task-status-tabs surface="transparent" variant="episode"></task-status-tabs><dataset-trajectory></dataset-trajectory><div data-episode-extra hidden></div></div></div></section><section data-view="analysis" hidden><h3>数据构成</h3><div class="dataset-analysis"><article>Episodes<strong>12</strong></article><article>相机视角<strong>3</strong></article><article>格式<strong>LeRobot</strong></article></div></section><section data-view="versions" hidden><h3>版本</h3><p>v3 · 当前示例版本</p><p>v2 · 历史示例版本</p><p>v1 · 初始示例版本</p></section><section data-view="info" hidden><h3>基本信息</h3><dl class="dataset-info"><dt>名称</dt><dd data-name></dd><dt>格式</dt><dd>LeRobot</dd><dt>来源</dt><dd>本地演示数据，未连接数据服务</dd></dl></section><p class="dataset-status" data-message role="status"></p></div></section>';
      const header=this.querySelector('.dataset-heading task-page-header header');
      const actions=document.createElement('div');actions.className='task-page-header__actions';
      actions.append(this.querySelector('[data-lineage]'),this.querySelector('[data-export]'));
      header.append(actions);
      header.querySelector('.task-page-header__title-row').append(this.querySelector('[data-version]'));
      this.querySelector('[data-name]').textContent=this.name;
      this.addEventListener('tab-change',e=>{if(e.target.getAttribute('variant')==='dataset'){this.querySelectorAll('[data-view]').forEach(v=>v.hidden=v.dataset.view!==e.detail.value);}else if(e.target.getAttribute('variant')==='episode'){const trajectory=e.detail.value==='trajectory';this.querySelector('dataset-trajectory').hidden=!trajectory;this.querySelector('dataset-trajectory').stop();const extra=this.querySelector('[data-episode-extra]');extra.hidden=trajectory;extra.className='dataset-empty';extra.textContent=e.detail.value==='annotation'?'当前示例暂无标注信息':'暂无真实轨迹数据可供分析';}});
      this.addEventListener('dataset-select',e=>{this.name=e.detail.name;this.querySelector('.dataset-heading task-page-header h1').textContent=this.name;this.querySelector('[data-name]')&&(this.querySelector('[data-name]').textContent=this.name);this.querySelector('dataset-episodes').select(0);this.updateEpisode(0);});
      this.addEventListener('episode-select',e=>this.updateEpisode(e.detail.index));
      this.addEventListener('directory-create',()=>this.message('当前为组件演示页；新建目录需接入数据服务。'));
      this.addEventListener('dataset-create',()=>this.message('当前为组件演示页；新建数据集需接入数据服务。'));
      this.querySelector('[data-version]').addEventListener('change',()=>{this.updateEpisode(0);this.querySelector('dataset-episodes').select(0);this.message('已切换版本；当前展示该版本的示例数据。');});
      this.querySelector('[data-lineage]').addEventListener('click',()=>this.message('示例血缘：原始 recording → 预训练目录 → '+this.name));
      this.querySelector('[data-export]').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify({name:this.name,version:this.querySelector('[data-version]').value,demo:true,episodes:48,frames:52310,previewEpisodes:12},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=this.name+'-demo.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);this.message('已导出演示元数据 JSON，不包含视频。');});
      setupDatasetDetails(this);
    }
    message(text){this.querySelector('[data-message]').textContent=text;}
    updateEpisode(index){const t=this.querySelector('dataset-trajectory');t.stop();t.episode=index;t.querySelector('input').value=0;t.render();}
  }
  customElements.define('dataset-catalog',DatasetCatalog);customElements.define('dataset-episodes',DatasetEpisodes);customElements.define('dataset-trajectory',DatasetTrajectory);customElements.define('dataset-browser',DatasetBrowser);
})();
