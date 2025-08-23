"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { User, Mail, Edit3, Save, X, LogOut, User as UserIcon } from "lucide-react"
import { authManager, type User as UserType } from "@/lib/auth"
import { UsageLimits } from "@/components/usage-limits"

interface ProfileSettingsProps {
  user: UserType
  onClose: () => void
  userData: {
    usage: {
      blogs_generated: number
      blogs_limit: number
      wordpress_accounts_used: number
      wordpress_accounts_limit: number
    }
    userFeatures?: {
      features_enabled: {
        blog_generation: boolean
        wordpress_accounts: boolean
        ai_image_generation: boolean
        advanced_features: boolean
      }
      feature_limits: {
        blogs_limit: number
        wordpress_accounts_limit: number
        images_limit: number
      }
      pricing_tier: string
    }
  }
}

export function ProfileSettings({ user, onClose, userData }: ProfileSettingsProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [fullName, setFullName] = useState(user.full_name || "")
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  // Debug log to ensure userData is properly passed
  console.log("ProfileSettings userData:", userData)

  const handleSave = async () => {
    if (!fullName.trim()) {
      setError("Name cannot be empty")
      return
    }

    setIsSaving(true)
    setError("")
    setSuccess("")

    try {
      // Update user profile in database
      const { error: updateError } = await authManager.updateProfile({
        full_name: fullName.trim()
      })

      if (updateError) {
        setError(updateError)
      } else {
        setSuccess("Profile updated successfully!")
        setIsEditing(false)
        // Update the user object in the parent component
        // This will be handled by the auth system
      }
    } catch (err) {
      setError("Failed to update profile. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    setFullName(user.full_name || "")
    setIsEditing(false)
    setError("")
    setSuccess("")
  }

  const handleLogout = async () => {
    try {
      await authManager.signOut()
      // The auth system will handle the redirect
    } catch (error) {
      console.error("Logout failed:", error)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-lg mx-4 max-h-[85vh] overflow-y-auto">
        <CardHeader className="text-center pb-4">
          <div className="mx-auto w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-3">
            <UserIcon className="w-6 h-6 text-white" />
          </div>
          <CardTitle className="text-xl">Profile Settings</CardTitle>
          <CardDescription className="text-sm">
            Manage your account information and preferences
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Success/Error Messages */}
          {success && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-700 text-sm">{success}</p>
            </div>
          )}
          
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Full Name Section */}
          <div className="space-y-2">
            <Label htmlFor="fullName" className="flex items-center gap-2">
              <User className="w-4 h-4" />
              Full Name
            </Label>
            <div className="flex gap-2">
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={!isEditing}
                placeholder="Enter your full name"
                className="flex-1"
              />
              {!isEditing ? (
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setIsEditing(true)}
                  className="shrink-0"
                >
                  <Edit3 className="w-4 h-4" />
                </Button>
              ) : (
                <div className="flex gap-1 shrink-0">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={handleSave}
                    disabled={isSaving}
                  >
                    <Save className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={handleCancel}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* Email Section (Read-only) */}
          <div className="space-y-2">
            <Label htmlFor="email" className="flex items-center gap-2">
              <Mail className="w-4 h-4" />
              Email Address
            </Label>
            <Input
              id="email"
              value={user.email}
              disabled
              className="bg-gray-50"
            />
            <p className="text-xs text-gray-500">
              Email cannot be changed for security reasons
            </p>
          </div>

          <Separator />

          {/* Account Info */}
          <div className="space-y-2">
            <Label className="text-sm font-medium text-gray-700">Account Information</Label>
            <div className="text-sm text-gray-600 space-y-1">
              <p>Plan: <span className="font-medium capitalize">{user.subscription?.plan || 'free'}</span></p>
              <p>Member since: <span className="font-medium">
                {new Date(user.created_at).toLocaleDateString()}
              </span></p>
            </div>
          </div>

          <Separator />

          {/* Usage Limits & Features */}
          <div className="space-y-2">
            <Label className="text-sm font-medium text-gray-700">Access & Limits</Label>
            <UsageLimits
              onUpgrade={() => onClose()} // Close modal to go to pricing
              currentPlan={user.subscription?.plan || 'free'}
              usage={userData.usage}
              userFeatures={userData.userFeatures}
            />
          </div>

          <Separator />

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1"
            >
              Close
            </Button>
            <Button
              variant="destructive"
              onClick={handleLogout}
              className="flex-1"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
