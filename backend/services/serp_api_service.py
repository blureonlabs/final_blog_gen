import asyncio
import logging
import json
import re
from typing import List, Dict, Any, Optional
import aiohttp
from urllib.parse import urlparse
import random

logger = logging.getLogger(__name__)

class SerpAPIService:
    def __init__(self):
        self.base_url = "https://serpapi.com/search"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def research_topic(self, topic: str, api_key: str, num_results: int = 10, enhanced_research: bool = False) -> Dict[str, Any]:
        """
        Research a topic using SerpAPI and return relevant content
        
        Args:
            topic: The topic to research
            api_key: SerpAPI key
            num_results: Number of search results to fetch
            enhanced_research: Whether to use enhanced research features (AI queries, external links, content scraping)
            
        Returns:
            Dictionary containing research results and summary
        """
        try:
            logger.info(f"🔍 Starting SerpAPI research for topic: {topic}")
            
            if enhanced_research:
                logger.info("🚀 Using enhanced research features")
                return await self._enhanced_research(topic, api_key, num_results)
            else:
                logger.info("📝 Using standard research features")
                return await self._standard_research(topic, api_key, num_results)
            
        except Exception as e:
            logger.error(f"❌ SerpAPI research failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "research_summary": "",
                "external_links": [],
                "key_insights": []
            }
    
    async def _standard_research(self, topic: str, api_key: str, num_results: int) -> Dict[str, Any]:
        """Standard research flow - maintains existing functionality"""
        # Generate search queries based on the topic
        search_queries = self._generate_search_queries(topic)
        logger.info(f"🔍 Generated {len(search_queries)} search queries")
        
        all_results = []
        
        # Research each query
        for i, query in enumerate(search_queries):
            logger.info(f"🔍 Researching query {i+1}/{len(search_queries)}: {query}")
            
            try:
                # Add delay between requests to respect rate limits
                if i > 0:
                    await asyncio.sleep(2)
                
                results = await self._search_serpapi(query, api_key, num_results)
                if results:
                    all_results.extend(results)
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to research query '{query}': {e}")
                continue
        
        if not all_results:
            logger.warning("⚠️ No research results found")
            return {
                "success": False,
                "error": "No research results found",
                "research_summary": "",
                "external_links": [],
                "key_insights": []
            }
        
        # Filter and process results
        filtered_results = self._filter_results(all_results)
        logger.info(f"✅ Found {len(filtered_results)} relevant results after filtering")
        
        # Extract key insights and create research summary
        research_summary = self._create_research_summary(topic, filtered_results)
        external_links = self._extract_external_links(filtered_results)
        key_insights = self._extract_key_insights(filtered_results)
        
        # Extract SEO keywords for content optimization
        seo_keywords = self._extract_seo_keywords(filtered_results, topic)
        
        return {
            "success": True,
            "research_summary": research_summary,
            "external_links": external_links,
            "key_insights": key_insights,
            "seo_keywords": seo_keywords,  # Add SEO keywords
            "total_results": len(filtered_results),
            "raw_results": filtered_results[:5]  # Include top 5 for reference
        }
    
    async def _enhanced_research(self, topic: str, api_key: str, num_results: int) -> Dict[str, Any]:
        """Enhanced research flow with AI-generated queries, external links, and content scraping"""
        logger.info("🚀 Starting enhanced research pipeline")
        
        # Phase 1: Generate AI-powered search queries
        ai_queries = self._generate_ai_search_queries(topic)
        logger.info(f"🤖 Generated {len(ai_queries)} AI-powered search queries")
        
        # Phase 2: Primary SerpAPI research
        primary_results = await self._research_multiple_queries(ai_queries, api_key, num_results)
        if not primary_results:
            logger.warning("⚠️ No primary research results found")
            return await self._standard_research(topic, api_key, num_results)
        
        # Phase 3: External links research (authoritative sites)
        external_links_results = await self._research_external_links(topic, api_key)
        logger.info(f"🔗 Found {len(external_links_results)} external link results")
        
        # Phase 4: Content scraping for deeper analysis
        enhanced_results = await self._enhance_with_content_scraping(primary_results)
        
        # Phase 5: Combine and process all results
        all_results = primary_results + external_links_results
        filtered_results = self._filter_results(all_results)
        
        # Create enhanced research summary
        research_summary = self._create_enhanced_research_summary(topic, filtered_results, enhanced_results)
        external_links = self._extract_enhanced_external_links(filtered_results, enhanced_results)
        key_insights = self._extract_enhanced_key_insights(filtered_results, enhanced_results)
        
        # Extract SEO keywords for content optimization
        seo_keywords = self._extract_seo_keywords(filtered_results, topic)
        
        return {
            "success": True,
            "research_summary": research_summary,
            "external_links": external_links,
            "key_insights": key_insights,
            "seo_keywords": seo_keywords,  # New SEO keywords field
            "total_results": len(filtered_results),
            "raw_results": filtered_results[:5],
            "enhanced_research": True,
            "content_analysis": enhanced_results
        }
    
    def _generate_search_queries(self, topic: str) -> List[str]:
        """Generate relevant search queries for the topic"""
        # Basic query generation - can be enhanced with AI later
        base_queries = [
            f"{topic} guide",
            f"{topic} tips",
            f"{topic} best practices",
            f"{topic} examples",
            f"{topic} tutorial",
            f"how to {topic}",
            f"{topic} for beginners"
        ]
        
        # Add industry-specific queries if topic contains business keywords
        business_keywords = ["business", "marketing", "sales", "startup", "entrepreneur", "company"]
        if any(keyword in topic.lower() for keyword in business_keywords):
            base_queries.extend([
                f"{topic} business strategy",
                f"{topic} marketing tips",
                f"{topic} industry trends"
            ])
        
        return base_queries[:5]  # Limit to 5 queries
    
    async def _search_serpapi(self, query: str, api_key: str, num_results: int) -> List[Dict[str, Any]]:
        """Search SerpAPI for a specific query"""
        try:
            params = {
                "q": query,
                "gl": "US",
                "api_key": api_key,
                "num": num_results,
                "engine": "google",
                "hl": "en"
            }
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"❌ SerpAPI request failed with status {response.status}")
                    return []
                
                data = await response.json()
                
                if "organic_results" not in data:
                    logger.warning(f"⚠️ No organic results in SerpAPI response")
                    return []
                
                return data["organic_results"]
                
        except Exception as e:
            logger.error(f"❌ SerpAPI search failed for query '{query}': {e}")
            return []
    
    def _filter_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out problematic results and keep only relevant ones"""
        problematic_domains = [
            'youtube.com', 'quora.com', 'medium.com', 'linkedin.com',
            'facebook.com', 'twitter.com', 'x.com', 'instagram.com',
            'reddit.com', 'pinterest.com', 'tiktok.com'
        ]
        
        filtered = []
        
        for result in results:
            try:
                # Check if result has required fields
                if not result.get("link") or not result.get("snippet"):
                    continue
                
                # Extract domain
                domain = self._extract_domain(result["link"])
                if not domain:
                    continue
                
                # Check against problematic domains
                if any(problematic in domain for problematic in problematic_domains):
                    continue
                
                # Check snippet length
                snippet = result.get("snippet", "")
                if len(snippet) < 100:
                    continue
                
                # Keep only essential fields
                filtered.append({
                    "title": result.get("title", ""),
                    "link": result["link"],
                    "snippet": snippet,
                    "domain": domain
                })
                
            except Exception as e:
                logger.warning(f"⚠️ Error filtering result: {e}")
                continue
        
        return filtered
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return None
    
    def _create_research_summary(self, topic: str, results: List[Dict[str, Any]]) -> str:
        """Create a research summary based on the filtered results"""
        if not results:
            return f"No research results found for '{topic}'."
        
        # Extract key information from results
        titles = [r["title"] for r in results[:5]]
        domains = [r["domain"] for r in results[:5]]
        
        summary = f"Research Summary for '{topic}':\n\n"
        summary += f"Found {len(results)} relevant sources covering various aspects of {topic}.\n\n"
        
        summary += "Key Sources:\n"
        for i, (title, domain) in enumerate(zip(titles, domains), 1):
            summary += f"{i}. {title} ({domain})\n"
        
        summary += f"\nResearch covers: {', '.join(set(domains))}\n"
        summary += f"Total relevant sources: {len(results)}"
        
        return summary
    
    def _extract_external_links(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract external links for the blog post"""
        links = []
        for result in results[:10]:  # Limit to top 10
            links.append({
                "title": result["title"],
                "url": result["link"],
                "description": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"]
            })
        return links
    
    def _extract_key_insights(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract key insights from the research results"""
        insights = []
        
        # Extract common themes from titles and snippets
        all_text = " ".join([r["title"] + " " + r["snippet"] for r in results])
        
        # Look for common patterns (this is a simple approach - can be enhanced with AI)
        common_patterns = [
            "best practices", "tips", "strategies", "trends", "benefits",
            "challenges", "solutions", "approaches", "methods", "techniques"
        ]
        
        for pattern in common_patterns:
            if pattern in all_text.lower():
                insights.append(f"Coverage of {pattern} related to the topic")
        
        # Add general insights
        if len(results) >= 5:
            insights.append("Comprehensive coverage from multiple sources")
        if len(set(r["domain"] for r in results)) >= 3:
            insights.append("Diverse perspectives from different websites")
        
        return insights[:5]  # Limit to 5 insights
    
    def _generate_ai_search_queries(self, topic: str) -> List[str]:
        """Generate AI-powered search queries based on topic context"""
        # Enhanced query generation with context awareness
        base_queries = [
            f"{topic} guide",
            f"{topic} tips",
            f"{topic} best practices",
            f"{topic} examples",
            f"{topic} tutorial",
            f"how to {topic}",
            f"{topic} for beginners",
            f"{topic} strategies",
            f"{topic} techniques",
            f"{topic} methods"
        ]
        
        # Add industry-specific queries
        business_keywords = ["business", "marketing", "sales", "startup", "entrepreneur", "company", "industry"]
        if any(keyword in topic.lower() for keyword in business_keywords):
            base_queries.extend([
                f"{topic} business strategy",
                f"{topic} marketing tips",
                f"{topic} industry trends",
                f"{topic} competitive analysis",
                f"{topic} market research"
            ])
        
        # Add technical queries for tech topics
        tech_keywords = ["software", "programming", "development", "technology", "digital", "online", "web"]
        if any(keyword in topic.lower() for keyword in tech_keywords):
            base_queries.extend([
                f"{topic} software solutions",
                f"{topic} development tools",
                f"{topic} technology trends",
                f"{topic} digital transformation"
            ])
        
        # Randomize and limit to 8 queries for enhanced research
        random.shuffle(base_queries)
        return base_queries[:8]
    
    async def _research_multiple_queries(self, queries: List[str], api_key: str, num_results: int) -> List[Dict[str, Any]]:
        """Research multiple queries with rate limiting"""
        all_results = []
        
        for i, query in enumerate(queries):
            logger.info(f"🔍 Researching query {i+1}/{len(queries)}: {query}")
            
            try:
                # Add delay between requests to respect rate limits
                if i > 0:
                    await asyncio.sleep(2)
                
                results = await self._search_serpapi(query, api_key, num_results)
                if results:
                    all_results.extend(results)
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to research query '{query}': {e}")
                continue
        
        return all_results
    
    async def _research_external_links(self, topic: str, api_key: str) -> List[Dict[str, Any]]:
        """Research external links from authoritative sites"""
        logger.info("🔗 Researching external links from authoritative sites")
        
        # Generate queries specifically for external links
        external_queries = [
            f"{topic} site:wikipedia.org",
            f"{topic} site:quora.com",
            f"{topic} site:medium.com",
            f"{topic} site:forbes.com",
            f"{topic} site:hbr.org"
        ]
        
        external_results = []
        
        for query in external_queries:
            try:
                await asyncio.sleep(1)  # Shorter delay for external links
                results = await self._search_serpapi(query, api_key, 3)  # Fewer results for external links
                if results:
                    external_results.extend(results)
            except Exception as e:
                logger.warning(f"⚠️ Failed to research external query '{query}': {e}")
                continue
        
        return external_results
    
    async def _enhance_with_content_scraping(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance results with content scraping for deeper analysis"""
        logger.info("📄 Enhancing results with content scraping")
        
        enhanced_results = []
        
        for result in results[:5]:  # Limit to top 5 for performance
            try:
                if result.get("link"):
                    # Scrape content from the link
                    content = await self._scrape_content(result["link"])
                    if content:
                        result["scraped_content"] = content[:500]  # Limit content length
                        result["content_length"] = len(content)
                        enhanced_results.append(result)
                    else:
                        enhanced_results.append(result)
                else:
                    enhanced_results.append(result)
                    
                await asyncio.sleep(1)  # Rate limiting for scraping
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to scrape content from {result.get('link', 'unknown')}: {e}")
                enhanced_results.append(result)
                continue
        
        return enhanced_results
    
    async def _scrape_content(self, url: str) -> Optional[str]:
        """Scrape content from a URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    # Basic HTML cleaning
                    clean_content = self._clean_html_content(content)
                    return clean_content
                else:
                    logger.warning(f"⚠️ Failed to scrape {url}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.warning(f"⚠️ Error scraping {url}: {e}")
            return None
    
    def _clean_html_content(self, html_content: str) -> str:
        """Clean HTML content and extract readable text"""
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', html_content)
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        # Remove special characters but keep basic punctuation
        clean_text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', clean_text)
        return clean_text.strip()
    
    def _create_enhanced_research_summary(self, topic: str, results: List[Dict[str, Any]], enhanced_results: List[Dict[str, Any]]) -> str:
        """Create enhanced research summary with content analysis"""
        if not results:
            return f"No research results found for '{topic}'."
        
        # Extract key information
        titles = [r["title"] for r in results[:5]]
        domains = [r["domain"] for r in results[:5]]
        
        summary = f"Enhanced Research Summary for '{topic}':\n\n"
        summary += f"Found {len(results)} relevant sources covering various aspects of {topic}.\n\n"
        
        summary += "Key Sources:\n"
        for i, (title, domain) in enumerate(zip(titles, domains), 1):
            summary += f"{i}. {title} ({domain})\n"
        
        # Add content analysis insights
        if enhanced_results:
            content_lengths = [r.get("content_length", 0) for r in enhanced_results if r.get("content_length")]
            if content_lengths:
                avg_length = sum(content_lengths) / len(content_lengths)
                summary += f"\nContent Analysis:\n"
                summary += f"• Average content length: {int(avg_length)} characters\n"
                summary += f"• Deep content analysis available for {len(enhanced_results)} sources\n"
        
        summary += f"\nResearch covers: {', '.join(set(domains))}\n"
        summary += f"Total relevant sources: {len(results)}"
        
        return summary
    
    def _extract_enhanced_external_links(self, results: List[Dict[str, Any]], enhanced_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract enhanced external links with content analysis"""
        links = []
        
        for result in results[:10]:
            link_data = {
                "title": result["title"],
                "url": result["link"],
                "description": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"]
            }
            
            # Add content analysis if available
            if result.get("scraped_content"):
                link_data["content_preview"] = result["scraped_content"][:200] + "..."
                link_data["content_length"] = result.get("content_length", 0)
            
            links.append(link_data)
        
        return links
    
    def _extract_enhanced_key_insights(self, results: List[Dict[str, Any]], enhanced_results: List[Dict[str, Any]]) -> List[str]:
        """Extract enhanced key insights with content analysis"""
        insights = []
        
        # Extract common themes from titles and snippets
        all_text = " ".join([r["title"] + " " + r["snippet"] for r in results])
        
        # Look for common patterns
        common_patterns = [
            "best practices", "tips", "strategies", "trends", "benefits",
            "challenges", "solutions", "approaches", "methods", "techniques",
            "frameworks", "methodologies", "tools", "platforms", "services"
        ]
        
        for pattern in common_patterns:
            if pattern in all_text.lower():
                insights.append(f"Coverage of {pattern} related to the topic")
        
        # Add content analysis insights
        if enhanced_results:
            content_lengths = [r.get("content_length", 0) for r in enhanced_results if r.get("content_length")]
            if content_lengths:
                if max(content_lengths) > 2000:
                    insights.append("In-depth content analysis available from authoritative sources")
                if len([l for l in content_lengths if l > 1000]) >= 3:
                    insights.append("Multiple comprehensive sources with detailed information")
        
        # Add general insights
        if len(results) >= 5:
            insights.append("Comprehensive coverage from multiple sources")
        if len(set(r["domain"] for r in results)) >= 3:
            insights.append("Diverse perspectives from different websites")
        
        return insights[:7]  # Allow more insights for enhanced research
    
    def _extract_seo_keywords(self, results: List[Dict[str, Any]], topic: str) -> List[str]:
        """
        Extract actual SEO keywords from research results
        
        Args:
            results: Research results from SerpAPI
            topic: Original research topic
            
        Returns:
            List of relevant SEO keywords
        """
        try:
            # Combine all text for analysis
            all_text = " ".join([
                r.get("title", "") + " " + r.get("snippet", "") 
                for r in results
            ]).lower()
            
            # Extract topic-related keywords
            topic_words = topic.lower().split()
            base_keywords = []
            
            # Generate base keyword combinations
            for i in range(len(topic_words)):
                for j in range(i + 1, len(topic_words) + 1):
                    keyword = " ".join(topic_words[i:j])
                    if len(keyword) > 2:  # Avoid single letters
                        base_keywords.append(keyword)
            
            # Add common industry-specific keywords
            industry_keywords = self._get_industry_keywords(topic)
            
            # Extract trending keywords from titles and snippets
            trending_keywords = self._extract_trending_keywords(all_text, topic)
            
            # Combine and rank keywords
            all_keywords = base_keywords + industry_keywords + trending_keywords
            
            # Remove duplicates and sort by relevance
            unique_keywords = list(set(all_keywords))
            ranked_keywords = self._rank_keywords_by_relevance(unique_keywords, all_text, topic)
            
            # Return top 15 most relevant keywords
            return ranked_keywords[:15]
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting SEO keywords: {e}")
            return []
    
    def _get_industry_keywords(self, topic: str) -> List[str]:
        """Get industry-specific keywords based on topic"""
        topic_lower = topic.lower()
        
        # Business/Agriculture keywords
        if any(word in topic_lower for word in ["farming", "agriculture", "plantation", "cultivation"]):
            return [
                "sustainable farming", "organic techniques", "precision agriculture",
                "soil health", "irrigation systems", "pest management",
                "harvest optimization", "post-harvest handling", "crop rotation",
                "climate resilience", "water management", "fertilization",
                "disease prevention", "weed control", "market analysis"
            ]
        
        # Technology/Digital keywords
        elif any(word in topic_lower for word in ["digital", "technology", "software", "app"]):
            return [
                "digital transformation", "automation", "artificial intelligence",
                "machine learning", "data analytics", "cloud computing",
                "mobile applications", "user experience", "performance optimization",
                "scalability", "security", "integration", "API development"
            ]
        
        # Marketing/Business keywords
        elif any(word in topic_lower for word in ["marketing", "business", "strategy", "sales"]):
            return [
                "digital marketing", "content strategy", "SEO optimization",
                "social media marketing", "email campaigns", "lead generation",
                "conversion optimization", "customer acquisition", "brand awareness",
                "market research", "competitive analysis", "ROI optimization"
            ]
        
        # Default keywords
        return [
            "best practices", "industry trends", "expert insights",
            "case studies", "success strategies", "innovation",
            "quality improvement", "efficiency", "growth strategies"
        ]
    
    def _extract_trending_keywords(self, text: str, topic: str) -> List[str]:
        """Extract trending keywords from research text"""
        try:
            # Common trending patterns
            trending_patterns = [
                r'\b\d{4}\s+(?:trends?|innovations?|developments?)\b',
                r'\b(?:new|latest|modern|contemporary)\s+\w+\b',
                r'\b(?:emerging|growing|increasing)\s+\w+\b',
                r'\b(?:sustainable|eco-friendly|green)\s+\w+\b',
                r'\b(?:AI|artificial intelligence|machine learning)\b',
                r'\b(?:blockchain|IoT|cloud|mobile)\b',
                r'\b(?:remote|virtual|digital|online)\s+\w+\b'
            ]
            
            trending_keywords = []
            for pattern in trending_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                trending_keywords.extend(matches)
            
            # Extract topic-specific trending terms
            topic_words = topic.lower().split()
            for word in topic_words:
                if len(word) > 3:  # Avoid short words
                    # Look for combinations with trending terms
                    trending_combinations = re.findall(rf'\b\w+\s+{word}\b', text, re.IGNORECASE)
                    trending_keywords.extend(trending_combinations)
            
            return list(set(trending_keywords))
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting trending keywords: {e}")
            return []
    
    def _rank_keywords_by_relevance(self, keywords: List[str], text: str, topic: str) -> List[str]:
        """Rank keywords by relevance to the topic and research text"""
        try:
            keyword_scores = []
            
            for keyword in keywords:
                score = 0
                keyword_lower = keyword.lower()
                
                # Frequency in text
                frequency = text.count(keyword_lower)
                score += frequency * 2
                
                # Topic relevance (keywords that contain topic words get higher scores)
                topic_words = topic.lower().split()
                for topic_word in topic_words:
                    if topic_word in keyword_lower:
                        score += 5
                
                # Length bonus (longer, more specific keywords)
                score += len(keyword.split()) * 2
                
                # Trending bonus (keywords with numbers, modern terms)
                if re.search(r'\d{4}', keyword) or any(word in keyword.lower() for word in ['new', 'modern', 'sustainable', 'AI']):
                    score += 3
                
                keyword_scores.append((keyword, score))
            
            # Sort by score (highest first)
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return just the keywords, not the scores
            return [keyword for keyword, score in keyword_scores]
            
        except Exception as e:
            logger.warning(f"⚠️ Error ranking keywords: {e}")
            return keywords  # Return original list if ranking fails
    
    def is_research_fresh(self, research_data: Dict[str, Any], max_age_hours: int = 24) -> bool:
        """
        Check if existing research is still fresh and can be reused
        
        Args:
            research_data: Existing research data from database
            max_age_hours: Maximum age in hours before research is considered stale
            
        Returns:
            True if research is fresh and can be reused, False otherwise
        """
        try:
            if not research_data or not research_data.get("timestamp"):
                return False
            
            timestamp = research_data["timestamp"]
            
            # Handle different timestamp formats
            if isinstance(timestamp, str):
                if timestamp == "now()":
                    # This is a database placeholder, consider it fresh
                    return True
                
                # Parse ISO format timestamp
                from datetime import datetime, timezone
                try:
                    research_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    if research_time.tzinfo is None:
                        research_time = research_time.replace(tzinfo=timezone.utc)
                except ValueError:
                    # If we can't parse the timestamp, consider it stale
                    return False
            else:
                # Assume it's already a datetime object
                research_time = timestamp
            
            # Calculate age
            current_time = datetime.now(timezone.utc)
            age_hours = (current_time - research_time).total_seconds() / 3600
            
            # Check if research is fresh
            is_fresh = age_hours <= max_age_hours
            
            if is_fresh:
                logger.info(f"✅ Research is fresh (age: {age_hours:.1f} hours)")
            else:
                logger.info(f"⚠️ Research is stale (age: {age_hours:.1f} hours, max: {max_age_hours} hours)")
            
            return is_fresh
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking research freshness: {e}")
            # If we can't determine freshness, consider it stale for safety
            return False
    
    def should_reuse_research(self, research_data: Dict[str, Any], topic: str, max_age_hours: int = 24) -> bool:
        """
        Determine if existing research should be reused for a given topic
        
        Args:
            research_data: Existing research data from database
            topic: Current topic to research
            max_age_hours: Maximum age in hours before research is considered stale
            
        Returns:
            True if research should be reused, False if new research is needed
        """
        try:
            # Check if research exists
            if not research_data:
                logger.info("🔍 No existing research found, new research needed")
                return False
            
            # Check if topic matches (allowing for minor variations)
            existing_topic = research_data.get("topic", "")
            if not existing_topic:
                logger.info("🔍 No topic found in existing research, new research needed")
                return False
            
            # Simple topic similarity check (can be enhanced with semantic similarity later)
            topic_lower = topic.lower().strip()
            existing_lower = existing_topic.lower().strip()
            
            # Check if topics are similar (exact match or one is contained in the other)
            topics_similar = (
                topic_lower == existing_lower or
                topic_lower in existing_lower or
                existing_lower in topic_lower or
                # Check if they share key words (simple heuristic)
                len(set(topic_lower.split()) & set(existing_lower.split())) >= 2
            )
            
            if not topics_similar:
                logger.info(f"🔍 Topics don't match: '{topic}' vs '{existing_topic}', new research needed")
                return False
            
            # Check if research is fresh
            if not self.is_research_fresh(research_data, max_age_hours):
                logger.info("🔍 Research is stale, new research needed")
                return False
            
            # Check if research has sufficient results
            total_results = research_data.get("total_results", 0)
            if total_results < 3:
                logger.info(f"🔍 Insufficient research results ({total_results}), new research needed")
                return False
            
            logger.info(f"✅ Research can be reused: topic matches, fresh, and has {total_results} results")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Error determining research reusability: {e}")
            return False
