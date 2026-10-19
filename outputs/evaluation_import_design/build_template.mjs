import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const out = path.dirname(fileURLToPath(import.meta.url));
const workbook = Workbook.create();
const sheets = {};
for (const name of ['评测用例', 'Factor配置', '图片', '填写说明', '选项字典', '填写示例']) {
  sheets[name] = workbook.worksheets.add(name);
  sheets[name].showGridLines = false;
}
const colors = { header: '#253B61', blue: '#245DB0', muted: '#637083', required: '#FFF5D9', light: '#EFF3F8', line: '#CCD5E0' };
const mainHeaders = ['用例 ID','Stage','Story','prompt_EN','prompt_CN','Skill','数据归属','所属项目','标签','道具','可见性','可见用户组'];
const factorHeaders = ['用例 ID','Factor','Factor 取值'];
const imageHeaders = ['用例 ID','文件路径','图片类型'];
function block(sheet,r,c,values) {
  if(values.length) sheet.getRangeByIndexes(r,c,values.length,values[0].length).values = values;
}
function base(sheet,rows,cols) {
  const range = sheet.getRangeByIndexes(0,0,rows,cols);
  range.setNumberFormat('@');
  range.format.font = { name:'Arial', size:11, color:'#202A38' };
  range.format.verticalAlignment = 'center';
  range.format.rowHeight = 28;
}
function header(sheet,row,labels) {
  block(sheet,row,0,[labels]);
  const range = sheet.getRangeByIndexes(row,0,1,labels.length);
  range.format.fill = colors.header;
  range.format.font = { name:'Arial', size:11, color:'#FFFFFF', bold:true };
  range.format.rowHeight = 34;
  range.format.horizontalAlignment = 'center';
}
function widths(sheet,items) {
  items.forEach((w,i)=>{sheet.getRangeByIndexes(0,i,1,1).format.columnWidth=w;});
}
function inputs(name,headers,widthArray,required) {
  const sheet = sheets[name]; base(sheet,51,headers.length);header(sheet,0,headers);widths(sheet,widthArray);
  for (const col of required) sheet.getRangeByIndexes(1,col,50,1).format.fill=colors.required;
  sheet.freezePanes.freezeRows(1);sheet.freezePanes.freezeColumns(1);
  sheet.tabColor=colors.blue;
}
inputs('评测用例', mainHeaders,[23,27,34,66,44,37,22,24,35,45,19,33],[0,1,2,3,4,6]);
inputs('Factor配置', factorHeaders,[23,63,43],[0,1,2]);
inputs('图片',imageHeaders,[23,65,30],[0,1,2]);
sheets['评测用例'].getRange('G2:G51').dataValidation={rule:{type:'list',values:['Train-训练','Eval-白盒','Test-黑盒']}};
sheets['评测用例'].getRange('H2:H51').dataValidation={rule:{type:'list',values:['预训练评测','后训练评测']}};
sheets['评测用例'].getRange('K2:K51').dataValidation={rule:{type:'list',values:['公开','受限']}};
sheets['图片'].getRange('C2:C51').dataValidation={rule:{type:'list',values:['初始状态','目标状态','关键物体位置']}};

const rules = [
 ['评测用例','用例 ID','必填','文本；字母、数字、横线、下划线，全平台唯一；建议≤64字符。'],
 ['评测用例','Stage','必填，单选','完整名称或匹配键；唯一关联 Stage 定义。未知项在预检中处理。'],
 ['评测用例','Story','必填，单选','完整名称或匹配键；独立匹配 Story，组合是否存在由场景预览处理。'],
 ['评测用例','prompt_EN','必填','英文提示词；建议≤4,000字符，不自动补写。'],
 ['评测用例','prompt_CN','必填','中文提示词；建议≤4,000字符，不自动翻译补齐。'],
 ['评测用例','Skill','非必填，多选','单元格内换行，每行一个完整名称/匹配键；不要按逗号或斜杠分隔。'],
 ['评测用例','数据归属','必填','标准项或平台已有自定义项；下拉列出标准项，自定义项由系统预检。'],
 ['评测用例','所属项目','表内可空','空值继承导入抽屉必选项目；有值必须与本批项目一致。'],
 ['评测用例','标签','非必填，多选','每行一个完整层级路径或稳定匹配键；不能只填重名叶子标签。'],
 ['评测用例','道具','非必填','实际道具说明，建议≤2,000字符；不要填“同上”等不明确引用。'],
 ['评测用例','可见性','默认公开','公开 / 受限；受限时可见用户组必填。'],
 ['评测用例','可见用户组','受限时必填','每行一个数据平台用户组匹配键；公开时应为空。'],
 ['Factor配置','用例 ID','子行必填','必须与本批主表 ID 相同；主表跳过时子行一起跳过。'],
 ['Factor配置','Factor','子行必填，单选','一个完整 Factor 名称/匹配键；同一 Factor 可多行填写取值。'],
 ['Factor配置','Factor 取值','子行必填，单值','一行一个完整取值，必须属于所选 Factor；球体/圆弧类不能拆分。'],
 ['图片','用例 ID','子行必填','必须与本批主表 ID 相同；不引用批次外已有用例。'],
 ['图片','文件路径','子行必填','图片 zip 内相对路径；必须存在实际文件，不填 URL 或飞书 token。'],
 ['图片','图片类型','子行必填，单选','初始状态 / 目标状态 / 关键物体位置；每例最多3张，当前每张≤1MB。'],
];
const guide=sheets['填写说明'];base(guide,44,4);widths(guide,[20,25,24,94]);
block(guide,1,0,[['评测用例导入模板 V1.0（草案）']]);guide.getRange('A2').format.font={name:'Arial',size:15,bold:true};
block(guide,3,0,[['填写方式','前三个 Sheet 填数据；其余页不导入。']]);
block(guide,4,0,[['必填提示','浅黄色为必填输入；受限用户组为条件必填。']]);
block(guide,5,0,[['多选格式','单元格内换行，每行一个完整项；无宏多选下拉。']]);
block(guide,6,0,[['项目与状态','导入抽屉必选项目；建议新增用例统一未发布、停用。']]);
block(guide,7,0,[['字典说明','固定枚举供参考；动态字典需由平台按当前权限生成。']]);
for(let row=3;row<=7;row++){guide.getRangeByIndexes(row,1,1,1).format.columnWidth=25;}
// Short guidance uses D, so long text never spills across populated fields.
for(let row=3;row<=7;row++){
  const v=guide.getRangeByIndexes(row,1,1,1).values[0][0];
  guide.getRangeByIndexes(row,1,1,1).clear({applyTo:'contents'});block(guide,row,3,[[v]]);
}
header(guide,9,['工作表','字段','必填性','格式与校验']);block(guide,10,0,rules);
guide.getRange('D11:D28').format.wrapText=true;guide.getRange('A11:D28').format.rowHeight=48;
block(guide,30,0,[['源字段映射','平台目标','类型','处理说明']]);
guide.getRange('A31:D31').format.fill=colors.light;guide.getRange('A31:D31').format.font.bold=true;
block(guide,31,0,[
 ['Prompt / prompt_ch','prompt_EN / prompt_CN','直接映射','兼容导入自动识别原表头。'],
 ['Stage / Story / Skill标签','对应要素ID','关联','复用已有；未知项补全确认后新增。'],
 ['Factor / Factor取值','Factor配置子行','结构化映射','保留 Factor→取值对应关系；合并键需确认。'],
 ['来源等历史字段','来源扩展信息','保留','不映射为项目、用户组、发布状态或评测集成员。'],
 ['表头依据','评测组线下测试用例表','飞书 Base','https://nwd4iy9rd2s.feishu.cn/base/OQ2UbV65natigrstPbXcwhWinyb'],
]);
guide.getRange('A32:D36').format.wrapText=true;guide.getRange('A32:D36').format.rowHeight=48;
guide.freezePanes.freezeRows(10);guide.tabColor='#7E8AA2';

const dict=sheets['选项字典'];base(dict,27,4);widths(dict,[25,28,28,85]);
header(dict,0,['字段','匹配键','展示名','说明']);
const dictRows=[
 ['数据归属','Train-训练','Train-训练','标准选项；如有自定义项，正式模板由平台追加。'],
 ['数据归属','Eval-白盒','Eval-白盒','标准选项；兼容原表 Eval。'],
 ['数据归属','Test-黑盒','Test-黑盒','标准选项。'],
 ['所属项目','预训练评测','预训练评测','当前原型项目；正式模板仅导出当前用户可写项目。'],
 ['所属项目','后训练评测','后训练评测','当前原型项目；单批仅一个项目。'],
 ['可见性','公开','公开','留空默认公开。'],
 ['可见性','受限','受限','必须填写可见用户组。'],
 ['图片类型','初始状态','初始状态','每张图片选一个类型。'],
 ['图片类型','目标状态','目标状态','同一用例总计最多3张。'],
 ['图片类型','关键物体位置','关键物体位置','不能用源图片顺序猜测类型。'],
 ...['Stage','Story','Skill','Factor','Factor 取值','标签','可见用户组'].map(x=>[x,'（平台生成）','（平台生成）','草案占位，不可复制为选项；正式下载时替换为可用展示名〔稳定ID〕。']),
];
block(dict,1,0,dictRows);dict.getRange('D2:D18').format.wrapText=true;dict.getRange('A2:D18').format.rowHeight=42;
dict.freezePanes.freezeRows(1);dict.freezePanes.freezeColumns(1);

const example=sheets['填写示例'];base(example,23,12);widths(example,[23,55,34,63,43,35,22,23,28,32,18,26]);
block(example,1,0,[['填写示例（不导入）']]);example.getRange('A2').format.font={name:'Arial',size:15,bold:true};
block(example,2,0,[['示例仅解释结构；要素须在平台匹配或确认新增。']]);
header(example,4,mainHeaders);
block(example,5,0,[['CASE_DEMO_001','厨房餐厅','餐桌整理','Place the bowl on the table.','把碗放在桌上。','抓取（Pick）\n放置（Place）','Eval-白盒','预训练评测','','碗、餐桌','公开','']]);
example.getRange('A6:L6').format.rowHeight=64;example.getRange('A6:L6').format.wrapText=true;
block(example,8,0,[['Factor配置：同一用例多值分行填写']]);header(example,9,factorHeaders);
block(example,10,0,[
 ['CASE_DEMO_001','被操作物品属性-尺寸','大'],
 ['CASE_DEMO_001','被操作物品属性-尺寸','小'],
 ['CASE_DEMO_001','被操作物品属性-几何形态-物体形状','球体/圆弧类'],
]);
example.getRange('B11:B13').format.wrapText=true;example.getRange('A11:C13').format.rowHeight=48;
block(example,15,0,[['图片：可选，文件需与图片包一致']]);header(example,16,imageHeaders);
block(example,17,0,[['CASE_DEMO_001','images/CASE_DEMO_001/initial.png','初始状态']]);
example.getRange('B18').format.wrapText=true;example.getRange('A18:C18').format.rowHeight=52;
block(example,20,0,[['该例产生 1 个用例、2 个 Factor 配置、3 个取值选择。']]);
example.tabColor='#7E8AA2';

workbook.recalculate();
await fs.mkdir(path.join(out,'previews'),{recursive:true});
const renders=[
 ['评测用例','A1:F7','cases-left'],['评测用例','G1:L7','cases-right'],
 ['Factor配置','A1:C7','factors'],['图片','A1:C7','images'],
 ['填写说明','A2:D18','guide-top'],['填写说明','A19:D36','guide-bottom'],
 ['选项字典','A1:D18','dictionary'],['填写示例','A1:F18','example-left'],['填写示例','G5:L6','example-right'],
];
for(const [sheetName,range,name] of renders.filter(row=>!process.env.RENDER_ONLY||row[2]===process.env.RENDER_ONLY)){
  const png=await workbook.render({sheetName,range,scale:1,format:'png'});
  await fs.writeFile(path.join(out,'previews',`${name}.png`),new Uint8Array(await png.arrayBuffer()));
}
const inspect=await workbook.inspect({kind:'table',range:'填写示例!A5:L6',include:'values,formulas',tableMaxRows:3,tableMaxCols:12,maxChars:2500});
const errors=await workbook.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20},maxChars:1500});
await fs.writeFile(path.join(out,'template-check.json'),JSON.stringify({inspect,errors},null,2));
const file=await SpreadsheetFile.exportXlsx(workbook);
await file.save(path.join(out,'评测用例导入模板.xlsx'));
console.log('Saved 评测用例导入模板.xlsx; rendered all six sheets.');
