// Run against the local Flask preview: NODE_PATH=<packages> node tests/data_management_selection.cjs
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.BROWSER_CHANNEL || 'chrome' });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.PREVIEW_URL || 'http://127.0.0.1:5007/data/recordings');
    const count = () => page.locator('.dpr-instance-select:checked').count();
    const range = async scope => {
      await page.locator('#dprSelectionMenuTrigger').click();
      await page.locator(`[data-selection-scope="${scope}"]`).click();
    };
    const closeReassign = () => page.locator('#dprInstanceActionMask .drawer-close').click();
    for (const [id, taskId, person, resource] of [
      ['405708', '020454', '包媛桐', null],
      ['405761', '020454', null, '质检复核用户组'],
      ['405711', '020453', null, '供应商 A'],
      ['406006', '020455', '陈晨', null],
    ]) {
      const row = page.locator(`[data-data-id="${id}"]`);
      assert.equal(await row.locator('.dpr-instance-actions button').isEnabled(), true);
      await row.locator('.dpr-instance-actions button').click();
      const facts = await page.locator('#dprInstanceActionContext').innerText();
      assert.ok(facts.includes(`数据 ID：${id}`));
      assert.ok(facts.includes(`处理任务 ID：${taskId}`));
      assert.ok(!facts.includes('数据处理 ID'));
      const options = await page.locator('[data-reassign-type]:visible').allTextContents();
      assert.deepEqual(options, person ? ['指定用户'] : ['用户组', '供应商', '指定用户']);
      if (person) {
        assert.ok(facts.includes(`当前处理人：${person}`));
        assert.ok(!facts.includes('当前处理用户组/供应商'));
        assert.equal(await page.locator('[name="dprReassignType"][value="person"]').isChecked(), true);
      } else {
        assert.ok(facts.includes(`当前处理用户组/供应商：${resource}`));
        assert.ok(!facts.includes('当前处理人：'));
        for (const type of ['user_group', 'supplier', 'person']) {
          await page.locator(`[name="dprReassignType"][value="${type}"]`).check();
          assert.equal(await page.locator(type === 'person' ? '#dprInstancePersonPicker' : '#dprInstanceAssignee').isVisible(), true);
        }
      }
      await closeReassign();
    }
    assert.equal(await page.locator('[data-status="archived"] .dpr-instance-actions button:disabled').count(), 2);
    // A supplier-backed row with a named person follows the same batch rule as a user row.
    for (const id of ['405708', '406006']) await page.locator(`[data-data-id="${id}"] .dpr-instance-select`).check();
    await page.locator('#dprBulkReassignInstances').click();
    assert.deepEqual(await page.locator('[data-reassign-type]:visible').allTextContents(), ['指定用户']);
    await closeReassign();
    for (const id of ['405708', '406006']) await page.locator(`[data-data-id="${id}"] .dpr-instance-select`).uncheck();
    for (const id of ['405761', '405711']) await page.locator(`[data-data-id="${id}"] .dpr-instance-select`).check();
    await page.locator('#dprBulkReassignInstances').click();
    assert.deepEqual(await page.locator('[data-reassign-type]:visible').allTextContents(), ['用户组', '供应商', '指定用户']);
    await closeReassign();
    for (const id of ['405761', '405711']) await page.locator(`[data-data-id="${id}"] .dpr-instance-select`).uncheck();
    await page.locator('#dprInstancePageSize').selectOption('5');
    assert.equal(await page.locator('[data-instance-row]:visible').count(), 5);
    await range('page');
    assert.equal(await count(), 4);
    assert.equal(await page.locator('.dpr-instance-select:disabled:checked').count(), 0);
    await page.locator('#dprInstanceNext').click();
    assert.equal(await count(), 4);
    assert.equal(await page.locator('#dprInstanceSelectAll').isChecked(), false);
    await range('all');
    assert.equal(await count(), 4);
    assert.match(await page.locator('#dprInstanceSelectedSummary').innerText(), /4/);
    await page.locator('#dprBulkStartProcessing').click();
    assert.equal(await page.locator('#dprBatchStartModalIds').inputValue(), '405708,405761,405711,406006');
    await page.locator('#dprBatchStartModalMask .drawer-close').click();
    await page.locator('#dprBulkReassignInstances').click();
    assert.equal(await page.locator('#dprReassignNoticeMask').isVisible(), true);
    await page.locator('#dprReassignNoticeMask .drawer-close').click();
    await page.locator('#dprInstancePrev').click();
    await page.locator('[data-data-id="406006"] .dpr-instance-select').uncheck();
    assert.equal(await count(), 3);
    assert.equal(await page.locator('#dprInstanceSelectAll').evaluate(el => el.indeterminate), true);
    await range('page');
    assert.equal(await count(), 4);
    await page.locator('#dprInstanceSelectAll').uncheck();
    assert.equal(await count(), 0);
    await page.locator('[data-filter="taskId"]').fill('020454');
    await page.locator('.dpr-instance-filter-actions .btn-primary').click();
    assert.equal(await page.locator('#dprInstancePageLabel').innerText(), '1 / 1');
    await range('all');
    assert.equal(await count(), 2);
    await page.locator('#dprBulkStartProcessing').click();
    assert.equal(await page.locator('#dprBatchStartModalIds').inputValue(), '405708,405761');
    await page.locator('#dprBatchStartModalMask .drawer-close').click();
    await page.locator('[data-filter="taskId"]').fill('missing');
    await page.locator('.dpr-instance-filter-actions .btn-primary').click();
    assert.equal(await count(), 0);
    assert.equal(await page.locator('#dprInstanceSelectAll').isDisabled(), true);
    assert.equal(await page.locator('#dprBulkReassignInstances').isDisabled(), true);
    assert.equal(await page.locator('#dprInstanceEmpty').isVisible(), true);
    await page.locator('#dprSelectionMenuTrigger').click();
    assert.equal(await page.locator('[data-selection-scope="all"]').isDisabled(), true);
    await page.keyboard.press('Escape');
    await page.locator('.dpr-instance-filter-actions .btn').first().click();
    await page.locator('[data-header-control="status"] .dpr-header-filter-trigger').click();
    await page.locator('[data-header-control="status"] button[data-value="archived"]').click();
    assert.equal(await page.locator('#dprInstanceSelectAll').isDisabled(), true);
    assert.equal(await count(), 0);
    await page.locator('.dpr-instance-filter-actions .btn').first().click();
    await range('all');
    await page.locator('#dprInstanceSelectAll').uncheck();
    assert.equal(await count(), 0);
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
      await page.setViewportSize(viewport);
      await page.locator('#dprSelectionMenuTrigger').scrollIntoViewIfNeeded();
      await page.waitForTimeout(150);
      await page.locator('#dprSelectionMenuTrigger').click();
      const bounds = await page.locator('#dprSelectionMenu').boundingBox();
      assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= viewport.width);
      assert.ok(bounds.y >= 0 && bounds.y + bounds.height <= viewport.height);
      await page.screenshot({ path: `/tmp/data-selection-${viewport.width}.png` });
      assert.equal(await page.locator('#dprSelectionMenu').isVisible(), true);
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#dprSelectionMenu').isHidden(), true);
    }
    assert.deepEqual(errors, []);
    console.log('PASS: reassignment eligibility, person/resource options and context, batch rules, selection, pagination, filters, and responsive menu.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
