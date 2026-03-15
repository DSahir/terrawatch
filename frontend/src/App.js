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
  const [backendError, setBackendError] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedYear(selectedYear), 300);
    return () => clearTimeout(timer);
  }, [selectedYear]);

  useEffect(() => {
    axios.get(`${config.API_BASE}/api/cities?year=${debouncedYear}`)
      .then(response => {
        setDisasters(response.data);
        setBackendError(false);
      })
      .catch(error => {
        console.error('Failed to fetch risk data:', error);
        setDisasters([]);
        setBackendError(true);
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
    setNarration('');
    setInsurance(null);

    // Fetch narration and insurance data
    Promise.all([
      axios.get(`${config.API_BASE}/api/narrate?city=${encodeURIComponent(disaster.city)}&year=${debouncedYear}`),
      axios.get(`${config.API_BASE}/api/insurance?city=${encodeURIComponent(disaster.city)}&year=${debouncedYear}`)
    ]).then(([narrateRes, insuranceRes]) => {
      setNarration(narrateRes.data);
      setInsurance(insuranceRes.data);
      setLoading(false);
    }).catch(error => {
      console.error('Failed to fetch city data:', error);
      setNarration({
        risk_brief: 'Unable to load AI analysis at this time. Please try again later.',
        adaptation_actions: []
      });
      setInsurance(null);
      setLoading(false);
    });
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) return;

    axios.get(`${config.API_BASE}/api/search?q=${encodeURIComponent(searchQuery)}`)
      .then(response => {
        const results = response.data;
        if (results && results.length > 0) {
          const result = results[0]; // Take the first result
          // Fly to location
          setFlyTo({ center: [result.latitude, result.longitude], zoom: 10 });
          // Create a city object for the marker (without risk data initially)
          const searchedCityData = {
            city: result.city,
            lat: result.latitude,
            lng: result.longitude,
            risk: 0.5, // Default risk for searched cities
            risk_level: 'Unknown',
            type: 'Searched Location'
          };
          setSearchedCity(searchedCityData);
        } else {
          alert(`City "${searchQuery}" not found. Please try a different city name.`);
        }
      }).catch(error => {
        console.error('Failed to search for city:', error);
        alert(`City "${searchQuery}" not found. Please try a different city name.`);
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

          {/* Backend Error Message */}
          {backendError && (
            <div style={{
              position: 'absolute',
              top: '20px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: '#ef4444',
              color: 'white',
              padding: '10px 20px',
              borderRadius: '5px',
              boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
              zIndex: 1000
            }}>
              ⚠️ Backend service unavailable. Please ensure the backend server is running on port 8001.
            </div>
          )}

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
                  {insurance ? (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span>Flood Risk:</span>
                        <span>{Math.round((insurance.flood_multiplier - 1) * 100)}%</span>
                      </div>
                      <div style={{ background: '#e5e7eb', height: '10px', borderRadius: '5px', marginBottom: '15px' }}>
                        <div style={{ background: getColor((insurance.flood_multiplier - 1) / 2.5), height: '100%', borderRadius: '5px', width: `${Math.min((insurance.flood_multiplier - 1) * 100 / 2.5, 100)}%` }}></div>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span>Heat Risk:</span>
                        <span>{Math.round((insurance.heat_multiplier - 1) * 100)}%</span>
                      </div>
                      <div style={{ background: '#e5e7eb', height: '10px', borderRadius: '5px', marginBottom: '15px' }}>
                        <div style={{ background: '#f59e0b', height: '100%', borderRadius: '5px', width: `${Math.min((insurance.heat_multiplier - 1) * 100 / 1.5, 100)}%` }}></div>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span>Storm Risk:</span>
                        <span>{Math.round((insurance.storm_multiplier - 1) * 100)}%</span>
                      </div>
                      <div style={{ background: '#e5e7eb', height: '10px', borderRadius: '5px', marginBottom: '15px' }}>
                        <div style={{ background: '#8b5cf6', height: '100%', borderRadius: '5px', width: `${Math.min((insurance.storm_multiplier - 1) * 100 / 2.0, 100)}%` }}></div>
                      </div>
                    </>
                  ) : (
                    <p style={{ color: '#ef4444' }}>Risk data unavailable</p>
                  )}
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <h4>Insurance Impact</h4>
                  {insurance ? (
                    <>
                      <p><strong>Base Premium:</strong> ${insurance.base_premium}</p>
                      <p><strong>Adjusted Premium:</strong> ${insurance.adjusted_premium}</p>
                      <p><strong>Total Multiplier:</strong> {insurance.total_multiplier}x</p>
                      <p style={{ fontSize: '0.9rem', color: '#6b7280', marginTop: '10px' }}>{insurance.explanation}</p>
                    </>
                  ) : (
                    <p style={{ color: '#ef4444' }}>Insurance data unavailable</p>
                  )}
                </div>

                <div>
                  <h4>AI Analysis</h4>
                  {narration ? (
                    <>
                      <p style={{ lineHeight: '1.5', marginBottom: '15px' }}>{narration.risk_brief}</p>
                      {narration.adaptation_actions && narration.adaptation_actions.length > 0 && (
                        <div>
                          <h5>Recommended Actions:</h5>
                          <ul style={{ paddingLeft: '20px' }}>
                            {narration.adaptation_actions.map((action, index) => (
                              <li key={index} style={{ marginBottom: '5px', fontSize: '0.9rem' }}>{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </>
                  ) : (
                    <p>Analysis unavailable</p>
                  )}
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
