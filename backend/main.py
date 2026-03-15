from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json
import logging
from typing import List, Optional
import asyncio

# Import local modules
from backend.models import (
    RiskResponse, NarrateResponse, InsuranceResponse, 
    CitySearchResponse, VisionAnalysisResponse
)
from backend.risk_engine import get_risk_data, risk_label
from backend.insurance_engine import InsuranceEngine
from backend.ai_client import FeatherlessAIClient
from backend.config import FEATHERLESS_API_KEY

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
            "GET /api/search",
            "POST /api/narrate",
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

@app.get("/api/risk", response_model=RiskResponse)
async def get_risk(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year")
):
    """
    T3: Get climate risk data for a location and year
    
    Returns:
    - Flood, heat, and storm risk scores
    - Climate Risk Index (0-100)
    - Risk level classification
    - Estimated economic damage
    """
    try:
        risk_data = get_risk_data(lat, lng, year)
        
        if risk_data is None:
            raise HTTPException(
                status_code=404,
                detail="No risk data available for the given coordinates"
            )
        
        return RiskResponse(**risk_data)
    
    except Exception as e:
        logger.error(f"Error fetching risk data: {e}")
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
                    "count": 10,
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

@app.post("/api/narrate", response_model=NarrateResponse)
async def narrate_risk(
    city: str = Query(..., description="City name"),
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year"),
    live: bool = Query(False, description="Use live AI inference (True) or cache (False)")
):
    """
    T4: Generate AI-powered risk narration
    Uses Qwen-72B to create plain-English risk brief + adaptation actions
    
    Parameters:
    - live: Set to True for live AI inference, False to use cache
    """
    try:
        # Get risk data
        risk_data = get_risk_data(lat, lng, year)
        if risk_data is None:
            raise HTTPException(status_code=404, detail="Risk data not found")
        
        # Check cache first if not live
        cache_key = f"{city}_{year}_{lat:.2f}_{lng:.2f}"
        
        if not live and cache_key in demo_cache:
            logger.info(f"Using cached narration for {cache_key}")
            return NarrateResponse(
                risk_brief=demo_cache[cache_key]["risk_brief"],
                adaptation_actions=demo_cache[cache_key]["adaptation_actions"],
                cached=True
            )
        
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
            
            return NarrateResponse(
                risk_brief=narration_data.get("risk_brief", ""),
                adaptation_actions=narration_data.get("adaptation_actions", []),
                cached=False
            )
        
        except Exception as ai_error:
            logger.error(f"AI generation failed: {ai_error}")
            # Fallback to template
            fallback_brief = f"{city} faces escalating climate risks by {year} across flood, heat, and storm hazards. Infrastructure and vulnerable populations require immediate adaptation planning. Insurance and development decisions must incorporate these hyper-local projections."
            fallback_actions = [
                "Implement community-based early warning systems and evacuation plans for flood events",
                "Expand urban green spaces and cool roofs to reduce heat island effects and lower energy demand"
            ]
            
            return NarrateResponse(
                risk_brief=fallback_brief,
                adaptation_actions=fallback_actions,
                cached=False
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in narrate endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# T5: INSURANCE ENDPOINT
# ============================================================================

@app.get("/api/insurance", response_model=InsuranceResponse)
async def get_insurance(
    city: str = Query(..., description="City name"),
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year"),
    live: bool = Query(False, description="Use live AI inference")
):
    """
    T5: Calculate climate-adjusted insurance premiums
    Uses Qwen-7B to generate premium increase explanation
    
    Parameters:
    - Base premium: $1,200
    - Multipliers based on flood (2.5x weight), heat (1.5x), storm (2.0x)
    - live: Set to True for AI explanation, False for fallback
    """
    try:
        # Get risk data
        risk_data = get_risk_data(lat, lng, year)
        if risk_data is None:
            raise HTTPException(status_code=404, detail="Risk data not found")
        
        # Check cache
        cache_key = f"insurance_{city}_{year}_{lat:.2f}_{lng:.2f}"
        
        if not live and cache_key in demo_cache:
            logger.info(f"Using cached insurance for {cache_key}")
            cached_data = demo_cache[cache_key]
            return InsuranceResponse(**cached_data)
        
        # Calculate premium
        insurance_data = await insurance_engine.get_insurance_estimate(
            city=city,
            flood_risk=risk_data["flood_risk"],
            heat_risk=risk_data["heat_risk"],
            storm_risk=risk_data["storm_risk"],
            use_live_ai=live
        )
        
        # Cache result
        demo_cache[cache_key] = insurance_data
        
        return InsuranceResponse(**insurance_data)
    
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
    uvicorn.run(app, host="0.0.0.0", port=8000)