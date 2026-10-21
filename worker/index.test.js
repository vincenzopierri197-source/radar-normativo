import test from "node:test";
import assert from "node:assert/strict";
import { handleCommand, renderMarkets, publishedDay } from "./src/index.js";

const today = new Date().toISOString();
const archive = { updated_at: today, items: [
  { title: "Nuovo decreto fiscale", summary: "Misure IVA", url: "https://x.test/1", source_name: "GU", published_at: today, topics: ["fisco"] },
  { title: "Regolamento agricolo", summary: "Aziende", url: "https://x.test/2", source_name: "EUR-Lex", published_at: "2020-01-01T00:00:00+00:00", topics: ["agricoltura"] },
]};
const sources = { sources: [{ name: "Gazzetta Ufficiale", url: "https://x.test/feed" }] };

function memKV() {
  const m = new Map();
  return { get: async (k) => m.get(k) ?? null, put: async (k, v) => void m.set(k, v), delete: async (k) => void m.delete(k) };
}
const realFetch = globalThis.fetch;
test.before(() => {
  globalThis.fetch = async (url) => {
    const body = String(url).endsWith("archive.json") ? archive : String(url).endsWith("sources.json") ? sources : null;
    return new Response(JSON.stringify(body), { status: body ? 200 : 404 });
  };
});
test.after(() => { globalThis.fetch = realFetch; });

const env = () => ({ GITHUB_REPO: "o/r", GITHUB_BRANCH: "main", STATE: memKV() });

test("start, aiuto, fonti", async () => {
  const e = env();
  assert.match(await handleCommand("/start", 1, e), /pronto/);
  assert.match(await handleCommand("/aiuto@MioBot", 1, e), /\/ultime/);
  assert.match(await handleCommand("/fonti", 1, e), /Gazzetta Ufficiale/);
});

test("cerca, ultime, oggi, ieri, stato", async () => {
  const e = env();
  assert.match(await handleCommand("/cerca fiscale", 1, e), /decreto fiscale/);
  assert.match(await handleCommand("/ultime", 1, e), /Ultime pubblicazioni/);
  assert.match(await handleCommand("/oggi", 1, e), /decreto fiscale/);
  assert.doesNotMatch(await handleCommand("/ieri", 1, e), /decreto fiscale/);
  assert.match(await handleCommand("/ultimi7giorni", 1, e), /decreto fiscale/);
  assert.match(await handleCommand("/stato", 1, e), /Elementi in archivio: 2/);
});

test("filtri", async () => {
  const e = env();
  assert.match(await handleCommand("/filtri agricoltura", 1, e), /salvati: agricoltura/);
  const r = await handleCommand("/ultime", 1, e);
  assert.match(r, /agricolo/);
  assert.doesNotMatch(r, /fiscale/);
  assert.match(await handleCommand("/filtri off", 1, e), /disattivati/);
});

test("mercati con dati simulati e con errori", async () => {
  const ok = await renderMarkets(async () => ({ value: 1234.5, change: 1.2, currency: "USD", time: new Date() }));
  assert.match(ok, /1,234.5000 USD \(\+1.20%\)/);
  assert.match(ok, /prevalentemente positivo/);
  const ko = await renderMarkets(async () => { throw new Error("HTTP 429"); });
  assert.match(ko, /dato non disponibile/);
  assert.match(ko, /Dati insufficienti/);
});

test("data pubblicazione in fuso Roma", () => {
  assert.equal(publishedDay({ published_at: "2026-10-20T23:30:00+00:00" }), "2026-10-21");
});
