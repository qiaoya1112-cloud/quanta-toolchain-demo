const assert=require('node:assert/strict');
const {batchScenarios,batchScenarioCount,scenarioValueRows,upgrade,validateScenario,saveScenarioRow,filterRecords}=require('../static/eval_catalog/catalog.js');
const seed=JSON.parse(require('node:fs').readFileSync(process.argv[2],'utf8'));
// This fixture includes a draft Stage; publish it before exercising batch creation.
Object.assign(seed.stages.find(row=>row.id==='ST_BASIC'),{publish_status:'已发布',enabled:true});
const db=upgrade(seed,null);
const selection={project:'后训练评测',tag_ids:['act_pick','obj_phone'],stage_ids:['ST_BASIC','ST_KITCHEN'],story_ids:['SR_READ'],skill_ids:['SK_PICK','SK_PLACE'],factors:[
 {factor_id:'FC_SIZE',values:['小','大']},
 {factor_id:'FC_COLOR',values:[db.factors.find(f=>f.id==='FC_COLOR').values[0].value]}
]};
const before=JSON.stringify(db),created=batchScenarios(db,selection,'2026-09-20 12:00');
assert.equal(created.length,12);
assert.equal(batchScenarioCount(selection),12);
assert.equal(new Set(created.map(row=>row.id)).size,12);
assert.equal(JSON.stringify(db),before);
for(const row of created){
 assert.equal(row.publish_status,'未发布');
 assert.equal(row.project,selection.project);
 assert.deepEqual(row.tag_ids,selection.tag_ids);
 assert.notEqual(row.tag_ids,selection.tag_ids);
 assert.deepEqual(validateScenario(db,row),[]);
}
const saved={...db,scenarios:created},restored=upgrade(seed,saved);
assert.deepEqual(restored.scenarios,created);
const rows=scenarioValueRows(restored).filter(row=>row.scenario_record);
assert.equal(rows.length,12);
assert.deepEqual(rows.map(row=>[row.factor_id,row.factor_value]),created.map(row=>[row.factor_id,row.factor_value]));
assert.equal(batchScenarios(restored,selection,'later').length,0);
assert.equal(batchScenarios({...db,scenarios:created.slice(0,1)},selection,'later').length,11);
assert.equal(filterRecords(restored,'stories','scenario',{stages:['ST_BASIC'],stories:['SR_READ'],skills:['SK_PICK'],factors:['FC_SIZE']}).length,2);
restored.factors.find(f=>f.id==='FC_SIZE').values.push({value:'新取值'});
assert.equal(scenarioValueRows(restored).filter(row=>row.scenario_record).length,12);
const edited=saveScenarioRow(restored,{...rows[0],notes:'按取值保存',tag_ids:['act_pick']});
assert.equal(scenarioValueRows(upgrade(seed,edited)).find(row=>row.row_key===rows[0].row_key).notes,'按取值保存');
const duplicate={...selection,factors:[...selection.factors,{factor_id:'FC_SIZE',values:['小','小']}]};
assert.equal(batchScenarioCount(duplicate),12);
assert.equal(batchScenarios(db,duplicate,'now').length,12);
for(const invalid of [
 {...selection,stage_ids:[]},
 {...selection,factors:[]},
 {...selection,factors:[{factor_id:'',values:[]}]},
 {...selection,factors:[{factor_id:'FC_SIZE',values:[]}]}
]){
 assert.equal(batchScenarioCount(invalid),0);
 assert.throws(()=>batchScenarios(db,invalid,'now'));
}
assert.throws(()=>batchScenarios(db,{...selection,factors:[{factor_id:'FC_SIZE',values:['无效取值']}]},'now'),/无效/);
const disabled=structuredClone(db);disabled.factors.find(f=>f.id==='FC_SIZE').enabled=false;
assert.throws(()=>batchScenarios(disabled,selection,'now'),/停用/);
const legacy=scenarioValueRows(db).find(row=>row.factor_value&&row.skill_id);
assert.equal(batchScenarios(db,{stage_ids:[legacy.stage_id],story_ids:[legacy.story_id],skill_ids:[legacy.skill_id],factors:[{factor_id:legacy.factor_id,values:[legacy.factor_value]}]},'now').length,0);
console.log('Batch scene value counts, validation, deduplication, persistence and legacy compatibility passed.');
