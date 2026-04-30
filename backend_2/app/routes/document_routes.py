from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

import os
from datetime import datetime

from app.database.connection import Database
from app.services.process_document import process_documents, DocumentProcessingResult
from app.services.validate_document import validate_document, ValidationReport
from app.utils.logging_config import setup_logging

logger = setup_logging(level="INFO")

document_router = APIRouter()

# Configuration
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Domain-specific terms for spell checking
CUSTOM_DICTIONARY: Set[str] = {
    "indemnification", "lessor", "lessee", "hereinafter",
    "aforementioned", "contractual", "sublease", "blockchain",
    "cryptocurrency", "tokenization", "aml", "kyc"
}

# Expected sections for different document types
EXPECTED_SECTIONS = {
    "contract": ["Introduction", "Terms and Conditions", "Signatures"],
    "mou": ["Parties", "Purpose", "Terms", "Signatures"],
    "agreement": ["Parties", "Recitals", "Terms", "Signatures"],
}

class DocumentAnalysis(BaseModel):
    id: Optional[str] = None
    filename: str
    file_type: str
    upload_timestamp: datetime
    analysis_status: str = "pending"
    risk_score: Optional[float] = None
    findings: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    validation_report: Optional[Dict[str, Any]] = None
    processed_files: Optional[Dict[str, str]] = None

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str

class ValidationRequest(BaseModel):
    document_type: Optional[str] = None  # "contract", "mou", "agreement"
    expected_sections: Optional[List[str]] = None
    custom_terms: Optional[List[str]] = None

async def process_document_task(
    document_id: str,
    file_path: Path,
    filename: str,
    document_type: Optional[str] = None,
    expected_sections: Optional[List[str]] = None,
    custom_terms: Optional[Set[str]] = None,
):
    """
    Background task to process and validate document.
    """
    db = Database.get_database()
    
    try:
        logger.info(f"Starting processing for document {document_id}: {filename}")
        
        # Update status to processing
        await db.document_analysis.update_one(
            {"_id": document_id},
            {"$set": {"analysis_status": "processing"}}
        )
        
        # Step 1: Process document with Docling
        output_subdir = OUTPUT_DIR / document_id
        output_subdir.mkdir(exist_ok=True)
        
        logger.info(f"Processing document with Docling...")
        results = process_documents(
            [file_path],
            output_dir=str(output_subdir),
            export_formats=["markdown", "json"],
            auto_detect=True,
            log_level="INFO",
        )
        
        if not results or not results[0].success:
            raise Exception(f"Document processing failed")
        
        process_result = results[0]
        logger.info(f"Document processed successfully")
        
        # Step 2: Use the DocumentProcessingResult directly for validation
        doc_processing_result = process_result
        
        # Step 3: Validate document
        logger.info(f"Validating document...")
        
        # Determine expected sections
        if not expected_sections and document_type:
            expected_sections = EXPECTED_SECTIONS.get(document_type, [])
        
        # Merge custom terms
        validation_dict = CUSTOM_DICTIONARY.copy()
        if custom_terms:
            validation_dict.update(custom_terms)
        
        validation_report = validate_document(
            doc_processing_result,
            expected_sections=expected_sections,
            custom_dictionary=validation_dict,
            output_json=True,  # Get dict for MongoDB
        )
        
        logger.info(f"Validation complete: {validation_report['summary']}")
        
        # Step 4: Calculate risk score based on validation issues
        risk_score = calculate_risk_score(validation_report)
        
        # Step 5: Format findings for frontend
        findings = format_findings(validation_report)
        
        # Step 6: Update database with results
        await db.document_analysis.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "analysis_status": "completed",
                    "risk_score": risk_score,
                    "findings": findings,
                    "validation_report": validation_report,
                    "processed_files": {
                        k: str(v) for k, v in process_result.output_paths.items()
                    },
                    "analysis_completed_at": datetime.utcnow(),
                    "metadata": {
                        "total_pages": validation_report.get("total_pages", 0),
                        "total_issues": validation_report["summary"]["total_issues"],
                        "errors": validation_report["summary"]["errors"],
                        "warnings": validation_report["summary"]["warnings"],
                    }
                }
            }
        )
        
        logger.info(f"Document {document_id} processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
        
        # Update status to failed
        await db.document_analysis.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "analysis_status": "failed",
                    "error_message": str(e),
                    "analysis_completed_at": datetime.utcnow()
                }
            }
        )


def calculate_risk_score(validation_report: Dict[str, Any]) -> float:
    """
    Calculate risk score based on validation issues.
    
    Returns a score between 0 (no risk) and 1 (high risk).
    """
    summary = validation_report["summary"]
    
    # Weight different issue types
    error_weight = 0.5
    warning_weight = 0.3
    info_weight = 0.1
    
    errors = summary.get("errors", 0)
    warnings = summary.get("warnings", 0)
    info = summary.get("info", 0)
    
    # Calculate weighted score
    weighted_issues = (errors * error_weight) + (warnings * warning_weight) + (info * info_weight)
    
    # Normalize to 0-1 range (assuming max 20 weighted issues = high risk)
    risk_score = min(weighted_issues / 20.0, 1.0)
    
    return round(risk_score, 3)


def format_findings(validation_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Format validation issues into a frontend-friendly structure.
    """
    findings = []
    
    for issue in validation_report.get("issues", []):
        finding = {
            "category": issue["category"],
            "severity": issue["severity"],
            "type": issue["type"],
            "description": issue["description"],
            "location": issue.get("location"),
            "suggestions": issue.get("suggestions", []),
        }
        findings.append(finding)
    
    return findings

@document_router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: Optional[str] = None,
    expected_sections: Optional[str] = None,  # Comma-separated string
    custom_terms: Optional[str] = None,  # Comma-separated string
):
    """
    Upload and analyze a document.
    
    Args:
        file: Document file to upload
        document_type: Type of document (contract, mou, agreement)
        expected_sections: Comma-separated list of expected sections
        custom_terms: Comma-separated list of domain-specific terms
    """
    try:
        # Validate file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        allowed_types = [".pdf", ".doc", ".docx"]
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not allowed. Supported types: {allowed_types}"
            )
        
        # Read file content
        content = await file.read()
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create document analysis record
        db = Database.get_database()
        doc_analysis = {
            "filename": file.filename,
            "file_type": file_extension,
            "file_path": str(file_path),
            "upload_timestamp": datetime.utcnow(),
            "analysis_status": "queued",
            "file_size": len(content),
            "metadata": {
                "document_type": document_type,
            }
        }
        
        result = await db.document_analysis.insert_one(doc_analysis)
        document_id = str(result.inserted_id)
        
        # Parse optional parameters
        parsed_sections = None
        if expected_sections:
            parsed_sections = [s.strip() for s in expected_sections.split(",")]
        
        parsed_terms = None
        if custom_terms:
            parsed_terms = {t.strip() for t in custom_terms.split(",")}
        
        # Schedule background processing
        background_tasks.add_task(
            process_document_task,
            document_id,
            file_path,
            file.filename,
            document_type,
            parsed_sections,
            parsed_terms,
        )
        
        logger.info(f"Document {document_id} queued for processing")
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="queued",
            message="Document uploaded successfully and queued for analysis"
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document analysis {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@document_router.get("/analysis", response_model=List[DocumentAnalysis])
async def get_all_document_analyses():
    """Get all document analyses"""
    try:
        db = Database.get_database()
        analyses_cursor = db.document_analysis.find().sort("upload_timestamp", -1)
        analyses = []
        
        async for analysis in analyses_cursor:
            analysis["id"] = str(analysis["_id"])
            del analysis["_id"]
            analyses.append(DocumentAnalysis(**analysis))
        
        return analyses
        
    except Exception as e:
        logger.error(f"Error fetching document analyses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@document_router.post("/validate/{document_id}")
async def revalidate_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    validation_request: Optional[ValidationRequest] = None,
):
    """
    Re-run validation on an already processed document with new parameters.
    """
    try:
        db = Database.get_database()

        # Check if document exists
        doc = await db.document_analysis.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document has been processed
        if doc.get("analysis_status") not in ["completed", "failed"]:
            raise HTTPException(
                status_code=400,
                detail="Document must be processed before re-validation"
            )
        
        file_path = Path(doc["file_path"])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Original file not found")
        
        # Extract validation parameters
        expected_sections = None
        custom_terms = None
        document_type = None
        
        if validation_request:
            expected_sections = validation_request.expected_sections
            if validation_request.custom_terms:
                custom_terms = set(validation_request.custom_terms)
            document_type = validation_request.document_type
        
        # Schedule revalidation
        background_tasks.add_task(
            process_document_task,
            document_id,
            file_path,
            doc["filename"],
            document_type,
            expected_sections,
            custom_terms,
        )
        
        # Update status
        await db.document_analysis.update_one(
            {"_id": document_id},
            {"$set": {"analysis_status": "queued"}}
        )
        
        return {
            "message": "Document queued for re-validation",
            "document_id": document_id,
            "status": "queued"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-validating document {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@document_router.get("/download/{document_id}/markdown")
async def download_markdown(document_id: str):
    """Download processed markdown file"""
    try:
        db = Database.get_database()
        
        doc = await db.document_analysis.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        processed_files = doc.get("processed_files", {})
        md_path = processed_files.get("markdown")
        
        if not md_path or not Path(md_path).exists():
            raise HTTPException(status_code=404, detail="Markdown file not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=md_path,
            media_type="text/markdown",
            filename=f"{Path(doc['filename']).stem}.md"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading markdown {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@document_router.get("/download/{document_id}/json")
async def download_json(document_id: str):
    """Download processed JSON file"""
    try:
        db = Database.get_database()
        
        doc = await db.document_analysis.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        processed_files = doc.get("processed_files", {})
        json_path = processed_files.get("json")
        
        if not json_path or not Path(json_path).exists():
            raise HTTPException(status_code=404, detail="JSON file not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=json_path,
            media_type="application/json",
            filename=f"{Path(doc['filename']).stem}.json"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading JSON {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@document_router.delete("/analysis/{document_id}")
async def delete_document_analysis(document_id: str):
    """Delete a document analysis and its files"""
    try:
        db = Database.get_database()
        
        doc = await db.document_analysis.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete files
        file_path = Path(doc.get("file_path", ""))
        if file_path.exists():
            file_path.unlink()
        
        # Delete processed files
        output_dir = OUTPUT_DIR / document_id
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir)
        
        # Delete database record
        await db.document_analysis.delete_one({"_id": document_id})
        
        return {
            "message": "Document analysis deleted successfully",
            "document_id": document_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")