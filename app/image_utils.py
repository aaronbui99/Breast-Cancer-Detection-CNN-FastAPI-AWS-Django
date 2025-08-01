"""
Image processing utilities with enhanced error handling and debugging
"""

from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def process_uploaded_image(file_contents: bytes, filename: str = "unknown") -> Image.Image:
    """
    Process uploaded image data with comprehensive error handling and debugging
    
    Args:
        file_contents: Raw bytes from uploaded file
        filename: Original filename for debugging
        
    Returns:
        PIL Image object converted to RGB
        
    Raises:
        ValueError: If image cannot be processed
    """
    try:
        # Log basic file information
        logger.info(f"Processing uploaded image: {filename}")
        logger.info(f"File size: {len(file_contents)} bytes")
        
        # Check if file is empty
        if len(file_contents) == 0:
            raise ValueError("Empty file received")
            
        # Log first few bytes for debugging (safe for logging)
        first_bytes = file_contents[:20] if len(file_contents) >= 20 else file_contents
        logger.info(f"First 20 bytes: {first_bytes}")
        
        # Check file signatures to identify format
        file_signatures = {
            'PNG': b'\x89PNG\r\n\x1a\n',
            'JPEG': b'\xff\xd8\xff',
            'GIF87a': b'GIF87a',
            'GIF89a': b'GIF89a', 
            'BMP': b'BM',
            'WEBP': b'RIFF'
        }
        
        detected_format = None
        for format_name, signature in file_signatures.items():
            if file_contents.startswith(signature):
                detected_format = format_name
                break
                
        logger.info(f"Detected image format: {detected_format or 'Unknown'}")
        
        if not detected_format:
            logger.warning("Unknown image format - attempting to process anyway")
            
        # Multiple attempts to open the image with different strategies
        image = None
        attempts = [
            # Strategy 1: Direct BytesIO approach
            lambda: _attempt_image_open_direct(file_contents),
            # Strategy 2: Reset stream position
            lambda: _attempt_image_open_with_reset(file_contents),
            # Strategy 3: Copy data to new BytesIO
            lambda: _attempt_image_open_copy(file_contents),
        ]
        
        last_error = None
        for i, attempt_func in enumerate(attempts, 1):
            try:
                logger.info(f"Attempting image open strategy {i}/3")
                image = attempt_func()
                logger.info(f"Success with strategy {i}")
                break
            except Exception as attempt_error:
                logger.warning(f"Strategy {i} failed: {attempt_error}")
                last_error = attempt_error
                continue
                
        if image is None:
            logger.error(f"All image opening strategies failed. Last error: {last_error}")
            logger.error(f"Raw data sample (first 50 bytes): {file_contents[:50]}")
            raise ValueError(f"Cannot open image file after {len(attempts)} attempts. Last error: {last_error}")
            
        # Convert to RGB mode
        if image.mode != 'RGB':
            logger.info(f"Converting from {image.mode} to RGB")
            image = image.convert('RGB')
        else:
            logger.info("Image already in RGB mode")
            
        # Final validation - try to access pixel data
        try:
            width, height = image.size
            # Try to get a pixel to ensure image data is accessible
            pixel = image.getpixel((0, 0))
            logger.info(f"Image processing successful: {width}x{height}, sample pixel: {pixel}")
            
        except Exception as pixel_error:
            logger.error(f"Cannot access image pixel data: {pixel_error}")
            raise ValueError(f"Image data appears corrupted: {pixel_error}")
            
        return image
            
    except ValueError:
        # Re-raise ValueError as-is
        raise
    except Exception as unexpected_error:
        logger.error(f"Unexpected error processing image: {unexpected_error}")
        raise ValueError(f"Unexpected image processing error: {unexpected_error}")

def _attempt_image_open_direct(file_contents: bytes) -> Image.Image:
    """Attempt 1: Direct BytesIO approach"""
    image_stream = io.BytesIO(file_contents)
    image = Image.open(image_stream)
    # Load the image to ensure it's valid
    image.load()
    return image

def _attempt_image_open_with_reset(file_contents: bytes) -> Image.Image:
    """Attempt 2: BytesIO with explicit reset"""
    image_stream = io.BytesIO(file_contents)
    image_stream.seek(0)  # Ensure we're at the beginning
    image = Image.open(image_stream)
    image.load()
    return image

def _attempt_image_open_copy(file_contents: bytes) -> Image.Image:
    """Attempt 3: Copy to new BytesIO stream"""
    # Create a fresh copy of the data
    image_data = bytes(file_contents)  # Make a copy
    image_stream = io.BytesIO(image_data)
    image = Image.open(image_stream)
    image.load()
    return image

def validate_image_for_model(image: Image.Image, target_size: tuple = (64, 64)) -> bool:
    """
    Validate that an image is suitable for model processing
    
    Args:
        image: PIL Image object
        target_size: Expected target size for model input
        
    Returns:
        True if image is valid for model processing
        
    Raises:
        ValueError: If image is not suitable for processing
    """
    try:
        # Check image mode
        if image.mode != 'RGB':
            raise ValueError(f"Image must be in RGB mode, got {image.mode}")
            
        # Check image size
        width, height = image.size
        if width < 1 or height < 1:
            raise ValueError(f"Invalid image dimensions: {width}x{height}")
            
        # Check if image can be resized to target size
        try:
            test_resize = image.resize(target_size)
            logger.info(f"Image validation successful: can resize from {image.size} to {target_size}")
            return True
            
        except Exception as resize_error:
            raise ValueError(f"Cannot resize image to {target_size}: {resize_error}")
            
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Image validation failed: {e}")