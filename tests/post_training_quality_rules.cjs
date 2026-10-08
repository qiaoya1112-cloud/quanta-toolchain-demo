const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class HTMLElement {}
const document = {addEventListener(){},dispatchEvent(){},querySelector(){return null;}};
const localStorage = {getItem(){return null;},setItem(){},removeItem(){}};
const customElements = {define(){}};
class CustomEvent {constructor(type,options={}){this.type=type;this.detail=options.detail;}}
const window = {confirm(){return true;}};
const context = {console,document,localStorage,customElements,CustomEvent,HTMLElement,window};
vm.createContext(context);
vm.runInContext(fs.readFileSync('static/annotation_workbench/post-training-quality.js','utf8'),context);

const rules=context.window.__postTrainingQualityRules;
assert.ok(rules,'应导出后训练质检规则');
assert.equal(rules.constants.trackCount,3);

const validMistake={id:'M',start:1,end:5,conclusion:'mistake',mistakeReasons:['M01'],rejectedReasons:[],reviewErrorReason:'动作不符合要求',order:1};
assert.deepEqual(Array.from(rules.segmentErrors(validMistake)),[]);
assert.match(rules.segmentErrors({...validMistake,mistakeReasons:[]})[0],/失误原因/);
assert.match(rules.segmentErrors({...validMistake,rejectedReasons:['U01']})[0],/移除不合格原因/);
assert.match(rules.segmentErrors({...validMistake,reviewErrorReason:''})[0],/错误原因/);

const validRejected={id:'R',start:3,end:8,conclusion:'rejected',mistakeReasons:['M02'],rejectedReasons:['U01'],reviewErrorReason:'视频不可用',order:2};
assert.deepEqual(Array.from(rules.segmentErrors(validRejected)),[]);
assert.match(rules.segmentErrors({...validRejected,rejectedReasons:[]})[0],/不合格原因/);
assert.match(rules.segmentErrors({...validRejected,start:8,end:8})[0],/时间不合法/);

assert.equal(rules.overlapDuration({start:1,end:5},{start:5,end:8}),0,'首尾相接不算重合');
assert.equal(rules.overlapDuration({start:1,end:6},{start:4,end:8}),2);

const trackOneOccupied=[{id:'A',start:1,end:5,track:0}];
assert.equal(rules.placeSegment({id:'B',start:2,end:4},trackOneOccupied).track,1,'轨道1重合时应选择第一条无重合轨道');
assert.equal(rules.placeSegment({id:'B',start:5,end:7},trackOneOccupied).track,0,'首尾相接时轨道1可用');

const allOccupied=[
  {id:'A',start:0,end:8,track:0},
  {id:'B',start:3,end:4,track:1},
  {id:'C',start:1,end:3,track:2}
];
const leastOverlap=rules.placeSegment({id:'D',start:1,end:5},allOccupied);
assert.equal(leastOverlap.track,1,'三轨均重合时应选择重合总时长最小的轨道');
assert.equal('clustered' in leastOverlap,false,'新规则不应生成聚合状态');

const tied=[
  {id:'A',start:1,end:3,track:0},
  {id:'B',start:2,end:4,track:1},
  {id:'C',start:3,end:5,track:2}
];
assert.equal(rules.placeSegment({id:'D',start:2,end:4},tied).track,0,'重合总时长并列时选择编号更小的轨道');

assert.equal(rules.calculateConclusion([validMistake,validRejected],true),'不合格');
assert.equal(rules.calculateConclusion([validMistake],true),'失误');
assert.equal(rules.calculateConclusion([],false),'待计算');
assert.equal(rules.calculateConclusion([],true),'合格');
assert.equal(rules.calculateConclusion([{...validMistake,conclusion:'pending',mistakeReasons:[]}],true),'待计算');

const sorted=rules.sortSegments([
  {id:'3',start:2,end:4,order:1},
  {id:'2',start:1,end:4,order:3},
  {id:'1',start:1,end:3,order:2}
]);
assert.deepEqual(Array.from(sorted,item=>item.id),['1','2','3']);

console.log('post-training quality rules: passed');
