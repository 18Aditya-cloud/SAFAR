const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api"

export async function getDashboard() {
  const r = await fetch(`${API}/dashboard`)
  return r.json()
}

export async function getInventory() {
  const r = await fetch(`${API}/inventory`)
  return r.json()
}

export async function getAssets() {
  const r = await fetch(`${API}/assets`)
  return r.json()
}

export async function createSOS(payload) {
  const r = await fetch(`${API}/sos`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  })
  return r.json()
}

export async function simulate(payload) {
  const r = await fetch(`${API}/simulate`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  })
  return r.json()
}
