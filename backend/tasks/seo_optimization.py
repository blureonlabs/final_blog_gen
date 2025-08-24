from celery import shared_task
from typing import Dict, List, Any
import logging
import re
from datetime import datetime

from core.supabase_client import supabase_client
from models.blog import BlogStatus

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="optimize_seo")
def optimize_seo_task(self, blog_id: str):
    """
    Optimize blog content for SEO
    
    Args:
        blog_id: Blog UUID as string
    """
    try:
        logger.info(f"Starting SEO optimization for blog {blog_id}")
        
        # Get blog data
        blog_data = get_blog_data(blog_id)
        if not blog_data:
            logger.error(f"Blog {blog_id} not found")
            return
        
        # Update status to SEO optimizing
        update_blog_status(blog_id, BlogStatus.SEO_OPTIMIZING)
        
        # Extract content and title
        content = blog_data.get("content", "")
        title = blog_data.get("title", "")
        
        # Generate SEO metadata
        seo_meta = generate_seo_metadata(title, content)
        
        # Optimize content structure
        optimized_content = optimize_content_structure(content)
        
        # Add internal/external links suggestions
        link_suggestions = generate_link_suggestions(content, title)
        
        # Update blog with SEO optimizations
        update_blog_seo(blog_id, seo_meta, optimized_content, link_suggestions)
        
        # Update status to formatting
        update_blog_status(blog_id, BlogStatus.FORMATTING)
        
        logger.info(f"SEO optimization completed for blog {blog_id}")
        
        return {
            "blog_id": blog_id,
            "status": "seo_optimized",
            "seo_meta": seo_meta,
            "link_suggestions": link_suggestions
        }
        
    except Exception as e:
        logger.error(f"Error in SEO optimization for blog {blog_id}: {e}")
        update_blog_status(blog_id, BlogStatus.FAILED, str(e))
        raise

def generate_seo_metadata(title: str, content: str) -> Dict[str, Any]:
    """Generate comprehensive SEO metadata"""
    try:
        # Extract main keyword from title
        main_keyword = extract_main_keyword(title)
        
        # Generate meta description
        meta_description = generate_meta_description(content, main_keyword)
        
        # Generate slug
        slug = generate_slug(title)
        
        # Extract headings for structure
        headings = extract_headings(content)
        
        # Calculate reading time
        reading_time = calculate_reading_time(content)
        
        # Generate tags based on content
        tags = generate_content_tags(content, title)
        
        seo_meta = {
            "title": title,
            "meta_description": meta_description,
            "slug": slug,
            "main_keyword": main_keyword,
            "headings": headings,
            "reading_time": reading_time,
            "tags": tags,
            "word_count": len(content.split()),
            "keyword_density": calculate_keyword_density(content, main_keyword),
            "seo_score": calculate_seo_score(content, title, meta_description),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return seo_meta
        
    except Exception as e:
        logger.error(f"Error generating SEO metadata: {e}")
        return {}

def extract_main_keyword(title: str) -> str:
    """Extract main keyword from title"""
    # Remove common words and extract meaningful terms
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    
    words = re.findall(r'\b\w+\b', title.lower())
    meaningful_words = [word for word in words if word not in stop_words and len(word) > 3]
    
    if meaningful_words:
        return meaningful_words[0]
    
    return "blog"

def generate_meta_description(content: str, main_keyword: str) -> str:
    """Generate meta description from content"""
    # Take first 150 characters and ensure it ends at a word boundary
    if len(content) <= 150:
        return content
    
    # Find the last space within 150 characters
    truncated = content[:150]
    last_space = truncated.rfind(' ')
    
    if last_space > 100:  # Only truncate if we have enough content
        truncated = truncated[:last_space]
    
    # Ensure main keyword is included if possible
    if main_keyword.lower() not in truncated.lower():
        # Try to include keyword by extending slightly
        keyword_pos = content.lower().find(main_keyword.lower())
        if keyword_pos != -1 and keyword_pos < 200:
            end_pos = min(keyword_pos + 150, len(content))
            truncated = content[:end_pos]
            last_space = truncated.rfind(' ')
            if last_space > 100:
                truncated = truncated[:last_space]
    
    return truncated + "..."

def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    # Convert to lowercase and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def extract_headings(content: str) -> List[Dict[str, str]]:
    """Extract headings from content for structure analysis"""
    headings = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            heading_text = line.lstrip('#').strip()
            headings.append({
                "level": level,
                "text": heading_text,
                "slug": generate_slug(heading_text)
            })
    
    return headings

def calculate_reading_time(content: str) -> int:
    """Calculate estimated reading time in minutes"""
    words = len(content.split())
    # Average reading speed: 200 words per minute
    reading_time = max(1, round(words / 200))
    return reading_time

def generate_content_tags(content: str, title: str) -> List[str]:
    """Generate relevant tags based on content"""
    # Combine title and content for analysis
    full_text = f"{title} {content}".lower()
    
    # Common content categories and their keywords
    categories = {
        "technology": ["tech", "software", "programming", "ai", "machine learning", "data"],
        "business": ["business", "marketing", "strategy", "management", "entrepreneurship"],
        "health": ["health", "fitness", "wellness", "nutrition", "exercise"],
        "lifestyle": ["lifestyle", "travel", "food", "fashion", "home"],
        "education": ["education", "learning", "teaching", "courses", "skills"]
    }
    
    tags = []
    for category, keywords in categories.items():
        if any(keyword in full_text for keyword in keywords):
            tags.append(category)
    
    # Add specific tags based on content
    if "how to" in title.lower() or "guide" in title.lower():
        tags.append("how-to")
    
    if "tips" in title.lower() or "advice" in title.lower():
        tags.append("tips")
    
    # Limit to 5 tags
    return tags[:5]

def calculate_keyword_density(content: str, keyword: str) -> float:
    """Calculate keyword density in content"""
    if not keyword or not content:
        return 0.0
    
    words = content.lower().split()
    keyword_count = content.lower().count(keyword.lower())
    
    if len(words) == 0:
        return 0.0
    
    density = (keyword_count / len(words)) * 100
    return round(density, 2)

def calculate_seo_score(content: str, title: str, meta_description: str) -> int:
    """Calculate overall SEO score (0-100)"""
    score = 0
    
    # Title length (optimal: 50-60 characters)
    title_length = len(title)
    if 50 <= title_length <= 60:
        score += 20
    elif 30 <= title_length <= 70:
        score += 15
    else:
        score += 5
    
    # Meta description length (optimal: 150-160 characters)
    desc_length = len(meta_description)
    if 150 <= desc_length <= 160:
        score += 20
    elif 120 <= desc_length <= 180:
        score += 15
    else:
        score += 5
    
    # Content length (minimum 300 words)
    word_count = len(content.split())
    if word_count >= 800:
        score += 20
    elif word_count >= 500:
        score += 15
    elif word_count >= 300:
        score += 10
    else:
        score += 5
    
    # Headings structure
    headings = extract_headings(content)
    if len(headings) >= 3:
        score += 20
    elif len(headings) >= 1:
        score += 10
    
    # Keyword in title
    if title and len(title.split()) > 0:
        score += 20
    
    return min(100, score)

def optimize_content_structure(content: str) -> str:
    """Optimize content structure for better readability"""
    lines = content.split('\n')
    optimized_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Ensure proper heading formatting
        if line.startswith('#'):
            # Ensure there's a space after #
            if not line.startswith('# '):
                line = line.replace('#', '# ', 1)
        
        # Add spacing around lists
        if line.startswith(('-', '*', '1.', '2.', '3.')):
            if optimized_lines and optimized_lines[-1] != '':
                optimized_lines.append('')
            optimized_lines.append(line)
            optimized_lines.append('')
        else:
            optimized_lines.append(line)
    
    return '\n'.join(optimized_lines)

def generate_link_suggestions(content: str, title: str) -> Dict[str, List[str]]:
    """Generate suggestions for internal and external links"""
    suggestions = {
        "internal_links": [],
        "external_links": [],
        "related_topics": []
    }
    
    # Extract potential topics for internal linking
    topics = extract_topics_from_content(content)
    suggestions["related_topics"] = topics[:5]
    
    # Suggest external resources based on content
    if any(word in content.lower() for word in ["research", "study", "data"]):
        suggestions["external_links"].append("Academic research papers")
    
    if any(word in content.lower() for word in ["tool", "software", "app"]):
        suggestions["external_links"].append("Product reviews and comparisons")
    
    if any(word in content.lower() for word in ["case study", "example", "success story"]):
        suggestions["external_links"].append("Industry case studies")
    
    return suggestions

def extract_topics_from_content(content: str) -> List[str]:
    """Extract potential topics for internal linking"""
    # Simple keyword extraction (could be enhanced with NLP)
    words = re.findall(r'\b\w+\b', content.lower())
    
    # Filter out common words and short words
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should"}
    
    meaningful_words = [word for word in words if word not in stop_words and len(word) > 4]
    
    # Count frequency and return top topics
    word_freq = {}
    for word in meaningful_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top words
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:10]]

def get_blog_data(blog_id: str) -> Dict[str, Any]:
    """Get blog data from database"""
    try:
        response = supabase_client.table("blogs").select("*").eq("id", blog_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching blog data: {e}")
        return None

def update_blog_status(blog_id: str, status: BlogStatus, error_message: str = None):
    """Update blog status in database"""
    try:
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if error_message:
            update_data["error_message"] = error_message
        
        response = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if not response.data:
            logger.error(f"Failed to update blog {blog_id} status")
            
    except Exception as e:
        logger.error(f"Error updating blog status: {e}")

def update_blog_seo(blog_id: str, seo_meta: Dict, optimized_content: str, link_suggestions: Dict):
    """Update blog with SEO optimizations"""
    try:
        update_data = {
            "seo_meta": seo_meta,
            "content": optimized_content,
            "generation_logs": [{
                "step": "seo_optimization",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
                "seo_score": seo_meta.get("seo_score", 0)
            }],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if not response.data:
            logger.error(f"Failed to update blog {blog_id} SEO data")
            
    except Exception as e:
        logger.error(f"Error updating blog SEO: {e}")
