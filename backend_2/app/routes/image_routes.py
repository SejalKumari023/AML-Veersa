from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database.connection import Database
from app.services.image_storage_service import get_image_storage_service
from app.services.metadata_extraction_service import get_metadata_extraction_service
from app.services.tampering_detection_service import get_tampering_detection_service
from app.services.forensic_analysis_service import get_forensic_analysis_service
from app.services.ai_detection_service import get_ai_detection_service
from app.services.reverse_search_service import get_reverse_search_service
import logging
import os
import asyncio
from datetime import datetime
from PIL import Image
import io

logger = logging.getLogger(__name__)

image_router = APIRouter()

class ImageAnalysis(BaseModel):
    id: Optional[str] = None
    filename: str
    file_type: str
    upload_timestamp: datetime
    analysis_status: str = "pending"
    authenticity_score: Optional[float] = None
    tampering_detected: Optional[bool] = None
    ai_generated_probability: Optional[float] = None
    findings: Optional[Dict[str, Any]] = None  # Changed from List to Dict to match verification_results
    metadata: Dict[str, Any] = {}

class ImageUploadResponse(BaseModel):
    image_id: str
    filename: str
    status: str
    message: str

@image_router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """Upload and analyze an image"""
    try:
        # Validate file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        allowed_types = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not allowed. Supported types: {allowed_types}"
            )
        
        # Read and validate image
        content = await file.read()

        # Enforce size limit (default 20 MB for images)
        max_bytes = int(os.getenv("MAX_IMAGE_SIZE", str(20 * 1024 * 1024)))
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail=f"Image too large. Max size: {max_bytes // (1024*1024)} MB")

        try:
            image = Image.open(io.BytesIO(content))
            width, height = image.size
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Extract metadata using metadata extraction service
        metadata_service = get_metadata_extraction_service()
        extracted_metadata = metadata_service.extract_metadata(content)
        
        # Create image analysis record in database
        db = Database.get_database()
        image_analysis = {
            "filename": file.filename,
            "file_type": file_extension,
            "upload_timestamp": datetime.utcnow(),
            "analysis_status": "processing",
            "file_size": len(content),
            "metadata": extracted_metadata
        }
        
        result = await db.image_analysis.insert_one(image_analysis)
        image_id = str(result.inserted_id)
        
        # Save image to disk using storage service
        storage_service = get_image_storage_service()
        try:
            file_path = storage_service.save_image(content, image_id, file_extension)
            image_hash = storage_service.get_image_hash(content)
            
            # Update database with storage info
            await db.image_analysis.update_one(
                {"_id": image_id},
                {"$set": {
                    "file_path": file_path,
                    "image_hash": image_hash
                }}
            )
            
            # Note: Image indexing for local search removed - using SerpAPI only
            
            logger.info(f"Image {image_id} saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save image {image_id} to disk: {e}")
            # Don't fail the upload, but log the error
        
        return ImageUploadResponse(
            image_id=image_id,
            filename=file.filename,
            status="uploaded",
            message="Image uploaded successfully and queued for analysis"
        )
        
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@image_router.get("/analysis/{image_id}", response_model=ImageAnalysis)
async def get_image_analysis(image_id: str):
    """Get image analysis results"""
    try:
        db = Database.get_database()

        analysis = await db.image_analysis.find_one({"_id": image_id})
        if not analysis:
            raise HTTPException(status_code=404, detail="Image analysis not found")

        # Safely convert _id to id
        if "_id" in analysis:
            analysis["id"] = str(analysis["_id"])
            del analysis["_id"]
        elif "id" not in analysis:
            # If no _id found, use the provided image_id
            analysis["id"] = image_id
        
        # Handle backward compatibility: if findings is a list, convert to dict format
        if "findings" in analysis and isinstance(analysis["findings"], list):
            # Old format was a list, convert to dict if possible
            if len(analysis["findings"]) > 0 and isinstance(analysis["findings"][0], dict):
                # If it's a list of dicts, take the first one or merge them
                analysis["findings"] = analysis["findings"][0] if len(analysis["findings"]) > 0 else None
            else:
                analysis["findings"] = None

        return ImageAnalysis(**analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching image analysis {image_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@image_router.get("/analysis", response_model=List[ImageAnalysis])
async def get_all_image_analyses():
    """Get all image analyses"""
    try:
        db = Database.get_database()
        analyses_cursor = await db.image_analysis.find()
        analyses = []
        
        async for analysis in analyses_cursor:
            # Safely convert _id to id
            if "_id" in analysis:
                analysis["id"] = str(analysis["_id"])
                del analysis["_id"]
            elif "id" not in analysis:
                # If no _id, skip or use a default
                analysis["id"] = "unknown"
            
            # Handle backward compatibility: if findings is a list, convert to dict format
            if "findings" in analysis and isinstance(analysis["findings"], list):
                if len(analysis["findings"]) > 0 and isinstance(analysis["findings"][0], dict):
                    analysis["findings"] = analysis["findings"][0] if len(analysis["findings"]) > 0 else None
                else:
                    analysis["findings"] = None
            
            try:
                analyses.append(ImageAnalysis(**analysis))
            except Exception as e:
                logger.warning(f"Skipping invalid analysis record: {e}")
                continue
        
        return analyses
        
    except Exception as e:
        logger.error(f"Error fetching image analyses: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@image_router.post("/verify/{image_id}")
async def verify_image_authenticity(image_id: str):
    """Perform authenticity verification on an image"""
    try:
        db = Database.get_database()

        # Check if image exists
        img = await db.image_analysis.find_one({"_id": image_id})
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")

        # Get existing metadata from database
        existing_metadata = img.get("metadata", {})
        metadata_analysis = existing_metadata.get("analysis", {})
        
        # Load image from storage for tampering detection
        storage_service = get_image_storage_service()
        tampering_results = {"error": "Image not found in storage"}
        
        file_path = img.get("file_path")
        file_type = img.get("file_type", ".jpg")
        
        if file_path:
            image_content = storage_service.read_image(
                image_id,
                file_type
            )
            
            if image_content:
                # Perform tampering detection
                tampering_service = get_tampering_detection_service()
                tampering_results = tampering_service.detect_tampering(image_content)
                
                # Perform forensic analysis
                forensic_service = get_forensic_analysis_service()
                forensic_results = forensic_service.perform_forensic_analysis(image_content)
                
                # Perform AI-generated detection
                ai_detection_service = get_ai_detection_service()
                ai_results = ai_detection_service.detect_ai_generated(image_content, img.get("filename"))
        else:
            forensic_results = {"error": "Image not found in storage"}
            ai_results = {"error": "Image not found in storage", "ai_generated_probability": 0.0}
        
        # Calculate authenticity score based on metadata, tampering, and forensic results
        authenticity_score = 1.0
        
        # Reduce score based on metadata red flags
        if metadata_analysis.get("red_flags"):
            authenticity_score -= len(metadata_analysis["red_flags"]) * 0.1
        
        # Reduce score based on tampering detection
        if tampering_results.get("tampering_detected", False):
            authenticity_score -= tampering_results.get("confidence", 0.5) * 0.3
        
        # Reduce score based on forensic analysis
        forensic_manipulation = forensic_results.get("manipulation_probability", 0.0)
        if forensic_manipulation > 0.3:
            authenticity_score -= forensic_manipulation * 0.4
        
        # Use forensic score if available
        if "forensic_score" in forensic_results:
            authenticity_score = (authenticity_score + forensic_results["forensic_score"]) / 2
        
        # Ensure score is between 0 and 1
        authenticity_score = max(0.0, min(1.0, authenticity_score))
        
        # Adjust authenticity score based on AI detection
        ai_probability = ai_results.get("ai_generated_probability", 0.0)
        if ai_probability > 0.5:
            # Reduce authenticity if AI-generated
            authenticity_score *= (1.0 - ai_probability * 0.3)
        
        # Build verification results
        verification_results = {
            "authenticity_score": round(authenticity_score, 2),
            "tampering_detected": tampering_results.get("tampering_detected", False),
            "ai_generated_probability": round(ai_probability, 2),
            "metadata_analysis": {
                "exif_present": metadata_analysis.get("exif_present", False),
                "camera_info": metadata_analysis.get("camera_info", {}),
                "timestamp_consistent": metadata_analysis.get("timestamp_consistent"),
                "red_flags": metadata_analysis.get("red_flags", []),
                "anomalies": metadata_analysis.get("metadata_anomalies", [])
            },
            "pixel_analysis": tampering_results,
            "forensic_analysis": forensic_results,
            "ai_detection": ai_results,
            "verification_timestamp": datetime.utcnow()
        }

        # Update image with verification results
        await db.image_analysis.update_one(
            {"_id": image_id},
            {
                "$set": {
                    "analysis_status": "completed",
                    "authenticity_score": verification_results["authenticity_score"],
                    "tampering_detected": verification_results["tampering_detected"],
                    "ai_generated_probability": verification_results["ai_generated_probability"],
                    "findings": verification_results,
                    "analysis_completed_at": datetime.utcnow()
                }
            }
        )

        return verification_results

    except Exception as e:
        logger.error(f"Error verifying image {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@image_router.post("/reverse-search/{image_id}")
async def reverse_image_search(image_id: str, limit: int = 10):
    """Perform reverse image search to detect stolen images"""
    try:
        db = Database.get_database()

        # Check if image exists
        img = await db.image_analysis.find_one({"_id": image_id})
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")

        # Load image from storage
        storage_service = get_image_storage_service()
        file_path = img.get("file_path")
        file_type = img.get("file_type", ".jpg")
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Image file not found in storage")
        
        image_content = storage_service.read_image(image_id, file_type)
        if not image_content:
            raise HTTPException(status_code=404, detail="Could not read image file")
        
        # Perform reverse search using SerpAPI only
        reverse_search_service = get_reverse_search_service()
        search_results = await reverse_search_service.search_similar(image_content, limit=limit)
        
        # Add metadata
        search_results["search_timestamp"] = datetime.utcnow()
        
        # Calculate confidence based on matches found
        if search_results.get("similar_images"):
            # Use highest similarity as confidence
            max_similarity = max(img.get("similarity", 0.0) for img in search_results["similar_images"])
            search_results["confidence"] = max_similarity
        else:
            search_results["confidence"] = 0.0
        
        # Add stolen image indicator based on matches
        if search_results.get("matches_found", 0) > 0:
            similar_images = search_results.get("similar_images", [])
            if len(similar_images) > 0:
                search_results["potentially_stolen"] = True
                search_results["stolen_confidence"] = min(0.9, 0.5 + (len(similar_images) * 0.05))
                search_results["stolen_indicators"] = [
                    f"Found {len(similar_images)} potential matches on the web",
                    f"Top match: {similar_images[0].get('title', 'Unknown')} at {similar_images[0].get('link', 'N/A')}"
                ]
            else:
                search_results["potentially_stolen"] = False
        else:
            search_results["potentially_stolen"] = False

        return search_results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing reverse search for image {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")