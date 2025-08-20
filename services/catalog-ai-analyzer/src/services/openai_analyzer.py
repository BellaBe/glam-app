# services/catalog-ai-analyzer/src/services/openai_analyzer.py
import base64
import json
import asyncio
from typing import Optional, Dict, Any
import httpx
from shared.utils.logger import ServiceLogger
from ..config import ServiceConfig
from ..schemas.analysis import AttributeResult, ColorResult, PatternResult
from ..exceptions import OpenAIAPIError, OpenAIRateLimitError

class OpenAIAnalyzer:
    """OpenAI Vision API integration for semantic attribute analysis"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        self.client = httpx.AsyncClient(timeout=config.openai_timeout_seconds)
    
    async def analyze_attributes(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Analyze product attributes using OpenAI Vision API"""
        try:
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            prompt = self._build_analysis_prompt()
            
            for attempt in range(self.config.openai_max_retries):
                try:
                    response = await self._call_openai_api(base64_image, prompt)
                    if response:
                        return self._parse_openai_response(response)
                        
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        # Rate limited
                        wait_time = 2 ** attempt
                        if attempt == self.config.openai_max_retries - 1:
                            raise OpenAIRateLimitError(
                                retry_after=wait_time
                            )
                        self.logger.warning(f"OpenAI rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    elif e.response.status_code >= 500:
                        # Server error
                        if attempt == self.config.openai_max_retries - 1:
                            raise OpenAIAPIError(
                                f"OpenAI server error: {e.response.status_code}",
                                status_code=e.response.status_code,
                                error_type="server_error"
                            )
                        await asyncio.sleep(2 ** attempt)
                    else:
                        # Client error - don't retry
                        raise OpenAIAPIError(
                            f"OpenAI client error: {e.response.status_code}",
                            status_code=e.response.status_code,
                            error_type="client_error"
                        )
                except httpx.TimeoutException:
                    if attempt == self.config.openai_max_retries - 1:
                        raise OpenAIAPIError(
                            "OpenAI API timeout",
                            error_type="timeout"
                        )
                    await asyncio.sleep(2 ** attempt)
            
            return None
            
        except (OpenAIAPIError, OpenAIRateLimitError):
            raise  # Re-raise our domain exceptions
        except Exception as e:
            raise OpenAIAPIError(
                f"Unexpected OpenAI error: {str(e)}",
                error_type="unexpected"
            )
    
    async def _call_openai_api(self, base64_image: str, prompt: str) -> Dict:
        """Call OpenAI Vision API"""
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.openai_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }
        
        response = await self.client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        
        return response.json()
    
    def _build_analysis_prompt(self) -> str:
        """Build structured prompt for OpenAI Vision"""
        return """Analyze this product image and return a JSON object with the following structure:
        {
            "category": "main product category (e.g., shirts, dresses, shoes)",
            "subcategory": "specific subcategory (e.g., casual-shirts, evening-dresses)",
            "description": "brief product description (max 100 chars)",
            "gender": "male|female|unisex",
            "attributes": {
                "colors": [
                    {"name": "color name", "confidence": 0.0-1.0}
                ],
                "patterns": [
                    {"name": "pattern name", "confidence": 0.0-1.0}
                ],
                "styles": [
                    {"name": "style name", "confidence": 0.0-1.0}
                ],
                "materials": [
                    {"name": "material name", "confidence": 0.0-1.0}
                ],
                "season": ["spring", "summer", "fall", "winter"],
                "occasion": ["casual", "formal", "business", "sport", "evening"]
            }
        }
        
        Focus on fashion/apparel attributes. Be precise and confident.
        Return ONLY valid JSON, no additional text."""
    
    def _parse_openai_response(self, response: Dict) -> Optional[Dict[str, Any]]:
        """Parse OpenAI response and extract structured data"""
        try:
            content = response['choices'][0]['message']['content']
            
            # Clean up response (remove markdown if present)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            # Parse JSON
            data = json.loads(content.strip())
            
            # Convert to our schema
            return {
                "category": data.get("category"),
                "subcategory": data.get("subcategory"),
                "description": data.get("description"),
                "gender": data.get("gender"),
                "attributes": AttributeResult(
                    colors=[ColorResult(**c) for c in data.get("attributes", {}).get("colors", [])],
                    patterns=[PatternResult(**p) for p in data.get("attributes", {}).get("patterns", [])],
                    styles=[{"name": s["name"], "confidence": s["confidence"]} 
                            for s in data.get("attributes", {}).get("styles", [])],
                    materials=[{"name": m["name"], "confidence": m["confidence"]} 
                              for m in data.get("attributes", {}).get("materials", [])],
                    season=data.get("attributes", {}).get("season", []),
                    occasion=data.get("attributes", {}).get("occasion", [])
                )
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse OpenAI response: {e}")
            return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()