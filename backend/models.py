from pydantic import BaseModel
from typing import Optional, List

class RiskResponse(BaseModel):
    city: str
    year: int
    latitude: float
    longitude: float
    flood_risk: float
    heat_risk: float
    storm_risk: float
    climate_risk_index: int
    risk_level: str
    damage_estimate: float

class NarrateResponse(BaseModel):
    risk_brief: str
    adaptation_actions: List[str]
    cached: bool = False

class InsuranceResponse(BaseModel):
    base_premium: float
    flood_multiplier: float
    heat_multiplier: float
    storm_multiplier: float
    total_multiplier: float
    adjusted_premium: float
    explanation: str
    cached: bool = False

class CitySearchResponse(BaseModel):
    city: str
    country: str
    latitude: float
    longitude: float
    admin1: Optional[str] = None
    population: Optional[int] = None

class VisionAnalysisResponse(BaseModel):
    satellite_image_url: str
    detected_features: List[str]
    risk_assessment: str
    confidence: float

class RootResponse(BaseModel):
    message: str
    version: str
    endpoints: List[str]

class HealthResponse(BaseModel):
    status: str

class CityRiskResponse(BaseModel):
    id: int
    city: str
    lat: float
    lng: float
    type: str
    description: str
    risk: float
    flood_risk: float
    heat_risk: float
    storm_risk: float
    risk_level: str
    damage_estimate: float

class RealtimeLocation(BaseModel):
    city: str
    latitude: float
    longitude: float

class RealtimeCurrentRisks(BaseModel):
    flood_risk: float
    heat_risk: float
    storm_risk: float
    climate_risk_index: int
    risk_level: str
    damage_estimate: float

class TrendItem(BaseModel):
    trajectory: str
    value_2024: float
    value_2035: float
    value_2050: float
    years_to_critical: Optional[int] = None

class RiskTrends(BaseModel):
    flood: TrendItem
    heat: TrendItem
    storm: TrendItem

class AIInsights(BaseModel):
    risk_brief: str
    adaptation_actions: List[str]
    cached: bool = False

class RealtimeAnalysisResponse(BaseModel):
    location: RealtimeLocation
    current_risks: RealtimeCurrentRisks
    risk_trends: Optional[RiskTrends] = None
    ai_insights: Optional[AIInsights] = None

class DemoCacheResponse(BaseModel):
    status: str
    cached_items: Optional[int] = None
    cache_keys: Optional[List[str]] = None
    items: Optional[int] = None

class WarmupResults(BaseModel):
    successful: int
    failed: int
    errors: List[str]

class WarmupCacheResponse(BaseModel):
    warmup_complete: bool
    results: WarmupResults
    total_cached: int

