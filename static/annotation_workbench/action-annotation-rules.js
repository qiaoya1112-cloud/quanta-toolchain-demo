(function (root) {
  'use strict';
  const rule = Object.freeze({ id: 'ACTION-S027-001', version: '1.0' });
  const elementTypes = {
    Object: { label: '物体', values: ['遥控器', '纸盒', '书本', '笔记本', '把手'] },
    Location: { label: '位置', values: ['桌面', '抽屉', '书架'] },
    Container: { label: '容器', values: ['杯子', '碗', '收纳盒'] },
    Fruit: { label: '水果', values: ['苹果', '草莓', '香蕉'] },
    Tool: { label: '工具', values: ['剪刀', '夹子', '清洁刷'] }
  };
  const templates = {
    '观察并整理桌面物品': '观察并整理 {Object} 至 {Location}',
    '选择并移动遥控器到目标位置': '选择并移动 {Object}',
    '打开或关闭抽屉': '使用 {Object} 打开或关闭 {Location}',
    '调整纸盒摆放位置': '调整 {Object} 的摆放位置',
    '整理散落书本': '整理散落的 {Object}',
    '将书本竖直放回书架': '将 {Object} 竖直放回 {Location}',
    '按类别整理笔记本': '按类别整理 {Object}',
    '放回指定位置': '放回 {Location}',
    '拿起': '拿起 {Object}',
    '移动': '将 {Object} 移动至 {Location}',
    '放置': '将 {Object} 放置在 {Location}',
    '整理': '整理 {Object}',
    '将水果放入容器': '将 {Fruit} 放入 {Container}',
    '将两种水果放入容器': '将 {Fruit}、{Fruit} 放入 {Container}',
    '用工具夹取水果': '使用 {Tool} 夹取 {Fruit}',
    '将物体放入容器': '将 {Object} 放入 {Container}',
    '将容器放到指定位置': '将 {Container} 放到 {Location}',
    '用工具整理两个物体': '使用 {Tool} 整理 {Object} 和 {Object}',
    '整理两个物体': '整理 {Object} 和 {Object}'
  };
  const typeByValue = Object.fromEntries(Object.entries(elementTypes).flatMap(([type, group]) => group.values.map(value => [value, type])));
  const slots = Object.fromEntries(Object.entries(templates).map(([name, label]) => {
    const counts = {};
    for (const match of label.matchAll(/\{([A-Za-z]+)\}/g)) counts[match[1]] = (counts[match[1]] || 0) + 1;
    return [name, counts];
  }));
  const countElements = values => values.reduce((counts, value) => {
    const type = typeByValue[value];
    if (type) counts[type] = (counts[type] || 0) + 1;
    return counts;
  }, {});
  const sameCounts = (left, right) => Boolean(left && right) && [...new Set([...Object.keys(left), ...Object.keys(right)])].every(type => (left[type] || 0) === (right[type] || 0));
  const signature = descriptions => {
    if (!descriptions.length) return {};
    const first = slots[descriptions[0]];
    return first && descriptions.every(name => sameCounts(slots[name], first)) ? first : null;
  };
  function validate(data) {
    if (!data?.elements?.length || !data?.descriptions?.length) return { valid: false, message: '动作元素和动作描述不能为空' };
    if (data.elements.some(value => !Object.hasOwn(typeByValue, value))) return { valid: false, message: '动作元素不属于任务绑定规则' };
    if (data.descriptions.some(name => !Object.hasOwn(slots, name))) return { valid: false, message: '动作描述不属于任务绑定规则' };
    if (!data.descriptions.every(name => sameCounts(countElements(data.elements), slots[name]))) return { valid: false, message: '动作元素类型或数量与动作描述不匹配' };
    if (data.ruleId !== rule.id || data.ruleVersion !== rule.version) return { valid: false, message: '动作标注规则版本不匹配' };
    return { valid: true, message: '' };
  }
  function availableDescriptions(elements, descriptions) {
    if (elements.some(value => !Object.hasOwn(typeByValue, value))) return [];
    const target = elements.length ? countElements(elements) : signature(descriptions);
    return Object.keys(templates).filter(name => target !== null && (!Object.keys(target).length || sameCounts(slots[name], target)));
  }
  const api = { rule, elementTypes, templates, slots, countElements, sameCounts, signature, validate, availableDescriptions };
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (!root.document) return;
  root.ActionAnnotationRules = api;

  function init() {
    const editor = document.querySelector('workbench-segment-editor[variant="variant-3"]');
    const list = document.querySelector('workbench-segment-list');
    if (!editor || !list) return;
    const elements = editor.querySelector('workbench-multi-select[aria-label="动作元素"]');
    const descriptions = editor.querySelector('workbench-multi-select[aria-label="动作描述"]');
    elements._options = Object.keys(typeByValue);
    elements.querySelector('.workbench-multi-select__options').innerHTML = Object.entries(elementTypes).map(([type, group]) => `<div class="action-element-group" data-element-type="${type}"><div class="action-element-group__title">${group.label}<span>${type}</span><em>【新】</em></div>${group.values.map(value => `<button type="button" data-multi-option="${value}" data-element-option-type="${type}" role="option">${value}<span>✓</span></button>`).join('')}</div>`).join('');
    descriptions._options = Object.keys(templates);
    descriptions.querySelector('.workbench-multi-select__options').innerHTML = Object.entries(templates).map(([name, label]) => `<button type="button" data-multi-option="${name}" role="option">${label}<span>✓</span></button>`).join('');
    const renderValue = descriptions._renderValue.bind(descriptions);
    descriptions._renderValue = () => {
      renderValue();
      descriptions.querySelectorAll('.workbench-multi-select__tag').forEach(tag => {
        const name = tag.querySelector('[data-remove-value]').dataset.removeValue;
        tag.firstChild.textContent = templates[name] || name;
      });
    };
    // Existing unversioned demo records are migrated once; saved rule records retain their edits.
    editor._actionData = editor._actionData.map((data, index) => {
      if (data.ruleId) return data;
      const migrated = { ...data, elements: [...data.elements], descriptions: [...data.descriptions], ruleId: rule.id, ruleVersion: rule.version };
      if (index === 4 && migrated.descriptions.join('|') === '整理散落书本|将书本竖直放回书架') migrated.descriptions = ['观察并整理桌面物品', '将书本竖直放回书架'];
      if (index === 5 && migrated.descriptions.join('|') === '按类别整理笔记本|放回指定位置') { migrated.elements = ['笔记本', '书架']; migrated.descriptions = ['移动', '放置']; }
      return migrated;
    });
    function renderRules() {
      const data = editor._actionData[editor._index - 1];
      const counts = countElements(data.elements), required = signature(data.descriptions);
      const visible = new Set(availableDescriptions(data.elements, data.descriptions));
      descriptions.querySelectorAll('[data-multi-option]').forEach(option => { option.hidden = !visible.has(option.dataset.multiOption); });
      const compatible = required !== null && data.elements.every(value => Object.hasOwn(typeByValue, value)) && (!data.descriptions.length || Object.entries(counts).every(([type, count]) => count <= (required[type] || 0)));
      elements.querySelectorAll('.action-element-group').forEach(group => { group.hidden = !compatible || (data.descriptions.length > 0 && !required[group.dataset.elementType]); });
      elements.querySelectorAll('[data-element-option-type]').forEach(option => {
        const type = option.dataset.elementOptionType;
        option.disabled = data.descriptions.length > 0 && !data.elements.includes(option.dataset.multiOption) && (counts[type] || 0) >= ((required || {})[type] || 0);
      });
      const result = validate(data);
      for (const select of [elements, descriptions]) select._trigger.title = result.message;
      if (!elements._popover.hidden) elements._positionPopover();
      if (!descriptions._popover.hidden) descriptions._positionPopover();
    }
    const setSegment = editor._setSeveritySegment.bind(editor);
    editor._setSeveritySegment = (...args) => { setSegment(...args); renderRules(); };
    editor.addEventListener('multi-select-change', event => {
      if (event.target !== elements && event.target !== descriptions) return;
      Object.assign(editor._actionData[editor._index - 1], { ruleId: rule.id, ruleVersion: rule.version });
      renderRules();
      const result = validate(editor._actionData[editor._index - 1]);
      if (!result.valid) notifyWorkbench(`${result.message}，请检查动作元素和动作描述。`);
    });
    const actionList = list.querySelector('[data-action-list]');
    if (actionList) {
      actionList._items.forEach((item, index) => {
        item.elements = [...editor._actionData[index].elements];
        item.description = [...editor._actionData[index].descriptions];
      });
      actionList.render();
    }
    // Capture before the original footer confirms or records a successful submission.
    function blockInvalidSubmit(event) {
      if (list.variant !== 'action') return;
      const invalid = editor._actionData.findIndex(data => !validate(data).valid);
      if (invalid < 0) return;
      event.preventDefault(); event.stopImmediatePropagation();
      editor.setSegment(invalid + 1, true);
      list.selectSegment(invalid + 1, false);
      let dialog = document.querySelector('.action-rule-error-dialog');
      if (!dialog) {
        dialog = document.createElement('dialog');
        dialog.className = 'workbench-submit-dialog workbench-submit-dialog--submit action-rule-error-dialog';
        dialog.setAttribute('aria-label', '标注内容校验失败');
        dialog.innerHTML = '<header><h2>提示</h2><button type="button" data-close aria-label="关闭">×</button></header><div class="workbench-submit-dialog__body"><span class="workbench-submit-dialog__icon is-warning" aria-hidden="true">!</span><p>标注内容有误，请检查动作元素和动作描述。</p></div><footer><button type="button" data-close>我知道了</button></footer>';
        dialog.addEventListener('click', event => { if (event.target === dialog || event.target.closest('[data-close]')) dialog.close(); });
        document.body.append(dialog);
      }
      if (!dialog.open) dialog.showModal();
    }
    list.addEventListener('click', event => { if (event.target.closest('workbench-footer-actions button[data-action="submit"]')) blockInvalidSubmit(event); }, true);
    list.addEventListener('workbench-action', event => { if (event.detail?.action === 'submit') blockInvalidSubmit(event); }, true);
    editor.setSegment(editor._index, false);
    editor.dispatchEvent(new CustomEvent('action-annotation-change', { bubbles: true, detail: { index: editor._index, elements: elements.values, descriptions: descriptions.values } }));
  }
  init();
})(typeof window === 'undefined' ? globalThis : window);
