import { useEffect, useState } from "react"
import {
  GeoJSON,
  CircleMarker,
  Polyline,
  Tooltip,
  useMap,
  Marker,
} from "react-leaflet"
import L from "leaflet"

const MAP_LEVELS = {
  overview: "/data/antarctica-overview.geojson",
  medium: "/data/antarctica-medium.geojson",
  detailed: "/data/antarctica-detailed.geojson",
}

const ICE_URL = "/data/ice-shelves.geojson"


function createPolarGrid() {
  const lines = []

  for (let latitude = -60; latitude >= -85; latitude -= 5) {
    const points = []

    for (let longitude = -180; longitude <= 180; longitude += 2) {
      points.push([latitude, longitude])
    }

    lines.push({
      id: `lat-${latitude}`,
      points,
    })
  }

  for (let longitude = -180; longitude < 180; longitude += 15) {
    const points = []

    for (let latitude = -60; latitude >= -89; latitude -= 1) {
      points.push([latitude, longitude])
    }

    lines.push({
      id: `lon-${longitude}`,
      points,
    })
  }

  return lines
}


function getMapLevel(zoom) {
  if (zoom <= 2) return "overview"
  if (zoom <= 4) return "medium"
  return "detailed"
}


function MapLevelController({ onLevelChange }) {
  const map = useMap()

  useEffect(() => {
    const updateLevel = () => {
      onLevelChange(getMapLevel(map.getZoom()))
    }

    updateLevel()

    map.on("zoomend", updateLevel)

    return () => {
      map.off("zoomend", updateLevel)
    }
  }, [map, onLevelChange])

  return null
}


function landStyle() {
  return {
    color: "#9ab7c0",
    weight: 1.4,
    opacity: 0.95,
    fillColor: "#d7e5e8",
    fillOpacity: 0.92,
  }
}


function iceStyle() {
  return {
    color: "#83b5c2",
    weight: 1,
    opacity: 0.8,
    fillColor: "#b8dce3",
    fillOpacity: 0.42,
  }
}


function StationLabel({ position, name, subtitle }) {
  const icon = L.divIcon({
    className: "safar-station-label",
    html: `
      <div style="
        display:flex;
        align-items:center;
        gap:6px;
        white-space:nowrap;
        transform:translate(-4px,-4px);
      ">
        <div style="
          width:10px;
          height:10px;
          border-radius:50%;
          background:#ffffff;
          border:2px solid #173746;
          box-shadow:0 0 0 2px rgba(255,255,255,0.25);
        "></div>

        <div style="
          background:rgba(5,20,30,0.88);
          border:1px solid rgba(160,210,220,0.35);
          border-radius:5px;
          padding:4px 7px;
          color:#e8f5f7;
          font-family:Arial,sans-serif;
          font-size:10px;
          line-height:1.2;
          box-shadow:0 3px 10px rgba(0,0,0,0.25);
        ">
          <strong>${name}</strong>
          <div style="
            color:#9bb7bf;
            font-size:8px;
            margin-top:1px;
          ">
            ${subtitle}
          </div>
        </div>
      </div>
    `,
    iconSize: [1, 1],
    iconAnchor: [0, 0],
  })

  return (
    <Marker
      position={position}
      icon={icon}
      interactive={false}
    />
  )
}


export default function OfflineAntarcticMap() {
  const [mapLevel, setMapLevel] = useState("overview")
  const [land, setLand] = useState(null)
  const [iceShelves, setIceShelves] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const grid = createPolarGrid()

  useEffect(() => {
    let cancelled = false

    async function loadLand() {
      try {
        setLoading(true)
        setError(null)

        const url = MAP_LEVELS[mapLevel]

        const response = await fetch(url)

        if (!response.ok) {
          throw new Error(
            `Unable to load ${mapLevel} Antarctic map (${response.status})`
          )
        }

        const data = await response.json()

        if (data.type !== "FeatureCollection") {
          throw new Error("Invalid Antarctic GeoJSON")
        }

        if (!cancelled) {
          setLand(data)
        }

        console.log(
          `SAFAR ${mapLevel} map loaded:`,
          data.features?.length,
          "features"
        )
      } catch (err) {
        console.error("SAFAR map error:", err)

        if (!cancelled) {
          setError(err.message || "Unable to load Antarctic map")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadLand()

    return () => {
      cancelled = true
    }
  }, [mapLevel])


  useEffect(() => {
    let cancelled = false

    async function loadIceShelves() {
      try {
        const response = await fetch(ICE_URL)

        if (!response.ok) return

        const data = await response.json()

        if (!cancelled) {
          setIceShelves(data)
        }
      } catch (err) {
        console.warn("Ice shelf layer unavailable:", err)
      }
    }

    loadIceShelves()

    return () => {
      cancelled = true
    }
  }, [])


  return (
    <>
      <MapLevelController onLevelChange={setMapLevel} />


      {/* POLAR GRID */}
      {grid.map((line) => (
        <Polyline
          key={line.id}
          positions={line.points}
          pathOptions={{
            color: "#6d929d",
            weight: 0.7,
            opacity: 0.3,
            dashArray: "3 7",
          }}
          interactive={false}
        />
      ))}


      {/* ANTARCTIC LAND */}
      {land && (
        <GeoJSON
          key={mapLevel}
          data={land}
          style={landStyle}
        />
      )}


      {/* ICE SHELVES */}
      {iceShelves && (
        <GeoJSON
          data={iceShelves}
          style={iceStyle}
        />
      )}


      {/* SOUTH POLE */}
      <CircleMarker
        center={[-89.8, 0]}
        radius={5}
        pathOptions={{
          color: "#ffffff",
          weight: 2,
          fillColor: "#173746",
          fillOpacity: 1,
        }}
      >
        <Tooltip direction="top">
          <strong>South Pole</strong>
          <br />
          90°S
        </Tooltip>
      </CircleMarker>


      {/* MAITRI */}
      <StationLabel
        position={[-70.7693, 11.7497]}
        name="MAITRI"
        subtitle="Indian Research Station"
      />


      {/* BHARATI */}
      <StationLabel
        position={[-69.416, 76.187]}
        name="BHARATI"
        subtitle="Indian Research Station"
      />


      {/* STATUS */}
      <div
        style={{
          position: "absolute",
          top: "14px",
          left: "14px",
          zIndex: 1000,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            background: "rgba(3,18,29,0.94)",
            border: "1px solid rgba(126,190,204,0.35)",
            borderRadius: "10px",
            padding: "8px 12px",
            color: "#dce9ec",
            fontSize: "10px",
          }}
        >
          <strong>● OFFLINE MAP</strong>
          <br />
          <span style={{ color: "#8eabb3" }}>
            Local Antarctic geography
          </span>
        </div>
      </div>


      {/* MAP LEVEL */}
      <div
        style={{
          position: "absolute",
          top: "14px",
          right: "14px",
          zIndex: 1000,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            background: "rgba(3,18,29,0.9)",
            border: "1px solid rgba(126,190,204,0.25)",
            borderRadius: "8px",
            padding: "7px 10px",
            color: "#9fb8bf",
            fontSize: "9px",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
          }}
        >
          {mapLevel} coastline
        </div>
      </div>


      {/* LOADING */}
      {loading && (
        <div
          style={{
            position: "absolute",
            bottom: "14px",
            left: "14px",
            zIndex: 1000,
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              background: "rgba(3,18,29,0.92)",
              borderRadius: "7px",
              padding: "7px 10px",
              color: "#b7ccd2",
              fontSize: "9px",
            }}
          >
            Loading local map...
          </div>
        </div>
      )}


      {/* ERROR */}
      {error && (
        <div
          style={{
            position: "absolute",
            bottom: "14px",
            left: "14px",
            zIndex: 1000,
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              background: "rgba(80,15,15,0.94)",
              border: "1px solid rgba(255,90,90,0.45)",
              borderRadius: "7px",
              padding: "8px 11px",
              color: "#ffd4d4",
              fontSize: "9px",
            }}
          >
            {error}
          </div>
        </div>
      )}
    </>
  )
}