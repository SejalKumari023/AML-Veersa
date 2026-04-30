import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from collections import Counter
import PyPDF2
from app.utils.logging_config import setup_logging
from app.services.process_document import process_documents, DocumentProcessingResult

# For spell checking
try:
    from spellchecker import SpellChecker
    SPELLCHECK_AVAILABLE = True
except ImportError:
    SPELLCHECK_AVAILABLE = False
    print("Install pyspellchecker: pip install pyspellchecker")

# For advanced PDF analysis
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Install pdfplumber: pip install pdfplumber")

_log = setup_logging(level="INFO")


@dataclass
class ValidationIssue:
    """Represents a validation issue found in the document"""
    category: str  # 'formatting', 'content', 'structure'
    severity: str  # 'error', 'warning', 'info'
    issue_type: str
    description: str
    location: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation report for a document"""
    document_path: str
    total_pages: int
    issues: List[ValidationIssue] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == 'error')
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == 'warning')
    
    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == 'info')
    
    def get_issues_by_category(self, category: str) -> List[ValidationIssue]:
        return [i for i in self.issues if i.category == category]
    
    def to_dict(self) -> dict:
        return {
            "document_path": self.document_path,
            "total_pages": self.total_pages,
            "summary": {
                "total_issues": len(self.issues),
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
            },
            "issues": [
                {
                    "category": i.category,
                    "severity": i.severity,
                    "type": i.issue_type,
                    "description": i.description,
                    "location": i.location,
                    "suggestions": i.suggestions,
                }
                for i in self.issues
            ],
        }


class DocumentValidator:
    """
    Comprehensive document validator using Docling and specialized libraries
    """
    
    def __init__(
        self,
        check_spelling: bool = True,
        check_formatting: bool = True,
        check_structure: bool = True,
        expected_sections: Optional[List[str]] = None,
        custom_dictionary: Optional[Set[str]] = None,
    ):
        """
        Initialize document validator.
        
        Args:
            process_result: Result from document processing
            check_spelling: Enable spell checking
            check_formatting: Enable formatting checks
            check_structure: Enable structure validation
            expected_sections: List of section headers that should be present
            custom_dictionary: Additional words to consider correct
        """
        self.check_spelling = check_spelling and SPELLCHECK_AVAILABLE
        self.check_formatting = check_formatting
        self.check_structure = check_structure
        self.expected_sections = expected_sections or []
        self.custom_dictionary = custom_dictionary or set()
        
        # Initialize spell checker
        if self.check_spelling:
            self.spell = SpellChecker()
            if self.custom_dictionary:
                self.spell.word_frequency.load_words(self.custom_dictionary)

    
    def validate_document(self, process_result: DocumentProcessingResult) -> ValidationReport:
        """
        Perform comprehensive validation on a document.
        
        Args:
            pdf_path: Path to PDF document
            
        Returns:
            ValidationReport with all issues found
        """
        self.process_result = process_result
        pdf_path = self.process_result.source

        report = ValidationReport(
            document_path=pdf_path,
            total_pages=0,
        )
        
        try:
            # Get document structure from Docling
            markdown = process_result.markdown
            doc_dict = process_result.dict

            if not markdown:
                report.issues.append(
                    ValidationIssue(
                        category="system",
                        severity="error",
                        issue_type="missing_data",
                        description="No markdown content available for validation",
                    )
                )
                return report
            
            if Path(pdf_path).exists():
                # Get page count
                with open(pdf_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    report.total_pages = len(pdf_reader.pages)
            else:
                _log.warning(f"PDF file not found: {pdf_path}")
            
            # Run validation checks
            if self.check_structure:
                report.issues.extend(self._validate_structure(doc_dict, markdown))
            
            if self.check_formatting and PDFPLUMBER_AVAILABLE:
                report.issues.extend(self._validate_formatting(pdf_path))
            
            if self.check_spelling:
                report.issues.extend(self._validate_spelling(markdown))
            
        except Exception as e:
            _log.error(f"Validation error: {e}", exc_info=True)
            report.issues.append(
                ValidationIssue(
                    category="system",
                    severity="error",
                    issue_type="processing_error",
                    description=f"Failed to process document: {str(e)}",
                )
            )
        
        return report
    
    def _validate_structure(
        self, doc_dict: dict, markdown: str
    ) -> List[ValidationIssue]:
        """Validate document structure and completeness."""
        issues = []
        
        # Check for expected sections
        if self.expected_sections:
            found_sections = self._extract_headers(markdown)
            missing_sections = [
                s for s in self.expected_sections 
                if not any(s.lower() in h.lower() for h in found_sections)
            ]
            
            for section in missing_sections:
                issues.append(
                    ValidationIssue(
                        category="structure",
                        severity="error",
                        issue_type="missing_section",
                        description=f"Required section missing: {section}",
                        suggestions=[f"Add section: {section}"],
                    )
                )
        
        # Check document hierarchy
        headers = self._extract_headers_with_levels(markdown)
        if headers:
            # Check for skipped header levels
            levels = [h[1] for h in headers]
            for i in range(len(levels) - 1):
                if levels[i + 1] > levels[i] + 1:
                    issues.append(
                        ValidationIssue(
                            category="structure",
                            severity="warning",
                            issue_type="skipped_header_level",
                            description=f"Header level skipped from H{levels[i]} to H{levels[i+1]}",
                            location=f"After: {headers[i][0]}",
                            suggestions=["Use consecutive header levels"],
                        )
                    )
        
        # Check for empty sections
        sections = markdown.split('\n#')
        for i, section in enumerate(sections[1:], 1):
            lines = section.strip().split('\n')
            if len(lines) <= 1:
                header = lines[0].lstrip('#').strip()
                issues.append(
                    ValidationIssue(
                        category="structure",
                        severity="warning",
                        issue_type="empty_section",
                        description=f"Section appears to be empty: {header}",
                        location=f"Section {i}",
                    )
                )
        
        return issues
    
    def _validate_formatting(self, pdf_path: Path) -> List[ValidationIssue]:
        """Validate formatting consistency using pdfplumber."""
        issues = []
        
        if not PDFPLUMBER_AVAILABLE:
            return issues
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                font_sizes = []
                fonts = []
                line_spacings = []
                indentations = []
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text with layout info
                    words = page.extract_words(
                        x_tolerance=3,
                        y_tolerance=3,
                        keep_blank_chars=False,
                    )
                    
                    if not words:
                        continue
                    
                    # Collect font information
                    for word in words:
                        if 'fontname' in word:
                            fonts.append(word['fontname'])
                        if 'height' in word:
                            font_sizes.append(word['height'])
                        if 'x0' in word:
                            indentations.append(word['x0'])
                
                # Detect irregular fonts
                if fonts:
                    font_counter = Counter(fonts)
                    total_fonts = len(fonts)
                    
                    # Check for too many different fonts
                    if len(font_counter) > 5:
                        issues.append(
                            ValidationIssue(
                                category="formatting",
                                severity="warning",
                                issue_type="irregular_fonts",
                                description=f"Document uses {len(font_counter)} different fonts",
                                suggestions=["Limit to 2-3 fonts for consistency"],
                            )
                        )
                    
                    # Check for rarely used fonts (potential mistakes)
                    for font, count in font_counter.items():
                        if count / total_fonts < 0.05 and count > 1:
                            issues.append(
                                ValidationIssue(
                                    category="formatting",
                                    severity="info",
                                    issue_type="rare_font",
                                    description=f"Font '{font}' used only {count} times ({count/total_fonts*100:.1f}%)",
                                    suggestions=["Check if this font usage is intentional"],
                                )
                            )
                
                # Detect inconsistent font sizes
                if font_sizes:
                    size_counter = Counter([round(s, 1) for s in font_sizes])
                    if len(size_counter) > 10:
                        issues.append(
                            ValidationIssue(
                                category="formatting",
                                severity="warning",
                                issue_type="inconsistent_font_sizes",
                                description=f"Document has {len(size_counter)} different font sizes",
                                suggestions=["Standardize font sizes for consistency"],
                            )
                        )
                
                # Detect inconsistent indentation
                if indentations:
                    # Round to nearest 5 points to group similar indentations
                    indent_groups = Counter([round(x / 5) * 5 for x in indentations])
                    if len(indent_groups) > 8:
                        issues.append(
                            ValidationIssue(
                                category="formatting",
                                severity="warning",
                                issue_type="inconsistent_indentation",
                                description=f"Document has {len(indent_groups)} different indentation levels",
                                suggestions=["Standardize indentation throughout document"],
                            )
                        )
                
        except Exception as e:
            _log.error(f"Formatting validation error: {e}", exc_info=True)
            issues.append(
                ValidationIssue(
                    category="formatting",
                    severity="warning",
                    issue_type="formatting_check_error",
                    description=f"Could not complete formatting checks: {str(e)}",
                )
            )
        
        return issues
    
    def _validate_spelling(self, text: str) -> List[ValidationIssue]:
        """Validate spelling in document text."""
        issues = []
        
        if not SPELLCHECK_AVAILABLE:
            return issues
        
        # Split into words, removing markdown syntax
        text_clean = re.sub(r'[#*_`\[\](){}]', ' ', text)
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text_clean)
        
        # Find misspelled words
        misspelled = self.spell.unknown(words)
        
        # Group by word for reporting
        misspelled_counter = Counter([w.lower() for w in misspelled])
        
        # Report most common misspellings
        for word, count in misspelled_counter.most_common(20):
            # Get suggestions
            candidates = self.spell.candidates(word)
            if candidates:
                suggestions = list(candidates)[:3]
            else:
                suggestions = []
            
            issues.append(
                ValidationIssue(
                    category="content",
                    severity="warning",
                    issue_type="spelling_error",
                    description=f"Possible spelling error: '{word}' (appears {count} times)",
                    suggestions=suggestions if suggestions else ["No suggestions available"],
                )
            )
        
        if len(misspelled_counter) > 20:
            issues.append(
                ValidationIssue(
                    category="content",
                    severity="info",
                    issue_type="spelling_summary",
                    description=f"Total unique potentially misspelled words: {len(misspelled_counter)}",
                    suggestions=["Run a thorough spell check"],
                )
            )
        
        return issues
    
    def _extract_headers(self, markdown: str) -> List[str]:
        """Extract all headers from markdown."""
        headers = re.findall(r'^#+\s+(.+)$', markdown, re.MULTILINE)
        return headers
    
    def _extract_headers_with_levels(self, markdown: str) -> List[Tuple[str, int]]:
        """Extract headers with their level (1-6)."""
        headers = []
        for match in re.finditer(r'^(#+)\s+(.+)$', markdown, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2)
            headers.append((text, level))
        return headers


def validate_document(
    process_result: DocumentProcessingResult, 
    # pdf_path: Path,
    expected_sections: Optional[List[str]] = None,
    custom_dictionary: Optional[Set[str]] = None,
    output_json: bool = False,
) -> Union[ValidationReport, dict]:
    """
    Convenience function to validate a document.
    
    Args:
        pdf_path: Path to PDF document
        expected_sections: Required section headers
        custom_dictionary: Domain-specific terms to ignore in spell check
        output_json: If True, return dict instead of ValidationReport
    
    Returns:
        ValidationReport or dict with validation results
    """
    validator = DocumentValidator(
        expected_sections=expected_sections,
        custom_dictionary=custom_dictionary,
    )
    
    report = validator.validate_document(process_result)
    
    return report.to_dict() if output_json else report


if __name__ == "__main__":
    """Example usage"""
    import json
    
    # Example: Validate a legal document
    custom_terms = {
        "indemnification", "lessor", "lessee", "hereinafter",
        "aforementioned", "contractual", "sublease"
    }
    
    required_sections = [
        "Introduction",
        "Terms and Conditions", 
        "Signatures",
    ]
    
    pdf_path = Path(__file__).resolve().parents[2] / "data" / "Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf"
    if pdf_path.exists():
        print(f"Validating: {pdf_path}")
        print("="*60)

        # process_results = process_documents(
        #     [pdf_path],
        #     output_dir="output/auto",
        #     export_formats=["markdown", "json"],
        #     auto_detect=True,  # Auto-detect PDF type
        #     log_level="INFO",
        # )

        md_path = Path(__file__).resolve().parents[2] / "output" / "auto" / "[NEW] Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.md"
        with open(md_path, 'r') as f:
            md_output = f.read()
        json_path = Path(__file__).resolve().parents[2] / "output" / "auto" / "[NEW] Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.json"
        with open(json_path, 'r') as f:
            json_output = json.load(f)

        process_results = DocumentProcessingResult(
            str(pdf_path),
            {"markdown": str(md_path), "json": str(json_path)},
            md_output,
            json_output,
            True
        )
        
        if process_results.success:
            report = validate_document(
                process_results,
                expected_sections=required_sections,
                custom_dictionary=custom_terms,
            )
            
            # Print summary
            print(f"\nDocument: {report.document_path}")
            print(f"Pages: {report.total_pages}")
            print(f"\nSummary:")
            print(f"  Errors: {report.error_count}")
            print(f"  Warnings: {report.warning_count}")
            print(f"  Info: {report.info_count}")
            
            # Print issues by category
            for category in ["structure", "formatting", "content"]:
                issues = report.get_issues_by_category(category)
                if issues:
                    print(f"\n{category.upper()} ISSUES ({len(issues)}):")
                    for issue in issues:
                        print(f"\n  [{issue.severity.upper()}] {issue.issue_type}")
                        print(f"  {issue.description}")
                        if issue.location:
                            print(f"  Location: {issue.location}")
                        if issue.suggestions:
                            print(f"  Suggestions: {', '.join(issue.suggestions)}")
            
            # Save to JSON
            output_dir = Path(__file__).resolve().parents[2] / "output" / "auto"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "validation_report.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"\nFull report saved to: {output_path}")

    else:
        print(f"File not found: {pdf_path}")
        print("\nExample validation report structure:")
        example_report = ValidationReport(
            document_path="example.pdf",
            total_pages=5,
            issues=[
                ValidationIssue(
                    category="structure",
                    severity="error",
                    issue_type="missing_section",
                    description="Required section missing: Signatures",
                    suggestions=["Add Signatures section at end of document"],
                ),
                ValidationIssue(
                    category="formatting",
                    severity="warning",
                    issue_type="irregular_fonts",
                    description="Document uses 7 different fonts",
                    suggestions=["Limit to 2-3 fonts for consistency"],
                ),
                ValidationIssue(
                    category="content",
                    severity="warning",
                    issue_type="spelling_error",
                    description="Possible spelling error: 'recieve' (appears 3 times)",
                    suggestions=["receive", "receiver", "received"],
                ),
            ],
        )
        print(json.dumps(example_report.to_dict(), indent=2))