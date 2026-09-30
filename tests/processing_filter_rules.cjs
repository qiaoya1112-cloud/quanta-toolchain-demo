// Run with rendered /data/processing-tasks HTML on stdin.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const html = require('node:fs').readFileSync(0, 'utf8');
const context = vm.createContext({});
for (const name of ['DPR_NODE_RULES', 'DPR_TASK_FILTER_FIELDS', 'DPR_TASK_FILTER_OPERATORS', 'DPR_EDITABLE_TASK_FILTER_FIELDS']) {
  const start = html.indexOf('    var ' + name + ' =');
  assert.ok(start >= 0, name);
  vm.runInContext(html.slice(start, html.indexOf(';', start) + 1), context);
}
for (const name of ['dprProcessingEscape', 'dprTaskFilterFieldName', 'dprTaskFilterScopeControl', 'dprTaskFilterValueControl', 'dprTaskFilterMultiControl', 'dprTaskFilterRow', 'dprCanonicalTaskFilters', 'dprCurrentTaskFilters']) {
  const start = html.indexOf('    function ' + name + '(');
  assert.ok(start >= 0, name);
  vm.runInContext(html.slice(start, html.indexOf('\n    }', start) + 6), context);
}
const key = (filters) => context.dprCanonicalTaskFilters(filters);
const scope = JSON.stringify(['质检', '通用质检规则', 'v3']);
const otherVersion = JSON.stringify(['质检', '通用质检规则', 'v2']);
const qualityOptions = context.dprTaskFilterScopeControl('是否完成质检');
assert.match(qualityOptions, /value="any" selected>任意规则/);
assert.match(qualityOptions, /通用质检规则 · v3/);
assert.doesNotMatch(qualityOptions, /端到端切分标注规则/);
const annotationOptions = context.dprTaskFilterScopeControl('是否完成标注');
assert.match(annotationOptions, /端到端切分标注规则 · v1/);
assert.doesNotMatch(annotationOptions, /通用质检规则/);
assert.equal(key([['是否质检', '是']]), key([['是否完成质检', '等于', '是', 'any']]));
assert.equal(key([['质检结论', '合格、操作失误']]), key([['质检结果', '等于', '操作失误,合格', 'any']]));
assert.notEqual(key([['质检结果', '等于', '合格', scope]]), key([['质检结果', '等于', '合格', otherVersion]]));
assert.notEqual(key([['质检结果', '等于', '合格', scope]]), key([['质检结果', '等于', '合格', 'any']]));
assert.equal(key([['质检结果', '等于', '', scope]]), null);
const row = context.dprTaskFilterRow('质检结论', '等于', '合格', false, scope);
assert.doesNotMatch(row, /<option[^>]*>所属项目<\/option>/);
const basicRow = context.dprTaskFilterRow('所属项目', '等于', 'demo 项目');
assert.doesNotMatch(basicRow, /dpr-task-filter-scope/);
assert.doesNotMatch(basicRow, /<option[^>]*>是否完成质检<\/option>/);
assert.doesNotMatch(basicRow, /<option[^>]*>是否完成标注<\/option>/);
assert.doesNotMatch(basicRow, /<option[^>]*>质检结果<\/option>/);
const addedRow = context.dprTaskFilterRow('采集任务 ID', '等于', '', true);
assert.doesNotMatch(addedRow, /dpr-task-filter-scope/);
assert.match(addedRow, /data-added-filter="true"/);
assert.ok(row.includes(context.dprProcessingEscape(scope) + '" selected'));
assert.match(row, /value="合格" checked/);
assert.match(context.dprTaskFilterScopeControl('质检结果', otherVersion), /通用质检规则 · v2<\/option>/);
// Serialization keeps the selected scope, so switching panes and duplicate checks use it.
const controls = {
  '.dpr-task-filter-field': {value: '是否完成质检'},
  '.dpr-task-filter-operator': {value: '等于'},
  '.dpr-task-filter-scope': {value: scope},
  '.dpr-task-filter-value-wrap': {querySelector: (selector) => selector === '.dpr-task-filter-value' ? {value: '是'} : null},
};
context.document = {querySelectorAll: () => [{querySelector: (selector) => controls[selector]}]};
assert.equal(JSON.stringify(context.dprCurrentTaskFilters()), JSON.stringify([['是否完成质检', '等于', '是', scope]]));
const basicControls = {
  '.dpr-task-filter-field': {value: '数据 ID'},
  '.dpr-task-filter-operator': {value: '等于'},
  '.dpr-task-filter-value-wrap': {querySelector: (selector) => selector === '.dpr-task-filter-value' ? {value: 'REC-1'} : null},
};
context.document.querySelectorAll = () => [basicControls, controls].map((fields) => ({querySelector: (selector) => fields[selector]}));
assert.equal(JSON.stringify(context.dprCurrentTaskFilters()), JSON.stringify([['数据 ID', '等于', 'REC-1'], ['是否完成质检', '等于', '是', scope]]));
assert.notEqual(key(context.dprCurrentTaskFilters()), key([['数据 ID', '等于', 'REC-1']]));
console.log('Processing filter rule scope checks passed');
