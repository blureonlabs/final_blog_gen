"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { X, ExternalLink, Loader2 } from "lucide-react"

interface Blog {
  id: string
  title: string
  content?: string
  seo_meta?: any
  wordpress_url?: string | null
  status: "generating" | "draft" | "publishing" | "published" | "failed" | "ready"
  created_at: string
  word_count?: number
  prompt?: string
  ai_model?: string
  storage_path?: string | null | undefined
  storage_bucket?: string | null | undefined
}

interface BlogPreviewModalProps {
  blog: Blog
  onClose: () => void
}

export function BlogPreviewModal({ blog, onClose }: BlogPreviewModalProps) {
  const [blogContent, setBlogContent] = useState<string | null>(blog.content || null)
  const [isLoadingContent, setIsLoadingContent] = useState(false)
  const [contentError, setContentError] = useState<string | null>(null)

  // Fetch blog content from backend when modal opens
  useEffect(() => {
    const fetchBlogContent = async () => {
      // If we already have content, don't fetch again
      if (blogContent) return
      
      console.log("🔍 Fetching blog content for blog ID:", blog.id)
      console.log("🔍 Blog status:", blog.status)
      console.log("🔍 Blog object:", blog)
      
      setIsLoadingContent(true)
      setContentError(null)
      
      try {
        const response = await fetch(`http://localhost:8000/api/content-generation/blog/${blog.id}/public`)
        console.log("📡 Response status:", response.status)
        console.log("📡 Response headers:", response.headers)
        
        if (response.ok) {
          const blogData = await response.json()
          console.log("📝 Fetched blog data:", blogData)
          console.log("📝 Content length:", blogData.content ? blogData.content.length : 0)
          console.log("📝 Content preview:", blogData.content ? blogData.content.substring(0, 100) + "..." : "No content")
          
          setBlogContent(blogData.content || "No content available")
        } else {
          const errorText = await response.text()
          console.error("❌ Failed to fetch blog:", response.status, response.statusText)
          console.error("❌ Error response:", errorText)
          setContentError("Failed to load blog content")
        }
      } catch (error) {
        console.error("Error fetching blog content:", error)
        setContentError("Error loading blog content")
      } finally {
        setIsLoadingContent(false)
      }
    }

    fetchBlogContent()
  }, [blog.id, blog.status, blogContent])

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-4xl max-h-[90vh] bg-white shadow-xl overflow-hidden">
        <CardHeader className="border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-bold text-gray-900">{blog.title || "Untitled Blog"}</CardTitle>
              <CardDescription className="text-gray-600">
                Created on {new Date(blog.created_at).toLocaleDateString()} • Status: {blog.status}
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              {blog.wordpress_url && (
                <Button
                  onClick={() => window.open(blog.wordpress_url!, "_blank")}
                  variant="outline"
                  size="sm"
                  className="border-gray-300 text-gray-600 hover:bg-gray-50"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Live
                </Button>
              )}
              <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-400 hover:text-gray-600">
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="overflow-y-auto max-h-[calc(90vh-120px)] p-6">
          {/* SEO Meta Information */}
          {blog.seo_meta && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-2">SEO Information</h3>
              <div className="space-y-2 text-sm">
                {blog.seo_meta.meta_description && (
                  <div>
                    <span className="font-medium text-gray-700">Meta Description:</span>
                    <p className="text-gray-600 mt-1">{blog.seo_meta.meta_description}</p>
                  </div>
                )}
                {blog.seo_meta.keywords && (
                  <div>
                    <span className="font-medium text-gray-700">Keywords:</span>
                    <p className="text-gray-600 mt-1">{blog.seo_meta.keywords}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Blog Details */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="font-medium text-blue-900 mb-3">Blog Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {blog.word_count && (
                <div>
                  <span className="font-medium text-blue-700">Word Count:</span>
                  <span className="ml-2 text-blue-600">{blog.word_count}</span>
                </div>
              )}
              {blog.ai_model && (
                <div>
                  <span className="font-medium text-blue-700">AI Model:</span>
                  <span className="ml-2 text-blue-600">{blog.ai_model}</span>
                </div>
              )}
              {blog.prompt && (
                <div className="col-span-2">
                  <span className="font-medium text-blue-700">Generation Prompt:</span>
                  <p className="text-blue-600 mt-1">{blog.prompt}</p>
                </div>
              )}
            </div>
          </div>

          {/* Blog Content */}
          <div className="prose max-w-none">
            <h3 className="font-medium text-gray-900 mb-4">Blog Content</h3>
            {isLoadingContent ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600 mr-3" />
                <span className="text-gray-600">Loading blog content...</span>
              </div>
            ) : contentError ? (
              <div className="text-center py-8">
                <p className="text-red-600 mb-2">{contentError}</p>
                <Button 
                  onClick={() => window.location.reload()} 
                  variant="outline" 
                  size="sm"
                >
                  Retry
                </Button>
              </div>
            ) : blogContent ? (
              <div
                className="text-gray-800 leading-relaxed whitespace-pre-wrap bg-white p-6 border border-gray-200 rounded-lg"
                dangerouslySetInnerHTML={{ __html: blogContent.replace(/\n/g, "<br>") }}
              />
            ) : (
              <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-gray-600 italic">No content available</p>
                <p className="text-sm text-gray-500 mt-2">The blog content could not be loaded.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
