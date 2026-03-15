import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';
import config from './config';

// Map controller component to handle flyTo
function MapController({ flyTo }) {
  const map = useMap();
  useEffect(() => {
    if (flyTo) {
      map.flyTo(flyTo.center, flyTo.zoom);
    }
  }, [flyTo, map]);
  return null;
}

function App() {
  const [selectedYear, setSelectedYear] = useState(2024);
  const [debouncedYear, setDebouncedYear] = useState(2024);
  const [disasters, setDisasters] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchedCity, setSearchedCity] = useState(null);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);
  const [selectedCity, setSelectedCity] = useState(null);
  const [loading, setLoading] = useState(false);
  const [narration, setNarration] = useState('');
  const [insurance, setInsurance] = useState(null);
  const [flyTo, setFlyTo] = useState(null);

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
          { id: 5, lat: 19.0760, lng: 72.8777, type: 'Flood', description: 'Flooding in Mumbai', risk: 0.9, city: 'Mumbai' },
          { id: 6, lat: 6.5244, lng: 3.3792, type: 'Heatwave', description: 'Heatwave in Lagos', risk: 0.6, city: 'Lagos' },
          { id: 7, lat: 25.7617, lng: -80.1918, type: 'Hurricane', description: 'Hurricane risk in Miami', risk: 0.7, city: 'Miami' },
          { id: 8, lat: -6.2088, lng: 106.8456, type: 'Flood', description: 'Flooding in Jakarta', risk: 0.8, city: 'Jakarta' },
        ]);
      });
  }, [debouncedYear]);

  const getColor = (risk) => {
    if (risk < 0.3) return '#22c55e';
    if (risk <= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  const handleMarkerClick = (disaster) => {
    setSelectedCity(disaster);
    setSidePanelOpen(true);
    setLoading(true);
    // Fetch narration and insurance
    Promise.all([
      axios.get(`${config.API_BASE}/api/narrate?city=${disaster.city}&year=${debouncedYear}`),
      axios.get(`${config.API_BASE}/api/insurance?city=${disaster.city}&year=${debouncedYear}`)
    ]).then(([narrateRes, insuranceRes]) => {
      setNarration(narrateRes.data.narration);
      setInsurance(insuranceRes.data);
      setLoading(false);
    }).catch(() => {
      // Mock fallback
      setNarration(`AI Analysis: ${disaster.city} faces significant ${disaster.type.toLowerCase()} risks by ${debouncedYear}. Climate models predict increased frequency and severity of these events, impacting infrastructure and population.`);
      setInsurance({
        floodPercent: Math.round(disaster.risk * 100),
        heatPercent: Math.round((1 - disaster.risk) * 100),
        damage: `$${Math.round(disaster.risk * 1000000000)}M`,
        premiumChange: `${Math.round(disaster.risk * 50)}% increase`
      });
      setLoading(false);
    });
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) return;
    axios.get(`${config.API_BASE}/api/search?q=${encodeURIComponent(searchQuery)}`)
      .then(response => {
        const result = response.data;
        if (result && result.lat && result.lng) {
          // Fly to location
          setFlyTo({ center: [result.lat, result.lng], zoom: 10 });
          // Add marker and fetch risk
          const newCity = { ...result, id: Date.now(), risk: 0.5 }; // Default risk
          setSearchedCity(newCity);
          // Fetch risk for this city
          axios.get(`${config.API_BASE}/api/risk?city=${result.city}&year=${debouncedYear}`)
            .then(riskRes => {
              setSearchedCity({ ...newCity, risk: riskRes.data.risk });
            }).catch(() => {
              // Keep default
            });
        }
      }).catch(() => {
        // Mock search for test cities
        const mockCities = {
          'mumbai': { lat: 19.0760, lng: 72.8777, city: 'Mumbai' },
          'lagos': { lat: 6.5244, lng: 3.3792, city: 'Lagos' },
          'miami': { lat: 25.7617, lng: -80.1918, city: 'Miami' },
          'jakarta': { lat: -6.2088, lng: 106.8456, city: 'Jakarta' }
        };
        const query = searchQuery.toLowerCase();
        if (mockCities[query]) {
          const result = mockCities[query];
          setFlyTo({ center: [result.lat, result.lng], zoom: 10 });
          const newCity = { ...result, id: Date.now(), risk: 0.5 };
          setSearchedCity(newCity);
        }
      });
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', fontFamily: 'Arial, sans-serif' }}>
      {/* Header */}
      <div style={{ padding: '10px 20px', background: '#1f2937', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>🌍 TerraWatch</h1>
        <div style={{ fontSize: '0.9rem' }}>
          {disasters.length} cities monitored | Viewing: {debouncedYear} | SDG 13
        </div>
      </div>

      {/* Controls */}
      <div style={{ padding: '10px 20px', background: 'white', borderBottom: '1px solid #ccc', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Search city..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', minWidth: '200px' }}
          />
          <button onClick={handleSearch} style={{ padding: '8px 16px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px' }}>Search</button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <span>Year: {debouncedYear}</span>
          <input
            type="range"
            min="2024"
            max="2050"
            step="1"
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            style={{ width: '150px' }}
          />
          <button onClick={() => setSelectedYear(2024)} style={{ padding: '4px 8px', fontSize: '0.8rem' }}>Today</button>
          <button onClick={() => setSelectedYear(2030)} style={{ padding: '4px 8px', fontSize: '0.8rem' }}>2030</button>
          <button onClick={() => setSelectedYear(2050)} style={{ padding: '4px 8px', fontSize: '0.8rem' }}>2050</button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', position: 'relative' }}>
        {/* Map */}
        <div style={{ flex: 1, position: 'relative' }}>
          <MapContainer center={[0, 0]} zoom={2} style={{ height: '100%', width: '100%' }}>
            <MapController flyTo={flyTo} />
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
                eventHandlers={{
                  click: () => handleMarkerClick(disaster),
                }}
              >
                <Tooltip>{disaster.city}</Tooltip>
              </CircleMarker>
            ))}
            {searchedCity && (
              <CircleMarker
                center={[searchedCity.lat, searchedCity.lng]}
                radius={20}
                color={getColor(searchedCity.risk)}
                fillColor={getColor(searchedCity.risk)}
                fillOpacity={0.5}
                eventHandlers={{
                  click: () => handleMarkerClick(searchedCity),
                }}
              >
                <Tooltip>{searchedCity.city}</Tooltip>
              </CircleMarker>
            )}
          </MapContainer>

          {/* Legend */}
          <div style={{ position: 'absolute', bottom: '20px', left: '20px', background: 'white', padding: '15px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', fontSize: '0.9rem' }}>
            <h4 style={{ margin: '0 0 10px 0' }}>Risk Legend</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '20px', height: '20px', background: '#22c55e', borderRadius: '50%' }}></div>
                <span>Low Risk (&lt;30%)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '20px', height: '20px', background: '#f59e0b', borderRadius: '50%' }}></div>
                <span>Medium Risk (30-60%)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '20px', height: '20px', background: '#ef4444', borderRadius: '50%' }}></div>
                <span>High Risk (&gt;60%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Side Panel */}
        {sidePanelOpen && (
          <div style={{ width: '350px', background: 'white', borderLeft: '1px solid #ccc', padding: '20px', overflowY: 'auto', boxShadow: '-2px 0 10px rgba(0,0,0,0.1)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3>{selectedCity?.city}</h3>
              <button onClick={() => setSidePanelOpen(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
            </div>
            
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <div style={{ border: '4px solid #f3f3f3', borderTop: '4px solid #3498db', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 2s linear infinite', margin: '0 auto 20px' }}></div>
                <p>Loading risk analysis...</p>
              </div>
            ) : (
              <div>
                <div style={{ marginBottom: '20px' }}>
                  <h4>Risk Assessment ({debouncedYear})</h4>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span>Flood Risk:</span>
                    <span>{insurance?.floodPercent || Math.round(selectedCity.risk * 100)}%</span>
                  </div>
                  <div style={{ background: '#e5e7eb', height: '10px', borderRadius: '5px', marginBottom: '15px' }}>
                    <div style={{ background: getColor(selectedCity.risk), height: '100%', borderRadius: '5px', width: `${insurance?.floodPercent || selectedCity.risk * 100}%` }}></div>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span>Heat Risk:</span>
                    <span>{insurance?.heatPercent || Math.round((1 - selectedCity.risk) * 100)}%</span>
                  </div>
                  <div style={{ background: '#e5e7eb', height: '10px', borderRadius: '5px', marginBottom: '15px' }}>
                    <div style={{ background: '#f59e0b', height: '100%', borderRadius: '5px', width: `${insurance?.heatPercent || (1 - selectedCity.risk) * 100}%` }}></div>
                  </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <h4>Projected Damage</h4>
                  <p style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#ef4444' }}>{insurance?.damage || `$${Math.round(selectedCity.risk * 1000000000)}M`}</p>
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <h4>Insurance Premium Change</h4>
                  <p style={{ color: insurance?.premiumChange?.includes('+') ? '#ef4444' : '#22c55e' }}>{insurance?.premiumChange || `${Math.round(selectedCity.risk * 50)}% increase`}</p>
                </div>

                <div>
                  <h4>AI Analysis</h4>
                  <p style={{ lineHeight: '1.5' }}>{narration}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
          .header { flex-direction: column; text-align: center; }
          .controls { flex-direction: column; gap: 10px; }
          .side-panel { width: 100%; position: absolute; right: 0; top: 0; z-index: 1000; }
        }
      `}</style>
    </div>
  );
}

export default App;
