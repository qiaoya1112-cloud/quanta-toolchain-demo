'use strict';
// One validation implementation for the UI and the background import worker.
const fs = require('node:fs');
const catalog = require('../static/eval_catalog/catalog.js');
try {
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  catalog.setActor(input.actor || 'Joanna Qiao');
  let result;
  if (input.action === 'initialize') {
    result = catalog.upgrade(input.seed, input.saved || null);
  } else if (input.action === 'audit') {
    result = catalog.recordElementUpdates(input.previous, input.next, input.tags || [], input.now);
  } else if (input.action === 'plan') {
    result = catalog.planCaseImport(input.db, input.parsed, input.context || {}, input.now);
    if (result.next) result.next = catalog.recordElementUpdates(input.db, result.next, input.context?.tags || [], input.now);
    for (const key of ['created', 'updated', 'unchanged', 'skipped']) result[key] = result[key].map(row => ({id: row.id, row: row.row}));
  } else {
    throw new Error('未知导入操作');
  }
  process.stdout.write(JSON.stringify(result));
} catch (error) {
  process.stderr.write(error.message);
  process.exitCode = 1;
}
