const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const {mkdtemp, rm} = require('node:fs/promises');
const {tmpdir} = require('node:os');
const {join} = require('node:path');
const net = require('node:net');

async function run() {
  const directory = await mkdtemp(join(tmpdir(), 'leadflow-auth-browser-'));
  const reservation = net.createServer();
  await new Promise(resolve => reservation.listen(0, '127.0.0.1', resolve));
  const port = reservation.address().port;
  await new Promise(resolve => reservation.close(resolve));
  const origin = `http://127.0.0.1:${port}`;
  const token = 'synthetic-browser-token-' + 'B'.repeat(40);
  const server = spawn(process.env.PYTHON || 'python', [
    '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(port)
  ], {
    env: {
      ...process.env,
      LEADFLOW_DB_PATH: join(directory, 'synthetic.db'),
      LEADFLOW_REQUIRE_OPERATOR_AUTH: '1',
      LEADFLOW_OPERATOR_TOKEN: token,
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let serverError;
  server.on('error', error => {serverError = error;});
  let browser;
  try {
    const deadline = Date.now() + 15000;
    while (true) {
      if (serverError) throw serverError;
      if (server.exitCode !== null) throw new Error('Protected demo server exited');
      try { if ((await fetch(`${origin}/health`)).ok) break; } catch {}
      if (Date.now() > deadline) throw new Error('Protected demo did not start');
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    browser = await chromium.launch({headless: true});
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const intake = await page.request.post(`${origin}/api/leads`, {
      data: {
        name: 'Synthetic Private Lead',
        email: 'synthetic-private@example.com',
        service: 'Synthetic service',
        source: 'browser-test',
        communication_consent: false,
      },
    });
    assert.equal(intake.status(), 201);

    const withoutAccess = await page.request.get(`${origin}/api/leads`);
    assert.equal(withoutAccess.status(), 401);
    const withAccess = await page.request.get(`${origin}/api/leads`, {
      headers: {Authorization: `Bearer ${token}`},
    });
    assert.equal(withAccess.status(), 200);
    assert.equal((await withAccess.json()).length, 1);

    await page.goto(origin);
    const status = page.locator('#queue-status');
    const accessField = page.locator('#operator-token');
    const refresh = page.getByRole('button', {name:'Refresh', exact:true});
    const denied = 'Operator access required. Enter a valid token and refresh.';
    await page.waitForFunction(expected => document.querySelector('#queue-status').textContent === expected, denied);
    assert.equal(await page.locator('#queue .lead').count(), 0);

    await accessField.fill('synthetic-invalid-token');
    await refresh.click();
    await page.waitForFunction(expected => document.querySelector('#queue-status').textContent === expected, denied);
    assert.equal(await page.locator('#queue .lead').count(), 0);

    await accessField.fill(token);
    await refresh.click();
    await page.waitForFunction(() => document.querySelector('#queue-status').textContent === 'Queue refreshed: 1 lead loaded.');
    assert.equal(await page.locator('#queue .lead').count(), 1);
    assert.match(await page.locator('#queue').textContent(), /Synthetic Private Lead/);

    // Revocation/clearing must not leave old PII rendered in the operator queue.
    await accessField.fill('');
    await refresh.click();
    await page.waitForFunction(expected => document.querySelector('#queue-status').textContent === expected, denied);
    assert.equal(await page.locator('#queue .lead').count(), 0);
    await page.reload();
    await page.waitForFunction(expected => document.querySelector('#queue-status').textContent === expected, denied);
    assert.equal(await accessField.inputValue(), '', 'Secret persisted across reload');
    assert.equal(await page.locator('#queue .lead').count(), 0);
    assert.deepEqual(errors, []);
    console.log('PASS: authorized queue, denied private API, invalid token, clear stale PII, no persisted browser secret');
  } finally {
    if (browser) await browser.close();
    if (server.exitCode === null) {
      const exited = new Promise(resolve => server.once('exit', resolve));
      server.kill('SIGTERM');
      const timer = setTimeout(() => server.kill('SIGKILL'), 3000);
      await exited;
      clearTimeout(timer);
    }
    await rm(directory, {recursive:true, force:true});
  }
}
run().catch(error => {console.error(error); process.exitCode = 1;});
