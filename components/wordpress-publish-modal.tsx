"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, Upload, CheckCircle, XCircle, ExternalLink } from "lucide-react"
import { supabaseApi, type WordPressAccount } from "@/lib/supabase-api"

interface WordPressPublishModalProps {
  isOpen: boolean
  onClose: () => void
  blogId: string
  blogTitle: string
  blogStatus?: string
  onSuccess?: () => void
}

export function WordPressPublishModal({ 
  isOpen, 
  onClose, 
  blogId, 
  blogTitle, 
  onSuccess 
}: WordPressPublishModalProps) {
  const [wordpressAccounts, setWordpressAccounts] = useState<WordPressAccount[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState<string>("")
  const [publishStatus, setPublishStatus] = useState<"draft" | "publish">("draft")
  const [loading, setLoading] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [error, setError] = useState<string>("")
  const [success, setSuccess] = useState(false)
  const [publishResult, setPublishResult] = useState<any>(null)

  useEffect(() => {
    if (isOpen) {
      loadWordPressAccounts()
    }
  }, [isOpen])

  const loadWordPressAccounts = async () => {
    try {
      setLoading(true)
      const accounts = await supabaseApi.getWordPressAccounts()
      setWordpressAccounts(accounts)
      
      // Auto-select first account if available
      if (accounts.length > 0 && !selectedAccountId) {
        setSelectedAccountId(accounts[0].id)
      }
    } catch (error) {
      console.error("Error loading WordPress accounts:", error)
      setError("Failed to load WordPress accounts")
    } finally {
      setLoading(false)
    }
  }

  const handlePublish = async () => {
    if (!selectedAccountId) {
      setError("Please select a WordPress account")
      return
    }

    try {
      setPublishing(true)
      setError("")

      const response = await fetch(`http://localhost:8000/api/blogs/${blogId}/publish`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          wordpress_account_id: selectedAccountId,
          publish_status: publishStatus,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "Failed to publish blog")
      }

      const result = await response.json()
      setPublishResult(result)
      setSuccess(true)

      // Call success callback if provided
      if (onSuccess) {
        onSuccess()
      }

      // Auto-close after 3 seconds
      setTimeout(() => {
        onClose()
      }, 3000)

    } catch (error) {
      console.error("Error publishing blog:", error)
      setError(error instanceof Error ? error.message : "Failed to publish blog")
    } finally {
      setPublishing(false)
    }
  }

  const handleClose = () => {
    if (!publishing) {
      setError("")
      setSuccess(false)
      setPublishResult(null)
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-2xl bg-white shadow-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Publish to WordPress
          </CardTitle>
          <CardDescription>
            Publish "{blogTitle}" to your WordPress site
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="ml-2">Loading WordPress accounts...</span>
            </div>
          ) : wordpressAccounts.length === 0 ? (
            <Alert>
              <XCircle className="h-4 w-4" />
              <AlertDescription>
                No WordPress accounts configured. Please add a WordPress account in Settings first.
              </AlertDescription>
            </Alert>
          ) : (
            <>
              {/* WordPress Account Selection */}
              <div className="space-y-2">
                <Label htmlFor="wordpress-account">WordPress Account</Label>
                <Select value={selectedAccountId} onValueChange={setSelectedAccountId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select WordPress account" />
                  </SelectTrigger>
                  <SelectContent>
                    {wordpressAccounts.map((account) => (
                      <SelectItem key={account.id} value={account.id}>
                        {account.name} ({account.site_url})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Publish Status */}
              <div className="space-y-2">
                <Label>Publish Status</Label>
                <RadioGroup value={publishStatus} onValueChange={(value: "draft" | "publish") => setPublishStatus(value)}>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="draft" id="draft" />
                    <Label htmlFor="draft">Draft (save as draft)</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="publish" id="publish" />
                    <Label htmlFor="publish">Publish immediately</Label>
                  </div>
                </RadioGroup>
              </div>

              {/* Error Display */}
              {error && (
                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Success Display */}
              {success && publishResult && (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    Blog published successfully! 
                    {publishResult.wordpress_url && (
                      <div className="mt-2">
                        <a 
                          href={publishResult.wordpress_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 underline inline-flex items-center gap-1"
                        >
                          View on WordPress <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4">
                <Button
                  variant="outline"
                  onClick={handleClose}
                  disabled={publishing}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handlePublish}
                  disabled={!selectedAccountId || publishing}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {publishing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Publishing...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Publish to WordPress
                    </>
                  )}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
