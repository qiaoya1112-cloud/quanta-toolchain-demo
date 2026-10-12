import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile, Workbook} from '@oai/artifact-tool';

const base = new URL('.', import.meta.url).pathname;
const input = '/Users/benyin/Documents/workfile/collection_instructions_v9_materials_keyed.xlsx';
const output = base + 'collection_instructions_v9_指定道具筛选.xlsx';
const source = await SpreadsheetFile.importXlsx(await FileBlob.load(input));
const rows = source.worksheets.getItemAt(0).getRange('A1:L1130').values;
const terms = ['筷子', '笔记本', '皂盒', '菜刀', '充电器'];
const seen = new Set();
const selected = [rows[0]];
const counts = {};
for (const term of terms) {
  let count = 0;
  for (const row of rows.slice(1)) {
    const props = String(row[10] ?? '').split('、').map(v => v.trim());
    const keys = String(row[11] ?? '').split('、').map(v => v.trim());
    if (!props.some(p => p.includes(term))) continue;
    if (props.length !== keys.length || keys.some(k => !/^OBJ\d+$/.test(k))) continue;
    const id = row[2];
    if (seen.has(id)) continue;
    seen.add(id);
    selected.push(row);
    count++;
  }
  counts[term] = count;
}

const wb = Workbook.create();
const sheet = wb.worksheets.add('筛选结果');
sheet.getRange(`A1:L${selected.length}`).values = selected;
sheet.getRange('A1:L1').format = {
  fill: '#DCEAF3',
  font: {name: 'Arial', bold: true, color: '#153347', size: 11},
  rowHeight: 28,
};
sheet.getRange(`A2:L${selected.length}`).format.font = {name: 'Arial', size: 10};
sheet.getRange(`J2:J${selected.length}`).setNumberFormat('0.0');
sheet.getRange(`A1:A${selected.length}`).format.columnWidth = 12;
sheet.getRange(`B1:B${selected.length}`).format.columnWidth = 16;
sheet.getRange(`C1:C${selected.length}`).format.columnWidth = 16;
sheet.getRange(`D1:D${selected.length}`).format.columnWidth = 31;
sheet.getRange(`E1:F${selected.length}`).format.columnWidth = 13;
sheet.getRange(`G1:G${selected.length}`).format.columnWidth = 86;
sheet.getRange(`H1:J${selected.length}`).format.columnWidth = 14;
sheet.getRange(`K1:K${selected.length}`).format.columnWidth = 48;
sheet.getRange(`L1:L${selected.length}`).format.columnWidth = 62;
sheet.freezePanes.freezeRows(1);

let position = 1;
for (const term of terms) {
  for (let i = 0; i < counts[term]; i++, position++) {
    if (!String(selected[position][10]).includes(term)) throw Error('Group order mismatch');
  }
}
if (position !== selected.length || seen.size !== selected.length - 1) throw Error('Deduplication mismatch');
console.log(JSON.stringify({counts, total: selected.length - 1}));
console.log((await wb.inspect({kind:'table', range:'筛选结果!A1:L5', tableMaxRows:5, tableMaxCols:12, maxChars:2500})).ndjson);
console.log((await wb.inspect({kind:'match', searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options:{useRegex:true,maxResults:10}, maxChars:1000})).ndjson);
const preview = await wb.render({sheetName:'筛选结果', range:'A1:F8', scale:1.5});
await fs.writeFile(base + 'filtered_preview.png', new Uint8Array(await preview.arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(wb)).save(output);
console.log(output);
