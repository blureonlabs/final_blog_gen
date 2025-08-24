import asyncio
import logging
import hashlib
import json
from typing import List, Dict, Any
from datetime import datetime
import openai
import google.generativeai as genai
from core.config import settings
from core.supabase_client import supabase_client
from models.blog import BlogCreate, BlogStatus
from services.s3_storage_service import S3StorageService

logger = logging.getLogger(__name__)

class BlogGenerationService:
    def __init__(self):
        self.openai_client = None
        self.gemini_client = None
        self.s3_storage = S3StorageService()
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize OpenAI and Gemini clients - now using project-specific keys"""
        try:
            # Don't initialize global clients - we'll use project-specific keys
            logger.info("✅ BlogGenerationService initialized - will use project-specific API keys")
            self.openai_client = None  # Will be created per-request with project API key
            self.gemini_client = None  # Will be created per-request with project API key
        except Exception as e:
            logger.error(f"❌ Failed to initialize BlogGenerationService: {e}")
    
    async def generate_blog_content(
        self, 
        project_description: str, 
        blog_number: int, 
        ai_model: str = "openai",
        project_api_keys: dict = None
    ) -> Dict[str, Any]:
        """Generate blog content using specified AI model"""
        try:
            logger.info(f"🔍 Starting blog content generation for blog {blog_number}")
            logger.info(f"🔍 AI model: {ai_model}")
            logger.info(f"🔍 Project API keys: {project_api_keys}")
            logger.info(f"🔍 Project description: {project_description}")
            
            # Use project API keys - no fallback to global settings
            if ai_model == "openai":
                logger.info(f"🔍 Using OpenAI model")
                if project_api_keys and project_api_keys.get("openai"):
                    logger.info(f"✅ Using project-specific OpenAI key")
                    # Use project-specific OpenAI key
                    return self._generate_with_openai(project_description, blog_number, project_api_keys["openai"])
                else:
                    logger.error(f"❌ No OpenAI API key found in project")
                    raise ValueError("OpenAI API key not configured for this project")
            elif ai_model == "gemini":
                logger.info(f"🔍 Using Gemini model")
                if project_api_keys and project_api_keys.get("gemini"):
                    logger.info(f"✅ Using project-specific Gemini key")
                    # Use project-specific Gemini key
                    return self._generate_with_gemini(project_description, blog_number, project_api_keys["gemini"])
                else:
                    logger.error(f"❌ No Gemini API key found in project")
                    raise ValueError("Gemini API key not configured for this project")
            else:
                logger.error(f"❌ Unsupported AI model: {ai_model}")
                raise ValueError(f"AI model '{ai_model}' not supported")
        except Exception as e:
            logger.error(f"❌ Failed to generate blog content: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def _generate_with_openai(self, project_description: str, blog_number: int, api_key: str) -> Dict[str, Any]:
        """Generate blog content using OpenAI with project-specific API key"""
        try:
            logger.info(f"🔍 Starting OpenAI generation for blog {blog_number}")
            logger.info(f"🔍 API key provided: {bool(api_key)}")
            logger.info(f"🔍 Project description: {project_description}")
            
            # Always require API key - no fallback to global client
            if not api_key:
                logger.error(f"❌ No OpenAI API key provided")
                raise ValueError("OpenAI API key is required")
            
            logger.info(f"✅ Using project-specific OpenAI API key")
            import openai
            openai.api_key = api_key
            
            prompt = f"""
            Create a comprehensive blog post about: {project_description}
            
            This is blog #{blog_number} in a series. Make it unique and engaging.
            
            Requirements:
            - Write in a professional, informative tone
            - Include a compelling title
            - Structure with clear headings and subheadings
            - Provide practical insights and actionable advice
            - Aim for 800-1200 words
            - Include relevant examples and case studies
            
            Format the response as:
            TITLE: [Your blog title here]
            CONTENT: [Your blog content here with proper markdown formatting]
            """
            
            logger.info(f"📝 Sending prompt to OpenAI: {prompt[:100]}...")
            
            # Use the older OpenAI API syntax for Python 3.8 compatibility
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            logger.info(f"✅ OpenAI response received")
            
            content = response.choices[0].message.content
            
            logger.info(f"📝 Raw OpenAI response: {content[:200]}...")
            
            # Extract title and content
            title = self._extract_title_from_openai_response(content)
            blog_content = self._extract_content_from_openai_response(content)
            
            logger.info(f"✅ Extracted title: {title}")
            logger.info(f"✅ Extracted content length: {len(blog_content)} characters")
            
            return {
                "title": title,
                "content": blog_content,
                "word_count": len(blog_content.split()),
                "ai_model": "openai",
                "prompt": prompt
            }
            
        except Exception as e:
            logger.error(f"❌ OpenAI generation failed: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def _generate_with_gemini(self, project_description: str, blog_number: int, api_key: str) -> Dict[str, Any]:
        """Generate blog content using Gemini with project-specific API key"""
        try:
            logger.info(f"🔍 Starting Gemini generation for blog {blog_number}")
            logger.info(f"🔍 API key provided: {bool(api_key)}")
            logger.info(f"🔍 Project description: {project_description}")
            
            # Always require API key - no fallback to global client
            if not api_key:
                logger.error(f"❌ No Gemini API key provided")
                raise ValueError("Gemini API key is required")
            
            logger.info(f"✅ Using project-specific Gemini API key")
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini with provided key: {e}")
                raise ValueError(f"Invalid Gemini API key: {e}")
            
            prompt = f"""
            Create a comprehensive blog post about: {project_description}
            
            This is blog #{blog_number} in a series. Make it unique and engaging.
            
            Requirements:
            - Write in a professional, informative tone
            - Include a compelling title
            - Structure with clear headings and subheadings
            - Provide practical insights and actionable advice
            - Aim for 800-1200 words
            - Include relevant examples and case studies
            
            Format the response as:
            TITLE: [Your blog title here]
            CONTENT: [Your blog content here with proper markdown formatting]
            """
            
            logger.info(f"📝 Sending prompt to Gemini: {prompt[:100]}...")
            
            # Use synchronous call for Python 3.8 compatibility
            response = model.generate_content(prompt)
            
            logger.info(f"✅ Gemini response received")
            
            content = response.text
            
            logger.info(f"📝 Raw Gemini response: {content[:200]}...")
            
            # Extract title and content
            title = self._extract_title_from_gemini_response(content)
            blog_content = self._extract_content_from_gemini_response(content)
            
            logger.info(f"✅ Extracted title: {title}")
            logger.info(f"✅ Extracted content length: {len(blog_content)} characters")
            
            return {
                "title": title,
                "content": blog_content,
                "word_count": len(blog_content.split()),
                "ai_model": "gemini",
                "prompt": prompt
            }
            
        except Exception as e:
            logger.error(f"❌ Gemini generation failed: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def _extract_title_from_openai_response(self, response: str) -> str:
        """Extract title from OpenAI response"""
        try:
            if "TITLE:" in response:
                title_start = response.find("TITLE:") + 6
                title_end = response.find("\n", title_start)
                if title_end == -1:
                    title_end = len(response)
                title = response[title_start:title_end].strip()
                return title if title else f"Blog Post - {datetime.now().strftime('%Y-%m-%d')}"
            else:
                # Fallback: use first line as title
                lines = response.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('#'):
                        return line.strip()[:100]  # Limit title length
                return f"Blog Post - {datetime.now().strftime('%Y-%m-%d')}"
        except Exception as e:
            logger.error(f"❌ Failed to extract title: {e}")
            return f"Blog Post - {datetime.now().strftime('%Y-%m-%d')}"
    
    def _extract_content_from_openai_response(self, response: str) -> str:
        """Extract content from OpenAI response"""
        try:
            if "CONTENT:" in response:
                content_start = response.find("CONTENT:") + 8
                return response[content_start:].strip()
            else:
                # Fallback: remove title line and return rest
                lines = response.strip().split('\n')
                if lines and "TITLE:" in lines[0]:
                    return '\n'.join(lines[1:]).strip()
                return response.strip()
        except Exception as e:
            logger.error(f"❌ Failed to extract content: {e}")
            return response.strip()
    
    def _extract_title_from_gemini_response(self, response: str) -> str:
        """Extract title from Gemini response"""
        return self._extract_title_from_openai_response(response)
    
    def _extract_content_from_gemini_response(self, response: str) -> str:
        """Extract content from Gemini response"""
        return self._extract_content_from_openai_response(response)
    
    async def generate_blogs_for_project(
        self,
        project_id: str,
        project_description: str,
        num_blogs: int,
        ai_model: str = "openai",
        project_api_keys: dict = None
    ) -> List[Dict[str, Any]]:
        """Generate multiple blogs for a project"""
        generated_blogs = []
        
        try:
            logger.info(f"🚀 Starting blog generation for project {project_id}: {num_blogs} blogs")
            logger.info(f"🔍 AI model: {ai_model}")
            logger.info(f"🔍 Project API keys: {project_api_keys}")
            logger.info(f"🔍 Project description: {project_description}")
            
            for blog_number in range(1, num_blogs + 1):
                try:
                    logger.info(f"📝 Generating blog {blog_number}/{num_blogs}")
                    
                    # Generate blog content using project API keys if available
                    blog_data = await self.generate_blog_content(
                        project_description, 
                        blog_number, 
                        ai_model,
                        project_api_keys
                    )
                    
                    logger.info(f"✅ Blog content generated: {blog_data['title']}")
                    
                    # Create blog record with generating status
                    blog_create = BlogCreate(
                        project_id=project_id,
                        title=blog_data["title"],
                        status=BlogStatus.GENERATING,  # Start with generating status
                        word_count=blog_data["word_count"],
                        prompt=blog_data["prompt"],
                        ai_model=blog_data["ai_model"]
                    )
                    
                    logger.info(f"📝 Storing blog in database: {blog_data['title']}")
                    
                    # Store in database with content
                    blog_record = self._store_blog(blog_create, blog_data["content"])
                    
                    logger.info(f"✅ Blog stored in database: {blog_record['id']}")
                    
                    # Update blog status to ready after successful storage
                    supabase_client.table("blogs").update({
                        "status": "ready",
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", blog_record["id"]).execute()
                    
                    # Update the blog record status
                    blog_record["status"] = "ready"
                    
                    generated_blogs.append(blog_record)
                    logger.info(f"✅ Blog {blog_number} generated successfully: {blog_data['title']}")
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate blog {blog_number}: {e}")
                    logger.error(f"❌ Error type: {type(e)}")
                    import traceback
                    logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                    # Continue with next blog
                    continue
            
            logger.info(f"🎉 Blog generation completed: {len(generated_blogs)}/{num_blogs} blogs generated")
            return generated_blogs
            
        except Exception as e:
            logger.error(f"❌ Blog generation service failed: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def _store_blog(self, blog_create: BlogCreate, content: str) -> dict:
        """Store blog content and metadata"""
        try:
            logger.info("🔍 Starting blog storage process")
            logger.info(f"🔍 Blog title: {blog_create.title}")
            logger.info(f"🔍 Project ID: {blog_create.project_id}")
            logger.info(f"🔍 Content length: {len(content)} characters")
            
            # Generate storage path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            storage_path = f"blogs/{blog_create.project_id}/{timestamp}_{content_hash}.json"
            
            logger.info(f"📁 Generated storage path: {storage_path}")
            
            # Try S3 storage first
            try:
                logger.info("📦 Using S3 storage for blog content")
                self.s3_storage.ensure_bucket_exists()
                
                # Create blog content data for S3
                blog_content_data = {
                    "title": blog_create.title,
                    "content": content,
                    "project_id": str(blog_create.project_id),
                    "created_at": datetime.now().isoformat(),
                    "word_count": len(content.split()),
                    "content_size_bytes": len(content.encode('utf-8')),
                    "content_hash": content_hash
                }
                
                # Store in S3
                s3_result = self.s3_storage.store_blog_content(storage_path, blog_content_data)
                
                if s3_result.get("success"):
                    logger.info("✅ Blog content stored in S3 successfully")
                    storage_bucket = "s3-blog-content"
                else:
                    raise Exception(f"S3 storage failed: {s3_result.get('error')}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to store content in S3: {str(e)}, using database fallback")
                storage_bucket = "database"
                storage_path = f"database_fallback_{timestamp}"
            
            # Prepare blog metadata for database
            blog_metadata = {
                "project_id": str(blog_create.project_id),  # Convert UUID to string
                "title": blog_create.title,
                "status": blog_create.status.value if hasattr(blog_create.status, 'value') else str(blog_create.status),
                "word_count": len(content.split()),
                "prompt": blog_create.prompt,
                "ai_model": blog_create.ai_model,
                "storage_path": storage_path,
                "storage_bucket": storage_bucket,
                "content_size_bytes": len(content.encode('utf-8')),
                "content_hash": content_hash,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Add content field for database fallback
            if storage_bucket == "database":
                blog_metadata["content"] = content
                logger.info("📝 Using database fallback for content storage")
            
            logger.info(f"📝 Blog metadata prepared: {blog_metadata}")
            
            # Insert blog metadata into database
            try:
                logger.info("💾 Inserting blog metadata into database...")
                result = supabase_client.table("blogs").insert(blog_metadata).execute()
                
                if result.data:
                    blog_record = result.data[0]
                    logger.info(f"✅ Blog metadata stored in database: {blog_record.get('id')}")
                    return blog_record
                else:
                    raise Exception("No data returned from database insert")
                    
            except Exception as db_error:
                logger.error(f"❌ Database insert failed: {str(db_error)}")
                
                # Try simplified insert with content field
                try:
                    logger.info("📝 Trying simplified insert with content field")
                    simplified_metadata = {
                        "project_id": str(blog_create.project_id),  # Convert UUID to string
                        "title": blog_create.title,
                        "status": "generating",
                        "word_count": len(content.split()),
                        "prompt": blog_create.prompt,
                        "ai_model": blog_create.ai_model,
                        "storage_path": storage_path,
                        "storage_bucket": storage_bucket,
                        "content": content,  # Always include content for fallback
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    result = supabase_client.table("blogs").insert(simplified_metadata).execute()
                    
                    if result.data:
                        blog_record = result.data[0]
                        logger.info(f"✅ Blog stored with simplified metadata: {blog_record.get('id')}")
                        return blog_record
                    else:
                        raise Exception("No data returned from simplified insert")
                        
                except Exception as simplified_error:
                    logger.error(f"❌ Failed to store blog: {str(simplified_error)}")
                    logger.error(f"❌ Error type: {type(simplified_error)}")
                    logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                    raise simplified_error
                    
        except Exception as e:
            logger.error(f"❌ Failed to store blog: {str(e)}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise e
    
    async def _store_content_in_storage(
        self, 
        bucket_name: str, 
        file_path: str, 
        content: str, 
        content_type: str = "application/json"
    ) -> bool:
        """Store content in Supabase Storage"""
        try:
            logger.info(f"🔍 Starting content storage in Supabase")
            logger.info(f"🔍 Bucket: {bucket_name}")
            logger.info(f"🔍 File path: {file_path}")
            logger.info(f"🔍 Content type: {content_type}")
            logger.info(f"🔍 Content length: {len(content)} characters")
            
            # Ensure bucket exists
            if not bucket_name:
                bucket_name = "blog-content"
            
            logger.info(f"🔍 Ensuring bucket exists: {bucket_name}")
            self._ensure_bucket_exists(bucket_name)
            
            logger.info(f"📤 Uploading content to storage...")
            
            # Upload content to storage
            result = supabase_client.storage.from_(bucket_name).upload(
                path=file_path,
                file=content.encode('utf-8'),
                file_options={"content-type": content_type}
            )
            
            logger.info(f"📤 Storage upload result: {result}")
            
            if result:
                logger.info(f"✅ Content stored in {bucket_name}/{file_path}")
                return True
            else:
                logger.error(f"❌ Failed to store content in {bucket_name}/{file_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Storage error: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            logger.warning(f"⚠️ Storage failed, will use database fallback")
            return False
    
    def _ensure_bucket_exists(self, bucket_name: str):
        """Ensure storage bucket exists, create if it doesn't"""
        try:
            if not bucket_name:
                bucket_name = "blog-content"
            # List buckets to check if ours exists
            buckets = supabase_client.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            if bucket_name not in bucket_names:
                # Create bucket with public access for blog content
                try:
                    supabase_client.storage.create_bucket(
                        name=bucket_name,
                        file_size_limit=52428800,  # 50MB limit
                        allowed_mime_types=["application/json", "text/plain", "text/markdown"]
                    )
                    logger.info(f"✅ Created storage bucket: {bucket_name}")
                except Exception as create_error:
                    logger.warning(f"⚠️ Could not create bucket {bucket_name}: {create_error}")
                    # Try to create without additional parameters
                    try:
                        supabase_client.storage.create_bucket(name=bucket_name)
                        logger.info(f"✅ Created basic storage bucket: {bucket_name}")
                    except Exception as basic_error:
                        logger.warning(f"⚠️ Could not create basic bucket {bucket_name}: {basic_error}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not ensure bucket exists: {e}")
            # Continue anyway, bucket might already exist

    def get_blog_content(self, storage_path: str, bucket_name: str = None) -> Dict[str, Any]:
        """Retrieve blog content from S3 or database"""
        try:
            logger.info(f"🔍 get_blog_content called with storage_path: {storage_path}, bucket_name: {bucket_name}")
            
            # If it's an S3 storage path, retrieve from S3
            if bucket_name == "s3-blog-content" or storage_path.startswith("blogs/"):
                logger.info(f"🔍 Retrieving content from S3: {storage_path}")
                try:
                    content_data = self.s3_storage.retrieve_blog_content(storage_path)
                    logger.info(f"🔍 S3 retrieval result: {content_data}")
                    if content_data:
                        return content_data
                    else:
                        logger.warning(f"⚠️ S3 returned empty content for: {storage_path}")
                        raise Exception(f"Failed to retrieve content from S3: {storage_path}")
                except Exception as s3_error:
                    logger.error(f"❌ S3 retrieval failed: {s3_error}")
                    # Fall back to database content if available
                    logger.info("🔄 Falling back to database content...")
                    return {"content": "S3 content retrieval failed, using database fallback", "storage_type": "database_fallback", "error": str(s3_error)}
            
            # If it's a database fallback, return None (content is in database)
            elif bucket_name == "database":
                logger.info(f"🔍 Content stored in database, not in S3")
                return {"content": "Content stored in database", "storage_type": "database"}
            
            # Fallback to old Supabase storage method
            else:
                logger.info(f"🔍 Falling back to Supabase storage: {bucket_name}/{storage_path}")
                if bucket_name is None:
                    bucket_name = settings.STORAGE_BUCKET_NAME or "blog-content"
                if not bucket_name:
                    bucket_name = "blog-content"
                
                # Download content from storage
                result = supabase_client.storage.from_(bucket_name).download(storage_path)
                
                if result:
                    # Parse JSON content
                    content_data = json.loads(result.decode('utf-8'))
                    logger.info(f"✅ Retrieved content from {bucket_name}/{storage_path}")
                    return content_data
                else:
                    raise Exception(f"Failed to retrieve content from {bucket_name}/{storage_path}")
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve blog content: {e}")
            raise
    
    async def update_blog_content(
        self, 
        blog_id: str, 
        new_content: str, 
        new_title: str = None
    ) -> bool:
        """Update blog content in storage and metadata in database"""
        try:
            # Get current blog metadata
            blog_response = supabase_client.table("blogs").select("*").eq("id", blog_id).execute()
            
            if not blog_response.data:
                raise Exception("Blog not found")
            
            blog = blog_response.data[0]
            current_path = blog["storage_path"]
            
            # Create new version path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_hash = hashlib.md5(new_content.encode()).hexdigest()
            new_path = f"blogs/{blog['project_id']}/{timestamp}_{new_hash[:8]}.json"
            
            # Prepare updated content
            content_data = {
                "title": new_title or blog["title"],
                "content": new_content,
                "prompt": blog["prompt"],
                "ai_model": blog["ai_model"],
                "word_count": len(new_content.split()),
                "generated_at": datetime.now().isoformat(),
                "version": "2.0",
                "previous_version": current_path
            }
            
            # Store new content
            bucket_name = settings.STORAGE_BUCKET_NAME or "blog-content"
            if not bucket_name:
                bucket_name = "blog-content"
            storage_result = await self._store_content_in_storage(
                bucket_name=bucket_name,
                file_path=new_path,
                content=json.dumps(content_data, indent=2)
            )
            
            if not storage_result:
                raise Exception("Failed to store updated content")
            
            # Update database metadata
            update_data = {
                "title": new_title or blog["title"],
                "storage_path": new_path,
                "word_count": len(new_content.split()),
                "content_size_bytes": len(new_content.encode('utf-8')),
                "content_hash": new_hash,
                "updated_at": datetime.now().isoformat()
            }
            
            result = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
            
            if result.data:
                logger.info(f"✅ Blog content updated successfully: {blog_id}")
                return True
            else:
                raise Exception("Failed to update blog metadata")
                
        except Exception as e:
            logger.error(f"❌ Failed to update blog content: {e}")
            return False

# Create service instance
blog_generation_service = BlogGenerationService()
