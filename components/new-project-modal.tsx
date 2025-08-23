"use client"

import type React from "react"
import type { ReactElement } from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { X, Globe, Key, AlertTriangle } from "lucide-react"
import { supabaseApi, type Project, type UserData } from "@/lib/supabase-api"

interface NewProjectModalProps {
  onClose: () => void
  onSuccess: (project: Project) => void
  userId: string
  userData: UserData
}

export function NewProjectModal({ onClose, onSuccess, userId, userData }: NewProjectModalProps): ReactElement {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [numBlogs, setNumBlogs] = useState(10)
  const [selectedWordPressAccount, setSelectedWordPressAccount] = useState("")
  const [selectedOpenAIKey, setSelectedOpenAIKey] = useState("")
  const [selectedGeminiKey, setSelectedGeminiKey] = useState("")
  const [selectedSerpKey, setSelectedSerpKey] = useState("")
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-2xl bg-white shadow-xl max-h-[90vh] overflow-y-auto">
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
                <select
                  value={selectedWordPressAccount}
                  onChange={(e) => setSelectedWordPressAccount(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Select WordPress Account</option>
                  {userData.wordpressAccounts.map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.name} ({account.site_url})
                    </option>
                  ))}
                </select>
              )}
            </div>

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
                    <select
                      value={selectedOpenAIKey}
                      onChange={(e) => setSelectedOpenAIKey(e.target.value)}
                      className="w-full px-2 py-1.5 text-sm bg-gray-50 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">Select Key</option>
                      {openAIKeys.map((key) => (
                        <option key={key.id} value={key.id}>
                          {key.name} {key.is_default ? "(Default)" : ""}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Gemini Key</label>
                  {geminiKeys.length === 0 ? (
                    <div className="text-xs text-red-600">No keys configured</div>
                  ) : (
                    <select
                      value={selectedGeminiKey}
                      onChange={(e) => setSelectedGeminiKey(e.target.value)}
                      className="w-full px-2 py-1.5 text-sm bg-gray-50 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">Select Key</option>
                      {geminiKeys.map((key) => (
                        <option key={key.id} value={key.id}>
                          {key.name} {key.is_default ? "(Default)" : ""}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">SERP API Key</label>
                  {serpKeys.length === 0 ? (
                    <div className="text-xs text-red-600">No keys configured</div>
                  ) : (
                    <select
                      value={selectedSerpKey}
                      onChange={(e) => setSelectedSerpKey(e.target.value)}
                      className="w-full px-2 py-1.5 text-sm bg-gray-50 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">Select Key</option>
                      {serpKeys.map((key) => (
                        <option key={key.id} value={key.id}>
                          {key.name} {key.is_default ? "(Default)" : ""}
                        </option>
                      ))}
                    </select>
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
