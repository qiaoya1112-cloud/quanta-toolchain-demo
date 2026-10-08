/* Shared confirmations for the pool list and its quality workbench. */
(function () {
  'use strict';
  const payload = JSON.parse(document.getElementById('wpPayload').textContent);
  const task = payload.task;
  const mask = document.getElementById('wpDecision');
  const confirm = document.getElementById('wpConfirmDecision');
  const cancel = document.getElementById('wpCancelDecision');
  const reason = document.getElementById('wpReason');
  const remark = document.getElementById('wpRemark');
  const error = document.getElementById('wpDecisionError');
  let pending = null, submitting = false, previousFocus = null;
  const listUrl = '/data/workbench-v2/pools/' + encodeURIComponent(task.pool) + '/records?source=' + encodeURIComponent(task.id);
  async function action(body) {
    const response = await fetch(listUrl.replace('/records?', '/records/actions?'), {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
    });
    const result = await response.json();
    if (!response.ok) {
      const error = new Error(result.error || '操作失败，请重试');
      error.code = result.code; error.status = response.status;
      throw error;
    }
    return result.records;
  }
  function close() {
    if (submitting) return;
    mask.hidden = true;
    pending = null;
    if (previousFocus && previousFocus.isConnected) previousFocus.focus();
  }
  function open(id, result, onComplete) {
    previousFocus = document.activeElement;
    pending = {id, result, onComplete};
    document.getElementById('wpDecisionTitle').textContent = result === '合格' ? '确认标记为合格' : '标记为不合格';
    document.getElementById('wpDecisionCopy').textContent = 'Recording ' + id + ' · ' + task.node + '。确认后将提交结论，并移出当前任务池。';
    document.getElementById('wpRejectionFields').hidden = result !== '不合格';
    reason.value = ''; remark.value = ''; error.hidden = true;
    document.getElementById('wpRemarkRequired').textContent = '（可选）';
    mask.hidden = false;
    (result === '不合格' ? reason : cancel).focus();
  }
  reason.addEventListener('change', () => {
    document.getElementById('wpRemarkRequired').textContent = reason.value === '其他' ? '（必填）' : '（可选）';
  });
  cancel.addEventListener('click', close);
  mask.addEventListener('click', event => { if (event.target === mask) close(); });
  mask.addEventListener('keydown', event => {
    if (event.key === 'Escape') close();
    if (event.key === 'Tab') {
      const fields = [...mask.querySelectorAll('button,select,textarea')].filter(item => !item.disabled && item.getClientRects().length);
      const first = fields[0], last = fields[fields.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  confirm.addEventListener('click', async () => {
    if (!pending || submitting) return;
    error.hidden = true;
    if (pending.result === '不合格' && (!reason.value || (reason.value === '其他' && !remark.value.trim()))) {
      error.textContent = !reason.value ? '请选择不合格原因' : '请填写其他原因说明'; error.hidden = false;
      (!reason.value ? reason : remark).focus(); return;
    }
    submitting = true; confirm.disabled = true; cancel.disabled = true;
    try {
      const saved = pending;
      const records = await action({action: 'finish', ids: [saved.id], result: saved.result,
                                    reason: reason.value, remark: remark.value});
      submitting = false; close(); saved.onComplete(records);
      if (typeof toast === 'function') toast('已提交 · ' + saved.result);
    } catch (err) { error.textContent = err.message; error.hidden = false; }
    finally { submitting = false; confirm.disabled = false; cancel.disabled = false; }
  });
  window.WorkbenchPool = {payload, listUrl, action, open};
})();
