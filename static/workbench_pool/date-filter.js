(function () {
  const form = document.getElementById('wbFilterForm');
  const start = form?.querySelector('[name="collected_from"]');
  const end = form?.querySelector('[name="collected_to"]');
  if (!start || !end) return;
  const day = value => Date.parse(value + 'T00:00:00Z');
  const shifted = (value, days) => new Date(day(value) + days * 86400000).toISOString().slice(0, 10);
  function validate() {
    start.setCustomValidity(''); end.setCustomValidity('');
    end.min = start.value || ''; end.max = start.value ? shifted(start.value, 29) : '';
    start.min = end.value ? shifted(end.value, -29) : ''; start.max = end.value || '';
    if (start.value && !end.value) end.setCustomValidity('请选择采集结束日期');
    else if (end.value && !start.value) start.setCustomValidity('请选择采集开始日期');
    else if (start.value && end.value) {
      const days = (day(end.value) - day(start.value)) / 86400000;
      if (days < 0 || days > 29) end.setCustomValidity('采集时间范围最多30天，结束日期不能早于开始日期');
    }
  }
  start.addEventListener('input', validate); end.addEventListener('input', validate);
  form.addEventListener('submit', event => { validate(); if (!form.reportValidity()) event.preventDefault(); });
  form.addEventListener('reset', () => setTimeout(validate, 0));
  validate();
})();
