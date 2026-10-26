const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../static/eval_catalog/catalog.js'),'utf8');
const code=source.slice(source.indexOf('let importBusy='),source.indexOf("if($('ec-import')){"));

function environment(){
 const elements={},tasks=[],messages=[],storage=new Map();let sequence=0,failUpload=false,catalogLoads=0;
 const element=id=>elements[id]??={hidden:false,disabled:false,value:id==='ec-import-duplicate-mode'?'skip':'',style:{},classList:{contains:()=>true}};
 Object.defineProperty(element('ec-import-file-state'),'textContent',{get(){return messages.at(-1)||'';},set(value){messages.push(value);}});
 const response=value=>({ok:true,status:200,json:async()=>structuredClone(value)});
 const context={$,console,crypto:{randomUUID:()=>`request-${++sequence}`},AbortSignal:{timeout:()=>null},
  setTimeout:()=>1,clearTimeout:()=>{},catalogNamespace:'test-user',catalogReady:Promise.resolve(true),
  sessionStorage:{setItem:(k,v)=>storage.set(k,v),getItem:k=>storage.get(k),removeItem:k=>storage.delete(k)},
  FormData:class{append(){}},esc:value=>String(value??'').replaceAll('<','&lt;').replaceAll('>','&gt;'),
  loadServerCatalog:async()=>{catalogLoads++;},
  fetch:async(url,options={})=>{
   if(url.endsWith('/jobs')&&options.method==='POST'){
    const payload=JSON.parse(options.body);let task=tasks.find(item=>item.key===payload.request_key);
    if(!task){task={id:`job-${tasks.length+1}`,key:payload.request_key,filename:payload.filename,submitted_at:'2026-10-27 12:00:00',status:'uploading',has_report:false,download_url:null};tasks.unshift(task);}
    else if(task.status==='upload_failed')task.status='uploading';
    return response(task);
   }
   if(url.includes('/jobs?page='))return response({items:tasks,total:tasks.length});
   const task=tasks.find(item=>url.includes('/jobs/'+item.id));assert(task,url);
   if(url.endsWith('/upload')){if(task.status==='uploading'){task.status='upload_failed';task.message='网络中断，请重试。';}return response(task);}
   return response(task);
  },
  XMLHttpRequest:class{
   constructor(){this.upload={};}
   open(method,url){this.url=url;}
   send(){queueMicrotask(()=>{
    this.upload.onprogress({lengthComputable:true,loaded:50,total:100});
    if(failUpload){this.onerror();return;}
    this.upload.onload();const task=tasks.find(item=>this.url.includes('/jobs/'+item.id));
    task.status='validating';task.download_url='/file/'+task.id;this.responseText=JSON.stringify(task);this.onload();
   });}
  }
 };
 function $(id){return element(id);}
 vm.createContext(context);vm.runInContext(code,context);
 return {context,tasks,elements,messages,storage,setFailure:value=>{failUpload=value;},catalogLoads:()=>catalogLoads,get:expr=>vm.runInContext(expr,context)};
}

(async()=>{
 const env=environment(),file={name:'cases.xlsx',size:1024};
 const pending=env.context.selectImportFile(file);
 assert.equal(env.get('importTask.status'),'uploading','Selecting a file immediately starts upload');
 assert(env.elements['ec-import-choose'].disabled);
 await pending;
 assert(env.messages.includes('上传中 50%'),'Progress reflects transferred bytes');
 assert.equal(env.get('importTask.status'),'validating');
 assert(env.elements['ec-import-history-body'].innerHTML.includes('校验中'));
 env.tasks[0].status='importing';await env.context.pollImport();
 assert(env.elements['ec-import-history-body'].innerHTML.includes('导入中'));
 env.tasks[0].status='success';await env.context.pollImport();
 assert(env.elements['ec-import-history-body'].innerHTML.includes('导入成功'));
 assert.equal(env.catalogLoads(),1);assert(!env.elements['ec-import-choose'].disabled);
 assert(env.elements['ec-import-submit'].hidden);
 const failed=environment();failed.setFailure(true);await failed.context.selectImportFile(file);
 assert.equal(failed.get('importTask.status'),'upload_failed');
 assert.equal(failed.elements['ec-import-submit'].textContent,'重试上传');
 assert(!failed.elements['ec-import-submit'].disabled);
 assert(failed.elements['ec-import-history-body'].innerHTML.includes('网络中断，请重试。'));
 failed.setFailure(false);await failed.context.submitImport();
 assert.equal(failed.tasks.length,1,'Retry reuses the reserved task');
 assert.equal(failed.get('importTask.status'),'validating');
 failed.tasks[0].status='validation_failed';failed.tasks[0].has_report=true;failed.tasks[0].message='prompt_CN 必填';
 await failed.context.pollImport();
 assert(failed.elements['ec-import-history-body'].innerHTML.includes('下载错误文件'));
 assert.equal(failed.elements['ec-import-submit'].textContent,'重新上传');
 await failed.context.submitImport();assert.equal(failed.tasks.length,2,'Revalidation creates a new historical record');
 failed.tasks[0].status='import_failed';failed.tasks[0].message='写入冲突';await failed.context.pollImport();
 assert(failed.elements['ec-import-history-body'].innerHTML.includes('导入失败'));
 const labels=env.get('Object.values(importStates).map(item=>item[0])');
 for(const label of ['上传中','上传失败','校验中','校验失败','导入中','导入成功','导入失败'])assert(labels.includes(label));
 console.log('PASS: auto-upload, real progress, seven stage labels, failure records, retry idempotency, and automatic completion.');
})().catch(error=>{console.error(error);process.exitCode=1;});
