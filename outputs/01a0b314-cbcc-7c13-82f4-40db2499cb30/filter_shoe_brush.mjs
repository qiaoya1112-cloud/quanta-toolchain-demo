import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile, Workbook} from '@oai/artifact-tool';

const base = new URL('.', import.meta.url).pathname;
const input = await SpreadsheetFile.importXlsx(await FileBlob.load('/Users/benyin/Documents/workfile/collection_instructions_v9_materials_keyed.xlsx'));
const rows = input.worksheets.getItemAt(0).getRange('A1:L1130').values;
const previousFiles = [
  'collection_instructions_v9_指定道具筛选.xlsx',
  'collection_instructions_v9_零食相关去重.xlsx',
];
const previousIds = new Set();
for (const file of previousFiles) {
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(base + file));
  for (const row of wb.worksheets.getItemAt(0).getUsedRange().values.slice(1)) previousIds.add(row[2]);
}

const selected = [rows[0]];
const seen = new Set();
let candidates = 0, invalid = 0, overlap = 0;
for (const row of rows.slice(1)) {
  if (!String(row[10] ?? '').split('、').some(item => item.includes('鞋刷'))) continue;
  candidates++;
  const props = String(row[10] ?? '').split('、').map(v => v.trim());
  const keys = String(row[11] ?? '').split('、').map(v => v.trim());
  if (props.length !== keys.length || keys.some(key => !/^OBJ\d+$/.test(key))) { invalid++; continue; }
  if (previousIds.has(row[2])) { overlap++; continue; }
  if (seen.has(row[2])) continue;
  seen.add(row[2]);
  selected.push(row);
}

const wb = Workbook.create();
const sheet = wb.worksheets.add('鞋刷相关指令');
sheet.getRange(`A1:L${selected.length}`).values = selected;
sheet.getRange('A1:L1').format = {fill:'#DCEAF3',font:{name:'Arial',bold:true,color:'#153347',size:11},rowHeight:28};
sheet.getRange(`A2:L${selected.length}`).format.font = {name:'Arial',size:10};
sheet.getRange(`J2:J${selected.length}`).setNumberFormat('0.0');
const widths = [12,16,16,31,13,13,86,14,14,14,48,62];
for (let i=0;i<12;i++) sheet.getRangeByIndexes(0,i,selected.length,1).format.columnWidth=widths[i];
sheet.freezePanes.freezeRows(1);

if (selected.length-1 !== seen.size || selected.slice(1).some(r => previousIds.has(r[2]))) throw Error('Deduplication failed');
console.log(JSON.stringify({candidates,invalid,overlap,output:selected.length-1}));
console.log((await wb.inspect({kind:'table',range:'鞋刷相关指令!A1:L5',tableMaxRows:5,tableMaxCols:12,maxChars:2500})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:10},maxChars:1000})).ndjson);
const preview = await wb.render({sheetName:'鞋刷相关指令',range:'A1:F8',scale:1.5});
await fs.writeFile(base+'shoe_brush_preview.png',new Uint8Array(await preview.arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(wb)).save(base+'collection_instructions_v9_鞋刷相关去重.xlsx');
