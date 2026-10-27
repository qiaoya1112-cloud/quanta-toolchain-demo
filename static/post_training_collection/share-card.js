/* Plain-text handoff. Requirements are excerpted verbatim, never summarized. */
(() => {
  function model(task, context) {
    const description = String(task.description || '').replace(/\s+/g, ' ').trim();
    const characters = Array.from(description);
    const excerpted = characters.length > 100;
    return {id:task.id,name:task.name,priority:task.priority??6,expected_hours:task.expected_hours??null,project:context.project,mode:task.source==='udas'?'UDAS':context.mode,closed:task.status!=='open',location:task.location||'',description:excerpted?characters.slice(0,100).join('')+'…':description,excerpted,link:context.link,spec:task.spec_url||''};
  }
  function text(card) {
    card={...card,priority:card.priority>=7?'高':card.priority>=4?'中':'低'};
    return [card.name,'',`任务 ID：${card.id}`,`所属项目：${card.project} · ${card.mode}`,`优先级：${card.priority}`,...(card.expected_hours!=null?[`预期采集时长：${card.expected_hours} 小时`]:[]),...(card.location?[`采集地点：${card.location}`]:[]),...(card.closed?['采集状态：已结束采集，请勿开始新录制']:[]),'',card.excerpted?'采集要求（节选）':'采集要求',card.description||'见任务详情。',...(card.excerpted?['','完整采集要求请查看任务详情。']:[]),'',...(card.spec?[`采集规范：${card.spec}`]:[]),`任务详情：${card.link}`].join('\n');
  }
  window.DCShareCard={model,text};
})();
