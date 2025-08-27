import asyncio
import logging
import hashlib
import json
import traceback
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
        ai_model: str, 
        project_api_keys: dict = None
    ) -> Dict[str, Any]:
        """Generate blog content using specified AI model with fallback to Gemini if OpenAI fails"""
        try:
            logger.info(f"🔍 Starting blog content generation for blog {blog_number}")
            logger.info(f"🔍 AI model: {ai_model}")
            logger.info(f"🔍 Project API keys: {list(project_api_keys.keys()) if project_api_keys else 'None'}")
            logger.info(f"🔍 Project description: {project_description}")
            
            # Use project API keys - no fallback to global settings
            if ai_model.lower() == "openai":
                logger.info(f"🔍 Using OpenAI model")
                if project_api_keys and project_api_keys.get("openai"):
                    logger.info(f"✅ Using project-specific OpenAI key")
                    try:
                        # Try OpenAI first
                        return await self._generate_with_openai(project_description, blog_number, project_api_keys["openai"])
                    except Exception as openai_error:
                        logger.warning(f"⚠️ OpenAI generation failed: {openai_error}")
                        logger.info(f"🔄 Attempting fallback to Gemini...")
                        
                        # Fallback to Gemini if available
                        if project_api_keys and project_api_keys.get("gemini"):
                            logger.info(f"✅ Fallback: Using Gemini for blog {blog_number}")
                            try:
                                return await self._generate_with_gemini(project_description, blog_number, project_api_keys["gemini"])
                            except Exception as gemini_error:
                                logger.error(f"❌ Gemini fallback also failed: {gemini_error}")
                                # Re-raise the original OpenAI error since both failed
                                raise openai_error
                        else:
                            logger.error(f"❌ No Gemini API key available for fallback")
                            raise openai_error
                else:
                    logger.error(f"❌ No OpenAI API key found in project")
                    raise ValueError("OpenAI API key not configured for this project")
            elif ai_model.lower() == "gemini":
                logger.info(f"🔍 Using Gemini model")
                if project_api_keys and project_api_keys.get("gemini"):
                    logger.info(f"✅ Using project-specific Gemini key")
                    # Use project-specific Gemini key
                    return await self._generate_with_gemini(project_description, blog_number, project_api_keys["gemini"])
                else:
                    logger.error(f"❌ No Gemini API key found in project")
                    raise ValueError("Gemini API key not configured for this project")
            else:
                logger.error(f"❌ Unsupported AI model: {ai_model}")
                raise ValueError(f"AI model '{ai_model}' not supported")
        except Exception as e:
            logger.error(f"❌ Failed to generate blog content: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    async def _generate_with_openai(self, project_description: str, blog_number: int, api_key: str) -> Dict[str, Any]:
        """Generate blog content using OpenAI with project-specific API key
        
        NOTE: Creates a FRESH OpenAI client configuration for each blog
        to ensure independent requests and better content variation.
        """
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
            openai.api_key = api_key  # Fresh API key configuration per blog
            logger.info(f"🔍 Fresh OpenAI client configured for blog {blog_number}")
            
            # Generate unique writing style and content angle for each blog
            writing_styles = [
                "analytical and data-driven",
                "storytelling and narrative",
                "practical and hands-on",
                "educational and tutorial",
                "insightful and thought-provoking",
                "comprehensive and detailed",
                "focused and specialized",
                "innovative and cutting-edge"
            ]
            content_angles = [
                "focus on beginner-friendly explanations",
                "emphasize advanced techniques and insights",
                "highlight common mistakes and solutions",
                "explore industry trends and innovations",
                "provide step-by-step implementation guides",
                "discuss real-world applications and case studies",
                "examine the science and theory behind the topic",
                "offer expert tips and best practices"
            ]
            selected_style = writing_styles[blog_number % len(writing_styles)]
            selected_angle = content_angles[blog_number % len(content_angles)]
            
            prompt = f"""
            Create a comprehensive, STANDALONE blog post about: {project_description}
            
            IMPORTANT: This is NOT part of a series. Create a completely independent blog post.
            
            Writing Style: Use a {selected_style} approach for this blog.
            Content Focus: {selected_angle}
            
            Requirements:
            - Write in a professional, informative tone
            - Include a compelling, unique title that stands alone
            - Structure with clear headings and subheadings
            - Provide practical insights and actionable advice
            - Aim for 800-1200 words
            - Include relevant examples and case studies
            - Make this blog completely self-contained and independent
            - Use a unique writing style and perspective
            - Avoid any references to being part of a series or collection
            - Emphasize the {selected_style} approach throughout the content
            - Focus on {selected_angle} as the primary content angle
            
            Format the response as:
            TITLE: [Your blog title here]
            CONTENT: [Your blog content here with proper markdown formatting]
            """
            
            logger.info(f"📝 Sending prompt to OpenAI: {prompt[:100]}...")
            
            # Use asyncio.run_in_executor to make the OpenAI call non-blocking
            # This allows other coroutines to run while waiting for the API response
            logger.info(f"🔍 Sending request to fresh OpenAI instance for blog {blog_number}")
            
            # Convert the synchronous OpenAI call to asynchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,  # Use default executor
                lambda: openai.ChatCompletion.create(
                    model="gpt-4o-mini-2024-07-18",  # Updated to GPT-4o Mini
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,  # Use max_tokens for GPT-4o Mini
                    temperature=0.7  # Restored temperature parameter for GPT-4o Mini
                )
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
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    async def _generate_with_gemini(self, project_description: str, blog_number: int, api_key: str) -> Dict[str, Any]:
        """Generate blog content using Gemini with project-specific API key
        
        NOTE: Creates a FRESH Gemini model instance for each blog (like OpenAI)
        to ensure independent requests and better content variation.
        """
        try:
            logger.info(f"🔍 Starting Gemini generation for blog {blog_number}")
            logger.info(f"🔍 API key provided: {bool(api_key)}")
            logger.info(f"🔍 Project description: {project_description}")
            
            # Always require API key - no fallback to global client
            if not api_key:
                logger.error(f"❌ No Gemini API key provided")
                raise ValueError("Gemini API key is required")
            
            logger.info(f"✅ Using project-specific Gemini API key")
            logger.info(f"🔍 API key length: {len(api_key) if api_key else 0}")
            
            # Configure Gemini with the project-specific API key
            import google.generativeai as genai
            try:
                genai.configure(api_key=api_key)
                logger.info(f"✅ Gemini configured with API key")
            except Exception as e:
                logger.error(f"❌ Failed to configure Gemini: {e}")
                raise ValueError(f"Failed to configure Gemini API: {e}")
            
            # Create a FRESH Gemini model instance for each blog (like OpenAI)
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')  # Fresh instance per blog
                logger.info(f"✅ Fresh Gemini model instance created for blog {blog_number}: gemini-1.5-pro")
            except Exception as e:
                logger.error(f"❌ Failed to create Gemini model: {e}")
                raise ValueError(f"Failed to create Gemini model: {e}")
            
            # Generate unique writing style and content angle for each blog
            writing_styles = [
                "analytical and data-driven",
                "storytelling and narrative",
                "practical and hands-on",
                "educational and tutorial",
                "insightful and thought-provoking",
                "comprehensive and detailed",
                "focused and specialized",
                "innovative and cutting-edge"
            ]
            content_angles = [
                "focus on beginner-friendly explanations",
                "emphasize advanced techniques and insights",
                "highlight common mistakes and solutions",
                "explore industry trends and innovations",
                "provide step-by-step implementation guides",
                "discuss real-world applications and case studies",
                "examine the science and theory behind the topic",
                "offer expert tips and best practices"
            ]
            selected_style = writing_styles[blog_number % len(writing_styles)]
            selected_angle = content_angles[blog_number % len(content_angles)]
            
            prompt = f"""
            Create a comprehensive, STANDALONE blog post about: {project_description}
            
            IMPORTANT: This is NOT part of a series. Create a completely independent blog post.
            
            Writing Style: Use a {selected_style} approach for this blog.
            Content Focus: {selected_angle}
            
            Requirements:
            - Write in a professional, informative tone
            - Include a compelling, unique title that stands alone
            - Structure with clear headings and subheadings
            - Include introduction, main content sections, and conclusion
            - Aim for 800-1200 words
            - Use bullet points and numbered lists where appropriate
            - Include a call-to-action at the end
            - Make it SEO-friendly with natural keyword usage
            - Make this blog completely self-contained and independent
            - Use a unique writing style and perspective
            - Avoid any references to being part of a series or collection
            - Emphasize the {selected_style} approach throughout the content
            - Focus on {selected_angle} as the primary content angle
            
            Format the response exactly as follows:
            TITLE: [Your blog title here]
            
            [Your blog content here with proper formatting]
            """
            
            logger.info(f"📝 Sending prompt to Gemini: {prompt[:100]}...")
            
            # Generate content with Gemini (fresh instance per blog) - now asynchronous
            try:
                logger.info(f"🔍 Sending request to fresh Gemini instance for blog {blog_number}")
                
                # Convert the synchronous Gemini call to asynchronous
                # This allows other coroutines to run while waiting for the API response
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,  # Use default executor
                    lambda: model.generate_content(prompt)
                )
                
                logger.info(f"✅ Gemini content generation request sent successfully")
            except Exception as e:
                logger.error(f"❌ Failed to generate content with Gemini: {e}")
                raise ValueError(f"Failed to generate content with Gemini: {e}")
            
            # Check if response is valid
            if not response:
                logger.error(f"❌ No response from Gemini")
                raise ValueError("No response from Gemini API")
            
            if not hasattr(response, 'text') or not response.text:
                logger.error(f"❌ Invalid response from Gemini: {response}")
                logger.error(f"❌ Response type: {type(response)}")
                logger.error(f"❌ Response attributes: {dir(response)}")
                raise ValueError("Invalid response from Gemini API")
            
            content = response.text
            logger.info(f"🔍 Raw Gemini response: {content[:200]}...")
            logger.info(f"🔍 Response type: {type(response)}")
            logger.info(f"🔍 Response attributes: {dir(response)}")
            logger.info(f"🔍 Response text length: {len(content) if content else 0}")
            
            # Extract title and content
            logger.info(f"🔍 Starting title and content extraction...")
            title = self._extract_title_from_gemini_response(content)
            blog_content = self._extract_content_from_gemini_response(content)
            
            logger.info(f"🔍 Extracted title: {title}")
            logger.info(f"🔍 Extracted content length: {len(blog_content)} characters")
            logger.info(f"🔍 Content preview: {blog_content[:100]}...")
            
            # Calculate word count
            word_count = len(blog_content.split())
            
            logger.info(f"✅ Gemini generation completed successfully")
            logger.info(f"🔍 Generated title: {title}")
            logger.info(f"🔍 Content length: {word_count} words")
            
            return {
                "title": title or f"Blog #{blog_number}: {project_description[:50]}...",
                "content": blog_content,
                "word_count": word_count,
                "ai_model": "gemini",
                "model_version": "gemini-1.5-pro",  # Updated model version
                "prompt": prompt,
                "tokens_used": len(content.split()),  # Approximate token count
                "model_provider": "gemini"
            }
            
        except Exception as e:
            logger.error(f"❌ Gemini generation failed: {e}")
            logger.error(f"❌ Error type: {type(e)}")
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
        try:
            logger.info(f"🔍 Extracting title from Gemini response...")
            logger.info(f"🔍 Response preview: {response[:200]}...")
            title = self._extract_title_from_openai_response(response)
            logger.info(f"🔍 Extracted title: {title}")
            return title
        except Exception as e:
            logger.error(f"❌ Failed to extract title from Gemini response: {e}")
            return f"Blog Post - {datetime.now().strftime('%Y-%m-%d')}"
    
    def _extract_content_from_gemini_response(self, response: str) -> str:
        """Extract content from Gemini response"""
        try:
            logger.info(f"🔍 Extracting content from Gemini response...")
            logger.info(f"🔍 Response preview: {response[:200]}...")
            content = self._extract_content_from_openai_response(response)
            logger.info(f"🔍 Extracted content length: {len(content)}")
            return content
        except Exception as e:
            logger.error(f"❌ Failed to extract content from Gemini response: {e}")
            return response.strip()
    
    async def generate_blogs_for_project(
        self,
        project_id: str,
        project_description: str,
        num_blogs: int,
        ai_model: str = "openai",
        project_api_keys: dict = None,
        max_concurrent_blogs: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate multiple blogs for a project with automatic multi-threading for multiple blogs"""
        # Automatically enable multi-threading if generating more than 1 blog
        use_multithreading = num_blogs > 1
        
        if use_multithreading:
            logger.info(f"🚀 Starting multi-threaded blog generation for {num_blogs} blogs")
            return await self._generate_blogs_multithreaded(
                project_id, project_description, num_blogs, ai_model, 
                project_api_keys, max_concurrent_blogs
            )
        else:
            logger.info(f"🚀 Starting sequential blog generation for {num_blogs} blog")
            return await self._generate_blogs_sequential(
                project_id, project_description, num_blogs, ai_model, project_api_keys
            )

    async def _generate_blogs_multithreaded(
        self,
        project_id: str,
        project_description: str,
        num_blogs: int,
        ai_model: str,
        project_api_keys: dict,
        max_concurrent_blogs: int
    ) -> List[Dict[str, Any]]:
        """Generate multiple blogs concurrently using asyncio.gather with semaphore for rate limiting"""
        generated_blogs = []
        failed_blogs = []
        
        # Create semaphore to control concurrency
        semaphore = asyncio.Semaphore(max_concurrent_blogs)
        
        # Log multi-threading setup
        start_time = asyncio.get_event_loop().time()
        logger.info(f"🚀 MULTI-THREADING SETUP:")
        logger.info(f"   📊 Total blogs to generate: {num_blogs}")
        logger.info(f"   🔀 Max concurrent blogs: {max_concurrent_blogs}")
        logger.info(f"   ⏱️  Start time: {start_time:.2f}s")
        logger.info(f"   🎯 Expected batches: {(num_blogs + max_concurrent_blogs - 1) // max_concurrent_blogs}")
        
        async def generate_single_blog(blog_number: int) -> Dict[str, Any]:
            """Generate a single blog with semaphore control and immediate database save"""
            blog_start_time = asyncio.get_event_loop().time()
            
            # Acquire semaphore to control concurrency
            async with semaphore:
                logger.info(f"🔓 SEMAPHORE ACQUIRED for Blog {blog_number} at {blog_start_time:.2f}s")
                try:
                    # Generate blog content
                    result = await self.generate_blog_content(
                        project_description, 
                        blog_number, 
                        ai_model,
                        project_api_keys
                    )
                    
                    # IMMEDIATELY save blog to database
                    logger.info(f"💾 IMMEDIATELY SAVING Blog {blog_number} to database...")
                    save_start = asyncio.get_event_loop().time()
                    
                    # Create blog record
                    blog_create = BlogCreate(
                        project_id=project_id,
                        title=result["title"],
                        status=BlogStatus.READY,
                        word_count=result["word_count"],
                        prompt=result["prompt"],
                        ai_model=result["ai_model"]
                    )
                    
                    # Store in database with content immediately
                    blog_record = self._store_blog(blog_create, result["content"])
                    
                    # Update blog with generation metadata immediately
                    supabase_client.table("blogs").update({
                        "generation_metadata": {
                            "ai_model": ai_model,
                            "generated_at": datetime.now().isoformat(),
                            "model_provider": result.get("model_provider", ai_model),
                            "generation_method": "multithreaded",
                            "concurrent_batch": f"batch_{blog_number // max_concurrent_blogs + 1}",
                            "concurrency_level": max_concurrent_blogs,
                            "immediate_save": True
                        },
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", blog_record["id"]).execute()
                    
                    save_end = asyncio.get_event_loop().time()
                    save_time = save_end - save_start
                    logger.info(f"💾 Blog {blog_number} IMMEDIATELY SAVED to database in {save_time:.2f}s (ID: {blog_record['id']})")
                    
                    # Update project progress in real-time
                    try:
                        # Get current completed blogs count and increment
                        current_response = supabase_client.table("projects").select("completed_blogs").eq("id", project_id).execute()
                        if current_response.data:
                            current_count = current_response.data[0].get("completed_blogs", 0)
                            new_count = current_count + 1
                            
                            supabase_client.table("projects").update({
                                "completed_blogs": new_count,
                                "updated_at": datetime.now().isoformat()
                            }).eq("id", project_id).execute()
                            logger.info(f"📊 Project progress updated: {current_count} → {new_count} blogs completed")
                    except Exception as progress_error:
                        logger.warning(f"⚠️ Could not update project progress: {progress_error}")
                    
                    blog_end_time = asyncio.get_event_loop().time()
                    blog_duration = blog_end_time - blog_start_time
                    logger.info(f"✅ Blog {blog_number} COMPLETED and SAVED in {blog_duration:.2f}s")
                    
                    # Return the saved blog record instead of just the generation result
                    return {
                        **result,
                        "blog_id": blog_record["id"],
                        "saved_to_db": True,
                        "save_time": save_time
                    }
                    
                except Exception as e:
                    blog_end_time = asyncio.get_event_loop().time()
                    blog_duration = blog_end_time - blog_start_time
                    logger.error(f"❌ Blog {blog_number} FAILED in {blog_duration:.2f}s: {e}")
                    raise
                finally:
                    logger.info(f"🔓 SEMAPHORE RELEASED for Blog {blog_number}")
        
        # Create all tasks at once - they will compete for semaphore slots
        logger.info(f"🔧 CREATING {num_blogs} CONCURRENT TASKS...")
        tasks = []
        for blog_number in range(1, num_blogs + 1):
            task = generate_single_blog(blog_number)
            tasks.append(task)
            logger.info(f"   📝 Task {blog_number} created and queued")
        
        logger.info(f"🚀 STARTING CONCURRENT EXECUTION with {len(tasks)} tasks...")
        logger.info(f"   🔀 Semaphore will allow {max_concurrent_blogs} blogs to run simultaneously")
        
        try:
            # Execute all tasks concurrently - they will compete for semaphore slots
            execution_start = asyncio.get_event_loop().time()
            
            # Use asyncio.gather to run all tasks concurrently
            # The semaphore will control how many can run at the same time
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            execution_end = asyncio.get_event_loop().time()
            total_execution_time = execution_end - execution_start
            
            logger.info(f"🎉 CONCURRENT EXECUTION COMPLETED in {total_execution_time:.2f}s")
            logger.info(f"   📊 Total blogs processed: {len(responses)}")
            logger.info(f"   ⚡ Average time per blog: {total_execution_time / num_blogs:.2f}s")
            logger.info(f"   🚀 Speed improvement: {num_blogs * 2 / total_execution_time:.1f}x faster than sequential")
            
            # Process results with detailed logging
            logger.info(f"📝 PROCESSING GENERATION RESULTS...")
            
            for i, response in enumerate(responses):
                blog_number = i + 1
                try:
                    if isinstance(response, Exception):
                        logger.error(f"❌ Blog {blog_number} generation failed: {response}")
                        failed_blogs.append(blog_number)
                        continue
                    
                    blog_data = response
                    if not blog_data:
                        logger.error(f"❌ Blog {blog_number} generation returned no data")
                        failed_blogs.append(blog_number)
                        continue
                    
                    logger.info(f"✅ Blog {blog_number} SUCCESS: '{blog_data.get('title', 'No title')}' - Already saved to database")
                    
                    # Blog was already saved during generation, just add to our list
                    if "blog_id" in blog_data:
                        # Get the blog record from database since it was already saved
                        try:
                            blog_record = supabase_client.table("blogs").select("*").eq("id", blog_data["blog_id"]).execute()
                            if blog_record.data:
                                generated_blogs.append(blog_record.data[0])
                                logger.info(f"📝 Blog {blog_number} added to results (ID: {blog_data['blog_id']})")
                            else:
                                logger.warning(f"⚠️ Blog {blog_number} not found in database despite being saved")
                        except Exception as db_error:
                            logger.error(f"❌ Error retrieving saved blog {blog_number}: {db_error}")
                    else:
                        logger.warning(f"⚠️ Blog {blog_number} missing blog_id - may not have been saved properly")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to process blog {blog_number}: {e}")
                    failed_blogs.append(blog_number)
                    continue
            
            # Final summary with timing
            end_time = asyncio.get_event_loop().time()
            total_time = end_time - start_time
            
            logger.info(f"📊 FINAL MULTI-THREADING SUMMARY:")
            logger.info(f"   ⏱️  Total time: {total_time:.2f}s")
            logger.info(f"   🚀 Concurrent execution: {total_execution_time:.2f}s")
            logger.info(f"   💾 Storage & metadata: {total_time - total_execution_time:.2f}s")
            logger.info(f"   📝 Successfully generated: {len(generated_blogs)} blogs")
            logger.info(f"   ❌ Failed: {len(failed_blogs)} blogs")
            logger.info(f"   🎯 Success rate: {(len(generated_blogs) / num_blogs) * 100:.1f}%")
            
            if failed_blogs:
                logger.info(f"   📋 Failed blog numbers: {failed_blogs}")
            
            # Performance analysis
            if len(generated_blogs) > 0:
                sequential_estimate = num_blogs * 2  # Assume 2 seconds per blog sequentially
                speedup = sequential_estimate / total_time
                logger.info(f"   ⚡ Performance: {speedup:.1f}x faster than estimated sequential")
                logger.info(f"   💡 Concurrency efficiency: {(speedup / max_concurrent_blogs) * 100:.1f}%")
            
            logger.info(f"🎉 Multi-threaded blog generation completed: {len(generated_blogs)}/{num_blogs} successful")
            return generated_blogs
            
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            total_time = end_time - start_time
            logger.error(f"❌ Multi-threaded blog generation failed after {total_time:.2f}s: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    async def _generate_blogs_sequential(
        self,
        project_id: str,
        project_description: str,
        num_blogs: int,
        ai_model: str,
        project_api_keys: dict
    ) -> List[Dict[str, Any]]:
        """Generate multiple blogs for a project sequentially"""
        generated_blogs = []
        
        try:
            logger.info(f"🚀 Starting sequential blog generation for project {project_id}: {num_blogs} blogs")
            logger.info(f"🔍 AI Model: {ai_model}")
            logger.info(f"🔍 Project API keys: {list(project_api_keys.keys()) if project_api_keys else 'None'}")
            logger.info(f"🔍 Project description: {project_description}")
            
            for blog_number in range(1, num_blogs + 1):
                try:
                    logger.info(f"📝 Generating blog {blog_number}/{num_blogs}")
                    
                    # Generate blog content using project API keys
                    blog_data = await self.generate_blog_content(
                        project_description, 
                        blog_number, 
                        ai_model,
                        project_api_keys
                    )
                    
                    logger.info(f"✅ Blog content generated: {blog_data['title']}")
                    
                    # Create blog record with ready status
                    blog_create = BlogCreate(
                        project_id=project_id,
                        title=blog_data["title"],
                        status=BlogStatus.READY,  # Always ready after generation
                        word_count=blog_data["word_count"],
                        prompt=blog_data["prompt"],
                        ai_model=blog_data["ai_model"]
                    )
                    
                    logger.info(f"📝 Storing blog in database: {blog_data['title']}")
                    
                    # Store in database with content
                    blog_record = self._store_blog(blog_create, blog_data["content"])
                    
                    logger.info(f"✅ Blog stored in database: {blog_record['id']}")
                    
                    # Update blog with generation metadata
                    supabase_client.table("blogs").update({
                        "generation_metadata": {
                            "ai_model": ai_model,
                            "generated_at": datetime.now().isoformat(),
                            "model_provider": blog_data.get("model_provider", ai_model),
                            "generation_method": "sequential"
                        },
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", blog_record["id"]).execute()
                    
                    # Update the blog record with metadata
                    blog_record["generation_metadata"] = {
                        "ai_model": ai_model,
                        "generated_at": datetime.now().isoformat(),
                        "model_provider": blog_data.get("model_provider", ai_model),
                        "generation_method": "sequential"
                    }
                    
                    generated_blogs.append(blog_record)
                    logger.info(f"✅ Blog {blog_number} generated successfully: {blog_data['title']}")
                    
                    # Update project progress in real-time
                    try:
                        # Get current completed blogs count and increment
                        current_response = supabase_client.table("projects").select("completed_blogs").eq("id", project_id).execute()
                        if current_response.data:
                            current_count = current_response.data[0].get("completed_blogs", 0)
                            new_count = current_count + 1
                            
                            supabase_client.table("projects").update({
                                "completed_blogs": new_count,
                                "updated_at": datetime.now().isoformat()
                            }).eq("id", project_id).execute()
                            logger.info(f"📊 Project progress updated: {current_count} → {new_count} blogs completed")
                    except Exception as progress_error:
                        logger.warning(f"⚠️ Could not update project progress: {progress_error}")
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate blog {blog_number}: {e}")
                    logger.error(f"❌ Error type: {type(e)}")
                    logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                    # Continue with next blog
                    continue
            
            logger.info(f"🎉 Sequential blog generation completed: {len(generated_blogs)}/{num_blogs} blogs generated")
            return generated_blogs
            
        except Exception as e:
            logger.error(f"❌ Sequential blog generation service failed: {e}")
            logger.error(f"❌ Error type: {type(e)}")
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
                # Store content in S3
                s3_key = storage_path  # Use storage_path directly, no need to prefix with bucket name
                self.s3_storage.upload_content(
                    content=content,
                    key=s3_key,
                    content_type="application/json"
                )
                logger.info(f"✅ Content uploaded to S3: {s3_key}")
                
                # Store blog metadata in database
                blog_metadata = {
                    "project_id": str(blog_create.project_id),
                    "title": blog_create.title,
                    "status": blog_create.status,
                    "word_count": blog_create.word_count,
                    "prompt": blog_create.prompt,
                    "ai_model": blog_create.ai_model,
                    "storage_path": storage_path,
                    "storage_bucket": "blog-content",
                    "s3_content_key": s3_key,
                    "content_size_bytes": len(content.encode()),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                logger.info(f"📝 Blog metadata prepared: {blog_metadata}")
                
                # Insert into database
                response = supabase_client.table("blogs").insert(blog_metadata).execute()
                
                if response.data:
                    logger.info(f"✅ Blog stored in database: {response.data[0]['id']}")
                    return response.data[0]
                else:
                    logger.error(f"❌ Failed to store blog in database")
                    raise RuntimeError("Database insert failed")
                    
            except Exception as s3_error:
                logger.warning(f"⚠️ S3 storage failed, using database fallback: {s3_error}")
                
                # Fallback: store content directly in database
                logger.info("📝 Using database fallback for content storage")
                
                blog_metadata = {
                    "project_id": str(blog_create.project_id),
                    "title": blog_create.title,
                    "content": content,  # Store content directly in database
                    "status": blog_create.status,
                    "word_count": blog_create.word_count,
                    "prompt": blog_create.prompt,
                    "ai_model": blog_create.ai_model,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                logger.info(f"📝 Blog metadata prepared: {blog_metadata}")
                
                # Insert into database
                response = supabase_client.table("blogs").insert(blog_metadata).execute()
                
                if response.data:
                    logger.info(f"✅ Blog stored in database (fallback): {response.data[0]['id']}")
                    return response.data[0]
                else:
                    logger.error(f"❌ Failed to store blog in database (fallback)")
                    raise RuntimeError("Database insert failed (fallback)")
                    
        except Exception as e:
            logger.error(f"❌ Blog storage failed: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
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
            
            # Normalize bucket name - treat 's3-blog-content' as 'blog-content'
            if bucket_name == "s3-blog-content":
                bucket_name = "blog-content"
                logger.info(f"🔄 Normalized bucket name from 's3-blog-content' to 'blog-content'")
            
            # If it's a Supabase storage bucket, try Supabase storage first
            if bucket_name == "blog-content":
                logger.info(f"🔍 Attempting Supabase storage for bucket: {bucket_name}")
                try:
                    # Download content from Supabase storage
                    result = supabase_client.storage.from_(bucket_name).download(storage_path)
                    
                    if result:
                        # Parse JSON content
                        content_data = json.loads(result.decode('utf-8'))
                        logger.info(f"✅ Retrieved content from Supabase storage: {bucket_name}/{storage_path}")
                        return content_data
                    else:
                        raise Exception(f"Failed to retrieve content from Supabase storage: {bucket_name}/{storage_path}")
                        
                except Exception as supabase_error:
                    logger.warning(f"⚠️ Supabase storage failed: {supabase_error}")
                    # Fall back to S3 if Supabase fails
                    logger.info("🔄 Falling back to S3 storage...")
                    try:
                        content_data = self.s3_storage.retrieve_blog_content(storage_path, bucket_name)
                        if content_data:
                            return content_data
                        else:
                            raise Exception("S3 also failed")
                    except Exception as s3_error:
                        logger.error(f"❌ Both Supabase and S3 storage failed")
                        # Final fallback to database content
                        return {"content": "Storage retrieval failed, using database fallback", "storage_type": "database_fallback", "error": f"Supabase: {supabase_error}, S3: {s3_error}"}
            
            # If it's an S3 storage path, retrieve from S3
            elif storage_path.startswith("blogs/"):
                logger.info(f"🔍 Retrieving content from S3: {storage_path}")
                try:
                    content_data = self.s3_storage.retrieve_blog_content(storage_path, bucket_name)
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
