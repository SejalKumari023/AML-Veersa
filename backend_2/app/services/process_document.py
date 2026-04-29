import json
import re
from pathlib import Path
from typing import Union, List, Optional, Tuple
from enum import Enum
import PyPDF2
import sys
import os

import yaml
# Temporarily disabled docling imports to test Google Cloud Vision API
# from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
# from docling.datamodel import vlm_model_specs
# from docling.datamodel.base_models import InputFormat
# from docling.datamodel.pipeline_options import VlmPipelineOptions
# from docling.document_converter import (
#     DocumentConverter,
#     PdfFormatOption,
#     WordFormatOption,
# )
# from docling.pipeline.simple_pipeline import SimplePipeline
# from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
# from docling.pipeline.vlm_pipeline import VlmPipeline

from dataclasses import dataclass, field
from typing import Dict, Any

from app.utils.logging_config import setup_logging
from app.config import GOOGLE_CLOUD_VISION_ENABLED, GOOGLE_APPLICATION_CREDENTIALS, GROQ_API_KEY

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


def process_pdf_with_google_vision(pdf_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Process PDF using Google Cloud Vision API.
    Handles both text-based and image-based (scanned) PDFs.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Dictionary containing processed content
    """
    try:
        from google.cloud import vision
        from pdf2image import convert_from_path
        import io
        
        # Set credentials if provided
        if GOOGLE_APPLICATION_CREDENTIALS:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_APPLICATION_CREDENTIALS
        
        source_path = Path(pdf_path)
        if not source_path.exists():
            raise Exception(f"PDF file not found: {pdf_path}")
        
        _log.info(f"Reading PDF file: {source_path}")
        
        # Initialize Google Vision client
        try:
            _log.info("Initializing Google Cloud Vision client...")
            client = vision.ImageAnnotatorClient()
            _log.info("Google Vision client initialized successfully")
        except Exception as init_error:
            _log.error(f"Google Vision client initialization error: {init_error}", exc_info=True)
            raise
        
        # Try to extract text first (for text-based PDFs)
        pdf_text = ""
        text_annotations = []
        structured_data = []  # Store structured data for better markdown generation
        
        try:
            # Try document_text_detection for PDFs
            with open(source_path, "rb") as pdf_file:
                content = pdf_file.read()
            
            image = vision.Image(content=content)
            _log.info("Attempting document_text_detection on PDF...")
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                _log.warning(f"Google Vision error: {response.error.message}")
                raise Exception(f"Google Vision API error: {response.error.message}")
            
            full_text_annotation = response.full_text_annotation
            if full_text_annotation and full_text_annotation.text:
                pdf_text = full_text_annotation.text
                _log.info(f"Extracted {len(pdf_text)} characters using document_text_detection")
                
                # Extract structured data (blocks, paragraphs) for better markdown
                if full_text_annotation.pages:
                    for page_num, page in enumerate(full_text_annotation.pages, 1):
                        if page.blocks:
                            for block in page.blocks:
                                block_data = {
                                    "page": page_num,
                                    "paragraphs": []
                                }
                                
                                if block.paragraphs:
                                    for para in block.paragraphs:
                                        para_text = ""
                                        para_words = []
                                        
                                        if para.words:
                                            for word in para.words:
                                                word_text = ''.join([
                                                    symbol.text for symbol in word.symbols
                                                ])
                                                if word_text:
                                                    para_text += word_text + " "
                                                    annotation = {
                                                        "description": word_text,
                                                        "confidence": word.confidence if hasattr(word, 'confidence') else None
                                                    }
                                                    if word.bounding_box:
                                                        vertices = []
                                                        for vertex in word.bounding_box.vertices:
                                                            vertices.append({"x": vertex.x, "y": vertex.y})
                                                        annotation["bounding_poly"] = vertices
                                                    para_words.append(annotation)
                                        
                                        if para_text.strip():
                                            # Get font information if available
                                            font_size = None
                                            if para.property and hasattr(para.property, 'detected_break') and para.property.detected_break:
                                                # Analyze paragraph properties
                                                pass
                                            
                                            block_data["paragraphs"].append({
                                                "text": para_text.strip(),
                                                "words": para_words,
                                                "bounding_box": [
                                                    {"x": para.bounding_box.vertices[0].x, "y": para.bounding_box.vertices[0].y}
                                                    if para.bounding_box else None
                                                ]
                                            })
                                            text_annotations.extend(para_words)
                                
                                if block_data["paragraphs"]:
                                    structured_data.append(block_data)
        except Exception as e:
            _log.warning(f"document_text_detection failed (may be image-based PDF): {e}")
            pdf_text = ""
        
        # If no text extracted, convert PDF pages to images and use Vision API
        if not pdf_text or len(pdf_text.strip()) < 10:
            _log.info("PDF appears to be image-based. Converting pages to images...")
            
            try:
                # Convert PDF pages to images
                images = convert_from_path(str(source_path), dpi=200)
                _log.info(f"Converted PDF to {len(images)} images")
                
                # Process each image with Google Vision
                pdf_text = ""
                for page_num, img in enumerate(images, 1):
                    _log.info(f"Processing page {page_num}/{len(images)} with Google Vision...")
                    
                    # Convert PIL Image to bytes
                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    image_content = buffered.getvalue()
                    
                    # Send to Google Vision
                    image = vision.Image(content=image_content)
                    response = client.document_text_detection(image=image)
                    
                    if response.error.message:
                        _log.warning(f"Google Vision error for page {page_num}: {response.error.message}")
                        continue
                    
                    full_text_annotation = response.full_text_annotation
                    if full_text_annotation and full_text_annotation.text:
                        page_text = full_text_annotation.text
                        pdf_text += f"\n\n--- Page {page_num} ---\n\n{page_text}"
                        
                        # Extract structured data for better markdown generation
                        if full_text_annotation.pages:
                            for page in full_text_annotation.pages:
                                if page.blocks:
                                    for block in page.blocks:
                                        block_data = {
                                            "page": page_num,
                                            "paragraphs": []
                                        }
                                        
                                        if block.paragraphs:
                                            for para in block.paragraphs:
                                                para_text = ""
                                                para_words = []
                                                
                                                if para.words:
                                                    for word in para.words:
                                                        word_text = ''.join([
                                                            symbol.text for symbol in word.symbols
                                                        ])
                                                        if word_text:
                                                            para_text += word_text + " "
                                                            annotation = {
                                                                "description": word_text,
                                                                "page": page_num
                                                            }
                                                            if word.bounding_box:
                                                                vertices = []
                                                                for vertex in word.bounding_box.vertices:
                                                                    vertices.append({"x": vertex.x, "y": vertex.y})
                                                                annotation["bounding_poly"] = vertices
                                                            para_words.append(annotation)
                                                
                                                if para_text.strip():
                                                    block_data["paragraphs"].append({
                                                        "text": para_text.strip(),
                                                        "words": para_words
                                                    })
                                                    text_annotations.extend(para_words)
                                        
                                        if block_data["paragraphs"]:
                                            structured_data.append(block_data)
                
                if not pdf_text or len(pdf_text.strip()) < 10:
                    raise Exception("Google Vision could not extract meaningful text from PDF images")
                
                _log.info(f"Google Vision extracted {len(pdf_text)} characters from images")
                    
            except Exception as e:
                _log.error(f"Error processing image-based PDF with Google Vision: {e}", exc_info=True)
                raise Exception(f"Could not process image-based PDF with Google Vision. Error: {str(e)}")
        
        return {
            "full_text": pdf_text,
            "text_annotations": text_annotations,
            "text_count": len(text_annotations),
            "structured_data": structured_data,  # Include structured data for markdown generation
            "source": "google_vision"
        }
        
    except ImportError:
        raise Exception(
            "Google Cloud Vision library not installed. "
            "Install with: pip install google-cloud-vision"
        )
    except Exception as e:
        _log.error(f"Google Vision API error: {e}", exc_info=True)
        raise Exception(f"Google Vision API failed: {str(e)}")


def detect_heading(text: str, y_position: Optional[float] = None, prev_y: Optional[float] = None) -> bool:
    """
    Detect if a paragraph is likely a heading based on text patterns and positioning.
    
    Args:
        text: Text content
        y_position: Y coordinate of the text
        prev_y: Y coordinate of previous paragraph
    
    Returns:
        True if text appears to be a heading
    """
    text_stripped = text.strip()
    
    # Heading indicators:
    # 1. Short text (typically headings are shorter)
    # 2. All caps (often used for headings)
    # 3. Ends with colon
    # 4. Starts with number (numbered sections)
    # 5. Contains common heading words
    is_short = len(text_stripped.split()) <= 10 and len(text_stripped) < 80
    is_mostly_upper = text_stripped.isupper() and len(text_stripped) > 3
    ends_with_colon = text_stripped.endswith(':')
    starts_with_number = bool(text_stripped and text_stripped[0].isdigit())
    has_heading_keywords = any(word in text_stripped.lower() for word in [
        'section', 'chapter', 'article', 'clause', 'appendix', 'schedule',
        'part', 'title', 'heading', 'introduction', 'summary', 'conclusion'
    ])
    
    # If significantly higher on page than previous paragraph, might be heading
    is_at_top = y_position and prev_y and (prev_y - y_position) > 20
    
    # Combine indicators
    heading_score = sum([
        is_short,
        is_mostly_upper,
        ends_with_colon,
        starts_with_number,
        has_heading_keywords,
        bool(is_at_top)
    ])
    
    return heading_score >= 2  # Need at least 2 indicators


def convert_structured_to_markdown(structured_data: List[Dict[str, Any]], fallback_text: str) -> str:
    """
    Convert structured data from Google Vision to properly formatted Markdown.
    
    Args:
        structured_data: List of blocks with paragraphs
        fallback_text: Plain text fallback
    
    Returns:
        Formatted markdown content
    """
    if not structured_data:
        # Fallback to simple markdown
        return f"# Document Content\n\n{fallback_text}"
    
    markdown_lines = []
    prev_y = None
    
    for block in structured_data:
        for para_idx, para in enumerate(block.get("paragraphs", [])):
            para_text = para.get("text", "").strip()
            if not para_text:
                continue
            
            # Get Y position if available
            bounding_box = para.get("bounding_box")
            y_position = None
            if bounding_box and isinstance(bounding_box, list) and len(bounding_box) > 0:
                if isinstance(bounding_box[0], dict) and "y" in bounding_box[0]:
                    y_position = bounding_box[0]["y"]
                elif bounding_box[0] is not None:
                    # Try to extract from tuple or other format
                    try:
                        y_position = float(bounding_box[0].get("y", 0)) if isinstance(bounding_box[0], dict) else None
                    except:
                        y_position = None
            
            # Detect if this is a heading
            is_heading = detect_heading(para_text, y_position, prev_y)
            
            if is_heading:
                # Use heading format - try to determine heading level
                # Most headings at document start are H1, others might be H2
                if markdown_lines and len(markdown_lines) < 5:
                    markdown_lines.append(f"# {para_text}")
                else:
                    markdown_lines.append(f"## {para_text}")
            else:
                # Regular paragraph
                # Check if it looks like a list item
                if para_text and (para_text[0] in ['-', '*', '•', '·'] or 
                                  (para_text[0].isdigit() and '.' in para_text[:5])):
                    markdown_lines.append(para_text)
                else:
                    markdown_lines.append(para_text)
            
            # Add spacing between paragraphs
            markdown_lines.append("")
            prev_y = y_position
    
    # Join and clean up excessive blank lines
    markdown_content = "\n".join(markdown_lines)
    # Remove more than 2 consecutive blank lines
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
    
    return markdown_content.strip() if markdown_content.strip() else f"# Document Content\n\n{fallback_text}"


def convert_text_to_markdown_with_groq(text: str) -> str:
    """
    Convert plain text to properly formatted Markdown using Groq API.
    Groq will understand the document structure and format it correctly.
    
    Args:
        text: Plain text extracted from Google Vision
    
    Returns:
        Formatted markdown content
    """
    try:
        from groq import Groq
        
        if not GROQ_API_KEY:
            raise Exception("GROQ_API_KEY not found in environment variables")
        
        _log.info("Sending text to Groq API for markdown conversion...")
        
        # Initialize Groq client
        try:
            client = Groq(api_key=GROQ_API_KEY)
        except Exception as init_error:
            _log.error(f"Groq client initialization error: {init_error}")
            import os
            os.environ.pop('HTTP_PROXY', None)
            os.environ.pop('HTTPS_PROXY', None)
            os.environ.pop('http_proxy', None)
            os.environ.pop('https_proxy', None)
            client = Groq(api_key=GROQ_API_KEY)
        
        # Create prompt for markdown conversion
        prompt = f"""Convert the following document text into well-formatted Markdown. 
Analyze the structure and format it with appropriate headings, paragraphs, lists, and sections.

IMPORTANT: Do NOT correct any mistakes, typos, or errors in the text. Keep all text exactly as it appears. Only format it as Markdown - do not change, fix, or improve the content itself.

Text:
{text}

Please format it as proper Markdown with:
- Headings (# ## ###) for titles and sections
- Proper paragraph breaks
- Lists formatted correctly (bullet points, numbered lists)
- Preserve any tables if present
- Maintain document structure and hierarchy
- Preserve all original text exactly as written (including any errors or typos)

Return ONLY the formatted Markdown content, no additional explanation."""
        
        # Try current models
        models_to_try = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama3-70b-8192",
            "mixtral-8x7b-32768"
        ]
        
        response = None
        for model_name in models_to_try:
            try:
                _log.info(f"Calling Groq API with model: {model_name} for markdown conversion...")
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a document formatting assistant. Convert text to well-structured Markdown. Do NOT correct mistakes, typos, or errors - only format the text. Keep all original text exactly as it appears."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,  # Lower temperature for more consistent formatting
                    max_tokens=4000
                )
                _log.info(f"Groq API markdown conversion completed with model: {model_name}")
                break
            except Exception as api_error:
                _log.warning(f"Model {model_name} failed: {api_error}")
                continue
        
        if response is None:
            _log.warning("All Groq models failed, using simple markdown format")
            return f"# Document Content\n\n{text}"
        
        markdown_content = response.choices[0].message.content.strip()
        _log.info(f"Groq converted text to markdown ({len(markdown_content)} characters)")
        
        return markdown_content
        
    except Exception as e:
        _log.error(f"Error converting to markdown with Groq: {e}", exc_info=True)
        # Fallback to simple markdown
        return f"# Document Content\n\n{text}"


def parse_google_vision_response(vision_response: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Parse Google Vision API response and format as markdown and JSON.
    Uses Groq API to convert text to properly formatted Markdown.
    
    Args:
        vision_response: Dictionary response from Google Vision API
    
    Returns:
        Tuple of (markdown_text, json_dict)
    """
    try:
        full_text = vision_response.get("full_text", "")
        text_annotations = vision_response.get("text_annotations", [])
        
        if not full_text and not text_annotations:
            raise Exception("No text detected by Google Vision API")
        
        # Send extracted text to Groq API for markdown conversion
        _log.info("Sending extracted text to Groq API for markdown conversion...")
        markdown_content = convert_text_to_markdown_with_groq(full_text)
        
        # Create JSON structure compatible with DocumentProcessingResult
        json_content = {
            "source": "google_vision",
            "parsed_text": full_text,
            "text_count": vision_response.get("text_count", len(text_annotations)),
            "text_annotations": text_annotations[:20],  # Limit to first 20 annotations
            "processing_method": "google_vision_api + groq_markdown_conversion"
        }
        
        return markdown_content, json_content
        
    except Exception as e:
        _log.error(f"Error parsing Google Vision response: {e}", exc_info=True)
        raise


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
    
    def _create_converter(self, use_vlm: bool):
        """Create a document converter for the specified mode (TEMPORARILY DISABLED - using OCR.space)."""
        raise Exception("Docling converters are temporarily disabled. OCR.space API is being used instead.")
        # ORIGINAL DOCLING CODE (TEMPORARILY DISABLED):
        # if use_vlm:
        #     # VLM mode - keep it simple like the original
        #     vlm_options = (
        #         vlm_model_specs.GRANITEDOCLING_MLX
        #         if self.use_mlx_acceleration
        #         else vlm_model_specs.GRANITEDOCLING_TRANSFORMERS
        #     )
        #     
        #     pipeline_options = VlmPipelineOptions(vlm_options=vlm_options)
        #     
        #     # CRITICAL: For VLM, only configure PDF format, nothing else
        #     converter = DocumentConverter(
        #         format_options={
        #             InputFormat.PDF: PdfFormatOption(
        #                 pipeline_cls=VlmPipeline,
        #                 pipeline_options=pipeline_options,
        #             ),
        #         }
        #     )
        #     
        #     _log.debug(f"Created VLM converter with {'MLX' if self.use_mlx_acceleration else 'Transformers'}")
        #     return converter
        # 
        # else:
        #     # Standard mode - configure all formats
        #     format_options = {
        #         InputFormat.PDF: PdfFormatOption(
        #             pipeline_cls=StandardPdfPipeline,
        #             backend=PyPdfiumDocumentBackend,
        #         ),
        #         InputFormat.DOCX: WordFormatOption(pipeline_cls=SimplePipeline),
        #     }
        #     
        #     converter = DocumentConverter(
        #         allowed_formats=[
        #             InputFormat.PDF,
        #             InputFormat.IMAGE,
        #             InputFormat.DOCX,
        #             InputFormat.HTML,
        #             InputFormat.PPTX,
        #             InputFormat.ASCIIDOC,
        #             InputFormat.CSV,
        #             InputFormat.MD,
        #         ],
        #         format_options=format_options,
        #     )
        #     
        #     _log.debug("Created STANDARD converter")
        #     return converter
    
    def _get_converter(self, source: Union[str, Path]):
        """Get appropriate converter based on source and mode (TEMPORARILY DISABLED - using OCR.space)."""
        raise Exception("Docling converters are temporarily disabled. OCR.space API is being used instead.")
        # ORIGINAL DOCLING CODE (TEMPORARILY DISABLED):
        # # For non-AUTO modes, use fixed converter
        # if self.pdf_mode == PdfProcessingMode.STANDARD:
        #     if self._standard_converter is None:
        #         self._standard_converter = self._create_converter(use_vlm=False)
        #     return self._standard_converter
        # 
        # elif self.pdf_mode == PdfProcessingMode.VLM:
        #     if self._vlm_converter is None:
        #         self._vlm_converter = self._create_converter(use_vlm=True)
        #     return self._vlm_converter
        # 
        # # AUTO mode: detect PDF type
        # else:
        #     source_path = Path(source) if not isinstance(source, Path) else source
        #     
        #     # Only detect for local PDF files
        #     if source_path.suffix.lower() == '.pdf' and source_path.exists():
        #         is_readable, detection_info = detect_pdf_readability(source_path)
        #         
        #         if is_readable:
        #             _log.info(f"Auto-detected: Machine-readable PDF - using STANDARD pipeline")
        #             if self._standard_converter is None:
        #                 self._standard_converter = self._create_converter(use_vlm=False)
        #             return self._standard_converter
        #         else:
        #             _log.info(f"Auto-detected: Scanned PDF - using VLM pipeline")
        #             if self._vlm_converter is None:
        #                 self._vlm_converter = self._create_converter(use_vlm=True)
        #             return self._vlm_converter
        #     
        #     # Default to standard for non-PDFs or URLs
        #     _log.debug("Using STANDARD pipeline (not a local PDF)")
        #     if self._standard_converter is None:
        #         self._standard_converter = self._create_converter(use_vlm=False)
        #     return self._standard_converter
    
    def process_document(
        self,
        source: Union[str, Path],
        export_formats: Optional[List[str]] = None,
    ) -> DocumentProcessingResult:
        """
        Process a single document using Google Cloud Vision API.
        
        Process:
        1. Send PDF file to Google Cloud Vision API
        2. If image-based, convert to images and process each page
        3. Extract text and format as markdown and JSON
        """
        if export_formats is None:
            export_formats = ["markdown"]
        
        # Filter to supported export formats
        supported_formats = ["markdown", "json", "yaml"]
        export_formats = [f for f in export_formats if f in supported_formats]
        
        if not export_formats:
            export_formats = ["markdown"]  # Default to markdown
        
        _log.info(f"Processing document with Google Cloud Vision API: {source} (formats: {export_formats})")
        
        # Check if Google Vision is enabled
        if not GOOGLE_CLOUD_VISION_ENABLED:
            raise Exception("Google Cloud Vision is disabled. Enable GOOGLE_CLOUD_VISION_ENABLED in config.")
        
        try:
            source_path = Path(source) if not isinstance(source, Path) else source
            
            # Check if it's a PDF
            if source_path.suffix.lower() != '.pdf':
                raise Exception(f"Currently only PDF files are supported. Got: {source_path.suffix}")
            
            # Determine output filename
            stem = source_path.stem
            
            # Process PDF with Google Cloud Vision
            _log.info(f"Sending PDF file to Google Cloud Vision API: {source_path}")
            vision_response = process_pdf_with_google_vision(source_path)
            
            # Parse Google Vision response (format as markdown/JSON)
            markdown_content, json_content = parse_google_vision_response(vision_response)
            
            output_paths = {}
            
            # Export to requested formats (only what we can generate)
            # Use absolute paths to ensure files can be found later
            if "markdown" in export_formats:
                md_path = self.output_dir / f"{stem}.md"
                md_path_absolute = md_path.resolve()
                with md_path_absolute.open("w", encoding="utf-8") as f:
                    f.write(markdown_content)
                output_paths["markdown"] = str(md_path_absolute)
                _log.info(f"Saved markdown: {md_path_absolute} (absolute path: {output_paths['markdown']})")
            
            if "json" in export_formats:
                json_path = self.output_dir / f"{stem}.json"
                json_path_absolute = json_path.resolve()
                with json_path_absolute.open("w", encoding="utf-8") as f:
                    json.dump(json_content, f, indent=2)
                output_paths["json"] = str(json_path_absolute)
                _log.info(f"Saved JSON: {json_path_absolute} (absolute path: {output_paths['json']})")
            
            if "yaml" in export_formats:
                yaml_path = self.output_dir / f"{stem}.yaml"
                yaml_path_absolute = yaml_path.resolve()
                with yaml_path_absolute.open("w", encoding="utf-8") as f:
                    yaml.safe_dump(json_content, f)
                output_paths["yaml"] = str(yaml_path_absolute)
                _log.info(f"Saved YAML: {yaml_path_absolute} (absolute path: {output_paths['yaml']})")
            
            _log.info(f"Successfully processed document with Google Cloud Vision API: {source}")
            
            return DocumentProcessingResult(
                str(source),
                output_paths,
                markdown_content,
                json_content,
                True,
            )
            
        except Exception as e:
            _log.error(f"Failed to process {source} with Google Vision: {e}", exc_info=True)
            # Return DocumentProcessingResult for error case (consistent interface)
            return DocumentProcessingResult(
                str(source),
                {},  # No output paths on error
                None,  # No markdown on error
                {"error": str(e), "source": "google_vision"},
                False,  # success = False
            )
        
        # ORIGINAL DOCLING CODE (TEMPORARILY DISABLED):
        # try:
        #     # Get appropriate converter (auto-detection happens here)
        #     converter = self._get_converter(source)
        #     
        #     result = converter.convert(source=source)
        #     doc = result.document
        #     
        #     # Determine output filename
        #     if isinstance(source, Path):
        #         stem = source.stem
        #     else:
        #         stem = Path(source).stem if "/" in str(source) else "document"
        #     
        #     output_paths = {}
        #     markdown_content = None
        #     json_content = None
        #     
        #     # Export to requested formats
        #     if "markdown" in export_formats:
        #         md_path = self.output_dir / f"{stem}.md"
        #         markdown_content = doc.export_to_markdown()
        #         with md_path.open("w", encoding="utf-8") as f:
        #             f.write(markdown_content)
        #         output_paths["markdown"] = md_path
        #         _log.info(f"Saved markdown: {md_path}")
        #     
        #     if "json" in export_formats:
        #         json_path = self.output_dir / f"{stem}.json"
        #         with json_path.open("w", encoding="utf-8") as f:
        #             json_content = doc.export_to_dict()
        #             json.dump(json_content, f, indent=2)
        #         output_paths["json"] = json_path
        #         _log.info(f"Saved JSON: {json_path}")
        #     
        #     if "yaml" in export_formats:
        #         yaml_path = self.output_dir / f"{stem}.yaml"
        #         with yaml_path.open("w", encoding="utf-8") as f:
        #             yaml.safe_dump(doc.export_to_dict(), f)
        #         output_paths["yaml"] = yaml_path
        #         _log.info(f"Saved YAML: {yaml_path}")
        #     
        #     return DocumentProcessingResult(
        #         str(source),
        #         output_paths,
        #         markdown_content,
        #         json_content,
        #         True,
        #     )
        # 
        # except Exception as e:
        #     _log.error(f"Failed to process {source}: {e}", exc_info=True)
        #     return {
        #         "source": str(source),
        #         "error": str(e),
        #         "success": False,
        #     }
    
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
        
        # All results should now be DocumentProcessingResult objects
        successful = sum(1 for r in results if isinstance(r, DocumentProcessingResult) and r.success)
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