import json
from pathlib import Path
from typing import Union, List, Optional, Tuple
from enum import Enum
import PyPDF2
import sys

import yaml
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel import vlm_model_specs
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
)
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling.pipeline.vlm_pipeline import VlmPipeline

from dataclasses import dataclass, field
from typing import Dict, Any

from app.utils.logging_config import setup_logging

_log = setup_logging(level="INFO")


@dataclass
class DocumentProcessingResult:
    source: str
    output_paths: Dict[str, str]
    markdown: str 
    dict: Dict[str, Any] 
    success: bool

class PdfProcessingMode(Enum):
    """PDF processing strategies"""
    STANDARD = "standard"
    VLM = "vlm"
    AUTO = "auto"  # Automatically detect


def detect_pdf_readability(
    pdf_path: Path,
    min_text_length: int = 100,
    sample_pages: int = 3,
) -> Tuple[bool, dict]:
    """
    Detect if a PDF is machine-readable.
    
    Args:
        pdf_path: Path to PDF file
        min_text_length: Minimum characters to consider readable
        sample_pages: Number of pages to sample
    
    Returns:
        Tuple of (is_readable, info_dict)
    """
    info = {
        "path": str(pdf_path),
        "is_readable": False,
        "text_length": 0,
        "pages_checked": 0,
    }
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            pages_to_check = min(sample_pages, num_pages)
            
            total_text = ""
            for i in range(pages_to_check):
                page = reader.pages[i]
                text = page.extract_text()
                total_text += text
            
            text_length = len(total_text.strip())
            is_readable = text_length >= min_text_length
            
            info.update({
                "is_readable": is_readable,
                "text_length": text_length,
                "pages_checked": pages_to_check,
                "total_pages": num_pages,
            })
            
            _log.debug(
                f"PDF detection: {pdf_path.name} - "
                f"{'Machine-readable' if is_readable else 'Scanned'} "
                f"({text_length} chars from {pages_to_check} pages)"
            )
            
            return is_readable, info
    
    except Exception as e:
        _log.error(f"Error detecting PDF readability: {e}")
        info["error"] = str(e)
        return False, info


class DocumentProcessor:
    """
    A unified document processor with automatic PDF type detection.
    """
    
    def __init__(
        self,
        output_dir: Union[str, Path] = "output",
        pdf_mode: PdfProcessingMode = PdfProcessingMode.AUTO,
        use_mlx_acceleration: bool = False,
        log_level: str = "INFO",
    ):
        """
        Initialize the document processor.
        
        Args:
            output_dir: Directory to save output files
            pdf_mode: Processing mode (STANDARD, VLM, or AUTO)
            use_mlx_acceleration: Use MLX on macOS for VLM
            log_level: Logging level
        """
        if log_level:
            _log.setLevel(log_level.upper())
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_mode = pdf_mode
        self.use_mlx_acceleration = use_mlx_acceleration
        
        _log.debug(f"Initializing DocumentProcessor with pdf_mode={pdf_mode.value}")
        
        # We'll create converters on-demand for AUTO mode
        self._standard_converter = None
        self._vlm_converter = None
    
    def _create_converter(self, use_vlm: bool) -> DocumentConverter:
        """Create a document converter for the specified mode."""
        
        if use_vlm:
            # VLM mode - keep it simple like the original
            vlm_options = (
                vlm_model_specs.GRANITEDOCLING_MLX
                if self.use_mlx_acceleration
                else vlm_model_specs.GRANITEDOCLING_TRANSFORMERS
            )
            
            pipeline_options = VlmPipelineOptions(vlm_options=vlm_options)
            
            # CRITICAL: For VLM, only configure PDF format, nothing else
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_cls=VlmPipeline,
                        pipeline_options=pipeline_options,
                    ),
                }
            )
            
            _log.debug(f"Created VLM converter with {'MLX' if self.use_mlx_acceleration else 'Transformers'}")
            return converter
        
        else:
            # Standard mode - configure all formats
            format_options = {
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=StandardPdfPipeline,
                    backend=PyPdfiumDocumentBackend,
                ),
                InputFormat.DOCX: WordFormatOption(pipeline_cls=SimplePipeline),
            }
            
            converter = DocumentConverter(
                allowed_formats=[
                    InputFormat.PDF,
                    InputFormat.IMAGE,
                    InputFormat.DOCX,
                    InputFormat.HTML,
                    InputFormat.PPTX,
                    InputFormat.ASCIIDOC,
                    InputFormat.CSV,
                    InputFormat.MD,
                ],
                format_options=format_options,
            )
            
            _log.debug("Created STANDARD converter")
            return converter
    
    def _get_converter(self, source: Union[str, Path]) -> DocumentConverter:
        """Get appropriate converter based on source and mode."""
        # For non-AUTO modes, use fixed converter
        if self.pdf_mode == PdfProcessingMode.STANDARD:
            if self._standard_converter is None:
                self._standard_converter = self._create_converter(use_vlm=False)
            return self._standard_converter
        
        elif self.pdf_mode == PdfProcessingMode.VLM:
            if self._vlm_converter is None:
                self._vlm_converter = self._create_converter(use_vlm=True)
            return self._vlm_converter
        
        # AUTO mode: detect PDF type
        else:
            source_path = Path(source) if not isinstance(source, Path) else source
            
            # Only detect for local PDF files
            if source_path.suffix.lower() == '.pdf' and source_path.exists():
                is_readable, detection_info = detect_pdf_readability(source_path)
                
                if is_readable:
                    _log.info(f"Auto-detected: Machine-readable PDF - using STANDARD pipeline")
                    if self._standard_converter is None:
                        self._standard_converter = self._create_converter(use_vlm=False)
                    return self._standard_converter
                else:
                    _log.info(f"Auto-detected: Scanned PDF - using VLM pipeline")
                    if self._vlm_converter is None:
                        self._vlm_converter = self._create_converter(use_vlm=True)
                    return self._vlm_converter
            
            # Default to standard for non-PDFs or URLs
            _log.debug("Using STANDARD pipeline (not a local PDF)")
            if self._standard_converter is None:
                self._standard_converter = self._create_converter(use_vlm=False)
            return self._standard_converter
    
    def process_document(
        self,
        source: Union[str, Path],
        export_formats: Optional[List[str]] = None,
    ) -> DocumentProcessingResult:
        """Process a single document with automatic pipeline selection."""
        if export_formats is None:
            export_formats = ["markdown"]
        
        _log.info(f"Processing document: {source}")
        
        try:
            # Get appropriate converter (auto-detection happens here)
            converter = self._get_converter(source)
            
            result = converter.convert(source=source)
            doc = result.document
            
            # Determine output filename
            if isinstance(source, Path):
                stem = source.stem
            else:
                stem = Path(source).stem if "/" in str(source) else "document"
            
            output_paths = {}
            markdown_content = None
            json_content = None
            
            # Export to requested formats
            if "markdown" in export_formats:
                md_path = self.output_dir / f"{stem}.md"
                markdown_content = doc.export_to_markdown()
                with md_path.open("w", encoding="utf-8") as f:
                    f.write(markdown_content)
                output_paths["markdown"] = md_path
                _log.info(f"Saved markdown: {md_path}")
            
            if "json" in export_formats:
                json_path = self.output_dir / f"{stem}.json"
                with json_path.open("w", encoding="utf-8") as f:
                    json_content = doc.export_to_dict()
                    json.dump(json_content, f, indent=2)
                output_paths["json"] = json_path
                _log.info(f"Saved JSON: {json_path}")
            
            if "yaml" in export_formats:
                yaml_path = self.output_dir / f"{stem}.yaml"
                with yaml_path.open("w", encoding="utf-8") as f:
                    yaml.safe_dump(doc.export_to_dict(), f)
                output_paths["yaml"] = yaml_path
                _log.info(f"Saved YAML: {yaml_path}")
            
            return DocumentProcessingResult(
                str(source),
                output_paths,
                markdown_content,
                json_content,
                True,
            )
        
        except Exception as e:
            _log.error(f"Failed to process {source}: {e}", exc_info=True)
            return {
                "source": str(source),
                "error": str(e),
                "success": False,
            }
    
    def process_multiple(
        self,
        sources: List[Union[str, Path]],
        export_formats: Optional[List[str]] = None,
    ) -> List[DocumentProcessingResult]:
        """Process multiple documents with automatic detection."""
        _log.info(f"Processing {len(sources)} documents")
        results = []
        
        for idx, source in enumerate(sources, 1):
            _log.info(f"Document {idx}/{len(sources)}: {source}")
            result = self.process_document(source, export_formats)
            results.append(result)
        
        successful = sum(1 for r in results if r.success)
        _log.info(f"Processing complete: {successful}/{len(sources)} successful")
        
        return results


# Simplified convenience function
def process_documents(
    sources: List[Union[str, Path]],
    output_dir: str = "output",
    export_formats: Optional[List[str]] = None,
    auto_detect: bool = True,
    use_mlx: bool = False,
    log_level: str = "INFO",
) -> List[DocumentProcessingResult]:
    """
    Process documents with automatic PDF type detection.
    
    Args:
        sources: List of document paths or URLs
        output_dir: Output directory
        export_formats: Export formats (default: ['markdown'])
        auto_detect: Automatically detect PDF type (default: True)
        use_mlx: Use MLX acceleration for VLM on macOS
        log_level: Logging level
    """
    pdf_mode = PdfProcessingMode.AUTO if auto_detect else PdfProcessingMode.STANDARD
    
    processor = DocumentProcessor(
        output_dir=output_dir,
        pdf_mode=pdf_mode,
        use_mlx_acceleration=use_mlx,
        log_level=log_level,
    )
    
    return processor.process_multiple(sources, export_formats)


if __name__ == "__main__":
    # Example: Mix of machine-readable and scanned PDFs
    documents = [
        # Path(__file__).resolve().parents[2] / "data" / "NES Memorandum of Understanding - NUS Product Club.pdf", # Machine-readable
        Path(__file__).resolve().parents[2] / "data" / "Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf", # Scanned
        # Path("../../data/NES Memorandum of Understanding - NUS Product Club.pdf"),  # Machine-readable
        # Path("../../data/Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf"),  # Scanned
        Path("README.md"),  # Markdown
    ]
    
    # Automatically detect and process with appropriate pipeline
    results = process_documents(
        documents,
        output_dir="output/auto",
        export_formats=["markdown", "json"],
        auto_detect=True,  # Auto-detect PDF type
        log_level="INFO",
    )
    
    # Print summary
    for result in results:
        if result.get("success"):
            print(f"✓ {result['source']}")
        else:
            print(f"✗ {result['source']}: {result.get('error')}")