"""
AI-Generated Image Detection Service
Detects AI-generated or synthetic images using Sightengine API, Groq API, and local analysis
"""

import io
import logging
from typing import Dict, Any, Optional
import numpy as np
from PIL import Image
import requests
from groq import Groq

from app.config import GROQ_API_KEY, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, SIGHTENGINE_ENABLED

logger = logging.getLogger(__name__)


class AIDetectionService:
    """Service for detecting AI-generated images"""

    def __init__(self):
        """Initialize the AI detection service"""
        self.groq_client = None
        self.sightengine_enabled = SIGHTENGINE_ENABLED
        
        if GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=GROQ_API_KEY)
                logger.info("Groq API client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")
        
        if self.sightengine_enabled:
            logger.info("Sightengine API enabled for AI detection")
        else:
            logger.info("Sightengine API not configured, using local analysis")

    def detect_ai_generated(self, image_content: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect if an image is AI-generated
        
        Args:
            image_content: Raw image bytes
            filename: Optional filename for context
        
        Returns:
            Dictionary containing AI detection results
        """
        results = {
            "ai_generated_probability": 0.0,
            "confidence": 0.0,
            "indicators": [],
            "analysis_method": "local_only",
            "detailed_analysis": {}
        }
        
        # Try Sightengine API first (most accurate for AI detection)
        logger.info(f"Sightengine enabled: {self.sightengine_enabled}, API_USER: {SIGHTENGINE_API_USER[:5] if SIGHTENGINE_API_USER else 'None'}..., API_SECRET: {'*' * 10 if SIGHTENGINE_API_SECRET else 'None'}")
        
        if self.sightengine_enabled:
            logger.info(f"Attempting Sightengine analysis for image: {filename or 'unknown'}")
            sightengine_results = self._analyze_with_sightengine(image_content, filename)
            logger.info(f"Sightengine results: {sightengine_results}")
            if sightengine_results and not sightengine_results.get("error"):
                results.update(sightengine_results)
                results["analysis_method"] = "sightengine_api"
                logger.info(f"Successfully used Sightengine API, probability: {results.get('ai_generated_probability', 0.0)}")
            else:
                logger.warning(f"Sightengine analysis failed or returned error: {sightengine_results.get('error') if sightengine_results else 'No results'}")
        else:
            logger.warning("Sightengine is not enabled - check API credentials in .env file")
        
        # Try Groq API as secondary option if Sightengine not available/configured
        if results["analysis_method"] == "local_only" and self.groq_client:
            groq_results = self._analyze_with_groq(image_content, filename)
            if groq_results and not groq_results.get("error"):
                results.update(groq_results)
                results["analysis_method"] = "groq_api"
        
        # Always perform local analysis as backup/complement
        local_results = self._local_ai_detection(image_content)
        
        # Combine results
        if results["analysis_method"] == "local_only":
            results.update(local_results)
        else:
            # Merge local results with API results
            local_probability = local_results.get("ai_generated_probability", 0.0)
            api_probability = results.get("ai_generated_probability", 0.0)
            
            logger.info(f"Combining results - API method: {results['analysis_method']}, API probability: {api_probability:.4f}, Local probability: {local_probability:.4f}")
            
            # For Sightengine, use 100% API result (most reliable)
            # For Groq, use weighted average
            if results["analysis_method"] == "sightengine_api":
                # Use Sightengine result directly (don't dilute with local analysis)
                logger.info(f"Using Sightengine result directly: {api_probability:.4f}")
                results["ai_generated_probability"] = float(api_probability)
            else:
                # Weighted average for Groq: 70% Groq, 30% local
                weight_api = 0.7
                weight_local = 0.3
                combined_probability = (api_probability * weight_api) + (local_probability * weight_local)
                results["ai_generated_probability"] = float(combined_probability)
                logger.info(f"Combined probability (Groq): {combined_probability:.4f}")
            
            # Combine indicators
            if local_results.get("indicators"):
                results["indicators"].extend(local_results["indicators"])
            
            results["detailed_analysis"]["local"] = local_results
        
        # Update confidence based on agreement
        results["confidence"] = self._calculate_confidence(results)
        
        return results

    def _analyze_with_sightengine(self, image_content: bytes, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze image using Sightengine API for AI detection
        
        Args:
            image_content: Raw image bytes
            filename: Optional filename for context
            
        Returns:
            Dictionary with Sightengine analysis results
        """
        results = {
            "ai_generated_probability": 0.0,
            "confidence": 0.0,
            "indicators": [],
            "sightengine_analysis": {}
        }
        
        try:
            # Validate credentials
            if not SIGHTENGINE_API_USER or not SIGHTENGINE_API_SECRET:
                logger.error("Sightengine credentials not found in config")
                results["error"] = "Sightengine API credentials not configured"
                return results
            
            # Validate image content
            if not image_content or len(image_content) == 0:
                logger.error("Empty or invalid image content provided to Sightengine")
                results["error"] = "Empty or invalid image content"
                return results
            
            logger.info(f"Preparing Sightengine API request: image_size={len(image_content)} bytes, filename={filename}")
            
            # Prepare API request
            params = {
                'models': 'genai',  # AI generation detection model
                'api_user': SIGHTENGINE_API_USER,
                'api_secret': SIGHTENGINE_API_SECRET
            }
            
            logger.debug(f"Sightengine API params: api_user={SIGHTENGINE_API_USER}, api_secret={'*' * 10}")
            
            # Prepare image file for upload
            # Use BytesIO to create a file-like object from bytes
            image_file = io.BytesIO(image_content)
            image_file.seek(0)  # Ensure we're at the beginning of the stream
            files = {
                'media': (filename or 'image.jpg', image_file, 'image/jpeg')
            }
            
            logger.info(f"Making Sightengine API request to https://api.sightengine.com/1.0/check.json")
            
            # Make API request
            response = requests.post(
                'https://api.sightengine.com/1.0/check.json',
                files=files,
                data=params,
                timeout=30  # 30 second timeout
            )
            
            logger.info(f"Sightengine API response status: {response.status_code}")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Log response details
            logger.info(f"Sightengine API response headers: {dict(response.headers)}")
            
            # Parse JSON response
            try:
                output = response.json()
                logger.info(f"Sightengine API full response: {output}")
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}, Response text: {response.text[:500]}")
                results["error"] = f"Invalid JSON response: {str(e)}"
                return results
            
            # Store full response for debugging
            results["sightengine_analysis"]["raw_response"] = output
            
            # Extract AI generation probability
            # Sightengine returns results in 'type' field with 'ai_generated' (probability)
            # Response format: {'status': 'success', 'type': {'ai_generated': 0.99}, ...}
            type_result = output.get('type', {})
            
            logger.info(f"Sightengine type_result: {type_result}")
            
            # Try to get probability from different possible locations
            probability = None
            
            # Primary location: type.ai_generated (actual response format)
            if type_result and 'ai_generated' in type_result:
                probability = type_result.get('ai_generated')
                logger.info(f"Found probability in type.ai_generated: {probability}")
            # Fallback: genai.prob (documented format, but might not be used)
            elif 'genai' in output:
                genai_result = output.get('genai', {})
                probability = genai_result.get('prob', genai_result.get('probability', None))
                logger.info(f"Found probability in genai field: {probability}")
            
            if probability is not None:
                # Ensure probability is in valid range
                if isinstance(probability, (int, float)):
                    probability = float(probability)
                    
                    # Check if probability might be in percentage format (0-100 instead of 0-1)
                    if probability > 1.0:
                        logger.info(f"Probability appears to be in percentage format ({probability}), converting to 0-1 scale")
                        probability = probability / 100.0
                    
                    # Clamp to valid range [0, 1]
                    probability = max(0.0, min(1.0, probability))
                    logger.info(f"Final Sightengine probability (AI-generated): {probability:.4f}")
                    
                    results["ai_generated_probability"] = probability
                    results["confidence"] = 0.9  # Sightengine API is highly reliable
                    
                    # Add indicators based on probability
                    if probability >= 0.8:
                        results["indicators"].append("Very high probability of AI generation detected by Sightengine")
                    elif probability >= 0.6:
                        results["indicators"].append("High probability of AI generation detected by Sightengine")
                    elif probability >= 0.4:
                        results["indicators"].append("Moderate probability of AI generation detected by Sightengine")
                    elif probability >= 0.2:
                        results["indicators"].append("Low probability of AI generation detected by Sightengine")
                    else:
                        results["indicators"].append("Image appears to be authentic (low AI generation probability)")
                    
                    # Store detailed analysis
                    results["sightengine_analysis"]["type_details"] = type_result
                    results["sightengine_analysis"]["model"] = "genai"
                    
                    logger.info(f"Sightengine analysis complete: AI probability={probability:.2f}")
                else:
                    logger.warning(f"Probability is not a number: {probability}, type: {type(probability)}")
                    results["error"] = f"Invalid probability value: {probability}"
            else:
                logger.warning(f"Sightengine response missing probability field. Full response: {output}")
                logger.warning(f"Available keys: {list(output.keys())}")
                logger.warning(f"type_result keys: {list(type_result.keys()) if type_result else 'N/A'}")
                # Check if there's an error in the response
                if 'error' in output:
                    results["error"] = f"Sightengine API error: {output.get('error', 'Unknown error')}"
                elif 'message' in output:
                    results["error"] = f"Sightengine API message: {output.get('message', 'Unknown message')}"
                else:
                    results["error"] = "Invalid response from Sightengine API: missing 'type.ai_generated' or 'genai' field"
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Sightengine API HTTP error: {e}")
            logger.error(f"Response status: {e.response.status_code if hasattr(e, 'response') else 'N/A'}")
            logger.error(f"Response text: {e.response.text[:500] if hasattr(e, 'response') and e.response else 'N/A'}")
            results["error"] = f"HTTP error: {str(e)}"
        except requests.exceptions.RequestException as e:
            logger.error(f"Sightengine API request failed: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            results["error"] = f"API request failed: {str(e)}"
        except ValueError as e:
            logger.error(f"Failed to parse Sightengine JSON response: {e}")
            results["error"] = f"Invalid JSON response: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in Sightengine analysis: {e}", exc_info=True)
            results["error"] = f"Unexpected error: {str(e)}"
        
        return results

    def _analyze_with_groq(self, image_content: bytes, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze image using Groq API with vision capabilities
        
        Args:
            image_content: Raw image bytes
            filename: Optional filename
        
        Returns:
            Dictionary with Groq analysis results
        """
        results = {
            "ai_generated_probability": 0.0,
            "indicators": [],
            "groq_analysis": {}
        }
        
        try:
            # Prepare prompt for AI detection
            prompt = """Analyze this image and determine if it is likely AI-generated or synthetic. 
            Consider the following factors:
            1. Unnatural textures or patterns (especially in hair, skin, backgrounds)
            2. Inconsistent lighting or shadows
            3. Unusual artifacts or distortions
            4. Too perfect or too uniform elements
            5. Watermarks or signatures that might indicate AI generation
            6. Unnatural perspective or proportions
            7. Color inconsistencies
            8. Lack of fine details or over-smoothing
            
            Provide your assessment as a probability (0.0 to 1.0) where:
            - 0.0-0.3: Likely authentic/natural image
            - 0.3-0.6: Possibly AI-generated, some indicators present
            - 0.6-0.8: Probably AI-generated, multiple indicators
            - 0.8-1.0: Almost certainly AI-generated, strong indicators
            
            Format your response as JSON with this structure:
            {
                "probability": <number between 0.0 and 1.0>,
                "confidence": <number between 0.0 and 1.0>,
                "indicators": ["list", "of", "specific", "indicators"],
                "reasoning": "brief explanation"
            }"""
            
            # Groq may not support direct vision API, so we'll analyze image characteristics
            # and use LLM to reason about them
            
            # First, extract image characteristics for analysis
            image_characteristics = self._extract_image_characteristics(image_content)
            
            # Create enhanced prompt with image characteristics
            enhanced_prompt = f"""Based on the following image characteristics, determine if this image is likely AI-generated:

Image Characteristics:
- Dimensions: {image_characteristics.get('dimensions', 'Unknown')}
- Format: {image_characteristics.get('format', 'Unknown')}
- Texture variance: {image_characteristics.get('texture_variance', 'Unknown')}
- Color characteristics: {image_characteristics.get('color_info', 'Unknown')}
- Common AI size: {image_characteristics.get('is_common_ai_size', False)}
- Texture uniformity: {image_characteristics.get('uniformity_score', 'Unknown')}

{prompt}"""
            
            messages = [
                {
                    "role": "user",
                    "content": enhanced_prompt
                }
            ]
            
            # Use Groq's text model to analyze
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-70b-versatile",  # or "llama-3.1-8b-instant" for faster
                    messages=messages,
                    temperature=0.3,
                    max_tokens=500
                )
                
                response_text = response.choices[0].message.content
                results["groq_analysis"]["raw_response"] = response_text
                
                # Parse JSON response if possible
                import json
                try:
                    # Extract JSON from response
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        parsed = json.loads(response_text[json_start:json_end])
                        
                        results["ai_generated_probability"] = float(parsed.get("probability", 0.0))
                        results["confidence"] = float(parsed.get("confidence", 0.5))
                        results["indicators"] = parsed.get("indicators", [])
                        results["groq_analysis"]["reasoning"] = parsed.get("reasoning", "")
                    else:
                        # Fallback: extract probability from text
                        results = self._parse_groq_text_response(response_text)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse Groq JSON response: {e}")
                    results = self._parse_groq_text_response(response_text)
                
            except Exception as e:
                # If API call fails, use local analysis
                logger.warning(f"Groq API call failed: {e}, using local analysis")
                results = self._groq_text_based_analysis(image_content)
                
        except Exception as e:
            logger.error(f"Error in Groq API analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _parse_groq_text_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Groq text response to extract probability and indicators"""
        import re
        
        results = {
            "ai_generated_probability": 0.0,
            "confidence": 0.5,
            "indicators": [],
            "groq_analysis": {"raw_response": response_text}
        }
        
        # Try to extract probability number
        probability_patterns = [
            r'"probability":\s*([0-9.]+)',
            r'probability[:\s]+([0-9.]+)',
            r'([0-9.]+)\s*(?:out of 1|probability|likely)',
        ]
        
        for pattern in probability_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                try:
                    results["ai_generated_probability"] = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Extract indicators (look for list items or bullet points)
        indicator_patterns = [
            r'[-•*]\s*([^\n]+)',
            r'\d+\.\s*([^\n]+)',
        ]
        
        indicators = []
        for pattern in indicator_patterns:
            matches = re.findall(pattern, response_text)
            if matches:
                indicators.extend([m.strip() for m in matches[:5]])  # Limit to 5
        
        if indicators:
            results["indicators"] = indicators
        
        return results

    def _extract_image_characteristics(self, image_content: bytes) -> Dict[str, Any]:
        """Extract characteristics from image for analysis"""
        characteristics = {}
        try:
            image = Image.open(io.BytesIO(image_content))
            image_array = np.array(image.convert('RGB'))
            
            width, height = image.size
            characteristics["dimensions"] = f"{width}x{height}"
            characteristics["format"] = image.format or "Unknown"
            
            # Common AI sizes
            common_ai_sizes = [(1024, 1024), (512, 512), (768, 768), (1536, 1536), (2048, 2048)]
            characteristics["is_common_ai_size"] = (width, height) in common_ai_sizes
            
            # Texture variance
            if len(image_array.shape) == 3:
                h, w = image_array.shape[:2]
                regions = [
                    image_array[:h//3, :w//3],
                    image_array[:h//3, 2*w//3:],
                    image_array[2*h//3:, :w//3],
                    image_array[2*h//3:, 2*w//3:]
                ]
                region_variances = [np.var(r) for r in regions]
                variance_mean = np.mean(region_variances)
                variance_std = np.std(region_variances)
                
                characteristics["texture_variance"] = f"mean={variance_mean:.2f}, std={variance_std:.2f}"
                characteristics["uniformity_score"] = "high" if variance_std / variance_mean < 0.2 else "low"
                
                # Color info
                saturation_variance = np.var(image_array, axis=2)
                characteristics["color_info"] = f"high_saturation" if np.mean(saturation_variance) > 10000 else "normal"
            
        except Exception as e:
            logger.warning(f"Error extracting image characteristics: {e}")
        
        return characteristics

    def _groq_text_based_analysis(self, image_content: bytes) -> Dict[str, Any]:
        """
        Alternative text-based analysis when vision API is not available
        Uses image metadata and descriptions
        """
        results = {
            "ai_generated_probability": 0.0,
            "indicators": [],
            "groq_analysis": {"method": "text_based"}
        }
        
        try:
            # Analyze image properties that might indicate AI generation
            image = Image.open(io.BytesIO(image_content))
            width, height = image.size
            
            # Very large or very square images might be AI-generated
            aspect_ratio = width / height if height > 0 else 1.0
            if abs(aspect_ratio - 1.0) < 0.1:  # Very square
                results["indicators"].append("Perfect square aspect ratio")
            
            if width > 2048 or height > 2048:  # Very large
                results["indicators"].append("Unusually large dimensions")
            
            # Check for common AI generation artifacts using local analysis
            local_results = self._local_ai_detection(image_content)
            results.update(local_results)
            
        except Exception as e:
            logger.warning(f"Error in text-based Groq analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _local_ai_detection(self, image_content: bytes) -> Dict[str, Any]:
        """
        Local analysis for AI-generated image detection
        Uses heuristics and pattern detection
        """
        results = {
            "ai_generated_probability": 0.0,
            "indicators": [],
            "detailed_analysis": {}
        }
        
        try:
            image = Image.open(io.BytesIO(image_content))
            image_array = np.array(image.convert('RGB'))
            
            indicators = []
            probability_factors = []
            
            # Check 1: Unusually uniform textures
            if len(image_array.shape) == 3:
                # Analyze variance in different regions
                h, w = image_array.shape[:2]
                regions = [
                    image_array[:h//3, :w//3],
                    image_array[:h//3, 2*w//3:],
                    image_array[2*h//3:, :w//3],
                    image_array[2*h//3:, 2*w//3:]
                ]
                
                region_variances = [np.var(r) for r in regions]
                variance_std = np.std(region_variances)
                variance_mean = np.mean(region_variances)
                
                # Very low variance might indicate AI smoothing
                if variance_mean < 500:
                    indicators.append("Unusually low texture variance (possible over-smoothing)")
                    probability_factors.append(0.2)
                elif variance_std / variance_mean < 0.1:
                    indicators.append("Extremely uniform texture across regions")
                    probability_factors.append(0.15)
            
            # Check 2: Perfect dimensions (AI often generates in specific sizes)
            width, height = image.size
            common_ai_sizes = [(1024, 1024), (512, 512), (768, 768), (1536, 1536)]
            if (width, height) in common_ai_sizes:
                indicators.append(f"Common AI generation size ({width}x{height})")
                probability_factors.append(0.1)
            
            # Check 3: Color distribution (AI images sometimes have unusual distributions)
            if len(image_array.shape) == 3:
                # Check for over-saturation or unusual color balance
                hsv = image_array.astype(np.float32)
                # Simple saturation check
                saturation_variance = np.var(image_array, axis=2)
                if np.mean(saturation_variance) > 10000:
                    indicators.append("Unusual color saturation patterns")
                    probability_factors.append(0.1)
            
            # Calculate probability based on factors
            if probability_factors:
                results["ai_generated_probability"] = min(0.6, sum(probability_factors))
            else:
                results["ai_generated_probability"] = 0.1  # Low probability if no indicators
            
            results["indicators"] = indicators
            results["detailed_analysis"] = {
                "method": "local_heuristics",
                "factors_count": len(probability_factors)
            }
            
        except Exception as e:
            logger.warning(f"Error in local AI detection: {e}")
            results["error"] = str(e)
        
        return results

    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score based on result agreement"""
        analysis_method = results.get("analysis_method", "local_only")
        
        # Base confidence by method
        if analysis_method == "sightengine_api":
            confidence = 0.9  # Sightengine is highly reliable for AI detection
        elif analysis_method == "groq_api":
            confidence = 0.7  # Groq API results are moderately reliable
        else:
            confidence = 0.5  # Local analysis base confidence
        
        # Adjust based on number of indicators
        indicator_count = len(results.get("indicators", []))
        if indicator_count > 0:
            confidence = min(0.95, confidence + (indicator_count * 0.02))
        
        # Adjust based on probability extremity (clear results get higher confidence)
        probability = results.get("ai_generated_probability", 0.0)
        if probability < 0.1 or probability > 0.9:
            confidence = min(0.98, confidence + 0.08)  # Very high confidence for clear results
        elif probability < 0.2 or probability > 0.8:
            confidence = min(0.95, confidence + 0.05)  # Higher confidence for clear results
        
        return float(min(1.0, confidence))


# Singleton instance
_ai_detection_service: Optional[AIDetectionService] = None


def get_ai_detection_service() -> AIDetectionService:
    """Get or create the AI detection service singleton"""
    global _ai_detection_service
    if _ai_detection_service is None:
        _ai_detection_service = AIDetectionService()
    return _ai_detection_service

