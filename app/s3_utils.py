import boto3
import os
from datetime import datetime
import io
from PIL import Image
import logging
import traceback
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Handler:
    def __init__(self, bucket_name):
        """Initialize S3 client and bucket name."""
        try:
            self.s3_client = boto3.client('s3')
            self.bucket_name = bucket_name
            logger.info(f"S3Handler initialized with bucket: {bucket_name}")
            
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"Bucket {bucket_name} exists and is accessible")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    logger.warning(f"Bucket {bucket_name} does not exist")
                elif error_code == '403':
                    logger.warning(f"Access to bucket {bucket_name} is forbidden")
                else:
                    logger.warning(f"Error checking bucket {bucket_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def upload_image(self, image_data, original_filename):
        """
        Upload an image to S3 with a folder structure of year/month/day.
        
        Args:
            image_data: The binary image data
            original_filename: Original filename of the uploaded image
            
        Returns:
            S3 URL of the uploaded image
        """
        try:
            # Create folder structure based on current date
            now = datetime.now()
            folder_path = f"{now.year}/{now.month:02d}/{now.day:02d}"
            
            # Generate a unique filename
            file_extension = os.path.splitext(original_filename)[1] or '.jpg'  # Default to .jpg if no extension
            timestamp = now.strftime("%H%M%S")
            safe_filename = ''.join(c for c in original_filename if c.isalnum() or c in '._-')  # Sanitize filename
            filename = f"{timestamp}_{safe_filename}"
            
            # Full S3 key with folder structure
            s3_key = f"{folder_path}/{filename}"
            
            logger.info(f"Uploading image to S3: {s3_key}")
            
            # Upload to S3
            content_type = f"image/{file_extension.lstrip('.') or 'jpeg'}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=image_data,
                ContentType=content_type
            )
            
            logger.info(f"Image uploaded successfully to S3: {s3_key}")
            
            # Generate the S3 URL
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            return {
                "s3_url": s3_url,
                "s3_key": s3_key,
                "bucket": self.bucket_name
            }
        except Exception as e:
            logger.error(f"Failed to upload image to S3: {str(e)}")
            logger.error(traceback.format_exc())
            raise