#!/usr/bin/env python3
"""
TerraWatch API Usage Examples

Demonstrates all main features:
- T3: Risk data retrieval
- T4: AI narration
- T5: Insurance calculation
- T6: City search
- BONUS: Satellite analysis
"""

import asyncio
import httpx
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_health_check():
    """Test health endpoint"""
    print("=" * 70)
    print("🏥 HEALTH CHECK")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.json()}\n")


async def test_city_search():
    """T6: Test city search endpoint"""
    print("=" * 70)
    print("🔍 T6: CITY SEARCH & GEOCODING")
    print("=" * 70)
    
    cities = ["Mumbai", "Lagos", "Miami", "Tokyo"]
    
    async with httpx.AsyncClient() as client:
        for city in cities:
            response = await client.get(
                f"{BASE_URL}/api/search",
                params={"q": city}
            )
            results = response.json()
            
            if results:
                result = results[0]
                print(f"✓ {result['city']}, {result['country']}")
                print(f"  Coords: ({result['latitude']:.4f}, {result['longitude']:.4f})")
            else:
                print(f"✗ {city} not found")
    
    print()


async def test_risk_endpoint():
    """T3: Test risk endpoint"""
    print("=" * 70)
    print("📊 T3: CLIMATE RISK ASSESSMENT")
    print("=" * 70)
    
    test_cases = [
        {"city": "Mumbai", "lat": 19.0760, "lng": 72.8777, "years": [2024, 2035, 2050]},
        {"city": "Miami", "lat": 25.7617, "lng": -80.1918, "years": [2024, 2050]},
    ]
    
    async with httpx.AsyncClient() as client:
        for test in test_cases:
            print(f"\n🏙️  {test['city']}:")
            
            for year in test["years"]:
                response = await client.get(
                    f"{BASE_URL}/api/risk",
                    params={
                        "lat": test["lat"],
                        "lng": test["lng"],
                        "year": year
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"\n   📅 {year}:")
                    print(f"      Flood:  {data['flood_risk']:.1%}")
                    print(f"      Heat:   {data['heat_risk']:.1%}")
                    print(f"      Storm:  {data['storm_risk']:.1%}")
                    print(f"      CRI:    {data['climate_risk_index']} ({data['risk_level']})")
                    print(f"      💰 Damage Est: ${data['damage_estimate']:,.0f}")
                else:
                    print(f"   ❌ Error: {response.status_code}")
    
    print()


async def test_narration():
    """T4: Test narration endpoint"""
    print("=" * 70)
    print("📝 T4: AI RISK NARRATION (Qwen-72B)")
    print("=" * 70)
    
    test_cases = [
        {"city": "Mumbai", "lat": 19.0760, "lng": 72.8777, "year": 2050},
        {"city": "Miami", "lat": 25.7617, "lng": -80.1918, "year": 2050},
    ]
    
    async with httpx.AsyncClient() as client:
        for test in test_cases:
            print(f"\n🌏 {test['city']} ({test['year']}) - Using Cache (live=false):")
            
            response = await client.post(
                f"{BASE_URL}/api/narrate",
                params={
                    "city": test["city"],
                    "lat": test["lat"],
                    "lng": test["lng"],
                    "year": test["year"],
                    "live": False  # Use cache for demo
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n📋 Risk Brief:")
                print(f"   {data['risk_brief']}")
                print(f"\n🛠️  Adaptation Actions:")
                for i, action in enumerate(data['adaptation_actions'], 1):
                    print(f"   {i}. {action}")
                print(f"\n💾 Cached: {data['cached']}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
    
    print()


async def test_insurance():
    """T5: Test insurance endpoint"""
    print("=" * 70)
    print("💰 T5: INSURANCE PREMIUM CALCULATION (Qwen-7B)")
    print("=" * 70)
    
    test_cases = [
        {"city": "Mumbai", "lat": 19.0760, "lng": 72.8777, "year": 2050},
        {"city": "Miami", "lat": 25.7617, "lng": -80.1918, "year": 2050},
    ]
    
    async with httpx.AsyncClient() as client:
        for test in test_cases:
            print(f"\n🏙️  {test['city']} ({test['year']}):")
            
            response = await client.get(
                f"{BASE_URL}/api/insurance",
                params={
                    "city": test["city"],
                    "lat": test["lat"],
                    "lng": test["lng"],
                    "year": test["year"],
                    "live": False  # Use cache for demo
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n   Base Premium:      ${data['base_premium']:,}")
                print(f"   Flood Multiplier:  {data['flood_multiplier']:.2f}x")
                print(f"   Heat Multiplier:   {data['heat_multiplier']:.2f}x")
                print(f"   Storm Multiplier:  {data['storm_multiplier']:.2f}x")
                print(f"   ─────────────────────────")
                print(f"   Total Multiplier:  {data['total_multiplier']:.2f}x")
                print(f"   Adjusted Premium:  ${data['adjusted_premium']:,.0f}")
                print(f"\n   📊 Explanation:")
                print(f"   {data['explanation']}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
    
    print()


async def test_cache_management():
    """T7: Test cache management"""
    print("=" * 70)
    print("💾 T7: DEMO CACHE MANAGEMENT")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        # Check current cache
        response = await client.get(f"{BASE_URL}/api/demo-cache")
        data = response.json()
        
        print(f"\n📊 Current Cache Status:")
        print(f"   Cached Items: {data['cached_items']}")
        print(f"   Items: {', '.join(data['cache_keys'][:3])}{'...' if len(data['cache_keys']) > 3 else ''}")
        
        # Optionally warmup cache
        print(f"\n🔥 Warming up cache with 9 scenarios...")
        response = await client.post(f"{BASE_URL}/api/warmup-cache")
        warmup_data = response.json()
        
        print(f"   Successful: {warmup_data['results']['successful']}")
        print(f"   Failed: {warmup_data['results']['failed']}")
        print(f"   Total Cached: {warmup_data['total_cached']}")
    
    print()


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🌍 TERRAWATCH API - COMPREHENSIVE TEST SUITE")
    print("=" * 70 + "\n")
    
    try:
        await test_health_check()
        await test_city_search()
        await test_risk_endpoint()
        await test_narration()
        await test_insurance()
        await test_cache_management()
        
        print("=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70)
        print("\n📚 API Documentation: http://localhost:8000/docs")
        print("📖 OpenAPI Schema: http://localhost:8000/openapi.json\n")
        
    except Exception as e:
        print(f"\n❌ Error during tests: {e}")
        print("\n⚠️  Make sure the API is running: uvicorn backend.main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())
