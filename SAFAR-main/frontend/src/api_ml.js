// AI/ML API helpers. Import alongside api.js. Adjust BASE if your api.js exports one.
const BASE = "http://localhost:8000/api";
const j = async (r) => { if (!r.ok) throw new Error(await r.text()); return r.json(); };
const post = (u, body) => fetch(`${BASE}${u}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(j);

export const getRouteRisks = (month) => fetch(`${BASE}/risks/routes${month ? `?month=${month}` : ""}`).then(j);
export const scoreRoute = (payload) => post("/risks/score", payload);
export const getInventoryForecast = (personnel = 60) => fetch(`${BASE}/risks/inventory?personnel=${personnel}`).then(j);
export const getAssetRisks = () => fetch(`${BASE}/risks/assets`).then(j);
export const triageSOS = (text) => post("/risks/triage", { text });
export const optimiseCargo = (payload = { source: "db" }) => post("/optimization/cargo", payload);
export const getRouteOptions = (origin, destination, riskAversion = 1) =>
  fetch(`${BASE}/optimization/routes?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&risk_aversion=${riskAversion}`).then(j);
export const getDigitalTwin = () => fetch(`${BASE}/digital-twin`).then(j);
export const runWhatIf = (scenario, resupplyInDays = 30) => post("/digital-twin/what-if", { scenario, resupply_in_days: resupplyInDays });
export const getSyncStatus = () => fetch(`${BASE}/sync/status`).then(j);
export const flushSync = (channelAvailable) => fetch(`${BASE}/sync/flush?channel_available=${channelAvailable}`, { method: "POST" }).then(j);
export const getModelMetrics = () => fetch(`${BASE}/reports/model-metrics`).then(j);
export const getSummary = () => fetch(`${BASE}/reports/summary`).then(j);
