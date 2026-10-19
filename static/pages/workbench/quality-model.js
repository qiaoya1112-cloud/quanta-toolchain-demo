(function(root){
  const mistakes=['夹爪超出画面','手部脱离夹爪','其他身体部位辅助','无意义动作或假动作','可用时长太短','重复尝试次数过多','操作过程中物品掉落','抓取位置偏移','动作执行不连贯','任务结束后多余操作','目标物体摆放偏差','动作速度不稳定'];
  const failures=['视频损坏或相机卡死','采集时长不足','画面全程完全遮挡','设备穿戴不规范','关键操作过程缺失','视频与采集任务不符','关键视角缺失','多视角时间不同步','画面严重模糊','采集过程异常中断','任务未完成','设备数据缺失'];
  const complete=item=>(item.type==='failure'?item.failures:item.mistakes).length>0;
  function changeType(item,type){item.type=type;if(type==='mistake')item.failures=[];}
  function lanes(items){
    const tracks=[[],[],[]],result=new Map();
    items.filter(item=>Number.isInteger(item.lane)&&item.lane>=0&&item.lane<3).forEach(item=>{
      tracks[item.lane].push(item);result.set(item.id,item.lane);
    });
    items.filter(item=>!result.has(item.id)).sort((a,b)=>a.start-b.start||a.end-b.end||a.id.localeCompare(b.id)).forEach(item=>{
      const scores=tracks.map(track=>track.reduce((sum,other)=>sum+Math.max(0,Math.min(item.end,other.end)-Math.max(item.start,other.start)),0));
      const lane=scores.indexOf(Math.min(...scores));tracks[lane].push(item);result.set(item.id,lane);
    });return result;
  }
  const conclusion=items=>items.some(item=>item.type==='failure')?'不合格':'合格';
  const api={mistakes,failures,complete,changeType,lanes,conclusion};
  if(typeof module!=='undefined')module.exports=api;else root.QualityModel=api;
})(globalThis);
