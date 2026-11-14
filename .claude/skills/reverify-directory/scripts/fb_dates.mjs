// usage: node fb_dates.mjs urls.tsv            (one "label<TAB>facebook-url" per line)
// Needs a headless Brave/Chrome with --remote-debugging-port (CDP_PORT, default 9333).
// Scrolls each page so logged-out Facebook renders post timestamps, then prints the newest ones.
import { readFileSync } from "node:fs";

const PORT = process.env.CDP_PORT || 9333;
const DATE_RE = /(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), ([A-Z][a-z]+ \d{1,2}, 20\d{2})/g;
const items = readFileSync(process.argv[2], "utf8").trim().split("\n").map((l) => l.split("\t"));
const pause = (ms) => new Promise((r) => setTimeout(r, ms));

async function pageText(url) {
  const t = await (await fetch(`http://localhost:${PORT}/json/new?about:blank`, { method: "PUT" })).json();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0;
  const pending = new Map();
  ws.onmessage = (m) => {
    const x = JSON.parse(m.data);
    if (x.id && pending.has(x.id)) { pending.get(x.id)(x); pending.delete(x.id); }
  };
  const send = (method, params = {}) => new Promise((r) => {
    const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params }));
  });
  try {
    await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 1600, deviceScaleFactor: 1, mobile: false });
    await send("Page.navigate", { url });
    await pause(7000);
    await send("Runtime.evaluate", { expression: `[...document.querySelectorAll('[aria-label="Close"]')].forEach(b => b.click())` });
    for (let i = 0; i < 4; i++) {
      await send("Runtime.evaluate", { expression: "window.scrollBy(0, 1400)" });
      await pause(2000);
    }
    const r = await send("Runtime.evaluate", { expression: "document.body.innerText.replace(/\\s+/g,' ')", returnByValue: true });
    return r.result?.result?.value || "";
  } finally {
    ws.close();
    await fetch(`http://localhost:${PORT}/json/close/${t.id}`);
  }
}

for (const [label, url] of items) {
  const text = await pageText(url);
  const dates = [...new Set([...text.matchAll(DATE_RE)].map((m) => new Date(m[2]).toISOString().slice(0, 10)))]
    .sort().reverse();
  const unavailable = /content isn't available|Page isn't available/i.test(text);
  const verdict = unavailable ? "UNAVAILABLE logged out" : dates.length ? `newest ${dates.slice(0, 3).join(", ")}` : "no dated posts visible";
  console.log(`${label}\t${dates.length} dated posts\t${verdict}`);
}
