const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
for(const mode of ['pre','post']){
 const registry=new Map(),storage=new Map();
 class HTMLElement{};class CustomEvent{constructor(type,options){this.type=type;this.detail=options.detail;}}
 const context=vm.createContext({HTMLElement,CustomEvent,window:{},document:{querySelector(){return null;},addEventListener(){},dispatchEvent(){}},customElements:{define(n,t){registry.set(n,t);}},localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)}});
 vm.runInContext(fs.readFileSync(`static/annotation_workbench/${mode}-training-quality.js`,'utf8'),context);
 const rules=context.window[`__${mode}TrainingQualityRules`],demo=context.window[`${mode==='pre'?'Pre':'Post'}TrainingQualityDemo`];
 const problem=(start,end)=>({id:`P${start}`,start,end,conclusion:'rejected',mistakeReasons:[],rejectedReasons:['U01'],reviewErrorReason:'片段范围错误',order:start,track:0});
 if(mode==='pre'){
 const mistake=(start,end)=>({...problem(start,end),conclusion:'mistake',rejectedReasons:[],mistakeReasons:['M05']});
 assert.equal(rules.calculateConclusion([mistake(0,20)],true),'不合格','50%边界');
 assert.equal(rules.calculateConclusion([mistake(0,10),mistake(5,15)],true),'失误','重叠时长不重复计入');
 demo.state.segments=[problem(1,8),problem(9.4,10.8),problem(12,22.5)];
 assert.equal(rules.pendingCount(),0);
 assert.equal(rules.validateUsableDuration(),3);
 const autos=demo.state.segments.filter(r=>r.autoShortDuration);
 assert.deepEqual(Array.from(autos,r=>[r.start,r.end]),[[0,1],[8,9.4],[10.8,12]]);
 assert.ok(autos.every(r=>rules.isShortDuration(r)&&rules.segmentErrors(r).length===0));
 assert.equal(rules.visibleSegments().length,3,'系统自动标记不显示在质检列表');
 demo.selectSegment(autos[0].id);assert.equal(demo.state.selectedId,autos[0].id,'特殊片段支持点击查看');
 const original=autos[0].start;demo.updateTime(autos[0].id,'start',original+.5);assert.equal(autos[0].start,original,'系统自动标记不支持调整');
 assert.equal(rules.validateUsableDuration(),3,'再次提交按当前时间重算，不重复添加');assert.equal(demo.state.segments.length,6);
 demo.state.segments=[problem(3,37)];assert.equal(rules.validateUsableDuration(),0,'恰好3秒保留为合格');
 demo.state.segments=[problem(1,8)];rules.validateUsableDuration();demo.updateTime('P1','start',3);assert.equal(demo.state.segments.filter(r=>r.autoShortDuration).length,0,'调整后实时移除已达到3秒的自动片段');demo.updateTime('P1','start',1);assert.equal(demo.state.segments.filter(r=>r.autoShortDuration).length,1,'调整后实时生成短片段');
 demo.state.segments=[];assert.equal(rules.validateUsableDuration(),0,'整段合格无需新增问题');
 demo.state.segments=[problem(0,40)];assert.equal(rules.validateUsableDuration(),0,'没有可用片段时无空片段');
 demo.state.segments=[problem(1,5),problem(4,8)];assert.equal(rules.validateUsableDuration(),1,'重叠问题取并集');
 }else{assert.equal(rules.validateUsableDuration,undefined,'后训练不进行短片段校验');}
 const sidebar=new (registry.get(`${mode}-training-quality-sidebar`))();sidebar.render=()=>{};sidebar.toast=()=>{};
 let opened='';const fields={};sidebar.querySelector=selector=>({showModal(){opened=selector;},close(){},querySelector:field=>(fields[field]??={})});
 const click=action=>sidebar.onClick({target:{closest:selector=>selector==='[data-action]'?{dataset:{action}}:null}});
 demo.state.segments=[{...problem(1,5),conclusion:'mistake',mistakeReasons:[],rejectedReasons:[]}];click('submit');assert.match(opened,/ErrorDialog/,'默认失误但缺少失误原因时应阻止提交');
 demo.state.segments=[{...problem(1,5),reviewErrorReason:''}];assert.equal(rules.pendingCount(),0);opened='';click('submit');assert.match(opened,/SubmitDialog/,`${mode} 训练审核错误原因选填，不应阻止提交`);
 demo.state.segments=[problem(1,5)];click('submit');assert.match(opened,/SubmitDialog/);if(mode==='pre')assert.match(fields['[data-duration-check]'].textContent,/1 处可用片段不足 3 秒/);else assert.equal(demo.state.segments.length,1);
 if(mode==='pre'){click('save');assert.equal(demo.state.segments.filter(r=>r.autoShortDuration).length,1,'保存时重新判定短片段');}
 sidebar.save();const saved=JSON.parse([...storage.values()][0]);assert.equal(saved.segments.filter(r=>r.autoShortDuration).length,mode==='pre'?1:0);
 click('confirm-submit');assert.equal(demo.state.submitted,true);
 if(mode==='pre'){
  demo.state.submitted=false;opened='';click('leave');assert.match(opened,/ReleaseDialog/,'释放前应二次确认');
  click('confirm-release');assert.equal(demo.state.submitted,true);assert.match(opened,/SuccessDialog/,'释放成功后显示不可关闭的操作结果弹窗');
 }
 const markup=fs.readFileSync(`static/annotation_workbench/${mode}-training-quality.js`,'utf8');assert.ok(!markup.includes('待完善'));assert.ok(!markup.includes('save-state'));assert.ok(!markup.includes("['pending','待判定']"));
 if(mode==='pre'){assert.match(markup,/SuccessDialog/);assert.match(markup,/confirm-release/);}
}
console.log('Quality submissions: common validation, pre-training-only short duration, strict 3s boundary, idempotence and confirmation passed');
