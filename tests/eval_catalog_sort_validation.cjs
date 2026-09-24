const assert=require('node:assert/strict');
const {sortCaseRows}=require('../static/eval_catalog/catalog.js');
const db={stories:[{id:'S1',stage_id:'A'},{id:'S2',stage_id:'A'}]};
const rows=[
 {id:'older',case_stage:'A',story_id:'S1',created_at:'2026-09-20 08:00:00'},
 {id:'other-stage',case_stage:'B',story_id:'S1',created_at:'2026-09-23 08:00:00'},
 {id:'other-story',case_stage:'A',story_id:'S2',created_at:'2026-09-22T08:00:00'},
 {id:'latest',case_stage:'A',story_id:'S1',created_at:'2026-09-24 08:00:00'},
 {id:'legacy',story_id:'S1',created_at:'2026-09-21 08:00:00'},
 {id:'missing',created_at:''},
 {id:'invalid',created_at:'unknown'}
];
const before=JSON.stringify(rows),ids=items=>items.map(row=>row.id);
assert.deepEqual(ids(sortCaseRows(db,rows,'created-desc')),['latest','other-stage','other-story','legacy','older','missing','invalid']);
assert.deepEqual(ids(sortCaseRows(db,rows)),['latest','legacy','older','other-story','other-stage','missing','invalid']);
assert.deepEqual(ids(sortCaseRows(db,rows.filter(row=>row.story_id==='S1'))),['latest','legacy','older','other-stage']);
assert.deepEqual(sortCaseRows(db,[]),[]);
assert.equal(JSON.stringify(rows),before,'Sorting does not mutate records or source order');
console.log('Case sorting: dates, Stage/Story grouping, legacy Stage fallback, filtered rows, empty data and immutability passed.');
