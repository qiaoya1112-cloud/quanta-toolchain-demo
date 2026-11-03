/* Shared persistence adapter for the existing complete rule form. */
(() => {
  const drawer = document.getElementById('drawerRuleCreate');
  if (!drawer || drawer.dataset.persistenceReady) return;
  drawer.dataset.persistenceReady = 'true';
  const $ = id => document.getElementById(id), value = id => $(id).value.trim();
  let saving = false, requestKey = crypto.randomUUID(), permissionEpoch = 0, cleanState = '';
  const formState = () => JSON.stringify([...drawer.querySelectorAll('input,select,textarea')].map(e=>[e.id,e.value,e.checked]));
  window.ruleMarkClean = () => requestAnimationFrame(()=> { cleanState=formState(); });
  const originalOpen = window.openRuleCreate, originalClose = window.closeDrawer;
  const originalDetail = window.openRuleDetail;
  const error = document.createElement('p');
  error.className = 'rule-save-error'; error.setAttribute('role', 'alert'); error.hidden = true;
  drawer.querySelector('.drawer-foot').before(error);
  const publish = document.createElement('button');
  publish.type = 'button'; publish.className = 'btn btn-primary'; publish.id = 'rulePublishUse';
  publish.textContent = '发布并使用'; publish.hidden = true;
  publish.onclick = () => window.ruleSave();
  drawer.querySelector('.drawer-foot').append(publish);
  let nameEpoch = 0, nameTimer;
  function showNameError(message = '') {
    $('ruleNameError').textContent = message; $('ruleNameError').hidden = !message;
    $('ruleCreateName').setAttribute('aria-invalid', message ? 'true' : 'false');
  }
  async function checkName() {
    const epoch = ++nameEpoch, name = value('ruleCreateName'), project = value('ruleCreateProject');
    if (!name || !project || $('ruleCreateName').disabled) { showNameError(); return; }
    const exclude = drawer.dataset.mode === 'edit' ? drawer.dataset.ruleId : '';
    try {
      const params = new URLSearchParams({name, project, exclude_id: exclude || ''});
      const response = await fetch('/api/processing-rules/check-name?' + params, {cache:'no-store'});
      if (!response.ok) return; // Saving still performs authoritative validation.
      const data = await response.json();
      if (epoch === nameEpoch && name === value('ruleCreateName') && project === value('ruleCreateProject')) showNameError(data.duplicate ? data.message : '');
    } catch (_) { /* Do not report a network failure as an available name. */ }
  }
  function scheduleNameCheck() {
    ++nameEpoch; clearTimeout(nameTimer); showNameError(); error.hidden = true;
    nameTimer = setTimeout(checkName, 300);
  }
  $('ruleCreateName').addEventListener('input', scheduleNameCheck);
  $('ruleCreateName').addEventListener('blur', () => { clearTimeout(nameTimer); checkName(); });
  $('ruleCreateProject').addEventListener('change', scheduleNameCheck);
  function reset() { ++nameEpoch; clearTimeout(nameTimer); showNameError(); error.hidden = true; requestKey = crypto.randomUUID(); }
  async function refreshPermissions() {
    const epoch = ++permissionEpoch;
    publish.disabled = true;
    try {
      const response = await fetch('/api/processing-rules?project=' + encodeURIComponent(value('ruleCreateProject')), {cache:'no-store'});
      if (!response.ok) throw Error('权限读取失败，请重试');
      const data = await response.json();
      if (epoch !== permissionEpoch) return;
      const inline = !!window.inlineRuleContext;
      const editing = ['edit','revision'].includes(drawer.dataset.mode);
      publish.hidden = (inline ? !data.permissions.create || !data.permissions.edit || !data.permissions.publish : !(editing ? data.permissions.edit && (drawer.dataset.mode !== 'revision' || data.permissions.publish) : data.permissions.create)) || drawer.dataset.mode === 'detail';
      publish.textContent = inline ? '发布并使用' : drawer.dataset.mode === 'revision' ? '保存并发布' : editing ? '保存修改' : '创建';
      publish.disabled = saving;
    } catch (e) { error.textContent = e.message; error.hidden = false; }
  }
  window.openRuleCreate = function() {
    originalOpen(); reset(); refreshPermissions();
    window.ruleMarkClean();
    $('ruleCreateName').focus();
  };
  window.openRuleDetail = function(...args) {
    originalDetail(...args); reset(); refreshPermissions();
    window.ruleMarkClean();
  };
  window.ruleRefreshPermissions = refreshPermissions;
  $('ruleCreateProject').addEventListener('change', refreshPermissions);
  window.closeDrawer = function() {
    if (saving) return;
    if (drawer.classList.contains('active') && drawer.dataset.mode !== 'detail' && cleanState && cleanState !== formState() && !confirm('修改尚未保存，确定关闭？')) return;
    if (window.inlineRuleContext) {
      const context = window.inlineRuleContext;
      window.inlineRuleContext = null;
      drawer.classList.remove('active'); $('drawerMask').classList.remove('active');
      document.getElementById('drawerProcessingTaskForm')?.removeAttribute('inert');
      context.trigger?.focus();
      return;
    }
    originalClose();
  };
  window.addEventListener('beforeunload', e=>{
    if(drawer.classList.contains('active')&&drawer.dataset.mode!=='detail'&&cleanState&&cleanState!==formState()){
      e.preventDefault();e.returnValue='';
    }
  });
  window.rulePersist = async function() {
    if (saving) return;
    if (!$('ruleNameError').hidden) { $('ruleCreateName').focus(); return; }
    const context = window.inlineRuleContext;
    const mode = document.querySelector('input[name="ruleSemanticMode"]:checked').value;
    const values = selector => [...document.querySelectorAll(selector)].map(e=>e.value.trim()).filter(Boolean);
    const body = {
      name: value('ruleCreateName'), project: value('ruleCreateProject'), stage: value('ruleCreateStage'), rule_type: value('ruleCreateType'),
      semantic_mode: mode, document_link: value('ruleDocumentLink'), semantic_text: value('ruleTextDescription'),
      quality_mistakes: values('#ruleMistakeRows .rule-quality-value'), quality_unqualified: values('#ruleUnqualifiedRows .rule-quality-value'),
      annotation_tags: window.ruleSelectedTags(), error_reasons: values('#ruleErrorReasonRows .rule-error-name').map(name=>({name})),
      action_elements: [...document.querySelectorAll('#ruleActionElements .rule-action-tree-group')].map(e=>({
        name:e.querySelector('.rule-action-element-name').value.trim(), key:e.querySelector('.rule-action-element-key').value.trim(),
        values:[...e.querySelectorAll('.rule-action-value-row')].map(r=>({name:r.querySelector('.rule-enum-value-name').value.trim(),key:r.querySelector('.rule-enum-value-key').value.trim()}))
      })),
      action_descriptions: [...document.querySelectorAll('#ruleActionDescriptionRows tr')].map(e=>({zh:e.querySelector('.rule-action-desc-zh').value.trim(),en:e.querySelector('.rule-action-desc-en').value.trim()})).filter(d=>d.zh||d.en),
      publish: !!context || drawer.dataset.mode === 'revision', revision: Number(drawer.dataset.revision || 0)
    };
    if(context)body.node_context={project:context.project,stage:context.stage,flow:context.flow,node:context.node};
    if (context && (body.project !== context.project || body.stage !== context.stage || !context.types.includes(body.rule_type))) {
      error.textContent = '规则与当前项目、环节或流程不匹配'; error.hidden = false; return;
    }
    saving = true; error.hidden = true;
    drawer.querySelectorAll('.drawer-foot button').forEach(b=>b.disabled=true);
    try {
      const editing = drawer.dataset.mode === 'edit', revising = drawer.dataset.mode === 'revision';
      const response = await fetch('/api/processing-rules' + (editing || revising ? '/' + encodeURIComponent(drawer.dataset.ruleId) + (revising ? '/revisions' : '') : ''), {
        method: editing ? 'PUT' : 'POST', headers: {'Content-Type':'application/json','Idempotency-Key':requestKey}, body:JSON.stringify(body)
      });
      const data = await response.json();
      if (!response.ok) {
        if (data.field === 'name') { ++nameEpoch; showNameError(data.error); $('ruleCreateName').focus(); return; }
        throw Error(data.error || '保存失败，请重试');
      }
      saving = false;
      cleanState = formState();
      if (context) {
        if (data.rule.publish_status === '已发布') await context.use(data.rule);
        window.closeDrawer();
        window.toast(data.rule.publish_status === '已发布' ? '规则已发布并选用' : '规则已保存，发布后可使用');
      } else { window.location.reload(); }
    } catch (e) {
      error.textContent = e.message || '保存失败，请重试'; error.hidden = false;
    } finally {
      saving = false; drawer.querySelectorAll('.drawer-foot button').forEach(b=>b.disabled=false);
    }
  };
  drawer.addEventListener('keydown', e => {
    if (e.key === 'Escape' && !$('ruleTagModal').classList.contains('active')) { e.preventDefault(); window.closeDrawer(); }
    if (e.key === 'Tab') {
      const controls = [...drawer.querySelectorAll('button,input,select,textarea,[tabindex="0"]')].filter(e=>!e.disabled&&e.getClientRects().length);
      const first=controls[0],last=controls.at(-1);
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
    }
  });
  // Management page actions follow server-provided permissions as well.
  if (location.pathname === '/data/rules') {
    const rights=window.RULE_EDITOR_PERMISSIONS;
    if (rights && !rights.create) document.querySelectorAll('[onclick*="openRuleCreate"],[onclick*="ruleCopy"]').forEach(e=>e.hidden=true);
    if (rights && !rights.edit) document.querySelectorAll('[onclick*="openRuleDetail(this,false)"],[onclick*="ruleDelete"],.rule-update-action').forEach(e=>e.hidden=true);
    if (rights && !rights.manage) document.querySelectorAll('.rule-status-switch').forEach(e=>e.hidden=true);
    if (rights && !rights.publish) document.querySelectorAll('[onclick*="rulePublish(this)"]').forEach(e=>e.hidden=true);
  }
})();
