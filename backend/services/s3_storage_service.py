import logging
from typing import Optional
from datetime import datetime
from uuid import UUID

from core.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class S3StorageService:
    def __init__(self):
        self.bucket_name = "blog_content"
    
    async def store_blog_content(self, blog_id: UUID, content: str, project_name: str) -> str:
        """Store blog content in S3 bucket and return the storage key"""
        try:
            # Create a unique storage key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            storage_key = f"projects/{project_name}/{blog_id}_{timestamp}.txt"
            
            # Upload content to Supabase storage
            response = supabase_client.storage.from_(self.bucket_name).upload(
                path=storage_key,
                file=content.encode('utf-8'),
                file_options={"content-type": "text/plain"}
            )
            
            if response:
                logger.info(f"Successfully stored blog content: {storage_key}")
                return storage_key
            else:
                raise Exception("Failed to upload content to storage")
                
        except Exception as e:
            logger.error(f"Error storing blog content: {e}")
            raise
    
    async def retrieve_blog_content(self, storage_key: str) -> Optional[str]:
        """Retrieve blog content from S3 bucket"""
        try:
            # Download content from Supabase storage
            response = supabase_client.storage.from_(self.bucket_name).download(path=storage_key)
            
            if response:
                content = response.decode('utf-8')
                logger.info(f"Successfully retrieved blog content: {storage_key}")
                return content
            else:
                logger.warning(f"No content found for storage key: {storage_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving blog content: {e}")
            return None
    
    async def delete_blog_content(self, storage_key: str) -> bool:
        """Delete blog content from S3 bucket"""
        try:
            # Delete content from Supabase storage
            response = supabase_client.storage.from_(self.bucket_name).remove([storage_key])
            
            if response:
                logger.info(f"Successfully deleted blog content: {storage_key}")
                return True
            else:
                logger.warning(f"Failed to delete blog content: {storage_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting blog content: {e}")
            return False
    
    async def update_blog_content(self, blog_id: UUID, new_content: str, project_name: str, old_storage_key: Optional[str] = None) -> str:
        """Update blog content in S3 bucket"""
        try:
            # Delete old content if it exists
            if old_storage_key:
                await self.delete_blog_content(old_storage_key)
            
            # Store new content
            new_storage_key = await self.store_blog_content(blog_id, new_content, project_name)
            
            logger.info(f"Successfully updated blog content: {new_storage_key}")
            return new_storage_key
            
        except Exception as e:
            logger.error(f"Error updating blog content: {e}")
            raise
    
    def get_public_url(self, storage_key: str) -> str:
        """Get public URL for blog content"""
        try:
            # Get public URL from Supabase storage
            response = supabase_client.storage.from_(self.bucket_name).get_public_url(path=storage_key)
            return response
        except Exception as e:
            logger.error(f"Error getting public URL: {e}")
            return ""
    
    async def ensure_bucket_exists(self) -> bool:
        """Ensure the blog_content bucket exists in Supabase storage"""
        try:
            # List buckets to check if blog_content exists
            buckets = supabase_client.storage.list_buckets()
            
            bucket_names = [bucket.name for bucket in buckets]
            
            if self.bucket_name not in bucket_names:
                # Create the bucket if it doesn't exist
                response = supabase_client.storage.create_bucket(
                    name=self.bucket_name,
                    public=True,  # Make it public for easy access
                    file_size_limit=52428800,  # 50MB limit
                    allowed_mime_types=["text/plain", "text/html"]
                )
                
                if response:
                    logger.info(f"Created storage bucket: {self.bucket_name}")
                    return True
                else:
                    logger.error(f"Failed to create storage bucket: {self.bucket_name}")
                    return False
            else:
                logger.info(f"Storage bucket already exists: {self.bucket_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            return False
