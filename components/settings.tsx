"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Plus, Edit, Trash2, Eye, EyeOff, Check, X } from "lucide-react"
import { supabaseApi, type UserData, type WordPressAccount, type APIKey } from "@/lib/supabase-api"

interface SettingsProps {
  onUpdate: () => void
}

export function Settings({ onUpdate }: SettingsProps) {
  const [userData, setUserData] = useState<UserData | null>(null)
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState("")
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingAccount, setEditingAccount] = useState<string | null>(null)
  const [showAddApiKeyForm, setShowAddApiKeyForm] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await supabaseApi.getUserData()
        setUserData(data)
      } catch (error) {
        console.error("Error fetching user data:", error)
        setMessage("Error loading settings")
      }
    }
    fetchData()
  }, [])

  const refreshData = async () => {
    try {
      const data = await supabaseApi.getUserData()
      setUserData(data)
      onUpdate()
    } catch (error) {
      console.error("Error refreshing user data:", error)
      setMessage("Error refreshing settings")
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      // No need to save userData - it's already saved to Supabase
      setMessage("Settings saved successfully!")
      refreshData()
    } catch (error) {
      console.error("Error saving user data:", error)
      setMessage("Error saving settings")
    } finally {
      setSaving(false)
    }
  }

  const togglePasswordVisibility = (field: string) => {
    setShowPasswords((prev) => ({
      ...prev,
      [field]: !prev[field],
    }))
  }

  const addApiKey = async (service: "openai" | "gemini" | "serp") => {
    if (!userData) return
    
    try {
      const newKey = await supabaseApi.addAPIKey({
        name: `${service.charAt(0).toUpperCase() + service.slice(1)} Key ${userData.apiKeys.filter((k) => k.service === service).length + 1}`,
        api_key: "",
        service,
        is_default: userData.apiKeys.filter((k) => k.service === service).length === 0,
      })

      setMessage(`${service.charAt(0).toUpperCase() + service.slice(1)} key added successfully!`)
      refreshData()
      setShowAddApiKeyForm(null)
    } catch (error) {
      console.error("Error adding API key:", error)
      setMessage("Error adding API key")
    }
  }

  const updateApiKey = async (keyId: string, field: keyof APIKey, value: string | boolean) => {
    try {
      await supabaseApi.updateAPIKey(keyId, { [field]: value })
      refreshData()
    } catch (error) {
      console.error("Error updating API key:", error)
      setMessage("Error updating API key")
    }
  }

  const deleteApiKey = async (keyId: string) => {
    try {
      await supabaseApi.deleteAPIKey(keyId)
      setMessage("API key deleted successfully!")
      refreshData()
    } catch (error) {
      console.error("Error deleting API key:", error)
      setMessage("Error deleting API key")
    }
  }

  const setDefaultApiKey = async (keyId: string) => {
    if (!userData) return
    
    try {
      const key = userData.apiKeys.find((k) => k.id === keyId)
      if (key) {
        // First, unset all other keys of the same service as default
        const otherKeys = userData.apiKeys.filter(k => k.service === key.service && k.id !== keyId)
        for (const otherKey of otherKeys) {
          await supabaseApi.updateAPIKey(otherKey.id, { is_default: false })
        }
        
        // Then set the selected key as default
        await supabaseApi.updateAPIKey(keyId, { is_default: true })
        setMessage(`${key.service.charAt(0).toUpperCase() + key.service.slice(1)} default key updated!`)
        refreshData()
      }
    } catch (error) {
      console.error("Error setting default API key:", error)
      setMessage("Error setting default API key")
    }
  }

  const serviceConfigs = {
    openai: { name: "OpenAI", placeholder: "sk-..." },
    gemini: { name: "Google Gemini", placeholder: "AIza..." },
    serp: { name: "SERP API", placeholder: "your-serp-api-key..." },
  }

  const addWordPressAccount = async () => {
    if (!userData) return
    
    try {
      const newAccount = await supabaseApi.addWordPressAccount({
        name: `WordPress Site ${userData.wordpressAccounts.length + 1}`,
        site_url: "",
        username: "",
        password: "",
      })

      setEditingAccount(newAccount.id)
      setShowAddForm(false)
      setMessage("WordPress account added successfully!")
      refreshData()
    } catch (error) {
      console.error("Error adding WordPress account:", error)
      setMessage("Error adding WordPress account")
    }
  }

  const updateWordPressAccount = async (id: string, field: keyof WordPressAccount, value: string) => {
    try {
      await supabaseApi.updateWordPressAccount(id, { [field]: value })
      refreshData()
    } catch (error) {
      console.error("Error updating WordPress account:", error)
      setMessage("Error updating WordPress account")
    }
  }

  const deleteWordPressAccount = async (id: string) => {
    try {
      await supabaseApi.deleteWordPressAccount(id)
      if (editingAccount === id) {
        setEditingAccount(null)
      }
      setMessage("WordPress account deleted successfully!")
      refreshData()
    } catch (error) {
      console.error("Error deleting WordPress account:", error)
      setMessage("Error deleting WordPress account")
    }
  }

  const getApiKeysByService = (service: string) => {
    return userData?.apiKeys.filter((key) => key.service === service) || []
  }

  if (!userData) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded mb-6"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
        <p className="text-gray-600">Configure your API keys and WordPress settings</p>
      </div>

      <div className="space-y-6">
        <Card className="bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg text-gray-900">AI & Search API Keys</CardTitle>
            <CardDescription className="text-gray-600">
              Configure multiple API keys for each service. Mark one as default for each service.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {Object.entries(serviceConfigs).map(([service, config]) => {
              const serviceKeys = getApiKeysByService(service)

              return (
                <div key={service} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900">{config.name}</h4>
                    <Button
                      onClick={() => setShowAddApiKeyForm(service)}
                      variant="outline"
                      size="sm"
                      className="border-gray-300 text-gray-700 hover:bg-gray-50"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Key
                    </Button>
                  </div>

                  {serviceKeys.length === 0 ? (
                    <div className="text-center py-4 text-gray-500 border border-gray-200 rounded-lg">
                      <p className="text-sm">No {config.name} keys configured</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {serviceKeys.map((apiKey) => (
                        <div key={apiKey.id} className="border border-gray-200 rounded-lg p-3">
                          <div className="flex items-center gap-3 mb-2">
                            <Input
                              type="text"
                              placeholder="Key name (e.g., Production Key)"
                              value={apiKey.name}
                              onChange={(e) => updateApiKey(apiKey.id, "name", e.target.value)}
                              className="bg-gray-50 border-gray-300 flex-1"
                            />
                            <Button
                              onClick={() => setDefaultApiKey(apiKey.id)}
                              variant={apiKey.is_default ? "default" : "outline"}
                              size="sm"
                              className={
                                apiKey.is_default
                                  ? "bg-indigo-600 hover:bg-indigo-700 text-white"
                                  : "border-gray-300 text-gray-700 hover:bg-gray-50"
                              }
                            >
                              <Check className={`h-4 w-4 ${apiKey.is_default ? "fill-current" : ""}`} />
                            </Button>
                            <Button
                              onClick={() => deleteApiKey(apiKey.id)}
                              variant="ghost"
                              size="sm"
                              className="text-red-500 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                          <div className="relative">
                            <Input
                              type={showPasswords[`${service}_${apiKey.id}`] ? "text" : "password"}
                              placeholder={config.placeholder}
                              value={apiKey.api_key}
                              onChange={(e) => updateApiKey(apiKey.id, "api_key", e.target.value)}
                              className="bg-gray-50 border-gray-300 pr-10"
                            />
                            <button
                              type="button"
                              onClick={() => togglePasswordVisibility(`${service}_${apiKey.id}`)}
                              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                            >
                              {showPasswords[`${service}_${apiKey.id}`] ? (
                                <EyeOff className="h-4 w-4" />
                              ) : (
                                <Eye className="h-4 w-4" />
                              )}
                            </button>
                          </div>
                          {apiKey.is_default && (
                            <p className="text-xs text-indigo-600 mt-1 flex items-center">
                              <Check className="h-3 w-3 mr-1 fill-current" />
                              Default key for {config.name}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {showAddApiKeyForm === service && (
                    <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-medium text-gray-900">Add New {config.name} Key</h5>
                        <Button
                          onClick={() => setShowAddApiKeyForm(null)}
                          variant="ghost"
                          size="sm"
                          className="text-gray-500 hover:text-gray-700"
                        >
                          <X className="h-4 w-4 mr-2" />
                          Cancel
                        </Button>
                      </div>
                      <Button
                        onClick={() => addApiKey(service as "openai" | "gemini" | "serp")}
                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Create {config.name} Key
                      </Button>
                    </div>
                  )}
                </div>
              )
            })}
          </CardContent>
        </Card>

        <Card className="bg-white shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg text-gray-900">WordPress Accounts</CardTitle>
                <CardDescription className="text-gray-600">
                  Manage multiple WordPress sites for automatic publishing
                </CardDescription>
              </div>
              <Button
                onClick={() => setShowAddForm(true)}
                variant="outline"
                size="sm"
                className="border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Account
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {userData?.wordpressAccounts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No WordPress accounts configured</p>
                <Button
                  onClick={addWordPressAccount}
                  variant="outline"
                  className="mt-4 border-gray-300 text-gray-700 hover:bg-gray-50 bg-transparent"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Your First Account
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {userData.wordpressAccounts.map((account) => (
                  <div key={account.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">{account.name || "Unnamed Account"}</h4>
                      <div className="flex items-center gap-2">
                        <Button
                          onClick={() => setEditingAccount(editingAccount === account.id ? null : account.id)}
                          variant="ghost"
                          size="sm"
                          className="text-gray-500 hover:text-gray-700"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          onClick={() => deleteWordPressAccount(account.id)}
                          variant="ghost"
                          size="sm"
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {editingAccount === account.id ? (
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Account Name</label>
                          <Input
                            type="text"
                            placeholder="My WordPress Site"
                            value={account.name}
                            onChange={(e) => updateWordPressAccount(account.id, "name", e.target.value)}
                            className="bg-gray-50 border-gray-300"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Site URL</label>
                          <Input
                            type="url"
                            placeholder="https://yoursite.com"
                            value={account.site_url}
                            onChange={(e) => updateWordPressAccount(account.id, "site_url", e.target.value)}
                            className="bg-gray-50 border-gray-300"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                          <Input
                            type="text"
                            placeholder="admin"
                            value={account.username}
                            onChange={(e) => updateWordPressAccount(account.id, "username", e.target.value)}
                            className="bg-gray-50 border-gray-300"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Application Password</label>
                          <div className="relative">
                            <Input
                              type={showPasswords[`wp_${account.id}`] ? "text" : "password"}
                              placeholder="xxxx xxxx xxxx xxxx xxxx xxxx"
                              value={account.password}
                              onChange={(e) => updateWordPressAccount(account.id, "password", e.target.value)}
                              className="bg-gray-50 border-gray-300 pr-10"
                            />
                            <button
                              type="button"
                              onClick={() => togglePasswordVisibility(`wp_${account.id}`)}
                              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                            >
                              {showPasswords[`wp_${account.id}`] ? (
                                <EyeOff className="h-4 w-4" />
                              ) : (
                                <Eye className="h-4 w-4" />
                              )}
                            </button>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            Generate an application password in your WordPress admin under Users → Profile
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-600">
                        <p>
                          <span className="font-medium">URL:</span> {account.site_url || "Not configured"}
                        </p>
                        <p>
                          <span className="font-medium">Username:</span> {account.username || "Not configured"}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {showAddForm && (
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-900">Add New WordPress Account</h4>
                  <Button
                    onClick={() => setShowAddForm(false)}
                    variant="ghost"
                    size="sm"
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </div>
                <Button onClick={addWordPressAccount} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
                  <Plus className="h-4 w-4 mr-2" />
                  Create Account
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex items-center justify-between">
          <div>
            {message && (
              <p className={`text-sm ${message.includes("Error") ? "text-red-600" : "text-green-600"}`}>{message}</p>
            )}
          </div>
          <Button onClick={handleSave} disabled={saving} className="bg-gray-800 hover:bg-gray-700 text-white">
            <Check className="h-4 w-4 mr-2" />
            {saving ? "Saving..." : "Save Settings"}
          </Button>
        </div>
      </div>
    </div>
  )
}
