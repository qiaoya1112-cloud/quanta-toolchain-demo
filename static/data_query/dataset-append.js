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
  const mode = byId('qAppendMode');
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
    const selected=(versions[target.value]||[]).find(item=>item.version===version.value);
    const isDraft=mode.value==='draft';
    description.value=isDraft && selected?selected.description:'';
    byId('qAppendVersionLabel').textContent=isDraft?'目标未发布版本':'来源已发布版本';
    submit.textContent=isDraft?'确认添加':'新建版本并添加';
    submit.disabled=!selected || !selected.ready;
    byId('qAppendVersionHint').textContent=!target.value
      ? '选择数据集后，可添加至未发布版本，或基于已发布版本新建。'
      : !selected ? (isDraft?'暂无可添加的未发布版本，可切换为基于已发布版本新建。':'暂无已发布版本，可切换为添加至未发布版本。')
      : !selected.ready ? '所选版本尚未完成处理，暂不能添加数据。'
      : isDraft ? '数据直接追加至 '+selected.version+'，该版本保持未发布，版本描述同步更新。'
      : '保留 '+selected.version+' 的已有数据，合并本次结果生成新的未发布版本；来源版本保持不变，版本号自动生成。';
  }
  function updateVersionOptions() {
    version.replaceChildren();
    version.disabled=!target.value;
    function add(value,label,disabled=false) {
      const option=document.createElement('option');
      option.value=value;option.textContent=label;option.disabled=disabled;
      version.append(option);
    }
    if(!target.value){add('','请先选择数据集');}
    else {
      const publishStatus=mode.value==='draft'?'未发布':'已发布';
      const options=(versions[target.value]||[]).filter(item=>item.publish_status===publishStatus);
      options.forEach(item=>add(item.version,item.version+' · '+publishStatus+(item.status==='生效中'?' · 当前生效':'')+(item.ready?'':'（尚未完成处理）'),!item.ready));
      if(!options.length) add('',mode.value==='draft'?'暂无未发布版本':'暂无已发布版本');
      const preferred=options.find(item=>item.ready && item.status==='生效中') || options.find(item=>item.ready);
      version.value=preferred?preferred.version:'';
    }
    updateVersionFields();
  }
  function updateVersions() {
    byId('qAppendFormat').value = target.value ? target.selectedOptions[0].dataset.format : '';
    search.setCustomValidity(target.value ? '' : '请选择我创建的数据集');
    mode.disabled=!target.value;
    const catalog=versions[target.value]||[];
    mode.value=catalog.some(item=>item.publish_status==='已发布' && item.ready)?'new':'draft';
    updateVersionOptions();
  }
  target.addEventListener('change',updateVersions);
  mode.addEventListener('change',updateVersionOptions);
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
    if (!version.value) {
      error.textContent='请选择可用的'+(mode.value==='draft'?'未发布版本':'已发布来源版本');
      error.hidden=false; version.focus(); return;
    }
    closePicker();
    if (!description.value.trim()) {
      error.textContent = '请填写版本描述'; error.hidden = false; description.focus(); return;
    }
    pending = true;
    submit.disabled = true;
    search.disabled = target.disabled = mode.disabled = version.disabled = description.disabled = true;
    submit.textContent = '添加中…';
    form.setAttribute('aria-busy','true');
    error.hidden = true;
    try {
      const response = await fetch(form.action, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({dataset_id:target.value, base_version:mode.value==='new'?version.value:'',
          target_version:mode.value==='draft'?version.value:'',
          description:description.value.trim(), source_token:byId('qAppendSource').value})
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || '添加失败，请重试');
      byId('qAppendSuccessMessage').textContent = '已添加 '+result.added+' 条数据'+(result.skipped?'，跳过 '+result.skipped+' 条重复数据':'')+'，'+(result.created?'新建未发布版本 ':'更新未发布版本 ')+result.version+'。';
      const drafts=versions[target.value]||(versions[target.value]=[]);
      const saved=drafts.find(item=>item.version===result.version);
      if(saved)saved.description=description.value.trim();
      else drafts.unshift({version:result.version,description:description.value.trim(),ready:true,publish_status:'未发布',status:'未生效'});
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
      search.disabled = target.disabled = description.disabled = false;
      mode.disabled = version.disabled = !target.value;
      submit.disabled = !version.value;
      submit.textContent = mode.value==='draft'?'确认添加':'新建版本并添加';
      form.removeAttribute('aria-busy');
    }
  });
})();
