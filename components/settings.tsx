"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Plus, Edit, Trash2, Eye, EyeOff, Check, X } from "lucide-react"
import { supabaseApi, type UserData, type WordPressAccount, type APIKey } from "@/lib/supabase-api"

interface SettingsProps {
  onUpdate: () => void
}

// Debounce hook for input fields
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

export function Settings({ onUpdate }: SettingsProps) {
  const [userData, setUserData] = useState<UserData | null>(null)
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState("")
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingAccount, setEditingAccount] = useState<string | null>(null)
  const [showAddApiKeyForm, setShowAddApiKeyForm] = useState<string | null>(null)
  const [newApiKeyName, setNewApiKeyName] = useState("")
  const [newApiKeyValue, setNewApiKeyValue] = useState("")
  const [newWordPressName, setNewWordPressName] = useState("")
  const [newWordPressUrl, setNewWordPressUrl] = useState("")
  const [newWordPressUsername, setNewWordPressUsername] = useState("")
  const [newWordPressPassword, setNewWordPressPassword] = useState("")
  const [isDemoMode, setIsDemoMode] = useState(false)
  
  // Local state for editing - prevents immediate API calls
  const [editingApiKeys, setEditingApiKeys] = useState<Record<string, APIKey>>({})
  const [editingWordPressAccounts, setEditingWordPressAccounts] = useState<Record<string, WordPressAccount>>({})

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await supabaseApi.getUserData()
        setUserData(data)
        // Check if we're in demo mode (no Supabase connection)
        setIsDemoMode(!process.env.NEXT_PUBLIC_SUPABASE_URL)
      } catch (error) {
        console.error("Error fetching user data:", error)
        setMessage("Error loading settings")
        // If error is about Supabase not being configured, set demo mode
        if (error instanceof Error && error.message === 'Supabase not configured') {
          setIsDemoMode(true)
        }
      }
    }
    fetchData()
  }, [])

  const refreshData = async () => {
    try {
      console.log("🔄 Refreshing user data...")
      
      // Add a small random delay to avoid cache issues
      const randomDelay = Math.random() * 1000
      await new Promise(resolve => setTimeout(resolve, randomDelay))
      
      const data = await supabaseApi.getUserData()
      console.log("✅ Fresh data received:", data)
      
      setUserData(data)
      onUpdate()
    } catch (error) {
      console.error("Error refreshing user data:", error)
      setMessage("Error refreshing settings")
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage("") // Clear any previous messages
    
    try {
      console.log("Starting save process...")
      console.log("Editing API keys:", editingApiKeys)
      console.log("Editing WordPress accounts:", editingWordPressAccounts)
      
      // Check if we're in demo mode
      if (isDemoMode) {
        setMessage("Demo mode: Cannot save changes without database connection")
        setSaving(false)
        return
      }
      
      // Save all pending changes
      const promises = []
      
      // Save API key changes
      for (const [keyId, apiKey] of Object.entries(editingApiKeys)) {
        console.log(`Saving API key ${keyId}:`, apiKey)
        
        // Add individual timeout for each API key save
        const apiKeySavePromise = supabaseApi.updateAPIKey(keyId, apiKey)
        const apiKeyTimeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error(`API key save timed out for ${keyId}`)), 15000)
        })
        
        promises.push(Promise.race([apiKeySavePromise, apiKeyTimeoutPromise]))
      }
      
      // Save WordPress account changes
      for (const [accountId, account] of Object.entries(editingWordPressAccounts)) {
        console.log(`Saving WordPress account ${accountId}:`, account)
        promises.push(supabaseApi.updateWordPressAccount(accountId, account))
      }
      
      if (promises.length > 0) {
        console.log(`Executing ${promises.length} save operations...`)
        await Promise.all(promises)
        console.log("All save operations completed successfully")
      } else {
        console.log("No changes to save")
      }
      
          setMessage("Settings saved successfully!")
    
    // Immediately update local state with the saved changes to show them in the UI
    setUserData(prevData => {
      if (!prevData) return prevData
      
      let newData = { ...prevData }
      
      // Apply API key changes immediately
      Object.entries(editingApiKeys).forEach(([keyId, apiKey]) => {
        newData.apiKeys = newData.apiKeys.map(key => 
          key.id === keyId ? { ...key, ...apiKey } : key
        )
      })
      
      // Apply WordPress account changes immediately
      Object.entries(editingWordPressAccounts).forEach(([accountId, account]) => {
        newData.wordpressAccounts = newData.wordpressAccounts.map(acc => 
          acc.id === accountId ? { ...acc, ...account } : acc
        )
      })
      
      console.log("🔄 Updated local state with saved changes:", newData)
      return newData
    })
    
    // Clear editing states after successful save
    setEditingApiKeys({})
    setEditingWordPressAccounts({})
    
    // Force multiple refresh attempts to ensure database consistency
    // This addresses Supabase caching and transaction isolation issues
    try {
      console.log("🔄 Starting multi-stage refresh process...")
      
      // Stage 1: Immediate refresh
      console.log("🔄 Stage 1: Immediate refresh")
      await refreshData()
      
      // Stage 2: Medium delay refresh
      console.log("🔄 Stage 2: Medium delay refresh (3s)")
      await new Promise(resolve => setTimeout(resolve, 3000))
      await refreshData()
      
      // Stage 3: Final delayed refresh
      console.log("🔄 Stage 3: Final delayed refresh (2s)")
      await new Promise(resolve => setTimeout(resolve, 2000))
      await refreshData()
      
      console.log("✅ Multi-stage refresh completed")
      
    } catch (refreshError) {
      console.warn("Some refresh attempts failed, but data was saved:", refreshError)
    }
    } catch (error) {
      console.error("Error saving user data:", error)
      if (error instanceof Error) {
        if (error.message === 'Supabase not configured') {
          setMessage("Error: Database connection not configured. Please check your environment settings.")
        } else {
          setMessage(`Error saving settings: ${error.message}`)
        }
      } else {
        setMessage("Error saving settings: Unknown error occurred")
      }
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

  // Handle API key input changes with local state
  const handleApiKeyChange = (keyId: string, field: keyof APIKey, value: string | boolean) => {
    if (!userData) return
    
    const originalKey = userData.apiKeys.find(k => k.id === keyId)
    if (!originalKey) return
    
    setEditingApiKeys(prev => ({
      ...prev,
      [keyId]: {
        ...originalKey,
        ...prev[keyId],
        [field]: value
      }
    }))
  }

  // Handle WordPress account input changes with local state
  const handleWordPressAccountChange = (accountId: string, field: keyof WordPressAccount, value: string) => {
    if (!userData) return
    
    const originalAccount = userData.wordpressAccounts.find(a => a.id === accountId)
    if (!originalAccount) return
    
    setEditingWordPressAccounts(prev => ({
      ...prev,
      [accountId]: {
        ...originalAccount,
        ...prev[accountId],
        [field]: value
      }
    }))
  }

  // Get the current value (either edited or original)
  const getApiKeyValue = (keyId: string, field: keyof APIKey) => {
    if (editingApiKeys[keyId] && editingApiKeys[keyId][field] !== undefined) {
      return editingApiKeys[keyId][field]
    }
    const originalKey = userData?.apiKeys.find(k => k.id === keyId)
    return originalKey?.[field] || ""
  }

  const getWordPressAccountValue = (accountId: string, field: keyof WordPressAccount) => {
    if (editingWordPressAccounts[accountId] && editingWordPressAccounts[accountId][field] !== undefined) {
      return editingWordPressAccounts[accountId][field]
    }
    const originalAccount = userData?.wordpressAccounts.find(a => a.id === accountId)
    return originalAccount?.[field] || ""
  }

  const addApiKey = async (service: "openai" | "gemini" | "serp" | "fal") => {
    if (!userData || !newApiKeyName || !newApiKeyValue) return
    
    try {
      const newKey = await supabaseApi.addAPIKey({
        name: newApiKeyName,
        api_key: newApiKeyValue,
        service,
        is_default: userData.apiKeys.filter((k) => k.service === service).length === 0,
      })

      setMessage(`${service.charAt(0).toUpperCase() + service.slice(1)} key added successfully!`)
      refreshData()
      setShowAddApiKeyForm(null)
      // Clear the form
      setNewApiKeyName("")
      setNewApiKeyValue("")
    } catch (error) {
      console.error("Error adding API key:", error)
      if (error instanceof Error && error.message === 'Supabase not configured') {
        setMessage("Demo mode: API keys cannot be added without database connection")
      } else {
        setMessage("Error adding API key")
      }
    }
  }

  const updateApiKey = async (keyId: string, field: keyof APIKey, value: string | boolean) => {
    try {
      await supabaseApi.updateAPIKey(keyId, { [field]: value })
      refreshData()
    } catch (error) {
      console.error("Error updating API key:", error)
      if (error instanceof Error && error.message === 'Supabase not configured') {
        setMessage("Demo mode: API keys cannot be updated without database connection")
      } else {
        setMessage("Error updating API key")
      }
    }
  }

  const deleteApiKey = async (keyId: string) => {
    try {
      await supabaseApi.deleteAPIKey(keyId)
      // Remove from editing state if it exists
      setEditingApiKeys(prev => {
        const newState = { ...prev }
        delete newState[keyId]
        return newState
      })
      setMessage("API key deleted successfully!")
      refreshData()
    } catch (error) {
      console.error("Error deleting API key:", error)
      if (error instanceof Error && error.message === 'Supabase not configured') {
        setMessage("Demo mode: API keys cannot be deleted without database connection")
      } else {
        setMessage("Error deleting API key")
      }
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
    fal: { name: "Fal AI", placeholder: "fal-..." },
  }

  const addWordPressAccount = async () => {
    if (!userData || !newWordPressName || !newWordPressUrl || !newWordPressUsername || !newWordPressPassword) return
    
    try {
      const newAccount = await supabaseApi.addWordPressAccount({
        name: newWordPressName,
        site_url: newWordPressUrl,
        username: newWordPressUsername,
        password: newWordPressPassword,
      })

      setShowAddForm(false)
      // Clear the form
      setNewWordPressName("")
      setNewWordPressUrl("")
      setNewWordPressUsername("")
      setNewWordPressPassword("")
      setMessage("WordPress account added successfully!")
      refreshData()
    } catch (error) {
      console.error("Error adding WordPress account:", error)
      if (error instanceof Error && error.message === 'Supabase not configured') {
        setMessage("Demo mode: WordPress accounts cannot be added without database connection")
      } else {
        setMessage("Error adding WordPress account")
      }
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
      // Remove from editing state if it exists
      setEditingWordPressAccounts(prev => {
        const newState = { ...prev }
        delete newState[id]
        return newState
      })
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

  // Check if there are unsaved changes
  const hasUnsavedChanges = Object.keys(editingApiKeys).length > 0 || Object.keys(editingWordPressAccounts).length > 0

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
        
        {isDemoMode && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Demo Mode</h3>
                <p className="text-sm text-yellow-700 mt-1">
                  You're running in demo mode. API keys and WordPress accounts cannot be created, updated, or deleted without a database connection.
                </p>
              </div>
            </div>
          </div>
        )}
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
                       onClick={() => {
                         setShowAddApiKeyForm(service)
                         // Clear the form when opening
                         setNewApiKeyName("")
                         setNewApiKeyValue("")
                         // Clear any previous messages
                         setMessage("")
                       }}
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
                              value={getApiKeyValue(apiKey.id, "name") as string}
                              onChange={(e) => handleApiKeyChange(apiKey.id, "name", e.target.value)}
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
                              value={getApiKeyValue(apiKey.id, "api_key") as string}
                              onChange={(e) => handleApiKeyChange(apiKey.id, "api_key", e.target.value)}
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
                           onClick={() => {
                             setShowAddApiKeyForm(null)
                             // Clear the form when canceling
                             setNewApiKeyName("")
                             setNewApiKeyValue("")
                             // Clear any previous messages
                             setMessage("")
                           }}
                           variant="ghost"
                           size="sm"
                           className="text-gray-500 hover:text-gray-700"
                         >
                          <X className="h-4 w-4 mr-2" />
                          Cancel
                        </Button>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Key Name</label>
                          <input
                            type="text"
                            placeholder={`${config.name} Key ${userData?.apiKeys.filter((k) => k.service === service).length + 1}`}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            onChange={(e) => setNewApiKeyName(e.target.value)}
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                          <input
                            type="password"
                            placeholder={config.placeholder}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            onChange={(e) => setNewApiKeyValue(e.target.value)}
                          />
                        </div>
                        <Button
                          onClick={() => addApiKey(service as "openai" | "gemini" | "serp" | "fal")}
                          disabled={!newApiKeyName || !newApiKeyValue}
                          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white disabled:bg-gray-400 disabled:cursor-not-allowed"
                        >
                          <Plus className="h-4 w-4 mr-2" />
                          Create {config.name} Key
                        </Button>
                      </div>
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
                 onClick={() => {
                   setShowAddForm(true)
                   // Clear the form when opening
                   setNewWordPressName("")
                   setNewWordPressUrl("")
                   setNewWordPressUsername("")
                   setNewWordPressPassword("")
                   // Clear any previous messages
                   setMessage("")
                 }}
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
                   onClick={() => {
                     setShowAddForm(true)
                     // Clear the form when opening
                     setNewWordPressName("")
                     setNewWordPressUrl("")
                     setNewWordPressUsername("")
                     setNewWordPressPassword("")
                     // Clear any previous messages
                     setMessage("")
                   }}
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
                          <Edit className="h-4 w-4" />i
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
                            value={getWordPressAccountValue(account.id, "name") as string}
                            onChange={(e) => handleWordPressAccountChange(account.id, "name", e.target.value)}
                            className="bg-gray-50 border-gray-300"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Site URL</label>
                          <Input
                            type="url"
                            placeholder="https://yoursite.com"
                            value={getWordPressAccountValue(account.id, "site_url") as string}
                            onChange={(e) => handleWordPressAccountChange(account.id, "site_url", e.target.value)}
                            className="bg-gray-50 border-gray-300"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                          <Input
                            type="text"
                            placeholder="admin"
                            value={getWordPressAccountValue(account.id, "username") as string}
                            onChange={(e) => handleWordPressAccountChange(account.id, "username", e.target.value)}
                            className="bg-gray-50 border-gray-300"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Application Password</label>
                          <div className="relative">
                            <Input
                              type={showPasswords[`wp_${account.id}`] ? "text" : "password"}
                              placeholder="xxxx xxxx xxxx xxxx xxxx xxxx"
                              value={getWordPressAccountValue(account.id, "password") as string}
                              onChange={(e) => handleWordPressAccountChange(account.id, "password", e.target.value)}
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
                     onClick={() => {
                       setShowAddForm(false)
                       // Clear the form when canceling
                       setNewWordPressName("")
                       setNewWordPressUrl("")
                       setNewWordPressUsername("")
                       setNewWordPressPassword("")
                       // Clear any previous messages
                       setMessage("")
                     }}
                     variant="ghost"
                     size="sm"
                     className="text-gray-500 hover:text-gray-700"
                   >
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Account Name</label>
                    <input
                      type="text"
                      placeholder="My WordPress Site"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      onChange={(e) => setNewWordPressName(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Site URL</label>
                    <input
                      type="url"
                      placeholder="https://yoursite.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      onChange={(e) => setNewWordPressUrl(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                    <input
                      type="text"
                      placeholder="admin"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      onChange={(e) => setNewWordPressUsername(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Application Password</label>
                    <input
                      type="password"
                      placeholder="xxxx xxxx xxxx xxxx xxxx xxxx"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      onChange={(e) => setNewWordPressPassword(e.target.value)}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Generate an application password in your WordPress admin under Users → Profile
                    </p>
                  </div>
                  <Button 
                    onClick={addWordPressAccount} 
                    disabled={!newWordPressName || !newWordPressUrl || !newWordPressUsername || !newWordPressPassword}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Create WordPress Account
                  </Button>
                </div>
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
            {hasUnsavedChanges && (
              <p className="text-sm text-amber-600">You have unsaved changes. Click Save to apply them.</p>
            )}
          </div>
          <Button 
            onClick={handleSave} 
            disabled={saving || !hasUnsavedChanges} 
            className="bg-gray-800 hover:bg-gray-700 text-white disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            <Check className="h-4 w-4 mr-2" />
            {saving ? "Saving..." : "Save Settings"}
          </Button>
        </div>
      </div>
    </div>
  )
}
