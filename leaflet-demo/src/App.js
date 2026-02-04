import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

// --- 1. HELPERS & CONFIG ---

const getMagColor = (mag) => {
  if (mag >= 5) return '#dc2626'; // Red (Critical)
  if (mag >= 3) return '#ea580c'; // Orange (Severe)
  if (mag >= 1) return '#ca8a04'; // Yellow (Moderate)
  return '#2563eb';               // Blue (Minor)
};

const createCustomIcon = (mag) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${getMagColor(mag)};
      width: 14px; height: 14px;
      border-radius: 50%;
      border: 2px solid white;
      box-shadow: 0 0 4px rgba(0,0,0,0.5);
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -10]
  });
};

// --- 2. GENERATE IRREGULAR "IMPACT ZONES" ---
// This function creates a jagged polygon around a center point to mimic real damage zones.
// It avoids the "perfect circle" look.
const generateImpactPolygon = (lat, lon, mag) => {
  const points = [];
  const numPoints = 12; // How many corners the shape has
  // Mag 5 = ~0.3 degrees radius (approx 30km), Mag 2 = ~0.05 degrees
  const baseRadius = mag * 0.04; 
  
  for (let i = 0; i < numPoints; i++) {
    // Calculate angle for this point
    const angle = (i / numPoints) * (2 * Math.PI);
    
    // Add "Randomness" to the radius to make it jagged/irregular
    // varies between 70% and 130% of the base radius
    const variance = 0.7 + Math.random() * 0.6; 
    const r = baseRadius * variance;
    
    // Convert polar coordinates to Lat/Lon offsets
    const deltaLat = r * Math.cos(angle);
    const deltaLon = r * Math.sin(angle);
    
    points.push([lat + deltaLat, lon + deltaLon]);
  }
  return points;
};

// --- 3. HARDCODED TWEET GENERATOR (unchanged) ---
const generateMockTweets = (placeName, magnitude) => {
  const hashtags = ["#Earthquake", "#Emergency", "#SOS", "#Safety"];
  const randomTag = hashtags[Math.floor(Math.random() * hashtags.length)];
  
  return [
    { user: "@LocalNewsAlerts", text: `BREAKING: Magnitude ${magnitude} earthquake detected near ${placeName}. Residents advised to stay outdoors.`, time: "2m ago", isOfficial: true },
    { user: "@CitizenJoe", text: `Whoa! Just felt huge shaking in ${placeName.split(',')[0]}! Everyone okay? ${randomTag}`, time: "5m ago", isOfficial: false },
    { user: "@SafeCity", text: `Reports of structural vibrations in the ${placeName} sector. Avoid glass buildings.`, time: "10m ago", isOfficial: false },
    { user: "@GeoMonitor", text: `Seismic activity confirms mag ${magnitude} event. Aftershocks possible.`, time: "12m ago", isOfficial: true }
  ];
};

// --- 4. MAP CONTROLLER ---
function FlyToLocation({ target }) {
  const map = useMap();
  if (target) {
    const [lon, lat] = target.geometry.coordinates;
    map.flyTo([lat, lon], 9, { duration: 1.5 });
  }
  return null;
}

// --- 5. MAIN APP ---
function App() {
  const [disasters, setDisasters] = useState([]);
  const [selectedDisaster, setSelectedDisaster] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEarthquakes = async () => {
      try {
        const response = await fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson');
        const data = await response.json();
        
        // Filter and Process Data
        const processedData = data.features
          .filter(f => f.properties.mag > 1.0)
          .map(f => {
             // We generate the "Shape" once when data loads, so it doesn't flicker
             const [lon, lat] = f.geometry.coordinates;
             return {
               ...f,
               // Store the calculated polygon in the object
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
            <div style={{padding: 20}}>Loading USGS Data...</div>
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
                <div className="feed-label">Live Social Updates</div>
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
            <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            
            <FlyToLocation target={selectedDisaster} />

            {disasters.map((feature) => {
              const { coordinates } = feature.geometry;
              const { mag, place } = feature.properties;
              const isSelected = selectedDisaster?.id === feature.id;
              const color = getMagColor(mag);

              return (
                <React.Fragment key={feature.id}>
                  {/* DYNAMIC IRREGULAR POLYGON */}
                  {isSelected && (
                    <Polygon 
                      positions={feature.impactZone}
                      pathOptions={{ 
                        color: color, 
                        fillColor: color, 
                        fillOpacity: 0.4,
                        weight: 2,
                        dashArray: '5, 10' 
                      }}
                    >
                      <Popup>
                        <div style={{textAlign: 'center', color: '#b91c1c'}}>
                           <strong>⚠️ IMPACT ZONE</strong><br/>
                           Avoid this area
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