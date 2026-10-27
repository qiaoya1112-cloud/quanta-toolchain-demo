const assert=require('node:assert/strict');
const {upgrade,prepareElement,quickCreateCases,quickCreateBatch,batchCaseStatus}=require('../static/eval_catalog/catalog.js');
const seed=JSON.parse(require('node:fs').readFileSync(process.argv[2],'utf8'));
const db=upgrade(seed,null),stage=db.stages.find(row=>row.enabled!==false),story=db.stories.find(row=>row.enabled!==false);
const selection={case_stage:stage.id,story_id:story.id,project:'后训练评测'};
const rows=[{id:' QUICK_01 ',prompt:' Pick the bowl. ',prompt_cn:' 拿起碗。 '},{id:'QUICK_02',prompt:'Place the bowl.',prompt_cn:'放下碗。'}];
const before=JSON.stringify(db),created=quickCreateCases(db,selection,rows,'2026-10-20 12:00:00');
assert.equal(JSON.stringify(db),before,'Validation and collection must not mutate saved records');
assert.equal(created.length,2);assert.equal(created[0].id,'QUICK_01');assert.equal(created[0].prompt,'Pick the bowl.');
for(const row of created){assert.equal(row.case_stage,stage.id);assert.equal(row.story_id,story.id);assert.equal(row.project,selection.project);assert.equal(row.publish_status,'未发布');assert.equal(row.enabled,false);assert.equal(row.visibility,'公开');assert.deepEqual(row.factors,[]);assert.deepEqual(row.skill_ids,[]);assert.equal(row.created_by,'Joanna Qiao');}
for(const [items,pattern] of [
 [[],/至少/],[[rows[0],{...rows[1],id:'QUICK_01'}],/重复/],[[{...rows[0],id:db['test-cases'][0].id}],/已存在/],
 [[{...rows[0],prompt_cn:' '}],/prompt_CN/],[[{...rows[0],prompt:''}],/prompt_EN/],[[{...rows[0],id:'bad id'}],/编号/]
])assert.throws(()=>quickCreateCases(db,selection,items,'now'),pattern);
assert.throws(()=>quickCreateCases(db,{...selection,case_stage:'missing'},rows,'now'),/Stage/);
assert.throws(()=>quickCreateCases(db,{...selection,story_id:'missing'},rows,'now'),/Story/);
const stage2=db.stages.find(row=>row.enabled!==false&&row.id!==stage.id),story2=db.stories.find(row=>row.enabled!==false&&row.id!==story.id);
const groupedRows=[{...rows[0],case_stage:stage.id,story_id:story.id},{...rows[1],case_stage:stage2.id,story_id:story2.id}];
const grouped=quickCreateCases(db,{project:selection.project},groupedRows,'now');
assert.deepEqual(grouped.map(row=>[row.case_stage,row.story_id]),[[stage.id,story.id],[stage2.id,story2.id]],'Each group keeps its own Stage and Story');
assert.throws(()=>quickCreateCases(db,{project:selection.project},[groupedRows[0],{...groupedRows[1],id:'QUICK_01'}],'now'),/重复/,'IDs must be unique across groups');
for(const key of ['case_stage','story_id'])assert.throws(()=>quickCreateCases(db,{project:selection.project},[groupedRows[0],{...groupedRows[1],[key]:''}],'now'),/Stage|Story/,'Every group requires both scene elements');
const next=structuredClone(db);
for(const kind of ['stages','stories']){
 const element=prepareElement(next,kind,{name:'快捷新增'+kind,project:selection.project});
 Object.assign(element,{publish_status:'已发布',enabled:true});next[kind].push(element);selection[kind==='stages'?'case_stage':'story_id']=element.id;
}
assert.equal(quickCreateCases(next,selection,rows,'now').length,2,'Newly added Stage and Story can be used together');
assert.equal(JSON.stringify(db),before,'A failed or canceled batch leaves original catalog unchanged');
const pendingStage={...prepareElement(db,'stages',{name:'分组场域',project:'预训练评测'}),quick_group:'2'};
const pendingStory={...prepareElement(db,'stories',{name:'分组任务',project:'预训练评测'}),quick_group:'2'};
const projectRows=[{...groupedRows[0],project:'预训练评测',quick_group:'1'},{...groupedRows[1],case_stage:pendingStage.id,story_id:pendingStory.id,project:'后训练评测',quick_group:'2'}];
const batch=quickCreateBatch(db,projectRows,[pendingStage],[pendingStory],'now');
assert.deepEqual(batch.created.map(row=>row.project),['预训练评测','后训练评测']);
for(const key of ['stages','stories']){
 const element=batch.next[key][0];assert.equal(element.project,'后训练评测','New definitions follow their group project at save time');
 assert.equal(element.publish_status,'已发布');assert.equal(element.enabled,true);assert(!Object.hasOwn(element,'quick_group'));
}
assert.throws(()=>quickCreateBatch(db,[projectRows[0],{...projectRows[1],project:''}],[pendingStage],[pendingStory],'now'),/所属项目/);
assert.equal(JSON.stringify(db),before,'Failed grouped saves never write new definitions');
const published=batchCaseStatus(batch.next,batch.created.map(row=>row.id),'publish','publish time');
assert.equal(published.updated.length,2);assert.equal(published.failed.length,0);
for(const row of published.next['test-cases'].slice(0,2)){assert.equal(row.publish_status,'已发布');assert.equal(row.enabled,false,'Publishing does not implicitly enable cases');assert.equal(row.updated_by,'Joanna Qiao');assert.equal(row.created_at,'now');}
const enabled=batchCaseStatus(published.next,[batch.created[0].id],'enable','enable time');
assert.equal(enabled.updated.length,1);assert.equal(enabled.next['test-cases'][0].enabled,true);assert.equal(enabled.next['test-cases'][1].enabled,false);
assert.equal(batchCaseStatus(enabled.next,[batch.created[0].id],'enable','later').unchanged.length,1);
const disabled=batchCaseStatus(enabled.next,[batch.created[0].id],'disable','disable time');assert.equal(disabled.next['test-cases'][0].enabled,false);
const invalidDb=structuredClone(batch.next);invalidDb['test-cases'][1].project='';
const partial=batchCaseStatus(invalidDb,batch.created.map(row=>row.id),'publish','partial time');
assert.equal(partial.updated.length,1);assert.equal(partial.failed.length,1);assert.equal(partial.next['test-cases'][1].publish_status,'未发布');
const disableDb=structuredClone(batch.next);
Object.assign(disableDb['test-cases'][0],{enabled:true,publish_status:'已发布'});
Object.assign(disableDb['test-cases'][1],{enabled:true,project:'',story_id:'missing',prompt:''});
disableDb['test-cases'][2].prerequisite_ids=[batch.created[0].id];
const disableBefore=JSON.stringify(disableDb),unrestricted=batchCaseStatus(disableDb,batch.created.map(row=>row.id),'disable','unrestricted time');
assert.equal(unrestricted.updated.length,2,'Published, unpublished, referenced and incomplete cases can all be disabled');
assert.deepEqual(unrestricted.failed,[]);
for(const row of unrestricted.next['test-cases'].slice(0,2)){assert.equal(row.enabled,false);assert.equal(row.updated_at,'unrestricted time');assert.equal(row.updated_by,'Joanna Qiao');}
assert.equal(unrestricted.next['test-cases'][0].publish_status,'已发布');assert.equal(unrestricted.next['test-cases'][1].publish_status,'未发布');
assert.equal(JSON.stringify(disableDb),disableBefore);
assert.equal(JSON.stringify(db),before,'Batch status changes never mutate the original database');
console.log('Quick case creation: shared scene, trimmed values, required fields, existing/batch ID conflicts, and new definitions passed.');
console.log('Group projects, atomic related writes, unpublished/disabled defaults, batch publish/enable/disable and partial validation failures passed.');
