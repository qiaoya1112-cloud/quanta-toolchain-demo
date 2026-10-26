(() => {
  'use strict';
  const configElement = document.getElementById('qAdvancedConfig');
  if (!configElement) return;
  const config = JSON.parse(configElement.textContent);
  const form = document.getElementById('qform');
  const ANY = '*';
  const create = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const option = (value, label) => {
    const item = create('option', '', label); item.value = value; return item;
  };
  document.addEventListener('click', event => {
    document.querySelectorAll('.query-processing-picker').forEach(wrap => {
      if (!wrap.contains(event.target)) wrap.dispatchEvent(new Event('picker-close'));
    });
  });
  document.querySelectorAll('[data-processing-kind]').forEach(section => {
    const kind = section.dataset.processingKind;
    const quality = kind === 'quality';
    const title = quality ? '质检' : '标注';
    const state = config.processing[kind];
    if (!state.groups.length) {
      state.groups.push(quality
        ? {status:'', rule:[ANY], flow:[ANY], rule_match:'any', results:[]}
        : {status:'', rule:[ANY], flow:[ANY], version:''});
    }
    state.groups.forEach(group => {
      ['rule', 'flow'].forEach(key => {
        const value = group[key];
        group[key] = Array.isArray(value) && value.length ? [value[0]] : [value || ANY];
      });
    });
    const catalog = config.processingOptions[kind];
    const hidden = section.querySelector('input[type=hidden]');
    const rows = section.querySelector('[data-processing-rows]');
    const help = section.querySelector('[data-processing-help]');
    const description = quality
      ? '“任意规则”表示不按规则筛选，“任意流程”表示不按流程筛选；两项均为“任意”时，可匹配新旧平台数据。选择具体项后，仅匹配新平台对应数据。'
      : '“任意规则”表示不按规则筛选，“任意流程”表示不按流程筛选；两项均为“任意”时，可匹配新旧平台数据。选择具体项后，仅匹配新平台对应数据。筛选旧平台版本时，规则和流程保留“任意”。';
    function sync(notify = true) {
      hidden.value = JSON.stringify(state);
      if (notify) hidden.dispatchEvent(new Event('change', {bubbles:true}));
    }
    section.addEventListener('query-clear-field', event => {
      const {index, key} = event.detail;
      const group = state.groups[index];
      if (!group) return;
      if (key === 'rule' || key === 'flow') group[key] = [ANY];
      else if (key === 'results') group.results = [];
      else group[key] = '';
      render(); sync();
    });
    function render() {
      rows.replaceChildren();
      help.textContent = (state.groups.length > 1 ? '历史多组条件' + (state.logic === 'or' ? '（任一组满足）：' : '（全部组满足）：') : '') + description;
      state.groups.forEach((group, index) => {
        const row = create('div', 'query-processing-row q-filter-row q-adv-row query-fixed-grid');
        row.dataset.processingRow = String(index);
        row.setAttribute('role', 'group'); row.setAttribute('aria-label', title + '条件组 ' + (index + 1));
        const controls = {};
        function field(key, label, input) {
          const wrapper = create('div', 'q-field');
          const id = 'q-' + kind + '-' + index + '-' + key;
          const caption = create('label', '', label);
          caption.htmlFor = input.querySelector('.query-picker-input') ? id + '-input' : input.querySelector('button') ? id + '-trigger' : id;
          input.id = id; input.dataset.processingField = key;
          input.setAttribute('aria-label', title + '条件组 ' + (index + 1) + ' ' + label);
          controls[key] = input; wrapper.append(caption, input); row.append(wrapper);
          return input;
        }
        function select(key, label, choices, current, onChange) {
          const input = create('select');
          choices.forEach(([value, text]) => input.append(option(value, text)));
          if (current && !choices.some(([value]) => value === current)) input.append(option(current, quality && key === 'rule' ? current.replace(/^rule:/, '') : current));
          input.value = current; input.classList.toggle('has-value', !!current);
          input.addEventListener('change', () => {
            onChange(input.value); input.classList.toggle('has-value', !!input.value);
            dependencies(); sync();
          });
          return field(key, label, input);
        }
        function singleSelect(key, label, anyLabel) {
          const wrap = create('div', 'ms-wrap query-processing-picker');
          const input = create('input', 'query-picker-input'); input.type = 'text';
          input.autocomplete = 'off'; input.spellcheck = false;
          input.setAttribute('role', 'combobox');
          input.setAttribute('aria-autocomplete', 'list');
          input.setAttribute('aria-expanded', 'false');
          input.setAttribute('aria-label', title + '条件组 ' + (index + 1) + ' ' + label);
          const panel = create('div', 'ms-panel'); panel.setAttribute('role', 'listbox');
          panel.setAttribute('aria-label', label);
          const choices = [...new Set([...catalog[key], ...group[key].filter(value => value !== ANY)])];
          const options = [];
          let active = -1;
          function selectedText() { return group[key][0] === ANY ? anyLabel : group[key][0]; }
          function update() {
            input.value = selectedText();
            input.title = input.value;
            input.classList.toggle('has-value', group[key][0] !== ANY);
            if (group[key][0] === ANY) input.dataset.processingDefault = 'true';
            else delete input.dataset.processingDefault;
            options.forEach(({row, value}) => row.setAttribute('aria-selected', String(group[key][0] === value)));
          }
          [[ANY, anyLabel], ...choices.map(value => [value,value])].forEach(([value, text]) => {
            const item = create('div', 'query-picker-option', text);
            item.id = 'q-' + kind + '-' + index + '-' + key + '-option-' + options.length;
            item.setAttribute('role', 'option');
            item.addEventListener('mousedown', event => event.preventDefault());
            item.addEventListener('click', () => choose(value));
            panel.append(item);
            options.push({value, row:item, text});
          });
          const empty = create('p','muted query-picker-empty','无匹配选项'); empty.hidden = true; panel.append(empty);
          function searchOptions() {
            const query = input.value.trim().toLocaleLowerCase();
            options.forEach(item => {
              item.row.hidden = !!query && !item.text.toLocaleLowerCase().includes(query);
            });
            empty.hidden = options.some(item => !item.row.hidden);
            active = -1;
            input.removeAttribute('aria-activedescendant');
          }
          function close() {
            wrap.classList.remove('open'); input.setAttribute('aria-expanded', 'false');
            input.removeAttribute('aria-activedescendant'); update();
          }
          function choose(value) {
            group[key] = [value]; update(); dependencies(); sync(); close();
            input.focus({preventScroll:true});
          }
          function open() {
            if (wrap.classList.contains('open')) return;
            section.querySelectorAll('.query-processing-picker.open').forEach(other => {
              if (other !== wrap) other.dispatchEvent(new Event('picker-close'));
            });
            wrap.classList.add('open'); input.setAttribute('aria-expanded', 'true');
            options.forEach(item => {item.row.hidden = false;});
            empty.hidden = true;
            active = options.findIndex(item => item.value === group[key][0]);
            input.setAttribute('aria-activedescendant', options[active].row.id);
          }
          input.addEventListener('focus', () => {open(); input.select();});
          input.addEventListener('click', () => {if (!wrap.classList.contains('open')) open();});
          input.addEventListener('input', () => {open(); searchOptions();});
          input.addEventListener('keydown', event => {
            if (event.key === 'Escape') {event.preventDefault(); close(); input.blur(); return;}
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
              event.preventDefault(); open();
              const visible = options.filter(item => !item.row.hidden);
              if (!visible.length) return;
              const current = visible.findIndex(item => options.indexOf(item) === active);
              const next = visible[(current + (event.key === 'ArrowDown' ? 1 : visible.length - 1)) % visible.length];
              active = options.indexOf(next);
              input.setAttribute('aria-activedescendant', next.row.id);
              next.row.scrollIntoView({block:'nearest'});
            }
            if (event.key === 'Enter') {
              event.preventDefault();
              if (wrap.classList.contains('open')) {
                const candidate = options[active] || options.find(item => !item.row.hidden);
                if (candidate && !candidate.row.hidden) choose(candidate.value);
              }
            }
          });
          wrap.addEventListener('focusout', event => {if(!event.relatedTarget || !wrap.contains(event.relatedTarget)) close();});
          wrap.addEventListener('picker-close', close);
          wrap.append(input, panel); field(key, label, wrap);
          input.id = wrap.id + '-input'; panel.id = wrap.id + '-panel';
          input.setAttribute('aria-controls', panel.id);
          controls[key + 'Picker'] = {setDisabled(disabled) {
            input.disabled = disabled;
            wrap.classList.toggle('qf-off',disabled);
            input.title = disabled ? '筛选旧平台版本时，规则和流程保持任意' : selectedText();
            if(disabled) close();
          }};
          update();
        }
        select('status', '是否' + title, [['','不限'],['yes','是'],['no','否']], group.status, value => {group.status = value;});
        singleSelect('rule', title + '规则（新平台）', '任意规则');
        singleSelect('flow', title + '流程（新平台）', '任意流程');
        if (quality) {
          const wrap = create('div', 'ms-wrap');
          const trigger = create('button', 'ms-trigger'); trigger.type = 'button';
          const caption = create('span', 'ms-label'); trigger.append(caption);
          trigger.setAttribute('aria-expanded','false');
          const panel = create('div', 'ms-panel');
          function updateConclusion() {
            const names = {pass:'合格', fail:'不合格', warn:'操作失误'};
            caption.textContent = group.results.length ? group.results.map(value => names[value]).join('、') : '全部';
            trigger.classList.toggle('has-value', !!group.results.length);
          }
          [['pass','合格'],['fail','不合格'],['warn','操作失误']].forEach(([value, text]) => {
            const label = create('label'); const checkbox = create('input');
            checkbox.type = 'checkbox'; checkbox.value = value; checkbox.checked = group.results.includes(value);
            checkbox.addEventListener('change', () => {
              group.results = [...panel.querySelectorAll('input:checked')].map(input => input.value);
              updateConclusion(); sync();
            });
            label.append(checkbox, create('span', '', text)); panel.append(label);
          });
          trigger.addEventListener('click', () => {
            const open = wrap.classList.toggle('open'); trigger.setAttribute('aria-expanded', String(open));
          });
          wrap.append(trigger,panel);
          field('results', '质检结论', wrap);
          trigger.setAttribute('aria-label', '质检条件组 ' + (index + 1) + ' 质检结论');
          trigger.id = wrap.id + '-trigger';
          controls.conclusionTrigger = trigger; controls.updateConclusion = updateConclusion;
          updateConclusion();
        } else {
          const version = create('input'); version.type = 'number'; version.min = '1'; version.step = '1';
          version.placeholder = '不限版本'; version.value = group.version;
          version.addEventListener('input', () => {group.version = version.value; dependencies(); sync();});
          field('version', '标注版本（旧平台）', version);
        }
        function dependencies() {
          if (quality) {
            const disabled = group.status === 'no';
            if (disabled) {
              group.results = [];
              controls.results.querySelectorAll('input').forEach(input => {input.checked = false;});
              controls.results.classList.remove('open');
              controls.conclusionTrigger.setAttribute('aria-expanded','false');
            }
            controls.results.querySelectorAll('input').forEach(input => {input.disabled = disabled;});
            controls.conclusionTrigger.disabled = disabled;
            controls.results.closest('.q-field').classList.toggle('qf-off', disabled);
            controls.updateConclusion();
          } else {
            controls.rulePicker.setDisabled(!!group.version);
            controls.flowPicker.setDisabled(!!group.version);
            controls.version.disabled = [...group.rule, ...group.flow].some(value => value !== ANY);
            controls.version.title = controls.version.disabled ? '选择任意规则和任意流程后，可筛选旧平台版本' : '';
          }
        }
        if (state.groups.length > 1) {
          const remove = create('button', 'query-text-button query-remove', '移除'); remove.type = 'button';
          remove.setAttribute('aria-label', '移除' + title + '条件组 ' + (index + 1));
          remove.addEventListener('click', () => {state.groups.splice(index,1); render(); sync();});
          row.append(remove);
        }
        rows.append(row); dependencies();
      });
    }
    render(); sync(false);
    form.addEventListener('submit', () => sync(false));
  });
})();
