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

class NarrateRequest(BaseModel):
    city: str
    latitude: float
    longitude: float
    year: int
    flood_risk: float
    heat_risk: float
    storm_risk: float
    damage_estimate: float

class NarrateResponse(BaseModel):
    risk_brief: str
    adaptation_actions: List[str]
    cached: bool = False

class InsuranceRequest(BaseModel):
    city: str
    flood_risk: float
    heat_risk: float
    storm_risk: float

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
