import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ============================================================================
# FEATHERLESS AI CONFIGURATION
# ============================================================================

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")

if not FEATHERLESS_API_KEY:
    # Allow running without API key for testing basic endpoints
    print("⚠️  WARNING: FEATHERLESS_API_KEY not set. AI features will be unavailable.")
    print("   Get one from https://featherless.ai and add to .env file")
    FEATHERLESS_API_KEY = "sk-test-key"  # Dummy key for basic testing

BASE_URL = "https://api.featherless.ai/v1"

# ============================================================================
# MODEL CONFIGURATIONS
# ============================================================================

# T4: Risk Narration - Uses large model for detailed analysis
NARRATION_MODEL = "Qwen/Qwen2.5-72B-Instruct"
NARRATION_MAX_TOKENS = 300
NARRATION_TEMPERATURE = 0.7

# T5: Insurance Explanation - Uses smaller model for concise output
INSURANCE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
INSURANCE_MAX_TOKENS = 100
INSURANCE_TEMPERATURE = 0.5

# T6: City Query Interpretation
QUERY_MODEL = "Qwen/Qwen2.5-7B-Instruct"
QUERY_MAX_TOKENS = 100
QUERY_TEMPERATURE = 0.3

# BONUS: Vision Model for satellite analysis
VISION_MODEL = "Gemma-3-27B-Vision"
VISION_MAX_TOKENS = 500

# ============================================================================
# INSURANCE CONFIGURATION
# ============================================================================

BASE_PREMIUM = 1200  # USD, T5 baseline

# Risk multiplier weights (impact on premium)
FLOOD_WEIGHT = 2.5   # Flood is most damaging
HEAT_WEIGHT = 1.5    # Health + infrastructure
STORM_WEIGHT = 2.0   # Property damage
MAX_MULTIPLIER = 5.0 # Cap premium increase

# ============================================================================
# CLIMATE DATA CONFIGURATION
# ============================================================================

# IPCC SSP2-4.5 scenario multipliers (T2)
# Baseline (2024) → +30% (2030) → +70% (2050)
IPCC_MULTIPLIER_2030 = 1.3
IPCC_MULTIPLIER_2050 = 1.7

# Damage estimation time factor (5% increase per year)
DAMAGE_TIME_MULTIPLIER = 0.05

# ============================================================================
# API CONFIGURATION
# ============================================================================

# Open-Meteo geocoding (free, no key required)
OPENMETEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
GEOCODING_RESULTS_LIMIT = 10

# ============================================================================
# DEMO CONFIGURATION
# ============================================================================

# Demo cities for pre-caching (T7)
DEMO_SCENARIOS = [
    ("Mumbai", 19.0760, 72.8777, [2024, 2035, 2050]),
    ("Lagos", 6.5244, 3.3792, [2024, 2035, 2050]),
    ("Miami", 25.7617, -80.1918, [2024, 2035, 2050]),
]

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
