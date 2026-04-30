from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database.connection import Database
import logging
import os
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

document_router = APIRouter()

class DocumentAnalysis(BaseModel):
    id: Optional[str] = None
    filename: str
    file_type: str
    upload_timestamp: datetime
    analysis_status: str = "pending"
    risk_score: Optional[float] = None
    findings: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str

@document_router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and analyze a document"""
    try:
        # Validate file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        allowed_types = [".pdf", ".doc", ".docx", ".txt"]
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not allowed. Supported types: {allowed_types}"
            )
        
        # Read file content
        content = await file.read()
        
        # Create document analysis record
        db = Database.get_database()
        doc_analysis = {
            "filename": file.filename,
            "file_type": file_extension,
            "upload_timestamp": datetime.utcnow(),
            "analysis_status": "processing",
            "file_size": len(content),
            "metadata": {}
        }
        
        result = await db.document_analysis.insert_one(doc_analysis)
        document_id = str(result.inserted_id)
        
        # TODO: Implement actual document processing
        # For now, simulate processing
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="uploaded",
            message="Document uploaded successfully and queued for analysis"
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@document_router.get("/analysis/{document_id}", response_model=DocumentAnalysis)
async def get_document_analysis(document_id: str):
    """Get document analysis results"""
    try:
        db = Database.get_database()

        analysis = await db.document_analysis.find_one({"_id": document_id})
        if not analysis:
            raise HTTPException(status_code=404, detail="Document analysis not found")

        analysis["id"] = str(analysis["_id"])
        del analysis["_id"]

        return DocumentAnalysis(**analysis)

    except Exception as e:
        logger.error(f"Error fetching document analysis {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@document_router.get("/analysis", response_model=List[DocumentAnalysis])
async def get_all_document_analyses():
    """Get all document analyses"""
    try:
        db = Database.get_database()
        analyses_cursor = db.document_analysis.find()
        analyses = []
        
        async for analysis in analyses_cursor:
            analysis["id"] = str(analysis["_id"])
            del analysis["_id"]
            analyses.append(DocumentAnalysis(**analysis))
        
        return analyses
        
    except Exception as e:
        logger.error(f"Error fetching document analyses: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@document_router.post("/validate/{document_id}")
async def validate_document(document_id: str):
    """Perform detailed validation on a document"""
    try:
        db = Database.get_database()

        # Check if document exists
        doc = await db.document_analysis.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # TODO: Implement actual validation logic
        # Mock validation results
        validation_results = {
            "format_issues": ["Double spacing detected in paragraph 3", "Inconsistent font size in header"],
            "content_issues": ["Spelling error: 'recieve' should be 'receive'", "Missing signature block"],
            "structure_issues": ["Missing table of contents", "Inconsistent section numbering"],
            "risk_score": 0.3,
            "validation_timestamp": datetime.utcnow()
        }

        # Update document with validation results
        await db.document_analysis.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "analysis_status": "completed",
                    "risk_score": validation_results["risk_score"],
                    "findings": validation_results,
                    "analysis_completed_at": datetime.utcnow()
                }
            }
        )

        return validation_results

    except Exception as e:
        logger.error(f"Error validating document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")