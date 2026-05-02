"""
Document & Image Corroboration Agent Tools

Each tool wraps existing backend_2 services and returns a JSON string.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from langchain_core.tools import tool

from app.database.connection import Database
from app.services.report_generation_service import get_report_generation_service
from app.services.tampering_detection_service import get_tampering_detection_service
from app.services.ai_detection_service import get_ai_detection_service
from app.services.reverse_search_service import get_reverse_search_service
from app.services.image_storage_service import get_image_storage_service

logger = logging.getLogger(__name__)


def _safe_json(obj):
    """Handle datetime and other non-serialisable types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


async def _resolve_document_id(db, document_id: str) -> Optional[str]:
    """Resolve special document IDs like 'latest' or placeholders to a real ID."""
    normalized = (document_id or "").strip().lower()
    if normalized in {"latest", "latest_document", "latest_document_id", "last"}:
        latest_doc = None
        cursor = await db.document_analysis.find()
        async for doc in cursor:
            if latest_doc is None or doc.get("upload_timestamp") > latest_doc.get(
                "upload_timestamp"
            ):
                latest_doc = doc
        return latest_doc.get("_id") if latest_doc else None
    return document_id


async def _resolve_image_id(db, image_id: str) -> Optional[str]:
    """Resolve special image IDs like 'latest' or placeholders to a real ID."""
    normalized = (image_id or "").strip().lower()
    if normalized in {"latest", "latest_image", "latest_image_id", "last"}:
        latest_img = None
        cursor = await db.image_analysis.find()
        async for img in cursor:
            if latest_img is None or img.get("upload_timestamp") > latest_img.get(
                "upload_timestamp"
            ):
                latest_img = img
        return latest_img.get("_id") if latest_img else None
    return image_id


@tool
async def list_documents() -> str:
    """List all ingested documents with their status and risk scores."""
    try:
        db = Database.get_database()
        docs = []
        cursor = await db.document_analysis.find()
        async for doc in cursor:
            docs.append({
                "id": doc.get("_id"),
                "filename": doc.get("filename"),
                "analysis_status": doc.get("analysis_status"),
                "risk_score": doc.get("risk_score"),
                "upload_timestamp": doc.get("upload_timestamp"),
            })
        docs.sort(key=lambda d: d.get("upload_timestamp") or "", reverse=True)
        return json.dumps(docs[:50], default=_safe_json)
    except Exception as e:
        logger.error(f"list_documents error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_document_analysis(document_id: str) -> str:
    """Get full analysis results for a document by its ID."""
    try:
        db = Database.get_database()
        resolved_id = await _resolve_document_id(db, document_id)
        if not resolved_id:
            return json.dumps({"error": "No documents available"})
        doc = await db.document_analysis.find_one({"_id": resolved_id})
        if not doc:
            return json.dumps({"error": f"Document {resolved_id} not found"})
        return json.dumps(doc, default=_safe_json)
    except Exception as e:
        logger.error(f"get_document_analysis error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_document_risk_score(document_id: str) -> str:
    """Get the risk score and a summary of findings for a specific document."""
    try:
        db = Database.get_database()
        resolved_id = await _resolve_document_id(db, document_id)
        if not resolved_id:
            return json.dumps({"error": "No documents available"})
        doc = await db.document_analysis.find_one({"_id": resolved_id})
        if not doc:
            return json.dumps({"error": f"Document {resolved_id} not found"})
        return json.dumps({
            "document_id": resolved_id,
            "filename": doc.get("filename"),
            "risk_score": doc.get("risk_score"),
            "analysis_status": doc.get("analysis_status"),
            "findings_count": len(doc.get("findings", [])),
            "errors": doc.get("metadata", {}).get("errors", 0),
            "warnings": doc.get("metadata", {}).get("warnings", 0),
        }, default=_safe_json)
    except Exception as e:
        logger.error(f"get_document_risk_score error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def validate_document_structure(document_id: str, expected_sections: Optional[str] = None) -> str:
    """Re-run structural validation on a processed document. expected_sections is a comma-separated list."""
    try:
        db = Database.get_database()
        resolved_id = await _resolve_document_id(db, document_id)
        if not resolved_id:
            return json.dumps({"error": "No documents available"})
        doc = await db.document_analysis.find_one({"_id": resolved_id})
        if not doc:
            return json.dumps({"error": f"Document {resolved_id} not found"})

        validation_report = doc.get("validation_report")
        if validation_report:
            return json.dumps({
                "document_id": resolved_id,
                "validation_report": validation_report,
                "note": "Returning cached validation. Upload the document again to re-validate.",
            }, default=_safe_json)

        return json.dumps({
            "document_id": resolved_id,
            "status": doc.get("analysis_status"),
            "message": "No validation report available yet.",
        })
    except Exception as e:
        logger.error(f"validate_document_structure error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def list_images() -> str:
    """List all uploaded images with their analysis status and authenticity scores."""
    try:
        db = Database.get_database()
        images = []
        cursor = await db.image_analysis.find()
        async for img in cursor:
            images.append({
                "id": img.get("_id"),
                "filename": img.get("filename"),
                "analysis_status": img.get("analysis_status"),
                "authenticity_score": img.get("authenticity_score"),
                "tampering_detected": img.get("tampering_detected"),
                "ai_generated_probability": img.get("ai_generated_probability"),
            })
        return json.dumps(images[:50], default=_safe_json)
    except Exception as e:
        logger.error(f"list_images error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_image_analysis(image_id: str) -> str:
    """Get authenticity, tampering, and AI-detection results for a specific image."""
    try:
        db = Database.get_database()
        resolved_id = await _resolve_image_id(db, image_id)
        if not resolved_id:
            return json.dumps({"error": "No images available"})
        img = await db.image_analysis.find_one({"_id": resolved_id})
        if not img:
            return json.dumps({"error": f"Image {resolved_id} not found"})
        return json.dumps(img, default=_safe_json)
    except Exception as e:
        logger.error(f"get_image_analysis error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def verify_image_tampering(image_id: str) -> str:
    """Run ELA, copy-move, noise, and edge analysis to detect tampering in an image."""
    try:
        db = Database.get_database()
        resolved_id = await _resolve_image_id(db, image_id)
        if not resolved_id:
            return json.dumps({"error": "No images available"})
        img = await db.image_analysis.find_one({"_id": resolved_id})
        if not img:
            return json.dumps({"error": f"Image {resolved_id} not found"})

        storage_svc = get_image_storage_service()
        file_type = img.get("file_type", "jpg").lstrip(".")
        image_bytes = storage_svc.read_image(resolved_id, file_type)
        if not image_bytes:
            return json.dumps({"error": "Image file not found on disk"})

        svc = get_tampering_detection_service()
        result = svc.detect_tampering(image_bytes)
        return json.dumps(result, default=_safe_json)
    except Exception as e:
        logger.error(f"verify_image_tampering error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def detect_ai_generated(image_id: str) -> str:
    """Check if an image was AI-generated using Sightengine, Groq, or local heuristics."""
    try:
        db = Database.get_database()
        resolved_id = await _resolve_image_id(db, image_id)
        if not resolved_id:
            return json.dumps({"error": "No images available"})
        img = await db.image_analysis.find_one({"_id": resolved_id})
        if not img:
            return json.dumps({"error": f"Image {resolved_id} not found"})

        storage_svc = get_image_storage_service()
        file_type = img.get("file_type", "jpg").lstrip(".")
        image_bytes = storage_svc.read_image(resolved_id, file_type)
        if not image_bytes:
            return json.dumps({"error": "Image file not found on disk"})

        svc = get_ai_detection_service()
        result = svc.detect_ai_generated(image_bytes, img.get("filename", ""))
        return json.dumps(result, default=_safe_json)
    except Exception as e:
        logger.error(f"detect_ai_generated error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def reverse_image_search(image_id: str, limit: int = 10) -> str:
    """Run a reverse image search (SerpAPI/Imgur) to find if the image appears elsewhere on the web."""
    try:
        db = Database.get_database()
        resolved_id = await _resolve_image_id(db, image_id)
        if not resolved_id:
            return json.dumps({"error": "No images available"})
        img = await db.image_analysis.find_one({"_id": resolved_id})
        if not img:
            return json.dumps({"error": f"Image {resolved_id} not found"})

        storage_svc = get_image_storage_service()
        file_type = img.get("file_type", "jpg").lstrip(".")
        image_bytes = storage_svc.read_image(resolved_id, file_type)
        if not image_bytes:
            return json.dumps({"error": "Image file not found on disk"})

        svc = get_reverse_search_service()
        results = await svc.search_similar(image_bytes, limit=limit)
        return json.dumps(results, default=_safe_json)
    except Exception as e:
        logger.error(f"reverse_image_search error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def generate_persona_report(document_id: str, persona: str = "all") -> str:
    """Generate an AI-powered Groq report for a document. persona: executive, compliance, legal, front_office, audit, all."""
    try:
        db = Database.get_database()
        resolved_id = await _resolve_document_id(db, document_id)
        if not resolved_id:
            return json.dumps({"error": "No documents available"})
        doc = await db.document_analysis.find_one({"_id": resolved_id})
        if not doc:
            return json.dumps({"error": f"Document {resolved_id} not found"})

        if doc.get("analysis_status") != "completed":
            return json.dumps({
                "error": f"Document is not yet completed (status: {doc.get('analysis_status')})"
            })

        svc = get_report_generation_service()
        report = await svc.generate_complete_report(
            document_data=doc,
            image_data={},
            persona=persona,
        )
        return json.dumps({"report": report, "persona": persona}, default=_safe_json)
    except Exception as e:
        logger.error(f"generate_persona_report error: {e}")
        return json.dumps({"error": str(e)})
