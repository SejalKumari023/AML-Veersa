"""
Reverse Image Search Service
Detects stolen or duplicate images using perceptual hashing, local database, and SerpAPI
"""

import io
import logging
import hashlib
import base64
import os
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json
import numpy as np
from PIL import Image
import imagehash
from app.database.connection import Database
from app.config import SERPAPI_API_KEY, SERPAPI_ENABLED

logger = logging.getLogger(__name__)
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID", "")

# Import SerpAPI if available
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    logger.warning("SerpAPI library not installed. Install with: pip install google-search-results")


class ReverseSearchService:
    """Service for reverse image search using perceptual hashing"""

    def __init__(self):
        """Initialize the reverse search service"""
        self.db = Database.get_database()
        # Ensure hash index collection exists
        self.hash_collection = self.db.image_hashes
        self.serpapi_enabled = SERPAPI_ENABLED and SERPAPI_AVAILABLE
        
        if self.serpapi_enabled:
            logger.info("SerpAPI Google Reverse Image Search enabled")
        elif SERPAPI_API_KEY and not SERPAPI_AVAILABLE:
            logger.warning("SerpAPI key configured but library not installed")
        else:
            logger.info("SerpAPI Google Reverse Image Search not configured")

    async def index_image(self, image_content: bytes, image_id: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Index an image by computing and storing its perceptual hashes
        
        Args:
            image_content: Raw image bytes
            image_id: Unique identifier for the image
            metadata: Optional metadata about the image
        
        Returns:
            Dictionary containing computed hashes
        """
        try:
            image = Image.open(io.BytesIO(image_content))
            
            # Compute multiple hash types for better matching
            hashes = {
                "average": str(imagehash.average_hash(image)),
                "perceptual": str(imagehash.phash(image)),
                "difference": str(imagehash.dhash(image)),
                "wavelet": str(imagehash.whash(image)),
                "color": str(imagehash.colorhash(image))
            }
            
            # Compute SHA-256 for exact matches
            content_hash = hashlib.sha256(image_content).hexdigest()
            
            # Store in database
            hash_record = {
                "image_id": image_id,
                "hashes": hashes,
                "content_hash": content_hash,
                "metadata": metadata or {},
                "dimensions": {"width": image.size[0], "height": image.size[1]},
                "format": image.format or "unknown"
            }
            
            # Check if record exists, then update or insert
            existing = await self.hash_collection.find_one({"image_id": image_id})
            if existing:
                await self.hash_collection.update_one(
                    {"image_id": image_id},
                    {"$set": hash_record}
                )
            else:
                hash_record["_id"] = image_id  # Use image_id as _id
                await self.hash_collection.insert_one(hash_record)
            
            logger.info(f"Indexed image {image_id} with hashes")
            
            return {
                "indexed": True,
                "hashes": hashes,
                "content_hash": content_hash
            }
            
        except Exception as e:
            logger.error(f"Error indexing image {image_id}: {e}")
            return {"indexed": False, "error": str(e)}

    async def search_similar(self, image_content: bytes, image_url: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Search for similar images using SerpAPI Google and Bing Reverse Image Search
        
        Args:
            image_content: Raw image bytes
            image_url: Optional URL to the image (if provided, will use this instead of uploading)
            limit: Maximum number of results to return per engine
        
        Returns:
            Dictionary containing search results from both engines
        """
        results = {
            "matches_found": 0,
            "similar_images": [],
            "sources_checked": [],
            "search_method": "serpapi_multi_engine",
            "engines_used": []
        }
        
        if not self.serpapi_enabled:
            results["error"] = "SerpAPI is not enabled - check API key and library installation"
            logger.warning("SerpAPI is not enabled")
            return results
        
        try:
            logger.info(f"Starting multi-engine reverse image search (image_url provided: {image_url is not None})")
            
            # SerpAPI supports both image_url and image_base64
            # If we have image_content, we'll use base64 directly (no need for Imgur upload)
            # Only use image_url if explicitly provided
            
            # Perform searches with both Google and Bing using local image content
            all_similar_images = []
            engines_checked = []
            web_search_results = {}
            
            # 1. Google Reverse Image Search
            logger.info("Performing Google Reverse Image Search with local image upload...")
            google_results = await self._search_with_serpapi(image_content, image_url, engine="google_reverse_image")
            
            if not google_results.get("error"):
                google_matches = google_results.get("matches", [])
                engines_checked.append("Google")
                web_search_results["google"] = google_results
                
                for idx, img_result in enumerate(google_matches[:limit]):
                    match = {
                        "title": img_result.get("title", "Untitled"),
                        "link": img_result.get("link", ""),
                        "source": img_result.get("source", ""),
                        "thumbnail": img_result.get("thumbnail", ""),
                        "original": img_result.get("original", ""),
                        "snippet": img_result.get("snippet", ""),
                        "position": len(all_similar_images) + 1,
                        "match_type": "web_search",
                        "similarity": 1.0 - (idx * 0.05),
                        "search_engine": "Google"
                    }
                    all_similar_images.append(match)
                
                logger.info(f"Google found {len(google_matches)} matches")
            else:
                logger.warning(f"Google search error: {google_results.get('error')}")
            
            # 2. Bing Reverse Image Search
            logger.info("Performing Bing Reverse Image Search with local image upload...")
            bing_results = await self._search_with_serpapi(image_content, image_url, engine="bing_reverse_image")
            
            if not bing_results.get("error"):
                bing_matches = bing_results.get("matches", [])
                engines_checked.append("Bing")
                web_search_results["bing"] = bing_results
                
                for idx, img_result in enumerate(bing_matches[:limit]):
                    match = {
                        "title": img_result.get("title", "Untitled"),
                        "link": img_result.get("link", ""),
                        "source": img_result.get("source", ""),
                        "thumbnail": img_result.get("thumbnail", ""),
                        "original": img_result.get("original", ""),
                        "snippet": img_result.get("snippet", ""),
                        "position": len(all_similar_images) + 1,
                        "match_type": "web_search",
                        "similarity": 1.0 - (idx * 0.05),
                        "search_engine": "Bing"
                    }
                    all_similar_images.append(match)
                
                logger.info(f"Bing found {len(bing_matches)} matches")
            else:
                logger.warning(f"Bing search error: {bing_results.get('error')}")
            
            # Combine and sort results
            results["similar_images"] = all_similar_images
            results["matches_found"] = len(all_similar_images)
            results["sources_checked"] = [f"{engine} Reverse Image Search (SerpAPI)" for engine in engines_checked]
            results["engines_used"] = engines_checked
            results["web_search"] = web_search_results
            
            logger.info(f"Total matches found: {results['matches_found']} (Google: {len(google_results.get('matches', []))}, Bing: {len(bing_results.get('matches', []))})")
            
        except Exception as e:
            logger.error(f"Error in reverse image search: {e}", exc_info=True)
            results["error"] = str(e)
        
        return results

    def _create_image_data_url(self, image_content: bytes, image_format: str = "jpeg") -> str:
        """
        Create a data URL from image bytes for use with APIs that accept data URLs
        
        Args:
            image_content: Raw image bytes
            image_format: Image format (jpeg, png, etc.)
        
        Returns:
            Data URL string
        """
        import base64
        mime_types = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }
        mime_type = mime_types.get(image_format.lower(), "image/jpeg")
        base64_data = base64.b64encode(image_content).decode('utf-8')
        return f"data:{mime_type};base64,{base64_data}"

    async def _upload_to_temporary_hosting(self, image_content: bytes) -> Optional[str]:
        """
        Upload image to Imgur to get a public URL for reverse image search
        
        Args:
            image_content: Raw image bytes
        
        Returns:
            URL string if successful, None otherwise
        """
        try:
            import requests
            import base64
            
            # Imgur anonymous upload endpoint (no API key required, but rate limited)
            imgur_upload_url = "https://api.imgur.com/3/image"
            
            # Encode image to base64
            image_b64 = base64.b64encode(image_content).decode('utf-8')
            
            # Prepare headers (Imgur allows anonymous uploads)
            if not IMGUR_CLIENT_ID:
                logger.warning("IMGUR_CLIENT_ID is not configured; cannot upload image for reverse search fallback")
                return None

            headers = {
                "Authorization": f"Client-ID {IMGUR_CLIENT_ID}"
            }
            
            # Prepare data
            data = {
                'image': image_b64,
                'type': 'base64'
            }
            
            logger.info("Uploading image to Imgur for reverse image search...")
            
            # Make request (run in executor since it's blocking)
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(imgur_upload_url, headers=headers, data=data, timeout=30)
            )
            
            logger.info(f"Imgur upload response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Imgur upload response: success={result.get('success')}, status={result.get('status')}")
                
                if result.get('success'):
                    # Get the direct link (not the album link)
                    image_data = result.get('data', {})
                    image_url = image_data.get('link')
                    
                    # Imgur sometimes returns different link formats - prefer direct image link
                    if not image_url:
                        image_url = image_data.get('id')
                        if image_url:
                            image_url = f"https://i.imgur.com/{image_url}.jpg"
                    
                    if image_url:
                        # Ensure it's a direct image URL (not .gifv or with query params)
                        if '.gifv' in image_url:
                            image_url = image_url.replace('.gifv', '.jpg')
                        if '?' in image_url:
                            image_url = image_url.split('?')[0]
                            
                        logger.info(f"Successfully uploaded image to Imgur: {image_url}")
                        logger.info(f"Image URL accessible check - URL format looks valid")
                        return image_url
                    else:
                        logger.error(f"Imgur upload succeeded but no link in response. Full result: {json.dumps(result, indent=2)[:500]}")
                else:
                    error_msg = result.get('data', {}).get('error', 'Unknown error')
                    logger.error(f"Imgur upload failed: {error_msg}")
                    logger.error(f"Full Imgur response: {json.dumps(result, indent=2)[:500]}")
            else:
                logger.error(f"Imgur upload failed with status {response.status_code}")
                logger.error(f"Imgur response: {response.text[:500]}")
                
        except Exception as e:
            logger.warning(f"Failed to upload image to Imgur: {e}")
        
        return None

    async def _search_with_serpapi(self, image_content: bytes, image_url: Optional[str] = None, engine: str = "google_reverse_image") -> Dict[str, Any]:
        """
        Search for image using SerpAPI Reverse Image Search
        
        Args:
            image_content: Raw image bytes
            image_url: Optional URL to the image (if not provided, will try to create one)
            engine: Search engine to use ("google_reverse_image" or "bing_reverse_image")
        
        Returns:
            Dictionary containing SerpAPI search results
        """
        results = {
            "matches_found": 0,
            "matches": [],
            "search_method": "serpapi_google_reverse_image",
            "error": None
        }
        
        if not self.serpapi_enabled:
            results["error"] = "SerpAPI not enabled or not available"
            return results
        
        try:
            # SerpAPI reverse image search requires image_url parameter
            # If no URL provided, we need to upload to temporary hosting first
            # Then use that URL for the search
            
            import asyncio
            import base64
            loop = asyncio.get_event_loop()
            
            # Determine image URL to use
            search_image_url = image_url
            
            if not search_image_url:
                # No URL provided - need to upload image to get a public URL
                # SerpAPI doesn't directly accept base64, so we upload to Imgur first
                logger.info(f"No image URL provided for {engine}, uploading to Imgur to get public URL...")
                
                if not image_content or len(image_content) == 0:
                    results["error"] = "No image content provided and no image URL available"
                    logger.error("Cannot perform search: no image content or URL")
                    return results
                
                search_image_url = await self._upload_to_temporary_hosting(image_content)
                
                if not search_image_url:
                    results["error"] = "Failed to upload image to temporary hosting. Cannot perform reverse search without a public image URL."
                    logger.error("Cannot perform SerpAPI search: failed to get public image URL")
                    return results
                
                logger.info(f"Successfully uploaded image to Imgur: {search_image_url}")
            
            # Verify URL is accessible
            try:
                import requests
                test_response = await loop.run_in_executor(
                    None,
                    lambda: requests.head(search_image_url, timeout=10, allow_redirects=True)
                )
                logger.info(f"Image URL accessibility check: status_code={test_response.status_code}")
                
                if test_response.status_code != 200:
                    logger.warning(f"Image URL returned status {test_response.status_code} - may not be accessible to SerpAPI")
            except Exception as e:
                logger.warning(f"Could not verify image URL accessibility: {e}")
            
            # Use image URL for SerpAPI search
            logger.info(f"Using image URL for {engine}: {search_image_url[:100]}...")
            
            params = {
                "engine": engine,
                "image_url": search_image_url,
                "api_key": SERPAPI_API_KEY
            }
            
            logger.info(f"SerpAPI params: engine={params['engine']}, image_url={params['image_url'][:100]}..., api_key={'*' * 20}")
            
            # Execute search (SerpAPI is synchronous, so we run it in executor)
            search = GoogleSearch(params)
            raw_results = await loop.run_in_executor(None, search.get_dict)
            
            # Check if SerpAPI did a text search instead of image search
            # This happens when SerpAPI/Google extracts text from image via OCR and searches for that text
            search_info = raw_results.get("search_information", {})
            organic_state = search_info.get("organic_results_state", "")
            
            # Check if we got image_results (Google) or related_content (Bing)
            if engine == "bing_reverse_image":
                has_results = "related_content" in raw_results
            else:
                has_results = "image_results" in raw_results or "images_results" in raw_results
            
            # Check if organic_results_state indicates text search
            is_text_search = ("exact spelling" in organic_state.lower() or 
                            "text" in organic_state.lower())
            
            # Check for error in response
            if "error" in raw_results:
                error_msg = raw_results.get("error", "")
                logger.error(f"SerpAPI returned error: {error_msg}")
                results["error"] = error_msg
                
                # If error is about missing image_url, something went wrong with our upload
                if "image_url" in error_msg.lower():
                    logger.error("SerpAPI didn't receive image_url parameter - upload may have failed")
                    results["error"] = f"Failed to provide image URL to SerpAPI: {error_msg}"
                    return results
            
            # Check if text search was performed instead of image search
            if is_text_search and not has_results:
                logger.warning(f"SerpAPI performed text search instead of image search (state: {organic_state})")
                logger.warning("This usually means the search engine OCR'd the image and searched for extracted text")
            
            logger.info(f"SerpAPI search completed. Response keys: {list(raw_results.keys())}")
            
            # Log what parameters SerpAPI actually used
            if "search_parameters" in raw_results:
                search_params = raw_results.get("search_parameters", {})
                logger.info(f"SerpAPI search_parameters: {json.dumps(search_params, indent=2)}")
                if "image_url" in search_params:
                    logger.info(f"SerpAPI received image_url: {search_params.get('image_url')}")
                else:
                    logger.warning("SerpAPI search_parameters does NOT contain 'image_url' - this is the problem!")
            
            logger.info(f"Full SerpAPI response (first 2000 chars): {json.dumps(raw_results, indent=2)[:2000]}...")
            
            # Parse results - different engines use different field names
            images_results = []
            
            if engine == "bing_reverse_image":
                # Bing uses "related_content" field (as per SerpAPI Bing Reverse Image Search format)
                images_results = raw_results.get("related_content", [])
                logger.info(f"Bing related_content found: {len(images_results) if isinstance(images_results, list) else 'not a list'}")
                
                if not isinstance(images_results, list):
                    logger.warning(f"Bing related_content is not a list: {type(images_results)}")
                    images_results = []
            else:
                # Google uses "image_results" or "images_results"
                images_results = raw_results.get("image_results", [])  # Correct field name (singular)
                
                # Fallback to plural if singular doesn't exist (for backwards compatibility)
                if not images_results:
                    images_results = raw_results.get("images_results", [])
            
            logger.info(f"SerpAPI returned {len(images_results)} image results")
            logger.info(f"Checking for 'image_results' and 'images_results' - found: image_results={len(raw_results.get('image_results', []))}, images_results={len(raw_results.get('images_results', []))}")
            
            # Check if SerpAPI did a text search instead of image search
            # For Bing, check for "related_content", for Google check for "image_results" or "images_results"
            if engine == "bing_reverse_image":
                has_results = "related_content" in raw_results and len(images_results) > 0
            else:
                has_results = ("image_results" in raw_results or "images_results" in raw_results) and len(images_results) > 0
            
            if not has_results:
                logger.warning(f"SerpAPI response missing expected result fields. Available fields: {list(raw_results.keys())}")
                if "error" in raw_results:
                    logger.error(f"SerpAPI error in response: {raw_results['error']}")
                # Check if it did a text search instead
                if "organic_results" in raw_results or "search_information" in raw_results:
                    query = raw_results.get('search_information', {}).get('query_displayed', 'unknown')
                    logger.warning(f"SerpAPI appears to have done a TEXT search (query: '{query}') instead of IMAGE search")
                    logger.warning("This usually means the image_url is invalid, inaccessible, or SerpAPI couldn't process it")
                    results["error"] = f"SerpAPI performed text search ('{query}') instead of image search. Image URL may be invalid or inaccessible."
                    results["raw_response"] = {
                        "search_information": raw_results.get("search_information", {}),
                        "error": raw_results.get("error", None),
                        "response_keys": list(raw_results.keys())
                    }
                    return results
            
            # Check if image_results is a list or a dict with nested structure
            if isinstance(images_results, dict):
                logger.info(f"image_results is a dict, checking for nested structure: {list(images_results.keys())}")
                # Sometimes SerpAPI wraps results in a dict
                if "results" in images_results:
                    images_results = images_results["results"]
                elif "data" in images_results:
                    images_results = images_results["data"]
                else:
                    logger.warning(f"image_results is a dict but doesn't contain 'results' or 'data'. Keys: {list(images_results.keys())}")
                    images_results = []
            
            if images_results and len(images_results) > 0:
                matches = []
                logger.info(f"Processing {len(images_results)} image results from SerpAPI")
                
                for idx, img_result in enumerate(images_results[:20]):  # Limit to 20 results
                    # Handle both dict and different structure formats
                    if isinstance(img_result, dict):
                        # Bing and Google have slightly different field names
                        if engine == "bing_reverse_image":
                            match = {
                                "title": img_result.get("title", img_result.get("name", "Untitled")),
                                "link": img_result.get("link", img_result.get("url", img_result.get("href", ""))),
                                "source": img_result.get("source", img_result.get("source_name", img_result.get("domain", ""))),
                                "thumbnail": img_result.get("thumbnail", img_result.get("thumbnail_url", img_result.get("image", ""))),
                                "original": img_result.get("original", img_result.get("original_url", img_result.get("image", ""))),
                                "snippet": img_result.get("snippet", img_result.get("description", img_result.get("text", ""))),
                                "position": idx + 1,
                                "match_type": "web_search",
                                "similarity": 1.0 - (idx * 0.05),
                                "search_engine": "Bing"
                            }
                        else:
                            match = {
                                "title": img_result.get("title", img_result.get("name", "Untitled")),
                                "link": img_result.get("link", img_result.get("url", "")),
                                "source": img_result.get("source", img_result.get("source_name", "")),
                                "thumbnail": img_result.get("thumbnail", img_result.get("thumbnail_url", "")),
                                "original": img_result.get("original", img_result.get("original_url", "")),
                                "snippet": img_result.get("snippet", img_result.get("description", "")),
                                "position": idx + 1,
                                "match_type": "web_search",
                                "similarity": 1.0 - (idx * 0.05),
                                "search_engine": "Google"
                            }
                    else:
                        logger.warning(f"Unexpected image result format: {type(img_result)} - {str(img_result)[:200]}")
                        continue
                    
                    matches.append(match)
                
                results["matches"] = matches
                results["matches_found"] = len(matches)
                results["total_results"] = len(images_results)
                
                logger.info(f"Processed {results['matches_found']} matches from SerpAPI")
            else:
                logger.info(f"SerpAPI returned no image results (image_results length: {len(images_results) if isinstance(images_results, list) else 'not a list'})")
                results["matches_found"] = 0
                results["matches"] = []
                
                # Log the actual structure for debugging
                if raw_results.get("image_results") is not None:
                    logger.info(f"image_results structure: {type(raw_results.get('image_results'))}")
                    if isinstance(raw_results.get("image_results"), dict):
                        logger.info(f"image_results dict keys: {list(raw_results.get('image_results', {}).keys())}")
            
            # Store raw response for debugging
            results["raw_response"] = {
                "search_information": raw_results.get("search_information", {}),
                "error": raw_results.get("error", None),
                "image_results_count": len(images_results),
                "response_keys": list(raw_results.keys())
            }
            
            # Log a sample of image_results if available to see structure
            if images_results and len(images_results) > 0:
                logger.info(f"First image result sample: {json.dumps(images_results[0], indent=2)[:500]}")
            
        except Exception as e:
            logger.error(f"Error in SerpAPI search: {e}", exc_info=True)
            results["error"] = str(e)
        
        return results

    async def remove_index(self, image_id: str) -> bool:
        """
        Remove an image from the hash index
        
        Args:
            image_id: Unique identifier for the image to remove
        
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            result = await self.hash_collection.delete_one({"image_id": image_id})
            logger.info(f"Removed image {image_id} from hash index")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error removing image {image_id} from index: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the hash index
        
        Returns:
            Dictionary containing index statistics
        """
        try:
            total_indexed = await self.hash_collection.count_documents({})
            
            # Get sample of hash types
            sample = await self.hash_collection.find_one({})
            hash_types = list(sample.get("hashes", {}).keys()) if sample else []
            
            return {
                "total_indexed_images": total_indexed,
                "hash_types": hash_types,
                "index_status": "active"
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"error": str(e)}


# Singleton instance
_reverse_search_service: Optional[ReverseSearchService] = None


def get_reverse_search_service() -> ReverseSearchService:
    """Get or create the reverse search service singleton"""
    global _reverse_search_service
    if _reverse_search_service is None:
        _reverse_search_service = ReverseSearchService()
    return _reverse_search_service
