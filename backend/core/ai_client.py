import openai
import google.generativeai as genai  # Enable Gemini
from typing import Dict, Any, Optional, List
import asyncio
import logging
from .config import settings
from datetime import datetime

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
                logger.info("✅ OpenAI client initialized successfully")
            else:
                logger.warning("⚠️ OpenAI API key not found")
                
            # Enable Gemini client
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_client = genai.GenerativeModel('gemini-2.0-flash')  # Updated to Gemini 2.0 Flash
                logger.info("✅ Gemini client initialized successfully with gemini-2.0-flash")
            else:
                logger.warning("⚠️ Gemini API key not found")
                
        except Exception as e:
            logger.error(f"❌ Error initializing AI clients: {e}")
    
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
                logger.warning("Gemini is disabled - falling back to OpenAI")
                return await self._generate_with_openai(prompt, ai_model_version, **kwargs)
            else:
                raise ValueError(f"Unsupported AI model: {ai_model}")
                
        except Exception as e:
            logger.error(f"Error generating blog draft with {ai_model}: {e}")
            raise
    
    async def _generate_with_openai(
        self, 
        prompt: str, 
        model_version: Optional[str] = None,
        max_completion_tokens: int = 2000,  # Fixed: Use max_completion_tokens for GPT-5 Nano
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate blog draft using OpenAI API"""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        # Use specified model version or default to GPT-5 Nano
        model = model_version or "gpt-5-nano-2025-08-07"
        
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
            # Use the newer OpenAI API syntax for GPT-5 Nano compatibility
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": enhanced_prompt}],
                max_completion_tokens=max_completion_tokens,  # Fixed: Use max_completion_tokens for GPT-5 Nano
                temperature=temperature
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
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else len(content.split()),
                "model_provider": "openai"
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_with_gemini(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate content using Gemini API"""
        try:
            if not self.gemini_client:
                raise RuntimeError("Gemini client not initialized")
            
            logger.info(f"🚀 Generating content with Gemini Pro")
            logger.info(f"🔍 Prompt length: {len(prompt)} characters")
            logger.info(f"🔍 Temperature: {temperature}")
            logger.info(f"🔍 Max tokens: {max_tokens}")
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=min(max_tokens, 8192),  # Gemini's limit
                top_p=kwargs.get('top_p', 0.8),
                top_k=kwargs.get('top_k', 40)
            )
            
            # Generate content
            response = self.gemini_client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            content = response.text
            
            # Extract title and content if structured
            title = ""
            blog_content = content
            
            if "TITLE:" in content:
                title_part, content_part = content.split("TITLE:", 1)
                title = title_part.strip()
                blog_content = content_part.strip()
            
            logger.info(f"✅ Gemini generation completed")
            logger.info(f"🔍 Generated content length: {len(blog_content)} characters")
            logger.info(f"🔍 Title: {title or 'Not specified'}")
            
            return {
                "title": title or f"Blog about {prompt[:50]}...",
                "content": blog_content,
                "model": "gemini-2.0-flash",  # Updated model name
                "tokens_used": len(content.split()),  # Approximate token count
                "model_provider": "gemini",
                "generation_config": {
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "top_p": kwargs.get('top_p', 0.8),
                    "top_k": kwargs.get('top_k', 40)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
            raise
    
    async def generate_content(
        self,
        prompt: str,
        model: str = "openai",
        max_completion_tokens: int = 2000,  # Fixed: Use max_completion_tokens for GPT-5 Nano
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate content using the specified AI model
        
        Args:
            prompt: The content generation prompt
            model: Either 'openai' or 'gemini'
            max_completion_tokens: Maximum tokens to generate (GPT-5 Nano compatible)
            temperature: Creativity level (0.0 to 1.0)
            **kwargs: Additional parameters
            
        Returns:
            Generated content as string
        """
        try:
            if model.lower() == "openai":
                if not self.openai_client:
                    raise RuntimeError("OpenAI client not initialized")
                result = await self._generate_with_openai(prompt, max_completion_tokens=max_completion_tokens, temperature=temperature, **kwargs)
                return result.get("content", result.get("title", ""))
            elif model.lower() == "gemini":
                if not self.gemini_client:
                    raise RuntimeError("Gemini client not initialized")
                result = await self._generate_with_gemini(prompt, max_tokens=max_completion_tokens, temperature=temperature, **kwargs)
                return result.get("content", result.get("title", ""))
            else:
                raise ValueError(f"Unsupported AI model: {model}")
                
        except Exception as e:
            logger.error(f"❌ Error generating content with {model}: {e}")
            raise

    async def vet_content(
        self,
        content: str,
        title: str,
        project_description: str,
        vetting_model: str = "openai",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Vet generated content for quality, accuracy, and adherence to project requirements
        
        Args:
            content: The blog content to vet
            title: The blog title
            project_description: Project description for context
            vetting_model: Either 'openai' or 'gemini'
            **kwargs: Additional parameters
            
        Returns:
            Dict containing vetting results and recommendations
        """
        try:
            vetting_prompt = f"""
            Please review and vet the following blog content for quality and adherence to project requirements:
            
            PROJECT DESCRIPTION: {project_description}
            BLOG TITLE: {title}
            BLOG CONTENT: {content}
            
            Please evaluate the following aspects and provide a comprehensive review:
            
            1. Content Quality (1-10):
               - Relevance to project topic
               - Writing clarity and engagement
               - Structure and flow
            
            2. SEO Optimization (1-10):
               - Keyword usage and density
               - Title optimization
               - Meta description potential
            
            3. Technical Requirements (1-10):
               - Word count appropriateness
               - Heading structure
               - Readability score
            
            4. Overall Score (1-10):
               - Combined assessment
            
            5. Recommendations:
               - Specific improvements needed
               - Areas of strength
               - Action items for enhancement
            
            Please provide your evaluation in this exact format:
            SCORE: [overall_score]/10
            QUALITY: [content_quality]/10
            SEO: [seo_score]/10
            TECHNICAL: [technical_score]/10
            RECOMMENDATIONS: [detailed recommendations]
            """
            
            if vetting_model.lower() == "openai":
                if not self.openai_client:
                    raise RuntimeError("OpenAI client not initialized for vetting")
                result = await self._generate_with_openai(vetting_prompt, max_completion_tokens=1000, temperature=0.3, **kwargs)
            elif vetting_model.lower() == "gemini":
                if not self.gemini_client:
                    raise RuntimeError("Gemini client not initialized for vetting")
                result = await self._generate_with_gemini(vetting_prompt, max_tokens=1000, temperature=0.3, **kwargs)
            else:
                raise ValueError(f"Unsupported vetting model: {vetting_model}")
            
            vetting_response = result.get("content", result.get("title", ""))
            
            # Parse the vetting response
            vetting_result = self._parse_vetting_response(vetting_response)
            
            return {
                "vetting_model": vetting_model,
                "vetting_response": vetting_response,
                "parsed_results": vetting_result,
                "passed": vetting_result.get("overall_score", 0) >= 7,  # Pass threshold of 7/10
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error vetting content with {vetting_model}: {e}")
            # Return a default vetting result on error
            return {
                "vetting_model": vetting_model,
                "vetting_response": "Vetting failed due to error",
                "parsed_results": {"overall_score": 0, "error": str(e)},
                "passed": False,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _parse_vetting_response(self, response: str) -> Dict[str, Any]:
        """Parse the structured vetting response from AI"""
        try:
            lines = response.split('\n')
            results = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('SCORE:'):
                    results['overall_score'] = int(line.split(':')[1].split('/')[0].strip())
                elif line.startswith('QUALITY:'):
                    results['content_quality'] = int(line.split(':')[1].split('/')[0].strip())
                elif line.startswith('SEO:'):
                    results['seo_score'] = int(line.split(':')[1].split('/')[0].strip())
                elif line.startswith('TECHNICAL:'):
                    results['technical_score'] = int(line.split(':')[1].split('/')[0].strip())
                elif line.startswith('RECOMMENDATIONS:'):
                    results['recommendations'] = line.split(':', 1)[1].strip()
            
            return results
        except Exception as e:
            logger.error(f"Error parsing vetting response: {e}")
            return {"overall_score": 0, "error": "Failed to parse vetting response"}
    
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
                # Create completely independent prompts for each blog
                # Add subtle variation without referencing series
                variation_keywords = [
                    "comprehensive", "detailed", "in-depth", "thorough", "extensive",
                    "complete", "exhaustive", "systematic", "methodical", "analytical"
                ]
                variation = variation_keywords[i % len(variation_keywords)]
                
                varied_prompt = f"{prompt} (Create a {variation} and unique perspective)"
                
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
            "openai": ["gpt-5-nano-2025-08-07", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],  # Updated with GPT-5 Nano
            "gemini": ["gemini-2.0-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
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
