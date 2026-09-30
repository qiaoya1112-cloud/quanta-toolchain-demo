// Render /data/rules with Flask's test client and pipe the HTML into this test.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const html = require('node:fs').readFileSync(0, 'utf8');
const script = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)]
  .map(match => match[1]).find(code => code.includes('function ruleRemoveActionElement'));
const context = vm.createContext({});
for (const name of ['ruleEscape', 'ruleRemoveActionElement', 'ruleActionElementTokens',
  'ruleSyncDescriptionHighlight', 'ruleInsertDescriptionToken', 'ruleSave']) {
  const start = script.indexOf('    function ' + name + '(');
  let end = script.indexOf('\n    function ', start + 1);
  if (end < 0) end = script.indexOf('\n    ruleInitTagPicker();', start);
  assert.ok(start >= 0 && end > start, name);
  vm.runInContext(script.slice(start, end), context);
}
let groups = [];
const descriptions = {zh: [], en: []};
const controls = {
  ruleCreateName: {value: '测试规则'}, ruleCreateProject: {value: 'demo 项目'},
  ruleCreateStage: {value: '标注'}, ruleCreateType: {value: '动作标注'},
};
context.document = {
  getElementById: id => controls[id],
  querySelectorAll: selector => {
    if (selector === '#ruleActionElements .rule-action-tree-group') return groups;
    if (selector === '#ruleActionDescriptionRows input') return [...descriptions.zh, ...descriptions.en];
    if (selector.endsWith('.rule-action-desc-zh')) return descriptions.zh;
    if (selector.endsWith('.rule-action-desc-en')) return descriptions.en;
    throw new Error('Unexpected selector: ' + selector);
  },
};
context.ruleRefreshActionTree = () => {};
context.ruleRefreshPlaceholders = () => {};
context.toast = message => { context.lastToast = message; };
function element(zh, en) {
  const group = {
    querySelector: selector => ({value: selector.endsWith('-name') ? zh : en}),
    remove: () => { groups = groups.filter(item => item !== group); },
  };
  groups.push(group);
  return {closest: () => group};
}
function description(language, value) {
  const classes = new Set();
  const text = {innerHTML: '', style: {}};
  const editor = {classList: {toggle: (key, yes) => yes ? classes.add(key) : classes.delete(key)}, querySelector: () => text};
  const input = {value, scrollLeft: 0, disabled: false, selectionStart: 0, selectionEnd: 0,
    closest: () => editor, setAttribute: (key, value) => { input[key] = value; }, focus: () => {},
    setSelectionRange: (start, end) => { input.selectionStart = start; input.selectionEnd = end; }};
  descriptions[language].push(input);
  return {input, text, classes};
}
const target = element('物体', 'object');
element('位置', 'location');
const zh = description('zh', '拿起{物体}，把{物体}放到{位置}；物体文字保留');
const en = description('en', 'Move {object} to {location}, then release {object}');
const untouched = description('zh', '移动到{位置}');
context.ruleRemoveActionElement(target);
assert.equal(zh.input.value, '拿起{}，把{}放到{位置}；物体文字保留');
assert.equal(en.input.value, 'Move {} to {location}, then release {}');
assert.equal(untouched.input.value, '移动到{位置}');
assert.equal((zh.text.innerHTML.match(/class="rule-desc-empty-slot"/g) || []).length, 2);
assert.ok(zh.classes.has('has-empty-slot'));
assert.equal(zh.input['aria-invalid'], 'true');
context.ruleSave();
assert.equal(context.lastToast, '请补全动作描述中的空变量插槽');
zh.input.selectionStart = zh.input.selectionEnd = 3;
const select = {value: '位置', closest: () => ({querySelector: () => zh.input})};
context.ruleInsertDescriptionToken(select);
assert.equal(zh.input.value, '拿起{位置}，把{}放到{位置}；物体文字保留');
zh.input.value = '拿起{位置}';
context.ruleSyncDescriptionHighlight(zh.input);
assert.equal(zh.classes.has('has-empty-slot'), false);
assert.equal(zh.input['aria-invalid'], 'false');
zh.input.value = '<img src=x onerror=alert(1)>{}';
zh.input.scrollLeft = 25;
context.ruleSyncDescriptionHighlight(zh.input);
assert.ok(zh.text.innerHTML.startsWith('&lt;img'));
assert.equal(zh.text.style.transform, 'translateX(-25px)');
// Literal replacement handles regex metacharacters, multiple rows, and duplicate tokens.
const duplicate = element('位置', 'location');
context.ruleRemoveActionElement(duplicate);
assert.equal(untouched.input.value, '移动到{位置}');
const special = element('对象(A)+', 'object.a');
const specialDescription = description('en', '{object.a} / {objectXa}');
context.ruleRemoveActionElement(special);
assert.equal(specialDescription.input.value, '{} / {objectXa}');
console.log('Action element deletion, bilingual slots, highlighting, repair, and validation: OK');
