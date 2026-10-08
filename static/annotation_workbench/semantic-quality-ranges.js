(() => {
  const merge = (ranges, duration = 100) => {
    const ordered = ranges.filter(r => Number.isFinite(r.start) && Number.isFinite(r.end) && r.end > r.start)
      .map(r => ({start:Math.max(0,r.start),end:Math.min(duration,r.end)})).filter(r=>r.end>r.start).sort((a,b)=>a.start-b.start);
    const result=[];
    for(const range of ordered){const last=result.at(-1);if(last&&range.start<=last.end)last.end=Math.max(last.end,range.end);else result.push({...range});}
    return result;
  };
  const contains = (ranges, point) => ranges.some(r=>point>r.start&&point<r.end);
  const overlaps = (ranges, start, end) => ranges.some(r=>start<r.end&&end>r.start);
  function clip(ranges,start,end){
    if(end<=start)return '';
    const holes=merge(ranges).filter(r=>r.start<end&&r.end>start);
    if(!holes.length)return '';
    const points=['0% 0%'];
    for(const r of holes){const left=Math.max(0,(r.start-start)/(end-start)*100),right=Math.min(100,(r.end-start)/(end-start)*100);points.push(`${left}% 0%`,`${left}% 100%`,`${right}% 100%`,`${right}% 0%`);}
    points.push('100% 0%','100% 100%','0% 100%');
    return `polygon(evenodd, ${points.join(', ')})`;
  }
  const api={merge,contains,overlaps,clip};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else window.WorkbenchQualityRanges=api;
})();
