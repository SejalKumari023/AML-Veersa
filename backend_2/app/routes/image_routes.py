from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database.connection import Database
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
    findings: List[Dict[str, Any]] = []
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
        try:
            image = Image.open(io.BytesIO(content))
            width, height = image.size
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Create image analysis record
        db = Database.get_database()
        image_analysis = {
            "filename": file.filename,
            "file_type": file_extension,
            "upload_timestamp": datetime.utcnow(),
            "analysis_status": "processing",
            "file_size": len(content),
            "metadata": {
                "width": width,
                "height": height,
                "format": image.format
            }
        }
        
        result = await db.image_analysis.insert_one(image_analysis)
        image_id = str(result.inserted_id)
        
        # TODO: Implement actual image processing
        # For now, simulate processing
        await asyncio.sleep(0.1)  # Simulate processing time
        
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

        analysis["id"] = str(analysis["_id"])
        del analysis["_id"]

        return ImageAnalysis(**analysis)

    except Exception as e:
        logger.error(f"Error fetching image analysis {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@image_router.get("/analysis", response_model=List[ImageAnalysis])
async def get_all_image_analyses():
    """Get all image analyses"""
    try:
        db = Database.get_database()
        analyses_cursor = db.image_analysis.find()
        analyses = []
        
        async for analysis in analyses_cursor:
            analysis["id"] = str(analysis["_id"])
            del analysis["_id"]
            analyses.append(ImageAnalysis(**analysis))
        
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

        # TODO: Implement actual image verification logic
        # Mock verification results
        verification_results = {
            "authenticity_score": 0.85,
            "tampering_detected": False,
            "ai_generated_probability": 0.12,
            "metadata_analysis": {
                "exif_data_present": True,
                "camera_model": "Canon EOS R5",
                "timestamp_consistent": True
            },
            "pixel_analysis": {
                "compression_artifacts": "Normal",
                "noise_patterns": "Consistent",
                "edge_analysis": "Natural"
            },
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
async def reverse_image_search(image_id: str):
    """Perform reverse image search to detect stolen images"""
    try:
        db = Database.get_database()

        # Check if image exists
        img = await db.image_analysis.find_one({"_id": image_id})
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")

        # TODO: Implement actual reverse image search
        # Mock reverse search results
        search_results = {
            "matches_found": 0,
            "similar_images": [],
            "sources_checked": ["Google Images", "TinEye", "Bing Images"],
            "search_timestamp": datetime.utcnow(),
            "confidence": 0.95
        }

        return search_results

    except Exception as e:
        logger.error(f"Error performing reverse search for image {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")