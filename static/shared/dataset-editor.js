(function () {
  'use strict';
  const byId = id => document.getElementById(id);
  const configNode = byId('datasetEditorConfig');
  if (!configNode) return;
  const config = JSON.parse(configNode.textContent);
  const workspace = byId('datasetWorkspace');
  const mask = byId('datasetOperationDrawer');
  const dialog = mask.querySelector('[role="dialog"]');
  const canSaveCurrent = config.publish_status === '未发布';
  const original = config.episodes;
  const originalById = new Map(original.map(row => [row.idx, row]));
  const labels = {remove: '剔除数据', prompt: '修改 Prompt', operator: '执行算子', workflow: '执行工作流'};
  const isAuto = step => step.type === 'operator' || step.type === 'workflow';
  let rows = [], operations = [], selected = new Set(), expandedPromptRows = new Set(), editing = false, saving = false, page = 0;
  let pendingAction = null, previousOverflow = '', confirmFocus = null, operationFocus = null, query = '';
  let lowlevelZhQuery = '', lowlevelEnQuery = '';
  let batchMode = false;
  let changesFocus = null, changesOverflow = '';
  const changesOpen = () => byId('datasetChangesModal').classList.contains('active');
  const pageSize = 10;
  const promptPreviewCount = 3;
  const nodes = new Map();
  const formOpen = () => !byId('datasetOperationForm').hidden;
  const dirty = () => editing && (operations.length > 0 || formOpen());
  const pendingAuto = () => operations.some(isAuto);
  function closeBatchMenu() {
    byId('datasetBatchMenu').hidden = true;
    byId('datasetSelectionAction').setAttribute('aria-expanded', 'false');
  }
  function closeSelectionMenu() {
    byId('datasetSelectionMenu').hidden = true;
    byId('datasetSelectionMenuTrigger').setAttribute('aria-expanded', 'false');
  }
  const changes = () => ({deleted: rows.filter(row => row.deleted).length,
    updated: rows.filter(row => !row.deleted && (row.instr !== originalById.get(row.idx).instr ||
      JSON.stringify(row.lowlevel_prompts) !== JSON.stringify(originalById.get(row.idx).lowlevel_prompts))).length});
  const promptId = replacement => 'custom:' + replacement.zh.trim() + '\x1f' + replacement.en.trim();
  const availablePrompts = () => {
    const prompts = new Map();
    rows.filter(row => !row.deleted && selected.has(row.idx)).forEach(row =>
      (row.lowlevel_prompts || []).forEach(prompt => prompts.set(prompt.id, prompt)));
    return [...prompts.values()];
  };
  const targetFor = (type, id) => (config.catalog[type] || []).find(item => item.id === id);
  const text = (tag, value, className) => {
    const node = document.createElement(tag);
    node.textContent = value;
    if (className) node.className = className;
    return node;
  };
  const button = (label, action, ariaLabel) => {
    const node = text('button', label, 'action-link');
    if (ariaLabel) node.setAttribute('aria-label', ariaLabel);
    node.addEventListener('click', action);
    return node;
  };

  function requestConfirm(message, action) {
    pendingAction = action;
    confirmFocus = document.activeElement;
    byId('datasetConfirmMessage').textContent = message;
    byId('datasetConfirmModal').classList.add('active');
    byId('datasetConfirmModal').querySelector('.btn').focus();
  }

  function preview(plan) {
    const result = original.map(row => ({...row, lowlevel_prompts: (row.lowlevel_prompts || []).map(prompt => ({...prompt})), deleted: false}));
    for (const step of plan) {
      if (isAuto(step)) continue;
      const ids = new Set(step.episode_ids || []);
      const affected = result.filter(row => !row.deleted && (step.scope === 'all' || ids.has(row.idx)));
      if (!affected.length) throw new Error('该操作范围内的数据已被前序操作剔除。');
      if (step.type === 'remove') affected.forEach(row => { row.deleted = true; });
      if (step.type === 'prompt') affected.forEach(row => {
        if (!step.replacements) { row.instr = step.prompt; return; }
        const mapping = new Map(step.replacements.map(item => [item.old_id, item]));
        const prompts = row.lowlevel_prompts.map(prompt => {
          const replacement = mapping.get(prompt.id);
          return replacement ? {id: promptId(replacement), zh: replacement.zh.trim(), en: replacement.en.trim()} : prompt;
        });
        row.lowlevel_prompts = [...new Map(prompts.map(prompt => [prompt.id, prompt])).values()];
      });
      if (result.every(row => row.deleted)) throw new Error('至少需要保留一条数据。');
    }
    return result;
  }

  const filteredRows = () => rows.filter(row =>
    (!query || String(row.rec).toLowerCase().includes(query)) &&
    (!lowlevelZhQuery || (row.lowlevel_prompts || []).some(prompt => prompt.zh.toLowerCase().includes(lowlevelZhQuery))) &&
    (!lowlevelEnQuery || (row.lowlevel_prompts || []).some(prompt => prompt.en.toLowerCase().includes(lowlevelEnQuery))));
  const pageRows = () => filteredRows().slice(page * pageSize, (page + 1) * pageSize);
  function setView(view) {
    window.switchTab(byId(view === 'detail' ? 'datasetDetailViewButton' : 'datasetListViewButton'), view === 'detail' ? 'preview' : 'list');
    if (view === 'detail') window.dispatchEvent(new Event('resize'));
  }
  function refresh(rebuild = false) {
    if (rebuild) {
      rows = preview(operations);
      selected = new Set([...selected].filter(id => rows.some(row => row.idx === id && !row.deleted)));
      renderRows();
      renderOperations();
    }
    byId('datasetPreviewStatus').hidden = !editing;
    byId('datasetPreviewStatus').textContent = editing ? '请先筛选并勾选数据，再通过「批量操作」选择要执行的操作。修改完成后，请在顶部保存。' : '';
    const visibleAvailable = pageRows().filter(row => !row.deleted);
    nodes.forEach((node, id) => {
      node.checkbox.checked = selected.has(id);
      node.checkbox.disabled = saving || pendingAuto() || rows.find(row => row.idx === id).deleted;
      node.root.classList.toggle('dataset-row-selected', selected.has(id));
    });
    const all = byId('datasetSelectAll');
    all.checked = visibleAvailable.length > 0 && visibleAvailable.every(row => selected.has(row.idx));
    all.indeterminate = visibleAvailable.some(row => selected.has(row.idx)) && !all.checked;
    all.disabled = saving || pendingAuto() || !visibleAvailable.length;
    byId('datasetSelectionMenuTrigger').disabled = all.disabled || formOpen();
    if (!editing || byId('datasetSelectionMenuTrigger').disabled) closeSelectionMenu();
    byId('datasetSelectionCount').textContent = '共 ' + filteredRows().length + ' 条';
    byId('datasetSelectedCount').textContent = '已选择 ' + selected.size + ' 条';
    byId('datasetSelectedCount').hidden = !editing || !selected.size;
    byId('datasetClearSelection').hidden = !editing || !selected.size;
    byId('datasetSelectionAction').disabled = !selected.size || saving || formOpen() || pendingAuto();
    if (byId('datasetSelectionAction').disabled) closeBatchMenu();
    byId('datasetClearSelection').disabled = !selected.size || saving || formOpen() || pendingAuto();
    byId('datasetOperationList').querySelectorAll('button').forEach(node => { node.disabled = saving || formOpen(); });
    byId('datasetSelectedScope').disabled = !selected.size;
    byId('datasetSelectedScope').textContent = '选中数据（' + selected.size + ' 条）';
    const kind = byId('datasetOperationType').value;
    const automatic = kind === 'operator' || kind === 'workflow';
    if (!selected.size && byId('datasetOperationScope').value === 'selected') byId('datasetOperationScope').value = 'all';
    byId('datasetOperationScopeHint').textContent = automatic ? '本次仅提交一个任务，处理完成后再手动发起下一项。' : '执行后立即更新列表，保存后生效。';
    const change = changes(), autoCount = operations.filter(isAuto).length;
    const summary = [];
    if (change.deleted) summary.push('已剔除 ' + change.deleted + ' 条');
    if (change.updated) summary.push('已修改 Prompt ' + change.updated + ' 条');
    if (autoCount) summary.push('待提交 ' + autoCount + ' 项处理任务');
    byId('datasetEditSummary').textContent = summary.length ? summary.join(' · ') + '（未保存）' : '暂无修改';
    byId('datasetViewChanges').hidden = !operations.length;
    byId('datasetUndoButton').hidden = !operations.length;
    byId('datasetUndoButton').disabled = saving || formOpen();
    byId('datasetSaveButton').disabled = saving || (!change.deleted && !change.updated && !autoCount);
    byId('datasetSaveButton').textContent = saving ? '提交中…' : '保存为新版本';
    const currentButton = byId('datasetSaveCurrentButton');
    if (currentButton) {
      currentButton.disabled = byId('datasetSaveButton').disabled;
      currentButton.textContent = saving ? '提交中…' : '保存至当前版本';
    }
    byId('datasetAutomationHint').hidden = !autoCount;
    byId('datasetOperationCount').textContent = operations.length;
    byId('datasetOperationEmpty').hidden = operations.length > 0 || formOpen();
    const count = Math.max(1, Math.ceil(filteredRows().length / pageSize));
    byId('datasetPageInfo').textContent = '第 ' + (page + 1) + ' / ' + count + ' 页';
    byId('datasetCurrentPage').textContent = page + 1;
    byId('datasetPrevPage').disabled = page === 0 || saving;
    byId('datasetNextPage').disabled = page + 1 >= count || saving;
  }

  function renderRows() {
    byId('datasetListView').querySelectorAll('.dataset-editor-table thead th').forEach(header => {
      if (['质检规则', '标注规则'].includes(header.textContent.trim())) header.remove();
    });
    nodes.clear();
    byId('datasetEditorRows').replaceChildren();
    pageRows().forEach(row => {
      const tr = document.createElement('tr');
      tr.dataset.episodeId = row.idx;
      if (row.deleted) tr.className = 'dataset-row-deleted';
      const cell = () => tr.appendChild(document.createElement('td'));
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.setAttribute('aria-label', '选择数据 ID ' + row.rec);
      checkbox.addEventListener('change', () => {
        checkbox.checked ? selected.add(row.idx) : selected.delete(row.idx);
        refresh();
      });
      const checkCell = cell(); checkCell.className = 'dpr-selection-cell'; checkCell.hidden = !editing; checkCell.appendChild(checkbox);
      cell().textContent = row.rec;
      const videos = document.createElement('div'); videos.className = 'dpr-video-group';
      if (config.imported && !Object.keys(row.videos || {}).length) {
        videos.appendChild(text('span', '暂无视频', 'muted'));
      } else {
        (config.imported ? Object.keys(row.videos || {}) : ['头部', '左臂', '右臂']).forEach(camera => {
          const thumb = document.createElement('button'); thumb.className = 'vid-thumb';
          thumb.setAttribute('aria-label', '预览数据 ID ' + row.rec + ' ' + camera + '视频');
          thumb.title = camera; thumb.addEventListener('click', () => window.datasetEditor.detail(row.idx));
          if (config.imported && config.media_url) {
            thumb.classList.add('has-video');
            const clip = document.createElement('video');
            clip.muted = true; clip.playsInline = true; clip.preload = 'metadata';
            clip.src = config.media_url + '?episode=' + encodeURIComponent(row.idx) + '&camera=' + encodeURIComponent(camera);
            clip.addEventListener('loadedmetadata', () => { clip.currentTime = Math.min(0.2, clip.duration || 0); }, {once: true});
            thumb.appendChild(clip);
          }
          videos.appendChild(thumb);
        });
      }
      cell().appendChild(videos);
      const promptCell = cell(); promptCell.className = 'dataset-lowlevel-cell';
      if ((row.lowlevel_prompts || []).length) {
        const promptList = text('div', '', 'dataset-lowlevel-list');
        const expanded = expandedPromptRows.has(row.idx);
        promptList.id = 'datasetPromptList-' + row.idx;
        (expanded ? row.lowlevel_prompts : row.lowlevel_prompts.slice(0, promptPreviewCount)).forEach(item => {
          const line = text('div', '', 'dataset-lowlevel-item');
          line.title = item.zh + '\n' + item.en;
          line.append(text('span', item.zh), text('span', item.en, 'dataset-lowlevel-en'));
          promptList.appendChild(line);
        });
        promptCell.appendChild(promptList);
        if (row.lowlevel_prompts.length > promptPreviewCount) {
          const toggle = button(expanded ? '收起' : '展开更多', () => {
            expanded ? expandedPromptRows.delete(row.idx) : expandedPromptRows.add(row.idx);
            renderRows(); refresh();
            byId('datasetEditorRows').querySelector('[data-episode-id="' + row.idx + '"] .dataset-prompt-toggle')?.focus();
          }, (expanded ? '收起' : '展开更多') + '数据 ID ' + row.rec + ' 的 lowlevel prompt');
          toggle.type = 'button'; toggle.classList.add('dataset-prompt-toggle');
          toggle.setAttribute('aria-expanded', String(expanded));
          toggle.setAttribute('aria-controls', promptList.id);
          promptCell.appendChild(toggle);
        }
      } else promptCell.appendChild(text('span', '—', 'muted'));
      const qualityTone = {'合格': 'green', '不合格': 'red', '操作失误': 'orange'}[row.quality_result] || 'gray';
      cell().appendChild(text('span', row.quality_result, 'tag tag-' + qualityTone));
      cell().appendChild(text('span', row.annotation_status, 'tag tag-' + (row.annotation_status === '已标注' ? 'green' : 'gray')));
      const action = button(row.deleted ? '恢复' : '剔除', () => {
        if (saving || formOpen() || pendingAuto()) return;
        if (row.deleted) {
          const plan = operations.map(step => step.type === 'remove'
            ? {...step, episode_ids: step.episode_ids.filter(id => id !== row.idx)} : step)
            .filter(step => step.type !== 'remove' || step.episode_ids.length);
          commitPlan(plan);
        } else {
          commitPlan([...operations, {type: 'remove', scope: 'selected', episode_ids: [row.idx]}]);
        }
      }, (row.deleted ? '恢复' : '剔除') + '数据 ID ' + row.rec);
      action.disabled = saving || formOpen() || pendingAuto() || (!row.deleted && rows.filter(item => !item.deleted).length <= 1);
      const actions = cell(); actions.className = 'dataset-row-actions';
      actions.hidden = !editing;
      if (editing) actions.appendChild(action);
      nodes.set(row.idx, {root: tr, checkbox});
      byId('datasetEditorRows').appendChild(tr);
    });
    if (!pageRows().length) {
      const row = document.createElement('tr'), cell = document.createElement('td');
      cell.colSpan = editing ? 7 : 5; cell.className = 'muted dataset-list-empty';
      cell.textContent = '暂无匹配数据'; row.appendChild(cell); byId('datasetEditorRows').appendChild(row);
    }
  }

  function renderOperations() {
    byId('datasetOperationList').replaceChildren();
    operations.forEach((step, index) => {
      const item = document.createElement('li');
      item.className = 'dataset-operation-item';
      const head = document.createElement('div');
      head.className = 'dataset-operation-head';
      head.appendChild(text('strong', labels[step.type]));
      if (isAuto(step)) {
        head.appendChild(button('取消', () => {
          if (!saving && !formOpen()) commitPlan(operations.filter((_, i) => i !== index));
        }, '取消待提交任务'));
      } else head.appendChild(text('span', '未保存', 'muted'));
      item.appendChild(head);
      item.appendChild(text('div', step.scope === 'all' ? '范围：全部保留数据' : '范围：指定 ' + step.episode_ids.length + ' 条数据', 'muted'));
      if (isAuto(step)) item.appendChild(text('div', targetFor(step.type, step.target_id).name + ' · 保存后提交'));
      const detail = text('div', '', 'dataset-change-detail');
      if (step.scope === 'selected') {
        const dataIds = [...new Set(step.episode_ids.map(id => originalById.get(id).rec))];
        detail.appendChild(text('div', '数据 ID：' + dataIds.join('、')));
      } else detail.appendChild(text('div', '操作范围：全部保留数据'));
      if (step.type === 'prompt') {
        if (step.replacements) step.replacements.forEach(replacement => {
          const old = original.flatMap(row => row.lowlevel_prompts || []).find(prompt => prompt.id === replacement.old_id);
          detail.appendChild(text('div', (replacement.old_zh && replacement.old_en
            ? replacement.old_zh + ' / ' + replacement.old_en
            : old ? old.zh + ' / ' + old.en : replacement.old_id) +
            ' → ' + replacement.zh + ' / ' + replacement.en));
        });
        else detail.appendChild(text('div', '修改后的 Prompt：\n' + step.prompt));
      }
      if (isAuto(step)) {
        const entries = Object.entries(step.params).filter(([, value]) => value);
        entries.forEach(([key, value]) => detail.appendChild(text('div', key + '：' + value)));
        if (!entries.length) detail.appendChild(text('div', '使用默认配置'));
      }
      item.appendChild(detail);
      byId('datasetOperationList').appendChild(item);
    });
  }

  function commitPlan(plan) {
    try {
      preview(plan);
      operations = plan;
      byId('datasetEditError').textContent = '';
      refresh(true);
      return true;
    } catch (error) {
      byId(formOpen() ? 'datasetOperationError' : 'datasetEditError').textContent = error.message;
      return false;
    }
  }

  function closeEditor() {
    window.datasetEditor.closeChanges();
    editing = false;
    workspace.classList.remove('dataset-editing');
    window.datasetEditor.closeOperation();
    operations = []; selected.clear();
    workspace.querySelectorAll('[data-edit-only]').forEach(node => { node.hidden = true; });
    byId('datasetEditButton').hidden = false;
    refresh(true); setView('list');
    const url = new URL(location.href);
    url.searchParams.delete('edit');
    history.replaceState(null, '', url);
    byId('datasetEditButton').focus();
  }

  function syncPromptMappings() {
    const groups = [...byId('datasetPromptMappings').children];
    const chosen = new Set(groups.map(group => group.querySelector('select').value).filter(Boolean));
    groups.forEach((group, index) => {
      group.querySelector('.dataset-prompt-mapping-title').textContent = '第 ' + (index + 1) + ' 组';
      group.querySelector('.dataset-prompt-mapping-remove').hidden = groups.length === 1;
      const select = group.querySelector('select');
      [...select.options].forEach(option => { option.disabled = !!option.value && option.value !== select.value && chosen.has(option.value); });
    });
    byId('datasetAddPromptMapping').disabled = groups.length >= 50 || groups.length >= availablePrompts().length;
  }

  function addPromptMapping() {
    const prompts = availablePrompts();
    const box = byId('datasetPromptMappings');
    if (!prompts.length || box.children.length >= 50) return;
    const group = document.createElement('div'); group.className = 'dataset-prompt-mapping';
    const head = text('div', '', 'dataset-prompt-mapping-head');
    head.appendChild(text('strong', '', 'dataset-prompt-mapping-title'));
    const remove = button('移除', () => { group.remove(); syncPromptMappings(); }, '移除这组 Prompt 修改');
    remove.classList.add('dataset-prompt-mapping-remove'); head.appendChild(remove);
    const oldField = text('div', '', 'fg');
    const oldLabel = text('label', '选择旧 Prompt');
    const old = document.createElement('select'); old.setAttribute('aria-label', '旧 Prompt');
    const empty = text('option', '请选择当前数据已有的 Prompt'); empty.value = ''; old.appendChild(empty);
    prompts.forEach(prompt => {
      const option = text('option', prompt.zh + ' / ' + prompt.en); option.value = prompt.id; old.appendChild(option);
    });
    old.addEventListener('change', () => {
      const prompt = prompts.find(item => item.id === old.value);
      group.querySelector('[data-old-zh]').value = prompt ? prompt.zh : '';
      group.querySelector('[data-old-en]').value = prompt ? prompt.en : '';
      group.querySelector('[data-new-zh]').value = prompt ? prompt.zh : '';
      group.querySelector('[data-new-en]').value = prompt ? prompt.en : '';
      syncPromptMappings();
    });
    oldField.append(oldLabel, old);
    const oldValues = text('div', '', 'dataset-prompt-pair');
    oldValues.appendChild(text('strong', '旧 Prompt', 'dataset-prompt-column-title'));
    [['中文', 'old-zh'], ['英文', 'old-en']].forEach(([label, key]) => {
      const field = text('div', '', 'fg'); field.appendChild(text('label', label));
      const input = document.createElement('textarea'); input.rows = 2; input.readOnly = true; input.setAttribute('data-' + key, '');
      input.setAttribute('aria-label', '旧 Prompt ' + label); field.appendChild(input); oldValues.appendChild(field);
    });
    const newValues = text('div', '', 'dataset-prompt-pair');
    newValues.appendChild(text('strong', '新 Prompt', 'dataset-prompt-column-title'));
    [['中文', 'new-zh'], ['英文', 'new-en']].forEach(([label, key]) => {
      const field = text('div', '', 'fg'); field.appendChild(text('label', label));
      const input = document.createElement('textarea'); input.rows = 2; input.maxLength = 10000; input.setAttribute('data-' + key, '');
      input.placeholder = '请输入' + label; input.setAttribute('aria-label', '新 Prompt ' + label);
      field.appendChild(input); newValues.appendChild(field);
    });
    const columns = text('div', '', 'dataset-prompt-columns');
    columns.append(oldValues, newValues);
    group.append(head, oldField, columns); box.appendChild(group);
    syncPromptMappings(); old.focus();
  }

  window.datasetEditor = {
    showChanges() {
      if (!editing || saving || formOpen() || changesOpen()) return;
      changesFocus = document.activeElement;
      changesOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      byId('datasetChangesModal').classList.add('active');
      byId('datasetChangesModal').querySelector('.drawer-close').focus();
    },
    closeChanges() {
      if (!changesOpen()) return;
      byId('datasetChangesModal').classList.remove('active');
      document.body.style.overflow = changesOverflow;
      if (changesFocus) changesFocus.focus();
    },
    undo() {
      if (!editing || saving || formOpen() || !operations.length) return;
      commitPlan(operations.slice(0, -1));
    },
    view(view) { setView(view); },
    detail(id) {
      setView('detail');
      if (window.setEp_dsv2) window.setEp_dsv2(id);
      byId('datasetDetailViewButton').focus();
    },
    filter(clear = false) {
      closeSelectionMenu();
      if (clear) ['datasetDataQuery', 'datasetLowlevelZhQuery', 'datasetLowlevelEnQuery'].forEach(id => { byId(id).value = ''; });
      query = byId('datasetDataQuery').value.trim().toLowerCase();
      lowlevelZhQuery = byId('datasetLowlevelZhQuery').value.trim().toLowerCase();
      lowlevelEnQuery = byId('datasetLowlevelEnQuery').value.trim().toLowerCase();
      page = 0; refresh(true);
    },
    expandPrompts(expand) {
      expandedPromptRows = new Set(expand ? rows.filter(row => (row.lowlevel_prompts || []).length > promptPreviewCount).map(row => row.idx) : []);
      renderRows(); refresh();
    },
    selectPage(checked) {
      if (!editing || saving || pendingAuto()) return;
      pageRows().filter(row => !row.deleted).forEach(row => { checked ? selected.add(row.idx) : selected.delete(row.idx); });
      refresh();
    },
    start() {
      if (editing || config.processing_status !== 'ready') return;
      operations = []; selected = new Set(); page = 0;
      byId('datasetOperationForm').hidden = true;
      byId('datasetEditError').textContent = '';
      editing = true;
      workspace.classList.add('dataset-editing');
      workspace.querySelectorAll('[data-edit-only]').forEach(node => { node.hidden = false; });
      byId('datasetEditButton').hidden = true;
      setView('list'); refresh(true);
      byId('datasetDataQuery').focus();
    },
    cancel() {
      if (saving) return;
      if (dirty()) requestConfirm('放弃本次编辑？未保存的操作将丢失。', closeEditor);
      else closeEditor();
    },
    closeConfirm() {
      byId('datasetConfirmModal').classList.remove('active'); pendingAction = null;
      if (confirmFocus) confirmFocus.focus();
    },
    confirmAction() {
      const action = pendingAction;
      this.closeConfirm();
      if (action) action();
    },
    selectAll(checked) {
      if (!editing || saving || formOpen() || pendingAuto()) return;
      selected = checked ? new Set(filteredRows().filter(row => !row.deleted).map(row => row.idx)) : new Set();
      refresh();
    },
    toggleSelectionMenu() {
      if (byId('datasetSelectionMenuTrigger').disabled) return;
      if (!byId('datasetSelectionMenu').hidden) { closeSelectionMenu(); return; }
      closeBatchMenu();
      const trigger = byId('datasetSelectionMenuTrigger').getBoundingClientRect();
      const menu = byId('datasetSelectionMenu');
      menu.hidden = false;
      menu.style.left = Math.max(8, Math.min(trigger.left, innerWidth - menu.offsetWidth - 8)) + 'px';
      menu.style.top = (trigger.bottom + menu.offsetHeight + 8 > innerHeight ? trigger.top - menu.offsetHeight - 4 : trigger.bottom + 4) + 'px';
      byId('datasetSelectionMenuTrigger').setAttribute('aria-expanded', 'true');
    },
    selectScope(scope) {
      closeSelectionMenu();
      if (!editing || saving || formOpen() || pendingAuto()) return;
      if (scope === 'all') this.selectAll(true);
      else this.selectPage(true);
    },
    page(delta) { closeSelectionMenu(); page = Math.max(0, Math.min(page + delta, Math.ceil(filteredRows().length / pageSize) - 1)); refresh(true); },
    toggleBatchMenu() {
      if (byId('datasetSelectionAction').disabled) return;
      closeSelectionMenu();
      const open = byId('datasetBatchMenu').hidden;
      byId('datasetBatchMenu').hidden = !open;
      byId('datasetSelectionAction').setAttribute('aria-expanded', String(open));
    },
    batch(type) {
      closeBatchMenu();
      if (!editing || saving || formOpen() || pendingAuto() || !selected.size) return;
      const ids = [...selected];
      if (type === 'remove') {
        if (ids.length >= rows.filter(row => !row.deleted).length) {
          byId('datasetEditError').textContent = '至少需要保留一条数据。'; return;
        }
        commitPlan([...operations, {type: 'remove', scope: 'selected', episode_ids: ids}]);
      } else if (type === 'prompt') this.openOperation('selected', 'prompt');
    },
    openOperation(scope, type = '') {
      if (!editing || saving || formOpen() || pendingAuto()) return;
      batchMode = !!type;
      closeBatchMenu();
      operationFocus = document.activeElement;
      previousOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      mask.classList.add('active');
      byId('datasetOperationForm').hidden = false;
      byId('datasetOperationType').value = type;
      byId('datasetOperationTypeField').hidden = batchMode;
      byId('datasetOperationScopeField').hidden = batchMode;
      byId('datasetPromptSelection').hidden = !batchMode;
      byId('datasetPromptSelection').textContent = '已选择 ' + selected.size + ' 条数据';
      byId('datasetOperationTitle').textContent = batchMode ? '批量修改 Prompt' : '执行操作';
      byId('datasetOperationScope').value = scope;
      byId('datasetPromptMappings').replaceChildren();
      byId('datasetOperationError').textContent = '';
      this.changeType();
      if (type === 'prompt') byId('datasetPromptMappings').querySelector('select')?.focus();
      else byId('datasetOperationType').focus();
    },
    addPromptMapping() { addPromptMapping(); },
    closeOperation() {
      if (saving) return;
      if (mask.classList.contains('active')) {
        mask.classList.remove('active'); document.body.style.overflow = previousOverflow;
        if (operationFocus) operationFocus.focus();
      }
      byId('datasetOperationForm').hidden = true;
      byId('datasetOperationError').textContent = '';
      refresh(true);
    },
    changeType() {
      const type = byId('datasetOperationType').value;
      const automatic = type === 'operator' || type === 'workflow';
      byId('datasetPromptField').hidden = type !== 'prompt';
      const hasPrompts = availablePrompts().length > 0;
      byId('datasetPromptEmpty').hidden = type !== 'prompt' || hasPrompts;
      byId('datasetAddPromptMapping').hidden = type === 'prompt' && !hasPrompts;
      byId('datasetExecuteOperation').disabled = type === 'prompt' && !hasPrompts;
      if (type === 'prompt' && !byId('datasetPromptMappings').children.length) addPromptMapping();
      byId('datasetAutomationFields').hidden = !automatic;
      byId('datasetOperationScope').disabled = automatic || batchMode;
      byId('datasetExecuteOperation').textContent = automatic ? '确认任务' : '确认修改';
      if (automatic) byId('datasetOperationScope').value = 'all';
      byId('datasetOperationError').textContent = '';
      const target = byId('datasetOperationTarget');
      target.replaceChildren();
      if (automatic) {
        byId('datasetOperationTargetLabel').textContent = type === 'operator' ? '算子' : '工作流';
        const empty = text('option', type === 'operator' ? '请选择算子' : '请选择工作流');
        empty.value = ''; target.appendChild(empty);
        config.catalog[type].forEach(item => {
          const option = text('option', item.name); option.value = item.id; target.appendChild(option);
        });
      }
      this.changeTarget();
      renderRows(); refresh();
    },
    changeTarget() {
      const type = byId('datasetOperationType').value;
      const target = targetFor(type, byId('datasetOperationTarget').value);
      byId('datasetOperationTargetDescription').textContent = target ? target.description : '';
      const box = byId('datasetOperationParams'); box.replaceChildren();
      const params = target ? target.parameters : [];
      byId('datasetNoParams').hidden = !target || !!params.length;
      params.forEach(field => {
        const row = document.createElement('tr');
        row.appendChild(text('td', field.key, 'pk'));
        const cell = document.createElement('td');
        const input = document.createElement('input'); input.value = field.default;
        input.dataset.paramKey = field.key; input.className = 'dataset-operation-param';
        input.setAttribute('aria-label', '参数 ' + field.key); input.maxLength = 10000;
        input.placeholder = '填写值'; cell.appendChild(input); row.appendChild(cell); box.appendChild(row);
      });
    },
    addOperation() {
      const type = byId('datasetOperationType').value;
      const scope = byId('datasetOperationScope').value;
      const step = {type, scope};
      const fail = message => { byId('datasetOperationError').textContent = message; };
      if (operations.length >= 100) return fail('本次编辑最多执行 100 项操作，请先保存。');
      if (pendingAuto()) return fail('请先保存并等待当前任务处理完成。');
      if (!type) return fail('请选择操作类型。');
      if (scope === 'selected') {
        if (!selected.size) return fail('请先选择数据。');
        step.episode_ids = [...selected];
      }
      if (type === 'remove') {
        step.episode_ids = scope === 'all' ? rows.filter(row => !row.deleted).map(row => row.idx) : [...selected];
        step.scope = 'selected';
      }
      if (type === 'prompt') {
        const groups = [...byId('datasetPromptMappings').children];
        if (!groups.length) return fail('请添加 Prompt 修改。');
        step.replacements = groups.map(group => ({old_id: group.querySelector('select').value,
          old_zh: group.querySelector('[data-old-zh]').value, old_en: group.querySelector('[data-old-en]').value,
          zh: group.querySelector('[data-new-zh]').value.trim(), en: group.querySelector('[data-new-en]').value.trim()}));
        if (step.replacements.some(item => !item.old_id || !item.zh || !item.en))
          return fail('请选择旧 Prompt，并填写新 Prompt 的中文和英文。');
        if (new Set(step.replacements.map(item => item.old_id)).size !== step.replacements.length)
          return fail('同一个旧 Prompt 只能修改一次。');
        const unchanged = step.replacements.findIndex(item => item.zh === item.old_zh && item.en === item.old_en);
        if (unchanged !== -1) return fail('第 ' + (unchanged + 1) + ' 组的新 Prompt 与旧 Prompt 相同，请修改后再确认。');
      }
      if (isAuto(step)) {
        step.target_id = byId('datasetOperationTarget').value;
        if (!step.target_id) return fail('请选择' + (type === 'operator' ? '算子' : '工作流') + '。');
        step.params = Object.fromEntries(Array.from(byId('datasetOperationParams').querySelectorAll('input')).map(input => [input.dataset.paramKey, input.value]));
      }
      if (!isAuto(step)) {
        step.episode_ids = rows.filter(row => !row.deleted && (scope === 'all' || selected.has(row.idx))).map(row => row.idx);
        step.scope = 'selected';
      }
      const plan = [...operations, step];
      if (commitPlan(plan)) this.closeOperation();
    },
    async save(saveMode = 'new') {
      if (saving || byId('datasetSaveButton').disabled || (saveMode === 'current' && !canSaveCurrent)) return;
      if (formOpen()) {
        byId('datasetEditError').textContent = '请先执行或取消正在配置的操作。';
        return;
      }
      saving = true;
      workspace.classList.add('dataset-saving');
      refresh(true);
      try {
        const response = await fetch(workspace.dataset.saveUrl, {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({base_version: config.version, save_mode: saveMode, operations})
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || '保存失败，请重试');
        editing = false;
        const url = new URL(location.href);
        url.searchParams.set('ver', result.version);
        url.searchParams.delete('edit');
        url.searchParams.delete('view');
        if (result.processing_status === 'queued') url.searchParams.set('tab', 'version');
        else url.searchParams.set('tab', 'list');
        sessionStorage.setItem('datasetSaved:' + workspace.dataset.saveUrl, JSON.stringify({
          version: result.version, mode: result.save_mode, queued: result.processing_status === 'queued'
        }));
        location.href = url.toString();
      } catch (error) {
        byId('datasetEditError').textContent = error.message || '保存失败，请重试';
      } finally {
        saving = false; workspace.classList.remove('dataset-saving'); refresh(true);
      }
    }
  };

  window.addEventListener('beforeunload', event => {
    if (dirty()) { event.preventDefault(); event.returnValue = ''; }
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('#datasetSelectionMenu, #datasetSelectionMenuTrigger')) closeSelectionMenu();
    const link = event.target.closest('a[href]');
    if (!dirty() || !link || link.getAttribute('href').startsWith('#')) return;
    event.preventDefault();
    if (!saving) requestConfirm('离开将丢弃未保存的操作，是否继续？', () => {
      editing = false; location.href = link.href;
    });
  }, true);
  document.addEventListener('click', event => {
    if (!event.target.closest('.dataset-batch-menu')) closeBatchMenu();
    const picker = byId('datasetVersionPicker');
    if (picker && !picker.contains(event.target)) picker.open = false;
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !byId('datasetSelectionMenu').hidden) {
      closeSelectionMenu(); byId('datasetSelectionMenuTrigger').focus(); event.preventDefault(); return;
    }
    if (event.key === 'Escape' && !byId('datasetBatchMenu').hidden) {
      closeBatchMenu(); byId('datasetSelectionAction').focus(); event.preventDefault(); return;
    }
    const picker = byId('datasetVersionPicker');
    if (event.key === 'Escape' && picker && picker.open) {
      picker.open = false; picker.querySelector('summary').focus(); event.preventDefault(); return;
    }
    if (!editing) return;
    const confirming = byId('datasetConfirmModal').classList.contains('active');
    if (event.key === 'Escape') {
      event.preventDefault(); event.stopImmediatePropagation();
      if (confirming) window.datasetEditor.closeConfirm();
      else if (formOpen()) window.datasetEditor.closeOperation();
      else if (changesOpen()) window.datasetEditor.closeChanges();
    }
    if (event.key === 'Tab' && (confirming || formOpen() || changesOpen())) {
      const activeDialog = confirming ? byId('datasetConfirmModal') : changesOpen() ? byId('datasetChangesModal') : dialog;
      const focusable = Array.from(activeDialog.querySelectorAll('button,input,textarea,select,summary,[tabindex="0"]'))
        .filter(node => !node.disabled && node.getClientRects().length);
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog)) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialog)) {
        event.preventDefault(); first.focus();
      }
    }
  }, true);
  document.addEventListener('scroll', closeSelectionMenu, true);
  window.addEventListener('resize', closeSelectionMenu);
  const params = new URLSearchParams(location.search);
  refresh(true);
  if (params.get('edit') === '1') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => window.datasetEditor.start());
    else window.datasetEditor.start();
  }
  const savedKey = 'datasetSaved:' + workspace.dataset.saveUrl;
  let saved;
  try { saved = JSON.parse(sessionStorage.getItem(savedKey)); } catch (_) { saved = null; }
  if (saved && saved.version === config.version) {
    sessionStorage.removeItem(savedKey);
    document.addEventListener('DOMContentLoaded', () => {
      const message = saved.mode === 'current' ? '已保存至当前版本 ' : '已保存为新版本 ';
      if (window.toast) window.toast(message + config.version + (saved.queued ? '，处理任务已提交' : ''));
    });
  }
})();
