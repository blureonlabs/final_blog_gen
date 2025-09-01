"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { BlogPreviewModal } from "@/components/blog-preview-modal"
import { WordPressPublishModal } from "@/components/wordpress-publish-modal"
import { 
  Pagination, 
  PaginationContent, 
  PaginationItem, 
  PaginationLink, 
  PaginationNext, 
  PaginationPrevious 
} from "@/components/ui/pagination"
import { ArrowLeft, FileText, Eye, ExternalLink, Clock, CheckCircle, XCircle, Upload, RotateCcw, Search } from "lucide-react"
import { storage, type Project, type Blog } from "@/lib/storage"
import { ContentGenerationModal } from "@/components/content-generation-modal"
import { useToast } from "@/hooks/use-toast"

interface ProjectDetailProps {
  projectId: string
  project: Project  // Add project as prop
  onBack: () => void
  onUpdate: () => void
}

export function ProjectDetail({ projectId, project: initialProject, onBack, onUpdate }: ProjectDetailProps) {
  const [project, setProject] = useState<Project | null>(initialProject)
  const [blogs, setBlogs] = useState<Blog[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedBlog, setSelectedBlog] = useState<Blog | null>(null)
  const [showContentGenerationModal, setShowContentGenerationModal] = useState(false)
  const [showWordPressPublishModal, setShowWordPressPublishModal] = useState(false)
  const [blogToPublish, setBlogToPublish] = useState<Blog | null>(null)
     const [isGeneratingContent, setIsGeneratingContent] = useState(false)
   const [shouldAutoRefresh, setShouldAutoRefresh] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null)
  const [generationStarted, setGenerationStarted] = useState(false)
  const [isExtractingKeywords, setIsExtractingKeywords] = useState(false)
  const [keywordsExtractionStarted, setKeywordsExtractionStarted] = useState(false)
  const [researchStarted, setResearchStarted] = useState(false)
  const [refreshInterval, setRefreshInterval] = useState(2000)
  const { toast } = useToast()
   
   // Pagination state
   const [currentPage, setCurrentPage] = useState(1)
  const [perPage, setPerPage] = useState(10)
  const [totalBlogs, setTotalBlogs] = useState(0)
  const [totalPages, setTotalPages] = useState(0)

     useEffect(() => {
     console.log("🔄 ProjectDetail useEffect triggered with initialProject:", initialProject)
     console.log("🔍 initialProject num_blogs:", initialProject?.num_blogs)
     console.log("🔍 initialProject status:", initialProject?.status)
     if (initialProject) {
       loadProjectData(initialProject)
       // Reset auto-refresh flag when project changes
       setShouldAutoRefresh(false)
       setGenerationStarted(false)
       setResearchStarted(false)
       setRefreshInterval(2000) // Reset to default interval
     }
   }, [initialProject])

   // Auto-refresh effect
   useEffect(() => {
     let intervalId: NodeJS.Timeout | null = null

     if (shouldAutoRefresh && (project?.status === 'in_progress' || generationStarted || researchStarted)) {
       console.log("🔄 Starting auto-refresh interval...")
       console.log("🔍 Auto-refresh conditions:", {
         shouldAutoRefresh,
         projectStatus: project?.status,
         generationStarted,
         keywordsExtractionStarted,
         refreshInterval
       })
       intervalId = setInterval(async () => {
         console.log("🔄 Auto-refresh triggered")
         await refreshProjectData()
       }, refreshInterval) // Use dynamic refresh interval
     }

     return () => {
       if (intervalId) {
         console.log("🔄 Clearing auto-refresh interval")
         clearInterval(intervalId)
       }
     }
   }, [shouldAutoRefresh, project?.status, project?.id, generationStarted, researchStarted, refreshInterval])

   // Stop auto-refresh when project is completed or failed
   useEffect(() => {
     if (project?.status === 'completed' || project?.status === 'failed') {
       console.log("🔄 Project completed/failed, stopping auto-refresh")
       setShouldAutoRefresh(false)
       setGenerationStarted(false)
       setResearchStarted(false)
       setRefreshInterval(2000) // Reset to default interval
     }
   }, [project?.status])

  // Debug effect to monitor project state changes
  useEffect(() => {
    console.log("🔍 Project state changed:")
    console.log("🔍 Project ID:", project?.id)
    console.log("🔍 Project status:", project?.status)
    console.log("🔍 Project serp_api_on:", project?.serp_api_on)
    console.log("🔍 Project serp_api_contents:", project?.serp_api_contents)
    console.log("🔍 Project serp_api_contents type:", typeof project?.serp_api_contents)
    console.log("🔍 Project serp_api_contents keys:", project?.serp_api_contents ? Object.keys(project.serp_api_contents) : "null")
  }, [project])

  const loadProjectData = async (foundProject: Project) => {
    console.log("🚀 loadProjectData called with project:", foundProject)
    console.log("🔍 Initial project num_blogs:", foundProject?.num_blogs)
    console.log("🔍 Initial project ID:", foundProject?.id)
    console.log("🔍 Initial project status:", foundProject?.status)
    console.log("🔍 Initial project serp_api_on:", foundProject?.serp_api_on)
    console.log("🔍 Initial project serp_api_contents:", foundProject?.serp_api_contents)

    if (foundProject) {
      // First, try to get updated project status from backend
      try {
        console.log("🔄 Fetching updated project status from backend...")
        const projectResponse = await fetch(`http://localhost:8000/api/projects/${projectId}`)
        console.log("📡 Backend response status:", projectResponse.status)
        
        if (projectResponse.ok) {
          const backendProject = await projectResponse.json()
              console.log("📊 Backend project data:", backendProject)
    console.log("🔍 Backend num_blogs:", backendProject.num_blogs)
    console.log("🔍 Backend project ID:", backendProject.id)
    console.log("🔍 Backend serp_api_on:", backendProject.serp_api_on)
              console.log("🔍 Backend serp_api_contents:", backendProject.serp_api_contents)
          console.log("🔍 Backend serp_api_contents type:", typeof backendProject.serp_api_contents)
          console.log("🔍 Backend serp_api_contents keys:", backendProject.serp_api_contents ? Object.keys(backendProject.serp_api_contents) : "null")
          console.log("🔍 Frontend num_blogs:", foundProject.num_blogs)
          console.log("🔍 Frontend project ID:", foundProject.id)
          
          // Update project with backend data - CRITICAL: Use backend ID
          const updatedProject = {
            ...foundProject,
            ...backendProject, // Merge all backend data to ensure num_blogs is included
            id: backendProject.id, // CRITICAL: Use the real database ID
            status: backendProject.status || foundProject.status,
            updated_at: backendProject.updated_at || foundProject.updated_at
          }
          console.log("🔄 Updated project with backend data:", updatedProject)
          console.log("🔍 Final num_blogs:", updatedProject.num_blogs)
          console.log("🔍 Final project ID:", updatedProject.id)
          setProject(updatedProject)
        } else {
          console.log("⚠️ Could not fetch project status from backend, using local data")
          console.log("🔍 Using local project num_blogs:", foundProject.num_blogs)
          console.log("🔍 Using local project ID:", foundProject.id)
          setProject(foundProject)
        }
      } catch (error) {
        console.log("❌ Backend project API not available, using local data:", error)
        console.log("🔍 Using local project num_blogs:", foundProject.num_blogs)
        console.log("🔍 Using local project ID:", foundProject.id)
        setProject(foundProject)
      }

      // Try to fetch real blogs from backend API
      try {
        console.log("🔄 Fetching blogs from backend API for project:", projectId)
        const response = await fetch(`http://localhost:8000/api/blogs/project/${projectId}?page=${currentPage}&per_page=${perPage}`)
        console.log("📡 Backend response status:", response.status)
        
        if (response.ok) {
          const apiData = await response.json()
          console.log("📊 Backend API response:", apiData)
          console.log("📝 Raw blogs from backend:", apiData.blogs)
          console.log("📝 Total blogs from backend:", apiData.total)
          
          // Update pagination state
          setTotalBlogs(apiData.total || 0)
          const calculatedTotalPages = Math.ceil((apiData.total || 0) / perPage)
          setTotalPages(calculatedTotalPages)
          
                    if (apiData.blogs && apiData.blogs.length > 0) {
            // Map backend blog statuses to frontend statuses
                         const mappedBlogs = apiData.blogs.map((blog: any) => {
               const mappedStatus = mapBackendStatusToFrontend(blog.status)
               console.log(`🔄 Mapping blog "${blog.title}": ${blog.status} → ${mappedStatus}`)
               console.log(`🔍 Blog ${blog.title} is_published:`, blog.is_published)
               console.log(`🔍 Blog ${blog.title} wordpress_url:`, blog.wordpress_url)
               return {
                 ...blog, // Include all backend fields including is_published
                 status: mappedStatus,
                 word_count: blog.word_count || 0,
                 created_at: blog.created_at,
                 published_at: blog.status === "ready" ? blog.created_at : undefined,
                 content: "", // Content is now stored in Supabase Storage, not in database
                 prompt: blog.prompt || "",
                 wordpress_url: blog.wordpress_url || null,
                 storage_path: blog.storage_path || null,
                 storage_bucket: blog.storage_bucket || null
               }
             })
            
            console.log("✅ Final mapped blogs for frontend:", mappedBlogs)
            console.log("🔍 Blogs with is_published=true:", mappedBlogs.filter((b: any) => b.is_published === true))
            setBlogs(mappedBlogs)
            setLoading(false)
            return
          } else {
            console.log("⚠️ No blogs found in backend response")
          }
        } else {
          console.log("❌ Backend API error:", response.status, response.statusText)
          const errorText = await response.text()
          console.log("❌ Error details:", errorText)
        }
      } catch (error) {
        console.log("❌ Backend API not available, using mock data:", error)
      }

             // Fallback to mock data if backend is not available
       const generatedBlogs: Blog[] = []
       const statusDistribution = [
         { status: "published", count: Math.floor(foundProject.completed_blogs * 0.7) },
         { status: "draft", count: Math.floor(foundProject.completed_blogs * 0.2) },
         { status: "generating", count: Math.floor(foundProject.completed_blogs * 0.05) },
         { status: "failed", count: Math.floor(foundProject.completed_blogs * 0.05) },
       ]

       let blogIndex = 1
       statusDistribution.forEach(({ status, count }) => {
         for (let i = 0; i < count; i++) {
           const blogTitle = `Blog Post ${blogIndex}: ${generateBlogTitle(foundProject.name)}`
           const blogContent = generateMockBlogContent(blogTitle, foundProject.name)
           
           generatedBlogs.push({
             id: `blog-${blogIndex}`,
             title: blogTitle,
             status: status as Blog["status"],
             word_count: blogContent.split(' ').length,
             created_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
             published_at: status === "published" ? new Date().toISOString() : undefined,
             is_published: status === "published", // Add is_published field for mock data
             content: blogContent,
             prompt: `Generate content about ${foundProject.name}`,
             wordpress_url: status === "published" ? `https://yourwordpress.com/blog-${blogIndex}` : `https://yourwordpress.com/draft-${blogIndex}`,
             storage_path: `blogs/${foundProject.id}/mock_${blogIndex}.json`,
             storage_bucket: "blog-content"
           })
           blogIndex++
         }
       })

      setBlogs(generatedBlogs)
    }

    setLoading(false)
  }

  // Helper function to map backend statuses to frontend statuses
  const mapBackendStatusToFrontend = (backendStatus: string): Blog["status"] => {
    switch (backendStatus) {
      case "ready":
        return "ready"  // Keep as "ready" for preview functionality
      case "generating":
        return "generating"
      case "draft":
        return "draft"
      case "published":
        return "published"  // Add support for published status
      case "failed":
        return "failed"
      case "pending":
        return "draft"
      default:
        console.log(`⚠️ Unknown backend status: ${backendStatus}, mapping to draft`)
        return "draft"
    }
  }

  const generateBlogTitle = (projectName: string): string => {
    const titles = [
      "Complete Guide",
      "Best Practices",
      "Tips and Tricks",
      "Ultimate Tutorial",
      "Step-by-Step Guide",
      "Expert Insights",
      "Advanced Techniques",
      "Beginner's Guide",
      "Pro Tips",
      "Essential Strategies",
    ]
    return titles[Math.floor(Math.random() * titles.length)]
  }

  const generateMockBlogContent = (title: string, projectName: string): string => {
    const contentTemplates = [
      `# ${title}

## Introduction

Welcome to our comprehensive guide on ${projectName}. This article will provide you with everything you need to know to get started and succeed in this field.

## What is ${projectName}?

${projectName} represents a revolutionary approach to content creation and management. It combines cutting-edge technology with user-friendly interfaces to deliver exceptional results.

## Key Benefits

- **Efficiency**: Streamlined workflows that save time and resources
- **Quality**: AI-powered content generation that maintains high standards
- **Scalability**: Easy to scale from small projects to enterprise-level operations
- **Integration**: Seamless integration with existing tools and platforms

## Getting Started

To begin your journey with ${projectName}, follow these simple steps:

1. **Setup**: Configure your account and preferences
2. **Configuration**: Choose your AI models and settings
3. **Generation**: Start creating content with your prompts
4. **Review**: Edit and refine generated content as needed
5. **Publish**: Share your content across various platforms

## Best Practices

- Always review AI-generated content before publishing
- Use specific and detailed prompts for better results
- Maintain consistency in your content style and tone
- Regularly update your AI model preferences

## Conclusion

${projectName} offers an innovative solution for modern content creators. By leveraging the power of artificial intelligence, you can produce high-quality content faster than ever before.

Start exploring the possibilities today and transform your content creation process!`,

      `# ${title}

## Overview

In this comprehensive article, we'll explore the fascinating world of ${projectName} and discover how it's revolutionizing the way we approach content creation.

## Understanding ${projectName}

${projectName} is more than just a tool—it's a complete ecosystem designed to enhance your creative capabilities. Whether you're a seasoned professional or just starting out, this platform provides the resources you need to succeed.

## Core Features

### AI-Powered Generation
The heart of ${projectName} lies in its advanced artificial intelligence capabilities. Using state-of-the-art language models, it can generate content that's not only relevant but also engaging and informative.

### Smart Workflow Management
Efficient project management tools help you organize your work, track progress, and collaborate with team members seamlessly.

### Quality Assurance
Built-in quality checks ensure that every piece of content meets your standards before publication.

## Real-World Applications

- **Blog Writing**: Create engaging blog posts on any topic
- **Marketing Content**: Generate compelling marketing copy
- **Educational Materials**: Develop comprehensive learning resources
- **Social Media**: Craft engaging social media posts

## Tips for Success

1. **Be Specific**: The more detailed your prompts, the better your results
2. **Iterate**: Don't settle for the first draft—refine and improve
3. **Stay Consistent**: Maintain your brand voice across all content
4. **Monitor Performance**: Track how your content performs and adjust accordingly

## Future of ${projectName}

As technology continues to evolve, ${projectName} will only become more powerful and intuitive. Stay ahead of the curve by embracing these innovative tools today.

## Final Thoughts

${projectName} represents the future of content creation. By combining human creativity with artificial intelligence, you can achieve results that were previously impossible.

Embrace the future and start creating amazing content with ${projectName}!`,

      `# ${title}

## Executive Summary

${projectName} has emerged as a game-changing solution in the digital content landscape. This comprehensive analysis explores how this innovative platform is transforming the way businesses and creators approach content generation.

## The ${projectName} Revolution

In today's fast-paced digital world, content creation has become both a necessity and a challenge. ${projectName} addresses this by providing an intelligent, scalable solution that leverages cutting-edge artificial intelligence.

## Key Innovation Areas

### 1. **Intelligent Content Generation**
${projectName} uses advanced language models to understand context, tone, and audience preferences, resulting in content that resonates with readers.

### 2. **Workflow Optimization**
The platform streamlines the entire content creation process, from ideation to publication, saving valuable time and resources.

### 3. **Quality Assurance**
Built-in quality checks and human review workflows ensure that every piece of content meets professional standards.

## Market Impact

${projectName} is not just another tool—it's a paradigm shift in content creation. Early adopters report:
- 70% reduction in content creation time
- 85% improvement in content quality
- 60% increase in audience engagement

## Implementation Strategy

### Phase 1: Foundation
- Set up your account and configure preferences
- Integrate with existing tools and workflows
- Train your team on best practices

### Phase 2: Optimization
- Analyze performance metrics
- Refine AI model settings
- Implement advanced features

### Phase 3: Scale
- Expand to multiple content types
- Integrate with marketing automation
- Leverage analytics for continuous improvement

## Conclusion

${projectName} represents the future of content creation. By embracing this technology, organizations can stay competitive in an increasingly content-driven marketplace.

The question is not whether to adopt ${projectName}, but how quickly you can implement it to gain a competitive advantage.`
    ]
    
    return contentTemplates[Math.floor(Math.random() * contentTemplates.length)]
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "published":
        return "bg-green-100 text-green-800 border-green-200"
      case "publishing":
        return "bg-blue-100 text-blue-800 border-blue-200"
      case "failed":
        return "bg-red-100 text-red-800 border-red-200"
      case "generating":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "published":
        return <CheckCircle className="h-4 w-4" />
      case "publishing":
        return <Upload className="h-4 w-4" />
      case "failed":
        return <XCircle className="h-4 w-4" />
      case "generating":
        return <Clock className="h-4 w-4 animate-spin" />
      default:
        return <FileText className="h-4 w-4" />
    }
  }

  const handleRegenerateFailed = () => {
    console.log("[v0] Republishing failed blogs...")
    const updatedBlogs = blogs.map((blog) =>
      blog.status === "failed" ? { ...blog, status: "ready" as Blog["status"] } : blog,
    )
    setBlogs(updatedBlogs)

    // Update project in storage
    if (project) {
      storage.updateProject(project.id, { updated_at: new Date().toISOString() })
      onUpdate()
    }
  }

  const handleReuploadFailed = () => {
    console.log("[v0] Reuploading failed uploads...")
    if (project) {
      storage.updateProject(project.id, { updated_at: new Date().toISOString() })
      onUpdate()
    }
  }

  const handlePublishDrafts = () => {
    console.log("[v0] Publishing draft blogs...")
    const updatedBlogs = blogs.map((blog) =>
      blog.status === "draft" ? { ...blog, status: "publishing" as Blog["status"] } : blog,
    )
    setBlogs(updatedBlogs)

    // Simulate publishing process
    setTimeout(() => {
      const publishedBlogs = updatedBlogs.map((blog) =>
        blog.status === "publishing"
          ? {
              ...blog,
              status: "published" as Blog["status"],
              published_at: new Date().toISOString(),
            }
          : blog,
      )
      setBlogs(publishedBlogs)

      if (project) {
        const newCompletedCount = publishedBlogs.filter((b) => b.status === "published").length
        storage.updateProject(project.id, {
          completed_blogs: newCompletedCount,
          updated_at: new Date().toISOString(),
        })
        onUpdate()
      }
    }, 2000)
  }

  const handlePublishSingle = (blogId: string) => {
    console.log(`[v0] Publishing single blog: ${blogId}`)
    const blogToPublish = blogs.find(blog => blog.id === blogId);
    if (blogToPublish) {
      setBlogToPublish(blogToPublish);
      setShowWordPressPublishModal(true);
    }
  }

  const refreshProjectData = async () => {
    if (!project) return;
    
    try {
      setIsRefreshing(true)
      console.log("🔄 Refreshing project data...")
      
      // Refresh project status
      console.log("🔍 Fetching project data from:", `http://localhost:8000/api/projects/${project.id}`)
      const projectResponse = await fetch(`http://localhost:8000/api/projects/${project.id}`)
      console.log("🔍 Project response status:", projectResponse.status)
      console.log("🔍 Project response ok:", projectResponse.ok)
      if (projectResponse.ok) {
        const backendProject = await projectResponse.json()
        console.log("🔍 Backend project data:", backendProject)
        console.log("🔍 Backend extracted_seo_keywords:", backendProject.extracted_seo_keywords)
        console.log("🔍 Backend serp_api_contents:", backendProject.serp_api_contents)
        console.log("🔍 Backend serp_api_contents type:", typeof backendProject.serp_api_contents)
        console.log("🔍 Backend serp_api_contents keys:", backendProject.serp_api_contents ? Object.keys(backendProject.serp_api_contents) : "null")
        console.log("🔍 Current project serp_api_contents:", project.serp_api_contents)
        console.log("🔍 Current project serp_api_contents type:", typeof project.serp_api_contents)
        
        const updatedProject = {
          ...project,
          ...backendProject,
          id: backendProject.id,
          status: backendProject.status || project.status,
          updated_at: backendProject.updated_at || project.updated_at,
          // Explicitly ensure serp_api_contents is included
          serp_api_contents: backendProject.serp_api_contents,
          serp_api_on: backendProject.serp_api_on
        }
        setProject(updatedProject)
        console.log("✅ Project data refreshed")
        console.log("🔍 Updated project extracted_seo_keywords:", updatedProject.extracted_seo_keywords)
        console.log("🔍 Updated project serp_api_contents:", updatedProject.serp_api_contents)
        console.log("🔍 Updated project serp_api_contents type:", typeof updatedProject.serp_api_contents)
        console.log("🔍 Updated project serp_api_contents keys:", updatedProject.serp_api_contents ? Object.keys(updatedProject.serp_api_contents) : "null")
        console.log("🔍 Updated project serp_api_on:", updatedProject.serp_api_on)
        console.log("🔍 Updated project status:", updatedProject.status)
        
        // Stop research started flag when research is completed
        if (researchStarted && updatedProject.serp_api_contents) {
          setResearchStarted(false)
          console.log("🔄 Research completed, stopping research started flag")
        }
        
        // Auto-extract keywords when SerpAPI research is available but keywords are not
        if (updatedProject.serp_api_contents && !updatedProject.extracted_seo_keywords && !isExtractingKeywords) {
          console.log("🔄 Auto-extracting keywords from available research data...")
          await extractKeywordsAutomatically(updatedProject.id)
        }
        
        // Force re-render if serp_api_contents changed
        if (project.serp_api_contents !== updatedProject.serp_api_contents) {
          console.log("🔄 SerpAPI contents updated, forcing re-render")
          console.log("🔍 Old serp_api_contents:", project.serp_api_contents)
          console.log("🔍 New serp_api_contents:", updatedProject.serp_api_contents)
          
          // Force a re-render by updating a dummy state
          setLastRefreshTime(new Date())
        }
        
        // Force re-render if keywords changed
        if (project.extracted_seo_keywords !== updatedProject.extracted_seo_keywords) {
          console.log("🔄 Keywords updated, forcing re-render")
          console.log("🔍 Old keywords:", project.extracted_seo_keywords)
          console.log("🔍 New keywords:", updatedProject.extracted_seo_keywords)
          console.log("🔍 New keywords length:", updatedProject.extracted_seo_keywords?.length)
        } else {
          console.log("🔍 Keywords unchanged:", updatedProject.extracted_seo_keywords)
        }
      }
      
      // Refresh blog list
      await refreshBlogList()
      
      setLastRefreshTime(new Date())
      
      // Gradually increase refresh interval as more blogs are generated
      if (shouldAutoRefresh && project?.status === 'in_progress') {
        const currentBlogCount = blogs.length
        if (currentBlogCount < 3) {
          setRefreshInterval(1000) // 1 second for first few blogs
        } else if (currentBlogCount < 10) {
          setRefreshInterval(2000) // 2 seconds for next few blogs
        } else {
          setRefreshInterval(3000) // 3 seconds for remaining blogs
        }
      }
      

    } catch (error) {
      console.error("❌ Error refreshing project data:", error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const extractKeywordsAutomatically = async (projectId: string) => {
    try {
      console.log('🔄 Auto-extracting SEO keywords for project:', projectId);
      setIsExtractingKeywords(true);
      
      const response = await fetch(`http://localhost:8000/api/projects/${projectId}/extract-seo-keywords`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json' 
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ Auto-extracted SEO keywords successfully:', result);
        
        // Refresh project data to show the extracted keywords
        await refreshProjectData();
        
        toast({
          title: "Keywords Auto-Extracted",
          description: "SEO keywords have been automatically extracted from research data.",
        });
      } else {
        const errorText = await response.text();
        console.error('❌ Auto keyword extraction failed:', response.status, response.statusText);
        console.error('❌ Error details:', errorText);
        
        toast({
          title: "Auto Keyword Extraction Failed",
          description: `Failed to auto-extract keywords: ${response.statusText}`,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('❌ Error in auto keyword extraction:', error);
      toast({
        title: "Auto Keyword Extraction Error",
        description: "An error occurred while auto-extracting keywords.",
        variant: "destructive",
      });
    } finally {
      setIsExtractingKeywords(false);
    }
  }

  const refreshBlogList = async () => {
    if (!project) return;
    
    try {
      console.log("🔄 Refreshing blog list...")
      const response = await fetch(`http://localhost:8000/api/blogs/project/${project.id}?page=${currentPage}&per_page=${perPage}`)
      
      if (response.ok) {
        const apiData = await response.json()
        console.log("📡 Refresh response:", apiData)
        
        // Update pagination state
        setTotalBlogs(apiData.total || 0)
        const calculatedTotalPages = Math.ceil((apiData.total || 0) / perPage)
        setTotalPages(calculatedTotalPages)
        
        if (apiData.blogs && apiData.blogs.length > 0) {
          const mappedBlogs = apiData.blogs.map((blog: any) => {
            const mappedStatus = mapBackendStatusToFrontend(blog.status)
            console.log(`🔄 Refresh mapping blog "${blog.title}": status=${blog.status} → ${mappedStatus}, is_published=${blog.is_published}`)
            return {
              ...blog,
              status: mappedStatus,
              created_at: blog.created_at || new Date().toISOString(),
              word_count: blog.word_count || 0
            }
          })
          setBlogs(mappedBlogs)
          console.log("✅ Blog list refreshed:", mappedBlogs.length, "blogs")
          console.log("🔍 Blogs with is_published=true after refresh:", mappedBlogs.filter((b: any) => b.is_published === true))
        }
      }
    } catch (error) {
      console.error("❌ Error refreshing blog list:", error)
    }
  }

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setLoading(true)
    setCurrentPage(newPage)
  }



  const handleStartContentGeneration = async () => {
    console.log("[v0] Starting content generation...")
    console.log("🔍 Project object:", project)
    console.log("🔍 Project num_blogs:", project?.num_blogs)
    console.log("🔍 Project ID being sent:", project?.id)
    console.log("🔍 Project ID type:", typeof project?.id)
    console.log("🔍 Project status:", project?.status)
    
    // Prevent multiple simultaneous requests
    if (isGeneratingContent) {
      console.log("⚠️ Content generation already in progress, ignoring duplicate request")
      return
    }
    
    if (!project) {
      console.error("❌ No project object available")
      alert("No project data available. Please refresh the page and try again.")
      return
    }
    
    if (!project.id) {
      console.error("❌ Project ID is missing")
      alert("Project ID is missing. Please refresh the page and try again.")
      return
    }
    
    // Validate that project ID is a valid UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    if (!uuidRegex.test(project.id)) {
      console.error("❌ Invalid project ID format:", project.id)
      alert("Invalid project ID format. Please refresh the page and try again.")
      return
    }
    
    // Set generating state to prevent duplicate requests
    setIsGeneratingContent(true)
    
    // Start auto-refresh immediately when generation begins
    setShouldAutoRefresh(true)
    setGenerationStarted(true)
    setResearchStarted(true) // Research starts when content generation begins
    setRefreshInterval(1000) // Start with 1 second intervals for faster updates
    console.log("🚀 Auto-refresh started immediately for content generation...")
    
    try {
      // First, verify the project exists in the database
      console.log("🔍 Verifying project exists in database...")
      console.log("🔍 Project ID being sent:", project.id)
      console.log("🔍 Backend URL:", `http://localhost:8000/api/projects/${project.id}`)
      
      let projectData = null
      
      try {
        // Call the backend API directly since Next.js API routes don't exist
        const verifyResponse = await fetch(`http://localhost:8000/api/projects/${project.id}`)
        console.log("🔍 Verification response status:", verifyResponse.status)
        console.log("🔍 Verification response headers:", verifyResponse.headers)
        
        if (!verifyResponse.ok) {
          const errorText = await verifyResponse.text()
          console.error("❌ Project verification failed:", errorText)
          throw new Error(`Project verification failed: ${verifyResponse.statusText} - ${errorText}`)
        }
        
        projectData = await verifyResponse.json()
        console.log("✅ Project verified in database:", projectData)
      } catch (verifyError) {
        console.warn("⚠️ Project verification failed, proceeding with local project data:", verifyError)
        console.log("🔍 Using local project data for content generation")
        projectData = project
      }
      
      // Now start content generation
      const requestBody = {
        project_id: project.id,  // This should now be a valid UUID string
        prompt: project.description || `Generate ${project.num_blogs} blog posts for the project: ${project.name}`,
        ai_model: project.draft_creation_model || "openai",  // Use draft_creation_model from database
        num_blogs: project.num_blogs,
        batch_size: Math.min(5, project.num_blogs)  // Default to 5 or less if fewer blogs requested
      }
      
      console.log("🚀 Starting content generation with request:", requestBody)
      console.log("🔍 AI Model Configuration:")
      console.log("  - AI Model:", project.draft_creation_model || "openai")
      
      const contentResponse = await fetch('http://localhost:8000/api/content-generation/generate-direct', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })
      
      if (!contentResponse.ok) {
        const errorData = await contentResponse.json()
        if (contentResponse.status === 409) {
          const errorMessage = errorData.detail || "Project is already generating content"
          alert(`⚠️ ${errorMessage}. Please wait for the current generation to complete.`)
          return
        }
        throw new Error(`Blog generation failed: ${JSON.stringify(errorData)}`)
      }
      
      const result = await contentResponse.json()
      console.log("✅ Content generation started successfully:", result)
      
             // Update project status to show it's in progress
       setProject(prev => prev ? { ...prev, status: 'in_progress' } : null)
       
       // Show success toast
       toast({
         title: "Content Generation Started",
         description: "Blogs are now being generated and will appear below as they're completed.",
       })
       
       // Start immediate refresh to show blogs as they're generated
       setTimeout(() => {
         console.log("🔄 Content generation refresh 1 (500ms)")
         refreshProjectData()
       }, 500) // Refresh after 500ms to catch initial blogs
       
       // Additional immediate refresh after 2 seconds
       setTimeout(() => {
         console.log("🔄 Content generation refresh 2 (2s)")
         refreshProjectData()
       }, 2000)
       
       // Another refresh after 4 seconds to catch early blogs
       setTimeout(() => {
         console.log("🔄 Content generation refresh 3 (4s)")
         refreshProjectData()
       }, 4000)
       
       // Additional refreshes for research completion
       setTimeout(() => {
         console.log("🔄 Research completion refresh 1 (6s)")
         refreshProjectData()
       }, 6000) // Refresh after 6 seconds
       
       setTimeout(() => {
         console.log("🔄 Research completion refresh 2 (10s)")
         refreshProjectData()
       }, 10000) // Refresh after 10 seconds
       
       setTimeout(() => {
         console.log("🔄 Research completion refresh 3 (15s)")
         refreshProjectData()
       }, 15000) // Refresh after 15 seconds
      
    } catch (error) {
      console.error("❌ Error starting content generation:", error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      
      // Stop auto-refresh if generation fails
      setShouldAutoRefresh(false)
      setGenerationStarted(false)
      setResearchStarted(false)
      
      toast({
        title: "Generation Failed",
        description: `Failed to start content generation: ${errorMessage}`,
        variant: "destructive",
      })
    } finally {
      // Always reset the generating state
      setIsGeneratingContent(false)
    }
  }

  const handleStartGeneration = () => {
    console.log("[v0] Starting content generation...")
    // In a real application, you would trigger the actual generation process here
    // This would involve calling an API endpoint to start the generation pipeline
    // For now, we'll just simulate it
    const newBlogs: Blog[] = []
    const statusDistribution = [
      { status: "published", count: Math.floor(project!.num_blogs * 0.7) },
      { status: "draft", count: Math.floor(project!.num_blogs * 0.2) },
      { status: "generating", count: Math.floor(project!.num_blogs * 0.05) },
      { status: "failed", count: Math.floor(project!.num_blogs * 0.05) },
    ]

    let blogIndex = 1
    statusDistribution.forEach(({ status, count }) => {
      for (let i = 0; i < count; i++) {
        newBlogs.push({
          id: `blog-${blogIndex}`,
          title: `Blog Post ${blogIndex}: ${generateBlogTitle(project!.name)}`,
          status: status as Blog["status"],
          word_count: Math.floor(Math.random() * 1000) + 500,
          created_at: new Date().toISOString(),
          published_at: status === "published" ? new Date().toISOString() : undefined,
          is_published: status === "published", // Add is_published field for mock data
        })
        blogIndex++
      }
    })

    setBlogs(newBlogs)
    setShowContentGenerationModal(false)
    onUpdate()
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
        <div className="h-32 bg-gray-200 rounded mb-6"></div>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-16">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Project not found</h3>
        <p className="text-gray-600 mb-4">The project you're looking for doesn't exist.</p>
        <Button onClick={onBack} variant="outline">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>
    )
  }

  const publishedBlogs = blogs.filter((blog) => blog.is_published === true).length
  const draftBlogs = blogs.filter((blog) => blog.status === "draft").length
  const generatingBlogs = blogs.filter((blog) => blog.status === "generating").length
  const failedBlogs = blogs.filter((blog) => blog.status === "failed").length
  const postingBlogs = blogs.filter((blog) => blog.status === "publishing").length

     const progressPercentage = project.num_blogs > 0 ? (totalBlogs / project.num_blogs) * 100 : 0
   const publishedPercentage = project.num_blogs > 0 ? (publishedBlogs / project.num_blogs) * 100 : 0

  const getProjectStatus = () => {
    if (project.num_blogs === 0) return "none";
    
    // Check if all blogs are actually published to WordPress
    if (publishedBlogs === project.num_blogs) return "completed";
    
    // Check if all blogs are generated but not all published (this should be "partial")
    if (totalBlogs === project.num_blogs && publishedBlogs < project.num_blogs) return "partial";
    
    // Check if blogs are currently being generated
    if (generatingBlogs > 0 || postingBlogs > 0) return "in_progress";
    
    // Check if some blogs are generated but not all
    if (totalBlogs > 0 && totalBlogs < project.num_blogs) return "in_progress";
    
    // Check if some blogs exist but none are published
    if (totalBlogs > 0 && publishedBlogs === 0) return "generated_not_published";
    
    return "none";
  };

  const getStatusInfo = () => {
    const status = getProjectStatus();
    switch (status) {
      case "completed":
        return { label: "🎉 All Blogs Published to WordPress", bgColor: "bg-green-100 text-green-800 border-green-200" };
             case "partial":
         return { label: "", bgColor: "" };
      case "in_progress":
        return { label: "🔄 Blogs Being Generated", bgColor: "bg-blue-100 text-blue-800 border-blue-200" };
      case "generated_not_published":
        return { label: "⚠️ All Blogs Generated but None Published", bgColor: "bg-yellow-100 text-yellow-800 border-yellow-200" };
             case "none":
       default:
         return { label: "", bgColor: "" };
    }
  };

  return (
    <div>
             {/* Header */}
       <div className="flex items-center justify-between mb-6">
         {/* Left side - Back button */}
         <Button
           onClick={onBack}
           variant="outline"
           size="sm"
           className="border-gray-300 text-gray-600 hover:bg-gray-50 bg-transparent"
         >
           <ArrowLeft className="h-4 w-4 mr-2" />
           Back to Dashboard
         </Button>
         
                   {/* Center - Project title */}
          <div className="flex-1 flex justify-center">
            <div>
            <h2 className="text-2xl font-bold text-gray-900">{project.name}</h2>
              
            {/* SerpAPI Status Indicator */}

          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Refresh Button */}
          <Button
            onClick={(e) => {
              e.preventDefault()
              refreshProjectData()
            }}
            variant="outline"
            size="sm"
            disabled={isRefreshing}
            className="border-gray-300 text-gray-600 hover:bg-gray-50"
            title="Refresh content"
          >
            <Clock className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </Button>

          {/* Start Content Generation Button */}
          {(((project.status === "pending" || project.status === "ready") && blogs.length === 0) || 
           (project.status === "in_progress" && isGeneratingContent)) && (
            <Button
              onClick={handleStartContentGeneration}
              disabled={isGeneratingContent || project.status === "in_progress"}
              className={`${
                (isGeneratingContent || project.status === "in_progress")
                  ? "bg-blue-600 cursor-not-allowed"
                  : "bg-green-600 hover:bg-green-700"
              } text-white`}
              size="sm"
              title={
                (isGeneratingContent || project.status === "in_progress") 
                  ? "Content generation in progress..." 
                  : "Start generating blog content"
              }
            >
              {(isGeneratingContent || project.status === "in_progress") ? (
                <>
                  <Clock className="h-4 w-4 mr-2 animate-spin" />
                  {isGeneratingContent ? "Starting Generation..." : "Generating Content..."}
                </>
              ) : (
                <>
                  <FileText className="h-4 w-4 mr-2" />
                  Start Content Generation
                </>
              )}
            </Button>
          )}

           {failedBlogs > 0 && (
             <Button
               onClick={handleRegenerateFailed}
               variant="outline"
               size="sm"
               className="border-red-300 text-red-600 hover:bg-red-50 bg-transparent"
             >
               <XCircle className="h-4 w-4 mr-2" />
               Republish Failed ({failedBlogs})
             </Button>
           )}

           

          {draftBlogs > 0 && (
            <Button onClick={handlePublishDrafts} className="bg-indigo-600 text-white hover:bg-indigo-700" size="sm">
              <CheckCircle className="h-4 w-4 mr-2" />
              Publish All Drafts ({draftBlogs})
            </Button>
          )}

          
        </div>
      </div>

      {/* SerpAPI Research Results Display */}
      {project && project.serp_api_on && (
        <div className="mb-6">
          {(() => {
            console.log("🔍 SerpAPI Research Display - project.serp_api_on:", project.serp_api_on);
            console.log("🔍 SerpAPI Research Display - project.serp_api_contents:", project.serp_api_contents);
            return null;
          })()}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Search className="h-5 w-5 text-blue-600" />
                    SerpAPI Research Results
                  </CardTitle>
                  <CardDescription>
                    {project.serp_api_contents && project.serp_api_contents.total_results
                      ? `${project.serp_api_contents.total_results} sources researched with SEO keywords extracted`
                      : (project.status === 'in_progress' || researchStarted)
                        ? "Research is currently in progress..."
                        : "Research will be performed when you start content generation"
                    }
                  </CardDescription>
                </div>

              </div>
            </CardHeader>
                        <CardContent className="space-y-4">

              
              {/* Research Status */}
              {!project.serp_api_contents ? (
                <div className="text-center py-8">
                  <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
                    <Search className={`h-8 w-8 text-blue-600 ${(project.status === 'in_progress' || researchStarted) ? 'animate-pulse' : ''}`} />
                  </div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">
                    {(project.status === 'in_progress' || researchStarted) ? 'Research Started' : 'Research Not Started Yet'}
                  </h4>
                  <p className="text-gray-600 mb-4">
                    {(project.status === 'in_progress' || researchStarted)
                      ? 'Research is currently in progress. Results will appear here once completed.'
                      : 'Research will be automatically performed when you start content generation.'
                    }
                  </p>
                  {(project.status === 'in_progress' || researchStarted) && (
                    <div className="flex items-center justify-center gap-2 text-sm text-blue-600">
                      <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                      <span>Researching sources and extracting data...</span>
                    </div>
                  )}
                </div>
              ) : (
                <>


                  {/* SEO Keywords Display */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">
                        SEO Keywords
                        {project.extracted_seo_keywords && project.extracted_seo_keywords.length > 0 && (
                          <span className="ml-2 text-sm text-gray-500">
                            ({project.extracted_seo_keywords.length})
                          </span>
                        )}
                      </h4>
                      <div className="flex gap-2">

                        {project.serp_api_contents && !project.extracted_seo_keywords && !isExtractingKeywords && (
                          <Button
                            onClick={async () => {
                              try {
                                setIsExtractingKeywords(true);
                                console.log('🔍 Attempting to extract SEO keywords for project:', project.id);
                                
                                const response = await fetch(`http://localhost:8000/api/projects/${project.id}/extract-seo-keywords`, {
                                  method: 'POST',
                                  headers: { 
                                    'Content-Type': 'application/json' 
                                  }
                                });
                                
                                console.log('📡 Response status:', response.status);
                                console.log('📡 Response headers:', response.headers);
                                
                                if (response.ok) {
                                  const result = await response.json();
                                  console.log('✅ SEO keywords extracted successfully:', result);
                                  
                                  // Single refresh to show the extracted keywords
                                  console.log('🔄 Refreshing project data to show extracted keywords...');
                                  await refreshProjectData();
                                  
                                  // Additional check to see if keywords are now available
                                  console.log('🔍 After refresh - project.extracted_seo_keywords:', project?.extracted_seo_keywords);
                                  
                                  // Force an additional refresh after a short delay to ensure keywords are visible
                                  setTimeout(async () => {
                                    console.log('🔄 Additional refresh to ensure keywords are visible...');
                                    await refreshProjectData();
                                    console.log('🔍 After additional refresh - project.extracted_seo_keywords:', project?.extracted_seo_keywords);
                                  }, 1000);
                                  
                                  // Also try a direct fetch to get the latest project data
                                  setTimeout(async () => {
                                    try {
                                      console.log('🔄 Direct fetch to get latest project data...');
                                      const directResponse = await fetch(`http://localhost:8000/api/projects/${project.id}`);
                                      if (directResponse.ok) {
                                        const directProject = await directResponse.json();
                                        console.log('🔍 Direct fetch - extracted_seo_keywords:', directProject.extracted_seo_keywords);
                                        if (directProject.extracted_seo_keywords && directProject.extracted_seo_keywords.length > 0) {
                                          console.log('🔄 Updating project state with direct fetch data...');
                                          setProject(prev => prev ? ({
                                            ...prev,
                                            extracted_seo_keywords: directProject.extracted_seo_keywords
                                          }) : null);
                                        }
                                      }
                                    } catch (error) {
                                      console.error('❌ Error in direct fetch:', error);
                                    }
                                  }, 2000);
                                  
                                  toast({
                                    title: "Keywords Extracted",
                                    description: "SEO keywords have been successfully extracted from research data.",
                                  });
                                } else {
                                  const errorText = await response.text();
                                  console.error('❌ Failed to extract SEO keywords:', response.status, response.statusText);
                                  console.error('❌ Error details:', errorText);
                                  // No auto-refresh cleanup needed since we don't use auto-refresh for keyword extraction
                                  toast({
                                    title: "Keyword Extraction Failed",
                                    description: `Failed to extract keywords: ${response.statusText}`,
                                    variant: "destructive",
                                  });
                                }
                              } catch (error) {
                                console.error('❌ Exception during SEO keywords extraction:', error);
                                // No auto-refresh cleanup needed since we don't use auto-refresh for keyword extraction
                                toast({
                                  title: "Keyword Extraction Failed",
                                  description: "An error occurred while extracting keywords. Please try again.",
                                  variant: "destructive",
                                });
                              } finally {
                                setIsExtractingKeywords(false);
                              }
                            }}
                            size="sm"
                            variant="outline"
                            disabled={isExtractingKeywords}
                            className="text-xs"
                          >
                            {isExtractingKeywords ? (
                              <>
                                <RotateCcw className="h-3 w-3 mr-1 animate-spin" />
                                Extracting...
                              </>
                            ) : (
                              "Extract Keywords"
                            )}
                          </Button>
                        )}
                        
                        {/* Auto-extraction loading indicator */}
                        {project.serp_api_contents && !project.extracted_seo_keywords && isExtractingKeywords && (
                          <div className="flex items-center gap-2 text-sm text-blue-600">
                            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                            <span>Auto-extracting keywords...</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {project.extracted_seo_keywords && project.extracted_seo_keywords.length > 0 ? (
                      <>
                        <div className="flex flex-wrap gap-2">
                          {project.extracted_seo_keywords.map((keyword: string, index: number) => (
                            <span 
                              key={index} 
                              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                        <p className="text-xs text-gray-600 mt-2">
                          These keywords are extracted from research and should be naturally incorporated into your content for better SEO.
                        </p>
                      </>
                    ) : (
                      <div className="text-center py-4">
                        <p className="text-gray-600">No SEO keywords extracted yet</p>
                        {project.serp_api_contents && !project.extracted_seo_keywords && !isExtractingKeywords && (
                          <p className="text-xs text-gray-500 mt-1">
                            Keywords will be automatically extracted from research data, or click "Extract Keywords" to extract manually
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}

             {/* Project Overview */}
       <Card className="bg-white shadow-sm mb-8">
         <CardHeader>
           <div className="flex items-center justify-between">
                           <div>
                <CardTitle className="text-xl text-gray-900">{project.description}</CardTitle>
                <CardDescription className="text-gray-600">
                  Created on {new Date(project.created_at).toLocaleDateString()}
                </CardDescription>
              </div>
              

           </div>
         </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Project Configuration Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                             <div>
                 <h4 className="text-sm font-medium text-gray-700 mb-2">WordPress Account</h4>
                 <p className="text-sm text-gray-900 font-medium">
                   {project.wordpress_account_id || "Not configured yet"}
                 </p>
               </div>
                             <div>
                 <h4 className="text-sm font-medium text-gray-700 mb-2">API Keys Used</h4>
                 <div className="space-y-1">
                   {project.api_keys ? (
                     <>
                       <p className="text-xs text-gray-600">
                         OpenAI: <span className="font-medium">{project.api_keys.openai || "Not configured"}</span>
                       </p>
                       <p className="text-xs text-gray-600">
                         Gemini: <span className="font-medium">{project.api_keys.gemini || "Not configured"}</span>
                       </p>
                       <p className="text-xs text-gray-600">
                         SERP: <span className="font-medium">{project.api_keys.serp || "Not configured"}</span>
                       </p>
                     </>
                   ) : (
                     <p className="text-xs text-gray-500 italic">API keys not configured yet</p>
                   )}
                 </div>
               </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                                 <div className="flex items-center justify-between">
                   <span className="text-sm font-medium text-gray-700">Blogs Generated</span>
                   <span className="text-sm text-gray-600">
                     {totalBlogs} of {project.num_blogs} blogs
                   </span>
                 </div>
                <Progress value={progressPercentage} className="h-2" />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Published</span>
                  <span className="text-sm text-gray-600">
                    {publishedBlogs} of {project.num_blogs} published
                  </span>
                </div>
                <Progress value={publishedPercentage} className="h-2" />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="text-2xl font-bold text-green-600">{publishedBlogs}</div>
                <div className="text-xs text-green-700">Published</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="text-2xl font-bold text-gray-600">{draftBlogs}</div>
                <div className="text-xs text-gray-700">Draft</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                <div className="text-2xl font-bold text-blue-600">{postingBlogs}</div>
                <div className="text-xs text-blue-700">Publishing</div>
              </div>
              <div className="text-center p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <div className="text-2xl font-bold text-yellow-600">{generatingBlogs}</div>
                <div className="text-xs text-yellow-700">Generating</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="text-2xl font-bold text-red-600">{failedBlogs}</div>
                <div className="text-xs text-red-700">Failed</div>
              </div>
            </div>

                                                         {/* Project Status Display */}
                 <div className="mt-3">
                   {getStatusInfo().label && (
                     <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusInfo().bgColor} border`}>
                       {getStatusInfo().label}
                     </div>
                   )}
                  

                  

                  
                  {/* Status Messages */}
                  
                  {getProjectStatus() === "generated_not_published" && (
                    <p className="text-xs text-yellow-600 mt-2">
                      ⚠️ {totalBlogs} blogs generated but none published to WordPress yet
                    </p>
                  )}
                  {getProjectStatus() === "completed" && (
                    <p className="text-xs text-green-600 mt-2">
                      🎉 All {publishedBlogs} blogs successfully published to WordPress!
                    </p>
                  )}
                </div>
          </div>
        </CardContent>
      </Card>

      {/* Content Monitoring Section */}
              {project.status === "in_progress" && (
        <Card className="bg-blue-50 border-blue-200 mb-6">
          <CardHeader>
            <CardTitle className="text-lg text-blue-900 flex items-center">
              <Clock className="h-5 w-5 mr-2" />
              Content Generation in Progress
            </CardTitle>
            <CardDescription className="text-blue-700">
              {generationStarted 
                ? "✅ Content generation started successfully! Blogs will appear below as they're generated."
                : "Your blogs are being generated. Here's how to monitor progress:"
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Real-time Progress */}
              <div className="bg-white p-4 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-900 mb-3">📊 Generation Progress</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-lg font-bold text-blue-600">{generatingBlogs}</div>
                    <div className="text-blue-700">Currently Generating</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-green-600">{publishedBlogs}</div>
                    <div className="text-green-700">Completed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-yellow-600">{draftBlogs}</div>
                    <div className="text-yellow-700">Ready for Review</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-gray-600">{project.num_blogs - blogs.length}</div>
                    <div className="text-gray-700">Remaining</div>
                  </div>
                </div>
              </div>

              {/* Where to Check Content */}
              <div className="bg-white p-4 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-900 mb-3">📍 Where to Check Generated Content</h4>
                <div className="space-y-2 text-sm text-blue-800">
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span><strong>This Page:</strong> Blogs appear here as they're generated</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span><strong>Backend API:</strong> GET /api/blogs/project/{project.id}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span><strong>Database:</strong> Check 'blogs' table in Supabase</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span><strong>Console Logs:</strong> Backend terminal shows real-time progress</span>
                  </div>
                </div>
              </div>

              {/* Estimated Completion */}
              <div className="bg-white p-4 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-900 mb-3">⏱️ Estimated Completion</h4>
                <div className="text-sm text-blue-800">
                          <p><strong>Current Progress:</strong> {blogs.length} of {project.num_blogs} blogs</p>
        <p><strong>Estimated Time:</strong> {Math.ceil((project.num_blogs - blogs.length) / 5)} minutes remaining</p>
                  <p><strong>Status:</strong> {project.status === "in_progress" ? "🔄 Active" : "⏸️ Paused"}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Blogs List */}
      <Card className="bg-white shadow-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
                         <div>
               <CardTitle className="text-lg text-gray-900">Generated Blogs</CardTitle>
             </div>
            
                         {/* Show per page selector - Top Right */}
             {blogs.length > 0 && (
               <div className="flex items-center space-x-2">
                 <label htmlFor="per-page" className="text-sm text-gray-600">Show:</label>
                 <select
                   id="per-page"
                   value={perPage}
                   onChange={(e) => {
                     setPerPage(Number(e.target.value))
                     setCurrentPage(1) // Reset to first page when changing per-page
                   }}
                   className="border border-gray-300 rounded px-2 py-1 text-sm"
                 >
                   <option value={5}>5</option>
                   <option value={10}>10</option>
                   <option value={20}>20</option>
                   <option value={50}>50</option>
                 </select>
                 <span className="text-sm text-gray-600">per page</span>
               </div>
             )}
          </div>
        </CardHeader>
        <CardContent>
           
           {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading blogs...</p>
            </div>
          ) : blogs.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No blogs have been generated yet.</p>
              <p className="text-sm text-gray-500 mt-2">Blog generation will start automatically.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {blogs.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No blogs found on this page.</p>
                  {totalPages > 1 && (
                    <p className="text-sm text-gray-500 mt-2">
                      Try navigating to a different page or adjust the items per page.
                    </p>
                  )}
                </div>
              ) : (
                blogs.map((blog) => (
                <div
                  key={blog.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 mb-2">{blog.title}</h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>Created: {new Date(blog.created_at).toLocaleDateString()}</span>
                      <span>{blog.word_count} words</span>
                      <span
                        className={`px-3 py-1 rounded-full text-xs border flex items-center space-x-1 ${getStatusColor(blog.status)}`}
                      >
                        {getStatusIcon(blog.status)}
                        <span className="capitalize">{blog.status}</span>
                      </span>
                      {blog.is_published && (
                        <span className="px-2 py-1 rounded-full text-xs bg-green-100 text-green-800 border border-green-200 flex items-center space-x-1">
                          <CheckCircle className="h-3 w-3" />
                          <span>Published</span>
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {blog.status === "generating" && (
                      <div className="flex items-center space-x-2 text-blue-600">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        <span className="text-sm">Generating...</span>
                      </div>
                    )}

                    {(blog.status === "draft" || blog.status === "ready") && !blog.is_published && (
                      <Button
                        onClick={() => handlePublishSingle(blog.id)}
                        variant="outline"
                        size="sm"
                        className="border-green-300 text-green-600 hover:bg-green-50"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Publish
                      </Button>
                    )}



                    {blog.status === "ready" && (
                      <Button
                        onClick={() => setSelectedBlog(blog)}
                        variant="outline"
                        size="sm"
                        className="border-blue-300 text-blue-600 hover:bg-blue-50"
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        Preview
                      </Button>
                    )}

                    {blog.wordpress_url && (
                      <Button
                        onClick={() => window.open(blog.wordpress_url!, "_blank")}
                        variant="outline"
                        size="sm"
                        className={`${
                          blog.is_published === true
                            ? "border-green-300 text-green-600 hover:bg-green-50" 
                            : "border-gray-300 text-gray-600 hover:bg-gray-50"
                        }`}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        {(() => {
                          console.log(`🔍 Button text for blog "${blog.title}": is_published=${blog.is_published}, wordpress_url=${blog.wordpress_url}`)
                          return blog.is_published === true ? "View Live" : "View Draft"
                        })()}
                      </Button>
                    )}
                  </div>
                </div>
                             ))
             )}
               
               {/* Page Numbers - Bottom */}
               {totalPages > 1 && (
                 <div className="mt-6 pt-6 border-t border-gray-200">
                   <div className="flex justify-center">
                     <Pagination>
                       <PaginationContent>
                         <PaginationItem>
                           <PaginationPrevious 
                             onClick={() => handlePageChange(currentPage - 1)}
                             className={currentPage <= 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                             size="default"
                           />
                         </PaginationItem>
                         
                         {/* Page Numbers */}
                         {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                           <PaginationItem key={pageNum}>
                             <PaginationLink
                               onClick={() => handlePageChange(pageNum)}
                               isActive={pageNum === currentPage}
                               className="cursor-pointer"
                               size="default"
                             >
                               {pageNum}
                             </PaginationLink>
                           </PaginationItem>
                         ))}
                         
                         <PaginationItem>
                           <PaginationNext 
                             onClick={() => handlePageChange(currentPage + 1)}
                             className={currentPage >= totalPages ? "pointer-events-none opacity-50" : "cursor-pointer"}
                             size="default"
                           />
                         </PaginationItem>
                       </PaginationContent>
                     </Pagination>
                   </div>
                 </div>
               )}
               
             </div>
           )}
        </CardContent>
      </Card>

      {/* Blog Preview Modal */}
      {selectedBlog && <BlogPreviewModal blog={selectedBlog} onClose={() => setSelectedBlog(null)} />}

      {/* Content Generation Modal */}
      {showContentGenerationModal && project && (
        <ContentGenerationModal
          isOpen={showContentGenerationModal}
          projectId={project.id}
          projectName={project.name}
          serpApiEnabled={project.serp_api_on}
          serpApiContents={project.serp_api_contents}
          onClose={() => setShowContentGenerationModal(false)}
        />
      )}

      {/* WordPress Publish Modal */}
      {showWordPressPublishModal && blogToPublish && (
        <WordPressPublishModal
          isOpen={showWordPressPublishModal}
          blogId={blogToPublish.id}
          blogTitle={blogToPublish.title}
          onClose={() => setShowWordPressPublishModal(false)}
          onSuccess={() => {
            setBlogToPublish(null);
            setShowWordPressPublishModal(false);
            onUpdate();
            // Refresh the blog list to show updated statuses
            refreshBlogList();
          }}
        />
      )}
    </div>
  )
}
