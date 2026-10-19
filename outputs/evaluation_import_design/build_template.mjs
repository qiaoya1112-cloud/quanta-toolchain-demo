import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const out=path.dirname(fileURLToPath(import.meta.url));
const wb=Workbook.create();
const input=wb.worksheets.add('评测用例');
const guide=wb.worksheets.add('填写说明');
const navy='#253B61', muted='#647185', line='#DDE3EB';
function write(s,r,c,values){s.getRangeByIndexes(r,c,values.length,values[0].length).values=values;}
function base(s,rows,cols){
 s.showGridLines=false;
 const area=s.getRangeByIndexes(0,0,rows,cols);
 area.setNumberFormat('@');
 area.format.font={name:'Arial',size:11,color:'#202A38'};
 area.format.verticalAlignment='center';area.format.rowHeight=36;
}
function widths(s,values){values.forEach((w,c)=>{s.getRangeByIndexes(0,c,1,1).format.columnWidth=w;});}
function header(s,row,labels){
 write(s,row,0,[labels]);const a=s.getRangeByIndexes(row,0,1,labels.length);
 a.format.fill=navy;a.format.font={name:'Arial',size:11,bold:true,color:'#FFFFFF'};
 a.format.horizontalAlignment='center';a.format.rowHeight=38;
}

const headers=['用例 ID','Stage','Story','prompt_EN','prompt_CN','Skill','Factor 1','Factor 取值 1','Factor 2','Factor 取值 2','数据归属','所属项目','标签','道具','图片 1','图片类型 1','图片 2','图片类型 2','图片 3','图片类型 3','可见性','可见用户组'];
base(input,24,22);widths(input,[23,24,29,55,40,33,46,30,46,30,22,23,32,33,39,25,39,25,39,25,18,32]);
write(input,0,0,[['评测用例导入模板 V1.1']]);
input.getRange('A1').format.font={name:'Arial',size:16,bold:true,color:navy};
write(input,1,0,[['第4行灰底为示例，不导入；第5行起填写。深蓝表头为必填。每行一个用例，Factor和图片都在本行；更多列向右滚动。']]);
input.getRange('A2').format.font={name:'Arial',size:11,color:muted};
input.getRange('A1:V2').format.rowHeight=28;
header(input,2,headers);
input.getRange('A3:V3').format.fill='#E9EDF3';
input.getRange('A3:V3').format.font={name:'Arial',size:11,bold:true,color:'#253B61'};
for(const c of [0,1,2,3,4,10]){
 const a=input.getRangeByIndexes(2,c,1,1);a.format.fill=navy;a.format.font.color='#FFFFFF';
}
const sample=['CASE_DEMO_001','厨房餐厅','餐桌整理','Place the large and small bowls on the table.','把大碗和小碗放在桌上。','抓取（Pick）\n放置（Place）','被操作物品属性-尺寸','大\n小','被操作物品属性-几何形态-物体形状','球体/圆弧类','Eval-白盒','预训练评测','','碗、餐桌','CASE_DEMO_001_initial.png','初始状态','','','','','公开',''];
write(input,3,0,[sample]);
input.getRange('A4:V4').format.fill='#F1F3F6';
input.getRange('A4:V4').format.font.color=muted;
input.getRange('A4:V4').format.rowHeight=72;
input.getRange('A4:V24').format.wrapText=true;
input.getRange('A5:V24').format.borders={insideHorizontal:{style:'thin',color:line},bottom:{style:'thin',color:line}};
input.freezePanes.freezeRows(4);input.freezePanes.freezeColumns(1);input.tabColor='#245DB0';
input.getRange('K5:K24').dataValidation={rule:{type:'list',values:['Train-训练','Eval-白盒','Test-黑盒']}};
input.getRange('L5:L24').dataValidation={rule:{type:'list',values:['预训练评测','后训练评测']}};
input.getRange('U5:U24').dataValidation={rule:{type:'list',values:['公开','受限']}};
for(const col of ['P','R','T'])input.getRange(`${col}5:${col}24`).dataValidation={rule:{type:'list',values:['初始状态','目标状态','关键物体位置']}};

base(guide,64,4);widths(guide,[34,24,92,46]);
write(guide,1,0,[['填写说明与字段映射']]);guide.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:navy};
write(guide,2,0,[['只填写“评测用例”一张表。本页不导入；第4行灰底示例由模板规则排除。']]);
header(guide,4,['字段','必填性','填写与校验规则','样例']);
const rules=[
 ['用例 ID','必填','字母、数字、横线、下划线，全平台唯一，建议≤64字符；保留前导零。','CASE_001'],
 ['Stage','必填，单选','填写完整名称；唯一关联已有 Stage，未知/重名项上传后处理。','厨房餐厅'],
 ['Story','必填，单选','填写完整名称；独立匹配，不要求事先存在 Stage×Story 组合。','餐桌整理'],
 ['prompt_EN','必填','英文提示词，建议≤4,000字符，缺失不能自动补写。','Place the bowl on the table.'],
 ['prompt_CN','必填','中文提示词，建议≤4,000字符，缺失不能自动翻译补齐。','把碗放在桌上。'],
 ['Skill','非必填，多选','单元格内换行，每行一个完整选项名称，不按逗号或斜杠拆分。','抓取（Pick）\n放置（Place）'],
 ['Factor 1','非必填，单选','一个完整 Factor 名称；有 Factor 必须填写同编号取值。','被操作物品属性-尺寸'],
 ['Factor 取值 1','有Factor 1时必填','多选在单元格内换行，每行一个完整取值；必须属于 Factor 1。','大\n小'],
 ['Factor 2','非必填，单选','第二个 Factor，不能与本行其他 Factor 重复；两列可同时留空。','被操作物品属性-几何形态-物体形状'],
 ['Factor 取值 2','有Factor 2时必填','取值必须属于 Factor 2；球体/圆弧类是一个值，不能拆分。','球体/圆弧类'],
 ['数据归属','必填','标准项或已有自定义项；未知项上传后明确关联/新增。','Train-训练 / Eval-白盒 / Test-黑盒'],
 ['所属项目','表内可空','空值继承导入抽屉必选项目；填写时必须与本批项目一致。','预训练评测'],
 ['标签','非必填，多选','每行一个完整层级路径，不能只填可能重名的叶子标签。','使用平台已有完整路径'],
 ['道具','非必填','填写实际道具，建议≤2,000字符，不用“同上”等不明确引用。','碗、餐桌'],
 ['图片 1','非必填','图片zip内唯一文件名/相对路径，必须有实际文件；每张≤1MB。','CASE_001_initial.png'],
 ['图片类型 1','有图片1时必填','初始状态 / 目标状态 / 关键物体位置，单选。','初始状态'],
 ['图片 2','非必填','同图片1，可留空；有文件必须填写同编号类型。','CASE_001_target.png'],
 ['图片类型 2','有图片2时必填','与图片2对应；不能只填类型，不填图片。','目标状态'],
 ['图片 3','非必填','同图片1，每例最多3张；不填写URL或飞书附件token。','CASE_001_object.png'],
 ['图片类型 3','有图片3时必填','与图片3对应，单选。','关键物体位置'],
 ['可见性','默认公开','公开 / 受限；受限时可见用户组必填。','公开'],
 ['可见用户组','受限时必填，多选','数据平台已有用户组，单元格内每行一个；公开时保持空白。','使用平台已有用户组名称'],
];
write(guide,5,0,rules);guide.getRange('A6:D27').format.wrapText=true;guide.getRange('A6:D27').format.rowHeight=52;
write(guide,29,0,[['线下表头与平台映射']]);guide.getRange('A30').format.font.bold=true;
header(guide,30,['源字段','平台字段/位置','处理方式','说明']);
const mappings=[
 ['用例ID','用例 ID','保留业务ID；内部主键由平台生成。','唯一性校验'],
 ['Stage','Stage 定义关联','名称解析为ID；未知项确认后补全新增。','不整体迁移所有选项'],
 ['Story','Story 定义关联','名称解析为ID；与Stage的组合另存场景库。','不另建英文Story'],
 ['Prompt','prompt_EN','直接写入英文提示词。','必填'],
 ['prompt_ch','prompt_CN','直接写入中文提示词。','必填'],
 ['Skill标签','Skill 多选关联','数组逐项匹配Skill，转成关联ID。','非必填'],
 ['Factor','Factor 配置','保持每个Factor与对应取值的关系。','标准模板用编号列'],
 ['Factor取值','对应 Factor 取值','兼容旧JSON；标准模板同行填写，每行一个完整值。','不要求手写JSON'],
 ['数据归属','数据归属','Train→Train-训练，Eval→Eval-白盒，Test-黑盒不变。','自定义项明确处理'],
 ['道具','道具','保留文本，不创建道具字典。','不能按排序猜“同上”'],
 ['布置图片','场景示意图/布置图片','存实际图片并补充每张图片类型。','最多3张'],
 ['来源','来源扩展信息','保留原值，不转换为所属项目或标签。','不增加普通列表列'],
 ['版本','来源扩展信息','保留来源版本，不转换为优先级或发布状态。','不推断平台状态'],
 ['story(英文版）','来源扩展信息','保留英文名，不覆盖Story定义名称。','不自动建第二条Story'],
 ['ft采集组','来源扩展信息','保留采集组，不转为可见用户组。','不自动创建用户组'],
 ['是否采集过遥操数据','来源扩展信息','保留是/否/空，异常原值保留并提示。','不转为启用状态'],
 ['是否在eval场景集','来源扩展信息','仅保留标记，不自动创建评测集/成员。','另行显式操作'],
 ['前置用例（隐藏）','来源扩展信息','保留原值，不恢复已移除的依赖关系。','避免字段丢失'],
];
write(guide,31,0,mappings);guide.getRange('A32:D49').format.wrapText=true;guide.getRange('A32:D49').format.rowHeight=52;
write(guide,51,0,[['选项与扩展规则']]);guide.getRange('A53:D53').format.rowHeight=38;
header(guide,52,['字段/规则','形式','可选项/操作','说明']);
write(guide,53,0,[
 ['数据归属','单选','Train-训练 / Eval-白盒 / Test-黑盒；支持平台已有自定义项。','下拉为标准项'],
 ['所属项目','单批一个项目','预训练评测 / 后训练评测，实际以当前用户可写项目为准。','抽屉必选'],
 ['可见性','单选','公开 / 受限。','默认公开'],
 ['图片类型','单选','初始状态 / 目标状态 / 关键物体位置。','不按文件顺序猜类型'],
 ['更多 Factor','复制一对列','按 Factor 3 / Factor 取值 3 依次编号；不是最多2个Factor。','编号匹配，必须成对'],
 ['动态选项','平台实时生成','正式模板在本页追加当前可见的Stage/Story/Skill/Factor/取值/标签/用户组名称。','草案不放假选项'],
]);guide.getRange('A54:D59').format.wrapText=true;guide.getRange('A54:D59').format.rowHeight=52;
write(guide,61,0,[['表头依据：评测组线下测试用例表']]);
write(guide,62,0,[['https://nwd4iy9rd2s.feishu.cn/base/OQ2UbV65natigrstPbXcwhWinyb']]);
guide.freezePanes.freezeRows(5);guide.tabColor='#7E8AA2';

wb.recalculate();
await fs.mkdir(path.join(out,'previews'),{recursive:true});
for(const [sheetName,range,name] of [
 ['评测用例','A1:F8','v11-cases'],['评测用例','G3:N8','v11-factors'],['评测用例','O3:V8','v11-images'],
 ['填写说明','A2:D17','v11-guide-top'],['填写说明','A18:D27','v11-guide-fields'],
 ['填写说明','A30:D49','v11-mapping'],['填写说明','A52:D63','v11-options'],
]){
 const png=await wb.render({sheetName,range,scale:1,format:'png'});
 await fs.writeFile(path.join(out,'previews',`${name}.png`),new Uint8Array(await png.arrayBuffer()));
}
const check=await wb.inspect({kind:'table',range:'评测用例!A3:V5',include:'values,formulas',tableMaxRows:3,tableMaxCols:22,maxChars:3500});
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20},maxChars:1000});
await fs.writeFile(path.join(out,'template-check.json'),JSON.stringify({check,errors},null,2));
const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(path.join(out,'评测用例导入模板.xlsx'));
console.log('Saved V1.1: one input sheet, inline example, one guide sheet.');
