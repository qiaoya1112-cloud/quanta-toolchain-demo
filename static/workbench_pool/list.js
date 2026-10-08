(function () {
  'use strict';
  const pool = window.WorkbenchPool;
  const task = pool.payload.task;
  const conflictKey = 'quanta.pool.conflict.' + task.pool + ':' + task.id;
  let records = pool.payload.records;
  const selected = new Set();
  const filters = document.getElementById('wpFilters');
  const rows = document.getElementById('wpRows');
  const selectAll = document.getElementById('wpSelectAll');
  const batch = document.getElementById('wpBatch');
  let activeFilters = {}, busy = false;
  const escape = value => String(value).replace(/[&<>"']/g, value => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[value]));
  function visibleRecords() {
    return records.filter(item => item.status !== 'completed').filter(item => {
      return Object.entries(activeFilters).every(([key, value]) => {
        if (!value) return true;
        if (key === 'from') return item.collected_at.slice(0, 10) >= value;
        if (key === 'to') return item.collected_at.slice(0, 10) <= value;
        if (['supplier', 'status', 'auto_reason'].includes(key)) return item[key] === value;
        return String(item[key]).toLowerCase().includes(value.toLowerCase());
      });
    }).sort((a, b) => Number(b.status === 'processing') - Number(a.status === 'processing'));
  }
  function render() {
    const visible = visibleRecords();
    const pending = visible.filter(item => item.status === 'pending');
    for (const id of selected) if (!pending.some(item => item.id === id)) selected.delete(id);
    document.getElementById('wpCount').textContent = '共 ' + visible.length + ' 条数据';
    document.getElementById('wpSelected').textContent = '已选 ' + selected.size + ' 条';
    const completed = records.filter(item => item.status === 'completed').length;
    document.getElementById('wpSummary').textContent = '本任务池已提交 ' + completed + ' 条。合格 / 不合格结论提交后移出列表；待处理数据可批量开始。';
    batch.disabled = busy || !selected.size;
    selectAll.disabled = busy || !pending.length;
    selectAll.checked = pending.length > 0 && pending.every(item => selected.has(item.id));
    selectAll.indeterminate = selected.size > 0 && !selectAll.checked;
    rows.innerHTML = visible.length ? visible.map(item => {
      const processing = item.status === 'processing';
      const images = ['头部', '左臂', '右臂'].map(view => '<div class="wp-view"><img src="/static/annotation_workbench/assets/frame.png" alt="' + view + '视角示例帧"><span>' + view + ' · 示例</span></div>').join('');
      const ops = Object.entries(item.operators).map(([name, value]) => '<div>' + escape(name) + '：' + escape(value) + '</div>').join('');
      const buttons = (processing && !item.occupied ? '<button data-action="合格">合格</button><button data-action="不合格" class="wp-reject">不合格</button>' : '') + '<button class="wp-process" data-action="process">处理</button>';
      return '<tr data-record-id="' + escape(item.id) + '" class="' + (processing ? 'wp-processing' : '') + '">' +
        '<td><input type="checkbox" aria-label="选择 ' + escape(item.id) + '" ' + ((processing || busy) ? 'disabled ' : '') + (selected.has(item.id) ? 'checked ' : '') + '></td>' +
        '<td class="wp-task-id">' + escape(item.task_id) + '<br><b>' + escape(item.id) + '</b></td>' +
        '<td><div class="wp-preview"><div class="wp-instruction"><b>' + escape(item.instruction) + '</b>：<span>' + escape(item.description) + '</span></div><div class="wp-views">' + images + '</div></div></td>' +
        '<td>' + escape(item.device) + '</td><td>' + escape(item.supplier) + '</td><td>' + escape(item.collected_at) + '</td><td>' + escape(item.standard) + '</td>' +
        '<td><span class="wp-status wp-auto ' + (item.auto_result === '合格' ? 'good' : 'warning') + '">' + escape(item.auto_result) + '</span></td><td class="wp-operators">' + ops + '</td>' +
        '<td><span class="wp-status ' + (processing ? 'processing' : '') + '">' + (processing ? '处理中' : '待处理') + '</span></td>' +
        '<td><div class="wp-row-actions">' + buttons + '</div></td></tr>';
    }).join('') : '<tr><td colspan="11" class="wp-empty">当前没有匹配的数据</td></tr>';
    rows.querySelectorAll('button').forEach(button => { button.disabled = busy; });
  }
  function report(message) {
    const error = document.getElementById('wpError');
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
      } else if (typeof toast === 'function') toast('已将 ' + ids.length + ' 条数据置为处理中');
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
  selectAll.addEventListener('change', () => {
    const checked = selectAll.checked;
    visibleRecords().filter(item => item.status === 'pending').forEach(item => checked ? selected.add(item.id) : selected.delete(item.id));
    render();
  });
  rows.addEventListener('click', event => {
    const button = event.target.closest('button[data-action]');
    if (!button || busy) return;
    const id = button.closest('tr').dataset.recordId;
    if (button.dataset.action === 'process') start([id], true);
    else pool.open(id, button.dataset.action, updated => { records = updated; render(); });
  });
  batch.addEventListener('click', () => start([...selected], false));
  filters.addEventListener('submit', event => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(filters));
    if (values.from && values.to && values.from > values.to) { report('采集开始时间不能晚于结束时间'); return; }
    activeFilters = values; selected.clear(); report(''); render();
  });
  filters.addEventListener('reset', () => { activeFilters = {}; selected.clear(); report(''); render(); });
  // Back-forward caches must not show a stale row after a workbench submission.
  window.addEventListener('pageshow', event => { if (event.persisted) location.reload(); });
  render();
  const notice = sessionStorage.getItem(conflictKey) || pool.payload.notice;
  sessionStorage.removeItem(conflictKey);
  if (notice) report(notice);
})();
