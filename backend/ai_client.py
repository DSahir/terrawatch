import httpx
import json
from typing import Optional
from backend.config import FEATHERLESS_API_KEY, BASE_URL
import logging

logger = logging.getLogger(__name__)

class FeatherlessAIClient:
    """Client for Featherless AI API with support for multiple models"""
    
    def __init__(self, api_key: str = FEATHERLESS_API_KEY):
        self.api_key = api_key
        self.base_url = BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_narration(
        self, 
        city: str, 
        latitude: float, 
        longitude: float, 
        year: int,
        flood_risk: float, 
        heat_risk: float,
        storm_risk: float,
        damage_estimate: float
    ) -> str:
        """
        T4: Use Qwen-72B to generate plain-English risk brief + adaptation actions
        """
        prompt = f"""You are a climate risk analyst briefing city planners. 
        
City: {city} (coordinates: {latitude}, {longitude})
Year: {year}
Risk Assessment:
- Flood Risk: {flood_risk:.1%}
- Heat Risk: {heat_risk:.1%}
- Storm Risk: {storm_risk:.1%}
- Estimated Damage: ${damage_estimate:,.0f}

Generate:
1. A 3-sentence plain-English risk brief explaining the climate threats to this location
2. Two specific, actionable adaptation measures city planners should implement before {year}

Format your response as JSON with keys: "risk_brief" (string), "adaptation_actions" (list of 2 strings)"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "Qwen/Qwen2.5-72B-Instruct",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 300,
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Extract JSON from response
                try:
                    # Try to parse JSON directly
                    narration_data = json.loads(content)
                except json.JSONDecodeError:
                    # If response contains markdown code blocks, extract JSON
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                        narration_data = json.loads(json_str)
                    else:
                        # Fallback parsing
                        narration_data = {
                            "risk_brief": content,
                            "adaptation_actions": ["Strengthen drainage systems", "Increase green space coverage"]
                        }
                
                return narration_data
                
        except Exception as e:
            logger.error(f"Error generating narration: {e}")
            raise
    
    async def generate_insurance_explanation(
        self, 
        city: str,
        flood_risk: float,
        heat_risk: float,
        storm_risk: float,
        multiplier: float
    ) -> str:
        """
        T5: Use Qwen-7B to generate one-line premium increase explanation
        """
        prompt = f"""You are an insurance expert explaining premium adjustments.

Location: {city}
Climate Risks:
- Flood: {flood_risk:.1%}
- Heat: {heat_risk:.1%}
- Storm: {storm_risk:.1%}
Premium Multiplier: {multiplier:.2f}x

Write ONE concise sentence explaining why the premium is increasing by {(multiplier-1)*100:.0f}%. Focus on the primary risk driver."""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "Qwen/Qwen2.5-7B-Instruct",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.5,
                        "max_tokens": 100,
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                explanation = result["choices"][0]["message"]["content"].strip()
                return explanation
                
        except Exception as e:
            logger.error(f"Error generating insurance explanation: {e}")
            raise
    
    async def analyze_satellite_imagery(
        self, 
        image_url: str,
        city: str,
        year: int
    ) -> dict:
        """
        BONUS: Use Gemma-3-27B vision model to analyze satellite imagery for climate risks
        """
        prompt = f"""Analyze this satellite image of {city} for climate change impacts and urban vulnerability indicators relevant to projections for {year}.

Identify:
1. Urban features (buildings, impervious surfaces, vegetation)
2. Water features (rivers, coasts, flooding potential)
3. Heat vulnerability (density, green space)
4. Adaptation infrastructure (if visible)

Respond in JSON with: detected_features (list), risk_assessment (string), confidence (0-1)"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "Gemma-3-27B-Vision",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": image_url}}
                                ]
                            }
                        ],
                        "max_tokens": 500,
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                try:
                    vision_data = json.loads(content)
                except json.JSONDecodeError:
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                        vision_data = json.loads(json_str)
                    else:
                        vision_data = {
                            "detected_features": ["Urban development", "Water bodies"],
                            "risk_assessment": "Moderate climate vulnerability",
                            "confidence": 0.75
                        }
                
                return vision_data
                
        except Exception as e:
            logger.error(f"Error analyzing satellite imagery: {e}")
            raise
    
    async def interpret_city_query(self, query: str) -> dict:
        """
        T6: Use lightweight model to parse natural language city searches
        Returns suggested cities with coordinates
        """
        prompt = f"""Parse this city search query into structured format:
Query: "{query}"

If it's a city name, respond with JSON containing:
- city (string, standard city name)
- country (string)
- confidence (0-1, how confident you are in the interpretation)

If unclear, suggest the most likely city."""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": "Qwen/Qwen2.5-7B-Instruct",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 100,
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError:
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                        parsed = json.loads(json_str)
                    else:
                        parsed = {"city": query, "country": "Unknown", "confidence": 0.5}
                
                return parsed
                
        except Exception as e:
            logger.error(f"Error interpreting city query: {e}")
            raise
