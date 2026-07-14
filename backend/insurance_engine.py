from backend.ai_client import generate_insurance_explanation
from backend.config import BASE_PREMIUM
import logging

logger = logging.getLogger(__name__)

def calculate_multipliers(
    flood_risk: float, 
    heat_risk: float, 
    storm_risk: float
) -> dict:
    """
    Calculate premium multipliers based on climate risks
    """
    flood_capped = min(flood_risk, 1.0)
    heat_capped = min(heat_risk, 1.0)
    storm_capped = min(storm_risk, 1.0)
    
    flood_multiplier = 1.0 + (flood_capped * 2.5)
    heat_multiplier = 1.0 + (heat_capped * 1.5)
    storm_multiplier = 1.0 + (storm_capped * 2.0)
    
    total_multiplier = flood_multiplier * heat_multiplier * storm_multiplier
    total_multiplier = min(total_multiplier, 5.0)
    
    return {
        "flood_multiplier": round(flood_multiplier, 2),
        "heat_multiplier": round(heat_multiplier, 2),
        "storm_multiplier": round(storm_multiplier, 2),
        "total_multiplier": round(total_multiplier, 2),
    }

def calculate_premium(
    flood_risk: float,
    heat_risk: float,
    storm_risk: float
) -> dict:
    """Calculate base and adjusted premiums"""
    multipliers = calculate_multipliers(flood_risk, heat_risk, storm_risk)
    adjusted_premium = BASE_PREMIUM * multipliers["total_multiplier"]
    
    return {
        "base_premium": BASE_PREMIUM,
        "adjusted_premium": round(adjusted_premium, 2),
        **multipliers
    }

async def get_insurance_estimate(
    city: str,
    flood_risk: float,
    heat_risk: float,
    storm_risk: float,
    use_live_ai: bool = False
) -> dict:
    """
    Get insurance estimate with AI explanation
    """
    premium_data = calculate_premium(flood_risk, heat_risk, storm_risk)
    
    explanation = ""
    if use_live_ai:
        try:
            explanation = await generate_insurance_explanation(
                city=city,
                flood_risk=flood_risk,
                heat_risk=heat_risk,
                storm_risk=storm_risk,
                multiplier=premium_data["total_multiplier"]
            )
        except Exception as e:
            logger.error(f"Failed to generate AI explanation: {e}")
            explanation = _generate_fallback_explanation(
                flood_risk, heat_risk, storm_risk, 
                premium_data["total_multiplier"]
            )
    else:
        explanation = _generate_fallback_explanation(
            flood_risk, heat_risk, storm_risk,
            premium_data["total_multiplier"]
        )
    
    return {
        **premium_data,
        "explanation": explanation,
        "cached": not use_live_ai
    }

def _generate_fallback_explanation(
    flood_risk: float,
    heat_risk: float,
    storm_risk: float,
    multiplier: float
) -> str:
    """Generate fallback explanation when AI is unavailable"""
    primary_risk = max(
        ("flood", flood_risk),
        ("heat", heat_risk),
        ("storm", storm_risk),
        key=lambda x: x[1]
    )
    
    risk_name = primary_risk[0].capitalize()
    increase_pct = (multiplier - 1) * 100
    
    return f"{risk_name} risk ({primary_risk[1]:.0%}) is the primary driver of the {increase_pct:.0f}% premium increase."
