import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat'; // Import the heatmap library
import './App.css';

// --- 1. CONFIGURATION ---

const getMagColor = (mag) => {
  if (mag >= 5) return '#dc2626'; // Red
  if (mag >= 3) return '#ea580c'; // Orange
  if (mag >= 1) return '#ca8a04'; // Yellow
  return '#2563eb';               // Blue
};

const createCustomIcon = (mag) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${getMagColor(mag)};
      width: 10px; height: 10px;
      border-radius: 50%;
      border: 1px solid white;
      box-shadow: 0 0 4px rgba(0,0,0,0.5);
    "></div>`,
    iconSize: [10, 10],
    iconAnchor: [5, 5],
    popupAnchor: [0, -6]
  });
};

// --- 2. NEW COMPONENT: HEATMAP LAYER ---
// This component reads the disaster data and draws a heat layer on the map
const HeatmapLayer = ({ data }) => {
  const map = useMap();
  const heatLayerRef = useRef(null);

  useEffect(() => {
    if (!map || !data || data.length === 0) return;

    // Convert GeoJSON features to Heatmap points: [lat, lon, intensity]
    // Intensity is scaled based on Magnitude (mag 5 is "hotter" than mag 2)
    const points = data.map(feature => {
      const [lon, lat] = feature.geometry.coordinates;
      const mag = feature.properties.mag;
      return [lat, lon, mag * 2]; // Scaled intensity
    });

    // If layer exists, remove it (cleanup)
    if (heatLayerRef.current) {
      map.removeLayer(heatLayerRef.current);
    }

    // Create new Heat layer
    // radius: how "spread out" the heat is
    // blur: how smooth the gradient is
    heatLayerRef.current = L.heatLayer(points, {
      radius: 25,
      blur: 15,
      maxZoom: 10,
      gradient: { 0.4: 'blue', 0.6: 'lime', 0.8: 'orange', 1.0: 'red' }
    }).addTo(map);

    // Cleanup on unmount
    return () => {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current);
      }
    };
  }, [map, data]);

  return null;
};

// --- 3. GENERATE IRREGULAR "IMPACT ZONES" ---
const generateImpactPolygon = (lat, lon, mag) => {
  const points = [];
  const numPoints = 12; 
  // Mag 5 = bigger polygon, Mag 2 = smaller
  const baseRadius = mag * 0.04; 
  
  for (let i = 0; i < numPoints; i++) {
    const angle = (i / numPoints) * (2 * Math.PI);
    const variance = 0.7 + Math.random() * 0.6; 
    const r = baseRadius * variance;
    const deltaLat = r * Math.cos(angle);
    const deltaLon = r * Math.sin(angle);
    points.push([lat + deltaLat, lon + deltaLon]);
  }
  return points;
};

// --- 4. MOCK TWEET GENERATOR ---
const generateMockTweets = (placeName, magnitude) => {
  return [
    { user: "@LocalNewsAlerts", text: `BREAKING: Magnitude ${magnitude} detected near ${placeName}.`, time: "2m ago", isOfficial: true },
    { user: "@CitizenJoe", text: `Felt that shaking in ${placeName.split(',')[0]}! #Earthquake`, time: "5m ago", isOfficial: false },
    { user: "@GeoMonitor", text: `Seismic alert: Avoid damaged infrastructure in ${placeName}.`, time: "12m ago", isOfficial: true }
  ];
};

// --- 5. FLY TO LOCATION HELPER ---
function FlyToLocation({ target }) {
  const map = useMap();
  if (target) {
    const [lon, lat] = target.geometry.coordinates;
    map.flyTo([lat, lon], 9, { duration: 1.5 });
  }
  return null;
}

// --- 6. MAIN APP ---
function App() {
  const [disasters, setDisasters] = useState([]);
  const [selectedDisaster, setSelectedDisaster] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEarthquakes = async () => {
      try {
        const response = await fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson');
        const data = await response.json();
        
        const processedData = data.features
          .filter(f => f.properties.mag > 1.0)
          .map(f => {
             const [lon, lat] = f.geometry.coordinates;
             return {
               ...f,
               impactZone: generateImpactPolygon(lat, lon, f.properties.mag)
             };
          });

        setDisasters(processedData);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching USGS data:", error);
        setLoading(false);
      }
    };

    fetchEarthquakes();
  }, []);

  const handleSelect = (feature) => setSelectedDisaster(feature);
  const clearSelection = (e) => { e.stopPropagation(); setSelectedDisaster(null); };

  return (
    <div className="App">
      <header className="app-header">
        <h1>Refra SOS | Live Global Monitor</h1>
      </header>

      <div className="dashboard-container">
        
        {/* SIDE PANE */}
        <div className="side-pane">
          {loading ? (
            <div style={{padding: 20}}>Loading Data...</div>
          ) : !selectedDisaster ? (
            <>
              <h2>Live Incidents ({disasters.length})</h2>
              <div className="list-container">
                {disasters.map((feature) => (
                  <div key={feature.id} className="list-item" onClick={() => handleSelect(feature)}>
                    <div className="status-dot" style={{ backgroundColor: getMagColor(feature.properties.mag) }}></div>
                    <div className="item-info">
                      <h3>{feature.properties.place}</h3>
                      <span className="badge">Mag {feature.properties.mag.toFixed(1)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <>
              <div className="pane-header">
                <button className="back-btn" onClick={clearSelection}>← Back</button>
                <h2>{selectedDisaster.properties.place}</h2>
              </div>
              <div className="tweet-feed">
                <div className="feed-label">Live Updates</div>
                {generateMockTweets(selectedDisaster.properties.place, selectedDisaster.properties.mag).map((tweet, idx) => (
                  <div key={idx} className="tweet-card">
                    <div className="tweet-header">
                      <span className={`username ${tweet.isOfficial ? 'official' : ''}`}>{tweet.user}</span>
                      <span className="timestamp">{tweet.time}</span>
                    </div>
                    <div className="tweet-body">{tweet.text}</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* MAP PANE */}
        <div className="map-wrapper">
          <MapContainer center={[37.09, -95.71]} zoom={4} style={{ height: "100%", width: "100%" }}>
            
            {/* 1. BASE MAP */}
            <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            
            {/* 2. HEATMAP LAYER (Renders beneath markers/polygons) */}
            <HeatmapLayer data={disasters} />

            {/* 3. INTERACTIVE LAYERS (Polygons & Markers) */}
            <FlyToLocation target={selectedDisaster} />

            {disasters.map((feature) => {
              const { coordinates } = feature.geometry;
              const { mag, place } = feature.properties;
              const isSelected = selectedDisaster?.id === feature.id;
              const color = getMagColor(mag);

              return (
                <React.Fragment key={feature.id}>
                  
                  {/* BORDER (POLYGON) - Rendered ON TOP of Heatmap */}
                  {isSelected && (
                    <Polygon 
                      positions={feature.impactZone}
                      pathOptions={{ 
                        color: color, 
                        weight: 3,           // Thicker border
                        fillColor: color, 
                        fillOpacity: 0.1,    // Very transparent fill so Heatmap shows through
                        dashArray: '8, 8'    // Dashed "Danger" look
                      }}
                    >
                      <Popup>
                        <div style={{textAlign: 'center', color: '#b91c1c'}}>
                           <strong>⚠️ EXCLUSION ZONE</strong><br/>
                           Authorized Personnel Only
                        </div>
                      </Popup>
                    </Polygon>
                  )}

                  <Marker 
                    position={[coordinates[1], coordinates[0]]} 
                    icon={createCustomIcon(mag)}
                    eventHandlers={{ click: () => handleSelect(feature) }}
                  >
                    <Popup><strong>{place}</strong><br/>Mag: {mag}</Popup>
                  </Marker>
                </React.Fragment>
              );
            })}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}

export default App;