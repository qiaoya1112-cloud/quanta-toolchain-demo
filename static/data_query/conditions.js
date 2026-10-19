(() => {
  'use strict';
  const configElement = document.getElementById('qAdvancedConfig');
  if (!configElement) return;
  const config = JSON.parse(configElement.textContent);
  const form = document.getElementById('qform');
  const fields = config.fields;
  const trees = { conditions: config.conditions, exclusions: config.exclusions };
  const builders = { conditions: document.getElementById('qConditionsBuilder'), exclusions: document.getElementById('qExclusionsBuilder') };
  const hidden = { conditions: document.getElementById('qConditionsValue'), exclusions: document.getElementById('qExclusionsValue') };
  const nodeElements = new WeakMap();
  const idsInput = document.getElementById('qExcludedIds');
  const durationInput = document.getElementById('qDurationLimit');
  durationInput.addEventListener('blur',()=>{
    if(durationInput.value!=='' && Number.isFinite(Number(durationInput.value))) {
      durationInput.value=Number(durationInput.value).toFixed(2);
      markDirty();
    }
  });
  const errorBox = document.getElementById('qConditionError');
  const buildButton = document.getElementById('qBuildDataset');
  const appendButton = document.getElementById('qAppendDataset');
  const originalCanBuild = document.querySelector('.query-result-actions').dataset.hasResults === '1';
  let queryDirty = false;
  Object.keys(trees).forEach(key => hidden[key].value = JSON.stringify(trees[key]));
  const initialForm = new URLSearchParams(new FormData(form)).toString();
  function element(tag, className, text) {
    const item = document.createElement(tag);
    if (className) item.className = className;
    if (text !== undefined) item.textContent = text;
    return item;
  }
  function option(value, label) { const item = element('option', '', label); item.value = value; return item; }
  function button(label, action, className = 'query-text-button') {
    const item = element('button', className, label); item.type = 'button'; item.addEventListener('click', action); return item;
  }
  function showError(message) { errorBox.textContent = message; errorBox.hidden = !message; if (message) errorBox.scrollIntoView({block:'center', behavior:'smooth'}); }
  function markDirty() {
    queryDirty = new URLSearchParams(new FormData(form)).toString() !== initialForm;
    document.getElementById('qQueryDirty').hidden = !queryDirty;
    updateResultActions();
  }
  function sync() {
    Object.keys(trees).forEach(key => hidden[key].value = JSON.stringify(trees[key]));
    updateCounts();
    markDirty();
  }
  function ruleCount(group) { return group.children.reduce((count,child)=>count+(child.children?ruleCount(child):1),0); }
  function updateCounts() {
    const include=ruleCount(trees.conditions),exclude=ruleCount(trees.exclusions),manual=ids().length;
    document.getElementById('qIncludeCount').textContent=include?include+' 个条件':'';
    document.getElementById('qExcludeCount').textContent=[exclude?exclude+' 个条件':'',manual?manual+' 条指定数据':''].filter(Boolean).join(' · ');
    document.getElementById('qExclusions').classList.toggle('has-config',!!(exclude||manual));
  }
  function newRule() { return {field:'recording_id', op:'eq', value:''}; }
  function newGroup(key, children = []) { return {logic:key==='exclusions'?'or':'and', children}; }
  function fieldControl(label, input, className = '') {
    const wrap = element('div', 'q-field ' + className);
    input.setAttribute('aria-label', label);
    wrap.append(input);
    return wrap;
  }
  function renderValue(rule) {
    const spec = fields[rule.field];
    if (['empty','not_empty'].includes(rule.op)) {
      const input = element('input'); input.disabled = true; input.placeholder = '无需填写'; return input;
    }
    const multi = ['in','not_in'].includes(rule.op);
    let input;
    if (spec.options || spec.type === 'boolean') {
      if (multi) {
        const wrap=element('div','ms-wrap');
        const trigger=element('div','ms-trigger');
        trigger.dataset.base='请选择';
        const label=element('span','ms-label'); trigger.append(label);
        trigger.tabIndex=0; trigger.setAttribute('role','button'); trigger.setAttribute('aria-expanded','false');
        const panel=element('div','ms-panel');
        const selected=(Array.isArray(rule.value)?rule.value:String(rule.value).replaceAll('，',',').split(',')).map(String);
        function update() {
          const checked=[...panel.querySelectorAll('input:checked')];
          rule.value=checked.map(input=>input.value);
          label.textContent=checked.length?checked.map(input=>input.parentNode.textContent).join(', '):'请选择';
          trigger.classList.toggle('has-value',!!checked.length);
          trigger.setAttribute('aria-label','值：'+(checked.length?checked.map(input=>input.parentNode.textContent).join('、'):'请选择'));
        }
        function toggle(){const open=wrap.classList.toggle('open');trigger.setAttribute('aria-expanded',String(open));}
        trigger.addEventListener('click',toggle);
        trigger.addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();toggle();}});
        spec.options.forEach(([value,name])=>{
          const row=element('label');const checkbox=element('input');checkbox.type='checkbox';checkbox.value=value;checkbox.checked=selected.includes(String(value));
          checkbox.addEventListener('change',()=>{update();sync();});row.append(checkbox,element('span','',name));panel.append(row);
        });
        update();wrap.append(trigger,panel);return wrap;
      }
      input = element('select');
      const options = spec.type === 'boolean' ? [['true','是'],['false','否']] : spec.options;
      if (!multi) input.append(option('', '请选择'));
      input.multiple = multi;
      const values = (Array.isArray(rule.value) ? rule.value : String(rule.value).split(',')).map(String);
      options.forEach(([value,label]) => { const opt = option(value,label); opt.selected = values.includes(String(value)); input.append(opt); });
      input.addEventListener('change', () => { rule.value = multi ? [...input.selectedOptions].map(opt => opt.value) : input.value; sync(); });
    } else {
      input = element('input');
      input.type = spec.type === 'date' ? 'date' : spec.type === 'number' && !multi ? 'number' : 'text';
      if (input.type === 'number') input.step = 'any';
      input.value = Array.isArray(rule.value) ? rule.value.join(',') : rule.value;
      input.placeholder = multi ? '多个值用逗号分隔' : spec.type === 'number' ? '请输入数字' : '请输入条件值';
      input.addEventListener('input', () => { rule.value = input.value; sync(); });
    }
    return input;
  }
  function renderGroup(group, key, depth, remove) {
    const box = element('div', 'query-condition-group'); box.dataset.logic = group.logic; box.dataset.depth = depth;
    nodeElements.set(group,box);
    const toolbar = element('div', 'query-condition-toolbar');
    toolbar.append(element('span','query-group-caption',depth?'条件组':'满足以下'));
    const logic = element('select');
    const logicOptions = key==='exclusions' ? [['or','或（任一满足）'],['and','且（全部满足）']] : [['and','且（全部满足）'],['or','或（任一满足）']];
    logicOptions.forEach(([value,label]) => logic.append(option(value,label)));
    logic.value = group.logic;
    logic.setAttribute('aria-label','条件组关系');
    logic.addEventListener('change', () => { group.logic = logic.value; refresh(key); });
    const logicWrap = element('div','q-field'); logicWrap.append(logic); toolbar.append(logicWrap);
    const actions=element('div','query-group-actions');
    const add = button('+ 添加条件', () => { const rule=newRule();group.children.push(rule);refresh(key,rule); },'query-text-button');
    add.disabled = depth >= 6; actions.append(add);
    const addGroup = button('+ 添加条件组', () => { const rule=newRule();group.children.push(newGroup(key,[rule]));refresh(key,rule); },'query-text-button');
    addGroup.disabled = depth >= 5; actions.append(addGroup);
    if (remove) toolbar.append(button('移除组', remove,'query-text-button query-remove query-group-clear'));
    else if (group.children.length) toolbar.append(button('清空条件', () => { group.children = []; refresh(key); },'query-text-button query-remove query-group-clear'));
    box.append(toolbar);
    if (!group.children.length) box.append(element('p','muted query-empty',key==='exclusions'?'暂未配置剔除条件，可添加条件或在上方指定数据 ID。':'暂未添加复杂条件，当前仅使用固定筛选。'));
    group.children.forEach((child,index) => {
      const removeNode = () => { group.children.splice(index,1); refresh(key); };
      if (child.children) { box.append(renderGroup(child,key,depth+1,removeNode)); return; }
      const row = element('div','query-condition-row');
      nodeElements.set(child,row);
      const field = element('select');
      Object.entries(fields).forEach(([id,spec]) => field.append(option(id,spec.label)));
      field.value = child.field;
      field.addEventListener('change', () => { child.field=field.value; child.op=config.typeOperators[fields[field.value].type][0]; child.value=''; refresh(key); });
      const op = element('select');
      config.typeOperators[fields[child.field].type].forEach(value => op.append(option(value,config.operators[value])));
      op.value = child.op;
      op.addEventListener('change', () => { child.op=op.value; child.value=''; refresh(key); });
      row.append(fieldControl('字段',field), fieldControl('运算符',op), fieldControl('值',renderValue(child), 'query-value'), button('移除',removeNode,'query-text-button query-remove'));
      box.append(row);
    });
    box.append(actions);
    return box;
  }
  function refresh(key, addedNode) {
    builders[key].replaceChildren(renderGroup(trees[key],key,0));sync();showError('');
    if(addedNode) {
      const row=nodeElements.get(addedNode);
      row.querySelector('select').focus({preventScroll:true});
      row.scrollIntoView({block:'nearest'});
    }
  }
  function ids() { return [...new Set(idsInput.value.split(/[,，\s]+/).map(id=>id.replace(/^#/,'').trim()).filter(Boolean))]; }
  function renderIds() {
    const chips=document.getElementById('qExcludedChips'); chips.replaceChildren();
    ids().forEach(id => {
      const chip=element('span','visibility-chip'); chip.append(element('span','', '#' + id));
      const remove=button('×',()=>{idsInput.value=ids().filter(item=>item!==id).join(',');renderIds();markDirty();});
      remove.setAttribute('aria-label','恢复数据 '+id); chip.append(remove); chips.append(chip);
    });
    updateCounts();
  }
  function validateTree(node, depth=0, counter={count:0}) {
    counter.count++;
    if (counter.count>100 || depth>6) return '最多支持 100 个条件节点、6 层嵌套';
    if (node.children) {
      if (depth && !node.children.length) return '条件组不能为空，请添加条件或移除该组';
      for (const child of node.children) { const error=validateTree(child,depth+1,counter); if(error)return error; }
    } else if (!['empty','not_empty'].includes(node.op)) {
      const values=Array.isArray(node.value)?node.value:['in','not_in'].includes(node.op)?String(node.value).replaceAll('，',',').split(','):[node.value];
      if(!values.length || values.some(value=>String(value).trim()==='')) return '请完整填写条件值，或移除未使用的条件';
      if(fields[node.field].type==='number' && values.some(value=>!Number.isFinite(Number(value)))) return '数值字段必须填写有效数字';
    }
    return '';
  }
  form.addEventListener('submit', event => {
    sync();
    const error=validateTree(trees.conditions)||validateTree(trees.exclusions)||(ids().some(id=>!/^\d+$/.test(id))?'剔除数据 ID 必须为数字':'');
    if(error){event.preventDefault();showError(error);return;}
    idsInput.value=ids().join(',');
    showError('');
  });
  form.addEventListener('input',markDirty); form.addEventListener('change',markDirty);
  const filterGroups=[...document.querySelectorAll('.query-fixed-group, .query-volume')];
  function updateFilterCounts() {
    filterGroups.forEach(group=>{
      const panel=group.querySelector('.query-fixed-panel');
      const count=[...panel.querySelectorAll('.q-field')].filter(field=>[...field.querySelectorAll('input,select')].some(input=>{
        if(input.closest('.qf-off')||input.matches('.ms-search,.ps-input'))return false;
        if(input.type==='checkbox')return input.checked;
        return !!input.value;
      })).length;
      group.querySelector('.query-fixed-count').textContent=count?'已选 '+count+' 项':'';
    });
  }
  form.addEventListener('input',updateFilterCounts);form.addEventListener('change',updateFilterCounts);
  const pickerObserver=new MutationObserver(()=>{updateFilterCounts();markDirty();});
  document.querySelectorAll('.query-fixed-panel .ps-chips').forEach(chips=>pickerObserver.observe(chips,{childList:true,subtree:true}));
  updateFilterCounts();
  idsInput.addEventListener('input',renderIds);
  Object.keys(builders).forEach(key => builders[key].append(renderGroup(trees[key],key,0)));
  renderIds();
  document.getElementById('qClearExclusions').addEventListener('click',()=>{trees.exclusions=newGroup('exclusions');idsInput.value='';refresh('exclusions');renderIds();});
  function updateResultActions() {
    buildButton.disabled = appendButton.disabled = queryDirty || !originalCanBuild;
  }
  updateResultActions();
})();
