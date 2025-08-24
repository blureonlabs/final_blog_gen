import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import json

logger = logging.getLogger(__name__)

class S3StorageService:
    def __init__(self):
        # S3 configuration for Supabase S3-compatible endpoint
        self.endpoint_url = "https://kjijwycmwjxqurdlnalo.storage.supabase.co/storage/v1/s3"
        self.region_name = "ap-south-1"
        self.access_key_id = "119a93eec5d176f37095b7d657ab1d37"
        self.secret_access_key = "74a0bc91a799586fa3aa66d52e37e12dba018ec092e2b9eb261f7a88872975be"
        self.bucket_name = "blog-content"
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                region_name=self.region_name,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key
            )
            logger.info(f"✅ S3 client initialized successfully for endpoint: {self.endpoint_url}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def store_blog_content(self, storage_path: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store blog content in S3 bucket and return result"""
        try:
            if not self.s3_client:
                raise Exception("S3 client not initialized")
            
            # Convert to JSON
            json_content = json.dumps(content_data, indent=2, ensure_ascii=False)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_path,
                Body=json_content.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'blog_id': content_data.get('project_id', 'unknown'),
                    'project_name': content_data.get('project_id', 'unknown'),
                    'timestamp': content_data.get('created_at', datetime.now().isoformat())
                }
            )
            
            logger.info(f"✅ Successfully stored blog content in S3: {storage_path}")
            return {"success": True, "storage_path": storage_path}
                
        except Exception as e:
            logger.error(f"❌ Error storing blog content in S3: {e}")
            return {"success": False, "error": str(e)}
    
    def retrieve_blog_content(self, storage_path: str) -> Optional[Dict[str, Any]]:
        """Retrieve blog content from S3 bucket"""
        try:
            if not self.s3_client:
                raise Exception("S3 client not initialized")
            
            # Download content from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            
            if response:
                content = response['Body'].read().decode('utf-8')
                content_data = json.loads(content)
                logger.info(f"✅ Successfully retrieved blog content from S3: {storage_path}")
                return content_data
            else:
                logger.warning(f"⚠️ No content found for storage path: {storage_path}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error retrieving blog content from S3: {e}")
            return None
    
    def delete_blog_content(self, storage_path: str) -> bool:
        """Delete blog content from S3 bucket"""
        try:
            if not self.s3_client:
                raise Exception("S3 client not initialized")
            
            # Delete content from S3
            response = self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            
            if response:
                logger.info(f"✅ Successfully deleted blog content from S3: {storage_path}")
                return True
            else:
                logger.warning(f"⚠️ Failed to delete blog content from S3: {storage_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting blog content from S3: {e}")
            return False
    
    def update_blog_content(self, storage_path: str, new_content_data: Dict[str, Any], old_storage_path: Optional[str] = None) -> Dict[str, Any]:
        """Update blog content in S3 bucket"""
        try:
            # Delete old content if it exists
            if old_storage_path:
                self.delete_blog_content(old_storage_path)
            
            # Store new content
            result = self.store_blog_content(storage_path, new_content_data)
            
            if result.get("success"):
                logger.info(f"✅ Successfully updated blog content in S3: {storage_path}")
                return result
            else:
                logger.error(f"❌ Failed to update blog content in S3: {result.get('error')}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Error updating blog content in S3: {e}")
            return {"success": False, "error": str(e)}
    
    def get_public_url(self, storage_key: str) -> str:
        """Get public URL for blog content"""
        try:
            # Construct public URL for Supabase S3 endpoint
            public_url = f"{self.endpoint_url}/{self.bucket_name}/{storage_key}"
            return public_url
        except Exception as e:
            logger.error(f"❌ Error getting public URL: {e}")
            return ""
    
    def ensure_bucket_exists(self) -> bool:
        """Ensure the blog-content bucket exists in S3"""
        try:
            if not self.s3_client:
                raise Exception("S3 client not initialized")
            
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"✅ S3 bucket already exists: {self.bucket_name}")
                return True
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    # Bucket doesn't exist, create it
                    logger.info(f"📦 Creating S3 bucket: {self.bucket_name}")
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={
                            'LocationConstraint': self.region_name
                        }
                    )
                    logger.info(f"✅ Successfully created S3 bucket: {self.bucket_name}")
                    return True
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"❌ Error ensuring bucket exists: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test S3 connection and bucket access"""
        try:
            if not self.s3_client:
                return False
            
            # Try to list objects in bucket (this will test the connection)
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=1
            )
            
            logger.info(f"✅ S3 connection test successful. Bucket: {self.bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ S3 connection test failed: {e}")
            return False
    
    def get_bucket_info(self) -> Dict[str, Any]:
        """Get information about the S3 bucket"""
        try:
            if not self.s3_client:
                return {"error": "S3 client not initialized"}
            
            # Get bucket location
            location = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            
            # Get bucket versioning
            try:
                versioning = self.s3_client.get_bucket_versioning(Bucket=self.bucket_name)
            except:
                versioning = {"Status": "NotEnabled"}
            
            bucket_info = {
                "bucket_name": self.bucket_name,
                "endpoint_url": self.endpoint_url,
                "region": location.get('LocationConstraint', 'us-east-1'),
                "versioning": versioning.get('Status', 'NotEnabled'),
                "connection_status": "Connected"
            }
            
            return bucket_info
            
        except Exception as e:
            return {
                "error": str(e),
                "connection_status": "Failed"
            }
