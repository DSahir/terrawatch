# ⚡ TerraWatch - Quick Reference Card

## 🚀 START SERVER

```bash
cd /Users/sameeksha/Documents/Career/hackthon/girls_in_code/terrawatch
source venv/bin/activate
uvicorn backend.main:app --reload
```

**Output should be:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 📍 BASE URL
```
http://localhost:8000
```

---

## 🌐 EASIEST WAY TO TEST: Interactive Docs

### Swagger UI (Recommended)
```
http://localhost:8000/docs
```

You can click "Try it out" on each endpoint!

### Alternative: ReDoc
```
http://localhost:8000/redoc
```

---

## 📡 Quick API Tests (Copy & Paste URLs)

### 1. Health Check
```
http://localhost:8000/health
```
✅ Returns: `{"status": "healthy"}`

### 2. Search City
```
http://localhost:8000/api/search?q=Mumbai
```
✅ Returns: City info with lat/lng

### 3. Risk 2024 (Current)
```
http://localhost:8000/api/risk?lat=19.076&lng=72.8777&year=2024
```
✅ Lower risk values

### 4. Risk 2050 (Future)
```
http://localhost:8000/api/risk?lat=19.076&lng=72.8777&year=2050
```
✅ Higher risk values

### 5. Insurance Quote
```
http://localhost:8000/api/insurance?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=false
```
✅ Returns: Premium calculation

### 6. AI Narration (Cached - Fast)
```
http://localhost:8000/api/narrate?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=false
```
✅ Instant response

### 7. AI Narration (Live - Slow but Fresh)
```
http://localhost:8000/api/narrate?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=true
```
⏳ Wait 2-10 seconds

### 8. Cache Status
```
http://localhost:8000/api/demo-cache
```
✅ Shows cached items

---

## 🌍 Test Different Cities

| City | Coords | Example URL |
|------|--------|------------|
| Mumbai | 19.076, 72.8777 | `?lat=19.076&lng=72.8777` |
| Lagos | 6.5244, 3.3792 | `?lat=6.5244&lng=3.3792` |
| Miami | 25.7617, -80.1918 | `?lat=25.7617&lng=-80.1918` |
| Paris | 48.8566, 2.3522 | `?lat=48.8566&lng=2.3522` |
| London | 51.5074, -0.1278 | `?lat=51.5074&lng=-0.1278` |
| Tokyo | 35.6762, 139.6503 | `?lat=35.6762&lng=139.6503` |

---

## ⏱️ Test Different Years

- **2024** = Current (baseline)
- **2030** = +30% risk (IPCC)
- **2035** = Between current & 2050
- **2050** = +70% risk (IPCC)

### Example URLs
```
2024: ?year=2024
2030: ?year=2030
2035: ?year=2035
2050: ?year=2050
```

---

## 📊 Response Patterns

### Risk Endpoint Response
```json
{
  "city": "Mumbai",
  "year": 2050,
  "flood_risk": 0.595,           ← 0 to 1 (percentage)
  "heat_risk": 0.567,            ← 0 to 1 (percentage)
  "storm_risk": 0.255,           ← 0 to 1 (percentage)
  "climate_risk_index": 57,      ← 0-100 score
  "risk_level": "High",          ← Low/Moderate/High/Severe
  "damage_estimate": 1245000.0   ← USD
}
```

### Insurance Endpoint Response
```json
{
  "base_premium": 1200,
  "total_multiplier": 6.95,      ← How much more expensive
  "adjusted_premium": 8340,      ← New price
  "explanation": "..."           ← Why it increased
}
```

### Narration Endpoint Response
```json
{
  "risk_brief": "...",           ← 3-sentence summary
  "adaptation_actions": [        ← 2 things to do
    "Action 1...",
    "Action 2..."
  ],
  "cached": false
}
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | Start server first |
| "404 Not Found" | Check URL spelling exactly |
| "500 Error" | Check .env has FEATHERLESS_API_KEY |
| Slow response (5+ sec) | Using ?live=true, wait for it |
| No results from search | Try different city name |

---

## 📚 Complete Endpoint List

| Method | Path | Purpose | Speed |
|--------|------|---------|-------|
| GET | / | API info | <10ms |
| GET | /health | Health check | <10ms |
| GET | /api/search | Find cities | <200ms |
| GET | /api/risk | Climate risk | <50ms |
| POST | /api/narrate (cache) | Risk brief | <100ms |
| POST | /api/narrate (live) | AI narration | 2-10s |
| GET | /api/insurance (cache) | Insurance quote | <100ms |
| GET | /api/insurance (live) | AI explanation | 1-5s |
| GET | /api/demo-cache | Cache status | <10ms |
| POST | /api/warmup-cache | Pre-compute cache | 30-90s |

---

## 🎯 Full URL Examples

### Search Mumbai
```
http://localhost:8000/api/search?q=Mumbai
```

### Risk for Mumbai 2050
```
http://localhost:8000/api/risk?lat=19.076&lng=72.8777&year=2050
```

### Insurance Mumbai 2050
```
http://localhost:8000/api/insurance?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=false
```

### Narration Mumbai 2050 (Live AI)
```
http://localhost:8000/api/narrate?city=Mumbai&lat=19.076&lng=72.8777&year=2050&live=true
```

---

## 💡 Pro Tips

1. **Use /docs first** - Most visual and interactive
2. **Test 2024 vs 2050** - See how risks increase
3. **Compare cities** - Mumbai vs Miami vs Paris
4. **Live AI takes time** - Use cached endpoints for quick testing
5. **Check browser console** - See full JSON responses

---

## ✅ Quick Test Sequence (5 minutes)

1. Open: `http://localhost:8000/docs`
2. Click "Try it out" on `/api/search`
3. Search "Mumbai"
4. Get latitude/longitude from response
5. Click "Try it out" on `/api/risk`
6. Paste coordinates, test 2024 vs 2050
7. Click "Try it out" on `/api/insurance`
8. See how premium changes

Done! 🎉

---

**All 7 tasks + bonus implemented and ready to test!**
