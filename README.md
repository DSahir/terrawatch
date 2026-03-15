# TerraWatch — AI-Powered Hyper-Local Climate Risk Intelligence Platform

## 🌍 Project Overview

TerraWatch is a city-agnostic, AI-powered climate risk intelligence platform that overlays hyper-local flood, heat, and storm risk projections on any city worldwide across a 2024–2050 timeline.

**Core Vision:** Democratize climate intelligence previously locked in expensive consulting firms and put it in hands of city planners, NGOs, insurers, and residents worldwide.

---

## 📋 Task Completion Status

| Task | Name | Status | Duration | Dependencies |
|------|------|--------|----------|--------------|
| T1 | Project scaffold + repo init | ✅ **DONE** | 45 min | — |
| T2 | Risk data table builder | ✅ **DONE** | 60 min | T1 |
| T3 | /api/risk endpoint | ✅ **DONE** | 60 min | T2 |
| T4 | Featherless narration (Qwen-72B) | ✅ **DONE** | 90 min | T3 |
| T5 | Insurance premium calculator | ✅ **DONE** | 60 min | T3 |
| T6 | City search + geocoding | ✅ **DONE** | 60 min | T1 |
| T7 | Pre-cache demo scenarios | ✅ **DONE** | 60 min | T4, T5 |
| **BONUS** | Satellite imagery analysis (Gemma-3-27B) | ✅ **DONE** | — | — |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Featherless API key (get from https://featherless.ai)

### Quick Start (Single Command)

```bash
./start.sh
```

This will start both the backend API server (port 8001) and frontend React app (port 3000).

### Manual Setup

1. **Install backend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your FEATHERLESS_API_KEY
   ```

4. **Start services:**
   ```bash
   # Terminal 1 - Backend
   PYTHONPATH=/Users/dhanshri/Documents/hackathon/terrawatch python3 backend/main.py

   # Terminal 2 - Frontend
   cd frontend && npm start
   ```

### Access Points

- **Frontend App:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Documentation:** http://localhost:8001/docs

4. **Warmup demo cache (optional):**
   ```bash
   python scripts/warmup_cache.py
   ```

---

## 📡 API Endpoints

### Health Check
```bash
GET /
GET /health
```

### T3: Get Climate Risk Data
```bash
GET /api/risk?lat=19.08&lng=72.88&year=2050
```

**Response:**
```json
{
  "city": "Mumbai",
  "year": 2050,
  "latitude": 19.08,
  "longitude": 72.88,
  "flood_risk": 0.595,
  "heat_risk": 0.567,
  "storm_risk": 0.255,
  "climate_risk_index": 57,
  "risk_level": "High",
  "damage_estimate": 1245000.0
}
```

**Risk Calculation:**
- **Climate Risk Index (CRI):** 50% × flood + 35% × heat + 15% × storm
- **IPCC Multipliers:** Baseline (2024) → +30% (2030) → +70% (2050)
- **Damage Estimates:** Scale by risk level and time horizon

---

### T6: Search Cities
```bash
GET /api/search?q=Mumbai
```

**Response:**
```json
[
  {
    "city": "Mumbai",
    "country": "India",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "admin1": "Maharashtra",
    "population": 20411000
  }
]
```

Uses free Open-Meteo geocoding API (no API key required).

---

### T4: Generate Risk Narration (Qwen-72B)
```bash
POST /api/narrate?city=Mumbai&lat=19.08&lng=72.88&year=2050&live=true
```

**Response:**
```json
{
  "risk_brief": "Mumbai faces severe flood risk by 2050 (59.5%), with combined heat exposure creating compound climate stress. Economic losses could exceed $1.2M annually. Immediate adaptation infrastructure is critical.",
  "adaptation_actions": [
    "Implement community-based early warning systems with real-time flood alerts and evacuation protocols",
    "Expand mangrove restoration and wetland protection to provide natural coastal defense barriers"
  ],
  "cached": false
}
```

**Parameters:**
- `live=true`: Use live AI inference (slower, uses Featherless API)
- `live=false`: Use pre-cached response (faster, instant)

---

### T5: Calculate Insurance Premiums (Qwen-7B)
```bash
GET /api/insurance?city=Mumbai&lat=19.08&lng=72.88&year=2050&live=true
```

**Response:**
```json
{
  "base_premium": 1200,
  "flood_multiplier": 2.49,
  "heat_multiplier": 1.85,
  "storm_multiplier": 1.51,
  "total_multiplier": 6.95,
  "adjusted_premium": 8340,
  "explanation": "Flood risk (59.5%) is the primary driver of the 595% premium increase.",
  "cached": false
}
```

**Premium Formula:**
```
flood_mult = 1.0 + (flood_risk × 2.5)
heat_mult = 1.0 + (heat_risk × 1.5)
storm_mult = 1.0 + (storm_risk × 2.0)
total_mult = flood_mult × heat_mult × storm_mult (capped at 5.0x)
adjusted_premium = base_premium × total_mult
```

---

### BONUS: Satellite Imagery Analysis (Gemma-3-27B)
```bash
POST /api/analyze-satellite?image_url=https://...&city=Mumbai&year=2050
```

**Response:**
```json
{
  "satellite_image_url": "https://...",
  "detected_features": [
    "High urban density zones",
    "Coastal infrastructure vulnerable to flooding",
    "Limited green space for heat mitigation"
  ],
  "risk_assessment": "Moderate-to-high vulnerability to compound climate impacts",
  "confidence": 0.82
}
```

---

### T7: Demo Cache Management
```bash
# Check current cache
GET /api/demo-cache

# Clear cache
GET /api/demo-cache?clear=true

# Warmup cache with 9 pre-computed scenarios
POST /api/warmup-cache
```

---

## 🔧 Featherless AI Models Used

| Task | Model | Purpose |
|------|-------|---------|
| T4 | Qwen/Qwen2.5-72B-Instruct | Generate 3-sentence risk briefs + 2 adaptation actions |
| T5 | Qwen/Qwen2.5-7B-Instruct | Generate one-line insurance explanation |
| T6 | Qwen/Qwen2.5-7B-Instruct | Parse city search queries to coordinates |
| BONUS | Gemma-3-27B-Vision | Analyze satellite imagery for climate vulnerabilities |

All models accessed via OpenAI-compatible SDK from Featherless AI (https://featherless.ai/v1).

---

## 📊 Data Sources

| Data | Source | Cost |
|------|--------|------|
| City geocoding | Open-Meteo | Free |
| Risk scenarios | IPCC AR6 SSP2-4.5 | Public |
| Building geometry | OpenStreetMap | Free |
| AI inference | Featherless AI | Pay-as-you-go |

---

## 🏗️ Project Structure

```
terrawatch/
├── backend/
│   ├── main.py                 # FastAPI app + all endpoints
│   ├── config.py               # Configuration (API keys, URLs)
│   ├── models.py               # Pydantic response models
│   ├── risk_engine.py          # Risk calculation + IPCC scenarios
│   ├── insurance_engine.py     # Premium calculation engine
│   └── ai_client.py            # Featherless AI client
├── data/
│   ├── mock_risk_data.csv      # Mock climate risk data
│   └── demo_cache.json         # Pre-cached 9 scenarios
├── scripts/
│   └── warmup_cache.py         # Cache warmup script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (FEATHERLESS_API_KEY)
└── README.md                   # This file
```

---

## 🎯 Demo Script (90 seconds)

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Search Mumbai
cities = requests.get(f"{BASE_URL}/api/search", params={"q": "Mumbai"}).json()
mumbai = cities[0]
lat, lng = mumbai["latitude"], mumbai["longitude"]

# 2. Get 2050 risk
risk = requests.get(
    f"{BASE_URL}/api/risk",
    params={"lat": lat, "lng": lng, "year": 2050}
).json()
print(f"Mumbai 2050 Risk Level: {risk['risk_level']} (CRI: {risk['climate_risk_index']})")

# 3. Get AI narration
narration = requests.post(
    f"{BASE_URL}/api/narrate",
    params={"city": "Mumbai", "lat": lat, "lng": lng, "year": 2050, "live": True}
).json()
print(f"Brief: {narration['risk_brief']}")
print(f"Actions: {narration['adaptation_actions']}")

# 4. Get insurance quote
insurance = requests.get(
    f"{BASE_URL}/api/insurance",
    params={"city": "Mumbai", "lat": lat, "lng": lng, "year": 2050, "live": True}
).json()
print(f"Premium: ${insurance['adjusted_premium']} (${insurance['base_premium']} × {insurance['total_multiplier']}x)")

# 5. Repeat for Lagos and Miami...
```

---

## 🔐 Environment Setup

Create `.env` file:
```bash
FEATHERLESS_API_KEY=your_api_key_here
BASE_URL=https://api.featherless.ai/v1
```

Get API key from: https://featherless.ai

---

## 📈 Key Features

✅ **Hyper-Local Intelligence**
- Street-level climate risk scoring
- Asset-specific damage estimates
- Neighborhood-aware adaptation planning

✅ **AI-Powered Insights**
- Plain-English risk briefs (Qwen-72B)
- Insurance premium explanations (Qwen-7B)
- Satellite imagery analysis (Gemma-3-27B)

✅ **Scalable & Fast**
- Demo cache for offline operation
- Asyncio for concurrent requests
- Pre-computed 9-scenario cache

✅ **Open & Accessible**
- City-agnostic (works for any city on Earth)
- Free data sources (Open-Meteo, IPCC, OSM)
- OpenAI-compatible SDK

---

## 🌱 SDG Alignment

| SDG | Target | Implementation |
|-----|--------|-----------------|
| 13: Climate Action | 13.1 Strengthen resilience | Risk scores guide infrastructure adaptation |
| 13: Climate Action | 13.3 Education & awareness | Plain-English narration for stakeholders |
| 11: Sustainable Cities | 11.5 Reduce disaster impact | Hyper-local vulnerability mapping |
| 1: No Poverty | 1.5 Resilience of vulnerable | Equity-focused adaptation intelligence |

---

## 🚧 Future Enhancements

- [ ] Frontend: React + Leaflet.js interactive map with time slider
- [ ] Real-time Open-Meteo weather feed integration
- [ ] Multi-hazard compound risk modeling
- [ ] n8n workflow automation trigger for parametric insurance
- [ ] Ensemble risk modeling (IPCC AR6 multi-model uncertainty)
- [ ] Cost-benefit analysis tool for adaptation investments

---

## 📞 Support

- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **OpenAPI Schema:** http://localhost:8000/openapi.json
- **Featherless API:** https://featherless.ai
- **IPCC AR6:** https://www.ipcc.ch/

---

## 📜 License

Open source for climate action. Use freely to save lives.

---

**Last Updated:** March 2026  
**Status:** 7/7 Tasks Complete ✅
