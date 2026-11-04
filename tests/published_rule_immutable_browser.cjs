const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {chromium}=require('C:/Users/tinab/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..');
const dir=fs.mkdtempSync(path.join(root,'instance','immutable-rule-'));
const python=path.resolve(root,'../../05-demo-source/.venv/Scripts/python.exe');
const port=Number(process.env.RULE_TEST_PORT||5192);
const service=spawn(python,['-B','-m','flask','--app','toolchain_demo','run','--host','127.0.0.1','--port',String(port),'--no-reload','--no-debugger'],{
  cwd:root,env:{...process.env,COLLECTION_DEMO_DB:path.join(dir,'demo.sqlite3')},stdio:'ignore',windowsHide:true
});
(async()=>{
  let browser;
  try {
    const url=`http://127.0.0.1:${port}`;
    for(let i=0;i<100;i++){try{if((await fetch(url+'/data/rules')).ok)break}catch{}await new Promise(r=>setTimeout(r,100));}
    browser=await chromium.launch({channel:'chrome',headless:true});
    const page=await browser.newPage({viewport:{width:1440,height:900}});
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto(url+'/data/rules');
    const published=page.locator('.rule-management-table tr').filter({has:page.locator('[data-rule-id="RL-009"]')});
    await published.waitFor();
    assert.equal(await published.locator('[onclick*="ruleUpdate"], [onclick*="rulePublish"]').count(),0);
    assert.equal(await published.locator('[onclick*="ruleCopy"]').count(),1);
    await published.locator('[onclick*="openRuleDetail"]').click();
    await page.locator('#drawerRuleCreate.active').waitFor();
    assert.equal(await page.locator('#ruleCreateName').isDisabled(),true);
    await page.evaluate(()=>closeDrawer());
    const draft=page.locator('.rule-management-table tr').filter({has:page.locator('[data-rule-id="RL-010"]')});
    assert.equal(await draft.locator('[onclick*="openRuleDetail(this,false)"]').count(),1);
    assert.equal(await draft.locator('[onclick*="rulePublish"]').count(),1);
    assert.deepEqual(errors,[]);
    console.log('PASS published rules read-only and copyable; unpublished rules editable and publishable');
  } finally {
    if(browser)await browser.close();
    service.kill();
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
