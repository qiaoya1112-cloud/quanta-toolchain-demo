const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const registry = new Map(), storage = new Map(), events = [];
class HTMLElement {}
class CustomEvent {constructor(type, options={}) {this.type=type;this.detail=options.detail;}}
const context = vm.createContext({HTMLElement, CustomEvent, window:{confirm:()=>true},
  document:{addEventListener(){},dispatchEvent(event){events.push(event.type);},querySelector(){return null;}},
  localStorage:{getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value),removeItem:key=>storage.delete(key)},
  customElements:{define(name, type){assert.ok(!registry.has(name));registry.set(name,type);}}
});
for (const name of ['post', 'pre']) vm.runInContext(fs.readFileSync(`static/annotation_workbench/${name}-training-quality.js`,'utf8'), context);
const pre=context.window.PreTrainingQualityDemo, post=context.window.PostTrainingQualityDemo;
assert.notEqual(pre.state, post.state);
assert.equal(registry.size,6);
assert.notEqual(registry.get('pre-training-quality-workspace'), registry.get('post-training-quality-workspace'));
pre.state.rangeStart=30;pre.state.rangeEnd=32;pre.addSegment();
assert.equal(pre.state.segments.length,9);
assert.equal(post.state.segments.length,8);
assert.ok(events.every(name=>name.startsWith('pre-quality-')), '预训练操作只通知预训练组件');
for(const [name,demo,prefix] of [['pre',pre,'prq'],['post',post,'ptq']]) {
  const sidebar = new (registry.get(`${name}-training-quality-sidebar`))();
  sidebar.render=()=>{};sidebar.toast=()=>{};
  let opened='';
  const fields={};
  sidebar.querySelector = selector=>({showModal(){opened=selector;},querySelector:field=>(fields[field]??={}),close(){}});
  const click=action=>sidebar.onClick({target:{closest:selector=>selector==='[data-action]'?{dataset:{action}}:null}});
  click('submit');
  assert.equal(opened,`#${prefix}ErrorDialog`,'未完善的片段仍阻止提交');
  demo.state.segments = [{id:'valid',start:1,end:3,conclusion:'mistake',mistakeReasons:['M01'],rejectedReasons:[],reviewErrorReason:'片段范围错误',order:1,track:0}];
  click('submit');
  assert.equal(opened,`#${prefix}SubmitDialog`,'完整片段可直接提交，无需完成检查复选框');
  assert.equal(sidebar.save(),true);
}
assert.equal(storage.size,2,'两个工作台分别保存草稿');
for(const [name,script] of [['pre','pre'],['post','post']]) {
  const css = fs.readFileSync(`static/annotation_workbench/${script}-training-quality.css`,'utf8');
  assert.ok(css.includes(`${name}-training-quality-workspace`));
  assert.ok(!css.includes(`${name==='pre'?'post':'pre'}-training-quality-workspace`),'样式分别维护');
}
console.log('Independent quality components: separate state, events, drafts, styles and submission validation passed');
