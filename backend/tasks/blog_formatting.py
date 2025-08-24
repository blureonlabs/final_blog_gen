from celery import shared_task
from typing import Dict, List, Any
import logging
import re
from datetime import datetime

from core.supabase_client import supabase_client
from models.blog import BlogStatus

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="format_blog")
def format_blog_task(self, blog_id: str):
    """
    Format blog content with TOC, FAQs, CTAs, and proper structure
    
    Args:
        blog_id: Blog UUID as string
    """
    try:
        logger.info(f"Starting blog formatting for blog {blog_id}")
        
        # Get blog data
        blog_data = get_blog_data(blog_id)
        if not blog_data:
            logger.error(f"Blog {blog_id} not found")
            return
        
        # Update status to formatting
        update_blog_status(blog_id, BlogStatus.FORMATTING)
        
        # Extract content and SEO data
        content = blog_data.get("content", "")
        seo_meta = blog_data.get("seo_meta", {})
        
        # Generate table of contents
        toc = generate_table_of_contents(content)
        
        # Add FAQ section
        faq_section = generate_faq_section(content, seo_meta)
        
        # Add call-to-action sections
        content_with_ctas = add_call_to_actions(content)
        
        # Add related posts section
        related_section = generate_related_posts_section(seo_meta)
        
        # Combine all sections
        formatted_content = combine_formatted_sections(
            toc, content_with_ctas, faq_section, related_section
        )
        
        # Update blog with formatted content
        update_blog_formatting(blog_id, formatted_content, toc, faq_section)
        
        # Update status to image generation
        update_blog_status(blog_id, BlogStatus.IMAGE_GENERATING)
        
        logger.info(f"Blog formatting completed for blog {blog_id}")
        
        return {
            "blog_id": blog_id,
            "status": "formatted",
            "toc_items": len(toc),
            "faq_count": len(faq_section),
            "content_length": len(formatted_content)
        }
        
    except Exception as e:
        logger.error(f"Error in blog formatting for blog {blog_id}: {e}")
        update_blog_status(blog_id, BlogStatus.FAILED, str(e))
        raise

def generate_table_of_contents(content: str) -> List[Dict[str, str]]:
    """Generate table of contents from content headings"""
    toc = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            heading_text = line.lstrip('#').strip()
            
            # Skip if heading is too short or too long
            if len(heading_text) < 3 or len(heading_text) > 100:
                continue
            
            toc.append({
                "level": level,
                "text": heading_text,
                "slug": generate_heading_slug(heading_text),
                "indent": "  " * (level - 1) if level > 1 else ""
            })
    
    return toc

def generate_heading_slug(heading: str) -> str:
    """Generate slug for heading"""
    # Convert to lowercase and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', heading.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def generate_faq_section(content: str, seo_meta: Dict) -> List[Dict[str, str]]:
    """Generate FAQ section based on content and SEO data"""
    faqs = []
    
    # Extract main topic from SEO data
    main_topic = seo_meta.get("main_keyword", "this topic")
    
    # Generate relevant FAQs based on content type
    if "how to" in content.lower() or "guide" in content.lower():
        faqs.extend([
            {
                "question": f"What is the best way to approach {main_topic}?",
                "answer": f"The best approach to {main_topic} depends on your specific needs and circumstances. This guide provides a comprehensive framework to help you get started."
            },
            {
                "question": f"How long does it take to master {main_topic}?",
                "answer": f"Mastering {main_topic} is a journey that varies for each individual. With consistent practice and the right approach, you can see significant progress within weeks to months."
            },
            {
                "question": f"What are the most common mistakes when learning {main_topic}?",
                "answer": f"Common mistakes include rushing the process, skipping fundamentals, and not practicing consistently. This guide helps you avoid these pitfalls."
            }
        ])
    
    elif "tips" in content.lower() or "advice" in content.lower():
        faqs.extend([
            {
                "question": f"Why are these {main_topic} tips important?",
                "answer": f"These tips are based on proven strategies and real-world experience. They help you navigate {main_topic} more effectively and avoid common pitfalls."
            },
            {
                "question": f"How can I implement these {main_topic} strategies?",
                "answer": f"Start with one or two strategies that resonate with you, practice them consistently, and gradually incorporate more as you become comfortable."
            }
        ])
    
    else:
        # Generic FAQs for informational content
        faqs.extend([
            {
                "question": f"What makes {main_topic} important?",
                "answer": f"{main_topic} plays a crucial role in modern business and technology. Understanding it can give you a competitive advantage and open new opportunities."
            },
            {
                "question": f"How does {main_topic} relate to current trends?",
                "answer": f"{main_topic} is closely connected to emerging technologies and market demands. Staying updated on this topic can help you anticipate future developments."
            }
        ])
    
    return faqs

def add_call_to_actions(content: str) -> str:
    """Add strategic call-to-action sections throughout the content"""
    lines = content.split('\n')
    enhanced_lines = []
    
    # Track paragraph count to add CTAs at strategic points
    paragraph_count = 0
    cta_added = False
    
    for line in lines:
        enhanced_lines.append(line)
        
        # Count paragraphs (non-empty lines that aren't headings)
        if line.strip() and not line.strip().startswith('#'):
            paragraph_count += 1
            
            # Add CTA after every 3-4 paragraphs
            if paragraph_count % 4 == 0 and not cta_added:
                cta = generate_contextual_cta(line.strip())
                if cta:
                    enhanced_lines.append("")
                    enhanced_lines.append(cta)
                    enhanced_lines.append("")
                    cta_added = True
            elif paragraph_count % 8 == 0:
                cta_added = False
    
    # Add final CTA at the end
    final_cta = generate_final_cta()
    enhanced_lines.append("")
    enhanced_lines.append(final_cta)
    
    return '\n'.join(enhanced_lines)

def generate_contextual_cta(context: str) -> str:
    """Generate contextual CTA based on content"""
    context_lower = context.lower()
    
    if any(word in context_lower for word in ["learn", "understand", "discover"]):
        return "**💡 Ready to dive deeper?** Explore our comprehensive resources on this topic and take your knowledge to the next level."
    
    elif any(word in context_lower for word in ["implement", "apply", "use"]):
        return "**🚀 Ready to put this into action?** Start implementing these strategies today and see the results for yourself."
    
    elif any(word in context_lower for word in ["problem", "challenge", "issue"]):
        return "**🔧 Facing similar challenges?** Get personalized guidance and solutions tailored to your specific situation."
    
    else:
        return "**📚 Want to learn more?** Continue reading to discover additional insights and practical applications."

def generate_final_cta() -> str:
    """Generate final call-to-action for the blog"""
    return """## 🎯 Take Action Today

**Ready to transform your approach?** Here's what you can do right now:

1. **📝 Review the key points** from this article
2. **🎯 Choose one strategy** to implement this week
3. **📊 Track your progress** and measure results
4. **🔄 Iterate and improve** based on what you learn

**💬 Share your experience:** What strategies worked best for you? Leave a comment below and help others on their journey.

**📧 Stay updated:** Subscribe to our newsletter for more insights and tips delivered straight to your inbox."""

def generate_related_posts_section(seo_meta: Dict) -> str:
    """Generate related posts section"""
    main_topic = seo_meta.get("main_keyword", "this topic")
    tags = seo_meta.get("tags", [])
    
    related_section = f"""## 🔗 Related Articles

**Want to explore more about {main_topic}?** Check out these related articles:"""
    
    # Add placeholder related posts (in real implementation, these would be actual related posts)
    if tags:
        for tag in tags[:3]:
            related_section += f"\n- **{tag.title()}**: Discover the latest trends and strategies in {tag}"
    
    related_section += f"""

**📚 Browse our complete collection** of articles on {main_topic} and related topics to continue your learning journey."""
    
    return related_section

def combine_formatted_sections(toc: List[Dict], content: str, faq_section: List[Dict], 
                             related_section: str) -> str:
    """Combine all formatted sections into final content"""
    sections = []
    
    # Add table of contents if we have headings
    if toc:
        toc_text = "## 📋 Table of Contents\n\n"
        for item in toc:
            toc_text += f"{item['indent']}- [{item['text']}](#{item['slug']})\n"
        sections.append(toc_text)
    
    # Add main content
    sections.append(content)
    
    # Add FAQ section
    if faq_section:
        faq_text = "\n## ❓ Frequently Asked Questions\n\n"
        for i, faq in enumerate(faq_section, 1):
            faq_text += f"### Q{i}: {faq['question']}\n\n"
            faq_text += f"{faq['answer']}\n\n"
        sections.append(faq_text)
    
    # Add related posts section
    if related_section:
        sections.append(related_section)
    
    return '\n\n'.join(sections)

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

def update_blog_formatting(blog_id: str, formatted_content: str, toc: List[Dict], 
                          faq_section: List[Dict]):
    """Update blog with formatted content"""
    try:
        # Update generation logs
        current_logs = get_current_generation_logs(blog_id)
        current_logs.append({
            "step": "blog_formatting",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "toc_items": len(toc),
            "faq_count": len(faq_section)
        })
        
        update_data = {
            "content": formatted_content,
            "generation_logs": current_logs,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if not response.data:
            logger.error(f"Failed to update blog {blog_id} formatting")
            
    except Exception as e:
        logger.error(f"Error updating blog formatting: {e}")

def get_current_generation_logs(blog_id: str) -> List[Dict]:
    """Get current generation logs for the blog"""
    try:
        response = supabase_client.table("blogs").select("generation_logs").eq("id", blog_id).execute()
        if response.data and response.data[0].get("generation_logs"):
            return response.data[0]["generation_logs"]
        return []
    except Exception as e:
        logger.error(f"Error fetching generation logs: {e}")
        return []
