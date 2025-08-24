import openai
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import asyncio
import logging
from .config import settings

logger = logging.getLogger(__name__)

class AIClient:
    """AI client for OpenAI and Gemini APIs"""
    
    def __init__(self):
        self.openai_client = None
        self.gemini_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI clients with API keys"""
        try:
            if settings.OPENAI_API_KEY:
                openai.api_key = settings.OPENAI_API_KEY
                self.openai_client = openai
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI API key not found")
                
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini client initialized successfully")
            else:
                logger.warning("Gemini API key not found")
                
        except Exception as e:
            logger.error(f"Error initializing AI clients: {e}")
    
    async def generate_blog_draft(
        self, 
        prompt: str, 
        ai_model: str = "openai",
        ai_model_version: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a blog draft using the specified AI model
        
        Args:
            prompt: The blog generation prompt
            ai_model: Either 'openai' or 'gemini'
            ai_model_version: Specific model version (e.g., 'gpt-4', 'gpt-3.5-turbo')
            **kwargs: Additional parameters for the AI model
            
        Returns:
            Dict containing generated content and metadata
        """
        try:
            if ai_model.lower() == "openai":
                return await self._generate_with_openai(prompt, ai_model_version, **kwargs)
            elif ai_model.lower() == "gemini":
                return await self._generate_with_gemini(prompt, **kwargs)
            else:
                raise ValueError(f"Unsupported AI model: {ai_model}")
                
        except Exception as e:
            logger.error(f"Error generating blog draft with {ai_model}: {e}")
            raise
    
    async def _generate_with_openai(
        self, 
        prompt: str, 
        model_version: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate blog draft using OpenAI API"""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        # Use specified model version or default
        model = model_version or "gpt-3.5-turbo"
        
        # Enhanced prompt for better blog generation
        enhanced_prompt = f"""
        Write a comprehensive, engaging blog post based on the following topic:
        
        TOPIC: {prompt}
        
        Requirements:
        - Write in a professional, engaging tone
        - Include an attention-grabbing headline
        - Structure with clear headings and subheadings
        - Include introduction, main content sections, and conclusion
        - Aim for 800-1200 words
        - Use bullet points and numbered lists where appropriate
        - Include a call-to-action at the end
        - Make it SEO-friendly with natural keyword usage
        
        Format the response as:
        TITLE: [Your blog title here]
        
        [Your blog content here with proper formatting]
        """
        
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert content writer specializing in creating engaging, SEO-optimized blog posts."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=kwargs.get('max_tokens', 2000),
                temperature=kwargs.get('temperature', 0.7),
                top_p=kwargs.get('top_p', 1.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0.0),
                presence_penalty=kwargs.get('presence_penalty', 0.0)
            )
            
            content = response.choices[0].message.content
            
            # Extract title and content
            title = ""
            blog_content = content
            
            if "TITLE:" in content:
                title_part, content_part = content.split("TITLE:", 1)
                title = title_part.strip()
                blog_content = content_part.strip()
            
            return {
                "title": title or f"Blog about {prompt}",
                "content": blog_content,
                "model": model,
                "tokens_used": response.usage.total_tokens,
                "model_provider": "openai"
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_with_gemini(
        self, 
        prompt: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Generate blog draft using Gemini API"""
        if not self.gemini_client:
            raise RuntimeError("Gemini client not initialized")
        
        # Enhanced prompt for Gemini
        enhanced_prompt = f"""
        Write a comprehensive, engaging blog post based on the following topic:
        
        TOPIC: {prompt}
        
        Requirements:
        - Write in a professional, engaging tone
        - Include an attention-grabbing headline
        - Structure with clear headings and subheadings
        - Include introduction, main content sections, and conclusion
        - Aim for 800-1200 words
        - Use bullet points and numbered lists where appropriate
        - Include a call-to-action at the end
        - Make it SEO-friendly with natural keyword usage
        
        Format the response as:
        TITLE: [Your blog title here]
        
        [Your blog content here with proper formatting]
        """
        
        try:
            response = await self.gemini_client.generate_content(
                enhanced_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get('temperature', 0.7),
                    top_p=kwargs.get('top_p', 1.0),
                    top_k=kwargs.get('top_k', 40),
                    max_output_tokens=kwargs.get('max_tokens', 2000)
                )
            )
            
            content = response.text
            
            # Extract title and content
            title = ""
            blog_content = content
            
            if "TITLE:" in content:
                title_part, content_part = content.split("TITLE:", 1)
                title = title_part.strip()
                blog_content = content_part.strip()
            
            return {
                "title": title or f"Blog about {prompt}",
                "content": blog_content,
                "model": "gemini-pro",
                "tokens_used": len(content.split()),  # Approximate token count
                "model_provider": "gemini"
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def generate_multiple_blogs(
        self,
        prompt: str,
        num_blogs: int,
        ai_model: str = "openai",
        ai_model_version: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple blog drafts
        
        Args:
            prompt: The blog generation prompt
            num_blogs: Number of blogs to generate
            ai_model: Either 'openai' or 'gemini'
            ai_model_version: Specific model version
            **kwargs: Additional parameters for the AI model
            
        Returns:
            List of generated blog drafts
        """
        blogs = []
        
        for i in range(num_blogs):
            try:
                # Add variation to prompt for different blogs
                varied_prompt = f"{prompt} (Blog {i+1} of {num_blogs})"
                
                blog_draft = await self.generate_blog_draft(
                    varied_prompt, 
                    ai_model, 
                    ai_model_version, 
                    **kwargs
                )
                
                blogs.append(blog_draft)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error generating blog {i+1}: {e}")
                # Continue with other blogs even if one fails
                continue
        
        return blogs
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available AI models for each provider"""
        models = {
            "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
            "gemini": ["gemini-pro", "gemini-pro-vision"]
        }
        
        # Filter based on available clients
        if not self.openai_client:
            models["openai"] = []
        if not self.gemini_client:
            models["gemini"] = []
            
        return models
    
    def is_model_available(self, ai_model: str, model_version: Optional[str] = None) -> bool:
        """Check if a specific AI model is available"""
        if ai_model.lower() == "openai":
            return self.openai_client is not None
        elif ai_model.lower() == "gemini":
            return self.gemini_client is not None
        return False

# Create global AI client instance
ai_client = AIClient()
