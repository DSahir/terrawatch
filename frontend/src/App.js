import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import L from 'leaflet';
import 'leaflet.markercluster';
import axios from 'axios';
import config from './config';

// Marker cluster component to handle clustering using native Leaflet MarkerCluster
function MarkerClusterGroup({ cities, onMarkerClick, getColor, getRiskLevel }) {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    // Create marker cluster group
    const clusterGroup = L.markerClusterGroup();

    cities.forEach(city => {
      // Handle both city.risk (0-1 scale) and fallback to climate_risk_index (0-100 scale)
      const riskVal = city.risk !== undefined ? city.risk : (city.climate_risk_index !== undefined ? city.climate_risk_index / 100 : 0.5);
      const markerColor = getColor(riskVal);
      const marker = L.circleMarker([city.lat, city.lng], {
        radius: 15,
        color: markerColor,
        fillColor: markerColor,
        fillOpacity: 0.7,
        weight: 2
      });

      // Bind tooltip
      marker.bindTooltip(`${city.city} - ${getRiskLevel(riskVal)}`);

      // Bind click handler
      marker.on('click', () => {
        onMarkerClick(city);
      });

      // ARIA label attributes for accessibility (Bug 12)
      marker.on('add', (e) => {
        const el = e.target.getElement();
        if (el) {
          el.setAttribute('aria-label', `${city.city} - ${getRiskLevel(riskVal)} Risk`);
          el.setAttribute('role', 'img');
        }
      });

      clusterGroup.addLayer(marker);
    });

    // Hover tooltip for cluster details (Bug 9)
    clusterGroup.on('clustermouseover', (event) => {
      const markers = event.layer.getAllChildMarkers();
      const cityNames = markers.map(m => {
        const tooltip = m.getTooltip();
        return tooltip ? tooltip.getContent().split(' - ')[0] : '';
      }).filter(Boolean);
      
      event.layer.bindTooltip(cityNames.join(', '), { direction: 'top', permanent: false }).openTooltip();
    });

    map.addLayer(clusterGroup);

    return () => {
      map.removeLayer(clusterGroup);
    };
  }, [map, cities, onMarkerClick, getColor, getRiskLevel]);

  return null;
}


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
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [debouncedYear, setDebouncedYear] = useState(currentYear);
  const [cities, setCities] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchedCity, setSearchedCity] = useState(null);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);
  const [selectedCity, setSelectedCity] = useState(null);
  const [selectedCityRiskData, setSelectedCityRiskData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [narration, setNarration] = useState(null);
  const [insurance, setInsurance] = useState(null);
  const [flyTo, setFlyTo] = useState(null);
  const [backendError, setBackendError] = useState(false);
  const [aboutModalOpen, setAboutModalOpen] = useState(false);

  // Debounce year selection
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedYear(selectedYear), 300);
    return () => clearTimeout(timer);
  }, [selectedYear]);

  // Fetch all cities when year changes
  useEffect(() => {
    axios.get(`${config.API_BASE}/api/v1/cities?year=${debouncedYear}`)
      .then(response => {
        setCities(response.data);
        setBackendError(false);
      })
      .catch(error => {
        console.error('Failed to fetch risk data:', error);
        setCities([]);
        setBackendError(true);
      });
  }, [debouncedYear]);

  // Fetch real-time risk analysis and AI analysis for selected city - THIS UPDATES WHEN YEAR CHANGES
  useEffect(() => {
    if (!selectedCity) {
      setSelectedCityRiskData(null);
      setNarration(null);
      setInsurance(null);
      return;
    }

    const fetchCityData = async () => {
      setLoading(true);
      setNarration(null);
      setInsurance(null);
      try {
        // Fetch comprehensive real-time analysis (includes trends and AI insights)
        const realtimeResponse = await axios.get(
          `${config.API_BASE}/api/v1/realtime-analysis?lat=${selectedCity.lat}&lng=${selectedCity.lng}&year=${debouncedYear}&city=${encodeURIComponent(selectedCity.city)}`
        );
        
        // Extract current risks for display
        const realtimeData = realtimeResponse.data;
        setSelectedCityRiskData({
          ...realtimeData.current_risks,
          latitude: selectedCity.lat,
          longitude: selectedCity.lng,
          city: realtimeData.location.city,
          trends: realtimeData.risk_trends
        });
        
        // Set narration from AI insights
        setNarration(realtimeData.ai_insights);
        
        // Fetch insurance data separately
        const insuranceResponse = await axios.get(
          `${config.API_BASE}/api/v1/insurance?city=${encodeURIComponent(selectedCity.city)}&year=${debouncedYear}`
        );
        setInsurance(insuranceResponse.data);

        setBackendError(false);
      } catch (error) {
        console.error('Failed to fetch city data:', error);
        
        // Fallback: Try basic risk endpoint
        try {
          const riskResponse = await axios.get(
            `${config.API_BASE}/api/v1/risk?lat=${selectedCity.lat}&lng=${selectedCity.lng}&year=${debouncedYear}`
          );
          setSelectedCityRiskData(riskResponse.data);
          setNarration({
            risk_brief: 'Climate risk data loaded (real-time analysis unavailable)',
            adaptation_actions: []
          });
        } catch {
          setSelectedCityRiskData(null);
          setNarration({
            risk_brief: 'Unable to load analysis at this time. Please ensure backend is running.',
            adaptation_actions: []
          });
          setInsurance(null);
          setBackendError(true);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchCityData();
  }, [selectedCity, debouncedYear]);

  const getColor = (risk) => {
    if (risk < 0.3) return '#22c55e';
    if (risk <= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  const getRiskLevel = (risk) => {
    if (risk < 0.3) return 'Low';
    if (risk <= 0.6) return 'Medium';
    return 'High';
  };

  const handleMarkerClick = (city) => {
    setSelectedCity(city);
    setSidePanelOpen(true);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    axios.get(`${config.API_BASE}/api/v1/search?q=${encodeURIComponent(searchQuery)}`)
      .then(response => {
        const results = response.data;
        if (results && results.length > 0) {
          const result = results[0]; // Take the first result
          
          // Check if this city already exists in the predefined list (case-insensitive) (Bug 11)
          const existingCity = cities.find(c => c.city.toLowerCase() === result.city.toLowerCase());
          
          if (existingCity) {
            handleMarkerClick(existingCity);
            setFlyTo({ center: [existingCity.lat, existingCity.lng], zoom: 10 });
          } else {
            const searchedCityData = {
              city: result.city,
              country: result.country || 'Unknown',
              lat: result.latitude,
              lng: result.longitude,
              risk: 0.5, // Default risk for searched cities
              risk_level: 'Unknown',
              type: 'Searched Location'
            };
            setSearchedCity(searchedCityData);
            handleMarkerClick(searchedCityData);
            setFlyTo({ center: [result.latitude, result.longitude], zoom: 10 });
          }
        } else {
          alert(`City "${searchQuery}" not found in dataset.`);
        }
      }).catch(error => {
        console.error('Failed to search for city:', error);
        alert(`City "${searchQuery}" not found in dataset.`);
      });
  };

  // Helper function to render Risk Trends dynamically based on selected year (Bug 8, Bug 5, Bug 3)
  const renderTrendDetails = (hazard, currentVal, trendsData) => {
    if (!trendsData) return null;
    const currentPct = Math.round(currentVal * 100);
    const val24 = Math.round(trendsData.value_2024 * 100);
    const val35 = Math.round(trendsData.value_2035 * 100);
    const val50 = Math.round(trendsData.value_2050 * 100);

    let p1, p2, p3;
    let w1, w2, w3;

    if (selectedYear < 2035) {
      p1 = { year: selectedYear, val: currentPct };
      p2 = { year: 2035, val: val35 };
      p3 = { year: 2050, val: val50 };
      
      w1 = Math.min(p1.val, 100);
      w2 = Math.min(Math.max(0, p2.val - p1.val), 100);
      w3 = Math.min(Math.max(0, p3.val - p2.val), 100);
    } else if (selectedYear < 2050) {
      p1 = { year: 2024, val: val24 };
      p2 = { year: selectedYear, val: currentPct };
      p3 = { year: 2050, val: val50 };
      
      w1 = Math.min(p1.val, 100);
      w2 = Math.min(Math.max(0, p2.val - p1.val), 100);
      w3 = Math.min(Math.max(0, p3.val - p2.val), 100);
    } else {
      p1 = { year: 2024, val: val24 };
      p2 = { year: 2035, val: val35 };
      p3 = { year: selectedYear, val: currentPct };
      
      w1 = Math.min(p1.val, 100);
      w2 = Math.min(Math.max(0, p2.val - p1.val), 100);
      w3 = Math.min(Math.max(0, p3.val - p2.val), 100);
    }

    return (
      <div style={{ marginBottom: '15px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
          <span style={{ fontWeight: '500', fontSize: '0.9rem', textTransform: 'capitalize' }}>{hazard}</span>
          <span style={{ fontSize: '0.8rem', color: '#666' }}>{trendsData.trajectory}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', fontSize: '0.85rem', marginBottom: '5px' }}>
          <span style={{ minWidth: '40px' }}>{p1.year}: {p1.val}%</span>
          <span style={{ minWidth: '40px' }}>{p2.year}: {p2.val}%</span>
          <span style={{ minWidth: '40px' }}>{p3.year}: {p3.val}%</span>
        </div>
        <div style={{ background: '#e5e7eb', height: '6px', borderRadius: '3px', overflow: 'hidden', display: 'flex' }}>
          <div style={{ background: '#3b82f6', height: '100%', width: `${w1}%` }}></div>
          <div style={{ background: '#f59e0b', height: '100%', width: `${w2}%` }}></div>
          <div style={{ background: '#ef4444', height: '100%', width: `${w3}%` }}></div>
        </div>
        {trendsData.years_to_critical !== null && (
          <p style={{ margin: '5px 0 0 0', fontSize: '0.8rem', color: '#ef4444', fontWeight: '500' }}>
            {trendsData.years_to_critical <= 0
              ? "⚠️ Threshold already exceeded"
              : `⚠️ Critical threshold in ~${trendsData.years_to_critical} years`}
          </p>
        )}
      </div>
    );
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', fontFamily: 'Arial, sans-serif' }}>

      {/* Header */}
      <div style={{ padding: '10px 20px', background: '#1f2937', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>🌍 TerraWatch</h1>
        <div style={{ fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '15px' }}>
          <span>{cities.length} cities monitored | Viewing: {debouncedYear} | SDG 13</span>
          <button 
            onClick={() => setAboutModalOpen(true)} 
            style={{ background: '#374151', color: 'white', border: '1px solid #4b5563', borderRadius: '4px', padding: '4px 8px', fontSize: '0.8rem', cursor: 'pointer' }}
          >
            About the Data
          </button>
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
          <button onClick={handleSearch} style={{ padding: '8px 16px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Search</button>
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
          <button onClick={() => setSelectedYear(new Date().getFullYear())} style={{ padding: '4px 8px', fontSize: '0.8rem', cursor: 'pointer' }}>Today</button>
          <button onClick={() => setSelectedYear(2030)} style={{ padding: '4px 8px', fontSize: '0.8rem', cursor: 'pointer' }}>2030</button>
          <button onClick={() => setSelectedYear(2050)} style={{ padding: '4px 8px', fontSize: '0.8rem', cursor: 'pointer' }}>2050</button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', position: 'relative' }}>
        {/* Map */}
        <div style={{ flex: 1, position: 'relative' }}>
          <MapContainer center={[20, 0]} zoom={2} style={{ height: '100%', width: '100%' }}>
            <MapController flyTo={flyTo} />
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {/* Display all cities with clustering */}
            <MarkerClusterGroup
              key={`${debouncedYear}-${cities.length}`}
              cities={cities}
              onMarkerClick={handleMarkerClick}
              getColor={getColor}
              getRiskLevel={getRiskLevel}
            />
            {/* Display searched city if different */}
            {searchedCity && !cities.find(c => c.city === searchedCity.city) && (
              <CircleMarker
                center={[searchedCity.lat, searchedCity.lng]}
                radius={15}
                color="#3b82f6"
                fillColor="#3b82f6"
                fillOpacity={0.7}
                weight={3}
                eventHandlers={{
                  click: () => handleMarkerClick(searchedCity),
                  add: (e) => {
                    const el = e.target.getElement();
                    if (el) {
                      el.setAttribute('aria-label', `${searchedCity.city} - Searched Location`);
                      el.setAttribute('role', 'img');
                    }
                  }
                }}
              >
                <Tooltip>{searchedCity.city} (Searched)</Tooltip>
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
          <div style={{ position: 'absolute', bottom: '20px', left: '20px', background: 'white', padding: '15px', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', fontSize: '0.9rem', zIndex: 500 }}>
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
          <div style={{ width: '380px', background: 'white', borderLeft: '1px solid #ddd', padding: '20px', overflowY: 'auto', boxShadow: '-2px 0 10px rgba(0,0,0,0.1)', zIndex: 100 }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <h3 style={{ margin: '0 0 5px 0' }}>{selectedCity?.city}</h3>
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>{selectedCity?.country || 'Unknown'}</p>
              </div>
              <button onClick={() => setSidePanelOpen(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
            </div>

            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                <div style={{ border: '4px solid #f3f3f3', borderTop: '4px solid #3498db', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 2s linear infinite', margin: '0 auto 20px' }}></div>
                <p>Loading risk analysis for {debouncedYear}...</p>
              </div>
            ) : (!selectedCityRiskData && !insurance) ? (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: '#ef4444' }}>
                <span style={{ fontSize: '2rem' }}>⚠️</span>
                <h4 style={{ margin: '10px 0' }}>Data Unavailable</h4>
                <p style={{ fontSize: '0.9rem', color: '#666' }}>
                  Could not load climate risk data for {selectedCity?.city} in {debouncedYear}. Please check your connection or try again.
                </p>
              </div>
            ) : (
              <div>
                <div style={{ marginBottom: '20px' }}>
                  <h4>Risk Assessment ({debouncedYear})</h4>
                  {selectedCityRiskData ? (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span>Flood Risk:</span>
                        <span>{Math.round(selectedCityRiskData.flood_risk * 100)}%</span>
                      </div>
                      <div style={{ background: '#e5e7eb', height: '10px', borderRadius: '5px', marginBottom: '15px' }}>
                        <div style={{ background: getColor(selectedCityRiskData.flood_risk), height: '100%', borderRadius: '5px', width: `${Math.min(selectedCityRiskData.flood_risk * 100, 100)}%` }}></div>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span>Heat Risk:</span>
                        <span>{Math.round(selectedCityRiskData.heat_risk * 100)}%</span>
                      </div>
                      <div style={{ background: '#e5e7eb', height: '10px', borderRadius: '5px', marginBottom: '15px' }}>
                        <div style={{ background: '#f59e0b', height: '100%', borderRadius: '5px', width: `${Math.min(selectedCityRiskData.heat_risk * 100, 100)}%` }}></div>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span>Storm Risk:</span>
                        <span>{Math.round(selectedCityRiskData.storm_risk * 100)}%</span>
                      </div>
                      <div style={{ background: '#e5e7eb', height: '10px', borderRadius: '5px', marginBottom: '15px' }}>
                        <div style={{ background: '#8b5cf6', height: '100%', borderRadius: '5px', width: `${Math.min(selectedCityRiskData.storm_risk * 100, 100)}%` }}></div>
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

                {/* Risk Trends Section */}
                {selectedCityRiskData?.trends && (
                  <div style={{ marginBottom: '25px', paddingBottom: '20px', borderBottom: '1px solid #eee' }}>
                    <h4 style={{ margin: '0 0 15px 0', color: '#1f2937' }}>📊 Risk Trends ({debouncedYear}-2050)</h4>
                    {renderTrendDetails("flood", selectedCityRiskData.flood_risk, selectedCityRiskData.trends.flood)}
                    {renderTrendDetails("heat", selectedCityRiskData.heat_risk, selectedCityRiskData.trends.heat)}
                    {renderTrendDetails("storm", selectedCityRiskData.storm_risk, selectedCityRiskData.trends.storm)}
                  </div>
                )}

                {/* AI Analysis Section */}
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
        }
      `}</style>
      {/* About the Data Modal (Bug 10) */}
      {aboutModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 2000
        }}>
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '8px',
            maxWidth: '500px',
            width: '90%',
            boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
            position: 'relative',
            color: '#1f2937',
            fontFamily: 'sans-serif'
          }}>
            <button 
              onClick={() => setAboutModalOpen(false)} 
              style={{ position: 'absolute', top: '15px', right: '15px', background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: '#6b7280' }}
            >
              ×
            </button>
            <h3 style={{ marginTop: 0, borderBottom: '1px solid #eee', paddingBottom: '10px', fontSize: '1.3rem' }}>🌍 About TerraWatch Climate Data</h3>
            <div style={{ fontSize: '0.9rem', lineHeight: '1.6' }}>
              <p><strong>Methodology:</strong> Climate projections are fetched dynamically for your exact coordinates using the <strong>Open-Meteo Climate Change API</strong> based on HighResMip working group models.</p>
              <p><strong>Scenario:</strong> <strong>SSP2-4.5</strong> (Shared Socioeconomic Pathway 2-4.5), representing a medium-emission scenario with moderate mitigation.</p>
              <p><strong>Timeline:</strong> 2024 (Baseline) to 2050 timeline, evaluating daily max temperature, precipitation sums, and max wind speeds to compute heatwave, flood, and storm risk trends.</p>
              <p><strong>AI Integration:</strong> Explanations and local briefings are generated using Qwen-72B and Qwen-7B models via Featherless AI.</p>
            </div>
            <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '20px', borderTop: '1px solid #eee', paddingTop: '10px' }}>
              Official climate projections powered by Open-Meteo and IPCC CMIP6 models. Last updated: March 2026.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
