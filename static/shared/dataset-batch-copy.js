(function () {
  'use strict';
  const yamlIssues = item => [item.format !== 'mozdataset v2' ? '格式不支持' : '', !item.vepfs_addresses?.length ? '缺少 VEPFS 地址' : ''].filter(Boolean);
  const storageIssue = kind => '缺少 ' + kind + ' 地址';
  function formatSelection(items, kind) {
    if (!items.length) throw new Error('请先选择数据集。');
    if (kind === 'tos' || kind === 'ks3') {
      const missing = items.filter(item => !(item.addresses || []).some(address => address.startsWith(kind + '://')));
      if (missing.length) throw new Error(missing.map(item => item.name + ' ' + item.version + '：' + storageIssue(kind)).join('\n'));
      const field = value => String(value).replace(/[\r\n]/g, ' ');
      const entries = items.map(item => ({
        dataset_id: field(item.ident || item.id),
        [kind + '_addresses']: [...new Set(item.addresses)]
          .filter(address => address.startsWith(kind + '://')).map(field)
      }));
      return JSON.stringify(entries, null, 2) + '\n';
    }
    if (kind !== 'yaml') throw new Error('不支持的生成格式。');
    const invalid = items.flatMap(item => {
      const reasons = yamlIssues(item);
      return reasons.length ? [item.name + ' ' + item.version + '：' + reasons.join('；')] : [];
    });
    if (invalid.length) throw new Error('无法生成预训练 yaml：\n' + invalid.join('\n'));
    const quote = value => JSON.stringify(value);
    return '# 预训练数据集配置片段\ndatasets:\n' + items.map(item => [
      '  - name: ' + quote(item.name),
      '    version: ' + quote(item.version),
      '    format: ' + quote(item.format),
      '    storage_paths:',
      ...item.vepfs_addresses.map(address => '      - ' + quote(address))
    ].join('\n')).join('\n') + '\n';
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {formatSelection};
  if (typeof document === 'undefined') return;
  const byId = id => document.getElementById(id);
  const config = byId('datasetTreeCopyConfig');
  if (!config) return;
  const items = [...JSON.parse(config.textContent), ...JSON.parse(byId('datasetAdditionalConfig')?.textContent || '[]')];
  const checkboxes = [...document.querySelectorAll('.dataset-tree-checkbox')];
  const ids = new Set(checkboxes.map(node => node.value));
  let selected = new Set();
  const trigger = byId('datasetPreviewButton');
  const folders = [...document.querySelectorAll('.dataset-folder-checkbox')];
  const descendants = folder => [...folder.closest('.dataset-folder').querySelectorAll('.dataset-tree-checkbox')].map(node => node.value);
  const status = byId('datasetTreeCopyStatus');
  const panel = byId('datasetTreeBatch').closest('.tree-panel');
  const versionModal = byId('datasetVersionModal');
  let chosenVersions = [], versionOverflow = '', pendingBatch = false, submittedBatch = false, previewValidated = false;
  const versionsFor = candidate => {
    const source = items.find(item => item.id === candidate.id) || candidate;
    return (byId('datasetBatchType').value === 'storage' ? source.all_versions : source.versions) || [];
  };
  const availableVersions = (candidate, index) => versionsFor(candidate).filter(version => !chosenVersions.some((other, i) => i !== index && other.id === candidate.id && other.version === version.version));
  function closeVersions() {
    if (pendingBatch) return;
    versionModal.classList.remove('active');
    document.body.style.overflow = versionOverflow;
    (byId('datasetChooseVersions').disabled ? byId('datasetTreeBatchToggle') : byId('datasetChooseVersions')).focus();
  }
  function searchableDataset(select, cell, index) {
    select.hidden = true;
    const input = document.createElement('input');
    input.className = 'dataset-row-search'; input.placeholder = '搜索并选择数据集';
    input.setAttribute('role', 'combobox'); input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-label', '第 ' + (index + 1) + ' 行数据集');
    input.setAttribute('aria-expanded', 'false'); input.autocomplete = 'off';
    const list = document.createElement('div');
    list.className = 'rf-menu dataset-search-options'; list.id = 'datasetSearchOptions-' + index;
    list.setAttribute('role', 'listbox'); list.hidden = true;
    input.setAttribute('aria-controls', list.id);
    cell.appendChild(input); versionModal.appendChild(list);
    let active = -1;
    const restore = () => { input.value = select.value ? select.selectedOptions[0].textContent : ''; };
    const close = () => { list.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); restore(); };
    const highlight = value => {
      const options = [...list.querySelectorAll('button:not(:disabled)')]; active = value;
      list.querySelectorAll('button').forEach(node => node.classList.remove('on'));
      if (options[active]) { options[active].classList.add('on'); input.setAttribute('aria-activedescendant', options[active].id); options[active].scrollIntoView({block:'nearest'}); }
    };
    const show = (query = '') => {
      list.replaceChildren(); active = -1; input.removeAttribute('aria-activedescendant');
      [...select.options].filter(option => option.value && (option.textContent + ' ' + option.value).toLowerCase().includes(query.trim().toLowerCase())).forEach((option, i) => {
        const button = document.createElement('button'); button.type = 'button'; button.className = 'rf-option';
        button.textContent = option.textContent + (option.disabled && !option.textContent.includes('暂无已发布') ? '（已选择）' : '');
        button.disabled = option.disabled; button.tabIndex = -1; button.id = list.id + '-' + i;
        button.setAttribute('role', 'option'); button.setAttribute('aria-selected', String(select.value === option.value));
        button.addEventListener('mousedown', event => event.preventDefault());
        button.addEventListener('click', () => { close(); select.value = option.value; select.dispatchEvent(new Event('change')); });
        list.appendChild(button);
      });
      if (!list.children.length) { const empty = document.createElement('div'); empty.className = 'muted rf-option'; empty.textContent = '暂无匹配数据集'; list.appendChild(empty); }
      const rect = input.getBoundingClientRect();
      list.style.left = rect.left + 'px'; list.style.width = rect.width + 'px';
      const below = window.innerHeight - rect.bottom - 12;
      const above = rect.top - 12;
      list.style.top = below >= 180 || below >= above ? rect.bottom + 4 + 'px' : 'auto';
      list.style.bottom = below >= 180 || below >= above ? 'auto' : window.innerHeight - rect.top + 4 + 'px';
      list.style.maxHeight = Math.max(60, Math.min(220, Math.max(below, above))) + 'px';
      list.hidden = false; input.setAttribute('aria-expanded', 'true');
    };
    input.addEventListener('click', () => { if (list.hidden) { show(); input.select(); } });
    input.addEventListener('input', () => show(input.value));
    input.addEventListener('blur', close);
    input.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !list.hidden) { event.preventDefault(); event.stopPropagation(); close(); }
      else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault(); if (list.hidden) show();
        const count = list.querySelectorAll('button:not(:disabled)').length;
        if (count) highlight(active < 0 ? (event.key === 'ArrowDown' ? 0 : count - 1) : (active + (event.key === 'ArrowDown' ? 1 : count - 1)) % count);
      } else if (event.key === 'Enter' && !list.hidden) { event.preventDefault(); list.querySelectorAll('button:not(:disabled)')[Math.max(active, 0)]?.click(); }
    });
    restore();
  }
  versionModal.addEventListener('scroll', event => {
    if (event.target.closest?.('.dataset-search-options')) return;
    versionModal.querySelectorAll('.dataset-search-options').forEach(node => { node.hidden = true; });
    versionModal.querySelectorAll('.dataset-row-search').forEach(node => node.setAttribute('aria-expanded', 'false'));
  }, true);
  function renderVersions({preserveValidation = false} = {}) {
    if (!preserveValidation) previewValidated = false;
    byId('datasetVersionError').hidden = true;
    const storage = byId('datasetBatchType').value === 'storage';
    chosenVersions.forEach((item, index) => {
      if (!item.id || versionsFor(item).some(version => version.version === item.version)) return;
      const next = availableVersions(item, index)[0];
      chosenVersions[index] = {...item, ...(next || {version: '', publish_status: '', format: '', addresses: [], vepfs_addresses: []})};
    });
    const missingPublished = chosenVersions.some(item => item.id && !versionsFor(item).length);
    const blocked = !chosenVersions.length || missingPublished || chosenVersions.some(item => !item.id) || new Set(chosenVersions.map(item => item.id + ':' + item.version)).size !== chosenVersions.length;
    trigger.setAttribute('aria-disabled', String(blocked));
    trigger.disabled = blocked;
    byId('datasetVersionHint').textContent = storage ? '支持已发布和未发布版本。' : missingPublished
      ? '部分数据集暂无已发布版本，请移除或发布版本后再生成。'
      : '仅支持已发布版本，默认选择最新已发布版本。';
    versionModal.querySelectorAll('.dataset-search-options').forEach(node => node.remove());
    const tbody = byId('datasetVersionRows');
    tbody.replaceChildren();
    chosenVersions.forEach((item, index) => {
      const row = document.createElement('tr');
      const name = document.createElement('td'), datasetSelect = document.createElement('select');
      datasetSelect.className = 'dataset-row-select';
      datasetSelect.setAttribute('aria-label', '第 ' + (index + 1) + ' 行数据集');
      datasetSelect.appendChild(new Option('请选择数据集', ''));
      items.forEach(candidate => {
        const option = new Option(candidate.name + (versionsFor(candidate).length ? '' : (storage ? '（暂无版本）' : '（暂无已发布版本）')), candidate.id);
        option.disabled = !availableVersions(candidate, index).length && candidate.id !== item.id;
        datasetSelect.appendChild(option);
      });
      datasetSelect.value = item.id;
      datasetSelect.addEventListener('change', () => {
        const candidate = items.find(other => other.id === datasetSelect.value);
        const available = candidate ? availableVersions(candidate, index) : [];
        if (candidate && !available.length) return;
        chosenVersions[index] = candidate ? {...available[0], versions: candidate.versions} : {id: '', name: '', versions: []};
        selected = new Set(chosenVersions.filter(other => other.id).map(other => other.id));
        refresh(); renderVersions();
        byId('datasetVersionRows').rows[index].querySelector('.dataset-row-search').focus();
      });
      name.appendChild(datasetSelect);
      searchableDataset(datasetSelect, name, index);
      const format = document.createElement('td');
      format.className = 'dataset-row-format'; format.textContent = item.format || '—';
      const field = document.createElement('td'), select = document.createElement('select');
      select.className = 'dataset-row-version';
      select.setAttribute('aria-label', (item.name || '第 ' + (index + 1) + ' 行') + ' 版本');
      const actions = document.createElement('td'), remove = document.createElement('button');
      remove.type = 'button'; remove.className = 'action-link'; remove.textContent = '移除';
      remove.setAttribute('aria-label', item.id ? '移除数据集 ' + item.name : '移除第 ' + (index + 1) + ' 行');
      remove.addEventListener('click', () => {
        chosenVersions.splice(index, 1);
        selected = new Set(chosenVersions.filter(other => other.id).map(other => other.id));
        refresh(); renderVersions({preserveValidation: true});
        byId('datasetAddButton').focus();
      });
      actions.appendChild(remove);
      versionsFor(item).forEach((version, i) => {
        const option = document.createElement('option');
        option.value = version.version;
        option.disabled = chosenVersions.some((other, i) => i !== index && other.id === item.id && other.version === version.version);
        option.textContent = version.version + (storage ? '（' + version.publish_status + '）' : (i === 0 ? '（最新已发布）' : ''));
        select.appendChild(option);
      });
      if (!versionsFor(item).length) {
        const option = document.createElement('option');
        option.textContent = item.id ? (storage ? '暂无版本' : '暂无已发布版本') : '请先选择数据集';
        select.appendChild(option);
        select.disabled = true;
      }
      if (item.version) select.value = item.version;
      select.addEventListener('change', () => {
        const version = versionsFor(item).find(option => option.version === select.value);
        if (!availableVersions(item, index).some(other => other.version === version.version)) return;
        chosenVersions[index] = {...version, versions: item.versions};
        renderVersions();
        byId('datasetVersionRows').rows[index].querySelector('.dataset-row-version').focus();
      });
      field.appendChild(select); row.append(name, field, format, actions); tbody.appendChild(row);
    });
    if (!chosenVersions.length) {
      const row = document.createElement('tr'), cell = document.createElement('td');
      cell.colSpan = 4; cell.className = 'muted'; cell.textContent = '暂无数据集，请添加数据集';
      row.appendChild(cell); tbody.appendChild(row);
    }
    submittedBatch = false;
    byId('datasetBatchResult').hidden = true;
    updateBatchType();
  }
  const operators = JSON.parse(byId('datasetBatchOperators').textContent);
  const operatorSelect = byId('datasetBatchOperator');
  operatorSelect.appendChild(new Option('请选择算子', ''));
  operators.forEach(operator => operatorSelect.appendChild(new Option(operator.name, operator.id)));
  function updateYamlValidation() {
    const kind = byId('datasetPreviewFields').querySelector('input:checked')?.value;
    const checking = previewValidated && byId('datasetBatchType').value === 'preview';
    const invalid = chosenVersions.map((item, index) => ({item, index, reasons: !item.id ? [] : kind === 'yaml' ? yamlIssues(item) : (item.addresses || []).some(address => address.startsWith(kind + '://')) ? [] : [storageIssue(kind)]})).filter(row => row.reasons.length);
    byId('datasetYamlValidation').hidden = !checking || !invalid.length;
    byId('datasetYamlSummary').textContent = invalid.length + (kind === 'yaml' ? ' 个版本不符合预训练 YAML 要求' : ' 个版本缺少 ' + kind + ' 地址');
    byId('datasetValidationRequirement').textContent = kind === 'yaml' ? [
      invalid.some(row => row.item.format !== 'mozdataset v2') ? '只有 mozdataset v2 格式支持生成预训练 YAML，请移除格式不符的版本。' : '',
      invalid.some(row => !row.item.vepfs_addresses?.length) ? '缺少 VEPFS 地址的版本，请先通过「同步存储」同步至 VEPFS，完成后再生成预览。' : ''
    ].filter(Boolean).join(' ') : '请移除缺少 ' + kind + ' 地址的数据集版本，或者先通过「同步存储」同步至 ' + kind + '，完成后再生成预览。';
    byId('datasetVersionRows').querySelectorAll('tr').forEach((row, index) => {
      const issue = checking && invalid.find(item => item.index === index);
      row.classList.toggle('dataset-yaml-invalid', Boolean(issue));
      const search = row.querySelector('.dataset-row-search');
      if (search) search.setAttribute('aria-invalid', String(Boolean(issue)));
      let hint = row.querySelector('.dataset-row-validation');
      if (issue && !hint) {
        hint = document.createElement('div'); hint.className = 'dataset-row-validation';
        hint.id = 'datasetRowIssue-' + index; row.cells[0].appendChild(hint);
      }
      if (hint) { hint.hidden = !issue; hint.textContent = issue ? issue.reasons.join('；') : ''; }
      if (search) { if (issue) search.setAttribute('aria-describedby', hint.id); else search.removeAttribute('aria-describedby'); }
    });
    const incomplete = !chosenVersions.length || chosenVersions.some(item => !item.id || item.publish_status !== '已发布');
    trigger.disabled = incomplete;
    trigger.setAttribute('aria-disabled', String(trigger.disabled));
  }
  byId('datasetPreviewFields').addEventListener('change', () => { previewValidated = false; byId('datasetVersionError').hidden = true; updateYamlValidation(); });
  const taskListUrl = location.pathname.startsWith('/model/data/') ? '/model/data/tasks' : location.pathname.replace(/\/$/, '') + '/tasks';
  function storageTargets() {
    return [...byId('datasetStorageFields').querySelectorAll('input:checked')].map(node => node.value);
  }
  function renderStorageStatus() {
    const targets = storageTargets();
    const visible = byId('datasetBatchType').value === 'storage' && targets.length && chosenVersions.some(row => row.id && row.version);
    byId('datasetStorageStatus').hidden = !visible;
    const rows = byId('datasetStorageStatusRows'); rows.replaceChildren();
    if (!visible) return;
    const counts = {synced: 0, syncing: 0, pending: 0};
    chosenVersions.filter(row => row.id && row.version).forEach(row => {
      targets.forEach(target => { counts[row.storage_status?.[target] || 'pending'] += 1; });
    });
    rows.textContent = '已同步 ' + counts.synced + ' 项 · 同步中 ' + counts.syncing + ' 项 · 待同步 ' + counts.pending + ' 项';
  }
  function showStorageToast(count) {
    byId('datasetStorageToast')?.remove();
    const toast = document.createElement('div');
    toast.id = 'datasetStorageToast'; toast.className = 'q-toast show';
    toast.setAttribute('role', 'status');
    const message = document.createElement('span');
    message.appendChild(document.createTextNode('已提交 ' + count + ' 个数据同步任务，'));
    const link = document.createElement('a'); link.className = 'action-link';
    link.textContent = '查看进度'; link.href = taskListUrl + '?task_type=storage';
    message.appendChild(link); toast.appendChild(message); document.body.appendChild(toast);
    let timer;
    const dismiss = () => { clearTimeout(timer); timer = setTimeout(() => toast.remove(), 8000); };
    toast.addEventListener('mouseenter', () => clearTimeout(timer));
    toast.addEventListener('mouseleave', dismiss);
    toast.addEventListener('focusin', () => clearTimeout(timer));
    toast.addEventListener('focusout', dismiss);
    dismiss();
  }

  function updateBatchType() {
    const type = byId('datasetBatchType').value;
    byId('datasetPreviewFields').hidden = type !== 'preview'; trigger.hidden = type !== 'preview';
    updateYamlValidation();
    byId('datasetStorageFields').hidden = type !== 'storage';
    renderStorageStatus();
    byId('datasetOperatorFields').hidden = type !== 'operator';
    const submit = byId('datasetBatchSubmit');
    submit.hidden = type !== 'storage' && type !== 'operator';
    submit.textContent = pendingBatch ? '提交中…' : submittedBatch ? '已提交' : type === 'storage' ? '提交同步' : '执行算子';
    submit.disabled = !type || pendingBatch || submittedBatch || !chosenVersions.length || chosenVersions.some(row => !row.id || !row.version || (type !== 'storage' && row.publish_status !== '已发布'))
      || (type === 'storage' && !chosenVersions.some(row => storageTargets().some(target => (row.storage_status?.[target] || 'pending') === 'pending')))
      || (type === 'operator' && !operatorSelect.value);
  }
  byId('datasetBatchType').addEventListener('change', () => { renderVersions(); });
  byId('datasetStorageFields').addEventListener('change', () => { submittedBatch = false; byId('datasetBatchResult').hidden = true; updateBatchType(); });
  const script = byId('datasetOperatorScript');
  operatorSelect.addEventListener('change', () => {
    const operator = operators.find(item => item.id === operatorSelect.value);
    byId('datasetOperatorParams').hidden = !operator;
    script.value = operator ? JSON.stringify(Object.fromEntries(operator.parameters.map(param => [param.key, param.default])), null, 2) : '';
    byId('datasetVersionError').hidden = true;
    submittedBatch = false; updateBatchType();
  });
  script.addEventListener('input', () => { submittedBatch = false; byId('datasetVersionError').hidden = true; updateBatchType(); });
  byId('datasetBatchSubmit').addEventListener('click', async () => {
    if (pendingBatch || byId('datasetBatchSubmit').disabled) return;
    const type = byId('datasetBatchType').value;
    const payload = {type, datasets: chosenVersions.map(row => ({id: row.id, version: row.version}))};
    if (type === 'storage') payload.targets = [...byId('datasetStorageFields').querySelectorAll('input:checked')].map(node => node.value);
    else {
      payload.operator_id = operatorSelect.value;
      try {
        payload.params = JSON.parse(script.value);
        if (!payload.params || Array.isArray(payload.params) || typeof payload.params !== 'object') throw new Error();
        const keys = operators.find(item => item.id === operatorSelect.value).parameters.map(param => param.key);
        if (Object.entries(payload.params).some(([key, value]) => !keys.includes(key) || typeof value !== 'string')) throw new Error();
      } catch (_) {
        const error = byId('datasetVersionError');
        error.textContent = '请填写有效的 JSON 参数对象，key 须来自当前算子，参数值使用字符串。'; error.hidden = false; script.focus(); return;
      }
    }
    const error = byId('datasetVersionError'); error.hidden = true;
    pendingBatch = true;
    const controls = [...versionModal.querySelectorAll('button,input,select,textarea')];
    const states = controls.map(node => node.disabled);
    controls.forEach(node => { node.disabled = true; });
    updateBatchType();
    let storageSubmitted = false;
    try {
      const response = await fetch(location.pathname.replace(/\/$/, '') + '/batch-process', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || '提交失败，请重试');
      submittedBatch = true;
      if (type === 'storage') {
        result.results.forEach(resultRow => {
          const candidates = [...chosenVersions, ...items, ...items.flatMap(item => [...(item.versions || []), ...(item.all_versions || [])])];
          candidates.filter(row => row.id === resultRow.id && row.version === resultRow.version).forEach(row => { row.storage_status = resultRow.storage_status; });
        });
      }
      if (type === 'storage') {
        byId('datasetBatchResult').hidden = true;
        storageSubmitted = true;
        showStorageToast(result.results.filter(row => row.run_id).length);
      } else {
        const status = byId('datasetBatchResult'); status.replaceChildren(); status.hidden = false;
        status.appendChild(document.createTextNode('已提交 ' + result.results.length + ' 个任务，等待处理。'));
        const link = document.createElement('a'); link.textContent = '查看进度'; link.href = taskListUrl;
        status.appendChild(link);
      }
    } catch (failure) { error.textContent = failure.message; error.hidden = false; }
    finally { pendingBatch = false; controls.forEach((node, i) => { node.disabled = states[i]; }); updateBatchType(); if (storageSubmitted) closeVersions(); }
  });
  byId('datasetAddButton').addEventListener('click', () => {
    chosenVersions.push({id: '', name: '', versions: []});
    renderVersions();
    byId('datasetVersionRows').lastElementChild.querySelector('.dataset-row-search').focus();
  });
  byId('datasetChooseVersions').addEventListener('click', () => {
    if (!selected.size) return;
    byId('datasetBatchType').value = 'preview';
    chosenVersions = chosenVersions.filter(item => item.id && selected.has(item.id));
    items.filter(item => selected.has(item.id) && !chosenVersions.some(row => row.id === item.id)).forEach(item => chosenVersions.push({...item}));
    renderVersions();
    versionOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    versionModal.classList.add('active');
    versionModal.querySelector('.drawer-close').focus();
  });
  versionModal.querySelectorAll('[data-close-version-modal]').forEach(node => node.addEventListener('click', closeVersions));
  versionModal.addEventListener('click', event => { if (event.target === versionModal) closeVersions(); });
  versionModal.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); closeVersions(); }
    if (event.key === 'Tab') {
      const nodes = [...versionModal.querySelectorAll('button,select,summary,input,textarea')].filter(node => !node.disabled && node.getClientRects().length);
      const first = nodes[0], last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  let selecting = false;
  function refresh() {
    panel.classList.toggle('dataset-tree-selecting', selecting);
    byId('datasetTreeBatch').hidden = !selecting;
    byId('datasetTreeBatchToggle').textContent = selecting ? '取消' : '批量选择';
    byId('datasetTreeBatchToggle').setAttribute('aria-pressed', String(selecting));
    byId('datasetTreeBatchToggle').disabled = !ids.size;
    checkboxes.forEach(node => {
      node.checked = selected.has(node.value);
      node.closest('.dataset-tree-item').classList.toggle('dataset-batch-selected', node.checked);
    });
    folders.forEach(folder => {
      const children = descendants(folder);
      const count = children.filter(id => selected.has(id)).length;
      folder.checked = children.length > 0 && count === children.length;
      folder.indeterminate = count > 0 && count < children.length;
      folder.disabled = !children.length;
    });
    byId('datasetTreeSelectedCount').textContent = '已选 ' + selected.size + ' 项';
    byId('datasetTreeClear').hidden = !selected.size;
    byId('datasetChooseVersions').disabled = !selected.size;
    trigger.setAttribute('aria-disabled', String(!selected.size));
    trigger.disabled = !selected.size;
    status.hidden = true;
  }
  byId('datasetTreeBatchToggle').addEventListener('click', () => {
    selecting = !selecting;
    if (!selecting) selected.clear();
    refresh();
  });
  checkboxes.forEach(node => node.closest('.dataset-tree-item').querySelector('.tree-leaf').addEventListener('click', event => {
    if (!selecting || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    selected.has(node.value) ? selected.delete(node.value) : selected.add(node.value);
    refresh();
  }));
  checkboxes.forEach(node => node.addEventListener('change', () => {
    node.checked ? selected.add(node.value) : selected.delete(node.value);
    refresh();
  }));
  folders.forEach(folder => folder.addEventListener('change', () => {
    descendants(folder).forEach(id => folder.checked ? selected.add(id) : selected.delete(id));
    refresh();
  }));
  byId('datasetTreeClear').addEventListener('click', () => { selected.clear(); refresh(); });
  trigger.addEventListener('click', event => { if (!selected.size || trigger.getAttribute('aria-disabled') === 'true') event.preventDefault(); });
  function legacyCopy(value) {
    const previous = document.activeElement;
    const textarea = document.createElement('textarea');
    textarea.value = value;
    textarea.style.cssText = 'position:fixed;left:-9999px;top:0;';
    document.body.appendChild(textarea);
    textarea.select();
    try { if (!document.execCommand('copy')) throw new Error('copy failed'); }
    finally { textarea.remove(); previous?.focus(); }
  }
  const modal = byId('datasetGenerateModal');
  const content = byId('datasetGenerateContent');
  const copy = byId('datasetGenerateCopy');
  const copyStatus = byId('datasetGenerateStatus');
  let focusBeforePreview = null, previousOverflow = '';
  function closePreview() {
    if (!modal.classList.contains('active')) return;
    modal.classList.remove('active');
    document.body.style.overflow = previousOverflow;
    versionModal.classList.add('active');
    focusBeforePreview?.focus();
  }
  modal.querySelectorAll('[data-close-dataset-preview]').forEach(button => button.addEventListener('click', closePreview));
  modal.addEventListener('click', event => { if (event.target === modal) closePreview(); });
  modal.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); closePreview(); }
    if (event.key === 'Tab') {
      const targets = [...modal.querySelectorAll('button,textarea')].filter(node => !node.disabled);
      const first = targets[0], last = targets[targets.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  trigger.addEventListener('click', () => {
    if (!versionModal.classList.contains('active') || !chosenVersions.length || chosenVersions.some(item => item.publish_status !== '已发布')) return;
    const option = byId('datasetPreviewFields').querySelector('input:checked');
    const kind = option.value;
    const chosen = chosenVersions;
    previewValidated = true; updateYamlValidation();
    try { content.value = formatSelection(chosen, kind); }
    catch (error) {
      updateYamlValidation();
      return;
    }
    byId('datasetVersionError').hidden = true;
    byId('datasetGenerateWarning').hidden = true;
    byId('datasetGenerateTitle').textContent = option.parentElement.textContent + ' · 预览';
    const addressCount = kind === 'yaml' ? 0 : chosen.reduce((count, item) => count + new Set((item.addresses || []).filter(address => address.startsWith(kind + '://'))).size, 0);
    byId('datasetGenerateSummary').textContent = '已选 ' + chosen.length + ' 个数据集' + (kind === 'yaml' ? '' : ' · 生成 ' + addressCount + ' 条地址');
    content.placeholder = '所选数据集暂无对应地址';
    copy.disabled = !content.value;
    copyStatus.textContent = '';
    focusBeforePreview = trigger;
    previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    modal.classList.add('active');
    versionModal.classList.remove('active');
    modal.querySelector('.drawer-close').focus();
  });
  copy.addEventListener('click', async () => {
    if (!content.value) return;
    const value = content.value;
    copy.disabled = true;
    try {
      if (navigator.clipboard?.writeText) {
        try { await navigator.clipboard.writeText(value); } catch (_) { legacyCopy(value); }
      } else legacyCopy(value);
      copyStatus.textContent = '已复制到剪贴板';
      if (window.toast) window.toast(copyStatus.textContent);
    } catch (_) { copyStatus.textContent = '复制失败，请允许浏览器访问剪贴板后重试。'; }
    finally { copy.disabled = !content.value; }
  });
  refresh();
  window.addEventListener('pageshow', event => {
    if (!event.persisted) return;
    closePreview();
    versionModal.classList.remove('active');
    document.body.style.overflow = versionOverflow;
    selecting = false;
    selected.clear();
    refresh();
  });
})();
