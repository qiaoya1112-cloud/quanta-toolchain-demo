const assert = require('node:assert/strict');
const rules = require('../static/annotation_workbench/action-annotation-rules.js');

const data = (elements, descriptions) => ({
  elements, descriptions,
  ruleId: rules.rule.id,
  ruleVersion: rules.rule.version
});

assert.equal(rules.validate(data(['书本'], ['整理'])).valid, true);
assert.equal(rules.validate(data(['书本', '笔记本'], ['整理'])).valid, false);
assert.equal(rules.validate(data(['书本', '笔记本'], ['整理两个物体'])).valid, true);
assert.deepEqual(rules.availableDescriptions(['书本', '笔记本'], []), ['整理两个物体']);
assert.deepEqual(rules.availableDescriptions(['苹果', '杯子'], []), ['将水果放入容器']);
assert.equal(rules.availableDescriptions(['苹果', '草莓', '杯子'], []).includes('将两种水果放入容器'), true);
assert.equal(rules.availableDescriptions(['苹果', '杯子'], []).includes('将物体放入容器'), false);
assert.deepEqual(rules.availableDescriptions([], ['将两种水果放入容器']), []);
assert.equal(rules.fillTemplate('整理两个物体', ['书本', '纸盒']), '整理 {书本} 和 {纸盒}');
assert.equal(rules.fillTemplate('将两种水果放入容器', ['杯子', '苹果', '草莓']), '将 {苹果}、{草莓} 放入 {杯子}');
assert.equal(rules.validate(data(['书本'], ['整理', '拿起'])).valid, false);
assert.match(rules.validate(data(['书本'], ['整理', '拿起'])).message, /只能选择一个动作描述/);
assert.equal(rules.validate(data([], ['整理'])).valid, false);
assert.equal(rules.validate(data(['书本'], [])).valid, false);
console.log('PASS: action annotation rules use element-to-description matching and fill selected template placeholders.');
