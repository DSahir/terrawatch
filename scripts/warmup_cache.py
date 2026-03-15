#!/usr/bin/env python3
"""
T7: Demo Cache Warmup Script
Pre-computes and caches 9 demo scenarios (3 cities × 3 years)
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.risk_engine import get_risk_data
from backend.ai_client import FeatherlessAIClient
from backend.insurance_engine import InsuranceEngine


async def warmup_cache():
    """Pre-compute demo scenarios"""
    
    ai_client = FeatherlessAIClient()
    insurance_engine = InsuranceEngine()
    demo_cache = {}
    
    demo_scenarios = [
        # Mumbai - flood-heavy risk
        {"city": "Mumbai", "year": 2024, "lat": 19.0760, "lng": 72.8777},
        {"city": "Mumbai", "year": 2035, "lat": 19.0760, "lng": 72.8777},
        {"city": "Mumbai", "year": 2050, "lat": 19.0760, "lng": 72.8777},
        # Lagos - heat + flood risk
        {"city": "Lagos", "year": 2024, "lat": 6.5244, "lng": 3.3792},
        {"city": "Lagos", "year": 2035, "lat": 6.5244, "lng": 3.3792},
        {"city": "Lagos", "year": 2050, "lat": 6.5244, "lng": 3.3792},
        # Miami - coastal + heat
        {"city": "Miami", "year": 2024, "lat": 25.7617, "lng": -80.1918},
        {"city": "Miami", "year": 2035, "lat": 25.7617, "lng": -80.1918},
        {"city": "Miami", "year": 2050, "lat": 25.7617, "lng": -80.1918},
    ]
    
    print(f"🌍 TerraWatch Demo Cache Warmup - Processing {len(demo_scenarios)} scenarios\n")
    
    successful = 0
    failed = 0
    
    for i, scenario in enumerate(demo_scenarios, 1):
        city = scenario["city"]
        year = scenario["year"]
        lat = scenario["lat"]
        lng = scenario["lng"]
        
        print(f"[{i}/{len(demo_scenarios)}] Processing {city} {year}...", end=" ", flush=True)
        
        try:
            # Get risk data
            risk_data = get_risk_data(lat, lng, year)
            if risk_data is None:
                print("❌ No risk data")
                failed += 1
                continue
            
            # Generate narration
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
                
                cache_key = f"{city}_{year}_{lat:.2f}_{lng:.2f}"
                demo_cache[cache_key] = narration_data
                
                # Generate insurance estimate
                insurance_data = await insurance_engine.get_insurance_estimate(
                    city=city,
                    flood_risk=risk_data["flood_risk"],
                    heat_risk=risk_data["heat_risk"],
                    storm_risk=risk_data["storm_risk"],
                    use_live_ai=True
                )
                
                insurance_cache_key = f"insurance_{city}_{year}_{lat:.2f}_{lng:.2f}"
                demo_cache[insurance_cache_key] = insurance_data
                
                print("✅")
                successful += 1
                
            except Exception as e:
                print(f"⚠️ AI generation failed: {str(e)[:30]}")
                failed += 1
        
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            failed += 1
    
    # Save cache to file
    cache_file = Path("data/demo_cache.json")
    cache_file.parent.mkdir(exist_ok=True)
    
    with open(cache_file, "w") as f:
        json.dump(demo_cache, f, indent=2)
    
    print(f"\n📊 Results:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   💾 Cache items: {len(demo_cache)}")
    print(f"   📁 Saved to: {cache_file.absolute()}")
    
    return demo_cache


if __name__ == "__main__":
    asyncio.run(warmup_cache())
