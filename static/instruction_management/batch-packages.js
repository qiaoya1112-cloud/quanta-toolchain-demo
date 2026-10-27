var s026BatchRows=null,s026BatchResult=null,s026BatchRequest=0;
function s026OpenBatchPackages(){
 s026BatchRequest++;s026BatchRows=null;s026BatchResult=null;
 var body=`<div class="s026-upload-zone" id="s026BatchZone" ondragover="s026BatchDrag(event,true)" ondragleave="s026BatchDrag(event,false)" ondrop="s026BatchDrop(event)"><b id="s026BatchFileName">上传组包表格</b><span>支持 xlsx 格式，支持本地上传或拖拽上传；文件大小上限20M</span><input id="s026BatchFile" type="file" accept=".xlsx" onchange="s026ReadBatchFile(this.files[0])" hidden><div class="s026-upload-state" id="s026BatchFileState"></div><div><button class="s026-btn" onclick="document.getElementById('s026BatchFile').click()">选择本地文件</button> <button class="s026-btn danger" id="s026BatchDelete" hidden onclick="s026ResetBatchFile()">删除文件</button></div></div><div id="s026BatchSummary" role="status" style="margin-top:16px"></div><div id="s026BatchErrors" hidden style="margin-top:16px"><div style="display:flex;justify-content:space-between;align-items:center"><b>失败原因</b><button class="s026-btn" onclick="s026CopyBatchErrors()">复制失败原因</button></div><textarea id="s026BatchErrorText" aria-label="具体失败原因" readonly style="box-sizing:border-box;width:100%;min-height:160px;margin-top:10px;padding:12px;border:1px solid #e0e6e8;border-radius:6px;line-height:1.8"></textarea></div>`;
 var actions=`<button class="s026-btn" onclick="s026MockBatch(false)">Mock 校验成功</button><button class="s026-btn danger" onclick="s026MockBatch(true)">Mock 校验失败</button>`;
 s026OpenDrawer('批量创建指令包','<div class="s026-drawer-form">'+body+`<div class="s026-drawer-form-foot"><button class="s026-btn" onclick="s026CloseDrawer()">取消</button><button class="s026-btn primary" id="s026BatchCreate" disabled onclick="s026CreateBatchPackages()">创建并发布</button></div></div>`,actions);
}
function s026BatchDrag(event,active){event.preventDefault();document.getElementById('s026BatchZone').classList.toggle('dragging',active);}
function s026BatchDrop(event){s026BatchDrag(event,false);var file=event.dataTransfer&&event.dataTransfer.files[0];if(file)s026ReadBatchFile(file);}
function s026ResetBatchFile(){s026BatchRequest++;s026BatchRows=null;s026BatchResult=null;document.getElementById('s026BatchFile').value='';document.getElementById('s026BatchFileName').textContent='上传组包表格';document.getElementById('s026BatchFileState').textContent='';document.getElementById('s026BatchDelete').hidden=true;document.getElementById('s026BatchSummary').textContent='';document.getElementById('s026BatchErrors').hidden=true;document.getElementById('s026BatchCreate').disabled=true;}
function s026MockBatch(failed){
 s026ResetBatchFile();var rows=[],groups=new Map();
 s026State.library.filter(function(item){return item.status==='启用'&&item.scene&&item.zone;}).slice(0,6).forEach(function(item){var versions=item.versions.filter(function(version){return version.status==='启用';});if(!versions.length)return;var scope=item.scene+' / '+item.zone;if(!groups.has(scope))groups.set(scope,'MOCK'+String(groups.size+1).padStart(3,'0'));rows.push({line:rows.length+2,'指令包序号':groups.get(scope),'指令ID':item.id,'指令版本':versions[0].version,'指令包名称':'演示组包 · '+scope});});
 if(failed){rows.push({line:rows.length+2,'指令包序号':'MOCK-ERROR','指令ID':'MOCK-NOT-FOUND','指令版本':'V1','指令包名称':'异常示例包'});if(rows.length>1)rows.push(Object.assign({},rows[0],{line:rows.length+2}));}
 document.getElementById('s026BatchFileName').textContent=failed?'批量组包_校验失败示例.xlsx':'批量组包_校验成功示例.xlsx';document.getElementById('s026BatchFileState').textContent='Mock 演示文件';document.getElementById('s026BatchDelete').hidden=false;s026BatchRows=rows;s026RenderBatchResult(s026ValidateBatch(rows));
}
function s026ValidateBatch(rows){
 var groups=new Map(),errors=[];
 rows.forEach(function(row){var no=row['指令包序号'],id=row['指令ID'],version=row['指令版本'],name=row['指令包名称'],label='第 '+row.line+' 行';
 if(!no){errors.push(label+'：指令包序号为空');return;}
 if(!groups.has(no))groups.set(no,{no:no,name:name||'指令包 '+no,explicitName:name,keys:[],scene:'',zone:'',errors:[]});
 var group=groups.get(no);function fail(reason){group.errors.push(label+'（包 '+no+'）：'+reason);}
 if(name&&group.explicitName&&name!==group.explicitName)fail('同一包序号的指令包名称不一致');
 if(name&&!group.explicitName){group.name=name;group.explicitName=name;}
 if(group.name.length>100)fail('指令包名称不能超过 100 个字符');
 var instruction=s026State.library.find(function(item){return item.id===id;});
 if(!instruction){fail(id?'指令 '+id+' 不存在':'指令 ID 为空');return;}
 var enabled=instruction.versions.filter(function(item){return item.status==='启用';}).sort(function(a,b){return Number(b.version.replace(/^V/i,''))-Number(a.version.replace(/^V/i,''));});
 var selected=version?instruction.versions.find(function(item){return item.version.toLowerCase()===version.toLowerCase();}):enabled[0];
 if(!selected){fail(version?'指令 '+id+' 的版本 '+version+' 不存在':'指令 '+id+' 没有启用版本');return;}
 if(instruction.status!=='启用'||selected.status!=='启用'){fail('指令 '+id+' / '+selected.version+' 已停用，不能发布');return;}
 if(!instruction.scene||!instruction.zone){fail('指令 '+id+' 缺少场景或工作区');return;}
 var key=id+'-'+selected.version;
 if(group.keys.indexOf(key)>=0){fail('指令版本 '+key+' 在包内重复');return;}
 if(group.scene&&(group.scene!==instruction.scene||group.zone!==instruction.zone)){fail('包内指令的场景和工作区必须一致');return;}
 group.scene=instruction.scene;group.zone=instruction.zone;group.keys.push(key);
 });
 var packages=Array.from(groups.values());packages.forEach(function(group){errors=errors.concat(group.errors);});
 return {packages:packages,errors:errors,failed:packages.filter(function(group){return group.errors.length;}).length,unassigned:rows.filter(function(row){return !row['指令包序号'];}).length};
}
function s026RenderBatchResult(result){
 s026BatchResult=result;
 var failed=!!result.errors.length;
 document.getElementById('s026BatchFileState').textContent=failed?'上传失败':'上传成功';
 document.getElementById('s026BatchFileState').style.color=failed?'var(--red)':'var(--brand-dark)';
 document.getElementById('s026BatchSummary').innerHTML=failed?'':'<div class="s026-notice">共 <b>'+result.packages.length+'</b> 个指令包</div>';
 document.getElementById('s026BatchErrors').hidden=!failed;
 document.getElementById('s026BatchErrorText').value=result.errors.join('\n');
 document.getElementById('s026BatchCreate').disabled=failed||!result.packages.length;
}
async function s026ReadBatchFile(file){
 var token=++s026BatchRequest;s026BatchRows=null;s026BatchResult=null;document.getElementById('s026BatchCreate').disabled=true;document.getElementById('s026BatchErrors').hidden=true;
 document.getElementById('s026BatchFileName').textContent=file?file.name:'上传组包表格';document.getElementById('s026BatchDelete').hidden=!file;document.getElementById('s026BatchFileState').style.color='';document.getElementById('s026BatchFileState').textContent=file?'上传中…':'';var summary=document.getElementById('s026BatchSummary');summary.textContent='';
 try{if(!file)throw Error('请先选择 XLSX 文件');if(!/\.xlsx$/i.test(file.name))throw Error('仅支持 .xlsx 格式');if(file.size>20*1024*1024)throw Error('文件大小不能超过 20 MB');
 var body=new FormData();body.append('file',file);var response=await fetch('/data/instruction-packages/batch-parse',{method:'POST',body:body}),data=await response.json();if(token!==s026BatchRequest)return;if(!response.ok)throw Error(data.error||'读取失败');s026BatchRows=data.rows;s026RenderBatchResult(s026ValidateBatch(data.rows));
 }catch(error){if(token!==s026BatchRequest)return;document.getElementById('s026BatchFileState').textContent='上传失败';document.getElementById('s026BatchFileState').style.color='var(--red)';summary.textContent='';document.getElementById('s026BatchErrors').hidden=false;document.getElementById('s026BatchErrorText').value=error.message;}
}
async function s026CopyBatchErrors(){var field=document.getElementById('s026BatchErrorText');try{await navigator.clipboard.writeText(field.value);toast('失败原因已复制');}catch(error){field.focus();field.select();toast('已选中失败原因，可手动复制');}}
function s026CreateBatchPackages(){
 if(!s026BatchRows)return;var result=s026ValidateBatch(s026BatchRows);s026RenderBatchResult(result);if(result.errors.length||!result.packages.length)return;
 var now=s026Now(),stamp=Date.now().toString(),existing=new Set(s026State.packages.map(function(item){return item.id;}));
 var created=result.packages.map(function(group,index){var id='CIP'+stamp+String(index+1).padStart(4,'0');while(existing.has(id))id+='1';existing.add(id);return {id:id,name:group.name,scene:group.scene,zone:group.zone,status:'上线',configured:true,keys:group.keys.slice(),creator:'当前演示用户',created:now,updated:now,published:now,sourceBatch:stamp,sourcePackageNo:group.no};});
 var before=s026State.packages;s026State.packages=created.concat(before);
 try{s026SyncAllProjectMetrics();localStorage.setItem(S026_STORAGE_KEY,JSON.stringify(s026State));}catch(error){s026State.packages=before;toast('保存失败，未创建指令包，请检查浏览器存储空间后重试');return;}
 s026BatchRows=null;s026BatchResult=null;s026BatchRequest++;s026CloseDrawer();s026RenderAll();toast('已创建并发布 '+created.length+' 个指令包');
}
