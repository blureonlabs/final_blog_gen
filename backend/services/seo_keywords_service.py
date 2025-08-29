import logging
from typing import List, Optional
from core.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class SEOKeywordsService:
    """Simple service to extract and store SEO keywords"""
    
    @staticmethod
    def extract_seo_keywords(project_id: str) -> bool:
        """
        Extract SEO keywords from serp_api_contents and store in extracted_seo_keywords column
        
        Args:
            project_id: Project UUID as string
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"🔍 Extracting SEO keywords for project {project_id}")
            
            # Get project data
            project_response = supabase_client.table("projects").select("serp_api_contents").eq("id", project_id).execute()
            
            if not project_response.data:
                logger.error(f"❌ Project {project_id} not found")
                return False
            
            project = project_response.data[0]
            serp_contents = project.get("serp_api_contents")
            
            logger.info(f"🔍 Raw serp_contents type: {type(serp_contents)}")
            logger.info(f"🔍 Raw serp_contents preview: {str(serp_contents)[:200]}...")
            
            if not serp_contents:
                logger.warning(f"⚠️ No SerpAPI contents found for project {project_id}")
                return False
            
            # Handle serp_contents - it might be a string that needs parsing
            if isinstance(serp_contents, str):
                try:
                    import json
                    serp_contents = json.loads(serp_contents)
                    logger.info(f"✅ Parsed serp_api_contents from string to JSON")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse serp_api_contents JSON: {e}")
                    return False
            elif not isinstance(serp_contents, dict):
                logger.error(f"❌ serp_api_contents is neither string nor dict: {type(serp_contents)}")
                return False
            
            # Extract SEO keywords
            seo_keywords = serp_contents.get("seo_keywords", [])
            
            if not seo_keywords or not isinstance(seo_keywords, list):
                logger.warning(f"⚠️ No valid SEO keywords found in project {project_id}")
                return False
            
            logger.info(f"✅ Found {len(seo_keywords)} SEO keywords for project {project_id}")
            
            # Store extracted keywords in new column
            update_response = supabase_client.table("projects").update({
                "extracted_seo_keywords": seo_keywords
            }).eq("id", project_id).execute()
            
            if update_response.data:
                logger.info(f"✅ SEO keywords stored successfully for project {project_id}")
                return True
            else:
                logger.error(f"❌ Failed to store SEO keywords for project {project_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error extracting SEO keywords for project {project_id}: {e}")
            return False
    
    @staticmethod
    def get_extracted_seo_keywords(project_id: str) -> Optional[List[str]]:
        """
        Get extracted SEO keywords from the new column
        
        Args:
            project_id: Project UUID as string
            
        Returns:
            List of SEO keywords or None if not found
        """
        try:
            project_response = supabase_client.table("projects").select("extracted_seo_keywords").eq("id", project_id).execute()
            
            if not project_response.data:
                return None
            
            project = project_response.data[0]
            return project.get("extracted_seo_keywords", [])
            
        except Exception as e:
            logger.error(f"❌ Error getting extracted SEO keywords for project {project_id}: {e}")
            return None
