import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';
import config from './config';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

function App() {
  const [selectedYear, setSelectedYear] = useState(2024);
  const [debouncedYear, setDebouncedYear] = useState(2024);
  const [disasters, setDisasters] = useState([]);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedYear(selectedYear), 300);
    return () => clearTimeout(timer);
  }, [selectedYear]);

  useEffect(() => {
    axios.get(`${config.API_BASE}/api/risk?year=${debouncedYear}`)
      .then(response => setDisasters(response.data))
      .catch(() => {
        // Fallback to mock data if API not ready
        setDisasters([
          { id: 1, lat: 40.7128, lng: -74.0060, type: 'Flood', description: 'Heavy flooding in New York City', risk: 0.8, city: 'New York City' },
          { id: 2, lat: 34.0522, lng: -118.2437, type: 'Heatwave', description: 'Extreme heatwave in Los Angeles', risk: 0.2, city: 'Los Angeles' },
          { id: 3, lat: 51.5074, lng: -0.1278, type: 'Coastal Erosion', description: 'Coastal erosion in London', risk: 0.5, city: 'London' },
          { id: 4, lat: -33.8688, lng: 151.2093, type: 'Wildfire', description: 'Wildfire risk in Sydney', risk: 0.7, city: 'Sydney' },
        ]);
      });
  }, [debouncedYear]);

  const getColor = (risk) => {
    if (risk < 0.3) return '#22c55e';
    if (risk <= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '10px', background: 'white', borderBottom: '1px solid #ccc', textAlign: 'center' }}>
        <h2>TerraWatch - Climate Risk Assessment: {debouncedYear}</h2>
        <div style={{ marginBottom: '10px' }}>
          <input
            type="range"
            min="2024"
            max="2050"
            step="1"
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            style={{ width: '80%', margin: '0 auto' }}
          />
        </div>
        <div>
          <button onClick={() => setSelectedYear(2024)} style={{ marginRight: '10px' }}>Today</button>
          <button onClick={() => setSelectedYear(2030)} style={{ marginRight: '10px' }}>2030</button>
          <button onClick={() => setSelectedYear(2050)}>2050</button>
        </div>
      </div>
      <div style={{ flex: 1 }}>
        <MapContainer center={[0, 0]} zoom={2} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          {disasters.map(disaster => (
            <CircleMarker
              key={disaster.id}
              center={[disaster.lat, disaster.lng]}
              radius={20}
              color={getColor(disaster.risk)}
              fillColor={getColor(disaster.risk)}
              fillOpacity={0.5}
            >
              <Tooltip>{disaster.city}</Tooltip>
              <Popup>
                <strong>{disaster.type}</strong><br />
                {disaster.description}<br />
                Risk: {disaster.risk}
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
