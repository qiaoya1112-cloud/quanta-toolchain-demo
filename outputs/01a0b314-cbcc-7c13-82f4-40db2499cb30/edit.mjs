import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const dir = new URL('.', import.meta.url).pathname;
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load('/Users/benyin/Documents/workfile/工作簿1.xlsx'));
const s = wb.worksheets.getItem('Sheet1');
const rows = s.getRange('A1:C1130').values;
if (process.argv.includes('--inspect')) {
  console.log((await wb.inspect({kind:'table',range:'Sheet1!A1:C5',tableMaxRows:5,tableMaxCols:3,maxChars:2500})).ndjson);
  const im = await wb.render({sheetName:'Sheet1',range:'A1:C6',scale:1});
  await fs.writeFile(dir+'before.png',new Uint8Array(await im.arrayBuffer()));
} else {
  let state = 9182026;
  function rnd(){state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296;}
  const n=rows.length-1, main=Math.round(n*0.9), low=Math.floor((n-main)/2);
  const times=Array.from({length:n},(_,i)=>i<main ? (10+Math.floor(rnd()*991))/10 : i<main+low ? (1+Math.floor(rnd()*9))/10 : (1001+Math.floor(rnd()*98999))/10);
  times[main]=0.1; times[n-1]=9999.9;
  for(let i=n-1;i>0;i--){const j=Math.floor(rnd()*(i+1));[times[i],times[j]]=[times[j],times[i]];}
  const data=[['目标采集时长',...Array.from({length:12},(_,i)=>[`道具${i+1}`,`道具${i+1}key`]).flat()]];
  rows.slice(1).forEach((r,i)=>{
    const names=r[1].split('、'),keys=r[2].split('、');
    if(names.length!==keys.length)throw Error('pair mismatch');
    data.push([times[i],...Array.from({length:12},(_,k)=>[names[k]??null,keys[k]??null]).flat()]);
  });
  s.getRange('A1:Y1130').values=data;
  s.getRange('A2:A1130').setNumberFormat('0.0');
  s.getRange('B1:Y1130').format.columnWidth=14;
  const actual=s.getRange('A1:Y1130').values;
  let mainCount=0;
  for(let i=1;i<actual.length;i++){
    const r=actual[i],t=r[0];
    if(typeof t!=='number'||t<0.1||t>9999.9||Math.abs(t*10-Math.round(t*10))>1e-8)throw Error('invalid duration');
    if(t>=1&&t<=100)mainCount++;
    const names=rows[i][1].split('、'),keys=rows[i][2].split('、');
    for(let k=0;k<12;k++)if(r[1+k*2] !== (names[k]??null)||r[2+k*2] !== (keys[k]??null))throw Error('pair verification failed');
  }
  console.log(JSON.stringify({rows:n,mainCount,mainPct:100*mainCount/n,min:Math.min(...times),max:Math.max(...times),pairs:12}));
  console.log((await wb.inspect({kind:'table',range:'Sheet1!A1:G6',tableMaxRows:6,tableMaxCols:7,maxChars:2200})).ndjson);
  console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:10},maxChars:1000})).ndjson);
  const im=await wb.render({sheetName:'Sheet1',range:'A1:I8',scale:1.5});
  await fs.writeFile(dir+'after.png',new Uint8Array(await im.arrayBuffer()));
  await (await SpreadsheetFile.exportXlsx(wb)).save(dir+'工作簿1_已修改.xlsx');
}
