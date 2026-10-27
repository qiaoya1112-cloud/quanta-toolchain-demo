(function () {
  'use strict';
  const pool = window.WorkbenchPool;
  const task = pool.payload.task;
  const conflictKey = 'quanta.pool.conflict.' + task.pool + ':' + task.id;
  let records = pool.payload.records;
  const selected = new Set();
  const filters = document.getElementById('wpFilters');
  const filterToggle = document.getElementById('wpFilterToggle');
  const advancedFilters = document.getElementById('wpAdvancedFilters');
  const rows = document.getElementById('wpRows');
  const selectAll = document.getElementById('wpSelectAll');
  const batch = document.getElementById('wpBatch');
  let activeFilters = {}, busy = false;
  function visibleRecords() {
    return records.filter(item => (task.compact_list || item.status !== 'completed') && (!task.job_batch || (item.job_batch || item.id) === task.job_batch)).filter(item => {
      return Object.entries(activeFilters).every(([key, value]) => {
        if (!value) return true;
        if (key === 'time_node') return true;
        if (key === 'from' || key === 'to') {
          const time = activeFilters.time_node === 'collection_qc' ? item.collection_qc_at : activeFilters.time_node === 'self_check' ? item.self_checked_at : item.collected_at;
          return Boolean(time) && (key === 'from' ? time.slice(0, 10) >= value : time.slice(0, 10) <= value);
        }
        if (key === 'status') return item.status === value;
        if (key === 'supplier_id') return String(item.supplier_id || '').toLowerCase().includes(value.toLowerCase());
        if (key === 'operator') return window.WorkbenchPoolRows.history(item, task).some(entry => String(entry.name || '').toLowerCase().includes(value.toLowerCase()));
        return String(item[key]).toLowerCase().includes(value.toLowerCase());
      });
    }).sort((a, b) => Number(b.status === 'processing') - Number(a.status === 'processing'));
  }
  function render() {
    const visible = visibleRecords();
    const batchCount = document.getElementById('wpBatchCount');
    if (batchCount) batchCount.textContent = '共 ' + records.length + ' 条数据';
    const pending = visible.filter(item => item.status === 'pending');
    for (const id of selected) if (!pending.some(item => item.id === id)) selected.delete(id);
    if (!task.job_center && !task.compact_list) {
      document.getElementById('wpCount').textContent = '共 ' + visible.length + ' 条数据';
      document.getElementById('wpSelected').textContent = '已选' + selected.size + '条，最多同时执行20条';
      batch.disabled = busy || !selected.size;
      selectAll.disabled = busy || !pending.length;
      selectAll.checked = pending.length > 0 && pending.every(item => selected.has(item.id));
      selectAll.indeterminate = selected.size > 0 && !selectAll.checked;
    }
    rows.innerHTML = window.WorkbenchPoolRows.render(visible, task, {busy, selected});
    rows.querySelectorAll('button').forEach(button => { button.disabled = busy; });
  }
  let validationToastTimer;
  function report(message) {
    const error = document.getElementById('wpError');
    if (message && message.includes('存在未质检的数据')) {
      error.textContent = ''; error.hidden = true;
      const notice = document.getElementById('wpValidationToast');
      clearTimeout(validationToastTimer);
      notice.textContent = message; notice.hidden = false;
      validationToastTimer = setTimeout(() => { notice.hidden = true; }, 3000);
      return;
    }
    if (message && message.includes('数据已被其他人占用或处理')) {
      error.textContent = ''; error.hidden = true;
      if (typeof toast === 'function') toast('当前批次已变化，请刷新后重试');
      return;
    }
    error.textContent = message; error.hidden = !message;
    if (message) error.scrollIntoView({block: 'center', inline: 'nearest'});
  }
  async function start(ids, navigate) {
    if (busy) return;
    busy = true; report(''); render();
    try {
      records = await pool.action({action: 'start', ids});
      selected.clear();
      if (navigate) {
        location.href = '/data/workbench-v2/edit?' + new URLSearchParams({task:task.id, recording_id: ids[0], pool_id:task.pool, mode:'quality', entry:'pool'});
      } else if (typeof toast === 'function') toast('已将 ' + ids.length + ' 条数据领取成功');
    } catch (error) {
      if (error.code === 'record_occupied') {
        sessionStorage.setItem(conflictKey, '数据已被其他人占用或处理，已刷新任务池列表，请选择其他数据');
        location.reload();
        return;
      }
      report(error.message);
    }
    finally { busy = false; render(); }
  }
  rows.addEventListener('change', event => {
    if (event.target.type !== 'checkbox') return;
    const id = event.target.closest('tr').dataset.recordId;
    if (event.target.checked) selected.add(id); else selected.delete(id);
    render();
  });
  selectAll?.addEventListener('change', () => {
    const checked = selectAll.checked;
    visibleRecords().filter(item => item.status === 'pending').forEach(item => checked ? selected.add(item.id) : selected.delete(item.id));
    render();
  });
  rows.addEventListener('click', async event => {
    const button = event.target.closest('button[data-action]');
    if (!button || busy) return;
    const id = button.closest('tr').dataset.recordId;
    if (button.dataset.action === 'process' && task.process_url) location.href = task.process_url + '&recording_id=' + encodeURIComponent(id);
    else if (button.dataset.action === 'process') start([id], true);
    else {
      const item = records.find(record => record.id === id);
      if (item.status !== 'processing') {
        try { records = await pool.action({action:'start', ids:[id]}); render(); }
        catch (error) { report(error.message); return; }
      }
      pool.open(id, button.dataset.action, updated => { records = updated; render(); });
    }
  });
  batch?.addEventListener('click', () => start([...selected], false));
  document.getElementById('wpBatchActions')?.addEventListener('click', async event => {
    const button = event.target.closest('[data-batch-action]');
    if (!button || busy) return;
    const ids = visibleRecords().map(item => item.id);
    if (!ids.length) { report('当前没有可操作的数据'); return; }
    if (button.dataset.batchAction === 'submit' && visibleRecords().some(item => !['合格','不合格','失误'].includes(item.result))) {
      report('存在未质检的数据，请完成质检后再提交'); return;
    }
    const confirmed = await new Promise(resolve => {
      const mask = document.getElementById('wpBatchConfirm');
      const remark = document.getElementById('wpBatchRemark');
      const error = document.getElementById('wpBatchConfirmError');
      const requiresRemark = button.dataset.batchAction === 'reject';
      document.getElementById('wpBatchRemarkField').hidden = button.dataset.batchAction === 'release';
      document.getElementById('wpBatchRemarkRequirement').textContent = requiresRemark ? '（必填）' : '（选填）';
      remark.value = ''; remark.required = requiresRemark; error.hidden = true;
      document.getElementById('wpBatchConfirmTitle').textContent = '确认' + button.textContent;
      document.getElementById('wpBatchConfirmText').textContent = '确认' + button.textContent + '当前批次的 ' + ids.length + ' 条数据？' + (button.dataset.batchAction === 'submit' && task.node === '采集验收' ? '提交后将清除本批数据的错误原因，请确认已完成核验。' : '');
      mask.hidden = false;
      const finish = value => { mask.hidden = true; resolve(value); button.focus(); };
      document.getElementById('wpBatchCancel').onclick = () => finish(false);
      document.getElementById('wpBatchConfirmButton').onclick = () => {
        if (requiresRemark && !remark.value.trim()) {
          error.textContent = '请输入驳回说明'; error.hidden = false; remark.focus(); return;
        }
        finish(true);
      };
      document.getElementById('wpBatchCancel').focus();
    });
    if (!confirmed) return;
    busy = true; report('');
    const buttons = [...document.querySelectorAll('[data-batch-action]')];
    buttons.forEach(item => { item.disabled = true; });
    try {
      records = await pool.action({action:'batch_' + button.dataset.batchAction, ids,
        remark:document.getElementById('wpBatchRemark').value.trim()});
      if (!task.return_to_workbench) {
        if (document.getElementById('wpContinueProcessing')?.checked) {
          window.location.reload();
        } else {
          const next = new URL(window.location.href);
          next.pathname = next.pathname.replace(/\/records$/, '');
          next.searchParams.delete('entry');
          window.location.assign(next.href);
        }
        return;
      }
      selected.clear(); render();
      if (typeof toast === 'function') toast('操作成功，已加载新一批数据');
    } catch (error) { report(error.message); }
    finally { busy = false; buttons.forEach(item => { item.disabled = false; }); render(); }
  });
  filterToggle?.addEventListener('click', () => {
    const expanded = advancedFilters.hidden;
    advancedFilters.hidden = !expanded;
    filterToggle.setAttribute('aria-expanded', String(expanded));
    filterToggle.innerHTML = (expanded ? '收起' : '展开') + ' <span aria-hidden="true">' + (expanded ? '⌃' : '⌄') + '</span>';
  });
  filters?.addEventListener('submit', event => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(filters));
    if ((values.from || values.to) && !values.time_node) { report('请先选择操作节点，再设置时间范围'); return; }
    if (values.from && values.to && values.from > values.to) { report('操作开始时间不能晚于结束时间'); return; }
    activeFilters = values; selected.clear(); report(''); render();
  });
  filters?.addEventListener('reset', () => { activeFilters = {}; selected.clear(); report(''); render(); });
  // Back-forward caches must not show a stale row after a workbench submission.
  window.addEventListener('pageshow', event => { if (event.persisted) location.reload(); });
  render();
  const notice = sessionStorage.getItem(conflictKey) || pool.payload.notice;
  sessionStorage.removeItem(conflictKey);
  if (notice) report(notice);
})();
