(() => {
  'use strict';
  const modal = document.getElementById('qAppendModal');
  if (!modal) return;
  const byId = id => document.getElementById(id);
  const form = byId('qAppendForm');
  const target = byId('qAppendTarget');
  const picker = byId('qAppendPicker');
  const search = byId('qAppendTargetSearch');
  const results = byId('qAppendTargetOptions');
  const datasetOptions = [...target.options].filter(option => option.value);
  const version = byId('qAppendVersion');
  const versions = JSON.parse(byId('qAppendVersionsConfig').textContent);
  const description = byId('qAppendDescription');
  const error = byId('qAppendError');
  const opener = byId('qAppendDataset');
  const submit = byId('qAppendSubmit');
  let pending = false;
  let activeIndex = -1;
  function closePicker() {
    picker.classList.remove('open');
    search.setAttribute('aria-expanded','false');
    search.removeAttribute('aria-activedescendant');
    search.value = target.value ? target.selectedOptions[0].textContent : '';
  }
  function highlight(index) {
    const options = [...results.children];
    activeIndex = index;
    options.forEach((option,i) => option.classList.toggle('active',i===index));
    if(options[index]) {
      search.setAttribute('aria-activedescendant',options[index].id);
      options[index].scrollIntoView({block:'nearest'});
    } else search.removeAttribute('aria-activedescendant');
  }
  function showOptions(query = '') {
    if(pending) return;
    const term = query.trim().toLowerCase();
    results.replaceChildren();
    datasetOptions.filter(option => (option.textContent+' '+option.value).toLowerCase().includes(term)).forEach(option => {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'ps-opt'; button.tabIndex = -1;
      button.id = 'qAppendOption-'+option.value;
      button.setAttribute('role','option');
      button.setAttribute('aria-selected',String(target.value===option.value));
      button.textContent = option.textContent;
      button.addEventListener('mousedown',event => event.preventDefault());
      button.addEventListener('click',() => {
        target.value = option.value;
        target.dispatchEvent(new Event('change',{bubbles:true}));
        closePicker(); search.focus();
      });
      results.append(button);
    });
    byId('qAppendTargetEmpty').style.display = results.children.length ? 'none' : 'block';
    picker.classList.add('open');
    search.setAttribute('aria-expanded','true');
    highlight(-1);
  }
  search.addEventListener('focus',() => { showOptions(); search.select(); });
  search.addEventListener('click',() => { if(!picker.classList.contains('open')) { showOptions(); search.select(); } });
  picker.querySelector('.ps-control').addEventListener('click',event => {
    if(event.target!==search && !pending) { search.focus(); showOptions(); }
  });
  search.addEventListener('input',() => showOptions(search.value));
  search.addEventListener('blur',closePicker);
  document.addEventListener('click',event => { if(!picker.contains(event.target)) closePicker(); });
  search.addEventListener('keydown',event => {
    if(event.key==='Escape' && picker.classList.contains('open')) {
      event.preventDefault(); event.stopPropagation(); closePicker();
    } else if(event.key==='ArrowDown' || event.key==='ArrowUp') {
      event.preventDefault();
      if(!picker.classList.contains('open')) showOptions();
      const count=results.children.length;
      if(count) highlight(activeIndex<0 ? (event.key==='ArrowDown'?0:count-1)
        : (activeIndex+(event.key==='ArrowDown'?1:count-1))%count);
    } else if(event.key==='Enter' && picker.classList.contains('open')) {
      event.preventDefault();
      const option=results.children[Math.max(0,activeIndex)];
      if(option) option.click();
    }
  });
  function updateVersionFields() {
    const draft=(versions[target.value]||[]).find(item=>item.version===version.value);
    description.value=draft?draft.description:'';
    byId('qAppendVersionHint').textContent=draft
      ? '数据将直接追加至 '+draft.version+'，版本保持未发布，版本描述同步更新。'
      : target.value?'基于当前生效版本 '+target.selectedOptions[0].dataset.version+' 新建未发布版本，版本号自动生成。'
      :'支持选择未发布版本，或新建一个版本。';
  }
  function updateVersions() {
    byId('qAppendFormat').value = target.value ? target.selectedOptions[0].dataset.format : '';
    search.setCustomValidity(target.value ? '' : '请选择我创建的数据集');
    version.replaceChildren();
    version.disabled=!target.value;
    function add(value,label,disabled=false) {
      const option=document.createElement('option');
      option.value=value;option.textContent=label;option.disabled=disabled;
      version.append(option);
    }
    if(!target.value){add('','请先选择数据集');}
    else {
      (versions[target.value]||[]).forEach(item=>add(item.version,item.version+' · 未发布'+(item.ready?'':'（尚未完成处理）'),!item.ready));
      add('__new__','+ 新建版本');
      version.value='__new__';
    }
    updateVersionFields();
  }
  target.addEventListener('change',updateVersions);
  version.addEventListener('change',updateVersionFields);
  function close() {
    if (pending) return;
    closePicker();
    modal.classList.remove('active');
    opener.focus();
  }
  opener.addEventListener('click', () => {
    if (opener.disabled) return;
    form.reset();
    closePicker();
    updateVersions();
    form.hidden = false;
    byId('qAppendSuccess').hidden = true;
    error.hidden = true;
    modal.classList.add('active');
    search.focus();
    closePicker();
  });
  ['qAppendClose','qAppendCancel','qAppendDone'].forEach(id => byId(id).addEventListener('click',close));
  modal.addEventListener('click',event => { if (event.target === modal) close(); });
  modal.addEventListener('keydown',event => {
    if (event.key === 'Escape') { event.stopPropagation(); close(); }
    if (event.key === 'Tab') {
      const controls = [...modal.querySelectorAll('button,input,select,textarea,a[href]')].filter(el => !el.disabled && el.getClientRects().length);
      const first = controls[0], last = controls[controls.length-1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  form.addEventListener('input',() => { error.hidden = true; });
  form.addEventListener('change',() => { error.hidden = true; });
  form.addEventListener('submit',async event => {
    event.preventDefault();
    if (pending) return;
    if (!target.value) {
      search.reportValidity(); search.focus(); return;
    }
    closePicker();
    if (!description.value.trim()) {
      error.textContent = '请填写版本描述'; error.hidden = false; description.focus(); return;
    }
    pending = true;
    submit.disabled = true;
    search.disabled = target.disabled = version.disabled = description.disabled = true;
    submit.textContent = '添加中…';
    form.setAttribute('aria-busy','true');
    error.hidden = true;
    try {
      const response = await fetch(form.action, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({dataset_id:target.value, base_version:target.selectedOptions[0].dataset.version,
          target_version:version.value==='__new__'?'':version.value,
          description:description.value.trim(), source_token:byId('qAppendSource').value})
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || '添加失败，请重试');
      byId('qAppendSuccessMessage').textContent = '已添加 '+result.added+' 条数据'+(result.skipped?'，跳过 '+result.skipped+' 条重复数据':'')+'，'+(result.created?'新建未发布版本 ':'更新未发布版本 ')+result.version+'。';
      const drafts=versions[target.value]||(versions[target.value]=[]);
      const saved=drafts.find(item=>item.version===result.version);
      if(saved)saved.description=description.value.trim();
      else drafts.unshift({version:result.version,description:description.value.trim(),ready:true});
      const url = new URL(form.action);
      url.pathname = url.pathname.replace(/\/append$/,'');
      url.search = new URLSearchParams({sel:target.value,ver:result.version,tab:'version'}).toString();
      byId('qAppendView').href = url.toString();
      form.hidden = true;
      byId('qAppendSuccess').hidden = false;
      byId('qAppendView').focus();
    } catch (failure) {
      error.textContent = failure.message || '添加失败，请重试'; error.hidden = false;
    } finally {
      pending = false;
      submit.disabled = false;
      search.disabled = target.disabled = description.disabled = false;
      version.disabled = !target.value;
      submit.textContent = '确认添加';
      form.removeAttribute('aria-busy');
    }
  });
})();
