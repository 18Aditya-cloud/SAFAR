import { useEffect, useState } from "react"
import L from "leaflet"
import { GeoJSON, MapContainer, useMap } from "react-leaflet"
import { CircleMarker, Polyline, useMapEvents } from "react-leaflet"
import { getDashboard, getInventory, getAssets, createSOS, simulate } from "./api"

const scenarios = ["Cargo delay", "Vehicle failure", "Fuel shortage", "Food shortage", "Severe weather", "Medical emergency"]

const antarcticaStyle = feature => ({
  color: feature?.properties?.type === "continent" ? "#d9eef0" : "#64d8e9",
  weight: feature?.properties?.type === "continent" ? 1.5 : 2,
  fillColor: "#b9d7d9",
  fillOpacity: 0.86
})

function expeditionMarker(feature, latitudeLongitude) {
  const isCenter = feature?.properties?.type === "center"
  return L.circleMarker(latitudeLongitude, {
    radius: isCenter ? 8 : 6,
    color: isCenter ? "#ffbd66" : "#62e5ef",
    weight: 2,
    fillColor: isCenter ? "#ff7d57" : "#164c62",
    fillOpacity: 1
  }).bindTooltip(feature.properties.name)
}

function degreesToRadians(value) {
  return value * Math.PI / 180
}

function navigationDistance(from, to) {
  const earthRadius = 6371
  const latitudeDelta = degreesToRadians(to[0] - from[0])
  const longitudeDelta = degreesToRadians(to[1] - from[1])
  const latitude = degreesToRadians((from[0] + to[0]) / 2)
  const x = longitudeDelta * Math.cos(latitude)
  const y = latitudeDelta
  return earthRadius * Math.sqrt(x * x + y * y)
}

function navigationBearing(from, to) {
  const latitude = degreesToRadians(to[0] - from[0])
  const longitude = degreesToRadians(to[1] - from[1])
  const fromLatitude = degreesToRadians(from[0])
  const toLatitude = degreesToRadians(to[0])
  const bearing = Math.atan2(
    Math.sin(longitude) * Math.cos(toLatitude),
    Math.cos(fromLatitude) * Math.sin(toLatitude) - Math.sin(fromLatitude) * Math.cos(toLatitude) * Math.cos(longitude)
  ) * 180 / Math.PI
  return (bearing + 360) % 360
}

function Stat({label, value, sub}) {
  return <div className="card stat"><div className="muted">{label}</div><div className="big">{value}</div><div className="muted">{sub}</div></div>
}

function FitAntarctica({data}) {
  const map = useMap()

  useEffect(() => {
    if (data) map.fitBounds([[-89, -180], [-60, 180]], {padding: [12, 12]})
  }, [data, map])

  return null
}

function NavigationLayer({position, destination, onDestination}) {
  const map = useMapEvents({
    click(event) {
      onDestination([event.latlng.lat, event.latlng.lng])
    }
  })

  useEffect(() => {
    if (position) map.setView(position, Math.max(map.getZoom(), 3))
  }, [map, position])

  return (
    <>
      {position && <CircleMarker center={position} radius={9} pathOptions={{color: "#fff", weight: 3, fillColor: "#25d6a2", fillOpacity: 1}}><span /></CircleMarker>}
      {destination && <CircleMarker center={destination} radius={8} pathOptions={{color: "#fff", weight: 2, fillColor: "#ff765f", fillOpacity: 1}} />}
      {position && destination && <Polyline positions={[position, destination]} pathOptions={{color: "#ffbd66", weight: 3, dashArray: "8 8"}} />}
    </>
  )
}

export default function App() {
  const [dash, setDash] = useState(null)
  const [inventory, setInventory] = useState([])
  const [assets, setAssets] = useState([])
  const [scenario, setScenario] = useState("Cargo delay")
  const [simulation, setSimulation] = useState(null)
  const [sosMessage, setSosMessage] = useState("")
  const [mapData, setMapData] = useState(null)
  const [position, setPosition] = useState(null)
  const [destination, setDestination] = useState(null)
  const [locationStatus, setLocationStatus] = useState("Location not started")

  async function refresh() {
    setDash(await getDashboard())
    setInventory(await getInventory())
    setAssets(await getAssets())
  }

  useEffect(() => {
    refresh()
    fetch("/data/polar.geojson").then(response => response.json()).then(setMapData).catch(() => {})
  }, [])

  async function runSimulation() {
    setSimulation(await simulate({scenario, duration_days: 7}))
  }

  async function triggerSOS() {
    const result = await createSOS({
      incident_type: "Medical Emergency",
      severity: "CRITICAL",
      location: "Field Camp B",
      latitude: -70.77,
      longitude: 11.95,
      description: "Prototype offline SOS event"
    })
    setSosMessage(result.message)
  }

  function locateScientist() {
    if (!navigator.geolocation) {
      setLocationStatus("GPS is not available on this device")
      return
    }

    setLocationStatus("Requesting GPS position...")
    navigator.geolocation.getCurrentPosition(
      result => {
        setPosition([result.coords.latitude, result.coords.longitude])
        setLocationStatus(`GPS accuracy ±${Math.round(result.coords.accuracy)} m`)
      },
      error => setLocationStatus(error.code === error.PERMISSION_DENIED ? "Location permission was denied" : "Unable to get GPS position"),
      {enableHighAccuracy: true, timeout: 15000, maximumAge: 10000}
    )
  }

  if (!dash && !mapData) return <div className="loading">Loading SAFAR local system...</div>

  return (
    <div className="app">
      <header>
        <div>
          <div className="brand">SAFAR</div>
          <div className="subtitle">Smart Antarctic Expedition & Resource Management</div>
        </div>
        <div className="offline"><span>●</span> OFFLINE-FIRST</div>
      </header>

      <main>
        <section className="hero">
          <div>
            <p className="eyebrow">EXPEDITION COMMAND</p>
            <h1>Operational intelligence,<br/>even without connectivity.</h1>
            <p className="muted">Predict · Optimize · Simulate · Respond</p>
          </div>
          <button className="sos" onClick={triggerSOS}>🚨 SOS</button>
        </section>

        <section className="card mapCard">
          <div className="mapHeader">
            <div>
              <div className="sectionTitle">Offline Antarctica Map</div>
              <div className="muted">Local vector chart · station positions and operations zone</div>
            </div>
            <span className="mapStatus">LOCAL DATA</span>
          </div>
          <div className="navigationTools">
            <button className="locateButton" onClick={locateScientist}>◎ Locate me</button>
            <div className="locationReadout"><strong>{locationStatus}</strong><span>Tap anywhere on the map to set a destination</span></div>
            {position && destination && <div className="routeReadout"><strong>{navigationDistance(position, destination).toFixed(1)} km</strong><span>heading {Math.round(navigationBearing(position, destination))}°</span></div>}
          </div>
          <MapContainer className="map" center={[-78, 0]} zoom={2} minZoom={2} maxZoom={6} scrollWheelZoom>
            <FitAntarctica data={mapData} />
            <NavigationLayer position={position} destination={destination} onDestination={setDestination} />
            {mapData && <GeoJSON data={mapData} style={antarcticaStyle} pointToLayer={expeditionMarker} />}
          </MapContainer>
          <div className="mapLegend"><span><i className="legendDot scientist" /> Your position</span><span><i className="legendDot destination" /> Destination</span><span>Direct-line estimate only · check terrain and crevasse data before travel</span></div>
        </section>

        {sosMessage && <div className="alert">{sosMessage}</div>}

        {dash && <section className="stats">
          <Stat label="Expeditions" value={dash.expeditions} sub="active / planned" />
          <Stat label="Inventory Items" value={dash.inventory_items} sub="locally tracked" />
          <Stat label="Assets" value={dash.assets} sub="monitored locally" />
          <Stat label="Open SOS" value={dash.open_sos} sub="queued / active" />
        </section>}

        {dash && <section className="grid">
          <div className="card">
            <div className="sectionTitle">Inventory Intelligence</div>
            <div className="table">
              {inventory.map(x => (
                <div className="row" key={x.id}>
                  <div><strong>{x.item}</strong><div className="muted">{x.location} · {x.category}</div></div>
                  <div>{x.days_left} days</div>
                  <span className={x.status === "CRITICAL" ? "pill danger" : "pill ok"}>{x.status}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="sectionTitle">What-If Simulation</div>
            <p className="muted">Test a disruption and calculate its operational impact.</p>
            <select value={scenario} onChange={e => setScenario(e.target.value)}>
              {scenarios.map(s => <option key={s}>{s}</option>)}
            </select>
            <button className="primary" onClick={runSimulation}>Run Simulation</button>
            {simulation && (
              <div className="simulation">
                <div className="impact">{simulation.impact_score}% impact</div>
                <div>Risk: <strong>{simulation.risk_before} → {simulation.risk_after}</strong></div>
                <p>{simulation.recommendation}</p>
              </div>
            )}
          </div>
        </section>}

        {dash && <section className="card">
          <div className="sectionTitle">Asset Monitoring</div>
          <div className="assetGrid">
            {assets.map(a => (
              <div className="asset" key={a.id}>
                <strong>{a.name}</strong>
                <span>{a.asset_type}</span>
                <span>{a.location}</span>
                <span className={a.risk_score >= 50 ? "risk high" : "risk"}>Risk {a.risk_score}%</span>
              </div>
            ))}
          </div>
        </section>}
      </main>
    </div>
  )
}
