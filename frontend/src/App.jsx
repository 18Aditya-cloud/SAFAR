import { useEffect, useState } from "react"
import L from "leaflet"

import {
  GeoJSON,
  MapContainer,
  useMap,
  CircleMarker,
  Polyline,
  useMapEvents,
  ScaleControl,
  ZoomControl,
  Popup,
} from "react-leaflet"

import OfflineAntarcticMap from "./components/OfflineAntarcticMap"

import {
  getDashboard,
  getInventory,
  getAssets,
  getCargo,
  getRoutes,
  getStations,
  getFacilities,
  getRouteSummary,
  createSOS,
  simulate
} from "./api"


// ============================================================
// SCENARIOS
// ============================================================

const scenarios = [
  "Cargo delay",
  "Vehicle failure",
  "Fuel shortage",
  "Food shortage",
  "Severe weather",
  "Medical emergency"
]


// ============================================================
// DISTANCE
// ============================================================

function degreesToRadians(value) {
  return value * Math.PI / 180
}


function navigationDistance(from, to) {
  const earthRadius = 6371

  const latitudeDelta =
    degreesToRadians(
      to[0] - from[0]
    )

  const longitudeDelta =
    degreesToRadians(
      to[1] - from[1]
    )

  const latitude =
    degreesToRadians(
      (from[0] + to[0]) / 2
    )

  const x =
    longitudeDelta *
    Math.cos(latitude)

  const y =
    latitudeDelta

  return (
    earthRadius *
    Math.sqrt(
      x * x +
      y * y
    )
  )
}


// ============================================================
// BEARING
// ============================================================

function navigationBearing(from, to) {
  const latitude =
    degreesToRadians(
      to[0] - from[0]
    )

  const longitude =
    degreesToRadians(
      to[1] - from[1]
    )

  const fromLatitude =
    degreesToRadians(
      from[0]
    )

  const toLatitude =
    degreesToRadians(
      to[0]
    )

  const bearing =
    Math.atan2(
      Math.sin(longitude) *
        Math.cos(toLatitude),

      Math.cos(fromLatitude) *
        Math.sin(toLatitude) -

      Math.sin(fromLatitude) *
        Math.cos(toLatitude) *
        Math.cos(longitude)
    ) *
    180 /
    Math.PI

  return (
    bearing + 360
  ) % 360
}


// ============================================================
// STAT CARD
// ============================================================

function Stat({
  label,
  value,
  sub
}) {
  return (
    <div className="card stat">

      <div className="muted">
        {label}
      </div>

      <div className="big">
        {value}
      </div>

      <div className="muted">
        {sub}
      </div>

    </div>
  )
}


// ============================================================
// FIT ANTARCTICA
// ============================================================

function FitAntarctica() {
  const map = useMap()

  useEffect(() => {
    map.fitBounds(
      [
        [-89, -180],
        [-58, 180]
      ],
      {
        padding: [20, 20]
      }
    )
  }, [map])

  return null
}


// ============================================================
// NAVIGATION LAYER
// ============================================================

function NavigationLayer({
  position,
  destination,
  onDestination
}) {
  const map = useMapEvents({

    click(event) {
      onDestination([
        event.latlng.lat,
        event.latlng.lng
      ])
    }

  })

  useEffect(() => {
    if (position) {
      map.setView(
        position,
        Math.max(
          map.getZoom(),
          3
        )
      )
    }
  }, [
    map,
    position
  ])

  return (
    <>
      {position && (
        <CircleMarker
          center={position}
          radius={9}
          pathOptions={{
            color: "#ffffff",
            weight: 3,
            fillColor: "#25d6a2",
            fillOpacity: 1
          }}
        >
        </CircleMarker>
      )}

      {destination && (
        <CircleMarker
          center={destination}
          radius={8}
          pathOptions={{
            color: "#ffffff",
            weight: 2,
            fillColor: "#ff765f",
            fillOpacity: 1
          }}
        >
        </CircleMarker>
      )}

      {position && destination && (
        <Polyline
          positions={[
            position,
            destination
          ]}
          pathOptions={{
            color: "#ffbd66",
            weight: 3,
            dashArray: "8 8",
            opacity: 0.9
          }}
        />
      )}
    </>
  )
}


// ============================================================
// ROUTE STYLE
// ============================================================

function getRouteStyle(
  riskLevel
) {
  if (
    riskLevel === "HIGH"
  ) {
    return {
      color: "#ff5f56",
      weight: 5,
      opacity: 0.95
    }
  }

  if (
    riskLevel === "MEDIUM"
  ) {
    return {
      color: "#ffbd66",
      weight: 4,
      opacity: 0.95
    }
  }

  return {
    color: "#25d6a2",
    weight: 4,
    opacity: 0.95
  }
}


// ============================================================
// ROUTE LAYER
// ============================================================

function RouteLayer({ routes, cargo = [] }) {
  if (!routes || !routes.features) return null

  const getCargoForRoute = (properties) => {
    const routeText = [
      properties.name,
      properties.from,
      properties.to,
      properties.origin,
      properties.destination,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()

    return cargo.filter(item => {
      const cargoText = [
        item.origin,
        item.destination,
        item.current_location,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()

      return (
        routeText.includes(item.origin?.toLowerCase?.() || "___") ||
        routeText.includes(item.destination?.toLowerCase?.() || "___") ||
        cargoText.includes(properties.name?.toLowerCase?.() || "___")
      )
    })
  }

  return (
    <GeoJSON
      data={routes}
      style={feature => {
        const risk = feature?.properties?.risk_level || "LOW"
        return getRouteStyle(risk)
      }}
      onEachFeature={(feature, layer) => {
        const properties = feature.properties || {}
        const routeCargo = getCargoForRoute(properties)

        const cargoHtml =
          routeCargo.length > 0
            ? `
              <hr style="margin:8px 0"/>
              <strong>Associated Cargo</strong>
              ${routeCargo
                .slice(0, 5)
                .map(
                  item => `
                    <div style="margin-top:5px">
                      <strong>${item.cargo_code}</strong>
                      — ${item.description}
                      <br/>
                      <span>Status: ${item.status}</span>
                    </div>
                  `
                )
                .join("")}
            `
            : `
              <hr style="margin:8px 0"/>
              <span style="color:#777">No linked cargo records</span>
            `

        layer.bindPopup(`
          <div style="min-width:230px">
            <strong style="font-size:15px">
              ${properties.name || "Transport Route"}
            </strong>

            <br/><br/>

            <strong>Mode:</strong>
            ${properties.mode || properties.type || "N/A"}

            <br/>

            <strong>Risk:</strong>
            ${properties.risk_level || "LOW"}

            <br/>

            <strong>Status:</strong>
            ${properties.status || "UNKNOWN"}

            <br/>

            <strong>Estimated:</strong>
            ${properties.estimated_days || "N/A"} days

            ${cargoHtml}
          </div>
        `)

        layer.on({
          mouseover: event => {
            event.target.setStyle({
              weight: 5,
              opacity: 1,
            })
          },
          mouseout: event => {
            event.target.setStyle(
              getRouteStyle(properties.risk_level || "LOW")
            )
          },
        })
      }}
    />
  )
}


// ============================================================
// STATION LAYER
// ============================================================

function StationLayer({
  stations,
  cargo = [],
  inventory = [],
  assets = [],
}) {
  if (!stations || !stations.features) return null

  const getStationCargo = stationName => {
    const name = stationName.toLowerCase()

    return cargo.filter(item => {
      const destination = String(item.destination || "").toLowerCase()
      const location = String(item.current_location || "").toLowerCase()

      return (
        destination.includes(name) ||
        location.includes(name)
      )
    })
  }

  const getStationInventory = stationName => {
    const name = stationName.toLowerCase()

    return inventory.filter(item =>
      String(item.location || "")
        .toLowerCase()
        .includes(name)
    )
  }

  const getStationAssets = stationName => {
    const name = stationName.toLowerCase()

    return assets.filter(item =>
      String(item.location || "")
        .toLowerCase()
        .includes(name)
    )
  }

  return (
    <>
      {stations.features.map(feature => {
        const coordinates = feature.geometry?.coordinates

        if (!coordinates || coordinates.length < 2) {
          return null
        }

        const [longitude, latitude] = coordinates
        const properties = feature.properties || {}

        const stationName = properties.name || "Station"

        const stationCargo = getStationCargo(stationName)
        const stationInventory = getStationInventory(stationName)
        const stationAssets = getStationAssets(stationName)

        return (
          <CircleMarker
            key={properties.id || stationName}
            center={[latitude, longitude]}
            radius={10}
            pathOptions={{
              color: "#ffffff",
              weight: 2,
              fillColor: "#2c8cff",
              fillOpacity: 1,
            }}
          >
            <Popup>
              <div style={{ minWidth: "270px" }}>
                <strong style={{ fontSize: "16px" }}>
                  {stationName}
                </strong>

                <br />

                <span>
                  {properties.type || "RESEARCH_STATION"}
                </span>

                <hr style={{ margin: "8px 0" }} />

                <div>
                  <strong>Operational Status:</strong>{" "}
                  {properties.status || "UNKNOWN"}
                </div>

                <div>
                  <strong>Personnel Capacity:</strong>{" "}
                  {properties.personnel_capacity ?? "N/A"}
                </div>

                <hr style={{ margin: "8px 0" }} />

                <strong>Cargo</strong>

                {stationCargo.length > 0 ? (
                  <div style={{ marginTop: "5px" }}>
                    {stationCargo.slice(0, 5).map(item => (
                      <div
                        key={item.id || item.cargo_code}
                        style={{ marginBottom: "5px" }}
                      >
                        <strong>{item.cargo_code}</strong>{" "}
                        — {item.description}
                        <br />
                        <span>
                          {item.quantity} {item.category}
                        </span>
                        <br />
                        <span>Status: {item.status}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: "#777", marginTop: "4px" }}>
                    No cargo records
                  </div>
                )}

                <hr style={{ margin: "8px 0" }} />

                <strong>Inventory</strong>

                {stationInventory.length > 0 ? (
                  <div style={{ marginTop: "5px" }}>
                    {stationInventory.slice(0, 5).map(item => (
                      <div
                        key={item.id || item.item}
                        style={{ marginBottom: "4px" }}
                      >
                        <strong>{item.item}</strong>
                        <br />
                        {item.quantity} {item.unit}
                        <br />
                        <span>
                          Consumption: {item.daily_consumption}/day
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: "#777", marginTop: "4px" }}>
                    No inventory records
                  </div>
                )}

                <hr style={{ margin: "8px 0" }} />

                <strong>Assets</strong>

                {stationAssets.length > 0 ? (
                  <div style={{ marginTop: "5px" }}>
                    {stationAssets.slice(0, 5).map(item => (
                      <div
                        key={item.id || item.name}
                        style={{ marginBottom: "4px" }}
                      >
                        <strong>{item.name}</strong>
                        <br />
                        {item.asset_type}
                        <br />
                        Status: {item.status}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: "#777", marginTop: "4px" }}>
                    No asset records
                  </div>
                )}
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </>
  )
}


// ============================================================
// FACILITY LAYER
// ============================================================

function FacilityLayer({
  facilities
}) {
  if (
    !facilities ||
    !facilities.features
  ) {
    return null
  }

  return (
    <>
      {facilities.features.map(
        feature => {

          const coordinates =
            feature.geometry?.coordinates

          if (
            !coordinates ||
            coordinates.length < 2
          ) {
            return null
          }

          const [
            longitude,
            latitude
          ] = coordinates

          const properties =
            feature.properties || {}

          return (
            <CircleMarker
              key={
                properties.id ||
                properties.name
              }
              center={[
                latitude,
                longitude
              ]}
              radius={7}
              pathOptions={{
                color: "#fff4d6",
                weight: 2,
                fillColor: "#ff7d57",
                fillOpacity: 1
              }}
            >
              <div />
            </CircleMarker>
          )
        }
      )}
    </>
  )
}

// ============================================================
// BETTER STATION / FACILITY POPUPS
// ============================================================

function OperationalMarkers({
  stations,
  facilities
}) {
  return (
    <>
      {stations?.features?.map(
        feature => {

          const coordinates =
            feature.geometry
              ?.coordinates

          if (
            !coordinates ||
            coordinates.length < 2
          ) {
            return null
          }

          const [
            longitude,
            latitude
          ] = coordinates

          const properties =
            feature.properties || {}

          return (
            <CircleMarker
              key={`ops-station-${properties.id || properties.name}`}
              center={[
                latitude,
                longitude
              ]}
              radius={9}
              pathOptions={{
                color: "#ffffff",
                weight: 2,
                fillColor: "#2c8cff",
                fillOpacity: 1
              }}
            >
              <div />

            </CircleMarker>
          )
        }
      )}
    </>
  )
}


// ============================================================
// CARGO SUMMARY
// ============================================================

function CargoSummary({
  cargo
}) {
  const total =
    cargo.length

  const critical =
    cargo.filter(
      item =>
        item.priority ===
        "CRITICAL"
    ).length

  const transit =
    cargo.filter(
      item =>
        item.status ===
        "IN_TRANSIT"
    ).length

  return (
    <div className="card">

      <div className="sectionTitle">
        Cargo Operations
      </div>

      <div className="assetGrid">

        <div className="asset">
          <strong>
            {total}
          </strong>

          <span>
            Cargo consignments
          </span>
        </div>

        <div className="asset">
          <strong>
            {critical}
          </strong>

          <span>
            Critical priority
          </span>
        </div>

        <div className="asset">
          <strong>
            {transit}
          </strong>

          <span>
            In transit
          </span>
        </div>

      </div>

      {cargo.length > 0 && (
        <div className="table">

          {cargo.map(item => (
            <div
              className="row"
              key={item.id}
            >

              <div>
                <strong>
                  {item.cargo_code}
                </strong>

                <div className="muted">
                  {item.description}
                  {" · "}
                  {item.destination}
                </div>
              </div>

              <div>
                {item.transport_mode}
              </div>

              <span
                className={
                  item.priority ===
                  "CRITICAL"
                    ? "pill danger"
                    : "pill ok"
                }
              >
                {item.priority}
              </span>

            </div>
          ))}

        </div>
      )}

    </div>
  )
}


// ============================================================
// OFFLINE MAP STATUS
// ============================================================

function OfflineMapStatus() {
  return (
    <div
      style={{
        position: "absolute",
        top: "14px",
        right: "14px",
        zIndex: 1000,
        pointerEvents: "none"
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "10px 14px",
          borderRadius: "12px",
          background: "rgba(3, 15, 24, 0.92)",
          border: "1px solid rgba(37, 214, 162, 0.35)",
          boxShadow:
            "0 8px 30px rgba(0,0,0,0.35)",
          backdropFilter: "blur(8px)"
        }}
      >

        <span
          style={{
            width: "9px",
            height: "9px",
            borderRadius: "50%",
            background: "#25d6a2",
            boxShadow:
              "0 0 12px rgba(37,214,162,0.9)"
          }}
        />

        <div>

          <div
            style={{
              color: "#7ef0c5",
              fontSize: "11px",
              fontWeight: 800,
              letterSpacing: "0.12em"
            }}
          >
            OFFLINE MAP
          </div>

          <div
            style={{
              color: "#94a9b4",
              fontSize: "10px",
              marginTop: "2px"
            }}
          >
            Local geographic data
          </div>

        </div>

      </div>
    </div>
  )
}


// ============================================================
// MAP LEGEND
// ============================================================

function MapLegend() {
  return (
    <div className="mapLegend">

      <span>
        <i className="legendDot scientist" />
        Your position
      </span>

      <span>
        <i className="legendDot destination" />
        Destination
      </span>

      <span>
        <i
          className="legendLine"
          style={{
            background: "#25d6a2"
          }}
        />
        Low risk
      </span>

      <span>
        <i
          className="legendLine"
          style={{
            background: "#ffbd66"
          }}
        />
        Medium risk
      </span>

      <span>
        <i
          className="legendLine"
          style={{
            background: "#ff5f56"
          }}
        />
        High risk
      </span>

      <span>
        <i
          className="legendDot station"
        />
        Station
      </span>

      <span>
        <i
          className="legendDot facility"
        />
        Facility
      </span>

    </div>
  )
}


// ============================================================
// MAIN APPLICATION
// ============================================================

export default function App() {

  const [dash, setDash] =
    useState(null)

  const [inventory, setInventory] =
    useState([])

  const [assets, setAssets] =
    useState([])

  const [cargo, setCargo] =
    useState([])

  const [routes, setRoutes] =
    useState(null)

  const [stations, setStations] =
    useState(null)

  const [facilities, setFacilities] =
    useState(null)

  const [routeSummary, setRouteSummary] =
    useState(null)

  const [scenario, setScenario] =
    useState("Cargo delay")

  const [simulation, setSimulation] =
    useState(null)

  const [sosMessage, setSosMessage] =
    useState("")

  const [position, setPosition] =
    useState(null)

  const [destination, setDestination] =
    useState(null)

  const [locationStatus, setLocationStatus] =
    useState(
      "Location not started"
    )

  const [routeLoading, setRouteLoading] =
    useState(true)

  const [routeError, setRouteError] =
    useState("")


  // ==========================================================
  // REFRESH DATA
  // ==========================================================

  async function refresh() {
    try {

      const [
        dashboardData,
        inventoryData,
        assetsData,
        cargoData,
        routesData,
        stationsData,
        facilitiesData,
        summaryData
      ] = await Promise.all([

        getDashboard(),

        getInventory(),

        getAssets(),

        getCargo(),

        getRoutes(),

        getStations(),

        getFacilities(),

        getRouteSummary()

      ])

      setDash(
        dashboardData
      )

      setInventory(
        inventoryData
      )

      setAssets(
        assetsData
      )

      setCargo(
        cargoData
      )

      setRoutes(
        routesData
      )

      setStations(
        stationsData
      )

      setFacilities(
        facilitiesData
      )

      setRouteSummary(
        summaryData
      )

      setRouteError("")

    } catch (error) {

      console.error(
        "SAFAR data loading error:",
        error
      )

      setRouteError(
        error.message ||
        "Unable to load local SAFAR data"
      )

    } finally {

      setRouteLoading(false)

    }
  }


  // ==========================================================
  // INITIAL LOAD
  // ==========================================================

  useEffect(() => {
    refresh()
  }, [])


  // ==========================================================
  // SIMULATION
  // ==========================================================

  async function runSimulation() {
    try {

      const result =
        await simulate({
          scenario,
          duration_days: 7
        })

      setSimulation(
        result
      )

    } catch (error) {

      console.error(
        "Simulation error:",
        error
      )

    }
  }


  // ==========================================================
  // SOS
  // ==========================================================

  async function triggerSOS() {
    try {

      const result =
        await createSOS({

          incident_type:
            "Medical Emergency",

          severity:
            "CRITICAL",

          location:
            "Field Camp B",

          latitude:
            -70.77,

          longitude:
            11.95,

          description:
            "Prototype offline SOS event"

        })

      setSosMessage(
        result.message
      )

    } catch (error) {

      console.error(
        "SOS transmission unavailable:",
        error
      )

      setSosMessage(
        "SOS queued locally"
      )

    }
  }


  // ==========================================================
  // GPS
  // ==========================================================

  function locateScientist() {

    if (
      !navigator.geolocation
    ) {

      setLocationStatus(
        "GPS is not available on this device"
      )

      return
    }

    setLocationStatus(
      "Requesting GPS position..."
    )

    navigator.geolocation
      .getCurrentPosition(

        result => {

          setPosition([
            result.coords.latitude,
            result.coords.longitude
          ])

          setLocationStatus(
            `GPS accuracy ±${Math.round(
              result.coords.accuracy
            )} m`
          )

        },

        error => {

          setLocationStatus(
            error.code ===
              error.PERMISSION_DENIED
              ? "Location permission was denied"
              : "Unable to get GPS position"
          )

        },

        {
          enableHighAccuracy:
            true,

          timeout:
            15000,

          maximumAge:
            10000
        }
      )
  }


  // ==========================================================
  // LOADING
  // ==========================================================

  if (!dash) {
    return (
      <div className="loading">
        Loading SAFAR local system...
      </div>
    )
  }


  // ==========================================================
  // UI
  // ==========================================================

  return (

    <div className="app">

      {/* ====================================================
          HEADER
      ==================================================== */}

      <header>

        <div>

          <div className="brand">
            SAFAR
          </div>

          <div className="subtitle">
            Smart Antarctic Expedition
            & Resource Management
          </div>

        </div>

        <div className="offline">
          <span>●</span>
          OFFLINE-FIRST
        </div>

      </header>


      <main>

        {/* ==================================================
            HERO
        ================================================== */}

        <section className="hero">

          <div>

            <p className="eyebrow">
              EXPEDITION COMMAND
            </p>

            <h1>
              Operational intelligence,
              <br />
              even without connectivity.
            </h1>

            <p className="muted">
              Predict · Optimize · Simulate · Respond
            </p>

          </div>

          <button
            className="sos"
            onClick={
              triggerSOS
            }
          >
            🚨 SOS
          </button>

        </section>


        {/* ==================================================
            ROUTE STATUS
        ================================================== */}

        <section className="stats">

          <Stat
            label="Routes"
            value={
              routeSummary
                ?.route_count ?? "—"
            }
            sub="local logistics network"
          />

          <Stat
            label="Stations"
            value={
              routeSummary
                ?.station_count ?? "—"
            }
            sub="Antarctic stations"
          />

          <Stat
            label="Facilities"
            value={
              routeSummary
                ?.facility_count ?? "—"
            }
            sub="logistics facilities"
          />

          <Stat
            label="Cargo"
            value={
              cargo.length
            }
            sub="locally tracked"
          />

        </section>


        {/* ==================================================
            MAP
        ================================================== */}

        <section className="card mapCard">

          <div className="mapHeader">

            <div>

              <div className="sectionTitle">
                Antarctic Logistics Network
              </div>

              <div className="muted">
                Offline Antarctic operations map
              </div>

            </div>

            <span className="mapStatus">
              {routeLoading
                ? "LOADING LOCAL DATA"
                : "● OFFLINE MAP"}
            </span>

          </div>


          {/* MAP CONTROLS */}

          <div className="navigationTools">

            <button
              className="locateButton"
              onClick={
                locateScientist
              }
            >
              ◎ Locate me
            </button>

            <div className="locationReadout">

              <strong>
                {locationStatus}
              </strong>

              <span>
                Tap anywhere on the map
                to set a destination
              </span>

            </div>

            {position &&
              destination && (

                <div className="routeReadout">

                  <strong>
                    {navigationDistance(
                      position,
                      destination
                    ).toFixed(1)}
                    {" "}km
                  </strong>

                  <span>
                    heading{" "}
                    {Math.round(
                      navigationBearing(
                        position,
                        destination
                      )
                    )}
                    °
                  </span>

                </div>

              )}

          </div>


          {/* =================================================
              OFFLINE MAP
          ================================================= */}

          <div
            style={{
              position: "relative"
            }}
          >

            <MapContainer
              className="map"
              center={[
                -78,
                0
              ]}
              zoom={2}
              minZoom={2}
              maxZoom={6}
              preferCanvas={true}
              scrollWheelZoom={true}
              zoomControl={false}
              maxBounds={[
                [-90, -180],
                [-55, 180]
              ]}
              maxBoundsViscosity={0.85}
            >

              {/* Real local Antarctic geography */}

              <OfflineAntarcticMap />


              {/* Fit the polar map */}

              <FitAntarctica />


              {/* Leaflet scale */}

              <ScaleControl
                position="bottomleft"
                imperial={false}
              />

              <ZoomControl
                position="bottomright"
              />


              {/* GPS navigation */}

              <NavigationLayer
                position={position}
                destination={destination}
                onDestination={
                  setDestination
                }
              />


              {/* SAFAR logistics routes */}

              <RouteLayer
  routes={routes}
  cargo={cargo}
/>

<StationLayer
  stations={stations}
  cargo={cargo}
  inventory={inventory}
  assets={assets}
/>

<FacilityLayer
  facilities={facilities}
/>

            </MapContainer>


            {/* OFFLINE STATUS */}

            <OfflineMapStatus />

          </div>


          {/* LEGEND */}

          <MapLegend />

        </section>


        {/* ==================================================
            ERROR
        ================================================== */}

        {routeError && (

          <div className="alert">

            Local data warning:
            {" "}
            {routeError}

          </div>

        )}


        {/* ==================================================
            SOS MESSAGE
        ================================================== */}

        {sosMessage && (

          <div className="alert">
            {sosMessage}
          </div>

        )}


        {/* ==================================================
            DASHBOARD
        ================================================== */}

        {dash && (

          <section className="stats">

            <Stat
              label="Expeditions"
              value={
                dash.expeditions
              }
              sub="active / planned"
            />

            <Stat
              label="Inventory Items"
              value={
                dash.inventory_items
              }
              sub="locally tracked"
            />

            <Stat
              label="Assets"
              value={
                dash.assets
              }
              sub="monitored locally"
            />

            <Stat
              label="Open SOS"
              value={
                dash.open_sos
              }
              sub="queued / active"
            />

          </section>

        )}


        {/* ==================================================
            CARGO
        ================================================== */}

        <CargoSummary
          cargo={cargo}
        />


        {/* ==================================================
            INVENTORY + SIMULATION
        ================================================== */}

        {dash && (

          <section className="grid">

            {/* INVENTORY */}

            <div className="card">

              <div className="sectionTitle">
                Inventory Intelligence
              </div>

              <div className="table">

                {inventory.map(
                  x => (

                    <div
                      className="row"
                      key={x.id}
                    >

                      <div>

                        <strong>
                          {x.item}
                        </strong>

                        <div className="muted">

                          {x.location}
                          {" · "}
                          {x.category}

                        </div>

                      </div>

                      <div>
                        {x.days_left} days
                      </div>

                      <span
                        className={
                          x.status ===
                          "CRITICAL"
                            ? "pill danger"
                            : "pill ok"
                        }
                      >
                        {x.status}
                      </span>

                    </div>

                  )
                )}

              </div>

            </div>


            {/* SIMULATION */}

            <div className="card">

              <div className="sectionTitle">
                What-If Simulation
              </div>

              <p className="muted">
                Test a disruption and
                calculate its operational
                impact.
              </p>

              <select
                value={scenario}
                onChange={e =>
                  setScenario(
                    e.target.value
                  )
                }
              >

                {scenarios.map(
                  s => (
                    <option
                      key={s}
                    >
                      {s}
                    </option>
                  )
                )}

              </select>

              <button
                className="primary"
                onClick={
                  runSimulation
                }
              >
                Run Simulation
              </button>


              {simulation && (

                <div className="simulation">

                  <div className="impact">
                    {simulation.impact_score}%
                    {" "}impact
                  </div>

                  <div>
                    Risk:
                    {" "}
                    <strong>

                      {simulation.risk_before}

                      {" → "}

                      {simulation.risk_after}

                    </strong>
                  </div>

                  <p>
                    {simulation.recommendation}
                  </p>

                </div>

              )}

            </div>

          </section>

        )}


        {/* ==================================================
            ASSETS
        ================================================== */}

        {dash && (

          <section className="card">

            <div className="sectionTitle">
              Asset Monitoring
            </div>

            <div className="assetGrid">

              {assets.map(
                a => (

                  <div
                    className="asset"
                    key={a.id}
                  >

                    <strong>
                      {a.name}
                    </strong>

                    <span>
                      {a.asset_type}
                    </span>

                    <span>
                      {a.location}
                    </span>

                    <span
                      className={
                        a.risk_score >= 50
                          ? "risk high"
                          : "risk"
                      }
                    >
                      Risk {a.risk_score}%
                    </span>

                  </div>

                )
              )}

            </div>

          </section>

        )}

      </main>

    </div>

  )
}