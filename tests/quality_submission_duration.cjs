const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
for(const mode of ['pre','post']){
 const registry=new Map(),storage=new Map();
 class HTMLElement{};class CustomEvent{constructor(type,options){this.type=type;this.detail=options.detail;}}
 const context=vm.createContext({HTMLElement,CustomEvent,window:{},document:{querySelector(){return null;},addEventListener(){},dispatchEvent(){}},customElements:{define(n,t){registry.set(n,t);}},localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)}});
 vm.runInContext(fs.readFileSync(`static/annotation_workbench/${mode}-training-quality.js`,'utf8'),context);
 const rules=context.window[`__${mode}TrainingQualityRules`],demo=context.window[`${mode==='pre'?'Pre':'Post'}TrainingQualityDemo`];
 const problem=(start,end)=>({id:`P${start}`,start,end,conclusion:'rejected',mistakeReasons:[],rejectedReasons:['U01'],reviewErrorReason:'片段范围错误',order:start,track:0});
 if(mode==='pre'){
 demo.state.segments=[problem(1,8),problem(9.4,10.8),problem(12,22.5)];
 assert.equal(rules.pendingCount(),0);
 assert.equal(rules.validateUsableDuration(),3);
 const autos=demo.state.segments.filter(r=>r.autoShortDuration);
 assert.deepEqual(Array.from(autos,r=>[r.start,r.end]),[[0,1],[8,9.4],[10.8,12]]);
 assert.ok(autos.every(r=>rules.isShortDuration(r)&&rules.segmentErrors(r).length===0));
 assert.equal(rules.validateUsableDuration(),3,'再次提交按当前时间重算，不重复添加');assert.equal(demo.state.segments.length,6);
 demo.state.segments=[problem(3,37)];assert.equal(rules.validateUsableDuration(),0,'恰好3秒保留为合格');
 demo.state.segments=[];assert.equal(rules.validateUsableDuration(),0,'整段合格无需新增问题');
 demo.state.segments=[problem(0,40)];assert.equal(rules.validateUsableDuration(),0,'没有可用片段时无空片段');
 demo.state.segments=[problem(1,5),problem(4,8)];assert.equal(rules.validateUsableDuration(),1,'重叠问题取并集');
 }else{assert.equal(rules.validateUsableDuration,undefined,'后训练不进行短片段校验');}
 const sidebar=new (registry.get(`${mode}-training-quality-sidebar`))();sidebar.render=()=>{};sidebar.toast=()=>{};
 let opened='';const fields={};sidebar.querySelector=selector=>({showModal(){opened=selector;},close(){},querySelector:field=>(fields[field]??={})});
 const click=action=>sidebar.onClick({target:{closest:selector=>selector==='[data-action]'?{dataset:{action}}:null}});
 demo.state.segments=[{...problem(1,5),conclusion:'mistake',mistakeReasons:[],rejectedReasons:[]}];click('submit');assert.match(opened,/ErrorDialog/,'默认失误但缺少失误原因时应阻止提交');
 demo.state.segments=[{...problem(1,5),reviewErrorReason:''}];assert.equal(rules.pendingCount(),0);click('submit');assert.match(opened,/ErrorDialog/,'缺少审核错误原因时仍应阻止提交');
 demo.state.segments=[problem(1,5)];click('submit');assert.match(opened,/SubmitDialog/);if(mode==='pre')assert.match(fields['[data-duration-check]'].textContent,/1 处可用片段不足 3 秒/);else assert.equal(demo.state.segments.length,1);
 sidebar.save();const saved=JSON.parse([...storage.values()][0]);assert.equal(saved.segments.filter(r=>r.autoShortDuration).length,mode==='pre'?1:0);
 click('confirm-submit');assert.equal(demo.state.submitted,true);
 const markup=fs.readFileSync(`static/annotation_workbench/${mode}-training-quality.js`,'utf8');assert.ok(!markup.includes('待完善'));assert.ok(!markup.includes('save-state'));assert.ok(!markup.includes("['pending','待判定']"));
}
console.log('Quality submissions: common validation, pre-training-only short duration, strict 3s boundary, idempotence and confirmation passed');
