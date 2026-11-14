// usage: node probe.mjs urls.txt out.json   (one "label<TAB>url" per line; sequential, one tab)
import { readFileSync, writeFileSync } from "node:fs";
const [listFile, outFile] = process.argv.slice(2);
const PORT = process.env.CDP_PORT || 9333;
const items = readFileSync(listFile, "utf8").trim().split("\n").map((l) => l.split("\t"));

const target = await (await fetch(`http://localhost:${PORT}/json/new?about:blank`, { method: "PUT" })).json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
let id = 0;
const pending = new Map();
let mainStatus = null;
ws.onmessage = (m) => {
  const msg = JSON.parse(m.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  else if (msg.method === "Network.responseReceived" && msg.params.type === "Document" && mainStatus === null) {
    mainStatus = msg.params.response.status;
  }
};
const send = (method, params = {}) => new Promise((resolve) => {
  const i = ++id; pending.set(i, resolve); ws.send(JSON.stringify({ id: i, method, params }));
});
const pause = (ms) => new Promise((r) => setTimeout(r, ms));
await send("Page.enable");
await send("Network.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });

const EXTRACT = `(() => {
  const meta = (n) => document.querySelector('meta[property="' + n + '"], meta[name="' + n + '"]')?.content || null;
  return {
    finalUrl: location.href,
    title: document.title,
    ogTitle: meta("og:title"),
    description: meta("og:description") || meta("description"),
    text: (document.body?.innerText || "").replace(/\\s+/g, " ").slice(0, 700),
  };
})()`;

const results = [];
for (const [label, url] of items) {
  mainStatus = null;
  const started = Date.now();
  await send("Page.navigate", { url });
  await pause(7000);
  const r = await send("Runtime.evaluate", { expression: EXTRACT, returnByValue: true });
  results.push({ label, url, status: mainStatus, ms: Date.now() - started, ...(r.result?.result?.value || { error: JSON.stringify(r) }) });
  console.log(label, mainStatus, results.at(-1).title?.slice(0, 80));
}
writeFileSync(outFile, JSON.stringify(results, null, 1));
ws.close();
await fetch(`http://localhost:${PORT}/json/close/${target.id}`);
