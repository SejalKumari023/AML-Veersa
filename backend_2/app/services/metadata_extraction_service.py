"""
Metadata Extraction Service
Extracts EXIF data and image metadata, analyzes for inconsistencies
"""

import io
import logging
from typing import Dict, Any, Optional
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import exifread

logger = logging.getLogger(__name__)


class MetadataExtractionService:
    """Service for extracting and analyzing image metadata"""

    def extract_metadata(self, image_content: bytes) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from an image
        
        Args:
            image_content: Raw image bytes
        
        Returns:
            Dictionary containing all extracted metadata and analysis
        """
        metadata = {
            "image_properties": {},
            "exif_data": {},
            "gps_data": {},
            "analysis": {
                "exif_present": False,
                "metadata_anomalies": [],
                "timestamp_consistent": None,
                "camera_info": {},
                "software_info": {}
            }
        }
        
        try:
            # Extract using PIL
            image = Image.open(io.BytesIO(image_content))
            metadata["image_properties"] = self._extract_image_properties(image)
            
            # Extract EXIF using PIL (built-in)
            exif_data_pil = self._extract_exif_pil(image)
            if exif_data_pil:
                metadata["exif_data"] = exif_data_pil
                metadata["analysis"]["exif_present"] = True
            
            # Extract EXIF using exifread (more detailed)
            exif_data_read = self._extract_exif_exifread(image_content)
            if exif_data_read:
                # Merge with PIL data, exifread data takes precedence for overlaps
                metadata["exif_data"].update(exif_data_read)
            
            # Extract GPS data if present
            if "GPS" in metadata["exif_data"]:
                metadata["gps_data"] = metadata["exif_data"]["GPS"]
            
            # Analyze metadata for inconsistencies
            metadata["analysis"].update(self._analyze_metadata(metadata))
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            metadata["error"] = str(e)
        
        return metadata

    def _extract_image_properties(self, image: Image.Image) -> Dict[str, Any]:
        """Extract basic image properties using PIL"""
        return {
            "format": image.format,
            "mode": image.mode,
            "size": {
                "width": image.size[0],
                "height": image.size[1]
            },
            "has_transparency": image.mode in ('RGBA', 'LA') or 'transparency' in image.info,
            "palette": image.palette is not None if hasattr(image, 'palette') else None,
        }

    def _extract_exif_pil(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """Extract EXIF data using PIL"""
        exif_data = {}
        
        def serialize_value(val):
            """Convert PIL-specific types to JSON-serializable types"""
            from PIL.TiffImagePlugin import IFDRational
            if isinstance(val, IFDRational):
                # Convert IFDRational to float or dict
                try:
                    return float(val)
                except (ZeroDivisionError, ValueError):
                    return {"numerator": val.numerator, "denominator": val.denominator}
            elif isinstance(val, tuple):
                return tuple(serialize_value(v) for v in val)
            elif isinstance(val, list):
                return [serialize_value(v) for v in val]
            elif isinstance(val, bytes):
                return f"<bytes:{len(val)}>"
            elif isinstance(val, dict):
                return {k: serialize_value(v) for k, v in val.items()}
            else:
                return val
        
        if hasattr(image, '_getexif') and image._getexif() is not None:
            exif_dict = image._getexif()
            for tag_id, value in exif_dict.items():
                tag = TAGS.get(tag_id, tag_id)
                # Handle GPSInfo specially before serialization
                if tag == "GPSInfo" and isinstance(value, dict):
                    gps_data = {}
                    for key, val in value.items():
                        gps_tag = GPSTAGS.get(key, key)
                        gps_data[gps_tag] = serialize_value(val)
                    exif_data[tag] = serialize_value(value)
                    exif_data["GPS"] = gps_data
                else:
                    exif_data[tag] = serialize_value(value)
        
        # Also check for other metadata in image.info
        if image.info:
            for key, value in image.info.items():
                if key not in exif_data:
                    exif_data[key] = serialize_value(value)
        
        return exif_data if exif_data else None

    def _extract_exif_exifread(self, image_content: bytes) -> Optional[Dict[str, Any]]:
        """Extract EXIF data using exifread library (more detailed)"""
        exif_data = {}
        
        try:
            tags = exifread.process_file(io.BytesIO(image_content), details=True)
            
            for tag in tags.keys():
                # Skip thumbnail data
                if tag.startswith('JPEGThumbnail') or tag.startswith('TIFFThumbnail'):
                    continue
                
                # Format tag name (remove spaces, make readable)
                tag_name = tag.replace(' ', '_')
                value = str(tags[tag])
                
                # Try to parse numeric values
                try:
                    if '/' in value:
                        # EXIF often uses fractions like "123/456"
                        parts = value.split('/')
                        if len(parts) == 2:
                            num_value = float(parts[0]) / float(parts[1])
                            exif_data[tag_name] = num_value
                        else:
                            exif_data[tag_name] = value
                    elif value.isdigit():
                        exif_data[tag_name] = int(value)
                    else:
                        exif_data[tag_name] = value
                except (ValueError, ZeroDivisionError):
                    exif_data[tag_name] = value
            
            return exif_data if exif_data else None
            
        except Exception as e:
            logger.warning(f"Error extracting EXIF with exifread: {e}")
            return None

    def _analyze_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metadata for inconsistencies and red flags"""
        analysis = {
            "metadata_anomalies": [],
            "timestamp_consistent": None,
            "camera_info": {},
            "software_info": {},
            "red_flags": []
        }
        
        exif_data = metadata.get("exif_data", {})
        
        # Extract camera information
        if "Make" in exif_data:
            analysis["camera_info"]["make"] = exif_data["Make"]
        if "Model" in exif_data:
            analysis["camera_info"]["model"] = exif_data["Model"]
        if "EXIF_Make" in exif_data:
            analysis["camera_info"]["make"] = exif_data["EXIF_Make"]
        if "EXIF_Model" in exif_data:
            analysis["camera_info"]["model"] = exif_data["EXIF_Model"]
        
        # Extract software information
        if "Software" in exif_data:
            analysis["software_info"]["software"] = exif_data["Software"]
        if "EXIF_Software" in exif_data:
            analysis["software_info"]["software"] = exif_data["EXIF_Software"]
        
        # Check for missing EXIF data (potential red flag)
        if not metadata.get("analysis", {}).get("exif_present", False):
            analysis["red_flags"].append("No EXIF data found - image may be processed or stripped")
            analysis["metadata_anomalies"].append("missing_exif")
        
        # Check for suspicious software
        software = analysis["software_info"].get("software", "").lower()
        suspicious_software = ["photoshop", "gimp", "gimp-", "paint.net", "fotor", "photoscape"]
        if any(sus in software for sus in suspicious_software):
            analysis["red_flags"].append(f"Image edited with: {analysis['software_info'].get('software', 'Unknown')}")
            analysis["metadata_anomalies"].append("edited_software_detected")
        
        # Check for date/time consistency
        dates = []
        if "DateTime" in exif_data:
            dates.append(exif_data["DateTime"])
        if "EXIF_DateTimeOriginal" in exif_data:
            dates.append(exif_data["EXIF_DateTimeOriginal"])
        if "EXIF_DateTimeDigitized" in exif_data:
            dates.append(exif_data["EXIF_DateTimeDigitized"])
        
        if len(dates) > 1:
            # Check if dates are consistent
            unique_dates = set(dates)
            analysis["timestamp_consistent"] = len(unique_dates) == 1
            if not analysis["timestamp_consistent"]:
                analysis["red_flags"].append("Inconsistent timestamps in EXIF data")
                analysis["metadata_anomalies"].append("timestamp_inconsistency")
        
        # Check for missing camera info when EXIF is present
        if metadata.get("analysis", {}).get("exif_present") and not analysis["camera_info"]:
            analysis["red_flags"].append("EXIF present but no camera information found")
            analysis["metadata_anomalies"].append("missing_camera_info")
        
        # Check for unusual image dimensions or format
        img_props = metadata.get("image_properties", {})
        size = img_props.get("size", {})
        width = size.get("width", 0)
        height = size.get("height", 0)
        
        # Flag very large images (might be AI-generated or heavily processed)
        if width > 10000 or height > 10000:
            analysis["metadata_anomalies"].append("unusual_dimensions")
        
        return analysis

    def get_camera_summary(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Get a human-readable camera summary"""
        camera_info = metadata.get("analysis", {}).get("camera_info", {})
        make = camera_info.get("make")
        model = camera_info.get("model")
        
        if make or model:
            return f"{make or 'Unknown'} {model or ''}".strip()
        return None


# Singleton instance
_metadata_extraction_service: Optional[MetadataExtractionService] = None


def get_metadata_extraction_service() -> MetadataExtractionService:
    """Get or create the metadata extraction service singleton"""
    global _metadata_extraction_service
    if _metadata_extraction_service is None:
        _metadata_extraction_service = MetadataExtractionService()
    return _metadata_extraction_service

