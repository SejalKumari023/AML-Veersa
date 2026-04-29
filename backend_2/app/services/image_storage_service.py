"""
Image Storage Service
Handles saving and retrieving image files from disk storage
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple
from app.config import UPLOAD_DIRECTORY

logger = logging.getLogger(__name__)


class ImageStorageService:
    """Service for managing image file storage on disk"""

    def __init__(self, base_directory: Optional[str] = None):
        """
        Initialize the image storage service
        
        Args:
            base_directory: Base directory for uploads (defaults to config value)
        """
        self.base_directory = Path(base_directory or UPLOAD_DIRECTORY)
        self.images_directory = self.base_directory / "images"
        self._ensure_directories_exist()

    def _ensure_directories_exist(self):
        """Create necessary directories if they don't exist"""
        try:
            self.images_directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Image storage directory ready: {self.images_directory}")
        except Exception as e:
            logger.error(f"Failed to create image storage directory: {e}")
            raise

    def save_image(self, image_content: bytes, image_id: str, file_extension: str) -> str:
        """
        Save an image to disk
        
        Args:
            image_content: Raw image bytes
            image_id: Unique identifier for the image (from database)
            file_extension: File extension (e.g., '.jpg', '.png')
        
        Returns:
            str: Relative file path where image was saved
        """
        try:
            # Generate filename: {image_id}{extension}
            filename = f"{image_id}{file_extension}"
            file_path = self.images_directory / filename
            
            # Write image to disk
            with open(file_path, 'wb') as f:
                f.write(image_content)
            
            relative_path = str(file_path.relative_to(self.base_directory))
            logger.info(f"Image saved: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Failed to save image {image_id}: {e}")
            raise

    def get_image_path(self, image_id: str, file_extension: str) -> Optional[Path]:
        """
        Get the file path for an image
        
        Args:
            image_id: Unique identifier for the image
            file_extension: File extension
        
        Returns:
            Path object if file exists, None otherwise
        """
        filename = f"{image_id}{file_extension}"
        file_path = self.images_directory / filename
        
        if file_path.exists():
            return file_path
        return None

    def read_image(self, image_id: str, file_extension: str) -> Optional[bytes]:
        """
        Read an image file from disk
        
        Args:
            image_id: Unique identifier for the image
            file_extension: File extension
        
        Returns:
            Image bytes if file exists, None otherwise
        """
        file_path = self.get_image_path(image_id, file_extension)
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read image {image_id}: {e}")
                return None
        return None

    def delete_image(self, image_id: str, file_extension: str) -> bool:
        """
        Delete an image file from disk
        
        Args:
            image_id: Unique identifier for the image
            file_extension: File extension
        
        Returns:
            True if deleted successfully, False otherwise
        """
        file_path = self.get_image_path(image_id, file_extension)
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Image deleted: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete image {image_id}: {e}")
                return False
        return False

    def get_image_hash(self, image_content: bytes) -> str:
        """
        Generate SHA-256 hash of image content for verification
        
        Args:
            image_content: Raw image bytes
        
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(image_content).hexdigest()


# Singleton instance
_image_storage_service: Optional[ImageStorageService] = None


def get_image_storage_service() -> ImageStorageService:
    """Get or create the image storage service singleton"""
    global _image_storage_service
    if _image_storage_service is None:
        _image_storage_service = ImageStorageService()
    return _image_storage_service

