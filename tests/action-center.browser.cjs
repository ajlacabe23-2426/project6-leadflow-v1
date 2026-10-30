const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const {mkdtemp,rm} = require('node:fs/promises');
const {tmpdir} = require('node:os');
const {join} = require('node:path');
const net = require('node:net');

async function run(){
  const dir=await mkdtemp(join(tmpdir(),'leadflow-action-browser-'));
  const reservation=net.createServer();
  await new Promise(resolve=>reservation.listen(0,'127.0.0.1',resolve));
  const port=reservation.address().port;
  await new Promise(resolve=>reservation.close(resolve));
  const origin='http://127.0.0.1:'+port;
  const token='local-test-'+ 'T'.repeat(44);
  const server=spawn(process.env.PYTHON||'python',
    ['-m','uvicorn','app.main:app','--host','127.0.0.1','--port',String(port)],{
      env:{...process.env,LEADFLOW_DB_PATH:join(dir,'synthetic.db'),
        LEADFLOW_ENABLE_AUTO_TRIAGE:'1',LEADFLOW_REQUIRE_OPERATOR_AUTH:'1',
        LEADFLOW_OPERATOR_TOKEN:token},
      stdio:['ignore','pipe','pipe'],
    });
  let startupError;
  server.on('error',e=>{startupError=e;});
  let browser;
  try{
    const deadline=Date.now()+15000;
    while(true){
      if(startupError)throw startupError;
      if(server.exitCode!==null)throw Error('Local verification server exited');
      try{if((await fetch(origin+'/health')).ok)break;}catch{}
      if(Date.now()>deadline)throw Error('Local verification server did not start');
      await new Promise(resolve=>setTimeout(resolve,100));
    }
    browser=await chromium.launch({headless:true});
    const page=await browser.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto(origin+'/widget');
    await page.getByLabel('Name').fill('Synthetic Widget Lead');
    await page.getByLabel('Email').fill('synthetic-widget@example.com');
    await page.getByLabel('What do you need?').fill('Synthetic estimate');
    await page.getByRole('button',{name:'Send inquiry'}).click();
    await page.getByRole('status').getByText(/Your inquiry was recorded as #/).waitFor();
    assert.equal((await page.request.get(origin+'/api/action-center')).status(),401);

    await page.goto(origin+'/action-center');
    await page.locator('#token').fill(token);
    await page.getByRole('button',{name:'Refresh actions'}).click();
    await page.locator('.case').waitFor();
    assert.equal(await page.locator('.case').count(),1);
    assert.match(await page.locator('.case').innerText(),/Synthetic Widget Lead/);
    assert.match(await page.locator('.case').innerText(),/queue\.triage/);
    assert.match(await page.locator('.case').innerText(),/owner review/i);
    await page.locator('#owner').fill('operator.browser');
    await page.getByRole('button',{name:'Assign to operator'}).click();
    await page.getByText('operator.browser').waitFor();
    await page.getByRole('button',{name:'Mark completed'}).click();
    await page.locator('.task.done').waitFor();

    // Reload discards operator secret; private records must disappear.
    await page.reload();
    await page.getByRole('status').getByText(/Operator access required/).waitFor();
    assert.equal(await page.locator('#token').inputValue(),'');
    assert.equal(await page.locator('.case').count(),0);
    assert.deepEqual(errors,[]);
    console.log('PASS: real browser widget intake, protected action center, assignment, task completion, secret reset');
  }finally{
    if(browser)await browser.close();
    if(server.exitCode===null){
      const done=new Promise(resolve=>server.once('exit',resolve));
      server.kill('SIGTERM');
      const timer=setTimeout(()=>server.kill('SIGKILL'),3000);
      await done;clearTimeout(timer);
    }
    await rm(dir,{recursive:true,force:true});
  }
}
run().catch(e=>{console.error(e);process.exitCode=1;});
