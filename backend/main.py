from fastapi import FastAPI, Query, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json
import logging
from typing import List, Optional
import asyncio
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Import local modules
from models import (
    RiskResponse, NarrateResponse, InsuranceResponse, 
    CitySearchResponse, VisionAnalysisResponse,
    RootResponse, HealthResponse, CityRiskResponse,
    RealtimeAnalysisResponse, DemoCacheResponse, WarmupCacheResponse
)
from fastapi import APIRouter
from typing import Union

router = APIRouter(prefix="/api/v1")
from risk_engine import get_risk_data, risk_label, get_risk_trends
from insurance_engine import get_insurance_estimate
from ai_client import generate_narration, analyze_satellite_imagery
from config import FEATHERLESS_API_KEY, ALLOWED_ORIGINS, TERRAWATCH_API_KEY

import contextvars
import uuid
import datetime
import os
from prometheus_fastapi_instrumentator import Instrumentator

# Correlation ID Context Variable
correlation_id_ctx_var = contextvars.ContextVar("correlation_id", default=None)

# Setup logging
class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_ctx_var.get() or "N/A"
        return True

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
            "correlation_id": getattr(record, "correlation_id", "N/A")
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    is_prod = os.getenv("ENV", "development").lower() == "production"
    
    # Custom handler
    handler = logging.StreamHandler()
    handler.addFilter(CorrelationIdFilter())
    
    if is_prod:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s"
        )
    handler.setFormatter(formatter)
    
    # Apply to root logger
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
    # Apply to uvicorn and fastapi loggers
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        logger_to_configure = logging.getLogger(logger_name)
        for h in logger_to_configure.handlers[:]:
            logger_to_configure.removeHandler(h)
        logger_to_configure.addHandler(handler)
        logger_to_configure.setLevel(log_level)
        logger_to_configure.propagate = False

# Call immediately on module load
setup_logging()
logger = logging.getLogger(__name__)

class CorrelationIdMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = scope.get("headers", [])
        
        def get_header(name):
            name_bytes = name.lower().encode("latin1")
            for k, v in headers:
                if k == name_bytes:
                    return v.decode("latin1")
            return None

        corr_id = get_header("x-request-id") or get_header("x-correlation-id")
        if not corr_id:
            corr_id = str(uuid.uuid4())

        token = correlation_id_ctx_var.set(corr_id)

        # Inject X-Request-ID if not present
        if not get_header("x-request-id"):
            headers.append((b"x-request-id", corr_id.encode("latin1")))
            scope["headers"] = headers

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                resp_headers = message.get("headers", [])
                has_x_request_id = False
                for k, v in resp_headers:
                    if k == b"x-request-id":
                        has_x_request_id = True
                        break
                if not has_x_request_id:
                    resp_headers.append((b"x-request-id", corr_id.encode("latin1")))
                    message["headers"] = resp_headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            correlation_id_ctx_var.reset(token)

import redis
import threading
import time

class HybridCache:
    def __init__(self, redis_url="redis://localhost:6379/0", expire_seconds=300):
        self.expire_seconds = expire_seconds
        self.redis_client = None
        self.use_redis = False
        
        # Thread-safe process memory fallback
        self.memory_cache = {}
        self.memory_cache_lock = threading.Lock()
        
        try:
            self.redis_client = redis.from_url(redis_url, socket_timeout=1.0, socket_connect_timeout=1.0)
            if self.redis_client.ping():
                self.use_redis = True
                logger.info("Connected to Redis cache successfully.")
            else:
                logger.warning("Redis ping failed. Falling back to in-memory cache.")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to thread-safe in-memory cache.")

    def get(self, key: str):
        if self.use_redis:
            try:
                val = self.redis_client.get(key)
                if val:
                    return val.decode("utf-8")
                return None
            except Exception as e:
                logger.warning(f"Redis get failed: {e}. Falling back to in-memory cache for this read.")
        
        with self.memory_cache_lock:
            cached = self.memory_cache.get(key)
            if cached:
                val, expires_at = cached
                if time.time() < expires_at:
                    return val
                else:
                    del self.memory_cache[key]
            return None

    def set(self, key: str, value: str, expire: int = None):
        exp = expire or self.expire_seconds
        if self.use_redis:
            try:
                self.redis_client.setex(key, exp, value)
                return
            except Exception as e:
                logger.warning(f"Redis set failed: {e}. Falling back to in-memory cache for this write.")
        
        with self.memory_cache_lock:
            self.memory_cache[key] = (value, time.time() + exp)

    def clear(self):
        if self.use_redis:
            try:
                self.redis_client.flushdb()
                logger.info("Cleared Redis cache.")
            except Exception as e:
                logger.warning(f"Redis flush failed: {e}")
        
        with self.memory_cache_lock:
            self.memory_cache.clear()
            logger.info("Cleared in-memory cache.")

class CachingMiddleware:
    def __init__(self, app, cache: HybridCache, paths_to_cache=None):
        self.app = app
        self.cache = cache
        self.paths_to_cache = paths_to_cache or [
            "/api/v1/risk", "/api/v1/cities", "/api/v1/search", 
            "/api/v1/narrate", "/api/v1/insurance", "/api/v1/realtime-analysis"
        ]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "GET":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        if not any(path.startswith(p) for p in self.paths_to_cache):
            await self.app(scope, receive, send)
            return

        query_string = scope.get("query_string", b"").decode("latin1")
        cache_key = f"cache:{path}:{query_string}"

        # Check cache
        cached_val = self.cache.get(cache_key)
        if cached_val:
            try:
                data = json.loads(cached_val)
                body = data["body"].encode("utf-8")
                status = data["status_code"]
                headers = [(k.encode("latin1"), v.encode("latin1")) for k, v in data["headers"].items()]
                
                # Check if x-cache-hit is already in headers
                has_cache_header = False
                for k, v in headers:
                    if k == b"x-cache-hit":
                        has_cache_header = True
                        break
                if not has_cache_header:
                    headers.append((b"x-cache-hit", b"True"))
                
                await send({
                    "type": "http.response.start",
                    "status": status,
                    "headers": headers
                })
                await send({
                    "type": "http.response.body",
                    "body": body
                })
                return
            except Exception as e:
                logger.warning(f"Error serving from cache: {e}")

        response_body = bytearray()
        response_status = [200]
        response_headers = []

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_status[0] = message["status"]
                response_headers.extend(message.get("headers", []))
                # Add X-Cache-Hit header
                message["headers"] = message.get("headers", []) + [(b"x-cache-hit", b"False")]
            elif message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))
            await send(message)

        await self.app(scope, receive, send_wrapper)

        if response_status[0] == 200 and response_body:
            try:
                headers_dict = {}
                for k, v in response_headers:
                    headers_dict[k.decode("latin1")] = v.decode("latin1")
                
                cache_data = {
                    "body": response_body.decode("utf-8"),
                    "status_code": response_status[0],
                    "headers": headers_dict
                }
                self.cache.set(cache_key, json.dumps(cache_data))
            except Exception as e:
                logger.warning(f"Failed to cache response: {e}")

# Initialize slowapi rate limiter with default 60/minute limit
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# Initialize FastAPI app
app = FastAPI(
    title="TerraWatch API",
    description="AI-Powered Hyper-Local Climate Risk Intelligence Platform",
    version="1.0.0"
)

# Initialize HybridCache
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
hybrid_cache = HybridCache(redis_url=redis_url)

# SlowAPI configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caching Middleware (added before CorrelationIdMiddleware so correlation id runs first on requests)
app.add_middleware(CachingMiddleware, cache=hybrid_cache)

# Correlation ID Middleware
app.add_middleware(CorrelationIdMiddleware)

# Prometheus instrumentator setup
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

@app.on_event("startup")
async def startup_event():
    # Setup logging again at startup to override configurations initialized by uvicorn
    setup_logging()

# Initialize engines
# ai_client class removed

# Demo cache for pre-computed scenarios
demo_cache = {}

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    import os
    env_key = os.getenv("TERRAWATCH_API_KEY")
    if env_key and x_api_key != env_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@router.get("/", response_model=RootResponse)
def root():
    """Root endpoint - API status"""
    return {
        "message": "TerraWatch API running",
        "version": "1.0.0",
        "endpoints": [
            "GET /api/v1/risk",
            "GET /api/v1/cities",
            "GET /api/v1/search",
            "GET /api/v1/narrate",
            "GET /api/v1/insurance",
            "POST /api/v1/analyze-satellite",
            "GET /api/v1/demo-cache"
        ]
    }

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# ============================================================================
# T3: RISK ENDPOINT
# ============================================================================

# ============================================================================
# T3: RISK ENDPOINT
# ============================================================================

@router.get("/risk", response_model=Union[RiskResponse, List[CityRiskResponse]])
@limiter.limit("10/minute")
async def get_risk(
    request: Request,
    lat: Optional[float] = Query(None, ge=-90, le=90, description="Latitude (optional)"),
    lng: Optional[float] = Query(None, ge=-180, le=180, description="Longitude (optional)"),
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

@router.get("/cities", response_model=List[CityRiskResponse])
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

@router.get("/search", response_model=List[CitySearchResponse])
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
# REALTIME ANALYSIS ENDPOINT
# ============================================================================

@router.get("/realtime-analysis", response_model=RealtimeAnalysisResponse)
@limiter.limit("10/minute")
async def get_realtime_analysis(
    request: Request,
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year"),
    city: str = Query(..., description="City name"),
    live: bool = Query(True, description="Whether to use live AI analysis")
):
    """
    Get comprehensive real-time analysis (includes trends and AI insights)
    """
    try:
        # Get risk data
        risk_data = get_risk_data(lat, lng, year)
        if risk_data is None:
            raise HTTPException(status_code=404, detail="Risk data not found")
            
        # Get trends
        trends = get_risk_trends(lat, lng, year)
        
        # Get AI narration
        cache_key = f"{city}_{year}_{lat:.2f}_{lng:.2f}"
        if cache_key in demo_cache:
            ai_insights = demo_cache[cache_key]
        else:
            if live:
                try:
                    ai_insights = await generate_narration(
                        city=city,
                        latitude=lat,
                        longitude=lng,
                        year=year,
                        flood_risk=risk_data["flood_risk"],
                        heat_risk=risk_data["heat_risk"],
                        storm_risk=risk_data["storm_risk"],
                        damage_estimate=risk_data["damage_estimate"]
                    )
                    demo_cache[cache_key] = ai_insights
                except Exception as ai_error:
                    logger.error(f"Realtime AI generation failed: {ai_error}")
                    fallback_brief = f"{city} faces escalating climate risks by {year} across flood, heat, and storm hazards. Infrastructure and vulnerable populations require immediate adaptation planning. Insurance and development decisions must incorporate these hyper-local projections."
                    fallback_actions = [
                        "Implement community-based early warning systems and evacuation plans for flood events",
                        "Expand urban green spaces and cool roofs to reduce heat island effects and lower energy demand"
                    ]
                    ai_insights = {
                        "risk_brief": fallback_brief,
                        "adaptation_actions": fallback_actions,
                        "cached": False
                    }
            else:
                fallback_brief = f"{city} faces escalating climate risks by {year} across flood, heat, and storm hazards. Infrastructure and vulnerable populations require immediate adaptation planning. Insurance and development decisions must incorporate these hyper-local projections."
                fallback_actions = [
                    "Implement community-based early warning systems and evacuation plans for flood events",
                    "Expand urban green spaces and cool roofs to reduce heat island effects and lower energy demand"
                ]
                ai_insights = {
                    "risk_brief": fallback_brief,
                    "adaptation_actions": fallback_actions,
                    "cached": False
                }
                
        return {
            "location": {
                "city": city,
                "latitude": lat,
                "longitude": lng
            },
            "current_risks": {
                "flood_risk": risk_data["flood_risk"],
                "heat_risk": risk_data["heat_risk"],
                "storm_risk": risk_data["storm_risk"],
                "climate_risk_index": risk_data["climate_risk_index"],
                "risk_level": risk_data["risk_level"],
                "damage_estimate": risk_data["damage_estimate"]
            },
            "risk_trends": trends,
            "ai_insights": ai_insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in realtime-analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# T4: NARRATION ENDPOINT
# ============================================================================

@router.get("/narrate", response_model=NarrateResponse)
@limiter.limit("10/minute")
async def narrate_risk(
    request: Request,
    city: str = Query(..., description="City name"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year"),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="Latitude"),
    lng: Optional[float] = Query(None, ge=-180, le=180, description="Longitude"),
    live: bool = Query(True, description="Whether to use live AI"),
    api_key_valid: None = Depends(verify_api_key)
):
    """
    Generate AI-powered risk narration for a city
    """
    try:
        if lat is None or lng is None:
            # Find city coordinates from our data
            from backend.risk_engine import data
            city_match = next((row for row in data if row['city'].lower() == city.lower()), None)
            if not city_match:
                raise HTTPException(status_code=404, detail=f"City '{city}' not found")
            
            lat = float(city_match['lat'])
            lng = float(city_match['lng'])
        
        # Get risk data
        risk_data = get_risk_data(lat, lng, year)
        if risk_data is None:
            raise HTTPException(status_code=404, detail="Risk data not found")
        
        # Check cache first
        cache_key = f"{city}_{year}_{lat:.2f}_{lng:.2f}"
        
        if cache_key in demo_cache:
            logger.info(f"Using cached narration for {cache_key}")
            return demo_cache[cache_key]
            
        if not live:
            fallback_brief = f"{city} faces escalating climate risks by {year} across flood, heat, and storm hazards. Infrastructure and vulnerable populations require immediate adaptation planning. Insurance and development decisions must incorporate these hyper-local projections."
            fallback_actions = [
                "Implement community-based early warning systems and evacuation plans for flood events",
                "Expand urban green spaces and cool roofs to reduce heat island effects and lower energy demand"
            ]
            return {
                "risk_brief": fallback_brief,
                "adaptation_actions": fallback_actions,
                "cached": False
            }
        
        # Generate using Featherless AI (Qwen-72B)
        try:
            narration_data = await generate_narration(
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

@router.get("/insurance", response_model=InsuranceResponse)
@limiter.limit("10/minute")
async def get_insurance(
    request: Request,
    city: str = Query(..., description="City name"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year"),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="Latitude"),
    lng: Optional[float] = Query(None, ge=-180, le=180, description="Longitude"),
    live: bool = Query(True, description="Whether to use live AI"),
    api_key_valid: None = Depends(verify_api_key)
):
    """
    Calculate climate-adjusted insurance premiums for a city
    """
    try:
        if lat is None or lng is None:
            # Find city coordinates from our data
            from backend.risk_engine import data
            city_match = next((row for row in data if row['city'].lower() == city.lower()), None)
            if not city_match:
                raise HTTPException(status_code=404, detail=f"City '{city}' not found")
            
            lat = float(city_match['lat'])
            lng = float(city_match['lng'])
        
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
        insurance_data = await get_insurance_estimate(
            city=city,
            flood_risk=risk_data["flood_risk"],
            heat_risk=risk_data["heat_risk"],
            storm_risk=risk_data["storm_risk"],
            use_live_ai=live
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

@router.post("/analyze-satellite", response_model=VisionAnalysisResponse)
@limiter.limit("10/minute")
async def analyze_satellite(
    request: Request,
    image_url: str = Query(..., description="URL to satellite image"),
    city: str = Query(..., description="City name"),
    year: int = Query(2024, ge=2024, le=2050, description="Projection year"),
    api_key_valid: None = Depends(verify_api_key)
):
    """
    BONUS: Analyze satellite imagery for climate risks
    Uses Gemma-3-27B vision model to identify urban vulnerability
    """
    try:
        vision_data = await analyze_satellite_imagery(
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

@router.get("/demo-cache", response_model=DemoCacheResponse)
async def get_demo_cache(clear: bool = Query(False)):
    """
    T7: Pre-cache demo scenarios for offline demo
    Returns current cache state or clears it if requested
    """
    if clear:
        demo_cache.clear()
        hybrid_cache.clear()
        return {"status": "Cache cleared", "items": 0}
    
    return {
        "status": "OK",
        "cached_items": len(demo_cache),
        "cache_keys": list(demo_cache.keys())
    }

# ============================================================================
# BATCH DEMO CACHE WARMING
# ============================================================================

@router.post("/warmup-cache", response_model=WarmupCacheResponse)
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
                narration_data = await generate_narration(
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
                insurance_data = await get_insurance_estimate(
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

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)