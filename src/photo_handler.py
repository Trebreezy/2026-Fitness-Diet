"""
Photo handling for the Fitness & Diet Logger.
Processes images and prepares them for upload to Notion.
"""
import base64
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import shutil

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import settings


class PhotoHandler:
    """
    Handles photo processing for the fitness and diet logger.
    - Validates images
    - Extracts metadata (EXIF data, timestamps)
    - Resizes images for optimal storage
    - Prepares images for upload
    """

    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif"}
    MAX_DIMENSION = 2048  # Max width or height
    JPEG_QUALITY = 85

    def __init__(self, upload_dir: Optional[Path] = None):
        """
        Initialize the photo handler.

        Args:
            upload_dir: Directory to store processed photos
        """
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_image(self, image_path: Path) -> Tuple[bool, str]:
        """
        Validate that the file is a supported image.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not image_path.exists():
            return False, f"File not found: {image_path}"

        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {image_path.suffix}. Supported: {self.SUPPORTED_FORMATS}"

        if not HAS_PIL:
            # Without PIL, just check extension
            return True, ""

        try:
            with Image.open(image_path) as img:
                img.verify()
            return True, ""
        except Exception as e:
            return False, f"Invalid image file: {e}"

    def extract_metadata(self, image_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from an image.

        Args:
            image_path: Path to the image

        Returns:
            Dictionary of metadata
        """
        metadata = {
            "filename": image_path.name,
            "size_bytes": image_path.stat().st_size,
            "format": image_path.suffix.lower(),
            "created_time": None,
            "width": None,
            "height": None,
            "camera": None,
            "gps": None,
        }

        if not HAS_PIL:
            return metadata

        try:
            with Image.open(image_path) as img:
                metadata["width"] = img.width
                metadata["height"] = img.height
                metadata["format"] = img.format

                # Extract EXIF data if available
                exif_data = img._getexif()
                if exif_data:
                    exif = {TAGS.get(k, k): v for k, v in exif_data.items()}

                    # Get creation date
                    for date_field in ["DateTimeOriginal", "DateTime", "DateTimeDigitized"]:
                        if date_field in exif:
                            try:
                                dt = datetime.strptime(
                                    exif[date_field], "%Y:%m:%d %H:%M:%S"
                                )
                                metadata["created_time"] = dt.isoformat()
                                break
                            except ValueError:
                                pass

                    # Get camera info
                    make = exif.get("Make", "")
                    model = exif.get("Model", "")
                    if make or model:
                        metadata["camera"] = f"{make} {model}".strip()

        except Exception:
            pass  # Non-critical metadata extraction

        return metadata

    def process_image(
        self,
        image_path: Path,
        max_dimension: Optional[int] = None,
        quality: Optional[int] = None,
    ) -> Path:
        """
        Process an image for upload (resize if needed, optimize).

        Args:
            image_path: Path to the original image
            max_dimension: Maximum width/height (defaults to MAX_DIMENSION)
            quality: JPEG quality (defaults to JPEG_QUALITY)

        Returns:
            Path to the processed image
        """
        max_dimension = max_dimension or self.MAX_DIMENSION
        quality = quality or self.JPEG_QUALITY

        # Generate unique filename
        file_hash = hashlib.md5(
            f"{image_path.name}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{timestamp}_{file_hash}.jpg"
        output_path = self.upload_dir / output_filename

        if not HAS_PIL:
            # Without PIL, just copy the file
            shutil.copy2(image_path, output_path)
            return output_path

        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for JPEG output)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Resize if needed
                if img.width > max_dimension or img.height > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

                # Preserve EXIF orientation
                try:
                    from PIL import ImageOps
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass

                # Save optimized image
                img.save(output_path, "JPEG", quality=quality, optimize=True)

            return output_path

        except Exception as e:
            # If processing fails, just copy the original
            shutil.copy2(image_path, output_path)
            return output_path

    def image_to_base64(self, image_path: Path) -> str:
        """
        Convert an image to base64 string.

        Args:
            image_path: Path to the image

        Returns:
            Base64 encoded string
        """
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def get_data_uri(self, image_path: Path) -> str:
        """
        Get a data URI for an image.

        Args:
            image_path: Path to the image

        Returns:
            Data URI string
        """
        mime_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
        b64 = self.image_to_base64(image_path)
        return f"data:{mime_type};base64,{b64}"

    def cleanup_old_files(self, max_age_days: int = 30) -> int:
        """
        Remove processed files older than the specified age.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of files removed
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=max_age_days)
        removed = 0

        for file_path in self.upload_dir.glob("*"):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff:
                    file_path.unlink()
                    removed += 1

        return removed

    def analyze_food_photo(self, image_path: Path) -> Dict[str, Any]:
        """
        Placeholder for food photo analysis.
        In a production system, this could integrate with a food recognition API.

        Args:
            image_path: Path to the food photo

        Returns:
            Analysis results (placeholder)
        """
        # This is a placeholder - in production, you would:
        # 1. Send to a food recognition API (like Google Vision, AWS Rekognition, etc.)
        # 2. Get estimated nutritional info
        # 3. Return structured data

        return {
            "analyzed": False,
            "message": "Food analysis not implemented. Add your preferred food recognition API.",
            "suggestions": [
                "Consider integrating with Google Cloud Vision API",
                "Or use AWS Rekognition for food detection",
                "Manual entry is always available",
            ],
        }
