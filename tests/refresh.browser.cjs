const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const { mkdtemp, rm } = require('node:fs/promises');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const net = require('node:net');

async function run() {
  const directory = await mkdtemp(join(tmpdir(), 'leadflow-browser-'));
  const reservation = net.createServer();
  await new Promise(resolve => reservation.listen(0, '127.0.0.1', resolve));
  const port = reservation.address().port;
  await new Promise(resolve => reservation.close(resolve));
  const origin = `http://127.0.0.1:${port}`;
  const server = spawn(process.env.PYTHON || 'python', ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(port)], {
    env: {...process.env, LEADFLOW_DB_PATH: join(directory, 'synthetic.db')},
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let serverError;
  server.on('error', error => {serverError = error;});
  let browser;
  try {
    const deadline = Date.now() + 15000;
    while (true) {
      if (serverError) throw serverError;
      if (server.exitCode !== null) throw new Error('Disposable server exited before readiness');
      try {if ((await fetch(`${origin}/health`)).ok) break;} catch {}
      if (Date.now() > deadline) throw new Error('Disposable server readiness timed out');
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    browser = await chromium.launch({headless: true});
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', route => {
      if (new URL(route.request().url()).origin === origin) return route.continue();
      errors.push('Unexpected external browser request');
      return route.abort();
    });
    const status = page.locator('#queue-status');
    const button = page.getByRole('button', {name: 'Refresh', exact: true});
    async function waitStatus(text) {
      await page.waitForFunction(expected => document.querySelector('#queue-status').textContent === expected && !document.querySelector('#refresh').disabled, text);
      assert.equal(await page.locator('#refresh').isEnabled(), true);
    }
    await page.goto(origin);
    await waitStatus('Queue refreshed. No leads yet.');
    // Create data through the real API outside the loaded queue, then use the actual button.
    const created = await page.request.post(`${origin}/api/leads`, {data: {
      name: 'Synthetic <img src=x onerror=alert(1)>', email: 'browser@example.com',
      service: 'Synthetic browser verification', source: 'test', communication_consent: false,
    }});
    assert.equal(created.status(), 201);
    assert.equal(await page.locator('#queue .lead').count(), 0);
    await button.click();
    await waitStatus('Queue refreshed: 1 lead loaded.');
    assert.equal(await page.locator('#queue .lead').count(), 1);
    assert.equal(await page.locator('#queue img').count(), 0);
    assert.match(await page.locator('#queue').textContent(), /Synthetic <img/);
    const saved = await page.locator('#queue').innerHTML();
    // Hold a real click's request to observe loading and duplicate-click suppression.
    let release;
    let requests = 0;
    let requestEntered;
    const entered = new Promise(resolve => {requestEntered = resolve;});
    await page.route('**/api/leads', async route => {
      requests++;
      await new Promise(resolve => {release = resolve; requestEntered();});
      await route.fulfill({status: 503, contentType: 'application/json', body: '{}'});
    });
    await button.click();
    await entered;
    await page.waitForFunction(() => document.querySelector('#queue-status').textContent === 'Refreshing operator queue…');
    assert.equal(await page.locator('#refresh').isDisabled(), true);
    await page.locator('#refresh').evaluate(element => element.click());
    assert.equal(requests, 1);
    release();
    await waitStatus('Unable to refresh queue. Check the local server and try again.');
    assert.equal(await page.locator('#queue').innerHTML(), saved);
    await page.unroute('**/api/leads');
    // Invalid JSON and non-array payloads must preserve the last valid queue.
    for (const body of ['invalid json', '{}']) {
      await page.route('**/api/leads', route => route.fulfill({status: 200, contentType: 'application/json', body}));
      await button.click();
      await waitStatus('Unable to refresh queue. Check the local server and try again.');
      assert.equal(await page.locator('#queue').innerHTML(), saved);
      await page.unroute('**/api/leads');
    }
    await page.route('**/api/leads', route => route.abort('failed'));
    await button.click();
    await waitStatus('Unable to refresh queue. Check the local server and try again.');
    assert.equal(await page.locator('#queue').innerHTML(), saved);
    await page.unroute('**/api/leads');
    await button.focus();
    await page.keyboard.press('Enter');
    await waitStatus('Queue refreshed: 1 lead loaded.');
    assert.equal(await status.getAttribute('aria-live'), 'polite');
    assert.equal(await status.getAttribute('role'), 'status');
    await page.setViewportSize({width: 390, height: 844});
    assert.equal(await page.locator('#refresh').isVisible(), true);
    assert.deepEqual(errors, []);
    console.log('PASS: Chromium real refresh/API/SQLite flow, loading, duplicate suppression, failures, recovery, escaping, keyboard and mobile visibility');
  } finally {
    if (browser) await browser.close();
    if (server.exitCode === null) {
      const exited = new Promise(resolve => server.once('exit', resolve));
      server.kill('SIGTERM');
      const timer = setTimeout(() => server.kill('SIGKILL'), 3000);
      await exited;
      clearTimeout(timer);
    }
    await rm(directory, {recursive: true, force: true});
  }
}
run().catch(error => {console.error(error); process.exitCode = 1;});
