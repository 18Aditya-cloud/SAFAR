const API =
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000/api"


// ============================================================
// DASHBOARD
// ============================================================

export async function getDashboard() {
  const r = await fetch(`${API}/dashboard`)

  if (!r.ok) {
    throw new Error("Failed to load dashboard")
  }

  return r.json()
}


// ============================================================
// INVENTORY
// ============================================================

export async function getInventory() {
  const r = await fetch(`${API}/inventory`)

  if (!r.ok) {
    throw new Error("Failed to load inventory")
  }

  return r.json()
}


// ============================================================
// ASSETS
// ============================================================

export async function getAssets() {
  const r = await fetch(`${API}/assets`)

  if (!r.ok) {
    throw new Error("Failed to load assets")
  }

  return r.json()
}


// ============================================================
// CARGO
// ============================================================

export async function getCargo() {
  const r = await fetch(`${API}/cargo/`)

  if (!r.ok) {
    throw new Error("Failed to load cargo")
  }

  return r.json()
}


// ============================================================
// ROUTES
// ============================================================

export async function getRoutes() {
  const r = await fetch(`${API}/routes/`)

  if (!r.ok) {
    throw new Error("Failed to load routes")
  }

  return r.json()
}


// ============================================================
// STATIONS
// ============================================================

export async function getStations() {
  const r = await fetch(`${API}/routes/stations`)

  if (!r.ok) {
    throw new Error("Failed to load stations")
  }

  return r.json()
}


// ============================================================
// FACILITIES
// ============================================================

export async function getFacilities() {
  const r = await fetch(`${API}/routes/facilities`)

  if (!r.ok) {
    throw new Error("Failed to load facilities")
  }

  return r.json()
}


// ============================================================
// ROUTE SUMMARY
// ============================================================

export async function getRouteSummary() {
  const r = await fetch(`${API}/routes/summary`)

  if (!r.ok) {
    throw new Error("Failed to load route summary")
  }

  return r.json()
}


// ============================================================
// SOS
// ============================================================

export async function createSOS(payload) {
  const r = await fetch(`${API}/sos`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  })

  if (!r.ok) {
    throw new Error("Failed to create SOS")
  }

  return r.json()
}


// ============================================================
// SIMULATION
// ============================================================

export async function simulate(payload) {
  const r = await fetch(`${API}/simulate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  })

  if (!r.ok) {
    throw new Error("Simulation failed")
  }

  return r.json()
}