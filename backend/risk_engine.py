import pandas as pd
from math import radians, sin, cos, sqrt, atan2
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Load mock data
try:
    data = pd.read_csv("data/mock_risk_data.csv")
except FileNotFoundError:
    logger.warning("Mock risk data not found. Using sample city data.")
    # Sample cities with risk data
    sample_data = [
        {"city": "New York City", "lat": 40.7128, "lng": -74.0060, "flood_2024": 0.8, "heat_2024": 0.3, "storm_2024": 0.2},
        {"city": "Los Angeles", "lat": 34.0522, "lng": -118.2437, "flood_2024": 0.2, "heat_2024": 0.9, "storm_2024": 0.1},
        {"city": "London", "lat": 51.5074, "lng": -0.1278, "flood_2024": 0.5, "heat_2024": 0.4, "storm_2024": 0.3},
        {"city": "Sydney", "lat": -33.8688, "lng": 151.2093, "flood_2024": 0.3, "heat_2024": 0.7, "storm_2024": 0.4},
        {"city": "Mumbai", "lat": 19.0760, "lng": 72.8777, "flood_2024": 0.9, "heat_2024": 0.8, "storm_2024": 0.5},
        {"city": "Lagos", "lat": 6.5244, "lng": 3.3792, "flood_2024": 0.6, "heat_2024": 0.9, "storm_2024": 0.3},
        {"city": "Miami", "lat": 25.7617, "lng": -80.1918, "flood_2024": 0.7, "heat_2024": 0.6, "storm_2024": 0.8},
        {"city": "Jakarta", "lat": -6.2088, "lng": 106.8456, "flood_2024": 0.8, "heat_2024": 0.7, "storm_2024": 0.4},
        {"city": "Tokyo", "lat": 35.6762, "lng": 139.6503, "flood_2024": 0.4, "heat_2024": 0.5, "storm_2024": 0.6},
        {"city": "São Paulo", "lat": -23.5505, "lng": -46.6333, "flood_2024": 0.5, "heat_2024": 0.6, "storm_2024": 0.2}
    ]
    data = pd.DataFrame(sample_data)


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def nearest_point(lat: float, lng: float):
    """Find nearest point in data to given coordinates"""
    if data.empty:
        return None
    
    distances = data.apply(
        lambda row: haversine(lat, lng, row.lat, row.lng),
        axis=1
    )

    idx = distances.idxmin()
    return data.iloc[idx]


def apply_ipcc_multiplier(base_risk: float, year: int) -> float:
    """
    Apply IPCC SSP2-4.5 scenario multipliers
    - 2024: baseline (1.0x)
    - 2030: +30% (1.3x)
    - 2050: +70% (1.7x)
    Linear interpolation for intermediate years
    """
    if year <= 2024:
        return base_risk * 1.0
    elif year >= 2050:
        return base_risk * 1.7
    else:
        # Linear interpolation
        years_from_2024 = year - 2024
        progress = years_from_2024 / (2050 - 2024)
        multiplier = 1.0 + (0.7 * progress)
        return base_risk * multiplier


def interpolate_risk(point: dict, year: int) -> dict:
    """
    T2: Interpolate risk data for target year using IPCC scenarios
    Returns flood, heat, and storm risks for the given year
    """
    if point is None:
        return None
    
    # Get base risks (2024)
    base_flood = float(point.get("flood_2024", 0))
    base_heat = float(point.get("heat_2024", 0))
    base_storm = float(point.get("storm_2024", 0.1))  # Default storm risk
    
    # Apply IPCC multipliers
    flood_risk = apply_ipcc_multiplier(base_flood, year)
    heat_risk = apply_ipcc_multiplier(base_heat, year)
    storm_risk = apply_ipcc_multiplier(base_storm, year)
    
    # Cap at 1.0 (100%)
    flood_risk = min(flood_risk, 1.0)
    heat_risk = min(heat_risk, 1.0)
    storm_risk = min(storm_risk, 1.0)
    
    return {
        "flood_risk": round(flood_risk, 3),
        "heat_risk": round(heat_risk, 3),
        "storm_risk": round(storm_risk, 3),
    }


def climate_risk_index(flood: float, heat: float, storm: float = 0.1) -> int:
    """
    Calculate composite Climate Risk Index (CRI)
    Weighted average: 50% flood, 35% heat, 15% storm
    Returns 0-100 scale
    """
    score = (0.50 * flood + 0.35 * heat + 0.15 * storm) * 100
    return round(score)


def risk_label(score: int) -> str:
    """Map CRI score to risk level"""
    if score < 25:
        return "Low"
    elif score < 50:
        return "Moderate"
    elif score < 75:
        return "High"
    else:
        return "Severe"


def estimate_damage(city: str, flood_risk: float, heat_risk: float, storm_risk: float, year: int) -> float:
    """
    T3: Estimate economic damage in USD
    Simplified model based on risk levels and future year
    
    Base estimates (2024):
    - Low risk (0-25%): $50-100k
    - Moderate (25-50%): $100-300k
    - High (50-75%): $300-800k
    - Severe (75%+): $800k+
    """
    
    # Calculate composite risk
    composite = (flood_risk * 0.5 + heat_risk * 0.35 + storm_risk * 0.15)
    
    # Base damage estimate
    if composite < 0.25:
        base_damage = 75_000
    elif composite < 0.50:
        base_damage = 200_000
    elif composite < 0.75:
        base_damage = 550_000
    else:
        base_damage = 1_200_000
    
    # Scale by time - assumes compounding climate impacts
    years_ahead = max(0, year - 2024)
    time_multiplier = 1.0 + (0.05 * years_ahead)  # 5% increase per year
    
    total_damage = base_damage * time_multiplier
    
    return round(total_damage, 0)


def get_risk_data(lat: float, lng: float, year: int) -> Optional[dict]:
    """
    T3: Main function to get complete risk data for a location and year
    Returns complete risk assessment with damage estimate
    """
    
    point = nearest_point(lat, lng)
    if point is None:
        return None
    
    # Interpolate risks for target year
    risks = interpolate_risk(point, year)
    if risks is None:
        return None
    
    flood_risk = risks["flood_risk"]
    heat_risk = risks["heat_risk"]
    storm_risk = risks["storm_risk"]
    
    # Calculate composite index
    cri = climate_risk_index(flood_risk, heat_risk, storm_risk)
    
    # Estimate damage
    damage = estimate_damage(
        str(point.get("city", "Unknown")),
        flood_risk,
        heat_risk,
        storm_risk,
        year
    )
    
    return {
        "city": str(point.get("city", "Unknown")),
        "latitude": float(point.get("lat", lat)),
        "longitude": float(point.get("lng", lng)),
        "year": year,
        "flood_risk": flood_risk,
        "heat_risk": heat_risk,
        "storm_risk": storm_risk,
        "climate_risk_index": cri,
        "risk_level": risk_label(cri),
        "damage_estimate": damage,
    }


def get_all_cities_risk(year: int) -> list:
    """
    Get risk data for all cities for a given year
    Returns list of city risk data compatible with frontend expectations
    """
    if data.empty:
        return []
    
    cities = []
    for idx, row in data.iterrows():
        # Get risk data for this city
        risk_data = get_risk_data(row['lat'], row['lng'], year)
        if risk_data:
            # Convert to frontend-compatible format
            cities.append({
                "id": idx + 1,
                "city": risk_data["city"],
                "lat": risk_data["latitude"],
                "lng": risk_data["longitude"],
                "type": "Climate Risk",  # Generic type since we have multiple risks
                "description": f"Climate risk assessment for {risk_data['city']} in {year}",
                "risk": risk_data["climate_risk_index"] / 100.0,  # Convert to 0-1 scale
                "flood_risk": risk_data["flood_risk"],
                "heat_risk": risk_data["heat_risk"],
                "storm_risk": risk_data["storm_risk"],
                "risk_level": risk_data["risk_level"],
                "damage_estimate": risk_data["damage_estimate"]
            })
    
    return cities