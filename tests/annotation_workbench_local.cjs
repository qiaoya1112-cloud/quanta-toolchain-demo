// NODE_PATH=<bundled node_modules> node tests/annotation_workbench_local.cjs
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
(async () => {
  const browser = await chromium.launch({headless: true, channel: process.env.BROWSER_CHANNEL || 'chrome'});
  try {
    const context = await browser.newContext({viewport: {width:1600, height:1000}});
    const page = await context.newPage();
    const root = process.env.PREVIEW_URL || 'http://127.0.0.1:5004';
    const errors=[], external=[], failed=[];
    page.on('pageerror', e => errors.push(e.message));
    page.on('request', r => {if(new URL(r.url()).origin!==new URL(root).origin) external.push(r.url());});
    page.on('response', r => {if(r.status()>=400) failed.push(r.url());});
    await page.goto(root+'/data/workbench-v2/optimized');
    await page.locator('.main[aria-busy="false"]').waitFor();
    assert.equal(await page.locator('iframe').count(),0);
    assert.equal(await page.locator('.workbench-feed').count(),4);
    const semantic=page.locator('workbench-segment-editor:not([variant])');
    await page.locator('.workbench-review__row[data-index="3"]').click();
    assert.equal(await semantic.locator('[data-number]').innerText(),'03');
    await semantic.locator('[data-action="error"]').click();
    await semantic.locator('[data-reason="描述与画面不一致"]').click();
    assert.match(await page.locator('.workbench-review__row.is-active').innerText(),/描述与画面不一致/);
    await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    await page.reload(); await page.locator('.main[aria-busy="false"]').waitFor();
    assert.equal(await semantic.locator('[data-number]').innerText(),'03');
    assert.equal(await semantic.locator('[data-error]').innerText(),'描述与画面不一致');
    await page.locator('[data-review-variant="quality"]').click();
    assert.equal(await page.locator('.workbench-feed').count(),3);
    const quality=page.locator('workbench-segment-editor[variant="variant-2"]');
    await quality.locator('.workbench-mistake-description').fill('质检草稿 <检查画面>');
    assert.match(await page.locator('[data-quality-list] .is-active').innerText(),/质检草稿 <检查画面>/);
    await page.locator('[data-review-variant="action"]').click();
    assert.equal(await page.locator('.workbench-feed').count(),4);
    const action=page.locator('workbench-segment-editor[variant="variant-3"]');
    assert.equal(await action.isVisible(),true);
    await action.locator('[data-action="error"]').click();
    await action.locator('[data-reason="动作结束边界偏晚"]').click();
    assert.match(await page.locator('[data-action-list] .is-active').innerText(),/动作结束边界偏晚/);
    await page.locator('.workbench-review__tabs button').filter({hasText:/^标签$/}).click();
    assert.equal(await page.locator('.workbench-feed').count(),3);
    assert.equal(await page.locator('.tag-editor').isVisible(),true);
    assert.equal(await action.isVisible(),false);
    assert.equal(await page.locator('.tag-block').count(),9);
    assert.equal(await page.locator('.tag-lane').count(),7);
    assert.equal(await page.locator('.tag-lanes-window').evaluate(el=>el.clientHeight),155);
    assert.equal(await page.locator('.tag-record-group').evaluateAll(groups=>groups.every(group=>Boolean(group.querySelector('[data-tag-add-label]'))===!group.querySelector('.tag-record'))),true);
    await page.locator('[data-tag-delete-track]').click();
    assert.equal(await page.locator('.tag-lane[data-tag-label="act_pick"]').count(),0);
    assert.equal(await page.locator('.tag-record').count(),6);
    await page.locator('[data-tag-undo]').click();
    assert.equal(await page.locator('.tag-lane[data-tag-label="act_pick"] .tag-block').count(),3);
    assert.equal(await page.locator('.tag-record').count(),9);
    const toolbar=page.locator('.tag-toolbar');
    assert.ok((await toolbar.boundingBox()).y < (await page.locator('.tag-lanes').boundingBox()).y);
    assert.equal(await toolbar.locator('[aria-label="父级分割"]').isDisabled(),true);
    assert.equal(await toolbar.locator('[data-playback-current]').innerText(),'00:18');
    await toolbar.locator('[aria-label="倍速"]').click();
    assert.equal(await toolbar.locator('[aria-label="倍速"] span').innerText(),'1.5x');
    await toolbar.locator('[aria-label="播放"]').click();
    await page.waitForFunction(()=>document.querySelector('.tag-toolbar [data-playback-current]').textContent!=='00:18');
    await toolbar.locator('[aria-label="暂停"]').click();
    const untouched=await page.locator('.tag-block[data-tag-id="tag-hands"]').getAttribute('style');
    await toolbar.locator('[aria-label="分割"]').click();
    const splitting=page.locator('.tag-block[data-tag-id="tag-books"]');
    const splitBounds=await splitting.boundingBox();
    await splitting.click({position:{x:splitBounds.width*.65,y:9}});
    assert.equal(await page.locator('.tag-block').count(),10);
    await toolbar.locator('[aria-label="分割"]').click();
    await toolbar.locator('[aria-label="合并"]').click();
    assert.equal(await page.locator('.tag-block').count(),9);
    assert.equal(await page.locator('.tag-block[data-tag-id="tag-hands"]').getAttribute('style'),untouched);
    await page.locator('[data-tag-next]').click();
    assert.equal(await page.locator('[data-tag-start]').inputValue(),'00:40');
    await page.locator('[data-tag-previous]').click();
    assert.equal(await page.locator('[data-tag-start]').inputValue(),'00:08');
    assert.equal(await page.locator('.tag-editor .form-row').count(),2);
    assert.equal(await page.locator('.tag-editor [data-tag-unavailable]').count(),0);
    assert.equal(await page.locator('.tag-editor .field-label').innerText(),'错误原因');
    await page.locator('#tag-error').selectOption('片段范围错误');
    await page.locator('[data-tag-down]').click();
    assert.match(await page.locator('.tag-block.is-selected').innerText(),/放置/);
    await page.locator('[data-tag-up]').click();
    assert.match(await page.locator('.tag-block.is-selected').innerText(),/拿取/);
    assert.equal(await page.locator('#tag-error').inputValue(),'片段范围错误');
    assert.equal(await page.locator('[data-tag-up]').isDisabled(),true);
    assert.deepEqual(await page.locator('.tag-editor .segment-action--navigate').allTextContents(),['⌘↑','⌘↓','⌘←','⌘→']);
    await page.locator('[data-tag-next]').focus();
    await page.keyboard.press('Meta+ArrowRight');
    assert.equal(await page.locator('[data-tag-start]').inputValue(),'00:40');
    await page.keyboard.press('Meta+ArrowLeft');
    assert.equal(await page.locator('[data-tag-start]').inputValue(),'00:08');
    await page.keyboard.press('Meta+ArrowDown');
    assert.match(await page.locator('.tag-block.is-selected').innerText(),/放置/);
    await page.keyboard.press('Meta+ArrowUp');
    assert.match(await page.locator('.tag-block.is-selected').innerText(),/拿取/);
    await page.locator('[data-tag-expand="all"]').click();
    assert.equal(await page.locator('.tag-panel details:not([open])').count(),0);
    await page.locator('[data-tag-expand="annotated"]').click();
    assert.equal(await page.locator('.tag-panel [data-tag-add-label]').count(),0);
    assert.equal(await page.locator('.tag-panel .tag-record-group').count(),7);
    assert.equal(await page.locator('.tag-panel details').evaluateAll(branches=>branches.every(branch=>branch.open===Boolean(branch.querySelector('.tag-record')))),true);

    const search=page.locator('[data-tag-search]');
    await search.fill('取');
    assert.deepEqual(await page.locator('.tag-panel .tag-record-title').allTextContents(),['拿取','取出']);
    await search.fill('放入');
    assert.equal(await page.locator('.tag-panel .tag-record-group').count(),0);
    assert.equal(await page.locator('.tag-panel .tag-empty').innerText(),'未找到匹配标签');
    await page.locator('[data-tag-expand="all"]').click();
    assert.deepEqual(await page.locator('.tag-panel .tag-record-title').allTextContents(),['放入']);
    assert.equal(await page.locator('.tag-panel [data-tag-add-label]').count(),1);
    await search.fill('拿放类');
    assert.equal(await page.locator('.tag-panel .tag-record-group').count(),6);
    await search.fill('');
    assert.equal(await page.locator('.tag-panel .tag-empty').count(),0);
    const trackColors=await page.locator('.tag-lane[data-tag-label]').evaluateAll(lanes=>lanes.map(lane=>lane.querySelector('.tag-block').style.getPropertyValue('--tag-color')));
    assert.equal(new Set(trackColors).size,7);
    assert.ok((await page.locator('.tag-lane-name').allTextContents()).every(Boolean));
    const alignment=await page.locator('.tag-timeline').evaluate(el=>({
      label:el.querySelector('.tag-lane-name').getBoundingClientRect().width,
      rail:el.querySelector('.tag-lane-rail').getBoundingClientRect().x,
      selector:el.querySelector('.tag-selection').getBoundingClientRect().x,
      playhead:el.querySelector('.tag-playhead-track').getBoundingClientRect().x
    }));
    assert.equal(alignment.label,64);
    assert.ok(Math.abs(alignment.rail-alignment.selector)<1);
    assert.ok(Math.abs(alignment.rail-alignment.playhead)<1);
    // Add overlapping labels through the right-side leaf entries.
    for(const label of ['act_pick','act_put_in']) {
      if(label==='act_pick')await page.locator('[data-tag-new]').click();
      else await page.locator(`[data-tag-add-label="${label}"]`).click();
      await page.locator('[data-tag-start]').fill('00:20');
      await page.locator('[data-tag-end]').fill('00:38');
      await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    }
    await page.locator('.tag-lane[data-tag-label="act_pick"] .tag-block').nth(1).click();
    assert.equal(await page.locator('.tag-record').count(),11);
    assert.equal(await page.locator('.tag-lane[data-tag-label]').count(),8);
    assert.equal(await page.locator('.tag-lane').count(),8);
    const bookBlocks=page.locator('.tag-lane[data-tag-label="act_pick"]').locator('.tag-block');
    assert.equal(await bookBlocks.count(),4);
    assert.notEqual(await bookBlocks.nth(0).evaluate(e=>e.style.top),await bookBlocks.nth(1).evaluate(e=>e.style.top));
    // A bad bound must not mutate records, and selecting/editing one leaves overlaps intact.
    await page.locator('[data-tag-end]').fill('01:20');
    await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    assert.match(await page.locator('[data-tag-message]').innerText(),/00:00–01:10/);
    assert.equal(await page.locator('.tag-record').count(),11);
    await page.locator('[data-tag-end]').fill('00:40');
    await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    assert.match(await page.locator('.tag-record.is-active').innerText(),/00:40/);
    await page.locator('[data-tag-delete]').click();
    assert.equal(await page.locator('.tag-record').count(),10);
    await page.locator('[data-tag-undo]').click();
    assert.equal(await page.locator('.tag-record').count(),11);
    // Existing range handles edit the chosen tag without affecting another tag.
    const handle=page.locator('.tag-selection .segmented-timeline__range-handle.is-end');
    const bounds=await handle.boundingBox();
    await page.mouse.move(bounds.x+bounds.width/2,bounds.y+bounds.height/2);
    await page.mouse.down(); await page.mouse.move(bounds.x+bounds.width/2+35,bounds.y+bounds.height/2,{steps:5}); await page.mouse.up();
    assert.ok((await page.locator('[data-tag-end]').inputValue())>'00:40');
    await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    assert.equal(await page.locator('.tag-record-group[data-tag-label="act_put_in"] .tag-record').count(),1);
    assert.match(await page.locator('.tag-record-group[data-tag-label="act_put_in"]').innerText(),/00:20 → 00:38/);
    // Saving also applies the current edit so switching modes cannot lose it.
    await page.locator('[data-tag-end]').fill('00:45');
    await page.locator('#tag-error').selectOption('标签选择错误');
    await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    await page.reload(); await page.locator('.main[aria-busy="false"]').waitFor();
    await page.locator('[data-review-variant="tags"]').click();
    assert.equal(await page.locator('.tag-record').count(),11);
    assert.equal(await page.locator('[data-tag-end]').inputValue(),'00:45');
    assert.equal(await page.locator('#tag-error').inputValue(),'标签选择错误');
    // Add a disjoint range through the label's own entry, preserving its other ranges.
    const books=page.locator('.tag-record-group[data-tag-label="act_pick"]');
    assert.equal(await books.locator('.tag-record').count(),4);
    assert.equal(await books.locator('[data-tag-add-label]').count(),0);
    await page.locator('[data-tag-new]').click();
    assert.match(await page.locator('[data-tag-title]').getAttribute('title'),/拿取/);
    await page.locator('[data-tag-start]').fill('00:50');
    await page.locator('[data-tag-end]').fill('00:53');
    await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    assert.equal(await books.locator('.tag-record').count(),5);
    assert.equal(await page.locator('[data-tag-count], .tag-panel-guide').count(),0);
    await page.locator('[data-tag-end]').fill('00:52');
    await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    assert.match(await books.innerText(),/00:40 → 00:49/);
    assert.match(await books.innerText(),/00:55 → 01:04/);
    await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    await page.reload(); await page.locator('.main[aria-busy="false"]').waitFor();
    await page.locator('[data-review-variant="tags"]').click();
    assert.equal(await books.locator('.tag-record').count(),5);
    assert.match(await books.innerText(),/00:50 → 00:52/);
    await page.locator('[data-tag-delete]').click();
    assert.equal(await books.locator('.tag-record').count(),4);
    assert.match(await books.innerText(),/00:40 → 00:49/);
    await page.locator('[data-tag-undo]').click();
    const otherRecords=await page.locator('.tag-record:not(.tag-record-group[data-tag-label="act_pick"] .tag-record)').count();
    await page.locator('[data-tag-delete-track]').click();
    assert.equal(await books.locator('.tag-record').count(),0);
    assert.equal(await books.locator('[data-tag-add-label]').count(),1);
    assert.equal(await page.locator('.tag-record').count(),otherRecords);
    await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    await page.reload();await page.locator('.main[aria-busy="false"]').waitFor();
    await page.locator('[data-review-variant="tags"]').click();
    assert.equal(await books.locator('.tag-record').count(),0);
    // Re-add a segment to the empty track for the remaining smoke checks.
    await books.locator('[data-tag-add-label]').click();
    await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    // Additional tracks scroll inside the fixed five-track viewport.
    await page.locator('[data-tag-expand="all"]').click();
    for(let i=0;i<2;i++) {
      await page.locator('.tag-panel [data-tag-add-label]').first().click();
      await page.locator('workbench-footer-actions:visible [data-action="save"]').click();
    }
    assert.equal(await page.locator('.tag-lane[data-tag-label]').count(),10);
    assert.equal(await page.locator('.tag-lanes-window').evaluate(el=>el.clientHeight),155);
    assert.equal(await page.locator('.tag-lanes').evaluate(el=>el.scrollHeight>el.clientHeight),true);
    await page.locator('.tag-lanes').evaluate(el=>el.scrollTop=el.scrollHeight);
    assert.ok(await page.locator('.tag-lanes').evaluate(el=>el.scrollTop)>0);
    for(const theme of ['dark','light']) {
      await page.locator('.workbench-theme-tabs [data-theme="'+theme+'"]').click();
      await page.screenshot({path:'/tmp/annotation-tags-'+theme+'.png'});
    }
    await page.setViewportSize({width:1280,height:800});
    await page.screenshot({path:'/tmp/annotation-tags-compact.png'});
    assert.ok((await page.locator('.tag-editor').boundingBox()).y>=0);
    await page.setViewportSize({width:1600,height:1000});
    await page.locator('[data-review-variant="quality"]').click();
    assert.equal(await quality.locator('.workbench-mistake-description').inputValue(),'质检草稿 <检查画面>');
    await page.locator('[data-review-variant="segments"]').click();
    assert.equal(await semantic.locator('[data-error]').innerText(),'描述与画面不一致');
    await page.locator('workbench-footer-actions:visible [data-action="submit"]').click();
    await page.locator('dialog[open] [data-dialog-action="confirm"]').click();
    await page.locator('[data-review-variant="log"]').click();
    assert.match(await page.locator('.review-log__card').first().innerText(),/Joanna Qiao/);
    await page.locator('[data-review-variant="segments"]').click();
    await page.locator('workbench-footer-actions:visible [data-action="reject"]').click();
    await page.locator('dialog[open] textarea').fill('请核对片段边界');
    await page.locator('dialog[open] [data-dialog-action="confirm"]').click();
    await page.locator('[data-review-variant="log"]').click();
    assert.match(await page.locator('.review-log__card').first().innerText(),/请核对片段边界/);
    await page.locator('[data-review-variant="info"]').click();
    assert.equal(await page.locator('.review-info').isVisible(),true);
    for(const theme of ['light','blue','dark']) {
      await page.locator('.workbench-theme-tabs [data-theme="'+theme+'"]').click();
      assert.equal(await page.locator('html').getAttribute('data-workbench-theme'),theme);
    }
    await page.locator('[data-review-variant="segments"]').click();
    await page.screenshot({path:'/tmp/annotation-local-verified.png'});
    assert.deepEqual(errors,[]); assert.deepEqual(external,[]); assert.deepEqual(failed,[]);
    await page.locator('.workbench-task-info__close').click();
    await page.waitForURL(root+'/data/workbench-v2');
    console.log('PASS: local assets, segment/editor sync, isolated modes, draft reload, tags, submit/reject, themes and return.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
