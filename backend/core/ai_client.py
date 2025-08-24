import openai
import google.generativeai as genai
from typing import Dict, List, Optional, Literal
import logging
from core.config import settings
import os

logger = logging.getLogger(__name__)

class AIClient:
    """AI client that can switch between OpenAI and Gemini APIs"""
    
    def __init__(self):
        self.openai_client = None
        self.gemini_client = None
        self._setup_clients()
    
    def _setup_clients(self):
        """Setup OpenAI and Gemini clients"""
        # Setup OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai
            logger.info("OpenAI client initialized")
        
        # Setup Gemini
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_client = genai
            logger.info("Gemini client initialized")
    
    async def generate_blog_draft(
        self, 
        prompt: str, 
        model: Literal["openai", "gemini"] = "openai",
        **kwargs
    ) -> Dict:
        """
        Generate a blog draft using specified AI model
        
        Args:
            prompt: Blog generation prompt
            model: AI model to use ("openai" or "gemini")
            **kwargs: Additional parameters for the AI model
        
        Returns:
            Dict containing generated content and metadata
        """
        try:
            if model == "openai":
                return await self._generate_with_openai(prompt, **kwargs)
            elif model == "gemini":
                return await self._generate_with_gemini(prompt, **kwargs)
            else:
                raise ValueError(f"Unsupported model: {model}")
        except Exception as e:
            logger.error(f"Error generating blog draft with {model}: {e}")
            raise
    
    async def _generate_with_openai(self, prompt: str, **kwargs) -> Dict:
        """Generate blog draft using OpenAI"""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        # Default parameters
        default_params = {
            "model": "gpt-4",
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        # Override with provided kwargs
        params = {**default_params, **kwargs}
        
        # Enhanced prompt for better blog generation
        enhanced_prompt = f"""
        Write a comprehensive, engaging blog post based on the following prompt:
        
        {prompt}
        
        Requirements:
        - Write in a professional, engaging tone
        - Include a compelling headline
        - Structure with clear sections and subheadings
        - Include relevant examples and insights
        - End with a strong conclusion
        - Target length: 800-1200 words
        - Use markdown formatting for structure
        
        Blog Post:
        """
        
        response = self.openai_client.ChatCompletion.create(
            messages=[
                {"role": "system", "content": "You are an expert content writer specializing in creating engaging, informative blog posts."},
                {"role": "user", "content": enhanced_prompt}
            ],
            **params
        )
        
        content = response.choices[0].message.content
        
        return {
            "content": content,
            "model": "openai",
            "model_version": params["model"],
            "tokens_used": response.usage.total_tokens,
            "finish_reason": response.choices[0].finish_reason
        }
    
    async def _generate_with_gemini(self, prompt: str, **kwargs) -> Dict:
        """Generate blog draft using Gemini"""
        if not self.gemini_client:
            raise RuntimeError("Gemini client not initialized")
        
        # Default parameters
        default_params = {
            "model": "gemini-pro",
            "temperature": 0.7,
            "top_p": 1.0,
            "top_k": 40,
            "max_output_tokens": 2000
        }
        
        # Override with provided kwargs
        params = {**default_params, **kwargs}
        
        # Enhanced prompt for better blog generation
        enhanced_prompt = f"""
        Write a comprehensive, engaging blog post based on the following prompt:
        
        {prompt}
        
        Requirements:
        - Write in a professional, engaging tone
        - Include a compelling headline
        - Structure with clear sections and subheadings
        - Include relevant examples and insights
        - End with a strong conclusion
        - Target length: 800-1200 words
        - Use markdown formatting for structure
        
        Blog Post:
        """
        
        model = self.gemini_client.GenerativeModel(
            model_name=params["model"],
            generation_config=self.gemini_client.types.GenerationConfig(
                temperature=params["temperature"],
                top_p=params["top_p"],
                top_k=params["top_k"],
                max_output_tokens=params["max_output_tokens"]
            )
        )
        
        response = model.generate_content(enhanced_prompt)
        
        return {
            "content": response.text,
            "model": "gemini",
            "model_version": params["model"],
            "finish_reason": "stop" if response.candidates[0].finish_reason == 1 else "other"
        }
    
    async def refine_blog_content(
        self, 
        content: str, 
        instructions: str,
        model: Literal["openai", "gemini"] = "openai",
        **kwargs
    ) -> Dict:
        """
        Refine existing blog content based on instructions
        
        Args:
            content: Original blog content
            instructions: Refinement instructions
            model: AI model to use
            **kwargs: Additional parameters
        
        Returns:
            Dict containing refined content
        """
        try:
            if model == "openai":
                return await self._refine_with_openai(content, instructions, **kwargs)
            elif model == "gemini":
                return await self._refine_with_gemini(content, instructions, **kwargs)
            else:
                raise ValueError(f"Unsupported model: {model}")
        except Exception as e:
            logger.error(f"Error refining blog content with {model}: {e}")
            raise
    
    async def _refine_with_openai(self, content: str, instructions: str, **kwargs) -> Dict:
        """Refine content using OpenAI"""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        refinement_prompt = f"""
        Please refine the following blog content based on these instructions:
        
        Instructions: {instructions}
        
        Original Content:
        {content}
        
        Refined Content:
        """
        
        response = self.openai_client.ChatCompletion.create(
            messages=[
                {"role": "system", "content": "You are an expert content editor who can improve blog posts based on specific instructions."},
                {"role": "user", "content": refinement_prompt}
            ],
            model="gpt-4",
            max_tokens=2500,
            temperature=0.3,
            **kwargs
        )
        
        refined_content = response.choices[0].message.content
        
        return {
            "original_content": content,
            "refined_content": refined_content,
            "instructions": instructions,
            "model": "openai",
            "tokens_used": response.usage.total_tokens
        }
    
    async def _refine_with_gemini(self, content: str, instructions: str, **kwargs) -> Dict:
        """Refine content using Gemini"""
        if not self.gemini_client:
            raise RuntimeError("Gemini client not initialized")
        
        refinement_prompt = f"""
        Please refine the following blog content based on these instructions:
        
        Instructions: {instructions}
        
        Original Content:
        {content}
        
        Refined Content:
        """
        
        model = self.gemini_client.GenerativeModel("gemini-pro")
        response = model.generate_content(refinement_prompt)
        
        return {
            "original_content": content,
            "refined_content": response.text,
            "instructions": instructions,
            "model": "gemini"
        }
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models for each AI provider"""
        models = {}
        
        if self.openai_client:
            models["openai"] = ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
        
        if self.gemini_client:
            models["gemini"] = ["gemini-pro", "gemini-pro-vision"]
        
        return models
    
    def is_model_available(self, model: str) -> bool:
        """Check if a specific model is available"""
        available_models = self.get_available_models()
        
        for provider, models_list in available_models.items():
            if model in models_list:
                return True
        
        return False

# Global AI client instance
ai_client = AIClient()
