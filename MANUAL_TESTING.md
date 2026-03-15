# 🌍 TerraWatch - Manual API Testing Guide

## Step 1: Start the Server ✅

Open Terminal 1 and run:

```bash
cd /Users/sameeksha/Documents/Career/hackthon/girls_in_code/terrawatch
source venv/bin/activate
uvicorn backend.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 [Ctrl+C to quit]
INFO:     Application startup complete
```

**✓ Keep this terminal open!**

---

## Step 2: Open Your Web Browser

Open a new browser tab and test each endpoint below.

**Base URL:** `http://localhost:8000`

---

## 📡 Testing Endpoints (One by One)

### 1️⃣ HEALTH CHECK
**Purpose:** Verify API is running

**URL to paste in browser:**
```
http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy"
}
```

---

### 2️⃣ ROOT ENDPOINT (API Info)
**Purpose:** See available endpoints

**URL:**
```
http://localhost:8000/
```

**Expected Response:**
```json
{
  "message": "TerraWatch API running",
  "version": "1.0.0",
  "endpoints": [
    "GET /api/risk",
    "GET /api/search",
    "POST /api/narrate",
    "GET /api/insurance",
    "POST /api/analyze-satellite",
    "GET /api/demo-cache"
  ]
}
```

---

### 3️⃣ SEARCH CITIES (T6)
**Purpose:** Find a city and get its coordinates

**URL:**
```
http://localhost:8000/api/search?q=Mumbai
```

**Expected Response:**
```json
[
  {
    "city": "Mumbai",
    "country": "India",
    "latitude": 19.076,
    "longitude": 72.8777,
    "admin1": "Maharashtra",
    "population": 20411000
  }
]
```

**Try other cities:**
- `?q=Lagos`
- `?q=Miami`
- `?q=Paris`

---

### 4️⃣ GET RISK DATA (T3)
**Purpose:** Get climate risk for a location and year

**URLs to test:**

#### Mumbai 2024 (Current):
```
http://localhost:8000/api/risk?lat=19.076&lng=72.8777&year=2024
```

#### Mumbai 2035 (Future):
```
http://localhost:8000/api/risk?lat=19.076&lng=72.8777&year=2035
```

#### Mumbai 2050 (Far Future):
```
http://localhost:8000/api/risk?lat=19.076&lng=72.8777&year=2050
```

#### Miami 2050:
```
http://localhost:8000/api/risk?lat=25.7617&lng=-80.1918&year=2050
```

**Expected Response:**
```json
{
  "city": "Mumbai",
  "year": 2024,
  "latitude": 19.076,
  "longitude": 72.8777,
  "flood_risk": 0.35,
  "heat_risk": 0.42,
  "storm_risk": 0.15,
  "climate_risk_index": 39,
  "risk_level": "Moderate",
  "damage_estimate": 189000.0
}
```

**Notice:** 
- Flood/heat/storm increase from 2024 → 2035 → 2050
- Damage estimates also increase
- Risk level changes: Low → Moderate → High

---

### 5️⃣ INTERACTIVE API DOCS
**Purpose:** See all endpoints with interactive testing

**URL:**
```
http://localhost:8000/docs
```

This opens **Swagger UI** where you can:
- See all endpoints
- See request/response schemas
- Test endpoints with a GUI

**Alternative (ReDoc):**
```
http://localhost:8000/redoc
```

---

### 6️⃣ NARRATION ENDPOINT (T4) - CACHED
**Purpose:** Get AI-generated risk brief (using cache for speed)

**URL (cached - instant):**
```
http://localhost:8000/api/narrate?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=false
```

**Expected Response:**
```json
{
  "risk_brief": "Mumbai faces escalating climate risks by 2050 across flood, heat, and storm hazards...",
  "adaptation_actions": [
    "Implement community-based early warning systems...",
    "Expand urban green spaces and cool roofs..."
  ],
  "cached": false
}
```

**Note:** This uses cache so it returns instantly.

---

### 7️⃣ NARRATION ENDPOINT (T4) - LIVE AI
**Purpose:** Get AI-generated text using Featherless (Qwen-72B)

**⚠️ NOTE:** This is slower (2-10 seconds) because it calls Featherless AI

**URL (live AI):**
```
http://localhost:8000/api/narrate?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=true
```

**Expected Response (different each time):**
```json
{
  "risk_brief": "By 2050, Mumbai's 59.5% flood risk combined with 56.7% heat exposure creates severe climate vulnerability...",
  "adaptation_actions": [
    "Install comprehensive flood barriers and tidal barriers...",
    "Establish green infrastructure corridors..."
  ],
  "cached": false
}
```

**Try other cities:**
- `?q=Lagos&...&year=2050`
- `?q=Miami&...&year=2050`

---

### 8️⃣ INSURANCE PREMIUM (T5) - CACHED
**Purpose:** Calculate climate-adjusted insurance premium (cached)

**URL (cached - instant):**
```
http://localhost:8000/api/insurance?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=false
```

**Expected Response:**
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

**What this means:**
- Base: $1,200/year
- Adjusted: $8,340/year (6.95x more expensive)
- Reason: High flood risk

---

### 9️⃣ INSURANCE PREMIUM (T5) - LIVE AI
**Purpose:** Get AI explanation from Qwen-7B

**⚠️ NOTE:** Slower (1-5 seconds) due to AI call

**URL (live AI):**
```
http://localhost:8000/api/insurance?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=true
```

**Expected Response:**
```json
{
  "base_premium": 1200,
  "flood_multiplier": 2.49,
  "heat_multiplier": 1.85,
  "storm_multiplier": 1.51,
  "total_multiplier": 6.95,
  "adjusted_premium": 8340,
  "explanation": "Mumbai's escalating flood risk (59.5% by 2050) is the primary driver of the 595% premium increase.",
  "cached": false
}
```

---

### 🔟 DEMO CACHE STATUS (T7)
**Purpose:** Check what's cached in the system

**URL:**
```
http://localhost:8000/api/demo-cache
```

**Expected Response:**
```json
{
  "status": "OK",
  "cached_items": 0,
  "cache_keys": []
}
```

Initially empty. Once you test narration/insurance, it gets populated.

---

### 1️⃣1️⃣ WARMUP CACHE (T7)
**Purpose:** Pre-compute 9 demo scenarios (3 cities × 3 years)

**⚠️ NOTE:** This is slow (30-90 seconds) - DO THIS LAST

**URL (POST request):**
```
http://localhost:8000/api/warmup-cache
```

**To test this, you need to use a different method:**

**Option A: Use curl in Terminal 2:**
```bash
curl -X POST http://localhost:8000/api/warmup-cache
```

**Expected Response:**
```json
{
  "warmup_complete": true,
  "results": {
    "successful": 9,
    "failed": 0,
    "errors": []
  },
  "total_cached": 18
}
```

---

### 1️⃣2️⃣ CLEAR CACHE (T7)
**Purpose:** Clear all cached items

**URL:**
```
http://localhost:8000/api/demo-cache?clear=true
```

**Expected Response:**
```json
{
  "status": "Cache cleared",
  "items": 0
}
```

---

## 📋 Complete Testing Sequence

Copy and paste each URL in order:

### Session 1: Basic Tests (5 minutes)
1. `http://localhost:8000/health`
2. `http://localhost:8000/`
3. `http://localhost:8000/api/search?q=Mumbai`
4. `http://localhost:8000/api/risk?lat=19.076&lng=72.8777&year=2024`
5. `http://localhost:8000/api/risk?lat=19.076&lng=72.8777&year=2050`
6. `http://localhost:8000/api/insurance?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=false`
7. `http://localhost:8000/api/narrate?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=false`
8. `http://localhost:8000/api/demo-cache`

### Session 2: Live AI Tests (10-15 minutes) - OPTIONAL
9. `http://localhost:8000/api/narrate?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=true`
   - ⏳ Wait 2-10 seconds for response
10. `http://localhost:8000/api/insurance?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=true`
    - ⏳ Wait 1-5 seconds for response

### Session 3: Different Cities (5 minutes)
11. `http://localhost:8000/api/search?q=Lagos`
12. `http://localhost:8000/api/risk?lat=6.5244&lng=3.3792&year=2050`
13. `http://localhost:8000/api/insurance?city=Lagos&lat=6.5244&lng=3.3792&year=2050&live=false`

### Session 4: Interactive Docs (2 minutes)
14. `http://localhost:8000/docs` (Swagger UI)
15. `http://localhost:8000/redoc` (ReDoc)

---

## 🔍 Testing Different Cities & Years

### City Coordinates (for Copy-Paste)

| City | Latitude | Longitude | Year to Test |
|------|----------|-----------|--------------|
| Mumbai | 19.076 | 72.8777 | 2024, 2050 |
| Lagos | 6.5244 | 3.3792 | 2024, 2050 |
| Miami | 25.7617 | -80.1918 | 2024, 2050 |
| Paris | 48.8566 | 2.3522 | 2024, 2050 |
| London | 51.5074 | -0.1278 | 2024, 2050 |
| Tokyo | 35.6762 | 139.6503 | 2024, 2050 |
| Sydney | -33.8688 | 151.2093 | 2024, 2050 |
| New York | 40.7128 | -74.0060 | 2024, 2050 |
| Moscow | 55.7558 | 37.6173 | 2024, 2050 |
| Delhi | 28.6139 | 77.2090 | 2024, 2050 |
| Jakarta | -6.2 | 106.8 | 2024, 2050 |

### Test Template

Copy this and replace values:
```
http://localhost:8000/api/risk?lat=LATITUDE&lng=LONGITUDE&year=YEAR
```

Example with New York 2035:
```
http://localhost:8000/api/risk?lat=40.7128&lng=-74.0060&year=2035
```

---

## 📊 What to Look For

### Risk Endpoint
- ✅ **flood_risk** increases 2024 → 2050
- ✅ **heat_risk** increases 2024 → 2050
- ✅ **climate_risk_index** increases
- ✅ **risk_level** changes: Low → Moderate → High → Severe
- ✅ **damage_estimate** increases

### Narration Endpoint
- ✅ Response is plain English
- ✅ Contains 2 adaptation actions
- ✅ Mentions specific risks for the city/year
- ✅ Live vs cached marked correctly

### Insurance Endpoint
- ✅ **total_multiplier** increases with risk
- ✅ **adjusted_premium** is base × multiplier
- ✅ Explanation mentions primary risk driver
- ✅ Different for each city/year

---

## 🚀 Using Swagger UI (Easiest!)

Instead of pasting URLs, you can use the interactive docs:

**URL:**
```
http://localhost:8000/docs
```

This gives you:
- ✅ List of all endpoints
- ✅ Request parameters with descriptions
- ✅ "Try it out" button to test each endpoint
- ✅ See responses formatted nicely
- ✅ Full API schema

**This is the easiest way to test!**

---

## ❌ Troubleshooting

### "Connection refused"
```
❌ Make sure server is running: uvicorn backend.main:app --reload
```

### "Cannot GET /api/risk"
```
❌ Check the URL is exactly correct (case-sensitive)
❌ Check parameters are in the right format
```

### "500 Internal Server Error"
```
❌ Check Terminal 1 for error messages
❌ Make sure .env has FEATHERLESS_API_KEY
❌ Check internet connection
```

### Slow responses for ?live=true
```
⏳ Normal! Featherless AI takes 1-10 seconds
✅ Just wait for the response
```

---

## ✅ Success Checklist

- [ ] API starts without errors
- [ ] Health check returns `{"status": "healthy"}`
- [ ] Root endpoint shows version info
- [ ] Search for "Mumbai" returns coordinates
- [ ] Risk for 2024 shows lower values than 2050
- [ ] Insurance premium increases for 2050
- [ ] Narration generates text
- [ ] Cache status shows empty or items
- [ ] Swagger UI loads at `/docs`

---

**Ready to test? Start with:** `http://localhost:8000/docs`

This will be the easiest and most interactive way! 🎉
