(function(root){
'use strict';
let userGroups=[];
const labels={stages:'Stage',stories:'Story',skills:'Skill',factors:'Factor','test-cases':'评测用例'};
const projects=['预训练评测','后训练评测'];
const projectField=['project','所属项目','project',true];
const tagField=['tag_ids','标签','catalogTags[]'];
const dataOwnershipField=['data_owner','数据归属','dataOwnership',true];
const defaultDataOwnershipOptions=['Train-训练','Eval-白盒','Test-黑盒'];
let dataOwnershipValues=[...defaultDataOwnershipOptions];
function dataOwnershipOptions(){return dataOwnershipValues;}
function skillCategories(db){return [...new Set(['辨别类','动作类',...(db.skill_categories||[]),...db.skills.map(row=>row.category)].filter(Boolean))];}
const imageRoles=['初始状态','目标状态','关键物体位置'];
const validImageSource=src=>typeof src==='string'&&(/^https?:\/\/\S+$/i.test(src)||/^data:image\/(png|jpeg|webp|gif);base64,[a-z0-9+/=]+$/i.test(src));
function normalizeImages(images=[]){return images.map((item,index)=>typeof item==='string'?{src:item,name:'布置图片 '+(index+1),role:imageRoles[0]}:{...item});}
function conditionValues(f){return Array.isArray(f.values)?f.values:f.value?[f.value]:[];}
function references(db,kind,id){
 const refs=[];
 const scenarioKey={stages:'stage_id',stories:'story_id',skills:'skill_id',factors:'factor_id'}[kind];
 if(scenarioKey)(db.scenarios||[]).filter(x=>x[scenarioKey]===id).forEach(x=>refs.push('场景 '+x.id));
 if(scenarioKey)scenarioValueRows(db).filter(x=>db.scenario_row_edits?.[x.row_key]&&x[scenarioKey]===id).forEach(x=>refs.push('场景 '+x.id));
 if(kind==='stories')db.stories.filter(x=>x.parent_id===id).forEach(x=>refs.push('子 Story '+x.name));
 if(kind==='skills'){
  db.stories.filter(x=>(x.skill_ids||[]).includes(id)).forEach(x=>refs.push('Story '+x.name));
  db.skills.filter(x=>(x.tool_usage||[]).includes(id)).forEach(x=>refs.push('Skill '+x.name));
 }
 if(kind==='factors'){
  db.stories.filter(x=>(x.factor_ids||[]).includes(id)).forEach(x=>refs.push('Story '+x.name));
  db.factors.filter(x=>x.id!==id&&(x.parent_id===id||x.values.some(v=>v.factor_id===id||(v.linked_factor_ids||[]).includes(id)))).forEach(x=>refs.push('Factor '+x.name));
 }
 if(kind==='stages') db.stories.filter(x=>x.stage_id===id).forEach(x=>refs.push('Story '+x.name));
 db['test-cases'].forEach(x=>{if((kind==='stages'&&x.case_stage===id)||(kind==='stories'&&x.story_id===id)||(kind==='skills'&&x.skill_ids.includes(id))||(kind==='factors'&&(x.factors.some(f=>f.factor_id===id)||(x.factor_option_ids||[]).includes(id)))||(kind==='test-cases'&&x.prerequisite_ids.includes(id)))refs.push('用例 '+x.id);});
 return refs;
}
function validate(db,kind,r,editing){
 const errors=[]; const has=(k,id)=>db[k].some(x=>x.id===id);const active=(k,id)=>db[k].some(x=>x.id===id&&x.enabled!==false);
 if(!r.id||!/^[-A-Za-z0-9_]+$/.test(r.id)) errors.push('编号只能包含字母、数字、下划线或短横线');
 if(!(r.name||'').trim()) errors.push('请填写名称');
 if(db[kind].some(x=>x.id===r.id&&x.id!==editing))errors.push('编号已存在');
 if(db[kind].some(x=>x.name.trim()===r.name.trim()&&x.id!==editing&&(kind!=='stories'||x.stage_id===r.stage_id)))errors.push('名称已存在');
 if(!['已发布','未发布'].includes(r.publish_status))errors.push('发布状态无效');
 if(kind!=='test-cases'&&!projects.includes(r.project))errors.push('请选择所属项目');
 if(!r.owner.trim()) errors.push('请填写负责人');
 if(editing && r.enabled === false && references(db, kind, editing).length)errors.push('此记录已被引用，请先调整关联后再关闭启用状态');
 if(kind==='stories'&&r.stage_id&&(!has('stages',r.stage_id)||(r.enabled!==false&&!active('stages',r.stage_id)))) errors.push('请选择启用的 Stage');
 if(kind==='skills'&&!skillCategories(db).includes(r.category))errors.push('请选择类别');
 if(kind==='skills'&&!(r.name_en||'').trim())errors.push('请填写 Skill_EN');
 for(const [key,target] of [['skill_ids','skills'],['factor_ids','factors'],['factor_option_ids','factors'],['tool_usage','skills']]){
  if((r[key]||[]).some(id=>!has(target,id)||(r.enabled!==false&&!active(target,id))))errors.push('关联的 '+labels[target]+' 不存在或未启用');
 }
 if(r.parent_id&&['stories','factors'].includes(kind)){
  let id=r.parent_id;const seen=new Set([r.id]);
  while(id){if(seen.has(id)){errors.push('父记录不能形成循环');break;}seen.add(id);const parent=db[kind].find(x=>x.id===id);if(!parent){errors.push('父记录不存在');break;}id=parent.parent_id;}
 }
 if(kind==='factors'){
  if(!r.category.trim()||!r.dimension.trim()) errors.push('请填写因素分类与维度');
  const values=r.values.map(x=>x.value);
  for(const v of r.values){
   if(v.factor_id&&v.factor_id!==r.id&&!has('factors',v.factor_id))errors.push('取值说明的 factor 不存在');
   if((v.linked_factor_ids||[]).some(id=>id!==r.id&&!has('factors',id)))errors.push('取值说明的关联 Factor 不存在');
  }
  if(!values.length||values.some(v=>!v.trim()))errors.push('至少填写一个非空标准取值');
  if(new Set(values).size!==values.length)errors.push('标准取值不能重复');
  if(r.default_value&&!values.includes(r.default_value))errors.push('默认值必须属于标准取值');
  if(db['test-cases'].some(x=>x.factors.some(f=>f.factor_id===r.id&&conditionValues(f).some(v=>!values.includes(v)))))errors.push('不能移除正在被用例引用的取值');
 }
 if(kind==='test-cases'){
  if(!['公开','受限'].includes(r.visibility))errors.push('请选择可见性：公开或受限');
  if(![...defaultDataOwnershipOptions,...(db.data_ownership_options||[])].includes(r.data_owner))errors.push('请选择有效的数据归属');
  if(!projects.includes(r.project))errors.push('请选择所属项目');
  if(r.visibility==='受限'&&Object.hasOwn(r,'visible_group_ids')){
   const groups=Array.isArray(r.visible_group_ids)?r.visible_group_ids:[];
   if(!groups.length)errors.push('受限可见性至少选择一个可见用户组');
   if(userGroups.length&&groups.some(id=>!userGroups.some(group=>group.id===id)))errors.push('可见用户组无效，请重新选择');
  }
  const story=db.stories.find(x=>x.id===r.story_id);
  if(!story||(r.enabled!==false&&(!active('stories',r.story_id)||!active('stages',r.case_stage||story.stage_id))))errors.push('请选择启用的 Story 和 Stage');
  if(!r.prompt.trim())errors.push('请填写 prompt_EN');
  if(!r.skill_ids.length||r.skill_ids.some(id=>!has('skills',id)||(r.enabled!==false&&!active('skills',id))))errors.push('至少选择一个启用的 Skill');
  if(!['P0','P1','P2','P3'].includes(r.priority))errors.push('请选择优先级');

  if(new Set(r.factors.map(f=>f.factor_id)).size!==r.factors.length)errors.push('同一 Factor 只能配置一次');
  for(const f of r.factors){const def=db.factors.find(x=>x.id===f.factor_id),values=conditionValues(f);if(!def||!values.length||values.some(v=>!def.values.some(x=>x.value===v))||(r.enabled!==false&&def.enabled===false))errors.push('Factor 或取值无效，请重新选择');}
  if(r.prerequisite_ids.some(id=>!has('test-cases',id)||(r.enabled!==false&&!active('test-cases',id))))errors.push('前置用例不存在或未启用');
  const graph=new Map(db['test-cases'].map(x=>[x.id,x.prerequisite_ids]));graph.set(r.id,r.prerequisite_ids);
  const visiting=new Set(),done=new Set();
  function cycle(id){if(visiting.has(id))return true;if(done.has(id))return false;visiting.add(id);if((graph.get(id)||[]).some(cycle))return true;visiting.delete(id);done.add(id);return false;}
  if(cycle(r.id))errors.push('前置用例不能形成循环依赖');
  const images=normalizeImages(r.attachments);
  if(images.length>3)errors.push('布置图片最多 3 张，请移除多余图片');
  if(images.some(x=>!validImageSource(x.src)))errors.push('布置图片需上传图片或填写 http / https 图片链接');
  if(images.some(x=>!imageRoles.includes(x.role)))errors.push('请选择布置图片类型：初始状态、目标状态或关键物体位置');
 }
 return [...new Set(errors)];
}
// Field labels and order transcribed from Feishu record details, including hidden fields.
const schemas={
 stages:[['name','1级-场域-Stage','text',true]],
 stories:[['stage_id','1级-场域-Stage','stages',true],['name','2级-任务-Story','text',true],['skill_ids','3级-原子能力-Skill','skills[]'],['factor_ids','4级-factor','factors[]'],['factor_values','factor取值','textarea'],['notes','备注','textarea'],['case_ids','用例id','computed'],['text3','文本 3','textarea'],['parent_id','父记录','stories'],['stage_count','unique stage cnt','computed'],['story_count','unique story cnt','computed'],['skill_count','unique skill count','computed'],['factor_count','unique factor cnt','computed']],
 skills:[['name','Skill','text',true],['name_zh','Skill_中文','text'],['name_en','Skill_EN','text'],['action_descriptions','可能的动作描述','lines'],['tool_usage','工具使用','skills[]'],['category','SKill类别','category'],['notes','备注','textarea'],['key_factor','Key Factor','textarea']],
 factors:[['name','Factor','text',true],['category','一级（影响来源）','text',true],['dimension','二级（维度组）','text',true],['level3','三级（具体 factor）','text'],['default_value','default 标准值','text'],['value_range','取值范围','textarea'],['values','取值说明','values'],['directory_ids','场景库目录表','computed'],['parent_id','父记录','factors']],
 'test-cases':[['id','用例ID','text',true],['prerequisite_ids','前置用例','test-cases[]'],['priority','优先级','priority'],['case_stage','Stage','stages',true],['story_id','Story','stories',true],['prompt','prompt_EN','textarea',true],['prompt_cn','prompt_CN','textarea'],['skill_ids','Skill标签','skills[]',true],['factor_ids','Factor','caseFactors'],['factor_values','Factor取值','caseValues'],['props','道具','textarea'],['attachments','布置图片','images'],['factor_option_ids','Factor（选项版）','factors[]'],['text8','文本 8','textarea'],['attributes','属性','textarea'],['attribute_values','属性取值','textarea'],['lookup_reference','查找引用','text'],['t4','T-4','text'],['t5','T-5','text']]
};
const listSchemas={...schemas,
 stages:[['name','Stage 场域','text',true]],
 stories:[['name','Story 任务','text',true]],
 skills:schemas.skills.filter(f=>!['action_descriptions','tool_usage','notes','key_factor'].includes(f[0])).map(([key,label,...rest])=>[key,{name_zh:'Skill_CN',category:'类别'}[key]||label,...rest]),
 factors:schemas.factors.filter(f=>!['parent_id','directory_ids','values'].includes(f[0])),
 'test-cases':[...schemas['test-cases'].filter(f=>!['prerequisite_ids','priority','props','factor_values','factor_option_ids','text8','attributes','attribute_values','lookup_reference','t4','t5'].includes(f[0])),dataOwnershipField,projectField]
};
const scenarioSchema=[['stage_id','场域-Stage','stages'],['name','任务-Story','text'],['skill_id','原子能力-Skill','skills'],['factor_id','Factor','factors'],['factor_range','Factor 取值范围','text'],['case_count','用例数','computed']];
const batchScenarioSchema=[['stage_ids','Stage','stages[]',true],['story_ids','Story','stories[]',true],['skill_ids','Skill','skills[]',true]];
const scenarioEditSchema=[['stage_id','Stage','stages',true],['story_id','Story','stories',true],['skill_id','Skill','skills',true],['factor_id','Factor','factors',true]];
const scenarioFormSchema=[...scenarioEditSchema,['factor_value','Factor 取值','scenarioValue'],['notes','备注','textarea'],projectField,tagField];
const scenarioEditableFields=scenarioFormSchema.filter(([key])=>['notes','project','tag_ids'].includes(key));
const valueSchema=[['value','取值','text'],['description','说明','textarea'],['example','举例','textarea']];
const elementForms={
 stages:[['name','Stage 场域','text',true]],
 stories:[['name','Story 任务','text',true]],
 skills:[['name_zh','Skill_中文','text',true],['name_en','Skill_EN','text',true],['action_descriptions','可能的动作描述','lines'],['category','类别','category',true],['notes','备注','textarea']],
 factors:[['category','一级（影响来源）','text',true],['dimension','二级（维度组）','text',true],['level3','三级（具体 factor）','text'],['values','取值说明','values'],['default_value','default 标准值','factorDefault']]
};
const systemSchema=[['publish_status','发布状态','publish_status'],['enabled','启用状态','enabled'],['id','平台编号','text',true],['owner','负责人','text',true],['created_at','创建时间','computed'],['updated_at','更新时间','computed']];
const listSystemSchema=[projectField,['publish_status','发布状态','publish_status'],['enabled','启用状态','enabled'],['updated_by','更新人','computed'],['updated_at','更新时间','computed'],['created_by','创建人','computed'],['created_at','创建时间','computed']];
const caseSystemSchema=[['publish_status','发布状态','publish_status'],['enabled','启用状态','enabled'],['visibility','可见性','visibility'],['updated_by','更新人','computed'],['updated_at','更新时间','computed']];
const demoActor='Joanna Qiao';
function auditPerson(value,fallback=demoActor){return typeof value==='string'&&value.trim()&&value.trim()!=='评测团队'?value:fallback;}
const caseColumnWidths={id:120,prerequisite_ids:130,priority:88,case_stage:180,story_id:240,prompt:420,prompt_cn:360,skill_ids:180,factor_ids:260,attachments:140,data_owner:140,project:140,publish_status:110,enabled:100,visibility:110,updated_by:140,updated_at:180};
const factorColumnWidths={display_id:64,name:340,category:180,dimension:160,level3:220,default_value:160,value_range:280,publish_status:110,enabled:100,updated_by:140,updated_at:180,created_by:140,created_at:180};
const scenarioMinWidths={stage_id:240,name:300,skill_id:220,factor_id:340,factor_range:180,case_count:100,publish_status:110,enabled:100,updated_by:140,updated_at:180,created_by:140,created_at:180};
function factorValueOptions(values){return [...new Set(values.map(row=>row.value.trim()).filter(Boolean))];}
function fieldsFor(kind,section='elements',mode='list'){
 if(section==='scenario'&&mode==='form')return scenarioFormSchema;
 if(kind==='test-cases'&&mode==='form')return fieldsFor(kind,section,'create');
 if(kind==='test-cases'&&mode==='create')return ['prompt','prompt_cn','id','case_stage','story_id','skill_ids','factor_ids','factor_values','data_owner','project','tag_ids','props','attachments','visibility','visible_group_ids'].map(key=>{const f=key==='visible_group_ids'?['visible_group_ids','可见用户组','userGroups[]']:key==='data_owner'?dataOwnershipField:key==='project'?projectField:key==='tag_ids'?tagField:key==='visibility'?['visibility','可见性','visibility']:schemas[kind].find(f=>f[0]===key);return [f[0],key==='attachments'?'场景示意图':key==='skill_ids'?'Skill':f[1],['prompt','prompt_cn'].includes(key)?'text':f[2],...f.slice(3)];});
 if(mode==='form'&&section==='elements'&&elementForms[kind])return [...elementForms[kind],projectField,tagField];
 const fields=mode==='form'?schemas[kind]:section==='scenario'?scenarioSchema:listSchemas[kind];
 const catalogList=mode==='list'&&kind!=='test-cases';
 return [...(catalogList&&section==='elements'?[['display_id','ID','computed']]:[]),...fields,...(kind==='test-cases'?caseSystemSchema:catalogList?listSystemSchema:[projectField,...systemSchema]).filter(x=>!fields.some(f=>f[0]===x[0])&&!(catalogList&&section==='scenario'&&['publish_status','enabled'].includes(x[0])))];
}
function publishedDeleteBlocked(kind,row){return row?.publish_status==='已发布';}
function elementName(kind,row){return kind==='skills'?(row.name_zh||row.name)+(row.name_en?'（'+row.name_en+'）':''):row.name||'';}
function nextDisplayId(rows){return Math.max(0,...rows.map(r=>Number.isInteger(r.display_id)&&r.display_id>0?r.display_id:0))+1;}
function prepareElement(db,kind,changes,original=null){
 const defaults={id:'',name:'',project:projects[0],owner:demoActor,publish_status:'未发布',enabled:true,stage_id:'',skill_ids:[],factor_ids:[],values:[],tool_usage:[],action_descriptions:[],category:kind==='skills'?'动作类':'',dimension:''};
 const row={...defaults,...JSON.parse(JSON.stringify(original||{})),...changes};
 if(!original){
  const prefix={stages:'ST',stories:'SR',skills:'SK',factors:'FC'}[kind];
  let serial=nextDisplayId(db[kind]);
  do{row.id=prefix+'_'+String(serial++).padStart(2,'0');}while(db[kind].some(x=>x.id===row.id));
  row.publish_status='未发布';
 }
 if(kind==='skills')row.name=row.name_zh;
 if(kind==='factors')row.name=[row.category,row.dimension,row.level3].filter(Boolean).join('-');
 if(row.publish_status==='未发布')row.enabled=false;
 return row;
}
function canPublish(kind,section,row){return section==='elements'&&['stages','stories','skills'].includes(kind)&&row?.publish_status==='未发布';}
function elementHistoryValue(row,[key,,type]){
 if(!row)return null;
 if(type==='values')return (row[key]||[]).map(value=>Object.fromEntries(valueSchema.map(([key])=>[key,value[key]||''])));
 if(type==='catalogTags[]')return [...new Set(row[key]||[])].sort();
 if(type==='lines')return [...(row[key]||[])];
 if(type==='enabled')return row[key]!==false;
 return row[key]??'';
}
function historyValueText(value,[,,type],tags){
 if(value===null||value===''||Array.isArray(value)&&!value.length)return '--';
 if(type==='enabled')return value?'启用':'停用';
 if(type==='catalogTags[]')return value.map(id=>tags.find(tag=>tag.id===id)?.name||id).join('\n');
 if(type==='values')return value.map((item,index)=>`${index+1}. `+valueSchema.map(([key,label])=>`${label}：${item[key]||'--'}`).join('；')).join('\n');
 return Array.isArray(value)?value.join('\n'):String(value);
}
function recordElementUpdates(previous,next,tags=[],now=new Date().toLocaleString('sv-SE')){
 const result={...next};
 for(const kind of ['stages','stories','skills','factors']){
  const fields=[...fieldsFor(kind,'elements','form'),['publish_status','发布状态','text'],['enabled','启用状态','enabled']];
  result[kind]=next[kind].map(row=>{
   const old=previous[kind].find(item=>item.id===row.id),changes=[];
   for(const field of fields){
    const before=elementHistoryValue(old,field),after=elementHistoryValue(row,field);
    if(JSON.stringify(before)!==JSON.stringify(after))changes.push({field:field[0],label:field[1],before,after,before_text:historyValueText(before,field,tags),after_text:historyValueText(after,field,tags)});
   }
   const history=old?.update_history||[];
   if(!changes.length)return {...row,created_by:old.created_by,updated_by:old.updated_by,updated_at:old.updated_at,update_history:history};
   return {...row,created_by:auditPerson(old?.created_by),updated_by:demoActor,updated_at:now,update_history:[{updated_at:now,updated_by:demoActor,changes},...history]};
  });
 }
 result['test-cases']=recordCaseUpdates(previous,next,tags,now);
 return result;
}
function recordCaseUpdates(previous,next,tags,now){
 const fields=[...fieldsFor('test-cases','elements','form').filter(([key])=>!['factor_ids','factor_values'].includes(key)),['factors','Factor 配置','caseFactors'],['publish_status','发布状态','text'],['enabled','启用状态','enabled']];
 const value=(row,[key,,type],catalog)=>{
  if(key==='case_stage')return row.case_stage||catalog.stories.find(story=>story.id===row.story_id)?.stage_id||'';
  if(key==='factors')return (row.factors||[]).map(f=>({factor_id:f.factor_id,values:[...new Set(conditionValues(f))].sort()})).sort((a,b)=>a.factor_id.localeCompare(b.factor_id));
  if(type==='images')return normalizeImages(row[key]||[]);
  if(type.endsWith('[]'))return [...new Set(row[key]||[])].sort();
  return elementHistoryValue(row,[key,'',type]);
 };
 const text=(value,field,catalog)=>{
  const [key,,type]=field,resolve=(kind,id)=>{const row=catalog[kind]?.find(row=>row.id===id);return row?elementName(kind,row):id;};
  if(key==='factors')return value.map(f=>`${resolve('factors',f.factor_id)}：${f.values.join('、')||'--'}`).join('\n')||'--';
  if(type==='images')return value.map(image=>`${image.name}（${image.role}）`).join('\n')||'--';
  if(Object.hasOwn(labels,type))return resolve(type,value)||'--';
  if(type==='skills[]')return value.map(id=>resolve('skills',id)).join('\n')||'--';
  if(type==='userGroups[]')return value.map(id=>userGroups.find(group=>group.id===id)?.name||id).join('\n')||'--';
  return historyValueText(value,field,tags);
 };
 return (next['test-cases']||[]).map(row=>{
  const old=previous['test-cases']?.find(item=>item.id===row.id),history=Array.isArray(old?.update_history)?old.update_history:[];
  if(!old)return {...row,update_history:[]};
  const changes=fields.flatMap(field=>{
   const before=value(old,field,previous),after=value(row,field,next);
   return JSON.stringify(before)===JSON.stringify(after)?[]:[{field:field[0],label:field[1],before,after,before_text:text(before,field,previous),after_text:text(after,field,next)}];
  });
  if(!changes.length)return {...row,updated_at:old.updated_at,updated_by:old.updated_by,update_history:history};
  return {...row,updated_at:now,updated_by:demoActor,update_history:[{updated_at:now,updated_by:demoActor,changes},...history]};
 });
}
function scenarioRows(db){
 const factors=new Map(db.factors.map(row=>[row.id,row]));
 const legacy=db.stories.flatMap(story=>{
  // Keep incomplete definitions visible while expanding each populated relationship.
  const skills=story.skill_ids?.length?[...new Set(story.skill_ids)]:[''];
  const ids=story.factor_ids?.length?[...new Set(story.factor_ids)]:[''];
  return skills.flatMap(skill_id=>ids.map(factor_id=>{
   const factor=factors.get(factor_id);
   return {...story,skill_id,factor_id,factor_range:factor?.value_range||factorValueOptions(factor?.values||[]).join(' / ')};
  }));
 });
 const added=(db.scenarios||[]).map(row=>{
  const factor=factors.get(row.factor_id),story=db.stories.find(x=>x.id===row.story_id);
  return {...row,name:story?.name||row.story_id,factor_range:factor?.value_range||factorValueOptions(factor?.values||[]).join(' / '),scenario_record:true};
 });
 return [...added,...legacy];
}
function scenarioValueRows(db){
 const values=new Map(db.factors.map(factor=>[factor.id,factorValueOptions(factor.values||[])]));
 const deleted=new Set(db.scenario_deleted_rows||[]);
 return scenarioRows(db).flatMap(row=>{
  const options=row.scenario_record&&Object.hasOwn(row,'factor_value')?[row.factor_value]:values.get(row.factor_id)||[];
  return (options.length?options:['']).map(value=>{
   // Each expanded value keeps a stable source key so edits affect only that row.
   const row_key=JSON.stringify([row.scenario_record?'scenarios':'stories',row.id,row.stage_id,row.skill_id,row.factor_id,value]);
   const result={...row,story_id:row.story_id||row.id,factor_value:value,...db.scenario_row_edits?.[row_key],row_key};
   return {...result,name:db.stories.find(story=>story.id===result.story_id)?.name||result.story_id,factor_range:result.factor_value};
  }).filter(row=>!deleted.has(row.row_key));
 });
}
function saveScenarioRow(db,row){
 const original=scenarioValueRows(db).find(x=>x.row_key===row.row_key);
 if(!original)throw new Error('场景记录已不存在，请刷新列表');
 if(!projects.includes(row.project))throw new Error('请选择所属项目');
 const changes=Object.fromEntries(scenarioEditableFields.map(([key])=>[key,row[key]??original[key]]));
 return {...db,scenario_row_edits:{...db.scenario_row_edits,[row.row_key]:{...db.scenario_row_edits?.[row.row_key],...changes,updated_by:demoActor,updated_at:row.updated_at}}};
}
function deleteScenarioRow(db,rowKey){
 const row=scenarioValueRows(db).find(x=>x.row_key===rowKey);
 if(!row)throw new Error('场景记录已不存在，请刷新列表');
 if(scenarioCaseCount(db,row)>0)throw new Error('该场景已有评测用例，无法删除');
 return {...db,scenario_deleted_rows:[...new Set([...(db.scenario_deleted_rows||[]),rowKey])]};
}
function scenarioCaseCount(db,row){
 const storyId=row.story_id||row.id;
 const legacyStage=db.stories.find(story=>story.id===storyId)?.stage_id||'';
 return db['test-cases'].filter(testCase=>{
  const skills=testCase.skill_ids||[],factors=testCase.factors||[];
  return testCase.story_id===storyId&&(testCase.case_stage||legacyStage)===(row.stage_id||'')
   &&(row.skill_id?skills.includes(row.skill_id):skills.length===0)
   &&(row.factor_id?factors.some(factor=>factor.factor_id===row.factor_id&&(!Object.hasOwn(row,'factor_value')||conditionValues(factor).includes(row.factor_value))):factors.length===0);
 }).length;
}
function caseOptions(db,selection={}){
 const active=(kind,id)=>db[kind].some(r=>r.id===id&&r.enabled!==false);
 const rows=scenarioValueRows(db).filter(r=>r.enabled!==false&&active('stages',r.stage_id)&&active('stories',r.story_id||r.id)&&(!r.skill_id||active('skills',r.skill_id))&&(!r.factor_id||active('factors',r.factor_id)));
 const select=(kind,ids)=>db[kind].filter(r=>ids.has(r.id));
 const storyRows=selection.case_stage?rows.filter(r=>r.stage_id===selection.case_stage):[];
 const skillRows=storyRows.filter(r=>(r.story_id||r.id)===selection.story_id);
 const factorRows=skillRows.filter(r=>(selection.skill_ids||[]).includes(r.skill_id));
 return {stages:select('stages',new Set(rows.map(r=>r.stage_id))),stories:select('stories',new Set(storyRows.map(r=>r.story_id||r.id))),skills:select('skills',new Set(skillRows.map(r=>r.skill_id))),factors:select('factors',new Set(factorRows.map(r=>r.factor_id)))};
}
function caseOptionGroups(db,selection={}){
 const linked=caseOptions(db,selection);
 return Object.fromEntries(['stories','skills','factors'].map(kind=>{
  const ids=new Set(linked[kind].map(row=>row.id));
  return [kind,{scene:linked[kind],other:db[kind].filter(row=>row.enabled!==false&&!ids.has(row.id))}];
 }));
}
function factorValueGroups(db,selection={},factorId){
 const selectedSkills=new Set(selection.skill_ids||[]),scene=new Set(scenarioValueRows(db).filter(row=>row.stage_id===selection.case_stage&&(row.story_id||row.id)===selection.story_id&&selectedSkills.has(row.skill_id)&&row.factor_id===factorId).map(row=>row.factor_value).filter(Boolean));
 return {scene:[...scene],other:factorValueOptions(db.factors.find(row=>row.id===factorId)?.values||[]).filter(value=>!scene.has(value))};
}
function validateCaseSelection(db,r){
 const active=(kind,id)=>db[kind].some(row=>row.id===id&&row.enabled!==false),errors=[];
 if(!active('stages',r.case_stage)||!active('stories',r.story_id))errors.push('请选择启用的 Stage 和 Story');
 if(!r.skill_ids.length||r.skill_ids.some(id=>!active('skills',id)))errors.push('请选择启用的 Skill');
 if(r.factors.some(f=>!active('factors',f.factor_id)))errors.push('请选择启用的 Factor');
 return errors;
}
function scenarioGroupKey(row,mode){return ({Stage:row.stage_id,Story:row.story_id||row.id,Skill:row.skill_id,Factor:row.factor_id})[mode]||'';}
function scenarioStats(db,rows,mode){
 const target={Stage:'stages',Story:'stories',Skill:'skills',Factor:'factors'}[mode];
 const definitions=new Map(db[target].map(row=>[row.id,elementName(target,row)])),counts=new Map();
 for(const row of rows){const key=scenarioGroupKey(row,mode);counts.set(key,(counts.get(key)||0)+1);}
 return [...counts].map(([id,count])=>({id,label:id?(definitions.get(id)||id):'未关联',count}));
}
function groupScenarios(rows,mode){
 const groups=new Map();
 for(const row of rows){const key=scenarioGroupKey(row,mode);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(row);}
 return [...groups.values()].flat();
}
function validateScenario(db,row){
 const errors=[];
 for(const [key,label,target] of scenarioEditSchema){
  if(!db[target].some(x=>x.id===row[key]&&(row.enabled===false||x.enabled!==false)))errors.push('请选择启用的 '+label);
 }
 if(!['已发布','未发布'].includes(row.publish_status))errors.push('发布状态无效');
 if(!projects.includes(row.project))errors.push('请选择所属项目');
 if(row.row_key||Object.hasOwn(row,'factor_value')){
  const values=factorValueOptions(db.factors.find(f=>f.id===row.factor_id)?.values||[]);
  if(values.length?!values.includes(row.factor_value):!!row.factor_value)errors.push('请选择当前 Factor 的取值');
  if(scenarioValueRows(db).some(x=>!(row.row_key?x.row_key===row.row_key:x.scenario_record&&x.id===row.id)&&x.stage_id===row.stage_id&&x.story_id===row.story_id&&x.skill_id===row.skill_id&&x.factor_id===row.factor_id&&x.factor_value===row.factor_value))errors.push('场景组合及取值已存在');
 }else if(scenarioValueRows(db).some(x=>!(x.scenario_record&&x.id===row.id)&&x.stage_id===row.stage_id&&(x.story_id||x.id)===row.story_id&&x.skill_id===row.skill_id&&x.factor_id===row.factor_id))errors.push('场景组合已存在');
 return errors;
}
function batchFactorPairs(factors=[]){
 const pairs=new Map();
 for(const factor of factors)for(const value of factor.values||[]){
  const pair={factor_id:factor.factor_id,factor_value:value};
  pairs.set(JSON.stringify([pair.factor_id,pair.factor_value]),pair);
 }
 return [...pairs.values()];
}
function batchScenarioCount(selections){
 const factors=selections.factors||[];
 if(!factors.length||factors.some(f=>!f.factor_id||!f.values?.length))return 0;
 return batchScenarioSchema.reduce((count,[key])=>count*new Set(selections[key]||[]).size,batchFactorPairs(factors).length);
}
function batchScenarios(db,selections,now){
 const project=selections.project??projects[0];
 if(!projects.includes(project))throw new Error('请选择所属项目');
 const chosen={};
 for(const [key,label,type] of batchScenarioSchema){
  chosen[key]=[...new Set(selections[key]||[])];
  if(!chosen[key].length)throw new Error('请选择 '+label);
  if(chosen[key].some(id=>!db[type.slice(0,-2)].some(x=>x.id===id&&x.enabled!==false)))throw new Error(label+' 包含不存在或停用的要素');
 }
 const factors=selections.factors||[];
 if(!factors.length)throw new Error('请添加 Factor 并选择取值');
 for(const [index,selection] of factors.entries()){
  if(!selection.factor_id)throw new Error(`请选择第 ${index+1} 行的 Factor`);
  const factor=db.factors.find(f=>f.id===selection.factor_id&&f.enabled!==false);
  if(!factor)throw new Error('Factor 包含不存在或停用的要素');
  if(!selection.values?.length)throw new Error(`请选择「${factor.name}」的 Factor 取值`);
  const available=factorValueOptions(factor.values||[]);
  if(selection.values.some(value=>!available.includes(value)))throw new Error(`「${factor.name}」包含无效的 Factor 取值`);
 }
 const tuple=row=>JSON.stringify([row.stage_id,row.story_id||row.id,row.skill_id,row.factor_id,row.factor_value]);
 const existing=new Set(scenarioValueRows(db).filter(r=>r.skill_id&&r.factor_id).map(tuple));
 const ids=new Set((db.scenarios||[]).map(r=>r.id));let serial=1;
 const result=[];
 for(const stage_id of chosen.stage_ids)for(const story_id of chosen.story_ids)for(const skill_id of chosen.skill_ids)for(const pair of batchFactorPairs(factors)){
  const row={stage_id,story_id,skill_id,...pair};if(existing.has(tuple(row)))continue;
  while(ids.has('SC_'+String(serial).padStart(2,'0')))serial++;
  row.id='SC_'+String(serial++).padStart(2,'0');ids.add(row.id);existing.add(tuple(row));
  result.push({...row,project,publish_status:'未发布',enabled:true,created_by:demoActor,updated_by:demoActor,created_at:now,updated_at:now});
 }
 return result;
}
function filterRecords(db,kind,section,filters={}){
 const {query='',publishStatus='',enabled='',project='',dataOwner='',stages=[],stories=[],skills=[],factors=[]}=filters;
 const search=query.trim().toLowerCase();
 const rows=(section==='scenario'?scenarioValueRows(db):db[kind]).filter(r=>{
  if(project&&r.project!==project)return false;
  if(kind==='test-cases'&&dataOwner&&r.data_owner!==dataOwner)return false;
  if(section==='scenario')return (!stages.length||stages.includes(r.stage_id))&&(!stories.length||stories.includes(r.story_id||r.id))&&(!skills.length||skills.includes(r.skill_id))&&(!factors.length||factors.includes(r.factor_id));
  const text=kind==='test-cases'?r.id:elementName(kind,r);
  const matchesCommon=(!search||text.toLowerCase().includes(search))&&(!publishStatus||r.publish_status===publishStatus)&&(!enabled||(r.enabled!==false)===(enabled==='true'));
  if(kind==='test-cases')return matchesCommon&&(!stages.length||stages.includes(r.case_stage||db.stories.find(x=>x.id===r.story_id)?.stage_id))&&(!stories.length||stories.includes(r.story_id))&&(!skills.length||(r.skill_ids||[]).some(id=>skills.includes(id)))&&(!factors.length||(r.factors||[]).some(f=>factors.includes(f.factor_id)));
  return matchesCommon;
 });
 // 要素定义列表以首列 ID 降序展示；测试用例继续按其原有顺序展示。
 if(section==='elements'&&kind!=='test-cases')rows.sort((a,b)=>(b.display_id||0)-(a.display_id||0));
 return rows;
}
function upgrade(seed,saved){
 const result=JSON.parse(JSON.stringify(seed));
 result.data_ownership_options=[...new Set([...defaultDataOwnershipOptions,...(saved?.data_ownership_options||[])].filter(value=>typeof value==='string'&&value.trim()).map(value=>value.trim()))];
 result.skill_categories=[...new Set((saved?.skill_categories||[]).filter(value=>typeof value==='string'&&value.trim()).map(value=>value.trim()))];
 result.scenarios=JSON.parse(JSON.stringify(saved?.scenarios||seed.scenarios||[]));
 result.scenario_row_edits=JSON.parse(JSON.stringify(saved?.scenario_row_edits||{}));
 result.scenario_deleted_rows=[...new Set(saved?.scenario_deleted_rows||[])];
 for(const k of Object.keys(labels))if(Array.isArray(saved?.[k]))result[k]=saved[k].map(old=>{
  const base=seed[k].find(x=>x.id===old.id)||{};
  const row={...base,...old};
  if(k!=='test-cases'&&!old.update_history?.length)row.update_history=old.updated_at===base.updated_at?JSON.parse(JSON.stringify(base.update_history||[])):[];
  // Refresh untouched demo statuses without overwriting user edits or publish actions.
  if(k!=='test-cases'&&base.publish_status==='未发布'&&old.publish_status==='已发布'&&old.updated_at===base.updated_at)row.publish_status='未发布';
  if(k==='test-cases'&&old.prompt_cn===undefined){
   const translated=seed[k].find(x=>x.prompt===row.prompt);
   row.prompt_cn=translated?.prompt_cn||'';
  }
  if(old.status && old.publish_status===undefined)row.publish_status=old.status==='启用'?'已发布':'未发布';
  if(old.enabled===undefined)row.enabled=old.status!=='停用';
  for(const [key,,type] of schemas[k])if(row[key]===undefined)row[key]=type.endsWith('[]')||['lines','images','values'].includes(type)?[]:'';
  if(k==='factors')row.values=(row.values||[]).map(v=>({...Object.fromEntries(valueSchema.map(([key,,type])=>[key,type.endsWith('[]')?[]:''])),factor_id:row.id,linked_factor_ids:[row.id],...v}));
  return row;
 });
 for(const kind of ['stages','stories','skills','factors']){
  const seen=new Set();let next=nextDisplayId(result[kind]);
  for(const row of result[kind]){
   if(kind==='skills')row.category=['辨别类','辨别类 Skill','感知能力'].includes(row.category)?'辨别类':['操作能力','动作类 Skill',''].includes(row.category)||!row.category?'动作类':row.category;
   row.tag_ids=Array.isArray(row.tag_ids)?row.tag_ids:[];
   row.update_history=Array.isArray(row.update_history)?row.update_history:[];
   if(row.publish_status==='未发布')row.enabled=false;
   const base=seed[kind].find(x=>x.id===row.id);
   row.project=row.project||base?.project||projects[0];
   row.created_by=auditPerson(row.created_by,auditPerson(row.owner,auditPerson(base?.created_by)));
   row.updated_by=auditPerson(row.updated_by,auditPerson(row.owner,auditPerson(base?.updated_by)));
   if(!Number.isInteger(row.display_id)||row.display_id<1||seen.has(row.display_id))row.display_id=next++;
   seen.add(row.display_id);
  }
 }
 for(const row of result.scenarios)row.project=row.project||result.stories.find(story=>story.id===row.story_id)?.project||projects[0];
 for(const row of result['test-cases']){
  row.attachments=normalizeImages(row.attachments);
  row.data_owner=row.data_owner||'Eval-白盒';
  row.project=row.project||projects[0];
  row.tag_ids=Array.isArray(row.tag_ids)?row.tag_ids:[];
  row.visibility=row.visibility||'受限';
  row.updated_by=row.updated_by||row.owner||'评测团队';
 }
 return result;
}
const api={references,validate,schemas,listSchemas,scenarioSchema,fieldsFor,valueSchema,upgrade,filterRecords,elementName,nextDisplayId,normalizeImages,publishedDeleteBlocked,prepareElement,canPublish,recordElementUpdates,factorValueOptions,scenarioRows,scenarioValueRows,saveScenarioRow,deleteScenarioRow,scenarioCaseCount,groupScenarios,scenarioStats,batchScenarios,batchScenarioCount,validateScenario,caseOptions,caseOptionGroups,factorValueGroups,validateCaseSelection};if(typeof module!=='undefined'&&module.exports)module.exports=api;
if(!root.document)return;
const $=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
if(!$('ec-filter'))return;
const kind=$('catalog').dataset.kind,section=$('catalog').dataset.section,storageKey='quanta.eval-catalog.v1',seed=JSON.parse($('ec-seed').textContent);
const catalogTags=JSON.parse($('ec-tag-options').textContent);
const catalogTagTree=JSON.parse($('ec-tag-tree').textContent);
if($('ec-user-groups')){try{userGroups=JSON.parse($('ec-user-groups').textContent)||[];}catch(error){userGroups=[];}}
let valueRowCounter=0,currentValueOwnerPublished=false;
let db=upgrade(seed,null),page=1,editing=null,viewing=null,readonly=false,pendingDelete=null,returnFocus=null,batchCreating=false,scenarioEditing=false,pendingCollection=null,caseCreating=false;
let editingScenarioKey=null;
let pendingScenarioKey=null;
let pendingCaseStories=[];
try{db=upgrade(seed,JSON.parse(localStorage.getItem(storageKey)||'null'));dataOwnershipValues=[...db.data_ownership_options];}catch(e){toast('本地存储不可用');}
const clone=x=>JSON.parse(JSON.stringify(x)),name=(k,id)=>db[k].find(x=>x.id===id)?.name||id||'—';
function persist(next){try{const updated=recordElementUpdates(db,next,catalogTags);localStorage.setItem(storageKey,JSON.stringify(updated));db=updated;return true;}catch(e){$('ec-error').textContent='保存失败：浏览器存储不可用或空间不足。';toast('保存失败，修改未生效');return false;}}
function toast(message){if(root.showToast)root.showToast(message);else $('ec-error').textContent=message;}
function show(id){returnFocus=document.activeElement;$(id).classList.add('active');document.body.style.overflow='hidden';$(id).querySelector('button,input,select')?.focus();}
function close(id){$(id).classList.remove('active');document.body.style.overflow='';returnFocus?.focus();}
function computed(r,key){
 if(key==='case_count')return scenarioCaseCount(db,r);
 if(key==='case_stage')return r.case_stage||db.stories.find(x=>x.id===r.story_id)?.stage_id||'';
 if(key==='case_ids')return db['test-cases'].filter(x=>x.story_id===r.id).map(x=>x.id);
 if(key==='directory_ids')return db.stories.filter(x=>(x.factor_ids||[]).includes(r.id)).map(x=>x.name);
 if(key==='stage_count')return db.stages.length;
 if(key==='story_count')return db.stories.length;
 if(key==='skill_count')return db.skills.length;
 if(key==='factor_count')return db.factors.length;
 return r[key]??'';
}
function display(r,[key,label,type]){
 let value=computed(r,key);
 if(key==='name')value=elementName(kind,r);
 if(key==='display_id')return esc(String(value).padStart(2,'0'));
 if(key==='updated_by'||key==='created_by')value=auditPerson(value);
 if(type==='publish_status')return `<span class="tag ${value==='已发布'?'tag-green':'tag-gray'}">${esc(value)}</span>`;
 if(type==='enabled'){
  const locked=section==='elements'&&!!elementForms[kind]&&r.publish_status==='未发布',on=!locked&&value!==false;
  return `<button type="button" class="capsule ${on?'on':''}" data-field-toggle="enabled" aria-label="切换启用状态" aria-pressed="${on}" ${locked?'disabled title="未发布记录不可启用"':''}><span class="capsule-dot"></span></button>`;
 }
 if(type==='caseFactors')value=r.factors.map(f=>name('factors',f.factor_id));
 else if(type==='caseValues')value=r.factors.map(f=>conditionValues(f).join('、'));
 else if(type==='images'){
  const images=normalizeImages(value||[]);
  return images.length?`<button type="button" class="prompt-scene-entry" data-action="view-images" data-id="${esc(r.id)}" aria-label="查看布置图片"><span class="prompt-scene-thumbs">${images.map(image=>`<span class="prompt-scene-thumb" title="${esc(image.name+' · '+image.role)}"><img src="${esc(validImageSource(image.src)?image.src:'')}" alt="${esc(image.role)}"></span>`).join('')}</span></button>`:'—';
 }
 else if(type==='values')return `<button type="button" class="action-link" style="border:0;background:none" data-action="edit-values" data-id="${esc(r.id)}">${r.values.length} 条取值说明</button>`;
 else if(type.endsWith('[]'))value=(value||[]).map(id=>name(type.slice(0,-2),id));
 else if(Object.hasOwn(labels,type))value=value?name(type,value):'';
 if(Array.isArray(value))return value.length?value.map(esc).join('<br>'):'—';
 if(key==='name'||key==='id'&&kind==='test-cases')return `<button type="button" class="action-link" style="border:0;background:none;padding:0" data-action="view" data-id="${esc(r.id)}">${esc(value)}</button>`;
 return esc(value)||'—';
}
const selectedCases=new Set();
let selectableCases=[];
let benchmarkCases=[];
function benchmarkCaseDisplay(row,field){
 if(field[0]==='id')return esc(row.id);
 if(field[2]==='enabled')return row.enabled!==false?'启用':'停用';
 const cell=document.createElement('div');cell.innerHTML=display(row,field);
 cell.querySelectorAll('button').forEach(button=>{const span=document.createElement('span');span.className=button.className;span.innerHTML=button.innerHTML;button.replaceWith(span);});
 return cell.innerHTML;
}
function syncBenchmarkTags(){
 const wrap=$('ec-benchmark-tags');if(!wrap)return;
 const checked=[...wrap.querySelectorAll('input[name="benchmark_tag_ids"]:checked')];
 wrap.querySelector('.ts-trigger').innerHTML=checked.map(input=>`<span class="ts-chip" style="max-width:100%"><span class="ts-chip-text">${esc(input.getAttribute('aria-label')||input.value)}</span><button type="button" class="ts-chip-close" data-benchmark-tag-remove="${esc(input.value)}" aria-label="移除 ${esc(input.getAttribute('aria-label'))}" style="border:0;background:none">×</button></span>`).join('')||'<span class="ts-placeholder">请选择标签</span>';
 wrap.querySelectorAll('input').forEach(input=>input.closest('.ts-row')?.classList.toggle('selected',input.checked));
 $('ec-benchmark-tags-value').value=checked.map(input=>input.value).join(',');
}
function renderBenchmarkTable(){
 const fields=fieldsFor('test-cases').filter(([key])=>!['created_by','created_at','updated_by','updated_at','publish_status'].includes(key));
 const table=$('ec-benchmark-table'),widths=[...fields.map(([key])=>caseColumnWidths[key]||160),140,76];
 table.style.width=widths.reduce((sum,width)=>sum+width,0)+'px';
 table.querySelector('colgroup').innerHTML=widths.map(width=>`<col style="width:${width}px">`).join('');
 table.querySelector('thead').innerHTML='<tr>'+fields.map(field=>`<th>${esc(field[1])}</th>`).join('')+'<th style="position:sticky;right:76px;background:#fafafa;z-index:2">分布类型</th><th style="position:sticky;right:0;background:#fafafa;z-index:2">操作</th></tr>';
 table.querySelector('tbody').innerHTML=benchmarkCases.map((row,index)=>'<tr>'+fields.map(field=>`<td style="white-space:normal;overflow-wrap:anywhere">${benchmarkCaseDisplay(row,field)}</td>`).join('')+`<td style="position:sticky;right:76px;background:#fff"><div class="form-group" style="margin:0"><select class="has-value" data-case-distribution="${index}" aria-label="${esc(row.id)} 分布类型"><option>ID</option><option>OOD</option></select></div></td><td style="position:sticky;right:0;background:#fff"><button type="button" class="action-link danger" data-case-remove-row="${index}" aria-label="移除 ${esc(row.id)}" style="border:0;background:none;padding:0">移除</button></td></tr>`).join('')||`<tr><td colspan="${fields.length+2}" class="muted" style="padding:32px">暂无用例</td></tr>`;
 table.querySelectorAll('[data-case-distribution]').forEach(select=>select.value=benchmarkCases[Number(select.dataset.caseDistribution)]?.distribution_type||'ID');
 $('ec-benchmark-count').textContent=`共 ${benchmarkCases.length} 条已发布用例`;
 $('ec-benchmark-cases').value=JSON.stringify(benchmarkCases);
 $('ec-benchmark-form').querySelector('[type="submit"]').disabled=!benchmarkCases.length;
}
function selectedBenchmarkCases(){
 return clone(db['test-cases'].filter(row=>selectedCases.has(row.id)&&row.publish_status==='已发布')).map(row=>({...row,case_stage:computed(row,'case_stage'),distribution_type:'ID',case_labels:{case_stage:name('stages',computed(row,'case_stage')),story_id:name('stories',row.story_id),skill_ids:(row.skill_ids||[]).map(id=>name('skills',id)).join('、'),factor_ids:(row.factors||[]).map(factor=>name('factors',factor.factor_id)).join('、')}}));
}
function closeBenchmarkMenu(){
 $('ec-benchmark-actions')?.classList.remove('open');
 $('ec-benchmark-menu-trigger')?.setAttribute('aria-expanded','false');
}
function openBenchmark(){
 closeBenchmarkMenu();benchmarkCases=selectedBenchmarkCases();
 if(!benchmarkCases.length)return toast('所选用例均未发布，请选择已发布用例');
 try{sessionStorage.setItem('quanta.benchmark-case-selection',JSON.stringify(benchmarkCases));location.href='/model/eval/benchmarks?open=create&source=test-cases';}
 catch(error){toast('无法暂存所选用例，请检查浏览器存储空间');}
}
let benchmarkAdding=false,benchmarkOptionsRequest=null;
async function loadDraftBenchmarks(){
 benchmarkOptionsRequest?.abort();const controller=new AbortController();benchmarkOptionsRequest=controller;
 const select=$('ec-benchmark-target');select.disabled=true;select.classList.remove('has-value');select.innerHTML='<option value="">加载中…</option>';
 $('ec-benchmark-add-submit').disabled=true;$('ec-benchmark-add-error').textContent='';$('ec-benchmark-add-retry').hidden=true;
 try{
  const response=await fetch('/model/eval/benchmarks/drafts',{signal:controller.signal,cache:'no-store'});
  if(!response.ok)throw new Error('评测集加载失败，请重试');
  const data=await response.json(),drafts=data.benchmarks.filter(row=>row.publish_status==='未发布');
  select.innerHTML=`<option value="">${drafts.length?'请选择评测集':'暂无未发布的评测集'}</option>`+drafts.map(row=>`<option value="${esc(row.id)}">${esc(row.name)}</option>`).join('');select.disabled=!drafts.length;
 }catch(error){if(error.name==='AbortError')return;select.innerHTML='<option value="">加载失败</option>';$('ec-benchmark-add-error').textContent='评测集加载失败，请重试';$('ec-benchmark-add-retry').hidden=false;}
}
function openAddToBenchmark(){
 closeBenchmarkMenu();benchmarkCases=selectedBenchmarkCases();
 if(!benchmarkCases.length)return toast('所选用例均未发布，请选择已发布用例');
 const skipped=selectedCases.size-benchmarkCases.length;
 $('ec-benchmark-add-count').textContent=`共计 ${benchmarkCases.length} 条用例${skipped?`（已跳过 ${skipped} 条未发布用例）`:''}`;
 show('ec-benchmark-add-dialog');loadDraftBenchmarks();
}
function closeAddToBenchmark(){
 if(benchmarkAdding)return;
 benchmarkOptionsRequest?.abort();close('ec-benchmark-add-dialog');$('ec-benchmark-menu-trigger').focus();
}
async function addToBenchmark(event){
 event.preventDefault();if(benchmarkAdding||!$('ec-benchmark-target').value)return;
 benchmarkAdding=true;
 const controls=['ec-benchmark-add-submit','ec-benchmark-add-cancel','ec-benchmark-add-close','ec-benchmark-target'];
 controls.forEach(id=>$(id).disabled=true);$('ec-benchmark-add-submit').textContent='添加中…';$('ec-benchmark-add-error').textContent='';$('ec-benchmark-add-retry').hidden=true;
 let added=false;
 try{
  const response=await fetch('/model/eval/benchmarks/'+encodeURIComponent($('ec-benchmark-target').value)+'/cases',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({test_cases:benchmarkCases})});
  const data=await response.json();if(!response.ok)throw new Error(data.message||'添加失败，请重试');
  added=true;toast(`已添加 ${data.added} 条用例${data.skipped?`，跳过 ${data.skipped} 条重复用例`:''}`);
 }catch(error){$('ec-benchmark-add-error').textContent=error.message||'添加失败，请重试';$('ec-benchmark-add-retry').hidden=false;}
 finally{benchmarkAdding=false;controls.forEach(id=>$(id).disabled=false);$('ec-benchmark-add-submit').textContent='确认添加';}
 if(added)closeAddToBenchmark();
}
function closeSelectionMenu(){
 if(!$('ec-selection-menu'))return;
 $('ec-selection-menu').style.display='none';
 $('ec-selection-trigger')?.setAttribute('aria-expanded','false');
}
function syncCaseSelection(){
 for(const id of selectedCases)if(!db['test-cases'].some(r=>r.id===id))selectedCases.delete(id);
 const boxes=[...document.querySelectorAll('[data-select-case]')],checked=boxes.filter(x=>x.checked).length,all=$('ec-select-page');
 all.checked=boxes.length>0&&checked===boxes.length;all.indeterminate=checked>0&&checked<boxes.length;all.disabled=!boxes.length;
 $('ec-selected-count').hidden=$('ec-clear-selection').hidden=!selectedCases.size;
 $('ec-selected-count').textContent=`已选择 ${selectedCases.size} 条`;
 $('ec-create-benchmark').disabled=!selectedCases.size;
 $('ec-benchmark-menu-trigger').disabled=!selectedCases.size;
 if(!selectedCases.size)closeBenchmarkMenu();
 $('ec-selection-trigger').disabled=!boxes.length;
}
if(kind==='test-cases'){
 $('ec-thead').addEventListener('click',e=>{
  const trigger=e.target.closest('#ec-selection-trigger');if(!trigger)return;
  const menu=$('ec-selection-menu'),open=trigger.getAttribute('aria-expanded')==='true';closeSelectionMenu();
  if(!open){const rect=trigger.getBoundingClientRect();menu.style.display='block';Object.assign(menu.style,{left:Math.max(8,Math.min(rect.left,innerWidth-menu.offsetWidth-8))+'px',top:(rect.bottom+4)+'px'});trigger.setAttribute('aria-expanded','true');menu.querySelector('button').focus();}
 });
 $('ec-selection-menu').addEventListener('click',e=>{
  const scope=e.target.closest('[data-select-scope]')?.dataset.selectScope;if(!scope)return;
  const ids=scope==='all'?selectableCases:[...document.querySelectorAll('[data-select-case]')].map(x=>x.dataset.selectCase);
  selectedCases.clear();ids.forEach(id=>selectedCases.add(id));closeSelectionMenu();render();$('ec-selection-trigger').focus();
 });
 document.addEventListener('click',e=>{if(!e.target.closest('#ec-selection-trigger,#ec-selection-menu'))closeSelectionMenu();});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){const wasOpen=$('ec-selection-trigger')?.getAttribute('aria-expanded')==='true';closeSelectionMenu();if(wasOpen)$('ec-selection-trigger').focus();}});
 root.addEventListener('resize',closeSelectionMenu);
 document.addEventListener('scroll',closeSelectionMenu,true);
 $('ec-tbody').addEventListener('change',e=>{if(e.target.hasAttribute('data-select-case')){const id=e.target.dataset.selectCase;if(e.target.checked)selectedCases.add(id);else selectedCases.delete(id);syncCaseSelection();}});
 $('ec-thead').addEventListener('change',e=>{if(e.target.id==='ec-select-page'){document.querySelectorAll('[data-select-case]').forEach(x=>{x.checked=e.target.checked;if(x.checked)selectedCases.add(x.dataset.selectCase);else selectedCases.delete(x.dataset.selectCase);});syncCaseSelection();}});
 $('ec-clear-selection').onclick=()=>{selectedCases.clear();render();};
 $('ec-create-benchmark').onclick=openBenchmark;
 $('ec-benchmark-menu-create').onclick=openBenchmark;
 $('ec-benchmark-menu-add').onclick=openAddToBenchmark;
 $('ec-benchmark-menu-trigger').onclick=()=>{const open=$('ec-benchmark-actions').classList.toggle('open');$('ec-benchmark-menu-trigger').setAttribute('aria-expanded',String(open));if(open)$('ec-benchmark-menu-create').focus();};
 document.addEventListener('click',e=>{if(!e.target.closest('#ec-benchmark-actions'))closeBenchmarkMenu();});
 $('ec-benchmark-menu').addEventListener('keydown',e=>{const buttons=[...$('ec-benchmark-menu').querySelectorAll('button')];if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();buttons[(buttons.indexOf(document.activeElement)+(e.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length].focus();}if(e.key==='Escape'){closeBenchmarkMenu();$('ec-benchmark-menu-trigger').focus();}});
 $('ec-benchmark-add-close').onclick=$('ec-benchmark-add-cancel').onclick=closeAddToBenchmark;
 $('ec-benchmark-add-retry').onclick=loadDraftBenchmarks;
 $('ec-benchmark-target').onchange=()=>{$('ec-benchmark-target').classList.toggle('has-value',!!$('ec-benchmark-target').value);$('ec-benchmark-add-submit').disabled=!$('ec-benchmark-target').value;};
 $('ec-benchmark-add-form').onsubmit=addToBenchmark;
}
function syncScenarioFrozenColumns(){
 if(section!=='scenario')return;
 const table=$('ec-table'),headers=[...$('ec-thead').rows[0].cells].slice(0,5);
 const preferred=scenarioSchema.slice(0,5).map(([key])=>scenarioMinWidths[key]);
 // Leave room for scrolling columns even when the viewport is narrower than the frozen block.
 const available=Math.min(table.parentElement.clientWidth*.82,preferred.reduce((sum,width)=>sum+width,0));
 const valueWidth=Math.min(preferred[4],available*.22);
 const scale=(available-valueWidth)/preferred.slice(0,4).reduce((sum,width)=>sum+width,0);
 const rows=[...table.rows].filter(row=>row.cells.length>=5);
 rows.forEach(row=>[...row.cells].slice(0,5).forEach((cell,index)=>{
  const width=Math.floor(index===4?valueWidth:preferred[index]*scale);
  Object.assign(cell.style,{width:width+'px',minWidth:width+'px',maxWidth:width+'px',boxSizing:'border-box',position:'sticky',zIndex:cell.tagName==='TH'?'4':'2',background:cell.tagName==='TH'?'#fafafa':'#fff'});
  if(!cell.querySelector('[data-frozen-content]')){
   const content=document.createElement('div');content.dataset.frozenContent='';content.title=cell.textContent.trim();
   while(cell.firstChild)content.appendChild(cell.firstChild);
   cell.appendChild(content);
  }
  Object.assign(cell.firstElementChild.style,{width:Math.max(0,width-32)+'px',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'});
  if(index===4)cell.style.boxShadow='inset -1px 0 #e8e8e8';
 }));
 let left=0;
 headers.forEach((header,index)=>{rows.forEach(row=>{row.cells[index].style.left=left+'px';});left+=header.getBoundingClientRect().width;});
}
function syncElementFrozenColumns(){
 if(section!=='elements'||!elementForms[kind])return;
 const table=$('ec-table'),rows=[...table.rows].filter(row=>row.cells.length>=2),headers=[...$('ec-thead').rows[0].cells].slice(0,2);
 rows.forEach(row=>[...row.cells].slice(0,2).forEach((cell,index)=>{
  const header=cell.tagName==='TH';
  Object.assign(cell.style,{position:'sticky',zIndex:header?4:2,background:header?'#fafafa':'#fff',boxSizing:'border-box'});
  if(index===1)cell.style.boxShadow='inset -1px 0 #e8e8e8';
 }));
 let left=0;
 headers.forEach((header,index)=>{rows.forEach(row=>{row.cells[index].style.left=left+'px';});left+=header.getBoundingClientRect().width;});
}
function render(){
 closeSelectionMenu();
 syncCaseFilterSingles();
 refreshElementFilters();
 syncDataOwnershipFilter();
 const filters={query:$('ec-search')?.value,publishStatus:$('ec-status')?.value,enabled:$('ec-enabled')?.value,project:$('ec-project')?.value,dataOwner:$('ec-data-owner')?.value};
 for(const wrap of document.querySelectorAll('[data-filter-kind]'))filters[wrap.dataset.filterKind]=[...wrap.querySelectorAll('input:checked')].map(x=>x.value);
 for(const select of document.querySelectorAll('[data-filter-single]'))filters[select.dataset.filterSingle]=select.value?[select.value]:[];
 const filtered=filterRecords(db,kind,section,filters),rows=section==='scenario'?groupScenarios(filtered,'Stage'):filtered;
 if(kind==='test-cases')selectableCases=rows.map(r=>r.id);
 if(section==='elements'&&kind!=='test-cases')for(const target of ['stages','stories','skills','factors'])$('ec-total-'+target).textContent=db[target].length;
 const fields=fieldsFor(kind,section),pages=Math.max(1,Math.ceil(rows.length/10));page=Math.min(page,pages);
 if(section==='scenario')Object.assign($('ec-table').style,{tableLayout:'auto',width:'max-content',minWidth:'100%'});
 if(kind==='test-cases'||kind==='factors'){
  const widths=[...(kind==='test-cases'?[72]:[]),...fields.map(([key])=>(kind==='factors'?factorColumnWidths:caseColumnWidths)[key]||160),180];
  $('ec-columns').innerHTML=widths.map(width=>`<col style="width:${width}px">`).join('');
  Object.assign($('ec-table').style,{tableLayout:'fixed',width:widths.reduce((sum,width)=>sum+width,0)+'px',minWidth:'100%'});
 }
 const cellStyle=(f,header=false)=>section==='scenario'?`min-width:${scenarioMinWidths[f[0]]||120}px;white-space:nowrap`:kind==='factors'&&header?'white-space:nowrap':['test-cases','factors'].includes(kind)?'white-space:pre-wrap;overflow-wrap:break-word':'max-width:360px;white-space:pre-wrap;min-width:120px;overflow-wrap:anywhere';
 const caseSticky=(left,header=false)=>kind==='test-cases'?`;position:sticky;left:${left}px;z-index:${header?4:2};background:${header?'#fafafa':'#fff'};`:'';
 $('ec-thead').innerHTML='<tr>'+(kind==='test-cases'?`<th style="${caseSticky(0,true)}"><div style="display:flex;align-items:center;gap:4px"><input type="checkbox" id="ec-select-page" aria-label="选择当前页全部用例"><button type="button" id="ec-selection-trigger" class="action-link" style="border:0;background:none;padding:0;width:20px;height:24px" aria-label="选择范围" title="选择范围" aria-expanded="false" aria-controls="ec-selection-menu">&#9662;</button></div></th>`:'')+fields.map((f,index)=>`<th style="${cellStyle(f,true)}${kind==='test-cases'&&index===0?caseSticky(72,true):''}">${esc(f[1])}</th>`).join('')+'<th>操作</th></tr>';
 const actions=[...(kind==='test-cases'||section==='scenario'||section==='elements'&&elementForms[kind]?[]:['view']),'edit',...(section==='elements'&&['stages','stories','skills'].includes(kind)?['publish']:[]),'delete'];
 $('ec-tbody').innerHTML=rows.slice((page-1)*10,page*10).map(r=>{
  return `<tr data-collection="${r.scenario_record?'scenarios':kind}"${section==='scenario'?` data-scenario-key="${esc(r.row_key)}"`:''}>`+(kind==='test-cases'?`<td style="${caseSticky(0)}"><input type="checkbox" data-select-case="${esc(r.id)}" aria-label="选择用例 ${esc(r.id)}" ${selectedCases.has(r.id)?'checked':''}></td>`:'')+fields.map((f,index)=>`<td style="${cellStyle(f)}${kind==='test-cases'&&index===0?caseSticky(72):''}">${display(r,f)}</td>`).join('')+`<td class="actions-cell"><div style="display:flex;gap:12px">${actions.map(a=>{
  const blocked=a==='delete'&&(section==='scenario'?scenarioCaseCount(db,r)>0:publishedDeleteBlocked(kind,r))||a==='publish'&&!canPublish(kind,section,r);
  return `<button type="button" class="action-link ${blocked?'action-disabled':a==='delete'?'danger':''}" style="border:0;background:none;padding:0" data-action="${a}" data-id="${esc(r.id)}" ${blocked?`disabled title="${a==='delete'?(section==='scenario'?'该场景已有评测用例，无法删除':'已发布记录不可删除'):'已发布'}"`:''}>${{view:'详情',edit:'编辑',copy:'复制',publish:'发布',delete:'删除'}[a]}</button>`;
 }).join('')}</div></td></tr>`;}).join('')||`<tr><td colspan="${fields.length+(kind==='test-cases'?2:1)}" style="text-align:center;padding:64px">暂无匹配记录</td></tr>`;
 if(kind==='test-cases')syncCaseSelection();
 syncScenarioFrozenColumns();
 syncElementFrozenColumns();
 $('ec-count').textContent=`共 ${rows.length} 条`;$('ec-page-label').textContent=`第 ${page} / ${pages} 页`;$('ec-prev').disabled=page===1;$('ec-next').disabled=page===pages;
}
function updateFilterSummary(wrap){
 const checked=[...wrap.querySelectorAll('input:checked')],trigger=wrap.querySelector('.ts-trigger');
 const title=checked.map(x=>x.parentElement.textContent.trim()).join('、');
 trigger.innerHTML=checked.length?'<span class="skill-filter-values">'+checked.map(input=>`<span class="ts-chip"><span class="ts-chip-text" title="${esc(input.parentElement.textContent.trim())}">${esc(input.parentElement.textContent.trim())}</span></span>`).join('')+'</span>':`<span class="ts-placeholder">全部 ${labels[wrap.dataset.filterKind]}</span>`;
 trigger.title=title;
 wrap.querySelectorAll('.ts-row').forEach(row=>row.classList.toggle('selected',row.querySelector('input').checked));
}
function refreshElementFilters(){
 for(const wrap of document.querySelectorAll('[data-filter-kind]')){
  const selected=[...wrap.querySelectorAll('input:checked')].map(x=>x.value),target=wrap.dataset.filterKind;
  wrap.querySelector('.ts-panel').innerHTML=db[target].map(r=>`<label class="ts-row"><input type="checkbox" value="${esc(r.id)}" ${selected.includes(r.id)?'checked':''} style="width:14px;height:14px;min-width:14px;padding:0;margin:0 8px 0 0;flex-shrink:0">${esc(elementName(target,r))}</label>`).join('');
  updateFilterSummary(wrap);
 }
}
function syncCaseFilterSingles(){
 for(const select of document.querySelectorAll('[data-filter-single]')){
  const key=select.dataset.filterSingle, rows=key==='stages'?db.stages:key==='stories'?db.stories:db.factors, value=select.value;
  select.innerHTML='<option value="">全部 '+esc(labels[key])+'</option>'+rows.filter(row=>row.enabled!==false).map(row=>`<option value="${esc(row.id)}" ${row.id===value?'selected':''}>${esc(elementName(key,row))}</option>`).join('');
  select.classList.toggle('has-value',!!value);
 }
}
function options(rows,selected='',empty='请选择'){return `<option value="">${empty}</option>`+rows.map(x=>`<option value="${esc(x.id)}" ${x.id===selected?'selected':''}>${esc(x.name)}${x.enabled===false?'（未启用）':''}</option>`).join('');}
function groupedCaseOptions(groups,selected,allowed=null){
 return '<option value="">请选择</option>'+[['scene','场景库选项'],['other','其他选项']].map(([key,label])=>`<optgroup label="${label}">${groups[key].filter(row=>!allowed||allowed.has(row.id)).map(row=>`<option value="${esc(row.id)}" ${row.id===selected?'selected':''}>${esc(row.name)}</option>`).join('')}</optgroup>`).join('');
}
// All four case pickers share the same trigger, group rows and selection display.
function casePickerPanel(groups,selected,multiple,key){
 return [['scene','场景库选项'],['other','其他选项']].filter(([group])=>groups[group].length).map(([group,label])=>`<div class="case-picker-group" role="group" aria-label="${label}"><div class="case-picker-group-title">${label}</div>${groups[group].map(row=>multiple?`<label class="ts-row${selected.includes(row.id)?' selected':''}" style="white-space:normal;display:flex;align-items:center;gap:8px"><input type="checkbox" name="${esc(key)}" class="${key==='factor_values'?'ec-factor-value':''}" value="${esc(row.id)}" ${selected.includes(row.id)?'checked':''} ${readonly?'disabled':''} style="width:14px;height:14px;min-width:14px;padding:0;margin:0">${esc(row.name)}</label>`:`<button type="button" class="ts-row case-single-option${selected.includes(row.id)?' selected':''}" data-case-single="${esc(row.id)}" aria-pressed="${selected.includes(row.id)}" ${readonly?'disabled':''}>${esc(row.name)}</button>`).join('')}</div>`).join('')||'<div class="case-picker-empty" role="status">暂无选项</div>';
}
function syncCasePicker(wrap){
 const selected=[...wrap.querySelectorAll('.ts-panel input:checked')],single=wrap.querySelector('.ts-panel [data-case-single][aria-pressed="true"]');
 if(single){const value=single.dataset.caseSingle,text=single.textContent.trim();wrap.querySelector('.ts-trigger').innerHTML=`<span class="ts-single-value" title="${esc(text)}">${esc(text)}</span>${readonly?'':`<button type="button" class="ts-single-remove" data-case-remove="${esc(value)}" aria-label="移除 ${esc(text)}">×</button>`}`;}
 else {
  const items=selected.map(input=>({value:input.value,text:input.parentElement.textContent.trim()}));
  wrap.querySelector('.ts-trigger').innerHTML=items.map(({value,text})=>`<span class="ts-chip" style="max-width:100%"><span class="ts-chip-text" title="${esc(text)}">${esc(text)}</span>${readonly?'':`<button type="button" class="ts-chip-close" data-case-remove="${esc(value)}" aria-label="移除 ${esc(text)}" style="border:0;background:none">×</button>`}</span>`).join('')||'<span class="ts-placeholder">请选择</span>';
 }
 wrap.querySelectorAll('.ts-row').forEach(row=>{const input=row.querySelector('input');if(input)row.classList.toggle('selected',input.checked);});
}
function caseSinglePicker(select,label){
 return `<div class="ts-wrap" data-case-picker>${select}<div class="ts-trigger" role="button" tabindex="0" aria-label="${label}" aria-expanded="false"><span class="ts-placeholder">请选择</span></div><div class="ts-panel" style="width:100%;box-sizing:border-box"></div></div>`;
}
function editableChoiceOptions(values,selected,attribute){return values.map(value=>`<button type="button" class="ts-row${value===selected?' selected':''}" ${attribute}="${esc(value)}" style="width:100%;border:0;text-align:left;white-space:normal;overflow-wrap:anywhere">${esc(value)}</button>`).join('');}
function caseStoryFooter(){
 return `<div style="border-top:1px solid #f0f0f0;padding:8px 12px"><button class="action-link" type="button" id="ec-add-story" style="border:0;background:none;padding:0">+ 添加 Story</button><div id="ec-story-editor" hidden><div style="display:flex;align-items:center;gap:12px"><input type="text" id="ec-story-name" aria-label="新 Story 名称" placeholder="输入 Story 名称"><button type="button" class="action-link" id="ec-save-story" style="border:0;background:none;padding:0;white-space:nowrap">添加</button></div><span id="ec-story-error" role="alert" style="color:#cf1322;font-size:12px"></span></div></div>`;
}
function caseStoryCatalog(){return {...db,stories:[...pendingCaseStories,...db.stories]};}
function addCaseStory(){
 const value=$('ec-story-name').value.trim(),catalog=caseStoryCatalog();
 if(!value){$('ec-story-error').textContent='请输入 Story 名称';return;}
 if(catalog.stories.some(row=>row.name.trim()===value)){$('ec-story-error').textContent='该 Story 已存在，请选择已有选项';return;}
 const row=prepareElement(catalog,'stories',{name:value,project:$('ec-form').elements.project.value,tag_ids:[]});
 pendingCaseStories.push({...row,display_id:nextDisplayId(catalog.stories),publish_status:'已发布',enabled:true});
 const select=$('ec-form').elements.story_id;
 select.innerHTML=options(caseStoryCatalog().stories,row.id);
 refreshCaseOptions();
 const wrap=select.closest('.ts-wrap');wrap.classList.remove('open');wrap.querySelector('.ts-trigger').setAttribute('aria-expanded','false');wrap.querySelector('.ts-trigger').focus();
}
function editableChoice(attrs,value,label,prefix,values,attribute){
 return `<div class="ts-wrap" id="${prefix}-wrap"><input type="hidden" ${attrs} value="${esc(value)}"><button type="button" class="ts-trigger" id="${prefix}-trigger" aria-label="${label}" aria-expanded="false"><span>${esc(value)||'请选择'}</span></button><div class="ts-panel" style="width:100%;box-sizing:border-box"><div id="${prefix}-options">${editableChoiceOptions(values,value,attribute)}</div>${readonly?'':`<div style="border-top:1px solid #f0f0f0;padding:8px 12px"><button class="action-link" type="button" id="${prefix==='ec-category'?'ec-add-category':'ec-add-data-ownership'}" style="border:0;background:none;padding:0">+ 添加${label}</button><div id="${prefix}-editor" hidden><div style="display:flex;align-items:center;gap:12px"><input type="text" id="${prefix}-name" aria-label="新${label}名称" placeholder="输入${label}名称" maxlength="50"><button type="button" class="action-link" id="${prefix==='ec-category'?'ec-save-category':'ec-save-data-ownership'}" style="border:0;background:none;padding:0;white-space:nowrap">添加</button></div><span id="${prefix}-error" role="alert" style="color:#cf1322;font-size:12px"></span></div></div>`}</div></div>`;
}
function tagChips(values){
 return values.map(id=>{
  const path=catalogTags.find(tag=>tag.id===id)?.name||id;
  return `<span class="ts-chip" style="max-width:100%"><span class="ts-chip-text" style="white-space:normal;overflow-wrap:anywhere" title="${esc(path)}">${esc(path)}</span>${readonly?'':`<button type="button" class="ts-chip-close" data-remove-tag="${esc(id)}" aria-label="移除 ${esc(path)}" style="border:0;background:none;flex-shrink:0">&times;</button>`}</span>`;
 }).join('')||'<span class="ts-placeholder">请选择</span>';
}
function tagTreeNodes(nodes,selected,path=[],inputName='tag_ids'){
 const hasSelection=node=>selected.includes(node.id)||(node.tags||node.sub_tags||[]).some(hasSelection);
 return nodes.map(node=>{
  const children=node.tags||node.sub_tags||[],names=[...path,node.name],fullPath=names.join(' / '),dimension=Array.isArray(node.tags);
  const descendants=tagTreeNodes(children,selected,names,inputName),expanded=children.some(hasSelection);
  const arrow=children.length?`<button type="button" class="ts-arrow${expanded?' expanded':''}" data-tag-expand aria-label="展开 ${esc(fullPath)}" aria-expanded="${expanded}" style="border:0;background:none;padding:0">&#9654;</button>`:'<span class="ts-arrow empty"></span>';
  const content=dimension?`<button type="button" data-tag-expand aria-expanded="${expanded}" style="border:0;background:none;padding:0;font:inherit;color:inherit;text-align:left;flex:1">${esc(node.name)}</button>`:`<label style="display:flex;align-items:center;gap:8px;flex:1;margin:0;font:inherit;color:inherit;cursor:pointer"><input type="checkbox" name="${esc(inputName)}" value="${esc(node.id)}" aria-label="${esc(fullPath)}" ${selected.includes(node.id)?'checked':''} style="width:14px;height:14px;min-width:14px;padding:0;margin:0">${esc(node.name)}</label>`;
  return `<div class="ts-node"><div class="ts-row${selected.includes(node.id)?' selected':''}" style="white-space:normal">${arrow}${content}</div>${children.length?`<div class="ts-children${expanded?' expanded':''}">${descendants}</div>`:''}</div>`;
 }).join('');
}
function syncTagSelection(wrap){
 const checked=[...wrap.querySelectorAll('input[name="tag_ids"]:checked')].map(input=>input.value);
 wrap.querySelector('.ts-trigger').innerHTML=tagChips(checked);
 wrap.querySelectorAll('input[name="tag_ids"]').forEach(input=>input.closest('.ts-row').classList.toggle('selected',input.checked));
}
function toggleTagNode(button){
 const node=button.closest('.ts-node'),children=node.querySelector(':scope > .ts-children'),expanded=!children.classList.contains('expanded');
 children.classList.toggle('expanded',expanded);
 node.querySelectorAll(':scope > .ts-row [data-tag-expand]').forEach(control=>control.setAttribute('aria-expanded',String(expanded)));
 node.querySelector(':scope > .ts-row .ts-arrow').classList.toggle('expanded',expanded);
}
function input([key,label,type,required],r,scope='',rows=3){
 const value=computed(r,key),id=scope+key,attrs=`name="${esc(key)}" id="${esc(id)}" ${required?'required':''}`;
 if(caseCreating&&['case_stage','story_id'].includes(key))return caseSinglePicker(`<select ${attrs.replace('required','')} hidden>${options(db[key==='case_stage'?'stages':'stories'],value)}</select>`,label);
 if(type==='images')return `<div id="ec-images-section">
  <div class="prompt-scene-guidance"><span class="prompt-scene-guidance-icon">i</span><span>可添加 1–3 张布置图片，并为每张图片选择初始状态、目标状态或关键物体位置。</span></div>
  <button type="button" class="prompt-scene-upload" id="ec-image-upload" style="width:100%" ${readonly?'hidden':''}><span class="prompt-scene-upload-icon">⇧</span><strong>点击或拖拽上传布置图片</strong><small>支持 JPG、PNG、WebP、GIF，单张不超过 1 MB，最多 3 张</small></button>
  <input type="file" id="ec-image-file" accept="image/png,image/jpeg,image/webp,image/gif" multiple hidden>
  <div class="prompt-scene-grid" id="ec-image-list" style="margin-top:16px"></div>
  <div class="prompt-scene-empty-state" id="ec-image-empty"><span>图</span><strong>暂无布置图片</strong><small>上传后可设置图片类型</small></div>
  <textarea name="attachments" id="attachments" hidden>${esc(JSON.stringify(normalizeImages(value||[])))}</textarea></div>`;
 if(type==='factorDefault')return `<select ${attrs}>${options(factorValueOptions(r.values||[]).map(value=>({id:value,name:value})),value)}</select>`;
 if(type==='scenarioValue')return `<select ${attrs}>${options(factorValueOptions(db.factors.find(f=>f.id===r.factor_id)?.values||[]).map(value=>({id:value,name:value})),value)}</select>`;
 if(type==='dataOwnership')return editableChoice(attrs,value,label,'ec-data-ownership',dataOwnershipOptions(),'data-ownership');
 if(type==='enabled')return `<button type="button" class="capsule ${value!==false?'on':''}" data-field-toggle="enabled" aria-pressed="${value!==false}" ${readonly?'disabled':''}><span class="capsule-dot"></span></button>`;
 if(type==='computed')return `<input type="text" ${attrs} value="${esc(Array.isArray(value)?value.join('、'):value)}" disabled>`;
 if(type==='category'&&kind==='skills'&&section==='elements')return editableChoice(attrs,value,label,'ec-category',skillCategories(db),'data-category');
 if(type==='catalogTags[]'){
  const values=Array.isArray(value)?value:[],unknown=values.filter(id=>!catalogTags.some(tag=>tag.id===id)).map(id=>({id,name:id}));
  return `<div class="ts-wrap" data-tag-select><div class="ts-trigger" id="${esc(id)}" tabindex="${readonly?'-1':'0'}" role="button" aria-label="${esc(label)}" aria-expanded="false" aria-disabled="${readonly}">${tagChips(values)}</div><div class="ts-panel" style="width:100%;box-sizing:border-box">${tagTreeNodes([...catalogTagTree,...unknown],values)}</div></div>`;
 }
 if(type==='userGroups[]'){
  const values=Array.isArray(value)?value:[];
  const choices=userGroups;
  const chipSelect=type==='userGroups[]';
  const selectedNames=values.map(groupId=>choices.find(group=>group.id===groupId)?.name||groupId);
  const selectedMarkup=chipSelect?selectedNames.map((groupName,index)=>`<span class="ts-chip" data-chip-value="${esc(values[index])}"><span class="ts-chip-text">${esc(groupName)}</span>${readonly?'':`<span class="ts-chip-close" data-remove-user-group="${esc(values[index])}" role="button" tabindex="0" aria-label="移除 ${esc(groupName)}">&times;</span>`}</span>`).join(''):esc(selectedNames.join('、'));
  return `<div class="ts-wrap"${chipSelect?' data-chip-select="user-groups"':''}><div class="ts-trigger" id="${esc(id)}" tabindex="0" role="button" aria-label="${esc(label)}" aria-expanded="false"><span class="${chipSelect?'ts-chip-list':'ts-placeholder'}" style="overflow-wrap:anywhere;max-width:100%">${selectedMarkup||'请选择'}</span></div><div class="ts-panel" style="width:100%;box-sizing:border-box">${choices.map(group=>`<label class="ts-row" style="white-space:normal"><input type="checkbox" name="${esc(key)}" value="${esc(group.id)}" ${values.includes(group.id)?'checked':''}> ${esc(group.name)}</label>`).join('')}</div></div>`;
 }
 if(type.endsWith('[]')){
  const k=type.slice(0,-2),values=Array.isArray(value)?value:[];
  if(kind==='test-cases'&&key==='skill_ids')return `<div class="ts-wrap" data-case-picker><div class="ts-trigger" id="${esc(id)}" tabindex="0" role="button" aria-label="${esc(label)}" aria-expanded="false"><span class="ts-placeholder">请选择</span></div><div class="ts-panel" style="width:100%;box-sizing:border-box">${casePickerPanel({scene:[],other:db.skills.map(row=>({...row,name:elementName('skills',row)}))},values,true,key)}</div></div>`;
  return `<div class="ts-wrap"><div class="ts-trigger" id="${esc(id)}" tabindex="0" role="button" aria-label="${esc(label)}" aria-expanded="false"><span class="ts-placeholder" style="overflow-wrap:anywhere;max-width:100%">${esc(values.length?values.map(v=>name(k,v)).join('、'):'请选择')}</span></div><div class="ts-panel" style="width:100%;box-sizing:border-box">${db[k].filter(x=>!(key==='prerequisite_ids'&&x.id===r.id)&&(!batchCreating||x.enabled!==false)).map(x=>`<label class="ts-row" style="white-space:normal"><input type="checkbox" name="${esc(key)}" value="${esc(x.id)}" ${values.includes(x.id)?'checked':''}> ${esc(batchCreating?elementName(k,x):x.name)}</label>`).join('')}</div></div>`;
 }
 if(Object.hasOwn(labels,type)){let rows=db[type];if(kind==='test-cases'&&key==='story_id')rows=db.stories;if(key==='parent_id')rows=rows.filter(x=>x.id!==r.id);return `<select ${attrs}>${options(rows,value)}</select>`;}
 if(['publish_status','priority','category','visibility','project'].includes(type)){const vals={project:projects,publish_status:['已发布','未发布'],visibility:['公开','受限'],priority:['P0','P1','P2','P3'],category:['辨别类','动作类']}[type];return `<select ${attrs}>${vals.map(v=>`<option ${v===value?'selected':''}>${esc(v)}</option>`).join('')}</select>`;}
 if(type==='textarea'||type==='lines')return `<textarea ${attrs} rows="${rows}"${rows===1?' style="min-height:36px;height:36px;resize:vertical"':''}>${esc(Array.isArray(value)?value.join('\n'):value)}</textarea>`;
 return `<input type="text" ${attrs} value="${esc(value)}">`;
}
function field(schema,r,scope=''){const visibilityClass=schema[0]==='visible_group_ids'?' visibility-groups-field':'';const visibilityAttr=schema[0]==='visible_group_ids'?` data-visibility-groups="true"${r.visibility==='受限'?'':' style="display:none"'}`:'';return `<div class="form-group${visibilityClass}"${visibilityAttr}><label for="${schema[2]==='images'?'ec-image-upload':scope+schema[0]}">${esc(schema[1])}${schema[2]==='images'?' <span id="ec-image-total"></span>':''}${schema[3]?' <span style="color:#cf1322">*</span>':''}${batchCreating&&schema[2].endsWith('[]')?` <span class="muted" style="margin-left:8px;font-size:12px;font-weight:400" id="ec-selected-${schema[0]}" aria-live="polite">已选择 0 项</span>`:''}</label>${input(schema,r,scope)}</div>`;}
function syncUserGroupChips(wrap){
 if(!wrap?.dataset.chipSelect)return;
 const checked=[...wrap.querySelectorAll('input[name="visible_group_ids"]:checked')];
 const trigger=wrap.querySelector('.ts-trigger');
 trigger.innerHTML=checked.map(input=>`<span class="ts-chip" data-chip-value="${esc(input.value)}"><span class="ts-chip-text">${esc(input.parentElement.textContent.trim())}</span>${readonly?'':`<span class="ts-chip-close" data-remove-user-group="${esc(input.value)}" role="button" tabindex="0" aria-label="移除 ${esc(input.parentElement.textContent.trim())}">&times;</span>`}</span>`).join('')||'<span class="ts-placeholder">请选择</span>';
}
function factorValueOptionGroups(values,groups=null){
 const scene=new Set(groups?.scene||[]),sceneValues=values.filter(value=>scene.has(value)),otherValues=values.filter(value=>!scene.has(value));
 return [[sceneValues,'场景库选项'],[otherValues,'其他选项']];
}
function conditionValueInput(def,selected=[],groups=null){
 const values=factorValueOptions(def?.values||[]),chosen=selected.filter(v=>values.includes(v));
 if(kind==='test-cases'){
  const grouped={scene:values.filter(v=>groups?.scene.includes(v)).map(id=>({id,name:id})),other:values.filter(v=>!groups?.scene.includes(v)).map(id=>({id,name:id}))};
  return `<div class="ts-wrap" data-case-picker><div class="ts-trigger" role="button" tabindex="0" aria-label="Factor 取值" aria-expanded="false"><span class="ts-placeholder">请选择</span></div><div class="ts-panel" style="width:100%;box-sizing:border-box">${casePickerPanel(grouped,chosen,true,'factor_values')}</div></div>`;
 }
 return `<div class="ts-wrap"><button type="button" class="ts-trigger" aria-label="Factor 取值" aria-expanded="false" ${readonly||!def?'disabled':''}><span class="ts-placeholder">${esc(chosen.join('、')||(def&&!values.length?'暂无可选取值':'请选择'))}</span></button><div class="ts-panel" style="width:100%;box-sizing:border-box">${values.length?values.map(value=>`<label class="ts-row" style="white-space:normal"><input type="checkbox" class="ec-factor-value" value="${esc(value)}" ${chosen.includes(value)?'checked':''} ${readonly?'disabled':''}> ${esc(value)}</label>`).join(''):'<div class="muted" style="padding:8px 12px">暂无选项</div>'}</div></div>`;
}
function conditionRow(f={}){
 const def=db.factors.find(x=>x.id===f.factor_id),remove='<button class="action-link" style="border:0;background:none;padding:0;flex-shrink:0" type="button" data-remove-condition>移除</button>';
 const select=`<select class="ec-factor-id" aria-label="Factor" style="min-width:0" ${kind==='test-cases'?'hidden':''}>${options(db.factors.filter(row=>!batchCreating||row.enabled!==false),f.factor_id)}</select>`;
 const factor=kind==='test-cases'?caseSinglePicker(select,'Factor'):select;
 return `<tr><td>${factor}</td><td class="ec-factor-values">${conditionValueInput(def,conditionValues(f))}</td><td>${remove}</td></tr>`;
}
function valueRow(v={},index=null){
 const scope='value-'+(++valueRowCounter)+'-',existing=Number.isInteger(index),published=currentValueOwnerPublished;
 const canRemove=!readonly&&(!published||!existing);
 return `<tr${existing?` data-value-index="${index}"`:''}>${valueSchema.map(f=>`<td style="min-width:180px;vertical-align:top"><div class="form-group" style="margin:0">${input(f,v,scope,1)}</div></td>`).join('')}${canRemove?'<td class="actions-cell"><button class="action-link danger" style="border:0;background:none;padding:0" type="button" data-remove-value>移除</button></td>':readonly?'':'<td class="actions-cell"></td>'}</tr>`;
}
function syncFactorDefault(){
 const select=$('ec-form').elements.default_value;
 if(kind!=='factors'||!select||!$('ec-values'))return;
 const selected=select.value,values=[...$('ec-values').querySelectorAll('[name="value"]')].map(input=>({value:input.value}));
 select.innerHTML=options(factorValueOptions(values).map(value=>({id:value,name:value})),selected);
 syncSelects();
}
function emptyRecord(){return {id:'',name:'',description:'',publish_status:'未发布',enabled:true,visibility:'公开',visible_group_ids:[],data_owner:'Eval-白盒',project:projects[0],tag_ids:[],owner:demoActor,skill_ids:[],factor_ids:[],factors:[],factor_option_ids:[],prerequisite_ids:[],attachments:[],values:[],tool_usage:[],action_descriptions:[],category:kind==='skills'?'动作类':'',dimension:'',priority:'P1'};}
function detailFields(row,fields){
 return '<dl style="display:grid;grid-template-columns:110px minmax(0,1fr);gap:16px;font-size:13px;margin:0">'+fields.map(([key,label,type])=>{
  let value=row[key];
  if(Object.hasOwn(labels,type)){const entity=db[type].find(x=>x.id===value);value=entity?elementName(type,entity):value;}
  const content=key==='tag_ids'&&value?.length?`<div style="display:flex;flex-wrap:wrap;gap:4px">${tagChips(value)}</div>`:esc(key==='tag_ids'?'--':Array.isArray(value)?value.join('\n')||'--':value||'--');
  return `<dt class="muted">${esc(label)}</dt><dd style="margin:0;white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.8">${content}</dd>`;
 }).join('')+'</dl>';
}
function elementDetails(row){
 const fields=fieldsFor(kind,'elements','form');
 let html='';
 if(kind==='factors'){
  html='<h4>基本信息</h4>'+detailFields(row,fields.filter(f=>['category','dimension','level3'].includes(f[0])));
  html+='<h4 style="margin-top:24px">取值范围</h4><div class="muted" style="margin-bottom:12px">取值说明</div><div style="overflow-x:auto"><table class="ant-table" style="table-layout:fixed;width:100%;min-width:540px"><thead><tr>'+valueSchema.map(f=>`<th>${esc(f[1])}</th>`).join('')+'</tr></thead><tbody>';
  html+=(row.values||[]).map(value=>'<tr>'+valueSchema.map(([key])=>`<td style="white-space:pre-wrap;overflow-wrap:anywhere;vertical-align:top">${esc(value[key]||'--')}</td>`).join('')+'</tr>').join('')||'<tr><td colspan="3" class="muted">暂无取值说明</td></tr>';
  html+='</tbody></table></div><div style="margin-top:16px">'+detailFields(row,fields.filter(f=>['default_value','project','tag_ids'].includes(f[0])))+'</div>';
 }else html=detailFields(row,fields);
 return html+updateHistorySection(row);
}
function updateHistorySection(row){
 let html='<h4 style="margin-top:28px">更新记录</h4><div style="overflow-x:auto"><table class="ant-table" id="ec-update-history" style="table-layout:fixed;width:100%;min-width:640px"><colgroup><col style="width:180px"><col style="width:140px"><col></colgroup><thead><tr><th>更新时间</th><th>更新人</th><th>更新内容</th></tr></thead><tbody>';
 html+=(row.update_history||[]).map(entry=>`<tr><td style="vertical-align:top">${esc(entry.updated_at)}</td><td style="vertical-align:top">${esc(entry.updated_by)}</td><td style="white-space:pre-wrap;overflow-wrap:anywhere">${(entry.changes||[]).map(change=>`<div>${esc(change.label)}：${esc(change.before_text)} → ${esc(change.after_text)}</div>`).join('')}</td></tr>`).join('')||'<tr><td colspan="3" class="muted" style="text-align:center;padding:24px">暂无更新记录</td></tr>';
 return html+'</tbody></table></div>';
}
function open(mode,id,collection=kind,rowKey=null){
 pendingCaseStories=[];
 caseCreating=kind==='test-cases'&&['create','copy'].includes(mode);
 batchCreating=section==='scenario'&&mode==='create';scenarioEditing=section==='scenario'&&!batchCreating;editingScenarioKey=rowKey;
 const original=scenarioEditing?scenarioValueRows(db).find(x=>x.row_key===rowKey):db[collection].find(x=>x.id===id),r={...emptyRecord(),...(original?clone(original):{})};editing=['edit','edit-values'].includes(mode)?id:null;viewing=id;readonly=mode==='view';
 currentValueOwnerPublished=kind==='factors'&&r.publish_status==='已发布';
 if(mode==='copy'){r.id='';r.name+='（副本）';r.publish_status='未发布';r.enabled=true;}
 $('ec-dialog-title').textContent=(readonly?'查看':editing?'编辑':mode==='copy'?'复制':'新增')+(section==='scenario'?'场景':labels[kind]);$('ec-dialog-subtitle').textContent='';$('ec-error').textContent='';
 if(scenarioEditing&&readonly)$('ec-dialog-title').textContent='场景详情';
 if(section==='elements'&&elementForms[kind]&&readonly)$('ec-dialog-title').textContent=labels[kind]+' 详情';
 $('ec-batch-notice').style.display=batchCreating?'flex':'none';
 $('ec-dialog').classList.toggle('ec-case-readonly',kind==='test-cases'&&readonly);
 if(kind==='test-cases'&&readonly)$('ec-dialog-title').textContent='评测用例详情';
 if(batchCreating){$('ec-dialog-title').textContent='批量新增场景';$('ec-dialog-subtitle').textContent='各要素支持多选，会按照「Stage x Story x Skill x Factor x Factor取值」拆分成多条。系统会自动与已有场景去重，相同组合不会重复添加。';}
 const formFields=batchCreating?[projectField,...batchScenarioSchema]:fieldsFor(kind,section,kind==='test-cases'&&!editing&&!readonly?'create':'form');
 if(kind==='test-cases'&&readonly)formFields.push(caseSystemSchema.find(field=>field[0]==='publish_status'));
 const metadataStart=formFields.find(f=>!schemas[kind].includes(f));
 let html='';for(const f of formFields){
  if(kind==='test-cases'&&['prompt','case_stage','props','visibility'].includes(f[0]))html+=`<h4>${{prompt:'提示词',case_stage:'用例属性',props:'场景说明',visibility:'可见性配置'}[f[0]]}</h4>`;
  if(kind==='test-cases'&&f[0]==='publish_status')html+='<h4>记录信息</h4>';
  if(section==='elements'&&elementForms[kind]&&kind!=='factors'&&f===formFields[0])html+='<h4>基础信息</h4>';
  if(kind==='factors'&&f[0]==='category')html+='<h4>基础信息</h4>';
  if(kind==='factors'&&f[0]==='values')html+=editing?'<div class="muted" style="margin:24px 0 12px">取值范围</div>':'<h4>取值范围</h4>';
  if(kind!=='test-cases'&&!batchCreating&&!scenarioEditing&&!(section==='elements'&&elementForms[kind])&&f===metadataStart)html+='<h4>平台维护信息</h4>';
  if(f[2]==='caseValues')continue;
  if(f[2]==='caseFactors')html+=`<div class="form-group"><label>Factor 配置</label><table class="ant-table" style="table-layout:fixed"><thead><tr><th>Factor</th><th>Factor 取值</th><th style="width:72px">操作</th></tr></thead><tbody id="ec-factors">${r.factors.map(conditionRow).join('')}</tbody></table><button class="action-link" style="border:0;background:none;padding:0;margin-top:12px" type="button" id="ec-add-factor">添加 Factor</button></div>`;
  else if(f[2]==='values')html+=`<div class="form-group" id="ec-values-section"><label>取值说明</label><div style="overflow-x:auto"><table class="ant-table"><thead><tr>${valueSchema.map(x=>'<th>'+esc(x[1])+'</th>').join('')}${readonly?'':'<th>操作</th>'}</tr></thead><tbody id="ec-values">${r.values.map(valueRow).join('')}</tbody></table></div>${readonly?'':'<button class="action-link" style="border:0;background:none;padding:0;margin-top:12px" type="button" id="ec-add-value">添加取值说明</button>'}</div>`;
  else html+=field(f,r);
 }
 if(batchCreating){
  html+=`<div class="form-group"><label>Factor 配置 <span style="color:#cf1322">*</span></label><table class="ant-table" style="table-layout:fixed;width:100%"><thead><tr><th>Factor</th><th>Factor取值（多选）</th><th style="width:72px">操作</th></tr></thead><tbody id="ec-factors">${conditionRow()}</tbody></table><button class="action-link" style="border:0;background:none;padding:0;margin-top:12px" type="button" id="ec-add-factor">添加 Factor</button></div>`;
  html+='<div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px 16px;border-top:1px solid #f0f0f0;padding-top:16px;font-size:14px" aria-live="polite"><span>组合条数</span><span class="muted" id="ec-batch-formula" style="font-variant-numeric:tabular-nums"></span><span id="ec-batch-total" style="margin-left:auto;white-space:nowrap;font-variant-numeric:tabular-nums"></span></div>';
 }
 if((section==='elements'&&elementForms[kind]&&editing)||(kind==='test-cases'&&(editing||readonly)))html+=updateHistorySection(r);
 $('ec-fields').innerHTML=readonly?(scenarioEditing?detailFields(r,scenarioFormSchema):section==='elements'&&elementForms[kind]?elementDetails(r):html):html;$('ec-save').hidden=readonly;$('ec-save').disabled=false;$('ec-cancel').textContent=readonly?'关闭':'取消';
 if(batchCreating)refreshConditions();
 if((editing||readonly)&&$('ec-form').elements.namedItem('id'))$('ec-form').elements.namedItem('id').disabled=true;
 if(readonly)$('ec-fields').querySelectorAll('input,select,textarea,button').forEach(x=>x.disabled=true);
 if(currentValueOwnerPublished)$('ec-fields').querySelectorAll('#ec-values [data-value-index] [name="value"]').forEach(control=>{control.disabled=true;});
 if(scenarioEditing&&!readonly)for(const [key] of scenarioFormSchema)if(!scenarioEditableFields.some(f=>f[0]===key))$('ec-form').elements.namedItem(key).disabled=true;
 if(caseCreating)refreshCaseOptions();else if(kind==='test-cases')refreshConditionOptions(db.factors);
 if(kind==='test-cases')$('ec-fields').querySelectorAll('[data-case-picker]').forEach(syncCasePicker);
 syncSelects();renderImages();
 if(kind==='test-cases'&&readonly){
  $('ec-fields').querySelectorAll('input,select,textarea,button').forEach(control=>control.disabled=true);
  $('ec-fields').querySelectorAll('.ts-trigger').forEach(trigger=>{trigger.setAttribute('aria-disabled','true');trigger.tabIndex=-1;});
 }
 show('ec-dialog');if(mode==='edit-values')$('ec-values-section').scrollIntoView({block:'start'});
}
function syncSelects(){document.querySelectorAll('#ec-fields select').forEach(x=>x.classList.toggle('has-value',!!x.value));}
function categoryOptions(selected){return skillCategories(db).map(value=>`<button type="button" class="ts-row${value===selected?' selected':''}" data-category="${esc(value)}" style="width:100%;border:0;text-align:left;white-space:normal;overflow-wrap:anywhere">${esc(value)}</button>`).join('');}
function selectCategory(value){
 $('ec-form').elements.category.value=value;
 $('ec-category-trigger').textContent=value;
 $('ec-category-trigger').setAttribute('aria-expanded','false');
 $('ec-category-options').innerHTML=categoryOptions(value);
 $('ec-category-wrap').classList.remove('open');
}
function addCategory(){
 const value=$('ec-category-name').value.trim();
 if(!value){$('ec-category-error').textContent='请输入类别名称';return;}
 if(skillCategories(db).includes(value)){$('ec-category-error').textContent='该类别已存在';return;}
 const next=clone(db);next.skill_categories=[...(next.skill_categories||[]),value];
 if(persist(next)){selectCategory(value);$('ec-category-editor').hidden=true;$('ec-add-category').hidden=false;}
}
function dataOwnershipSelect(value){
 const select=$('ec-form').elements.data_owner;
 if(!select)return;
 select.value=value;
 $('ec-data-ownership-trigger').textContent=value;
 $('ec-data-ownership-trigger').setAttribute('aria-expanded','false');
 $('ec-data-ownership-options').innerHTML=editableChoiceOptions(dataOwnershipOptions(),value,'data-ownership');
 $('ec-data-ownership-wrap').classList.remove('open');
}
function syncDataOwnershipFilter(){
 const select=$('ec-data-owner');if(!select)return;
 const selected=select.value;
 select.innerHTML=options([...new Set([...dataOwnershipOptions(),...db['test-cases'].map(row=>row.data_owner).filter(Boolean)])].map(value=>({id:value,name:value})),selected,'全部数据归属');
}
function addDataOwnership(){
 const value=$('ec-data-ownership-name').value.trim();
 if(!value){$('ec-data-ownership-error').textContent='请输入数据归属名称';return;}
 if(dataOwnershipOptions().includes(value)){$('ec-data-ownership-error').textContent='该数据归属已存在';return;}
 const next=clone(db);next.data_ownership_options=[...dataOwnershipOptions(),value];
 if(persist(next)){dataOwnershipValues=[...next.data_ownership_options];dataOwnershipSelect(value);syncDataOwnershipFilter();$('ec-data-ownership-editor').hidden=true;$('ec-data-ownership-name').value='';$('ec-data-ownership-error').textContent='';$('ec-add-data-ownership').hidden=false;}
}
function syncBatchSelection(){
 const counts=batchScenarioSchema.map(([key])=>{
  const trigger=$(key),wrap=trigger.closest('.ts-wrap'),checked=[...wrap.querySelectorAll('input:checked')];
  $('ec-selected-'+key).textContent=`已选择 ${checked.length} 项`;
  trigger.innerHTML=checked.map(input=>`<span class="ts-chip" style="max-width:100%"><span class="ts-chip-text" style="white-space:normal;overflow-wrap:anywhere">${esc(input.parentElement.textContent.trim())}</span></span>`).join('')||'<span class="ts-placeholder">请选择</span>';
  wrap.querySelectorAll('.ts-row').forEach(row=>row.classList.toggle('selected',row.querySelector('input').checked));
  return checked.length;
 });
 for(const row of $('ec-factors').children){
  const wrap=row.querySelector('.ts-wrap'),checked=[...wrap.querySelectorAll('input:checked')];
  wrap.querySelector('.ts-trigger').innerHTML=checked.map(input=>`<span class="ts-chip" style="max-width:100%"><span class="ts-chip-text" style="white-space:normal;overflow-wrap:anywhere">${esc(input.value)}</span></span>`).join('')||'<span class="ts-placeholder">请选择</span>';
  wrap.querySelectorAll('.ts-row').forEach(option=>option.classList.toggle('selected',option.querySelector('input').checked));
 }
 const selections=collectBatchSelection(),valueCounts=selections.factors.map(f=>new Set(f.values).size);
 const factorsComplete=selections.factors.length&&selections.factors.every(f=>f.factor_id&&f.values.length);
 $('ec-batch-formula').textContent=counts.join(' × ')+' × '+(factorsComplete?(valueCounts.length>1?'('+valueCounts.join(' + ')+')':valueCounts[0]):0);
 $('ec-batch-total').textContent='共 '+batchScenarioCount(selections)+' 条';
}
function collectBatchSelection(){
 return {...Object.fromEntries([projectField,...batchScenarioSchema].map(f=>[f[0],readValue($('ec-fields'),f)])),factors:[...$('ec-factors').children].map(row=>({factor_id:row.querySelector('.ec-factor-id').value,values:[...row.querySelectorAll('.ec-factor-value:checked')].map(input=>input.value)}))};
}
function refreshCaseOptions(){
 const form=$('ec-form'),stage=form.elements.case_stage,story=form.elements.story_id;
 const selectedSkills=[...form.querySelectorAll('[name="skill_ids"]:checked')].map(x=>x.value);
 const stageValue=stage.value;stage.innerHTML=options(db.stages.filter(row=>row.enabled!==false),stageValue);
 const stageWrap=stage.closest('[data-case-picker]');
 const linkedStages=new Set(caseOptions(db,{}).stages.map(row=>row.id));
 stageWrap.querySelector('.ts-panel').innerHTML=casePickerPanel({scene:caseOptions(db,{}).stages,other:db.stages.filter(row=>row.enabled!==false&&!linkedStages.has(row.id))},[stage.value],false,'case_stage');syncCasePicker(stageWrap);
 let groups=caseOptionGroups(caseStoryCatalog(),{case_stage:stage.value});
 const storyValue=story.value;story.innerHTML=groupedCaseOptions(groups.stories,storyValue);story.disabled=false;
 const storyWrap=story.closest('.ts-wrap');
 storyWrap.querySelector('.ts-panel').innerHTML=casePickerPanel(groups.stories,[story.value],false,'story_id')+caseStoryFooter();
 storyWrap.querySelector('.ts-trigger').setAttribute('aria-disabled',String(story.disabled));syncCasePicker(storyWrap);
 groups=caseOptionGroups(db,{case_stage:stage.value,story_id:story.value});
 const skills=selectedSkills.filter(id=>db.skills.some(x=>x.id===id&&x.enabled!==false));
 const wrap=$('skill_ids').closest('.ts-wrap');
 wrap.setAttribute('data-case-picker','');
 const skillGroups=Object.fromEntries(Object.entries(groups.skills).map(([key,rows])=>[key,rows.map(row=>({...row,name:elementName('skills',row)}))]));
 wrap.querySelector('.ts-panel').innerHTML=casePickerPanel(skillGroups,skills,true,'skill_ids');syncCasePicker(wrap);
 groups=caseOptionGroups(db,{case_stage:stage.value,story_id:story.value,skill_ids:skills});
 refreshConditionOptions([...groups.factors.scene,...groups.factors.other],groups.factors);
 syncSelects();
}
function refreshConditionOptions(available,groups=null){
 const rows=[...$('ec-factors').children],selected=rows.map(row=>row.querySelector('.ec-factor-id').value).filter(Boolean);
 const form=$('ec-form'),selection={case_stage:form.elements.case_stage?.value||'',story_id:form.elements.story_id?.value||'',skill_ids:[...form.querySelectorAll('[name="skill_ids"]:checked')].map(input=>input.value)};
 for(const row of rows){
  const factor=row.querySelector('.ec-factor-id'),old=factor.value,chosen=[...row.querySelectorAll('.ec-factor-value:checked')].map(x=>x.value);
  const allowed=available.filter(f=>f.id===old||!selected.includes(f.id));
  factor.innerHTML=groups?groupedCaseOptions(groups,old,new Set(allowed.map(f=>f.id))):options(allowed,old);factor.disabled=readonly||!available.length;
  if(kind==='test-cases'){const wrap=factor.closest('.ts-wrap'),allowedIds=new Set(allowed.map(row=>row.id));wrap.querySelector('.ts-panel').innerHTML=casePickerPanel(Object.fromEntries(Object.entries(groups||{scene:[],other:available}).map(([key,rows])=>[key,rows.filter(row=>allowedIds.has(row.id))])),[factor.value],false,'factor_id');syncCasePicker(wrap);}
  const def=available.find(f=>f.id===factor.value);
  row.querySelector('.ec-factor-values').innerHTML=conditionValueInput(def,chosen, factorValueGroups(db,selection,factor.value));
  if(kind==='test-cases')syncCasePicker(row.querySelector('.ec-factor-values .ts-wrap'));
 }
 $('ec-add-factor').disabled=readonly||rows.some(row=>!row.querySelector('.ec-factor-id').value)||!available.some(f=>!selected.includes(f.id));
}
function refreshConditions(){if(batchCreating){refreshConditionOptions(db.factors.filter(f=>f.enabled!==false));syncBatchSelection();}else if(caseCreating)refreshCaseOptions();else if(kind==='test-cases'&&$('ec-factors'))refreshConditionOptions(db.factors);}
function readValue(container,[key,,type]){
 const els=[...container.querySelectorAll('[name]')].filter(x=>x.name===key);
 if(type==='images')return JSON.parse(els[0]?.value||'[]');
 if(type.endsWith('[]'))return els.filter(x=>x.checked).map(x=>x.value);
 const val=(els[0]?.value||'').trim();return type==='lines'?val.split('\n').map(x=>x.trim()).filter(Boolean):val;
}
function collect(){
 if(scenarioEditing){const original=scenarioValueRows(db).find(x=>x.row_key===editingScenarioKey);return {...original,row_key:editingScenarioKey,...Object.fromEntries(scenarioEditableFields.map(f=>[f[0],readValue($('ec-fields'),f)])),updated_by:demoActor,updated_at:new Date().toLocaleString('sv-SE')};}
 const original=db[kind].find(x=>x.id===editing),now=new Date().toLocaleString('sv-SE');let r={...emptyRecord(),...clone(original||{})};
 for(const f of fieldsFor(kind,section,kind==='test-cases'&&!editing?'create':'form'))if(!['computed','caseFactors','caseValues','values','enabled'].includes(f[2]))r[f[0]]=readValue($('ec-fields'),f);
 const enabledToggle=$('ec-fields').querySelector('[data-field-toggle="enabled"]');if(enabledToggle)r.enabled=enabledToggle.getAttribute('aria-pressed')==='true';
 r.id=editing||r.id;r.created_at=original?.created_at||now;r.updated_at=now;
 if(section==='elements'&&elementForms[kind])r=prepareElement(db,kind,r,original);
 if(kind==='test-cases'){
  r.updated_by='Joanna Qiao';
  r.name=original?.name||r.id;r.factors=[...$('ec-factors').children].map(row=>({factor_id:row.querySelector('.ec-factor-id').value,values:[...row.querySelectorAll('.ec-factor-value:checked')].map(x=>x.value)}));
  if(r.visibility==='公开')r.visible_group_ids=[];
 }
 if(kind==='factors')r.values=[...$('ec-values').children].map(row=>{
  const previous=original?.values[Number(row.dataset.valueIndex)]||{};
  const v=Object.fromEntries(valueSchema.map(f=>[f[0],readValue(row,f)]));
  if(original?.publish_status==='已发布'&&row.hasAttribute('data-value-index'))v.value=previous.value;
  return {...previous,...v,factor_id:previous.factor_id||r.id,linked_factor_ids:previous.linked_factor_ids?.length?previous.linked_factor_ids:[r.id]};
 });
 if(kind==='factors')r.value_range=factorValueOptions(r.values).join(' / ');
 return r;
}
function renderImages(){
 if(!$('ec-image-list'))return;
 const field=$('ec-form').elements.attachments,values=JSON.parse(field.value||'[]'),busy=field.dataset.uploading==='true',disabled=readonly||busy;
 $('ec-image-total').textContent=`（${values.length}/3）${busy?' · 正在读取…':''}`;
 $('ec-image-empty').style.display=values.length?'none':'flex';
 $('ec-image-upload').hidden=readonly||values.length>=3;
 $('ec-image-upload').disabled=$('ec-image-file').disabled=disabled;
 $('ec-save').disabled=busy;
 $('ec-image-list').innerHTML=values.map((image,i)=>`<article class="prompt-scene-card"><div class="prompt-scene-preview"><img src="${esc(validImageSource(image.src)?image.src:'')}" alt="${esc(image.name)}" style="object-fit:contain"></div><div class="prompt-scene-card-body"><div class="prompt-scene-name" title="${esc(image.name)}">${esc(image.name)}</div><select class="prompt-scene-role has-value" data-image-role="${i}" aria-label="第 ${i+1} 张图片类型" ${disabled?'disabled':''}>${imageRoles.map(role=>`<option ${role===image.role?'selected':''}>${role}</option>`).join('')}</select><div class="prompt-scene-card-actions">${readonly?'':`<button type="button" class="danger" data-remove-image="${i}" ${busy?'disabled':''}>删除</button>`}</div></div></article>`).join('');
}
async function addImages(files){
 const field=$('ec-form').elements.attachments,accepted=[...files];
 if(readonly||!field||field.dataset.uploading==='true'||!accepted.length)return;
 $('ec-image-file').value='';
 if(JSON.parse(field.value).length+accepted.length>3)return toast('布置图片最多 3 张，请减少选择或先删除已有图片');
 if(accepted.some(f=>!['image/png','image/jpeg','image/webp','image/gif'].includes(f.type)||f.size>1024*1024))return toast('请上传 PNG/JPEG/WebP/GIF 图片，每张不超过 1 MB');
 field.dataset.uploading='true';renderImages();
 try{
  const images=await Promise.all(accepted.map(file=>new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve({src:reader.result,name:file.name,role:imageRoles[0]});reader.onerror=reject;reader.readAsDataURL(file);}))); 
  if(field!==$('ec-form').elements.attachments||!$('ec-dialog').classList.contains('active'))return;
  field.value=JSON.stringify([...JSON.parse(field.value),...images]);
 }catch(err){if(field===$('ec-form').elements.attachments)toast('图片读取失败，请重新上传');}
 finally{field.dataset.uploading='false';if(field===$('ec-form').elements.attachments)renderImages();}
}
$('ec-fields').addEventListener('click',e=>{
 if(caseCreating&&!readonly&&e.target.id==='ec-add-story'){$('ec-story-editor').hidden=false;e.target.hidden=true;$('ec-story-name').focus();return;}
 if(caseCreating&&!readonly&&e.target.id==='ec-save-story'){addCaseStory();return;}
 const singleChoice=e.target.closest('[data-case-single]');
 if(singleChoice&&!readonly){
  const wrap=singleChoice.closest('[data-case-picker]'),select=wrap.querySelector('select');
  wrap.querySelectorAll('[data-case-single]').forEach(option=>option.setAttribute('aria-pressed',String(option===singleChoice)));
  select.value=singleChoice.dataset.caseSingle;syncCasePicker(wrap);select.dispatchEvent(new Event('change',{bubbles:true}));wrap.classList.remove('open');wrap.querySelector('.ts-trigger').setAttribute('aria-expanded','false');return;
 }
 const removeCase=e.target.closest('[data-case-remove]');
 if(removeCase&&!readonly){
  e.stopPropagation();const wrap=removeCase.closest('[data-case-picker]'),input=[...wrap.querySelectorAll('.ts-panel input')].find(input=>input.value===removeCase.dataset.caseRemove),single=wrap.querySelector(`[data-case-single="${CSS.escape(removeCase.dataset.caseRemove)}"]`);
  if(single){single.setAttribute('aria-pressed','false');const select=wrap.querySelector('select');select.value='';syncCasePicker(wrap);select.dispatchEvent(new Event('change',{bubbles:true}));}
  else if(input){input.checked=false;input.dispatchEvent(new Event('change',{bubbles:true}));}
  return;
 }
 const removeTag=e.target.closest('[data-remove-tag]');
 if(removeTag&&!readonly){
  e.stopPropagation();
  const wrap=removeTag.closest('[data-tag-select]'),input=[...wrap.querySelectorAll('input[name="tag_ids"]')].find(input=>input.value===removeTag.dataset.removeTag);
  if(input){input.checked=false;syncTagSelection(wrap);wrap.querySelector('.ts-trigger').focus();}return;
 }
 const expandTag=e.target.closest('[data-tag-expand]');
 if(expandTag&&!readonly){
  toggleTagNode(expandTag);return;
 }
 if(!readonly&&e.target.closest('[data-category]'))selectCategory(e.target.closest('[data-category]').dataset.category);
 if(!readonly&&e.target.id==='ec-add-category'){$('ec-category-editor').hidden=false;e.target.hidden=true;$('ec-category-name').focus();}
 if(!readonly&&e.target.id==='ec-save-category')addCategory();
 if(!readonly&&e.target.closest('[data-ownership]'))dataOwnershipSelect(e.target.closest('[data-ownership]').dataset.ownership);
 if(!readonly&&e.target.id==='ec-add-data-ownership'){$('ec-data-ownership-editor').hidden=false;e.target.hidden=true;$('ec-data-ownership-name').focus();}
 if(!readonly&&e.target.id==='ec-save-data-ownership')addDataOwnership();
 if(e.target.closest('#ec-image-upload')&&!readonly)$('ec-image-file').click();
 if(e.target.hasAttribute('data-remove-image')&&!readonly){const field=$('ec-form').elements.attachments,values=JSON.parse(field.value);values.splice(Number(e.target.dataset.removeImage),1);field.value=JSON.stringify(values);renderImages();}
 const removeUserGroup=e.target.closest('[data-remove-user-group]');
 if(removeUserGroup&&!readonly){const wrap=removeUserGroup.closest('.ts-wrap'),input=wrap?.querySelector(`input[name="visible_group_ids"][value="${CSS.escape(removeUserGroup.dataset.removeUserGroup)}"]`);if(input){input.checked=false;syncUserGroupChips(wrap);}return;}
 const fieldToggle=e.target.closest('[data-field-toggle="enabled"]');if(fieldToggle&&!readonly){const enabled=fieldToggle.getAttribute('aria-pressed')==='true';fieldToggle.setAttribute('aria-pressed',String(!enabled));fieldToggle.classList.toggle('on',!enabled);}
 const trigger=e.target.closest('.ts-trigger');if(trigger&&!readonly&&trigger.getAttribute('aria-disabled')!=='true'){const wrap=trigger.closest('.ts-wrap'),wasOpen=wrap.classList.contains('open');$('ec-fields').querySelectorAll('.ts-wrap.open').forEach(other=>{other.classList.remove('open');other.querySelector('.ts-trigger').setAttribute('aria-expanded','false');});wrap.classList.toggle('open',!wasOpen);trigger.setAttribute('aria-expanded',String(!wasOpen));}
 if(!readonly&&e.target.closest('[data-remove-condition],[data-remove-value]')){e.target.closest('tr').remove();syncFactorDefault();refreshConditions();}
 if(e.target.id==='ec-add-factor'){$('ec-factors').insertAdjacentHTML('beforeend',conditionRow());refreshConditions();}
 if(e.target.id==='ec-add-value'&&!readonly){$('ec-values').insertAdjacentHTML('beforeend',valueRow());syncFactorDefault();}
 syncSelects();
});
 $('ec-fields').addEventListener('keydown',e=>{if(e.target.id==='ec-story-name'&&e.key==='Enter'){e.preventDefault();addCaseStory();}else if(e.target.id==='ec-category-name'&&e.key==='Enter'){e.preventDefault();addCategory();}else if(e.target.id==='ec-data-ownership-name'&&e.key==='Enter'){e.preventDefault();addDataOwnership();}else if(e.target.matches('[data-remove-user-group]')&&['Enter',' '].includes(e.key)){e.preventDefault();e.target.click();}else if(e.target.matches('.ts-trigger')&&['Enter',' '].includes(e.key)){e.preventDefault();e.target.click();}});
$('ec-fields').addEventListener('input',e=>{if(!readonly&&e.target.matches('#ec-values [name="value"]'))syncFactorDefault();});
for(const type of ['dragover','dragleave','drop'])$('ec-fields').addEventListener(type,e=>{
 const zone=e.target.closest('#ec-image-upload');if(!zone||readonly)return;e.preventDefault();
 zone.classList.toggle('dragover',type==='dragover');if(type==='drop')addImages(e.dataTransfer.files);
});
$('ec-fields').addEventListener('change',e=>{
 if(scenarioEditing&&e.target.name==='factor_id'){
  const select=$('ec-form').elements.factor_value,values=factorValueOptions(db.factors.find(f=>f.id===e.target.value)?.values||[]);
  select.innerHTML=options(values.map(value=>({id:value,name:value})),values.includes(select.value)?select.value:'');
 }
 if(e.target.id==='ec-image-file'&&!readonly)addImages(e.target.files);
 if(e.target.hasAttribute('data-image-role')&&!readonly){const field=$('ec-form').elements.attachments,values=JSON.parse(field.value);values[Number(e.target.dataset.imageRole)].role=e.target.value;field.value=JSON.stringify(values);}
 if(e.target.name==='visibility')$('ec-fields').querySelector('[data-visibility-groups="true"]')?.style.setProperty('display',e.target.value==='受限'?'':'none');
 if(caseCreating&&['case_stage','story_id','skill_ids'].includes(e.target.name))refreshCaseOptions();
 else if(e.target.name==='case_stage')$('ec-form').elements.story_id.innerHTML=options(db.stories,$('ec-form').elements.story_id.value);
 if(e.target.matches('.ec-factor-id')){const f=db.factors.find(x=>x.id===e.target.value);e.target.closest('tr').querySelector('.ec-factor-values').innerHTML=conditionValueInput(f,!batchCreating&&f?.default_value?[f.default_value]:[]);refreshConditions();}
 if(e.target.type==='checkbox'&&e.target.isConnected){if(batchCreating)syncBatchSelection();else{const wrap=e.target.closest('.ts-wrap');if(wrap?.hasAttribute('data-case-picker'))syncCasePicker(wrap);else if(wrap?.hasAttribute('data-tag-select'))syncTagSelection(wrap);else if(wrap?.dataset.chipSelect)syncUserGroupChips(wrap);else wrap.querySelector('.ts-placeholder').textContent=[...wrap.querySelectorAll('input:checked')].map(x=>x.parentElement.textContent.trim()).join('、')||'请选择';}}
 syncSelects();
});
$('ec-form').addEventListener('submit',e=>{
 e.preventDefault();if(readonly)return;
 if(batchCreating){
  try{const created=batchScenarios(db,collectBatchSelection(),new Date().toLocaleString('sv-SE'));
   if(!created.length){$('ec-error').textContent='所选组合已存在';return;}
   const next=clone(db);next.scenarios=[...created,...next.scenarios];
   if(persist(next)){close('ec-dialog');page=1;render();toast(`已新增 ${created.length} 条场景`);}
  }catch(error){$('ec-error').textContent=error.message;}return;
 }
 if($('ec-form').elements.attachments?.dataset.uploading==='true')return toast('请等待图片读取完成');const r=collect(),next=clone(db);
 if(caseCreating)next.stories.unshift(...pendingCaseStories.map(story=>({...story,project:r.project,created_at:r.created_at,updated_at:r.updated_at,created_by:demoActor,updated_by:demoActor})));
 const errors=scenarioEditing?[]:validate(next,kind,r,editing);
 if(caseCreating)errors.push(...validateCaseSelection(next,r));
 if(errors.length){$('ec-error').textContent=errors.join('；');return;}
 if(scenarioEditing){try{if(persist(saveScenarioRow(db,r))){close('ec-dialog');render();toast('保存成功');}}catch(error){$('ec-error').textContent=error.message;}return;}
 const collection=scenarioEditing?'scenarios':kind;if(editing)next[collection][next[collection].findIndex(x=>x.id===editing)]=r;else {if(kind!=='test-cases')r.display_id=nextDisplayId(next[kind]);next[kind].unshift(r);}
 if(persist(next)){close('ec-dialog');page=1;render();toast('保存成功');}
});
$('ec-tbody').addEventListener('click',e=>{
 const collection=e.target.closest('tr')?.dataset.collection||kind;
 const switchButton=e.target.closest('[data-field-toggle="enabled"]');
 if(switchButton){
  if(switchButton.disabled)return;
  const id=switchButton.closest('tr')?.querySelector('[data-action="edit"]')?.dataset.id;
  const r=id&&db[collection].find(x=>x.id===id);if(!r||section==='elements'&&elementForms[kind]&&r.publish_status==='未发布')return;
  const row={...r,enabled:r.enabled===false,updated_at:new Date().toLocaleString('sv-SE'),updated_by:demoActor};
  const errors=collection==='scenarios'?validateScenario(db,row):validate(db,kind,row,id);
  if(errors.length)return toast(errors.join('；'));
  const next=clone(db);next[collection][next[collection].findIndex(x=>x.id===id)]=row;
  if(persist(next)){render();toast('启用状态已更新');}return;
 }
 const btn=e.target.closest('[data-action]');if(!btn||btn.disabled)return;
 const {action,id}=btn.dataset,r=db[collection].find(x=>x.id===id);if(!r)return;
 if(action==='view-images'){open('view',id);$('ec-images-section').scrollIntoView({block:'center'});return;}
 if(['view','edit','copy','edit-values'].includes(action))return open(action,id,collection,btn.closest('tr')?.dataset.scenarioKey);
 if(action==='delete'&&section==='scenario'){
  const rowKey=btn.closest('tr').dataset.scenarioKey,row=scenarioValueRows(db).find(x=>x.row_key===rowKey);
  if(!row)return toast('场景记录已不存在，请刷新列表');
  if(scenarioCaseCount(db,row)>0)return toast('该场景已有评测用例，无法删除');
  pendingScenarioKey=rowKey;$('ec-confirm-text').textContent=`确认删除场景「${row.name} / ${name('factors',row.factor_id)} / ${row.factor_value||'--'}」？`;show('ec-confirm');return;
 }
 pendingScenarioKey=null;
 const refs=collection==='scenarios'?[]:references(db,kind,id);
 if(action==='publish'){
  if(!canPublish(kind,section,r))return;
  const row={...r,publish_status:'已发布',updated_at:new Date().toLocaleString('sv-SE')},errors=validate(db,kind,row,id);
  if(errors.length)return toast(errors.join('；'));
  const next=clone(db);next[kind][next[kind].findIndex(x=>x.id===id)]=row;
  if(persist(next)){render();toast('发布成功');}return;
 }
 if(action==='delete'){if(publishedDeleteBlocked(kind,r))return toast('已发布记录不可删除');if(refs.length)return toast('无法删除：被 '+refs.slice(0,3).join('、')+' 引用');pendingDelete=id;pendingCollection=collection;$('ec-confirm-text').textContent=`确认删除「${r.name||name('stories',r.story_id)}」？`;show('ec-confirm');}
});
$('ec-confirm-delete').onclick=()=>{
 if(pendingScenarioKey){try{if(persist(deleteScenarioRow(db,pendingScenarioKey))){pendingScenarioKey=null;close('ec-confirm');render();toast('已删除');}}catch(error){toast(error.message);}return;}
 const collection=pendingCollection||kind;if(publishedDeleteBlocked(kind,db[collection].find(x=>x.id===pendingDelete)))return toast('已发布记录不可删除');if(collection!=='scenarios'&&references(db,kind,pendingDelete).length)return toast('记录已被引用，无法删除');const next=clone(db);next[collection]=next[collection].filter(x=>x.id!==pendingDelete);if(persist(next)){close('ec-confirm');render();toast('已删除');}
};
$('ec-confirm-cancel').onclick=()=>close('ec-confirm');$('ec-create').onclick=()=>open('create');$('ec-close').onclick=$('ec-cancel').onclick=()=>close('ec-dialog');
$('ec-filter').onsubmit=e=>{e.preventDefault();page=1;render();};$('ec-clear').onclick=()=>{$('ec-filter').reset();if($('ec-data-owner'))$('ec-data-owner').value='';$('ec-filter').querySelectorAll('input[type="checkbox"]').forEach(x=>x.checked=false);closeFilterMenus();page=1;render();};$('ec-prev').onclick=()=>{page--;render();};$('ec-next').onclick=()=>{page++;render();};
function closeFilterMenus(){document.querySelectorAll('[data-filter-kind].open').forEach(wrap=>{wrap.classList.remove('open');wrap.querySelector('.ts-trigger').setAttribute('aria-expanded','false');});}
$('ec-filter').addEventListener('click',e=>{const trigger=e.target.closest('.ts-trigger');if(!trigger)return;const wrap=trigger.closest('.ts-wrap'),wasOpen=wrap.classList.contains('open');closeFilterMenus();wrap.classList.toggle('open',!wasOpen);trigger.setAttribute('aria-expanded',String(!wasOpen));});
$('ec-filter').addEventListener('change',e=>{const wrap=e.target.closest('[data-filter-kind]');if(wrap)updateFilterSummary(wrap);});
document.addEventListener('click',e=>{if(!e.target.closest('[data-filter-kind]'))closeFilterMenus();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeFilterMenus();});
render();
if(section==='scenario')new ResizeObserver(syncScenarioFrozenColumns).observe($('ec-table').parentElement);
if(section==='elements'&&elementForms[kind])new ResizeObserver(syncElementFrozenColumns).observe($('ec-table').parentElement);
document.addEventListener('keydown',e=>{if(e.key==='Escape'){document.querySelectorAll('.ts-wrap.open').forEach(x=>x.classList.remove('open'));if($('ec-benchmark-add-dialog')?.classList.contains('active'))closeAddToBenchmark();else if($('ec-confirm').classList.contains('active'))close('ec-confirm');else if($('ec-benchmark-dialog')?.classList.contains('active'))close('ec-benchmark-dialog');else if($('ec-dialog').classList.contains('active'))close('ec-dialog');}if(e.key==='Tab'){const panel=document.querySelector('#ec-confirm.active,#ec-dialog.active,#ec-benchmark-dialog.active,#ec-benchmark-add-dialog.active');if(!panel)return;const focusable=[...panel.querySelectorAll('button,input,select,textarea,[tabindex="0"]')].filter(x=>!x.disabled&&x.offsetParent!==null);const first=focusable[0],last=focusable.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});
document.addEventListener('click',e=>{if(!e.target.closest('.ts-wrap'))document.querySelectorAll('.ts-wrap.open').forEach(x=>x.classList.remove('open'));});
root.addEventListener('storage',e=>{if(e.key===storageKey&&e.newValue){try{db=upgrade(seed,JSON.parse(e.newValue));dataOwnershipValues=[...db.data_ownership_options];render();}catch(err){toast('无法载入更新的数据');}}});
})(typeof globalThis!=='undefined'?globalThis:this);
