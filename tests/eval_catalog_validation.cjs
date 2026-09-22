const assert=require('node:assert/strict');
const {validate,references}=require('../static/eval_catalog/catalog.js');
const db=JSON.parse(require('node:fs').readFileSync(process.argv[2],'utf8'));
for(const [kind,rows] of Object.entries(db))for(const r of rows)assert.deepEqual(validate(db,kind,r,r.id),[],`${kind}: ${r.id}`);
for(const [kind,rows] of Object.entries(db))for(const r of rows){
  assert(['已发布','未发布'].includes(r.publish_status),`${kind}: invalid publish status`);
  assert.equal(typeof r.enabled,'boolean',`${kind}: enabled must be boolean`);
}
assert.equal(validate(db,'stories',{...db.stories[0],publish_status:'启用'},db.stories[0].id).some(x=>x.includes('发布状态')),true);
assert.equal(validate(db,'stories',{...db.stories[0],enabled:false},db.stories[0].id).some(x=>x.includes('引用')),true);
const case0=structuredClone(db['test-cases'][0]);
const multiValueCase={...case0,factors:[{factor_id:'FC_SIZE',values:['小','适中']}]};
assert.deepEqual(validate(db,'test-cases',multiValueCase,case0.id),[]);
assert(validate(db,'test-cases',{...multiValueCase,factors:[{factor_id:'FC_SIZE',values:[]}]},case0.id).length);
assert(validate(db,'test-cases',{...multiValueCase,factors:[{factor_id:'FC_SIZE',values:['小','未知']}]},case0.id).length);
const multiValueDb={...db,'test-cases':[multiValueCase]};
const sizeFactor=db.factors.find(f=>f.id==='FC_SIZE');
assert(validate(multiValueDb,'factors',{...sizeFactor,values:sizeFactor.values.filter(v=>v.value!=='小')},sizeFactor.id).some(x=>x.includes('引用')));
assert(validate(db,'test-cases',{...case0,story_id:'missing'},case0.id).length);
assert(validate(db,'test-cases',{...case0,skill_ids:[]},case0.id).length);
assert(validate(db,'test-cases',{...case0,factors:[{factor_id:'FC_SIZE',value:'玻璃'}]},case0.id).length);
assert(validate(db,'test-cases',{...case0,factors:[...case0.factors,...case0.factors]},case0.id).length);
const pre=db['test-cases'].find(x=>x.id==='Study_47');
assert(validate(db,'test-cases',{...pre,prerequisite_ids:['Study_49']},pre.id).some(x=>x.includes('循环')));
const factor=db.factors.find(x=>x.id==='FC_SIZE');
assert(validate(db,'factors',{...factor,values:[{value:'大'}],default_value:'大'},factor.id).some(x=>x.includes('引用')));
assert(validate(db,'factors',{...factor,default_value:'未知'},factor.id).some(x=>x.includes('默认')));
assert(references(db,'stages','ST_STUDY').length>0);
assert(validate(db,'test-cases',{...case0,id:'NEW',name:'新用例',attachments:['javascript:alert(1)']},null).some(x=>x.includes('链接')));
console.log('Seed integrity and 10 relationship validation scenarios passed.');
const {schemas,listSchemas,scenarioSchema,fieldsFor,valueSchema,upgrade}=require('../static/eval_catalog/catalog.js');
const {caseOptions,caseOptionGroups,validateCaseSelection}=require('../static/eval_catalog/catalog.js');
const sceneDb=structuredClone(db);
sceneDb.scenarios=[{id:'CUSTOM_SCENE',stage_id:'ST_KITCHEN',story_id:'SR_IDENTIFY',skill_id:'SK_TURN',factor_id:'FC_POSITION',enabled:true}];
assert(caseOptions(sceneDb,{case_stage:'ST_KITCHEN'}).stories.some(r=>r.id==='SR_IDENTIFY'),'Include explicit cross-stage scene combinations');
const linkedCaseSelection={case_stage:'ST_KITCHEN',story_id:'SR_IDENTIFY',skill_ids:['SK_TURN'],factors:[{factor_id:'FC_POSITION',value:'特定位置'}]};
assert.deepEqual(caseOptions(sceneDb,linkedCaseSelection).skills.map(r=>r.id),['SK_TURN']);
assert.deepEqual(caseOptions(sceneDb,linkedCaseSelection).factors.map(r=>r.id),['FC_POSITION']);
assert.deepEqual(validateCaseSelection(sceneDb,linkedCaseSelection),[]);
assert.deepEqual(validateCaseSelection(sceneDb,{...linkedCaseSelection,skill_ids:['SK_PICK']}),[]);
assert.deepEqual(validateCaseSelection(sceneDb,{...linkedCaseSelection,factors:[{factor_id:'FC_COLOR',value:'红色'}]}),[]);
const grouped=caseOptionGroups(sceneDb,linkedCaseSelection);
for(const selection of [{},{case_stage:''}]){
 const stories=caseOptionGroups(sceneDb,selection).stories;
 assert.deepEqual(stories.scene,[],'Without Stage there are no scene Story options');
 assert.deepEqual(stories.other.map(row=>row.id),sceneDb.stories.filter(row=>row.enabled!==false).map(row=>row.id),'All enabled Stories remain selectable before Stage');
}
assert(grouped.stories.scene.some(row=>row.id==='SR_IDENTIFY'),'Selecting Stage restores linked Story grouping');
assert(grouped.skills.scene.some(r=>r.id==='SK_TURN'));
assert(grouped.skills.other.some(r=>r.id==='SK_PICK'));
assert(!grouped.skills.other.some(r=>r.id==='SK_TURN'));
assert(grouped.factors.other.some(r=>r.id==='FC_COLOR'));
sceneDb.skills.find(r=>r.id==='SK_PICK').enabled=false;
assert(!caseOptionGroups(sceneDb,linkedCaseSelection).skills.other.some(r=>r.id==='SK_PICK'));
assert(validateCaseSelection(sceneDb,{...linkedCaseSelection,skill_ids:['SK_PICK']}).length);
sceneDb.scenarios[0].enabled=false;
assert(!caseOptions(sceneDb,{case_stage:'ST_KITCHEN'}).stories.some(r=>r.id==='SR_IDENTIFY'));
assert.deepEqual(schemas.skills.map(x=>x[1]),['Skill','Skill_中文','Skill_EN','可能的动作描述','工具使用','SKill类别','备注','Key Factor']);
assert.deepEqual(schemas.factors.map(x=>x[1]),['Factor','一级（影响来源）','二级（维度组）','三级（具体 factor）','default 标准值','取值范围','取值说明','场景库目录表','父记录']);
assert.deepEqual(listSchemas.skills.map(x=>x[1]),['Skill','Skill_CN','Skill_EN','类别']);
assert.deepEqual(listSchemas.factors.map(x=>x[1]),['Factor','一级（影响来源）','二级（维度组）','三级（具体 factor）','default 标准值','取值范围']);
assert.deepEqual(schemas['test-cases'].map(x=>x[1]),['用例ID','前置用例','优先级','Stage','Story','prompt_EN','prompt_CN','Skill标签','Factor','Factor取值','道具','布置图片','Factor（选项版）','文本 8','属性','属性取值','查找引用','T-4','T-5']);
assert.equal(schemas.stories.length,13);
assert.deepEqual(fieldsFor('stories','scenario').map(x=>x[1]),['场域-Stage','任务-Story','原子能力-Skill','Factor','Factor 取值范围','用例数','所属项目','更新人','更新时间','创建人','创建时间']);
assert.equal(fieldsFor('stages')[1][1],'Stage 场域');
assert.equal(fieldsFor('stories')[1][1],'Story 任务');
assert.deepEqual(fieldsFor('stories').slice(2),fieldsFor('stages').slice(2));
assert.equal(fieldsFor('stories').length,fieldsFor('stages').length);
assert.deepEqual(listSchemas['test-cases'].map(x=>x[1]),['用例ID','Stage','Story','prompt_EN','prompt_CN','Skill标签','Factor','布置图片','数据归属','所属项目']);
assert.equal(fieldsFor('stories','scenario')[0][0],'stage_id');
assert(fieldsFor('stories','scenario','form').some(f=>f[0]==='stage_id'),'Scenario forms retain the Stage relationship');
assert.deepEqual(fieldsFor('stages','elements','form').map(f=>f[1]),['Stage 场域','所属项目','标签']);
assert.deepEqual(fieldsFor('stories','elements','form').map(f=>f[1]),['Story 任务','所属项目','标签']);
assert.deepEqual(fieldsFor('skills','elements','form').map(f=>f[1]),['Skill_中文','Skill_EN','可能的动作描述','类别','备注','所属项目','标签']);
assert.deepEqual(fieldsFor('factors','elements','form').map(f=>f[1]),['一级（影响来源）','二级（维度组）','三级（具体 factor）','取值说明','default 标准值','所属项目','标签']);
assert(!fieldsFor('factors','elements','form').find(f=>f[0]==='level3')[3]);
assert.equal(fieldsFor('factors','elements','form').find(f=>f[0]==='default_value')[2],'factorDefault');
assert.deepEqual(valueSchema.map(x=>x[1]),['取值','说明','举例']);
const legacy=structuredClone(db);legacy.skills[0].category='操作能力';legacy.skills[0].notes='本地修改保留';delete legacy.skills[0].action_descriptions;legacy.factors[0].values[0].field_16='历史值';
const migrated=upgrade(db,legacy);assert.equal(migrated.skills[0].category,'动作类');assert.equal(migrated.skills[0].notes,'本地修改保留');assert.deepEqual(migrated.skills[0].action_descriptions,db.skills[0].action_descriptions);assert.equal(migrated.factors[0].values[0].field_16,'历史值');
assert.deepEqual(validate(db,'test-cases',{...case0,priority:'P3'},case0.id),[]);
assert(validate(db,'factors',{...factor,parent_id:factor.id},factor.id).some(x=>x.includes('循环')));
const legacyStatus=structuredClone(db);delete legacyStatus.stories[0].publish_status;delete legacyStatus.stories[0].enabled;legacyStatus.stories[0].status='停用';
const migratedStatus=upgrade(db,legacyStatus);assert.equal(migratedStatus.stories[0].publish_status,'未发布');assert.equal(migratedStatus.stories[0].enabled,false);
console.log('Source field coverage, P3 priority, parent cycle and migration checks passed.');
const {filterRecords,nextDisplayId}=require('../static/eval_catalog/catalog.js');
const {publishedDeleteBlocked}=require('../static/eval_catalog/catalog.js');
for(const kind of ['stages','stories','skills','factors']){
 assert.deepEqual(fieldsFor(kind).slice(-4).map(f=>f[1]),['更新人','更新时间','创建人','创建时间']);
 assert(!fieldsFor(kind).some(f=>f[0]==='owner'));
 assert(!fieldsFor(kind,'elements','form').some(f=>['id','owner','publish_status','enabled'].includes(f[0])));
 assert.equal(publishedDeleteBlocked(kind,{publish_status:'已发布'}),true);
 assert.equal(publishedDeleteBlocked(kind,{publish_status:'未发布'}),false);
 assert.equal(fieldsFor(kind)[0][1],'ID');
 assert(!fieldsFor(kind,'elements','form').some(f=>f[0]==='display_id'));
 const original=upgrade(db,null)[kind];
 assert.equal(new Set(original.map(r=>r.display_id)).size,original.length);
 assert.deepEqual(filterRecords(db,kind,'elements',{}).map(r=>r.display_id),original.map(r=>r.display_id).sort((a,b)=>b-a),'Element lists sort by ID descending');
 const filtered=filterRecords(db,kind,'elements',{publishStatus:'已发布',enabled:'true'}).map(r=>r.display_id);
 assert.deepEqual(filtered,[...filtered].sort((a,b)=>b-a),'Filtering preserves ID descending order');
 assert.equal(filterRecords(db,kind,'elements',{query:'评测团队'}).length,0,'Name search must not match the owner');
 assert.equal(filterRecords(db,kind,'elements',{query:original[0].name}).some(r=>r.id===original[0].id),true);
 const saved=structuredClone(db);saved[kind].reverse();delete saved[kind][0].display_id;
 const upgraded=upgrade(db,saved)[kind];
 for(const r of upgraded)assert.equal(r.display_id,original.find(x=>x.id===r.id).display_id,'IDs stay stable across legacy migration and sorting');
 upgraded.unshift({...original[0],id:'CUSTOM',display_id:nextDisplayId(upgraded)});
 assert.equal(new Set(upgraded.map(r=>r.display_id)).size,upgraded.length);
}
const filterDb={...db,stories:[
 {id:'A',stage_id:'S1',skill_ids:['K1'],factor_ids:['F1']},
 {id:'B',stage_id:'S2',skill_ids:['K2'],factor_ids:['F2']},
 {id:'C',stage_id:'S3',skill_ids:['K1'],factor_ids:['F2']}
]};
assert.deepEqual(filterRecords(filterDb,'stories','scenario',{stages:['S1','S2']}).map(r=>r.id),['A','B']);
assert.deepEqual(filterRecords(filterDb,'stories','scenario',{stages:['S1','S2'],skills:['K2'],factors:['F2'],stories:['B','C']}).map(r=>r.id),['B']);
assert.equal(filterRecords(filterDb,'stories','scenario',{}).length,3);
const {scenarioRows,scenarioValueRows}=require('../static/eval_catalog/catalog.js');
const combinationsDb={...db,stories:[{...db.stories[0],id:'COMBINATIONS',stage_id:'S1',skill_ids:['K1','K2'],factor_ids:['F1','F2']}],factors:[{id:'F1',value_range:'大 / 小',values:[{value:'大'},{value:'小'}]},{id:'F2',values:[{value:'红'},{value:'蓝'}]}]};
const beforeExpansion=JSON.stringify(combinationsDb);
const expanded=scenarioRows(combinationsDb);
assert.deepEqual(expanded.map(r=>[r.stage_id,r.id,r.skill_id,r.factor_id,r.factor_range]),[
 ['S1','COMBINATIONS','K1','F1','大 / 小'],['S1','COMBINATIONS','K1','F2','红 / 蓝'],
 ['S1','COMBINATIONS','K2','F1','大 / 小'],['S1','COMBINATIONS','K2','F2','红 / 蓝']
]);
assert.equal(JSON.stringify(combinationsDb),beforeExpansion,'Expansion must not mutate source associations');
assert.deepEqual(filterRecords(combinationsDb,'stories','scenario',{skills:['K2'],factors:['F1']}).map(r=>[r.skill_id,r.factor_id,r.factor_range]),[['K2','F1','大'],['K2','F1','小']]);
assert.equal(filterRecords(combinationsDb,'stories','scenario',{skills:['K1','K2'],factors:['F1','F2']}).length,8);
assert.equal(filterRecords(combinationsDb,'stories','scenario',{stages:['other']}).length,0);
assert.equal(scenarioRows({...combinationsDb,stories:[{id:'EMPTY',skill_ids:[],factor_ids:[]}]}).length,1);
const seedExpanded=scenarioRows(db);
assert.equal(seedExpanded.length,db.stories.reduce((n,r)=>n+Math.max(1,r.skill_ids.length)*Math.max(1,r.factor_ids.length),0));
assert(seedExpanded.slice(0,10).every(r=>typeof r.skill_id==='string'&&typeof r.factor_id==='string'));
combinationsDb.factors[0].value_range='更新后的范围';
assert.equal(scenarioRows(combinationsDb)[0].factor_range,'更新后的范围');
const statuses={...db,stages:[{name:'Alpha',publish_status:'已发布',enabled:true},{name:'Alpha draft',publish_status:'未发布',enabled:false}]};
assert.equal(filterRecords(statuses,'stages','elements',{query:'ALPHA',publishStatus:'未发布',enabled:'false'}).length,1);
assert.equal(filterRecords(statuses,'stages','elements',{publishStatus:'未发布',enabled:'true'}).length,0);
assert(filterRecords(db,'skills','elements',{query:db.skills[0].name_en.toUpperCase()}).some(r=>r.id===db.skills[0].id));
console.log('Element IDs, name/status filters and multi-select scenario filters passed.');
const auditLegacy=structuredClone(db);
auditLegacy.stages.push({...auditLegacy.stages[0],id:'CUSTOM_AUDIT',created_by:undefined,updated_by:undefined,owner:'历史维护人'});
const auditMigrated=upgrade(db,auditLegacy).stages.at(-1);
assert.equal(auditMigrated.created_by,'历史维护人');
assert.equal(auditMigrated.updated_by,'历史维护人');
auditLegacy.stages.at(-1).created_by='原创建人';
assert.equal(upgrade(db,auditLegacy).stages.at(-1).created_by,'原创建人');
const teamLegacy=structuredClone(db);
for(const kind of ['stages','stories','skills','factors']){
 for(const row of teamLegacy[kind]){row.created_by='评测团队';row.updated_by='评测团队';}
 teamLegacy[kind].push({...teamLegacy[kind][0],id:'CUSTOM_TEAM'});
}
const peopleMigrated=upgrade(db,teamLegacy);
for(const kind of ['stages','stories','skills','factors']){
 for(const row of peopleMigrated[kind]){
  const expected=db[kind].find(x=>x.id===row.id);
  assert.equal(row.created_by,expected?.created_by||'Joanna Qiao');
  assert.equal(row.updated_by,expected?.updated_by||'Joanna Qiao');
  assert.notEqual(row.created_by,'评测团队');
  assert.notEqual(row.updated_by,'评测团队');
 }
}
const caseIds=filters=>filterRecords(db,'test-cases','elements',filters).map(r=>r.id);
assert.deepEqual(caseIds({query:'  bm_0  '}),['BM_05','BM_06','BM_07']);
assert.deepEqual(caseIds({query:'bowl'}),[],'Case ID search must not match prompt text');
assert.deepEqual(caseIds({stages:['ST_STUDY','ST_KITCHEN'],stories:['SR_READ','SR_FOLD'],skills:['SK_PICK','SK_FOLD'],factors:['FC_SHAPE','FC_MATERIAL']}),['Study_47','Kit_05']);
assert.deepEqual(caseIds({stages:['ST_STUDY'],stories:['SR_FOLD']}),[]);
assert.deepEqual(caseIds({factors:['FC_SIZE','FC_COLOR']}),['BM_05','BM_06','BM_14','BM_22']);
assert.deepEqual(caseIds({}),db['test-cases'].map(r=>r.id));
const caseStatuses=structuredClone(db);
caseStatuses['test-cases'][0].publish_status='未发布';
caseStatuses['test-cases'][0].enabled=false;
assert.deepEqual(filterRecords(caseStatuses,'test-cases','elements',{query:'bm_',stages:['ST_BM'],publishStatus:'未发布',enabled:'false'}).map(r=>r.id),['BM_05']);
assert.equal(filterRecords(caseStatuses,'test-cases','elements',{publishStatus:'未发布',enabled:'true'}).length,0);
console.log('Case ID search, combined element selections and case status filters passed.');
const imageSet=['初始状态','目标状态','关键物体位置'].map((role,i)=>({name:`scene-${i}.png`,src:`https://example.com/${i}.png`,role}));
assert.deepEqual(validate(db,'test-cases',{...case0,attachments:imageSet},case0.id),[]);
assert(validate(db,'test-cases',{...case0,attachments:[...imageSet,imageSet[0]]},case0.id).some(x=>x.includes('最多 3 张')));
assert(validate(db,'test-cases',{...case0,attachments:[{...imageSet[0],role:'其他'}]},case0.id).some(x=>x.includes('图片类型')));
assert(validate(db,'test-cases',{...case0,attachments:[{...imageSet[0],src:'javascript:alert(1)'}]},case0.id).some(x=>x.includes('链接')));
const legacyImages=structuredClone(db);
legacyImages['test-cases'][0].attachments=['https://example.com/old.png',...imageSet];
const upgradedImages=upgrade(db,legacyImages)['test-cases'][0].attachments;
assert.equal(upgradedImages.length,4,'Migration must not silently discard existing images');
assert.equal(upgradedImages[0].src,'https://example.com/old.png');
assert.deepEqual(upgradedImages.slice(1),imageSet,'Existing names and roles survive migration');
console.log('Image count, category, source validation and legacy migration passed.');
const {prepareElement,canPublish,elementName}=require('../static/eval_catalog/catalog.js');
for(const [kind,changes] of Object.entries({
 stages:{name:'测试场域'},stories:{name:'测试任务'},
 skills:{name_zh:'测试能力',name_en:'Test Skill',category:'辨别类',action_descriptions:['test'],notes:'测试备注'},
 factors:{category:'测试一级',dimension:'测试二级',level3:'测试三级',default_value:'标准',value_range:'标准 / 扩展',values:[{value:'标准',description:'说明',example:'举例'}]}
})){
 const row=prepareElement(db,kind,changes);
 assert.deepEqual(validate(db,kind,row,null),[],`${kind} saves with only visible fields`);
 assert.equal(row.publish_status,'未发布');
 assert(row.id&&!db[kind].some(x=>x.id===row.id));
 if(kind==='skills')assert.equal(elementName('skills',row),'测试能力（Test Skill）');
 if(kind==='factors')assert.equal(row.name,'测试一级-测试二级-测试三级');
 if(kind!=='factors'){
  assert(canPublish(kind,'elements',row));
  assert(!canPublish(kind,'elements',{...row,publish_status:'已发布'}));
  assert.deepEqual(validate(db,kind,{...row,publish_status:'已发布'},row.id),[]);
  assert(publishedDeleteBlocked(kind,{...row,publish_status:'已发布'}));
 }
 const original=db[kind][0];
 const edited=prepareElement(db,kind,kind==='skills'?{name_zh:'新能力'}:kind==='factors'?{level3:'新三级'}:{name:'新名称'},original);
 assert.equal(edited.id,original.id);
 assert.equal(edited.created_by,original.created_by);
 assert.equal(edited.publish_status,original.publish_status);
 if(kind==='stories'){
  assert.equal(edited.stage_id,original.stage_id);
  assert.deepEqual(edited.skill_ids,original.skill_ids);
  assert.deepEqual(edited.factor_ids,original.factor_ids);
 }
 if(kind==='factors')assert.deepEqual(edited.values,original.values);
}
const collisionDb=structuredClone(db);
const candidate=prepareElement(collisionDb,'stages',{name:'新场域'});
collisionDb.stages.push({...candidate,display_id:1});
assert.notEqual(prepareElement(collisionDb,'stages',{name:'另一场域'}).id,candidate.id);
assert(!canPublish('stories','scenario',{publish_status:'未发布'}));
assert(!canPublish('factors','elements',{publish_status:'未发布'}));
const skillLegacy=structuredClone(db);skillLegacy.skills[0].category='辨别类 Skill';
assert.equal(upgrade(db,skillLegacy).skills[0].category,'辨别类');
console.log('Minimal element forms, generated IDs, retained associations and publish eligibility passed.');
const {factorValueOptions}=require('../static/eval_catalog/catalog.js');
assert.deepEqual(factorValueOptions([{value:' A '},{value:'B'},{value:''},{value:'A'}]),['A','B']);
const twoLevelFactor=prepareElement(db,'factors',{category:'测试一级',dimension:'测试二级',level3:'',default_value:'A',values:[{value:'A',description:'说明',example:'示例'}]});
assert.equal(twoLevelFactor.name,'测试一级-测试二级');
assert.deepEqual(validate(db,'factors',twoLevelFactor,null),[]);
assert.deepEqual(factorValueOptions([{value:'B'}]),['B'],'Removed values are no longer default choices');
const {batchScenarios,batchScenarioCount,groupScenarios,validateScenario}=require('../static/eval_catalog/catalog.js');
const batchDb=upgrade(db,null),batchBefore=JSON.stringify(batchDb);
const selection={stage_ids:['ST_BASIC','ST_KITCHEN'],story_ids:['SR_READ','SR_STORE'],skill_ids:['SK_PICK','SK_PLACE'],factors:['FC_SIZE','FC_COLOR'].map(factor_id=>({factor_id,values:factorValueOptions(batchDb.factors.find(f=>f.id===factor_id).values)}))};
const batch=batchScenarios(batchDb,selection,'2026-09-17 12:00');
assert.equal(batch.length,8*selection.factors.reduce((sum,f)=>sum+f.values.length,0));
assert.equal(new Set(batch.map(x=>x.id)).size,batch.length);
assert.equal(batchScenarioCount(selection),batch.length);
assert.equal(JSON.stringify(batchDb),batchBefore,'Batch creation does not modify element definitions');
for(const row of batch){assert.equal(row.publish_status,'未发布');assert.deepEqual(validateScenario(batchDb,row),[]);}
batchDb.scenarios=batch;
assert.equal(batchScenarios(batchDb,selection,'later').length,0,'Existing combinations are skipped');
assert.deepEqual(upgrade(db,batchDb).scenarios,batch,'Saved combinations survive reload');
assert.equal(filterRecords(batchDb,'stories','scenario',{stages:['ST_BASIC'],stories:['SR_READ'],skills:['SK_PICK'],factors:['FC_SIZE']}).length,3);
for(const [target,id] of [['stages','ST_BASIC'],['stories','SR_READ'],['skills','SK_PICK'],['factors','FC_SIZE']])assert(references(batchDb,target,id).some(x=>x.startsWith('场景 ')));
assert.throws(()=>batchScenarios(batchDb,{...selection,skill_ids:[]},'now'),/请选择 Skill/);
assert.throws(()=>batchScenarios(batchDb,{...selection,factors:[{factor_id:'missing',values:['A']}]},'now'),/不存在/);
assert.throws(()=>batchScenarios(batchDb,{...selection,factors:[]},'now'),/请添加 Factor/);
assert.throws(()=>batchScenarios(batchDb,{...selection,factors:[{factor_id:'FC_SIZE',values:[]}]},'now'),/Factor 取值/);
assert.throws(()=>batchScenarios(batchDb,{...selection,factors:[{factor_id:'FC_SIZE',values:['missing']}]},'now'),/无效/);
const disabledDb=structuredClone(batchDb);disabledDb.stages.find(x=>x.id==='ST_BASIC').enabled=false;
assert.throws(()=>batchScenarios(disabledDb,selection,'now'),/停用/);
for(const mode of ['Stage','Story','Skill','Factor']){
 const original=scenarioRows(batchDb),grouped=groupScenarios(original,mode);
 assert.equal(grouped.length,original.length);
 const seen=new Set();let previous=null;
 for(const row of grouped){const key=({Stage:row.stage_id,Story:row.story_id||row.id,Skill:row.skill_id,Factor:row.factor_id})[mode]||'';
  if(key!==previous){assert(!seen.has(key),`${mode} groups must be contiguous`);seen.add(key);previous=key;}
 }
}
console.log('Batch combinations, deduplication, persistence, references, filters and all aggregation modes passed.');
const {scenarioStats}=require('../static/eval_catalog/catalog.js');
for(const mode of ['Stage','Story','Skill','Factor']){
 const rows=scenarioRows(batchDb),stats=scenarioStats(batchDb,rows,mode);
 assert.equal(stats.reduce((sum,stat)=>sum+stat.count,0),rows.length);
 assert.deepEqual(scenarioStats(batchDb,[],mode),[]);
}
const filteredStatsRows=filterRecords(batchDb,'stories','scenario',{stages:['ST_BASIC'],stories:['SR_READ']});
assert.deepEqual(scenarioStats(batchDb,filteredStatsRows,'Story'),[{id:'SR_READ',label:batchDb.stories.find(r=>r.id==='SR_READ').name,count:14}]);
const readRows=scenarioRows(batchDb).filter(r=>(r.story_id||r.id)==='SR_READ');
assert(readRows.some(r=>r.scenario_record)&&readRows.some(r=>!r.scenario_record));
assert.equal(scenarioStats(batchDb,readRows,'Story').length,1,'Legacy and new rows for the same story share one count');
assert.equal(scenarioStats(batchDb,readRows,'Story')[0].count,readRows.length);
assert.deepEqual(scenarioStats(batchDb,[{skill_id:''},{skill_id:'missing'}],'Skill'),[{id:'',label:'未关联',count:1},{id:'missing',label:'missing',count:1}]);
console.log('Aggregation counts, filtered totals, mixed story rows and missing associations passed.');
const {scenarioCaseCount}=require('../static/eval_catalog/catalog.js');
const countDb={stories:[{id:'story',stage_id:'stage'}],'test-cases':[
 {id:'one',story_id:'story',skill_ids:['skill','other-skill'],factors:[{factor_id:'factor',values:['a','b']},{factor_id:'other-factor',value:'c'}]},
 {id:'two',case_stage:'stage',story_id:'story',skill_ids:['skill'],factors:[{factor_id:'factor',value:'a'}],enabled:false,publish_status:'未发布'},
 {id:'three',case_stage:'other-stage',story_id:'story',skill_ids:['skill'],factors:[{factor_id:'factor'}]},
 {id:'four',case_stage:'stage',story_id:'other-story',skill_ids:['skill'],factors:[{factor_id:'factor'}]},
 {id:'five',case_stage:'stage',story_id:'story',skill_ids:['skill'],factors:[]}
]};
const countedRow={id:'story',stage_id:'stage',skill_id:'skill',factor_id:'factor'};
assert.equal(scenarioCaseCount(countDb,countedRow),2,'Each matching case counts once regardless of values or status');
assert.equal(scenarioCaseCount(countDb,{...countedRow,id:'new-scene',story_id:'story'}),2,'Explicit and legacy scenes match the same story');
assert.equal(scenarioCaseCount(countDb,{...countedRow,stage_id:'other-stage'}),1);
assert.equal(scenarioCaseCount(countDb,{...countedRow,skill_id:'other-skill',factor_id:'other-factor'}),1);
assert.equal(scenarioCaseCount(countDb,{...countedRow,factor_id:''}),1,'Empty factor only matches cases without factors');
assert.equal(scenarioCaseCount(countDb,{...countedRow,skill_id:''}),0);
assert.equal(scenarioCaseCount(countDb,{...countedRow,factor_id:'missing'}),0);
countDb['test-cases'].splice(0,1);
assert.equal(scenarioCaseCount(countDb,countedRow),1,'Counts use current case records after deletion');
countDb['test-cases'][0].skill_ids=['other-skill'];
assert.equal(scenarioCaseCount(countDb,countedRow),0,'Counts follow edited case associations');
console.log('Scenario case counts, complete combination matching, multiple values and live records passed.');
for(const kind of ['stages','stories','skills','factors']){
 assert.deepEqual(new Set(db[kind].map(row=>row.publish_status)),new Set(['已发布','未发布']));
 const oldDemo=structuredClone(db),draft=oldDemo[kind].find(row=>row.publish_status==='未发布');
 draft.publish_status='已发布';
 assert.equal(upgrade(db,oldDemo)[kind].find(row=>row.id===draft.id).publish_status,'未发布');
 draft.updated_at='2026-09-18 10:00';
 assert.equal(upgrade(db,oldDemo)[kind].find(row=>row.id===draft.id).publish_status,'已发布','Preserve user publishing and edits');
}
assert.deepEqual(new Set(scenarioRows(db).map(row=>row.publish_status)),new Set(['已发布','未发布']));
console.log('Mixed catalog demo statuses and preservation of user status changes passed.');
for(const kind of ['stages','stories','skills','factors']){
 const fields=fieldsFor(kind),statusIndex=fields.findIndex(f=>f[0]==='publish_status');
 assert.equal(fields[statusIndex-1][0],'project');
 for(const project of ['预训练评测','后训练评测']){
  const expected=db[kind].filter(row=>row.project===project);
  assert(expected.length>0);
  const filtered=filterRecords(db,kind,'elements',{project});
  assert.equal(filtered.length,expected.length);
  assert(filtered.every(row=>row.project===project));
  const combined=filterRecords(db,kind,'elements',{project,publishStatus:'未发布',query:expected[0].name});
  assert(combined.every(row=>row.project===project&&row.publish_status==='未发布'&&elementName(kind,row).includes(expected[0].name)));
 }
}
const projectDb=upgrade(db,null);
const postBatch=batchScenarios(projectDb,{...selection,project:'后训练评测'},'now');
assert(postBatch.every(row=>row.project==='后训练评测'));
projectDb.scenarios=postBatch;
const postRows=filterRecords(projectDb,'stories','scenario',{project:'后训练评测',stages:['ST_BASIC']});
assert.equal(postRows.length,28);
assert(postRows.every(row=>row.project==='后训练评测'));
assert.equal(scenarioStats(projectDb,postRows,'Story').reduce((sum,row)=>sum+row.count,0),28);
assert.throws(()=>batchScenarios(db,{...selection,project:'其他'},'now'),/所属项目/);
const projectLegacy=structuredClone(projectDb);
for(const kind of ['stages','stories','skills','factors'])for(const row of projectLegacy[kind])delete row.project;
delete projectLegacy.scenarios[0].project;
projectLegacy.stages[0].project='后训练评测';
const projectUpgraded=upgrade(db,projectLegacy);
assert.equal(projectUpgraded.stages[0].project,'后训练评测');
assert.equal(projectUpgraded.scenarios[0].project,projectUpgraded.stories.find(row=>row.id===projectUpgraded.scenarios[0].story_id).project);
assert.equal(projectUpgraded.factors[0].project,db.factors[0].project);
const projectElement=prepareElement(db,'stages',{name:'项目场域',project:'后训练评测'});
assert.equal(projectElement.project,'后训练评测');
assert.deepEqual(validate(db,'stages',projectElement,null),[]);
assert(validate(db,'stages',{...projectElement,project:'其他'},null).some(error=>error.includes('所属项目')));
assert(fieldsFor('test-cases').some(f=>f[0]==='project'));
const caseFilterDb={...db,'test-cases':[{...case0,id:'OWN1',data_owner:'Train-训练',project:'预训练评测'},{...case0,id:'OWN2',data_owner:'Train-训练',project:'后训练评测'},{...case0,id:'OWN3',data_owner:'Eval-白盒',project:'后训练评测'}]};
assert.deepEqual(filterRecords(caseFilterDb,'test-cases','elements',{dataOwner:'Train-训练',project:'后训练评测'}).map(r=>r.id),['OWN2']);
console.log('Project columns, combined filters, batch creation and legacy project migration passed.');
assert.deepEqual(scenarioValueRows(combinationsDb).map(row=>row.factor_range),['大','小','红','蓝','大','小','红','蓝']);
assert.equal(scenarioValueRows({...combinationsDb,stories:[{id:'EMPTY',skill_ids:[],factor_ids:[]}]}).length,1);
const valueDb={...combinationsDb,scenarios:[{id:'NEW',stage_id:'S1',story_id:'COMBINATIONS',skill_id:'K3',factor_id:'F2'}]};
assert.deepEqual(scenarioValueRows(valueDb).filter(row=>row.scenario_record).map(row=>row.factor_value),['红','蓝']);
const valueCases={stories:[{id:'S',stage_id:'ST'}],'test-cases':[
 {id:'A',story_id:'S',skill_ids:['K'],factors:[{factor_id:'F',values:['大','小','小']}]},
 {id:'B',story_id:'S',skill_ids:['K'],factors:[{factor_id:'F',value:'小'}]}
]};
for(const [value,count] of [['大',1],['小',2],['中',0]])assert.equal(scenarioCaseCount(valueCases,{id:'S',stage_id:'ST',skill_id:'K',factor_id:'F',factor_value:value}),count);
for(const mode of ['Stage','Story','Skill','Factor'])assert.equal(scenarioStats(db,scenarioValueRows(db),mode).reduce((sum,row)=>sum+row.count,0),scenarioValueRows(db).length);
console.log('Factor value rows, explicit scenes, empty placeholders and per-value case counts passed.');
assert(fieldsFor('skills','elements','form').find(field=>field[0]==='name_en')[3]);
assert(validate(db,'skills',{...db.skills[0],name_en:'  '},db.skills[0].id).some(error=>error.includes('Skill_EN')));
const categoryDb=upgrade(db,null);
categoryDb.skill_categories=['组合类'];
const customSkill=prepareElement(categoryDb,'skills',{name_zh:'组合能力',name_en:'Composite',category:'组合类',tag_ids:['act_pick','obj_phone']});
assert.deepEqual(validate(categoryDb,'skills',customSkill,null),[]);
categoryDb.skills.push(customSkill);
const categoryRestored=upgrade(db,categoryDb);
assert.deepEqual(categoryRestored.skill_categories,['组合类']);
assert.equal(categoryRestored.skills.at(-1).category,'组合类');
assert.deepEqual(categoryRestored.skills.at(-1).tag_ids,['act_pick','obj_phone']);
assert(validate(db,'skills',{...db.skills[0],category:'未知类别'},db.skills[0].id).some(error=>error.includes('类别')));
for(const kind of ['stages','stories','skills','factors']){
 assert.deepEqual(upgrade(db,null)[kind][0].tag_ids,[]);
 const tagged=structuredClone(db);tagged[kind][0].tag_ids=['act_pick'];
 assert.deepEqual(upgrade(db,tagged)[kind][0].tag_ids,['act_pick']);
}
console.log('Element field ordering, required Skill_EN, tags and persistent custom categories passed.');
const {saveScenarioRow}=require('../static/eval_catalog/catalog.js');
assert.deepEqual(fieldsFor('stories','scenario','form').map(f=>f[1]),['Stage','Story','Skill','Factor','Factor 取值','备注','所属项目','标签']);
const scenarioEditDb=upgrade(db,null),originalSceneRows=scenarioValueRows(scenarioEditDb);
const originalScene=originalSceneRows.find(row=>row.factor_value&&row.skill_id);
const sceneChanges={...originalScene,notes:'仅修改当前取值行',tag_ids:['act_pick'],project:'后训练评测',updated_at:'2026-09-20 12:00:00'};
assert.deepEqual(validateScenario(scenarioEditDb,sceneChanges),[]);
const savedSceneDb=saveScenarioRow(scenarioEditDb,sceneChanges),editedSceneRows=scenarioValueRows(savedSceneDb);
assert.deepEqual(savedSceneDb.stories,scenarioEditDb.stories,'Scene editing must preserve element definitions');
assert.deepEqual(editedSceneRows.filter(row=>row.row_key!==originalScene.row_key),originalSceneRows.filter(row=>row.row_key!==originalScene.row_key),'Sibling combinations and value rows stay unchanged');
const restoredScene=scenarioValueRows(upgrade(db,savedSceneDb)).find(row=>row.row_key===originalScene.row_key);
assert.equal(restoredScene.notes,sceneChanges.notes);
assert.equal(restoredScene.project,sceneChanges.project);
assert.deepEqual(restoredScene.tag_ids,['act_pick']);
assert.equal(restoredScene.updated_by,'Joanna Qiao');
assert(validateScenario(savedSceneDb,{...restoredScene,factor_value:'无效取值'}).some(error=>error.includes('Factor 的取值')));
const siblingScene=originalSceneRows.find(row=>row.row_key!==originalScene.row_key&&row.stage_id===originalScene.stage_id&&row.story_id===originalScene.story_id&&row.skill_id===originalScene.skill_id&&row.factor_id===originalScene.factor_id);
assert(siblingScene);
assert(validateScenario(scenarioEditDb,{...originalScene,factor_value:siblingScene.factor_value}).some(error=>error.includes('已存在')));
const explicitSceneDb={...scenarioEditDb,scenarios:[{...originalScene,id:'SC_EDIT',story_id:originalScene.story_id}]};
const explicitScene=scenarioValueRows(explicitSceneDb).find(row=>row.scenario_record);
const explicitSaved=saveScenarioRow(explicitSceneDb,{...explicitScene,notes:'独立场景备注',tag_ids:['q_success']});
assert.equal(scenarioValueRows(explicitSaved).find(row=>row.row_key===explicitScene.row_key).notes,'独立场景备注');
assert.deepEqual(scenarioValueRows(explicitSaved).filter(row=>row.row_key!==explicitScene.row_key),scenarioValueRows(explicitSceneDb).filter(row=>row.row_key!==explicitScene.row_key));
console.log('Scenario drawer fields, row isolation, persistence and Factor value validation passed.');
