const assert = require('node:assert/strict');
const fs = require('node:fs');
const {upgrade, planCaseImport, scenarioValueRows, recordElementUpdates} = require('../static/eval_catalog/catalog.js');
const db = upgrade(JSON.parse(fs.readFileSync(process.argv[2], 'utf8')), null);
const before = JSON.stringify(db);
const stage = db.stages.find(row => row.enabled && row.publish_status === '已发布');
const story = db.stories.find(row => row.enabled && row.publish_status === '已发布');
const factor = db.factors.find(row => row.enabled && row.publish_status === '已发布' && row.values.length);
const headers = ['用例 ID（必填，唯一）','Stage（必填）','Story（必填）','prompt_EN（必填）','prompt_CN（必填）','Skill','Factor 1','Factor 取值 1','Factor 2','Factor 取值 2','Factor 3','Factor 取值 3','所属项目（必填）','数据归属（默认 Eval-白盒）','道具','图片','可见性','可见用户组','Skill 类别'];
const values = ['IMPORT_001',stage.id,story.id,'Pick up the bowl.','拿起碗。','','','','','','','','预训练评测','','碗','','',''];
const parsed = rows => ({headers,header_row:1,sheet:'导入模板',rows:rows.map((values,index)=>({row:index+2,values})),issues:[]});
const plan = (rows,source=db,context={}) => planCaseImport(source,parsed(rows),context,'2026-10-20 12:00:00');
let result = plan([values]);
assert.deepEqual(result.errors, []);
assert.equal(result.created.length, 1);
const record = result.created[0];
assert.equal(record.publish_status, '未发布'); assert.equal(record.enabled, false);
assert.equal(record.data_owner, 'Eval-白盒'); assert.equal(record.visibility, '公开');
assert.deepEqual(record.skill_ids, []); assert.deepEqual(record.factors, []);
assert.equal(record.created_by, 'Joanna Qiao');
assert(scenarioValueRows(result.next).some(row=>row.stage_id===stage.id&&row.story_id===story.id&&!row.skill_id&&!row.factor_id));
assert.equal(JSON.stringify(db), before);

const filled = [...values];
filled[1]='导入新场域'; filled[2]='导入新任务'; filled[5]='导入抓取（Import Pick）\n导入放置（Import Place）';filled[18]='动作类\n动作类';
filled[6]=factor.id; filled[7]=factor.values[0].value; filled[13]='新数据归属';
result=plan([filled]);
assert.deepEqual(result.errors, []);
assert.equal(result.counts.stages, 1); assert.equal(result.counts.stories, 1);assert.equal(result.counts.skills, 2);
assert.equal(result.counts.scenarios, 2);assert.equal(result.counts.data_ownership_options, 1);
for(const kind of ['stages','stories','skills']){
 const added=result.next[kind].filter(row=>!db[kind].some(old=>old.id===row.id));
 assert(added.length); for(const item of added){assert.equal(item.project,'预训练评测');assert.equal(item.publish_status,'已发布');assert.equal(item.enabled,true);assert(item.display_id>0);}
}
assert(result.next.skills.some(row=>row.name_zh==='导入抓取'&&row.name_en==='Import Pick'&&row.category==='动作类'));
assert.equal(JSON.stringify(db), before, 'Planning does not write related definitions');
const more=[...filled];more[0]='IMPORT_002';
const batch=plan([filled,more]);
assert.equal(batch.counts.stages,1);assert.equal(batch.counts.skills,2);assert.equal(batch.counts.scenarios,2,'Identical scene tuples are deduplicated within a batch');
const again=[...filled];again[0]='IMPORT_003';
const appended=plan([again],batch.next);
assert.deepEqual(appended.errors,[]);assert.equal(appended.counts.scenarios,0,'Existing scenes are reused');

function failed(rows,pattern,source=db){
 const result=plan(rows,source);
 assert.equal(result.next,null);assert.deepEqual(result.created,[]);
 assert(result.errors.some(error=>pattern.test(error.message)),JSON.stringify(result.errors));
 assert.equal(JSON.stringify(db),before,'Every failure leaves catalog and linked tables intact');
 return result;
}
let invalid=[...filled];invalid[4]='';
failed([filled,invalid],/prompt_CN/);
result=failed([values,values],/重复/);assert.deepEqual([...new Set(result.errors.map(error=>error.row))],[2,3]);
invalid=[...filled];invalid[12]='';failed([invalid],/所属项目/);
invalid=[...values];invalid[6]='not a defined Factor';invalid[7]='large';failed([invalid],/Factor.*层级不完整/);
invalid=[...values];invalid[6]=factor.id;invalid[7]='new valid value';result=plan([invalid]);assert.deepEqual(result.errors,[]);assert.equal(result.counts.factor_values,1);
invalid=[...values];invalid[6]=factor.id;failed([invalid],/同时填写/);
invalid=[...values];invalid[6]=factor.id;invalid[7]=factor.values[0].value;invalid[8]=factor.id;invalid[9]=factor.values[0].value;failed([invalid],/重复配置/);
invalid=[...values];invalid[5]='Only Chinese';failed([invalid],/中文（英文）/);
const inactive=structuredClone(db);inactive.stages.find(row=>row.id===stage.id).enabled=false;failed([values],/未启用/,inactive);
const ambiguous=structuredClone(db);ambiguous.stages.push({...stage,id:'ST_AMBIGUOUS',project:'预训练评测'});ambiguous.stages.find(row=>row.id===stage.id).project='预训练评测';
invalid=[...values];invalid[1]=stage.name;failed([invalid],/重名/,ambiguous);

invalid=[...values];invalid[16]='受限';failed([invalid],/可见用户组/);
invalid[17]='missing group';failed([invalid],/不存在/);
invalid[17]='质量组\n研发组';
result=plan([invalid],db,{userGroups:[{id:'G1',name:'质量组'},{id:'G2',name:'研发组'}]});
assert.deepEqual(result.errors,[]);assert.deepEqual(result.created[0].visible_group_ids,['G1','G2']);
invalid[16]='公开';failed([invalid],/应留空/);

const imageRow=[...values];imageRow[15]='a.png';failed([imageRow],/图片.*未找到/);
const dataImage={name:'a.png',src:'data:image/png;base64,AAAA'};
result=planCaseImport(db,{...parsed([imageRow]),embedded:{2:[dataImage]}},{},'now');
assert.deepEqual(result.errors,[]);assert.equal(result.created[0].attachments[0].role,'初始状态');
result=planCaseImport(db,{...parsed([values]),embedded:{2:[dataImage,dataImage]}},{});
assert.deepEqual(result.errors,[]);assert.equal(result.created[0].attachments.length,2);
result=planCaseImport(db,{...parsed([values]),embedded:{2:Array(4).fill(dataImage)}},{});
assert(result.errors.some(error=>/最多.*3/.test(error.message)));

const punctuation=structuredClone(db);const special=punctuation.factors.find(row=>row.id===factor.id);special.values=[{value:'球体，圆弧类'},{value:'大'},{value:'小'}];special.default_value='大';
invalid=[...values];invalid[6]=factor.id;invalid[7]='球体，圆弧类';
result=plan([invalid],punctuation);assert.deepEqual(result.errors,[]);assert.deepEqual(result.created[0].factors[0].values,['球体，圆弧类'],'Exact complete values take priority over delimiters');
invalid[7]='大，小';result=plan([invalid],punctuation);assert.deepEqual(result.created[0].factors[0].values,['大','小']);

for(const input of [
 {...parsed([values]),issues:[{row:2,message:'不支持公式'}]},
 {...parsed([values]),headers:[...headers,'unknown field']},
 {...parsed([values]),headers:headers.map(value=>value.startsWith('Story')?'Story changed':value)},
 parsed([])
]){result=planCaseImport(db,input,{});assert(result.errors.length);assert.equal(result.next,null);}
assert.equal(JSON.stringify(db),before);
// Existing IDs follow the selected strategy; duplicated IDs within the file remain errors.
const existingDb=structuredClone(db),original=existingDb['test-cases'][0];
Object.assign(original,{publish_status:'已发布',enabled:true,visibility:'公开',visible_group_ids:[],created_at:'2024-01-01 10:00:00',created_by:'Original Creator',updated_at:'2024-02-01 10:00:00',updated_by:'Original Updater',tag_ids:['KEEP_TAG'],update_history:[]});
const existingBefore=JSON.stringify(existingDb),replacement=[...filled];replacement[0]=original.id;
result=plan([replacement],existingDb);
assert.deepEqual(result.errors,[]);assert.equal(result.skipped.length,1);assert.equal(result.created.length,0);assert.equal(result.updated.length,0);
assert.deepEqual(result.next['test-cases'],existingDb['test-cases']);
assert.equal(result.counts.stages,0);assert.equal(result.counts.stories,0);assert.equal(result.counts.skills,0);assert.equal(result.counts.scenarios,0);assert.equal(result.counts.data_ownership_options,0,'Skipped rows must not create any related data');
const ignored=[...replacement];ignored[4]='';ignored[6]='Missing factor';ignored[7]='Missing value';ignored[16]='wrong visibility';
result=planCaseImport(existingDb,{...parsed([ignored]),issues:[{row:2,message:'不支持公式'}]},{duplicateMode:'skip'},'now');
assert.deepEqual(result.errors,[]);assert.equal(result.skipped.length,1,'Skipped rows need no field validation');
result=plan([ignored,values],existingDb,{duplicateMode:'skip'});
assert.deepEqual(result.errors,[]);assert.equal(result.skipped.length,1);assert.equal(result.created.length,1);
assert.deepEqual(result.next['test-cases'].find(row=>row.id===original.id),original);

result=plan([replacement],existingDb,{duplicateMode:'update'});
assert.deepEqual(result.errors,[]);assert.equal(result.updated.length,1);assert.equal(result.created.length,0);assert.equal(result.skipped.length,0);
const changed=result.next['test-cases'].find(row=>row.id===original.id);
assert.equal(result.next['test-cases'].length,existingDb['test-cases'].length);
assert.equal(changed.prompt,replacement[3]);assert.equal(changed.prompt_cn,replacement[4]);
assert.equal(changed.publish_status,'已发布');assert.equal(changed.enabled,true);
assert.equal(changed.created_at,original.created_at);assert.equal(changed.created_by,original.created_by);
assert.equal(changed.updated_by,'Joanna Qiao');assert.equal(changed.updated_at,'2026-10-20 12:00:00');
assert.deepEqual(changed.tag_ids,['KEEP_TAG'],'A column absent from the template keeps its original value');
assert.deepEqual(changed.prerequisite_ids,original.prerequisite_ids);
const history=recordElementUpdates(existingDb,result.next,[],'2026-10-20 12:01:00')['test-cases'].find(row=>row.id===original.id).update_history;
assert.equal(history.length,1);assert(history[0].changes.some(change=>change.field==='prompt'));
assert.equal(JSON.stringify(existingDb),existingBefore);

const cleared=[...values];cleared[0]=original.id;
result=plan([cleared],existingDb,{duplicateMode:'update'});
assert.deepEqual(result.errors,[]);assert.deepEqual(result.updated[0].skill_ids,[]);assert.deepEqual(result.updated[0].factors,[]);assert.deepEqual(result.updated[0].attachments,[]);
const requiredColumns=[0,1,2,3,4,12],minimal={header_row:1,headers:requiredColumns.map(index=>headers[index]),rows:[{row:2,values:requiredColumns.map(index=>cleared[index])}]};
result=planCaseImport(existingDb,minimal,{duplicateMode:'update'},'now');
assert.deepEqual(result.errors,[]);assert.deepEqual(result.updated[0].factors,original.factors);assert.deepEqual(result.updated[0].attachments,original.attachments);
const restricted=structuredClone(existingDb);Object.assign(restricted['test-cases'][0],{visibility:'受限',visible_group_ids:['KEEP_GROUP']});
result=planCaseImport(restricted,minimal,{duplicateMode:'update',userGroups:[{id:'KEEP_GROUP',name:'保留组'}]},'now');
assert.deepEqual(result.errors,[]);assert.equal(result.updated[0].visibility,'受限');assert.deepEqual(result.updated[0].visible_group_ids,['KEEP_GROUP']);

result=plan([replacement,values],existingDb,{duplicateMode:'update'});
assert.deepEqual(result.errors,[]);assert.equal(result.updated.length,1);assert.equal(result.created.length,1);
result=plan([ignored,values],existingDb,{duplicateMode:'update'});
assert.equal(result.next,null);assert.equal(result.updated.length,0);assert.equal(result.created.length,0,'A failed update must also block the new cases');
for(const duplicateMode of ['update','skip']){
 result=plan([replacement,replacement],existingDb,{duplicateMode});assert.equal(result.next,null);assert.deepEqual([...new Set(result.errors.filter(error=>/在文件/.test(error.message)).map(error=>error.row))],[2,3]);
}
result=plan([values],existingDb,{duplicateMode:'invalid'});assert.equal(result.next,null);assert(result.errors.some(error=>/处理方式/.test(error.message)));
assert.equal(JSON.stringify(existingDb),existingBefore);
console.log('Import validation: live headers, all-or-nothing writes, linked elements/scenes, duplicates, required fields, groups, factors and images passed.');
console.log('Duplicate modes: skip without side effects, atomic updates, protected metadata, absent/empty optional fields and history passed.');
