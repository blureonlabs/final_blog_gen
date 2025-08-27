"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { BlogPreviewModal } from "@/components/blog-preview-modal"
import { ArrowLeft, FileText, Eye, ExternalLink, Clock, CheckCircle, XCircle, Upload } from "lucide-react"
import { storage, type Project, type Blog } from "@/lib/storage"
import { ContentGenerationModal } from "@/components/content-generation-modal"

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
  const [isGeneratingContent, setIsGeneratingContent] = useState(false)

  useEffect(() => {
    console.log("🔄 ProjectDetail useEffect triggered with initialProject:", initialProject)
    console.log("🔍 initialProject num_blogs:", initialProject?.num_blogs)
    console.log("🔍 initialProject status:", initialProject?.status)
    if (initialProject) {
      loadProjectData(initialProject)
    }
  }, [initialProject])

  const loadProjectData = async (foundProject: Project) => {
    console.log("🚀 loadProjectData called with project:", foundProject)
    console.log("🔍 Initial project num_blogs:", foundProject?.num_blogs)
    console.log("🔍 Initial project ID:", foundProject?.id)
    console.log("🔍 Initial project status:", foundProject?.status)

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
        const response = await fetch(`http://localhost:8000/api/blogs/project/${projectId}`)
        console.log("📡 Backend response status:", response.status)
        
        if (response.ok) {
          const apiData = await response.json()
          console.log("📊 Backend API response:", apiData)
          console.log("📝 Raw blogs from backend:", apiData.blogs)
          
          if (apiData.blogs && apiData.blogs.length > 0) {
            // Map backend blog statuses to frontend statuses
                         const mappedBlogs = apiData.blogs.map((blog: any) => {
               const mappedStatus = mapBackendStatusToFrontend(blog.status)
               console.log(`🔄 Mapping blog "${blog.title}": ${blog.status} → ${mappedStatus}`)
               return {
                 id: blog.id,
                 title: blog.title,
                 status: mappedStatus,
                 word_count: blog.word_count || 0,
                 created_at: blog.created_at,
                 published_at: blog.status === "ready" ? blog.created_at : undefined,
                 content: "", // Content is now stored in Supabase Storage, not in database
                 prompt: blog.prompt || "",
                 ai_model: blog.ai_model || "",
                 wordpress_url: blog.wordpress_url || null,
                 storage_path: blog.storage_path || null,
                 storage_bucket: blog.storage_bucket || null
               }
             })
            
            console.log("✅ Final mapped blogs for frontend:", mappedBlogs)
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
             content: blogContent,
             prompt: `Generate content about ${foundProject.name}`,
             ai_model: "openai",
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
    console.log("[v0] Regenerating failed blogs...")
    const updatedBlogs = blogs.map((blog) =>
      blog.status === "failed" ? { ...blog, status: "generating" as Blog["status"] } : blog,
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
    const updatedBlogs = blogs.map((blog) =>
      blog.id === blogId && blog.status === "draft" ? { ...blog, status: "publishing" as Blog["status"] } : blog,
    )
    setBlogs(updatedBlogs)

    // Simulate publishing process
    setTimeout(() => {
      const publishedBlogs = updatedBlogs.map((blog) =>
        blog.id === blogId && blog.status === "publishing"
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
    }, 1000)
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
      
      // Show success message
      alert("Content generation started successfully! Check the logs for progress.")
      
    } catch (error) {
      console.error("❌ Error starting content generation:", error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      alert(`Failed to start content generation: ${errorMessage}`)
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

  const publishedBlogs = blogs.filter((blog) => blog.status === "published").length
  const draftBlogs = blogs.filter((blog) => blog.status === "draft").length
  const generatingBlogs = blogs.filter((blog) => blog.status === "generating").length
  const failedBlogs = blogs.filter((blog) => blog.status === "failed").length
  const postingBlogs = blogs.filter((blog) => blog.status === "publishing").length

  const progressPercentage = project.num_blogs > 0 ? (blogs.length / project.num_blogs) * 100 : 0
  const publishedPercentage = project.num_blogs > 0 ? (publishedBlogs / project.num_blogs) * 100 : 0

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Button
            onClick={onBack}
            variant="outline"
            size="sm"
            className="border-gray-300 text-gray-600 hover:bg-gray-50 bg-transparent"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
          <h2 className="text-2xl font-bold text-gray-900">{project.name}</h2>
        </div>

        <div className="flex items-center space-x-3">
          {/* Refresh Button */}
          <Button
            onClick={(e) => {
              e.preventDefault()
              loadProjectData(project)
            }}
            variant="outline"
            size="sm"
            className="border-gray-300 text-gray-600 hover:bg-gray-50"
            title="Refresh content"
          >
            <Clock className="h-4 w-4 mr-2" />
            Refresh
          </Button>

                     {/* Start Content Generation Button */}
           {(project.status === "pending" || project.status === "in_progress" || project.status === "ready") && (
             <Button
               onClick={handleStartContentGeneration}
               disabled={isGeneratingContent}
               className={`${
                 isGeneratingContent
                   ? "bg-gray-400 cursor-not-allowed"
                   : "bg-green-600 hover:bg-green-700"
               } text-white`}
               size="sm"
               title={isGeneratingContent ? "Content generation already in progress..." : "Start generating blog content"}
             >
               {isGeneratingContent ? (
                 <>
                   <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                   Starting Generation...
                 </>
               ) : (
                 <>
                   <FileText className="h-4 w-4 mr-2" />
                   {project.status === "ready"
                     ? "Start Content Generation"
                     : project.status === "pending"
                       ? "Start Content Generation"
                       : "Resume Content Generation"
                   }
                 </>
               )}
             </Button>
           )}
           
           {/* Debug info for button visibility */}
           {(() => {
             console.log("🔍 Button visibility check - project status:", project.status, "should show:", (project.status === "pending" || project.status === "in_progress" || project.status === "ready"))
             return null
           })()}

          {/* Show status when generating */}
          {project.status === "in_progress" && (
            <Button
              disabled
              className="bg-blue-600 text-white cursor-not-allowed"
              size="sm"
            >
              <Clock className="h-4 w-4 mr-2 animate-spin" />
              Generating Content...
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
              Regenerate Failed ({failedBlogs})
            </Button>
          )}

          <Button
            onClick={handleReuploadFailed}
            variant="outline"
            size="sm"
            className="border-orange-300 text-orange-600 hover:bg-orange-50 bg-transparent"
          >
            <Upload className="h-4 w-4 mr-2" />
            Reupload Failed
          </Button>

          {draftBlogs > 0 && (
            <Button onClick={handlePublishDrafts} className="bg-indigo-600 text-white hover:bg-indigo-700" size="sm">
              <CheckCircle className="h-4 w-4 mr-2" />
              Publish All Drafts ({draftBlogs})
            </Button>
          )}
        </div>
      </div>

      {/* Project Overview */}
      <Card className="bg-white shadow-sm mb-8">
        <CardHeader>
          <CardTitle className="text-xl text-gray-900">{project.description}</CardTitle>
          <CardDescription className="text-gray-600">
            Created on {new Date(project.created_at).toLocaleDateString()}
          </CardDescription>
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
                    {blogs.length} of {project.num_blogs} blogs
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
              Your blogs are being generated. Here's how to monitor progress:
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
          <CardTitle className="text-lg text-gray-900">Generated Blogs</CardTitle>
          <CardDescription className="text-gray-600">
            {blogs.length > 0 ? `${blogs.length} blogs generated` : "No blogs generated yet"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {blogs.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No blogs have been generated yet.</p>
              <p className="text-sm text-gray-500 mt-2">Blog generation will start automatically.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {blogs.map((blog) => (
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
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {blog.status === "generating" && (
                      <div className="flex items-center space-x-2 text-blue-600">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        <span className="text-sm">Generating...</span>
                      </div>
                    )}

                    {blog.status === "draft" && (
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
                          blog.status === "published" 
                            ? "border-green-300 text-green-600 hover:bg-green-50" 
                            : "border-gray-300 text-gray-600 hover:bg-gray-50"
                        }`}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        {blog.status === "published" ? "View Live" : "View Draft"}
                      </Button>
                    )}
                  </div>
                </div>
              ))}
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
          onClose={() => setShowContentGenerationModal(false)}
        />
      )}
    </div>
  )
}
