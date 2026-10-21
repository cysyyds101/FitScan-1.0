// 临时脚本：用 CDP 打开页面 → 点击第一件服装 → 截图，验证交互与选中态。
import fs from 'node:fs';

const PORT = process.env.CDP_PORT || '9333';
const OUT = process.argv[2] || 'shot.png';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
const target = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
if (!target) {
  console.error('no page target');
  process.exit(1);
}

const ws = new WebSocket(target.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
ws.addEventListener('message', (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    pending.get(msg.id)(msg);
    pending.delete(msg.id);
  }
});
await new Promise((res, rej) => {
  ws.addEventListener('open', res);
  ws.addEventListener('error', rej);
});

const send = (method, params = {}) => {
  const mid = ++id;
  return new Promise((resolve) => {
    pending.set(mid, resolve);
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
};

await send('Page.enable');
await send('Runtime.enable');
await sleep(2500);

const clicked = await send('Runtime.evaluate', {
  expression: `(() => {
    const btn = document.querySelector('.list .item');
    if (!btn) return 'no-item';
    const name = btn.querySelector('.name')?.textContent || '?';
    btn.click();
    return 'clicked: ' + name;
  })()`,
  returnByValue: true,
});
console.log(clicked.result?.result?.value);

await sleep(4000);

const state = await send('Runtime.evaluate', {
  expression: `(() => {
    const active = document.querySelector('.list .item.active .name')?.textContent || null;
    const canvas = !!document.querySelector('canvas');
    return JSON.stringify({ activeItem: active, canvas });
  })()`,
  returnByValue: true,
});
console.log('state:', state.result?.result?.value);

const shot = await send('Page.captureScreenshot', { format: 'png' });
fs.writeFileSync(OUT, Buffer.from(shot.result.data, 'base64'));
console.log('saved', OUT);
ws.close();
