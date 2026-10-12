(function () {
  const payload = JSON.parse(document.getElementById('wbHeldPayload').textContent);
  const dialog = document.createElement('dialog');
  dialog.className = 'wb-held-dialog';
  dialog.innerHTML = '<h3>确认释放</h3><p>释放后，当前已领取的数据将返回任务池。再次开始处理时，将按筛选条件领取数据。</p><p role="alert" class="wb-held-error" hidden></p><footer><button class="btn" data-cancel>取消</button><button class="btn btn-primary" data-confirm>确认释放</button></footer>';
  document.body.appendChild(dialog);
  document.getElementById('wbReleaseHeld').onclick = () => dialog.showModal();
  dialog.querySelector('[data-cancel]').onclick = () => dialog.close();
  dialog.querySelector('[data-confirm]').onclick = async function () {
    this.disabled = true;
    try {
      const response = await fetch(payload.url, {method:'POST', headers:{'Content-Type':'application/json'},body:JSON.stringify({action:payload.action,ids:payload.ids})});
      const result = await response.json();
      if (!response.ok) throw Error(result.error || '释放失败，请重试');
      window.location.reload();
    } catch (error) {
      const notice = dialog.querySelector('[role="alert"]');notice.textContent = error.message;notice.hidden = false;
      this.disabled = false;
    }
  };
})();
