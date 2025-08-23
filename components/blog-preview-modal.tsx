"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { X, ExternalLink } from "lucide-react"

interface Blog {
  id: string
  title: string
  content: string
  seo_meta: any
  wp_url: string | null
  status: "draft" | "published" | "failed"
  created_at: string
}

interface BlogPreviewModalProps {
  blog: Blog
  onClose: () => void
}

export function BlogPreviewModal({ blog, onClose }: BlogPreviewModalProps) {
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
              {blog.wp_url && (
                <Button
                  onClick={() => window.open(blog.wp_url, "_blank")}
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

          {/* Blog Content */}
          <div className="prose max-w-none">
            {blog.content ? (
              <div
                className="text-gray-800 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: blog.content.replace(/\n/g, "<br>") }}
              />
            ) : (
              <p className="text-gray-600 italic">No content available</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
