(() => {
  const library=document.querySelector('process-node-library[variant="workflow"]');
  if(!library)return;
  const section=document.createElement('section');section.className='component-gallery__group';
  section.innerHTML='<h2>节点样式 · 节点库与拖入画布后</h2><div class="node-table-scroll"><table class="node-state-table"><thead><tr><th scope="col">节点库样式</th><th scope="col">画布节点 · 默认</th><th scope="col">画布节点 · 已填写</th><th scope="col">面板属性</th></tr></thead><tbody></tbody></table></div>';
  const gallery=section.querySelector('tbody');
  library.querySelectorAll('.palette-item').forEach(item=>{
    if(item.dataset.nodeType==='Call Flow')return;
    const row=document.createElement('tr');
    const libraryCell=document.createElement('td');libraryCell.append(item.cloneNode(true));row.append(libraryCell);
    const canvas=document.createElement('div');canvas.className='node-state-canvas';
    const node=document.createElement('div');node.className='graph-node';
    const icon=item.querySelector('.node-icon').cloneNode(true);icon.classList.replace('node-icon','mini');
    const title=document.createElement('div');title.className='graph-title';title.textContent=item.textContent.trim();
    node.append(icon,title);
    const ports='<span class="port" style="left:-4px;top:calc(50% - 4px)"></span><span class="port" style="right:-4px;top:calc(50% - 4px)"></span>';
    node.insertAdjacentHTML('beforeend',ports);
    if(item.dataset.nodeType==='Start'){
      node.classList.add('start-main');const image=icon.querySelector('img');image.style.width='23px';image.style.height='23px';icon.replaceWith(image);
      const text=document.createElement('div');text.className='node-text';title.replaceWith(text);title.textContent='start';text.append(title);node.querySelector('.port').remove();
    }
    if(item.dataset.nodeType==='Condition'){
      node.classList.add('condition-cases');node.replaceChildren();
      const header=document.createElement('div');header.className='condition-case-header';header.append(icon,title);node.append(header);
      node.insertAdjacentHTML('beforeend','<div class="branch-row" style="height:72px"><div class="condition-case-label"><span>CASE 1</span><span>IF</span></div><div class="condition-expression"><span>条件未设置</span></div></div><div class="branch-row condition-fallback" style="height:40px">ELSE</div><span class="port" style="left:-4px;top:88.5px"></span><span class="port" style="right:-4px;top:88.5px"></span><span class="port" style="right:-4px;top:144.5px"></span>');
    }
    if(item.dataset.nodeType==='Variable Assignment'){
      node.classList.add('variable-default');
      const text=document.createElement('div');text.className='node-text';title.replaceWith(text);text.append(title);
      text.insertAdjacentHTML('beforeend','<div class="variable-empty">未选择变量</div>');
    }
    window.applyProcessNodeDefaultSummary(node,item.dataset.nodeType,true);
    canvas.append(node);
    const canvasCell=document.createElement('td');canvasCell.append(canvas);row.append(canvasCell);
    const examples={Start:['京东单品拣放开始','流程入口'],End:['京东单品拣放结束','流程结束'],Condition:['检查是否还有任务','当前 Loop 轮次 <= current_order.task_count'],Loop:['订单循环','订单任务循环'],'Variable Assignment':['设置当前任务','1 项变量赋值'],'API Request':['获取京东订单','GET · 获取京东订单'],'Human Interrupt':['抓取人工接管','120s · 抓取失败人工介入'],'Pose Set':['准备拣选位姿','工作点位 · VRMOV'],Navigation:['导航至拣选工位','目标点位 · PICK_STATION'],'Omini Model':['执行商品抓取','1 个输入 · 30s 超时']};
    const filled=node.cloneNode(true),example=examples[item.dataset.nodeType];
    if(example){
      if(item.dataset.nodeType!=='Variable Assignment'){filled.classList.remove('variable-default');filled.querySelector('.variable-empty')?.remove();}
      const heading=filled.querySelector('.graph-title');heading.textContent=example[0];heading.title=example[0];
      if(item.dataset.nodeType==='Variable Assignment'){
        filled.querySelector('.variable-empty').textContent='1 项变量赋值';
      }else if(filled.classList.contains('condition-cases')){
        heading.textContent='检查任务执行状态';heading.title='检查任务执行状态';
        filled.querySelectorAll('.branch-row,.port').forEach(element=>element.remove());
        const branches=[
          ['IF','AND',['current_task.status == success','current_order.remaining_count > 0']],
          ['ELIF','OR',['current_task.status == timeout','current_task.status == cancelled','current_task.status == failed']],
          ['ELIF','AND',['current_task.status == success','current_order.remaining_count == 0']]
        ];
        let offset=56;
        const addPort=(side,y)=>{const port=document.createElement('span');port.className='port';port.style.cssText=`${side}:-4px;top:${y-4}px`;filled.append(port);};
        branches.forEach(([operator,join,expressions],index)=>{
          const branch=document.createElement('div');branch.className='branch-row';
          const height=42+expressions.length*32;branch.style.height=`${height}px`;
          branch.innerHTML=`<div class="condition-case-label"><span>条件 ${index+1}</span><span>${operator}</span></div>`;
          expressions.forEach((value,i)=>{const chip=document.createElement('div');chip.className='condition-expression';const text=document.createElement('span');text.textContent=value;chip.title=value;chip.append(text);if(i<expressions.length-1){const logic=document.createElement('b');logic.textContent=join;chip.append(logic);}branch.append(chip);});
          filled.append(branch);addPort('right',offset+height/2);if(index===0)addPort('left',offset+height/2);offset+=height;
        });
        ['ELSE','发生错误'].forEach((label,index)=>{const branch=document.createElement('div');branch.className='branch-row condition-fallback'+(index?' condition-error':'');branch.style.height='40px';branch.textContent=label;filled.append(branch);addPort('right',offset+20);offset+=40;});
        filled.style.height=`${offset}px`;
      }else{
        let text=filled.querySelector('.node-text');
        if(!text){text=document.createElement('div');text.className='node-text';heading.replaceWith(text);text.append(heading);}
        let subtitle=text.querySelector('.graph-sub');if(!subtitle){subtitle=document.createElement('div');subtitle.className='graph-sub';text.append(subtitle);}subtitle.textContent=example[1];
      }
    }
    const filledCell=document.createElement('td'),filledCanvas=document.createElement('div');filledCanvas.className='node-state-canvas';if(example)filledCanvas.append(filled);else{filledCanvas.textContent='本期流程未使用该节点';filledCanvas.classList.add('node-properties-empty');}filledCell.append(filledCanvas);row.append(filledCell);
    const properties=document.createElement('td');
    const panelVariant={Start:'start',End:'end',Loop:'workflow-loop','Variable Assignment':'workflow-variable',Navigation:'workflow-navigation','Omini Model':'workflow-automation','Omni Model':'workflow-automation','Pose Set':'workflow-pose',Condition:'workflow-condition','Human Interrupt':'workflow-human','API Request':'api-request'}[item.dataset.nodeType];
    let panel=panelVariant?document.querySelector(`process-node-properties[variant="${panelVariant}"]`):null;
    if(['api-request','end','workflow-variable','workflow-condition','workflow-human','workflow-loop','workflow-pose','workflow-navigation','workflow-automation'].includes(panelVariant)&&!panel){panel=document.createElement('process-node-properties');panel.setAttribute('variant',panelVariant);}
    if(panel){const oldSection=panel.closest('section.component-gallery__group');properties.append(panel);oldSection?.remove();}
    else{properties.textContent='暂无';properties.className='node-properties-empty';}
    row.append(properties);gallery.append(row);
  });
  library.closest('section').after(section);
  const librarySection=library.closest('section');
  const treeSection=document.createElement('section');treeSection.className='component-gallery__group';treeSection.id='process-flow-tree';
  treeSection.innerHTML='<h2>流程树</h2><div class="library-variants-row"><div class="library-variant"><h3>多流程</h3><process-flow-tree></process-flow-tree></div><div class="library-variant"><h3>单流程</h3><process-flow-tree variant="single"></process-flow-tree></div></div>';
  librarySection.before(treeSection);
  const variants=document.createElement('div');variants.className='library-variants-row';
  [...librarySection.querySelectorAll(':scope > h3')].forEach(heading=>{
    const preview=heading.nextElementSibling;
    const variant=document.createElement('div');variant.className='library-variant';
    variant.append(heading,preview);variants.append(variant);
  });
  librarySection.append(variants);
  const legacyColors=document.createElement('div');legacyColors.className='legacy-node-colors';
  legacyColors.innerHTML='<h3>原节点配色 · 保留备用</h3><div class="legacy-node-colors__items">'+[
    ['青绿色','green','start','#0E9488','#E0F3F0'],['灰色','gray','end','#60788A','#EEF3F6'],
    ['蓝色','blue','condition-fix','#3B92C9','#E6F1F9'],['薄荷绿','mint','loop','#1BB985','#E5F4EC'],
    ['黄色','yellow','variable-yellow','#D99A00','#FAF2DC'],['紫色','purple','api','#6C63E6','#ECECF8'],
    ['粉紫色','pink2','human','#C058A2','#F5EAF3'],['粉色','pink','wait','#D75D9F','#F7EAF1']
  ].map(([label,color,icon,foreground,background])=>`<div class="legacy-node-colors__item"><span class="node-icon ${color}"><img src="../../pages/process-editor/assets/${icon}.svg" alt=""></span><div><strong>${label}</strong><small>图标 ${foreground}<br>底色 ${background}</small></div></div>`).join('')+'</div>';
  librarySection.append(legacyColors);
  variants.querySelectorAll('.library-variant').forEach(item=>{
    const component=item.querySelector('process-node-library');
    if(component&&!component.hasAttribute('no-flow')&&component.getAttribute('variant')!=='workflow')item.remove();
  });
  librarySection.querySelectorAll('process-node-library').forEach(component=>{
    const tree=component.querySelector('.flow-list');if(!tree)return;
    tree.querySelector('.library-subflows')?.remove();
    tree.querySelector('.flow-tree-toggle')?.remove();
    tree.querySelector('.flow-main-tag')?.remove();
    const count=tree.querySelector('.library-heading-count');if(count)count.textContent='1';
    const name=tree.querySelector('.flow-name');
    if(name){const variant=component.getAttribute('variant');name.textContent=variant==='basic'?'端到端切分标注':variant==='workflow'?'京东单 SKU 拣放':'通用工作流';name.title=name.textContent;}
  });
  const names={...window.processNodeNames,'CASE 1':'条件 1'};
  section.querySelectorAll('.palette-item,.node-state-canvas').forEach(container=>{
    const walker=document.createTreeWalker(container,NodeFilter.SHOW_TEXT);
    let text;
    while((text=walker.nextNode())){const name=text.textContent.trim();if(names[name])text.textContent=text.textContent.replace(name,names[name]);}
  });
  const info=document.querySelector('#process-node-info');
  if(info){
    const spacingSpec=document.createElement('section');
    spacingSpec.className='node-spacing-spec';
    spacingSpec.id='node-spacing-spec';
    spacingSpec.innerHTML=`<h3>节点信息 · 间距规范</h3><p>建议值，待确认。按内容层级区分间距，不将所有空隙设为同一数值；以下单位均为 CSS px。</p><div class="node-spacing-spec__grid"><article><h4>01 小标题 → 信息 · 8px</h4><p>字段标签底部到输入框、下拉框或信息内容顶部。标签和内容一起构成一个信息组。</p><div class="node-spacing-spec__field"><span>工作台</span><div class="node-spacing-spec__gap" style="height:var(--node-space-label)"></div><div class="node-spacing-spec__control">语义标注工作台 v1.0</div></div><code>--node-space-label: 8px</code></article><article><h4>02 信息组 → 信息组 · 12px</h4><p>上一组内容底部到下一组标签顶部，例如“节点名称”与“下游节点”；不是两组标签之间的距离。</p><div class="node-spacing-spec__field"><span>节点名称</span><div class="node-spacing-spec__control">HUMAN_INTERRUPT</div></div><div class="node-spacing-spec__gap" style="height:var(--node-space-field)"></div><div class="node-spacing-spec__field"><span>下游节点</span><div class="node-spacing-spec__control">输入下游节点名称</div></div><code>--node-space-field: 12px</code></article><article><h4>03 组合组 → 组合组 · 18px</h4><p>上一模块整体底部到下一模块标题顶部，例如“输入配置”与“后续节点”。标题、说明及内部信息组属于同一组合组。</p><div class="node-spacing-spec__module"><strong>输入配置</strong><span>循环模式、重复次数</span></div><div class="node-spacing-spec__gap" style="height:var(--node-space-section)"></div><div class="node-spacing-spec__module"><strong>后续节点</strong><span>说明、节点卡片与添加按钮</span></div><code>--node-space-section: 18px</code></article></div><p>实现规则：由共同父容器的 gap 控制，同一间隙不叠加子元素 margin 或额外 padding。卡片内边距、同行列距、说明文字及添加按钮间距另行定义，不计入这三类。</p>`;
    info.querySelector('h2').after(spacingSpec);
    const addSpacing=document.createElement('article');
    addSpacing.innerHTML='<h4>04 信息 → 添加按钮 · 4px</h4><p>最后一条信息或条件卡片底部，到添加按钮点击区域顶部。按钮内部保留点击留白，不按加号图形边缘测量。</p><div class="node-spacing-spec__control">sku_mode　 single</div><div class="node-spacing-spec__gap" style="height:4px"></div><text-button variant="text" icon="plus">添加查询参数</text-button><code>--node-space-add: 4px</code>';
    spacingSpec.querySelector('.node-spacing-spec__grid').append(addSpacing);
    const titleSpacing=document.createElement('article');
    titleSpacing.innerHTML='<h4>05 模块标题 → 信息 · 8px</h4><p>带色条的模块标题底部，到第一条信息顶部。有字段标签时测量到标签，无标签时测量到输入框或信息行；例如“请求 → 请求方法”和“请求头 → Accept”。与字段小标题到控件的间距独立管理。</p><div class="node-spacing-spec__module" style="gap:0"><strong>请求头</strong><div class="node-spacing-spec__gap" style="height:8px"></div><div class="node-spacing-spec__control">Accept　 application/json</div></div><code>--node-space-title: 8px</code>';
    spacingSpec.querySelector('.node-spacing-spec__grid').append(titleSpacing);
    const cardSpacing=document.createElement('article');
    cardSpacing.innerHTML='<h4>06 灰底参数卡片 · 内边距 8px</h4><p>灰底边框内侧到内容的上、下、左、右距离均为 8px，适用于人工、位姿、循环及超时重试参数卡片。公用外框、卡片之间及字段之间的间距保持各自规范，不叠加到卡片内边距。</p><div class="workflow-human-field"><form-input label="超时时间（秒）" value="120"></form-input></div><code>--node-card-padding: 8px</code>';
    spacingSpec.querySelector('.node-spacing-spec__grid').append(cardSpacing);
    const feedbackSpacing=document.createElement('article');
    feedbackSpacing.innerHTML='<h4>07 内容 → 校验提示 · 8px</h4><p>内容或参数卡片底部到校验提示顶部为 8px，两者属于同一组合组。提示到下一个独立模块保持 18px；不改变提示框自身内边距。</p><form-input label="地图文件路径" placeholder="/data/maps/map.yaml"></form-input><div class="node-spacing-spec__gap" style="height:8px"></div><div class="workflow-navigation-warning">地图文件路径为必填项。</div><code>--node-space-feedback: 8px</code>';
    spacingSpec.querySelector('.node-spacing-spec__grid').append(feedbackSpacing);
    const descriptionSpacing=document.createElement('article');
    descriptionSpacing.innerHTML='<h4>08 副文本 → 信息 · 8px</h4><p>从副文本最后一行的行盒底部，到下一块信息的外边界顶部，统一为 8px。适用于后续节点卡片、无出口空状态、自定义输入及参数配置；下方带字段标签时测量到标签顶部，不是输入框顶部。</p><p>引用 --node-space-description，由共同父容器的 gap 控制，不叠加 margin、padding 或空容器。标题到副文本仍为 8px；信息组之间为 12px；独立模块之间为 18px。没有副文本时沿用标题到信息规范。</p><code>--node-space-description: 8px</code>';
    spacingSpec.querySelector('.node-spacing-spec__grid').append(descriptionSpacing);
    // Examples use the same form controls as the properties panels.
    spacingSpec.querySelectorAll('.node-spacing-spec__control').forEach(placeholder=>{
      const value=placeholder.textContent.trim();
      if(value.startsWith('sku_mode')||value.startsWith('Accept')){
        const row=document.createElement('div');row.className='api-pair node-spacing-spec__pair';
        const values=value.startsWith('sku_mode')?['sku_mode','single']:['Accept','application/json'];
        values.forEach((text,index)=>{const input=document.createElement('form-input');input.setAttribute('value',text);input.setAttribute('aria-label',index?'值':'名称');row.append(input);});
        placeholder.replaceWith(row);
      }else{
        const control=document.createElement(value.startsWith('语义标注')?'form-select':'form-input');
        if(control.localName==='form-select'){const option=document.createElement('option');option.textContent=value;control.append(option);control.setAttribute('aria-label','工作台');}
        else{control.setAttribute(value==='输入下游节点名称'?'placeholder':'value',value);control.setAttribute('aria-label',value==='输入下游节点名称'?'下游节点':'节点名称');}
        placeholder.replaceWith(control);
      }
    });
    const forms=document.querySelector('.form-control-samples');
    if(forms){
      const previousGroup=forms.closest('.component-gallery__group');
      const heading=document.createElement('h3');heading.textContent='基础表单组件';
      info.append(heading,forms);
      if(previousGroup&&previousGroup!==info)previousGroup.remove();
    }
    const samples=document.createElement('div');samples.className='panel-component-samples';
    const parts=[
      ['可编辑面板头部','start','.interrupt-heading'],
      ['自定义输入 · 添加与删除','workflow-human','.api-custom-inputs'],
      ['变量赋值 · 赋值规则','workflow-variable','workflow-field-collection[kind="assignments"]'],
      ['变量赋值 · 输出字段','workflow-variable','workflow-field-collection[kind="outputs"]'],
      ['参数卡片 · 超时与描述','workflow-human','.api-properties__body > section:nth-of-type(2)'],
      ['条件分支 · 条件与分支操作','workflow-condition','[data-workflow-cases]'],
      ['循环模式与取值','workflow-loop','.api-properties__body > section:nth-of-type(2)'],
      ['参数卡片 · 整行与双列','workflow-pose','.workflow-pose-fields'],
      ['导航配置','workflow-navigation','.api-properties__body > section:first-child'],
      ['超时与重试','workflow-navigation','.workflow-human-field'],
      ['自动化输入配置','workflow-automation','.api-properties__body > section:nth-of-type(2)'],
      ['执行限制','workflow-automation','.api-properties__body > section:nth-of-type(3)'],
      ['中断控制','workflow-automation','section:has(>form-input[name="monitor"])'],
      ['必填提示','workflow-navigation','.workflow-navigation-warning'],
      ['输出变量 · 已配置','api-request','workflow-output-variables'],
      ['输出变量 · 空状态','workflow-human','workflow-output-variables'],
      ['后续节点 · 标题与计数','start','.start-properties__body'],
      ['后续节点 · 未连接','workflow-navigation','.api-properties__body > section:last-child'],
      ['后续节点 · 无出口','end','.start-properties__body']
    ];
    for(const [label,variant,selector] of parts){const sample=document.createElement('div');sample.className='panel-component-sample';const title=document.createElement('h3');title.textContent=label;const part=document.createElement('workflow-panel-part');part.setAttribute('variant',variant);part.setAttribute('selector',selector);sample.append(title,part);samples.append(sample);}
    info.append(samples);
    const headerExample=samples.querySelector('workflow-panel-part[selector=".interrupt-heading"]');
    if(headerExample){
      const emptyHeader=document.createElement('workflow-panel-part');
      emptyHeader.setAttribute('variant','start');emptyHeader.setAttribute('selector','.interrupt-heading');
      emptyHeader.style.marginTop='12px';headerExample.after(emptyHeader);
      const description=emptyHeader.querySelector('[data-header-field="description"]');
      if(description)description.textContent='';
    }
    const parameterExample=samples.querySelector('workflow-panel-part[selector=".workflow-pose-fields"]');
    if(parameterExample){
      parameterExample.classList.add('parameter-layout-example');
      parameterExample.querySelectorAll('.workflow-pose-fields>.workflow-human-field').forEach(card=>{
        if(!['workpoint_name','jog_vel','jog_acc'].includes(card.querySelector('form-input')?.getAttribute('name')))card.remove();
      });
    }
    const conditionGroup=document.createElement('section');conditionGroup.className='node-condition-group';
    const conditionTitle=document.createElement('h3');conditionTitle.textContent='条件类组件';
    const conditionGrid=document.createElement('div');conditionGrid.className='node-condition-group__grid';
    const branchSample=samples.querySelector('workflow-panel-part[variant="workflow-condition"]')?.closest('.panel-component-sample');
    if(branchSample)conditionGrid.append(branchSample);
    info.querySelectorAll('.form-control-sample').forEach(sample=>{if(sample.querySelector('form-condition-group'))conditionGrid.append(sample);});
    conditionGroup.append(conditionTitle,conditionGrid);samples.before(conditionGroup);
    // Organize existing live examples without cloning their controls or handlers.
    const atoms=document.createElement('section');atoms.className='node-component-tier';atoms.id='node-atomic-components';
    atoms.innerHTML='<h3>原子级组件</h3><p>不依赖节点业务的基础控件与通用反馈，可独立复用。</p>';
    const business=document.createElement('section');business.className='node-component-tier';business.id='node-business-components';
    business.innerHTML='<h3>业务级组件</h3><p>由原子控件组合，承载节点配置、条件操作和流程关系。</p>';
    if(forms){
      const oldHeading=forms.previousElementSibling;
      if(oldHeading?.tagName==='H3'&&oldHeading.textContent==='基础表单组件')oldHeading.remove();
      const addSample=document.createElement('div');addSample.className='form-control-sample';
      addSample.innerHTML='<h3>添加</h3><text-button variant="text" icon="plus" class="form-add-action">添加参数</text-button><text-button variant="text" icon="plus" class="form-add-action" disabled>添加参数</text-button><small>字号 12px，文字行高 12px，点击区域高 28px。信息底部到点击区域顶部 4px，内部保留点击留白。</small>';
      const deleteSample=document.createElement('div');deleteSample.className='form-control-sample';
      deleteSample.innerHTML='<h3>删除</h3><text-button variant="text" icon="delete" icon-only class="form-delete-action" aria-label="删除参数" title="删除参数"></text-button><text-button variant="text" icon="delete" icon-only class="form-delete-action" aria-label="删除参数（禁用）" disabled></text-button><small>图标 16px，点击区域 24 × 24px。删除单行时与输入框居中对齐；删除整卡时放在卡片右侧居中。</small>';
      const searchSample=document.createElement('div');searchSample.className='form-control-sample';
      searchSample.innerHTML='<h3>搜索框</h3><search-input placeholder="搜索并聚焦 Flow"></search-input>';
      forms.append(searchSample,addSample,deleteSample);
      atoms.append(forms);
    }
    const feedback=samples.querySelector('workflow-panel-part[selector=".workflow-navigation-warning"]')?.closest('.panel-component-sample');
    if(feedback){
      const atomicSamples=document.createElement('div');atomicSamples.className='panel-component-samples';
      feedback.querySelector('h3').textContent='警告提示 · 必填';atomicSamples.append(feedback);
      [['info','信息提示','配置完成后，请保存当前流程。'],['success','成功提示','参数校验通过，可以继续配置。'],['error','错误提示','参数格式有误，请检查后重试。']].forEach(([tone,title,message])=>{
        const sample=document.createElement('div');sample.className='panel-component-sample';
        sample.innerHTML=`<h3>${title}</h3><div class="form-control-sample"><div class="form-feedback form-feedback--${tone}" role="${tone==='error'?'alert':'status'}">${message}</div></div>`;
        atomicSamples.append(sample);
      });
      atoms.append(atomicSamples);
    }
    const basics=info.querySelector('.node-info-variants');
    if(basics){const heading=document.createElement('h4');heading.textContent='节点基础信息';business.append(heading,basics);}
    business.append(samples,conditionGroup);
    info.append(atoms,spacingSpec,business);
    if(location.hash==='#node-spacing-spec')window.addEventListener('load',()=>spacingSpec.scrollIntoView({block:'start'}),{once:true});
    // Gallery labels sit outside preview frames; component-owned headings stay inside.
    info.querySelectorAll('.form-control-sample').forEach(preview=>{
      const title=preview.querySelector(':scope > h3');
      if(!title)return;
      const sample=document.createElement('div');sample.className='panel-component-sample';
      preview.before(sample);sample.append(title,preview);
    });
  }
  section.querySelector('h2').textContent='京东sku';
  const standard=document.createElement('section');standard.className='component-gallery__group';
  standard.innerHTML='<h2>端到端切分标注</h2><div class="node-table-scroll"><table class="node-state-table"><thead>'+section.querySelector('thead').innerHTML+'</thead><tbody></tbody></table></div>';
  const types={'开始节点':'Start','人工节点':'Human Interrupt','自动化节点':'Omini Model','条件节点':'Condition','结束节点':'End'};
  const examples={'开始节点':['标注流程开始','流程入口'],'人工节点':['内部验收','内部验收'],'自动化节点':['数据预处理','自动切分与预标注'],'条件节点':['供应商抽样','是否需要内部验收 == true'],'结束节点':['标注流程结束','流程结束']};
  document.querySelector('process-node-library[variant="basic"]').querySelectorAll('.palette-item').forEach(item=>{
    const name=item.textContent.trim(),type=types[name];
    const source=[...gallery.rows].find(row=>row.querySelector('.palette-item').dataset.nodeType===type);
    if(!source)return;
    const row=document.createElement('tr');
    row.append(source.cells[0].cloneNode(true));
    const defaultCell=source.cells[1].cloneNode(true);row.append(defaultCell);
    if(['Human Interrupt','Omini Model'].includes(type))defaultCell.querySelectorAll('.graph-sub').forEach(sub=>sub.remove());
    const filledCell=defaultCell.cloneNode(true);row.append(filledCell);
    const node=filledCell.querySelector('.graph-node'),heading=node.querySelector('.graph-title');
    heading.textContent=type==='Start'?'开始':type==='End'?'结束':examples[name][0];
    if(type==='Start'||type==='End')node.querySelectorAll('.graph-sub').forEach(el=>el.remove());
    else if(type==='Condition')node.querySelector('.condition-expression span').textContent=examples[name][1];
    else{
      node.querySelectorAll('.graph-sub').forEach(el=>el.remove());
      let text=node.querySelector('.node-text');
      if(!text){text=document.createElement('div');text.className='node-text';heading.replaceWith(text);text.append(heading);}
      const sub=document.createElement('div');sub.className='graph-sub';sub.textContent=examples[name][1];text.append(sub);
    }
    const properties=row.insertCell();
    const panel=name==='人工节点'?document.querySelector('process-node-properties[variant="basic"]'):null;
    if(panel){
      const oldSection=panel.closest('section.component-gallery__group');
      properties.append(panel);
      oldSection?.remove();
    }else if(type==='Condition'){properties.append(document.createElement('condition-panel'));}
    else if(type==='Omini Model'){const automation=document.createElement('process-node-properties');automation.setAttribute('variant','automation');properties.append(automation);}
    else{properties.className='node-properties-empty';properties.textContent='暂无';}
    standard.querySelector('tbody').append(row);
  });
  section.after(standard);
  // Group by presentation layer, keeping each live properties panel intact.
  const nodeCards=document.createElement('div');nodeCards.className='node-showcase-list';
  const makeLayer=(label,kind)=>{const layer=document.createElement('section');layer.className='node-showcase-layer';const title=document.createElement('h3');title.textContent=label;const items=document.createElement('div');items.className=`node-showcase-items node-showcase-items--${kind}`;layer.append(title,items);nodeCards.append(layer);return items;};
  const comparison=document.createElement('div');comparison.className='node-table-scroll node-comparison-scroll';
  comparison.innerHTML='<table class="node-state-table node-state-table--comparison"><thead><tr><th scope="col">节点库</th><th scope="col">画布节点 · 默认</th><th scope="col">画布节点 · 已填写</th></tr></thead><tbody></tbody></table>';
  nodeCards.append(comparison);
  const panelItems=makeLayer('面板属性','panels');
  [...gallery.rows].forEach(row=>{
    const comparisonRow=document.createElement('tr');
    [0,1,2].forEach(index=>{const cell=document.createElement('td');cell.append(...row.cells[index].childNodes);comparisonRow.append(cell);});
    comparison.querySelector('tbody').append(comparisonRow);
    const tallPreview=comparisonRow.querySelector('td:nth-child(3) .condition-cases');
    if(tallPreview){
      const canvas=tallPreview.closest('.node-state-canvas');canvas.classList.add('node-preview-collapsible');
      const toggle=document.createElement('button');toggle.type='button';toggle.className='node-preview-toggle';toggle.textContent='展开完整节点';toggle.setAttribute('aria-expanded','false');
      toggle.addEventListener('click',()=>{const expanded=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(expanded));toggle.textContent=expanded?'收起节点':'展开完整节点';canvas.classList.toggle('is-expanded',expanded);});
      canvas.after(toggle);
    }
    if(!row.cells[3].classList.contains('node-properties-empty'))panelItems.append(...row.cells[3].childNodes);
  });
  section.querySelector('.node-table-scroll').replaceWith(nodeCards);
  const nodeComparison=document.createElement('section');nodeComparison.className='node-library-comparison';
  const comparisonTitle=document.createElement('h3');comparisonTitle.textContent='京东 SKU · 节点样式对照';
  nodeComparison.append(comparisonTitle,comparison);
  variants.after(nodeComparison);
  const humanRow=[...standard.querySelectorAll('tbody > tr')].find(row=>row.querySelector('process-node-properties[variant="basic"]'));
  if(humanRow){
    const panels=document.createElement('div');panels.className='human-panel-variants';
    const cell=humanRow.cells[3];
    panels.append(cell.querySelector('process-node-properties'));
    for(const stage of ['review','accept','internal']){
      const panel=document.createElement('process-node-properties');panel.setAttribute('variant','basic');panel.setAttribute('human-stage',stage);panels.append(panel);
    }
    cell.append(panels);
  }
  standard.querySelectorAll('tbody > tr').forEach(row=>{
    const card=row.cells[2]?.querySelector('.graph-node'),cell=row.cells[3];
    if(!card||!cell)return;
    const properties=document.createElement('div');properties.className='standard-panel-group';
    properties.append(...cell.childNodes);cell.append(properties);
    const sync=()=>{
      const conditionPanel=properties.querySelector('condition-panel');
      if(conditionPanel)window.syncConditionNodePreview?.(card,conditionPanel.value);
      const name=properties.querySelector('input[name="nodeName"],input[name="name"]');
      const description=properties.querySelector('textarea[name="description"]');
      if(!name)return;
      const title=card.querySelector('.graph-title');title.textContent=name.value;title.title=name.value;
      const panelTitle=properties.querySelector('h2');if(panelTitle){panelTitle.textContent=name.value;panelTitle.title=name.value;}
      if(description){
        let text=card.querySelector('.node-text');
        if(!text){text=document.createElement('div');text.className='node-text';title.replaceWith(text);text.append(title);}
        let sub=text.querySelector('.graph-sub');if(!sub){sub=document.createElement('div');sub.className='graph-sub';text.append(sub);}
        sub.textContent=description.value;sub.title=description.value;sub.hidden=!description.value;
      }
    };
    sync();properties.addEventListener('input',sync);properties.addEventListener('change',sync);properties.addEventListener('click',()=>queueMicrotask(sync));properties.addEventListener('node-info-change',sync);properties.addEventListener('node-properties-save',sync);properties.addEventListener('automation-node-save',sync);
  });
  const standardPanels=document.createElement('div');standardPanels.className='node-showcase-items node-showcase-items--panels';
  standard.querySelectorAll('tbody > tr').forEach(row=>{
    const cell=row.cells[3];
    if(cell.querySelector('process-node-properties,condition-panel'))standardPanels.append(...cell.childNodes);
    cell.remove();
  });
  const standardTable=standard.querySelector('.node-table-scroll');
  standardTable.classList.add('node-comparison-scroll');
  standardTable.querySelector('table').classList.add('node-state-table--comparison');
  standardTable.querySelector('thead th:last-child').remove();
  const standardComparison=document.createElement('section');standardComparison.className='node-library-comparison';
  const standardTitle=document.createElement('h3');standardTitle.textContent='端到端切分标注 · 节点样式对照';
  standardComparison.append(standardTitle,standardTable);
  const comparisons=document.createElement('div');comparisons.className='node-library-comparisons';
  nodeComparison.before(comparisons);comparisons.append(nodeComparison,standardComparison);
  const panelsTitle=document.createElement('h3');panelsTitle.textContent='面板属性';
  standard.append(panelsTitle,standardPanels);
})();
