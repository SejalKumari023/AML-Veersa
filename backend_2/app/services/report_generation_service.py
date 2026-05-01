"""
Report Generation Service for Multi-Persona Document & Image Analysis Reports

Generates tailored markdown reports using Groq API for:
- Executive Summary (Front Office & Legal)
- Issue Breakdown (Compliance Officers)
- Image & Authenticity Checks (Compliance/Legal)
- Document Format Validation (Front Office/Ops)
- Audit Trail (Compliance & Internal Audit)
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from app.utils.logging_config import setup_logging
from app.config import GROQ_API_KEY
from app.database.connection import Database

_log = setup_logging(level="INFO")


class ReportGenerationService:
    """Generate persona-specific reports using Groq API"""
    
    def __init__(self):
        self.groq_api_key = GROQ_API_KEY
        if not self.groq_api_key:
            raise Exception("GROQ_API_KEY not found in environment variables")
    
    def _get_groq_client(self):
        """Initialize Groq client"""
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_api_key)
            return client
        except Exception as e:
            _log.error(f"Groq client initialization error: {e}")
            import os
            os.environ.pop('HTTP_PROXY', None)
            os.environ.pop('HTTPS_PROXY', None)
            os.environ.pop('http_proxy', None)
            os.environ.pop('https_proxy', None)
            client = Groq(api_key=self.groq_api_key)
            return client
    
    def _format_risk_level(self, risk_score: float) -> tuple:
        """Convert risk score to level and emoji"""
        if risk_score >= 0.7:
            return ("High", "🔴", "high")
        elif risk_score >= 0.4:
            return ("Medium", "🟡", "medium")
        else:
            return ("Low", "🟢", "low")
    
    def _calculate_integrity_score(self, image_data: Dict[str, Any]) -> float:
        """Calculate overall image integrity score from various checks"""
        authenticity_score = image_data.get("authenticity_score", 1.0)
        ai_probability = image_data.get("ai_generated_probability", 0.0)
        tampering_detected = image_data.get("tampering_detected", False)
        
        # Integrity = authenticity adjusted by AI and tampering
        integrity = authenticity_score
        if ai_probability > 0.5:
            integrity *= (1.0 - ai_probability * 0.3)
        if tampering_detected:
            integrity *= 0.5
        
        return round(integrity * 100, 0)
    
    def _format_verdict(self, risk_score: float, issues_count: int) -> str:
        """Generate summary verdict based on risk and issues"""
        risk_level, _, _ = self._format_risk_level(risk_score)
        
        if risk_score < 0.3 and issues_count == 0:
            return "Document accepted; no issues detected."
        elif risk_score < 0.5 and issues_count < 3:
            return "Document accepted provisionally; minor issues noted."
        elif risk_score < 0.7:
            return "Document requires review; authenticity check recommended."
        else:
            return "Document rejected; significant issues require resolution."
    
    async def generate_executive_summary(
        self,
        document_data: Dict[str, Any],
        image_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Executive Summary report (Front Office & Legal)
        Goal: Instant clarity on whether document can be accepted or needs review
        """
        risk_score = document_data.get("risk_score", 0.0)
        risk_level, risk_emoji, risk_class = self._format_risk_level(risk_score)
        risk_score_display = int(risk_score * 100)
        
        issues_count = len(document_data.get("findings", []))
        verdict = self._format_verdict(risk_score, issues_count)
        
        filename = document_data.get("filename", "Unknown")
        doc_type = document_data.get("metadata", {}).get("document_type", "Document")
        upload_timestamp = document_data.get("upload_timestamp", datetime.utcnow())
        
        # Build data summary for Groq
        data_summary = {
            "risk_score": risk_score_display,
            "risk_level": risk_level,
            "risk_emoji": risk_emoji,
            "verdict": verdict,
            "document_type": doc_type,
            "filename": filename,
            "upload_date": upload_timestamp.isoformat() if isinstance(upload_timestamp, datetime) else str(upload_timestamp),
            "total_issues": issues_count,
            "errors": document_data.get("metadata", {}).get("errors", 0),
            "warnings": document_data.get("metadata", {}).get("warnings", 0),
        }
        
        if image_data:
            integrity_score = self._calculate_integrity_score(image_data.get("findings", {}))
            data_summary["image_integrity_score"] = integrity_score
            data_summary["authenticity_score"] = image_data.get("authenticity_score", 0)
        
        prompt = f"""Generate an Executive Summary report for document analysis in markdown format.

REQUIREMENTS:
- Start with "# Executive Summary"
- Use clear, concise business language (not technical jargon)
- Focus on actionable decision: can document be accepted?
- Include all required sections below
- Use emojis for visual indicators where appropriate
- Keep it brief (1-2 pages max)

DATA PROVIDED:
{json.dumps(data_summary, indent=2)}

STRUCTURE REQUIRED:
1. **Overall Risk Score**: {data_summary['risk_score']}/100 ({data_summary['risk_level']} Risk {data_summary['risk_emoji']})
2. **Risk Level Indicator**: {data_summary['risk_emoji']} {data_summary['risk_level']}
3. **Summary Verdict**: {data_summary['verdict']}
4. **Document Information**:
   - Type: {data_summary['document_type']}
   - Source: {data_summary['filename']}
   - Upload Date: {data_summary['upload_date']}
5. **Quick Stats**:
   - Total Issues: {data_summary['total_issues']}
   - Errors: {data_summary['errors']}
   - Warnings: {data_summary['warnings']}

{f"6. **Image Integrity**: {data_summary.get('image_integrity_score', 0)}/100 (Authenticity: {data_summary.get('authenticity_score', 0)})" if image_data else ""}

Generate the complete markdown report now. Use professional formatting with proper headers, bold text for key metrics, and clear sections."""
        
        return await self._call_groq(prompt, "executive_summary")
    
    async def generate_issue_breakdown(
        self,
        document_data: Dict[str, Any]
    ) -> str:
        """
        Generate Issue Breakdown report (Compliance Officers)
        Goal: Show exactly what triggered risk or anomalies
        """
        findings = document_data.get("findings", [])
        risk_score = document_data.get("risk_score", 0.0)
        filename = document_data.get("filename", "Unknown")
        
        # Group issues by category and severity
        issues_by_category = {}
        for finding in findings:
            category = finding.get("category", "Unknown")
            if category not in issues_by_category:
                issues_by_category[category] = []
            issues_by_category[category].append(finding)
        
        data_summary = {
            "filename": filename,
            "risk_score": round(risk_score * 100, 1),
            "total_issues": len(findings),
            "issues_by_category": issues_by_category,
            "all_findings": findings
        }
        
        prompt = f"""Generate a detailed Issue Breakdown report for compliance officers in markdown format.

REQUIREMENTS:
- Start with "# Issue Breakdown"
- Create a table with columns: Category | Description | Severity | Suggested Action
- Group issues by category with subheaders
- Use clear, technical language (compliance officers need detail)
- Prioritize High severity issues first
- Provide actionable suggestions for each issue
- Link each issue to potential document locations if provided

DATA PROVIDED:
{json.dumps(data_summary, indent=2, default=str)}

STRUCTURE REQUIRED:
1. **Summary**: Total issues found, breakdown by severity
2. **Issue Table**: All issues with Category, Description, Severity, Suggested Action
3. **Detailed Findings**: Expand each high/medium severity issue with:
   - Exact location in document (if available)
   - Impact assessment
   - Remediation steps

Generate the complete markdown report with proper table formatting."""
        
        return await self._call_groq(prompt, "issue_breakdown")
    
    async def generate_authenticity_report(
        self,
        image_data: Dict[str, Any],
        document_filename: Optional[str] = None
    ) -> str:
        """
        Generate Image & Authenticity Checks report (Compliance/Legal)
        Goal: Validate document/images haven't been manipulated
        """
        findings = image_data.get("findings", {})
        authenticity_score = image_data.get("authenticity_score", 0.0)
        tampering_detected = image_data.get("tampering_detected", False)
        ai_probability = image_data.get("ai_generated_probability", 0.0)
        
        metadata_analysis = findings.get("metadata_analysis", {})
        pixel_analysis = findings.get("pixel_analysis", {})
        forensic_analysis = findings.get("forensic_analysis", {})
        ai_detection = findings.get("ai_detection", {})
        
        integrity_score = self._calculate_integrity_score(image_data)
        
        data_summary = {
            "document_filename": document_filename or "Unknown",
            "authenticity_score": round(authenticity_score * 100, 1),
            "integrity_score": integrity_score,
            "tampering_detected": tampering_detected,
            "ai_generated_probability": round(ai_probability * 100, 1),
            "metadata_analysis": metadata_analysis,
            "pixel_analysis": pixel_analysis,
            "forensic_analysis": forensic_analysis,
            "ai_detection": ai_detection
        }
        
        prompt = f"""Generate an Image & Authenticity Checks report for compliance/legal teams in markdown format.

REQUIREMENTS:
- Start with "# Image & Authenticity Analysis"
- Use technical but accessible language
- Focus on evidence of manipulation or tampering
- Include specific metrics and probabilities
- Highlight any red flags prominently

DATA PROVIDED:
{json.dumps(data_summary, indent=2, default=str)}

STRUCTURE REQUIRED:
1. **Integrity Score**: {data_summary['integrity_score']}/100
2. **Tampering Analysis**:
   - Detected: {data_summary['tampering_detected']}
   - Pixel-level analysis results
   - ELA visualization indicators (if available)
3. **Metadata Review**:
   - Creation date and software used
   - Modification timestamps
   - Red flags found
4. **AI-Generated Probability**: {data_summary['ai_generated_probability']}% likelihood AI-generated
5. **Reverse Image Search**: Results (if available)
6. **Forensic Analysis**: Detailed technique results

Generate the complete markdown report with technical details and evidence."""
        
        return await self._call_groq(prompt, "authenticity_check")
    
    async def generate_format_validation_report(
        self,
        document_data: Dict[str, Any]
    ) -> str:
        """
        Generate Document Format Validation report (Front Office/Ops)
        Goal: Check structural compliance with expected templates
        """
        validation_report = document_data.get("validation_report", {})
        findings = document_data.get("findings", [])
        metadata = document_data.get("metadata", {})
        
        # Calculate completeness score
        total_pages = metadata.get("total_pages", 0)
        total_issues = metadata.get("total_issues", 0)
        completeness_score = max(0, 100 - (total_issues * 10))  # Rough calculation
        
        # Extract structure issues
        structure_issues = [f for f in findings if f.get("category") == "structure"]
        formatting_issues = [f for f in findings if f.get("category") == "formatting"]
        
        data_summary = {
            "filename": document_data.get("filename", "Unknown"),
            "completeness_score": completeness_score,
            "total_pages": total_pages,
            "structure_issues": structure_issues,
            "formatting_issues": formatting_issues,
            "validation_summary": validation_report.get("summary", {}),
            "expected_sections": validation_report.get("expected_sections", []),
            "found_sections": validation_report.get("found_sections", [])
        }
        
        prompt = f"""Generate a Document Format Validation report for front office/operations teams in markdown format.

REQUIREMENTS:
- Start with "# Document Format Validation"
- Focus on structural compliance and completeness
- Use clear, actionable language
- Highlight missing sections prominently
- Provide quick checklist format where possible

DATA PROVIDED:
{json.dumps(data_summary, indent=2, default=str)}

STRUCTURE REQUIRED:
1. **Completeness Score**: {data_summary['completeness_score']}/100
2. **Header/Footer Consistency**: Check results
3. **Section Order**: Expected vs found sections
4. **Formatting Flags**: Any irregular formatting detected
5. **Missing Elements**: List of missing sections/headers
6. **Recommendations**: Quick fixes needed

Generate the complete markdown report focused on structural compliance."""
        
        return await self._call_groq(prompt, "format_validation")
    
    async def generate_audit_trail(
        self,
        document_data: Dict[str, Any],
        image_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Audit Trail report (Compliance & Internal Audit)
        Goal: Preserve traceability for regulatory defense
        """
        upload_timestamp = document_data.get("upload_timestamp", datetime.utcnow())
        completed_at = document_data.get("analysis_completed_at", datetime.utcnow())
        
        # Determine checks performed
        checks_performed = []
        if document_data.get("processed_files"):
            checks_performed.append("OCR/Text Extraction")
            checks_performed.append("Document Structure Validation")
            checks_performed.append("Content Validation")
        
        if image_data:
            checks_performed.append("Metadata Analysis")
            if image_data.get("findings", {}).get("pixel_analysis"):
                checks_performed.append("ELA (Error Level Analysis)")
            if image_data.get("findings", {}).get("forensic_analysis"):
                checks_performed.append("Forensic Analysis")
            if image_data.get("findings", {}).get("ai_detection"):
                checks_performed.append("AI-Generated Detection")
            if "reverse_search" in str(image_data.get("findings", {})):
                checks_performed.append("Reverse Image Search")
        
        data_summary = {
            "document_id": document_data.get("id", "Unknown"),
            "filename": document_data.get("filename", "Unknown"),
            "upload_timestamp": upload_timestamp.isoformat() if isinstance(upload_timestamp, datetime) else str(upload_timestamp),
            "analysis_completed_at": completed_at.isoformat() if isinstance(completed_at, datetime) else str(completed_at),
            "checks_performed": checks_performed,
            "processing_method": document_data.get("validation_report", {}).get("processing_method", "Unknown"),
            "analyst_id": "SYSTEM",  # Could be user ID if available
            "version": "1.0"
        }
        
        prompt = f"""Generate an Audit Trail report for compliance and internal audit in markdown format.

REQUIREMENTS:
- Start with "# Audit Trail"
- Use formal, regulatory-compliant language
- Include all timestamps and identifiers
- Document all checks performed
- Suitable for regulatory defense

DATA PROVIDED:
{json.dumps(data_summary, indent=2, default=str)}

STRUCTURE REQUIRED:
1. **Processing Information**:
   - Document ID: {data_summary['document_id']}
   - Filename: {data_summary['filename']}
   - Upload Timestamp: {data_summary['upload_timestamp']}
   - Analysis Completed: {data_summary['analysis_completed_at']}
2. **Analyst Information**:
   - Analyst/System ID: {data_summary['analyst_id']}
   - Processing Method: {data_summary['processing_method']}
3. **Checks Performed**: {', '.join(data_summary['checks_performed'])}
4. **Version History**: Version {data_summary['version']}

Generate the complete markdown report with all traceability information."""
        
        return await self._call_groq(prompt, "audit_trail")
    
    async def generate_complete_report(
        self,
        document_data: Dict[str, Any],
        image_data: Optional[Dict[str, Any]] = None,
        persona: str = "all"
    ) -> str:
        """
        Generate complete multi-persona report
        Combines all sections based on persona needs
        """
        reports = []
        
        # Executive Summary (always included)
        exec_summary = await self.generate_executive_summary(document_data, image_data)
        reports.append(exec_summary)
        
        if persona in ["all", "compliance", "compliance_officer"]:
            issue_breakdown = await self.generate_issue_breakdown(document_data)
            reports.append(issue_breakdown)
        
        if persona in ["all", "compliance", "legal"] and image_data:
            authenticity = await self.generate_authenticity_report(image_data, document_data.get("filename"))
            reports.append(authenticity)
        
        if persona in ["all", "front_office", "operations"]:
            format_validation = await self.generate_format_validation_report(document_data)
            reports.append(format_validation)
        
        if persona in ["all", "compliance", "audit"]:
            audit_trail = await self.generate_audit_trail(document_data, image_data)
            reports.append(audit_trail)
        
        # Combine all reports
        combined_report = "\n\n---\n\n".join(reports)
        
        # Add header
        final_report = f"""# Document Analysis Report

**Generated**: {datetime.utcnow().isoformat()}
**Document**: {document_data.get('filename', 'Unknown')}
**Persona**: {persona.title()}

---

{combined_report}
"""
        return final_report
    
    async def _call_groq(self, prompt: str, report_type: str) -> str:
        """Call Groq API to generate markdown report"""
        try:
            client = self._get_groq_client()
            
            models_to_try = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "llama3-70b-8192",
                "mixtral-8x7b-32768"
            ]
            
            system_message = "You are a professional report generation assistant. Generate well-structured markdown reports for financial compliance and document analysis. Use clear headers, tables, bullet points, and professional formatting."
            
            response = None
            for model_name in models_to_try:
                try:
                    _log.info(f"Calling Groq API with model: {model_name} for {report_type} report...")
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,  # Lower temperature for consistent, professional reports
                        max_tokens=4000
                    )
                    _log.info(f"Groq API {report_type} report generation completed")
                    break
                except Exception as api_error:
                    _log.warning(f"Model {model_name} failed: {api_error}")
                    continue
            
            if response is None:
                raise Exception("All Groq models failed")
            
            markdown_content = response.choices[0].message.content.strip()
            return markdown_content
            
        except Exception as e:
            _log.error(f"Error generating {report_type} report with Groq: {e}", exc_info=True)
            raise Exception(f"Failed to generate report: {str(e)}")


def get_report_generation_service() -> ReportGenerationService:
    """Get singleton instance of ReportGenerationService"""
    return ReportGenerationService()

