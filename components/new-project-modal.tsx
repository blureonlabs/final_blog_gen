"use client"

import type React from "react"
import type { ReactElement } from "react"
import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { X, Globe, Key, AlertTriangle, Brain, CheckCircle, Zap, ChevronDown } from "lucide-react"
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
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [numBlogs, setNumBlogs] = useState(10)
  const [selectedWordPressAccount, setSelectedWordPressAccount] = useState("")
  const [selectedOpenAIKey, setSelectedOpenAIKey] = useState("")
  const [selectedGeminiKey, setSelectedGeminiKey] = useState("")
  const [selectedSerpKey, setSelectedSerpKey] = useState("")
  
  // New AI model selection fields
  const [draftCreationModel, setDraftCreationModel] = useState<"openai" | "gemini">("openai")
  const [contentVettingModel, setContentVettingModel] = useState<"openai" | "gemini" | "same">("same")
  const [useSameModel, setUseSameModel] = useState(true)
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [showUpgradePrompt, setShowUpgradePrompt] = useState(false)

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

    setSelectedOpenAIKey(defaultOpenAI?.id || "")
    setSelectedGeminiKey(defaultGemini?.id || "")
    setSelectedSerpKey(defaultSerp?.id || "")
  }, [userData])

  // Handle same model toggle
  useEffect(() => {
    if (useSameModel) {
      setContentVettingModel("same")
    }
  }, [useSameModel])

  // Handle content vetting model change
  useEffect(() => {
    if (contentVettingModel === "same") {
      setUseSameModel(true)
    } else {
      setUseSameModel(false)
    }
  }, [contentVettingModel])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const remainingBlogs = userData.usage.blogs_limit - userData.usage.blogs_generated
    const canCreateProject =
      userData.wordpressAccounts.length > 0 &&
      userData.usage.wordpress_accounts_used < userData.usage.wordpress_accounts_limit

    if (numBlogs > remainingBlogs) {
      setShowUpgradePrompt(true)
      return
    }

    if (!canCreateProject) {
      setError("You've reached your WordPress account limit. Please upgrade to add more accounts.")
      return
    }

    if (!selectedWordPressAccount || !selectedOpenAIKey || !selectedGeminiKey || !selectedSerpKey) {
      setError("Please configure all required accounts and API keys in Settings first.")
      return
    }

    setLoading(true)
    setError("")

    try {
      const selectedWPAccount = userData.wordpressAccounts.find((a) => a.id === selectedWordPressAccount)
      const selectedOpenAI = userData.apiKeys.find((k) => k.id === selectedOpenAIKey)
      const selectedGeminiAPI = userData.apiKeys.find((k) => k.id === selectedGeminiKey)
      const selectedSerpAPI = userData.apiKeys.find((k) => k.id === selectedSerpKey)

      // Determine final vetting model
      const finalVettingModel = contentVettingModel === "same" ? draftCreationModel : contentVettingModel

      const newProject = await supabaseApi.addProject({
        name: name.trim(),
        description: description.trim(),
        total_blogs: numBlogs,
        completed_blogs: 0,
        status: "in_progress",
        wordpress_account_id: selectedWPAccount?.id || "",
        api_keys: {
          openai: selectedOpenAI?.id || "",
          gemini: selectedGeminiAPI?.id || "",
          serp: selectedSerpAPI?.id || "",
        },
        // AI Model Configuration
        draft_creation_model: draftCreationModel,
        content_vetting_model: finalVettingModel,
        model_settings: {
          openai: {
            temperature: 0.7,
            max_tokens: 2000,
            model_version: "gpt-4"
          },
          gemini: {
            temperature: 0.3,
            max_output_tokens: 2000,
            model_version: "gemini-pro"
          }
        },
        workflow_preferences: {
          auto_vet_after_draft: true,
          require_human_review: false,
          vetting_threshold: 0.8
        }
      })

      onSuccess(newProject)
      onClose()
    } catch (error: any) {
      setError(error.message || "Failed to create project")
    } finally {
      setLoading(false)
    }
  }

  const openAIKeys = userData.apiKeys.filter((k) => k.service === "openai")
  const geminiKeys = userData.apiKeys.filter((k) => k.service === "gemini")
  const serpKeys = userData.apiKeys.filter((k) => k.service === "serp")

  // Dropdown options
  const draftModelOptions = [
    { value: "openai", label: "OpenAI GPT-4 - Creative & Engaging" },
    { value: "gemini", label: "Gemini Pro - Structured & Informative" }
  ]

  const vettingModelOptions = [
    { value: "same", label: "Same as Draft Model" },
    { value: "openai", label: "OpenAI GPT-4 - Quality & Fact-Checking" },
    { value: "gemini", label: "Gemini Pro - Consistency & Analysis" }
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-4xl bg-white shadow-xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-bold text-gray-900">New Project</CardTitle>
              <CardDescription className="text-gray-600">Create a new Blu Blog Gen project</CardDescription>
            </div>
            <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-400 hover:text-gray-600">
              <X className="h-4 w-4" />
            </Button>
          </div>
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
                    {userData.usage.blogs_limit - userData.usage.blogs_generated} blogs remaining on your{" "}
                    {userData.subscription.plan} plan.
                  </p>
                  <Button
                    onClick={() => {
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
                <label className="block text-sm font-medium text-gray-700 mb-2">Project Name</label>
                <Input
                  placeholder="e.g., Tech Blog Series"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="bg-gray-50 border-gray-300"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Number of Blogs</label>
                <Input
                  type="number"
                  min="1"
                  max="1000"
                  value={numBlogs}
                  onChange={(e) => setNumBlogs(Number.parseInt(e.target.value))}
                  required
                  className="bg-gray-50 border-gray-300"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Remaining: {userData.usage.blogs_limit - userData.usage.blogs_generated} blogs
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <Textarea
                placeholder="e.g., Comprehensive guides about digital marketing strategies for small businesses"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
                rows={3}
                className="bg-gray-50 border-gray-300"
              />
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
                    Draft Creation Model
                  </label>
                  <CustomDropdown
                    value={draftCreationModel}
                    onChange={(value) => setDraftCreationModel(value as "openai" | "gemini")}
                    options={draftModelOptions}
                    placeholder="Select draft creation model"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {draftCreationModel === 'openai' 
                      ? "Best for creative, engaging content with personality"
                      : "Best for structured, SEO-optimized content"
                    }
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content Vetting Model
                  </label>
                  <CustomDropdown
                    value={contentVettingModel}
                    onChange={(value) => setContentVettingModel(value as "openai" | "gemini" | "same")}
                    options={vettingModelOptions}
                    placeholder="Select vetting model"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {contentVettingModel === 'same' 
                      ? `Using ${draftCreationModel} for both creation and vetting`
                      : contentVettingModel === 'openai'
                      ? "Strong quality assurance and fact-checking"
                      : "Excellent consistency and analytical review"
                    }
                  </p>
                </div>
              </div>
              
              {/* Same Model Toggle */}
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="sameModel"
                  checked={useSameModel}
                  onChange={(e) => setUseSameModel(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <label htmlFor="sameModel" className="text-sm text-gray-700">
                  Use same model for both draft creation and vetting
                </label>
              </div>
            </div>

            {/* WordPress Account Selection */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Globe className="h-4 w-4" />
                WordPress Account
              </label>
              {userData.wordpressAccounts.length === 0 ? (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <p className="text-sm text-yellow-800">
                    No WordPress accounts configured. Please add one in Settings first.
                  </p>
                </div>
              ) : (
                <CustomDropdown
                  value={selectedWordPressAccount}
                  onChange={setSelectedWordPressAccount}
                  options={wordpressOptions}
                  placeholder="Select WordPress Account"
                />
              )}
            </div>

            {/* API Keys Configuration */}
            <div className="space-y-4">
              <h3 className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <Key className="h-4 w-4" />
                API Keys Configuration
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">OpenAI Key</label>
                  {openAIKeys.length === 0 ? (
                    <div className="text-xs text-red-600">No keys configured</div>
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
                  <label className="block text-xs font-medium text-gray-600 mb-1">Gemini Key</label>
                  {geminiKeys.length === 0 ? (
                    <div className="text-xs text-red-600">No keys configured</div>
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
                  <label className="block text-xs font-medium text-gray-600 mb-1">SERP API Key</label>
                  {serpKeys.length === 0 ? (
                    <div className="text-xs text-red-600">No keys configured</div>
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
              </div>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <div className="flex space-x-3 pt-4">
              <Button
                type="button"
                onClick={onClose}
                variant="outline"
                className="flex-1 border-gray-300 text-gray-600 hover:bg-gray-50 bg-transparent"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={loading || !name.trim() || !description.trim() || !selectedWordPressAccount}
                className="flex-1 bg-gray-800 hover:bg-gray-700 text-white disabled:opacity-50"
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
