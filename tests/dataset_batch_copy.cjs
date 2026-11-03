const assert = require('node:assert/strict');
const {formatSelection} = require('../static/shared/dataset-batch-copy.js');
const items = [
  {id: 'ds1', ident: 'test_one', name: '数据集: "A"\n换行', version: 'v2', format: 'mozdataset v2', vepfs_addresses: ['/mnt/vepfs01/a/'], addresses: ['tos://bucket/a/', 'ks3://bucket/a/']},
  {id: 'ds2', ident: 'test_two', name: '</script>', version: 'v1', format: 'mozdataset v2', vepfs_addresses: ['/mnt/vepfs02/b/'], addresses: ['tos://bucket/a/']}
];
assert.deepEqual(JSON.parse(formatSelection(items, 'tos')), [
  {dataset_id: 'test_one', tos_addresses: ['tos://bucket/a/']},
  {dataset_id: 'test_two', tos_addresses: ['tos://bucket/a/']}
]);
assert.deepEqual(JSON.parse(formatSelection([items[0]], 'ks3')), [
  {dataset_id: 'test_one', ks3_addresses: ['ks3://bucket/a/']}
]);
assert.throws(() => formatSelection(items, 'ks3'), /缺少 ks3/);
assert.throws(() => formatSelection([items[1]], 'ks3'), /缺少 ks3/);
const yaml = formatSelection(items, 'yaml');
assert.ok(yaml.startsWith('# 预训练数据集配置片段\ndatasets:\n'));
assert.equal(JSON.parse(yaml.split('\n')[2].slice('  - name: '.length)), items[0].name);
assert.ok(yaml.includes('    version: "v2"\n    format: "mozdataset v2"\n    storage_paths:\n      - "/mnt/vepfs01/a/"'));
assert.equal((yaml.match(/  - name:/g) || []).length, 2);
assert.throws(() => formatSelection([], 'yaml'), /请先选择/);
assert.throws(() => formatSelection([{...items[0], addresses: []}], 'tos'), /缺少 tos/);
assert.ok(formatSelection([{...items[0], vepfs_addresses: []}], 'yaml').includes('    storage_paths: []\n'));
assert.ok(formatSelection([{...items[0], vepfs_addresses: undefined}], 'yaml').includes('    storage_paths: []\n'));
assert.throws(() => formatSelection([{...items[0], format: 'lebort'}], 'yaml'), /格式不支持/);
assert.equal((formatSelection([items[0], {...items[1], vepfs_addresses: []}], 'yaml').match(/  - name:/g) || []).length, 2);
assert.throws(() => formatSelection(items, 'invalid'), /不支持/);
console.log('Dataset batch copy formatting checks passed.');
