"use client"

import type React from "react"
import type { ReactElement } from "react"
import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { X, Globe, Key, AlertTriangle, Brain, CheckCircle, Zap, ChevronDown, Search } from "lucide-react"
import { supabaseApi, type Project, type UserData } from "@/lib/supabase-api"

interface NewProjectModalProps {
  onClose: () => void
  onSuccess: (project: Project) => void
  userId: string
  userData: UserData
}

// Custom Dropdown Component
interface CustomDropdownProps {
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
  placeholder?: string
  className?: string
  disabled?: boolean
}

function CustomDropdown({ value, onChange, options, placeholder, className = "", disabled = false }: CustomDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selectedOption = options.find(opt => opt.value === value)

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-left flex items-center justify-between text-sm ${
          disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:bg-gray-100'
        }`}
      >
        <span className={selectedOption ? 'text-gray-900' : 'text-gray-500'}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                onChange(option.value)
                setIsOpen(false)
              }}
              className={`w-full px-3 py-2 text-left text-sm hover:bg-indigo-50 hover:text-indigo-900 transition-colors border-b border-gray-100 last:border-b-0 ${
                option.value === value 
                  ? 'bg-indigo-100 text-indigo-900 border-r-2 border-indigo-500' 
                  : 'text-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                {option.value === value && (
                  <CheckCircle className="w-4 h-4 text-indigo-600" />
                )}
                <span className={option.value === value ? 'ml-0' : 'ml-6'}>
                  {option.label}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export function NewProjectModal({ onClose, onSuccess, userId, userData }: NewProjectModalProps): ReactElement {
  // Safety check - if userData is not provided, show loading state
  if (!userData) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <Card className="w-full max-w-4xl bg-white shadow-xl p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading project creation form...</p>
          </div>
        </Card>
      </div>
    )
  }

  // Function to reset form state
  const resetForm = () => {
    console.log("🔄 Starting form reset...")
    setName("")
    setDescription("")
    setNumBlogs(10)
    setSelectedWordPressAccount("")
    setSelectedOpenAIKey("")
    setSelectedGeminiKey("")
    setSelectedSerpKey("")
    setSelectedFalKey("")
    setSerpApiEnabled(false)
    setEnhancedResearch(false)
    setGenerateImages(false)
    setNumImagesPerBlog(1)
    setSelectedAIModel("openai")
    setLoading(false)
    setError("")
    setShowUpgradePrompt(false)
    
    console.log("🔄 Form reset completed - SerpAPI:", false, "Enhanced Research:", false, "Generate Images:", false, "Num Images:", 1, "Fal AI:", false)
  }

  // Reset form when modal closes or unmounts
  useEffect(() => {
    // Reset form when component mounts
    console.log("🔄 Modal mounted - initializing form state")
    console.log("🔄 Modal component instance created at:", new Date().toISOString())
    resetForm()
    
    return () => {
      console.log("🔄 Modal unmounting - cleaning up form state")
      console.log("🔄 Modal component instance destroyed at:", new Date().toISOString())
      resetForm()
    }
  }, [])



  // Additional cleanup when modal is about to close
  const handleClose = () => {
    console.log("🔄 Modal closing - cleaning up before close")
    resetForm()
    onClose()
  }

  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [numBlogs, setNumBlogs] = useState(10)
  const [selectedWordPressAccount, setSelectedWordPressAccount] = useState("")
  const [selectedOpenAIKey, setSelectedOpenAIKey] = useState("")
  const [selectedGeminiKey, setSelectedGeminiKey] = useState("")
  const [selectedSerpKey, setSelectedSerpKey] = useState("")
  const [selectedFalKey, setSelectedFalKey] = useState("")
  
  // Add SerpAPI toggle state
  const [serpApiEnabled, setSerpApiEnabled] = useState(false)
  const [enhancedResearch, setEnhancedResearch] = useState(false)
  
  // Image generation settings
  const [generateImages, setGenerateImages] = useState(false)
  const [numImagesPerBlog, setNumImagesPerBlog] = useState(1)
  
  // Debug logging for state changes
  useEffect(() => {
    console.log("🔍 State changed - serpApiEnabled:", serpApiEnabled, "enhancedResearch:", enhancedResearch)
  }, [serpApiEnabled, enhancedResearch])
  
  useEffect(() => {
    console.log("🖼️ Image generation state - generateImages:", generateImages, "numImagesPerBlog:", numImagesPerBlog)
  }, [generateImages, numImagesPerBlog])
  
  // Simplified AI model selection - just one model
  const [selectedAIModel, setSelectedAIModel] = useState<"openai" | "gemini">("openai")
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [showUpgradePrompt, setShowUpgradePrompt] = useState(false)



  // Safety check for userData.usage - provide default values if missing
  const safeUserData = {
    ...userData,
    usage: userData.usage || {
      blogs_generated: 0,
      blogs_limit: 50,
      wordpress_accounts_used: 0,
      wordpress_accounts_limit: 10
    }
  }

  const remainingBlogs = safeUserData.usage.blogs_limit - safeUserData.usage.blogs_generated
  const isDemoMode = !process.env.NEXT_PUBLIC_SUPABASE_URL

  // Auto-select required fields after form reset
  useEffect(() => {
    if (!isDemoMode && userData) {
      console.log("🔄 Auto-selecting required fields...")
      
      // Auto-select first WordPress account if only one is available
      if (userData.wordpressAccounts?.length === 1 && !selectedWordPressAccount) {
        console.log("🔄 Auto-selecting single WordPress account:", userData.wordpressAccounts[0].id)
        setSelectedWordPressAccount(userData.wordpressAccounts[0].id)
      }
      
      // Auto-select first API keys if only one is available
      if (userData.apiKeys) {
        const openAIKeys = userData.apiKeys.filter(k => k.service === "openai")
        const geminiKeys = userData.apiKeys.filter(k => k.service === "gemini")
        const serpKeys = userData.apiKeys.filter(k => k.service === "serp")
        const falKeys = userData.apiKeys.filter(k => k.service === "fal")
        
        if (openAIKeys.length === 1 && !selectedOpenAIKey) {
          console.log("🔄 Auto-selecting single OpenAI key:", openAIKeys[0].id)
          setSelectedOpenAIKey(openAIKeys[0].id)
        }
        if (geminiKeys.length === 1 && !selectedGeminiKey) {
          console.log("🔄 Auto-selecting single Gemini key:", geminiKeys[0].id)
          setSelectedGeminiKey(geminiKeys[0].id)
        }
        if (serpKeys.length === 1 && !selectedSerpKey) {
          console.log("🔄 Auto-selecting single SERP key:", serpKeys[0].id)
          setSelectedSerpKey(serpKeys[0].id)
        }
        if (falKeys.length === 1 && !selectedFalKey) {
          console.log("🔄 Auto-selecting single Fal AI key:", falKeys[0].id)
          setSelectedFalKey(falKeys[0].id)
        }
      }
    }
  }, [isDemoMode, userData, selectedWordPressAccount, selectedOpenAIKey, selectedGeminiKey, selectedSerpKey, selectedFalKey])

  // Debug button state
  useEffect(() => {
    const buttonDisabled = loading || !name.trim() || !description.trim() || (!isDemoMode && !selectedWordPressAccount)
    console.log("🔍 Button state check:", {
      loading,
      nameEmpty: !name.trim(),
      descriptionEmpty: !description.trim(),
      noWordPressAccount: !isDemoMode && !selectedWordPressAccount,
      isDemoMode,
      selectedWordPressAccount,
      buttonDisabled
    })
  }, [loading, name, description, isDemoMode, selectedWordPressAccount])

  useEffect(() => {
    if (userData.wordpressAccounts.length > 0) {
      setSelectedWordPressAccount(userData.wordpressAccounts[0].id)
    }

    const defaultOpenAI =
      userData.apiKeys.find((k) => k.service === "openai" && k.is_default) ||
      userData.apiKeys.find((k) => k.service === "openai")
    const defaultGemini =
      userData.apiKeys.find((k) => k.service === "gemini" && k.is_default) ||
      userData.apiKeys.find((k) => k.service === "gemini")
    const defaultSerp =
      userData.apiKeys.find((k) => k.service === "serp" && k.is_default) ||
      userData.apiKeys.find((k) => k.service === "serp")
    const defaultFal =
      userData.apiKeys.find((k) => k.service === "fal" && k.is_default) ||
      userData.apiKeys.find((k) => k.service === "fal")

    setSelectedOpenAIKey(defaultOpenAI?.id || "")
    setSelectedGeminiKey(defaultGemini?.id || "")
    setSelectedSerpKey(defaultSerp?.id || "")
    setSelectedFalKey(defaultFal?.id || "")
    
    // Reset SerpAPI toggles to default state
    setSerpApiEnabled(false)
    setEnhancedResearch(false)
    
    console.log("🔄 Modal initialized - SerpAPI:", false, "Enhanced Research:", false)
  }, []) // Empty dependency array - only run once when component mounts

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    console.log("🚀 Form submission started at:", new Date().toISOString())
    console.log("🔍 Current form state:", { name, description, numBlogs, loading })
    
    // Prevent multiple submissions
    if (loading) {
      console.log("⚠️ Form submission blocked - already loading")
      return
    }

    const canCreateProject =
      userData.wordpressAccounts.length > 0 &&
      safeUserData.usage.wordpress_accounts_used < safeUserData.usage.wordpress_accounts_limit

    if (numBlogs > remainingBlogs) {
      setShowUpgradePrompt(true)
      return
    }

    // In demo mode, allow project creation without strict validation
    if (!isDemoMode && !canCreateProject) {
      setError("You've reached your WordPress account limit. Please upgrade to add more accounts.")
      return
    }

    // In demo mode, allow creation with minimal requirements
    if (!isDemoMode && (!selectedWordPressAccount || !selectedOpenAIKey || !selectedGeminiKey || !selectedSerpKey)) {
      setError("Please configure all required accounts and API keys in Settings first.")
      return
    }

    // For demo mode, only require basic project info
    if (isDemoMode && (!name.trim() || !description.trim())) {
      setError("Please provide project name and description.")
      return
    }

    setLoading(true)
    setError("")

    // Add timeout to prevent hanging
    const submissionTimeout = setTimeout(() => {
      if (loading) {
        console.error("❌ Project creation timed out after 30 seconds")
        setError("Project creation timed out. Please try again.")
        setLoading(false)
      }
    }, 30000)

    try {
      const selectedWPAccount = userData.wordpressAccounts.find((a) => a.id === selectedWordPressAccount)
      const selectedOpenAI = userData.apiKeys.find((k) => k.id === selectedOpenAIKey)
      const selectedGeminiAPI = userData.apiKeys.find((k) => k.id === selectedGeminiKey)
      const selectedSerpAPI = userData.apiKeys.find((k) => k.id === selectedSerpKey)
      const selectedFalAPI = userData.apiKeys.find((k) => k.id === selectedFalKey)

      // Log final state before submission
      console.log("🚀 Submitting project with state:", {
        serpApiEnabled,
        enhancedResearch,
        selectedAIModel,
        numBlogs,
        generateImages,
        numImagesPerBlog
      })
      
      // Simplified project creation
      const newProject = await supabaseApi.addProject({
        name: name.trim(),
        description: description.trim(),
        num_blogs: numBlogs,
        completed_blogs: 0,
        status: "ready",
        wordpress_account_id: selectedWPAccount?.id || (isDemoMode ? "demo-wp-account" : ""),
        api_keys: {
          openai: selectedOpenAI?.id || (isDemoMode ? "demo-openai-key" : ""),
          gemini: selectedGeminiAPI?.id || (isDemoMode ? "demo-gemini-key" : ""),
          serp: selectedSerpAPI?.id || (isDemoMode ? "demo-serb-key" : ""),
          fal: selectedFalAPI?.id || (isDemoMode ? "demo-fal-key" : ""),
        },
        // AI Model Configuration - using draft_creation_model from database
        draft_creation_model: selectedAIModel,  // Single model selection
        // Add SerpAPI configuration
        serp_api_on: serpApiEnabled,
        serp_api_contents: null,  // Will be populated during research phase
        enhanced_research: enhancedResearch,  // Add enhanced research setting
        // Add image generation configuration
        generate_images: generateImages,
        num_images_per_blog: numImagesPerBlog
      })

      console.log("✅ Project created successfully:", newProject)
      console.log("🔍 Project ID after creation:", newProject.id)
      console.log("🔍 Project status after creation:", newProject.status)
      console.log("🔍 Project object type:", typeof newProject)
      
      console.log("✅ Calling onSuccess with project:", newProject)
      onSuccess(newProject)
      
      // Show demo mode message if Supabase is not configured
      if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
        setError("Project created in demo mode. To save projects permanently, configure Supabase in Settings.")
        // Clear the error after 5 seconds
        setTimeout(() => setError(""), 5000)
      }
      
      console.log("🔄 Resetting form after successful creation...")
      resetForm()
      console.log("🔄 Closing modal after successful creation...")
      onClose()
    } catch (error: any) {
      console.error("❌ Project creation failed:", error)
      
      // Provide more helpful error messages
      if (error.message && error.message.includes("projects_status_check")) {
        setError("Database constraint error: 'ready' status not allowed. Please run the database migration script in Supabase.")
      } else if (error.message && error.message.includes("Supabase not configured")) {
        setError("Supabase not configured. Project created in demo mode only.")
        // Create a mock project for demo mode
        const mockProject = {
          id: `mock-project-${Date.now()}`,
          name: name.trim(),
          description: description.trim(),
          num_blogs: numBlogs,
          completed_blogs: 0,
          status: "ready" as const,
          wordpress_account_id: "demo-wp-account",
          api_keys: {
            openai: "demo-openai-key",
            gemini: "demo-gemini-key",
            serp: "demo-serb-key",
            fal: "demo-fal-key",
          },
          draft_creation_model: selectedAIModel,
          generate_images: generateImages,
          num_images_per_blog: numImagesPerBlog,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
        onSuccess(mockProject)
        resetForm()
        onClose()
        return
      } else {
        setError(error.message || "Failed to create project. Please try again.")
      }
    } finally {
      clearTimeout(submissionTimeout)
      setLoading(false)
    }
  }

  const openAIKeys = userData.apiKeys.filter((k) => k.service === "openai")
  const geminiKeys = userData.apiKeys.filter((k) => k.service === "gemini")
  const serpKeys = userData.apiKeys.filter((k) => k.service === "serp")
  const falKeys = userData.apiKeys.filter((k) => k.service === "fal")

  // Simplified model options
  const aiModelOptions = [
    { value: "openai", label: "OpenAI GPT-5 Nano - Advanced & Fast" },
    { value: "gemini", label: "Gemini 2.0 Flash - Fast & Efficient" }
  ]

  const wordpressOptions = userData.wordpressAccounts.map(account => ({
    value: account.id,
    label: `${account.name} (${account.site_url})`
  }))

  const openAIOptions = openAIKeys.map(key => ({
    value: key.id,
    label: `${key.name} ${key.is_default ? "(Default)" : ""}`
  }))

  const geminiOptions = geminiKeys.map(key => ({
    value: key.id,
    label: `${key.name} ${key.is_default ? "(Default)" : ""}`
  }))

  const serpOptions = serpKeys.map(key => ({
    value: key.id,
    label: `${key.name} ${key.is_default ? "(Default)" : ""}`
  }))

  const falOptions = falKeys.map(key => ({
    value: key.id,
    label: `${key.name} ${key.is_default ? "(Default)" : ""}`
  }))

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-4xl bg-white shadow-xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-semibold text-gray-900">Create New Project</CardTitle>
              <CardDescription className="text-gray-600">
                Set up a new blog generation project with your preferred AI models and settings
              </CardDescription>
            </div>
            <Button
              onClick={handleClose}
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          
          {/* Demo Mode Indicator */}
          {!process.env.NEXT_PUBLIC_SUPABASE_URL && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <p className="text-sm text-yellow-700">
                  Demo Mode: Projects will be created locally but not saved to database. Configure Supabase in Settings for permanent storage.
                </p>
              </div>
            </div>
          )}
        </CardHeader>
        <CardContent>
          {showUpgradePrompt && (
            <div className="mb-4 p-4 bg-orange-50 border border-orange-200 rounded-md">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-orange-900">Upgrade Required</h4>
                  <p className="text-sm text-orange-700 mt-1">
                    You're trying to create {numBlogs} blogs, but you only have{" "}
                    {safeUserData.usage.blogs_limit - safeUserData.usage.blogs_generated} blogs remaining on your{" "}
                    {userData.subscription.plan} plan.
                  </p>
                  <Button
                    onClick={() => {
                      resetForm()
                      onClose()
                    }}
                    size="sm"
                    className="mt-2 bg-indigo-600 hover:bg-indigo-700 text-white"
                  >
                    Upgrade Now - Starting at ₹499/month
                  </Button>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Project Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Name <span className="text-red-500">*</span>
                </label>
                <Input
                  type="text"
                  placeholder="Enter project name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description <span className="text-red-500">*</span>
                </label>
                <Textarea
                  placeholder="Describe your project goals and requirements"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full"
                  rows={3}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Number of Blogs <span className="text-red-500">*</span>
                </label>
                <Input
                  type="number"
                  min="1"
                  max={remainingBlogs}
                  value={numBlogs}
                  onChange={(e) => setNumBlogs(parseInt(e.target.value) || 1)}
                  className="w-full"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Available: {remainingBlogs} blogs
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  WordPress Account {!isDemoMode && <span className="text-red-500">*</span>}
                  {isDemoMode && <span className="text-gray-500">(Optional in demo mode)</span>}
                </label>
                {wordpressOptions.length === 0 ? (
                  <div className="text-sm text-gray-500">
                    {isDemoMode ? "No WordPress accounts configured (optional in demo mode)" : "No WordPress accounts configured"}
                  </div>
                ) : (
                  <CustomDropdown
                    value={selectedWordPressAccount}
                    onChange={setSelectedWordPressAccount}
                    options={wordpressOptions}
                    placeholder="Select WordPress Account"
                    className="w-full"
                  />
                )}
              </div>
            </div>

            {/* AI Model Configuration */}
            <div className="space-y-4">
              <h3 className="flex items-center gap-2 text-lg font-medium text-gray-900">
                <Brain className="h-5 w-5 text-purple-600" />
                AI Model Configuration
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    AI Model
                  </label>
                  <CustomDropdown
                    value={selectedAIModel}
                    onChange={(value) => setSelectedAIModel(value as "openai" | "gemini")}
                    options={aiModelOptions}
                    placeholder="Select AI Model"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {selectedAIModel === 'openai' 
                      ? "Best for creative, engaging content with personality"
                      : "Best for structured, SEO-optimized content"
                    }
                  </p>
                </div>

                {/* SerpAPI Research Toggle */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <div className="flex items-center gap-2">
                      <Search className="h-4 w-4 text-blue-600" />
                      SerpAPI Research
                    </div>
                  </label>
                  <div className="flex items-center space-x-3">
                    <button
                      type="button"
                      onClick={() => {
                        const newValue = !serpApiEnabled
                        console.log("🔄 Toggling SerpAPI from", serpApiEnabled, "to", newValue)
                        setSerpApiEnabled(newValue)
                        // If disabling SerpAPI, also disable enhanced research
                        if (!newValue) {
                          console.log("🔄 Disabling enhanced research because SerpAPI is disabled")
                          setEnhancedResearch(false)
                        }
                      }}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                        serpApiEnabled ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          serpApiEnabled ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                    <span className="text-sm text-gray-600">
                      {serpApiEnabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {serpApiEnabled 
                      ? "Will research topics using SerpAPI before generating content"
                      : "Generate content directly without external research"
                    }
                  </p>
                  
                  {/* Status indicator */}
                  <div className="mt-2 p-2 bg-gray-50 rounded-md border">
                    <div className="text-xs text-gray-600">
                      <strong>Current State:</strong>
                      <div className="mt-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${serpApiEnabled ? 'bg-blue-500' : 'bg-gray-300'}`}></span>
                          SerpAPI Research: {serpApiEnabled ? 'ON' : 'OFF'}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${enhancedResearch ? 'bg-green-500' : 'bg-gray-300'}`}></span>
                          Enhanced Research: {enhancedResearch ? 'ON' : 'OFF'}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Enhanced Research Toggle (only shown when SerpAPI is enabled) */}
                  {serpApiEnabled && (
                    <div className="mt-3 pl-4 border-l-2 border-blue-200">
                      <label className="block text-sm font-medium text-gray-600 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs">🚀</span>
                          Enhanced Research
                        </div>
                      </label>
                      <div className="flex items-center space-x-3">
                        <button
                          type="button"
                          onClick={() => {
                            const newValue = !enhancedResearch
                            console.log("🔄 Toggling Enhanced Research from", enhancedResearch, "to", newValue)
                            setEnhancedResearch(newValue)
                          }}
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                            enhancedResearch ? 'bg-green-600' : 'bg-gray-200'
                          }`}
                        >
                          <span
                            className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                              enhancedResearch ? 'translate-x-5' : 'translate-x-1'
                            }`}
                          />
                        </button>
                        <span className="text-xs text-gray-600">
                          {enhancedResearch ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {enhancedResearch 
                          ? "AI-powered queries, external links research, and content scraping"
                          : "Standard research with basic search queries"
                        }
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Image Generation Configuration */}
            <div className="space-y-4">
              <h3 className="flex items-center gap-2 text-lg font-medium text-gray-900">
                <span className="text-2xl">🖼️</span>
                Image Generation Configuration
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">🎨</span>
                      Generate Images
                    </div>
                  </label>
                  <div className="flex items-center space-x-3">
                    <button
                      type="button"
                      onClick={() => {
                        const newValue = !generateImages
                        console.log("🔄 Toggling Image Generation from", generateImages, "to", newValue)
                        setGenerateImages(newValue)
                        // If disabling image generation, reset number of images to 1
                        if (!newValue) {
                          setNumImagesPerBlog(1)
                        }
                      }}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 ${
                        generateImages ? 'bg-purple-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          generateImages ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                    <span className="text-sm text-gray-600">
                      {generateImages ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {generateImages 
                      ? "AI-generated images will be created for each blog post"
                      : "No images will be generated for blog posts"
                    }
                  </p>
                </div>

                {/* Number of Images Per Blog */}
                {generateImages && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">🔢</span>
                        Images Per Blog
                      </div>
                    </label>
                    <Input
                      type="number"
                      min="1"
                      max="4"
                      value={numImagesPerBlog}
                      onChange={(e) => setNumImagesPerBlog(parseInt(e.target.value) || 1)}
                      className="w-full"
                      disabled={!generateImages}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Choose between 1-4 images per blog post
                    </p>
                  </div>
                )}
              </div>
              
              {/* Image Generation Status */}
              {generateImages && (
                <div className="mt-2 p-3 bg-purple-50 rounded-md border border-purple-200">
                  <div className="text-xs text-purple-700">
                    <strong>Image Generation Status:</strong>
                    <div className="mt-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                        Image Generation: ON
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                        Images per Blog: {numImagesPerBlog}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* API Keys Configuration */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">API Keys Configuration</h3>
              <p className="text-sm text-gray-600">
                {isDemoMode 
                  ? "API keys are optional in demo mode. Configure them in Settings for full functionality."
                  : "Select API keys for AI content generation and search functionality."
                }
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    OpenAI API Key {!isDemoMode && <span className="text-red-500">*</span>}
                    {isDemoMode && <span className="text-gray-500">(Optional)</span>}
                  </label>
                  {openAIKeys.length === 0 ? (
                    <div className="text-xs text-gray-500">
                      {isDemoMode ? "No keys configured (optional in demo mode)" : "No keys configured"}
                    </div>
                  ) : (
                    <CustomDropdown
                      value={selectedOpenAIKey}
                      onChange={setSelectedOpenAIKey}
                      options={openAIOptions}
                      placeholder="Select Key"
                      className="text-sm"
                    />
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Gemini API Key {!isDemoMode && <span className="text-red-500">*</span>}
                    {isDemoMode && <span className="text-gray-500">(Optional)</span>}
                  </label>
                  {geminiKeys.length === 0 ? (
                    <div className="text-xs text-gray-500">
                      {isDemoMode ? "No keys configured (optional in demo mode)" : "No keys configured"}
                    </div>
                  ) : (
                    <CustomDropdown
                      value={selectedGeminiKey}
                      onChange={setSelectedGeminiKey}
                      options={geminiOptions}
                      placeholder="Select Key"
                      className="text-sm"
                    />
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    SERP API Key {!isDemoMode && <span className="text-red-500">*</span>}
                    {isDemoMode && <span className="text-gray-500">(Optional)</span>}
                  </label>
                  {serpKeys.length === 0 ? (
                    <div className="text-xs text-gray-500">
                      {isDemoMode ? "No keys configured (optional in demo mode)" : "No keys configured"}
                    </div>
                  ) : (
                    <CustomDropdown
                      value={selectedSerpKey}
                      onChange={setSelectedSerpKey}
                      options={serpOptions}
                      placeholder="Select Key"
                      className="text-sm"
                    />
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Fal AI API Key {!isDemoMode && <span className="text-gray-500">(Optional)</span>}
                    {isDemoMode && <span className="text-gray-500">(Optional)</span>}
                  </label>
                  {falKeys.length === 0 ? (
                    <div className="text-xs text-gray-500">
                      {isDemoMode ? "No keys configured (optional in demo mode)" : "No keys configured"}
                    </div>
                  ) : (
                    <CustomDropdown
                      value={selectedFalKey}
                      onChange={setSelectedFalKey}
                      options={falOptions}
                      placeholder="Select Key"
                      className="text-sm"
                    />
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    For AI image generation
                  </p>
                </div>
              </div>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <div className="flex space-x-3 pt-4">
              <Button
                type="button"
                onClick={handleClose}
                variant="outline"
                className="flex-1 border-gray-300 text-gray-600 hover:bg-gray-50 bg-transparent"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={loading || !name.trim() || !description.trim() || (!isDemoMode && !selectedWordPressAccount)}
                className="flex-1 bg-gray-800 hover:bg-gray-700 text-white disabled:opacity-50"
                onClick={() => {
                  console.log("🔍 Submit button clicked")
                  console.log("🔍 Button disabled state:", {
                    loading,
                    nameEmpty: !name.trim(),
                    descriptionEmpty: !description.trim(),
                    noWordPressAccount: !isDemoMode && !selectedWordPressAccount,
                    isDemoMode,
                    selectedWordPressAccount
                  })
                }}
              >
                {loading ? "Creating..." : "Create Project"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
