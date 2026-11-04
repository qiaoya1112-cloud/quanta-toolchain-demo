/* Version browsing, direct publishing and complete copies share the existing form. */
function installRuleVersionEditor() {
  const drawer = document.getElementById('drawerRuleCreate');
  if (!drawer || drawer.dataset.versionsReady) return;
  drawer.dataset.versionsReady = 'true';
  const $ = id => document.getElementById(id), esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let current, busy = false;
  const panel = document.createElement('section'); panel.id = 'ruleVersionPanel'; panel.hidden = true;
  drawer.querySelector('.drawer-body').prepend(panel);
  const records=document.createElement('dialog');records.id='ruleRecordsDialog';records.className='rule-records-dialog';
  records.setAttribute('aria-labelledby','ruleRecordsTitle');document.body.append(records);
  let recordsTrigger;
  const closeRecords=()=>{if(records.open)records.close();};
  records.addEventListener('click',event=>{
    if(event.target.closest('[data-close-rule-records]'))closeRecords();
    const tab=event.target.closest('[data-rule-record-tab]');
    if(tab)switchRecords(tab.dataset.ruleRecordTab);
    if(event.target===records){const r=records.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closeRecords();}
  });
  records.addEventListener('close',()=>{if(recordsTrigger?.isConnected&&drawer.classList.contains('active'))recordsTrigger.focus();});
  records.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();closeRecords();}},true);
  records.addEventListener('cancel',event=>{event.preventDefault();closeRecords();});
  function switchRecords(tab){
    records.querySelectorAll('[data-rule-record-tab]').forEach(button=>{const active=button.dataset.ruleRecordTab===tab;button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1;});
    records.querySelectorAll('[data-rule-record-pane]').forEach(pane=>pane.hidden=pane.dataset.ruleRecordPane!==tab);
  }
  records.addEventListener('keydown',event=>{
    const tab=event.target.closest('[data-rule-record-tab]');if(!tab||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    event.preventDefault();const target=event.key==='Home'?'versions':event.key==='End'?'events':tab.dataset.ruleRecordTab==='versions'?'events':'versions';
    switchRecords(target);records.querySelector('[data-rule-record-tab="'+target+'"]').focus();
  });
  function openRecords(tab,trigger){recordsTrigger=trigger;switchRecords(tab);records.showModal();records.querySelector('[aria-selected="true"]').focus();}
  const originalCreate = window.openRuleCreate;
  const originalDetail = window.openRuleDetail;
  window.ruleOpenMenu = function(trigger) {
    const menu=trigger.nextElementSibling,rect=trigger.getBoundingClientRect();
    menu.showPopover();menu.style.left=Math.min(rect.right-menu.offsetWidth,innerWidth-menu.offsetWidth-12)+'px';
    menu.style.top=(rect.bottom+menu.offsetHeight>innerHeight?rect.top-menu.offsetHeight:rect.bottom+5)+'px';
  };
  document.addEventListener('click',e=>e.target.closest('.rule-overflow-menu a')?.closest('[popover]')?.hidePopover());
  function lockIdentity(locked) {
    ['ruleCreateName','ruleCreateProject','ruleCreateStage','ruleCreateType'].forEach(id => $(id).disabled = locked);
  }
  function applyContent(data, readonly) {
    ruleApplyDetailContent(data,readonly); lockIdentity(readonly || (drawer.dataset.mode !== 'new' && !!current?.versions.length));
    window.ruleMarkClean?.();
  }
  function editMode() {
    closeRecords();
    drawer.dataset.mode = 'edit';
    drawer.dataset.ruleId = current.id; drawer.dataset.revision = current.revision;
    $('ruleEditorTitle').textContent = '编辑规则';
    applyContent(current.draft || current, false);
    panel.hidden = true;
    panel.innerHTML='';
    ruleRefreshPermissions();
  }
  function showVersion(number) {
    const selected = current.versions.find(v => v.number === Number(number));
    if (!selected) return;
    const latest = selected.number === current.versions.at(-1)?.number;
    applyContent(selected.content, true);
    panel.querySelectorAll('select,button').forEach(control=>control.disabled=false);
    $('ruleHistoryVersion').textContent = 'V'+selected.number;
    $('ruleVersionState').textContent = latest ? '当前发布' : '历史版本';
    $('ruleVersionState').classList.toggle('is-current', latest);
    $('ruleVersionMeta').innerHTML = [
      selected.published_by ? '<span><b>发布人</b>'+esc(selected.published_by)+'</span>' : '',
      selected.published_at ? '<span><b>发布时间</b>'+esc(selected.published_at)+'</span>' : '<span><b>发布时间</b>未记录</span>'
    ].filter(Boolean).join('');
    $('ruleVersionMeta').title = $('ruleVersionMeta').textContent;
  }
  function renderHistory() {
    closeRecords();panel.hidden=false;
    panel.innerHTML='<div class="rule-version-toolbar"><div class="rule-version-picker"><span>版本</span><b id="ruleHistoryVersion"></b><span class="rule-version-state" id="ruleVersionState"></span></div><div id="ruleVersionMeta"></div><div class="rule-record-actions">'+
      '<button type="button" data-open-rule-records="versions">版本记录<span>'+current.versions.length+'</span></button><button type="button" data-open-rule-records="events">操作记录</button></div></div>';
    records.innerHTML='<header><div><h3 id="ruleRecordsTitle">规则记录</h3><p>'+esc(current.name)+'</p></div><button type="button" data-close-rule-records aria-label="关闭规则记录">×</button></header>'+
      '<div class="rule-record-tabs" role="tablist" aria-label="记录类型"><button id="ruleRecordsVersionsTab" type="button" role="tab" data-rule-record-tab="versions" aria-controls="ruleRecordsVersions">版本记录 <span>'+current.versions.length+'</span></button>'+
      '<button id="ruleRecordsEventsTab" type="button" role="tab" data-rule-record-tab="events" aria-controls="ruleRecordsEvents">操作记录 <span>'+current.events.length+'</span></button></div><div class="rule-record-body">'+
      '<section id="ruleRecordsVersions" role="tabpanel" aria-labelledby="ruleRecordsVersionsTab" data-rule-record-pane="versions"><div class="rule-version-table-wrap"><table class="rule-version-table"><thead><tr><th>版本</th><th>状态</th><th>发布人</th><th>发布时间</th></tr></thead><tbody>'+
      [...current.versions].reverse().map(v=>'<tr><td>V'+v.number+'</td><td>'+
        (v.number===current.versions.at(-1).number?'<span class="rule-version-current-label">当前发布</span>':'<span class="rule-version-history-label">历史版本</span>')+'</td><td>'+esc(v.published_by||'-')+'</td><td>'+esc(v.published_at||'未记录')+'</td></tr>').join('')+
      '</tbody></table></div></section><section id="ruleRecordsEvents" role="tabpanel" aria-labelledby="ruleRecordsEventsTab" data-rule-record-pane="events"><div class="rule-history-event-list">'+[...current.events].reverse().map(e=>
        '<div class="rule-history-event"><i></i><div><b>'+esc(e.action)+(e.version?' · '+esc(e.version.toUpperCase()):'')+'</b><span>'+esc(e.actor)+' · '+esc(e.at)+'</span>'+
        (e.changes?.length?'<p>'+esc(e.changes.join('；'))+'</p>':'')+'</div></div>').join('')+
      (!current.events.length?'<p class="rule-history-empty">暂无操作记录</p>':'')+'</div></section></div><footer><button type="button" class="btn" data-close-rule-records>关闭</button></footer>';
    panel.querySelectorAll('[data-open-rule-records]').forEach(button=>button.onclick=()=>openRecords(button.dataset.openRuleRecords,button));
    showVersion(current.versions.at(-1).number);
  }
  async function load(trigger) {
    if (busy) return;
    busy = true;
    try {
      const response = await fetch('/api/processing-rules/'+encodeURIComponent(trigger.dataset.ruleId),{cache:'no-store'});
      const data = await response.json(); if (!response.ok) throw Error(data.error || '规则读取失败');
      current = {...data.rule, permissions:data.permissions};
      RULE_DETAIL_DATA[current.id] = {...current, document_link:current.rule_config || ''};
      return current;
    } catch(e) { toast(e.message); } finally { busy = false; }
  }
  window.openRuleCreate = function() {
    closeRecords();originalCreate(); current = null; panel.hidden = true;
    drawer.dataset.revision = '0'; lockIdentity(false);
  };
  window.openRuleDetail = async function(trigger, editable) {
    const rule = await load(trigger); if (!rule) return;
    if (editable===false && rule.versions.length) {toast('已发布规则不可编辑，请复制创建新规则');return;}
    if (editable===false&&!rule.permissions.edit) {toast('没有编辑规则权限');return;}
    originalDetail(trigger, editable);
    drawer.dataset.revision = rule.revision;
    if (editable === false) { editMode(); return; }
    $('ruleEditorTitle').textContent = '规则详情';
    if (rule.versions.length) renderHistory(); else { panel.hidden = true; applyContent(rule.draft || rule,true); }
  };
  window.ruleUpdate = async function(trigger) {
    const rule = await load(trigger); if (!rule) return;
    if (rule.versions.length) {toast('已发布规则不可编辑，请复制创建新规则');return;}
    if (!rule.permissions.edit) {toast('没有编辑规则权限');return;}
    originalDetail(trigger, false); editMode();
  };
  window.ruleCopy = async function(trigger) {
    const rule = await load(trigger); if (!rule) return;
    if (!rule.permissions.create) {toast('没有创建规则权限');return;}
    const source = structuredClone(rule);
    window.openRuleCreate();
    applyContent({...source, name:source.name+' - 副本'},false);
    $('ruleEditorTitle').textContent = '复制规则';
    $('ruleCreateName').dispatchEvent(new Event('input',{bubbles:true}));
    ruleRefreshPermissions();
  };
  window.rulePublish = async function(trigger) {
    const rule = await load(trigger); if (!rule) return;
    if (!rule.permissions.publish) { toast('没有发布规则权限'); return; }
    if (rule.versions.length) {toast('已发布规则不可修改，请复制创建新规则');return;}
    if (!confirm('确认发布规则吗？')) return;
    try {
      const response = await fetch('/data/rules/'+encodeURIComponent(rule.id)+'/publish',{
        method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:rule.revision})});
      const data = await response.json(); if (!response.ok) throw Error(data.error || '发布失败');
      location.reload();
    } catch(e) { toast(e.message); }
  };
  window.ruleDelete = async function(trigger) {
    const rule = await load(trigger); if (!rule) return;
    if (!confirm('删除此未发布规则？')) return;
    try {
      const response = await fetch('/data/rules/'+encodeURIComponent(rule.id),{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:rule.revision})});
      const data = await response.json(); if (!response.ok) throw Error(data.error || '删除失败');
      location.reload();
    } catch(e) { toast(e.message); }
  };
  if(window.RULE_EDITOR_PERMISSIONS&&!window.RULE_EDITOR_PERMISSIONS.edit)document.querySelectorAll('.rule-update-action').forEach(e=>e.hidden=true);
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', installRuleVersionEditor);
else installRuleVersionEditor();
