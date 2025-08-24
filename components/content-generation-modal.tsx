"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { X, FileText, Brain, Settings, Play, Clock, ArrowLeft } from "lucide-react"
import { Project } from "@/lib/storage"
import { storage } from "@/lib/storage"

interface ContentGenerationModalProps {
  project: Project
  onClose: () => void
  onStartGeneration: () => void
}

export function ContentGenerationModal({ project, onClose, onStartGeneration }: ContentGenerationModalProps) {
  const [generationPrompt, setGenerationPrompt] = useState("")
  const [numBlogs, setNumBlogs] = useState(project.total_blogs)
  const [aiModel, setAiModel] = useState(project.draft_creation_model || "openai")
  const [batchSize, setBatchSize] = useState(5)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    console.log("Form submitted with:", { generationPrompt, numBlogs, aiModel, batchSize })
    
    if (!generationPrompt.trim()) {
      alert("Please enter a generation prompt")
      return
    }
    
    setLoading(true)

    try {
      // Call the backend API to start content generation
      const response = await fetch('http://localhost:8000/api/blogs/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Note: In production, you'd include the user's JWT token here
          // 'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({
          project_id: project.id,
          prompt: generationPrompt,
          num_blogs: numBlogs,
          ai_model: aiModel,
          batch_size: batchSize
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const result = await response.json()
      console.log("Content generation started:", result)

      // Update project status to running
      storage.updateProject(project.id, { 
        status: "running", 
        updated_at: new Date().toISOString() 
      })

      // Show success message
      alert(`✅ Content generation started! Task ID: ${result.task_id}\n\nEstimated time: ${result.estimated_time} minutes\n\nYou can monitor progress in the project details.`)

      // Call the parent handler
      onStartGeneration()
    } catch (error) {
      console.error("Failed to start content generation:", error)
      
      if (error.message.includes('Failed to fetch')) {
        alert("❌ Cannot connect to backend server. Please ensure the backend is running on localhost:8000")
      } else {
        alert(`❌ Failed to start content generation: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-4xl bg-white shadow-xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="sticky top-0 bg-white z-10 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Button
                onClick={onClose}
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-gray-600 p-2"
                title="Go back to projects"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <CardTitle className="text-xl font-semibold text-gray-900">
                  {project.status === "pending" ? "Start Content Generation" : "Resume Content Generation"}
                </CardTitle>
                <CardDescription className="text-gray-600">
                  Configure parameters for generating {project.total_blogs} blogs for "{project.name}"
                </CardDescription>
              </div>
            </div>
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Project Information */}
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Project Details</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Name:</span>
                  <p className="font-medium text-gray-900">{project.name}</p>
                </div>
                <div>
                  <span className="text-gray-600">Description:</span>
                  <p className="font-medium text-gray-900">{project.description}</p>
                </div>
                <div>
                  <span className="text-gray-600">Total Blogs:</span>
                  <p className="font-medium text-gray-900">{project.total_blogs}</p>
                </div>
                <div>
                  <span className="text-gray-600">AI Model:</span>
                  <p className="font-medium text-gray-900 capitalize">{aiModel}</p>
                </div>
              </div>
            </div>

            {/* Instructions */}
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <FileText className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-700">
                  <p className="font-medium mb-1">Ready to generate content?</p>
                  <p>Fill in the generation prompt below to start creating your {project.total_blogs} blogs. You can adjust the number of blogs and batch size as needed.</p>
                </div>
              </div>
            </div>

            {/* Generation Parameters */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Generation Prompt <span className="text-red-500">*</span>
                </label>
                <Textarea
                  placeholder="Describe what kind of content you want to generate (e.g., 'Write comprehensive guides about digital marketing strategies for small businesses')"
                  value={generationPrompt}
                  onChange={(e) => setGenerationPrompt(e.target.value)}
                  rows={4}
                  required
                  className="w-full border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Be specific about the topic, tone, and target audience
                </p>
                {generationPrompt.trim() && (
                  <p className="text-xs text-green-600 mt-1">
                    ✓ Prompt entered - Form is ready to submit
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Number of Blogs
                  </label>
                  <Input
                    type="number"
                    min="1"
                    max={project.total_blogs}
                    value={numBlogs}
                    onChange={(e) => setNumBlogs(parseInt(e.target.value) || 1)}
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Max: {project.total_blogs} blogs
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Batch Size
                  </label>
                  <Input
                    type="number"
                    min="1"
                    max="10"
                    value={batchSize}
                    onChange={(e) => setBatchSize(parseInt(e.target.value) || 1)}
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Blogs processed simultaneously (1-10)
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Model
                </label>
                <div className="flex space-x-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="aiModel"
                      value="openai"
                      checked={aiModel === "openai"}
                      onChange={(e) => setAiModel(e.target.value)}
                      className="text-indigo-600"
                    />
                    <span className="text-sm text-gray-700">OpenAI GPT-4</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="aiModel"
                      value="gemini"
                      checked={aiModel === "gemini"}
                      onChange={(e) => setAiModel(e.target.value)}
                      className="text-indigo-600"
                    />
                    <span className="text-sm text-gray-700">Gemini Pro</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Estimated Time */}
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-blue-600" />
                <span className="text-sm text-blue-700">
                  Estimated generation time: {Math.ceil(numBlogs / batchSize)} minutes
                </span>
              </div>
            </div>

            {/* Where to Check Generated Content */}
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <FileText className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-green-700">
                  <p className="font-medium mb-1">📍 Where to Check Generated Content:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li><strong>Project Details:</strong> Click on your project to see blog status</li>
                    <li><strong>Backend API:</strong> GET /api/blogs/project/{project.id}</li>
                    <li><strong>Database:</strong> Check 'blogs' table in Supabase</li>
                    <li><strong>Console Logs:</strong> Backend terminal shows progress</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-3 pt-4 border-t border-gray-200">
              <Button
                type="button"
                onClick={onClose}
                variant="outline"
                className="flex-1 border-gray-300 text-gray-600 hover:bg-gray-50 bg-transparent"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Projects
              </Button>
              
              {/* Debug button - remove this in production */}
              <Button
                type="button"
                onClick={() => console.log("Current form state:", { generationPrompt, numBlogs, aiModel, batchSize })}
                variant="outline"
                size="sm"
                className="px-3 text-xs"
              >
                Debug
              </Button>
              
              <Button
                type="submit"
                disabled={loading || !generationPrompt.trim() || numBlogs < 1}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Clock className="h-4 w-4 mr-2 animate-spin" />
                    Starting Generation...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    {project.status === "pending" ? "Start Generation" : "Resume Generation"}
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
