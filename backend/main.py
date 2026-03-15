from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json
import logging
from typing import List, Optional
import asyncio

# Import local modules
from models import (
    RiskResponse, NarrateResponse, InsuranceResponse, 
    CitySearchResponse, VisionAnalysisResponse
)
from risk_engine import get_risk_data, risk_label
from insurance_engine import InsuranceEngine
from ai_client import FeatherlessAIClient
from config import FEATHERLESS_API_KEY

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TerraWatch API",
    description="AI-Powered Hyper-Local Climate Risk Intelligence Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
insurance_engine = InsuranceEngine()
ai_client = FeatherlessAIClient()

# Demo cache for pre-computed scenarios
demo_cache = {}

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Root endpoint - API status"""
    return {
        "message": "TerraWatch API running",
        "version": "1.0.0",
        "endpoints": [
            "GET /api/risk",
            "GET /api/cities",
            "GET /api/search",
            "GET /api/narrate",
            "GET /api/insurance",
            "POST /api/analyze-satellite",
            "GET /api/demo-cache"
        ]
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# ============================================================================
# T3: RISK ENDPOINT
# ============================================================================

# ============================================================================
# T3: RISK ENDPOINT
# ============================================================================

@app.get("/api/risk")
async def get_risk(
    lat = Query(None, description="Latitude (optional)"),
    lng = Query(None, description="Longitude (optional)"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year")
):
    """
    Get climate risk data
    
    If lat/lng provided: Returns risk data for specific location
    If lat/lng not provided: Returns risk data for all cities
    """
    try:
        if lat is not None and lng is not None:
            # Specific location query
            risk_data = get_risk_data(lat, lng, year)
            if risk_data is None:
                raise HTTPException(
                    status_code=404,
                    detail="No risk data available for the given coordinates"
                )
            return RiskResponse(**risk_data)
        else:
            # Return all cities
            from backend.risk_engine import get_all_cities_risk
            cities_data = get_all_cities_risk(year)
            return cities_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risk data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cities")
async def get_cities(year: int = Query(2024, ge=2024, le=2050, description="Projection year")):
    """
    Get all cities with risk data for a given year
    """
    try:
        from backend.risk_engine import get_all_cities_risk
        cities_data = get_all_cities_risk(year)
        return cities_data
    except Exception as e:
        logger.error(f"Error fetching cities data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# T6: CITY SEARCH & GEOCODING ENDPOINT
# ============================================================================

@app.get("/api/search", response_model=List[CitySearchResponse])
async def search_cities(
    q: str = Query(..., min_length=2, description="City name or partial match")
):
    """
    T6: Search for cities and get coordinates
    Uses Open-Meteo free geocoding API (no key required)
    
    Returns up to 10 matching cities with coordinates
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": q,
                    "count": 4,
                    "language": "en",
                    "format": "json"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if "results" in data:
                for result in data["results"]:
                    results.append(CitySearchResponse(
                        city=result.get("name", ""),
                        country=result.get("country", ""),
                        latitude=result.get("latitude", 0),
                        longitude=result.get("longitude", 0),
                        admin1=result.get("admin1", None),
                        population=result.get("population", None)
                    ))
            
            return results
    
    except Exception as e:
        logger.error(f"Error searching cities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# T4: NARRATION ENDPOINT
# ============================================================================

@app.get("/api/narrate")
async def narrate_risk(
    city: str = Query(..., description="City name"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year")
):
    """
    Generate AI-powered risk narration for a city
    """
    try:
        # Find city coordinates from our data
        from backend.risk_engine import data
        city_row = data[data['city'].str.lower() == city.lower()]
        if city_row.empty:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found")
        
        lat = float(city_row.iloc[0]['lat'])
        lng = float(city_row.iloc[0]['lng'])
        
        # Get risk data
        risk_data = get_risk_data(lat, lng, year)
        if risk_data is None:
            raise HTTPException(status_code=404, detail="Risk data not found")
        
        # Check cache first
        cache_key = f"{city}_{year}_{lat:.2f}_{lng:.2f}"
        
        if cache_key in demo_cache:
            logger.info(f"Using cached narration for {cache_key}")
            return demo_cache[cache_key]
        
        # Generate using Featherless AI (Qwen-72B)
        try:
            narration_data = await ai_client.generate_narration(
                city=city,
                latitude=lat,
                longitude=lng,
                year=year,
                flood_risk=risk_data["flood_risk"],
                heat_risk=risk_data["heat_risk"],
                storm_risk=risk_data["storm_risk"],
                damage_estimate=risk_data["damage_estimate"]
            )
            
            # Cache the result
            demo_cache[cache_key] = narration_data
            
            return narration_data
        
        except Exception as ai_error:
            logger.error(f"AI generation failed: {ai_error}")
            # Fallback to template
            fallback_brief = f"{city} faces escalating climate risks by {year} across flood, heat, and storm hazards. Infrastructure and vulnerable populations require immediate adaptation planning. Insurance and development decisions must incorporate these hyper-local projections."
            fallback_actions = [
                "Implement community-based early warning systems and evacuation plans for flood events",
                "Expand urban green spaces and cool roofs to reduce heat island effects and lower energy demand"
            ]
            1
            return {
                "risk_brief": fallback_brief,
                "adaptation_actions": fallback_actions,
                "cached": False
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in narrate endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# T5: INSURANCE ENDPOINT
# ============================================================================

@app.get("/api/insurance")
async def get_insurance(
    city: str = Query(..., description="City name"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year")
):
    """
    Calculate climate-adjusted insurance premiums for a city
    """
    try:
        # Find city coordinates from our data
        from backend.risk_engine import data
        city_row = data[data['city'].str.lower() == city.lower()]
        if city_row.empty:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found")
        
        lat = float(city_row.iloc[0]['lat'])
        lng = float(city_row.iloc[0]['lng'])
        
        # Get risk data
        risk_data = get_risk_data(lat, lng, year)
        if risk_data is None:
            raise HTTPException(status_code=404, detail="Risk data not found")
        
        # Check cache
        cache_key = f"insurance_{city}_{year}_{lat:.2f}_{lng:.2f}"
        
        if cache_key in demo_cache:
            logger.info(f"Using cached insurance for {cache_key}")
            return demo_cache[cache_key]
        
        # Calculate premium
        insurance_data = await insurance_engine.get_insurance_estimate(
            city=city,
            flood_risk=risk_data["flood_risk"],
            heat_risk=risk_data["heat_risk"],
            storm_risk=risk_data["storm_risk"],
            use_live_ai=False
        )
        
        # Cache result
        demo_cache[cache_key] = insurance_data
        
        return insurance_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in insurance endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BONUS: SATELLITE IMAGERY ANALYSIS
# ============================================================================

@app.post("/api/analyze-satellite", response_model=VisionAnalysisResponse)
async def analyze_satellite(
    image_url: str = Query(..., description="URL to satellite image"),
    city: str = Query(..., description="City name"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year")
):
    """
    BONUS: Analyze satellite imagery for climate risks
    Uses Gemma-3-27B vision model to identify urban vulnerability
    """
    try:
        vision_data = await ai_client.analyze_satellite_imagery(
            image_url=image_url,
            city=city,
            year=year
        )
        
        return VisionAnalysisResponse(
            satellite_image_url=image_url,
            detected_features=vision_data.get("detected_features", []),
            risk_assessment=vision_data.get("risk_assessment", ""),
            confidence=vision_data.get("confidence", 0.5)
        )
    
    except Exception as e:
        logger.error(f"Error analyzing satellite imagery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DEMO CACHE MANAGEMENT
# ============================================================================

@app.get("/api/demo-cache")
async def get_demo_cache(clear: bool = Query(False)):
    """
    T7: Pre-cache demo scenarios for offline demo
    Returns current cache state or clears it if requested
    """
    if clear:
        demo_cache.clear()
        return {"status": "Cache cleared", "items": 0}
    
    return {
        "status": "OK",
        "cached_items": len(demo_cache),
        "cache_keys": list(demo_cache.keys())
    }

# ============================================================================
# BATCH DEMO CACHE WARMING
# ============================================================================

@app.post("/api/warmup-cache")
async def warmup_demo_cache():
    """
    T7: Pre-compute and cache 9 demo scenarios
    3 cities × 3 years = 9 scenarios
    
    Cities: Mumbai, Lagos, Miami
    Years: 2024, 2035, 2050
    """
    demo_scenarios = [
        # Mumbai
        {"city": "Mumbai", "year": 2024, "lat": 19.0760, "lng": 72.8777},
        {"city": "Mumbai", "year": 2035, "lat": 19.0760, "lng": 72.8777},
        {"city": "Mumbai", "year": 2050, "lat": 19.0760, "lng": 72.8777},
        # Lagos
        {"city": "Lagos", "year": 2024, "lat": 6.5244, "lng": 3.3792},
        {"city": "Lagos", "year": 2035, "lat": 6.5244, "lng": 3.3792},
        {"city": "Lagos", "year": 2050, "lat": 6.5244, "lng": 3.3792},
        # Miami
        {"city": "Miami", "year": 2024, "lat": 25.7617, "lng": -80.1918},
        {"city": "Miami", "year": 2035, "lat": 25.7617, "lng": -80.1918},
        {"city": "Miami", "year": 2050, "lat": 25.7617, "lng": -80.1918},
    ]
    
    results = {"successful": 0, "failed": 0, "errors": []}
    
    for scenario in demo_scenarios:
        try:
            # Get risk data
            risk_data = get_risk_data(scenario["lat"], scenario["lng"], scenario["year"])
            if risk_data is None:
                results["failed"] += 1
                continue
            
            # Generate narration
            try:
                narration_data = await ai_client.generate_narration(
                    city=scenario["city"],
                    latitude=scenario["lat"],
                    longitude=scenario["lng"],
                    year=scenario["year"],
                    flood_risk=risk_data["flood_risk"],
                    heat_risk=risk_data["heat_risk"],
                    storm_risk=risk_data["storm_risk"],
                    damage_estimate=risk_data["damage_estimate"]
                )
                
                cache_key = f"{scenario['city']}_{scenario['year']}_{scenario['lat']:.2f}_{scenario['lng']:.2f}"
                demo_cache[cache_key] = narration_data
                
                # Generate insurance
                insurance_data = await insurance_engine.get_insurance_estimate(
                    city=scenario["city"],
                    flood_risk=risk_data["flood_risk"],
                    heat_risk=risk_data["heat_risk"],
                    storm_risk=risk_data["storm_risk"],
                    use_live_ai=True
                )
                
                insurance_cache_key = f"insurance_{scenario['city']}_{scenario['year']}_{scenario['lat']:.2f}_{scenario['lng']:.2f}"
                demo_cache[insurance_cache_key] = insurance_data
                
                results["successful"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{scenario['city']} {scenario['year']}: {str(e)}")
        
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"{scenario['city']} {scenario['year']}: {str(e)}")
    
    return {
        "warmup_complete": True,
        "results": results,
        "total_cached": len(demo_cache)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)