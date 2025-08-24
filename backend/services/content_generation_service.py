import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from uuid import UUID

from core.ai_client import AIClient
from core.supabase_client import supabase_client
from models.blog import BlogCreate, BlogResponse
from models.project import ProjectResponse

logger = logging.getLogger(__name__)

class ContentGenerationService:
    def __init__(self):
        self.ai_client = AIClient()
    
    async def generate_blog_titles(self, project: ProjectResponse, num_blogs: int) -> List[str]:
        """Generate blog titles based on project description"""
        try:
            prompt = f"""
            Generate {num_blogs} engaging blog post titles based on this project description:
            
            Project: {project.name}
            Description: {project.description}
            
            Requirements:
            - Titles should be SEO-optimized
            - Each title should be unique and engaging
            - Focus on the main topic from the description
            - Use action words and numbers where appropriate
            - Keep titles between 50-60 characters
            
            Return only the titles, one per line, without numbering or quotes.
            """
            
            # Use the project's configured AI model
            ai_model = project.draft_creation_model or "openai"
            
            response = await self.ai_client.generate_content(
                prompt=prompt,
                model=ai_model,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Parse the response to extract titles
            titles = [title.strip() for title in response.split('\n') if title.strip()]
            
            # Ensure we have the right number of titles
            if len(titles) < num_blogs:
                logger.warning(f"Generated only {len(titles)} titles, expected {num_blogs}")
                # Generate additional titles if needed
                remaining = num_blogs - len(titles)
                additional_prompt = f"Generate {remaining} more unique blog titles for the same project. Be creative and diverse."
                additional_response = await self.ai_client.generate_content(
                    prompt=additional_prompt,
                    model=ai_model,
                    max_tokens=500,
                    temperature=0.8
                )
                additional_titles = [title.strip() for title in additional_response.split('\n') if title.strip()]
                titles.extend(additional_titles[:remaining])
            
            return titles[:num_blogs]
            
        except Exception as e:
            logger.error(f"Error generating blog titles: {e}")
            raise
    
    async def create_blog_entries(self, project: ProjectResponse, titles: List[str]) -> List[BlogResponse]:
        """Create blog entries in the database with generated titles"""
        try:
            blogs = []
            
            for title in titles:
                blog_data = {
                    "project_id": str(project.id),
                    "user_id": str(project.user_id),
                    "title": title,
                    "status": "draft",
                    "generation_metadata": {
                        "ai_model": project.draft_creation_model or "openai",
                        "generated_at": datetime.utcnow().isoformat(),
                        "project_name": project.name
                    },
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Insert blog into database
                response = supabase_client.table("blogs").insert(blog_data).execute()
                
                if response.data:
                    blog = BlogResponse(**response.data[0])
                    blogs.append(blog)
                    logger.info(f"Created blog entry: {blog.id} - {title}")
                else:
                    logger.error(f"Failed to create blog entry for title: {title}")
            
            return blogs
            
        except Exception as e:
            logger.error(f"Error creating blog entries: {e}")
            raise
    
    async def generate_full_blog_content(self, blog_id: UUID, project: ProjectResponse) -> str:
        """Generate full blog content for a specific blog"""
        try:
            # Get the blog entry
            response = supabase_client.table("blogs").select("*").eq("id", str(blog_id)).execute()
            
            if not response.data:
                raise ValueError(f"Blog not found: {blog_id}")
            
            blog = response.data[0]
            
            # Generate content prompt
            prompt = f"""
            Write a comprehensive, engaging blog post with the title: "{blog['title']}"
            
            Project Context: {project.description}
            
            Requirements:
            - Write in a professional yet engaging tone
            - Include an introduction, main content sections, and conclusion
            - Use proper headings and subheadings
            - Include relevant examples and actionable insights
            - Optimize for SEO with natural keyword usage
            - Target word count: 800-1200 words
            - Format with proper HTML tags for structure
            
            Write the complete blog post:
            """
            
            # Use the project's configured AI model
            ai_model = project.draft_creation_model or "openai"
            
            content = await self.ai_client.generate_content(
                prompt=prompt,
                model=ai_model,
                max_tokens=2000,
                temperature=0.7
            )
            
            # Update blog status and metadata
            word_count = len(content.split())
            seo_score = self._calculate_seo_score(content, blog['title'])
            
            update_data = {
                "status": "completed",
                "word_count": word_count,
                "seo_score": seo_score,
                "generation_metadata": {
                    **blog.get("generation_metadata", {}),
                    "content_generated_at": datetime.utcnow().isoformat(),
                    "content_ai_model": ai_model,
                    "word_count": word_count,
                    "seo_score": seo_score
                },
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Update the blog entry
            supabase_client.table("blogs").update(update_data).eq("id", str(blog_id)).execute()
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating full blog content: {e}")
            # Update blog status to failed
            try:
                supabase_client.table("blogs").update({
                    "status": "failed",
                    "generation_metadata": {
                        "error": str(e),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(blog_id)).execute()
            except:
                pass
            raise
    
    def _calculate_seo_score(self, content: str, title: str) -> int:
        """Calculate a basic SEO score for the blog content"""
        score = 0
        
        # Title length check (50-60 characters is optimal)
        if 50 <= len(title) <= 60:
            score += 20
        
        # Content length check (800+ words is good)
        word_count = len(content.split())
        if word_count >= 800:
            score += 20
        elif word_count >= 500:
            score += 10
        
        # Heading structure check
        if "<h1>" in content.lower() or "# " in content:
            score += 15
        
        if "<h2>" in content.lower() or "## " in content:
            score += 15
        
        # Keyword density check (basic)
        title_words = set(title.lower().split())
        content_lower = content.lower()
        keyword_count = sum(content_lower.count(word) for word in title_words if len(word) > 3)
        if 5 <= keyword_count <= 20:
            score += 20
        elif keyword_count > 20:
            score += 10
        
        return min(score, 100)
    
    async def process_project(self, project_id: UUID) -> Dict[str, Any]:
        """Process a complete project: generate titles and create blog entries"""
        try:
            # Get project details
            response = supabase_client.table("projects").select("*").eq("id", str(project_id)).execute()
            
            if not response.data:
                raise ValueError(f"Project not found: {project_id}")
            
            project = ProjectResponse(**response.data[0])
            
            # Update project status to in_progress
            supabase_client.table("projects").update({
                "status": "in_progress",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(project_id)).execute()
            
            # Generate blog titles
            titles = await self.generate_blog_titles(project, project.total_blogs)
            
            # Create blog entries
            blogs = await self.create_blog_entries(project, titles)
            
            # Update project with completed blogs count
            supabase_client.table("projects").update({
                "completed_blogs": len(blogs),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(project_id)).execute()
            
            logger.info(f"Successfully processed project {project_id}: {len(blogs)} blogs created")
            
            return {
                "project_id": str(project_id),
                "titles_generated": len(titles),
                "blogs_created": len(blogs),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error processing project {project_id}: {e}")
            
            # Update project status to failed
            try:
                supabase_client.table("projects").update({
                    "status": "failed",
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(project_id)).execute()
            except:
                pass
            
            raise
