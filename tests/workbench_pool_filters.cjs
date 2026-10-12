const assert = require('node:assert/strict');
const fs = require('node:fs'), vm = require('node:vm');
const elements = new Map();
const element = id => {
  if (!elements.has(id)) elements.set(id, {hidden:true, textContent:'', innerHTML:'', handlers:{},
    addEventListener(name, handler){this.handlers[name]=handler;}, querySelectorAll(){return [];},
    setAttribute(){}, scrollIntoView(){}});
  return elements.get(id);
};
const records = [
  {id:'1',task_id:'10',status:'processing',supplier_id:'SUP-001',collector:'甲',self_checker:'乙',collected_at:'2026-09-30 10:00:00',self_checked_at:'2026-10-01 10:00:00'},
  {id:'2',task_id:'10',status:'pending',supplier_id:'SUP-003',collector:'丙',collected_at:'2026-10-01 10:00:00'},
  {id:'3',task_id:'11',status:'pending',supplier_id:'SUP-001',collector:'丁',self_checker:'戊',collected_at:'2026-10-02 10:00:00',self_checked_at:'2026-10-03 10:00:00'},
];
let values = {};
const context = {window:{WorkbenchPool:{payload:{task:{id:'task',pool:'pool'},records}},addEventListener(){}},
  document:{getElementById:element},sessionStorage:{getItem(){return null;},removeItem(){}},
  FormData: class {constructor(){return Object.entries(values);}}, URLSearchParams};
vm.runInNewContext(fs.readFileSync('static/workbench_pool/list.js','utf8'),context);
const rows = element('wpRows'), form = element('wpFilters');
const ids = () => [...rows.innerHTML.matchAll(/data-record-id="([^"]+)"/g)].map(m=>m[1]);
const search = filters => {values=filters;form.handlers.submit({preventDefault(){}});return ids();};
assert.deepEqual(ids(),['1','2','3']);
assert.doesNotMatch(rows.innerHTML,/data-action="合格"/);
assert.match(rows.innerHTML,/甲（SUP-001）/);
assert.deepEqual(search({supplier_id:'SUP-001'}),['1','3']);
assert.deepEqual(search({operator:'甲'}),['1']);
assert.deepEqual(search({operator:'乙'}),['1']);
assert.deepEqual(search({operator:'戊',supplier_id:'SUP-001'}),['3']);
assert.deepEqual(search({operator:'未执行质检人'}),[]);
assert.deepEqual(search({time_node:'collection',from:'2026-10-01',to:'2026-10-01'}),['2']);
assert.deepEqual(search({time_node:'self_check',from:'2026-10-01',to:'2026-10-01'}),['1']);
assert.deepEqual(search({time_node:'self_check',from:'2026-10-01',to:'2026-10-03',supplier_id:'SUP-001'}),['1','3']);
assert.deepEqual(search({status:'pending'}),['2','3']);
search({from:'2026-10-01'});
assert.match(element('wpError').textContent,/请先选择操作节点/);
assert.deepEqual(ids(),['2','3'],'invalid criteria retain the previous valid result');
search({time_node:'collection',from:'2026-10-03',to:'2026-10-01'});
assert.match(element('wpError').textContent,/开始时间不能晚于结束时间/);
form.handlers.reset();assert.deepEqual(ids(),['1','2','3']);
context.window.WorkbenchPool.payload.task.id='WB-PRETRAINING-QC';
Object.assign(records[0], {result:'不合格',reviewed_at:'2026-10-09 10:00:00',operators:{'质检人':'当前节点人员'},self_checker_supplier_id:'SUP-028'});
vm.runInNewContext(fs.readFileSync('static/workbench_pool/list.js','utf8'),context);
assert.doesNotMatch(rows.innerHTML,/采集质检：|当前节点人员|2026-10-09/);
assert.match(rows.innerHTML,/乙（SUP-028）/);
assert.match(rows.innerHTML,/自动化质检/);
assert.doesNotMatch(rows.innerHTML,/自动化自检|未自检|未质检/);
assert.deepEqual(search({operator:'当前节点人员'}),[]);
context.window.WorkbenchPool.payload.task.id='WB-PRETRAINING-ACCEPTANCE';
Object.assign(records[0], {collection_qc_result:'合格',collection_qc_at:'2026-10-08 10:00:00',collection_qc_operator:'前序质检人员',collection_qc_supplier_id:'SUP-039'});
vm.runInNewContext(fs.readFileSync('static/workbench_pool/list.js','utf8'),context);
assert.match(rows.innerHTML,/前序质检人员（SUP-039）/);
assert.match(rows.innerHTML,/采集质检：<\/span>合格/);
assert.doesNotMatch(rows.innerHTML,/当前节点人员|2026-10-09/);
assert.deepEqual(search({operator:'前序质检人员'}),['1']);
assert.deepEqual(search({time_node:'collection_qc',from:'2026-10-08',to:'2026-10-08'}),['1']);
console.log('Task pool filters and node-scoped history passed');
