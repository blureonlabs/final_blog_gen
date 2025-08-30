import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TextCleaner:
    """
    Utility class for cleaning blog content by removing only # and * characters
    while preserving all other content and formatting.
    """

    @staticmethod
    def clean_blog_content(content: str) -> str:
        """
        Remove only # and * characters from blog content.
        
        Args:
            content (str): The original blog content
            
        Returns:
            str: Content with # and * characters removed
        """
        if not content:
            return content
        
        # Remove only # and * characters
        cleaned = content.replace('#', '').replace('*', '')
        
        logger.info(f"Cleaned blog content: removed # and * characters")
        return cleaned

    @staticmethod
    def clean_title(title: str) -> str:
        """
        Remove only # and * characters from blog titles.
        
        Args:
            title (str): The original blog title
            
        Returns:
            str: Title with # and * characters removed
        """
        if not title:
            return title
        
        # Remove only # and * characters
        cleaned = title.replace('#', '').replace('*', '')
        
        logger.info(f"Cleaned title: removed # and * characters")
        return cleaned

    @staticmethod
    def clean_prompt(prompt: str) -> str:
        """
        Remove only # and * characters from prompts.
        
        Args:
            prompt (str): The original prompt
            
        Returns:
            str: Prompt with # and * characters removed
        """
        if not prompt:
            return prompt
        
        # Remove only # and * characters
        cleaned = prompt.replace('#', '').replace('*', '')
        
        logger.info(f"Cleaned prompt: removed # and * characters")
        return cleaned
    
    @staticmethod
    def validate_cleaned_content(content: str, original_length: int) -> bool:
        """
        Validate that cleaned content meets quality standards.
        
        Args:
            content: Cleaned content to validate
            original_length: Length of original content
            
        Returns:
            True if content is valid, False otherwise
        """
        if not content:
            return False
        
        # Check minimum length
        if len(content) < 50:
            return False
        
        # Check if cleaning removed too much content
        if original_length > 0:
            cleaning_ratio = len(content) / original_length
            if cleaning_ratio < 0.7:  # Lost more than 30% of content
                return False
        
        # Check if content has meaningful text
        word_count = len(content.split())
        if word_count < 10:
            return False
        
        return True
